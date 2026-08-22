#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
compute-epic-readiness.py
=========================
Aggregates per-repo asset_group_readiness data into epic-level % completion.

Usage:
    python unified-trading-pm/scripts/compute-epic-readiness.py [--output-dir <path>]

Reads:
    unified-trading-pm/codex/10-audit/repos/*.yaml   (per-repo checklists)
    unified-trading-pm/codex/11-project-management/epics/*-epic.yaml   (epic definitions)

Writes:
    unified-trading-pm/codex/11-project-management/epics/{epic_id}-status.yaml

SSOT: unified-trading-pm/codex/ (unified-trading-codex was archived and folded into PM)
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PM_ROOT = Path(__file__).parent.parent  # unified-trading-pm/

REPOS_DIR = PM_ROOT / "codex" / "10-audit" / "repos"
EPICS_DIR = PM_ROOT / "codex" / "11-project-management" / "epics"

CR_ORDINALS: dict[str, int] = {
    "cr0": 0,
    "cr1": 1,
    "cr2": 2,
    "cr3": 3,
    "cr4": 4,
    "cr5": 5,
}

BR_ORDINALS: dict[str, int] = {
    "br0": 0,
    "br1": 1,
    "br2": 2,
    "br3": 3,
    "br4": 4,
    "br5": 5,
    "br6": 6,
    "br7": 7,
    "br8": 8,
    "na": -1,  # not applicable — always satisfied
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data: dict[str, Any] | None = cast(dict[str, Any] | None, yaml.safe_load(f))
    return data if data is not None else {}


def load_all_repos() -> dict[str, dict[str, Any]]:
    """Return mapping of repo_name -> checklist YAML dict."""
    repos: dict[str, dict[str, Any]] = {}
    for yaml_file in REPOS_DIR.glob("*.yaml"):
        data = load_yaml(yaml_file)
        repo_name = data.get("repo") or yaml_file.stem
        repos[repo_name] = data
    return repos


def load_all_epics() -> list[dict[str, Any]]:
    """Return list of epic definition dicts (skips epic-schema.yaml and *-status.yaml)."""
    epics = []
    for yaml_file in sorted(EPICS_DIR.glob("*-epic.yaml")):
        epics.append(load_yaml(yaml_file))
    return epics


def cr_ordinal(stage: str | None) -> int:
    if not stage:
        return 0
    return CR_ORDINALS.get(stage.lower(), 0)


def br_ordinal(stage: str | None) -> int:
    if not stage:
        return 0
    return BR_ORDINALS.get(stage.lower(), 0)


def get_branch_status(
    repo_data: dict[str, Any],
    asset_group: str,
) -> dict[str, Any]:
    """Return branch_status dict for the given asset class (or core fallback)."""
    acr: dict[str, Any] = cast(dict[str, Any], repo_data.get("asset_group_readiness") or {})
    # Prefer exact class key, fall back to "core"
    class_data: dict[str, Any] = cast(dict[str, Any], acr.get(asset_group) or acr.get("core") or {})
    return cast(dict[str, Any], class_data.get("branch_status") or {})


def is_repo_complete(
    repo_data: dict[str, Any],
    min_cr_stage: str,
    min_br_stage: str,
    asset_group: str,
) -> tuple[bool, str]:
    """
    Return (is_complete, reason) for a single required repo entry.

    Complete when ALL of:
    1. code_readiness.current_stage ordinal >= min_cr_stage ordinal
    2. (if min_br_stage != na) business_readiness.current_stage >= min_br_stage
    3. asset_group_readiness.{asset_group|core}.branch_status.main.quickmerged = true
    """
    # ── CR check ──────────────────────────────────────────────────────────
    cr_current: str = cast(
        str, cast(dict[str, Any], repo_data.get("code_readiness") or {}).get("current_stage") or "CR0"
    )
    if cr_ordinal(cr_current) < cr_ordinal(min_cr_stage):
        return False, f"CR stage: {cr_current} (need {min_cr_stage.upper()})"

    # ── BR check ──────────────────────────────────────────────────────────
    if min_br_stage.lower() != "na":
        br_current: str = cast(
            str, cast(dict[str, Any], repo_data.get("business_readiness") or {}).get("current_stage") or "BR0"
        )
        if br_ordinal(br_current) < br_ordinal(min_br_stage):
            return False, f"BR stage: {br_current} (need {min_br_stage.upper()})"

    # ── Branch gate ───────────────────────────────────────────────────────
    branch_status = get_branch_status(repo_data, asset_group)
    main_status: dict[str, Any] = cast(dict[str, Any], branch_status.get("main") or {})
    if not main_status.get("quickmerged", False):
        return False, "branch_status.main.quickmerged = false"

    return True, ""


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------


def compute_epic(
    epic: dict[str, Any],
    repos: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compute readiness status for a single epic definition."""
    epic_id: str = cast(str, epic["epic_id"])
    required: list[dict[str, Any]] = cast(list[dict[str, Any]], epic.get("required_repos") or [])
    optional: list[dict[str, Any]] = cast(list[dict[str, Any]], epic.get("optional_repos") or [])

    total_required = len(required)
    completed = 0
    blocking_repos: list[dict[str, Any]] = []
    completed_repos: list[str] = []

    for req in required:
        repo_name: str = cast(str, req["repo"])
        min_cr: str = cast(str, req.get("min_stage") or "cr5")
        min_br: str = cast(str, req.get("min_br_stage") or "na")
        asset_group: str = cast(str, req.get("asset_group") or "core")

        repo_data = repos.get(repo_name)
        if repo_data is None:
            blocking_repos.append(
                {
                    "repo": repo_name,
                    "asset_group": asset_group,
                    "blocking_reason": "No per-repo YAML found in 10-audit/repos/",
                    "cr_current": None,
                    "br_current": None,
                    "main_quickmerged": False,
                }
            )
            continue

        ok, reason = is_repo_complete(repo_data, min_cr, min_br, asset_group)
        if ok:
            completed += 1
            completed_repos.append(repo_name)
        else:
            cr_current = cast(
                str, cast(dict[str, Any], repo_data.get("code_readiness") or {}).get("current_stage") or "CR0"
            )
            br_current = cast(
                str, cast(dict[str, Any], repo_data.get("business_readiness") or {}).get("current_stage") or "BR0"
            )
            branch_status = get_branch_status(repo_data, asset_group)
            main_qm: bool = cast(
                bool, cast(dict[str, Any], branch_status.get("main") or {}).get("quickmerged") or False
            )
            blocking_repos.append(
                {
                    "repo": repo_name,
                    "asset_group": asset_group,
                    "blocking_reason": reason,
                    "cr_current": cr_current,
                    "cr_required": min_cr.upper(),
                    "br_current": br_current,
                    "br_required": min_br.upper() if min_br.lower() != "na" else "na",
                    "main_quickmerged": main_qm,
                }
            )

    epic_pct = round(completed / total_required * 100) if total_required > 0 else 0

    # Optional repos summary
    optional_status: list[dict[str, Any]] = []
    for opt in optional:
        repo_name = cast(str, opt["repo"])
        asset_group = cast(str, opt.get("asset_group") or "")
        repo_data = repos.get(repo_name)
        cr_current = (
            cast(str, cast(dict[str, Any], repo_data.get("code_readiness") or {}).get("current_stage") or "CR0")
            if repo_data
            else None
        )
        optional_status.append(
            {
                "repo": repo_name,
                "asset_group": asset_group,
                "note": opt.get("note", ""),
                "cr_current": cr_current,
                "yaml_present": repo_data is not None,
            }
        )

    return {
        "epic_id": epic_id,
        "display_name": epic.get("display_name", epic_id),
        "mvp_priority": epic.get("mvp_priority", 99),
        "computed_at": datetime.now(UTC).isoformat(),
        "epic_pct": epic_pct,
        "total_required": total_required,
        "completed": completed,
        "epic_complete": epic_pct == 100,
        "business_requirement_minimum": epic.get("business_requirement_minimum", "br5_pnl_backtest"),
        "completion_criteria": epic.get("completion_criteria", {}),  # noqa: qg-empty-fallback
        "blocking_repos": blocking_repos,
        "completed_repos": completed_repos,
        "optional_repos_status": optional_status,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


class _ParsedArgs(argparse.Namespace):
    output_dir: Path
    epic: str | None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute epic readiness from per-repo YAML checklists")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=EPICS_DIR,
        dest="output_dir",
        help="Directory to write {epic_id}-status.yaml files (default: epics/)",
    )
    parser.add_argument(
        "--epic",
        type=str,
        default=None,
        help="Compute a single epic by ID (e.g. defi). Default: all epics.",
    )
    args = parser.parse_args(argv, namespace=_ParsedArgs())

    if not REPOS_DIR.exists():
        print(f"ERROR: repos dir not found: {REPOS_DIR}", file=sys.stderr)
        return 1
    if not EPICS_DIR.exists():
        print(f"ERROR: epics dir not found: {EPICS_DIR}", file=sys.stderr)
        return 1

    repos = load_all_repos()
    epics = load_all_epics()

    if not epics:
        print("ERROR: no *-epic.yaml files found in epics/", file=sys.stderr)
        return 1

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    any_errors = False

    for epic in epics:
        epic_id: str = cast(str, epic.get("epic_id") or "unknown")
        if args.epic and epic_id != args.epic:
            continue

        result = compute_epic(epic, repos)

        out_path = output_dir / f"{epic_id}-status.yaml"
        with out_path.open("w") as f:
            yaml.dump(result, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        status_icon = "✅" if result["epic_complete"] else "⬜"
        priority_tag = f"[P{result['mvp_priority']}]" if result["mvp_priority"] <= 4 else ""
        print(
            f"{status_icon} {priority_tag} {result['display_name']}: "
            f"{result['epic_pct']}% ({result['completed']}/{result['total_required']} repos) "
            f"→ {out_path.relative_to(PM_ROOT)}"
        )
        if result["blocking_repos"]:
            blocking: list[dict[str, Any]] = cast(list[dict[str, Any]], result["blocking_repos"])
            for br in blocking:
                print(f"   ✗ {br['repo']} [{br['asset_group']}]: {br['blocking_reason']}")

    return 1 if any_errors else 0


if __name__ == "__main__":
    sys.exit(main())
