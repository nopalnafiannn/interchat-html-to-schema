"""
Token Splitter Module
-------------------
Functions for splitting text into chunks based on token count
"""

import tiktoken
from src.utils.logging_utils import get_logger

logger = get_logger(__name__)

def split_text_by_tokens(text, max_tokens=7000, encoding_name="cl100k_base"):
    """
    Splits the text into chunks, each with token count <= max_tokens.
    
    Args:
        text (str): Text to split into chunks
        max_tokens (int): Maximum tokens per chunk
        encoding_name (str): Name of the tiktoken encoding to use
        
    Returns:
        tuple: (list of text chunks, total token count)
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    total_tokens = len(tokens)
    logger.info(f"Total token count: {total_tokens}")
    
    chunks = []
    start = 0
    
    while start < total_tokens:
        end = start + max_tokens
        if end > total_tokens:
            end = total_tokens
            
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        start = end
    
    # Log token distribution
    chunk_token_counts = [len(encoding.encode(chunk)) for chunk in chunks]
    logger.info(f"Created {len(chunks)} chunks with token counts: {chunk_token_counts}")
    
    return chunks, total_tokens

def count_tokens(text, encoding_name="cl100k_base"):
    """
    Count the number of tokens in a text
    
    Args:
        text (str): Text to count tokens in
        encoding_name (str): Name of the tiktoken encoding to use
        
    Returns:
        int: Number of tokens
    """
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    return len(tokens)

def estimate_token_cost(total_tokens, model="gpt-3.5-turbo"):
    """
    Estimate the cost of processing tokens with a given model
    
    Args:
        total_tokens (int): Number of tokens
        model (str): Model name
        
    Returns:
        float: Estimated cost in USD
    """
    # Approximate cost per 1000 tokens (rates as of March 2024)
    model_rates = {
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03}
    }
    
    if model not in model_rates:
        logger.warning(f"Unknown model: {model}, using gpt-3.5-turbo rates")
        model = "gpt-3.5-turbo"
    
    # Assuming 1:3 ratio of input:output tokens for estimation
    input_tokens = int(total_tokens * 0.75)
    output_tokens = int(total_tokens * 0.25)
    
    input_cost = (input_tokens / 1000) * model_rates[model]["input"]
    output_cost = (output_tokens / 1000) * model_rates[model]["output"]
    
    total_cost = input_cost + output_cost
    
    return total_cost