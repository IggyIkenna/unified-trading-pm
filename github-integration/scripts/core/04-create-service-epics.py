#!/usr/bin/env python3
"""
Create Service-Level Epics with Task/Subtask Hierarchy
=======================================================

**New Structure:** One Epic per Service

Epic: instruments-service
|- Task: Batch Mode Checklist Items (Priority 3b)
|  |- Subtask: DATA-04 (Sports support)
|  +- Subtask: BASELINE-01 (Config)
|- Task: Live Mode Implementation (Priority 3a - NEW, nothing exists)
|  |- Subtask: WebSocket client
|  |- Subtask: Real-time processing
|  +- Subtask: Observability
+- Task: Testing & Infrastructure

**Key Principles:**
- Service doesn't exist -> Full Epic/Task/Subtask (Repo, Core, Live, Testing)
- Service exists, batch mode -> Checklist items as subtasks
- Service exists, live mode -> Full Live implementation (nothing exists yet)
- Rich labels: mode/batch, mode/live, domain/sports, type/ui, etc.

Usage:
  # Dry run (preview)
  python3 create-service-epics.py --all-services --dry-run

  # Create epics
  python3 create-service-epics.py --all-services

  # Single service
  python3 create-service-epics.py --service instruments-service
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from typing import cast

from lib.epic_loaders import (
    WORKSPACE_ROOT,
    get_template_for_service,
    load_codex_templates,
    load_deployment_checklist,
    load_service_registry,
)
from lib.epic_models import Epic, Subtask, Task

# ============================================================================
# Config
# ============================================================================


ORG = "IggyIkenna"
REPO = "unified-trading-codex"  # All issues in codex repo
PROJECT_NUMBER = 1  # "Codex Delta Wave 1 - Unified Board"

# Type aliases
ServiceDict = dict[str, object]
RegistryDict = dict[str, object]
TemplateDict = dict[str, object]
ChecklistDict = dict[str, object]


# ============================================================================


def _build_repo_scaffolding_task(service_name: str) -> Task:
    """Build Repo Scaffolding task."""
    return Task(
        title="Repo Scaffolding",
        description="Set up repository structure and base configuration",
        priority="P1-high",
        mode=None,
        subtasks=[
            Subtask(
                title="Create repository",
                description=f"Create {service_name} repo in IggyIkenna org",
                complexity="LOW",
                priority="P1-high",
                hours=1.0,
            ),
            Subtask(
                title="Add pyproject.toml",
                description="Add dependency management with pinned versions",
                complexity="LOW",
                priority="P1-high",
                hours=1.5,
                codex_refs=["06-coding-standards/dependency-management.md"],
            ),
            Subtask(
                title="Add Dockerfile",
                description="Add multi-stage Dockerfile with UCS base image",
                complexity="MEDIUM",
                priority="P1-high",
                hours=2.0,
                codex_refs=["05-infrastructure/docker-standards.md"],
            ),
            Subtask(
                title="Add CI/CD configs",
                description=("Add cloudbuild.yaml, quality-gates.yml, quickmerge.sh"),
                complexity="MEDIUM",
                priority="P1-high",
                hours=2.5,
                codex_refs=["06-coding-standards/ci-cd.md"],
            ),
            Subtask(
                title="Add .cursorrules",
                description="Add per-repo .cursorrules referencing codex",
                complexity="LOW",
                priority="P2-medium",
                hours=1.0,
                codex_refs=["06-coding-standards/cursor-rules-system.md"],
            ),
        ],
    )


def _build_batch_mode_task(service_name: str) -> Task:
    """Build Batch Mode Implementation task."""
    return Task(
        title="Batch Mode Implementation",
        description="Core batch processing logic",
        priority="P1-high",
        mode="batch",
        subtasks=[
            Subtask(
                title="Implement main entry point",
                description="Add CLI with batch mode support",
                complexity="MEDIUM",
                priority="P1-high",
                hours=4.0,
                codex_refs=["04-architecture/batch-live-symmetry.md"],
            ),
            Subtask(
                title="Add configuration class",
                description="Extend UnifiedCloudServicesConfig",
                complexity="MEDIUM",
                priority="P1-high",
                hours=3.0,
                codex_refs=["06-coding-standards/README.md#configuration"],
            ),
            Subtask(
                title="Implement core processing logic",
                description=(f"Service-specific logic for {service_name}"),
                complexity="HIGH",
                priority="P0-critical",
                hours=16.0,
            ),
            Subtask(
                title="Add GCS data I/O",
                description=("Read from input buckets, write to output buckets"),
                complexity="MEDIUM",
                priority="P1-high",
                hours=6.0,
                codex_refs=["02-data/gcs-structure.md"],
            ),
            Subtask(
                title="Add data status tracking",
                description=("Implement manifest files for coverage tracking"),
                complexity="MEDIUM",
                priority="P2-medium",
                hours=4.0,
                codex_refs=["02-data/data-status-tracking.md"],
            ),
        ],
    )


def _build_live_mode_task_missing() -> Task:
    """Build Live Mode Implementation task (service does not exist)."""
    return Task(
        title="Live Mode Implementation",
        description="Real-time processing (NEW - nothing exists yet)",
        priority="P0-critical",
        mode="live",
        subtasks=[
            Subtask(
                title="Implement WebSocket client",
                description="Connect to venue WebSocket streams",
                complexity="HIGH",
                priority="P0-critical",
                hours=8.0,
                codex_refs=["04-architecture/live-market-data-architecture.md"],
            ),
            Subtask(
                title="Add real-time processing logic",
                description="Process live data with <100ms latency",
                complexity="HIGH",
                priority="P0-critical",
                hours=12.0,
            ),
            Subtask(
                title="Add Redis Streams fanout",
                description="Pub/Sub for downstream consumers",
                complexity="MEDIUM",
                priority="P1-high",
                hours=6.0,
                codex_refs=["04-architecture/live-market-data-architecture.md"],
            ),
            Subtask(
                title="Add reconnection logic",
                description=("Handle disconnects with exponential backoff"),
                complexity="MEDIUM",
                priority="P1-high",
                hours=4.0,
            ),
        ],
    )


def _build_observability_task() -> Task:
    """Build Observability task."""
    return Task(
        title="Observability",
        description="Lifecycle events, metrics, alerts",
        priority="P1-high",
        mode=None,
        subtasks=[
            Subtask(
                title="Add lifecycle events",
                description=("STARTED, INGESTING, PROCESSING, COMPLETED, FAILED"),
                complexity="MEDIUM",
                priority="P1-high",
                hours=3.0,
                codex_refs=["03-observability/lifecycle-events.md"],
            ),
            Subtask(
                title="Add metrics",
                description=("Counter, Gauge, Histogram for service-specific metrics"),
                complexity="MEDIUM",
                priority="P1-high",
                hours=4.0,
                codex_refs=["03-observability/metrics-catalog.md"],
            ),
            Subtask(
                title="Add alerts",
                description="Cloud Monitoring alert policies",
                complexity="LOW",
                priority="P2-medium",
                hours=2.0,
            ),
            Subtask(
                title="Add test_event_logging.py",
                description="Unit tests for lifecycle events",
                complexity="LOW",
                priority="P1-high",
                hours=2.0,
            ),
        ],
    )


def _build_testing_task() -> Task:
    """Build Testing task."""
    return Task(
        title="Testing",
        description="Unit, integration, E2E tests",
        priority="P1-high",
        mode=None,
        subtasks=[
            Subtask(
                title="Unit tests",
                description=">80% coverage for core logic",
                complexity="MEDIUM",
                priority="P1-high",
                hours=12.0,
                codex_refs=["06-coding-standards/testing.md"],
            ),
            Subtask(
                title="Integration tests",
                description="Test with mock GCS, API responses",
                complexity="MEDIUM",
                priority="P2-medium",
                hours=8.0,
            ),
            Subtask(
                title="E2E smoke test",
                description="End-to-end with --max-results 1",
                complexity="LOW",
                priority="P2-medium",
                hours=4.0,
            ),
        ],
    )


def _build_live_mode_task_existing() -> Task:
    """Build Live Mode Implementation task (service exists, batch done)."""
    return Task(
        title="Live Mode Implementation",
        description=("Real-time processing (NEW - nothing exists yet)"),
        priority="P0-critical",
        mode="live",
        subtasks=[
            Subtask(
                title="Implement WebSocket client",
                description="Connect to venue WebSocket streams",
                complexity="HIGH",
                priority="P0-critical",
                hours=8.0,
            ),
            Subtask(
                title="Add real-time processing logic",
                description="Process live data with <100ms latency",
                complexity="HIGH",
                priority="P0-critical",
                hours=12.0,
            ),
        ],
    )


def generate_epic_for_missing_service(service: ServiceDict) -> Epic:
    """Generate Epic/Task/Subtask for a service that doesn't exist."""
    service_name = str(service.get("service", ""))
    tasks: list[Task] = []

    tasks.append(_build_repo_scaffolding_task(service_name))

    raw_data_coverage = service.get("data_coverage") or {}
    data_coverage: dict[str, object] = (
        cast(dict[str, object], raw_data_coverage) if isinstance(raw_data_coverage, dict) else {}
    )
    has_batch = bool(data_coverage.get("batch_mode", True))
    if has_batch:
        tasks.append(_build_batch_mode_task(service_name))

    has_live = bool(data_coverage.get("live_mode", False))
    if has_live:
        tasks.append(_build_live_mode_task_missing())

    tasks.append(_build_observability_task())
    tasks.append(_build_testing_task())

    return Epic(service=service, tasks=tasks)


def _build_batch_checklist_task(
    service: ServiceDict,
    checklist: ChecklistDict,
    template: TemplateDict | None,
) -> Task | None:
    """Build Batch Mode Checklist Items task from template + checklist."""
    batch_subtasks: list[Subtask] = []
    if not template or not checklist:
        return None

    raw_baseline = template.get("baseline_items") or []
    baseline_items: list[object] = cast(list[object], raw_baseline) if isinstance(raw_baseline, list) else []
    raw_group = template.get("group_items") or []
    group_items: list[object] = cast(list[object], raw_group) if isinstance(raw_group, list) else []
    all_items: list[object] = [*baseline_items, *group_items]

    raw_checklist_items = checklist.get("checklist_items") or {}
    checklist_items: dict[str, object] = (
        cast(dict[str, object], raw_checklist_items) if isinstance(raw_checklist_items, dict) else {}
    )
    if not checklist_items:
        for key, value in dict(checklist).items():
            if isinstance(key, str) and key.startswith("phase_") and isinstance(value, dict):
                checklist_items.update(cast(dict[str, object], value))

    for raw_item in all_items:
        if not isinstance(raw_item, dict):
            continue
        item: dict[str, object] = cast(dict[str, object], raw_item)
        item_id = str(item.get("id", ""))
        item_title = str(item.get("title", ""))
        item_priority = str(item.get("priority", "P2-medium"))
        item_description = str(item.get("description", ""))
        item_key_pattern = f"item_{item_id.lower().replace('-', '_')}"

        checklist_item: dict[str, object] | None = None
        for key, value in checklist_items.items():
            if item_key_pattern in key.lower() and isinstance(value, dict):
                checklist_item = cast(dict[str, object], value)
                break

        if not checklist_item or str(checklist_item.get("status", "")) in ["pending", "fail", "partial"]:
            codex_ref = str(item.get("codex_ref", ""))
            batch_subtasks.append(
                Subtask(
                    title=f"{item_id}: {item_title}",
                    description=item_description,
                    complexity="MEDIUM",
                    priority=item_priority,
                    hours=estimate_hours_from_priority(item_priority),
                    checklist_item_id=item_id,
                    codex_refs=[codex_ref] if codex_ref else [],
                )
            )

    if not batch_subtasks:
        return None
    return Task(
        title="Batch Mode Checklist Items",
        description="Implement missing checklist items for batch mode",
        priority="P2-medium",
        mode="batch",
        subtasks=batch_subtasks,
    )


def generate_epic_for_existing_service(
    service: ServiceDict,
    checklist: ChecklistDict,
    template: TemplateDict | None,
) -> Epic:
    """Generate Epic/Task/Subtask for service that exists (checklist items)."""
    tasks: list[Task] = []

    batch_task = _build_batch_checklist_task(service, checklist, template)
    if batch_task:
        tasks.append(batch_task)

    raw_data_coverage = service.get("data_coverage") or {}
    data_coverage: dict[str, object] = (
        cast(dict[str, object], raw_data_coverage) if isinstance(raw_data_coverage, dict) else {}
    )
    has_live = bool(data_coverage.get("live_mode", False))
    if has_live:
        tasks.append(_build_live_mode_task_existing())

    return Epic(service=service, tasks=tasks)


def estimate_hours_from_priority(priority: str) -> float:
    """Estimate hours based on priority."""
    hours_map: dict[str, float] = {
        "P0-critical": 8.0,
        "P1-high": 6.0,
        "P2-medium": 4.0,
        "P3-low": 2.0,
    }
    return hours_map.get(priority, 4.0)


# ============================================================================
# GitHub Issue Creation
# ============================================================================


def ensure_labels_exist(dry_run: bool = False) -> None:
    """Ensure all required GitHub labels exist."""
    # Label definitions: (name, color, description)
    labels_to_create: list[tuple[str, str, str]] = [
        # Hierarchy
        ("epic", "8B5CF6", "Service-level Epic"),
        ("task", "3B82F6", "Logical work grouping"),
        ("subtask", "10B981", "Atomic work unit"),
        # Priority
        ("p0-critical", "DC2626", "Critical priority"),
        ("p1-high", "F97316", "High priority"),
        ("p2-medium", "FACC15", "Medium priority"),
        ("p3-low", "4ADE80", "Low priority"),
        # Mode
        ("mode/batch", "6366F1", "Batch processing mode"),
        ("mode/live", "EC4899", "Live/streaming mode"),
        # Domain
        ("domain/sports", "14B8A6", "Sports betting domain"),
        ("domain/crypto", "F59E0B", "Cryptocurrency domain"),
        ("domain/equities", "8B5CF6", "Equities domain"),
        ("domain/fx", "06B6D4", "Foreign exchange domain"),
        # Type
        ("type/pipeline", "737373", "Pipeline service"),
        ("type/platform", "525252", "Platform service"),
        ("type/ui", "404040", "UI service"),
        # Asset classes (matching service-registry.yaml)
        ("asset/crypto-cefi", "F59E0B", "Centralized crypto"),
        ("asset/defi", "EAB308", "Decentralized finance"),
        ("asset/tradfi-equities", "8B5CF6", "Traditional equities"),
        ("asset/tradfi-options", "A78BFA", "Traditional options"),
        ("asset/sports", "14B8A6", "Sports betting"),
        ("asset/fx", "06B6D4", "Foreign exchange"),
        ("asset/all", "6B7280", "All asset classes"),
        # UI categories
        ("ui/observability", "6366F1", "Observability UI"),
        ("ui/control", "DC2626", "Control/Trading UI"),
        ("ui/analysis", "3B82F6", "Analysis UI"),
        # Infrastructure
        ("infra/cloud", "64748B", "Cloud infrastructure"),
        ("infra/security", "DC2626", "Security infrastructure"),
    ]

    if dry_run:
        print("\n[DRY RUN] Would create labels:")
        for name, color, desc in labels_to_create:
            print(f"   - {name} (#{color}): {desc}")
        return

    print("\nEnsuring labels exist...")
    created_count = 0
    skipped_count = 0

    for name, color, description in labels_to_create:
        cmd: list[str] = [
            "gh",
            "label",
            "create",
            name,
            "--repo",
            f"{ORG}/{REPO}",
            "--color",
            color,
            "--description",
            description,
            "--force",  # Update if exists
        ]

        result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if "already exists" in result.stderr.lower():
                skipped_count += 1
            else:
                created_count += 1
        elif "already exists" not in result.stderr.lower():
            print(f"   Warning: {result.stderr.strip()}")

    print(f"   Labels ready ({created_count} created, {skipped_count} updated)\n")


def create_github_issue(
    title: str,
    body: str,
    labels: list[str],
    milestone: str | None,
    dry_run: bool,
) -> str | None:
    """Create a GitHub issue."""
    cmd: list[str] = [
        "gh",
        "issue",
        "create",
        "--repo",
        f"{ORG}/{REPO}",
        "--title",
        title,
        "--body",
        body,
    ]

    # Only add --label if we have labels (avoid empty string)
    if labels:
        cmd.extend(["--label", ",".join(labels)])

    if milestone:
        cmd.extend(["--milestone", milestone])

    if dry_run:
        print(f"\n{'=' * 80}")
        print("[DRY RUN] Would create issue")
        print(f"Title: {title}")
        print(f"Labels: {', '.join(labels) if labels else 'None'}")
        print(f"Milestone: {milestone or 'None'}")
        print(f"\nBody:\n{body}")
        print(f"{'=' * 80}\n")
        return None

    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to create issue: {result.stderr}")
        return None

    # Extract issue number from URL
    issue_url = result.stdout.strip()
    issue_number = issue_url.split("/")[-1]
    print(f"Created issue #{issue_number}: {title}")

    # Add to GitHub Project for hierarchy view
    add_to_project(issue_url, dry_run=False)

    return issue_number


def add_to_project(issue_url: str, dry_run: bool) -> bool:
    """Add issue to GitHub Project for hierarchy view."""
    if dry_run:
        return True

    cmd: list[str] = [
        "gh",
        "project",
        "item-add",
        str(PROJECT_NUMBER),
        "--owner",
        ORG,
        "--url",
        issue_url,
    ]

    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Silently continue if already added or other error
        return False
    return True


def get_issue_node_id(issue_number: int) -> str | None:
    """Get the node_id for an issue (required for GraphQL)."""
    cmd: list[str] = [
        "gh",
        "api",
        f"/repos/{ORG}/{REPO}/issues/{issue_number}",
        "--jq",
        ".node_id",
    ]
    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def check_rate_limit() -> dict[str, object]:
    """Check GitHub GraphQL API rate limits."""
    cmd: list[str] = [
        "gh",
        "api",
        "rate_limit",
        "--jq",
        ".resources.graphql",
    ]
    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"remaining": 0, "limit": 5000, "reset": 0}
    return cast(dict[str, object], json.loads(result.stdout))


def link_sub_issue(parent_issue_number: int, sub_issue_number: int, dry_run: bool) -> bool:
    """Link a sub-issue to its parent using GitHub's GraphQL API."""
    if dry_run:
        print(f"   [DRY RUN] Would link #{sub_issue_number} as sub-issue of #{parent_issue_number}")
        return True

    # Check rate limit before GraphQL call
    rate_limit = check_rate_limit()
    remaining_raw = rate_limit.get("remaining", 0)
    remaining = int(remaining_raw) if isinstance(remaining_raw, (int, float)) else 0

    if remaining < 10:
        reset_raw = rate_limit.get("reset", 0)
        reset_time = int(reset_raw) if isinstance(reset_raw, (int, float)) else 0
        wait_seconds = max(0, reset_time - int(time.time()))
        print(f"   GraphQL rate limit low ({remaining}/5000 remaining)")
        if wait_seconds > 60:
            print(f"   Rate limit resets in {int(wait_seconds / 60)} minutes - skipping links for now")
            return False

    # Get node IDs (required for GraphQL)
    parent_node_id = get_issue_node_id(parent_issue_number)
    sub_issue_node_id = get_issue_node_id(sub_issue_number)

    if not parent_node_id or not sub_issue_node_id:
        print("   Failed to get node IDs for linking")
        return False

    # Use GraphQL mutation (REST API doesn't support adding sub-issues)
    query = (
        "mutation {"
        f"  addSubIssue(input: {{"
        f'    issueId: "{parent_node_id}",'
        f'    subIssueId: "{sub_issue_node_id}"'
        "  }) {"
        "    issue { number title }"
        "    subIssue { number title }"
        "  }"
        "}"
    )

    cmd: list[str] = ["gh", "api", "graphql", "-f", f"query={query}"]
    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        if "rate limit" in result.stderr.lower():
            print("   Rate limit exceeded - skipping link")
            return False
        print(f"   Failed to link: {result.stderr.strip()[:80]}")
        return False

    print(f"   Linked #{sub_issue_number} -> #{parent_issue_number}")
    return True


def generate_labels_for_service(service: ServiceDict, mode: str | None = None) -> list[str]:
    """Generate labels for a service."""
    labels: list[str] = [
        "epic",
        str(service.get("priority", "P2-medium")).lower(),
    ]

    # Service type
    service_type = str(service.get("type", ""))
    if service_type:
        labels.append(f"type/{service_type}")

    # Mode
    if mode:
        labels.append(f"mode/{mode}")

    # Asset classes (from nested domain_coverage)
    raw_domain = service.get("domain_coverage") or {}
    domain_coverage: dict[str, object] = cast(dict[str, object], raw_domain) if isinstance(raw_domain, dict) else {}
    raw_asset_groupes = domain_coverage.get("asset_groupes") or []
    asset_groupes: list[str] = cast(list[str], raw_asset_groupes) if isinstance(raw_asset_groupes, list) else []
    for asset_group in asset_groupes:
        # Normalize label (e.g., CRYPTO_CEFI -> crypto-cefi)
        normalized = asset_group.lower().replace("_", "-")
        labels.append(f"asset/{normalized}")

    # UI category (from nested ui_metadata)
    if service_type == "ui":
        raw_ui_meta = service.get("ui_metadata") or {}
        ui_meta: dict[str, object] = cast(dict[str, object], raw_ui_meta) if isinstance(raw_ui_meta, dict) else {}
        ui_category = str(ui_meta.get("category", ""))
        if ui_category:
            labels.append(f"ui/{ui_category}")

    return labels


# ============================================================================
# Main
# ============================================================================


def _parse_args() -> tuple[str, bool, bool]:
    """Parse CLI arguments. Returns (service_arg, all_services, dry_run)."""
    parser = argparse.ArgumentParser(description="Create service-level epics")
    parser.add_argument("--service", help="Create epic for single service (e.g., instruments-service)")
    parser.add_argument("--all-services", action="store_true", help="Create epics for all services")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")
    parsed = parser.parse_args()
    service_arg = str(getattr(parsed, "service", "") or "")
    all_services = bool(getattr(parsed, "all_services", False))
    dry_run = bool(getattr(parsed, "dry_run", False))
    if not any([service_arg, all_services]):
        parser.error("Must specify --service or --all-services")
    return service_arg, all_services, dry_run


def _resolve_services_to_process(registry: RegistryDict, service_arg: str, all_services: bool) -> list[ServiceDict]:
    """Resolve which services to process from registry."""
    if service_arg:
        raw_svcs = registry.get("services") or []
        svcs_list: list[object] = cast(list[object], raw_svcs) if isinstance(raw_svcs, list) else []
        for svc in svcs_list:
            if isinstance(svc, dict):
                svc_dict: ServiceDict = cast(ServiceDict, svc)
                if str(svc_dict.get("service", "")) == service_arg:
                    return [svc_dict]
        print(f"Service {service_arg} not found in registry")
        sys.exit(1)
    raw_svcs = registry.get("services") or []
    return cast(list[ServiceDict], raw_svcs) if isinstance(raw_svcs, list) else []


def _create_epic_and_issues(
    service: ServiceDict,
    templates: dict[str, TemplateDict],
    dry_run: bool,
) -> tuple[int, int, int]:
    """Create epic + tasks + subtasks for one service. Returns (1, tasks_count, subtasks_count)."""
    service_name = str(service.get("service", ""))
    print(f"\nProcessing {service_name}...")

    repo_path = WORKSPACE_ROOT / service_name
    service_exists = repo_path.exists()
    checklist = load_deployment_checklist(service_name)
    template = get_template_for_service(service, templates)

    if service_exists and checklist:
        print("   Service exists with checklist")
        epic = generate_epic_for_existing_service(service, checklist, template)
    else:
        print("   Service missing - generating full Epic")
        epic = generate_epic_for_missing_service(service)

    epic_labels = generate_labels_for_service(service)
    epic_number = create_github_issue(
        title=f"[Epic] {service_name}",
        body=epic.to_github_issue_body(),
        labels=epic_labels,
        milestone=epic.milestone,
        dry_run=dry_run,
    )
    if not epic_number:
        epic_number = "999"

    tasks_count = len(epic.tasks)
    subtasks_count = 0

    for task in epic.tasks:
        task_labels: list[str] = ["task", task.priority.lower()]
        if task.mode:
            task_labels.append(f"mode/{task.mode}")

        task_number = create_github_issue(
            title=f"[Task] {service_name}: {task.title}",
            body=task.to_github_issue_body(epic_number=int(epic_number)),
            labels=task_labels,
            milestone=epic.milestone,
            dry_run=dry_run,
        )
        if not task_number:
            task_number = "999"

        link_sub_issue(parent_issue_number=int(epic_number), sub_issue_number=int(task_number), dry_run=dry_run)
        subtasks_count += len(task.subtasks)

        for subtask in task.subtasks:
            subtask_labels = ["subtask", subtask.priority.lower()]
            subtask_number = create_github_issue(
                title=f"[Subtask] {service_name}: {subtask.title}",
                body=subtask.to_github_issue_body(parent_task_number=int(task_number), epic_number=int(epic_number)),
                labels=subtask_labels,
                milestone=epic.milestone,
                dry_run=dry_run,
            )
            if not subtask_number:
                subtask_number = "999"
            link_sub_issue(parent_issue_number=int(task_number), sub_issue_number=int(subtask_number), dry_run=dry_run)

    print(f"   Created: 1 Epic, {tasks_count} Tasks, {subtasks_count} Subtasks")
    return 1, tasks_count, subtasks_count


def _print_summary(total_epics: int, total_tasks: int, total_subtasks: int, dry_run: bool) -> None:
    """Print final summary."""
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Epics: {total_epics}")
    print(f"Tasks: {total_tasks}")
    print(f"Subtasks: {total_subtasks}")
    print(f"Total Issues: {total_epics + total_tasks + total_subtasks}")
    print(f"{'=' * 80}\n")
    if dry_run:
        print("Dry run complete - no issues created")
    else:
        print("All epics created!")


def main() -> None:
    service_arg, all_services, dry_run = _parse_args()

    print("Loading service registry...")
    registry = load_service_registry()
    print("Loading codex templates...")
    templates = load_codex_templates()

    services_to_process = _resolve_services_to_process(registry, service_arg, all_services)
    print(f"Processing {len(services_to_process)} services...\n")

    ensure_labels_exist(dry_run=dry_run)

    total_epics = 0
    total_tasks = 0
    total_subtasks = 0

    for service in services_to_process:
        epics_delta, tasks_delta, subtasks_delta = _create_epic_and_issues(service, templates, dry_run)
        total_epics += epics_delta
        total_tasks += tasks_delta
        total_subtasks += subtasks_delta

    _print_summary(total_epics, total_tasks, total_subtasks, dry_run)


if __name__ == "__main__":
    main()
