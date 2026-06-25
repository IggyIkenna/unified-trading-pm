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


def test_lower_green_to_green_tier_diff_without_main_pass_is_not_corrected() -> None:
    # FEATURE_GREEN current, v2 green only on staging (no main run): a lower green↔green
    # promotion-state difference with NO main pass — NOT a drift this guard touches.
    d = mod.decide("FEATURE_GREEN", main_concl="", staging_concl="success", ldr_concl="success")
    assert d.reconcile is False


def test_missed_main_green_upgrades_when_main_v2_passed() -> None:
    # Drift 3 — the deadlock case. A repo on main with a GREEN main v2 but ci_status
    # knocked down to a lower green tier (e.g. STAGING_GREEN, from the live ldr→staging
    # promoter re-running v2 on staging after the main run). MAIN_GREEN is the dep-order
    # gate signal — without this upgrade the bottom-up fleet drain DEADLOCKS.
    d = mod.decide("STAGING_GREEN", main_concl="success", staging_concl="success", ldr_concl="success")
    assert d.reconcile is True
    assert d.target_status == "MAIN_GREEN"
    # also upgrades from FEATURE_GREEN when main v2 is green
    d2 = mod.decide("FEATURE_GREEN", main_concl="success", staging_concl="", ldr_concl="success")
    assert d2.reconcile is True
    assert d2.target_status == "MAIN_GREEN"
    # but NOT when main v2 is absent/not-success (no false upgrade)
    d3 = mod.decide("STAGING_GREEN", main_concl="", staging_concl="success", ldr_concl="success")
    assert d3.reconcile is False


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


# ── Slack↔/repos parity: a FAILING open promotion PR must surface, not be masked by green main ──
# (ci_status_repos_promotion_failure_parity_2026_06_25)


def test_promotion_failing_overrides_green_main_does_not_reset_to_main_green() -> None:
    # THE PM #547 BUG: the LDR→main promotion PR's v2 FAILED (promo=failure), but the last
    # push to `main` is still GREEN (main=success) → without promo-awareness the reconciler
    # computed expected=MAIN_GREEN and would have reset a FAILING ci_status back to MAIN_GREEN,
    # masking the Slack CRITICAL page. With promo-awareness the green main NEVER masks it.
    d = mod.decide(
        "MAIN_GREEN", main_concl="success", staging_concl="success", ldr_concl="success", promo_concl="failure"
    )
    assert d.reconcile is True
    assert d.target_status == "FAILING"


def test_promotion_failing_resets_stale_green_to_failing_even_with_empty_branch_signals() -> None:
    # The repo reads MAIN_GREEN but the open promotion PR's v2 failed and NO branch-push v2 ran
    # this window (all branch signals empty). The promotion failure is authoritative → FAILING.
    d = mod.decide("MAIN_GREEN", main_concl="", staging_concl="", ldr_concl="", promo_concl="failure")
    assert d.reconcile is True
    assert d.target_status == "FAILING"


def test_promotion_failing_already_failing_is_no_drift() -> None:
    # ci_status is already correctly FAILING + the promotion PR is still failing → parity holds,
    # nothing to reconcile (and crucially the green main does NOT flip it back to MAIN_GREEN).
    d = mod.decide("FAILING", main_concl="success", staging_concl="success", ldr_concl="success", promo_concl="failure")
    assert d.reconcile is False


def test_promotion_success_is_a_pure_noop_branch_logic_unchanged() -> None:
    # A green/absent promo_concl must leave the branch-based decision identical to before — the
    # missed-recovery reset still works when the promotion is NOT failing (genuine recovery).
    d_green = mod.decide(
        "FAILING", main_concl="success", staging_concl="success", ldr_concl="success", promo_concl="success"
    )
    assert d_green.reconcile is True and d_green.target_status == "MAIN_GREEN"
    d_empty = mod.decide("FAILING", main_concl="success", staging_concl="success", ldr_concl="success", promo_concl="")
    assert d_empty.reconcile is True and d_empty.target_status == "MAIN_GREEN"


def test_promotion_failing_with_no_branch_signal_is_not_a_failsafe_noop() -> None:
    # Distinct from test_absent_v2_signal_is_failsafe_noop: there ALL signals (incl. promo) are
    # empty → no-op. Here the promotion PR genuinely failed, so the absent-branch-signal fail-safe
    # must NOT swallow it — the failing promotion is real evidence and must surface.
    d = mod.decide("MAIN_GREEN", main_concl="", staging_concl="", ldr_concl="", promo_concl="failure")
    assert d.reconcile is True
    assert d.target_status == "FAILING"


def test_default_promo_concl_keeps_legacy_three_arg_call_working() -> None:
    # The CLI/older callers pass only the 4 branch args; promo_concl defaults to "" → unchanged.
    d = mod.decide("FAILING", main_concl="success", staging_concl="success", ldr_concl="success")
    assert d.reconcile is True
    assert d.target_status == "MAIN_GREEN"
