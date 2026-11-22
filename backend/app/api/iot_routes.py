"""
AquaMediAI — IoT Telemetry & Virtual Sensor API Routes
======================================================
Exposes endpoints for:
1. Ingesting LoRaWAN and ESP32 telemetry packets.
2. Querying latest soil telemetry per sensor node.
3. Simulating 24-hour diurnal capacitive soil moisture physics.
"""

from __future__ import annotations

import hmac
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.api.deps import require_farmer_or_expert
from app.config import get_settings
from app.services.iot_service import iot_telemetry_service

router = APIRouter(prefix="/iot", tags=["IoT & Field Telemetry"])


def require_device_key(
    x_device_key: Optional[str] = Header(None, alias="X-Device-Key"),
) -> None:
    """
    Authenticate IoT telemetry ingestion with a shared device API key.

    Fails closed when IOT_API_KEY is not configured. Per-device keys and
    rotation are a production follow-up.
    """
    expected = get_settings().iot_api_key
    if not expected or not x_device_key or not hmac.compare_digest(x_device_key, expected):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "unauthorized_device",
                "detail": "A valid X-Device-Key header is required for telemetry ingestion.",
                "status_code": 401,
            },
        )


class TelemetryPacketRequest(BaseModel):
    device_id: str = Field(..., description="Unique hardware identifier (e.g. LORA_NODE_01)")
    farmer_id: str = Field(..., description="Associated farmer ID")
    soil_moisture_pct: float = Field(..., ge=0.0, le=100.0, description="Volumetric soil moisture percentage")
    soil_temp_c: float = Field(..., ge=-10.0, le=60.0, description="Soil temperature in Celsius")
    battery_mv: int = Field(..., ge=2000, le=4500, description="Battery voltage in millivolts")
    timestamp: Optional[str] = None


@router.post(
    "/telemetry",
    summary="Ingest sensor telemetry packet",
    description="Receives encrypted or standard LoRaWAN/ESP32 agricultural sensor packets.",
)
def ingest_telemetry(
    payload: TelemetryPacketRequest,
    _device: None = Depends(require_device_key),
) -> Dict[str, Any]:
    try:
        return iot_telemetry_service.ingest_packet(
            device_id=payload.device_id,
            farmer_id=payload.farmer_id,
            soil_moisture_pct=payload.soil_moisture_pct,
            soil_temp_c=payload.soil_temp_c,
            battery_mv=payload.battery_mv,
            timestamp=payload.timestamp,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.get(
    "/telemetry/{device_id}",
    summary="Get latest telemetry for a sensor node",
)
def get_latest_telemetry(
    device_id: str,
    _identity: Dict[str, Any] = Depends(require_farmer_or_expert),
) -> Dict[str, Any]:
    data = iot_telemetry_service.get_latest_telemetry(device_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"No telemetry found for device: {device_id}")
    return data


@router.get(
    "/simulate",
    summary="Generate diurnal soil moisture curve",
    description="Simulates 24-hour physical soil moisture transpiration and evaporation cycles.",
)
def simulate_diurnal_curve(
    farmer_id: str = Query("F001", description="Farmer ID"),
    base_moisture: float = Query(48.0, ge=10.0, le=90.0, description="Baseline moisture percentage"),
    _identity: Dict[str, Any] = Depends(require_farmer_or_expert),
) -> Dict[str, Any]:
    return iot_telemetry_service.simulate_diurnal_curve(farmer_id=farmer_id, base_moisture=base_moisture)
