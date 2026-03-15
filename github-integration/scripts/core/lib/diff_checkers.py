"""Diff checkers: find gaps between codex and codebase."""
# SCHEMA_PROVENANCE_EXEMPT — PM-internal tooling model, not a domain schema

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import cast


@dataclass
class DriftGap:
    """Represents a gap between codex and codebase."""

    gap_id: str  # Unique identifier
    gap_type: str  # missing_implementation | wrong_implementation | standards_violation | etc.
    category: str  # coding_standards | architecture | observability | data | domain
    service: str  # Target service/repo
    title: str  # Human-readable title
    description: str  # Detailed description
    priority: str  # P0-critical | P1-high | P2-medium | P3-low
    codex_reference: str  # Path to codex section
    affected_files: list[str]  # Files that need changes
    auto_fixable: bool  # Can agent auto-fix this?


def _check_bare_except(content: str, relative_path: str, service_name: str, py_file: Path) -> DriftGap | None:
    if not re.search(r"except\s*:", content):
        return None
    return DriftGap(
        gap_id=f"COD-BARE-{service_name}-{py_file.stem}",
        gap_type="standards_violation",
        category="coding_standards",
        service=service_name,
        title=f"Bare except clause in {relative_path}",
        description=(
            "File contains bare `except:` clause which violates coding standards. "
            "Should use `@handle_api_errors` decorator or specific exception types."
        ),
        priority="P2-medium",
        codex_reference="06-coding-standards/README.md#error-handling",
        affected_files=[str(relative_path)],
        auto_fixable=False,
    )


def _check_os_getenv(content: str, relative_path: str, service_name: str, py_file: Path) -> DriftGap | None:
    if not re.search(r"os\.getenv\s*\(", content):
        return None
    return DriftGap(
        gap_id=f"COD-GETENV-{service_name}-{py_file.stem}",
        gap_type="standards_violation",
        category="coding_standards",
        service=service_name,
        title=f"os.getenv() usage in {relative_path}",
        description=(
            "File uses os.getenv() which violates coding standards. Should extend UnifiedCloudServicesConfig instead."
        ),
        priority="P2-medium",
        codex_reference="06-coding-standards/README.md#configuration",
        affected_files=[str(relative_path)],
        auto_fixable=False,
    )


def _check_datetime_utc(content: str, relative_path: str, service_name: str, py_file: Path) -> DriftGap | None:
    if not (re.search(r"datetime\.now\(\)", content) and "timezone.utc" not in content):
        return None
    return DriftGap(
        gap_id=f"COD-UTC-{service_name}-{py_file.stem}",
        gap_type="standards_violation",
        category="coding_standards",
        service=service_name,
        title=f"datetime.now() without UTC in {relative_path}",
        description=("File uses datetime.now() without timezone.utc. Should use datetime.now(timezone.utc)."),
        priority="P1-high",
        codex_reference="06-coding-standards/README.md#utc",
        affected_files=[str(relative_path)],
        auto_fixable=True,
    )


def _check_imports_inside_function(
    lines: list[str], relative_path: str, service_name: str, py_file: Path
) -> list[DriftGap]:
    gaps: list[DriftGap] = []
    for i, line in enumerate(lines):
        if re.match(r"^\s+import\s+", line) or re.match(r"^\s+from\s+.+\s+import\s+", line):
            for j in range(max(0, i - 20), i):
                if re.match(r"^\s+def\s+", lines[j]) or re.match(r"^\s+async\s+def\s+", lines[j]):
                    gaps.append(
                        DriftGap(
                            gap_id=f"COD-IMPORT-{service_name}-{py_file.stem}-{i}",
                            gap_type="standards_violation",
                            category="coding_standards",
                            service=service_name,
                            title=f"Import inside function in {relative_path}:{i}",
                            description=(
                                f"Import statement found inside function at line {i}. "
                                f"All imports should be at top of file."
                            ),
                            priority="P3-low",
                            codex_reference="06-coding-standards/README.md#imports",
                            affected_files=[str(relative_path)],
                            auto_fixable=True,
                        )
                    )
                    break
    return gaps


def _check_print(content: str, relative_path: str, service_name: str, py_file: Path) -> DriftGap | None:
    if not (re.search(r"\bprint\s*\(", content) and "/tests/" not in str(relative_path)):
        return None
    return DriftGap(
        gap_id=f"COD-PRINT-{service_name}-{py_file.stem}",
        gap_type="standards_violation",
        category="coding_standards",
        service=service_name,
        title=f"Print statement in {relative_path}",
        description=("File contains print() statement. Should use logger.info() instead."),
        priority="P3-low",
        codex_reference="06-coding-standards/README.md",
        affected_files=[str(relative_path)],
        auto_fixable=True,
    )


def _check_requests_async(content: str, relative_path: str, service_name: str, py_file: Path) -> DriftGap | None:
    if not (re.search(r"import\s+requests", content) and re.search(r"async\s+def", content)):
        return None
    return DriftGap(
        gap_id=f"COD-REQUESTS-{service_name}-{py_file.stem}",
        gap_type="standards_violation",
        category="coding_standards",
        service=service_name,
        title=f"Using requests in async code in {relative_path}",
        description=(
            "File imports requests library and has async functions. Should use aiohttp for async HTTP operations."
        ),
        priority="P2-medium",
        codex_reference="06-coding-standards/PERFORMANCE_STANDARDS.md#async-http",
        affected_files=[str(relative_path)],
        auto_fixable=False,
    )


def _check_asyncio_run(content: str, relative_path: str, service_name: str, py_file: Path) -> DriftGap | None:
    if not re.search(r"for\s+.+:\s*\n\s*asyncio\.run\(", content):
        return None
    return DriftGap(
        gap_id=f"COD-ASYNCRUN-{service_name}-{py_file.stem}",
        gap_type="standards_violation",
        category="coding_standards",
        service=service_name,
        title=f"asyncio.run() in loop in {relative_path}",
        description=(
            "File contains asyncio.run() inside a loop, which "
            "creates a new event loop each iteration. "
            "Should use asyncio.gather() or run event loop once."
        ),
        priority="P1-high",
        codex_reference="06-coding-standards/PERFORMANCE_STANDARDS.md#async-http",
        affected_files=[str(relative_path)],
        auto_fixable=False,
    )


def _check_time_sleep_async(lines: list[str], relative_path: str, service_name: str, py_file: Path) -> list[DriftGap]:
    gaps: list[DriftGap] = []
    for i, line in enumerate(lines):
        if re.search(r"time\.sleep\(", line):
            for j in range(max(0, i - 30), i):
                if re.match(r"^\s*async\s+def\s+", lines[j]):
                    gaps.append(
                        DriftGap(
                            gap_id=f"COD-TIMESLEEP-{service_name}-{py_file.stem}-{i}",
                            gap_type="standards_violation",
                            category="coding_standards",
                            service=service_name,
                            title=f"time.sleep() in async function in {relative_path}:{i}",
                            description=(
                                "time.sleep() blocks the event loop. Should use await asyncio.sleep() instead."
                            ),
                            priority="P2-medium",
                            codex_reference="06-coding-standards/PERFORMANCE_STANDARDS.md#async-http",
                            affected_files=[str(relative_path)],
                            auto_fixable=True,
                        )
                    )
                    break
    return gaps


def _check_py_file_violations(py_file: Path, workspace_root: Path, service_name: str) -> list[DriftGap]:
    """Run all coding standards checks on a single Python file."""
    gaps: list[DriftGap] = []
    content = py_file.read_text()
    lines = content.split("\n")
    relative_path = py_file.relative_to(workspace_root)

    for g in [
        _check_bare_except(content, relative_path, service_name, py_file),
        _check_os_getenv(content, relative_path, service_name, py_file),
        _check_datetime_utc(content, relative_path, service_name, py_file),
        _check_print(content, relative_path, service_name, py_file),
        _check_requests_async(content, relative_path, service_name, py_file),
        _check_asyncio_run(content, relative_path, service_name, py_file),
    ]:
        if g:
            gaps.append(g)

    gaps.extend(_check_imports_inside_function(lines, relative_path, service_name, py_file))
    gaps.extend(_check_time_sleep_async(lines, relative_path, service_name, py_file))
    return gaps


def find_coding_standards_violations(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """
    Check for coding standards violations.

    Checks from 06-coding-standards/:
    - Bare except clauses
    - os.getenv() usage
    - datetime.now() without UTC
    - Imports inside functions
    - Print statements instead of logger
    - Files >1500 lines
    """
    gaps: list[DriftGap] = []
    service_dirs = [
        d
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "pyproject.toml").exists()
        and d.name not in {"unified-trading-services", "unified-trading-codex", "mr_report"}
    ]

    for service_dir in service_dirs:
        service_name = service_dir.name
        python_files = list(service_dir.rglob("*.py"))

        for py_file in python_files:
            if (
                "__pycache__" in str(py_file)
                or ".venv" in str(py_file)
                or "/tests/" in str(py_file)
                or "/scripts/" in str(py_file)
            ):
                continue

            try:
                gaps.extend(_check_py_file_violations(py_file, workspace_root, service_name))
            except (OSError, ValueError) as e:
                print(f"Warning: Could not check {py_file}: {e}", file=sys.stderr)
                continue

    return gaps


def find_event_logging_gaps(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """
    Check for missing 3-tier event logging.

    From 03-observability/lifecycle-events.md:
    - Missing log_event("STARTED")
    - Missing log_event("STOPPED" or "FAILED")
    - Missing test_event_logging.py
    """
    gaps: list[DriftGap] = []
    service_dirs = [
        d
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "pyproject.toml").exists()
        and d.name not in {"unified-trading-services", "unified-trading-codex", "mr_report"}
    ]

    for service_dir in service_dirs:
        service_name = service_dir.name

        # Check for test_event_logging.py
        test_event_logging = service_dir / "tests" / "unit" / "test_event_logging.py"
        if not test_event_logging.exists():
            gaps.append(
                DriftGap(
                    gap_id=f"OBS-EVENT-TEST-{service_name}",
                    gap_type="missing_implementation",
                    category="observability",
                    service=service_name,
                    title=f"Missing test_event_logging.py in {service_name}",
                    description=(
                        "Service lacks tests/unit/test_event_logging.py. "
                        "All services MUST test 3-tier event logging (STARTED, STOPPED/FAILED)."
                    ),
                    priority="P1-high",
                    codex_reference="03-observability/lifecycle-events.md",
                    affected_files=["tests/unit/test_event_logging.py"],
                    auto_fixable=False,  # Requires understanding service lifecycle
                )
            )

        # Check main.py for log_event usage
        main_py = service_dir / f"{service_name.replace('-', '_')}" / "main.py"
        if not main_py.exists():
            main_py = service_dir / "main.py"

        if main_py.exists():
            content = main_py.read_text()
            has_started = "log_event(" in content and "STARTED" in content
            has_stopped = "log_event(" in content and ("STOPPED" in content or "FAILED" in content)

            if not has_started:
                gaps.append(
                    DriftGap(
                        gap_id=f"OBS-EVENT-START-{service_name}",
                        gap_type="missing_implementation",
                        category="observability",
                        service=service_name,
                        title=f"Missing log_event('STARTED') in {service_name}/main.py",
                        description=(
                            "Main entry point lacks log_event('STARTED'). "
                            "All services MUST log STARTED event at beginning of execution."
                        ),
                        priority="P1-high",
                        codex_reference="03-observability/lifecycle-events.md",
                        affected_files=[str(main_py.relative_to(workspace_root))],
                        auto_fixable=True,  # Can add boilerplate
                    )
                )

            if not has_stopped:
                gaps.append(
                    DriftGap(
                        gap_id=f"OBS-EVENT-STOP-{service_name}",
                        gap_type="missing_implementation",
                        category="observability",
                        service=service_name,
                        title=f"Missing log_event('STOPPED'/'FAILED') in {service_name}/main.py",
                        description=(
                            "Main entry point lacks log_event('STOPPED' or 'FAILED'). "
                            "All services MUST log completion event at end of execution."
                        ),
                        priority="P1-high",
                        codex_reference="03-observability/lifecycle-events.md",
                        affected_files=[str(main_py.relative_to(workspace_root))],
                        auto_fixable=True,  # Can add boilerplate
                    )
                )

    return gaps


def find_domain_event_gaps(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """
    Check for missing or incomplete domain-specific event enforcement.

    From 03-observability/[batch|live]/per-service/*.md:
    - Missing SERVICE_SPECIFIC_EVENTS population in test_event_logging.py
    - SERVICE_SPECIFIC_EVENTS doesn't match codex documentation
    """
    gaps: list[DriftGap] = []

    # Map services to their codex per-service docs
    service_to_doc: dict[str, Path] = {}
    for mode in ["batch", "live"]:
        per_service_dir = codex_root / "03-observability" / mode / "per-service"
        if per_service_dir.exists():
            for doc in per_service_dir.glob("*.md"):
                service_name = doc.stem
                service_to_doc[service_name] = doc

    service_dirs = [
        d
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "pyproject.toml").exists()
        and d.name not in {"unified-trading-services", "unified-trading-codex", "mr_report"}
    ]

    for service_dir in service_dirs:
        service_name = service_dir.name

        # Check if service has a codex per-service doc
        if service_name not in service_to_doc:
            continue  # No domain events documented yet

        codex_doc = service_to_doc[service_name]

        # Extract expected events from codex doc
        expected_events = extract_domain_events_from_codex(codex_doc)

        if not expected_events:
            continue  # No domain events defined in codex

        # Check if test_event_logging.py exists
        test_file = service_dir / "tests" / "unit" / "test_event_logging.py"
        if not test_file.exists():
            # Already caught by OBS-EVENT-TEST check
            continue

        # Check if SERVICE_SPECIFIC_EVENTS is populated
        content = test_file.read_text()

        # Check 1: Is SERVICE_SPECIFIC_EVENTS populated for this service?
        if f'"{service_name}":' not in content and f"'{service_name}':" not in content:
            gaps.append(
                DriftGap(
                    gap_id=f"OBS-EVENT-DOMAIN-{service_name}",
                    gap_type="missing_implementation",
                    category="observability",
                    service=service_name,
                    title=f"SERVICE_SPECIFIC_EVENTS not populated in {service_name}",
                    description=(
                        f"test_event_logging.py lacks SERVICE_SPECIFIC_EVENTS for {service_name}. "
                        f"Domain events are documented in {codex_doc.relative_to(codex_root)} "
                        f"but not enforced in tests."
                    ),
                    priority="P2-medium",
                    codex_reference=str(codex_doc.relative_to(codex_root)),
                    affected_files=["tests/unit/test_event_logging.py"],
                    auto_fixable=True,  # Can copy from codex
                )
            )
            continue

        # Check 2: Are the events complete compared to codex?
        actual_events = extract_service_specific_events_from_test(content, service_name)
        missing_events = expected_events - actual_events

        if missing_events:
            gaps.append(
                DriftGap(
                    gap_id=f"OBS-EVENT-INCOMPLETE-{service_name}",
                    gap_type="incomplete_implementation",
                    category="observability",
                    service=service_name,
                    title=f"Incomplete SERVICE_SPECIFIC_EVENTS in {service_name}",
                    description=(
                        f"SERVICE_SPECIFIC_EVENTS missing {len(missing_events)} events: "
                        f"{', '.join(sorted(missing_events))}. "
                        f"See {codex_doc.relative_to(codex_root)} for complete list."
                    ),
                    priority="P2-medium",
                    codex_reference=str(codex_doc.relative_to(codex_root)),
                    affected_files=["tests/unit/test_event_logging.py"],
                    auto_fixable=True,
                )
            )

    return gaps


def extract_domain_events_from_codex(codex_doc: Path) -> set[str]:
    """Parse domain events from codex per-service markdown."""
    content = codex_doc.read_text()
    events: set[str] = set()

    # Find the "Domain-Specific Events" table
    in_table = False
    for line in content.split("\n"):
        if "## Domain-Specific Events" in line or "## Additional Events" in line:
            in_table = True
            continue
        if in_table:
            if line.startswith("##"):  # Next section
                break
            # Match table rows with event names (| EVENT_NAME | ...)
            match = re.match(r"\|\s*`?([A-Z_]+)`?\s*\|", line)
            if match:
                event = match.group(1)
                # Filter out table headers
                if event not in {"Event", "EVENT"}:
                    events.add(event)

    return events


def extract_service_specific_events_from_test(content: str, service_name: str) -> set[str]:
    """Extract events from SERVICE_SPECIFIC_EVENTS dict in test file."""
    events: set[str] = set()

    # Find the service's entry in SERVICE_SPECIFIC_EVENTS dict
    pattern = rf'"{service_name}":\s*\[(.*?)\]'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        pattern = rf"'{service_name}':\s*\[(.*?)\]"
        match = re.search(pattern, content, re.DOTALL)

    if match:
        events_str = match.group(1)
        # Extract all quoted strings
        event_matches: list[str] = cast(list[str], re.findall(r'["\']([A-Z_]+)["\']', events_str))
        events = set(event_matches)

    return events


def find_architecture_gaps(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """
    Check for architecture violations.

    From 04-architecture/:
    - Missing batch-live symmetry (--mode flag)
    - Wrong concurrency patterns (MAX_WORKERS)
    """
    gaps: list[DriftGap] = []
    service_dirs = [
        d
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "pyproject.toml").exists()
        and d.name
        not in {
            "unified-trading-services",
            "unified-trading-codex",
            "unified-trading-deployment-v2",
        }
    ]

    for service_dir in service_dirs:
        service_name = service_dir.name

        # Check for --mode batch|live support in main.py
        main_py = service_dir / f"{service_name.replace('-', '_')}" / "main.py"
        if not main_py.exists():
            main_py = service_dir / "main.py"

        if main_py.exists():
            content = main_py.read_text()

            # Check for mode flag
            has_mode_flag = "--mode" in content or "mode=" in content
            if not has_mode_flag and service_name not in {
                "unified-trading-services",
                "alerting-service",
                "disaster-recovery-service",
            }:
                gaps.append(
                    DriftGap(
                        gap_id=f"ARCH-MODE-{service_name}",
                        gap_type="missing_implementation",
                        category="architecture",
                        service=service_name,
                        title=f"Missing --mode batch|live support in {service_name}",
                        description=(
                            "Service lacks --mode flag for batch-live symmetry. "
                            "Services should support both batch and live modes per architecture standards."
                        ),
                        priority="P2-medium",
                        codex_reference="04-architecture/batch-live-symmetry.md",
                        affected_files=[str(main_py.relative_to(workspace_root))],
                        auto_fixable=False,  # Requires architecture refactor
                    )
                )

            # Check for MAX_WORKERS configuration
            has_max_workers = "MAX_WORKERS" in content or "max_workers" in content
            if not has_max_workers:
                gaps.append(
                    DriftGap(
                        gap_id=f"ARCH-WORKERS-{service_name}",
                        gap_type="missing_implementation",
                        category="architecture",
                        service=service_name,
                        title=f"Missing MAX_WORKERS configuration in {service_name}",
                        description=(
                            "Service lacks MAX_WORKERS concurrency configuration. "
                            "Should have configurable parallelism per concurrency standards."
                        ),
                        priority="P3-low",
                        codex_reference="04-architecture/concurrency.md",
                        affected_files=[str(main_py.relative_to(workspace_root))],
                        auto_fixable=False,  # Requires understanding workload
                    )
                )

    return gaps


def find_validator_violations(workspace_root: Path) -> list[DriftGap]:
    """
    Run PM validators (manifest, checklist, plan links) and convert failures to DriftGaps.
    Phase 7: Refactor diff-checker to use validators.
    """
    gaps: list[DriftGap] = []
    workspace_root = workspace_root.resolve()
    pm_root = workspace_root / "unified-trading-pm"
    validators_dir = pm_root / "scripts" / "validators"
    if not validators_dir.exists():
        return gaps

    validator_checks = [
        ("validate_workspace_manifest.py", "workspace-manifest.json", "plans_to_deployable Phase 1"),
        ("validate_checklist_phase9.py", "checklist phase_9", "plans_to_deployable checklist-enhancements"),
        ("validate_plan_links.py", "plans/active links", "plans_to_deployable Phase 0b"),
    ]
    for script_name, title, codex_ref in validator_checks:
        script = validators_dir / script_name
        if not script.exists():
            continue
        args_list = [sys.executable, str(script)]
        if script_name == "validate_checklist_phase9.py":
            configs = workspace_root / "deployment-service" / "configs"
            if configs.is_dir():
                args_list.extend(["--configs", str(configs)])
        elif script_name == "validate_plan_links.py":
            args_list.extend(["--workspace-root", str(workspace_root)])
        result = subprocess.run(
            args_list,
            cwd=str(pm_root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            gaps.append(
                DriftGap(
                    gap_id=f"VALIDATOR-{script_name}",
                    gap_type="standards_violation",
                    category="data",
                    service="unified-trading-pm",
                    title=f"Validator failed: {title}",
                    description=result.stderr or result.stdout or "Validator exited non-zero",
                    priority="P1-high",
                    codex_reference=codex_ref,
                    affected_files=[str(script)],
                    auto_fixable=False,
                )
            )
    return gaps
