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
context_scope:
  [
    /plans/active/issues/mdps_features_ml_strategy_orphan_sweep_tooling_gap_2026_07_27.md,
    /plans/archive/issues/mdps_candle_orphan_sweep_design_brief_2026_07_27.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /codex/02-data/orphan-object-detection.md,
    /plans/archive/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md,
  ]
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
- [ ] [DATA] P2. **Complete the sports full-corpus sweep** (only a bounded 200-object sample has been run) to confirm
      the ~100% coverage pattern holds across sports's entire historical corpus, not just a recent-day sample.
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
- [ ] [DATA] P2. **Remediate cefi + prediction `processed_candles/` objects mis-tagged with an unregistered
      `source=databento`** — two independent AGs hit the identical mistag SHAPE (a manifest write attempted with
      `source='databento'`, which isn't in that AG's `SOURCE_PRIORITY`-registered source list), confirmed via
      `RECORD-ERROR` warnings in the backfill VMs' `run.log`; `backfill_candle_manifest.py` correctly REFUSED to write a
      manifest row in every case (never silently mis-records) — these objects remain unmanifested after todo 1's
      backfill. - **cefi** (10 `RECORD-ERROR`s, `backfill-candle-manifest-cefi-20260727-151741`): root-caused via direct
      GCS listing — for the SAME shard key
      (`day=2019-04-01/timeframe=1d/data_type=derivative_ticker/instrument_type=PERPETUAL/venue=DERIBIT/*-PERPETUAL`),
      TWO objects exist — one correctly at `pipeline_mode=batch_tardis/`, one incorrectly at
      `pipeline_mode=batch_databento/` (databento is not in cefi's registered source list: aster, binance, bybit,
      deribit, extended, hyperliquid, kalshi_perp, kraken, okx, polymarket_perp, tardis). Confirmed scope via
      `gcloud storage ls -r gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/**/pipeline_mode=batch_databento/**`
      → 1,639 objects across ~1,638 distinct day/instrument combos, DERIBIT PERPETUAL derivative_ticker/1d only (not
      re-checked for other data_types/timeframes/venues — scope this todo's own read before remediating). -
      **prediction** (10 `RECORD-ERROR`s, confirmed 2026-07-27 slot-6,
      `backfill-candle-manifest-prediction-20260727-152012`): same shape, different AG — all 10 are
      `MissingSourceError: source='databento' ... not a registered source for       asset_group='prediction' data_type='trades'`
      (allowed sources: `kalshi`, `polymarket_clob`), all `venue='POLYMARKET'`, dates `2025-03-14`..`2025-03-24`
      (contiguous run, one `date` per RECORD-ERROR — not yet checked whether this is the full extent or just what this
      backfill pass's report happened to cover; scope a fresh GCS listing before remediating, same as cefi's open scope
      gap). Not yet root-caused whether this is the same underlying mistag mechanism as cefi's (a stray
      databento-sourced write landing on a non-databento AG's canonical path) or a distinct cause — worth checking
      together given the identical error shape landed on two unrelated AGs. - **tradfi** (0 `RECORD-ERROR`s, confirmed
      2026-07-27 slot-6, `backfill-candle-manifest-tradfi-20260727-151950`, clean
      `escalated=0 read_failed=0 verify_failed=0`) — does NOT show this pattern, so it's not universal across AGs;
      consistent with tradfi being a legitimate Databento-sourced AG (`SOURCE_PRIORITY` databento-first there), so a
      `source=databento` write there is expected to be valid, not mistagged. - **defi** (10 `RECORD-ERROR`s, confirmed
      2026-07-27 slot-6, `backfill-candle-manifest-defi-20260727-151932`, otherwise clean VERDICT
      `already_covered=0 ok=1131367 recorded_cells=36145 junk=0 escalated=0 read_failed=0 verify_failed=0`): same mistag
      SHAPE, a THIRD distinct source pairing —
      `MissingSourceError: source='onchain_rpc' ... not a registered source for asset_group='defi' data_type='dex_pool_swaps'`
      (allowed: `onchain_subgraph`), all `venue='BALANCER'`, `chain` in `{ARBITRUM, ETHEREUM}`, `date=2023-01-01` only
      (one date, all 7 candle timeframes for each of the 2 chains — 10 total). Same open question as prediction's: not
      yet confirmed whether this is the full extent (scope a fresh GCS listing before remediating) or root-caused
      against cefi/prediction's mechanism — three AGs now show the identical REFUSED-not-recorded shape with three
      different disallowed sources (`databento`→cefi, `databento`→prediction, `onchain_rpc`→defi), which may point to a
      shared upstream cause (e.g. a migration/backfill step that stamped the wrong `source=` on a small slice of objects
      across AGs) rather than three independent one-offs — worth a joint root-cause pass before remediating any of the
      three individually. Options for all three AGs: (a) relabel the mistagged objects' `pipeline_mode=`/source path
      segment to the correct source (copy-not-move + verify twin content matches, then this todo's own `record_captured`
      pass), or (b) if the mistagged object is actually STALE/superseded by a correctly-tagged twin, treat as a
      legacy-duplicate cleanup candidate instead (needs a content diff first — do NOT assume). Small, bounded, does not
      block todo 1's completion (25,593 cefi + 1,609 prediction + 36,145 defi cells recorded successfully despite these
      — 30 total mistagged/refused objects across all 4 AGs, out of ~2.6M actionable rows processed).

## Progress Log

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
