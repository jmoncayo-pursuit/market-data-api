"""Authentication and authorization module."""

import logging
from typing import Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

logger = logging.getLogger(__name__)

# Security scheme for API key authentication
security = HTTPBearer(auto_error=False)

# In production, this would be stored in a secure database or environment variable
# For demo purposes, we'll use a simple API key
VALID_API_KEYS = {
    "demo-api-key-123": "demo-user",
    "admin-api-key-456": "admin-user",
    "readonly-api-key-789": "readonly-user",
}

# API key permissions
API_KEY_PERMISSIONS = {
    "demo-api-key-123": ["read", "write"],
    "admin-api-key-456": ["read", "write", "delete", "admin"],
    "readonly-api-key-789": ["read"],
}


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> Optional[str]:
    """
    Validate API key and return user identifier.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User identifier if valid, None if no credentials provided

    Raises:
        HTTPException: If API key is invalid
    """
    if not credentials:
        return None

    api_key = credentials.credentials

    if api_key not in VALID_API_KEYS:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = VALID_API_KEYS[api_key]
    logger.info(f"Authenticated user: {user}")
    return user


async def require_auth(current_user: Optional[str] = Depends(get_current_user)) -> str:
    """
    Require authentication for protected endpoints.

    Args:
        current_user: Current authenticated user

    Returns:
        User identifier

    Raises:
        HTTPException: If no valid authentication provided
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_permission(
    permission: str, current_user: Optional[str] = Depends(get_current_user)
) -> str:
    """
    Require specific permission for protected endpoints.

    Args:
        permission: Required permission (read, write, delete, admin)
        current_user: Current authenticated user

    Returns:
        User identifier

    Raises:
        HTTPException: If no valid authentication or insufficient permissions
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Find the API key for the current user
    api_key = None
    for key, user in VALID_API_KEYS.items():
        if user == current_user:
            api_key = key
            break

    if not api_key or permission not in API_KEY_PERMISSIONS.get(api_key, []):
        logger.warning(
            f"User {current_user} attempted to access {permission} without permission"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions. Required: {permission}",
        )

    return current_user


# Convenience functions for common permission checks
async def require_read_permission(
    current_user: Optional[str] = Depends(get_current_user),
) -> str:
    """Require read permission."""
    return await require_permission("read", current_user)


async def require_write_permission(
    current_user: Optional[str] = Depends(get_current_user),
) -> str:
    """Require write permission."""
    return await require_permission("write", current_user)


async def require_admin_permission(
    current_user: Optional[str] = Depends(get_current_user),
) -> str:
    """Require admin permission."""
    return await require_permission("admin", current_user)
