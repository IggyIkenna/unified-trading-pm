#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Check dependency alignment: derived manifest vs workspace-manifest.json.

Compares:
  1. Internal deps: pyproject.toml (derived) vs manifest repositories.<repo>.dependencies
  2. External deps: pyproject.toml vs workspace-constraints.toml / canonical-dependency-manifest.json

Run generate-derived-manifest.py first.

Usage:
    python check-dependency-alignment.py
    python check-dependency-alignment.py --repo instruments-service
    python check-dependency-alignment.py --json

Exit: 0 = aligned, 1 = misalignments found.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
DERIVED_PATH = PM_ROOT / "derived-dependency-manifest.json"
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CANONICAL_PATH = PM_ROOT / "canonical-dependency-manifest.json"

# Status values that exempt a repository from the disk-presence check.
# These statuses indicate the repo is intentionally not cloned under WORKSPACE_ROOT.
# Any other status (incl. "active", "scaffolded", missing/empty) → repo MUST be on disk.
DISK_ABSENT_OK_STATUSES: frozenset[str] = frozenset(
    {
        "archived",
        "deprecated",
        "deleted",
        "future",
    }
)

# Status prefixes that exempt a repo from disk-presence check (consolidations / merges).
DISK_ABSENT_OK_PREFIXES: tuple[str, ...] = (
    "consolidated-into-",
    "merged-into-",
    "pending-archive-into-",
)

# Per-repo external-dependency exceptions: (repo, normalized_pkg) -> the exact spec string
# that repo is INTENTIONALLY allowed to declare instead of the fleet canonical. An entry
# means "this repo's pyproject.toml deliberately diverges from workspace-constraints.toml,
# and that divergence is a reviewed, permanent decision", not a place to silence a
# misalignment you haven't investigated.
#
# SSOT for entries: dependency-exceptions.yaml (sibling file, same directory) — a
# YAML list + mandatory `justification`/`ssot` fields, not a hand-edited Python dict
# literal. Migrated 2026-07-14 (dependency_alignment_red_multi_repo_ceiling_drift_2026_07_13.md
# todo 3): the fastapi<0.138.0 exception recurred across 7 repos in one day, and a
# dict-literal entry per repo doesn't scale — a YAML row is a data change, not a
# Python-syntax change, and is easier to diff/scan/review. Loaded + schema-validated at
# import time (a malformed entry fails LOUD via _load_per_repo_exceptions, never
# silently ignored).
EXCEPTIONS_YAML_PATH = SCRIPT_DIR / "dependency-exceptions.yaml"

JsonDict = dict[str, object]


def _load_per_repo_exceptions(path: Path) -> dict[tuple[str, str], str]:
    """Load + schema-validate ``dependency-exceptions.yaml`` into the lookup dict
    ``check_alignment`` consumes: ``(repo, package) -> exact allowed spec string``.

    Raises ``SystemExit`` with a clear message on any schema violation (missing
    required field, wrong type, duplicate (repo, package) pair) — a malformed
    exceptions file must fail the gate loudly, never silently drop coverage.
    """
    if not path.is_file():
        # No exceptions file is a valid (if unusual) state — an empty exception set.
        return {}
    with path.open("r", encoding="utf-8") as fh:
        parsed = yaml.safe_load(fh)
    if not isinstance(parsed, dict) or not isinstance(parsed.get("exceptions"), list):
        print(f"ERROR: {path} must be a mapping with a top-level 'exceptions' list.", file=sys.stderr)
        raise SystemExit(2)
    required_fields = ("repo", "package", "spec", "justification", "ssot", "added")
    result: dict[tuple[str, str], str] = {}
    for i, entry in enumerate(cast(list[object], parsed["exceptions"])):
        if not isinstance(entry, dict):
            print(f"ERROR: {path} exceptions[{i}] is not a mapping.", file=sys.stderr)
            raise SystemExit(2)
        entry_d = cast(JsonDict, entry)
        missing = [f for f in required_fields if not entry_d.get(f)]
        if missing:
            print(f"ERROR: {path} exceptions[{i}] missing required field(s): {missing}.", file=sys.stderr)
            raise SystemExit(2)
        key = (str(entry_d["repo"]), str(entry_d["package"]))
        if key in result:
            print(f"ERROR: {path} has a duplicate exception entry for {key}.", file=sys.stderr)
            raise SystemExit(2)
        result[key] = str(entry_d["spec"])
    return result


PER_REPO_EXTERNAL_EXCEPTIONS: dict[tuple[str, str], str] = _load_per_repo_exceptions(EXCEPTIONS_YAML_PATH)


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jlist(val: object) -> list[JsonDict] | None:
    if isinstance(val, list):
        return cast(list[JsonDict], val)
    return None


def _jstr(val: object, default: str = "") -> str:
    return str(val) if val is not None else default


def load_json(path: Path) -> JsonDict:
    with open(path) as f:
        return cast(JsonDict, json.load(f))


def normalize(name: str) -> str:
    return name.lower().replace("_", "-").strip()


def main() -> int:  # noqa: C901
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", help="Check single repo only")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()
    repo_filter: str | None = cast(str | None, args.repo)
    json_output: bool = cast(bool, args.json)

    if not DERIVED_PATH.is_file():
        print(f"ERROR: Run generate-derived-manifest.py first. Missing: {DERIVED_PATH}", file=sys.stderr)
        return 1
    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    derived = load_json(DERIVED_PATH)
    manifest = load_json(MANIFEST_PATH)
    canonical: dict[str, str] = {}
    if CANONICAL_PATH.is_file():
        c = load_json(CANONICAL_PATH)
        ext_pkgs = _jlist(c.get("externalPackages")) or []
        for p in ext_pkgs:
            p_dict = _jdict(p)
            if p_dict:
                canonical[normalize(_jstr(p_dict.get("name")))] = _jstr(p_dict.get("versionRange"))

    repos_raw = _jdict(derived.get("repositories")) or {}
    repos: dict[str, object] = dict(repos_raw)
    if repo_filter:
        repos = {k: v for k, v in repos.items() if k == repo_filter}
        if not repos:
            print(f"ERROR: Repo not found: {repo_filter}", file=sys.stderr)
            return 1

    issues: list[dict[str, object]] = []
    disk_absent: list[dict[str, object]] = []
    manifest_repos_raw = _jdict(manifest.get("repositories")) or {}

    # Disk-presence check: every manifest repo (status=active or unspecified) MUST
    # have a directory under WORKSPACE_ROOT. Statuses in DISK_ABSENT_OK_STATUSES (or
    # with DISK_ABSENT_OK_PREFIXES) are exempt. Entries with `archived: true` are
    # exempt as well. Prevents stale manifest entries from being silently skipped by
    # workspace iteration tooling (rollout-workflow-templates.sh, run-all-setup.sh).
    # SSOT: plans/archive/issues/stale_manifest_entries_disk_absent_2026_05_18.md.
    if not repo_filter:
        for name, raw_entry in manifest_repos_raw.items():
            entry = _jdict(raw_entry) or {}
            if entry.get("archived") is True:
                continue
            status = _jstr(entry.get("status"), "active") or "active"
            if status in DISK_ABSENT_OK_STATUSES:
                continue
            if any(status.startswith(prefix) for prefix in DISK_ABSENT_OK_PREFIXES):
                continue
            folder = _jstr(entry.get("folder_name")) or name
            repo_path = WORKSPACE_ROOT / folder
            if not repo_path.is_dir():
                disk_absent.append(
                    {
                        "repo": name,
                        "expected_path": str(repo_path),
                        "status": status,
                    }
                )

    for repo_name, data in repos.items():
        data_d = _jdict(data) or {}
        if data_d.get("skipped"):
            continue
        manifest_entry_raw = manifest_repos_raw.get(repo_name)
        manifest_entry = _jdict(manifest_entry_raw) or {} if manifest_entry_raw is not None else {}
        deps_list = _jlist(manifest_entry.get("dependencies")) or []
        manifest_deps: dict[str, str] = {}
        for d in deps_list:
            d_dict = _jdict(d)
            if d_dict and "name" in d_dict:
                manifest_deps[normalize(_jstr(d_dict.get("name")))] = _jstr(d_dict.get("version"))

        derived_internal_raw = data_d.get("internal_deps")
        derived_internal = _jdict(derived_internal_raw) or {} if isinstance(derived_internal_raw, dict) else {}
        derived_external_raw = data_d.get("external_deps")
        derived_external = _jdict(derived_external_raw) or {} if isinstance(derived_external_raw, dict) else {}

        for dep in derived_internal:
            if dep not in manifest_deps:
                issues.append({"repo": repo_name, "type": "internal_in_pyproject_not_manifest", "dep": dep})
        for dep in manifest_deps:
            if dep not in derived_internal:
                issues.append({"repo": repo_name, "type": "internal_in_manifest_not_pyproject", "dep": dep})

        for pkg, specs_obj in derived_external.items():
            if pkg in canonical:
                canon_spec = canonical[pkg]
                exception_spec = PER_REPO_EXTERNAL_EXCEPTIONS.get((repo_name, pkg))
                specs_list = _jlist(specs_obj) or [] if isinstance(specs_obj, list) else [specs_obj]
                for spec in specs_list:
                    spec_str = _jstr(spec)
                    if spec_str == canon_spec:
                        continue
                    if exception_spec is not None and spec_str == exception_spec:
                        continue
                    issues.append(
                        {
                            "repo": repo_name,
                            "type": "external_version_mismatch",
                            "dep": pkg,
                            "pyproject_spec": spec_str,
                            "canonical_spec": canon_spec,
                        }
                    )

    aligned = len(issues) == 0 and len(disk_absent) == 0
    if json_output:
        out: dict[str, object] = {
            "aligned": aligned,
            "issues": issues,
            "count": len(issues),
            "disk_absent": disk_absent,
            "disk_absent_count": len(disk_absent),
        }
        print(json.dumps(out, indent=2))
    else:
        if aligned:
            print("OK: All dependencies aligned with manifest and canonical constraints.")
            print("OK: All non-archived manifest repos present on disk.")
            return 0
        if issues:
            print(f"Found {len(issues)} misalignment(s):\n")
            for i in issues:
                print(f"  [{i['repo']}] {i['type']}: {i['dep']}")
                if "pyproject_spec" in i:
                    print(f"    pyproject: {i['pyproject_spec']}")
                    print(f"    canonical: {i['canonical_spec']}")
        if disk_absent:
            print(f"\nFound {len(disk_absent)} manifest repo(s) absent from disk:\n")
            for d in disk_absent:
                print(f"  [{d['repo']}] status={d['status']!r} expected={d['expected_path']}")
            ok_statuses = "archived,deprecated,deleted,future"
            ok_prefixes = "consolidated-into-*,merged-into-*,pending-archive-into-*"
            print(
                f"\nFix: either re-clone the repo, set 'archived: true' / status in "
                f"{{{ok_statuses},{ok_prefixes}}}, or move the entry to removedEntries.",
            )
        return 1
    return 0 if aligned else 1


if __name__ == "__main__":
    sys.exit(main())
