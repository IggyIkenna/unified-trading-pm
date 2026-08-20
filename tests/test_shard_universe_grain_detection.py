#!/usr/bin/env python3
# Epic: system_readiness_master
# Lifecycle: permanent
# Delete-when: NA
"""Regression tests for `shard_universe.detect_grain` / `iter_shard_cells`.

Why this exists
---------------
/plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md
carries a P0 whose wording is the whole point: "Re-run the dump at the finer grain the
moment T2 lands `instrument_type` / `data_type` in `coverage.json`. The skill auto-detects
grain from the payload — **verify that, do not assume it**."

Grain is decided in exactly one place, from the payload itself, and both the
readiness-state-dump and honest-coverage-dump skills depend on that decision agreeing.
The case that actually bites during a cross-tranche handoff is the third one below: T2
lands the `by_venue_instrument_type_data_type` KEY before it lands any data under it. A
detector that keyed off the key's mere presence would flip to the fine grain and then
enumerate ZERO shard cells — every coverage figure silently collapsing to nothing while
looking structurally fine. The shipped detector requires a non-empty venue block, so it
falls back to the 2-tuple grain and keeps reporting real numbers.

Verified live 2026-08-20: all four cases pass against the shipped implementation.

Extended same day for the league FOLD-IN grain (the operator's actual W3 ruling,
``by_venue_instrument_type_data_type_league`` — see
instruments-service/scripts/measure_honest_coverage.py's level-5e block): the identical
silent-zero-coverage trap applies one level deeper, so the key-but-empty case is tested at
this grain too, not just assumed to generalise.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_PM_DIR = Path(__file__).resolve().parents[1]
_SHARD_SCRIPTS = _PM_DIR / "cursor-configs" / "skills" / "honest-coverage-dump" / "scripts"
sys.path.insert(0, str(_SHARD_SCRIPTS))

from shard_universe import detect_grain, iter_shard_cells

_TWO_TUPLE = {"by_venue_data_type": {"cefi": {"OKX-FUTURES": {"trades": {"captured": 3}}}}}

_THREE_TUPLE = {
    "by_venue_data_type": {"cefi": {"OKX-FUTURES": {"trades": {"captured": 3}}}},
    "by_venue_instrument_type_data_type": {"cefi": {"OKX-FUTURES": {"PERPETUAL": {"trades": {"captured": 3}}}}},
}

# T2 lands the key before the data — the silent-zero-coverage trap.
_THREE_TUPLE_KEY_BUT_EMPTY = {
    "by_venue_data_type": {"cefi": {"OKX-FUTURES": {"trades": {"captured": 3}}}},
    "by_venue_instrument_type_data_type": {"cefi": {"OKX-FUTURES": {}}},
}

_NOTHING = {"by_venue_data_type": {}, "by_venue_instrument_type_data_type": None}

_FOUR_TUPLE = {
    "by_venue_data_type": {"sports": {"BET365": {"odds": {"captured": 3}}}},
    "by_venue_instrument_type_data_type": {"sports": {"BET365": {"MATCH_ODDS": {"odds": {"captured": 3}}}}},
    "by_venue_instrument_type_data_type_league": {
        "sports": {"BET365": {"MATCH_ODDS": {"odds": {"EPL": {"captured": 3}}}}}
    },
}

# T2 lands the deepest key before the data — the same silent-zero-coverage trap one level down.
_FOUR_TUPLE_KEY_BUT_EMPTY = {
    "by_venue_data_type": {"sports": {"BET365": {"odds": {"captured": 3}}}},
    "by_venue_instrument_type_data_type": {"sports": {"BET365": {"MATCH_ODDS": {"odds": {"captured": 3}}}}},
    "by_venue_instrument_type_data_type_league": {"sports": {"BET365": {}}},
}


@pytest.mark.parametrize(
    ("payload", "expected_grain", "expected_cells"),
    [
        (_TWO_TUPLE, "venue_data_type", 1),
        (_THREE_TUPLE, "instrument_type", 1),
        (_THREE_TUPLE_KEY_BUT_EMPTY, "venue_data_type", 1),
        (_NOTHING, "venue_data_type", 0),
        (_FOUR_TUPLE, "league", 1),
        (_FOUR_TUPLE_KEY_BUT_EMPTY, "instrument_type", 1),
    ],
    ids=[
        "two-tuple-only",
        "three-tuple-populated",
        "three-tuple-key-but-empty",
        "nothing",
        "four-tuple-populated",
        "four-tuple-key-but-empty",
    ],
)
def test_grain_is_detected_from_data_not_key_presence(payload: dict, expected_grain: str, expected_cells: int) -> None:
    assert detect_grain(payload) == expected_grain
    assert len(list(iter_shard_cells(payload))) == expected_cells


def test_fine_grain_carries_instrument_type_and_coarse_grain_does_not() -> None:
    """The instrument_type axis must actually reach the ShardCell, not just the grain label."""
    fine = list(iter_shard_cells(_THREE_TUPLE))
    coarse = list(iter_shard_cells(_TWO_TUPLE))
    assert [c.instrument_type for c in fine] == ["PERPETUAL"]
    assert [c.instrument_type for c in coarse] == [None]


def test_empty_fine_grain_block_does_not_zero_out_coverage() -> None:
    """The regression this file exists for: a key-but-no-data payload must still report
    the real 2-tuple cells rather than silently enumerating nothing."""
    cells = list(iter_shard_cells(_THREE_TUPLE_KEY_BUT_EMPTY))
    assert len(cells) == 1
    assert cells[0].venue == "OKX-FUTURES"
    assert cells[0].count("captured") == 3


def test_explicit_grain_override_beats_detection() -> None:
    """Callers may pin the grain; detection is only the default."""
    assert len(list(iter_shard_cells(_THREE_TUPLE, "venue_data_type"))) == 1
    assert [c.instrument_type for c in iter_shard_cells(_THREE_TUPLE, "venue_data_type")] == [None]


def test_league_grain_carries_league_id_and_instrument_type() -> None:
    """The deepest grain must carry BOTH axes through, not just league_id at the cost of
    dropping instrument_type (or vice versa) — that would silently re-blend the cells the
    fold-in exists to keep separate."""
    cells = list(iter_shard_cells(_FOUR_TUPLE))
    assert len(cells) == 1
    assert cells[0].instrument_type == "MATCH_ODDS"
    assert cells[0].league_id == "EPL"
    assert cells[0].count("captured") == 3


def test_coarser_grains_leave_league_id_none() -> None:
    """league_id must not leak onto ShardCells built from a coarser grain."""
    assert [c.league_id for c in iter_shard_cells(_THREE_TUPLE)] == [None]
    assert [c.league_id for c in iter_shard_cells(_TWO_TUPLE)] == [None]


def test_empty_league_block_falls_back_to_instrument_type_not_zero() -> None:
    """The regression this extension exists for: a key-but-no-data league payload must still
    report the real 3-tuple cells rather than silently enumerating nothing."""
    cells = list(iter_shard_cells(_FOUR_TUPLE_KEY_BUT_EMPTY))
    assert len(cells) == 1
    assert cells[0].venue == "BET365"
    assert cells[0].instrument_type == "MATCH_ODDS"
    assert cells[0].league_id is None
    assert cells[0].count("captured") == 3
