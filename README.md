# MCYJ Parsing Script

## Get all the available documents from the Michigan Welfare public search API

```bash
python pull_agency_info_api.py --output-dir metadata_output --overwrite=False --verbose
```

This will output the agency info and correpsonding documents to the `metadata_output` directory.
The default behavior will output all available documents in both json and csv formats.

## Get a list of extra and missing files in the downloaded files
```{r}
python get_download_list.py --download-folder Statcom_final --available-files metadata_output/2025-08-27_combined_pdf_content_details.csv
```

## Download missing documents

```bash

```