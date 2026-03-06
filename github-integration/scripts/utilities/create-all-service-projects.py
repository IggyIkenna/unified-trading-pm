#!/usr/bin/env python3
"""
Create All Service-Level Projects

This script creates one GitHub project per service (32 total) with:
  - Filtered views for work items, CODs, Waves, Epics
  - Label-based dual attachment (CODs + Waves appear in multiple projects)
  - Idempotent operation (checks if project exists)

Features:
  - Reads service-registry.yaml for canonical service list
  - Creates projects with custom fields (Status, Priority)
  - Sets up filtered views automatically
  - Batched operations for efficiency
  - Dry-run mode for testing

Usage:
    # Create all 32 service projects
    python3 create-all-service-projects.py --all-services --dry-run
    python3 create-all-service-projects.py --all-services

    # Create single service project
    python3 create-all-service-projects.py --service execution-service

    # With custom views
    python3 create-all-service-projects.py --all-services --views "work,cods,waves"
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import cast

import yaml

# Type alias
JsonDict = dict[str, object]

# ==============================================================================
# Constants
# ==============================================================================

CODEX_ROOT: Path = Path(__file__).resolve().parents[4]
SERVICE_REGISTRY: Path = CODEX_ROOT / "11-project-management" / "service-registry.yaml"
DEFAULT_ORG = "IggyIkenna"

# View configurations
VIEWS: dict[str, dict[str, str]] = {
    "work": {"name": "Work Items", "filter": "-label:cod", "description": "All work items except CODs"},
    "cods": {"name": "CODs Only", "filter": "label:cod", "description": "Code-Owned Debt issues"},
    "waves": {"name": "Wave 1 Items", "filter": "milestone:Wave1", "description": "Wave 1 milestone items"},
    "epics": {"name": "Epics Only", "filter": "label:epic -label:cod", "description": "Epic-level issues"},
}


# ==============================================================================
# Color Logging
# ==============================================================================


class Colors:
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"


def log_info(msg: str) -> None:
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")


def log_success(msg: str) -> None:
    print(f"{Colors.GREEN}[OK]{Colors.NC} {msg}")


def log_warning(msg: str) -> None:
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")


def log_error(msg: str) -> None:
    print(f"{Colors.RED}[ERR]{Colors.NC} {msg}")


# ==============================================================================
# Service Registry Parsing
# ==============================================================================


def load_service_registry() -> list[JsonDict]:
    """Load and parse service-registry.yaml."""
    if not SERVICE_REGISTRY.exists():
        log_error(f"Service registry not found: {SERVICE_REGISTRY}")
        sys.exit(1)

    with open(SERVICE_REGISTRY, "r") as f:
        data: JsonDict = cast(JsonDict, yaml.safe_load(f) or {})

    raw_services: object = data.get("services") or []
    services: list[JsonDict] = (
        [cast(JsonDict, s) for s in cast(list[object], raw_services) if isinstance(s, dict)]
        if isinstance(raw_services, list)
        else []
    )
    log_info(f"Loaded {len(services)} services from registry")
    return services


def get_service_by_name(services: list[JsonDict], name: str) -> JsonDict | None:
    """Get single service by name."""
    for service in services:
        if str(service.get("service", "")) == name:
            return service
    return None


# ==============================================================================
# GitHub API Helpers
# ==============================================================================


def run_gh_command(cmd: str, capture_output: bool = True) -> subprocess.CompletedProcess[str]:
    """Run gh CLI command with error handling."""
    # Split command string into list to avoid shell=True vulnerability
    cmd_list: list[str] = cmd.split()
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd_list,
            check=True,
            capture_output=capture_output,
            text=True,
        )
        return result
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {' '.join(cmd_list)}")
        raw_stderr: object = getattr(e, "stderr", None)
        log_error(f"Error: {raw_stderr if capture_output else str(e)}")
        raise


def get_user_node_id(org: str) -> str:
    """Get GitHub user node ID for project creation."""
    _ = org  # Used for context
    cmd: str = "gh api user -q .node_id"
    result: subprocess.CompletedProcess[str] = run_gh_command(cmd)
    return result.stdout.strip()


def check_project_exists(org: str, project_name: str) -> int | None:
    """
    Check if project already exists.

    Returns:
        Project number if exists, None otherwise
    """
    cmd: str = f"gh project list --owner {org} --limit 100"
    result: subprocess.CompletedProcess[str] = run_gh_command(cmd)

    for line in result.stdout.strip().split("\n"):
        parts: list[str] = line.split("\t")
        if len(parts) >= 2:
            number: str = parts[0].strip()
            title: str = parts[1].strip()
            if title == project_name:
                return int(number)

    return None


# ==============================================================================
# Project Creation
# ==============================================================================


def create_project(org: str, project_name: str, dry_run: bool = False) -> str | None:
    """
    Create GitHub project using GraphQL API.

    Returns:
        Project ID if created, None if dry-run or error
    """
    if dry_run:
        log_info(f"[DRY-RUN] Would create project: {project_name}")
        return None

    # Check if already exists
    existing: int | None = check_project_exists(org, project_name)
    if existing:
        log_warning(f"Project '{project_name}' already exists (#{existing})")
        return None

    # Get owner node ID
    owner_id: str = get_user_node_id(org)

    # Create project using GraphQL
    query: str = f'''
    mutation {{
      createProjectV2(input: {{
        ownerId: "{owner_id}"
        title: "{project_name}"
      }}) {{
        projectV2 {{
          id
          number
          url
        }}
      }}
    }}
    '''

    cmd: str = f"gh api graphql -f query='{query}'"
    result: subprocess.CompletedProcess[str] = run_gh_command(cmd)

    data: JsonDict = cast(JsonDict, json.loads(result.stdout))
    data_field: JsonDict = cast(JsonDict, cast(JsonDict, data.get("data") or {}).get("createProjectV2") or {})
    project_v2: JsonDict = cast(JsonDict, data_field.get("projectV2") or {})
    project_id: str = str(project_v2.get("id", ""))
    project_number: str = str(project_v2.get("number", ""))
    project_url: str = str(project_v2.get("url", ""))

    log_success(f"Created project #{project_number}: {project_name}")
    log_info(f"URL: {project_url}")

    return project_id


def add_custom_fields(org: str, project_id: str, dry_run: bool = False) -> None:
    """Add custom fields to project (Status, Priority)."""
    _ = org  # Used for context
    if dry_run:
        log_info(f"[DRY-RUN] Would add custom fields to project {project_id}")
        return

    # Status field
    status_query: str = f'''
    mutation {{
      createProjectV2Field(input: {{
        projectId: "{project_id}"
        dataType: SINGLE_SELECT
        name: "Status"
        singleSelectOptions: [
          {{name: "Open", color: GRAY}}
          {{name: "Planned", color: BLUE}}
          {{name: "Implementing", color: YELLOW}}
          {{name: "Testing", color: ORANGE}}
          {{name: "Review", color: PURPLE}}
          {{name: "Completed", color: GREEN}}
        ]
      }}) {{
        projectV2Field {{ id }}
      }}
    }}
    '''

    cmd: str = f"gh api graphql -f query='{status_query}'"
    run_gh_command(cmd)
    log_success("Added Status field")

    # Priority field
    priority_query: str = f'''
    mutation {{
      createProjectV2Field(input: {{
        projectId: "{project_id}"
        dataType: SINGLE_SELECT
        name: "Priority"
        singleSelectOptions: [
          {{name: "P0-critical", color: RED}}
          {{name: "P1-high", color: ORANGE}}
          {{name: "P2-medium", color: YELLOW}}
          {{name: "P3-low", color: GREEN}}
        ]
      }}) {{
        projectV2Field {{ id }}
      }}
    }}
    '''

    cmd = f"gh api graphql -f query='{priority_query}'"
    run_gh_command(cmd)
    log_success("Added Priority field")


def setup_views(
    org: str,
    project_number: int,
    view_list: list[str],
    dry_run: bool = False,
) -> None:
    """Set up filtered views for project."""
    _ = org, project_number  # Used for context
    if dry_run:
        log_info(f"[DRY-RUN] Would set up views: {', '.join(view_list)}")
        return

    log_info(f"Setting up {len(view_list)} views...")

    for view_key in view_list:
        if view_key not in VIEWS:
            log_warning(f"Unknown view: {view_key}, skipping")
            continue

        view_config: dict[str, str] = VIEWS[view_key]
        log_info(f"Creating view: {view_config['name']}")
        log_info(f"  Filter: {view_config['filter']}")

        # Note: gh CLI doesn't support creating views via command line yet
        # This would require GraphQL mutations

    log_warning("NOTE: View creation not yet automated via gh CLI")
    log_info("Views must be created manually in GitHub UI:")
    for view_key in view_list:
        if view_key in VIEWS:
            vc: dict[str, str] = VIEWS[view_key]
            log_info(f"  - {vc['name']}: filter='{vc['filter']}'")


# ==============================================================================
# Main Processing
# ==============================================================================


def process_service(
    service: JsonDict,
    org: str,
    view_list: list[str],
    dry_run: bool,
) -> bool:
    """
    Create project for a single service.

    Returns:
        True if project was created, False if skipped
    """
    service_name: str = str(service.get("service", ""))
    service_type: str = str(service.get("type", ""))
    priority: str = str(service.get("priority", "P2-medium"))

    # Generate project name
    project_name_parts: list[str] = service_name.split("-")
    project_name: str = " ".join(word.capitalize() for word in project_name_parts)

    log_info(f"\n{'=' * 70}")
    log_info(f"Service: {service_name}")
    log_info(f"Type: {service_type}, Priority: {priority}")
    log_info(f"Project Name: {project_name}")
    log_info(f"{'=' * 70}")

    # Create project
    project_id: str | None = create_project(org, project_name, dry_run)

    if not project_id and not dry_run:
        # Project already exists or error occurred
        return False

    if dry_run:
        # In dry-run, simulate the rest
        log_info("[DRY-RUN] Would add custom fields")
        log_info(f"[DRY-RUN] Would set up {len(view_list)} views")
        return False

    # Add custom fields
    add_custom_fields(org, project_id or "", dry_run)

    # Set up views (not yet automated)
    log_info("\nRecommended Views:")
    for view_key in view_list:
        if view_key in VIEWS:
            vc: dict[str, str] = VIEWS[view_key]
            log_info(f"  - {vc['name']}: {vc['description']}")
            log_info(f"    Filter: {vc['filter']}")

    return True


# ==============================================================================
# Main CLI
# ==============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create service-level GitHub projects (32 total)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create all 32 service projects
  python3 create-all-service-projects.py --all-services --dry-run
  python3 create-all-service-projects.py --all-services

  # Create single service project
  python3 create-all-service-projects.py --service execution-service

  # With custom views
  python3 create-all-service-projects.py --all-services --views "work,cods,waves"
        """,
    )

    parser.add_argument("--service", type=str, help="Service name (e.g., execution-service)")
    parser.add_argument("--all-services", action="store_true", help="Create projects for all 32 services")
    parser.add_argument(
        "--org",
        type=str,
        default=DEFAULT_ORG,
        help=f"GitHub organization (default: {DEFAULT_ORG})",
    )
    parser.add_argument(
        "--views",
        type=str,
        default="work,cods,waves,epics",
        help="Comma-separated list of views to create (default: work,cods,waves,epics)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be created without creating projects",
    )

    parsed = parser.parse_args()

    service_arg: str = str(getattr(parsed, "service", "") or "")
    all_services_flag: bool = bool(getattr(parsed, "all_services", False))
    org: str = str(getattr(parsed, "org", DEFAULT_ORG))
    views_str: str = str(getattr(parsed, "views", "work,cods,waves,epics"))
    dry_run: bool = bool(getattr(parsed, "dry_run", False))

    # Validate arguments
    if not (service_arg or all_services_flag):
        parser.error("Must specify --service or --all-services")

    # Parse views
    view_list: list[str] = [v.strip() for v in views_str.split(",")]

    # Load services
    all_services: list[JsonDict] = load_service_registry()

    # Filter services
    services: list[JsonDict]
    if service_arg:
        service: JsonDict | None = get_service_by_name(all_services, service_arg)
        if not service:
            log_error(f"Service not found: {service_arg}")
            sys.exit(1)
        services = [service]
    else:
        services = all_services

    # Create projects
    log_info(f"\n{'=' * 70}")
    log_info(f"Creating projects for {len(services)} services")
    if dry_run:
        log_warning("DRY-RUN MODE: No projects will be created")
    log_info(f"Views: {', '.join(view_list)}")
    log_info(f"{'=' * 70}")

    created: int = 0
    skipped: int = 0

    for svc in services:
        if process_service(svc, org, view_list, dry_run):
            created += 1
        else:
            skipped += 1

    # Summary
    log_info(f"\n{'=' * 70}")
    log_info("SUMMARY")
    log_info(f"{'=' * 70}")
    log_success(f"Created: {created} projects")
    if skipped > 0:
        log_warning(f"Skipped: {skipped} projects (already exist or error)")
    log_info(f"Total Services: {len(services)}")
    log_info(f"{'=' * 70}")

    if not dry_run and created > 0:
        log_info("\nNEXT STEPS:")
        log_info("1. Manually create views in GitHub UI for each project")
        log_info("2. Configure project workflows (auto-add issues based on labels)")
        log_info("3. Test cross-cutting attachment (CODs + Waves)")


if __name__ == "__main__":
    main()
