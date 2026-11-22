# AquaMedi AI — Agronomic Validation Report (Phase C)

## Independent reference tests

- `backend/tests/test_fao56_reference.py`: sugarcane benchmark (ETc 5.98 mm, 299.0 m³), 1 mm×1 ha = 10 m³ conversion, rainfall reduces demand.

## Verified equations

- ETc = Kc × ET0
- Net irrigation = max(0, ETc - Peff)
- Gross = net / efficiency
- Volumetric (m³/day) = gross(mm) × area(ha) × 10

## Known limitations

- Synthetic data only; no field validation.
- Single crop per farmer; no multi-crop/rotation.
- Kc fixed per growth stage; stage progression not modeled within a record.
- Regional calibration (NASA POWER) scaffolded but not yet integrated into demand generation.
