"""Main entry point for the HTML to Data Schema Converter."""

import os
import re
import pandas as pd
from .agents.html_reader import html_reader_agent
from .agents.table_analyzer import analyze_tables_with_llm
from .agents.schema_generator import generate_datascheme_with_llm
from .utils.formatters import format_schema, format_csv_schema
from .utils.kaggle import setup_kaggle_credentials, parse_dataset_id_from_url, generate_csv_schema
from .llm.openai_client import OpenAIClient
from .config import Config

from dotenv import load_dotenv
load_dotenv()

def display_tables_and_get_selection(tables_info, llm_analysis):
    """
    Displays information about tables and the LLM recommendation.
    
    Args:
        tables_info (dict): Tables information
        llm_analysis (dict): LLM analysis results
        
    Returns:
        int or None: Selected table index, or None if invalid
    """
    if tables_info["status"] != "Success":
        print(tables_info["status"])
        return None
    
    print(f"Found {tables_info['tables_count']} tables in the HTML document.\n")
    
    # Parse LLM recommendation
    main_table_rec = None
    reasoning = "No reasoning provided."
    table_type = "unknown"
    
    if llm_analysis["status"] == "Success":
        analysis_text = llm_analysis["raw_analysis"]
        main_table_match = re.search(r'Main Table:\s*(\d+)', analysis_text)
        if main_table_match:
            main_table_rec = int(main_table_match.group(1)) - 1
            
        reasoning_match = re.search(r'Reasoning:(.*?)(?:Table Type:|$)', analysis_text, re.DOTALL)
        if reasoning_match:
            reasoning = reasoning_match.group(1).strip()
            
        type_match = re.search(r'Table Type:\s*(\w+)', analysis_text)
        if type_match:
            table_type = type_match.group(1).strip()
    
    # Display tables
    for i, table in enumerate(tables_info["tables"]):
        print(f"Table {i+1}:")
        print(f"  Caption/Context: {table.get('caption', 'None')}")
        print(f"  Columns: {table['column_count']}")
        print(f"  Headers: {', '.join(table['headers'][:5])}{'...' if len(table['headers']) > 5 else ''}")
        print(f"  Rows: {table['row_count']}")
        if table['sample_data']:
            first_row = table['sample_data'][0]
            print(f"  Sample Row: {first_row[:3]}{'...' if len(first_row) > 3 else ''}")
        print()
    
    # Display recommendation
    if main_table_rec is not None:
        print("\nRecommendation:")
        print(f"  Recommended Table: Table {main_table_rec + 1}")
        print(f"  Reasoning: {reasoning}")
        print(f"  Table Type: {table_type}")
        print()
    
    # Handle table selection
    if tables_info["tables_count"] == 1:
        print("Only one table found. Automatically selecting it.")
        return 0
        
    if main_table_rec is not None and 0 <= main_table_rec < tables_info["tables_count"]:
        selection = input(f"Accept recommendation (Table {main_table_rec + 1})? (y/n): ")
        if selection.lower() == 'y':
            return main_table_rec
            
    selected = input(f"Select a table (1-{tables_info['tables_count']}): ")
    try:
        selected_idx = int(selected) - 1
        if 0 <= selected_idx < tables_info["tables_count"]:
            return selected_idx
    except:
        pass
        
    print("Invalid selection.")
    return None

def process_kaggle_dataset(url, config):
    """
    Downloads a Kaggle dataset from its URL, lets the user pick a CSV file,
    generates a CSV schema, and outputs it.
    
    Args:
        url (str): Kaggle dataset URL
        config (Config): Application configuration
    """
    # Setup Kaggle credentials
    setup_kaggle_credentials()

    # Import Kaggle API
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        raise ImportError("Please install kaggle package: !pip install kaggle")

    # Parse dataset ID and prepare download directory
    dataset_id = parse_dataset_id_from_url(url)
    print(f"Parsed Kaggle dataset id: {dataset_id}")

    download_path = config.get("kaggle", "download_path")
    if os.path.exists(download_path):
        import shutil
        shutil.rmtree(download_path)
    os.makedirs(download_path, exist_ok=True)

    # Download dataset
    api = KaggleApi()
    api.authenticate()
    print("Downloading dataset (this may take a few moments)...")
    api.dataset_download_files(dataset_id, path=download_path, unzip=True)
    print("Download complete and files unzipped.")

    # List CSV files
    import glob
    csv_files = glob.glob(os.path.join(download_path, "*.csv"))
    if not csv_files:
        print("No CSV files found in the downloaded dataset.")
        return

    # Select CSV file
    print("Available CSV files:")
    for i, file in enumerate(csv_files):
        print(f"{i+1}. {file}")
    choice = input(f"Choose a CSV file (1-{len(csv_files)}): ")
    try:
        selected_csv = csv_files[int(choice)-1]
    except (IndexError, ValueError):
        print("Invalid selection.")
        return

    # Generate schema
    print(f"Selected CSV: {selected_csv}")
    schema = generate_csv_schema(selected_csv)
    
    # Create dummy metrics
    metrics = {
        "Agent": "Kaggle CSV Schema Generation",
        "Latency (s)": 0,
        "Memory Usage (MB)": 0,
        "Prompt Tokens": 0,
        "Completion Tokens": 0,
        "Total Tokens": 0
    }
    
    # Select output format
    print("\nAvailable output formats:")
    print("1. Text (raw JSON string)")
    print("2. JSON (pretty-printed)")
    print("3. YAML")
    format_choice = input("Select output format (1-3, or press Enter for default=Text): ").strip()
    
    if format_choice == "2":
        fmt = "json"
    elif format_choice == "3":
        fmt = "yaml"
    else:
        fmt = "text"
    
    # Format and save output
    final_output = format_csv_schema(schema, fmt)
    print("\n--- Generated CSV Schema ---")
    print(final_output)
    
    output_filename = "generated_csv_schema"
    if fmt == "json":
        output_filename += ".json"
    elif fmt == "yaml":
        output_filename += ".yaml"
    else:
        output_filename += ".txt"
        
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_output)
        
    print(f"\nCSV schema generation complete! Saved to {output_filename}")
    
    # Display metrics
    print("\n--- LLM Agents Metrics Report (Kaggle Branch) ---")
    df = pd.DataFrame([metrics])
    print(df)

def process_html_url(url, config):
    """
    Processes an HTML URL to extract tables and generate a schema.
    
    Args:
        url (str): URL to process
        config (Config): Application configuration
    """
    # Create LLM client
    llm_client = OpenAIClient()
    
    # Extract tables
    print("Detecting tables in HTML...")
    tables_info = html_reader_agent(url)
    
    if tables_info["tables_count"] == 0:
        print("No tables found in the HTML document.")
        return
        
    print(f"Found {tables_info['tables_count']} tables.\n")
    
    # Analyze tables
    print("Analyzing tables with LLM (to find main table)...")
    llm_analysis = analyze_tables_with_llm(tables_info, llm_client)
    
    metrics_report = []
    if "metrics" in llm_analysis:
        metrics_report.append(llm_analysis["metrics"])
    
    # Select table
    selected_table_index = display_tables_and_get_selection(tables_info, llm_analysis)
    if selected_table_index is None:
        return
        
    selected_table = tables_info["tables"][selected_table_index]
    print(f"\nProcessing Table {selected_table_index + 1}...\n")
    
    # Generate schema
    print("Generating descriptive data schema (JSON) with LLM...")
    schema = generate_datascheme_with_llm(selected_table, llm_client)
    
    if "metrics" in schema:
        metrics_report.append(schema["metrics"])
    
    # Select output format
    print("\nAvailable output formats:")
    print("1. Text (raw JSON string)")
    print("2. JSON (pretty-printed)")
    print("3. YAML")
    format_choice = input("Select output format (1-3, or press Enter for default=Text): ").strip()
    
    if format_choice == "2":
        format_type = "json"
    elif format_choice == "3":
        format_type = "yaml"
    else:
        format_type = "text"
    
    # Format and save output
    final_output = format_schema(schema, format_type)
    print("\n--- Generated Schema ---")
    print(final_output)
    
    output_filename = "generated_schema"
    if format_type == "json":
        output_filename += ".json"
    elif format_type == "yaml":
        output_filename += ".yaml"
    else:
        output_filename += ".txt"
        
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_output)
        
    print(f"\nSchema generation complete! Saved to {output_filename}")
    
    # Display metrics
    if metrics_report:
        print("\n--- LLM Agents Metrics Report ---")
        df = pd.DataFrame(metrics_report)
        print(df)

def main():
    """Main entry point for the application."""
    # Load configuration
    config = Config()
    
    print("=" * 50)
    print("HTML to Data Schema Converter (Descriptive Format)")
    print("=" * 50)
    
    url = input("Enter the URL of the page to analyze (can be an HTML page or a Kaggle dataset URL): ").strip()
    print(f"Processing URL: {url}\n")
    
    if "kaggle.com/datasets" in url:
        process_kaggle_dataset(url, config)
    else:
        process_html_url(url, config)

if __name__ == "__main__":
    main()