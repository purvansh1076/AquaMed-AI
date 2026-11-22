# AquaMedi AI — Farmer Digital Twin Report

## State validation

`FarmerAgent._validate` enforces non-empty IDs, valid crops/soils/stages, positive demand, ordered water bounds, urgency/sensitivity/flexibility in [0,1], timing order.

## Demand consistency

Demand comes from `WaterDemandPredictor` via `agent_factory`; no arbitrary substitution.

## Tests

Existing farmer agent tests pass; new message contract tests added.
