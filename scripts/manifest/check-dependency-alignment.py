#!/usr/bin/env python3
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

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
DERIVED_PATH = PM_ROOT / "derived-dependency-manifest.json"
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CANONICAL_PATH = PM_ROOT / "canonical-dependency-manifest.json"

JsonDict = dict[str, object]


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


def main() -> int:
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
    manifest_repos_raw = _jdict(manifest.get("repositories")) or {}

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
                specs_list = _jlist(specs_obj) or [] if isinstance(specs_obj, list) else [specs_obj]
                for spec in specs_list:
                    spec_str = _jstr(spec)
                    if spec_str != canon_spec:
                        issues.append(
                            {
                                "repo": repo_name,
                                "type": "external_version_mismatch",
                                "dep": pkg,
                                "pyproject_spec": spec_str,
                                "canonical_spec": canon_spec,
                            }
                        )

    if json_output:
        out: dict[str, object] = {"aligned": len(issues) == 0, "issues": issues, "count": len(issues)}
        print(json.dumps(out, indent=2))
    else:
        if not issues:
            print("OK: All dependencies aligned with manifest and canonical constraints.")
            return 0
        print(f"Found {len(issues)} misalignment(s):\n")
        for i in issues:
            print(f"  [{i['repo']}] {i['type']}: {i['dep']}")
            if "pyproject_spec" in i:
                print(f"    pyproject: {i['pyproject_spec']}")
                print(f"    canonical: {i['canonical_spec']}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
