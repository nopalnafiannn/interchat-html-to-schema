"""HTML Reader Agent for extracting tables from HTML content."""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional, Union
import os

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
        # Extract headers
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
        
        # Extract sample data
        sample_data = self._extract_sample_data(table, unique_headers)
        
        # Extract caption or context
        caption = self._extract_caption(table)
        
        return {
            "table_id": table_id,
            "caption": caption,
            "column_count": len(unique_headers),
            "row_count": len(sample_data),
            "headers": unique_headers,
            "sample_data": sample_data
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