"""Schema Generator Agent for creating data schemas from tables."""

import json
from ..llm.openai_client import OpenAIClient

def generate_datascheme_with_llm(table_info, llm_client=None):
    """
    Generates a descriptive data schema using LLM.
    
    Args:
        table_info (dict): Table information
        llm_client (OpenAIClient, optional): LLM client. Creates a new one if None.
        
    Returns:
        dict: Generated schema and metrics
    """
    # Create LLM client if not provided
    if llm_client is None:
        llm_client = OpenAIClient()
    
    # Extract schema data
    from .html_reader import extract_schema_from_table
    extracted_data = extract_schema_from_table(table_info)
    
    if extracted_data["status"] != "Success":
        return {"schema_table": "Could not extract schema data"}
    
    headers = extracted_data["original_headers"]
    sample_rows = extracted_data["schema_data"][:5]
    prompt_rows_str = ""
    for row in sample_rows:
        prompt_rows_str += f"{row}\n"
    
    # Create the prompt
    prompt = f"""
You are a data extraction engine. I have a table with these headers:
{headers}

Here are some sample rows:
{prompt_rows_str}

Generate valid JSON describing each column in the format:

{{
  "schema": [
    {{
      "column_name": "ColumnName",
      "type": "string/number/date/unknown",
      "description": "A short description of the column"
    }},
    ...
  ]
}}

- Use the header text as "column_name".
- Infer "type" from sample data if possible.
- Provide a short "description" for each column.
- Output only valid JSON. Do not include extra text.
"""
    
    # Get LLM response
    system_prompt = "You are a data extraction engine. Output only valid JSON in the specified format."
    schema_text, metrics = llm_client.generate_completion(
        system_prompt, 
        prompt, 
        model="gpt-3.5-turbo-16k",
        max_tokens=2000
    )
    
    return {
        "schema_table": schema_text.strip(),
        "metrics": {
            "Agent": "Generate Data Schema LLM",
            **metrics
        }
    }