# Michigan Child Welfare Licensing Dashboard

A lightweight web dashboard built with Vite to display Michigan Child Welfare agency documents and reports.  Live [here](https://scintillating-licorice-0dd1c4.netlify.app/).

## Features

- **Agency Directory**: Browse all child welfare agencies
- **Document Tracking**: View detailed document reports for each agency
- **Search & Filter**: Search agencies by name or ID
- **Expandable Details**: Click any agency to view detailed documents
- **Summary Statistics**: Dashboard showing total agencies and reports

## Development

### Prerequisites

- Node.js (v18 or later recommended)
- Python 3.11+
- pandas and pyarrow Python packages

### Local Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Generate the data files:
   ```bash
   ./build.sh
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Open your browser to `http://localhost:5173` (or the port shown in the terminal)

### Building for Production

Run the build script which:
1. Generates document info CSV from parquet files
2. Creates JSON data files from the document info CSV
3. Applies keyword reduction to consolidate violation keywords
4. Builds the static website

```bash
./build.sh
```

The built files will be in the `dist/` directory.

## Netlify Deployment

The site is configured for automatic deployment on Netlify. The build process:

1. Runs `pdf_parsing/extract_document_info.py` to generate document info from parquet files
2. Runs `generate_website_data.py` to create JSON files from document info CSV
3. Applies keyword reduction using `violation_curation_keyword_reduction.csv` to consolidate similar violation keywords
4. Builds the static site with Vite

### Keyword Reduction

The build process applies keyword reduction to consolidate similar violation keywords for better consistency. For example:
- "inadequate supervision" and "lack of supervision" → "supervision failure"
- "unsafe de-escalation" → "de-escalation failure"
- "paperwork delay" → "paperwork error"

This is configured through `pdf_parsing/violation_curation_keyword_reduction.csv` and is automatically applied during the build. The original data in `sir_violation_levels.csv` remains unchanged.

### Netlify Configuration

The `netlify.toml` file configures:
- Build command: `bash build.sh`
- Publish directory: `dist`
- Python version: 3.11
- SPA routing with redirects

## Data Sources

The dashboard uses data from:

- **Parquet Files**: PDF text extracts in `../pdf_parsing/parquet_files/`
- **Document Info CSV**: Generated from parquet files via `pdf_parsing/extract_document_info.py`
- **SIR Violation Levels CSV**: Contains severity levels and keywords for Special Investigation Reports
- **Keyword Reduction CSV**: Maps original keywords to consolidated versions for consistency

The dashboard derives all agency information directly from the document data (no separate facility metadata required).

## Project Structure

```
website/
├── index.html               # Main HTML file
├── src/
│   └── main.js              # JavaScript application logic
├── public/
│   └── data/                # Generated JSON data files (git-ignored)
├── generate_website_data.py # Script to generate JSON from CSVs
├── build.sh                 # Build script for the entire site
├── vite.config.js           # Vite configuration
├── netlify.toml             # Netlify deployment configuration
├── package.json             # Node.js dependencies and scripts
└── README.md                # This file
```

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `./build.sh` - Full build pipeline (data generation + site build)

## Data Generation

To regenerate the data manually:

```bash
# From the website directory
cd website

# Generate document info CSV from parquet files
python3 ../pdf_parsing/extract_document_info.py \
  --parquet-dir ../pdf_parsing/parquet_files \
  -o ../document_info.csv

# Generate JSON files for website (derives agency info from documents)
python3 generate_website_data.py \
  --document-csv ../document_info.csv \
  --output-dir public/data
```

## License

ISC
