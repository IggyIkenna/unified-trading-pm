#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Generate Mermaid DAG from strategy-manifest.json.

Outputs a Mermaid diagram to stdout showing:
  - Strategy nodes (colored by maturity)
  - Edges: strategy -> asset_groupes
  - Edges: strategy -> venues
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = WORKSPACE_ROOT / "strategy-manifest.json"

MATURITY_STYLES = {
    "production": "fill:#2ecc71,stroke:#27ae60,color:#000",
    "beta": "fill:#3498db,stroke:#2980b9,color:#fff",
    "experimental": "fill:#e67e22,stroke:#d35400,color:#fff",
}


def _sanitize_id(name: str) -> str:
    """Convert a name to a valid Mermaid node ID."""
    return name.replace(" ", "_").replace("-", "_").replace(".", "_")


def main() -> int:
    if not MANIFEST_PATH.exists():
        print(f"ERROR: Manifest not found at {MANIFEST_PATH}", file=sys.stderr)
        return 1

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    strategies = manifest.get("strategies", [])  # noqa: qg-empty-fallback

    if not strategies:
        print("WARNING: No strategies found in manifest", file=sys.stderr)
        return 0

    # Collect unique asset classes and venues
    all_asset_groupes: set[str] = set()
    all_venues: set[str] = set()
    for strat in strategies:
        all_asset_groupes.update(strat.get("asset_groupes", []))  # noqa: qg-empty-fallback
        all_venues.update(strat.get("venues", []))  # noqa: qg-empty-fallback

    lines: list[str] = []
    lines.append("graph LR")
    lines.append("")

    # --- Subgraph: Asset Classes ---
    lines.append("    subgraph asset_groupes")
    for ac in sorted(all_asset_groupes):
        ac_id = _sanitize_id(f"ac_{ac}")
        lines.append(f'        {ac_id}["{ac}"]')
    lines.append("    end")
    lines.append("")

    # --- Subgraph: Strategies ---
    lines.append("    subgraph Strategies")
    for strat in strategies:
        name = strat["name"]
        maturity = strat["maturity"]
        node_id = _sanitize_id(f"s_{name}")
        label = f"{name}\\n({maturity})"
        lines.append(f'        {node_id}["{label}"]')
    lines.append("    end")
    lines.append("")

    # --- Subgraph: Venues ---
    lines.append("    subgraph Venues")
    for venue in sorted(all_venues):
        v_id = _sanitize_id(f"v_{venue}")
        lines.append(f'        {v_id}["{venue}"]')
    lines.append("    end")
    lines.append("")

    # --- Edges: strategy -> asset class ---
    lines.append("    %% Strategy -> Asset Class edges")
    for strat in strategies:
        name = strat["name"]
        s_id = _sanitize_id(f"s_{name}")
        for ac in strat.get("asset_groupes", []):  # noqa: qg-empty-fallback
            ac_id = _sanitize_id(f"ac_{ac}")
            lines.append(f"    {ac_id} --> {s_id}")
    lines.append("")

    # --- Edges: strategy -> venue ---
    lines.append("    %% Strategy -> Venue edges")
    for strat in strategies:
        name = strat["name"]
        s_id = _sanitize_id(f"s_{name}")
        for venue in strat.get("venues", []):  # noqa: qg-empty-fallback
            v_id = _sanitize_id(f"v_{venue}")
            lines.append(f"    {s_id} --> {v_id}")
    lines.append("")

    # --- Style nodes by maturity ---
    lines.append("    %% Maturity-based styling")
    for strat in strategies:
        name = strat["name"]
        maturity = strat["maturity"]
        node_id = _sanitize_id(f"s_{name}")
        style = MATURITY_STYLES.get(maturity, MATURITY_STYLES["experimental"])
        lines.append(f"    style {node_id} {style}")

    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
