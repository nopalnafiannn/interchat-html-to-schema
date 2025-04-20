"""OpenAI client for LLM integration."""

import time
import os
import psutil
from typing import Dict, List, Any, Optional

import openai
from openai import OpenAI

from html_schema_converter.config import config

class OpenAIClient:
    """Client for interacting with OpenAI LLMs."""
    
    def __init__(self):
        """Initialize OpenAI client with API key from config."""
        api_key = config.get_openai_api_key()
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        
        # Set API key for both new and old OpenAI libraries
        openai.api_key = api_key
        self.client = OpenAI(api_key=api_key)
    
    def generate(self, prompt: str, model: str = "gpt-4o-mini", 
                 system_message: str = None, max_tokens: int = 1000, 
                 temperature: float = 0) -> Dict[str, Any]:
        """
        Generate text using OpenAI LLM.
        
        Args:
            prompt: User prompt
            model: LLM model to use
            system_message: Optional system message
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Dictionary with generated content and metrics
        """
        messages = []
        
        # Add system message if provided
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Add user prompt
        messages.append({"role": "user", "content": prompt})
        
        # Track metrics
        start_time = time.perf_counter()
        mem_before = psutil.Process(os.getpid()).memory_info().rss
        
        # Make API call
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            generated_text = response.choices[0].message.content
            
            # Extract token usage
            tokens_usage = {}
            if hasattr(response, "usage"):
                tokens_usage = response.usage
                if not isinstance(tokens_usage, dict):
                    # Convert to dict if it's an object
                    tokens_usage = tokens_usage.dict()
        except Exception as e:
            return {"content": f"Error: {str(e)}", "error": str(e)}
        
        # Calculate metrics
        end_time = time.perf_counter()
        mem_after = psutil.Process(os.getpid()).memory_info().rss
        latency = end_time - start_time
        mem_usage = (mem_after - mem_before) / (1024 * 1024)  # Convert to MB
        
        # Compile metrics
        metrics = {
            "Latency (s)": round(latency, 3),
            "Memory Usage (MB)": round(mem_usage, 3),
            "Prompt Tokens": tokens_usage.get('prompt_tokens', 0),
            "Completion Tokens": tokens_usage.get('completion_tokens', 0),
            "Total Tokens": tokens_usage.get('total_tokens', 0),
            "Model": model
        }
        
        return {
            "content": generated_text,
            "metrics": metrics
        }