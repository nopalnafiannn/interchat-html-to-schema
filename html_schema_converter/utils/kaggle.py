"""Kaggle integration utilities for the HTML to Data Schema Converter."""

import os
import json
import shutil
import glob
import pandas as pd

def setup_kaggle_credentials():
    """
    Retrieves Kaggle credentials and writes the kaggle.json file.
    
    Raises:
        Exception: If Kaggle credentials are not found
    """
    # Try environment variables first
    kaggle_username = os.environ.get("KAGGLE_USERNAME")
    kaggle_key = os.environ.get("KAGGLE_SECRET_KEY")
    
    # Try Colab secrets if not found
    if not kaggle_username or not kaggle_key:
        try:
            from google.colab import userdata
            kaggle_username = userdata.get("KAGGLE_USERNAME")
            kaggle_key = userdata.get("KAGGLE_SECRET_KEY")
        except (ImportError, AttributeError):
            pass
    
    if not kaggle_username or not kaggle_key:
        raise Exception("Kaggle credentials not found in environment or Colab secrets.")
    
    # Create Kaggle directory and credentials file
    kaggle_json = {"username": kaggle_username, "key": kaggle_key}
    kaggle_dir = os.path.join(os.path.expanduser("~"), ".kaggle")
    if not os.path.exists(kaggle_dir):
        os.makedirs(kaggle_dir, exist_ok=True)
    
    with open(os.path.join(kaggle_dir, "kaggle.json"), "w") as f:
        json.dump(kaggle_json, f)
    
    # Set permissions to 600
    os.chmod(os.path.join(kaggle_dir, "kaggle.json"), 0o600)

def generate_csv_schema(csv_file):
    """
    Generates a simple schema from a CSV file.
    
    Args:
        csv_file (str): Path to CSV file
        
    Returns:
        dict: Schema dictionary
    """
    try:
        df = pd.read_csv(csv_file, nrows=100)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return {"schema": []}

    schema = {"schema": []}
    for col in df.columns:
        dtype = str(df[col].dtype)
        description = f"Column '{col}' with inferred type {dtype}"
        schema["schema"].append({
            "column_name": col,
            "type": dtype,
            "description": description
        })
    return schema

def parse_dataset_id_from_url(url):
    """
    Parses Kaggle dataset ID from URL.
    
    Args:
        url (str): Kaggle dataset URL
        
    Returns:
        str: Dataset ID
    """
    url = url.strip().rstrip("/")
    parts = url.split('/')
    dataset_id = parts[-2] + "/" + parts[-1]
    return dataset_id

def format_csv_schema(schema, format_type="text"):
    """
    Formats a CSV schema in the desired format.
    
    Args:
        schema (dict): Schema dictionary
        format_type (str): Output format (text, json, or yaml)
        
    Returns:
        str: Formatted schema
    """
    if format_type.lower() == "json":
        return json.dumps(schema, indent=2)
    elif format_type.lower() == "yaml":
        import yaml
        return yaml.dump(schema, sort_keys=False, default_flow_style=False)
    else:
        return json.dumps(schema)