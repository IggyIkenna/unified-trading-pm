#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""fix-cloudbuild-coverage.py — Add coverage enforcement to library cloudbuild.yaml inline pytest.

Library cloudbuild.yaml files use `python:3.13-slim` with inline pytest:
    python -m pytest tests/ -v --tb=short

These have no --cov-fail-under, so coverage is never enforced in Cloud Build.
This script adds:
    --cov=<SOURCE_DIR> --cov-fail-under=<MIN_COVERAGE> --cov-report=xml --cov-report=term-missing

Where SOURCE_DIR and MIN_COVERAGE are read from the repo's scripts/quality-gates.sh.

Note: Library cloudbuild.yaml CANNOT call bash scripts/quality-gates.sh because
WORKSPACE_ROOT would resolve to / (parent of /workspace in Cloud Build). The canonical
quality-gates.sh stub requires unified-trading-pm at WORKSPACE_ROOT/../unified-trading-pm
which is not possible in Cloud Build without a preceding clone step. The pragmatic fix is
to enforce coverage directly in the inline pytest command.

Usage:
    python3 fix-cloudbuild-coverage.py [--dry-run] [--repo <name>]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]


def read_qg_config(repo_path: Path) -> tuple[str, int] | None:
    """Read SOURCE_DIR and MIN_COVERAGE from scripts/quality-gates.sh."""
    qg_sh = repo_path / "scripts" / "quality-gates.sh"
    if not qg_sh.exists():
        return None
    text = qg_sh.read_text()

    source_match = re.search(r"^SOURCE_DIR=[\"']?(\w+)[\"']?", text, re.MULTILINE)
    cov_match = re.search(r"^MIN_COVERAGE=[\"']?(\d+)[\"']?", text, re.MULTILINE)

    if not source_match or not cov_match:
        return None
    return source_match.group(1), int(cov_match.group(1))


def patch_cloudbuild(path: Path, dry_run: bool) -> tuple[str, str]:
    """Patch cloudbuild.yaml. Returns (status, detail)."""
    text = path.read_text()

    # Skip if already calls quality-gates.sh
    if "quality-gates.sh" in text:
        return "has_qg", ""

    # Skip if already has --cov-fail-under
    if "--cov-fail-under" in text:
        return "already_ok", ""

    # Check if it has inline pytest
    if "python -m pytest" not in text:
        return "no_pytest", ""

    # Read config from quality-gates.sh
    repo_path = path.parent
    config = read_qg_config(repo_path)
    if config is None:
        return "no_qg_sh", ""
    source_dir, min_coverage = config

    # Find and replace the pytest line(s)
    # Pattern: python -m pytest tests/ ... (with optional flags, possibly trailing whitespace)
    pytest_pattern = re.compile(
        r"(python -m pytest\s+tests/[^\n]*?)(\s*\n)",
        re.MULTILINE,
    )

    def add_cov_flags(m: re.Match[str]) -> str:
        existing = m.group(1)
        # Don't add if already has coverage flags
        if "--cov" in existing:
            return m.group(0)
        suffix = (
            f" \\\n"
            f"          --cov={source_dir} \\\n"
            f"          --cov-fail-under={min_coverage} \\\n"
            f"          --cov-report=xml \\\n"
            f"          --cov-report=term-missing"
        )
        return existing + suffix + m.group(2)

    new_text, count = pytest_pattern.subn(add_cov_flags, text)

    if count == 0:
        return "no_match", ""

    if not dry_run:
        path.write_text(new_text)

    return "patched", f"SOURCE_DIR={source_dir} MIN_COVERAGE={min_coverage}"


class _ParsedArgs(argparse.Namespace):
    dry_run: bool
    repo: str


def main() -> None:
    parser = argparse.ArgumentParser(description="Add coverage enforcement to library cloudbuild.yaml")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Preview changes without writing")
    parser.add_argument("--repo", default="", help="Only process this one repo")
    args = parser.parse_args(namespace=_ParsedArgs())

    if args.repo:
        cloudbuild_files = [WORKSPACE_ROOT / args.repo / "cloudbuild.yaml"]
    else:
        cloudbuild_files = sorted(WORKSPACE_ROOT.glob("*/cloudbuild.yaml"))

    counts: dict[str, int] = {}

    for cb_path in cloudbuild_files:
        repo = cb_path.parent.name
        if not cb_path.exists():
            continue

        status, detail = patch_cloudbuild(cb_path, dry_run=args.dry_run)
        counts[status] = counts.get(status, 0) + 1

        if status == "patched":
            verb = "DRY-RUN would patch" if args.dry_run else "Patched"
            print(f"  [FIX]    {repo} — {verb}: added coverage flags ({detail})")
        elif status == "has_qg":
            pass  # service pattern — uses quality-gates.sh, correct
        elif status == "already_ok":
            print(f"  [OK]     {repo} — already has --cov-fail-under")
        elif status == "no_pytest":
            pass  # no pytest in cloudbuild (service Docker build pattern)
        elif status == "no_qg_sh":
            print(f"  [WARN]   {repo} — has inline pytest but no scripts/quality-gates.sh (no MIN_COVERAGE)")
        elif status == "no_match":
            print(f"  [WARN]   {repo} — has pytest but regex didn't match; manual fix needed")

    patched = counts.get("patched", 0)
    no_qg_sh = counts.get("no_qg_sh", 0)
    no_match = counts.get("no_match", 0)

    print()
    print(
        f"Results: patched={patched}  already_ok={counts.get('already_ok', 0)}  "
        f"no_qg_sh={no_qg_sh}  no_match={no_match}"
    )

    if args.dry_run:
        print("\n(dry-run — no files written)")
    else:
        print(f"\n✅ Patched {patched} cloudbuild.yaml file(s).")
        if no_qg_sh or no_match:
            print(f"⚠️  {no_qg_sh + no_match} file(s) need manual attention.")
        sys.exit(1 if (no_qg_sh or no_match) else 0)


if __name__ == "__main__":
    main()
