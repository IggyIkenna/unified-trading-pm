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
from typing import cast

# Type alias
JsonDict = dict[str, object]


def run_gh_command(cmd: list[str], check: bool = True) -> JsonDict | list[object] | str | None:
    """Run a GitHub CLI command and return parsed JSON output."""
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd,
            check=check,
            capture_output=True,
            text=True,
        )

        # If command succeeded
        if result.returncode == 0:
            if result.stdout.strip():
                try:
                    raw_parsed: object = cast(object, json.loads(result.stdout))
                    if isinstance(raw_parsed, list):
                        return cast(list[object], raw_parsed)
                    if isinstance(raw_parsed, dict):
                        return cast(JsonDict, raw_parsed)
                    return str(raw_parsed)
                except json.JSONDecodeError:
                    return result.stdout.strip()
            return ""  # Success but no output

        # Command failed
        if not check:
            # Return error info as dict so caller can handle it
            return {"_error": True, "stderr": result.stderr.strip(), "returncode": result.returncode}

        return None

    except subprocess.CalledProcessError as e:
        raw_stderr: object = getattr(e, "stderr", None)
        print(f"Command failed: {' '.join(cmd)}")
        print(f"   Error: {raw_stderr}")
        if check:
            raise
        return None


def create_cod_label(org: str, repos: list[str], dry_run: bool = False) -> None:
    """Create 'cod' label in all repositories.

    Note: GitHub doesn't support batch label creation - must be done per-repo.
    """
    print("\nStep 1: Creating 'cod' label...")
    print("  (Note: GitHub requires individual API calls per repo for label creation)")

    label_config: dict[str, str] = {
        "name": "cod",
        "description": "Change of Direction - architectural/design pivots tracked separately",
        "color": "d4c5f9",  # Light purple
    }

    skipped: int = 0
    created: int = 0
    existing: int = 0

    for repo in repos:
        print(f"  Processing {repo}...")

        # Check if repo has issues enabled
        test: JsonDict | list[object] | str | None = run_gh_command(
            ["gh", "label", "list", "--repo", f"{org}/{repo}", "--json", "name", "--limit", "1"], check=False
        )

        if test is None:
            print("    WARN: Skipping (issues disabled or access denied)")
            skipped += 1
            continue

        # Check if label exists
        existing_labels: JsonDict | list[object] | str | None = run_gh_command(
            ["gh", "label", "list", "--repo", f"{org}/{repo}", "--json", "name"], check=False
        )

        # Handle errors in listing labels
        if isinstance(existing_labels, dict) and existing_labels.get("_error"):
            stderr_val: str = str(existing_labels.get("stderr", "unknown"))
            print(f"    WARN: Skipping (error: {stderr_val})")
            skipped += 1
            continue

        if existing_labels and isinstance(existing_labels, list):
            labels_list: list[JsonDict] = [cast(JsonDict, item) for item in existing_labels if isinstance(item, dict)]
            if any(str(label.get("name", "")) == "cod" for label in labels_list):
                if dry_run:
                    print("    [DRY RUN] Label 'cod' already exists")
                else:
                    print("    OK: Label 'cod' already exists")
                existing += 1
                continue

        if dry_run:
            print(f"    [DRY RUN] Would create label: {label_config}")
            created += 1
            continue

        # Create label
        result: JsonDict | list[object] | str | None = run_gh_command(
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
            stderr_str: str = str(result.get("stderr", ""))
            if "already exists" in stderr_str.lower():
                print("    OK: Label 'cod' already exists")
                existing += 1
            else:
                print(f"    WARN: Failed: {stderr_str[:80]}")
                skipped += 1
        elif result is not None and result != "":
            print("    OK: Created 'cod' label")
            created += 1
        else:
            print("    OK: Created 'cod' label")
            created += 1

    mode: str = "[DRY RUN] " if dry_run else ""
    verb: str = "would be created" if dry_run else "created"
    print(f"\n  {mode}Summary: {created} {verb}, {existing} already exist, {skipped} skipped")


def find_cod_issues(org: str, repos: list[str]) -> list[JsonDict]:
    """Find all issues that mention COD in title or have 'change of direction' in body.

    Uses org-wide search to batch API calls (3 queries instead of repos * 3).
    """
    print("\nStep 2: Finding COD issues...")
    print("  Using batched org-wide search (faster, fewer API calls)...")

    cod_issues: list[JsonDict] = []
    search_terms: list[str] = [
        f"org:{org} COD in:title",
        f'org:{org} "change of direction" in:title',
        f'org:{org} "change-of-direction" in:title',
    ]

    for term in search_terms:
        print(f"  Searching: {term.split('org:')[1][:50]}...")

        result: JsonDict | list[object] | str | None = run_gh_command(
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
            stderr_val: str = str(result.get("stderr", "unknown"))
            print(f"    WARN: Search failed: {stderr_val[:80]}")
            continue

        if result and isinstance(result, list):
            print(f"    Found {len(result)} issues")
            for raw_issue in result:
                if not isinstance(raw_issue, dict):
                    continue
                issue: JsonDict = cast(JsonDict, raw_issue)

                # Parse repo name from URL: https://github.com/org/repo/issues/123
                repo_name: str = ""
                issue_url: str = str(issue.get("url", ""))
                if issue_url:
                    url_parts: list[str] = issue_url.split("/")
                    if len(url_parts) >= 5:
                        repo_name = url_parts[4]

                # Check if already labeled
                raw_labels: object = issue.get("labels") or []
                labels_list: list[JsonDict] = (
                    [cast(JsonDict, lb) for lb in cast(list[object], raw_labels) if isinstance(lb, dict)]
                    if isinstance(raw_labels, list)
                    else []
                )
                has_cod_label: bool = any(str(lb.get("name", "")) == "cod" for lb in labels_list)

                issue_info: JsonDict = {
                    "repo": repo_name,
                    "number": issue.get("number", 0),
                    "title": str(issue.get("title", "")),
                    "url": issue_url,
                    "has_cod_label": has_cod_label,
                }

                # Avoid duplicates
                if not any(str(i.get("url", "")) == str(issue_info.get("url", "")) for i in cod_issues):
                    cod_issues.append(issue_info)

    unique_repos: set[str] = {str(i.get("repo", "")) for i in cod_issues}
    unlabeled: int = sum(1 for i in cod_issues if not i.get("has_cod_label"))
    print(f"\n  Found {len(cod_issues)} unique COD issues across {len(unique_repos)} repos")
    print(f"    {unlabeled} need labeling")
    print(f"    API calls saved: ~{len(repos) * 3 - 3} (batched {len(repos) * 3} -> 3 queries)")

    return cod_issues


def apply_cod_labels(org: str, cod_issues: list[JsonDict], dry_run: bool = False) -> None:
    """Apply 'cod' label to all identified COD issues.

    Note: GitHub CLI requires individual API calls per issue for label edits.
    GraphQL mutations could batch this, but would add complexity.
    """
    print("\nStep 3: Applying 'cod' labels...")

    unlabeled: list[JsonDict] = [issue for issue in cod_issues if not issue.get("has_cod_label")]

    if not unlabeled:
        print("  OK: All COD issues already labeled")
        return

    print(f"  Labeling {len(unlabeled)} issues (individual API calls required)...")

    for idx, issue in enumerate(unlabeled, 1):
        issue_repo: str = str(issue.get("repo", ""))
        issue_number: str = str(issue.get("number", ""))
        issue_title: str = str(issue.get("title", ""))

        if dry_run:
            if idx % 10 == 0 or idx <= 10:
                print(f"  [{idx}/{len(unlabeled)}] {issue_repo}#{issue_number}: {issue_title[:50]}...")
                print("    [DRY RUN] Would add 'cod' label")
            continue

        result: JsonDict | list[object] | str | None = run_gh_command(
            [
                "gh",
                "issue",
                "edit",
                issue_number,
                "--repo",
                f"{org}/{issue_repo}",
                "--add-label",
                "cod",
            ],
            check=False,
        )

        # Handle result and show progress every 10 issues
        if isinstance(result, dict) and result.get("_error"):
            stderr_val: str = str(result.get("stderr", ""))
            print(f"  [{idx}/{len(unlabeled)}] {issue_repo}#{issue_number}: WARN: {stderr_val[:60]}")
        else:
            if idx % 10 == 0:  # Show every 10th
                print(f"  [{idx}/{len(unlabeled)}] {issue_repo}#{issue_number}: OK: Labeled")

    print(f"  OK: Completed labeling {len(unlabeled)} issues")


def create_cod_project(org: str, dry_run: bool = False) -> str | None:
    """Create a GitHub project for COD issues."""
    print("\nStep 4: Creating COD project...")

    project_title: str = "CODs (Change of Direction)"
    project_body: str = """
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
    existing_result: JsonDict | list[object] | str | None = run_gh_command(
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

    if isinstance(existing_result, dict):
        raw_projects: object = existing_result.get("projects") or []
        if isinstance(raw_projects, list):
            projects_list: list[JsonDict] = [
                cast(JsonDict, p) for p in cast(list[object], raw_projects) if isinstance(p, dict)
            ]
            for project in projects_list:
                if str(project.get("title", "")) == project_title:
                    print(f"  OK: Project already exists: {project.get('url')}")
                    return str(project.get("number", ""))

    # Create project
    create_result: JsonDict | list[object] | str | None = run_gh_command(
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

    if isinstance(create_result, dict):
        project_number: str = str(create_result.get("number", ""))
        print(f"  OK: Created project #{project_number}")

        # Update description (requires separate API call via gh api)
        subprocess.run(
            [
                "gh",
                "api",
                "graphql",
                "-f",
                "query=mutation {{ updateProjectV2(input: {{"
                f'projectId: "{create_result.get("id", "")}", '
                f'readme: "{project_body}"'
                "}}) {{ projectV2 {{ id }} }} }}",
            ],
            check=False,
        )

        return project_number

    return None


def add_issues_to_project(org: str, project_number: str, cod_issues: list[JsonDict], dry_run: bool = False) -> None:
    """Add all COD issues to the COD project.

    Note: GitHub requires individual API calls per issue to add to project.
    """
    print("\nStep 5: Adding issues to COD project...")

    if dry_run:
        print(f"  [DRY RUN] Would add {len(cod_issues)} issues to project #{project_number}")
        for issue in cod_issues[:5]:
            issue_repo: str = str(issue.get("repo", ""))
            issue_num: str = str(issue.get("number", ""))
            issue_title: str = str(issue.get("title", ""))
            print(f"    - {issue_repo}#{issue_num}: {issue_title[:50]}...")
        if len(cod_issues) > 5:
            print(f"    ... and {len(cod_issues) - 5} more")
        return

    print(f"  Adding {len(cod_issues)} issues to project (individual API calls required)...")

    added: int = 0
    skipped: int = 0

    for idx, issue in enumerate(cod_issues, 1):
        issue_url = str(issue.get("url", ""))
        issue_repo = str(issue.get("repo", ""))
        issue_num = str(issue.get("number", ""))

        result: JsonDict | list[object] | str | None = run_gh_command(
            [
                "gh",
                "project",
                "item-add",
                project_number,
                "--owner",
                org,
                "--url",
                issue_url,
            ],
            check=False,
        )

        # Handle result and show progress every 10 issues
        if isinstance(result, dict) and result.get("_error"):
            skipped += 1
            stderr_val: str = str(result.get("stderr", ""))
            if "already exists" in stderr_val.lower():
                if idx % 10 == 0:
                    print(f"  [{idx}/{len(cod_issues)}] {issue_repo}#{issue_num}: Already in project")
            else:
                print(f"  [{idx}/{len(cod_issues)}] {issue_repo}#{issue_num}: WARN: {stderr_val[:60]}")
        else:
            added += 1
            if idx % 10 == 0:  # Show every 10th
                print(f"  [{idx}/{len(cod_issues)}] {issue_repo}#{issue_num}: OK: Added")

    print(f"\n  OK: Completed: {added} added, {skipped} skipped")


def setup_project_automation(org: str, project_number: str, dry_run: bool = False) -> None:
    """Set up automation rules for the COD project using GitHub GraphQL API."""
    print("\nStep 6: Setting up project automation...")

    # Get project ID (needed for GraphQL)
    project_data: JsonDict | list[object] | str | None = run_gh_command(
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
        print("  WARN: Could not fetch project details. Automation must be configured manually.")
        print(f"     https://github.com/orgs/{org}/projects/{project_number}/settings")
        return

    if dry_run:
        print("  [DRY RUN] Would configure automation rules:")
        print("    1. Auto-add: When 'cod' label is added -> Add to project")
        print("    2. Auto-status: When issue is closed -> Move to 'Done'")
        print("    3. Auto-archive: When issue closed for 30 days -> Archive")
        return

    # GitHub Projects V2 automation via GraphQL
    # Note: GitHub doesn't provide full CLI support for workflow automation yet
    # We'll create the workflows using gh api with GraphQL

    print("  OK: Configuring automation workflows via GraphQL...")

    # For now, document the manual steps since GH CLI doesn't fully support workflow automation
    print("  WARN: GitHub CLI doesn't yet support full project workflow automation")
    print("  OK: Created project successfully. Configure automation rules manually:")
    print(f"     https://github.com/orgs/{org}/projects/{project_number}/settings/workflows")
    print("\n  Recommended automation rules:")
    print("    1. Item added to project: When issue has label 'cod' -> Add to project")
    print("    2. Item closed: When issue is closed -> Set status to 'Done'")
    print("    3. Auto-archive: When issue closed -> Wait 30 days -> Archive")
    print("\n  These rules prevent manual maintenance and keep the project clean automatically.")


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
    print("\nStep 7: Updating issue templates...")

    template_snippet: str = create_issue_template_snippet()

    if dry_run:
        print("  [DRY RUN] Would add this snippet to issue templates:")
        print(template_snippet)
        return

    print("  Manual step required:")
    print("     Add the following snippet to your issue templates:")
    print(template_snippet)


def get_main_projects(org: str) -> list[JsonDict]:
    """Get list of main GitHub projects (excluding COD project)."""
    result: JsonDict | list[object] | str | None = run_gh_command(
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
        stderr_val: str = str(result.get("stderr", "Unknown error"))
        print(f"  WARN: Could not fetch projects: {stderr_val}")
        return []

    if not result or not isinstance(result, dict):
        return []

    # Filter out COD project
    raw_projects: object = result.get("projects") or []
    if not isinstance(raw_projects, list):
        return []
    projects: list[JsonDict] = [cast(JsonDict, p) for p in cast(list[object], raw_projects) if isinstance(p, dict)]
    main_projects: list[JsonDict] = [
        p
        for p in projects
        if "cod" not in str(p.get("title", "")).lower() and "change of direction" not in str(p.get("title", "")).lower()
    ]

    return main_projects


def create_project_filters(org: str, project_number: str, project_title: str, dry_run: bool = False) -> None:
    """Create filtered views in a GitHub project to exclude CODs."""
    print(f"  Processing {project_title} (#{project_number})...")

    views_to_create: list[dict[str, str | bool]] = [
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
    existing_views_result: JsonDict | list[object] | str | None = run_gh_command(
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

    existing_views: list[str] = []
    if isinstance(existing_views_result, dict) and not existing_views_result.get("_error"):
        raw_views: object = existing_views_result.get("views") or []
        if isinstance(raw_views, list):
            views_list: list[JsonDict] = [
                cast(JsonDict, v) for v in cast(list[object], raw_views) if isinstance(v, dict)
            ]
            existing_views = [str(v.get("name", "")) for v in views_list]

    skipped: int = 0

    for view_config in views_to_create:
        view_name: str = str(view_config.get("name", ""))
        view_filter: str = str(view_config.get("filter", ""))
        if view_name in existing_views:
            print(f"    WARN: View '{view_name}' already exists - skipping")
            skipped += 1
            continue

        # Note: GitHub CLI doesn't yet support creating custom views with filters
        # This would require GraphQL API calls
        print(f"    WARN: View creation requires manual setup: '{view_name}'")
        print(f"       Filter: {view_filter}")
        skipped += 1

    if skipped > 0:
        print(f"    Create views manually at: https://github.com/orgs/{org}/projects/{project_number}")


def setup_main_project_filters(org: str, dry_run: bool = False) -> None:
    """Set up filters in main projects to exclude COD label."""
    print("\nStep 8: Setting up filters in main projects...")

    main_projects: list[JsonDict] = get_main_projects(org)

    if not main_projects:
        print("  WARN: No main projects found or unable to fetch projects")
        print(f"  Configure filters manually at: https://github.com/orgs/{org}/projects")
        return

    print(f"  Found {len(main_projects)} main project(s)")

    if dry_run:
        print("  [DRY RUN] Would create filtered views in:")
        for project in main_projects:
            print(f"    - {project.get('title')} (#{project.get('number')})")
        return

    for project in main_projects:
        create_project_filters(
            org,
            str(project.get("number", "")),
            str(project.get("title", "Untitled")),
            dry_run=dry_run,
        )

    print("\n  Note: GitHub CLI doesn't yet support programmatic view creation")
    print("     Manual steps for each main project:")
    print("     1. Go to project -> Views -> New view -> Table")
    print("     2. Add filter: -label:cod")
    print("     3. Set as default view")
    print("     4. Save view as 'Work Items (No CODs)'")


def _parse_setup_args() -> argparse.Namespace:
    """Parse and return setup script arguments."""
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
    return parser.parse_args()


def _validate_mode(parsed: argparse.Namespace) -> None:
    """Validate dry-run and apply flags; exit on error."""
    dry_run_flag: bool = bool(getattr(parsed, "dry_run", False))
    apply_flag: bool = bool(getattr(parsed, "apply", False))
    if not dry_run_flag and not apply_flag:
        print("ERROR: Must specify either --dry-run or --apply")
        sys.exit(1)
    if apply_flag and dry_run_flag:
        print("ERROR: Cannot use both --dry-run and --apply")
        sys.exit(1)


def _resolve_repos(org: str, raw_repos: object) -> list[str]:
    """Resolve repository list from args or fetch from GitHub."""
    if isinstance(raw_repos, list) and raw_repos:
        raw_repos_list: list[object] = cast(list[object], raw_repos)
        return [str(r) for r in raw_repos_list]
    print("Fetching repository list...")
    result: JsonDict | list[object] | str | None = run_gh_command(
        [
            "gh",
            "repo",
            "list",
            org,
            "--json",
            "name",
            "--limit",
            "1000",
        ]
    )
    if isinstance(result, list):
        result_dicts: list[JsonDict] = [cast(JsonDict, item) for item in result if isinstance(item, dict)]
        repos = [str(rd.get("name", "")) for rd in result_dicts]
    else:
        repos = []
    print(f"  Found {len(repos)} repositories")
    return repos


def _run_setup_steps(org: str, repos: list[str], dry_run: bool) -> str | None:
    """Execute setup steps 1-8; returns project_number if created."""
    create_cod_label(org, repos, dry_run)
    cod_issues: list[JsonDict] = find_cod_issues(org, repos)
    apply_cod_labels(org, cod_issues, dry_run)
    project_number: str | None = create_cod_project(org, dry_run)
    if project_number:
        add_issues_to_project(org, project_number, cod_issues, dry_run)
        setup_project_automation(org, project_number, dry_run)
    update_issue_templates(Path.cwd(), dry_run)
    setup_main_project_filters(org, dry_run)
    return project_number


def _print_completion(org: str, dry_run: bool, project_number: str | None) -> None:
    """Print setup completion and manual steps."""
    print("\n" + "=" * 80)
    print("Setup complete!")
    print("=" * 80)
    if not dry_run and project_number:
        print("\nRemaining manual steps (GitHub CLI limitations):")
        print("1. Configure project automation rules:")
        print(f"   https://github.com/orgs/{org}/projects/{project_number}/settings/workflows")
        print("   - Auto-add: When label 'cod' is added -> Add to project")
        print("   - Auto-status: When issue is closed -> Move to 'Done'")
        print("   - Auto-archive: When closed for 30 days -> Archive")
        print("\n2. Create filtered views in main projects:")
        print(f"   https://github.com/orgs/{org}/projects")
        print("   - For each main project: Views -> New view -> Table")
        print("   - Add filter: -label:cod")
        print("   - Set as default view")
        print("\nThese are one-time manual steps. Once configured, automation handles everything.")


def main() -> None:
    parsed = _parse_setup_args()
    _validate_mode(parsed)
    dry_run: bool = bool(getattr(parsed, "dry_run", False))
    org: str = str(getattr(parsed, "org", "IggyIkenna"))
    raw_repos: object = getattr(parsed, "repos", None)

    print("=" * 80)
    print("COD Project Setup")
    print("=" * 80)
    if dry_run:
        print("\nDRY RUN MODE - No changes will be made\n")
    else:
        print("\nAPPLY MODE - Changes will be made to GitHub\n")

    repos: list[str] = _resolve_repos(org, raw_repos)
    project_number: str | None = _run_setup_steps(org, repos, dry_run)
    _print_completion(org, dry_run, project_number)


if __name__ == "__main__":
    main()
