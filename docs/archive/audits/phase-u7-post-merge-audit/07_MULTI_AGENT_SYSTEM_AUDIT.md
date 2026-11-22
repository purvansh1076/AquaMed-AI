# Phase U7 — Audit Report 07: Multi-Agent System & Negotiation Dynamics Audit

**Document ID:** `AQUA-AUDIT-U7-07`  
**Date:** 2026-11-15  
**Review Type:** Multi-Agent Architecture, Protocol Safety & Mechanism Design Audit  
**Component:** Agent Framework (`backend/app/agents/`)  

---

## 1. Executive Summary

This report evaluates the multi-agent negotiation system, agent communication protocols, message schemas, and authority boundaries in AquaMedi AI.

The audit verified that agent interactions are strictly mediated by strongly-typed message schemas, that LP optimization remains authoritative over all agent proposals, and that the multi-agent system functions as an exploratory decision-support capability rather than an autonomous decision-maker.

---

## 2. Multi-Agent Architecture & Roles

The system models agricultural canal networks through distributed autonomous agents (`backend/app/agents/`):

1. **Farmer Digital Twins (`FarmerAgent`):**
   - Represents the individual farmer's agricultural goals.
   - Computes utility based on crop growth stage sensitivity, daily soil moisture depletion, and economic crop valuation.
   - Generates counter-proposals and concessions during water shortage negotiations.
2. **Authority / Mediator Agent (`AuthorityAgent`):**
   - Represents the district water authority or irrigation department.
   - Enforces physical conservation constraints ($\sum x_i \le W_{\text{available}}$) and prevents upstream overuse.
   - Mediates disputes and issues arbitration rulings based on Nash bargaining or Max-Min fairness criteria.

---

## 3. Communication Protocol & Message Validation

All agent exchanges use strongly-typed Pydantic v2 schemas (`backend/app/agents/messages.py`):
```python
class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    receiver_id: str
    round_number: int = Field(ge=0, le=10)
    proposal: Dict[str, float]
    message_type: MessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @model_validator(mode="after")
    def validate_endpoints(self) -> "AgentMessage":
        if self.sender_id == self.receiver_id:
            raise ValueError("Sender and receiver cannot be identical.")
        return self
```
- **Validation Rules:** Self-directed messages are rejected. Round counters are bounded ($0 \le t \le 10$). Stale or out-of-order messages are dropped.

---

## 4. Authority Hierarchy & Optimization Primacy

A critical safety question is whether autonomous agents can bypass physical water constraints:
- **Primacy of Optimization:** All final water dispatch quantities are computed by the authoritative LP allocator.
- **Agent Sandbox Boundary:** Agent proposals represent advisory requests or preferences. Agents cannot directly write to canal schedule tables or override physical sluice constraints.
- **Post-Negotiation Verification:** Even if agents reach a bilateral agreement, the final proposed schedule is re-submitted to the LP allocator to mathematically confirm that physical capacity $\sum x_i \le W_{\text{available}}$ is not violated.

---

## 5. Investigation of Negotiation Dynamics & Convergence

During Phase G and Phase H testing, earlier simulation runs frequently reported agreement within a single negotiation round:

### 5.1 Root Cause Analysis of Fast Convergence
1. **Initial Feasibility Overlap:** In standard test scenarios, the difference between initial farmer requests and available water was small ($\le 10\%$).
2. **Boulware Concession Sensitivity:** Under mild shortage, the Authority Agent's initial counter-proposal satisfied each farmer's survival threshold, leading to immediate acceptance in Round 1.
3. **Severe Shortage Behavior:** In multi-parcel drought simulations with large deficits ($>40\%$), the negotiation engine executes multi-round concession curves (Boulware and Conceder decay functions) across 4 to 8 rounds before converging to a Pareto-optimal allocation.
4. **Non-Convergence Protocol:** If agents fail to agree within $T_{\max} = 10$ rounds, the mediator terminates negotiation and enforces the default Max-Min fairness allocation.

---

## 6. System Classification & Operational Boundaries

In alignment with engineering governance standards:
- **Classification:** The multi-agent negotiation system is classified as an **experimental decision-support capability**.
- **Human Oversight:** Agent-generated compromise schedules are recommendations presented to human irrigation officers in the Expert Portal. They do not execute autonomously in the field.

---

## 7. Verdict

**Multi-Agent Status: PASS (Strict Authority Boundaries & Decision-Support Classification)**
