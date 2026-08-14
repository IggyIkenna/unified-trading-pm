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
# Content-hash (frontmatter-blind) incremental-skip tests
#
# Covers the fix from
# plans/archive/issues/na_eligibility_incremental_diff_false_positive_on_frontmatter_only_backfills_2026_08_03.md:
# a context_scope: or other frontmatter-only backfill commit must NOT force a
# Phase-1 re-read on the next na-eligibility-audit run.
# ---------------------------------------------------------------------------

# Body template already includes a Progress Log section so tests can append individual marker
# lines without the section header itself changing the hash.
_BODY_TMPL = """
# {title}

Fixture body — only this section matters for body_content_hash.

- [ ] open todo

## Progress Log
"""

_FM_TMPL = """---
doc_type: issue
title: "{title}"
summary: test fixture
status: open
nature: issue
asset_group: [infrastructure]
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
{extra_fm}---
{body}"""


def _write_hash_doc(
    root: Path,
    name: str,
    *,
    title: str = "hash test doc",
    extra_fm: str = "",
    body: str | None = None,
    progress_log: str = "",
) -> Path:
    """Write a synthetic NA doc with optional verdict marker in the body."""
    resolved_body = (body if body is not None else _BODY_TMPL.format(title=title)) + progress_log
    p = root / "plans" / "active" / "issues" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        _FM_TMPL.format(title=title, extra_fm=extra_fm, body=resolved_body),
        encoding="utf-8",
    )
    return p


def _hash_record(records: list[dict], basename: str) -> dict:
    for r in records:
        if r["basename"] == basename:
            return r
    raise AssertionError(f"{basename} not found in records")


def test_strip_frontmatter_removes_yaml_block():
    """strip_frontmatter must return only the body, not the --- delimiters or YAML."""
    text = "---\ntitle: foo\nstatus: open\n---\n# Heading\n\nbody here\n"
    body = MOD.strip_frontmatter(text)
    assert "title: foo" not in body
    assert "# Heading" in body
    assert body.startswith("# Heading") or body.startswith("\n# Heading")


def test_strip_frontmatter_no_frontmatter_returns_unchanged():
    """A doc without a --- delimiter must be returned as-is."""
    text = "# No frontmatter\n\nPlain body.\n"
    assert MOD.strip_frontmatter(text) == text


def test_body_content_hash_stable_across_frontmatter_change():
    """The hash of two docs that differ only in frontmatter must be identical.

    This is the core invariant: a context_scope: backfill must NOT change the hash.
    """
    base = "---\ntitle: doc\nstatus: open\n---\n# Body\n\n- [ ] todo\n"
    with_extra_fm = "---\ntitle: doc\nstatus: open\ncontext_scope: [/some/path]\n---\n# Body\n\n- [ ] todo\n"
    assert MOD.body_content_hash(base) == MOD.body_content_hash(with_extra_fm)


def test_body_content_hash_differs_on_body_change():
    """A doc whose body content changed must produce a different hash."""
    v1 = "---\ntitle: doc\n---\n# Body\n\n- [ ] original todo\n"
    v2 = "---\ntitle: doc\n---\n# Body\n\n- [ ] original todo\n- [ ] new todo added\n"
    assert MOD.body_content_hash(v1) != MOD.body_content_hash(v2)


def test_body_content_hash_stable_across_context_scout_marker_line():
    """A context-scout-only touch (its dated Progress Log bookkeeping line) must not
    change the hash -- the false-positive class from
    na_eligibility_hash_blind_to_context_scout_progress_log_line_2026_08_09.md: 44% of
    one tranche's docs (11/25) were needlessly re-classified because context-scout's
    line survived _VERDICT_MARKER_LINE_RE's stripping (it only matched
    na-eligibility-audit's own marker).
    """
    before = "---\ntitle: doc\n---\n# Body\n\n- [ ] a todo\n\n## Progress Log\n\n- **2026-08-01** -- initial content.\n"
    context_scout_line = "- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).\n"
    after_context_scout_touch = before + context_scout_line
    assert MOD.body_content_hash(before) == MOD.body_content_hash(after_context_scout_touch)


def test_body_content_hash_stable_across_multiline_marker():
    """A multi-line verdict marker's own continuation lines must not survive into the
    hashed body -- the bug from
    na_eligibility_multiline_marker_continuation_lines_never_stripped_from_hash_2026_08_10.md:
    _VERDICT_MARKER_LINE_RE stripped only the marker's FIRST line, so the reasoning/
    evidence prose on indented continuation lines (the norm for a real verdict, not the
    exception) leaked into every later hash computation. This is the exact invariant the
    issue doc's todo calls for: body_content_hash(body_before_marker) must equal
    body_content_hash(body_before_marker + <the marker written with that exact hash>).
    """
    body_before = "---\ntitle: doc\n---\n# Body\n\n- [ ] a todo\n\n## Progress Log\n\n- **2026-08-01** -- initial.\n"
    h0 = MOD.body_content_hash(body_before)
    multiline_marker = (
        f"- **na-eligibility-audit 2026-08-09** [body-hash:{h0}]: KEEP-NA, valid --\n"
        "  a two-line continuation\n"
        "  explaining why.\n"
    )
    body_after = body_before + multiline_marker
    assert MOD.body_content_hash(body_after) == h0

    # A sibling marker immediately following must still be stripped/parsed independently
    # -- the continuation-lines clause must stop at the next top-level bullet, not eat it.
    sibling_marker = "- **context-scout 2026-08-10**: refreshed context_scope (2 entries).\n"
    body_with_sibling = body_after + sibling_marker
    assert MOD.body_content_hash(body_with_sibling) == h0


def test_incremental_skip_true_when_stored_hash_matches(monkeypatch, tmp_path):
    """A doc with a [body-hash:…] marker whose stored hash equals the current body hash
    must report incremental_skip=True — the primary (no-git) skip path.

    This is the exact false-positive class from the measurement table: a doc that has
    a verdict marker and only received a frontmatter backfill since then should be
    reported as skippable so Phase 1 does not re-read it.

    The fixture already includes a '## Progress Log' section so that only the verdict
    marker LINE itself is appended — which body_content_hash strips — meaning the hash
    is stable across the write.  This mirrors the realistic scenario where the Progress
    Log section pre-exists and only the marker entry is added.
    """
    monkeypatch.setattr(MOD, "PM", tmp_path)
    # Base doc already has a '## Progress Log' section (no marker lines yet).
    doc = _write_hash_doc(tmp_path, "skip_hash_match_2026_07_01.md", title="skip by hash")
    # Compute hash of the doc before any marker is written.
    # body_content_hash strips verdict-marker lines, so this is the stable hash.
    current = MOD.body_content_hash(doc.read_text(encoding="utf-8"))
    # Append just the verdict marker LINE (section header already present in fixture).
    # In production the skill does exactly this: appends one Progress Log entry.
    marker_line = f"- **na-eligibility-audit 2026-08-01** [body-hash:{current}]: KEEP-NA, valid — test\n"
    doc.write_text(doc.read_text(encoding="utf-8") + marker_line, encoding="utf-8")

    records = _run_json()
    rec = _hash_record(records, "skip_hash_match_2026_07_01.md")
    assert rec["incremental_skip"] is True, f"expected skip; stored={current}, current={rec['body_content_hash']}"
    assert rec["verdict_marker_date"] == "2026-08-01"


def test_incremental_skip_false_when_body_changed_after_marker(monkeypatch, tmp_path):
    """A doc whose body changed after the verdict marker must report incremental_skip=False
    even though a [body-hash:…] is present — the stored hash no longer matches.
    """
    monkeypatch.setattr(MOD, "PM", tmp_path)
    doc = _write_hash_doc(tmp_path, "no_skip_body_changed_2026_07_01.md", title="body changed")
    # Compute a STALE hash (of a different body).
    stale_hash = MOD.body_content_hash("---\n---\nstale body content\n")
    marker = f"\n## Progress Log\n\n- **na-eligibility-audit 2026-08-01** [body-hash:{stale_hash}]: KEEP-NA, valid\n"
    doc.write_text(doc.read_text(encoding="utf-8") + marker, encoding="utf-8")

    records = _run_json()
    rec = _hash_record(records, "no_skip_body_changed_2026_07_01.md")
    assert rec["incremental_skip"] is False


def test_incremental_skip_false_when_no_marker(monkeypatch, tmp_path):
    """A doc with no verdict marker at all is always in-scope (incremental_skip=False)."""
    monkeypatch.setattr(MOD, "PM", tmp_path)
    _write_hash_doc(tmp_path, "no_marker_2026_07_01.md", title="no marker doc")

    records = _run_json()
    rec = _hash_record(records, "no_marker_2026_07_01.md")
    assert rec["incremental_skip"] is False
    assert rec["verdict_marker_date"] is None


def test_incremental_skip_false_when_marker_has_no_hash_and_no_git(monkeypatch, tmp_path):
    """A doc with an old-style marker (no [body-hash:…]) and no git history available
    must fall back to incremental_skip=False — in-scope, safe to re-read.

    In the unit-test context, tmp_path has no git repo, so the git fallback returns
    None and the doc is conservatively flagged as in-scope (not skipped).
    """
    monkeypatch.setattr(MOD, "PM", tmp_path)
    marker = "\n## Progress Log\n\n- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid — old format\n"
    _write_hash_doc(tmp_path, "old_marker_no_hash_2026_07_01.md", title="old marker", progress_log=marker)

    records = _run_json()
    rec = _hash_record(records, "old_marker_no_hash_2026_07_01.md")
    assert rec["incremental_skip"] is False
    assert rec["verdict_marker_date"] == "2026-08-01"


def test_body_content_hash_field_always_present_in_json(monkeypatch, tmp_path):
    """body_content_hash must be present on every record in --json output."""
    monkeypatch.setattr(MOD, "PM", tmp_path)
    _write_hash_doc(tmp_path, "hash_field_check_2026_07_01.md", title="hash field check")

    records = _run_json()
    for r in records:
        assert "body_content_hash" in r, f"missing body_content_hash on {r['basename']}"
        assert isinstance(r["body_content_hash"], str) and len(r["body_content_hash"]) == 16
        assert "incremental_skip" in r
        assert isinstance(r["incremental_skip"], bool)
