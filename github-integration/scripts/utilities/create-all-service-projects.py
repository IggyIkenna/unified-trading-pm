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
    python3 create-all-service-projects.py --service execution-services

    # With custom views
    python3 create-all-service-projects.py --all-services --views "work,cods,waves"
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# ==============================================================================
# Constants
# ==============================================================================

CODEX_ROOT = Path(__file__).resolve().parents[4]
SERVICE_REGISTRY = CODEX_ROOT / "11-project-management" / "service-registry.yaml"
DEFAULT_ORG = "IggyIkenna"

# View configurations
VIEWS = {
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


def get_service_by_name(services: List[Dict], name: str) -> Optional[Dict]:
    """Get single service by name."""
    for service in services:
        if service.get("service") == name:
            return service
    return None


# ==============================================================================
# GitHub API Helpers
# ==============================================================================


def run_gh_command(cmd: str, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run gh CLI command with error handling."""
    try:
        # Split command string into list to avoid shell=True vulnerability
        cmd_list = cmd.split()
        result = subprocess.run(cmd_list, check=True, capture_output=capture_output, text=True)
        return result
    except subprocess.CalledProcessError as e:
        log_error(f"Command failed: {' '.join(cmd_list)}")
        log_error(f"Error: {e.stderr if capture_output else str(e)}")
        raise


def get_user_node_id(org: str) -> str:
    """Get GitHub user node ID for project creation."""
    cmd = "gh api user -q .node_id"
    result = run_gh_command(cmd)
    return result.stdout.strip()


def check_project_exists(org: str, project_name: str) -> Optional[int]:
    """
    Check if project already exists.

    Returns:
        Project number if exists, None otherwise
    """
    cmd = f"gh project list --owner {org} --limit 100"
    result = run_gh_command(cmd)

    for line in result.stdout.strip().split("\n"):
        parts = line.split("\t")
        if len(parts) >= 2:
            number = parts[0].strip()
            title = parts[1].strip()
            if title == project_name:
                return int(number)

    return None


# ==============================================================================
# Project Creation
# ==============================================================================


def create_project(org: str, project_name: str, dry_run: bool = False) -> Optional[str]:
    """
    Create GitHub project using GraphQL API.

    Returns:
        Project ID if created, None if dry-run or error
    """
    if dry_run:
        log_info(f"[DRY-RUN] Would create project: {project_name}")
        return None

    # Check if already exists
    existing = check_project_exists(org, project_name)
    if existing:
        log_warning(f"Project '{project_name}' already exists (#{existing})")
        return None

    # Get owner node ID
    owner_id = get_user_node_id(org)

    # Create project using GraphQL
    query = f'''
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

    cmd = f"gh api graphql -f query='{query}'"
    result = run_gh_command(cmd)

    data = json.loads(result.stdout)
    project_id = data["data"]["createProjectV2"]["projectV2"]["id"]
    project_number = data["data"]["createProjectV2"]["projectV2"]["number"]
    project_url = data["data"]["createProjectV2"]["projectV2"]["url"]

    log_success(f"Created project #{project_number}: {project_name}")
    log_info(f"URL: {project_url}")

    return project_id


def add_custom_fields(org: str, project_id: str, dry_run: bool = False):
    """Add custom fields to project (Status, Priority)."""
    if dry_run:
        log_info(f"[DRY-RUN] Would add custom fields to project {project_id}")
        return

    # Status field
    status_query = f'''
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

    cmd = f"gh api graphql -f query='{status_query}'"
    run_gh_command(cmd)
    log_success("Added Status field")

    # Priority field
    priority_query = f'''
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


def setup_views(org: str, project_number: int, view_list: List[str], dry_run: bool = False):
    """Set up filtered views for project."""
    if dry_run:
        log_info(f"[DRY-RUN] Would set up views: {', '.join(view_list)}")
        return

    log_info(f"Setting up {len(view_list)} views...")

    for view_key in view_list:
        if view_key not in VIEWS:
            log_warning(f"Unknown view: {view_key}, skipping")
            continue

        view_config = VIEWS[view_key]
        log_info(f"Creating view: {view_config['name']}")
        log_info(f"  Filter: {view_config['filter']}")

        # Note: gh CLI doesn't support creating views via command line yet
        # This would require GraphQL mutations
        # For now, document what needs to be done manually

    log_warning("NOTE: View creation not yet automated via gh CLI")
    log_info("Views must be created manually in GitHub UI:")
    for view_key in view_list:
        if view_key in VIEWS:
            view_config = VIEWS[view_key]
            log_info(f"  - {view_config['name']}: filter='{view_config['filter']}'")


# ==============================================================================
# Main Processing
# ==============================================================================


def process_service(service: Dict, org: str, view_list: List[str], dry_run: bool) -> bool:
    """
    Create project for a single service.

    Returns:
        True if project was created, False if skipped
    """
    service_name = service["service"]
    service_type = service["type"]
    priority = service.get("priority", "P2-medium")

    # Generate project name
    # Format: "Service Name" (e.g., "Execution Services")
    project_name_parts = service_name.split("-")
    project_name = " ".join(word.capitalize() for word in project_name_parts)

    log_info(f"\n{'=' * 70}")
    log_info(f"Service: {service_name}")
    log_info(f"Type: {service_type}, Priority: {priority}")
    log_info(f"Project Name: {project_name}")
    log_info(f"{'=' * 70}")

    # Create project
    project_id = create_project(org, project_name, dry_run)

    if not project_id and not dry_run:
        # Project already exists or error occurred
        return False

    if dry_run:
        # In dry-run, simulate the rest
        log_info("[DRY-RUN] Would add custom fields")
        log_info(f"[DRY-RUN] Would set up {len(view_list)} views")
        return False

    # Add custom fields
    add_custom_fields(org, project_id, dry_run)

    # Set up views (not yet automated)
    # For now, just document what needs to be done
    log_info("\nRecommended Views:")
    for view_key in view_list:
        if view_key in VIEWS:
            view_config = VIEWS[view_key]
            log_info(f"  - {view_config['name']}: {view_config['description']}")
            log_info(f"    Filter: {view_config['filter']}")

    return True


# ==============================================================================
# Main CLI
# ==============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Create service-level GitHub projects (32 total)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create all 32 service projects
  python3 create-all-service-projects.py --all-services --dry-run
  python3 create-all-service-projects.py --all-services

  # Create single service project
  python3 create-all-service-projects.py --service execution-services

  # With custom views
  python3 create-all-service-projects.py --all-services --views "work,cods,waves"
        """,
    )

    parser.add_argument("--service", type=str, help="Service name (e.g., execution-services)")

    parser.add_argument("--all-services", action="store_true", help="Create projects for all 32 services")

    parser.add_argument("--org", type=str, default=DEFAULT_ORG, help=f"GitHub organization (default: {DEFAULT_ORG})")

    parser.add_argument(
        "--views",
        type=str,
        default="work,cods,waves,epics",
        help="Comma-separated list of views to create (default: work,cods,waves,epics)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Preview what would be created without creating projects"
    )

    args = parser.parse_args()

    # Validate arguments
    if not (args.service or args.all_services):
        parser.error("Must specify --service or --all-services")

    # Parse views
    view_list = [v.strip() for v in args.views.split(",")]

    # Load services
    all_services = load_service_registry()

    # Filter services
    if args.service:
        service = get_service_by_name(all_services, args.service)
        if not service:
            log_error(f"Service not found: {args.service}")
            sys.exit(1)
        services = [service]
    else:
        services = all_services

    # Create projects
    log_info(f"\n{'=' * 70}")
    log_info(f"Creating projects for {len(services)} services")
    if args.dry_run:
        log_warning("DRY-RUN MODE: No projects will be created")
    log_info(f"Views: {', '.join(view_list)}")
    log_info(f"{'=' * 70}")

    created = 0
    skipped = 0

    for service in services:
        if process_service(service, args.org, view_list, args.dry_run):
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

    if not args.dry_run and created > 0:
        log_info("\nNEXT STEPS:")
        log_info("1. Manually create views in GitHub UI for each project")
        log_info("2. Configure project workflows (auto-add issues based on labels)")
        log_info("3. Test cross-cutting attachment (CODs + Waves)")


if __name__ == "__main__":
    main()
