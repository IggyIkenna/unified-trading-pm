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
from pathlib import Path
from typing import Dict, List, Optional

import yaml

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
# Color Logging
# ==============================================================================


class Colors:
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"  # No Color


def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}[⚠]{Colors.NC} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")


# ==============================================================================
# Service Registry Parsing
# ==============================================================================


def load_service_registry() -> List[Dict]:
    """Load and parse service-registry.yaml."""
    if not SERVICE_REGISTRY.exists():
        log_error(f"Service registry not found: {SERVICE_REGISTRY}")
        sys.exit(1)

    with open(SERVICE_REGISTRY, "r") as f:
        data = yaml.safe_load(f)

    services = data.get("services", [])
    log_info(f"Loaded {len(services)} services from registry")
    return services


def filter_services_by_priority(services: List[Dict], priority: str) -> List[Dict]:
    """Filter services by priority (P0, P1, P2, P3)."""
    allowed = PRIORITY_GROUPS.get(priority, [])
    if not allowed:
        log_error(f"Invalid priority: {priority}. Must be P0, P1, P2, or P3")
        sys.exit(1)

    filtered = [s for s in services if s.get("priority") in allowed]
    log_info(f"Filtered to {len(filtered)} {priority} services")
    return filtered


def get_service_by_name(services: List[Dict], name: str) -> Optional[Dict]:
    """Get single service by name."""
    for service in services:
        if service.get("service") == name:
            return service
    return None


# ==============================================================================
# Spec File Generation
# ==============================================================================


def generate_domain_spec(service: Dict) -> str:
    """Generate domain specification content."""
    service_name = service["service"]
    service_type = service["type"]

    # Determine batch/live modes
    data_coverage = service.get("data_coverage", {})
    batch_mode = data_coverage.get("batch_mode", False)
    live_mode = data_coverage.get("live_mode", False)

    # Domain coverage
    domain_coverage = service.get("domain_coverage", {})
    venues = domain_coverage.get("venues", [])
    asset_classes = domain_coverage.get("asset_classes", [])

    # Pipeline-specific metadata
    pipeline_metadata = service.get("pipeline_metadata", {})
    upstream_deps = pipeline_metadata.get("upstream_dependencies", [])

    content = f"""# Domain Specification: {service_name}

<!-- AUTO-GENERATED BASELINE - NEEDS MANUAL REVIEW -->

## Service Overview

**Service Name:** `{service_name}`
**Service Type:** `{service_type}`
**Priority:** `{service.get("priority", "N/A")}`
**Milestone:** `{service.get("milestone", "N/A")}`

## Operational Modes

**Batch Mode:** {"✅ Supported" if batch_mode else "❌ Not Supported"}
**Live Mode:** {"✅ Supported" if live_mode else "❌ Not Supported"}

## Domain Coverage

### Venues
{chr(10).join([f"- {venue}" for venue in venues]) if venues else "- N/A"}

### Asset Classes
{chr(10).join([f"- {ac}" for ac in asset_classes]) if asset_classes else "- N/A"}

## Dependencies

### Upstream Dependencies
{chr(10).join([f"- `{dep}`" for dep in upstream_deps]) if upstream_deps else "- None"}

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

**Last Updated:** {service.get("last_updated", "TBD")}
**Review Status:** 🔴 Needs Review (Auto-Generated Baseline)
"""
    return content


def generate_data_spec(service: Dict) -> str:
    """Generate data specification content."""
    service_name = service["service"]

    # Data coverage
    data_coverage = service.get("data_coverage", {})
    start_date = data_coverage.get("start_date", "N/A")
    end_date = data_coverage.get("end_date", "Ongoing")

    # Pipeline metadata
    pipeline_metadata = service.get("pipeline_metadata", {})
    output_bucket = pipeline_metadata.get("output_bucket", "N/A")

    content = f"""# Data Specification: {service_name}

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

**Last Updated:** {service.get("last_updated", "TBD")}
**Review Status:** 🔴 Needs Review (Auto-Generated Baseline)
"""
    return content


def generate_observability_spec(service: Dict) -> str:
    """Generate observability specification content."""
    service_name = service["service"]

    content = f"""# Observability Specification: {service_name}

<!-- AUTO-GENERATED BASELINE - NEEDS MANUAL REVIEW -->

## Lifecycle Events

### Required Events (All Services)

All services MUST implement these 11 lifecycle events:

1. **STARTED** - Service initialization began
2. **INGESTING_DATA** - Data ingestion started
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
- [ ] INGESTING_DATA implemented
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
setup_service(service_name="{service_name}", mode="batch", sink=GCSEventSink(...))
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

**Last Updated:** {service.get("last_updated", "TBD")}
**Review Status:** 🔴 Needs Review (Auto-Generated Baseline)
"""
    return content


def generate_architecture_spec(service: Dict) -> str:
    """Generate architecture specification content."""
    service_name = service["service"]
    service_type = service["type"]

    # Data coverage for batch/live modes
    data_coverage = service.get("data_coverage", {})
    batch_mode = data_coverage.get("batch_mode", False)
    live_mode = data_coverage.get("live_mode", False)

    content = f"""# Architecture Specification: {service_name}

<!-- AUTO-GENERATED BASELINE - NEEDS MANUAL REVIEW -->

## Service Type

**Type:** `{service_type}`

## Operational Modes

**Batch Mode:** {"✅ Supported" if batch_mode else "❌ Not Supported"}
**Live Mode:** {"✅ Supported" if live_mode else "❌ Not Supported"}

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

**Last Updated:** {service.get("last_updated", "TBD")}
**Review Status:** 🔴 Needs Review (Auto-Generated Baseline)
"""
    return content


def generate_infrastructure_spec(service: Dict) -> str:
    """Generate infrastructure specification content."""
    service_name = service["service"]

    # Infrastructure metadata
    infrastructure = service.get("infrastructure", {})
    has_ui = infrastructure.get("has_ui", False)
    config_paths = infrastructure.get("config_paths", [])
    credentials = infrastructure.get("credentials", [])
    deployment = infrastructure.get("deployment", {})

    # Readiness
    readiness = service.get("readiness", {})
    test_coverage = readiness.get("test_coverage", 0)
    test_coverage_target = readiness.get("test_coverage_target", 80)
    cloud_compat = readiness.get("cloud_compatibility", [])

    content = f"""# Infrastructure Specification: {service_name}

<!-- AUTO-GENERATED BASELINE - NEEDS MANUAL REVIEW -->

## Deployment

### Configuration

**Config Paths:**
{chr(10).join([f"- `{path}`" for path in config_paths]) if config_paths else "- None"}

**Required Credentials:**
{chr(10).join([f"- {cred}" for cred in credentials]) if credentials else "- None"}

### Deployment Type

**GitHub Token Required:** {"✅ Yes" if deployment.get("github_token_required", False) else "❌ No"}
**Cloud Build Auth:** `{deployment.get("cloud_build_auth", "N/A")}`

### UI Component

**Has UI:** {"✅ Yes" if has_ui else "❌ No"}
{"**UI Path:** `" + infrastructure.get("ui_path", "N/A") + "`" if has_ui else ""}

## Cloud Compatibility

**Supported Clouds:**
{chr(10).join([f"- {cloud}" for cloud in cloud_compat]) if cloud_compat else "- N/A"}

## Quality Metrics

### Test Coverage

**Current:** {test_coverage}%
**Target:** {test_coverage_target}%
**Status:** {"✅ Meets Target" if test_coverage >= test_coverage_target else f"🔴 Gap: {test_coverage_target - test_coverage}%"}

### Coding Standards

**Compliance:** {"✅ Compliant" if readiness.get("coding_standards_compliant", False) else "🔴 Non-Compliant"}

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

**Last Updated:** {service.get("last_updated", "TBD")}
**Review Status:** 🔴 Needs Review (Auto-Generated Baseline)
"""
    return content


# Map spec types to generator functions
SPEC_GENERATORS = {
    "domain": generate_domain_spec,
    "data": generate_data_spec,
    "observability": generate_observability_spec,
    "architecture": generate_architecture_spec,
    "infrastructure": generate_infrastructure_spec,
}


def generate_spec_file(service: Dict, spec_type: str, dry_run: bool = False) -> bool:
    """
    Generate a single spec file for a service.

    Returns:
        True if file was created, False if skipped (already exists)
    """
    service_name = service["service"]

    # Determine directory (batch vs live)
    data_coverage = service.get("data_coverage", {})
    batch_mode = data_coverage.get("batch_mode", False)
    live_mode = data_coverage.get("live_mode", False)

    # Use batch if both, otherwise use the supported mode
    mode = "batch" if batch_mode else "live" if live_mode else "batch"

    # Build file path
    spec_dir = SPEC_DIR_MAP[spec_type]
    file_dir = CODEX_ROOT / spec_dir / mode / "per-service"
    file_path = file_dir / f"{service_name}.md"

    # Check if file already exists (idempotent)
    if file_path.exists():
        log_warning(f"Skipping {spec_type} (exists): {file_path.relative_to(CODEX_ROOT)}")
        return False

    # Generate content
    generator = SPEC_GENERATORS[spec_type]
    content = generator(service)

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


def generate_all_specs_for_service(service: Dict, dry_run: bool = False) -> Dict[str, int]:
    """
    Generate all 5 spec files for a service.

    Returns:
        Dict with counts: {"created": N, "skipped": N}
    """
    service_name = service["service"]
    log_info(f"\n{'=' * 70}")
    log_info(f"Service: {service_name}")
    log_info(f"Type: {service.get('type')}, Priority: {service.get('priority')}")
    log_info(f"{'=' * 70}\n")

    created = 0
    skipped = 0

    for spec_type in SPEC_TYPES:
        if generate_spec_file(service, spec_type, dry_run):
            created += 1
        else:
            skipped += 1

    return {"created": created, "skipped": skipped}


# ==============================================================================
# Main CLI
# ==============================================================================


def main():
    parser = argparse.ArgumentParser(
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

    args = parser.parse_args()

    # Validate arguments
    if not (args.service or args.all_services or args.priority):
        parser.error("Must specify --service, --all-services, or --priority")

    # Load services
    all_services = load_service_registry()

    # Filter services
    if args.service:
        service = get_service_by_name(all_services, args.service)
        if not service:
            log_error(f"Service not found: {args.service}")
            sys.exit(1)
        services = [service]
    elif args.priority:
        services = filter_services_by_priority(all_services, args.priority)
    else:  # --all-services
        services = all_services

    # Generate specs
    log_info(f"\n{'=' * 70}")
    log_info(f"Generating specs for {len(services)} services")
    if args.dry_run:
        log_warning("DRY-RUN MODE: No files will be created")
    log_info(f"{'=' * 70}\n")

    total_created = 0
    total_skipped = 0

    for service in services:
        stats = generate_all_specs_for_service(service, args.dry_run)
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
