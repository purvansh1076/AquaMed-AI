from app.allocation.lp_allocator import WaterAllocator
from app.agents.agent_factory import build_agents_from_scenario
from app.ml.predictor import WaterDemandPredictor
from app.config import get_settings


def test_maxmin_feasible():
    settings = get_settings()
    predictor = WaterDemandPredictor.from_artifacts(settings.model_dir_path, model_name="XGBoost")
    triples = build_agents_from_scenario("moderate_shortage", 4, predictor, seed=42)
    agents = [t[0] for t in triples]
    from app.ml.data_generator import SyntheticDataGenerator
    gen = SyntheticDataGenerator(seed=42)
    sdf = gen.generate_scenario("moderate_shortage", n_farmers=4)
    available = float(sdf["total_available_water_m3"].iloc[0])
    allocator = WaterAllocator(agents=agents, available_water_m3=available, scenario_id="t")
    res = allocator.solve_fairness_aware()
    assert res.verification.is_valid
    assert res.total_allocated_m3 <= available + 1e-3
    assert res.fairness_score >= 0
