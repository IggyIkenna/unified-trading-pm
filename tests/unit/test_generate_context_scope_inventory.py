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
# _latest_marker and _latest_marker_info
# ---------------------------------------------------------------------------


def test_latest_marker_picks_the_max_dated_marker():
    body = "- **context-scout 2026-08-01**: populated.\n- **context-scout 2026-08-03**: re-scouted."
    assert MOD._latest_marker(body) == "2026-08-03"


def test_latest_marker_none_when_absent():
    assert MOD._latest_marker("no markers here") is None


def test_latest_marker_info_returns_date_and_position():
    body = "- **context-scout 2026-08-01**: populated.\n- **context-scout 2026-08-03**: re-scouted."
    info = MOD._latest_marker_info(body)
    assert info is not None
    date, pos = info
    assert date == "2026-08-03"
    assert body[pos : pos + 25].startswith("context-scout 2026-08-03")


def test_latest_marker_info_none_when_absent():
    assert MOD._latest_marker_info("no markers here") is None


def test_latest_marker_info_breaks_ties_by_taking_last_occurrence():
    body = "- **context-scout 2026-08-03**: first.\n- **context-scout 2026-08-03**: second."
    info = MOD._latest_marker_info(body)
    assert info is not None
    _, pos = info
    # the second occurrence is later in the string
    assert "second" in body[pos:]


# ---------------------------------------------------------------------------
# _marker_claimed_count
# ---------------------------------------------------------------------------


def test_marker_claimed_count_extracts_singular_entry():
    body = "- **context-scout 2026-08-06**: populated/refreshed context_scope (1 entry).\n"
    marker_pos = body.index("context-scout")
    assert MOD._marker_claimed_count(body, marker_pos) == 1


def test_marker_claimed_count_extracts_plural_entries():
    body = "- **context-scout 2026-08-06**: populated/refreshed context_scope (4 entries).\n"
    marker_pos = body.index("context-scout")
    assert MOD._marker_claimed_count(body, marker_pos) == 4


def test_marker_claimed_count_returns_none_when_no_parenthetical():
    body = "- **context-scout 2026-08-06**: populated context_scope with the SSOT doc.\n"
    marker_pos = body.index("context-scout")
    assert MOD._marker_claimed_count(body, marker_pos) is None


def test_marker_claimed_count_extracts_comma_extended_claim_not_a_later_quoted_spillover():
    """Reproduces context_scope_count_mismatch_regex_false_positive_comma_extended_claim_2026_08_08.md:
    the marker's own claim is comma-extended prose ("(4 entries, written and counted with extra
    care ...)"), so the closing paren isn't immediately after "entries" -- the old strict regex
    skipped it and matched a LATER, strict-form quoted excerpt of a different doc's marker
    ("context-scout 2026-08-01 (5 entries)") instead, producing a false claimed=5. The real claim
    (4) must win."""
    body = (
        "- **context-scout 2026-08-07**: refreshed context_scope (4 entries, written and counted "
        "with extra care given this doc's own subject matter) -- swapped the now-fixed "
        "`lst_rate_honest_coverage_2026_07_21.md` for the sibling that superseded it, plus "
        "`check_line_caps.sh`. Live-checked `data_completion_defi_2026_07_15.md` at write time: "
        "still 1000L, still carries the stale `context-scout 2026-08-01 (5 entries)` marker, "
        "unrelated to this doc.\n"
    )
    marker_pos = body.index("context-scout")
    assert MOD._marker_claimed_count(body, marker_pos) == 4


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


# Fixture for COUNT_MISMATCH tests: 3 actual context_scope entries, marker claims 4.
# Reproduces the confirmed entry-drop shape from context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md
# (e.g. perp_funding_data_semantics_and_cadence_2026_06_16.md: marker 2026-08-03 claimed 4, frontmatter had 3).
_COUNT_MISMATCH_DOC = """\
---
doc_type: issue
title: count-mismatch fixture
summary: test fixture for COUNT_MISMATCH verdict
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer]
tags: []
related: []
created: "2026-08-06"
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
context_scope:
  - /codex/02-data/honest-coverage-model.md
  - /plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md
  - /cursor-configs/skills/context-scout/SKILL.md
---

# count-mismatch fixture

Fixture body.

## Progress Log

- **context-scout 2026-08-06**: populated/refreshed context_scope (4 entries).
"""


def test_count_mismatch_verdict_when_marker_claims_more_than_actual(tmp_path, monkeypatch):
    """A date-fresh marker that claims 4 entries while only 3 are in the frontmatter must
    produce COUNT_MISMATCH, not UP_TO_DATE — reproducing the confirmed entry-drop shape
    (e.g. perp_funding_data_semantics_and_cadence_2026_06_16.md, marker 2026-08-03 claimed 4,
    frontmatter had 3 after a subsequent batch removed an entry without updating the marker)."""
    plans_dir = tmp_path / "plans" / "active" / "issues"
    plans_dir.mkdir(parents=True)
    doc = plans_dir / "fixture_count_mismatch_entry_drop_2026_08_06.md"
    doc.write_text(_COUNT_MISMATCH_DOC, encoding="utf-8")
    monkeypatch.setattr(MOD, "PM", tmp_path)
    # Marker date 2026-08-06 >= git date 2026-08-05: date-fresh, so only COUNT_MISMATCH fires.
    monkeypatch.setattr(MOD, "_git_last_commit_date_cheap", lambda path: "2026-08-05")
    monkeypatch.setattr(MOD, "_git_last_commit_date_accurate", lambda path: "2026-08-05")
    records = _run_json()
    assert len(records) == 1
    assert records[0]["verdict"] == "COUNT_MISMATCH"
    assert records[0]["context_scope_count"] == 3


def test_count_mismatch_verdict_when_marker_claims_fewer_than_actual(tmp_path, monkeypatch):
    """A date-fresh marker that claims 3 entries while 5 are in the frontmatter must also
    produce COUNT_MISMATCH — this covers the write-time miscount shape confirmed by the
    corpus-wide sweep (e.g. tradfi_satellite_ao_dispatch_batch2_2026_07_25.md: wrote '6 entries'
    onto an already-8-entry list)."""
    plans_dir = tmp_path / "plans" / "active" / "issues"
    plans_dir.mkdir(parents=True)
    doc = plans_dir / "fixture_count_mismatch_write_time_2026_08_06.md"
    doc.write_text(
        """\
---
doc_type: issue
title: write-time miscount fixture
summary: test
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer]
tags: []
related: []
created: "2026-08-06"
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
context_scope:
  - /codex/02-data/honest-coverage-model.md
  - /codex/02-data/pipeline-mode-partition.md
  - /codex/04-architecture/tier-and-import-architecture.md
  - /plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md
  - /cursor-configs/skills/context-scout/SKILL.md
---

# write-time miscount fixture

Fixture body.

## Progress Log

- **context-scout 2026-08-06**: populated/refreshed context_scope (3 entries).
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)
    monkeypatch.setattr(MOD, "_git_last_commit_date_cheap", lambda path: "2026-08-05")
    monkeypatch.setattr(MOD, "_git_last_commit_date_accurate", lambda path: "2026-08-05")
    records = _run_json()
    assert len(records) == 1
    assert records[0]["verdict"] == "COUNT_MISMATCH"
    assert records[0]["context_scope_count"] == 5


def test_up_to_date_when_marker_has_no_count_claim(tmp_path, monkeypatch):
    """A date-fresh marker without a parenthetical count claim must produce UP_TO_DATE —
    the absent count is not treated as a mismatch (prose-form markers are outside the
    mechanical check's scope and verified via manual glance in the sweep tool)."""
    plans_dir = tmp_path / "plans" / "active" / "issues"
    plans_dir.mkdir(parents=True)
    doc = plans_dir / "fixture_no_count_claim_2026_08_06.md"
    doc.write_text(
        FRONTMATTER_TMPL.format(
            title="no-count-claim fixture",
            last_updated="2026-08-01",
            marker_line="- **context-scout 2026-08-06**: populated context_scope with the SSOT doc.",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)
    monkeypatch.setattr(MOD, "_git_last_commit_date_cheap", lambda path: "2026-08-05")
    monkeypatch.setattr(MOD, "_git_last_commit_date_accurate", lambda path: "2026-08-05")
    records = _run_json()
    assert len(records) == 1
    assert records[0]["verdict"] == "UP_TO_DATE"


def test_up_to_date_when_marker_count_matches_actual(tmp_path, monkeypatch):
    """A date-fresh marker whose claimed count exactly matches the live frontmatter list must
    produce UP_TO_DATE — no false COUNT_MISMATCH on a correctly-written marker."""
    plans_dir = tmp_path / "plans" / "active" / "issues"
    plans_dir.mkdir(parents=True)
    doc = plans_dir / "fixture_count_matches_2026_08_06.md"
    doc.write_text(
        FRONTMATTER_TMPL.format(
            title="count-matches fixture",
            last_updated="2026-08-01",
            marker_line="- **context-scout 2026-08-06**: populated/refreshed context_scope (1 entries).",
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(MOD, "PM", tmp_path)
    monkeypatch.setattr(MOD, "_git_last_commit_date_cheap", lambda path: "2026-08-05")
    monkeypatch.setattr(MOD, "_git_last_commit_date_accurate", lambda path: "2026-08-05")
    records = _run_json()
    assert len(records) == 1
    assert records[0]["verdict"] == "UP_TO_DATE"
