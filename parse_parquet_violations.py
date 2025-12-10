#!/usr/bin/env python3
"""
Parse parquet files containing PDF text extracts and output violation information to CSV.

This script reads concatenated parquet files and extracts:
- Agency ID (License #)
- Date (inspection/report date)
- Agency name
- List of policies/rules considered violated (excluding "not violated" entries)

Output is saved as a CSV file with one row per document.
"""

import argparse
import ast
import csv
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# Set up logger
logger = logging.getLogger(__name__)


def extract_license_number(text: str) -> Optional[str]:
    """Extract license number from text."""
    # Look for patterns like "License #: CB250296641" or "License#: CA110200973"
    patterns = [
        r'License\s*#?\s*:\s*([A-Z0-9]+)',
        r'License\s*Number\s*:\s*([A-Z0-9]+)',
        r'Re:\s*License\s*#?\s*:\s*([A-Z0-9]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1)
    
    return None


def extract_agency_name(text: str) -> Optional[str]:
    """Extract agency name from text."""
    # Look for patterns like "Agency Name: SAMARITAS - BAY" or "Name of Agency:"
    patterns = [
        r'Agency Name:\s*([^\n]+)',
        r'Name of Agency:\s*([^\n]+)',
        r'Licensee Name:\s*([^\n]+)',
        r'Name of Facility:\s*([^\n]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            # Clean up the name
            name = re.sub(r'\s+', ' ', name)
            return name
    
    return None


def extract_inspection_date(text: str) -> Optional[str]:
    """Extract inspection or report date from text."""
    # Look for various date patterns
    patterns = [
        r'Date\(s\) of On-site Inspection:\s*([^\n]+)',
        r'Date of On-site Inspection\(s\):\s*([^\n]+)',
        r'Special Investigation Intake Date:\s*([^\n]+)',
        r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1) if pattern.count('(') > 1 else match.group(0)
            date_str = date_str.strip()
            # Clean up date string
            date_str = re.sub(r'\s+', ' ', date_str)
            return date_str
    
    return None


def extract_violations(text: str) -> List[str]:
    """Extract list of violated policies/rules from text."""
    violations = []
    
    # Look for specific violation sections
    # Pattern 1: Look for "Rule Code & Section" with "Violation Established" or "Violation" conclusion
    rule_pattern = r'Rule Code & CPA Rule\s+(\d+\.\d+[^\n]*)'
    rule_matches = re.finditer(rule_pattern, text, re.IGNORECASE)
    
    for match in rule_matches:
        rule_ref = match.group(1).strip()
        # Get context around this rule to check if it's violated
        start_pos = match.start()
        end_pos = min(start_pos + 3000, len(text))  # Look ahead up to 3000 chars
        context = text[start_pos:end_pos]
        
        # Check if this rule is marked as violated
        if re.search(r'Conclusion\s+Violation Established', context, re.IGNORECASE):
            violations.append(f"CPA Rule {rule_ref}")
        elif re.search(r'Analysis.*?violation', context, re.IGNORECASE | re.DOTALL):
            # Check if analysis mentions violation
            if not re.search(r'is not violated|not in violation|no violation', context, re.IGNORECASE):
                violations.append(f"CPA Rule {rule_ref}")
    
    # Pattern 2: Look for "R 400." references (Michigan Administrative Code)
    r400_pattern = r'R\s+400\.\d+[a-z]?(?:\([^\)]+\))?'
    r400_matches = re.finditer(r400_pattern, text, re.IGNORECASE)
    
    for match in r400_matches:
        rule_ref = match.group(0).strip()
        # Get context to check if violated
        start_pos = max(0, match.start() - 500)
        end_pos = min(match.end() + 500, len(text))
        context = text[start_pos:end_pos]
        
        # Only include if context suggests violation
        if re.search(r'violation|violated|non-compliance|not.*compliance', context, re.IGNORECASE):
            if not re.search(r'is not violated|not in violation|no violation', context, re.IGNORECASE):
                if rule_ref not in [v for v in violations if rule_ref in v]:
                    violations.append(rule_ref)
    
    # Pattern 3: Look for MCL (Michigan Compiled Laws) references
    mcl_pattern = r'MCL\s+\d+\.\d+[a-z]?'
    mcl_matches = re.finditer(mcl_pattern, text, re.IGNORECASE)
    
    for match in mcl_matches:
        rule_ref = match.group(0).strip()
        # Get context to check if violated
        start_pos = max(0, match.start() - 500)
        end_pos = min(match.end() + 500, len(text))
        context = text[start_pos:end_pos]
        
        # Only include if context suggests violation
        if re.search(r'violation|violated|non-compliance|not.*compliance', context, re.IGNORECASE):
            if not re.search(r'is not violated|not in violation|no violation', context, re.IGNORECASE):
                if rule_ref not in [v for v in violations if rule_ref in v]:
                    violations.append(rule_ref)
    
    return violations


def parse_document(text_pages: List[str]) -> Dict[str, Any]:
    """Parse a document (list of pages) and extract relevant information."""
    # Combine all pages into a single text for parsing
    full_text = '\n'.join(text_pages)
    
    # Extract information
    license_number = extract_license_number(full_text)
    agency_name = extract_agency_name(full_text)
    inspection_date = extract_inspection_date(full_text)
    violations = extract_violations(full_text)
    
    return {
        'agency_id': license_number,
        'date': inspection_date,
        'agency_name': agency_name,
        'violations': violations,
        'num_violations': len(violations)
    }


def process_parquet_files(parquet_dir: str, output_csv: str) -> None:
    """Process all parquet files in directory and output to CSV."""
    parquet_path = Path(parquet_dir)
    
    if not parquet_path.exists():
        logger.error(f"Directory '{parquet_dir}' does not exist")
        sys.exit(1)
    
    # Find all parquet files
    parquet_files = list(parquet_path.glob("*.parquet"))
    
    if not parquet_files:
        logger.error(f"No parquet files found in '{parquet_dir}'")
        sys.exit(1)
    
    logger.info(f"Found {len(parquet_files)} parquet files")
    
    # Collect all records
    all_records = []
    total_documents = 0
    documents_with_violations = 0
    
    for parquet_file in sorted(parquet_files):
        logger.info(f"Processing: {parquet_file.name}")
        
        try:
            df = pd.read_parquet(parquet_file)
            logger.info(f"  Found {len(df)} documents in file")
            
            for idx, row in df.iterrows():
                total_documents += 1
                
                # Parse text (stored as string representation of list)
                try:
                    text_pages = ast.literal_eval(row['text']) if isinstance(row['text'], str) else row['text']
                except (ValueError, SyntaxError):
                    logger.error(f"Failed to parse text for document {row['sha256']}")
                    continue
                
                # Parse document
                parsed = parse_document(text_pages)
                
                # Add metadata from parquet
                parsed['sha256'] = row['sha256']
                parsed['date_processed'] = row['dateprocessed']
                
                # Track statistics
                if parsed['num_violations'] > 0:
                    documents_with_violations += 1
                
                all_records.append(parsed)
                
        except Exception as e:
            logger.error(f"Error processing {parquet_file.name}: {e}")
            continue
    
    logger.info(f"\nProcessed {total_documents} documents total")
    logger.info(f"Found {documents_with_violations} documents with violations")
    
    # Write to CSV
    if all_records:
        output_path = Path(output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['agency_id', 'date', 'agency_name', 'violations_list', 'num_violations', 'sha256', 'date_processed']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for record in all_records:
                # Convert violations list to string for CSV
                writer.writerow({
                    'agency_id': record['agency_id'] or '',
                    'date': record['date'] or '',
                    'agency_name': record['agency_name'] or '',
                    'violations_list': '; '.join(record['violations']) if record['violations'] else '',
                    'num_violations': record['num_violations'],
                    'sha256': record['sha256'],
                    'date_processed': record['date_processed']
                })
        
        logger.info(f"\nWrote {len(all_records)} records to {output_csv}")
    else:
        logger.warning("No records to write")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Parse parquet files and extract violation information to CSV"
    )
    parser.add_argument(
        "--parquet-dir",
        default="pdf_parsing/parquet_files",
        help="Directory containing parquet files (default: pdf_parsing/parquet_files)"
    )
    parser.add_argument(
        "-o", "--output",
        default="violations_output.csv",
        help="Output CSV file path (default: violations_output.csv)"
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
    
    process_parquet_files(args.parquet_dir, args.output)


if __name__ == "__main__":
    main()
