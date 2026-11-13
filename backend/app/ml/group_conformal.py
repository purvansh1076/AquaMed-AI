"""
AquaMedi AI - Group-conditional conformal prediction (Phase E).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np

from app.ml.conformal_predictor import ConformalPredictor


class GroupConformalPredictor:
    def __init__(self, confidence_level: float = 0.90, min_group_size: int = 30) -> None:
        self.confidence_level = confidence_level
        self.min_group_size = min_group_size
        self.group_q: Dict[str, float] = {}
        self.global_q: float = 25.6610
        self._base = ConformalPredictor(q_norm=self.global_q, confidence_level=confidence_level, use_normalized=True)

    @staticmethod
    def _finite_sample_quantile_level(n: int, alpha: float) -> float:
        # Standard split conformal finite-sample correction:
        # k = ceil((n + 1) * (1 - alpha)); level = k / n, capped at 1.0.
        if n <= 0:
            return 1.0
        import math
        level = math.ceil((n + 1) * (1.0 - alpha)) / n
        return min(1.0, max(0.0, level))

    def calibrate(self, residuals: np.ndarray, scales: np.ndarray, groups: np.ndarray) -> None:
        # residuals: |y - yhat|, scales: area scale s(A)
        scores = residuals / np.clip(scales, 1e-6, None)
        alpha = 1.0 - self.confidence_level
        self.global_q = float(np.quantile(scores, self._finite_sample_quantile_level(len(scores), alpha)))
        self._base = ConformalPredictor(q_norm=self.global_q, confidence_level=self.confidence_level, use_normalized=True)
        for g in np.unique(groups):
            mask = groups == g
            n_g = int(mask.sum())
            if n_g >= self.min_group_size:
                self.group_q[str(g)] = float(np.quantile(scores[mask], self._finite_sample_quantile_level(n_g, alpha)))

    def predict_interval(self, point_prediction_m3: float, farm_area_ha: float = 1.0, group: Optional[str] = None, growth_stage: str = "vegetative") -> Dict[str, Any]:
        q = self.group_q.get(str(group), self.global_q) if group is not None else self.global_q
        cp = ConformalPredictor(q_norm=q, confidence_level=self.confidence_level, use_normalized=True)
        return cp.predict_interval(point_prediction_m3, farm_area_ha=farm_area_ha, growth_stage=growth_stage)
