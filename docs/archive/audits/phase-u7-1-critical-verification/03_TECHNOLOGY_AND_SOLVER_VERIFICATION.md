# Phase U7.1 — Audit Report 03: Technology Stack & Optimization Solver Verification

**Document ID:** `AQUA-AUDIT-U7.1-03`  
**Date:** 2026-11-15  
**Review Type:** Codebase Ground-Truth Technology & Dependency Verification  
**Components:** `frontend/package.json`, `backend/app/allocation/lp_allocator.py`, `backend/requirements.txt`  

---

## 1. Executive Summary

This report reconciles discrepancies between the technology versions described in the Phase U7 audit report and the actual implementations found in the merged `main` branch.

The Phase U7 report claimed that the frontend operates on **React 18 and Vite 5**, and that the water allocation engine uses **SciPy `linprog` with the HiGHS solver**.

**Key Findings:**  
1. **Frontend Architecture:** The frontend operates on **React 19 (v19.3.0)** with **TypeScript 6 (~6.0.2)** and **Vite 8 (v8.3.0)**, not React 18 / Vite 5.
2. **Optimization Solver:** The production water allocator exclusively uses **Google OR-Tools GLOP (`pywraplp.Solver.CreateSolver("GLOP")`)**, not SciPy HiGHS. SciPy `linprog` is not imported or used anywhere in `backend/app/allocation/`.

Both discrepancies were pure documentation errors in the audit reporting text. The actual software runs on modern, stable versions of React 19 and Google OR-Tools.

---

## 2. Frontend Technology Stack Audit

Inspecting `frontend/package.json` and active `node_modules` runtime manifests:

| Technology Component | Claimed in Phase U7 Report | Declared in `package.json` | Live Installed Runtime | Status |
| :--- | :--- | :--- | :--- | :--- |
| **React** | React 18 | `^19.2.8` | **React 19.3.0** | **DOCUMENTATION CORRECTION** |
| **React-DOM** | React-DOM 18 | `^19.2.8` | **React-DOM 19.3.0** | **DOCUMENTATION CORRECTION** |
| **TypeScript** | TypeScript 5 | `~6.0.2` | **TypeScript 6.0.2** | **DOCUMENTATION CORRECTION** |
| **Vite** | Vite 5 | `^8.3.0` | **Vite 8.3.0** | **DOCUMENTATION CORRECTION** |
| **Vitest** | Vitest 1.6 | `^5.0.1` | **Vitest 5.0.1** | **DOCUMENTATION CORRECTION** |
| **React Router** | React Router v6 | `^7.18.4` | **React Router 7.18.4**| **DOCUMENTATION CORRECTION** |

### 2.1 Codebase Evidence:
Running direct Node evaluation within `aquamedi-ai/frontend`:
```bash
node -e "console.log('React:', require('react/package.json').version); console.log('Vite:', require('vite/package.json').version)"
# Output:
# React: 19.3.0
# Vite: 8.3.0
```
The application compiles cleanly under React 19, and all 95 component tests pass in Vitest 5.

---

## 3. Optimization Solver Audit

The Phase U7 report repeatedly stated:
> *"Water allocation across multiple agricultural parcels is formulated as an optimization problem solved using the scipy.optimize.linprog HiGHS solver (`backend/app/allocation/lp_allocator.py`)."*

### 3.1 Ground-Truth Code Inspection
Inspecting `backend/app/allocation/lp_allocator.py`:
- **Line 5:** `"Phase 5: Constraint-Based Water Allocation using OR-Tools GLOP."`
- **Line 96:** `from ortools.linear_solver import pywraplp`
- **Line 304:** `solver = pywraplp.Solver.CreateSolver("GLOP")`
- **Line 314–320:** Variables declared via `solver.NumVar(...)`
- **Line 329:** Constraints added via `solver.Add(...)`

### 3.2 Search for SciPy HiGHS in `backend/app/`
An exhaustive code search across all Python files in `backend/app/` returned **zero matches** for `scipy.optimize`, `linprog`, or `HiGHS`.
While `scipy` is present in `backend/requirements.txt` (used elsewhere for statistical utilities), it plays **no role** in the production water allocation engine.

### 3.3 Active Solver Characteristics (OR-Tools GLOP)
- **Engine:** Google OR-Tools GLOP (Google Linear Optimization Package), an industrial-strength dual simplex LP solver.
- **Formulation:** Hard upper/lower bounds, supply conservation constraints, and soft shortfall penalties when minimum requirements cannot be met simultaneously.
- **Testing:** 87 tests in `tests/test_lp_allocator.py` validate the OR-Tools GLOP formulation across normal, deficit, empty, and infeasible scenarios.

---

## 4. Reconciled Technology Matrix

| System Subsystem | Erroneous Audit Claim | Actual Production Implementation |
| :--- | :--- | :--- |
| **Frontend UI Framework** | React 18 | **React 19.3.0 (React 19)** |
| **Frontend Tooling** | Vite 5 | **Vite 8.3.0** |
| **Frontend Typing** | TypeScript 5 | **TypeScript 6.0.2** |
| **Frontend Routing** | React Router 6 | **React Router 7.18.4** |
| **Water Allocation LP** | SciPy `linprog` (HiGHS) | **Google OR-Tools GLOP (`pywraplp`)** |

---

## 5. Verdict

**Technology Verification Status: DISCREPANCIES RECONCILED (Documentation Errors Corrected; Production Codebase is React 19 & OR-Tools GLOP)**
