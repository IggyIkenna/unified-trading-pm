"""Helper functions for R&D Tax Credit Export Script."""

import csv
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

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


def run_command(cmd: list[str], cwd: Optional[Path] = None) -> str:
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


def get_closed_issues(repo: str, start_date: str, end_date: str) -> list[dict]:
    """Query GitHub for closed issues in date range."""
    print(f"Querying GitHub issues for {repo}...")
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


def find_commits_for_issue(repo_path: Path, issue_number: int) -> list[dict]:
    """Find all commits that reference an issue number."""
    patterns = [
        f"#{issue_number}",
        f"(#{issue_number})",
        f"fixes #{issue_number}",
        f"closes #{issue_number}",
        f"resolves #{issue_number}",
    ]
    commits = []
    for pattern in patterns:
        cmd = ["git", "log", "--all", "--grep", pattern, "--format=%H|%aI|%s"]
        output = run_command(cmd, cwd=repo_path)
        if output:
            for line in output.split("\n"):
                if not line:
                    continue
                parts = line.split("|", 2)
                if len(parts) == 3:
                    sha, timestamp, message = parts
                    if not any(c["sha"] == sha for c in commits):
                        commits.append({"sha": sha, "timestamp": timestamp, "message": message})
    commits.sort(key=lambda c: c["timestamp"])
    return commits


def calculate_actual_hours(commits: list[dict], issue_closed_at: str) -> float:
    """Calculate actual hours worked based on commit timestamps."""
    if not commits:
        return 0.0
    if len(commits) == 1:
        return 2.0
    first = datetime.fromisoformat(commits[0]["timestamp"].replace("Z", "+00:00"))
    last_c = datetime.fromisoformat(commits[-1]["timestamp"].replace("Z", "+00:00"))
    last_i = datetime.fromisoformat(issue_closed_at.replace("Z", "+00:00"))
    last = max(last_c, last_i)
    hours = (last - first).total_seconds() / 3600
    max_hours = ((last - first).days + 1) * 8
    return min(hours, max_hours)


def extract_time_estimate(issue_body: str) -> Optional[float]:
    """Extract time estimate from issue body."""
    if not issue_body:
        return None
    m = re.search(r"effort:\s*(\d+\.?\d*)\s*hours?", issue_body, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"time estimate:\s*(\d+\.?\d*)\s*days?", issue_body, re.IGNORECASE)
    if m:
        return float(m.group(1)) * 8
    m = re.search(r"estimate:\s*(\d+\.?\d*)\s*weeks?", issue_body, re.IGNORECASE)
    if m:
        return float(m.group(1)) * 40
    m = re.search(r"(\d+\.?\d*)\s*h(?:ours?)?", issue_body, re.IGNORECASE)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+\.?\d*)\s*d(?:ays?)?", issue_body, re.IGNORECASE)
    if m:
        return float(m.group(1)) * 8
    m = re.search(r"(\d+\.?\d*)\s*w(?:eeks?)?", issue_body, re.IGNORECASE)
    if m:
        return float(m.group(1)) * 40
    return None


def extract_data_cost(issue_body: str) -> Optional[float]:
    """Extract data cost from issue body."""
    if not issue_body:
        return None
    for pat in [
        r"data cost:\s*\$?([\d,]+\.?\d*)",
        r"cost:\s*\$?([\d,]+\.?\d*)",
        r"budget:\s*\$?([\d,]+\.?\d*)",
    ]:
        m = re.search(pat, issue_body, re.IGNORECASE)
        if m:
            return float(m.group(1).replace(",", ""))
    return None


def get_issue_type(labels: list[dict]) -> str:
    """Determine issue type from labels."""
    names = [label["name"].lower() for label in labels]
    if "feature" in names or "enhancement" in names:
        return "feature"
    if "bug" in names or "bugfix" in names:
        return "bug"
    if "research" in names or "r&d" in names or "spike" in names:
        return "research"
    if "infrastructure" in names or "devops" in names:
        return "infrastructure"
    if "documentation" in names:
        return "documentation"
    return "other"


def get_issue_area(labels: list[dict]) -> str:
    """Determine issue area from labels."""
    names = [label["name"].lower() for label in labels]
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
    for area, kw in area_map.items():
        if any(k in " ".join(names) for k in kw):
            return area
    return "general"


def get_service_from_repo(repo: str) -> str:
    """Extract service name from repo name."""
    return repo.replace("-service", "").replace("-services", "")


def build_issue_row(
    issue: dict,
    repo: str,
    commits: list[dict],
) -> dict:
    """Build a single row dict for export from issue and commits."""
    issue_number = issue["number"]
    actual_hours = calculate_actual_hours(commits, issue["closedAt"])
    time_estimate = extract_time_estimate(issue.get("body", ""))
    data_cost = extract_data_cost(issue.get("body", ""))
    issue_type = get_issue_type(issue.get("labels") or [])
    issue_area = get_issue_area(issue.get("labels") or [])
    assignees = issue.get("assignees") or []
    assignee = assignees[0]["login"] if assignees else "unassigned"
    start_date = commits[0]["timestamp"][:10] if commits else issue["closedAt"][:10]
    end_date = commits[-1]["timestamp"][:10] if commits else issue["closedAt"][:10]
    commit_shas = "; ".join(c["sha"][:7] for c in commits)
    technical_description = (issue.get("body", "") or "")[:500].replace("\n", " ").strip()

    return {
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


def process_repos_for_export(
    repos: list[str],
    workspace_root: Path,
    github_org: str,
    start_date: str,
    end_date: str,
) -> list[dict]:
    """Process repos and collect issue/commit data for export."""
    all_data: list[dict] = []
    for repo in repos:
        sep = "=" * 80
        print(f"\n{sep}\nProcessing repo: {repo}\n{sep}\n")
        full_repo = f"{github_org}/{repo}"
        issues = get_closed_issues(full_repo, start_date, end_date)
        if not issues:
            print(f"No closed issues found for {repo} in date range")
            continue
        repo_path = workspace_root / repo
        if not repo_path.exists():
            print(f"Warning: Repo not found at {repo_path}, skipping commit analysis")
            continue
        for issue in issues:
            issue_number = issue["number"]
            title_preview = issue["title"][:60]
            print(f"Processing issue #{issue_number}: {title_preview}...")
            commits = find_commits_for_issue(repo_path, issue_number)
            if not commits:
                print(f"  No commits found for issue #{issue_number}")
            all_data.append(build_issue_row(issue, repo, commits))
    return all_data


def print_export_summary(all_data: list[dict], output_path: Path) -> None:
    """Print export summary and breakdowns."""
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total issues: {len(all_data)}")
    print(f"Issues with commits: {sum(1 for d in all_data if d['commit_count'] > 0)}")
    print(f"Issues with time estimates: {sum(1 for d in all_data if d['time_estimate_hours'])}")
    print(f"Issues with data costs: {sum(1 for d in all_data if d['data_cost_usd'])}")

    total_est = sum(float(d["time_estimate_hours"]) for d in all_data if d["time_estimate_hours"])
    total_act = sum(float(d["actual_hours"]) for d in all_data if d["actual_hours"])
    total_cost = sum(float(d["data_cost_usd"]) for d in all_data if d["data_cost_usd"])
    print(f"\nTotal estimated hours: {total_est:.2f}")
    print(f"Total actual hours: {total_act:.2f}")
    print(f"Total data costs: ${total_cost:,.2f}")

    print("\nBreakdown by type:")
    for it in ["feature", "bug", "research", "infrastructure", "other"]:
        cnt = sum(1 for d in all_data if d["type"] == it)
        hrs = sum(float(d["actual_hours"]) for d in all_data if d["type"] == it and d["actual_hours"])
        print(f"  {it}: {cnt} issues, {hrs:.2f} hours")

    print("\nBreakdown by area:")
    for area in sorted(set(d["area"] for d in all_data)):
        cnt = sum(1 for d in all_data if d["area"] == area)
        hrs = sum(float(d["actual_hours"]) for d in all_data if d["area"] == area and d["actual_hours"])
        print(f"  {area}: {cnt} issues, {hrs:.2f} hours")

    print("\n" + "=" * 80)
    print(f"Export complete! Output: {output_path}")
    print("=" * 80)


def export_to_csv(data: list[dict], output_path: Path) -> None:
    """Export data to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fn = [
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
    with open(output_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fn)
        w.writeheader()
        w.writerows(data)
    print(f"\nExported {len(data)} issues to {output_path}")
