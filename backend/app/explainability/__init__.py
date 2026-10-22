"""
AquaMediAI - Explainability Package (Phase 7)
===============================================

Provides a unified Explainability Layer that answers:
  1. WHY was this water demand predicted?
  2. WHY did this conflict occur?
  3. WHY was this amount of water allocated?
  4. WHY did a farmer receive/concede water?
  5. WHY did negotiation terminate?
  6. WHY did the final agreement look like this?

The layer is READ-ONLY with respect to all Phase 2-6 outputs.
It never modifies predictions, allocations, or negotiation outcomes.

Public API
----------
Types:
    PredictionExplanation, AllocationExplanation, ConstraintExplanation
    FairnessExplanation, ConflictExplanationEntry, BATNAExplanation
    ConcessionExplanation, NegotiationRoundExplanation, NashObjectiveExplanation
    NegotiationExplanation, FinalDecisionExplanation
    ReasonCode, ContributionDirection, ConstraintStatus

Service:
    ExplanationService -- orchestrates all explanations

Individual explainers (can be used directly):
    explain_prediction_from_shap  -- wraps existing WaterDemandExplainer
    explain_prediction_without_shap
    explain_allocation            -- Phase 5 AllocationResult
    explain_fairness              -- Jain's Fairness
    explain_conflict              -- Phase 4 ConflictReport
    explain_all_conflicts         -- Phase 4 ScenarioConflictReport
    explain_negotiation_round     -- Phase 6 NegotiationRound
    explain_concession            -- Phase 6 Concession
    explain_batna                 -- Phase 3/6 BATNA
    explain_nash_objective        -- Phase 6 Nash-inspired objective
    explain_negotiation_session   -- Phase 6 NegotiationSession
    build_global_constraint_explanations
"""

from app.explainability.explanation_types import (
    AllocationExplanation,
    BATNAExplanation,
    ConcessionExplanation,
    ConflictExplanationEntry,
    ConstraintExplanation,
    ConstraintStatus,
    ContributionDirection,
    FairnessExplanation,
    FeatureContributionExplanation,
    FinalDecisionExplanation,
    NashObjectiveExplanation,
    NegotiationExplanation,
    NegotiationRoundExplanation,
    PredictionExplanation,
    ReasonCode,
)
from app.explainability.prediction_explainer import (
    explain_prediction_from_shap,
    explain_prediction_without_shap,
)
from app.explainability.allocation_explainer import (
    build_global_constraint_explanations,
    explain_all_conflicts,
    explain_allocation,
    explain_conflict,
    explain_fairness,
)
from app.explainability.negotiation_explainer import (
    explain_batna,
    explain_concession,
    explain_nash_objective,
    explain_negotiation_round,
    explain_negotiation_session,
)
from app.explainability.explanation_service import ExplanationService

__all__ = [
    # Types
    "AllocationExplanation",
    "BATNAExplanation",
    "ConcessionExplanation",
    "ConflictExplanationEntry",
    "ConstraintExplanation",
    "ConstraintStatus",
    "ContributionDirection",
    "FairnessExplanation",
    "FeatureContributionExplanation",
    "FinalDecisionExplanation",
    "NashObjectiveExplanation",
    "NegotiationExplanation",
    "NegotiationRoundExplanation",
    "PredictionExplanation",
    "ReasonCode",
    # Prediction
    "explain_prediction_from_shap",
    "explain_prediction_without_shap",
    # Allocation
    "build_global_constraint_explanations",
    "explain_all_conflicts",
    "explain_allocation",
    "explain_conflict",
    "explain_fairness",
    # Negotiation
    "explain_batna",
    "explain_concession",
    "explain_nash_objective",
    "explain_negotiation_round",
    "explain_negotiation_session",
    # Service
    "ExplanationService",
]
