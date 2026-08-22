#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Reverse dependency lookup for workspace-manifest.json.

For a given repo, finds all repos that depend on it. Without --repo, prints
the full reverse dependency map for every repo.

Usage:
    python3 reverse-dependency-lookup.py                        # full map (text)
    python3 reverse-dependency-lookup.py --repo unified-trading-library
    python3 reverse-dependency-lookup.py --repo unified-trading-library --format json
    python3 reverse-dependency-lookup.py --format mermaid
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"


def _load_manifest() -> dict[str, dict[str, object]]:
    """Load the repos dict from workspace-manifest.json."""
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    repos: dict[str, dict[str, object]] = data.get("repositories", {})  # noqa: qg-empty-fallback
    return repos


def _extract_dep_name(dep: dict[str, str] | str) -> str:
    """Extract dependency name from either dict or plain string format."""
    if isinstance(dep, dict):
        return str(dep.get("name", ""))
    return str(dep)


def build_reverse_map(repos: dict[str, dict[str, object]]) -> dict[str, list[str]]:
    """Build {repo: [list of repos that depend on it]} for every repo."""
    reverse: dict[str, list[str]] = {name: [] for name in repos}

    for repo_name, repo_data in repos.items():
        deps = repo_data.get("dependencies", [])  # noqa: qg-empty-fallback
        if not isinstance(deps, list):
            continue
        for dep in deps:
            dep_name = _extract_dep_name(dep)
            if dep_name in reverse:
                reverse[dep_name].append(repo_name)

    # Sort each dependent list for deterministic output
    for dep_list in reverse.values():
        dep_list.sort()

    return reverse


def _format_text(reverse_map: dict[str, list[str]], repo_filter: str | None) -> str:
    """Human-readable text output."""
    lines: list[str] = []

    if repo_filter:
        dependents = reverse_map.get(repo_filter, [])
        lines.append(f"{repo_filter} ({len(dependents)} dependents):")
        if dependents:
            for dep in dependents:
                lines.append(f"  - {dep}")
        else:
            lines.append("  (no dependents)")
        return "\n".join(lines)

    # Full map: sorted by number of dependents (most first)
    sorted_repos = sorted(reverse_map.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    for repo_name, dependents in sorted_repos:
        count = len(dependents)
        if count == 0:
            lines.append(f"{repo_name}: (no dependents)")
        else:
            dep_str = ", ".join(dependents)
            lines.append(f"{repo_name} ({count}): {dep_str}")

    return "\n".join(lines)


def _format_json(reverse_map: dict[str, list[str]], repo_filter: str | None) -> str:
    """JSON output."""
    if repo_filter:
        subset = {repo_filter: reverse_map.get(repo_filter, [])}
        return json.dumps(subset, indent=2, sort_keys=True)
    return json.dumps(reverse_map, indent=2, sort_keys=True)


def _sanitize_id(name: str) -> str:
    """Convert a repo name to a valid Mermaid node ID."""
    return name.replace("-", "_").replace(".", "_")


def _format_mermaid(reverse_map: dict[str, list[str]], repo_filter: str | None) -> str:
    """Mermaid flowchart: dependent --> dependency."""
    lines: list[str] = ["graph LR", ""]

    if repo_filter:
        # Show only edges pointing to repo_filter
        dependents = reverse_map.get(repo_filter, [])
        target_id = _sanitize_id(repo_filter)
        lines.append(f'    {target_id}["{repo_filter}"]')
        for dep in dependents:
            dep_id = _sanitize_id(dep)
            lines.append(f'    {dep_id}["{dep}"] --> {target_id}')
    else:
        # Full graph: only repos with at least one dependent
        emitted_nodes: set[str] = set()
        for repo_name, dependents in sorted(reverse_map.items()):
            if not dependents:
                continue
            target_id = _sanitize_id(repo_name)
            if target_id not in emitted_nodes:
                lines.append(f'    {target_id}["{repo_name}"]')
                emitted_nodes.add(target_id)
            for dep in dependents:
                dep_id = _sanitize_id(dep)
                if dep_id not in emitted_nodes:
                    lines.append(f'    {dep_id}["{dep}"]')
                    emitted_nodes.add(dep_id)
                lines.append(f"    {dep_id} --> {target_id}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Reverse dependency lookup from workspace-manifest.json")
    parser.add_argument(
        "--repo",
        type=str,
        default=None,
        help="Show dependents for this specific repo only",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "mermaid"],
        default="text",
        help="Output format (default: text)",
    )
    args = parser.parse_args()

    repos = _load_manifest()
    reverse_map = build_reverse_map(repos)

    if args.repo and args.repo not in repos:
        print(f"ERROR: Repo '{args.repo}' not found in manifest", file=sys.stderr)
        print(f"Available repos: {', '.join(sorted(repos.keys()))}", file=sys.stderr)
        return 1

    if args.format == "text":
        output = _format_text(reverse_map, args.repo)
    elif args.format == "json":
        output = _format_json(reverse_map, args.repo)
    elif args.format == "mermaid":
        output = _format_mermaid(reverse_map, args.repo)
    else:
        output = _format_text(reverse_map, args.repo)

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
