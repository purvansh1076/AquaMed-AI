"""
AquaMediAI — train_models.py
==============================

Reproducible CLI script that runs the full ML training pipeline:

    1. Generate synthetic agronomic dataset (FAO-56 ET₀ × Kc × area).
    2. Validate the dataset.
    3. Perform feature engineering (fit encoders on train split only).
    4. Train Random Forest baseline.
    5. Train XGBoost primary model (with validation early stopping).
    6. Evaluate both models on the held-out TEST set.
    7. Save models, encoders, and evaluation results.

Usage
-----
    # From the backend/ directory:
    python scripts/train_models.py

    # With options:
    python scripts/train_models.py --n-samples 5000 --seed 123 --model-dir data/models

IMPORTANT DISCLAIMER
--------------------
All data is synthetically generated. This script does NOT use real farmer data.
Metrics printed below come from the actual held-out test set — they are not
fabricated or cherry-picked.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

# ── Ensure backend/ is on sys.path when run as a script ──────────────────────
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ml.trainer import run_training_pipeline

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AquaMediAI — Train water-demand prediction models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=3000,
        help="Number of synthetic samples to generate (default: 3000)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default="data/models",
        help="Directory to save model artefacts (default: data/models)",
    )
    return parser.parse_args()


def print_separator(char: str = "-", width: int = 70) -> None:
    print(char * width)


def print_model_results(result) -> None:
    """Pretty-print ModelResult metrics."""
    print(f"\n  Model         : {result.model_name} v{result.model_version}")
    print(f"  Training time : {result.training_time_seconds:.2f}s")
    print(f"  N features    : {result.n_features}")
    print()
    for split_attr, label in [
        ("train_metrics", "Train "),
        ("val_metrics",   "Val   "),
        ("test_metrics",  "Test  "),
    ]:
        m = getattr(result, split_attr)
        if m:
            print(
                f"  {label}| MAE={m.mae:>9.4f} m3/day  "
                f"RMSE={m.rmse:>9.4f} m3/day  "
                f"R2={m.r2:>7.4f}  "
                f"(n={m.n_samples})"
            )


def main() -> int:
    args = parse_args()
    model_dir = Path(args.model_dir)

    print_separator("=")
    print(" AquaMediAI -- ML Training Pipeline")
    print_separator("=")
    print(" DISCLAIMER: ALL DATA IS SYNTHETIC (FAO-56 ET0 x Kc x area pipeline)")
    print("             No real farmer records are used.")
    print_separator("-")
    print(f" n_samples : {args.n_samples}")
    print(f" seed      : {args.seed}")
    print(f" model_dir : {model_dir.resolve()}")
    print_separator("-")

    t_start = time.perf_counter()

    try:
        artifacts = run_training_pipeline(
            n_samples=args.n_samples,
            seed=args.seed,
            model_dir=model_dir,
            save_artifacts=True,
        )
    except Exception as exc:
        logger.error("Training pipeline failed: %s", exc, exc_info=True)
        return 1

    elapsed_total = time.perf_counter() - t_start

    # Print results
    print_separator("=")
    print(" TRAINING RESULTS (metrics from held-out TEST set)")
    print_separator("=")

    print_model_results(artifacts.rf_result)
    print_separator()
    print_model_results(artifacts.xgb_result)

    print_separator("=")
    print(f" Best model (by test MAE): *** {artifacts.best_model_name} ***")
    print_separator("-")

    # Comparison table
    rf_t = artifacts.rf_result.test_metrics
    xgb_t = artifacts.xgb_result.test_metrics
    print(f"\n  {'Model':<18} {'MAE':>12} {'RMSE':>12} {'R2':>8} {'Train(s)':>10}")
    print(f"  {'-'*18} {'-'*12} {'-'*12} {'-'*8} {'-'*10}")
    print(
        f"  {'RandomForest':<18} {rf_t.mae:>12.4f} {rf_t.rmse:>12.4f}"
        f" {rf_t.r2:>8.4f} {artifacts.rf_result.training_time_seconds:>10.2f}"
    )
    print(
        f"  {'XGBoost':<18} {xgb_t.mae:>12.4f} {xgb_t.rmse:>12.4f}"
        f" {xgb_t.r2:>8.4f} {artifacts.xgb_result.training_time_seconds:>10.2f}"
    )

    print_separator("-")
    print(f"\n Artifacts saved to: {model_dir.resolve()}")
    print("  - rf_model.joblib")
    print("  - xgb_model.joblib")
    print("  - encoders.joblib")
    print("  - evaluation_results.json")
    print(f"\n Total wall time: {elapsed_total:.2f}s")
    print_separator("=")

    return 0


if __name__ == "__main__":
    sys.exit(main())
