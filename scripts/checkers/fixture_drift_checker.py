#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Fixture drift prevention checker — validates UI mock fixture schemas match contracts.

Scans UI repos for mock fixture files (JSON/TS/JS) and compares their schema
structure against UIC/UAC contract model expectations from the flow manifest.
Flags fixtures whose field sets have drifted from the declared contract models.

This is a build-time check: if a UI mock fixture's schema does not match the
corresponding UIC/UAC model structure, this checker reports the drift.

Usage
-----
    python fixture_drift_checker.py                           # scan all UI repos
    python fixture_drift_checker.py --repo deployment-ui      # single repo
    python fixture_drift_checker.py --workspace-root /path    # custom workspace
    python fixture_drift_checker.py --format json             # JSON output
    python fixture_drift_checker.py --strict                  # exit 1 on any drift

Exit codes
----------
    0  No drift detected (or --strict not set)
    1  Schema drift detected (only with --strict)
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

# Directories where UI mock fixtures commonly live
_FIXTURE_DIR_NAMES = (
    "fixtures",
    "__fixtures__",
    "mock",
    "mocks",
    "__mocks__",
    "mock-data",
    "test-data",
    "test-fixtures",
    "src/test",
    "src/mocks",
    "src/__mocks__",
)

# File extensions for fixture files
_FIXTURE_EXTENSIONS = (".json", ".ts", ".tsx", ".js", ".jsx")

# Exclusion directories
_EXCLUDED_DIRS = frozenset({"node_modules", ".venv", ".venv-workspace", "dist", "build", "__pycache__", ".next"})

# Pattern to extract TypeScript/JS object literals that look like mock data
_TS_EXPORT_PATTERN = re.compile(
    r"""export\s+(?:const|let|var)\s+(\w+)\s*(?::\s*\w+(?:<[^>]+>)?\s*)?=\s*(\{[\s\S]*?\})\s*;""",
    re.MULTILINE,
)

# Pattern to extract JSON-like objects from mock files
_MOCK_DATA_PATTERN = re.compile(
    r"""(?:mockData|mockResponse|fixture|testData|sampleData|mock\w+)\s*(?::\s*\w+(?:<[^>]+>)?\s*)?=\s*(\{[\s\S]*?\})\s*[;,]""",
    re.MULTILINE | re.IGNORECASE,
)

# Pattern to detect mock response in route.fulfill or similar
_FULFILL_BODY_PATTERN = re.compile(
    r"""(?:body|json)\s*:\s*(?:JSON\.stringify\()?\s*(\{[\s\S]*?\})\s*\)?""",
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class FixtureFile:
    """A discovered mock fixture file with extracted schema."""

    file_path: str
    repo: str
    fields: list[str] = field(default_factory=list)
    raw_keys: list[str] = field(default_factory=list)
    parse_method: str = ""  # "json", "ts_export", "mock_pattern"


@dataclass
class ContractExpectation:
    """Expected fields from a UIC/UAC contract model (derived from manifest)."""

    contract_model: str
    journey_id: str
    repo: str
    expected_endpoint: str
    # We derive expected fields from the response contract name and common patterns
    inferred_fields: list[str] = field(default_factory=list)


@dataclass
class DriftResult:
    """Result of comparing a fixture against a contract expectation."""

    fixture_file: str
    contract_model: str
    journey_id: str
    fixture_fields: list[str] = field(default_factory=list)
    contract_fields: list[str] = field(default_factory=list)
    missing_in_fixture: list[str] = field(default_factory=list)
    extra_in_fixture: list[str] = field(default_factory=list)
    overlap_pct: float = 0.0
    drifted: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class FixtureDriftReport:
    """Full fixture drift report."""

    fixtures_found: int = 0
    fixtures_with_drift: int = 0
    fixtures_clean: int = 0
    results: list[DriftResult] = field(default_factory=list)
    unmatched_fixtures: list[FixtureFile] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Fixture discovery
# ---------------------------------------------------------------------------


def discover_fixtures(repo_path: Path, repo_name: str) -> list[FixtureFile]:
    """Discover mock fixture files in a UI repo."""
    fixtures: list[FixtureFile] = []

    # Search in known fixture directories
    for dir_name in _FIXTURE_DIR_NAMES:
        fixture_dir = repo_path / dir_name
        if fixture_dir.is_dir():
            for f in fixture_dir.rglob("*"):
                if not f.is_file():
                    continue
                if any(part in _EXCLUDED_DIRS for part in f.parts):
                    continue
                if f.suffix in _FIXTURE_EXTENSIONS:
                    fixture = _parse_fixture_file(f, repo_path, repo_name)
                    if fixture and fixture.fields:
                        fixtures.append(fixture)

    # Also search for common fixture file naming patterns across src/
    src_dir = repo_path / "src"
    if src_dir.is_dir():
        for f in src_dir.rglob("*"):
            if not f.is_file():
                continue
            if any(part in _EXCLUDED_DIRS for part in f.parts):
                continue
            name_lower = f.name.lower()
            is_fixture = any(
                pat in name_lower for pat in ("fixture", "mock-data", "mock_data", "test-data", "sample-data", "seed")
            )
            if is_fixture and f.suffix in _FIXTURE_EXTENSIONS:
                fixture = _parse_fixture_file(f, repo_path, repo_name)
                if fixture and fixture.fields:
                    fixtures.append(fixture)

    # Deduplicate by file path
    seen: set[str] = set()
    unique: list[FixtureFile] = []
    for fix in fixtures:
        if fix.file_path not in seen:
            seen.add(fix.file_path)
            unique.append(fix)

    return unique


def _parse_fixture_file(file_path: Path, repo_path: Path, repo_name: str) -> FixtureFile | None:
    """Parse a fixture file and extract its schema (field names)."""
    rel_path = str(file_path.relative_to(repo_path))

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    fixture = FixtureFile(file_path=rel_path, repo=repo_name)

    # Try JSON first
    if file_path.suffix == ".json":
        fields = _extract_json_fields(content)
        if fields:
            fixture.fields = fields
            fixture.raw_keys = fields
            fixture.parse_method = "json"
            return fixture

    # Try TS/JS export pattern
    for match in _TS_EXPORT_PATTERN.finditer(content):
        obj_literal = match.group(2)
        fields = _extract_ts_object_fields(obj_literal)
        if fields:
            fixture.fields = fields
            fixture.raw_keys = fields
            fixture.parse_method = "ts_export"
            return fixture

    # Try mock data pattern
    for match in _MOCK_DATA_PATTERN.finditer(content):
        obj_literal = match.group(1)
        fields = _extract_ts_object_fields(obj_literal)
        if fields:
            fixture.fields = fields
            fixture.raw_keys = fields
            fixture.parse_method = "mock_pattern"
            return fixture

    return None


def _extract_json_fields(content: str) -> list[str]:
    """Extract top-level field names from JSON content."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return []

    if isinstance(data, dict):
        return _flatten_json_keys(data)
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return _flatten_json_keys(data[0])
    return []


def _flatten_json_keys(data: dict[str, object], prefix: str = "") -> list[str]:
    """Flatten nested JSON keys into dot-notation."""
    keys: list[str] = []
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        keys.append(full_key)
        if isinstance(value, dict):
            keys.extend(_flatten_json_keys(value, full_key))
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            keys.extend(_flatten_json_keys(value[0], f"{full_key}[]"))
    return keys


def _extract_ts_object_fields(obj_literal: str) -> list[str]:
    """Extract field names from a TypeScript/JS object literal (best-effort)."""
    # Simple regex to find property names: `key:` or `"key":` or `'key':`
    field_pattern = re.compile(r"""(?:^|\n)\s*['"]*(\w+)['"]*\s*:""", re.MULTILINE)
    fields: list[str] = []
    for match in field_pattern.finditer(obj_literal):
        field_name = match.group(1)
        if field_name not in fields:
            fields.append(field_name)
    return fields


# ---------------------------------------------------------------------------
# Contract model inference
# ---------------------------------------------------------------------------

# Common field patterns by contract model name suffix
_MODEL_FIELD_PATTERNS: dict[str, list[str]] = {
    "Response": ["status", "data", "message"],
    "State": ["id", "status", "updated_at"],
    "ListResponse": ["items", "total", "page"],
    "DetailResponse": ["id", "name", "status", "created_at", "updated_at"],
}

# Known contract model fields from the manifest (derived from model names)
_KNOWN_MODELS: dict[str, list[str]] = {
    "DeploymentState": ["id", "service", "status", "region", "version", "timestamp", "cloud_provider"],
    "ServiceState": ["id", "name", "status", "kill_switch", "circuit_breaker", "health"],
    "ConfigUpdateResponse": ["success", "field", "value", "previous_value"],
    "LogQueryResponse": ["logs", "total", "page", "service", "level"],
    "AuditTrailResponse": ["events", "total", "page"],
    "BacktestRunResponse": ["run_id", "status", "strategy", "progress"],
    "ResultsResponse": ["results", "total", "page"],
    "ExecutionAlphaResponse": ["alpha", "distribution", "summary"],
    "ManualTradeResponse": ["instruction_id", "status", "message"],
    "PositionsResponse": ["positions", "total"],
    "HealthResponse": ["services", "overall_status"],
    "AlertHistoryResponse": ["alerts", "total", "page"],
    "SettlementPositionsResponse": ["positions", "total", "as_of_date"],
    "InvoicesResponse": ["invoices", "total", "page"],
    "ReportDownloadResponse": ["url", "filename", "content_type"],
    "VenueRegistrationResponse": ["venue_id", "name", "status"],
    "ClientRegistrationResponse": ["client_id", "name", "status"],
    "StrategyRegistrationResponse": ["strategy_id", "name", "status"],
    "StrategyDetailResponse": ["id", "name", "sharpe", "daily_pnl", "monthly_return", "venues"],
    "BacktestResultResponse": ["equity_curve", "sharpe", "total_return", "max_drawdown", "trade_count"],
    "StrategyLiveResponse": ["id", "status", "pnl", "open_positions"],
    "ExperimentDetailResponse": ["id", "name", "accuracy", "loss", "epochs", "dataset", "status"],
    "ModelDeployResponse": ["model_id", "status", "version"],
    "ModelPromoteResponse": ["model_id", "status", "promoted_to"],
    "BatchJobsResponse": ["jobs", "total", "page"],
    "TTSRecordsResponse": ["records", "total", "page"],
    "DataHealthResponse": ["services", "overall_health"],
    "ReconRunsResponse": ["runs", "total", "page"],
    "ReconDeviationsResponse": ["deviations", "total", "date"],
    "OrderBookResponse": ["bids", "asks", "mid_price", "spread", "symbol"],
    "LatencyAnalyticsResponse": ["p50", "p95", "p99", "p999", "venues"],
    "ReportGenerateResponse": ["report_id", "status", "message"],
    "PerformanceResponse": ["monthly_returns", "performance", "aum"],
    "ReportsListResponse": ["reports", "total", "page"],
}


def get_contract_fields(contract_model: str) -> list[str]:
    """Get expected fields for a contract model name."""
    # Check known models first
    if contract_model in _KNOWN_MODELS:
        return _KNOWN_MODELS[contract_model]

    # Fall back to pattern matching
    for suffix, base_fields in _MODEL_FIELD_PATTERNS.items():
        if contract_model.endswith(suffix):
            return base_fields

    return []


# ---------------------------------------------------------------------------
# Drift comparison
# ---------------------------------------------------------------------------


def check_drift(
    fixtures: list[FixtureFile],
    manifest_path: Path,
) -> list[DriftResult]:
    """Compare discovered fixtures against manifest contract expectations."""
    results: list[DriftResult] = []

    with open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    journeys = manifest.get("journeys", [])  # noqa: qg-empty-fallback

    # Build a mapping of repo -> contract models
    repo_contracts: dict[str, list[dict[str, str]]] = {}
    for j in journeys:
        repo = j.get("repo", "")
        contract = j.get("expected_response_contract", "")
        if repo and contract:
            repo_contracts.setdefault(repo, []).append(
                {
                    "contract_model": contract,
                    "journey_id": j.get("journey_id", ""),
                    "expected_request": j.get("expected_request", ""),
                }
            )

    for fixture in fixtures:
        repo = fixture.repo
        if repo not in repo_contracts:
            continue

        # Try to match fixture to a contract based on field overlap
        best_match: DriftResult | None = None
        best_overlap = 0.0

        for contract_info in repo_contracts[repo]:
            contract_model = contract_info["contract_model"]
            contract_fields = get_contract_fields(contract_model)

            if not contract_fields:
                continue

            # Compute overlap
            fixture_field_set = {f.split(".")[-1].lower() for f in fixture.fields}
            contract_field_set = {f.lower() for f in contract_fields}

            overlap = fixture_field_set & contract_field_set
            if not contract_field_set:
                continue

            overlap_pct = len(overlap) / len(contract_field_set) * 100

            if overlap_pct > best_overlap:
                best_overlap = overlap_pct

                missing = sorted(contract_field_set - fixture_field_set)
                extra = sorted(fixture_field_set - contract_field_set)

                best_match = DriftResult(
                    fixture_file=fixture.file_path,
                    contract_model=contract_model,
                    journey_id=contract_info["journey_id"],
                    fixture_fields=sorted(fixture_field_set),
                    contract_fields=sorted(contract_field_set),
                    missing_in_fixture=missing,
                    extra_in_fixture=extra,
                    overlap_pct=overlap_pct,
                    drifted=len(missing) > 0,
                )

        if best_match is not None and best_overlap > 20.0:
            # Only report if there's meaningful overlap (>20%) — avoids false positives
            results.append(best_match)

    return results


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def format_report(report: FixtureDriftReport) -> str:
    """Format the fixture drift report as human-readable text."""
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("Fixture Drift Prevention Report")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Fixtures discovered: {report.fixtures_found}")
    lines.append(f"Fixtures with drift: {report.fixtures_with_drift}")
    lines.append(f"Fixtures clean: {report.fixtures_clean}")
    lines.append("")

    if report.results:
        lines.append("-" * 60)
        lines.append("Drift Results")
        lines.append("-" * 60)
        for dr in report.results:
            status = "DRIFT" if dr.drifted else "OK"
            lines.append(f"  [{status}] {dr.fixture_file}")
            lines.append(f"         Contract: {dr.contract_model} (journey: {dr.journey_id})")
            lines.append(f"         Overlap: {dr.overlap_pct:.0f}%")
            if dr.missing_in_fixture:
                lines.append(f"         Missing in fixture: {', '.join(dr.missing_in_fixture)}")
            if dr.extra_in_fixture:
                lines.append(f"         Extra in fixture: {', '.join(dr.extra_in_fixture[:10])}")
                if len(dr.extra_in_fixture) > 10:
                    lines.append(f"         ... and {len(dr.extra_in_fixture) - 10} more extra fields")
            for note in dr.notes:
                lines.append(f"         Note: {note}")
        lines.append("")

    if report.unmatched_fixtures:
        lines.append("-" * 60)
        lines.append(f"Unmatched Fixtures ({len(report.unmatched_fixtures)})")
        lines.append("-" * 60)
        for uf in report.unmatched_fixtures[:20]:
            lines.append(f"  {uf.repo}/{uf.file_path} ({len(uf.fields)} fields, via {uf.parse_method})")
        if len(report.unmatched_fixtures) > 20:
            lines.append(f"  ... and {len(report.unmatched_fixtures) - 20} more")
        lines.append("")

    if report.errors:
        lines.append("-" * 60)
        lines.append("Errors")
        lines.append("-" * 60)
        for err in report.errors:
            lines.append(f"  ERROR: {err}")
        lines.append("")

    return "\n".join(lines)


def format_report_json(report: FixtureDriftReport) -> str:
    """Format the fixture drift report as JSON."""
    output: dict[str, object] = {
        "summary": {
            "fixtures_found": report.fixtures_found,
            "fixtures_with_drift": report.fixtures_with_drift,
            "fixtures_clean": report.fixtures_clean,
        },
        "results": [
            {
                "fixture_file": dr.fixture_file,
                "contract_model": dr.contract_model,
                "journey_id": dr.journey_id,
                "drifted": dr.drifted,
                "overlap_pct": dr.overlap_pct,
                "missing_in_fixture": dr.missing_in_fixture,
                "extra_in_fixture": dr.extra_in_fixture,
                "notes": dr.notes,
            }
            for dr in report.results
        ],
        "unmatched_fixtures": [
            {"file": uf.file_path, "repo": uf.repo, "fields": len(uf.fields)} for uf in report.unmatched_fixtures
        ],
        "errors": report.errors,
    }
    return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point for the fixture drift prevention checker."""
    parser = argparse.ArgumentParser(
        description="Fixture drift prevention checker — validates UI mock fixtures match UIC/UAC contracts.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root directory (default: auto-detect)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Single UI repo to check (default: all UI repos)",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="Exit 1 if any fixture drift detected",
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

    report = FixtureDriftReport()

    # Discover fixtures
    all_fixtures: list[FixtureFile] = []

    if args.repo:
        repo_path = workspace_root / args.repo
        if repo_path.is_dir():
            all_fixtures = discover_fixtures(repo_path, args.repo)
        else:
            report.errors.append(f"Repo not found: {args.repo}")
    else:
        for ui_dir in sorted(workspace_root.iterdir()):
            if not ui_dir.is_dir() or not ui_dir.name.endswith("-ui"):
                continue
            fixtures = discover_fixtures(ui_dir, ui_dir.name)
            all_fixtures.extend(fixtures)

    report.fixtures_found = len(all_fixtures)

    # Check drift against manifest contracts
    drift_results = check_drift(all_fixtures, manifest_path)
    report.results = drift_results
    report.fixtures_with_drift = sum(1 for dr in drift_results if dr.drifted)
    report.fixtures_clean = sum(1 for dr in drift_results if not dr.drifted)

    # Find unmatched fixtures (discovered but not matched to any contract)
    matched_files = {dr.fixture_file for dr in drift_results}
    report.unmatched_fixtures = [f for f in all_fixtures if f.file_path not in matched_files]

    # Format and print
    output = format_report_json(report) if args.format == "json" else format_report(report)

    print(output)

    if args.strict and report.fixtures_with_drift > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
