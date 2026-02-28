#!/usr/bin/env python3
"""
Create Service-Level Epics with Task/Subtask Hierarchy
=======================================================

**New Structure:** One Epic per Service

Epic: instruments-service
├─ Task: Batch Mode Checklist Items (Priority 3b)
│  ├─ Subtask: DATA-04 (Sports support)
│  └─ Subtask: BASELINE-01 (Config)
├─ Task: Live Mode Implementation (Priority 3a - NEW, nothing exists)
│  ├─ Subtask: WebSocket client
│  ├─ Subtask: Real-time processing
│  └─ Subtask: Observability
└─ Task: Testing & Infrastructure

**Key Principles:**
- Service doesn't exist → Full Epic/Task/Subtask (Repo, Core, Live, Testing)
- Service exists, batch mode → Checklist items as subtasks
- Service exists, live mode → Full Live implementation (nothing exists yet)
- Rich labels: mode/batch, mode/live, domain/sports, type/ui, etc.

Usage:
  # Dry run (preview)
  python3 create-service-epics.py --all-services --dry-run

  # Create epics
  python3 create-service-epics.py --all-services

  # Single service
  python3 create-service-epics.py --service instruments-service
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import yaml

# ============================================================================
# Config
# ============================================================================

CODEX_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = CODEX_ROOT.parent
SERVICE_REGISTRY = CODEX_ROOT / "11-project-management" / "service-registry.yaml"
CODEX_TEMPLATES_DIR = CODEX_ROOT / "10-audit"
DEPLOYMENT_CHECKLISTS_DIR = WORKSPACE_ROOT / "unified-trading-deployment-v2" / "configs"

ORG = "IggyIkenna"
REPO = "unified-trading-codex"  # All issues in codex repo
PROJECT_NUMBER = 1  # "Codex Delta Wave 1 - Unified Board"


# ============================================================================
# Epic/Task/Subtask Structure
# ============================================================================


class Subtask:
    """Atomic work unit."""

    def __init__(
        self,
        title: str,
        description: str,
        complexity: str,  # LOW, MEDIUM, HIGH
        priority: str,  # P0-critical, P1-high, P2-medium, P3-low
        hours: float,
        checklist_item_id: str | None = None,  # e.g., DATA-04
        codex_refs: list[str] | None = None,
    ):
        self.title = title
        self.description = description
        self.complexity = complexity
        self.priority = priority
        self.hours = hours
        self.checklist_item_id = checklist_item_id
        self.codex_refs = codex_refs or []

    def to_github_issue_body(self, parent_task_number: int, epic_number: int) -> str:
        """Format subtask as GitHub issue body."""
        body_parts = [
            f"**Parent Task:** #{parent_task_number}",
            f"**Parent Epic:** #{epic_number}",
            f"**Complexity:** {self.complexity}",
            f"**Priority:** {self.priority}",
            f"**Estimated Hours:** {self.hours}",
            "",
            "## Description",
            self.description,
        ]

        if self.checklist_item_id:
            body_parts.extend(
                [
                    "",
                    f"**Checklist Item:** {self.checklist_item_id}",
                ]
            )

        if self.codex_refs:
            body_parts.extend(
                [
                    "",
                    "## Codex References",
                ]
            )
            for ref in self.codex_refs:
                body_parts.append(f"- `{ref}`")

        body_parts.extend(
            [
                "",
                "## Success Criteria",
                "- [ ] Implementation complete",
                "- [ ] Tests pass (>80% coverage)",
                "- [ ] Quality gates pass",
                "- [ ] PR merged",
            ]
        )

        if self.checklist_item_id:
            body_parts.append(f"- [ ] Checklist item {self.checklist_item_id} updated to 'done'")

        body_parts.extend(
            [
                "",
                f"<!-- subtask-ref: {self.checklist_item_id or self.title} -->",
            ]
        )

        return "\n".join(body_parts)


class Task:
    """Logical work grouping."""

    def __init__(
        self,
        title: str,
        description: str,
        priority: str,
        mode: str | None = None,  # batch, live, or None
        subtasks: list[Subtask] | None = None,
    ):
        self.title = title
        self.description = description
        self.priority = priority
        self.mode = mode
        self.subtasks = subtasks or []

    def total_hours(self) -> float:
        """Calculate total hours for all subtasks."""
        return sum(s.hours for s in self.subtasks)

    def to_github_issue_body(self, epic_number: int) -> str:
        """Format task as GitHub issue body."""
        body_parts = [
            f"**Parent Epic:** #{epic_number}",
            f"**Priority:** {self.priority}",
        ]

        if self.mode:
            body_parts.append(f"**Mode:** {self.mode}")

        body_parts.extend(
            [
                f"**Total Hours:** {self.total_hours():.1f}h",
                "",
                "## Description",
                self.description,
                "",
                "## Subtasks",
                "",
            ]
        )

        for i, subtask in enumerate(self.subtasks, 1):
            body_parts.append(f"{i}. **{subtask.title}** ({subtask.complexity}, {subtask.hours}h)")

        body_parts.extend(
            [
                "",
                f"<!-- task-ref: {self.title} -->",
            ]
        )

        return "\n".join(body_parts)


class Epic:
    """Service-level epic."""

    def __init__(
        self,
        service: dict[str, Any],
        tasks: list[Task] | None = None,
        milestone: str | None = None,
    ):
        self.service = service
        self.service_name = service["service"]
        self.tasks = tasks or []
        self.milestone = milestone or service.get("milestone", "Backlog")

    def total_hours(self) -> float:
        """Calculate total hours for all tasks."""
        return sum(t.total_hours() for t in self.tasks)

    def to_github_issue_body(self) -> str:
        """Format epic as GitHub issue body."""
        service_type = self.service.get("type", "unknown")
        layer = self.service.get("layer", "N/A")
        venues = ", ".join(self.service.get("venues", []))
        asset_classes = ", ".join(self.service.get("asset_classes", []))

        body_parts = [
            f"**Service:** `{self.service_name}`",
            f"**Type:** {service_type}",
            f"**Layer:** {layer}",
            f"**Milestone:** {self.milestone}",
            f"**Total Hours:** {self.total_hours():.1f}h",
            "",
        ]

        if venues:
            body_parts.append(f"**Venues:** {venues}")
        if asset_classes:
            body_parts.append(f"**Asset Classes:** {asset_classes}")

        body_parts.extend(
            [
                "",
                "## Tasks",
                "",
            ]
        )

        for i, task in enumerate(self.tasks, 1):
            mode_label = f" ({task.mode})" if task.mode else ""
            body_parts.append(f"{i}. **{task.title}**{mode_label} - {task.total_hours():.1f}h")

        body_parts.extend(
            [
                "",
                f"<!-- epic-ref: {self.service_name} -->",
            ]
        )

        return "\n".join(body_parts)


# ============================================================================
# Service Registry & Checklist Loading
# ============================================================================


def load_service_registry() -> dict[str, Any]:
    """Load service registry."""
    with open(SERVICE_REGISTRY) as f:
        return yaml.safe_load(f)


def load_deployment_checklist(service_name: str) -> dict | None:
    """Load deployment checklist for a service."""
    checklist_path = DEPLOYMENT_CHECKLISTS_DIR / f"checklist.{service_name}.yaml"
    if not checklist_path.exists():
        return None

    with open(checklist_path) as f:
        return yaml.safe_load(f)


def load_codex_templates() -> dict[str, dict]:
    """Load all codex templates."""
    templates = {}
    for path in CODEX_TEMPLATES_DIR.glob("_service-*.yaml"):
        with open(path) as f:
            data = yaml.safe_load(f)
            template_name = path.stem
            templates[template_name] = data
    return templates


def get_template_for_service(service: dict, templates: dict) -> dict | None:
    """Get codex template for a service."""
    service_type = service.get("type")

    # Handle nested pipeline_metadata structure
    pipeline_meta = service.get("pipeline_metadata", {})
    layer = pipeline_meta.get("layer")
    group = pipeline_meta.get("group")

    if service_type == "pipeline":
        # Map layer number + group to template
        if layer == 1 and group == "data-io":
            template_key = "_service-pipeline-data-io"
        elif layer == 2:
            template_key = "_service-pipeline-market-data"
        elif layer == 3:
            template_key = "_service-pipeline-features"
        elif layer == 4:
            template_key = "_service-pipeline-ml"
        elif layer in [5, 6]:
            template_key = "_service-pipeline-strategy-execution"
        elif layer == 7:
            template_key = "_service-pipeline-post-trade"
        else:
            print(f"⚠️  Unknown pipeline layer {layer} for {service.get('service')}")
            return None
    elif service_type == "platform":
        template_key = "_service-platform"
    elif service_type == "ui":
        # Handle nested ui_metadata structure
        ui_meta = service.get("ui_metadata", {})
        ui_category = ui_meta.get("category", "observability")
        template_key = f"_service-ui-{ui_category}"
    else:
        return None

    return templates.get(template_key)


# ============================================================================
# Epic Generation Logic
# ============================================================================


def generate_epic_for_missing_service(service: dict) -> Epic:
    """Generate Epic/Task/Subtask for a service that doesn't exist."""
    service_name = service["service"]
    service_type = service.get("type", "pipeline")

    tasks = []

    # Task 1: Repo Scaffolding
    tasks.append(
        Task(
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
                    description="Add cloudbuild.yaml, quality-gates.yml, quickmerge.sh",
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
    )

    # Task 2: Batch Mode Implementation (if service has batch)
    # Check nested data_coverage structure
    data_coverage = service.get("data_coverage", {})
    has_batch = data_coverage.get("batch_mode", True)  # Default True for most services

    if has_batch:
        tasks.append(
            Task(
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
                        description=f"Service-specific logic for {service_name}",
                        complexity="HIGH",
                        priority="P0-critical",
                        hours=16.0,
                    ),
                    Subtask(
                        title="Add GCS data I/O",
                        description="Read from input buckets, write to output buckets",
                        complexity="MEDIUM",
                        priority="P1-high",
                        hours=6.0,
                        codex_refs=["02-data/gcs-structure.md"],
                    ),
                    Subtask(
                        title="Add data status tracking",
                        description="Implement manifest files for coverage tracking",
                        complexity="MEDIUM",
                        priority="P2-medium",
                        hours=4.0,
                        codex_refs=["02-data/data-status-tracking.md"],
                    ),
                ],
            )
        )

    # Task 3: Live Mode Implementation (if service has live)
    has_live = data_coverage.get("live_mode", False)  # Default False

    if has_live:
        tasks.append(
            Task(
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
                        description="Handle disconnects with exponential backoff",
                        complexity="MEDIUM",
                        priority="P1-high",
                        hours=4.0,
                    ),
                ],
            )
        )

    # Task 4: Observability
    tasks.append(
        Task(
            title="Observability",
            description="Lifecycle events, metrics, alerts",
            priority="P1-high",
            mode=None,
            subtasks=[
                Subtask(
                    title="Add lifecycle events",
                    description="STARTED, INGESTING, PROCESSING, COMPLETED, FAILED",
                    complexity="MEDIUM",
                    priority="P1-high",
                    hours=3.0,
                    codex_refs=["03-observability/lifecycle-events.md"],
                ),
                Subtask(
                    title="Add metrics",
                    description="Counter, Gauge, Histogram for service-specific metrics",
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
    )

    # Task 5: Testing
    tasks.append(
        Task(
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
    )

    return Epic(service=service, tasks=tasks)


def generate_epic_for_existing_service(service: dict, checklist: dict, template: dict) -> Epic:
    """Generate Epic/Task/Subtask for service that exists (checklist items)."""
    service_name = service["service"]
    tasks = []

    # Task 1: Batch Mode Checklist Items
    batch_subtasks = []
    if template and checklist:
        baseline_items = template.get("baseline_items", [])
        group_items = template.get("group_items", [])
        all_items = baseline_items + group_items

        # Get checklist items dict
        checklist_items = checklist.get("checklist_items", {})
        if not checklist_items:
            # Try phase-based structure
            for key, value in checklist.items():
                if key.startswith("phase_") and isinstance(value, dict):
                    checklist_items.update(value)

        for item in all_items:
            item_id = item["id"]
            item_title = item["title"]
            item_priority = item.get("priority", "P2-medium")
            item_description = item.get("description", "")

            # Check if item is pending/fail in actual checklist
            # Convert item_id (e.g., "DATA-04") to checklist key format (e.g., "item_data_04_...")
            item_key_pattern = f"item_{item_id.lower().replace('-', '_')}"

            # Find matching checklist item
            checklist_item = None
            for key, value in checklist_items.items():
                if item_key_pattern in key.lower():
                    checklist_item = value
                    break

            # Only add if status is pending, fail, or partial (or if not in checklist at all)
            if not checklist_item or checklist_item.get("status") in ["pending", "fail", "partial"]:
                batch_subtasks.append(
                    Subtask(
                        title=f"{item_id}: {item_title}",
                        description=item_description,
                        complexity="MEDIUM",
                        priority=item_priority,
                        hours=estimate_hours_from_priority(item_priority),
                        checklist_item_id=item_id,
                        codex_refs=[item.get("codex_ref", "")] if item.get("codex_ref") else [],
                    )
                )

    if batch_subtasks:
        tasks.append(
            Task(
                title="Batch Mode Checklist Items",
                description="Implement missing checklist items for batch mode",
                priority="P2-medium",
                mode="batch",
                subtasks=batch_subtasks,
            )
        )

    # Task 2: Live Mode Implementation (if service should have live but doesn't)
    data_coverage = service.get("data_coverage", {})
    has_live = data_coverage.get("live_mode", False)

    if has_live:
        tasks.append(
            Task(
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
        )

    return Epic(service=service, tasks=tasks)


def estimate_hours_from_priority(priority: str) -> float:
    """Estimate hours based on priority."""
    return {
        "P0-critical": 8.0,
        "P1-high": 6.0,
        "P2-medium": 4.0,
        "P3-low": 2.0,
    }.get(priority, 4.0)


# ============================================================================
# GitHub Issue Creation
# ============================================================================


def ensure_labels_exist(dry_run: bool = False) -> None:
    """Ensure all required GitHub labels exist."""
    # Label definitions: (name, color, description)
    labels_to_create = [
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
        print("\n🏷️  [DRY RUN] Would create labels:")
        for name, color, desc in labels_to_create:
            print(f"   - {name} (#{color}): {desc}")
        return

    print("\n🏷️  Ensuring labels exist...")
    created_count = 0
    skipped_count = 0

    for name, color, description in labels_to_create:
        cmd = [
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

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            if "already exists" in result.stderr.lower():
                skipped_count += 1
            else:
                created_count += 1
        else:
            # Label already exists is not an error with --force
            if "already exists" not in result.stderr.lower():
                print(f"   ⚠️  Warning: {result.stderr.strip()}")

    print(f"   ✅ Labels ready ({created_count} created, {skipped_count} updated)\n")


def create_github_issue(title: str, body: str, labels: list[str], milestone: str | None, dry_run: bool) -> str | None:
    """Create a GitHub issue."""
    cmd = [
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

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create issue: {result.stderr}")
        return None

    # Extract issue number from URL
    issue_url = result.stdout.strip()
    issue_number = issue_url.split("/")[-1]
    print(f"✅ Created issue #{issue_number}: {title}")

    # Add to GitHub Project for hierarchy view
    add_to_project(issue_url, dry_run=False)

    return issue_number


def add_to_project(issue_url: str, dry_run: bool) -> bool:
    """Add issue to GitHub Project for hierarchy view."""
    if dry_run:
        return True

    cmd = ["gh", "project", "item-add", str(PROJECT_NUMBER), "--owner", ORG, "--url", issue_url]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Silently continue if already added or other error
        return False
    return True


def get_issue_node_id(issue_number: int) -> str | None:
    """Get the node_id for an issue (required for GraphQL)."""
    cmd = ["gh", "api", f"/repos/{ORG}/{REPO}/issues/{issue_number}", "--jq", ".node_id"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def check_rate_limit() -> dict:
    """Check GitHub GraphQL API rate limits."""
    cmd = ["gh", "api", "rate_limit", "--jq", ".resources.graphql"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"remaining": 0, "limit": 5000, "reset": 0}
    return json.loads(result.stdout)


def link_sub_issue(parent_issue_number: int, sub_issue_number: int, dry_run: bool) -> bool:
    """Link a sub-issue to its parent using GitHub's GraphQL API."""
    if dry_run:
        print(f"   [DRY RUN] Would link #{sub_issue_number} as sub-issue of #{parent_issue_number}")
        return True

    # Check rate limit before GraphQL call
    rate_limit = check_rate_limit()
    remaining = rate_limit.get("remaining", 0)

    if remaining < 10:
        reset_time = rate_limit.get("reset", 0)
        wait_seconds = max(0, reset_time - int(time.time()))
        print(f"   ⚠️  GraphQL rate limit low ({remaining}/5000 remaining)")
        if wait_seconds > 60:
            print(f"   ⏳  Rate limit resets in {int(wait_seconds / 60)} minutes - skipping links for now")
            return False

    # Get node IDs (required for GraphQL)
    parent_node_id = get_issue_node_id(parent_issue_number)
    sub_issue_node_id = get_issue_node_id(sub_issue_number)

    if not parent_node_id or not sub_issue_node_id:
        print("   ⚠️  Failed to get node IDs for linking")
        return False

    # Use GraphQL mutation (REST API doesn't support adding sub-issues)
    query = f'''
    mutation {{
      addSubIssue(input: {{
        issueId: "{parent_node_id}",
        subIssueId: "{sub_issue_node_id}"
      }}) {{
        issue {{
          number
          title
        }}
        subIssue {{
          number
          title
        }}
      }}
    }}
    '''

    cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        if "rate limit" in result.stderr.lower():
            print("   ⚠️  Rate limit exceeded - skipping link")
            return False
        print(f"   ⚠️  Failed to link: {result.stderr.strip()[:80]}")
        return False

    print(f"   🔗 Linked #{sub_issue_number} → #{parent_issue_number}")
    return True


def generate_labels_for_service(service: dict, mode: str | None = None) -> list[str]:
    """Generate labels for a service."""
    labels = ["epic", service.get("priority", "P2-medium").lower()]

    # Service type
    service_type = service.get("type")
    if service_type:
        labels.append(f"type/{service_type}")

    # Mode
    if mode:
        labels.append(f"mode/{mode}")

    # Asset classes (from nested domain_coverage)
    domain_coverage = service.get("domain_coverage", {})
    asset_classes = domain_coverage.get("asset_classes", [])
    for asset_class in asset_classes:
        # Normalize label (e.g., CRYPTO_CEFI → crypto-cefi)
        normalized = asset_class.lower().replace("_", "-")
        labels.append(f"asset/{normalized}")

    # UI category (from nested ui_metadata)
    if service_type == "ui":
        ui_meta = service.get("ui_metadata", {})
        ui_category = ui_meta.get("category")
        if ui_category:
            labels.append(f"ui/{ui_category}")

    return labels


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Create service-level epics")
    parser.add_argument("--service", help="Create epic for single service (e.g., instruments-service)")
    parser.add_argument("--all-services", action="store_true", help="Create epics for all services")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating")

    args = parser.parse_args()

    if not any([args.service, args.all_services]):
        parser.error("Must specify --service or --all-services")

    print("🔍 Loading service registry...")
    registry = load_service_registry()

    print("📋 Loading codex templates...")
    templates = load_codex_templates()

    # Determine which services to process
    services_to_process = []
    if args.service:
        for service in registry.get("services", []):
            if service["service"] == args.service:
                services_to_process = [service]
                break
        if not services_to_process:
            print(f"❌ Service {args.service} not found in registry")
            sys.exit(1)
    elif args.all_services:
        services_to_process = registry.get("services", [])

    print(f"📊 Processing {len(services_to_process)} services...\n")

    # Ensure all labels exist BEFORE creating issues
    ensure_labels_exist(dry_run=args.dry_run)

    total_epics = 0
    total_tasks = 0
    total_subtasks = 0

    for service in services_to_process:
        service_name = service["service"]
        print(f"\n🔨 Processing {service_name}...")

        # Check if service exists
        repo_path = WORKSPACE_ROOT / service_name
        service_exists = repo_path.exists()

        # Load checklist and template
        checklist = load_deployment_checklist(service_name)
        template = get_template_for_service(service, templates)

        if service_exists and checklist:
            print("   ✅ Service exists with checklist")
            epic = generate_epic_for_existing_service(service, checklist, template)
        else:
            print("   🆕 Service missing - generating full Epic")
            epic = generate_epic_for_missing_service(service)

        # Create Epic issue
        epic_labels = generate_labels_for_service(service)
        epic_number = create_github_issue(
            title=f"[Epic] {service_name}",
            body=epic.to_github_issue_body(),
            labels=epic_labels,
            milestone=epic.milestone,
            dry_run=args.dry_run,
        )

        if not epic_number:
            epic_number = 999  # Placeholder for dry-run

        total_epics += 1
        total_tasks += len(epic.tasks)

        # Create Task issues
        for task in epic.tasks:
            task_labels = ["task", task.priority.lower()]
            if task.mode:
                task_labels.append(f"mode/{task.mode}")

            task_number = create_github_issue(
                title=f"[Task] {service_name}: {task.title}",
                body=task.to_github_issue_body(epic_number=int(epic_number)),
                labels=task_labels,
                milestone=epic.milestone,
                dry_run=args.dry_run,
            )

            if not task_number:
                task_number = 999  # Placeholder for dry-run

            # Always link (works in dry-run too)
            link_sub_issue(
                parent_issue_number=int(epic_number),
                sub_issue_number=int(task_number),
                dry_run=args.dry_run,
            )

            total_subtasks += len(task.subtasks)

            # Create Subtask issues
            for subtask in task.subtasks:
                subtask_labels = ["subtask", subtask.priority.lower()]

                subtask_number = create_github_issue(
                    title=f"[Subtask] {service_name}: {subtask.title}",
                    body=subtask.to_github_issue_body(
                        parent_task_number=int(task_number),
                        epic_number=int(epic_number),
                    ),
                    labels=subtask_labels,
                    milestone=epic.milestone,
                    dry_run=args.dry_run,
                )

                if not subtask_number:
                    subtask_number = 999  # Placeholder for dry-run

                # Always link (works in dry-run too)
                link_sub_issue(
                    parent_issue_number=int(task_number),
                    sub_issue_number=int(subtask_number),
                    dry_run=args.dry_run,
                )

        print(f"   ✅ Created: 1 Epic, {len(epic.tasks)} Tasks, {sum(len(t.subtasks) for t in epic.tasks)} Subtasks")

    # Summary
    print(f"\n{'=' * 80}")
    print("📊 SUMMARY")
    print(f"{'=' * 80}")
    print(f"Epics: {total_epics}")
    print(f"Tasks: {total_tasks}")
    print(f"Subtasks: {total_subtasks}")
    print(f"Total Issues: {total_epics + total_tasks + total_subtasks}")
    print(f"{'=' * 80}\n")

    if args.dry_run:
        print("🔍 Dry run complete - no issues created")
    else:
        print("✅ All epics created!")


if __name__ == "__main__":
    main()
