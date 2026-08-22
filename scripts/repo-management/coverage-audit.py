#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
coverage-audit.py — Audit test coverage across all workspace repos.

Reports:
  [A] FAIL  — repos below their coverage floor (service=70%, library=80%)
  [B] WARN  — repos not producing coverage in standard format (missing reports)
  [C] INFO  — repos where MIN_COVERAGE threshold is stale vs actual coverage

Exit 0 = no FAIL repos. Exit 1 = one or more FAIL repos.

Usage:
    python3 unified-trading-pm/scripts/repo-management/coverage-audit.py
    python3 unified-trading-pm/scripts/repo-management/coverage-audit.py --json
    python3 unified-trading-pm/scripts/repo-management/coverage-audit.py --no-color

Run from workspace root (parent of unified-trading-pm).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

type JsonDict = dict[str, object]


class _Args(argparse.Namespace):
    json: bool
    no_color: bool
    repo: str | None


# ── Config ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = SCRIPT_DIR.parent.parent.parent
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"

# Repos exempt from standard floors — these have documented override reasons
EXCEPTIONS: frozenset[str] = frozenset(
    {
        "ibkr-gateway-infra",  # gateway client; limited unit-testable surface (override=51)
        "system-integration-tests",  # pure test-harness repo; no source package (override=0)
        "unified-trading-pm",  # self-managed; rollout skips it
        "unified-trading-codex",  # docs-only repo; no Python source
    }
)

# Repo types that are Python repos (expect coverage.xml)
PYTHON_TYPES: frozenset[str] = frozenset(
    {
        "service",
        "api-service",
        "library",
        "infrastructure",
        "test-harness",
        "devops",
    }
)

# Repo types that are UI (expect coverage/coverage-summary.json from vitest)
UI_TYPES: frozenset[str] = frozenset({"ui"})


# Coverage floor by repo type
def coverage_floor(repo_type: str, template_type: str) -> int:
    if template_type == "library":
        return 80
    return 70  # service, api-service, infrastructure, ui, devops, test-harness


def _is_library(repo_type: str) -> bool:
    return repo_type == "library"


# ── Data structures ───────────────────────────────────────────────────────────


@dataclass
class RepoResult:
    name: str
    repo_type: str
    floor: int
    actual_pct: int | None  # None = could not measure
    min_coverage: int | None  # from quality-gates.sh; None = not set / UI repo
    expected_min: int | None  # max(floor, actual-1); None = no data
    status: str  # "fail", "warn", "info", "ok", "skip", "exception"
    note: str = ""


# ── Parsers ───────────────────────────────────────────────────────────────────


def parse_python_coverage(repo_path: Path) -> int | None:
    """Return coverage % from coverage.xml, or None if not present/parseable."""
    xml_path = repo_path / "coverage.xml"
    if not xml_path.exists():
        return None
    try:
        tree = ET.parse(xml_path)  # nosec B314 — local coverage.xml, not untrusted input
        root = tree.getroot()
        line_rate = root.get("line-rate")
        if line_rate is not None:
            return int(float(line_rate) * 100)
    except (ET.ParseError, ValueError):
        pass
    return None


def parse_ui_coverage(repo_path: Path) -> int | None:
    """Return coverage % from coverage/coverage-summary.json (vitest/istanbul), or None."""
    summary_path = repo_path / "coverage" / "coverage-summary.json"
    if not summary_path.exists():
        return None
    try:
        data: JsonDict = cast(JsonDict, json.loads(summary_path.read_text()))
        total = data.get("total")
        if not isinstance(total, dict):
            return None
        lines = total.get("lines")
        if not isinstance(lines, dict):
            return None
        pct = lines.get("pct")
        if pct is not None:
            return int(float(pct))
    except (json.JSONDecodeError, ValueError, OSError):
        pass
    return None


def parse_min_coverage(repo_path: Path) -> int | None:
    """Return MIN_COVERAGE from scripts/quality-gates.sh, or None if absent."""
    qg = repo_path / "scripts" / "quality-gates.sh"
    if not qg.exists():
        return None
    m = re.search(r"^MIN_COVERAGE=(\d+)", qg.read_text(), re.MULTILINE)
    return int(m.group(1)) if m else None


def has_vitest_unit_test_script(repo_path: Path) -> bool:
    """True if package.json has a 'test' script that is NOT playwright-only."""
    pkg = repo_path / "package.json"
    if not pkg.exists():
        return False
    try:
        pkg_data: JsonDict = cast(JsonDict, json.loads(pkg.read_text()))
        scripts = pkg_data.get("scripts")
        if not isinstance(scripts, dict):
            return False
        test_cmd = scripts.get("test")
        if not test_cmd or not isinstance(test_cmd, str):
            return False
        return "playwright" not in test_cmd
    except (json.JSONDecodeError, OSError):
        return False


# ── Core audit logic ──────────────────────────────────────────────────────────


def audit_repo(
    name: str,
    repo_info: JsonDict,
    workspace_root: Path,
) -> RepoResult:
    repo_type = str(repo_info.get("type", "service"))
    status_field = str(repo_info.get("status", "active"))
    repo_path = workspace_root / name

    # Skip deprecated/archived
    if status_field in ("deprecated", "archived", "deleted"):
        return RepoResult(name, repo_type, 0, None, None, None, "skip", f"status={status_field}")

    # Override: package.json + no pyproject.toml = typescript UI
    has_pkg = (repo_path / "package.json").exists()
    has_pyproject = (repo_path / "pyproject.toml").exists()
    if has_pkg and not has_pyproject:
        repo_type = "ui"

    floor = coverage_floor(repo_type, "library" if _is_library(repo_type) else "service")

    # Exceptions: still audit but label differently
    is_exception = name in EXCEPTIONS

    if repo_type in UI_TYPES:
        actual_pct = parse_ui_coverage(repo_path)
        min_coverage = None  # UI repos don't have MIN_COVERAGE in QG (no Python gate)
        expected_min = None

        if actual_pct is None:
            if has_vitest_unit_test_script(repo_path):
                has_v8 = _has_coverage_v8(repo_path)
                note = "no coverage/coverage-summary.json" + ("" if has_v8 else " (@vitest/coverage-v8 not installed)")
            else:
                note = "no unit test script (playwright-only or no test script)"
            return RepoResult(name, repo_type, floor, None, None, None, "warn", note)

        expected_min = max(floor, actual_pct - 1)
        if actual_pct < floor and not is_exception:
            return RepoResult(name, repo_type, floor, actual_pct, min_coverage, expected_min, "fail")
        return RepoResult(name, repo_type, floor, actual_pct, min_coverage, expected_min, "ok")

    elif repo_type in PYTHON_TYPES:
        actual_pct = parse_python_coverage(repo_path)
        min_coverage = parse_min_coverage(repo_path)

        if actual_pct is None:
            if has_pyproject:
                return RepoResult(
                    name,
                    repo_type,
                    floor,
                    None,
                    min_coverage,
                    None,
                    "warn",
                    "pyproject.toml exists but no coverage.xml",
                )
            return RepoResult(name, repo_type, floor, None, min_coverage, None, "skip", "no pyproject.toml")

        expected_min = max(floor, actual_pct - 1)

        if is_exception:
            return RepoResult(
                name, repo_type, floor, actual_pct, min_coverage, expected_min, "exception", "approved exception"
            )

        if actual_pct < floor:
            return RepoResult(name, repo_type, floor, actual_pct, min_coverage, expected_min, "fail")

        if min_coverage is not None and min_coverage != expected_min:
            return RepoResult(
                name,
                repo_type,
                floor,
                actual_pct,
                min_coverage,
                expected_min,
                "info",
                f"MIN_COVERAGE={min_coverage} but expected {expected_min}",
            )

        return RepoResult(name, repo_type, floor, actual_pct, min_coverage, expected_min, "ok")

    else:
        return RepoResult(name, repo_type, floor, None, None, None, "skip", f"unhandled type={repo_type}")


def _has_coverage_v8(repo_path: Path) -> bool:
    pkg = repo_path / "package.json"
    if not pkg.exists():
        return False
    try:
        data: JsonDict = cast(JsonDict, json.loads(pkg.read_text()))
        raw_deps = data.get("dependencies")
        raw_dev_deps = data.get("devDependencies")
        deps: dict[str, object] = {}
        if isinstance(raw_deps, dict):
            deps.update(raw_deps)
        if isinstance(raw_dev_deps, dict):
            deps.update(raw_dev_deps)
        return "@vitest/coverage-v8" in deps or "@vitest/coverage-istanbul" in deps
    except (json.JSONDecodeError, OSError):
        return False


# ── Formatting ────────────────────────────────────────────────────────────────


class Colors:
    RED = "\033[0;31m"
    YELLOW = "\033[1;33m"
    GREEN = "\033[0;32m"
    CYAN = "\033[0;36m"
    BOLD = "\033[1m"
    NC = "\033[0m"

    def __init__(self, enabled: bool = True) -> None:
        if not enabled:
            for attr in ("RED", "YELLOW", "GREEN", "CYAN", "BOLD", "NC"):
                setattr(self, attr, "")


def _pct(val: int | None) -> str:
    return f"{val}%" if val is not None else "N/A"


def _gap(actual: int | None, floor: int) -> str:
    if actual is None:
        return ""
    g = actual - floor
    return f"{g:+d}%"


def print_report(results: list[RepoResult], c: Colors) -> None:
    fails = [r for r in results if r.status == "fail"]
    warns = [r for r in results if r.status == "warn"]
    infos = [r for r in results if r.status == "info"]
    oks = [r for r in results if r.status == "ok"]
    excepts = [r for r in results if r.status == "exception"]

    today = datetime.now(UTC).date().isoformat()
    print(f"\n{c.BOLD}━━━ Coverage Audit ━━━{c.NC}  ({today})\n")

    # [A] Below floor
    label_a = f"{c.RED}[FAIL]{c.NC}" if fails else f"{c.GREEN}[PASS]{c.NC}"
    print(f"{c.BOLD}[A] BELOW FLOOR — {len(fails)} repo(s)  {label_a}{c.NC}")
    if fails:
        for r in sorted(fails, key=lambda x: x.actual_pct or 0):
            gap = _gap(r.actual_pct, r.floor)
            print(
                f"  {c.RED}[FAIL]{c.NC}  {r.name:<45}  {r.repo_type:<12}  "
                f"actual={_pct(r.actual_pct):<6}  floor={r.floor}%  gap={gap}"
            )
    else:
        print(f"  {c.GREEN}All repos meet their coverage floor.{c.NC}")

    # [B] Non-uniform reporters
    print(
        f"\n{c.BOLD}[B] NON-UNIFORM REPORTERS — {len(warns)} repo(s)  "
        f"({'⚠' if warns else c.GREEN + 'PASS' + c.NC}){c.NC}"
        if not warns
        else f"\n{c.BOLD}[B] NON-UNIFORM REPORTERS — {len(warns)} repo(s)  {c.YELLOW}[WARN]{c.NC}{c.NC}"
    )
    for r in sorted(warns, key=lambda x: x.name):
        print(f"  {c.YELLOW}[WARN]{c.NC}  {r.name:<45}  {r.repo_type:<12}  {r.note}")

    if not warns:
        print(f"  {c.GREEN}All active repos producing coverage reports.{c.NC}")

    # [C] Stale thresholds
    print(f"\n{c.BOLD}[C] STALE THRESHOLD — {len(infos)} repo(s){c.NC}")
    for r in sorted(infos, key=lambda x: x.name):
        print(f"  {c.CYAN}[INFO]{c.NC}  {r.name:<45}  {r.repo_type:<12}  {r.note}")
    if not infos:
        print(f"  {c.GREEN}All thresholds calibrated correctly.{c.NC}")

    # Exceptions (informational)
    if excepts:
        print(f"\n{c.BOLD}[D] APPROVED EXCEPTIONS — {len(excepts)} repo(s){c.NC}")
        for r in sorted(excepts, key=lambda x: x.name):
            print(f"  [SKIP]  {r.name:<45}  actual={_pct(r.actual_pct):<6}  floor={r.floor}%  {r.note}")

    # Summary
    print(f"\n{c.BOLD}━━━ Summary ━━━{c.NC}")
    print(f"  Below floor   {c.RED}[FAIL]{c.NC}:  {len(fails)}")
    print(f"  Non-uniform   {c.YELLOW}[WARN]{c.NC}:  {len(warns)}")
    print(f"  Stale thresh  {c.CYAN}[INFO]{c.NC}:  {len(infos)}")
    print(f"  Compliant     {c.GREEN}[OK]{c.NC}:    {len(oks)}")
    print(f"  Exceptions   [SKIP]:  {len(excepts)}")
    print()

    if fails:
        print(f"  {c.RED}Fix: write tests to reach the floor, then run:{c.NC}")
        print("  python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py --recalibrate")
    else:
        print(f"  {c.GREEN}✅ No below-floor failures.{c.NC}")
    print()


def to_json(results: list[RepoResult]) -> dict[str, object]:
    def _row(r: RepoResult) -> dict[str, object]:
        return {
            "repo": r.name,
            "type": r.repo_type,
            "floor": r.floor,
            "actual_pct": r.actual_pct,
            "min_coverage": r.min_coverage,
            "expected_min": r.expected_min,
            "status": r.status,
            "note": r.note,
        }

    return {
        "below_floor": [_row(r) for r in results if r.status == "fail"],
        "non_uniform": [_row(r) for r in results if r.status == "warn"],
        "stale_threshold": [_row(r) for r in results if r.status == "info"],
        "compliant": [_row(r) for r in results if r.status == "ok"],
        "exceptions": [_row(r) for r in results if r.status == "exception"],
        "summary": {
            "below_floor": sum(1 for r in results if r.status == "fail"),
            "non_uniform": sum(1 for r in results if r.status == "warn"),
            "stale_threshold": sum(1 for r in results if r.status == "info"),
            "compliant": sum(1 for r in results if r.status == "ok"),
            "exceptions": sum(1 for r in results if r.status == "exception"),
        },
    }


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit test coverage across all workspace repos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Run from workspace root (parent of unified-trading-pm).",
    )
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI color output")
    parser.add_argument("--repo", type=str, help="Audit a single repo by name")
    args = parser.parse_args(namespace=_Args())

    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found: {MANIFEST_PATH}", file=sys.stderr)
        print("   Run from workspace root (parent of unified-trading-pm).", file=sys.stderr)
        return 2

    with open(MANIFEST_PATH) as f:
        manifest: JsonDict = json.load(f)  # type: ignore[assignment]

    repos_raw = manifest.get("repositories")
    if not isinstance(repos_raw, dict):
        print("❌ Invalid manifest: 'repositories' must be a dict.", file=sys.stderr)
        return 2
    repositories: dict[str, JsonDict] = repos_raw  # type: ignore[assignment]

    if args.repo:
        if args.repo not in repositories:
            print(f"❌ Repo not in manifest: {args.repo}", file=sys.stderr)
            return 2
        repositories = {args.repo: repositories[args.repo]}

    results: list[RepoResult] = []
    for name, info in sorted(repositories.items()):
        if not isinstance(info, dict):
            continue
        results.append(audit_repo(name, info, WORKSPACE_ROOT))

    if args.json:
        print(json.dumps(to_json(results), indent=2))
    else:
        c = Colors(enabled=not args.no_color)
        print_report(results, c)

    has_failures = any(r.status == "fail" for r in results)
    return 1 if has_failures else 0


if __name__ == "__main__":
    sys.exit(main())
