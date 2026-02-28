#!/usr/bin/env python3
"""
Setup COD (Change of Direction) Project

Organizes COD issues into a dedicated GitHub project to improve visibility
of epics, tasks, and subtasks in main projects.

Steps:
1. Create a GitHub project for CODs
2. Create/apply 'cod' label to existing COD issues
3. Add all COD issues to the new project
4. Set up automation rules in project settings
5. Update issue templates to include COD option
6. Create saved filters for main projects to exclude COD label

Usage:
    python setup-cod-project.py --org IggyIkenna --dry-run
    python setup-cod-project.py --org IggyIkenna --apply

Requirements:
    - GitHub CLI (`gh`) installed and authenticated
    - PyYAML for template updates
    - Admin access to the organization/repositories

Python 3.13+
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def run_gh_command(cmd: list[str], check: bool = True) -> dict[str, Any] | str | None:
    """Run a GitHub CLI command and return parsed JSON output."""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
        )

        # If command succeeded
        if result.returncode == 0:
            if result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return result.stdout.strip()
            return ""  # Success but no output

        # Command failed
        if not check:
            # Return error info as dict so caller can handle it
            return {"_error": True, "stderr": result.stderr.strip(), "returncode": result.returncode}

        return None

    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"   Error: {e.stderr}")
        if check:
            raise
        return None


def create_cod_label(org: str, repos: list[str], dry_run: bool = False) -> None:
    """Create 'cod' label in all repositories.

    Note: GitHub doesn't support batch label creation - must be done per-repo.
    """
    print("\n📋 Step 1: Creating 'cod' label...")
    print("  (Note: GitHub requires individual API calls per repo for label creation)")

    label_config = {
        "name": "cod",
        "description": "Change of Direction - architectural/design pivots tracked separately",
        "color": "d4c5f9",  # Light purple
    }

    skipped = 0
    created = 0
    existing = 0

    for repo in repos:
        print(f"  Processing {repo}...")

        # Check if repo has issues enabled
        test = run_gh_command(
            ["gh", "label", "list", "--repo", f"{org}/{repo}", "--json", "name", "--limit", "1"], check=False
        )

        if test is None:
            print("    ⚠️  Skipping (issues disabled or access denied)")
            skipped += 1
            continue

        # Check if label exists
        existing_labels = run_gh_command(
            ["gh", "label", "list", "--repo", f"{org}/{repo}", "--json", "name"], check=False
        )

        # Handle errors in listing labels
        if isinstance(existing_labels, dict) and existing_labels.get("_error"):
            print(f"    ⚠️  Skipping (error: {existing_labels.get('stderr', 'unknown')})")
            skipped += 1
            continue

        if existing_labels and any(label.get("name") == "cod" for label in existing_labels):
            if dry_run:
                print("    [DRY RUN] Label 'cod' already exists")
            else:
                print("    ✓ Label 'cod' already exists")
            existing += 1
            continue

        if dry_run:
            print(f"    [DRY RUN] Would create label: {label_config}")
            created += 1
            continue

        # Create label
        result = run_gh_command(
            [
                "gh",
                "label",
                "create",
                "cod",
                "--repo",
                f"{org}/{repo}",
                "--description",
                label_config["description"],
                "--color",
                label_config["color"],
            ],
            check=False,
        )

        # Handle result
        if isinstance(result, dict) and result.get("_error"):
            # Check if it's "already exists" error
            stderr = result.get("stderr", "")
            if "already exists" in stderr.lower():
                print("    ✓ Label 'cod' already exists")
                existing += 1
            else:
                print(f"    ⚠️  Failed: {stderr[:80]}")
                skipped += 1
        elif result is not None and result != "":
            print("    ✓ Created 'cod' label")
            created += 1
        else:
            print("    ✓ Created 'cod' label")
            created += 1

    mode = "[DRY RUN] " if dry_run else ""
    print(
        f"\n  {mode}Summary: {created} {'would be created' if dry_run else 'created'}, {existing} already exist, {skipped} skipped"
    )


def find_cod_issues(org: str, repos: list[str]) -> list[dict[str, Any]]:
    """Find all issues that mention COD in title or have 'change of direction' in body.

    Uses org-wide search to batch API calls (3 queries instead of repos * 3).
    """
    print("\n🔍 Step 2: Finding COD issues...")
    print("  Using batched org-wide search (faster, fewer API calls)...")

    cod_issues = []
    search_terms = [
        f"org:{org} COD in:title",
        f'org:{org} "change of direction" in:title',
        f'org:{org} "change-of-direction" in:title',
    ]

    for term in search_terms:
        print(f"  Searching: {term.split('org:')[1][:50]}...")

        result = run_gh_command(
            [
                "gh",
                "issue",
                "list",
                "--search",
                term,
                "--json",
                "number,title,url,labels",
                "--limit",
                "1000",
            ],
            check=False,
        )

        # Handle errors
        if isinstance(result, dict) and result.get("_error"):
            print(f"    ⚠️  Search failed: {result.get('stderr', 'unknown')[:80]}")
            continue

        if result and isinstance(result, list):
            print(f"    Found {len(result)} issues")
            for issue in result:
                # Parse repo name from URL: https://github.com/org/repo/issues/123
                repo_name = ""
                if issue.get("url"):
                    url_parts = issue["url"].split("/")
                    if len(url_parts) >= 5:
                        repo_name = url_parts[4]

                # Check if already labeled
                has_cod_label = any(label["name"] == "cod" for label in issue.get("labels", []))

                issue_info = {
                    "repo": repo_name,
                    "number": issue["number"],
                    "title": issue["title"],
                    "url": issue["url"],
                    "has_cod_label": has_cod_label,
                }

                # Avoid duplicates
                if not any(i["url"] == issue_info["url"] for i in cod_issues):
                    cod_issues.append(issue_info)

    print(f"\n  ✓ Found {len(cod_issues)} unique COD issues across {len(set(i['repo'] for i in cod_issues))} repos")
    print(f"    {sum(1 for i in cod_issues if not i['has_cod_label'])} need labeling")
    print(f"    API calls saved: ~{len(repos) * 3 - 3} (batched {len(repos) * 3} → 3 queries)")

    return cod_issues


def apply_cod_labels(org: str, cod_issues: list[dict[str, Any]], dry_run: bool = False) -> None:
    """Apply 'cod' label to all identified COD issues.

    Note: GitHub CLI requires individual API calls per issue for label edits.
    GraphQL mutations could batch this, but would add complexity.
    """
    print("\n🏷️  Step 3: Applying 'cod' labels...")

    unlabeled = [issue for issue in cod_issues if not issue["has_cod_label"]]

    if not unlabeled:
        print("  ✓ All COD issues already labeled")
        return

    print(f"  Labeling {len(unlabeled)} issues (individual API calls required)...")

    for idx, issue in enumerate(unlabeled, 1):
        if dry_run:
            if idx % 10 == 0 or idx <= 10:
                print(f"  [{idx}/{len(unlabeled)}] {issue['repo']}#{issue['number']}: {issue['title'][:50]}...")
                print("    [DRY RUN] Would add 'cod' label")
            continue

        result = run_gh_command(
            [
                "gh",
                "issue",
                "edit",
                str(issue["number"]),
                "--repo",
                f"{org}/{issue['repo']}",
                "--add-label",
                "cod",
            ],
            check=False,
        )

        # Handle result and show progress every 10 issues
        if isinstance(result, dict) and result.get("_error"):
            stderr = result.get("stderr", "")
            print(f"  [{idx}/{len(unlabeled)}] {issue['repo']}#{issue['number']}: ⚠️  Failed: {stderr[:60]}")
        else:
            if idx % 10 == 0:  # Show every 10th
                print(f"  [{idx}/{len(unlabeled)}] {issue['repo']}#{issue['number']}: ✓ Labeled")

    print(f"  ✓ Completed labeling {len(unlabeled)} issues")


def create_cod_project(org: str, dry_run: bool = False) -> str | None:
    """Create a GitHub project for COD issues."""
    print("\n📊 Step 4: Creating COD project...")

    project_title = "CODs (Change of Direction)"
    project_body = """
# Change of Direction Issues

This project tracks all COD (Change of Direction) issues across repositories.
These represent architectural pivots, design changes, and strategic redirections.

## Purpose
- Separate CODs from main epics/tasks/subtasks for better visibility
- Track architectural evolution and decision history
- Provide central view of all design pivots

## Workflow
1. Issues labeled with 'cod' are automatically added to this project
2. CODs are excluded from main project views via filters
3. Review CODs quarterly to assess impact and completion

---
Auto-managed by setup-cod-project.py
""".strip()

    if dry_run:
        print(f"  [DRY RUN] Would create project: '{project_title}'")
        print(f"  [DRY RUN] Description: {project_body[:100]}...")
        return "dry-run-project-id"

    # Check if project exists
    existing = run_gh_command(
        [
            "gh",
            "project",
            "list",
            "--owner",
            org,
            "--format",
            "json",
        ]
    )

    if existing:
        for project in existing.get("projects", []):
            if project.get("title") == project_title:
                print(f"  ✓ Project already exists: {project.get('url')}")
                return str(project.get("number"))

    # Create project
    result = run_gh_command(
        [
            "gh",
            "project",
            "create",
            "--owner",
            org,
            "--title",
            project_title,
            "--format",
            "json",
        ]
    )

    if result:
        project_number = result.get("number")
        print(f"  ✓ Created project #{project_number}")

        # Update description (requires separate API call via gh api)
        subprocess.run(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                f'query=mutation {{ updateProjectV2(input: {{projectId: "{result.get("id")}", readme: "{project_body}"}}) {{ projectV2 {{ id }} }} }}',
            ],
            check=False,
        )

        return str(project_number)

    return None


def add_issues_to_project(
    org: str, project_number: str, cod_issues: list[dict[str, Any]], dry_run: bool = False
) -> None:
    """Add all COD issues to the COD project.

    Note: GitHub requires individual API calls per issue to add to project.
    """
    print("\n➕ Step 5: Adding issues to COD project...")

    if dry_run:
        print(f"  [DRY RUN] Would add {len(cod_issues)} issues to project #{project_number}")
        for issue in cod_issues[:5]:
            print(f"    - {issue['repo']}#{issue['number']}: {issue['title'][:50]}...")
        if len(cod_issues) > 5:
            print(f"    ... and {len(cod_issues) - 5} more")
        return

    print(f"  Adding {len(cod_issues)} issues to project (individual API calls required)...")

    added = 0
    skipped = 0

    for idx, issue in enumerate(cod_issues, 1):
        result = run_gh_command(
            [
                "gh",
                "project",
                "item-add",
                project_number,
                "--owner",
                org,
                "--url",
                issue["url"],
            ],
            check=False,
        )

        # Handle result and show progress every 10 issues
        if isinstance(result, dict) and result.get("_error"):
            skipped += 1
            stderr = result.get("stderr", "")
            if "already exists" in stderr.lower():
                if idx % 10 == 0:
                    print(f"  [{idx}/{len(cod_issues)}] {issue['repo']}#{issue['number']}: ⚠️  Already in project")
            else:
                print(f"  [{idx}/{len(cod_issues)}] {issue['repo']}#{issue['number']}: ⚠️  {stderr[:60]}")
        else:
            added += 1
            if idx % 10 == 0:  # Show every 10th
                print(f"  [{idx}/{len(cod_issues)}] {issue['repo']}#{issue['number']}: ✓ Added")

    print(f"\n  ✓ Completed: {added} added, {skipped} skipped")


def setup_project_automation(org: str, project_number: str, dry_run: bool = False) -> None:
    """Set up automation rules for the COD project using GitHub GraphQL API."""
    print("\n⚙️  Step 6: Setting up project automation...")

    # Get project ID (needed for GraphQL)
    project_data = run_gh_command(
        [
            "gh",
            "project",
            "view",
            project_number,
            "--owner",
            org,
            "--format",
            "json",
        ],
        check=False,
    )

    if isinstance(project_data, dict) and project_data.get("_error"):
        print("  ⚠️  Could not fetch project details. Automation must be configured manually.")
        print(f"     https://github.com/orgs/{org}/projects/{project_number}/settings")
        return

    if dry_run:
        print("  [DRY RUN] Would configure automation rules:")
        print("    1. Auto-add: When 'cod' label is added → Add to project")
        print("    2. Auto-status: When issue is closed → Move to 'Done'")
        print("    3. Auto-archive: When issue closed for 30 days → Archive")
        return

    # GitHub Projects V2 automation via GraphQL
    # Note: GitHub doesn't provide full CLI support for workflow automation yet
    # We'll create the workflows using gh api with GraphQL

    print("  ✓ Configuring automation workflows via GraphQL...")

    workflows = [
        {
            "name": "Auto-add COD issues",
            "description": "Automatically add issues with 'cod' label to project",
            "enabled": True,
        },
        {
            "name": "Auto-status on close",
            "description": "Move to 'Done' when issue is closed",
            "enabled": True,
        },
        {
            "name": "Auto-archive after 30 days",
            "description": "Archive items closed for 30+ days",
            "enabled": True,
        },
    ]

    # For now, document the manual steps since GH CLI doesn't fully support workflow automation
    print("  ⚠️  Note: GitHub CLI doesn't yet support full project workflow automation")
    print("  ✓ Created project successfully. Configure automation rules manually:")
    print(f"     https://github.com/orgs/{org}/projects/{project_number}/settings/workflows")
    print("\n  Recommended automation rules:")
    print("    1. Item added to project: When issue has label 'cod' → Add to project")
    print("    2. Item closed: When issue is closed → Set status to 'Done'")
    print("    3. Auto-archive: When issue closed → Wait 30 days → Archive")
    print("\n  💡 These rules prevent manual maintenance and keep the project clean automatically.")


def create_issue_template_snippet() -> str:
    """Generate issue template snippet for COD option."""
    return """
## Issue Classification

- [ ] Epic
- [ ] Task
- [ ] Subtask
- [ ] COD (Change of Direction)

> **Note:** Select 'COD' for architectural pivots, design changes, or strategic redirections.
> CODs are tracked separately in the [COD Project](https://github.com/orgs/IggyIkenna/projects/COD_PROJECT_NUMBER).
"""


def update_issue_templates(repos_path: Path, dry_run: bool = False) -> None:
    """Update issue templates to include COD option."""
    print("\n📝 Step 7: Updating issue templates...")

    template_snippet = create_issue_template_snippet()

    if dry_run:
        print("  [DRY RUN] Would add this snippet to issue templates:")
        print(template_snippet)
        return

    # Search for issue template files
    template_patterns = [
        ".github/ISSUE_TEMPLATE/*.md",
        ".github/ISSUE_TEMPLATE.md",
    ]

    print("  💡 Manual step required:")
    print("     Add the following snippet to your issue templates:")
    print(template_snippet)


def get_main_projects(org: str) -> list[dict[str, Any]]:
    """Get list of main GitHub projects (excluding COD project)."""
    result = run_gh_command(
        [
            "gh",
            "project",
            "list",
            "--owner",
            org,
            "--format",
            "json",
            "--limit",
            "100",
        ],
        check=False,
    )

    if isinstance(result, dict) and result.get("_error"):
        print(f"  ⚠️  Could not fetch projects: {result.get('stderr', 'Unknown error')}")
        return []

    if not result or not isinstance(result, dict):
        return []

    # Filter out COD project
    projects = result.get("projects", [])
    main_projects = [
        p
        for p in projects
        if "cod" not in p.get("title", "").lower() and "change of direction" not in p.get("title", "").lower()
    ]

    return main_projects


def create_project_filters(org: str, project_number: str, project_title: str, dry_run: bool = False) -> None:
    """Create filtered views in a GitHub project to exclude CODs."""
    print(f"  Processing {project_title} (#{project_number})...")

    views_to_create = [
        {
            "name": "Work Items (No CODs)",
            "filter": "-label:cod",
            "description": "All work items excluding CODs",
            "default": True,
        },
        {
            "name": "Epics Only",
            "filter": "label:epic -label:cod",
            "description": "Epic-level items only",
            "default": False,
        },
        {
            "name": "Tasks & Subtasks",
            "filter": "label:task,subtask -label:cod",
            "description": "Task and subtask level items",
            "default": False,
        },
    ]

    if dry_run:
        print(f"    [DRY RUN] Would create {len(views_to_create)} filtered views")
        for view in views_to_create:
            print(f"      - {view['name']}: {view['filter']}")
        return

    # Get existing views
    existing_views_result = run_gh_command(
        [
            "gh",
            "project",
            "view",
            project_number,
            "--owner",
            org,
            "--format",
            "json",
        ],
        check=False,
    )

    existing_views = []
    if isinstance(existing_views_result, dict) and not existing_views_result.get("_error"):
        existing_views = [v.get("name", "") for v in existing_views_result.get("views", [])]

    created = 0
    skipped = 0

    for view_config in views_to_create:
        if view_config["name"] in existing_views:
            print(f"    ⚠️  View '{view_config['name']}' already exists - skipping")
            skipped += 1
            continue

        # Note: GitHub CLI doesn't yet support creating custom views with filters
        # This would require GraphQL API calls
        print(f"    ⚠️  View creation requires manual setup: '{view_config['name']}'")
        print(f"       Filter: {view_config['filter']}")
        skipped += 1

    if skipped > 0:
        print(f"    💡 Create views manually at: https://github.com/orgs/{org}/projects/{project_number}")


def setup_main_project_filters(org: str, dry_run: bool = False) -> None:
    """Set up filters in main projects to exclude COD label."""
    print("\n🔍 Step 8: Setting up filters in main projects...")

    main_projects = get_main_projects(org)

    if not main_projects:
        print("  ⚠️  No main projects found or unable to fetch projects")
        print(f"  💡  Configure filters manually at: https://github.com/orgs/{org}/projects")
        return

    print(f"  Found {len(main_projects)} main project(s)")

    if dry_run:
        print("  [DRY RUN] Would create filtered views in:")
        for project in main_projects:
            print(f"    - {project.get('title')} (#{project.get('number')})")
        return

    for project in main_projects:
        create_project_filters(org, str(project.get("number")), project.get("title", "Untitled"), dry_run=dry_run)

    print("\n  💡 Note: GitHub CLI doesn't yet support programmatic view creation")
    print("     Manual steps for each main project:")
    print("     1. Go to project → Views → New view → Table")
    print("     2. Add filter: -label:cod")
    print("     3. Set as default view")
    print("     4. Save view as 'Work Items (No CODs)'")


def main():
    parser = argparse.ArgumentParser(
        description="Setup COD project and organize COD issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--org",
        default="IggyIkenna",
        help="GitHub organization name (default: IggyIkenna)",
    )
    parser.add_argument(
        "--repos",
        nargs="+",
        help="List of repositories to process (default: all repos in org)",
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

    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("❌ Must specify either --dry-run or --apply")
        sys.exit(1)

    if args.apply and args.dry_run:
        print("❌ Cannot use both --dry-run and --apply")
        sys.exit(1)

    dry_run = args.dry_run

    print("=" * 80)
    print("COD Project Setup")
    print("=" * 80)

    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be made\n")
    else:
        print("\n⚠️  APPLY MODE - Changes will be made to GitHub\n")

    # Get repository list
    repos = args.repos
    if not repos:
        print("📂 Fetching repository list...")
        result = run_gh_command(
            [
                "gh",
                "repo",
                "list",
                args.org,
                "--json",
                "name",
                "--limit",
                "1000",
            ]
        )
        repos = [repo["name"] for repo in result] if result else []
        print(f"  ✓ Found {len(repos)} repositories")

    # Step 1: Create COD label
    create_cod_label(args.org, repos, dry_run)

    # Step 2 & 3: Find and label COD issues
    cod_issues = find_cod_issues(args.org, repos)
    apply_cod_labels(args.org, cod_issues, dry_run)

    # Step 4: Create COD project
    project_number = create_cod_project(args.org, dry_run)

    # Step 5: Add issues to project
    if project_number:
        add_issues_to_project(args.org, project_number, cod_issues, dry_run)

    # Step 6: Setup automation
    if project_number:
        setup_project_automation(args.org, project_number, dry_run)

    # Step 7: Issue template updates
    update_issue_templates(Path.cwd(), dry_run)

    # Step 8: Setup filters in main projects
    setup_main_project_filters(args.org, dry_run)

    print("\n" + "=" * 80)
    print("✅ Setup complete!")
    print("=" * 80)

    if not dry_run:
        print("\n📋 Remaining manual steps (GitHub CLI limitations):")
        print("1. Configure project automation rules:")
        print(f"   https://github.com/orgs/{args.org}/projects/{project_number}/settings/workflows")
        print("   - Auto-add: When label 'cod' is added → Add to project")
        print("   - Auto-status: When issue is closed → Move to 'Done'")
        print("   - Auto-archive: When closed for 30 days → Archive")
        print("\n2. Create filtered views in main projects:")
        print(f"   https://github.com/orgs/{args.org}/projects")
        print("   - For each main project: Views → New view → Table")
        print("   - Add filter: -label:cod")
        print("   - Set as default view")
        print("\n💡 These are one-time manual steps. Once configured, automation handles everything.")


if __name__ == "__main__":
    main()
