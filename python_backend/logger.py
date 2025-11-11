"""
Structured Logging Configuration
Uses loguru for structured, contextual logging with proper formatting and rotation.
"""
import sys
import os
from pathlib import Path
from loguru import logger
from typing import Optional
import json

# Remove default logger
logger.remove()

# Get configuration from environment
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.getenv("LOG_FORMAT", "json").lower()
NODE_ENV = os.getenv("NODE_ENV", "development")

# Determine if we're in production
IS_PRODUCTION = NODE_ENV == "production"

def json_formatter(record):
    """Format log records as JSON - simplified version"""
    import json
    
    subset = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "function": record["function"],
        "line": record["line"],
    }
    
    # Add exception if present
    if record["exception"]:
        subset["exception"] = str(record["exception"])
    
    return json.dumps(subset) + "\n"


def text_formatter(record):
    """Format log records as readable text (for development)"""
    # Simple format for development
    format_str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Add context if present
    if "extra" in record and record["extra"]:
        context_parts = []
        for key, value in record["extra"].items():
            if not key.startswith("_"):
                context_parts.append(f"{key}={value}")
        if context_parts:
            context_str = ", ".join(context_parts)
            format_str += f" | {context_str}"
    
    return format_str + "\n"


# Configure stdout logger
if IS_PRODUCTION or LOG_FORMAT == "json":
    # Production: Simple JSON format
    logger.add(
        sys.stdout,
        format="{message}",
        level=LOG_LEVEL,
        serialize=True,  # Use loguru's built-in JSON serialization
        enqueue=True,
        backtrace=True,
        diagnose=False,
    )
else:
    # Development: Simple readable format
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=LOG_LEVEL,
        colorize=True,
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

# Add file logging with rotation (if enabled)
if os.getenv("LOG_TO_FILE", "true").lower() == "true":
    log_dir = Path(__file__).parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format="{time} | {level} | {name}:{function}:{line} - {message}",
        level=LOG_LEVEL,
        rotation="00:00",
        retention="7 days",
        compression="gz",
        enqueue=True,
    )

# Add error-only log file
if IS_PRODUCTION:
    log_dir = Path(__file__).parent.parent / "logs"
    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        format="{time} | {level} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="gz",
        enqueue=True,
    )


def sanitize_log_data(data: dict) -> dict:
    """
    Sanitize sensitive data from logs (passwords, tokens, etc).
    """
    sensitive_keys = {
        "password", "passwd", "pwd",
        "token", "api_key", "apikey", "secret",
        "authorization", "auth",
        "credit_card", "card_number", "cvv",
    }
    
    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "***REDACTED***"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        else:
            sanitized[key] = value
    
    return sanitized


def log_with_context(level: str, message: str, **context):
    """
    Log a message with additional context fields.
    Context will be sanitized to remove sensitive data.
    """
    sanitized_context = sanitize_log_data(context) if context else {}
    
    log_func = getattr(logger.bind(**sanitized_context), level.lower())
    log_func(message)


# Export configured logger
__all__ = ["logger", "log_with_context", "sanitize_log_data"]


# Log startup
logger.info(
    "Logger initialized",
    environment=NODE_ENV,
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    production=IS_PRODUCTION,
)

