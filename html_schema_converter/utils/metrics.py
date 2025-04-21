"""Metrics tracking utilities."""

import time
import os
import psutil
import functools
from typing import Dict, Any, Callable, Optional, List

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
        mem_usage = abs(mem_after - mem_before) / (1024 * 1024)  # Convert to MB
        
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
        """Initialize empty metrics collections for initial generation and feedback iterations."""
        self.initial_metrics = []  # Metrics for initial LLM generation
        self.feedback_metrics = []  # Metrics for human feedback iterations
    
    def add_metrics(self, metrics_dict: Dict[str, Any], agent_name: Optional[str] = None, is_feedback: bool = False) -> None:
        """
        Add metrics from an operation, separating initial generation from feedback iterations.
        
        Args:
            metrics_dict: Dictionary of metrics
            agent_name: Optional name of the agent that produced the metrics
            is_feedback: Flag indicating if these metrics are from a feedback iteration
        """
        metrics_entry = metrics_dict.copy()
        if agent_name:
            metrics_entry["Agent"] = agent_name
        
        # Add to the appropriate collection based on whether this is feedback or initial generation
        if is_feedback:
            self.feedback_metrics.append(metrics_entry)
        else:
            self.initial_metrics.append(metrics_entry)
    
    def get_metrics_report(self) -> Dict[str, Any]:
        """
        Generate a detailed summary report of collected metrics, separating initial generation 
        from feedback iterations to provide more accurate performance insights.
        
        Returns:
            Dictionary with separated metrics summaries
        """
        if not self.initial_metrics and not self.feedback_metrics:
            return {"message": "No metrics collected"}
        
        # Process initial generation metrics
        initial_summary = self._calculate_summary(self.initial_metrics, "Initial Generation")
        
        # Process feedback iteration metrics
        feedback_summary = self._calculate_summary(self.feedback_metrics, "Feedback Iterations")
        
        # Combine summaries
        combined_latency = initial_summary.get("Total Processing Time (s)", 0) + \
                         feedback_summary.get("Total Processing Time (s)", 0)
        
        combined_tokens = initial_summary.get("Total Tokens", 0) + \
                         feedback_summary.get("Total Tokens", 0)
        
        # Create comprehensive summary
        summary = {
            "Total Agents": len(self.initial_metrics) + len(self.feedback_metrics),
            "Total Processing Time (s)": round(combined_latency, 3),
            "Total Tokens": combined_tokens,
            "Initial Generation": initial_summary,
            "Feedback Iterations": feedback_summary,
            "Initial Generation Metrics": self.initial_metrics,
            "Feedback Iteration Metrics": self.feedback_metrics
        }
        
        return summary
    
    def _calculate_summary(self, metrics_list: List[Dict[str, Any]], category: str) -> Dict[str, Any]:
        """
        Calculate summary statistics for a list of metrics.
        
        Args:
            metrics_list: List of metrics dictionaries
            category: Category name for the metrics group
            
        Returns:
            Summary dictionary for the metrics group
        """
        if not metrics_list:
            return {"message": f"No {category.lower()} metrics collected"}
        
        # Calculate total latency
        total_latency = sum(m.get("Latency (s)", 0) for m in metrics_list)
        
        # Calculate total token usage if available
        total_prompt_tokens = sum(m.get("Prompt Tokens", 0) for m in metrics_list)
        total_completion_tokens = sum(m.get("Completion Tokens", 0) for m in metrics_list)
        total_tokens = sum(m.get("Total Tokens", 0) for m in metrics_list)
        
        # Create summary
        return {
            "Category": category,
            "Number of Operations": len(metrics_list),
            "Total Processing Time (s)": round(total_latency, 3),
            "Total Prompt Tokens": total_prompt_tokens,
            "Total Completion Tokens": total_completion_tokens,
            "Total Tokens": total_tokens,
            "Average Processing Time (s)": round(total_latency / max(1, len(metrics_list)), 3),
            "Average Tokens per Operation": round(total_tokens / max(1, len(metrics_list)), 1)
        }