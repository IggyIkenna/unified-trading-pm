#!/usr/bin/env python3
"""
Check File Size CODs (Code-Owned Debt)

This script scans repositories for files exceeding 1500 lines (SRP violation)
and creates GitHub issues labeled with `cod` and `COD-SIZE`.

Features:
  - Parallel repo scanning (ThreadPoolExecutor)
  - Only checks git-tracked files (respects .gitignore)
  - Batched issue creation
  - Idempotent (updates existing issues, no duplicates)
  - Auto-assigns to COD project (#3)
  - Provides split suggestions
  - Supports dry-run mode

Usage:
    # Check all repos
    python3 05-check-file-size-cods.py --all-repos --dry-run

    # Check single repo
    python3 05-check-file-size-cods.py --repo instruments-service

    # With custom threshold
    python3 05-check-file-size-cods.py --all-repos --threshold 1200

    # Limit number of issues created (for testing)
    python3 05-check-file-size-cods.py --repo unified-trading-codex --max-issues 5
"""

import argparse
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import cast

# ==============================================================================
# Constants
# ==============================================================================

DEFAULT_THRESHOLD = 1500
DEFAULT_ORG = "IggyIkenna"
COD_PROJECT_NUMBER = 3

# Repos to scan (30 repos total)
ALL_REPOS = [
    # Pipeline services (17)
    "instruments-service",
    "corporate-actions",
    "features-calendar-service",
    "market-tick-data-handler",
    "market-data-processing-service",
    "features-delta-one-service",
    "features-volatility-service",
    "features-onchain-service",
    "features-sports-service",
    "ml-training-service",
    "ml-inference-service",
    "strategy-service",
    "execution-service",
    "reconciliation-service",
    "pnl-attribution-service",
    "position-balance-monitor-service",
    "risk-monitor-service",
    # Platform services (5)
    "unified-trading-services",
    "unified-trading-deployment-v2",
    "unified-trading-codex",
    "exchange-interface-library",
    "alerting-service",
    # UI services (8 - excluding 2 not yet created)
    "live-health-monitor-ui",
    "batch-audit-ui",
    "logs-dashboard-ui",
    "ml-training-ui",
    "execution-analytics-ui",
    "trading-analytics-ui",
    "settlement-ui",
    "client-reporting-ui",
]

# File extensions to check
EXTENSIONS = [".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml"]

# Paths to exclude
EXCLUDE_PATTERNS = [
    "node_modules/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".git/",
    "build/",
    "dist/",
    "htmlcov/",
    "docs/",
    "tests/",  # Exclude tests from COD-SIZE checks
]


# ==============================================================================
# Color Logging
# ==============================================================================


class Colors:
    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"


def log_info(msg: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")


def log_warning(msg: str):
    print(f"{Colors.YELLOW}[⚠]{Colors.NC} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")


# ==============================================================================
# File Scanning
# ==============================================================================


def count_lines(file_path: Path) -> int:
    """Count non-empty lines in a file."""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return sum(1 for line in f if line.strip())
    except (OSError, ValueError) as e:
        log_warning(f"Could not read {file_path}: {e}")
        return 0


def should_exclude(file_path: Path) -> bool:
    """Check if file should be excluded from scanning."""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)


def scan_repo_for_large_files(repo_name: str, threshold: int, org: str = DEFAULT_ORG) -> list[tuple[str, int]]:
    """
    Scan a single repo for files exceeding threshold.
    Only checks files tracked by git (respects .gitignore).

    Returns:
        List of (relative_file_path, line_count) tuples
    """
    # Clone or use existing repo
    repo_dir = Path(f"/tmp/cod-scan/{repo_name}")

    if not repo_dir.exists():
        log_info(f"Cloning {org}/{repo_name}...")
        # Use list args to avoid shell=True vulnerability
        clone_cmd: list[str] = [
            "git",
            "clone",
            "--depth",
            "1",
            f"https://github.com/{org}/{repo_name}.git",
            str(repo_dir),
        ]
        try:
            subprocess.run(clone_cmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            raw_stderr: object = getattr(e, "stderr", None)
            log_error(f"Failed to clone {repo_name}: {raw_stderr}")
            return []

    # Get list of tracked files from git (respects .gitignore)
    git_ls_cmd: list[str] = ["git", "ls-files"]
    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            git_ls_cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=repo_dir,
        )
        tracked_files: list[str] = result.stdout.strip().split("\n")
    except subprocess.CalledProcessError as e:
        raw_stderr2: object = getattr(e, "stderr", None)
        log_error(f"Failed to get tracked files from {repo_name}: {raw_stderr2}")
        return []

    # Scan tracked files for large files
    large_files: list[tuple[str, int]] = []

    for rel_path_str in tracked_files:
        file_path = repo_dir / rel_path_str

        # Check if file extension is in our list
        if not any(file_path.suffix == ext for ext in EXTENSIONS):
            continue

        # Additional exclusions (even if tracked by git)
        if should_exclude(file_path):
            continue

        # Check if file exists and count lines
        if file_path.exists() and file_path.is_file():
            line_count = count_lines(file_path)

            if line_count >= threshold:
                large_files.append((rel_path_str, line_count))

    return large_files


def scan_all_repos(repos: list[str], threshold: int, org: str = DEFAULT_ORG) -> dict[str, list[tuple[str, int]]]:
    """
    Scan multiple repos in parallel.

    Returns:
        Dict mapping repo_name -> list of (file_path, line_count)
    """
    results: dict[str, list[tuple[str, int]]] = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_repo = {executor.submit(scan_repo_for_large_files, repo, threshold, org): repo for repo in repos}

        for future in as_completed(future_to_repo):
            repo = future_to_repo[future]
            try:
                large_files = future.result()
                if large_files:
                    results[repo] = large_files
                    log_success(f"{repo}: Found {len(large_files)} files >={threshold} lines")
                else:
                    log_info(f"{repo}: No files >={threshold} lines")
            except (OSError, ValueError) as e:
                log_error(f"Error scanning {repo}: {e}")

    return results


# ==============================================================================
# GitHub Issue Management
# ==============================================================================


def generate_issue_title(repo: str, file_path: str, line_count: int) -> str:
    """Generate consistent issue title."""
    return f"[COD-SIZE] {repo}/{file_path} ({line_count} lines)"


def generate_issue_body(repo: str, file_path: str, line_count: int, threshold: int, org: str = DEFAULT_ORG) -> str:
    """Generate issue body with split suggestions."""
    overage = line_count - threshold
    overage_pct = (overage / threshold) * 100

    return f"""## File Size Violation

**Repository:** `{repo}`
**File:** `{file_path}`
**Line Count:** {line_count}
**Threshold:** {threshold}
**Overage:** {overage} lines ({overage_pct:.1f}% over)

## Single Responsibility Principle (SRP) Violation

Files exceeding {threshold} lines typically violate the Single Responsibility Principle.
This makes the code harder to:
- Understand
- Test
- Maintain
- Review

## Suggested Actions

1. **Identify Responsibilities:** What distinct tasks does this file handle?
2. **Split by Responsibility:** Create separate files/classes for each responsibility
3. **Extract Utilities:** Move helper functions to utility modules
4. **Separate Concerns:** Split business logic from data access, I/O, etc.

## Split Strategy Examples

### For Large Classes (>1500 lines)
- Extract data validation → `validators.py`
- Extract data transformations → `transformers.py`
- Extract I/O operations → `io_handlers.py`
- Extract business logic → `business_logic.py`

### For Large Modules (>1500 lines)
- Group related functions → separate modules
- Extract constants → `constants.py`
- Extract utilities → `utils.py`

## Success Criteria

- [ ] File split into smaller, focused modules
- [ ] Each new file <{threshold} lines
- [ ] All tests still pass
- [ ] Code coverage maintained or improved
- [ ] Documentation updated

## Codex References

- [Single Responsibility Principle](https://github.com/{org}/unified-trading-codex/blob/main/06-coding-standards/README.md#single-responsibility-principle)
- [Code Organization](https://github.com/{org}/unified-trading-codex/blob/main/06-coding-standards/README.md#code-organization)

---

**Auto-generated by:** `check-file-size-cods.py`
**Threshold:** {threshold} lines
"""


def get_existing_issues(org: str, repo: str) -> dict[str, int]:
    """
    Get existing COD-SIZE issues for a repo.

    Returns:
        Dict mapping issue_title -> issue_number
    """
    # Use list args to avoid shell=True vulnerability
    cmd: list[str] = [
        "gh",
        "issue",
        "list",
        "--repo",
        f"{org}/{repo}",
        "--label",
        "COD-SIZE",
        "--state",
        "all",
        "--limit",
        "1000",
        "--json",
        "number,title",
    ]

    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
        )
        issues: list[dict[str, object]] = cast(
            list[dict[str, object]],
            json.loads(result.stdout),
        )
        return {str(issue["title"]): int(str(issue["number"])) for issue in issues}
    except subprocess.CalledProcessError as e:
        raw_stderr: object = getattr(e, "stderr", None)
        log_error(f"Failed to fetch existing issues: {raw_stderr}")
        return {}
    except json.JSONDecodeError as e:
        log_error(f"Failed to parse issue JSON: {e}")
        return {}


def create_issue(org: str, repo: str, title: str, body: str, dry_run: bool = False) -> int | None:
    """
    Create a GitHub issue.

    Returns:
        Issue number if created, None otherwise
    """
    if dry_run:
        log_info(f"[DRY-RUN] Would create: {title}")
        return None

    # Create issue with labels - use list args to avoid shell=True vulnerability
    cmd: list[str] = [
        "gh",
        "issue",
        "create",
        "--repo",
        f"{org}/{repo}",
        "--title",
        title,
        "--label",
        "cod,COD-SIZE,P1-high",
        "--body",
        "-",
    ]

    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            input=body,
        )
        issue_url: str = result.stdout.strip()
        issue_number: int = int(issue_url.split("/")[-1])
        log_success(f"Created issue #{issue_number}: {title}")
        return issue_number
    except subprocess.CalledProcessError as e:
        raw_stderr: object = getattr(e, "stderr", None)
        log_error(f"Failed to create issue: {raw_stderr}")
        return None


def add_to_project(org: str, issue_number: int, repo: str, project_number: int, dry_run: bool = False) -> None:
    """Add issue to COD project."""
    if dry_run:
        log_info(f"[DRY-RUN] Would add #{issue_number} to project {project_number}")
        return

    # Use list args to avoid shell=True vulnerability
    cmd: list[str] = [
        "gh",
        "project",
        "item-add",
        str(project_number),
        "--owner",
        org,
        "--url",
        f"https://github.com/{org}/{repo}/issues/{issue_number}",
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        log_success(f"Added #{issue_number} to project {project_number}")
    except subprocess.CalledProcessError as e:
        raw_stderr: object = getattr(e, "stderr", None)
        log_warning(f"Failed to add to project: {raw_stderr}")


def update_issue(org: str, repo: str, issue_number: int, new_body: str, dry_run: bool = False) -> None:
    """Update existing issue body."""
    if dry_run:
        log_info(f"[DRY-RUN] Would update #{issue_number}")
        return

    # Use list args to avoid shell=True vulnerability
    cmd: list[str] = [
        "gh",
        "issue",
        "edit",
        str(issue_number),
        "--repo",
        f"{org}/{repo}",
        "--body",
        "-",
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, input=new_body)
        log_success(f"Updated issue #{issue_number}")
    except subprocess.CalledProcessError as e:
        raw_stderr: object = getattr(e, "stderr", None)
        log_error(f"Failed to update issue: {raw_stderr}")


# ==============================================================================
# Main Processing
# ==============================================================================


def process_repo(
    repo: str,
    large_files: list[tuple[str, int]],
    threshold: int,
    org: str,
    dry_run: bool,
    max_issues: int | None = None,
) -> None:
    """Process large files in a repo and create/update issues."""
    log_info(f"\nProcessing {org}/{repo}...")

    # Get existing issues
    existing_issues = get_existing_issues(org, repo)

    created = 0
    updated = 0
    skipped = 0

    for file_path, line_count in large_files:
        if max_issues and created >= max_issues:
            log_warning(f"Reached max issues limit ({max_issues})")
            break

        title = generate_issue_title(repo, file_path, line_count)
        body = generate_issue_body(repo, file_path, line_count, threshold)

        # Check if issue already exists
        if title in existing_issues:
            issue_number = existing_issues[title]
            log_info(f"Issue exists: #{issue_number}")

            # Update issue body (line count may have changed)
            update_issue(org, repo, issue_number, body, dry_run)
            updated += 1
        else:
            # Create new issue
            issue_number = create_issue(org, repo, title, body, dry_run)

            if issue_number:
                # Add to COD project
                add_to_project(org, issue_number, repo, COD_PROJECT_NUMBER, dry_run)
                created += 1

    log_info(f"{repo}: Created={created}, Updated={updated}, Skipped={skipped}")


# ==============================================================================
# Main CLI
# ==============================================================================


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check file sizes and create COD-SIZE issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--all-repos", action="store_true", help="Scan all 30 repos")
    parser.add_argument("--repo", type=str, help="Scan single repo (e.g., instruments-service)")
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Line count threshold (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--org",
        type=str,
        default=DEFAULT_ORG,
        help=f"GitHub organization (default: {DEFAULT_ORG})",
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview actions without creating issues")
    parser.add_argument("--max-issues", type=int, help="Max issues to create per repo (for testing)")

    parsed = parser.parse_args()

    all_repos_flag: bool = bool(getattr(parsed, "all_repos", False))
    repo_arg: str = str(getattr(parsed, "repo", "") or "")
    threshold: int = int(getattr(parsed, "threshold", DEFAULT_THRESHOLD))
    org: str = str(getattr(parsed, "org", DEFAULT_ORG))
    dry_run: bool = bool(getattr(parsed, "dry_run", False))
    max_issues_raw: object = getattr(parsed, "max_issues", None)
    max_issues: int | None = int(str(max_issues_raw)) if max_issues_raw is not None else None

    # Validate arguments
    if not (all_repos_flag or repo_arg):
        parser.error("Must specify --all-repos or --repo")

    # Determine repos to scan
    repos: list[str] = [repo_arg] if repo_arg else ALL_REPOS

    # Scan repos
    log_info(f"Scanning {len(repos)} repos for files >={threshold} lines...")
    if dry_run:
        log_warning("DRY-RUN MODE: No issues will be created")

    results = scan_all_repos(repos, threshold, org)

    if not results:
        log_success("No files exceed threshold!")
        return

    # Process results
    total_files = sum(len(files) for files in results.values())
    log_info(f"\nFound {total_files} files across {len(results)} repos")

    for repo_name, large_files in results.items():
        process_repo(repo_name, large_files, threshold, org, dry_run, max_issues)

    log_info("\n" + "=" * 70)
    log_success("COD-SIZE check complete!")
    log_info("=" * 70)


if __name__ == "__main__":
    main()
