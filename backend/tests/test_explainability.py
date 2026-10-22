"""
AquaMediAI - Phase 7 Explainability Tests
==========================================

30 test classes covering all Phase 7 requirements.

Tests use ACTUAL Phase 2-6 classes and fixtures.
No Phase 2-6 tests are modified.

DISCLAIMER: All data is SYNTHETIC.
"""

from __future__ import annotations

import math
import uuid
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest

from app.allocation.allocation_types import (
    AllocationResult,
    ConstraintVerificationResult,
    FarmerAllocation,
    SolverStatus,
)
from app.conflict.conflict_types import (
    ConflictReport,
    ConflictType,
    ScenarioConflictReport,
    Severity,
)
from app.negotiation.negotiation_types import (
    Agreement,
    AgreementStatus,
    Concession,
    FarmerResponse,
    NegotiationConfig,
    NegotiationRound,
    NegotiationSession,
    Proposal,
    ResponseType,
    make_agreement_id,
    make_concession_id,
    make_proposal_id,
    make_session_id,
)
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


# ======================================================
# Shared fixture helpers
# ======================================================

def _make_verification(
    is_valid=True, total_water_ok=True, non_negative_ok=True,
    maximum_ok=True, no_nan_ok=True, all_farmers_present=True, violations=None,
):
    return ConstraintVerificationResult(
        is_valid=is_valid, total_water_ok=total_water_ok,
        non_negative_ok=non_negative_ok, maximum_ok=maximum_ok,
        no_nan_ok=no_nan_ok, all_farmers_present=all_farmers_present,
        violations=violations or [],
    )


def _make_fa(fid="F001", alloc=3200.0, demand=3600.0, mn=2000.0, mx=4500.0,
             urgency=0.5, sens=0.7, stage="flowering", crop="wheat", cs="satisfied"):
    return FarmerAllocation(
        farmer_id=fid, allocated_water_m3=alloc, predicted_demand_m3=demand,
        minimum_requirement_m3=mn, maximum_requirement_m3=mx,
        urgency=urgency, crop_sensitivity=sens, growth_stage=stage, crop=crop,
        constraint_status=cs,
    )


def _make_ar(farmers=None, avail=10000.0, demand=11000.0, mn=6000.0,
             alloc=9800.0, fair=0.88, status=SolverStatus.OPTIMAL, feasible=True):
    if farmers is None:
        farmers = [_make_fa("F001", 4800.0, 5500.0, 3000.0, 7000.0),
                   _make_fa("F002", 5000.0, 5500.0, 3000.0, 7000.0)]
    return AllocationResult(
        solver_status=status, objective_value=0.95,
        available_water_m3=avail, total_demand_m3=demand,
        total_minimum_requirement_m3=mn, total_allocated_m3=alloc,
        remaining_water_m3=avail - alloc,
        utilization=min(1.0, alloc / avail) if avail > 0 else 0.0,
        fairness_score=fair, minimum_requirements_feasible=feasible,
        allocations=farmers, verification=_make_verification(),
        scenario_id="test_scenario", allocation_method="lp_optimal",
    )


def _make_shap_expl(pred=4000.0, base=3500.0, model="XGBoost", shap_vals=None):
    from app.ml.explainer import FeatureContribution, SHAPExplanation
    sv = shap_vals or [120.0, -80.0, 60.0, -30.0, 10.0]
    names = ["temperature_celsius", "soil_moisture", "etc_mm_per_day", "rainfall_mm", "kc_value"]
    contribs = []
    for i, (name, s) in enumerate(zip(names, sv)):
        impact = "positive" if s > 1e-9 else ("negative" if s < -1e-9 else "neutral")
        contribs.append(FeatureContribution(feature=name, raw_value=float(i*10+20),
                                            shap_value=s, impact=impact, abs_shap=abs(s)))
    contribs.sort(key=lambda c: c.abs_shap, reverse=True)
    top_pos = [c for c in contribs if c.impact == "positive"][:5]
    top_neg = [c for c in contribs if c.impact == "negative"][:5]
    return SHAPExplanation(prediction=pred, base_value=base, features=contribs,
                           top_positive=top_pos, top_negative=top_neg, model_name=model)


def _make_concession_obj(fid="F001", rnd=1, prev=5500.0, new=4800.0, flex=0.6, urg=0.4):
    amt = prev - new
    space = prev - 2000.0
    ratio = amt / space if space > 0 else 0.0
    return Concession(concession_id=make_concession_id(fid, rnd), farmer_id=fid,
                      round_number=rnd, previous_ask_m3=prev, new_ask_m3=new,
                      concession_amount_m3=amt, concession_ratio=ratio,
                      flexibility_factor=flex, urgency_factor=urg, reason="Test")


def _make_fr(fid="F001", alloc=4000.0, util=0.70, batna=0.45,
             rt=ResponseType.ACCEPT, batna_prot=False, rnd=1):
    return FarmerResponse(farmer_id=fid, allocation_m3=alloc, utility=util,
                          batna_utility=batna, surplus=util-batna, response_type=rt,
                          is_batna_protected=batna_prot,
                          satisfaction_ratio=min(1.0, alloc/5500.0),
                          minimum_met=(alloc >= 2000.0), reason="Test", round_number=rnd)


def _make_nr(rnd=1, alloc=None, responses=None, concessions=None):
    if alloc is None:
        alloc = {"F001": 4500.0, "F002": 4500.0}
    if responses is None:
        responses = [_make_fr("F001", 4500.0, 0.72, 0.45, ResponseType.ACCEPT),
                     _make_fr("F002", 4500.0, 0.48, 0.43, ResponseType.REQUEST_CHANGE)]
    utils = {r.farmer_id: r.utility for r in responses}
    batnas = {r.farmer_id: r.batna_utility for r in responses}
    surps = {r.farmer_id: r.surplus for r in responses}
    na = sum(1 for r in responses if r.response_type == ResponseType.ACCEPT)
    nrc = sum(1 for r in responses if r.response_type == ResponseType.REQUEST_CHANGE)
    nrj = sum(1 for r in responses if r.response_type == ResponseType.REJECT)
    return NegotiationRound(round_number=rnd, current_allocation=alloc,
                            farmer_responses=responses, utilities=utils,
                            batna_utilities=batnas, surpluses=surps,
                            nash_objective=-5.2, fairness_score=0.88,
                            n_accepting=na, n_requesting_change=nrc, n_rejecting=nrj,
                            proposed_changes={"F002": 4800.0},
                            accepted_concessions=concessions or [],
                            solver_status="optimal", explanation="Test round")


def _make_agreement_obj(alloc=None, utils=None, batnas=None, status=AgreementStatus.AGREED):
    if alloc is None:
        alloc = {"F001": 4800.0, "F002": 5000.0}
    if utils is None:
        utils = {"F001": 0.72, "F002": 0.68}
    if batnas is None:
        batnas = {"F001": 0.45, "F002": 0.43}
    surplus = {fid: utils[fid] - batnas[fid] for fid in alloc}
    return Agreement(agreement_id=make_agreement_id(), session_id=make_session_id(),
                     final_allocation=alloc, participating_farmers=list(alloc.keys()),
                     final_utilities=utils, batna_utilities=batnas, final_surplus=surplus,
                     concessions=[], fairness_score=0.88, water_utilization=0.98,
                     negotiation_rounds=2, agreement_status=status,
                     termination_reason="All farmers accepted.",
                     round_fairness_history=[0.85, 0.88], round_nash_history=[-6.1, -5.2],
                     is_physically_valid=True)


def _make_session(fids=None, rounds=None, concessions=None, agreement=None):
    if fids is None:
        fids = ["F001", "F002"]
    if rounds is None:
        rounds = [_make_nr()]
    if concessions is None:
        concessions = [_make_concession_obj()]
    if agreement is None:
        agreement = _make_agreement_obj()
    init = {"F001": 4500.0, "F002": 4500.0}
    best = {"F001": 4800.0, "F002": 5000.0}
    return NegotiationSession(session_id=make_session_id(), scenario_id="test_scenario",
                              farmer_ids=fids, available_water_m3=10000.0,
                              initial_allocation=init, current_allocation=best,
                              current_round=len(rounds), max_rounds=5,
                              status=AgreementStatus.AGREED, rounds=rounds,
                              proposals=[], concessions=concessions,
                              utility_history=[{"F001": 0.72, "F002": 0.68}],
                              best_nash_objective=-5.2, best_allocation=best,
                              config=NegotiationConfig(), agreement=agreement)


def _make_cr(ctype=ConflictType.RESOURCE_SHORTAGE, sev=Severity.HIGH,
             fids=None, avail=8000.0, demand=11000.0, mn=6000.0, score=0.35):
    if fids is None:
        fids = ["F001", "F002"]
    gap = max(0.0, demand - avail)
    mgap = max(0.0, mn - avail)
    return ConflictReport(conflict_type=ctype, severity=sev, severity_score=score,
                          involved_farmer_ids=fids, total_demand_m3=demand,
                          total_minimum_requirement_m3=mn, available_water_m3=avail,
                          resource_gap_m3=gap, minimum_requirement_gap_m3=mgap,
                          explanation="Test conflict", evidence={"test": "data"},
                          scenario_id="test_scenario")


def _make_scr(conflicts=None):
    if conflicts is None:
        conflicts = [_make_cr()]
    return ScenarioConflictReport(scenario_id="test_scenario", n_farmers=2,
                                  total_demand_m3=11000.0, available_water_m3=8000.0,
                                  total_minimum_requirement_m3=6000.0, conflicts=conflicts)

# ============================================================
# Tests 1-5: Prediction / SHAP
# ============================================================

class TestPredictionExplanation:
    def test_explain_prediction_from_shap_basic(self):
        shap_expl = _make_shap_expl(4000.0, 3500.0)
        result = explain_prediction_from_shap(shap_expl, farmer_id="F001")
        assert isinstance(result, PredictionExplanation)
        assert result.predicted_demand_m3 == 4000.0
        assert result.base_value == 3500.0
        assert result.farmer_id == "F001"
        assert result.shap_available is True

    def test_prediction_without_shap(self):
        result = explain_prediction_without_shap(3200.0, "RandomForest", "1.0", "F002")
        assert result.shap_available is False
        assert result.predicted_demand_m3 == 3200.0
        assert "F002" in result.summary


class TestSHAPIntegration:
    def test_all_features_included(self):
        shap_expl = _make_shap_expl()
        result = explain_prediction_from_shap(shap_expl)
        assert len(result.all_features) == len(shap_expl.features)

    def test_base_value_matches(self):
        shap_expl = _make_shap_expl(base=3750.5)
        result = explain_prediction_from_shap(shap_expl)
        assert result.base_value == 3750.5

    def test_prediction_matches(self):
        shap_expl = _make_shap_expl(pred=5123.4)
        result = explain_prediction_from_shap(shap_expl)
        assert result.predicted_demand_m3 == 5123.4


class TestPositiveSHAPContribution:
    def test_positive_shap_direction(self):
        shap_expl = _make_shap_expl(shap_vals=[100.0, -50.0, 30.0, -20.0, 5.0])
        result = explain_prediction_from_shap(shap_expl)
        positive = [f for f in result.all_features if f.shap_value > 1e-9]
        for feat in positive:
            assert feat.direction == ContributionDirection.INCREASES

    def test_positive_in_positive_contributors(self):
        shap_expl = _make_shap_expl(shap_vals=[100.0, -50.0, 30.0, -20.0, 0.0])
        result = explain_prediction_from_shap(shap_expl)
        pos_count = sum(1 for f in result.all_features if f.direction == ContributionDirection.INCREASES)
        assert len(result.positive_contributors) == pos_count

    def test_positive_rationale_contains_increased(self):
        shap_expl = _make_shap_expl(shap_vals=[100.0, -50.0, 0.0, 0.0, 0.0])
        result = explain_prediction_from_shap(shap_expl)
        pos = [f for f in result.all_features if f.direction == ContributionDirection.INCREASES]
        assert len(pos) > 0
        assert "increased" in pos[0].rationale


class TestNegativeSHAPContribution:
    def test_negative_shap_direction(self):
        shap_expl = _make_shap_expl(shap_vals=[100.0, -80.0, 30.0, -20.0, 0.0])
        result = explain_prediction_from_shap(shap_expl)
        negative = [f for f in result.all_features if f.shap_value < -1e-9]
        for feat in negative:
            assert feat.direction == ContributionDirection.DECREASES

    def test_negative_in_negative_contributors(self):
        shap_expl = _make_shap_expl(shap_vals=[100.0, -50.0, 30.0, -20.0, 0.0])
        result = explain_prediction_from_shap(shap_expl)
        neg_count = sum(1 for f in result.all_features if f.direction == ContributionDirection.DECREASES)
        assert len(result.negative_contributors) == neg_count

    def test_negative_rationale_contains_decreased(self):
        shap_expl = _make_shap_expl(shap_vals=[-100.0, 50.0, 0.0, 0.0, 0.0])
        result = explain_prediction_from_shap(shap_expl)
        neg = [f for f in result.all_features if f.direction == ContributionDirection.DECREASES]
        assert len(neg) > 0
        assert "decreased" in neg[0].rationale


class TestFeatureRanking:
    def test_features_ranked_by_abs_shap(self):
        shap_expl = _make_shap_expl(shap_vals=[50.0, -200.0, 10.0, -80.0, 5.0])
        result = explain_prediction_from_shap(shap_expl)
        for i in range(len(result.all_features) - 1):
            assert result.all_features[i].abs_shap >= result.all_features[i+1].abs_shap

    def test_rank_field_values(self):
        shap_expl = _make_shap_expl()
        result = explain_prediction_from_shap(shap_expl)
        for i, feat in enumerate(result.all_features, start=1):
            assert feat.rank == i

    def test_top_contributors_highest_abs_shap(self):
        shap_expl = _make_shap_expl(shap_vals=[50.0, -200.0, 10.0, -80.0, 5.0])
        result = explain_prediction_from_shap(shap_expl, top_n=2)
        top2 = sorted([abs(v) for v in [50.0, -200.0, 10.0, -80.0, 5.0]], reverse=True)[:2]
        res_abs = sorted([c.abs_shap for c in result.top_contributors], reverse=True)
        assert res_abs == pytest.approx(top2, abs=1e-6)


# ============================================================
# Tests 6-11: Allocation / Reason Codes
# ============================================================

class TestAllocationExplanation:
    def test_produces_one_per_farmer(self):
        farmers = [_make_fa("F001"), _make_fa("F002"), _make_fa("F003")]
        ar = _make_ar(farmers=farmers)
        exps = explain_allocation(ar)
        assert len(exps) == 3

    def test_values_match_actual(self):
        fa = _make_fa("F001", alloc=3200.0, demand=3600.0)
        ar = _make_ar(farmers=[fa])
        e = explain_allocation(ar)[0]
        assert e.allocated_m3 == pytest.approx(3200.0)
        assert e.predicted_demand_m3 == pytest.approx(3600.0)
        assert e.unmet_demand_m3 == pytest.approx(400.0)

    def test_does_not_modify_allocation_result(self):
        fa = _make_fa("F001", alloc=3200.0)
        ar = _make_ar(farmers=[fa])
        orig = ar.allocations[0].allocated_water_m3
        explain_allocation(ar)
        assert ar.allocations[0].allocated_water_m3 == orig


class TestReasonCodeGeneration:
    def test_no_phantom_reason_codes(self):
        fa = _make_fa("F001", alloc=5500.0, demand=5500.0, mn=2000.0, mx=6000.0, urgency=0.3, sens=0.5)
        ar = _make_ar(farmers=[fa], avail=20000.0, demand=5500.0, alloc=5500.0, fair=1.0)
        exps = explain_allocation(ar)
        e = exps[0]
        assert ReasonCode.RESOURCE_SHORTAGE not in e.reason_codes
        assert ReasonCode.UNMET_DEMAND not in e.reason_codes
        assert ReasonCode.FULL_DEMAND_SATISFACTION in e.reason_codes

    def test_reason_codes_deterministic(self):
        fa = _make_fa("F001", urgency=0.8)
        ar = _make_ar(farmers=[fa])
        codes1 = explain_allocation(ar)[0].reason_codes
        codes2 = explain_allocation(ar)[0].reason_codes
        assert sorted(r.value for r in codes1) == sorted(r.value for r in codes2)


class TestResourceShortageReasonCode:
    def test_emitted_when_demand_exceeds_available(self):
        fa = _make_fa("F001", alloc=3500.0, demand=5500.0)
        ar = _make_ar(farmers=[fa], avail=8000.0, demand=11000.0, alloc=8000.0)
        assert ReasonCode.RESOURCE_SHORTAGE in explain_allocation(ar)[0].reason_codes

    def test_not_emitted_when_supply_adequate(self):
        fa = _make_fa("F001", alloc=5500.0, demand=5500.0)
        ar = _make_ar(farmers=[fa], avail=10000.0, demand=5500.0, alloc=5500.0)
        assert ReasonCode.RESOURCE_SHORTAGE not in explain_allocation(ar)[0].reason_codes


class TestWaterSurplusReasonCode:
    def test_emitted_when_surplus_and_satisfied(self):
        fa = _make_fa("F001", alloc=5500.0, demand=5500.0, mn=2000.0, mx=7000.0)
        ar = _make_ar(farmers=[fa], avail=20000.0, demand=5500.0, alloc=5500.0)
        assert ReasonCode.WATER_SURPLUS in explain_allocation(ar)[0].reason_codes

    def test_not_emitted_when_demand_unmet(self):
        fa = _make_fa("F001", alloc=3000.0, demand=5500.0)
        ar = _make_ar(farmers=[fa], avail=8000.0, demand=11000.0, alloc=3000.0)
        assert ReasonCode.WATER_SURPLUS not in explain_allocation(ar)[0].reason_codes


class TestHighUrgencyReasonCode:
    def test_emitted_above_threshold(self):
        fa = _make_fa("F001", urgency=0.85)
        ar = _make_ar(farmers=[fa])
        assert ReasonCode.HIGH_URGENCY in explain_allocation(ar)[0].reason_codes

    def test_not_emitted_below_threshold(self):
        fa = _make_fa("F001", urgency=0.50)
        ar = _make_ar(farmers=[fa])
        assert ReasonCode.HIGH_URGENCY not in explain_allocation(ar)[0].reason_codes


class TestHighCropSensitivityReasonCode:
    def test_emitted_above_threshold(self):
        fa = _make_fa("F001", sens=0.9)
        ar = _make_ar(farmers=[fa])
        assert ReasonCode.HIGH_CROP_SENSITIVITY in explain_allocation(ar)[0].reason_codes

    def test_not_emitted_below_threshold(self):
        fa = _make_fa("F001", sens=0.6)
        ar = _make_ar(farmers=[fa])
        assert ReasonCode.HIGH_CROP_SENSITIVITY not in explain_allocation(ar)[0].reason_codes


# ============================================================
# Tests 12-14: Constraints / Fairness
# ============================================================

class TestConstraintExplanation:
    def test_global_constraints_include_h3(self):
        ar = _make_ar()
        constraints = build_global_constraint_explanations(ar)
        names = [c.constraint_name for c in constraints]
        assert any("H3" in n or "TOTAL_WATER_LIMIT" in n for n in names)

    def test_h3_satisfied_within_limit(self):
        ar = _make_ar(avail=10000.0, alloc=9800.0)
        constraints = build_global_constraint_explanations(ar)
        h3 = next(c for c in constraints if "H3" in c.constraint_name)
        assert h3.status == ConstraintStatus.SATISFIED

    def test_constraint_values_match_actual(self):
        ar = _make_ar(avail=10000.0, alloc=9800.0)
        constraints = build_global_constraint_explanations(ar)
        h3 = next(c for c in constraints if "H3" in c.constraint_name)
        assert h3.actual_value == pytest.approx(ar.total_allocated_m3)
        assert h3.limit == pytest.approx(ar.available_water_m3)


class TestSoftMinimumConstraint:
    def test_s1_relaxed_when_infeasible(self):
        ar = _make_ar(avail=5000.0, mn=8000.0, feasible=False)
        constraints = build_global_constraint_explanations(ar)
        s1 = next(c for c in constraints if "S1" in c.constraint_name or "MINIMUM_REQUIREMENTS_FEASIBILITY" in c.constraint_name)
        assert s1.status == ConstraintStatus.RELAXED

    def test_s1_satisfied_when_feasible(self):
        ar = _make_ar(avail=10000.0, mn=6000.0, feasible=True)
        constraints = build_global_constraint_explanations(ar)
        s1 = next(c for c in constraints if "S1" in c.constraint_name or "MINIMUM_REQUIREMENTS_FEASIBILITY" in c.constraint_name)
        assert s1.status == ConstraintStatus.SATISFIED

    def test_s1_is_soft(self):
        ar = _make_ar()
        constraints = build_global_constraint_explanations(ar)
        s1 = next(c for c in constraints if "S1" in c.constraint_name or "MINIMUM_REQUIREMENTS_FEASIBILITY" in c.constraint_name)
        assert s1.is_hard is False


class TestFairnessExplanation:
    def test_fairness_score_matches(self):
        ar = _make_ar(fair=0.87)
        expl = explain_fairness(ar)
        assert expl.fairness_score == pytest.approx(0.87)

    def test_note_distinguishes_measurement_from_causation(self):
        ar = _make_ar()
        expl = explain_fairness(ar)
        assert "measured" in expl.note.lower() or "not" in expl.note.lower() or "did not include" in expl.note.lower()

    def test_n_farmers_matches(self):
        farmers = [_make_fa(f"F00{i}") for i in range(4)]
        ar = _make_ar(farmers=farmers)
        assert explain_fairness(ar).n_farmers == 4

    def test_satisfaction_ratios_present(self):
        farmers = [_make_fa("F001", alloc=3200.0, demand=3600.0),
                   _make_fa("F002", alloc=4000.0, demand=4000.0)]
        ar = _make_ar(farmers=farmers)
        expl = explain_fairness(ar)
        assert "F001" in expl.satisfaction_ratios
        assert expl.satisfaction_ratios["F002"] == pytest.approx(1.0)


# ============================================================
# Tests 15-16: Conflict / Negotiation Round
# ============================================================

class TestConflictExplanation:
    def test_resource_shortage_uses_actual_values(self):
        cr = _make_cr(ctype=ConflictType.RESOURCE_SHORTAGE, avail=8000.0, demand=11000.0)
        entry = explain_conflict(cr)
        assert entry.conflict_type == "resource_shortage"
        assert entry.available_water_m3 == pytest.approx(8000.0)
        assert entry.total_demand_m3 == pytest.approx(11000.0)

    def test_explain_all_conflicts_none_input(self):
        assert explain_all_conflicts(None) == []

    def test_explain_all_conflicts_multiple(self):
        conflicts = [_make_cr(ConflictType.RESOURCE_SHORTAGE),
                     _make_cr(ConflictType.IRRIGATION_WINDOW_OVERLAP)]
        scr = _make_scr(conflicts)
        entries = explain_all_conflicts(scr)
        assert len(entries) == 2


class TestNegotiationRoundExplanation:
    def test_correct_round_number(self):
        rnd = _make_nr(rnd=3)
        expl = explain_negotiation_round(rnd)
        assert expl.round_number == 3

    def test_allocation_matches_actual(self):
        alloc = {"F001": 4200.0, "F002": 4800.0}
        rnd = _make_nr(alloc=alloc)
        expl = explain_negotiation_round(rnd)
        assert expl.current_allocation["F001"] == pytest.approx(4200.0)

    def test_response_counts_match(self):
        responses = [_make_fr("F001", rt=ResponseType.ACCEPT),
                     _make_fr("F002", rt=ResponseType.REQUEST_CHANGE)]
        rnd = _make_nr(responses=responses)
        expl = explain_negotiation_round(rnd)
        assert expl.n_accepting == 1
        assert expl.n_requesting_change == 1
        assert expl.n_rejecting == 0

    def test_nash_objective_matches(self):
        rnd = _make_nr()
        expl = explain_negotiation_round(rnd)
        assert expl.nash_objective == pytest.approx(rnd.nash_objective)


# ============================================================
# Tests 17-19: BATNA / Concession / Nash
# ============================================================

class TestBATNAExplanation:
    def test_utility_matches(self):
        expl = explain_batna("F001", 0.42, 2000.0)
        assert expl.batna_utility == pytest.approx(0.42)
        assert expl.batna_allocation_m3 == pytest.approx(2000.0)

    def test_is_above_batna_true(self):
        expl = explain_batna("F001", 0.42, 2000.0, 0.68, 4000.0)
        assert expl.is_above_batna is True
        assert expl.surplus == pytest.approx(0.68 - 0.42)

    def test_is_above_batna_false(self):
        expl = explain_batna("F002", 0.60, 3000.0, 0.50, 2500.0)
        assert expl.is_above_batna is False

    def test_neutral_language(self):
        expl = explain_batna("F001", 0.42, 2000.0, 0.68, 4000.0)
        for word in ["happy", "sad", "angry", "frustrated"]:
            assert word not in expl.rationale.lower()

    def test_without_negotiated_data(self):
        expl = explain_batna("F001", 0.42, 2000.0)
        assert expl.negotiated_utility is None
        assert expl.is_above_batna is None
        assert expl.surplus is None


class TestConcessionExplanation:
    def test_fields_match_actual(self):
        c = _make_concession_obj("F001", 1, 5500.0, 4800.0, 0.6, 0.4)
        expl = explain_concession(c)
        assert expl.farmer_id == "F001"
        assert expl.previous_ask_m3 == pytest.approx(5500.0)
        assert expl.new_ask_m3 == pytest.approx(4800.0)
        assert expl.concession_amount_m3 == pytest.approx(700.0)
        assert expl.flexibility_factor == pytest.approx(0.6)
        assert expl.urgency_factor == pytest.approx(0.4)

    def test_rationale_mentions_concession(self):
        c = _make_concession_obj()
        expl = explain_concession(c)
        assert "flexibility" in expl.rationale.lower() or "concession" in expl.rationale.lower()


class TestNashObjectiveExplanation:
    def test_formula_contains_log(self):
        agr = _make_agreement_obj()
        expl = explain_nash_objective(agr)
        assert "log" in expl.formula.lower()

    def test_called_nash_bargaining_inspired(self):
        agr = _make_agreement_obj()
        expl = explain_nash_objective(agr)
        assert "inspired" in expl.disclaimer.lower()
        assert "not a mathematically complete" in expl.disclaimer.lower()

    def test_trajectory_matches_history(self):
        agr = _make_agreement_obj()
        expl = explain_nash_objective(agr)
        assert expl.trajectory == pytest.approx(agr.round_nash_history)

    def test_final_value_matches_last_round(self):
        agr = _make_agreement_obj()
        expl = explain_nash_objective(agr)
        assert expl.final_value == pytest.approx(agr.round_nash_history[-1])


# ============================================================
# Test 20: Final agreement explanation
# ============================================================

class TestFinalAgreementExplanation:
    def test_final_allocation_matches_agreement(self):
        session = _make_session()
        expl = explain_negotiation_session(session)
        agr = session.agreement
        assert expl.final_allocation["F001"] == pytest.approx(agr.final_allocation["F001"])

    def test_agreement_status_present(self):
        session = _make_session()
        expl = explain_negotiation_session(session)
        assert expl.agreement_status == "AGREED"

    def test_termination_reason_present(self):
        session = _make_session()
        expl = explain_negotiation_session(session)
        assert expl.termination_reason != ""


# ============================================================
# Test 21: Deterministic output
# ============================================================

class TestDeterministicOutput:
    def test_prediction_deterministic(self):
        shap_expl = _make_shap_expl()
        r1 = explain_prediction_from_shap(shap_expl, farmer_id="F001")
        r2 = explain_prediction_from_shap(shap_expl, farmer_id="F001")
        assert r1.summary == r2.summary
        for f1, f2 in zip(r1.all_features, r2.all_features):
            assert f1.shap_value == f2.shap_value
            assert f1.direction == f2.direction

    def test_allocation_deterministic(self):
        ar = _make_ar()
        e1 = explain_allocation(ar)
        e2 = explain_allocation(ar)
        for a1, a2 in zip(e1, e2):
            assert a1.rationale == a2.rationale

    def test_concession_deterministic(self):
        c = _make_concession_obj()
        e1 = explain_concession(c)
        e2 = explain_concession(c)
        assert e1.rationale == e2.rationale


# ============================================================
# Test 22: Missing optional data
# ============================================================

class TestMissingOptionalData:
    def test_without_negotiation(self):
        service = ExplanationService()
        final = service.explain_final_decision(_make_ar(), "test", negotiation_session=None)
        assert isinstance(final, FinalDecisionExplanation)
        assert final.negotiation_explanation is None

    def test_without_conflict_report(self):
        service = ExplanationService()
        final = service.explain_final_decision(_make_ar(), "test", conflict_report=None)
        assert final.conflict_explanations == []

    def test_without_prediction_explanations(self):
        service = ExplanationService()
        final = service.explain_final_decision(_make_ar(), "test")
        assert final.prediction_explanations == []

    def test_batna_without_negotiated_data(self):
        expl = explain_batna("F001", 0.42, 2000.0, None, None)
        assert expl.is_above_batna is None
        assert expl.surplus is None
        assert "No negotiated" in expl.rationale


# ============================================================
# Test 23: Invalid input
# ============================================================

class TestInvalidInput:
    def test_prediction_from_shap_none_raises(self):
        with pytest.raises(ValueError):
            explain_prediction_from_shap(None)

    def test_session_none_raises(self):
        with pytest.raises(ValueError):
            explain_negotiation_session(None)

    def test_final_decision_none_allocation_raises(self):
        service = ExplanationService()
        with pytest.raises((ValueError, AttributeError)):
            service.explain_final_decision(allocation_result=None, scenario_id="test")

    def test_empty_farmers(self):
        ar = _make_ar(farmers=[])
        assert explain_allocation(ar) == []


# ============================================================
# Test 24: No fabricated numerical values
# ============================================================

class TestNoFabricatedNumericalValues:
    def test_allocation_values_from_actual(self):
        fa = _make_fa("F001", alloc=2731.5, demand=3814.2, urgency=0.63, sens=0.71)
        ar = _make_ar(farmers=[fa])
        e = explain_allocation(ar)[0]
        assert e.allocated_m3 == pytest.approx(fa.allocated_water_m3)
        assert e.predicted_demand_m3 == pytest.approx(fa.predicted_demand_m3)
        assert e.urgency == pytest.approx(fa.urgency)
        assert e.crop_sensitivity == pytest.approx(fa.crop_sensitivity)

    def test_fairness_from_actual(self):
        ar = _make_ar(fair=0.7312)
        expl = explain_fairness(ar)
        assert expl.fairness_score == pytest.approx(ar.fairness_score)

    def test_concession_from_actual(self):
        c = _make_concession_obj("F001", 2, 6100.0, 5400.0, 0.7, 0.3)
        expl = explain_concession(c)
        assert expl.previous_ask_m3 == pytest.approx(c.previous_ask_m3)
        assert expl.new_ask_m3 == pytest.approx(c.new_ask_m3)
        assert expl.flexibility_factor == pytest.approx(c.flexibility_factor)


# ============================================================
# Test 25: Phase 2 integration
# ============================================================

class TestPhase2Integration:
    def test_shap_values_preserved(self):
        shap_expl = _make_shap_expl(shap_vals=[80.0, -40.0, 20.0, -10.0, 0.0])
        result = explain_prediction_from_shap(shap_expl)
        by_feat = {fc.feature: fc.shap_value for fc in shap_expl.features}
        for fe in result.all_features:
            assert fe.shap_value == pytest.approx(by_feat[fe.feature])

    def test_model_name_preserved(self):
        shap_expl = _make_shap_expl(model="RandomForest")
        result = explain_prediction_from_shap(shap_expl)
        assert result.model_name == "RandomForest"


# ============================================================
# Test 26: Phase 4 integration
# ============================================================

class TestPhase4Integration:
    def test_conflict_id_preserved(self):
        cr = _make_cr()
        entry = explain_conflict(cr)
        assert entry.conflict_id == cr.conflict_id

    def test_evidence_preserved(self):
        cr = _make_cr()
        cr.evidence = {"available": 8000.0, "demand": 11000.0}
        entry = explain_conflict(cr)
        assert entry.evidence == cr.evidence

    def test_all_conflict_types_explained(self):
        conflicts = [_make_cr(ConflictType.RESOURCE_SHORTAGE),
                     _make_cr(ConflictType.IRRIGATION_WINDOW_OVERLAP),
                     _make_cr(ConflictType.HIGH_CROP_STRESS)]
        scr = _make_scr(conflicts)
        entries = explain_all_conflicts(scr)
        types = [e.conflict_type for e in entries]
        assert "resource_shortage" in types
        assert "irrigation_window_overlap" in types
        assert "high_crop_stress" in types


# ============================================================
# Test 27: Phase 5 integration
# ============================================================

class TestPhase5Integration:
    def test_solver_status_in_summary(self):
        ar = _make_ar(status=SolverStatus.RELAXED)
        service = ExplanationService()
        final = service.explain_final_decision(ar, "test")
        assert "relaxed" in final.summary.lower() or "RELAXED" in final.summary

    def test_violations_in_unresolved_issues(self):
        verif = _make_verification(is_valid=False, total_water_ok=False,
                                    violations=["Total allocated exceeds available water by 500m3"])
        farmers = [_make_fa("F001")]
        ar = AllocationResult(
            solver_status=SolverStatus.OPTIMAL, objective_value=0.8,
            available_water_m3=5000.0, total_demand_m3=6000.0,
            total_minimum_requirement_m3=3000.0, total_allocated_m3=5500.0,
            remaining_water_m3=-500.0, utilization=1.0, fairness_score=0.85,
            minimum_requirements_feasible=True, allocations=farmers,
            verification=verif, scenario_id="test",
        )
        service = ExplanationService()
        final = service.explain_final_decision(ar, "test")
        assert len(final.unresolved_issues) > 0


# ============================================================
# Test 28: Phase 6 integration
# ============================================================

class TestPhase6Integration:
    def test_round_count_matches_session(self):
        rounds = [_make_nr(rnd=i) for i in range(1, 4)]
        session = _make_session(rounds=rounds)
        expl = explain_negotiation_session(session)
        assert expl.n_rounds == 3
        assert len(expl.round_explanations) == 3

    def test_all_concessions_explained(self):
        concessions = [_make_concession_obj("F001", 1), _make_concession_obj("F002", 1)]
        session = _make_session(concessions=concessions)
        expl = explain_negotiation_session(session)
        assert len(expl.concession_explanations) == 2

    def test_farmer_ids_match_session(self):
        session = _make_session(fids=["FA", "FB", "FC"])
        expl = explain_negotiation_session(session)
        assert sorted(expl.farmer_ids) == sorted(["FA", "FB", "FC"])


# ============================================================
# Test 29: Read-only
# ============================================================

class TestExplainabilityReadOnly:
    def test_shap_not_modified(self):
        shap_expl = _make_shap_expl(pred=4000.0, base=3500.0)
        orig_pred = shap_expl.prediction
        orig_base = shap_expl.base_value
        explain_prediction_from_shap(shap_expl)
        assert shap_expl.prediction == orig_pred
        assert shap_expl.base_value == orig_base

    def test_allocation_result_not_modified(self):
        ar = _make_ar()
        orig_alloc = ar.total_allocated_m3
        orig_fair = ar.fairness_score
        explain_allocation(ar)
        explain_fairness(ar)
        assert ar.total_allocated_m3 == orig_alloc
        assert ar.fairness_score == orig_fair

    def test_session_not_modified(self):
        session = _make_session()
        orig_status = session.status
        orig_rounds = len(session.rounds)
        explain_negotiation_session(session)
        assert session.status == orig_status
        assert len(session.rounds) == orig_rounds

    def test_concession_not_modified(self):
        c = _make_concession_obj()
        orig_amt = c.concession_amount_m3
        orig_fid = c.farmer_id
        explain_concession(c)
        assert c.concession_amount_m3 == orig_amt
        assert c.farmer_id == orig_fid


# ============================================================
# Test 30: Full final decision explanation
# ============================================================

class TestFullFinalDecisionExplanation:
    def test_full_pipeline_structure(self):
        service = ExplanationService()
        ar = _make_ar()
        scr = _make_scr()
        session = _make_session()
        final = service.explain_final_decision(
            allocation_result=ar, scenario_id="scenario_final",
            conflict_report=scr, negotiation_session=session,
        )
        assert isinstance(final, FinalDecisionExplanation)
        assert final.scenario_id == "scenario_final"
        assert final.summary != ""
        assert len(final.allocation_explanations) > 0
        assert len(final.conflict_explanations) > 0
        assert final.fairness_explanation is not None
        assert len(final.constraint_explanations) > 0
        assert final.negotiation_explanation is not None

    def test_full_explanation_serializable(self):
        service = ExplanationService()
        ar = _make_ar()
        session = _make_session()
        final = service.explain_final_decision(ar, "test", negotiation_session=session)
        d = final.as_dict()
        assert isinstance(d, dict)
        assert "scenario_id" in d
        assert "allocation_explanations" in d
        assert "negotiation_explanation" in d

    def test_reason_codes_aggregated(self):
        fa1 = _make_fa("F001", urgency=0.85)
        fa2 = _make_fa("F002", urgency=0.3)
        ar = _make_ar(farmers=[fa1, fa2])
        service = ExplanationService()
        final = service.explain_final_decision(ar, "test")
        assert ReasonCode.HIGH_URGENCY in final.all_reason_codes

    def test_counterfactual_baseline_passthrough(self):
        service = ExplanationService()
        ar = _make_ar()
        baseline = {"available_water_m3": 12000.0, "note": "counterfactual"}
        final = service.explain_final_decision(ar, "test", counterfactual_baseline=baseline)
        assert final.counterfactual_baseline == baseline

    def test_data_disclaimer_present(self):
        service = ExplanationService()
        ar = _make_ar()
        final = service.explain_final_decision(ar, "test")
        assert "SYNTHETIC" in final.data_disclaimer or "synthetic" in final.data_disclaimer.lower()


# ============================================================
# Audit Tests (Phase 7 Validation Check)
# ============================================================

class TestGLOPAllocationDescription:
    """Audit Test 1 -- GLOP allocation described as LP optimisation."""

    def test_lp_optimal_rationale_mentions_glop_or_lp(self):
        """lp_optimal allocation rationale references the LP optimization method."""
        fa = _make_fa("F001", alloc=4800.0, demand=5500.0)
        ar = _make_ar(farmers=[fa])
        ar.allocation_method = "lp_optimal"
        exps = explain_allocation(ar)
        rationale = exps[0].rationale.lower()
        assert "lp" in rationale or "glop" in rationale or "optim" in rationale

    def test_lp_relaxed_rationale_mentions_penalty(self):
        """lp_relaxed allocation rationale mentions penalty or relaxed constraints."""
        fa = _make_fa("F001", alloc=1500.0, demand=5500.0, mn=2000.0, cs="minimum_relaxed")
        ar = _make_ar(farmers=[fa], avail=5000.0, mn=8000.0, feasible=False)
        ar.allocation_method = "lp_relaxed"
        exps = explain_allocation(ar)
        rationale = exps[0].rationale.lower()
        assert "penalty" in rationale or "relaxed" in rationale or "lp" in rationale

    def test_h3_constraint_mentions_lp_method(self):
        """H3 global constraint explanation references the allocation method."""
        ar = _make_ar()
        ar.allocation_method = "lp_optimal"
        constraints = build_global_constraint_explanations(ar)
        h3 = next(c for c in constraints if "H3" in c.constraint_name)
        assert "lp" in h3.rationale.lower() or "optim" in h3.rationale.lower() or "glop" in h3.rationale.lower()


class TestProportionalFallbackOnlyWhenActual:
    """Audit Test 2 -- proportional fallback language only when allocation_method confirms it."""

    def test_no_proportional_language_for_lp_optimal(self):
        """lp_optimal result does NOT mention 'proportional' in rationale."""
        fa = _make_fa("F001", alloc=3500.0, demand=5500.0)
        ar = _make_ar(farmers=[fa], avail=8000.0, demand=11000.0, alloc=8000.0)
        ar.allocation_method = "lp_optimal"
        exps = explain_allocation(ar)
        # Must not suggest proportional distribution for an LP result
        assert "proportional" not in exps[0].rationale.lower()

    def test_proportional_language_appears_for_fallback(self):
        """proportional_fallback result includes 'proportional' in rationale."""
        fa = _make_fa("F001", alloc=3636.0, demand=5500.0)
        ar = _make_ar(farmers=[fa], avail=8000.0, demand=11000.0, alloc=8000.0)
        ar.allocation_method = "proportional_fallback"
        exps = explain_allocation(ar)
        assert "proportional" in exps[0].rationale.lower()

    def test_h3_constraint_no_proportional_for_lp(self):
        """H3 constraint explanation for lp_optimal does not say 'proportional'."""
        ar = _make_ar()
        ar.allocation_method = "lp_optimal"
        constraints = build_global_constraint_explanations(ar)
        h3 = next(c for c in constraints if "H3" in c.constraint_name)
        assert "proportional" not in h3.rationale.lower()


class TestReasonCodeThresholdDocumentation:
    """Audit Test 3 -- reason code thresholds match and document their source."""

    def test_high_urgency_threshold_is_0_70(self):
        """HIGH_URGENCY fires at urgency > 0.70 (Phase 4 constant)."""
        from app.explainability.allocation_explainer import _URGENCY_HIGH_THRESHOLD
        assert _URGENCY_HIGH_THRESHOLD == pytest.approx(0.70)

    def test_high_crop_sensitivity_threshold_is_0_70(self):
        """HIGH_CROP_SENSITIVITY fires at crop_sensitivity > 0.70 (Phase 4 constant)."""
        from app.explainability.allocation_explainer import _CROP_SENSITIVITY_HIGH_THRESHOLD
        assert _CROP_SENSITIVITY_HIGH_THRESHOLD == pytest.approx(0.70)

    def test_urgency_rationale_states_threshold_is_not_optimizer_cutoff(self):
        """Urgency rationale states urgency is a continuous LP weight, not a cutoff."""
        fa = _make_fa("F001", urgency=0.85, alloc=4800.0, demand=5500.0)
        ar = _make_ar(farmers=[fa])
        ar.allocation_method = "lp_optimal"
        exps = explain_allocation(ar)
        rationale = exps[0].rationale.lower()
        # Must mention LP objective / weight
        assert "objective" in rationale or "weight" in rationale or "lp" in rationale

    def test_crop_sensitivity_rationale_states_lp_role(self):
        """Crop sensitivity rationale states it is a continuous LP objective weight."""
        fa = _make_fa("F001", sens=0.9, alloc=4800.0, demand=5500.0)
        ar = _make_ar(farmers=[fa])
        ar.allocation_method = "lp_optimal"
        exps = explain_allocation(ar)
        rationale = exps[0].rationale.lower()
        assert "objective" in rationale or "weight" in rationale or "lp" in rationale

    def test_high_urgency_threshold_boundary(self):
        """HIGH_URGENCY NOT emitted at exactly 0.70 (threshold is >)."""
        fa = _make_fa("F001", urgency=0.70)
        ar = _make_ar(farmers=[fa])
        exps = explain_allocation(ar)
        # 0.70 is NOT > 0.70, so HIGH_URGENCY should not be present
        assert ReasonCode.HIGH_URGENCY not in exps[0].reason_codes

    def test_high_urgency_emitted_just_above_boundary(self):
        """HIGH_URGENCY emitted at urgency = 0.71 (strictly above 0.70)."""
        fa = _make_fa("F001", urgency=0.71)
        ar = _make_ar(farmers=[fa])
        exps = explain_allocation(ar)
        assert ReasonCode.HIGH_URGENCY in exps[0].reason_codes


class TestNoCausalityViolations:
    """Audit Test 4 -- no unsupported causal claims in rationale text."""

    def test_fairness_not_described_as_cause(self):
        """Fairness explanation note clearly states it is a measurement, not a cause."""
        ar = _make_ar(fair=0.88)
        expl = explain_fairness(ar)
        note = expl.note.lower()
        # Must say measurement / measured / not include / did not
        assert ("measured" in note or "not include" in note
                or "did not" in note or "post-hoc" in note)

    def test_fairness_rationale_uses_word_measured(self):
        """Fairness rationale uses 'measured' to describe the Jain's index."""
        ar = _make_ar(fair=0.88)
        expl = explain_fairness(ar)
        assert "measured" in expl.rationale.lower()

    def test_urgency_not_described_as_sole_cause(self):
        """Urgency rationale for LP result does not say 'caused' or 'determined'."""
        fa = _make_fa("F001", urgency=0.85)
        ar = _make_ar(farmers=[fa])
        ar.allocation_method = "lp_optimal"
        exps = explain_allocation(ar)
        rationale = exps[0].rationale.lower()
        # Should not claim direct causation without LP evidence
        assert "caused this allocation" not in rationale
        assert "determined the allocation" not in rationale

    def test_fairness_adjustment_reason_code_not_emitted(self):
        """FAIRNESS_ADJUSTMENT reason code is never emitted by explain_allocation."""
        # Use a scenario where all farmers are perfectly satisfied
        fa = _make_fa("F001", alloc=5500.0, demand=5500.0)
        ar = _make_ar(farmers=[fa], avail=20000.0, demand=5500.0, alloc=5500.0, fair=1.0)
        exps = explain_allocation(ar)
        for e in exps:
            assert ReasonCode.FAIRNESS_ADJUSTMENT not in e.reason_codes

    def test_s1_rationale_distinguishes_hard_vs_penalty(self):
        """S1 rationale clearly states whether it was hard or penalty based."""
        # Feasible case: S1 was hard constraint
        fa_feasible = _make_fa("F001", alloc=4800.0, demand=5500.0, mn=2000.0)
        ar_feasible = _make_ar(farmers=[fa_feasible], feasible=True)
        exps_f = explain_allocation(ar_feasible)
        s1_f = next(c for c in exps_f[0].constraint_explanations if "S1" in c.constraint_name)
        # Must mention hard/constraint/enforced
        assert ("hard" in s1_f.rationale.lower() or
                "lower bound" in s1_f.rationale.lower() or
                "met" in s1_f.rationale.lower() or
                "satisfied" in s1_f.rationale.lower())

        # Infeasible case: S1 was penalty term
        fa_relax = _make_fa("F001", alloc=1500.0, demand=5500.0, mn=2000.0, cs="minimum_relaxed")
        ar_relax = _make_ar(farmers=[fa_relax], avail=5000.0, mn=8000.0, feasible=False)
        exps_r = explain_allocation(ar_relax)
        s1_r = next(c for c in exps_r[0].constraint_explanations if "S1" in c.constraint_name)
        assert "penalty" in s1_r.rationale.lower()


class TestExplanationDoesNotModifyResult:
    """Audit Test 5 -- explanation does not modify the original computational result."""

    def test_allocation_method_unchanged_after_explanation(self):
        """AllocationResult.allocation_method is unchanged after explain_allocation."""
        fa = _make_fa("F001")
        ar = _make_ar(farmers=[fa])
        ar.allocation_method = "lp_optimal"
        explain_allocation(ar)
        assert ar.allocation_method == "lp_optimal"

    def test_allocations_list_unchanged_after_explanation(self):
        """AllocationResult.allocations list is unchanged after explain_allocation."""
        fa = _make_fa("F001", alloc=4800.0, demand=5500.0)
        ar = _make_ar(farmers=[fa])
        orig_len = len(ar.allocations)
        orig_alloc = ar.allocations[0].allocated_water_m3
        explain_allocation(ar)
        assert len(ar.allocations) == orig_len
        assert ar.allocations[0].allocated_water_m3 == orig_alloc

    def test_fairness_score_unchanged_after_fairness_explanation(self):
        """AllocationResult.fairness_score unchanged after explain_fairness."""
        ar = _make_ar(fair=0.8132)
        explain_fairness(ar)
        assert ar.fairness_score == pytest.approx(0.8132)

    def test_global_constraints_unchanged_after_constraint_explanation(self):
        """AllocationResult fields unchanged after build_global_constraint_explanations."""
        ar = _make_ar(avail=10000.0, alloc=9800.0)
        orig_avail = ar.available_water_m3
        orig_alloc = ar.total_allocated_m3
        build_global_constraint_explanations(ar)
        assert ar.available_water_m3 == orig_avail
        assert ar.total_allocated_m3 == orig_alloc

    def test_conflict_report_unchanged_after_explain_conflict(self):
        """ConflictReport fields unchanged after explain_conflict."""
        cr = _make_cr(avail=8000.0, demand=11000.0)
        orig_avail = cr.available_water_m3
        orig_demand = cr.total_demand_m3
        explain_conflict(cr)
        assert cr.available_water_m3 == orig_avail
        assert cr.total_demand_m3 == orig_demand
