# MCYJ Parsing Script

## 1. Get all the available documents from the Michigan Welfare public search API

```bash
python pull_agency_info_api.py --output-dir metadata_output --overwrite=False --verbose
```

This will output the agency info and correpsonding documents to the `metadata_output` directory.
The default behavior will output all available documents in both json and csv formats.

### 1. Output
```bash
ls metadata_output
#> 2025-10-30_agency_info.csv
#> 2025-10-30_all_agency_info.json
#> 2025-10-30_combined_pdf_content_details.csv
```

## 2. Get a list of extra and missing files in the downloaded files

```r
python get_download_list.py --download-folder Downloads --available-files "metadata_output/$(date +"%Y-%m-%d")_combined_pdf_content_details.csv"
```

### 2. Output
```bash
ls metadata_output
#> 2025-10-30_agency_info.csv
#> 2025-10-30_all_agency_info.json
#> 2025-10-30_combined_pdf_content_details.csv
#> extra_files.txt
#> missing_files.csv
```

  - `extra_files.txt` contains files that are in `Downloads` but are not found from the API (most likely due to naming discrepancies)
  - `missing_Files.csv` contains missing files in the csv format with header:

```
generated_filename,agency_name,agency_id,FileExtension,CreatedDate,Title,ContentBodyId,Id,ContentDocumentId
```

## 3. Download missing documents

```bash
python download_all_pdfs.py --csv metadata_output/missing_files.csv --output-dir Downloads
```

### 3. Output

```bash
$ ls downloads/ | head
# 42ND_CIRCUIT_COURT_-_FAMILY_DIVISION_42ND_CIRCUIT_COURT_-_FAMILY_DIVISION_Interim_2025_2025-07-18_069cs0000104BR0AAM.pdf
# ADOPTION_AND_FOSTER_CARE_SPECIALISTS,_INC._CB440295542_INSP_201_2020-03-14_0698z000005Hpu5AAC.pdf
# ADOPTION_AND_FOSTER_CARE_SPECIALISTS,_INC._CB440295542_ORIG.pdf_2008-06-24_0698z000005HozQAAS.pdf
# ADOPTION_ASSOCIATES,_INC_Adoption_Associates_INC_Renewal_2025_2025-08-20_069cs0000163byMAAQ.pdf
# ADOPTION_OPTION,_INC._CB560263403_ORIG.pdf_2004-05-08_0698z000005Hp18AAC.pdf
```

## 4. Check duplicates and update file metadata

check the md5sums

## 5. Extract text from PDFs and parse violations

Extract text from PDFs and save to parquet files:

```bash
python3 pdf_parsing/extract_pdf_text.py --pdf-dir Downloads --parquet-dir pdf_parsing/parquet_files
```

Parse parquet files to extract violation information to CSV:

```bash
python3 parse_parquet_violations.py --parquet-dir pdf_parsing/parquet_files -o violations_output.csv
```

The output CSV contains:
- Agency ID (License #)
- Agency name
- Inspection/report date
- List of policies/rules violated (excluding "not violated" entries)

See [pdf_parsing/README.md](pdf_parsing/README.md) for more details.