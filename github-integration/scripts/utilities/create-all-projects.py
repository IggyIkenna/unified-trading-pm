#!/usr/bin/env python3
"""
Create All GitHub Projects - Automated Setup

Creates 15 missing GitHub projects with labels, views, and automation.

Usage:
    # Dry run (preview):
    python create-all-projects.py --org IggyIkenna --dry-run

    # Apply changes:
    python create-all-projects.py --org IggyIkenna --apply

    # Create specific projects:
    python create-all-projects.py --org IggyIkenna --apply --projects bugs execution strategy

Based on PROJECT_STRUCTURE_REFERENCE.md
Python 3.13+
"""

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any

import requests

# ============================================================================
# PROJECT DEFINITIONS (from PROJECT_STRUCTURE_REFERENCE.md)
# ============================================================================

PROJECT_DEFINITIONS = {
    "bugs": {
        "title": "Bugs & Issues",
        "description": "Production failures requiring immediate attention",
        "type": "flat",
        "primary_label": "bug",
        "additional_labels": ["P0", "P1", "P2"],
        "filter": "label:bug is:open",
        "repos": "all",
        "views": [
            {"name": "P0 Critical", "filter": "label:bug label:P0 is:open"},
            {"name": "P1 High", "filter": "label:bug label:P1 is:open"},
            {"name": "All Open Bugs", "filter": "label:bug is:open"},
        ],
    },
    "execution": {
        "title": "Execution Services",
        "description": "Live trading execution + backtest + UI",
        "type": "hierarchy",
        "primary_label": "execution",
        "additional_labels": ["epic", "task", "subtask"],
        "filter": "repo:execution-service -label:cod",
        "repos": ["execution-service"],
        "views": [
            {"name": "Work Items", "filter": "repo:execution-service -label:cod"},
            {"name": "Epics Only", "filter": "repo:execution-service label:epic -label:cod"},
            {"name": "In Progress", "filter": "repo:execution-service is:open -label:cod"},
        ],
    },
    "strategy": {
        "title": "Strategy Services",
        "description": "Strategy logic + backtest + UI + analytics",
        "type": "hierarchy",
        "primary_label": "strategy",
        "additional_labels": ["epic", "task", "subtask", "backtest"],
        "filter": "repo:strategy-service -label:cod",
        "repos": ["strategy-service"],
        "views": [
            {"name": "Work Items", "filter": "repo:strategy-service -label:cod"},
            {"name": "Epics Only", "filter": "repo:strategy-service label:epic -label:cod"},
            {"name": "In Progress", "filter": "repo:strategy-service is:open -label:cod"},
        ],
    },
    "risk": {
        "title": "Position Monitoring & Risk",
        "description": "Real-time P&L, risk limits, alert system",
        "type": "hierarchy",
        "primary_label": "risk",
        "additional_labels": ["epic", "task", "subtask"],
        "filter": "label:risk -label:cod",
        "repos": ["position-monitoring", "risk-service"],
        "views": [
            {"name": "Work Items", "filter": "label:risk -label:cod"},
            {"name": "Epics Only", "filter": "label:risk label:epic -label:cod"},
            {"name": "In Progress", "filter": "label:risk is:open -label:cod"},
        ],
    },
    "market-data": {
        "title": "Market Data Pipeline",
        "description": "Tick ingestion, processing, storage",
        "type": "hierarchy",
        "primary_label": "market-data",
        "additional_labels": ["epic", "task", "subtask"],
        "filter": "repo:market-tick-data-handler,market-data-processing-service -label:cod",
        "repos": ["market-tick-data-handler", "market-data-processing-service"],
        "views": [
            {"name": "Work Items", "filter": "repo:market-tick-data-handler,market-data-processing-service -label:cod"},
            {
                "name": "Epics Only",
                "filter": "repo:market-tick-data-handler,market-data-processing-service label:epic -label:cod",
            },
            {
                "name": "In Progress",
                "filter": "repo:market-tick-data-handler,market-data-processing-service is:open -label:cod",
            },
        ],
    },
    "features": {
        "title": "Features Engineering",
        "description": "Calendar, Delta-one, Onchain, Volatility features",
        "type": "hierarchy",
        "primary_label": "features",
        "additional_labels": ["epic", "task", "subtask"],
        "filter": "repo:features-calendar-service,features-delta-one-service,features-onchain-service,features-volatility-service -label:cod",
        "repos": [
            "features-calendar-service",
            "features-delta-one-service",
            "features-onchain-service",
            "features-volatility-service",
        ],
        "views": [
            {
                "name": "Work Items",
                "filter": "repo:features-calendar-service,features-delta-one-service,features-onchain-service,features-volatility-service -label:cod",
            },
            {
                "name": "Epics Only",
                "filter": "repo:features-calendar-service,features-delta-one-service,features-onchain-service,features-volatility-service label:epic -label:cod",
            },
            {
                "name": "In Progress",
                "filter": "repo:features-calendar-service,features-delta-one-service,features-onchain-service,features-volatility-service is:open -label:cod",
            },
        ],
    },
    "ml-training": {
        "title": "ML Training Services",
        "description": "Model training, hyperparameter tuning, experiment tracking",
        "type": "hierarchy",
        "primary_label": "ml-training",
        "additional_labels": ["epic", "task", "subtask"],
        "filter": "repo:ml-training-service -label:cod",
        "repos": ["ml-training-service"],
        "views": [
            {"name": "Work Items", "filter": "repo:ml-training-service -label:cod"},
            {"name": "Epics Only", "filter": "repo:ml-training-service label:epic -label:cod"},
            {"name": "In Progress", "filter": "repo:ml-training-service is:open -label:cod"},
        ],
    },
    "ml-inference": {
        "title": "ML Inference Services",
        "description": "Real-time prediction, batch inference, model monitoring",
        "type": "hierarchy",
        "primary_label": "ml-inference",
        "additional_labels": ["epic", "task", "subtask"],
        "filter": "repo:ml-inference-service -label:cod",
        "repos": ["ml-inference-service"],
        "views": [
            {"name": "Work Items", "filter": "repo:ml-inference-service -label:cod"},
            {"name": "Epics Only", "filter": "repo:ml-inference-service label:epic -label:cod"},
            {"name": "In Progress", "filter": "repo:ml-inference-service is:open -label:cod"},
        ],
    },
    "ml-analytics": {
        "title": "ML Deployment Analytics",
        "description": "Model performance tracking, drift detection",
        "type": "flat",
        "primary_label": "ml-analytics",
        "additional_labels": [],
        "filter": "label:ml-analytics",
        "repos": ["ml-inference-service"],
        "views": [
            {"name": "All Analytics", "filter": "label:ml-analytics"},
            {"name": "Performance Issues", "filter": "label:ml-analytics label:performance"},
        ],
    },
    "settlement": {
        "title": "Settlement & Reconciliation",
        "description": "Trade settlement, accounting integration, audit trail",
        "type": "hierarchy",
        "primary_label": "settlement",
        "additional_labels": ["epic", "task", "subtask"],
        "filter": "label:settlement -label:cod",
        "repos": ["settlement-service"],
        "views": [
            {"name": "Work Items", "filter": "label:settlement -label:cod"},
            {"name": "Epics Only", "filter": "label:settlement label:epic -label:cod"},
            {"name": "In Progress", "filter": "label:settlement is:open -label:cod"},
        ],
    },
    "reporting": {
        "title": "Client Reporting",
        "description": "Performance reports, analytics dashboards, custom queries",
        "type": "flat",
        "primary_label": "reporting",
        "additional_labels": [],
        "filter": "label:reporting",
        "repos": ["client-reporting-api"],
        "views": [
            {"name": "All Reports", "filter": "label:reporting"},
            {"name": "Custom Queries", "filter": "label:reporting label:custom-query"},
        ],
    },
    "infrastructure": {
        "title": "Infrastructure & Tooling",
        "description": "Cloud services, deployment automation, monitoring",
        "type": "hierarchy",
        "primary_label": "infrastructure",
        "additional_labels": ["epic", "task", "subtask"],
        "filter": "repo:unified-trading-services,unified-trading-deployment-v2 -label:cod",
        "repos": ["unified-trading-services", "unified-trading-deployment-v2"],
        "views": [
            {"name": "Work Items", "filter": "repo:unified-trading-services,unified-trading-deployment-v2 -label:cod"},
            {
                "name": "Epics Only",
                "filter": "repo:unified-trading-services,unified-trading-deployment-v2 label:epic -label:cod",
            },
            {
                "name": "In Progress",
                "filter": "repo:unified-trading-services,unified-trading-deployment-v2 is:open -label:cod",
            },
        ],
    },
    "execution-backtest": {
        "title": "Execution Backtest & UI",
        "description": "Backtest execution strategies on historical data",
        "type": "hierarchy",
        "primary_label": "execution-backtest",
        "additional_labels": ["epic", "task", "subtask", "backtest"],
        "filter": "repo:execution-service label:backtest -label:cod",
        "repos": ["execution-service"],
        "views": [
            {"name": "Work Items", "filter": "repo:execution-service label:backtest -label:cod"},
            {"name": "Epics Only", "filter": "repo:execution-service label:backtest label:epic -label:cod"},
            {"name": "In Progress", "filter": "repo:execution-service label:backtest is:open -label:cod"},
        ],
    },
    "strategy-backtest": {
        "title": "Strategy Backtest & UI",
        "description": "Backtest trading strategies on historical data",
        "type": "hierarchy",
        "primary_label": "strategy-backtest",
        "additional_labels": ["epic", "task", "subtask", "backtest"],
        "filter": "repo:strategy-service label:backtest -label:cod",
        "repos": ["strategy-service"],
        "views": [
            {"name": "Work Items", "filter": "repo:strategy-service label:backtest -label:cod"},
            {"name": "Epics Only", "filter": "repo:strategy-service label:backtest label:epic -label:cod"},
            {"name": "In Progress", "filter": "repo:strategy-service label:backtest is:open -label:cod"},
        ],
    },
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_github_token() -> str:
    """Get GitHub token from environment or gh CLI."""
    token = os.getenv("GITHUB_TOKEN")
    if token:
        return token

    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except (ConnectionError, TimeoutError, OSError, ValueError) as e:
        print(f"❌ Error: Could not get GitHub token: {e}")
        print("   Set GITHUB_TOKEN env var or run 'gh auth login'")
        sys.exit(1)


def run_gh_command(args: list[str], check: bool = True) -> dict[str, Any] | None:
    """Run a gh CLI command and return parsed JSON output."""
    try:
        result = subprocess.run(
            ["gh"] + args,
            capture_output=True,
            text=True,
            check=check,
        )

        if result.returncode != 0:
            if not check:
                return {"_error": True, "stderr": result.stderr, "stdout": result.stdout}
            return None

        if result.stdout.strip():
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"_raw": result.stdout.strip()}

        return {"_success": True}

    except subprocess.CalledProcessError as e:
        if check:
            print(f"❌ Command failed: gh {' '.join(args)}")
            print(f"   Error: {e.stderr}")
        return None


def run_graphql_query(token: str, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run a GraphQL query against GitHub API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post("https://api.github.com/graphql", headers=headers, json=payload, timeout=30)
    response.raise_for_status()

    data = response.json()
    if "errors" in data:
        raise Exception(f"GraphQL errors: {data['errors']}")

    return data


# ============================================================================
# PROJECT OPERATIONS
# ============================================================================


def create_project(org: str, project_key: str, project_def: dict[str, Any], dry_run: bool) -> tuple[bool, str]:
    """Create a single GitHub project."""
    title = project_def["title"]
    description = project_def["description"]

    if dry_run:
        print(f"   Would create project: {title}")
        return (True, "dry-run")

    # Check if project already exists
    existing = run_gh_command(["project", "list", "--owner", org, "--format", "json"], check=False)
    if existing and "_error" not in existing:
        for proj in existing.get("projects", []):
            if proj.get("title") == title:
                print(f"   ✅ Project already exists: {title} (#{proj['number']})")
                return (True, str(proj["number"]))

    # Create project
    result = run_gh_command(
        [
            "project",
            "create",
            "--owner",
            org,
            "--title",
            title,
            "--format",
            "json",
        ],
        check=False,
    )

    if result and "_error" not in result:
        project_number = result.get("number")
        print(f"   ✅ Created project: {title} (#{project_number})")
        return (True, str(project_number))
    else:
        print(f"   ❌ Failed to create project: {title}")
        if result:
            print(f"      Error: {result.get('stderr', 'Unknown error')}")
        return (False, "")


def create_labels(org: str, project_def: dict[str, Any], dry_run: bool) -> int:
    """Create labels for project repos."""
    labels_to_create = [project_def["primary_label"]] + project_def["additional_labels"]
    repos = project_def["repos"]

    if repos == "all":
        # Get all repos
        all_repos_result = run_gh_command(
            [
                "repo",
                "list",
                org,
                "--limit",
                "100",
                "--json",
                "name",
            ],
            check=False,
        )
        if not all_repos_result or "_error" in all_repos_result:
            print(f"   ⚠️ Could not list repos for org: {org}")
            return 0
        repos = [r["name"] for r in all_repos_result]

    created_count = 0

    for repo_name in repos:
        repo_full = f"{org}/{repo_name}"

        for label_name in labels_to_create:
            if dry_run:
                print(f"      Would create label '{label_name}' in {repo_full}")
                created_count += 1
                continue

            # Check if label exists
            existing = run_gh_command(
                [
                    "label",
                    "list",
                    "--repo",
                    repo_full,
                    "--json",
                    "name",
                ],
                check=False,
            )

            if existing and "_error" not in existing:
                if any(lbl["name"] == label_name for lbl in existing):
                    continue  # Label already exists

            # Create label
            result = run_gh_command(
                [
                    "label",
                    "create",
                    label_name,
                    "--repo",
                    repo_full,
                    "--color",
                    "0366d6",
                ],
                check=False,
            )

            if result and "_error" not in result:
                created_count += 1

    return created_count


def document_manual_steps(project_key: str, project_def: dict[str, Any], project_number: str) -> str:
    """Generate manual setup instructions for workflows and views."""
    title = project_def["title"]
    views = project_def["views"]

    instructions = f"""
# Manual Setup Required for Project: {title} (#{project_number})

## 1. Configure Project Automation Workflows

Navigate to: https://github.com/users/IggyIkenna/projects/{project_number}/settings/workflows

**Add these automation rules:**

### Rule 1: Auto-add items
- **When:** Issues are created or updated
- **If:** Label = "{project_def["primary_label"]}"
- **Then:** Add to project

### Rule 2: Auto-status
- **When:** Item is closed
- **Then:** Set status to "Done"

### Rule 3: Auto-archive
- **When:** Item is in "Done" and closed for 30 days
- **Then:** Archive item

---

## 2. Create Filtered Views

Navigate to: https://github.com/users/IggyIkenna/projects/{project_number}

"""

    for idx, view in enumerate(views, 1):
        instructions += f"""
### View {idx}: {view["name"]}
- Click "+ New view"
- Name: "{view["name"]}"
- Filter: `{view["filter"]}`
- Save view
"""

    instructions += """
---

## 3. Verify Setup

- [ ] Automation rules created (3 rules)
- [ ] Views created ({} views)
- [ ] Labels exist in target repos
- [ ] Test: Create issue with label, verify it appears in project

---

**Estimated time:** 5 minutes
""".format(len(views))

    return instructions


# ============================================================================
# MAIN LOGIC
# ============================================================================


def main():
    parser = argparse.ArgumentParser(description="Create all missing GitHub projects")
    parser.add_argument("--org", required=True, help="GitHub organization or user")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--projects", nargs="+", help="Specific projects to create (default: all)")

    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("❌ Error: Must specify --dry-run or --apply")
        sys.exit(1)

    # Get GitHub token
    token = get_github_token()

    # Determine which projects to create
    projects_to_create = args.projects if args.projects else list(PROJECT_DEFINITIONS.keys())

    # Validate project keys
    invalid_keys = [k for k in projects_to_create if k not in PROJECT_DEFINITIONS]
    if invalid_keys:
        print(f"❌ Error: Invalid project keys: {', '.join(invalid_keys)}")
        print(f"   Valid keys: {', '.join(PROJECT_DEFINITIONS.keys())}")
        sys.exit(1)

    print(f"\n{'=' * 80}")
    print(f"Create All GitHub Projects - {'DRY RUN' if args.dry_run else 'APPLY'}")
    print(f"{'=' * 80}\n")
    print(f"Organization: {args.org}")
    print(f"Projects to create: {len(projects_to_create)}")
    print()

    # Summary stats
    total_created = 0
    total_failed = 0
    manual_steps_files = []

    # Create each project
    for idx, project_key in enumerate(projects_to_create, 1):
        project_def = PROJECT_DEFINITIONS[project_key]
        print(f"[{idx}/{len(projects_to_create)}] {project_def['title']}")

        # Step 1: Create project
        success, project_number = create_project(args.org, project_key, project_def, args.dry_run)

        if not success:
            total_failed += 1
            continue

        total_created += 1

        # Step 2: Create labels
        if not args.dry_run:
            print("   Creating labels...")
            labels_created = create_labels(args.org, project_def, args.dry_run)
            if labels_created > 0:
                print(f"   ✅ Created {labels_created} labels")

        # Step 3: Document manual steps
        if not args.dry_run and project_number != "dry-run":
            manual_file = f"/tmp/project-{project_number}-manual-setup.md"
            instructions = document_manual_steps(project_key, project_def, project_number)

            with open(manual_file, "w") as f:
                f.write(instructions)

            manual_steps_files.append((project_def["title"], project_number, manual_file))
            print(f"   📝 Manual setup guide: {manual_file}")

        print()

        # Rate limit pause
        if not args.dry_run:
            time.sleep(1)

    # Summary
    print(f"{'=' * 80}")
    print("Summary")
    print(f"{'=' * 80}\n")
    print(f"✅ Projects created: {total_created}")
    print(f"❌ Projects failed: {total_failed}")

    if manual_steps_files:
        print(f"\n📝 Manual setup required for {len(manual_steps_files)} projects:")
        for title, number, filepath in manual_steps_files:
            print(f"   - {title} (#{number}): {filepath}")
        print()
        print("Each file contains step-by-step instructions for:")
        print("   1. Configuring automation workflows (auto-add, auto-status, auto-archive)")
        print("   2. Creating filtered views")
        print("   3. Verification checklist")
        print()
        print("Estimated time: 5 minutes per project (~{} minutes total)".format(len(manual_steps_files) * 5))

    print(f"\n{'=' * 80}\n")

    if args.dry_run:
        print("ℹ️ This was a dry run. Run with --apply to create projects.")
    else:
        print("✅ Done! Check manual setup guides in /tmp/")


if __name__ == "__main__":
    main()
