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
status: resolved
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
resolved_by: slot-12-data_engineering-2026-07-26
drift_direction: advance-code
depends_on: []
---

> **🟢 RESOLVED 2026-07-26** — live end-to-end trace confirmed MDPS's candle-manifest emission logic is correct today
> (both `batch_hyperliquid` and `batch_tardis` paths); the original "0 rows, ever" verdict was a
> verification-methodology mistake, not a code defect (see "Root cause" below). The one genuine, still-open follow-up
> (reconciling candle files orphaned by past OOM crashes before the fix landed) was extracted to its own tracked doc at
> archival time so it doesn't get buried in a resolved issue:
> `/plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`.

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

## Root cause (found 2026-07-26, slot-12 `data_engineering`)

**MDPS's candle-manifest emission logic is NOT broken.** Live-traced end-to-end and confirmed correct for BOTH the
non-tardis path (HYPERLIQUID, `pipeline_mode=batch_hyperliquid`) and the tardis path (BITGET-FUTURES,
`pipeline_mode=batch_tardis`) — see evidence below. This doc's original "0 rows, ever — FAIL" verdict was produced by
TWO independent verification-methodology mistakes, not a code defect:

1. **Wrong `data_type` vocabulary queried (the primary mistake).** MDPS candle-manifest rows are stamped with
   `data_type=<SOURCE data_type>` (e.g. `"trades"`, `"book_snapshot_5"`) — NOT the aggregated `ohlcv_1m`/`book5_ohlcv_*`
   family this doc's manifest query filtered on. This is a DELIBERATE, operator-ruled design
   (`canonical_writer.py::write_candle_parquet`, comment:
   `"Manifest data_type AXIS = SOURCE data_type (operator ruling 2026-07-21): path==manifest on data_type"`) — and it
   matches the actual GCS object path, which also carries `data_type=trades` (confirmed via `gcloud storage ls` on real
   candle parquets, e.g.
   `processed_candles/.../timeframe=1m/data_type=trades/.../HYPERLIQUID:PERPETUAL:BTC-USD@LIN.parquet`). A query for
   `data_type IN {ohlcv_1m, ...}` will ALWAYS return 0 MDPS rows by design, regardless of whether emission is working.
   Candle rows are disambiguated from MTDS/IS's raw tick-capture rows (same `data_type=trades`) by `timeframe`: raw
   capture rows carry `timeframe=""`, MDPS candle rows carry a real cadence (`15s`/`1m`/`5m`/`15m`/`1h`/`4h`/`1d`) —
   confirmed via a live manifest query: `service_name=market-data-processing-service AND data_type=trades` returns ONLY
   rows with real timeframe values (zero `timeframe=""` rows), while `market-tick-data-service`'s 114,096 HYPERLIQUID
   `trades` rows are ALL `timeframe=""`. This ALSO explains why the doc's earlier "MTDS 2,953 ohlcv rows vs MDPS 0"
   comparison isn't a defect: MTDS's REST-poll adapters fetch pre-aggregated candles directly (their manifest
   `data_type` naturally IS the fetched cadence, e.g. `ohlcv_1m`), a structurally different acquisition pattern from
   MDPS's tick→candle derivation — not two implementations of the same thing where one is broken.
2. **A genuine but PAST (already-fixed) gap for `pipeline_mode=batch_tardis` shards, not a live one.** The
   BITGET-FUTURES/BITFINEX-FUTURES/KRAKEN-FUTURES `day=2026-05-03` candle files this doc's file-side evidence cites
   really did have zero manifest rows — confirmed: their GCS object `creation_time` is `2026-07-22T21:23:40Z` (well
   post-Phase-1.2A manifest-verb migration), yet zero manifest rows existed for them as of this session. Root cause: the
   SAME per-date memory-scaling OOM bug fixed today in the sibling issue
   (`mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md` bug 1,
   `market-data-processing-service@86a16239c3`+`@335e9cc`) killed backfill VMs mid-run, losing whichever shard's
   manifest write/flush was in flight when the kernel OOM-killer struck (bytes already uploaded to GCS; the
   `ManifestWriter.record_captured` + `_flush_manifest_with_backoff` call for that shard never completed or never got
   consolidated) — the SAME failure class the `_flush_manifest_with_backoff` per-shard-flush code comment explicitly
   documents ("2026-04-29 cefi-fwd OOM lost 134 shards of manifest because the Python interpreter was killed before
   atexit could fire"). This is a data-completeness gap in the EXISTING corpus, not a live/ongoing code defect.

**Live proof the emission path works correctly today** (evidence, not inference — per this doc's own instruction to do a
real trace, not further manifest-query guessing):

- HYPERLIQUID BTC/ETH `trades`→candle backfill for `day=2026-07-19` (run as part of the sibling issue's verification,
  `mdps-backfill-cefi-20260726-225028`): produced 14 real `captured` manifest rows (`data_type=trades`, 7 timeframes × 2
  instruments), `row_count` exactly matching the real candle counts (1440 for `1m`, 288 for `5m`, etc.).
- **BITGET-FUTURES `day=2026-05-03` (the exact previously-zero-manifest shard from this doc's own evidence),
  `--force`-reprocessed live this session** (`mdps-backfill-cefi-20260726-230715`, `pipeline_mode=batch_tardis`):
  run.log shows `ManifestWriter: per-VM shard updated (... 1 new ...)` — confirmed by directly reading the per-VM shard
  `_index/per_vm/mdps-backfill-cefi-20260726-230715.parquet`: 2 real `captured` rows,
  `service_name=market-data-processing-service`, `venue=BITGET-FUTURES`, `date=2026-05-03`, `data_type=trades`,
  `row_count=5760` (matching the `15s` candle count) — a previously-invisible venue/date now has a fresh, real manifest
  row, produced by TODAY's code with no manifest-path code change needed.

## Recommended fix path

- [x] [DATA] P1. **Root-cause and fix MDPS's cefi candle-manifest emission gap.** — **RESOLVED 2026-07-26, NO CODE FIX
      REQUIRED.** See "Root cause (found 2026-07-26)" above: live end-to-end trace + a real re-run of the exact
      previously-zero-manifest BITGET-FUTURES `day=2026-05-03` shard confirms the CURRENT emission logic is correct.
      This doc's own FAIL verdict flips to PASS: `data_completion_cefi_2026_07_15.md`'s CF-11 3rd sub-item can close —
      MDPS DOES faithfully register manifest rows for the candle files it writes (under the `data_type=<SOURCE type>`
      axis, by design). Repos touched: none (verification-only; the sibling OOM fix that incidentally resolved the PAST
      batch_tardis gap already shipped as `market-data-processing-service@335e9cc` under a separate issue).
- [x] ✅ [DATA] P2. Reconcile the manifest for candle files orphaned by PAST OOM crashes (before the
      `market-data-processing-service@335e9cc` OOM fix landed). — EXTRACTED 2026-07-26 (cicd plan_health wall-clear) to
      its own tracked doc rather than left open inside this now-resolved doc:
      `/plans/active/issues/mdps_cefi_candle_manifest_orphan_reconciliation_2026_07_26.md`.

## Progress Log

- 2026-07-26 (slot-12, `data_engineering`): Root-caused via live end-to-end trace (not further manifest-query inference,
  per this doc's own instruction) — see "Root cause (found 2026-07-26)" above. No code fix shipped (none needed):
  confirmed the emission path is correct today for both `pipeline_mode=batch_hyperliquid` and
  `pipeline_mode=batch_tardis` via two live VM runs (`mdps-backfill-cefi-20260726-225028`,
  `mdps-backfill-cefi-20260726-230715`), the second of which `--force`-reprocessed the EXACT previously-zero-manifest
  BITGET-FUTURES `day=2026-05-03` shard this doc's own file-side evidence cited, and confirmed a fresh manifest row.
  Todo 1 flipped `[x]`. Filed todo 2 (P2, reconciliation backfill for pre-fix-era orphaned candle files) as a properly
  scoped follow-up rather than absorbing it into this session — full-corpus reconciliation needs its own Tier-2 SPOT VM
  run, not an in-session action.
