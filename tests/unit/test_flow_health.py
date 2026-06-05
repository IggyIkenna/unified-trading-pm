"""Hermetic unit tests for the unified flow-health compute core.

Imports the module directly (SSOT) — no replication of the decision rules.
Covers: per-repo block triggers (LDR red, each drift pair, stuck PR), fail-open
safe-defaults, firm-wide aggregation, and the transition gate.

Mirrors tests/unit/test_tier_c_promotion_gate.py — loads the by-path module and
registers it in sys.modules BEFORE exec so @dataclass resolves cls.__module__
(Py3.13 quirk).
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_MOD_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "flow_health.py"
_spec = importlib.util.spec_from_file_location("flow_health", _MOD_PATH)
assert _spec and _spec.loader
fh = importlib.util.module_from_spec(_spec)
sys.modules["flow_health"] = fh
_spec.loader.exec_module(fh)


def _facts(repos: dict[str, dict]) -> dict:
    return {"repos": repos}


def _manifest(repos: dict[str, dict]) -> dict:
    return {"repositories": repos}


# ── per-repo: FLOWING cases ───────────────────────────────────────────────────


def test_repo_level_no_drift_no_red_is_flowing():
    facts = fh._parse_repo_facts(
        {
            "branches": {"main": True, "staging": True, "live-defi-rollout": True},
            "compare": {
                "main_vs_staging": {"ahead_by": 0, "behind_by": 0},
                "main_vs_ldr": {"ahead_by": 2, "behind_by": 0},
                "staging_vs_ldr": {"ahead_by": 1, "behind_by": 0},
            },
            "oldest_open_pr_age_hours": 3.0,
        }
    )
    rf = fh.evaluate_repo("svc", facts, "STAGING_GREEN")
    assert rf.blocked is False
    assert rf.reasons == ()


def test_repo_missing_compare_facts_is_flowing():
    rf = fh.evaluate_repo("svc", fh._parse_repo_facts({}), "MAIN_GREEN")
    assert rf.blocked is False


def test_repo_ci_status_unset_not_red():
    rf = fh.evaluate_repo("svc", fh._parse_repo_facts({}), None)
    assert rf.blocked is False


def test_drift_at_cap_is_not_blocked():
    facts = fh._parse_repo_facts({"compare": {"main_vs_ldr": {"ahead_by": fh.DRIFT_CAP, "behind_by": 0}}})
    assert fh.evaluate_repo("svc", facts, "STAGING_GREEN").blocked is False


def test_pr_age_at_threshold_is_not_blocked():
    facts = fh._parse_repo_facts({"oldest_open_pr_age_hours": fh.STUCK_PR_HOURS})
    assert fh.evaluate_repo("svc", facts, "STAGING_GREEN").blocked is False


def test_junk_compare_values_fail_open():
    facts = fh._parse_repo_facts(
        {"compare": {"main_vs_ldr": {"ahead_by": "lots", "behind_by": None}}, "oldest_open_pr_age_hours": "old"}
    )
    assert fh.evaluate_repo("svc", facts, "STAGING_GREEN").blocked is False


def test_negative_drift_treated_as_zero():
    facts = fh._parse_repo_facts({"compare": {"main_vs_ldr": {"ahead_by": -100, "behind_by": -3}}})
    assert fh.evaluate_repo("svc", facts, "STAGING_GREEN").blocked is False


# ── per-repo: BLOCKED cases ───────────────────────────────────────────────────


def test_block_ldr_red():
    rf = fh.evaluate_repo("svc", fh._parse_repo_facts({}), "FAILING")
    assert rf.blocked is True
    assert any("LDR CI FAILING" in r for r in rf.reasons)


def test_block_main_vs_staging_drift_ahead():
    facts = fh._parse_repo_facts({"compare": {"main_vs_staging": {"ahead_by": fh.DRIFT_CAP + 1, "behind_by": 0}}})
    rf = fh.evaluate_repo("svc", facts, "STAGING_GREEN")
    assert rf.blocked is True
    assert any("main↔staging" in r for r in rf.reasons)


def test_block_main_vs_ldr_drift_behind():
    facts = fh._parse_repo_facts({"compare": {"main_vs_ldr": {"behind_by": 99, "ahead_by": 0}}})
    rf = fh.evaluate_repo("svc", facts, "STAGING_GREEN")
    assert rf.blocked is True
    assert any("main↔LDR" in r for r in rf.reasons)


def test_block_staging_vs_ldr_drift():
    facts = fh._parse_repo_facts({"compare": {"staging_vs_ldr": {"ahead_by": 50, "behind_by": 0}}})
    rf = fh.evaluate_repo("svc", facts, "STAGING_GREEN")
    assert rf.blocked is True
    assert any("staging↔LDR" in r for r in rf.reasons)


def test_block_stuck_pr():
    facts = fh._parse_repo_facts({"oldest_open_pr_age_hours": fh.STUCK_PR_HOURS + 1})
    rf = fh.evaluate_repo("svc", facts, "STAGING_GREEN")
    assert rf.blocked is True
    assert any("stuck PR" in r for r in rf.reasons)


def test_multiple_reasons_accumulate():
    facts = fh._parse_repo_facts(
        {
            "compare": {
                "main_vs_ldr": {"ahead_by": 100, "behind_by": 0},
                "staging_vs_ldr": {"ahead_by": 100, "behind_by": 0},
            },
            "oldest_open_pr_age_hours": 200.0,
        }
    )
    rf = fh.evaluate_repo("svc", facts, "FAILING")
    assert rf.blocked is True
    assert len(rf.reasons) == 4  # LDR red + 2 drift pairs + stuck PR


def test_custom_thresholds_respected():
    facts = fh._parse_repo_facts({"compare": {"main_vs_ldr": {"ahead_by": 3, "behind_by": 0}}})
    assert fh.evaluate_repo("svc", facts, "STAGING_GREEN", drift_cap=2).blocked is True
    assert fh.evaluate_repo("svc", facts, "STAGING_GREEN", drift_cap=10).blocked is False


# ── firm-wide aggregation ─────────────────────────────────────────────────────


def test_evaluate_all_flowing():
    facts = _facts(
        {
            "a": {"compare": {"main_vs_ldr": {"ahead_by": 0, "behind_by": 0}}},
            "b": {"compare": {"staging_vs_ldr": {"ahead_by": 1, "behind_by": 0}}},
        }
    )
    report = fh.evaluate(facts, _manifest({"a": {"ci_status": "STAGING_GREEN"}}))
    assert report.blocked is False
    assert report.state() == "flow-flowing"
    assert set(report.ok_repos) == {"a", "b"}
    assert report.blocked_repos == ()


def test_evaluate_one_blocked():
    facts = _facts(
        {
            "a": {"compare": {"main_vs_ldr": {"ahead_by": 0, "behind_by": 0}}},
            "b": {"compare": {"main_vs_ldr": {"ahead_by": 99, "behind_by": 0}}},
        }
    )
    report = fh.evaluate(facts, _manifest({}))
    assert report.blocked is True
    assert report.state() == "flow-blocked"
    assert [rf.repo for rf in report.blocked_repos] == ["b"]
    assert report.ok_repos == ("a",)


def test_evaluate_pulls_ci_status_from_manifest():
    facts = _facts({"svc": {}})
    report = fh.evaluate(facts, _manifest({"svc": {"ci_status": "FAILING"}}))
    assert report.blocked is True
    assert report.blocked_repos[0].repo == "svc"


def test_evaluate_empty_facts_is_flowing():
    report = fh.evaluate(_facts({}), _manifest({}))
    assert report.blocked is False
    assert report.ok_repos == ()


def test_summary_blocked_lists_repos():
    facts = _facts({"b": {"compare": {"main_vs_ldr": {"ahead_by": 99, "behind_by": 0}}}})
    report = fh.evaluate(facts, _manifest({}))
    s = report.summary()
    assert s.startswith("🔴 flow-blocked")
    assert "b:" in s


def test_summary_flowing():
    report = fh.evaluate(_facts({"a": {}}), _manifest({"a": {"ci_status": "MAIN_GREEN"}}))
    assert report.summary().startswith("🟢 flow-flowing")


# ── transition gate (anti-spam) ───────────────────────────────────────────────


def test_transition_first_block_announced():
    assert fh.is_transition(None, "flow-blocked") is True


def test_transition_first_flowing_silent():
    assert fh.is_transition(None, "flow-flowing") is False


def test_transition_block_to_flow_announced():
    assert fh.is_transition("flow-blocked", "flow-flowing") is True


def test_transition_flow_to_block_announced():
    assert fh.is_transition("flow-flowing", "flow-blocked") is True


def test_transition_steady_state_silent():
    assert fh.is_transition("flow-blocked", "flow-blocked") is False
    assert fh.is_transition("flow-flowing", "flow-flowing") is False


# ── constants ─────────────────────────────────────────────────────────────────


def test_pair_labels_cover_three_axes():
    assert set(fh.PAIR_LABELS) == {"main_vs_staging", "main_vs_ldr", "staging_vs_ldr"}


def test_load_json_roundtrip(tmp_path):
    p = tmp_path / "f.json"
    p.write_text('{"repos": {"a": {}}}')
    assert fh.load_json(p)["repos"] == {"a": {}}


@pytest.mark.parametrize("bad", ["[]", '"x"', "42"])
def test_load_json_rejects_non_object(tmp_path, bad):
    p = tmp_path / "f.json"
    p.write_text(bad)
    with pytest.raises(ValueError):
        fh.load_json(p)
