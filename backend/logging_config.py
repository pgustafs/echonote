"""
Enhanced Logging Configuration for EchoNote

Provides structured JSON logging with file rotation and separate audit trail.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from datetime import datetime


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields"""

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        if not log_record.get('timestamp'):
            log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'

        # Add log level
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name


def setup_logging(log_dir: str = "logs", log_level: str = "INFO"):
    """
    Initialize logging configuration with structured JSON logging

    Args:
        log_dir: Directory for log files (default: "logs")
        log_level: Logging level (default: "INFO")
    """
    # Create logs directory if it doesn't exist
    os.makedirs(log_dir, exist_ok=True)

    # Define log format
    log_format = '%(timestamp)s %(level)s %(logger)s %(message)s'

    # Create JSON formatter
    json_formatter = CustomJsonFormatter(log_format)

    # Create console formatter (non-JSON for readability in development)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console Handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # Application Log Handler (rotating file, JSON)
    app_log_file = os.path.join(log_dir, 'app.log')
    app_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(json_formatter)
    root_logger.addHandler(app_handler)

    # Error Log Handler (rotating file, JSON)
    error_log_file = os.path.join(log_dir, 'error.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    root_logger.addHandler(error_handler)

    # Create security logger (separate logger for audit trail)
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.WARNING)
    security_logger.propagate = False  # Don't propagate to root logger

    security_log_file = os.path.join(log_dir, 'security.log')
    security_handler = RotatingFileHandler(
        security_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(json_formatter)
    security_logger.addHandler(security_handler)

    # Also add console handler to security logger for visibility
    security_console_handler = logging.StreamHandler()
    security_console_handler.setLevel(logging.WARNING)
    security_console_handler.setFormatter(console_formatter)
    security_logger.addHandler(security_console_handler)

    logging.info(f"Logging configuration initialized. Log directory: {log_dir}")
    logging.info(f"Log level: {log_level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance

    Args:
        name: Logger name (typically __name__ from calling module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def get_security_logger() -> logging.Logger:
    """
    Get the dedicated security/audit logger

    Returns:
        Security logger instance
    """
    return logging.getLogger('security')


def log_structured(logger: logging.Logger, level: str, message: str, **kwargs):
    """
    Helper function for structured logging with additional context

    Args:
        logger: Logger instance
        level: Log level (INFO, WARNING, ERROR, etc.)
        message: Log message
        **kwargs: Additional fields to include in structured log

    Example:
        log_structured(logger, 'INFO', 'User action',
                      user_id=123, action='login', ip='192.168.1.1')
    """
    log_method = getattr(logger, level.lower())
    log_method(message, extra=kwargs)
