# Violation Parsing Discrepancy Report

## SHA: 6e5b899cf078b4bf0829e4dce8113aaac61edfa5bc0958efa725ae8607008f68

**Date:** December 12, 2025  
**Document:** Special Investigation Report #2024C0001157SI  
**Agency:** Lotus Treatment Program (License #: CI411000929)

## Summary

The violation parsing script (`parse_parquet_violations.py`) incorrectly identifies **2 violations** for this document when there should only be **1 violation**.

## Discrepancy Details

### What the Parser Found:
1. ✗ **Rule 400.4158** - Intervention standards and prohibitions (INCORRECTLY IDENTIFIED)
2. ✓ **Rule 400.4109** - Program Statement (CORRECTLY IDENTIFIED)

### What the Document Actually Contains:

#### Rule 400.4158 - Intervention standards and prohibitions
- **Actual Conclusion:** "Violation Not Established"
- **Analysis:** "Based on interviews conducted and documentation reviewed, there is no violation established."
- **Status:** NOT VIOLATED

#### Rule 400.4109 - Program Statement
- **Actual Conclusion:** "Repeat Violation Established"
- **Analysis:** "Based on interviews conducted and documentation reviewed, this violation is established."
- **Status:** VIOLATED (with 2 prior violations cited)

## Root Cause

The parsing script has a logic flaw in the `extract_violations()` function (lines 214-294 in `parse_parquet_violations.py`):

1. For each "Rule Code & CCI Rule" pattern found, the script searches up to **50,000 characters ahead** to find a conclusion
2. When searching from Rule 400.4158, the script finds TWO conclusions in that 50,000-character window:
   - First: "Conclusion Violation Not Established" (at ~10,981 chars from start)
   - Second: "Conclusion Repeat Violation Established" (at ~13,357 chars from start)
3. The regex pattern `r'Conclusion\s+(?:Repeat\s+)?Violation Established'` matches the SECOND conclusion (from Rule 400.4109), not the first one
4. This causes Rule 400.4158 to be incorrectly marked as violated

## Technical Details

```python
# Current logic (BUGGY):
for match in rule_matches:
    rule_ref = match.group(1).strip()
    start_pos = match.start()
    end_pos = min(start_pos + 50000, len(text))  # Too large!
    context = full_text[start_pos:end_pos]
    
    # This finds conclusions from OTHER rules!
    if re.search(r'Conclusion\s+(?:Repeat\s+)?Violation Established', context, ...):
        violations.append(f"Rule {rule_ref}")  # WRONG!
```

## Solution

The parsing logic needs to be fixed to:
1. Limit the search window to the CURRENT rule section only (not 50,000 chars)
2. Stop searching when the next "Rule Code" section is encountered
3. Or use a more sophisticated approach to match conclusions to their respective rules

## How to Reproduce

```bash
# 1. Run the investigation script
python3 investigate_sha.py 6e5b899cf078b4bf0829e4dce8113aaac61edfa5bc0958efa725ae8607008f68

# 2. The script will show:
#    - Parsed violations: 2 (INCORRECT)
#    - Expected violations: 1 (Rule 400.4109 only)

# 3. Manually verify by examining the document text
#    - Rule 400.4158 has "Conclusion Violation Not Established"
#    - Rule 400.4109 has "Conclusion Repeat Violation Established"
```

## Impact

This bug causes:
- **False positives**: Rules marked as violated when they are actually not violated
- **Inflated violation counts**: Documents appear to have more violations than they actually do
- **Cross-contamination**: A rule's conclusion can be incorrectly attributed to a previous rule in the same document

This is particularly problematic when:
- Multiple rules are listed in a single document
- The first rule is NOT violated but the second rule IS violated
- The rules are close together (within 50,000 chars)

## Recommendations

1. **Immediate:** Fix the `extract_violations()` function to properly scope conclusion searches to individual rule sections
2. **Verify:** Re-run the parsing on all documents and check for changes in violation counts
3. **Test:** Add test cases for documents with multiple rules where some are violated and others are not
