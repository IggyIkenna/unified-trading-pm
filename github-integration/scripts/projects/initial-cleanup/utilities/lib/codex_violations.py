"""Codex violation checkers and GitHub issue helpers for check-codex-violations."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

JsonDict = dict[str, object]


@dataclass
class DriftGap:
    """Represents a gap between codex and codebase."""

    gap_id: str
    gap_type: str
    category: str
    service: str
    title: str
    description: str
    priority: str
    codex_reference: str
    affected_files: list[str]
    auto_fixable: bool


def _check_bare_except(
    content: str,
    service_name: str,
    py_file: Path,
    relative_path: Path,
    gaps: list[DriftGap],
) -> None:
    """Check for bare except clause."""
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
                auto_fixable=False,
            )
        )


def _check_getenv(
    content: str,
    service_name: str,
    py_file: Path,
    relative_path: Path,
    gaps: list[DriftGap],
) -> None:
    """Check for os.getenv() usage."""
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
                auto_fixable=False,
            )
        )


def _check_utc_datetime(
    content: str,
    service_name: str,
    py_file: Path,
    relative_path: Path,
    gaps: list[DriftGap],
) -> None:
    """Check for datetime.now() without UTC."""
    if re.search(r"datetime\.now\(\)", content) and "timezone.utc" not in content:
        gaps.append(
            DriftGap(
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
        )


def _check_imports_inside_function(
    lines: list[str],
    service_name: str,
    py_file: Path,
    relative_path: Path,
    gaps: list[DriftGap],
) -> None:
    """Check for imports inside functions."""
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


def _check_print(
    content: str,
    service_name: str,
    py_file: Path,
    relative_path: Path,
    gaps: list[DriftGap],
) -> None:
    """Check for print() statements."""
    if re.search(r"print\s*\(", content) and "/tests/" not in str(relative_path):
        gaps.append(
            DriftGap(
                gap_id=f"COD-PRINT-{service_name}-{py_file.stem}",
                gap_type="standards_violation",
                category="coding_standards",
                service=service_name,
                title=f"Print statement in {relative_path}",
                description="File contains print() statement. Should use logger.info() instead.",
                priority="P3-low",
                codex_reference="06-coding-standards/README.md",
                affected_files=[str(relative_path)],
                auto_fixable=True,
            )
        )


def _check_requests_async(
    content: str,
    service_name: str,
    py_file: Path,
    relative_path: Path,
    gaps: list[DriftGap],
) -> None:
    """Check for requests in async code."""
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
                auto_fixable=False,
            )
        )


def _check_asyncio_run_loop(
    content: str,
    service_name: str,
    py_file: Path,
    relative_path: Path,
    gaps: list[DriftGap],
) -> None:
    """Check for asyncio.run() inside loop."""
    if re.search(r"for\s+.+:\s*\n\s*asyncio\.run\(", content):
        gaps.append(
            DriftGap(
                gap_id=f"COD-ASYNCRUN-{service_name}-{py_file.stem}",
                gap_type="standards_violation",
                category="coding_standards",
                service=service_name,
                title=f"asyncio.run() in loop in {relative_path}",
                description=(
                    "File contains asyncio.run() inside a loop. Should use asyncio.gather() or run event loop once."
                ),
                priority="P1-high",
                codex_reference="06-coding-standards/PERFORMANCE_STANDARDS.md#async-http",
                affected_files=[str(relative_path)],
                auto_fixable=False,
            )
        )


def _check_time_sleep_async(
    lines: list[str],
    service_name: str,
    py_file: Path,
    relative_path: Path,
    gaps: list[DriftGap],
) -> None:
    """Check for time.sleep() in async functions."""
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


def find_coding_standards_violations(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """Check for coding standards violations."""
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
                content = py_file.read_text()
                lines = content.split("\n")
                relative_path = py_file.relative_to(workspace_root)

                _check_bare_except(content, service_name, py_file, relative_path, gaps)
                _check_getenv(content, service_name, py_file, relative_path, gaps)
                _check_utc_datetime(content, service_name, py_file, relative_path, gaps)
                _check_imports_inside_function(lines, service_name, py_file, relative_path, gaps)
                _check_print(content, service_name, py_file, relative_path, gaps)
                _check_requests_async(content, service_name, py_file, relative_path, gaps)
                _check_asyncio_run_loop(content, service_name, py_file, relative_path, gaps)
                _check_time_sleep_async(lines, service_name, py_file, relative_path, gaps)

            except (OSError, ValueError) as e:
                print(f"Warning: Could not check {py_file}: {e}", file=sys.stderr)
                continue

    return gaps


def find_event_logging_gaps(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """Check for missing 3-tier event logging."""
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
                    auto_fixable=False,
                )
            )

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
                        auto_fixable=True,
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
                        auto_fixable=True,
                    )
                )

    return gaps


def extract_domain_events_from_codex(codex_doc: Path) -> set[str]:
    """Parse domain events from codex per-service markdown."""
    content = codex_doc.read_text()
    events: set[str] = set()
    in_table = False
    for line in content.split("\n"):
        if "## Domain-Specific Events" in line or "## Additional Events" in line:
            in_table = True
            continue
        if in_table:
            if line.startswith("##"):
                break
            match = re.match(r"\|\s*`?([A-Z_]+)`?\s*\|", line)
            if match:
                event = match.group(1)
                if event not in {"Event", "EVENT"}:
                    events.add(event)
    return events


def extract_service_specific_events_from_test(content: str, service_name: str) -> set[str]:
    """Extract events from SERVICE_SPECIFIC_EVENTS dict in test file."""
    events: set[str] = set()
    pattern = rf'"{service_name}":\s*\[(.*?)\]'
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        pattern = rf"'{service_name}':\s*\[(.*?)\]"
        match = re.search(pattern, content, re.DOTALL)
    if match:
        events_str = match.group(1)
        event_matches: list[str] = cast(list[str], re.findall(r'["\']([A-Z_]+)["\']', events_str))
        events = set(event_matches)
    return events


def find_domain_event_gaps(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """Check for missing or incomplete domain-specific event enforcement."""
    gaps: list[DriftGap] = []
    service_to_doc: dict[str, Path] = {}
    for mode in ["batch", "live"]:
        per_service_dir = codex_root / "03-observability" / mode / "per-service"
        if per_service_dir.exists():
            for doc in per_service_dir.glob("*.md"):
                service_to_doc[doc.stem] = doc

    service_dirs = [
        d
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "pyproject.toml").exists()
        and d.name not in {"unified-trading-services", "unified-trading-codex", "mr_report"}
    ]

    for service_dir in service_dirs:
        service_name = service_dir.name
        if service_name not in service_to_doc:
            continue
        codex_doc = service_to_doc[service_name]
        expected_events = extract_domain_events_from_codex(codex_doc)
        if not expected_events:
            continue
        test_file = service_dir / "tests" / "unit" / "test_event_logging.py"
        if not test_file.exists():
            continue
        content = test_file.read_text()
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
                        f"Domain events are documented in {codex_doc.relative_to(codex_root)}."
                    ),
                    priority="P2-medium",
                    codex_reference=str(codex_doc.relative_to(codex_root)),
                    affected_files=["tests/unit/test_event_logging.py"],
                    auto_fixable=True,
                )
            )
            continue
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


def find_architecture_gaps(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """Check for architecture violations."""
    gaps: list[DriftGap] = []
    service_dirs = [
        d
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "pyproject.toml").exists()
        and d.name not in {"unified-trading-services", "unified-trading-codex", "unified-trading-deployment-v2"}
    ]

    for service_dir in service_dirs:
        service_name = service_dir.name
        main_py = service_dir / f"{service_name.replace('-', '_')}" / "main.py"
        if not main_py.exists():
            main_py = service_dir / "main.py"

        if main_py.exists():
            content = main_py.read_text()
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
                        auto_fixable=False,
                    )
                )

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
                        auto_fixable=False,
                    )
                )
    return gaps


def fetch_all_existing_issues(repo: str) -> dict[str, str]:
    """Fetch ALL open issues from repo and build gap_id index."""
    print("  Fetching all existing issues from GitHub...")
    gap_id_to_issue: dict[str, str] = {}
    try:
        result = subprocess.run(
            ["gh", "issue", "list", "--repo", repo, "--state", "open", "--limit", "1000", "--json", "number,body"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"  Warning: gh issue list failed with code {result.returncode}", file=sys.stderr)
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
        for issue in issues_list:
            body_val: str = str(issue.get("body", ""))
            match = re.search(r"gap-id:\s*(\S+)", body_val)
            if match:
                gap_id_str: str = match.group(1)
                gap_id_to_issue[gap_id_str] = str(issue.get("number", ""))
        print(f"  Found {len(gap_id_to_issue)} issues with gap-id markers")
    except (OSError, ValueError) as e:
        print(f"  Warning: Could not fetch existing issues: {e}", file=sys.stderr)
    return gap_id_to_issue


def check_for_existing_issue(gap: DriftGap, existing_issues: dict[str, str]) -> str | None:
    """Check if issue already exists by looking up gap_id in pre-loaded index."""
    return existing_issues.get(gap.gap_id)


def create_github_issue(gap: DriftGap, repo: str, dry_run: bool) -> JsonDict:
    """Create GitHub issue for this gap."""
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
    labels = ["issue", gap.priority]
    category_label_map = {
        "coding_standards": "area/coding-standards",
        "observability": "area/observability",
        "architecture": "area/architecture",
        "data": "area/data",
        "domain": "area/domain",
    }
    if gap.category in category_label_map:
        labels.append(category_label_map[gap.category])
    labels.append(f"service/{gap.service}")
    if gap.auto_fixable:
        labels.append("auto-fixable")

    if dry_run:
        return {"action": "create", "title": title, "labels": labels, "gap_id": gap.gap_id, "service": gap.service}

    try:
        cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
        for label in labels:
            cmd.extend(["--label", label])
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
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
        return {"action": "error", "error": str(raw_stderr) if raw_stderr is not None else "", "gap_id": gap.gap_id}


def ensure_labels_exist(repo: str, workspace_root: Path, dry_run: bool) -> None:
    """Create all required labels for diff checker issues."""
    if dry_run:
        return
    service_dirs = [
        d.name
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "pyproject.toml").exists()
        and d.name not in {"unified-trading-services", "unified-trading-codex", "mr_report"}
    ]
    labels_to_create = [
        ("p0-critical", "DC2626", "Critical priority"),
        ("p1-high", "F97316", "High priority"),
        ("p2-medium", "FACC15", "Medium priority"),
        ("p3-low", "4ADE80", "Low priority"),
        ("area/coding-standards", "8B5CF6", "Coding standards area"),
        ("area/observability", "3B82F6", "Observability area"),
        ("area/architecture", "06B6D4", "Architecture area"),
        ("area/data", "10B981", "Data area"),
        ("area/domain", "F59E0B", "Domain area"),
        ("auto-fixable", "22C55E", "Can be auto-fixed by agent"),
        ("issue", "6B7280", "Flat issue (not part of Epic hierarchy)"),
    ]
    for service in service_dirs:
        labels_to_create.append((f"service/{service}", "64748B", f"Service: {service}"))
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
        label_result = subprocess.run(cmd, capture_output=True, text=True)
        if label_result.returncode == 0:
            created += 1
    print(f"Ensured {len(labels_to_create)} labels exist ({created} created/updated)")


def gap_to_dict(gap: DriftGap) -> JsonDict:
    """Convert a DriftGap dataclass to a JSON-serializable dict."""
    return {
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
