"""Metrics collection utilities for the HTML to Data Schema Converter."""

import time
import psutil
import os
from typing import Dict, Any, Callable, TypeVar, Optional
import pandas as pd

# Type variable for the decorated function
T = TypeVar('T')

def measure_performance(agent_name: str) -> Callable[[Callable[..., T]], Callable[..., Dict[str, Any]]]:
    """
    Decorator to measure function performance.
    
    Args:
        agent_name (str): Name of the agent being measured
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Dict[str, Any]]:
        def wrapper(*args, **kwargs) -> Dict[str, Any]:
            # Measure start state
            start_time = time.perf_counter()
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Call the function
            result = func(*args, **kwargs)
            
            # Measure end state
            end_time = time.perf_counter()
            mem_after = process.memory_info().rss / (1024 * 1024)  # MB
            
            # Calculate metrics
            latency = end_time - start_time
            memory_used = mem_after - mem_before
            
            # Add metrics to result
            metrics = {
                "Agent": agent_name,
                "Latency (s)": round(latency, 3),
                "Memory Usage (MB)": round(memory_used, 3)
            }
            
            if isinstance(result, dict):
                if "metrics" in result:
                    result["metrics"].update(metrics)
                else:
                    result["metrics"] = metrics
            else:
                # If result is not a dict, wrap it
                result = {
                    "result": result,
                    "metrics": metrics
                }
            
            return result
        return wrapper
    return decorator

def generate_metrics_report(metrics_list: list) -> Optional[pd.DataFrame]:
    """
    Generate a DataFrame report from metrics data.
    
    Args:
        metrics_list (list): List of metrics dictionaries
        
    Returns:
        pandas.DataFrame or None: Metrics report
    """
    if not metrics_list:
        return None
    
    return pd.DataFrame(metrics_list)

def log_metrics(metrics: Dict[str, Any], output_file: str = "metrics_log.csv") -> None:
    """
    Log metrics to a CSV file.
    
    Args:
        metrics (dict): Metrics dictionary
        output_file (str): Path to output file
    """
    df = pd.DataFrame([metrics])
    file_exists = os.path.isfile(output_file)
    
    if file_exists:
        df.to_csv(output_file, mode='a', header=False, index=False)
    else:
        df.to_csv(output_file, index=False)