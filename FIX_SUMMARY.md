# Violation Parsing Fix Summary

## Overview

Fixed a critical bug in `parse_parquet_violations.py` that caused incorrect violation detection when multiple rules were present in a single document.

## The Problem

**SHA256:** `6e5b899cf078b4bf0829e4dce8113aaac61edfa5bc0958efa725ae8607008f68`  
**Document:** Special Investigation Report #2024C0001157SI  
**Agency:** Lotus Treatment Program (License #: CI411000929)

### Before Fix:
- **Violations Detected:** 2
  1. ✗ Rule 400.4158 Intervention standards and prohibitions (INCORRECT)
  2. ✓ Rule 400.4109 Program Statement (CORRECT)

### After Fix:
- **Violations Detected:** 1
  1. ✓ Rule 400.4109 Program Statement (CORRECT)

## Root Cause

The `extract_violations()` function searched up to 50,000 characters ahead from each "Rule Code & CCI Rule" pattern to find conclusions. When multiple rules appeared in a document, this caused the conclusion from a later rule to be incorrectly matched to an earlier rule.

Specifically:
- Rule 400.4158 had conclusion: "Violation Not Established"
- Rule 400.4109 had conclusion: "Repeat Violation Established"
- The search from Rule 400.4158 found BOTH conclusions and matched the second one

## The Fix

Modified `extract_violations()` in `parse_parquet_violations.py` (lines 214-250):

```python
# OLD (BUGGY):
rule_matches = re.finditer(rule_pattern, text, re.IGNORECASE)
for match in rule_matches:
    start_pos = match.start()
    end_pos = min(start_pos + 50000, len(text))  # Searches too far!
    context = text[start_pos:end_pos]

# NEW (FIXED):
rule_matches = list(re.finditer(rule_pattern, text, re.IGNORECASE))
for i, match in enumerate(rule_matches):
    start_pos = match.start()
    # Limit search to current rule section by finding next rule boundary
    if i + 1 < len(rule_matches):
        end_pos = rule_matches[i + 1].start()  # Stop at next rule
    else:
        end_pos = min(start_pos + 50000, len(text))
    context = text[start_pos:end_pos]
```

## Impact

- **Documents Processed:** 3,510
- **Documents with Violations:** 2,212
- **Fix Applied:** The parsing now correctly scopes conclusion searches to individual rule sections

## Tools Added

### 1. `investigate_sha.py`
A new command-line tool to investigate specific documents by SHA256 hash:

```bash
python3 investigate_sha.py <sha256>
```

Features:
- Displays parsed violation information
- Shows original document text from parquet files
- Useful for debugging and verification

### 2. `DISCREPANCY_REPORT.md`
Detailed documentation of the discrepancy found and the fix applied.

## Verification

```bash
# Test the specific SHA
python3 investigate_sha.py 6e5b899cf078b4bf0829e4dce8113aaac61edfa5bc0958efa725ae8607008f68

# Run full parsing with fix
python3 parse_parquet_violations.py --parquet-dir pdf_parsing/parquet_files -o violations_output_fixed.csv
```

## Testing Recommendations

1. Compare violation counts before/after fix for all documents
2. Look for cases where violation counts decreased (likely false positives fixed)
3. Verify documents with multiple rules are parsed correctly
4. Pay special attention to documents where:
   - First rule: "Violation Not Established"
   - Second rule: "Violation Established"

## Related Files

- `parse_parquet_violations.py` - Fixed violation parsing logic
- `investigate_sha.py` - New investigation tool
- `DISCREPANCY_REPORT.md` - Detailed discrepancy analysis
- `README.md` - Updated documentation
