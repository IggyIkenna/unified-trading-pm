---
doc_type: issue
title: >-
  BALANCER dex_pool_state writer emits legacy `swap_volume`/`swap_fees`/`total_shares` column names (CUMULATIVE, not
  daily) — `CanonicalDexPoolProvider` reads `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps`, so Balancer pools always
  read 0 fee accrual
summary: >-
  Found while verifying (2026-08-04) whether `dex_pool_state` already carries the subgraph fee/volume columns that
  `materialize_dex_pool_fees.py` used to separately materialize (see
  `/plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md`, now executed — that script is
  retired). CURVE-ETHEREUM's `dex_pool_state` rows carry real, populated `fees_usd`/`volume_usd`/`fee_rate_bps` (the
  DIAG condition was MET for Curve). BALANCER-ETHEREUM's `dex_pool_state` rows — sampled live from the exact
  `0x06df3b2bbb68adc8b0e302443692037ed9f91b42...` USDC/DAI/USDT pool `materialize_dex_pool_fees.py` targeted, day
  2026-06-20 — carry a DIFFERENT column set entirely: `swap_volume` / `swap_fees` / `total_shares` (no `tvl_usd`,
  `volume_usd`, `fees_usd`, or `fee_rate_bps` columns at all). `CanonicalDexPoolProvider._aggregate_pool_state` reads
  `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps` by name — for a BALANCER row these keys are absent, so
  `_to_float(record.get(col))` silently returns `0.0` for all four. Result: **every BALANCER pool has read
  `fee_apy_bps=0` in production regardless of real on-chain fee activity**, independent of the `dex_pool_fees`
  retirement (that corpus was ALSO confirmed empty for its entire lifetime, so it never covered Balancer either — this
  is a pre-existing, separate bug, not a regression from the retirement). Additionally, Balancer's subgraph
  `swapVolume`/`swapFees` are CUMULATIVE per-pool totals (not daily deltas) per the protocol's snapshot schema — even a
  column rename alone would NOT fix this; the writer needs a day-over-day delta computation (the exact logic the now-
  deleted `materialize_dex_pool_fees.py::_fetch_balancer_rows` already implemented, just never wired into the canonical
  `dex_pool_state` writer path).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, strategy-service]
scope: [engineer]
tags: [defi, dex-pool-state, balancer, schema-mismatch, writer-gap, fee-accrual, data-correctness]
related:
  [
    /plans/archive/issues/defi_dex_pool_fees_retirement_recommendation_2026_08_04.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-04"
author: unknown
last_updated: "2026-08-04"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
source: >-
  Found as a side-effect of the dex_pool_fees retirement dispatch's gating verification (bounded sample read of real
  production dex_pool_state parquet for CURVE-ETHEREUM + BALANCER-ETHEREUM, 2026-08-04). Not caused by that retirement —
  the underlying bug pre-dates it and would exist whether or not dex_pool_fees was retired.
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_subgraph.py,
    strategy-service/strategy_service/engine/core/canonical_dex_pool_provider.py,
  ]
---

# BALANCER `dex_pool_state` writer schema mismatch — fee accrual silently reads 0 (2026-08-04)

## Why this is filed as `assigned_vm: NA` (human-planning, not AO-dispatched)

The fix needs a real design decision (how to compute the daily delta from Balancer's cumulative subgraph fields, what
column names to standardize on across CURVE/BALANCER/other Messari-schema venues, whether to backfill historical days or
go-forward-only) before it is a bounded, deterministic AO todo — matches this workspace's "figure out how X should look
is a human decision wearing a todo's clothes" dispatch-scope bar. It also touches a live MTDS writer path that
`canonical_dex_pool_provider.py` (a strategy-layer read path) depends on, the same category of change the sibling
`dex_pool_fees` retirement doc declined to dispatch autonomously.

## What I found (empirical, 2026-08-04)

- **CURVE-ETHEREUM** `dex_pool_state` row (pool `CRV-FRXETH`, day=2026-07-13, read live from
  `gs://market-data-tick-defi-prd-central-element-323112`): columns include `tvl_usd`, `volume_usd`, `fees_usd`,
  `fee_rate_bps`, `daily_supply_revenue_usd`, `daily_protocol_revenue_usd` — POPULATED with real nonzero values
  (`tvl_usd=8097.69`, `volume_usd=69.48`, `fees_usd=0.2503`, `fee_rate_bps=2600`). This is the Messari-subgraph-daily
  shape (`_parse_curve`/`_parse_messari_dex` in
  `market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py`) — daily values, no delta
  computation needed.
- **BALANCER-ETHEREUM** `dex_pool_state` row for the EXACT pool `materialize_dex_pool_fees.py` targeted
  (`0x06df3b2bbb68adc8b0e302443692037ed9f91b42000000000000000000000063`, "Balancer USD Stable Pool", day=2026-06-20):
  columns are `protocol`, `chain`, `pool_id`, `pool_name`, `tokens_list`, `timestamp`, `swap_volume`, `total_shares`,
  `swap_fees`, `amounts`, `symbol`, `pool_address`, `pair_address`, `instrument_id`, `venue`, `instrument_type`,
  `data_type`, `available_at` — **no `tvl_usd`, `volume_usd`, `fees_usd`, or `fee_rate_bps` at all.** Sample real
  values: `swap_volume=11,605,303,288.26`, `swap_fees=854,998.45`, `total_shares=32,800.24`. This matches
  `_parse_balancer` in the same `_dex_pools_parsers.py` file — a DIFFERENT (legacy `dex_pools`-shaped) parser than the
  Messari one CURVE uses, whose Balancer subgraph query (`poolSnapshots`) returns CUMULATIVE `swapVolume`/`swapFees`
  (protocol-level running totals since pool inception, not a daily figure) with no delta computed before writing.
- `strategy-service/strategy_service/engine/core/canonical_dex_pool_provider.py::_aggregate_pool_state` (as of the
  2026-08-04 `dex_pool_fees` retirement commit) reads `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps` by literal column
  name via `_to_float(record.get(col))`. For a BALANCER row none of these keys exist in the DataFrame →
  `record.get(col)` is `None`/`NaN` → `_to_float` coerces to `0.0` for all four. `_fee_apy_bps` then sees
  `fees_usd<=0, volume_usd<=0` → returns `0.0` (honest-absence path) even though the pool has $854,998 of real
  cumulative swap fees on-chain.
- **Cumulative-vs-daily gotcha**: even a straight column rename (`swap_volume`→`volume_usd`, `swap_fees`→`fees_usd`)
  would be WRONG — `swap_volume=$11.6B` is obviously a lifetime cumulative figure for one pool, not one day's volume.
  The now-deleted `strategy-service/scripts/materialize_dex_pool_fees.py::_fetch_balancer_rows` already had the correct
  fix pattern (fetch one extra day before the window, delta cumulative→daily, treat a negative delta — a subgraph
  reindex/reset boundary — as an honest-skip day); that logic needs to move into the actual `dex_pool_state`-writing
  path (`_dex_pools_subgraph.py`/`_dex_pools_parsers.py::_parse_balancer`), not stay in a side corpus.
- Confirmed this is INDEPENDENT of the `dex_pool_fees` retirement: the retired `dex_pool_fees` corpus was confirmed to
  hold **zero objects under any sampled day** (10+ days spanning 2026-06 through 2026-08) — it never covered Balancer
  either, so Balancer's `fee_apy_bps=0` was ALREADY the production reality before, during, and after the retirement. The
  retirement changes no observable behavior for either venue.

## Todos

- [ ] [DESIGN] P2. Decide the target schema: should `_parse_balancer`
      (`market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py`) emit the SAME
      `tvl_usd`/`volume_usd`/`fees_usd`/`fee_rate_bps` column names the Messari parsers (`_parse_curve`/
      `_parse_messari_dex`) already use (recommended — one shape for `CanonicalDexPoolProvider` to read across every
      venue), and how to source `fee_rate_bps` for Balancer weighted pools (no single static fee tier on-chain the same
      way Curve/Uniswap have one — may need the vault-level `swapFeePercentage` per pool from the subgraph
      `pool.swapFee` field, not currently queried).
- [ ] [IMPL] P2. (Gated on the DESIGN above.) Add day-over-day cumulative→daily delta computation to the Balancer write
      path (mirror the deleted `materialize_dex_pool_fees.py::_fetch_balancer_rows` pattern: query one extra day before
      the window, delta consecutive cumulative snapshots, honest-skip a negative-delta day as a subgraph reindex
      boundary) so `swap_volume`/`swap_fees` become real daily `volume_usd`/`fees_usd` under the renamed canonical
      columns.
- [ ] [VERIFY] P2. After the writer change ships + a forward day captures, confirm
      `CanonicalDexPoolProvider.pool_for_day` returns a nonzero `fee_apy_bps` for a real BALANCER-ETHEREUM pool (e.g.
      re-sample the USDC/DAI/USDT pool `0x06df3b2bbb68adc8b0e302443692037ed9f91b42...`) — this is the acceptance bar,
      not just "columns renamed."
- [ ] [AUDIT] P3. Grep for any OTHER venue writers sharing the legacy `_parse_balancer`-style (non-Messari,
      cumulative-not-delta) shape under `_dex_pools_parsers.py` that might have the same silent-zero-fee bug — the DIAG
      for `dex_pool_fees_retirement` only checked CURVE + BALANCER (the two venues that script targeted); other venues
      sharing this legacy parser family were not audited.

## Progress Log

- **2026-08-04 (sub-agent dispatch, verifying `defi_dex_pool_fees_retirement_recommendation_2026_08_04.md`)**: found
  while doing the bounded live-parquet sample read that doc's own DIAG todo required. Filed as a separate issue (rather
  than folded into the retirement doc) because it is a genuinely different, larger-scope problem (a live MTDS writer
  schema/computation gap, not a "should we keep this corpus" question) that pre-dates and is unaffected by the
  retirement decision.
- **context-scout 2026-08-05**: populated/refreshed context_scope (3 entries).
