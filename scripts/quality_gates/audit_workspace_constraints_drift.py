# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Workspace-wide external dependency drift audit against workspace-constraints.toml.

Compares each Python repo's pyproject.toml [project.dependencies] against the canonical
version ranges in workspace-constraints.toml. Reports:
  - Floors below canonical (dep has >=X, constraint has >=Y where Y > X)
  - Floors above canonical (dep pins tighter floor than needed — not an error)
  - Ceilings above canonical (<X where constraint has <Y and Y < X — wider than allowed)
  - Ceilings below canonical (dep more restrictive — warn only)
  - Deps not in constraints (unknown / new deps — informational)

Usage:
    python scripts/quality_gates/audit_workspace_constraints_drift.py
    python scripts/quality_gates/audit_workspace_constraints_drift.py --fix     # auto-fix alignable drift
    python scripts/quality_gates/audit_workspace_constraints_drift.py --json    # machine-readable
    python scripts/quality_gates/audit_workspace_constraints_drift.py --repo execution-service

Exit codes:
    0 = no errors (warnings OK)
    1 = errors found
    2 = config error
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
from typing import Any

PM_ROOT = Path(__file__).resolve().parents[2]  # scripts/quality_gates/ → scripts/ → unified-trading-pm/
WORKSPACE_ROOT = Path(os.environ.get("WORKSPACE_ROOT", str(PM_ROOT.parent)))
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints.toml"


def _norm(name: str) -> str:
    base = re.sub(r"\[.*?\]", "", name)
    return re.sub(r"[-_.]", "-", base.strip().lower())


def _parse_version_floor(spec: str) -> str | None:
    m = re.search(r">=\s*(\S+?)(?:,|$)", spec)
    return m.group(1) if m else None


def _parse_version_ceiling(spec: str) -> str | None:
    m = re.search(r"<\s*(\S+?)(?:,|$)", spec)
    return m.group(1) if m else None


def _ver_tuple(v: str) -> tuple[int, ...]:
    parts = re.split(r"[.\-]", v.split("+")[0].split("a")[0].split("b")[0].split("rc")[0])
    result = []
    for p in parts:
        try:
            result.append(int(p))
        except ValueError:
            break
    return tuple(result)


def _ver_lt(a: str, b: str) -> bool:
    return _ver_tuple(a) < _ver_tuple(b)


def _ver_gt(a: str, b: str) -> bool:
    return _ver_tuple(a) > _ver_tuple(b)


@dataclass
class DriftEntry:
    repo: str
    dep_name: str
    dep_raw: str
    canon_raw: str
    kind: (
        str  # "floor_below_canon" | "ceiling_above_canon" | "exact_pin" | "warn_tighter_ceiling" | "not_in_constraints"
    )
    detail: str


@dataclass
class RepoResult:
    repo: str
    errors: list[DriftEntry] = field(default_factory=list)
    warnings: list[DriftEntry] = field(default_factory=list)
    unknown_deps: list[str] = field(default_factory=list)
    dep_count: int = 0
    checked: int = 0


def load_constraints(path: Path) -> dict[str, str]:
    """Returns normalised_name -> canonical_spec."""
    with open(path, "rb") as f:
        data = tomllib.load(f)
    deps = data.get("dependencies", {})  # noqa: qg-empty-fallback
    return {_norm(k): v for k, v in deps.items()}


def load_pyproject_deps(path: Path) -> list[str]:
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        project = data.get("project", {})  # noqa: qg-empty-fallback
        if not isinstance(project, dict):
            return []
        deps = project.get("dependencies", [])  # noqa: qg-empty-fallback
        return [d for d in deps if isinstance(d, str)]
    except (OSError, tomllib.TOMLDecodeError):
        return []


# Internal package names — skip alignment checks for these
INTERNAL_PKG_RE = re.compile(r"^unified-")


def is_internal(name: str) -> bool:
    return bool(INTERNAL_PKG_RE.match(_norm(name)))


def audit_repo(repo_path: Path, constraints: dict[str, str]) -> RepoResult:
    result = RepoResult(repo=repo_path.name)
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.exists():
        return result

    deps = load_pyproject_deps(pyproject)
    result.dep_count = len(deps)

    for dep_raw in deps:
        # Parse dep name + extras
        m = re.match(r"^([a-zA-Z0-9][a-zA-Z0-9._-]*(?:\[[a-zA-Z0-9_,]+\])?)\s*(.*)", dep_raw.strip())
        if not m:
            continue
        dep_name = m.group(1)
        dep_spec = m.group(2)

        if is_internal(dep_name):
            continue

        norm = _norm(dep_name)
        canon_raw = constraints.get(norm)
        if canon_raw is None:
            result.unknown_deps.append(dep_name)
            continue

        result.checked += 1

        dep_floor = _parse_version_floor(dep_spec)
        dep_ceiling = _parse_version_ceiling(dep_spec)
        canon_floor = _parse_version_floor(canon_raw)
        canon_ceiling = _parse_version_ceiling(canon_raw)

        canon_is_exact_pin = bool(re.search(r"==\s*\d", canon_raw))
        dep_is_exact_pin = bool(re.search(r"==\s*\d", dep_spec))

        if canon_is_exact_pin:
            # Canonical is an exact pin (ruff, basedpyright) — repo must match exactly
            canon_pin_ver_m = re.search(r"==\s*(\S+)", canon_raw)
            dep_pin_ver_m = re.search(r"==\s*(\S+)", dep_spec)
            if dep_is_exact_pin and canon_pin_ver_m and dep_pin_ver_m:
                if canon_pin_ver_m.group(1) != dep_pin_ver_m.group(1):
                    result.errors.append(
                        DriftEntry(
                            repo=repo_path.name,
                            dep_name=dep_name,
                            dep_raw=dep_raw,
                            canon_raw=canon_raw,
                            kind="exact_pin_mismatch",
                            detail=f"=={dep_pin_ver_m.group(1)} != canonical =={canon_pin_ver_m.group(1)}",
                        )
                    )
            # If repo doesn't pin at all or uses range, that's also wrong for exact-pin canonicals
            elif not dep_is_exact_pin:
                result.errors.append(
                    DriftEntry(
                        repo=repo_path.name,
                        dep_name=dep_name,
                        dep_raw=dep_raw,
                        canon_raw=canon_raw,
                        kind="missing_exact_pin",
                        detail=f"canonical requires exact pin {canon_raw}, repo has: {dep_spec!r}",
                    )
                )
            continue

        if dep_is_exact_pin and not canon_is_exact_pin:
            # Repo uses exact pin but canonical is a range — violation
            result.errors.append(
                DriftEntry(
                    repo=repo_path.name,
                    dep_name=dep_name,
                    dep_raw=dep_raw,
                    canon_raw=canon_raw,
                    kind="exact_pin_on_range_dep",
                    detail=f"exact pin {dep_spec!r} — canonical is a range: {canon_raw}",
                )
            )
            continue

        # Floor: repo uses lower floor than canonical → error (could pull in old vulnerable version)
        if dep_floor and canon_floor and _ver_lt(dep_floor, canon_floor):
            result.errors.append(
                DriftEntry(
                    repo=repo_path.name,
                    dep_name=dep_name,
                    dep_raw=dep_raw,
                    canon_raw=canon_raw,
                    kind="floor_below_canon",
                    detail=f">={dep_floor} < canonical >={canon_floor}",
                )
            )

        # Floor: repo uses higher floor than canonical → just informational (fine)

        # Ceiling: repo allows higher version than canonical ceiling → error (could pull in breaking release)
        if dep_ceiling and canon_ceiling:
            if _ver_gt(dep_ceiling, canon_ceiling):
                result.errors.append(
                    DriftEntry(
                        repo=repo_path.name,
                        dep_name=dep_name,
                        dep_raw=dep_raw,
                        canon_raw=canon_raw,
                        kind="ceiling_above_canon",
                        detail=f"<{dep_ceiling} > canonical <{canon_ceiling} — wider than allowed",
                    )
                )
            elif _ver_lt(dep_ceiling, canon_ceiling):
                # Tighter ceiling — warn only
                result.warnings.append(
                    DriftEntry(
                        repo=repo_path.name,
                        dep_name=dep_name,
                        dep_raw=dep_raw,
                        canon_raw=canon_raw,
                        kind="warn_tighter_ceiling",
                        detail=f"<{dep_ceiling} < canonical <{canon_ceiling} — more restrictive (may need widening)",
                    )
                )

        # Missing ceiling — warn if canonical has one
        if not dep_ceiling and canon_ceiling:
            result.warnings.append(
                DriftEntry(
                    repo=repo_path.name,
                    dep_name=dep_name,
                    dep_raw=dep_raw,
                    canon_raw=canon_raw,
                    kind="missing_ceiling",
                    detail=f"no upper bound; canonical has <{canon_ceiling}",
                )
            )

    return result


def fix_dep_in_file(pyproject_path: Path, dep_name: str, new_spec: str) -> bool:
    """Replace the version spec for dep_name in pyproject.toml. Returns True if changed."""
    content = pyproject_path.read_text()
    name_variants = [dep_name, dep_name.replace("-", "_"), dep_name.replace("_", "-")]
    for variant in name_variants:
        # Match only quoted dep entries (inside the dependencies array) — not comments
        pat = re.compile(
            r'(?m)^(\s*")'  # start of a quoted dep line (indented)
            + r"("
            + re.escape(variant)
            + r"(?:\[[^\]]*\])?)"
            + r'([^"]+)'
            + r'(")',
            re.IGNORECASE,
        )
        m = pat.search(content)
        if m:
            # Reconstruct: indent + quote + name+extras + new_spec + closing quote
            new_dep = m.group(1) + m.group(2) + new_spec + m.group(4)
            new_content = content[: m.start()] + new_dep + content[m.end() :]
            if new_content != content:
                pyproject_path.write_text(new_content)
                return True
    return False


def _build_fixed_spec(err: DriftEntry, canon_raw: str) -> str:
    """Build the corrected spec, preserving tighter floors when only ceiling is wrong."""
    dep_spec = re.sub(r"^[^><=!]*", "", err.dep_raw)  # strip dep name prefix
    dep_floor = _parse_version_floor(dep_spec)
    canon_floor = _parse_version_floor(canon_raw)
    canon_ceiling = _parse_version_ceiling(canon_raw)

    if err.kind == "ceiling_above_canon" and dep_floor and canon_floor and _ver_gt(dep_floor, canon_floor):
        # Preserve the repo's floor if it's tighter (higher) than canonical
        if canon_ceiling:
            return f">={dep_floor},<{canon_ceiling}"
        return f">={dep_floor}"
    # Default: use the full canonical spec
    spec_m = re.search(r"[><=!].*", canon_raw)
    return spec_m.group(0) if spec_m else ""


def apply_fixes(results: list[RepoResult], constraints: dict[str, str], workspace_root: Path) -> int:
    """Fix errors in-place. Returns count of fixed deps."""
    fixed = 0
    for result in results:
        for err in result.errors:
            if err.kind in ("floor_below_canon", "ceiling_above_canon"):
                repo_path = workspace_root / err.repo
                pyproject_path = repo_path / "pyproject.toml"
                norm = _norm(err.dep_name)
                canon_full = constraints.get(norm, "")
                new_spec = _build_fixed_spec(err, canon_full)
                if not new_spec:
                    continue
                if fix_dep_in_file(pyproject_path, err.dep_name, new_spec):
                    print(f"  FIXED {err.repo}: {err.dep_name} → {new_spec}")
                    fixed += 1
    return fixed


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit workspace pyproject.toml vs workspace-constraints.toml")
    parser.add_argument("--fix", action="store_true", help="Auto-fix alignable errors")
    parser.add_argument("--json", dest="json_out", action="store_true", help="JSON output")
    parser.add_argument("--repo", help="Audit single repo only")
    parser.add_argument("--errors-only", action="store_true", help="Skip warnings")
    args = parser.parse_args()

    if not CONSTRAINTS_PATH.exists():
        print(f"ERROR: {CONSTRAINTS_PATH} not found", file=sys.stderr)
        return 2

    constraints = load_constraints(CONSTRAINTS_PATH)

    # Collect repos
    if args.repo:
        repo_dirs = [WORKSPACE_ROOT / args.repo]
    else:
        repo_dirs = sorted([p for p in WORKSPACE_ROOT.iterdir() if p.is_dir() and (p / "pyproject.toml").exists()])

    results: list[RepoResult] = []
    for repo_dir in repo_dirs:
        if repo_dir.name.startswith("."):
            continue
        r = audit_repo(repo_dir, constraints)
        results.append(r)

    total_errors = sum(len(r.errors) for r in results)
    total_warnings = sum(len(r.warnings) for r in results)
    total_unknown = sum(len(r.unknown_deps) for r in results)

    if args.fix:
        fixed = apply_fixes(results, constraints, WORKSPACE_ROOT)
        print(f"\nFixed {fixed} dep(s). Re-run without --fix to verify.")
        # Re-audit
        results = []
        for repo_dir in repo_dirs:
            if repo_dir.name.startswith("."):
                continue
            results.append(audit_repo(repo_dir, constraints))
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)

    if args.json_out:
        out: dict[str, Any] = {
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_unknown_deps": total_unknown,
            "repos": [],
        }
        for r in results:
            if not r.errors and not r.warnings and not r.unknown_deps:
                continue
            out["repos"].append(
                {  # type: ignore[union-attr]
                    "repo": r.repo,
                    "dep_count": r.dep_count,
                    "checked": r.checked,
                    "errors": [
                        {
                            "dep": e.dep_name,
                            "kind": e.kind,
                            "detail": e.detail,
                            "dep_raw": e.dep_raw,
                            "canon": e.canon_raw,
                        }
                        for e in r.errors
                    ],
                    "warnings": [{"dep": w.dep_name, "kind": w.kind, "detail": w.detail} for w in r.warnings],
                    "unknown_deps": r.unknown_deps,
                }
            )
        print(json.dumps(out, indent=2))
        return 0 if total_errors == 0 else 1

    # Human-readable output
    print(f"\n{'=' * 70}")
    print(f" Workspace constraints drift audit — {len(repo_dirs)} repos")
    print(f" Constraints: {CONSTRAINTS_PATH.name} ({len(constraints)} packages)")
    print(f"{'=' * 70}\n")

    for r in results:
        if not r.errors and (args.errors_only or not r.warnings):
            continue
        if r.errors or r.warnings:
            print(f"{'─' * 60}")
            print(f" {r.repo}  ({r.dep_count} deps, {r.checked} checked vs constraints)")
            if r.errors:
                print("  ❌ ERRORS:")
                for e in r.errors:
                    print(f"     [{e.kind}] {e.dep_name}: {e.detail}")
                    print(f"       repo:   {e.dep_raw}")
                    print(f"       canon:  {e.canon_raw}")
            if r.warnings and not args.errors_only:
                print("  ⚠️  WARNINGS:")
                for w in r.warnings:
                    print(f"     [{w.kind}] {w.dep_name}: {w.detail}")

    print(f"\n{'=' * 70}")
    print(f" SUMMARY: {total_errors} error(s), {total_warnings} warning(s), {total_unknown} unknown dep(s)")
    repos_with_errors = [r.repo for r in results if r.errors]
    if repos_with_errors:
        print(f" Repos with errors ({len(repos_with_errors)}): {', '.join(repos_with_errors)}")
        print()
        print(" To auto-fix: python scripts/quality_gates/audit_workspace_constraints_drift.py --fix")
    else:
        print(" ✅ No errors — all checked deps within canonical constraint bounds.")
    print(f"{'=' * 70}\n")

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
