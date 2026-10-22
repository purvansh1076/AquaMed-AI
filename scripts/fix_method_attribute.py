#!/usr/bin/env python3
"""Fix result.method -> result.allocation_method in lp_allocator.py"""
import pathlib

p = pathlib.Path(__file__).resolve().parent.parent / "backend" / "app" / "allocation" / "lp_allocator.py"
content = p.read_text()

# Replace result.method with result.allocation_method
content = content.replace('result.method', 'result.allocation_method')

p.write_text(content)
print('Replacement done')
print(f'File: {p}')