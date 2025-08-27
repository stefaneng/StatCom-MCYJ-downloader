import os
import argparse
import csv
from datetime import datetime
import re

def get_downloaded_files(download_folder, lower = True):
    all_files = os.listdir(download_folder)
    if lower:
        return set(f.lower() for f in all_files)
    else:
        return set(all_files)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check for missing downloaded files.")
    parser.add_argument("--download-folder", help="Folder containing downloaded files")
    parser.add_argument("--available-files", help="File listing expected files")
    args = parser.parse_args()

    downloaded_files = get_downloaded_files(args.download_folder)
    downloaded_files_no_date = {re.sub(r'_\d{4}-\d{2}-\d{2}\.pdf$', '', f) for f in downloaded_files if f.endswith('.pdf')}
    expected_files = set()
    expected_files_no_date = set()
    expected_files_info = []  # Store complete row information
    filename_to_row = {}  # Map filename to complete row

    # Get the directory of the available-files for output
    available_files_dir = os.path.dirname(args.available_files)
    if not available_files_dir:
        available_files_dir = "."  # Current directory if no path specified

    # Read the expected files as csv dict
    with open(args.available_files, "r") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            #print(row)
            document_agency = row.get("agency_name", "")
            document_agency = document_agency.strip().replace(" ", "_").replace("/", "_")
            document_name = row.get("Title", "")
            document_name = document_name.strip().replace(" ", "_").replace("/", "-")
            created_date = row.get("CreatedDate", "")
            extension = row.get("FileExtension", "pdf")
            #print(f"Processing: {document_agency}, {document_name}, {created_date}, {extension}")
    #        datetime.strptime(sanitized_date, '%m-%d-%Y').date()
            document_date = datetime.strptime(created_date, "%Y-%m-%dT%H:%M:%S.%fZ").date()
            filename_with_date = f"{document_agency}_{document_name}_{document_date}.{extension}".lower()
            filename_no_date = f"{document_agency}_{document_name}".lower()

            expected_files.add(filename_with_date)
            expected_files_no_date.add(filename_no_date)
            expected_files_info.append(row)
            filename_to_row[filename_no_date] = row


        # If the files have the same agency and name, but the date is different, we consider it a different file

        extra_files = downloaded_files_no_date - expected_files_no_date
        missing_files = expected_files_no_date - downloaded_files_no_date

#        print(list(downloaded_files)[:5])

        # Print intersection
        print("Files in both downloaded and expected:")
        for f in sorted(downloaded_files & expected_files):
            print(f)

        print("Files in downloaded but not expected:")
        # Write download files to a file
        extra_files_path = os.path.join(available_files_dir, "extra_files.txt")
        with open(extra_files_path, "w") as f:
            for file in sorted(extra_files):
                f.write(file + "\n")

        # Write expected files to a file using CSV writer
        missing_files_path = os.path.join(available_files_dir, "missing_files.csv")
        with open(missing_files_path, "w", newline='') as f:
            if missing_files and expected_files_info:
                # Get the first row to extract headers
                headers = list(expected_files_info[0].keys())
                writer = csv.writer(f)

                # Write header row with filename as additional column
                writer.writerow(["generated_filename"] + headers)

                # Write data rows for missing files
                for file in sorted(missing_files):
                    if file in filename_to_row:
                        row = filename_to_row[file]
                        row_values = [row.get(header, "") for header in headers]
                        # Add file extension to the generated filename
                        file_extension = row.get("FileExtension", "pdf")
                        filename_with_extension = f"{file}.{file_extension}"
                        writer.writerow([filename_with_extension] + row_values)
                    else:
                        # If no row data available, write just the filename
                        writer.writerow([file] + [""] * len(headers))
            else:
                # Fallback to just filenames if no row data available
                writer = csv.writer(f)
                writer.writerow(["generated_filename"])  # Simple header
                for file in sorted(missing_files):
                    writer.writerow([file])

        print(len(missing_files), "missing files found.")
        print(len(extra_files), "extra files found.")