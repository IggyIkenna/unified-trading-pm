#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Check that every single-asset-group plan/issue doc has a findable path to (or from)
its AG's consolidated closeout plan — the mechanism that stops a finding from becoming
a silently orphaned doc nothing will ever pick up (operator request 2026-07-25, prompted
by the /ag-closeout-audit skill's own "how many docs are orphaned" question needing a
standing gate, not just a periodic audit).

`asset_group` is already a REQUIRED, already-populated frontmatter field (docspec.py's
ASSET_GROUP enum; see check_frontmatter_schema.py) and already supports multi-value lists
— this script does not add a new field, it adds a new CONSEQUENCE for the existing one:

- A doc whose `asset_group` is a SINGLE COVERED value must have a findable path to that
  tranche's `<prefix>_consolidated_closeout_*.md` family (the base closeout doc + its
  discovered companions: `_aggregated_sources_*`, `_history_*`, `_audit_*` — discovered by
  filename glob, never hand-hardcoded per tranche, so a new companion doc is picked up
  automatically the moment it exists). COVERED = every real `asset_group` enum value except
  `meta` (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infrastructure/ui) — the
  2026-07-27 schema expansion (`unified-trading-pm@a97bc7bed`) made `ao`/`ci`/`infrastructure`
  real dedicated enum values with their own closeout families, not generic exemption
  markers, so treating them as exempt (the 2026-07-25 original design) was stale; see
  `ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`. Two tranches' filename
  PREFIX differs from their enum value (`cross-cutting` -> `cross_cutting_`, `infrastructure`
  -> `infra_`) — an explicit mapping, not a `.replace("-", "_")` transform (that alone would
  still miss `infra_`).
- A doc whose `asset_group` has MULTIPLE values, or is `meta` (never had its own tranche), is
  EXEMPT by construction.
- The closeout-family docs themselves are self-exempt (a doc cannot orphan itself).
- A covered tranche's closeout family can itself be ARCHIVED (e.g. `ao`, `ci` — both
  consolidated-closeout docs moved to `plans/archive/`) and is still a valid link TARGET; the
  family search spans `plans/active` + `plans/archive`. Only orphan CANDIDATES are restricted
  to `plans/active` (archived docs can never be live orphans). A tranche whose family
  resolves to genuinely ZERO docs anywhere prints a loud UNENFORCED warning on every run
  (never a silent no-op `continue`) — a family of zero must never read as "nothing to check".

TWO signals count as "findable", checked together because a same-day investigation
(2026-07-25) found real docs missed by either signal alone:
1. GRAPH REACHABILITY — an undirected BFS (max 3 hops) over every doc's `related:`
   frontmatter edges, resolved to real files. Most 2026-07-24/07-25 docs link BACKWARD
   to the closeout in their own `related:` even when the closeout's static text hasn't
   caught up to name them forward yet — this signal catches that direction.
2. BODY-TEXT MENTION — the doc's filename stem appears anywhere in the closeout family's
   own body text (a digest table, a "target:" citation, a Progress Log entry). This
   catches the forward direction for docs the closeout names but that never formally
   `related:`-linked back.

A doc failing BOTH signals is a genuine orphan candidate.

SHRINKING ratchet (same shape as check_reference_paths.py / check_line_caps.sh) — NOT
zero-tolerance from day 1. The 2026-07-25 investigation found the true "cold" orphan
count (no path back, either signal) is small (single digits to low teens) against a
219-doc single-AG population, but confirming and fixing each one is real per-doc
triage, not a mechanical fix — the baseline tolerates today's count, a live count
EXCEEDING baseline means a NEW doc landed with no path back to its AG's closeout, which
IS mechanically wrong (the fix is always "add a related: link or a closeout-doc
mention", never "raise the baseline").

Usage:
  python3 scripts/plan-hygiene/check_ag_closeout_linkage.py [--quiet] [--update-baseline]
Exit 0 if the orphan count is <= baseline. NEVER hand-raise a baseline entry.
"""

from __future__ import annotations

import sys
from collections import deque
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "docs"))
import docspec

PM_DIR = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).resolve().parent / "ag_closeout_linkage_baseline.yaml"

# Every real asset_group enum value except `meta`, which never had its own tranche (see
# module docstring). Sorted for deterministic iteration/printing order.
COVERED_ASSET_GROUPS = tuple(sorted(docspec.ASSET_GROUP - {"meta"}))
# Filename PREFIX differs from the enum value for two tranches — an explicit mapping, never
# a `.replace("-", "_")` transform (that alone would still miss `infra_`).
_CLOSEOUT_FILENAME_PREFIX = {"cross-cutting": "cross_cutting", "infrastructure": "infra"}
MAX_HOPS = 3

TARGET_DIRS = ("plans/active", "plans/active/issues")
# Where a closeout family doc can physically live — broader than TARGET_DIRS, since an
# archived closeout doc (ao/ci today) is still a valid link target, just never an orphan
# candidate itself.
CLOSEOUT_SEARCH_DIRS = ("plans/active", "plans/archive")


def target_files() -> list[Path]:
    files: list[Path] = []
    for rel in TARGET_DIRS:
        base = PM_DIR / rel
        if not base.is_dir():
            continue
        for p in sorted(base.glob("*.md")):
            if not docspec.is_exempt(str(p.relative_to(PM_DIR))):
                files.append(p)
    return files


def resolve_related_entry(entry: str, from_path: Path) -> Path | None:
    """Best-effort resolution of a related: entry to a real file — leading-slash
    /plans/.../codex/... form first (the convention), then a same-basename search
    across the corpus for a legacy bare-slug/filename entry."""
    entry = entry.strip()
    if not entry:
        return None
    if entry.startswith("/"):
        candidate = PM_DIR / entry.lstrip("/")
        return candidate if candidate.is_file() else None
    if entry.endswith(".md"):
        candidate = (from_path.parent / entry).resolve()
        if candidate.is_file():
            return candidate
        for hit in PM_DIR.rglob(Path(entry).name):
            if hit.is_file():
                return hit
        return None
    # Bare slug (parent_epic-style, no extension) — try a basename match under plans/.
    for hit in (PM_DIR / "plans").rglob(f"{entry}.md"):
        return hit
    return None


def build_related_graph(
    all_docs: dict[Path, dict], extra_nodes: frozenset[Path] = frozenset()
) -> dict[Path, set[Path]]:
    """Undirected adjacency from every doc's related: list, resolved to real files.

    `extra_nodes` seeds additional graph nodes (with no outgoing edges of their own) BEFORE
    edge resolution runs, so a `related:` entry that resolves to one of them (e.g. an active
    doc linking to an ARCHIVED closeout family doc) is still recorded as an edge — the target
    membership check below (`target in graph`) would otherwise silently drop it.
    """
    graph: dict[Path, set[Path]] = {p: set() for p in (*all_docs, *extra_nodes)}
    for path, fm in all_docs.items():
        for entry in docspec._as_list(fm.get("related")):
            if not isinstance(entry, str):
                continue
            target = resolve_related_entry(entry, path)
            if target is not None and target in graph:
                graph[path].add(target)
                graph[target].add(path)
    return graph


def bfs_reaches(graph: dict[Path, set[Path]], start: Path, targets: set[Path], max_hops: int) -> bool:
    if start in targets:
        return True
    seen = {start}
    frontier = deque([(start, 0)])
    while frontier:
        node, depth = frontier.popleft()
        if depth >= max_hops:
            continue
        for neighbor in graph.get(node, ()):
            if neighbor in targets:
                return True
            if neighbor not in seen:
                seen.add(neighbor)
                frontier.append((neighbor, depth + 1))
    return False


def closeout_search_paths() -> list[Path]:
    """Every candidate closeout-family filename across the corpus — `plans/active` AND
    `plans/archive`, since a tranche's own closeout family can itself be archived (ao, ci
    today: both consolidated-closeout docs moved to `plans/archive/2026_07/`) while its
    members still need gating. Deliberately broader than `target_files()`: closeout docs are
    valid link TARGETS even when archived; only active docs are ever orphan CANDIDATES."""
    paths: list[Path] = []
    for rel in CLOSEOUT_SEARCH_DIRS:
        base = PM_DIR / rel
        if base.is_dir():
            paths.extend(sorted(base.rglob("*.md")))
    return paths


def closeout_family_for(ag: str, search_paths: list[Path]) -> set[Path]:
    """Discover the tranche's closeout-family docs by filename glob — never hand-hardcoded,
    so a new companion (_aggregated_sources_/_history_/_audit_) is picked up the moment
    it exists."""
    prefix = f"{_CLOSEOUT_FILENAME_PREFIX.get(ag, ag)}_consolidated_"
    return {p for p in search_paths if p.name.startswith(prefix)}


def mentions_stem(text: str, stem: str) -> bool:
    return stem in text


def main() -> int:
    quiet = "--quiet" in sys.argv
    update = "--update-baseline" in sys.argv

    files = target_files()
    all_docs: dict[Path, dict] = {}
    all_bodies: dict[Path, str] = {}
    for p in files:
        text = p.read_text(encoding="utf-8")
        fm, body = docspec.parse_frontmatter(text)
        if fm is None:
            continue
        all_docs[p] = fm
        all_bodies[p] = body

    search_paths = closeout_search_paths()
    closeout_family: dict[str, set[Path]] = {ag: closeout_family_for(ag, search_paths) for ag in COVERED_ASSET_GROUPS}

    empty_families = sorted(ag for ag, fam in closeout_family.items() if not fam)
    if empty_families:
        # LOUD by design, printed unconditionally (even under --quiet, run_hygiene_sweep.sh's
        # invocation mode) — a family of zero must never read as "nothing to check" for that
        # tranche. See closeout_search_paths()'s docstring for why archived-only families
        # (ao/ci today) are still expected to resolve non-empty here.
        print(
            f"⚠️  check_ag_closeout_linkage: EMPTY closeout family (UNENFORCED): {', '.join(empty_families)}",
            file=sys.stderr,
        )

    closeout_targets = frozenset(p for fam in closeout_family.values() for p in fam)
    graph = build_related_graph(all_docs, extra_nodes=closeout_targets)

    closeout_body_blob: dict[str, str] = {}
    for ag, fam in closeout_family.items():
        bodies: list[str] = []
        for p in fam:
            body = all_bodies.get(p)
            if body is None:
                # archived closeout doc — not in the active-only all_docs/all_bodies scan.
                try:
                    _, body = docspec.parse_frontmatter(p.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError):
                    body = None
            bodies.append(body or "")
        closeout_body_blob[ag] = "\n".join(bodies)

    violations: list[str] = []
    for path, fm in all_docs.items():
        ag_values = [v for v in docspec._as_list(fm.get("asset_group")) if isinstance(v, str)]
        if len(ag_values) != 1 or ag_values[0] not in COVERED_ASSET_GROUPS:
            continue
        ag = ag_values[0]
        family = closeout_family[ag]
        if not family or path in family:
            continue  # no closeout doc yet for this AG, or this doc IS the closeout family

        if bfs_reaches(graph, path, family, MAX_HOPS):
            continue
        if mentions_stem(closeout_body_blob[ag], path.stem):
            continue

        relpath = path.relative_to(PM_DIR).as_posix()
        violations.append(f"{relpath}: asset_group=[{ag}] has no path (graph or mention) to its closeout family")

    baseline = load_baseline()
    n = len(violations)
    ok = n <= baseline

    if not quiet:
        print(f"AG-closeout linkage check ({len(all_docs)} docs scanned, {len(files)} candidate files):")
        print()
        for v in sorted(violations):
            print(f"  ORPHAN  {v}")
        print()

    print(f"{'✅' if ok else '❌'} check_ag_closeout_linkage: {n} orphan(s) (baseline {baseline})")

    if update:
        write_baseline(n, baseline)
        print(f"Baseline updated: {min(n, baseline or n)}")

    return 0 if ok else 1


def load_baseline() -> int:
    if not BASELINE_PATH.exists():
        return 0
    raw = yaml.safe_load(BASELINE_PATH.read_text(encoding="utf-8")) or {}
    return int(raw.get("orphan_count", 0))


def write_baseline(n: int, existing: int) -> None:
    new_count = min(n, existing) if existing else n
    BASELINE_PATH.write_text(
        "# Baseline for check_ag_closeout_linkage.py — every single-asset-group plan/issue\n"
        "# doc must have a findable path to its AG's consolidated closeout plan (operator\n"
        "# request 2026-07-25).\n"
        "#\n"
        "# This is a SHRINKING ratchet. orphan_count is the number of pre-existing orphans\n"
        "# the gate tolerates. A live count EXCEEDING this fails the check — a NEW doc\n"
        "# landed with no path back to its AG's closeout, fix it (add a related: link or a\n"
        "# closeout-doc mention), don't raise the number. LOWER it (re-run\n"
        "# --update-baseline) the moment orphans get fixed. NEVER hand-raise it.\n"
        f"orphan_count: {new_count}\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
