#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
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
- A tranche whose closeout family resolves ONLY to ARCHIVED docs (coordinator archived, not yet
  reopened — `ao` 2026-07-25 -> 2026-08-12) is still a valid link target, but an orphan whose
  AG's coordinator is archived gets a violation message that NAMES the archived match and flags
  "the tranche may need reopening", instead of the generic "no path" that cost a 10-day
  diagnosis (finding: `ao_consolidated_closeout_2026_08_12.md`).

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
  python3 scripts/plan-hygiene/check_ag_closeout_linkage.py --diff-base <ref> [--quiet]
Exit 0 if the orphan count is <= baseline. NEVER hand-raise a baseline entry.

``--diff-base <ref>`` (2026-08-14, extends the proven pattern from check_reference_paths.py /
check_na_corpus_ratchet.py / check_archive_candidates.sh / check_effort_signal_ratchet.py — see
their own --diff-base docs + plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_
2026_08_09.md): this check was itself named as "another corpus-wide ratchet with no diff-scoped
fast path — the same class" in na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_
2026_08_10.md's own todo list, having independently tripped the identical lag-deadlock (frozen
head reported 1 orphan baseline 0; LDR tip reported 0 the same minute — transient corpus state no
individual commit owned, and the eventual drain was attributed to someone else's unrelated
commit). Diff-scoped mode computes the orphan SET at HEAD (live worktree) and the orphan SET at
`<ref>` (read via `git ls-tree`/`cat-file --batch`, never a live-disk read — no worktree
checkout), and fails only on a path that is an orphan at HEAD but was NOT an orphan at `<ref>`.
Unlike the flat string-diff the other consumers use, this compares by PATH IDENTITY (the doc
itself), not by violation message text, since this check's message can legitimately reword (e.g.
the archived-coordinator wording) across two states for the SAME underlying orphan — comparing
paths avoids reading a pure message-text change as a false "new" orphan.

Building the base-ref orphan set replicates the full graph/closeout-family/body-blob computation
against `<ref>` content instead of the worktree: `_scan_dirs_at_ref` reads TARGET_DIRS (direct
children only, exempt-filtered — mirrors target_files()) and CLOSEOUT_SEARCH_DIRS (recursive,
unfiltered — mirrors closeout_search_paths()) via git, so no closeout-family body ever needs a
live-disk fallback read for the base state. `related:` resolution against `<ref>` is backed by a
ref-scoped basename index (`git ls-tree -r <ref> -- plans codex`, same directory scope
check_reference_paths.py's own diff-base already uses) instead of `_md_basename_index()`'s live
`PM_DIR.rglob`. Falls back safely to "no orphans at base" (every current orphan reads as new) if
`<ref>` cannot be resolved locally — callers MUST verify the ref is fetched/resolvable before
passing --diff-base (see run_hygiene_sweep.sh's DIFF_BASE_REF guard, which already gates every
other --diff-base consumer this same way).

``--tranche <name>`` (2026-08-14, additive/opt-in): scopes the printed orphan list + count to
ONE tranche (mirrors generate_ag_closeout_audit_candidates.py's --tranche flag) — a real,
measured cost a full-corpus run incurs for a tranche-scoped dispatch (e.g. cefi's own
/ag-closeout-audit run surfacing 80 non-cefi orphans irrelevant to it). DIAGNOSTIC ONLY: the
corpus-wide baseline ratchet is a single number for the whole corpus, not decomposable per
tranche, so this mode always exits 0 (informational) rather than gating against it — no-flag
mode's baseline-gated behavior is completely unchanged.

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
MAX_HOPS = 3
# Closed/terminal statuses excluded from orphan candidacy — a superseded, resolved,
# cancelled, or completed doc is already closed; flagging it as an unlinked orphan is noise.
# Mirrors generate_ag_closeout_audit_candidates.py's EXCLUDED_STATUS.
EXCLUDED_STATUS = frozenset({"archived", "cancelled", "complete", "false-positive", "resolved", "superseded"})


def _is_active_path(p: Path) -> bool:
    """True when a doc lives under `plans/active` (a LIVE coordinator), False when it lives
    under `plans/archive` (an archived one). Lets an orphan's violation message distinguish an
    archived-coordinator tranche (may need reopening) from a live one (just needs a link)."""
    return (PM_DIR / "plans" / "active") in p.parents


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


_MD_BASENAME_INDEX: dict[str, list[Path]] | None = None


def _md_basename_index() -> dict[str, list[Path]]:
    """basename -> every matching Path under PM_DIR, built via ONE `rglob("*.md")` walk and
    memoized process-wide.

    Perf fix (2026-08-12, pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md
    todo B): `resolve_related_entry` used to run its OWN fresh `rglob` per fallback lookup,
    called once per `related:` ENTRY across the whole corpus (`build_related_graph`'s loop) —
    with ~750 docs each carrying several `related:` entries, a meaningful fraction landing on
    the fallback path meant hundreds of full recursive directory walks. Measured: 42.7s wall,
    31.1s of it kernel time (`rglob`'s stat/readdir syscalls), for a single `--only` run.
    One walk + a dict lookup is behaviorally identical (same "first match" semantics — Python's
    `rglob` order was never guaranteed sorted to begin with, so this changes no live case where
    exactly one file matches a basename, which is every case seen in this corpus) and turns
    O(entries x corpus size) into O(corpus size).
    """
    global _MD_BASENAME_INDEX
    if _MD_BASENAME_INDEX is None:
        index: dict[str, list[Path]] = {}
        for p in PM_DIR.rglob("*.md"):
            index.setdefault(p.name, []).append(p)
        _MD_BASENAME_INDEX = index
    return _MD_BASENAME_INDEX


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
    index = _md_basename_index()
    if entry.endswith(".md"):
        candidate = (from_path.parent / entry).resolve()
        if candidate.is_file():
            return candidate
        for hit in index.get(Path(entry).name, ()):
            if hit.is_file():
                return hit
        return None
    # Bare slug (parent_epic-style, no extension) — try a basename match under plans/.
    plans_dir = PM_DIR / "plans"
    for hit in index.get(f"{entry}.md", ()):
        if plans_dir in hit.parents:
            return hit
    return None


def build_related_graph(
    all_docs: dict[Path, dict],
    extra_nodes: frozenset[Path] = frozenset(),
    resolve_fn=resolve_related_entry,
) -> dict[Path, set[Path]]:
    """Undirected adjacency from every doc's related: list, resolved to real files.

    `extra_nodes` seeds additional graph nodes (with no outgoing edges of their own) BEFORE
    edge resolution runs, so a `related:` entry that resolves to one of them (e.g. an active
    doc linking to an ARCHIVED closeout family doc) is still recorded as an edge — the target
    membership check below (`target in graph`) would otherwise silently drop it.

    `resolve_fn` defaults to the live-disk `resolve_related_entry` above; --diff-base mode
    passes a ref-scoped resolver instead (see `_ref_resolver`) so graph construction never
    touches the live worktree when evaluating a historical ref.
    """
    graph: dict[Path, set[Path]] = {p: set() for p in (*all_docs, *extra_nodes)}
    for path, fm in all_docs.items():
        for entry in docspec._as_list(fm.get("related")):
            if not isinstance(entry, str):
                continue
            target = resolve_fn(entry, path)
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


def _has_active_single_ag_docs(ag: str, all_docs: dict[Path, dict]) -> bool:
    """True when at least one live candidate doc is tagged with this single covered asset
    group — the population whose commits the closeout gate actually screens. Mirrors
    `_orphans_for`'s candidacy predicate (single covered value + non-closed status)."""
    for _p, fm in all_docs.items():
        if fm.get("status") in EXCLUDED_STATUS:
            continue
        ag_values = [v for v in docspec._as_list(fm.get("asset_group")) if isinstance(v, str)]
        if len(ag_values) == 1 and ag_values[0] == ag:
            return True
    return False


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
    graph_resolver=resolve_related_entry,
) -> dict[Path, str]:
    """Every current orphan among `all_docs`, given a precomputed closeout_family (paths only —
    filename-glob-derived, does not depend on doc content, so it's safe to compute ONCE and
    reuse across the current-state pass and every staged file's HEAD-content-override pass).
    Shared by full-sweep mode, `--only`, and `--diff-base` so no mode can ever define "an
    orphan" differently. `graph_resolver` defaults to the live-disk resolver; --diff-base
    mode passes a ref-scoped one (see `_ref_resolver`)."""
    closeout_targets = frozenset(p for fam in closeout_family.values() for p in fam)
    graph = build_related_graph(all_docs, extra_nodes=closeout_targets, resolve_fn=graph_resolver)

    closeout_body_blob: dict[str, str] = {}
    for ag, fam in closeout_family.items():
        bodies: list[str] = []
        for p in fam:
            body = all_bodies.get(p)
            if body is None:
                # archived closeout doc, or a doc excluded by an --only override — not
                # necessarily in the (possibly overridden) all_bodies scan. --diff-base mode
                # never hits this fallback: its all_bodies is pre-merged with every
                # closeout-family doc's ref content (see _run_diff_base), so this stays a
                # LIVE-DISK read used only by the worktree-backed callers (full-sweep/--only).
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
        ag_values = [v for v in docspec._as_list(fm.get("asset_group")) if isinstance(v, str)]
        # Keyed off closeout_family (not the module-level COVERED_ASSET_GROUPS) so a caller
        # that passes a SCOPED family dict (--tranche mode) only evaluates docs in that
        # tranche, instead of KeyError-ing on the first doc belonging to an excluded tranche.
        if len(ag_values) != 1 or ag_values[0] not in closeout_family:
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
        # Archived-coordinator signal (ao_consolidated_closeout_2026_08_12.md P2): when this
        # tranche's closeout family resolves ONLY to archived docs — the coordinator was
        # archived and never reopened — the generic "no path" message hides the real diagnosis
        # (the 2026-08 incident took a 10-day investigation to surface). Name the archived
        # match so the refused commit reads in one line: the tranche may need reopening.
        if not any(_is_active_path(p) for p in family):
            archived_names = ", ".join(sorted(p.name for p in family))
            msg = (
                f"{relpath}: asset_group=[{ag}] has no path (graph or mention) to its closeout "
                f"family — the only closeout-family match(es) are ARCHIVED ({archived_names}); "
                f"the tranche may need reopening"
            )
        else:
            msg = f"{relpath}: asset_group=[{ag}] has no path (graph or mention) to its closeout family"
        violations[path] = msg

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


def _tree_entries_md(ref: str, rel_dirs: tuple[str, ...]) -> list[tuple[str, str]]:
    """[(relpath, blob_sha), ...] for .md files under `rel_dirs` at `ref` (recursive) — one
    `git ls-tree -r` call regardless of corpus size. Mirrors check_reference_paths.py's
    `_tree_entries_md` helper of the same name/shape."""
    result = subprocess.run(
        ["git", "-C", str(PM_DIR), "ls-tree", "-r", ref, "--", *rel_dirs],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    entries: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) != 3 or parts[1] != "blob":
            continue
        if path.endswith(".md"):
            entries.append((path, parts[2]))
    return entries


def _batch_read_blobs(shas: list[str]) -> dict[str, str]:
    """sha -> decoded text content, via ONE `git cat-file --batch` call for the whole list.
    Mirrors check_reference_paths.py's `_batch_read_blobs` helper of the same name/shape."""
    if not shas:
        return {}
    proc = subprocess.run(
        ["git", "-C", str(PM_DIR), "cat-file", "--batch"],
        input=("\n".join(shas) + "\n").encode("utf-8"),
        capture_output=True,
        check=False,
    )
    out = proc.stdout
    result: dict[str, str] = {}
    pos = 0
    while pos < len(out):
        nl = out.index(b"\n", pos)
        header = out[pos:nl].decode("utf-8", "replace").split()
        if len(header) != 3:
            break
        sha, _obj_type, size_s = header
        size = int(size_s)
        start = nl + 1
        result[sha] = out[start : start + size].decode("utf-8", "replace")
        pos = start + size + 1  # +1 skips the trailing newline after object data
    return result


def _scan_dirs_at_ref(
    ref: str, rel_dirs: tuple[str, ...], *, direct_children_only: bool, filter_exempt: bool
) -> tuple[dict[Path, dict], dict[Path, str]]:
    """Parse frontmatter+body for every .md under `rel_dirs` at `ref` (git-backed, never a
    live-disk read). `direct_children_only` restricts each dir to its own immediate .md files
    (mirrors target_files()'s non-recursive `base.glob("*.md")`); False recurses (mirrors
    closeout_search_paths()'s `base.rglob(...)`). `filter_exempt` applies docspec.is_exempt
    (a path-string predicate, no disk I/O — safe against historical ref content), matching
    target_files()'s candidacy filter."""
    docs: dict[Path, dict] = {}
    bodies: dict[Path, str] = {}
    entries = _tree_entries_md(ref, rel_dirs)
    blobs = _batch_read_blobs([sha for _, sha in entries])
    for relpath, sha in entries:
        if direct_children_only and str(Path(relpath).parent) not in rel_dirs:
            continue
        if filter_exempt and docspec.is_exempt(relpath):
            continue
        text = blobs.get(sha)
        if text is None:
            continue
        try:
            fm, body = docspec.parse_frontmatter(text)
        except yaml.YAMLError:
            # Malformed frontmatter at this historical ref (e.g. an archived doc whose YAML
            # was never valid to begin with) — unparseable, same as fm is None below. A
            # corrupt doc elsewhere in the corpus must never crash this check.
            continue
        if fm is None:
            continue
        p = PM_DIR / relpath
        docs[p] = fm
        bodies[p] = body
    return docs, bodies


def _ref_resolver(existing_relpaths: set[str], basename_index: dict[str, list[str]]):
    """Build a resolve_related_entry-shaped callable backed by `ref` tree membership instead
    of live disk — same resolution order as resolve_related_entry (leading-slash exact match;
    same-dir relative .md; basename fallback; bare-slug under plans/)."""

    def resolver(entry: str, from_path: Path) -> Path | None:
        entry = entry.strip()
        if not entry:
            return None
        if entry.startswith("/"):
            rel = entry.lstrip("/")
            return (PM_DIR / rel) if rel in existing_relpaths else None
        if entry.endswith(".md"):
            from_rel = from_path.relative_to(PM_DIR).as_posix()
            candidate_rel = (Path(from_rel).parent / entry).as_posix()
            if candidate_rel in existing_relpaths:
                return PM_DIR / candidate_rel
            for hit in basename_index.get(Path(entry).name, ()):
                return PM_DIR / hit
            return None
        for hit in basename_index.get(f"{entry}.md", ()):
            if hit.startswith("plans/"):
                return PM_DIR / hit
        return None

    return resolver


def _run_diff_base(base_ref: str, quiet: bool) -> int:
    """Diff-scoped mode: fail only on orphans NEW at HEAD vs `base_ref` — see the module
    docstring's --diff-base section for the deadlock this closes."""
    head_docs, head_bodies = _scan_current()
    head_search_paths = closeout_search_paths()
    head_family = {ag: closeout_family_for(ag, head_search_paths) for ag in COVERED_ASSET_GROUPS}
    head_orphans = _orphans_for(head_docs, head_bodies, head_family)

    base_target_docs, base_target_bodies = _scan_dirs_at_ref(
        base_ref, TARGET_DIRS, direct_children_only=True, filter_exempt=True
    )
    base_closeout_docs, base_closeout_bodies = _scan_dirs_at_ref(
        base_ref, CLOSEOUT_SEARCH_DIRS, direct_children_only=False, filter_exempt=False
    )
    # Merge closeout bodies in so _orphans_for's body lookup never falls back to a live-disk
    # read for the base-ref pass (that fallback would read WORKTREE content, not `base_ref`'s).
    base_bodies = {**base_closeout_bodies, **base_target_bodies}
    base_search_paths = list({**base_closeout_docs, **base_target_docs}.keys())
    base_family = {ag: closeout_family_for(ag, base_search_paths) for ag in COVERED_ASSET_GROUPS}

    basename_entries = _tree_entries_md(base_ref, ("plans", "codex"))
    basename_index: dict[str, list[str]] = {}
    for relpath, _sha in basename_entries:
        basename_index.setdefault(Path(relpath).name, []).append(relpath)
    existing_relpaths = {relpath for relpath, _sha in basename_entries}
    resolver = _ref_resolver(existing_relpaths, basename_index)

    base_orphans = _orphans_for(base_target_docs, base_bodies, base_family, graph_resolver=resolver)

    new_orphans = sorted(v for p, v in head_orphans.items() if p not in base_orphans)

    if not quiet:
        for v in new_orphans:
            print(f"  ORPHAN  {v}")

    n = len(new_orphans)
    print(
        f"{'✅' if n == 0 else '❌'} check_ag_closeout_linkage (--diff-base {base_ref}): "
        f"{n} NEW orphan(s) vs {base_ref}"
    )
    return 0 if n == 0 else 1


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


def _tranche_from_argv() -> str | None:
    """`--tranche <name>` (additive/opt-in, see module docstring) — validated against
    COVERED_ASSET_GROUPS, the same value domain the rest of this script already keys on."""
    if "--tranche" not in sys.argv:
        return None
    idx = sys.argv.index("--tranche")
    if idx + 1 >= len(sys.argv):
        print("error: --tranche requires a value", file=sys.stderr)
        raise SystemExit(2)
    tranche = sys.argv[idx + 1]
    if tranche not in COVERED_ASSET_GROUPS:
        print(f"error: --tranche must be one of {sorted(COVERED_ASSET_GROUPS)}", file=sys.stderr)
        raise SystemExit(2)
    return tranche


def main() -> int:
    if "--only" in sys.argv:
        idx = sys.argv.index("--only")
        return _run_only(sys.argv[idx + 1 :], "--quiet" in sys.argv)

    if "--diff-base" in sys.argv:
        idx = sys.argv.index("--diff-base")
        return _run_diff_base(sys.argv[idx + 1], "--quiet" in sys.argv)

    quiet = "--quiet" in sys.argv
    update = "--update-baseline" in sys.argv
    tranche = _tranche_from_argv()

    files = target_files()
    all_docs, all_bodies = _scan_current()

    search_paths = closeout_search_paths()
    scoped_ags = (tranche,) if tranche else COVERED_ASSET_GROUPS
    closeout_family: dict[str, set[Path]] = {ag: closeout_family_for(ag, search_paths) for ag in scoped_ags}

    if tranche:
        # Diagnostic mode (see module docstring): scope the printed list + count to one
        # tranche and always exit 0 — the baseline ratchet is a single corpus-wide number,
        # not decomposable per tranche, so this mode never gates on it.
        violations_by_path = _orphans_for(all_docs, all_bodies, closeout_family)
        violations = list(violations_by_path.values())
        if not quiet:
            print(f"AG-closeout linkage check [{tranche}] ({len(all_docs)} docs scanned):")
            print()
            for v in sorted(violations):
                print(f"  ORPHAN  {v}")
            print()
        print(f"check_ag_closeout_linkage [{tranche}]: {len(violations)} orphan(s) (diagnostic, not baseline-gated)")
        return 0

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

    # ARCHIVED-only family with live members = the `ao` 2026-08-12 failure mode (coordinator
    # archived while the tranche kept producing docs → every new finding became an uncommittable
    # orphan, diagnosed only when a specific commit was refused 10 days later). The per-orphan
    # violation message added for that incident only fires at commit time on the ONE doc being
    # committed; this surfaces the latent condition proactively at sweep time — same posture as
    # the EMPTY-family warning above — so the tranche is reopened before it blocks anything.
    archived_only_live = sorted(
        ag
        for ag in COVERED_ASSET_GROUPS
        if closeout_family[ag]
        and not any(_is_active_path(p) for p in closeout_family[ag])
        and _has_active_single_ag_docs(ag, all_docs)
    )
    if archived_only_live:
        for ag in archived_only_live:
            names = ", ".join(sorted(p.name for p in closeout_family[ag]))
            print(
                f"⚠️  check_ag_closeout_linkage: [{ag}] closeout family is ARCHIVED-only ({names}) "
                f"but the tranche still has live docs — reopen it (<ag>_consolidated_closeout_<date>.md) "
                f"or new findings will block at commit time",
                file=sys.stderr,
            )

    violations_by_path = _orphans_for(all_docs, all_bodies, closeout_family)
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
