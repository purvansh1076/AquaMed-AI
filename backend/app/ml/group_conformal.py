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

    def calibrate(self, residuals: np.ndarray, scales: np.ndarray, groups: np.ndarray) -> None:
        # residuals: |y - yhat|, scales: area scale s(A)
        scores = residuals / np.clip(scales, 1e-6, None)
        self.global_q = float(np.quantile(scores, self.confidence_level))
        self._base = ConformalPredictor(q_norm=self.global_q, confidence_level=self.confidence_level, use_normalized=True)
        for g in np.unique(groups):
            mask = groups == g
            if mask.sum() >= self.min_group_size:
                self.group_q[str(g)] = float(np.quantile(scores[mask], self.confidence_level))

    def predict_interval(self, point_prediction_m3: float, farm_area_ha: float = 1.0, group: Optional[str] = None, growth_stage: str = "vegetative") -> Dict[str, Any]:
        q = self.group_q.get(str(group), self.global_q) if group is not None else self.global_q
        cp = ConformalPredictor(q_norm=q, confidence_level=self.confidence_level, use_normalized=True)
        return cp.predict_interval(point_prediction_m3, farm_area_ha=farm_area_ha, growth_stage=growth_stage)
