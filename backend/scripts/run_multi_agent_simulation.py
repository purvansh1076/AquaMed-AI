"""
AquaMedi AI - Phase D reproducible multi-agent simulation benchmark.
"""
from __future__ import annotations

import json
import time

from app.config import get_settings
from app.agents.agent_factory import build_agents_from_scenario
from app.ml.predictor import WaterDemandPredictor
from app.negotiation.negotiation_engine import NegotiationEngine
from app.allocation.fairness import fairness_summary


def main():
    settings = get_settings()
    predictor = WaterDemandPredictor.from_artifacts(settings.model_dir_path, model_name="XGBoost")
    results = []
    for scenario in ("normal_water", "moderate_shortage", "severe_shortage"):
        triples = build_agents_from_scenario(scenario, 5, predictor, seed=42)
        agents = [t[0] for t in triples]
        available = None
        from app.ml.data_generator import SyntheticDataGenerator
        gen = SyntheticDataGenerator(seed=42)
        sdf = gen.generate_scenario(scenario, n_farmers=5)
        available = float(sdf["total_available_water_m3"].iloc[0])

        t0 = time.perf_counter()
        engine = NegotiationEngine(agents=agents, available_water_m3=available, scenario_id=scenario)
        agreement = engine.run()
        elapsed = (time.perf_counter() - t0) * 1000

        demands = [a.predicted_water_demand for a in agents]
        allocs = [agreement.final_allocation.get(a.farmer_id, 0.0) for a in agents]
        fs = fairness_summary(allocs, demands, sum(allocs), sum(demands))
        report = {
            "scenario": scenario,
            "n_farmers": len(agents),
            "available_water_m3": available,
            "total_demand_m3": round(sum(demands), 2),
            "final_allocation": {k: round(v, 2) for k, v in agreement.final_allocation.items()},
            "rounds": agreement.negotiation_rounds,
            "status": agreement.agreement_status.value,
            "termination_reason": agreement.termination_reason,
            "fairness": fs,
            "runtime_ms": round(elapsed, 2),
            "convergence": engine.convergence_report(),
        }
        results.append(report)

    out = settings.model_dir_path / "phase_d_simulation_results.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
