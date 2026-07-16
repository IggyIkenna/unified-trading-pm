---
doc_type: issue
title:
  DRIFT Helius perp_funding shards contain ZERO funding rates — 1.2M mislabeled signature rows/day counted as captured
summary:
  "The Helius `perp_funding` path writes rows whose funding fields are ALL hardcoded 0.0 — it captures transaction
  signatures, not funding. Verified on prod: day=2025-01-09 `drift_helius_SOL-PERP_20250109.parquet` = 1,209,478 rows,
  data_quality='helius_v2_signatures_only' (100%), funding_rate_24h/mark_price/oracle_price nonzero=0/1209478, every row
  stamped symbol='SOL-PERP' + market_index=0 though the sig index is DRIFT-PROGRAM-wide (all markets/liquidations/
  oracle cranks), and written under the WRONG partition pipeline_mode=batch_hyperliquid. These shards count as
  `captured` perp_funding, satisfying the mvp_backfill_defi_onchain_v10 MVP gate with data containing no funding rates.
  The correct data already exists beside them: the Velocity per-day CSV path writes 24 real hourly rows/day
  (batch_onchain_rpc/SOL-PERP.parquet, funding_rate=0.002007041 …, per-market, ~7 KB). Recommendation: delete the helius
  shards, retire the Helius perp_funding path, let the Velocity API own history."
status: open
nature: record
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, drift, perp-funding, helius, data-correctness, mislabeled, mvp-gate, pipeline-mode, silent-corruption]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md,
    plans/active/issues/mtds_solana_drift_backfill_manifest_staleness_redoes_captured_days_2026_07_15.md,
    plans/active/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
  ]
created: 2026-07-16
assigned_vm: NA
source:
  ["operator question 2026-07-16 (does Drift's public API give us full history)", "live parquet + API verification"]
parent_epic: defi_master
priority: P0
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-16
---

# DRIFT Helius perp_funding shards are zero-valued signature noise (2026-07-16)

> Found while answering the operator's question "does Drift's public API give us what we need for full history?". The
> answer turned out to be yes — and in proving it, the Helius shards were shown to contain no funding data at all.

## Evidence (measured on prod, not inferred)

**The Helius shard** —
`day=2025-01-09/pipeline_mode=batch_hyperliquid/…/venue=DRIFT/…/data_type=perp_funding/ drift_helius_SOL-PERP_20250109.parquet`:

| check                                 | result                             |
| ------------------------------------- | ---------------------------------- |
| rows                                  | **1,209,478**                      |
| `data_quality`                        | `helius_v2_signatures_only` (100%) |
| `funding_rate_24h` nonzero            | **0 / 1,209,478**                  |
| `mark_price` / `oracle_price` nonzero | **0 / 1,209,478**                  |
| `market_index` nonzero                | 0 / 1,209,478 (hardcoded)          |
| distinct `symbol`                     | `['SOL-PERP']` — all 1.2M rows     |
| partition `pipeline_mode`             | **`batch_hyperliquid`** (wrong)    |

Code: `market_tick_data_service/cli/handlers/solana_defi_drift_helius.py::_parse_helius_batch` (~:229-272) hardcodes
`funding_rate_24h/7d/30d = 0.0`, `oracle_price = 0.0`, `mark_price = 0.0`, `oi_long/short = 0.0`, `market_index = 0`,
and stamps `"symbol": market` (the CLI-provided string) on every row unconditionally — while the sig index it reads is
built at the **DRIFT V2 PROGRAM level** (every instruction touching the program: all markets, trades, funding
settlements, liquidations, oracle cranks) per `drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md`. So the rows
are (a) not funding data and (b) not SOL-PERP's transactions.

**The correct data, already present for the same day/market** —
`…/pipeline_mode=batch_onchain_rpc/…/perp_funding/ SOL-PERP.parquet` (written by the AO-launched
`backfill_drift_v2_historical`, Velocity per-day CSV path):

| check            | result                                                                                                                                                                                            |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| rows             | **24** — exactly the day's hourly funding settlements (ts deltas ≈3600s)                                                                                                                          |
| `funding_rate`   | **real** — 24/24 nonzero, e.g. `0.002007041`                                                                                                                                                      |
| schema (23 cols) | `ts, tx_sig, tx_sig_index, slot, record_id, market_index, symbol, funding_rate, funding_rate_long, funding_rate_short, cumulative_funding_rate_long/short, oracle_price_twap, mark_price_twap, …` |
| labeling         | per-market by URL **and** `symbol` carried in the payload; `market_index=0` is genuinely correct (SOL-PERP IS marketIndex 0)                                                                      |
| size             | ~7 KB vs the Helius shard's 1.2M rows                                                                                                                                                             |

**Velocity API coverage envelope** (probed live 2026-07-16,
`data.api.drift.trade/market/{MKT}/{fundingRates|trades}/ {Y}/{M}/{D}?format=csv`): real data genesis **2022-11-04 →
~2026-03-31**; **2026-04-05+ returns HTTP 200 with 0 bytes** (archive lags real-time ~3.5 months; bisected 03-29 ✓ /
04-05 ✗). Trades paginate at 4,999 rows/page via `page=N` (`limit`/`offset`/`cursor` are silently ignored) — SOL-PERP
2025-01-09 = 17,219 trades across 4 pages; `drift_v2_historical_handler.py` already paginates correctly (docstring:
"5000 rows/page; pages iterate until empty body").

## Why it matters

- These shards are `capture_status=captured` for `perp_funding` — an MVP gate data_type on
  `mvp_backfill_defi_onchain_v10` — so **the gate is being satisfied by rows with no funding rates**, and the DeFi
  captured% on the Honest Coverage panel is inflated by them.
- Anything reading `perp_funding` for DRIFT gets 1.2M zero-funding rows instead of 24 real ones.
- Interaction with `mtds_solana_drift_backfill_manifest_staleness_redoes_captured_days_2026_07_15` (skip-gate,
  `mtds@6d91aa33`): the gate correctly stops re-walking "captured" days — but for these days the captured data is WRONG,
  so they must be deleted (making them genuinely uncaptured) rather than skipped. Order matters: delete first, then the
  Velocity backfill refills them.

## Todos

- [ ] [SCRIPT] P0. Enumerate every `drift_helius_*.parquet` shard (all dates/markets; bounded prefix scan) + their
      manifest rows. Report counts. (Jan-2025 sample: 8 files.) Repo: market-tick-data-service.
- [ ] [SCRIPT] P0. Delete them + their manifest rows (or reclass to honest absence) so the days become genuinely
      uncaptured and the Velocity backfill refills them. Follow the ICE-purge precedent
      (`purge_tradfi_ice_non_24h_2026_07_14.py`): snapshot → pause the defi consolidator cron → dry-run → apply → verify
      row deltas → GCS-delete via UTL `gcs_delete_object` → resume + confirm a green cycle. Repo:
      market-tick-data-service.
- [ ] [CODE] P0. Retire the Helius `perp_funding` write path (`_backfill_drift_helius_date` / `_parse_helius_batch` /
      `_resolve_helius_rows`, `solana_defi_drift_helius.py`) — it cannot produce funding rates by construction
      (signature metadata only) and the Velocity path supersedes it for genesis→~2026-03-31. Delete rather than shim
      (no-shims rule). Keep/park the sig-index work only if some OTHER data_type genuinely needs it — state which, or
      delete that too. Repo: market-tick-data-service.
- [ ] [CODE] P1. Fix the partition bug: DRIFT Helius shards were written under `pipeline_mode=batch_hyperliquid`
      (verified live). If the Helius path is deleted per the todo above this dies with it — otherwise fix the mode
      resolution. Audit whether any OTHER venue's shards carry a foreign `pipeline_mode`. Repo:
      market-tick-data-service.
- [ ] [DECISION] P1. The ~2026-04-01→today tail has NO Velocity archive coverage (200/0 bytes). Decide the source for
      it: (a) wait — the archive lags ~3.5 months and should backfill itself; (b) live capture forward from now; (c)
      another source. Note the DRIFT `derivative_ticker` leg is separately broken (legacy
      `fundingRates?     marketName=` endpoint now 403 — see
      `defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15`).

## Progress log

- 2026-07-16: Filed. Operator asked whether Drift's public API covers full history; proving it out surfaced that the
  Helius shards it would replace contain no funding data at all. Operator's initial instinct was to redesign the Helius
  adapter (fetch program-wide once, filter per market, keep per-instrument-per-day writes) — that design is sound in the
  abstract but unnecessary: the Velocity API already returns correct per-market funding directly, so the recommendation
  is RETIRE rather than redesign. Nothing deleted yet — purge is the P0 todo above.
