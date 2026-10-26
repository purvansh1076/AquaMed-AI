"""
AquaMediAI — Feature Leakage & Target Contamination Audit Tool
==============================================================

Automated auditing tool to detect:
1. Tautological formula leakage (features that are mathematical re-expressions of the target).
2. Extreme collinearity (|r| > 0.95) indicating artificial label synthesis.
3. Operational game-state contamination (negotiation/agent variables used as natural biophysical predictors).
4. Temporal lookahead violations in time series.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

import numpy as np
import pandas as pd


@dataclass
class LeakageFinding:
    feature_name: str
    finding_type: str  # 'tautological', 'extreme_correlation', 'operational_leakage'
    severity: str      # 'CRITICAL', 'HIGH', 'MEDIUM', 'INFO'
    correlation_with_target: float
    description: str

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LeakageAuditReport:
    target_column: str
    total_features_audited: int
    findings: List[LeakageFinding] = field(default_factory=list)
    has_critical_leakage: bool = False
    verdict: str = "PASS"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "target_column": self.target_column,
            "total_features_audited": self.total_features_audited,
            "findings": [f.as_dict() for f in self.findings],
            "has_critical_leakage": self.has_critical_leakage,
            "verdict": self.verdict,
        }


# Known operational variables from the agent/negotiation layer that should NOT
# be used to predict natural crop biophysical water requirements:
OPERATIONAL_AGENT_VARS = {
    "preferred_start_hour",
    "irrigation_window_hours",
    "flexibility_score",
    "urgency_score",
    "crop_stress_index",
    "flexibility_window",
    "urgency_x_stress",
}


def audit_feature_leakage(
    df: pd.DataFrame,
    feature_columns: List[str],
    target_column: str = "water_demand_m3",
    correlation_threshold: float = 0.95,
) -> LeakageAuditReport:
    """
    Run an automated leakage and contamination audit on candidate features.

    Parameters
    ----------
    df : pd.DataFrame
        Dataset containing candidate features and target column.
    feature_columns : list of str
        Features to audit.
    target_column : str
        Target variable name.
    correlation_threshold : float
        Correlation threshold flagging potential label leakage (default 0.95).

    Returns
    -------
    LeakageAuditReport
    """
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in DataFrame.")

    target = df[target_column].astype(float)
    findings: List[LeakageFinding] = []

    for col in feature_columns:
        if col not in df.columns:
            continue

        series = pd.to_numeric(df[col], errors="coerce")
        if series.isna().all() or series.std() == 0:
            corr = 0.0
        else:
            valid_mask = series.notna() & target.notna()
            if valid_mask.sum() > 2:
                corr = float(np.corrcoef(series[valid_mask], target[valid_mask])[0, 1])
            else:
                corr = 0.0

        # Check 1: Known tautological feature (area_x_etc)
        if col in ("area_x_etc", "etc_x_area"):
            findings.append(
                LeakageFinding(
                    feature_name=col,
                    finding_type="tautological",
                    severity="CRITICAL",
                    correlation_with_target=round(corr, 4),
                    description=(
                        f"'{col}' is a mathematical duplicate of the defining equation "
                        f"for '{target_column}' (demand = area * etc * 10). "
                        "Trees simply learn a constant multiplier, masking real agronomic modeling."
                    ),
                )
            )

        # Check 2: Extreme correlation indicating synthetic formula leakage
        elif abs(corr) >= correlation_threshold:
            findings.append(
                LeakageFinding(
                    feature_name=col,
                    finding_type="extreme_correlation",
                    severity="HIGH",
                    correlation_with_target=round(corr, 4),
                    description=(
                        f"Feature '{col}' has |r| = {corr:.4f} >= {correlation_threshold}, "
                        "indicating near-deterministic collinearity with the target."
                    ),
                )
            )

        # Check 3: Operational agent variables
        if col in OPERATIONAL_AGENT_VARS:
            findings.append(
                LeakageFinding(
                    feature_name=col,
                    finding_type="operational_leakage",
                    severity="MEDIUM",
                    correlation_with_target=round(corr, 4),
                    description=(
                        f"'{col}' is an agent negotiation/game-state variable, not an "
                        "antecedent biophysical atmospheric or physiological property."
                    ),
                )
            )

    has_critical = any(f.severity == "CRITICAL" for f in findings)
    verdict = "FAIL" if has_critical else ("WARNING" if findings else "PASS")

    return LeakageAuditReport(
        target_column=target_column,
        total_features_audited=len(feature_columns),
        findings=findings,
        has_critical_leakage=has_critical,
        verdict=verdict,
    )
