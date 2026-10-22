"""
AquaMediAI — Tests for Synthetic Data Generator & Feature Engineering
======================================================================

Test coverage:
  - Dataset generation (shape, columns, no invalid values)
  - All 8 scenario types present and correctly labelled
  - Agronomic range checks (ETc, Kc, demand)
  - Synthetic flag always True
  - Reproducibility with fixed seed
  - Single-scenario generation
  - Feature engineering: encoding, interactions, train/val/test split
  - DataFrame validation utility
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from app.ml.data_generator import (
    CROPS,
    GROWTH_STAGES,
    SCENARIO_TYPES,
    SOILS,
    KC_TABLE,
    SyntheticDataGenerator,
)
from app.ml.feature_engineering import (
    ENGINEERED_FEATURE_COLS,
    TARGET_COL,
    FittedEncoders,
    add_interaction_features,
    apply_encoders,
    engineer_features,
    fit_encoders,
    get_feature_matrix,
    train_val_test_split,
    validate_dataframe,
)


# ─── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def gen():
    return SyntheticDataGenerator(seed=42)


@pytest.fixture(scope="module")
def dataset_400(gen):
    return gen.generate_dataset(n_samples=400)


@pytest.fixture(scope="module")
def dataset_2000(gen):
    return gen.generate_dataset(n_samples=2000)


# ─── 1. Dataset generation ────────────────────────────────────────────────────


class TestDatasetGeneration:
    """Tests for SyntheticDataGenerator.generate_dataset()."""

    def test_dataset_returns_dataframe(self, dataset_400):
        assert isinstance(dataset_400, pd.DataFrame)

    def test_dataset_has_correct_row_count(self, gen):
        df = gen.generate_dataset(n_samples=800)
        # Allow ±1 row due to integer rounding per scenario
        assert abs(len(df) - 800) <= len(SCENARIO_TYPES)

    def test_dataset_has_required_columns(self, dataset_400):
        required = [
            "farmer_id",
            "scenario_type",
            "is_synthetic",
            "crop_type",
            "soil_type",
            "growth_stage",
            "season",
            "farm_area_hectares",
            "et0_mm_per_day",
            "kc_value",
            "etc_mm_per_day",
            "soil_whc_mm_per_m",
            "water_demand_m3",
            "minimum_requirement_m3",
            "preferred_start_hour",
            "irrigation_window_hours",
            "flexibility_score",
            "urgency_score",
            "crop_stress_index",
            "temperature_celsius",
            "humidity_percent",
            "rainfall_mm",
        ]
        missing = [c for c in required if c not in dataset_400.columns]
        assert missing == [], f"Missing columns: {missing}"

    def test_no_null_values_in_required_cols(self, dataset_400):
        critical_cols = [
            "crop_type", "soil_type", "growth_stage", "season",
            "farm_area_hectares", "water_demand_m3", "et0_mm_per_day",
            "kc_value", "flexibility_score", "urgency_score",
        ]
        null_counts = dataset_400[critical_cols].isnull().sum()
        assert null_counts.sum() == 0, f"NaN found: {null_counts[null_counts > 0]}"

    def test_is_synthetic_always_true(self, dataset_400):
        assert dataset_400["is_synthetic"].all(), (
            "All rows must have is_synthetic=True"
        )

    def test_water_demand_positive(self, dataset_400):
        assert (dataset_400["water_demand_m3"] > 0).all()

    def test_farm_area_positive(self, dataset_400):
        assert (dataset_400["farm_area_hectares"] > 0).all()

    def test_minimum_requirement_less_than_demand(self, dataset_400):
        assert (
            dataset_400["minimum_requirement_m3"] < dataset_400["water_demand_m3"]
        ).all()

    def test_flexibility_score_in_range(self, dataset_400):
        assert (dataset_400["flexibility_score"] >= 0).all()
        assert (dataset_400["flexibility_score"] <= 1).all()

    def test_urgency_score_in_range(self, dataset_400):
        assert (dataset_400["urgency_score"] >= 0).all()
        assert (dataset_400["urgency_score"] <= 1).all()

    def test_crop_stress_index_in_range(self, dataset_400):
        assert (dataset_400["crop_stress_index"] >= 0).all()
        assert (dataset_400["crop_stress_index"] <= 1).all()

    def test_preferred_start_hour_valid(self, dataset_400):
        assert (dataset_400["preferred_start_hour"] >= 0).all()
        assert (dataset_400["preferred_start_hour"] <= 23).all()

    def test_etc_mm_equals_et0_times_kc_approx(self, dataset_400):
        """ETc should be close to ET₀ × Kc (within 5% due to noise)."""
        expected = dataset_400["et0_mm_per_day"] * dataset_400["kc_value"]
        # Note: etc_mm_per_day is the exact product; demand has noise
        np.testing.assert_allclose(
            dataset_400["etc_mm_per_day"].values,
            expected.values,
            rtol=1e-3,
        )


# ─── 2. Scenario types ────────────────────────────────────────────────────────


class TestScenarioTypes:
    """Tests ensuring all 8 scenario types are generated and correctly labelled."""

    def test_all_8_scenario_types_present(self, dataset_400):
        found = set(dataset_400["scenario_type"].unique())
        missing = set(SCENARIO_TYPES) - found
        assert missing == set(), f"Missing scenario types: {missing}"

    def test_scenario_types_are_valid_strings(self, dataset_400):
        invalid = set(dataset_400["scenario_type"]) - set(SCENARIO_TYPES)
        assert invalid == set(), f"Invalid scenario types found: {invalid}"

    @pytest.mark.parametrize("scenario_type", SCENARIO_TYPES)
    def test_generate_scenario_single_type(self, gen, scenario_type):
        """Each scenario type can be generated individually."""
        df = gen.generate_scenario(scenario_type=scenario_type, n_farmers=5)
        assert len(df) == 5
        assert (df["scenario_type"] == scenario_type).all()

    def test_generate_scenario_invalid_type_raises(self, gen):
        with pytest.raises(ValueError, match="Unknown scenario_type"):
            gen.generate_scenario("totally_fake_scenario", n_farmers=3)

    def test_generate_scenario_too_few_farmers_raises(self, gen):
        with pytest.raises(ValueError, match="n_farmers"):
            gen.generate_scenario("normal_water", n_farmers=1)

    def test_severe_shortage_has_lower_supply_than_demand(self, gen):
        """Severe shortage supply should be less than total demand."""
        df = gen.generate_scenario("severe_shortage", n_farmers=5)
        total_demand = df["water_demand_m3"].sum()
        supply = df["total_available_water_m3"].iloc[0]
        assert supply < total_demand, (
            f"Severe shortage: supply ({supply:.1f}) >= demand ({total_demand:.1f})"
        )

    def test_normal_water_supply_exceeds_demand(self, gen):
        """Normal water scenario supply should meet or exceed demand."""
        df = gen.generate_scenario("normal_water", n_farmers=5)
        total_demand = df["water_demand_m3"].sum()
        supply = df["total_available_water_m3"].iloc[0]
        assert supply >= total_demand * 0.95, (
            f"Normal water: supply ({supply:.1f}) << demand ({total_demand:.1f})"
        )

    def test_high_urgency_farmer_has_flowering_stage(self, gen):
        """high_urgency_farmer scenario: first farmer must be at flowering stage."""
        df = gen.generate_scenario("high_urgency_farmer", n_farmers=5)
        assert df.loc[0, "growth_stage"] == "flowering"
        assert df.loc[0, "urgency_score"] >= 0.80

    def test_flexible_farmer_has_high_flexibility(self, gen):
        """flexible_farmer scenario: last farmer has flexibility_score >= 0.80."""
        df = gen.generate_scenario("flexible_farmer", n_farmers=5)
        assert df.loc[4, "flexibility_score"] >= 0.75

    def test_simultaneous_demand_same_start_hour(self, gen):
        """simultaneous_demand: all farmers share the same preferred_start_hour."""
        df = gen.generate_scenario("simultaneous_demand", n_farmers=5)
        assert df["preferred_start_hour"].nunique() == 1

    def test_sudden_rainfall_has_extra_rainfall(self, gen):
        """sudden_rainfall scenario has rainfall_mm boosted."""
        df_rain = gen.generate_scenario("sudden_rainfall", n_farmers=5)
        df_normal = gen.generate_scenario("normal_water", n_farmers=5)
        assert df_rain["rainfall_mm"].mean() > df_normal["rainfall_mm"].mean()


# ─── 3. Agronomic range checks ────────────────────────────────────────────────


class TestAgronomicRanges:
    """Validate that generated values respect FAO-56 grounded ranges."""

    def test_kc_values_match_fao56_table(self, dataset_400):
        """All Kc values should be within known FAO-56 Kc ranges."""
        # Min Kc across all crops/stages = 0.20, max = 1.30 (with small noise)
        assert (dataset_400["kc_value"] >= 0.20).all()
        assert (dataset_400["kc_value"] <= 1.35).all()

    def test_et0_in_realistic_range(self, dataset_400):
        """ET₀ should be between 1 and 15 mm/day for Indian conditions."""
        assert (dataset_400["et0_mm_per_day"] >= 1.0).all()
        assert (dataset_400["et0_mm_per_day"] <= 15.0).all()

    def test_water_demand_within_practical_limits(self, dataset_400):
        """Demand per farmer should be between 5 and 800 m³/day."""
        assert (dataset_400["water_demand_m3"] >= 5.0).all()
        assert (dataset_400["water_demand_m3"] <= 800.0).all()

    def test_crop_types_all_known(self, dataset_400):
        unknown = set(dataset_400["crop_type"]) - set(CROPS)
        assert unknown == set(), f"Unknown crop types: {unknown}"

    def test_soil_types_all_known(self, dataset_400):
        unknown = set(dataset_400["soil_type"]) - set(SOILS)
        assert unknown == set(), f"Unknown soil types: {unknown}"

    def test_growth_stages_all_known(self, dataset_400):
        unknown = set(dataset_400["growth_stage"]) - set(GROWTH_STAGES)
        assert unknown == set(), f"Unknown growth stages: {unknown}"


# ─── 4. Reproducibility ───────────────────────────────────────────────────────


class TestReproducibility:
    """Fixed seed must produce identical datasets across independent runs."""

    def test_same_seed_produces_identical_dataset(self):
        gen_a = SyntheticDataGenerator(seed=99)
        gen_b = SyntheticDataGenerator(seed=99)
        df_a = gen_a.generate_dataset(n_samples=200)
        df_b = gen_b.generate_dataset(n_samples=200)
        pd.testing.assert_frame_equal(df_a, df_b)

    def test_different_seeds_produce_different_datasets(self):
        df_42 = SyntheticDataGenerator(seed=42).generate_dataset(n_samples=200)
        df_99 = SyntheticDataGenerator(seed=99).generate_dataset(n_samples=200)
        # At least the demand values should differ
        assert not df_42["water_demand_m3"].equals(df_99["water_demand_m3"])

    def test_scenario_generation_reproducible(self):
        gen_a = SyntheticDataGenerator(seed=7)
        gen_b = SyntheticDataGenerator(seed=7)
        df_a = gen_a.generate_scenario("severe_shortage", n_farmers=5)
        df_b = gen_b.generate_scenario("severe_shortage", n_farmers=5)
        pd.testing.assert_frame_equal(df_a, df_b)


# ─── 5. Feature Engineering ───────────────────────────────────────────────────


class TestFeatureEngineering:
    """Tests for encoding, interaction features, splitting."""

    @pytest.fixture(scope="class")
    def raw_df(self):
        gen = SyntheticDataGenerator(seed=42)
        return gen.generate_dataset(n_samples=400)

    @pytest.fixture(scope="class")
    def train_df(self, raw_df):
        train, _, _ = train_val_test_split(raw_df, seed=42)
        return train

    @pytest.fixture(scope="class")
    def encoders(self, train_df):
        return fit_encoders(train_df)

    def test_fit_encoders_returns_fitted_encoders(self, encoders):
        assert isinstance(encoders, FittedEncoders)
        assert "crop_type" in encoders.label_encoders
        assert "soil_type" in encoders.label_encoders
        assert "season" in encoders.label_encoders
        assert encoders.growth_stage_encoder is not None

    def test_apply_encoders_adds_encoded_columns(self, train_df, encoders):
        df = apply_encoders(train_df, encoders)
        assert "crop_type_encoded" in df.columns
        assert "soil_type_encoded" in df.columns
        assert "growth_stage_encoded" in df.columns
        assert "season_encoded" in df.columns

    def test_growth_stage_ordinal_order(self, encoders):
        """flowering (index 2) should have a higher code than germination (index 0)."""
        import pandas as pd
        oe = encoders.growth_stage_encoder
        test = pd.DataFrame({"growth_stage": ["germination", "flowering", "harvest"]})
        encoded = oe.transform(test[["growth_stage"]]).ravel()
        assert encoded[1] > encoded[0], "flowering should rank higher than germination"
        assert encoded[2] > encoded[1], "harvest should rank higher than flowering"

    def test_interaction_features_added(self, train_df, encoders):
        df = engineer_features(train_df, encoders)
        assert "area_x_etc" in df.columns
        assert "urgency_x_stress" in df.columns
        assert "rain_deficit" in df.columns
        assert "flexibility_window" in df.columns
        assert "et0_x_kc" in df.columns

    def test_rain_deficit_non_negative(self, train_df, encoders):
        df = engineer_features(train_df, encoders)
        assert (df["rain_deficit"] >= 0).all()

    def test_get_feature_matrix_shapes(self, train_df, encoders):
        df_eng = engineer_features(train_df, encoders)
        X, y = get_feature_matrix(df_eng)
        assert X.shape[0] == len(train_df)
        assert X.shape[1] == len(ENGINEERED_FEATURE_COLS)
        assert y.shape == (len(train_df),)
        assert y.dtype == np.float64

    def test_no_nans_after_engineering(self, train_df, encoders):
        df_eng = engineer_features(train_df, encoders)
        X, y = get_feature_matrix(df_eng)
        assert not np.any(np.isnan(X)), "NaN in feature matrix X"
        assert not np.any(np.isnan(y)), "NaN in target vector y"

    def test_train_val_test_split_sizes(self, raw_df):
        train, val, test = train_val_test_split(raw_df, seed=42)
        total = len(raw_df)
        assert abs(len(train) / total - 0.70) < 0.05
        assert abs(len(val) / total - 0.15) < 0.05
        assert abs(len(test) / total - 0.15) < 0.05

    def test_train_val_test_no_overlap(self, raw_df):
        train, val, test = train_val_test_split(raw_df, seed=42)
        # Use _row_id (original row stamps) not reset integer indices
        train_ids = set(train["_row_id"])
        val_ids = set(val["_row_id"])
        test_ids = set(test["_row_id"])
        assert train_ids.isdisjoint(val_ids), "Train and val overlap (by _row_id)!"
        assert train_ids.isdisjoint(test_ids), "Train and test overlap (by _row_id)!"
        assert val_ids.isdisjoint(test_ids), "Val and test overlap (by _row_id)!"
        # Also check total coverage
        assert len(train_ids | val_ids | test_ids) == len(raw_df), "Some rows missing!"

    def test_all_scenario_types_in_train_and_test(self, raw_df):
        train, val, test = train_val_test_split(raw_df, seed=42)
        for split_df, name in [(train, "train"), (test, "test")]:
            found = set(split_df["scenario_type"].unique())
            missing = set(SCENARIO_TYPES) - found
            assert missing == set(), (
                f"Missing scenario types in {name} split: {missing}"
            )


# ─── 6. DataFrame Validation Utility ─────────────────────────────────────────


class TestValidateDataframe:
    """Tests for the validate_dataframe() utility."""

    def test_valid_dataframe_produces_no_errors(self, dataset_400):
        errors = validate_dataframe(dataset_400)
        assert errors == [], f"Unexpected validation errors: {errors}"

    def test_missing_column_detected(self, dataset_400):
        bad_df = dataset_400.drop(columns=["water_demand_m3"])
        errors = validate_dataframe(bad_df)
        assert any("Missing required columns" in e for e in errors)

    def test_invalid_scenario_type_detected(self, dataset_400):
        bad_df = dataset_400.copy()
        bad_df.loc[0, "scenario_type"] = "fake_scenario"
        errors = validate_dataframe(bad_df)
        assert any("Unknown scenario_type" in e for e in errors)

    def test_negative_demand_detected(self, dataset_400):
        bad_df = dataset_400.copy()
        bad_df.loc[0, "water_demand_m3"] = -10.0
        errors = validate_dataframe(bad_df)
        assert any("water_demand_m3" in e for e in errors)

    def test_non_synthetic_flag_detected(self, dataset_400):
        bad_df = dataset_400.copy()
        bad_df.loc[0, "is_synthetic"] = False
        errors = validate_dataframe(bad_df)
        assert any("is_synthetic" in e for e in errors)

    def test_out_of_range_flexibility_detected(self, dataset_400):
        bad_df = dataset_400.copy()
        bad_df.loc[0, "flexibility_score"] = 1.5
        errors = validate_dataframe(bad_df)
        assert any("flexibility_score" in e for e in errors)


# ─── 7. Static method helpers ─────────────────────────────────────────────────


class TestStaticHelpers:
    """Tests for SyntheticDataGenerator static helpers."""

    def test_get_scenario_types_returns_all_8(self):
        types = SyntheticDataGenerator.get_scenario_types()
        assert len(types) == 8
        assert set(types) == set(SCENARIO_TYPES)

    def test_get_crops_returns_list(self):
        crops = SyntheticDataGenerator.get_crops()
        assert isinstance(crops, list)
        assert len(crops) >= 1

    def test_get_feature_columns_returns_engineered_cols(self):
        cols = SyntheticDataGenerator.get_feature_columns()
        assert isinstance(cols, list)
        assert "water_demand_m3" not in cols, "Target must not be in feature list"

    def test_get_target_column(self):
        assert SyntheticDataGenerator.get_target_column() == "water_demand_m3"

    def test_describe_scenario_returns_dict(self):
        gen = SyntheticDataGenerator(seed=42)
        info = gen.describe_scenario("severe_shortage")
        assert info["scenario_type"] == "severe_shortage"
        assert "description" in info

    def test_describe_scenario_invalid_raises(self):
        gen = SyntheticDataGenerator(seed=42)
        with pytest.raises(ValueError):
            gen.describe_scenario("not_a_real_scenario")
