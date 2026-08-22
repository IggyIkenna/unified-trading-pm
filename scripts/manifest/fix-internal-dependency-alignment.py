#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Fix internal dependency alignment: code uses -> add; code doesnt use -> remove.

Tier rule: No repo may import from a higher or equal tier. If code uses a dep
but it would violate the tier DAG (circular or wrong direction), reports
TIER_VIOLATION and requires architectural change — does not auto-fix.

Usage:
    python fix-internal-dependency-alignment.py              # dry run
    python fix-internal-dependency-alignment.py --apply
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import cast

import tomli_w

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", str(PM_ROOT.parent)))
DERIVED_PATH = PM_ROOT / "derived-dependency-manifest.json"
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
EXCLUDE = {".venv", "venv", ".venv-workspace", "__pycache__", ".git", "examples", "docs", "scripts", ".github"}


def pkg_to_import(pkg: str) -> str:
    return pkg.replace("-", "_")


JsonDict = dict[str, object]
TomlDict = dict[str, object]  # mutable, for tomllib


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


def load_manifest() -> JsonDict:
    with open(MANIFEST_PATH) as f:
        return cast(JsonDict, json.load(f))


def get_repo_path(manifest: JsonDict, repo: str) -> Path:
    repos = _jdict(manifest.get("repositories")) or {}
    e = _jdict(repos.get(repo)) or {}
    if e.get("folder_name"):
        return WORKSPACE_ROOT / str(e.get("folder_name"))
    return WORKSPACE_ROOT / repo


def _dep_matches_spec(spec: str, dep: str) -> bool:
    """True if spec refers to package dep (exact name match)."""
    if spec == dep:
        return True
    if not spec.startswith(dep):
        return False
    rest = spec[len(dep) :]
    return rest.startswith((">=", "==", "<", "~", "["))


def get_internal_dep_version(manifest: JsonDict, dep: str) -> str:
    """Version range for internal dep: from manifest versions or default."""
    versions = _jdict(manifest.get("versions")) or {}
    ver = versions.get(dep)
    if isinstance(ver, str) and ver and not dep.startswith("_"):
        major = int(ver.split(".")[0])
        return f">={ver},<{major + 1}.0.0"
    return ">=0.1.0,<1.0.0"


def workspace_sibling_exists(manifest: JsonDict, dep: str) -> bool:
    return get_repo_path(manifest, dep).is_dir()


def add_to_pyproject(repo: str, dep: str, manifest: JsonDict) -> None:
    repo_path = get_repo_path(manifest, repo)
    pyproject_path = repo_path / "pyproject.toml"
    if not pyproject_path.is_file():
        raise FileNotFoundError(f"No pyproject.toml: {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        data = cast(TomlDict, tomllib.load(f))

    project = cast(TomlDict, data.setdefault("project", {}))
    deps_raw = project.get("dependencies") or []  # PEP 621: optional
    deps = list(deps_raw) if isinstance(deps_raw, list) else []
    dep_spec = f"{dep}{get_internal_dep_version(manifest, dep)}"

    # Avoid duplicate
    deps = [str(d) for d in deps if not _dep_matches_spec(str(d), dep)]
    deps.append(dep_spec)
    project["dependencies"] = deps

    if workspace_sibling_exists(manifest, dep):
        tool = cast(TomlDict, data.setdefault("tool", {}))
        uv = cast(TomlDict, tool.setdefault("uv", {}))
        sources = cast(TomlDict, uv.setdefault("sources", {}))
        dep_folder = get_repo_path(manifest, dep).name
        sources[dep] = {"path": f"../{dep_folder}"}
        uv["sources"] = sources
        tool["uv"] = uv
        data["tool"] = tool

    with open(pyproject_path, "wb") as f:
        tomli_w.dump(data, f)


def remove_from_pyproject(repo: str, dep: str, manifest: JsonDict) -> None:
    repo_path = get_repo_path(manifest, repo)
    pyproject_path = repo_path / "pyproject.toml"
    if not pyproject_path.is_file():
        return

    with open(pyproject_path, "rb") as f:
        data = cast(TomlDict, tomllib.load(f))

    project = cast(TomlDict, data.get("project") or {})
    deps_raw = project.get("dependencies") or []  # PEP 621: optional
    deps = list(deps_raw) if isinstance(deps_raw, list) else []
    deps = [str(d) for d in deps if not _dep_matches_spec(str(d), dep)]
    project["dependencies"] = deps
    data["project"] = project

    tool = cast(TomlDict, data.get("tool") or {})
    uv = cast(TomlDict, tool.get("uv") or {})
    sources = cast(TomlDict, uv.get("sources") or {})
    if dep in sources:
        del sources[dep]
        if "tool" not in data:
            data["tool"] = {}
        tool_d = cast(TomlDict, data.get("tool") or {})
        if "uv" not in tool_d:
            tool_d["uv"] = {}
        uv_inner = cast(TomlDict, tool_d["uv"])
        uv_inner["sources"] = sources
        data["tool"] = tool_d

    with open(pyproject_path, "wb") as f:
        tomli_w.dump(data, f)


def add_to_manifest(manifest: JsonDict, repo: str, dep: str) -> None:
    repos = cast(JsonDict, manifest.setdefault("repositories", {}))
    entry = cast(JsonDict, repos.setdefault(repo, {}))
    deps_list = cast(list[object], entry.setdefault("dependencies", []))
    if not isinstance(deps_list, list):
        deps_list = []
        entry["dependencies"] = deps_list
    existing_names = {d["name"] for d in deps_list if isinstance(d, dict) and "name" in d}
    if dep not in existing_names:
        deps_list.append(
            {
                "name": dep,
                "version": get_internal_dep_version(manifest, dep),
                "required": True,
            }
        )
        entry["dependencies"] = deps_list
        repos[repo] = entry
        manifest["repositories"] = repos


def remove_from_manifest(manifest: JsonDict, repo: str, dep: str) -> None:
    repos = _jdict(manifest.get("repositories")) or {}
    entry = _jdict(repos.get(repo)) or {}
    deps_list = _jlist(entry.get("dependencies")) or []
    if not isinstance(deps_list, list):
        return
    deps_list = [d for d in deps_list if not (isinstance(d, dict) and d.get("name") == dep)]
    entry["dependencies"] = deps_list
    repos[repo] = entry
    manifest["repositories"] = repos


def scan_imports(repo_dir: Path, own: str) -> set[str]:
    out: set[str] = set()
    for p in repo_dir.rglob("*.py"):
        if any(x in p.relative_to(repo_dir).parts for x in EXCLUDE):
            continue
        try:
            t = ast.parse(p.read_text())
            for n in ast.walk(t):
                if isinstance(n, ast.Import):
                    for a in n.names:
                        out.add(a.name.split(".")[0])
                elif isinstance(n, ast.ImportFrom) and n.module and n.level == 0:
                    out.add(n.module.split(".")[0])
        except (OSError, SyntaxError):
            pass
    out.discard(own)
    return out


def _pyproject_package_name(repo_name: str) -> str | None:
    """Return the Python package name from a repo's pyproject.toml if it differs from the repo name."""
    pp = WORKSPACE_ROOT / repo_name / "pyproject.toml"
    if not pp.is_file():
        return None
    try:
        with pp.open("rb") as f:
            data = tomllib.load(f)
        proj_section = data.get("project")
        if not isinstance(proj_section, dict):
            return None
        proj_name = proj_section.get("name")
        if isinstance(proj_name, str) and proj_name and proj_name != repo_name:
            return proj_name
    except (OSError, tomllib.TOMLDecodeError):
        pass
    return None


def get_imported_internal(manifest: JsonDict, repos: set[str] | None = None) -> dict[str, set[str]]:
    """Scan repos for internal imports. If repos is None, scan all; else only those repos.

    Handles repos whose pyproject.toml package name differs from the repo name (e.g.
    unified-feature-calculator-library publishes 'unified-feature-calculator', so code
    imports 'unified_feature_calculator', not 'unified_feature_calculator_library').
    """
    repos_map = _jdict(manifest.get("repositories")) or {}
    # Map import-module-name → canonical repo name.
    # Seed with repo-name-derived key, then override/add with pyproject package name if different.
    internal: dict[str, str] = {pkg_to_import(n): n for n in repos_map}
    for repo_name in repos_map:
        pkg_name = _pyproject_package_name(repo_name)
        if pkg_name:
            internal[pkg_to_import(pkg_name)] = repo_name
    to_scan = repos if repos is not None else set(repos_map.keys())
    result: dict[str, set[str]] = {}
    for repo in to_scan:
        path = get_repo_path(manifest, repo)
        if not path.is_dir():
            continue
        imp = scan_imports(path, pkg_to_import(repo))
        result[repo] = {internal[x] for x in imp if x in internal}
    return result


def get_tier_map(manifest: JsonDict) -> dict[str, int]:
    tiers: dict[str, int] = {}
    repos_map = _jdict(manifest.get("repositories")) or {}
    for name, info in repos_map.items():
        info_d = _jdict(info) or {} if isinstance(info, dict) else {}
        t = _jstr(info_d.get("arch_tier", "0"))
        if t.isdigit():
            tiers[name] = int(t)
        elif t in ("service", "api", "ui"):
            tiers[name] = 999
        else:
            tiers[name] = 0
    return tiers


# Repos exempt from tier violation checks — these have documented bootstrap exceptions.
# deployment-service: directly uses cloud/config/events for infrastructure orchestration.
# e2e-testing: Phase-6 revocation black-box tests intentionally import service internals
# (RULED 2026-08-16, e2e_testing_deployment_service_manifest_drift_regression_2026_08_15.md) —
# importing service internals for black-box coverage is the repo's whole purpose, not an
# accidental violation.
TIER_EXEMPT_REPOS: frozenset[str] = frozenset(
    {
        "deployment-service",
        "e2e-testing",
    }
)


def is_tier_violation(repo: str, dep: str, tier_map: dict[str, int]) -> bool:
    """True if repo importing dep would violate DAG (repo tier must be > dep tier)."""
    if repo in TIER_EXEMPT_REPOS:
        return False
    repo_tier = tier_map.get(repo, 0)
    dep_tier = tier_map.get(dep, 0)
    return repo_tier <= dep_tier


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    do_apply: bool = cast(bool, args.apply)
    json_out: bool = cast(bool, args.json)

    if not DERIVED_PATH.is_file():
        print("Run generate-derived-manifest.py first.", file=sys.stderr)
        return 1

    manifest = load_manifest()

    r = subprocess.run(
        [sys.executable, str(PM_ROOT / "scripts/manifest/check-dependency-alignment.py"), "--json"],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT),
    )
    data = cast(JsonDict, json.loads(r.stdout))
    issues_raw = _jlist(data.get("issues")) or []
    issues = [i for i in issues_raw if isinstance(i, dict) and "internal" in _jstr(i.get("type"))]
    repos_with_issues = {_jstr(i.get("repo")) for i in issues if isinstance(i, dict)}
    imported = get_imported_internal(manifest, repos_with_issues) if repos_with_issues else {}

    # Build pyproject package-name → canonical repo-name map for repos whose
    # published package name differs from their repo name (e.g. unified-feature-calculator-library
    # publishes the 'unified-feature-calculator' package). Without this, `dep` (the pyproject dep
    # name) would not match the repo name stored in `imported[repo]`.
    repos_map_main = _jdict(manifest.get("repositories")) or {}
    pkg_to_repo: dict[str, str] = {}
    for rname in repos_map_main:
        pname = _pyproject_package_name(rname)
        if pname and pname != rname:
            pkg_to_repo[pname] = rname

    tier_map = get_tier_map(manifest)
    actions: list[dict] = []
    tier_violations: list[dict] = []

    for i in issues:
        if not isinstance(i, dict):
            continue
        repo = _jstr(i.get("repo"))
        dep = _jstr(i.get("dep"))
        itype = _jstr(i.get("type"))
        # Normalize dep to repo name so it can be matched against `imported[repo]`
        # (which stores canonical repo names, not pyproject package names).
        dep_as_repo = pkg_to_repo.get(dep, dep)
        uses = dep_as_repo in imported.get(repo, set())

        if itype == "internal_in_manifest_not_pyproject":
            if uses and is_tier_violation(repo, dep, tier_map):
                tier_violations.append({"repo": repo, "dep": dep, "reason": "add_to_pyproject would violate tier DAG"})
            else:
                actions.append(
                    {
                        "action": "add_to_pyproject" if uses else "remove_from_manifest",
                        "repo": repo,
                        "dep": dep,
                        "uses": uses,
                    }
                )
        else:
            if uses and is_tier_violation(repo, dep, tier_map):
                tier_violations.append({"repo": repo, "dep": dep, "reason": "add_to_manifest would violate tier DAG"})
            else:
                actions.append(
                    {
                        "action": "add_to_manifest" if uses else "remove_from_pyproject",
                        "repo": repo,
                        "dep": dep,
                        "uses": uses,
                    }
                )

    has_tier_violations = bool(tier_violations)
    if has_tier_violations:
        print("TIER_VIOLATION (architectural change required):", file=sys.stderr)
        for v in tier_violations:
            print(f"  [{v['repo']}] imports [{v['dep']}] — {v['reason']}", file=sys.stderr)
        print("  Fix: move shared code to a lower tier, or restructure dependency.", file=sys.stderr)
        print("  Continuing to apply non-violation fixes...", file=sys.stderr)

    if json_out:
        print(json.dumps({"actions": actions, "tier_violations": tier_violations}, indent=2))
        if has_tier_violations and not actions:
            return 1
        return 0 if not has_tier_violations else 1

    print(f"Planned {len(actions)} action(s) (code uses -> add; else -> remove):\n")
    for a in actions:
        print(f"  [{a['repo']}] {a['action']}: {a['dep']} (uses={a['uses']})")

    if do_apply:
        print("\nApplying...")
        manifest = load_manifest()
        for a in actions:
            act, repo, dep = a["action"], a["repo"], a["dep"]
            try:
                if act == "add_to_pyproject":
                    add_to_pyproject(repo, dep, manifest)
                elif act == "remove_from_pyproject":
                    remove_from_pyproject(repo, dep, manifest)
                elif act == "add_to_manifest":
                    add_to_manifest(manifest, repo, dep)
                elif act == "remove_from_manifest":
                    remove_from_manifest(manifest, repo, dep)
                print(f"  OK [{repo}] {act}: {dep}")
            except (OSError, FileNotFoundError, json.JSONDecodeError, tomllib.TOMLDecodeError) as e:
                print(f"  FAIL [{repo}] {act}: {dep} — {e}", file=sys.stderr)
                return 1

        with open(MANIFEST_PATH, "w") as f:
            json.dump(manifest, f, indent=2)
            f.write("\n")

        print("\nRegenerating derived manifest...")
        r_gen = subprocess.run(
            [sys.executable, str(PM_ROOT / "scripts/manifest/generate-derived-manifest.py")],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT),
        )
        if r_gen.returncode != 0:
            print(f"Failed to regenerate derived manifest: {r_gen.stderr}", file=sys.stderr)
            return 1

        print("\nVerifying...")
        r2 = subprocess.run(
            [sys.executable, str(PM_ROOT / "scripts/manifest/check-dependency-alignment.py"), "--json"],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_ROOT),
        )
        verify = cast(JsonDict, json.loads(r2.stdout))
        verify_issues = _jlist(verify.get("issues")) or []
        internal_issues = [i for i in verify_issues if isinstance(i, dict) and "internal" in _jstr(i.get("type"))]
        if internal_issues:
            print(f"Verification failed: {len(internal_issues)} internal mismatch(es) remaining.", file=sys.stderr)
            for i in internal_issues:
                print(f"  [{i['repo']}] {i['type']}: {i['dep']}", file=sys.stderr)
            return 1
        print("OK: 0 internal mismatches.")
    # Still exit non-zero if architectural tier violations remain unresolved
    return 1 if has_tier_violations else 0


if __name__ == "__main__":
    sys.exit(main())
