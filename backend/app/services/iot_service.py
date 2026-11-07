"""
AquaMediAI — IoT & Soil Telemetry Ingestion Service
===================================================
Ingests capacitive soil moisture and microclimatic sensor packets from
field-deployed ESP32 and LoRaWAN gateways (ChirpStack / TTN payloads).
Provides a calibrated virtual sensor simulator for rural agricultural deployments.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class IoTTelemetryService:
    """Service managing IoT node registration, telemetry ingestion, and simulation."""

    def __init__(self) -> None:
        # In-memory buffer of latest sensor telemetry by device_id
        self._telemetry_store: Dict[str, List[Dict[str, Any]]] = {}

    def ingest_packet(
        self,
        device_id: str,
        farmer_id: str,
        soil_moisture_pct: float,
        soil_temp_c: float,
        battery_mv: int,
        timestamp: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Validate and store a telemetry packet from an agricultural sensor node."""
        if not (0.0 <= soil_moisture_pct <= 100.0):
            raise ValueError(f"Soil moisture out of physical bounds: {soil_moisture_pct}%")

        ts = timestamp or datetime.now(timezone.utc).isoformat()
        packet = {
            "device_id": device_id,
            "farmer_id": farmer_id,
            "soil_moisture_pct": round(soil_moisture_pct, 1),
            "soil_temp_c": round(soil_temp_c, 1),
            "battery_mv": battery_mv,
            "battery_status": "Healthy" if battery_mv > 3300 else "Low Battery Warning",
            "timestamp": ts,
        }

        if device_id not in self._telemetry_store:
            self._telemetry_store[device_id] = []
        self._telemetry_store[device_id].append(packet)

        # Keep last 100 readings per device
        if len(self._telemetry_store[device_id]) > 100:
            self._telemetry_store[device_id] = self._telemetry_store[device_id][-100:]

        logger.info("Ingested IoT telemetry packet for device %s (moisture=%.1f%%)", device_id, soil_moisture_pct)
        return {
            "status": "ingested",
            "packet": packet,
            "validation": "PASS",
        }

    def get_latest_telemetry(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Return the most recent telemetry packet for a device."""
        history = self._telemetry_store.get(device_id)
        return history[-1] if history else None

    def simulate_diurnal_curve(self, farmer_id: str = "F001", base_moisture: float = 48.0) -> Dict[str, Any]:
        """
        Generate a realistic 24-hour diurnal soil moisture curve simulating
        daytime plant transpiration depletion and nighttime equilibrium.
        """
        curve = []
        for hour in range(24):
            # Transpiration peak between 11:00 and 16:00
            if 9 <= hour <= 17:
                depletion = (hour - 9) * 0.9 if hour <= 14 else (17 - hour) * 0.9
            else:
                depletion = 0.2
            moisture = max(15.0, round(base_moisture - depletion, 1))
            temp = round(20.0 + 12.0 * max(0.0, (hour - 6) / 8) if 6 <= hour <= 14 else 32.0 - (hour - 14) * 1.2, 1)
            curve.append({
                "hour": f"{hour:02d}:00",
                "soil_moisture_pct": moisture,
                "soil_temperature_c": temp,
            })

        return {
            "farmer_id": farmer_id,
            "simulation_type": "Calibrated 24-Hour Diurnal Soil Physics",
            "base_moisture_pct": base_moisture,
            "diurnal_readings": curve,
        }


iot_telemetry_service = IoTTelemetryService()
