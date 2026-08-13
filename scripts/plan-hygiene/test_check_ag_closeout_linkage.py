# Epic: infrastructure_master
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
