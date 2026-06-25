#!/usr/bin/env python3
"""gen_doc_index — the L0 map generator (W4 of agent_operating_framework_master).

Builds an `llms.txt`-style index FROM frontmatter: one greppable line per doc with its title,
summary, and facets, grouped by doc_type and deterministically sorted (no timestamps,
repo-root-relative paths) so it is byte-identical across hosts. The output is a CONSUMER-SIDE
LOCAL, gitignored artifact (C2): every host regenerates it from the docs it has, so there is no
multi-writer git contention. Regen is cheap + idempotent — wire it into the FF-pull cron
(`--stale-check` only rewrites when the content changed).

Agents read THIS first (L0) to route, then open the one doc they need (L3) — "retrieve less but
right". Reuses docspec for frontmatter parsing + doc_type detection + exemptions.

# Epic: agent_operating_framework_master
# Lifecycle: permanent
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import docspec
import yaml
from docspec import doc_type_for_path, is_exempt, parse_frontmatter

# doc_type -> the facet keys worth surfacing on its index line (beyond the universal ones)
_FACET_ORDER = ["asset_group", "stage", "repos", "scope", "status", "nature", "tags"]
_PER_TYPE_FACETS = {
    "plan": ["parent_epic", "assigned_vm", "priority"],
    "epic": ["assigned_vm", "tier", "priority"],
    "issue": ["parent_epic", "priority"],
    "audit-result": ["parent_epic", "severity"],
    "audit-instruction": ["parent_epic", "tier"],
    "codex-ssot": ["authoritative_for", "owner"],
    "codex-runbook": ["owner", "cadence"],
    "agent-role": ["role"],
}

# the doc roots to walk (PM corpus + the cross-repo agent-role boot prompts)
_ROOTS: list[tuple[str, str]] = [
    ("plans/active", "*.md"),
    ("plans/epics", "*.md"),
    ("plans/active/issues", "*.md"),
    ("plans/audit/results", "**/*.md"),
    ("plans/audit/instructions", "**/*.md"),
    ("codex", "**/*.md"),
]


def _fmt_val(v: object) -> str:
    if isinstance(v, list):
        return ",".join(str(x) for x in v)
    return str(v)


def _doc_entry(path: Path, pm_root: Path) -> tuple[str, str] | None:
    """Return (doc_type, one-line index entry) for a doc, or None if exempt/untyped."""
    sp = str(path)
    if is_exempt(sp):
        return None
    dt = doc_type_for_path(sp)
    if dt is None or dt == "cursor-rule":
        return None
    text = path.read_text(errors="replace")
    try:
        fm, body = parse_frontmatter(text)
    except yaml.YAMLError:
        fm, body = None, text  # malformed frontmatter -> minimal entry, never crash the index
    fm = fm or {}
    # title: frontmatter, else first H1, else stem
    title = fm.get("title") or fm.get("name")
    if not title:
        title = next((ln[2:].strip() for ln in body.splitlines() if ln.startswith("# ")), path.stem)
    summary = (fm.get("summary") or "").strip() if isinstance(fm.get("summary"), str) else ""
    rel = _rel(path, pm_root)
    facets = []
    for key in _FACET_ORDER + _PER_TYPE_FACETS.get(dt, []):
        val = fm.get(key)
        if val not in (None, "", [], {}):
            facets.append(f"{key}={_fmt_val(val)}")
    facet_str = f"  ·  [{' '.join(facets)}]" if facets else ""
    summ = f" — {summary}" if summary else " — (no summary yet)"
    return dt, f"- [{title}]({rel}){summ}{facet_str}"


def _rel(path: Path, pm_root: Path) -> str:
    """Repo-root-relative path (PM-relative; cross-repo docs keep a `../` prefix) — host-stable."""
    try:
        return str(path.resolve().relative_to(pm_root))
    except ValueError:
        return str(path.resolve().relative_to(pm_root.parent).as_posix()).replace("../", "")


def build_index(pm_root: Path) -> str:
    ws = pm_root.parent
    entries: dict[str, list[str]] = {}
    seen: set[Path] = set()
    roots = [pm_root / r for r, _ in _ROOTS] + [ws / "agent-orchestrator/agents"]
    globs = [g for _, g in _ROOTS] + ["*.md"]
    for root, glob in zip(roots, globs, strict=True):
        if not root.is_dir():
            continue
        for path in root.glob(glob):
            rp = path.resolve()
            if rp in seen or not path.is_file():
                continue
            seen.add(rp)
            res = _doc_entry(path, pm_root)
            if res is not None:
                entries.setdefault(res[0], []).append(res[1])
    lines = [
        "# UTS documentation index (L0 map — generated)",
        "",
        "> Generated from frontmatter by `scripts/docs/gen_doc_index.py`. Greppable: one line per doc with its",
        "> title, summary, and facets. Route here (L0), then open the one doc you need (L3). Do NOT edit by hand —",
        "> regenerate. Gitignored (consumer-side local; no git contention).",
        "",
    ]
    for dt in sorted(entries):
        lines.append(f"## {dt} ({len(entries[dt])})")
        lines.append("")
        lines.extend(sorted(entries[dt]))
        lines.append("")
    return "\n".join(lines) + "\n"


def _pm_root() -> Path:
    return docspec._pm_root()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--out",
        default=None,
        help="output path (default: <pm_root>/DOC_INDEX.generated.md — gitignored)",
    )
    ap.add_argument(
        "--stale-check",
        action="store_true",
        help="only rewrite if the content changed (for the FF-cron hook); exit 0 always",
    )
    args = ap.parse_args(argv)
    pm_root = _pm_root()
    out = Path(args.out) if args.out else pm_root / "DOC_INDEX.generated.md"
    content = build_index(pm_root)
    if args.stale_check and out.exists() and out.read_text() == content:
        print(f"doc-index fresh: {out}")
        return 0
    out.write_text(content)
    n = content.count("\n- [")
    print(f"doc-index regenerated: {out} ({n} docs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
