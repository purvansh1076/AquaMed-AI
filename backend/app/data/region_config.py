"""
AquaMediAI — Pilot Region Configuration for Agricultural Data Ingestion
=======================================================================

Configurable pilot regions in Maharashtra, India.
Represents canal command areas and agricultural basins rather than individual private farms.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class RegionConfig:
    """
    Geographic and agronomic configuration for an agricultural study region.

    Attributes
    ----------
    region_id : str
        Unique slug/key for the region (e.g. 'maharashtra_ahmednagar').
    region_name : str
        Human-readable descriptor of the canal command area or district.
    latitude : float
        Representative centroid latitude (degrees North).
    longitude : float
        Representative centroid longitude (degrees East).
    elevation_m : float
        Representative altitude above mean sea level in meters.
    basin_name : str
        River basin name governing canal hydrology.
    state : str
        Administrative state.
    country : str
        Country.
    predominant_soils : tuple of str
        Major soil textural classes in this command area.
    major_crops : tuple of str
        Major crops cultivated in Kharif/Rabi seasons.
    notes : str
        Contextual hydrological and agricultural notes.
    """

    region_id: str
    region_name: str
    latitude: float
    longitude: float
    elevation_m: float
    basin_name: str
    state: str = "Maharashtra"
    country: str = "India"
    predominant_soils: tuple[str, ...] = ("clay", "clay_loam", "loam")
    major_crops: tuple[str, ...] = ("sugarcane", "wheat", "cotton", "soybean", "maize", "groundnut")
    notes: str = ""


# ── Pre-configured Pilot Regions ───────────────────────────────────────────────

PREDEFINED_REGIONS: Dict[str, RegionConfig] = {
    "maharashtra_ahmednagar": RegionConfig(
        region_id="maharashtra_ahmednagar",
        region_name="Pravara-Mula Canal Command (Ahmednagar, Central Maharashtra)",
        latitude=19.09,
        longitude=74.74,
        elevation_m=540.0,
        basin_name="Godavari River Basin",
        predominant_soils=("clay", "clay_loam", "loam"),
        major_crops=("sugarcane", "wheat", "cotton", "soybean", "maize", "groundnut"),
        notes=(
            "Semi-arid agro-ecological zone with high canal dependency. "
            "Pravara and Mula irrigation projects provide gravity flow canal water "
            "to water user associations (WUAs)."
        ),
    ),
    "maharashtra_baramati": RegionConfig(
        region_id="maharashtra_baramati",
        region_name="Nira Left-Right Bank Canal Command (Baramati/Pune, Western Maharashtra)",
        latitude=18.15,
        longitude=74.58,
        elevation_m=550.0,
        basin_name="Krishna-Bhima River Basin",
        predominant_soils=("clay_loam", "loam", "sandy"),
        major_crops=("sugarcane", "wheat", "maize", "soybean"),
        notes="Nira valley canal network serving intensive sugarcane and horticulture.",
    ),
    "maharashtra_paithan": RegionConfig(
        region_id="maharashtra_paithan",
        region_name="Jayakwadi Dam Command Area (Paithan, Marathwada)",
        latitude=19.48,
        longitude=75.38,
        elevation_m=458.0,
        basin_name="Godavari River Basin",
        predominant_soils=("clay", "clay_loam"),
        major_crops=("cotton", "soybean", "wheat", "maize"),
        notes="Major reservoir in drought-prone Marathwada subject to severe inter-annual allocation disputes.",
    ),
}

DEFAULT_REGION_ID = "maharashtra_ahmednagar"


def get_region_config(region_id: Optional[str] = None) -> RegionConfig:
    """Return the RegionConfig for a given region_id, defaulting to Ahmednagar."""
    rid = region_id or DEFAULT_REGION_ID
    if rid not in PREDEFINED_REGIONS:
        valid_keys = list(PREDEFINED_REGIONS.keys())
        raise ValueError(f"Unknown region_id {rid!r}. Available regions: {valid_keys}")
    return PREDEFINED_REGIONS[rid]
