#!/usr/bin/env python3
"""Generate the current assigned_vm:NA + status:{active,open} doc inventory, split by the 9
/ag-closeout-audit tranches (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra).

Why this exists: a single-line `grep -lE '^assigned_vm:\\s*$'`-style sweep misses multi-line YAML
values (key on its own line, value on an indented continuation) and any value expressed via YAML
flow/quoting — confirmed live on sports_consolidated_closeout_2026_07_19.md
(na_docs_validity_and_ao_eligibility_audit_2026_07_26.md Phase 0). This script parses frontmatter
properly via scripts/docs/docspec.py (PyYAML) instead of line-grepping, for this and every future
sweep.

ao/ci/infrastructure are real dedicated asset_group enum values (2026-07-27 schema expansion,
unified-trading-pm@a97bc7bed) -- membership for those 3 tranches (plus the 5 real AGs) is tested
directly against `asset_group`, exactly like the 5 real AGs (`infra`'s enum VALUE is
`infrastructure`, not `infra` -- see TRANCHE_ASSET_GROUP_VALUE). This replaces a retired
2026-07-25->27 workaround (ground-truthing membership by citation-grepping each tranche's own
<tranche>_consolidated_closeout_2026_07_25.md body) that silently zeroed out a tranche's whole
membership the moment its closeout doc archived -- a normal, expected lifecycle event -- and
separately cross-contaminated tranches via ordinary `related:`/footnote citations; see
na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md for the
incident this fixed (same root-cause family as
generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md,
the sibling script's identical bug, already fixed there).

# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: never (this class of bug -- grep-based frontmatter/membership sweeps -- has recurred
# twice already; keep the proper-parse version around as the standing tool)
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
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/docs/docspec.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["docspec"] = mod
    spec.loader.exec_module(mod)
    return mod


ds = _load_docspec()

AGS = ["cefi", "defi", "tradfi", "prediction", "sports"]
NON_AG_TRANCHES = ["ao", "ci", "infra"]
ALL_TRANCHES = [*AGS, "cross-cutting", *NON_AG_TRANCHES]

# infra's TRANCHE name (CLI --tranche, closeout-doc prefix) does not match its actual `asset_group`
# enum VALUE, which is `infrastructure` (plans/PLAN_FORMAT.md's ASSET_GROUP enum has no "infra"
# member) -- ao/ci have no such mismatch (their enum values equal their tranche names).
TRANCHE_ASSET_GROUP_VALUE = {"infra": "infrastructure"}

DOC_TREES = ["plans/active/*.md", "plans/active/issues/*.md"]

DATA_EPICS = {
    "infrastructure_master",
    "instruments_master",
    "mtds_mdps_master",
    "manifest_master",
    "features_and_ml_master",
}

# [-*] bullet, standard case. A star-bullet variant is confirmed live
# (defi_expected_unattempted_backlog_1m_2026_07_03.md -- exactly the "non-canonical checkbox format
# the regex missed" failure class this script exists to avoid).
CHECKBOX_RE = re.compile(r"^\s*[-*]\s*\[ \]", re.MULTILINE)


def _iter_docs() -> list[Path]:
    seen: set[Path] = set()
    out: list[Path] = []
    for pat in DOC_TREES:
        for p in PM.glob(pat):
            rel = p.relative_to(PM).as_posix()
            if p.is_file() and p not in seen and not rel.startswith(".claude/"):
                seen.add(p)
                out.append(p)
    return sorted(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tranche", choices=[*ALL_TRANCHES, "all"], default="all")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a summary table")
    args = parser.parse_args(argv)

    records = []
    for path in _iter_docs():
        rel = path.relative_to(PM).as_posix()
        try:
            fm, _ = ds.parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        except yaml.YAMLError:
            continue
        if fm is None:
            continue
        assigned_vm = fm.get("assigned_vm")
        status = fm.get("status")
        if not (isinstance(assigned_vm, str) and assigned_vm.strip().upper() == "NA"):
            continue
        if status not in ("active", "open"):
            continue

        asset_group = fm.get("asset_group") or []
        if isinstance(asset_group, str):
            asset_group = [asset_group]
        parent_epic = fm.get("parent_epic") or ""
        basename = path.name

        open_todos = len(CHECKBOX_RE.findall(path.read_text(encoding="utf-8", errors="replace")))

        tranches: list[str] = []
        for ag in AGS:
            if ag in asset_group:
                tranches.append(ag)
        for t in NON_AG_TRANCHES:
            # ao/ci/infra are real dedicated asset_group enum values (2026-07-27 schema expansion) --
            # tested identically to the 5 real AGs, not via the retired closeout-citation proxy (see
            # na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md).
            if TRANCHE_ASSET_GROUP_VALUE.get(t, t) in asset_group:
                tranches.append(t)
        if "meta" in asset_group and not tranches:
            tranches.append("infra")  # default fold per ag_closeout_audit_scope_widening_triage precedent
        if "cross-cutting" in asset_group and (parent_epic in DATA_EPICS or not tranches):
            tranches.append("cross-cutting")

        records.append(
            {
                "path": rel,
                "basename": basename,
                "doc_type": fm.get("doc_type"),
                "asset_group": asset_group,
                "parent_epic": parent_epic,
                "open_todos": open_todos,
                "tranches": tranches or ["UNCLASSIFIED"],
            }
        )

    if args.tranche != "all":
        records = [r for r in records if args.tranche in r["tranches"]]

    if args.json:
        print(json.dumps(records, indent=1))
        return 0

    tranches_with_unclassified = [*ALL_TRANCHES, "UNCLASSIFIED"]
    by_tranche: dict[str, list[dict]] = {t: [] for t in tranches_with_unclassified}
    for r in records:
        for t in r["tranches"]:
            by_tranche.setdefault(t, []).append(r)

    total_docs = len(records)
    total_zero = sum(1 for r in records if r["open_todos"] == 0)
    print(f"Total NA+active/open docs: {total_docs}  (zero-open-todo: {total_zero})")
    for t in tranches_with_unclassified:
        docs = by_tranche.get(t, [])
        zero = sum(1 for r in docs if r["open_todos"] == 0)
        print(f"  {t:14s} {len(docs):4d} docs  ({zero} zero-open-todo)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
