#!/usr/bin/env python3
"""
Re-link Sub-Issues After Rate Limit Reset

This script finds Epic/Task/Subtask issues that were created but not linked
(due to rate limits) and re-establishes the parent-child relationships.

Usage:
  python relink-sub-issues.py [--dry-run]
"""

import argparse
import json
import subprocess
import sys
import time
from typing import cast

ORG = "IggyIkenna"
REPO = "unified-trading-codex"


def check_rate_limit() -> dict[str, object]:
    """Check GitHub GraphQL API rate limits."""
    cmd: list[str] = ["gh", "api", "rate_limit", "--jq", ".resources.graphql"]
    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return {"remaining": 0, "limit": 5000, "reset": 0}
    return cast(dict[str, object], json.loads(result.stdout))


def get_issue_node_id(issue_number: int) -> str | None:
    """Get the node_id for an issue."""
    cmd: list[str] = ["gh", "api", f"/repos/{ORG}/{REPO}/issues/{issue_number}", "--jq", ".node_id"]
    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def link_sub_issue(parent_num: int, sub_num: int, dry_run: bool) -> bool | None:
    """Link a sub-issue to its parent. Returns None on rate limit."""
    if dry_run:
        print(f"  [DRY RUN] Would link #{sub_num} -> #{parent_num}")
        return True

    parent_node = get_issue_node_id(parent_num)
    sub_node = get_issue_node_id(sub_num)

    if not parent_node or not sub_node:
        return False

    query = (
        "mutation {"
        f"  addSubIssue(input: {{"
        f'    issueId: "{parent_node}",'
        f'    subIssueId: "{sub_node}"'
        "  }) {"
        "    issue { number }"
        "    subIssue { number }"
        "  }"
        "}"
    )

    cmd: list[str] = ["gh", "api", "graphql", "-f", f"query={query}"]
    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        if "rate limit" in result.stderr.lower():
            print("  Rate limit hit again - stopping")
            return None  # Signal to stop
        return False

    print(f"  Linked #{sub_num} -> #{parent_num}")
    time.sleep(0.2)  # Small delay to avoid hammering API
    return True


def get_all_issues() -> list[dict[str, object]]:
    """Get all open issues."""
    cmd: list[str] = [
        "gh",
        "issue",
        "list",
        "--repo",
        f"{ORG}/{REPO}",
        "--state",
        "open",
        "--limit",
        "1000",
        "--json",
        "number,title,body",
    ]
    result: subprocess.CompletedProcess[str] = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return []
    return cast(list[dict[str, object]], json.loads(result.stdout))


def main() -> None:
    parser = argparse.ArgumentParser(description="Re-link sub-issues after rate limit reset")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
    parsed = parser.parse_args()
    dry_run: bool = bool(getattr(parsed, "dry_run", False))

    print("Re-linking Sub-Issues")
    print("=" * 80)

    # Check rate limit
    rate_limit = check_rate_limit()
    remaining_raw = rate_limit.get("remaining", 0)
    remaining = int(remaining_raw) if isinstance(remaining_raw, (int, float)) else 0
    limit_raw = rate_limit.get("limit", 5000)
    limit = int(limit_raw) if isinstance(limit_raw, (int, float)) else 5000

    print(f"\nGraphQL Rate Limit: {remaining}/{limit} remaining")

    if remaining < 100:
        reset_raw = rate_limit.get("reset", 0)
        reset_time = int(reset_raw) if isinstance(reset_raw, (int, float)) else 0
        wait_seconds = max(0, reset_time - int(time.time()))
        print(f"Rate limit low - resets in {int(wait_seconds / 60)} minutes")
        if not dry_run and wait_seconds > 0:
            response = input(f"\nWait {int(wait_seconds / 60)} minutes? (y/n): ")
            if response.lower() != "y":
                sys.exit(0)
            print("Waiting...")
            time.sleep(wait_seconds + 5)

    print("\nFetching all issues...")
    issues = get_all_issues()

    epics: dict[int, dict[str, str]] = {}
    tasks: dict[int, dict[str, str | int]] = {}
    subtasks: list[dict[str, int]] = []

    # Categorize issues
    for issue in issues:
        num = int(str(issue.get("number", 0)))
        title = str(issue.get("title", ""))
        body = str(issue.get("body", "") or "")

        if "[Epic]" in title:
            epics[num] = {"title": title, "body": body}
        elif "[Task]" in title:
            # Extract parent Epic from body
            for line in body.split("\n"):
                if "**Parent Epic:**" in line and "#" in line:
                    epic_num = int(line.split("#")[1].split()[0])
                    tasks[num] = {"title": title, "epic": epic_num}
                    break
        elif "[Subtask]" in title:
            # Extract parent Task from body
            for line in body.split("\n"):
                if "**Parent Task:**" in line and "#" in line:
                    task_num = int(line.split("#")[1].split()[0])
                    subtasks.append({"num": num, "task": task_num})
                    break

    print(f"  Found: {len(epics)} Epics, {len(tasks)} Tasks, {len(subtasks)} Subtasks")

    # Re-link Tasks -> Epics
    print("\nLinking Tasks -> Epics...")
    linked_count = 0
    for task_num, task_data in tasks.items():
        epic_num_val = task_data.get("epic")
        if isinstance(epic_num_val, int) and epic_num_val in epics:
            link_result = link_sub_issue(epic_num_val, task_num, dry_run)
            if link_result is None:  # Rate limit hit
                break
            if link_result:
                linked_count += 1

    print(f"  Linked {linked_count} Tasks")

    # Re-link Subtasks -> Tasks
    print("\nLinking Subtasks -> Tasks...")
    linked_count = 0
    for subtask_data in subtasks:
        subtask_num = subtask_data["num"]
        task_num_val = subtask_data["task"]
        if task_num_val in tasks:
            link_result = link_sub_issue(task_num_val, subtask_num, dry_run)
            if link_result is None:  # Rate limit hit
                break
            if link_result:
                linked_count += 1

    print(f"  Linked {linked_count} Subtasks")

    print("\nRe-linking complete!")


if __name__ == "__main__":
    main()
