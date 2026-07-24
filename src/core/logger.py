"""Logging configuration for Profynex AI."""

import sys
from pathlib import Path
from loguru import logger
from .config import get_config


def setup_logging():
    """Configure logging system."""
    config = get_config()
    logger.remove()
    logger.add(
        sys.stdout,
        format="<level>{time:YYYY-MM-DD HH:mm:ss}</level> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=config.LOG_LEVEL,
        colorize=True,
    )
    log_file = config.LOGS_DIR / "profynex.log"
    logger.add(
        str(log_file),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="500 MB",
        retention="7 days",
    )
    error_log = config.LOGS_DIR / "profynex_error.log"
    logger.add(
        str(error_log),
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="500 MB",
        retention="30 days",
    )


def get_logger(name: str):
    """Get logger instance for a module."""
    return logger.bind(name=name)


setup_logging()
