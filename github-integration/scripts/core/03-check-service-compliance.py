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
from typing import cast

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

# Type aliases for clarity
ServiceDict = dict[str, object]
RegistryDict = dict[str, object]
TemplateDict = dict[str, object]
SubtaskDict = dict[str, object]
ChecklistDict = dict[str, object]
ItemDict = dict[str, object]


def _format_gap_subtasks(breakdown: list[SubtaskDict]) -> list[str]:
    """Format breakdown subtasks for GitHub issue body."""
    parts: list[str] = []
    if not breakdown:
        return parts
    parts.extend(["", "## Required Subtasks", ""])
    for subtask in breakdown:
        subtask_type = str(subtask.get("type", "task"))
        stitle = str(subtask.get("title", "Untitled"))
        desc = str(subtask.get("description", ""))
        hours = subtask.get("estimated_hours", 0)
        parts.append(f"### {stitle} ({hours}h)")
        parts.append(f"**Type:** {subtask_type}")
        if desc:
            parts.append(desc)
        parts.append("")
        if "files" in subtask:
            raw_files = subtask["files"]
            file_list: list[str] = cast(list[str], raw_files) if isinstance(raw_files, list) else []
            parts.append(f"**Files:** `{', '.join(file_list)}`")
            parts.append("")
    return parts


def _format_gap_codex_refs(codex_refs: list[str]) -> list[str]:
    """Format codex refs section for GitHub issue body."""
    if not codex_refs:
        return []
    parts: list[str] = ["", "## Codex References"]
    for ref in codex_refs:
        parts.append(f"- `{ref}`")
    return parts


def _format_gap_footer(gap_type: str, service: str, estimated_hours: float) -> list[str]:
    """Format footer section for GitHub issue body."""
    return [
        "",
        "## Success Criteria",
        "- [ ] All subtasks completed",
        "- [ ] Tests pass (>80% coverage)",
        "- [ ] Quality gates pass",
        "- [ ] Deployment checklist updated",
        "",
        "## Time Estimate",
        f"{estimated_hours:.1f} hours",
        "",
        f"<!-- gap-id: {gap_type}:{service} -->",
    ]


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
        breakdown: list[SubtaskDict],
        milestone: str | None = None,
        labels: list[str] | None = None,
        codex_refs: list[str] | None = None,
        estimated_hours: float = 0,
    ) -> None:
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
        body_parts: list[str] = [
            f"**Service:** `{self.service}`",
            f"**Priority:** {self.priority}",
            f"**Gap Type:** {self.gap_type}",
        ]
        if self.milestone:
            body_parts.append(f"**Milestone:** {self.milestone}")
        body_parts.extend(["", "## Context", self.description])
        body_parts.extend(_format_gap_subtasks(self.breakdown))
        body_parts.extend(_format_gap_codex_refs(self.codex_refs))
        body_parts.extend(_format_gap_footer(self.gap_type, self.service, self.estimated_hours))
        return "\n".join(body_parts)


# ============================================================================
# Service Registry
# ============================================================================


def load_service_registry() -> RegistryDict:
    """Load service registry."""
    with open(SERVICE_REGISTRY) as f:
        return cast(RegistryDict, yaml.safe_load(f))


def get_service_from_registry(registry: RegistryDict, service_name: str) -> ServiceDict | None:
    """Get service metadata from registry."""
    raw_services = registry.get("services") or []
    services: list[object] = cast(list[object], raw_services) if isinstance(raw_services, list) else []
    for svc in services:
        if isinstance(svc, dict):
            service: ServiceDict = cast(ServiceDict, svc)
            if service.get("service") == service_name:
                return service
    return None


# ============================================================================
# Codex Templates
# ============================================================================


def load_codex_templates() -> dict[str, TemplateDict]:
    """Load all codex templates from 10-audit/_service-*.yaml."""
    templates: dict[str, TemplateDict] = {}
    for path in CODEX_TEMPLATES_DIR.glob("_service-*.yaml"):
        with open(path) as f:
            data: TemplateDict = cast(TemplateDict, yaml.safe_load(f))
            template_name = path.stem  # e.g., _service-pipeline-data-io
            templates[template_name] = data
    return templates


def get_template_for_service(
    service: ServiceDict,
    templates: dict[str, TemplateDict],
) -> TemplateDict | None:
    """Get the appropriate codex template for a service."""
    service_type = str(service.get("type", ""))
    layer = str(service.get("layer", ""))

    template_key: str | None = None
    if service_type == "pipeline":
        # Map layer to template
        layer_map: dict[str, str] = {
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
        ui_category = str(service.get("ui_category", "observability"))
        template_key = f"_service-ui-{ui_category}"

    if template_key is None:
        return None
    return templates.get(template_key)


# ============================================================================
# Deployment Checklists
# ============================================================================


def load_deployment_checklist(service_name: str) -> ChecklistDict | None:
    """Load deployment checklist for a service."""
    checklist_path = DEPLOYMENT_CHECKLISTS_DIR / f"checklist.{service_name}.yaml"
    if not checklist_path.exists():
        return None

    with open(checklist_path) as f:
        return cast(ChecklistDict, yaml.safe_load(f))


def find_item_in_deployment_checklist(checklist: ChecklistDict, item_id: str) -> ItemDict | None:
    """Find a checklist item by ID in deployment checklist."""
    if not checklist:
        return None

    raw_items = checklist.get("checklist_items") or {}
    if not isinstance(raw_items, dict):
        return None
    items: dict[str, object] = cast(dict[str, object], raw_items)
    for key, item in items.items():
        # item_id format: item_data_04_sports_support
        # We need to check if item description or notes mention the ID
        if item_id.lower().replace("-", "_") in key.lower():
            return cast(ItemDict, item) if isinstance(item, dict) else None

    return None


# ============================================================================
# Gap Detection: Missing Services
# ============================================================================


def check_missing_services(registry: RegistryDict) -> list[Gap]:
    """Find services in registry but repo doesn't exist."""
    gaps: list[Gap] = []
    raw_services = registry.get("services") or []
    services: list[object] = cast(list[object], raw_services) if isinstance(raw_services, list) else []

    for svc in services:
        if not isinstance(svc, dict):
            continue
        service: ServiceDict = cast(ServiceDict, svc)
        service_name = str(service.get("service", ""))
        repo_path = WORKSPACE_ROOT / service_name

        if not repo_path.exists():
            # This is an EPIC-level gap (entire service missing)
            breakdown = generate_service_creation_breakdown(service)
            raw_venues = service.get("venues") or []
            venues: list[str] = cast(list[str], raw_venues) if isinstance(raw_venues, list) else []
            raw_asset_classes = service.get("asset_classes") or []
            asset_classes: list[str] = cast(list[str], raw_asset_classes) if isinstance(raw_asset_classes, list) else []
            gaps.append(
                Gap(
                    gap_type="missing_service",
                    service=service_name,
                    title=f"[Epic] Create {service_name} repo",
                    priority=str(service.get("priority", "P2-medium")),
                    description=(
                        f"Service defined in service-registry.yaml but repo doesn't exist.\n\n"
                        f"**Type:** {service.get('type')}\n"
                        f"**Layer:** {service.get('layer', 'N/A')}\n"
                        f"**Venues:** {', '.join(venues)}\n"
                        f"**Asset Classes:** {', '.join(asset_classes)}\n"
                    ),
                    breakdown=breakdown,
                    milestone=str(service.get("milestone", "")) or None,
                    labels=["missing_implementation", "epic", "P1-high"],
                    codex_refs=[
                        "06-coding-standards/repo-structure.md",
                        "04-architecture/batch-live-symmetry.md",
                    ],
                    estimated_hours=sum(
                        float(cast(int | float, s.get("estimated_hours", 0)))
                        if isinstance(s.get("estimated_hours"), (int, float))
                        else 0
                        for s in breakdown
                    ),
                )
            )

    return gaps


def generate_service_creation_breakdown(service: ServiceDict) -> list[SubtaskDict]:
    """Generate subtask breakdown for creating a new service."""
    service_name = str(service.get("service", ""))

    breakdown: list[SubtaskDict] = [
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
            "description": "- Unit tests (>80% coverage)\n- Integration tests\n- E2E smoke test",
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


def check_checklist_compliance(
    service: ServiceDict,
    templates: dict[str, TemplateDict],
    deployment_checklist: ChecklistDict | None,
) -> list[Gap]:
    """Find checklist items that are fail/pending/missing."""
    gaps: list[Gap] = []
    service_name = str(service.get("service", ""))

    # Get template for this service type
    template = get_template_for_service(service, templates)
    if not template:
        print(f"  No template found for {service_name}")
        return gaps

    # Check baseline items
    raw_baseline = template.get("baseline_items") or []
    baseline_items: list[object] = cast(list[object], raw_baseline) if isinstance(raw_baseline, list) else []
    raw_group = template.get("group_items") or []
    group_items: list[object] = cast(list[object], raw_group) if isinstance(raw_group, list) else []
    all_items: list[object] = [*baseline_items, *group_items]

    for raw_item in all_items:
        if not isinstance(raw_item, dict):
            continue
        item: ItemDict = cast(ItemDict, raw_item)
        item_id = str(item.get("id", ""))
        item_title = str(item.get("title", ""))
        item_priority = str(item.get("priority", "P2-medium"))
        item_area = str(item.get("area", "unknown"))
        item_description = str(item.get("description", ""))
        item_codex_ref = str(item.get("codex_ref", ""))

        # Check if in deployment checklist
        deployment_item: ItemDict | None = None
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
                    milestone=str(service.get("milestone", "")) or None,
                    labels=["missing_checklist_item", item_priority.lower()],
                    codex_refs=[item_codex_ref] if item_codex_ref else [],
                    estimated_hours=estimate_complexity(item),
                )
            )
        elif str(deployment_item.get("status", "")) in ["pending", "fail", "partial"]:
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
                        f"**Current Status:** {deployment_item.get('status')}\n\n"
                        f"{item_description}\n\n"
                        f"**Current Notes:** {deployment_item.get('notes', 'None')}"
                    ),
                    breakdown=generate_implementation_breakdown(service_name, item, item_id),
                    milestone=str(service.get("milestone", "")) or None,
                    labels=[
                        "checklist_item_unsatisfied",
                        item_priority.lower(),
                        str(deployment_item.get("status", "")),
                    ],
                    codex_refs=[item_codex_ref] if item_codex_ref else [],
                    estimated_hours=estimate_complexity(item),
                )
            )

    return gaps


def generate_implementation_breakdown(
    service_name: str,
    item: ItemDict,
    item_id: str,
) -> list[SubtaskDict]:
    """Generate subtask breakdown for a checklist item."""
    item_title = str(item.get("title", ""))
    item_description = str(item.get("description", ""))
    item_evidence = str(item.get("evidence", ""))

    subtasks: list[SubtaskDict] = []

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
    if str(item.get("priority", "")) in ["P0-critical", "P1-high"]:
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
            "description": (f"Update unified-trading-deployment-v2/configs/checklist.{service_name}.yaml"),
            "estimated_hours": 0.5,
        }
    )

    return subtasks


def extract_files_from_evidence(evidence: str) -> list[str]:
    """Extract file paths from evidence string."""
    # Simple heuristic: look for patterns like "Check path/to/file.py"
    files: list[str] = []
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


def estimate_complexity(item: ItemDict) -> float:
    """Estimate hours for an item based on priority and description length."""
    priority = str(item.get("priority", "P2-medium"))
    description = str(item.get("description", ""))

    base_hours: dict[str, int] = {
        "P0-critical": 12,
        "P1-high": 8,
        "P2-medium": 4,
        "P3-low": 2,
    }

    hours = float(base_hours.get(priority, 4))

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

    cmd: list[str] = [
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

    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to create issue: {result.stderr}")
        return None

    issue_url = result.stdout.strip()
    print(f"Created issue: {issue_url}")
    return issue_url


def check_existing_issue(gap: Gap) -> bool:
    """Check if an issue already exists for this gap."""
    repo = f"{ORG}/{gap.service}"
    gap_id = f"{gap.gap_type}:{gap.service}"

    cmd: list[str] = [
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

    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return False

    issues: list[dict[str, object]] = cast(list[dict[str, object]], json.loads(result.stdout))
    for issue in issues:
        if gap_id in str(issue.get("body", "")):
            return True

    return False


# ============================================================================
# Main
# ============================================================================


def _parse_compliance_args() -> argparse.Namespace:
    """Parse and validate CLI arguments."""
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
    parsed = parser.parse_args()
    repo_arg = str(getattr(parsed, "repo", "") or "")
    all_services = bool(getattr(parsed, "all_services", False))
    service_type_arg = str(getattr(parsed, "service_type", "") or "")
    if not any([repo_arg, all_services, service_type_arg]):
        parser.error("Must specify --repo, --all-services, or --service-type")
    return parsed


def _resolve_services_to_check(parsed: argparse.Namespace, registry: RegistryDict) -> list[ServiceDict]:
    """Resolve which services to check from parsed args and registry."""
    repo_arg = str(getattr(parsed, "repo", "") or "")
    all_services = bool(getattr(parsed, "all_services", False))
    service_type_arg = str(getattr(parsed, "service_type", "") or "")

    if repo_arg:
        svc_name = repo_arg.split("/")[1]
        svc = get_service_from_registry(registry, svc_name)
        if svc:
            return [svc]
        print(f"Service {svc_name} not found in registry")
        sys.exit(1)

    raw_svcs = registry.get("services") or []
    svcs_list: list[object] = cast(list[object], raw_svcs) if isinstance(raw_svcs, list) else []

    if all_services:
        return [cast(ServiceDict, s) for s in svcs_list if isinstance(s, dict)]

    if service_type_arg:
        return [
            cast(ServiceDict, s)
            for s in svcs_list
            if isinstance(s, dict) and cast(ServiceDict, s).get("type") == service_type_arg
        ]

    return []


def _print_compliance_summary(all_gaps: list[Gap]) -> None:
    """Print compliance gap summary to stdout."""
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total gaps found: {len(all_gaps)}")

    gap_type_counts: dict[str, int] = {}
    for gap in all_gaps:
        gap_type_counts[gap.gap_type] = gap_type_counts.get(gap.gap_type, 0) + 1
    for gap_type, count in gap_type_counts.items():
        print(f"  {gap_type}: {count}")

    priority_counts: dict[str, int] = {}
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


def _create_issues_from_gaps(
    all_gaps: list[Gap],
    dry_run: bool,
    skip_existing: bool,
) -> None:
    """Create GitHub issues from gaps (or dry-run)."""
    if not dry_run:
        print("Creating GitHub issues...")
        created = 0
        skipped = 0
        for gap in all_gaps:
            if skip_existing and check_existing_issue(gap):
                print(f"Skipping {gap.title} (already exists)")
                skipped += 1
                continue
            issue_url = create_github_issue(gap, dry_run=False)
            if issue_url:
                created += 1
        print(f"\nCreated {created} issues")
        if skipped > 0:
            print(f"Skipped {skipped} existing issues")
    else:
        print("Dry run mode - no issues created")
        print("   Run without --dry-run to create issues")


def main() -> None:
    parsed = _parse_compliance_args()
    dry_run = bool(getattr(parsed, "dry_run", False))
    skip_existing = bool(getattr(parsed, "skip_existing", False))
    all_services = bool(getattr(parsed, "all_services", False))
    service_type_arg = str(getattr(parsed, "service_type", "") or "")

    print(f"Loading service registry from {SERVICE_REGISTRY}...")
    registry = load_service_registry()

    print(f"Loading codex templates from {CODEX_TEMPLATES_DIR}...")
    templates = load_codex_templates()

    services_to_check = _resolve_services_to_check(parsed, registry)
    print(f"Checking {len(services_to_check)} services...\n")

    all_gaps: list[Gap] = []

    if all_services or service_type_arg:
        print("Checking for missing services...")
        missing_service_gaps = check_missing_services(registry)
        all_gaps.extend(missing_service_gaps)
        print(f"   Found {len(missing_service_gaps)} missing services\n")

    for service in services_to_check:
        svc_name_str = str(service.get("service", ""))
        print(f"Checking {svc_name_str}...")
        deployment_checklist = load_deployment_checklist(svc_name_str)
        if not deployment_checklist:
            print(f"   No deployment checklist found for {svc_name_str}")
        gaps = check_checklist_compliance(service, templates, deployment_checklist)
        all_gaps.extend(gaps)
        print(f"   Found {len(gaps)} gaps\n")

    _print_compliance_summary(all_gaps)
    _create_issues_from_gaps(all_gaps, dry_run, skip_existing)


if __name__ == "__main__":
    main()
