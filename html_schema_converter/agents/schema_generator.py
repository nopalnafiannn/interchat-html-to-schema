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
            print("DEBUG: Could not extract schema data - creating default schema")
            # Create a default schema instead of returning None
            headers = table_info.get('headers', [])
            if not headers:
                return {"schema": None, "error": "No headers found in table data"}
                
            # Create basic schema with just the headers
            columns = []
            for header in headers:
                columns.append(SchemaColumn(
                    name=header,
                    type="string",
                    description=f"Column containing {header} data",
                    nullable=True,
                    inferred=True,
                    confidence=0.5
                ))
            
            schema = Schema(
                name="CSV Data Schema",
                description="Automatically generated schema for CSV data",
                columns=columns
            )
            
            return {
                "schema": schema,
                "metrics": {}
            }
        
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
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                model=self.model,
                system_message="You are a data extraction engine specialized in precise type inference. Output only valid JSON in the specified format. Do not use markdown code blocks (```). Return only the JSON object with no additional text.",
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            schema_text = response["content"].strip()
            
            # Parse the schema text
            schema_obj = self._parse_schema_json(schema_text)
            if schema_obj is None:
                print("DEBUG: Failed to parse schema JSON - creating fallback schema")
                # Create a fallback schema with basic structure
                columns = []
                for header in headers:
                    columns.append(SchemaColumn(
                        name=header,
                        type="string", 
                        description=f"Column containing {header} data",
                        nullable=True,
                        inferred=True,
                        confidence=0.5
                    ))
                
                schema = Schema(
                    name="CSV Data Schema",
                    description="Automatically generated schema for CSV data",
                    columns=columns
                )
                
                return {
                    "schema": schema,
                    "raw_output": schema_text,
                    "metrics": response.get("metrics", {})
                }
            
            # Create Schema object
            try:
                schema = self._create_schema_object(schema_obj, has_sample_data)
                # Debug to verify Schema object creation
                print(f"DEBUG schema_generator: Created schema object type: {type(schema)}")
                
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
            except Exception as e:
                print(f"DEBUG schema_generator ERROR: {str(e)}")
                # Create a fallback schema
                columns = []
                for header in headers:
                    columns.append(SchemaColumn(
                        name=header,
                        type="string",
                        description=f"Column containing {header} data",
                        nullable=True,
                        inferred=True,
                        confidence=0.5
                    ))
                
                schema = Schema(
                    name="CSV Data Schema",
                    description=f"Fallback schema created due to error: {str(e)}",
                    columns=columns
                )
                
                return {
                    "schema": schema,
                    "raw_output": schema_text,
                    "metrics": response.get("metrics", {})
                }
        except Exception as e:
            print(f"DEBUG schema_generator LLM ERROR: {str(e)}")
            # Create a fallback schema in case of LLM failure
            columns = []
            for header in headers:
                columns.append(SchemaColumn(
                    name=header,
                    type="string",
                    description=f"Column containing {header} data",
                    nullable=True,
                    inferred=True,
                    confidence=0.5
                ))
            
            schema = Schema(
                name="CSV Data Schema",
                description=f"Fallback schema created due to LLM error: {str(e)}",
                columns=columns
            )
            
            return {
                "schema": schema,
                "error": f"LLM error: {str(e)}"
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
  "name": "Table Schema",
  "description": "A brief description of the overall table",
  "columns": [
    {{
      "name": "ColumnName",
      "type": "string/number/date/boolean/object/array/null",
      "python_type": "str/int/float/list/tuple/dict/bool/bytes/NoneType/etc.",
      "description": "A short description of the column",
      "nullable": true,
      "format": "Optional format specification like YYYY-MM-DD for dates",
      "constraints": {{
        "minimum": 0,          # Optional min value for numbers
        "maximum": 100,        # Optional max value for numbers
        "pattern": "^[A-Z].*"  # Optional regex pattern for strings
      }}
    }},
    ...
  ]
}}

- Use the header text as "name".
- Infer accurate "type" based on sample data (e.g., string, number, date).
- Provide the precise "python_type" that matches Python's type system (e.g., str, int, float, list).
- When appropriate, add a "format" field for date formats, number formats, etc.
- Add "constraints" when values follow clear patterns (only include relevant constraints).
- Make inferences based on both column names and actual values in the data.
- Provide a concise but informative "description" for each column.
- Include a nullable property (true/false) for each column based on observed data.
- Add a descriptive table-level name and description.
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
  "name": "Table Schema",
  "description": "A brief description of the overall table",
  "columns": [
    {{
      "name": "ColumnName",
      "type": "string/number/date/boolean/object/array/null",
      "python_type": "str/int/float/list/tuple/dict/bool/bytes/NoneType/etc.",
      "description": "A short description of the column",
      "nullable": true,
      "inferred": true,
      "confidence": 0.7,
      "format": "Optional format specification",
      "constraints": {{
        "minimum": 0,          # Only include for number fields when appropriate
        "maximum": 100,        # Only include for number fields when appropriate
        "pattern": "^[A-Z].*"  # Only include for string fields when appropriate
      }}
    }},
    ...
  ]
}}

- Use the header text as "name".
- Infer "type" based on common naming conventions (using JSON schema types).
- Specify the most likely "python_type" based on column name conventions.
- Add a "confidence" score between 0.0 and 1.0 to indicate your confidence in the type inference.
- Include "inferred": true for all columns to indicate this is based only on column names.
- Add format and constraints fields when column names strongly suggest specific patterns.
- Provide a short "description" that explains what data you expect in this column.
- Include a nullable property (true/false) for each column.
- Also add a table-level name and description.
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
        # Clean up the text before parsing
        cleaned_text = schema_text.strip()
        
        # Debug original text
        print(f"DEBUG: Raw schema text length: {len(schema_text)}")
        
        # Remove markdown code block markers if present
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[3:]
        
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
        
        cleaned_text = cleaned_text.strip()
        
        # Try to parse the JSON
        try:
            # Fix invalid escape sequences that may be in the JSON
            fixed_text = cleaned_text.replace('\\', '\\\\')
            # But don't double escape valid escape sequences
            for valid_escape in ['\\"', '\\n', '\\t', '\\r', '\\b', '\\f']:
                fixed_text = fixed_text.replace('\\\\' + valid_escape[1], valid_escape)
            
            json_obj = json.loads(fixed_text)
            
            # If the result is still a string, try parsing it again
            if isinstance(json_obj, str):
                json_obj = json.loads(json_obj)
            
            # Verify that we have a valid schema structure
            if not isinstance(json_obj, dict):
                print(f"DEBUG: JSON is not a dictionary: {type(json_obj)}")
                return None
                
            # Check for required keys in the schema
            if "columns" not in json_obj and "schema" not in json_obj:
                print(f"DEBUG: JSON missing required keys (columns/schema)")
                # If we have name and description, try to create a base object
                if "name" in json_obj:
                    default_schema = {
                        "name": json_obj.get("name", "Table Schema"),
                        "description": json_obj.get("description", ""),
                        "columns": []
                    }
                    return default_schema
                return None
                
            return json_obj
        except json.JSONDecodeError as e:
            print(f"DEBUG: JSON decode error: {str(e)}")
            # Try to fix specific escape character issues
            try:
                # Replace invalid escape sequences
                fixed_text = cleaned_text.replace('\\', '\\\\')
                # But don't double escape valid escape sequences
                for valid_escape in ['\\"', '\\n', '\\t', '\\r', '\\b', '\\f']:
                    fixed_text = fixed_text.replace('\\\\' + valid_escape[1], valid_escape)
                
                json_obj = json.loads(fixed_text)
                return json_obj
            except json.JSONDecodeError:
                # Still failed, try to extract valid JSON
                try:
                    # Look for JSON starting with { and ending with }
                    start_idx = cleaned_text.find("{")
                    end_idx = cleaned_text.rfind("}")
                    
                    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                        extracted_json = cleaned_text[start_idx:end_idx+1]
                        print(f"DEBUG: Attempting to extract JSON from text. Range: {start_idx}-{end_idx}")
                        
                        # Try to fix escape sequences in the extracted JSON
                        fixed_json = extracted_json.replace('\\', '\\\\')
                        for valid_escape in ['\\"', '\\n', '\\t', '\\r', '\\b', '\\f']:
                            fixed_json = fixed_json.replace('\\\\' + valid_escape[1], valid_escape)
                        
                        parsed_json = json.loads(fixed_json)
                        
                        # Verify basic structure
                        if isinstance(parsed_json, dict):
                            if "columns" in parsed_json or "schema" in parsed_json:
                                return parsed_json
                            elif "name" in parsed_json:
                                # Try to create a minimal valid schema
                                default_schema = {
                                    "name": parsed_json.get("name", "Table Schema"),
                                    "description": parsed_json.get("description", ""),
                                    "columns": []
                                }
                                return default_schema
                    
                    # If we reach here, no valid JSON was found
                    print("DEBUG: Could not extract valid JSON from LLM response")
                    
                    # Last resort: create a fallback schema
                    print("DEBUG: Failed to parse schema JSON - creating fallback schema")
                    return {
                        "name": "Table Schema",
                        "description": "Fallback schema created due to JSON parsing issues",
                        "columns": []
                    }
                except json.JSONDecodeError as nested_e:
                    print(f"DEBUG: Nested JSON decode error: {str(nested_e)}")
                    # Create a fallback schema
                    return {
                        "name": "Table Schema",
                        "description": "Fallback schema created due to JSON parsing issues",
                        "columns": []
                    }
        except Exception as e:
            print(f"DEBUG: Unexpected error parsing JSON: {str(e)}")
            # Create a fallback schema
            return {
                "name": "Table Schema",
                "description": "Fallback schema created due to unexpected error",
                "columns": []
            }
    
    def _create_schema_object(self, schema_data: Dict[str, Any], has_sample_data: bool) -> Schema:
        """
        Create a Schema object from parsed schema data.
        
        Args:
            schema_data: Parsed schema dictionary
            has_sample_data: Whether sample data was available
            
        Returns:
            Schema object
        """
        # Debug input
        print(f"DEBUG: Creating schema object from data: {type(schema_data)}")
        
        # Handle both the old and new schema formats
        columns_data = schema_data.get("columns", schema_data.get("schema", []))
        
        # If we don't have column data, we'll create an empty schema
        if not columns_data:
            print("DEBUG: No columns data found - creating empty schema")
            return Schema(
                name=schema_data.get("name", "Empty Table Schema"),
                description=schema_data.get("description", "Schema created with no column data")
            )
            
        columns = []
        for col_data in columns_data:
            try:
                # Handle both naming conventions
                col_name = col_data.get("name", col_data.get("column_name", ""))
                
                # If we don't have a valid column name or type, create a default entry
                if not col_name:
                    print(f"DEBUG: Missing column name in {col_data}")
                    # Try to create a placeholder name
                    col_name = f"Column_{len(columns) + 1}"
                
                # If type is missing, default to string
                col_type = col_data.get("type", "string")
                
                column = SchemaColumn(
                    name=col_name,
                    type=col_type,
                    description=col_data.get("description", f"Column containing {col_name} data"),
                    nullable=col_data.get("nullable", True),
                    confidence=col_data.get("confidence", 1.0),
                    inferred=col_data.get("inferred", not has_sample_data),
                    python_type=col_data.get("python_type", ""),
                    format=col_data.get("format", ""),
                    constraints=col_data.get("constraints", {})
                )
                columns.append(column)
            except Exception as e:
                print(f"DEBUG: Error creating column from {col_data}: {str(e)}")
                # Add a placeholder column instead of failing
                placeholder_name = f"Column_{len(columns) + 1}"
                columns.append(SchemaColumn(
                    name=placeholder_name,
                    type="string",
                    description=f"Placeholder for column that failed to parse",
                    nullable=True,
                    confidence=0.5,
                    inferred=True
                ))
        
        name = schema_data.get("name", "Table Schema")
        description = schema_data.get("description", "")
        
        # If we somehow have no columns at this point, add a note to the description
        if not columns:
            description += " (No columns were successfully parsed from the schema data)"
        
        return Schema(
            name=name,
            description=description,
            columns=columns
        )
    
    @track_metrics
    def incorporate_feedback(self, original_schema: Schema, feedback: Dict[str, Any]) -> Dict[str, Any]:
        # The result of this method will be passed to add_metrics with is_feedback=True
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