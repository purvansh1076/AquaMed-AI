"""
AquaMediAI — Agreement ORM Model
==================================
A signed, auditable agreement produced by the mediation pipeline.
Stores the full mediation result including conflict detection summary,
allocation decisions, and explainability narrative.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List, Optional

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
    from app.models.scenario import Scenario
    from app.models.allocation import AllocationRecord


class Agreement(Base):
    """
    SQLAlchemy ORM model for a completed water-sharing mediation agreement.

    This is the top-level audit record. It links to a Scenario (context),
    contains multiple AllocationRecords (one per farmer), and stores the
    full explanation narrative.

    Attributes
    ----------
    id : int
        Primary key.
    scenario_id : int
        FK → scenarios.id — the context in which this agreement was reached.
    status : str
        'pending', 'in_progress', 'agreed', 'failed', 'partial'.
    total_water_available_m3 : float
        Total water available in this session (m³/day).
    total_water_allocated_m3 : float
        Total water actually allocated across all farmers.
    num_conflicts_detected : int
        Number of conflicts detected before mediation.
    num_negotiation_rounds : int
        Rounds of negotiation executed.
    overall_utility : float
        Aggregate utility score across all farmers (0.0–1.0).
    nash_welfare : float
        Nash social welfare product of utilities (for academic reporting).
    conflict_summary : str
        JSON-serialised list of detected conflicts.
    explanation_narrative : str
        Full human-readable explanation of the mediation outcome.
    is_synthetic : bool
        Always True for MVP.
    agreed_at : datetime
        Timestamp when the agreement was finalised.
    created_at : datetime
        Record creation timestamp (UTC).
    """

    __tablename__ = "agreements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scenario_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("scenarios.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # ── Status ─────────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", index=True
    )

    # ── Allocation summary ─────────────────────────────────────────────────────
    total_water_available_m3: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_water_allocated_m3: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Mediation summary ──────────────────────────────────────────────────────
    num_conflicts_detected: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    num_negotiation_rounds: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    overall_utility: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    nash_welfare: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    # ── Rich text fields ───────────────────────────────────────────────────────
    conflict_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanation_narrative: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Metadata ───────────────────────────────────────────────────────────────
    is_synthetic: Mapped[bool] = mapped_column(Integer, nullable=False, default=True)

    agreed_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    scenario: Mapped[Optional["Scenario"]] = relationship(
        "Scenario", back_populates="agreements"
    )
    allocation_records: Mapped[List["AllocationRecord"]] = relationship(
        "AllocationRecord", back_populates="agreement", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Agreement id={self.id} scenario_id={self.scenario_id} "
            f"status={self.status!r} utility={self.overall_utility:.3f}>"
        )
