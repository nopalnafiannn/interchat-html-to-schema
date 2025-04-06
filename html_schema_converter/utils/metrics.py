"""Metrics tracking utilities."""

import time
import os
import psutil
import functools
from typing import Dict, Any, Callable, Optional

def track_metrics(func: Callable) -> Callable:
    """
    Decorator to track performance metrics for functions.
    
    Args:
        func: Function to track
        
    Returns:
        Wrapped function with metrics tracking
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Track start time and memory
        start_time = time.perf_counter()
        mem_before = psutil.Process(os.getpid()).memory_info().rss
        
        # Call the function
        result = func(*args, **kwargs)
        
        # Calculate metrics
        end_time = time.perf_counter()
        mem_after = psutil.Process(os.getpid()).memory_info().rss
        
        latency = end_time - start_time
        mem_usage = (mem_after - mem_before) / (1024 * 1024)  # Convert to MB
        
        # Add metrics to result if it's a dict
        if isinstance(result, dict):
            # If there's already a metrics dict, update it
            if "metrics" in result and isinstance(result["metrics"], dict):
                result["metrics"].update({
                    "Function": func.__name__,
                    "Latency (s)": round(latency, 3),
                    "Memory Usage (MB)": round(mem_usage, 3)
                })
            else:
                # Otherwise create a new metrics dict
                result["metrics"] = {
                    "Function": func.__name__,
                    "Latency (s)": round(latency, 3),
                    "Memory Usage (MB)": round(mem_usage, 3)
                }
        
        return result
    
    return wrapper

class MetricsCollector:
    """Collects and aggregates metrics from different operations."""
    
    def __init__(self):
        """Initialize an empty metrics collection."""
        self.metrics = []
    
    def add_metrics(self, metrics_dict: Dict[str, Any], agent_name: Optional[str] = None) -> None:
        """
        Add metrics from an operation.
        
        Args:
            metrics_dict: Dictionary of metrics
            agent_name: Optional name of the agent that produced the metrics
        """
        metrics_entry = metrics_dict.copy()
        if agent_name:
            metrics_entry["Agent"] = agent_name
        self.metrics.append(metrics_entry)
    
    def get_metrics_report(self) -> Dict[str, Any]:
        """
        Generate a summary report of collected metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        if not self.metrics:
            return {"message": "No metrics collected"}
        
        # Calculate total latency
        total_latency = sum(m.get("Latency (s)", 0) for m in self.metrics)
        
        # Calculate total token usage if available
        total_prompt_tokens = sum(m.get("Prompt Tokens", 0) for m in self.metrics)
        total_completion_tokens = sum(m.get("Completion Tokens", 0) for m in self.metrics)
        total_tokens = sum(m.get("Total Tokens", 0) for m in self.metrics)
        
        # Create summary
        summary = {
            "Total Agents": len(self.metrics),
            "Total Processing Time (s)": round(total_latency, 3),
            "Total Prompt Tokens": total_prompt_tokens,
            "Total Completion Tokens": total_completion_tokens,
            "Total Tokens": total_tokens,
            "Detailed Metrics": self.metrics
        }
        
        return summary