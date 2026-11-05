"""
AquaMediAI — User & Authentication Models
=========================================
SQLAlchemy ORM models for user accounts, expert roles, and guest session definitions.
"""

from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserRole(str, enum.Enum):
    """System access roles enforcing principle of least privilege."""
    FARMER_GUEST = "farmer_guest"
    EXPERT = "expert"
    ADMIN = "admin"


class User(Base):
    """
    Authenticated user model for Agricultural Experts and Administrators.
    Stores password hashes using PBKDF2-HMAC-SHA256 (never plain text).
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default=UserRole.EXPERT.value, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    department: Mapped[Optional[str]] = mapped_column(
        String(255),
        default="Department of Agriculture & Water Resources",
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"


class GuestSession:
    """
    In-memory representation of an uncredentialed Farmer Guest Session.
    Provides frictionless access while enforcing strict permission boundary.
    """

    FARMER_PERMISSIONS: List[str] = [
        "farmer:read",
        "farmer:overview",
        "farmer:predict",
        "farmer:irrigation_advice",
        "farmer:weather_insights",
    ]

    def __init__(
        self,
        session_id: str,
        role: str = UserRole.FARMER_GUEST.value,
        created_at: Optional[datetime] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        self.session_id = session_id
        self.role = role
        self.created_at = created_at or datetime.now(timezone.utc)
        self.expires_at = expires_at
        self.permissions = list(self.FARMER_PERMISSIONS)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "role": self.role,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }
