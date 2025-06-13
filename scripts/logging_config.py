import logging
import os
from datetime import datetime

def setup_logger(module_name):
    """
    Set up a logger for a specific module with file and console handlers.
    File handler logs at DEBUG level, console handler logs at INFO level.
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Get or create logger
    logger = logging.getLogger(module_name)
    
    # If logger already has handlers, return it
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.DEBUG)  # Set to lowest level to capture all logs

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )

    # File handler - DEBUG level
    log_file = f'logs/{module_name}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(file_formatter)

    # Console handler - INFO level only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Only show INFO and above in console
    console_handler.setFormatter(console_formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger 