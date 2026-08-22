#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Pre-commit hook: check Python file size (900 lines max per codex standard)."""

import contextlib
import sys

MAX_LINES = 900
errors: list[str] = []
for filepath in sys.argv[1:]:
    with contextlib.suppress(OSError):
        with open(filepath, encoding="utf-8", errors="ignore") as f:
            lines = sum(1 for _ in f)
        if lines > MAX_LINES:
            errors.append(f"  {filepath}: {lines} lines (max {MAX_LINES})")

if errors:
    print(f"ERROR: Files exceed {MAX_LINES} lines (split per SRP):")
    for e in errors:
        print(e)
    sys.exit(1)
