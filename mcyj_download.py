from datetime import datetime
import os
import re
import argparse
import csv

def file_info_to_filename(agency_id, document_name, document_date):
    # Convert file information dictionary to a filename string

    document_agency = agency_id.strip().replace(" ", "_").replace("/", "_")
    document_name = document_name.strip().replace(" ", "_").replace("/", "-")

    return f"{document_agency}_{document_name}_{document_date}.pdf"

def get_output_dir_info(output_dir):
    """
    Get the list of files in the output directory and the latest date from filenames.

    Args:
        output_dir (str): Directory to check for existing files."""

    existing_files = os.listdir(output_dir)
    if existing_files:
        pdf_files = [f for f in existing_files if re.match(r'.*\d{4}-\d{2}-\d{2}\.pdf$', f)]
        # Extract date from filename using regex and find the most recent date
        all_dates = []
        for f in pdf_files:
            match = re.search(r'(\d{4}-\d{2}-\d{2})\.pdf$', f)
            if match:
                all_dates.append(match.group(1))
        # Get the latest date from the list, parsing as YYYY-MM-DD date
        all_dates = [datetime.strptime(date, '%Y-%m-%d') for date in all_dates]
        if all_dates:
            latest_date = max(all_dates).strftime('%Y-%m-%d')
            print(f"Latest date found in existing files: {latest_date}")
        else:
            latest_date = None

    return existing_files, latest_date


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download Child Welfare Licensing agency PDFs from Michigan's public licensing search.")
    parser.add_argument("--output-dir", dest="output_dir", help="Directory to save the CSV and JSON files", default="./")
    parser.add_argument("--input-file", dest="input_file", help="Path to the input CSV file")
    args = parser.parse_args()
    output_dir = args.output_dir
    input_file = args.input_file

    # Read all of the files in the output directory and get the latest date
    if not os.path.exists(output_dir):
        print(f"Output directory {output_dir} does not exist. Creating it.")
        os.makedirs(output_dir)
    existing_files, latest_date = get_output_dir_info(output_dir)

    # Read in the input file csv as dictionary
    if input_file:
        if os.path.exists(input_file):
            with open(input_file, 'r') as f:
                reader = csv.DictReader(f)
                input_data = [row for row in reader]
        else:
            raise FileNotFoundError(f"Input file {input_file} does not exist.")

    for row in input_data:
        # Parse document_date in "2023-08-22T15:30:32.000Z" format to "YYYY-MM-DD"
        raw_date = row.get('CreatedDate', '')
        try:
            parsed_date = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            parsed_date = raw_date  # fallback if parsing fails

        print(file_info_to_filename(
            agency_id=row.get('agency_id', ''),
            document_name=row.get('Title', ''),
            document_date=parsed_date
        ))
#    print(input_data)
    print(existing_files[:5])
    print(latest_date)