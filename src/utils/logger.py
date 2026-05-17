"""
Logging configuration and structured JSON logging.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Optional
from pythonjsonlogger import jsonlogger

from src.config import get_settings


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Configure structured logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format ("json" or "text")
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if log_format.lower() == "json":
        formatter = jsonlogger.JsonFormatter(
            "%(timestamp)s %(level)s %(name)s %(message)s",
            timestamp=True,
            datefmt="%Y-%m-%dT%H:%M:%SZ"
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(getattr(logging, log_level.upper()))
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (IOError, OSError) as e:
            logger.warning(f"Failed to create log file {log_file}: {e}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get logger with given name"""
    return logging.getLogger(name)


# Initialize logger based on settings
def init_logger() -> logging.Logger:
    """Initialize logger from settings"""
    settings = get_settings()
    return setup_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        log_file=settings.LOG_FILE
    )
