"""
AquaMedi AI - Typed multi-agent message contract.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, model_validator


class MessageType(str, Enum):
    DEMAND_PROPOSAL = "DEMAND_PROPOSAL"
    WATER_REQUEST = "WATER_REQUEST"
    ALLOCATION_PROPOSAL = "ALLOCATION_PROPOSAL"
    COUNTER_PROPOSAL = "COUNTER_PROPOSAL"
    ACCEPTANCE = "ACCEPTANCE"
    REJECTION = "REJECTION"
    NEGOTIATION_UPDATE = "NEGOTIATION_UPDATE"
    CONFLICT = "CONFLICT"
    FINAL_ALLOCATION = "FINAL_ALLOCATION"
    ERROR = "ERROR"


class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_agent_id: str
    receiver_agent_id: str
    message_type: MessageType
    scenario_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"
    correlation_id: Optional[str] = None

    @model_validator(mode="after")
    def validate_ids(self) -> "AgentMessage":
        if not self.sender_agent_id or not self.receiver_agent_id:
            raise ValueError("sender and receiver agent ids are required")
        if self.sender_agent_id == self.receiver_agent_id:
            raise ValueError("sender and receiver must differ")
        if not self.scenario_id:
            raise ValueError("scenario_id is required")
        return self
