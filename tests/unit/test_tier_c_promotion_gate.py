"""Hermetic unit tests for the Tier C LDR→staging promotion gate.

Imports the gate logic directly (SSOT) — no replication of the decision rules,
unlike the inline-heredoc STAGE 1.8 test. Covers: dep-order PASS/BLOCK, Tier A
LDR-red BLOCK, and every fail-open safe-default.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

# Load the gate module by path (scripts/ is not an importable package). Register it
# in sys.modules BEFORE exec so @dataclass can resolve cls.__module__ (Py3.13 quirk).
_GATE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "tier_c_promotion_gate.py"
_spec = importlib.util.spec_from_file_location("tier_c_promotion_gate", _GATE_PATH)
assert _spec and _spec.loader
gate = importlib.util.module_from_spec(_spec)
sys.modules["tier_c_promotion_gate"] = gate
_spec.loader.exec_module(gate)


def _manifest(repos: dict[str, dict]) -> dict:
    return {"repositories": repos}


# ── PASS cases ──────────────────────────────────────────────────────────────


def test_pass_repo_not_in_manifest():
    res = gate.evaluate_repo(_manifest({}), "ghost-repo")
    assert res.promote is True
    assert "no manifest entry" in res.reason


def test_pass_no_deps():
    m = _manifest({"a": {"ci_status": "FEATURE_GREEN", "dependencies": []}})
    assert gate.evaluate_repo(m, "a").promote is True


def test_pass_all_deps_on_staging_staging_green():
    m = _manifest(
        {
            "uac": {"ci_status": "STAGING_GREEN"},
            "utl": {"ci_status": "FEATURE_GREEN", "dependencies": [{"name": "uac"}]},
        }
    )
    assert gate.evaluate_repo(m, "utl").promote is True


def test_pass_dep_sit_validated_and_main_green_count_as_on_staging():
    m = _manifest(
        {
            "uac": {"ci_status": "SIT_VALIDATED"},
            "utl": {"ci_status": "MAIN_GREEN"},
            "svc": {"ci_status": "FEATURE_GREEN", "dependencies": [{"name": "uac"}, {"name": "utl"}]},
        }
    )
    assert gate.evaluate_repo(m, "svc").promote is True


def test_pass_dep_not_in_manifest_is_safe_default():
    m = _manifest({"svc": {"ci_status": "FEATURE_GREEN", "dependencies": [{"name": "external-lib"}]}})
    assert gate.evaluate_repo(m, "svc").promote is True


def test_pass_dep_ci_status_unset_is_safe_default():
    m = _manifest(
        {
            "uac": {},  # no ci_status → treat as external/not tracked
            "svc": {"ci_status": "FEATURE_GREEN", "dependencies": [{"name": "uac"}]},
        }
    )
    assert gate.evaluate_repo(m, "svc").promote is True


def test_pass_own_ci_status_unset_passes_tier_a():
    m = _manifest({"svc": {"dependencies": []}})  # no ci_status → not red → pass
    assert gate.evaluate_repo(m, "svc").promote is True


def test_pass_bare_string_dependency_form():
    m = _manifest(
        {
            "uac": {"ci_status": "STAGING_GREEN"},
            "svc": {"ci_status": "FEATURE_GREEN", "dependencies": ["uac"]},
        }
    )
    assert gate.evaluate_repo(m, "svc").promote is True


def test_pass_malformed_repo_entry():
    m = _manifest({"svc": "not-a-dict"})
    assert gate.evaluate_repo(m, "svc").promote is True


# ── BLOCK cases ─────────────────────────────────────────────────────────────


def test_block_tier_a_ldr_red():
    m = _manifest({"svc": {"ci_status": "FAILING", "dependencies": []}})
    res = gate.evaluate_repo(m, "svc")
    assert res.promote is False
    assert "Tier A" in res.reason


def test_block_dep_feature_green_not_yet_on_staging():
    m = _manifest(
        {
            "uac": {"ci_status": "FEATURE_GREEN"},  # not yet on staging
            "utl": {"ci_status": "FEATURE_GREEN", "dependencies": [{"name": "uac"}]},
        }
    )
    res = gate.evaluate_repo(m, "utl")
    assert res.promote is False
    assert "dep-order" in res.reason
    assert "uac:FEATURE_GREEN" in res.reason


def test_block_dep_local_pass_not_on_staging():
    m = _manifest(
        {
            "uac": {"ci_status": "LOCAL_PASS"},
            "utl": {"ci_status": "FEATURE_GREEN", "dependencies": [{"name": "uac"}]},
        }
    )
    assert gate.evaluate_repo(m, "utl").promote is False


def test_block_dep_failing():
    m = _manifest(
        {
            "uac": {"ci_status": "FAILING"},
            "utl": {"ci_status": "FEATURE_GREEN", "dependencies": [{"name": "uac"}]},
        }
    )
    assert gate.evaluate_repo(m, "utl").promote is False


def test_block_multi_dep_reports_only_the_below_staging_one():
    m = _manifest(
        {
            "uac": {"ci_status": "STAGING_GREEN"},  # ok
            "utl": {"ci_status": "FEATURE_GREEN"},  # below staging → the blocker
            "svc": {"ci_status": "FEATURE_GREEN", "dependencies": [{"name": "uac"}, {"name": "utl"}]},
        }
    )
    res = gate.evaluate_repo(m, "svc")
    assert res.promote is False
    assert "utl:FEATURE_GREEN" in res.reason
    assert "uac" not in res.reason.split("(")[1]  # uac (the passing dep) not named in the blocked list


def test_tier_a_red_takes_precedence_over_dep_check():
    # Own repo FAILING blocks regardless of deps being fine.
    m = _manifest(
        {
            "uac": {"ci_status": "STAGING_GREEN"},
            "svc": {"ci_status": "FAILING", "dependencies": [{"name": "uac"}]},
        }
    )
    res = gate.evaluate_repo(m, "svc")
    assert res.promote is False
    assert "Tier A" in res.reason


# ── lifecycle constant assertions ───────────────────────────────────────────


def test_on_staging_status_set_is_exact():
    assert {"STAGING_GREEN", "SIT_VALIDATED", "MAIN_GREEN"} == gate.ON_STAGING_STATUSES


@pytest.mark.parametrize("below", ["NOT_CONFIGURED", "LOCAL_PASS", "FEATURE_GREEN", "STAGING_PENDING", "FAILING"])
def test_below_staging_statuses_are_not_on_staging(below):
    assert below not in gate.ON_STAGING_STATUSES


def test_load_manifest_roundtrip(tmp_path):
    p = tmp_path / "m.json"
    p.write_text('{"repositories": {"a": {"ci_status": "STAGING_GREEN"}}}')
    m = gate.load_manifest(p)
    assert m["repositories"]["a"]["ci_status"] == "STAGING_GREEN"
