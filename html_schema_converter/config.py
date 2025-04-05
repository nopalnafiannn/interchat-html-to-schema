"""Configuration management for the HTML to Data Schema Converter."""

import os
import yaml
from typing import Dict, Any, Optional

# Default configuration file path
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')

class Config:
    """Configuration manager for the application."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration.
        
        Args:
            config_path (str, optional): Path to the configuration file. 
                                         If None, uses the default path.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Load the configuration from the YAML file.
        
        Returns:
            dict: Configuration dictionary
        """
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_path} not found. Using default settings.")
            return self._default_config()
    
    def _default_config(self) -> Dict[str, Any]:
        """
        Provide default configuration if the config file is not found.
        
        Returns:
            dict: Default configuration dictionary
        """
        return {
            "openai": {
                "default_model": "gpt-3.5-turbo",
                "schema_model": "gpt-3.5-turbo-16k",
                "max_tokens": 1000,
                "temperature": 0
            },
            "html": {
                "max_file_size_mb": 10,
                "max_sample_rows": 5
            },
            "schema": {
                "output_formats": ["text", "json", "yaml"],
                "default_format": "json"
            },
            "kaggle": {
                "download_path": "kaggle_data"
            },
            "metrics": {
                "track_latency": True,
                "track_memory": True,
                "track_tokens": True
            }
        }
    
    def get(self, section: str, key: Optional[str] = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section (str): Configuration section
            key (str, optional): Configuration key. If None, returns the entire section.
            
        Returns:
            any: Configuration value
        """
        if section not in self.config:
            raise KeyError(f"Configuration section '{section}' not found")
        
        if key is None:
            return self.config[section]
        
        if key not in self.config[section]:
            raise KeyError(f"Configuration key '{key}' not found in section '{section}'")
        
        return self.config[section][key]