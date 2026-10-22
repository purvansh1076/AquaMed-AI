"""
AquaMediAI - Prediction Explainer
===================================

Wraps the existing WaterDemandExplainer (Phase 2) to produce
PredictionExplanation objects.

Design
------
This module is a thin adapter. It reuses the existing WaterDemandExplainer
and SHAPExplanation from app.ml.explainer -- it does NOT create a second
SHAP implementation.

The explainer:
  1. Calls the existing WaterDemandExplainer.explain_single()
  2. Converts FeatureContribution objects to FeatureContributionExplanation
  3. Derives direction from the actual SHAP value (not hard-coded)
  4. Generates deterministic rationale text from structured values

Direction is determined as:
  shap_value > 1e-9  -> INCREASES
  shap_value < -1e-9 -> DECREASES
  otherwise          -> NEGLIGIBLE

This matches the tolerance used in WaterDemandExplainer.explain_single().

IMPORTANT
---------
- This module is READ-ONLY with respect to predictions.
- It never modifies PredictionResult or SHAPExplanation.
- The same inputs always produce the same explanation (deterministic).
- All data is SYNTHETIC.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.explainability.explanation_types import (
    ContributionDirection,
    FeatureContributionExplanation,
    PredictionExplanation,
)

logger = logging.getLogger(__name__)

# Tolerance matching WaterDemandExplainer._explain_single()
_SHAP_ZERO_TOLERANCE: float = 1e-9


def _direction_from_shap(shap_value: float) -> ContributionDirection:
    """
    Determine contribution direction from actual SHAP value.

    Direction is computed from the data -- NOT hard-coded per feature.

    Parameters
    ----------
    shap_value : float

    Returns
    -------
    ContributionDirection
    """
    if shap_value > _SHAP_ZERO_TOLERANCE:
        return ContributionDirection.INCREASES
    elif shap_value < -_SHAP_ZERO_TOLERANCE:
        return ContributionDirection.DECREASES
    else:
        return ContributionDirection.NEGLIGIBLE


def _build_rationale(
    feature: str,
    direction: ContributionDirection,
    shap_value: float,
    raw_value: float,
) -> str:
    """
    Build a deterministic rationale sentence for a feature contribution.

    Parameters
    ----------
    feature : str
    direction : ContributionDirection
    shap_value : float
    raw_value : float

    Returns
    -------
    str
    """
    direction_phrase = {
        ContributionDirection.INCREASES: "increased",
        ContributionDirection.DECREASES: "decreased",
        ContributionDirection.NEGLIGIBLE: "had negligible effect on",
    }[direction]
    return (
        f"Feature '{feature}' (value={raw_value:.4g}) {direction_phrase} "
        f"the predicted demand by {abs(shap_value):.4g} m3/day "
        f"(SHAP contribution: {shap_value:+.4g})."
    )


def explain_prediction_from_shap(
    shap_explanation: Any,
    farmer_id: Optional[str] = None,
    model_version: str = "unknown",
    top_n: int = 5,
) -> PredictionExplanation:
    """
    Build a PredictionExplanation from an existing SHAPExplanation.

    This function adapts SHAPExplanation (from app.ml.explainer) to the
    structured PredictionExplanation type. It does NOT call the SHAP library
    again -- it reads from the already-computed SHAPExplanation object.

    Parameters
    ----------
    shap_explanation : SHAPExplanation
        Computed by WaterDemandExplainer.explain_single().
    farmer_id : str or None
        Farmer identifier to attach to the explanation.
    model_version : str
        Model version string.
    top_n : int
        Number of top contributors to include in top_contributors.

    Returns
    -------
    PredictionExplanation
    """
    if shap_explanation is None:
        raise ValueError("shap_explanation must not be None")

    all_feature_explanations: List[FeatureContributionExplanation] = []

    for rank, fc in enumerate(shap_explanation.features, start=1):
        direction = _direction_from_shap(fc.shap_value)
        rationale = _build_rationale(fc.feature, direction, fc.shap_value, fc.raw_value)
        all_feature_explanations.append(
            FeatureContributionExplanation(
                feature=fc.feature,
                raw_value=fc.raw_value,
                shap_value=fc.shap_value,
                direction=direction,
                abs_shap=fc.abs_shap,
                rank=rank,
                rationale=rationale,
            )
        )

    top_contributors = all_feature_explanations[:top_n]
    positive_contributors = [
        f for f in all_feature_explanations
        if f.direction == ContributionDirection.INCREASES
    ]
    negative_contributors = [
        f for f in all_feature_explanations
        if f.direction == ContributionDirection.DECREASES
    ]

    # Deterministic summary
    predicted = shap_explanation.prediction
    base = shap_explanation.base_value
    farmer_part = f"Farmer {farmer_id}: " if farmer_id else ""
    if top_contributors:
        top_feat = top_contributors[0].feature
        top_dir = top_contributors[0].direction.value
        summary = (
            f"{farmer_part}Predicted water demand is {predicted:.2f} m3/day "
            f"(base value: {base:.2f} m3/day). "
            f"Top contributor: '{top_feat}' ({top_dir} demand)."
        )
    else:
        summary = (
            f"{farmer_part}Predicted water demand is {predicted:.2f} m3/day "
            f"(base value: {base:.2f} m3/day). "
            f"No significant SHAP contributors identified."
        )

    return PredictionExplanation(
        farmer_id=farmer_id,
        predicted_demand_m3=float(shap_explanation.prediction),
        model_name=shap_explanation.model_name,
        model_version=model_version,
        base_value=float(shap_explanation.base_value),
        top_contributors=top_contributors,
        positive_contributors=positive_contributors,
        negative_contributors=negative_contributors,
        all_features=all_feature_explanations,
        shap_available=True,
        summary=summary,
    )


def explain_prediction_without_shap(
    predicted_demand_m3: float,
    model_name: str,
    model_version: str,
    farmer_id: Optional[str] = None,
    feature_values: Optional[Dict[str, float]] = None,
) -> PredictionExplanation:
    """
    Build a minimal PredictionExplanation when SHAP is unavailable.

    Provides structured information about the prediction without SHAP
    attribution values. Returns shap_available=False.

    Parameters
    ----------
    predicted_demand_m3 : float
    model_name : str
    model_version : str
    farmer_id : str or None
    feature_values : dict or None
        Raw feature values used in prediction, if available.

    Returns
    -------
    PredictionExplanation
    """
    farmer_part = f"Farmer {farmer_id}: " if farmer_id else ""
    summary = (
        f"{farmer_part}Predicted water demand is {predicted_demand_m3:.2f} m3/day "
        f"(model: {model_name}). "
        f"SHAP explanation is unavailable for this prediction."
    )

    return PredictionExplanation(
        farmer_id=farmer_id,
        predicted_demand_m3=predicted_demand_m3,
        model_name=model_name,
        model_version=model_version,
        base_value=0.0,
        top_contributors=[],
        positive_contributors=[],
        negative_contributors=[],
        all_features=[],
        shap_available=False,
        summary=summary,
    )
