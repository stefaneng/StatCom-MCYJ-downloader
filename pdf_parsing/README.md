# PDF Parsing

This directory contains tools for processing PDF documents from Michigan child welfare licensing (MCYJ) and extracting structured data from them.

## Directory Structure

```
pdf_parsing/
├── parquet_files/           # Extracted PDF text stored as parquet files
├── document_info.csv        # Structured metadata extracted from documents
├── sir_summaries.csv        # AI-generated summaries for Special Investigation Reports
├── sir_violation_levels.csv # AI-classified severity levels for SIR violations
├── sir_theming.txt          # Criteria for categorizing SIR severity levels
├── violation_curation_keyword_reduction.csv  # Keyword data for violation curation
└── [Python scripts]         # Processing and analysis tools
```

## Scripts

### Core Processing

| Script | Purpose |
|--------|---------|
| `extract_pdf_text.py` | Extracts text from PDF files using pdfplumber and saves to parquet files. Each PDF is identified by its SHA256 hash. |
| `extract_document_info.py` | Parses parquet files to extract structured document metadata (agency ID, name, dates, document titles) into CSV. |

### AI-Powered Analysis

| Script | Purpose |
|--------|---------|
| `update_sir_summaries.py` | Generates AI summaries for Special Investigation Reports using OpenRouter API (DeepSeek model). |
| `update_violation_levels.py` | Classifies SIR violations into severity levels (low/moderate/severe) using AI, based on criteria in `sir_theming.txt`. |

### Utilities

| Script | Purpose |
|--------|---------|
| `check_unique_hashes.py` | Verifies all SHA256 hashes across parquet files are unique (no duplicate documents). |
| `investigate_sha.py` | Inspects a specific document by its SHA256 hash for debugging. |
| `investigate_violations.py` | Displays random documents with their extracted info for quality checking. |

## Data Files

### `parquet_files/`

Contains timestamped parquet files (e.g., `20251103_133347_pdf_text.parquet`) with extracted PDF text. Each record has:
- `sha256` - SHA256 hash of the original PDF
- `text` - List of strings, one per page
- `dateprocessed` - ISO 8601 timestamp

### `document_info.csv`

Structured metadata extracted from documents:
- `agency_id` - License number (e.g., CB250296641)
- `agency_name` - Name of the licensed agency
- `date` - Inspection or report date
- `document_title` - Type of document (e.g., "Special Investigation Report", "Renewal Inspection Report")
- `is_special_investigation` - Boolean flag for SIR documents
- `sha256` - Link back to source document
- `date_processed` - When the PDF was processed

### `sir_summaries.csv`

AI-generated summaries for Special Investigation Reports:
- Document identifiers (sha256, agency_id, agency_name, document_title, date)
- `response` - AI-generated summary
- `violation` - Whether violations were substantiated ("y" or "n")
- API usage metrics (tokens, cost, duration)

### `sir_violation_levels.csv`

AI-classified severity levels for SIRs where violations were substantiated:
- Document identifiers
- `level` - Severity classification: "low", "moderate", or "severe"
- `justification` - Explanation of the classification
- `keywords` - JSON list of relevant keywords

### `sir_theming.txt`

Defines the criteria for categorizing SIR severity:
- **Severe**: Safety/violence, restraint/seclusion, medical/mental health concerns
- **Moderate**: Administrative/rights issues, supervision failures, non-violent staff misconduct
- **Low**: Paperwork issues, non-safety policy compliance, non-hazardous facility conditions

### `violation_curation_keyword_reduction.csv`

Maps raw violation keywords to consolidated terms for consistency in analysis and display. Contains:
- `original_keyword` - Raw keyword from AI classification
- `reduced_keyword` - Normalized/consolidated keyword (empty if keyword should be removed)
- `frequency` - How often this keyword appears in the data

## Document Info Extraction Tool

The `extract_document_info.py` script extracts basic document information from parquet files containing PDF text extracts and outputs to CSV.

### What It Does

This script processes all parquet files and extracts structured information about licensing documents:
- Agency ID (License #)
- Agency name
- Inspection/report date
- Document title (extracted from document content)
- Special Investigation Report indicator (whether document is a SIR)

### Usage

**Note**: Run from the project root directory.

#### Basic Usage

Extract document info from all parquet files and create a CSV report:

```bash
python3 extract_document_info.py
```

This will read from `pdf_parsing/parquet_files/` by default and output to `document_info.csv`.

#### Custom Paths

Specify custom input and output paths:

```bash
python3 extract_document_info.py --parquet-dir /path/to/parquet/files -o my_document_info.csv
```

#### Verbose Mode

Enable detailed logging:

```bash
python3 extract_document_info.py --verbose
```

### Output Format

The CSV contains the following columns:

| Column | Description | Example |
|--------|-------------|---------|
| `agency_id` | License number | CB250296641, CA110200973 |
| `date` | Inspection or report date | February 14, 2020 |
| `agency_name` | Name of the licensed agency | Child & Family Services - Northeast Michigan |
| `document_title` | Type of document | Special Investigation Report #2019C0114036 |
| `is_special_investigation` | Whether document is a Special Investigation Report | True, False |
| `sha256` | SHA256 hash of the source PDF | abc123... |
| `date_processed` | Timestamp when the PDF was processed | 2025-11-03T13:33:47.274306 |

### Example Output

```csv
agency_id,date,agency_name,document_title,is_special_investigation,sha256,date_processed
CB040201041,February 14, 2020,Child & Family Services - Northeast Michigan,Special Investigation Report #2019C0114036,True,2731d75f...,2025-11-03T13:33:47.274306
CB040201041,October 25, 2021,Child Family Services of NE Michigan,Renewal Inspection Report,False,d29a479d...,2025-11-03T13:33:47.470767
CA110200973,04/28/2022,Berrien County Trial Court-Family Division,Licensing Study,False,38b0a4d0...,2025-11-03T13:33:47.750253
```

## Investigate Documents Tool

The `investigate_violations.py` script helps you inspect random documents from the extracted document data, showing both the extracted information and the original document text.

## Update SIR Summaries (update_summaryqueries.py)

Automatically generate and maintain AI-powered summaries for Special Investigation Reports (SIRs).

### Purpose

This script maintains an up-to-date `sir_summaries.csv` file containing AI-generated summaries of all SIRs. It:
1. Scans document information CSV to identify all SIR documents
2. Compares against existing summaries in `sir_summaries.csv`
3. Queries OpenRouter API (DeepSeek v3.2) for missing summaries
4. Appends new results to the CSV file

### Usage

```bash
# Update summaries for up to 100 missing SIRs (default)
cd pdf_parsing
python3 update_summaryqueries.py

# Specify custom count
python3 update_summaryqueries.py --count 50

# Use custom paths
python3 update_summaryqueries.py --doc-info document_info.csv --output sir_summaries.csv
```

### Requirements

- `OPENROUTER_KEY` environment variable must be set with your OpenRouter API key
- Dependencies: `pandas`, `pyarrow`, `requests`

### Output Format

The `sir_summaries.csv` file contains:
- `sha256`: Document hash identifier  
- `agency_id`: Agency license number
- `agency_name`: Name of the agency
- `document_title`: Title of the document
- `date`: Report date
- `query`: Query text sent to AI
- `response`: AI-generated summary and culpability assessment
- `violation`: Whether allegations were substantiated ("y" or "n")
- `input_tokens`: API input token count
- `output_tokens`: API output token count  
- `cost`: API cost (if provided)
- `duration_ms`: Query duration in milliseconds

### Automation

A GitHub Actions workflow (`.github/workflows/update-sir-summaries.yml`) automatically runs this script:
- **Scheduled**: Weekly on Mondays at 00:00 UTC
- **Manual**: Can be triggered from the Actions tab with custom count

The workflow automatically commits new summaries to the repository.

### Query

The script asks: *"Please analyze this Special Investigation Report and respond with a JSON object containing exactly two fields: (1) 'summary' - a few sentences explaining what went down, including one sentence weighing in on culpability, and (2) 'violation' - either 'y' if allegations of policy/code violations were substantiated, or 'n' if they were not substantiated."*

This generates concise incident summaries with clear responsibility assessments and violation status.

### Usage

**Note**: Run from the `pdf_parsing/` directory.

#### Basic Usage

Show a random Special Investigation Report (default):

```bash
python3 investigate_violations.py
```

#### Filter by Category

Show documents from specific categories:

```bash
# Show Special Investigation Reports only (default)
python3 investigate_violations.py --category sir

# Show any document regardless of type
python3 investigate_violations.py --category all
```

### Categories

- **`sir`**: Special Investigation Reports only (default)
- **`all`**: Any document

### Output

The script displays:
- Document metadata (agency ID, name, date, document title)
- Whether it's a Special Investigation Report
- Full document text from the parquet file

This is useful for:
- Verifying that information is being correctly extracted
- Understanding the document structure
- Quality checking the parsing logic

## Complete Workflow

1. **Extract PDF text**: Use `extract_pdf_text.py` to process PDFs and create parquet files
   ```bash
   python3 pdf_parsing/extract_pdf_text.py --pdf-dir /path/to/pdfs
   ```

2. **Extract document info**: Use `extract_document_info.py` to extract basic document information
   ```bash
   python3 pdf_parsing/extract_document_info.py
   ```

3. **Update SIR summaries**: Use `update_summaryqueries.py` to generate AI summaries for SIRs
   ```bash
   cd pdf_parsing
   export OPENROUTER_KEY="your-api-key"
   python3 update_summaryqueries.py
   ```

4. **Investigate results**: Use `investigate_violations.py` to inspect random documents
   ```bash
   cd pdf_parsing
   python3 investigate_violations.py
   ```

5. **Analyze results**: Use the CSV outputs for analysis, reporting, or further processing

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

