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

- [x] ✅ [CODE] P3. **`--operation status --asset-group prediction` can't read the flat-kind bucket — STALE PREMISE on
      the named path + ADJACENT FIX in `_run_reprocess_shards`.** Source:
      `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`. The named `_run_coverage_status` status-path bug
      was already fixed at `instruments-service@086eeffe` (2026-08-03 — 6 days before this plan was authored): line 79
      already routes through `get_instruments_bucket_for_asset_group`, the prediction-aware resolver. The ADJACENT
      same-class bug in `_run_reprocess_shards` (line 295, still used
      `get_write_bucket_name("instruments", asset_group)` — same BucketNamingError for prediction) was fixed in this
      same commit. Done when: `--operation status --asset-group prediction` AND
      `--operation reprocess-shards --asset-group prediction` both resolve the flat bucket. Repo:
      instruments-service@c8e3686ca4.
- [x] ✅ [CODE] P2. **DeFi venue-grain — align the ADAPTER/writer shard key to the decided PROTOCOL-CHAIN grain — STALE
      PREMISE, already shipped (verification only).** Source: same doc. This exact fix landed on
      `instruments-service@6b7fbadf`/`ec73983e` (2026-08-05,
      `fix(defi): align multi-chain adapter venue property to PROTOCOL-CHAIN grain`, 42 adapter files + 49 test
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
      (`VENUES=EXTENDED-STARKNET SHARD_DAYS=60 CUTOFF_DATE=2026-08-08 SYMBOLS=ALL`) — 13 SPOT VMs sharding
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
- [x] ✅ [CODE] P3. **Align/consolidate the two parallel Extended candle paths — STALE PREMISE, already shipped
      (verification only).** Source: same doc. The parallel `ExtendedAdapter`
      (`market_interface/adapters/onchain_perps/extended_adapter.py`) was already DELETED at
      `market-tick-data-service@f6bda91b` (2026-06-24 — six weeks before this batch-11 doc was authored 2026-08-09):
      `refactor(market-interface): delete unused ExtendedAdapter/Starknet parallel path` removed `extended_adapter.py`,
      `clients/extended_base_client.py`, the sole integration test (`integration/test_extended_starknet_adapter.py`),
      and the `__init__` re-exports — the commit message explicitly names `adapters/_umi_extended.py` via
      `umi_tick_provider._route_extended` as the canonical EXTENDED-STARKNET path. Verified against current HEAD, not
      just the commit log: (1) zero references to `extended_adapter`/`ExtendedAdapter`/`extended_base_client` anywhere
      in the tree (`rg` exit 1); (2) `onchain_perps/__init__.py` re-exports only Aster/Hyperliquid/Base,
      `clients/__init__.py` has no extended_base_client; (3) the global `EXTENDED_DEPLOY_DATE` floor is gone — zero
      matches — the live path `_umi_extended.py` uses per-instrument/venue-aware handling (`_EXTENDED_FUNDING_START_MS`
      aligned to the UAC `coverage_start`, live symbol resolution from `/info/markets`); (4) exactly ONE candle-fetch
      path remains live: `fetch_extended_candles` in `_umi_extended.py`, routed through
      `umi_tick_provider._route_extended` (line 592) → `_fetch_extended_candles`, with current unit coverage
      (`test_extended_candles.py`, `test_umi_extended_book_gate.py`, `test_umi_tick_provider_coverage.py`). Repo:
      market-tick-data-service (verified, no change needed) @f6bda91b.
- [x] ✅ [DATA] P3. **Sports catalogue `mvp` column is 100% False (numeric league IDs vs `is_mvp()` canonical strings) —
      STALE PREMISE, ALREADY WORKING (verified 2026-08-10, slot 24).** No code change needed in
      `build_instrument_catalogue.py` — the numeric→canonical mapping is moot because the catalogue `league_id` is
      ALREADY canonical end-to-end. Measured evidence (read-only, against the LIVE prod catalogue
      `gs://instruments-store-sports-prd-central-element-323112/prod/catalog.parquet`, rebuilt 2026-08-10 10:52Z): (1)
      **0 numeric `league_id` rows** (532,868 rows, all canonical strings like `ALLSVENSKAN`/`EPL`); (2) all 96 v10 MVP
      football leagues (`_mvp_football_league_ids()`) present in the catalogue are tagged `mvp=True` — **0 false
      negatives**; 272,006 rows `mvp=True` today, and recomputing with the CURRENT UAC `is_mvp` yields 267,893
      `mvp=True` — the done-condition ("a fresh build tags ≥1 MVP-qualifying league `mvp=True`") is met by the live
      catalogue. The ONLY anomaly is a STALE false positive: `SEGUNDA_DIVISION` (4,113 rows, a non-canonical alias of
      the Spanish second tier) is tagged `mvp=True` — current `is_mvp` returns False for it, so a rebuild with current
      code drops it (cosmetic; the MVP tag is unused downstream today). Original premise (numeric provider IDs → no
      league ever tagged True) reflects the 2026-06-19 catalogue verify; superseded by the later canonicalization of the
      sports by_date source (`sports_reference/by_date/.../league=<canonical>` paths + the MTDS odds adapter
      `_canonical_league_id`). Repo: instruments-service (`build_instrument_catalogue.py`).
- [x] ✅ [SCRIPT] P2. **Diagnose the SFI backfill mid-processing hang + add a request timeout + per-date isolation —
      STALE PREMISE, already shipped (verification via 3 real production runs).** Source: same doc. The described
      2026-06-19 hang was already root-caused and fixed well before this batch was authored (2026-07-24 source doc /
      2026-08-09 extraction): (1) bounded per-request HTTP timeouts (`sock_connect=15s`, `sock_read=60s`, `total=120s`)
      landed `instruments-service@0261e4259` (2026-06-19) in
      `reference_data/adapters/sports/adapters/base.py::_make_session()` — the docstring there names this exact incident
      as root cause; (2) per-match `asyncio.wait_for(..., timeout=30.0)` +
      `asyncio.wait_for(get_match_descriptors_for_date, timeout=60.0)` with per-match try/except shard isolation landed
      `instruments-service@367afc6e0` (2026-06-24) in `engine/orchestrator/sfi.py::_fetch_sfi_data`; (3) the launcher's
      `--chunks` ban (SFI's RapidAPI key is per-account, N>1 chunks multiply 429s) landed `deployment-service@51cbacd9d`
      (2026-06-19); (4) a VM-level silent-stall watchdog (`STALL_PROGRESS_REGEX=league`, `vm-exec-with-gcs-tee.sh`
      kills+dumps the worker if no matching log line lands within `STALL_TIMEOUT_SEC`) landed
      `deployment-service@a8ee104e5` (2026-06-22). **Verified via a fresh run — not a newly-launched VM, but 3 real
      recent production SFI backfill VMs already run since**: `sfi-backfill-20260806-140815`,
      `sfi-backfill-20260807-101503`, `sfi-backfill-20260807-123519` (GCS logs at
      `gs://deployment-scripts-central-element-323112/vm-logs/<name>/run.log`) — all three completed cleanly
      (`exit_code=0`, monotonic `[[VM_PROGRESS]]` advancement, no `WORKER_STALLED` breadcrumb) despite hitting real
      transient errors mid-run (a 429 storm on the GCS manifest-cache write in the first; 10 JSON-truncation errors from
      the SFI API in the third) — each error was caught, classified, and recorded via the existing per-match shard
      isolation without ever stalling the run. Done-when clause ("relaunched SFI backfill either completes or fails
      loud+isolated, never silently hangs, verified via a fresh run") is satisfied — no code change needed in either
      named repo. **Distinct finding surfaced during this verification (NOT this todo — a low-frequency data-quality
      gap, not a hang)**: `/plans/active/issues/sfi_progressive_stats_json_truncation_2026_08_09.md` (10/2254
      date-completions in one run hit an unretried `json.JSONDecodeError`-shaped truncation; already honestly recorded
      via shard-level `record_failed`, filed as a P3 follow-up). Repo: instruments-service (verified, no change needed)
      / deployment-service (verified, no change needed).
- [x] ✅ [SCRIPT] P2. **Apply the parallelization pattern to the sfi/sports collector's per-date sequential loop within
      the RapidAPI rate budget.** — instruments-service@8afe2053. Source: same doc. **Correction to this todo's own repo
      attribution**: SFI/soccer-football-info is entirely owned by instruments-service (no SFI/RapidAPI code exists in
      market-tick-data-service — confirmed via repo-wide grep; MTDS's sports adapters are a separate provider,
      Sportradar/odds, unrelated to SFI). The needlessly-serial loop is the per-MATCH progressive-stats fetch inside
      `_fetch_sfi_data()` (`instruments_service/engine/orchestrator/sfi.py`) — one
      `await adapter.get_progressive_stats(mid)` at a time across every completed match on a date. Applied the SAME
      bounded-concurrency pattern already used for api_football
      (`sports_reference_fixtures.py::_gather_per_fixture_rows`): `asyncio.Semaphore(5)` + `gather`. The adapter's
      existing `_throttle()` (`adapters/sports/adapters/base.py`) already self-enforces the RapidAPI 4 req/s account cap
      via a class-level lock-guarded token bucket (SFI `_min_request_interval=0.34s`) — that lock serialises every
      concurrent task onto the same send-rate slot, so the added concurrency only overlaps per-match network latency; it
      structurally cannot raise the actual request rate (no increase in 429s possible by construction). QG green
      (`quality-gates.sh`, instruments-service). **Live backfill wall-clock/429 measurement NOT run this session**
      (requires a real SFI backfill invocation against live RapidAPI — out of this todo's scope; the per-worker cross-VM
      concern this todo raised is otherwise moot per the sibling todo below, which retires multi-VM SFI chunking
      entirely). Repo: instruments-service (SFI adapter); market-tick-data-service has no SFI involvement.
- [x] ✅ [SCRIPT] P2. **`launch-sfi-backfill-vm.sh` must DEFAULT SFI to a single stream (or refuse `--chunks N>1`).**
      Source: same doc. The RapidAPI key's 4 req/s limit is PER-ACCOUNT, not per-VM — N parallel chunks just multiply
      429 collisions (measured: 4-chunk-parallel sharing one key produced WORSE aggregate throughput than one clean
      stream). The `sfi_chunk_parallel_backfill_2026_04_22` plan's premise (independent per-chunk rate budgets) is
      invalid for a shared key and should be treated as superseded. Optionally tighten the per-instance pace 0.34s→0.25s
      to use the full 4/s on the single stream. Done when: the launcher script either defaults to a single stream or
      hard-refuses `--chunks N>1`. Repo: deployment-service (launcher) + instruments-service (`soccerfootball_info.py`
      `_min_request_interval`). **STALE FINDING — already fixed pre-audit.** Verified 2026-08-09:
      `launch-sfi-backfill-vm.sh` has hard-refused `--chunks N>1` (exact same rationale — per-account rate limit, 429
      collision storms) since `deployment-service@51cbacd9` (2026-06-19), which predates this residuals doc's 2026-07-24
      source scan. The `--chunks` flag now only accepts `1`/unset; any `N>1` exits 1 with the refusal message; `CHUNKS`
      is unconditionally forced to `""` afterward so the dead chunked-fan-out code path below it never executes. No code
      change needed — flipping as already-shipped, not re-implementing. The optional pace tighten (0.34s→0.25s) was NOT
      applied (still 0.34s in `soccerfootball_info.py:43`) — left as-is since it's explicitly optional and outside this
      item's done-when.
- [x] ✅ [SCRIPT] P3. **`launch-mtds-prediction-backfill-vm.sh` singleton lock must be per-venue — STALE PREMISE,
      already shipped by slot 28.** Source: same doc. The exact fix described — per-venue singleton lock
      (`^mtds-prediction-${VENUE_LOWER}-`), `VENUE_LOWER` variable, updated error message, DRY'd VM_NAME — landed at
      `deployment-service@fce66018` ("fix(scripts): make mtds-prediction singleton lock per-venue", 2026-08-11 00:30
      UTC) before this task was dispatched to slot 22. Verified against current HEAD: filter reads
      `name~^mtds-prediction-${VENUE_LOWER}-`, KALSHI and POLYMARKET runs no longer block each other. No code change
      needed. Repo: deployment-service@fce66018.
- [x] ✅ [TEST] P3. **Re-baseline the UEI-lifecycle contract-call ratchet for
      `canonical/crosscutting/honest_coverage.py` post-split — STALE PREMISE, baseline already accurate (verification
      only).** Source: same doc. This is the per-file adapter/manifest contract-call ratchet —
      `unified-trading-pm/scripts/quality_gates/check_adapter_contract_regression.py` (QG STEP 5.83, invoked cross-repo
      via `base-service.sh`/`no_adapter_contract_regression.sh` against the shared `adapter_contract_baseline.yaml`,
      scanning the whole workspace regardless of which repo's QG triggers it — the "cross-repo line" the todo refers
      to). Verified live: the baseline already carries separate, correct entries for `honest_coverage.py` (38) and all
      three split-out registry files created by `27a80d2` and later commits — `_honest_coverage_clusters.py` (4,
      baselined 2026-06-22, 3 days after the split), `_honest_coverage_empty_reasons.py` (5, last touched 2026-08-10),
      `_honest_coverage_logic.py` (11, baselined 2026-06-11) — summing to 58 combined contract calls across the
      post-split file set. Direct pattern-count against the live files matches the baseline exactly (38/4/5/11, zero
      drift), and running `check_adapter_contract_regression.py --regenerate-baseline` over the whole workspace produced
      a **byte-identical** `adapter_contract_baseline.yaml` (`git diff --stat` empty) — definitive proof the baseline
      already reflects current reality with no stale entry. The scanner's own workspace-wide run reports
      `OK — 361 baselined file(s) at or above minimum`. UAC's own QG (`base-library.sh`) doesn't invoke this
      service-template-only check directly, but IS's QG (`base-service.sh`) does and it passes cross-repo, which is what
      the done-when's "both UAC + IS QG pass" resolves to. No baseline edit, no code change. Repo: unified-api-contracts
      (verified, no change needed).

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

- **2026-08-09**: SFI mid-processing-hang todo (P2) flipped — STALE PREMISE, the described 2026-06-19 hang was already
  fixed via bounded HTTP timeouts (`instruments-service@0261e4259`, 2026-06-19), per-match `asyncio.wait_for` shard
  isolation (`instruments-service@367afc6e0`, 2026-06-24), the `--chunks` ban for SFI's shared-key rate limit
  (`deployment-service@51cbacd9d`, 2026-06-19), and a VM-level silent-stall watchdog (`deployment-service@a8ee104e5`,
  2026-06-22) — all landing weeks before this batch's 2026-07-24 source doc. Verified via 3 real recent production SFI
  backfill runs (`sfi-backfill-20260806-140815`,`-20260807-101503`,`-20260807-123519`) — all completed cleanly
  (`exit_code=0`) despite hitting real transient errors (a 429 storm, 10 JSON-truncation errors) mid-run, each correctly
  shard-isolated without stalling. No code change needed in either named repo. Distinct low-frequency data-quality
  finding (JSON truncation on ~0.4% of date-completions in one run, NOT a hang) filed as
  `/plans/active/issues/sfi_progressive_stats_json_truncation_2026_08_09.md`.
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
- **2026-08-10**: Prediction flat-kind bucket item (P3, todo 1) flipped — STALE PREMISE on the named code path
  (`_run_coverage_status` was already fixed at `instruments-service@086eeffe`, 2026-08-03, 6 days before this plan was
  authored) + ADJACENT FIX for the same-class bug in `_run_reprocess_shards` (line 295 still used
  `get_write_bucket_name("instruments", asset_group)` — same `BucketNamingError` for prediction). Route both through
  `_get_instruments_bucket_for_asset_group`, the prediction-aware flat-kind resolver. Repo:
  instruments-service@c8e3686ca4.
- **2026-08-10**: Extended candle parallel-path todo (P3, todo 6) flipped — STALE PREMISE, the parallel
  `ExtendedAdapter`/Starknet path was already deleted at `market-tick-data-service@f6bda91b` (2026-06-24, six weeks
  before this batch was authored): `refactor(market-interface): delete unused ExtendedAdapter/Starknet parallel path`
  removed `extended_adapter.py` + `clients/extended_base_client.py` + the integration test + the `__init__` re-exports,
  keeping `_umi_extended.py` (via `umi_tick_provider._route_extended`) as the single canonical EXTENDED-STARKNET path.
  Verified against current HEAD: zero `extended_adapter`/`ExtendedAdapter`/`extended_base_client` references anywhere,
  the global `EXTENDED_DEPLOY_DATE` floor is gone (live path uses per-instrument/venue-aware handling aligned to UAC
  coverage_start), and exactly one candle-fetch path remains (`fetch_extended_candles` in `_umi_extended.py`). No code
  change needed.
- **2026-08-10 (slot 24, data_engineering, task `cross_cutting_satellite_ao_dispatch_batch11-0d6336a233f8`)**: sports
  catalogue `mvp` todo (P3, todo 7) flipped — **STALE PREMISE, already working**. Read-only verification against the
  LIVE prod sports catalogue (`instruments-store-sports-prd-central-element-323112/prod/catalog.parquet`, rebuilt
  2026-08-10 10:52Z): 0 numeric `league_id` rows (all canonical), all 96 v10 MVP football leagues present tagged
  `mvp=True` (0 false negatives), 272,006 rows `mvp=True`; recomputing with current UAC `is_mvp` yields 267,893
  `mvp=True` — done-condition met. The numeric-ID premise reflects the 2026-06-19 catalogue verify; the sports by_date
  source + MTDS odds adapter have since canonicalized league_id end-to-end. No code change needed. One stale false
  positive observed (`SEGUNDA_DIVISION`, 4,113 rows — a non-canonical Spanish-second-tier alias tagged `mvp=True` by the
  build's UAC version; current `is_mvp` returns False, so the next catalogue rebuild drops it; cosmetic, MVP tag unused
  downstream). Source checkbox in `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` stays open for the
  batch-11 finalize twin to reconcile.
- **2026-08-10 (slot 24)**: recovery note — the safe-doc-push prek-patch orphan incident
  (`safe_doc_push_prek_patch_not_restored_on_retry_success_2026_08_09.md`) manifested on this commit's push: a retried
  commit stashed unstaged foreign WIP into `~/.cache/prek/patches/` and the restore step never ran. Restored via
  `git apply`, then verified the content had ALREADY landed on origin via its owners (cefi batch9 LC_TARBALL flip @
  `43ec2ec651`, sports_af monitoring tick @ `395b50bc83`) — resolved all conflicts to origin, no duplicate commit. No
  impact on this task's mvp flip (`8a561c3ed0`).
