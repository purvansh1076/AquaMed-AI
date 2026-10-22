"""
AquaMediAI — Agent Factory
============================

Builds FarmerAgent objects by combining:

    Synthetic Farmer Data  (from SyntheticDataGenerator)
        +
    ML Predicted Water Demand  (from WaterDemandPredictor — NOT duplicated)
        +
    Farmer Preferences  (derived from raw features)
        =
    FarmerAgent

Design Principles
-----------------
- The factory is the ONLY place that calls the predictor.
- No ML prediction logic is duplicated here.
- All water demand values come from the Phase 2 WaterDemandPredictor.
- Agents are built in batch for efficiency.

Pipeline
--------
    SyntheticDataGenerator.generate_scenario()
            │
            ▼
    WaterDemandPredictor.predict_single() per farmer
            │  predicted_demand_m3
            ▼
    _build_preferences()   — derive water bounds, timing, flexibility
            │
            ▼
    FarmerAgent.__init__()  — validates all fields
            │
            ▼
    DigitalTwin              (optional, returned separately)

DISCLAIMER: All data is SYNTHETIC.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.agents.digital_twin import DigitalTwin
from app.agents.farmer_agent import FarmerAgent, UtilityWeights

logger = logging.getLogger(__name__)

# ─── Constants for water bound derivation ─────────────────────────────────────
# These multipliers are grounded in FAO-56 agronomic literature.

# Minimum water = fraction of predicted demand (survival threshold)
# FAO-56 depletion: crop stress begins at ~40% of ETc fulfilment
_MIN_WATER_FRACTION_DEFAULT: float = 0.40

# Maximum water = fraction above demand (diminishing returns / runoff)
# Based on soil saturation point — typically 15–25% above ETc demand
_MAX_WATER_FRACTION_DEFAULT: float = 1.20


def build_agent(
    farmer_data: Dict[str, Any],
    predictor: "WaterDemandPredictor",  # type: ignore[name-defined]
    farmer_name: Optional[str] = None,
    utility_weights: Optional[UtilityWeights] = None,
) -> Tuple[FarmerAgent, "PredictionResult"]:  # type: ignore[name-defined]
    """
    Build a single FarmerAgent from raw farmer data + ML predictor.

    Parameters
    ----------
    farmer_data : dict
        Raw farmer features (same schema as WaterDemandPredictor.predict_single).
        Required keys include: crop_type, farm_area_hectares, soil_type,
        growth_stage, et0_mm_per_day, kc_value, etc_mm_per_day.
        Optional keys: preferred_start_hour, irrigation_window_hours,
        flexibility_score, urgency_score, crop_stress_index,
        minimum_requirement_m3 (if pre-computed).
    predictor : WaterDemandPredictor
        Initialised Phase 2 predictor (loaded from artifacts).
    farmer_name : str, optional
        Human-readable name. Defaults to farmer_id.
    utility_weights : UtilityWeights, optional
        Custom utility weights. Defaults to UtilityWeights().

    Returns
    -------
    (FarmerAgent, PredictionResult)
        The constructed agent and the raw prediction result.

    Raises
    ------
    ValueError
        If required fields are missing or invalid.
    """
    # ── Step 1: Run ML prediction ─────────────────────────────────────────────
    prediction = predictor.predict_single(farmer_data)
    predicted_demand = prediction.predicted_water_demand_m3

    # ── Step 2: Extract / derive agent parameters ─────────────────────────────
    farmer_id = str(farmer_data.get("farmer_id", "UNKNOWN"))
    name = farmer_name or farmer_id

    crop = str(farmer_data.get("crop_type", "wheat"))
    soil_type = str(farmer_data.get("soil_type", "loam"))
    growth_stage = str(farmer_data.get("growth_stage", "vegetative"))
    farm_area = float(farmer_data.get("farm_area_hectares", 1.0))

    # Water bounds
    if "minimum_requirement_m3" in farmer_data and farmer_data["minimum_requirement_m3"]:
        min_water = float(farmer_data["minimum_requirement_m3"])
    else:
        min_water = predicted_demand * _MIN_WATER_FRACTION_DEFAULT

    max_water = predicted_demand * _MAX_WATER_FRACTION_DEFAULT

    # Safety: clamp min to [0.01, predicted_demand]
    min_water = max(0.01, min(min_water, predicted_demand))
    max_water = max(predicted_demand, max_water)

    # Timing
    preferred_start = int(farmer_data.get("preferred_start_hour", 6))
    window_hours = int(farmer_data.get("irrigation_window_hours", 4))
    preferred_end = min(23, preferred_start + window_hours)

    # Ensure preferred_end > preferred_start
    if preferred_end <= preferred_start:
        preferred_end = preferred_start + 1

    # Agent scores
    urgency = float(farmer_data.get("urgency_score", 0.5))
    crop_sensitivity = float(farmer_data.get("crop_stress_index", 0.5))
    flexibility = float(farmer_data.get("flexibility_score", 0.5))

    # Clamp all [0,1] scores
    urgency = max(0.0, min(1.0, urgency))
    crop_sensitivity = max(0.0, min(1.0, crop_sensitivity))
    flexibility = max(0.0, min(1.0, flexibility))

    # ── Step 3: Build agent ────────────────────────────────────────────────────
    agent = FarmerAgent(
        farmer_id=farmer_id,
        name=name,
        crop=crop,
        farm_area=farm_area,
        soil_type=soil_type,
        growth_stage=growth_stage,
        predicted_water_demand=predicted_demand,
        minimum_water_requirement=min_water,
        maximum_water_requirement=max_water,
        preferred_start_time=preferred_start,
        preferred_end_time=preferred_end,
        urgency=urgency,
        crop_sensitivity=crop_sensitivity,
        flexibility=flexibility,
        utility_weights=utility_weights,
    )

    logger.info(
        "Built FarmerAgent: id=%s crop=%s stage=%s demand=%.1fm3 "
        "[min=%.1f max=%.1f] urgency=%.2f flex=%.2f",
        farmer_id, crop, growth_stage, predicted_demand,
        min_water, max_water, urgency, flexibility,
    )
    return agent, prediction


def build_agents(
    farmers_data: List[Dict[str, Any]],
    predictor: "WaterDemandPredictor",  # type: ignore[name-defined]
    utility_weights: Optional[UtilityWeights] = None,
) -> List[Tuple[FarmerAgent, "PredictionResult"]]:  # type: ignore[name-defined]
    """
    Build a list of FarmerAgents from a list of farmer data dicts.

    Parameters
    ----------
    farmers_data : list of dict
        Each dict is a raw farmer features row.
    predictor : WaterDemandPredictor
        Initialised Phase 2 predictor.
    utility_weights : UtilityWeights, optional
        Shared utility weights for all agents.

    Returns
    -------
    list of (FarmerAgent, PredictionResult) tuples
    """
    results = []
    errors = []
    for i, fdata in enumerate(farmers_data):
        try:
            agent, pred = build_agent(fdata, predictor, utility_weights=utility_weights)
            results.append((agent, pred))
        except Exception as exc:
            fid = fdata.get("farmer_id", f"index_{i}")
            logger.error("Failed to build agent for farmer_id=%s: %s", fid, exc)
            errors.append((fid, str(exc)))

    if errors:
        logger.warning(
            "build_agents: %d/%d agents failed: %s",
            len(errors), len(farmers_data), errors,
        )

    logger.info(
        "build_agents: built %d/%d agents successfully.",
        len(results), len(farmers_data),
    )
    return results


def build_twins(
    farmers_data: List[Dict[str, Any]],
    predictor: "WaterDemandPredictor",  # type: ignore[name-defined]
    utility_weights: Optional[UtilityWeights] = None,
) -> List[Tuple[FarmerAgent, DigitalTwin, "PredictionResult"]]:  # type: ignore[name-defined]
    """
    Build FarmerAgents + DigitalTwins in one call.

    Convenience wrapper that calls build_agents and wraps each agent
    in a DigitalTwin ready for simulation.

    Parameters
    ----------
    farmers_data : list of dict
    predictor : WaterDemandPredictor
    utility_weights : UtilityWeights, optional

    Returns
    -------
    list of (FarmerAgent, DigitalTwin, PredictionResult) tuples
    """
    agent_results = build_agents(farmers_data, predictor, utility_weights=utility_weights)
    triples = []
    for agent, prediction in agent_results:
        twin = DigitalTwin(agent)
        triples.append((agent, twin, prediction))
    logger.info("build_twins: created %d digital twins.", len(triples))
    return triples


def build_agents_from_scenario(
    scenario_type: str,
    n_farmers: int,
    predictor: "WaterDemandPredictor",  # type: ignore[name-defined]
    seed: int = 42,
    utility_weights: Optional[UtilityWeights] = None,
) -> List[Tuple[FarmerAgent, DigitalTwin, "PredictionResult"]]:  # type: ignore[name-defined]
    """
    Build agents + twins from a generated synthetic scenario.

    This is the primary integration point demonstrating the
    Farmer Data -> WaterDemandPredictor -> FarmerAgent pipeline.

    Parameters
    ----------
    scenario_type : str
        One of the 8 SCENARIO_TYPES from SyntheticDataGenerator.
    n_farmers : int
        Number of farmers in the scenario (2–20).
    predictor : WaterDemandPredictor
        Initialised Phase 2 predictor.
    seed : int
        Random seed for the data generator.
    utility_weights : UtilityWeights, optional

    Returns
    -------
    list of (FarmerAgent, DigitalTwin, PredictionResult) tuples
    """
    from app.ml.data_generator import SyntheticDataGenerator

    gen = SyntheticDataGenerator(seed=seed)
    scenario_df = gen.generate_scenario(scenario_type=scenario_type, n_farmers=n_farmers)
    farmers_data = scenario_df.to_dict(orient="records")

    logger.info(
        "build_agents_from_scenario: scenario=%s n_farmers=%d seed=%d",
        scenario_type, n_farmers, seed,
    )
    return build_twins(farmers_data, predictor, utility_weights=utility_weights)


def build_agent_from_artifacts(
    farmer_data: Dict[str, Any],
    model_dir: Path,
    model_name: str = "XGBoost",
    utility_weights: Optional[UtilityWeights] = None,
) -> Tuple[FarmerAgent, DigitalTwin]:
    """
    Build a FarmerAgent + DigitalTwin by loading model artifacts from disk.

    Convenience wrapper for use in scripts and API endpoints.

    Parameters
    ----------
    farmer_data : dict
        Raw farmer features.
    model_dir : Path
        Directory containing trained model .joblib files.
    model_name : str
        'XGBoost' (default) or 'RandomForest'.
    utility_weights : UtilityWeights, optional

    Returns
    -------
    (FarmerAgent, DigitalTwin)
    """
    from app.ml.predictor import WaterDemandPredictor

    predictor = WaterDemandPredictor.from_artifacts(model_dir, model_name=model_name)
    agent, _ = build_agent(farmer_data, predictor, utility_weights=utility_weights)
    twin = DigitalTwin(agent)
    return agent, twin
