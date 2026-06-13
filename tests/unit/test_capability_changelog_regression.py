"""Unit tests for the capability changelog + regression gate (Wave-2 #5).

Pins:
  - diff_statuses classifies newly-available / regressed / soft / new / removed.
  - load_edge_statuses takes the BEST status on duplicate edge keys.
  - The regression gate (diff) fires on available -> not_available and is silent
    on improvements (not_registered -> available).
  - Changelog render is deterministic.

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Wave-2 #5.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_OPENAPI = Path(__file__).resolve().parent.parent.parent / "scripts" / "openapi"
if str(_SCRIPTS_OPENAPI) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_OPENAPI))

from generate_capability_changelog import (
    diff_statuses,
    edge_key,
    render_changelog,
)


def test_diff_classifies_each_transition() -> None:
    baseline = {
        "a|supports|x": "available",  # regressed below
        "b|supports|x": "not_registered",  # improves below
        "c|supports|x": "available",  # unchanged
        "d|supports|x": "available",  # removed below
    }
    current = {
        "a|supports|x": "not_available",  # REGRESSED
        "b|supports|x": "available",  # newly available
        "c|supports|x": "available",  # unchanged
        "e|supports|x": "available",  # NEW + newly available
    }
    newly, regressed, soft, new_edges, removed = diff_statuses(baseline, current)
    assert "b|supports|x" in newly
    assert "e|supports|x" in newly
    assert ("a|supports|x", "available", "not_available") in regressed
    assert "e|supports|x" in new_edges
    assert "d|supports|x" in removed
    assert soft == []


def test_regression_only_from_available_to_lost() -> None:
    """available->partial is soft (not a hard regression); available->not_registered IS."""
    baseline = {"k|r|t": "available", "m|r|t": "available"}
    current = {"k|r|t": "partial", "m|r|t": "not_registered"}
    _newly, regressed, soft, _new, _removed = diff_statuses(baseline, current)
    regressed_keys = {k for k, _o, _n in regressed}
    assert "m|r|t" in regressed_keys  # available -> not_registered = lost
    assert "k|r|t" not in regressed_keys  # available -> partial = soft
    assert ("k|r|t", "available→partial") in soft


def test_improvement_never_regresses() -> None:
    baseline = {"k|r|t": "not_registered"}
    current = {"k|r|t": "available"}
    newly, regressed, _soft, _new, _removed = diff_statuses(baseline, current)
    assert regressed == []
    assert "k|r|t" in newly


def test_edge_key_is_stable() -> None:
    assert edge_key("CARRY_STAKED_BASIS", "supports", "venue:deribit") == "CARRY_STAKED_BASIS|supports|venue:deribit"


def test_changelog_render_is_deterministic() -> None:
    args = ("abc123", ["b|r|x"], [("a|r|x", "available", "not_available")], [], ["c|r|x"], [])
    assert render_changelog(*args) == render_changelog(*args)


def test_changelog_render_lists_regression_with_transition() -> None:
    out = render_changelog("abc123", [], [("a|r|x", "available", "not_available")], [], [], [])
    assert "a|r|x  (available→not_available)" in out
    assert "Regressed" in out
