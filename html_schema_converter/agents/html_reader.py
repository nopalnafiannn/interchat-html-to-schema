"""HTML Reader Agent for extracting tables from HTML content."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Union
import os
import csv
import pandas as pd

from html_schema_converter.config import config

class HTMLReader:
    """Agent for extracting tables from HTML content."""
    
    def __init__(self, sample_rows: int = 5):
        """
        Initialize the HTML reader.
        
        Args:
            sample_rows: Number of sample rows to extract from tables
        """
        self.sample_rows = sample_rows
        self.max_file_size_mb = config.get("html_reader.max_file_size_mb", 10)
        self.detect_implicit_tables = config.get("html_reader.table_detection.detect_implicit_tables", True)
        self.search_div_classes = config.get("html_reader.table_detection.search_div_classes", True)
    
    def read_from_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch HTML from a URL and extract tables.
        
        Args:
            url: URL to fetch HTML from
            
        Returns:
            Dictionary with table information
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.content
            return self._extract_tables(content)
        except Exception as e:
            return {"status": f"Error: {str(e)}", "tables_count": 0}
    
    def read_from_file(self, file_path: str) -> Dict[str, Any]:
        """
        Read HTML from a file and extract tables.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Dictionary with table information
        """
        try:
            # Check file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                return {
                    "status": f"Error: File size ({file_size_mb:.2f} MB) exceeds maximum ({self.max_file_size_mb} MB)",
                    "tables_count": 0
                }
            
            # Check if it's a CSV file with schema description format
            if file_path.endswith('.csv'):
                return self._extract_schema_from_csv(file_path)
                
            with open(file_path, 'rb') as f:
                content = f.read()
            return self._extract_tables(content)
        except Exception as e:
            return {"status": f"Error: {str(e)}", "tables_count": 0}
    
    def _extract_tables(self, content: bytes) -> Dict[str, Any]:
        """
        Extract tables from HTML content.
        
        Args:
            content: HTML content as bytes
            
        Returns:
            Dictionary with table information
        """
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')
        
        # If no standard tables found, look for div-based tables if enabled
        if not tables and self.detect_implicit_tables:
            if self.search_div_classes:
                possible_tables = soup.find_all('div', class_=lambda c: c and ('table' in c.lower() or 'grid' in c.lower()))
                if possible_tables:
                    tables = possible_tables
        
        if not tables:
            return {"status": "No tables found", "tables_count": 0}
        
        tables_info = []
        for i, table in enumerate(tables):
            table_info = self._extract_table_info(table, i)
            tables_info.append(table_info)
        
        return {
            "status": "Success", 
            "tables_count": len(tables), 
            "tables": tables_info
        }
    
    def _extract_table_info(self, table: BeautifulSoup, table_id: int) -> Dict[str, Any]:
        """
        Extract information from a single table.
        
        Args:
            table: BeautifulSoup object representing a table
            table_id: ID to assign to the table
            
        Returns:
            Dictionary with table information
        """
        # Check for vertically structured tables like in AdventureWorks documentation
        # These often have 2 columns with property names in first column and values in second
        is_vertical_structure = self._detect_vertical_table_structure(table)
        
        if is_vertical_structure:
            # Process as a vertical property-value table
            headers, sample_data = self._extract_vertical_table(table)
        else:
            # Extract headers normally
            headers = self._extract_headers(table)
            
            # Handle duplicate headers by appending index to duplicates
            seen_headers = {}
            unique_headers = []
            for i, header in enumerate(headers):
                if header in seen_headers:
                    seen_headers[header] += 1
                    unique_headers.append(f"{header}_{seen_headers[header]}")
                else:
                    seen_headers[header] = 0
                    unique_headers.append(header)
            
            # Extract sample data normally
            sample_data = self._extract_sample_data(table, unique_headers)
            headers = unique_headers
        
        # Extract caption or context
        caption = self._extract_caption(table)
        
        return {
            "table_id": table_id,
            "caption": caption,
            "column_count": len(headers),
            "row_count": len(sample_data),
            "headers": headers,
            "sample_data": sample_data,
            "is_vertical_structure": is_vertical_structure
        }
    
    def _extract_headers(self, table: BeautifulSoup) -> List[str]:
        """
        Extract column headers from a table.
        
        Args:
            table: BeautifulSoup object representing a table
            
        Returns:
            List of header texts
        """
        headers = []
        
        # Try to find headers in th tags
        th_tags = table.find_all('th')
        if th_tags:
            headers = [th.get_text(strip=True) for th in th_tags]
        
        # If no headers found, try thead > tr
        if not headers and table.find('thead'):
            thead = table.find('thead')
            header_row = thead.find('tr')
            if header_row:
                headers = [td.get_text(strip=True) for td in header_row.find_all(['td', 'th'])]
        
        # If still no headers, use first row
        if not headers and table.find_all('tr'):
            rows = table.find_all('tr')
            if rows:
                first_row_cells = rows[0].find_all(['td', 'th'])
                if first_row_cells:
                    headers = [td.get_text(strip=True) for td in first_row_cells]
        
        # For div-based tables
        if not headers and self.search_div_classes:
            header_divs = table.find_all('div', class_=lambda c: c and 'header' in c.lower())
            if header_divs:
                headers = [div.get_text(strip=True) for div in header_divs]
        
        return headers
    
    def _extract_sample_data(self, table: BeautifulSoup, headers: List[str]) -> List[List[str]]:
        """
        Extract sample data rows from a table.
        
        Args:
            table: BeautifulSoup object representing a table
            headers: List of column headers
            
        Returns:
            List of data rows
        """
        sample_data = []
        
        # Regular table rows
        rows = table.find_all('tr')
        if rows:
            start_index = 1 if headers and len(rows) > 1 else 0
            for row in rows[start_index: min(start_index + self.sample_rows, len(rows))]:
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_data = [cell.get_text(strip=True) for cell in cells]
                    if any(cell.strip() for cell in row_data):
                        sample_data.append(row_data)
        
        # Div-based table rows
        if not sample_data and self.search_div_classes:
            row_divs = table.find_all('div', class_=lambda c: c and 'row' in c.lower())
            for row_div in row_divs[:self.sample_rows]:
                cell_divs = row_div.find_all('div', class_=lambda c: c and ('cell' in c.lower() or 'col' in c.lower()))
                if cell_divs:
                    row_data = [cell.get_text(strip=True) for cell in cell_divs]
                    if any(cell.strip() for cell in row_data):
                        sample_data.append(row_data)
        
        return sample_data
    
    def _detect_vertical_table_structure(self, table: BeautifulSoup) -> bool:
        """
        Detect if a table is structured vertically (property-value table) like in AdventureWorks docs.
        
        Args:
            table: BeautifulSoup object representing a table
            
        Returns:
            True if table appears to be a vertical property-value structure, False otherwise
        """
        rows = table.find_all('tr')
        if not rows or len(rows) < 2:
            print("DEBUG: Table has fewer than 2 rows, not a vertical structure")
            return False
            
        # Check first few rows to see if they look like property-value pairs
        # Typically these have 2 columns, with first column containing property names
        property_value_indicators = 0
        rows_to_check = min(5, len(rows))
        
        print(f"DEBUG: Checking {rows_to_check} rows for vertical structure detection")
        
        for i in range(rows_to_check):
            cells = rows[i].find_all(['td', 'th'])
            
            # Property-value tables typically have 2 columns
            if len(cells) == 2:
                # First cell often contains property names like "Name", "Description", "Type", etc.
                first_cell_text = cells[0].get_text(strip=True)
                second_cell_text = cells[1].get_text(strip=True)
                
                print(f"DEBUG: Row {i+1} - First cell: '{first_cell_text}', Second cell: '{second_cell_text}'")
                
                # Check if first cell looks like a property name - usually short and ends with ":"
                if (len(first_cell_text) < 30 and 
                    (first_cell_text.endswith(':') or 
                     first_cell_text.lower() in [
                         'name', 'type', 'description', 'id', 'key', 'column', 'property',
                         'attribute', 'field', 'constraint', 'value', 'default', 'null',
                         'nullable', 'required', 'format', 'length', 'min', 'max'
                     ])):
                    property_value_indicators += 1
                    print(f"DEBUG: Row {i+1} identified as a property-value pair")
            else:
                print(f"DEBUG: Row {i+1} has {len(cells)} cells, not a typical property-value structure")
        
        # If most of the checked rows look like property-value pairs, consider it vertical
        is_vertical = property_value_indicators >= (rows_to_check // 2)
        print(f"DEBUG: Vertical table detection result: {is_vertical} (indicators: {property_value_indicators}/{rows_to_check})")
        return is_vertical
        
    def _extract_vertical_table(self, table: BeautifulSoup) -> tuple:
        """
        Extract data from a vertical property-value table structure.
        
        Args:
            table: BeautifulSoup object representing a table
            
        Returns:
            Tuple of (headers, sample_data) with headers being property names and
            sample_data containing corresponding values
        """
        rows = table.find_all('tr')
        property_names = []
        property_values = []
        
        print(f"DEBUG: Extracting data from vertical table with {len(rows)} rows")
        
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                # First cell is the property name
                prop_name = cells[0].get_text(strip=True)
                # Remove trailing colon if present
                if prop_name.endswith(':'):
                    prop_name = prop_name[:-1].strip()
                    
                # Second cell is the property value
                prop_value = cells[1].get_text(strip=True)
                
                print(f"DEBUG: Extracted row {i+1}: Property '{prop_name}' = '{prop_value}'")
                property_names.append(prop_name)
                property_values.append(prop_value)
        
        print(f"DEBUG: Extracted {len(property_names)} property-value pairs")
        
        # For schema generation, we want the property names to be the headers (column names)
        # and the property values to be the sample data
        print(f"DEBUG: Using property names as headers: {property_names[:5]}")
        print(f"DEBUG: Using property values as sample data: {property_values[:5]}")
        
        # Create a single row containing all the values
        # This format fits with how the schema generator expects data
        return property_names, [property_values]
        
    def _extract_caption(self, table: BeautifulSoup) -> str:
        """
        Extract caption or context for a table.
        
        Args:
            table: BeautifulSoup object representing a table
            
        Returns:
            Caption text
        """
        caption = ""
        
        # Check for preceding headers
        if table.find_previous('h1'):
            caption = table.find_previous('h1').get_text(strip=True)
        elif table.find_previous('h2'):
            caption = table.find_previous('h2').get_text(strip=True)
        elif table.find_previous('h3'):
            caption = table.find_previous('h3').get_text(strip=True)
        
        # Check for table caption
        elif table.find('caption'):
            caption = table.find('caption').get_text(strip=True)
        
        return caption
        
    def _extract_schema_from_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Extract table information from a CSV file that contains database schema information.
        
        Args:
            file_path: Path to the CSV file
            
        Returns:
            Dictionary with table information in a format suitable for schema generation
        """
        try:
            # Read the CSV file directly - some schema exports have irregular headers
            # that pandas might struggle with
            rows = []
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                csv_reader = csv.reader(f)
                for row in csv_reader:
                    rows.append(row)
                    
            if not rows:
                return {"status": "Error: Empty CSV file", "tables_count": 0}
                
            # Extract headers from the first row
            headers = rows[0] if rows else []
            print(f"DEBUG: CSV headers: {headers}")
            
            # Check if this looks like a schema description CSV with database table columns
            # Looking for headers like _1, Key, Name, Data type, Null, Attributes, References, Description
            schema_header_terms = ['key', 'name', 'data type', 'null', 'attributes', 'references', 'description']
            
            # Check for schema format by looking for common schema header terms
            header_texts = [h.lower() if h else '' for h in headers]
            schema_matches = sum(1 for term in schema_header_terms if any(term in h for h in header_texts))
            is_schema_format = schema_matches >= 1  # If at least 1 schema header term is found - less strict
            
            # Special case for empty/weird headers but content matches schema format
            if not is_schema_format and len(rows) > 1:
                # Check if second row has typical schema content (looking for int, varchar, etc.)
                second_row = rows[1]
                data_type_patterns = ['int', 'varchar', 'char', 'text', 'date', 'time', 'float', 'decimal']
                if any(pattern in str(cell).lower() for cell in second_row for pattern in data_type_patterns):
                    print(f"DEBUG: Schema format detected from data type patterns in row content")
                    is_schema_format = True
            
            if is_schema_format:
                print(f"DEBUG: Detected schema format CSV")
                
                # For schema format, we'll process it as a structured table definition
                # with column definitions as rows
                
                # First, try to identify the key columns based on headers or position
                name_idx = next((i for i, h in enumerate(header_texts) if 'name' in h), None)
                if name_idx is None or header_texts[name_idx] == '':
                    # Try to find by position - usually the 3rd or 4th column 
                    name_idx = 3 if len(headers) > 3 else 0
                
                datatype_idx = next((i for i, h in enumerate(header_texts) if 'type' in h or 'data' in h), None)
                if datatype_idx is None:
                    # Try to find by position - usually the 4th or 5th column
                    datatype_idx = 4 if len(headers) > 4 else 1
                
                key_idx = next((i for i, h in enumerate(header_texts) if 'key' in h), None)
                null_idx = next((i for i, h in enumerate(header_texts) if 'null' in h), None)
                ref_idx = next((i for i, h in enumerate(header_texts) if 'ref' in h), None)
                desc_idx = next((i for i, h in enumerate(header_texts) if 'desc' in h), None)
                
                print(f"DEBUG: Column indexes - name:{name_idx}, datatype:{datatype_idx}, key:{key_idx}, null:{null_idx}, ref:{ref_idx}, desc:{desc_idx}")
                
                # Prepare properties and values for each column in the table
                property_names = []
                property_values = []
                
                # Process each row (after header) as a column definition
                for row in rows[1:]:
                    if not row or len(row) < max(filter(None, [name_idx, datatype_idx])) + 1:
                        continue  # Skip rows that don't have enough cells
                        
                    column_name = row[name_idx].strip() if name_idx is not None and name_idx < len(row) else ""
                    if not column_name:
                        continue  # Skip rows without a column name
                    
                    # Add the main column properties
                    property_names.append('Column Name')
                    property_values.append(column_name)
                    
                    if datatype_idx is not None and datatype_idx < len(row):
                        datatype = row[datatype_idx].strip()
                        if datatype:
                            property_names.append('Data Type')
                            property_values.append(datatype)
                    
                    if key_idx is not None and key_idx < len(row):
                        key_value = row[key_idx].strip()
                        if key_value:
                            property_names.append('Key')
                            property_values.append(key_value)
                    
                    if null_idx is not None and null_idx < len(row):
                        null_value = row[null_idx].strip()
                        property_names.append('Nullable')
                        property_values.append(null_value if null_value else "Yes")
                    
                    if ref_idx is not None and ref_idx < len(row):
                        ref_value = row[ref_idx].strip()
                        if ref_value:
                            property_names.append('References')
                            property_values.append(ref_value)
                    
                    if desc_idx is not None and desc_idx < len(row):
                        desc_value = row[desc_idx].strip()
                        if desc_value:
                            property_names.append('Description')
                            property_values.append(desc_value)
                
                # Add any other useful properties that might help with schema generation
                for row in rows[1:]:
                    for i, cell in enumerate(row):
                        if i not in [name_idx, datatype_idx, key_idx, null_idx, ref_idx, desc_idx] and cell.strip():
                            if i < len(headers) and headers[i].strip():
                                property_names.append(headers[i])
                                property_values.append(cell.strip())
                
                print(f"DEBUG: Extracted {len(property_names)} property-value pairs")
                
                # Create a table info structure with vertical format flag
                return {
                    "status": "Success",
                    "tables_count": 1,
                    "tables": [
                        {
                            "table_id": 0,
                            "caption": "Database Schema",
                            "column_count": len(headers),
                            "row_count": len(rows) - 1,  # Exclude header
                            "headers": headers,
                            "sample_data": rows[1:self.sample_rows+1],
                            "is_vertical_structure": False,  # Changed to False to ensure headers are used directly
                            "property_names": property_names,
                            "property_values": property_values,
                            "original_headers": headers
                        }
                    ]
                }
            else:
                # Standard CSV format - read as a normal table
                headers = rows[0] if rows else []
                sample_data = rows[1:self.sample_rows+1] if len(rows) > 1 else []
                
                return {
                    "status": "Success",
                    "tables_count": 1,
                    "tables": [
                        {
                            "table_id": 0,
                            "caption": os.path.basename(file_path),
                            "column_count": len(headers),
                            "row_count": len(sample_data),
                            "headers": headers,
                            "sample_data": sample_data,
                            "is_vertical_structure": False
                        }
                    ]
                }
                
        except Exception as e:
            print(f"DEBUG: Error processing CSV file: {str(e)}")
            # Fallback to standard CSV reading
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    csv_reader = csv.reader(f)
                    rows = list(csv_reader)
                
                if not rows:
                    return {"status": "Error: Empty CSV file", "tables_count": 0}
                    
                headers = rows[0]
                sample_data = rows[1:self.sample_rows+1]
                
                return {
                    "status": "Success",
                    "tables_count": 1,
                    "tables": [
                        {
                            "table_id": 0,
                            "caption": os.path.basename(file_path),
                            "column_count": len(headers),
                            "row_count": len(sample_data),
                            "headers": headers,
                            "sample_data": sample_data,
                            "is_vertical_structure": False
                        }
                    ]
                }
            except Exception as fallback_error:
                return {"status": f"Error: {str(fallback_error)}", "tables_count": 0}