"""Centralized logging configuration for Open Mental Health Collective.

This module provides consistent logging configuration across the application,
supporting environment-based log level control and structured formatting
suitable for production deployments.

Usage:
    from logging_config import configure_logging
    
    logger = configure_logging("omhc.mymodule")
    logger.info("Processing started")
    logger.debug("Detailed debug information")
    logger.error("An error occurred")

Environment Variables:
    OMHC_LOG_LEVEL: Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                    Default: INFO
"""

import logging
import os
import sys


def configure_logging(name: str = "omhc", level: str = None) -> logging.Logger:
    """
    Configure and return a logger with consistent formatting.
    
    Args:
        name: Logger name (default: "omhc"). Use hierarchical names like
              "omhc.eval" or "omhc.orchestrator" for better filtering.
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, reads from OMHC_LOG_LEVEL env var (default: INFO).
    
    Returns:
        Configured logger instance
        
    Example:
        >>> logger = configure_logging("omhc.eval", "DEBUG")
        >>> logger.info("Evaluation started")
        2025-11-27 08:23:45 - omhc.eval - INFO - Evaluation started
    """
    if level is None:
        level = os.getenv("OMHC_LOG_LEVEL", "INFO").upper()
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Avoid duplicate handlers if logger already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger
