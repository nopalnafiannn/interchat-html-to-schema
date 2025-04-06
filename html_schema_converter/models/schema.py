"""Schema data structures for HTML to Data Schema Converter."""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
import json
import yaml

@dataclass
class SchemaColumn:
    """Represents a column in the data schema."""
    
    column_name: str
    type: str
    description: str
    confidence: float = 1.0
    sample_values: List[Any] = field(default_factory=list)
    inferred: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding internal fields."""
        result = {
            "column_name": self.column_name,
            "type": self.type,
            "description": self.description
        }
        # Only include confidence and inferred if they're non-default
        if self.confidence < 1.0:
            result["confidence"] = self.confidence
        if self.inferred:
            result["inferred"] = True
        return result

@dataclass
class Schema:
    """Represents a complete data schema extracted from a table."""
    
    schema: List[SchemaColumn] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Schema':
        """
        Create a Schema instance from a dictionary.
        
        Args:
            data: Dictionary containing schema data
            
        Returns:
            Schema instance
        """
        if "schema" not in data:
            raise ValueError("Invalid schema format: 'schema' key missing")
            
        columns = []
        for col_data in data["schema"]:
            if "column_name" not in col_data or "type" not in col_data:
                raise ValueError(f"Invalid column format: {col_data}")
                
            columns.append(SchemaColumn(
                column_name=col_data["column_name"],
                type=col_data["type"],
                description=col_data.get("description", ""),
                confidence=col_data.get("confidence", 1.0),
                inferred=col_data.get("inferred", False)
            ))
            
        metadata = data.get("metadata", {})
        metrics = data.get("metrics", {})
        
        return cls(schema=columns, metadata=metadata, metrics=metrics)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Schema':
        """
        Create a Schema instance from a JSON string.
        
        Args:
            json_str: JSON string containing schema data
            
        Returns:
            Schema instance
        """
        try:
            data = json.loads(json_str)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert schema to a dictionary.
        
        Returns:
            Dictionary representation of the schema
        """
        result = {
            "schema": [col.to_dict() for col in self.schema]
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert schema to a JSON string.
        
        Args:
            indent: Indentation level for pretty printing
            
        Returns:
            JSON string representation of the schema
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    def to_yaml(self) -> str:
        """
        Convert schema to a YAML string.
        
        Returns:
            YAML string representation of the schema
        """
        return yaml.dump(self.to_dict(), sort_keys=False)
    
    def format(self, format_type: str = "text") -> str:
        """
        Format the schema according to the specified format type.
        
        Args:
            format_type: One of "text", "json", or "yaml"
            
        Returns:
            Formatted string representation of the schema
        """
        format_type = format_type.lower()
        if format_type in ["text", "json"]:
            return self.to_json()
        elif format_type == "yaml":
            return self.to_yaml()
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def __len__(self) -> int:
        """Return the number of columns in the schema."""
        return len(self.schema)