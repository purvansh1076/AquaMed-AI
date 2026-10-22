#!/usr/bin/env python3
"""Add min_nash_improvement and concession_progress_threshold to NegotiationConfig."""
import pathlib

p = pathlib.Path(__file__).resolve().parent.parent / "backend" / "app" / "negotiation" / "negotiation_types.py"
content = p.read_text()

# Find the line with stagnation_rounds and add new params after it
# Locate the stagnation_rounds line
idx = content.find("stagnation_rounds: int = 2")
if idx == -1:
    print("ERROR: stagnation_rounds not found")
    sys.exit(1)

# Find the line after it (concession_scale)
search_start = idx + len("stagnation_rounds: int = 2\n")
concession_scale_line = content.find("concession_scale: float = 1.0", search_start)
if concession_scale_line == -1:
    print("ERROR: concession_scale not found after stagnation_rounds")
    sys.exit(1)

# Insert new parameters before concession_scale
new_text = """    stagnation_rounds: int = 2
    min_nash_improvement: float = 1e-4
        Minimum absolute improvement in Nash log-objective to count as "improvement".
        Default 1e-4 (avoids counting negligible numerical differences as progress).
    concession_progress_threshold: float = 0.1
        Minimum fraction of total concession gap that must be made to prevent
        premature stagnation termination. Default 0.1 (10% of remaining gap).
    concession_scale: float = 1.0"""

# Replace
new_content = content[:concession_scale_line] + new_content if False else (
    content[:concession_scale_line] + new_text + content[concession_scale_line:]
    if content[:concession_scale_line].endswith("\n") and content[concession_scale_line:concession_scale_line+1] == "\n"
    else content[:concession_scale_line - 1] + new_text + content[concession_scale_line - 1:]
)

# Simpler approach: just insert after the stagnation_rounds line
lines = content.split("\n")
new_lines = []
inserted = False
for i, line in enumerate(lines):
    new_lines.append(line)
    if not inserted and line.strip() == "stagnation_rounds: int = 2":
        # Add the new lines after this one
        new_lines.append("")
        new_lines.append("    min_nash_improvement: float = 1e-4")
        new_lines.append("        Minimum absolute improvement in Nash log-objective to count as \"improvement\".")
        new_lines.append("        Default 1e-4 (avoids counting negligible numerical differences as progress).")
        new_lines.append("")
        new_lines.append("    concession_progress_threshold: float = 0.1")
        new_lines.append("        Minimum fraction of total concession gap that must be made to prevent")
        new_lines.append("        premature stagnation termination. Default 0.1 (10% of remaining gap).")
        new_lines.append("")
        inserted = True

if not inserted:
    print("WARNING: Insertion point not found")
else:
    content = "\n".join(new_lines)

p.write_text(content)
print("Done adding config parameters")