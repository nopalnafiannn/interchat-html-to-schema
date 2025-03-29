"""
File Utilities Module
-------------------
Functions for handling file operations
"""

import os
import json
from pathlib import Path
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

def read_file(file_path, encoding='utf-8'):
    """
    Read content from a file
    
    Args:
        file_path (str): Path to the file
        encoding (str): File encoding
        
    Returns:
        str: File content or None if error
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
            
        with open(file_path, 'r', encoding=encoding) as f:
            content = f.read()
        return content
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None

def save_file(content, file_path, encoding='utf-8'):
    """
    Save content to a file
    
    Args:
        content (str): Content to save
        file_path (str): Path to save the file
        encoding (str): File encoding
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        file_path = Path(file_path)
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
            
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error saving file {file_path}: {e}")
        return False

def save_json(data, file_path, encoding='utf-8', indent=2):
    """
    Save data as JSON
    
    Args:
        data (dict): Data to save
        file_path (str): Path to save the JSON file
        encoding (str): File encoding
        indent (int): JSON indentation
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        file_path = Path(file_path)
        
        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)
            
        with open(file_path, 'w', encoding=encoding) as f:
            json.dump(data, f, indent=indent)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file {file_path}: {e}")
        return False

def load_json(file_path, encoding='utf-8'):
    """
    Load JSON data from a file
    
    Args:
        file_path (str): Path to the JSON file
        encoding (str): File encoding
        
    Returns:
        dict: Loaded JSON data or None if error
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return None
            
        with open(file_path, 'r', encoding=encoding) as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading JSON file {file_path}: {e}")
        return None

def get_file_extension(file_path):
    """
    Get the extension of a file
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: File extension (lowercase, without dot)
    """
    return Path(file_path).suffix.lower().lstrip('.')

def list_files(directory, extension=None):
    """
    List files in a directory
    
    Args:
        directory (str): Path to the directory
        extension (str, optional): Filter by file extension
        
    Returns:
        list: List of file paths
    """
    try:
        directory = Path(directory)
        if not directory.exists():
            logger.error(f"Directory not found: {directory}")
            return []
            
        files = []
        for file_path in directory.iterdir():
            if file_path.is_file():
                if extension is None or file_path.suffix.lower().lstrip('.') == extension.lower().lstrip('.'):
                    files.append(str(file_path))
        return files
    except Exception as e:
        logger.error(f"Error listing files in {directory}: {e}")
        return []