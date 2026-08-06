"""Unit tests for scripts/plan-hygiene/generate_context_scope_inventory.py.

Covers the `_last_touched()` precedence fix: it used to trust a manually-maintained
`last_updated` frontmatter field over the real git commit date whenever both were present.
Nothing in this workspace auto-bumps `last_updated` on edit, so it silently goes stale --
measured 2026-08-03: 390/435 docs carrying the field were behind their real last commit, and for
200 of those the stale value alone flipped the doc's verdict to a false UP_TO_DATE, hiding real
post-scout edits from the incremental sweep. The fix takes the MAX of `last_updated` and the best
available git signal (the cheap single-commit date, or the reference-only-commit-walkback
"accurate" date when the cheap one would flag STALE) instead of trusting `last_updated` outright.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "plan-hygiene" / "generate_context_scope_inventory.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("generate_context_scope_inventory", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["generate_context_scope_inventory"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ---------------------------------------------------------------------------
# _last_touched: last_updated vs git-commit-date precedence
# ---------------------------------------------------------------------------


def _patch_git_dates(monkeypatch, cheap, accurate=None):
    """The merged git signal: cheap single-commit date, only falling to the (2-subprocess-call)
    accurate walk-back-past-reference-only-commits path when the cheap date doesn't already
    satisfy the marker short-circuit in `_last_touched`."""
    monkeypatch.setattr(MOD, "_git_last_commit_date_cheap", lambda path: cheap)
    monkeypatch.setattr(MOD, "_git_last_commit_date_accurate", lambda path: accurate if accurate is not None else cheap)


def test_last_touched_prefers_real_git_date_over_a_stale_last_updated(monkeypatch):
    """The confirmed corpus bug: last_updated=2026-07-28 but the doc was really last touched
    2026-08-03 via git (nothing bumped the field). The real, later date must win."""
    _patch_git_dates(monkeypatch, cheap="2026-08-03")
    fm = {"last_updated": "2026-07-28"}
    assert MOD._last_touched(fm, Path("irrelevant.md"), marker="2026-08-01") == "2026-08-03"


def test_last_touched_keeps_last_updated_when_it_is_the_more_recent_date(monkeypatch):
    """A legitimately-set last_updated (e.g. an edit not yet committed) must still count."""
    _patch_git_dates(monkeypatch, cheap="2026-07-20")
    fm = {"last_updated": "2026-08-01"}
    assert MOD._last_touched(fm, Path("irrelevant.md"), marker="2026-07-20") == "2026-08-01"


def test_last_touched_falls_back_to_git_date_when_last_updated_absent(monkeypatch):
    _patch_git_dates(monkeypatch, cheap="2026-07-15")
    assert MOD._last_touched({}, Path("irrelevant.md"), marker="2026-07-15") == "2026-07-15"


def test_last_touched_handles_a_real_date_object_not_just_a_string(monkeypatch):
    _patch_git_dates(monkeypatch, cheap="2026-07-01")
    fm = {"last_updated": dt.date(2026, 7, 30)}
    assert MOD._last_touched(fm, Path("irrelevant.md"), marker="2026-07-01") == "2026-07-30"


def test_last_touched_returns_none_when_neither_signal_is_available(monkeypatch):
    _patch_git_dates(monkeypatch, cheap=None)
    assert MOD._last_touched({}, Path("irrelevant.md"), marker=None) is None


def test_last_touched_ignores_blank_last_updated_string(monkeypatch):
    _patch_git_dates(monkeypatch, cheap="2026-07-10")
    fm = {"last_updated": "   "}
    assert MOD._last_touched(fm, Path("irrelevant.md"), marker="2026-07-10") == "2026-07-10"


def test_last_touched_skips_expensive_walk_when_cheap_date_already_satisfies_marker(monkeypatch):
    """The short-circuit: if the cheap single-commit date already clears UP_TO_DATE against the
    marker, the accurate multi-commit walk (2 subprocess calls per commit) must not run at all."""
    accurate_called = []

    def _accurate(path):
        accurate_called.append(path)
        return "2026-07-01"

    monkeypatch.setattr(MOD, "_git_last_commit_date_cheap", lambda path: "2026-08-01")
    monkeypatch.setattr(MOD, "_git_last_commit_date_accurate", _accurate)
    assert MOD._last_touched({}, Path("irrelevant.md"), marker="2026-08-01") == "2026-08-01"
    assert accurate_called == []


def test_last_touched_walks_back_when_cheap_date_would_flag_stale(monkeypatch):
    """Cheap date is newer than the marker (would flag STALE) -- the accurate walk-back runs and
    can find an OLDER, reference-only-commit-adjusted real content date."""
    _patch_git_dates(monkeypatch, cheap="2026-08-02", accurate="2026-07-20")
    assert MOD._last_touched({}, Path("irrelevant.md"), marker="2026-07-25") == "2026-07-20"


def test_last_touched_takes_max_even_when_git_walk_back_wins(monkeypatch):
    """last_updated can still beat a walked-back accurate date that turns out earlier."""
    _patch_git_dates(monkeypatch, cheap="2026-08-02", accurate="2026-07-01")
    fm = {"last_updated": "2026-07-15"}
    assert MOD._last_touched(fm, Path("irrelevant.md"), marker="2026-07-10") == "2026-07-15"


# ---------------------------------------------------------------------------
# _latest_marker
# ---------------------------------------------------------------------------


def test_latest_marker_picks_the_max_dated_marker():
    body = "- **context-scout 2026-08-01**: populated.\n- **context-scout 2026-08-03**: re-scouted."
    assert MOD._latest_marker(body) == "2026-08-03"


def test_latest_marker_none_when_absent():
    assert MOD._latest_marker("no markers here") is None


# ---------------------------------------------------------------------------
# End-to-end: main() over a real fixture tree
# ---------------------------------------------------------------------------


FRONTMATTER_TMPL = """---
doc_type: issue
title: "{title}"
summary: test fixture
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer]
tags: []
related: []
created: "2026-08-01"
parent_epic: agent_operating_framework_master
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
last_updated: "{last_updated}"
context_scope: [/codex/02-data/honest-coverage-model.md]
---

# {title}

Fixture body.
{marker_line}
"""


def _run_json() -> list[dict]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = MOD.main(["--json"])
    assert rc == 0
    return json.loads(buf.getvalue())


def test_end_to_end_stale_last_updated_no_longer_masks_a_real_later_edit(tmp_path, monkeypatch):
    """The exact confirmed-corpus shape: a stale last_updated must not produce a false
    UP_TO_DATE when the real (mocked) git edit date is later than the scout marker."""
    plans_dir = tmp_path / "plans" / "active" / "issues"
    plans_dir.mkdir(parents=True)
    doc = plans_dir / "fixture_stale_last_updated_2026_08_03.md"
    doc.write_text(
        FRONTMATTER_TMPL.format(
            title="fixture",
            last_updated="2026-07-28",
            marker_line="- **context-scout 2026-08-01**: populated/refreshed context_scope (1 entries).",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)
    monkeypatch.setattr(MOD, "_git_last_commit_date_cheap", lambda path: "2026-08-03")
    monkeypatch.setattr(MOD, "_git_last_commit_date_accurate", lambda path: "2026-08-03")
    records = _run_json()
    assert len(records) == 1
    assert records[0]["verdict"] == "STALE"


# ---------------------------------------------------------------------------
# _marker_claimed_entries — the COUNT_MISMATCH signal
# ---------------------------------------------------------------------------


def test_marker_claimed_entries_parens_form():
    body = "- **context-scout 2026-08-03**: refreshed context_scope (4 entries, still accurate)."
    assert MOD._marker_claimed_entries(body) == 4


def test_marker_claimed_entries_bare_form_last_match():
    """Non-parens marker ('...doc. 5 entries.') and the 'trimmed from 7 to 5 entries' shape both
    resolve to the post-trim count via the bare fallback's LAST-match rule."""
    body = "- **context-scout 2026-08-06**: restored the dropped SSOT + added a follow-up doc. 5\n  entries."
    assert MOD._marker_claimed_entries(body) == 5
    body2 = "- **context-scout 2026-08-03**: re-scouted; trimmed context_scope (7 -> 5 entries)."
    assert MOD._marker_claimed_entries(body2) == 5


def test_marker_claimed_entries_none_when_no_marker():
    assert MOD._marker_claimed_entries("no markers here") is None


def test_marker_claimed_entries_none_when_latest_marker_has_no_count():
    """An OLDER marker with a count does not count once a NEWER marker with no count claim exists."""
    body = (
        "- **context-scout 2026-08-03**: populated context_scope (4 entries).\n"
        "- **context-scout 2026-08-06**: re-scouted; no change."
    )
    assert MOD._marker_claimed_entries(body) is None


def test_marker_claimed_entries_uses_latest_marker_only():
    body = (
        "- **context-scout 2026-08-01**: populated context_scope (2 entries).\n"
        "- **context-scout 2026-08-03**: refreshed context_scope (5 entries)."
    )
    assert MOD._marker_claimed_entries(body) == 5


def test_marker_claimed_entries_ignores_body_prose_past_the_marker():
    """Regression guard (confirmed false positive 2026-08-06 on lst_rate_honest_coverage: the bare
    fallback matched '406 entries' in body text far past the marker). The search must be bounded to
    the marker's own bullet -- next marker / first blank line / 600-char cap."""
    body = (
        "- **context-scout 2026-08-06**: re-verified the current 3 entries resolve on disk, unchanged.\n"
        "\n"
        "## RESUME POINT\n"
        "The corpus has 406 entries across all fixtures and 12 more in the annex; none of this "
        "body prose should be read as the marker's claimed count."
    )
    assert MOD._marker_claimed_entries(body) == 3


def test_marker_claimed_entries_stops_at_next_marker():
    body = (
        "- **context-scout 2026-08-03**: populated context_scope (4 entries).\n"
        "- **context-scout 2026-08-05**: re-scouted; populated context_scope (6 entries)."
    )
    assert MOD._marker_claimed_entries(body) == 6


# ---------------------------------------------------------------------------
# End-to-end: COUNT_MISMATCH verdict
# ---------------------------------------------------------------------------


FRONTMATTER_CM_TMPL = """---
doc_type: issue
title: "{title}"
summary: test fixture
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer]
tags: []
related: []
created: "2026-08-01"
parent_epic: agent_operating_framework_master
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
last_updated: "{last_updated}"
context_scope: {scope_list}
---

# {title}

Fixture body.
{marker_line}
"""


def _write_cm_fixture(tmp_path, monkeypatch, name, scope_list, marker_line, last_updated="2026-08-01"):
    plans_dir = tmp_path / "plans" / "active" / "issues"
    plans_dir.mkdir(parents=True)
    doc = plans_dir / f"{name}.md"
    doc.write_text(
        FRONTMATTER_CM_TMPL.format(
            title=name,
            last_updated=last_updated,
            scope_list=scope_list,
            marker_line=marker_line,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)
    # Marker (08-05) newer than the git edit date (08-03): would read UP_TO_DATE without the
    # count check, exactly the insidious shape where a content regression hides under a fresh marker.
    monkeypatch.setattr(MOD, "_git_last_commit_date_cheap", lambda path: "2026-08-03")
    monkeypatch.setattr(MOD, "_git_last_commit_date_accurate", lambda path: "2026-08-03")


def test_end_to_end_count_mismatch_flags_doc(tmp_path, monkeypatch):
    """The confirmed bug shape (perp_funding instance): a marker claiming 4 entries next to a live
    list of 3. The doc would otherwise read UP_TO_DATE; the count mismatch is the only signal."""
    _write_cm_fixture(
        tmp_path,
        monkeypatch,
        "fixture_count_mismatch_2026_08_06",
        "[/codex/02-data/a.md, /codex/02-data/b.md, /codex/02-data/c.md]",
        "- **context-scout 2026-08-05**: refreshed context_scope (4 entries, still accurate).",
    )
    records = _run_json()
    assert len(records) == 1
    assert records[0]["verdict"] == "COUNT_MISMATCH"
    assert records[0]["context_scope_count"] == 3
    assert records[0]["marker_claimed_entries"] == 4


def test_end_to_end_matching_count_is_up_to_date(tmp_path, monkeypatch):
    """Control: a marker that claims exactly the live count stays UP_TO_DATE -- no false positive."""
    _write_cm_fixture(
        tmp_path,
        monkeypatch,
        "fixture_matching_count_2026_08_06",
        "[/codex/02-data/a.md, /codex/02-data/b.md, /codex/02-data/c.md]",
        "- **context-scout 2026-08-05**: refreshed context_scope (3 entries, still accurate).",
    )
    records = _run_json()
    assert len(records) == 1
    assert records[0]["verdict"] == "UP_TO_DATE"


def test_end_to_end_marker_without_count_not_flagged(tmp_path, monkeypatch):
    """A fresh marker that states no count cannot be checked -- it must stay UP_TO_DATE, not be
    (wrongly) inferred as a mismatch."""
    _write_cm_fixture(
        tmp_path,
        monkeypatch,
        "fixture_no_count_marker_2026_08_06",
        "[/codex/02-data/a.md, /codex/02-data/b.md, /codex/02-data/c.md]",
        "- **context-scout 2026-08-05**: re-scouted; no change needed.",
    )
    records = _run_json()
    assert len(records) == 1
    assert records[0]["verdict"] == "UP_TO_DATE"
    assert records[0]["marker_claimed_entries"] is None
