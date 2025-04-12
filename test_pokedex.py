#!/usr/bin/env python
import sys
import os
from dotenv import load_dotenv
from html_schema_converter.main import SchemaConverter
from html_schema_converter.config import config
from html_schema_converter.utils.kaggle import KaggleIntegration

def load_api_key():
    """Load OpenAI API key from .env or environment."""
    # Try to load from .env file
    load_dotenv()
    
    api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        print("Error: OpenAI API key not found in environment or .env file.")
        sys.exit(1)
    
    return api_key

def non_interactive_kaggle_process(url):
    """Process a Kaggle dataset without interactive prompts."""
    print(f"Processing Kaggle dataset: {url}")
    
    # Initialize components
    converter = SchemaConverter()
    kaggle_integration = KaggleIntegration()
    
    # Set up credentials and parse dataset ID
    cred_result = kaggle_integration.setup_kaggle_credentials()
    if cred_result["status"] != "Success":
        print(f"Error setting up Kaggle credentials: {cred_result['message']}")
        return None
    
    try:
        dataset_id = kaggle_integration.parse_dataset_id(url)
        print(f"Parsed Kaggle dataset id: {dataset_id}")
    except ValueError as e:
        print(f"Error parsing dataset ID: {str(e)}")
        return None
    
    # Download dataset
    download_result = kaggle_integration.download_dataset(dataset_id)
    if download_result["status"] != "Success":
        print(f"Error downloading dataset: {download_result['message']}")
        return None
    
    # List CSV files
    csv_files = kaggle_integration.list_csv_files()
    if not csv_files:
        print("No CSV files found in the downloaded dataset.")
        return None
    
    # Auto-select first CSV file
    selected_csv = kaggle_integration.interactive_csv_selection(csv_files, auto_select=True)
    if not selected_csv:
        print("Error selecting CSV file.")
        return None
    
    # Generate schema
    print("Generating descriptive data schema with LLM...")
    schema_result = kaggle_integration.generate_csv_schema(selected_csv)
    
    if "error" in schema_result:
        print(f"Error generating schema: {schema_result['error']}")
        
    # Get the schema object
    schema = schema_result["schema"]
    
    # Add source metadata
    schema.metadata["source_type"] = "kaggle"
    schema.metadata["source_url"] = url
    schema.metadata["csv_file"] = os.path.basename(selected_csv)
    
    return schema

def main():
    """Test the Pokedex dataset schema generation."""
    print("== Testing Pokedex Dataset Schema Generation ==")
    
    # Load API key
    api_key = load_api_key()
    print("API key loaded successfully!")
    
    converter = SchemaConverter()
    
    try:
        # Process the specific Kaggle dataset
        kaggle_url = "https://www.kaggle.com/datasets/rzgiza/pokdex-for-all-1025-pokemon-w-text-description"
        
        schema = non_interactive_kaggle_process(kaggle_url)
        
        if schema:
            # Save as JSON
            output_file = "pokedex_schema.json"
            converter.save_schema(schema, output_file, "json")
            
            print(f"Complete! Schema saved to {output_file}")
        else:
            print("Failed to generate schema.")
            return 1
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())