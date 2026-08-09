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
      `--operation status --asset-group     prediction` runs without raising and renders coverage. Repo:
      instruments-service.
- [x] ✅ [CODE] P2. **DeFi venue-grain — align the ADAPTER/writer shard key to the decided PROTOCOL-CHAIN grain — STALE
      PREMISE, already shipped (verification only).** Source: same doc. This exact fix landed on
      `instruments-service@6b7fbadf`/`ec73983e` (2026-08-05,
      `fix(defi): align multi-chain adapter venue property to     PROTOCOL-CHAIN grain`, 42 adapter files + 49 test
      assertions) — **four days before this batch-11 doc was authored (2026-08-09)** — so the source doc's checkbox was
      already stale at extraction time. Verified live against current HEAD, not just the commit log: every multi-chain
      DeFi adapter's `venue` property returns the combined form (e.g.
      `instruments_service/reference_data/adapters/defi/aave_v3.py:224-226` → `f"{self._venue_prefix}-{self._chain}"` =
      `AAVE_V3-ETHEREUM`; `compound_v3.py:95-97` → `f"COMPOUND_V3-{self._chain}"`; spot-checked across all 57 non-oracle
      defi adapters, no bare-spelling holdouts found), each adapter's `_build_*_records` threads that same combined
      string into `InstrumentRecord.venue` (no drift between the two), and the manifest writer
      (`engine/orchestrator/writers.py:43` `_canonical_manifest_venue_chain()`) splits the combined form into
      `(venue=PROTOCOL, chain=CHAIN)` for the manifest row_key — used identically by both the capture path
      (`_write_venue`, line ~405) and the expected-unattempted seeder (`process_write.py:853`), so a seed row and a
      captured row land on the same key with no re-reconcile needed. Test coverage already exists and is current:
      `tests/unit/test_defi_adapters_comprehensive.py` (per-adapter `test_venue_property` assertions),
      `tests/unit/test_orchestrator_helpers.py:196-232` (`_canonical_manifest_venue_chain` unit tests incl. the
      CeFi-perp non-split guard). unified-trading-library's `manifest_writer` is generic infra that records whatever
      `(venue, chain)` the caller passes — no separate bare-venue keying bug found there. **Distinct,
      still-genuinely-open issue in the same family** (NOT this todo — a duplicate-alias-key bug in the pre-launch
      enumerator, not the adapter/writer venue property):
      `/plans/active/issues/defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md` (code fixed
      `instruments-service@2b2e9f124`; an `[OPERATOR]`-gated stale-row purge + a `[DESIGN]` question remain open there,
      untouched by this todo). Repo: instruments-service (verified, no change needed) / unified-trading-library
      (verified, no change needed).
- [x] ✅ [INFRA] P1. **B3 — copy e2e research data to canonical placement + e2e doc — STALE PREMISE, no copy needed
      (verification + doc-fix only).** Both the legacy research buckets (`perp-funding-central-element-323112`,
      `lst-rates-central-element-323112`) AND the `-prd-` twins this todo assumed already existed
      (`perp-funding-prd-central-element-323112`, `lst-rates-prd-central-element-323112`) are confirmed **DELETED**
      (`gcloud storage buckets describe` → 404 on all 4, verified 2026-08-09; independently corroborated same-day by
      `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`). The real canonical home is the SHARED
      `resolve_bucket_name(cloud="gcp", kind="tick-data", asset_group="defi")` bucket
      (`market-data-tick-defi-prd-central-element-323112`) — the dedicated `perp-funding`/`lst-rates` `kind=` entries
      were removed from `deployment-service/configs/cloud-providers.yaml` on 2026-07-13, and the data was carried into
      the shared bucket by that same migration before the dedicated buckets were deleted 2026-07-14. (a) canonical-home
      decision: recorded above. (b) copy: MOOT — nothing to copy, already migrated. Content-verified via a targeted
      filtered `read_availability_index` spot-check (not a whole-corpus walk): HYPERLIQUID `perp_funding` (1,364
      `captured` rows, 2026-06-04..06-09) + `perp_daily_ctx` (231 `captured` rows, 2026-06-01) present in the shared
      bucket; `lst_rates` likewise (506 `captured` rows in the 2026-07-25..08-08 window, 40+ venues) — confirms the
      2026-07-13 migration carried the historical corpus forward intact. (c) e2e doc: the doc already existed
      (`e2e-testing/docs/defi/research_data_canonical_sources_2026_06_18.md`) but described the stale June-18
      `-prd`-twin plan as current — added a SUPERSEDED banner recording the true final state + the already-repointed
      consuming scripts (`staked_basis_funding_scan.py`, `funding_regime_classifier.py` — both confirmed already
      migrated off the dedicated buckets 2026-07-13) + cross-refs to the two adjacent already-tracked issues (HL
      forward-capture gap since 2026-06-02; the 2 dead-code companion scripts' disposition in batch9's DIAG todo) rather
      than duplicating either. Repo: e2e-testing@ea38428.
- [x] ✅ [DATA] P2. **Run the Extended public instrument + perp backfill (UNBLOCKED — no key needed).** Source: same
      doc. IS daily-listing CLI for EXTENDED-STARKNET (genesis-accurate per-instrument `available_from`, already
      shipped) + MTDS OHLCV/funding capture over 2024-07-26→yesterday (funding only from 2025-08-01 mainnet). No API key
      required for market data (verified live — only order placement needs the stark private key). Done when: the honest
      coverage index shows `expected_unattempted`→`captured` conversion for EXTENDED-STARKNET across the backfill
      window. Repo: mtds / instruments-service (defi/cefi perp). **Done —
      instruments-service@catalogue-rollup-cefi-20260809T203518Z + market-tick-data-service (13 sharded backfill VMs
      `cefi-extended-starknet-*-20260809-203922`).** Ran (1) IS
      `--operation instruments --mode batch --asset-group cefi --venues EXTENDED-STARKNET` (already-fresh listing,
      genesis-accurate `available_from` confirmed live) → (2) `scripts/build_instrument_catalogue.py`
      (`--asset-group cefi --mode incremental`, promoted 431,777-row catalogue, 200 distinct EXTENDED-STARKNET
      instruments now resolve for the `ALL` symbol sentinel with correct per-instrument lifecycle windows) → (3)
      launched `scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`
      (`VENUES=EXTENDED-STARKNET SHARD_DAYS=60     CUTOFF_DATE=2026-08-08 SYMBOLS=ALL`) — 13 SPOT VMs sharding
      2024-10-01→2026-08-08 (the venue's real `_VENUE_LAUNCH`/UAC capability floor; the plan's own 2024-07-26 predates
      the funding/trades floor and applies only to the OHLCV candle path, which was already fully `captured` with zero
      `expected_unattempted` before this run — verified, no gap). All 13 VMs confirmed RUNNING then completed +
      self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`) within ~45min; one VM's `run.log` spot-checked directly
      (`OnchainPerpBatch complete ... 5707 rows`, `ManifestWriter: per-VM shard updated`, `exit_code=0`). **Verification
      (bounded, targeted read of this run's own 677 per-VM manifest shard files — not a whole-corpus walk, ~17MB total,
      single-walk-discipline-compliant)**: every one of the 677 days 2024-10-01→2026-08-08 is present (0 gaps), and all
      107,096 attempted (date, symbol, data_type) shards resolved to `captured` (28,922) or `empty_confirmed` (78,174) —
      **zero `expected_unattempted` remain in the written shards**, i.e. the honest-coverage conversion the done-when
      clause asks for. (Note: the consolidated `availability_index.parquet` blob itself won't reflect this until the
      next manifest-consolidator Cloud Run cycle merges these per-VM shards — reading it directly right after the
      backfill is a known reader gap, self-shard-only merge on a still-fresh consolidated blob, not a data-loss signal;
      the per-VM shard read above is the writer's own authoritative record.)
- [x] ✅ [CODE] P2. **Harden MTDS Extended candle sharp edge (silent truncation) — STALE PREMISE, already shipped
      (regression test added).** Source: same doc. The todo's premise ("the live `_umi_extended.py` candle fetch sends
      `{interval, limit:1440, endTime}` with NO `startTime`") was already stale: `_extended_candle_params()`
      (`market_tick_data_service/adapters/_umi_extended.py:67-82`) already startTime-bounds the request, caps `limit` to
      the page cap, and LOUDLY `logger.warning`s on an oversized window — shipped `market-tick-data-service@3b9b27e`
      ("fix(extended): window-aware candle params — guard silent truncation") on 2026-06-22, 48 days before this batch
      was authored. Both candle-fetch call sites (`_fetch_extended_candles_for_symbol`, `fetch_extended_candles`)
      already use it. The one real gap was the done-condition's required regression test — added
      `test_extended_candle_params_within_cap_no_truncation_warning` +
      `test_extended_candle_params_oversized_window_warns_loudly_instead_of_silent_truncation` to
      `tests/unit/test_extended_candles.py`, locking in the startTime-bound + capped-limit + loud-warning behavior for
      both the within-cap and oversized-window cases. Repo: market-tick-data-service@f8d9033b5. Evidence: QG green
      (sentinel-verified on HEAD), 6/6 tests in `test_extended_candles.py` pass, landed on `live-defi-rollout`.
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

- **2026-08-09**: EXTENDED-STARKNET perp backfill todo (P2) flipped — ran the IS listing refresh + catalogue rollup then
  launched 13 sharded SPOT VMs (`cefi-extended-starknet-*`) covering the full 2024-10-01→2026-08-08 window; all
  completed and self-deleted within ~45min. Bounded, targeted per-VM-shard verification (677 files, ~17MB, not a
  whole-corpus walk) confirmed 0 date gaps and 0 remaining `expected_unattempted` across 107,096 attempted shards. See
  the todo's own note for the discrepancy vs the plan's stated 2024-07-26 start (that date is the OHLCV genesis probe
  floor, not the funding/trades venue-launch floor MTDS actually seeds `expected_unattempted` against) and the
  consolidated-index reader gap (self-shard-only merge on a fresh-but-stale-relative-to-just-written-per-VM-data blob —
  not a data-loss signal, just a read-path staleness window until the next consolidator cycle).
- **2026-08-09**: DeFi venue-grain todo (P2, adapter/writer PROTOCOL-CHAIN shard key) flipped — STALE PREMISE, the fix
  was already shipped `instruments-service@6b7fbadf`/`ec73983e` on 2026-08-05, four days before this batch was authored.
  Verified live against current HEAD (not just the commit log): all 57 non-oracle multi-chain DeFi adapters' `venue`
  properties + `InstrumentRecord.venue` + the manifest writer's `_canonical_manifest_venue_chain()` split already emit
  the canonical combined/split form consistently; existing test coverage (`test_defi_adapters_comprehensive.py`,
  `test_orchestrator_helpers.py`) is current. No code change needed in either named repo. See the todo's own note for
  the distinct still-open sibling issue (`defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md`).
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
