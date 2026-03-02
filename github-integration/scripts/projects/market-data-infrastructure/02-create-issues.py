#!/usr/bin/env python3
"""
Create GitHub Issues from Epic Breakdown

Parses epic-market-data-infrastructure.md and creates 4 GitHub issues
in market-tick-data-handler repository.

Usage:
    # Dry run (preview):
    python 02-create-issues.py --org IggyIkenna \
        --epic-file "../../epic-breakdowns/epic-market-data-infrastructure.md" \
        --dry-run

    # Apply changes:
    python 02-create-issues.py --org IggyIkenna \
        --epic-file "../../epic-breakdowns/epic-market-data-infrastructure.md" \
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

        if result.returncode == 0:
            if result.stdout.strip():
                try:
                    raw_parsed: object = cast(object, json.loads(result.stdout))
                    if isinstance(raw_parsed, list):
                        return cast(list[object], raw_parsed)
                    return cast(JsonDict, raw_parsed)
                except json.JSONDecodeError:
                    return result.stdout.strip()
            return ""

        if not check:
            return {"_error": True, "stderr": result.stderr.strip(), "returncode": result.returncode}

        return None

    except subprocess.CalledProcessError as e:
        raw_stderr: object = getattr(e, "stderr", None)
        print(f"  Command failed: {' '.join(cmd)}")
        print(f"   Error: {raw_stderr}")
        if check:
            raise
        return None


def parse_epic_breakdown(epic_file: Path) -> list[JsonDict]:
    """Parse epic breakdown markdown file and extract subtasks."""
    print(f"\n  Parsing epic breakdown: {epic_file}")

    if not epic_file.exists():
        print(f"  Epic file not found: {epic_file}")
        sys.exit(1)

    content: str = epic_file.read_text()

    # Extract all subtasks (### Subtask X.Y.Z: Title format)
    subtask_pattern = r"### (Subtask \d+\.\d+(?:\.\d+)?): (.+?)(?=\n\n###|\Z)"
    subtasks: list[JsonDict] = []

    for match in re.finditer(subtask_pattern, content, re.DOTALL):
        subtask_id: str = match.group(1)
        subtask_content: str = match.group(2)

        # Extract title (first line after subtask ID)
        title_match = re.search(r"^(.+?)$", subtask_content, re.MULTILINE)
        title: str = title_match.group(1).strip() if title_match else "Unknown"

        # Extract fields
        description: str = extract_field(subtask_content, "Description")
        complexity: str = extract_field(subtask_content, "Complexity")
        priority: str = extract_field(subtask_content, "Priority")
        risk: str = extract_field(subtask_content, "Risk")
        estimated: str = extract_field(subtask_content, "Estimated")
        files: str = extract_field(subtask_content, "Files to modify")
        codex_sections: str = extract_field(subtask_content, "Codex sections")
        tests: str = extract_field(subtask_content, "Tests required")
        blocking: str = extract_field(subtask_content, "Blocking")
        parent: str = extract_field(subtask_content, "Parent")

        # Determine target repo from files
        repo: str = determine_repo(files, title, subtask_id)

        subtask: JsonDict = {
            "id": subtask_id,
            "title": f"[MarketData] {title}",
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
    repo_counts: dict[str, int] = {}
    for st in subtasks:
        st_repo: str = str(st.get("repo", ""))
        repo_counts[st_repo] = repo_counts.get(st_repo, 0) + 1

    print("\n   Distribution:")
    for r_name, r_count in sorted(repo_counts.items()):
        print(f"     - {r_name}: {r_count} issues")

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
    # All subtasks for market-data-infrastructure go to market-tick-data-handler
    # (single service for this epic)
    _ = files, title, subtask_id  # Used for other epic variants
    return "market-tick-data-handler"


def create_issue_body(subtask: JsonDict) -> str:
    """Generate GitHub issue body from subtask data."""
    body: str = f"""## Description

{subtask.get("description", "")}

## Complexity

{subtask.get("complexity", "")}

## Priority

{subtask.get("priority", "")}

## Risk

{subtask.get("risk", "")}

## Estimated Hours

{subtask.get("estimated", "")}

## Files to Modify

{subtask.get("files", "")}

## Codex References

{subtask.get("codex_sections", "")}

## Tests Required

{subtask.get("tests", "")}

## Blocking

{subtask.get("blocking", "")}

## Parent

{subtask.get("parent", "")}

---

**Epic:** Market Data Infrastructure
**Subtask ID:** {subtask.get("id", "")}
**Label:** `MARKET-DATA-INFRASTRUCTURE`
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


def create_issues(org: str, subtasks: list[JsonDict], dry_run: bool = True) -> dict[str, list[JsonDict]]:
    """Create GitHub issues for all subtasks."""
    print(f"\n  {'[DRY RUN] ' if dry_run else ''}Creating issues...")

    issue_manifest: dict[str, list[JsonDict]] = {}

    for subtask in subtasks:
        repo: str = str(subtask.get("repo", ""))
        title: str = str(subtask.get("title", ""))
        body: str = create_issue_body(subtask)
        priority_label: str = get_priority_label(str(subtask.get("priority", "")))

        print(f"\n  {subtask.get('id', '')}: {title}")
        print(f"    Repo: {repo}")
        print(f"    Priority: {priority_label}")

        if dry_run:
            print(f"    [DRY RUN] Would create issue in {org}/{repo}")
            issue_manifest.setdefault(repo, []).append(
                {
                    "subtask_id": str(subtask.get("id", "")),
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
            first_item: JsonDict = cast(JsonDict, existing[0])
            issue_number_val: str = str(first_item.get("number", ""))
            print(f"    Issue already exists: #{issue_number_val}")
            issue_manifest.setdefault(repo, []).append(
                {
                    "subtask_id": str(subtask.get("id", "")),
                    "title": title,
                    "number": issue_number_val,
                    "url": f"https://github.com/{org}/{repo}/issues/{issue_number_val}",
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
                    f"MARKET-DATA-INFRASTRUCTURE,{priority_label}",
                    "--assignee",
                    "@me",
                ]
            )

            if result:
                issue_url: str = str(result) if isinstance(result, str) else str(cast(JsonDict, result).get("url", ""))
                issue_number_str: str = issue_url.split("/")[-1] if issue_url else "unknown"
                print(f"    Created issue: #{issue_number_str}")
                print(f"       {issue_url}")

                issue_manifest.setdefault(repo, []).append(
                    {
                        "subtask_id": str(subtask.get("id", "")),
                        "title": title,
                        "number": issue_number_str,
                        "url": issue_url,
                        "existing": False,
                    }
                )
        except (OSError, ValueError) as e:
            print(f"    Failed to create issue: {e}")
            issue_manifest.setdefault(repo, []).append(
                {
                    "subtask_id": str(subtask.get("id", "")),
                    "title": title,
                    "number": None,
                    "url": None,
                    "error": str(e),
                }
            )

    return issue_manifest


def save_manifest(manifest: dict[str, list[JsonDict]], output_file: Path) -> None:
    """Save issue manifest to JSON file."""
    output_file.write_text(json.dumps(manifest, indent=2))
    print(f"\n  Issue manifest saved to: {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create GitHub issues from epic breakdown")
    parser.add_argument("--org", default="IggyIkenna", help="GitHub organization/user")
    parser.add_argument("--epic-file", required=True, help="Path to epic breakdown markdown file")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without creating issues")
    parser.add_argument("--apply", action="store_true", help="Apply changes (create issues)")
    parser.add_argument("--output", default="issue-manifest.json", help="Output file for issue manifest")

    parsed = parser.parse_args()

    dry_run: bool = bool(getattr(parsed, "dry_run", False))
    apply_flag: bool = bool(getattr(parsed, "apply", False))
    org: str = str(getattr(parsed, "org", "IggyIkenna"))
    epic_file_str: str = str(getattr(parsed, "epic_file", ""))
    output_str: str = str(getattr(parsed, "output", "issue-manifest.json"))

    if not dry_run and not apply_flag:
        print("  Error: Specify either --dry-run or --apply")
        sys.exit(1)

    epic_file = Path(epic_file_str)
    output_file = Path(output_str)

    print("========================================")
    print("GitHub Issue Creation")
    print("========================================")
    print(f"Organization: {org}")
    print(f"Epic file: {epic_file}")
    print(f"Mode: {'DRY RUN' if dry_run else 'APPLY'}")
    print("")

    # Parse epic breakdown
    subtasks: list[JsonDict] = parse_epic_breakdown(epic_file)

    if not subtasks:
        print("\n  No subtasks found in epic breakdown")
        sys.exit(1)

    # Create issues
    issue_manifest: dict[str, list[JsonDict]] = create_issues(org, subtasks, dry_run=dry_run)

    # Save manifest
    save_manifest(issue_manifest, output_file)

    # Summary
    print("\n========================================")
    print("Summary")
    print("========================================")
    total_issues: int = sum(len(issues) for issues in issue_manifest.values())
    print(f"Total subtasks: {len(subtasks)}")
    print(f"Issues {'would be created' if dry_run else 'created'}: {total_issues}")
    print("")
    print("Distribution:")
    for repo_name, repo_issues in sorted(issue_manifest.items()):
        print(f"  - {repo_name}: {len(repo_issues)} issues")
    print("")

    if not dry_run:
        print("Next steps:")
        print("  1. Link issues to project (Stage 4):")
        print("     bash 03-link-issues-to-project.sh --project <NUMBER> --issue-manifest issue-manifest.json")
        print("")

    print("========================================")


if __name__ == "__main__":
    main()
