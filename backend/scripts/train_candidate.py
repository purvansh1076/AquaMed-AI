#!/usr/bin/env python3
"""Reproduce candidate v1/v2/v3 training artifacts.

Usage:
    python backend/scripts/train_candidate.py --version v1 --seed 42
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure backend/ is on sys.path when invoked from repo root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.ml.candidate_trainer import CandidatePipelineTrainer

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Reproduce candidate ML artifacts.")
    parser.add_argument("--version", default="v1", help="Candidate version (v1, v2, v3).")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--data", type=str, default=None, help="Optional processed CSV (follow-up: not yet wired).")
    args = parser.parse_args()

    if args.data is not None:
        logging.warning("--data is accepted but the trainer currently builds its own dataset; recorded as follow-up.")

    version = args.version if args.version.startswith("candidate_") else f"candidate_{args.version}"
    trainer = CandidatePipelineTrainer(candidate_dir_name=version, seed=args.seed)
    results = trainer.run_pipeline()
    print("Decision:", results["decision"])


if __name__ == "__main__":
    main()
