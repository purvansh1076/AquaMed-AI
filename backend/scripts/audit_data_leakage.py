"""
AquaMedi AI - Phase B dataset leakage audit (read-only).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.config import get_settings
from app.ml.data_generator import SyntheticDataGenerator
from app.ml.feature_engineering import train_val_test_split


def main() -> None:
    settings = get_settings()
    seed = 42
    gen = SyntheticDataGenerator(seed=seed)
    df = gen.generate_dataset(n_samples=3000)
    train_df, val_df, test_df = train_val_test_split(df, seed=seed)

    report = {
        "seed": seed,
        "n_total": len(df),
        "n_train": len(train_df),
        "n_val": len(val_df),
        "n_test": len(test_df),
        "duplicate_rows_total": int(df.duplicated().sum()),
        "train_val_row_overlap": int(len(set(train_df["_row_id"]) & set(val_df["_row_id"]))),
        "train_test_row_overlap": int(len(set(train_df["_row_id"]) & set(test_df["_row_id"]))),
        "val_test_row_overlap": int(len(set(val_df["_row_id"]) & set(test_df["_row_id"]))),
        "is_synthetic_all_true": bool(df["is_synthetic"].all()) if "is_synthetic" in df.columns else None,
        "scenario_distribution": df["scenario_type"].value_counts().to_dict(),
        "columns": list(df.columns),
    }

    # Check feature-target correlation for obvious leakage (target derived from etc/area)
    if "water_demand_m3" in df.columns:
        corr = df.select_dtypes(include=[np.number]).corr()["water_demand_m3"].sort_values(ascending=False)
        report["top_correlations_with_target"] = {k: float(v) for k, v in corr.head(8).items()}

    out = settings.model_dir_path / "data_leakage_audit_phase_b.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
