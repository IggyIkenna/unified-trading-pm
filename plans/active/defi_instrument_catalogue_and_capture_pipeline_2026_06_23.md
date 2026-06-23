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

## SHARPENED root cause (measured 2026-06-23 from live `_index`, UNISWAP_V3/dex_pool_state) — the grain mismatch is a NAMESPACE mismatch

Measured the actual instrument_id values per capture_status on the biggest live-venue DELISTED bucket. The two sides
use **DIFFERENT instrument_id vocabularies → 0 overlap → reconciliation is structurally impossible**:

| capture_status | instrument_id form | distinct | sample |
| --- | --- | --- | --- |
| `captured` (282 pools, back to 2021) | **`pool_address.lower()`** (canonical) | 282 | `0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8` |
| `empty_confirmed` (DELISTED 84,778) | **legacy glued composite** `UNISWAPV3-ARBITRUM:POOL:WETH-DAI:500` | 1,658 | `UNISWAPV3-ARBITRUM:POOL:LDO-WETH:3000` |

`captured ∩ DELISTED instrument_id = 0`. DELISTED dates are RECENT (2026-03-02→2026-06-23, 114 days) on LIVE pools —
captured history runs 2021→2026-06-21. So the seeded per-pool cells (from `enumerate_expected_universe.py` reading the
IS catalogue) carry the **legacy glued `PROTOCOL-CHAIN:POOL:PAIR:fee` instrument_id**, while the captured rows carry the
**canonical `pool_address.lower()`** (`_canonical_defi_id`). They can never match → the live pools stay seeded-empty/DELISTED.
ALSO: captured has 7,952 BLANK-instrument_id rows (the venue×chain aggregates the dex handlers' `record_captured` emit) +
282 per-pool rows (from a newer/other path) — so the writer is ALSO emitting blank aggregates.

**Canonical decision (operator-locked, per `defi-canonical-naming-ssot.md` + `_canonical_defi_id`): pool instrument_id =
`pool_address.lower()`.** The glued `UNISWAPV3-ARBITRUM:POOL:...` composite is the legacy form the plan explicitly
eliminates. THREE convergence points must all use `pool_address.lower()`: (a) MTDS dex handlers' `record_captured`
(Phase 4 writer fix — thread per-pool `pool_id.lower()`), (b) the IS catalogue `instrument_id` (`build_instrument_catalogue.py`
/ `CATALOG_COLUMNS`), (c) the `enumerate_expected_universe.py` seeder reading (b). The reconcile (Phase 4-data) re-stamps
the 84,778 (×all venues = 408k) legacy-keyed empty cells once the namespaces converge.

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

- [x] ✅ [CODE] P1. Add `EXPECTED_NOT_ENOUGH_TVL` to the `EmptyConfirmedReason` closed set — a pool that EXISTS but is
      below the TVL filter on that day is a GENUINE empty. — unified-api-contracts@7459ee9a | added enum member
      (`honest_coverage.py:135`) + `OUT_OF_COVERAGE_WINDOW_REASONS` (denominator-excluded, like NOT_LISTED); keystone-exempt
      (writer gate at `_writer_record.py:238` only requires FetchEvidence for `SOURCE_RETURNED_ZERO`, so no evidence needed);
      `EMPTY_CONFIRMED_REASONS` frozenset auto-derives; QG-green (220s, exit 0).
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

- **2026-06-23 (autonomous takeover — fresh-context investigation COMPLETE, 3 parallel sub-agents)**: Mapped the full
  surface before touching code. KEY FINDINGS (decisive — reshape the fix):
  - **`instrument_id` IS already a first-class manifest dimension** — `unified-trading-library/.../manifest_writer/_writer_ingest.py`
    `add()` accepts `instrument_id: str=""` (Phase-1.9); `_rows.py` `_ROW_KEY_COLUMNS` includes it; `AvailabilityRecord.instrument_id`
    is a v9 column ("matches InstrumentRecord.instrument_key"); `_SHARD_ATOM_KEYS = frozenset({"instrument_id","chain"})`
    means once in a row_key it MUST be non-blank. **The prediction handler already records per-instrument via
    `instrument_id=cqg`** — that is the template. **NO UTL/UAC schema change needed** — the writer fix THREADS an existing column.
  - **Live `_index` measured fresh** (`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`):
    **6,519,518 rows, 100% schema_version=9**, `instrument_id` non-null on all, **11,628 distinct instrument_id values**.
    capture_status: empty_confirmed 3,626,037 / expected_unattempted 1,856,985 / captured 1,005,848 / attempted_failed 30,648.
    empty reasons: NOT_LISTED 1,977,666 · PRE_GENESIS_CHAIN 1,171,997 · **DELISTED 408,442 (matches plan)** · SOURCE_RETURNED_ZERO 48,925 ·
    PRE_VENUE_LAUNCH 18,665. DELISTED spans live venues (UNISWAP_V3 254,334 / PANCAKESWAP_V3 33,652 / UNISWAP_V4 32,368 /
    CAMELOT_V3 9,294 / AERODROME_V3 6,256) AND lending/perp/oracle (AAVE_V3/COMPOUND_V3/MORPHO) — so the fix touches MORE
    handlers than just dex_swaps+dex_pools. 35 distinct data_types present (not 4); the 4 MVP DeFi data_types =
    `dex_pool_state`, `dex_pool_swaps`, `oracle_prices`, + lending/lst.
  - **ROOT CAUSE pinned (the grain mismatch, exactly)**: IS lifecycle catalogue `build_instrument_catalogue.py` →
    `instruments-store-defi-prd/prod/catalog.parquet` emits per-pool rows (`instrument_id=pool_address.lower()`,
    `available_from`/`available_to`, `mvp`). `enumerate_expected_universe.py::_enumerate_v2_defi` seeds the `_index`
    PER-POOL with `instrument_id`: `date > available_to` → `EXPECTED_INSTRUMENT_DELISTED`. But the DEX/lending handlers'
    `record_captured` pass **NO `instrument_id`** (`_defi_manifest.py::_emit_captured_add` + `_build_row_key` omit it) →
    a captured venue×chain aggregate row `(date,UNISWAP_V3,ARBITRUM,dex_pool_state,instrument_id="")` NEVER reconciles
    against the per-pool seeded cell `(...,instrument_id=0xabc...)` → the per-pool cell stays at its seeded
    empty/DELISTED state. PLUS the catalogue `available_to` closes when a still-live pool drops out of a daily top-N-by-TVL
    subgraph snapshot → next day `date>available_to` → DELISTED on a genuinely-live pool (the discontinuous-liquidity nuance, Phase 2).
  - **EmptyConfirmedReason** = 36 values in `unified-api-contracts/.../canonical/crosscutting/honest_coverage.py` (line 89 enum;
    `EMPTY_CONFIRMED_REASONS` frozenset auto-derives; `OUT_OF_COVERAGE_WINDOW_REASONS` line ~451 = denominator-excluded set).
    Adding `EXPECTED_NOT_ENOUGH_TVL` = one enum line + add to `OUT_OF_COVERAGE_WINDOW_REASONS` (it's outside-coverage like NOT_LISTED).
  - **Catalogue today**: lifecycle roll-up daily 01:00 UTC via `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf`
    (`lifecycle-catalogue-regen-defi` Cloud Run job). Single `(available_from,available_to)` pair — NO discontinuous-range modeling yet (Phase 2).
  - **PLAN OF ATTACK** (revised, dependency-ordered): (5) UAC `EXPECTED_NOT_ENOUGH_TVL` first (lowest-risk, unblocks correct
    classification) → (4-writer) thread per-pool `instrument_id` through dex_swaps + dex_pools handlers (+ verify lending/oracle/perp
    handlers' grain) → (1-3) IS catalogue per-pool availability + monotonic available_to (fix premature delisting) →
    (4-data) re-capture/reconcile the 408k → (gates) answer the 4 verification gates with measured evidence.
