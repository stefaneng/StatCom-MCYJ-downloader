#!/usr/bin/env python3
"""
Update sir_violation_levels.csv with AI-generated violation severity levels for SIRs.

This script:
1. Reads sir_summaries.csv to identify SIRs where violations were substantiated
2. Compares against existing levels in pdf_parsing/sir_violation_levels.csv
3. Queries up to N missing SIRs using OpenRouter API
4. Appends new results to pdf_parsing/sir_violation_levels.csv
"""

import argparse
import ast
import csv
import json
import logging
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set

import pandas as pd
import requests

# Set up logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add file handler for detailed logging
script_dir = Path(__file__).parent
log_file = script_dir / 'update_violation_levels.log'
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# OpenRouter API configuration
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL = 'deepseek/deepseek-v3.2'  # DeepSeek v3.2

# Query template for violation level classification
# Document comes first with a common prefix to enable prompt caching
QUERY_TEMPLATE = """Consider the following document.

{document_text}

Based on the categorization instructions below, please analyze this Special Investigation Report and determine the severity level of the actual violations that were substantiated (ignore any unsubstantiated allegations).

Categorization Instructions:
{theming_instructions}

Please respond with a JSON object containing exactly three fields:

1. "level": Either "low", "moderate", or "severe" based on the categorization instructions above
2. "justification": A brief explanation of why you chose this level, referencing the specific violations found and how they align with the categorization criteria
3. "keywords": A list of keywords pertinent to the reasons why this document is labelled with this violation level (e.g., ["physical assault", "inadequate supervision"], ["medication error"], ["paperwork delay", "documentation"])

Return ONLY the JSON object, no other text. Format:
{{"level": "...", "justification": "...", "keywords": [...]}}"""


def get_api_key() -> str:
    """Get OpenRouter API key from environment variable."""
    api_key = os.environ.get('OPENROUTER_KEY')
    if not api_key:
        raise ValueError(
            "OPENROUTER_KEY environment variable not set. "
            "Please set it with your OpenRouter API key."
        )
    return api_key


def load_theming_instructions(theming_path: str) -> str:
    """
    Load the sir_theming.txt file with instructions for categorizing violations.
    
    Args:
        theming_path: Path to sir_theming.txt file
    
    Returns:
        Content of the theming instructions file
    """
    theming_file = Path(theming_path)
    if not theming_file.exists():
        raise FileNotFoundError(f"Theming instructions file not found: {theming_path}")
    
    with open(theming_file, 'r', encoding='utf-8') as f:
        return f.read()


def get_sirs_with_violations(summaries_csv: str) -> List[Dict[str, str]]:
    """
    Get all SIRs from sir_summaries.csv where violations were substantiated.
    
    Args:
        summaries_csv: Path to sir_summaries.csv file
    
    Returns:
        List of dicts with SIR information for documents with violations
    """
    summaries_path = Path(summaries_csv)
    if not summaries_path.exists():
        raise FileNotFoundError(f"Summaries CSV not found: {summaries_csv}")
    
    df = pd.read_csv(summaries_csv)
    
    # Filter for SIRs where violation was substantiated
    violations = df[df['violation'] == 'y']
    
    logger.info(f"Found {len(violations)} SIRs with substantiated violations")
    
    # Convert to list of dicts
    sir_list = []
    for _, row in violations.iterrows():
        sir_info = {
            'sha256': str(row['sha256']),
            'agency_id': str(row['agency_id']) if pd.notna(row['agency_id']) else '',
            'agency_name': str(row['agency_name']) if pd.notna(row['agency_name']) else '',
            'document_title': str(row['document_title']) if pd.notna(row['document_title']) else '',
            'date': str(row['date']) if pd.notna(row['date']) else '',
        }
        sir_list.append(sir_info)
    
    return sir_list


def get_existing_level_shas(levels_path: str) -> Set[str]:
    """
    Get SHA256 hashes that already have violation levels.
    
    Args:
        levels_path: Path to sir_violation_levels.csv
    
    Returns:
        Set of SHA256 hashes that already have levels
    """
    if not Path(levels_path).exists():
        logger.info(f"No existing {levels_path}, will create new file")
        return set()
    
    try:
        df = pd.read_csv(levels_path)
        existing_shas = set(df['sha256'].unique())
        logger.info(f"Found {len(existing_shas)} existing violation levels")
        return existing_shas
    except Exception as e:
        logger.error(f"Error reading {levels_path}: {e}")
        return set()


def load_document_from_parquet(sha256: str, parquet_dir: str) -> Optional[Dict]:
    """Load a document from parquet files by SHA256 hash."""
    parquet_path = Path(parquet_dir)
    parquet_files = list(parquet_path.glob("*.parquet"))
    
    for parquet_file in parquet_files:
        try:
            df = pd.read_parquet(parquet_file)
            matches = df[df['sha256'] == sha256]
            
            if not matches.empty:
                row = matches.iloc[0]
                
                # Parse text
                text_data = row['text']
                if isinstance(text_data, str):
                    text_stripped = text_data.strip()
                    if text_stripped.startswith('[') and text_stripped.endswith(']'):
                        text_pages = ast.literal_eval(text_data)
                    else:
                        text_pages = []
                else:
                    text_pages = list(text_data) if text_data is not None else []
                
                full_text = '\n\n'.join(text_pages)
                
                return {
                    'sha256': row['sha256'],
                    'text_pages': text_pages,
                    'full_text': full_text
                }
        except Exception as e:
            logger.debug(f"Error reading {parquet_file.name}: {e}")
            continue
    
    return None


def normalize_violation_level(level: str) -> str:
    """
    Normalize a violation level string to one of: 'low', 'moderate', 'severe', or empty.
    
    Args:
        level: Raw level string from LLM response
    
    Returns:
        Normalized level string
    """
    level = level.lower()
    if level in ['low', 'moderate', 'severe']:
        return level
    
    # Try to normalize variations
    if 'low' in level:
        return 'low'
    elif 'moderate' in level or 'medium' in level:
        return 'moderate'
    elif 'severe' in level or 'high' in level:
        return 'severe'
    
    return ''


def query_openrouter(api_key: str, theming_instructions: str, document_text: str) -> Dict:
    """
    Query OpenRouter API with the document and theming instructions.
    
    Args:
        api_key: OpenRouter API key
        theming_instructions: Content from sir_theming.txt
        document_text: Full document text (all pages concatenated)
    
    Returns:
        Dict with level, justification, keywords, response, tokens, cost, and duration
        
    Raises:
        Exception: If API request fails or JSON response cannot be parsed
    """
    start_time = time.time()
    
    # Construct the query using the template
    full_prompt = QUERY_TEMPLATE.format(
        theming_instructions=theming_instructions,
        document_text=document_text
    )
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/jacksonloper/MCYJ-Datapipeline',
        'X-Title': 'MCYJ Datapipeline SIR Violation Level Updates'
    }
    
    payload = {
        'model': MODEL,
        'messages': [
            {
                'role': 'user',
                'content': full_prompt
            }
        ],
        'usage': {
            'include': True
        }
    }
    
    response = requests.post(
        OPENROUTER_API_URL,
        headers=headers,
        json=payload,
        timeout=180  # 3 minute timeout
    )
    
    end_time = time.time()
    duration_ms = int((end_time - start_time) * 1000)
    
    if not response.ok:
        error_msg = f"API request failed: {response.status_code} {response.text}"
        logger.error(error_msg)
        raise Exception(error_msg)
    
    data = response.json()

    # Extract completion ID
    completion_id = data.get('id', '')
    logger.info(f"Completion ID: {completion_id}")

    # Extract response and token usage
    ai_response = data.get('choices', [{}])[0].get('message', {}).get('content', 'No response received')
    usage = data.get('usage', {})
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)

    # Extract cost from usage object
    cost = usage.get('cost', None)

    # Extract cache discount information (shows savings from prompt caching)
    cache_discount = usage.get('cache_discount', None)

    # Extract cached tokens information
    prompt_tokens_details = usage.get('prompt_tokens_details', {})
    cached_tokens = prompt_tokens_details.get('cached_tokens', 0) if prompt_tokens_details else 0
    
    # Parse JSON response
    level = ''
    justification = ''
    keywords = []
    
    try:
        # Try to parse the response as JSON directly first
        parsed = json.loads(ai_response)
        level = parsed.get('level', '')
        justification = parsed.get('justification', '')
        keywords = parsed.get('keywords', [])
    except json.JSONDecodeError:
        # If direct parsing fails, try to extract JSON from the response (in case there's extra text)
        # Find the first { and attempt to parse from there, trying progressively longer substrings
        start_idx = ai_response.find('{')
        if start_idx != -1:
            # Try to find a valid JSON object by looking for matching braces
            brace_count = 0
            for i in range(start_idx, len(ai_response)):
                if ai_response[i] == '{':
                    brace_count += 1
                elif ai_response[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Found matching closing brace
                        json_str = ai_response[start_idx:i+1]
                        try:
                            parsed = json.loads(json_str)
                            level = parsed.get('level', '')
                            justification = parsed.get('justification', '')
                            keywords = parsed.get('keywords', [])
                            break
                        except json.JSONDecodeError:
                            continue
            else:
                logger.error("No valid JSON object found in response")
                raise Exception("No valid JSON object found in response")
        else:
            logger.error("No JSON object found in response")
            raise Exception("No JSON object found in response")
    
    # Validate and normalize parsed values (applies to both parsing paths)
    try:
        # Ensure keywords is a list and handle None/empty cases properly
        if keywords is None:
            keywords = []
        elif not isinstance(keywords, list):
            logger.warning(f"Keywords is not a list, converting: {keywords}")
            # Convert to string and wrap in list
            keywords = [str(keywords)] if keywords else []
        
        # Normalize level to low, moderate, or severe
        normalized_level = normalize_violation_level(level)
        if normalized_level != level.lower():
            logger.warning(f"Normalized level '{level}' to '{normalized_level}'")
        level = normalized_level
        
        # Raise error if level is empty (parsing failed)
        if not level:
            raise ValueError(f"Could not extract valid level from response: {ai_response[:200]}")
    except (json.JSONDecodeError, AttributeError, KeyError, ValueError) as e:
        # If JSON parsing or validation fails, raise exception to skip this result
        logger.error(f"Failed to parse/validate JSON response: {e}")
        logger.error(f"Raw response: {ai_response}")
        raise Exception(f"JSON parsing/validation failed: {e}")
    
    return {
        'completion_id': completion_id,
        'level': level,
        'justification': justification,
        'keywords': keywords,
        'response': ai_response,  # Keep raw response for debugging
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'cached_tokens': cached_tokens,
        'cost': cost if cost else '',
        'cache_discount': cache_discount if cache_discount else '',
        'duration_ms': duration_ms
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update sir_violation_levels.csv with AI-generated violation severity levels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--summaries',
        default='sir_summaries.csv',
        help='Path to sir_summaries.csv file (default: sir_summaries.csv)'
    )
    parser.add_argument(
        '--theming',
        default='sir_theming.txt',
        help='Path to sir_theming.txt file (default: sir_theming.txt)'
    )
    parser.add_argument(
        '--parquet-dir',
        default='parquet_files',
        help='Directory containing parquet files (default: parquet_files)'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='sir_violation_levels.csv',
        help='Output CSV file path (default: sir_violation_levels.csv)'
    )
    parser.add_argument(
        '--max-count',
        type=int,
        default=100,
        help='Maximum number of new SIRs to query (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to script directory
    script_dir = Path(__file__).parent
    summaries_path = script_dir / args.summaries
    theming_path = script_dir / args.theming
    parquet_dir = script_dir / args.parquet_dir
    output_path = script_dir / args.output
    
    # Get API key
    try:
        api_key = get_api_key()
        logger.info("API key loaded from environment")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Load theming instructions
    logger.info(f"Loading theming instructions from {theming_path}...")
    try:
        theming_instructions = load_theming_instructions(str(theming_path))
        logger.info(f"Loaded {len(theming_instructions)} characters of theming instructions")
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Get all SIRs with violations from summaries CSV
    logger.info(f"Reading summaries from {summaries_path}...")
    try:
        all_sirs = get_sirs_with_violations(str(summaries_path))
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    if not all_sirs:
        logger.warning("No SIRs with violations found in summaries CSV")
        sys.exit(0)
    
    all_sir_shas = {sir['sha256'] for sir in all_sirs}
    sir_info_map = {sir['sha256']: sir for sir in all_sirs}
    
    # Get existing level shas
    existing_shas = get_existing_level_shas(str(output_path))
    
    # Find missing shas
    missing_shas = all_sir_shas - existing_shas
    logger.info(f"Found {len(missing_shas)} SIRs without violation levels")
    
    if not missing_shas:
        logger.info("All SIRs with violations already have levels!")
        sys.exit(0)
    
    # Limit to requested count
    shas_to_query = sorted(list(missing_shas))[:args.max_count]
    logger.info(f"Will query {len(shas_to_query)} SIRs")
    
    # Prepare results list
    results = []
    
    # Query each SIR
    for idx, sha in enumerate(shas_to_query, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing SIR {idx}/{len(shas_to_query)}: {sha}")
        
        # Get info from sir info map
        sir_info = sir_info_map.get(sha, {})
        
        logger.info("Loading document from parquet...")
        doc = load_document_from_parquet(sha, str(parquet_dir))
        
        if not doc:
            logger.error(f"Could not find document in parquet files: {sha}")
            continue
        
        logger.info(f"Agency: {sir_info.get('agency_name', 'Unknown')}")
        logger.info(f"Title: {sir_info.get('document_title', 'Unknown')}")
        logger.info(f"Date: {sir_info.get('date', 'Unknown')}")
        logger.info(f"Document: {len(doc['text_pages'])} pages, {len(doc['full_text'])} characters")
        
        # Query the API
        logger.info("Querying OpenRouter API...")
        try:
            result = query_openrouter(api_key, theming_instructions, doc['full_text'])
            
            logger.info(f"Response received:")
            logger.info(f"  Input tokens: {result['input_tokens']}")
            logger.info(f"  Output tokens: {result['output_tokens']}")
            logger.info(f"  Cached tokens: {result['cached_tokens']}")
            logger.info(f"  Duration: {result['duration_ms']/1000:.2f}s")
            if result['cost']:
                logger.info(f"  Cost: ${result['cost']:.6f}")
            logger.info(f"  Level: {result['level']}")
            logger.info(f"  Keywords: {result['keywords']}")
            logger.info(f"  Justification preview: {result['justification'][:150]}...")
            
            # Store result
            results.append({
                'sha256': sha,
                'agency_id': sir_info.get('agency_id', ''),
                'agency_name': sir_info.get('agency_name', ''),
                'document_title': sir_info.get('document_title', ''),
                'date': sir_info.get('date', ''),
                'level': result['level'],
                'justification': result['justification'],
                'keywords': json.dumps(result['keywords']),  # Store as JSON string
                'input_tokens': result['input_tokens'],
                'output_tokens': result['output_tokens'],
                'cost': result['cost'],
                'duration_ms': result['duration_ms']
            })
            
            # Add a small delay to avoid rate limiting
            if idx < len(shas_to_query):
                logger.info("Waiting 2 seconds before next query...")
                time.sleep(2)
            
        except requests.RequestException as e:
            logger.error(f"API request error: {e}")
            continue
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            continue
    
    if not results:
        logger.warning("No results to save")
        sys.exit(0)
    
    # Append results to CSV
    logger.info(f"\n{'='*80}")
    logger.info(f"Appending {len(results)} results to {output_path}")
    
    file_exists = output_path.exists()
    
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['sha256', 'agency_id', 'agency_name', 'document_title', 'date',
                     'level', 'justification', 'keywords',
                     'input_tokens', 'output_tokens', 'cost', 'duration_ms']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(results)
    
    logger.info("Done!")
    
    # Print summary
    successful = len(results)
    total_input_tokens = sum(r['input_tokens'] for r in results)
    total_output_tokens = sum(r['output_tokens'] for r in results)
    level_counts = {}
    for r in results:
        level = r['level']
        level_counts[level] = level_counts.get(level, 0) + 1
    
    logger.info(f"\nSummary:")
    logger.info(f"  New levels added: {successful}")
    logger.info(f"  Level distribution: {level_counts}")
    logger.info(f"  Total input tokens: {total_input_tokens:,}")
    logger.info(f"  Total output tokens: {total_output_tokens:,}")
    logger.info(f"  Output file: {output_path}")


if __name__ == "__main__":
    main()
