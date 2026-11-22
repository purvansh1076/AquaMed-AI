# AquaMedi AI — Multi-Agent Communication Report

## Typed contract

`backend/app/agents/messages.py` defines `AgentMessage` (Pydantic) with message ID, sender, receiver, type, scenario ID, timestamp, payload, schema version, correlation ID. Validates sender != receiver and non-empty scenario.

## Tests

`backend/tests/test_agent_messages.py` (3 tests).
