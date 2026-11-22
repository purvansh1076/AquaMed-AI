"""
AquaMedi AI - Shadow evaluation state definitions (Phase I).
"""
from __future__ import annotations

from enum import Enum


class ShadowState(str, Enum):
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    EVALUATED = "EVALUATED"
    REJECTED_INPUT = "REJECTED_INPUT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    SHADOW_COMPLETE = "SHADOW_COMPLETE"
    NEEDS_REVIEW = "NEEDS_REVIEW"
