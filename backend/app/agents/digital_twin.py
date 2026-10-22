"""
AquaMediAI — Farmer Digital Twin
==================================

The Digital Twin represents the *current simulation state* of a FarmerAgent.

Design
------
FarmerAgent is IMMUTABLE — it holds the identity, preferences, and
ML-predicted demand.  The DigitalTwin is MUTABLE — it tracks simulation
state changes as water is allocated, concessions are made, and
negotiations progress.

This separation ensures:
  - Reproducibility: the agent itself is always the same.
  - Testability: twin state can be reset without recreating the agent.
  - Thread safety: multiple twins can be created from one agent.

All state transitions are deterministic — there is no randomness.

Negotiation State Machine
--------------------------
  IDLE -> BIDDING -> CONCEDING -> SETTLED
                               -> FAILED

  IDLE:      Initial state before negotiation starts.
  BIDDING:   Agent has submitted a bid (its predicted demand).
  CONCEDING: Agent has made a concession (reduced its ask).
  SETTLED:   Allocation finalised.
  FAILED:    Negotiation failed; BATNA applies.

DISCLAIMER: All values are computed from SYNTHETIC data.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from app.agents.utility import (
    compute_crop_stress,
    compute_utility,
    minimum_requirement_satisfaction,
    water_satisfaction,
)

logger = logging.getLogger(__name__)


class NegotiationState(str, Enum):
    """Negotiation state machine states."""
    IDLE = "IDLE"
    BIDDING = "BIDDING"
    CONCEDING = "CONCEDING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"


@dataclass
class ConcessionRecord:
    """Record of a single concession event."""
    round_number: int
    previous_ask_m3: float
    new_ask_m3: float
    concession_amount_m3: float
    reason: str = ""


class DigitalTwin:
    """
    Mutable simulation state for a FarmerAgent.

    Tracks real-time changes during a negotiation/allocation simulation.
    All calculations are deterministic.

    Parameters
    ----------
    agent : FarmerAgent
        The immutable agent this twin represents.
    """

    def __init__(self, agent: "FarmerAgent") -> None:  # type: ignore[name-defined]
        from app.agents.farmer_agent import FarmerAgent
        if not isinstance(agent, FarmerAgent):
            raise TypeError(f"agent must be FarmerAgent, got {type(agent).__name__}")

        self._agent = agent
        self._reset_state()
        logger.debug("DigitalTwin created for farmer_id=%s", agent.farmer_id)

    def _reset_state(self) -> None:
        """Initialise / reset all mutable simulation fields."""
        self._current_allocation_m3: float = 0.0
        self._allocated_start_hour: Optional[int] = None
        self._current_ask_m3: float = self._agent.predicted_water_demand
        self._negotiation_state: NegotiationState = NegotiationState.IDLE
        self._concession_history: List[ConcessionRecord] = []
        self._satisfaction_score: float = 0.0
        self._utility_score: float = 0.0
        self._unmet_demand_m3: float = self._agent.predicted_water_demand
        self._round_number: int = 0
        # Compute initial stress at zero allocation (no water yet)
        # Deferred until after _agent is set — called from __init__ only
        self._crop_stress_level: float = self._compute_initial_stress()


    # ─── Core state mutation methods ──────────────────────────────────────────

    def _compute_initial_stress(self) -> float:
        """Compute crop stress at zero allocation (initial worst-case state)."""
        return compute_crop_stress(
            allocation_m3=0.0,
            minimum_requirement_m3=self._agent.minimum_water_requirement,
            growth_stage=self._agent.growth_stage,
            crop_sensitivity=self._agent.crop_sensitivity,
        )

    def update_allocation(
        self,
        allocation_m3: float,
        start_hour: Optional[int] = None,
    ) -> None:
        """
        Update the agent's current water allocation.

        Triggers recalculation of satisfaction, utility, and crop stress.

        Parameters
        ----------
        allocation_m3 : float
            Allocated water volume in m³. Must be >= 0.
        start_hour : int or None
            Hour at which irrigation begins (0–23). None = timing unknown.

        Raises
        ------
        ValueError
            If allocation_m3 is negative.
        """
        if allocation_m3 < 0:
            raise ValueError(
                f"allocation_m3 must be >= 0, got {allocation_m3} "
                f"(farmer={self._agent.farmer_id})"
            )
        if start_hour is not None and not (0 <= start_hour <= 23):
            raise ValueError(f"start_hour must be in [0,23], got {start_hour}")

        old_alloc = self._current_allocation_m3
        self._current_allocation_m3 = allocation_m3
        self._allocated_start_hour = start_hour
        self._unmet_demand_m3 = max(
            0.0, self._agent.predicted_water_demand - allocation_m3
        )

        # Recalculate derived scores
        self._satisfaction_score = self.calculate_satisfaction()
        self._utility_score = self.calculate_utility()
        self._crop_stress_level = self.calculate_stress()

        logger.debug(
            "DigitalTwin[%s]: allocation %.1f->%.1f m3, "
            "unmet=%.1f, satisfaction=%.3f, utility=%.4f, stress=%.3f",
            self._agent.farmer_id,
            old_alloc,
            allocation_m3,
            self._unmet_demand_m3,
            self._satisfaction_score,
            self._utility_score,
            self._crop_stress_level,
        )

    def calculate_satisfaction(self) -> float:
        """
        Compute current water satisfaction score.

        S_w = clip(allocation / predicted_demand, 0, 1)

        Returns
        -------
        float in [0, 1]
        """
        return water_satisfaction(
            self._current_allocation_m3,
            self._agent.predicted_water_demand,
        )

    def calculate_utility(self) -> float:
        """
        Compute current utility score using the configured utility function.

        Returns
        -------
        float in [0, 1]
        """
        prefs = self._agent.preferences
        return compute_utility(
            allocation_m3=self._current_allocation_m3,
            predicted_demand_m3=self._agent.predicted_water_demand,
            minimum_requirement_m3=self._agent.minimum_water_requirement,
            irrigation_start_hour=self._allocated_start_hour,
            preferred_start_hour=prefs.preferred_start_hour,
            preferred_end_hour=prefs.preferred_end_hour,
            acceptable_start_hour=prefs.acceptable_start_hour,
            acceptable_end_hour=prefs.acceptable_end_hour,
            urgency=self._agent.urgency,
            crop_sensitivity=self._agent.crop_sensitivity,
            flexibility=self._agent.flexibility,
            weights=self._agent.utility_weights,
        )

    def calculate_stress(self) -> float:
        """
        Compute current crop stress level.

        Stress = (1 - min_req_satisfaction) * stage_criticality * crop_sensitivity

        Returns
        -------
        float in [0, 1]
            0.0 = no stress, 1.0 = maximum stress.
        """
        return compute_crop_stress(
            allocation_m3=self._current_allocation_m3,
            minimum_requirement_m3=self._agent.minimum_water_requirement,
            growth_stage=self._agent.growth_stage,
            crop_sensitivity=self._agent.crop_sensitivity,
        )

    def apply_concession(
        self,
        new_ask_m3: float,
        reason: str = "",
    ) -> ConcessionRecord:
        """
        Apply a concession — reduce the agent's current water ask.

        A concession must be a reduction (new_ask < current_ask).
        The new ask must not go below the minimum_water_requirement (BATNA floor).

        Parameters
        ----------
        new_ask_m3 : float
            Reduced water ask (m³).
        reason : str
            Human-readable reason for the concession.

        Returns
        -------
        ConcessionRecord
            Record of the concession event.

        Raises
        ------
        ValueError
            If new_ask_m3 >= current_ask or < minimum_water_requirement.
        """
        if new_ask_m3 >= self._current_ask_m3:
            raise ValueError(
                f"new_ask_m3 ({new_ask_m3:.2f}) must be < current_ask "
                f"({self._current_ask_m3:.2f}) for farmer {self._agent.farmer_id}"
            )
        if new_ask_m3 < self._agent.minimum_water_requirement:
            raise ValueError(
                f"new_ask_m3 ({new_ask_m3:.2f}) must be >= minimum_water_requirement "
                f"({self._agent.minimum_water_requirement:.2f}) — cannot concede below BATNA floor "
                f"for farmer {self._agent.farmer_id}"
            )

        self._round_number += 1
        record = ConcessionRecord(
            round_number=self._round_number,
            previous_ask_m3=self._current_ask_m3,
            new_ask_m3=new_ask_m3,
            concession_amount_m3=self._current_ask_m3 - new_ask_m3,
            reason=reason,
        )
        self._concession_history.append(record)
        self._current_ask_m3 = new_ask_m3
        self._negotiation_state = NegotiationState.CONCEDING

        logger.debug(
            "DigitalTwin[%s]: concession round %d: %.1f->%.1f m3 (%s)",
            self._agent.farmer_id,
            self._round_number,
            record.previous_ask_m3,
            new_ask_m3,
            reason,
        )
        return record

    def set_negotiation_state(self, state: NegotiationState) -> None:
        """Manually advance the negotiation state machine."""
        self._negotiation_state = state
        logger.debug(
            "DigitalTwin[%s]: negotiation state -> %s", self._agent.farmer_id, state.value
        )

    def settle(self, final_allocation_m3: float, start_hour: Optional[int] = None) -> None:
        """Finalise the allocation and mark the twin as SETTLED."""
        self.update_allocation(final_allocation_m3, start_hour)
        self._negotiation_state = NegotiationState.SETTLED

    def fail(self) -> None:
        """Apply BATNA outcome and mark the twin as FAILED."""
        batna = self._agent.batna
        self.update_allocation(batna.fallback_allocation_m3, start_hour=None)
        self._negotiation_state = NegotiationState.FAILED
        logger.info(
            "DigitalTwin[%s]: negotiation FAILED — applying BATNA (%.1f m3, utility=%.4f)",
            self._agent.farmer_id,
            batna.fallback_allocation_m3,
            batna.fallback_utility,
        )

    def reset(self) -> None:
        """Reset the twin to its initial state."""
        self._reset_state()
        logger.debug("DigitalTwin[%s]: reset to initial state", self._agent.farmer_id)

    # ─── Read-only properties ─────────────────────────────────────────────────

    @property
    def agent(self) -> "FarmerAgent":  # type: ignore[name-defined]
        return self._agent

    @property
    def farmer_id(self) -> str:
        return self._agent.farmer_id

    @property
    def current_allocation_m3(self) -> float:
        return self._current_allocation_m3

    @property
    def allocated_start_hour(self) -> Optional[int]:
        return self._allocated_start_hour

    @property
    def current_ask_m3(self) -> float:
        return self._current_ask_m3

    @property
    def unmet_demand_m3(self) -> float:
        return self._unmet_demand_m3

    @property
    def crop_stress_level(self) -> float:
        return self._crop_stress_level

    @property
    def satisfaction_score(self) -> float:
        return self._satisfaction_score

    @property
    def utility_score(self) -> float:
        return self._utility_score

    @property
    def negotiation_state(self) -> NegotiationState:
        return self._negotiation_state

    @property
    def concession_history(self) -> List[ConcessionRecord]:
        return list(self._concession_history)  # defensive copy

    @property
    def total_concessions_made(self) -> int:
        return len(self._concession_history)

    @property
    def total_concession_volume_m3(self) -> float:
        return sum(r.concession_amount_m3 for r in self._concession_history)

    @property
    def is_minimum_met(self) -> bool:
        """True if the current allocation meets the minimum water requirement."""
        return self._current_allocation_m3 >= self._agent.minimum_water_requirement

    @property
    def min_req_satisfaction(self) -> float:
        """Satisfaction relative to minimum requirement, not demand."""
        return minimum_requirement_satisfaction(
            self._current_allocation_m3, self._agent.minimum_water_requirement
        )

    # ─── State export ─────────────────────────────────────────────────────────

    def get_state_dict(self) -> Dict[str, Any]:
        """
        Return the full simulation state as a serialisable dict.

        This is the primary interface for the negotiation engine.
        All values are computed — never hard-coded.
        """
        batna = self._agent.batna
        return {
            "farmer_id": self._agent.farmer_id,
            "predicted_demand_m3": round(self._agent.predicted_water_demand, 2),
            "minimum_requirement_m3": round(self._agent.minimum_water_requirement, 2),
            "current_allocation_m3": round(self._current_allocation_m3, 2),
            "current_ask_m3": round(self._current_ask_m3, 2),
            "allocated_start_hour": self._allocated_start_hour,
            "unmet_demand_m3": round(self._unmet_demand_m3, 2),
            "satisfaction_score": round(self._satisfaction_score, 4),
            "utility_score": round(self._utility_score, 4),
            "crop_stress_level": round(self._crop_stress_level, 4),
            "is_minimum_met": self.is_minimum_met,
            "min_req_satisfaction": round(self.min_req_satisfaction, 4),
            "urgency": round(self._agent.urgency, 4),
            "crop_sensitivity": round(self._agent.crop_sensitivity, 4),
            "flexibility": round(self._agent.flexibility, 4),
            "batna_allocation_m3": round(batna.fallback_allocation_m3, 2),
            "batna_utility": round(batna.fallback_utility, 4),
            "negotiation_state": self._negotiation_state.value,
            "total_concessions": self.total_concessions_made,
            "total_concession_volume_m3": round(self.total_concession_volume_m3, 2),
        }

    def __repr__(self) -> str:
        return (
            f"DigitalTwin(id={self._agent.farmer_id!r}, "
            f"state={self._negotiation_state.value}, "
            f"alloc={self._current_allocation_m3:.1f}m3, "
            f"utility={self._utility_score:.4f}, "
            f"stress={self._crop_stress_level:.4f})"
        )
