# flake8: noqa: D401
"""Audit logging module for security and compliance."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request

logger = logging.getLogger(__name__)


class AuditLogger:
    """Audit logger for security and compliance tracking."""

    def __init__(self):
        """Initialize audit logger."""
        self.audit_logger = logging.getLogger("audit")

    def log_api_access(
        self,
        request: Request,
        user: Optional[str] = None,
        status_code: int = 200,
        duration: float = 0.0,
    ):
        """
        Log API access for audit purposes.

        Args:
            request: FastAPI request object
            user: Authenticated user (if any)
            status_code: HTTP status code
            duration: Request duration in seconds
        """
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "api_access",
            "method": request.method,
            "path": str(request.url.path),
            "query_params": dict(request.query_params),
            "client_ip": request.client.host,
            "user_agent": request.headers.get("user-agent", ""),
            "user": user or "anonymous",
            "status_code": status_code,
            "duration_ms": round(duration * 1000, 2),
            "headers": dict(request.headers),
        }

        self.audit_logger.info("API Access", extra={"audit_data": audit_entry})

    def log_authentication_event(
        self,
        event_type: str,
        user: Optional[str] = None,
        client_ip: str = "",
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log authentication events.

        Args:
            event_type: Type of auth event (login, logout, failed_login, etc.)
            user: User identifier
            client_ip: Client IP address
            success: Whether the authentication was successful
            details: Additional details about the event
        """
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": f"auth_{event_type}",
            "user": user or "unknown",
            "client_ip": client_ip,
            "success": success,
            "details": details or {},
        }

        self.audit_logger.info(
            "Authentication Event", extra={"audit_data": audit_entry}
        )

    def log_data_access(
        self,
        user: str,
        operation: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log data access events.

        Args:
            user: User performing the operation
            operation: Type of operation (read, write, delete, etc.)
            resource_type: Type of resource being accessed
            resource_id: ID of the specific resource
            details: Additional details about the operation
        """
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "data_access",
            "user": user,
            "operation": operation,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
        }

        self.audit_logger.info("Data Access", extra={"audit_data": audit_entry})

    def log_security_event(
        self,
        event_type: str,
        severity: str = "medium",
        user: Optional[str] = None,
        client_ip: str = "",
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Log security events.

        Args:
            event_type: Type of security event
            severity: Event severity (low, medium, high, critical)
            user: User involved (if any)
            client_ip: Client IP address
            details: Additional details about the event
        """
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": f"security_{event_type}",
            "severity": severity,
            "user": user or "unknown",
            "client_ip": client_ip,
            "details": details or {},
        }

        if severity in ["high", "critical"]:
            self.audit_logger.warning(
                "Security Event", extra={"audit_data": audit_entry}
            )
        else:
            self.audit_logger.info("Security Event", extra={"audit_data": audit_entry})

    def log_rate_limit_event(
        self,
        client_ip: str,
        user: Optional[str] = None,
        endpoint: str = "",
        limit_exceeded: bool = False,
    ):
        """
        Log rate limiting events.

        Args:
            client_ip: Client IP address
            user: User identifier (if authenticated)
            endpoint: API endpoint being accessed
            limit_exceeded: Whether rate limit was exceeded
        """
        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "rate_limit",
            "client_ip": client_ip,
            "user": user or "anonymous",
            "endpoint": endpoint,
            "limit_exceeded": limit_exceeded,
        }

        if limit_exceeded:
            self.audit_logger.warning(
                "Rate Limit Exceeded", extra={"audit_data": audit_entry}
            )
        else:
            self.audit_logger.info(
                "Rate Limit Check", extra={"audit_data": audit_entry}
            )


# Global audit logger instance
audit_logger = AuditLogger()


def setup_audit_logging():
    """Setup audit logging configuration."""
    # Create audit logger
    audit_log = logging.getLogger("audit")
    audit_log.setLevel(logging.INFO)

    # Create file handler for audit logs
    audit_handler = logging.FileHandler("audit.log")
    audit_handler.setLevel(logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    audit_handler.setFormatter(formatter)

    # Add handler to logger
    audit_log.addHandler(audit_handler)

    # Prevent propagation to avoid duplicate logs
    audit_log.propagate = False

    logger.info("Audit logging configured")


# Convenience functions for common audit events
def log_api_request(
    request: Request,
    user: Optional[str] = None,
    status_code: int = 200,
    duration: float = 0.0,
):
    """Log an API request for audit."""  # noqa: D401
    audit_logger.log_api_access(request, user, status_code, duration)


def log_auth_success(user: str, client_ip: str):
    """Log successful authentication."""
    audit_logger.log_authentication_event("success", user, client_ip, success=True)


def log_auth_failure(user: Optional[str], client_ip: str, reason: str):
    """Log failed authentication."""
    audit_logger.log_authentication_event(
        "failure", user, client_ip, success=False, details={"reason": reason}
    )


def log_data_read(user: str, resource_type: str, resource_id: Optional[str] = None):
    """Log data read operation."""
    audit_logger.log_data_access(user, "read", resource_type, resource_id)


def log_data_write(
    user: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """Log data write operation."""
    audit_logger.log_data_access(user, "write", resource_type, resource_id, details)


def log_data_delete(user: str, resource_type: str, resource_id: Optional[str] = None):
    """Log data delete operation."""
    audit_logger.log_data_access(user, "delete", resource_type, resource_id)


def log_security_violation(
    event_type: str,
    user: Optional[str],
    client_ip: str,
    details: Optional[Dict[str, Any]] = None,
):
    """Log security violation."""
    audit_logger.log_security_event(event_type, "high", user, client_ip, details)


def log_rate_limit_exceeded(client_ip: str, user: Optional[str], endpoint: str):
    """Log rate limit exceeded."""
    audit_logger.log_rate_limit_event(client_ip, user, endpoint, limit_exceeded=True)
