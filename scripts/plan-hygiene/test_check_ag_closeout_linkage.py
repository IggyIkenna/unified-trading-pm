# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_ag_closeout_linkage.py's basename-index perf fix
(pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md, todo B).

THE REGRESSION THIS PREVENTS: `resolve_related_entry` used to run a fresh `rglob` per
fallback-form `related:` entry, called once per entry across the WHOLE corpus in
`build_related_graph`'s loop. Measured 42.7s wall (31.1s kernel/syscall time) for a single
`--only` run on this repo's ~750-doc corpus. Fixed by building one basename index via a
SINGLE `rglob("*.md")` walk, memoized, with `resolve_related_entry` doing O(1) dict lookups
against it instead. These tests pin the resolution semantics (both fallback forms, the
plans/-only scoping for the bare-slug form) so a future edit can't silently change which
file a legacy `related:` entry resolves to while chasing this speed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import check_ag_closeout_linkage as checker


@pytest.fixture(autouse=True)
def _reset_memoized_index(monkeypatch: pytest.MonkeyPatch) -> None:
    # The index is memoized module-globally (deliberately, for the real run's perf) -- each
    # test needs its own PM_DIR, so the cache must not leak between tests.
    monkeypatch.setattr(checker, "_MD_BASENAME_INDEX", None)


@pytest.fixture
def pm_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "pm"
    (root / "plans" / "active" / "issues").mkdir(parents=True)
    (root / "plans" / "archive").mkdir(parents=True)
    (root / "codex" / "05-infrastructure").mkdir(parents=True)
    monkeypatch.setattr(checker, "PM_DIR", root)
    return root


def test_resolves_bare_slug_fallback_scoped_to_plans(pm_dir: Path) -> None:
    target = pm_dir / "plans" / "active" / "issues" / "some_epic_2026_08_01.md"
    target.write_text("content\n", encoding="utf-8")
    from_path = pm_dir / "plans" / "active" / "citer.md"
    from_path.write_text("content\n", encoding="utf-8")

    resolved = checker.resolve_related_entry("some_epic_2026_08_01", from_path)
    assert resolved == target


def test_bare_slug_fallback_ignores_a_same_stem_file_outside_plans(pm_dir: Path) -> None:
    # A same-named .md OUTSIDE plans/ (e.g. under codex/) must never satisfy the bare-slug
    # form -- the original rglob was explicitly scoped to `PM_DIR / "plans"` and the index
    # must preserve that scoping, not just "any file with this basename anywhere".
    (pm_dir / "codex" / "05-infrastructure" / "some_epic_2026_08_01.md").write_text("x\n", encoding="utf-8")
    from_path = pm_dir / "plans" / "active" / "citer.md"
    from_path.write_text("content\n", encoding="utf-8")

    resolved = checker.resolve_related_entry("some_epic_2026_08_01", from_path)
    assert resolved is None


def test_resolves_dot_md_fallback_by_basename_anywhere_under_pm_dir(pm_dir: Path) -> None:
    # The `.md`-suffixed form's fallback searches the WHOLE PM_DIR (matching the original
    # `PM_DIR.rglob(...)`, not scoped to plans/) -- codex counts.
    target = pm_dir / "codex" / "05-infrastructure" / "per-tab-worktrees.md"
    target.write_text("content\n", encoding="utf-8")
    from_path = pm_dir / "plans" / "active" / "citer.md"
    from_path.write_text("content\n", encoding="utf-8")

    resolved = checker.resolve_related_entry("per-tab-worktrees.md", from_path)
    assert resolved == target


def test_dot_md_fallback_prefers_same_directory_relative_resolution_first(pm_dir: Path) -> None:
    sibling = pm_dir / "plans" / "active" / "issues" / "companion.md"
    sibling.write_text("content\n", encoding="utf-8")
    decoy = pm_dir / "codex" / "05-infrastructure" / "companion.md"
    decoy.write_text("content\n", encoding="utf-8")
    from_path = pm_dir / "plans" / "active" / "issues" / "citer.md"
    from_path.write_text("content\n", encoding="utf-8")

    resolved = checker.resolve_related_entry("companion.md", from_path)
    assert resolved == sibling


def test_unresolvable_entry_returns_none(pm_dir: Path) -> None:
    from_path = pm_dir / "plans" / "active" / "citer.md"
    from_path.write_text("content\n", encoding="utf-8")
    assert checker.resolve_related_entry("nothing_named_this", from_path) is None
    assert checker.resolve_related_entry("nothing_named_this.md", from_path) is None


def test_leading_slash_form_is_unaffected_by_the_index(pm_dir: Path) -> None:
    target = pm_dir / "codex" / "05-infrastructure" / "per-tab-worktrees.md"
    target.write_text("content\n", encoding="utf-8")
    from_path = pm_dir / "plans" / "active" / "citer.md"
    from_path.write_text("content\n", encoding="utf-8")

    resolved = checker.resolve_related_entry("/codex/05-infrastructure/per-tab-worktrees.md", from_path)
    assert resolved == target


def test_index_is_built_once_and_reused(pm_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (pm_dir / "plans" / "active" / "issues" / "a.md").write_text("x\n", encoding="utf-8")
    from_path = pm_dir / "plans" / "active" / "citer.md"
    from_path.write_text("content\n", encoding="utf-8")

    calls = {"n": 0}
    real_rglob = Path.rglob

    def _counting_rglob(self: Path, pattern: str):
        if pattern == "*.md":
            calls["n"] += 1
        return real_rglob(self, pattern)

    monkeypatch.setattr(Path, "rglob", _counting_rglob)

    checker.resolve_related_entry("a", from_path)
    checker.resolve_related_entry("a.md", from_path)
    checker.resolve_related_entry("still_nothing", from_path)

    assert calls["n"] == 1


def test_orphan_message_names_archived_coordinator(pm_dir: Path) -> None:
    # An orphan whose AG's closeout family resolves ONLY to an archived coordinator gets a
    # message that NAMES the archived match + flags the tranche may need reopening — not the
    # generic "no path" (regression for ao_consolidated_closeout_2026_08_12.md P2: an archived
    # coordinator took a 10-day investigation to surface; the refused commit must name it).
    archived = pm_dir / "plans" / "archive" / "2026_07" / "ao_consolidated_closeout_2026_07_25.md"
    archived.parent.mkdir(parents=True, exist_ok=True)
    archived.write_text("# ao\nbody that does not mention the orphan stem\n", encoding="utf-8")

    orphan = pm_dir / "plans" / "active" / "issues" / "ao_live_doc_2026_08_01.md"
    orphan.write_text("x\n", encoding="utf-8")
    all_docs = {orphan: {"asset_group": ["ao"], "status": "active", "title": "x"}}
    all_bodies = {orphan: "body\n"}
    family = {"ao": {archived}}

    violations = checker._orphans_for(all_docs, all_bodies, family)
    msg = violations[orphan]
    assert "ARCHIVED" in msg
    assert "ao_consolidated_closeout_2026_07_25.md" in msg
    assert "may need reopening" in msg


def test_orphan_message_stays_generic_when_coordinator_active(pm_dir: Path) -> None:
    # When the tranche has a LIVE coordinator (plans/active), the orphan message stays the
    # generic "no path" — an active coordinator means the fix is a related: link, not a reopen.
    active = pm_dir / "plans" / "active" / "ao_consolidated_closeout_2026_08_12.md"
    active.write_text("# ao\nbody\n", encoding="utf-8")
    archived = pm_dir / "plans" / "archive" / "2026_07" / "ao_consolidated_closeout_2026_07_25.md"
    archived.parent.mkdir(parents=True, exist_ok=True)
    archived.write_text("# ao\nbody\n", encoding="utf-8")

    orphan = pm_dir / "plans" / "active" / "issues" / "ao_live_doc_2026_08_01.md"
    orphan.write_text("x\n", encoding="utf-8")
    all_docs = {orphan: {"asset_group": ["ao"], "status": "active", "title": "x"}}
    all_bodies = {orphan: "body\n"}
    family = {"ao": {active, archived}}

    violations = checker._orphans_for(all_docs, all_bodies, family)
    msg = violations[orphan]
    assert "ARCHIVED" not in msg
    assert "may need reopening" not in msg


def test_has_active_single_ag_docs_true_on_live_member(pm_dir: Path) -> None:
    # A live (non-excluded-status) doc with exactly this single covered asset_group makes the
    # tranche "has live docs" — the population whose commits the closeout gate screens.
    live = pm_dir / "plans" / "active" / "issues" / "cefi_finding_2026_08_01.md"
    live.write_text("x\n", encoding="utf-8")
    all_docs = {live: {"asset_group": ["cefi"], "status": "active", "title": "x"}}
    assert checker._has_active_single_ag_docs("cefi", all_docs) is True


def test_has_active_single_ag_docs_false_when_closed_status(pm_dir: Path) -> None:
    # A doc whose status is closed/terminal (resolved, archived, ...) is NOT a live doc —
    # a tranche with only closed members needs no active coordinator.
    closed = pm_dir / "plans" / "active" / "issues" / "cefi_finding_2026_08_01.md"
    closed.write_text("x\n", encoding="utf-8")
    all_docs = {closed: {"asset_group": ["cefi"], "status": "resolved", "title": "x"}}
    assert checker._has_active_single_ag_docs("cefi", all_docs) is False


def test_has_active_single_ag_docs_ignores_other_ag_and_multi_value(pm_dir: Path) -> None:
    # Only docs tagged with THIS single covered asset_group count: another tranche's live doc
    # is not evidence for cefi, and a multi-value doc is exempt by construction.
    other = pm_dir / "plans" / "active" / "issues" / "defi_finding_2026_08_01.md"
    other.write_text("x\n", encoding="utf-8")
    multi = pm_dir / "plans" / "active" / "issues" / "cross_finding_2026_08_01.md"
    multi.write_text("x\n", encoding="utf-8")
    all_docs = {
        other: {"asset_group": ["defi"], "status": "active", "title": "x"},
        multi: {"asset_group": ["cefi", "defi"], "status": "active", "title": "x"},
    }
    assert checker._has_active_single_ag_docs("cefi", all_docs) is False
    assert checker._has_active_single_ag_docs("defi", all_docs) is True


# --- --diff-base regression coverage -----------------------------------------------------
#
# Regression for ag_closeout_linkage_zero_baseline_recurring_collision_2026_08_14.md: at
# baseline 0, this was a whole-corpus SCALAR ratchet -- ANY single doc landing without a
# related:/body-mention link failed the NEXT unrelated commit's CI, not the commit that
# actually created the gap (unified-trading-pm ships via quickmerge at high concurrent
# velocity, so same-day multi-slot archival races routinely tripped an innocent bystander
# commit). --diff-base fixes this by comparing the orphan SET at HEAD (worktree) against the
# orphan SET at a base ref, flagging only a path that is newly orphaned since that ref.


def _git(pm_dir: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(pm_dir), *args], check=True, capture_output=True, text=True)


def _git_commit_all(pm_dir: Path, message: str) -> str:
    _git(pm_dir, "add", "-A")
    _git(pm_dir, "commit", "-m", message)
    result = subprocess.run(["git", "-C", str(pm_dir), "rev-parse", "HEAD"], check=True, capture_output=True, text=True)
    return result.stdout.strip()


@pytest.fixture
def git_pm_dir(pm_dir: Path) -> Path:
    _git(pm_dir, "init", "-q")
    _git(pm_dir, "config", "user.email", "test@example.com")
    _git(pm_dir, "config", "user.name", "test")
    return pm_dir


_CLOSEOUT_DOC = """---
doc_type: plan
title: AO consolidated closeout
status: active
asset_group: [ao]
---

# ao closeout
body that does not mention any member doc's stem
"""

_LINKED_MEMBER_DOC = """---
doc_type: issue
title: batch5 finalize
status: active
asset_group: [ao]
related: [/plans/active/ao_consolidated_closeout_2026_08_12.md]
---

body
"""

_UNLINKED_MEMBER_DOC = """---
doc_type: issue
title: batch5 finalize
status: active
asset_group: [ao]
---

body
"""


def test_diff_base_does_not_flag_a_pre_existing_orphan_from_an_earlier_commit(
    git_pm_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # The exact recurring incident: `ao_batch5_finalize` already landed orphaned in an EARLIER
    # same-day commit (now captured in base_sha). The commit under test here never touches
    # it -- diff-base must not blame this unrelated commit for pre-existing debt.
    (git_pm_dir / "plans" / "active" / "ao_consolidated_closeout_2026_08_12.md").write_text(
        _CLOSEOUT_DOC, encoding="utf-8"
    )
    orphan = git_pm_dir / "plans" / "active" / "issues" / "ao_batch5_finalize_2026_08_03.md"
    orphan.write_text(_UNLINKED_MEMBER_DOC, encoding="utf-8")
    base_sha = _git_commit_all(git_pm_dir, "base: batch5 finalize lands already-orphaned")

    # This commit's own (unrelated) change -- a brand-new, properly-linked doc.
    (git_pm_dir / "plans" / "active" / "issues" / "unrelated_finding_2026_08_14.md").write_text(
        _LINKED_MEMBER_DOC, encoding="utf-8"
    )

    exit_code = checker._run_diff_base(base_sha, quiet=True)
    out = capsys.readouterr().out
    assert exit_code == 0, out
    assert "0 NEW orphan(s)" in out


def test_diff_base_flags_an_orphan_this_commit_itself_introduced(
    git_pm_dir: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (git_pm_dir / "plans" / "active" / "ao_consolidated_closeout_2026_08_12.md").write_text(
        _CLOSEOUT_DOC, encoding="utf-8"
    )
    member = git_pm_dir / "plans" / "active" / "issues" / "ao_batch5_finalize_2026_08_03.md"
    member.write_text(_LINKED_MEMBER_DOC, encoding="utf-8")
    base_sha = _git_commit_all(git_pm_dir, "base: batch5 finalize lands linked")

    # This commit's own edit: drops the related: link -- newly orphans the doc.
    member.write_text(_UNLINKED_MEMBER_DOC, encoding="utf-8")

    exit_code = checker._run_diff_base(base_sha, quiet=False)
    out = capsys.readouterr().out
    assert exit_code == 1, out
    assert "1 NEW orphan(s)" in out
    assert "ao_batch5_finalize_2026_08_03.md" in out
