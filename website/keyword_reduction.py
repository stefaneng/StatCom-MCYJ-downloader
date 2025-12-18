#!/usr/bin/env python3
"""
Utility functions for applying keyword reduction to violation data.

This module provides functions to load keyword reduction mappings from CSV
and apply them to keyword lists in violation data.
"""

import csv
import os
from typing import Dict, List


def load_keyword_reduction_map(csv_path: str) -> Dict[str, str]:
    """
    Load keyword reduction mappings from CSV.
    
    Args:
        csv_path: Path to the violation_curation_keyword_reduction.csv file
        
    Returns:
        Dictionary mapping original_keyword to reduced_keyword.
        Empty string values indicate the keyword should be discarded.
    """
    keyword_map = {}
    
    if not os.path.exists(csv_path):
        print(f"Warning: Keyword reduction file not found: {csv_path}")
        return keyword_map
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            original = row.get('original_keyword', '').strip()
            reduced = row.get('reduced_keyword', '').strip()
            # Load mapping even if reduced is empty (empty = discard keyword)
            # Only load if original is not empty string
            if original != '':
                keyword_map[original] = reduced
    
    print(f"Loaded {len(keyword_map)} keyword reduction mappings")
    return keyword_map


def apply_keyword_reduction(keywords: List[str], keyword_map: Dict[str, str]) -> List[str]:
    """
    Apply keyword reduction to a list of keywords.
    
    Args:
        keywords: List of original keywords
        keyword_map: Dictionary mapping original_keyword to reduced_keyword.
                    Empty string values cause the keyword to be discarded.
        
    Returns:
        List of reduced keywords (with duplicates removed, preserving order).
        Keywords mapped to empty string are discarded.
    """
    if not keyword_map:
        return keywords
    
    reduced_keywords = []
    seen = set()
    
    for keyword in keywords:
        # Apply reduction if mapping exists, otherwise keep original
        reduced = keyword_map.get(keyword, keyword)
        
        # Discard keywords mapped to empty string
        if reduced == '':
            continue
        
        # Add to result list only if not already seen (removes duplicates)
        if reduced not in seen:
            reduced_keywords.append(reduced)
            seen.add(reduced)
    
    return reduced_keywords
