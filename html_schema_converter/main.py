"""Main entry point for HTML to Data Schema Converter."""

import argparse
import sys
import os
import pandas as pd
from typing import Dict, List, Any, Optional, Union

from html_schema_converter.config import config
from html_schema_converter.agents.html_reader import HTMLReader
from html_schema_converter.agents.table_analyzer import TableAnalyzer
from html_schema_converter.agents.schema_generator import SchemaGenerator
from html_schema_converter.models.schema import Schema
from html_schema_converter.utils.metrics import MetricsCollector
from html_schema_converter.utils.formatters import SchemaFormatter
from html_schema_converter.utils.kaggle import KaggleIntegration

class SchemaConverter:
    """Main class for HTML to Data Schema conversion."""
    
    def __init__(self):
        """Initialize the schema converter with its component agents."""
        self.html_reader = HTMLReader()
        self.table_analyzer = TableAnalyzer()
        self.schema_generator = SchemaGenerator()
        self.kaggle_integration = KaggleIntegration()
        self.metrics_collector = MetricsCollector()
        self.formatter = SchemaFormatter()
    
    def from_url(self, url: str, output_format: str = "json") -> Union[Schema, Dict[str, Any]]:
        """
        Generate schema from a URL containing HTML tables.
        
        Args:
            url: URL to fetch HTML from
            output_format: Format for the schema output (json, yaml, text)
            
        Returns:
            Schema object or error dictionary
        """
        # Check if this is a Kaggle URL
        if "kaggle.com/datasets" in url:
            return self.from_kaggle(url, output_format)
        
        # Read HTML and extract tables
        print("Detecting tables in HTML...")
        tables_info = self.html_reader.read_from_url(url)
        
        if tables_info["tables_count"] == 0:
            print("No tables found in the HTML document.")
            return {"status": "Error", "message": "No tables found"}
            
        print(f"Found {tables_info['tables_count']} tables.\n")
        
        # Analyze tables to find the most relevant one
        print("Analyzing tables with LLM (to find main table)...")
        llm_analysis = self.table_analyzer.analyze_tables(tables_info)
        
        if "metrics" in llm_analysis:
            self.metrics_collector.add_metrics(llm_analysis["metrics"], "Table Analyzer")
        
        # User selects table
        selected_table_index = self.table_analyzer.display_tables_and_get_selection(
            tables_info, llm_analysis
        )
        
        if selected_table_index is None:
            return {"status": "Error", "message": "No table selected"}
            
        selected_table = tables_info["tables"][selected_table_index]
        print(f"\nProcessing Table {selected_table_index + 1}...\n")
        
        # Generate schema
        print("Generating descriptive data schema with LLM...")
        schema_result = self.schema_generator.generate_schema(selected_table)
        
        if "metrics" in schema_result:
            self.metrics_collector.add_metrics(schema_result["metrics"], "Schema Generator")
        
        if "error" in schema_result:
            return {"status": "Error", "message": schema_result["error"]}
            
        schema = schema_result["schema"]
        
        # Add source metadata
        schema.metadata["source_url"] = url
        schema.metadata["table_index"] = selected_table_index
        
        return schema
    
    def from_file(self, file_path: str, output_format: str = "json") -> Union[Schema, Dict[str, Any]]:
        """
        Generate schema from a local HTML file.
        
        Args:
            file_path: Path to HTML file
            output_format: Format for the schema output (json, yaml, text)
            
        Returns:
            Schema object or error dictionary
        """
        # Read HTML and extract tables
        print("Detecting tables in HTML file...")
        tables_info = self.html_reader.read_from_file(file_path)
        
        if tables_info["tables_count"] == 0:
            print("No tables found in the HTML file.")
            return {"status": "Error", "message": "No tables found"}
            
        print(f"Found {tables_info['tables_count']} tables.\n")
        
        # Analyze tables to find the most relevant one
        print("Analyzing tables with LLM (to find main table)...")
        llm_analysis = self.table_analyzer.analyze_tables(tables_info)
        
        if "metrics" in llm_analysis:
            self.metrics_collector.add_metrics(llm_analysis["metrics"], "Table Analyzer")
        
        # User selects table
        selected_table_index = self.table_analyzer.display_tables_and_get_selection(
            tables_info, llm_analysis
        )
        
        if selected_table_index is None:
            return {"status": "Error", "message": "No table selected"}
            
        selected_table = tables_info["tables"][selected_table_index]
        print(f"\nProcessing Table {selected_table_index + 1}...\n")
        
        # Generate schema
        print("Generating descriptive data schema with LLM...")
        schema_result = self.schema_generator.generate_schema(selected_table)
        
        if "metrics" in schema_result:
            self.metrics_collector.add_metrics(schema_result["metrics"], "Schema Generator")
        
        if "error" in schema_result:
            return {"status": "Error", "message": schema_result["error"]}
            
        schema = schema_result["schema"]
        
        # Add source metadata
        schema.metadata["source_file"] = os.path.basename(file_path)
        schema.metadata["table_index"] = selected_table_index
        
        return schema
    
    def from_kaggle(self, url: str, output_format: str = "json") -> Union[Schema, Dict[str, Any]]:
        """
        Generate schema from a Kaggle dataset.
        
        Args:
            url: Kaggle dataset URL
            output_format: Format for the schema output (json, yaml, text)
            
        Returns:
            Schema object or error dictionary
        """
        print(f"Processing Kaggle dataset: {url}\n")
        
        # Process Kaggle dataset
        result = self.kaggle_integration.process_dataset(url)
        
        if result["status"] != "Success":
            print(f"Error: {result['message']}")
            return {"status": "Error", "message": result["message"]}
            
        csv_files = result["csv_files"]
        
        # User selects CSV file
        selected_csv = self.kaggle_integration.interactive_csv_selection(csv_files)
        
        if not selected_csv:
            return {"status": "Error", "message": "No CSV file selected"}
            
        print(f"Selected CSV: {selected_csv}")
        
        # Generate schema
        print("Generating descriptive data schema with LLM...")
        schema_result = self.kaggle_integration.generate_csv_schema(selected_csv)
        
        if "metrics" in schema_result:
            self.metrics_collector.add_metrics(schema_result["metrics"], "Schema Generator (CSV)")
        
        if "error" in schema_result:
            return {"status": "Error", "message": schema_result["error"]}
            
        schema = schema_result["schema"]
        
        # Add source metadata
        schema.metadata["source_type"] = "kaggle"
        schema.metadata["source_url"] = url
        schema.metadata["csv_file"] = os.path.basename(selected_csv)
        
        return schema
    
    def save_schema(self, schema: Union[Schema, Dict[str, Any]], output_path: str, 
                    format_type: str = None) -> None:
        """
        Save schema to a file.
        
        Args:
            schema: Schema object or dictionary
            output_path: Path to save the schema to
            format_type: Optional format type override
        """
        if isinstance(schema, Dict):
            if "status" in schema and schema["status"] == "Error":
                print(f"Error: {schema['message']}")
                return
            # If it's not a Schema object but a successful result, convert to string
            content = self.formatter.format_dict_schema(schema, format_type or "json")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Schema saved to {output_path}")
        else:
            # It's a Schema object
            self.formatter.save_schema(schema, output_path, format_type)
    
    def get_metrics_report(self) -> Dict[str, Any]:
        """
        Get a report of collected metrics.
        
        Returns:
            Dictionary with metrics report
        """
        return self.metrics_collector.get_metrics_report()
    
    def print_metrics_report(self) -> None:
        """Print a formatted metrics report."""
        metrics = self.get_metrics_report()
        
        if "Detailed Metrics" in metrics:
            detailed = metrics["Detailed Metrics"]
            if detailed:
                print("\n--- LLM Agents Metrics Report ---")
                df = pd.DataFrame(detailed)
                print(df)
        
        print("\n--- Overall Metrics ---")
        print(f"Total Processing Time: {metrics.get('Total Processing Time (s)', 0):.3f} s")
        print(f"Total Tokens: {metrics.get('Total Tokens', 0)}")

def cli_main():
    """Command-line interface entry point."""
    parser = argparse.ArgumentParser(description="HTML to Data Schema Converter for InterChat")
    
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--url", help="URL to HTML page with tables")
    source_group.add_argument("--file", help="Path to local HTML file")
    source_group.add_argument("--kaggle", help="Kaggle dataset URL")
    
    parser.add_argument("--output", help="Output file path", default="generated_schema.json")
    parser.add_argument("--format", choices=["json", "yaml", "text"], 
                       help="Output format", default="json")
    
    args = parser.parse_args()
    
    converter = SchemaConverter()
    
    try:
        if args.url:
            schema = converter.from_url(args.url, args.format)
        elif args.file:
            schema = converter.from_file(args.file, args.format)
        elif args.kaggle:
            schema = converter.from_kaggle(args.kaggle, args.format)
        
        converter.save_schema(schema, args.output, args.format)
        converter.print_metrics_report()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(cli_main())