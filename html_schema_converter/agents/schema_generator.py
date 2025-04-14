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
        is_vertical_structure = table_info.get('is_vertical_structure', False)
        
        if not headers or not rows:
            return {"status": "No data found", "schema_data": []}
        
        # For vertical tables like AdventureWorks, the headers are already property names
        # and sample_data contains the values for those properties in the same order
        if is_vertical_structure:
            # Check if this is from CSV schema format with explicit property names/values
            if 'property_names' in table_info and 'property_values' in table_info:
                return {
                    "status": "Success",
                    "original_headers": table_info['property_names'],
                    "schema_data": [table_info['property_values']],
                    "has_sample_data": True,
                    "is_vertical_structure": True,
                    "is_schema_csv": True
                }
            return {
                "status": "Success",
                "original_headers": headers,
                "schema_data": rows,
                "has_sample_data": bool(rows),
                "is_vertical_structure": True
            }
            
        return {
            "status": "Success",
            "original_headers": headers,
            "schema_data": rows,
            "has_sample_data": bool(rows),
            "is_vertical_structure": False
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
        is_vertical_structure = extracted_data.get("is_vertical_structure", False)
        
        # Create the appropriate prompt
        is_schema_csv = extracted_data.get("is_schema_csv", False)
        original_headers = extracted_data.get("original_headers", headers)
        
        if is_schema_csv:
            # For CSV files containing database schema information
            prompt = self._create_prompt_schema_csv(headers, sample_rows, original_headers)
        elif is_vertical_structure:
            # For vertical tables (property-value pairs like in AdventureWorks)
            prompt = self._create_prompt_vertical_table(headers, sample_rows)
        elif has_sample_data:
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
      "type": "string/int/float/date/boolean/object/array/null",
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

- CRITICALLY IMPORTANT: Use the EXACT header text as the "name" for each column. Do not modify, rename, or merge header names.
- If column names include empty strings, "_1", or other unusual names, preserve them exactly as is.
- Create a schema column for EVERY header in the list, even if some appear to be unusual or not meaningful.
- For example, if headers are ["", "_1", "Key", "Name", "Data type"], create 5 columns with those exact names.
- Infer accurate "type" based on sample data (e.g., string, number, date).
- Use specific data types for the "type" field (e.g., int, float, string, boolean).
- When appropriate, add a "format" field for date formats, number formats, etc.
- Add "constraints" when values follow clear patterns (only include relevant constraints).
- Make inferences based on both column names and actual values in the data.
- Provide a concise but informative "description" for each column.
- Include a nullable property (true/false) for each column based on observed data.
- Add a descriptive table-level name and description.
- Output only valid JSON. Do not include extra text.
"""
        return prompt
    
    def _create_prompt_vertical_table(self, properties: List[str], values: List[List[str]]) -> str:
        """
        Create a prompt for schema generation when dealing with a vertical property-value table.
        
        Args:
            properties: List of property names from the first column
            values: List of property values from the second column
            
        Returns:
            Prompt string
        """
        print(f"DEBUG schema_generator: Creating prompt for vertical table")
        print(f"DEBUG schema_generator: Property names: {properties[:5]}")
        print(f"DEBUG schema_generator: Values: {values[0][:5] if values and len(values) > 0 else 'None'}")
        
        # Combine properties and values for display in the prompt
        property_value_pairs = []
        if values and len(values) > 0:
            # Ensure we don't go out of bounds
            value_list = values[0]
            for i, prop in enumerate(properties):
                if i < len(value_list):
                    pair = f"{prop}: {value_list[i]}"
                    property_value_pairs.append(pair)
                    print(f"DEBUG schema_generator: Added pair: {pair}")
                else:
                    property_value_pairs.append(f"{prop}: (no value)")
                    
        prop_value_text = "\n".join(property_value_pairs)
        print(f"DEBUG schema_generator: Created {len(property_value_pairs)} property-value pairs for prompt")
        
        prompt = f"""
You are a data extraction engine. I have a vertical property-value table from a database schema documentation.
The first column contains property names and the second column contains their corresponding values.

Here are the property-value pairs:
{prop_value_text}

This describes a database table or entity in a data model. Generate valid JSON for a schema that captures all these properties
in the format:

{{
  "name": "The table name found in the properties",
  "description": "A comprehensive description of the table based on the properties",
  "columns": [
    {{
      "name": "column_name",
      "type": "string/int/float/date/boolean/object/array/null",
      "description": "Description of the column",
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

- Extract the table name, column information, primary key, foreign keys and other properties from the data
- If there are columns listed in the properties, create a schema column entry for each one
- If the list of columns is not explicitly provided, create a reasonable schema based on the nature of the table
- Infer accurate types based on property descriptions or values
- Only include constraints when they can be determined from the data
- Output only valid JSON. Do not include extra text.
"""
        return prompt
        
    def _create_prompt_schema_csv(self, property_names: List[str], property_values: List[List[str]], original_headers: List[str] = None) -> str:
        """
        Create a prompt for schema generation for CSV files that contain database schema information.
        
        Args:
            property_names: List of property names
            property_values: List containing a single list of property values
            original_headers: Original CSV headers before any processing
            
        Returns:
            Prompt string
        """
        # Combine properties and values for display in the prompt
        property_value_pairs = []
        
        if original_headers:
            headers_text = f"Original CSV Headers: {str(original_headers)}"
        else:
            headers_text = f"Property Names: {str(property_names)}"
        
        if property_values and len(property_values) > 0:
            # We expect a single row of values
            value_list = property_values[0]
            for i, prop in enumerate(property_names):
                if i < len(value_list):
                    pair = f"{prop}: {value_list[i]}"
                    property_value_pairs.append(pair)
                else:
                    property_value_pairs.append(f"{prop}: (no value)")
                    
        prop_value_text = "\n".join(property_value_pairs)
        
        prompt = f"""
You are a database schema analyzer. I have a CSV file that describes a database table schema with column definitions. The file has a list of properties and values that describe the columns in the table.

Here are the headers from the file:
{headers_text}

Here are the property-value pairs extracted from the file:
{prop_value_text}

This describes a database table with its columns and their properties. Generate valid JSON for a data schema that captures this table structure in the format:

{{
  "name": "The table name derived from context",
  "description": "A description of the table's purpose based on the column information",
  "columns": [
    {{
      "name": "column_name",
      "type": "The appropriate data type (string, int, float, boolean, etc.)",
      "description": "Description of what this column contains",
      "nullable": true or false (based on the 'Null' attribute),
      "primary_key": true or false (based on 'Key' attribute),
      "foreign_key": "Referenced table.column if applicable"
    }},
    ...
  ]
}}

- CRITICALLY IMPORTANT: Each column in the schema must match EXACTLY with one of the header fields in the CSV file. Do not create new column names or merge header fields.
- For CSV files with headers like "", "_1", "Key", "Name", "Data type", create a column in the schema for EACH of these headers using their exact names.
- Use the EXACT headers as column names in your schema, preserving the exact spelling, case, and even empty string headers.
- If a header is empty or just whitespace, still create a column for it with that empty name.
- If columns have names like "_1", they should get schema columns with exactly that name "_1".
- Use the rows beneath the headers to determine the appropriate data types and properties of each column.
- Do not make up column names that don't appear in the headers - use only the headers that were actually present.
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
      "type": "string/int/float/date/boolean/object/array/null",
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

- CRITICALLY IMPORTANT: Use the EXACT header text as the "name" for each column. Do not modify, rename, or merge header names.
- If column names include empty strings, "_1", or other unusual names, preserve them exactly as is.
- Create a schema column for EVERY header in the list, even if some appear to be unusual or not meaningful.
- For example, if headers are ["", "_1", "Key", "Name", "Data type"], create 5 columns with those exact names.
- Infer "type" based on common naming conventions (using JSON schema types).
- Use specific data types for the "type" field like int, float, etc.
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
                
                # Allow empty string column names - don't replace them
                if col_name is None:  # Only replace if truly None, not empty string
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