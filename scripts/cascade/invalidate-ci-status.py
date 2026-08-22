#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Transitive ci_status invalidation after a breaking dependency update.

When repo X fails QG after a breaking change, all repos that transitively
depend on X should be set to STAGING_PENDING to prevent stale
FEATURE_GREEN/LOCAL_PASS on repos that haven't been tested against the
breaking change.

Usage:
    python3 scripts/cascade/invalidate-ci-status.py <failed_repo> [--dry-run] [--reason "..."]

Examples:
    python3 scripts/cascade/invalidate-ci-status.py unified-market-interface
    python3 scripts/cascade/invalidate-ci-status.py unified-market-interface --dry-run
    python3 scripts/cascade/invalidate-ci-status.py unified-market-interface \\
        --reason "unified-market-interface 0.3.0 breaking change"
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import sys
from collections import deque
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
PM_ROOT = SCRIPT_DIR.parent.parent
MANIFEST = PM_ROOT / "workspace-manifest.json"
LOCK_FILE = PM_ROOT / ".workspace-manifest.lock"

# Statuses that should NOT be overwritten (already indicate a problem or pending state)
SKIP_STATUSES = frozenset({"FAILING", "STAGING_PENDING"})

# Lock timeout in seconds (5 minutes — matches existing convention)
LOCK_TIMEOUT_SECONDS = 300


# ---------------------------------------------------------------------------
# Locking
# ---------------------------------------------------------------------------


def _lock_timeout_handler(signum: int, frame: object) -> None:
    raise TimeoutError(f"manifest lock held >{LOCK_TIMEOUT_SECONDS}s — stale lock?")


# ---------------------------------------------------------------------------
# Dependency graph construction
# ---------------------------------------------------------------------------


def build_forward_dependents_graph(
    repositories: dict[str, dict[str, object]],
) -> dict[str, list[str]]:
    """Build forward dependency graph: for each repo R, collect all repos
    that list R in their dependencies (i.e., R's dependents).

    Returns a mapping from repo name to the sorted list of repos that
    directly depend on it.
    """
    reverse: dict[str, list[str]] = {}

    for repo_name, repo_info in repositories.items():
        if not isinstance(repo_info, dict):
            continue
        deps_raw = repo_info.get("dependencies", [])  # noqa: qg-empty-fallback
        if not isinstance(deps_raw, list):
            continue
        for dep in deps_raw:
            if isinstance(dep, dict):
                dep_name = dep.get("name", "")
            elif isinstance(dep, str):
                dep_name = dep
            else:
                continue
            if not dep_name:
                continue
            reverse.setdefault(dep_name, []).append(repo_name)

    # Sort for deterministic output
    for dep_name in reverse:
        reverse[dep_name].sort()

    return reverse


def find_transitive_dependents(
    failed_repo: str,
    reverse_graph: dict[str, list[str]],
) -> list[str]:
    """BFS from failed_repo through the reverse graph to find all
    transitive dependents. Returns a sorted list of repo names
    (excludes the failed_repo itself).
    """
    visited: set[str] = set()
    queue: deque[str] = deque()

    # Seed with direct dependents
    for dep in reverse_graph.get(failed_repo, []):
        if dep != failed_repo and dep not in visited:
            visited.add(dep)
            queue.append(dep)

    # BFS
    while queue:
        current = queue.popleft()
        for next_dep in reverse_graph.get(current, []):
            if next_dep not in visited and next_dep != failed_repo:
                visited.add(next_dep)
                queue.append(next_dep)

    return sorted(visited)


# ---------------------------------------------------------------------------
# Manifest read/write with locking
# ---------------------------------------------------------------------------


def read_manifest_locked(
    lock_fd: int,
) -> dict[str, object]:
    """Read manifest JSON while holding the lock."""
    with open(MANIFEST) as f:
        data: dict[str, object] = json.load(f)
    return data


def write_manifest_atomic(data: dict[str, object]) -> None:
    """Write manifest using tmp+rename for atomicity."""
    tmp_path = str(MANIFEST) + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp_path, str(MANIFEST))


# ---------------------------------------------------------------------------
# Core invalidation logic
# ---------------------------------------------------------------------------


def invalidate(
    failed_repo: str,
    reason: str,
    dry_run: bool,
) -> int:
    """Perform the transitive ci_status invalidation.

    Returns 0 on success, 1 on error.
    """
    # Set up lock timeout (signal.alarm only works on main thread, which
    # is the case for CLI scripts)
    signal.signal(signal.SIGALRM, _lock_timeout_handler)
    signal.alarm(LOCK_TIMEOUT_SECONDS)

    try:
        with open(LOCK_FILE, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            signal.alarm(0)  # Cancel alarm once lock acquired

            data = read_manifest_locked(lf.fileno())
            repositories = data.get("repositories", {})  # noqa: qg-empty-fallback
            if not isinstance(repositories, dict):
                print(
                    f"Error: 'repositories' key missing or invalid in {MANIFEST}",
                    file=sys.stderr,
                )
                return 1

            # Validate that the failed repo exists in the manifest
            if failed_repo not in repositories:
                print(
                    f"Error: repo '{failed_repo}' not found in manifest.",
                    file=sys.stderr,
                )
                available = sorted(repositories.keys())
                print(
                    f"Available repos: {', '.join(available)}",
                    file=sys.stderr,
                )
                return 1

            # Build the forward dependents graph
            reverse_graph = build_forward_dependents_graph(repositories)

            # Find all transitive dependents
            dependents = find_transitive_dependents(failed_repo, reverse_graph)

            if not dependents:
                print(f"No downstream dependents of {failed_repo} — nothing to invalidate.")
                return 0

            # Determine which repos actually need updating
            invalidated: list[str] = []
            skipped: list[str] = []

            for repo_name in dependents:
                repo_info = repositories.get(repo_name)
                if not isinstance(repo_info, dict):
                    continue
                current_status = repo_info.get("ci_status", "NOT_CONFIGURED")
                if current_status in SKIP_STATUSES:
                    skipped.append(f"  {repo_name}: already {current_status} — skipped")
                    continue
                invalidated.append(repo_name)

            if dry_run:
                print(f"[DRY RUN] Would invalidate {len(invalidated)} repos downstream of {failed_repo}:")
                for repo_name in invalidated:
                    repo_info = repositories[repo_name]
                    if not isinstance(repo_info, dict):
                        continue
                    current_status = repo_info.get("ci_status", "NOT_CONFIGURED")
                    print(f"  {repo_name}: {current_status} -> STAGING_PENDING")
                if skipped:
                    print(f"\nSkipped {len(skipped)} repos (already FAILING/STAGING_PENDING):")
                    for line in skipped:
                        print(line)
                print(f"\nReason: {reason}")
                return 0

            # Apply the invalidation
            for repo_name in invalidated:
                repo_info = repositories[repo_name]
                if not isinstance(repo_info, dict):
                    continue
                old_status = repo_info.get("ci_status", "NOT_CONFIGURED")
                repo_info["ci_status"] = "STAGING_PENDING"
                repo_info["breaking_cascade_source"] = reason
                print(f"  {repo_name}: {old_status} -> STAGING_PENDING")

            # Write the updated manifest atomically
            write_manifest_atomic(data)

            # Print summary
            print(f"\nInvalidated {len(invalidated)} repos downstream of {failed_repo}: [{', '.join(invalidated)}]")
            if skipped:
                print(f"Skipped {len(skipped)} repos (already FAILING/STAGING_PENDING):")
                for line in skipped:
                    print(line)
            print(f"Reason: {reason}")

    except TimeoutError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description=(
            "Transitive ci_status invalidation. Sets all transitive "
            "dependents of a failed repo to STAGING_PENDING in the "
            "workspace manifest."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s unified-market-interface\n"
            "  %(prog)s unified-market-interface --dry-run\n"
            '  %(prog)s unified-market-interface --reason "UMI 0.3.0 breaking change"\n'
        ),
    )
    parser.add_argument(
        "failed_repo",
        help="The repo that failed QG after a breaking dependency update",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be invalidated without writing the manifest",
    )
    parser.add_argument(
        "--reason",
        default=None,
        help=(
            "Reason string stored in manifest breaking_cascade_source field "
            '(e.g., "unified-market-interface 0.3.0 breaking change")'
        ),
    )

    args = parser.parse_args()

    # Default reason if not provided
    reason = args.reason or f"{args.failed_repo} breaking change"

    exit_code = invalidate(
        failed_repo=args.failed_repo,
        reason=reason,
        dry_run=args.dry_run,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
