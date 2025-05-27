"""
Centralized logging configuration for the Buchloe event scraper.

This module provides a custom formatter that includes extra fields
in the console output, making debugging and monitoring more effective.
"""

import logging
import sys


class ExtraFieldsFormatter(logging.Formatter):
    """
    Custom formatter that includes extra fields in log output.

    This formatter will append any extra fields passed to logger calls
    to the end of the log message in a structured format.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Get the base formatted message
        base_message = super().format(record)

        # Extract extra fields (anything not in the standard LogRecord attributes)
        standard_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
            "exc_info",
            "exc_text",
            "stack_info",
            "message",
        }

        extra_fields = {
            key: value
            for key, value in record.__dict__.items()
            if key not in standard_attrs and not key.startswith("_")
        }

        # If there are extra fields, append them to the message
        if extra_fields:
            extra_str = " | ".join(
                f"{key}={value}" for key, value in extra_fields.items()
            )
            return f"{base_message} | {extra_str}"

        return base_message


# Global flag to track if logging has been configured
_logging_configured = False


def setup_logging(level: int = logging.INFO) -> None:
    """
    Set up centralized logging configuration for the application.

    This function is idempotent - it can be called multiple times safely.

    Args:
        level: The logging level to use (default: INFO)
    """
    global _logging_configured

    # Only configure logging once
    if _logging_configured:
        return

    # Create a custom formatter that includes extra fields
    formatter = ExtraFieldsFormatter(
        fmt="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add our custom handler
    root_logger.addHandler(console_handler)

    # Mark as configured
    _logging_configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: The name for the logger (typically __name__)

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)
