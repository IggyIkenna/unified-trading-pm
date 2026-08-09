#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
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
import os
import sys
import tempfile
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

# The doc roots to walk — PM-repo LIVE trees ONLY (operator decision 2026-07-04):
#   - agents/*.md (the agent-role charters) — indexed as a PM-repo live tree since 2026-07-16,
#     after the charters moved into this repo (the former cross-repo agent-orchestrator/agents
#     root is gone). Still NO other repos — cross-repo coverage is a future task, rolled out
#     deliberately, not one repo at a time here.
#   - NO plans/archive — EVER, even after the archive frontmatter backfill lands. Archived
#     plans/issues are closed records: indexing them grows the L0 map without routing value.
#     Agents needing history take the costlier grep-the-archive path, which is rare enough
#     that keeping the hot index small wins.
_ROOTS: list[tuple[str, str]] = [
    ("plans/active", "*.md"),
    ("plans/epics", "*.md"),
    ("plans/active/issues", "*.md"),
    ("plans/audit/results", "**/*.md"),
    ("plans/audit/instructions", "**/*.md"),
    ("codex", "**/*.md"),
    ("agents", "*.md"),
]
_EXCLUDED_PREFIX = "plans/archive/"  # safety net if a future root glob ever reaches into it
ROOTS = _ROOTS  # public alias — gen_doc_graph.py walks the same corpus (keep in lockstep)


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
    entries: dict[str, list[str]] = {}
    seen: set[Path] = set()
    roots = [pm_root / r for r, _ in _ROOTS]
    globs = [g for _, g in _ROOTS]
    for root, glob in zip(roots, globs, strict=True):
        if not root.is_dir():
            continue
        for path in root.glob(glob):
            rp = path.resolve()
            if rp in seen or not path.is_file():
                continue
            if _rel(path, pm_root).startswith(_EXCLUDED_PREFIX):
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


def _atomic_write_text(out: Path, content: str) -> None:
    """Write `content` to `out` atomically so no reader or racing writer ever sees a partial index.

    The write is truncate-then-write when done via `Path.write_text`, which leaves a window where a
    concurrent reader (an agent grepping the L0 map) reads a truncated file, or two concurrent writers
    (the FF-pull cron regenerating this per-clone file at the same instant the on-demand
    `refresh-doc-index.sh` wrapper does) interleave into a corrupt one. Instead: write to a
    uniquely-named temp file in the SAME directory (a same-filesystem sibling is required for the
    rename to be atomic), fsync it durable, then `os.replace()` it over `out` — a single atomic
    rename syscall on POSIX. The generator is deterministic + per-host, so racing writers emit
    byte-identical content; whichever rename lands last, `out` is always a complete, valid index and
    a reader observes either the old or the new file, never a truncation.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    # mkstemp guarantees a unique name, so two concurrent writers never share a temp file. The
    # leading-dot + out.name prefix makes any crash-leftover temp obvious and gitignore-matchable.
    fd, tmp_name = tempfile.mkstemp(dir=str(out.parent), prefix=f".{out.name}.", suffix=".tmp")
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, out)
    except BaseException:  # noqa: broad-except — deliberately the widest catch (incl.
        # KeyboardInterrupt/SystemExit) to guarantee the temp-file cleanup always runs; always re-raises
        tmp.unlink(missing_ok=True)
        raise


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
    _atomic_write_text(out, content)
    n = content.count("\n- [")
    print(f"doc-index regenerated: {out} ({n} docs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
