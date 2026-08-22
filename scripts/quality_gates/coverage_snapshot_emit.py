#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""coverage_snapshot_emit.py — emit per-(repo, surface) coverage JSON lines.

Called by coverage_snapshot.sh, one invocation per repo. Reads the workspace
SSOT (coverage_targets.yaml), parses the repo's coverage.xml, computes the
per-surface aggregate using the same logic as check_coverage_targets.py, and
prints one JSON line per surface present in the repo.

Output schema (one JSON object per line on stdout):
    {
      "repo": str,
      "surface": str,
      "target_pct": int,
      "actual_pct": float,
      "files_matched": int,
      "lines_covered": int,
      "lines_valid": int,
      "snapshot_at": str  # ISO-8601 UTC
    }

Plan: deployment_and_qg_strategy_implementation_2026_05_13.md Phase 8.E.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from check_coverage_targets import (
    _compute_surface_result,
    _load_local_surfaces,
    _load_targets,
    _parse_coverage_xml,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit per-surface coverage rows for one repo")
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--coverage-xml", type=Path, required=True)
    parser.add_argument("--snapshot-at", required=True)
    parser.add_argument(
        "--targets-path",
        type=Path,
        default=SCRIPT_DIR / "coverage_targets.yaml",
    )
    ns = parser.parse_args()

    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    repo_name: str = cast(str, ns.repo)
    coverage_xml: Path = cast(Path, ns.coverage_xml)
    snapshot_at: str = cast(str, ns.snapshot_at)
    targets_path: Path = cast(Path, ns.targets_path)

    if not coverage_xml.exists():
        print(f"WARN: coverage.xml not found at {coverage_xml}", file=sys.stderr)
        return 0

    surfaces = _load_targets(targets_path)
    file_coverages = _parse_coverage_xml(coverage_xml)
    if not file_coverages:
        print(f"WARN: no <class> entries in {coverage_xml}", file=sys.stderr)
        return 0

    repo_path = workspace_root / repo_name
    enabled = _load_local_surfaces(repo_path)

    for surface in surfaces:
        if enabled is not None and surface.name not in enabled:
            continue
        result = _compute_surface_result(surface, repo_name, file_coverages)
        if result is None:
            continue
        row = {
            "repo": repo_name,
            "surface": result.surface,
            "target_pct": result.target_pct,
            "actual_pct": round(result.actual_pct, 2),
            "files_matched": result.files_matched,
            "lines_covered": result.lines_covered,
            "lines_valid": result.lines_valid,
            "snapshot_at": snapshot_at,
        }
        print(json.dumps(row))

    return 0


if __name__ == "__main__":
    sys.exit(main())
