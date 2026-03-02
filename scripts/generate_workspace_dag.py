#!/usr/bin/env python3
"""Generate WORKSPACE_MANIFEST_DAG.svg from workspace-manifest.json.

SSOT: unified-trading-pm/workspace-manifest.json
Output: unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg
Symlink: unified-trading-codex/04-architecture/WORKSPACE_MANIFEST_DAG.svg -> ../../unified-trading-pm/WORKSPACE_MANIFEST_DAG.svg
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
MANIFEST = SCRIPT_DIR.parent / "workspace-manifest.json"
OUTPUT = SCRIPT_DIR.parent / "WORKSPACE_MANIFEST_DAG.svg"

LEVEL_COLORS = {
    0: "#1e3a5f",   # PM — dark navy
    1: "#16a34a",   # Codex — green
    2: "#3b82f6",   # T0 foundation — blue
    3: "#7c3aed",   # T1 UTS — purple
    4: "#8b5cf6",   # T2 interfaces — violet
    5: "#ec4899",   # T3 core interfaces — pink
    6: "#dc2626",   # DeFi/sports execution — red
    7: "#ea580c",   # Foundational services — orange
    8: "#0891b2",   # Deployment infra — cyan
    9: "#06b6d4",   # Data-flow services — teal
    10: "#f97316",  # Operational + API — amber
    11: "#a855f7",  # UIs — purple
    12: "#64748b",  # IaC + post-deploy — slate
}

TYPE_CSS = {
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


def bw(name: str) -> int:
    return max(len(name) * CHARS_PX + 20, BOX_MIN_W)


def layout_rows(repos: list) -> list:
    rows, row, x = [], [], CANVAS_L
    for item in repos:
        w = bw(item[0])
        if row and x + w > CANVAS_L + ROW_MAX_W:
            rows.append(row)
            row, x = [], CANVAS_L
        row.append((*item, x, w))
        x += w + BOX_PAD
    if row:
        rows.append(row)
    return rows


def band_h(rows: list) -> int:
    return LVL_HDR_H + LVL_PAD_T + len(rows) * ROW_H + LVL_PAD_B


def generate() -> None:
    with open(MANIFEST) as f:
        data = json.load(f)

    repos = data["repositories"]
    total = len(repos)

    level_desc: dict[int, str] = {}
    # Read level descriptions from topologicalOrder (SSOT) or legacy topology.merge_order
    topo_levels = data.get("topologicalOrder", {}).get("levels", [])
    if not topo_levels:
        topo_levels = data.get("topology", {}).get("merge_order", [])
    for entry in topo_levels:
        level_desc[entry["level"]] = entry.get("description", f"Level {entry['level']}")

    levels: dict[int, list] = {}
    for name, info in repos.items():
        lvl = info.get("merge_level")
        if lvl is None or lvl < 0:
            continue  # skip deprecated/null repos
        css = "future" if info.get("status") == "planned" else TYPE_CSS.get(info.get("type", ""), "infra")
        ver = info.get("version", "0.1.0")
        levels.setdefault(lvl, []).append((name, ver, css))

    for lvl in levels:
        levels[lvl].sort(key=lambda x: x[0])

    level_rows = {lvl: layout_rows(levels[lvl]) for lvl in levels}
    level_heights = {lvl: band_h(level_rows[lvl]) for lvl in levels}

    HEADER_H = 90
    LEGEND_H = 90
    FOOTER_H = 100
    content_h = sum(level_heights[lvl] for lvl in levels) + LVL_GAP * (len(levels) - 1)
    SVG_H = HEADER_H + LEGEND_H + content_h + FOOTER_H + 40

    out: list[str] = []

    def ln(s: str) -> None:
        out.append(s)

    ln(f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_W}" height="{SVG_H}" viewBox="0 0 {SVG_W} {SVG_H}">')
    ln("  <defs><style>")
    ln(CSS)
    ln("  </style></defs>")
    ln(f'  <rect class="bg" x="0" y="0" width="{SVG_W}" height="{SVG_H}" />')

    ln(f'  <text x="40" y="38" class="title">Workspace Manifest - Topological DAG ({len(levels)} levels)</text>')
    ln(f'  <text x="40" y="58" class="subtitle">{total} repos. SSOT: workspace-manifest.json. Generated by unified-trading-pm/scripts/generate_workspace_dag.py</text>')
    ln('  <text x="40" y="74" class="subtitle">Quickmerge in level order: L0 first, then L1, etc. Version bumps auto-triggered by GitHub Actions on merge to main.</text>')

    # Legend
    ln('  <rect x="1700" y="15" width="670" height="74" class="legend-box" />')
    ln('  <text x="1720" y="36" class="section">Legend</text>')
    legend_items = [
        (1720, 46, "lib", "library"), (1840, 46, "svc", "service"),
        (1960, 46, "api", "api-service"), (2100, 46, "ui-box", "ui"),
        (1720, 66, "infra", "infrastructure"), (1880, 66, "devops", "devops"),
        (2020, 66, "test", "test-harness"), (2160, 66, "future", "future"),
    ]
    for lx, ly, cls, lbl in legend_items:
        ln(f'  <rect x="{lx}" y="{ly}" width="50" height="16" class="{cls}" /><text x="{lx+58}" y="{ly+12}" class="small">{lbl}</text>')

    y = HEADER_H + LEGEND_H
    for lvl in sorted(levels.keys()):
        rows = level_rows[lvl]
        bh = level_heights[lvl]
        desc = level_desc.get(lvl, f"Level {lvl}")
        color = LEVEL_COLORS.get(lvl, "#64748b")
        count = len(levels[lvl])

        ln(f'  <!-- L{lvl}: {desc} ({count} repos) -->')
        ln(f'  <rect x="40" y="{y}" width="2320" height="{bh}" class="level-bg" />')
        ln(f'  <rect x="55" y="{y+8}" width="80" height="22" fill="{color}" class="level-badge" />')
        ln(f'  <text x="95" y="{y+24}" text-anchor="middle" class="level-label">L{lvl}</text>')
        ln(f'  <text x="150" y="{y+24}" class="desc">{desc} ({count} repos)</text>')

        row_y = y + LVL_HDR_H + LVL_PAD_T
        for row in rows:
            for name, ver, css, bx, w in row:
                cx = bx + w // 2
                ln(f'  <rect x="{bx}" y="{row_y}" width="{w}" height="{BOX_H}" class="{css}" />')
                ln(f'  <text x="{cx}" y="{row_y+18}" text-anchor="middle" class="label">{name}</text>')
                ln(f'  <text x="{cx}" y="{row_y+30}" text-anchor="middle" class="ver">{ver}</text>')
            row_y += ROW_H

        y += bh + LVL_GAP

    # Footer
    footer_y = y + 20
    type_counts: dict[str, int] = {}
    for info in repos.values():
        t = info.get("type", "unknown")
        type_counts[t] = type_counts.get(t, 0) + 1
    counts_str = ", ".join(f"{v} {k}s" for k, v in sorted(type_counts.items()))

    ln(f'  <rect x="40" y="{footer_y}" width="2320" height="90" fill="#ffffff" stroke="#e2e8f0" stroke-width="1" rx="8" />')
    ln(f'  <text x="60" y="{footer_y+25}" class="section">Versioning + Summary</text>')
    ln(f'  <text x="60" y="{footer_y+45}" class="small">All 0.x.x. Version 1.0.0 = first stable (GitHub Actions auto-bump on main merge). No local version bumping. CI/CD in level order.</text>')
    ln(f'  <text x="60" y="{footer_y+60}" class="small">{total} repos: {counts_str}</text>')
    ln(f'  <text x="60" y="{footer_y+75}" class="small">Deployment modes: runtime-topology.yaml deployment_modes | Checklist SSOTs: checklist.template.{{service,api-service,ui,library}}.yaml</text>')
    ln("</svg>")

    OUTPUT.write_text("\n".join(out) + "\n")
    print(f"Generated: {OUTPUT}")
    print(f"  {total} repos across {len(levels)} levels")


if __name__ == "__main__":
    generate()
