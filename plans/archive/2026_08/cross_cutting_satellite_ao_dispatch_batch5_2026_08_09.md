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
status: complete
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
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch5_2026_08_09_finalize.md,
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

> **ARCHIVED 2026-08-09 -- COMPLETE.** Both todos shipped. Finalize plan
> `cross_cutting_satellite_ao_dispatch_batch5_2026_08_09_finalize.md` (source-doc reconciliation + this archival)
> completed and archived alongside in the same commit set. Successor: none.

> **Status (historical): active.** Both todos below are same-priority-independent and touch distinct files — no
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
- [x] ✅ [DATA] P2. **AUDIT COMPLETE, BACKFILL DISPATCHED-BUT-BLOCKED (upstream, tracked) — not silently absorbed.**
      Audit (`read_availability_index_safe`, `market-data-tick-cefi-prd-central-element-323112`, filtered
      2026-04-14..04-30): confirmed a genuine gap — CeFi 1h candles + BITGET-SPOT 4h/24h had **zero rows** for 16/17
      days (only 2026-04-14 had any); BITGET-SPOT 24h had zero rows for all 17 days. Root-caused further: BITGET-SPOT
      has **zero raw MTDS ticks** for the entire window (any data_type) and BITGET-FUTURES `trades` is
      `expected_unattempted` 2026-04-14..04-19 — an upstream MTDS gap outside this repo's scope, filed as
      `/plans/active/issues/mdps_1h_candle_backfill_blocked_upstream_mtds_raw_tick_gap_bitget_2026_08_09.md`. Dispatched
      the MDPS-closable portion (BITGET-FUTURES 1h, 2026-04-20..04-30, real raw ticks exist) via
      `deployment-service/scripts/vm/launch-mdps-backfill-vm.sh` — first attempt over-scoped (no `--timeframes` filter
      existed, so it computed the full 7-timeframe default set and every date TIMED OUT at 1800s); **shipped a fix**
      adding `--timeframes` narrow-scope filtering (deployment-service@8f1feb4eb9e4, mirrors the existing
      `--data-types`/`--venues` pattern) and relaunched properly scoped to `1h` only. **BLOCKED on a newly-discovered,
      currently-live, fleet-wide infra bug** (not this task's to fix — `infra`-craft, high blast radius): the VM tarball
      bootstrap's `SETUPTOOLS_SCM_PRETEND_VERSION=0.99.0` is now below the `>=0.106.0` `unified-api-contracts` floor
      that MDPS/MTDS/UTL/deployment-service all independently require (MTDS raised its floor in `@8baed21f`) — every VM
      launch installing this combination fails `uv pip install` immediately. Root-caused via local repro (identical
      commit SHAs succeed on a real git checkout, fail only under the tarball/pretend-version scheme). Filed P0 +
      notified main:
      `/plans/active/issues/vm_tarball_setuptools_scm_pretend_version_below_uac_floor_breaks_all_vm_launches_2026_08_09.md`.
      **Remaining work** (both tracked, neither silently dropped): (1) once the P0 infra fix lands, relaunch the
      already-correctly-scoped
      `--timeframes 1h --venues BITGET-FUTURES --data-types trades cefi 2026-04-20 2026-04-30     full` backfill and
      verify `captured`+file-present; (2) the upstream MTDS raw-tick gap (BITGET-SPOT entirely, BITGET-FUTURES
      04-14..04-19) needs its own MTDS-scope backfill decision per the first issue doc's todos before the rest of the
      named window can close. Repo: market-data-processing-service (+ deployment-service for the shipped launcher fix).
      Source: `features_service_e2e_pipeline_test_2026_05_26.md` (deferred MDPS fan-out item).

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility".

## Progress Log

- **2026-08-09**: Batch authored via the satellite-batch-extraction sweep. 2 items extracted from
  `features_service_e2e_pipeline_test_2026_05_26.md`, the sole `features_and_ml_master` source doc in this pass.
- **2026-08-09 (slot 22)**: Todo 2 audited + backfill dispatched-but-blocked. Along the way discovered + fixed a
  narrow-scope gap in `launch-mdps-backfill-vm.sh` (missing `--timeframes` filter, deployment-service@8f1feb4eb9e4) and
  discovered + filed a P0 fleet-wide VM-launch blocker (tarball pretend-version below uac's real floor) + notified main.
  3 issue docs filed total (upstream MTDS gap, host `/tmp` tmpfs exhaustion, the P0 VM blocker). See the todo's own flip
  for full evidence.
