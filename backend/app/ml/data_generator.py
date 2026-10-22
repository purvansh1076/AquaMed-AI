"""
AquaMediAI — Synthetic Agronomic Data Generator
================================================

IMPORTANT DISCLAIMER
--------------------
All data produced by this module is **completely synthetic**.
No real farmer records, real water usage data, or real negotiation transcripts
are used or implied. The parameter ranges are grounded in published
agronomic literature (FAO-56, Allen et al. 1998) to ensure academic credibility,
but the individual records are algorithmically generated.

Agronomic Grounding
-------------------
- Crop water requirements (ETc) derived from:
    Allen, R.G. et al. (1998). *Crop evapotranspiration — FAO Irrigation and
    Drainage Paper No. 56*. FAO, Rome.
- Reference evapotranspiration (ET₀) ranges for semi-arid Indian conditions:
    3–8 mm/day (kharif), 2–5 mm/day (rabi).
- Crop coefficients (Kc) by growth stage taken from FAO-56 Table 12.
- Soil water-holding capacity (WHC) ranges from Doorenbos & Pruitt (1977).

Scenario Types
--------------
The generator produces 8 clearly labelled scenario types:
    1. normal_water          — supply >= demand
    2. moderate_shortage     — supply ~70-80% of demand
    3. severe_shortage       — supply ~40-60% of demand
    4. sudden_rainfall       — extra supply mid-season
    5. canal_reduction       — canal capacity reduced 30-50%
    6. simultaneous_demand   — multiple farmers peak simultaneously
    7. high_urgency_farmer   — one farmer at critical stress stage
    8. flexible_farmer       — one farmer with wide schedule flexibility

Usage
-----
    from app.ml.data_generator import SyntheticDataGenerator

    gen = SyntheticDataGenerator(seed=42)
    df = gen.generate_dataset(n_samples=2000)
    scenario_df = gen.generate_scenario(scenario_type="severe_shortage", n_farmers=5)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Agronomic Constants ──────────────────────────────────────────────────────
# Source: FAO-56 Table 12 — crop coefficients (Kc) by stage
# Stages: germination, vegetative, flowering, maturity, harvest

KC_TABLE: Dict[str, Dict[str, float]] = {
    "wheat": {
        "germination": 0.40,
        "vegetative": 0.70,
        "flowering":  1.15,
        "maturity":   0.65,
        "harvest":    0.25,
    },
    "rice": {
        "germination": 1.05,
        "vegetative": 1.10,
        "flowering":  1.20,
        "maturity":   1.05,
        "harvest":    0.90,
    },
    "cotton": {
        "germination": 0.45,
        "vegetative": 0.75,
        "flowering":  1.15,
        "maturity":   0.80,
        "harvest":    0.60,
    },
    "sugarcane": {
        "germination": 0.40,
        "vegetative": 0.80,
        "flowering":  1.25,
        "maturity":   0.75,
        "harvest":    0.60,
    },
    "maize": {
        "germination": 0.40,
        "vegetative": 0.80,
        "flowering":  1.15,
        "maturity":   0.70,
        "harvest":    0.50,
    },
    "soybean": {
        "germination": 0.40,
        "vegetative": 0.80,
        "flowering":  1.15,
        "maturity":   0.50,
        "harvest":    0.30,
    },
    "groundnut": {
        "germination": 0.45,
        "vegetative": 0.75,
        "flowering":  1.05,
        "maturity":   0.70,
        "harvest":    0.55,
    },
    "sunflower": {
        "germination": 0.35,
        "vegetative": 0.75,
        "flowering":  1.10,
        "maturity":   0.70,
        "harvest":    0.35,
    },
}

# Soil WHC (mm/m) — plant-available water capacity
# Source: Doorenbos & Pruitt (1977)
SOIL_WHC: Dict[str, Tuple[float, float]] = {
    "clay":   (150.0, 200.0),
    "loam":   (100.0, 150.0),
    "sandy":  (50.0,  100.0),
    "silt":   (120.0, 160.0),
    "clay_loam": (130.0, 170.0),
}

# ET₀ ranges (mm/day) for Indian semi-arid / sub-humid conditions
ET0_RANGE: Dict[str, Tuple[float, float]] = {
    "kharif": (4.0, 8.0),   # June–October, monsoon season
    "rabi":   (2.5, 5.0),   # November–March, cool dry season
    "zaid":   (5.0, 9.0),   # March–June, hot dry season
}

# Growth stage criticality (crop stress sensitivity) — 1.0 = most critical
STAGE_CRITICALITY: Dict[str, float] = {
    "germination": 0.90,
    "vegetative":  0.60,
    "flowering":   1.00,   # Most sensitive — water stress here causes yield loss
    "maturity":    0.50,
    "harvest":     0.20,
}

# Valid scenario type strings
SCENARIO_TYPES: List[str] = [
    "normal_water",
    "moderate_shortage",
    "severe_shortage",
    "sudden_rainfall",
    "canal_reduction",
    "simultaneous_demand",
    "high_urgency_farmer",
    "flexible_farmer",
]

CROPS = list(KC_TABLE.keys())
SOILS = list(SOIL_WHC.keys())
GROWTH_STAGES = ["germination", "vegetative", "flowering", "maturity", "harvest"]
SEASONS = ["kharif", "rabi", "zaid"]


@dataclass
class ScenarioConfig:
    """
    Configuration parameters for a single synthetic scenario.

    All numerical ranges are expressed as multipliers / offsets applied
    to the base agronomic values. This keeps scenarios agronomically
    plausible while varying water-supply pressure.
    """

    scenario_type: str
    # Water supply multiplier relative to total demand
    supply_fraction_range: Tuple[float, float] = (0.95, 1.20)
    # Canal capacity range (m³/hour)
    canal_capacity_range: Tuple[float, float] = (40.0, 80.0)
    # Whether to inject a high-urgency farmer
    inject_urgency_farmer: bool = False
    # Whether to force simultaneous peak demand windows
    force_simultaneous_windows: bool = False
    # Whether to widen one farmer's flexibility window
    inject_flexible_farmer: bool = False
    # Extra rainfall addition (mm)
    rainfall_bonus_mm: float = 0.0
    # Description for human-readable output
    description: str = ""


SCENARIO_CONFIGS: Dict[str, ScenarioConfig] = {
    "normal_water": ScenarioConfig(
        scenario_type="normal_water",
        supply_fraction_range=(1.05, 1.30),
        canal_capacity_range=(50.0, 80.0),
        description="Water supply comfortably exceeds total demand. No significant conflict.",
    ),
    "moderate_shortage": ScenarioConfig(
        scenario_type="moderate_shortage",
        supply_fraction_range=(0.70, 0.85),
        canal_capacity_range=(40.0, 65.0),
        description="Water supply is 70-85% of total demand. Moderate conflict likely.",
    ),
    "severe_shortage": ScenarioConfig(
        scenario_type="severe_shortage",
        supply_fraction_range=(0.40, 0.62),
        canal_capacity_range=(30.0, 50.0),
        description="Critical water scarcity — 40-62% of demand available.",
    ),
    "sudden_rainfall": ScenarioConfig(
        scenario_type="sudden_rainfall",
        supply_fraction_range=(1.10, 1.50),
        canal_capacity_range=(50.0, 80.0),
        rainfall_bonus_mm=25.0,
        description="Unexpected rainfall event increases effective supply mid-season.",
    ),
    "canal_reduction": ScenarioConfig(
        scenario_type="canal_reduction",
        supply_fraction_range=(0.80, 1.00),
        canal_capacity_range=(18.0, 32.0),   # Canal throttled 30-50%
        description="Canal capacity reduced 30-50% due to maintenance or damage.",
    ),
    "simultaneous_demand": ScenarioConfig(
        scenario_type="simultaneous_demand",
        supply_fraction_range=(0.75, 0.95),
        canal_capacity_range=(35.0, 60.0),
        force_simultaneous_windows=True,
        description="Multiple farmers demand irrigation in the same time window.",
    ),
    "high_urgency_farmer": ScenarioConfig(
        scenario_type="high_urgency_farmer",
        supply_fraction_range=(0.70, 0.90),
        canal_capacity_range=(40.0, 65.0),
        inject_urgency_farmer=True,
        description="One farmer's crop is at flowering stage — critical water stress risk.",
    ),
    "flexible_farmer": ScenarioConfig(
        scenario_type="flexible_farmer",
        supply_fraction_range=(0.75, 0.90),
        canal_capacity_range=(40.0, 65.0),
        inject_flexible_farmer=True,
        description="One farmer can accept water in any 8-hour window — aids reallocation.",
    ),
}


class SyntheticDataGenerator:
    """
    Generates synthetic but agronomically grounded datasets for AquaMediAI.

    Parameters
    ----------
    seed : int
        Random seed for reproducibility. Default 42.

    Notes
    -----
    All generated data is synthetic. Parameter distributions are calibrated
    against FAO-56 crop water requirement tables for academic credibility.
    """

    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        logger.info("SyntheticDataGenerator initialised (seed=%d)", seed)

    # ─── Core dataset generation ───────────────────────────────────────────────

    def generate_dataset(
        self,
        n_samples: int = 2000,
        scenario_distribution: Optional[Dict[str, float]] = None,
    ) -> pd.DataFrame:
        """
        Generate the full ML training/evaluation dataset.

        Each row represents one farmer-day observation. The target variable
        is ``water_demand_m3`` — the daily water requirement in cubic metres.

        Parameters
        ----------
        n_samples : int
            Total number of rows to generate.
        scenario_distribution : dict, optional
            Fraction of rows per scenario type. Must sum to 1.0.
            Defaults to equal distribution across all 8 types.

        Returns
        -------
        pd.DataFrame
            Dataset with features and target column ``water_demand_m3``.
            Always includes column ``is_synthetic=True``.
        """
        if scenario_distribution is None:
            # Equal split
            n = len(SCENARIO_TYPES)
            scenario_distribution = {s: 1.0 / n for s in SCENARIO_TYPES}

        if abs(sum(scenario_distribution.values()) - 1.0) > 1e-6:
            raise ValueError("scenario_distribution values must sum to 1.0")

        records: List[pd.DataFrame] = []
        for scenario_type, fraction in scenario_distribution.items():
            n_rows = max(1, int(n_samples * fraction))
            rows = self._generate_rows(scenario_type, n_rows)
            records.append(rows)

        df = pd.concat(records, ignore_index=True)
        # Shuffle with reproducible rng
        df = df.sample(frac=1, random_state=self.seed).reset_index(drop=True)
        logger.info(
            "Generated dataset: %d rows, %d columns, scenarios: %s",
            len(df),
            len(df.columns),
            df["scenario_type"].value_counts().to_dict(),
        )
        return df

    def generate_scenario(
        self,
        scenario_type: str,
        n_farmers: int = 5,
    ) -> pd.DataFrame:
        """
        Generate a single scenario with ``n_farmers`` farmer-agents.

        Used by the mediation pipeline to create one simulation instance.

        Parameters
        ----------
        scenario_type : str
            One of the 8 SCENARIO_TYPES.
        n_farmers : int
            Number of farmers in this scenario (2–10 recommended).

        Returns
        -------
        pd.DataFrame
            One row per farmer with all features + ``water_demand_m3``.
        """
        if scenario_type not in SCENARIO_TYPES:
            raise ValueError(
                f"Unknown scenario_type {scenario_type!r}. "
                f"Valid types: {SCENARIO_TYPES}"
            )
        if not (2 <= n_farmers <= 20):
            raise ValueError("n_farmers must be between 2 and 20.")

        cfg = SCENARIO_CONFIGS[scenario_type]
        rows = self._generate_rows(scenario_type, n_farmers, cfg=cfg)

        # Apply scenario-specific overrides
        if cfg.inject_urgency_farmer and n_farmers >= 1:
            rows.loc[0, "growth_stage"] = "flowering"
            rows.loc[0, "urgency_score"] = self.rng.uniform(0.85, 1.0)
            rows.loc[0, "crop_stress_index"] = self.rng.uniform(0.75, 1.0)
            # Recompute water demand for that row
            rows.loc[0, "water_demand_m3"] = self._compute_demand(rows.iloc[0])

        if cfg.inject_flexible_farmer and n_farmers >= 2:
            rows.loc[n_farmers - 1, "flexibility_score"] = self.rng.uniform(0.80, 1.0)
            rows.loc[n_farmers - 1, "irrigation_window_hours"] = self.rng.integers(10, 18)

        if cfg.force_simultaneous_windows:
            # Force all farmers to prefer the same 6-hour window
            rows["preferred_start_hour"] = 6
            rows["irrigation_window_hours"] = 6

        if cfg.rainfall_bonus_mm > 0:
            rows["rainfall_mm"] += cfg.rainfall_bonus_mm
            # Rainfall reduces effective demand (deficit decreases)
            rows["water_demand_m3"] = (
                rows["water_demand_m3"] * (1.0 - cfg.rainfall_bonus_mm / 60.0)
            ).clip(lower=5.0)

        # Compute total demand and set scenario water supply
        total_demand = rows["water_demand_m3"].sum()
        supply_fraction = self.rng.uniform(*cfg.supply_fraction_range)
        rows["total_available_water_m3"] = round(total_demand * supply_fraction, 2)
        rows["canal_capacity_m3_per_hour"] = round(
            self.rng.uniform(*cfg.canal_capacity_range), 2
        )
        rows["scenario_type"] = scenario_type

        logger.info(
            "Scenario '%s': %d farmers, demand=%.1fm³, supply=%.1fm³ (%.0f%%)",
            scenario_type,
            n_farmers,
            total_demand,
            rows["total_available_water_m3"].iloc[0],
            supply_fraction * 100,
        )
        return rows.reset_index(drop=True)

    # ─── Internal helpers ──────────────────────────────────────────────────────

    def _generate_rows(
        self,
        scenario_type: str,
        n_rows: int,
        cfg: Optional[ScenarioConfig] = None,
    ) -> pd.DataFrame:
        """Generate ``n_rows`` farmer observations for a given scenario."""
        cfg = cfg or SCENARIO_CONFIGS[scenario_type]

        crops = self.rng.choice(CROPS, size=n_rows)
        soils = self.rng.choice(SOILS, size=n_rows)
        stages = self.rng.choice(GROWTH_STAGES, size=n_rows)
        seasons = self.rng.choice(SEASONS, size=n_rows)

        farm_areas = self.rng.uniform(0.5, 10.0, size=n_rows)        # hectares
        et0_values = np.array([
            self.rng.uniform(*ET0_RANGE[s]) for s in seasons
        ])                                                             # mm/day

        kc_values = np.array([
            KC_TABLE[crop][stage] for crop, stage in zip(crops, stages)
        ])

        # ETc = ET₀ × Kc (FAO-56 single crop coefficient approach)
        etc_mm_per_day = et0_values * kc_values

        # Convert ETc to m³/day per farm:
        # ETc (mm/day) × area (ha) × 10 = m³/day
        base_demand_m3 = etc_mm_per_day * farm_areas * 10.0

        # Add realistic noise: ±15% to represent field heterogeneity
        noise = self.rng.normal(1.0, 0.10, size=n_rows)
        water_demand_m3 = np.clip(base_demand_m3 * noise, 5.0, 800.0)

        # Soil WHC → affects minimum requirement
        whc_values = np.array([
            self.rng.uniform(*SOIL_WHC[s]) for s in soils
        ])
        # Minimum requirement: 40% of demand (crop survival threshold)
        min_requirement_m3 = water_demand_m3 * self.rng.uniform(0.35, 0.45, size=n_rows)

        # Irrigation window
        pref_start = self.rng.integers(4, 20, size=n_rows)   # 4 AM–8 PM
        window_hours = self.rng.integers(4, 10, size=n_rows)  # 4–10 hour window

        # Urgency = stage criticality + some noise
        stage_crit = np.array([STAGE_CRITICALITY[s] for s in stages])
        urgency = np.clip(stage_crit + self.rng.normal(0, 0.1, size=n_rows), 0.0, 1.0)

        # Flexibility score
        flexibility = self.rng.uniform(0.1, 0.9, size=n_rows)

        # Weather features
        temp_c = np.array([
            self.rng.uniform(22.0, 38.0) if s in ("kharif", "zaid") else
            self.rng.uniform(10.0, 24.0)
            for s in seasons
        ])
        humidity = self.rng.uniform(30.0, 90.0, size=n_rows)
        rainfall_mm = np.where(
            np.array(seasons) == "kharif",
            self.rng.uniform(0.0, 15.0, size=n_rows),
            self.rng.uniform(0.0, 3.0, size=n_rows),
        )

        # Crop stress index — elevated at flowering, lower at harvest
        crop_stress = np.clip(
            stage_crit * self.rng.uniform(0.7, 1.0, size=n_rows), 0.0, 1.0
        )

        # Synthetic farmer IDs
        farmer_ids = [f"FARM_{i+1:04d}" for i in range(n_rows)]

        df = pd.DataFrame(
            {
                # Identifiers
                "farmer_id": farmer_ids,
                "scenario_type": scenario_type,
                "is_synthetic": True,

                # Farm characteristics
                "crop_type": crops,
                "soil_type": soils,
                "growth_stage": stages,
                "season": seasons,
                "farm_area_hectares": np.round(farm_areas, 3),

                # Agronomic parameters
                "et0_mm_per_day": np.round(et0_values, 3),
                "kc_value": np.round(kc_values, 3),
                "etc_mm_per_day": np.round(etc_mm_per_day, 3),
                "soil_whc_mm_per_m": np.round(whc_values, 2),

                # Water demand (TARGET)
                "water_demand_m3": np.round(water_demand_m3, 2),
                "minimum_requirement_m3": np.round(min_requirement_m3, 2),

                # Irrigation scheduling
                "preferred_start_hour": pref_start,
                "irrigation_window_hours": window_hours,
                "flexibility_score": np.round(flexibility, 3),

                # Agent properties
                "urgency_score": np.round(urgency, 3),
                "crop_stress_index": np.round(crop_stress, 3),

                # Weather context
                "temperature_celsius": np.round(temp_c, 2),
                "humidity_percent": np.round(humidity, 2),
                "rainfall_mm": np.round(rainfall_mm, 2),
            }
        )
        return df

    def _compute_demand(self, row: pd.Series) -> float:
        """
        Recompute water demand for a single row after overrides.
        Uses the FAO-56 single crop coefficient approach.
        """
        kc = KC_TABLE.get(row["crop_type"], {}).get(row["growth_stage"], 1.0)
        et0 = row["et0_mm_per_day"]
        area = row["farm_area_hectares"]
        etc = et0 * kc
        demand = etc * area * 10.0
        noise = float(self.rng.normal(1.0, 0.10))
        return round(float(np.clip(demand * noise, 5.0, 800.0)), 2)

    # ─── Convenience helpers ───────────────────────────────────────────────────

    def get_scenario_water_supply(
        self,
        scenario_type: str,
        total_demand_m3: float,
    ) -> Tuple[float, float]:
        """
        Compute water supply and canal capacity for a scenario.

        Returns
        -------
        (total_available_water_m3, canal_capacity_m3_per_hour)
        """
        cfg = SCENARIO_CONFIGS[scenario_type]
        supply_frac = float(self.rng.uniform(*cfg.supply_fraction_range))
        canal_cap = float(self.rng.uniform(*cfg.canal_capacity_range))
        return round(total_demand_m3 * supply_frac, 2), round(canal_cap, 2)

    def describe_scenario(self, scenario_type: str) -> Dict[str, str]:
        """Return human-readable description of a scenario type."""
        if scenario_type not in SCENARIO_CONFIGS:
            raise ValueError(f"Unknown scenario_type: {scenario_type!r}")
        cfg = SCENARIO_CONFIGS[scenario_type]
        return {
            "scenario_type": scenario_type,
            "description": cfg.description,
            "supply_range": f"{cfg.supply_fraction_range[0]*100:.0f}%–{cfg.supply_fraction_range[1]*100:.0f}% of demand",
            "canal_capacity_range": f"{cfg.canal_capacity_range[0]:.0f}–{cfg.canal_capacity_range[1]:.0f} m³/hour",
        }

    @staticmethod
    def get_scenario_types() -> List[str]:
        """Return the list of all valid scenario type strings."""
        return SCENARIO_TYPES.copy()

    @staticmethod
    def get_crops() -> List[str]:
        """Return the list of all supported crop types."""
        return CROPS.copy()

    @staticmethod
    def get_feature_columns() -> List[str]:
        """
        Return the list of feature column names used for ML training.
        (Excludes identifier and target columns.)
        """
        return [
            "farm_area_hectares",
            "et0_mm_per_day",
            "kc_value",
            "etc_mm_per_day",
            "soil_whc_mm_per_m",
            "minimum_requirement_m3",
            "preferred_start_hour",
            "irrigation_window_hours",
            "flexibility_score",
            "urgency_score",
            "crop_stress_index",
            "temperature_celsius",
            "humidity_percent",
            "rainfall_mm",
            # Encoded categoricals added by feature_engineering.py:
            "crop_type_encoded",
            "soil_type_encoded",
            "growth_stage_encoded",
            "season_encoded",
        ]

    @staticmethod
    def get_target_column() -> str:
        """Return the target column name."""
        return "water_demand_m3"
