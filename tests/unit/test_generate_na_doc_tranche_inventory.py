"""Unit tests for scripts/plan-hygiene/generate_na_doc_tranche_inventory.py.

Covers the fix for
plans/active/issues/na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md:
the ao/ci/infra (and cross-cutting) tranche-membership test used to be defined by citation --
whether a doc's basename appeared anywhere in the body of that tranche's own
`<tranche>_consolidated_closeout_2026_07_25.md` (a retired 2026-07-25->27 workaround, same root-cause
family as generate_ag_closeout_audit_candidates.py's identical bug, fixed separately in
unified-trading-pm@e88c41727). Two independent failure modes:

1. Hard zero once the closeout doc archives (`ci`'s own closeout archived 2026-07-28, a normal,
   expected lifecycle event) -- `_cited_basenames()` on a nonexistent path silently returns an empty
   set, so every candidate fails the membership test with no error.
2. Cross-contamination even while the closeout doc is still active: an ordinary `related:`-frontmatter
   link or footnote citation inside one tranche's closeout doc got treated as a membership CLAIM on the
   cited doc, leaking coordinator docs into the wrong tranche and (via a tautological `peer_cited`
   self-veto) dropping their real `cross-cutting` tag entirely.

These tests prove the fix (direct `asset_group` testing, matching the 5 real AGs, with no closeout-doc
file read at all):
- ao/ci/infra membership no longer depends on any closeout-doc file existing;
- a doc is never assigned a tranche merely because some OTHER doc's prose cites its basename;
- `infra`'s asset_group VALUE is `infrastructure` (not `infra`);
- `cross-cutting` is assigned via direct tag + the DATA_EPICS/no-other-tranche fallback, not a
  citation proxy -- and an AG-tagged doc that ALSO carries `cross-cutting` is not double-counted
  unless its parent_epic is a genuine data epic.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "plan-hygiene" / "generate_na_doc_tranche_inventory.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_na_doc_tranche_inventory", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["generate_na_doc_tranche_inventory"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()

FRONTMATTER_TMPL = """---
doc_type: issue
title: "{title}"
summary: test fixture
status: {status}
nature: issue
asset_group: [{asset_group}]
stage: [meta]
repos: []
scope: [engineer]
tags: []
related: []
created: "2026-07-01"
parent_epic: {parent_epic}
assigned_vm: {assigned_vm}
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.1
assigned_role: infra
drift_direction: none
depends_on: []
resolved_by:
locked_by:
supersedes:
superseded_by:
---

# {title}

Fixture doc for test_generate_na_doc_tranche_inventory.py. Cites a peer basename in prose to prove
citation alone must NOT confer tranche membership: peer_citation_target_2026_07_01.md.

- [ ] open todo one
"""


def _write_doc(
    root: Path,
    rel: str,
    *,
    title: str,
    status: str = "open",
    asset_group: str,
    parent_epic: str = "infrastructure_master",
    assigned_vm: str = "NA",
) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        FRONTMATTER_TMPL.format(
            title=title,
            status=status,
            asset_group=asset_group,
            parent_epic=parent_epic,
            assigned_vm=assigned_vm,
        ),
        encoding="utf-8",
    )
    return p


def _run_json(tranche: str = "all") -> list[dict]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = MOD.main(["--tranche", tranche, "--json"])
    assert rc == 0
    return json.loads(buf.getvalue())


def _tranches_of(records: list[dict], basename: str) -> list[str]:
    for r in records:
        if r["basename"] == basename:
            return r["tranches"]
    raise AssertionError(f"{basename} not present in inventory output")


@pytest.mark.parametrize(
    ("tranche", "asset_group_value"),
    [("ci", "ci"), ("ao", "ao"), ("infra", "infrastructure")],
)
def test_non_ag_tranche_membership_needs_no_closeout_doc(monkeypatch, tmp_path, tranche, asset_group_value):
    """The exact reported failure: membership must not depend on
    `plans/active/<tranche>_consolidated_closeout_2026_07_25.md` existing at all -- no such file is
    ever written in this fixture corpus, mirroring the post-archival state."""
    _write_doc(
        tmp_path,
        f"plans/active/issues/{tranche}_member_doc_2026_07_01.md",
        title=f"{tranche} member doc",
        asset_group=asset_group_value,
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json(tranche)
    assert len(records) == 1, f"tranche={tranche}: expected exactly the one fixture doc, got {records}"
    assert records[0]["tranches"] == [tranche]


def test_infra_tranche_asset_group_value_is_infrastructure_not_infra(monkeypatch, tmp_path):
    """`infra` the TRANCHE name != `infrastructure` the asset_group VALUE (plans/PLAN_FORMAT.md's
    ASSET_GROUP enum has no `infra` member). A doc tagged `asset_group: [infrastructure]` must land in
    the `infra` tranche."""
    _write_doc(
        tmp_path,
        "plans/active/issues/real_infra_doc_2026_07_01.md",
        title="real infra doc",
        asset_group="infrastructure",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json("infra")
    assert len(records) == 1
    assert records[0]["tranches"] == ["infra"]


def test_ag_tranche_membership_unaffected_by_the_fix(monkeypatch, tmp_path):
    """Regression guard: the 5 real AGs (e.g. cefi) keep working exactly as before -- this fix only
    touches the ao/ci/infra/cross-cutting branches."""
    _write_doc(
        tmp_path,
        "plans/active/issues/cefi_member_doc_2026_07_01.md",
        title="cefi member doc",
        asset_group="cefi",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json("cefi")
    assert len(records) == 1
    assert records[0]["tranches"] == ["cefi"]


def test_citation_in_a_peer_closeout_doc_does_not_confer_membership(monkeypatch, tmp_path):
    """The cross-contamination half of the bug: a doc must never be assigned a tranche merely because
    some OTHER tranche's closeout/hub doc happens to cite its basename in `related:` or prose. Build an
    `infra`-tagged closeout-shaped doc that cites a `ci`-tagged doc's basename in its body, and confirm
    the `ci` doc is NOT also tagged `infra`."""
    cited_name = "ci_member_doc_2026_07_01.md"
    _write_doc(
        tmp_path,
        f"plans/active/issues/{cited_name}",
        title="ci member doc",
        asset_group="ci",
    )
    citer = _write_doc(
        tmp_path,
        "plans/active/infra_consolidated_closeout_2026_07_25.md",
        title="infra consolidated closeout",
        status="active",
        asset_group="infrastructure",
    )
    # Graft an explicit citation of the ci doc's basename into the infra closeout's body (the exact
    # shape that used to leak membership: a related:/footnote-style basename mention).
    citer.write_text(citer.read_text(encoding="utf-8") + f"\nSee also {cited_name} for background.\n", encoding="utf-8")
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json("all")
    assert _tranches_of(records, cited_name) == ["ci"], "citation in a peer tranche's closeout leaked membership"
    assert _tranches_of(records, "infra_consolidated_closeout_2026_07_25.md") == ["infra"]


def test_cross_cutting_solo_tag_is_assigned_without_data_epic_or_citation(monkeypatch, tmp_path):
    """Mirrors june_2026_vintage_audit_findings_2026_07_27.md's real shape: a doc tagged only
    `cross-cutting`, parent_epic NOT a data epic, with no citation anywhere, must still land in
    `cross-cutting` (the tautological `peer_cited` self-veto used to be able to drop this)."""
    _write_doc(
        tmp_path,
        "plans/active/issues/cc_solo_doc_2026_07_01.md",
        title="cross-cutting solo doc",
        asset_group="cross-cutting",
        parent_epic="plan_hygiene_master",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json("cross-cutting")
    assert len(records) == 1
    assert records[0]["tranches"] == ["cross-cutting"]


def test_ag_tagged_doc_with_cross_cutting_is_not_double_counted_unless_data_epic(monkeypatch, tmp_path):
    """Mirrors ag_closeout_audit_rollout_2026_07_25.md's real shape: a doc tagged BOTH a real AG and
    `cross-cutting`, with a non-data-epic parent, belongs to the AG tranche only. The same doc with a
    genuine DATA_EPICS parent belongs to BOTH (multi-tranche membership preserved)."""
    _write_doc(
        tmp_path,
        "plans/active/issues/multi_tag_non_data_epic_2026_07_01.md",
        title="multi-tag, non-data-epic",
        asset_group="cefi, cross-cutting",
        parent_epic="agent_operating_framework_master",
    )
    _write_doc(
        tmp_path,
        "plans/active/issues/multi_tag_data_epic_2026_07_01.md",
        title="multi-tag, data epic",
        asset_group="cefi, cross-cutting",
        parent_epic="infrastructure_master",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json("all")
    assert _tranches_of(records, "multi_tag_non_data_epic_2026_07_01.md") == ["cefi"]
    assert _tranches_of(records, "multi_tag_data_epic_2026_07_01.md") == ["cefi", "cross-cutting"]
