"""
AquaMedi AI - Phase C allocation strategy comparison (read-only).
Compares equal, proportional, priority-based and LP allocations.
"""
from __future__ import annotations

import json

from app.config import get_settings
from app.agents.agent_factory import build_agents_from_scenario
from app.ml.predictor import WaterDemandPredictor
from app.allocation.lp_allocator import WaterAllocator
from app.allocation.fairness import fairness_summary


def equal_allocation(agents, available):
    n = len(agents)
    if n == 0:
        return [0.0] * n
    share = available / n
    return [min(share, a.maximum_water_requirement) for a in agents]


def proportional_allocation(agents, available):
    total_demand = sum(a.predicted_water_demand for a in agents)
    if total_demand <= 0:
        return [0.0] * len(agents)
    raw = []
    for a in agents:
        alloc = available * (a.predicted_water_demand / total_demand)
        alloc = min(alloc, a.maximum_water_requirement)
        raw.append(max(0.0, alloc))
    return raw


def priority_allocation(agents, available):
    order = sorted(range(len(agents)), key=lambda i: agents[i].urgency * agents[i].crop_sensitivity, reverse=True)
    alloc = [0.0] * len(agents)
    remaining = available
    for i in order:
        if remaining <= 0:
            break
        give = min(agents[i].maximum_water_requirement, remaining)
        alloc[i] = give
        remaining -= give
    return alloc


def main():
    settings = get_settings()
    predictor = WaterDemandPredictor.from_artifacts(settings.model_dir_path, model_name="XGBoost")
    results = {}
    for scenario in ("normal_water", "moderate_shortage", "severe_shortage"):
        triples = build_agents_from_scenario(scenario, 5, predictor, seed=42)
        agents = [t[0] for t in triples]
        available = float(sum(a.predicted_water_demand for a in agents))  # placeholder, override below
        # Recover available water from scenario generator by regenerating metadata
        from app.ml.data_generator import SyntheticDataGenerator
        gen = SyntheticDataGenerator(seed=42)
        sdf = gen.generate_scenario(scenario, n_farmers=5)
        available = float(sdf["total_available_water_m3"].iloc[0])
        demands = [a.predicted_water_demand for a in agents]

        allocator = WaterAllocator(agents=agents, available_water_m3=available, scenario_id=scenario)
        lp_result = allocator.solve()
        lp_alloc = [fa.allocated_water_m3 for fa in lp_result.allocations]

        strategies = {
            "equal": equal_allocation(agents, available),
            "proportional": proportional_allocation(agents, available),
            "priority": priority_allocation(agents, available),
            "lp": lp_alloc,
        }

        strat_results = {}
        for name, alloc in strategies.items():
            fs = fairness_summary(alloc, demands, sum(alloc), sum(demands))
            strat_results[name] = {
                "total_allocated": round(sum(alloc), 2),
                "fairness": fs,
            }
        results[scenario] = {"available_water_m3": available, "strategies": strat_results}

    out = settings.model_dir_path / "allocation_strategy_comparison_phase_c.json"
    with open(out, "w", encoding="utf-8") as f:
        import json
        json.dump(results, f, indent=2)
    print("saved", out)


if __name__ == "__main__":
    main()
