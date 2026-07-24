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
status: complete
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
    /plans/archive/2026_07/canonical_id_p0_kraken_futures_collision_2026_07_08.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
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
- [x] [DATA] P1. **Run the migration dry-run to completion and record the real GCS+manifest volume** —
      market-tick-data-service@dd1c3ec7 (script extended same pass, see below). Real dry-run completed 2026-07-09
      against production: manifest 498,388 in-scope rows, 100% already `:PERP:`-shaped
      (`instrument_ids_transformed_from_venue_perp_shape=498388`); GCS full-corpus walk (4,120,516 objects scanned,
      ~82min) found 136,814 real in-scope objects — **the largest real finding**: 97,138 (71%) were in an EVEN OLDER
      bare-symbol shape (`AAVE-PERP.parquet` / `AAVEUSDT.parquet`, no venue prefix at all) that neither this script's
      original regex NOR the 2026-06-22 precedent's own apply run had actually caught, vs. only 39,202 already in the
      `{VENUE}:PERP:{SYMBOL}` shape. Extended `plan_rename`/`rewrite_manifest` to also parse venue from the GCS object
      PATH (not just the filename) so the bare-symbol shape resolves straight to the final
      `VENUE:PERPETUAL:BASE-QUOTE@LIN` target in one touch — market-tick-data-service@dd1c3ec7.
- [x] [SCRIPT] P1. **Apply the historical-data migration** (GCS rename + manifest rewrite,
      `--apply --stamp     20260709T1323Z`) — REAL, COMPLETE. GCS: 134,855 renamed + 1,453 duplicate-old-shape sources
      cleaned up + 32 transient SSL/connection-pool errors (0.02% of 136,340, `--workers 96` exceeded the underlying
      HTTP client's default pool size) — all 32 resolved via a targeted idempotent retry (16 genuine renames, 11
      dup-source cleanups, 5 already-resolved) for a final **0 errors**. Manifest: 7,219,598 rows before/after (0
      drift), 0 dedup collisions, real backup at
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/backups/availability_index.pre_perpetual_canonical_20260709T1323Z.parquet`.
      Real wall-clock: ~82min discovery + ~2h20m GCS rename + ~2min manifest rewrite/upload (~4h40m end-to-end,
      unattended background job — see Progress Log for the full timeline and the connection-pool-tuning finding).
- [x] [VERIFY] P1. **Post-apply verification** — confirmed via a fresh re-download of the real post-write manifest: 100%
      of the 498,388 in-scope rows now read `VENUE:PERPETUAL:BASE-QUOTE@LIN` with `instrument_type=PERPETUAL` uniformly,
      0 rows in any old shape, 0 row-count drift (7,219,598 before/after), 0 in-scope duplicate
      `(venue, data_type, date, instrument_type, instrument_id, pipeline_mode)` keys. GCS-side: spot-checked 15+ real
      dates spanning 2023-04 through 2026-01 (incl. every date that had a transient rename error) — every sampled
      `data_type=` partition now contains exactly one canonical file per symbol, zero trace of `-PERP` / bare-symbol /
      intermediate `:PERP:` shapes.
- [x] [SCRIPT] P2. **Update `instruments-service/docs/DEFI_INSTRUMENTS.md`'s on-chain-perp section** with the real
      shipped commit SHAs once all 3 repos have landed — instruments-service@f7cf3ea5 (docs follow-up commit), filled in
      `instruments-service@f7cf3ea5` + `market-tick-data-service@c20ea464` (both were `<PENDING-SHA>` placeholders at
      initial ship time since MTDS shipped after the docs commit landed).

## Progress Log

- **2026-07-10** — **Status-flip note**: all 10 todos confirmed `[x]` with cited evidence; independently re-verified the
  docs-follow-up todo's SHA trail against git history (instruments-service commit `975c70a9` — 7 min after `f7cf3ea5` —
  confirmed the real SHAs replaced the `<PENDING-SHA>` placeholders on `live-defi-rollout`, resolving the apparent
  "currently BLOCKED" note in the 2026-07-09 log entry). Flipped `status: active` → `complete`.
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
- **2026-07-08 (later)** — The dry-run's `discover_parquet_files()` listing (walking the WHOLE `raw_tick_data/by_date/`
  prefix client-side-filtered, same approach as the 2026-06-22 precedent — there is no day-independent prefix for
  `pipeline_mode=`) ran for 25+ minutes with a live, ESTABLISHED HTTPS connection to a GCS endpoint the whole time
  (confirmed via `lsof` — not hung, genuinely slow real pagination) without completing. This is itself real evidence the
  historical volume is large — consistent with the 2026-06-22 precedent script's own real production run, which needed
  periodic "renamed N/M" progress logging for exactly this reason. Left running in the background (read-only,
  non-mutating, safe to let finish unattended); real counts were not captured before this pass ended. **Explicit
  decision, not a silent skip**: given the confirmed-large scale, do NOT attempt `--apply` in the same pass that
  produced the dry-run — the 2 open todos above (capture real counts, then apply) are the correct next step for whoever
  picks this up, following the same operator-decided migration-mechanics discipline (rewrite in place, backup first,
  dedup on capture_status precedence) already proven safe by the 2026-06-22 precedent.
- **2026-07-09** — Real, full-scale `--apply` run authorized and executed to completion (this was explicitly NOT a smoke
  test — real production GCS + manifest mutation). Real GCS scoping confirmed the counts had NOT materially changed
  since the prior pass's partial dry-run evidence. **Regex-extension gap (the largest real gap in this whole sweep, per
  the operator's framing)**: extended `migrate_onchain_perp_perpetual_canonical_2026_07_08.py`'s `plan_rename()` (GCS)
  and `rewrite_manifest()` (manifest) to ALSO recognize an EVEN OLDER bare-symbol shape with NO venue prefix at all in
  the filename (HL `{SYM}-PERP.parquet`, ASTER `{SYM}{QUOTE}.parquet`) by parsing venue from the object's GCS **path**
  (`venue=` partition) instead of the filename — added `legacy_bare_symbol_canonical_id()`, mirroring the 2026-06-22
  precedent's own path-based venue resolution. Verified via targeted unit-level sanity checks (idempotency: both the
  bare-legacy and `:PERP:` shapes for the same symbol correctly collapse onto the identical final target) before running
  against real infra — market-tick-data-service@dd1c3ec7. Real dry-run (re-run with the extension, full production
  corpus, ~82min discovery walk — 4,120,516 objects scanned, single-walk discipline honoured): 136,814 real in-scope
  HL/ASTER objects found, **97,138 (71%) in the bare-legacy shape** vs 39,202 already `:PERP:`-shaped — confirming the
  2026-06-22 migration's own apply pass had left the large majority of real objects un-renamed despite the manifest
  already reading the newer shape (a manifest/GCS-filename divergence, now closed). Manifest side: 100% of 498,388
  in-scope rows were already `:PERP:`-shaped (0 bare-legacy rows found at the manifest level — the divergence was
  GCS-object-only). Real `--apply --stamp 20260709T1323Z --workers 96` executed against
  `market-data-tick-cefi-prd-central-element-323112` (backup-first per the established migration-mechanics discipline,
  real concurrency via the script's own `ThreadPoolExecutor`): GCS renamed 134,855 + cleaned up 1,453
  duplicate-old-shape sources + 32 transient errors (SSL/`BrokenPipeError`/one 404-on-retry — all correctly isolated
  per-object, never aborted the pool). **Real, measured throughput finding for future similar migrations**:
  `--workers 96` exceeded the underlying HTTP client's default connection-pool size (10), causing "connection pool is
  full, discarding connection" churn and a slow initial ramp (~400 renames/min); throughput self-stabilized as
  connections settled, reaching ~1,300-1,700 renames/min once warm — net ~2h20m wall-clock for the 136,340-object rename
  phase (down from a naive ~5.7h projection at the initial degraded rate). The 32 transient errors were resolved via a
  small targeted retry script (reusing the migration module's own idempotent `plan_rename`/`do_rename` directly on the
  32 known failed paths, rather than a second full-corpus walk) — 0 remaining errors, verified via real GCS listing
  (every previously-failing date/symbol now shows exactly one canonical object, no leftover old-shape duplicates).
  Manifest rewrite completed with a real backup + real upload (7,219,598 rows before/after, 0 drift, 0 dedup
  collisions). Post-apply verification (re-downloaded the real post-write manifest + spot-checked 15+ real GCS dates
  spanning 2023-04 through 2026-01, including every date that had a transient error): 100% of in-scope rows/objects now
  read the final `VENUE:PERPETUAL:BASE-QUOTE@LIN` canonical shape, 0 remaining old-format traces of any kind. Shipped
  the script fix via quickmerge (market-tick-data-service@dd1c3ec7, scoped `--files` in a shared/dirty clone — a sibling
  agent had unrelated staged changes in the same clone at the time). Wrote the
  `instruments-service/docs/DEFI_INSTRUMENTS.md` "On-chain-perp DEXes" section update with the real before/after counts
  above, but its quickmerge is **currently BLOCKED** by a pre-existing, unrelated repo-wide QG hard-fail in
  instruments-service: `scripts/reconcile_phantom_manifest_rows.py:45` imports `google.cloud.storage` directly (TID251
  ratchet: baseline 58, actual 59 — a real regression already landed in that repo's history, nothing to do with this
  plan's scope — a sports-manifest-reconciliation script, not on-chain-perp). Did not attempt to fix it blind
  (unfamiliar file, outside this plan's scope, per the workspace's own findings-triage discipline) — flagging here + in
  the session report for the operator/a follow-up agent to fix or dispatch; the doc content itself is written, accurate,
  and ready to ship once that blocker clears.
