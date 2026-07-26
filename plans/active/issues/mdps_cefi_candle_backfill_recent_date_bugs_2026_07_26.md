---
doc_type: issue
title:
  Three MDPS cefi candle-building bugs found while backfilling on-chain-perp venues (memory-scaling OOM,
  derivative_ticker schema gap, book_snapshot_5 column mismatch)
summary: >-
  Discovered while executing cefi_satellite_ao_dispatch_batch1-001 (extend MDPS candle-building to
  ASTER/HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET + backfill). Three independent, code-level bugs surfaced in
  market-data-processing-service's candle-building path, all reproducible against real prod data, none specific to the 4
  target venues (they'd affect any high-volume/high-instrument-count CeFi venue's candle backfill). Filed here per the
  findings-closure hard rule rather than left as prose in the source plan's Progress Log.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, unified-api-contracts]
scope: [engineer]
tags: [mdps, candle, ohlcv, memory, oom, schema-contract, book-snapshot, backfill]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/issues/mdps_cefi_candle_manifest_never_emitted_2026_07_26.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.5
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Discovered 2026-07-26 while executing cefi_satellite_ao_dispatch_batch1-001 (slot 6). All three measured against real
  prod data on live SPOT VMs (mdps-backfill-cefi-20260726-*), not inferred.
locked_by:
locked_since:
resolved_by:
depends_on: []
---

# MDPS cefi candle-building: three backfill-blocking bugs

## What I found

### Bug 1 — per-day memory scaling: a SINGLE real day for ONE venue can exceed 32GB RAM (most severe, P1)

Backfilling HYPERLIQUID `trades` candles for `day=2026-07-19` alone (177 tradable instruments, all 7 timeframes
`15s..24h`) on a `e2-standard-8` (32GB RAM) VM was killed by the kernel OOM-killer at `rc=137` after RSS climbed
monotonically through the aggregation cascade: 17.1 → 20.1 → 24.8 → 26.2 → 27.1 GiB (58.5% → 88.6% mem) before being
killed. This reproduced identically on THREE separate VM launches for the same date/venue (once as part of a 7-day
window, once in single-day isolation, once with an `--instrument-ids` filter narrowed to BTC/ETH only) — not a fluke,
and **not bounded by the instrument-id filter**. **Correction to an earlier reading of this same session**: a
2-instrument-scoped run initially LOOKED like it fit comfortably (~1.5-2.4GB RSS at the ~1-minute mark), but continued
monitoring past that point showed RSS climbing on the SAME trajectory as the full 177-instrument run — 17.1 → 21.7 →
23.5 → 25.7 GiB (60.6% → 85.1% mem) — before the VM went silent (no new log/heartbeat activity for 6+ minutes, no clean
kernel OOM message this time, effectively hung/dead) despite processing only 2 of 177 instruments' raw files. **This
means the memory driver is NOT the number of instruments actually being aggregated** — something in the per-date
invocation (loading "13601 cefi instruments from GCS" / "177 instruments tradable" / the `cefi_wire_bridge` catalogue,
all logged identically regardless of the `--instrument-ids` filter) holds a large in-memory structure sized to the FULL
venue universe, not the requested subset. A `MACHINE_TYPE=e2-highmem-8` (64GB RAM, vs the launcher's default
`e2-standard-8` 32GB) relaunch of the same narrow 2-instrument request is in flight to confirm whether doubling RAM is a
viable stopgap or whether the growth is effectively unbounded. Separately, a MULTI-day run (30-day + 7-day windows) also
OOM'd, but only reached ~2-4 days in before crashing — consistent with per-date memory not being released between dates
(each date's fixed catalogue-load footprint compounds with whatever the process already retained). Suspected root cause:
the candle aggregator (or its dependency/schema/catalogue loading step) likely loads a fixed, large, venue-wide
structure per date invocation regardless of the actual instrument scope requested — not scoped streaming/chunking;
`cefi_wire_bridge: loaded 429129 catalogue rows` is reloaded once per date-invocation, which may also not be released.

### Bug 2 — `derivative_ticker` candle building fails for ALL HYPERLIQUID instruments sampled (P2)

Every sampled HYPERLIQUID instrument (8/8: ADA/AVAX/BNB/DOGE/FIL/LTC/MATIC/SOL-PERP) failed
`derivative_ticker`→`deriv_ohlcv_1m` candle building with
`[CRITICAL] No SchemaContract registered for asset_group='cefi' instrument_type='UNKNOWN' data_type='deriv_ohlcv_1m' venue='HYPERLIQUID'`
plus a companion `SCHEMA_VALIDATION_FAILED` (NOT-NULLABLE OHLC columns getting 4320 NaN/null values) at the `15s` tier.
The `instrument_type='UNKNOWN'` in the error (vs the expected `perpetual`) suggests a resolution bug, not necessarily a
genuinely-missing contract. Does NOT affect the `trades`→`quote_volume` path (the ADV-reader-relevant data_type).

### Bug 3 — `book_snapshot_5` column-name mismatch for HYPERLIQUID (P2)

HYPERLIQUID's raw `book_snapshot_5` columns are named `bid_px_00`/`ask_px_00` (etc., 5 levels), not the
`bid_price_0`/`ask_price_0` the book-candle aggregator expects (`WARNING Missing bid_price_0 or ask_price_0 columns`).
This makes the aggregator treat the shard as "no valid rows" and attempt `record_empty(reason=SOURCE_RETURNED_ZERO)`
without `FetchEvidence` — correctly REFUSED by the UTL Phase-1 KEYSTONE honest-absence gate
(`UnprovenHonestAbsenceError`), so no bad data lands, but the shard is never candle-built either. Worth checking
LIGHTER-ZKSYNC/EXTENDED-STARKNET for the same `bid_px_NN`/`ask_px_NN` naming convention since they may share the same
on-chain-CLOB wire format.

## Why it matters

- Bug 1 makes ANY recent-date CeFi candle backfill on the default `e2-standard-8` launcher unreliable for a
  large-universe venue — not just for these 4 venues, and (per the corrected finding above) NOT avoidable by narrowing
  `--instrument-ids`/`--venues` scope, since the memory driver appears tied to the per-date invocation's full-universe
  catalogue load rather than the actual instruments processed. It will recur for BITGET/BINANCE/etc. tardis-sourced
  venues too if their CURRENT (2026) instrument counts are similarly large; the full-range 2024-dated backfill (smaller
  historical universe at that point in time) has run 80+ days cleanly so far, suggesting the ceiling tracks the VENUE'S
  CURRENT universe size at invocation time, not the requested date/ instrument scope.
- Bugs 2/3 are narrower (specific data_types) but silently drop real candle coverage for those data_types/venues without
  a loud, actionable alert beyond a WARNING/CRITICAL log line — worth a proper fix so `derivative_ticker` and
  `book_snapshot_5` candle coverage isn't permanently zero for HYPERLIQUID.

## Recommended decision

- [ ] [DATA] P1. **Fix MDPS's per-date candle-aggregation memory scaling.** Root-cause why a single CeFi venue/date
      invocation exceeds 32GB RAM even when `--instrument-ids` narrows the actual work to 2 instruments — the memory
      growth appears tied to a fixed per-date catalogue/universe load (13,601 instruments loaded, 177 tradable), NOT the
      instrument scope requested, so narrowing scope is not a viable workaround on its own. Find and fix whatever
      loads/retains the full-universe structure regardless of the instrument filter (the instruments catalogue,
      `cefi_wire_bridge` wire map, or a validation/schema step that iterates the full tradable set even when only a
      subset was requested). Repo: market-data-processing-service. **Done when**: a `--instrument-ids`-narrowed (e.g.
      2-instrument) HYPERLIQUID `trades` candle backfill for one high-volume recent day completes on the STANDARD
      `e2-standard-8` launcher without OOM (confirming the fix actually scopes memory to the requested work), with a
      regression test/benchmark recorded. A full (all-177-instrument) run completing is a stretch goal, not required for
      this item's own done-when. — **CODE FIX SHIPPED 2026-07-26, live-VM done-when proof still OUTSTANDING** (see
      Progress Log — NOT flipped `[x]` since the actual gate, a real backfill completing without OOM, hasn't been run).
- [ ] [DATA] P2. **Fix HYPERLIQUID `derivative_ticker`→`deriv_ohlcv_1m` candle building.** Root-cause the
      `instrument_type='UNKNOWN'` resolution (should resolve `perpetual`) for HYPERLIQUID `derivative_ticker` rows, then
      either fix the resolution or register the missing
      `unified_api_contracts.internal.schemas.contracts.     CONTRACT_REGISTRY` entry for `deriv_ohlcv_1m`. Repos:
      market-data-processing-service (+ unified-api-contracts if a new contract is needed). **Done when**: a real
      `derivative_ticker` backfill for at least one HYPERLIQUID instrument produces a valid `deriv_ohlcv_1m` candle with
      no SchemaContract/validation error.
- [ ] [DATA] P2. **Fix the `book_snapshot_5` column-name mapping for on-chain-perp venues.** Map HYPERLIQUID's (and
      check LIGHTER-ZKSYNC/EXTENDED-STARKNET's) `bid_px_NN`/`ask_px_NN` raw columns to the `bid_price_0`/`ask_price_0`
      the book-candle aggregator expects. Repo: market-data-processing-service. **Done when**: a real `book_snapshot_5`
      backfill for at least one HYPERLIQUID instrument produces a valid candle instead of the "Missing bid_price_0"
      warning + refused honest-absence write.

## Progress Log

- 2026-07-26 (slot-12, `data_engineering`): **Root-caused + fixed bug 1's code path; live-VM done-when proof NOT yet
  run.** Root cause: `market_data_processing_service/app/core/orchestration_scanner.py::_list_instrument_files` listed
  the ENTIRE day's `raw_tick_data/by_date/day={date}/` prefix (every venue/instrument_type/data_type in the category)
  and materialized every `BlobMetadata` into a Python list BEFORE applying the `--venues`/`--instrument-ids` filter —
  this is what actually drove the multi-GB RSS growth, not the 13,601-instrument catalogue load (that load's own result,
  `tradable_keys`, is even unused/discarded downstream — wasteful but not GB-scale). Fix: for CEFI, derive a venue set
  (explicit `--venues`, or parsed from canonical `VENUE:TYPE:SYMBOL` `--instrument-ids` via the existing
  `parse_canonical_instrument_id`) and scope the GCS listing to
  `raw_tick_data/by_date/day={date}/{asset_group|category}= cefi/venue={V}/` per venue instead of the whole-day scan —
  falls back to the pre-existing whole-day scan when no venue is resolvable (bare-symbol instrument_ids, or neither
  filter given), and other categories (DeFi's DEX venues nest under `pipeline_mode=` instead, unconfirmed to match this
  hive layout) are left on the unchanged whole-day path. Threaded `category:` through `_list_instrument_files` → the
  public `list_instrument_files` wrapper → `_resolve_files_to_process` → the CLI pre-count loop in
  `cli/handlers/process_handler.py`. Added 6 regression tests
  (`tests/unit/test_orchestration_scanner_venue_scoped_listing.py`) pinning: instrument-id-derived venue scoping +
  exclusion of other venues' blobs, explicit-`--venues` scoping, both `asset_group=`/`category=` hive-key spellings
  tried per venue, bare-symbol fallback to whole-day scan, `category=None` full backward-compatibility, and non-CEFI
  categories keeping the whole-day scan. `quality-gates.sh` green (61s, fresh run post-fix — caught + fixed a
  `reportPossiblyUnboundVariable` on `prefix` I introduced in the first pass, confirmed via direct `basedpyright`
  before/after: 8→7 errors, the remaining 7 all pre-existing/unrelated). Shipped:
  `market-data-processing-service@86a16239c35ae3aea6e1439c3599c7a428f93f0c`. **NOT done**: the todo's own done-when is a
  LIVE backfill (`--instrument-ids`-narrowed HYPERLIQUID `trades`, one recent day, on the standard `e2-standard-8`
  launcher, completing without OOM) — this requires launching a VM, which wasn't attempted this session (ran into a
  severe, unrelated `/home` disk-space crisis workspace-wide, see `codex`/operator channel; also this is real infra
  verification that deserves its own dedicated attention, not a rushed check under context pressure). **Next step**:
  launch the standard backfill launcher against HYPERLIQUID `trades`, `--instrument-ids` narrowed to 2, for one
  high-volume recent day (e.g. `2026-07-19`, the day originally OOM'd), confirm it completes without OOM, then flip this
  todo `[x]` with the run's evidence (VM name + log tail showing completion). Todos 2/3 (bugs 2/3,
  `derivative_ticker`/`book_snapshot_5`) are untouched — separate, smaller fixes, not started.
