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
status: resolved
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
resolved_by: "slot-5, 2026-07-26, pm docs-only + new follow-up issue doc filed"
drift_direction: advance-code
---

> **🟢 RESOLVED 2026-07-26** — re-diagnosis complete; the doc's own P2 todo is done and the new blocker it found is
> tracked in `/plans/active/issues/tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md`. Archived
> per the terminal-status-archived rule. No further action needed on this doc.

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

- [x] ✅ [DATA] P2. **DONE 2026-07-26 (slot-5).** Updated the P0 items at lines 91/105 of
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`. Determined from live code + GCS re-verification that
      the underlying pipeline is **still blocked**, just by a different set of issues than the stale operator-decision
      framing implied: mismatches 2 (filename format) and 4 (features-service read-path handling) from the original
      4-mismatch diagnosis are confirmed STILL unfixed by direct code read, and no successful tradfi features run has
      ever landed (manifest 404 on `features-tradfi-prd-central-element-323112`). Also found the archived doc's own
      "Option A" label doesn't match what actually shipped (looks like a partial Option-B-direction fix instead) —
      flagged, not resolved, in the follow-up. Documented the new blocker with full evidence + concrete fix todos in
      `tradfi_mdps_build_continuous_mismatches_2_and_4_still_open_2026_07_26.md` rather than launching a VM that would
      predictably repeat the 3 prior failed attempts. Corrected `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`'s
      Deferred entry (also completed its truncated sentence) to match the archived doc's own "Option A" label, with a
      pointer to the label-dispute finding.
