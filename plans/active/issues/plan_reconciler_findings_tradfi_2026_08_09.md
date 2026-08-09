---
doc_type: issue
title: plan_reconciler findings — tradfi tranche — 2026-08-09
summary: >-
  Daily deep plan-reconciliation run-findings doc for the tradfi topic tranche, dispatch agt-642862 (slot 2). Records
  hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and coverage
  for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, tradfi, sharded-run]
related: [/plans/active/tradfi_consolidated_closeout_2026_07_18.md]
created: "2026-08-09"
author: plan_reconciler
source: agt-642862
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler (agt-642862) since 2026-08-09T16:00:00Z
depends_on: []
---

# plan_reconciler findings — tradfi tranche — 2026-08-09

Dispatch `agt-642862`, slot 2, tranche `tradfi`. PM head at run start: `953188e730`.

## Scope

66 docs carry `asset_group: tradfi` in `plans/active/` (incl. `issues/`). **50 of 66 are inside the 12-hour grace
window** (heavy concurrent fleet activity on this tranche today — several sibling batch/finalize plan pairs and issue
docs from the last few hours) and are READ-ONLY context this run. **16 are writable** (outside grace):

- `plans/active/data_pipeline_check_mdps_features_2026_07_20.md`
- `plans/active/data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md`
- `plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md`
- `plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`
- `plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`
- `plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`
- `plans/active/issues/features_delta_one_instrument_type_filter_stg_bucket_404_and_swing_outcome_targets_dispatch_gap_2026_08_03.md`
- `plans/active/issues/features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`
- `plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`
- `plans/active/issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`
- `plans/active/issues/mtds_available_at_cross_asset_backfill_line_cap_remediation_2026_07_31.md`
- `plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md`
- `plans/active/issues/tradfi_canonical_path_migration_design_2026_07_19.md`
- `plans/active/issues/tradfi_fx_krw_usd_triplicate_venue_partitions_2026_08_04.md`
- `plans/active/issues/tradfi_recovery_quarantine_registration_gap_2026_07_27.md`
- `plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25_finalize.md`

No `parent_epic: tradfi_master` docs found missing the `asset_group: tradfi` tag (tag-coverage check clean).

## Flips verified

_(pending STEP 5)_

## Contradictions

Applied (HARD-evidence, writable-set docs) — 3 fixes:

1. **`issues/features_delta_one_instrument_type_filter_stg_bucket_404_and_swing_outcome_targets_dispatch_gap_2026_08_03.md`**
   — a 2026-08-06 audit note claimed "deferred work with no tracked todo" directly below a todo that demonstrably IS
   tracked (`- [ ] [DATA] P3. Scope a -test-/IS_TEST_RUN-aware relaxation...`, one line above). Also surfaced:
   `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` (grace-protected) independently drafted a duplicate `[CODE] P3`
   AO-dispatch todo for the identical fix, unaware this one existed. Appended a dated correction noting both facts and
   recommending batch7's copy as the execution vehicle. — `unified-trading-pm@<pending>`
2. **`data_pipeline_check_mdps_features_2026_07_20_finalize_2026_07_27.md`** — body banner read
   `STATUS: draft — NOT dispatched`, contradicting the frontmatter's own `status: active`. Doc predates the 2026-07-30
   ruling that finalize plans ship `active` from the start (gated via `depends_on`+`gate_on_depends` alone, no body
   banner). Replaced with a dated correction; verified against 3 post-ruling sibling finalize docs (batch8/9/10) which
   correctly carry no such banner. — `unified-trading-pm@<pending>`
3. **`issues/mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md`** — a P3 todo's 2026-07-30 blocking note
   (re-verified accurate 2026-07-31) claimed still-blocked on a P2 "Deeper root cause" dependency; that dependency
   shipped 2026-08-03 (`market-data-processing-service@0671953`, landed as `de8ea9f` after a quickmerge rebase) but the
   blocking note was never revisited. **Verified live in code** (not just re-reading the plan doc):
   `market_data_processing_service/app/adapters/tradfi/ohlcv_passthrough.py` on current `origin/live-defi-rollout` now
   declares `related_data_types` on both `TradfiOhlcv15mAdapter` and `TradfiOhlcv24hAdapter`. Appended an UNBLOCKED
   annotation with the exact grep evidence; preserved the doc's own distinction that the todo's separate ETF half needs
   unrelated schema-registration work regardless. — `unified-trading-pm@<pending>`

Big P0/P1 candidates surfaced by hunters (billing-suspension self-contradiction, batch5-archived-vs-cited-active,
massive.py stale plan claim, PAYG-billing-stale operator-decision-cost, batch6 P0 todo line-1-completeness failure) —
**all land on grace-protected or otherwise unwritable docs this run**; routed to `## Doc-drift` / `## Filed` below
rather than fixed directly. See that section for the full adversarial-verification writeup.

## Doc-drift

- **Corpus-wide `check_prosewrap_padding` ratchet regrew (+266: baseline 4472 → live 4738) after its tracking issue
  `plans/archive/issues/prettier_prosewrap_mangles_long_inline_code_spans_2026_07_31.md` was archived
  `status: resolved`.** Tradfi docs are heavy contributors (`tradfi_backfill_oom_remediation_2026_06_24.md` 48 lines,
  `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md` 174 lines,
  `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` 14 lines, several more with 1 line each) but this is a
  **corpus-wide, `asset_group: cross-cutting` mechanical formatting artifact** (prettier's proseWrap mangling long
  inline code spans on every save), not tradfi-specific content drift, and none of the flagged tradfi docs are in this
  run's writable set (either in the 12h grace window or the violations are pre-existing, not newly introduced this run).
  Not fixed here — out of this shard's scope (cross-cutting tranche owns it) and the "resolved" issue's own repair
  recipe appears to need re-opening or re-running, which is itself the finding. Filed below.

Other corpus-wide hygiene-sweep hard failures checked for tradfi relevance and confirmed **NOT tradfi** (owned by other
tranches, no action taken): `check_reference_paths` 2 dangling refs (both `infra`:
`asia_northeast1_zombie_schedulers_dead_targets_2026_08_07.md`, `infra_health_audit_alert_coverage_gaps_2026_08_07.md` —
both cite a since-moved-or-renamed `infra_health_audit_findings_fix_2026_08_07` doc that no longer resolves);
`check_create_only_archive_commits` 1 pair (`escalation_root_key_stale_predecessor_chaining_2026_08_09.md`,
`ao`/escalation); `check_archive_candidates` 3 docs (2 `sports`, 1 `strategy`/infra — none tradfi).

## Codex corrections applied (mechanical, evidence-cited)

_(pending STEP 5.f2)_

## Hygiene fixes

_(pending STEP 5)_

## Filed

_(pending STEP 6)_

## Archive candidates (operator review)

_(pending STEP 5g)_

## Refuted (dropped by verify)

_(pending STEP 4)_

## Coverage (hunters / batches / docs)

_(pending STEP 7)_

## Plans not reached

_(pending STEP 7, if applicable)_

## Progress Log

- **2026-08-09 16:12 UTC, plan_reconciler (agt-642862)**: run started. All slot-2 repos FF-clean at boot (heartbeat's
  git-status nudges were stale from a prior cycle — live-verified clean via `git status --porcelain` across every repo).
  STEP 1 FF sweep: PM + all sibling repos already current on `live-defi-rollout` (PM head `953188e730`). Hygiene sweep
  (`run_hygiene_sweep.sh --ci`) kicked off in background — shared host running ~5-6 concurrent slots' hygiene sweeps
  simultaneously (slots 6, 9, 12, 20, 23, 25 observed), so it's slow but progressing (confirmed via child-process CPU
  activity, not stalled). STEP 2 grace-set computed: 50/66 tradfi docs <12h old, 16 writable. Proceeding to STEP 3
  hunter fan-out while the sweep finishes.
- **2026-08-09 16:22 UTC**: hygiene sweep completed (4 hard failures corpus-wide, 1 soft warning) — cross-checked all 4
  against the tradfi doc population; none touch a tradfi-writable doc directly. The `check_prosewrap_padding` ratchet
  regrowth (+266) does implicate several tradfi docs as content contributors but is a cross-cutting mechanical-format
  issue, not tradfi content drift — logged under Doc-drift, to be filed (STEP 6), not fixed here. Launched STEP 3's
  9-hunter fan-out (3 epic-cluster batches × 22 docs each + epic hub `tradfi_master.md`, 2 topic hunters
  [databento/canonical-ID/instruments/manifest; VM-SPOT/billing/backfill/batch=live], 1 codex-alignment hunter, 1
  missed-flip hunter, 1 AO-dispatch-readiness hunter over the 5 batch6-10 pairs, 1 data-pipeline-milestones-drift hunter
  for the 7 tradfi-targeted todos in `data_pipeline_e2e_milestones_gate_2026_07_24.md`). All running in background;
  awaiting completion notifications before STEP 4 verification.
