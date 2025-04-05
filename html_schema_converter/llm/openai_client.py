"""OpenAI client for the HTML to Data Schema Converter."""

import os
import time
import psutil
from openai import OpenAI

class OpenAIClient:
    """Client for interacting with OpenAI API."""
    
    def __init__(self, api_key=None):
        """
        Initialize the OpenAI client.
        
        Args:
            api_key (str, optional): OpenAI API key. If None, attempts to get from environment.
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            try:
                from google.colab import userdata
                self.api_key = userdata.get('OPENAI_API_KEY')
            except (ImportError, AttributeError):
                pass
                
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Please provide it or set OPENAI_API_KEY environment variable.")
            
        self.client = OpenAI(api_key=self.api_key)
        
    def generate_completion(self, system_prompt, user_prompt, model="gpt-3.5-turbo", max_tokens=1000, temperature=0):
        """
        Generate a completion using OpenAI's API.
        
        Args:
            system_prompt (str): System prompt
            user_prompt (str): User prompt
            model (str, optional): Model to use. Defaults to "gpt-3.5-turbo".
            max_tokens (int, optional): Maximum tokens to generate. Defaults to 1000.
            temperature (float, optional): Temperature parameter. Defaults to 0.
            
        Returns:
            tuple: (response_text, metrics)
        """
        start_time = time.perf_counter()
        mem_before = psutil.Process(os.getpid()).memory_info().rss
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        end_time = time.perf_counter()
        mem_after = psutil.Process(os.getpid()).memory_info().rss
        latency = end_time - start_time
        mem_usage = (mem_after - mem_before) / (1024 * 1024)
        
        result = response.choices[0].message.content
        tokens_usage = response.usage if hasattr(response, "usage") else {}
        if not isinstance(tokens_usage, dict):
            tokens_usage = tokens_usage.dict()
            
        metrics = {
            "Latency (s)": round(latency, 3),
            "Memory Usage (MB)": round(mem_usage, 3),
            "Prompt Tokens": tokens_usage.get('prompt_tokens', 0),
            "Completion Tokens": tokens_usage.get('completion_tokens', 0),
            "Total Tokens": tokens_usage.get('total_tokens', 0)
        }
        
        return result, metrics