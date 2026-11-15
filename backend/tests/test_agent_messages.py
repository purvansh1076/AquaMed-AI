from datetime import datetime

import pytest
from pydantic import ValidationError

from app.agents.messages import AgentMessage, MessageType


def test_valid_message():
    m = AgentMessage(
        sender_agent_id="farmer_1",
        receiver_agent_id="mediator",
        message_type=MessageType.WATER_REQUEST,
        scenario_id="scn_1",
        payload={"demand": 100.0},
    )
    assert m.message_type == MessageType.WATER_REQUEST
    assert m.schema_version == "1.0"


def test_same_sender_receiver_rejected():
    with pytest.raises(ValidationError):
        AgentMessage(
            sender_agent_id="a",
            receiver_agent_id="a",
            message_type=MessageType.ACCEPTANCE,
            scenario_id="scn_1",
        )


def test_empty_scenario_rejected():
    with pytest.raises(ValidationError):
        AgentMessage(
            sender_agent_id="a",
            receiver_agent_id="b",
            message_type=MessageType.ERROR,
            scenario_id="",
        )
