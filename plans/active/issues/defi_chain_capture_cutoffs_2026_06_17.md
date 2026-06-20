---
title: DeFi BSC capture "cutoff" + corpus-wide mid-history venue-cutoff scan
created: 2026-06-17
author: ikennaigboaka [investigation]
source:
  - plans/audit/results/instrument_pool_universe_audit_2026_06_17/defi.md
  - gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet
  - gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet
  - gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet
  - unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py
locked_by: live-defi-rollout
status: active
priority: P2
---

## What I found

### BSC "drops after 2023" — it is NOT a coding drop and NOT a dead endpoint. It is (a) a sampling artifact + (b) sparse intermittent subgraph coverage.

The DeFi pool-universe audit sampled **one mid-June day per year** (2024-06-15, 2025-06-15, 2026-06-15) and saw
`chain=BSC / PANCAKESWAP_V3` present only in 2023 → flagged "BSC drops after 2023". That conclusion is wrong; the
sample days simply landed on un-captured/empty BSC days.

Direct manifest evidence (`PANCAKESWAP_V3 / chain=BSC / data_type=dex_swaps`, 1,245 manifest rows):

- `captured`: **400 rows, date range 2023-04-01 → 2026-04-28** — **110 captured days in 2024**, 14 in 2025, 1 in 2026.
- `empty_confirmed`: **844 rows, `error_reason=SOURCE_RETURNED_ZERO`** (honest absence — the writer attempted, the
  subgraph returned zero swaps for that day).
- `attempted_failed`: 1.

GCS confirms: `day=2025-10-15/.../venue=PANCAKESWAP_V3/chain=BSC/.../dex_swaps/` HAS a parquet; `day=2024-09-15` does
NOT. So BSC data genuinely exists for 2024/2025 — just not on the June sample days. The audit's mid-June probe missed it.

**Why it's intermittent, not continuous:** all BSC parquets carry a single backfill epoch write-stamp
(`*_BSC_20260525_*`, written 2026-05-25/26). Compare: `PANCAKESWAP_V3 / chain=ETHEREUM` from the SAME 2026-05-26 run is
present continuously 2023→2026, and `UNISWAP_V3 / ETHEREUM` continues past 2024-03 — so this is **not** a generic
backfill-horizon cutoff. The BSC PancakeSwap subgraph (`Hv1GncLY5docZoGtXjo4kwbTvxm3MAhVZqBZE4sUT9eZ`,
`_defi.py:146`) returns `poolDayDatas` only for a SUBSET of days (the historic TheGraph hosted-service → decentralized-
net BSC migration left coverage holes), and the backfill honestly recorded the holes as `empty_confirmed`.

**Root-cause file:line:**
- `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py:145-149` — `pancakeswap_v3`
  IS wired for BSC (subgraph id present), `get_supported_chains_for_protocol("pancakeswap_v3")` returns `["BSC",
  "ETHEREUM","BASE"]`, `get_subgraph_id` (`:228`) resolves BSC → not None. **The code does not drop BSC.**
- `market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py:211` enumerates BSC via that
  registry; `:316` routes a zero-result subgraph response to `empty_confirmed` (the 844 `SOURCE_RETURNED_ZERO` rows).
  BSC is chain-agnostic-handled, with a dedicated `_PANCAKESWAP_BSC_SWAPS_QUERY` (`:57`, `:521`).

### Recurrence: a fresh run captures BSC today (wired + endpoint live, intermittent).
BSC stays in the supported-chain list (`aave_v3:94`, `pancakeswap_v3:146`, `venus:188`) and resolves to live subgraph
IDs, so the next batch run WILL attempt BSC and capture it on the days the subgraph has data (it captured a 2026-04-28
day). It will NOT silently stop. The "gap" is the subgraph's sparse historical coverage, not a capture-pipeline break —
i.e. a **backfill-completeness** issue (fill the `empty_confirmed`/un-attempted BSC days from an alt source), not a
re-enable-code issue.

### Other real mid-history (chain,protocol/venue,data_type) cutoffs found

**DeFi:** no OTHER per-(chain,protocol,dex/lending) hard cutoff — the only BSC anomaly is the sparse-coverage one above.
(Solana side-tree static-snapshot issue is already filed in the audit, item #1; not a cutoff.)

**CeFi** (corpus captured max 2026-05-24):
- `DERIBIT / liquidations` last captured **2022-08-21** while every other Deribit data_type (trades, book_snapshot_5,
  derivative_ticker) runs to 2026-05-22 → **real upstream (Tardis) Deribit-liquidations coverage window ended Aug 2022.**
- Perp-future liquidations cut off mid-history: `LTCF0`/`UNIF0` (2021-01), `DOGEF0` (2023-01), `ADAF0`/`BTCF0` (2024-01)
  → Tardis liquidation-feed per-instrument coverage windows.
- `BYBIT ohlcv_*` last captured **2024-01-02** — but BYBIT trades/derivative_ticker continue to 2026-05-22, and only
  brand-new venues (LIGHTER-ZKSYNC, PACIFICA-SOLANA) still write recent `ohlcv_*`. This is a **data-model shift**
  (ohlcv derived downstream, raw trades captured) — NOT a venue cutoff. Sanity-checked, benign.

**TradFi** (corpus captured max 2026-06-05):
- `CBOE / ohlcv_1m` last 2024-01-01, `YAHOO_FINANCE / ohlcv_24h` last 2020-02-04 — narrow per-source windows;
  VIX/Yahoo coverage is already governed by the dual-source continuity registry (CLAUDE.md "VIX 15m" rule), so likely
  expected. Worth a confirm but not a silent break.

## Why it matters

1. **The audit's "BSC retired/coverage-drop" flag is a false alarm** caused by single-day-per-year sampling on a
   sparsely-captured chain. Any audit that samples N days/year MUST cross-check the manifest `capture_status` per
   (venue,chain,data_type) before declaring a chain "dropped" — a `dex_swaps`/onchain venue can be `captured` on most
   days and `empty_confirmed`/un-backfilled on the exact sample day.
2. The genuine BSC gap is **backfill incompleteness** (844 `empty_confirmed` + un-attempted days), which IS a data-
   heartbeat issue: PancakeSwap-BSC is a named `arbitrage_price_dispersion` DEX venue, so its history should be filled.
3. `DERIBIT/liquidations` (and the F0 liquidations windows) are real upstream coverage ends — honest-absence correct,
   but should be acknowledged so downstream liquidation features don't treat post-2022 Deribit-liq absence as a bug.

## Root cause (per cutoff)

| Cutoff | Verdict | Root cause |
|---|---|---|
| BSC PANCAKESWAP_V3 dex_swaps "absent 2024+" | **sampling artifact + sparse intermittent subgraph coverage** (NOT coding-drop, NOT dead endpoint) | `_defi.py:146` BSC wired & live; handler captures it (`dex_swaps_handler.py:211`); 110 captured days in 2024, 844 `empty_confirmed SOURCE_RETURNED_ZERO`; audit probed only mid-June (a non-captured day) |
| DERIBIT liquidations (last 2022-08-21) | upstream-coverage-window-end | Tardis Deribit-liquidations feed; other Deribit dtypes continue to 2026-05 |
| LTCF0/UNIF0/DOGEF0/ADAF0/BTCF0 liquidations | upstream-coverage-window-end | Tardis per-instrument liquidation windows |
| BYBIT ohlcv_* (last 2024-01-02) | NOT a cutoff (benign) | data-model shift: raw trades captured to 2026-05, ohlcv derived downstream |
| CBOE ohlcv_1m / YAHOO ohlcv_24h | likely-expected (dual-source continuity) | VIX/Yahoo source-continuity registry governs these windows |

## Recommended decision

1. **BSC**: re-enable is a no-op (already wired + live). The action is **backfill the BSC PancakeSwap_V3 dex_swaps
   history** to fill the `empty_confirmed SOURCE_RETURNED_ZERO`/un-attempted days from an alternate source (PancakeSwap
   info API / a richer BSC subgraph), since the decentralized-net subgraph has historical holes. Treat as a DeFi
   data-heartbeat backfill todo, NOT a code change. **Operator decision: is the sparse BSC PancakeSwap history good
   enough for `arbitrage_price_dispersion`, or fund a richer BSC source?**
2. **Audit-method fix**: the pool-universe audit must reconcile per-day sampling against the manifest `capture_status`
   before flagging a chain "dropped" (add to the audit instructions).
3. **DERIBIT/F0 liquidations + CBOE/Yahoo ohlcv**: confirm these against the source-continuity registry; if they are
   genuine vendor coverage ends, record them as known gaps (no fix). If any is a feed that SHOULD continue, file a
   per-venue backfill.

- [ ] [DATA] P1. Backfill BSC PancakeSwap_V3 `dex_swaps` history (fill `empty_confirmed SOURCE_RETURNED_ZERO` + un-attempted days from an alt BSC source) — repo: market-tick-data-service. **DEFERRED pending operator decision** on richer-BSC-source vs accept-sparse. Provenance: this issue doc.
- [ ] [DATA] P2. Confirm DERIBIT/liquidations + LTCF0/UNIF0/DOGEF0/ADAF0/BTCF0 liquidations + CBOE/YAHOO ohlcv windows against `unified_api_contracts/registry/data_source_continuity.py`; record genuine vendor coverage-ends as known gaps. **NICE-TO-HAVE**. Provenance: this issue doc.
- [ ] [DATA] P2. Audit-method fix: pool-universe audit must reconcile per-day sampling vs manifest `capture_status` before declaring a chain "dropped" — update `plans/audit/instructions/` for the instrument_pool_universe audit. Provenance: this issue doc.
