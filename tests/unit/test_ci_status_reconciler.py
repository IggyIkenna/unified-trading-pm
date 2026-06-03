"""Guard 3 — tests for the ci_status drift reconciler decision core."""

from __future__ import annotations

import importlib.util
from pathlib import Path

_MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "ci_status_reconciler.py"
_spec = importlib.util.spec_from_file_location("ci_status_reconciler", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)


def test_missed_recovery_failing_but_main_green_resets_to_main_green() -> None:
    # The live 2026-06-03 UTL incident: v2 success on main, ci_status stuck FAILING.
    d = mod.decide("FAILING", main_concl="success", staging_concl="success", ldr_concl="success")
    assert d.reconcile is True
    assert d.target_status == "MAIN_GREEN"


def test_missed_recovery_failing_but_only_ldr_green_resets_to_feature_green() -> None:
    d = mod.decide("FAILING", main_concl="", staging_concl="", ldr_concl="success")
    assert d.reconcile is True
    assert d.target_status == "FEATURE_GREEN"


def test_missed_regression_green_but_main_failed_resets_to_failing() -> None:
    d = mod.decide("MAIN_GREEN", main_concl="failure", staging_concl="success", ldr_concl="success")
    assert d.reconcile is True
    assert d.target_status == "FAILING"


def test_no_drift_when_status_matches_v2() -> None:
    d = mod.decide("MAIN_GREEN", main_concl="success", staging_concl="success", ldr_concl="success")
    assert d.reconcile is False


def test_green_to_green_tier_diff_is_not_corrected() -> None:
    # FEATURE_GREEN current, v2 green on main (→MAIN_GREEN expected): a promotion-state
    # difference, NOT a drift this guard touches.
    d = mod.decide("FEATURE_GREEN", main_concl="success", staging_concl="", ldr_concl="success")
    assert d.reconcile is False


def test_absent_v2_signal_is_failsafe_noop() -> None:
    d = mod.decide("FAILING", main_concl="", staging_concl="", ldr_concl="")
    assert d.reconcile is False


def test_failure_on_highest_branch_wins_over_lower_success() -> None:
    # main failed, staging/ldr succeeded → expected FAILING (highest definitive branch).
    assert mod.expected_from_v2("failure", "success", "success") == "FAILING"
    # main no-run, staging success → STAGING_GREEN.
    assert mod.expected_from_v2("", "success", "failure") == "STAGING_GREEN"
    # nothing ran → None.
    assert mod.expected_from_v2("", "", "") is None
