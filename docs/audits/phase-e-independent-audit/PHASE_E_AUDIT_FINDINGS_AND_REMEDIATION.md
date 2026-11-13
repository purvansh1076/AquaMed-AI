# Phase E Audit Findings and Remediation

## Critical
None.

## High
- H1: Group conformal lacks finite-sample correction and independent coverage evaluation.
- H2: No independent ET0 reference validation.

## Medium
- M1: Max-min LP not integrated/benchmarked.
- M2: Repeated CV uses random splits only.
- M3: No subgroup performance reporting.
- M4: New modules isolated from production.

## Low
- L1: Only 3 seeds.
- L2: min_group_size=30 may be small.

## Remediation
- Add finite-sample correction and group coverage evaluation.
- Add independent ET0 reference tests.
- Run integrated benchmark comparing all strategies.
- Increase seeds and add subgroup reporting.
