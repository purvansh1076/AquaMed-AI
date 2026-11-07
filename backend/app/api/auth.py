"""
AquaMediAI — Authentication & Role-Based Access Endpoints
=========================================================
Implements:
1. Frictionless Farmer Guest Session generation (no password required).
2. Agricultural Expert Authentication (PBKDF2-HMAC-SHA256, rate limiting, lockout).
3. Session verification and identity status.
"""

from __future__ import annotations

import hmac
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import get_current_identity
from app.config import get_settings
from app.core.security import (
    create_access_token,
    hash_password,
    login_rate_limiter,
    verify_password,
)
from app.database import check_db_connection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication & Access"])


# ─── Schemas ──────────────────────────────────────────────────────────────────

class GuestSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "farmer_guest"
    session_id: str
    display_name: str = "Farmer Guest"
    permissions: List[str]
    expires_in_seconds: int


class ExpertLoginRequest(BaseModel):
    username_or_email: str = Field(..., description="Email address or username")
    password: str = Field(..., min_length=6, description="Expert account password")


class UserProfile(BaseModel):
    email: str
    full_name: str
    role: str
    department: str


class ExpertLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str = "expert"
    user: UserProfile
    expires_in_seconds: int
    message: str = "Authentication successful"


class IdentityResponse(BaseModel):
    sub: str
    role: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    permissions: List[str]
    is_authenticated: bool


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post(
    "/guest-session",
    response_model=GuestSessionResponse,
    summary="Create uncredentialed Farmer Guest Session",
    description="Allows farmers immediate, frictionless access to crop water demand and farm insights without credentials.",
)
def create_farmer_guest_session(request: Request) -> Dict[str, Any]:
    """Establish a restricted guest session for farmers."""
    settings = get_settings()
    session_id = f"guest_{uuid.uuid4().hex[:12]}"
    expire_hours = settings.guest_session_expire_hours
    expires_delta = timedelta(hours=expire_hours)

    permissions = [
        "farmer:read",
        "farmer:overview",
        "farmer:predict",
        "farmer:irrigation_advice",
        "farmer:weather_insights",
    ]

    token_payload = {
        "sub": session_id,
        "role": "farmer_guest",
        "display_name": "Farmer Guest",
        "permissions": permissions,
    }

    token = create_access_token(
        data=token_payload,
        secret_key=settings.jwt_secret_key,
        expires_delta=expires_delta,
    )

    logger.info("Farmer guest session created: %s", session_id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "farmer_guest",
        "session_id": session_id,
        "display_name": "Farmer Guest",
        "permissions": permissions,
        "expires_in_seconds": int(expires_delta.total_seconds()),
    }


@router.post(
    "/expert/login",
    response_model=ExpertLoginResponse,
    summary="Authenticate Agricultural Expert",
    description="Validates expert credentials with rate-limiting and account lockout protection.",
)
def expert_login(
    payload: ExpertLoginRequest,
    request: Request,
) -> Dict[str, Any]:
    """Secure login for agricultural extension officers and system experts."""
    settings = get_settings()
    identifier = payload.username_or_email.strip().lower()

    # 1. Rate limiter check
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"{client_ip}:{identifier}"
    is_locked, remaining_secs = login_rate_limiter.is_locked_out(rate_limit_key)

    if is_locked:
        logger.warning("Blocked login attempt from locked-out client: %s", rate_limit_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "too_many_attempts",
                "detail": (
                    f"Too many failed login attempts. For security reasons, "
                    f"account access is locked for {remaining_secs} seconds."
                ),
                "status_code": 429,
                "retry_after_seconds": remaining_secs,
            },
        )

    # 2. Check credentials
    # Supports both provisioned expert credentials and configured default
    is_valid = False
    full_name = settings.expert_default_name
    department = "Department of Agriculture & Water Resources"
    target_email = settings.expert_default_email.lower()

    if identifier in {target_email, "expert", "admin", "expert@aquamedi.gov.in", "admin123"}:
        # Compare with configured expert password or prototype admin123 credentials (if dev credentials enabled)
        expected_pwd = settings.expert_default_password
        if identifier == "admin123" and payload.password == "12345678":
            if getattr(settings, "enable_dev_demo_credentials", False):
                is_valid = True
                target_email = "admin123@aquamedi.gov.in"
                full_name = "Senior Agricultural Specialist (Admin)"
                department = "Agricultural Intelligence"
            else:
                logger.warning("Prototype credentials rejected: enable_dev_demo_credentials is False")
        elif hmac.compare_digest(payload.password, expected_pwd):
            is_valid = True

    # 3. Check database if connected
    if not is_valid and check_db_connection():
        try:
            from app.database import SessionLocal
            from app.models.user import User
            from sqlalchemy import or_

            with SessionLocal() as db:
                user = db.query(User).filter(
                    or_(User.email == identifier, User.username == identifier)
                ).first()
                if user and user.is_active:
                    if verify_password(payload.password, user.hashed_password):
                        is_valid = True
                        target_email = user.email
                        full_name = user.full_name
                        department = user.department or department
        except Exception as exc:
            logger.warning("Database user lookup error: %s", exc)

    # 4. Handle authentication failure
    if not is_valid:
        is_locked_now, attempts_left_or_lockout = login_rate_limiter.record_failure(rate_limit_key)
        if is_locked_now:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "too_many_attempts",
                    "detail": (
                        f"Invalid credentials. Maximum attempts exceeded. "
                        f"Locked for {attempts_left_or_lockout} seconds."
                    ),
                    "status_code": 429,
                    "retry_after_seconds": attempts_left_or_lockout,
                },
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_credentials",
                "detail": f"Invalid username/email or password. {attempts_left_or_lockout} attempt(s) remaining.",
                "status_code": 401,
            },
        )

    # 5. Handle authentication success
    login_rate_limiter.record_success(rate_limit_key)
    expires_delta = timedelta(hours=settings.jwt_expire_hours)

    expert_permissions = [
        "farmer:*",
        "expert:*",
        "mediation:run",
        "ml:diagnostics",
        "lp:allocate",
        "reports:export",
    ]

    token_payload = {
        "sub": target_email,
        "email": target_email,
        "role": "expert",
        "full_name": full_name,
        "department": department,
        "permissions": expert_permissions,
    }

    token = create_access_token(
        data=token_payload,
        secret_key=settings.jwt_secret_key,
        expires_delta=expires_delta,
    )

    logger.info("Agricultural Expert authenticated successfully: %s", target_email)

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": "expert",
        "user": {
            "email": target_email,
            "full_name": full_name,
            "role": "expert",
            "department": department,
        },
        "expires_in_seconds": int(expires_delta.total_seconds()),
        "message": "Welcome, Agricultural Extension Specialist",
    }


@router.get(
    "/me",
    response_model=IdentityResponse,
    summary="Get current session identity and permissions",
)
def get_current_user_profile(
    identity: Dict[str, Any] = Depends(get_current_identity),
) -> Dict[str, Any]:
    """Return the profile, role, and permission grants of the active token."""
    role = identity.get("role", "unknown")
    return {
        "sub": identity.get("sub", ""),
        "role": role,
        "email": identity.get("email"),
        "full_name": identity.get("full_name") or ("Farmer Guest" if role == "farmer_guest" else "Expert User"),
        "department": identity.get("department") or ("Agricultural Community" if role == "farmer_guest" else "Department of Agriculture"),
        "permissions": identity.get("permissions", []),
        "is_authenticated": role in {"expert", "admin"},
    }


@router.post(
    "/logout",
    summary="Log out active session",
)
def logout_user(
    identity: Dict[str, Any] = Depends(get_current_identity),
) -> Dict[str, str]:
    """Client clears token. Server confirms termination."""
    logger.info("Session terminated for: %s", identity.get("sub"))
    return {"status": "success", "message": "Logged out successfully."}

