#!/usr/bin/env python3
"""
Daily Diff Checker: Compare codex documentation against actual codebase.

Identifies gaps where documentation describes standards/functionality but code
doesn't match, and creates GitHub issues for remediation.

Usage:
  python run-diff-checker.py [--dry-run] [--repo OWNER/REPO] [--output-json PATH] [--max-workers N]

Performance:
  - Batch fetches existing issues (~5-10 API calls instead of 1,209)
  - Creates issues in parallel (10 workers by default)
  - Total time: ~1-2 minutes for 1,000+ issues (vs. ~20 minutes sequential)

Requires: gh CLI (https://cli.github.com/) authenticated, or GITHUB_TOKEN.
          Python 3.13+
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

# Type alias
JsonDict = dict[str, object]


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
            # Skip test files, scripts, __pycache__, .venv
            if (
                "__pycache__" in str(py_file)
                or ".venv" in str(py_file)
                or "/tests/" in str(py_file)
                or "/scripts/" in str(py_file)
            ):
                continue

            try:
                content = py_file.read_text()
                lines = content.split("\n")
                relative_path = py_file.relative_to(workspace_root)

                # Check 1: Bare except clauses
                if re.search(r"except\s*:", content):
                    gaps.append(
                        DriftGap(
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
                            auto_fixable=False,  # Requires understanding context
                        )
                    )

                # Check 2: os.getenv() usage (should use config classes)
                if re.search(r"os\.getenv\s*\(", content):
                    gaps.append(
                        DriftGap(
                            gap_id=f"COD-GETENV-{service_name}-{py_file.stem}",
                            gap_type="standards_violation",
                            category="coding_standards",
                            service=service_name,
                            title=f"os.getenv() usage in {relative_path}",
                            description=(
                                "File uses os.getenv() which violates coding standards. "
                                "Should extend UnifiedCloudServicesConfig instead."
                            ),
                            priority="P2-medium",
                            codex_reference="06-coding-standards/README.md#configuration",
                            affected_files=[str(relative_path)],
                            auto_fixable=False,  # Requires config class design
                        )
                    )

                # Check 3: datetime.now() without UTC
                if re.search(r"datetime\.now\(\)", content) and "timezone.utc" not in content:
                    gaps.append(
                        DriftGap(
                            gap_id=f"COD-UTC-{service_name}-{py_file.stem}",
                            gap_type="standards_violation",
                            category="coding_standards",
                            service=service_name,
                            title=f"datetime.now() without UTC in {relative_path}",
                            description=(
                                "File uses datetime.now() without timezone.utc. Should use datetime.now(timezone.utc)."
                            ),
                            priority="P1-high",
                            codex_reference="06-coding-standards/README.md#utc",
                            affected_files=[str(relative_path)],
                            auto_fixable=True,  # Simple find/replace
                        )
                    )

                # Check 4: Imports inside functions
                for i, line in enumerate(lines):
                    if re.match(r"^\s+import\s+", line) or re.match(r"^\s+from\s+.+\s+import\s+", line):
                        # Check if this is inside a function (crude check: indented import after def)
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
                                        auto_fixable=True,  # Can be moved to top
                                    )
                                )
                                break

                # Check 5: Print statements (should use logger)
                # Skip tests/ directory - print() in tests is acceptable for debugging
                if re.search(r"\bprint\s*\(", content) and "/tests/" not in str(relative_path):
                    gaps.append(
                        DriftGap(
                            gap_id=f"COD-PRINT-{service_name}-{py_file.stem}",
                            gap_type="standards_violation",
                            category="coding_standards",
                            service=service_name,
                            title=f"Print statement in {relative_path}",
                            description=("File contains print() statement. Should use logger.info() instead."),
                            priority="P3-low",
                            codex_reference="06-coding-standards/README.md",
                            affected_files=[str(relative_path)],
                            auto_fixable=True,  # Simple replacement
                        )
                    )

                # Check 6: Files >1500 lines
                # SKIP: COD-SIZE violations are tracked separately via check-codsize-violations.sh
                # and have dedicated COD-SIZE GitHub issues. Manifest focuses on code-level violations.
                # Uncomment if you want to include in manifest:
                # if len(lines) > 1500:
                #     gaps.append(
                #         DriftGap(
                #             gap_id=f"COD-SIZE-{service_name}-{py_file.stem}",
                #             gap_type="standards_violation",
                #             category="coding_standards",
                #             service=service_name,
                #             title=f"File >1500 lines in {relative_path} ({len(lines)} lines)",
                #             description=(
                #                 f"File has {len(lines)} lines, exceeding 1500-line guideline. "
                #                 f"Should split by Single Responsibility Principle. "
                #                 f"Note: 1500 is the maximum for centralized scripts; aim for <500 for most modules."
                #             ),
                #             priority="P3-low",
                #             codex_reference="06-coding-standards/README.md",
                #             affected_files=[str(relative_path)],
                #             auto_fixable=False,  # Requires design decisions
                #         )
                #     )

                # Check 7: requests library in async functions
                if re.search(r"import\s+requests", content) and re.search(r"async\s+def", content):
                    gaps.append(
                        DriftGap(
                            gap_id=f"COD-REQUESTS-{service_name}-{py_file.stem}",
                            gap_type="standards_violation",
                            category="coding_standards",
                            service=service_name,
                            title=f"Using requests in async code in {relative_path}",
                            description=(
                                "File imports requests library and has async functions. "
                                "Should use aiohttp for async HTTP operations."
                            ),
                            priority="P2-medium",
                            codex_reference="06-coding-standards/PERFORMANCE_STANDARDS.md#async-http",
                            affected_files=[str(relative_path)],
                            auto_fixable=False,  # Requires rewrite
                        )
                    )

                # Check 8: asyncio.run() in loops
                if re.search(r"for\s+.+:\s*\n\s*asyncio\.run\(", content):
                    gaps.append(
                        DriftGap(
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
                            auto_fixable=False,  # Requires refactor
                        )
                    )

                # Check 9: time.sleep() in async functions
                for i, line in enumerate(lines):
                    if re.search(r"time\.sleep\(", line):
                        # Check if inside async function
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
                                            "time.sleep() blocks the event loop. "
                                            "Should use await asyncio.sleep() instead."
                                        ),
                                        priority="P2-medium",
                                        codex_reference="06-coding-standards/PERFORMANCE_STANDARDS.md#async-http",
                                        affected_files=[str(relative_path)],
                                        auto_fixable=True,  # Simple replacement
                                    )
                                )
                                break

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


def fetch_all_existing_issues(repo: str) -> dict[str, str]:
    """
    Fetch ALL open issues from repo and build gap_id index.

    This is much faster than checking each gap individually:
    - Old way: ~1,209 API calls (one per gap)
    - New way: ~5-10 API calls (fetching 1000 issues at once)

    Returns dict mapping gap_id -> issue_number.
    """
    print("  Fetching all existing issues from GitHub...")
    gap_id_to_issue: dict[str, str] = {}

    try:
        # Fetch up to 1000 open issues (should cover most repos)
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--limit",
                "1000",
                "--json",
                "number,body",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print(
                f"  Warning: gh issue list failed with code {result.returncode}",
                file=sys.stderr,
            )
            return gap_id_to_issue

        if not result.stdout.strip():
            print("  No existing issues found")
            return gap_id_to_issue

        raw_issues: object = cast(object, json.loads(result.stdout))
        issues_list: list[JsonDict] = (
            [cast(JsonDict, item) for item in cast(list[object], raw_issues) if isinstance(item, dict)]
            if isinstance(raw_issues, list)
            else []
        )
        print(f"  Loaded {len(issues_list)} existing open issues")

        # Extract gap_id from each issue body
        for issue in issues_list:
            body_val: str = str(issue.get("body", ""))
            # Look for "gap-id: XXX" marker
            match = re.search(r"gap-id:\s*(\S+)", body_val)
            if match:
                gap_id_str: str = match.group(1)
                gap_id_to_issue[gap_id_str] = str(issue.get("number", ""))

        print(f"  Found {len(gap_id_to_issue)} issues with gap-id markers")

    except (OSError, ValueError) as e:
        print(f"  Warning: Could not fetch existing issues: {e}", file=sys.stderr)

    return gap_id_to_issue


def check_for_existing_issue(gap: DriftGap, existing_issues: dict[str, str]) -> str | None:
    """
    Check if issue already exists by looking up gap_id in pre-loaded index.

    Args:
        gap: The gap to check
        existing_issues: Dict mapping gap_id -> issue_number

    Returns issue number if found, None otherwise.
    """
    return existing_issues.get(gap.gap_id)


def create_github_issue(gap: DriftGap, repo: str, dry_run: bool) -> JsonDict:
    """
    Create GitHub issue for this gap.

    Returns dict with issue details.
    """
    title = f"[{gap.service}] {gap.gap_id}: {gap.title}"

    body = f"""## Gap Type: {gap.gap_type}

{gap.description}

## Details

- **Category**: {gap.category}
- **Service**: {gap.service}
- **Priority**: {gap.priority}
- **Auto-fixable**: {"Yes" if gap.auto_fixable else "No"}
- **Codex Reference**: {gap.codex_reference}

## Affected Files

{chr(10).join(f"- {f}" for f in gap.affected_files)}

## Standards Reference

See codex: `{gap.codex_reference}`

---

**Markers for Drift Checker:**
- gap-id: {gap.gap_id}
- gap-type: {gap.gap_type}
- category: {gap.category}
- auto-fixable: {gap.auto_fixable}
- detected: {datetime.now(timezone.utc).isoformat()}
"""

    # Determine labels
    labels = ["issue", gap.priority]

    # Add category label
    category_label_map = {
        "coding_standards": "area/coding-standards",
        "observability": "area/observability",
        "architecture": "area/architecture",
        "data": "area/data",
        "domain": "area/domain",
    }
    if gap.category in category_label_map:
        labels.append(category_label_map[gap.category])

    # Add service label (keep full service name for clarity)
    service_label = f"service/{gap.service}"
    labels.append(service_label)

    # Add auto-fixable label if applicable
    if gap.auto_fixable:
        labels.append("auto-fixable")

    if dry_run:
        return {
            "action": "create",
            "title": title,
            "labels": labels,
            "gap_id": gap.gap_id,
            "service": gap.service,
        }

    try:
        # Create issue using gh CLI
        cmd = [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
        ]

        for label in labels:
            cmd.extend(["--label", label])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        issue_url = result.stdout.strip()
        issue_number = issue_url.split("/")[-1] if issue_url else "unknown"

        return {
            "action": "created",
            "issue_number": issue_number,
            "issue_url": issue_url,
            "gap_id": gap.gap_id,
            "service": gap.service,
        }

    except subprocess.CalledProcessError as e:
        raw_stderr: object = getattr(e, "stderr", None)
        print(f"Error creating issue: {raw_stderr}", file=sys.stderr)
        return {
            "action": "error",
            "error": str(raw_stderr) if raw_stderr is not None else "",
            "gap_id": gap.gap_id,
        }


def ensure_labels_exist(repo: str, workspace_root: Path, dry_run: bool) -> None:
    """Create all required labels for diff checker issues."""
    if dry_run:
        return

    # Get all service names from workspace
    service_dirs = [
        d.name
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "pyproject.toml").exists()
        and d.name not in {"unified-trading-services", "unified-trading-codex", "mr_report"}
    ]

    labels_to_create = [
        # Priority labels
        ("p0-critical", "DC2626", "Critical priority"),
        ("p1-high", "F97316", "High priority"),
        ("p2-medium", "FACC15", "Medium priority"),
        ("p3-low", "4ADE80", "Low priority"),
        # Category labels
        ("area/coding-standards", "8B5CF6", "Coding standards area"),
        ("area/observability", "3B82F6", "Observability area"),
        ("area/architecture", "06B6D4", "Architecture area"),
        ("area/data", "10B981", "Data area"),
        ("area/domain", "F59E0B", "Domain area"),
        # Misc
        ("auto-fixable", "22C55E", "Can be auto-fixed by agent"),
        ("issue", "6B7280", "Flat issue (not part of Epic hierarchy)"),
    ]

    # Add service labels dynamically
    for service in service_dirs:
        labels_to_create.append((f"service/{service}", "64748B", f"Service: {service}"))

    # Create labels
    created = 0
    for label_name, color, description in labels_to_create:
        cmd = [
            "gh",
            "label",
            "create",
            label_name,
            "--repo",
            repo,
            "--color",
            color,
            "--description",
            description,
            "--force",
        ]
        label_result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if label_result.returncode == 0:
            created += 1

    print(f"Ensured {len(labels_to_create)} labels exist ({created} created/updated)")


def _gap_to_dict(gap: DriftGap) -> JsonDict:
    """Convert a DriftGap dataclass to a JSON-serializable dict."""
    gap_dict: JsonDict = {
        "gap_id": gap.gap_id,
        "title": gap.title,
        "category": gap.category,
        "priority": gap.priority,
        "gap_type": gap.gap_type,
        "description": gap.description,
        "service": gap.service,
        "affected_files": gap.affected_files,
        "codex_reference": gap.codex_reference,
        "auto_fixable": gap.auto_fixable,
    }
    return gap_dict


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


def main() -> int:

    parser = argparse.ArgumentParser(description="Daily diff checker: codex vs codebase")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating issues")
    parser.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPO", "IggyIkenna/unified-trading-deployment-v2"),
        help="Target GitHub repo (OWNER/REPO)",
    )
    parser.add_argument("--output-json", type=Path, help="Write results to JSON file")
    parser.add_argument("--codex-dir", type=Path, help="Path to unified-trading-codex")
    parser.add_argument("--workspace-dir", type=Path, help="Path to workspace root")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Max parallel workers for creating issues (default: 10)",
    )

    parsed = parser.parse_args()

    # Extract typed args
    dry_run: bool = bool(getattr(parsed, "dry_run", False))
    repo: str = str(getattr(parsed, "repo", "IggyIkenna/unified-trading-deployment-v2"))
    max_workers: int = int(getattr(parsed, "max_workers", 10))
    raw_output_json: object = getattr(parsed, "output_json", None)
    output_json: Path | None = cast(Path, raw_output_json) if isinstance(raw_output_json, Path) else None
    raw_codex_dir: object = getattr(parsed, "codex_dir", None)
    raw_workspace_dir: object = getattr(parsed, "workspace_dir", None)

    # Determine paths
    script_dir: Path = Path(__file__).parent
    codex_root: Path = cast(Path, raw_codex_dir) if isinstance(raw_codex_dir, Path) else script_dir.parent.parent
    workspace_root: Path = cast(Path, raw_workspace_dir) if isinstance(raw_workspace_dir, Path) else codex_root.parent

    if not (codex_root / "06-coding-standards").exists():
        print(f"Error: Could not find codex at {codex_root}", file=sys.stderr)
        return 1

    print(f"Codex root: {codex_root}")
    print(f"Workspace root: {workspace_root}")
    print(f"Target repo: {repo}")
    print(f"Dry run: {dry_run}")
    print()

    # Ensure all labels exist before creating issues
    print("Ensuring labels exist...")
    ensure_labels_exist(repo, workspace_root, dry_run)
    print()

    # Run checks
    print("Running diff checks...")
    all_gaps: list[DriftGap] = []

    print("  - Checking coding standards...")
    all_gaps.extend(find_coding_standards_violations(codex_root, workspace_root))

    print("  - Checking event logging...")
    all_gaps.extend(find_event_logging_gaps(codex_root, workspace_root))

    print("  - Checking domain-specific events...")
    all_gaps.extend(find_domain_event_gaps(codex_root, workspace_root))

    print("  - Checking architecture...")
    all_gaps.extend(find_architecture_gaps(codex_root, workspace_root))

    print("  - Running validators (manifest, checklist, plan links)...")
    all_gaps.extend(find_validator_violations(workspace_root))

    print(f"\nFound {len(all_gaps)} gaps")

    # Categorize and prioritize
    by_priority: dict[str, list[DriftGap]] = {}
    for gap in all_gaps:
        by_priority.setdefault(gap.priority, []).append(gap)

    for priority in ["P0-critical", "P1-high", "P2-medium", "P3-low"]:
        count: int = len(by_priority.get(priority, []))
        print(f"  {priority}: {count}")

    # Fetch all existing issues once (batched, much faster than 1,209 individual calls)
    print("\nFetching existing issues...")
    existing_issues: dict[str, str] = fetch_all_existing_issues(repo)

    # Separate gaps into two groups: existing vs new
    gaps_to_create: list[DriftGap] = []
    results: list[JsonDict] = []
    created_count: int = 0
    skipped_count: int = 0

    print("\nChecking which gaps need new issues...")
    for gap in all_gaps:
        existing_issue: str | None = check_for_existing_issue(gap, existing_issues)

        if existing_issue:
            print(f"  SKIP {gap.gap_id}: Already exists (#{existing_issue})")
            skipped_count += 1
            results.append(
                {
                    "action": "skipped",
                    "gap_id": gap.gap_id,
                    "existing_issue": existing_issue,
                }
            )
        else:
            gaps_to_create.append(gap)
            if dry_run:
                # For COD-SIZE issues, show line count from title
                if gap.gap_id.startswith("COD-SIZE-"):
                    print(f"  OK {gap.gap_id}: Would create issue (dry-run)")
                    print(f"      Title: {gap.title}")
                else:
                    print(f"  OK {gap.gap_id}: Would create issue (dry-run)")

    # Create issues in parallel (if not dry-run and we have gaps to create)
    if not dry_run and gaps_to_create:
        print(f"\nCreating {len(gaps_to_create)} issues in parallel (max {max_workers} workers)...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all issue creation tasks
            future_to_gap: dict[Future[JsonDict], DriftGap] = {
                executor.submit(create_github_issue, g, repo, False): g for g in gaps_to_create
            }

            # Process completed tasks as they finish
            for i, future in enumerate(as_completed(future_to_gap), 1):
                current_gap = future_to_gap[future]
                try:
                    issue_result: JsonDict = future.result()
                    results.append(issue_result)
                    action_val: str = str(issue_result.get("action", ""))
                    if action_val in {"create", "created"}:
                        created_count += 1
                        print(f"  OK [{i}/{len(gaps_to_create)}] {current_gap.gap_id}: Created")
                    else:
                        print(f"  WARN [{i}/{len(gaps_to_create)}] {current_gap.gap_id}: Failed")
                except (OSError, ValueError) as e:
                    print(f"  ERR [{i}/{len(gaps_to_create)}] {current_gap.gap_id}: Error - {e}")
                    results.append(
                        {
                            "action": "error",
                            "gap_id": current_gap.gap_id,
                            "error": str(e),
                        }
                    )
    elif dry_run and gaps_to_create:
        # In dry-run, just count what would be created
        created_count = len(gaps_to_create)
        for gap in gaps_to_create:
            results.append(
                {
                    "action": "create",
                    "gap_id": gap.gap_id,
                    "title": f"[{gap.service}] {gap.gap_id}: {gap.title}",
                }
            )

    print("\nSummary:")
    print(f"  Total gaps found: {len(all_gaps)}")
    if dry_run:
        print(f"  Issues that would be created: {created_count} (dry-run, not actually created)")
    else:
        print(f"  Issues created: {created_count}")
    print(f"  Issues skipped (already exist): {skipped_count}")

    # Write output JSON if requested
    if output_json is not None:
        # Convert gaps to JSON-serializable format
        serializable_gaps: list[JsonDict] = []
        for gap in all_gaps:
            gap_dict: JsonDict = _gap_to_dict(gap)
            serializable_gaps.append(gap_dict)

        output_data: JsonDict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "codex_root": str(codex_root),
            "workspace_root": str(workspace_root),
            "target_repo": repo,
            "dry_run": dry_run,
            "total_gaps": len(all_gaps),
            "gaps_by_priority": {k: len(v) for k, v in by_priority.items()},
            "created_count": created_count,
            "skipped_count": skipped_count,
            "results": results,
            "gaps": serializable_gaps,
        }
        output_json.write_text(json.dumps(output_data, indent=2))
        print(f"\nResults written to {output_json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
