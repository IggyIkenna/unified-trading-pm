#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Check that all repo pyproject.toml dependency versions align with
canonical-dependency-manifest.json.

Usage:
    python scripts/check_dependency_alignment.py
    python scripts/check_dependency_alignment.py --json        # machine-readable output
    python scripts/check_dependency_alignment.py --repo instruments-service  # single repo

Exit codes:
    0 = all aligned
    1 = violations found
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.version import Version

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


_pm_root = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", str(_pm_root.parent)))
MANIFEST_PATH = Path(__file__).resolve().parents[1] / "canonical-dependency-manifest.json"
WORKSPACE_MANIFEST_PATH = Path(__file__).resolve().parents[1] / "workspace-manifest.json"


def load_internal_package_names(workspace_manifest: Path) -> frozenset[str]:
    """
    Load all repo names from workspace-manifest.json and return them as a
    frozenset of normalised package names (hyphens, lowercase).
    These are internal packages — never in PyPI — so skip them in alignment checks.
    Falls back to an empty set if the manifest is missing (graceful degradation).
    """
    if not workspace_manifest.exists():
        return frozenset()
    try:
        data = cast(JsonDict, json.loads(workspace_manifest.read_text()))
        repos = _jdict(data.get("repositories")) or {}
        return frozenset(re.sub(r"[-_]", "-", _jstr(name).strip().lower()) for name in repos)
    except (OSError, json.JSONDecodeError):
        return frozenset()


# Loaded once at module level; updated whenever workspace-manifest.json changes
_INTERNAL_PACKAGES: frozenset[str] = load_internal_package_names(WORKSPACE_MANIFEST_PATH)


# Normalise package name: lowercase, replace - and _ with canonical form
def _norm(name: str) -> str:
    """Canonical package name: lowercase, hyphens normalised."""
    # Strip extras like [standard] or [s3,secretsmanager]
    base = re.sub(r"\[.*\]", "", name)
    return re.sub(r"[-_]", "-", base.strip().lower())


def _strip_extras(specifier_str: str) -> str:
    """Remove extras from a requirement string before parsing."""
    return re.sub(r"\[.*?\]", "", specifier_str)


@dataclass
class CanonicalEntry:
    name: str
    norm_name: str
    version_range: str  # raw string e.g. "pandas>=2.3.0,<3.0.0"
    specifier: SpecifierSet

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> CanonicalEntry:
        name = d["name"]
        version_range = d["versionRange"]
        # Parse just the specifier part (strip package name + extras)
        try:
            req = Requirement(_strip_extras(version_range))
            spec = req.specifier
        except (OSError, json.JSONDecodeError):
            spec = SpecifierSet()
        return cls(
            name=name,
            norm_name=_norm(name),
            version_range=version_range,
            specifier=spec,
        )


@dataclass
class Violation:
    repo: str
    package: str
    repo_spec: str  # what the repo says
    canonical_spec: str  # what canonical says
    severity: str  # "MISMATCH" | "UNPINNED" | "UNKNOWN"
    section: str  # "dependencies" | "dev"


@dataclass
class RepoResult:
    repo: str
    pyproject: Path
    violations: list[Violation] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""
    checked_deps: int = 0


def load_canonical(manifest_path: Path) -> dict[str, CanonicalEntry]:
    data = cast(JsonDict, json.loads(manifest_path.read_text()))
    ext = _jlist(data.get("externalPackages")) or []
    result: dict[str, CanonicalEntry] = {}
    for e in ext:
        ed = _jdict(e)
        if ed:
            name = _jstr(ed.get("name"))
            version_range = _jstr(ed.get("versionRange"))
            result[_norm(name)] = CanonicalEntry.from_dict({"name": name, "versionRange": version_range})
    return result


def is_internal(name: str) -> bool:
    """Return True if the package name matches a known internal (workspace) repo."""
    return _norm(name) in _INTERNAL_PACKAGES


def check_specifier_compatible(repo_spec_str: str, canonical: CanonicalEntry) -> tuple[bool, str]:
    """
    Returns (is_compatible, reason).
    A repo specifier is compatible if every version it allows is also
    allowed by the canonical specifier.  We do a simple structural check:
    - If canonical is exact pin (==), repo must use the same exact pin.
    - Otherwise, repo specifier must be a subset of (or equal to) canonical.
    We approximate subset by checking lower-bound >= canonical lower and
    upper-bound <= canonical upper.
    """
    if not repo_spec_str or repo_spec_str == "*":
        return False, "no version constraint (must pin to canonical range)"

    try:
        repo_spec = SpecifierSet(_strip_extras(repo_spec_str))
    except (OSError, json.JSONDecodeError):
        return False, f"unparseable specifier: {repo_spec_str!r}"

    canonical_str = str(canonical.specifier)

    # Exact pin in canonical (e.g. ruff==0.15.0)
    canonical_pins = [s for s in canonical.specifier if s.operator == "=="]
    if canonical_pins:
        repo_pins = [s for s in repo_spec if s.operator == "=="]
        if not repo_pins:
            return False, f"canonical requires exact pin {canonical_str}; repo has {repo_spec_str!r}"
        if repo_pins[0].version != canonical_pins[0].version:
            return False, (f"exact pin mismatch: canonical=={canonical_pins[0].version}, repo=={repo_pins[0].version}")
        return True, ""

    # No canonical specifier — package exists but no version range defined
    if not canonical_str:
        return True, ""  # e.g. pandas-gbq (no range)

    # Check that repo version is compatible with canonical (not obviously outside)
    # We check: repo's >= lower >= canonical's >= lower (not too old)
    # and repo's < upper <= canonical's < upper (not too new)
    def _extract(spec: SpecifierSet, op: str) -> Version | None:
        for s in spec:
            if s.operator == op:
                try:
                    return Version(s.version)
                except (OSError, json.JSONDecodeError):
                    pass
        return None

    canon_min = _extract(canonical.specifier, ">=")
    canon_max = _extract(canonical.specifier, "<")
    repo_min = _extract(repo_spec, ">=")
    repo_max = _extract(repo_spec, "<")

    reasons = []

    if canon_min and repo_min and repo_min < canon_min:
        reasons.append(f"lower bound too old: repo>={repo_min} < canonical>={canon_min}")

    if canon_max and repo_max and repo_max > canon_max:
        reasons.append(f"upper bound too high: repo<{repo_max} > canonical<{canon_max}")

    # If repo has no upper bound but canonical does — flag it
    if canon_max and not repo_max:
        # Only flag if repo also has no == pin
        repo_eq = [s for s in repo_spec if s.operator == "=="]
        if not repo_eq:
            reasons.append(f"missing upper bound; canonical requires <{canon_max}")

    if reasons:
        return False, "; ".join(reasons)
    return True, ""


def check_repo(
    repo_path: Path,
    canonical: dict[str, CanonicalEntry],
) -> RepoResult:
    pyproject_path = repo_path / "pyproject.toml"
    result = RepoResult(repo=repo_path.name, pyproject=pyproject_path)

    if not pyproject_path.exists():
        result.skipped = True
        result.skip_reason = "no pyproject.toml"
        return result

    try:
        data = cast(JsonDict, tomllib.loads(pyproject_path.read_text()))
    except (OSError, ValueError, tomllib.TOMLDecodeError) as e:
        result.skipped = True
        result.skip_reason = f"parse error: {e}"
        return result

    project = _jdict(data.get("project")) or {}
    deps_raw = _jlist(project.get("dependencies")) or []
    deps: list[str] = [_jstr(x) for x in deps_raw]
    optional = _jdict(project.get("optional-dependencies")) or {}
    dev_raw = _jlist(optional.get("dev")) or []
    dev_deps: list[str] = [_jstr(x) for x in dev_raw]

    def _check_deps(dep_list: list[str], section: str) -> None:
        for dep_str in dep_list:
            dep_str = dep_str.strip()
            if not dep_str or dep_str.startswith("#"):
                continue
            # Strip inline comments
            dep_str = dep_str.split("#")[0].strip()
            if not dep_str:
                continue

            try:
                req = Requirement(dep_str)
            except (OSError, json.JSONDecodeError):
                continue

            pkg_name = req.name
            if is_internal(pkg_name):
                continue

            norm = _norm(pkg_name)
            result.checked_deps += 1

            if norm not in canonical:
                # Not in canonical manifest — skip (internal or unknown package)
                continue

            canon_entry = canonical[norm]
            spec_str = str(req.specifier)

            # If canonical has no version range, nothing to enforce
            if not str(canon_entry.specifier):
                continue

            ok, _reason = check_specifier_compatible(spec_str, canon_entry)
            if not ok:
                result.violations.append(
                    Violation(
                        repo=repo_path.name,
                        package=pkg_name,
                        repo_spec=spec_str or "(none)",
                        canonical_spec=canon_entry.version_range,
                        severity="MISMATCH",
                        section=section,
                    )
                )

    _check_deps(deps, "dependencies")
    _check_deps(dev_deps, "dev")
    return result


def find_repos(workspace: Path, single_repo: str | None) -> list[Path]:
    """
    Return repo paths to check.

    When workspace-manifest.json is present, use its repo list as the canonical
    source so new repos are picked up automatically.  Repos that don't exist on
    disk are silently skipped — not all developers clone every repo.

    Falls back to scanning workspace subdirs for pyproject.toml if the manifest
    is unavailable.
    """
    if single_repo:
        p = workspace / single_repo
        if not p.is_dir():
            print(f"ERROR: repo not found: {p}")
            sys.exit(1)
        return [p]

    # Prefer manifest-driven repo list
    if WORKSPACE_MANIFEST_PATH.exists():
        try:
            data = cast(JsonDict, json.loads(WORKSPACE_MANIFEST_PATH.read_text()))
            repos_d = _jdict(data.get("repositories")) or {}
            repo_names = sorted(repos_d.keys())
            repos = []
            for name in repo_names:
                p = workspace / name
                if p.is_dir() and (p / "pyproject.toml").exists():
                    repos.append(p)
            return repos
        except (OSError, json.JSONDecodeError):
            pass  # fall through to filesystem scan

    # Fallback: scan workspace for pyproject.toml dirs
    return sorted(
        child
        for child in workspace.iterdir()
        if child.is_dir()
        and not child.name.startswith(".")
        and not child.name.startswith("_")
        and (child / "pyproject.toml").exists()
    )


def print_report(results: list[RepoResult], *, show_clean: bool = False) -> int:
    """Print human-readable report. Returns exit code."""
    total_violations = sum(len(r.violations) for r in results)
    total_checked = sum(r.checked_deps for r in results)
    repos_with_issues = [r for r in results if r.violations]
    repos_clean = [r for r in results if not r.violations and not r.skipped]
    repos_skipped = [r for r in results if r.skipped]

    # Header
    print("\n" + "=" * 72)
    print("  CANONICAL DEPENDENCY ALIGNMENT CHECK")
    print("=" * 72)
    print(f"  Repos scanned:     {len(results)}")
    print(f"  Deps checked:      {total_checked}")
    print(f"  Repos with issues: {len(repos_with_issues)}")
    print(f"  Clean repos:       {len(repos_clean)}")
    print(f"  Skipped (no toml): {len(repos_skipped)}")
    print("=" * 72)

    if repos_with_issues:
        print("\n── VIOLATIONS ──────────────────────────────────────────────────────")
        for result in repos_with_issues:
            print(f"\n  [{result.repo}]  ({len(result.violations)} violation(s))")
            for v in sorted(result.violations, key=lambda x: x.package):
                print(f"    {'[' + v.section + ']':<16} {v.package}")
                print(f"      repo:      {v.repo_spec}")
                print(f"      canonical: {v.canonical_spec}")

    if show_clean and repos_clean:
        print("\n── CLEAN ───────────────────────────────────────────────────────────")
        for r in repos_clean:
            print(f"  ✓  {r.repo}  ({r.checked_deps} deps checked)")

    if repos_skipped:
        print("\n── SKIPPED ─────────────────────────────────────────────────────────")
        for r in repos_skipped:
            print(f"  -  {r.repo}  ({r.skip_reason})")

    print("\n" + "=" * 72)
    if total_violations == 0:
        print("  RESULT: ✓ ALL ALIGNED")
    else:
        print(f"  RESULT: ✗ {total_violations} VIOLATION(S) ACROSS {len(repos_with_issues)} REPO(S)")
    print("=" * 72 + "\n")

    return 0 if total_violations == 0 else 1


def print_json_report(results: list[RepoResult]) -> int:
    output = {
        "summary": {
            "repos_scanned": len(results),
            "repos_with_violations": sum(1 for r in results if r.violations),
            "total_violations": sum(len(r.violations) for r in results),
        },
        "repos": [],
    }
    for r in results:
        entry: dict = {
            "repo": r.repo,
            "skipped": r.skipped,
            "checked_deps": r.checked_deps,
            "violations": [
                {
                    "package": v.package,
                    "section": v.section,
                    "repo_spec": v.repo_spec,
                    "canonical_spec": v.canonical_spec,
                    "severity": v.severity,
                }
                for v in r.violations
            ],
        }
        if r.skipped:
            entry["skip_reason"] = r.skip_reason
        output["repos"].append(entry)

    print(json.dumps(output, indent=2))
    total = output["summary"]["total_violations"]
    return 0 if total == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Check pyproject.toml deps against canonical manifest")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of human-readable")
    parser.add_argument("--repo", metavar="NAME", help="Check a single repo only")
    parser.add_argument("--show-clean", action="store_true", help="Also list repos with no violations")
    args = parser.parse_args()
    repo_filter: str | None = cast(str | None, args.repo)
    json_out: bool = cast(bool, args.json)
    show_clean: bool = cast(bool, args.show_clean)

    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found: {MANIFEST_PATH}")
        sys.exit(1)

    canonical = load_canonical(MANIFEST_PATH)
    repos = find_repos(WORKSPACE_ROOT, repo_filter)

    results = [check_repo(repo, canonical) for repo in repos]

    if json_out:
        sys.exit(print_json_report(results))
    else:
        sys.exit(print_report(results, show_clean=show_clean))


if __name__ == "__main__":
    main()
