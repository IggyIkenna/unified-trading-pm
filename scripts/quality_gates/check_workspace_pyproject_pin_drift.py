# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Workspace-wide pyproject pin-drift audit — catches the next VM-launch failure
before it happens.

For each repo, finds dependency floors (`>= X.Y.Z`) on PEER WORKSPACE REPOS,
and checks whether the floor exceeds the peer's current version. Pin drift
caused two VM-launch failures on 2026-05-16/17:

  - ml-training-service pinned `unified-trading-library>=0.4.0` while UTL was
    at 0.3.167 → `uv pip install` unsatisfiable → VM idled 55 min before
    operator caught it.
  - system-integration-tests pinned `features-service>=0.1.0` while
    features-service was at 0.0.1 → masked by `[tool.uv.sources]` path
    override but tripped pip-compile / non-uv installers.

Exit codes:
  0 — all floors at-or-below peer current versions
  1 — pin drift detected (script prints the offending entries)

Designed to be wired into VM-launch preflight + per-repo QG. Cheap to run
(<100 ms across 25 repos). No external deps beyond stdlib tomllib.
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path


def _read_pyproject(path: Path) -> dict[str, object]:
    try:
        with path.open("rb") as fh:
            return tomllib.load(fh)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def _extract_version(data: dict[str, object]) -> str | None:
    project = data.get("project")
    if not isinstance(project, dict):
        return None
    version = project.get("version")
    if isinstance(version, str):
        return version
    return None


def _extract_name(data: dict[str, object]) -> str | None:
    project = data.get("project")
    if not isinstance(project, dict):
        return None
    name = project.get("name")
    if isinstance(name, str):
        return name
    return None


def _extract_dependencies(data: dict[str, object]) -> list[str]:
    project = data.get("project")
    if not isinstance(project, dict):
        return []
    deps = project.get("dependencies")
    if not isinstance(deps, list):
        return []
    return [d for d in deps if isinstance(d, str)]


def _parse_version_tuple(version: str) -> tuple[int, ...] | None:
    parts = version.split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return None


def _scan_workspace(workspace_root: Path) -> int:
    """Return 0 if no drift, 1 if drift detected."""
    repos: list[Path] = sorted([p for p in workspace_root.iterdir() if (p / "pyproject.toml").exists()])

    # Build peer name → current version map
    name_to_version: dict[str, str] = {}
    name_to_repo: dict[str, str] = {}
    for repo in repos:
        data = _read_pyproject(repo / "pyproject.toml")
        name = _extract_name(data)
        version = _extract_version(data)
        if name and version:
            name_to_version[name] = version
            name_to_repo[name] = repo.name

    # Scan each repo's deps for peer-pin drift
    drifts: list[tuple[str, str, str, str]] = []
    dep_floor_re = re.compile(r"^([a-zA-Z0-9_-]+)\s*([><=!,\s\d\.]*)$")
    floor_re = re.compile(r">=\s*(\d+\.\d+(?:\.\d+)?)")

    for repo in repos:
        data = _read_pyproject(repo / "pyproject.toml")
        for dep_spec in _extract_dependencies(data):
            m = dep_floor_re.match(dep_spec)
            if not m:
                continue
            dep_name = m.group(1).strip()
            spec = m.group(2).strip()
            if dep_name not in name_to_version:
                continue
            fm = floor_re.search(spec)
            if not fm:
                continue
            floor = fm.group(1)
            current = name_to_version[dep_name]
            f_parts = _parse_version_tuple(floor)
            c_parts = _parse_version_tuple(current)
            if f_parts is None or c_parts is None:
                continue
            # Pad to same length
            max_len = max(len(f_parts), len(c_parts))
            f_padded = f_parts + (0,) * (max_len - len(f_parts))
            c_padded = c_parts + (0,) * (max_len - len(c_parts))
            if f_padded > c_padded:
                drifts.append((repo.name, dep_name, floor, current))

    print(f"Scanned {len(repos)} repo(s); {len(name_to_version)} peer pkg(s); {len(drifts)} pin-drift(s).")

    if drifts:
        print()
        print("❌ PIN DRIFT — these floors exceed peer current versions:")
        for consumer, dep_name, floor, current in drifts:
            peer_repo = name_to_repo.get(dep_name, "?")
            print(f"  {consumer}/pyproject.toml: {dep_name}>={floor}  (peer {peer_repo} at {current})")
        print()
        print(
            "Resolution: lower the floor in the consumer's pyproject.toml OR bump the peer's "
            "version via semver-agent. Pin drift causes VM-launch failures + non-uv installer breakage."
        )
        return 1

    print("✅ All workspace-internal pyproject floors at-or-below peer current versions.")
    return 0


def main() -> int:
    # workspace root = parent of unified-trading-pm
    here = Path(__file__).resolve()
    # scripts/quality_gates/ → scripts/ → unified-trading-pm/ → workspace root
    workspace_root = here.parents[3]
    if not (workspace_root / "unified-trading-pm").is_dir():
        print(
            f"ERROR: workspace root inference wrong; {workspace_root} does not contain "
            "unified-trading-pm/. Run from a slot worktree.",
            file=sys.stderr,
        )
        return 2
    return _scan_workspace(workspace_root)


if __name__ == "__main__":
    sys.exit(main())
