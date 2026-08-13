# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_codex_doc_freshness.py.

Focus: the per-file baseline-diffing fix
(codex_doc_freshness_regression_ambient_staleness_drift_2026_08_09.md) — a doc
already known-violating at baseline time drifting further stale must NOT count
as a new regression, and the baseline file must store WORKSPACE-RELATIVE paths
(not absolute per-slot-worktree paths) so a snapshot written by one slot is
diffable by any other.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import pytest
from check_codex_doc_freshness import (
    BaselineSnapshot,
    FreshnessViolation,
    FrontmatterParseError,
    _check_doc,
    _is_retired_with_successor,
    _load_baseline,
    _new_violations,
    _parse_frontmatter,
    _relative_path,
    _write_baseline,
    partition_by_agency,
)


def _violation(rel_path: str, workspace_root: Path, reason: str = "stale") -> FreshnessViolation:
    return FreshnessViolation(workspace_root / rel_path, reason)


def test_relative_path_strips_workspace_root(tmp_path: Path) -> None:
    p = tmp_path / "unified-trading-pm" / "codex" / "02-data" / "x.md"
    assert _relative_path(p, tmp_path) == "unified-trading-pm/codex/02-data/x.md"


def test_relative_path_falls_back_to_absolute_outside_root(tmp_path: Path) -> None:
    other = Path("/some/unrelated/path.md")
    assert _relative_path(other, tmp_path) == str(other)


def test_write_then_load_baseline_round_trips_relative_paths(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.yaml"
    violations = [_violation("unified-trading-pm/codex/02-data/a.md", tmp_path)]
    _write_baseline(baseline_path, violations, tmp_path)

    loaded = _load_baseline(baseline_path)
    assert loaded.count == 1
    assert loaded.known_paths == frozenset({"unified-trading-pm/codex/02-data/a.md"})


def test_write_baseline_never_stores_absolute_paths(tmp_path: Path) -> None:
    """Direct regression test for the slot-10 incident: an absolute per-slot
    prefix (e.g. .tabs/4/) must never land in the shared baseline file."""
    baseline_path = tmp_path / "baseline.yaml"
    violations = [_violation("unified-trading-pm/codex/04-architecture/b.md", tmp_path)]
    _write_baseline(baseline_path, violations, tmp_path)

    raw = baseline_path.read_text(encoding="utf-8")
    assert str(tmp_path) not in raw
    assert ".tabs" not in raw


def test_load_baseline_missing_file_is_empty_snapshot(tmp_path: Path) -> None:
    loaded = _load_baseline(tmp_path / "does-not-exist.yaml")
    assert loaded.count == 0
    assert loaded.known_paths == frozenset()


def test_load_baseline_ignores_malformed_entries(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.yaml"
    baseline_path.write_text(
        "violation_count: 2\n"
        "baseline_files:\n"
        "  - path: unified-trading-pm/codex/a.md\n"
        "    reason: stale\n"
        "  - not-a-dict-marker\n",
        encoding="utf-8",
    )
    loaded = _load_baseline(baseline_path)
    assert loaded.count == 2
    assert loaded.known_paths == frozenset({"unified-trading-pm/codex/a.md"})


def test_new_violations_excludes_already_known_paths(tmp_path: Path) -> None:
    """The core ambient-drift fix: a doc already in the baseline snapshot
    getting older (still stale, or now MORE stale) is not a new regression."""
    known = _violation("unified-trading-pm/codex/02-data/already_stale.md", tmp_path)
    baseline = BaselineSnapshot(1, frozenset({_relative_path(known.path, tmp_path)}))

    result = _new_violations([known], baseline, tmp_path)

    assert result == []


def test_new_violations_flags_paths_absent_from_baseline(tmp_path: Path) -> None:
    known = _violation("unified-trading-pm/codex/02-data/already_stale.md", tmp_path)
    fresh_regression = _violation("unified-trading-pm/codex/05-infrastructure/newly_stale.md", tmp_path)
    baseline = BaselineSnapshot(1, frozenset({_relative_path(known.path, tmp_path)}))

    result = _new_violations([known, fresh_regression], baseline, tmp_path)

    assert result == [fresh_regression]


def test_new_violations_empty_baseline_flags_every_violation(tmp_path: Path) -> None:
    v = _violation("unified-trading-pm/codex/02-data/a.md", tmp_path)
    baseline = BaselineSnapshot(0, frozenset())

    assert _new_violations([v], baseline, tmp_path) == [v]


def test_new_violations_no_violations_is_always_clean(tmp_path: Path) -> None:
    baseline = BaselineSnapshot(3, frozenset({"unified-trading-pm/codex/x.md"}))
    assert _new_violations([], baseline, tmp_path) == []


# ---------------------------------------------------------------------------
# _check_doc — unchanged behaviour sanity checks (not the focus of this fix,
# but cheap to lock in given the file's already open for review).
# ---------------------------------------------------------------------------


def test_check_doc_missing_frontmatter(tmp_path: Path) -> None:
    p = tmp_path / "no_fm.md"
    p.write_text("# just a heading, no frontmatter\n", encoding="utf-8")
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.reason == "no-frontmatter"


def test_check_doc_missing_last_reviewed_field(tmp_path: Path) -> None:
    p = tmp_path / "no_field.md"
    p.write_text("---\ndoc_type: codex-ssot\n---\nbody\n", encoding="utf-8")
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.reason == "no-last_reviewed-field"


def test_check_doc_stale(tmp_path: Path) -> None:
    p = tmp_path / "stale.md"
    p.write_text("---\nlast_reviewed: 2026-01-01\n---\nbody\n", encoding="utf-8")
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.reason == "stale"


def test_check_doc_fresh_is_clean(tmp_path: Path) -> None:
    p = tmp_path / "fresh.md"
    p.write_text("---\nlast_reviewed: 2026-08-01\n---\nbody\n", encoding="utf-8")
    assert _check_doc(p, 90, datetime.date(2026, 8, 9)) is None


def test_check_doc_future_dated_is_clean_not_an_error(tmp_path: Path) -> None:
    """Staggered-review convention (see module docstring): a future
    last_reviewed is intentional, never flagged."""
    p = tmp_path / "future.md"
    p.write_text("---\nlast_reviewed: 2026-10-20\n---\nbody\n", encoding="utf-8")
    assert _check_doc(p, 90, datetime.date(2026, 8, 9)) is None


# ---------------------------------------------------------------------------
# no-frontmatter vs yaml-parse-error (2026-08-13, batch13).
# The 2026-08-12 incident: a present-but-malformed frontmatter block (a plain multi-line
# scalar with an internal ": ") reported as "no-frontmatter" -- a misleading diagnostic that
# sends the next person looking for a missing --- block that was never missing. The two
# failure classes must be distinguishable.
# ---------------------------------------------------------------------------


def test_parse_frontmatter_absent_returns_none(tmp_path: Path) -> None:
    p = tmp_path / "no_fm.md"
    p.write_text("# just a heading, no frontmatter\n", encoding="utf-8")
    assert _parse_frontmatter(p) is None


def test_parse_frontmatter_parses_valid_block(tmp_path: Path) -> None:
    p = tmp_path / "good.md"
    p.write_text("---\nlast_reviewed: 2026-01-01\n---\nbody\n", encoding="utf-8")
    assert _parse_frontmatter(p) == {"last_reviewed": datetime.date(2026, 1, 1)}


def test_parse_frontmatter_raises_on_yaml_scanner_error(tmp_path: Path) -> None:
    """The 2026-08-12 reproduction: a plain (non-block-indicator) multi-line scalar
    containing an internal ': ' breaks yaml.safe_load with a ScannerError."""
    p = tmp_path / "bad_yaml.md"
    p.write_text(
        "---\ntitle: X\nsummary: WALL_TYPES accepts: what triggers it\n---\nbody\n",
        encoding="utf-8",
    )
    with pytest.raises(FrontmatterParseError) as excinfo:
        _parse_frontmatter(p)
    assert "yaml parse failed" in str(excinfo.value)
    assert "ScannerError" in str(excinfo.value) or "mapping values" in str(excinfo.value)


def test_parse_frontmatter_raises_on_missing_closing_delimiter(tmp_path: Path) -> None:
    p = tmp_path / "no_close.md"
    p.write_text("---\nlast_reviewed: 2026-01-01\nbody-no-closing-delim\n", encoding="utf-8")
    with pytest.raises(FrontmatterParseError) as excinfo:
        _parse_frontmatter(p)
    assert "missing closing" in str(excinfo.value)


def test_parse_frontmatter_raises_on_non_mapping(tmp_path: Path) -> None:
    p = tmp_path / "list_yaml.md"
    p.write_text("---\n- one\n- two\n---\nbody\n", encoding="utf-8")
    with pytest.raises(FrontmatterParseError) as excinfo:
        _parse_frontmatter(p)
    assert "expected a mapping" in str(excinfo.value)


def test_check_doc_reports_yaml_parse_error_not_no_frontmatter(tmp_path: Path) -> None:
    """The regression that matters: a present-but-malformed block must NOT be reported as
    no-frontmatter -- the misleading diagnostic the incident documented."""
    p = tmp_path / "bad.md"
    p.write_text(
        "---\ntitle: X\nsummary: WALL_TYPES accepts: what triggers it\n---\nbody\n",
        encoding="utf-8",
    )
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.reason == "yaml-parse-error"
    assert "yaml parse failed" in v.detail


def test_check_doc_reports_no_frontmatter_when_truly_absent(tmp_path: Path) -> None:
    p = tmp_path / "no_fm.md"
    p.write_text("# heading only\n", encoding="utf-8")
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.reason == "no-frontmatter"


# ---------------------------------------------------------------------------
# Retired-doc exemption (operator ruling 2026-08-12). A formally retired doc that
# NAMES its successor is out of the staleness window; one that does not is still in.
# The asymmetry is the whole design — see _is_retired_with_successor's docstring.
# ---------------------------------------------------------------------------

_ANCIENT = "last_reviewed: 2020-01-01"
_TODAY = datetime.date(2026, 8, 12)


def _doc(tmp_path: Path, name: str, *fields: str) -> Path:
    p = tmp_path / name
    p.write_text("---\n" + "\n".join(fields) + "\n---\nbody\n", encoding="utf-8")
    return p


def test_retired_with_successor_is_exempt_however_stale(tmp_path: Path) -> None:
    """The point of the ruling: 6 years stale, still clean, because it is retired."""
    p = _doc(tmp_path, "sup.md", _ANCIENT, "status: superseded", "superseded_by: replacement.md")
    assert _check_doc(p, 90, _TODAY) is None


def test_retired_without_successor_is_still_stale(tmp_path: Path) -> None:
    """The mute-button guard. Without this, `status: superseded` alone silences any doc."""
    p = _doc(tmp_path, "orphan.md", _ANCIENT, "status: superseded")
    v = _check_doc(p, 90, _TODAY)
    assert v is not None
    assert v.reason == "stale"


def test_empty_successor_does_not_buy_the_exemption(tmp_path: Path) -> None:
    """`superseded_by:` with no value parses to None — an empty field is not a successor."""
    p = _doc(tmp_path, "empty.md", _ANCIENT, "status: superseded", "superseded_by:")
    v = _check_doc(p, 90, _TODAY)
    assert v is not None
    assert v.reason == "stale"


def test_blank_string_successor_does_not_buy_the_exemption(tmp_path: Path) -> None:
    p = _doc(tmp_path, "blank.md", _ANCIENT, "status: superseded", "superseded_by: '   '")
    v = _check_doc(p, 90, _TODAY)
    assert v is not None
    assert v.reason == "stale"


def test_current_status_is_never_exempt_even_with_successor(tmp_path: Path) -> None:
    """`status` is what retires a doc; a stray superseded_by on a live doc must not exempt it."""
    p = _doc(tmp_path, "live.md", _ANCIENT, "status: current", "superseded_by: other.md")
    v = _check_doc(p, 90, _TODAY)
    assert v is not None
    assert v.reason == "stale"


def test_deprecated_and_archived_also_retire(tmp_path: Path) -> None:
    for status in ("deprecated", "archived"):
        p = _doc(tmp_path, f"{status}.md", _ANCIENT, f"status: {status}", "superseded_by: x.md")
        assert _check_doc(p, 90, _TODAY) is None, status


def test_status_match_is_case_and_whitespace_insensitive(tmp_path: Path) -> None:
    p = _doc(tmp_path, "shouty.md", _ANCIENT, "status: '  SUPERSEDED  '", "superseded_by: x.md")
    assert _check_doc(p, 90, _TODAY) is None


def test_successor_as_list_counts(tmp_path: Path) -> None:
    """Frontmatter across the corpus uses both scalar and list forms for this field."""
    p = _doc(tmp_path, "listy.md", _ANCIENT, "status: superseded", "superseded_by: [a.md, b.md]")
    assert _check_doc(p, 90, _TODAY) is None


def test_empty_list_successor_does_not_buy_the_exemption(tmp_path: Path) -> None:
    p = _doc(tmp_path, "emptylist.md", _ANCIENT, "status: superseded", "superseded_by: []")
    v = _check_doc(p, 90, _TODAY)
    assert v is not None
    assert v.reason == "stale"


def test_retired_exemption_does_not_mask_missing_frontmatter(tmp_path: Path) -> None:
    """A file with no frontmatter has no status to be retired BY — it must still fail."""
    p = tmp_path / "nofm.md"
    p.write_text("# heading only\n", encoding="utf-8")
    v = _check_doc(p, 90, _TODAY)
    assert v is not None
    assert v.reason == "no-frontmatter"


def test_is_retired_with_successor_predicate_directly() -> None:
    assert _is_retired_with_successor({"status": "superseded", "superseded_by": "x.md"})
    assert not _is_retired_with_successor({"status": "superseded"})
    assert not _is_retired_with_successor({"status": "current", "superseded_by": "x.md"})
    assert not _is_retired_with_successor({})
    # A non-string status (e.g. an accidental YAML bool/int) must not crash or exempt.
    assert not _is_retired_with_successor({"status": True, "superseded_by": "x.md"})
    assert not _is_retired_with_successor({"status": "superseded", "superseded_by": [None, 3]})


# ---------------------------------------------------------------------------
# partition_by_agency — the warn-with-digest split
# (/plans/active/issues/qg_ratchets_block_unrelated_ships_2026_08_12.md).
# Staleness is the CLOCK moving and must never block a ship; the three
# authoring reasons are caused by the change in hand and must. This composes
# with the retired-doc exemption above: that removes docs nobody should re-read,
# this stops the remainder from blocking unrelated ships.
# ---------------------------------------------------------------------------


def test_partition_stale_is_advisory_never_blocking(tmp_path: Path) -> None:
    stale = _violation("codex/02-data/aged.md", tmp_path, reason="stale")
    blocking, advisory = partition_by_agency([stale])
    assert blocking == []
    assert advisory == [stale]


def test_partition_authoring_reasons_block(tmp_path: Path) -> None:
    for reason in (
        "no-frontmatter",
        "yaml-parse-error",
        "no-last_reviewed-field",
        "invalid-last_reviewed-format",
    ):
        v = _violation(f"codex/02-data/{reason}.md", tmp_path, reason=reason)
        blocking, advisory = partition_by_agency([v])
        assert blocking == [v], f"{reason} must block — it is an authoring defect"
        assert advisory == []


def test_partition_unknown_reason_fails_closed(tmp_path: Path) -> None:
    """A reason nobody classified must BLOCK, not silently become a warning.

    This is the regression that matters: if a future check adds a reason and
    the partition defaulted to advisory, the new check would ship as a no-op
    that nothing ever fails on. Guarding the default direction, not the
    specific string.
    """
    v = _violation("codex/02-data/mystery.md", tmp_path, reason="some-future-reason")
    blocking, advisory = partition_by_agency([v])
    assert blocking == [v]
    assert advisory == []


def test_partition_mixed_set_splits_both_ways(tmp_path: Path) -> None:
    stale = _violation("codex/02-data/aged.md", tmp_path, reason="stale")
    missing = _violation("codex/02-data/new.md", tmp_path, reason="no-last_reviewed-field")
    blocking, advisory = partition_by_agency([stale, missing])
    assert blocking == [missing]
    assert advisory == [stale]


def test_partition_empty_is_clean_both_ways() -> None:
    assert partition_by_agency([]) == ([], [])


def test_check_doc_stale_captures_owner_for_digest_routing(tmp_path: Path) -> None:
    """The digest groups by owner, so _check_doc must carry it through."""
    p = tmp_path / "owned.md"
    p.write_text("---\nlast_reviewed: 2026-01-01\nowner: ikenna@odum-research.com\n---\nbody\n", encoding="utf-8")
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.owner == "ikenna@odum-research.com"


def test_check_doc_stale_without_owner_has_empty_owner(tmp_path: Path) -> None:
    p = tmp_path / "unowned.md"
    p.write_text("---\nlast_reviewed: 2026-01-01\n---\nbody\n", encoding="utf-8")
    v = _check_doc(p, 90, datetime.date(2026, 8, 9))
    assert v is not None
    assert v.owner == ""
