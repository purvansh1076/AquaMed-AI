"""
Mathematical verification of Conformal Prediction on validation and test sets.
"""
import joblib
import numpy as np
import pandas as pd
from app.ml.data_generator import SyntheticDataGenerator
from app.ml.feature_engineering import (
    apply_encoders,
    engineer_features,
    get_feature_matrix,
    train_val_test_split,
)
from app.ml.trainer import load_model, load_encoders

def test_conformal_math():
    gen = SyntheticDataGenerator(seed=42)
    df = gen.generate_dataset(n_samples=3000)
    df_train, df_val, df_test = train_val_test_split(df, seed=42)
    
    from pathlib import Path
    model_dir = Path("data/models")
    encoders = load_encoders(model_dir)
    xgb_model = load_model(model_dir, "XGBoost")
    
    # Process val
    val_eng = engineer_features(apply_encoders(df_val, encoders), encoders)
    X_val, y_val = get_feature_matrix(val_eng)
    preds_val = xgb_model.predict(X_val)
    residuals_val = np.abs(y_val - preds_val)
    
    # Process test
    test_eng = engineer_features(apply_encoders(df_test, encoders), encoders)
    X_test, y_test = get_feature_matrix(test_eng)
    preds_test = xgb_model.predict(X_test)
    residuals_test = np.abs(y_test - preds_test)
    
    print(f"Validation size: {len(y_val)}, Test size: {len(y_test)}")
    
    # 1. Standard unweighted conformal quantile
    alpha = 0.10
    n_val = len(y_val)
    # Finite sample quantile index: ceil((n+1)(1-alpha)) / n
    p = np.ceil((n_val + 1) * (1 - alpha)) / n_val
    print(f"p for quantile: {p:.6f}")
    q_hat_raw = np.quantile(residuals_val, min(1.0, p))
    q_hat_90 = np.quantile(residuals_val, 0.90)
    print(f"Raw quantile with finite-sample correction: {q_hat_raw:.4f}")
    print(f"Raw quantile at exactly 0.90: {q_hat_90:.4f}")
    
    # Test coverage of raw quantile without area scaling
    cov_test_raw = np.mean(residuals_test <= q_hat_raw)
    print(f"Test coverage of raw q_hat ({q_hat_raw:.2f} m3) across all test samples: {cov_test_raw * 100:.2f}%")
    
    # 2. Check area scaling factor s(A)
    # In conformal_predictor.py:
    # scaled_q_hat = self.q_hat * (0.8 + 0.2 * max(0.5, min(5.0, farm_area_ha)))
    areas_val = df_val["farm_area_hectares"].to_numpy()
    areas_test = df_test["farm_area_hectares"].to_numpy()
    
    s_val = 0.8 + 0.2 * np.clip(areas_val, 0.5, 5.0)
    s_test = 0.8 + 0.2 * np.clip(areas_test, 0.5, 5.0)
    print(f"\nArea scaling factors in test set: min={s_test.min():.2f}, mean={s_test.mean():.2f}, max={s_test.max():.2f}")
    
    # If using DEFAULT_Q_HAT_M3 = 45.68 with area scaling at test time:
    q_hat_code = 45.68
    half_widths_test = q_hat_code * s_test
    cov_test_scaled = np.mean(residuals_test <= half_widths_test)
    print(f"Test coverage of code implementation (q_hat={q_hat_code} * s(A)): {cov_test_scaled * 100:.2f}%")
    print(f"Average interval half-width with s(A): {half_widths_test.mean():.2f} m3 (full width: {half_widths_test.mean()*2:.2f} m3)")
    
    # 3. What if properly normalized conformal prediction is used?
    # R_i = |y_i - y_hat| / s(A_i)
    normalized_scores_val = residuals_val / s_val
    q_hat_normalized = np.quantile(normalized_scores_val, min(1.0, p))
    print(f"\nProperly normalized conformal quantile q_hat_norm: {q_hat_normalized:.4f}")
    cov_test_proper = np.mean(residuals_test <= (q_hat_normalized * s_test))
    print(f"Test coverage of PROPERLY normalized conformal prediction: {cov_test_proper * 100:.2f}%")
    print(f"Average interval half-width of properly normalized: {(q_hat_normalized * s_test).mean():.2f} m3")

if __name__ == "__main__":
    test_conformal_math()
