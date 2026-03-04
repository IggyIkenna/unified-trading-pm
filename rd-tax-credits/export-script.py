#!/usr/bin/env python3
"""
R&D Tax Credit Export Script

Queries GitHub issues and git commits to generate a CSV export for R&D tax credit claims.
Calculates actual hours worked based on commit timestamps and extracts time/cost estimates
from issue bodies.

Usage:
    python export-script.py --start-date 2024-01-01 --end-date 2024-12-31 --output exports/rd-claim-2024.csv
    python export-script.py --start-date 2024-01-01 --end-date 2024-12-31 \
        --output exports/rd-claim-2024.csv --repo unified-trading-deployment-v3
    python export-script.py --start-date 2024-01-01 --end-date 2024-12-31 --output exports/rd-claim-2024.csv --all-repos

Requirements:
    - gh CLI installed and authenticated
    - git repositories cloned locally
    - Python 3.8+
"""

import argparse
import csv
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Default repos to scan (if --all-repos flag used)
DEFAULT_REPOS = [
    "unified-trading-deployment-v3",
    "instruments-service",
    "market-tick-data-service",
    "market-data-processing-service",
    "features-delta-one-service",
    "features-calendar-service",
    "features-volatility-service",
    "features-onchain-service",
    "ml-inference-service",
    "ml-training-service",
    "strategy-service",
    "corporate-actions",
    "execution-service",
    "unified-trading-services",
]


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> str:
    """Run shell command and return output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e.stderr}")
        return ""


def get_closed_issues(repo: str, start_date: str, end_date: str) -> List[Dict]:
    """
    Query GitHub for closed issues in date range.

    Returns list of dicts with: number, title, labels, assignees, closed_at, body
    """
    print(f"Querying GitHub issues for {repo}...")

    # Use gh CLI to query issues
    # Format: closed:YYYY-MM-DD..YYYY-MM-DD
    cmd = [
        "gh",
        "issue",
        "list",
        "--repo",
        repo,
        "--state",
        "closed",
        "--search",
        f"closed:{start_date}..{end_date}",
        "--limit",
        "1000",
        "--json",
        "number,title,labels,assignees,closedAt,body",
    ]

    output = run_command(cmd)
    if not output:
        return []

    try:
        issues = json.loads(output)
        print(f"Found {len(issues)} closed issues")
        return issues
    except json.JSONDecodeError as e:
        print(f"Error parsing GitHub response: {e}")
        return []


def find_commits_for_issue(repo_path: Path, issue_number: int) -> List[Dict]:
    """
    Find all commits that reference an issue number.

    Returns list of dicts with: sha, timestamp, message
    """
    # Search git log for issue number in commit message
    # Patterns: #123, (#123), "fixes #123", "closes #123", etc.
    patterns = [
        f"#{issue_number}",
        f"(#{issue_number})",
        f"fixes #{issue_number}",
        f"closes #{issue_number}",
        f"resolves #{issue_number}",
    ]

    commits = []

    for pattern in patterns:
        cmd = [
            "git",
            "log",
            "--all",
            "--grep",
            pattern,
            "--format=%H|%aI|%s",  # SHA|ISO timestamp|subject
        ]

        output = run_command(cmd, cwd=repo_path)
        if output:
            for line in output.split("\n"):
                if not line:
                    continue

                parts = line.split("|", 2)
                if len(parts) == 3:
                    sha, timestamp, message = parts

                    # Avoid duplicates (same commit matching multiple patterns)
                    if not any(c["sha"] == sha for c in commits):
                        commits.append(
                            {
                                "sha": sha,
                                "timestamp": timestamp,
                                "message": message,
                            }
                        )

    # Sort by timestamp
    commits.sort(key=lambda c: c["timestamp"])

    return commits


def calculate_actual_hours(commits: List[Dict], issue_closed_at: str) -> float:
    """
    Calculate actual hours worked based on commit timestamps.

    Uses first commit timestamp to last commit (or issue close) timestamp.
    If only 1 commit, assumes 2 hours minimum.
    """
    if not commits:
        return 0.0

    if len(commits) == 1:
        # Single commit: assume 2 hours minimum
        return 2.0

    # Multiple commits: calculate time between first and last
    first_timestamp = datetime.fromisoformat(commits[0]["timestamp"].replace("Z", "+00:00"))

    # Use last commit or issue close time, whichever is later
    last_commit_timestamp = datetime.fromisoformat(commits[-1]["timestamp"].replace("Z", "+00:00"))
    issue_close_timestamp = datetime.fromisoformat(issue_closed_at.replace("Z", "+00:00"))

    last_timestamp = max(last_commit_timestamp, issue_close_timestamp)

    # Calculate hours
    time_delta = last_timestamp - first_timestamp
    hours = time_delta.total_seconds() / 3600

    # Cap at reasonable maximum (8 hours per day * days)
    days = time_delta.days + 1
    max_hours = days * 8

    return min(hours, max_hours)


def extract_time_estimate(issue_body: str) -> Optional[float]:
    """
    Extract time estimate from issue body.

    Looks for patterns like:
    - "Effort: 16 hours"
    - "Time estimate: 2 days" (convert to hours)
    - "Estimate: 1 week" (convert to hours)
    """
    if not issue_body:
        return None

    # Pattern: "Effort: 16 hours"
    match = re.search(r"effort:\s*(\d+\.?\d*)\s*hours?", issue_body, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Pattern: "Time estimate: 2 days"
    match = re.search(r"time estimate:\s*(\d+\.?\d*)\s*days?", issue_body, re.IGNORECASE)
    if match:
        return float(match.group(1)) * 8  # 8 hours per day

    # Pattern: "Estimate: 1 week"
    match = re.search(r"estimate:\s*(\d+\.?\d*)\s*weeks?", issue_body, re.IGNORECASE)
    if match:
        return float(match.group(1)) * 40  # 40 hours per week

    # Pattern: "16h" or "2d" or "1w"
    match = re.search(r"(\d+\.?\d*)\s*h(?:ours?)?", issue_body, re.IGNORECASE)
    if match:
        return float(match.group(1))

    match = re.search(r"(\d+\.?\d*)\s*d(?:ays?)?", issue_body, re.IGNORECASE)
    if match:
        return float(match.group(1)) * 8

    match = re.search(r"(\d+\.?\d*)\s*w(?:eeks?)?", issue_body, re.IGNORECASE)
    if match:
        return float(match.group(1)) * 40

    return None


def extract_data_cost(issue_body: str) -> Optional[float]:
    """
    Extract data cost from issue body.

    Looks for patterns like:
    - "Data cost: $1,250"
    - "Cost: $500"
    - "Budget: $2,000"
    """
    if not issue_body:
        return None

    # Pattern: "Data cost: $1,250" or "Cost: $1,250.50"
    patterns = [
        r"data cost:\s*\$?([\d,]+\.?\d*)",
        r"cost:\s*\$?([\d,]+\.?\d*)",
        r"budget:\s*\$?([\d,]+\.?\d*)",
    ]

    for pattern in patterns:
        match = re.search(pattern, issue_body, re.IGNORECASE)
        if match:
            # Remove commas and convert to float
            cost_str = match.group(1).replace(",", "")
            return float(cost_str)

    return None


def get_issue_type(labels: List[Dict]) -> str:
    """
    Determine issue type from labels.

    Maps to R&D categories: feature, bug, enhancement, research, infrastructure
    """
    label_names = [label["name"].lower() for label in labels]

    if "feature" in label_names or "enhancement" in label_names:
        return "feature"
    elif "bug" in label_names or "bugfix" in label_names:
        return "bug"
    elif "research" in label_names or "r&d" in label_names or "spike" in label_names:
        return "research"
    elif "infrastructure" in label_names or "devops" in label_names:
        return "infrastructure"
    elif "documentation" in label_names:
        return "documentation"
    else:
        return "other"


def get_issue_area(labels: List[Dict]) -> str:
    """
    Determine issue area from labels.

    Maps to codex areas: domain, data, observability, architecture, infrastructure,
    coding, security, workflows, analysis
    """
    label_names = [label["name"].lower() for label in labels]

    area_map = {
        "domain": ["domain", "strategy", "instruments"],
        "data": ["data", "schema", "pipeline"],
        "observability": ["observability", "logging", "monitoring", "alerting"],
        "architecture": ["architecture", "design", "scalability"],
        "infrastructure": ["infrastructure", "deployment", "ci/cd", "docker"],
        "coding": ["code quality", "refactoring", "testing"],
        "security": ["security", "credentials", "iam"],
        "workflows": ["workflows", "reconciliation", "disaster recovery"],
        "analysis": ["analysis", "backtest", "performance"],
    }

    for area, keywords in area_map.items():
        if any(keyword in " ".join(label_names) for keyword in keywords):
            return area

    return "general"


def get_service_from_repo(repo: str) -> str:
    """Extract service name from repo name."""
    # Remove common suffixes
    service = repo.replace("-service", "").replace("-services", "")
    return service


def export_to_csv(data: List[Dict], output_path: Path):
    """Export data to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "issue_number",
        "title",
        "type",
        "area",
        "service",
        "assignee",
        "time_estimate_hours",
        "actual_hours",
        "data_cost_usd",
        "start_date",
        "end_date",
        "commit_count",
        "commit_shas",
        "technical_description",
        "repo",
    ]

    with open(output_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    print(f"\nExported {len(data)} issues to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Export GitHub issues and commits for R&D tax credit claims")
    parser.add_argument(
        "--start-date",
        required=True,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output CSV file path",
    )
    parser.add_argument(
        "--repo",
        help="Single repository to scan (e.g., unified-trading-deployment-v3)",
    )
    parser.add_argument(
        "--all-repos",
        action="store_true",
        help="Scan all repos in the workspace",
    )
    parser.add_argument(
        "--workspace-root",
        default=".",
        help="Path to workspace root (default: current directory)",
    )
    parser.add_argument(
        "--github-org",
        default="IggyIkenna",
        help="GitHub organization/user (default: IggyIkenna)",
    )

    args = parser.parse_args()

    # Determine which repos to scan
    if args.all_repos:
        repos = DEFAULT_REPOS
    elif args.repo:
        repos = [args.repo]
    else:
        print("Error: Must specify either --repo or --all-repos")
        return 1

    workspace_root = Path(args.workspace_root).resolve()
    all_data = []

    for repo in repos:
        print(f"\n{'=' * 80}")
        print(f"Processing repo: {repo}")
        print(f"{'=' * 80}\n")

        # Get closed issues from GitHub
        full_repo = f"{args.github_org}/{repo}"
        issues = get_closed_issues(full_repo, args.start_date, args.end_date)

        if not issues:
            print(f"No closed issues found for {repo} in date range")
            continue

        # Find local repo path
        repo_path = workspace_root / repo
        if not repo_path.exists():
            print(f"Warning: Repo not found at {repo_path}, skipping commit analysis")
            continue

        for issue in issues:
            issue_number = issue["number"]
            print(f"Processing issue #{issue_number}: {issue['title'][:60]}...")

            # Find commits referencing this issue
            commits = find_commits_for_issue(repo_path, issue_number)

            if not commits:
                print(f"  No commits found for issue #{issue_number}")
                # Still include in export, but with 0 actual hours

            # Calculate actual hours
            actual_hours = calculate_actual_hours(commits, issue["closedAt"])

            # Extract time estimate and data cost from issue body
            time_estimate = extract_time_estimate(issue.get("body", ""))
            data_cost = extract_data_cost(issue.get("body", ""))

            # Determine issue type and area
            issue_type = get_issue_type(issue.get("labels", []))
            issue_area = get_issue_area(issue.get("labels", []))

            # Get assignee (first one if multiple)
            assignees = issue.get("assignees", [])
            assignee = assignees[0]["login"] if assignees else "unassigned"

            # Get start and end dates
            start_date = commits[0]["timestamp"][:10] if commits else issue["closedAt"][:10]
            end_date = commits[-1]["timestamp"][:10] if commits else issue["closedAt"][:10]

            # Get commit SHAs
            commit_shas = "; ".join(c["sha"][:7] for c in commits)

            # Technical description (from issue body, first 500 chars)
            technical_description = (issue.get("body", "") or "")[:500].replace("\n", " ").strip()

            # Add to data
            all_data.append(
                {
                    "issue_number": issue_number,
                    "title": issue["title"],
                    "type": issue_type,
                    "area": issue_area,
                    "service": get_service_from_repo(repo),
                    "assignee": assignee,
                    "time_estimate_hours": time_estimate or "",
                    "actual_hours": round(actual_hours, 2) if actual_hours > 0 else "",
                    "data_cost_usd": data_cost or "",
                    "start_date": start_date,
                    "end_date": end_date,
                    "commit_count": len(commits),
                    "commit_shas": commit_shas,
                    "technical_description": technical_description,
                    "repo": repo,
                }
            )

    # Export to CSV
    output_path = Path(args.output)
    export_to_csv(all_data, output_path)

    # Print summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total issues: {len(all_data)}")
    print(f"Issues with commits: {sum(1 for d in all_data if d['commit_count'] > 0)}")
    print(f"Issues with time estimates: {sum(1 for d in all_data if d['time_estimate_hours'])}")
    print(f"Issues with data costs: {sum(1 for d in all_data if d['data_cost_usd'])}")

    total_estimated_hours = sum(float(d["time_estimate_hours"]) for d in all_data if d["time_estimate_hours"])
    total_actual_hours = sum(float(d["actual_hours"]) for d in all_data if d["actual_hours"])
    total_data_costs = sum(float(d["data_cost_usd"]) for d in all_data if d["data_cost_usd"])

    print(f"\nTotal estimated hours: {total_estimated_hours:.2f}")
    print(f"Total actual hours: {total_actual_hours:.2f}")
    print(f"Total data costs: ${total_data_costs:,.2f}")

    # Breakdown by type
    print("\nBreakdown by type:")
    for issue_type in ["feature", "bug", "research", "infrastructure", "other"]:
        count = sum(1 for d in all_data if d["type"] == issue_type)
        hours = sum(float(d["actual_hours"]) for d in all_data if d["type"] == issue_type and d["actual_hours"])
        print(f"  {issue_type}: {count} issues, {hours:.2f} hours")

    # Breakdown by area
    print("\nBreakdown by area:")
    areas = set(d["area"] for d in all_data)
    for area in sorted(areas):
        count = sum(1 for d in all_data if d["area"] == area)
        hours = sum(float(d["actual_hours"]) for d in all_data if d["area"] == area and d["actual_hours"])
        print(f"  {area}: {count} issues, {hours:.2f} hours")

    print("\n" + "=" * 80)
    print(f"Export complete! Output: {output_path}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    exit(main())
