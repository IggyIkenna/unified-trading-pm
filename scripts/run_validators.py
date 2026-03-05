#!/usr/bin/env python3
"""Run validators by scope, repo-type, or specific check.

plans_to_deployable_unified_audit.plan.md Phase 6, 8.

Usage:
    python run_validators.py --scope all
    python run_validators.py --scope checklist
    python run_validators.py --repo-type service
    python run_validators.py --check-codex-refs  # Phase 8: detect stale codex refs

Exit: 0 = all pass, 1 = failures.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VALIDATORS_DIR = SCRIPT_DIR / "validators"
PM_ROOT = SCRIPT_DIR.parent
WORKSPACE_ROOT = PM_ROOT.parent


def run_checklist_validator(configs_path: Path | None = None) -> int:
    configs = configs_path or WORKSPACE_ROOT / "deployment-service" / "configs"
    if not configs.is_dir():
        print(f"Skip: configs not found {configs}", file=sys.stderr)
        return 0
    script = VALIDATORS_DIR / "validate_checklist_phase9.py"
    if not script.is_file():
        print(f"Skip: {script} not found", file=sys.stderr)
        return 0
    return subprocess.run(
        [sys.executable, str(script), "--configs", str(configs)],
        cwd=str(PM_ROOT),
    ).returncode


def run_manifest_validator() -> int:
    manifest = PM_ROOT / "workspace-manifest.json"
    if not manifest.is_file():
        print(f"Skip: manifest not found {manifest}", file=sys.stderr)
        return 0
    script = VALIDATORS_DIR / "validate_workspace_manifest.py"
    if not script.is_file():
        return 0
    return subprocess.run([sys.executable, str(script)], cwd=str(PM_ROOT)).returncode


def run_plan_links_validator() -> int:
    script = VALIDATORS_DIR / "validate_plan_links.py"
    if not script.is_file():
        return 0
    plans_dir = PM_ROOT / "plans" / "active"
    if not plans_dir.is_dir():
        return 0
    return subprocess.run(
        [sys.executable, str(script), "--workspace-root", str(WORKSPACE_ROOT)],
        cwd=str(PM_ROOT),
    ).returncode


def main() -> int:

    parser = argparse.ArgumentParser()
    parser.add_argument("--scope", choices=["all", "checklist", "manifest"], default="all")
    parser.add_argument("--repo-type", help="Filter by repo type (service, library, ui)")
    parser.add_argument("--check-codex-refs", action="store_true", help="Phase 8: detect stale codex refs")
    parser.add_argument("--configs", type=Path, help="Path to deployment configs")
    args = parser.parse_args()

    failed = 0
    if args.scope in ("all", "checklist"):
        failed |= run_checklist_validator(args.configs)
    if args.scope in ("all", "manifest"):
        failed |= run_manifest_validator()
    if args.scope == "all":
        failed |= run_plan_links_validator()
    if args.check_codex_refs:
        # Phase 8: placeholder - implement when codex-ref tracking exists
        print("--check-codex-refs: not yet implemented (Approach A: validator only)")
    return min(failed, 1)


if __name__ == "__main__":
    sys.exit(main())
