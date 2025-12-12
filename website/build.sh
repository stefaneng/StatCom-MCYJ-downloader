#!/bin/bash

# Build script for generating website data and building the site

set -e  # Exit on error

echo "==> Step 0: Installing Python dependencies with pip..."
# Install dependencies from pyproject.toml
cd ..
pip install -e .
cd website

echo ""
echo "==> Step 1: Generating violations CSV from parquet files..."
python3 ../parse_parquet_violations.py \
  --parquet-dir ../pdf_parsing/parquet_files \
  -o ../violations_output.csv

echo ""
echo "==> Step 2: Generating JSON data for website..."
python3 generate_website_data.py \
  --violations-csv ../violations_output.csv \
  --output-dir public/data

echo ""
echo "==> Step 2.5: Exporting parquet documents to individual JSON files..."
python3 export_parquet_to_json.py \
  --parquet-dir ../pdf_parsing/parquet_files \
  --output-dir public/documents \
  --violations-csv ../violations_output.csv

echo ""
echo "==> Step 3: Building website with Vite..."
npm run build

echo ""
echo "==> Build complete! Output is in dist/"
