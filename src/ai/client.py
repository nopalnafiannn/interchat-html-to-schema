"""
OpenAI Client Module
------------------
Functions for setting up and managing the OpenAI client
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

# Ensure environment variables are loaded
load_dotenv()

def get_openai_client():
    """
    Get an OpenAI client instance with API key from environment variables
    
    Returns:
        OpenAI: OpenAI client instance
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    return OpenAI(api_key=api_key)

def is_api_key_valid():
    """
    Check if the OpenAI API key is valid
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        client = get_openai_client()
        # Make a small request to check if the API key is valid
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=5
        )
        return True
    except Exception as e:
        logger.error(f"API key validation failed: {e}")
        return False