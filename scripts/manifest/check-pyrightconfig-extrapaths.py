#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
check-pyrightconfig-extrapaths.py — Validate basedpyright extraPaths against
the workspace manifest declared dependencies.

Config source per repo (fleet-wide migration off pyrightconfig.json is complete —
see codex/06-coding-standards/quality-gates.md § "pyrightconfig.json silently
overrides pyproject.toml"): prefer `pyrightconfig.json` if a repo still has one
(back-compat), else fall back to `pyproject.toml`'s `[tool.basedpyright]` table.

Rules enforced:
  1. DEAD extraPath — listed in the config but NOT declared in manifest deps
       --apply: remove it (if code doesn't import it) OR error (if code imports it)
       (pyrightconfig.json sources only — auto-apply is not supported for
       pyproject.toml sources; those report as a warning requiring a manual edit)
  2. PHANTOM dep — declared in manifest deps AND in pyproject.toml, but code has
       zero imports from that package → always ERROR (cannot auto-fix a missing usage)
  3. MISSING extraPath — declared as internal manifest dep but not in extraPaths
       --apply: add it (pyrightconfig.json sources only, same caveat as Rule 1)

Usage:
    python3 check-pyrightconfig-extrapaths.py          # check only
    python3 check-pyrightconfig-extrapaths.py --apply  # fix + report errors
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import cast

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def repo_to_package(repo_name: str) -> str:
    """unified-api-contracts → unified_api_contracts"""
    return repo_name.replace("-", "_")


def extrapaths_from_config(config: dict[str, object]) -> list[str]:
    """Extract all extraPaths entries from a pyrightconfig dict (all locations)."""
    paths: list[str] = []
    # Top-level extraPaths
    raw_extra = config.get("extraPaths")
    if isinstance(raw_extra, list):
        paths.extend(str(p) for p in raw_extra)
    # executionEnvironments[*].extraPaths
    envs = config.get("executionEnvironments")
    for env in envs if isinstance(envs, list) else []:
        env_dict = cast(dict[str, object], env) if isinstance(env, dict) else {}
        env_extra = env_dict.get("extraPaths")
        if isinstance(env_extra, list):
            paths.extend(str(p) for p in env_extra)
    return paths


def extrapaths_to_repo_names(paths: list[str], repo_root: Path, workspace_root: Path) -> dict[str, str]:
    """Map each raw extraPath string to its resolved sibling repo name.

    Only includes paths that resolve to a direct sibling of the workspace root.
    Skips '.' (self-reference), '..' and non-sibling paths silently.

    "../unified-api-contracts"                           → "unified-api-contracts"
    "../api-contracts"                                   → "api-contracts" (typo)
    "/abs/path/to/workspace/features-cross-instrument-service" → "features-cross-instrument-service"
    "."                                                  → skipped
    """
    result: dict[str, str] = {}
    for p in paths:
        raw = Path(p)
        # Skip self-reference and parent-only paths
        if str(p) in (".", ".."):
            continue
        # Resolve to absolute
        resolved = raw if raw.is_absolute() else (repo_root / raw).resolve()
        # Must be a direct child of workspace_root to be a sibling repo
        try:
            resolved.relative_to(workspace_root)
        except ValueError:
            continue
        if resolved.parent != workspace_root:
            continue  # nested path, not a direct sibling repo
        result[p] = resolved.name
    return result


def imports_package_in_source(source_dir: Path, package_name: str) -> bool:
    """Return True if any .py file in source_dir or sibling tests/ imports package_name."""
    search_dirs = [d for d in [source_dir, source_dir.parent / "tests"] if d.is_dir()]
    if not search_dirs:
        return False
    patterns = [f"from {package_name}", f"import {package_name}"]
    for search_dir in search_dirs:
        for pattern in patterns:
            result = subprocess.run(
                ["grep", "-r", "--include=*.py", "-l", pattern, str(search_dir)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                return True
    return False


def get_source_dir(repo_root: Path, config: dict[str, object]) -> Path:
    """Derive source directory from pyrightconfig include list or fall back."""
    raw_include = config.get("include")
    includes: list[str] = [str(x) for x in raw_include] if isinstance(raw_include, list) else []
    for inc in includes:
        candidate = repo_root / inc
        if candidate.is_dir() and not str(inc).startswith("test"):
            return candidate
    # Fallback: repo_name with hyphens → underscores
    pkg = repo_to_package(repo_root.name)
    candidate = repo_root / pkg
    if candidate.is_dir():
        return candidate
    return repo_root


def load_basedpyright_config(repo_root: Path) -> tuple[dict[str, object], Path] | None:
    """Resolve the basedpyright config for a repo: pyrightconfig.json if present
    (back-compat), else pyproject.toml's [tool.basedpyright] table. Returns
    (config_dict, source_path) or None if neither carries a usable config.

    tomllib parses [tool.basedpyright] into the same dict shape pyrightconfig.json
    would have ("include"/"extraPaths"/"executionEnvironments" keys), so it's a
    drop-in for extrapaths_from_config()/get_source_dir() below.
    """
    pyright_path = repo_root / "pyrightconfig.json"
    if pyright_path.exists():
        return cast(dict[str, object], json.loads(pyright_path.read_text())), pyright_path

    pyproject_path = repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        return None
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    tool = cast(dict[str, object], data.get("tool") or {})
    basedpyright = tool.get("basedpyright")
    if not isinstance(basedpyright, dict) or not basedpyright:
        return None
    return cast(dict[str, object], basedpyright), pyproject_path


def get_pyproject_internal_deps(repo_root: Path, internal_repos: set[str]) -> set[str]:
    """Return set of internal repo names declared in pyproject.toml dependencies."""
    pyproject = repo_root / "pyproject.toml"
    if not pyproject.exists():
        return set()
    text = pyproject.read_text()
    found: set[str] = set()
    # Match dep lines like:  "unified-api-contracts>=0.1.0,<1.0.0"
    for match in re.finditer(r'"([a-z][a-z0-9-]+)(?:>=|==|~=|>|@)', text):
        name = match.group(1)
        if name in internal_repos:
            found.add(name)
    return found


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply safe fixes")
    args = parser.parse_args()
    apply_fix: bool = cast(bool, args.apply)

    # Resolve workspace root (script lives in unified-trading-pm/scripts/manifest/)
    script_dir = Path(__file__).resolve().parent
    pm_root = script_dir.parent.parent
    workspace_root = pm_root.parent

    manifest_path = pm_root / "workspace-manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: workspace-manifest.json not found at {manifest_path}", file=sys.stderr)
        return 1

    manifest = cast(dict[str, object], json.loads(manifest_path.read_text()))
    repositories: dict[str, dict[str, object]] = cast(dict[str, dict[str, object]], manifest.get("repositories") or {})
    internal_repos: set[str] = set(repositories.keys())

    errors: list[str] = []
    warnings: list[str] = []
    fixes_applied: list[str] = []

    for repo_name, repo_meta in repositories.items():
        repo_root = workspace_root / repo_name

        loaded = load_basedpyright_config(repo_root)
        if loaded is None:
            continue
        config, config_path = loaded
        # Auto-apply (--apply) mutates JSON in place; pyproject.toml sources are
        # reported as warnings requiring a manual edit instead (see module docstring).
        can_apply = config_path.suffix == ".json"

        raw_paths = extrapaths_from_config(config)
        if not raw_paths:
            continue

        path_to_repo = extrapaths_to_repo_names(raw_paths, repo_root, workspace_root)
        # Internal manifest deps declared for this repo
        # deps can be list[dict] ({"name": ..., "version": ...}) or list[str]
        raw_deps_val = repo_meta.get("dependencies")
        raw_deps: list[object] = list(raw_deps_val) if isinstance(raw_deps_val, list) else []
        manifest_internal_deps: set[str] = set()
        for dep in raw_deps:
            dep_name = str(cast(dict[str, object], dep)["name"]) if isinstance(dep, dict) else str(dep)
            if dep_name in internal_repos:
                manifest_internal_deps.add(dep_name)

        source_dir = get_source_dir(repo_root, config)
        pyproject_internal_deps = get_pyproject_internal_deps(repo_root, internal_repos)

        # ── Rule 1: Dead extraPaths (not in manifest) ────────────────────────
        dead_paths: list[str] = [raw for raw, name in path_to_repo.items() if name not in manifest_internal_deps]
        for raw in dead_paths:
            dep_name = path_to_repo[raw]
            pkg_name = repo_to_package(dep_name)
            used_in_code = imports_package_in_source(source_dir, pkg_name)

            if used_in_code:
                errors.append(
                    f"[{repo_name}] extraPath '{raw}' (→ {dep_name}) is NOT in manifest deps "
                    f"but IS imported in source — add '{dep_name}' to manifest dependencies first"
                )
            elif apply_fix and can_apply:
                _remove_extrapath(config_path, config, raw)
                fixes_applied.append(f"[{repo_name}] Removed dead extraPath '{raw}' (not in manifest, not imported)")
            else:
                suffix = (
                    " (edit pyproject.toml manually — auto-apply unsupported for toml sources)"
                    if apply_fix
                    else " — run --apply to remove"
                )
                warnings.append(
                    f"[{repo_name}] Dead extraPath '{raw}' (→ {dep_name}) not in manifest and not imported{suffix}"
                )

        # ── Rule 2: Phantom deps (manifest + pyproject dep but no imports) ───
        for dep in manifest_internal_deps & pyproject_internal_deps:
            pkg_name = repo_to_package(dep)
            if not imports_package_in_source(source_dir, pkg_name):
                errors.append(
                    f"[{repo_name}] Phantom dep '{dep}': declared in manifest + pyproject.toml "
                    f"but no import of '{pkg_name}' found in {source_dir.relative_to(workspace_root)} "
                    f"— add a real import or remove the dependency"
                )

        # ── Rule 3: Missing extraPaths (manifest dep, no extraPath) ──────────
        configured_repos = set(path_to_repo.values())
        missing: set[str] = manifest_internal_deps - configured_repos
        for dep in sorted(missing):
            if apply_fix and can_apply:
                _add_extrapath(config_path, config, f"../{dep}")
                fixes_applied.append(f"[{repo_name}] Added missing extraPath '../{dep}' (declared manifest dep)")
            else:
                suffix = (
                    " (edit pyproject.toml manually — auto-apply unsupported for toml sources)"
                    if apply_fix
                    else " — run --apply to add"
                )
                warnings.append(f"[{repo_name}] Manifest dep '{dep}' has no extraPath '../{dep}'{suffix}")

    # ── Report ───────────────────────────────────────────────────────────────
    if fixes_applied:
        print("\nFixes applied:")
        for f in fixes_applied:
            print(f"  ✅ {f}")

    if warnings:
        print("\nWarnings (run --apply to fix):")
        for w in warnings:
            print(f"  ⚠️  {w}")

    if errors:
        print("\nErrors (manual intervention required):")
        for e in errors:
            print(f"  ❌ {e}")
        return 1

    if not fixes_applied and not warnings and not errors:
        print("  extraPaths alignment OK")

    return 0


# ---------------------------------------------------------------------------
# Mutation helpers
# ---------------------------------------------------------------------------


def _load_config(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text()))


def _save_config(path: Path, config: dict[str, object]) -> None:
    path.write_text(json.dumps(config, indent=2) + "\n")


def _remove_extrapath(path: Path, config: dict[str, object], raw: str) -> None:
    """Remove raw extraPath from all locations in config and save."""
    changed = False

    raw_extra = config.get("extraPaths")
    if isinstance(raw_extra, list):
        old: list[str] = [str(p) for p in raw_extra]
        new = [p for p in old if p != raw]
        if new != old:
            config["extraPaths"] = new
            changed = True

    envs = config.get("executionEnvironments")
    for env in envs if isinstance(envs, list) else []:
        env_dict = cast(dict[str, object], env) if isinstance(env, dict) else {}
        env_extra = env_dict.get("extraPaths")
        if isinstance(env_extra, list):
            old = [str(p) for p in env_extra]
            new = [p for p in old if p != raw]
            if new != old:
                env_dict["extraPaths"] = new
                changed = True

    if changed:
        _save_config(path, config)


def _add_extrapath(path: Path, config: dict[str, object], raw: str) -> None:
    """Add raw extraPath to the top-level extraPaths list and save."""
    if "extraPaths" not in config:
        config["extraPaths"] = []
    raw_extra = config["extraPaths"]
    paths: list[str] = [str(p) for p in raw_extra] if isinstance(raw_extra, list) else []
    if raw not in paths:
        paths.append(raw)
        config["extraPaths"] = sorted(paths)
        _save_config(path, config)


if __name__ == "__main__":
    sys.exit(main())
