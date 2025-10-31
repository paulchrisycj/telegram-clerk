"""
Logging configuration for the Telegram bot.
Sets up structured console logging without PII.
"""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the application.

    Args:
        level: The logging level to use (default: INFO)
    """
    # Create a formatter that includes timestamp, level, logger name, and message
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific log levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("telegram.ext").setLevel(logging.INFO)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: The name of the logger (typically __name__)

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
