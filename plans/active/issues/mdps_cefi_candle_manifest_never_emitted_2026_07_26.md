---
doc_type: issue
title:
  "MDPS cefi candle-generation pipeline writes real processed_candles/ parquet files but has NEVER emitted a manifest
  row for any of them — 0 rows across the entire live corpus"
summary: >-
  Verified live (cefi_satellite_ao_dispatch_batch1-003, 2026-07-26): the cefi availability manifest
  (`market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet`) contains ZERO rows with
  `service_name=market-data-processing-service` under ANY candle data_type prefix
  (`ohlcv_*`/`book5_ohlcv_*`/`deriv_ohlcv_*`/`liq_agg_*`/`swaps_ohlcv_*`/`state_ohlcv_*`) — all 2,953 candle-manifest
  rows in the whole corpus belong to `market-tick-data-service`'s 3 REST-poll venues (COINBASE-FUTURES 1700,
  EXTENDED-STARKNET 778, LIGHTER-ZKSYNC 475). Meanwhile `processed_candles/by_date/day=2026-05-03/` alone contains 1,236
  real parquet files across BITGET-FUTURES (662), BITGET-SPOT (340), BITFINEX-FUTURES (199), KRAKEN-FUTURES (35),
  spanning 7 timeframes. This is NOT the previously-diagnosed "phantom captured" issue (that hypothesis was disproven
  2026-06-03, see the absorbed doc) — this is the OPPOSITE failure mode: MDPS is under-emitting, silently producing real
  files with zero manifest registration, despite `_upload_candles_to_gcs` → `write_candle_parquet` delegating to
  `ManifestWriter.record_captured` on every write per its own docstring.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, cefi, manifest, candle, ohlcv, mdps, operator-notify]
related: [/plans/archive/issues/cefi_processed_candles_manifest_file_disconnect_2026_05_25.md]
created: 2026-07-26
priority: P1
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
source: >-
  cefi_satellite_ao_dispatch_batch1-003 (`plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md`), which asked to
  "verify MDPS candle-manifest faithfulness" on a sample day per `data_completion_cefi_2026_07_15.md`'s open sub-item.
  FAIL verdict — filed here per the findings-closure hard rule.
execution_scope_note: read-only verification this session; the fix is the follow-up todo below.
locked_by:
locked_since:
resolved_by:
drift_direction: advance-code
depends_on: []
---

# MDPS cefi candle-manifest emission: 0 rows, ever

> **🟥 OPERATOR-NOTIFY (data-correctness, cross-repo).** This is a genuine, systemic gap distinct from the earlier
> "phantom captured" false alarm: MDPS's cefi candle pipeline writes real files but has NEVER registered a single one in
> the manifest. Every downstream consumer that trusts `capture_status` for cefi `ohlcv`-family data types (data-status
> UI, honest-coverage denominators, any manifest-driven reader) sees the ENTIRE MDPS-derived candle corpus as absent —
> not stale, not partial, **zero ever**. Per the `Data pipeline correctness is the heartbeat` HARD RULE this is exactly
> the class of divergence layer-N+1 work should not build on top of until fixed.

## What was measured (2026-07-26, slot-5/review)

**Manifest side** (`read_availability_index(get_bucket_name("market_data", "CEFI"))` —
`market-data-tick-cefi-prd-central-element-323112`, same bucket as the GCS check below):

```
candle-manifest rows (ohlcv_*, book5_ohlcv_*, deriv_ohlcv_*, liq_agg_*, swaps_ohlcv_*, state_ohlcv_* — the FULL set
per canonical_writer_shaping.py::mdps_data_type_key, not just a naive "ohlcv_" prefix grep):
  total: 2,953
  service_name=market-tick-data-service: 2,953   (100%)
  service_name=market-data-processing-service: 0  (0%)

ohlcv_1m by venue (all market-tick-data-service): COINBASE-FUTURES 1700, EXTENDED-STARKNET 778, LIGHTER-ZKSYNC 475
```

**File side**
(`gcloud storage ls -r gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/day=2026-05-03/**`):

```
1,236 real .parquet files on 2026-05-03 alone:
  BITGET-FUTURES 662, BITGET-SPOT 340, BITFINEX-FUTURES 199, KRAKEN-FUTURES 35
  across 7 timeframes (15s/1m/5m/15m/1h/4h/1d), pipeline_mode=batch_tardis (1225) + batch_databento (11)
```

**Verdict: FAIL.** MDPS's real candle output for BITGET/BITFINEX/KRAKEN on 2026-05-03 (and, per the zero-total above,
every date MDPS has ever processed) has NO corresponding manifest row under any candle data_type key.

## Why the earlier "phantom captured" diagnosis doesn't apply here

The absorbed doc (`cefi_processed_candles_manifest_file_disconnect_2026_05_25.md`) diagnosed the OPPOSITE direction —
MTDS `trades`-captured rows being miscompared against candle files — and correctly disproved a "phantom manifest row"
theory. This finding is a fresh, independent measurement of the actual `ohlcv`-family manifest coverage vs the actual
file corpus, and finds the reverse defect: real files, no manifest row, ever. The absorbed doc's own §CF-11 3rd sub-item
("VERIFY MDPS candle-manifest faithfulness... do the ohlcv_* rows faithfully reflect the candle files that DO exist") is
exactly this check — and it comes back FAIL, not the assumed PASS its own text seemed to anticipate ("On all three
GREEN, archive the absorbed issue doc").

**Note on doc state**: the absorbed doc is ALREADY in `plans/archive/issues/` (moved by a separate hygiene pass before
this FAIL verdict existed) — this issue doc does not attempt to move it back; the archived doc's own banner already
explains it will need reconciling once all 3 sub-items are actually green, which they are not.

## Cross-write reconciliation (the todo's other half — RESOLVED, non-concerning)

The source doc's cited "782 MTDS-written ohlcv rows; 616 MDPS-written trades rows" cross-write framing has moved on
naturally since 2026-06-03 and is NOT a defect:

- MTDS's ohlcv row count grew to 2,953 as its REST-poll venue set expanded (COINBASE-FUTURES + EXTENDED-STARKNET added
  since). This is legitimate — MTDS DOES legitimately own `ohlcv` for venues whose adapter fetches pre-aggregated
  candles directly (REST-poll), never routing through MDPS's tick→candle derivation.
- MDPS's cross-write into `trades` is now 70 rows, ALL `venue=HYPERLIQUID` — a narrow, single-venue routing detail
  (HYPERLIQUID raw-trade capture apparently runs through MDPS for this one venue), unrelated to the candle-manifest gap
  above and not itself a data-correctness concern.

## Root-cause hypothesis (NOT investigated further this session — scope was verify, not fix)

`_upload_candles_to_gcs` (`market_data_processing_service/app/core/candle_write_mixin.py:656`) delegates to
`write_candle_parquet` (`canonical_writer.py:164`), whose own docstring says it "emits one `ManifestWriter` row with the
full v4 shard tuple" on every write. Candidate explanations for the total silent gap (needs real investigation, not
guessed here): (a) the manifest-write call is unreachable/short-circuited somewhere in the actual cefi-candle
orchestration path that never reaches `_upload_candles_to_gcs` proper (e.g. a different write path used for
`batch_tardis`-sourced cefi candles specifically — 1,225 of the 1,236 sample-day files are
`pipeline_mode=batch_tardis`); (b) `record_captured` raises and is swallowed by a broad exception handler upstream; (c)
the manifest write targets a DIFFERENT bucket/shard location than `read_availability_index` reads (e.g. an
un-consolidated `_index/per_vm/` shard that never gets merged for this specific write path). Per the workspace's
single-walk + honest-absence discipline, this needs a real code trace (add a breakpoint/log probe on one live cefi
candle write, or read the actual `batch_tardis` cefi orchestration entry point end-to-end), not further inference from
manifest queries.

## Recommended fix path

- [ ] [DATA] P1. **Root-cause and fix MDPS's cefi candle-manifest emission gap.** Trace ONE live cefi candle write
      (BITGET-FUTURES or BITFINEX-FUTURES, `pipeline_mode=batch_tardis`, any recent date) end-to-end from the
      orchestration entry point through `_upload_candles_to_gcs` → `write_candle_parquet` →
      `ManifestWriter.record_captured` to find where the manifest emission is actually lost (never called /
      raises-and-swallowed / wrong bucket-shard). Fix the root cause, then verify: re-run a small real cefi candle
      backfill for one venue/date and confirm a NEW manifest row lands in `availability_index.parquet` (or its `per_vm/`
      shard, pending consolidation) with `service_name=market-data-processing-service`. Once fixed, this doc's own FAIL
      verdict flips to PASS and `data_completion_cefi_2026_07_15.md`'s CF-11 3rd sub-item can close for real. Repo:
      market-data-processing-service (+ unified-trading-library if the shared `ManifestWriter`/`write_candle_parquet`
      boundary itself is implicated). **Done when**: root cause identified + fixed + a fresh manifest row is confirmed
      live for at least one previously-invisible venue/date, `quality-gates.sh` green.
