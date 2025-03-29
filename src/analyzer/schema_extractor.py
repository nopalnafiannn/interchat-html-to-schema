"""
Schema Extractor Module
----------------------
Functions for extracting data schema information from HTML content
"""

import time
import re
import json
from src.ai.client import get_openai_client
from src.ai.prompts import RAW_HTML_ANALYSIS_PROMPT, IMPROVED_COMBINE_PROMPT, SCHEMA_IMPROVEMENT_PROMPT
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

def detect_dataset_type(html_content):
    """
    Attempt to detect if this is a known dataset type based on content clues
    
    Args:
        html_content (str): HTML content
        
    Returns:
        str: Dataset type or None
    """
    html_lower = html_content.lower()
    
    # Check for common dataset names in the content
    if "titanic" in html_lower:
        return "titanic"
    elif "iris" in html_lower and ("sepal" in html_lower or "petal" in html_lower):
        return "iris"
    elif "mnist" in html_lower and "digit" in html_lower:
        return "mnist"
    elif "boston" in html_lower and "housing" in html_lower:
        return "boston_housing"
    elif "wine" in html_lower and "quality" in html_lower:
        return "wine_quality"
    
    # Check for JSON-LD dataset metadata
    if '<script type="application/ld+json">' in html_lower:
        json_ld_match = re.search(r'<script [^>]*type="application\/ld\+json"[^>]*>(.*?)<\/script>', 
                                  html_content, re.DOTALL)
        if json_ld_match:
            json_content = json_ld_match.group(1).lower()
            if "titanic" in json_content:
                return "titanic"
            elif "iris" in json_content:
                return "iris"
            # Add more dataset type detection based on JSON-LD content
            
    return None

def is_likely_dataset_html(html_content):
    """
    Check if the HTML likely contains a dataset by looking for table structures
    or dataset-related content
    
    Args:
        html_content (str): HTML content
        
    Returns:
        bool: True if HTML likely contains a dataset, False otherwise
    """
    html_lower = html_content.lower()
    
    # Check for table elements
    if "<table" in html_lower and ("<th" in html_lower or "<td" in html_lower):
        return True
    
    # Check for grid structures
    if ("class=" in html_lower and 
        any(grid_term in html_lower for grid_term in ["grid", "table", "data-table", "datatable"])):
        return True
    
    # Check for dataset-related terms in strong concentration
    dataset_terms = ["dataset", "data set", "data", "column", "row", "schema", 
                    "csv", "spreadsheet", "database", "table"]
    term_count = sum(html_lower.count(term) for term in dataset_terms)
    
    # If many dataset terms, likely a dataset page
    if term_count > 10:
        return True
    
    # Check for JSON-LD with dataset type
    if '<script type="application/ld+json">' in html_lower:
        json_ld_match = re.search(r'<script [^>]*type="application\/ld\+json"[^>]*>(.*?)<\/script>', 
                                 html_content, re.DOTALL)
        if json_ld_match:
            try:
                json_content = json_ld_match.group(1)
                json_data = json.loads(json_content)
                
                # Check if it has @type of Dataset
                if json_data.get("@type") == "Dataset" or "dataset" in str(json_data).lower():
                    return True
            except:
                pass  # If we can't parse the JSON, continue with other checks
    
    # If we get here, we didn't find strong evidence of dataset content
    return False

def analyze_chunk(chunk, model="gpt-3.5-turbo", max_tokens=700):
    """
    Analyze a chunk of HTML content to extract data schema information
    
    Args:
        chunk (str): HTML content chunk
        model (str): OpenAI model to use
        max_tokens (int): Maximum tokens in response
        
    Returns:
        str: Analysis results
    """
    client = get_openai_client()
    
    # Check if this is a known dataset type
    dataset_type = detect_dataset_type(chunk)
    if dataset_type:
        logger.info(f"Detected dataset type: {dataset_type}")
    
    prompt = RAW_HTML_ANALYSIS_PROMPT.format(chunk=chunk)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are a data schema expert specialized in extracting dataset information from HTML. {'This appears to be about the ' + dataset_type + ' dataset.' if dataset_type else ''}"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.2  # Lower temperature for more consistent outputs
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error processing chunk: {e}")
        return f"Error processing chunk: {e}"

def analyze_chunks(chunks, model="gpt-3.5-turbo", max_tokens=700, delay=1):
    """
    Analyze multiple chunks of HTML content
    
    Args:
        chunks (list): List of HTML content chunks
        model (str): OpenAI model to use
        max_tokens (int): Maximum tokens in response
        delay (int): Delay between API calls in seconds
        
    Returns:
        list: List of analysis results
    """
    results = []
    
    # Check if any chunk is likely to contain dataset information
    has_dataset_content = any(is_likely_dataset_html(chunk) for chunk in chunks)
    if not has_dataset_content:
        logger.warning("No dataset-related content detected in HTML")
        return ["NO_DATASET_FOUND"]
    
    # Check for known dataset types in all chunks
    dataset_types = set()
    for chunk in chunks:
        dataset_type = detect_dataset_type(chunk)
        if dataset_type:
            dataset_types.add(dataset_type)
    
    if dataset_types:
        dataset_type_str = ", ".join(dataset_types)
        logger.info(f"Detected potential dataset type(s): {dataset_type_str}")
    
    for i, chunk in enumerate(chunks):
        logger.info(f"Processing chunk {i+1} of {len(chunks)}...")
        result = analyze_chunk(chunk, model, max_tokens)
        logger.info(f"Chunk {i+1} analysis complete.")
        results.append(result)
        
        # Add delay to avoid rate limits
        if i < len(chunks) - 1 and delay > 0:
            time.sleep(delay)
    
    return results

def combine_results(results, model="gpt-3.5-turbo", max_tokens=1200):
    """
    Combine multiple chunk analysis results
    
    Args:
        results (list): List of analysis results
        model (str): OpenAI model to use
        max_tokens (int): Maximum tokens in response
        
    Returns:
        str: Combined analysis
    """
    # Check if no dataset was found
    if results == ["NO_DATASET_FOUND"]:
        return "ERROR: Your HTML does not contain dataset information. Please upload a correct HTML file with dataset content."
    
    client = get_openai_client()
    
    # Join results with chunk numbering for better context
    combined_text = "\n\n".join([f"CHUNK {i+1}:\n{r}" for i, r in enumerate(results)])
    
    # Look for dataset type mentions in the results
    dataset_types = set()
    for result in results:
        if "titanic" in result.lower():
            dataset_types.add("titanic")
        elif "iris" in result.lower() and ("sepal" in result.lower() or "petal" in result.lower()):
            dataset_types.add("iris")
        # Add more dataset type detection
        
    dataset_type_str = ""
    if dataset_types:
        dataset_type_str = f"The analyzed HTML appears to be about the {', '.join(dataset_types)} dataset(s). "
    
    prompt = IMPROVED_COMBINE_PROMPT.format(results=combined_text)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": f"You are a data schema expert. {dataset_type_str}Provide the most accurate and complete schema possible."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.2  # Lower temperature for more consistent outputs
        )
        
        combined_result = response.choices[0].message.content
        
        # If we've detected a specific dataset type, run an improvement step
        if dataset_types:
            logger.info(f"Running schema improvement for detected dataset type(s): {', '.join(dataset_types)}")
            improvement_prompt = SCHEMA_IMPROVEMENT_PROMPT.format(schema=combined_result)
            
            improve_response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": f"You are a data schema expert. The analyzed HTML is about the {', '.join(dataset_types)} dataset(s). Ensure the schema matches the standard structure for this dataset."},
                    {"role": "user", "content": improvement_prompt}
                ],
                max_tokens=max_tokens,
                temperature=0.2
            )
            
            return improve_response.choices[0].message.content
        
        return combined_result
    except Exception as e:
        logger.error(f"Error combining results: {e}")
        return f"Error combining results: {e}"

def parse_schema_to_json(schema_text):
    """
    Attempt to parse schema text into a structured JSON format
    
    Args:
        schema_text (str): Schema text from AI
        
    Returns:
        dict: Structured schema information
    """
    # Check if there was an error message
    if schema_text.startswith("ERROR:"):
        return {
            "error": schema_text,
            "columns": [],
            "column_count": 0
        }
    
    # This function is a bit more robust now
    lines = schema_text.split('\n')
    columns = []
    
    current_column = None
    current_description = []
    current_data_type = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for new column pattern (often numbered or bulleted)
        if (line.startswith(('- ', '* ', '• ')) or 
            (len(line) > 2 and line[0].isdigit() and line[1] == '.')):
            
            # Save previous column if it exists
            if current_column:
                columns.append({
                    "name": current_column,
                    "description": ' '.join(current_description),
                    "data_type": current_data_type or "unknown"
                })
            
            # Reset for new column
            parts = line.lstrip('-*•0123456789. \t').split(':', 1)
            current_column = parts[0].strip()
            current_description = [parts[1].strip()] if len(parts) > 1 else []
            current_data_type = None
            
            # Look for data type in the description
            if current_description and len(current_description[0]) > 0:
                desc = current_description[0].lower()
                if "string" in desc or "text" in desc:
                    current_data_type = "string"
                elif "int" in desc or "number" in desc or "float" in desc:
                    current_data_type = "number"
                elif "date" in desc or "time" in desc:
                    current_data_type = "datetime"
                elif "bool" in desc:
                    current_data_type = "boolean"
                
        # If this line contains "Type:" or similar, extract data type
        elif current_column and ("type:" in line.lower() or "data type:" in line.lower()):
            type_parts = line.split(':', 1)
            if len(type_parts) > 1:
                type_value = type_parts[1].strip().lower()
                if "string" in type_value or "text" in type_value:
                    current_data_type = "string"
                elif "int" in type_value or "number" in type_value or "float" in type_value:
                    current_data_type = "number"
                elif "date" in type_value or "time" in type_value:
                    current_data_type = "datetime"
                elif "bool" in type_value:
                    current_data_type = "boolean"
                else:
                    current_data_type = type_value
        elif current_column:
            # Continue description for current column
            current_description.append(line)
    
    # Add the last column if there is one
    if current_column:
        columns.append({
            "name": current_column,
            "description": ' '.join(current_description),
            "data_type": current_data_type or "unknown"
        })
    
    return {
        "columns": columns,
        "column_count": len(columns)
    }