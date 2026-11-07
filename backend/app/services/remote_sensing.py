"""
AquaMediAI — Satellite Remote Sensing & Agro-Hydrological Spatial Service
========================================================================
Calculates Sentinel-2 multispectral vegetation indices (NDVI, NDWI)
and computes dynamic satellite-adjusted crop coefficients (Kc,sat).
Provides simulated command area topology for irrigation demonstration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


def compute_spectral_indices(b3_green: float, b4_red: float, b8_nir: float) -> Dict[str, float]:
    """
    Calculate NDVI and NDWI from surface reflectance values.

    NDVI = (NIR - Red) / (NIR + Red)
    NDWI = (Green - NIR) / (Green + NIR)
    """
    # Safeguard against zero denominator
    ndvi_denom = b8_nir + b4_red
    ndvi = (b8_nir - b4_red) / ndvi_denom if ndvi_denom > 1e-4 else 0.0

    ndwi_denom = b3_green + b8_nir
    ndwi = (b3_green - b8_nir) / ndwi_denom if ndwi_denom > 1e-4 else 0.0

    # Clamping to theoretical [-1.0, 1.0] bounds
    ndvi_clamped = max(-1.0, min(1.0, ndvi))
    ndwi_clamped = max(-1.0, min(1.0, ndwi))

    return {
        "ndvi": round(ndvi_clamped, 3),
        "ndwi": round(ndwi_clamped, 3),
    }


def estimate_satellite_kc(ndvi: float, crop_type: str = "sugarcane") -> float:
    """
    Empirical calibration of crop coefficient Kc from satellite NDVI (Bausch & Neale, 1987).
    Kc,sat = 1.25 * NDVI + 0.10, clamped to physical limits [0.20, 1.35].
    """
    kc = 1.25 * max(0.0, ndvi) + 0.10
    return round(max(0.20, min(1.35, kc)), 2)


class RemoteSensingService:
    """Spatial and satellite intelligence service for the Godavari-Pravara canal system."""

    def get_parcel_indices(
        self,
        lat: float = 19.0948,
        lon: float = 74.7480,
        crop_type: str = "sugarcane",
    ) -> Dict[str, Any]:
        """Simulate Sentinel-2 MSI surface reflectance for registered farm coordinates."""
        # Realistic spectral reflectance for healthy vegetative Deccan plateau parcel
        b3_green = 0.082
        b4_red = 0.054
        b8_nir = 0.468

        indices = compute_spectral_indices(b3_green, b4_red, b8_nir)
        kc_sat = estimate_satellite_kc(indices["ndvi"], crop_type)

        vigor = "High Canopy Vigor" if indices["ndvi"] > 0.6 else "Moderate Vigor" if indices["ndvi"] > 0.3 else "Stressed / Fallow"

        return {
            "mission": "Copernicus Sentinel-2 MSI Level-2A",
            "coordinates": {"lat": lat, "lon": lon},
            "acquisition_date": "2026-11-04T05:32:18Z",
            "cloud_coverage_pct": 2.1,
            "bands": {
                "b3_green": b3_green,
                "b4_red": b4_red,
                "b8_nir": b8_nir,
            },
            "indices": indices,
            "vegetation_vigor_status": vigor,
            "satellite_calibrated_kc": kc_sat,
            "interpretation": (
                f"NDVI of {indices['ndvi']} reflects {vigor.lower()} with healthy leaf biomass. "
                f"Calibrated crop coefficient Kc is {kc_sat}."
            ),
        }

    def get_canal_network_topology(self) -> Dict[str, Any]:
        """GeoJSON feature collection representing the simulated canal distributary network for demonstration."""
        return {
            "type": "FeatureCollection",
            "name": "Demonstration Irrigation Command Area (Simulated Distributary Network)",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "id": "CANAL_MAIN",
                        "name": "Primary Distribution Canal (Simulated)",
                        "reach_type": "Main Canal",
                        "discharge_capacity_cusecs": 450,
                        "head_loss_coefficient_per_km": 0.015,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [74.6500, 19.1200],
                            [74.7000, 19.1050],
                            [74.7480, 19.0948],
                            [74.8200, 19.0750],
                        ],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "id": "DISTRIBUTARY_1",
                        "name": "Distributary Reach D1 (Head-End)",
                        "reach_type": "Head Reach",
                        "efficiency": 0.92,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [74.7000, 19.1050],
                            [74.7150, 19.1300],
                        ],
                    },
                },
                {
                    "type": "Feature",
                    "properties": {
                        "id": "DISTRIBUTARY_2",
                        "name": "Distributary Reach D2 (Tail-End)",
                        "reach_type": "Tail Reach",
                        "efficiency": 0.68,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [74.7480, 19.0948],
                            [74.7700, 19.0600],
                        ],
                    },
                },
            ],
            "control_nodes": [
                {"id": "SLUICE_HEAD", "name": "Head Regulator", "lat": 19.1200, "lon": 74.6500, "status": "Active (450 cusecs)"},
                {"id": "SLUICE_MID", "name": "Cross Regulator Mid-Reach", "lat": 19.1050, "lon": 74.7000, "status": "Active (320 cusecs)"},
                {"id": "SLUICE_TAIL", "name": "Tail-End Offtake Gate", "lat": 19.0750, "lon": 74.8200, "status": "Reduced Flow (140 cusecs)"},
            ],
            "farm_nodes": [
                {"farmer_id": "F_01", "name": "Ramesh Patil", "crop": "Sugarcane", "reach": "Head-End", "lat": 19.1150, "lon": 74.6800, "conveyance_loss_pct": 5.0},
                {"farmer_id": "F_02", "name": "Suresh Deshmukh", "crop": "Cotton", "reach": "Mid-Reach", "lat": 19.1000, "lon": 74.7100, "conveyance_loss_pct": 14.2},
                {"farmer_id": "F_03", "name": "Anand Shinde", "crop": "Soybean", "reach": "Tail-End", "lat": 19.0800, "lon": 74.7900, "conveyance_loss_pct": 31.8},
            ],
        }


remote_sensing_service = RemoteSensingService()
