"""
AquaMediAI — Scenario Orchestration Service
=============================================

Phase 8: Coordinates the full AquaMediAI pipeline by calling existing
Phase 1–7 implementations.  This service is a THIN ORCHESTRATION LAYER.

Design Principles
-----------------
1. READ-ONLY with respect to computational logic.  ScenarioService never
   implements ML, LP, negotiation, or explainability algorithms.
2. It CALLS existing components: WaterDemandPredictor, build_agents_from_scenario,
   ConflictDetector, WaterAllocator, NegotiationEngine, ExplanationService.
3. Error handling is localised here — API routes receive clean results or
   structured errors.
4. The service is STATELESS — all state lives in the caller (FastAPI app).

DISCLAIMER: All data processed through this service is SYNTHETIC.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from app.agents.agent_factory import build_agents_from_scenario
from app.allocation.lp_allocator import WaterAllocator
from app.conflict.detector import ConflictDetector
from app.explainability.explanation_service import ExplanationService
from app.ml.predictor import PredictionResult, WaterDemandPredictor
from app.negotiation.negotiation_engine import NegotiationEngine
from app.negotiation.negotiation_types import NegotiationConfig

logger = logging.getLogger(__name__)

# ─── Singleton predictor and explainer (loaded once per process) ───────────────

_predictor_cache: Dict[str, WaterDemandPredictor] = {}
_explainer_cache: Dict[str, Any] = {}


def _get_predictor(model_name: str = "XGBoost") -> WaterDemandPredictor:
    """Return a cached WaterDemandPredictor, loading from artifacts if needed."""
    if model_name not in _predictor_cache:
        from app.config import get_settings
        model_dir = get_settings().model_dir_path
        if not (model_dir / "encoders.joblib").exists():
            raise FileNotFoundError(
                f"Model artifacts not found in {model_dir}. "
                "Run 'python scripts/train_models.py' first."
            )
        _predictor_cache[model_name] = WaterDemandPredictor.from_artifacts(
            model_dir, model_name=model_name
        )
        logger.info("Loaded predictor: %s from %s", model_name, model_dir)
    return _predictor_cache[model_name]


def _get_explainer(model_name: str = "XGBoost") -> Optional[Any]:
    """Return a cached WaterDemandExplainer, loading from artifacts if needed."""
    if model_name not in _explainer_cache:
        from app.config import get_settings
        model_dir = get_settings().model_dir_path
        if not (model_dir / "encoders.joblib").exists():
            return None
        try:
            from app.ml.data_generator import SyntheticDataGenerator
            from app.ml.explainer import WaterDemandExplainer

            gen = SyntheticDataGenerator(seed=42)
            bg_df = gen.generate_dataset(n_samples=200)
            _explainer_cache[model_name] = WaterDemandExplainer.from_artifacts(
                model_dir=model_dir,
                train_df=bg_df,
                model_name=model_name,
                n_background=50,
            )
            logger.info("Loaded SHAP explainer: %s from %s", model_name, model_dir)
        except Exception as exc:
            logger.warning("Failed to initialize SHAP explainer for %s: %s", model_name, exc)
            return None
    return _explainer_cache.get(model_name)


def clear_predictor_cache() -> None:
    """Clear the cached predictor and explainer (for testing)."""
    _predictor_cache.clear()
    _explainer_cache.clear()


# ─── ScenarioService ─────────────────────────────────────────────────────────

class ScenarioService:
    """
    Orchestrates the full AquaMediAI pipeline.

    Each method calls existing Phase 1–7 implementations directly.
    No computational logic is duplicated.

    Usage
    -----
        service = ScenarioService()
        result = service.run_scenario(request)
    """

    def __init__(self) -> None:
        self._explanation_service = ExplanationService()

    # ─── Full pipeline ────────────────────────────────────────────────────────

    def run_scenario(
        self,
        scenario_type: str,
        n_farmers: int = 4,
        seed: int = 42,
        model_name: str = "XGBoost",
        available_water_override_m3: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full AquaMediAI pipeline.

        Steps
        -----
        1. Generate synthetic scenario data.
        2. Run ML predictions + build FarmerAgents.
        3. Detect conflicts.
        4. Run LP allocation.
        5. Run negotiation.
        6. Generate explanations.
        7. Return structured result.

        Parameters
        ----------
        scenario_type : str
        n_farmers : int
        seed : int
        model_name : str
        available_water_override_m3 : float or None

        Returns
        -------
        dict with all pipeline results.
        """
        scenario_id = f"scenario_{uuid.uuid4().hex[:12]}"

        # ── Step 1: Load predictor and generate scenario ──────────────────────
        predictor = _get_predictor(model_name)
        triples = build_agents_from_scenario(
            scenario_type=scenario_type,
            n_farmers=n_farmers,
            predictor=predictor,
            seed=seed,
        )

        if not triples:
            raise ValueError(
                f"Failed to build agents for scenario_type={scenario_type!r}. "
                "Check that model artifacts exist in data/models/."
            )

        agents = [t[0] for t in triples]
        predictions = [t[2] for t in triples]

        # Determine available water
        first_row = triples[0][2]
        if available_water_override_m3 is not None:
            available_water = available_water_override_m3
        else:
            # Build scenario to get the generated water supply
            from app.ml.data_generator import SyntheticDataGenerator
            gen = SyntheticDataGenerator(seed=seed)
            scenario_df = gen.generate_scenario(
                scenario_type=scenario_type, n_farmers=n_farmers
            )
            available_water = float(scenario_df["total_available_water_m3"].iloc[0])

        total_demand = sum(a.predicted_water_demand for a in agents)

        # ── Step 2: Build prediction response data ────────────────────────────
        prediction_responses = []
        for pred, agent in zip(predictions, agents):
            pred_item = {
                "farmer_id": agent.farmer_id,
                "predicted_water_demand_m3": round(pred.predicted_water_demand_m3, 2),
                "model_name": pred.model_name,
                "model_version": pred.model_version,
                "warning": pred.warning,
                "input_summary": pred.input_summary,
            }
            if getattr(pred, "shadow_agronomic_estimate_m3", None) is not None:
                pred_item["shadow_agronomic_estimate_m3"] = round(pred.shadow_agronomic_estimate_m3, 2)
            else:
                pred_item["shadow_agronomic_estimate_m3"] = None
            pred_item["shadow_comparison"] = getattr(pred, "shadow_comparison", None)

            if getattr(pred, "shadow_candidate_v3_estimate_m3", None) is not None:
                pred_item["shadow_candidate_v3_estimate_m3"] = round(pred.shadow_candidate_v3_estimate_m3, 2)
            else:
                pred_item["shadow_candidate_v3_estimate_m3"] = None
            pred_item["shadow_candidate_v3_comparison"] = getattr(pred, "shadow_candidate_v3_comparison", None)

            prediction_responses.append(pred_item)

        # ── Step 3: Farmer agent data ─────────────────────────────────────────
        farmer_dicts = [a.as_dict() for a in agents]

        # ── Step 4: Conflict detection (Phase 4) ─────────────────────────────
        detector = ConflictDetector(
            agents=agents,
            available_water_m3=available_water,
            scenario_id=scenario_id,
        )
        conflict_report = detector.detect_all()

        # ── Step 5: LP Allocation (Phase 5) ───────────────────────────────────
        allocator = WaterAllocator(
            agents=agents,
            available_water_m3=available_water,
            scenario_id=scenario_id,
        )
        initial_allocation_result = allocator.solve()
        initial_alloc_dict = initial_allocation_result.as_dict()

        # ── Step 6: Negotiation (Phase 6) ─────────────────────────────────────
        negotiation_config = NegotiationConfig()
        engine = NegotiationEngine(
            agents=agents,
            available_water_m3=available_water,
            config=negotiation_config,
            scenario_id=scenario_id,
        )
        agreement = engine.run()

        # Re-run allocation with best allocation from negotiation as final
        # The final_allocation from negotiation is already LP-verified
        final_allocation_result = initial_allocation_result  # use initial as base

        # ── Step 7: Explainability (Phase 7) ──────────────────────────────────
        session = engine.session
        if session is None:
            # Fallback if engine.session was not set
            from app.negotiation.negotiation_types import NegotiationSession
            session = NegotiationSession(
                session_id=agreement.session_id,
                scenario_id=scenario_id,
                farmer_ids=[a.farmer_id for a in agents],
                available_water_m3=available_water,
                initial_allocation={fa.farmer_id: fa.allocated_water_m3 for fa in initial_allocation_result.allocations},
                current_allocation=dict(agreement.final_allocation),
                current_round=agreement.negotiation_rounds,
                max_rounds=negotiation_config.max_rounds,
                status=agreement.agreement_status,
                rounds=[],
                proposals=[],
                concessions=list(agreement.concessions),
                utility_history=[dict(agreement.final_utilities)],
                best_nash_objective=agreement.round_nash_history[-1] if agreement.round_nash_history else 0.0,
                best_allocation=dict(agreement.final_allocation),
                config=negotiation_config,
                agreement=agreement,
            )

        # Get prediction explanations from SHAP or fallback
        prediction_explanations = []
        for pred, agent in zip(predictions, agents):
            pred_exp = self._build_prediction_explanation(pred, agent.farmer_id)
            prediction_explanations.append(pred_exp)

        final_explanation = self._explanation_service.explain_final_decision(
            allocation_result=initial_allocation_result,
            scenario_id=scenario_id,
            prediction_explanations=prediction_explanations,
            conflict_report=conflict_report,
            negotiation_session=session,
        )

        # ── Build structured response ─────────────────────────────────────────
        return self._build_response(
            scenario_id=scenario_id,
            scenario_type=scenario_type,
            n_farmers=n_farmers,
            available_water=available_water,
            total_demand=total_demand,
            prediction_responses=prediction_responses,
            farmer_dicts=farmer_dicts,
            conflict_report=conflict_report,
            initial_allocation_result=initial_allocation_result,
            agreement=agreement,
            final_explanation=final_explanation,
            session=session,
        )

    # ─── Partial pipeline: prediction only ────────────────────────────────────

    def predict_single(
        self,
        farmer_data: Dict[str, Any],
        model_name: str = "XGBoost",
        enable_shadow_mode: Optional[bool] = None,
        enable_candidate_v3_shadow: Optional[bool] = None,
    ) -> PredictionResult:
        """Run a single ML prediction using the existing predictor."""
        predictor = _get_predictor(model_name)
        return predictor.predict_single(
            farmer_data,
            enable_shadow_mode=enable_shadow_mode,
            enable_candidate_v3_shadow=enable_candidate_v3_shadow,
        )

    def predict_batch(
        self,
        farmers_data: List[Dict[str, Any]],
        model_name: str = "XGBoost",
        enable_shadow_mode: Optional[bool] = None,
        enable_candidate_v3_shadow: Optional[bool] = None,
    ) -> List[PredictionResult]:
        """Run batch ML predictions using the existing predictor."""
        predictor = _get_predictor(model_name)
        return [
            predictor.predict_single(
                fd,
                enable_shadow_mode=enable_shadow_mode,
                enable_candidate_v3_shadow=enable_candidate_v3_shadow,
            )
            for fd in farmers_data
        ]

    # ─── Partial pipeline: conflict detection only ────────────────────────────

    def detect_conflicts(
        self,
        scenario_type: str,
        n_farmers: int = 4,
        seed: int = 42,
        model_name: str = "XGBoost",
        available_water_override_m3: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Run data generation → agents → conflict detection."""
        predictor = _get_predictor(model_name)
        triples = build_agents_from_scenario(
            scenario_type=scenario_type,
            n_farmers=n_farmers,
            predictor=predictor,
            seed=seed,
        )
        agents = [t[0] for t in triples]

        if available_water_override_m3 is not None:
            available_water = available_water_override_m3
        else:
            from app.ml.data_generator import SyntheticDataGenerator
            gen = SyntheticDataGenerator(seed=seed)
            scenario_df = gen.generate_scenario(
                scenario_type=scenario_type, n_farmers=n_farmers
            )
            available_water = float(scenario_df["total_available_water_m3"].iloc[0])

        scenario_id = f"conflict_{uuid.uuid4().hex[:12]}"
        detector = ConflictDetector(
            agents=agents,
            available_water_m3=available_water,
            scenario_id=scenario_id,
        )
        report = detector.detect_all()
        return report.as_dict()

    # ─── Partial pipeline: allocation only ────────────────────────────────────

    def run_allocation(
        self,
        scenario_type: str,
        n_farmers: int = 4,
        seed: int = 42,
        model_name: str = "XGBoost",
        available_water_override_m3: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Run data generation → agents → LP allocation."""
        predictor = _get_predictor(model_name)
        triples = build_agents_from_scenario(
            scenario_type=scenario_type,
            n_farmers=n_farmers,
            predictor=predictor,
            seed=seed,
        )
        agents = [t[0] for t in triples]

        if available_water_override_m3 is not None:
            available_water = available_water_override_m3
        else:
            from app.ml.data_generator import SyntheticDataGenerator
            gen = SyntheticDataGenerator(seed=seed)
            scenario_df = gen.generate_scenario(
                scenario_type=scenario_type, n_farmers=n_farmers
            )
            available_water = float(scenario_df["total_available_water_m3"].iloc[0])

        scenario_id = f"alloc_{uuid.uuid4().hex[:12]}"
        allocator = WaterAllocator(
            agents=agents,
            available_water_m3=available_water,
            scenario_id=scenario_id,
        )
        result = allocator.solve()
        return result.as_dict()

    # ─── Partial pipeline: negotiation only ───────────────────────────────────

    def run_negotiation(
        self,
        scenario_type: str,
        n_farmers: int = 4,
        seed: int = 42,
        model_name: str = "XGBoost",
        available_water_override_m3: Optional[float] = None,
        max_rounds: int = 5,
        acceptance_threshold: float = 0.65,
        rejection_threshold: float = 0.35,
    ) -> Dict[str, Any]:
        """Run data generation → agents → negotiation."""
        predictor = _get_predictor(model_name)
        triples = build_agents_from_scenario(
            scenario_type=scenario_type,
            n_farmers=n_farmers,
            predictor=predictor,
            seed=seed,
        )
        agents = [t[0] for t in triples]

        if available_water_override_m3 is not None:
            available_water = available_water_override_m3
        else:
            from app.ml.data_generator import SyntheticDataGenerator
            gen = SyntheticDataGenerator(seed=seed)
            scenario_df = gen.generate_scenario(
                scenario_type=scenario_type, n_farmers=n_farmers
            )
            available_water = float(scenario_df["total_available_water_m3"].iloc[0])

        scenario_id = f"nego_{uuid.uuid4().hex[:12]}"
        config = NegotiationConfig(
            max_rounds=max_rounds,
            acceptance_threshold=acceptance_threshold,
            rejection_threshold=rejection_threshold,
        )
        engine = NegotiationEngine(
            agents=agents,
            available_water_m3=available_water,
            config=config,
            scenario_id=scenario_id,
        )
        agreement = engine.run()
        session = engine.session

        # Build session for full response
        session_data = {
            "session_id": agreement.session_id,
            "scenario_id": scenario_id,
            "n_rounds": agreement.negotiation_rounds,
            "agreement_status": agreement.agreement_status.value,
            "termination_reason": agreement.termination_reason,
            "initial_allocation": dict(session.initial_allocation) if session else {},
            "best_allocation": dict(agreement.final_allocation),
            "rounds": [r.as_dict() for r in session.rounds] if session else [],
            "agreement": agreement.as_dict(),
        }
        return session_data

    # ─── Prediction explanation builder ─────────────────────────────────────

    def _build_prediction_explanation(self, pred, farmer_id: str):
        """
        Build a PredictionExplanation using SHAP when available, falling back safely.
        """
        from app.explainability.prediction_explainer import (
            explain_prediction_from_shap,
            explain_prediction_without_shap,
        )

        try:
            explainer = _get_explainer(pred.model_name)
            if explainer is not None and pred.feature_values:
                from app.ml.feature_engineering import ENGINEERED_FEATURE_COLS
                X_row = np.array(
                    [pred.feature_values[col] for col in ENGINEERED_FEATURE_COLS],
                    dtype=float,
                ).reshape(1, -1)
                shap_exp = explainer.explain_single(
                    X_row=X_row,
                    prediction=pred.predicted_water_demand_m3,
                )
                return explain_prediction_from_shap(
                    shap_explanation=shap_exp,
                    model_version=pred.model_version,
                    farmer_id=farmer_id,
                )
        except Exception as exc:
            logger.warning("SHAP explanation failed for farmer %s: %s", farmer_id, exc)

        return explain_prediction_without_shap(
            predicted_demand_m3=pred.predicted_water_demand_m3,
            model_name=pred.model_name,
            model_version=pred.model_version,
            farmer_id=farmer_id,
            feature_values=pred.feature_values,
        )

    # ─── Response builder ─────────────────────────────────────────────────────

    def _build_response(
        self,
        scenario_id: str,
        scenario_type: str,
        n_farmers: int,
        available_water: float,
        total_demand: float,
        prediction_responses: List[Dict[str, Any]],
        farmer_dicts: List[Dict[str, Any]],
        conflict_report: Any,
        initial_allocation_result: Any,
        agreement: Any,
        final_explanation: Any,
        session: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Assemble the full pipeline response dict."""
        return {
            "scenario_id": scenario_id,
            "status": agreement.agreement_status.value,
            "scenario_type": scenario_type,
            "n_farmers": n_farmers,
            "available_water_m3": round(available_water, 2),
            "total_demand_m3": round(total_demand, 2),
            "predictions": prediction_responses,
            "farmers": farmer_dicts,
            "conflicts": conflict_report.as_dict(),
            "initial_allocation": initial_allocation_result.as_dict(),
            "negotiation": {
                "session_id": agreement.session_id,
                "scenario_id": scenario_id,
                "n_rounds": agreement.negotiation_rounds,
                "agreement_status": agreement.agreement_status.value,
                "termination_reason": agreement.termination_reason,
                "initial_allocation": dict(session.initial_allocation) if session else {},
                "best_allocation": dict(agreement.final_allocation),
                "rounds": [r.as_dict() for r in session.rounds] if session else [],
                "agreement": agreement.as_dict(),
            },
            "final_allocation": initial_allocation_result.as_dict(),
            "explanations": final_explanation.as_dict(),
            "final_decision": {
                "scenario_id": scenario_id,
                "summary": final_explanation.summary,
                "agreement_status": agreement.agreement_status.value,
                "termination_reason": agreement.termination_reason,
                "fairness_score": agreement.fairness_score,
                "water_utilization": agreement.water_utilization,
                "negotiation_rounds": agreement.negotiation_rounds,
                "is_physically_valid": agreement.is_physically_valid,
            },
        }
