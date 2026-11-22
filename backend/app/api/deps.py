"""
AquaMediAI — Authentication & RBAC Dependencies
================================================
FastAPI dependencies for identity resolution, session verification, and role-based access control.
Enforces the Principle of Least Privilege:
- Farmer Guests: permitted read, overview, water demand predictions, irrigation guidance.
- Agricultural Experts: permitted full pipeline, LP allocation, negotiation, diagnostics.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import Depends, Header, HTTPException, status

from app.config import get_settings
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


def _extract_token(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> Optional[str]:
    """Extract a Bearer token from the Authorization header only."""
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_authorization_header",
                "detail": "Authorization header must be 'Bearer <token>'.",
                "status_code": 401,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    return parts[1]


def get_current_identity(
    token: Optional[str] = Depends(_extract_token),
) -> Dict[str, Any]:
    """
    Validate the token and resolve caller identity and role.

    A valid token is required in every environment. There is no development or
    test authentication bypass.
    """
    settings = get_settings()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "unauthorized",
                "detail": "Authentication credentials required. Continue as Farmer (Guest) or Sign in as Expert.",
                "status_code": 401,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token, settings.jwt_secret_key)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_token",
                "detail": "Invalid or expired session. Please sign in again or re-enter as Farmer.",
                "status_code": 401,
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_farmer_or_expert(
    identity: Dict[str, Any] = Depends(get_current_identity),
) -> Dict[str, Any]:
    """Allow access to both Farmer Guests and Agricultural Experts."""
    role = identity.get("role")
    if role not in {"farmer_guest", "expert", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "detail": "Unauthorized role for this resource.",
                "status_code": 403,
            },
        )
    return identity


def require_expert(
    identity: Dict[str, Any] = Depends(get_current_identity),
) -> Dict[str, Any]:
    """
    Enforce strict Agricultural Expert / Admin access.
    Explicitly DENIES Guest Farmers with HTTP 403 Forbidden.
    """
    role = identity.get("role")
    if role == "farmer_guest":
        logger.warning(
            "Access denied: Farmer guest '%s' attempted to access expert endpoint",
            identity.get("sub"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "detail": (
                    "Access restricted to verified Agricultural Experts. "
                    "Guest farmers are not authorized to execute administrative "
                    "or multi-agent dispute mediation operations."
                ),
                "status_code": 403,
            },
        )

    if role not in {"expert", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "forbidden",
                "detail": "Agricultural Expert authentication required.",
                "status_code": 403,
            },
        )

    return identity
