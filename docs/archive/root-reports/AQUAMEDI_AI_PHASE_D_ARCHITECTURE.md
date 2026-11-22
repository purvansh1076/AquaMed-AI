# AquaMedi AI — Phase D Architecture

## Multi-agent architecture

- Farmer Digital Twin: `backend/app/agents/farmer_agent.py`, `digital_twin.py`, `utility.py`.
- Agent factory: `backend/app/agents/agent_factory.py`.
- Negotiation: `backend/app/negotiation/negotiation_engine.py`, `mediator.py`, `bargaining.py`.
- Typed message contract: `backend/app/agents/messages.py` (Phase D).
- Optimization: `backend/app/allocation/lp_allocator.py` (authoritative constraints).
- Fairness: `backend/app/allocation/fairness.py`.

## Constraint authority

LP allocator enforces hard constraints; agents propose/negotiate but cannot override.
Final allocation validated by `verify_constraints` and `_verify_allocation_physics`.

## Convergence

Bounded by `NegotiationConfig.max_rounds`; termination reasons recorded; `convergence_report()` provides measurable summary.
