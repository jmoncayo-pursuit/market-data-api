"""Logging utilities for the Market Data Service."""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if they exist
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add exception info if it exists
        if record.exc_info:
            exc_type = record.exc_info[0]
            log_data["exception"] = {
                "type": exc_type.__name__ if exc_type else None,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_data)


def setup_logging():
    """Configure logging for the application."""
    # Create logger
    logger = logging.getLogger("market_data_service")
    logger.setLevel(logging.INFO)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create file handler
    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.INFO)

    # Set formatter
    formatter = JSONFormatter()
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# Create a logger instance
logger = setup_logging()


def log_request(
    request_id: str, method: str, path: str, status_code: int, duration: float
):
    """Log HTTP request details."""
    logger.info(
        "HTTP Request",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration,
        },
    )


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log error details."""
    logger.error(str(error), exc_info=True, extra={"context": context or {}})


def log_market_data(symbol: str, price: float, provider: str):
    """Log market data updates."""
    logger.info(
        "Market Data Update",
        extra={"symbol": symbol, "price": price, "provider": provider},
    )


def log_job_status(job_id: str, status: str, config: Dict[str, Any]):
    """Log polling job status updates."""
    logger.info(
        "Job Status Update",
        extra={"job_id": job_id, "status": status, "config": config},
    )
