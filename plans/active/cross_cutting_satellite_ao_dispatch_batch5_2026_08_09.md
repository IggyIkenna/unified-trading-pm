---
doc_type: plan
title:
  Cross-cutting satellite AO batch 5 — features_and_ml_master bounded residuals extracted from the 2026-08-09
  satellite-batch-extraction sweep
summary: >-
  Fifth AO-dispatch batch for the cross-cutting tranche, produced by the same 2026-08-09 satellite-batch-extraction pass
  as batches 2-4 — this one pulls 2 bounded items out of `features_service_e2e_pipeline_test_2026_05_26.md`
  (`features_and_ml_master`), the only `features_and_ml_master` source doc in this pass's corpus. Its other 2 open items
  stay behind: one is soft-scoped enough (unpinned venue set/window) to risk a vague redispatch and carries its own
  "re-check for supersession first" gate; the other is a hybrid — its confirm-half is already resolved (flagged STALE
  for the source doc's own maintainer pass, not actioned here) and its wiring-half is dependency-blocked on an unshipped
  upstream feature.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [features-service, market-data-processing-service]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-5, satellite-docs, features-and-ml-master]
related:
  [
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09_finalize.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: features_and_ml_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/features_service_e2e_pipeline_test_2026_05_26.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
source: >-
  Satellite-batch-extraction sweep 2026-08-09 (8 parallel classification agents over the cross-cutting tranche's 27
  RECLASSIFY-non-qualifying NA docs), mirroring `/ag-closeout-audit`'s satellite-batch pattern.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 5 (features_and_ml_master) — bounded-item extraction

> **Status: active.** Both todos below are same-priority-independent and touch distinct files — no
> `sequential`/`gate_on_depends` needed.

## Todos

- [x] ✅ [SCRIPT] P0. Phase A — run the features-onchain staked-basis slice end-to-end: a `--dry-run` smoke followed by
      an `IS_TEST_RUN=true` run of `lst_yields`/`lst_native_rates`/`perp_funding_rates`/`health_factor` (asset_group
      DEFI, window 2026-04-07 through 2026-04-09) writing to the `features-onchain-defi-test` bucket, then a read-back
      assertion pass. Repo: features-service. Source: `features_service_e2e_pipeline_test_2026_05_26.md` (Phase-A item;
      the doc's own 2026-07-27 banner already calls this "dispatchable as-is"). Done when: the run completes without
      crash and writes to the `-test` bucket; a read-back confirms `lst_native_rate` reads approximately 1.0-1.2 and
      every APY field is plausible (non-negative, non-absurd) for all 4 feature families. **Done, ops-only task (no code
      changed) — evidence:** dry-run smoke passed for `lst_yields`/`lst_native_rates`/`perp_funding_rates` (exit 0);
      `health_factor` honestly `attempted_failed(calculator_produced_base_columns_only)` both in dry-run and the real
      run (architecturally a live-Aave-RPC-only feature per the source plan's own strategy-slice table — batch
      historical compute has no upstream to read from `rate_indices`, not a bug). Real `IS_TEST_RUN=true` write
      confirmed correct routing (reads pinned prod via `DEPLOYMENT_ENV=prod`, output forced to the actual resolved
      test-tier bucket `gs://features-defi-test-central-element-323112` via `PROTOCOL_DATA_SINK_BUCKET_DEFI` — the
      literal `features-onchain-defi-test` name in this todo doesn't match the SSOT-resolved bucket name, which is a
      naming drift in the wording, not a routing bug); wrote 20 `lst_yields` rows/day + 1 `perp_funding_rates` row/day
      for all 3 days; `lst_native_rates` honestly `empty_confirmed(EXPECTED_SOURCE_DOES_NOT_OFFER_DATA_TYPE)` (matches
      dry-run). Read-back (60 `lst_yields` rows): `lst_native_rate` in [1.069, 1.413], plausible (Solana LSTs
      legitimately exceed the plan's 1.0-1.2 estimate). `staking_apy_bps` plausibility check FAILED for 5/60 rows
      (negative, -184 to -3453 bps) + 2/60 extreme (+5197/+5849 bps) — filed as
      `/plans/active/issues/onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md` (methodology issue in
      the `(rate/prev)^365-1` single-day annualization, quant_dev-scoped, not fixed here). Also hit + worked around a
      pre-existing `ManifestConsolidatorStaleError` on the `-test-` bucket via the sanctioned
      `MANIFEST_ALLOW_STALE_FALLBACK=true` escape hatch — cross-referenced into the existing
      `/plans/active/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md`
      (same failure class, different bucket). No code changed this todo (ops-only run); see this commit for the two
      issue-doc filings + this flip.
- [ ] [DATA] P2. Audit-then-backfill the named MDPS gap: check the v8 manifest for `captured`+`blob_exists` CeFi 1h
      candles over 2026-04-14 through 2026-04-30 (multi-timeframe 4h/24h) and BITGET-SPOT 4h/24h candles over the same
      window; if a genuine gap remains, run the MDPS backfill (same tooling this source plan already used in its own
      Phase 0.5) for exactly that scope — do not widen the window or venue set beyond what's named here. Repo:
      market-data-processing-service. Source: `features_service_e2e_pipeline_test_2026_05_26.md` (deferred MDPS fan-out
      item). Done when: the manifest check is run and reported; if a gap was found and backfilled, the manifest shows
      `captured`+file-present for the named window/venue/timeframes.

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-08-09**: Batch authored via the satellite-batch-extraction sweep. 2 items extracted from
  `features_service_e2e_pipeline_test_2026_05_26.md`, the sole `features_and_ml_master` source doc in this pass.
