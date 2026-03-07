#!/usr/bin/env python3
"""
Generate Per-Service Specification Files

This script generates 5 specification files per service (160 total for 32 services):
  - Domain spec
  - Data spec
  - Observability spec
  - Architecture spec
  - Infrastructure spec

Features:
  - Reads service-registry.yaml for canonical service list
  - Uses templates from 10-audit/_service-*.yaml for structure
  - Prefills with service metadata (type, repos, dependencies, asset classes)
  - Idempotent (skips existing files, never overwrites manual work)
  - Supports dry-run mode
  - Supports priority filtering (P0, P1, P2)

Usage:
    # Generate all 160 files
    python3 generate-per-service-specs.py --all-services --dry-run
    python3 generate-per-service-specs.py --all-services

    # Generate for specific service
    python3 generate-per-service-specs.py --service instruments-service

    # Generate by priority
    python3 generate-per-service-specs.py --priority P0
    python3 generate-per-service-specs.py --priority P1
"""

import argparse
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

import yaml
from spec_logging import log_error, log_info, log_success, log_warning

JsonDict = dict[str, object]

# ==============================================================================
# Constants
# ==============================================================================

CODEX_ROOT = Path(__file__).resolve().parents[4]  # Up 4 levels to codex root
SERVICE_REGISTRY = CODEX_ROOT / "11-project-management" / "service-registry.yaml"
AUDIT_DIR = CODEX_ROOT / "10-audit"

SPEC_TYPES = ["domain", "data", "observability", "architecture", "infrastructure"]

# Map spec types to codex directories
SPEC_DIR_MAP = {
    "domain": "01-domain",
    "data": "02-data",
    "observability": "03-observability",
    "architecture": "04-architecture",
    "infrastructure": "05-infrastructure",
}

# Priority groups
PRIORITY_GROUPS = {
    "P0": ["P0-critical"],
    "P1": ["P1-high"],
    "P2": ["P2-medium"],
    "P3": ["P3-low"],
}


# ==============================================================================
# Service Registry Parsing
# ==============================================================================


def load_service_registry() -> list[JsonDict]:
    """Load and parse service-registry.yaml."""
    if not SERVICE_REGISTRY.exists():
        log_error(f"Service registry not found: {SERVICE_REGISTRY}")
        sys.exit(1)

    with open(SERVICE_REGISTRY, "r") as f:
        raw: object = cast(object, yaml.safe_load(f))

    if not isinstance(raw, dict):
        log_error("Service registry is not a valid YAML mapping")
        sys.exit(1)

    data: JsonDict = cast(JsonDict, raw)
    raw_services: object = data.get("services") or []
    services: list[JsonDict] = []
    if isinstance(raw_services, list):
        services = [cast(JsonDict, s) for s in cast(list[object], raw_services) if isinstance(s, dict)]
    log_info(f"Loaded {len(services)} services from registry")
    return services


def filter_services_by_priority(services: list[JsonDict], priority: str) -> list[JsonDict]:
    """Filter services by priority (P0, P1, P2, P3)."""
    allowed: list[str] = PRIORITY_GROUPS.get(priority, [])
    if not allowed:
        log_error(f"Invalid priority: {priority}. Must be P0, P1, P2, or P3")
        sys.exit(1)

    filtered: list[JsonDict] = [s for s in services if s.get("priority") in allowed]
    log_info(f"Filtered to {len(filtered)} {priority} services")
    return filtered


def get_service_by_name(services: list[JsonDict], name: str) -> JsonDict | None:
    """Get single service by name."""
    for service in services:
        if service.get("service") == name:
            return service
    return None


# ==============================================================================
# Safe Accessor Helpers
# ==============================================================================


def _get_str(d: JsonDict, key: str, default: str = "N/A") -> str:
    """Safely get a string value from a JsonDict."""
    val: object = d.get(key, default)
    return str(val) if val is not None else default


def _get_bool(d: JsonDict, key: str, default: bool = False) -> bool:
    """Safely get a boolean value from a JsonDict."""
    val: object = d.get(key, default)
    return bool(val)


def _get_dict(d: JsonDict, key: str) -> JsonDict:
    """Safely get a nested dict from a JsonDict."""
    val: object = d.get(key, {})
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return {}


def _get_str_list(d: JsonDict, key: str) -> list[str]:
    """Safely get a list of strings from a JsonDict."""
    val: object = d.get(key, [])
    if isinstance(val, list):
        return [str(item) for item in cast(list[object], val)]
    return []


def _get_int(d: JsonDict, key: str, default: int = 0) -> int:
    """Safely get an integer value from a JsonDict."""
    val: object = d.get(key, default)
    if isinstance(val, int):
        return val
    return default


# ==============================================================================
# Spec File Generation
# ==============================================================================


def _extract_domain_metadata(service: JsonDict) -> dict[str, str | list[str]]:
    """Extract metadata for domain spec generation."""
    data_coverage: JsonDict = _get_dict(service, "data_coverage")
    domain_coverage: JsonDict = _get_dict(service, "domain_coverage")
    pipeline_metadata: JsonDict = _get_dict(service, "pipeline_metadata")
    venues: list[str] = _get_str_list(domain_coverage, "venues")
    asset_classes: list[str] = _get_str_list(domain_coverage, "asset_classes")
    upstream_deps: list[str] = _get_str_list(pipeline_metadata, "upstream_dependencies")

    batch_status: str = "Supported" if _get_bool(data_coverage, "batch_mode") else "Not Supported"
    live_status: str = "Supported" if _get_bool(data_coverage, "live_mode") else "Not Supported"
    venues_str: str = chr(10).join([f"- {v}" for v in venues]) if venues else "- N/A"
    ac_str: str = chr(10).join([f"- {ac}" for ac in asset_classes]) if asset_classes else "- N/A"
    deps_str: str = chr(10).join([f"- `{d}`" for d in upstream_deps]) if upstream_deps else "- None"

    return {
        "service_name": _get_str(service, "service"),
        "service_type": _get_str(service, "type"),
        "priority": _get_str(service, "priority"),
        "milestone": _get_str(service, "milestone"),
        "last_updated": _get_str(service, "last_updated", "TBD"),
        "batch_status": batch_status,
        "live_status": live_status,
        "venues_str": venues_str,
        "ac_str": ac_str,
        "deps_str": deps_str,
    }


def _build_domain_content(m: dict[str, str | list[str]]) -> str:
    """Build domain spec content from extracted metadata."""
    return f"""# Domain Specification: {m["service_name"]}

<!-- AUTO-GENERATED BASELINE - NEEDS MANUAL REVIEW -->

## Service Overview

**Service Name:** `{m["service_name"]}`
**Service Type:** `{m["service_type"]}`
**Priority:** `{m["priority"]}`
**Milestone:** `{m["milestone"]}`

## Operational Modes

**Batch Mode:** {m["batch_status"]}
**Live Mode:** {m["live_status"]}

## Domain Coverage

### Venues
{m["venues_str"]}

### Asset Classes
{m["ac_str"]}

## Dependencies

### Upstream Dependencies
{m["deps_str"]}

## Business Logic (TODO: Manual Review Required)

<!-- Add service-specific business logic here -->

### Key Features
- [ ] Feature 1 (to be documented)
- [ ] Feature 2 (to be documented)
- [ ] Feature 3 (to be documented)

### Domain Rules
- [ ] Rule 1 (to be documented)
- [ ] Rule 2 (to be documented)

### Edge Cases
- [ ] Edge case 1 (to be documented)
- [ ] Edge case 2 (to be documented)

## Domain Events (TODO: Manual Review Required)

<!-- Document domain-specific events and their triggers -->

### Event Types
- [ ] Event type 1 (to be documented)
- [ ] Event type 2 (to be documented)

## Validation Rules (TODO: Manual Review Required)

<!-- Document input validation, business rule validation -->

### Input Validation
- [ ] Validation rule 1 (to be documented)

### Business Rule Validation
- [ ] Business rule 1 (to be documented)

## Codex References

- [Domain Model](../../01-domain/README.md)
- [Asset Classes](../../01-domain/asset-classes.md)
- [Venues](../../01-domain/venues.md)

---

**Last Updated:** {m["last_updated"]}
**Review Status:** Needs Review (Auto-Generated Baseline)
"""


def generate_domain_spec(service: JsonDict) -> str:
    """Generate domain specification content."""
    return _build_domain_content(_extract_domain_metadata(service))


def generate_data_spec(service: JsonDict) -> str:
    """Generate data specification content."""
    service_name: str = _get_str(service, "service")

    # Data coverage
    data_coverage: JsonDict = _get_dict(service, "data_coverage")
    start_date: str = _get_str(data_coverage, "start_date")
    end_date: str = _get_str(data_coverage, "end_date", "Ongoing")

    # Pipeline metadata
    pipeline_metadata: JsonDict = _get_dict(service, "pipeline_metadata")
    output_bucket: str = _get_str(pipeline_metadata, "output_bucket")

    last_updated: str = _get_str(service, "last_updated", "TBD")

    content: str = f"""# Data Specification: {service_name}

<!-- AUTO-GENERATED BASELINE - NEEDS MANUAL REVIEW -->

## Data I/O

### Input Data Sources (TODO: Manual Review Required)

**Source 1:**
- Type: (GCS, BigQuery, API, WebSocket, etc.)
- Location: TBD
- Format: TBD
- Schema: TBD

### Output Data Sinks

**Primary Output:**
- Type: GCS
- Location: `{output_bucket}`
- Format: Parquet (or specify)
- Partitioning: (date, venue, asset_class - TBD)

## Schema Definitions (TODO: Manual Review Required)

### Input Schema

```python
# TODO: Document input schema here
# Example:
# {{
#     "field1": "type",
#     "field2": "type"
# }}
```

### Output Schema

```python
# TODO: Document output schema here
# Refer to: schemas/output_schemas.py (if exists)
```

## Data Quality (TODO: Manual Review Required)

### Validation Rules
- [ ] Rule 1: Timestamp/date alignment (validate_timestamp_date_alignment)
- [ ] Rule 2: Required fields present
- [ ] Rule 3: Data types correct

### Quality Metrics
- [ ] Completeness: % of expected data received
- [ ] Accuracy: % of records passing validation
- [ ] Timeliness: Latency from source to sink

## Data Retention (TODO: Manual Review Required)

- **Hot Storage:** TBD days/months
- **Cold Storage:** TBD days/months/years
- **Archival:** TBD

## Historical Data Coverage

**Start Date:** `{start_date}`
**End Date:** `{end_date}`

## Codex References

- [Schema Governance](../../02-data/schema-governance.md)
- [Data Partitioning](../../02-data/partitioning-strategy.md)
- [Pre-Upload Validation](../../02-data/pre-upload-validation.md)

---

**Last Updated:** {last_updated}
**Review Status:** Needs Review (Auto-Generated Baseline)
"""
    return content


def _extract_observability_metadata(service: JsonDict) -> dict[str, str]:
    """Extract metadata for observability spec generation."""
    return {
        "service_name": _get_str(service, "service"),
        "last_updated": _get_str(service, "last_updated", "TBD"),
    }


def _build_observability_content(m: dict[str, str]) -> str:
    """Build observability spec content from extracted metadata."""
    return f"""# Observability Specification: {m["service_name"]}

<!-- AUTO-GENERATED BASELINE - NEEDS MANUAL REVIEW -->

## Lifecycle Events

### Required Events (All Services)

All services MUST implement these 11 lifecycle events:

1. **STARTED** - Service initialization began
2. **DATA_INGESTION_STARTED** - Data ingestion started
3. **PROCESSING_DATA** - Data processing started
4. **SAVING_DATA** - Data save operation started
5. **DATA_SAVED** - Data save operation completed
6. **COMPLETED** - Service execution completed successfully
7. **STOPPED** - Service stopped gracefully
8. **FAILED** - Service execution failed (with error details)
9. **VALIDATION_ERROR** - Data validation failed
10. **NO_DATA_FOUND** - No data found for processing
11. **SKIPPED** - Processing skipped (with reason)

### Implementation Status (TODO: Manual Review Required)

- [ ] STARTED implemented
- [ ] DATA_INGESTION_STARTED implemented
- [ ] PROCESSING_DATA implemented
- [ ] SAVING_DATA implemented
- [ ] DATA_SAVED implemented
- [ ] COMPLETED implemented
- [ ] STOPPED implemented
- [ ] FAILED implemented
- [ ] VALIDATION_ERROR implemented
- [ ] NO_DATA_FOUND implemented
- [ ] SKIPPED implemented

### Event Logging Tests

- [ ] `tests/unit/test_event_logging.py` exists
- [ ] All 11 events have test coverage
- [ ] Event sequence validated

## Resource Monitoring

### CPU, Memory, Disk Monitoring

```python
# Use unified_events_interface for lifecycle event logging
from unified_trading_services import setup_service, GCSEventSink
setup_service(service_name="{m["service_name"]}", mode="batch", sink=GCSEventSink(...))
```

**Thresholds:**
- CPU: 85% warning, 90% shutdown
- Memory: 85% warning, 90% shutdown
- Disk: 80% warning, 90% shutdown

### Implementation Status (TODO: Manual Review Required)

- [ ] PerformanceMonitor enabled
- [ ] Thresholds configured
- [ ] Adaptive concurrency implemented (reduces workers at 85% RAM)

## Alerting (TODO: Manual Review Required)

### Critical Alerts
- [ ] Alert 1: TBD
- [ ] Alert 2: TBD

### Warning Alerts
- [ ] Alert 1: TBD
- [ ] Alert 2: TBD

## Metrics (TODO: Manual Review Required)

### Business Metrics
- [ ] Metric 1: TBD
- [ ] Metric 2: TBD

### Technical Metrics
- [ ] Latency (p50, p95, p99)
- [ ] Throughput (records/sec)
- [ ] Error rate (%)

## Codex References

- [Lifecycle Events](../../03-observability/lifecycle-events.md)
- [Resource Monitoring](../../03-observability/resource-events.md)
- [Event Logging Tests](../../06-coding-standards/testing.md)

---

**Last Updated:** {m["last_updated"]}
**Review Status:** Needs Review (Auto-Generated Baseline)
"""


def generate_observability_spec(service: JsonDict) -> str:
    """Generate observability specification content."""
    return _build_observability_content(_extract_observability_metadata(service))


def generate_architecture_spec(service: JsonDict) -> str:
    """Generate architecture specification content."""
    service_name: str = _get_str(service, "service")
    service_type: str = _get_str(service, "type")

    # Data coverage for batch/live modes
    data_coverage: JsonDict = _get_dict(service, "data_coverage")
    batch_mode: bool = _get_bool(data_coverage, "batch_mode")
    live_mode: bool = _get_bool(data_coverage, "live_mode")

    last_updated: str = _get_str(service, "last_updated", "TBD")

    batch_status: str = "Supported" if batch_mode else "Not Supported"
    live_status: str = "Supported" if live_mode else "Not Supported"

    content: str = f"""# Architecture Specification: {service_name}

<!-- AUTO-GENERATED BASELINE - NEEDS MANUAL REVIEW -->

## Service Type

**Type:** `{service_type}`

## Operational Modes

**Batch Mode:** {batch_status}
**Live Mode:** {live_status}

## Batch-Live Symmetry (TODO: Manual Review Required)

Services supporting both modes MUST maintain 90% code symmetry with only 4 seams:

1. **Data Source Seam** - Batch: GCS/BigQuery, Live: WebSocket/API
2. **Data Sink Seam** - Batch: GCS parquet, Live: Pub/Sub/in-memory
3. **Persistence Seam** - Batch: per-date, Live: continuous thread
4. **Trigger Seam** - Batch: date loop, Live: event stream

### Implementation Status
- [ ] Data source seam implemented
- [ ] Data sink seam implemented
- [ ] Persistence seam implemented
- [ ] Trigger seam implemented
- [ ] Engine is mode-agnostic (no mode checks in core logic)

## Concurrency Model (TODO: Manual Review Required)

### Batch Mode Concurrency
- **Parallelization:** Per-date (or per-instrument, per-venue)
- **MAX_WORKERS:** TBD (I/O-bound=16, CPU-bound=1-3)
- **Adaptive:** Reduces workers at 85% RAM, shuts down at 90%

### Live Mode Concurrency
- **Parallelization:** Per-venue (one thread per WebSocket)
- **MAX_WORKERS:** Number of venues
- **Threading:** Async I/O for WebSocket connections

### Implementation Status
- [ ] MAX_WORKERS configured
- [ ] Adaptive concurrency implemented
- [ ] Thread safety verified

## Component Diagram (TODO: Manual Review Required)

```
[Input] --> [Processor] --> [Output]
   |            |              |
   v            v              v
[Validation] [Transform]  [Storage]
```

## Key Architectural Decisions (TODO: Manual Review Required)

### Decision 1: TBD
- **Context:** TBD
- **Decision:** TBD
- **Rationale:** TBD
- **Alternatives:** TBD

## Codex References

- [Batch-Live Symmetry](../../04-architecture/batch-live-symmetry.md)
- [Concurrency Model](../../04-architecture/concurrency.md)
- [Deployment Topology](../../04-architecture/deployment-topology.md)

---

**Last Updated:** {last_updated}
**Review Status:** Needs Review (Auto-Generated Baseline)
"""
    return content


def _extract_infrastructure_metadata(service: JsonDict) -> dict[str, str | int]:
    """Extract metadata for infrastructure spec generation."""
    infrastructure: JsonDict = _get_dict(service, "infrastructure")
    readiness: JsonDict = _get_dict(service, "readiness")
    deployment: JsonDict = _get_dict(infrastructure, "deployment")

    test_coverage: int = _get_int(readiness, "test_coverage", 0)
    test_coverage_target: int = _get_int(readiness, "test_coverage_target", 80)
    config_paths: list[str] = _get_str_list(infrastructure, "config_paths")
    credentials: list[str] = _get_str_list(infrastructure, "credentials")
    cloud_compat: list[str] = _get_str_list(readiness, "cloud_compatibility")

    coverage_gap: int = test_coverage_target - test_coverage
    coverage_status: str = "Meets Target" if test_coverage >= test_coverage_target else f"Gap: {coverage_gap}%"

    config_paths_str: str = chr(10).join([f"- `{p}`" for p in config_paths]) if config_paths else "- None"
    credentials_str: str = chr(10).join([f"- {c}" for c in credentials]) if credentials else "- None"
    cloud_compat_str: str = chr(10).join([f"- {cloud}" for cloud in cloud_compat]) if cloud_compat else "- N/A"

    has_ui: bool = _get_bool(infrastructure, "has_ui")
    ui_path: str = _get_str(infrastructure, "ui_path")
    ui_path_line: str = f"**UI Path:** `{ui_path}`" if has_ui else ""

    return {
        "service_name": _get_str(service, "service"),
        "last_updated": _get_str(service, "last_updated", "TBD"),
        "config_paths_str": config_paths_str,
        "credentials_str": credentials_str,
        "cloud_compat_str": cloud_compat_str,
        "github_token_str": "Yes" if _get_bool(deployment, "github_token_required") else "No",
        "cloud_build_auth": _get_str(deployment, "cloud_build_auth"),
        "has_ui_str": "Yes" if has_ui else "No",
        "ui_path_line": ui_path_line,
        "test_coverage": test_coverage,
        "test_coverage_target": test_coverage_target,
        "coverage_status": coverage_status,
        "compliance_str": "Compliant" if _get_bool(readiness, "coding_standards_compliant") else "Non-Compliant",
    }


def _build_infrastructure_content(m: dict[str, str | int]) -> str:
    """Build infrastructure spec content from extracted metadata."""
    return f"""# Infrastructure Specification: {m["service_name"]}

<!-- AUTO-GENERATED BASELINE - NEEDS MANUAL REVIEW -->

## Deployment

### Configuration

**Config Paths:**
{m["config_paths_str"]}

**Required Credentials:**
{m["credentials_str"]}

### Deployment Type

**GitHub Token Required:** {m["github_token_str"]}
**Cloud Build Auth:** `{m["cloud_build_auth"]}`

### UI Component

**Has UI:** {m["has_ui_str"]}
{m["ui_path_line"]}

## Cloud Compatibility

**Supported Clouds:**
{m["cloud_compat_str"]}

## Quality Metrics

### Test Coverage

**Current:** {m["test_coverage"]}%
**Target:** {m["test_coverage_target"]}%
**Status:** {m["coverage_status"]}

### Coding Standards

**Compliance:** {m["compliance_str"]}

## Service Structure (TODO: Manual Review Required)

### Required Files
- [ ] `config.py` (or `config/` package)
- [ ] `Dockerfile`
- [ ] `cloudbuild.yaml`
- [ ] `quality-gates.yml` (GitHub Actions)
- [ ] `pyproject.toml`
- [ ] `.env.example`
- [ ] `scripts/quickmerge.sh`
- [ ] `tests/unit/test_event_logging.py`
- [ ] `.cursorrules`

### Testing Structure
- [ ] `tests/unit/` (synthetic fixtures, 5-20 rows)
- [ ] `tests/integration/` (minimal data, <120s)
- [ ] `tests/e2e/` (single shard, <180s)
- [ ] `tests/smoke/` (--max-results 1)

## Deployment Checklist (TODO: Manual Review Required)

### Pre-Deployment
- [ ] Quality gates pass
- [ ] Config validated
- [ ] Credentials configured
- [ ] Tests pass

### Deployment
- [ ] Cloud Build triggered
- [ ] Deployment verified
- [ ] Smoke tests pass

### Post-Deployment
- [ ] Monitoring enabled
- [ ] Alerts configured
- [ ] Logs verified

## Codex References

- [Configuration Management](../../06-coding-standards/configuration-management.md)
- [Cloud-Agnostic Migration](../../05-infrastructure/cloud-agnostic-migration.md)
- [Quality Gates](../../06-coding-standards/quality-gates.md)
- [Testing Strategy](../../06-coding-standards/testing.md)

---

**Last Updated:** {m["last_updated"]}
**Review Status:** Needs Review (Auto-Generated Baseline)
"""


def generate_infrastructure_spec(service: JsonDict) -> str:
    """Generate infrastructure specification content."""
    return _build_infrastructure_content(_extract_infrastructure_metadata(service))


# Map spec types to generator functions
SPEC_GENERATORS: dict[str, Callable[[JsonDict], str]] = {
    "domain": generate_domain_spec,
    "data": generate_data_spec,
    "observability": generate_observability_spec,
    "architecture": generate_architecture_spec,
    "infrastructure": generate_infrastructure_spec,
}


def generate_spec_file(service: JsonDict, spec_type: str, dry_run: bool = False) -> bool:
    """
    Generate a single spec file for a service.

    Returns:
        True if file was created, False if skipped (already exists)
    """
    service_name: str = _get_str(service, "service")

    # Determine directory (batch vs live)
    data_coverage: JsonDict = _get_dict(service, "data_coverage")
    batch_mode: bool = _get_bool(data_coverage, "batch_mode")
    live_mode: bool = _get_bool(data_coverage, "live_mode")

    # Use batch if both, otherwise use the supported mode
    mode: str = "batch" if batch_mode else "live" if live_mode else "batch"

    # Build file path
    spec_dir: str = SPEC_DIR_MAP[spec_type]
    file_dir: Path = CODEX_ROOT / spec_dir / mode / "per-service"
    file_path: Path = file_dir / f"{service_name}.md"

    # Check if file already exists (idempotent)
    if file_path.exists():
        log_warning(f"Skipping {spec_type} (exists): {file_path.relative_to(CODEX_ROOT)}")
        return False

    # Generate content
    generator: Callable[[JsonDict], str] = SPEC_GENERATORS[spec_type]
    content: str = generator(service)

    if dry_run:
        log_info(f"[DRY-RUN] Would create {spec_type}: {file_path.relative_to(CODEX_ROOT)}")
        return False

    # Create directory if needed
    file_dir.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(file_path, "w") as f:
        f.write(content)

    log_success(f"Created {spec_type}: {file_path.relative_to(CODEX_ROOT)}")
    return True


def generate_all_specs_for_service(service: JsonDict, dry_run: bool = False) -> dict[str, int]:
    """
    Generate all 5 spec files for a service.

    Returns:
        Dict with counts: {"created": N, "skipped": N}
    """
    service_name: str = _get_str(service, "service")
    svc_type: str = _get_str(service, "type")
    svc_priority: str = _get_str(service, "priority")
    log_info(f"\n{'=' * 70}")
    log_info(f"Service: {service_name}")
    log_info(f"Type: {svc_type}, Priority: {svc_priority}")
    log_info(f"{'=' * 70}\n")

    created: int = 0
    skipped: int = 0

    for spec_type in SPEC_TYPES:
        if generate_spec_file(service, spec_type, dry_run):
            created += 1
        else:
            skipped += 1

    return {"created": created, "skipped": skipped}


# ==============================================================================
# Main CLI
# ==============================================================================


def main() -> None:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Generate per-service specification files (160 total for 32 services)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all 160 files (dry-run first)
  python3 generate-per-service-specs.py --all-services --dry-run
  python3 generate-per-service-specs.py --all-services

  # Generate for specific service
  python3 generate-per-service-specs.py --service instruments-service

  # Generate by priority
  python3 generate-per-service-specs.py --priority P0
  python3 generate-per-service-specs.py --priority P1
        """,
    )

    parser.add_argument("--service", type=str, help="Service name (e.g., instruments-service)")

    parser.add_argument("--all-services", action="store_true", help="Generate for all 32 services")

    parser.add_argument(
        "--priority", type=str, choices=["P0", "P1", "P2", "P3"], help="Filter by priority (P0, P1, P2, P3)"
    )

    parser.add_argument("--dry-run", action="store_true", help="Preview what would be created without creating files")

    parsed: argparse.Namespace = parser.parse_args()

    # Extract args with getattr to avoid Any
    service_arg: str = str(getattr(parsed, "service", "") or "")
    all_services_flag: bool = bool(getattr(parsed, "all_services", False))
    priority_arg: str = str(getattr(parsed, "priority", "") or "")
    dry_run: bool = bool(getattr(parsed, "dry_run", False))

    # Validate arguments
    if not (service_arg or all_services_flag or priority_arg):
        parser.error("Must specify --service, --all-services, or --priority")

    # Load services
    all_services: list[JsonDict] = load_service_registry()

    # Filter services
    services: list[JsonDict]
    if service_arg:
        found: JsonDict | None = get_service_by_name(all_services, service_arg)
        if not found:
            log_error(f"Service not found: {service_arg}")
            sys.exit(1)
        services = [found]
    elif priority_arg:
        services = filter_services_by_priority(all_services, priority_arg)
    else:  # --all-services
        services = all_services

    # Generate specs
    log_info(f"\n{'=' * 70}")
    log_info(f"Generating specs for {len(services)} services")
    if dry_run:
        log_warning("DRY-RUN MODE: No files will be created")
    log_info(f"{'=' * 70}\n")

    total_created: int = 0
    total_skipped: int = 0

    for svc in services:
        stats: dict[str, int] = generate_all_specs_for_service(svc, dry_run)
        total_created += stats["created"]
        total_skipped += stats["skipped"]

    # Summary
    log_info(f"\n{'=' * 70}")
    log_info("SUMMARY")
    log_info(f"{'=' * 70}")
    log_success(f"Created: {total_created} files")
    if total_skipped > 0:
        log_warning(f"Skipped: {total_skipped} files (already exist)")
    log_info(f"Total Services: {len(services)}")
    log_info(f"Total Specs: {len(services) * len(SPEC_TYPES)} ({len(SPEC_TYPES)} per service)")
    log_info(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
