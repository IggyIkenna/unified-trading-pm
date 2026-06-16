---
type: audit-result
title: CeFi Master — Audit Result 2026-06-03 (acquisition-mechanics pass)
epic: cefi_master
auditor: harsh + claude (opus-4-8, 1M)
date: 2026-06-03
status: complete
instructions_ref: plans/audit/instructions/cefi_master_audit_instructions.md
also_covers:
  - plans/audit/instructions/instruments_master_audit_instructions.md
  - plans/audit/instructions/mtds_mdps_master_audit_instructions.md (item k — new)
  - plans/audit/instructions/batch_live_symmetry_master_audit_instructions.md (item k — new)
  - plans/audit/instructions/features_and_ml_master_audit_instructions.md
  - plans/audit/instructions/strategy_master_audit_instructions.md
dimension: acquisition-mechanics + batch/live wiring + downstream propagation (CODE-VERIFIED)
not_covered: data-state corpus coverage (CF-1…12 data-state, per-venue captured%) — requires prod GCS/manifest reads
---

# CeFi Master — Audit Result 2026-06-03 (acquisition-mechanics pass)

Sibling of `defi_master_audit_2026_06_03.md`. Same operator framing + same code-verified method (2 sub-agent passes: 4a
instruments+MTDS-tick, 4b MDPS→features-delta-one→perp-archetype), key findings spot-verified by the auditor.

## Adversarial verification (2026-06-03) — findings reclassified

Independent adversarial-refutation pass; the fix plan `plans/active/data_pipeline_acquisition_remediation_2026_06_03.md`
acts only on survivors:

- **CONFIRMED (fix-now)**: funding-feature name/unit mismatch (P1 — no alias layer exists; `basis_perp` is the outlier
  vs sibling `staked_basis`); non-HL CeFi trades-only live / no live book+ticker (P1).
- **PARTIAL**: CeFi `source=""` — manifest-column half CONFIRMED (the `record_captured_from_counts` path sets no
  `source=`), per-row-parquet half **REFUTED** (cefi IS in `SOURCE_PRIORITY` → per-row stamp works); the genuine gap is
  owned by `data_source_provenance_all_asset_groups_2026_06_01.md`. `funding_oi` `need_data` = KNOWN-TRACKED
  (`features_registry_status_versioning_2026_05_28.md`).
- **REFUTED (out of scope)**: MTDS `TardisAdapter` "self-discovers universe" — `download_batch` uses IS-catalog
  `instrument_ids`; `availableSymbols` is a separate validation method, not the download path.

## Verdict by stage

| Stage                            | Verdict          | Headline                                                                                                                                        |
| -------------------------------- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| CeFi instrument acquisition (IS) | **GREEN**        | batch→Tardis `/instruments`, live→CCXT `load_markets()`; base/quote/instrument_type populated; HL/Aster dedicated adapter both modes.           |
| MTDS CeFi tick acquisition       | **AMBER**        | Tardis-CSV batch solid (sem=16, retry, SM auth, aiohttp); **live WS = trades only for non-HL venues** (book/derivative_ticker live is HL-only). |
| MDPS CeFi candles                | **GREEN**        | 6 registered adapters; LOCF/no-NaN + honest-absence correct; `derivative_ticker` preserves funding/mark/index.                                  |
| features-delta-one CeFi          | **AMBER/RED**    | funding/basis MATH exists but `funding_oi` is `_placeholder`/`need_data` (awaiting backfill); `realized_vol_*` registered+produced.             |
| strategy perp archetypes         | **RED (latent)** | name/unit mismatch on the funding feature → carry_basis_perp can't resolve it; dispersion needs unregistered per-venue funding.                 |

## Acquisition registry (GAP-1, mtds item k) — condensed

- **Batch (all Tardis venues)**: `TardisAdapter.download_batch` →
  `datasets.tardis.dev/v1/{exchange}/{data_type}/{Y}/{M}/{D}/{symbol}.csv.gz` (`tradfi/tardis_adapter.py:537`);
  venue→exchange via UAC `VenueMapping`; `asyncio.Semaphore(16)` (`tardis_adapter.py:182`); retry/backoff `:746`; SM
  `tardis-api-key`; aiohttp. Venues: Binance(spot/fut), Bybit(spot/linear), OKX(spot/swap/fut), Deribit
  (+options_chain/futures_chain grouped CSVs `:942`), Coinbase-spot, Upbit, Kraken(spot/fut).
- **Live (per-venue WS, trades)**: connectors in `market-tick-data-service/.../live/connectors/` — binance_spot_ws:23,
  binance_futures_ws:42, bybit_ws:37, bybit_spot_ws:23, okx_ws:36, okx_spot_ws:23, deribit_ws:38, coinbase_spot_ws:34,
  kraken_spot_ws:33, kraken_futures_ws:32. **Only Hyperliquid has live book + ticker** (`hyperliquid_l2book_ws:59`,
  `hyperliquid_ticker_ws:84`).
- **Hyperliquid**: batch = AWS S3 (`hl-mainnet-node-data` / `hyperliquid-archive`, `hyperliquid_s3.py:10-12`, SM
  `aws-hyperliquid-s3`); live = `wss://api.hyperliquid.xyz/ws`. **Aster**: batch = REST `fapi.asterdex.com/fapi/v1` (NOT
  Tardis); live = `wss://fstream.asterdex.com/ws` — **NOT a stub** (`aster_ws:48` parses). **Perp funding handler** =
  DEX-perp only (hyperliquid/aster/gmx/pacifica/lighter, `perp_funding_handler.py:95`); CeFi-venue funding arrives as
  Tardis `derivative_ticker` (rename of `market_stats`, `tardis_adapter.py:1032`).

## Checklist results (cefi_master a,b,d,e,i)

- (a) `classify_venue_error()` — PRESENT on Tardis paths (IS `tardis.py:693,742`; MTDS
  `tardis_adapter.py:155,472,523,918`). Per-WS-connector error handling is centralised in `live/websocket_runner.py`
  (not individually verified).
- (b) `ADAPTER_FETCH_FAILED` — emitted on Tardis error paths (IS `tardis.py:704,752`; MTDS `tardis_adapter.py:474,525`).
- (d) IS→MTDS — **DEVIATION**: MTDS `TardisAdapter` does its OWN instrument discovery via Tardis
  `/v1/exchanges/{exchange}` `availableSymbols` (`tardis_adapter.py:300,306`) rather than reading the universe from
  instruments-service `InstrumentRecord`. Venue→exchange map is UAC-sourced (OK); the discovery-bypass is the contract
  gap.
- (e) batch/live parity — spot/perp `trades` have both modes; **book_snapshot_5 + derivative_ticker live is HL-only**
  (non-HL CeFi has batch only).
- (i) `source="tardis"` — **RED**: per-row parquet stamping via `stamp_available_at_cefi_tick` silently skips on
  KeyError (`orchestrator.py:1309-1313`); the manifest `record_captured_from_counts` callsites pass no `source=`
  (`orchestrator.py:3084-3102`). Only TradFi enforces mandatory source. Matches existing cefi item (i) RED +
  `data_source_provenance_all_asset_groups_2026_06_01.md`.

## Gap items (dedup against `plans/active/` + `issues/` before filing)

- [ ] [BATCH-LIVE] P1. Non-HL CeFi `book_snapshot_5` + `derivative_ticker` have **no live WS connector** (only `trades`
      live; only Hyperliquid has live book+ticker) — live perp mark/funding (derivative_ticker) is absent for
      Binance/Bybit/OKX/Deribit/Kraken/Coinbase. Add live connectors or record an accepted-divergence register entry
      (batch_live item k). — parent_epic: cefi_master
- [ ] [CONTRACT] P1. MTDS `TardisAdapter` self-discovers the instrument universe from Tardis `/v1/exchanges`
      (`tardis_adapter.py:300,306`) instead of reading instruments-service `InstrumentRecord` — IS→MTDS contract
      deviation (venue→exchange map is UAC-sourced, but the universe should come from IS). — parent_epic:
      instruments_master
- [ ] [SOURCE-BLANK] P1. CeFi manifest rows don't stamp `source="tardis"` at `record_captured`
      (`orchestrator.py:3084-3102`); per-row parquet stamp silently skips on KeyError (`:1309-1313`). CF-4 RED; matches
      cefi item (i). — parent_epic: cefi_master (rider: data_source_provenance_all_asset_groups_2026_06_01)
- [ ] [CODE-BUG] P1. Funding-feature name/unit mismatch: `carry_basis_perp` consumes `funding_rate_annualised_bps`
      (`basis_perp.py:67`) but `FundingOI` emits `funding_rate_annualized` = `rate*3*365` fraction (`funding_oi.py:84`)
      — spelling + `_bps` suffix + unit (bps vs fraction) all diverge → silent no-trade when data lands. Align the
      producer to emit `funding_rate_annualised_bps` in bps. — parent_epic: features_and_ml_master (+ strategy_master)
- [ ] [L3-GAP] P2. funding/basis features computed by FundingOI/FuturesBasis but not registered with `formula_version`
      (`funding_oi` = `_placeholder`/`need_data` `registry.py:18148`; futures_basis registers only OHLCV proxies) — not
      backfilled into `features-delta-one-cefi-*`. NOTE: `need_data` is a KNOWN awaiting-backfill state, not accidental;
      register + backfill once the funding feed is wired. — parent_epic: features_and_ml_master
- [ ] [L3-GAP] P2. `funding_rate_dispersion` needs per-venue cross-sectional `funding_rate_<venue>`/`mid_price_<venue>`
      (`price_dispersion.py:86-87`); base per-venue funding feature is the unregistered one above (widening is
      strategy-side). — parent_epic: features_and_ml_master
- [ ] [BATCH-LIVE] P2. Upbit has no live WS connector (batch-only). — parent_epic: cefi_master
- [ ] [L3-GAP] P2. `funding_rate_apy_bps` has zero producers in features-service (consumed by carry_staked_basis hedge
      leg) — cross-ref the same DeFi-side finding; tracked plan `funding_rate_apy_bps_multi_venue_2026_06.md`. —
      parent_epic: features_and_ml_master

## Aligned / positive (no action)

Tardis batch acquisition solid (sem=16, retry/backoff, SM auth, aiohttp); CCXT live instrument discovery
(`load_markets()`); base/quote/instrument*type populated; `classify_venue_error` + `ADAPTER_FETCH_FAILED` on Tardis
paths; MDPS 6 cefi candle adapters with LOCF/no-NaN + honest-absence + `derivative_ticker` funding/mark/index preserved;
features-delta-one + strategy **batch=live parity intact** (same `OrchestrationService`, no `if mode=="live"` in signal
logic); `realized_vol*\*` registered+produced+consumed; Aster live WS is real (not a stub).

## What was NOT covered

Data-state corpus coverage (CF-1…12 data-state, per-venue captured% with IS∩UAC denominators); exhaustive
per-WS-connector error-handling read; runtime confirmation of the non-HL live book/ticker absence against a live
registry dump.

## Archive condition

Archives when all gap items above are `- [x]` in their parent active plans.
