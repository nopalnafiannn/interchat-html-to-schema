"""Configuration management for HTML to Data Schema Converter."""

import os
import yaml
from typing import Dict, Any, Optional

class Config:
    """Manages configuration for the HTML to Data Schema Converter."""

    DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration with a custom path or the default path.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Dict with configuration values
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, "r") as f:
                return yaml.safe_load(f)
        return {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key (can use dot notation for nested keys)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split(".")
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def get_env(self, key: str, env_var: str, default: Any = None) -> Any:
        """
        Get a configuration value with environment variable fallback.

        Args:
            key: Configuration key
            env_var: Environment variable name
            default: Default value if neither config nor env var exists

        Returns:
            Configuration value
        """
        # Try environment variable first
        env_value = os.environ.get(env_var)
        if env_value is not None:
            return env_value
            
        # Then try config file
        config_value = self.get(key)
        if config_value is not None:
            return config_value
            
        # Fall back to default
        return default

    def get_openai_api_key(self) -> Optional[str]:
        """
        Get OpenAI API key from environment or config.

        Returns:
            OpenAI API key if found, None otherwise
        """
        # Try different sources, prioritizing environment
        return (os.environ.get("OPENAI_API_KEY") or 
                self.get("llm.api_key"))

    def get_kaggle_credentials(self) -> Dict[str, str]:
        """
        Get Kaggle credentials from environment or config.

        Returns:
            Dict with username and key if found, empty dict otherwise
        """
        username = os.environ.get("KAGGLE_USERNAME") or self.get("kaggle.username")
        key = os.environ.get("KAGGLE_SECRET_KEY") or self.get("kaggle.key")
        
        if username and key:
            return {"username": username, "key": key}
        return {}

# Global config instance
config = Config()