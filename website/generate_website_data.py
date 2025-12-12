#!/usr/bin/env python3
"""
Generate JSON data files for the website from CSV files.

This script processes the violations CSV to create
JSON files that can be consumed by the web frontend.
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from pathlib import Path


def load_violations_csv(csv_path):
    """Load violations CSV and group by agency."""
    violations_by_agency = defaultdict(list)
    agency_names = {}  # Map agency_id to agency_name
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            agency_id = row.get('agency_id', '').strip()
            agency_name = row.get('agency_name', '').strip()
            
            if not agency_id:
                continue
            
            # Track agency name for this ID
            if agency_id and agency_name:
                agency_names[agency_id] = agency_name
            
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
                
            violation = {
                'date': row.get('date', ''),
                'agency_name': agency_name,
                'document_title': row.get('document_title', ''),
                'violations_list': row.get('violations_list', ''),
                'num_violations': int(row.get('num_violations', 0)),
                'is_special_investigation': row.get('is_special_investigation', 'False').lower() in ('true', '1', 'yes'),
                'has_not_in_compliance': row.get('has_not_in_compliance', 'False').lower() in ('true', '1', 'yes'),
                'has_in_compliance': row.get('has_in_compliance', 'False').lower() in ('true', '1', 'yes'),
                'not_in_compliance_pages': not_in_compliance_pages,
                'in_compliance_pages': in_compliance_pages,
                'violations_detailed': violations_detailed,
                'sha256': row.get('sha256', ''),
                'date_processed': row.get('date_processed', '')
            }
            violations_by_agency[agency_id].append(violation)
    
    return violations_by_agency, agency_names


def generate_json_files(violations_csv, output_dir):
    """Generate JSON files for the website."""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load violations data
    print("Loading violations data...")
    violations_by_agency, agency_names = load_violations_csv(violations_csv)
    
    # Build agency list from violations data
    print("Building agency list from violations...")
    agency_data = []
    
    for agency_id, violations in violations_by_agency.items():
        # Get agency name from the violations data
        agency_name = agency_names.get(agency_id, 'Unknown Agency')
        
        # Count violations
        total_violations = sum(v['num_violations'] for v in violations)
        
        agency_info = {
            'agencyId': agency_id,
            'AgencyName': agency_name,
            'violations': violations,
            'total_violations': total_violations,
            'total_reports': len(violations)
        }
        
        agency_data.append(agency_info)
    
    # Sort by agency name
    agency_data.sort(key=lambda x: x.get('AgencyName', ''))
    
    # Write full data file
    output_file = os.path.join(output_dir, 'agencies_data.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(agency_data, f, indent=2)
    print(f"Wrote full data to {output_file}")
    
    # Write summary file (without full violations list for faster loading)
    summary_data = []
    for agency in agency_data:
        summary = {
            'agencyId': agency['agencyId'],
            'AgencyName': agency['AgencyName'],
            'total_violations': agency['total_violations'],
            'total_reports': agency['total_reports']
        }
        summary_data.append(summary)
    
    summary_file = os.path.join(output_dir, 'agencies_summary.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)
    print(f"Wrote summary to {summary_file}")
    
    print(f"\nProcessed {len(agency_data)} agencies")
    print(f"Total violations: {sum(a['total_violations'] for a in agency_data)}")
    print(f"Total reports: {sum(a['total_reports'] for a in agency_data)}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate JSON data files for the website from violations CSV only"
    )
    parser.add_argument(
        "--violations-csv",
        required=True,
        help="Path to violations CSV file"
    )
    parser.add_argument(
        "--output-dir",
        default="public/data",
        help="Output directory for JSON files"
    )
    
    args = parser.parse_args()
    
    # Validate input files
    if not os.path.exists(args.violations_csv):
        print(f"Error: Violations CSV not found: {args.violations_csv}")
        sys.exit(1)
    
    generate_json_files(
        args.violations_csv,
        args.output_dir
    )


if __name__ == "__main__":
    main()
