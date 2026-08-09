#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Extraction-count regression gate for the openapi/config-registry regen outputs.

Formalizes the MANUAL checkpoint used in
``plans/active/issues/venv_workspace_openapi_regen_batch11_findings_2026_08_09.md``
("If the fresh count is LOWER than the committed baseline for ANY tracked output
file, DO NOT commit") into a real, non-discretionary script, instead of relying on
a worker's own in-the-moment judgment call under time pressure.

**Why not the retired ``check_openapi_drift.py``**: that script hashes
``unified-trading-api/openapi.json`` (61-path slim facade) against
``unified-trading-system-ui/lib/registry/openapi.json`` (479-path aggregated UI
mirror) — two structurally-different files by design, so full-hash comparison
always shows drift (deprecated 2026-05-16, see that script's own docstring +
``plans/active/issues/openapi_mirror_drift_2026_05_16.md``). This gate checks a
different, actually-comparable pair: the AGGREGATE EXTRACTION COUNTS of the two
files ``generate-unified-openapi.sh`` itself produces
(``unified-trading-system.openapi.json``, ``config-registry.json``) against the
git-committed baseline of those SAME files — a same-file-across-time comparison,
not a cross-file structural one.

Semantics: for each tracked output file, extract a small set of aggregate counts
(path/schema counts for the openapi spec; config/repo counts for the registry),
compare against the git-committed baseline (``--baseline-ref``, default HEAD), and
FAIL if any fresh count is LOWER than the committed baseline. A count going UP is
never a failure (new services/paths/schemas are expected growth). A file with no
committed baseline yet (brand new) is reported informationally, never failed.

Usage::

    # After running generate-unified-openapi.sh (which overwrites the tracked
    # files in-place in the unified-api-contracts working tree), before committing:
    python scripts/quality_gates/check_extraction_count_regression.py \\
        --workspace-root /path/to/workspace

    # --warn-only for transition/manual investigation (always exits 0)
    python scripts/quality_gates/check_extraction_count_regression.py --warn-only

Exit codes: 0 = no regression (or --warn-only); 1 = regression detected;
2 = a tracked fresh file is missing or unparseable (the generator didn't run, or
failed partway through).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Final

SCRIPT_DIR: Final[Path] = Path(__file__).resolve().parent
PM_ROOT: Final[Path] = SCRIPT_DIR.parent.parent
DEFAULT_WORKSPACE_ROOT: Final[Path] = PM_ROOT.parent
DEFAULT_BASELINE_REF: Final[str] = "HEAD"


def _config_registry_metrics(doc: dict[str, object]) -> dict[str, int]:
    meta = doc.get("_meta", {})
    if not isinstance(meta, dict):
        meta = {}
    return {
        "total_configs": _as_int(meta.get("total_configs")),
        "total_repos": _as_int(meta.get("total_repos")),
    }


def _as_int(value: object) -> int:
    return value if isinstance(value, int) else 0


def _openapi_spec_metrics(doc: dict[str, object]) -> dict[str, int]:
    paths = doc.get("paths", {})
    components = doc.get("components", {})
    schemas = components.get("schemas", {}) if isinstance(components, dict) else {}
    return {
        "paths": len(paths) if isinstance(paths, dict) else 0,
        "schemas": len(schemas) if isinstance(schemas, dict) else 0,
    }


class TrackedFile:
    def __init__(self, relpath: str, metrics_fn: Callable[[dict[str, object]], dict[str, int]]) -> None:
        self.relpath = relpath
        self.metrics_fn = metrics_fn


TRACKED_FILES: Final[list[TrackedFile]] = [
    TrackedFile("openapi/config-registry.json", _config_registry_metrics),
    TrackedFile("openapi/unified-trading-system.openapi.json", _openapi_spec_metrics),
]


def _git_show(repo_root: Path, ref: str, relpath: str) -> str | None:
    """Returns the committed file content at ref, or None if it doesn't exist there."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "show", f"{ref}:{relpath}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _repo_key_diff(baseline_doc: dict[str, object], fresh_doc: dict[str, object]) -> tuple[list[str], list[str]]:
    """For config-registry.json only: which top-level configs_by_repo keys were added/removed."""
    baseline_repos = baseline_doc.get("configs_by_repo", {})
    fresh_repos = fresh_doc.get("configs_by_repo", {})
    if not isinstance(baseline_repos, dict) or not isinstance(fresh_repos, dict):
        return [], []
    added = sorted(set(fresh_repos) - set(baseline_repos))
    removed = sorted(set(baseline_repos) - set(fresh_repos))
    return added, removed


def check_extraction_count_regression(
    repo_root: Path,
    baseline_ref: str,
    warn_only: bool,
) -> int:
    any_regression = False
    for tracked in TRACKED_FILES:
        fresh_path = repo_root / tracked.relpath
        if not fresh_path.is_file():
            print(f"ERROR: fresh output missing: {fresh_path} (did the generator run?)", file=sys.stderr)
            return 2

        try:
            fresh_doc = json.loads(fresh_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"ERROR: fresh output is not valid JSON: {fresh_path} ({exc})", file=sys.stderr)
            return 2

        baseline_text = _git_show(repo_root, baseline_ref, tracked.relpath)
        if baseline_text is None:
            print(f"(i) {tracked.relpath}: no baseline at {baseline_ref} (new file) — skipping regression check.")
            continue

        try:
            baseline_doc = json.loads(baseline_text)
        except json.JSONDecodeError as exc:
            print(
                f"ERROR: committed baseline is not valid JSON: {tracked.relpath}@{baseline_ref} ({exc})",
                file=sys.stderr,
            )
            return 2

        baseline_metrics = tracked.metrics_fn(baseline_doc)
        fresh_metrics = tracked.metrics_fn(fresh_doc)

        print(f"\n{tracked.relpath}:")
        file_regressed = False
        for key, baseline_value in baseline_metrics.items():
            fresh_value = fresh_metrics.get(key, 0)
            delta = fresh_value - baseline_value
            arrow = "→" if delta == 0 else ("↑" if delta > 0 else "↓")
            print(f"  {key}: {baseline_value} {arrow} {fresh_value} ({delta:+d})")
            if fresh_value < baseline_value:
                file_regressed = True

        if tracked.relpath.endswith("config-registry.json"):
            added, removed = _repo_key_diff(baseline_doc, fresh_doc)
            if added:
                print(f"  repos added:   {added}")
            if removed:
                print(f"  repos removed: {removed}")

        if file_regressed:
            any_regression = True
            print("  ❌ REGRESSION — a fresh extraction count dropped below the committed baseline.")

    print()
    if any_regression:
        if warn_only:
            print("⚠️  Extraction-count regression detected (--warn-only set — exiting 0).")
            return 0
        print(
            "❌ Extraction-count regression — DO NOT commit these outputs. Investigate (a genuine repo/service\n"
            "   consolidation must be independently confirmed before committing; an incomplete .venv-workspace\n"
            "   silently under-extracts and looks identical to this failure — see\n"
            "   venv_workspace_openapi_regen_batch11_findings_2026_08_09.md for the exact failure mode this closes)."
        )
        return 1

    print("✅ No extraction-count regression — every tracked metric is at or above its committed baseline.")
    return 0


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="Workspace root containing the unified-api-contracts sibling clone",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override: unified-api-contracts repo root directly (default: <workspace-root>/unified-api-contracts)",
    )
    parser.add_argument(
        "--baseline-ref",
        default=DEFAULT_BASELINE_REF,
        help=f"Git ref to compare against (default: {DEFAULT_BASELINE_REF})",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print regression status but always exit 0",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = _parse_args(argv)
    workspace_root: Path = ns.workspace_root.resolve()
    repo_root: Path = (ns.repo_root or (workspace_root / "unified-api-contracts")).resolve()
    baseline_ref: str = ns.baseline_ref
    warn_only: bool = ns.warn_only

    if not (repo_root / ".git").exists():
        print(f"ERROR: not a git repo (no .git): {repo_root}", file=sys.stderr)
        return 2

    return check_extraction_count_regression(repo_root, baseline_ref, warn_only)


if __name__ == "__main__":
    sys.exit(main())
