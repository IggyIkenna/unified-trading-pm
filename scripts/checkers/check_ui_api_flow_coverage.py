#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""UI/API flow coverage checker -- validates test coverage against flow manifest.

Loads ui-api-flow-test-manifest.yaml and checks that each declared journey
has corresponding test files referencing the page route, control IDs, or
API endpoints. Reports coverage per-UI, per-API, and overall.

Usage
-----
    python check_ui_api_flow_coverage.py                         # default scan
    python check_ui_api_flow_coverage.py --warning-only          # always exit 0
    python check_ui_api_flow_coverage.py --block-critical-gaps   # BLOCK if critical has no real-flow

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

import yaml

_MANIFEST_FILENAME = "ui-api-flow-test-manifest.yaml"
_UI_API_MAPPING_FILENAME = "scripts/dev/ui-api-mapping.json"
_UI_TEST_GLOBS = ("**/*.test.ts", "**/*.test.tsx", "**/*.spec.ts", "**/*.spec.tsx")
_E2E_DIR_NAME = "e2e"
_ROUTE_DECORATOR_RE = re.compile(r"@(?:app|router)\.(get|post|put|delete|patch)\(\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
_EXCLUDED_DIRS = frozenset({"node_modules", ".venv", ".venv-workspace", "dist", "build", ".next", "__pycache__"})


@dataclass
class Journey:
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
    journey: Journey
    test_files_matched: list[str] = field(default_factory=list)
    route_match: bool = False
    control_match: bool = False
    endpoint_match: bool = False
    has_real_flow_test: bool = False

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
        if self.has_real_flow_test:
            parts.append("real_flow")
        return "+".join(parts) if parts else "none"


@dataclass
class UICoverageReport:
    repo: str
    repo_exists: bool
    journeys_declared: int = 0
    journeys_covered: int = 0
    critical_uncovered: list[str] = field(default_factory=list)
    critical_no_real_flow: list[str] = field(default_factory=list)
    results: list[JourneyCoverageResult] = field(default_factory=list)


@dataclass
class APICoverageReport:
    repo: str
    repo_exists: bool
    endpoints_declared: list[str] = field(default_factory=list)
    endpoints_found: list[str] = field(default_factory=list)
    endpoints_missing: list[str] = field(default_factory=list)


@dataclass
class DiscoveryReport:
    undeclared_test_files: dict[str, list[str]] = field(default_factory=dict)
    undeclared_endpoints: dict[str, list[str]] = field(default_factory=dict)


def _find_test_files(repo_path: Path) -> list[Path]:
    test_files: list[Path] = []
    for glob_pat in _UI_TEST_GLOBS:
        for f in repo_path.glob(glob_pat):
            if not any(part in _EXCLUDED_DIRS for part in f.parts):
                test_files.append(f)
    for e2e_dir in repo_path.rglob(_E2E_DIR_NAME):
        if not e2e_dir.is_dir() or any(part in _EXCLUDED_DIRS for part in e2e_dir.parts):
            continue
        for f in e2e_dir.rglob("*"):
            if f.is_file() and f.suffix in (".ts", ".tsx", ".js", ".jsx") and f not in test_files:
                test_files.append(f)
    return sorted(set(test_files))


def _read_file_safe(filepath: Path) -> str:
    try:
        return filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _normalise_route_for_search(route: str) -> str:
    return re.sub(r"\{[^}]+\}", "", route).rstrip("/")


def _extract_search_terms(journey: Journey) -> list[str]:
    terms: list[str] = []
    route_norm = _normalise_route_for_search(journey.page_or_route)
    if route_norm and route_norm != "/":
        terms.append(route_norm)
        last_seg = route_norm.rsplit("/", 1)[-1]
        if last_seg and len(last_seg) > 2:
            terms.append(last_seg)
    testid_m = re.search(r"data-testid=['\"]([^'\"]+)['\"]", journey.control_id)
    if testid_m:
        terms.append(testid_m.group(1))
    hastext_m = re.search(r"has-text\(['\"]([^'\"]+)['\"]\)", journey.control_id)
    if hastext_m:
        terms.append(hastext_m.group(1))
    if journey.expected_request:
        parts = journey.expected_request.split(" ", 1)
        if len(parts) == 2:
            ep = _normalise_route_for_search(parts[1])
            if ep:
                terms.append(ep)
            last_ep = ep.rsplit("/", 1)[-1]
            if last_ep and len(last_ep) > 2:
                terms.append(last_ep)
    terms.append(journey.journey_id)
    seen: set[str] = set()
    unique: list[str] = []
    for t in terms:
        low = t.lower()
        if low not in seen:
            seen.add(low)
            unique.append(t)
    return unique


def _is_real_flow_test(test_file: Path, content: str) -> bool:
    """Determine if a test file is a real-flow (Playwright e2e) test."""
    if "e2e" in [p.lower() for p in test_file.parts]:
        return True
    indicators = (
        "from '@playwright/test'",
        'from "@playwright/test"',
        "page.goto(",
        "page.route(",
        "browser.newpage(",
        "test.describe(",
    )
    cl = content.lower()
    return any(ind.lower() in cl for ind in indicators)


def _check_journey_in_test_files(
    journey: Journey, test_files: list[Path], test_contents: dict[Path, str], repo_path: Path
) -> JourneyCoverageResult:
    result = JourneyCoverageResult(journey=journey)
    search_terms = _extract_search_terms(journey)
    route_norm = _normalise_route_for_search(journey.page_or_route)
    for test_file in test_files:
        content = test_contents.get(test_file, "")
        if not content:
            continue
        matched = False
        if route_norm and route_norm != "/" and route_norm in content:
            result.route_match = True
            matched = True
        testid_m = re.search(r"data-testid=['\"]([^'\"]+)['\"]", journey.control_id)
        if testid_m and testid_m.group(1) in content:
            result.control_match = True
            matched = True
        if journey.expected_request:
            ep_parts = journey.expected_request.split(" ", 1)
            if len(ep_parts) == 2:
                ep_path = _normalise_route_for_search(ep_parts[1])
                if ep_path and ep_path in content:
                    result.endpoint_match = True
                    matched = True
        if not matched:
            for term in search_terms:
                if len(term) > 2 and term.lower() in content.lower():
                    matched = True
                    break
        if matched:
            rel_path = str(test_file.relative_to(repo_path))
            if rel_path not in result.test_files_matched:
                result.test_files_matched.append(rel_path)
            if _is_real_flow_test(test_file, content):
                result.has_real_flow_test = True
    return result


def _scan_api_routes(api_repo_path: Path) -> list[str]:
    routes: list[str] = []
    for py_file in api_repo_path.rglob("*.py"):
        if any(part in _EXCLUDED_DIRS for part in py_file.parts):
            continue
        content = _read_file_safe(py_file)
        for match in _ROUTE_DECORATOR_RE.finditer(content):
            if match.group(2) not in routes:
                routes.append(match.group(2))
    return sorted(routes)


def _normalise_endpoint_for_comparison(endpoint: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", endpoint).lower().rstrip("/")


def _endpoint_exists_in_routes(endpoint: str, api_routes: list[str]) -> bool:
    norm_ep = _normalise_endpoint_for_comparison(endpoint)
    for route in api_routes:
        nr = _normalise_endpoint_for_comparison(route)
        if norm_ep == nr or nr.startswith(norm_ep) or norm_ep.startswith(nr):
            return True
    return False


def load_manifest(manifest_path: Path) -> list[Journey]:
    with open(manifest_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return [
        Journey(
            repo=e["repo"],
            journey_id=e["journey_id"],
            page_or_route=e.get("page_or_route", ""),
            control_id=e.get("control_id", ""),
            interaction_type=e.get("interaction_type", ""),
            expected_request=e.get("expected_request", ""),
            expected_response_contract=e.get("expected_response_contract", ""),
            expected_ui_update=e.get("expected_ui_update", ""),
            required_layers=e.get("required_layers", []),  # noqa: qg-empty-fallback
            criticality=e.get("criticality", "medium"),
        )
        for e in data.get("journeys", [])  # noqa: qg-empty-fallback
    ]


def load_ui_api_mapping(mapping_path: Path) -> dict[str, str]:
    if not mapping_path.is_file():
        return {}
    with open(mapping_path, encoding="utf-8") as f:
        data = json.load(f)
    mapping: dict[str, str] = {}
    for _name, info in data.get("stacks", data).items():
        ui, api = info.get("ui"), info.get("api")
        if ui and api:
            mapping[ui] = api
    return mapping


def check_ui_coverage(workspace_root: Path, journeys: list[Journey]) -> dict[str, UICoverageReport]:
    by_repo: dict[str, list[Journey]] = {}
    for j in journeys:
        by_repo.setdefault(j.repo, []).append(j)
    reports: dict[str, UICoverageReport] = {}
    for repo_name, repo_journeys in sorted(by_repo.items()):
        repo_path = workspace_root / repo_name
        repo_exists = repo_path.is_dir()
        report = UICoverageReport(repo=repo_name, repo_exists=repo_exists, journeys_declared=len(repo_journeys))
        if not repo_exists:
            for j in repo_journeys:
                report.results.append(JourneyCoverageResult(journey=j))
                if j.criticality == "critical":
                    report.critical_uncovered.append(j.journey_id)
                    if "real_flow" in j.required_layers:
                        report.critical_no_real_flow.append(j.journey_id)
            reports[repo_name] = report
            continue
        test_files = _find_test_files(repo_path)
        test_contents = {tf: _read_file_safe(tf) for tf in test_files}
        for j in repo_journeys:
            result = _check_journey_in_test_files(j, test_files, test_contents, repo_path)
            report.results.append(result)
            if result.covered:
                report.journeys_covered += 1
            elif j.criticality == "critical":
                report.critical_uncovered.append(j.journey_id)
            if j.criticality == "critical" and "real_flow" in j.required_layers and not result.has_real_flow_test:
                report.critical_no_real_flow.append(j.journey_id)
        reports[repo_name] = report
    return reports


def check_api_endpoints(
    workspace_root: Path, journeys: list[Journey], ui_api_mapping: dict[str, str]
) -> dict[str, APICoverageReport]:
    api_eps: dict[str, list[str]] = {}
    for j in journeys:
        if not j.expected_request:
            continue
        parts = j.expected_request.split(" ", 1)
        if len(parts) != 2:
            continue
        api_repo = ui_api_mapping.get(j.repo)
        if not api_repo:
            continue
        api_eps.setdefault(api_repo, [])
        if parts[1] not in api_eps[api_repo]:
            api_eps[api_repo].append(parts[1])
    reports: dict[str, APICoverageReport] = {}
    for api_repo, declared in sorted(api_eps.items()):
        rp = workspace_root / api_repo
        report = APICoverageReport(repo=api_repo, repo_exists=rp.is_dir(), endpoints_declared=declared)
        if rp.is_dir():
            actual = _scan_api_routes(rp)
            for ep in declared:
                (report.endpoints_found if _endpoint_exists_in_routes(ep, actual) else report.endpoints_missing).append(
                    ep
                )
        else:
            report.endpoints_missing = list(declared)
        reports[api_repo] = report
    return reports


def run_discovery(workspace_root: Path, journeys: list[Journey], ui_api_mapping: dict[str, str]) -> DiscoveryReport:
    discovery = DiscoveryReport()
    declared_repos = {j.repo for j in journeys}
    for ui_dir in sorted(workspace_root.iterdir()):
        if not ui_dir.is_dir() or not ui_dir.name.endswith("-ui"):
            continue
        test_files = _find_test_files(ui_dir)
        if not test_files:
            continue
        if ui_dir.name not in declared_repos:
            discovery.undeclared_test_files[ui_dir.name] = [str(f.relative_to(ui_dir)) for f in test_files]
            continue
        all_terms: set[str] = set()
        for j in [jj for jj in journeys if jj.repo == ui_dir.name]:
            all_terms.update(t.lower() for t in _extract_search_terms(j))
        unmatched = [
            str(tf.relative_to(ui_dir))
            for tf in test_files
            if not any(t in _read_file_safe(tf).lower() for t in all_terms if len(t) > 2)
        ]
        if unmatched:
            discovery.undeclared_test_files[ui_dir.name] = unmatched
    manifest_eps: dict[str, set[str]] = {}
    for j in journeys:
        ar = ui_api_mapping.get(j.repo)
        if not ar or not j.expected_request:
            continue
        parts = j.expected_request.split(" ", 1)
        if len(parts) == 2:
            manifest_eps.setdefault(ar, set()).add(_normalise_endpoint_for_comparison(parts[1]))
    for api_dir in sorted(workspace_root.iterdir()):
        if not api_dir.is_dir() or not api_dir.name.endswith("-api"):
            continue
        actual = _scan_api_routes(api_dir)
        if not actual:
            continue
        ds = manifest_eps.get(api_dir.name, set())
        undeclared = []
        for route in actual:
            norm = _normalise_endpoint_for_comparison(route)
            if any(s in norm for s in ("/health", "/readiness", "/{full_path", "/cache/clear", "/workers")):
                continue
            if not any(norm == d or norm.startswith(d) or d.startswith(norm) for d in ds):
                undeclared.append(route)
        if undeclared:
            discovery.undeclared_endpoints[api_dir.name] = undeclared
    return discovery


def _format_text(
    ui_reports: dict[str, UICoverageReport],
    api_reports: dict[str, APICoverageReport],
    discovery: DiscoveryReport | None,
) -> str:
    lines: list[str] = []
    total_j = sum(r.journeys_declared for r in ui_reports.values())
    total_c = sum(r.journeys_covered for r in ui_reports.values())
    total_cu = sum(len(r.critical_uncovered) for r in ui_reports.values())
    total_cnrf = sum(len(r.critical_no_real_flow) for r in ui_reports.values())
    pct = (total_c / total_j * 100) if total_j > 0 else 0.0
    lines.append("=" * 60)
    lines.append("UI/API Flow Coverage Report")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Overall: {total_c}/{total_j} journeys covered ({pct:.1f}%)")
    lines.append(f"Critical uncovered: {total_cu}")
    if total_cnrf > 0:
        lines.append(f"BLOCK: {total_cnrf} critical journey(s) have ZERO real-flow tests")
    lines.append("")
    lines.append("-" * 60)
    lines.append("Per-UI Summary")
    lines.append("-" * 60)
    for rn, rpt in sorted(ui_reports.items()):
        etag = "" if rpt.repo_exists else " [REPO NOT FOUND]"
        cp = (rpt.journeys_covered / rpt.journeys_declared * 100) if rpt.journeys_declared > 0 else 0.0
        lines.append(f"  {rn}: {rpt.journeys_covered}/{rpt.journeys_declared} ({cp:.0f}%){etag}")
        for res in rpt.results:
            j = res.journey
            st = "PASS" if res.covered else "MISS"
            ct = f" [{j.criticality.upper()}]" if j.criticality == "critical" else ""
            mi = f" ({res.match_summary})" if res.covered else ""
            lines.append(f"    {st} {j.journey_id}{ct}{mi}")
            if res.covered:
                for tf in res.test_files_matched[:3]:
                    lines.append(f"         -> {tf}")
        if rpt.critical_uncovered:
            lines.append(f"    ** CRITICAL UNCOVERED: {', '.join(rpt.critical_uncovered)}")
        if rpt.critical_no_real_flow:
            lines.append(f"    ** BLOCK -- CRITICAL NO REAL-FLOW: {', '.join(rpt.critical_no_real_flow)}")
        lines.append("")
    if api_reports:
        lines.append("-" * 60)
        lines.append("Per-API Endpoint Existence")
        lines.append("-" * 60)
        for an, ar in sorted(api_reports.items()):
            et = "" if ar.repo_exists else " [REPO NOT FOUND]"
            lines.append(f"  {an}: {len(ar.endpoints_found)}/{len(ar.endpoints_declared)} endpoints exist{et}")
            for ep in ar.endpoints_missing:
                lines.append(f"    MISSING: {ep}")
        lines.append("")
    if discovery is not None:
        lines.append("-" * 60)
        lines.append("Auto-Discovery: Undeclared Items")
        lines.append("-" * 60)
        if discovery.undeclared_test_files:
            lines.append("  Undeclared test files (exist but not in manifest):")
            for rn, files in sorted(discovery.undeclared_test_files.items()):
                lines.append(f"    {rn}:")
                for f in files[:10]:
                    lines.append(f"      - {f}")
                if len(files) > 10:
                    lines.append(f"      ... and {len(files) - 10} more")
        else:
            lines.append("  No undeclared test files found.")
        lines.append("")
        if discovery.undeclared_endpoints:
            lines.append("  Undeclared API endpoints (exist but not in manifest):")
            for rn, eps in sorted(discovery.undeclared_endpoints.items()):
                lines.append(f"    {rn}:")
                for ep in eps[:10]:
                    lines.append(f"      - {ep}")
                if len(eps) > 10:
                    lines.append(f"      ... and {len(eps) - 10} more")
        else:
            lines.append("  No undeclared API endpoints found.")
        lines.append("")
    return "\n".join(lines)


def _format_json(
    ui_reports: dict[str, UICoverageReport],
    api_reports: dict[str, APICoverageReport],
    discovery: DiscoveryReport | None,
) -> str:
    tj = sum(r.journeys_declared for r in ui_reports.values())
    tc = sum(r.journeys_covered for r in ui_reports.values())
    tcu = sum(len(r.critical_uncovered) for r in ui_reports.values())
    tcnrf = sum(len(r.critical_no_real_flow) for r in ui_reports.values())
    pct = (tc / tj * 100) if tj > 0 else 0.0
    output: dict[str, object] = {
        "summary": {
            "total_journeys": tj,
            "covered_journeys": tc,
            "coverage_pct": round(pct, 1),
            "critical_uncovered_count": tcu,
            "critical_no_real_flow_count": tcnrf,
            "block": tcnrf > 0,
        },
        "ui_reports": {
            repo: {
                "repo_exists": r.repo_exists,
                "journeys_declared": r.journeys_declared,
                "journeys_covered": r.journeys_covered,
                "critical_uncovered": r.critical_uncovered,
                "critical_no_real_flow": r.critical_no_real_flow,
                "journeys": [
                    {
                        "journey_id": res.journey.journey_id,
                        "criticality": res.journey.criticality,
                        "covered": res.covered,
                        "has_real_flow_test": res.has_real_flow_test,
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UI/API flow coverage checker")
    parser.add_argument("--workspace-root", type=Path, default=None)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--warning-only", action="store_true", default=False)
    parser.add_argument("--discover", action="store_true", default=False)
    parser.add_argument(
        "--block-critical-gaps",
        action="store_true",
        default=False,
        help="Exit 1 (BLOCK) if any critical journey has zero real-flow tests",
    )
    args = parser.parse_args(argv)
    ws = (
        Path(args.workspace_root).resolve()
        if args.workspace_root
        else Path(__file__).resolve().parent.parent.parent.parent
    )
    pm = ws / "unified-trading-pm"
    manifest_path, mapping_path = pm / _MANIFEST_FILENAME, pm / _UI_API_MAPPING_FILENAME
    if not manifest_path.is_file():
        print(f"ERROR: Manifest not found: {manifest_path}", file=sys.stderr)
        return 2
    try:
        journeys = load_manifest(manifest_path)
    except (yaml.YAMLError, KeyError) as exc:
        print(f"ERROR: Failed to parse manifest: {exc}", file=sys.stderr)
        return 2
    if not journeys:
        print("WARNING: No journeys found in manifest", file=sys.stderr)
        return 0
    ui_api_mapping = load_ui_api_mapping(mapping_path)
    ui_reports = check_ui_coverage(ws, journeys)
    api_reports = check_api_endpoints(ws, journeys, ui_api_mapping)
    discovery: DiscoveryReport | None = run_discovery(ws, journeys, ui_api_mapping) if args.discover else None
    output = (
        _format_json(ui_reports, api_reports, discovery)
        if args.format == "json"
        else _format_text(ui_reports, api_reports, discovery)
    )
    print(output)
    tcu = sum(len(r.critical_uncovered) for r in ui_reports.values())
    tcnrf = sum(len(r.critical_no_real_flow) for r in ui_reports.values())
    if args.warning_only:
        return 0
    if args.block_critical_gaps and tcnrf > 0:
        print(f"\nBLOCK: {tcnrf} critical journey(s) require real-flow tests but have none.", file=sys.stderr)
        return 1
    return 1 if tcu > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
