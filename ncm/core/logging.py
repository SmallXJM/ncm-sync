"""Logging configuration for NCM API."""

import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.DEBUG,
    format_string: Optional[str] = None,
    logger_name: str = "ncm"
) -> logging.Logger:
    """
    Setup logging configuration for NCM API.
    
    Args:
        level: Logging level (default: INFO)
        format_string: Custom format string
        logger_name: Logger name
        
    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "[%(asctime)s] %(name)s.%(levelname)s: %(message)s"
    
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str = "ncm") -> logging.Logger:
    """Get logger instance."""
    return logging.getLogger(name)


# Default logger instance
logger = setup_logging()