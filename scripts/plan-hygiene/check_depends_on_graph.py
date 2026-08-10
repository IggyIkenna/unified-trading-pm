#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate the plans `depends_on` DAG.

Why this exists (2026-07-15): `depends_on` was only ever SEEDED (fix_frontmatter.py adds
`depends_on: []` when missing) and never VALIDATED. Nothing checked the graph itself, so a
dependency CYCLE (A -> B -> A) or a self-dependency (A -> A) could sit in the corpus
indefinitely. That is not cosmetic: per CLAUDE.md, `depends_on` *gates archival*, so a cycle
means neither plan can ever be archived — a silent permanent stasis with no error anywhere.

HARD failures (exit 1):
  * a `depends_on` cycle among LIVE docs
  * a self-dependency

Advisory only (never fails the gate):
  * a `depends_on` naming a doc that resolves nowhere (live or archived)

Explicit NON-finding: `depends_on` pointing at an ARCHIVED plan is CORRECT — it means the
prerequisite is done and the dependent is unblocked. Bare slugs resolve against
plans/archive/. Do not flag it.

Usage:
    python3 scripts/plan-hygiene/check_depends_on_graph.py [--quiet]
    python3 scripts/plan-hygiene/check_depends_on_graph.py --only <path> [<path> ...]

``--only <paths>`` (2026-08-09, precommit migration): this ratchet previously had NO
precommit-time presence, only the full corpus-wide sweep — so a docs(plans) commit that
introduced a `depends_on` cycle/self-dep had zero enforcement at commit time, same
fast-path-blind-to-full-gate pattern as the other checks migrated this evening.

Unlike a single-file content check, a cycle can SPAN multiple files (A depends_on B,
B depends_on A, where only one of the two is in this commit's staged set) — scoping the
graph build itself to just the staged files would miss a cycle that only exists when
combined with the rest of the corpus's unchanged depends_on declarations. So `--only`
still builds the FULL corpus graph (cheap: local frontmatter reads only, no network,
~750 docs) exactly like the full-sweep mode, but reports a violation only if it
ORIGINATES from one of the staged files: a self-dep on a staged file, or a cycle where at
least one node in the cycle is a staged file. This is the blast-radius-safe shape (a
pre-existing cycle entirely among files this commit doesn't touch never blocks it) while
still catching "my edit introduced/is part of a cycle" — the actual growth signal. Since
a cycle is binary (present/absent, no per-file baseline-debt concept), there is no
HEAD-vs-current comparison needed here, unlike the growth-ratchet checks.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PM = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LIVE_DIRS = [
    os.path.join(PM, "plans", "active"),
    os.path.join(PM, "plans", "active", "issues"),
    os.path.join(PM, "plans", "epics"),
]
ARCHIVE_DIR = os.path.join(PM, "plans", "archive")
# Other legitimate resolution homes for a depends_on target. A prerequisite may be an audit
# result rather than a plan; those are real targets, not dangling refs.
OTHER_RESOLVABLE_DIRS = [os.path.join(PM, "plans", "audit")]


def _frontmatter_lines(path: str) -> list[str]:
    """Return the raw frontmatter lines (line-based; no regex backtracking)."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError:
        return []
    if not lines or lines[0].strip() != "---":
        return []
    out: list[str] = []
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        out.append(line)
    return []


def _field(fm_lines: list[str], key: str) -> str:
    """Raw value for `key`, joining a multi-line bracketed list into one string."""
    buf = ""
    depth = 0
    capturing = False
    for raw in fm_lines:
        line = raw.rstrip("\n")
        if not capturing and line.startswith(key + ":"):
            value = line.split(":", 1)[1].strip()
            depth = value.count("[") - value.count("]")
            if depth <= 0:
                return value
            buf, capturing = value, True
        elif capturing:
            buf += " " + line.strip()
            depth += line.count("[") - line.count("]")
            if depth <= 0:
                return buf
    return buf


def _slugs(value: str) -> list[str]:
    """Parse a depends_on value into bare slugs (drops paths, .md, inline comments)."""
    value = (value or "").strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    out: list[str] = []
    for part in value.split(","):
        part = part.split("#")[0].strip().strip("'\"")
        if not part:
            continue
        part = os.path.basename(part)
        if part.endswith(".md"):
            part = part[:-3]
        out.append(part)
    return out


def _collect() -> tuple[dict[str, list[str]], set[str], set[str]]:
    deps: dict[str, list[str]] = {}
    live: set[str] = set()
    for directory in LIVE_DIRS:
        if not os.path.isdir(directory):
            continue
        for name in sorted(os.listdir(directory)):
            if not name.endswith(".md"):
                continue
            slug = name[:-3]
            live.add(slug)
            deps[slug] = _slugs(_field(_frontmatter_lines(os.path.join(directory, name)), "depends_on"))
    archived: set[str] = set()
    for base in [ARCHIVE_DIR, *OTHER_RESOLVABLE_DIRS]:
        for _root, _dirs, files in os.walk(base):
            for name in files:
                if name.endswith(".md"):
                    archived.add(name[:-3])
    return deps, live, archived


def _find_violations(deps: dict[str, list[str]], live: set[str]) -> tuple[list[str], list[list[str]]]:
    """Corpus-wide self-deps + cycles over the LIVE subgraph. Shared by full-sweep mode and
    `--only` mode so the two can never define "a violation" differently — `--only` filters
    this SAME unrestricted result down to what touches a staged file, it does not recompute
    the graph differently."""
    self_deps = sorted(s for s, ds in deps.items() if s in ds)

    # iterative DFS over the LIVE subgraph (recursion would risk a deep-corpus stack blowout)
    cycles: list[list[str]] = []
    color: dict[str, int] = {}
    for root in sorted(live):
        if color.get(root, 0) != 0:
            continue
        stack: list[tuple[str, int]] = [(root, 0)]
        path: list[str] = [root]
        color[root] = 1
        while stack:
            node, idx = stack[-1]
            children = [d for d in deps.get(node, []) if d in live and d != node]
            if idx < len(children):
                stack[-1] = (node, idx + 1)
                nxt = children[idx]
                if color.get(nxt, 0) == 1:  # back-edge => cycle
                    if nxt in path:
                        cyc = [*path[path.index(nxt) :], nxt]
                        if cyc not in cycles:
                            cycles.append(cyc)
                elif color.get(nxt, 0) == 0:
                    color[nxt] = 1
                    stack.append((nxt, 0))
                    path.append(nxt)
            else:
                color[node] = 2
                stack.pop()
                if path:
                    path.pop()
    return self_deps, cycles


def _staged_slugs(paths: list[str]) -> set[str]:
    return {Path(p).stem for p in paths}


def _run_only(paths: list[str], quiet: bool) -> int:
    deps, live, _archived = _collect()
    self_deps, cycles = _find_violations(deps, live)
    staged = _staged_slugs(paths)

    flagged_self = [s for s in self_deps if s in staged]
    flagged_cycles = [cyc for cyc in cycles if staged & set(cyc)]

    hard = len(flagged_self) + len(flagged_cycles)
    if hard:
        print(f"❌ check_depends_on_graph (--only): {hard} hard violation(s) touching a staged file:")
        for cyc in flagged_cycles:
            print("   CYCLE: " + " -> ".join(cyc))
            print("      (depends_on gates archival — neither plan can ever close)")
        for slug in flagged_self:
            print(f"   SELF-DEPENDENCY: {slug} depends_on itself")
        print("   Remedy: break the cycle — drop the weaker depends_on edge, or merge the plans.")
        return 1

    if not quiet:
        print(f"✅ check_depends_on_graph (--only): 0 cycle/self-dep touching {len(staged)} staged file(s)")
    return 0


def main() -> int:
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        return _run_only(sys.argv[idx + 1 :], "--quiet" in sys.argv)

    parser = argparse.ArgumentParser()
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    deps, live, archived = _collect()
    self_deps, cycles = _find_violations(deps, live)

    unresolved = sorted({(s, d) for s, ds in deps.items() for d in ds if d not in live and d not in archived})

    hard = len(cycles) + len(self_deps)
    if hard:
        print(f"❌ check_depends_on_graph: {hard} hard violation(s):")
        for cyc in cycles:
            print("   CYCLE: " + " -> ".join(cyc))
            print("      (depends_on gates archival — neither plan can ever close)")
        for slug in self_deps:
            print(f"   SELF-DEPENDENCY: {slug} depends_on itself")
        print("   Remedy: break the cycle — drop the weaker depends_on edge, or merge the plans.")
        return 1

    if unresolved and not args.quiet:
        print(f"⚠️  check_depends_on_graph: {len(unresolved)} depends_on ref(s) resolve nowhere (advisory):")
        for slug, dep in unresolved[:10]:
            print(f"   {slug} -> {dep} (not in live plans nor plans/archive/)")

    if not args.quiet:
        print(
            f"✅ check_depends_on_graph: {len(deps)} docs, 0 cycles, 0 self-deps "
            f"({len(unresolved)} unresolved refs, advisory)"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
