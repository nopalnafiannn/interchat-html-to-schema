"""Formatters for the HTML to Data Schema Converter."""

import json
import yaml

def format_schema(schema, format_type="text"):
    """
    Formats the schema in the desired format.
    
    Args:
        schema (dict): Schema dictionary with schema_table key
        format_type (str, optional): Format type ("text", "json", or "yaml"). Defaults to "text".
        
    Returns:
        str: Formatted schema
    """
    raw_json_str = schema.get("schema_table", "")
    if not raw_json_str:
        return "No schema data."
    
    try:
        json_obj = json.loads(raw_json_str)
    except json.JSONDecodeError:
        return "Error: LLM did not produce valid JSON."
    
    if format_type.lower() == "json":
        return json.dumps(json_obj, indent=2)
    elif format_type.lower() == "yaml":
        return yaml.dump(json_obj, sort_keys=False, default_flow_style=False)
    
    return raw_json_str

def format_csv_schema(schema, format_type="text"):
    """
    Formats a CSV schema in the desired format.
    
    Args:
        schema (dict): Schema dictionary
        format_type (str): Output format (text, json, or yaml)
        
    Returns:
        str: Formatted schema
    """
    if format_type.lower() == "json":
        return json.dumps(schema, indent=2)
    elif format_type.lower() == "yaml":
        return yaml.dump(schema, sort_keys=False, default_flow_style=False)
    else:
        return json.dumps(schema)