---
doc_type: issue
title: >-
  6 live CeFi spot WS connectors build non-canonical instrument_ids (bare "SPOT" ITYPE token, never "SPOT_PAIR") —
  escalated out of a small-drift census finding once the true blast radius was found
summary: >-
  While fixing `cefi_sports_prediction_first_census_small_drift_2026_07_30.md`'s item 2 ("instrument_type=spot
  lowercase, 4,923 rows"), root-causing the 3 named live WS connectors revealed the actual defect is much larger and
  more foundational than a stray content-dict field: all 6 live CeFi spot connectors build their `instrument_id` (and
  therefore the parquet FILENAME, since cefi's single-instrument shard filename IS the full canonical id) with a bare
  `SPOT` type token (`f"{VENUE}:SPOT:{symbol}"`), never the canonical `SPOT_PAIR` — empirically confirmed non-canonical
  via `is_canonical_instrument_id()` (`BINANCE-SPOT:SPOT:BTC-USDT` → False, `BINANCE-SPOT:SPOT_PAIR:BTC-USDT` → True).
  Several connectors additionally emit a non-hyphenated BASE-QUOTE symbol (e.g. Binance's bare `SOLUSDT`), a second,
  independent canonicality defect on the same id. This is an ACTIVE, ongoing writer defect (not historical residue) —
  every new live tick from these connectors mints another non-canonical id. Deliberately NOT fixed in the same pass as
  the narrow small-drift item: fixing it correctly requires (1) a full audit of the true non-canonical population across
  all 6 venues (symbol-hyphenation is a SEPARATE dimension from the ITYPE-token bug and wasn't measured), (2)
  coordinated changes to the `instrument_id`/filename construction across 6 files (a foundational,
  downstream-reader-facing value, unlike the narrow `instrument_type` field originally scoped), and (3) new regression
  test coverage proving both dimensions fixed without silently breaking any reader keyed on the OLD id shape. Rushing a
  partial fix (e.g. correcting only the path/manifest `instrument_type` axis while leaving the filename/id itself
  unfixed) would have made things WORSE by making the manifest and the actual object filename disagree with each other.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [canonicalisation, instrument-id, live-writer, cefi, spot, id-form, census, data-correctness]
related:
  [
    cefi_sports_prediction_first_census_small_drift_2026_07_30,
    data_pipeline_reconciliation_skill_2026_07_20,
    canonical_path_oracle_blind_to_filename_stem_2026_07_20,
  ]
created: 2026-07-30
last_updated: 2026-07-30
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "operator request 2026-07-30 — root-causing cefi_sports_prediction_first_census_small_drift_2026_07_30.md item 2 while
  fixing the small-drift census findings"
resolved_by:
  "market-tick-data-service@46e85d94 — all 8 live CeFi spot venues (12 files) fixed to SPOT_PAIR + canonical BASE-QUOTE
  hyphenation; scope corrected from the originally-filed 6 files to 8 venues after a full re-audit found
  BITGET-SPOT/BYBIT-SPOT/KRAKEN-SPOT were live-registered but missed by the original census + file table; 2 additional
  canonicality defects found + fixed beyond the originally-scoped ITYPE-token + hyphenation dimensions (Kraken's `/`
  wire separator, Upbit's reversed QUOTE-BASE market-code order); new `derive_spot_pair_symbol()` helper in
  tardis_margin_marker.py is the single insertion point; full test suite green (7620 passed); downstream-reader audit
  found zero hardcoded-old-shape readers. Historical per-venue manifest row counts NOT measured (documented gap, see
  todo 1) — the code fix stops the ongoing writer defect regardless."
depends_on: []
---

# CeFi live spot connectors build non-canonical instrument_ids

## 1. Measured evidence

`unified_api_contracts.canonical._partition_path_canonicality.is_canonical_instrument_id`, called directly:

| candidate id                      | result                                            |
| --------------------------------- | ------------------------------------------------- |
| `BINANCE-SPOT:SPOT:BTCUSDT`       | `False`                                           |
| `BINANCE-SPOT:SPOT_PAIR:BTCUSDT`  | `False` (still fails — missing BASE-QUOTE hyphen) |
| `BINANCE-SPOT:SPOT:BTC-USDT`      | `False`                                           |
| `BINANCE-SPOT:SPOT_PAIR:BTC-USDT` | `True`                                            |

`SPOT_PAIR` is the ONLY canonical ITYPE token for cefi spot pairs — `SPOT` is never canonical regardless of symbol
format. This matches the dominant, correct value already observed in the manifest census (`SPOT_PAIR`: 1,963,329 cefi
rows) — confirming `SPOT_PAIR` is the right target, not a guess.

## 2. RE-AUDITED 2026-07-30 — true scope is 8 venues / 12 files, not 6

The original 6-file table below (§ 2a) was itself incomplete — a single grep pass on the 3 venues the census implicated,
plus 3 more named but unverified. A full repo-wide grep for `:SPOT:` id-construction and
`register_ws_feed_connector(venue=...)` enumeration turned up **3 additional live-registered spot venues the original
census never saw at all** (BITGET-SPOT, BYBIT-SPOT, KRAKEN-SPOT — none appear anywhere in the small-drift census this
issue was escalated from), plus **2 more files for venues already named** (Binance and OKX each have a separate
trades-connector file in addition to the book connector originally found; Upbit's book connector was likewise missed).

**Per-venue confirmed findings** (live/dead classification, symbol shape, fix applied):

| Venue         | File(s)                                                         | Live?                                                           | Wire symbol shape                                                                                                  | Defect(s) found                                                                                                                                                                                                                                                                                                                  |
| ------------- | --------------------------------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| BINANCE-SPOT  | `binance_spot_book_ws.py` (book), `binance_spot_ws.py` (trades) | Yes (`register_ws_feed_connector`)                              | Concatenated, e.g. `SOLUSDT`                                                                                       | ITYPE token + missing hyphen                                                                                                                                                                                                                                                                                                     |
| COINBASE-SPOT | `coinbase_book_ws.py` (book), `coinbase_spot_ws.py` (trades)    | Yes                                                             | Already `BASE-QUOTE`, e.g. `SOL-USD`                                                                               | ITYPE token only                                                                                                                                                                                                                                                                                                                 |
| OKX-SPOT      | `okx_spot_book_ws.py` (book), `okx_spot_ws.py` (trades)         | Yes                                                             | Already `BASE-QUOTE` (inherited from OKX-SWAP instId minus `-SWAP`)                                                | ITYPE token only                                                                                                                                                                                                                                                                                                                 |
| UPBIT         | `upbit_book_ws.py` (book), `upbit_spot_ws.py` (trades)          | Yes                                                             | Hyphenated but **QUOTE-BASE** (`KRW-BTC`)                                                                          | ITYPE token **+ reversed base/quote order** (real 3rd defect, confirmed against `unified-api-contracts`' own canonical_id_builder test fixture `("upbit", SPOT_PAIR, "WAXP-KRW", ...)` and instruments-service's batch-side `_resolve_base_quote` Upbit inversion — both already treat `BASE-QUOTE` as canonical for this venue) |
| BITFINEX-SPOT | `bitfinex_spot_ws.py`                                           | Yes                                                             | Concatenated, e.g. `BTCUSD` (legacy 3-char pseudo-quotes `UST`/`UDC` also possible)                                | ITYPE token + missing hyphen. Shares its parser with `bitfinex_futures_ws.py` (PERPETUAL) — fix gated to `instrument_type == "SPOT_PAIR"` only                                                                                                                                                                                   |
| BITGET-SPOT   | `bitget_spot_ws.py`                                             | Yes — **NOT in the original 6-file table or the census at all** | Concatenated, e.g. `BTCUSDT`                                                                                       | ITYPE token + missing hyphen. Shares its parser with `bitget_futures_ws.py` (PERPETUAL) — fix gated to `instrument_type == "SPOT_PAIR"` only                                                                                                                                                                                     |
| BYBIT-SPOT    | `bybit_spot_ws.py`                                              | Yes — **NOT in the original 6-file table or the census at all** | Concatenated, e.g. `BTCUSDT`                                                                                       | ITYPE token + missing hyphen                                                                                                                                                                                                                                                                                                     |
| KRAKEN-SPOT   | `kraken_spot_ws.py`                                             | Yes — **NOT in the original 6-file table or the census at all** | **`/`-separated** (Kraken v2 API), e.g. `BTC/USD` — a THIRD kind of defect (wrong separator, not missing/reversed) | ITYPE token + wrong separator                                                                                                                                                                                                                                                                                                    |

**Fix mechanism**: a new `derive_spot_pair_symbol(venue, raw_symbol) -> str` in
`market_tick_data_service/market_interface/adapters/cefi/tardis_margin_marker.py` is the single insertion point every
fixed connector calls — glued-symbol venues split on the longest matching quote suffix (BUSD/TUSD checked before the
shorter USD to avoid `BTCBUSD` → wrongly `BTCB-USD`), Kraken swaps `/` for `-`, Upbit swaps segment order. Reuses (does
not duplicate) the codebase's existing `derive_settlement_dimensions`/`derive_base_token` per-venue-symbol-shape
convention already established for the FUTURES side of these same venues — extended `derive_settlement_dimensions` with
4 new venue branches (BITFINEX-SPOT/BITGET-SPOT/BYBIT-SPOT/KRAKEN-SPOT) that didn't exist before, factored the new

- existing concatenated-venue logic into a `_extra_spot_settlement_dimensions()` helper to keep the function under the
  codex 200-line function-size ratchet (it hit 221L before the extraction). All reverse (canonical→wire) subscribe-path
  mapping functions were audited and fixed where the new hyphen/reversed-order would otherwise corrupt the wire
  subscribe message (Binance, Bitfinex, Bitget, Kraken, Upbit); Bybit's and OKX's reverse mappings were already
  itype-agnostic and needed no change (verified, not assumed).

### 2a. Original (incomplete) 6-file table — superseded by § 2 above, kept for provenance

| File                                                               | Line | Symbol source                                                 | Likely already hyphenated?                                                          |
| ------------------------------------------------------------------ | ---- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `market_tick_data_service/live/connectors/binance_spot_book_ws.py` | 64   | Binance wire symbol (e.g. `SOLUSDT`)                          | **No** — Binance wire format has no separator                                       |
| `market_tick_data_service/live/connectors/coinbase_book_ws.py`     | 60   | Coinbase `product_id`                                         | Likely yes (Coinbase product ids are natively `BASE-QUOTE`)                         |
| `market_tick_data_service/live/connectors/coinbase_spot_ws.py`     | 79   | Coinbase `product_id`                                         | Likely yes                                                                          |
| `market_tick_data_service/live/connectors/upbit_spot_ws.py`        | 76   | Upbit `code` (e.g. `KRW-BTC`)                                 | Likely yes, but base/quote ORDER may be reversed vs UAC convention — needs checking |
| `market_tick_data_service/live/connectors/bitfinex_spot_ws.py`     | 137  | `pair` (parametrized `instrument_type`, not hardcoded `SPOT`) | Unknown — needs checking                                                            |
| `market_tick_data_service/live/connectors/okx_spot_book_ws.py`     | 33   | Derived from an `OKX-SWAP:PERPETUAL:` id via string replace   | Depends on the perpetual id's own symbol shape                                      |

This table was NOT a verified per-venue audit — it was drawn from a single grep pass + inspection of
`binance_spot_book_ws.py`/`coinbase_book_ws.py`/`okx_spot_book_ws.py` (the 3 files the census originally implicated). It
missed BITGET-SPOT/BYBIT-SPOT/KRAKEN-SPOT entirely and missed the separate trades/book file pairs for Binance/OKX/Upbit
— see § 2 above for the corrected, verified scope.

## 3. Why this was NOT fixed in the same pass as the small-drift item

- **Blast radius is bigger than measured.** The census only sampled the `instrument_type` MANIFEST axis (4,923
  non-canonical rows across ALL cefi, not per-venue). It never measured the id-FORM / filename-hyphenation dimension at
  all — the true non-canonical population from THIS defect could be materially larger once symbol-hyphenation is
  accounted for, and is not yet known.
- **The id is a foundational, downstream-facing value.** Unlike the narrow `instrument_type` field (a content-dict key +
  one partition segment), `instrument_id` IS the parquet FILENAME for cefi single-instrument shards (`reference-cefi.md`
  path grammar). Any reader keyed on the current id shape needs auditing before the shape changes.
- **A partial fix would have been actively worse.** Fixing only the `instrument_type` structural field (feeding the PATH
  partition + manifest column) while leaving `canonical = f"{VENUE}:SPOT:{symbol}"` (the id + FILENAME) unchanged would
  make the manifest instrument_type disagree with the object's own filename/id column — a NEW internal inconsistency,
  not a fix.

## Todos

- [x] [DATA] P1. **Audit the true per-venue blast radius** — ✅ 2026-07-30. Corrected scope is 8 venues / 12 files
      (not 6) — see § 2. Confirmed live/dead (all 8 are live-registered via `register_ws_feed_connector`), confirmed
      on-the-wire symbol shape per venue (concatenated / already-hyphenated / slash-separated / reversed-order), found 3
      venues the original census + 6-file table missed entirely (BITGET-SPOT, BYBIT-SPOT, KRAKEN-SPOT). **Not done**:
      per-venue manifest row counts for the historical non-canonical population — that requires a manifest/GCS census
      query this interactive session didn't run (out of scope for a code-level writer fix; the fix stops the bleeding
      going forward regardless of the historical count). If the exact historical count is ever needed, run
      `/data-pipeline-reconciliation cefi`'s distinct-value census, scoped to these 8 venues' `instrument_type`/id-form
      axis.
- [x] [SERVICE] P1. **Fix the ITYPE token** — ✅ `market-tick-data-service@46e85d94` (QG-green, pushed, `ahead=0`). All
      12 files now build `SPOT_PAIR` (never a literal — `InstrumentType.SPOT_PAIR.value` via the string `"SPOT_PAIR"`,
      matching the enum's own value) in both the `instrument_id`/filename and the matching `ReceivedTick`/content-dict
      `instrument_type` fields (previously mixed `"SPOT"`/`"spot"`).
- [x] [SERVICE] P1. **Fix symbol hyphenation where missing** — ✅ same commit. Added
      `derive_spot_pair_symbol(venue,     raw_symbol)` to `tardis_margin_marker.py` — the single insertion point reused
      by every venue needing a transform. Found and fixed **2 additional canonicality defects the original todo didn't
      anticipate**: Kraken's wire format uses `/` not `-` (a third kind of defect — wrong separator, not
      missing/reversed), and Upbit's native market-code order is QUOTE-BASE (`KRW-BTC`) which needed REVERSING to
      BASE-QUOTE (`BTC-KRW`) to match the canonical grammar — confirmed against `unified-api-contracts`' own
      canonical_id_builder test fixture and instruments-service's batch-side `_resolve_base_quote` Upbit inversion (same
      real convention, re-implemented locally since MTDS cannot depend on instruments-service). Extended
      `derive_settlement_dimensions` with 4 new venue branches (BITFINEX-SPOT/BITGET-SPOT/BYBIT-SPOT/KRAKEN-SPOT)
      reusing the established quote-suffix-splitting convention rather than inventing a new one; factored the
      concatenated-venue branches into `_extra_spot_settlement_dimensions()` to keep `derive_settlement_dimensions`
      under the codex 200-line function-size ratchet (hit 221L before the extraction, caught by `quality-gates.sh`,
      fixed before shipping). Audited + fixed every reverse (canonical→wire) subscribe-path mapping affected by the new
      hyphen/reversed-order (Binance, Bitfinex, Bitget, Kraken, Upbit); verified Bybit's and OKX's were already
      itype-agnostic and needed no change.
- [x] [TEST] P1. **New regression tests per fixed connector** — ✅ same commit. Updated all 13 existing test files
      asserting the old `:SPOT:`/reversed/slash shapes; added a dedicated
      `tests/unit/test_cefi_spot_pair_canonicality_2026_07_30.py` asserting `is_canonical_instrument_id(...) is True` on
      each of the 8 venues' REAL connector code path output (not a hand-built id); added
      `TestDeriveSpotPairSymbol`/extended `TestSpotVenues` unit coverage for the new helper + the 4 new
      `derive_settlement_dimensions` branches in `test_tardis_shared_v6.py`. Full MTDS suite: 7620 passed, 0 failed.
- [x] [DATA] P2. **Downstream-reader audit before shipping** — ✅ 2026-07-30. Grepped the whole MTDS source tree
      (excluding `live/connectors/` + `tests/`) for the literal `:SPOT:` pattern — zero hits. No reader hard-codes the
      old shape; the standard `CanonicalParquetReader`/manifest-key resolution path is itype-value-agnostic. No
      follow-up needed.
