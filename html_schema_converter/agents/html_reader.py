"""HTML Reader Agent for extracting table data from HTML files."""

import requests
from bs4 import BeautifulSoup

def html_reader_agent(url):
    """
    Fetches HTML content from a URL and analyzes tables within it.
    Returns information about tables found in the HTML.
    
    Args:
        url (str): URL to fetch HTML from
        
    Returns:
        dict: Information about tables in the HTML
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        tables = soup.find_all('table')
        if not tables:
            possible_tables = soup.find_all('div', class_=lambda c: c and ('table' in c.lower() or 'grid' in c.lower()))
            if possible_tables:
                tables = possible_tables
        if not tables:
            return {"status": "No tables found", "tables_count": 0}

        tables_info = []
        for i, table in enumerate(tables):
            # Extract headers
            headers = []
            th_tags = table.find_all('th')
            if th_tags:
                headers = [th.get_text(strip=True) for th in th_tags]
            if not headers and table.find('thead'):
                thead = table.find('thead')
                header_row = thead.find('tr')
                if header_row:
                    headers = [td.get_text(strip=True) for td in header_row.find_all(['td', 'th'])]
            
            # Get rows first to handle the case where we check first row for headers
            rows = table.find_all('tr')
            
            if not headers and rows:
                first_row_cells = rows[0].find_all(['td', 'th'])
                if first_row_cells:
                    headers = [td.get_text(strip=True) for td in first_row_cells]
            if not headers and table.find_all('div', class_=lambda c: c and 'header' in c.lower()):
                header_divs = table.find_all('div', class_=lambda c: c and 'header' in c.lower())
                headers = [div.get_text(strip=True) for div in header_divs]
            
            # Extract sample data
            sample_data = []
            if rows:
                start_index = 1 if headers and len(rows) > 1 else 0
                for row in rows[start_index: min(start_index+5, len(rows))]:
                    cells = row.find_all(['td', 'th'])
                    if cells:
                        row_data = [cell.get_text(strip=True) for cell in cells]
                        if any(cell.strip() for cell in row_data):
                            sample_data.append(row_data)
            if not sample_data and table.find_all('div', class_=lambda c: c and 'row' in c.lower()):
                row_divs = table.find_all('div', class_=lambda c: c and 'row' in c.lower())
                for row_div in row_divs[:5]:
                    cell_divs = row_div.find_all('div', class_=lambda c: c and ('cell' in c.lower() or 'col' in c.lower()))
                    if cell_divs:
                        row_data = [cell.get_text(strip=True) for cell in cell_divs]
                        if any(cell.strip() for cell in row_data):
                            sample_data.append(row_data)
            
            # Extract caption/context
            caption = ""
            if table.find_previous('h1'):
                caption = table.find_previous('h1').get_text(strip=True)
            elif table.find_previous('h2'):
                caption = table.find_previous('h2').get_text(strip=True)
            elif table.find_previous('h3'):
                caption = table.find_previous('h3').get_text(strip=True)
            elif table.find('caption'):
                caption = table.find('caption').get_text(strip=True)
            
            tables_info.append({
                "table_id": i,
                "caption": caption,
                "column_count": len(headers),
                "row_count": len(sample_data),
                "headers": headers,
                "sample_data": sample_data
            })
        return {"status": "Success", "tables_count": len(tables), "tables": tables_info}
    except Exception as e:
        return {"status": f"Error: {str(e)}", "tables_count": 0}

def extract_schema_from_table(table_info):
    """
    Extracts headers and sample_data from the selected table.
    
    Args:
        table_info (dict): Table information
        
    Returns:
        dict: Extracted schema data
    """
    headers = table_info.get('headers', [])
    rows = table_info.get('sample_data', [])
    if not headers or not rows:
        return {"status": "No data found", "schema_data": []}
    return {"status": "Success", "original_headers": headers, "schema_data": rows}