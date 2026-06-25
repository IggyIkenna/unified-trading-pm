#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Guard 3 — ci_status drift reconciler (decision core).

WHY (cicd_contract_hardening_2026_06_01 § "Guard 3"): the manifest ``ci_status``
is the dep-order gate signal the promoter reads. It is meant to track the
**quality-gates-v2** conclusion (the authoritative deploy gate). But a NON-v2
workflow (e.g. "Agent Audit") can flip a repo to ``FAILING`` and then no green
event resets it — a **dropped transition** that leaves a repo falsely-FAILING and
**dams the whole dep-ordered LDR→staging cascade** (incident 2026-06-03:
unified-trading-library v2-green on main/staging/LDR but ci_status=FAILING blocked
every dependent).

This module is the PURE decision core (no I/O) so it is unit-testable. The
``ci-status-reconciler.yml`` workflow gathers the latest v2 conclusion per branch
(main → staging → live-defi-rollout) via ``gh`` and calls ``decide()``; on a
genuine drift it re-fires ``ci-status-update`` with the corrected status.

Conservative by design: it ONLY corrects the two unambiguous drift directions —
(1) ci_status=FAILING but v2 is green  → reset to the green tier v2 actually
    reached (missed-recovery), and
(2) ci_status is green but the highest branch that ran v2 last FAILED → FAILING
    (missed-regression).
It NEVER touches green↔green tier differences (FEATURE_GREEN vs STAGING_GREEN —
those are promotion state, not drift) and NEVER acts on an absent v2 signal
(fail-safe: unknown → no-op, never block).

PROMOTION-PR AWARENESS (ci_status_repos_promotion_failure_parity_2026_06_25)
---------------------------------------------------------------------------
A promotion PR (head=live-defi-rollout / staging, into staging / main) runs v2 as a
``pull_request`` event whose head BRANCH is ``live-defi-rollout`` — NOT a push to
``main``. When that PR's v2 FAILS, Slack pages CRITICAL, but the branch-PUSH v2 on
``main`` is still the LAST GREEN merge, so ``expected_from_v2`` (which scans main FIRST)
returned ``MAIN_GREEN`` → the reconciler RESET the (correctly-written) FAILING back to
MAIN_GREEN. That is the Slack↔/repos parity break the operator hit on PM #547. The
``promo_concl`` input (the latest v2 conclusion of the repo's OPEN promotion PR) closes
the hole: a failing OPEN promotion PR is authoritative — it forces FAILING and BLOCKS the
missed-recovery reset. Fail-safe: ``promo_concl`` is "" (no open promotion PR) for the
vast majority of repos, so it is a pure no-op there.
"""

from __future__ import annotations

import argparse
import sys
from typing import NamedTuple, cast

# v2 conclusion per branch: "success" | "failure" | "" (no run / unknown)
Conclusion = str
GREEN_TIERS: tuple[str, ...] = ("MAIN_GREEN", "STAGING_GREEN", "FEATURE_GREEN", "SIT_VALIDATED", "LOCAL_PASS")


class Decision(NamedTuple):
    reconcile: bool
    target_status: str  # the corrected ci_status to dispatch (only meaningful when reconcile=True)
    reason: str


def expected_from_v2(main_concl: Conclusion, staging_concl: Conclusion, ldr_concl: Conclusion) -> str | None:
    """The ci_status the latest v2 run WOULD have emitted, highest branch first.

    Mirrors python-quality-gates-v2.yml: success on main→MAIN_GREEN, staging→
    STAGING_GREEN, LDR/feature→FEATURE_GREEN. If the highest branch that has a v2
    run FAILED, expected is FAILING. If no branch has a v2 run, returns None
    (unknown → caller no-ops).
    """
    # Highest-precedence branch with a definitive (success/failure) conclusion wins.
    for concl, green in ((main_concl, "MAIN_GREEN"), (staging_concl, "STAGING_GREEN"), (ldr_concl, "FEATURE_GREEN")):
        if concl == "success":
            return green
        if concl == "failure":
            return "FAILING"
    return None


def decide(
    current_status: str,
    main_concl: Conclusion,
    staging_concl: Conclusion,
    ldr_concl: Conclusion,
    promo_concl: Conclusion = "",
) -> Decision:
    """Decide whether to reconcile a repo's ci_status against actual v2 state.

    ``promo_concl`` (default "") is the latest v2 conclusion of the repo's OPEN promotion PR
    (LDR/staging → staging/main). A FAILING open promotion PR is AUTHORITATIVE: it overrides the
    branch-push signals (the Slack↔/repos parity fix — a green ``main`` push must not mask a failing
    promotion). It NEVER invents a green; an empty/success ``promo_concl`` leaves the branch-based
    logic untouched, so it is a pure no-op for the repos with no open (or no failing) promotion PR.
    """
    expected = expected_from_v2(main_concl, staging_concl, ldr_concl)
    promo_failing = promo_concl == "failure"
    if expected is None and not promo_failing:
        return Decision(False, current_status, "no v2 signal — fail-safe no-op")

    cur = (current_status or "").strip()

    # Drift 0 — promotion-failing override (parity): an OPEN promotion PR's v2 FAILED. This is the
    # masked case — the branch-push v2 on `main` may still be GREEN (the last green merge), so
    # `expected` reads MAIN_GREEN and would (Drift 1) reset a correct FAILING back to green. A failing
    # open promotion PR is authoritative: force FAILING and SHORT-CIRCUIT before the missed-recovery
    # reset can mask it. Mirrors the Slack `quality-gates-v2 ... PR #N FAILED` CRITICAL page so the
    # dashboard ci_status agrees with Slack. ci_status_repos_promotion_failure_parity_2026_06_25.
    if promo_failing:
        if cur == "FAILING":
            return Decision(False, cur, "promotion PR failing + already FAILING — no drift (parity held)")
        return Decision(
            True, "FAILING", f"promotion-failing: open promotion PR v2 FAILED but ci_status={cur} → FAILING"
        )

    # Drift 1 — missed-recovery: falsely FAILING while v2 is green (and NO failing promotion PR — the
    # promo_failing short-circuit above already handled that case, so a green here is genuine recovery).
    if cur == "FAILING" and expected in GREEN_TIERS:
        return Decision(True, expected, f"missed-recovery: ci_status=FAILING but v2 green → {expected}")

    # Drift 2 — missed-regression: green while the highest v2 branch failed.
    if cur in GREEN_TIERS and expected == "FAILING":
        return Decision(True, "FAILING", f"missed-regression: ci_status={cur} but latest v2 failed → FAILING")

    # Drift 3 — missed-MAIN_GREEN: the repo's v2 PASSED on `main` (so it is on-main-
    # validated) but ci_status shows a LOWER green tier — typically because the live
    # ldr→staging promoter re-ran v2 on `staging` AFTER the main run and ci-status-update
    # last-writer-wins'd it down to STAGING_GREEN. MAIN_GREEN is the dep-order-gate
    # signal staging-to-main reads; without this upgrade the bottom-up fleet drain
    # DEADLOCKS (a base repo like uac/utl never reads MAIN_GREEN, so none of its
    # dependents ever become promote-ready). Only ever upgrades UP to MAIN_GREEN, and
    # only when main v2 is genuinely green — never a downgrade, never invents a pass.
    if cur in GREEN_TIERS and cur != "MAIN_GREEN" and main_concl == "success":
        return Decision(True, "MAIN_GREEN", f"missed-main-green: ci_status={cur} but main v2 is green → MAIN_GREEN")

    # Everything else (match, lower green↔green tier diff with no main pass, or current
    # is a transient state like STAGING_PENDING) → leave alone. Not drift this corrects.
    return Decision(False, cur, f"no actionable drift (current={cur}, expected={expected})")


def _main(argv: list[str]) -> int:
    """CLI for the ci-status-reconciler.yml workflow.

    Usage: ci_status_reconciler.py --current S --main C --staging C --ldr C [--promo C]
    Prints one line: ``RECONCILE <target_status> <reason>`` or ``SKIP <reason>``
    (exit 0 always; the workflow parses the first token).
    """
    parser = argparse.ArgumentParser(description="Guard 3 ci_status drift decision")
    parser.add_argument("--current", required=True, help="current manifest ci_status")
    parser.add_argument("--main", default="", help="latest v2 conclusion on main")
    parser.add_argument("--staging", default="", help="latest v2 conclusion on staging")
    parser.add_argument("--ldr", default="", help="latest v2 conclusion on live-defi-rollout")
    parser.add_argument(
        "--promo",
        default="",
        help="open promotion PR's latest v2 conclusion (LDR/staging → staging/main); 'failure' forces FAILING (parity)",
    )
    args = parser.parse_args(argv)

    d = decide(
        cast("str", args.current),
        cast("str", args.main),
        cast("str", args.staging),
        cast("str", args.ldr),
        cast("str", args.promo),
    )
    if d.reconcile:
        print(f"RECONCILE {d.target_status} {d.reason}")
    else:
        print(f"SKIP {d.reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
