"""Output formatting utilities for schemas."""

import json
import yaml
from typing import Dict, Any, Optional, List, Union

from html_schema_converter.models.schema import Schema, SchemaColumn

class SchemaFormatter:
    """Handles formatting of schemas into different output formats."""
    
    @staticmethod
    def format_schema(schema: Schema, format_type: str = "text") -> str:
        """
        Format a schema according to the specified format type.
        
        Args:
            schema: Schema object to format
            format_type: One of "text", "json", or "yaml"
            
        Returns:
            Formatted string representation of the schema
        """
        if not isinstance(schema, Schema):
            raise TypeError(f"Expected Schema object, got {type(schema)}")
        
        format_type = format_type.lower()
        
        if format_type in ["text", "json"]:
            return schema.to_json()
        elif format_type == "yaml":
            return schema.to_yaml()
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    @staticmethod
    def format_dict_schema(schema_dict: Dict[str, Any], format_type: str = "text") -> str:
        """
        Format a schema dictionary according to the specified format type.
        
        Args:
            schema_dict: Dictionary containing schema data
            format_type: One of "text", "json", or "yaml"
            
        Returns:
            Formatted string representation of the schema
        """
        format_type = format_type.lower()
        
        if format_type in ["text", "json"]:
            return json.dumps(schema_dict, indent=2)
        elif format_type == "yaml":
            return yaml.dump(schema_dict, sort_keys=False, default_flow_style=False)
        else:
            return str(schema_dict)
    
    @staticmethod
    def save_schema(schema: Schema, output_path: str, format_type: str = None) -> None:
        """
        Save a schema to a file.
        
        Args:
            schema: Schema object to save
            output_path: Path to save the schema to
            format_type: Optional format type override, otherwise inferred from file extension
        """
        if not isinstance(schema, Schema):
            raise TypeError("Expected Schema object")
        
        # Infer format type from file extension if not specified
        if format_type is None:
            if output_path.endswith(".json"):
                format_type = "json"
            elif output_path.endswith(".yaml") or output_path.endswith(".yml"):
                format_type = "yaml"
            else:
                format_type = "text"
        
        # Format the schema
        formatted_schema = SchemaFormatter.format_schema(schema, format_type)
        
        # Save to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_schema)
        
        print(f"Schema saved to {output_path}")
    
    @staticmethod
    def parse_schema_from_string(schema_string: str, format_type: str = "json") -> Schema:
        """
        Parse a schema from a string representation.
        
        Args:
            schema_string: String representation of the schema
            format_type: Format of the schema string (json or yaml)
            
        Returns:
            Parsed Schema object
        """
        format_type = format_type.lower()
        
        try:
            # Parse the string to a dictionary based on format
            if format_type in ["json", "text"]:
                schema_dict = json.loads(schema_string)
            elif format_type == "yaml":
                schema_dict = yaml.safe_load(schema_string)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
            
            # Extract schema components
            columns_data = schema_dict.get("columns", [])
            metadata = schema_dict.get("metadata", {})
            name = schema_dict.get("name", "Unknown")
            description = schema_dict.get("description", "")
            
            # Create SchemaColumn objects
            columns = []
            for col_data in columns_data:
                col = SchemaColumn(
                    name=col_data.get("name", ""),
                    type=col_data.get("type", "string"),
                    description=col_data.get("description", ""),
                    nullable=col_data.get("nullable", True),
                    confidence=col_data.get("confidence", 1.0)
                )
                columns.append(col)
            
            # Create and return the Schema object
            return Schema(name=name, description=description, columns=columns, metadata=metadata)
            
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Failed to parse schema string: {str(e)}")
        except KeyError as e:
            raise ValueError(f"Missing required key in schema: {str(e)}")