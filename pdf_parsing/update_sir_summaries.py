#!/usr/bin/env python3
"""
Update sir_summaries.csv with AI-generated summaries for SIRs.

This script:
1. Reads document_info.csv to identify all SIR document shas
2. Compares against existing summaries in pdf_parsing/sir_summaries.csv
3. Queries up to N missing SIRs using OpenRouter API
4. Appends new results to pdf_parsing/sir_summaries.csv
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
log_file = script_dir / 'update_sir_summaries.log'
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# OpenRouter API configuration
OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
MODEL = 'deepseek/deepseek-v3.2'  # DeepSeek v3.2

# Query to ask about each SIR - now requests JSON format
QUERY_TEXT = """Please analyze this Special Investigation Report and respond with a JSON object containing exactly two fields:

1. "summary": A few sentences explaining what went down here, including one extra sentence weighing in on culpability.
2. "violation": Either "y" if allegations of policy/code violations were substantiated in this report, or "n" if they were not substantiated.

Return ONLY the JSON object, no other text. Format:
{"summary": "...", "violation": "y"}"""



def get_api_key() -> str:
    """Get OpenRouter API key from environment variable."""
    api_key = os.environ.get('OPENROUTER_KEY')
    if not api_key:
        raise ValueError(
            "OPENROUTER_KEY environment variable not set. "
            "Please set it with your OpenRouter API key."
        )
    return api_key


def get_all_sir_shas(doc_info_csv: str) -> List[str]:
    """
    Get SHA256 hashes for all documents that are SIRs from document_info.csv.
    
    Args:
        doc_info_csv: Path to document_info.csv file
    
    Returns:
        List of SHA256 hashes for SIR documents
    """
    doc_info_path = Path(doc_info_csv)
    if not doc_info_path.exists():
        raise FileNotFoundError(f"Document info CSV not found: {doc_info_csv}")
    
    df = pd.read_csv(doc_info_csv)
    
    # Filter for Special Investigation Reports
    sirs = df[df['is_special_investigation'] == True]
    
    logger.info(f"Found {len(sirs)} SIRs in document info CSV")
    
    return [str(row['sha256']) for _, row in sirs.iterrows()]


def get_existing_summary_shas(summaryqueries_path: str) -> Set[str]:
    """
    Get SHA256 hashes that already have summaries.
    
    Args:
        summaryqueries_path: Path to sir_summaries.csv
    
    Returns:
        Set of SHA256 hashes that already have summaries
    """
    if not Path(summaryqueries_path).exists():
        logger.info(f"No existing {summaryqueries_path}, will create new file")
        return set()
    
    try:
        df = pd.read_csv(summaryqueries_path)
        existing_shas = set(df['sha256'].unique())
        logger.info(f"Found {len(existing_shas)} existing summaries")
        return existing_shas
    except Exception as e:
        logger.error(f"Error reading {summaryqueries_path}: {e}")
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


def query_openrouter(api_key: str, query: str, document_text: str) -> Dict:
    """
    Query OpenRouter API with the document.
    
    Args:
        api_key: OpenRouter API key
        query: The query text
        document_text: Full document text (all pages concatenated)
    
    Returns:
        Dict with summary, violation, response, tokens, and duration
    """
    start_time = time.time()
    
    # Put document first with a common prefix to enable prompt caching
    # This allows OpenRouter to cache the document portion across multiple queries
    full_prompt = f"Consider the following document.\n\n{document_text}\n\n{query}"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://github.com/jacksonloper/MCYJ-Datapipeline',
        'X-Title': 'MCYJ Datapipeline SIR Summary Updates'
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

    # Log raw response for debugging
    logger.debug(f"Raw API response: {ai_response}")
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)
    
    # Parse JSON response
    summary = ''
    violation = ''
    
    try:
        # Try to parse as JSON
        # First, try to extract JSON from the response (in case there's extra text)
        json_match = re.search(r'\{[^{}]*"summary"[^{}]*"violation"[^{}]*\}', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            parsed = json.loads(json_str)
            summary = parsed.get('summary', '')
            violation = parsed.get('violation', '').lower()
            # Normalize violation to y or n
            if violation not in ['y', 'n']:
                violation = 'y' if 'yes' in violation or 'substantiated' in violation.lower() else 'n'
        else:
            # If no JSON found, try parsing the whole response
            parsed = json.loads(ai_response)
            summary = parsed.get('summary', '')
            violation = parsed.get('violation', '').lower()
            if violation not in ['y', 'n']:
                violation = 'y' if 'yes' in violation or 'substantiated' in violation.lower() else 'n'
    except (json.JSONDecodeError, AttributeError, KeyError) as e:
        # If JSON parsing fails, leave both fields empty
        logger.warning(f"Could not parse JSON response: {e}. Setting summary and violation to empty strings.")
        summary = ''
        violation = ''
    
    return {
        'completion_id': completion_id,
        'summary': summary,
        'violation': violation,
        'response': ai_response,  # Keep raw response for debugging
        'input_tokens': input_tokens,
        'output_tokens': output_tokens,
        'duration_ms': duration_ms
    }



def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update sir_summaries.csv with AI summaries for missing SIRs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--doc-info',
        default='document_info.csv',
        help='Path to document_info.csv file (default: document_info.csv)'
    )
    parser.add_argument(
        '--parquet-dir',
        default='parquet_files',
        help='Directory containing parquet files (default: parquet_files)'
    )
    parser.add_argument(
        '--output',
        '-o',
        default='sir_summaries.csv',
        help='Output CSV file path (default: sir_summaries.csv)'
    )
    parser.add_argument(
        '--count',
        '-n',
        type=int,
        default=100,
        help='Maximum number of new SIRs to query (default: 100)'
    )
    parser.add_argument(
        '--query',
        default=QUERY_TEXT,
        help=f'Query text to use (default: "{QUERY_TEXT}")'
    )
    
    args = parser.parse_args()
    
    # Resolve paths relative to script directory
    script_dir = Path(__file__).parent
    doc_info_path = script_dir / args.doc_info
    parquet_dir = script_dir / args.parquet_dir
    output_path = script_dir / args.output
    
    # Get API key
    try:
        api_key = get_api_key()
        logger.info("API key loaded from environment")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Get all SIRs from document info CSV
    logger.info(f"Reading document info from {doc_info_path}...")
    all_sir_shas_list = get_all_sir_shas(str(doc_info_path))
    
    if not all_sir_shas_list:
        logger.warning("No SIRs found in document info CSV")
        sys.exit(0)
    
    all_sir_shas = set(all_sir_shas_list)
    
    # Get existing summary shas
    existing_shas = get_existing_summary_shas(str(output_path))
    
    # Find missing shas
    missing_shas = all_sir_shas - existing_shas
    logger.info(f"Found {len(missing_shas)} SIRs without summaries")
    
    if not missing_shas:
        logger.info("All SIRs already have summaries!")
        sys.exit(0)
    
    # Limit to requested count
    shas_to_query = sorted(list(missing_shas))[:args.count]
    logger.info(f"Will query {len(shas_to_query)} SIRs")
    
    # Prepare results list
    results = []
    
    # Query each SIR
    for idx, sha in enumerate(shas_to_query, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing SIR {idx}/{len(shas_to_query)}: {sha}")
        
        logger.info("Loading document from parquet...")
        doc = load_document_from_parquet(sha, str(parquet_dir))
        
        if not doc:
            logger.error(f"Could not find document in parquet files: {sha}")
            continue
        
        logger.info(f"Document: {len(doc['text_pages'])} pages, {len(doc['full_text'])} characters")
        
        # Query the API
        logger.info("Querying OpenRouter API...")
        try:
            result = query_openrouter(api_key, args.query, doc['full_text'])
            
            logger.info(f"Response received:")
            logger.info(f"  Input tokens: {result['input_tokens']}")
            logger.info(f"  Output tokens: {result['output_tokens']}")
            logger.info(f"  Duration: {result['duration_ms']/1000:.2f}s")
            logger.info(f"  Summary preview: {result['summary'][:150]}...")
            logger.info(f"  Violation: {result['violation']}")

            # Check if parsing succeeded - skip if both summary and violation are empty
            if not result['summary'] or not result['violation']:
                logger.error(f"JSON parsing failed for {sha} - skipping this document")
                logger.error(f"  Summary empty: {not result['summary']}")
                logger.error(f"  Violation empty: {not result['violation']}")
                logger.error(f"  Raw response: {result['response']}")
                continue

            # Store result
            results.append({
                'sha256': sha,
                'response': result['summary'],  # Use parsed summary, not raw response
                'violation': result['violation'],
                'input_tokens': result['input_tokens'],
                'output_tokens': result['output_tokens'],
                'duration_ms': result['duration_ms']
            })
            
            # Add a small delay to avoid rate limiting
            if idx < len(shas_to_query):
                logger.info("Waiting 2 seconds before next query...")
                time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error querying API: {e}")
            continue
    
    if not results:
        logger.warning("No results to save")
        sys.exit(0)
    
    # Append results to CSV
    logger.info(f"\n{'='*80}")
    logger.info(f"Appending {len(results)} results to {output_path}")
    
    file_exists = output_path.exists()
    
    with open(output_path, 'a', newline='', encoding='utf-8') as f:
        fieldnames = ['sha256', 'response', 'violation',
                     'input_tokens', 'output_tokens', 'duration_ms']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(results)
    
    logger.info("Done!")
    
    # Print summary
    successful = len(results)
    total_input_tokens = sum(r['input_tokens'] for r in results)
    total_output_tokens = sum(r['output_tokens'] for r in results)
    
    logger.info(f"\nSummary:")
    logger.info(f"  New summaries added: {successful}")
    logger.info(f"  Total input tokens: {total_input_tokens:,}")
    logger.info(f"  Total output tokens: {total_output_tokens:,}")
    logger.info(f"  Output file: {output_path}")


if __name__ == "__main__":
    main()
