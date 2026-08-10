#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Workspace `.code-workspace` repo-list drift QG check.

Guards against the drift root-caused in
`plans/active/issues/workspace_config_repo_list_drift_2026_06_01.md` (Finding 3:
nothing failed when the canonical multi-root workspace file diverged from the actual
repo set, so it drifted in both directions — stale deleted repos still listed +
real current repos missing — until a human saw VS Code throw
`<repo> does not appear to be a git repository`).

Assertions (hard, exit 1 on failure):

  1. The canonical `.code-workspace` `folders[]` (minus the `../../` / `.` workspace-root
     entry) == the active + scaffolded repo set in `workspace-manifest.json`
     (`status in {active, scaffolded}`).
  2. No `folders[]` path points at a known archived/consolidated repo (any manifest entry
     whose status is not active/scaffolded — e.g. `risk-and-exposure-service`,
     `ml-inference-service`, the consolidated `features-*-service`).

Soft validation (warn-only, never blocks):

  3. Every `git.scanRepositories` / `git.ignoredRepositories` entry resolves to a repo name
     known to the manifest (active OR archived). Absolute `.tabs/N/...` paths are accepted
     by basename — they are tab-specific and harmless, but an entry naming a repo the
     manifest has never heard of is surfaced as a likely typo / further drift.

Canonical SSOT (the file the repos-root symlink chain actually loads):
    unified-trading-pm/cursor-configs/unified-trading-system-repos.code-workspace
Manifest SSOT:
    unified-trading-pm/workspace-manifest.json

Exit-code semantics: 0 = clean; 1 = drift (hard assertion failed); 2 = arg / IO error.

SSOT: plans/active/workspace_config_drift_remediation_2026_06_01.md (Item 3) +
      plans/active/issues/workspace_config_repo_list_drift_2026_06_01.md.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast

_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")

ACTIVE_STATUSES = frozenset({"active", "scaffolded"})
# Folder paths that denote the workspace root rather than a repo.
WORKSPACE_ROOT_PATHS = frozenset({".", "..", "../", "../..", "../../", "./", ""})


def _repo_name_from_path(path: str) -> str | None:
    """Map a `folders[].path` to a bare repo name, or None for the workspace-root entry."""
    normalized = path.strip().rstrip("/")
    if normalized in {p.rstrip("/") for p in WORKSPACE_ROOT_PATHS}:
        return None
    # Strip any leading `../` segments, keep the final path component.
    return normalized.split("/")[-1]


def _load_jsonc(file_path: Path) -> dict[str, object]:
    """Load a JSON-with-line-comments file (VS Code `.code-workspace` allows `//` and
    trailing commas — the latter also matches what `prettier-autostage.sh` produces for
    this file, so tolerating them here avoids fighting every subsequent format pass)."""
    raw = file_path.read_text(encoding="utf-8")
    no_comments = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("//"))
    stripped = _TRAILING_COMMA_RE.sub(r"\1", no_comments)
    return cast("dict[str, object]", json.loads(stripped))


def _as_dict(value: object) -> dict[str, object]:
    return cast("dict[str, object]", value) if isinstance(value, dict) else {}


def _as_list(value: object) -> list[object]:
    return cast("list[object]", value) if isinstance(value, list) else []


def _folder_repo_names(ws: dict[str, object]) -> set[str]:
    names: set[str] = set()
    for folder in _as_list(ws.get("folders")):
        path_value = _as_dict(folder).get("path")
        if isinstance(path_value, str):
            name = _repo_name_from_path(path_value)
            if name is not None:
                names.add(name)
    return names


def _partition_repos(manifest: dict[str, object]) -> tuple[set[str], set[str]]:
    """Return (active+scaffolded, inactive) repo-name sets from the manifest."""
    repositories = _as_dict(manifest.get("repositories"))
    active: set[str] = set()
    inactive: set[str] = set()
    for name, meta in repositories.items():
        status = _as_dict(meta).get("status")
        if isinstance(status, str) and status in ACTIVE_STATUSES:
            active.add(name)
        else:
            inactive.add(name)
    return active, inactive


def check(workspace_root: Path) -> int:
    pm_root = workspace_root / "unified-trading-pm"
    canonical = pm_root / "cursor-configs" / "unified-trading-system-repos.code-workspace"
    manifest_path = pm_root / "workspace-manifest.json"

    if not canonical.is_file():
        print(f"❌ canonical .code-workspace not found at {canonical}", file=sys.stderr)
        return 2
    if not manifest_path.is_file():
        print(f"❌ workspace-manifest.json not found at {manifest_path}", file=sys.stderr)
        return 2

    try:
        ws = _load_jsonc(canonical)
        manifest = cast("dict[str, object]", json.loads(manifest_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"❌ failed to parse workspace config / manifest: {exc}", file=sys.stderr)
        return 2

    active_repos, inactive_repos = _partition_repos(manifest)
    folder_repos = _folder_repo_names(ws)

    failures: list[str] = []

    # Assertion 1 — folders[] repo set == active+scaffolded manifest set.
    missing_from_workspace = sorted(active_repos - folder_repos)
    extra_in_workspace = set(folder_repos - active_repos)
    if missing_from_workspace:
        failures.append("Active repos missing from .code-workspace folders[]: " + ", ".join(missing_from_workspace))
    if extra_in_workspace:
        # Split: archived/consolidated (Assertion 2) vs genuinely-unknown.
        archived_listed = sorted(extra_in_workspace & inactive_repos)
        unknown_listed = sorted(extra_in_workspace - inactive_repos)
        if archived_listed:
            failures.append(
                "Archived/consolidated repos still listed in folders[] (stale): " + ", ".join(archived_listed)
            )
        if unknown_listed:
            failures.append("folders[] lists repos absent from workspace-manifest.json: " + ", ".join(unknown_listed))

    if failures:
        print("❌ workspace .code-workspace repo-list drift detected:", file=sys.stderr)
        for line in failures:
            print(f"   - {line}", file=sys.stderr)
        print(
            "\n   Fix the canonical "
            "unified-trading-pm/cursor-configs/unified-trading-system-repos.code-workspace "
            "so folders[] == active+scaffolded repos in workspace-manifest.json.\n"
            "   SSOT: plans/active/workspace_config_drift_remediation_2026_06_01.md",
            file=sys.stderr,
        )
        return 1

    # Soft validation 3 — scanRepositories / ignoredRepositories name sanity (warn-only).
    known_repos = active_repos | inactive_repos
    settings = _as_dict(ws.get("settings"))
    for key in ("git.scanRepositories", "git.ignoredRepositories"):
        for entry in _as_list(settings.get(key)):
            if not isinstance(entry, str):
                continue
            name = _repo_name_from_path(entry)
            if name is not None and name not in known_repos:
                print(
                    f"⚠️  {key} entry '{entry}' names repo '{name}' unknown to workspace-manifest.json (possible drift)",
                    file=sys.stderr,
                )

    print(f"✅ workspace .code-workspace clean: folders[] == {len(active_repos)} active+scaffolded repos (no drift)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _ = parser.add_argument(
        "--workspace-root",
        required=True,
        help="Path to the unified-trading-system-repos workspace root.",
    )
    ns = parser.parse_args(argv)
    workspace_root = cast(str, ns.workspace_root)
    return check(Path(workspace_root).resolve())


if __name__ == "__main__":
    raise SystemExit(main())
