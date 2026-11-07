"""
AquaMediAI — Crop Health Diagnostics & Stress Screening Service
================================================================
Rule-based and symptom-guided diagnostic intelligence for water-stressed
and nutrient-deficient crops in Central Maharashtra (Ahmednagar basin).

DISCLAIMER: Provides screening recommendations based on agronomic heuristics.
Not a replacement for physical extension lab soil and plant tissue testing.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Diagnostic knowledge base for regional crops
DIAGNOSTIC_RULES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "sugarcane": {
        "yellowing_lower_leaves": {
            "condition": "Nitrogen Deficiency or Progressive Soil Moisture Stress",
            "severity": "Medium",
            "cause": "Depletion of available root-zone nitrogen compounded by prolonged deficit irrigation.",
            "recommendation": "Perform light supplemental irrigation (20-30 mm); top-dress with urea or apply 2% foliar nitrogen spray.",
        },
        "curled_spindle_leaves": {
            "condition": "Acute Drought & Atmospheric Heat Stress",
            "severity": "High",
            "cause": "Vapor pressure deficit exceeding stomatal regulation threshold (temp > 38°C).",
            "recommendation": "Schedule urgent canal or well irrigation within 24 hours. Apply trash mulching to conserve root-zone moisture.",
        },
        "red_rot_internal_streaks": {
            "condition": "Red Rot (Colletotrichum falcatum)",
            "severity": "Critical",
            "cause": "Fungal pathogen aggravated by waterlogging followed by drought cycles.",
            "recommendation": "Rogue out infected clumps immediately; avoid flood irrigation that carries fungal spores downstream; treat seed setts with carbendazim.",
        },
    },
    "cotton": {
        "leaf_reddening": {
            "condition": "Magnesium / Nitrogen Deficiency (Lal Patti)",
            "severity": "Medium",
            "cause": "Low soil temperature, waterlogging or sudden moisture stress during boll development.",
            "recommendation": "Spray 1% magnesium sulphate (MgSO4) + 1% urea at 15-day intervals.",
        },
        "wilting_midday": {
            "condition": "Parawilt or Vascular Wilting",
            "severity": "High",
            "cause": "Rapid transition from rain/irrigation to hot sunny conditions causing root hypoxia.",
            "recommendation": "Drench root zone with copper oxychloride (2.5 g/L); ensure drainage ditches are unobstructed.",
        },
    },
    "soybean": {
        "yellow_mosaic": {
            "condition": "Yellow Mosaic Virus (YMV)",
            "severity": "High",
            "cause": "Viral infection transmitted by whitefly (Bemisia tabaci) vectors.",
            "recommendation": "Spray dimethoate 30 EC (1.5 ml/L) to control vector population; avoid water stress during pod filling.",
        },
        "rust_pustules_underside": {
            "condition": "Soybean Rust (Phakopsora pachyrhizi)",
            "severity": "Critical",
            "cause": "High relative humidity (> 80%) with moderate temperatures (20-28°C).",
            "recommendation": "Foliar spray of hexaconazole 5 EC (1 ml/L) or propiconazole 25 EC (1 ml/L).",
        },
    },
    "wheat": {
        "yellow_stripes": {
            "condition": "Yellow Rust (Puccinia striiformis)",
            "severity": "High",
            "cause": "Cool humid climate during reproductive phase.",
            "recommendation": "Apply propiconazole 25 EC @ 0.1% upon initial detection of uredinial pustules.",
        },
        "tip_drying": {
            "condition": "Terminal Heat & Moisture Deficit",
            "severity": "Medium",
            "cause": "Premature hot winds during grain filling stage.",
            "recommendation": "Provide light evening irrigation to reduce microclimatic canopy temperature.",
        },
    },
}

DEFAULT_ADVISORY = {
    "condition": "General Abiotic Moisture Stress",
    "severity": "Low",
    "cause": "Elevated ambient evapotranspiration rate.",
    "recommendation": "Monitor soil moisture status using tensiometer or soil feel method; irrigate when available depletion exceeds 50%.",
}


class CropHealthService:
    """Service evaluating plant stress and symptoms against agronomic diagnostic rules."""

    def diagnose_symptoms(
        self,
        crop_type: str,
        symptom_key: str,
        soil_moisture_pct: Optional[float] = None,
        growth_stage: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate observed symptoms and generate validated agricultural guidance."""
        crop_normalized = crop_type.strip().lower()
        symptom_normalized = symptom_key.strip().lower()

        crop_diagnostics = DIAGNOSTIC_RULES.get(crop_normalized, {})
        diagnostic_entry = crop_diagnostics.get(symptom_normalized, DEFAULT_ADVISORY)

        # Moisture context refinement
        moisture_warning = None
        if soil_moisture_pct is not None:
            if soil_moisture_pct < 25.0:
                moisture_warning = "Critical Root-Zone Deficit: Soil moisture is severely depleted (< 25%). Symptoms are heavily exacerbated by moisture stress."
            elif soil_moisture_pct > 85.0:
                moisture_warning = "Root Hypoxia Warning: Soil moisture exceeds 85%, potential root waterlogging detected."

        return {
            "crop_type": crop_normalized.title(),
            "symptom": symptom_key.replace("_", " ").title(),
            "diagnosis": diagnostic_entry["condition"],
            "severity": diagnostic_entry["severity"],
            "agronomic_cause": diagnostic_entry["cause"],
            "recommended_action": diagnostic_entry["recommendation"],
            "soil_moisture_context": moisture_warning,
            "disclaimer": (
                "Screening advisory generated from agro-extension rules. "
                "Consult local Krishi Vigyan Kendra (KVK) for laboratory confirmation."
            ),
        }


crop_health_service = CropHealthService()
