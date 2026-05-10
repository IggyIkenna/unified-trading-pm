---
title: features-onchain suppresses LookaheadBiasError instead of raising loud
created: 2026-05-09
author: ikenna
source:
  - features-onchain-service/features_onchain_service/app/core/feature_writer.py:125-131
  - features-service/features_service/onchain/app/core/feature_writer.py:125-131
  - plans/questions/topology_features_strategy_ml_execution_2026_05_08.md (Q3.2.d)
  - plans/active/topology_qgroup_gap_closure_2026_05_09.md (Phase 5)
related_rule:
  - .claude/CLAUDE.md "LookaheadBiasError raised loud at every features-* compute"
  - .claude/CLAUDE.md "available_at is per-row, write-time, equal to live-pipeline-arrival"
locked_by: live-defi-rollout
locked_since: 2026-05-09
deadline: 2026-05-12
---

# features-onchain suppresses LookaheadBiasError instead of raising loud

> **Severity**: P0 — blocks 2026-05-23 live-DeFi cutover. **Blast radius**: features-onchain-service +
> features-service/onchain sub-package + every DeFi archetype (carry_staked_basis, leveraged_funding_arb) that
> consumes onchain features. **Suggested owner**: features-service maintainer (Phase 5 of
> [`topology_qgroup_gap_closure_2026_05_09.md`](../topology_qgroup_gap_closure_2026_05_09.md)).

## What I found

Two file:line sites suppress `LookaheadBiasError`:

- [`features-onchain-service/features_onchain_service/app/core/feature_writer.py:125-131`](../../../features-onchain-service/features_onchain_service/app/core/feature_writer.py#L125-L131)
- [`features-service/features_service/onchain/app/core/feature_writer.py:125-131`](../../../features-service/features_service/onchain/app/core/feature_writer.py#L125-L131)

Both wrap `PointInTimeEnforcer(strict=True)` in a `contextlib.suppress(LookaheadBiasError)` block. The intent
appears to be "let the calculator continue if a single row is non-compliant" — but the workspace contract per
CLAUDE.md is the opposite: every features-* compute must `raise LookaheadBiasError` loud at the first violated
row.

Sports calculators DO comply (see
[`features-service/features_service/sports/data/writer.py:180-200`](../../../features-service/features_service/sports/data/writer.py#L180-L200) —
documented 2026-05-06 as "previously used strict=False with try/except; handover plan requires LookaheadBiasError
to raise loud"). Onchain still uses the suppression workaround.

## Why it matters

1. **Carry_staked_basis archetype depends on onchain features** (LST yields, DEX pool state, gas prices). If a
   feature-row consumed by carry has a lookahead violation, the strategy's batch backtest result is silently
   inflated by future-knowledge — a classic Citadel-grade backtest-fidelity bug.
2. **Live = batch invariant breaks**: per CLAUDE.md "Live = batch — same data, same fields, same timing
   semantics," batch must respect the same `available_at` rule as live. Suppression masks violations that would
   never occur in live (where `available_at = arrival_time` enforces the rule structurally), creating a silent
   batch-vs-live divergence that the May-23 cutover-gate reconciliation (Group F item 21) will surface as a fault
   — but only AFTER cutover, when fix-time is most expensive.
3. **The suppression hides a real upstream problem**: the suppression was likely added because adapter-side
   `available_at` stamping is incomplete (writegate Phase 2.D in-flight). Removing the suppression without fixing
   upstream stamping will cause loud failures, but at least those failures are visible and routable.

## Root cause hypothesis

Most likely: features-onchain calculators consume MTDS or features-onchain-source data that doesn't have a proper
`available_at` column stamped at write-time. When `PointInTimeEnforcer(strict=True)` is invoked, it raises on every
row because every row's `available_at` is missing or wrong. The suppression was a "make it green" workaround.

Real fix path: writegate Phase 2.D adapter-side `available_at` stamping must land first, then the suppression can
be removed cleanly.

## Recommended decision

1. **Today (2026-05-09)**: file this issue doc + add to Phase 5 of `topology_qgroup_gap_closure_2026_05_09.md`.
2. **By 2026-05-11**: investigate WHY suppression was added. If writegate Phase 2.D is the upstream blocker,
   coordinate landing order via Cross-Plan Coordination Banner.
3. **By 2026-05-12**: either (a) remove suppression + verify all tests pass (if upstream stamping is now correct),
   OR (b) escalate to operator with finding "carry_staked_basis features are silently lookahead-biased; either
   delay May-23 carry-live ramp OR accept the bias with explicit operator sign-off."
4. **No silent acceptance.** Suppression stays only with explicit `# noqa-with-justification` comment + operator
   approval logged in this issue doc.

## Verification

- After removing suppression, run `cd features-onchain-service && bash scripts/quality-gates.sh` — all tests must
  pass.
- Backtest carry_staked_basis archetype on 2024-01-01 → 2024-12-31 — assert no `LookaheadBiasError` raised.
- Diff backtest result against pre-fix run; if >5bps annualized return shift, the suppression was masking a real
  bias and the strategy P&L claim must be revised.

## Composes with

- `topology_qgroup_gap_closure_2026_05_09.md` Phase 5 (this issue's owner phase).
- Writegate Phase 2.D (upstream `available_at` stamping; likely blocker for clean removal).
- CLAUDE.md "LookaheadBiasError raised loud at every features-* compute" rule (the contract being violated).
- CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green" HARD RULE (suppression = smoke-test green
  without actual completion).
