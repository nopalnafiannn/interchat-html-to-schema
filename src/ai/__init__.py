"""
AI package
--------
Contains modules for OpenAI client configuration and prompts.
"""

# Import key functions to make them available at the package level
from src.ai.client import get_openai_client, is_api_key_valid

# Import prompt templates
from src.ai.prompts import (
    RAW_HTML_ANALYSIS_PROMPT,
    IMPROVED_COMBINE_PROMPT,
    DESCRIPTION_ANALYSIS_PROMPT,
    SCHEMA_IMPROVEMENT_PROMPT,
    SCHEMA_QUALITY_CHECK_PROMPT
)