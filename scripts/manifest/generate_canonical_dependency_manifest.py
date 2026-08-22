#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Generate canonical-dependency-manifest.json and CANONICAL_DEPENDENCY_MANIFEST.svg.

Reads unified-trading-pm/workspace-constraints.toml (external packages only).
Outputs:
  - unified-trading-pm/canonical-dependency-manifest.json (SSOT for external deps)
  - unified-trading-pm/CANONICAL_DEPENDENCY_MANIFEST.svg (visual)

SSOT: unified-trading-pm/canonical-dependency-manifest.json
Source data: workspace-constraints.toml (from resolve-canonical-versions.py).
Workflow manifest (workspace-manifest.json) pins internal/private repos; this manifest
pins external PyPI packages. Together they form the full dependency picture.
"""

from __future__ import annotations

import json
import sys
import tomllib
import xml.etree.ElementTree as ET
from html import escape as html_escape
from pathlib import Path
from typing import Any, cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
CONSTRAINTS_PATH = PM_ROOT / "workspace-constraints.toml"
MANIFEST_JSON_PATH = PM_ROOT / "canonical-dependency-manifest.json"
SVG_PATH = PM_ROOT / "CANONICAL_DEPENDENCY_MANIFEST.svg"

# SVG layout
BOX_H = 32
BOX_PAD = 8
ROW_H = BOX_H + 6
CHARS_PX = 6
BOX_MIN_W = 100
ROW_MAX_W = 1100
SVG_W = 1200
CANVAS_L = 40
LVL_GAP = 8

CSS = """
  .bg { fill: #f8fafc; }
  .title { font: 700 22px Arial, sans-serif; fill: #0f172a; }
  .subtitle { font: 500 12px Arial, sans-serif; fill: #475569; }
  .section { font: 700 13px Arial, sans-serif; fill: #0f172a; }
  .label { font: 600 10px Arial, sans-serif; fill: #0f172a; }
  .ver { font: 500 9px Arial, sans-serif; fill: #64748b; }
  .pkg-box { fill: #e0f2fe; stroke: #0284c7; stroke-width: 1; rx: 4; }
  .footer { font: 500 10px Arial, sans-serif; fill: #64748b; }
"""


def load_constraints() -> dict[str, str]:
    """Load [dependencies] from workspace-constraints.toml. Keys = package name, values = spec."""
    if not CONSTRAINTS_PATH.is_file():
        return {}
    with open(CONSTRAINTS_PATH, "rb") as f:
        data: dict[str, Any] = cast(dict[str, Any], tomllib.load(f))
    deps = data.get("dependencies")
    if not isinstance(deps, dict):
        return {}
    return {k: str(v) for k, v in deps.items()}


def write_manifest_json(constraints: dict[str, str]) -> None:
    """Write canonical-dependency-manifest.json (external packages only)."""
    # Normalize to list of {name, versionRange} for stable order and clarity
    packages = [
        {"name": name, "versionRange": spec} for name, spec in sorted(constraints.items(), key=lambda x: x[0].lower())
    ]
    manifest = {
        "description": (
            "Canonical list of external (PyPI) dependency version ranges for the workspace. "
            "SSOT. Internal/private repos are in workspace-manifest.json."
        ),
        "sourceFile": "workspace-constraints.toml",
        # NOTE: deliberately NO generatedAt timestamp — this file is a TRACKED SSOT regenerated
        # by run-version-alignment.sh / QG; a wall-clock field churns it on every run (jamming
        # slot FF-pulls). Determinism > provenance: git history records when it actually changed.
        "generator": "unified-trading-pm/scripts/manifest/generate_canonical_dependency_manifest.py",
        "externalPackages": packages,
        "count": len(packages),
    }
    MANIFEST_JSON_PATH.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Wrote {MANIFEST_JSON_PATH} ({len(packages)} packages)")


def box_width(name: str, spec: str) -> int:
    """Width for a box showing name + truncated spec."""
    # One row: name on top, spec below
    w_name = max(len(name) * CHARS_PX + 16, BOX_MIN_W)
    w_spec = min(len(spec) * CHARS_PX + 16, 220)
    return max(w_name, w_spec)


def generate_svg(constraints: dict[str, str]) -> str:
    """Generate SVG: grid of packages (name + version range)."""
    # Sort by name for stable layout
    items = sorted(constraints.items(), key=lambda x: x[0].lower())
    rows: list[list[tuple[str, str, int, int]]] = []  # (name, spec, x, width)
    row: list[tuple[str, str, int, int]] = []
    x = CANVAS_L
    for name, spec in items:
        w = box_width(name, spec)
        if row and x + w > CANVAS_L + ROW_MAX_W:
            rows.append(row)
            row = []
            x = CANVAS_L
        row.append((name, spec, x, w))
        x += w + BOX_PAD
    if row:
        rows.append(row)

    header_h = 70
    content_h = len(rows) * ROW_H + LVL_GAP * max(len(rows) - 1, 0)
    footer_h = 50
    svg_h = header_h + content_h + footer_h + 40

    out: list[str] = []

    def ln(s: str) -> None:
        out.append(s)

    ln(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{svg_h}" viewBox="0 0 {SVG_W} {svg_h}">')
    ln("<defs><style>")
    ln(CSS)
    ln("</style></defs>")
    ln(f'<rect class="bg" x="0" y="0" width="{SVG_W}" height="{svg_h}" />')
    ln('<text x="40" y="32" class="title">Canonical External Dependencies</text>')
    ln(
        '<text x="40" y="50" class="subtitle">'
        "SSOT: unified-trading-pm/canonical-dependency-manifest.json. "
        "External packages only; internal repos in workspace-manifest.json.</text>"
    )
    ln(
        f'<text x="40" y="64" class="subtitle">'
        f"{len(items)} packages. Generated by scripts/manifest/generate_canonical_dependency_manifest.py</text>"
    )

    y = header_h
    for row_entries in rows:
        for name, spec, px, w in row_entries:
            # Truncate long specs for display
            spec_show = spec if len(spec) <= 28 else spec[:25] + "..."
            ln(f'  <rect x="{px}" y="{y}" width="{w}" height="{BOX_H}" class="pkg-box" />')
            ln(f'  <text x="{px + w // 2}" y="{y + 14}" text-anchor="middle" class="label">{html_escape(name)}</text>')
            ln(
                f'  <text x="{px + w // 2}" y="{y + 26}" text-anchor="middle" class="ver">'
                f"{html_escape(spec_show)}</text>"
            )
        y += ROW_H + LVL_GAP

    footer_y = y + 20
    ln(
        f'<text x="40" y="{footer_y}" class="footer">'
        "Pin new external deps to these ranges. See 06-coding-standards/dependency-management.md "
        "and cursor rule canonical-external-deps.mdc.</text>"
    )
    ln("</svg>")
    return "\n".join(out) + "\n"


def main() -> None:
    constraints = load_constraints()
    if not constraints:
        print(f"ERROR: No constraints found at {CONSTRAINTS_PATH}", file=sys.stderr)
        print("Run resolve-canonical-versions.py first.", file=sys.stderr)
        raise SystemExit(1)

    write_manifest_json(constraints)
    svg_content = generate_svg(constraints)
    ET.fromstring(svg_content)  # nosec B314 — validates our own generated SVG, not untrusted input
    SVG_PATH.write_text(svg_content)
    print(f"Wrote {SVG_PATH}")


if __name__ == "__main__":
    main()
