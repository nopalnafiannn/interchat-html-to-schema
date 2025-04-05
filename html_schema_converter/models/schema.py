"""Schema data structures for the HTML to Data Schema Converter."""

from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass

@dataclass
class SchemaColumn:
    """Represents a column in a data schema."""
    column_name: str
    type: str
    description: str
    confidence: float = 1.0  # 0.0 to 1.0, where 1.0 is highest confidence
    inferred: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "column_name": self.column_name,
            "type": self.type,
            "description": self.description,
            "confidence": self.confidence,
            "inferred": self.inferred
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SchemaColumn':
        """Create from dictionary."""
        return cls(
            column_name=data.get("column_name", ""),
            type=data.get("type", "unknown"),
            description=data.get("description", ""),
            confidence=data.get("confidence", 1.0),
            inferred=data.get("inferred", False)
        )

@dataclass
class DataSchema:
    """Represents a complete data schema."""
    columns: List[SchemaColumn]
    name: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        schema_dict = {
            "schema": [col.to_dict() for col in self.columns]
        }
        
        if self.name:
            schema_dict["name"] = self.name
            
        if self.description:
            schema_dict["description"] = self.description
            
        if self.source:
            schema_dict["source"] = self.source
            
        return schema_dict
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSchema':
        """Create from dictionary."""
        schema_list = data.get("schema", [])
        columns = [SchemaColumn.from_dict(col) for col in schema_list]
        
        return cls(
            columns=columns,
            name=data.get("name"),
            description=data.get("description"),
            source=data.get("source")
        )

@dataclass
class SchemaGenerationMetrics:
    """Metrics for schema generation."""
    latency_seconds: float
    memory_usage_mb: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    
    def to_dict(self) -> Dict[str, Union[float, int]]:
        """Convert to dictionary."""
        return {
            "Agent": "Schema Generation",
            "Latency (s)": round(self.latency_seconds, 3),
            "Memory Usage (MB)": round(self.memory_usage_mb, 3),
            "Prompt Tokens": self.prompt_tokens,
            "Completion Tokens": self.completion_tokens,
            "Total Tokens": self.total_tokens
        }