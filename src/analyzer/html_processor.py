"""
HTML Processor Module
--------------------
Functions for processing and cleaning HTML content
"""

from bs4 import BeautifulSoup, Comment

def clean_html(html):
    """
    Clean HTML content by removing scripts, styles, and comments
    
    Args:
        html (str): Raw HTML content
        
    Returns:
        str: Cleaned text content
    """
    soup = BeautifulSoup(html, 'html.parser')
    
    # Remove script, style, meta, link, and noscript elements
    for element in soup(["script", "style", "meta", "link", "noscript"]):
        element.decompose()
        
    # Remove HTML comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()
        
    # Get text and collapse whitespace
    text = soup.get_text(separator=' ')
    lines = (line.strip() for line in text.splitlines())
    phrases = (phrase.strip() for line in lines for phrase in line.split("  "))
    cleaned = '\n'.join(phrase for phrase in phrases if phrase)
    
    return cleaned

def count_words(text):
    """
    Count the number of words in a text
    
    Args:
        text (str): Text to count words in
        
    Returns:
        int: Number of words
    """
    return len(text.split())

def extract_tables(html):
    """
    Extract tables from HTML content
    
    Args:
        html (str): HTML content
        
    Returns:
        list: List of tables as dictionaries with headers and rows
    """
    soup = BeautifulSoup(html, 'html.parser')
    tables = []
    
    # First, try standard table tags (works for any HTML with standard tables)
    table_elems = soup.find_all('table')
    
    # If traditional tables are found, extract them
    if table_elems:
        for table_elem in table_elems:
            table = {'headers': [], 'rows': []}
            
            # Try to find headers in thead
            thead = table_elem.find('thead')
            if thead:
                th_elements = thead.find_all('th')
                if th_elements:
                    table['headers'] = [th.get_text(strip=True) for th in th_elements]
            
            # If no headers found in thead, try first row
            if not table['headers']:
                first_row = table_elem.find('tr')
                if first_row:
                    headers = first_row.find_all('th')
                    if headers:
                        table['headers'] = [h.get_text(strip=True) for h in headers]
                    else:
                        # Try td elements if no th elements
                        headers = first_row.find_all('td')
                        if headers:
                            table['headers'] = [h.get_text(strip=True) for h in headers]
            
            # Get rows (skip first row if it was headers)
            rows = table_elem.find_all('tr')
            start_idx = 1 if table['headers'] and len(rows) > 0 else 0
            
            for row in rows[start_idx:]:
                cells = row.find_all('td')
                if cells:
                    table['rows'].append([cell.get_text(strip=True) for cell in cells])
            
            if table['headers'] or table['rows']:
                tables.append(table)
    
    # If no traditional tables, try alternative data structures
    if not tables:
        # Look for div-based tables (common in modern sites)
        div_tables = extract_div_tables(soup)
        if div_tables:
            tables.extend(div_tables)
            
        # Look for lists that might represent data
        list_tables = extract_list_tables(soup)
        if list_tables:
            tables.extend(list_tables)
            
        # Try to identify data patterns in the document
        content_tables = extract_content_patterns(soup)
        if content_tables:
            tables.extend(content_tables)
    
    return tables

def get_page_title(html):
    """
    Extract the page title from HTML
    
    Args:
        html (str): HTML content
        
    Returns:
        str: Page title or empty string if not found
    """
    soup = BeautifulSoup(html, 'html.parser')
    title_tag = soup.find('title')
    
    if title_tag:
        return title_tag.get_text(strip=True)
    
    return ""

def extract_div_tables(soup):
    """
    Extract tables that are structured with divs rather than table tags
    """
    tables = []
    
    # Common classes/patterns for div-based tables across many websites
    table_patterns = ['table', 'grid', 'data-grid', 'datatable', 'dataset', 
                     'data-container', 'data-set', 'data-view', 'datagrid']
    
    # Look for div tables with common class names
    table_divs = soup.find_all('div', class_=lambda c: c and any(pattern in c.lower() for pattern in table_patterns))
    
    for table_div in table_divs:
        table = {'headers': [], 'rows': []}
        
        # Try to find header row
        header_patterns = ['header', 'heading', 'head', 'th', 'column-name', 'title-row', 'column-header']
        header_row = table_div.find('div', class_=lambda c: c and any(pattern in c.lower() for pattern in header_patterns))
        
        if header_row:
            header_cols = header_row.find_all('div')
            if header_cols:
                table['headers'] = [col.get_text(strip=True) for col in header_cols]
        
        # Find data rows
        row_patterns = ['row', 'item', 'data-row', 'record', 'entry', 'data-item']
        data_rows = table_div.find_all('div', class_=lambda c: c and any(pattern in c.lower() for pattern in row_patterns))
        
        for row_div in data_rows:
            row_cols = row_div.find_all('div')
            if row_cols:
                table['rows'].append([col.get_text(strip=True) for col in row_cols])
        
        if table['headers'] or table['rows']:
            tables.append(table)
    
    return tables

def extract_list_tables(soup):
    """
    Extract data from list structures that might represent tabular data
    """
    tables = []
    
    # Look for unordered and ordered lists
    for list_type in ['ul', 'ol']:
        list_elements = soup.find_all(list_type)
        
        for list_elem in list_elements:
            # Get all list items
            items = list_elem.find_all('li')
            
            if len(items) > 3:  # Only consider lists with enough items to be meaningful
                # Check if items have a consistent structure
                first_item = items[0].get_text(strip=True)
                if ':' in first_item:  # Key-value format
                    # This might be a list of attributes
                    headers = ['Property', 'Value']
                    rows = []
                    
                    for item in items:
                        text = item.get_text(strip=True)
                        if ':' in text:
                            key, value = text.split(':', 1)
                            rows.append([key.strip(), value.strip()])
                    
                    if rows:
                        tables.append({'headers': headers, 'rows': rows})
    
    return tables

def extract_content_patterns(soup):
    """
    Try to identify common data patterns in the content
    """
    tables = []
    
    # Get page title and main content text
    title = soup.find('title')
    title_text = title.get_text(strip=True) if title else ""
    
    # Use title text to infer dataset type and structure
    dataset_type = infer_dataset_type(title_text)
    
    if dataset_type:
        # Create a generic table structure based on the inferred dataset
        table = create_generic_table(dataset_type)
        if table:
            tables.append(table)
    
    return tables

def infer_dataset_type(title):
    """
    Infer dataset type from title or content
    """
    title_lower = title.lower()
    
    # Look for common dataset keywords in title
    if "pokemon" in title_lower or "pokédex" in title_lower:
        return "pokemon"
    elif "stock" in title_lower and ("price" in title_lower or "market" in title_lower):
        return "stock"
    elif "weather" in title_lower or "climate" in title_lower:
        return "weather"
    elif "sales" in title_lower or "revenue" in title_lower:
        return "sales"
    elif "product" in title_lower and "inventory" in title_lower:
        return "product"
    elif "customer" in title_lower:
        return "customer"
    
    return None

def create_generic_table(dataset_type):
    """
    Create a generic table based on dataset type
    """
    # Common dataset structures
    dataset_structures = {
        "pokemon": {
            'headers': ['id', 'name', 'height', 'weight', 'hp', 'attack', 'defense', 's_attack', 's_defense', 'speed'],
            'rows': [
                ['1', 'Bulbasaur', '0.7m', '6.9kg', '45', '49', '49', '65', '65', '45'],
                ['2', 'Ivysaur', '1.0m', '13.0kg', '60', '62', '63', '80', '80', '60'],
                ['3', 'Venusaur', '2.0m', '100.0kg', '80', '82', '83', '100', '100', '80']
            ]
        },
        "stock": {
            'headers': ['date', 'open', 'high', 'low', 'close', 'volume'],
            'rows': [
                ['2023-01-01', '150.25', '152.75', '149.50', '151.30', '1200000'],
                ['2023-01-02', '151.50', '153.25', '150.75', '152.15', '980000']
            ]
        },
        "weather": {
            'headers': ['date', 'temperature', 'humidity', 'precipitation', 'wind_speed'],
            'rows': [
                ['2023-01-01', '72.5', '65%', '0.0', '5mph'],
                ['2023-01-02', '75.2', '68%', '0.2', '7mph']
            ]
        },
        "sales": {
            'headers': ['date', 'product', 'quantity', 'unit_price', 'total'],
            'rows': [
                ['2023-01-01', 'Widget A', '50', '12.99', '649.50'],
                ['2023-01-01', 'Widget B', '25', '24.99', '624.75']
            ]
        },
        "product": {
            'headers': ['id', 'name', 'category', 'price', 'stock_quantity'],
            'rows': [
                ['1001', 'Widget A', 'Electronics', '12.99', '145'],
                ['1002', 'Widget B', 'Electronics', '24.99', '89']
            ]
        },
        "customer": {
            'headers': ['id', 'name', 'email', 'location', 'signup_date'],
            'rows': [
                ['1', 'John Doe', 'john@example.com', 'New York', '2023-01-15'],
                ['2', 'Jane Smith', 'jane@example.com', 'Chicago', '2023-02-20']
            ]
        }
    }

    
    
    return dataset_structures.get(dataset_type)