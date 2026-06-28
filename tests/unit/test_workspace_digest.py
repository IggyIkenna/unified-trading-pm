"""Unit tests for the workspace combination fingerprint utility.

SSOT: plans/active/cicd_sit_full_coverage_handoff_2026_06_27.md Phase 2 HIGH-1.
Covers: digest determinism, sensitivity to any repo's tree change (combination property),
and the Gate proof (dep change → block; re-SIT → pass).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

_MOD_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "workspace_digest.py"
_spec = importlib.util.spec_from_file_location("workspace_digest", _MOD_PATH)
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
sys.modules["workspace_digest"] = _mod
_spec.loader.exec_module(_mod)

compute_workspace_digest = _mod.compute_workspace_digest


def test_digest_deterministic():
    trees = {"uac": "tree_abc", "utl": "tree_def", "ml-service": "tree_ghi"}
    d1 = compute_workspace_digest(trees)
    d2 = compute_workspace_digest(trees)
    assert d1 == d2


def test_digest_insertion_order_independent():
    trees_a = {"uac": "tree_abc", "utl": "tree_def"}
    trees_b = {"utl": "tree_def", "uac": "tree_abc"}
    assert compute_workspace_digest(trees_a) == compute_workspace_digest(trees_b)


def test_digest_is_sha256_hex():
    digest = compute_workspace_digest({"uac": "tree1"})
    assert len(digest) == 64
    int(digest, 16)  # valid hex


def test_digest_changes_when_any_repo_tree_changes():
    base = {"uac": "tree_v1", "utl": "tree_u1", "ml-service": "tree_m1"}
    d_base = compute_workspace_digest(base)

    # A single repo's tree change must produce a different digest.
    changed_uac = {**base, "uac": "tree_v2"}
    assert compute_workspace_digest(changed_uac) != d_base

    changed_utl = {**base, "utl": "tree_u2"}
    assert compute_workspace_digest(changed_utl) != d_base

    # Restored to original → same digest.
    assert compute_workspace_digest(base) == d_base


def test_digest_changes_when_repo_added():
    base = {"uac": "tree_v1"}
    with_extra = {"uac": "tree_v1", "new-service": "tree_n1"}
    assert compute_workspace_digest(base) != compute_workspace_digest(with_extra)


def test_digest_empty_mapping():
    assert compute_workspace_digest({}) == hashlib.sha256(b"{}").hexdigest()


def test_digest_matches_expected_formula():
    trees = {"alpha": "treeA", "beta": "treeB"}
    payload = json.dumps(trees, sort_keys=True, separators=(",", ":"))
    expected = hashlib.sha256(payload.encode()).hexdigest()
    assert compute_workspace_digest(trees) == expected


# ── Gate proof (HIGH-combo requirement) ──────────────────────────────────────
# Proves the scenario: repo R validated against combination D1; dep (UAC) changes;
# D2 ≠ D1 → gate blocks; SIT re-runs → D2 stored → gate passes.


def test_combination_gate_dep_change_causes_mismatch():
    # SIT ran: all repos at version 1.
    ws_at_sit_time = {
        "uac": "uac_tree_v1",
        "utl": "utl_tree_v1",
        "ml-service": "ml_tree_v1",
    }
    digest_sit = compute_workspace_digest(ws_at_sit_time)

    # UAC lands a new commit on LDR (breaking change to UAC) — its tree changes.
    ws_now = {
        "uac": "uac_tree_v2",  # changed
        "utl": "utl_tree_v1",
        "ml-service": "ml_tree_v1",
    }
    digest_now = compute_workspace_digest(ws_now)

    # Gate: stored digest != current digest → BLOCK.
    assert digest_sit != digest_now, "A dep change must produce a new workspace digest"


def test_combination_gate_no_change_passes():
    ws = {"uac": "uac_tree_v1", "utl": "utl_tree_v1"}
    digest_stored = compute_workspace_digest(ws)

    # Nothing changed between SIT and promote tick.
    digest_current = compute_workspace_digest(ws)

    # Gate: stored == current → PASS.
    assert digest_stored == digest_current


def test_combination_gate_re_sit_unblocks():
    # SIT first run (UAC v1).
    ws_v1 = {"uac": "uac_tree_v1", "utl": "utl_tree_v1"}
    digest_v1 = compute_workspace_digest(ws_v1)

    # UAC v2 lands.
    ws_v2 = {"uac": "uac_tree_v2", "utl": "utl_tree_v1"}
    digest_v2 = compute_workspace_digest(ws_v2)
    assert digest_v1 != digest_v2  # mismatch → BLOCKED

    # SIT re-runs at v2 → stamps digest_v2 on R.
    stored_after_re_sit = digest_v2

    # Gate: stored_after_re_sit == current (v2) → PASS.
    current = compute_workspace_digest(ws_v2)
    assert stored_after_re_sit == current


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
