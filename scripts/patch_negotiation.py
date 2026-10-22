#!/usr/bin/env python3
"""Patch negotiation_engine.py with improved stagnation logic."""
import pathlib

p = pathlib.Path(__file__).resolve().parent.parent / "backend" / "app" / "negotiation" / "negotiation_engine.py"
content = p.read_text()

old = """            # Update best if improved
            if proposal.is_improvement:
                best_allocation = dict(new_allocation)
                best_nash = current_nash
                best_utilities = dict(current_utilities)
                best_responses = list(current_responses)
                best_fairness = current_fairness
                stagnation_count = 0
                session.best_allocation = dict(best_allocation)
                session.best_nash_objective = best_nash
            else:
                stagnation_count += 1
                logger.info(
                    "NegotiationEngine[r%d]: no improvement (stagnation=%d/%d)",
                    round_num, stagnation_count, self._config.stagnation_rounds,
                )

            # Check termination conditions"""

new = """            # Update best if improved (using configured minimum delta)
            improvement = is_nash_improvement(
                current_nash, best_nash, min_delta=self._config.min_nash_improvement,
            )
            concession_progress = self._check_concession_progress(
                current_allocation, current_responses,
                best_allocation, best_nash,
            )
            
            if improvement or concession_progress:
                best_allocation = dict(new_allocation)
                best_nash = current_nash
                best_utilities = dict(current_utilities)
                best_responses = list(current_responses)
                best_fairness = current_fairness
                stagnation_count = 0
                session.best_allocation = dict(best_allocation)
                session.best_nash_objective = best_nash
            else:
                stagnation_count += 1
                logger.info(
                    "NegotiationEngine[r%d]: no improvement (stagnation=%d/%d)",
                    round_num, stagnation_count, self._config.stagnation_rounds,
                )

            # Check termination conditions"""

assert old in content, "Old string not found in file!"
content = content.replace(old, new)
p.write_text(content)
print("Patch applied successfully")
" 2>&1 | head -5