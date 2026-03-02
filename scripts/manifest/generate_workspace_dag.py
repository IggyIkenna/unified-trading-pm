#!/usr/bin/env python3
"""Generate WORKSPACE_MANIFEST_DAG.svg from workspace-manifest.json.

SSOT: unified-trading-pm/workspace-manifest.json
Output: unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg
Symlink: unified-trading-codex/04-architecture/WORKSPACE_MANIFEST_DAG.svg
    -> ../../unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from html import escape as html_escape
from pathlib import Path
from typing import NamedTuple, cast

SCRIPT_DIR = Path(__file__).parent
PM_ROOT = SCRIPT_DIR.parent.parent
MANIFEST = PM_ROOT / "workspace-manifest.json"
OUTPUT = PM_ROOT / "WORKSPACE_MANIFEST_DAG.svg"

# --- JSON typing helpers (contained cast boundary for json.load) ---

JsonDict = dict[str, "JsonDict | list[JsonDict] | str | int | float | bool | None"]
"""Recursive JSON object type — used to replace bare `object` at the JSON boundary."""


def _jdict(val: object) -> JsonDict | None:
    """Narrow an object to JsonDict if it is a dict, else None."""
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jlist(val: object) -> list[JsonDict] | None:
    """Narrow an object to a list of JsonDict if it is a list, else None."""
    if isinstance(val, list):
        return cast(list[JsonDict], val)
    return None


def _jstr(val: object, default: str = "") -> str:
    """Extract a string from a JSON value, with fallback."""
    return str(val) if val is not None else default


def _jint(val: object) -> int | None:
    """Extract an int from a JSON value, or None."""
    return val if isinstance(val, int) else None


# --- Layout constants ---

LEVEL_COLORS: dict[int, str] = {
    0: "#1e3a5f",  # PM — dark navy
    1: "#16a34a",  # Codex — green
    2: "#3b82f6",  # T0 foundation — blue
    3: "#7c3aed",  # T1 UTS — purple
    4: "#8b5cf6",  # T2 interfaces — violet
    5: "#ec4899",  # T3 core interfaces — pink
    6: "#dc2626",  # DeFi/sports execution — red
    7: "#ea580c",  # Foundational services — orange
    8: "#0891b2",  # Deployment infra — cyan
    9: "#06b6d4",  # Data-flow services — teal
    10: "#f97316",  # Operational + API — amber
    11: "#a855f7",  # UIs — purple
    12: "#64748b",  # IaC + post-deploy — slate
}

TYPE_CSS: dict[str, str] = {
    "library": "lib",
    "service": "svc",
    "api-service": "api",
    "ui": "ui-box",
    "infrastructure": "infra",
    "devops": "devops",
    "test-harness": "test",
}

CSS = """\
      .bg { fill: #fafbfc; }
      .title { font: 700 26px Arial, sans-serif; fill: #0f172a; }
      .subtitle { font: 500 13px Arial, sans-serif; fill: #475569; }
      .section { font: 700 14px Arial, sans-serif; fill: #0f172a; }
      .level-label { font: 700 13px Arial, sans-serif; fill: #ffffff; }
      .label { font: 600 11px Arial, sans-serif; fill: #0f172a; }
      .ver { font: 500 10px Arial, sans-serif; fill: #64748b; }
      .small { font: 500 10px Arial, sans-serif; fill: #64748b; }
      .desc { font: 500 11px Arial, sans-serif; fill: #334155; }
      .lib { fill: #dbeafe; stroke: #3b82f6; stroke-width: 1.4; rx: 6; }
      .svc { fill: #fce7f3; stroke: #db2777; stroke-width: 1.4; rx: 6; }
      .api { fill: #f3e8ff; stroke: #7c3aed; stroke-width: 1.4; rx: 6; }
      .ui-box { fill: #ecfeff; stroke: #06b6d4; stroke-width: 1.4; rx: 6; }
      .infra { fill: #f1f5f9; stroke: #64748b; stroke-width: 1.4; rx: 6; }
      .devops { fill: #f0fdf4; stroke: #16a34a; stroke-width: 1.4; rx: 6; }
      .test { fill: #fef3c7; stroke: #d97706; stroke-width: 1.4; rx: 6; }
      .future { fill: #f8fafc; stroke: #cbd5e1; stroke-width: 1; rx: 6; stroke-dasharray: 4 2; }
      .level-bg { fill: #ffffff; stroke: #e2e8f0; stroke-width: 1; rx: 10; }
      .level-badge { rx: 4; }
      .legend-box { fill: #ffffff; stroke: #e2e8f0; stroke-width: 1; rx: 8; }"""

BOX_H = 38
BOX_PAD = 10
ROW_H = BOX_H + 10
LVL_HDR_H = 35
LVL_PAD_T = 12
LVL_PAD_B = 12
LVL_GAP = 12
CANVAS_L = 70
ROW_MAX_W = 2290
SVG_W = 2400
CHARS_PX = 7
BOX_MIN_W = 130

# --- Data structures ---


class RepoEntry(NamedTuple):
    """A repo's display info: name, version, CSS class."""

    name: str
    version: str
    css_class: str


class LayoutEntry(NamedTuple):
    """A repo positioned in the SVG layout."""

    name: str
    version: str
    css_class: str
    x: int
    width: int


# --- Layout helpers ---


def box_width(name: str) -> int:
    """Calculate box width based on name length."""
    return max(len(name) * CHARS_PX + 20, BOX_MIN_W)


def layout_rows(repos: list[RepoEntry]) -> list[list[LayoutEntry]]:
    """Arrange repos into rows that fit within ROW_MAX_W."""
    rows: list[list[LayoutEntry]] = []
    row: list[LayoutEntry] = []
    x = CANVAS_L
    for item in repos:
        w = box_width(item.name)
        if row and x + w > CANVAS_L + ROW_MAX_W:
            rows.append(row)
            row = []
            x = CANVAS_L
        row.append(
            LayoutEntry(
                name=item.name,
                version=item.version,
                css_class=item.css_class,
                x=x,
                width=w,
            )
        )
        x += w + BOX_PAD
    if row:
        rows.append(row)
    return rows


def band_height(rows: list[list[LayoutEntry]]) -> int:
    """Calculate the pixel height of a level band."""
    return LVL_HDR_H + LVL_PAD_T + len(rows) * ROW_H + LVL_PAD_B


# --- Manifest parsing ---


def parse_level_descriptions(data: JsonDict) -> dict[int, str]:
    """Extract level number -> description mapping from manifest."""
    level_desc: dict[int, str] = {}

    topo_levels: list[JsonDict] | None = None
    topo_order = _jdict(data.get("topologicalOrder"))
    if topo_order is not None:
        topo_levels = _jlist(topo_order.get("levels"))

    if topo_levels is None:
        topology = _jdict(data.get("topology"))
        if topology is not None:
            topo_levels = _jlist(topology.get("merge_order"))

    if topo_levels is None:
        return level_desc

    for entry_raw in topo_levels:
        entry = _jdict(entry_raw)
        if entry is None:
            continue
        lvl_val = _jint(entry.get("level"))
        if lvl_val is None:
            continue
        desc_val = entry.get("description")
        level_desc[lvl_val] = _jstr(desc_val, f"Level {lvl_val}")

    return level_desc


def parse_repos(
    repos_raw: JsonDict,
) -> tuple[dict[int, list[RepoEntry]], dict[str, int]]:
    """Extract level->repos map and type counts from repositories dict."""
    levels: dict[int, list[RepoEntry]] = {}
    type_counts: dict[str, int] = {}

    for name, info_raw in repos_raw.items():
        info = _jdict(info_raw)
        if info is None:
            continue

        # Count types for footer
        repo_type = _jstr(info.get("type"), "unknown")
        type_counts[repo_type] = type_counts.get(repo_type, 0) + 1

        # Skip repos without valid merge_level
        lvl = _jint(info.get("merge_level"))
        if lvl is None or lvl < 0:
            continue

        status = _jstr(info.get("status"))
        css = "future" if status == "planned" else TYPE_CSS.get(repo_type, "infra")
        ver = _jstr(info.get("version"), "0.1.0")
        levels.setdefault(lvl, []).append(
            RepoEntry(name=name, version=ver, css_class=css),
        )

    for lvl in levels:
        levels[lvl].sort(key=lambda r: r.name)

    return levels, type_counts


# --- SVG generation ---


def generate_svg(data: JsonDict) -> str:
    """Generate SVG string from parsed manifest data."""
    repos_raw = _jdict(data.get("repositories"))
    if repos_raw is None:
        raise ValueError("workspace-manifest.json missing 'repositories' dict")
    total = len(repos_raw)

    level_desc = parse_level_descriptions(data)
    levels, type_counts = parse_repos(repos_raw)

    level_rows = {lvl: layout_rows(levels[lvl]) for lvl in levels}
    level_heights = {lvl: band_height(level_rows[lvl]) for lvl in levels}

    header_h = 90
    legend_h = 90
    footer_h = 100
    content_h = sum(level_heights.values()) + LVL_GAP * max(len(levels) - 1, 0)
    svg_h = header_h + legend_h + content_h + footer_h + 40

    out: list[str] = []

    def ln(s: str) -> None:
        out.append(s)

    ln(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{svg_h}" viewBox="0 0 {SVG_W} {svg_h}">')
    ln("  <defs><style>")
    ln(CSS)
    ln("  </style></defs>")
    ln(f'  <rect class="bg" x="0" y="0" width="{SVG_W}" height="{svg_h}" />')

    ln(f'  <text x="40" y="38" class="title">Workspace Manifest - Topological DAG ({len(levels)} levels)</text>')
    ln(
        f'  <text x="40" y="58" class="subtitle">{total} repos.'
        " SSOT: workspace-manifest.json."
        " Generated by unified-trading-pm/scripts/manifest/generate_workspace_dag.py</text>"
    )
    ln(
        '  <text x="40" y="74" class="subtitle">'
        "Quickmerge in level order: L0 first, then L1, etc."
        " Version bumps auto-triggered by GitHub Actions on merge to main.</text>"
    )

    # Legend
    ln('  <rect x="1700" y="15" width="670" height="74" class="legend-box" />')
    ln('  <text x="1720" y="36" class="section">Legend</text>')
    legend_items: list[tuple[int, int, str, str]] = [
        (1720, 46, "lib", "library"),
        (1840, 46, "svc", "service"),
        (1960, 46, "api", "api-service"),
        (2100, 46, "ui-box", "ui"),
        (1720, 66, "infra", "infrastructure"),
        (1880, 66, "devops", "devops"),
        (2020, 66, "test", "test-harness"),
        (2160, 66, "future", "future"),
    ]
    for lx, ly, cls, lbl in legend_items:
        ln(
            f'  <rect x="{lx}" y="{ly}" width="50" height="16" class="{cls}" />'
            f'<text x="{lx + 58}" y="{ly + 12}" class="small">{lbl}</text>'
        )

    y = header_h + legend_h
    for lvl in sorted(levels.keys()):
        rows = level_rows[lvl]
        bh = level_heights[lvl]
        desc = level_desc.get(lvl, f"Level {lvl}")
        color = LEVEL_COLORS.get(lvl, "#64748b")
        count = len(levels[lvl])

        esc_desc = html_escape(desc)
        ln(f"  <!-- L{lvl}: {esc_desc} ({count} repos) -->")
        ln(f'  <rect x="40" y="{y}" width="2320" height="{bh}" class="level-bg" />')
        ln(f'  <rect x="55" y="{y + 8}" width="80" height="22" fill="{color}" class="level-badge" />')
        ln(f'  <text x="95" y="{y + 24}" text-anchor="middle" class="level-label">L{lvl}</text>')
        ln(f'  <text x="150" y="{y + 24}" class="desc">{esc_desc} ({count} repos)</text>')

        row_y = y + LVL_HDR_H + LVL_PAD_T
        for row in rows:
            for entry in row:
                cx = entry.x + entry.width // 2
                ln(
                    f'  <rect x="{entry.x}" y="{row_y}"'
                    f' width="{entry.width}" height="{BOX_H}"'
                    f' class="{entry.css_class}" />'
                )
                ln(
                    f'  <text x="{cx}" y="{row_y + 18}"'
                    f' text-anchor="middle" class="label">'
                    f"{html_escape(entry.name)}</text>"
                )
                ln(
                    f'  <text x="{cx}" y="{row_y + 30}"'
                    f' text-anchor="middle" class="ver">'
                    f"{html_escape(entry.version)}</text>"
                )
            row_y += ROW_H

        y += bh + LVL_GAP

    # Footer
    footer_y = y + 20
    counts_str = ", ".join(f"{v} {k}s" for k, v in sorted(type_counts.items()))

    ln(
        f'  <rect x="40" y="{footer_y}" width="2320" height="90"'
        ' fill="#ffffff" stroke="#e2e8f0" stroke-width="1" rx="8" />'
    )
    ln(f'  <text x="60" y="{footer_y + 25}" class="section">Versioning + Summary</text>')
    ln(
        f'  <text x="60" y="{footer_y + 45}" class="small">'
        "All 0.x.x. Version 1.0.0 = first stable"
        " (GitHub Actions auto-bump on main merge)."
        " No local version bumping. CI/CD in level order.</text>"
    )
    ln(f'  <text x="60" y="{footer_y + 60}" class="small">{total} repos: {counts_str}</text>')
    ln(
        f'  <text x="60" y="{footer_y + 75}" class="small">'
        "Deployment modes: runtime-topology.yaml deployment_modes"
        " | Checklist SSOTs:"
        " checklist.template.{service,api-service,ui,library}.yaml</text>"
    )
    ln("</svg>")

    return "\n".join(out) + "\n"


def generate(
    manifest_path: Path | None = None,
    output_path: Path | None = None,
) -> Path:
    """Generate the DAG SVG from the manifest and write to disk.

    Args:
        manifest_path: Path to workspace-manifest.json. Defaults to MANIFEST.
        output_path: Path for the output SVG. Defaults to OUTPUT.

    Returns:
        The path of the written SVG file.
    """
    src = manifest_path or MANIFEST
    dst = output_path or OUTPUT

    with open(src) as f:
        data = cast(JsonDict, json.load(f))

    svg_content = generate_svg(data)

    # Validate output is well-formed XML before writing
    ET.fromstring(svg_content)

    dst.write_text(svg_content)
    print(f"Generated: {dst}")
    return dst


if __name__ == "__main__":
    generate()
