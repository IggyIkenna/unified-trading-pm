---
doc_type: issue
title:
  "cefi `available_at` wall-clock in 2 BATCH handlers despite a deterministic per-row timestamp already present in the
  same function (same defect class as the DeFi `available_at` clobber fix)"
summary: >-
  Audit todo from defi_consolidated_closeout_2026_07_18.md line 761 ("cefi/prediction timestamp-provenance audit —
  backfills were only sampled for canonical-SHAPE, not this specific available_at timestamp mismatch class"). Sampled
  cefi + prediction MTDS write-path handlers for the DeFi bug's exact shape (stamp/derive a real per-row timestamp, then
  either clobber it or ignore it in favor of `datetime.now(UTC)` for `available_at`). PREDICTION's core adapters
  (kalshi_adapter.py, polymarket_adapter.py) already do this correctly (`available_at = max(tick_ts,
  market_created_at)`) — no gap found there. CEFI's primary high-volume path (ccxt_adapter.py, via
  compute_bar_close_boundary) is also correct. But 2 smaller/newer cefi BATCH handlers have the SAME defect: a
  deterministic timestamp is computed/available in the row but `available_at` uses wall-clock `attempted_at` instead —
  breaking the batch==live ε=0 determinism contract on re-run/replay, same as the resolved DeFi issue.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags:
  [data-correctness, available-at, determinism, batch-equals-live, cefi, deribit, book-microstructure, audit-finding]
related:
  - /plans/active/cefi_consolidated_closeout_2026_07_18.md
  - /plans/active/l2_book_microstructure_capture_2026_07_13.md
  - /plans/active/defi_consolidated_closeout_2026_07_18.md
  - /plans/archive/issues/defi_available_at_clobbered_by_wallclock_2026_07_20.md
  - /codex/09-strategy/operational/paper-batch-live-reconciliation.md
created: 2026-07-24
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: data-engineer
drift_direction: none
depends_on: []
locked_by:
locked_since:
source:
  [
    "defi_consolidated_closeout_2026_07_18.md line 761, [DATA] P2 'cefi/prediction timestamp-provenance audit' — audit
    executed 2026-07-24, this doc is its output",
  ]
resolved_by:
---

# cefi `available_at` wall-clock despite an available deterministic row timestamp

## What was audited and why

`defi_consolidated_closeout_2026_07_18.md`'s DeFi `available_at` fix (`market-tick-data-service@f7af6ece` + `@51ec9af2`,
see `plans/archive/issues/defi_available_at_clobbered_by_wallclock_2026_07_20.md`) found DeFi handlers
computing/stamping a deterministic on-chain timestamp for `available_at` and then clobbering it with
`datetime.now(UTC)`, or setting wall-clock directly when a real event timestamp existed in the fetched payload. The
cross-asset `mtds_available_at_cross_asset_backfill_2026_07_13.md` plan separately audited cefi/prediction/tradfi, but
only for **canonical-SHAPE** — whether the `available_at` manifest column was populated at all (0% fill rate → fix →
re-backfill). It never asked whether a NON-blank `available_at` value is wall-clock-when-a-real-timestamp-existed. This
doc closes that gap for cefi + prediction.

## Method

Read (not grepped-then-assumed) every candidate cefi/prediction write-path file for the
`stamp X, then assign datetime.now(UTC)` shape or a direct `available_at = attempted_at` assignment where the
surrounding function already computes a deterministic alternative:

- **prediction**: `market_interface/adapters/prediction/kalshi_adapter.py`,
  `market_interface/adapters/prediction/polymarket_adapter.py` — these are prediction's actual write path (MTDS
  `TickDataHandler`/`download` dispatches through these adapters; there are no prediction-specific `cli/handlers/*.py`
  files the way DeFi has one file per data_type).
- **cefi**: `market_interface/adapters/cefi/ccxt_adapter.py` (primary high-volume path), plus the newer standalone
  `cli/handlers/deribit_options_chain_handler.py`, `cli/handlers/deribit_volatility_index_handler.py`,
  `cli/handlers/book_microstructure_handler.py` (Deribit + cross-venue L2 additions, all cefi-tagged, all
  `record_captured` callers).
- `plans/epics/predictions_master.md`'s stale, explicitly-"UNVERIFIED against current reality" todo "Lifecycle-bounded
  `available_at` stamping for Polymarket + Kalshi adapters" was checked against the live adapter code and found already
  satisfied — not a live gap, just an un-flipped stale checkbox in a superseded epic doc (out of scope to fix here).

## Findings

**No gap in prediction.** Both `kalshi_adapter.py` (`:601-603`) and `polymarket_adapter.py` (`:678-680`) derive
`available_at = ts_series.where(ts_series >= created_floor, created_floor)` — i.e. `max(tick_ts, market_created_at)`, a
fully deterministic per-row derivation from the fetched trade data. Re-running the same historical window reproduces the
same `available_at`. This is exactly Option A's policy from the resolved DeFi issue, already implemented here.

**No gap in cefi's primary path.** `ccxt_adapter.py:366` derives via `compute_bar_close_boundary(open_ts, timeframe)` —
deterministic from the bar's own `open_ts`, not wall-clock.

**Two real gaps, same defect class as the resolved DeFi bug**:

1. `cli/handlers/deribit_volatility_index_handler.py::_candles_to_dataframe` (line ~154-172) — each row already carries
   a deterministic timestamp derived straight from Deribit's own OHLC candle data:
   `"timestamp": datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)`. The SAME function sets `"available_at": attempted_at`,
   where `attempted_at = datetime.now(UTC)` (set once per currency-day fetch, line ~222). This is a **BATCH** handler
   (explicit design doc: "BATCH == per-day dispatch... for consistency with the rest of the batch fleet") — a re-run of
   the same day produces a different `available_at` every time, breaking ε=0 exactly like the DeFi bug did. The fix is
   mechanical: derive `available_at` from each row's own `ts_ms`/`timestamp` instead of `attempted_at` (mirrors the DeFi
   fix's per-row `stamp_available_at_onchain_tick`-style pattern).
2. `cli/handlers/book_microstructure_handler.py::_process_one_instrument` / `_rows_to_dataframe` (line ~226-240,
   ~166-169) — the function already computes a deterministic, day-representative `as_of`
   (`datetime(target_day.year, ..., 12, 0, 0, tzinfo=UTC)`, honestly documented as an approximation since the upstream
   `depth_of_book_10` WS connectors don't carry a per-row capture timestamp) and passes it into
   `derive_microstructure_rows(...)`. But `_rows_to_dataframe` stamps `available_at=attempted_at.isoformat()` —
   `attempted_at = datetime.now(UTC)`, the BATCH-run wall-clock time, not the already-computed `as_of`. This handler's
   own docstring states "BATCH == LIVE — the canonical shape is IDENTICAL regardless of when the underlying book was
   captured" (an explicit ε=0 design goal), yet `available_at` is the one field that is NOT reproducible on re-run. Fix:
   use `as_of` (already computed, already passed into the row-derivation call) for `available_at` instead of
   `attempted_at`.

**One weaker/lower-confidence candidate, NOT asserted as a bug**:
`cli/handlers/deribit_options_chain_handler.py ::_rows_to_dataframe` (line ~499-503) calls
`stamp_available_at_explicit(df, when=attempted_at)` and then immediately overwrites the result with
`df.assign(available_at=datetime.now(UTC).isoformat())` — structurally identical to the DeFi bug's "stamp, then
adjacent-line clobber" shape. UNLIKE the two findings above, this handler's own docstring states wall-clock is the
intentional choice ("available_at — per-row write-time as required by UTL asserts") for a LIVE-only options-chain
snapshot with "NO backfill... built for live/replay dispatch only" — there is no on-chain/event timestamp in a ticker
snapshot the way there is in DeFi's data. The redundant `stamp_available_at_explicit` call immediately discarded by the
very next line is dead code / a leftover from an earlier revision, worth a cleanup, but is NOT the same "discarding a
genuine deterministic value" bug as findings 1-2. Flagged for the same code-owner to consider, not claimed as a
determinism regression.

## What is NOT claimed

- No claim about corrective backfill of already-written parquets for the 2 confirmed handlers — that is a design
  decision (same as the DeFi issue's Option A/B/C), not scoped here.
- No corpus-scale measurement of how many existing DVOL/book-microstructure rows carry a wrong `available_at` — this is
  a code-read finding, not a data audit.
- No claim this generalizes beyond the specific files read. Other cefi handlers not enumerated above were not checked.

## Recommended fix (mirrors the resolved DeFi pattern, NOT executed here — audit scope only)

- `deribit_volatility_index_handler.py`: `"available_at": datetime.fromtimestamp(ts_ms / 1000.0, tz=UTC)` (reuse the
  same `ts_ms`→`timestamp` conversion already happening on the same line) instead of `attempted_at`.
- `book_microstructure_handler.py`: `df.assign(available_at=as_of.isoformat(), source=_SOURCE)` instead of
  `attempted_at.isoformat()` (pass `as_of` into `_rows_to_dataframe` alongside `attempted_at`, or thread it through).
- Add a regression test per handler asserting a same-day re-run produces byte-identical `available_at` (same test shape
  the resolved DeFi issue recommended).

## Provenance

Filed 2026-07-24 executing `defi_consolidated_closeout_2026_07_18.md` line 761 (`[DATA] P2` audit todo). Code fix is
explicitly out of scope for this dispatch — routed to `cefi_consolidated_closeout_2026_07_18.md` Track 6 (cefi
data-correctness/hygiene) as the owning plan.
