#!/usr/bin/env python3
"""
Daily Diff Checker: Compare codex documentation against actual codebase.

Identifies gaps where documentation describes standards/functionality but code
doesn't match, and creates GitHub issues for remediation.

Usage:
  python run-diff-checker.py [--dry-run] [--repo OWNER/REPO] [--output-json PATH] [--max-workers N]

Performance:
  - Batch fetches existing issues (~5-10 API calls instead of 1,209)
  - Creates issues in parallel (10 workers by default)
  - Total time: ~1-2 minutes for 1,000+ issues (vs. ~20 minutes sequential)

Requires: gh CLI (https://cli.github.com/) authenticated, or GITHUB_TOKEN.
          Python 3.13+
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from lib.diff_checkers import (
    DriftGap,
    find_architecture_gaps,
    find_coding_standards_violations,
    find_domain_event_gaps,
    find_event_logging_gaps,
    find_validator_violations,
)

# Type alias
JsonDict = dict[str, object]


def fetch_all_existing_issues(repo: str) -> dict[str, str]:
    """
    Fetch ALL open issues from repo and build gap_id index.

    This is much faster than checking each gap individually:
    - Old way: ~1,209 API calls (one per gap)
    - New way: ~5-10 API calls (fetching 1000 issues at once)

    Returns dict mapping gap_id -> issue_number.
    """
    print("  Fetching all existing issues from GitHub...")
    gap_id_to_issue: dict[str, str] = {}

    try:
        # Fetch up to 1000 open issues (should cover most repos)
        result = subprocess.run(
            [
                "gh",
                "issue",
                "list",
                "--repo",
                repo,
                "--state",
                "open",
                "--limit",
                "1000",
                "--json",
                "number,body",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            print(
                f"  Warning: gh issue list failed with code {result.returncode}",
                file=sys.stderr,
            )
            return gap_id_to_issue

        if not result.stdout.strip():
            print("  No existing issues found")
            return gap_id_to_issue

        raw_issues: object = cast(object, json.loads(result.stdout))
        issues_list: list[JsonDict] = (
            [cast(JsonDict, item) for item in cast(list[object], raw_issues) if isinstance(item, dict)]
            if isinstance(raw_issues, list)
            else []
        )
        print(f"  Loaded {len(issues_list)} existing open issues")

        # Extract gap_id from each issue body
        for issue in issues_list:
            body_val: str = str(issue.get("body", ""))
            # Look for "gap-id: XXX" marker
            match = re.search(r"gap-id:\s*(\S+)", body_val)
            if match:
                gap_id_str: str = match.group(1)
                gap_id_to_issue[gap_id_str] = str(issue.get("number", ""))

        print(f"  Found {len(gap_id_to_issue)} issues with gap-id markers")

    except (OSError, ValueError) as e:
        print(f"  Warning: Could not fetch existing issues: {e}", file=sys.stderr)

    return gap_id_to_issue


def check_for_existing_issue(gap: DriftGap, existing_issues: dict[str, str]) -> str | None:
    """
    Check if issue already exists by looking up gap_id in pre-loaded index.

    Args:
        gap: The gap to check
        existing_issues: Dict mapping gap_id -> issue_number

    Returns issue number if found, None otherwise.
    """
    return existing_issues.get(gap.gap_id)


def _build_issue_body(gap: DriftGap) -> str:
    """Build issue body text for a drift gap."""
    return f"""## Gap Type: {gap.gap_type}

{gap.description}

## Details

- **Category**: {gap.category}
- **Service**: {gap.service}
- **Priority**: {gap.priority}
- **Auto-fixable**: {"Yes" if gap.auto_fixable else "No"}
- **Codex Reference**: {gap.codex_reference}

## Affected Files

{chr(10).join(f"- {f}" for f in gap.affected_files)}

## Standards Reference

See codex: `{gap.codex_reference}`

---

**Markers for Drift Checker:**
- gap-id: {gap.gap_id}
- gap-type: {gap.gap_type}
- category: {gap.category}
- auto-fixable: {gap.auto_fixable}
- detected: {datetime.now(timezone.utc).isoformat()}
"""


def _build_issue_labels(gap: DriftGap) -> list[str]:
    """Build label list for a drift gap."""
    labels = ["issue", gap.priority]
    category_label_map = {
        "coding_standards": "area/coding-standards",
        "observability": "area/observability",
        "architecture": "area/architecture",
        "data": "area/data",
        "domain": "area/domain",
    }
    if gap.category in category_label_map:
        labels.append(category_label_map[gap.category])
    labels.append(f"service/{gap.service}")
    if gap.auto_fixable:
        labels.append("auto-fixable")
    return labels


def create_github_issue(gap: DriftGap, repo: str, dry_run: bool) -> JsonDict:
    """
    Create GitHub issue for this gap.

    Returns dict with issue details.
    """
    title = f"[{gap.service}] {gap.gap_id}: {gap.title}"
    body = _build_issue_body(gap)
    labels = _build_issue_labels(gap)

    if dry_run:
        return {
            "action": "create",
            "title": title,
            "labels": labels,
            "gap_id": gap.gap_id,
            "service": gap.service,
        }

    try:
        # Create issue using gh CLI
        cmd = [
            "gh",
            "issue",
            "create",
            "--repo",
            repo,
            "--title",
            title,
            "--body",
            body,
        ]

        for label in labels:
            cmd.extend(["--label", label])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
        )

        issue_url = result.stdout.strip()
        issue_number = issue_url.split("/")[-1] if issue_url else "unknown"

        return {
            "action": "created",
            "issue_number": issue_number,
            "issue_url": issue_url,
            "gap_id": gap.gap_id,
            "service": gap.service,
        }

    except subprocess.CalledProcessError as e:
        raw_stderr: object = getattr(e, "stderr", None)
        print(f"Error creating issue: {raw_stderr}", file=sys.stderr)
        return {
            "action": "error",
            "error": str(raw_stderr) if raw_stderr is not None else "",
            "gap_id": gap.gap_id,
        }


def ensure_labels_exist(repo: str, workspace_root: Path, dry_run: bool) -> None:
    """Create all required labels for diff checker issues."""
    if dry_run:
        return

    # Get all service names from workspace
    service_dirs = [
        d.name
        for d in workspace_root.iterdir()
        if d.is_dir()
        and (d / "pyproject.toml").exists()
        and d.name not in {"unified-trading-services", "unified-trading-codex", "mr_report"}
    ]

    labels_to_create = [
        # Priority labels
        ("p0-critical", "DC2626", "Critical priority"),
        ("p1-high", "F97316", "High priority"),
        ("p2-medium", "FACC15", "Medium priority"),
        ("p3-low", "4ADE80", "Low priority"),
        # Category labels
        ("area/coding-standards", "8B5CF6", "Coding standards area"),
        ("area/observability", "3B82F6", "Observability area"),
        ("area/architecture", "06B6D4", "Architecture area"),
        ("area/data", "10B981", "Data area"),
        ("area/domain", "F59E0B", "Domain area"),
        # Misc
        ("auto-fixable", "22C55E", "Can be auto-fixed by agent"),
        ("issue", "6B7280", "Flat issue (not part of Epic hierarchy)"),
    ]

    # Add service labels dynamically
    for service in service_dirs:
        labels_to_create.append((f"service/{service}", "64748B", f"Service: {service}"))

    # Create labels
    created = 0
    for label_name, color, description in labels_to_create:
        cmd = [
            "gh",
            "label",
            "create",
            label_name,
            "--repo",
            repo,
            "--color",
            color,
            "--description",
            description,
            "--force",
        ]
        label_result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if label_result.returncode == 0:
            created += 1

    print(f"Ensured {len(labels_to_create)} labels exist ({created} created/updated)")


def _run_all_checks(codex_root: Path, workspace_root: Path) -> tuple[list[DriftGap], dict[str, list[DriftGap]]]:
    """Run all diff checks and return gaps plus by_priority."""
    print("Running diff checks...")
    all_gaps: list[DriftGap] = []
    print("  - Checking coding standards...")
    all_gaps.extend(find_coding_standards_violations(codex_root, workspace_root))
    print("  - Checking event logging...")
    all_gaps.extend(find_event_logging_gaps(codex_root, workspace_root))
    print("  - Checking domain-specific events...")
    all_gaps.extend(find_domain_event_gaps(codex_root, workspace_root))
    print("  - Checking architecture...")
    all_gaps.extend(find_architecture_gaps(codex_root, workspace_root))
    print("  - Running validators (manifest, checklist, plan links)...")
    all_gaps.extend(find_validator_violations(workspace_root))
    print(f"\nFound {len(all_gaps)} gaps")
    by_priority: dict[str, list[DriftGap]] = {}
    for gap in all_gaps:
        by_priority.setdefault(gap.priority, []).append(gap)
    for priority in ["P0-critical", "P1-high", "P2-medium", "P3-low"]:
        count: int = len(by_priority.get(priority, []))
        print(f"  {priority}: {count}")
    return all_gaps, by_priority


def _separate_gaps_and_create_issues(
    all_gaps: list[DriftGap],
    existing_issues: dict[str, str],
    repo: str,
    dry_run: bool,
    max_workers: int,
) -> tuple[list[JsonDict], int, int]:
    """Separate gaps into existing vs new, create issues, return results and counts."""
    gaps_to_create: list[DriftGap] = []
    results: list[JsonDict] = []
    created_count: int = 0
    skipped_count: int = 0
    print("\nChecking which gaps need new issues...")
    for gap in all_gaps:
        existing_issue: str | None = check_for_existing_issue(gap, existing_issues)
        if existing_issue:
            print(f"  SKIP {gap.gap_id}: Already exists (#{existing_issue})")
            skipped_count += 1
            results.append({"action": "skipped", "gap_id": gap.gap_id, "existing_issue": existing_issue})
        else:
            gaps_to_create.append(gap)
            if dry_run:
                if gap.gap_id.startswith("COD-SIZE-"):
                    print(f"  OK {gap.gap_id}: Would create issue (dry-run)")
                    print(f"      Title: {gap.title}")
                else:
                    print(f"  OK {gap.gap_id}: Would create issue (dry-run)")
    if not dry_run and gaps_to_create:
        print(f"\nCreating {len(gaps_to_create)} issues in parallel (max {max_workers} workers)...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_gap: dict[Future[JsonDict], DriftGap] = {
                executor.submit(create_github_issue, g, repo, False): g for g in gaps_to_create
            }
            for i, future in enumerate(as_completed(future_to_gap), 1):
                current_gap = future_to_gap[future]
                try:
                    issue_result: JsonDict = future.result()
                    results.append(issue_result)
                    action_val: str = str(issue_result.get("action", ""))
                    if action_val in {"create", "created"}:
                        created_count += 1
                        print(f"  OK [{i}/{len(gaps_to_create)}] {current_gap.gap_id}: Created")
                    else:
                        print(f"  WARN [{i}/{len(gaps_to_create)}] {current_gap.gap_id}: Failed")
                except (OSError, ValueError) as e:
                    print(f"  ERR [{i}/{len(gaps_to_create)}] {current_gap.gap_id}: Error - {e}")
                    results.append({"action": "error", "gap_id": current_gap.gap_id, "error": str(e)})
    elif dry_run and gaps_to_create:
        created_count = len(gaps_to_create)
        for gap in gaps_to_create:
            results.append(
                {"action": "create", "gap_id": gap.gap_id, "title": f"[{gap.service}] {gap.gap_id}: {gap.title}"}
            )
    return results, created_count, skipped_count


def _write_output_json(
    output_json: Path,
    all_gaps: list[DriftGap],
    by_priority: dict[str, list[DriftGap]],
    results: list[JsonDict],
    created_count: int,
    skipped_count: int,
    codex_root: Path,
    workspace_root: Path,
    repo: str,
    dry_run: bool,
) -> None:
    """Write results to JSON file."""
    serializable_gaps: list[JsonDict] = [_gap_to_dict(g) for g in all_gaps]
    output_data: JsonDict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "codex_root": str(codex_root),
        "workspace_root": str(workspace_root),
        "target_repo": repo,
        "dry_run": dry_run,
        "total_gaps": len(all_gaps),
        "gaps_by_priority": {k: len(v) for k, v in by_priority.items()},
        "created_count": created_count,
        "skipped_count": skipped_count,
        "results": results,
        "gaps": serializable_gaps,
    }
    output_json.write_text(json.dumps(output_data, indent=2))
    print(f"\nResults written to {output_json}")


def _gap_to_dict(gap: DriftGap) -> JsonDict:
    """Convert a DriftGap dataclass to a JSON-serializable dict."""
    gap_dict: JsonDict = {
        "gap_id": gap.gap_id,
        "title": gap.title,
        "category": gap.category,
        "priority": gap.priority,
        "gap_type": gap.gap_type,
        "description": gap.description,
        "service": gap.service,
        "affected_files": gap.affected_files,
        "codex_reference": gap.codex_reference,
        "auto_fixable": gap.auto_fixable,
    }
    return gap_dict


def main() -> int:

    parser = argparse.ArgumentParser(description="Daily diff checker: codex vs codebase")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating issues")
    parser.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPO", "IggyIkenna/unified-trading-deployment-v2"),
        help="Target GitHub repo (OWNER/REPO)",
    )
    parser.add_argument("--output-json", type=Path, help="Write results to JSON file")
    parser.add_argument("--codex-dir", type=Path, help="Path to unified-trading-codex")
    parser.add_argument("--workspace-dir", type=Path, help="Path to workspace root")
    parser.add_argument(
        "--max-workers",
        type=int,
        default=10,
        help="Max parallel workers for creating issues (default: 10)",
    )

    parsed = parser.parse_args()

    # Extract typed args
    dry_run: bool = bool(getattr(parsed, "dry_run", False))
    repo: str = str(getattr(parsed, "repo", "IggyIkenna/unified-trading-deployment-v2"))
    max_workers: int = int(getattr(parsed, "max_workers", 10))
    raw_output_json: object = getattr(parsed, "output_json", None)
    output_json: Path | None = cast(Path, raw_output_json) if isinstance(raw_output_json, Path) else None
    raw_codex_dir: object = getattr(parsed, "codex_dir", None)
    raw_workspace_dir: object = getattr(parsed, "workspace_dir", None)

    # Determine paths
    script_dir: Path = Path(__file__).parent
    codex_root: Path = cast(Path, raw_codex_dir) if isinstance(raw_codex_dir, Path) else script_dir.parent.parent
    workspace_root: Path = cast(Path, raw_workspace_dir) if isinstance(raw_workspace_dir, Path) else codex_root.parent

    if not (codex_root / "06-coding-standards").exists():
        print(f"Error: Could not find codex at {codex_root}", file=sys.stderr)
        return 1

    print(f"Codex root: {codex_root}")
    print(f"Workspace root: {workspace_root}")
    print(f"Target repo: {repo}")
    print(f"Dry run: {dry_run}")
    print()

    # Ensure all labels exist before creating issues
    print("Ensuring labels exist...")
    ensure_labels_exist(repo, workspace_root, dry_run)
    print()

    all_gaps, by_priority = _run_all_checks(codex_root, workspace_root)
    print("\nFetching existing issues...")
    existing_issues = fetch_all_existing_issues(repo)
    results, created_count, skipped_count = _separate_gaps_and_create_issues(
        all_gaps, existing_issues, repo, dry_run, max_workers
    )
    print("\nSummary:")
    print(f"  Total gaps found: {len(all_gaps)}")
    if dry_run:
        print(f"  Issues that would be created: {created_count} (dry-run, not actually created)")
    else:
        print(f"  Issues created: {created_count}")
    print(f"  Issues skipped (already exist): {skipped_count}")
    if output_json is not None:
        _write_output_json(
            output_json,
            all_gaps,
            by_priority,
            results,
            created_count,
            skipped_count,
            codex_root,
            workspace_root,
            repo,
            dry_run,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
