#!/usr/bin/env python3
"""
Create GitHub Issues from Epic Breakdown

Parses epic-post-trade-and-execution.md and creates 20 GitHub issues
across 4 repositories (position-balance-monitor-service,
risk-and-exposure-service, execution-service, live-health-monitor-ui).

Usage:
    # Dry run (preview):
    python 02-create-issues.py --org IggyIkenna \\
        --epic-file "../../epic-breakdowns/epic-post-trade-and-execution.md" \\
        --dry-run

    # Apply changes:
    python 02-create-issues.py --org IggyIkenna \\
        --epic-file "../../epic-breakdowns/epic-post-trade-and-execution.md" \\
        --apply

Requires:
    - gh CLI authenticated with repo scope
    - Epic breakdown file with subtasks

Python 3.13+
"""

import argparse
import json
import re
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

        if result.returncode == 0:
            if result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return result.stdout.strip()
            return ""

        if not check:
            return {"_error": True, "stderr": result.stderr.strip(), "returncode": result.returncode}

        return None

    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd)}")
        print(f"   Error: {e.stderr}")
        if check:
            raise
        return None


def parse_epic_breakdown(epic_file: Path) -> list[dict[str, Any]]:
    """Parse epic breakdown markdown file and extract subtasks."""
    print(f"\n📊 Parsing epic breakdown: {epic_file}")

    if not epic_file.exists():
        print(f"❌ Epic file not found: {epic_file}")
        sys.exit(1)

    content = epic_file.read_text()

    # Extract all subtasks (### Subtask X.Y.Z: Title format)
    subtask_pattern = r"### (Subtask \d+\.\d+(?:\.\d+)?): (.+?)(?=\n\n###|\Z)"
    subtasks = []

    for match in re.finditer(subtask_pattern, content, re.DOTALL):
        subtask_id = match.group(1)
        subtask_content = match.group(2)

        # Extract title (first line after subtask ID)
        title_match = re.search(r"^(.+?)$", subtask_content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "Unknown"

        # Extract fields
        description = extract_field(subtask_content, "Description")
        complexity = extract_field(subtask_content, "Complexity")
        priority = extract_field(subtask_content, "Priority")
        risk = extract_field(subtask_content, "Risk")
        estimated = extract_field(subtask_content, "Estimated")
        files = extract_field(subtask_content, "Files to modify")
        codex_sections = extract_field(subtask_content, "Codex sections")
        tests = extract_field(subtask_content, "Tests required")
        blocking = extract_field(subtask_content, "Blocking")
        parent = extract_field(subtask_content, "Parent")

        # Determine target repo from files
        repo = determine_repo(files, title, subtask_id)

        subtask = {
            "id": subtask_id,
            "title": f"[PostTrade] {title}",
            "description": description,
            "complexity": complexity,
            "priority": priority,
            "risk": risk,
            "estimated": estimated,
            "files": files,
            "codex_sections": codex_sections,
            "tests": tests,
            "blocking": blocking,
            "parent": parent,
            "repo": repo,
        }

        subtasks.append(subtask)

    print(f"   Found: {len(subtasks)} subtasks")

    # Group by repo
    repo_counts = {}
    for subtask in subtasks:
        repo = subtask["repo"]
        repo_counts[repo] = repo_counts.get(repo, 0) + 1

    print("\n   Distribution:")
    for repo, count in sorted(repo_counts.items()):
        print(f"     - {repo}: {count} issues")

    return subtasks


def extract_field(content: str, field_name: str) -> str:
    """Extract field value from subtask content."""
    pattern = rf"-\s+\*\*{re.escape(field_name)}:\*\*\s+(.+?)(?=\n\s*-\s+\*\*|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return ""


def determine_repo(files: str, title: str, subtask_id: str) -> str:
    """Determine target repository from files to modify."""
    # Check for repo names in files field
    if "position-balance-monitor-service" in files or "position_monitor" in files:
        return "position-balance-monitor-service"
    elif "risk-and-exposure-service" in files or "risk_exposure" in files:
        return "risk-and-exposure-service"
    elif (
        "live-health-monitor-ui" in files
        or "manual-trading-controls-ui" in title.lower()
        or "manual trading" in title.lower()
    ):
        return "live-health-monitor-ui"
    elif "execution-service" in files or "execution_service" in files:
        return "execution-service"

    # Fallback: infer from subtask ID (Task number)
    if "Subtask 1." in subtask_id:  # Task 1: position-monitor
        return "position-balance-monitor-service"
    elif "Subtask 2." in subtask_id:  # Task 2: risk-and-exposure
        return "risk-and-exposure-service"
    elif "Subtask 3." in subtask_id:  # Task 3: execution-service
        # Check if UI-related
        if "UI" in title or "manual trading" in title.lower():
            return "live-health-monitor-ui"
        return "execution-service"

    # Default to execution-service (most complex)
    return "execution-service"


def create_issue_body(subtask: dict[str, Any]) -> str:
    """Generate GitHub issue body from subtask data."""
    body = f"""## Description

{subtask["description"]}

## Complexity

{subtask["complexity"]}

## Priority

{subtask["priority"]}

## Risk

{subtask["risk"]}

## Estimated Hours

{subtask["estimated"]}

## Files to Modify

{subtask["files"]}

## Codex References

{subtask["codex_sections"]}

## Tests Required

{subtask["tests"]}

## Blocking

{subtask["blocking"]}

## Parent

{subtask["parent"]}

---

**Epic:** Post-Trade and Execution
**Subtask ID:** {subtask["id"]}
**Label:** `POST-TRADE-AND-EXECUTION`
"""
    return body


def get_priority_label(priority: str) -> str:
    """Extract priority label from priority field."""
    if "P0" in priority or "critical" in priority.lower():
        return "P0-critical"
    elif "P1" in priority or "high" in priority.lower():
        return "P1-high"
    elif "P2" in priority or "medium" in priority.lower():
        return "P2-medium"
    elif "P3" in priority or "low" in priority.lower():
        return "P3-low"
    return "P2-medium"  # Default


def create_issues(org: str, subtasks: list[dict[str, Any]], dry_run: bool = True) -> dict[str, list[dict[str, Any]]]:
    """Create GitHub issues for all subtasks."""
    print(f"\n📋 {'[DRY RUN] ' if dry_run else ''}Creating issues...")

    issue_manifest = {}

    for subtask in subtasks:
        repo = subtask["repo"]
        title = subtask["title"]
        body = create_issue_body(subtask)
        priority_label = get_priority_label(subtask["priority"])

        print(f"\n  {subtask['id']}: {title}")
        print(f"    Repo: {repo}")
        print(f"    Priority: {priority_label}")

        if dry_run:
            print(f"    [DRY RUN] Would create issue in {org}/{repo}")
            issue_manifest.setdefault(repo, []).append(
                {
                    "subtask_id": subtask["id"],
                    "title": title,
                    "number": None,
                    "url": None,
                    "dry_run": True,
                }
            )
            continue

        # Check if issue already exists
        existing = run_gh_command(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                f"{org}/{repo}",
                "--search",
                f'"{title}" in:title',
                "--json",
                "number,title",
                "--limit",
                "1",
            ],
            check=False,
        )

        if existing and isinstance(existing, list) and len(existing) > 0:
            issue_number = existing[0]["number"]
            print(f"    ✅ Issue already exists: #{issue_number}")
            issue_manifest.setdefault(repo, []).append(
                {
                    "subtask_id": subtask["id"],
                    "title": title,
                    "number": issue_number,
                    "url": f"https://github.com/{org}/{repo}/issues/{issue_number}",
                    "existing": True,
                }
            )
            continue

        # Create issue
        try:
            result = run_gh_command(
                [
                    "gh",
                    "issue",
                    "create",
                    "--repo",
                    f"{org}/{repo}",
                    "--title",
                    title,
                    "--body",
                    body,
                    "--label",
                    f"POST-TRADE-AND-EXECUTION,{priority_label}",
                    "--assignee",
                    "@me",
                ]
            )

            if result:
                issue_url = result if isinstance(result, str) else result.get("url", "")
                issue_number = issue_url.split("/")[-1] if issue_url else "unknown"
                print(f"    ✅ Created issue: #{issue_number}")
                print(f"       {issue_url}")

                issue_manifest.setdefault(repo, []).append(
                    {
                        "subtask_id": subtask["id"],
                        "title": title,
                        "number": issue_number,
                        "url": issue_url,
                        "existing": False,
                    }
                )
        except (ConnectionError, TimeoutError, OSError, ValueError) as e:
            print(f"    ❌ Failed to create issue: {e}")
            issue_manifest.setdefault(repo, []).append(
                {
                    "subtask_id": subtask["id"],
                    "title": title,
                    "number": None,
                    "url": None,
                    "error": str(e),
                }
            )

    return issue_manifest


def save_manifest(manifest: dict[str, list[dict[str, Any]]], output_file: Path):
    """Save issue manifest to JSON file."""
    output_file.write_text(json.dumps(manifest, indent=2))
    print(f"\n📝 Issue manifest saved to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Create GitHub issues from epic breakdown")
    parser.add_argument("--org", default="IggyIkenna", help="GitHub organization/user")
    parser.add_argument("--epic-file", required=True, help="Path to epic breakdown markdown file")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without creating issues")
    parser.add_argument("--apply", action="store_true", help="Apply changes (create issues)")
    parser.add_argument("--output", default="issue-manifest.json", help="Output file for issue manifest")

    args = parser.parse_args()

    if not args.dry_run and not args.apply:
        print("❌ Error: Specify either --dry-run or --apply")
        sys.exit(1)

    epic_file = Path(args.epic_file)
    output_file = Path(args.output)

    print("========================================")
    print("GitHub Issue Creation")
    print("========================================")
    print(f"Organization: {args.org}")
    print(f"Epic file: {epic_file}")
    print(f"Mode: {'DRY RUN' if args.dry_run else 'APPLY'}")
    print("")

    # Parse epic breakdown
    subtasks = parse_epic_breakdown(epic_file)

    if not subtasks:
        print("\n❌ No subtasks found in epic breakdown")
        sys.exit(1)

    # Create issues
    issue_manifest = create_issues(args.org, subtasks, dry_run=args.dry_run)

    # Save manifest
    save_manifest(issue_manifest, output_file)

    # Summary
    print("\n========================================")
    print("Summary")
    print("========================================")
    total_issues = sum(len(issues) for issues in issue_manifest.values())
    print(f"Total subtasks: {len(subtasks)}")
    print(f"Issues {'would be created' if args.dry_run else 'created'}: {total_issues}")
    print("")
    print("Distribution:")
    for repo, issues in sorted(issue_manifest.items()):
        print(f"  - {repo}: {len(issues)} issues")
    print("")

    if not args.dry_run:
        print("Next steps:")
        print("  1. Link issues to project (Stage 4):")
        print("     bash 03-link-issues-to-project.sh --project <NUMBER> --issue-manifest issue-manifest.json")
        print("")

    print("========================================")


if __name__ == "__main__":
    main()
