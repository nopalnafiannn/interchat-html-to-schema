"""
Logging Utilities Module
----------------------
Functions for setting up and managing logging
"""

import os
import logging
import sys
from pathlib import Path
from datetime import datetime

# Dictionary to store configured loggers
_loggers = {}

def setup_logger(name='html_analyzer', log_level=logging.INFO, log_to_file=True):
    """
    Set up a logger with console and file handlers
    
    Args:
        name (str): Logger name
        log_level (int): Logging level
        log_to_file (bool): Whether to log to a file
        
    Returns:
        logging.Logger: Configured logger
    """
    # Check if logger already exists
    if name in _loggers:
        return _loggers[name]
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Create file handler if requested
    if log_to_file:
        # Create logs directory if it doesn't exist
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = logs_dir / f"{name}_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Add file handler to logger
        logger.addHandler(file_handler)
    
    # Store logger
    _loggers[name] = logger
    
    return logger

def get_logger(name='html_analyzer'):
    """
    Get an existing logger or create a new one
    
    Args:
        name (str): Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    return setup_logger(name)