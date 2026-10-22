"""
AquaMediAI — Scenario ORM Model
================================
A Scenario captures the water-availability context for a mediation session.
Each scenario has a type (one of 8 defined synthetic types) and associated
hydrological parameters.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
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
    from app.models.agreement import Agreement


# Valid scenario type labels — must match data_generator.py
SCENARIO_TYPES = [
    "normal_water",
    "moderate_shortage",
    "severe_shortage",
    "sudden_rainfall",
    "canal_reduction",
    "simultaneous_demand",
    "high_urgency_farmer",
    "flexible_farmer",
]


class Scenario(Base):
    """
    SQLAlchemy ORM model for a water-sharing scenario / mediation session.

    Attributes
    ----------
    id : int
        Primary key.
    scenario_type : str
        One of the 8 defined scenario type labels.
    label : str
        Human-readable scenario label / title.
    description : str
        Narrative description of the scenario.
    total_available_water_m3 : float
        Total water available from the source (cubic metres / day).
    canal_capacity_m3_per_hour : float
        Maximum flow rate of the shared canal (m³/hour).
    num_farmers : int
        Number of farmers involved in this scenario.
    season : str
        Agricultural season label (e.g., 'kharif', 'rabi', 'zaid').
    rainfall_mm : float
        Recent rainfall in millimetres (affects effective demand).
    temperature_celsius : float
        Average daily temperature (affects evapotranspiration).
    humidity_percent : float
        Relative humidity percentage.
    is_synthetic : bool
        Always True for MVP — explicitly marks data as synthetic.
    created_at : datetime
        Record creation timestamp (UTC).
    """

    __tablename__ = "scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Hydrological parameters ────────────────────────────────────────────────
    total_available_water_m3: Mapped[float] = mapped_column(Float, nullable=False)
    canal_capacity_m3_per_hour: Mapped[float] = mapped_column(Float, nullable=False, default=50.0)
    num_farmers: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # ── Environmental context ──────────────────────────────────────────────────
    season: Mapped[str] = mapped_column(String(32), nullable=False, default="kharif")
    rainfall_mm: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    temperature_celsius: Mapped[float] = mapped_column(Float, nullable=False, default=28.0)
    humidity_percent: Mapped[float] = mapped_column(Float, nullable=False, default=60.0)

    # ── Metadata ───────────────────────────────────────────────────────────────
    is_synthetic: Mapped[bool] = mapped_column(
        Integer, nullable=False, default=True  # stored as 1/0 in some DBs
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    agreements: Mapped[List["Agreement"]] = relationship(
        "Agreement", back_populates="scenario", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Scenario id={self.id} type={self.scenario_type!r} "
            f"water={self.total_available_water_m3}m³ farmers={self.num_farmers}>"
        )
