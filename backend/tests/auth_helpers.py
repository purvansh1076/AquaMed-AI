"""Test-only helpers for minting short-lived API credentials.

These helpers use the application's own token function and configured secret.
They do not add any authentication bypass to the application.
"""

from __future__ import annotations

from typing import Dict

from app.config import get_settings
from app.core.security import create_access_token


def expert_headers() -> Dict[str, str]:
    """Return a valid expert Bearer header for integration tests."""
    settings = get_settings()
    token = create_access_token(
        {
            "sub": "pytest_expert@example.test",
            "email": "pytest_expert@example.test",
            "role": "expert",
            "full_name": "Pytest Expert",
            "permissions": ["farmer:*", "expert:*"],
        },
        secret_key=settings.jwt_secret_key,
    )
    return {"Authorization": f"Bearer {token}"}


def guest_headers() -> Dict[str, str]:
    """Return a valid farmer-guest Bearer header for integration tests."""
    settings = get_settings()
    token = create_access_token(
        {
            "sub": "pytest_guest",
            "role": "farmer_guest",
            "full_name": "Pytest Farmer Guest",
            "permissions": ["farmer:read", "farmer:predict"],
        },
        secret_key=settings.jwt_secret_key,
    )
    return {"Authorization": f"Bearer {token}"}
