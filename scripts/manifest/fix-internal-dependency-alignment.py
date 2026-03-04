#!/usr/bin/env python3
"""Fix internal dependency alignment: code uses -> add; code doesnt use -> remove.

Usage:
    python fix-internal-dependency-alignment.py              # dry run
    python fix-internal-dependency-alignment.py --apply
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
import sys
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-reuse-def]

import tomli_w

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
DERIVED_PATH = PM_ROOT / "derived-dependency-manifest.json"
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
EXCLUDE = {".venv", "venv", ".venv-workspace", "__pycache__", ".git", "tests", "examples", "docs", "scripts", ".github"}


def pkg_to_import(pkg: str) -> str:
    return pkg.replace("-", "_")


def load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def get_repo_path(manifest: dict, repo: str) -> Path:
    e = manifest.get("repositories", {}).get(repo, {})
    if isinstance(e, dict) and e.get("folder_name"):
        return WORKSPACE_ROOT / e["folder_name"]
    return WORKSPACE_ROOT / repo


def _dep_matches_spec(spec: str, dep: str) -> bool:
    """True if spec refers to package dep (exact name match)."""
    if spec == dep:
        return True
    if not spec.startswith(dep):
        return False
    rest = spec[len(dep) :]
    return rest.startswith((">=", "==", "<", "~", "["))


def get_internal_dep_version(manifest: dict, dep: str) -> str:
    """Version range for internal dep: from manifest versions or default."""
    versions = manifest.get("versions", {})
    ver = versions.get(dep) if isinstance(versions, dict) else None
    if ver and not dep.startswith("_"):
        return f">={ver},<1.0.0"
    return ">=0.1.0,<1.0.0"


def workspace_sibling_exists(manifest: dict, dep: str) -> bool:
    return get_repo_path(manifest, dep).is_dir()


def add_to_pyproject(repo: str, dep: str, manifest: dict) -> None:
    repo_path = get_repo_path(manifest, repo)
    pyproject_path = repo_path / "pyproject.toml"
    if not pyproject_path.is_file():
        raise FileNotFoundError(f"No pyproject.toml: {pyproject_path}")

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project = data.setdefault("project", {})
    deps = list(project.get("dependencies", []))
    dep_spec = f"{dep}{get_internal_dep_version(manifest, dep)}"

    # Avoid duplicate
    deps = [d for d in deps if not _dep_matches_spec(d, dep)]
    deps.append(dep_spec)
    project["dependencies"] = deps

    if workspace_sibling_exists(manifest, dep):
        tool = data.setdefault("tool", {})
        uv = tool.setdefault("uv", {})
        sources = uv.setdefault("sources", {})
        dep_folder = get_repo_path(manifest, dep).name
        sources[dep] = {"path": f"../{dep_folder}"}
        uv["sources"] = sources
        tool["uv"] = uv
        data["tool"] = tool

    with open(pyproject_path, "wb") as f:
        tomli_w.dump(data, f)


def remove_from_pyproject(repo: str, dep: str, manifest: dict) -> None:
    repo_path = get_repo_path(manifest, repo)
    pyproject_path = repo_path / "pyproject.toml"
    if not pyproject_path.is_file():
        return

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    deps = list(project.get("dependencies", []))
    deps = [d for d in deps if not _dep_matches_spec(d, dep)]
    project["dependencies"] = deps
    data["project"] = project

    sources = data.get("tool", {}).get("uv", {}).get("sources", {})
    if dep in sources:
        del sources[dep]
        if "tool" not in data:
            data["tool"] = {}
        if "uv" not in data["tool"]:
            data["tool"]["uv"] = {}
        data["tool"]["uv"]["sources"] = sources

    with open(pyproject_path, "wb") as f:
        tomli_w.dump(data, f)


def add_to_manifest(manifest: dict, repo: str, dep: str) -> None:
    repos = manifest.setdefault("repositories", {})
    entry = repos.setdefault(repo, {})
    deps_list = entry.setdefault("dependencies", [])
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


def remove_from_manifest(manifest: dict, repo: str, dep: str) -> None:
    repos = manifest.get("repositories", {})
    entry = repos.get(repo, {})
    deps_list = entry.get("dependencies", [])
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
        except Exception:
            pass
    out.discard(own)
    return out


def get_imported_internal(manifest: dict) -> dict[str, set[str]]:
    internal = {pkg_to_import(n): n for n in manifest.get("repositories", {})}
    result: dict[str, set[str]] = {}
    for repo in manifest.get("repositories", {}):
        path = get_repo_path(manifest, repo)
        if not path.is_dir():
            continue
        imp = scan_imports(path, pkg_to_import(repo))
        result[repo] = {internal[x] for x in imp if x in internal}
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not DERIVED_PATH.is_file():
        print("Run generate-derived-manifest.py first.", file=sys.stderr)
        return 1

    manifest = load_manifest()
    imported = get_imported_internal(manifest)

    r = subprocess.run(
        [sys.executable, str(PM_ROOT / "scripts/manifest/check-dependency-alignment.py"), "--json"],
        capture_output=True,
        text=True,
        cwd=str(WORKSPACE_ROOT),
    )
    data = json.loads(r.stdout)
    issues = [i for i in data.get("issues", []) if "internal" in i.get("type", "")]

    actions: list[dict] = []
    for i in issues:
        repo, dep, itype = i["repo"], i["dep"], i["type"]
        uses = dep in imported.get(repo, set())
        if itype == "internal_in_manifest_not_pyproject":
            actions.append(
                {
                    "action": "add_to_pyproject" if uses else "remove_from_manifest",
                    "repo": repo,
                    "dep": dep,
                    "uses": uses,
                }
            )
        else:
            actions.append(
                {
                    "action": "add_to_manifest" if uses else "remove_from_pyproject",
                    "repo": repo,
                    "dep": dep,
                    "uses": uses,
                }
            )

    if args.json:
        print(json.dumps({"actions": actions}, indent=2))
        return 0

    print(f"Planned {len(actions)} action(s) (code uses -> add; else -> remove):\n")
    for a in actions:
        print(f"  [{a['repo']}] {a['action']}: {a['dep']} (uses={a['uses']})")

    if args.apply:
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
            except Exception as e:
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
        verify = json.loads(r2.stdout)
        internal_issues = [i for i in verify.get("issues", []) if "internal" in i.get("type", "")]
        if internal_issues:
            print(f"Verification failed: {len(internal_issues)} internal mismatch(es) remaining.", file=sys.stderr)
            for i in internal_issues:
                print(f"  [{i['repo']}] {i['type']}: {i['dep']}", file=sys.stderr)
            return 1
        print("OK: 0 internal mismatches.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
