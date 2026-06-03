#!/usr/bin/env python3
"""
CI/CD Pipeline Diagram Generator

Reads docs/repo-management/cicd-pipeline-definition.yaml
Writes docs/repo-management/CI-CD-PIPELINE.svg
       docs/repo-management/CI-CD-PIPELINE.html

Regenerate: python3 scripts/generate-cicd-diagram.py
"""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import cast

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: uv pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ─── Layout constants ─────────────────────────────────────────────────────────
LANE_HEADER_W: int = 110  # left-side swimlane label strip width (px)
LANE_H: int = 210  # height of each swimlane row (px)
COL_W: int = 400  # width per column unit (px)
NODE_W: int = 240  # process / notification node width (px)
NODE_H: int = 88  # process / notification node height (px)
DIAMOND_W: int = 130  # half-width of decision diamond (px)
DIAMOND_H: int = 68  # half-height of decision diamond (px)
START_R: int = 44  # radius of start/trigger circle (px)
END_W: int = 200  # terminal box width
END_H: int = 72  # terminal box height
FONT_MAIN: int = 12  # node body font size (px)
FONT_LANE: int = 10  # swimlane label font size (px)
FONT_EDGE: int = 10  # edge label font size (px)
FONT_ANN: int = 9  # annotation font size (px)
LINE_H: int = 15  # line height inside nodes (px)
TITLE_H: int = 56  # title bar height (px)
LEGEND_H: int = 44  # legend bar height (px)
ARROW_HEAD: int = 8  # arrowhead size (px)

BRANCH_COLORS: dict[str, str] = {
    "feat_star": "#5882c8",
    "staging": "#d48c1a",
    "main": "#2e8f45",
    "agent": "#8040b0",
    "both": "#777777",
}
BRANCH_FILL: dict[str, str] = {
    "feat_star": "#dde8f8",
    "staging": "#fdf0d0",
    "main": "#d8f4e0",
    "agent": "#ede0f8",
    "both": "#f0f0f0",
}
DARK_FILL: dict[str, str] = {
    "feat_star": "#3a5fa8",
    "staging": "#a86800",
    "main": "#1e6030",
    "agent": "#5c2090",
    "both": "#444444",
}


# ─── Helpers ──────────────────────────────────────────────────────────────────


def x(col: float) -> float:
    """Convert column index to canvas x-center (accounts for lane header)."""
    return LANE_HEADER_W + col * COL_W + COL_W / 2


def y(lane_idx: int) -> float:
    """Convert lane index to canvas y-center (accounts for title bar)."""
    return TITLE_H + lane_idx * LANE_H + LANE_H / 2


def cx(node: dict, lm: dict[str, int]) -> float:
    return x(node["col"])


def cy(node: dict, lm: dict[str, int]) -> float:
    return y(lm[node["swimlane"]])


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def text_block(
    px: float, py: float, lines: list[str], font_size: int, fill: str, anchor: str = "middle", weight: str = "normal"
) -> str:
    """Multi-line text centered at (px, py). Uses absolute tspan y coords."""
    n = len(lines)
    start_y = py - (n - 1) * LINE_H / 2
    spans = "".join(
        f'<tspan x="{px:.1f}" y="{start_y + i * LINE_H:.1f}">{esc(ln)}</tspan>' for i, ln in enumerate(lines)
    )
    return (
        f'<text text-anchor="{anchor}" font-size="{font_size}" '
        f"font-family=\"Inter,'Segoe UI',Arial,sans-serif\" "
        f'font-weight="{weight}" fill="{fill}">{spans}</text>'
    )


def rect_node(
    cx_: float, cy_: float, w: float, h: float, label: str, fill: str, stroke: str, rx: float = 8, tooltip: str = ""
) -> str:
    lines = label.split("\n")
    x0, y0 = cx_ - w / 2, cy_ - h / 2
    title = f"<title>{esc(tooltip)}</title>" if tooltip else ""
    rect = (
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{h:.1f}" '
        f'rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    )
    txt = text_block(cx_, cy_, lines, FONT_MAIN, "#111111")
    return f'<g class="node">{title}{rect}{txt}</g>'


def diamond_node(
    cx_: float, cy_: float, hw: float, hh: float, label: str, fill: str, stroke: str, tooltip: str = ""
) -> str:
    pts = f"{cx_:.1f},{cy_ - hh:.1f} {cx_ + hw:.1f},{cy_:.1f} {cx_:.1f},{cy_ + hh:.1f} {cx_ - hw:.1f},{cy_:.1f}"
    lines = label.split("\n")
    title = f"<title>{esc(tooltip)}</title>" if tooltip else ""
    poly = f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    txt = text_block(cx_, cy_, lines, FONT_MAIN - 1, "#111111")
    return f'<g class="node">{title}{poly}{txt}</g>'


def circle_node(cx_: float, cy_: float, r: float, label: str, fill: str, stroke: str, tooltip: str = "") -> str:
    lines = label.split("\n")
    title = f"<title>{esc(tooltip)}</title>" if tooltip else ""
    circ = f'<circle cx="{cx_:.1f}" cy="{cy_:.1f}" r="{r}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
    txt = text_block(cx_, cy_, lines, FONT_MAIN - 1, "#ffffff")
    return f'<g class="node">{title}{circ}{txt}</g>'


def end_node(cx_: float, cy_: float, label: str, fill: str, stroke: str, tooltip: str = "") -> str:
    return rect_node(cx_, cy_, END_W, END_H, label, fill, stroke, rx=8, tooltip=tooltip)


def notification_node(cx_: float, cy_: float, label: str, fill: str, stroke: str, tooltip: str = "") -> str:
    """Notification: pill-shaped rectangle."""
    return rect_node(cx_, cy_, NODE_W, NODE_H, label, fill, stroke, rx=20, tooltip=tooltip)


# ─── Arrow routing ────────────────────────────────────────────────────────────


def boundary_point(node: dict, lm: dict[str, int], toward_x: float, toward_y: float) -> tuple[float, float]:
    """Return point on node boundary pointing toward (toward_x, toward_y)."""
    ncx, ncy = cx(node, lm), cy(node, lm)
    dx = toward_x - ncx
    dy_ = toward_y - ncy
    length = math.hypot(dx, dy_) or 1.0
    dx /= length
    dy_ /= length  # unit direction

    ntype = node.get("type", "process")

    if ntype in ("process", "notification", "end"):
        hw, hh = (NODE_W / 2, NODE_H / 2) if ntype != "end" else (END_W / 2, END_H / 2)
        # Clamp to rectangle edge
        if abs(dx) * hh >= abs(dy_) * hw:
            t = hw / abs(dx) if abs(dx) > 0 else 1e9
        else:
            t = hh / abs(dy_) if abs(dy_) > 0 else 1e9
        return ncx + dx * t, ncy + dy_ * t

    if ntype == "decision":
        # Diamond: |dx_unit| / DIAMOND_W + |dy_unit| / DIAMOND_H == 1/t  →  t = 1/(|dx|/W + |dy|/H)
        denom = abs(dx) / DIAMOND_W + abs(dy_) / DIAMOND_H
        if denom < 1e-9:
            return ncx, ncy
        t = 1.0 / denom
        return ncx + dx * t, ncy + dy_ * t

    if ntype == "start":
        return ncx + dx * START_R, ncy + dy_ * START_R

    return ncx, ncy


def draw_arrow(
    sx: float, sy: float, tx: float, ty: float, color: str, label: str = "", style: str = "solid", outcome: str = ""
) -> str:
    """Cubic bezier arrow from (sx,sy) to (tx,ty).

    outcome: "yes" | "no" | "" — renders a colored YES/NO badge near source.
    """
    dash = 'stroke-dasharray="7,5"' if style == "dashed" else ""
    dx, dy_ = tx - sx, ty - sy

    # Control points: bend midway, curving around the midpoint
    if abs(dy_) < 20:
        # Nearly horizontal: straight with slight vertical bow
        mx = (sx + tx) / 2
        c1x, c1y = mx, sy
        c2x, c2y = mx, ty
    elif abs(dx) < 20:
        # Nearly vertical: straight with slight horizontal bow
        my = (sy + ty) / 2
        c1x, c1y = sx, my
        c2x, c2y = tx, my
    else:
        # General: simple S-curve through midpoint
        mx, my = (sx + tx) / 2, (sy + ty) / 2
        c1x, c1y = sx + dx * 0.4, sy
        c2x, c2y = tx - dx * 0.4, ty

    path_d = f"M {sx:.1f},{sy:.1f} C {c1x:.1f},{c1y:.1f} {c2x:.1f},{c2y:.1f} {tx:.1f},{ty:.1f}"

    # Arrowhead polygon
    angle = math.atan2(ty - c2y, tx - c2x)
    ah = ARROW_HEAD
    ax1 = tx - ah * math.cos(angle - 0.45)
    ay1 = ty - ah * math.sin(angle - 0.45)
    ax2 = tx - ah * math.cos(angle + 0.45)
    ay2 = ty - ah * math.sin(angle + 0.45)
    head = f'<polygon points="{tx:.1f},{ty:.1f} {ax1:.1f},{ay1:.1f} {ax2:.1f},{ay2:.1f}" fill="{color}"/>'

    path_el = f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="1.8" {dash}/>'

    # Edge label — placed at 20% from source so it stays near the decision diamond
    label_t = 0.20 if outcome else 0.50
    lx = sx + (tx - sx) * label_t + 6
    ly = sy + (ty - sy) * label_t - 4
    label_el = ""
    if label.strip():
        lines = label.strip().split("\n")
        spans = "".join(f'<tspan x="{lx:.1f}" y="{ly + i * 11:.1f}">{esc(ln)}</tspan>' for i, ln in enumerate(lines))
        label_el = (
            f'<text text-anchor="start" font-size="{FONT_EDGE}" '
            f'font-family="Inter,Arial,sans-serif" font-weight="600" '
            f'fill="{color}">{spans}</text>'
        )

    out = path_el + head + label_el

    # YES / NO badge — rendered as a pill right at the source exit point
    if outcome in ("yes", "no"):
        badge_fill = "#1a7a38" if outcome == "yes" else "#b03030"
        badge_text = "YES" if outcome == "yes" else "NO"
        bw = 28 if outcome == "yes" else 22
        # 15% along the edge from source boundary
        bx = sx + (tx - sx) * 0.08
        by = sy + (ty - sy) * 0.08
        out += (
            f'<rect x="{bx - bw / 2:.1f}" y="{by - 8:.1f}" '
            f'width="{bw:.1f}" height="16" rx="4" fill="{badge_fill}" '
            f'stroke="#ffffff" stroke-width="0.8"/>'
            f'<text x="{bx:.1f}" y="{by + 4.5:.1f}" text-anchor="middle" '
            f'font-size="9" font-weight="700" fill="#ffffff" '
            f'font-family="Inter,Arial,sans-serif">{badge_text}</text>'
        )

    return out


# ─── Main generator ───────────────────────────────────────────────────────────


def generate_svg(defn: dict) -> str:
    lanes: list[dict] = defn.get("swimlanes", [])  # noqa: qg-empty-fallback
    nodes: list[dict] = defn.get("nodes", [])  # noqa: qg-empty-fallback
    conns: list[dict] = defn.get("connections", [])  # noqa: qg-empty-fallback
    anns: list[dict] = defn.get("annotations", [])  # noqa: qg-empty-fallback
    meta: dict = defn.get("meta", {})  # noqa: qg-empty-fallback
    legend_def: dict = defn.get("legend", {})  # noqa: qg-empty-fallback

    lm = {lane["id"]: idx for idx, lane in enumerate(lanes)}
    nm = {n["id"]: n for n in nodes}

    # Canvas dimensions
    max_col = max((n.get("col", 0) for n in nodes), default=10)
    cw = int(LANE_HEADER_W + (max_col + 1.8) * COL_W)
    ch = int(TITLE_H + len(lanes) * LANE_H + LEGEND_H)

    parts: list[str] = []

    # ── SVG root ──
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cw} {ch}" width="{cw}" height="{ch}">')

    # ── Defs ──
    all_colors = {BRANCH_COLORS.get(n.get("branch", "both"), "#777") for n in nodes}
    all_colors |= {BRANCH_COLORS.get(c.get("branch", "both"), "#777") for c in conns}
    parts.append("<defs>")
    # sorted() → deterministic marker order (set iteration is non-deterministic across runs and
    # was the sole source of byte-churn that re-dirtied the tracked SVG every regen — item H).
    for col in sorted(all_colors):
        cid = col.lstrip("#")
        parts.append(
            f'<marker id="ah-{cid}" markerWidth="12" markerHeight="8" '
            f'refX="10" refY="4" orient="auto">'
            f'<polygon points="0 0,12 4,0 8" fill="{col}"/></marker>'
        )
    # Drop shadow
    parts.append(
        '<filter id="shadow" x="-5%" y="-5%" width="110%" height="120%">'
        '<feDropShadow dx="1" dy="2" stdDeviation="2" flood-opacity="0.12"/>'
        "</filter>"
    )
    parts.append("</defs>")

    # ── Background ──
    parts.append(f'<rect width="{cw}" height="{ch}" fill="#f4f6fa"/>')

    # ── Title bar ──
    title = esc(meta.get("title", "CI/CD Pipeline"))
    sub = esc(meta.get("subtitle", ""))
    ver = esc(meta.get("version", ""))
    regen = esc(meta.get("regenerate", ""))
    parts.append(
        f'<rect x="0" y="0" width="{cw}" height="{TITLE_H}" fill="#0f1729"/>'
        f'<text x="{LANE_HEADER_W + 12}" y="26" font-size="17" font-weight="700" '
        f'fill="#ffffff" font-family="Inter,Arial,sans-serif">{title}</text>'
        f'<text x="{LANE_HEADER_W + 12}" y="46" font-size="10.5" fill="#8899bb" '
        f'font-family="Inter,Arial,sans-serif">{sub}  —  {ver}  |  '
        f"Regenerate: {regen}</text>"
    )

    # ── Swimlane bands + labels ──
    for idx, lane in enumerate(lanes):
        yt = TITLE_H + idx * LANE_H
        bg = lane.get("color", "#f8f8f8")
        bdr = lane.get("border", "#cccccc")
        # Band
        parts.append(
            f'<rect x="{LANE_HEADER_W}" y="{yt}" '
            f'width="{cw - LANE_HEADER_W}" height="{LANE_H}" '
            f'fill="{bg}" stroke="{bdr}" stroke-width="0.6"/>'
        )
        # Label strip
        parts.append(f'<rect x="0" y="{yt}" width="{LANE_HEADER_W}" height="{LANE_H}" fill="{bdr}" opacity="0.28"/>')
        label_text = lane.get("label", "").replace("\n", " · ")
        lx = LANE_HEADER_W / 2
        ly = yt + LANE_H / 2
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" '
            f'font-size="{FONT_LANE}" font-weight="700" fill="#1a1a2e" '
            f'font-family="Inter,Arial,sans-serif" '
            f'transform="rotate(-90,{lx:.1f},{ly:.1f})">{esc(label_text)}</text>'
        )

    # ── Connections (drawn below nodes) ──
    for conn in conns:
        fid, tid = conn.get("from", ""), conn.get("to", "")
        if fid not in nm or tid not in nm:
            continue
        src, dst = nm[fid], nm[tid]
        tcx, tcy = cx(dst, lm), cy(dst, lm)
        scx, scy = cx(src, lm), cy(src, lm)
        # Boundary exit/entry
        sp = boundary_point(src, lm, tcx, tcy)
        ep = boundary_point(dst, lm, scx, scy)
        color = BRANCH_COLORS.get(conn.get("branch", "both"), "#777")
        lbl = conn.get("label", "")
        style = conn.get("style", "solid")
        outcome = conn.get("outcome", "")
        parts.append(draw_arrow(sp[0], sp[1], ep[0], ep[1], color, lbl, style, outcome))

    # ── Nodes (drawn above connections) ──
    for node in nodes:
        ncx, ncy = cx(node, lm), cy(node, lm)
        ntype = node.get("type", "process")
        branch = node.get("branch", "both")
        label = node.get("label", "")
        tooltip = node.get("tooltip", "")
        fill = BRANCH_FILL.get(branch, "#f0f0f0")
        stroke = BRANCH_COLORS.get(branch, "#777")
        dark = DARK_FILL.get(branch, "#444")

        if ntype == "start":
            parts.append(circle_node(ncx, ncy, START_R, label, dark, stroke, tooltip))
        elif ntype == "decision":
            parts.append(diamond_node(ncx, ncy, DIAMOND_W, DIAMOND_H, label, fill, stroke, tooltip))
        elif ntype == "notification":
            parts.append(notification_node(ncx, ncy, label, fill, stroke, tooltip))
        elif ntype == "end":
            parts.append(end_node(ncx, ncy, label, "#ffe8e8", "#c04040", tooltip))
        else:
            parts.append(rect_node(ncx, ncy, NODE_W, NODE_H, label, fill, stroke, tooltip=tooltip))

        # Actor attribution — small italic text above decision nodes showing WHO decides
        actor = node.get("actor", "")
        if actor:
            actor_lines = actor.split("\n")
            if ntype == "decision":
                # Above the diamond tip so it doesn't clash with exit arrows
                actor_y0 = ncy - DIAMOND_H - 4 - (len(actor_lines) - 1) * 10
            elif ntype == "start":
                actor_y0 = ncy - START_R - 4 - (len(actor_lines) - 1) * 10
            else:
                actor_y0 = ncy - NODE_H / 2 - 4 - (len(actor_lines) - 1) * 10
            for i, aln in enumerate(actor_lines):
                parts.append(
                    f'<text x="{ncx:.1f}" y="{actor_y0 + i * 10:.1f}" '
                    f'text-anchor="middle" font-size="8.5" '
                    f'fill="#334466" font-style="italic" '
                    f'font-family="Inter,Arial,sans-serif">{esc(aln)}</text>'
                )

    # ── Annotations ──
    for ann in anns:
        nid = ann.get("node", "")
        if nid not in nm:
            continue
        node = nm[nid]
        ncx_a = cx(node, lm)
        ncy_a = cy(node, lm)
        pos = ann.get("position", "below")
        ay = (ncy_a + NODE_H / 2 + 16) if pos == "below" else (ncy_a - NODE_H / 2 - 16)
        lines = ann.get("text", "").split("\n")
        for i, ln in enumerate(lines):
            parts.append(
                f'<text x="{ncx_a:.1f}" y="{ay + i * 11:.1f}" '
                f'text-anchor="middle" font-size="{FONT_ANN}" '
                f'fill="#555566" font-style="italic" '
                f'font-family="Inter,Arial,sans-serif">{esc(ln)}</text>'
            )

    # ── Legend bar ──
    ly_bar = TITLE_H + len(lanes) * LANE_H
    parts.append(f'<rect x="0" y="{ly_bar}" width="{cw}" height="{LEGEND_H}" fill="#0f1729"/>')
    legend_branches = legend_def.get("branches", [])  # noqa: qg-empty-fallback
    lx_cur = LANE_HEADER_W + 16
    parts.append(
        f'<text x="{lx_cur}" y="{ly_bar + 22}" font-size="10" '
        f'fill="#7788aa" font-family="Inter,Arial,sans-serif" font-weight="700">'
        f"LEGEND:</text>"
    )
    lx_cur += 72
    for br in legend_branches:
        bcolor = br.get("color", "#888")
        blabel = esc(br.get("label", ""))
        parts.append(
            f'<rect x="{lx_cur}" y="{ly_bar + 10}" width="16" height="16" '
            f'fill="{bcolor}" rx="3"/>'
            f'<text x="{lx_cur + 20}" y="{ly_bar + 22}" font-size="10.5" '
            f'fill="#e0e0f0" font-family="Inter,Arial,sans-serif">{blabel}</text>'
        )
        lx_cur += 160
    # Node type legend
    lx_cur += 40
    parts.append(
        f'<text x="{lx_cur}" y="{ly_bar + 22}" font-size="10" fill="#7788aa" '
        f'font-family="Inter,Arial,sans-serif" font-weight="700">NODE TYPES:</text>'
    )
    lx_cur += 90
    for ntype_label, shape_hint in [
        ("Start/trigger", "●"),
        ("Process", "▬"),
        ("Decision (if/else)", "◆"),
        ("Telegram alert", "⬭"),
        ("Terminal state", "▣"),
    ]:
        parts.append(
            f'<text x="{lx_cur}" y="{ly_bar + 22}" font-size="10.5" '
            f'fill="#ccccee" font-family="Inter,Arial,sans-serif">'
            f"{esc(shape_hint)} {esc(ntype_label)}</text>"
        )
        lx_cur += 150

    parts.append("</svg>")
    return "\n".join(parts)


def generate_html(svg: str, meta: dict) -> str:
    title = esc(meta.get("title", "CI/CD Pipeline"))
    sub = esc(meta.get("subtitle", ""))
    ver = esc(meta.get("version", ""))
    source = esc(meta.get("source", ""))
    regen = esc(meta.get("regenerate", ""))
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0a0d18;
      font-family: Inter, 'Segoe UI', Arial, sans-serif;
      color: #dde0f0;
    }}
    header {{
      padding: 14px 20px;
      background: #0f1729;
      border-bottom: 2px solid #1e2a4a;
      display: flex;
      align-items: baseline;
      gap: 16px;
    }}
    header h1 {{ font-size: 1.25rem; color: #fff; }}
    header .meta {{ font-size: 0.82rem; color: #6677aa; }}
    header code {{
      background: #1a2340;
      padding: 2px 7px;
      border-radius: 4px;
      font-size: 0.78rem;
      color: #7ec8e3;
    }}
    .wrap {{
      overflow: auto;
      padding: 20px;
      min-height: calc(100vh - 80px);
    }}
    .wrap svg {{
      display: block;
      border-radius: 8px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.6);
    }}
    .node {{ transition: opacity 0.15s; }}
    .node:hover {{ opacity: 0.82; cursor: pointer; }}
    footer {{
      padding: 10px 20px;
      background: #0f1729;
      border-top: 1px solid #1e2a4a;
      font-size: 0.76rem;
      color: #445566;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{title}</h1>
    <span class="meta">{sub} &mdash; v{ver}</span>
    <span class="meta">Source: <code>{source}</code></span>
    <span class="meta">Regenerate: <code>{regen}</code></span>
  </header>
  <div class="wrap">
{svg}
  </div>
  <footer>Hover any node for details &middot; Generated from <strong>{source}</strong></footer>
</body>
</html>
"""


def main() -> None:
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    yaml_path = repo_root / "docs" / "repo-management" / "cicd-pipeline-definition.yaml"
    svg_path = repo_root / "docs" / "repo-management" / "CI-CD-PIPELINE.svg"
    html_path = repo_root / "docs" / "repo-management" / "CI-CD-PIPELINE.html"

    if not yaml_path.exists():
        print(f"ERROR: {yaml_path} not found", file=sys.stderr)
        sys.exit(1)

    print(f"Reading {yaml_path.name}...")
    defn: dict[str, object] = cast(dict[str, object], yaml.safe_load(yaml_path.read_text()) or {})

    print("Generating SVG...")
    svg = generate_svg(defn)
    svg_path.write_text(svg)
    print(f"Written → {svg_path}")

    print("Generating HTML...")
    meta = cast(dict[str, object], defn.get("meta", {}))  # noqa: qg-empty-fallback
    html = generate_html(svg, meta)
    html_path.write_text(html)
    print(f"Written → {html_path}")

    n_nodes = len(cast(list[object], defn.get("nodes", [])))  # noqa: qg-empty-fallback
    n_conns = len(cast(list[object], defn.get("connections", [])))  # noqa: qg-empty-fallback
    n_lanes = len(cast(list[object], defn.get("swimlanes", [])))  # noqa: qg-empty-fallback
    print(f"Diagram: {n_lanes} lanes · {n_nodes} nodes · {n_conns} connections")
    print(f"SVG size: {svg_path.stat().st_size // 1024}KB")


if __name__ == "__main__":
    main()
