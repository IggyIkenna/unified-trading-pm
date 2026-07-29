#!/usr/bin/env python3
"""Generate the current assigned_vm:NA + status:{active,open} doc inventory, split by the 9
/ag-closeout-audit tranches (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra).

Why this exists: a single-line `grep -lE '^assigned_vm:\\s*$'`-style sweep misses multi-line YAML
values (key on its own line, value on an indented continuation) and any value expressed via YAML
flow/quoting — confirmed live on sports_consolidated_closeout_2026_07_19.md
(na_docs_validity_and_ao_eligibility_audit_2026_07_26.md Phase 0). This script parses frontmatter
properly via scripts/docs/docspec.py (PyYAML) instead of line-grepping, for this and every future
sweep.

ao/ci/infra have no dedicated asset_group value (they stay tagged cross-cutting/infrastructure/meta
at the frontmatter level) -- membership for those 3 tranches is ground-truthed by reading that
tranche's own <tranche>_consolidated_closeout_2026_07_25.md body for cited basenames, per
cursor-configs/skills/ag-closeout-audit/SKILL.md's own classification-mechanism section. This is a
best-effort membership derivation (citation-grep on the closeout doc body), not the full per-doc
content judgment call the skill's Phase 1 agents make -- treat ao/ci/infra counts here as a first
pass, not a final verdict.

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

DOC_TREES = ["plans/active/*.md", "plans/active/issues/*.md"]

CITE_RE = re.compile(r"([a-z0-9_]+_20\d\d_\d\d_\d\d(?:_finalize)?\.md)")

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


def _cited_basenames(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return set(CITE_RE.findall(path.read_text(encoding="utf-8", errors="replace")))


def _find_closeout_doc(tranche: str) -> Path | None:
    """Locate a tranche's own consolidated-closeout doc, active or archived.

    A tranche's closeout digest can be archived once its own todos are done (its archival
    banner explicitly does not mean the tranche's underlying work is done -- see
    ci_consolidated_closeout_2026_07_25.md, archived 2026-07-28) while still being the only
    citation source for that tranche's membership. Falling back to plans/archive/*/ keeps
    membership derivation working after that archival instead of silently reporting 0.
    """
    name = f"{tranche}_consolidated_closeout_2026_07_25.md"
    active = PM / "plans" / "active" / name
    if active.exists():
        return active
    archived = sorted(PM.glob(f"plans/archive/*/{name}"))
    return archived[0] if archived else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tranche", choices=[*ALL_TRANCHES, "all"], default="all")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a summary table")
    args = parser.parse_args(argv)

    # non-AG tranche membership: citation-grep on that tranche's own consolidated-closeout doc
    non_ag_cited = {t: _cited_basenames(_find_closeout_doc(t) or Path("/nonexistent")) for t in NON_AG_TRANCHES}
    peer_cited: set[str] = set()
    for s in non_ag_cited.values():
        peer_cited |= s

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
        non_ag_all_cited = (
            non_ag_cited.get("ao", set()) | non_ag_cited.get("ci", set()) | non_ag_cited.get("infra", set())
        )
        if "cross-cutting" in asset_group and (parent_epic in DATA_EPICS or basename in non_ag_all_cited):
            if basename not in peer_cited:
                tranches.append("cross-cutting")
        elif "cross-cutting" in asset_group and not tranches:
            tranches.append("cross-cutting")
        if "infrastructure" in asset_group or "meta" in asset_group:
            for t in NON_AG_TRANCHES:
                if basename in non_ag_cited[t]:
                    tranches.append(t)
            if not any(t in tranches for t in NON_AG_TRANCHES):
                tranches.append("infra")  # default fold per ag_closeout_audit_scope_widening_triage precedent
        for t in NON_AG_TRANCHES:
            if basename in non_ag_cited[t] and t not in tranches:
                tranches.append(t)

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
