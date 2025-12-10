# PDF Text Extraction Tool

A Python script that extracts text from PDF files using [pdfplumber](https://github.com/jsvine/pdfplumber) and saves the results to compressed Parquet files.

## Overview

This script facilitates the production of a directory of parquet files that store text versions of each file in a directory of pdfs (such as that downloaded by ../ingestion).  We assume the pdf directory is continually being updated, and, as such, the script may need to be run again and again.  Each time the script it run, it:

- **Looks at the parquet files storing the text information we already have**.  These parquet files store both sha256 hashes of the original pdfs and the text that was extracted.
- **Looks at the sha256 of files in the directory**.
- **Figures out files that still need to be processed**.
- **Processes them** into a new parquet file that is added into the parquet directory.

By default the text information is stored in parquet_files, as that is where they are stored in this git repository for this project.  For this project's use, we find 500 pdf files boil down to about 1.5 megabytes.

## Usage

**Note**: All commands should be run from the project root directory.

### Basic Usage

Extract text from all PDFs in a directory:

```bash
uv run pdf_parsing/extract_pdf_text.py --pdf-dir /path/to/pdf/directory
```

This creates timestamped Parquet files in `pdf_parsing/parquet_files/` by default (e.g., `20251103_143052_pdf_text.parquet` with `%Y%m%d_%H%M%S` timestamp).

### Custom Output Directory

Specify a custom output directory:

```bash
uv run pdf_parsing/extract_pdf_text.py --pdf-dir /path/to/pdf/directory --parquet-dir /path/to/output
```

### Limit Processing

Process only a limited number of PDFs (useful for testing or incremental processing):

```bash
uv run pdf_parsing/extract_pdf_text.py --pdf-dir /path/to/pdf/directory --limit 100
```

This will process at most 100 PDFs. Note that already-processed PDFs (skipped files) don't count toward the limit.

### Spot Check

Verify existing extractions by re-processing N random PDFs:

```bash
uv run pdf_parsing/extract_pdf_text.py --pdf-dir /path/to/pdf/directory --spot-check 10
```

This will:
- Load existing records from all Parquet files in the output directory
- Randomly select up to 10 PDFs that have been previously processed
- Re-extract text from those PDFs
- Compare the newly extracted text with the stored text
- Report pass/fail for each PDF

Spot checking exits with code 0 if all checks pass, or code 1 if any fail.

## Output Format

The script outputs compressed Parquet files with the following schema:

### Fields

- **`sha256`** (string): SHA256 hash of the PDF file (hex digest)
- **`dateprocessed`** (string): ISO 8601 timestamp of when the PDF was processed
- **`text`** (list of strings): Text content, one string per page

### File Naming

Each processing run creates a new file named: `YYYYMMDD_HHMMSS_pdf_text.parquet`

Example: `20251103_143052_pdf_text.parquet`

## Violation Parsing Tool

The `parse_parquet_violations.py` script parses the parquet files containing PDF text extracts and outputs violation information to CSV.

### What It Does

This script processes all parquet files and extracts structured information about licensing violations:
- Agency ID (License #)
- Agency name
- Inspection/report date
- List of policies/rules that were violated

The script intelligently filters out rules that are marked as "not violated" or "no violation" and only includes actual violations.

### Usage

**Note**: Run from the project root directory.

#### Basic Usage

Parse all parquet files and create a CSV report:

```bash
python3 parse_parquet_violations.py
```

This will read from `pdf_parsing/parquet_files/` by default and output to `violations_output.csv`.

#### Custom Paths

Specify custom input and output paths:

```bash
python3 parse_parquet_violations.py --parquet-dir /path/to/parquet/files -o my_violations.csv
```

#### Verbose Mode

Enable detailed logging:

```bash
python3 parse_parquet_violations.py --verbose
```

### Output Format

The CSV contains the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `agency_id` | License number | CB250296641, CA110200973 |
| `date` | Inspection or report date | February 14, 2020 |
| `agency_name` | Name of the licensed agency | Child & Family Services - Northeast Michigan |
| `violations_list` | Semicolon-separated list of violated rules | R 400.12421; R 400.12418 |
| `num_violations` | Count of violations | 2 |
| `sha256` | SHA256 hash of the source PDF | abc123... |
| `date_processed` | Timestamp when the PDF was processed | 2025-11-03T13:33:47.274306 |

### Example Output

```csv
agency_id,date,agency_name,violations_list,num_violations,sha256,date_processed
CB040201041,February 14, 2020,Child & Family Services - Northeast Michigan,R 400.12324,1,2731d75f...,2025-11-03T13:33:47.274306
CB040201041,October 25, 2021,Child Family Services of NE Michigan,R 400.12421; R 400.12418,2,d29a479d...,2025-11-03T13:33:47.470767
CA110200973,04/28/2022,Berrien County Trial Court-Family Division,,0,38b0a4d0...,2025-11-03T13:33:47.750253
```

### Violation Detection

The parser identifies violations by looking for several patterns:

1. **CPA Rules**: "Rule Code & CPA Rule 400.XXXX" with "Conclusion: Violation Established"
2. **R 400 Rules**: Michigan Administrative Code references (e.g., "R 400.12421")
3. **MCL References**: Michigan Compiled Laws (e.g., "MCL 722.954c")

The parser explicitly filters out any rules marked as:
- "is not violated"
- "not in violation"
- "no violation"

This ensures that only actual violations are reported, not compliant items mentioned in the document.

### Example Statistics

When run on the existing parquet files:
- Processed: 3510 documents
- Documents with violations: 976
- Documents without violations: 2534

## Complete Workflow

1. **Extract PDF text**: Use `extract_pdf_text.py` to process PDFs and create parquet files
   ```bash
   python3 pdf_parsing/extract_pdf_text.py --pdf-dir /path/to/pdfs
   ```

2. **Parse violations**: Use `parse_parquet_violations.py` to extract violation information
   ```bash
   python3 parse_parquet_violations.py
   ```

3. **Analyze results**: Use the CSV output for analysis, reporting, or further processing

## Requirements

- Python 3.11+
- pandas
- pyarrow
- pdfplumber (for extract_pdf_text.py)
- regex (for extract_pdf_text.py)

Install with:
```bash
pip install pandas pyarrow pdfplumber regex
```

