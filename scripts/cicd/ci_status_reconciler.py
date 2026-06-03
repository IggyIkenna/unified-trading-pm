#!/usr/bin/env python3
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
"""

from __future__ import annotations

from typing import NamedTuple

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


def decide(current_status: str, main_concl: Conclusion, staging_concl: Conclusion, ldr_concl: Conclusion) -> Decision:
    """Decide whether to reconcile a repo's ci_status against actual v2 state."""
    expected = expected_from_v2(main_concl, staging_concl, ldr_concl)
    if expected is None:
        return Decision(False, current_status, "no v2 signal — fail-safe no-op")

    cur = (current_status or "").strip()

    # Drift 1 — missed-recovery: falsely FAILING while v2 is green.
    if cur == "FAILING" and expected in GREEN_TIERS:
        return Decision(True, expected, f"missed-recovery: ci_status=FAILING but v2 green → {expected}")

    # Drift 2 — missed-regression: green while the highest v2 branch failed.
    if cur in GREEN_TIERS and expected == "FAILING":
        return Decision(True, "FAILING", f"missed-regression: ci_status={cur} but latest v2 failed → FAILING")

    # Everything else (match, green↔green tier diff, or current is a transient
    # state like STAGING_PENDING) → leave alone. Not drift this guard corrects.
    return Decision(False, cur, f"no actionable drift (current={cur}, expected={expected})")


def _main(argv: list[str]) -> int:
    """CLI for the ci-status-reconciler.yml workflow.

    Usage: ci_status_reconciler.py --current S --main C --staging C --ldr C
    Prints one line: ``RECONCILE <target_status> <reason>`` or ``SKIP <reason>``
    (exit 0 always; the workflow parses the first token).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Guard 3 ci_status drift decision")
    parser.add_argument("--current", required=True, help="current manifest ci_status")
    parser.add_argument("--main", default="", help="latest v2 conclusion on main")
    parser.add_argument("--staging", default="", help="latest v2 conclusion on staging")
    parser.add_argument("--ldr", default="", help="latest v2 conclusion on live-defi-rollout")
    args = parser.parse_args(argv)

    d = decide(args.current, args.main, args.staging, args.ldr)
    if d.reconcile:
        print(f"RECONCILE {d.target_status} {d.reason}")
    else:
        print(f"SKIP {d.reason}")
    return 0


if __name__ == "__main__":
    import sys

    raise SystemExit(_main(sys.argv[1:]))
