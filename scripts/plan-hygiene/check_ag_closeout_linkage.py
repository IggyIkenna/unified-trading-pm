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

- A doc whose `asset_group` is a SINGLE real AG value (cefi/defi/tradfi/prediction/sports)
  must have a findable path to that AG's `<ag>_consolidated_closeout_*.md` family
  (the base closeout doc + its discovered companions: `_aggregated_sources_*`,
  `_history_*`, `_audit_*` — discovered by filename glob, never hand-hardcoded per AG, so
  a new companion doc is picked up automatically the moment it exists).
- A doc whose `asset_group` has MULTIPLE values, or is `cross-cutting`/`meta`/
  `infrastructure`, is EXEMPT by construction — that is exactly what those values already
  signal (this is a consequence of the existing tag, not a new one).
- The closeout-family docs themselves are self-exempt (a doc cannot orphan itself).

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

REAL_AGS = ("cefi", "defi", "tradfi", "prediction", "sports")
MAX_HOPS = 3

TARGET_DIRS = ("plans/active", "plans/active/issues")


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


def build_related_graph(all_docs: dict[Path, dict]) -> dict[Path, set[Path]]:
    """Undirected adjacency from every doc's related: list, resolved to real files."""
    graph: dict[Path, set[Path]] = {p: set() for p in all_docs}
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


def closeout_family_for(ag: str, all_paths: list[Path]) -> set[Path]:
    """Discover the AG's closeout-family docs by filename glob — never hand-hardcoded,
    so a new companion (_aggregated_sources_/_history_/_audit_) is picked up the moment
    it exists."""
    prefix = f"{ag}_consolidated_"
    return {p for p in all_paths if p.name.startswith(prefix)}


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

    graph = build_related_graph(all_docs)
    all_paths = list(all_docs)

    closeout_family: dict[str, set[Path]] = {ag: closeout_family_for(ag, all_paths) for ag in REAL_AGS}
    closeout_body_blob: dict[str, str] = {
        ag: "\n".join(all_bodies[p] for p in fam if p in all_bodies) for ag, fam in closeout_family.items()
    }

    violations: list[str] = []
    for path, fm in all_docs.items():
        ag_values = [v for v in docspec._as_list(fm.get("asset_group")) if isinstance(v, str)]
        if len(ag_values) != 1 or ag_values[0] not in REAL_AGS:
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
