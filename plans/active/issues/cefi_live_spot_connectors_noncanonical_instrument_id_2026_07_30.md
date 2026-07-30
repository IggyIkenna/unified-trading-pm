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
status: open
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

## 2. The 6 affected files (all build a `{VENUE}:SPOT:{symbol}` id)

| File                                                               | Line | Symbol source                                                 | Likely already hyphenated?                                                          |
| ------------------------------------------------------------------ | ---- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| `market_tick_data_service/live/connectors/binance_spot_book_ws.py` | 64   | Binance wire symbol (e.g. `SOLUSDT`)                          | **No** — Binance wire format has no separator                                       |
| `market_tick_data_service/live/connectors/coinbase_book_ws.py`     | 60   | Coinbase `product_id`                                         | Likely yes (Coinbase product ids are natively `BASE-QUOTE`)                         |
| `market_tick_data_service/live/connectors/coinbase_spot_ws.py`     | 79   | Coinbase `product_id`                                         | Likely yes                                                                          |
| `market_tick_data_service/live/connectors/upbit_spot_ws.py`        | 76   | Upbit `code` (e.g. `KRW-BTC`)                                 | Likely yes, but base/quote ORDER may be reversed vs UAC convention — needs checking |
| `market_tick_data_service/live/connectors/bitfinex_spot_ws.py`     | 137  | `pair` (parametrized `instrument_type`, not hardcoded `SPOT`) | Unknown — needs checking                                                            |
| `market_tick_data_service/live/connectors/okx_spot_book_ws.py`     | 33   | Derived from an `OKX-SWAP:PERPETUAL:` id via string replace   | Depends on the perpetual id's own symbol shape                                      |

This table is NOT a verified per-venue audit — it is drawn from a single grep pass + inspection of
`binance_spot_book_ws.py`/`coinbase_book_ws.py`/`okx_spot_book_ws.py` (the 3 files the census originally implicated).
`coinbase_spot_ws.py`/`upbit_spot_ws.py`/`bitfinex_spot_ws.py` are named by grep only, NOT yet individually confirmed to
be live/active writers, NOT yet confirmed for their actual symbol-hyphenation behavior. **Todo 1 below is exactly this
missing per-venue audit.**

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

- [ ] [DATA] P1. **Audit the true per-venue blast radius** — for each of the 6 files, confirm (a) is it a live,
      currently-run connector (not dead code), (b) what its actual on-the-wire symbol shape is (hyphenated BASE-QUOTE
      already, or not), (c) how many manifest rows currently carry a non-canonical id from this specific defect, sampled
      per venue (not the aggregate 4,923 the census measured). Gate: a per-venue table with real measured counts,
      replacing the "likely" column in § 2 above with confirmed facts.
- [ ] [SERVICE] P1. **Fix the ITYPE token** — change `f"{VENUE}:SPOT:{symbol}"` → `f"{VENUE}:SPOT_PAIR:{symbol}"` (or
      better, use `InstrumentType.SPOT_PAIR.value`, never a literal) in all 6 files, AND the matching
      `ReceivedTick`/content-dict `instrument_type` fields (currently `"SPOT"`/`"spot"` mixed) to
      `InstrumentType.SPOT_PAIR.value`. Depends on todo 1 (need the live/dead classification first — don't touch a
      connector that turns out to be dead code, just delete it instead).
- [ ] [SERVICE] P1. **Fix symbol hyphenation where missing** — for any venue confirmed non-hyphenated (Binance
      confirmed; others per todo 1), insert the BASE-QUOTE hyphen the canonical id grammar requires, using the SAME
      symbol-splitting convention already used elsewhere in this codebase for the same venue (do not invent a new one —
      check `market_interface/adapters/cefi/` for an existing Binance/etc. symbol-parser to reuse).
- [ ] [TEST] P1. **New regression tests per fixed connector** — for each of the 3 (or 6, per todo 1) changed files,
      assert `is_canonical_instrument_id(built_id) is True` on a representative real symbol, locking in both dimensions
      of the fix. Extend, do not just re-verify, the existing `tests/live/connectors/` suite for each file.
- [ ] [DATA] P2. **Downstream-reader audit before shipping** — grep every reader of these 6 venues' cefi spot data for
      any code that pattern-matches the OLD `:SPOT:` id shape (not just `CanonicalParquetReader`'s standard resolution)
      — a reader hard-coding the old shape would silently stop matching once the writer fix ships. Report findings; fix
      inline if trivial, otherwise a new todo.
