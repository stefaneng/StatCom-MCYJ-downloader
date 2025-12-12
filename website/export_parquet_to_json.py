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

# Set up logger
logger = logging.getLogger(__name__)


def load_violations_metadata(violations_csv: str) -> Dict[str, Dict]:
    """Load violations CSV and create a lookup by SHA256."""
    metadata_by_sha = {}
    
    if not violations_csv or not Path(violations_csv).exists():
        logger.warning(f"Violations CSV not found: {violations_csv}")
        return metadata_by_sha
    
    with open(violations_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sha256 = row.get('sha256', '').strip()
            if not sha256:
                continue
            
            # Parse JSON fields
            try:
                not_in_compliance_pages = json.loads(row.get('not_in_compliance_pages', '[]'))
            except (json.JSONDecodeError, TypeError):
                not_in_compliance_pages = []
            
            try:
                in_compliance_pages = json.loads(row.get('in_compliance_pages', '[]'))
            except (json.JSONDecodeError, TypeError):
                in_compliance_pages = []
            
            try:
                violations_detailed = json.loads(row.get('violations_detailed', '[]'))
            except (json.JSONDecodeError, TypeError):
                violations_detailed = []
            
            metadata_by_sha[sha256] = {
                'has_not_in_compliance': row.get('has_not_in_compliance', 'False').lower() in ('true', '1', 'yes'),
                'has_in_compliance': row.get('has_in_compliance', 'False').lower() in ('true', '1', 'yes'),
                'not_in_compliance_pages': not_in_compliance_pages,
                'in_compliance_pages': in_compliance_pages,
                'violations_detailed': violations_detailed
            }
    
    logger.info(f"Loaded metadata for {len(metadata_by_sha)} documents")
    return metadata_by_sha


def export_parquet_to_json(parquet_dir: str, output_dir: str, violations_csv: Optional[str] = None) -> None:
    """Export each parquet row to a separate JSON file."""
    parquet_path = Path(parquet_dir)
    output_path = Path(output_dir)
    
    if not parquet_path.exists():
        logger.error(f"Directory '{parquet_dir}' does not exist")
        sys.exit(1)
    
    # Create output directory
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Load violations metadata if provided
    violations_metadata = load_violations_metadata(violations_csv) if violations_csv else {}
    
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
                
                # Add highlighting metadata if available
                if sha256 in violations_metadata:
                    metadata = violations_metadata[sha256]
                    document['highlighting'] = {
                        'has_not_in_compliance': metadata['has_not_in_compliance'],
                        'has_in_compliance': metadata['has_in_compliance'],
                        'not_in_compliance_pages': metadata['not_in_compliance_pages'],
                        'in_compliance_pages': metadata['in_compliance_pages'],
                        'violations_detailed': metadata['violations_detailed']
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
        description="Export parquet rows to individual JSON files with highlighting metadata"
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
        "--violations-csv",
        default=str(script_dir / "../violations_output.csv"),
        help="Path to violations CSV file for highlighting metadata (default: ../violations_output.csv)"
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
    
    export_parquet_to_json(args.parquet_dir, args.output_dir, args.violations_csv)


if __name__ == "__main__":
    main()
