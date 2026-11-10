"""
Independent deep audit of XGBoost model artifact, datasets, base_score, and features.
"""
import json
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from app.ml.feature_engineering import (
    ENGINEERED_FEATURE_COLS,
    TARGET_COL,
    apply_encoders,
    engineer_features,
    get_feature_matrix,
    train_val_test_split,
)
from app.ml.data_generator import SyntheticDataGenerator

def audit_xgb():
    print("--- 1. LOADING ARTIFACTS ---")
    model_path = "data/models/xgb_model.joblib"
    encoders_path = "data/models/encoders.joblib"
    eval_path = "data/models/evaluation_results.json"
    
    with open(eval_path, "r") as f:
        eval_data = json.load(f)
    print(f"Eval JSON best_model: {eval_data.get('best_model')}")
    print(f"Eval JSON XGB test_metrics: {eval_data.get('XGBoost', {}).get('test_metrics')}")
    print(f"Eval JSON n_features: {eval_data.get('dataset', {}).get('n_features')}")
    print(f"Number of ENGINEERED_FEATURE_COLS in code: {len(ENGINEERED_FEATURE_COLS)}")

    # Load raw model without trainer.py load_model() calibration
    raw_model = joblib.load(model_path)
    print(f"\nModel class: {type(raw_model)}")
    print(f"Model n_features_in_: {getattr(raw_model, 'n_features_in_', None)}")
    print(f"Model feature_names_in_: {len(getattr(raw_model, 'feature_names_in_', []))} features")
    
    booster = raw_model.get_booster()
    config = json.loads(booster.save_config())
    learner_param = config.get("learner", {}).get("learner_model_param", {})
    print(f"\nBooster raw learner_model_param.base_score: {learner_param.get('base_score')}")
    print(f"Booster objective: {config.get('learner', {}).get('objective', {})}")

    # Generate dataset using the generator
    gen = SyntheticDataGenerator(seed=42)
    df = gen.generate_dataset(n_samples=3000)
    print(f"\nGenerated dataset shape: {df.shape}")
    print(f"Target column mean (all 3000): {df[TARGET_COL].mean():.5f}")
    
    # Check train/val/test split
    df_train, df_val, df_test = train_val_test_split(df, seed=42)
    print(f"Train set shape: {df_train.shape}, target mean: {df_train[TARGET_COL].mean():.5f}")
    print(f"Val set shape: {df_val.shape}, target mean: {df_val[TARGET_COL].mean():.5f}")
    print(f"Test set shape: {df_test.shape}, target mean: {df_test[TARGET_COL].mean():.5f}")
    
    # Load encoders and apply
    encoders = joblib.load(encoders_path)
    df_test_enc = apply_encoders(df_test, encoders)
    df_test_eng = engineer_features(df_test_enc, encoders)
    X_test, y_test = get_feature_matrix(df_test_eng)
    print(f"X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
    
    # Evaluate with raw booster (uncalibrated)
    y_pred_raw = booster.inplace_predict(X_test)
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    mae_raw = mean_absolute_error(y_test, y_pred_raw)
    rmse_raw = np.sqrt(mean_squared_error(y_test, y_pred_raw))
    r2_raw = r2_score(y_test, y_pred_raw)
    print(f"\n--- UNCALIBRATED BOOSTER EVALUATION (base_score={learner_param.get('base_score')}) ---")
    print(f"R2: {r2_raw:.6f}, MAE: {mae_raw:.6f}, RMSE: {rmse_raw:.6f}")
    print(f"Mean y_test: {y_test.mean():.4f}, Mean y_pred_raw: {y_pred_raw.mean():.4f}")
    print(f"Mean discrepancy: {y_test.mean() - y_pred_raw.mean():.4f}")

    # Evaluate after setting base_score to training mean
    train_mean = float(df_train[TARGET_COL].mean())
    booster.set_param('base_score', train_mean)
    y_pred_calibrated = booster.inplace_predict(X_test)
    mae_cal = mean_absolute_error(y_test, y_pred_calibrated)
    rmse_cal = np.sqrt(mean_squared_error(y_test, y_pred_calibrated))
    r2_cal = r2_score(y_test, y_pred_calibrated)
    print(f"\n--- CALIBRATED BOOSTER EVALUATION (base_score={train_mean:.5f}) ---")
    print(f"R2: {r2_cal:.8f}, MAE: {mae_cal:.6f}, RMSE: {rmse_cal:.6f}")
    print(f"Published in JSON: R2={eval_data['XGBoost']['test_metrics']['r2']:.8f}, MAE={eval_data['XGBoost']['test_metrics']['mae']:.6f}")

if __name__ == "__main__":
    audit_xgb()
