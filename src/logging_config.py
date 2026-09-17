import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

# Global logger configuration
_initialized = False


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    to_console: bool = True,
    to_file: bool = True
) -> None:
    """
    Configure and initialize application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (default: logs/app.log)
        max_bytes: Maximum log file size before rotation (default: 10MB)
        backup_count: Number of backup log files to keep
        to_console: Whether to output to console
        to_file: Whether to write to log file
    """
    global _initialized

    # Set default log level from environment or default to INFO
    if level is None:
        level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    else:
        level = level.upper()

    numeric_level = getattr(logging, level, logging.INFO)

    # Create logs directory if it doesn't exist
    log_directory = Path('logs')
    log_directory.mkdir(exist_ok=True)

    # Determine log file path
    if log_file is None:
        log_file = 'logs/app.log'

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter with timestamp and structured format
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if to_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)  # Always log debug in file
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Set module-level loggers to NOT propagate to root
    for module_name in ['google.gmail', 'google.spreadsheet', 'strava.browser_automation', 'download_account']:
        module_logger = logging.getLogger(module_name)
        module_logger.setLevel(numeric_level)
        module_logger.propagate = False

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Get module-specific logger.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    if not _initialized:
        setup_logging()

    return logging.getLogger(name)


def log_execution(func):
    """
    Decorator for logging function execution.

    Usage:
        @log_execution
        def my_function():
            pass
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.info(f"Executing {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Failed {func.__name__}: {e}")
            raise
    return wrapper


# Convenience functions for common logging patterns
def log_info(message: str, extra: Optional[dict] = None):
    """Log info message with optional structured data."""
    logger = get_logger(__name__)
    if extra:
        logger.info(message, extra=extra)
    else:
        logger.info(message)


def log_error(message: str, error: Optional[Exception] = None):
    """Log error message with optional exception."""
    logger = get_logger(__name__)
    if error:
        logger.error(message, exc_info=error)
    else:
        logger.error(message)


def log_debug(message: str):
    """Log debug message."""
    logger = get_logger(__name__)
    logger.debug(message)


def log_warning(message: str):
    """Log warning message."""
    logger = get_logger(__name__)
    logger.warning(message)
