"""
AquaMediAI — Agricultural Data Engineering Module
"""

from app.data.region_config import (
    PREDEFINED_REGIONS,
    RegionConfig,
    get_region_config,
)
from app.data.fao56_penman_monteith import (
    calculate_crop_water_requirements,
    calculate_effective_precipitation_usda,
    calculate_fao56_et0,
)
from app.data.nasa_power_client import NasaPowerClient
from app.data.agronomic_pipeline import (
    AgronomicDataPipeline,
    ValidationReport,
    assign_indian_agricultural_season,
)

__all__ = [
    "PREDEFINED_REGIONS",
    "RegionConfig",
    "get_region_config",
    "calculate_fao56_et0",
    "calculate_effective_precipitation_usda",
    "calculate_crop_water_requirements",
    "NasaPowerClient",
    "AgronomicDataPipeline",
    "ValidationReport",
    "assign_indian_agricultural_season",
]
