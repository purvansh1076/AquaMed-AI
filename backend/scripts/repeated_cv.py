"""
AquaMedi AI - Phase E repeated cross-validation (reproducible).
"""
from __future__ import annotations

import json
import time

import numpy as np

from app.config import get_settings
from app.ml.data_generator import SyntheticDataGenerator
from app.ml.feature_engineering import train_val_test_split, engineer_features, get_feature_matrix
from app.ml.trainer import train_xgboost, train_random_forest, compute_metrics, load_encoders
from app.ml.feature_engineering import fit_encoders

settings = get_settings()
seeds = [42, 7, 123]
n_samples = 1500
results = {"seeds": seeds, "n_samples": n_samples, "xgboost": [], "random_forest": []}

for seed in seeds:
    gen = SyntheticDataGenerator(seed=seed)
    df = gen.generate_dataset(n_samples=n_samples)
    train_df, val_df, test_df = train_val_test_split(df, seed=seed)
    encoders = fit_encoders(train_df)
    train_eng = engineer_features(train_df, encoders)
    val_eng = engineer_features(val_df, encoders)
    test_eng = engineer_features(test_df, encoders)
    X_train, y_train = get_feature_matrix(train_eng)
    X_val, y_val = get_feature_matrix(val_eng)
    X_test, y_test = get_feature_matrix(test_eng)

    xgb_model, _ = train_xgboost(X_train, y_train, X_val, y_val)
    rf_model, _ = train_random_forest(X_train, y_train)

    xgb_m = compute_metrics(y_test, xgb_model.predict(X_test), "test")
    rf_m = compute_metrics(y_test, rf_model.predict(X_test), "test")
    results["xgboost"].append(xgb_m.as_dict())
    results["random_forest"].append(rf_m.as_dict())
    print(f"seed {seed}: XGB MAE={xgb_m.mae:.3f} R2={xgb_m.r2:.4f} | RF MAE={rf_m.mae:.3f} R2={rf_m.r2:.4f}")

# Summary
for model in ("xgboost", "random_forest"):
    maes = [r["mae"] for r in results[model]]
    rmses = [r["rmse"] for r in results[model]]
    r2s = [r["r2"] for r in results[model]]
    results[model + "_summary"] = {
        "mae_mean": float(np.mean(maes)),
        "mae_std": float(np.std(maes)),
        "rmse_mean": float(np.mean(rmses)),
        "rmse_std": float(np.std(rmses)),
        "r2_mean": float(np.mean(r2s)),
        "r2_std": float(np.std(r2s)),
    }

out = settings.model_dir_path / "phase_e_repeated_cv.json"
with open(out, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)
print("saved", out)
print(json.dumps(results["xgboost_summary"], indent=2))
print(json.dumps(results["random_forest_summary"], indent=2))
