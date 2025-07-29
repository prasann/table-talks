"""Simple logging for TableTalk."""
import logging
import os

def setup_logger(name="tabletalk", level=logging.INFO):
    """Set up simple logger."""
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    # Create logs directory
    os.makedirs("logs", exist_ok=True)
    
    # File logging only
    handler = logging.FileHandler(f"logs/tabletalk.log")
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(message)s'))
    
    logger.addHandler(handler)
    logger.setLevel(level)
    
    # Suppress noisy libraries
    logging.getLogger("langchain").setLevel(logging.ERROR)
    
    return logger

def get_logger(name="tabletalk"):
    """Get logger."""
    return logging.getLogger(name)
