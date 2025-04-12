"""Kaggle integration for HTML to Data Schema Converter."""

import os
import json
import glob
import shutil
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

from html_schema_converter.config import config
from html_schema_converter.agents.schema_generator import SchemaGenerator
from html_schema_converter.models.schema import Schema, SchemaColumn

class KaggleIntegration:
    """Handles integration with Kaggle datasets."""
    
    def __init__(self):
        """Initialize Kaggle integration with configuration."""
        self.download_path = config.get("kaggle.download_path", "kaggle_data")
        self.schema_generator = SchemaGenerator()
    
    def setup_kaggle_credentials(self) -> Dict[str, str]:
        """
        Set up Kaggle credentials from config or environment.
        
        Returns:
            Dictionary with credential status
        """
        kaggle_credentials = config.get_kaggle_credentials()
        
        if not kaggle_credentials or 'username' not in kaggle_credentials or 'key' not in kaggle_credentials:
            return {"status": "Error", "message": "Kaggle credentials not found in environment or config."}
        
        # Create Kaggle directory if it doesn't exist
        kaggle_dir = os.path.join(os.path.expanduser("~"), ".kaggle")
        if not os.path.exists(kaggle_dir):
            os.makedirs(kaggle_dir, exist_ok=True)
        
        # Write kaggle.json
        with open(os.path.join(kaggle_dir, "kaggle.json"), "w") as f:
            json.dump(kaggle_credentials, f)
        
        # Set permissions
        os.chmod(os.path.join(kaggle_dir, "kaggle.json"), 0o600)
        
        return {"status": "Success", "message": "Kaggle credentials configured."}
    
    def parse_dataset_id(self, url: str) -> str:
        """
        Parse dataset ID from Kaggle URL.
        
        Args:
            url: Kaggle dataset URL
            
        Returns:
            Dataset ID in format "username/dataset-name"
        """
        url = url.strip().rstrip("/")
        parts = url.split('/')
        
        if len(parts) < 2:
            raise ValueError("Invalid Kaggle dataset URL")
            
        dataset_id = parts[-2] + "/" + parts[-1]
        return dataset_id
    
    def download_dataset(self, dataset_id: str) -> Dict[str, Any]:
        """
        Download a Kaggle dataset.
        
        Args:
            dataset_id: Dataset ID in format "username/dataset-name"
            
        Returns:
            Dictionary with download status
        """
        # Import Kaggle API
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
        except ImportError:
            return {"status": "Error", "message": "Please install kaggle package: pip install kaggle"}
        
        # Clear previous download directory
        if os.path.exists(self.download_path):
            shutil.rmtree(self.download_path)
        os.makedirs(self.download_path, exist_ok=True)
        
        # Authenticate and download
        try:
            api = KaggleApi()
            api.authenticate()
            api.dataset_download_files(dataset_id, path=self.download_path, unzip=True)
            return {"status": "Success", "message": "Dataset downloaded successfully."}
        except Exception as e:
            return {"status": "Error", "message": f"Failed to download dataset: {str(e)}"}
    
    def list_csv_files(self) -> List[str]:
        """
        List CSV files in the download directory.
        
        Returns:
            List of CSV file paths
        """
        return glob.glob(os.path.join(self.download_path, "*.csv"))
    
    def generate_csv_schema(self, csv_file: str) -> Dict[str, Any]:
        """
        Generate schema from a CSV file.
        
        Args:
            csv_file: Path to CSV file
            
        Returns:
            Dictionary with generated schema
        """
        try:
            # Read sample of CSV file
            df = pd.read_csv(csv_file, nrows=100)
        except Exception as e:
            print(f"DEBUG: Error reading CSV: {str(e)}")
            # Create a default schema object instead of returning None
            default_schema = Schema(
                name=f"CSV Schema: {os.path.basename(csv_file)}",
                description=f"Error reading CSV file: {str(e)}"
            )
            return {"schema": default_schema, "error": f"Error reading CSV: {str(e)}"}
        
        # Extract headers and sample data
        headers = list(df.columns)
        
        # Create fallback columns for the schema in case everything else fails
        fallback_columns = []
        for header in headers:
            fallback_columns.append(SchemaColumn(
                name=header,
                type="string",
                description=f"Column containing {header} data",
                nullable=True,
                inferred=True,
                confidence=0.5
            ))
        
        # Get a sample of the data
        sample_data = df.head(5).values.tolist()
        
        # Create table_info dict in the same format used for HTML tables
        table_info = {
            "headers": headers,
            "sample_data": sample_data
        }
        
        try:
            # Generate schema
            result = self.schema_generator.generate_schema(table_info)
            
            # Debug information to track what's returned
            print(f"DEBUG: Schema type: {type(result.get('schema'))}")
            
            # Ensure we return a Schema object and not a dictionary
            if result.get("schema") is None:
                # Create an empty schema object rather than returning None
                print(f"DEBUG: Creating fallback Schema object for null schema")
                result["schema"] = Schema(
                    name=f"CSV Schema: {os.path.basename(csv_file)}",
                    description=f"Generated schema for {os.path.basename(csv_file)}",
                    columns=fallback_columns
                )
                print(f"DEBUG: Created fallback Schema object: {type(result['schema'])}")
            elif not isinstance(result["schema"], Schema):
                print(f"DEBUG: Converting dictionary to Schema object")
                if isinstance(result["schema"], dict):
                    try:
                        result["schema"] = Schema.from_dict(result["schema"])
                        print(f"DEBUG: Successfully converted to Schema object: {type(result['schema'])}")
                    except Exception as e:
                        print(f"DEBUG: Schema conversion error: {str(e)}")
                        print(f"DEBUG: Dictionary content: {result['schema']}")
                        # Create a fallback schema instead of returning an error
                        result["schema"] = Schema(
                            name=f"CSV Schema: {os.path.basename(csv_file)}",
                            description=f"Fallback schema due to conversion error: {str(e)}",
                            columns=fallback_columns
                        )
                else:
                    print(f"DEBUG: Unexpected schema type: {type(result['schema'])}")
                    # Create a fallback schema instead of returning an error
                    result["schema"] = Schema(
                        name=f"CSV Schema: {os.path.basename(csv_file)}",
                        description=f"Fallback schema due to unexpected type: {type(result['schema'])}",
                        columns=fallback_columns
                    )
            
            return result
        except Exception as e:
            print(f"DEBUG: Unexpected error in generate_csv_schema: {str(e)}")
            # Create a fallback schema in case everything fails
            fallback_schema = Schema(
                name=f"CSV Schema: {os.path.basename(csv_file)}",
                description=f"Fallback schema due to unexpected error: {str(e)}",
                columns=fallback_columns
            )
            return {"schema": fallback_schema, "error": f"Unexpected error: {str(e)}"}
    
    def process_dataset(self, url: str) -> Dict[str, Any]:
        """
        Process a Kaggle dataset from URL to schema.
        
        Args:
            url: Kaggle dataset URL
            
        Returns:
            Dictionary with processing results
        """
        # Set up credentials
        cred_result = self.setup_kaggle_credentials()
        if cred_result["status"] != "Success":
            return cred_result
        
        # Parse dataset ID
        try:
            dataset_id = self.parse_dataset_id(url)
            print(f"Parsed Kaggle dataset id: {dataset_id}")
        except ValueError as e:
            return {"status": "Error", "message": str(e)}
        
        # Download dataset
        download_result = self.download_dataset(dataset_id)
        if download_result["status"] != "Success":
            return download_result
        
        # List CSV files
        csv_files = self.list_csv_files()
        if not csv_files:
            return {"status": "Error", "message": "No CSV files found in the downloaded dataset."}
        
        # Return list of available CSV files
        return {
            "status": "Success",
            "message": "Dataset processed successfully.",
            "csv_files": csv_files
        }
    
    def interactive_csv_selection(self, csv_files: List[str], auto_select: bool = False) -> Optional[str]:
        """
        Interactive selection of CSV file.
        
        Args:
            csv_files: List of CSV file paths
            auto_select: If True, automatically select the first CSV file
            
        Returns:
            Selected CSV file path or None if invalid selection
        """
        print("Available CSV files:")
        for i, file in enumerate(csv_files):
            print(f"{i+1}. {file}")
            
        # Default to auto-select in non-interactive environments
        if (auto_select and csv_files) or not csv_files:
            if csv_files:
                print(f"Auto-selecting file 1: {csv_files[0]}")
                return csv_files[0]
            else:
                return None
            
        try:
            choice = input(f"Choose a CSV file (1-{len(csv_files)}): ")
        except EOFError:
            # Handle non-interactive environment
            print("Non-interactive environment detected. Auto-selecting first CSV file.")
            if csv_files:
                return csv_files[0]
            return None
        
        try:
            selected_csv = csv_files[int(choice)-1]
            return selected_csv
        except (IndexError, ValueError):
            print("Invalid selection. Auto-selecting first CSV file.")
            if csv_files:
                return csv_files[0]
            return None