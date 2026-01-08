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


