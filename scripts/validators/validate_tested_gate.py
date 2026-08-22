#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate Tested gate: pytest --collect-only exits 0 (no import/path errors).

Phase 9: plans_to_deployable_unified_audit.plan.md
Criteria: pytest --collect-only -q exits 0 per repo.

Usage:
    python validate_tested_gate.py [--repo-dir PATH]

Exit: 0 = collect OK, 1 = collect failed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import cast


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-dir", type=Path, default=Path(__file__).resolve().parent.parent.parent)
    args = parser.parse_args()

    repo: Path = cast(Path, args.repo_dir)
    if not (repo / "pyproject.toml").exists():
        print(f"Skip: no pyproject.toml in {repo}", file=sys.stderr)
        return 0

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=str(repo),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        print(f"FAIL: pytest --collect-only failed: {result.stderr or result.stdout}", file=sys.stderr)
        return 1
    print("OK: pytest --collect-only passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
