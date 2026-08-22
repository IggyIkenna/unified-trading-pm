#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Triad assertion checker — verifies every critical journey has all 3 proof points.

For each critical journey in the manifest, checks that test files contain evidence of:
  (1) Correct request sent — page.route(), fetch(), or API call assertion
  (2) Contract-valid response received — response status/body assertion
  (3) UI state updated — DOM assertion after response (expect, toBeVisible, etc.)

Also detects no-op controls (BEH-004): click handlers that fire but have no
observable effect (no network call AND no DOM change assertion).

Usage
-----
    python triad_assertion_checker.py                         # default scan
    python triad_assertion_checker.py --workspace-root /path  # custom workspace
    python triad_assertion_checker.py --format json           # JSON output
    python triad_assertion_checker.py --critical-only         # only check critical journeys

Exit codes
----------
    0  All critical journeys pass triad check (or no critical journeys)
    1  At least one critical journey fails triad check
    2  Configuration error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MANIFEST_FILENAME = "ui-api-flow-test-manifest.yaml"

# Test file patterns
_TEST_FILE_SUFFIXES = (".spec.ts", ".spec.tsx", ".test.ts", ".test.tsx")
_E2E_SUFFIXES = (".spec.ts", ".test.ts")

# Exclusion directories
_EXCLUDED_DIRS = frozenset({"node_modules", ".venv", ".venv-workspace", "dist", "build", "__pycache__"})

# --- Triad detection patterns ---

# (1) Request sent patterns — evidence that the test triggers or asserts on a network request
_REQUEST_PATTERNS = [
    # Playwright page.route() or page.waitForRequest/Response
    re.compile(r"page\.route\(", re.IGNORECASE),
    re.compile(r"page\.waitForRequest\(", re.IGNORECASE),
    re.compile(r"page\.waitForResponse\(", re.IGNORECASE),
    # Fetch/XHR intercept assertions
    re.compile(r"request\.url\(\)", re.IGNORECASE),
    re.compile(r"request\.method\(\)", re.IGNORECASE),
    re.compile(r"request\.postData", re.IGNORECASE),
    # MSW (Mock Service Worker) handler setup
    re.compile(r"rest\.(get|post|put|delete|patch)\(", re.IGNORECASE),
    re.compile(r"http\.(get|post|put|delete|patch)\(", re.IGNORECASE),
    # vitest/jest mock for fetch/axios
    re.compile(r"(vi|jest)\.(fn|mock|spyOn).*fetch", re.IGNORECASE),
    re.compile(r"mockResolvedValue", re.IGNORECASE),
    # Direct API route reference in test
    re.compile(r"/api/", re.IGNORECASE),
]

# (2) Response received patterns — evidence that the test asserts on response data
_RESPONSE_PATTERNS = [
    # Playwright response assertions
    re.compile(r"response\.status\(\)", re.IGNORECASE),
    re.compile(r"response\.json\(\)", re.IGNORECASE),
    re.compile(r"response\.ok\(\)", re.IGNORECASE),
    re.compile(r"response\.text\(\)", re.IGNORECASE),
    # route.fulfill with status/body
    re.compile(r"route\.fulfill\(", re.IGNORECASE),
    re.compile(r"\.fulfill\(\s*\{[\s\S]*?status\s*:", re.IGNORECASE),
    # Mock response data assertions
    re.compile(r"expect\(.*\)\.toEqual\(", re.IGNORECASE),
    re.compile(r"expect\(.*\)\.toMatchObject\(", re.IGNORECASE),
    re.compile(r"expect\(.*\)\.toContain\(", re.IGNORECASE),
    re.compile(r"expect\(.*response", re.IGNORECASE),
    re.compile(r"expect\(.*data", re.IGNORECASE),
    # Status code assertions
    re.compile(r"expect\(.*status.*\)\.(toBe|toEqual)\(\s*2\d{2}", re.IGNORECASE),
    re.compile(r"toHaveBeenCalledWith\(", re.IGNORECASE),
]

# (3) UI state updated patterns — evidence that the test asserts on DOM changes after interaction
_UI_UPDATE_PATTERNS = [
    # Playwright DOM assertions
    re.compile(r"expect\(.*\)\.toBeVisible\(", re.IGNORECASE),
    re.compile(r"expect\(.*\)\.toHaveText\(", re.IGNORECASE),
    re.compile(r"expect\(.*\)\.toContainText\(", re.IGNORECASE),
    re.compile(r"expect\(.*\)\.toHaveValue\(", re.IGNORECASE),
    re.compile(r"expect\(.*\)\.toHaveAttribute\(", re.IGNORECASE),
    re.compile(r"expect\(.*\)\.toHaveClass\(", re.IGNORECASE),
    re.compile(r"expect\(.*\)\.toHaveCount\(", re.IGNORECASE),
    re.compile(r"expect\(.*\)\.not\.toBeVisible\(", re.IGNORECASE),
    # Playwright locator assertions
    re.compile(r"locator\(.*\)\.textContent\(", re.IGNORECASE),
    re.compile(r"locator\(.*\)\.innerText\(", re.IGNORECASE),
    re.compile(r"\.waitForSelector\(", re.IGNORECASE),
    re.compile(r"\.waitFor\(\s*\{.*state", re.IGNORECASE),
    # React Testing Library (vitest)
    re.compile(r"screen\.getByText\(", re.IGNORECASE),
    re.compile(r"screen\.getByRole\(", re.IGNORECASE),
    re.compile(r"screen\.getByTestId\(", re.IGNORECASE),
    re.compile(r"screen\.queryByText\(", re.IGNORECASE),
    re.compile(r"screen\.findByText\(", re.IGNORECASE),
    re.compile(r"getByText\(", re.IGNORECASE),
    re.compile(r"getByTestId\(", re.IGNORECASE),
    # DOM state assertions
    re.compile(r"toBeInTheDocument\(", re.IGNORECASE),
    re.compile(r"toHaveTextContent\(", re.IGNORECASE),
    re.compile(r"\.innerHTML", re.IGNORECASE),
    re.compile(r"\.textContent", re.IGNORECASE),
]

# No-op control patterns — click followed by no assertion
_CLICK_PATTERNS = [
    re.compile(r"\.click\(\s*\)", re.IGNORECASE),
    re.compile(r"fireEvent\.click\(", re.IGNORECASE),
    re.compile(r"userEvent\.click\(", re.IGNORECASE),
    re.compile(r"\.tap\(\s*\)", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class TriadResult:
    """Triad assertion check result for a single journey."""

    journey_id: str
    repo: str
    criticality: str
    has_request_evidence: bool = False
    has_response_evidence: bool = False
    has_ui_update_evidence: bool = False
    request_files: list[str] = field(default_factory=list)
    response_files: list[str] = field(default_factory=list)
    ui_update_files: list[str] = field(default_factory=list)
    test_files_scanned: int = 0
    noop_controls: list[str] = field(default_factory=list)

    @property
    def triad_complete(self) -> bool:
        """True if all three proof points are present."""
        return self.has_request_evidence and self.has_response_evidence and self.has_ui_update_evidence

    @property
    def missing_legs(self) -> list[str]:
        """Return list of missing triad legs."""
        missing: list[str] = []
        if not self.has_request_evidence:
            missing.append("request_sent")
        if not self.has_response_evidence:
            missing.append("response_received")
        if not self.has_ui_update_evidence:
            missing.append("ui_state_updated")
        return missing


@dataclass
class NoopControl:
    """A detected no-op control (BEH-004)."""

    file: str
    line_number: int
    control_text: str
    context: str


@dataclass
class TriadReport:
    """Full triad assertion report."""

    results: list[TriadResult] = field(default_factory=list)
    noop_controls: list[NoopControl] = field(default_factory=list)
    total_critical: int = 0
    critical_complete: int = 0
    critical_incomplete: int = 0
    total_journeys: int = 0
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_file_safe(filepath: Path) -> str:
    """Read file content, returning empty string on failure."""
    try:
        return filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _find_test_files(repo_path: Path) -> list[Path]:
    """Find all test files in a repo, excluding node_modules etc."""
    test_files: list[Path] = []
    for suffix in _TEST_FILE_SUFFIXES:
        for f in repo_path.rglob(f"*{suffix}"):
            if not any(part in _EXCLUDED_DIRS for part in f.parts):
                test_files.append(f)
    # Also grab files under e2e/ directories
    for e2e_dir in repo_path.rglob("e2e"):
        if not e2e_dir.is_dir():
            continue
        if any(part in _EXCLUDED_DIRS for part in e2e_dir.parts):
            continue
        for f in e2e_dir.rglob("*"):
            if f.is_file() and f.suffix in (".ts", ".tsx", ".js", ".jsx") and f not in test_files:
                test_files.append(f)
    return sorted(set(test_files))


def _normalise_route(route: str) -> str:
    """Strip path params and trailing slashes."""
    cleaned = re.sub(r"\{[^}]+\}", "", route)
    return cleaned.rstrip("/").lower()


def _content_matches_journey(
    content: str,
    journey_id: str,
    page_or_route: str,
    control_id: str,
    expected_request: str,
) -> bool:
    """Check if test file content references this journey."""
    content_lower = content.lower()

    # Check journey_id
    if journey_id.lower() in content_lower:
        return True

    # Check page route
    route_norm = _normalise_route(page_or_route)
    if route_norm and route_norm != "/" and route_norm in content_lower:
        return True

    # Check control ID
    testid_match = re.search(r"data-testid=['\"]([^'\"]+)['\"]", control_id)
    if testid_match and testid_match.group(1).lower() in content_lower:
        return True

    # Check has-text
    hastext_match = re.search(r"has-text\(['\"]([^'\"]+)['\"]\)", control_id)
    if hastext_match and hastext_match.group(1).lower() in content_lower:
        return True

    # Check endpoint path
    if expected_request:
        parts = expected_request.split(" ", 1)
        if len(parts) == 2:
            ep_norm = _normalise_route(parts[1])
            if ep_norm and ep_norm in content_lower:
                return True

    return False


def _check_patterns(content: str, patterns: list[re.Pattern[str]]) -> bool:
    """Check if any pattern matches in the content."""
    return any(pat.search(content) for pat in patterns)


def _detect_noop_controls(content: str, file_path: str) -> list[NoopControl]:
    """Detect click handlers that appear to have no observable effect.

    A no-op control is a click() call that is NOT followed (within ~10 lines)
    by any assertion or waitFor* call.
    """
    noops: list[NoopControl] = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        # Check if this line has a click pattern
        has_click = any(pat.search(line) for pat in _CLICK_PATTERNS)
        if not has_click:
            continue

        # Look ahead 10 lines for any assertion or wait
        lookahead = "\n".join(lines[i + 1 : i + 11])
        has_assertion = (
            _check_patterns(lookahead, _UI_UPDATE_PATTERNS)
            or _check_patterns(lookahead, _RESPONSE_PATTERNS)
            or re.search(r"waitFor", lookahead, re.IGNORECASE) is not None
            or re.search(r"expect\(", lookahead, re.IGNORECASE) is not None
        )

        if not has_assertion:
            noops.append(
                NoopControl(
                    file=file_path,
                    line_number=i + 1,
                    control_text=line.strip(),
                    context=f"Click at line {i + 1} with no assertion in next 10 lines",
                )
            )

    return noops


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def check_triad_for_journey(
    workspace_root: Path,
    journey: dict[str, str],
    test_files: list[Path],
    test_contents: dict[Path, str],
    repo_path: Path,
) -> TriadResult:
    """Check the request/response/ui-update triad for a single journey."""
    journey_id = journey.get("journey_id", "")
    repo = journey.get("repo", "")
    criticality = journey.get("criticality", "medium")
    page_or_route = journey.get("page_or_route", "")
    control_id = journey.get("control_id", "")
    expected_request = journey.get("expected_request", "")

    result = TriadResult(
        journey_id=journey_id,
        repo=repo,
        criticality=criticality,
        test_files_scanned=len(test_files),
    )

    for tf in test_files:
        content = test_contents.get(tf, "")
        if not content:
            continue

        # Check if this test file is related to this journey
        if not _content_matches_journey(content, journey_id, page_or_route, control_id, expected_request):
            continue

        rel_path = str(tf.relative_to(repo_path))

        # Check triad leg (1): request sent
        if _check_patterns(content, _REQUEST_PATTERNS):
            result.has_request_evidence = True
            if rel_path not in result.request_files:
                result.request_files.append(rel_path)

        # Check triad leg (2): response received
        if _check_patterns(content, _RESPONSE_PATTERNS):
            result.has_response_evidence = True
            if rel_path not in result.response_files:
                result.response_files.append(rel_path)

        # Check triad leg (3): UI state updated
        if _check_patterns(content, _UI_UPDATE_PATTERNS):
            result.has_ui_update_evidence = True
            if rel_path not in result.ui_update_files:
                result.ui_update_files.append(rel_path)

        # Check for no-op controls (BEH-004)
        noops = _detect_noop_controls(content, rel_path)
        for noop in noops:
            result.noop_controls.append(noop.context)

    return result


def run_triad_check(
    workspace_root: Path,
    manifest_path: Path,
    critical_only: bool = False,
) -> TriadReport:
    """Run triad assertion check for all journeys in the manifest."""
    report = TriadReport()

    with open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    journeys = manifest.get("journeys", [])  # noqa: qg-empty-fallback

    # Group journeys by repo
    by_repo: dict[str, list[dict[str, str]]] = {}
    for j in journeys:
        if critical_only and j.get("criticality") != "critical":
            continue
        by_repo.setdefault(j["repo"], []).append(j)

    report.total_journeys = sum(len(jl) for jl in by_repo.values())
    report.total_critical = sum(1 for j in journeys if j.get("criticality") == "critical")

    for repo_name, repo_journeys in sorted(by_repo.items()):
        repo_path = workspace_root / repo_name
        if not repo_path.is_dir():
            for j in repo_journeys:
                result = TriadResult(
                    journey_id=j.get("journey_id", ""),
                    repo=repo_name,
                    criticality=j.get("criticality", "medium"),
                )
                result.noop_controls.append(f"Repo {repo_name} not found in workspace")
                report.results.append(result)
            continue

        test_files = _find_test_files(repo_path)
        test_contents: dict[Path, str] = {}
        for tf in test_files:
            test_contents[tf] = _read_file_safe(tf)

        for j in repo_journeys:
            result = check_triad_for_journey(workspace_root, j, test_files, test_contents, repo_path)
            report.results.append(result)

            if result.criticality == "critical":
                if result.triad_complete:
                    report.critical_complete += 1
                else:
                    report.critical_incomplete += 1

    # Collect all no-op controls across all test files
    for repo_name in by_repo:
        repo_path = workspace_root / repo_name
        if not repo_path.is_dir():
            continue
        test_files = _find_test_files(repo_path)
        for tf in test_files:
            content = _read_file_safe(tf)
            if content:
                noops = _detect_noop_controls(content, str(tf.relative_to(repo_path)))
                report.noop_controls.extend(noops)

    return report


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def format_report(report: TriadReport) -> str:
    """Format the triad report as human-readable text."""
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("Triad Assertion Report")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Total journeys checked: {report.total_journeys}")
    lines.append(f"Critical journeys: {report.total_critical}")
    lines.append(f"  Complete (all 3 legs): {report.critical_complete}")
    lines.append(f"  Incomplete: {report.critical_incomplete}")
    lines.append("")

    # Per-journey details
    lines.append("-" * 60)
    lines.append("Per-Journey Triad Status")
    lines.append("-" * 60)

    for result in report.results:
        status = "PASS" if result.triad_complete else "FAIL"
        crit_tag = f" [{result.criticality.upper()}]" if result.criticality == "critical" else ""
        lines.append(f"  [{status}] {result.repo}/{result.journey_id}{crit_tag}")

        legs_status = []
        legs_status.append(f"request={'YES' if result.has_request_evidence else 'NO'}")
        legs_status.append(f"response={'YES' if result.has_response_evidence else 'NO'}")
        legs_status.append(f"ui_update={'YES' if result.has_ui_update_evidence else 'NO'}")
        lines.append(f"         Triad: {', '.join(legs_status)}")

        if result.missing_legs:
            lines.append(f"         Missing: {', '.join(result.missing_legs)}")

        if result.request_files:
            lines.append(f"         Request evidence: {', '.join(result.request_files[:3])}")
        if result.response_files:
            lines.append(f"         Response evidence: {', '.join(result.response_files[:3])}")
        if result.ui_update_files:
            lines.append(f"         UI update evidence: {', '.join(result.ui_update_files[:3])}")

    # BEH-004: No-op controls
    if report.noop_controls:
        lines.append("")
        lines.append("-" * 60)
        lines.append(f"BEH-004: No-Op Controls Detected ({len(report.noop_controls)})")
        lines.append("-" * 60)
        for noop in report.noop_controls[:20]:
            lines.append(f"  WARNING: {noop.file}:{noop.line_number}")
            lines.append(f"           {noop.control_text[:80]}")
            lines.append(f"           {noop.context}")
        if len(report.noop_controls) > 20:
            lines.append(f"  ... and {len(report.noop_controls) - 20} more")

    lines.append("")
    return "\n".join(lines)


def format_report_json(report: TriadReport) -> str:
    """Format the triad report as JSON."""
    output: dict[str, object] = {
        "summary": {
            "total_journeys": report.total_journeys,
            "total_critical": report.total_critical,
            "critical_complete": report.critical_complete,
            "critical_incomplete": report.critical_incomplete,
            "noop_controls_detected": len(report.noop_controls),
        },
        "results": [
            {
                "journey_id": r.journey_id,
                "repo": r.repo,
                "criticality": r.criticality,
                "triad_complete": r.triad_complete,
                "has_request_evidence": r.has_request_evidence,
                "has_response_evidence": r.has_response_evidence,
                "has_ui_update_evidence": r.has_ui_update_evidence,
                "missing_legs": r.missing_legs,
                "request_files": r.request_files,
                "response_files": r.response_files,
                "ui_update_files": r.ui_update_files,
                "noop_controls": r.noop_controls,
            }
            for r in report.results
        ],
        "noop_controls": [
            {
                "file": n.file,
                "line_number": n.line_number,
                "control_text": n.control_text,
                "context": n.context,
            }
            for n in report.noop_controls
        ],
        "errors": report.errors,
    }
    return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point for the triad assertion checker."""
    parser = argparse.ArgumentParser(
        description="Triad assertion checker — verifies request/response/ui-update evidence for critical journeys.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root directory (default: auto-detect)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--critical-only",
        action="store_true",
        default=False,
        help="Only check critical journeys",
    )
    parser.add_argument(
        "--warning-only",
        action="store_true",
        default=False,
        help="Always exit 0, even if critical journeys fail triad",
    )

    args = parser.parse_args(argv)

    # Resolve workspace root
    if args.workspace_root is not None:
        workspace_root = args.workspace_root.resolve()
    else:
        workspace_root = Path(__file__).resolve().parent.parent.parent.parent

    pm_root = workspace_root / "unified-trading-pm"
    manifest_path = pm_root / _MANIFEST_FILENAME

    if not manifest_path.is_file():
        print(f"ERROR: Manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    # Run check
    report = run_triad_check(workspace_root, manifest_path, critical_only=args.critical_only)

    # Format and print
    output = format_report_json(report) if args.format == "json" else format_report(report)

    print(output)

    if args.warning_only:
        return 0

    return 1 if report.critical_incomplete > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
