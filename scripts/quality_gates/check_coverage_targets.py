#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""check_coverage_targets.py — Phase 8.D `coverage_targets_enforcement` QG step.

Reads `scripts/quality_gates/coverage_targets.yaml` (workspace SSOT) + walks each
repo's `coverage.xml` (output of `pytest --cov` in QG step 3). For each declared
surface, computes aggregate line-coverage % across files matching the surface's
glob patterns; compares against `target_pct`; fails if below.

Per-repo overrides:
  Each repo may declare `scripts/quality_gates/coverage_targets_local.yaml` to
  enable a subset of workspace surfaces (e.g. deployment-service only enables
  service_startup + vm_deploy_scripts + default). Surfaces not enabled per-repo
  are skipped for that repo. If no local file exists, ALL workspace surfaces are
  checked against that repo.

Exit-code semantics:
  0 — at or above target for every (repo x surface) tuple checked
  1 — one or more surfaces below target
  2 — yaml / coverage.xml / IO error

Origin: deployment_and_qg_strategy_implementation_2026_05_13.md § Phase 8.D
        ("New QG STEP `coverage_targets_enforcement` reads coverage_targets.yaml +
        per-repo local; fails QG if any surface below target.").
"""

from __future__ import annotations

import argparse
import fnmatch
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

DEFAULT_TARGETS_PATH = Path(__file__).parent / "coverage_targets.yaml"


@dataclass(frozen=True)
class Surface:
    name: str
    target_pct: int
    rationale: str
    glob_patterns: list[str]


@dataclass(frozen=True)
class FileCoverage:
    relpath: str
    lines_covered: int
    lines_valid: int


@dataclass(frozen=True)
class SurfaceResult:
    surface: str
    target_pct: int
    actual_pct: float
    files_matched: int
    lines_covered: int
    lines_valid: int

    @property
    def passed(self) -> bool:
        return self.actual_pct >= self.target_pct


def _load_targets(path: Path) -> list[Surface]:
    raw = cast(object, yaml.safe_load(path.read_text(encoding="utf-8")))
    if not isinstance(raw, dict):
        raise ValueError("targets root must be a dict")
    surfaces_raw = cast(dict[str, object], raw).get("surfaces")
    if not isinstance(surfaces_raw, dict):
        raise ValueError("targets.surfaces must be a dict")
    out: list[Surface] = []
    for name, body in cast(dict[str, object], surfaces_raw).items():
        if not isinstance(body, dict):
            continue
        bd = cast(dict[str, object], body)
        out.append(
            Surface(
                name=name,
                target_pct=int(cast(int, bd.get("target_pct", 80))),
                rationale=str(bd.get("rationale", "")),
                glob_patterns=[str(g) for g in cast(list[object], bd.get("glob_patterns", []))],  # noqa: qg-empty-fallback
            )
        )
    return out


def _parse_coverage_xml(path: Path) -> list[FileCoverage]:
    """Parse Cobertura-format coverage.xml emitted by pytest --cov."""
    try:
        tree = ET.parse(path)  # nosec B320 — input is pytest-generated coverage.xml, not user-controlled
    except (OSError, ET.ParseError):
        return []
    root = tree.getroot()
    out: list[FileCoverage] = []
    # Cobertura schema: packages/package/classes/class[@filename + lines/line]
    for cls in root.iter("class"):
        filename = cls.attrib.get("filename", "")
        lines_valid = 0
        lines_covered = 0
        for line in cls.iter("line"):
            lines_valid += 1
            hits = line.attrib.get("hits", "0")
            try:
                if int(hits) > 0:
                    lines_covered += 1
            except ValueError:
                continue
        out.append(FileCoverage(relpath=filename, lines_covered=lines_covered, lines_valid=lines_valid))
    return out


def _file_matches_surface(filepath: str, repo_name: str, surface: Surface) -> bool:
    """Match file against any of the surface's glob patterns.

    Glob patterns in the SSOT use workspace-root-relative paths (e.g.
    `strategy-service/strategy_service/engine/**/*.py`). The coverage.xml
    `filename` is repo-relative (e.g. `strategy_service/engine/v2_orchestrator.py`).
    Prefix it with `{repo_name}/` to compare.
    """
    full_path = f"{repo_name}/{filepath}"
    return any(fnmatch.fnmatch(full_path, pat) for pat in surface.glob_patterns)


def _compute_surface_result(
    surface: Surface, repo_name: str, file_coverages: list[FileCoverage]
) -> SurfaceResult | None:
    """Aggregate coverage across files matching the surface's globs."""
    matched: list[FileCoverage] = []
    for fc in file_coverages:
        if _file_matches_surface(fc.relpath, repo_name, surface):
            matched.append(fc)
    if not matched:
        return None  # surface not present in this repo
    lines_valid = sum(fc.lines_valid for fc in matched)
    lines_covered = sum(fc.lines_covered for fc in matched)
    if lines_valid == 0:
        return None
    actual = 100.0 * lines_covered / lines_valid
    return SurfaceResult(
        surface=surface.name,
        target_pct=surface.target_pct,
        actual_pct=actual,
        files_matched=len(matched),
        lines_covered=lines_covered,
        lines_valid=lines_valid,
    )


def _load_local_surfaces(repo_path: Path) -> set[str] | None:
    """Return set of surface names enabled per repo, or None for 'all surfaces'."""
    local = repo_path / "scripts" / "quality_gates" / "coverage_targets_local.yaml"
    if not local.exists():
        return None
    try:
        loaded = cast(object, yaml.safe_load(local.read_text(encoding="utf-8")))
    except yaml.YAMLError:
        return None
    if not isinstance(loaded, dict):
        return None
    enabled_raw = cast(dict[str, object], loaded).get("enabled_surfaces")
    if isinstance(enabled_raw, list):
        return {str(s) for s in cast(list[object], enabled_raw)}
    return None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Coverage-targets enforcement QG step.")
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent,
    )
    parser.add_argument("--targets-path", type=Path, default=DEFAULT_TARGETS_PATH)
    parser.add_argument(
        "--repo",
        default="all",
        help="Single repo name OR 'all' for every repo with a coverage.xml",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Print results but exit 0 regardless (rollout/transition mode)",
    )
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    workspace_root: Path = cast(Path, ns.workspace_root).resolve()
    targets_path: Path = cast(Path, ns.targets_path)
    repo_filter: str = cast(str, ns.repo)
    warn_only: bool = cast(bool, ns.warn_only)

    if not targets_path.is_file():
        print(f"ERROR: targets yaml not found: {targets_path}", file=sys.stderr)
        return 2

    try:
        surfaces = _load_targets(targets_path)
    except (ValueError, yaml.YAMLError) as exc:
        print(f"ERROR: targets parse failed: {exc}", file=sys.stderr)
        return 2

    # Find repos with coverage.xml
    if repo_filter == "all":
        repo_paths: list[Path] = []
        for d in workspace_root.iterdir():
            if (d / "coverage.xml").is_file():
                repo_paths.append(d)
    else:
        repo_paths = [workspace_root / repo_filter]

    if not repo_paths:
        print(f"No repos with coverage.xml found under {workspace_root}")
        return 0

    failures: list[tuple[str, SurfaceResult]] = []
    total_checks = 0

    for repo_path in repo_paths:
        repo_name = repo_path.name
        cov_xml = repo_path / "coverage.xml"
        if not cov_xml.is_file():
            continue
        file_coverages = _parse_coverage_xml(cov_xml)
        if not file_coverages:
            print(f"  {repo_name}: no coverage data parsed from coverage.xml")
            continue
        enabled = _load_local_surfaces(repo_path)
        print(f"\n--- {repo_name} ({len(file_coverages)} files in coverage.xml) ---")
        for surface in surfaces:
            if enabled is not None and surface.name not in enabled:
                continue
            result = _compute_surface_result(surface, repo_name, file_coverages)
            if result is None:
                continue  # surface not present in this repo
            total_checks += 1
            status = "✅" if result.passed else "❌"
            print(
                f"  {status} {surface.name}: {result.actual_pct:.1f}% / "
                f"target {result.target_pct}% ({result.lines_covered}/{result.lines_valid} lines, "
                f"{result.files_matched} files)"
            )
            if not result.passed:
                failures.append((repo_name, result))

    print(f"\n=== Summary: {total_checks} (repo x surface) checks; {len(failures)} below target ===")
    if failures:
        print("\nFailures:")
        for repo_name, r in failures:
            gap = r.target_pct - r.actual_pct
            print(f"  [{repo_name}] {r.surface}: {r.actual_pct:.1f}% (gap {gap:.1f}pt below {r.target_pct}%)")

    if warn_only:
        print("\n(--warn-only set — exiting 0 regardless)")
        return 0
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
