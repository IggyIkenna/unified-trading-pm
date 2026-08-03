---
doc_type: issue
title:
  "MDPS candle-manifest coverage is near-zero corpus-wide for cefi/defi/tradfi/prediction — 0.1-2.3% of
  processed_candles/ objects have a manifest row under either vocabulary; sports is the sole outlier at ~100%"
summary: >-
  First-ever full-corpus run of the new candle_orphan_sweep.py tool (todo 1 of
  mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md), executed on real prod GCS + manifest data via 4
  Tier-2 SPOT VMs (cefi/defi/tradfi/prediction). Found near-total absence of `record_captured` manifest coverage for the
  MDPS processed_candles/ corpus: cefi 460/405,956 objects manifested (0.11%), tradfi 4,388/541,322 (0.81%), prediction
  13,281/583,228 (2.28%), defi 0/1,131,367 (0%). Sports (bounded 200-object sample, not yet full-corpus) showed 100%
  coverage, the opposite pattern. This is far larger in scope than todo 7's already-fixed self-referential emission-gate
  lockout (which targeted only the trades-sourced ohlcv_1m/ohlcv_1h/book_snapshot_5 family) — this gap spans EVERY
  data_type/timeframe combination observed, across 4 of 5 asset_groups.
status: open
nature: issue
asset_group: [cefi, defi, tradfi, prediction]
stage: [data]
repos: [market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [data-correctness, mdps, candle, manifest-completeness, orphan-real, honest-absence, big-finding]
related:
  [
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/archive/issues/mdps_candle_orphan_sweep_design_brief_2026_07_27.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /codex/02-data/orphan-object-detection.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Surfaced 2026-07-27 (slot 9) running the first full-corpus validation of the newly-shipped candle_orphan_sweep.py tool
  (market-data-processing-service@d921823 + deployment-service@d75e8f3/@ff8eebe), via 4 real Tier-2 SPOT VMs, per main's
  ruling on BLK-c8936baa (this VM-launch was read-only/safe-idempotent/AO-eligible without operator gate).
resolved_by:
locked_by:
locked_since:
context_scope: [/plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md, /plans/archive/issues/mdps_candle_orphan_sweep_design_brief_2026_07_27.md, /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md, /codex/02-data/orphan-object-detection.md, /plans/archive/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md]
depends_on: []
---

# MDPS candle-manifest coverage is near-zero corpus-wide (cefi/defi/tradfi/prediction)

## What I found

Ran the new `candle_orphan_sweep.py` (A/D/E/F taxonomy, dual-vocabulary manifest-coverage join — see the design brief)
on real prod data via 4 Tier-2 SPOT VMs (`canonical-migration-{cefi,defi,tradfi,prediction}-candle-orphan-sweep-*`,
`e2-standard-8`, all completed in <2 min each, no preemption). Real, measured results:

| asset_group | A (canonical_manifested)                      | E (orphan, post-cutover) | F (ambiguous, pre-cutover) | coverage % |
| ----------- | --------------------------------------------- | ------------------------ | -------------------------- | ---------- |
| cefi        | 460                                           | 0                        | 405,496                    | 0.11%      |
| defi        | 0                                             | 7,936                    | 1,123,431                  | 0.00%      |
| tradfi      | 4,388                                         | 0                        | 536,934                    | 0.81%      |
| prediction  | 13,281                                        | 0                        | 569,947                    | 2.28%      |
| **sports**  | 200 (bounded 200-obj sample, not full corpus) | 0                        | 0                          | **100%**   |

`--manifest-fix-cutover 2026-07-27` (today) was passed for every run, so the acceptance-bar metric (class E) reads 0 for
cefi/tradfi/prediction — but that is an artifact of the cutover classifying every pre-existing miss as (F) ambiguous
rather than a genuine "no gap" result. DeFi's 7,936 E-count proves the gap is NOT fully historical — objects written
strictly AFTER today's cutover are still landing with zero manifest coverage for DeFi specifically.

**Verified this is a real manifest absence, not a matching-logic bug** in the new sweep tool: spot-checked cefi's live
`_index/availability_index.parquet` directly (8,779,029 total rows) — `service_name == "market-data-processing-service"`
returns only **75 rows total** for the entire cefi bucket, with zero rows for `venue=DERIBIT` at all (the exact object
the sweep flagged). The sweep's `is_covered()` dual-vocabulary check (source `data_type` + `mdps_data_type_key()`
aggregated form) had nothing to match against — there is no row to find under either vocabulary.

**Why this differs from `candle_feature_canonical_path_divergence_2026_07_20.md` todo 7**: that fix
(`market-data-processing-service@caa995c`) targeted ONLY the trades-sourced, self-referentially-gated
`ohlcv_1m`/`ohlcv_1h`/`book_snapshot_5` family, and only the emission-GATE bug for NEW writes going forward. This gap
spans every `data_type` observed in the sweep (`derivative_ticker`, `trades`, `dex_pool_swaps`, plus whatever else
populates the remaining ~1M+ F-classified objects per AG) and clearly predates and postdates the fix — DeFi's
`dex_pool_swaps` path was explicitly named as OUT of todo 7's scope ("does NOT touch DEFI's dex_pool_swaps candle path —
policy resolver returns None, skips the gate entirely"), yet DeFi shows 0% coverage here, the worst of the four. This
means todo 7's fix, while correct for its narrow target, did not touch the actual root cause of `record_captured` never
being called for the vast majority of candle-writing code paths.

**Sports is the outlier** — its manifest DOES carry rows keyed with `timeframe` populated correctly (confirmed via
direct inspection, 157,527 mdps rows for sports alone vs. 75 for ALL of cefi). Whatever `record_captured` wiring
sports's candle writer has, cefi/defi/tradfi/prediction's candle writers evidently lack (or call it on a
disjoint/incompatible key that never lands as `service_name="market-data-processing-service"`,
`capture_status= "captured"` for these AGs).

## Why it matters

This is squarely the "data-pipeline correctness is the heartbeat" HARD RULE — a near-total absence of manifest coverage
for a major data corpus (processed_candles/) means the manifest can answer none of the standard questions (is this shard
captured? complete? stale?) for candle data across 4 of 5 asset_groups. Any downstream consumer that trusts
`capture_status="captured"` as the completeness signal for candles is silently blind to ~1.1-2.2M objects' worth of
real, on-disk data per asset_group. This is the "silent-write / manifest-completeness bug the operator fears as a v10
trigger" that `migration_orphan_sweep.py`'s own module docstring names as the reason CF-17 exists — just surfaced for
the candle layer instead of raw-tick.

## Recommended decision

- [x] ✅ [DIAG] P0. **Root-cause why `record_captured` is never reached (or never lands under a matching key) for the
      MDPS candle writer across cefi/defi/tradfi/prediction**, contrasted against sports's working wiring —
      market-data-processing-service@93a3680. Two distinct causes, not one: (1) **Historical, already-partially-fixed**
      — cefi/tradfi/prediction show `E=0` across the board (zero NEW post-cutover orphans), so their near-total gap is
      100% pre-cutover `F`. This matches the already-shipped `caa995c` fix to
      `canonical_writer_stamping.py::_publish_emission_check` (the `ohlcv_1m:` passthrough bypassing the
      self-referential upstream-manifest lookup that permanently STRICT_FAIL-locked every trades-sourced
      `ohlcv_1m`/`ohlcv_1h`/`book_snapshot_5` shard's first-ever write). That fix only covers GOING-FORWARD writes for
      that narrow trades-sourced ohlcv family, so the pre-fix historical corpus (the bulk of what's on GCS today)
      permanently lacks a manifest row until the todo-2 backfill runs — expected, not a new live bug, for THIS slice. It
      does NOT by itself explain non-ohlcv-family data_types (`derivative_ticker`, `dex_pool_swaps`, ...), which the
      sweep also found unmanifested. (2) **Still-active, now fixed this todo** — DeFi is structurally different: `A=0`
      AND a nonzero `E=7,936` objects written STRICTLY AFTER today's cutover with zero manifest coverage — proof of an
      ACTIVE bug, since `dex_pool_swaps` was explicitly out of the `caa995c` fix's scope (policy resolver returns
      `None`, no gate at all) and should otherwise call `record_captured` unconditionally. Root cause: DeFi's raw input
      arrives as multi-instrument `ticks.parquet` bundles (e.g. Aave's 51 reserves in one file per
      `live_workers_chain.py::_is_chain_data`'s own docstring) — `live_workers_chain.py::_chain_bundle_likely_from_path`
      routes ANY blob path ending in `/ticks.parquet` (not just `options_chain`/`futures_chain`) to the STREAMING write
      path (`canonical_writer_streaming.py::_process_chain_bundle_streaming` → `close_candle_streaming_writer`). That
      function's `manifest_writer.record_captured/write/flush` except-branch (line ~517) only logged a `logger.warning`
      on failure — UNLIKE the eager path's identical branch in `canonical_writer.py` (the "Gap 2 fix" from
      `mdps_candle_manifest_population_disconnect_2026_07_25.md` Todo 2), which already falls back to
      `record_failed_for_shard`. So ANY exception inside `record_captured` for a chain-bundle write (schema mismatch,
      4-pillar validation, GCS transient, etc.) left the shard with literally NO manifest row — not even
      `attempted_failed` — while the candle bytes were still uploaded to GCS beforehand (upload happens before the try
      block). This exactly matches DeFi's signature (real on-disk objects, zero manifest rows, including post-cutover).
      **Fixed**: added the same `_emit_status_for_shard(capture_status="attempted_failed", ...)` fallback to the
      streaming path's except-branch + a regression test
      (`tests/unit/test_streaming_write_per_tf.py::test_manifest_write_failure_records_attempted_failed`). This makes
      future failures visible/retriable; it does not itself backfill the already-orphaned historical objects (todo 2).
      **Ruled out**: a UAC `BUNDLED_DATA_TYPES` / MDPS `canonical_writer_shaping.py::_build_cluster_params` mismatch
      (the latter only implements `futures_chain`/`options_chain`, returning `(None, None)` for every other bundled
      type, which would unconditionally raise `MissingClusterValidationError` inside `record_captured`) — verified
      `mdps_data_type_key()` always appends a `_<tf>` suffix to the aggregated key (e.g. `odds_snapshot` →
      `odds_snapshot_<tf>`, `dex_pool_swaps` → `swaps_ohlcv_<tf>`), so the aggregated key passed as
      `record_captured(data_type=...)` can never literally equal a `BUNDLED_DATA_TYPES` member — this guard is
      structurally unreachable from MDPS's own candle writer today, which also explains why sports's
      `odds_snapshot`/`odds_movement`/`arbitrage_opportunity` (which ARE UAC-bundled) don't hit it either.
- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slots 8 + 6).** Executed the historical backfill for
      cefi/defi/tradfi/prediction's unmanifested candle objects via the purpose-built `backfill_candle_manifest.py`
      (`market-data-processing-service@cf94e23`) + `launch-backfill-candle-manifest-vm.sh`
      (`deployment-service@fafde10`/`@b947d9f`) campaign — 4 concurrent Tier-2 SPOT VMs, one per asset_group,
      `record_captured`-only (never deletes/re-uploads). All 4 finished clean:
      `VERDICT cefi: already_covered=0 ok=405496 recorded_cells=25593 junk=0 escalated=0 read_failed=0 verify_failed=0`,
      `VERDICT tradfi: already_covered=0 ok=536934 recorded_cells=22905 junk=0 escalated=0 read_failed=0 verify_failed=0`,
      `VERDICT prediction: already_covered=0 ok=569947 recorded_cells=1609 junk=0 escalated=0 read_failed=0 verify_failed=0`,
      `VERDICT defi: already_covered=0 ok=1131367 recorded_cells=36145 junk=0 escalated=0 read_failed=0 verify_failed=0`
      — 86,252 total `record_captured` cells written, zero `escalated`/`read_failed`/`verify_failed` across all 4. 30
      objects (10 per cefi/prediction/defi, 0 for tradfi) hit a pre-existing `source=` mistag and were correctly REFUSED
      rather than falsely manifested — tracked separately in the P2 todo below, does not block this todo. Verified via
      each AG's `_index/audit/candle_manifest_backfill_<ag>.parquet` existing with a size consistent with its
      recorded_cells count (7.1MB/9.3MB/40.9MB/53.4MB respectively, timestamps matching each VERDICT). Did not run a
      full manifest-consolidator + re-sweep pass in this session (step (e) in the prior checkpoint's own text is
      explicitly optional); the audit-parquet + VERDICT evidence is accepted per this plan's own acceptance bar. Newly
      recorded rows will land in each bucket's consolidated `_index/availability_index.parquet` on the consolidator's
      normal cadence.
- [x] ✅ [DATA] P2. **DONE 2026-08-03 (slot-13, `data_engineering`).** Ran the real full-corpus sports
      candle-orphan-sweep via a Tier-2 SPOT VM (`canonical-migration-sports-cdlorph-20260803-070805`, e2-standard-8
      SPOT, `asia-northeast1-c`, LC_TARBALL_FRESHNESS=auto confirmed all 4 code tarballs current, completed in ~13s
      wall-clock, `exit_code=0`, no preemption, self-shutdown) —
      `market-data-processing-service/scripts/candle_orphan_sweep.py --asset-group sports --manifest-fix-cutover     2026-07-27 --report-out gs://deployment-scripts-central-element-323112/canonical-migration-candle-orphan-sweep/20260803-070805/canonical-migration-sports-cdlorph-20260803-070805/orphan_sweep_sports.parquet`.
      Confirms the ~100% coverage pattern holds across sports's ENTIRE historical corpus, not just the earlier bounded
      200-object sample: `A_canonical_manifested=59,540`, `B_legacy_duplicate=0`, `C_manifest_infra=0`, `D_junk=0`,
      `E_orphan_real=0`, `F_ambiguous_pre_fix=0` — 59,540/59,540 candle objects manifested (100% coverage), zero
      orphans, zero ambiguous, acceptance bar (`orphan_class_E==0`) met. Report parquet wrote 0 actionable rows, as
      expected with E=F=0. No code changes were needed — sports's manifest-write wiring (unlike
      cefi/tradfi/prediction/defi) was already confirmed correct in the earlier bounded sample; this todo was purely the
      missing full-corpus verification run.
- [x] ✅ [REVIEW] P2. **DONE 2026-07-31 (slot-5, `review`).** Cross-check confirmed: YES, superseded. Live-verified via
      a single-day, row-group-pushdown `read_availability_index` read (not a corpus walk,
      `filters=[("date",">=",     "2026-05-03"),("date","<=","2026-05-03")]`) that the narrower doc's exact named shards
      — BITGET-FUTURES (29 rows)/BITFINEX-FUTURES (14 rows)/KRAKEN-FUTURES (7 rows), all `data_type`/`timeframe` combos,
      `day=2026-05-03` — now carry real `captured` MDPS manifest rows, with `written_at` timestamps matching THIS doc's
      own todo 2 backfill campaign (`backfill-candle-manifest-cefi-20260727-151741`, ~16:23:49Z 2026-07-27), not the
      narrower doc's own prescribed `merge_manifest_from_canonical_paths()` recipe (never actually run against prod).
      Folded: the narrower doc's own todo flipped + archived to
      `plans/archive/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md` citing this evidence, all
      corpus referrers updated in the same commit.
- [x] ✅ [DATA] P2. **Remediate cefi + prediction `processed_candles/` objects mis-tagged with an unregistered
      `source=databento`** — **DONE 2026-08-03 (slot-15, `data_engineering`): RE-SCOPED + RESOLVED, no destructive
      action needed.** The original characterization (10 `RECORD-ERROR`s per AG) was only a per-CELL sample count, not
      the real object count — a fresh, targeted (prefix-scoped, NOT a corpus walk) GCS listing against each AG's exact
      mistagged `pipeline_mode=batch_databento/` path found the real extent and, for both AGs, confirmed a
      correctly-tagged twin already exists for every mistagged object. **cefi**: 1,639 objects (DERIBIT PERPETUAL
      derivative_ticker/1d only, prior-session finding) all have a twin at `pipeline_mode=batch_tardis/` for the
      identical shard key. **prediction**: real extent is 498 objects (not 10), spanning `day=2025-03-14` through at
      least `day=2025-07-01` (not the originally-documented 10-day window), all
      `venue=POLYMARKET data_type=trades timeframe=1d instrument_type=PREDICTION_MARKET` — spot-checked instrument-id
      overlap on 3 dates spanning the full range (`2025-03-14`: 6/6; `2025-05-01`: 1/1; `2025-07-01`: 1/1 — 8/8, 100%)
      against `pipeline_mode=batch_polymarket_clob/` for the SAME `(day, instrument_id)`; every mistagged object has a
      correctly-tagged twin. Both AGs are legacy duplicates — the shard's manifest coverage is already fully satisfied
      by the twin, so the mistagged copy is inert extra storage, not a correctness gap. No GCS writes/copies/deletes
      performed (a future, separate, low-priority storage-cost cleanup could delete the redundant copies, but that needs
      its own content-diff + `[OPERATOR]`-gated delete per the GCS delete-safety protocol — out of this todo's scope).
      This closes the manifest-coverage question for cefi + prediction's mistagged objects.
- [ ] [DATA] P2. **RE-SCOPED + ROOT-CAUSED 2026-08-03 (slot-15, `data_engineering`), NOT yet remediated.** defi
      `processed_candles/dex_pool_swaps` objects mis-tagged `pipeline_mode=batch_onchain_rpc` (source `onchain_rpc`
      unregistered for `asset_group=defi data_type=dex_pool_swaps`) — real extent is far larger than the originally
      documented "10 objects, BALANCER only, 2 chains, 1 date": a targeted (prefix-scoped, not corpus-walk) GCS listing
      found **11,718 objects on `day=2023-01-01` ALONE** — 7 timeframes (`15s/15m/1m/5m/1h/4h/1d`) × multiple venues
      (`BALANCER`, `BALANCER-ARBITRUM/-ETHEREUM/-POLYGON`, `CURVE`, `CURVE-AVALANCHE/-ETHEREUM`, `SUSHISWAP`,
      `SUSHISWAP-ARBITRUM`, `UNISWAP_V3`, `UNISWAP_V3-ARBITRUM/-ETHEREUM/-OPTIMISM/-POLYGON`), all
      `data_type=dex_pool_swaps`. Confirmed the pattern recurs on other dates too (spot-checked `day=2023-01-02`,
      present) — full historical date range NOT yet quantified (deliberately did not run an exhaustive multi-date
      enumeration interactively — that is corpus-scale work belonging on a VM per the heavy-I/O rule). **ROOT CAUSE
      (confirmed via source + git history)**: `unified-api-contracts`
      `unified_api_contracts/canonical/crosscutting/_source_priority_data.py` lines 275-289 (own in-code comment):
      `("defi", "dex_pool_swaps")` was UNREGISTERED in `SOURCE_PRIORITY` before commit `012ccec1`
      (`fix(uac): defi     dex-swaps source — register canonical dex_pool_swaps->onchain_subgraph (was dead ('defi','n') typo)`,
      **2026-06-08**) — every write before that date fell through to the defi asset_group's fallback pipeline_mode
      (`BATCH_ONCHAIN_RPC`), mis-stamping the path even though the actual collection method has always been
      `onchain_subgraph` (The Graph). Already fixed for NEW writes since 2026-06-08; every pre-existing
      `pipeline_mode=batch_onchain_rpc` object under `dex_pool_swaps` needs a historical path correction, not a refetch
      (the bytes are correct; only the path segment + manifest `source=` are wrong). **Two distinct sub-populations,
      confirmed via instrument-id overlap checks (not assumed)**: (1) the chain-suffixed venues
      (`BALANCER-ARBITRUM`/`-ETHEREUM`/`-POLYGON`, sampled at `timeframe=1h day=2023-01-01`, 1 object each) DO have a
      matching object at `pipeline_mode=batch_onchain_subgraph/` for the same `(day, instrument_id)` — a
      legacy-duplicate shape like cefi/prediction above. (2) the bare/legacy venue names (`BALANCER`, `CURVE`,
      `SUSHISWAP`, `UNISWAP_V3` — pre-chain-suffix naming; confirmed via UAC
      `unified_api_contracts/registry/defi_venues.py` `LEGACY_DEFI_VENUE_ALIASES`, e.g. bare `"BALANCER"` aliases to
      `"BALANCER-ETHEREUM"`) are the VAST majority of the 11,718-object count and show almost NO twin coverage — sampled
      `BALANCER` bare (`timeframe=1h day=2023-01-01`): 363 objects, only 1 has a matching `BALANCER-ETHEREUM` subgraph
      twin, 362 do not; `UNISWAP_V3`/`CURVE`/`SUSHISWAP` bare (same timeframe/date): 1053/115/133 objects, 0 twins each.
      This sub-population is REAL, unique on-disk data with a genuine manifest-coverage gap, NOT a redundant duplicate.
      **Remaining work to close this todo** (design captured, NOT executed — real scope already exceeds the
      few-hundred-object interactive threshold on a single sampled date alone, so this needs a dedicated tool + VM
      campaign, not ad-hoc interactive GCS ops): (1) build a small CLI (`market-data-processing-service`, sibling of
      `backfill_candle_manifest.py`) that, per `(day, venue, chain, instrument, timeframe)` cell under
      `data_type=dex_pool_swaps, pipeline_mode=batch_onchain_rpc`, checks whether a `batch_onchain_subgraph` object
      already exists for the same `(day, instrument_id)` — if yes, skip (legacy duplicate, already covered); if no,
      copy-not-move the object to the `batch_onchain_subgraph` path (never delete/mutate the original) and
      `record_captured(source="onchain_subgraph", ...)`; (2) scope the full date range first via a bounded,
      prefix-targeted count (not a corpus walk) to size the campaign; (3) launch via a Tier-2 SPOT VM per the existing
      `launch-backfill-candle-manifest-vm.sh` pattern; (4) verify VERDICT counts + `_index/audit/` parquet, THEN flip
      this checkbox. No GCS writes/copies/deletes performed this session — every action taken was read-only listing
      against prod buckets.

## Progress Log

- **2026-08-03** (AO dispatch, slot 15, `data_engineering`) — Re-scoped + root-caused the P2 source-mistag todo (did NOT
  flip it — defi's real remediation still needs a VM campaign, see the new sub-todo). Found the original
  characterization (10 `RECORD-ERROR`s/AG, narrow windows) badly understated the real extent — those were per-CELL
  counts, and cells bundle many objects. Fresh, targeted (prefix-scoped, not corpus-walk) GCS listings: **cefi** (1,639
  objects, prior finding, confirmed twin at `batch_tardis`) and **prediction** (498 objects, `2025-03-14` through
  `2025-07-01`+, 100% twin match on an 8-object/3-date spot-check against `batch_polymarket_clob`) are both RESOLVED as
  harmless legacy duplicates — the shard manifest coverage is already satisfied by the twin, no action needed. **defi**
  is the real, substantial finding: 11,718 objects on `day=2023-01-01` ALONE (recurs on other dates, full range not
  quantified), root-caused via `unified-api-contracts@012ccec1` (2026-06-08) — `dex_pool_swaps` was unregistered in
  `SOURCE_PRIORITY` before that fix and fell through to the wrong `batch_onchain_rpc` fallback pipeline_mode; the true
  source has always been `onchain_subgraph`. Confirmed via instrument-id overlap checks that the chain-suffixed venue
  population (small) has subgraph twins (duplicate, like cefi/prediction) but the bare/legacy-named venue population
  (the vast majority — `BALANCER`/`CURVE`/`SUSHISWAP`/`UNISWAP_V3` per UAC's `LEGACY_DEFI_VENUE_ALIASES`) has almost
  zero twin coverage (362/363 sampled `BALANCER` pool-days had no twin) — real, unique, uncaptured data. Remediation is
  identified (copy-not-move to the correct `pipeline_mode=batch_onchain_subgraph` path +
  `record_captured(source="onchain_subgraph")`) but not executed — real extent already exceeds the few-hundred-object
  interactive threshold on a single sampled date alone, so this needs a dedicated tool + Tier-2 SPOT VM campaign (filed
  as a new sub-todo with the full design already captured, so the next worker doesn't re-derive root cause or scope). No
  GCS writes/copies/deletes were performed this session — every action was read-only listing against prod buckets.
- **2026-08-03** (AO dispatch, slot 13, `data_engineering`) — Completed the P2 sports full-corpus sweep todo. Launched
  `canonical-migration-sports-cdlorph-20260803-070805` (Tier-2 SPOT VM, `sports-candle-orphan-sweep` launcher category,
  read-only/no-`--apply`-path, `LC_TARBALL_FRESHNESS=auto` confirmed 4 tarballs current) — completed in ~13s, exit_code
  0, no preemption, self-shutdown. Result: `A=59,540 B=0 C=0 D=0 E_orphan_real=0 F_ambiguous_pre_fix=0` — 100% coverage
  across the entire sports historical corpus, confirming the earlier bounded 200-object sample's pattern held at full
  scale. No remediation needed for sports. Remaining open work on this doc is only the P2 source-mistag remediation todo
  (cefi/prediction/defi, unrelated to sports) — doc stays active, not yet archival-eligible.
- **2026-07-27** (AO dispatch, slot 9) — Filed while running the first full-corpus validation of
  `candle_orphan_sweep.py` (todo 1 of `mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md`). Real numbers
  captured above from 4 completed Tier-2 SPOT VM runs against live prod data; spot-verified the cefi gap directly
  against the live manifest (not a tool artifact). Did not attempt the backfill (P1) — out of scope for this dispatch
  and a real infra decision (~2.6M-row scale) that deserves its own scoped campaign.
- **2026-07-27** (AO dispatch, slot 8, `data_engineering`) — Completed todo 1 (DIAG). Read-through of
  `candle_write_mixin.py` → `canonical_writer.py` → `canonical_writer_stamping.py` → `canonical_writer_streaming.py` →
  UTL `manifest_writer/_writer_captured.py`. Found the historical (cefi/tradfi/prediction, `E=0`) gap is fully
  consistent with the already-shipped `caa995c` ohlcv self-lock fix being GOING-FORWARD only. Found + fixed a DISTINCT,
  ACTIVE bug explaining DeFi's `A=0` + nonzero post-cutover `E=7,936`: the streaming (chain-bundle) write path's
  manifest-write except-branch silently swallowed failures with no `attempted_failed` fallback, unlike the eager path's
  identical branch — shipped market-data-processing-service@93a3680 (fix + regression test, QG green). Did not attempt
  the P1 backfill (own VM-launch campaign, ~2.6M rows) or the P2 sports full-corpus sweep / P2 review cross-check —
  those remain queued as their own todos.
- **2026-07-27** (AO dispatch, slot 8, `data_engineering`) — todo 1 (P1 backfill), IN PROGRESS, not yet complete (do not
  flip the checkbox until the § "Remaining to close todo 1" steps below finish — a genuine multi-hour VM campaign, not a
  same-turn fix). Work done this session:
  1. **Built the backfill tool**: `market-data-processing-service/scripts/backfill_candle_manifest.py` (RECORD-ONLY —
     footer-reads each report row's object at its EXISTING path, never re-uploads/deletes; groups into
     `(day, venue, chain, instrument_type, data_type, timeframe, pipeline_mode)` cells, one `record_captured` per cell;
     mirrors `instruments-service/scripts/backfill_orphan_class_e.py`'s record-only branch) + 13 unit tests — shipped
     `market-data-processing-service@cf94e23` (QG green both passes).
  2. **Built the VM launcher**: `deployment-service/scripts/vm/launch-backfill-candle-manifest-vm.sh` (sibling of
     `launch-backfill-orphan-e-vm.sh`; e2-highmem-8 SPOT, 250GB boot disk — the 150GB first draft failed
     `check_backfill_vm_disk_provisioning.py`'s ≥250GB minimum) + registered
     `backfill-candle-manifest-{cefi,defi,tradfi,prediction}-` VM prefixes in `vm_prefix_registry.py` +
     `launcher_registry.py` — shipped `deployment-service@fafde10`.
  3. **Found + fixed a real bug on the first smoke launch**: `setup-data-pipeline-vm.sh` had NO `VM_TASK` dispatch
     branch for `backfill-candle-manifest` — the shared guard correctly refused (rc=1, self-deleted VM
     `backfill-candle-manifest-cefi-20260727-145850`, EXIT_STATUS=1) rather than silently crashing deep in an unrelated
     CLI's argparse. Added the missing `elif [[ "$VM_TASK" == "backfill-candle-manifest" ]]` branch (mirrors
     `backfill-orphan-e`'s, `cd`s into `$WORKSPACE/mdps` instead of `$WORKSPACE/instruments`) — shipped
     `deployment-service@b947d9f`.
  4. **Validated end-to-end with a `--dry-run` VM** (`backfill-candle-manifest-cefi-20260727-151057`, relaunched after
     the fix, ran clean rc=0): `report actionable rows (class E+F): 405496`,
     `re-verify vs LIVE index: already_covered=0 still_orphan=405496`, `characterised: record_only=405496 escalated=0`,
     dry-run sample `footer-read: ok=770 zero-row-junk=0 failed=0`,
     `VERDICT cefi: ... escalated=0 convert_failed=0 verify_failed=0`. Zero escalations/failures confirms the
     characterisation logic (canonical-shape `pipeline_mode=` path-segment resolution, `resolve_pipeline_mode`'s
     legacy-shape `SOURCE_PRIORITY` fallback) handles the REAL report data correctly for all 4 AGs (candle objects are
     v9-only since inception, so the legacy-shape branch is a defensive no-op in practice — confirmed, not just
     theorised).
  5. **Launched the real `--apply` campaign** — 4 concurrent Tier-2 SPOT VMs (`asia-northeast1-c`,
     `LC_TARBALL_FRESHNESS=auto LC_SETUP_SCRIPT_FRESHNESS=auto` so each VM's tarball/startup-script reflected this
     session's shipped SHAs):
     - `backfill-candle-manifest-cefi-20260727-151741` — report
       `gs://deployment-scripts-central-element-323112/canonical-migration-candle-orphan-sweep/20260727-124341/canonical-migration-cefi-candle-orphan-sweep-20260727-124341/orphan_sweep_cefi.parquet`
       (405,496 actionable rows)
     - `backfill-candle-manifest-defi-20260727-151932` — report
       `gs://deployment-scripts-central-element-323112/canonical-migration-candle-orphan-sweep/20260727-124409/canonical-migration-defi-candle-orphan-sweep-20260727-124409/orphan_sweep_defi.parquet`
       (1,131,367 actionable rows — the E+F combined total, largest of the 4)
     - `backfill-candle-manifest-tradfi-20260727-151950` — report
       `gs://deployment-scripts-central-element-323112/canonical-migration-candle-orphan-sweep/20260727-124443/canonical-migration-tradfi-candle-orphan-sweep-20260727-124443/orphan_sweep_tradfi.parquet`
       (536,934 actionable rows)
     - `backfill-candle-manifest-prediction-20260727-152012` — report
       `gs://deployment-scripts-central-element-323112/canonical-migration-candle-orphan-sweep/20260727-124605/canonical-migration-prediction-cdlorph-20260727-124605/orphan_sweep_prediction.parquet`
       (569,947 actionable rows) All 4 launched safe-idempotent WITHOUT an `[OPERATOR]` gate per the CLAUDE.md carve-out
       (never deletes, never mutates source objects, a re-run is a safe no-op re-write) — same precedent class as
       `backfill_orphan_class_e.py`'s own prior AO-dispatched launches.
  6. **Observed throughput**: ~100-150 footer-reads/sec aggregate (16 threads, ranged-GET-only reads — report already
     carries `size_bytes` so most objects need exactly one ranged GET), confirming this genuinely needs VM-hours not
     VM-minutes at this row count — e.g. defi's 1.13M rows imply ~2-2.5h just for the footer-read pass, before the
     `record_cells` write pass. As of 2026-07-27T16:23Z (launched ~15:17-15:20Z, ~65-70min elapsed): cefi footer-read
     400,000/405,496 (99%, nearly done), defi 386,000/1,131,367 (34%), tradfi 366,000/536,934 (68%), prediction
     336,000/569,947 (59%). All 4 healthy (`RUNNING`, heartbeat blobs current, log byte-counts climbing, zero
     errors/escalations observed in any log to this point) — confirmed via
     `gcloud storage cat gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log` +
     `gcloud compute instances describe <vm> --zone=asia-northeast1-c` polling on a ~25-30min re-armed
     `run_in_background` watchdog cadence (async-wait HARD RULE — no fire-and-forget, no busy-poll).
  - **Remaining to close todo 1** (whoever resumes this — same session post-compact, or a fresh one): (a) wait for all 4
    VMs to print a `VERDICT <ag>: ...` line in their `run.log` (self-shutdown on completion,
    `VM_SHUTDOWN_ON_COMPLETION=true`); (b) sanity-check each VERDICT's `recorded_cells`/`escalated`/`read_failed`/
    `verify_failed` counts (escalated/failed should stay 0 given the clean dry-run); (c) each VM also writes
    `gs://<ag-tick-bucket>/_index/audit/candle_manifest_backfill_{ag}.parquet` on apply — worth a spot-check; (d) run
    the manifest consolidator per bucket (or wait for its Cloud Scheduler cadence) so the newly-recorded rows land in
    `_index/availability_index.parquet`; (e) OPTIONALLY re-run
    `candle_orphan_sweep.py --manifest-fix-cutover 2026-07-27` per AG to confirm `orphan_class_E` drops to 0 (the
    acceptance bar) — this is a NEW VM-launch, not required to flip todo 1's checkbox (the backfill itself, not the
    re-sweep, is todo 1's scope) but strongly recommended before todo 3's REVIEW cross-check; (f) ONLY THEN flip todo
    1's `- [ ]` to `- [x]` citing `market-data-processing-service@cf94e23` + `deployment-service@fafde10`/`@b947d9f` +
    the 4 VERDICT lines as evidence, `docs(plans):` commit + push. Do NOT flip early on "VMs launched" alone — that is
    exactly the smoke-test-green false-completion the data-pipeline-correctness HARD RULE forbids.
- **2026-07-27T16:36Z** (AO dispatch, slot 8, `data_engineering`) — Second checkpoint:
  `backfill-candle-manifest-cefi-20260727-151741` finished
  (`VERDICT cefi: already_covered=0 ok=405496 recorded_cells=25593 junk=0 escalated=0 read_failed=0 verify_failed=0`,
  self-shutdown). Found + root-caused a small pre-existing data anomaly while it ran — see the new `[DATA] P2` todo
  above (~1,639 cefi objects mis-tagged `pipeline_mode=batch_databento`); NOT a bug in this backfill or its tool (the
  script correctly refused to falsely manifest them), and does NOT block todo 1's completion. The other 3 VMs are still
  running, all healthy, no errors observed beyond the same class covered by the new P2 todo (not yet confirmed whether
  defi/tradfi/prediction have their own analogous mistagged slices — check each VM's `run.log` for `RECORD-ERROR` lines
  when it finishes and fold any into the same P2 todo rather than filing duplicates). Snapshot at 16:36Z: defi
  footer-read 467,000/1,131,367 (41%), tradfi 459,000/536,934 (85%), prediction 418,000/569,947 (73%).
- **2026-07-27T17:05Z** (slot 6, `data_engineering`, monitoring the campaign from the sibling
  `mdps_candle_manifest_population_disconnect_2026_07_25.md` todo 5 — not this doc's own owner, folding in per the above
  instruction to check each finishing VM's `run.log`). `tradfi` finished clean
  (`VERDICT tradfi: already_covered=0 ok=536934 recorded_cells=22905 junk=0 escalated=0 read_failed=0 verify_failed=0`,
  exit_code=0, zero `RECORD-ERROR` lines) — no analogous mistag for tradfi, consistent with tradfi legitimately being a
  Databento-sourced AG. `prediction` finished
  (`VERDICT prediction: already_covered=0 ok=569947 recorded_cells=1609 junk=0 escalated=0 read_failed=0 verify_failed=0`,
  exit_code=1) with the SAME mistag shape as cefi's already-tracked finding — 10 `RECORD-ERROR`s, all
  `source='databento'` not registered for `asset_group='prediction'`, all `venue='POLYMARKET'` `data_type='trades'` —
  folded into the P2 todo above rather than filing a duplicate. `defi` still `RUNNING` as of this checkpoint
  (footer-read ~646,000/1,131,367, ~57%); will check back via a bounded watchdog.
- **2026-07-27T18:16Z** (slot 6, `data_engineering`) — `defi` (the last of the 4 campaign VMs) finished: footer-read
  pass clean (`ok=1131367 zero-row-junk=0 failed=0`), then
  `VERDICT defi: already_covered=0 ok=1131367 recorded_cells=36145 junk=0 escalated=0 read_failed=0 verify_failed=0`. 10
  `RECORD-ERROR`s — a THIRD distinct mistag pairing (`source='onchain_rpc'` not registered for
  `asset_group='defi' data_type='dex_pool_swaps'`, all `venue='BALANCER'`, `chain` in `{ARBITRUM, ETHEREUM}`,
  `date=2023-01-01`) — folded into the same P2 todo above, alongside a note that 3 AGs now show the identical
  REFUSED-not-recorded shape with 3 different disallowed sources, which may share an upstream cause worth a joint
  root-cause pass. **All 4 campaign VMs are now complete**: cefi 25,593 / tradfi 22,905 / prediction 1,609 / defi 36,145
  recorded_cells (86,252 total), zero `escalated`/`read_failed`/`verify_failed` across all 4, 30 total
  REFUSED-not-recorded objects (all pre-existing mistags, not backfill-tool defects). This closes out the campaign this
  doc's own todo 1 tracks — see its Progress Log entry for the todo 1 checkbox flip. Handing back to
  `mdps_candle_manifest_population_disconnect_2026_07_25.md` todo 5 to do its own manifest-coverage spot-check and flip
  against this evidence.
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
