---
doc_type: plan
title:
  Canonicalize the 5 on-chain-perp venues' instrument_id from PERP shorthand to VENUE:PERPETUAL:BASE-QUOTE with real
  settlement currencies
summary: >-
  HYPERLIQUID/ASTER/PACIFICA-SOLANA/EXTENDED-STARKNET/LIGHTER-ZKSYNC all stored instrument_type=PERPETUAL as the field
  but embedded PERP (not PERPETUAL) in the instrument_id key, with an inconsistent base-quote shape per venue (bare
  symbol, raw concatenated exchange symbol, a fake "-PERP" quote, or already dash-normalized). Fixed to
  VENUE:PERPETUAL:BASE-QUOTE with the real per-venue settlement currency (confirmed live per venue) across
  instruments-service's 5 reference-data adapters, unified-api-contracts' ASTER normalize.py, and
  market-tick-data-service's live WS connectors + onchain-perp batch handler + catalog-reader fallback.
status: active
nature: notes
asset_group: [cefi]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer]
tags: [instrument-id, canonicalization, on-chain-perp, perp-vs-perpetual, bug-fix, p1]
related:
  [
    issues/instrument_id_format_canonicalization_2026_07_08.md,
    ../audit/results/canonical_instrument_id_audit_2026_07_08.md,
    canonical_id_p0_kraken_futures_collision_2026_07_08.md,
    canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
model_tier: sonnet-doable
thinking_tier: medium
source:
  "Findings 3+4 in instrument_id_format_canonicalization_2026_07_08.md, which had no dedicated fix plan (unlike finding
  7). Operator-decided target: VENUE:PERPETUAL:BASE-QUOTE for all 5 on-chain-perp venues, real settlement currency per
  venue TBD at implementation time for ASTER/PACIFICA-SOLANA/LIGHTER-ZKSYNC (HYPERLIQUID/EXTENDED-STARKNET pre-confirmed
  USD)."
---

> **Real, shipped fix** — not a target-state-only doc. All 3 repos' code changes landed 2026-07-08; the remaining open
> item is the historical batch tick-data GCS/manifest migration (scoped below, dry-run evidence attached, apply decision
> pending on the real volume found).

## Root cause

All 5 on-chain-perp reference-data adapters (`instruments-service/instruments_service/reference_data/adapters/cefi/`)
built `instrument_key` with the literal `PERP` shorthand instead of `PERPETUAL`, each with its own base-quote bug on
top:

- `hyperliquid.py:156` — `f"HYPERLIQUID:PERP:{name}"` (bare symbol, no quote at all).
- `aster.py:198` — `f"ASTER:PERP:{raw_symbol}"` (raw concatenated exchange symbol, e.g. `BTCUSDT`, no dash).
- `pacifica.py:75` — `f"PACIFICA-SOLANA:PERP:{sym}"` where `sym = f"{coin}-PERP"` (quote segment is literally the string
  `PERP`, not a currency).
- `extended.py:139` — `f"EXTENDED-STARKNET:PERP:{sym.upper()}"` (already dash-normalized with a real currency, e.g.
  `ETH-USD` — only the `PERP` shorthand was wrong here).
- `lighter.py:111` — `f"LIGHTER-ZKSYNC:PERP:{sym}"` (bare symbol, no quote at all).

The same `PERP` shorthand also leaked into 3 other places, all fixed in this pass:

- `unified-api-contracts/unified_api_contracts/external/aster/normalize.py` — ASTER's dedicated UAC normalize module (4
  functions: `normalize_aster_market`, `normalize_aster_liquidation` used `:PERP:`; `normalize_aster_ticker` /
  `normalize_aster_derivative_ticker` already said `PERPETUAL` but still embedded the raw concatenated symbol with no
  dash-quote — finding 4's gap, not finding 3's).
- `market-tick-data-service`'s LIVE (not blocked-credentials-stub) WS connectors for HYPERLIQUID (`hyperliquid_ws.py`,
  `hyperliquid_l2book_ws.py`, `hyperliquid_ticker_ws.py`) and ASTER (`aster_book_liq_ws.py`) independently constructed
  `HYPERLIQUID:PERP:{coin}` / `ASTER:PERP:{symbol}` — a real live=batch consistency risk if left unfixed (the 3 other
  on-chain-perp venues' live connectors — EXTENDED-STARKNET/LIGHTER-ZKSYNC/PACIFICA-SOLANA — already correctly parsed a
  `VENUE:PERPETUAL:` prefix; they're `BLOCKED-CREDENTIALS` stubs today so no live data flows yet, no fix needed there).
- `market-tick-data-service/cli/handlers/onchain_perp_batch_handler.py:478` — the batch handler's OWN
  `instrument_id = f"{venue}:PERP:{symbol}"` construction (the real, wired write path for HL/ASTER batch backfill — NOT
  the internal `hyperliquid_s3.py` / `onchain_perps/{hyperliquid,aster}_adapter.py` symbol vars, which are overwritten
  downstream by `_rows_to_canonical_df` before being persisted and are not consequential to the fix).
  `market-tick-data-service/engine/cefi_catalog_reader.py`'s `_canonical_cefi_id` FALLBACK function (only reached when
  the catalogue row is missing `instrument_id`, a rare path) had the same class of bug — no venue prefix at all, `-PERP`
  as a fake quote — fixed alongside for consistency.

## Real confirmed settlement currency per venue (2026-07-08)

| Venue               | Real settlement currency                                               | Verification method                                                                                                                                                                                     |
| ------------------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `HYPERLIQUID`       | USD                                                                    | Pre-confirmed earlier in this session (adapter's own `quote_asset="USD"` field; vault collateral is USDC, kept as `settle_asset`).                                                                      |
| `ASTER`             | Per-symbol real quote (USDT for 504/509, USD1 for 3, a bare "U" for 2) | Live `curl https://fapi.asterdex.com/fapi/v1/exchangeInfo` 2026-07-08 — real quoteAsset distribution counted directly, not assumed.                                                                     |
| `PACIFICA-SOLANA`   | USDC                                                                   | Live fetch of `docs.pacifica.fi/trading-on-pacifica/unified-margin` 2026-07-08: "Pacifica users' account's USDC balance, unrealized PnL, and spot holdings are margined together in a unified account". |
| `EXTENDED-STARKNET` | USD                                                                    | Pre-confirmed earlier in this session (`collateralAssetName="USD"` uniformly across markets, live API).                                                                                                 |
| `LIGHTER-ZKSYNC`    | USDC                                                                   | Live fetch of `docs.lighter.xyz/trading/multi-asset-margin` 2026-07-08: "Portfolio Balance is the USDC value of the account including unrealized PnL on perpetual positions".                           |

ASTER is deliberately NOT hardcoded to one quote currency in the adapter fix — the real per-symbol `quote_asset` already
parsed from the live `exchangeInfo` response is used directly, so the ~1% of non-USDT-quoted symbols (USD1, a bare "U")
get their own real quote, not a wrong blanket USDT.

## Before → after (real samples)

- `HYPERLIQUID:PERP:BTC` → `HYPERLIQUID:PERPETUAL:BTC-USD`
- `ASTER:PERP:BTCUSDT` → `ASTER:PERPETUAL:BTC-USDT`
- `PACIFICA-SOLANA:PERP:SOL-PERP` → `PACIFICA-SOLANA:PERPETUAL:SOL-USDC`
- `EXTENDED-STARKNET:PERP:ETH-USD` → `EXTENDED-STARKNET:PERPETUAL:ETH-USD` (PERP→PERPETUAL only; base-quote was already
  correct)
- `LIGHTER-ZKSYNC:PERP:BTC` → `LIGHTER-ZKSYNC:PERPETUAL:BTC-USDC`

## Downstream consumer check (task item 4 — breaking-vs-corrective diligence)

Grepped the workspace for `:PERP:` construction sites (not just references) before shipping:

- **instruments-service**: no test hardcodes an old-format assertion for these 5 adapters (`test_hyperliquid_adapter.py`
  / `test_aster_adapter.py` / `test_lighter_extended_pacifica_coverage.py` don't assert exact `instrument_key` strings).
  `scripts/build_instrument_catalogue.py`'s fixture data (`LIGHTER-ZKSYNC:PERP:BTC-USDC` etc., lines 424-450) is inert
  test data for venue/chain-split detection logic, not an assertion tied to the adapters — left as-is (out of
  proportionate scope; a pure fixture staleness, not a functional dependency).
- **unified-api-contracts**: no dedicated ASTER normalize test exists; `test_instrument_id_patterns.py`'s
  `PERPETUAL_PATTERN` test documents strategy-service's OWN `@LIN@VENUE` position-id convention (a different,
  already-decided, unrelated format) — not affected.
- **market-tick-data-service**: `onchain_perp_batch_handler.py`'s `_catalogue_symbols_for_venue` extracted the catalog
  `instrument_id`'s last colon-segment and used it VERBATIM as the venue-native fetch symbol
  (`downloader.fetch_trades(symbol, ...)` for HL, `adapter.fetch_trades(symbol, ...)` for ASTER) — this WOULD have
  broken real fetches once the catalog started emitting a dash-quote segment (HL's API wants a bare coin; ASTER's API
  wants the concatenated exchange symbol, neither wants a dash). Fixed with a venue-aware
  `_canonical_segment_to_native_symbol()` / `_native_symbol_to_instrument_id()` round-trip pair so the real fetch symbol
  is correct AND the written `instrument_id` stays fully canonical (not a naive concat). Also found + fixed (in the same
  file, adjacent) a real pre-existing bug: `AsterBookWSConnector` inherits `BinanceFuturesBookWSConnector.stream()`
  unmodified, which hardcodes `venue="BINANCE-FUTURES"` in its shared parser — ASTER's live `book_snapshot_5` ticks were
  mislabeled as BINANCE-FUTURES data. Fixed via a non-invasive `stream()`-override re-tag (`_retag_aster_book_tick`) in
  `aster_book_liq_ws.py` rather than editing the shared Binance connector file (owned by a sibling this round).
- Corrective, not breaking: no real production consumer depended on the OLD `PERP`/bare-quote shape surviving — the
  catalog is regenerated fresh from each adapter's live REST call on every pipeline run (no historical dimension to the
  reference-data catalog itself), and the batch/live tick-data write paths were updated in the same pass to stay
  consistent with the new catalog shape.

## Todos

- [x] [DATA] P1. **Implement `VENUE:PERPETUAL:BASE-QUOTE` in all 5 instruments-service adapters**, real per-venue
      settlement currency (confirmed live, see table above) — instruments-service@f7cf3ea5 (`hyperliquid.py`,
      `aster.py`, `pacifica.py`, `extended.py`, `lighter.py`).
- [x] [DATA] P1. **Fix the same PERP shorthand in unified-api-contracts' ASTER normalize.py** (4 functions:
      `normalize_aster_market`, `normalize_aster_liquidation`, `normalize_aster_ticker`,
      `normalize_aster_derivative_ticker`) + a shared `_aster_canonical_symbol()` quote-splitter helper —
      unified-api-contracts@58a03793.
- [x] [DATA] P1. **Fix MTDS's live (non-stub) WS connectors for HYPERLIQUID + ASTER** to stop embedding the PERP
      shorthand, keeping live=batch consistent — `hyperliquid_ws.py`, `hyperliquid_l2book_ws.py`,
      `hyperliquid_ticker_ws.py`, `aster_book_liq_ws.py` — market-tick-data-service@c20ea464. Also fixed the
      pre-existing ASTER book_snapshot_5 → BINANCE-FUTURES mislabeling bug discovered while fixing this (see "Downstream
      consumer check" above).
- [x] [DATA] P1. **Fix `onchain_perp_batch_handler.py`'s own instrument_id construction + catalogue-driven symbol
      enumeration** (the real wired batch write path) and `cefi_catalog_reader.py`'s `_canonical_cefi_id` fallback —
      market-tick-data-service@c20ea464.
- [x] [VERIFY] P1. **Confirm no downstream consumer breaks** — grepped + read every `:PERP:` construction/consumption
      site across the workspace within the 3 permitted repos; documented findings above (batch handler symbol
      round-trip + the ASTER book mislabeling bug, both fixed).
- [x] [SCRIPT] P1. **Write the historical-data migration script** for the raw batch tick-data GCS objects + the
      availability manifest (mirrors the proven `migrate_onchain_perp_canonical_instrument_id.py` 2026-06-22 precedent)
      — `market-tick-data-service/scripts/migrate_onchain_perp_perpetual_canonical_2026_07_08.py`. DRY-RUN is the
      default; `--apply` requires `--stamp`.
- [ ] [DATA] P1. **Run the migration dry-run to completion and record the real GCS+manifest volume**, then decide
      apply-now vs. file as a dedicated backfill todo based on the real count (per the operator's migration-mechanics
      decision: always rewrite in place, never silently skip — this todo tracks executing that decision once the real
      volume is known). Dry-run was in progress at end of this pass — see Progress Log for partial evidence; the exact
      renamed/skipped/manifest-row counts were not yet fully captured when this plan was filed.
- [ ] [SCRIPT] P1. **Apply the historical-data migration** (GCS rename + manifest rewrite, `--apply --stamp <stamp>`)
      once the dry-run counts are reviewed, with a backup of the pre-migration manifest index (the script does this
      automatically).
- [ ] [VERIFY] P1. **Post-apply verification** — confirm 0 remaining `:PERP:`-shaped instrument_id rows for
      HYPERLIQUID/ASTER in the manifest + GCS object names, no row-count drift, no new duplicate `instrument_id`
      introduced by the dedup/merge step.
- [x] [SCRIPT] P2. **Update `instruments-service/docs/DEFI_INSTRUMENTS.md`'s on-chain-perp section** with the real
      shipped commit SHAs once all 3 repos have landed — instruments-service@f7cf3ea5 (docs follow-up commit), filled in
      `instruments-service@f7cf3ea5` + `market-tick-data-service@c20ea464` (both were `<PENDING-SHA>` placeholders at
      initial ship time since MTDS shipped after the docs commit landed).

## Progress Log

- **2026-07-08** — Filed + implemented in the same pass. Confirmed real settlement currencies live for
  ASTER/PACIFICA-SOLANA/LIGHTER-ZKSYNC (HYPERLIQUID/EXTENDED-STARKNET were already confirmed USD earlier this session):
  ASTER via `fapi.asterdex.com/fapi/v1/exchangeInfo` (509 real perp symbols, 504 USDT / 3 USD1 / 2 bare "U" — used the
  real per-symbol quote in the fix rather than hardcoding USDT); PACIFICA-SOLANA via
  `docs.pacifica.fi/trading-on-pacifica/unified-margin` (USDC-denominated unified margin, confirmed via WebFetch);
  LIGHTER-ZKSYNC via `docs.lighter.xyz/trading/multi-asset-margin` (USDC portfolio-balance quote, confirmed via WebFetch
  — Lighter's own public REST `/orderBookDetails` only exposes an opaque numeric `quote_asset_id`, always `0`, not a
  currency string, so the docs were the real source here, not the API response). Shipped code fixes to all 5
  instruments-service adapters, UAC's ASTER normalize.py (4 functions), and 3 MTDS files (the 4 live WS connectors + the
  batch handler + the catalog reader fallback). Discovered and fixed 2 adjacent real bugs while doing so: (1) the batch
  handler's catalogue-driven symbol enumeration would have broken real HL/ASTER fetches once the catalog started
  emitting a dash-quote segment (fixed via a venue-aware native-symbol round-trip); (2) ASTER's live `book_snapshot_5`
  WS ticks were being mislabeled as BINANCE-FUTURES data (pre-existing, unrelated to this finding, found because the
  shared Binance connector hardcodes the PERP shorthand + venue string — fixed via a non-invasive re-tag rather than
  touching the shared/sibling-owned Binance file). Wrote the historical-data migration script mirroring the proven
  2026-06-22 precedent; dry-run was in progress against the real `market-data-tick-cefi-prd-central-element-323112`
  bucket at the time this doc was filed (a full-corpus GCS listing takes several minutes on real production volume) —
  real counts + the apply-vs-defer decision are the 2 remaining open todos above, not silently dropped.
  instruments-service's quickmerge was transiently blocked by a live sibling agent's concurrent uncommitted WIP in the
  shared `unified-api-contracts` clone (protected per the workspace's inherited-dirty-WIP liveness rule, not
  force-pushed through) — retried once the sibling's changes landed.
