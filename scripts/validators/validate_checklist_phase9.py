#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate deployment checklists have phase_9_deployable_enhancements (items 38-41).

GATE: plans_to_deployable_unified_audit.md checklist-enhancements.
All service checklists must have: data_availability, gap_filling, recovery_processes, security_audit_trail.

Usage:
    python validate_checklist_phase9.py
    python validate_checklist_phase9.py --configs /path/to/configs

Exit: 0 = all pass, 1 = missing sections.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import cast

import yaml

# YAML typing: safe_load returns Any; cast at boundary
YamlDict = dict[str, object]

REQUIRED_ITEMS = [
    "item_38_data_availability",
    "item_39_gap_filling",
    "item_40_recovery_processes",
    "item_41_security_audit_trail",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate checklist phase_9 sections")
    parser.add_argument(
        "--configs",
        type=Path,
        default=Path(__file__).resolve().parent.parent.parent.parent / "deployment-service" / "configs",
        help="Path to deployment configs dir",
    )
    args = parser.parse_args()

    configs: Path = cast(Path, args.configs)
    if not configs.is_dir():
        print(f"ERROR: Configs dir not found: {configs}", file=sys.stderr)
        return 1

    failed: list[str] = []
    for path in sorted(configs.glob("checklist.*.yaml")):
        name = path.name
        if "template" in name or "prerequisites" in name:
            continue

        try:
            with open(path) as f:
                data: YamlDict = cast(YamlDict, yaml.safe_load(f))
        except (OSError, yaml.YAMLError) as e:
            failed.append(f"{name}: parse error: {e}")
            continue

        phase9_raw: object | None = data.get("phase_9_deployable_enhancements")
        if not phase9_raw or not isinstance(phase9_raw, dict):
            failed.append(f"{name}: missing phase_9_deployable_enhancements")
            continue

        phase9: dict[str, object] = phase9_raw
        missing = [i for i in REQUIRED_ITEMS if i not in phase9]
        if missing:
            failed.append(f"{name}: missing items: {', '.join(missing)}")

    if failed:
        for msg in failed:
            print(f"FAIL: {msg}", file=sys.stderr)
        return 1

    print("OK: All checklists have phase_9_deployable_enhancements (items 38-41)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
