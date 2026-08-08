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
import hashlib
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


def _owning_tranche_of(records: list[dict], basename: str) -> str:
    for r in records:
        if r["basename"] == basename:
            return r["owning_tranche"]
    raise AssertionError(f"{basename} not present in inventory output")


def test_owning_tranche_single_membership_is_trivial(monkeypatch, tmp_path):
    """A doc with exactly one classified tranche owns itself -- parent_epic never needs to arbitrate."""
    _write_doc(
        tmp_path,
        "plans/active/issues/solo_cefi_doc_2026_07_01.md",
        title="solo cefi doc",
        asset_group="cefi",
        parent_epic="orchestrator_master",  # deliberately wrong epic -- must not matter, only 1 tranche
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json("all")
    assert _owning_tranche_of(records, "solo_cefi_doc_2026_07_01.md") == "cefi"


def test_owning_tranche_multi_membership_uses_parent_epic_not_first_asset_group_entry(monkeypatch, tmp_path):
    """The exact bug this ships to fix: for a genuinely multi-tranche doc, ownership must come from
    `parent_epic`, not from `asset_group`'s list order. Put the AG that should NOT own second in the
    asset_group list, and prove parent_epic (mapped to cross-cutting via instruments_master, a
    DATA_EPICS member) still wins over cefi (the first-listed asset_group value)."""
    _write_doc(
        tmp_path,
        "plans/active/issues/multi_tag_owned_by_epic_2026_07_01.md",
        title="multi-tag, owned by parent_epic",
        asset_group="cefi, cross-cutting",
        parent_epic="instruments_master",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json("all")
    assert _tranches_of(records, "multi_tag_owned_by_epic_2026_07_01.md") == ["cefi", "cross-cutting"]
    assert _owning_tranche_of(records, "multi_tag_owned_by_epic_2026_07_01.md") == "cross-cutting"


def test_owning_tranche_falls_back_to_first_tranche_when_epic_unmapped(monkeypatch, tmp_path):
    """An unknown/blank parent_epic (or one mapped to a tranche the doc isn't otherwise a member of)
    must not raise or assign ownership outside the doc's real classification -- fall back to the first
    classified tranche, matching the pre-fix behaviour. Two real AG tags on one doc is an unusual shape
    (the Orthogonality HARD CHECK discourages it) but the script itself doesn't reject it, so it's a
    clean way to force genuine multi-membership without depending on the cross-cutting/DATA_EPICS path."""
    _write_doc(
        tmp_path,
        "plans/active/issues/multi_tag_unmapped_epic_2026_07_01.md",
        title="multi-tag, unmapped epic",
        asset_group="cefi, sports",
        parent_epic="some_epic_not_in_the_table",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json("all")
    assert _tranches_of(records, "multi_tag_unmapped_epic_2026_07_01.md") == ["cefi", "sports"]
    assert _owning_tranche_of(records, "multi_tag_unmapped_epic_2026_07_01.md") == "cefi"


def test_owned_only_filters_to_the_owning_tranche(monkeypatch, tmp_path):
    """--owned-only against --tranche cross-cutting must include the cross-cutting-owned doc and
    exclude the cefi-owned one, even though both carry `cross-cutting` in their `tranches` list."""
    _write_doc(
        tmp_path,
        "plans/active/issues/owned_by_cross_cutting_2026_07_01.md",
        title="owned by cross-cutting",
        asset_group="cefi, cross-cutting",
        parent_epic="instruments_master",
    )
    _write_doc(
        tmp_path,
        "plans/active/issues/owned_by_cefi_2026_07_01.md",
        title="owned by cefi",
        asset_group="cefi, cross-cutting",
        parent_epic="cefi_master",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = MOD.main(["--tranche", "cross-cutting", "--owned-only", "--json"])
    assert rc == 0
    records = json.loads(buf.getvalue())
    basenames = {r["basename"] for r in records}
    assert basenames == {"owned_by_cross_cutting_2026_07_01.md"}


def test_owned_only_without_specific_tranche_errors(monkeypatch, tmp_path):
    """--owned-only against --tranche all is meaningless (ownership is tranche-relative) -- must fail
    fast with a usage error rather than silently ignoring the flag."""
    monkeypatch.setattr(MOD, "PM", tmp_path)
    with pytest.raises(SystemExit):
        MOD.main(["--tranche", "all", "--owned-only", "--json"])


# ---------------------------------------------------------------------------
# Content-hash (frontmatter-blind) incremental mode
# Covers: na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md
# ---------------------------------------------------------------------------

_BODY_ONLY = "\n# Test doc\n\n- [ ] open todo\n"
_FM_BASE = (
    "---\n"
    "doc_type: issue\n"
    'title: "hash test"\n'
    "summary: fixture\n"
    "status: open\n"
    "nature: issue\n"
    "asset_group: [infrastructure]\n"
    "stage: [meta]\n"
    "repos: []\n"
    "scope: [engineer]\n"
    "tags: []\n"
    "related: []\n"
    'created: "2026-08-01"\n'
    "parent_epic: infrastructure_master\n"
    "assigned_vm: NA\n"
    "execution_scope: local-only\n"
    "priority: P3\n"
    "estimate_class: refactor\n"
    "estimate_baseline_ai_days: 0.1\n"
    "estimate_calibrated_ai_days: 0.1\n"
    "assigned_role: infra\n"
    "drift_direction: none\n"
    "depends_on: []\n"
    "resolved_by:\n"
    "locked_by:\n"
    "supersedes:\n"
    "superseded_by:\n"
    "---"
)
_FM_WITH_SCOPE = _FM_BASE.replace("---\n", "---\n", 1).replace(
    "depends_on: []\n",
    "depends_on: []\n"
    "context_scope: [scripts/plan-hygiene/generate_na_doc_tranche_inventory.py]\n",
)


def _make_doc_text(body: str, marker_hash: str | None = None) -> str:
    """Build a full doc string with optional verdict marker embedding a body-hash."""
    marker = ""
    if marker_hash is not None:
        marker = (
            f"\n\n## Progress Log\n\n"
            f"- **na-eligibility-audit 2026-08-08 (infra tranche)**: "
            f"KEEP-NA, valid — fixture (body-hash={marker_hash})\n"
        )
    return _FM_BASE + body + marker


def _write_doc_text(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _run_incremental_json(monkeypatch, tmp_path: Path) -> list[dict]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = MOD.main(["--incremental", "--json"])
    assert rc == 0
    return json.loads(buf.getvalue())


def test_body_hash_stable_across_frontmatter_only_change():
    """_compute_body_hash is frontmatter-blind: adding context_scope: leaves the hash unchanged.

    This is the core invariant that makes the incremental-skip scheme immune to future
    frontmatter-only maintenance skills (context-scout, docs-reconciler, etc.).
    """
    text_before = _FM_BASE + _BODY_ONLY
    text_after = _FM_WITH_SCOPE + _BODY_ONLY
    assert MOD._compute_body_hash(text_before) == MOD._compute_body_hash(text_after)


def test_body_hash_changes_when_body_changes():
    """_compute_body_hash produces a different value when the document body (not frontmatter) changes."""
    text_original = _FM_BASE + _BODY_ONLY
    text_changed = _FM_BASE + _BODY_ONLY + "- [ ] one more todo added to body\n"
    assert MOD._compute_body_hash(text_original) != MOD._compute_body_hash(text_changed)


def test_parse_marker_hash_returns_none_when_no_marker():
    """_parse_marker_hash returns None for a doc that has no verdict marker at all."""
    assert MOD._parse_marker_hash(_FM_BASE + _BODY_ONLY) is None


def test_parse_marker_hash_returns_none_for_old_format_marker():
    """_parse_marker_hash returns None for the pre-hash marker format (no body-hash token)."""
    text = (
        _FM_BASE
        + _BODY_ONLY
        + "\n- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — reason\n"
    )
    assert MOD._parse_marker_hash(text) is None


def test_parse_marker_hash_extracts_hash():
    """_parse_marker_hash correctly extracts the body-hash from a new-format marker."""
    body_hash = hashlib.sha256(b"body text").hexdigest()[:12]
    text = (
        _FM_BASE
        + _BODY_ONLY
        + f"\n- **na-eligibility-audit 2026-08-08 (infra tranche)**: KEEP-NA (body-hash={body_hash})\n"
    )
    assert MOD._parse_marker_hash(text) == body_hash


def test_incremental_skip_true_when_hash_matches(monkeypatch, tmp_path):
    """--incremental sets incremental_skip=True when the marker's body-hash matches the current body."""
    body_hash = MOD._compute_body_hash(_FM_BASE + _BODY_ONLY)
    text = _make_doc_text(_BODY_ONLY, marker_hash=body_hash)
    _write_doc_text(tmp_path, "plans/active/issues/hash_match_doc_2026_08_08.md", text)
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_incremental_json(monkeypatch, tmp_path)
    assert len(records) == 1
    assert records[0]["incremental_skip"] is True
    assert records[0]["body_hash"] == body_hash


def test_incremental_skip_false_when_body_changed_since_marker(monkeypatch, tmp_path):
    """--incremental sets incremental_skip=False when the body has changed since the marker hash was recorded."""
    old_body = "\n# Old body\n\n- [ ] original todo\n"
    old_hash = MOD._compute_body_hash(_FM_BASE + old_body)
    # Body was then changed (new todo added) after the marker was written
    new_body = old_body + "- [ ] additional todo added after verdict\n"
    text = _make_doc_text(new_body, marker_hash=old_hash)
    _write_doc_text(tmp_path, "plans/active/issues/body_changed_doc_2026_08_08.md", text)
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_incremental_json(monkeypatch, tmp_path)
    assert len(records) == 1
    assert records[0]["incremental_skip"] is False


def test_incremental_skip_false_when_no_hash_marker(monkeypatch, tmp_path):
    """--incremental sets incremental_skip=False for old-format markers (no body-hash token).

    Old markers (pre-hash-scheme) require a fresh verdict to update the marker with a hash;
    they must never be silently skipped just because they have a date-based marker.
    """
    text = (
        _make_doc_text(_BODY_ONLY, marker_hash=None).rstrip()
        + "\n\n- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — reason\n"
    )
    _write_doc_text(tmp_path, "plans/active/issues/old_marker_doc_2026_08_08.md", text)
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_incremental_json(monkeypatch, tmp_path)
    assert len(records) == 1
    assert records[0]["incremental_skip"] is False


def test_body_hash_emitted_without_incremental_flag(monkeypatch, tmp_path):
    """body_hash is always present in JSON output, even without --incremental, so the skill can
    write the hash token to the marker after a Phase-1 verdict without needing a second flag."""
    _write_doc(
        tmp_path,
        "plans/active/issues/body_hash_always_doc_2026_08_08.md",
        title="body_hash always",
        asset_group="infrastructure",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)

    records = _run_json()
    assert len(records) == 1
    assert "body_hash" in records[0]
    assert len(records[0]["body_hash"]) == 12  # 12-hex-char SHA256 prefix
    assert "incremental_skip" not in records[0]


def test_incremental_skip_is_frontmatter_blind_for_real_measurement_docs():
    """Verify the 5 docs from the measurement table: a context_scope:-only addition does not
    change the body hash, confirming that -- once these docs have their markers updated with
    hashes -- they will correctly report as incremental_skip=True after a context-scout pass.

    This test does NOT require the docs to currently carry hashed markers; it simply validates
    the key property (_compute_body_hash is frontmatter-blind) against real doc content.
    Source: na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md
    measurement table (5 false-positive docs from the 2026-08-03 infra-tranche run).
    """
    pm = REPO_ROOT
    docs = [
        pm / "plans/active/issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md",
        pm / "plans/active/issues/plan_reconcile_autonomous_sweep_2026_07_30.md",
        pm / "plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md",
    ]
    archive_docs = [
        pm / "plans/archive/issues/prod_vm_launch_missing_service_account_user_grant_2026_08_02.md",
        pm / "plans/archive/issues/stale_agentwork_scratch_clone_not_deletable_unpushed_stashes_2026_07_30.md",
    ]
    for path in docs + archive_docs:
        if not path.exists():
            pytest.skip(f"Measurement doc not found (may have been archived): {path.name}")
        text = path.read_text(encoding="utf-8")
        # Simulate a context_scope: backfill by inserting one field into the frontmatter
        _scope_line = "\ncontext_scope: [scripts/plan-hygiene/generate_na_doc_tranche_inventory.py]"
        text_with_scope = text.replace("\ndepends_on:", _scope_line + "\ndepends_on:", 1)
        if text_with_scope == text:
            # depends_on not present; inject before another reliable frontmatter field
            text_with_scope = text.replace("\nassigned_role:", _scope_line + "\nassigned_role:", 1)
        original_hash = MOD._compute_body_hash(text)
        modified_hash = MOD._compute_body_hash(text_with_scope)
        assert original_hash == modified_hash, (
            f"{path.name}: body hash changed after frontmatter-only edit — "
            f"_compute_body_hash is not correctly stripping frontmatter"
        )
