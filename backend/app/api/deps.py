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

from fastapi import Depends, Header, HTTPException, Request, status

from app.config import get_settings
from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


def _extract_token(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_auth_token: Optional[str] = Header(None, alias="X-Auth-Token"),
    x_guest_session: Optional[str] = Header(None, alias="X-Guest-Session"),
) -> Optional[str]:
    """Extract bearer or session token from HTTP headers."""
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return authorization
    if x_auth_token:
        return x_auth_token
    if x_guest_session:
        return x_guest_session
    return None


def get_current_identity(
    request: Request,
    token: Optional[str] = Depends(_extract_token),
) -> Dict[str, Any]:
    """
    Validate the token and resolve caller identity and role.
    If in production or token provided: strictly validates.
    """
    settings = get_settings()

    if not token:
        # In production mode, require token strictly
        if settings.app_env == "production":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "unauthorized",
                    "detail": "Authentication credentials required. Continue as Farmer (Guest) or Sign in as Expert.",
                    "status_code": 401,
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Development / test fallback when no token provided:
        return {
            "sub": "dev_expert_default",
            "role": "expert",
            "email": settings.expert_default_email,
            "full_name": settings.expert_default_name,
            "department": "Department of Agriculture",
            "permissions": ["farmer:*", "expert:*", "admin:*"],
            "is_default_dev": True,
        }

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
