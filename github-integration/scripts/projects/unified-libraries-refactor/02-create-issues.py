#!/usr/bin/env python3
"""
Create GitHub Issues from Epic Breakdown

Parses epic-unified-libraries-refactor.md and creates 51 GitHub issues
across 5 repositories (4 new library repos + unified-trading-services).

Usage:
    # Dry run (preview):
    python 02-create-issues.py --org IggyIkenna \
        --epic-file "../../epic-breakdowns/epic-unified-libraries-refactor.md" \
        --dry-run

    # Apply changes:
    python 02-create-issues.py --org IggyIkenna \
        --epic-file "../../epic-breakdowns/epic-unified-libraries-refactor.md" \
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
            "title": f"[UnifiedLibraries] {title}",
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
    # Check for repo names in files field
    if "unified-events-interface" in files:
        return "unified-events-interface"
    elif "unified-config-interface" in files:
        return "unified-config-interface"
    elif "unified-market-interface" in files:
        return "unified-market-interface"
    elif "unified-order-interface" in files:
        return "unified-order-interface"
    elif "unified-trading-services" in files:
        return "unified-trading-services"

    # Fallback: infer from subtask ID or title
    _ = title  # May be used for other epic variants
    if "0." in subtask_id:  # Phase 0 (infrastructure)
        return "unified-trading-services"
    elif "1." in subtask_id:  # Phase 1 (events)
        return "unified-events-interface"
    elif "2." in subtask_id:  # Phase 2 (config)
        return "unified-config-interface"
    elif "3." in subtask_id:  # Phase 3 (market)
        return "unified-market-interface"
    elif "4." in subtask_id:  # Phase 4 (order)
        return "unified-order-interface"

    # Default to unified-trading-services
    return "unified-trading-services"


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

**Epic:** Unified Libraries Refactor
**Subtask ID:** {subtask.get("id", "")}
**Label:** `UNIFIED-LIBRARIES-REFACTOR`
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


def _build_issue_specs(subtasks: list[JsonDict]) -> list[JsonDict]:
    """Build list of issue specs from subtasks."""
    specs: list[JsonDict] = []
    for subtask in subtasks:
        specs.append(
            {
                "subtask": subtask,
                "repo": str(subtask.get("repo", "")),
                "title": str(subtask.get("title", "")),
                "body": create_issue_body(subtask),
                "priority_label": get_priority_label(str(subtask.get("priority", ""))),
            }
        )
    return specs


def _find_existing_issue(org: str, repo: str, title: str) -> str | None:
    """Check if issue with title exists; return number or None."""
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
        return str(first_item.get("number", ""))
    return None


def _create_single_issue_on_github(
    org: str,
    repo: str,
    title: str,
    body: str,
    priority_label: str,
    epic_label: str,
) -> tuple[str, str]:
    """Create issue via gh CLI; returns (number, url). Raises on failure."""
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
            f"{epic_label},{priority_label}",
            "--assignee",
            "@me",
        ]
    )
    if result:
        issue_url: str = str(result) if isinstance(result, str) else str(cast(JsonDict, result).get("url", ""))
        issue_number: str = issue_url.split("/")[-1] if issue_url else "unknown"
        return (issue_number, issue_url)
    raise ValueError("gh issue create returned no result")


def _process_single_issue(
    org: str,
    spec: JsonDict,
    dry_run: bool,
    epic_label: str,
) -> JsonDict:
    """Process one issue spec: dry run, existing, or create. Returns manifest entry."""
    subtask: JsonDict = cast(JsonDict, spec["subtask"])
    repo: str = str(spec["repo"])
    title: str = str(spec["title"])
    body: str = str(spec["body"])
    priority_label: str = str(spec["priority_label"])
    subtask_id: str = str(subtask.get("id", ""))

    print(f"\n  {subtask_id}: {title}")
    print(f"    Repo: {repo}")
    print(f"    Priority: {priority_label}")

    if dry_run:
        print(f"    [DRY RUN] Would create issue in {org}/{repo}")
        return {
            "subtask_id": subtask_id,
            "title": title,
            "number": None,
            "url": None,
            "dry_run": True,
        }

    existing_num = _find_existing_issue(org, repo, title)
    if existing_num:
        print(f"    Issue already exists: #{existing_num}")
        return {
            "subtask_id": subtask_id,
            "title": title,
            "number": existing_num,
            "url": f"https://github.com/{org}/{repo}/issues/{existing_num}",
            "existing": True,
        }

    try:
        num, url = _create_single_issue_on_github(org, repo, title, body, priority_label, epic_label)
        print(f"    Created issue: #{num}")
        print(f"       {url}")
        return {
            "subtask_id": subtask_id,
            "title": title,
            "number": num,
            "url": url,
            "existing": False,
        }
    except (OSError, ValueError) as e:
        print(f"    Failed to create issue: {e}")
        return {
            "subtask_id": subtask_id,
            "title": title,
            "number": None,
            "url": None,
            "error": str(e),
        }


def create_issues(
    org: str,
    subtasks: list[JsonDict],
    dry_run: bool = True,
    epic_label: str = "UNIFIED-LIBRARIES-REFACTOR",
) -> dict[str, list[JsonDict]]:
    """Create GitHub issues for all subtasks."""
    print(f"\n  {'[DRY RUN] ' if dry_run else ''}Creating issues...")
    issue_manifest: dict[str, list[JsonDict]] = {}
    specs: list[JsonDict] = _build_issue_specs(subtasks)

    for spec in specs:
        repo: str = str(spec["repo"])
        entry: JsonDict = _process_single_issue(org, spec, dry_run, epic_label)
        issue_manifest.setdefault(repo, []).append(entry)

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
    issue_manifest: dict[str, list[JsonDict]] = create_issues(
        org, subtasks, dry_run=dry_run, epic_label="UNIFIED-LIBRARIES-REFACTOR"
    )

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
