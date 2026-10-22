"""
AquaMediAI — AllocationRecord ORM Model
========================================
Records the water allocation assigned to a specific farmer within an
Agreement. Each Agreement contains one AllocationRecord per farmer.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.farmer import Farmer
    from app.models.agreement import Agreement


class AllocationRecord(Base):
    """
    SQLAlchemy ORM model for a single farmer's water allocation within an Agreement.

    Attributes
    ----------
    id : int
        Primary key.
    agreement_id : int
        FK → agreements.id
    farmer_id : int
        FK → farmers.id
    predicted_demand_m3 : float
        ML-predicted water demand for this farmer (m³/day).
    minimum_requirement_m3 : float
        Hard minimum water requirement (m³/day) — must not be violated
        where supply allows.
    allocated_water_m3 : float
        Final allocated water quantity (m³/day) after optimisation + negotiation.
    allocation_fraction : float
        allocated / predicted_demand (0.0–1.0+).
    utility_score : float
        Farmer utility score for this allocation (0.0–1.0).
    negotiation_round : int
        Which negotiation round produced this allocation.
    allocation_method : str
        Method used: 'milp_initial', 'nash_bargaining', 'proportional_fallback'.
    explanation : str
        Human-readable rationale for this allocation.
    created_at : datetime
        Record creation timestamp (UTC).
    """

    __tablename__ = "allocation_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    agreement_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agreements.id", ondelete="CASCADE"), nullable=False, index=True
    )
    farmer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("farmers.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ── Demand & Allocation ────────────────────────────────────────────────────
    predicted_demand_m3: Mapped[float] = mapped_column(Float, nullable=False)
    minimum_requirement_m3: Mapped[float] = mapped_column(Float, nullable=False)
    allocated_water_m3: Mapped[float] = mapped_column(Float, nullable=False)
    allocation_fraction: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    utility_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Metadata ───────────────────────────────────────────────────────────────
    negotiation_round: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    allocation_method: Mapped[str] = mapped_column(
        String(64), nullable=False, default="milp_initial"
    )
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    farmer: Mapped["Farmer"] = relationship("Farmer", back_populates="allocation_records")
    agreement: Mapped["Agreement"] = relationship("Agreement", back_populates="allocation_records")

    def __repr__(self) -> str:
        return (
            f"<AllocationRecord id={self.id} farmer_id={self.farmer_id} "
            f"allocated={self.allocated_water_m3:.1f}m³ "
            f"method={self.allocation_method!r}>"
        )
