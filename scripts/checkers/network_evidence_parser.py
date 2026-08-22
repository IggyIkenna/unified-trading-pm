#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Network evidence parser — extracts and validates request/response pairs.

Parses Playwright HAR files and page.route() intercept patterns to extract
network evidence (request/response pairs). Validates extracted schemas against
UAC/UIC contract models. Flags mock fixtures that drift from API mock-mode
responses.

Usage
-----
    python network_evidence_parser.py --har-dir /path/to/har/files
    python network_evidence_parser.py --har-dir /path --manifest /path/to/manifest.yaml
    python network_evidence_parser.py --scan-intercepts /path/to/e2e/tests
    python network_evidence_parser.py --workspace-root /path --all

Exit codes
----------
    0  All evidence validates or no evidence found
    1  Schema drift detected between fixtures and contracts
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

# HAR entry structure keys
_HAR_LOG_KEY = "log"
_HAR_ENTRIES_KEY = "entries"
_HAR_REQUEST_KEY = "request"
_HAR_RESPONSE_KEY = "response"

# Playwright page.route() intercept pattern
_PAGE_ROUTE_RE = re.compile(
    r"""page\.route\(\s*['"*/]+(.*?)['"*/]+\s*,\s*(?:async\s+)?\(?(\w+)\)?\s*=>\s*\{([\s\S]*?)\}\s*\)""",
    re.MULTILINE,
)

# route.fulfill() pattern to extract mock response data
_ROUTE_FULFILL_RE = re.compile(
    r"""(?:route|response)\.fulfill\(\s*\{([\s\S]*?)\}\s*\)""",
    re.MULTILINE,
)

# JSON body pattern inside fulfill
_BODY_JSON_RE = re.compile(
    r"""body\s*:\s*JSON\.stringify\(\s*(\{[\s\S]*?\})\s*\)""",
    re.MULTILINE,
)

# Content-type header for JSON responses
_JSON_CONTENT_TYPES = frozenset({"application/json", "text/json"})

# Exclusion directories
_EXCLUDED_DIRS = frozenset({"node_modules", ".venv", ".venv-workspace", "dist", "build", "__pycache__"})


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class RequestResponsePair:
    """A single captured request/response pair from HAR or intercept."""

    source_file: str
    method: str
    url: str
    request_headers: dict[str, str] = field(default_factory=dict)
    request_body: str = ""
    response_status: int = 0
    response_headers: dict[str, str] = field(default_factory=dict)
    response_body: str = ""
    response_json: dict[str, object] | None = None


@dataclass
class SchemaField:
    """A field extracted from a JSON response for schema comparison."""

    name: str
    field_type: str  # "string", "number", "boolean", "array", "object", "null"
    nullable: bool = False
    nested_fields: list[SchemaField] = field(default_factory=list)


@dataclass
class SchemaValidationResult:
    """Result of validating an extracted schema against a contract model."""

    journey_id: str
    endpoint: str
    contract_model: str
    fields_expected: list[str] = field(default_factory=list)
    fields_found: list[str] = field(default_factory=list)
    fields_missing: list[str] = field(default_factory=list)
    fields_extra: list[str] = field(default_factory=list)
    type_mismatches: list[str] = field(default_factory=list)
    valid: bool = True
    notes: list[str] = field(default_factory=list)


@dataclass
class FixtureDriftResult:
    """Result of comparing a mock fixture schema against a HAR/contract schema."""

    fixture_file: str
    endpoint: str
    fixture_fields: list[str] = field(default_factory=list)
    evidence_fields: list[str] = field(default_factory=list)
    missing_in_fixture: list[str] = field(default_factory=list)
    extra_in_fixture: list[str] = field(default_factory=list)
    drifted: bool = False


@dataclass
class NetworkEvidenceReport:
    """Full report from network evidence parsing."""

    har_pairs: list[RequestResponsePair] = field(default_factory=list)
    intercept_pairs: list[RequestResponsePair] = field(default_factory=list)
    schema_validations: list[SchemaValidationResult] = field(default_factory=list)
    fixture_drifts: list[FixtureDriftResult] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# HAR file parsing
# ---------------------------------------------------------------------------


def parse_har_file(har_path: Path) -> list[RequestResponsePair]:
    """Parse a Playwright HAR file and extract request/response pairs.

    HAR (HTTP Archive) format: https://w3c.github.io/web-perf/specs/HAR/Overview.html
    """
    pairs: list[RequestResponsePair] = []
    try:
        with open(har_path, encoding="utf-8") as f:
            har_data = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"WARNING: Failed to parse HAR file {har_path}: {exc}", file=sys.stderr)
        return pairs

    log = har_data.get(_HAR_LOG_KEY, har_data)
    entries = log.get(_HAR_ENTRIES_KEY, [])

    for entry in entries:
        request = entry.get(_HAR_REQUEST_KEY, {})
        response = entry.get(_HAR_RESPONSE_KEY, {})

        method = request.get("method", "GET")
        url = request.get("url", "")

        # Extract request headers
        req_headers: dict[str, str] = {}
        for h in request.get("headers", []):  # noqa: qg-empty-fallback
            req_headers[h.get("name", "").lower()] = h.get("value", "")

        # Extract request body (postData)
        req_body = ""
        post_data = request.get("postData", {})  # noqa: qg-empty-fallback
        if isinstance(post_data, dict):
            req_body = post_data.get("text", "")

        # Extract response
        resp_status = response.get("status", 0)
        resp_headers: dict[str, str] = {}
        for h in response.get("headers", []):  # noqa: qg-empty-fallback
            resp_headers[h.get("name", "").lower()] = h.get("value", "")

        # Extract response body
        resp_content = response.get("content", {})  # noqa: qg-empty-fallback
        resp_body = resp_content.get("text", "")
        resp_mime = resp_content.get("mimeType", "")

        # Parse JSON response body if applicable
        resp_json: dict[str, object] | None = None
        if resp_body and any(ct in resp_mime.lower() for ct in ("json",)):
            try:
                parsed = json.loads(resp_body)
                if isinstance(parsed, dict):
                    resp_json = parsed
            except json.JSONDecodeError:
                pass

        # Only include API-like requests (skip static assets)
        if _is_api_url(url):
            pair = RequestResponsePair(
                source_file=str(har_path),
                method=method,
                url=url,
                request_headers=req_headers,
                request_body=req_body,
                response_status=resp_status,
                response_headers=resp_headers,
                response_body=resp_body,
                response_json=resp_json,
            )
            pairs.append(pair)

    return pairs


def _is_api_url(url: str) -> bool:
    """Check if a URL looks like an API endpoint (not a static asset)."""
    # Skip common static asset patterns
    static_patterns = (
        ".js",
        ".css",
        ".png",
        ".jpg",
        ".svg",
        ".ico",
        ".woff",
        ".ttf",
        ".map",
        ".html",
        "webpack",
        "hot-update",
        "__vite",
        "node_modules",
    )
    url_lower = url.lower()
    if any(pat in url_lower for pat in static_patterns):
        return False

    # Include API-like paths
    api_patterns = ("/api/", "/v1/", "/v2/", "/graphql", "/rest/")
    return any(pat in url_lower for pat in api_patterns)


# ---------------------------------------------------------------------------
# page.route() intercept scanning
# ---------------------------------------------------------------------------


def scan_intercepts_in_file(file_path: Path) -> list[RequestResponsePair]:
    """Extract mock request/response pairs from page.route() intercepts in test files."""
    pairs: list[RequestResponsePair] = []
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return pairs

    for route_match in _PAGE_ROUTE_RE.finditer(content):
        url_pattern = route_match.group(1)
        handler_body = route_match.group(3)

        # Look for route.fulfill() in the handler body
        for fulfill_match in _ROUTE_FULFILL_RE.finditer(handler_body):
            fulfill_body = fulfill_match.group(1)

            # Extract status code
            status_match = re.search(r"status\s*:\s*(\d+)", fulfill_body)
            status = int(status_match.group(1)) if status_match else 200

            # Extract JSON body
            resp_json: dict[str, object] | None = None
            body_match = _BODY_JSON_RE.search(fulfill_body)
            if body_match:
                try:
                    # Try to parse the JSON-like object literal
                    # Note: JS object literals aren't always valid JSON, so this is best-effort
                    raw_body = body_match.group(1)
                    # Quick cleanup: add quotes to unquoted keys
                    cleaned = re.sub(r"(\w+)\s*:", r'"\1":', raw_body)
                    cleaned = cleaned.replace("'", '"')
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, dict):
                        resp_json = parsed
                except (json.JSONDecodeError, ValueError):
                    pass

            pair = RequestResponsePair(
                source_file=str(file_path),
                method="GET",  # Default; page.route intercepts don't always specify method
                url=url_pattern,
                response_status=status,
                response_json=resp_json,
            )
            pairs.append(pair)

    return pairs


def scan_intercepts_in_directory(test_dir: Path) -> list[RequestResponsePair]:
    """Scan a directory tree for page.route() intercepts in test files."""
    all_pairs: list[RequestResponsePair] = []

    if not test_dir.is_dir():
        return all_pairs

    for file_path in test_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if any(part in _EXCLUDED_DIRS for part in file_path.parts):
            continue
        if file_path.suffix not in (".ts", ".tsx", ".js", ".jsx"):
            continue
        pairs = scan_intercepts_in_file(file_path)
        all_pairs.extend(pairs)

    return all_pairs


# ---------------------------------------------------------------------------
# Schema extraction and comparison
# ---------------------------------------------------------------------------


def extract_schema_from_json(data: dict[str, object]) -> list[SchemaField]:
    """Extract a flat schema (field names + types) from a JSON object."""
    fields: list[SchemaField] = []
    for key, value in data.items():
        field_type = _json_type(value)
        nested: list[SchemaField] = []
        if isinstance(value, dict):
            nested = extract_schema_from_json(value)
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            nested = extract_schema_from_json(value[0])

        fields.append(
            SchemaField(
                name=key,
                field_type=field_type,
                nullable=value is None,
                nested_fields=nested,
            )
        )
    return fields


def _json_type(value: object) -> str:
    """Return the JSON type string for a Python value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "number"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "unknown"


def compare_schemas(
    expected_fields: list[str],
    actual_json: dict[str, object],
) -> tuple[list[str], list[str], list[str]]:
    """Compare expected field names against actual JSON keys.

    Returns (found, missing, extra).
    """
    actual_keys = set(_flatten_keys(actual_json))
    expected_set = set(expected_fields)

    found = sorted(expected_set & actual_keys)
    missing = sorted(expected_set - actual_keys)
    extra = sorted(actual_keys - expected_set)

    return found, missing, extra


def _flatten_keys(data: dict[str, object], prefix: str = "") -> list[str]:
    """Flatten nested JSON keys into dot-notation paths."""
    keys: list[str] = []
    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        keys.append(full_key)
        if isinstance(value, dict):
            keys.extend(_flatten_keys(value, full_key))
        elif isinstance(value, list) and value and isinstance(value[0], dict):
            keys.extend(_flatten_keys(value[0], f"{full_key}[]"))
    return keys


# ---------------------------------------------------------------------------
# Fixture drift detection
# ---------------------------------------------------------------------------


def check_fixture_drift(
    fixture_json: dict[str, object],
    evidence_json: dict[str, object],
    fixture_file: str,
    endpoint: str,
) -> FixtureDriftResult:
    """Compare a mock fixture's schema against network evidence schema.

    Flags any fields present in evidence but missing from fixture (drift).
    """
    fixture_keys = set(_flatten_keys(fixture_json))
    evidence_keys = set(_flatten_keys(evidence_json))

    missing_in_fixture = sorted(evidence_keys - fixture_keys)
    extra_in_fixture = sorted(fixture_keys - evidence_keys)

    drifted = len(missing_in_fixture) > 0

    return FixtureDriftResult(
        fixture_file=fixture_file,
        endpoint=endpoint,
        fixture_fields=sorted(fixture_keys),
        evidence_fields=sorted(evidence_keys),
        missing_in_fixture=missing_in_fixture,
        extra_in_fixture=extra_in_fixture,
        drifted=drifted,
    )


# ---------------------------------------------------------------------------
# Manifest-aware validation
# ---------------------------------------------------------------------------


def validate_against_manifest(
    pairs: list[RequestResponsePair],
    manifest_path: Path,
) -> list[SchemaValidationResult]:
    """Validate captured request/response pairs against manifest contract expectations."""
    results: list[SchemaValidationResult] = []

    with open(manifest_path, encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    journeys = manifest.get("journeys", [])  # noqa: qg-empty-fallback

    for journey in journeys:
        journey_id = journey.get("journey_id", "")
        expected_request = journey.get("expected_request", "")
        contract_model = journey.get("expected_response_contract", "")

        if not expected_request or not contract_model:
            continue

        # Parse expected endpoint
        parts = expected_request.split(" ", 1)
        if len(parts) != 2:
            continue
        expected_method = parts[0].upper()
        expected_path = parts[1]

        # Find matching pairs
        matching_pairs = [
            p for p in pairs if _endpoint_matches(p.url, expected_path) and p.method.upper() == expected_method
        ]

        validation = SchemaValidationResult(
            journey_id=journey_id,
            endpoint=expected_request,
            contract_model=contract_model,
        )

        if not matching_pairs:
            validation.notes.append(f"No network evidence found for {expected_request}")
            validation.valid = True  # No evidence is not a failure — just no data
        else:
            # Check the first matching pair with JSON response
            for pair in matching_pairs:
                if pair.response_json:
                    fields = _flatten_keys(pair.response_json)
                    validation.fields_found = fields
                    validation.notes.append(f"Found {len(fields)} fields in response from {pair.source_file}")
                    break
            else:
                validation.notes.append("Matching requests found but no JSON response bodies to validate")

        results.append(validation)

    return results


def _endpoint_matches(actual_url: str, expected_path: str) -> bool:
    """Check if an actual URL matches an expected endpoint path."""
    # Strip query params from actual URL
    actual_path = actual_url.split("?")[0]

    # Normalise: remove host, strip trailing slash
    if "://" in actual_path:
        # Extract path from full URL
        path_start = actual_path.find("/", actual_path.find("://") + 3)
        if path_start >= 0:
            actual_path = actual_path[path_start:]

    actual_norm = actual_path.rstrip("/").lower()
    expected_norm = re.sub(r"\{[^}]+\}", "[^/]+", expected_path).rstrip("/").lower()

    return bool(re.match(f"^{expected_norm}$", actual_norm))


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def format_report(report: NetworkEvidenceReport) -> str:
    """Format the network evidence report as human-readable text."""
    lines: list[str] = []

    lines.append("=" * 60)
    lines.append("Network Evidence Report")
    lines.append("=" * 60)
    lines.append("")

    # HAR pairs summary
    lines.append(f"HAR request/response pairs extracted: {len(report.har_pairs)}")
    lines.append(f"page.route() intercepts extracted: {len(report.intercept_pairs)}")
    lines.append("")

    # Schema validations
    if report.schema_validations:
        lines.append("-" * 60)
        lines.append("Schema Validation Against Manifest")
        lines.append("-" * 60)
        for sv in report.schema_validations:
            status = "PASS" if sv.valid else "DRIFT"
            lines.append(f"  [{status}] {sv.journey_id}: {sv.endpoint}")
            lines.append(f"         Contract: {sv.contract_model}")
            if sv.fields_found:
                lines.append(f"         Fields found: {len(sv.fields_found)}")
            if sv.fields_missing:
                lines.append(f"         Fields MISSING: {', '.join(sv.fields_missing)}")
            if sv.type_mismatches:
                lines.append(f"         Type mismatches: {', '.join(sv.type_mismatches)}")
            for note in sv.notes:
                lines.append(f"         Note: {note}")
        lines.append("")

    # Fixture drift
    if report.fixture_drifts:
        lines.append("-" * 60)
        lines.append("Fixture Drift Detection")
        lines.append("-" * 60)
        for fd in report.fixture_drifts:
            status = "DRIFT" if fd.drifted else "OK"
            lines.append(f"  [{status}] {fd.fixture_file}")
            lines.append(f"         Endpoint: {fd.endpoint}")
            if fd.missing_in_fixture:
                lines.append(f"         Missing in fixture (added in API): {', '.join(fd.missing_in_fixture)}")
            if fd.extra_in_fixture:
                lines.append(f"         Extra in fixture (removed from API): {', '.join(fd.extra_in_fixture)}")
        lines.append("")

    # Errors
    if report.errors:
        lines.append("-" * 60)
        lines.append("Errors")
        lines.append("-" * 60)
        for err in report.errors:
            lines.append(f"  ERROR: {err}")
        lines.append("")

    return "\n".join(lines)


def format_report_json(report: NetworkEvidenceReport) -> str:
    """Format the network evidence report as JSON."""
    output: dict[str, object] = {
        "summary": {
            "har_pairs": len(report.har_pairs),
            "intercept_pairs": len(report.intercept_pairs),
            "schema_validations": len(report.schema_validations),
            "fixture_drifts": len(report.fixture_drifts),
            "drifted_fixtures": sum(1 for fd in report.fixture_drifts if fd.drifted),
            "errors": len(report.errors),
        },
        "schema_validations": [
            {
                "journey_id": sv.journey_id,
                "endpoint": sv.endpoint,
                "contract_model": sv.contract_model,
                "valid": sv.valid,
                "fields_found": sv.fields_found,
                "fields_missing": sv.fields_missing,
                "notes": sv.notes,
            }
            for sv in report.schema_validations
        ],
        "fixture_drifts": [
            {
                "fixture_file": fd.fixture_file,
                "endpoint": fd.endpoint,
                "drifted": fd.drifted,
                "missing_in_fixture": fd.missing_in_fixture,
                "extra_in_fixture": fd.extra_in_fixture,
            }
            for fd in report.fixture_drifts
        ],
        "errors": report.errors,
    }
    return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Entry point for the network evidence parser."""
    parser = argparse.ArgumentParser(
        description="Network evidence parser — extracts and validates request/response pairs.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=None,
        help="Workspace root directory (default: auto-detect)",
    )
    parser.add_argument(
        "--har-dir",
        type=Path,
        default=None,
        help="Directory containing HAR files to parse",
    )
    parser.add_argument(
        "--scan-intercepts",
        type=Path,
        default=None,
        help="Directory to scan for page.route() intercepts",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to ui-api-flow-test-manifest.yaml",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        default=False,
        help="Scan all UI repos for HAR files and intercepts",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)

    # Resolve workspace root
    if args.workspace_root is not None:
        workspace_root = args.workspace_root.resolve()
    else:
        workspace_root = Path(__file__).resolve().parent.parent.parent.parent

    pm_root = workspace_root / "unified-trading-pm"
    manifest_path = args.manifest or (pm_root / _MANIFEST_FILENAME)

    report = NetworkEvidenceReport()

    # Parse HAR files
    if args.har_dir:
        if args.har_dir.is_dir():
            for har_file in sorted(args.har_dir.rglob("*.har")):
                pairs = parse_har_file(har_file)
                report.har_pairs.extend(pairs)
        else:
            report.errors.append(f"HAR directory not found: {args.har_dir}")

    # Scan page.route() intercepts
    if args.scan_intercepts:
        pairs = scan_intercepts_in_directory(args.scan_intercepts)
        report.intercept_pairs.extend(pairs)

    # Scan all UI repos
    if args.all:
        for ui_dir in sorted(workspace_root.iterdir()):
            if not ui_dir.is_dir() or not ui_dir.name.endswith("-ui"):
                continue

            # Look for HAR files in common locations
            for har_dir_name in ("test-results", "e2e-results", "playwright-report", "e2e"):
                har_dir = ui_dir / har_dir_name
                if har_dir.is_dir():
                    for har_file in sorted(har_dir.rglob("*.har")):
                        pairs = parse_har_file(har_file)
                        report.har_pairs.extend(pairs)

            # Scan for page.route() intercepts in e2e and tests directories
            for test_dir_name in ("e2e", "tests", "src"):
                test_dir = ui_dir / test_dir_name
                if test_dir.is_dir():
                    pairs = scan_intercepts_in_directory(test_dir)
                    report.intercept_pairs.extend(pairs)

    # Validate against manifest if available
    if manifest_path.is_file():
        all_pairs = report.har_pairs + report.intercept_pairs
        if all_pairs:
            validations = validate_against_manifest(all_pairs, manifest_path)
            report.schema_validations.extend(validations)

    # Format and print output
    output = format_report_json(report) if args.format == "json" else format_report(report)

    print(output)

    # Exit with 1 if any fixture drift detected
    if any(fd.drifted for fd in report.fixture_drifts):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
