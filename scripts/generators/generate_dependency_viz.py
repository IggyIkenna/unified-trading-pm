#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Generate interactive Mermaid dependency graph from workspace-manifest.json.

Produces a Mermaid diagram of the full dependency graph, color-coded by tier:
  T0 = red, T1 = orange, T2 = yellow, T3 = green

Usage:
    python3 generate_dependency_viz.py                   # full graph
    python3 generate_dependency_viz.py --filter-tier 1   # T0 + T1 only
    python3 generate_dependency_viz.py --filter-tier 2   # T0 + T1 + T2
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"

# Mermaid style strings per tier
TIER_STYLES: dict[int, str] = {
    0: "fill:#e74c3c,stroke:#c0392b,color:#fff",  # red
    1: "fill:#e67e22,stroke:#d35400,color:#fff",  # orange
    2: "fill:#f1c40f,stroke:#f39c12,color:#000",  # yellow
    3: "fill:#2ecc71,stroke:#27ae60,color:#000",  # green
}

TIER_LABELS: dict[int, str] = {
    0: "T0 (Foundation)",
    1: "T1 (Core Libraries)",
    2: "T2 (Domain Libraries)",
    3: "T3 (Services / UIs / APIs)",
}

# Fallback style for repos without a tier
UNKNOWN_STYLE = "fill:#95a5a6,stroke:#7f8c8d,color:#fff"


def _load_manifest() -> dict[str, dict[str, object]]:
    """Load the repos dict from workspace-manifest.json."""
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        sys.exit(1)
    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    repos: dict[str, dict[str, object]] = data.get("repositories", {})  # noqa: qg-empty-fallback
    return repos


def _sanitize_id(name: str) -> str:
    """Convert a repo name to a valid Mermaid node ID."""
    return name.replace("-", "_").replace(".", "_")


def _extract_dep_name(dep: dict[str, str] | str) -> str:
    """Extract dependency name from either dict or plain string format."""
    if isinstance(dep, dict):
        return str(dep.get("name", ""))
    return str(dep)


def _get_tier(repo_data: dict[str, object]) -> int | None:
    """Extract the tier from repo data, returning None if absent."""
    tier = repo_data.get("tier")
    if tier is not None:
        return int(tier)
    return None


def generate_mermaid(repos: dict[str, dict[str, object]], max_tier: int | None) -> str:
    """Generate a Mermaid diagram string."""
    lines: list[str] = ["graph LR", ""]

    # Filter repos by tier if requested
    filtered_repos: dict[str, dict[str, object]] = {}
    for name, data in repos.items():
        tier = _get_tier(data)
        if max_tier is not None and (tier is None or tier > max_tier):
            continue
        filtered_repos[name] = data

    if not filtered_repos:
        lines.append("    empty[No repos match filter]")
        return "\n".join(lines)

    # Group repos by tier for subgraphs
    tier_groups: dict[int, list[str]] = {}
    no_tier: list[str] = []
    for name, data in sorted(filtered_repos.items()):
        tier = _get_tier(data)
        if tier is not None:
            tier_groups.setdefault(tier, []).append(name)
        else:
            no_tier.append(name)

    # Emit subgraphs per tier
    for tier in sorted(tier_groups.keys()):
        label = TIER_LABELS.get(tier, f"Tier {tier}")
        lines.append(f"    subgraph {_sanitize_id(label)}")
        lines.append("        direction TB")
        for repo_name in tier_groups[tier]:
            node_id = _sanitize_id(repo_name)
            lines.append(f'        {node_id}["{repo_name}"]')
        lines.append("    end")
        lines.append("")

    if no_tier:
        lines.append("    subgraph Unknown_Tier")
        lines.append("        direction TB")
        for repo_name in no_tier:
            node_id = _sanitize_id(repo_name)
            lines.append(f'        {node_id}["{repo_name}"]')
        lines.append("    end")
        lines.append("")

    # Emit dependency edges
    lines.append("    %% Dependency edges (consumer --> dependency)")
    for repo_name, repo_data in sorted(filtered_repos.items()):
        deps = repo_data.get("dependencies", [])  # noqa: qg-empty-fallback
        if not isinstance(deps, list):
            continue
        consumer_id = _sanitize_id(repo_name)
        for dep in deps:
            dep_name = _extract_dep_name(dep)
            if dep_name in filtered_repos:
                dep_id = _sanitize_id(dep_name)
                lines.append(f"    {consumer_id} --> {dep_id}")
    lines.append("")

    # Apply tier-based styles
    lines.append("    %% Tier-based styling")
    for repo_name, repo_data in sorted(filtered_repos.items()):
        tier = _get_tier(repo_data)
        node_id = _sanitize_id(repo_name)
        if tier is not None and tier in TIER_STYLES:
            lines.append(f"    style {node_id} {TIER_STYLES[tier]}")
        else:
            lines.append(f"    style {node_id} {UNKNOWN_STYLE}")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Mermaid dependency visualization from workspace-manifest.json"
    )
    parser.add_argument(
        "--filter-tier",
        type=int,
        default=None,
        metavar="N",
        help="Show only repos up to tier N (e.g. --filter-tier 1 shows T0+T1)",
    )
    args = parser.parse_args()

    repos = _load_manifest()
    output = generate_mermaid(repos, args.filter_tier)
    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
