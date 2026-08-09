---
doc_type: plan
title:
  Cross-cutting satellite AO batch 11 — instruments_master bounded residuals (11 independently-mechanical items)
  extracted from mtds_venue_backfill_and_ops_hardening_residuals, round11 2026-08-09 sweep
summary: >-
  Eleventh AO-dispatch batch for the cross-cutting tranche, produced by the round11 2026-08-09 RECLASSIFY +
  satellite-extraction sweep. Pulls 11 bounded items out of
  `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` (`instruments_master`, 22 open todos). That doc's own
  2026-08-07 na-eligibility-audit pass already found "roughly half the 22 open items ... read as independently
  bounded/mechanical with no operator or credential gate of their own — a candidate for a future doc-split ... not
  executed this run." Today's pass is that future split. The source doc's whole-doc RECLASSIFY bar stays unmet — the
  remaining 11 open items are a genuine mix of credential/cost-gated backfill scope (B0), an operator-sequenced B0→B1→B2
  dependency chain (2026-06-18 ruling), a foreign-repo dependency (`paper_engine.py`, source not yet on LDR), a
  dirty-tree-gated tarball rebuild, a large multi-file closed-set schema extension (`ohlcv-1s`/`BarTimeframe`, touches
  many services in one commit — too broad-blast-radius for a single bounded todo, left in place), and a known-stale
  manifest dedup fix already tracked elsewhere (`pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md`).
  **One named candidate explicitly excluded after conflict-check**: "Wire Kalshi into the pipeline" was NOT extracted —
  live evidence in `data_completion_to_100_all_ag_2026_06_21.md` (Kalshi deep-history seed VMs ran, `live_kalshi`
  present/`captured`) and `prediction_live_clob_depth_capture_2026_07_24.md` (Kalshi trades-adapter URL fix shipped +
  verified) shows this work already happened elsewhere; the source doc's own checkbox is very likely stale, flagged
  in-place rather than re-dispatched as fresh work.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos:
  [instruments-service, unified-trading-library, market-tick-data-service, deployment-service, unified-api-contracts]
scope: [engineer]
tags:
  [cross-cutting, ao-dispatch, close-out, batch-11, satellite-docs, instruments-master, mtds, sports, defi, prediction]
related:
  [
    /plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch11_2026_08_09_finalize.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 2.2
estimate_calibrated_ai_days: 1.76
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
source: >-
  round11 RECLASSIFY + satellite-batch-extraction sweep 2026-08-09 (cross-cutting + ui tranches) — formalizes this
  source doc's own 2026-08-07 na-eligibility-audit finding that ~half its 22 open items were independently bounded but
  never split out; conflict-checked against all active cross_cutting_satellite batches (1/1b/2/4/6/7 grepped clean) and
  the sibling instruments_master satellite/finalize docs before extraction.
assigned_role: data_engineering
effort: high
sequential: false
drift_direction: advance-code
---

# Cross-cutting satellite AO batch 11 (instruments_master) — bounded-item extraction

> **Status: active.** All 11 todos below are same-priority-independent and touch distinct files/repos — no
> `sequential`/`gate_on_depends` needed. Independent todos may run concurrently across workers.

## Todos

- [ ] [CODE] P3. **`--operation status --asset-group prediction` can't read the flat-kind bucket.** Source:
      `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`. `_run_coverage_status` calls
      `get_write_bucket_name("instruments", "prediction")` which raises `BucketNamingError` (the per-asset_group
      instruments-store dict has no PREDICTION entry; prediction resolves via the FLAT
      `resolve_instruments_store_kind`→`instruments-store-pred`). Teach the status path to use
      `_get_instruments_bucket_for_asset_group` (the same resolver the write path already uses) so prediction status
      renders. Display-only gap — the backfill WRITE path already works. Done when:
      `--operation status --asset-group prediction` runs without raising and renders coverage. Repo:
      instruments-service.
- [ ] [CODE] P2. **DeFi venue-grain — align the ADAPTER/writer shard key to the decided PROTOCOL-CHAIN grain.** Source:
      same doc. The `_index` reconcile (already DONE) fixed the STORED data to the decided PROTOCOL-CHAIN grain
      (`AAVE_V3-ETHEREUM`, per UAC SSOT `ALL_DEFI_VENUES`), but the WRITER still keys multi-chain protocol shards by the
      adapter's bare `venue` property rather than `InstrumentRecord.venue`=`PROTOCOL-CHAIN`, so a fresh capture can
      re-introduce a bare-spelling row. Make the adapter `venue` property, `InstrumentRecord.venue`, and the manifest
      shard key all emit the canonical PROTOCOL-CHAIN id so new writes match the canonicalised `_index` with no
      re-reconcile needed. Done when: a fresh capture for a multi-chain protocol writes under the PROTOCOL-CHAIN shard
      key, verified against the `_index`. Repo: instruments-service / unified-trading-library (manifest shard key).
- [ ] [INFRA] P1. **B3 — copy e2e research data to canonical placement + e2e doc.** Source: same doc. HL
      `perp_funding`/`perp_daily_ctx` currently lives ONLY in the no-env-suffix research bucket
      `gs://perp-funding-central-element-323112/day=*/`; LST rates ONLY in
      `gs://lst-rates-central-element-323112/day=*/` — prod-needed data outside canonical placement. (a) Determine the
      canonical home per data_type (the dedicated `-prd-` bucket, e.g. `lst-rates-prd`, already exists, vs the
      `market-data-tick-{cefi|defi}-prd` canonical `pipeline_mode=` path). (b) `gcs_copy_object` (workers=32, in-region)
      the research objects to canonical placement + `record_captured` so the `_index` reflects them. (c) Write a note in
      `e2e-testing/docs/` listing the old→canonical bucket/path mapping so the e2e funding scripts
      (`staked_basis_funding_scan`/`colocated_engine`/etc.) update their fetch paths. The research buckets become
      deletable only after (never in this todo — that step is operator-gated). Done when: the canonical-home decision is
      recorded, the copy is verified content-complete (count + spot content, not path existence), and the e2e doc note
      is written. Repo: instruments-service/deployment-service + e2e-testing (doc).
- [ ] [DATA] P2. **Run the Extended public instrument + perp backfill (UNBLOCKED — no key needed).** Source: same doc.
      IS daily-listing CLI for EXTENDED-STARKNET (genesis-accurate per-instrument `available_from`, already shipped) +
      MTDS OHLCV/funding capture over 2024-07-26→yesterday (funding only from 2025-08-01 mainnet). No API key required
      for market data (verified live — only order placement needs the stark private key). Done when: the honest coverage
      index shows `expected_unattempted`→`captured` conversion for EXTENDED-STARKNET across the backfill window. Repo:
      mtds / instruments-service (defi/cefi perp).
- [ ] [CODE] P2. **Harden MTDS Extended candle sharp edge (silent truncation).** Source: same doc. The live
      `_umi_extended.py` candle fetch sends `{interval, limit:1440, endTime}` with NO `startTime`; the API caps a single
      response at ~2800-3000 rows and returns the most-recent `limit` ending at `endTime`, so any window needing more
      than one page silently drops the earlier rows. Per-day shards (PT1M, 1440 bars) are currently safe, but add
      `startTime` + window-aware `limit` + a LOUD truncation warning so a multi-day/finer-interval call can never
      under-capture silently. Done when: a deliberately-oversized window request either pages correctly or loudly warns
      instead of silently truncating (regression test). Repo: mtds.
- [ ] [CODE] P3. **Align/consolidate the two parallel Extended candle paths.** Source: same doc. The live path is
      `adapters/_umi_extended.py`; `market_interface/adapters/onchain_perps/extended_adapter.py::ExtendedAdapter` is a
      separate, tested-but-unused parallel impl that still carries the global `EXTENDED_DEPLOY_DATE` pre-launch floor
      (vs the live path's per-instrument genesis). Decide: wire `ExtendedAdapter` as canonical (making its
      `_check_pre_launch` per-instrument first) OR delete it (confirm zero live importers first — a grep-then-READ
      check, not an assumption). Parallel-paths anti-pattern per the Delete-Deprecated-Code HARD RULE. Done when: only
      one Extended candle path remains live, QG green. Repo: mtds.
- [ ] [DATA] P3. **Sports catalogue `mvp` column is 100% False (numeric league IDs vs `is_mvp()` canonical strings).**
      Source: same doc. `prod/catalog.parquet`'s `league_id` holds NUMERIC provider IDs (`'10'`/`'100'`) while
      `is_mvp()`'s sports MVP rule keys canonical strings — so no sports league ever tags `mvp=True` in the catalogue.
      Map the provider `league_id` → canonical league_id (UAC `league_data`/`provider_league_ids`) before the `is_mvp()`
      check in `build_instrument_catalogue.py`. **Check against the v10 94-football-league MVP set**
      (`/codex/02-data/mvp-scope-canonical.md`, `_mvp_football_league_ids()`), NOT the doc's own stale 4-league pre-v10
      reference. Low-risk display/classification fix (the MVP tag is unused downstream today). Done when: a fresh
      catalogue build tags at least one MVP-qualifying league `mvp=True`. Repo: instruments-service
      (`build_instrument_catalogue.py`).
- [ ] [SCRIPT] P2. **Diagnose the SFI backfill mid-processing hang + add a request timeout + per-date isolation.**
      Source: same doc. The SFI backfill log froze ~4min post-launch with no crash (SFI key confirmed working). Check
      for an SFI-API request timeout / manifest-write stall as the cause; add a bounded request timeout + per-date
      isolation so a single hung request can't freeze the whole chunk, then relaunch the SFI chunks. Done when: a
      relaunched SFI backfill either completes or fails loud+isolated (never silently hangs), verified via a fresh run.
      Repo: market-tick-data-service (collector) + deployment-service (launcher).
- [ ] [SCRIPT] P2. **Apply the parallelization pattern to the sfi/sports collector's per-date sequential loop within the
      RapidAPI rate budget.** Source: same doc. The sfi/sports collector's per-date loop is needlessly serial on top of
      being rate-limited; apply the same parallelization pattern already used elsewhere, with concurrency capped so it
      does not increase 429s (the RapidAPI 4 req/s limit is per-ACCOUNT, not per-worker — cap total concurrent requests
      across all workers, not per-worker). Done when: a backfill run shows reduced wall-clock time with no increase in
      429 rate. Repo: instruments-service (SFI adapter) + market-tick-data-service (sports orchestration).
- [ ] [SCRIPT] P2. **`launch-sfi-backfill-vm.sh` must DEFAULT SFI to a single stream (or refuse `--chunks N>1`).**
      Source: same doc. The RapidAPI key's 4 req/s limit is PER-ACCOUNT, not per-VM — N parallel chunks just multiply
      429 collisions (measured: 4-chunk-parallel sharing one key produced WORSE aggregate throughput than one clean
      stream). The `sfi_chunk_parallel_backfill_2026_04_22` plan's premise (independent per-chunk rate budgets) is
      invalid for a shared key and should be treated as superseded. Optionally tighten the per-instance pace 0.34s→0.25s
      to use the full 4/s on the single stream. Done when: the launcher script either defaults to a single stream or
      hard-refuses `--chunks N>1`. Repo: deployment-service (launcher) + instruments-service (`soccerfootball_info.py`
      `_min_request_interval`).
- [ ] [SCRIPT] P3. **`launch-mtds-prediction-backfill-vm.sh` singleton lock must be per-venue.** Source: same doc. The
      lock currently matches `^mtds-prediction-`, so a KALSHI run is blocked by a concurrent POLYMARKET run even though
      they hit different APIs with no shared rate limit. Make the lock per-venue (`^mtds-prediction-{venue}-`);
      `--force` is the current bypass and should no longer be needed for this specific case once fixed. Done when: a
      KALSHI and a POLYMARKET backfill can run concurrently without the singleton lock blocking either. Repo:
      deployment-service.
- [ ] [TEST] P3. **Re-baseline the UEI-lifecycle contract-call ratchet for `canonical/crosscutting/honest_coverage.py`
      post-split.** Source: same doc. Commit `27a80d2` ("feat(freshness): feed-SLA Phase 1") split the honest_coverage
      cluster registries out from `honest_coverage.py` (900-line cap), so the UEI-lifecycle contract-call baseline of 27
      moved WITH the split calls into the new registry files (the file now carries ~21, was 27) — not a deletion, not a
      regression. Re-baseline the ratchet across `honest_coverage.py` + the split-out registry files' combined call
      count so the warn-tier cross-repo line reflects the post-split file set accurately. Done when: the ratchet
      baseline is updated and both UAC + IS QG pass with the new baseline. Repo: unified-api-contracts.

## Flagged, not extracted (stale-checkbox, needs the source doc's own maintainer to re-verify)

- **"Wire Kalshi into the pipeline (hist + live market data)"** — conflict-check found this is very likely already done:
  `data_completion_to_100_all_ag_2026_06_21.md` records a Kalshi deep-history seed backfill that RAN (VMs
  `mtds-prediction-kalshibulk-*`) with live capture confirmed (`live_kalshi` present, rows `empty_confirmed`/captured),
  and `prediction_live_clob_depth_capture_2026_07_24.md` records a Kalshi trades-adapter URL fix SHIPPED + verified
  (`kalshi_adapter.py::get_trades_with_status`). Not extracted as fresh work — flagging in the source doc instead so a
  future pass re-verifies against current manifest state and flips the checkbox rather than re-dispatching completed
  work.

## Codex SSOTs

`/codex/02-data/availability-manifest-and-data-status.md` (manifest/coverage model),
`/codex/02-data/defi-canonical-naming-ssot.md` (DeFi PROTOCOL-CHAIN grain), `/codex/02-data/mvp-scope-canonical.md` (v10
94-league sports MVP set).

## Progress Log

- **2026-08-09**: Batch authored via the round11 cross-cutting+ui RECLASSIFY + satellite-extraction sweep. 11 items
  extracted from `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` (`instruments_master`) — formalizing
  that doc's own 2026-08-07 audit finding that roughly half its 22 open items were independently bounded/mechanical and
  never split out. Conflict-checked against all 6 active `cross_cutting_satellite_ao_dispatch_batch*` docs (grepped
  clean) and the sibling `instruments_master` satellite/finalize docs before extraction. One named candidate ("Wire
  Kalshi into the pipeline") was excluded after conflict-check found live evidence the work already happened elsewhere —
  flagged in the source doc instead of re-dispatched. The `ohlcv-1s`/`BarTimeframe` closed-set extension item was
  deliberately NOT extracted despite being named in the source doc's own audit list — on full read it is a
  multi-service, one-commit closed-set schema extension (UAC + MTDS + features-service + every OHLCV write-callsite),
  too broad a blast radius for a single bounded AO todo; left as-is in the source doc.
