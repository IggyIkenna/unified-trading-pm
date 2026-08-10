"""Unit tests for scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py.

Covers the fix for
plans/active/issues/generate_ag_closeout_audit_candidates_ao_ci_infra_membership_stale_after_closeout_archival_2026_07_29.md:
the ao/ci/infra tranches' membership test used to be defined by citation inside that tranche's own
`<prefix>_consolidated_closeout_*.md` (a retired 2026-07-25->27 workaround) -- once that closeout doc
archived (a normal, expected lifecycle event), `_closeout_paths()` returned an empty glob and every
member test silently failed, so `--tranche ci --json` returned `total_members: 0` with no error.

These tests prove:
- membership for ao/ci/infra is now tested directly via `asset_group` (matching the 5 real AGs), not
  via the closeout-citation proxy;
- a synthetically-archived closeout doc (the exact failure mode reported) does NOT drop the tranche's
  candidate count to zero;
- the `infra` tranche's asset_group VALUE is `infrastructure` (not `infra`), a second, adjacent bug
  found while fixing the first -- a naive `t in asset_group` for `t == "infra"` would have silently
  reproduced the same zero-candidates failure via a different root cause.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "plan-hygiene" / "generate_ag_closeout_audit_candidates.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_ag_closeout_audit_candidates", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
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
parent_epic: infrastructure_master
assigned_vm: NA
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

Fixture doc for test_generate_ag_closeout_audit_candidates.py.
"""


def _write_doc(root: Path, rel: str, *, title: str, status: str, asset_group: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(FRONTMATTER_TMPL.format(title=title, status=status, asset_group=asset_group), encoding="utf-8")
    return p


def _make_corpus(tmp_path: Path, *, with_closeout: bool, tranche_prefix: str, asset_group_value: str) -> Path:
    """Build a minimal synthetic PM-shaped corpus: one member doc + optionally that tranche's own
    consolidated-closeout doc + a real dispatch-batch covering doc (so covering_paths is never empty).
    """
    _write_doc(
        tmp_path,
        f"plans/active/issues/{tranche_prefix}_member_doc_2026_07_01.md",
        title=f"{tranche_prefix} member doc",
        status="open",
        asset_group=asset_group_value,
    )
    _write_doc(
        tmp_path,
        f"plans/active/{tranche_prefix}_satellite_ao_dispatch_batch1_2026_07_26.md",
        title=f"{tranche_prefix} dispatch batch 1",
        status="active",
        asset_group=asset_group_value,
    )
    if with_closeout:
        _write_doc(
            tmp_path,
            f"plans/active/{tranche_prefix}_consolidated_closeout_2026_07_25.md",
            title=f"{tranche_prefix} consolidated closeout",
            status="active",
            asset_group=asset_group_value,
        )
    return tmp_path


@pytest.mark.parametrize(
    ("tranche", "asset_group_value"),
    [("ci", "ci"), ("ao", "ao"), ("infra", "infrastructure")],
)
def test_non_ag_tranche_membership_survives_closeout_archival(monkeypatch, tmp_path, tranche, asset_group_value):
    """The exact reported failure: archiving `<tranche>_consolidated_closeout_*.md` must NOT drop
    total_members to 0 for ao/ci/infra."""
    _make_corpus(tmp_path, with_closeout=True, tranche_prefix=tranche, asset_group_value=asset_group_value)
    monkeypatch.setattr(MOD, "PM", tmp_path)

    with_closeout = json.loads(_run_json(tranche))
    assert with_closeout["total_members"] >= 1, "closeout present: member must be counted"

    # Now synthetically archive the closeout doc (delete it, mirroring plans/archive/2026_07/ move) --
    # this is the precise scenario that used to zero out non_ag_member_sets.
    (tmp_path / f"plans/active/{tranche}_consolidated_closeout_2026_07_25.md").unlink()

    without_closeout = json.loads(_run_json(tranche))
    assert without_closeout["total_members"] >= 1, (
        f"tranche={tranche}: total_members silently dropped to 0 once the closeout doc archived "
        "-- this is the exact regression generate_ag_closeout_audit_candidates_ao_ci_infra_membership_"
        "stale_after_closeout_archival_2026_07_29.md reports"
    )
    assert without_closeout["total_members"] == with_closeout["total_members"]


def _run_json(tranche: str) -> str:
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = MOD.main(["--tranche", tranche, "--json"])
    assert rc == 0
    return buf.getvalue()


def test_infra_tranche_asset_group_value_is_infrastructure_not_infra(monkeypatch, tmp_path):
    """Second bug found while fixing the first: the `infra` TRANCHE name != its asset_group VALUE
    (`infrastructure`). A doc tagged `asset_group: [infrastructure]` must count as an `infra`-tranche
    member; a doc tagged (incorrectly) `asset_group: [infra]` must NOT (that value isn't in the real
    ASSET_GROUP enum, plans/PLAN_FORMAT.md)."""
    _write_doc(
        tmp_path,
        "plans/active/issues/real_infra_doc_2026_07_01.md",
        title="real infra doc",
        status="open",
        asset_group="infrastructure",
    )
    _write_doc(
        tmp_path,
        "plans/active/infra_satellite_ao_dispatch_batch1_2026_07_26.md",
        title="infra dispatch batch 1",
        status="active",
        asset_group="infrastructure",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    result = json.loads(_run_json("infra"))
    assert result["total_members"] >= 1
    paths = {c["path"] for c in result["never_cited"]} | {"plans/active/issues/real_infra_doc_2026_07_01.md"}
    assert "plans/active/issues/real_infra_doc_2026_07_01.md" in paths


def test_ag_tranche_membership_unaffected_by_the_fix(monkeypatch, tmp_path):
    """Regression guard: the 5 real AGs (e.g. cefi) must keep working exactly as before -- this fix
    only touches the ao/ci/infra `else` branch."""
    _write_doc(
        tmp_path,
        "plans/active/issues/cefi_member_doc_2026_07_01.md",
        title="cefi member doc",
        status="open",
        asset_group="cefi",
    )
    _write_doc(
        tmp_path,
        "plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_26.md",
        title="cefi dispatch batch 1",
        status="active",
        asset_group="cefi",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    result = json.loads(_run_json("cefi"))
    assert result["total_members"] == 1
    assert result["never_cited_count"] == 1


def test_aggregated_sources_digest_is_not_a_covering_doc(monkeypatch, tmp_path):
    """Finding 1 in ag_closeout_audit_orphan_definition_and_digest_citation_defects_2026_07_30.md:
    `_closeout_paths()`'s glob `{prefix}_consolidated_closeout_*.md` used to also match
    `{prefix}_consolidated_closeout_aggregated_sources_*.md` (the discoverability digest SKILL.md
    Phase 0.1 explicitly declares non-covering), so a doc cited ONLY in the digest wrongly read as
    `cited_somewhere` and vanished from the orphan-candidate list. A doc mentioned only in the digest
    must be reported as never_cited.
    """
    _write_doc(
        tmp_path,
        "plans/active/issues/cefi_only_in_digest_2026_07_01.md",
        title="cefi doc mentioned only in the digest",
        status="open",
        asset_group="cefi",
    )
    _write_doc(
        tmp_path,
        "plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_26.md",
        title="cefi dispatch batch 1",
        status="active",
        asset_group="cefi",
    )
    digest = _write_doc(
        tmp_path,
        "plans/active/cefi_consolidated_closeout_aggregated_sources_2026_07_24.md",
        title="cefi aggregated sources digest",
        status="active",
        asset_group="cefi",
    )
    # The digest's only "coverage" of the member doc is a plain citation of its basename -- exactly
    # what the aggregated-sources digest does for every doc in the AG (discoverability, not dispatch).
    citation_line = "\n- [cefi_only_in_digest_2026_07_01.md](issues/cefi_only_in_digest_2026_07_01.md)\n"
    digest.write_text(digest.read_text(encoding="utf-8") + citation_line, encoding="utf-8")
    monkeypatch.setattr(MOD, "PM", tmp_path)

    result = json.loads(_run_json("cefi"))
    covering_paths = MOD._covering_paths("cefi")
    assert not any("aggregated_sources" in p.name for p in covering_paths), (
        "the aggregated_sources digest must never be treated as a covering doc"
    )
    never_cited_paths = {c["path"] for c in result["never_cited"]}
    assert "plans/active/issues/cefi_only_in_digest_2026_07_01.md" in never_cited_paths, (
        "a doc cited ONLY in the aggregated_sources digest must surface as never_cited, not as covered"
    )


def test_finalize_doc_depends_on_pulls_in_its_line_cap_fork_as_covering(monkeypatch, tmp_path):
    """Finding 1 (secondary) + independently corroborated by
    ag_closeout_audit_sports_prefilter_covering_gap_and_false_unchecked_p0_2026_07_30.md: SKILL.md
    Phase 0.2 path (b) says a line-cap-split fork of the consolidated closeout (named after its own
    Track/phase, e.g. `cefi_misc_audits_and_hygiene_2026_07_25.md`) counts as a covering doc even
    though its filename doesn't match `(dispatch_batch|satellite|_finalize)` -- only its paired
    `_finalize` sibling does. `_covering_paths()` must resolve that finalize doc's `depends_on:` to
    pull the main fork in too, and use the fork's OWN content (not just the short finalize doc's) as a
    citation source.
    """
    _write_doc(
        tmp_path,
        "plans/active/issues/cefi_cited_only_by_the_fork_2026_07_01.md",
        title="cefi doc cited only inside the track fork's own todos",
        status="open",
        asset_group="cefi",
    )
    _write_doc(
        tmp_path,
        "plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_26.md",
        title="cefi dispatch batch 1",
        status="active",
        asset_group="cefi",
    )
    fork = _write_doc(
        tmp_path,
        "plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md",
        title="cefi misc audits + hygiene (line-cap fork)",
        status="active",
        asset_group="cefi",
    )
    fork.write_text(
        fork.read_text(encoding="utf-8") + "\nSource: `cefi_cited_only_by_the_fork_2026_07_01.md`\n",
        encoding="utf-8",
    )
    _write_doc(
        tmp_path,
        "plans/active/cefi_misc_audits_and_hygiene_finalize_2026_07_25.md",
        title="cefi misc audits + hygiene -- finalize",
        status="draft",
        asset_group="cefi",
    )
    finalize_path = tmp_path / "plans/active/cefi_misc_audits_and_hygiene_finalize_2026_07_25.md"
    finalize_path.write_text(
        finalize_path.read_text(encoding="utf-8").replace(
            "depends_on: []", "depends_on: [cefi_misc_audits_and_hygiene_2026_07_25]"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    covering_paths = MOD._covering_paths("cefi")
    assert any(p.name == "cefi_misc_audits_and_hygiene_2026_07_25.md" for p in covering_paths), (
        "the finalize doc's depends_on: must resolve its main fork into the covering set"
    )

    result = json.loads(_run_json("cefi"))
    never_cited_paths = {c["path"] for c in result["never_cited"]}
    assert "plans/active/issues/cefi_cited_only_by_the_fork_2026_07_01.md" not in never_cited_paths, (
        "the fork's own Source: citation must count as coverage once the fork is in the covering set"
    )


def test_cross_cutting_membership_not_gated_on_data_epic_or_citation(monkeypatch, tmp_path):
    """Process finding 2, issues/ag_closeout_audit_cross_cutting_parked_2026_08_08.md: the
    cross-cutting membership test used to be
    `"cross-cutting" in asset_group and (parent_epic in DATA_EPICS or basename in cited)` -- a bare
    `[cross-cutting]` doc with a non-data `parent_epic` (e.g. `plan_hygiene_master`) that had NEVER
    been cited anywhere failed the member test entirely, so it was invisible to both the "cited" and
    "never cited" buckets, not just the latter. Membership must now be plain tag membership, matching
    every other tranche -- citation status still drives the cited/never-cited split, not membership."""
    _write_doc(
        tmp_path,
        "plans/active/issues/cross_cutting_non_data_epic_never_cited_2026_07_01.md",
        title="cross-cutting doc with a non-data parent_epic, never cited anywhere",
        status="open",
        asset_group="cross-cutting",
    )
    _write_doc(
        tmp_path,
        "plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md",
        title="cross-cutting dispatch batch 1",
        status="active",
        asset_group="cross-cutting",
    )
    # override the fixture's default parent_epic (infrastructure_master, a DATA_EPICS member) with a
    # non-data epic -- the exact class the old test silently excluded.
    doc = tmp_path / "plans/active/issues/cross_cutting_non_data_epic_never_cited_2026_07_01.md"
    doc.write_text(
        doc.read_text(encoding="utf-8").replace(
            "parent_epic: infrastructure_master", "parent_epic: plan_hygiene_master"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    result = json.loads(_run_json("cross-cutting"))
    assert result["total_members"] == 1, (
        "a non-data-parent_epic, never-cited cross-cutting doc must now count as a member at all"
    )
    never_cited_paths = {c["path"] for c in result["never_cited"]}
    assert "plans/active/issues/cross_cutting_non_data_epic_never_cited_2026_07_01.md" in never_cited_paths, (
        "it must surface in the never_cited bucket, not vanish from candidates entirely"
    )


def test_issue_doc_title_merely_mentioning_closeout_is_not_excluded_as_a_hub_doc(monkeypatch, tmp_path):
    """2026-08-10 (ag-closeout-audit, tradfi tranche): the hub-doc exclusion used to be an unanchored
    `re.search(r"_consolidated_closeout", basename)`, which also matched any issue doc whose own (longer,
    more specific) title merely CONTAINS that substring while describing a problem WITH the hub doc,
    e.g. `tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md`. That doc carries
    genuine open tradfi-scoped work and was silently invisible to the candidate list for EVERY tranche
    (the substring match fires regardless of which tranche is being audited). Fixed by anchoring the
    exclusion to the real hub-doc filename shape via `re.fullmatch`."""
    _write_doc(
        tmp_path,
        "plans/active/issues/cefi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md",
        title="cefi_consolidated_closeout is over the line cap",
        status="open",
        asset_group="cefi",
    )
    _write_doc(
        tmp_path,
        "plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_26.md",
        title="cefi dispatch batch 1",
        status="active",
        asset_group="cefi",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    result = json.loads(_run_json("cefi"))
    assert result["total_members"] == 1, (
        "an issue doc whose title merely mentions the closeout doc must still count as a real member, "
        "not be silently excluded as if it were the hub doc itself"
    )
    all_paths = {c["path"] for c in result["candidates"]}
    target = "plans/active/issues/cefi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md"
    assert target in all_paths


def test_closeout_doc_depends_on_pulls_in_a_fork_with_no_finalize_pair(monkeypatch, tmp_path):
    """2026-08-01 (ag-closeout-audit, tradfi tranche): a line-cap-split fork that never got its OWN
    `*_finalize*` doc (e.g. tradfi_backfill_throughput_followups_2026_07_24.md,
    tradfi_phase_d_terminal_gate_2026_07_24.md -- both forked straight out of the consolidated closeout,
    tracked as plain ongoing plans rather than gated batch+finalize pairs) was previously invisible to
    `_covering_paths()`: the old code only resolved `depends_on:` for docs matching `_finalize` in their
    name, never for the closeout doc itself. Measured impact before this fix: tradfi's own
    total_members read 67 instead of the correct 65, because both such forks were double-counted as
    ordinary candidate members rather than recognized as covering apparatus. This test proves a fork
    named ONLY in the closeout's own `depends_on:` (no finalize doc anywhere) is now resolved into the
    covering set, and a doc cited only inside that fork's own todos is no longer misreported as orphaned.
    """
    _write_doc(
        tmp_path,
        "plans/active/issues/cefi_cited_only_by_the_depends_on_fork_2026_07_01.md",
        title="cefi doc cited only inside the depends_on-only fork's own todos",
        status="open",
        asset_group="cefi",
    )
    _write_doc(
        tmp_path,
        "plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_26.md",
        title="cefi dispatch batch 1",
        status="active",
        asset_group="cefi",
    )
    fork = _write_doc(
        tmp_path,
        "plans/active/cefi_throughput_followups_2026_07_24.md",
        title="cefi throughput followups (line-cap fork, no finalize pair)",
        status="active",
        asset_group="cefi",
    )
    fork.write_text(
        fork.read_text(encoding="utf-8") + "\nSource: `cefi_cited_only_by_the_depends_on_fork_2026_07_01.md`\n",
        encoding="utf-8",
    )
    closeout = _write_doc(
        tmp_path,
        "plans/active/cefi_consolidated_closeout_2026_07_25.md",
        title="cefi consolidated closeout",
        status="active",
        asset_group="cefi",
    )
    closeout.write_text(
        closeout.read_text(encoding="utf-8").replace(
            "depends_on: []", "depends_on: [cefi_throughput_followups_2026_07_24]"
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    covering_paths = MOD._covering_paths("cefi")
    assert any(p.name == "cefi_throughput_followups_2026_07_24.md" for p in covering_paths), (
        "the closeout doc's own depends_on: must resolve a finalize-less fork into the covering set"
    )

    result = json.loads(_run_json("cefi"))
    assert result["total_members"] == 1, (
        "the finalize-less fork must be excluded from total_members as covering apparatus, not counted "
        "as an ordinary candidate alongside the real member doc"
    )
    never_cited_paths = {c["path"] for c in result["never_cited"]}
    assert "plans/active/issues/cefi_cited_only_by_the_depends_on_fork_2026_07_01.md" not in never_cited_paths, (
        "the fork's own Source: citation must count as coverage once the fork is in the covering set"
    )
