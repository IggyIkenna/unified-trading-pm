---
doc_type: issue
title: >-
  TradFi CME instrument_type=FUTURE manifest rows (non-chain-bundle) also show a blank-instrument_id population — 20,254
  rows, static since 2026-08-07, distinct root cause from the chain-bundle fix
summary: >-
  While executing `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` todo 1 (backfilling blank `instrument_id` on CME
  `futures_chain`/`options_chain` chain-bundle OHLCV manifest rows, `market-tick-data-service@63cff354`), a live
  manifest census surfaced an ADJACENT but DISTINCT blank-`instrument_id` population under `instrument_type=FUTURE` (the
  canonical uppercase single-instrument type, i.e. `is_derivative=False` shards — NOT a chain-bundle) — 20,254
  `venue=CME` rows with `capture_status=captured` + blank `instrument_id` + `instrument_count>0`, spanning `data_type`
  ohlcv_1s/ohlcv_24h/mbp_10/ohlcv_1m/ohlcv_15m/trades/tbbo, dominated by `underlying` MICRO-SP500 (8,023) / SP500
  (7,956) / ES (3,089). This is NOT the same defect the chain-bundle fix addresses (`_resolve_chain_bundle_manifest_id`
  only applies to `is_derivative=True` futures_chain/options_chain shards) and `_resolve_chain_bundle_manifest_id`
  cannot resolve these rows (confirmed: the resolver requires `itype` to be `futures_chain` or `options_chain`, not
  `FUTURE`). Population is STATIC (no rows written after 2026-08-07 as of this session, 2026-08-09) — a closed
  historical backlog, not an actively-growing live bug.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [tradfi, manifest, data-correctness, cme, instrument_id, blank-id]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/archive/issues/tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md,
  ]
created: "2026-08-09"
author: slot-15 worker
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
source:
  [
    "side-finding while executing tradfi_satellite_ao_dispatch_batch7_2026_08_06.md todo 1, slot-15 worker session
    2026-08-09, task tradfi_satellite_ao_dispatch_batch7-001",
  ]
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/venue_fetch.py,
    market-tick-data-service/market_tick_data_service/engine/orchestrator/_tradfi_manifest_shard.py,
  ]
---

# TradFi CME `instrument_type=FUTURE` blank-instrument_id population — distinct from the chain-bundle fix

## What I found

Executing `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` todo 1 required a live census of `venue=CME`
blank-`instrument_id` captured rows in `market-data-tick-tradfi-prd`'s `_index/availability_index.parquet`. The todo's
own scope is `instrument_type in {futures_chain, options_chain}` (chain-bundle shards only) — but a broader, unscoped
query (no `instrument_type` filter) surfaced TWO adjacent populations in the identical shape that the chain-bundle fix
does NOT cover:

1. **`instrument_type=combo`** (~301K rows) — investigated and confirmed **BY DESIGN, not a bug**:
   `_tradfi_manifest_shard.py`'s own comment states combo bundle-grain shards have "no per-row id [that] can be rebuilt"
   — a calendar spread / user-defined combo has no single resolvable per-bundle instrument_id the way a plain
   futures/options chain does. No further action needed; not tracked as a defect.
2. **`instrument_type=FUTURE`** (this issue) — the canonical UPPERCASE value for `is_derivative= False`
   (non-chain-bundle, single-instrument) TradFi shards. Unlike `combo`, there is no known by-design reason this should
   be blank — `venue_fetch.py::_record_venue_shard_counts`'s non-derivative branch calls
   `_resolve_tradfi_manifest_shard(...)` and, on success, sets a REAL built id (`tradfi_shard[1]`); a blank result here
   means either that call returned `None` (raw symbol didn't map, or `build_instrument_id` raised `ValueError`) and the
   CEFI-oriented fallback `_canonicalize_manifest_instrument_id(...)` ALSO failed to resolve a tradfi-shaped symbol —
   **not verified by reading the actual failing call in this session; this is a hypothesis, not a confirmed root
   cause.**

**Measured population** (live query, `read_availability_index_safe` filtered to `venue=CME`+`instrument_type=FUTURE`,
2026-08-09): 399,588 total `instrument_type=FUTURE` CME rows; of these, `capture_status` distribution is
`empty_confirmed`=378,200 / `captured`=21,367 / `attempted_failed`=21. Scoping to `capture_status=captured` + blank
`instrument_id` + `instrument_count>0`: **20,254 rows**. `data_type` breakdown: `ohlcv_1s`=134,689, `ohlcv_24h`=120,683,
`mbp_10`=120,681, `ohlcv_1m`=21,726, `ohlcv_15m`=696, `trades`=606, `tbbo`=507 (note: these totals are across the FULL
399,588-row `instrument_type=FUTURE` population, not just the 20,254 blank-id captured subset — a per-data_type
breakdown of just the blank subset was not run this session). `underlying` distribution among the 20,254 blank rows (top
values): MICRO-SP500=8,023, SP500=7,956, ES=3,089, then COPPER/GOLD/AUD/JPY/SILVER/TNOTE10Y/CORN/EUR/CHF/
SOYOIL/SOYBEAN/SOYMEAL each in the 40-60 range. Date range 2020-01-02 to 2026-08-06. **`written_at` shows NO rows after
2026-08-07** (most recent write days: 07-31=11,436, 08-02=3,274, 08-03=4,192, 08-04=692, 08-05=140, 08-06=347,
08-07=173) — this population is a **static, closed backlog**, not actively growing (confirmed as of this session,
2026-08-09 — re-verify freshness if picking this up much later).

## Why it matters

Same class of defect as the chain-bundle blank-`instrument_id` issue this session's primary todo fixed
(`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`) — any downstream consumer that scopes a manifest query by
`instrument_id` (e.g. a per-instrument coverage check, an `ES.FUT`-keyed query like the one that originally triggered
that whole investigation chain) will undercount real captured CME single-instrument data for these 20,254 shard-dates.
`SP500`/`MICRO-SP500`/`ES` dominating the underlying distribution here overlaps directly with the same headline MVP
instruments (`tradfi_consolidated_closeout_2026_07_18.md`'s "Certify tradfi Layer-1" gate) the original ES investigation
was chasing — a per-instrument-id coverage check for ES specifically could still undercount even after the chain-bundle
fix, via this SEPARATE population.

Not urgent (static, not actively growing) but real and unaddressed.

## Recommended next steps (not executed here — root-cause diagnosis, not a mechanical fix)

1. Read `venue_fetch.py::_record_venue_shard_counts`'s non-derivative branch (`_resolve_tradfi_manifest_shard` →
   `_canonicalize_manifest_instrument_id` fallback) against a representative sample of the 20,254 rows' actual
   `date`/`underlying` values to confirm which of the two calls is actually failing and why (raw symbol shape mismatch?
   an unmapped `itype`? a `build_instrument_id` `ValueError` on a specific symbol pattern?).
2. Once root-caused, decide fix shape: a writer-side fix (prevents new occurrences, mirrors `@65beaeaf`'s chain-bundle
   fix) plus, if warranted, a dedicated backfill script for the existing 20,254 rows (mirrors
   `scripts/restamp_tradfi_cme_chain_bundle_blank_instrument_id_2026_08_09.py`'s pattern — though note THIS population's
   fix will likely need the RAW per-contract symbol, not just `underlying`, since `instrument_type=FUTURE` rows are
   single dated contracts, not bundles; `_resolve_chain_bundle_manifest_id` does not apply here at all).
3. Since the population is static (not growing), there is no urgency to re-launch anything — this can be scheduled as
   ordinary backlog work.

## Todos

- [ ] [DATA] P2. Root-cause why `venue_fetch.py`'s non-derivative (`is_derivative=False`) manifest-write branch left
      `instrument_id` blank for the 20,254 `venue=CME`, `instrument_type=FUTURE`, `capture_status=captured` rows found
      2026-08-09 (dominated by underlying MICRO-SP500/SP500/ES) — read `_resolve_tradfi_manifest_shard` and the
      `_canonicalize_manifest_instrument_id` fallback against a representative sample, determine whether this is a
      raw-symbol-shape mismatch, an unmapped `itype`, or a `build_instrument_id` failure, and record the finding here
      before scoping a fix. Repo: market-tick-data-service. **Done when**: a dated finding is recorded in this doc's
      Progress Log identifying the actual failing call + why, with enough detail that a follow-up writer-fix +
      backfill-script todo (if warranted) can be scoped without re-investigating from scratch.

## Progress Log

- **slot-15 worker 2026-08-09** (side-finding during `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` todo 1): filed
  this issue from a live manifest census; population confirmed static (no writes after 2026-08-07) — re-verify freshness
  before treating this as urgent if picked up much later than this filing date.
