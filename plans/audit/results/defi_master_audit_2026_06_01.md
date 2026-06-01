---
type: audit-result
epic: defi_master
instructions_ref: plans/audit/instructions/defi_master_audit_instructions.md
auditor: ikenna (interactive slot 1)
date: 2026-06-01
status: RED
scope: Strategy Data-Coverage Audit (items o–v) — staked basis carry / funding rate arb / basis carry
data_source:
  prd availability_index (defi 1.57M rows, cefi 2.64M rows, tradfi) — read from actual manifest, not constants
---

# DeFi Master — Strategy Data-Coverage Audit Result (2026-06-01)

> Run of the new **Strategy Data-Coverage Audit** (items o–v) added to the instructions today. Detailed per-cell
> breakdown: [`defi_strategy_coverage_report_2026_06_01.md`](defi_strategy_coverage_report_2026_06_01.md). Query:
> [`defi_strategy_coverage_query_2026_06_01.py`](defi_strategy_coverage_query_2026_06_01.py).

## Headline — all three strategies are RED on data

| Strategy                                      | Verdict                    | Why                                                                                                                                                                                                                                                                   |
| --------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **staked basis carry** (`carry_staked_basis`) | 🔴 NO USABLE DATA          | `lst_rates` **does not exist** as a data_type (0 rows). `staking_yields` exists (64,313 rows) but **0 captured**, stale to 2025-01-30. `lending_indices` 0 captured (stale 2025-01-30). `oracle_prices` only 5,053/69,366 captured (Ethereum only, stale 2026-01-23). |
| **funding rate arb** (`carry_basis_perp`)     | 🔴 PARTIAL + STALE         | CeFi has **no `perp_funding` data_type** — funding rides inside `derivative_ticker`, captured 0–68% per venue and stale ~3–5 weeks (max 2026-04-28→05-06). **OKX-FUTURES + ASTER = 0% captured** (100% attempted_failed).                                             |
| **basis carry** (`carry_basis_dated`)         | 🟠 SPOT/FUTURE LEGS PATCHY | Deribit `derivative_ticker` only 23% captured; `options_chain`/`futures_chain` present but partial. TradFi `trades`/`ohlcv_1m` healthier (CME 91%/96%) but `basis_bps` feature derivation for crypto basis blocked on the patchy Deribit leg.                         |

## Cross-cutting findings (apply to all strategies — BIG, operator notify)

- **(F1) v9 schema migration is ~0% in the DATA.** defi v9 = **0.03%** (407/1,569,805), cefi v9 = **0.00%**
  (0/2,640,864). The corpus is entirely v8 despite `MANIFEST_SCHEMA_VERSION = 9`. This is the exact "constant ≠
  data-state" incident the operator codified on 2026-05-20, recurring. Item (r) = RED.
- **(F2) `lst_rates` canonical data_type is absent from the corpus.** The strategies + catalog call for `lst_rates`; the
  manifest only has `staking_yields`. Either the LST handler writes the wrong data_type name or `lst_rates` was never
  enumerated. Item (s) = RED (data_type SSOT name not honoured in written rows).
- **(F3) DeFi venue naming uses legacy `VENUE-CHAIN` format + a nonsensical cartesian grid.** `perp_funding` rows are
  attributed to `UNISWAPV3-ETHEREUM`, `LIDO-ETHEREUM`, `AAVEV3-ETHEREUM`, `RAYDIUM-SOLANA` (DEX/LST/lending venues, not
  perps); same cross-product for `staking_yields`. Chain is embedded in the venue string instead of the `chain` column.
  Item (s)/(n) = RED. (expected_coverage.py already flags the `VENUE-CHAIN` format as a 2026-05-22 bug — it persists in
  data.)
- **(F4) DeFi capture is effectively zero.** Across `staking_yields` / `perp_funding` / `lending_indices` (and
  `oracle_prices` outside Ethereum), **0 captured rows**. The empties are mostly honest (`EXPECTED_PRE_GENESIS_CHAIN`
  34,411 + `EXPECTED_INSTRUMENT_NOT_LISTED` 29,902) but the net is: **no usable captured DeFi data for any MVP
  strategy.** Item (q)/(t) = RED.
- **(F5) Massive CeFi `attempted_failed` on key perp venues.** `derivative_ticker`: OKX-FUTURES 0% captured (22,012 all
  failed), ASTER 0% (5,706 failed); `book_snapshot_5`: OKX-FUTURES 46,223 all failed, COINBASE-SPOT 2,272/53,965 (4%).
  These are fetch failures, not absences — a backfill/credential problem, not honest empty. Item (q) = RED.
- **(F6) Staleness — data stops weeks ago.** CeFi perp `derivative_ticker` max dates 2026-04-28 → 05-06 (today 06-01 →
  ~3–5 weeks stale). DeFi `oracle_prices` Ethereum stale to 2026-01-23. A strategy cannot paper-trade on weeks-stale
  data.

## Per-item verdict (o–v)

| Item                                           | Verdict             | Evidence                                                                                                              |
| ---------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------- |
| (o) IS universe present                        | 🟠 NOT VERIFIED     | Manifest enumerates venues, but DeFi venue strings are legacy-format (F3) — IS↔manifest reconciliation needed.        |
| (p) Expected-coverage dump                     | 🟠 STALE            | `expected_coverage_dump_2026_05_20.parquet` is 12 days old; a2 hardcodes END_DATE 2026-05-20 — needs re-run to today. |
| (q) Divergence = 0 for strategy cells          | 🔴 RED              | 0 captured DeFi; 0–68% CeFi perp; OKX/ASTER 100% failed (F4/F5).                                                      |
| (r) v9 per-data_type from data                 | 🔴 RED              | defi 0.03%, cefi 0.00% at v9 (F1).                                                                                    |
| (s) Venue/data_type SSOT names in rows         | 🔴 RED              | `lst_rates` absent (F2); `VENUE-CHAIN` legacy + cartesian grid (F3).                                                  |
| (t) Required-history window covered            | 🔴 RED              | DeFi has no captured window; CeFi perp stale ~3–5 weeks (F6).                                                         |
| (u) features emit consumed feature over window | 🟠 BLOCKED-UPSTREAM | Cannot evaluate features over a window the upstream corpus doesn't cover. Re-run after q/t green.                     |
| (v) Honest-coverage totality breakdown         | ✅ PRODUCED         | Full per-data_type × venue and × chain tables in the linked report; this result is item (v).                          |

## Download / migration backlog (gaps as plan todos)

> Per `External Data Is Always Available` + `Data Pipeline Correctness Is The Heartbeat`: every cell below is a
> download/migration/fix item, NOT a deferral. To be wired into a `parent_epic: defi_master` plan (see Recommended
> action).

- [ ] [DATA] P0. Diagnose + fix `lst_rates` absence — confirm whether the LST handler writes `staking_yields` instead of
      canonical `lst_rates`, or never enumerates; then backfill `lst_rates` for Lido/RocketPool/Coinbase/Jito/Marinade
      over ≥1y. parent_epic: defi_master (F2)
- [ ] [DATA] P0. Backfill DeFi capture for `staking_yields`/`lst_rates`, `lending_indices`, `oracle_prices` (all chains
      past genesis) — currently 0 captured; strategies have no DeFi leg. parent_epic: defi_master (F4)
- [ ] [DATA] P0. Fix CeFi perp `derivative_ticker` capture failures — OKX-FUTURES + ASTER 100% attempted_failed; raise
      capture to ≥95% for Binance/Bybit/OKX/Deribit/Hyperliquid/Aster/Kraken + refresh to current date. parent_epic:
      defi_master (F5/F6)
- [ ] [MIGRATION] P0. v8→v9 manifest migration in actual rows — corpus is ~0% v9 despite the constant; re-version defi +
      cefi (+ tradfi source column) within the single-walk window. parent_epic: manifest_master (F1)
- [ ] [MIGRATION] P1. Normalise DeFi venue names off legacy `VENUE-CHAIN` format → flat venue + `chain` column; stop the
      cartesian data_type×venue grid (perp_funding attributed to DEX/LST venues). parent_epic: defi_master (F3)
- [ ] [DATA] P1. Refresh CeFi `book_snapshot_5` capture for OKX-FUTURES (0%), COINBASE-SPOT (4%) — fetch failures, not
      absences. parent_epic: cefi_master (F5)
- [ ] [SCRIPT] P2. Rename `a4_manifest_v8_compliance.py` → v9 and update `a2`/`a3` END_DATE to dynamic-today
      (stale-tooling finding from item r/p). parent_epic: manifest_master

## Transparency (where this sampled vs walked)

- **Walked exhaustively**: the full prd `_index/availability_index.parquet` for defi (1,569,805 rows) + cefi (2,640,864)
  - tradfi — every strategy-relevant `(data_type, venue, chain, capture_status, schema_version, date)` cell, no
    sampling.
- **Not covered here**: per-symbol/instrument axis (the index aggregates above instrument_id for most DeFi rows); the
  features-service corpus (item u — blocked until upstream q/t green); AWS-fleet manifest (GCP prd only); non-prd
  buckets.
- **Caveat**: `empty_confirmed` reason verification (owed-data vs genuine) done at the aggregate level — a per-reason
  audit against `is_before_source_coverage_start()` is the follow-up for the backfill plan.

## Gap → plan absorption

| Gap                                    | Active plan absorbing it                        | Plan status |
| -------------------------------------- | ----------------------------------------------- | ----------- |
| F1 (v9 in data)                        | _to file_ — manifest_master remediation wrapper | pending     |
| F2/F3/F4 (DeFi capture + naming)       | _to file_ — defi_master data-backfill wrapper   | pending     |
| F5/F6 (CeFi perp failures + staleness) | _to file_ — cefi_master / mtds_mdps backfill    | pending     |

**Archive condition**: archives when all backlog items above are `- [x]` in their parent plans.
