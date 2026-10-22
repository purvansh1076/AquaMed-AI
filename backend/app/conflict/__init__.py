"""
AquaMediAI — Conflict Detection Package
=========================================

Phase 4: Conflict Detection Engine

Exports
-------
ConflictType          — enum of 5 conflict types
Severity              — enum (LOW / MEDIUM / HIGH / CRITICAL)
severity_from_ratio   — map ratio [0,1] to Severity
WindowInterval        — time window model with overlap detection
ConflictReport        — single conflict report
ScenarioConflictReport — aggregate scenario-level report
ConflictDetector      — main detection engine
ConflictScoringWeights — configurable scoring weights

DISCLAIMER: All conflict analysis is performed on SYNTHETIC data.
"""

from app.conflict.conflict_types import (
    ConflictReport,
    ConflictType,
    ScenarioConflictReport,
    Severity,
    WindowInterval,
    severity_from_ratio,
)
from app.conflict.detector import (
    ConflictDetector,
    ConflictScoringWeights,
    DEFAULT_CANAL_CAPACITY_M3_PER_HOUR,
    HIGH_STRESS_URGENCY_THRESHOLD,
    HIGH_STRESS_SENSITIVITY_THRESHOLD,
)

__all__ = [
    # conflict_types
    "ConflictType",
    "Severity",
    "severity_from_ratio",
    "WindowInterval",
    "ConflictReport",
    "ScenarioConflictReport",
    # detector
    "ConflictDetector",
    "ConflictScoringWeights",
    "DEFAULT_CANAL_CAPACITY_M3_PER_HOUR",
    "HIGH_STRESS_URGENCY_THRESHOLD",
    "HIGH_STRESS_SENSITIVITY_THRESHOLD",
]
