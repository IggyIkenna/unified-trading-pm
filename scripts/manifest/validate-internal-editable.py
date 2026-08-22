#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate internal workspace deps are installed editable, not from Artifact Registry.

For each internal package (from workspace-manifest.json dependencies), check it is
installed from path/editable, NOT from Artifact Registry (wheel). Uses `uv pip show`
and inspects Editable project location. Fails with exit 1 if any internal dep is
from registry.

Usage:
    python validate-internal-editable.py
    python validate-internal-editable.py --repo execution-service

Run from workspace root after uv sync. Uses each repo's .venv for uv pip show.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"

JsonDict = dict[str, object]

SKIP_STATUSES = frozenset({"deprecated", "archived", "deleted"})
SKIP_TYPES = frozenset({"ui"})


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def normalize(name: str) -> str:
    return name.lower().replace("_", "-").strip()


def load_manifest() -> JsonDict:
    with open(MANIFEST_PATH) as f:
        return cast(JsonDict, json.load(f))


def get_workspace_repo_names(manifest: JsonDict) -> frozenset[str]:
    repos_raw = _jdict(manifest.get("repositories")) or {}
    return frozenset(normalize(r) for r in repos_raw)


def get_repos_to_check(manifest: JsonDict, repo_filter: str | None) -> list[tuple[str, Path]]:
    """Return list of (repo_name, repo_path) for Python repos to check."""
    repos_raw = _jdict(manifest.get("repositories")) or {}
    result: list[tuple[str, Path]] = []
    for name, meta in repos_raw.items():
        if not isinstance(meta, dict):
            continue
        status = str(meta.get("status", "")).lower()
        repo_type = str(meta.get("type", "")).lower()
        if status in SKIP_STATUSES or repo_type in SKIP_TYPES:
            continue
        repo_path = WORKSPACE_ROOT / name
        if not (repo_path / "pyproject.toml").exists():
            continue
        if not (repo_path / ".venv").exists():
            continue
        if repo_filter and normalize(name) != normalize(repo_filter):
            continue
        result.append((name, repo_path))
    return result


def parse_internal_deps(pyproject_path: Path, workspace_repos: frozenset[str]) -> list[str]:
    content = pyproject_path.read_text()
    found: list[str] = []
    for m in re.finditer(r'"([a-zA-Z0-9][a-zA-Z0-9._-]*?)(?:\[|>=|>|==|!=|<|,|")', content):
        raw_name = m.group(1)
        norm = normalize(raw_name)
        if norm in workspace_repos and norm not in found:
            found.append(norm)
    return found


def pip_show_editable_location(repo_path: Path, pkg: str) -> str | None:
    """Run uv pip show for pkg in repo's venv. Return editable location path, empty string if
    installed-but-not-editable (from Artifact Registry), or None if not installed at all."""
    venv_python = repo_path / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return None
    out = subprocess.run(
        ["uv", "pip", "show", "-p", str(venv_python), pkg],
        capture_output=True,
        text=True,
        cwd=str(PM_ROOT),
    )
    if out.returncode != 0:
        return None  # not installed
    for line in out.stdout.splitlines():
        if line.startswith("Editable project location:"):
            return line.split(":", 1)[1].strip()
    return ""  # installed from Artifact Registry (wheel), not editable


class _ParsedArgs(argparse.Namespace):
    repo: str | None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate internal deps are editable")
    parser.add_argument("--repo", help="Check only this repo")
    args = parser.parse_args(namespace=_ParsedArgs())

    manifest = load_manifest()
    workspace_repos = get_workspace_repo_names(manifest)
    repos = get_repos_to_check(manifest, args.repo)

    errors: list[str] = []
    for repo_name, repo_path in repos:
        pyproject = repo_path / "pyproject.toml"
        internal_deps = parse_internal_deps(pyproject, workspace_repos)
        repo_norm = normalize(repo_name)
        for dep in internal_deps:
            # Skip self-reference: parse_internal_deps regex can match name = "repo-name"
            # in [project]; repos like PM/codex/SIT have no installable self-package.
            if dep == repo_norm:
                continue
            loc = pip_show_editable_location(repo_path, dep)
            if loc is None:
                errors.append(f"  {repo_name}: {dep} — not installed (run: cd {repo_name} && bash scripts/setup.sh)")
                continue
            if loc == "":
                errors.append(
                    f"  {repo_name}: {dep} — installed from Artifact Registry (not editable)"
                    f" — add [tool.uv.sources.{dep}] path entry in pyproject.toml then re-run:"
                    f" cd {repo_name} && uv sync"
                )
                continue
            try:
                loc_path = Path(loc).resolve()
                ws = WORKSPACE_ROOT.resolve()
                if not str(loc_path).startswith(str(ws)):
                    errors.append(f"  {repo_name}: {dep} — editable path outside workspace: {loc}")
            except (OSError, ValueError):
                errors.append(f"  {repo_name}: {dep} — editable path invalid: {loc}")

    if errors:
        print("Internal deps must be editable (path install), not from Artifact Registry:")
        for e in errors:
            print(e)
        print("")
        print("Fix: run scripts/repo-management/run-version-alignment.sh --fix to auto-add")
        print("     [tool.uv.sources.*] entries, then: bash scripts/repo-management/run-all-setup.sh")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
