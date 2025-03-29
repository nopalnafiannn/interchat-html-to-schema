#!/usr/bin/env python3
"""
Test script for the HTML Dataset Analyzer
----------------------------------------
This script tests the direct column extraction from HTML files
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path to import from src
sys.path.append(str(Path(__file__).parent.parent))

from src.analyzer.html_processor import detect_table_columns_from_html, extract_tables
from src.analyzer.schema_extractor import detect_dataset_type, extract_direct_columns
from src.utils.file_utils import read_file

def test_html_file(file_path):
    """
    Test the column extraction on an HTML file
    
    Args:
        file_path: Path to the HTML file
    """
    print(f"\nTesting file: {file_path}")
    
    # Read the HTML file
    html_content = read_file(file_path)
    if not html_content:
        print(f"Failed to read file: {file_path}")
        return
    
    # Try to detect dataset type
    dataset_type = detect_dataset_type(html_content)
    if dataset_type:
        print(f"Detected dataset type: {dataset_type}")
    else:
        print("No specific dataset type detected")
    
    # Try direct column extraction
    print("\nDirect column extraction:")
    columns = extract_direct_columns(html_content)
    if columns:
        print("Extracted columns:")
        for col in columns:
            print(f"  - {col}")
    else:
        print("No columns extracted directly")
    
    # Try table extraction
    print("\nTable extraction:")
    tables = extract_tables(html_content)
    if tables:
        print(f"Found {len(tables)} tables")
        for i, table in enumerate(tables):
            print(f"\nTable {i+1}:")
            print(f"Headers: {table['headers']}")
            print(f"Row count: {len(table['rows'])}")
            if table['rows']:
                print(f"First row: {table['rows'][0]}")
    else:
        print("No tables found")
    
    # Try column detection
    print("\nColumn detection:")
    columns = detect_table_columns_from_html(html_content)
    if columns:
        print("Detected columns:")
        for col in columns:
            print(f"  - {col}")
    else:
        print("No columns detected")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        test_html_file(file_path)
    else:
        print("Please provide an HTML file path")
        sys.exit(1)