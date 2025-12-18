#!/usr/bin/env python3
"""
Export each row from parquet files to individual JSON files.

This script reads all parquet files and creates a separate JSON file
for each document (row) containing the full text content and highlighting metadata.
The JSON files are named by their sha256 hash for easy lookup.
"""

import argparse
import ast
import csv
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

from keyword_reduction import load_keyword_reduction_map, apply_keyword_reduction

# Set up logger
logger = logging.getLogger(__name__)


def load_sir_summaries(sir_summaries_csv: str) -> Dict[str, Dict]:
    """Load SIR summaries CSV and create a lookup by SHA256."""
    summaries_by_sha = {}
    
    if not sir_summaries_csv or not Path(sir_summaries_csv).exists():
        logger.warning(f"SIR summaries CSV not found: {sir_summaries_csv}")
        return summaries_by_sha
    
    with open(sir_summaries_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sha256 = row.get('sha256', '').strip()
            if not sha256:
                continue
            
            summaries_by_sha[sha256] = {
                'summary': row.get('response', ''),  # 'response' column contains the AI-generated summary text
                'violation': row.get('violation', '')
            }
    
    logger.info(f"Loaded {len(summaries_by_sha)} SIR summaries")
    return summaries_by_sha


def load_sir_violation_levels(sir_violation_levels_csv: str, keyword_map: Optional[Dict[str, str]] = None) -> Dict[str, Dict]:
    """Load SIR violation levels CSV and create a lookup by SHA256."""
    levels_by_sha = {}
    
    if not sir_violation_levels_csv or not Path(sir_violation_levels_csv).exists():
        logger.warning(f"SIR violation levels CSV not found: {sir_violation_levels_csv}")
        return levels_by_sha
    
    with open(sir_violation_levels_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sha256 = row.get('sha256', '').strip()
            if not sha256:
                continue
            
            # Parse keywords from JSON string if present
            keywords_str = row.get('keywords', '')
            keywords = []
            if keywords_str:
                try:
                    keywords = json.loads(keywords_str)
                except (json.JSONDecodeError, ValueError):
                    logger.warning(f"Failed to parse keywords for {sha256}: {keywords_str}")
                    keywords = []
            
            # Apply keyword reduction if map is provided
            if keyword_map:
                keywords = apply_keyword_reduction(keywords, keyword_map)
            
            levels_by_sha[sha256] = {
                'level': row.get('level', ''),
                'justification': row.get('justification', ''),
                'keywords': keywords
            }
    
    logger.info(f"Loaded {len(levels_by_sha)} SIR violation levels")
    return levels_by_sha


def load_document_metadata(document_csv: str) -> Dict[str, Dict]:
    """Load document CSV and create a lookup by SHA256."""
    metadata_by_sha = {}
    
    if not document_csv or not Path(document_csv).exists():
        logger.warning(f"Document CSV not found: {document_csv}")
        return metadata_by_sha
    
    with open(document_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sha256 = row.get('sha256', '').strip()
            if not sha256:
                continue
            
            metadata_by_sha[sha256] = {
                'agency_id': row.get('agency_id', ''),
                'agency_name': row.get('agency_name', ''),
                'document_title': row.get('document_title', ''),
                'date': row.get('date', ''),
                'is_special_investigation': row.get('is_special_investigation', 'False').lower() in ('true', '1', 'yes'),
            }
    
    logger.info(f"Loaded metadata for {len(metadata_by_sha)} documents")
    return metadata_by_sha


def export_parquet_to_json(parquet_dir: str, output_dir: str, document_csv: Optional[str] = None, sir_summaries_csv: Optional[str] = None, sir_violation_levels_csv: Optional[str] = None, keyword_reduction_csv: Optional[str] = None) -> None:
    """Export each parquet row to a separate JSON file."""
    parquet_path = Path(parquet_dir)
    output_path = Path(output_dir)
    
    if not parquet_path.exists():
        logger.error(f"Directory '{parquet_dir}' does not exist")
        sys.exit(1)
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load keyword reduction map if provided
    keyword_map = {}
    if keyword_reduction_csv:
        logger.info("Loading keyword reduction mappings...")
        keyword_map = load_keyword_reduction_map(keyword_reduction_csv)
    
    # Load document metadata if provided
    document_metadata = load_document_metadata(document_csv) if document_csv else {}
    
    # Load SIR summaries if provided
    sir_summaries = load_sir_summaries(sir_summaries_csv) if sir_summaries_csv else {}
    
    # Load SIR violation levels if provided (with keyword reduction)
    sir_violation_levels = load_sir_violation_levels(sir_violation_levels_csv, keyword_map) if sir_violation_levels_csv else {}
    
    # Find all parquet files
    parquet_files = list(parquet_path.glob("*.parquet"))
    
    if not parquet_files:
        logger.error(f"No parquet files found in '{parquet_dir}'")
        sys.exit(1)
    
    logger.info(f"Found {len(parquet_files)} parquet files")
    
    total_documents = 0
    
    for parquet_file in sorted(parquet_files):
        logger.info(f"Processing: {parquet_file.name}")
        
        try:
            df = pd.read_parquet(parquet_file)
            logger.info(f"  Found {len(df)} documents in file")
            
            for idx, row in df.iterrows():
                sha256 = row['sha256']
                dateprocessed = row['dateprocessed']
                
                # Parse text - it's stored as a list or numpy array
                text_data = row['text']
                if isinstance(text_data, str):
                    # If stored as string, parse it safely
                    try:
                        # Validate that it looks like a list before parsing
                        if text_data.strip().startswith('[') and text_data.strip().endswith(']'):
                            text_pages = ast.literal_eval(text_data)
                            # Ensure result is a list
                            if not isinstance(text_pages, list):
                                logger.warning(f"Parsed text is not a list for document {sha256}")
                                text_pages = []
                        else:
                            logger.warning(f"Text data is not in list format for document {sha256}")
                            text_pages = []
                    except (ValueError, SyntaxError) as e:
                        logger.warning(f"Failed to parse text for document {sha256}: {e}")
                        text_pages = []
                else:
                    # If already a list or array, convert to list
                    text_pages = list(text_data) if text_data is not None else []
                
                # Create JSON document with base data
                document = {
                    'sha256': sha256,
                    'dateprocessed': str(dateprocessed),
                    'pages': text_pages
                }
                
                # Add document metadata if available
                if sha256 in document_metadata:
                    metadata = document_metadata[sha256]
                    document['metadata'] = {
                        'agency_id': metadata['agency_id'],
                        'agency_name': metadata['agency_name'],
                        'document_title': metadata['document_title'],
                        'date': metadata['date'],
                        'is_special_investigation': metadata['is_special_investigation']
                    }
                
                # Add SIR summary if available
                if sha256 in sir_summaries:
                    summary = sir_summaries[sha256]
                    document['sir_summary'] = {
                        'summary': summary['summary'],
                        'violation': summary['violation']
                    }
                
                # Add SIR violation level if available
                if sha256 in sir_violation_levels:
                    level_data = sir_violation_levels[sha256]
                    document['sir_violation_level'] = {
                        'level': level_data['level'],
                        'justification': level_data['justification'],
                        'keywords': level_data.get('keywords', [])
                    }
                
                # Write to individual JSON file
                output_file = output_path / f"{sha256}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(document, f, indent=2, ensure_ascii=False)
                
                total_documents += 1
                
                if total_documents % 100 == 0:
                    logger.info(f"  Exported {total_documents} documents...")
                    
        except Exception as e:
            logger.error(f"Error processing {parquet_file.name}: {e}")
            continue
    
    logger.info(f"\nExported {total_documents} documents to {output_dir}")


def main():
    """Main entry point."""
    # Get script directory to make paths relative to script location
    script_dir = Path(__file__).parent.absolute()
    
    parser = argparse.ArgumentParser(
        description="Export parquet rows to individual JSON files with document metadata"
    )
    parser.add_argument(
        "--parquet-dir",
        default=str(script_dir / "../pdf_parsing/parquet_files"),
        help="Directory containing parquet files (default: ../pdf_parsing/parquet_files)"
    )
    parser.add_argument(
        "--output-dir",
        default=str(script_dir / "public/documents"),
        help="Output directory for JSON files (default: public/documents)"
    )
    parser.add_argument(
        "--document-csv",
        default=str(script_dir / "../document_info.csv"),
        help="Path to document info CSV file for metadata (default: ../document_info.csv)"
    )
    parser.add_argument(
        "--sir-summaries-csv",
        default=str(script_dir / "../pdf_parsing/sir_summaries.csv"),
        help="Path to SIR summaries CSV file (default: ../pdf_parsing/sir_summaries.csv)"
    )
    parser.add_argument(
        "--sir-violation-levels-csv",
        default=str(script_dir / "../pdf_parsing/sir_violation_levels.csv"),
        help="Path to SIR violation levels CSV file (default: ../pdf_parsing/sir_violation_levels.csv)"
    )
    parser.add_argument(
        "--keyword-reduction-csv",
        default=str(script_dir / "../pdf_parsing/violation_curation_keyword_reduction.csv"),
        help="Path to keyword reduction CSV file (default: ../pdf_parsing/violation_curation_keyword_reduction.csv)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose debug output"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    export_parquet_to_json(args.parquet_dir, args.output_dir, args.document_csv, args.sir_summaries_csv, args.sir_violation_levels_csv, args.keyword_reduction_csv)


if __name__ == "__main__":
    main()
