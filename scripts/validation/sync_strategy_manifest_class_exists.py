#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Set maturity.code.class_exists false when the manifest class_path module is absent.

Legacy strategy modules were removed or moved under v2; this keeps the SSOT manifest
consistent with ``validate-strategy-manifest.py`` file checks. Run from repo root:

  python3 scripts/validation/sync_strategy_manifest_class_exists.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PM_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = PM_ROOT / "strategy-manifest.json"
WORKSPACE_ROOT = PM_ROOT.parent
STRATEGY_SERVICE_ROOT = WORKSPACE_ROOT / "strategy-service"


def _module_file(class_path: str) -> Path:
    parts = class_path.rsplit(".", 1)
    module_dotted = parts[0]
    segments = module_dotted.split(".")
    return STRATEGY_SERVICE_ROOT / "/".join(segments[:-1]) / f"{segments[-1]}.py"


def _init_file(class_path: str) -> Path:
    parts = class_path.rsplit(".", 1)
    module_dotted = parts[0]
    segments = module_dotted.split(".")
    return STRATEGY_SERVICE_ROOT / "/".join(segments) / "__init__.py"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print counts only; do not write strategy-manifest.json",
    )
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1
    if not STRATEGY_SERVICE_ROOT.exists():
        print(
            f"strategy-service not found at {STRATEGY_SERVICE_ROOT} — nothing to sync",
            file=sys.stderr,
        )
        return 0

    raw = MANIFEST_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    strategies = data.get("strategies")
    if not isinstance(strategies, list):
        print("'strategies' must be a list", file=sys.stderr)
        return 1

    changed_ids: list[str] = []
    for strat in strategies:
        if not isinstance(strat, dict):
            continue
        maturity = strat.get("maturity")
        if not isinstance(maturity, dict):
            continue
        code = maturity.get("code")
        if not isinstance(code, dict) or not code.get("class_exists"):
            continue
        cp = strat.get("class_path")
        if not isinstance(cp, str):
            continue
        if _module_file(cp).exists() or _init_file(cp).exists():
            continue
        code["class_exists"] = False
        changed_ids.append(str(strat.get("strategy_id", "?")))

    if args.dry_run:
        print(f"would set class_exists=false for {len(changed_ids)} strategies")
        return 0

    if not changed_ids:
        print("strategy manifest already aligned (0 updates)")
        return 0

    MANIFEST_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"updated class_exists=false for {len(changed_ids)} strategies")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
