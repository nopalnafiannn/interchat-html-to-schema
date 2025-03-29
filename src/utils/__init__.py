"""
Utils package
-----------
Contains utility modules for file operations and logging.
"""

# Import key functions to make them available at the package level
from src.utils.file_utils import (
    read_file,
    save_file,
    save_json,
    load_json,
    get_file_extension,
    list_files
)

from src.utils.logging_utils import setup_logger, get_logger