#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Reverse dependency lookup tool.

Answers: "If I change repo X, what else breaks?"

Usage:
    python reverse-dependency-lookup.py --repo unified-market-interface
    python reverse-dependency-lookup.py --repo unified-trading-library --transitive
    python reverse-dependency-lookup.py --tag cefi
    python reverse-dependency-lookup.py --repo unified-events-interface --transitive --tag critical
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path
from typing import NamedTuple

SCRIPT_DIR = Path(__file__).parent
PM_ROOT = SCRIPT_DIR.parent.parent
MANIFEST = PM_ROOT / "workspace-manifest.json"


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


class RepoInfo(NamedTuple):
    """Lightweight repo descriptor."""

    name: str
    repo_type: str
    tier: int | None
    completion_path: str
    tags: list[str]


class Dependent(NamedTuple):
    """A repo that depends on the target, with relationship metadata."""

    name: str
    dep_type: str  # "direct" or "transitive"
    distance: int  # BFS distance (1 = direct)
    tier: int | None
    repo_type: str
    completion_path: str
    tags: list[str]


# ---------------------------------------------------------------------------
# Manifest parsing
# ---------------------------------------------------------------------------


def load_manifest(path: Path | None = None) -> dict[str, RepoInfo]:
    """Load repos from workspace-manifest.json into RepoInfo map."""
    src = path or MANIFEST
    with open(src) as f:
        data = json.load(f)

    repos_raw: dict[str, object] = data.get("repositories", {})  # noqa: qg-empty-fallback
    result: dict[str, RepoInfo] = {}

    for name, info_raw in repos_raw.items():
        if not isinstance(info_raw, dict):
            continue
        info: dict[str, object] = info_raw
        result[name] = RepoInfo(
            name=name,
            repo_type=str(info.get("type", "unknown")),
            tier=info.get("tier") if isinstance(info.get("tier"), int) else None,
            completion_path=str(info.get("completion_path", "")),
            tags=list(info.get("tags", [])) if isinstance(info.get("tags"), list) else [],  # noqa: qg-empty-fallback
        )

    return result


def build_forward_graph(path: Path | None = None) -> dict[str, list[str]]:
    """Build forward adjacency: repo -> list of repos it depends on."""
    src = path or MANIFEST
    with open(src) as f:
        data = json.load(f)

    repos_raw: dict[str, object] = data.get("repositories", {})  # noqa: qg-empty-fallback
    forward: dict[str, list[str]] = {}

    for name, info_raw in repos_raw.items():
        if not isinstance(info_raw, dict):
            continue
        deps_raw = info_raw.get("dependencies", [])  # noqa: qg-empty-fallback
        dep_names: list[str] = []
        if isinstance(deps_raw, list):
            for dep in deps_raw:
                if isinstance(dep, dict):
                    dep_name = dep.get("name", "")
                    if isinstance(dep_name, str) and dep_name:
                        dep_names.append(dep_name)
                elif isinstance(dep, str) and dep:
                    dep_names.append(dep)
        # Deduplicate (some repos have duplicate deps in the manifest)
        forward[name] = list(dict.fromkeys(dep_names))

    return forward


def build_reverse_graph(forward: dict[str, list[str]]) -> dict[str, list[str]]:
    """Invert: for each dep, who depends on it."""
    reverse: dict[str, list[str]] = {}
    for repo, deps in forward.items():
        for dep in deps:
            reverse.setdefault(dep, []).append(repo)
    # Sort for deterministic output
    for dep in reverse:
        reverse[dep].sort()
    return reverse


# ---------------------------------------------------------------------------
# Lookup logic
# ---------------------------------------------------------------------------


def direct_dependents(
    target: str,
    reverse: dict[str, list[str]],
    repo_map: dict[str, RepoInfo],
) -> list[Dependent]:
    """Return direct dependents of target repo."""
    deps = reverse.get(target, [])
    result: list[Dependent] = []
    for dep_name in deps:
        info = repo_map.get(dep_name)
        if info is None:
            continue
        result.append(
            Dependent(
                name=dep_name,
                dep_type="direct",
                distance=1,
                tier=info.tier,
                repo_type=info.repo_type,
                completion_path=info.completion_path,
                tags=info.tags,
            )
        )
    return result


def transitive_dependents(
    target: str,
    reverse: dict[str, list[str]],
    repo_map: dict[str, RepoInfo],
) -> list[Dependent]:
    """BFS to find all transitive dependents."""
    visited: dict[str, int] = {}  # name -> distance
    queue: deque[tuple[str, int]] = deque()

    # Seed with direct dependents
    for dep_name in reverse.get(target, []):
        if dep_name not in visited:
            visited[dep_name] = 1
            queue.append((dep_name, 1))

    while queue:
        current, dist = queue.popleft()
        for next_dep in reverse.get(current, []):
            if next_dep not in visited and next_dep != target:
                visited[next_dep] = dist + 1
                queue.append((next_dep, dist + 1))

    result: list[Dependent] = []
    for dep_name, dist in sorted(visited.items(), key=lambda x: (x[1], x[0])):
        info = repo_map.get(dep_name)
        if info is None:
            continue
        result.append(
            Dependent(
                name=dep_name,
                dep_type="direct" if dist == 1 else "transitive",
                distance=dist,
                tier=info.tier,
                repo_type=info.repo_type,
                completion_path=info.completion_path,
                tags=info.tags,
            )
        )
    return result


def filter_by_tag(dependents: list[Dependent], tag: str) -> list[Dependent]:
    """Filter dependents to those having a specific tag."""
    return [d for d in dependents if tag in d.tags]


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

# Column widths
COL_NAME = 42
COL_TYPE = 12
COL_DEP = 12
COL_DIST = 6
COL_TIER = 6
COL_PATH = 16
COL_TAGS = 40


def format_table(dependents: list[Dependent], show_distance: bool = False) -> str:
    """Format dependents as an aligned table."""
    if not dependents:
        return "  (no dependents found)\n"

    lines: list[str] = []

    # Header
    header = f"  {'Repo':<{COL_NAME}}{'Type':<{COL_TYPE}}{'Relation':<{COL_DEP}}"
    if show_distance:
        header += f"{'Dist':<{COL_DIST}}"
    header += f"{'Tier':<{COL_TIER}}{'Path':<{COL_PATH}}{'Tags':<{COL_TAGS}}"
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))

    for dep in dependents:
        tier_str = f"T{dep.tier}" if dep.tier is not None else "---"
        tags_str = ", ".join(dep.tags) if dep.tags else "(none)"
        row = f"  {dep.name:<{COL_NAME}}{dep.repo_type:<{COL_TYPE}}{dep.dep_type:<{COL_DEP}}"
        if show_distance:
            row += f"{dep.distance:<{COL_DIST}}"
        row += f"{tier_str:<{COL_TIER}}{dep.completion_path:<{COL_PATH}}{tags_str}"
        lines.append(row)

    return "\n".join(lines) + "\n"


def format_summary(target: str, dependents: list[Dependent], transitive: bool) -> str:
    """Format a summary header."""
    direct_count = sum(1 for d in dependents if d.dep_type == "direct")
    trans_count = sum(1 for d in dependents if d.dep_type == "transitive")

    parts = [f"\nReverse dependencies for: {target}"]
    if transitive:
        parts.append(f"  Direct: {direct_count}  |  Transitive: {trans_count}  |  Total impact: {len(dependents)}")
    else:
        parts.append(f"  Direct dependents: {direct_count}")
    parts.append("")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Tag-based listing
# ---------------------------------------------------------------------------


def list_repos_by_tag(
    tag: str,
    repo_map: dict[str, RepoInfo],
    reverse: dict[str, list[str]],
) -> str:
    """List all repos with a given tag, sorted by tier."""
    matching = [info for info in repo_map.values() if tag in info.tags]
    if not matching:
        return f"\nNo repos found with tag: {tag}\n"

    matching.sort(key=lambda r: (r.tier if r.tier is not None else 999, r.name))

    lines: list[str] = []
    lines.append(f"\nRepos with tag '{tag}': {len(matching)}")
    lines.append("")

    header = (
        f"  {'Repo':<{COL_NAME}}"
        f"{'Type':<{COL_TYPE}}"
        f"{'Tier':<{COL_TIER}}"
        f"{'Path':<{COL_PATH}}"
        f"{'Dependents':<12}"
        f"{'All Tags':<{COL_TAGS}}"
    )
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))

    for info in matching:
        tier_str = f"T{info.tier}" if info.tier is not None else "---"
        dep_count = len(reverse.get(info.name, []))
        tags_str = ", ".join(info.tags)
        lines.append(
            f"  {info.name:<{COL_NAME}}"
            f"{info.repo_type:<{COL_TYPE}}"
            f"{tier_str:<{COL_TIER}}"
            f"{info.completion_path:<{COL_PATH}}"
            f"{dep_count:<12}"
            f"{tags_str}"
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Reverse dependency lookup for the Unified Trading System workspace.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s --repo unified-trading-library\n"
            "  %(prog)s --repo unified-trading-library --transitive\n"
            "  %(prog)s --tag cefi\n"
            "  %(prog)s --repo unified-events-interface --transitive --tag critical\n"
        ),
    )
    parser.add_argument(
        "--repo",
        help="Target repo to look up reverse dependencies for",
    )
    parser.add_argument(
        "--transitive",
        action="store_true",
        help="Include transitive dependents (BFS)",
    )
    parser.add_argument(
        "--tag",
        help="Filter by tag. If --repo is omitted, lists all repos with this tag.",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help=f"Path to workspace-manifest.json (default: {MANIFEST})",
    )

    args = parser.parse_args()

    if not args.repo and not args.tag:
        parser.error("At least one of --repo or --tag is required")

    manifest_path = args.manifest
    repo_map = load_manifest(manifest_path)
    forward = build_forward_graph(manifest_path)
    reverse = build_reverse_graph(forward)

    # Tag-only mode: list repos by tag
    if args.tag and not args.repo:
        print(list_repos_by_tag(args.tag, repo_map, reverse))
        return

    # Repo mode: find dependents
    target: str = args.repo
    if target not in repo_map:
        print(f"Error: repo '{target}' not found in manifest.", file=sys.stderr)
        print(f"Available repos: {', '.join(sorted(repo_map.keys()))}", file=sys.stderr)
        sys.exit(1)

    if args.transitive:
        dependents = transitive_dependents(target, reverse, repo_map)
    else:
        dependents = direct_dependents(target, reverse, repo_map)

    # Apply tag filter if specified
    if args.tag:
        dependents = filter_by_tag(dependents, args.tag)

    print(format_summary(target, dependents, args.transitive))
    print(format_table(dependents, show_distance=args.transitive))

    # Target repo info
    target_info = repo_map[target]
    if target_info.tags:
        print(f"  Target tags: {', '.join(target_info.tags)}")
    else:
        print("  Target tags: (none — run auto-populate-tags.py to add tags)")


if __name__ == "__main__":
    main()
