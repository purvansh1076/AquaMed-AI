"""
AquaMedi AI - Phase B baseline evaluation script.

Reproducible baseline for existing XGBoost and Random Forest models.
Does not modify model artifacts.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.ml.data_generator import SyntheticDataGenerator
from app.ml.feature_engineering import (
    ENGINEERED_FEATURE_COLS,
    train_val_test_split,
    engineer_features,
    fit_encoders,
    get_feature_matrix,
)
from app.ml.trainer import load_model, load_encoders, compute_metrics
from app.ml.conformal_predictor import ConformalPredictor


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    settings = get_settings()
    model_dir = settings.model_dir_path
    seed = 42
    n_samples = 3000

    gen = SyntheticDataGenerator(seed=seed)
    df = gen.generate_dataset(n_samples=n_samples)
    train_df, val_df, test_df = train_val_test_split(df, seed=seed)

    encoders = load_encoders(model_dir)
    # Fit fresh encoders on train split to mirror training; compare to persisted
    train_eng = engineer_features(train_df, encoders)
    val_eng = engineer_features(val_df, encoders)
    test_eng = engineer_features(test_df, encoders)

    X_train, y_train = get_feature_matrix(train_eng)
    X_val, y_val = get_feature_matrix(val_eng)
    X_test, y_test = get_feature_matrix(test_eng)

    results = {"seed": seed, "n_samples": n_samples, "splits": {
        "train": len(train_df), "val": len(val_df), "test": len(test_df)
    }, "features": ENGINEERED_FEATURE_COLS, "models": {}}

    conformal = ConformalPredictor(use_normalized=True)
    conformal_raw = ConformalPredictor(use_normalized=False)

    for name in ("XGBoost", "RandomForest"):
        model = load_model(model_dir, model_name=name)
        tr = compute_metrics(y_train, model.predict(X_train), "train")
        va = compute_metrics(y_val, model.predict(X_val), "val")
        te = compute_metrics(y_test, model.predict(X_test), "test")

        preds = model.predict(X_test).astype(float)
        # Normalized conformal coverage
        widths_norm = []
        covered_norm = 0
        widths_raw = []
        covered_raw = 0
        for i in range(len(y_test)):
            area = float(test_df.iloc[i]["farm_area_hectares"])
            stage = str(test_df.iloc[i]["growth_stage"])
            iv_n = conformal.predict_interval(float(preds[i]), farm_area_ha=area, growth_stage=stage)
            iv_r = conformal_raw.predict_interval(float(preds[i]), farm_area_ha=area, growth_stage=stage)
            widths_norm.append(iv_n["interval_width_m3"])
            covered_norm += int(iv_n["lower_bound_m3"] <= y_test[i] <= iv_n["upper_bound_m3"])
            widths_raw.append(iv_r["interval_width_m3"])
            covered_raw += int(iv_r["lower_bound_m3"] <= y_test[i] <= iv_r["upper_bound_m3"])

        results["models"][name] = {
            "train": tr.as_dict(),
            "val": va.as_dict(),
            "test": te.as_dict(),
            "conformal_normalized": {
                "coverage": covered_norm / len(y_test),
                "mean_width": float(np.mean(widths_norm)),
                "median_width": float(np.median(widths_norm)),
            },
            "conformal_raw": {
                "coverage": covered_raw / len(y_test),
                "mean_width": float(np.mean(widths_raw)),
                "median_width": float(np.median(widths_raw)),
            },
        }

    # Artifact hashes
    results["artifact_hashes"] = {}
    for fname in ("xgb_model.joblib", "rf_model.joblib", "encoders.joblib", "evaluation_results.json"):
        p = model_dir / fname
        if p.exists():
            results["artifact_hashes"][fname] = sha256_file(p)

    out = model_dir / "baseline_metrics_phase_b.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
