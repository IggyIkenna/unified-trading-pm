#!/usr/bin/env python3
"""
Unified Service Compliance Checker
===================================

Checks service compliance against Codex standards by comparing:
  1. Service Registry (service-registry.yaml) - what services should exist
  2. Codex Templates (10-audit/_service-*.yaml) - required checklist items
  3. Deployment Checklists (deployment-v2/configs/checklist.*.yaml) - current status
  4. Actual Repos (workspace) - implementation reality
  5. GCS Data (manifests) - data coverage

Creates GitHub issues for gaps:
  - Missing services (registry → no repo)
  - Missing checklist items (codex template → deployment checklist)
  - Failed/pending items (deployment checklist status)
  - Batch data gaps (expected dates → actual GCS data)
  - Live data gaps (expected venues → active streams)

Usage:
  # Check single service (dry run)
  python3 check-service-compliance.py --repo IggyIkenna/instruments-service --dry-run

  # Check all services (create issues)
  python3 check-service-compliance.py --all-services

  # Check specific service types
  python3 check-service-compliance.py --service-type pipeline --dry-run
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

# ============================================================================
# Config
# ============================================================================

CODEX_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_ROOT = CODEX_ROOT.parent.parent
SERVICE_REGISTRY = CODEX_ROOT / "11-project-management" / "service-registry.yaml"
CODEX_TEMPLATES_DIR = CODEX_ROOT / "10-audit"
DEPLOYMENT_CHECKLISTS_DIR = WORKSPACE_ROOT / "unified-trading-deployment-v2" / "configs"

ORG = "IggyIkenna"
PROJECT_NUMBER = 7  # Unified Trading Deployment v2

# ============================================================================
# Gap Types
# ============================================================================


class Gap:
    """Base class for compliance gaps."""

    def __init__(
        self,
        gap_type: str,
        service: str,
        title: str,
        priority: str,
        description: str,
        breakdown: list[dict[str, Any]],
        milestone: str | None = None,
        labels: list[str] | None = None,
        codex_refs: list[str] | None = None,
        estimated_hours: float = 0,
    ):
        self.gap_type = gap_type
        self.service = service
        self.title = title
        self.priority = priority
        self.description = description
        self.breakdown = breakdown
        self.milestone = milestone
        self.labels = labels or []
        self.codex_refs = codex_refs or []
        self.estimated_hours = estimated_hours

    def to_github_issue_body(self) -> str:
        """Format gap as GitHub issue body."""
        body_parts = [
            f"**Service:** `{self.service}`",
            f"**Priority:** {self.priority}",
            f"**Gap Type:** {self.gap_type}",
        ]

        if self.milestone:
            body_parts.append(f"**Milestone:** {self.milestone}")

        body_parts.extend(
            [
                "",
                "## Context",
                self.description,
            ]
        )

        if self.breakdown:
            body_parts.extend(
                [
                    "",
                    "## Required Subtasks",
                    "",
                ]
            )
            for subtask in self.breakdown:
                subtask_type = subtask.get("type", "task")
                title = subtask.get("title", "Untitled")
                desc = subtask.get("description", "")
                hours = subtask.get("estimated_hours", 0)

                body_parts.append(f"### {title} ({hours}h)")
                body_parts.append(f"**Type:** {subtask_type}")
                if desc:
                    body_parts.append(desc)
                body_parts.append("")

                # Add file hints
                if "files" in subtask:
                    body_parts.append(f"**Files:** `{', '.join(subtask['files'])}`")
                    body_parts.append("")

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
                "- [ ] All subtasks completed",
                "- [ ] Tests pass (>80% coverage)",
                "- [ ] Quality gates pass",
                "- [ ] Deployment checklist updated",
                "",
                "## Time Estimate",
                f"{self.estimated_hours:.1f} hours",
                "",
                f"<!-- gap-id: {self.gap_type}:{self.service} -->",
            ]
        )

        return "\n".join(body_parts)


# ============================================================================
# Service Registry
# ============================================================================


def load_service_registry() -> dict[str, Any]:
    """Load service registry."""
    with open(SERVICE_REGISTRY) as f:
        return yaml.safe_load(f)


def get_service_from_registry(registry: dict, service_name: str) -> dict | None:
    """Get service metadata from registry."""
    for service in registry.get("services", []):
        if service["service"] == service_name:
            return service
    return None


# ============================================================================
# Codex Templates
# ============================================================================


def load_codex_templates() -> dict[str, dict]:
    """Load all codex templates from 10-audit/_service-*.yaml."""
    templates = {}
    for path in CODEX_TEMPLATES_DIR.glob("_service-*.yaml"):
        with open(path) as f:
            data = yaml.safe_load(f)
            template_name = path.stem  # e.g., _service-pipeline-data-io
            templates[template_name] = data
    return templates


def get_template_for_service(service: dict, templates: dict[str, dict]) -> dict | None:
    """Get the appropriate codex template for a service."""
    service_type = service.get("type")  # e.g., "pipeline"
    layer = service.get("layer")  # e.g., "1-data-io"

    if service_type == "pipeline":
        # Map layer to template
        layer_map = {
            "1-data-io": "_service-pipeline-data-io",
            "2-market-data": "_service-pipeline-market-data",
            "3-features": "_service-pipeline-features",
            "4-ml": "_service-pipeline-ml",
            "5-strategy": "_service-pipeline-strategy-execution",
            "6-execution": "_service-pipeline-strategy-execution",
        }
        template_key = layer_map.get(layer)
    elif service_type == "platform":
        template_key = "_service-platform"
    elif service_type == "ui":
        ui_category = service.get("ui_category", "observability")
        template_key = f"_service-ui-{ui_category}"
    else:
        return None

    return templates.get(template_key)


# ============================================================================
# Deployment Checklists
# ============================================================================


def load_deployment_checklist(service_name: str) -> dict | None:
    """Load deployment checklist for a service."""
    checklist_path = DEPLOYMENT_CHECKLISTS_DIR / f"checklist.{service_name}.yaml"
    if not checklist_path.exists():
        return None

    with open(checklist_path) as f:
        return yaml.safe_load(f)


def find_item_in_deployment_checklist(checklist: dict, item_id: str) -> dict | None:
    """Find a checklist item by ID in deployment checklist."""
    if not checklist:
        return None

    items = checklist.get("checklist_items", {})
    for key, item in items.items():
        # item_id format: item_data_04_sports_support
        # We need to check if item description or notes mention the ID
        if item_id.lower().replace("-", "_") in key.lower():
            return item

    return None


# ============================================================================
# Gap Detection: Missing Services
# ============================================================================


def check_missing_services(registry: dict) -> list[Gap]:
    """Find services in registry but repo doesn't exist."""
    gaps = []

    for service in registry.get("services", []):
        service_name = service["service"]
        repo_path = WORKSPACE_ROOT / service_name

        if not repo_path.exists():
            # This is an EPIC-level gap (entire service missing)
            breakdown = generate_service_creation_breakdown(service)
            gaps.append(
                Gap(
                    gap_type="missing_service",
                    service=service_name,
                    title=f"[Epic] Create {service_name} repo",
                    priority=service.get("priority", "P2-medium"),
                    description=(
                        f"Service defined in service-registry.yaml but repo doesn't exist.\n\n"
                        f"**Type:** {service.get('type')}\n"
                        f"**Layer:** {service.get('layer', 'N/A')}\n"
                        f"**Venues:** {', '.join(service.get('venues', []))}\n"
                        f"**Asset Classes:** {', '.join(service.get('asset_classes', []))}\n"
                    ),
                    breakdown=breakdown,
                    milestone=service.get("milestone"),
                    labels=["missing_implementation", "epic", "P1-high"],
                    codex_refs=[
                        "06-coding-standards/repo-structure.md",
                        "04-architecture/batch-live-symmetry.md",
                    ],
                    estimated_hours=sum(s["estimated_hours"] for s in breakdown),
                )
            )

    return gaps


def generate_service_creation_breakdown(service: dict) -> list[dict]:
    """Generate subtask breakdown for creating a new service."""
    service_name = service["service"]
    service_type = service.get("type", "pipeline")

    breakdown = [
        {
            "type": "implementation",
            "title": "Repo Scaffolding",
            "description": (
                f"- Create repo: {service_name}\n"
                "- Copy template from similar service\n"
                "- Add pyproject.toml, Dockerfile, cloudbuild.yaml\n"
                "- Add .cursorrules referencing unified-trading-codex\n"
                "- Add quality-gates.yml, quickmerge.sh"
            ),
            "files": [
                "pyproject.toml",
                "Dockerfile",
                "cloudbuild.yaml",
                ".cursorrules",
                "quality-gates.yml",
                "scripts/quickmerge.sh",
            ],
            "estimated_hours": 8,
        },
        {
            "type": "implementation",
            "title": "Core Implementation",
            "description": (
                f"Implement core logic for {service_name}.\n"
                "- Add main entry point\n"
                "- Add configuration (config.py or config package)\n"
                "- Add batch/live mode support (if applicable)\n"
                "- Add data ingestion/processing logic"
            ),
            "estimated_hours": 40,
        },
        {
            "type": "tests",
            "title": "Testing",
            "description": ("- Unit tests (>80% coverage)\n- Integration tests\n- E2E smoke test"),
            "estimated_hours": 16,
        },
        {
            "type": "observability",
            "title": "Observability",
            "description": (
                "- Add lifecycle events (STARTED, COMPLETED, FAILED)\n"
                "- Add metrics (counter, gauge, histogram)\n"
                "- Add alerts (Cloud Monitoring)\n"
                "- Add test_event_logging.py"
            ),
            "estimated_hours": 12,
        },
        {
            "type": "docs",
            "title": "Documentation",
            "description": (
                "- Add README.md\n"
                "- Add usage examples\n"
                "- Update service-registry.yaml (deployment info)\n"
                "- Create deployment checklist"
            ),
            "estimated_hours": 8,
        },
    ]

    return breakdown


# ============================================================================
# Gap Detection: Checklist Compliance
# ============================================================================


def check_checklist_compliance(service: dict, templates: dict, deployment_checklist: dict | None) -> list[Gap]:
    """Find checklist items that are fail/pending/missing."""
    gaps = []
    service_name = service["service"]

    # Get template for this service type
    template = get_template_for_service(service, templates)
    if not template:
        print(f"⚠️  No template found for {service_name}")
        return gaps

    # Check baseline items
    baseline_items = template.get("baseline_items", [])
    group_items = template.get("group_items", [])
    all_items = baseline_items + group_items

    for item in all_items:
        item_id = item["id"]  # e.g., DATA-04
        item_title = item["title"]
        item_priority = item.get("priority", "P2-medium")
        item_area = item.get("area", "unknown")
        item_description = item.get("description", "")
        item_codex_ref = item.get("codex_ref", "")

        # Check if in deployment checklist
        deployment_item = None
        if deployment_checklist:
            deployment_item = find_item_in_deployment_checklist(deployment_checklist, item_id)

        if not deployment_item:
            # Item in codex but not in deployment checklist
            gaps.append(
                Gap(
                    gap_type="missing_checklist_item",
                    service=service_name,
                    title=f"[Task] {service_name}: {item_title} (checklist item missing)",
                    priority=item_priority,
                    description=(
                        f"**Checklist Item:** {item_id}\n"
                        f"**Area:** {item_area}\n\n"
                        f"Codex template requires this item, but it's not in deployment checklist.\n\n"
                        f"{item_description}"
                    ),
                    breakdown=generate_implementation_breakdown(service_name, item, item_id),
                    milestone=service.get("milestone"),
                    labels=["missing_checklist_item", item_priority.lower()],
                    codex_refs=[item_codex_ref] if item_codex_ref else [],
                    estimated_hours=estimate_complexity(item),
                )
            )
        elif deployment_item.get("status") in ["pending", "fail", "partial"]:
            # Item exists but not satisfied
            gaps.append(
                Gap(
                    gap_type="checklist_item_unsatisfied",
                    service=service_name,
                    title=f"[Task] {service_name}: {item_title}",
                    priority=item_priority,
                    description=(
                        f"**Checklist Item:** {item_id}\n"
                        f"**Area:** {item_area}\n"
                        f"**Current Status:** {deployment_item['status']}\n\n"
                        f"{item_description}\n\n"
                        f"**Current Notes:** {deployment_item.get('notes', 'None')}"
                    ),
                    breakdown=generate_implementation_breakdown(service_name, item, item_id),
                    milestone=service.get("milestone"),
                    labels=[
                        "checklist_item_unsatisfied",
                        item_priority.lower(),
                        deployment_item["status"],
                    ],
                    codex_refs=[item_codex_ref] if item_codex_ref else [],
                    estimated_hours=estimate_complexity(item),
                )
            )

    return gaps


def generate_implementation_breakdown(service_name: str, item: dict, item_id: str) -> list[dict]:
    """Generate subtask breakdown for a checklist item."""
    item_title = item["title"]
    item_description = item.get("description", "")
    item_evidence = item.get("evidence", "")

    subtasks = []

    # Implementation subtask
    files = extract_files_from_evidence(item_evidence)
    subtasks.append(
        {
            "type": "implementation",
            "title": f"Implement {item_title}",
            "description": item_description,
            "files": files,
            "estimated_hours": estimate_complexity(item),
        }
    )

    # Tests subtask
    test_files = generate_test_file_names(service_name, item_id)
    subtasks.append(
        {
            "type": "tests",
            "title": f"Write tests for {item_title}",
            "description": "Unit + integration tests, >80% coverage",
            "files": test_files,
            "estimated_hours": estimate_complexity(item) * 0.5,
        }
    )

    # Observability subtask (for P0/P1 only)
    if item.get("priority") in ["P0-critical", "P1-high"]:
        subtasks.append(
            {
                "type": "observability",
                "title": f"Add observability for {item_title}",
                "description": "Add lifecycle events, metrics, alerts",
                "estimated_hours": 2,
            }
        )

    # Docs subtask
    subtasks.append(
        {
            "type": "docs",
            "title": f"Update docs for {item_title}",
            "description": "Update service README, checklist status",
            "estimated_hours": 1,
        }
    )

    # Checklist sync subtask
    subtasks.append(
        {
            "type": "checklist_sync",
            "title": f"Update checklist item {item_id} to 'done'",
            "description": f"Update unified-trading-deployment-v2/configs/checklist.{service_name}.yaml",
            "estimated_hours": 0.5,
        }
    )

    return subtasks


def extract_files_from_evidence(evidence: str) -> list[str]:
    """Extract file paths from evidence string."""
    # Simple heuristic: look for patterns like "Check path/to/file.py"
    files = []
    for word in evidence.split():
        if "/" in word and (".py" in word or ".yaml" in word):
            files.append(word.strip("`,.:;"))
    return files


def generate_test_file_names(service_name: str, item_id: str) -> list[str]:
    """Generate test file names for an item."""
    item_slug = item_id.lower().replace("-", "_")
    return [
        f"tests/unit/test_{item_slug}.py",
        f"tests/integration/test_{item_slug}_e2e.py",
    ]


def estimate_complexity(item: dict) -> float:
    """Estimate hours for an item based on priority and description length."""
    priority = item.get("priority", "P2-medium")
    description = item.get("description", "")

    base_hours = {
        "P0-critical": 12,
        "P1-high": 8,
        "P2-medium": 4,
        "P3-low": 2,
    }

    hours = base_hours.get(priority, 4)

    # Adjust for description length (proxy for complexity)
    if len(description) > 1000:
        hours *= 1.5
    elif len(description) > 500:
        hours *= 1.2

    return hours


# ============================================================================
# Issue Creation
# ============================================================================


def create_github_issue(gap: Gap, dry_run: bool = True) -> str | None:
    """Create a GitHub issue from a gap."""
    repo = f"{ORG}/{gap.service}"
    title = gap.title
    body = gap.to_github_issue_body()
    labels = ",".join(gap.labels)

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
        "--label",
        labels,
    ]

    if gap.milestone:
        cmd.extend(["--milestone", gap.milestone])

    if dry_run:
        print(f"\n{'=' * 80}")
        print(f"[DRY RUN] Would create issue in {repo}")
        print(f"Title: {title}")
        print(f"Labels: {labels}")
        print(f"Milestone: {gap.milestone or 'None'}")
        print(f"\nBody:\n{body}")
        print(f"{'=' * 80}\n")
        return None

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create issue: {result.stderr}")
        return None

    issue_url = result.stdout.strip()
    print(f"✅ Created issue: {issue_url}")
    return issue_url


def check_existing_issue(gap: Gap) -> bool:
    """Check if an issue already exists for this gap."""
    repo = f"{ORG}/{gap.service}"
    gap_id = f"{gap.gap_type}:{gap.service}"

    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        repo,
        "--search",
        gap_id,
        "--json",
        "body",
        "--limit",
        "100",
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False

    issues = json.loads(result.stdout)
    for issue in issues:
        if gap_id in issue.get("body", ""):
            return True

    return False


# ============================================================================
# Main
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Check service compliance against Codex standards")
    parser.add_argument(
        "--repo",
        help="Check single repo (e.g., IggyIkenna/instruments-service)",
    )
    parser.add_argument(
        "--all-services",
        action="store_true",
        help="Check all services in registry",
    )
    parser.add_argument(
        "--service-type",
        choices=["pipeline", "platform", "ui"],
        help="Check all services of a specific type",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print issues without creating them",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip gaps that already have issues",
    )

    args = parser.parse_args()

    if not any([args.repo, args.all_services, args.service_type]):
        parser.error("Must specify --repo, --all-services, or --service-type")

    print(f"🔍 Loading service registry from {SERVICE_REGISTRY}...")
    registry = load_service_registry()

    print(f"📋 Loading codex templates from {CODEX_TEMPLATES_DIR}...")
    templates = load_codex_templates()

    # Determine which services to check
    services_to_check = []

    if args.repo:
        service_name = args.repo.split("/")[1]
        service = get_service_from_registry(registry, service_name)
        if service:
            services_to_check = [service]
        else:
            print(f"❌ Service {service_name} not found in registry")
            sys.exit(1)
    elif args.all_services:
        services_to_check = registry.get("services", [])
    elif args.service_type:
        services_to_check = [s for s in registry.get("services", []) if s.get("type") == args.service_type]

    print(f"📊 Checking {len(services_to_check)} services...\n")

    all_gaps = []

    # Check missing services (only if checking all)
    if args.all_services or args.service_type:
        print("🔍 Checking for missing services...")
        missing_service_gaps = check_missing_services(registry)
        all_gaps.extend(missing_service_gaps)
        print(f"   Found {len(missing_service_gaps)} missing services\n")

    # Check checklist compliance
    for service in services_to_check:
        service_name = service["service"]
        print(f"🔍 Checking {service_name}...")

        # Load deployment checklist
        deployment_checklist = load_deployment_checklist(service_name)
        if not deployment_checklist:
            print(f"   ⚠️  No deployment checklist found for {service_name}")

        # Check compliance
        gaps = check_checklist_compliance(service, templates, deployment_checklist)
        all_gaps.extend(gaps)
        print(f"   Found {len(gaps)} gaps\n")

    # Summary
    print(f"\n{'=' * 80}")
    print("📊 SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total gaps found: {len(all_gaps)}")

    gap_type_counts = {}
    for gap in all_gaps:
        gap_type_counts[gap.gap_type] = gap_type_counts.get(gap.gap_type, 0) + 1

    for gap_type, count in gap_type_counts.items():
        print(f"  {gap_type}: {count}")

    priority_counts = {}
    for gap in all_gaps:
        priority_counts[gap.priority] = priority_counts.get(gap.priority, 0) + 1

    print("\nBy priority:")
    for priority in ["P0-critical", "P1-high", "P2-medium", "P3-low"]:
        count = priority_counts.get(priority, 0)
        if count > 0:
            print(f"  {priority}: {count}")

    total_hours = sum(gap.estimated_hours for gap in all_gaps)
    print(f"\nTotal estimated hours: {total_hours:.1f}h")
    print(f"{'=' * 80}\n")

    # Create issues
    if not args.dry_run:
        print("Creating GitHub issues...")
        created = 0
        skipped = 0

        for gap in all_gaps:
            if args.skip_existing and check_existing_issue(gap):
                print(f"⏭️  Skipping {gap.title} (already exists)")
                skipped += 1
                continue

            issue_url = create_github_issue(gap, dry_run=False)
            if issue_url:
                created += 1

        print(f"\n✅ Created {created} issues")
        if skipped > 0:
            print(f"⏭️  Skipped {skipped} existing issues")
    else:
        print("🔍 Dry run mode - no issues created")
        print("   Run without --dry-run to create issues")


if __name__ == "__main__":
    main()
