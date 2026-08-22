#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Auto-fix pyproject.toml dependency versions to align with canonical-dependency-manifest.json.

Strategy:
  - Parses each pyproject.toml to find misaligned deps
  - Replaces ONLY the version specifier in the raw file text (preserves formatting + comments)
  - Uses regex to find/replace the exact quoted dep string
  - Dry-run by default — pass --apply to write changes

Usage:
    python scripts/fix_dependency_alignment.py               # dry-run (safe preview)
    python scripts/fix_dependency_alignment.py --apply       # write changes
    python scripts/fix_dependency_alignment.py --repo instruments-service --apply
    python scripts/fix_dependency_alignment.py --json        # machine-readable dry-run

Exit codes:
    0 = nothing to fix (or --apply succeeded)
    1 = fixes needed (dry-run) or apply failed
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

from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

JsonDict = dict[str, object]


def _jdict(val: object):
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jlist(val: object):
    if isinstance(val, list):
        return cast(list[JsonDict], val)
    return None


def _jstr(val: object, default: str = ""):
    return str(val) if val is not None else default


# PM repo root (unified-trading-pm); workspace root is parent (where all repos live)
PM_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", str(PM_ROOT.parent)))
MANIFEST_PATH = PM_ROOT / "canonical-dependency-manifest.json"
WORKSPACE_MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"


def load_internal_package_names(workspace_manifest: Path) -> frozenset[str]:
    """
    Load all repo names from workspace-manifest.json as normalised package names.
    These are internal packages — never on PyPI — so skip them in alignment checks.
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


_INTERNAL_PACKAGES: frozenset[str] = load_internal_package_names(WORKSPACE_MANIFEST_PATH)


def _norm(name: str) -> str:
    base = re.sub(r"\[.*\]", "", name)
    return re.sub(r"[-_]", "-", base.strip().lower())


def _strip_extras(s: str) -> str:
    return re.sub(r"\[.*?\]", "", s)


def is_internal(name: str) -> bool:
    """Return True if the package name matches a known internal (workspace) repo."""
    return _norm(name) in _INTERNAL_PACKAGES


# ── Canonical loading ──────────────────────────────────────────────────────────


@dataclass
class CanonicalEntry:
    name: str
    norm_name: str
    version_range: str  # e.g. "pandas>=2.3.0,<3.0.0"
    specifier: SpecifierSet
    # The specifier string to USE when fixing (just the version part, e.g. ">=2.3.0,<3.0.0")
    fix_specifier: str

    @classmethod
    def from_dict(cls, d: dict[str, str]) -> CanonicalEntry:
        name = d["name"]
        version_range = d["versionRange"]
        try:
            req = Requirement(_strip_extras(version_range))
            spec = req.specifier
            fix_spec = str(spec)
        except InvalidRequirement:
            spec = SpecifierSet()
            fix_spec = ""
        return cls(
            name=name,
            norm_name=_norm(name),
            version_range=version_range,
            specifier=spec,
            fix_specifier=fix_spec,
        )


def load_canonical(manifest_path: Path) -> dict[str, CanonicalEntry]:
    data = cast(JsonDict, json.loads(manifest_path.read_text()))
    ext = _jlist(data.get("externalPackages")) or []
    result: dict[str, CanonicalEntry] = {}
    for e in ext:
        ed = _jdict(e)
        if ed:
            entry = {"name": _jstr(ed.get("name")), "versionRange": _jstr(ed.get("versionRange"))}
            result[_norm(_jstr(ed.get("name")))] = CanonicalEntry.from_dict(entry)
    return result


# ── Compatibility check (same logic as check script) ──────────────────────────


def needs_fix(repo_spec_str: str, canonical: CanonicalEntry) -> bool:
    """Return True if the repo specifier violates canonical."""
    if not repo_spec_str or repo_spec_str == "*":
        return bool(canonical.fix_specifier)

    try:
        repo_spec = SpecifierSet(_strip_extras(repo_spec_str))
    except InvalidSpecifier:
        return False

    canonical_str = str(canonical.specifier)

    # Exact pin
    canonical_pins = [s for s in canonical.specifier if s.operator == "=="]
    if canonical_pins:
        repo_pins = [s for s in repo_spec if s.operator == "=="]
        if not repo_pins:
            return True
        return repo_pins[0].version != canonical_pins[0].version

    if not canonical_str:
        return False

    def _extract(spec: SpecifierSet, op: str) -> Version | None:
        for s in spec:
            if s.operator == op:
                try:
                    return Version(s.version)
                except InvalidVersion:
                    pass
        return None

    canon_min = _extract(canonical.specifier, ">=")
    canon_max = _extract(canonical.specifier, "<")
    repo_min = _extract(repo_spec, ">=")
    repo_max = _extract(repo_spec, "<")

    if canon_min and repo_min and repo_min < canon_min:
        return True
    if canon_max and repo_max and repo_max > canon_max:
        return True
    if canon_max and not repo_max:
        repo_eq = [s for s in repo_spec if s.operator == "=="]
        if not repo_eq:
            return True

    return False


# ── Fix application ────────────────────────────────────────────────────────────


@dataclass
class Fix:
    package: str  # original name as written in pyproject.toml
    section: str
    old_spec: str  # e.g. ">=2.1.0,<2.4.0"
    new_spec: str  # e.g. ">=2.3.0,<2.4.0"
    old_line: str  # full original quoted dep string
    new_line: str  # full replacement quoted dep string
    applied: bool = False


@dataclass
class RepoFixResult:
    repo: str
    pyproject: Path
    fixes: list[Fix] = field(default_factory=list)
    skipped: bool = False
    skip_reason: str = ""
    write_error: str = ""


def build_new_dep_string(dep_str: str, new_spec: str) -> str:
    """
    Replace the version specifier in a dep string, preserving package name + extras.
    e.g. 'pandas>=2.2.3,<3.0.0' + '>=2.3.0,<3.0.0' → 'pandas>=2.3.0,<3.0.0'
    e.g. 'uvicorn[standard]>=0.27.0' + '>=0.27.0,<1.0.0' → 'uvicorn[standard]>=0.27.0,<1.0.0'
    """
    # Extract just the package name + extras (everything before the first version operator)
    match = re.match(r"^([A-Za-z0-9_.\-]+(?:\[[^\]]*\])?)\s*([><=!~].*)?$", dep_str.strip())
    if not match:
        return dep_str
    pkg_part = match.group(1)
    return f"{pkg_part}{new_spec}"


def find_and_collect_fixes(
    pyproject_path: Path,
    canonical: dict[str, CanonicalEntry],
) -> RepoFixResult:
    result = RepoFixResult(repo=pyproject_path.parent.name, pyproject=pyproject_path)

    if not pyproject_path.exists():
        result.skipped = True
        result.skip_reason = "no pyproject.toml"
        return result

    try:
        raw_text = pyproject_path.read_text()
        data = cast(JsonDict, tomllib.loads(raw_text))
    except (OSError, tomllib.TOMLDecodeError) as e:
        result.skipped = True
        result.skip_reason = f"parse error: {e}"
        return result

    project = _jdict(data.get("project")) or {}
    deps_raw = _jlist(project.get("dependencies")) or []
    deps = [_jstr(x) for x in deps_raw]
    dev_deps: list[str] = []  # no optional-dependencies — flat [project.dependencies] only

    def _collect(dep_list: list[str], section: str) -> None:
        for dep_str in dep_list:
            dep_str_clean = dep_str.strip().split("#")[0].strip()
            if not dep_str_clean:
                continue
            try:
                req = Requirement(dep_str_clean)
            except InvalidRequirement:
                continue

            if is_internal(req.name):
                continue

            norm = _norm(req.name)
            if norm not in canonical:
                continue

            canon = canonical[norm]
            if not canon.fix_specifier:
                continue  # no canonical range to enforce

            spec_str = str(req.specifier)
            if not needs_fix(spec_str, canon):
                continue

            # Build replacement strings
            old_dep = dep_str_clean
            new_dep = build_new_dep_string(dep_str_clean, canon.fix_specifier)

            if old_dep == new_dep:
                continue

            result.fixes.append(
                Fix(
                    package=req.name,
                    section=section,
                    old_spec=spec_str or "(none)",
                    new_spec=canon.fix_specifier,
                    old_line=old_dep,
                    new_line=new_dep,
                )
            )

    _collect(deps, "dependencies")
    _collect(dev_deps, "dev")
    return result


def apply_fixes_to_file(result: RepoFixResult) -> bool:
    """
    Apply all fixes by doing targeted string replacements in the raw TOML text.
    Returns True if the file was changed.
    """
    if result.skipped or not result.fixes:
        return False

    raw = result.pyproject.read_text()
    changed = False

    for fix in result.fixes:
        # We look for the dep string inside a quoted string in the TOML.
        # Pattern: "old_dep_string" (with optional trailing comment and whitespace)
        # We match the exact old dep string inside quotes, replacing only the version part.

        # Escape the old dep string for regex
        old_escaped = re.escape(fix.old_line)

        # Match: "pandas>=2.2.3,<3.0.0"  or  "pandas>=2.2.3,<3.0.0",
        # Handles both double-quoted and the trailing comma/comment
        pattern = r'("' + old_escaped + r'")'
        replacement = '"' + fix.new_line + '"'

        new_raw, count = re.subn(pattern, replacement, raw)

        if count > 0:
            raw = new_raw
            fix.applied = True
            changed = True
        else:
            # Try without quotes (some toml writers use different quoting)
            # Fallback: match just the dep string as a standalone token on a line
            pattern2 = r'(^\s*"?)(' + old_escaped + r')("?,?\s*(?:#.*)?)$'
            new_raw2, count2 = re.subn(pattern2, r"\g<1>" + fix.new_line + r"\g<3>", raw, flags=re.MULTILINE)
            if count2 > 0:
                raw = new_raw2
                fix.applied = True
                changed = True

    if changed:
        try:
            result.pyproject.write_text(raw)
        except OSError as e:
            result.write_error = str(e)
            return False

    return changed


# ── Reporting ──────────────────────────────────────────────────────────────────


def print_report(results: list[RepoFixResult], *, apply: bool) -> int:
    total_fixes = sum(len(r.fixes) for r in results)
    total_applied = sum(sum(1 for f in r.fixes if f.applied) for r in results)
    repos_with_fixes = [r for r in results if r.fixes]
    repos_clean = [r for r in results if not r.fixes and not r.skipped]
    repos_skipped = [r for r in results if r.skipped]
    repos_errors = [r for r in results if r.write_error]

    mode = "APPLIED" if apply else "DRY-RUN"
    print(f"\n{'=' * 72}")
    print(f"  CANONICAL DEPENDENCY FIX  [{mode}]")
    print(f"{'=' * 72}")
    print(f"  Repos scanned:    {len(results)}")
    print(f"  Repos with fixes: {len(repos_with_fixes)}")
    print(f"  Total fixes:      {total_fixes}")
    if apply:
        print(f"  Applied:          {total_applied}")
    print(f"{'=' * 72}")

    if repos_with_fixes:
        label = "CHANGES APPLIED" if apply else "PROPOSED CHANGES"
        print(f"\n── {label} {'─' * (60 - len(label))}")
        for result in repos_with_fixes:
            applied_count = sum(1 for f in result.fixes if f.applied)
            status = f"  ({applied_count}/{len(result.fixes)} applied)" if apply else f"  ({len(result.fixes)} fix(es))"
            print(f"\n  [{result.repo}]{status}")
            for fix in sorted(result.fixes, key=lambda x: x.package):
                icon = "✓" if fix.applied else ("✗" if apply else "→")
                print(f"    {icon} [{fix.section:<12}] {fix.package}")
                print(f"        old: {fix.old_line}")
                print(f"        new: {fix.new_line}")

    if repos_errors:
        print("\n── WRITE ERRORS ─────────────────────────────────────────────────────")
        for r in repos_errors:
            print(f"  ✗  {r.repo}: {r.write_error}")

    if repos_clean:
        print(f"\n── ALREADY ALIGNED ({len(repos_clean)} repos) ──────────────────────────────────────")
        for r in repos_clean:
            print(f"  ✓  {r.repo}")

    if repos_skipped:
        print("\n── SKIPPED ──────────────────────────────────────────────────────────")
        for r in repos_skipped:
            print(f"  -  {r.repo}  ({r.skip_reason})")

    print(f"\n{'=' * 72}")
    if not apply:
        if total_fixes == 0:
            print("  RESULT: ✓ NOTHING TO FIX — all aligned")
        else:
            print(f"  RESULT: {total_fixes} fix(es) ready — rerun with --apply to write changes")
    else:
        unapplied = total_fixes - total_applied
        if unapplied == 0:
            print(f"  RESULT: ✓ {total_applied} fix(es) applied successfully")
        else:
            print(f"  RESULT: ✓ {total_applied} applied, ✗ {unapplied} could not be matched")
            print("  NOTE: Unmatched fixes may use multiline TOML arrays — fix manually")
    print(f"{'=' * 72}\n")

    if not apply and total_fixes > 0:
        return 1
    if repos_errors:
        return 1
    return 0


def print_json_report(results: list[RepoFixResult], *, apply: bool) -> int:
    total_fixes = sum(len(r.fixes) for r in results)
    output = {
        "mode": "apply" if apply else "dry-run",
        "summary": {
            "repos_scanned": len(results),
            "repos_with_fixes": sum(1 for r in results if r.fixes),
            "total_fixes": total_fixes,
        },
        "repos": [
            {
                "repo": r.repo,
                "skipped": r.skipped,
                "fixes": [
                    {
                        "package": f.package,
                        "section": f.section,
                        "old": f.old_line,
                        "new": f.new_line,
                        "applied": f.applied,
                    }
                    for f in r.fixes
                ],
            }
            for r in results
        ],
    }
    print(json.dumps(output, indent=2))
    return 0 if total_fixes == 0 else 1


# ── Entry point ────────────────────────────────────────────────────────────────


def find_repos(workspace: Path, single_repo: str | None) -> list[Path]:
    """
    Return pyproject.toml paths to fix.

    Uses workspace-manifest.json as the canonical repo list so new repos are
    picked up automatically.  Repos that don't exist on disk are silently
    skipped — not all developers clone every repo.

    Falls back to a filesystem scan if the manifest is unavailable.
    """
    if single_repo:
        p = workspace / single_repo
        if not p.is_dir():
            print(f"ERROR: repo not found: {p}")
            sys.exit(1)
        return [p / "pyproject.toml"]

    # Prefer manifest-driven repo list
    if WORKSPACE_MANIFEST_PATH.exists():
        try:
            data = cast(JsonDict, json.loads(WORKSPACE_MANIFEST_PATH.read_text()))
            repos_d = _jdict(data.get("repositories")) or {}
            repo_names = sorted(repos_d.keys())
            return [
                workspace / name / "pyproject.toml"
                for name in repo_names
                if (workspace / name).is_dir() and (workspace / name / "pyproject.toml").exists()
            ]
        except (OSError, json.JSONDecodeError):
            pass  # fall through to filesystem scan

    # Fallback: scan workspace for pyproject.toml dirs
    return sorted(
        p / "pyproject.toml"
        for p in workspace.iterdir()
        if p.is_dir() and not p.name.startswith(".") and (p / "pyproject.toml").exists()
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix pyproject.toml deps to match canonical manifest")
    parser.add_argument("--apply", action="store_true", help="Write changes (default is dry-run)")
    parser.add_argument("--repo", metavar="NAME", help="Fix a single repo only")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    repo_filter: str | None = cast(str | None, args.repo)
    do_apply: bool = cast(bool, args.apply)
    json_out: bool = cast(bool, args.json)

    if not MANIFEST_PATH.exists():
        print(f"ERROR: manifest not found: {MANIFEST_PATH}")
        sys.exit(1)

    canonical = load_canonical(MANIFEST_PATH)
    pyprojects = find_repos(WORKSPACE_ROOT, repo_filter)

    results = [find_and_collect_fixes(p, canonical) for p in pyprojects]

    if do_apply:
        for result in results:
            apply_fixes_to_file(result)

    if json_out:
        sys.exit(print_json_report(results, apply=do_apply))
    else:
        sys.exit(print_report(results, apply=do_apply))


if __name__ == "__main__":
    main()
