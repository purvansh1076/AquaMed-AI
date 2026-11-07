"""
AquaMediAI — Spatial Intelligence & Remote Sensing API Routes
=============================================================
Exposes endpoints for:
1. Satellite vegetation indices (NDVI, NDWI) and calibrated Kc.
2. GeoJSON canal irrigation network and farm nodes.
"""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Query

from app.services.remote_sensing import remote_sensing_service

router = APIRouter(prefix="/spatial", tags=["Spatial & Remote Sensing"])


@router.get(
    "/indices",
    summary="Get Sentinel-2 satellite vegetation indices",
    description="Returns surface reflectance, NDVI, NDWI, and satellite-calibrated crop coefficient Kc.",
)
def get_satellite_indices(
    lat: float = Query(19.0948, description="Latitude"),
    lon: float = Query(74.7480, description="Longitude"),
    crop_type: str = Query("sugarcane", description="Target crop"),
) -> Dict[str, Any]:
    return remote_sensing_service.get_parcel_indices(lat=lat, lon=lon, crop_type=crop_type)


@router.get(
    "/canal-network",
    summary="Get GeoJSON canal network topology",
    description="Returns canal distributaries, sluice gates, and head-to-tail farm nodes with conveyance loss coefficients.",
)
def get_canal_network() -> Dict[str, Any]:
    return remote_sensing_service.get_canal_network_topology()
