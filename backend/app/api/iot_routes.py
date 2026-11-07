"""
AquaMediAI — IoT Telemetry & Virtual Sensor API Routes
======================================================
Exposes endpoints for:
1. Ingesting LoRaWAN and ESP32 telemetry packets.
2. Querying latest soil telemetry per sensor node.
3. Simulating 24-hour diurnal capacitive soil moisture physics.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.iot_service import iot_telemetry_service

router = APIRouter(prefix="/iot", tags=["IoT & Field Telemetry"])


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
def ingest_telemetry(payload: TelemetryPacketRequest) -> Dict[str, Any]:
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
def get_latest_telemetry(device_id: str) -> Dict[str, Any]:
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
) -> Dict[str, Any]:
    return iot_telemetry_service.simulate_diurnal_curve(farmer_id=farmer_id, base_moisture=base_moisture)
