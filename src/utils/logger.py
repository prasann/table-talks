"""
Centralized logging configuration for TableTalk.
"""
import logging
import os
from datetime import datetime

def setup_logger(name="tabletalk", level=logging.INFO):
    """
    Set up centralized logger for TableTalk.
    
    Args:
        name: Logger name
        level: Logging level (default: INFO for clean console)
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Create logs directory if needed
    os.makedirs("logs", exist_ok=True)
    
    # File handler for debug logs
    timestamp = datetime.now().strftime("%Y%m%d")
    debug_file = f"logs/tabletalk_debug_{timestamp}.log"
    file_handler = logging.FileHandler(debug_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler for user-facing messages only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Only warnings/errors to console
    
    # Formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    file_handler.setFormatter(detailed_formatter)
    console_handler.setFormatter(simple_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    # Suppress verbose LangChain logging
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("langchain.agents").setLevel(logging.WARNING)
    logging.getLogger("langchain.chains").setLevel(logging.WARNING)
    logging.getLogger("langchain.callbacks").setLevel(logging.WARNING)
    
    return logger

def get_logger(name="tabletalk"):
    """Get existing logger or create new one."""
    return logging.getLogger(name)
