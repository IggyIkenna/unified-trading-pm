"""Hermetic unit tests for the since-last-promote provenance range computation.

Locks in the fix for `provenance_gate_squash_perpetual_block_2026_06_17.md`: the promote
bots must run `check_strict_quickmerge.py` over `<last-promoted-marker>..LDR`, NOT raw
`<target>..LDR` (squash-promotes make the raw range re-flag an already-drained commit
forever). The two invariants under test:
  1. marker present + reachable → `<marker>..<ldr>` (only commits since the last drain).
  2. FAIL-SAFE: no marker / unreachable marker → raw `<base>..<ldr>` (WIDEN, never narrow).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# Load the helper by path (scripts/ is not an importable package) — mirrors
# test_tier_c_promotion_gate.py's loader.
_MOD_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "promote_provenance_range.py"
_spec = importlib.util.spec_from_file_location("promote_provenance_range", _MOD_PATH)
assert _spec and _spec.loader
ppr = importlib.util.module_from_spec(_spec)
sys.modules["promote_provenance_range"] = ppr
_spec.loader.exec_module(ppr)


# ── resolve_range: the core marker-vs-fallback decision ──────────────────────


def test_marker_present_and_reachable_uses_marker_range():
    rng, mode = ppr.resolve_range(
        "abc123", base_ref="origin/staging", ldr_ref="origin/live-defi-rollout", marker_reachable=True
    )
    assert mode == "marker"
    assert rng == "abc123..origin/live-defi-rollout"


def test_marker_present_but_unreachable_falls_back():
    # The unreachable-marker fail-safe (e.g. LDR was force-synced and the marker is gone).
    rng, mode = ppr.resolve_range(
        "deadbeef", base_ref="origin/staging", ldr_ref="origin/live-defi-rollout", marker_reachable=False
    )
    assert mode == "fallback"
    assert rng == "origin/staging..origin/live-defi-rollout"


def test_no_marker_falls_back():
    # First drain ever (no merged promote PR) → raw range.
    rng, mode = ppr.resolve_range(
        None, base_ref="origin/main", ldr_ref="origin/live-defi-rollout", marker_reachable=False
    )
    assert mode == "fallback"
    assert rng == "origin/main..origin/live-defi-rollout"


def test_empty_marker_falls_back():
    rng, mode = ppr.resolve_range(
        "", base_ref="origin/staging", ldr_ref="origin/live-defi-rollout", marker_reachable=True
    )
    assert mode == "fallback"
    assert rng == "origin/staging..origin/live-defi-rollout"


def test_custom_refs_are_honored():
    rng, mode = ppr.resolve_range("sha9", base_ref="origin/main", ldr_ref="HEAD", marker_reachable=True)
    assert mode == "marker"
    assert rng == "sha9..HEAD"


# ── last_promoted_marker: parse gh output / fail-safe to None ────────────────


def _patch_run(monkeypatch, rc: int, out: str):
    monkeypatch.setattr(ppr, "_run", lambda *_a, **_k: (rc, out))


def test_marker_parsed_from_gh_json(monkeypatch):
    _patch_run(monkeypatch, 0, '[{"headRefOid":"b859a15","mergedAt":"2026-06-16T22:32:52Z"}]')
    assert ppr.last_promoted_marker("IggyIkenna", "unified-trading-library", "staging") == "b859a15"


def test_marker_none_on_gh_error(monkeypatch):
    _patch_run(monkeypatch, 1, "")
    assert ppr.last_promoted_marker("IggyIkenna", "r", "staging") is None


def test_marker_none_on_empty_array(monkeypatch):
    # No merged promote PR yet.
    _patch_run(monkeypatch, 0, "[]")
    assert ppr.last_promoted_marker("IggyIkenna", "r", "main") is None


def test_marker_none_on_malformed_json(monkeypatch):
    _patch_run(monkeypatch, 0, "not json{{")
    assert ppr.last_promoted_marker("IggyIkenna", "r", "staging") is None


def test_marker_none_on_missing_field(monkeypatch):
    _patch_run(monkeypatch, 0, '[{"mergedAt":"2026-06-16T22:32:52Z"}]')
    assert ppr.last_promoted_marker("IggyIkenna", "r", "staging") is None


def test_marker_none_on_blank_field(monkeypatch):
    _patch_run(monkeypatch, 0, '[{"headRefOid":"   "}]')
    assert ppr.last_promoted_marker("IggyIkenna", "r", "staging") is None


# ── commit_reachable: thin wrapper over `git cat-file -e` ────────────────────


def test_commit_reachable_true(monkeypatch):
    _patch_run(monkeypatch, 0, "")
    assert ppr.commit_reachable("abc123") is True


def test_commit_reachable_false(monkeypatch):
    _patch_run(monkeypatch, 1, "")
    assert ppr.commit_reachable("deadbeef") is False
