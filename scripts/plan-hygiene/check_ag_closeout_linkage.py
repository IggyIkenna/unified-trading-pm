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
  python3 scripts/plan-hygiene/check_ag_closeout_linkage.py --only <path> [<path> ...]
  python3 scripts/plan-hygiene/check_ag_closeout_linkage.py --tranche <name> [--quiet]
Exit 0 if the orphan count is <= baseline. NEVER hand-raise a baseline entry.

``--tranche <name>`` (2026-08-11): an additive, opt-in REPORT filter for a tranche-scoped
consumer — an `/ag-closeout-audit <tranche>` dispatch runs this gate as its own safety net
(SKILL.md Phase 0.3) but only cares about ITS tranche's orphans; the corpus-wide listing
buries them (measured 2026-08-06: a cefi-scoped run had to read past 80 non-cefi orphans to
find its own 7). Mirrors the already-shipped ``--tranche`` on
generate_ag_closeout_audit_candidates.py, and accepts BOTH that script's CLI tranche
vocabulary and the raw `asset_group` enum value for the one tranche where they differ
(`infra` / `infrastructure`).

Two properties this filter deliberately keeps:
- The SCAN is never narrowed, only the OUTPUT. Orphan status depends on the full `related:`
  graph (undirected, up to 3 hops, freely pathing through OTHER tranches' docs) and on the
  closeout family's body text, so a tranche-scoped scan could invent orphans that a
  corpus-wide scan resolves. `--tranche` computes the identical corpus-wide orphan set the
  no-flag mode computes, then filters the printed rows to that tranche.
- It is a REPORT, never a gate: it always exits 0 and refuses ``--update-baseline``. The
  baseline is a single CORPUS-WIDE count; comparing one tranche's handful of orphans against
  it would pass trivially (a false green for a gate that never measured most of the corpus),
  and minting per-tranche baselines is a design call this filter deliberately does not make.
  The no-flag full-corpus ratchet remains the one gate, unchanged, and stays what
  run_hygiene_sweep.sh invokes. A tranche whose closeout family resolves to ZERO docs reports
  a loud UNENFORCED warning instead of a silent clean 0 — same honest-absence contract the
  full-sweep mode's empty-family warning already carries.

``--only <paths>`` (2026-08-09, precommit migration): this ratchet previously had NO
precommit-time presence, only the full corpus-wide baseline mode (baseline: 49 orphans at
time of writing) — a docs(plans) commit had zero enforcement at commit time, same
fast-path-blind-to-full-gate pattern as the other checks migrated this evening. Scoping
naively to "does the TOTAL orphan count among just the staged files exceed the corpus-wide
baseline" would be wrong for the same reason as check_prosewrap_padding.sh: a handful of
staged files' orphan count would essentially never approach a corpus-wide baseline of 49.

This check is ALSO cross-file like check_depends_on_graph.py — a doc's orphan status
depends on the `related:` graph (which can path through OTHER docs, undirected, up to 3
hops) and the closeout family's own body text (a DIFFERENT file). So `--only` builds the
FULL corpus graph/closeout-family/body-blob (cheap: local reads only) exactly like the
full-sweep mode — never a staged-only subgraph, which could miss a real reachability path
through an unstaged intermediate doc. It then asks, PER STAGED FILE: is it currently an
orphan? If not, nothing to flag. If it IS currently an orphan, was it ALSO an orphan when
evaluated with its OWN `git show HEAD:<path>` content substituted into today's otherwise
current corpus (rest of the graph/bodies held as-is)? If yes, this is pre-existing debt in
a file the commit merely touches — skip it (same never-block-on-debt-you-didn't-create
contract as check_effort_signal_ratchet.py --only). If the file was NOT an orphan at HEAD
content but IS now (e.g. this edit removed a `related:` link, or changed the doc's
`asset_group` from multi-value/meta to a single covered value), that is a violation this
commit genuinely introduced — flag it. A brand-new file (absent at HEAD) has no baseline
exemption, so its current orphan status determines the flag directly, matching the
check_effort_signal_ratchet.py convention for new files. Deliberately does NOT try to
reconstruct the ENTIRE corpus's state at HEAD (expensive, requires walking every file's
history) — only the staged file's OWN content is swapped; everything else stays at its
current on-disk state, which is a safe, cheap approximation since this check only needs to
answer "did editing THIS file make IT worse", not "did the whole corpus's graph shift".
"""

from __future__ import annotations

import argparse
import subprocess
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
# `--tranche` CLI vocabulary. The /ag-closeout-audit skill and
# generate_ag_closeout_audit_candidates.py's own `--tranche` call one tranche `infra`, while the
# `asset_group` enum value is `infrastructure` (that script's TRANCHE_ASSET_GROUP_VALUE documents
# the same mismatch). Accept BOTH spellings rather than picking a winner — a caller reaching for
# the wrong one gets a working filter, not a silent zero-row report. Derived from
# COVERED_ASSET_GROUPS (i.e. from docspec.ASSET_GROUP) rather than a second hardcoded tranche
# list, so a future enum expansion widens this filter automatically — the 2026-07-27 expansion
# going unnoticed is exactly what left the gate blind to four tranches
# (ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md).
_TRANCHE_ALIAS = {"infra": "infrastructure"}
TRANCHE_CHOICES = tuple(sorted({*COVERED_ASSET_GROUPS, *_TRANCHE_ALIAS}))
MAX_HOPS = 3
# Closed/terminal statuses excluded from orphan candidacy — a superseded, resolved,
# cancelled, or completed doc is already closed; flagging it as an unlinked orphan is noise.
# Mirrors generate_ag_closeout_audit_candidates.py's EXCLUDED_STATUS.
EXCLUDED_STATUS = frozenset({"archived", "cancelled", "complete", "false-positive", "resolved", "superseded"})

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


def single_covered_asset_group(fm: dict) -> str | None:
    """The doc's `asset_group` when it is exactly ONE covered tranche, else None.

    None means EXEMPT by construction — a multi-value list, `meta` (never had its own
    tranche), or a missing/malformed value. Shared by `_orphans_for` (which decides orphan
    candidacy) and the `--tranche` filter (which decides which orphans to print) so the two
    can never disagree about which tranche a doc belongs to."""
    ag_values = [v for v in docspec._as_list(fm.get("asset_group")) if isinstance(v, str)]
    if len(ag_values) != 1 or ag_values[0] not in COVERED_ASSET_GROUPS:
        return None
    return ag_values[0]


def _scan_current() -> tuple[dict[Path, dict], dict[Path, str]]:
    """Read every candidate doc's frontmatter + body from the CURRENT working-tree content."""
    all_docs: dict[Path, dict] = {}
    all_bodies: dict[Path, str] = {}
    for p in target_files():
        text = p.read_text(encoding="utf-8")
        fm, body = docspec.parse_frontmatter(text)
        if fm is None:
            continue
        all_docs[p] = fm
        all_bodies[p] = body
    return all_docs, all_bodies


def _with_override(
    all_docs: dict[Path, dict], all_bodies: dict[Path, str], path: Path, text: str | None
) -> tuple[dict[Path, dict], dict[Path, str]]:
    """Return a COPY of (all_docs, all_bodies) with `path`'s entry replaced by parsing `text`
    (or removed entirely if `text` is None, e.g. the path did not exist at HEAD). Used by
    `--only` mode to ask "what would this doc's orphan status be with its OWN HEAD content,
    holding the rest of today's corpus fixed" without re-reading every other file from disk."""
    docs2 = dict(all_docs)
    bodies2 = dict(all_bodies)
    docs2.pop(path, None)
    bodies2.pop(path, None)
    if text is not None:
        fm, body = docspec.parse_frontmatter(text)
        if fm is not None:
            docs2[path] = fm
            bodies2[path] = body
    return docs2, bodies2


def _orphans_for(
    all_docs: dict[Path, dict],
    all_bodies: dict[Path, str],
    closeout_family: dict[str, set[Path]],
) -> dict[Path, str]:
    """Every current orphan among `all_docs`, given a precomputed closeout_family (paths only —
    filename-glob-derived, does not depend on doc content, so it's safe to compute ONCE and
    reuse across the current-state pass and every staged file's HEAD-content-override pass).
    Shared by full-sweep mode and `--only` mode so the two can never define "an orphan"
    differently."""
    closeout_targets = frozenset(p for fam in closeout_family.values() for p in fam)
    graph = build_related_graph(all_docs, extra_nodes=closeout_targets)

    closeout_body_blob: dict[str, str] = {}
    for ag, fam in closeout_family.items():
        bodies: list[str] = []
        for p in fam:
            body = all_bodies.get(p)
            if body is None:
                # archived closeout doc, or a doc excluded by an --only override — not
                # necessarily in the (possibly overridden) all_bodies scan.
                try:
                    _, body = docspec.parse_frontmatter(p.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError):
                    body = None
            bodies.append(body or "")
        closeout_body_blob[ag] = "\n".join(bodies)

    violations: dict[Path, str] = {}
    for path, fm in all_docs.items():
        if fm.get("status") in EXCLUDED_STATUS:
            continue
        ag = single_covered_asset_group(fm)
        if ag is None:
            continue
        family = closeout_family[ag]
        if not family or path in family:
            continue  # no closeout doc yet for this AG, or this doc IS the closeout family

        if bfs_reaches(graph, path, family, MAX_HOPS):
            continue
        if mentions_stem(closeout_body_blob[ag], path.stem):
            continue

        relpath = path.relative_to(PM_DIR).as_posix()
        violations[path] = f"{relpath}: asset_group=[{ag}] has no path (graph or mention) to its closeout family"

    return violations


def _head_text(path: Path) -> str | None:
    """`git show HEAD:<relpath>` content, or None if the path did not exist at HEAD (a
    brand-new staged file — treated as having no pre-existing-debt exemption)."""
    try:
        rel = path.resolve().relative_to(PM_DIR).as_posix()
    except ValueError:
        return None
    proc = subprocess.run(
        ["git", "-C", str(PM_DIR), "show", f"HEAD:{rel}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def _run_only(paths: list[str], quiet: bool) -> int:
    all_docs, all_bodies = _scan_current()
    search_paths = closeout_search_paths()
    closeout_family: dict[str, set[Path]] = {ag: closeout_family_for(ag, search_paths) for ag in COVERED_ASSET_GROUPS}
    current_orphans = _orphans_for(all_docs, all_bodies, closeout_family)

    flagged: list[str] = []
    for raw in paths:
        p = Path(raw)
        p = (PM_DIR / raw).resolve() if not p.is_absolute() else p.resolve()
        if p not in current_orphans:
            continue  # not currently an orphan -> nothing to flag regardless of HEAD state

        head_text = _head_text(p)
        if head_text is None:
            # brand-new staged doc (or unresolvable path) — no pre-existing baseline to exempt
            # it against, matches check_effort_signal_ratchet.py's "absent at HEAD -> flag" rule.
            flagged.append(current_orphans[p])
            continue

        head_docs, head_bodies = _with_override(all_docs, all_bodies, p, head_text)
        head_orphans = _orphans_for(head_docs, head_bodies, closeout_family)
        if p not in head_orphans:
            # wasn't an orphan with its OWN head content (rest of today's corpus held fixed) ->
            # this commit's edit to the file itself introduced/worsened the orphan status.
            flagged.append(current_orphans[p])
        # else: already an orphan at HEAD -> pre-existing debt in a file this commit merely
        # touches, not this commit's problem — skip (never block on debt you didn't create).

    if not quiet:
        for v in sorted(flagged):
            print(f"  ORPHAN  {v}")

    n = len(flagged)
    print(f"{'✅' if n == 0 else '❌'} check_ag_closeout_linkage (--only): {n} new orphan(s) in staged files")
    return 0 if n == 0 else 1


def _run_tranche(
    tranche: str,
    violations_by_path: dict[Path, str],
    all_docs: dict[Path, dict],
    family: set[Path],
    quiet: bool,
) -> int:
    """Print the corpus-wide orphan set filtered to ONE tranche. REPORT ONLY — always exit 0;
    see the module docstring for why this is not (and must not silently become) a gate."""
    ag = _TRANCHE_ALIAS.get(tranche, tranche)
    scoped = sorted(msg for path, msg in violations_by_path.items() if single_covered_asset_group(all_docs[path]) == ag)

    if not quiet:
        for v in scoped:
            print(f"  ORPHAN  {v}")
        print()

    if not family:
        # A tranche with no closeout-family doc anywhere has every member skipped by
        # `_orphans_for`, so its orphan count is 0 for a reason that is NOT "clean". Say so
        # loudly rather than let a scoped run read as a pass — same contract as the
        # full-sweep mode's EMPTY-family warning.
        print(
            f"⚠️  check_ag_closeout_linkage (--tranche {tranche}): UNENFORCED — no closeout family "
            f"doc found for asset_group={ag}; 0 orphan(s) here does NOT mean clean",
            file=sys.stderr,
        )

    print(
        f"ℹ️  check_ag_closeout_linkage (--tranche {tranche}): {len(scoped)} orphan(s) "
        f"of {len(violations_by_path)} corpus-wide — REPORT ONLY, not the ratchet gate "
        f"(baseline {load_baseline()} counts the whole corpus; re-run with no --tranche to gate)"
    )
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check every single-asset-group plan/issue doc has a findable path to its AG's consolidated "
        "closeout plan (shrinking ratchet).",
    )
    parser.add_argument("--quiet", action="store_true", help="suppress the per-orphan listing, print only the verdict")
    parser.add_argument(
        "--update-baseline", action="store_true", help="lower the baseline to today's count (never raises it)"
    )
    parser.add_argument(
        "--only",
        nargs="+",
        metavar="PATH",
        help="precommit mode: flag only orphan status THIS commit's staged files newly introduced",
    )
    parser.add_argument(
        "--tranche",
        choices=TRANCHE_CHOICES,
        help="report mode: list only this tranche's orphans out of the full corpus-wide scan (always exits 0)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.only and args.tranche:
        parser.error("--only and --tranche are mutually exclusive (staged-file precommit mode vs. corpus report mode)")
    if args.tranche and args.update_baseline:
        parser.error(
            "--update-baseline refuses a --tranche-scoped run: the baseline is a single CORPUS-WIDE count, so writing "
            "one tranche's count into it would ratchet the gate down to a fraction of the corpus it never measured"
        )

    if args.only:
        return _run_only(args.only, args.quiet)

    quiet = args.quiet
    update = args.update_baseline

    files = target_files()
    all_docs, all_bodies = _scan_current()

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

    violations_by_path = _orphans_for(all_docs, all_bodies, closeout_family)

    if args.tranche:
        # Deliberately AFTER the identical full-corpus scan above — the filter narrows the
        # OUTPUT, never the scan (module docstring: reachability paths freely cross tranches).
        ag = _TRANCHE_ALIAS.get(args.tranche, args.tranche)
        if not quiet:
            print(f"AG-closeout linkage check ({len(all_docs)} docs scanned, {len(files)} candidate files):")
            print()
        return _run_tranche(args.tranche, violations_by_path, all_docs, closeout_family[ag], quiet)

    violations = list(violations_by_path.values())

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
