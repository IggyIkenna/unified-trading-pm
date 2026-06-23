---
title: "DeFi instrument-availability → catalogue → MTDS per-pool capture (mirror CeFi)"
created: 2026-06-23
parent_epic: mtds_mdps_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
estimate_class: design
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 7
locked_by: live-defi-rollout
locked_since: 2026-06-23
---

# DeFi instrument-availability → catalogue → MTDS per-pool capture (mirror CeFi)

> **Operator design (2026-06-23, human-led)**: DeFi must mirror the CeFi pipeline. The instrument catalogue is the SSOT
> + the MVP filter (no separate filters unless a better one appears). Every `empty_confirmed` MUST be GENUINE
> (pre-genesis / not-listed / not-enough-TVL / proven source-returned-zero) — NEVER a bad-retrieval or wrong-naming
> empty. The current 408k `EXPECTED_INSTRUMENT_DELISTED` on LIVE Uniswap/Pancake/Camelot/Aerodrome pools is exactly the
> anti-pattern to eliminate.

## Root cause this plan fixes (drilled 2026-06-23)

`dex_swaps_handler.py::_record_shard_manifest` (line 341) records ONE blank-`instrument_id` row per (venue, chain) with
`instrument_type="pool"`, `row_count=<sum of all pools>` — while the IS catalogue enumerates **per-pool**
(`UNISWAPV3-ARBITRUM:POOL:AAVE-USDC:100`, …). The swaps ARE fetched (`count>0`), but the per-pool catalogue cells never
match the blank-aggregate captured row → fall to `empty_confirmed` + the lifecycle stamps `EXPECTED_INSTRUMENT_DELISTED`
on **live, liquid pools**. ~408k rows across UNISWAP_V3/V4, PANCAKESWAP_V3, CAMELOT_V3, AERODROME_V3 on every chain.
Plus the instrument_ids are non-canonical (`UNISWAPV3-ARBITRUM:POOL:…` = glued venue-chain, not `UNISWAP_V3` +
`chain=ARBITRUM`). Operator decision: **canonical atom = per-pool; fix the WRITER** (not the enumerator).

## Phase 1 — IS per-day instrument availability (TVL-qualifying, per venue×chain×data_type)

- [ ] [CODE] P0. Per-day, enumerate every instrument (pool) meeting the **TVL criteria** for each venue × chain ×
      data_type (mirror CeFi's per-day instrument-availability snapshot). The TVL threshold is the MVP filter. Source =
      the per-venue subgraph/RPC pool universe ranked by TVL. — instruments-service
- [ ] [CODE] P0. Canonical instrument_id per pool: `venue=UNISWAP_V3` + `chain=ARBITRUM` (separate), instrument_id
      canonical (NOT glued `UNISWAPV3-ARBITRUM`). Align the catalogue's per-pool key to the canonical form the MTDS
      writer will stamp so the manifest cells reconcile. — instruments-service, unified-api-contracts

## Phase 2 — IS daily catalogue aggregation (available_from/to + liquidity windows)

- [ ] [CODE] P0. Daily scheduled job aggregates the per-day snapshots → per-instrument **available_from / available_to**.
      **DeFi liquidity nuance**: liquidity can DROP then recover, so model EITHER (a) a string of discontinuous
      `(from,to)` availability ranges, OR (b) `available_from/to` + a separate `liquidity_available_from/to` dissection.
      Pick (a) unless (b) proves simpler downstream. — instruments-service
- [ ] [VERIFY] P1. Per-day catalogue must be **monotonically ≥ the previous day for every (venue,chain,data_type,pool)
      combo** (cumulative availability only grows; a drop = a bug). Assert this in a daily check. — instruments-service

## Phase 3 — IS final aggregated catalogue + stats

- [ ] [CODE] P0. One daily-scheduled aggregation → a single catalogue file = everything available up to the present day
      for DeFi (the final SSOT MTDS reads). — instruments-service
- [ ] [VERIFY] P1. Dump the catalogue CSV, READ it, give detailed stats (instrument counts per venue/chain/data_type,
      available_from/to distributions, growth-over-time). Confirm it grows monotonically. — instruments-service

## Phase 4 — MTDS catalogue-filtered PER-POOL capture (the writer fix)

- [ ] [CODE] P0. **Fix `dex_swaps_handler` + `dex_pools_handler` to record PER-POOL** captured rows — one
      `record_captured(instrument_id=<canonical per-pool>, row_count=<that pool's count>, instrument_type="pool", …)`
      per pool that returned data, matching the catalogue grain. Drop the blank-instrument aggregate. The per-pool swap
      breakdown is already fetched (the subgraph returns per-pool); attribute it. — market-tick-data-service
- [ ] [CODE] P0. MTDS reads the IS catalogue as the MVP filter (the TVL-qualifying pools per day) — no extra filters.
      Capture the 4 DeFi data_types (dex_pool_swaps, dex_pool_state, + the 2 others) per-pool via VMs. — market-tick-data-service
- [ ] [DATA] P0. Re-capture/reconcile the ~408k currently-DELISTED-empty live-pool cells → `captured` (the data exists;
      the writer fix makes them reconcile). Verify honest_cov jumps + the DELISTED-on-live-pool count → 0. — market-tick-data-service

## Phase 5 — Genuine empty reasons (incl NOT_ENOUGH_TVL)

- [ ] [CODE] P1. Add `EXPECTED_NOT_ENOUGH_TVL` (or similar) to the `EmptyConfirmedReason` closed set — a pool that
      EXISTS but is below the TVL filter on that day is a GENUINE empty. — unified-api-contracts
- [ ] [RATCHET] P1. HARD invariant: a DeFi `empty_confirmed` is only valid if it's pre-genesis / not-listed /
      not-enough-TVL / proven source-returned-zero (FetchEvidence). A whole live-pool combo at empty = a bug (bad
      retrieval / wrong naming / grain mismatch), NOT honest absence. Wire a check. — market-tick-data-service

## Reference (the CeFi mirror)

- CeFi implementation is the template: per-day instrument availability → daily catalogue aggregation → catalogue-as-filter
  → MTDS capture. Read the CeFi catalogue + capture path and mirror it for DeFi.
- Canonical naming SSOT: `codex/02-data/defi-canonical-naming-ssot.md`.
- Shard-granularity SSOT (writer atom == enumerator atom == per-pool): `plans/epics/infrastructure_master.md`.

## Progress Log

- **2026-06-23 (human-led, slot-this-tab)**: Operator gave the full CeFi-mirror design. Drilled the root cause: the
  dex_swaps/pools writer records a blank-instrument venue×chain aggregate while the catalogue enumerates per-pool →
  408k live pools wrongly `EXPECTED_INSTRUMENT_DELISTED`. Operator chose canonical atom = per-pool (fix the writer).
  Plan captured. Next: Phase-4 per-pool writer fix (the bounded first code step), then the IS catalogue phases.
