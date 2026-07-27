#!/usr/bin/env python3
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
NON_AG_TRANCHES = ["ao", "ci", "infra"]
ALL_TRANCHES = [*AGS, "cross-cutting", *NON_AG_TRANCHES]

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
DATA_EPICS = {
    "infrastructure_master",
    "instruments_master",
    "mtds_mdps_master",
    "manifest_master",
    "features_and_ml_master",
}
EXCLUDED_STATUS = {"resolved", "archived", "superseded"}


def _iter_docs() -> list[Path]:
    out = []
    for pat in ["plans/active/*.md", "plans/active/issues/*.md"]:
        out.extend(PM.glob(pat))
    return sorted(set(out))


def _closeout_paths(tranche: str) -> list[Path]:
    prefix = "cross_cutting" if tranche == "cross-cutting" else tranche
    return sorted(PM.glob(f"plans/active/{prefix}_consolidated_closeout_*.md"))


def _covering_paths(tranche: str, include_closeout: bool = True) -> list[Path]:
    """Real covering docs: the consolidated closeout(s) + every dispatch_batch/finalize doc for this
    tranche. Excludes *_aggregated_sources* (digest, non-covering per skill) and *_history_* (archive).

    For ao/ci/infra, membership itself is DEFINED by citation in the closeout doc (see main()) -- so
    counting the closeout as a "covering" doc there would make every member trivially "cited"
    (tautology). Callers computing coverage for ao/ci/infra must pass include_closeout=False so only
    a REAL batch/finalize citation (actual dispatch, not just being listed in the closeout's own
    Sources/Tracks digest) counts as covered.
    """
    prefix = "cross_cutting" if tranche == "cross-cutting" else tranche
    paths = list(_closeout_paths(tranche)) if include_closeout else []
    for p in PM.glob(f"plans/active/{prefix}_*.md"):
        name = p.name
        if "aggregated_sources" in name or "_history_" in name:
            continue
        if re.search(r"(dispatch_batch|satellite|_finalize)", name):
            paths.append(p)
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

    covering_paths = _covering_paths(t, include_closeout=(t not in NON_AG_TRANCHES))
    cited = _cited_basenames(covering_paths)

    non_ag_member_sets = (
        {nt: _cited_basenames(_closeout_paths(nt)) for nt in NON_AG_TRANCHES} if t in NON_AG_TRANCHES else {}
    )

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
        parent_epic = fm.get("parent_epic") or ""

        if t in AGS:
            member = t in asset_group
        elif t == "cross-cutting":
            member = "cross-cutting" in asset_group and (parent_epic in DATA_EPICS or basename in cited)
        else:  # ao/ci/infra
            member = basename in non_ag_member_sets.get(t, set())

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
