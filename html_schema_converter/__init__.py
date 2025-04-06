"""
HTML to Data Schema Converter for InterChat.

This package provides tools to automatically extract and generate structured data schemas 
from HTML tables for use with the InterChat visual analytics system.
"""

__version__ = "0.1.0"

from html_schema_converter.models.schema import Schema
from html_schema_converter.agents.html_reader import HTMLReader
from html_schema_converter.agents.table_analyzer import TableAnalyzer
from html_schema_converter.agents.schema_generator import SchemaGenerator
from html_schema_converter.utils.kaggle import KaggleIntegration

# Main converter class for easy API access
from html_schema_converter.main import SchemaConverter

__all__ = [
    'Schema',
    'HTMLReader',
    'TableAnalyzer',
    'SchemaGenerator',
    'KaggleIntegration',
    'SchemaConverter',
]