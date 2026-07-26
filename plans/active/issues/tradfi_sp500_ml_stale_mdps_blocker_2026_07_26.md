---
doc_type: issue
title:
  "tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md's P0 checkboxes still read BLOCKED-OPERATOR-DECISION on the
  MDPS/ES dependency gap that was actually resolved 2026-06-29 — doc never updated, and the batch3 Deferred note citing
  the resolution names the wrong option (Option B) when the archived issue doc says Option A shipped"
summary: >-
  Daily `/ag-closeout-audit tradfi` run (2026-07-26) re-checked `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`'s
  "too-large-or-risky" Deferred entry for `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`, which claims (in a
  sentence that gets cut off mid-citation at the batch3 doc's own EOF) "the BLOCKED-OPERATOR-DECISION on the P0
  MDPS/build-continuous item was actually resolved 2026-06-29 (Option B adopted, mdps@cc63d1b +
  features-service@34a5d4ff + mdps@7d630a3, per the now-archived...". Independently verified against
  `plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md` (status: resolved, resolved_by the
  SAME 3 shas): the resolution was actually **Option A** (a direct raw-MTDS read path bypassing MDPS entirely), not
  Option B (the archived doc's own summary states this explicitly: "RESOLVED 2026-06-29 via a direct raw-MTDS read path
  (Option A)"). Two distinct findings: (1) batch3's citation names the wrong option — a small factual error worth
  correcting wherever it's referenced again; (2) the more material issue —
  `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` itself (P0, `status: active`, `locked_by:
  live-defi-rollout`) was NEVER updated to reflect this resolution. Its P0 todos at lines 91-111 (`- [ ] [AGENT] P0. Run
  MDPS --operation build-continuous...` and `- [ ] [AGENT] P0. Run features-delta-one-service for tradfi/ES...`) still
  read `**BLOCKED-OPERATOR-DECISION**` / `**GATED ON**: operator decision on Option A vs B`, i.e. the doc's own text
  presents an already-resolved architectural fork as still open — a genuine plan/reality drift on a locked P0 doc, not
  just a batch-audit classification nuance. This is a `/plan-reconcile`-shaped defect (stale blocking-language, not a
  fresh finding this skill is scoped to fix — `ag_closeout_auditor.md`'s `does_not` clause is explicit that this skill
  trusts frontmatter/checkbox state as-is and defers contradiction-resolution to `/plan-reconcile`), so it is filed here
  per the findings-closure rule rather than fixed inline.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm, features-service, market-data-processing-service]
scope: [engineer, admin]
tags: [tradfi, plan-hygiene, stale-checkbox, mdps, features, ml, sp500, ag-closeout-audit]
related:
  [
    /plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-07-26
priority: P2
parent_epic: tradfi_master
source:
  "slot 8, ag_closeout_auditor, 2026-07-26, /ag-closeout-audit tradfi daily run — re-checking batch3's Deferred
  too-large-or-risky item per the skill's batchN iterative-drain methodology (step 1: re-check whether a prior batch's
  deferred blocking claim has since resolved)"
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
---

## What I found

`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` (P0, `status: active`, `locked_by: live-defi-rollout`,
`estimate_baseline_ai_days: 4`) carries 3 P0 todos under "## P0 — ES / VIX feature-calculator data-clean runs". Items 2
and 3 (lines 91 and 105) are both still marked `[ ]` open with inline status text:

> **STATUS 2026-06-24**: MDPS process VM `mdps-backfill-tradfi-20260624-065912` was KILLED — architectural investigation
> confirmed it would produce output that CANNOT feed build-continuous (triple mismatch). Architectural decision required
> from operator before this step can run. ... **GATED ON**: operator decision on Option A vs B + corresponding code
> fix + re-run.

But the companion issue doc this same plan spawned,
`plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`, is `status: resolved` with
`resolved_by: market-data-processing-service@cc63d1b + features-service@34a5d4ff + market-data-processing-service@7d630a3 (2026-06-29)`
and its own summary states plainly: "RESOLVED 2026-06-29 via a direct raw-MTDS read path (Option A)." The sp500_ml doc's
checkboxes were never flipped or annotated to reflect this — they still present the Option A/B fork as an open operator
decision three-plus weeks after it was made and shipped.

Separately, `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`'s own Deferred section (the "too-large-or-risky" entry
for this same doc) cites the resolution but names it "**Option B** adopted" — the archived issue doc's own text says
Option A. Minor factual slip, but worth correcting if this Deferred note is copied forward into a future batch4.

## Why it matters

This is a P0, actively-locked plan whose own text tells a reader (human or agent) that ES/VIX feature-calculator runs —
and everything gated behind them (the ML training smoke test, the full S&P + price-arb backtests, ~4 AI-days of
estimated work) — cannot proceed without an operator decision that was, in fact, made and shipped over three weeks ago.
Left as-is, this doc will keep reading as blocked to any future audit/reconciliation pass or engineer picking up
tradfi_master ML work, when the real state is "the architectural blocker is gone; what's actually needed now is to
re-run/verify the feature-calculator jobs against the shipped Option-A code path." This is exactly the class of
plan/reality drift `/plan-reconcile` exists to catch — `/ag-closeout-audit` intentionally does not fix it inline (per
its own scope boundary), hence this issue doc.

## Recommended decision

Reconcile the doc against the shipped resolution, then re-scope its P0 items against current reality (they may now be
directly executable, or may have a new, different blocker — that needs to be checked against live infra, not assumed).

- [ ] [DATA] P2. In `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`, update the P0 items at lines 91 and 105
      (currently `**BLOCKED-OPERATOR-DECISION**` / `**GATED ON**: operator decision on Option A vs B`) to reflect the
      2026-06-29 Option-A resolution (`market-data-processing-service@cc63d1b` + `features-service@34a5d4ff` +
      `market-data-processing-service@7d630a3`, per the archived
      `features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md`). Then determine from current code/infra whether the
      underlying feature-calculator runs (features-delta-one for tradfi/ES; features-volatility for tradfi/ES +
      tradfi/CBOE-VIX) are now actually unblocked: if yes, re-scope the checkboxes as concrete VM-launch-and-verify
      todos and, per the "Plans run to actual completion" HARD RULE, actually launch + verify clean feature parquets
      land (not just mark the doc unblocked); if a new/different blocker is found, document it inline with evidence
      instead. Also correct `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`'s Deferred entry for this doc from
      "Option B" to "Option A" for accuracy. Repos: unified-trading-pm (doc), features-service,
      market-data-processing-service (if the runs are actually launched). Done when: the sp500_ml doc's blocking
      language matches current reality (either genuinely re-executed with evidence, or a new blocker documented), and
      the batch3 citation is corrected.
