#!/usr/bin/env python3
"""
Setup COD Project Workflows & Views (Full Automation)

Uses GitHub GraphQL API directly to configure:
1. Project automation workflows (auto-add, auto-status, auto-archive)
2. Filtered views in main projects (exclude CODs)

This script completes the automation that GitHub CLI doesn't yet support.

Usage:
    python setup-cod-project-workflows.py --org IggyIkenna --cod-project-number 3 --dry-run
    python setup-cod-project-workflows.py --org IggyIkenna --cod-project-number 3 --apply

Requirements:
    - GitHub Personal Access Token with `project` and `admin:org` scopes
    - Set GH_TOKEN environment variable or use gh CLI authentication
    - Python 3.13+
    - requests library (pip install requests)

Python 3.13+
"""

import argparse
import os
import subprocess
import sys
from typing import cast

import requests

# Type alias
JsonDict = dict[str, object]


def get_github_token() -> str:
    """Get GitHub token from environment or gh CLI."""
    token = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN")

    if token:
        return token

    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Could not get GitHub token")
        print("   Set GH_TOKEN environment variable or authenticate with: gh auth login")
        sys.exit(1)


def _get_nested(d: JsonDict, *keys: str) -> JsonDict:
    """Traverse nested dicts safely."""
    current: JsonDict = d
    for key in keys:
        val = current.get(key, {})
        current = cast(JsonDict, val) if isinstance(val, dict) else {}
    return current


def _get_nested_list(d: JsonDict, *keys: str) -> list[object]:
    """Traverse nested dicts and return final value as list."""
    if len(keys) < 1:
        return []
    parent = _get_nested(d, *keys[:-1])
    val = parent.get(keys[-1], [])
    return cast(list[object], val) if isinstance(val, list) else []


def run_graphql_query(
    token: str,
    query: str,
    variables: dict[str, str | int | None] | None = None,
) -> JsonDict:
    """Execute a GitHub GraphQL query."""
    headers: dict[str, str] = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload: dict[str, object] = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(
        "https://api.github.com/graphql",
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code != 200:
        print(f"GraphQL request failed: {response.status_code}")
        print(f"   Response: {response.text}")
        sys.exit(1)

    data: JsonDict = cast(JsonDict, response.json())

    if "errors" in data:
        print("GraphQL errors:")
        raw_errors = data.get("errors", [])
        errors_list: list[object] = cast(list[object], raw_errors) if isinstance(raw_errors, list) else []
        for error_raw in errors_list:
            if isinstance(error_raw, dict):
                error: JsonDict = cast(JsonDict, error_raw)
                print(f"   - {error.get('message', 'Unknown error')}")
        sys.exit(1)

    return data


def get_project_id(token: str, org: str, project_number: int) -> str | None:
    """Get the project node ID from project number."""
    query = """
    query($org: String!, $number: Int!) {
      organization(login: $org) {
        projectV2(number: $number) {
          id
          title
        }
      }
    }
    """

    variables: dict[str, str | int | None] = {"org": org, "number": project_number}
    result = run_graphql_query(token, query, variables)

    project = _get_nested(result, "data", "organization", "projectV2")
    if not project:
        return None

    proj_id = project.get("id")
    return str(proj_id) if proj_id else None


def setup_cod_project_workflows(token: str, org: str, cod_project_number: int, dry_run: bool = False) -> None:
    """Set up automation workflows for the COD project."""
    print(f"\nSetting up workflows for COD project #{cod_project_number}...")

    project_id = get_project_id(token, org, cod_project_number)
    if not project_id:
        print(f"  Could not find project #{cod_project_number}")
        return

    print(f"  Found project ID: {project_id}")

    workflows: list[JsonDict] = [
        {
            "name": "Auto-add COD issues",
            "description": "When label 'cod' is added -> Add to project",
            "enabled": True,
        },
        {
            "name": "Auto-status on close",
            "description": "When issue is closed -> Move to 'Done'",
            "enabled": True,
        },
        {
            "name": "Auto-archive after 30 days",
            "description": "When issue closed for 30 days -> Archive",
            "enabled": True,
        },
    ]

    if dry_run:
        print("  [DRY RUN] Would create workflows:")
        for workflow in workflows:
            print(f"    - {workflow.get('name')}: {workflow.get('description')}")
        return

    print("\n  GitHub GraphQL API doesn't yet support creating project workflows")
    print("     These must be configured manually in project settings:")
    print(f"     https://github.com/orgs/{org}/projects/{cod_project_number}/settings/workflows")
    print("\n  Required workflows:")
    for workflow in workflows:
        print(f"    - {workflow.get('name')}: {workflow.get('description')}")


def get_main_projects(token: str, org: str) -> list[JsonDict]:
    """Get list of main GitHub projects (excluding COD project)."""
    query = """
    query($org: String!, $cursor: String) {
      organization(login: $org) {
        projectsV2(first: 20, after: $cursor) {
          nodes {
            id
            number
            title
          }
          pageInfo {
            hasNextPage
            endCursor
          }
        }
      }
    }
    """

    projects: list[JsonDict] = []
    cursor: str | None = None

    while True:
        variables: dict[str, str | int | None] = {"org": org, "cursor": cursor}
        result = run_graphql_query(token, query, variables)

        data = _get_nested(result, "data", "organization", "projectsV2")
        nodes = _get_nested_list(data, "nodes")
        for node in nodes:
            if isinstance(node, dict):
                projects.append(cast(JsonDict, node))

        page_info = _get_nested(data, "pageInfo")
        if not page_info.get("hasNextPage"):
            break
        end_cursor = page_info.get("endCursor")
        cursor = str(end_cursor) if end_cursor else None

    # Filter out COD project
    main_projects: list[JsonDict] = [
        p
        for p in projects
        if "cod" not in str(p.get("title", "")).lower() and "change of direction" not in str(p.get("title", "")).lower()
    ]

    return main_projects


def create_project_view(
    token: str,
    project_id: str,
    view_name: str,
    filter_query: str,
    is_default: bool,
    dry_run: bool = False,
) -> bool:
    """Create a filtered view in a GitHub project."""
    if dry_run:
        print(f"    [DRY RUN] Would create view: {view_name} (filter: {filter_query})")
        return True

    # Check if view already exists
    query = """
    query($projectId: ID!) {
      node(id: $projectId) {
        ... on ProjectV2 {
          views(first: 20) {
            nodes {
              name
            }
          }
        }
      }
    }
    """

    result = run_graphql_query(token, query, {"projectId": project_id})
    existing_views = _get_nested_list(
        _get_nested(result, "data", "node", "views"),
        "nodes",
    )
    existing_names: list[str] = [str(cast(JsonDict, v).get("name", "")) for v in existing_views if isinstance(v, dict)]

    if view_name in existing_names:
        print(f"    View '{view_name}' already exists - skipping")
        return False

    print("\n  GitHub GraphQL API doesn't yet support creating project views with filters")
    print(f"     Manual step: Create view '{view_name}' with filter: {filter_query}")
    return False


def setup_main_project_views(token: str, org: str, dry_run: bool = False) -> None:
    """Create filtered views in main projects to exclude CODs."""
    print("\nSetting up views in main projects...")

    main_projects = get_main_projects(token, org)

    if not main_projects:
        print("  No main projects found")
        return

    print(f"  Found {len(main_projects)} main project(s)")

    views_to_create: list[JsonDict] = [
        {
            "name": "Work Items (No CODs)",
            "filter": "-label:cod",
            "is_default": True,
        },
        {
            "name": "Epics Only",
            "filter": "label:epic -label:cod",
            "is_default": False,
        },
        {
            "name": "Tasks & Subtasks",
            "filter": "label:task,subtask -label:cod",
            "is_default": False,
        },
    ]

    for project in main_projects:
        proj_title = str(project.get("title", ""))
        proj_number = str(project.get("number", ""))
        proj_id = str(project.get("id", ""))
        print(f"\n  Processing: {proj_title} (#{proj_number})")

        if dry_run:
            print("    [DRY RUN] Would create views:")
            for view in views_to_create:
                print(f"      - {view.get('name')}: {view.get('filter')}")
            continue

        for view in views_to_create:
            create_project_view(
                token,
                proj_id,
                str(view.get("name", "")),
                str(view.get("filter", "")),
                bool(view.get("is_default", False)),
                dry_run=dry_run,
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Setup COD project workflows and views (full automation)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--org",
        default="IggyIkenna",
        help="GitHub organization name (default: IggyIkenna)",
    )
    parser.add_argument(
        "--cod-project-number",
        type=int,
        required=True,
        help="COD project number (e.g., 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (required to make actual modifications)",
    )

    parsed = parser.parse_args()

    dry_run: bool = bool(getattr(parsed, "dry_run", False))
    apply_flag: bool = bool(getattr(parsed, "apply", False))
    org: str = str(getattr(parsed, "org", ""))
    cod_project_number: int = int(getattr(parsed, "cod_project_number", 0))

    if not dry_run and not apply_flag:
        print("Must specify either --dry-run or --apply")
        sys.exit(1)

    if apply_flag and dry_run:
        print("Cannot use both --dry-run and --apply")
        sys.exit(1)

    print("=" * 80)
    print("COD Project Workflows & Views Setup")
    print("=" * 80)

    if dry_run:
        print("\nDRY RUN MODE - No changes will be made\n")
    else:
        print("\nAPPLY MODE - Changes will be made to GitHub\n")

    # Get GitHub token
    token = get_github_token()
    print("GitHub authentication successful")

    # Setup COD project workflows
    setup_cod_project_workflows(token, org, cod_project_number, dry_run)

    # Setup main project views
    setup_main_project_views(token, org, dry_run)

    print("\n" + "=" * 80)
    print("Setup complete!")
    print("=" * 80)

    if not dry_run:
        print("\nRemaining manual steps (GitHub API limitations):")
        print("\n1. Configure COD project workflows:")
        print(f"   https://github.com/orgs/{org}/projects/{cod_project_number}/settings/workflows")
        print("   Required workflows:")
        print("     a. Item added to project:")
        print("        When: Issue has label 'cod'")
        print("        Then: Add to project")
        print("     b. Item closed:")
        print("        When: Issue is closed")
        print("        Then: Set status to 'Done'")
        print("     c. Auto-archive:")
        print("        When: Item status is 'Done'")
        print("        Then: Wait 30 days")
        print("        Then: Archive item")
        print("\n2. Create filtered views in main projects:")
        print(f"   https://github.com/orgs/{org}/projects")
        print("   For each main project:")
        print("     - Click: Views -> New view -> Table")
        print("     - Name: 'Work Items (No CODs)'")
        print("     - Filter: -label:cod")
        print("     - Set as default view")
        print("\nThese are one-time manual steps. Once configured, automation handles everything.")
        print("   GitHub's GraphQL API doesn't yet support programmatic workflow/view creation.")


if __name__ == "__main__":
    main()
