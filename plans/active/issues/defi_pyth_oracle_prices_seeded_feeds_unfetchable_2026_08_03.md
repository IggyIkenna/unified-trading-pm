---
doc_type: issue
title:
  "Pyth oracle_prices manifest seeds expected_unattempted for feeds the collector's static _PYTH_FEEDS dict cannot fetch
  (JTO/RAY/WIF/JUP/USDC)"
summary: >-
  While executing defi_satellite_ao_dispatch_batch3-006 (C6 Pyth oracle_prices historical backfill), found the
  market-data-tick-defi manifest carries a newer PYTH-SOLANA:SPOT_PAIR:{SYM}-USD instrument_id family (seeded
  2026-08-01, 9 pairs incl. JTO/RAY/WIF/JUP/USDC) that is 100% expected_unattempted and structurally unsatisfiable — the
  collector's static _PYTH_FEEDS dict only has Hermes feed-ids for 7 symbols (SOL/BTC/ETH/JitoSOL/mSOL/bSOL/INF), none
  of which include JTO/RAY/WIF/JUP, and even the 4 overlapping symbols write under a DIFFERENT instrument_id key than
  the seeder expects. This blocks C6's own done-when ("zero remaining gap days") from ever being fully true.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer]
tags: [defi, oracle-prices, pyth, manifest, expected-unattempted, honest-absence]
related:
  [/plans/active/defi_satellite_ao_dispatch_batch3_2026_07_26.md, /plans/active/data_completion_defi_2026_07_15.md]
created: 2026-08-03
parent_epic: defi_master
priority: P2
source:
  "worker analysis (slot-12, data_engineering craft) while executing defi_satellite_ao_dispatch_batch3-006 (C6 Pyth
  oracle_prices backfill), 2026-08-03"
assigned_vm: NA
execution_scope: local-only
estimate_class: design
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# Pyth oracle_prices manifest seeds expected_unattempted for feeds the collector cannot fetch

## What I found

Checking the live `market-data-tick-defi-prd-central-element-323112` consolidated manifest
(`_index/availability_index.parquet`, bounded read via `venue=PYTH`, `data_type=oracle_prices` row-group filters — no
whole-corpus walk) plus the in-flight per-VM shard for a backfill I was running, I found the PYTH/SOLANA `oracle_prices`
rows exist under **three coexisting `instrument_id` naming conventions**:

1. `{SYMBOL}_USD` (e.g. `BTC_USD`) — legacy, `captured`, last written 2026-07-23.
2. `{symbol}/usd` (e.g. `btc/usd`) — the CURRENT format `oracle_prices_handler.py`'s `_write_oracle_rows` actually
   writes today (confirmed live from my own backfill VM's shard writes), `captured`/`empty_confirmed`.
3. `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD` (e.g. `PYTH-SOLANA:SPOT_PAIR:JTO-USD`) — a newer family, ALL rows
   `expected_unattempted`, written `2026-08-01T13:02:37Z` (looks seeder-generated, consistent timestamp across every row
   — likely `DefiManifestRecorder.emit_expected_unattempted_for_remaining`, the mechanism this same batch3 plan's C8
   item confirms shipped 2026-08-01).

Family 3 enumerates **9 distinct pairs**: `BSOL-USD`, `JITOSOL-USD`, `JTO-USD`, `JUP-USD`, `MSOL-USD`, `RAY-USD`,
`SOL-USD`, `USDC-USD`, `WIF-USD` — **1485 rows fleet-wide, 999 of them in the 2026-04-15..2026-08-03 window, 100%
`expected_unattempted`, zero `captured`.**

Cross-referencing against `market_tick_data_service/cli/handlers/_oracle_prices_constants.py`'s `_PYTH_FEEDS` static
dict: it has Hermes feed-ids for exactly **7 symbols** — `SOL`, `BTC`, `ETH`, `JitoSOL`, `mSOL`, `bSOL`, `INF` — with
**no entry at all** for `JTO`, `RAY`, `WIF`, or `JUP`. Even for the 4 symbols that DO overlap
(`SOL`/`JitoSOL`/`mSOL`/`bSOL`), the collector writes them under the lowercase-slash `instrument_id` (family 2), never
under the seeder's uppercase-dash `PYTH-SOLANA:SPOT_PAIR:` key (family 3) — so those rows can't reconcile to `captured`
even for symbols the collector genuinely fetches, without an `instrument_id`-naming fix on top of the missing-feed-id
fix.

`load_oracle_feeds_for_date("PYTH", "SOLANA", ...)` (`_instruments_metadata.py:478`) reads IS's `instruments-store-defi`
`venue=PYTH-SOLANA` catalogue to FILTER already-fetched rows to the IS-enumerated `(base,quote)` overlap — it does not
drive what gets fetched (the static feed dict does). This means IS's own PYTH-SOLANA catalogue apparently enumerates a
wider universe (including JTO/RAY/WIF/JUP/USDC) than the collector's static Hermes feed-id list supports, and the
manifest seeder used that wider IS catalogue as its "expected" set.

## Why it matters

- **A permanently-unsatisfiable `expected_unattempted` row is a false "still pending" signal, not a genuine gap awaiting
  a future run.** No VM backfill — including the one this issue's source todo (`defi_satellite_ao_dispatch_batch3-006`,
  C6) dispatched — can ever flip these 999 rows to `captured` as the code is currently written. This pollutes any future
  coverage audit/dashboard with an unfixable-by-backfill entry that looks identical to a genuine, closeable gap.
- **Blocks C6's own done-when from ever being fully true.** That todo's done criterion is "the consolidated manifest
  shows Pyth oracle_prices rows captured (or empty_confirmed) ... with zero remaining gap days" — with family 3 present,
  some rows will always read `expected_unattempted` regardless of how many times a backfill VM runs, until this is
  resolved separately.
- **Data-pipeline correctness heartbeat**: per CLAUDE.md's data-correctness HARD RULE, an audit's issues get fixed in
  full — but resolving this requires a real design/operator call (see below), not a mechanical worker fix, so it is
  filed rather than force-fixed inline.

## Recommended decision (operator/design ruling — not a bounded worker fix)

Two genuinely different directions, not mutually exclusive with the naming reconciliation:

1. **Extend the collector**: add real Hermes feed-ids for `JTO/USD`, `RAY/USD`, `WIF/USD`, `JUP/USD`, `USDC/USD` to
   `_PYTH_FEEDS` (verify each id resolves live against `hermes.pyth.network/v2/price_feeds?query=<SYM>` first — this
   file's own inline comments document 2 prior transcription-slip incidents for bSOL/JitoSOL where a
   wrong-but-well-formed id caused a whole-batch 404/400), AND reconcile `_write_oracle_rows`'s output `instrument_id`
   so newly-fetched SOL/JitoSOL/mSOL/bSOL rows are recognizable under (or migrated to) the seeder's
   `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD` key.
2. **OR prune the seeder's input**: if IS's PYTH-SOLANA catalogue enumerating JTO/RAY/WIF/JUP/USDC for `oracle_prices`
   was itself an over-broad seed (these tokens may not actually need on-chain oracle price collection), correct the IS
   catalogue / the seeder's scope back to the 7 symbols the collector supports.
3. **Either way**: reconcile the pre-existing 3-way `instrument_id` naming split (`{SYM}_USD` / `{sym}/usd` /
   `PYTH-SOLANA:SPOT_PAIR:{SYM}-USD`) onto one canonical form, so a future coverage read doesn't need hand-rolled
   cross-naming normalization (a real risk of a wrong verdict — an early pass at reconciling these families in-session
   produced a false "77 gap days" result before the bug was caught, because normalizing `PYTH-SOLANA:SPOT_PAIR:SOL-USD`
   and the real captured `sol/usd` row to the same key let the newer expected_unattempted row's later `written_at`
   incorrectly shadow the genuinely-captured older row in a last-writer-wins merge).

## Todos

- [ ] [OPERATOR] P2. Rule on the resolution direction: extend `_PYTH_FEEDS` (+ reconcile `instrument_id` naming) to
      genuinely support JTO/RAY/WIF/JUP/USDC, OR prune the IS PYTH-SOLANA catalogue/seeder scope back to the 7
      currently-fetchable symbols. Gates the two todos below. (repo: unified-trading-pm, decision only)
- [ ] [BACKEND] P2. Once ruled: implement the chosen fix. Extend path →
      `market-tick-data-service/market_tick_data_service/cli/handlers/_oracle_prices_constants.py` (`_PYTH_FEEDS`) +
      `_write_oracle_rows`'s instrument_id derivation. Prune path → `unified-api-contracts`/`instruments-service`
      PYTH-SOLANA capability declarations. (repo: market-tick-data-service or unified-api-contracts/instruments-service,
      per ruling)
- [ ] [DATA] P3. Reconcile the 3 coexisting oracle_prices/PYTH `instrument_id` naming conventions onto one canonical
      form so manifest reads don't need hand-rolled normalization to determine true per-feed coverage. (repo:
      market-tick-data-service, unified-api-contracts)

## Progress Log

- 2026-08-03 (slot-12, data_engineering craft): Discovered while verifying `defi_satellite_ao_dispatch_batch3-006`'s
  (C6) done-when after a SPOT backfill VM (`mtds-pyth-archive-20260803-070759`) was preempted mid-run and I re-checked
  the manifest to determine real remaining gap. Filed this issue; C6 itself proceeds on its own achievable scope (the
  7-symbol fetchable universe) with a Progress Log note pointing here for the structurally-separate gap.
