"""Schema Generator Agent for creating structured data schemas."""

import json
import time
from typing import Dict, List, Any, Optional

from html_schema_converter.llm.openai_client import OpenAIClient
from html_schema_converter.models.schema import Schema, SchemaColumn
from html_schema_converter.config import config
from html_schema_converter.utils.metrics import track_metrics

class SchemaGenerator:
    """Agent for generating data schemas from table information."""
    
    def __init__(self):
        """Initialize the schema generator with LLM client."""
        self.llm_client = OpenAIClient()
        self.model = config.get("llm.schema_generation_model", "gpt-3.5-turbo-16k")
        self.temperature = config.get("llm.temperature", 0)
        self.max_tokens = config.get("schema_generation.max_tokens", 2000)
    
    def extract_schema_from_table(self, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract headers and sample data from a table.
        
        Args:
            table_info: Dictionary with table information
            
        Returns:
            Dictionary with extracted schema data
        """
        headers = table_info.get('headers', [])
        rows = table_info.get('sample_data', [])
        
        if not headers or not rows:
            return {"status": "No data found", "schema_data": []}
            
        return {
            "status": "Success",
            "original_headers": headers,
            "schema_data": rows,
            "has_sample_data": bool(rows)
        }
    
    @track_metrics
    def generate_schema(self, table_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a descriptive data schema using LLM.
        
        Args:
            table_info: Dictionary with table information
            
        Returns:
            Dictionary with generated schema and metrics
        """
        extracted_data = self.extract_schema_from_table(table_info)
        if extracted_data["status"] != "Success":
            return {"schema": None, "error": "Could not extract schema data"}
        
        # Prepare the prompt based on available data
        headers = extracted_data["original_headers"]
        sample_rows = extracted_data["schema_data"][:5]
        has_sample_data = extracted_data["has_sample_data"]
        
        # Create the appropriate prompt
        if has_sample_data:
            prompt = self._create_prompt_with_samples(headers, sample_rows)
        else:
            prompt = self._create_prompt_column_names_only(headers)
        
        # Generate schema using LLM
        response = self.llm_client.generate(
            prompt=prompt,
            model=self.model,
            system_message="You are a data extraction engine. Output only valid JSON in the specified format.",
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        schema_text = response["content"].strip()
        
        # Parse the schema text
        schema_obj = self._parse_schema_json(schema_text)
        if schema_obj is None:
            return {"schema": None, "error": "Failed to parse schema", "raw_output": schema_text}
        
        # Create Schema object
        schema = self._create_schema_object(schema_obj, has_sample_data)
        
        # Add metadata
        if table_info.get('caption'):
            schema.metadata['table_caption'] = table_info['caption']
        schema.metadata['column_count'] = len(headers)
        schema.metadata['sample_rows_count'] = len(sample_rows)
        schema.metadata['has_sample_data'] = has_sample_data
        
        return {
            "schema": schema,
            "raw_output": schema_text,
            "metrics": response.get("metrics", {})
        }
    
    def _create_prompt_with_samples(self, headers: List[str], sample_rows: List[List[str]]) -> str:
        """
        Create a prompt for schema generation when sample data is available.
        
        Args:
            headers: List of column headers
            sample_rows: List of sample data rows
            
        Returns:
            Prompt string
        """
        prompt_rows_str = ""
        for row in sample_rows:
            prompt_rows_str += f"{row}\n"
            
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
      "type": "string/number/date/boolean/unknown",
      "description": "A short description of the column"
    }},
    ...
  ]
}}

- Use the header text as "column_name".
- Infer "type" from sample data precisely.
- Provide a short "description" for each column.
- Output only valid JSON. Do not include extra text.
"""
        return prompt
    
    def _create_prompt_column_names_only(self, headers: List[str]) -> str:
        """
        Create a prompt for schema generation when only column names are available.
        
        Args:
            headers: List of column headers
            
        Returns:
            Prompt string
        """
        prompt = f"""
You are a data extraction engine. I have a table with these headers:
{headers}

There is no sample data available, so you need to infer the column types and descriptions based only on the column names.

Generate valid JSON describing each column in the format:

{{
  "schema": [
    {{
      "column_name": "ColumnName",
      "type": "string/number/date/boolean/unknown",
      "description": "A short description of the column",
      "inferred": true,
      "confidence": 0.7
    }},
    ...
  ]
}}

- Use the header text as "column_name".
- Infer "type" based on common naming conventions.
- Add a "confidence" score between 0.0 and 1.0 to indicate your confidence in the type inference.
- Include "inferred": true for all columns to indicate this is based only on column names.
- Provide a short "description" for each column.
- Output only valid JSON. Do not include extra text.
"""
        return prompt
    
    def _parse_schema_json(self, schema_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse the JSON schema text from LLM output.
        
        Args:
            schema_text: JSON string from LLM
            
        Returns:
            Parsed dictionary or None if parsing failed
        """
        try:
            json_obj = json.loads(schema_text)
            # If the result is still a string, try parsing it again
            if isinstance(json_obj, str):
                json_obj = json.loads(json_obj)
            return json_obj
        except json.JSONDecodeError:
            return None
    
    def _create_schema_object(self, schema_data: Dict[str, Any], has_sample_data: bool) -> Schema:
        """
        Create a Schema object from parsed schema data.
        
        Args:
            schema_data: Parsed schema dictionary
            has_sample_data: Whether sample data was available
            
        Returns:
            Schema object
        """
        if "schema" not in schema_data:
            raise ValueError("Invalid schema format: 'schema' key missing")
            
        columns = []
        for col_data in schema_data["schema"]:
            if "column_name" not in col_data or "type" not in col_data:
                raise ValueError(f"Invalid column format: {col_data}")
                
            column = SchemaColumn(
                column_name=col_data["column_name"],
                type=col_data["type"],
                description=col_data.get("description", ""),
                confidence=col_data.get("confidence", 1.0),
                inferred=col_data.get("inferred", not has_sample_data)
            )
            columns.append(column)
            
        return Schema(schema=columns)
    
    @track_metrics
    def incorporate_feedback(self, original_schema: Schema, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """
        Incorporate user feedback to refine the schema.
        
        Args:
            original_schema: Original Schema object
            feedback: Dictionary with user feedback
            
        Returns:
            Dictionary with updated schema and metrics
        """
        # Create a prompt with the original schema and user feedback
        original_json = original_schema.to_json()
        
        prompt = f"""
You are tasked with incorporating user feedback into a data schema. 

Original schema:
{original_json}

User feedback:
{json.dumps(feedback, indent=2)}

Generate an updated version of the schema that incorporates the user's feedback.
Maintain the same JSON structure as the original schema, but update the relevant fields.
Output only valid JSON. Do not include extra text.
"""
        
        # Generate updated schema using LLM
        response = self.llm_client.generate(
            prompt=prompt,
            model=self.model,
            system_message="You are a data schema refinement engine. Output only valid JSON in the specified format.",
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        schema_text = response["content"].strip()
        
        # Parse the updated schema text
        schema_obj = self._parse_schema_json(schema_text)
        if schema_obj is None:
            return {"schema": original_schema, "error": "Failed to parse updated schema", "raw_output": schema_text}
        
        # Create updated Schema object
        updated_schema = self._create_schema_object(schema_obj, True)
        
        # Preserve metadata from original schema
        updated_schema.metadata = original_schema.metadata.copy()
        updated_schema.metadata['feedback_incorporated'] = True
        
        return {
            "schema": updated_schema,
            "raw_output": schema_text,
            "metrics": response.get("metrics", {})
        }