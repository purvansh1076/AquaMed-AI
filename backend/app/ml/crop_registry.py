"""
AquaMediAI — Reviewed & Versioned Agricultural Crop Registry
============================================================

Provides versioned, agronomic reference data for pilot crops in Central Maharashtra
(Ahmednagar canal command area: Pravara & Mula irrigation systems).

References:
-----------
1. FAO Irrigation and Drainage Paper No. 56 (Allen et al., 1998)
   Table 12: Single (time-averaged) crop coefficients (Kc) for non-stressed crops.
2. Mahatma Phule Krishi Vidyapeeth (MPKV), Rahuri, Ahmednagar, Maharashtra
   Recommended crop water requirements and irrigation scheduling for canal command areas.
3. ICAR-Indian Institute of Water Management (IIWM)
   Irrigation water management guidelines for semi-arid agro-ecological zones.

Paddy Rice Note:
----------------
Paddy rice (Oryza sativa) requires specialized wetland water balance modeling
accounting for land soaking/saturation (150-200 mm), continuous deep percolation
(3-5 mm/day), and standing water depth (50-100 mm). The standard upland non-paddy
formula (ETc - Peff) does NOT apply to paddy rice without explicit water-layer dynamics.
Paddy rice is therefore flagged as requiring wetland water balance and excluded from
simple upland models.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class GrowthStageSpec:
    """Specification for an individual crop growth stage."""

    stage_name: str
    duration_days: int
    kc_value: float
    description: str
    criticality_score: float  # Water stress sensitivity: 1.0 = peak critical


@dataclass(frozen=True)
class CropSpec:
    """Comprehensive specification for a registered crop variety."""

    crop_id: str
    canonical_name: str
    botanical_name: str
    crop_category: str  # cereal, pulse, oilseed, cash_crop, etc.
    primary_season: str  # kharif, rabi, zaid, perennial
    total_duration_days: int
    is_paddy: bool
    stages: Tuple[GrowthStageSpec, ...]
    fao56_table_reference: str
    local_institution_reference: str
    applicability_notes: str

    def get_stage_spec(self, stage_name: str) -> Optional[GrowthStageSpec]:
        """Retrieve stage specification by name."""
        norm_name = stage_name.strip().lower()
        for s in self.stages:
            if s.stage_name.lower() == norm_name:
                return s
        return None

    def get_kc(self, stage_name: str) -> float:
        """Get Kc value for a specific stage. Raises KeyError if not found."""
        spec = self.get_stage_spec(stage_name)
        if spec is None:
            valid_stages = [s.stage_name for s in self.stages]
            raise KeyError(
                f"Stage '{stage_name}' not defined for crop '{self.crop_id}'. "
                f"Valid stages: {valid_stages}"
            )
        return spec.kc_value

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


class PaddyRiceExclusionError(ValueError):
    """Raised when attempting to calculate upland non-paddy water requirement for paddy rice."""
    pass


# ── Canonical Crop Registry (Version 1.0 - Ahmednagar Pilot) ───────────────────

CROP_REGISTRY_VERSION = "1.0.0"

REGISTERED_CROPS: Dict[str, CropSpec] = {
    "wheat": CropSpec(
        crop_id="wheat",
        canonical_name="Wheat",
        botanical_name="Triticum aestivum",
        crop_category="cereal",
        primary_season="rabi",
        total_duration_days=120,
        is_paddy=False,
        stages=(
            GrowthStageSpec("germination", 15, 0.40, "Initial germination & crown root initiation", 0.90),
            GrowthStageSpec("vegetative", 30, 0.70, "Tillering and stem elongation", 0.60),
            GrowthStageSpec("flowering", 40, 1.15, "Heading, flowering and milk stage (peak ET)", 1.00),
            GrowthStageSpec("maturity", 25, 0.65, "Dough stage and grain hardening", 0.50),
            GrowthStageSpec("harvest", 10, 0.25, "Ripening and harvest drying", 0.20),
        ),
        fao56_table_reference="FAO-56 Table 12: Wheat (Kc_ini=0.40, Kc_mid=1.15, Kc_end=0.25-0.40)",
        local_institution_reference="MPKV Rahuri Agronomy Guide for Western Maharashtra Canal Command",
        applicability_notes="Major Rabi cereal crop grown Nov-Mar under surface canal / borewell irrigation.",
    ),
    "sugarcane": CropSpec(
        crop_id="sugarcane",
        canonical_name="Sugarcane",
        botanical_name="Saccharum officinarum",
        crop_category="cash_crop",
        primary_season="perennial",
        total_duration_days=365,
        is_paddy=False,
        stages=(
            GrowthStageSpec("germination", 35, 0.40, "Sprouting and emergence", 0.50),
            GrowthStageSpec("vegetative", 60, 0.80, "Tillering and early elongation", 0.70),
            GrowthStageSpec("flowering", 180, 1.25, "Grand growth and cane elongation (peak water use)", 1.00),
            GrowthStageSpec("maturity", 60, 0.75, "Sucrose accumulation and ripening", 0.60),
            GrowthStageSpec("harvest", 30, 0.60, "Pre-harvest drying", 0.30),
        ),
        fao56_table_reference="FAO-56 Table 12: Sugarcane (Kc_ini=0.40, Kc_mid=1.25, Kc_end=0.75)",
        local_institution_reference="MPKV Rahuri Sugarcane Research Station (Suru/Pre-seasonal crops)",
        applicability_notes="High water-intensity cash crop dominating the Pravara-Mula canal command.",
    ),
    "cotton": CropSpec(
        crop_id="cotton",
        canonical_name="Cotton",
        botanical_name="Gossypium hirsutum",
        crop_category="cash_crop",
        primary_season="kharif",
        total_duration_days=165,
        is_paddy=False,
        stages=(
            GrowthStageSpec("germination", 25, 0.45, "Emergence and seedling establishment", 0.70),
            GrowthStageSpec("vegetative", 40, 0.75, "Square formation and vegetative branching", 0.80),
            GrowthStageSpec("flowering", 55, 1.15, "Peak flowering and boll development", 1.00),
            GrowthStageSpec("maturity", 30, 0.80, "Boll opening", 0.60),
            GrowthStageSpec("harvest", 15, 0.60, "Harvest and senescence", 0.30),
        ),
        fao56_table_reference="FAO-56 Table 12: Cotton (Kc_ini=0.45, Kc_mid=1.15-1.20, Kc_end=0.60-0.70)",
        local_institution_reference="Central Institute for Cotton Research (CICR) Nagpur & MPKV Rahuri",
        applicability_notes="Kharif cash crop in black cotton soils (vertisols) of Central Maharashtra.",
    ),
    "soybean": CropSpec(
        crop_id="soybean",
        canonical_name="Soybean",
        botanical_name="Glycine max",
        crop_category="oilseed",
        primary_season="kharif",
        total_duration_days=95,
        is_paddy=False,
        stages=(
            GrowthStageSpec("germination", 15, 0.40, "Emergence and unifoliate leaves", 0.60),
            GrowthStageSpec("vegetative", 25, 0.80, "Trifoliate leaves and rapid branching", 0.70),
            GrowthStageSpec("flowering", 30, 1.15, "Pod initiation and seed filling (stress-critical)", 1.00),
            GrowthStageSpec("maturity", 15, 0.50, "Leaf yellowing and pod browning", 0.50),
            GrowthStageSpec("harvest", 10, 0.30, "Senescence and harvest maturity", 0.20),
        ),
        fao56_table_reference="FAO-56 Table 12: Soybean (Kc_ini=0.40, Kc_mid=1.15, Kc_end=0.50)",
        local_institution_reference="ICAR-IISR Indore & MPKV Rahuri Pulse & Oilseed Recommendations",
        applicability_notes="Short-duration Kharif crop sensitive to dry spells during flowering.",
    ),
    "maize": CropSpec(
        crop_id="maize",
        canonical_name="Maize",
        botanical_name="Zea mays",
        crop_category="cereal",
        primary_season="kharif",
        total_duration_days=105,
        is_paddy=False,
        stages=(
            GrowthStageSpec("germination", 20, 0.40, "Emergence and early whorl", 0.50),
            GrowthStageSpec("vegetative", 30, 0.80, "Rapid stem elongation", 0.70),
            GrowthStageSpec("flowering", 35, 1.15, "Tasseling, silking, and grain filling", 1.00),
            GrowthStageSpec("maturity", 15, 0.70, "Dent stage and kernel dry down", 0.50),
            GrowthStageSpec("harvest", 5, 0.50, "Full maturity and harvest", 0.20),
        ),
        fao56_table_reference="FAO-56 Table 12: Sweet Maize / Field Maize (Kc_ini=0.40, Kc_mid=1.15, Kc_end=0.70)",
        local_institution_reference="ICAR-IIMR & MPKV Rahuri Coarse Cereal Package",
        applicability_notes="Versatile grain and fodder crop grown in Kharif and Rabi.",
    ),
    "groundnut": CropSpec(
        crop_id="groundnut",
        canonical_name="Groundnut",
        botanical_name="Arachis hypogaea",
        crop_category="oilseed",
        primary_season="kharif",
        total_duration_days=115,
        is_paddy=False,
        stages=(
            GrowthStageSpec("germination", 20, 0.45, "Emergence and early seedling", 0.60),
            GrowthStageSpec("vegetative", 30, 0.75, "Branching and early flowering", 0.80),
            GrowthStageSpec("flowering", 35, 1.05, "Peg penetration and pod formation (peak stress sensitivity)", 1.00),
            GrowthStageSpec("maturity", 20, 0.70, "Pod development and seed filling", 0.60),
            GrowthStageSpec("harvest", 10, 0.55, "Maturity and harvest lifting", 0.30),
        ),
        fao56_table_reference="FAO-56 Table 12: Groundnut (Kc_ini=0.40-0.50, Kc_mid=1.05-1.15, Kc_end=0.60)",
        local_institution_reference="ICAR-DGR Junagadh & MPKV Rahuri Groundnut Protocol",
        applicability_notes="Oilseed legume grown in light-to-medium well-drained soils.",
    ),
    "rice": CropSpec(
        crop_id="rice",
        canonical_name="Paddy Rice",
        botanical_name="Oryza sativa",
        crop_category="cereal",
        primary_season="kharif",
        total_duration_days=125,
        is_paddy=True,
        stages=(
            GrowthStageSpec("germination", 20, 1.05, "Nursery / early transplanted establishment", 0.80),
            GrowthStageSpec("vegetative", 30, 1.10, "Tillering and panicle initiation", 0.90),
            GrowthStageSpec("flowering", 40, 1.20, "Booting, heading, and flowering", 1.00),
            GrowthStageSpec("maturity", 25, 1.05, "Milk, dough, and grain filling", 0.70),
            GrowthStageSpec("harvest", 10, 0.90, "Drainage before harvest", 0.30),
        ),
        fao56_table_reference="FAO-56 Table 12: Rice (Wetland paddy requires separate percolation model)",
        local_institution_reference="CRRI Cuttack & MPKV Rice Research Station",
        applicability_notes="EXCLUDED from simple upland net irrigation models. Requires wetland water layer dynamics.",
    ),
}


class CropRegistry:
    """Registry accessor providing validated crop metadata and coefficient lookups."""

    version = CROP_REGISTRY_VERSION

    @classmethod
    def get_crop(cls, crop_id: str) -> CropSpec:
        cid = crop_id.strip().lower()
        if cid not in REGISTERED_CROPS:
            available = list(REGISTERED_CROPS.keys())
            raise KeyError(f"Unknown crop_id '{crop_id}'. Available crops: {available}")
        return REGISTERED_CROPS[cid]

    @classmethod
    def get_kc(cls, crop_id: str, growth_stage: str) -> float:
        crop = cls.get_crop(crop_id)
        if crop.is_paddy:
            raise PaddyRiceExclusionError(
                f"Crop '{crop_id}' is wetland paddy rice. The standard non-paddy net irrigation "
                f"equation cannot be applied without modeling saturation and percolation."
            )
        return crop.get_kc(growth_stage)

    @classmethod
    def list_crops(cls, include_paddy: bool = False) -> List[CropSpec]:
        """List registered crops, optionally filtering out paddy rice."""
        if include_paddy:
            return list(REGISTERED_CROPS.values())
        return [c for c in REGISTERED_CROPS.values() if not c.is_paddy]

    @classmethod
    def validate_crop_stage(cls, crop_id: str, growth_stage: str) -> bool:
        """Verify whether crop_id and growth_stage are valid and registered."""
        try:
            crop = cls.get_crop(crop_id)
            return crop.get_stage_spec(growth_stage) is not None
        except KeyError:
            return False
