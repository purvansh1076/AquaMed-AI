#!/usr/bin/env python3
"""Fix lp_allocator.py fallback chain."""
import pathlib

p = pathlib.Path(__file__).resolve().parent.parent / "backend" / "app" / "allocation" / "lp_allocator.py"
content = p.read_text()

old_section = """        # ── Main LP solve ─────────────────────────────────────────────────────
        try:
            result = self._solve_lp()
        except Exception as exc:  # noqa: BLE001
            logger.error("LP solver raised unexpectedly: %s", exc, exc_info=True)
            result = self._proportional_fallback(
                solver_status=SolverStatus.ERROR,
                method="proportional_fallback",
            )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        result.solver_wall_time_ms = elapsed_ms"""

new_section = """        # ── Main LP solve ─────────────────────────────────────────────────────
        try:
            result = self._solve_lp()
        except Exception as exc:  # noqa: BLE001
            logger.error("LP solver raised unexpectedly: %s", exc, exc_info=True)
            result = self._proportional_fallback(
                solver_status=SolverStatus.ERROR,
                method="proportional_fallback",
            )

        # ── Fallback chain: lp_optimal → lp_relaxed → proportional → empty ────
        if result.solver_status not in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
            # Try LP-relaxed fallback (soft minimum penalties)
            if result.method != "lp_relaxed":
                logger.warning(
                    "LP solver returned %s — trying lp_relaxed fallback.",
                    result.solver_status.value,
                )
                result = self._lp_relaxed_fallback()
            # If lp_relaxed also failed (or was already used), use proportional
            if result.solver_status not in (SolverStatus.OPTIMAL, SolverStatus.FEASIBLE):
                logger.warning(
                    "lp_relaxed fallback also returned %s — using proportional fallback.",
                    result.solver_status.value,
                )
                result = self._proportional_fallback(
                    solver_status=SolverStatus.ERROR,
                    method="proportional_fallback",
                )

        elapsed_ms = (time.perf_counter() - t0) * 1000
        result.solver_wall_time_ms = elapsed_ms"""

if old_section in content:
    content = content.replace(old_section, new_section)
    p.write_text(content)
    print('SUCCESS: Replacement done')
else:
    print('FAIL: Old section not found')
    # Debug: show what's around line 240
    lines = content.split('\n')
    for i in range(238, 255):
        print(f'{i+1}: {repr(lines[i])}')