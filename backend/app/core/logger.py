"""
Logging configuration for the application.
"""

import logging
import sys
from app.core.config import settings

def setup_logger() -> logging.Logger:
    """
    Set up application logger with console and file handlers.
    """
    logger = logging.getLogger(settings.PROJECT_NAME)
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (optional, for production)
    # file_handler = logging.FileHandler("app.log")
    # file_handler.setLevel(logging.INFO)
    # file_formatter = logging.Formatter(
    #     "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    # )
    # file_handler.setFormatter(file_formatter)
    # logger.addHandler(file_handler)

    return logger

logger = setup_logger()
