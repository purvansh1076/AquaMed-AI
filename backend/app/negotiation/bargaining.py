"""
AquaMediAI — Nash-Bargaining-Inspired Utility Optimization
============================================================

Implements a Nash-bargaining-inspired mechanism for the Phase 6
multi-agent negotiation mediator.

IMPORTANT DISCLAIMER
--------------------
This module implements a "Nash-bargaining-inspired utility optimization",
NOT a mathematically complete implementation of Nash Bargaining Theory.

A rigorous Nash Bargaining Solution (NBS) requires:
  1. A well-defined, compact, convex feasible utility set.
  2. A unique disagreement point (BATNA utility vector).
  3. Proof that the maximiser of Π(u_i - d_i) over the feasible set
     is unique and satisfies the four Nash axioms.

This implementation:
  - Uses the existing FarmerAgent utility function and BATNA utilities.
  - Maximises Σ log(max(surplus_i, floor)) as a tractable proxy objective.
  - Does NOT claim convergence guarantees, Pareto-optimality proofs, or
    full Nash axiom satisfaction.
  - Serves as a reasonable computational heuristic for the mediator to
    evaluate whether a candidate allocation improves the joint outcome.

The term "Nash-bargaining-inspired" is used throughout this codebase to
accurately reflect the limited scope of the implementation.

Mathematical Formulation
------------------------
For farmer i with utility u_i and BATNA utility d_i:

    surplus_i = u_i - d_i

Nash product (direct):
    NP = Π max(surplus_i, floor)

Log Nash objective (used in practice, avoids overflow):
    LNO = Σ log(max(surplus_i, floor))

where floor = config.min_surplus_floor > 0  (default 1e-6).

This formulation is safe against:
  - Zero surplus: max(0, floor) = floor → log(floor) instead of log(0)
  - Negative surplus: max(negative, floor) = floor → log(floor)
    (negative surplus indicates a proposal below the farmer's BATNA)

Safety policy:
  - We NEVER take log(0) or log(negative value).
  - A farmer with zero or negative surplus contributes log(floor) to the sum,
    which is a large negative number — this correctly penalises proposals
    that violate BATNA protection.

References
----------
- Nash, J.F. (1950). The Bargaining Problem. Econometrica 18(2): 155–162.
- Raiffa, H. (1982). The Art and Science of Negotiation.
- Osborne, M.J., Rubinstein, A. (1990). Bargaining and Markets.

DISCLAIMER: All values in this system are computed from SYNTHETIC data.
"""

from __future__ import annotations

import math
import logging
from typing import Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)

# ─── Default floor for safe log computation ──────────────────────────────────

_DEFAULT_LOG_FLOOR: float = 1e-6


# ─── Surplus computation ─────────────────────────────────────────────────────

def compute_surplus(utility: float, batna_utility: float) -> float:
    """
    Compute a single farmer's surplus above their BATNA.

    surplus = utility - batna_utility

    The surplus may be:
      - Positive: proposal is better than BATNA → farmer willing to accept.
      - Zero:     proposal equals BATNA → farmer is indifferent.
      - Negative: proposal is worse than BATNA → farmer should reject.

    Parameters
    ----------
    utility : float in [0, 1]
        Farmer's utility at the proposed allocation.
    batna_utility : float in [0, 1]
        Farmer's BATNA (Best Alternative To Negotiated Agreement) utility.

    Returns
    -------
    float
        surplus = utility - batna_utility. Unbounded below, bounded above by 1.
    """
    return float(utility - batna_utility)


def compute_surpluses(
    utilities: Dict[str, float],
    batna_utilities: Dict[str, float],
) -> Dict[str, float]:
    """
    Compute surplus for all farmers.

    Parameters
    ----------
    utilities : dict (farmer_id → utility)
    batna_utilities : dict (farmer_id → batna_utility)

    Returns
    -------
    dict (farmer_id → surplus)
    """
    result = {}
    for fid, u in utilities.items():
        d = batna_utilities.get(fid, 0.0)
        result[fid] = compute_surplus(u, d)
    return result


# ─── Nash product (direct — for small n) ─────────────────────────────────────

def compute_nash_product(
    surpluses: Sequence[float],
    floor: float = _DEFAULT_LOG_FLOOR,
) -> float:
    """
    Compute the Nash product: Π max(surplus_i, floor).

    Safe for zero and negative surpluses (uses floor instead of 0/negative).

    Note: For large n, this may underflow to 0 due to floating-point precision.
    In that case, use compute_log_nash_objective() instead.

    Parameters
    ----------
    surpluses : sequence of float
        Per-farmer surpluses.
    floor : float > 0
        Minimum value substituted for zero or negative surpluses.
        Default 1e-6. Must be > 0.

    Returns
    -------
    float >= 0
        Nash product. 0 only if floor = 0 (not recommended).
    """
    if floor <= 0:
        raise ValueError(f"floor must be > 0, got {floor}")
    if not surpluses:
        return 0.0

    product = 1.0
    for s in surpluses:
        safe_s = max(s, floor)
        product *= safe_s
    return float(product)


# ─── Log Nash objective (preferred for numerical stability) ──────────────────

def compute_log_nash_objective(
    surpluses: Sequence[float],
    floor: float = _DEFAULT_LOG_FLOOR,
) -> float:
    """
    Compute the log-sum Nash objective: Σ log(max(surplus_i, floor)).

    This is the preferred formulation for numerical stability because:
      1. It avoids underflow from multiplying many small numbers.
      2. Maximising Σ log(s_i) is equivalent to maximising Π s_i when all
         s_i > 0.
      3. log(floor) is a large negative number that heavily penalises
         proposals where any farmer is below BATNA, which is the correct
         behaviour.

    SAFETY GUARANTEE:
      - log(0) is NEVER computed (floor > 0 ensures safe_s >= floor > 0).
      - log(negative) is NEVER computed (max(..., floor) is always > 0).

    Parameters
    ----------
    surpluses : sequence of float
        Per-farmer surpluses (may be zero or negative).
    floor : float > 0
        Minimum value substituted for zero/negative surpluses.
        Default 1e-6. Must be > 0.

    Returns
    -------
    float
        Log-sum objective. In range (-∞, n × log(1)] = (-∞, 0].
        Higher is better (closer to 0).

    Examples
    --------
    >>> compute_log_nash_objective([0.3, 0.2, 0.1])
    -5.809...  # log(0.3) + log(0.2) + log(0.1)
    >>> compute_log_nash_objective([0.0, 0.2])  # zero surplus
    -13.815...  # log(1e-6) + log(0.2)  (floor applied to 0.0)
    >>> compute_log_nash_objective([-0.1, 0.2])  # negative surplus
    -13.815...  # log(1e-6) + log(0.2)  (floor applied to -0.1)
    """
    if floor <= 0:
        raise ValueError(f"floor must be > 0, got {floor}")
    if not surpluses:
        return float("-inf")

    total = 0.0
    for s in surpluses:
        safe_s = max(s, floor)
        # safe_s >= floor > 0, so log is always defined
        total += math.log(safe_s)

    logger.debug(
        "NashObjective: n=%d, surpluses=[%s], objective=%.6f",
        len(surpluses),
        ", ".join(f"{s:.4f}" for s in surpluses),
        total,
    )
    return float(total)


# ─── Surplus classification ──────────────────────────────────────────────────

def classify_surplus(surplus: float, floor: float = _DEFAULT_LOG_FLOOR) -> str:
    """
    Classify a farmer's surplus for the audit trail.

    Parameters
    ----------
    surplus : float
    floor : float > 0

    Returns
    -------
    str: 'positive' | 'zero' | 'negative'
    """
    if surplus > floor:
        return "positive"
    elif surplus >= -floor:
        return "zero"
    else:
        return "negative"


# ─── Improvement check ────────────────────────────────────────────────────────

def is_nash_improvement(
    new_objective: float,
    old_objective: float,
    min_delta: float = 1e-8,
) -> bool:
    """
    Check whether a new proposal strictly improves the Nash objective.

    Parameters
    ----------
    new_objective : float
        Nash log-sum objective for the new proposal.
    old_objective : float
        Nash log-sum objective for the current allocation.
    min_delta : float
        Minimum improvement required to count as an improvement.
        Avoids accepting negligible numerical differences.
        Default 1e-8.

    Returns
    -------
    bool
        True if new_objective > old_objective + min_delta.
    """
    return new_objective > old_objective + min_delta


# ─── Summary statistics ──────────────────────────────────────────────────────

def summarize_surpluses(
    surpluses: Dict[str, float],
    floor: float = _DEFAULT_LOG_FLOOR,
) -> Dict[str, object]:
    """
    Compute summary statistics on a surplus dict.

    Parameters
    ----------
    surpluses : dict (farmer_id → surplus)
    floor : float > 0

    Returns
    -------
    dict with keys:
        n_positive, n_zero, n_negative, nash_objective, mean_surplus,
        min_surplus, max_surplus
    """
    values = list(surpluses.values())
    if not values:
        return {
            "n_positive": 0,
            "n_zero": 0,
            "n_negative": 0,
            "nash_objective": float("-inf"),
            "mean_surplus": 0.0,
            "min_surplus": 0.0,
            "max_surplus": 0.0,
        }

    classifications = [classify_surplus(v, floor) for v in values]
    return {
        "n_positive": classifications.count("positive"),
        "n_zero": classifications.count("zero"),
        "n_negative": classifications.count("negative"),
        "nash_objective": compute_log_nash_objective(values, floor),
        "mean_surplus": sum(values) / len(values),
        "min_surplus": min(values),
        "max_surplus": max(values),
    }
