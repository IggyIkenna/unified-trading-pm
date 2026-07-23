#!/usr/bin/env python3
"""gen_doc_graph — interactive 3D doc-graph render of the L0 corpus (W4 rendered-view, local variant).

Builds a SELF-CONTAINED `DOC_GRAPH.generated.html` (gitignored, consumer-side local — same C2
decision as `DOC_INDEX.generated.md`): every live doc is a node (sized by in-degree, colored by
tree), every `related:` / `referenced_by:` frontmatter link is an edge, rendered as a WebGL
force-directed 3D graph (vendored `3d-force-graph`) with facet filters (doc_type / tree /
asset_group / status), search, and a click-through side panel (summary + neighbors + copy-path).
Open the file in any browser — no server. Serving the same file centrally (AO dashboard static
route) is the remaining thin step of the W4 rendered view.

The renderer lib is fetched ONCE per host into a gitignored vendor cache (checked-in blobs would
trip the large-file hook), then inlined so the artifact works offline.

# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path

import docspec
import yaml
from docspec import doc_type_for_path, is_exempt, parse_frontmatter
from gen_doc_index import ROOTS

_EXCLUDED_PREFIX = "plans/archive/"
_LIB_URL = "https://unpkg.com/3d-force-graph@1.77.0/dist/3d-force-graph.min.js"
_LIB_CACHE = Path(__file__).resolve().parent / "vendor-cache" / "3d-force-graph.min.js"
_OUT_NAME = "DOC_GRAPH.generated.html"
_SUMMARY_CAP = 400


def _rel(path: Path, pm_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(pm_root))
    except ValueError:
        return str(path.resolve().relative_to(pm_root.parent).as_posix()).replace("../", "")


def _tree_of(rel: str) -> str:
    parts = rel.split("/")
    if parts[0] == "codex" and len(parts) > 2:
        return "/".join(parts[:2])
    if parts[0] == "plans" and len(parts) > 2:
        return "/".join(parts[:2])
    return parts[0]


def _resolve_link(raw: object, src: Path, pm_root: Path) -> str | None:
    if not isinstance(raw, str):
        return None
    t = raw.strip().strip("'\"")
    if not t or t.startswith("http") or "*" in t:
        return None
    t = t.split(" ")[0]  # tolerate legacy "path Section 8.B" values
    # Leading-slash, PM-repo-root-relative (operator ruling 2026-07-23 — /plans/..., /codex/...)
    # MUST be joined against pm_root with the slash stripped first: `Path(base) / "/x"` discards
    # `base` entirely (pathlib treats an absolute-shaped RHS as a full replacement, not a join),
    # which would silently resolve every migrated link to the filesystem root instead of the repo.
    candidates = (pm_root / t.lstrip("/"),) if t.startswith("/") else (src.parent / t, pm_root / t)
    for cand in candidates:
        try:
            r = cand.resolve()
            if r.is_file() and r.is_relative_to(pm_root):
                return str(r.relative_to(pm_root))
        except OSError:
            continue
    return None


def _walk(pm_root: Path) -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for rel_root, glob in ROOTS:
        root = pm_root / rel_root
        if not root.is_dir():
            continue
        for path in sorted(root.glob(glob)):
            rp = path.resolve()
            if rp in seen or not path.is_file():
                continue
            if _rel(path, pm_root).startswith(_EXCLUDED_PREFIX):
                continue
            seen.add(rp)
            out.append(path)
    return out


def build_graph(pm_root: Path) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    nodes: dict[str, dict[str, object]] = {}
    fm_links: dict[str, set[str]] = {}
    for path in _walk(pm_root):
        if is_exempt(str(path)):
            continue
        dt = doc_type_for_path(str(path))
        if dt is None:
            continue
        try:
            fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError):
            continue
        if not isinstance(fm, dict):
            continue
        rel = _rel(path, pm_root)
        summary = str(fm.get("summary") or "").replace("\n", " ").strip()
        if len(summary) > _SUMMARY_CAP:
            summary = summary[: _SUMMARY_CAP - 1] + "…"
        nodes[rel] = {
            "id": rel,
            "t": str(fm.get("title") or path.stem),
            "s": summary,
            "dt": dt,
            "tree": _tree_of(rel),
            "ag": fm.get("asset_group") or [],
            "st": str(fm.get("status") or ""),
            "tags": fm.get("tags") or [],
        }
        targets: set[str] = set()
        for key in ("related", "referenced_by"):
            val = fm.get(key)
            if isinstance(val, list):
                for entry in val:
                    resolved = _resolve_link(entry, path, pm_root)
                    if resolved:
                        targets.add(resolved)
        fm_links[rel] = targets

    edges: list[dict[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()
    indeg: Counter[str] = Counter()
    for src, targets in fm_links.items():
        for dst in targets:
            if dst not in nodes or dst == src:
                continue
            pair = (min(src, dst), max(src, dst))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            edges.append({"source": src, "target": dst})
            indeg[dst] += 1
            indeg[src] += 1
    for rel, node in nodes.items():
        node["deg"] = indeg[rel]
    return list(nodes.values()), edges


def _lib_js(timeout: int = 60) -> str:
    if not _LIB_CACHE.is_file():
        _LIB_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(_LIB_URL, timeout=timeout) as resp:  # nosec B310 — hardcoded unpkg.com https URL, not user input
            _LIB_CACHE.write_bytes(resp.read())
    return _LIB_CACHE.read_text(encoding="utf-8")


_TEMPLATE = Path(__file__).resolve().parent / "doc_graph_template.html"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Generate the interactive 3D doc-graph HTML (gitignored artifact).")
    ap.add_argument("--out", default=None, help="output path (default: <pm-root>/DOC_GRAPH.generated.html)")
    args = ap.parse_args(argv)
    pm_root = docspec._pm_root()
    nodes, edges = build_graph(pm_root)
    data = json.dumps({"nodes": nodes, "links": edges}, separators=(",", ":"), sort_keys=True)
    html = _TEMPLATE.read_text(encoding="utf-8").replace("__LIB__", _lib_js()).replace("__DATA__", data)
    out = Path(args.out) if args.out else pm_root / _OUT_NAME
    out.write_text(html, encoding="utf-8")
    isolates = sum(1 for n in nodes if not n["deg"])
    print(f"doc-graph generated: {out} ({len(nodes)} nodes, {len(edges)} edges, {isolates} unlinked)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
