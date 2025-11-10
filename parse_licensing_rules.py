import pdfplumber
import argparse

def extract_text_from_pdf(pdf_path: str) -> list[str]:
    """Extract text from PDF, returning a list of strings (one per page)."""
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            pages_text.append(text)
    return pages_text


def parse_rules_from_pages(pages_text: list[str]) -> dict:
    """Combine page texts and split into rules.

    Rules are identified by an uppercase 'R' followed by a rule number, e.g.
    'R 400.4120'. This function returns a dictionary mapping the rule number
    string (without the leading 'R' and any surrounding whitespace) to the
    corresponding rule text (including the header line beginning with 'R ...').

    Args:
        pages_text: list of page text strings (as returned by extract_text_from_pdf)

    Returns:
        dict: { '400.4120': 'R 400.4120 ... full rule text', ... }
    """
    import re

    # Clean page-level footers (e.g., "Page 1" and "Courtesy of Michigan Administrative Rules")
    cleaned_pages = []
    for p in pages_text:
        if not p:
            continue
        # Remove footer lines that appear alone on a page
        p2 = re.sub(r'(?m)^\s*Page\s*\d+\s*$', '', p)
        p2 = re.sub(r'(?m)^\s*Courtesy of Michigan Administrative Rules\s*$', '', p2)
        # Collapse multiple blank lines to max two
        p2 = re.sub(r'\n{3,}', '\n\n', p2)
        cleaned_pages.append(p2.strip())

    # Join cleaned pages with newlines to avoid accidental word joins at page boundaries
    full_text = "\n".join(cleaned_pages)

    # Pattern: an R-rule header at the start of a line, e.g.:
    #   R 400.4103 Space and equipment requirements.
    # Require the header to be at the start of a line and to contain a period
    # on the same line so we don't treat inline references like "R 400.4510." as headers.
    rule_re = re.compile(r"(?m)^[ \t]*R\s*(\d+\.\d+)\b[^\n]*\.")

    matches = list(rule_re.finditer(full_text))
    rules = {}

    if not matches:
        return rules

    def split_by_token(text: str, token_pattern: str):
        """Split text by occurrences of token_pattern (a regex matching the token like '(1)' or '(a)').

        Returns a list of dicts: { 'id': token_without_parens, 'text': content_after_token }
        """
        parts = []
        token_re = re.compile(token_pattern)
        matches2 = list(token_re.finditer(text))
        if not matches2:
            return None
        for j, mm in enumerate(matches2):
            tid = mm.group(0)
            key = re.sub(r'[()\s]', '', tid)
            start2 = mm.end()
            end2 = matches2[j+1].start() if j+1 < len(matches2) else len(text)
            content2 = text[start2:end2].strip()
            parts.append({'id': key, 'text': content2})
        return parts

    for i, m in enumerate(matches):
        rule_num = m.group(1)
        start = m.start()
        end = matches[i+1].start() if i + 1 < len(matches) else len(full_text)
        rule_text_raw = full_text[start:end].strip()

        # Remove leading 'R <number>' from the rule text
        rule_text = re.sub(r'^\s*R\s*\d+\.\d+\s*', '', rule_text_raw).strip()

        # Extract the header line from the match and remove the leading 'R <num>'
        header_line = m.group(0)
        # Remove leading R and number, and trailing period
        header_rest = re.sub(r"^\s*R\s*\d+\.\d+\s*", "", header_line).strip()
        if header_rest.endswith('.'):
            header_rest = header_rest[:-1].strip()
        rule_name = header_rest

        # Try to find a 'Rule <number>' label inside the original raw text (preferred)
        rule_label_match = re.search(r"\bRule\s+(\d+)\b", rule_text_raw)
        if rule_label_match:
            rule_label = f"Rule {rule_label_match.group(1)}"
        else:
            tail = rule_num.split('.')[-1]
            rule_label = f"Rule {tail}"

        # Extract History: ... (if present) and remove from rule text
        history = None
        hist_match = re.search(r"History:\s*(.+?\.)", rule_text, flags=re.S)
        if hist_match:
            # store the part after 'History:' (without the label)
            history = hist_match.group(1).strip()
            # remove the history segment from the rule text
            rule_text = (rule_text[:hist_match.start()] + rule_text[hist_match.end():]).strip()

        # Parse rule conditions (numeric subrules (1), then lettered (a), then roman (i))
        conditions = []

        # First attempt: numeric subrules like (1), (2)
        numeric_parts = split_by_token(rule_text, r"\(\d+\)")
        if numeric_parts:
            for np in numeric_parts:
                # For each numeric part, look for lettered subparts (a), (b)
                letter_parts = split_by_token(np['text'], r"\([a-z]\)")
                if letter_parts:
                    # Possibly look for roman numerals inside each letter part
                    for lp in letter_parts:
                        roman_parts = split_by_token(lp['text'], r"\([ivxlcdm]+\)")
                        if roman_parts:
                            lp['sub'] = roman_parts
                    np['sub'] = letter_parts
                else:
                    # No lettered parts; also check for roman numerals directly
                    roman_parts = split_by_token(np['text'], r"\([ivxlcdm]+\)")
                    if roman_parts:
                        np['sub'] = roman_parts
                conditions.append({'id': np['id'], 'text': np['text'], 'sub': np.get('sub')})
        else:
            # No numeric parts: try lettered parts at top level
            letter_parts_top = split_by_token(rule_text, r"\([a-z]\)")
            if letter_parts_top:
                for lp in letter_parts_top:
                    # Look for roman numerals inside each letter part
                    roman_parts = split_by_token(lp['text'], r"\([ivxlcdm]+\)")
                    if roman_parts:
                        lp['sub'] = roman_parts
                    conditions.append({'id': lp['id'], 'text': lp['text'], 'sub': lp.get('sub')})

        rules[rule_num] = {
            'text': rule_text,
            'rule_name': rule_name,
            'rule_label': rule_label,
            'conditions': conditions,
            'History': history
        }

    return rules


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse licensing rules PDF into structured JSON")
    parser.add_argument('pdf_path', help='Path to the PDF file to parse')
    parser.add_argument('--out', dest='out_path', default='RulesData/parsed_rules.json', help='Output JSON file path')
    args = parser.parse_args()

    pdf_path = args.pdf_path
    pages_text = extract_text_from_pdf(pdf_path)
    # Parse rules into a dict keyed by rule number (without 'R')
    rules = parse_rules_from_pages(pages_text)

    # Basic output: print count and first few keys
    print(f"Extracted {len(rules)} rules")
    for k in list(rules.keys())[:10]:
        print(k)

    # Optionally save to JSON for downstream use
    try:
        import json
        out_path = args.out_path
        with open(out_path, "w", encoding="utf-8") as outf:
            json.dump(rules, outf, indent=2, ensure_ascii=False)
        print(f"Wrote parsed rules to {out_path}")
    except Exception as e:
        print(f"Failed to write parsed rules: {e}")
