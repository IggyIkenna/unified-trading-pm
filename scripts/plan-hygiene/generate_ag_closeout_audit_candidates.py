#!/usr/bin/env python3
# Epic: plan_hygiene_master
# Lifecycle: permanent
# Delete-when: NA
"""Cheap Phase-0 pre-filter for /ag-closeout-audit: per tranche, which AG-primary docs are NEVER
cited by basename in any of that tranche's real covering docs (consolidated-closeout's own todos +
every *_dispatch_batch*/*_finalize* doc; explicitly EXCLUDES *_aggregated_sources* digests, which are
non-covering per cursor-configs/skills/ag-closeout-audit/SKILL.md's own Phase 0.1: "treat as
NON-covering: being listed there is not dispatch").

This is NOT a replacement for the skill's real Phase 1 per-doc judgment (a citation can be a stale
reference, a partial-coverage mention, or a genuine close) -- it is the cheap mechanical narrowing
step that makes a full corpus-wide fresh audit tractable: docs cited nowhere in a real covering doc
are near-certain orphan candidates and get priority real agent review; docs cited somewhere were
very likely already resolved by a prior /ag-closeout-audit round or this session's own na_docs Phase
1/2 review, so re-reading all of them from scratch is low marginal value.

# Epic: agent_operating_framework_master
# Lifecycle: permanent
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

import yaml

PM = Path(__file__).resolve().parents[2]


def _load_docspec():
    spec = importlib.util.spec_from_file_location("docspec", PM / "scripts" / "docs" / "docspec.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docspec"] = mod
    spec.loader.exec_module(mod)
    return mod


ds = _load_docspec()

AGS = ["cefi", "defi", "tradfi", "prediction", "sports"]
NON_AG_TRANCHES = ["ao", "ci", "infra", "ui"]
ALL_TRANCHES = [*AGS, "cross-cutting", *NON_AG_TRANCHES]
# The `infra` TRANCHE name (CLI --tranche, SKILL.md, closeout-doc prefix) does not match the actual
# `asset_group` enum VALUE, which is `infrastructure` (plans/PLAN_FORMAT.md's ASSET_GROUP enum has no
# "infra" member) -- found while fixing this script's membership test to read asset_group directly
# (generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md):
# a naive `t in asset_group` for t="infra" would silently match zero docs (every real doc is tagged
# `infrastructure`), reproducing the exact silent-zero-candidates failure class this fix exists to
# close, just via a different root cause. `ao`/`ci`/`ui` have no such mismatch (their enum values equal
# their tranche names).
TRANCHE_ASSET_GROUP_VALUE = {"infra": "infrastructure"}

CLOSEOUT_NAME = {
    t: (
        "cross_cutting_consolidated_closeout_2026_07_25.md"
        if t == "cross-cutting"
        else f"{t}_consolidated_closeout_2026_07_25.md"
    )
    for t in ALL_TRANCHES
}
# a handful of AGs date their closeout doc differently -- resolved by globbing at use time, not hardcoded further

CITE_RE = re.compile(r"([a-z0-9_]+_20\d\d_\d\d_\d\d(?:_finalize)?\.md)")
EXCLUDED_STATUS = {"resolved", "archived", "superseded"}


def _iter_docs() -> list[Path]:
    out = []
    for pat in ["plans/active/*.md", "plans/active/issues/*.md"]:
        out.extend(PM.glob(pat))
    return sorted(set(out))


def _closeout_paths(tranche: str) -> list[Path]:
    prefix = "cross_cutting" if tranche == "cross-cutting" else tranche
    return sorted(
        p for p in PM.glob(f"plans/active/{prefix}_consolidated_closeout_*.md") if "aggregated_sources" not in p.name
    )


def _resolve_depends_on(path: Path) -> list[Path]:
    """Resolve a doc's frontmatter `depends_on:` slugs to real `plans/active/` file paths.

    A `*_finalize*` doc's `depends_on:` names its paired MAIN plan by bare slug (PLAN_FORMAT.md
    convention) -- for a line-cap-split fork of a consolidated closeout (e.g.
    `cefi_misc_audits_and_hygiene_2026_07_25.md`) that main doc's OWN filename does not match the
    `(dispatch_batch|satellite|_finalize)` regex below, so without this resolution step it is
    invisible to `_covering_paths()` even though SKILL.md Phase 0.2 path (b) requires counting it as
    covering. A slug whose target has since archived (e.g. a finalize whose main plan is already done
    and moved to `plans/archive/`) resolves to nothing under `plans/active/` -- harmless, since an
    archived doc can never appear in `_iter_docs()`'s candidate scan either.
    """
    if not path.exists():
        return []
    try:
        fm, _ = ds.parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
    except yaml.YAMLError:
        return []
    if fm is None:
        return []
    deps = fm.get("depends_on") or []
    if isinstance(deps, str):
        deps = [deps]
    out: list[Path] = []
    for slug in deps:
        out.extend(PM.glob(f"plans/active/{slug}.md"))
        out.extend(PM.glob(f"plans/active/issues/{slug}.md"))
    return out


def _covering_paths(tranche: str, include_closeout: bool = True) -> list[Path]:
    """Real covering docs: the consolidated closeout(s) + every dispatch_batch/finalize doc for this
    tranche, PLUS (Phase 0.2 path (b)) every plan a discovered `*_finalize*` doc's OR the closeout
    doc's own `depends_on:` resolves to. Excludes *_aggregated_sources* (digest, non-covering per
    skill -- see `_closeout_paths()`) and *_history_* (archive).

    ao/ci/infra membership is now tested the SAME way as the 5 real AGs (`t in asset_group`, see
    main()) -- as of the 2026-07-27 asset_group schema expansion (`unified-trading-pm@a97bc7bed`),
    ao/ci/infrastructure are real dedicated asset_group enum values, so there is no more tautology
    risk in counting a tranche's own closeout doc as a covering doc for it (this function used to be
    called with include_closeout=False for these 3 tranches for exactly that reason -- see
    generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md
    for the incident this fixed: once a tranche's closeout doc archives, the OLD citation-based
    membership mechanism silently returned zero members for that tranche).

    Resolving `depends_on:` for the closeout doc itself (added 2026-08-01, ag-closeout-audit tradfi
    tranche) closes a real gap: a line-cap-split fork with no paired `*_finalize*` doc of its own
    (e.g. tradfi_backfill_throughput_followups_2026_07_24.md, tradfi_phase_d_terminal_gate_2026_07_24.md
    -- both forked straight out of tradfi_consolidated_closeout_2026_07_18.md's own line-cap trim, per
    its Split notice table) was previously invisible to this function unless SOME OTHER covering doc's
    `_finalize` happened to also depend on it. The closeout's own `depends_on:` is the one place a fork
    with no finalize pair is guaranteed to be named -- ONLY if that field is kept complete (see the fix
    landed the same day on tradfi_consolidated_closeout_2026_07_18.md itself).
    """
    prefix = "cross_cutting" if tranche == "cross-cutting" else tranche
    paths = list(_closeout_paths(tranche)) if include_closeout else []
    for p in PM.glob(f"plans/active/{prefix}_*.md"):
        name = p.name
        if "aggregated_sources" in name or "_history_" in name:
            continue
        if re.search(r"(dispatch_batch|satellite|_finalize)", name):
            paths.append(p)
    for p in list(paths):
        if re.search(r"_finalize", p.name) or p in set(_closeout_paths(tranche)):
            paths.extend(_resolve_depends_on(p))
    return sorted(set(paths))


def _cited_basenames(paths: list[Path]) -> set[str]:
    out: set[str] = set()
    for p in paths:
        if p.exists():
            out |= set(CITE_RE.findall(p.read_text(encoding="utf-8", errors="replace")))
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tranche", choices=ALL_TRANCHES, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    t = args.tranche

    covering_paths = _covering_paths(t)
    cited = _cited_basenames(covering_paths)

    candidates = []
    for path in _iter_docs():
        rel = path.relative_to(PM).as_posix()
        try:
            fm, _ = ds.parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        except yaml.YAMLError:
            continue
        if fm is None:
            continue
        status = fm.get("status")
        if status in EXCLUDED_STATUS:
            continue
        basename = path.name
        if path in covering_paths:
            continue
        if re.search(r"_consolidated_closeout", basename):
            # a sibling tranche's own hub doc citing/being-cited-by another hub doc (e.g. ao's closeout
            # linking to ci's) is a hub cross-reference, never a real audit-target membership -- exclude
            # every *_consolidated_closeout_* doc regardless of which tranche's citation surfaced it.
            continue
        if re.search(r"_finalize(_\d{4}_\d{2}_\d{2})?\.md$", basename):
            # a finalize doc's filename is inherited from its SOURCE doc, not tranche-prefixed (e.g.
            # data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md carries cefi's
            # asset_group but doesn't match cefi's own `cefi_*.md` covering-doc glob) -- it's gating
            # scaffolding for its paired plan (depends_on + gate_on_depends), never an independent audit
            # target, regardless of tranche or naming prefix. Exclude blanket, not just via the
            # tranche-prefixed covering_paths glob.
            continue

        member = False
        asset_group = fm.get("asset_group") or []
        if isinstance(asset_group, str):
            asset_group = [asset_group]

        if t in AGS or t in NON_AG_TRANCHES:
            # ao/ci/infra are real dedicated asset_group enum values (2026-07-27 schema expansion) --
            # tested identically to the 5 real AGs, not via a closeout-citation proxy (the retired
            # 2026-07-25->27 workaround; see _covering_paths()'s docstring for the incident this fixed).
            # infra's enum VALUE is "infrastructure", not "infra" -- see TRANCHE_ASSET_GROUP_VALUE.
            member = TRANCHE_ASSET_GROUP_VALUE.get(t, t) in asset_group
        elif t == "cross-cutting":
            # Tested identically to every other tranche (plain tag membership) -- previously gated on
            # `parent_epic in DATA_EPICS or basename in cited`, which silently excluded a bare
            # `[cross-cutting]` doc with a non-data `parent_epic` (e.g. `plan_hygiene_master`,
            # `agent_operating_framework_master`) THAT HAD NEVER BEEN CITED ANYWHERE: it failed the
            # member test entirely, so it was invisible to both the "cited" and "never cited" buckets,
            # not just the latter (Process finding 2,
            # issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md -- 4 such docs were only found
            # by cross-checking against check_ag_closeout_linkage.py's stricter graph-reachability
            # check, which has no such member-test gate). Citation status still drives the
            # cited/never-cited split below via `cited_in_covering_doc` -- it just no longer gates
            # membership itself.
            member = "cross-cutting" in asset_group

        if not member:
            continue

        assigned_vm = fm.get("assigned_vm")
        # a doc that is itself assigned_vm:planning + status:active/open IS its own dispatch vehicle --
        # it does not need external citation elsewhere to be "covered" (it covers itself). Only a
        # self-dispatched doc's absence of ANY covering AND non-self-dispatched status is a true orphan
        # signal.
        self_dispatched = assigned_vm == "planning" and status in ("active", "open")

        candidates.append(
            {
                "path": rel,
                "basename": basename,
                "assigned_vm": assigned_vm,
                "status": status,
                "cited_in_covering_doc": basename in cited,
                "self_dispatched": self_dispatched,
            }
        )

    never_cited = [c for c in candidates if not c["cited_in_covering_doc"] and not c["self_dispatched"]]
    cited_somewhere = [c for c in candidates if c["cited_in_covering_doc"] or c["self_dispatched"]]

    if args.json:
        print(
            json.dumps(
                {
                    "tranche": t,
                    "covering_paths": [p.relative_to(PM).as_posix() for p in covering_paths],
                    "total_members": len(candidates),
                    "never_cited_count": len(never_cited),
                    "never_cited": never_cited,
                    "candidates": candidates,
                    "cited_somewhere_count": len(cited_somewhere),
                },
                indent=1,
            )
        )
    else:
        print(f"{t}: {len(candidates)} members, {len(covering_paths)} covering docs")
        print(f"  never cited in any real covering doc: {len(never_cited)}")
        for c in never_cited:
            print(f"    {c['path']}  (assigned_vm={c['assigned_vm']}, status={c['status']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
