"""
AquaMediAI — Farmer Utility Function
======================================

Implements the deterministic utility function U_i for each FarmerAgent.

Mathematical Definition
------------------------

U_i = (w1 * water_satisfaction
      + w2 * timing_satisfaction
      + w3 * urgency_protection
      + w4 * min_req_satisfaction
      - w5 * stress_penalty * crop_sensitivity)
      normalised to [0, 1]

where:

    water_satisfaction(a, d) = clip(a / d, 0, 1)
        How much of the predicted demand was fulfilled.
        a = allocation_m3, d = predicted_demand_m3

    timing_satisfaction(h, ps, pe, as_, ae) =
        1.0  if ps <= h <= pe          (inside preferred window)
        0.5  if as_ <= h <= ae (and not in preferred)  (acceptable window)
        0.0  otherwise  (outside all windows)
        None / 0.0 if h is None  (no timing info — worst case, used for BATNA)

    urgency_protection(u, ws) = 1.0 - u * (1.0 - ws)
        High urgency + low water = low urgency protection.
        Penalises unmet demand for high-urgency farmers.
        u = urgency [0,1], ws = water_satisfaction [0,1]

    min_req_satisfaction(a, m) = clip(a / m, 0, 1)
        Whether the minimum crop survival requirement was met.
        a = allocation_m3, m = minimum_requirement_m3

    stress_penalty = 1.0 - min_req_satisfaction
        Penalises cases where minimum requirement is not met.
        Scaled by crop_sensitivity to penalise sensitive crops more.

The raw utility sum is normalised by the theoretical maximum possible
utility to produce a value in [0, 1].

References
----------
- FAO-56 (Allen et al. 1998): yield-response factors Ky.
- Nash, J.F. (1950): utility in bargaining theory.
- Raiffa, H. (1982): The Art and Science of Negotiation.

DISCLAIMER: All values in this system are computed from SYNTHETIC data.
"""

from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Import UtilityWeights here (avoid circular by only importing type) ────────
# Full import at call sites to avoid circular dependency with farmer_agent.py


def water_satisfaction(allocation_m3: float, predicted_demand_m3: float) -> float:
    """
    Compute water satisfaction score.

    S_w(a, d) = clip(a / d, 0, 1)

    Parameters
    ----------
    allocation_m3 : float
        Water actually allocated (m³). May be 0.
    predicted_demand_m3 : float
        ML-predicted water demand (m³). Must be > 0.

    Returns
    -------
    float in [0, 1]
        1.0 = full satisfaction (allocation >= demand)
        0.0 = no water received
    """
    if predicted_demand_m3 <= 0:
        raise ValueError(f"predicted_demand_m3 must be > 0, got {predicted_demand_m3}")
    return float(min(1.0, max(0.0, allocation_m3 / predicted_demand_m3)))


def timing_satisfaction(
    irrigation_start_hour: Optional[int],
    preferred_start_hour: int,
    preferred_end_hour: int,
    acceptable_start_hour: int,
    acceptable_end_hour: int,
) -> float:
    """
    Compute timing satisfaction score.

    T(h) =
        1.0  if preferred_start <= h <= preferred_end
        0.5  if acceptable_start <= h <= acceptable_end (but outside preferred)
        0.0  if h is None or outside all windows

    The 0.5 score for the acceptable-but-not-preferred window reflects that
    the farmer can tolerate the timing but does not prefer it.  This
    intentionally creates a gradient that the negotiation engine can optimise.

    Parameters
    ----------
    irrigation_start_hour : int or None
        Hour at which irrigation starts (0–23). None = no timing known (BATNA case).
    preferred_start_hour, preferred_end_hour : int
        Preferred irrigation window bounds.
    acceptable_start_hour, acceptable_end_hour : int
        Outer bounds of the tolerable window.

    Returns
    -------
    float in {0.0, 0.5, 1.0}
    """
    if irrigation_start_hour is None:
        return 0.0

    h = irrigation_start_hour
    if preferred_start_hour <= h <= preferred_end_hour:
        return 1.0
    elif acceptable_start_hour <= h <= acceptable_end_hour:
        return 0.5
    else:
        return 0.0


def urgency_protection(urgency: float, water_sat: float) -> float:
    """
    Compute urgency-protection component.

    P_u(u, ws) = 1.0 - u * (1.0 - ws)

    Interpretation:
      - If urgency = 0: protection is always 1.0 (urgency plays no role)
      - If urgency = 1 and water_sat = 1: protection = 1.0 (full water = safe)
      - If urgency = 1 and water_sat = 0: protection = 0.0 (no water, critical)

    Parameters
    ----------
    urgency : float in [0, 1]
    water_sat : float in [0, 1]

    Returns
    -------
    float in [0, 1]
    """
    return float(1.0 - urgency * (1.0 - water_sat))


def minimum_requirement_satisfaction(
    allocation_m3: float, minimum_requirement_m3: float
) -> float:
    """
    Compute minimum requirement satisfaction.

    M(a, m) = clip(a / m, 0, 1)

    Parameters
    ----------
    allocation_m3 : float
        Allocated water (m³).
    minimum_requirement_m3 : float
        Minimum crop survival threshold (m³). Must be > 0.

    Returns
    -------
    float in [0, 1]
    """
    if minimum_requirement_m3 <= 0:
        raise ValueError(
            f"minimum_requirement_m3 must be > 0, got {minimum_requirement_m3}"
        )
    return float(min(1.0, max(0.0, allocation_m3 / minimum_requirement_m3)))


def compute_utility(
    allocation_m3: float,
    predicted_demand_m3: float,
    minimum_requirement_m3: float,
    irrigation_start_hour: Optional[int],
    preferred_start_hour: int,
    preferred_end_hour: int,
    acceptable_start_hour: int,
    acceptable_end_hour: int,
    urgency: float,
    crop_sensitivity: float,
    flexibility: float,
    weights: Optional["UtilityWeights"] = None,  # type: ignore[name-defined]
) -> float:
    """
    Compute the overall farmer utility U_i.

    U_i = (w1 * S_w
          + w2 * T
          + w3 * P_u
          + w4 * M
          - w5 * (1 - M) * crop_sensitivity)
          / U_max

    where U_max is the maximum achievable utility under these weights,
    used to normalise the score to [0, 1].

    Parameters
    ----------
    allocation_m3 : float
        Water allocated (m³). 0 = no water.
    predicted_demand_m3 : float
        ML-predicted water demand (m³).
    minimum_requirement_m3 : float
        Minimum crop survival threshold (m³).
    irrigation_start_hour : int or None
        Hour of irrigation start (0–23). None = no timing (BATNA).
    preferred_start_hour, preferred_end_hour : int
        Preferred window bounds.
    acceptable_start_hour, acceptable_end_hour : int
        Acceptable window bounds.
    urgency : float in [0, 1]
        Farmer urgency score.
    crop_sensitivity : float in [0, 1]
        Crop water stress sensitivity.
    flexibility : float in [0, 1]
        Scheduling flexibility (influences acceptable window).
    weights : UtilityWeights, optional
        Configurable component weights. Defaults to UtilityWeights().

    Returns
    -------
    float in [0, 1]
        Normalised utility score.
    """
    # Lazy import to avoid circular
    from app.agents.farmer_agent import UtilityWeights as UW
    w = weights if weights is not None else UW()

    # ── Component scores ──────────────────────────────────────────────────────
    s_w = water_satisfaction(allocation_m3, predicted_demand_m3)
    t = timing_satisfaction(
        irrigation_start_hour,
        preferred_start_hour,
        preferred_end_hour,
        acceptable_start_hour,
        acceptable_end_hour,
    )
    p_u = urgency_protection(urgency, s_w)
    m = minimum_requirement_satisfaction(allocation_m3, minimum_requirement_m3)
    stress = 1.0 - m  # inverse: stress when minimum not met

    # ── Raw utility ───────────────────────────────────────────────────────────
    raw = (
        w.water_satisfaction * s_w
        + w.timing_satisfaction * t
        + w.urgency_protection * p_u
        + w.crop_protection * m
        - w.stress_penalty * stress * crop_sensitivity
    )

    # ── Normalise to [0, 1] by computing maximum achievable utility ──────────
    # Maximum is when: s_w=1, t=1, p_u=1, m=1, stress=0
    u_max = (
        w.water_satisfaction
        + w.timing_satisfaction
        + w.urgency_protection
        + w.crop_protection
        # stress_penalty term = 0 at maximum
    )
    # Minimum (theoretical) for normalisation reference
    # When: s_w=0, t=0, p_u=1-urgency, m=0, stress=1
    u_min = (
        0.0
        + 0.0
        + w.urgency_protection * (1.0 - urgency)
        + 0.0
        - w.stress_penalty * crop_sensitivity
    )

    if u_max <= u_min:
        # Degenerate case — return 0.5 as neutral
        return 0.5

    # Normalise raw to [0, 1] relative to [u_min, u_max]
    normalised = (raw - u_min) / (u_max - u_min)
    result = float(max(0.0, min(1.0, normalised)))

    logger.debug(
        "Utility: alloc=%.1f demand=%.1f s_w=%.3f t=%.3f p_u=%.3f m=%.3f -> U=%.4f",
        allocation_m3, predicted_demand_m3, s_w, t, p_u, m, result,
    )
    return result


def compute_crop_stress(
    allocation_m3: float,
    minimum_requirement_m3: float,
    growth_stage: str,
    crop_sensitivity: float,
) -> float:
    """
    Compute normalised crop stress level.

    Stress = (1 - min_req_satisfaction) * stage_criticality * crop_sensitivity

    Parameters
    ----------
    allocation_m3 : float
    minimum_requirement_m3 : float
    growth_stage : str
    crop_sensitivity : float in [0,1]

    Returns
    -------
    float in [0, 1]
        0.0 = no stress, 1.0 = maximum stress.
    """
    from app.agents.farmer_agent import STAGE_CRITICALITY

    m = minimum_requirement_satisfaction(allocation_m3, minimum_requirement_m3)
    stage_crit = STAGE_CRITICALITY.get(growth_stage, 0.5)
    stress = (1.0 - m) * stage_crit * crop_sensitivity
    return float(min(1.0, max(0.0, stress)))
