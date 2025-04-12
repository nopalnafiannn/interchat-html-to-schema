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
from html_schema_converter.agents.schema_refiner import SchemaRefiner
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
        self.schema_refiner = SchemaRefiner()
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
            self.metrics_collector.add_metrics(llm_analysis["metrics"], "Table Analyzer", is_feedback=False)
        
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
            self.metrics_collector.add_metrics(schema_result["metrics"], "Schema Generator", is_feedback=False)
        
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
            self.metrics_collector.add_metrics(llm_analysis["metrics"], "Table Analyzer", is_feedback=False)
        
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
            self.metrics_collector.add_metrics(schema_result["metrics"], "Schema Generator", is_feedback=False)
        
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
            self.metrics_collector.add_metrics(schema_result["metrics"], "Schema Generator (CSV)", is_feedback=False)
        
        if "error" in schema_result:
            return {"status": "Error", "message": schema_result["error"]}
        
        # Get the schema object
        schema = schema_result["schema"]
        
        # Debug to verify we have a Schema object
        print(f"DEBUG main.py: Schema type before metadata: {type(schema)}")
        
        # Ensure schema is a Schema object and not a dictionary
        if schema is None:
            # Create an empty schema instead of returning an error
            print(f"DEBUG main.py: Creating empty Schema object for null schema")
            schema = Schema(
                name=f"CSV Schema: {os.path.basename(selected_csv)}",
                description=f"Generated schema for {os.path.basename(selected_csv)}"
            )
            print(f"DEBUG main.py: Created empty Schema object: {type(schema)} and {schema.name}")
        elif not isinstance(schema, Schema):
            print(f"DEBUG main.py: Converting to Schema object in main.py")
            try:
                if isinstance(schema, dict):
                    try:
                        schema = Schema.from_dict(schema)
                        print(f"DEBUG main.py: Successfully converted to Schema object")
                    except Exception as conv_error:
                        print(f"DEBUG main.py: Error in Schema.from_dict: {str(conv_error)}")
                        # Create a new Schema manually from the dictionary
                        columns = []
                        for col_data in schema.get("columns", schema.get("schema", [])):
                            try:
                                name = col_data.get("name", col_data.get("column_name", f"Column_{len(columns)+1}"))
                                columns.append(SchemaColumn(
                                    name=name,
                                    type=col_data.get("type", "string"),
                                    description=col_data.get("description", f"Column containing {name} data"),
                                    nullable=col_data.get("nullable", True),
                                    confidence=col_data.get("confidence", 1.0),
                                    inferred=col_data.get("inferred", False)
                                ))
                            except Exception as col_error:
                                print(f"DEBUG main.py: Error creating column: {str(col_error)}")
                                
                        schema = Schema(
                            name=schema.get("name", f"CSV Schema: {os.path.basename(selected_csv)}"),
                            description=schema.get("description", f"Generated schema for {os.path.basename(selected_csv)}"),
                            columns=columns
                        )
                        print(f"DEBUG main.py: Created Schema object manually: {type(schema)}")
                else:
                    return {"status": "Error", "message": f"Expected Schema object, got {type(schema)}"}
            except Exception as e:
                print(f"DEBUG main.py: Fallback to empty schema due to: {str(e)}")
                schema = Schema(
                    name=f"CSV Schema: {os.path.basename(selected_csv)}",
                    description=f"Fallback schema due to conversion error: {str(e)}"
                )
                return {"status": "Success", "schema": schema}
        
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
        # Debug information
        print(f"DEBUG: Schema type: {type(schema)}")
        
        # Handle None case
        if schema is None:
            print("DEBUG: Creating empty Schema object for null schema")
            schema = Schema(
                name="Empty Schema",
                description="This schema was created when a null schema was encountered."
            )
        
        if isinstance(schema, dict):
            if "status" in schema and schema["status"] == "Error":
                print(f"Error: {schema['message']}")
                return
                
            # If it's a dictionary containing a 'schema' key, extract it
            if "schema" in schema and isinstance(schema["schema"], Schema):
                print("DEBUG: Extracting Schema object from dict['schema']")
                schema = schema["schema"]
            elif "schema" in schema and schema["schema"] is None:
                print("DEBUG: Creating Schema for None value in dict['schema']")
                schema = Schema(
                    name="Empty Schema",
                    description="This schema was created when a null schema was encountered."
                )
            else:
                # It's a dictionary to be formatted directly
                print("DEBUG: Formatting dictionary schema")
                content = self.formatter.format_dict_schema(schema, format_type or "json")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Schema saved to {output_path}")
                return
                
        # At this point, schema should be a Schema object
        if not isinstance(schema, Schema):
            print(f"DEBUG: Converting dict to Schema before saving")
            try:
                schema = Schema.from_dict(schema)
            except Exception as e:
                print(f"Error converting to Schema object: {str(e)}")
                return
        
        # It's a Schema object - save it
        print(f"DEBUG: Saving Schema object to {output_path}")
        try:
            self.formatter.save_schema(schema, output_path, format_type)
            print(f"Schema successfully saved to {output_path}")
        except Exception as e:
            print(f"Error saving schema: {str(e)}")
    
    def process_human_feedback(self, schema: Schema, feedback: str) -> Schema:
        """
        Process human feedback to refine the schema with improved type inference.
        
        Args:
            schema: Original Schema object
            feedback: Human feedback string
            
        Returns:
            Refined Schema object with improved types and constraints
        """
        print("Processing human feedback to refine schema...")
        feedback_dict = {"user_feedback": feedback}
        
        # Use the schema refiner to incorporate feedback
        result = self.schema_refiner.refine_schema(schema, feedback_dict)
        
        if "error" in result:
            print(f"Error refining schema: {result['error']}")
            return schema
            
        # Add feedback metrics with the is_feedback flag
        if "metrics" in result:
            self.metrics_collector.add_metrics(result["metrics"], "Schema Refiner", is_feedback=True)
            
        print("Schema successfully refined with human feedback.")
        return result["schema"]
    
    def get_metrics_report(self) -> Dict[str, Any]:
        """
        Get a report of collected metrics.
        
        Returns:
            Dictionary with metrics report
        """
        return self.metrics_collector.get_metrics_report()
    
    def print_metrics_report(self) -> None:
        """Print a formatted metrics report with separate tracking for initial generation and feedback."""
        metrics = self.get_metrics_report()
        
        # Print initial generation metrics
        if "Initial Generation Metrics" in metrics and metrics["Initial Generation Metrics"]:
            print("\n--- Initial LLM Generation Metrics ---")
            initial_df = pd.DataFrame(metrics["Initial Generation Metrics"])
            print(initial_df)
            
            initial_summary = metrics.get("Initial Generation", {})
            print(f"Total Initial Processing Time: {initial_summary.get('Total Processing Time (s)', 0):.3f} s")
            print(f"Total Initial Tokens: {initial_summary.get('Total Tokens', 0)}")
        
        # Print feedback iteration metrics if any
        if "Feedback Iteration Metrics" in metrics and metrics["Feedback Iteration Metrics"]:
            print("\n--- Feedback Iteration Metrics ---")
            feedback_df = pd.DataFrame(metrics["Feedback Iteration Metrics"])
            print(feedback_df)
            
            feedback_summary = metrics.get("Feedback Iterations", {})
            print(f"Total Feedback Processing Time: {feedback_summary.get('Total Processing Time (s)', 0):.3f} s")
            print(f"Total Feedback Tokens: {feedback_summary.get('Total Tokens', 0)}")
        
        # Print overall combined metrics
        print("\n--- Overall Combined Metrics ---")
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
    parser.add_argument("--feedback", help="Human feedback to refine schema types and constraints")
    
    args = parser.parse_args()
    
    converter = SchemaConverter()
    
    try:
        if args.url:
            schema = converter.from_url(args.url, args.format)
        elif args.file:
            schema = converter.from_file(args.file, args.format)
        elif args.kaggle:
            schema = converter.from_kaggle(args.kaggle, args.format)
        
        # Process human feedback if provided
        if args.feedback:
            schema = converter.process_human_feedback(schema, args.feedback)
            
        converter.save_schema(schema, args.output, args.format)
        converter.print_metrics_report()
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(cli_main())