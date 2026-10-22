"""
AquaMediAI — Farmer ORM Model
==============================
Represents a farmer and their farm characteristics in the database.

NOTE: All farmer records in the MVP are synthetically generated.
No real-world farmer data is stored.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.allocation import AllocationRecord
    from app.models.agreement import Agreement


class Farmer(Base):
    """
    SQLAlchemy ORM model for a farmer / farm entity.

    Attributes
    ----------
    id : int
        Primary key.
    name : str
        Farmer's display name (synthetic).
    farm_id : str
        Unique farm identifier code.
    farm_area_hectares : float
        Total cultivated area in hectares.
    crop_type : str
        Primary crop being cultivated (e.g., 'wheat', 'rice', 'cotton').
    soil_type : str
        Soil classification (e.g., 'clay', 'loam', 'sandy').
    growth_stage : str
        Current growth stage (e.g., 'germination', 'vegetative', 'flowering',
        'maturity', 'harvest').
    location_village : str
        Village or locality name (synthetic).
    canal_id : str
        Canal the farm draws water from.
    preferred_irrigation_start : int
        Preferred irrigation window start hour (0–23).
    preferred_irrigation_end : int
        Preferred irrigation window end hour (0–23).
    flexibility_score : float
        0.0 (rigid schedule) to 1.0 (fully flexible).
    is_active : bool
        Whether the farmer record is active.
    created_at : datetime
        Record creation timestamp (UTC).
    updated_at : datetime
        Record last-update timestamp (UTC).
    """

    __tablename__ = "farmers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    farm_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    farm_area_hectares: Mapped[float] = mapped_column(Float, nullable=False)
    crop_type: Mapped[str] = mapped_column(String(64), nullable=False)
    soil_type: Mapped[str] = mapped_column(String(64), nullable=False)
    growth_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    location_village: Mapped[str] = mapped_column(String(128), nullable=True)
    canal_id: Mapped[str] = mapped_column(String(32), nullable=False, default="CANAL_A")
    preferred_irrigation_start: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    preferred_irrigation_end: Mapped[int] = mapped_column(Integer, nullable=False, default=18)
    flexibility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    allocation_records: Mapped[List["AllocationRecord"]] = relationship(
        "AllocationRecord", back_populates="farmer", cascade="all, delete-orphan"
    )
    agreements: Mapped[List["Agreement"]] = relationship(
        "Agreement",
        secondary="allocation_records",
        primaryjoin="Farmer.id == AllocationRecord.farmer_id",
        secondaryjoin="AllocationRecord.agreement_id == Agreement.id",
        viewonly=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Farmer id={self.id} farm_id={self.farm_id!r} "
            f"crop={self.crop_type!r} area={self.farm_area_hectares}ha>"
        )
