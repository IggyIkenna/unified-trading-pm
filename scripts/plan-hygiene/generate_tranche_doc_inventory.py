#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: never (this class of bug -- same-line grep for `asset_group:` -- has recurred multiple
# times across sibling scripts; keep the proper-parse version around as the standing shared tool)
"""Full doc inventory for one of the 10 /ag-closeout-audit tranches (cefi/defi/tradfi/prediction/
sports/cross-cutting/ao/ci/infra/ui) -- ANY `assigned_vm`/`status`, unlike
generate_ag_closeout_audit_candidates.py (which filters to orphan-candidates only, excluding covering
docs) and generate_na_doc_tranche_inventory.py (which filters to assigned_vm:NA + status:active/open
only). This is the plain "every doc tagged into this tranche" list `/plan-reconcile <tranche>` and
`/ag-closeout-audit <tranche>` both need for their own corpus-scoping step.

Why this exists: a single-line `rg -l '^asset_group:.*<tranche>'`-style sweep misses a multi-line YAML
block (`asset_group:` on its own line, the tag on an indented continuation, optionally followed by a
`#`-comment) -- confirmed live 2026-08-11 (`plan_reconciler_findings_ui_2026_08_11.md`): a same-line
grep found only 9 `ui`-tagged docs, undercounting the real tranche by at least 2 confirmed misses
(`data_status_tab_and_downloads_remediation_2026_06_16.md`,
`deployment_registry_firestore_migration_2026_07_14.md`, both retagged to `ui` via the exact
`asset_group:\\n  [ui] # corrected ...` shape same-line grep cannot see). This script reuses the same
`docspec.py` (PyYAML) frontmatter parser + membership test as the two sibling scripts above, so all
three agree on tranche membership.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
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
# `infra`'s asset_group enum VALUE is `infrastructure`, not `infra` -- see
# generate_ag_closeout_audit_candidates.py's identical constant for the incident this guards against.
TRANCHE_ASSET_GROUP_VALUE = {"infra": "infrastructure"}


def _iter_docs() -> list[Path]:
    out: list[Path] = []
    for pat in ["plans/active/*.md", "plans/active/issues/*.md"]:
        out.extend(PM.glob(pat))
    return sorted(set(out))


def is_member(asset_group: list[str], tranche: str) -> bool:
    if tranche in AGS or tranche in NON_AG_TRANCHES:
        return TRANCHE_ASSET_GROUP_VALUE.get(tranche, tranche) in asset_group
    if tranche == "cross-cutting":
        return "cross-cutting" in asset_group
    raise ValueError(f"unknown tranche: {tranche}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tranche", choices=ALL_TRANCHES, required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    t = args.tranche

    members = []
    for path in _iter_docs():
        rel = path.relative_to(PM).as_posix()
        try:
            fm, _ = ds.parse_frontmatter(path.read_text(encoding="utf-8", errors="replace"))
        except yaml.YAMLError:
            continue
        if fm is None:
            continue

        asset_group = fm.get("asset_group") or []
        if isinstance(asset_group, str):
            asset_group = [asset_group]

        if not is_member(asset_group, t):
            continue

        members.append(
            {
                "path": rel,
                "basename": path.name,
                "status": fm.get("status"),
                "assigned_vm": fm.get("assigned_vm"),
            }
        )

    members.sort(key=lambda m: m["basename"])

    if args.json:
        print(json.dumps({"tranche": t, "total": len(members), "docs": members}, indent=2))
        return 0

    print(f"tranche={t} total={len(members)}")
    for m in members:
        print(f"  {m['basename']:<70} status={m['status']} assigned_vm={m['assigned_vm']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
