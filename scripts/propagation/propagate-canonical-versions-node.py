#!/usr/bin/env python3
"""Propagate workspace canonical Node dependency versions to UI repo package.json files.

Reads unified-trading-pm/workspace-constraints-node.json and workspace-manifest.json,
then for each UI repo with package.json: replaces version specs for constrained packages
with the canonical spec, leaves file: and @unified-trading/* deps unchanged, and runs npm install.

Usage:
    python propagate-canonical-versions-node.py              # dry run (print changes only)
    python propagate-canonical-versions-node.py --apply       # write package.json and run npm install
    python propagate-canonical-versions-node.py --apply --commit  # also git add/commit per repo
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints-node.json"


def load_manifest() -> dict:
    with open(MANIFEST_PATH) as f:
        return json.load(f)


def get_ui_repos(manifest: dict) -> list[str]:
    """Return UI repo names from manifest, or scan workspace for package.json."""
    repos = manifest.get("repositories") or {}
    ui_repos = [name for name, meta in repos.items() if isinstance(meta, dict) and meta.get("type") == "ui"]
    if ui_repos:
        return ui_repos
    return [
        d.name
        for d in WORKSPACE_ROOT.iterdir()
        if d.is_dir() and (d / "package.json").is_file() and "node_modules" not in str(d) and d.name != "src"
    ]


def get_repo_path(manifest: dict, repo_name: str) -> Path:
    repos = manifest.get("repositories") or {}
    entry = repos.get(repo_name)
    if isinstance(entry, dict) and isinstance(entry.get("folder_name"), str):
        return WORKSPACE_ROOT / entry["folder_name"]
    return WORKSPACE_ROOT / repo_name


def load_constraints() -> dict[str, dict[str, str]]:
    """Load dependencies and devDependencies from workspace-constraints-node.json."""
    if not CONSTRAINTS_PATH.is_file():
        return {}
    data = json.loads(CONSTRAINTS_PATH.read_text(encoding="utf-8"))
    result: dict[str, dict[str, str]] = {}
    for key in ("dependencies", "devDependencies"):
        if key in data and isinstance(data[key], dict):
            result[key] = {k: str(v) for k, v in data[key].items()}
    return result


def update_package_json(pkg: dict, constraints: dict[str, dict[str, str]]) -> dict:
    """Merge canonical versions into package.json. Returns new dict, does not mutate."""
    out = json.loads(json.dumps(pkg))
    for dep_type in ("dependencies", "devDependencies"):
        if dep_type not in constraints:
            continue
        canon = constraints[dep_type]
        deps = out.get(dep_type)
        if not isinstance(deps, dict):
            continue
        for name, canon_spec in canon.items():
            if name in deps:
                current = deps[name]
                if isinstance(current, str) and not current.startswith("file:"):
                    if not name.startswith("@unified-trading/"):
                        deps[name] = canon_spec
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Propagate canonical Node versions to UI repo package.json files")
    parser.add_argument("--apply", action="store_true", help="Write changes and run npm install")
    parser.add_argument("--commit", action="store_true", help="Git add and commit (implies --apply)")
    args = parser.parse_args()
    do_apply = args.apply or args.commit
    do_commit = args.commit

    if not CONSTRAINTS_PATH.is_file():
        print(f"ERROR: Constraints file not found: {CONSTRAINTS_PATH}", file=sys.stderr)
        sys.exit(1)
    if not MANIFEST_PATH.is_file():
        print(f"ERROR: Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)

    constraints = load_constraints()
    if not constraints:
        print("ERROR: No dependencies in workspace-constraints-node.json", file=sys.stderr)
        sys.exit(1)

    manifest = load_manifest()
    ui_repos = get_ui_repos(manifest)
    updated: list[str] = []

    for repo_name in sorted(ui_repos):
        repo_path = get_repo_path(manifest, repo_name)
        pkg_path = repo_path / "package.json"
        if not pkg_path.is_file():
            continue
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
        new_pkg = update_package_json(pkg, constraints)
        if json.dumps(new_pkg, sort_keys=True, indent=2) != json.dumps(pkg, sort_keys=True, indent=2):
            updated.append(repo_name)
            if do_apply:
                pkg_path.write_text(
                    json.dumps(new_pkg, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                print(f"  Updated {repo_name}/package.json")
                r = subprocess.run(
                    ["npm", "install"],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                )
                if r.returncode != 0:
                    print(f"    WARNING: npm install failed: {r.stderr}", file=sys.stderr)
                else:
                    print("    npm install OK")
                if do_commit:
                    subprocess.run(
                        ["git", "add", "package.json", "package-lock.json"],
                        cwd=repo_path,
                        check=False,
                    )
                    subprocess.run(
                        [
                            "git",
                            "commit",
                            "-m",
                            "chore: align dependencies to workspace canonical Node versions",
                        ],
                        cwd=repo_path,
                        check=False,
                    )
            else:
                print(f"  Would update {repo_name}/package.json")

    if not updated:
        print("No UI repos needed updates.")
    elif not do_apply:
        print(f"\n{len(updated)} repo(s) would be updated. Run with --apply to write and run npm install.")


if __name__ == "__main__":
    main()
