#!/usr/bin/env python3
"""
Daily Diff Checker: Compare codex documentation against actual codebase.

Identifies gaps where documentation describes standards/functionality but code
doesn't match, and creates GitHub issues for remediation.

Usage:
  python check-codex-violations.py [--dry-run] [--repo OWNER/REPO] [--output-json PATH] [--max-workers N]

Requires: gh CLI (https://cli.github.com/) authenticated, or GITHUB_TOKEN.
          Python 3.13+
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from lib.codex_violations import (
    DriftGap,
    check_for_existing_issue,
    create_github_issue,
    ensure_labels_exist,
    fetch_all_existing_issues,
    find_architecture_gaps,
    find_coding_standards_violations,
    find_domain_event_gaps,
    find_event_logging_gaps,
    gap_to_dict,
)

JsonDict = dict[str, object]


def _parse_args() -> tuple[bool, str, int, Path | None, Path, Path]:
    """Parse CLI args. Returns (dry_run, repo, max_workers, output_json, codex_root, workspace_root)."""
    parser = argparse.ArgumentParser(description="Daily diff checker: codex vs codebase")
    parser.add_argument("--dry-run", action="store_true", help="Preview without creating issues")
    default_repo = os.getenv("GITHUB_REPO", "IggyIkenna/unified-trading-deployment-v2")
    parser.add_argument("--repo", default=default_repo, help="Target GitHub repo (OWNER/REPO)")
    parser.add_argument("--output-json", type=Path, help="Write results to JSON file")
    parser.add_argument("--codex-dir", type=Path, help="Path to unified-trading-codex")
    parser.add_argument("--workspace-dir", type=Path, help="Path to workspace root")
    parser.add_argument("--max-workers", type=int, default=10, help="Max parallel workers (default: 10)")
    parsed = parser.parse_args()

    dry_run: bool = bool(getattr(parsed, "dry_run", False))
    repo: str = str(getattr(parsed, "repo", "IggyIkenna/unified-trading-deployment-v2"))
    max_workers: int = int(getattr(parsed, "max_workers", 10))
    raw_output_json: object = getattr(parsed, "output_json", None)
    output_json: Path | None = cast(Path, raw_output_json) if isinstance(raw_output_json, Path) else None
    raw_codex_dir: object = getattr(parsed, "codex_dir", None)
    raw_workspace_dir: object = getattr(parsed, "workspace_dir", None)

    script_dir: Path = Path(__file__).parent
    codex_root: Path = cast(Path, raw_codex_dir) if isinstance(raw_codex_dir, Path) else script_dir.parent.parent
    workspace_root: Path = cast(Path, raw_workspace_dir) if isinstance(raw_workspace_dir, Path) else codex_root.parent
    return dry_run, repo, max_workers, output_json, codex_root, workspace_root


def _collect_all_gaps(codex_root: Path, workspace_root: Path) -> list[DriftGap]:
    """Run all diff checks and return combined gap list."""
    all_gaps: list[DriftGap] = []
    print("  - Checking coding standards...")
    all_gaps.extend(find_coding_standards_violations(codex_root, workspace_root))
    print("  - Checking event logging...")
    all_gaps.extend(find_event_logging_gaps(codex_root, workspace_root))
    print("  - Checking domain-specific events...")
    all_gaps.extend(find_domain_event_gaps(codex_root, workspace_root))
    print("  - Checking architecture...")
    all_gaps.extend(find_architecture_gaps(codex_root, workspace_root))
    return all_gaps


def _classify_gaps(
    all_gaps: list[DriftGap], existing_issues: dict[str, str], dry_run: bool
) -> tuple[list[DriftGap], list[JsonDict], int]:
    """Classify gaps into to-create vs skipped. Returns (gaps_to_create, results, skipped_count)."""
    gaps_to_create: list[DriftGap] = []
    results: list[JsonDict] = []
    skipped_count: int = 0
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
    return gaps_to_create, results, skipped_count


def _create_issues_parallel(gaps_to_create: list[DriftGap], repo: str, max_workers: int) -> tuple[list[JsonDict], int]:
    """Create issues in parallel. Returns (results, created_count)."""
    results: list[JsonDict] = []
    created_count: int = 0
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
    return results, created_count


def _write_output_json(
    output_json: Path,
    all_gaps: list[DriftGap],
    by_priority: dict[str, list[DriftGap]],
    codex_root: Path,
    workspace_root: Path,
    repo: str,
    dry_run: bool,
    created_count: int,
    skipped_count: int,
    results: list[JsonDict],
) -> None:
    """Write results to output JSON file."""
    serializable_gaps: list[JsonDict] = [gap_to_dict(g) for g in all_gaps]
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


def main() -> int:
    dry_run, repo, max_workers, output_json, codex_root, workspace_root = _parse_args()

    if not (codex_root / "06-coding-standards").exists():
        print(f"Error: Could not find codex at {codex_root}", file=sys.stderr)
        return 1

    print(f"Codex root: {codex_root}\nWorkspace root: {workspace_root}\nTarget repo: {repo}\nDry run: {dry_run}\n")

    print("Ensuring labels exist...")
    ensure_labels_exist(repo, workspace_root, dry_run)
    print()

    print("Running diff checks...")
    all_gaps: list[DriftGap] = _collect_all_gaps(codex_root, workspace_root)
    print(f"\nFound {len(all_gaps)} gaps")

    by_priority: dict[str, list[DriftGap]] = {}
    for gap in all_gaps:
        by_priority.setdefault(gap.priority, []).append(gap)
    for priority in ["P0-critical", "P1-high", "P2-medium", "P3-low"]:
        print(f"  {priority}: {len(by_priority.get(priority, []))}")

    print("\nFetching existing issues...")
    existing_issues: dict[str, str] = fetch_all_existing_issues(repo)

    print("\nChecking which gaps need new issues...")
    gaps_to_create, classify_results, skipped_count = _classify_gaps(all_gaps, existing_issues, dry_run)
    results: list[JsonDict] = classify_results
    created_count: int = 0

    if not dry_run and gaps_to_create:
        new_results, created_count = _create_issues_parallel(gaps_to_create, repo, max_workers)
        results.extend(new_results)
    elif dry_run and gaps_to_create:
        created_count = len(gaps_to_create)
        for gap in gaps_to_create:
            title = f"[{gap.service}] {gap.gap_id}: {gap.title}"
            results.append({"action": "create", "gap_id": gap.gap_id, "title": title})

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
            codex_root,
            workspace_root,
            repo,
            dry_run,
            created_count,
            skipped_count,
            results,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
