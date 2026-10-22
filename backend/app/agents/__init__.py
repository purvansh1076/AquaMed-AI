"""
AquaMediAI — Agents Package
=============================

Phase 3: Farmer Digital Agents

Exports
-------
FarmerAgent        — deterministic computational farmer agent
FarmerPreferences  — structured preference model
UtilityWeights     — configurable utility function weights
BATNA              — Best Alternative To a Negotiated Agreement
DigitalTwin        — mutable simulation state per farmer
NegotiationState   — state machine enum
ConcessionRecord   — concession event record
build_agent        — factory: single agent from raw data + predictor
build_agents       — factory: batch agent building
build_twins        — factory: agents + digital twins
build_agents_from_scenario — factory: from synthetic scenario
build_agent_from_artifacts — factory: load model from disk + build agent

DISCLAIMER: All data in this system is SYNTHETIC.
"""

from app.agents.farmer_agent import (
    BATNA,
    CROP_SENSITIVITY_TABLE,
    STAGE_CRITICALITY,
    VALID_CROPS,
    VALID_GROWTH_STAGES,
    VALID_SOILS,
    FarmerAgent,
    FarmerPreferences,
    UtilityWeights,
)
from app.agents.digital_twin import (
    ConcessionRecord,
    DigitalTwin,
    NegotiationState,
)
from app.agents.agent_factory import (
    build_agent,
    build_agent_from_artifacts,
    build_agents,
    build_agents_from_scenario,
    build_twins,
)

__all__ = [
    # farmer_agent
    "FarmerAgent",
    "FarmerPreferences",
    "UtilityWeights",
    "BATNA",
    "VALID_CROPS",
    "VALID_SOILS",
    "VALID_GROWTH_STAGES",
    "STAGE_CRITICALITY",
    "CROP_SENSITIVITY_TABLE",
    # digital_twin
    "DigitalTwin",
    "NegotiationState",
    "ConcessionRecord",
    # agent_factory
    "build_agent",
    "build_agents",
    "build_twins",
    "build_agents_from_scenario",
    "build_agent_from_artifacts",
]
