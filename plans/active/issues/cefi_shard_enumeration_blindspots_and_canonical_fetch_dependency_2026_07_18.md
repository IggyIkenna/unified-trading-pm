---
doc_type: issue
title:
  CeFi smoke matrix under-declares the real shard surface (8 live cells never enumerated), and targeted re-fetch breaks
  for venues already migrated to canonical instrument-id naming
summary:
  Two findings from building the Tardis-only pipeline smoke run. (1) ENUMERATION BLIND SPOTS — the UAC registry lists
  under-declare what is actually captured. OKX-FUTURES and OKX-SWAP carry captured PROD data but are absent from
  VENUES_BY_ASSET_GROUP['cefi'], and volatility_index is captured on DERIBIT but absent from
  DATA_TYPES_BY_ASSET_GROUP['cefi'] — 8 live (venue, data_type) cells the smoke matrix had NEVER enumerated, so it could
  report a clean sweep while never testing them. (2) CANONICAL-FETCH DEPENDENCY — the downloader's --instrument-ids
  filter matches RAW venue-native symbols EXACTLY (no substring or underlying expansion), with no canonical-to-raw
  resolution. Once a venue's PROD objects are renamed to canonical ids, any targeted per-instrument fetch of that venue
  silently returns 0 rows. Measured 2026-07-18 — 8 of 46 provable Tardis cells are already canonical-only
  (BITFINEX-FUTURES all 4 data_types, BYBIT-SPOT 2, COINBASE-FUTURES 2) and cannot be force-fetched at all.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [cefi, tardis, smoke-test, enumeration, canonical-id, migration, coverage, big-finding]
related:
  [
    tardis_silent_shard_upload_drop_on_429_burst_2026_07_17.md,
    tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md,
  ]
created: 2026-07-18
source:
  - Fell out of building the Tardis-scoped smoke run (--tardis-only) and reconciling why every force-leg reported a
    false no_parquet failure.
assigned_vm: NA
assigned_role: data_engineering
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
parent_epic: cefi_master
execution_scope: local-only
drift_direction: advance-code
last_updated: 2026-07-18
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# CeFi shard-enumeration blind spots + canonical-fetch dependency

## Finding 1 — the UAC lists under-declare the real shard surface (P1, coverage)

Enumerating the smoke matrix from `VENUES_BY_ASSET_GROUP` x `DATA_TYPES_BY_ASSET_GROUP` misses cells that demonstrably
hold captured PROD data:

| Missing from                        | Cells                                                                                                                             |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `VENUES_BY_ASSET_GROUP['cefi']`     | `OKX-FUTURES` (book_snapshot_5, derivative_ticker, trades), `OKX-SWAP` (book_snapshot_5, derivative_ticker, liquidations, trades) |
| `DATA_TYPES_BY_ASSET_GROUP['cefi']` | `DERIBIT/volatility_index`                                                                                                        |

**8 live cells** were therefore never enumerated by any matrix driven off those lists — the sweep reports a clean pass
while never having tested them. Note the enumeration DOES carry `OKX` (bare), which has captured data on exactly one day
ever, while the real OKX volume lives under the `-SWAP`/`-FUTURES`/`-SPOT` suffixes.

**Mitigated (not fixed) in the smoke check** by `market-tick-data-service@c0d6027c` (`_augment_with_observed_cells`):
the runner unions in every `(venue, data_type)` the PROD index shows as captured. That fixes the smoke matrix but NOT
the underlying registry under-declaration — any other consumer enumerating from the UAC lists has the same blind spot.

**Recommended**: reconcile the UAC registry against observed PROD capture (add the OKX suffixed venues +
`volatility_index`, or document why they are intentionally excluded).

## Finding 2 — targeted re-fetch breaks on canonical-migrated venues (P1, migration dependency)

`--instrument-ids` matches **raw venue-native symbols exactly** — no substring match, no underlying expansion, no
canonical-to-raw resolution. Evidence: `--instrument-ids ETH` (a chain root from the manifest) produced
`0 venues ok, 0 total records`; `--instrument-ids ADAUSDT` (raw) fetched **966,429 records** and wrote correctly.

The raw-to-canonical instrument-id migration renames PROD objects from `ADAUSDT.parquet` to
`BINANCE-FUTURES:PERPETUAL:ADA-USDT@LIN.parquet`. **Once a venue is migrated, there is no raw symbol left to pass**, so
any targeted per-instrument fetch of that venue silently fetches nothing. Measured 2026-07-18 across the 46 provable
Tardis cells:

- **RAW-named (targeted fetch works)**: 38 cells
- **CANONICAL-only (targeted fetch returns 0 rows)**: 8 cells — `BITFINEX-FUTURES` (all 4 data_types), `BYBIT-SPOT`
  (book_snapshot_5, trades), `COINBASE-FUTURES` (book_snapshot_5, trades)

This is a **dependency the migration must satisfy**, not a smoke-test defect: the downloader needs to accept canonical
ids (or resolve canonical to raw) BEFORE the remaining venues are migrated — otherwise targeted re-fetch and
per-instrument backfill repair silently no-op on migrated venues, and the failure mode is a silent 0 rows rather than an
error.

**Owner**: the raw-to-canonical migration plan (separate agent/plan, in flight). This doc exists so that dependency is
explicit and does not have to be re-discovered.

## Also worth knowing — manifest verdicts are unreliable mid-migration

The smoke check verifies a manifest row keyed on the sampled RAW symbol while the writer records the row under the
CANONICAL id, so `manifest_status_invalid:no_matching_row` appears even when the fetch and write both succeeded. Read
the VM `run.log` (`Processed date=...: N venues ok, 0 failed, R total records`) as ground truth until the migration
lands.
