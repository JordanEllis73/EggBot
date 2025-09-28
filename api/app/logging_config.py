"""
Logging configuration for EggBot API
This module configures logging early in the application startup
"""

import os
import logging

def configure_logging():
    """Configure logging based on environment variables"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Configure the root logger
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True  # Override any existing configuration
    )

    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")

    return logger

# Configure logging immediately when this module is imported
configure_logging()