#!/usr/bin/env python3
"""UI/API flow coverage checker — validates test coverage against flow manifest.

Loads ui-api-flow-test-manifest.yaml and checks that each declared journey
has corresponding test files referencing the page route, control IDs, or
API endpoints. Reports coverage per-UI, per-API, and overall.

Usage
-----
    python check_ui_api_flow_coverage.py                         # default scan
    python check_ui_api_flow_coverage.py --warning-only          # always exit 0
    python check_ui_api_flow_coverage.py --discover              # also report undeclared tests/endpoints
    python check_ui_api_flow_coverage.py --format json           # JSON output
    python check_ui_api_flow_coverage.py --workspace-root /path  # custom workspace root

Exit codes
----------
    0  All critical journeys have test coverage (or --warning-only)
    1  At least one CRITICAL journey has zero test coverage
    2  Configuration error (manifest not found, parse failure)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# PyYAML is available in the workspace venv
import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_MANIFEST_FILENAME = "ui-api-flow-test-manifest.yaml"
_UI_API_MAPPING_FILENAME = "scripts/dev/ui-api-mapping.json"

# Test file glob patterns for UI repos
_UI_TEST_GLOBS = (
    "**/*.test.ts",
    "**/*.test.tsx",
    "**/*.spec.ts",
    "**/*.spec.tsx",
)
_E2E_DIR_NAME = "e2e"

# FastAPI/Starlette route decorator pattern
_ROUTE_DECORATOR_RE = re.compile(
    r"@(?:app|router)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']",
    re.IGNORECASE,
)

# Exclusion directories for scanning
_EXCLUDED_DIRS = frozenset(
    {
        "node_modules",
        ".venv",
        ".venv-workspace",
        "dist",
        "build",
        ".next",
        "__pycache__",
    }
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class Journey:
    """A single declared UI journey from the manifest."""

    repo: str
    journey_id: str
    page_or_route: str
    control_id: str
    interaction_type: str
    expected_request: str
    expected_response_contract: str
    expected_ui_update: str
    required_layers: list[str]
    criticality: str


@dataclass
class JourneyCoverageResult:
    """Coverage result for a single journey."""

    journey: Journey
    test_files_matched: list[str] = field(default_factory=list)
    route_match: bool = False
    control_match: bool = False
    endpoint_match: bool = False

    @property
    def covered(self) -> bool:
        return len(self.test_files_matched) > 0

    @property
    def match_summary(self) -> str:
        parts: list[str] = []
        if self.route_match:
            parts.append("route")
        if self.control_match:
            parts.append("control")
        if self.endpoint_match:
            parts.append("endpoint")
        return "+".join(parts) if parts else "none"


@dataclass
class UICoverageReport:
    """Aggregated coverage for a single UI repo."""

    repo: str
    repo_exists: bool
    journeys_declared: int = 0
    journeys_covered: int = 0
    critical_uncovered: list[str] = field(default_factory=list)
    results: list[JourneyCoverageResult] = field(default_factory=list)


@dataclass
class APICoverageReport:
    """Endpoint existence check for an API repo."""

    repo: str
    repo_exists: bool
    endpoints_declared: list[str] = field(default_factory=list)
    endpoints_found: list[str] = field(default_factory=list)
    endpoints_missing: list[str] = field(default_factory=list)


@dataclass
class DiscoveryReport:
    """Undeclared tests and endpoints found via --discover."""

    undeclared_test_files: dict[str, list[str]] = field(default_factory=dict)
    undeclared_endpoints: dict[str, list[str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _should_skip_dir(dirname: str) -> bool:
    """Return True if directory should be excluded from scanning."""
    return dirname in _EXCLUDED_DIRS


def _find_test_files(repo_path: Path) -> list[Path]:
    """Find all test files in a UI repo, excluding node_modules etc."""
    test_files: list[Path] = []
    for glob_pat in _UI_TEST_GLOBS:
        for f in repo_path.glob(glob_pat):
            if not any(part in _EXCLUDED_DIRS for part in f.parts):
                test_files.append(f)
    # Also grab any files under e2e/ directories
    for e2e_dir in repo_path.rglob(_E2E_DIR_NAME):
        if not e2e_dir.is_dir():
            continue
        if any(part in _EXCLUDED_DIRS for part in e2e_dir.parts):
            continue
        for f in e2e_dir.rglob("*"):
            if f.is_file() and f.suffix in (".ts", ".tsx", ".js", ".jsx"):
                if f not in test_files:
                    test_files.append(f)
    return sorted(set(test_files))


def _read_file_safe(filepath: Path) -> str:
    """Read file content, returning empty string on failure."""
    try:
        return filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _normalise_route_for_search(route: str) -> str:
    """Convert /services/{id} to a regex-safe pattern: /services/."""
    # Strip path params
    cleaned = re.sub(r"\{[^}]+\}", "", route)
    # Remove trailing slashes for matching
    cleaned = cleaned.rstrip("/")
    return cleaned


def _extract_search_terms(journey: Journey) -> list[str]:
    """Extract search terms from a journey for test-file matching.

    Returns multiple terms — if ANY appears in a test file, we consider
    the journey referenced.
    """
    terms: list[str] = []

    # 1. Page route (normalised)
    route_norm = _normalise_route_for_search(journey.page_or_route)
    if route_norm and route_norm != "/":
        terms.append(route_norm)
        # Also add the last segment for fuzzy matching
        last_seg = route_norm.rstrip("/").rsplit("/", 1)[-1]
        if last_seg and len(last_seg) > 2:
            terms.append(last_seg)

    # 2. Control ID — extract data-testid value or button text
    ctrl = journey.control_id
    # data-testid='deploy-button' -> deploy-button
    testid_match = re.search(r"data-testid=['\"]([^'\"]+)['\"]", ctrl)
    if testid_match:
        terms.append(testid_match.group(1))
    # has-text('Submit Trade') -> Submit Trade
    hastext_match = re.search(r"has-text\(['\"]([^'\"]+)['\"]\)", ctrl)
    if hastext_match:
        terms.append(hastext_match.group(1))

    # 3. Expected request — extract the HTTP path
    if journey.expected_request:
        parts = journey.expected_request.split(" ", 1)
        if len(parts) == 2:
            endpoint_path = _normalise_route_for_search(parts[1])
            if endpoint_path:
                terms.append(endpoint_path)
            # Also add last significant segment
            last_ep_seg = endpoint_path.rstrip("/").rsplit("/", 1)[-1]
            if last_ep_seg and len(last_ep_seg) > 2:
                terms.append(last_ep_seg)

    # 4. Journey ID itself (kebab-case often appears in test descriptions)
    terms.append(journey.journey_id)

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: list[str] = []
    for t in terms:
        lower = t.lower()
        if lower not in seen:
            seen.add(lower)
            unique.append(t)
    return unique


def _check_journey_in_test_files(
    journey: Journey,
    test_files: list[Path],
    test_contents: dict[Path, str],
    repo_path: Path,
) -> JourneyCoverageResult:
    """Check if a journey is referenced in any test file."""
    result = JourneyCoverageResult(journey=journey)
    search_terms = _extract_search_terms(journey)

    route_norm = _normalise_route_for_search(journey.page_or_route)

    for test_file in test_files:
        content = test_contents.get(test_file, "")
        if not content:
            continue

        matched = False

        # Check route
        if route_norm and route_norm != "/" and route_norm in content:
            result.route_match = True
            matched = True

        # Check control ID terms
        testid_match = re.search(r"data-testid=['\"]([^'\"]+)['\"]", journey.control_id)
        if testid_match and testid_match.group(1) in content:
            result.control_match = True
            matched = True

        # Check endpoint path
        if journey.expected_request:
            ep_parts = journey.expected_request.split(" ", 1)
            if len(ep_parts) == 2:
                ep_path = _normalise_route_for_search(ep_parts[1])
                if ep_path and ep_path in content:
                    result.endpoint_match = True
                    matched = True

        # Fallback: any search term found
        if not matched:
            for term in search_terms:
                if len(term) > 2 and term.lower() in content.lower():
                    matched = True
                    break

        if matched:
            rel_path = str(test_file.relative_to(repo_path))
            if rel_path not in result.test_files_matched:
                result.test_files_matched.append(rel_path)

    return result


def _scan_api_routes(api_repo_path: Path) -> list[str]:
    """Scan an API repo for declared FastAPI/Starlette route endpoints."""
    routes: list[str] = []
    for py_file in api_repo_path.rglob("*.py"):
        if any(part in _EXCLUDED_DIRS for part in py_file.parts):
            continue
        content = _read_file_safe(py_file)
        for match in _ROUTE_DECORATOR_RE.finditer(content):
            route_path = match.group(2)
            if route_path not in routes:
                routes.append(route_path)
    return sorted(routes)


def _normalise_endpoint_for_comparison(endpoint: str) -> str:
    """Normalise endpoint for comparison: strip params, lowercase."""
    cleaned = re.sub(r"\{[^}]+\}", "{}", endpoint)
    return cleaned.lower().rstrip("/")


def _endpoint_exists_in_routes(endpoint: str, api_routes: list[str]) -> bool:
    """Check if a declared endpoint exists among actual API routes."""
    norm_ep = _normalise_endpoint_for_comparison(endpoint)

    for route in api_routes:
        norm_route = _normalise_endpoint_for_comparison(route)
        if norm_ep == norm_route:
            return True
        # Fuzzy: check if the route starts with or contains the endpoint path
        # e.g. declared "/api/deployments" matches route "/api/deployments/{service}/deploy"
        if norm_route.startswith(norm_ep) or norm_ep.startswith(norm_route):
            return True

    return False


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def load_manifest(manifest_path: Path) -> list[Journey]:
    """Load and parse the flow test manifest."""
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    journeys_raw = data.get("journeys", [])
    journeys: list[Journey] = []
    for entry in journeys_raw:
        journeys.append(
            Journey(
                repo=entry["repo"],
                journey_id=entry["journey_id"],
                page_or_route=entry.get("page_or_route", ""),
                control_id=entry.get("control_id", ""),
                interaction_type=entry.get("interaction_type", ""),
                expected_request=entry.get("expected_request", ""),
                expected_response_contract=entry.get("expected_response_contract", ""),
                expected_ui_update=entry.get("expected_ui_update", ""),
                required_layers=entry.get("required_layers", []),
                criticality=entry.get("criticality", "medium"),
            )
        )
    return journeys


def load_ui_api_mapping(mapping_path: Path) -> dict[str, str]:
    """Load ui-api-mapping.json and return {ui_repo: api_repo} mapping."""
    if not mapping_path.is_file():
        return {}
    with open(mapping_path, encoding="utf-8") as f:
        data = json.load(f)
    mapping: dict[str, str] = {}
    stacks = data.get("stacks", data)
    for _stack_name, info in stacks.items():
        ui = info.get("ui")
        api = info.get("api")
        if ui and api:
            mapping[ui] = api
    return mapping


def check_ui_coverage(
    workspace_root: Path,
    journeys: list[Journey],
) -> dict[str, UICoverageReport]:
    """Check test coverage for all UI repos referenced in journeys."""
    # Group journeys by repo
    by_repo: dict[str, list[Journey]] = {}
    for j in journeys:
        by_repo.setdefault(j.repo, []).append(j)

    reports: dict[str, UICoverageReport] = {}

    for repo_name, repo_journeys in sorted(by_repo.items()):
        repo_path = workspace_root / repo_name
        repo_exists = repo_path.is_dir()

        report = UICoverageReport(
            repo=repo_name,
            repo_exists=repo_exists,
            journeys_declared=len(repo_journeys),
        )

        if not repo_exists:
            # All journeys uncovered if repo doesn't exist
            for j in repo_journeys:
                result = JourneyCoverageResult(journey=j)
                report.results.append(result)
                if j.criticality == "critical":
                    report.critical_uncovered.append(j.journey_id)
            reports[repo_name] = report
            continue

        # Find and cache test files
        test_files = _find_test_files(repo_path)
        test_contents: dict[Path, str] = {}
        for tf in test_files:
            test_contents[tf] = _read_file_safe(tf)

        for j in repo_journeys:
            result = _check_journey_in_test_files(j, test_files, test_contents, repo_path)
            report.results.append(result)
            if result.covered:
                report.journeys_covered += 1
            elif j.criticality == "critical":
                report.critical_uncovered.append(j.journey_id)

        reports[repo_name] = report

    return reports


def check_api_endpoints(
    workspace_root: Path,
    journeys: list[Journey],
    ui_api_mapping: dict[str, str],
) -> dict[str, APICoverageReport]:
    """Check that declared API endpoints actually exist in API repos."""
    # Collect endpoints per API repo
    api_endpoints: dict[str, list[str]] = {}
    for j in journeys:
        if not j.expected_request:
            continue
        parts = j.expected_request.split(" ", 1)
        if len(parts) != 2:
            continue
        endpoint_path = parts[1]
        # Find API repo via mapping
        api_repo = ui_api_mapping.get(j.repo)
        if not api_repo:
            continue
        api_endpoints.setdefault(api_repo, [])
        if endpoint_path not in api_endpoints[api_repo]:
            api_endpoints[api_repo].append(endpoint_path)

    reports: dict[str, APICoverageReport] = {}

    for api_repo, declared_eps in sorted(api_endpoints.items()):
        repo_path = workspace_root / api_repo
        repo_exists = repo_path.is_dir()

        report = APICoverageReport(
            repo=api_repo,
            repo_exists=repo_exists,
            endpoints_declared=declared_eps,
        )

        if repo_exists:
            actual_routes = _scan_api_routes(repo_path)
            for ep in declared_eps:
                if _endpoint_exists_in_routes(ep, actual_routes):
                    report.endpoints_found.append(ep)
                else:
                    report.endpoints_missing.append(ep)
        else:
            report.endpoints_missing = list(declared_eps)

        reports[api_repo] = report

    return reports


def run_discovery(
    workspace_root: Path,
    journeys: list[Journey],
    ui_api_mapping: dict[str, str],
) -> DiscoveryReport:
    """Discover test files and endpoints not declared in the manifest."""
    discovery = DiscoveryReport()

    # Collect all declared journeys per UI repo for comparison
    declared_repos = {j.repo for j in journeys}

    # Scan ALL UI repos for test files not referenced in manifest
    for ui_dir in sorted(workspace_root.iterdir()):
        if not ui_dir.is_dir() or not ui_dir.name.endswith("-ui"):
            continue
        repo_name = ui_dir.name
        test_files = _find_test_files(ui_dir)
        if not test_files:
            continue

        # If repo not in manifest at all, report all test files
        if repo_name not in declared_repos:
            rel_paths = [str(f.relative_to(ui_dir)) for f in test_files]
            if rel_paths:
                discovery.undeclared_test_files[repo_name] = rel_paths
            continue

        # For repos in manifest, find test files that don't match any journey
        repo_journeys = [j for j in journeys if j.repo == repo_name]
        all_search_terms: set[str] = set()
        for j in repo_journeys:
            for term in _extract_search_terms(j):
                all_search_terms.add(term.lower())

        unmatched: list[str] = []
        for tf in test_files:
            content = _read_file_safe(tf).lower()
            if not any(term in content for term in all_search_terms if len(term) > 2):
                unmatched.append(str(tf.relative_to(ui_dir)))
        if unmatched:
            discovery.undeclared_test_files[repo_name] = unmatched

    # Scan ALL API repos for endpoints not in manifest
    manifest_endpoints: dict[str, set[str]] = {}
    for j in journeys:
        api_repo = ui_api_mapping.get(j.repo)
        if not api_repo or not j.expected_request:
            continue
        parts = j.expected_request.split(" ", 1)
        if len(parts) == 2:
            manifest_endpoints.setdefault(api_repo, set()).add(_normalise_endpoint_for_comparison(parts[1]))

    for api_dir in sorted(workspace_root.iterdir()):
        if not api_dir.is_dir() or not api_dir.name.endswith("-api"):
            continue
        repo_name = api_dir.name
        actual_routes = _scan_api_routes(api_dir)
        if not actual_routes:
            continue

        declared_set = manifest_endpoints.get(repo_name, set())
        undeclared: list[str] = []
        for route in actual_routes:
            norm = _normalise_endpoint_for_comparison(route)
            # Skip health/readiness/catch-all routes
            if any(skip in norm for skip in ("/health", "/readiness", "/{full_path", "/cache/clear", "/workers")):
                continue
            # Check if declared (fuzzy)
            is_declared = False
            for d in declared_set:
                if norm == d or norm.startswith(d) or d.startswith(norm):
                    is_declared = True
                    break
            if not is_declared:
                undeclared.append(route)
        if undeclared:
            discovery.undeclared_endpoints[repo_name] = undeclared

    return discovery


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def _format_text(
    ui_reports: dict[str, UICoverageReport],
    api_reports: dict[str, APICoverageReport],
    discovery: DiscoveryReport | None,
) -> str:
    """Format results as human-readable text."""
    lines: list[str] = []

    # Header
    total_journeys = sum(r.journeys_declared for r in ui_reports.values())
    total_covered = sum(r.journeys_covered for r in ui_reports.values())
    total_critical_uncovered = sum(len(r.critical_uncovered) for r in ui_reports.values())
    pct = (total_covered / total_journeys * 100) if total_journeys > 0 else 0.0

    lines.append("=" * 60)
    lines.append("UI/API Flow Coverage Report")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Overall: {total_covered}/{total_journeys} journeys covered ({pct:.1f}%)")
    lines.append(f"Critical uncovered: {total_critical_uncovered}")
    lines.append("")

    # Per-UI summary
    lines.append("-" * 60)
    lines.append("Per-UI Summary")
    lines.append("-" * 60)
    for repo_name, report in sorted(ui_reports.items()):
        exists_tag = "" if report.repo_exists else " [REPO NOT FOUND]"
        cov_pct = (report.journeys_covered / report.journeys_declared * 100) if report.journeys_declared > 0 else 0.0
        lines.append(
            f"  {repo_name}: {report.journeys_covered}/{report.journeys_declared} ({cov_pct:.0f}%){exists_tag}"
        )
        for result in report.results:
            j = result.journey
            status = "PASS" if result.covered else "MISS"
            crit_tag = f" [{j.criticality.upper()}]" if j.criticality == "critical" else ""
            match_info = f" ({result.match_summary})" if result.covered else ""
            lines.append(f"    {status} {j.journey_id}{crit_tag}{match_info}")
            if result.covered and result.test_files_matched:
                for tf in result.test_files_matched[:3]:
                    lines.append(f"         -> {tf}")

        if report.critical_uncovered:
            lines.append(f"    ** CRITICAL UNCOVERED: {', '.join(report.critical_uncovered)}")
        lines.append("")

    # Per-API endpoint check
    if api_reports:
        lines.append("-" * 60)
        lines.append("Per-API Endpoint Existence")
        lines.append("-" * 60)
        for api_name, report in sorted(api_reports.items()):
            exists_tag = "" if report.repo_exists else " [REPO NOT FOUND]"
            found_count = len(report.endpoints_found)
            total_count = len(report.endpoints_declared)
            lines.append(f"  {api_name}: {found_count}/{total_count} endpoints exist{exists_tag}")
            for ep in report.endpoints_missing:
                lines.append(f"    MISSING: {ep}")
        lines.append("")

    # Discovery
    if discovery is not None:
        lines.append("-" * 60)
        lines.append("Auto-Discovery: Undeclared Items")
        lines.append("-" * 60)

        if discovery.undeclared_test_files:
            lines.append("  Undeclared test files (exist but not in manifest):")
            for repo_name, files in sorted(discovery.undeclared_test_files.items()):
                lines.append(f"    {repo_name}:")
                for f in files[:10]:
                    lines.append(f"      - {f}")
                if len(files) > 10:
                    lines.append(f"      ... and {len(files) - 10} more")
        else:
            lines.append("  No undeclared test files found.")

        lines.append("")

        if discovery.undeclared_endpoints:
            lines.append("  Undeclared API endpoints (exist but not in manifest):")
            for repo_name, endpoints in sorted(discovery.undeclared_endpoints.items()):
                lines.append(f"    {repo_name}:")
                for ep in endpoints[:10]:
                    lines.append(f"      - {ep}")
                if len(endpoints) > 10:
                    lines.append(f"      ... and {len(endpoints) - 10} more")
        else:
            lines.append("  No undeclared API endpoints found.")
        lines.append("")

    return "\n".join(lines)


def _format_json(
    ui_reports: dict[str, UICoverageReport],
    api_reports: dict[str, APICoverageReport],
    discovery: DiscoveryReport | None,
) -> str:
    """Format results as JSON."""
    total_journeys = sum(r.journeys_declared for r in ui_reports.values())
    total_covered = sum(r.journeys_covered for r in ui_reports.values())
    total_critical_uncovered = sum(len(r.critical_uncovered) for r in ui_reports.values())
    pct = (total_covered / total_journeys * 100) if total_journeys > 0 else 0.0

    output: dict[str, object] = {
        "summary": {
            "total_journeys": total_journeys,
            "covered_journeys": total_covered,
            "coverage_pct": round(pct, 1),
            "critical_uncovered_count": total_critical_uncovered,
        },
        "ui_reports": {
            repo: {
                "repo_exists": r.repo_exists,
                "journeys_declared": r.journeys_declared,
                "journeys_covered": r.journeys_covered,
                "critical_uncovered": r.critical_uncovered,
                "journeys": [
                    {
                        "journey_id": res.journey.journey_id,
                        "criticality": res.journey.criticality,
                        "covered": res.covered,
                        "match_type": res.match_summary,
                        "test_files": res.test_files_matched,
                    }
                    for res in r.results
                ],
            }
            for repo, r in sorted(ui_reports.items())
        },
        "api_reports": {
            api: {
                "repo_exists": r.repo_exists,
                "endpoints_declared": r.endpoints_declared,
                "endpoints_found": r.endpoints_found,
                "endpoints_missing": r.endpoints_missing,
            }
            for api, r in sorted(api_reports.items())
        },
    }

    if discovery is not None:
        output["discovery"] = {
            "undeclared_test_files": discovery.undeclared_test_files,
            "undeclared_endpoints": discovery.undeclared_endpoints,
        }

    return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point for the UI/API flow coverage checker."""
    parser = argparse.ArgumentParser(
        description="UI/API flow coverage checker — validates test coverage against flow manifest.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root directory (default: auto-detect from script location)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--warning-only",
        action="store_true",
        default=False,
        help="Always exit 0, even if critical journeys are uncovered",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        default=False,
        help="Also report undeclared test files and API endpoints",
    )

    args = parser.parse_args(argv)

    # Resolve workspace root
    if args.workspace_root is not None:
        workspace_root = Path(args.workspace_root).resolve()
    else:
        # Default: grandparent of this script's parent (scripts/checkers/ -> unified-trading-pm -> workspace)
        workspace_root = Path(__file__).resolve().parent.parent.parent.parent

    pm_root = workspace_root / "unified-trading-pm"
    manifest_path = pm_root / _MANIFEST_FILENAME
    mapping_path = pm_root / _UI_API_MAPPING_FILENAME

    # Validate manifest
    if not manifest_path.is_file():
        print(f"ERROR: Manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    # Load data
    try:
        journeys = load_manifest(manifest_path)
    except (yaml.YAMLError, KeyError) as exc:
        print(f"ERROR: Failed to parse manifest: {exc}", file=sys.stderr)
        return 2

    if not journeys:
        print("WARNING: No journeys found in manifest", file=sys.stderr)
        return 0

    ui_api_mapping = load_ui_api_mapping(mapping_path)

    # Run checks
    ui_reports = check_ui_coverage(workspace_root, journeys)
    api_reports = check_api_endpoints(workspace_root, journeys, ui_api_mapping)

    discovery: DiscoveryReport | None = None
    if args.discover:
        discovery = run_discovery(workspace_root, journeys, ui_api_mapping)

    # Format and print output
    if args.format == "json":
        output = _format_json(ui_reports, api_reports, discovery)
    else:
        output = _format_text(ui_reports, api_reports, discovery)

    print(output)

    # Determine exit code
    total_critical_uncovered = sum(len(r.critical_uncovered) for r in ui_reports.values())

    if args.warning_only:
        return 0

    return 1 if total_critical_uncovered > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
