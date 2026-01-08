import csv
import requests
import json
import urllib3
import os

def get_all_agency_info():
    """Fetch all agency information from the Michigan Child Welfare licensing API."""
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    base_url = "https://michildwelfarepubliclicensingsearch.michigan.gov/licagencysrch/webruntime/api/apex/execute"

    params = {
        "cacheable": "true",
        "classname": "@udd/01p8z0000009E4V",
        "isContinuation": "false",
        "method": "getAgenciesDetail",
        "namespace": "",
        "params": json.dumps({"recordId": None}),
        "language": "en-US",
        "asGuest": "true",
        "htmlEncode": "false"
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://michildwelfarepubliclicensingsearch.michigan.gov/licagencysrch/'
    }

    try:
        print("Fetching agency information from API...")
        response = requests.get(base_url, params=params, headers=headers, verify=False, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching agency info: {e}")
        return None

def load_existing_data(csv_file):
    """Load existing facility information from CSV, keyed by LicenseNumber."""
    if not os.path.exists(csv_file):
        return {}

    existing_data = {}
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            license_number = row.get('LicenseNumber')
            if license_number:
                existing_data[license_number] = row

    print(f"Loaded {len(existing_data)} existing records from {csv_file}")
    return existing_data

def main():
    # Path relative to parent directory where script will be run from
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(script_dir, "facility_information.csv")

    # Define the columns we want to keep
    keep_cols = [
        "LicenseNumber",
        "Address",
        "agencyId",
        "AgencyName",
        "AgencyType",
        "City",
        "County",
        "LicenseEffectiveDate",
        "LicenseeGroupOrganizationName",
        "LicenseExpirationDate",
        "LicenseStatus",
        "Phone",
        "ZipCode"
    ]

    # Load existing data
    existing_data = load_existing_data(csv_file)

    # Fetch new data from API
    all_agency_info = get_all_agency_info()
    if not all_agency_info:
        print("Failed to fetch agency information")
        return

    # Extract the agency list
    agency_list = (
        all_agency_info.get('returnValue', {})
        .get('objectData', {})
        .get('responseResult', [])
    )

    print(f"Fetched {len(agency_list)} agencies from API")

    # Merge data: update existing_data with API data (append-only logic)
    # If license number is in CSV but not in API, keep CSV version
    # If license number is in API, use API version
    for agency in agency_list:
        license_number = agency.get('LicenseNumber')
        if license_number:
            # Create row with only the columns we want
            row = {col: agency.get(col, "") for col in keep_cols}
            existing_data[license_number] = row

    # Write merged data back to CSV
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keep_cols, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for license_number in sorted(existing_data.keys()):
            writer.writerow(existing_data[license_number])

    print(f"Written {len(existing_data)} records to {csv_file}")

if __name__ == "__main__":
    main()
