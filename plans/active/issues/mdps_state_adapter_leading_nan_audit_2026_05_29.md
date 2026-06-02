---
name: mdps_state_adapter_leading_nan_audit
title: "MDPS state adapter leading-NaN bins + NaN volume — multi-adapter audit"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
created: 2026-05-29
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
status: active
decisions_landed: 2026-06-01
source:
  - market-data-processing-service/market_data_processing_service/app/adapters/cefi/derivative_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/cefi/futures_chain_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/cefi/options_chain_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/defi/liquidity_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/defi/market_state_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/cefi/book_snapshot_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/tradfi/tbbo_adapter.py
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

## ✅ Operator decisions (2026-06-01) — UNBLOCKED

Two composing decisions landed (this doc was `BLOCKED-OPERATOR-DECISION`):

### Decision 1 — Leading-bin policy = **CARRY-FROM-PRIOR-DAY** (not drop)

The current `_finalize_session_grid` **drops** every bin before an instrument's first real trade of the day ("no prior
observation to carry forward"). Operator ruling: for a **continuously-traded** instrument we must instead **seed the
finalizer with the prior day's last known price** and forward-fill the leading bins from bin 0 — so the first N minutes
of each day are dense (carried-forward price, `volume=0`, `staleness_seconds` from the prior trade) rather than absent.

- **PIT-safe**: the prior day's last price is known at 00:00 — zero look-ahead, batch==live (a live trader at the open
  knows yesterday's close). Matches ta-lib/backtrader (carry prior close across the weekend gap).
- **Cold-start degrades to drop**: an instrument's _very first_ trading day (no prior observation anywhere) still drops
  pre-first-trade bins — there is genuinely nothing to carry.
- **Cost (the real work)**: breaks single-file independence. The finalizer must receive a per-instrument
  `last_known_price` + `last_trade_ts` seed (sourced from the prior day's last parquet / manifest). Edge cases: prior
  day missing, instrument halted for multiple days (staleness grows — fine, recorded), DST/holiday gaps.
- **`market_state==CLOSED` bins still drop** (untradeable — unchanged).

### Decision 2 — State adapters = **Option A** (`state_col` kwarg on `_finalize_session_grid`)

Extend the single SSOT helper with `state_col` (+ `flow_cols`) so the 7 state-only adapters (close structurally NaN) use
their first-observation driver column (`mark_price`, `tvl`, …) as the trigger instead of `close`. Single-helper SSOT,
smallest adapter-side change. Composes on top of Decision 1 (state adapters get prior-day carry too, keyed on
`state_col`).

**Sequence**: Decision 1 (leading-bin carry seed, applies to ALL adapters) → Decision 2 (Option A wires the 7 state
adapters to the same finalizer). The reprocess to make existing data dense rides the deferred backfill pass.

## What I found

While verifying the user's LOCF requirement during the pure-Polars Stage 4 sweep (2026-05-29), I audited every MDPS
adapter for density + NaN + leading-gap semantics. Per-adapter table:

| Adapter                      | finalize_session_grid | apply_locf_fill               | OHLC leading             | Volume         |
| ---------------------------- | --------------------- | ----------------------------- | ------------------------ | -------------- |
| `cefi/trades_adapter`        | ✓                     | —                             | dropped                  | dense          |
| `tradfi/trades_adapter`      | ✓                     | —                             | dropped                  | dense          |
| `tradfi/ohlcv_passthrough`   | ✓                     | —                             | dropped                  | dense          |
| `defi/fx_rate_adapter`       | ✓ (fixed 2026-05-29)  | —                             | dropped                  | zero           |
| `defi/swap_adapter`          | ✓ (fixed 2026-05-29)  | —                             | dropped                  | dense          |
| `cefi/derivative_adapter`    | ✗                     | mark/index/funding/OI         | NaN (pre-first-obs)      | NaN throughout |
| `cefi/futures_chain_adapter` | ✗                     | mark/index/last/basis/OI      | NaN (pre-first-obs)      | NaN throughout |
| `cefi/options_chain_adapter` | ✗                     | mark/index/IV/greeks          | NaN (pre-first-obs)      | NaN throughout |
| `defi/liquidity_adapter`     | ✗                     | tvl/reserves/prices/liquidity | NaN (pre-first-obs)      | NaN throughout |
| `defi/market_state_adapter`  | ✗                     | supply/borrow/liquidity/fee   | NaN (pre-first-obs)      | NaN throughout |
| `cefi/book_snapshot_adapter` | ✗                     | none                          | NaN throughout (no LOCF) | —              |
| `tradfi/tbbo_adapter`        | ✗                     | none                          | NaN-init                 | varies         |

Empirical verification (`/tmp/test_locf_nan.py` 2026-05-29): a state-only adapter with leading NaN bins propagates
through the 15s → 1m polars aggregator as 15 NaN minute candles + 1440 NaN-volume rows.

## Why it matters

The user's stated requirement (2026-05-29 — codified in [[feedback_locf_dense_candles_no_nan]]):

> lets say that an illiquid instrument have no trades for 2 hours straight so those 2 hours candles across the timeframe
> should be forward fill and their volume should be 0 and oi should be same and the same for other columns which are
> supported for that data type. I dont expect any nan values in the output.

The 7 state-only adapters above produce candle output with NaN — both leading-edge NaN (pre-first-obs bins not dropped)
and structural NaN (volume column never filled). Downstream consumers (features-service, strategy-service) either:

1. Trip on the NaN (correctness bug), OR
2. Carry a NaN-handling shim that masks the underlying density bug.

The pure-Polars Stage 4 aggregator now logs a WARN when it sees NaN in input (fast_candle_aggregation.py 2026-05-29
commit) — this gives the operator visibility into which adapter+data_type combos are violating the contract in
production.

## Why this is BLOCKED-OPERATOR-DECISION (not fixed inline)

`_finalize_session_grid` in `base_adapter.py` is currently **close-trigger only**: it uses `~np.isnan(close)` to find
the first observation. For state-only adapters where close is structurally NaN (no trades — these are derivative_ticker
/ liquidity / market_state snapshot streams), the existing helper returns `_make_empty_candle_output()` → would silently
drop legitimate state-only parquets.

A correct fix requires either:

- **Option A**: Extend `_finalize_session_grid` to accept a `state_col` parameter that names the "first-observation
  driver" column for state-only adapters (e.g. `mark_price` for derivative_adapter, `tvl` for liquidity_adapter).
  Pre-first-state-obs bins dropped; post-first LOCF carried; volume zeroed.
- **Option B**: Write a separate `_finalize_state_grid(output, *, state_col, flow_cols)` helper and dispatch from each
  adapter.
- **Option C**: Operator-acked decision that state-only adapters are exempt from the no-NaN contract (downstream
  consumers do their own NaN handling).

Each option ripples to 7 adapters × downstream consumers. Operator needs to pick A/B/C before agents touch state adapter
code.

## Recommended decision

**Option A** (extend `_finalize_session_grid` with a `state_col` kw parameter). It keeps the single-helper SSOT,
requires the smallest adapter-side change (each state-only adapter passes one extra kwarg), and surfaces a consistent
contract: every adapter calls `_finalize_session_grid` before returning.

## Scope (when unblocked)

1. Add `state_col: str | None = None` to `_finalize_session_grid`.
2. When `state_col` is provided, use `~np.isnan(<state_col>)` as the "first observation" mask instead of
   `~np.isnan(close)`.
3. Add `flow_cols: tuple[str, ...] | None = None` for zero-fill columns (default to
   `("volume", "trade_count", "buy_volume", "sell_volume", "buy_trade_count", "sell_trade_count", "total_volume", "swap_count", "volume_quote_usd")`
   if `state_col` provided and not overridden).
4. Update 7 state adapters to call `_finalize_session_grid(output, state_col=<canonical>)`.
5. Update tests to reflect dense LOCF semantic (no leading NaN, no NaN volume).
6. Remove the WARN log from `fast_candle_aggregation.py` once the adapters are clean (or keep as guard).

Tests in scope:

- `tests/unit/test_more_defi_adapters.py` — liquidity + market_state
- `tests/unit/test_futures_chain_adapter.py`
- `tests/unit/test_cefi_derivative_adapter.py`
- Add coverage for the leading-gap case in each.

## Codex SSOT updates

- `codex/02-data/honest-absence-downstream-handling.md` — add § "Per-adapter density contract: dense + LOCF + no leading
  NaN".
- `codex/06-coding-standards/adapter-finalization-contract.md` — new doc tying every adapter to `_finalize_session_grid`
  (or its state-col variant). Code-review checklist item.

## Composes with

- [[feedback_locf_dense_candles_no_nan]] — the user-visible contract.
- [[feedback_no_fallback_one_engine]] — fix at the adapter, not via aggregator post-processing.
- [[feedback_fix_bugs_you_find_not_just_yours]] — surfaced during a pure-Polars migration; not artificially scoped out.
- workspace `Manifest + honest absence` — shard-level honest absence is unchanged; this is a within-series density
  contract.

## Phase 1 unblock

- [x] ✅ [DECISION] P0. Operator picks A / B / C → **Option A** + leading-bin policy = **carry-from-prior-day**
      (2026-06-01).
- [x] ✅ [SCRIPT] P0. **Decision 1 — finalizer carry-seed support.** `_finalize_session_grid` now accepts
      `seed_price`/`seed_ts` (+ `seed_state` for state adapters) and fills leading bins from bin 0 instead of dropping;
      cold-start (no seed) still drops; CLOSED still drops. — MDPS@5a5e989 + @4fd962d (tests:
      test_finalize_session_grid_seed.py prior-day-carry vs cold-start-drop vs CLOSED-drop).
- [x] ✅ [SCRIPT] P0. **Decision 1 — SOURCE + THREAD the per-instrument prior-day seed (DONE).** —
      market-data-processing-service@56202b0 | `CandleWriteMixin._read_prior_day_frame` + `_get_prior_day_seed` +
      `_extract_seed_from_prior_df` + `_timestamp_to_epoch_us` read the prior day's written candle parquet via the
      bucket-name SSOT (`get_output_bucket_for_asset_group` + `get_processed_path` + `build_processed_candle_path`);
      `seed_price` = last finite `close` (post-finalize close == driver for every adapter), `seed_state` = last finite
      value of each float state column; NEVER raises (any miss → cold-start). `_process_instrument_file` stashes a
      per-file seed context; `_seed_adapter_for_instrument` sets `adapter.set_prior_day_seed(...)` before each
      base-timeframe `process_to_candles` across ALL 4 paths (chain-by-key, chain-by-symbol, streaming-slice, standard);
      chain bundles read the prior-day `ticks.parquet` ONCE (cached) + filter per instrument; larger timeframes
      aggregate from the seeded base. 12 adapters declare `supports_prior_day_seed=True`; finalizer consumes-once +
      clears (no chain-loop leakage). 18 new tests (test_prior_day_seed.py) + 1308 unit tests green + full QG exit 0.
      ORIGINAL SCOPE NOTE (kept for provenance): Build `_get_prior_day_seed(asset_group, date_str, venue, symbol,
      data_type, timeframe)` and thread it into BOTH paths. **Call-path map (verified 2026-06-02,
      market-data-processing-service):** per-instrument dispatch is `live_workers.py` `_process_chain_timeframe`
      (~L1014–1022: `adapter.process_to_candles(tick_data=inst_data, timeframe, instrument_info=inst_info)`) +
      `_process_standard_timeframe` (~L1609–1629); batch reuses live via `batch_workers.py` →
      `_process_instrument_file` (`date_str` available ~L275) → `_process_all_timeframes` → the same two methods (NOTE:
      `_process_standard_timeframe` does NOT currently receive `date_str` — thread it down). Seed source is **genuinely
      absent** (no prior-day candle reader, no warm last-price cache): build a reader that resolves the prior-day candle
      parquet via `resolve_bucket_name(...)` (bucket-name SSOT — NO inline gs://) + `get_processed_path(asset_group,
      prior_date, timeframe, data_type, venue=...)` + a UTL `cloud_interface` object read, takes the LAST row's
      price(s) + ts, returns `None` on missing/empty (cold-start). For state adapters return the full last-row values as
      `seed_state` (mark_price/index/funding/OI, tvl/reserves, mid/spread/depth) so secondary columns carry too —
      else leading carried bins NaN those columns. Add `prior_day_seed` to the abstract `process_to_candles` + forward
      it from all 9 finalizer-routed adapters. Edge cases: prior-day missing → drop; multi-day halt → staleness grows
      (fine, recorded); DST/holiday gaps. Tests: mock the prior-day parquet read (live + batch parity). Then flip the
      issue-doc-level Decision-1 carry todo. SSOT for the contract: `codex/06-coding-standards/adapter-finalization-contract.md`.
- [x] ✅ [SCRIPT] P0. **Decision 2 — Option A.** Add `state_col: str | None = None` (+ `flow_cols`, `seed_state`) to
      `_finalize_session_grid`; first-obs mask uses `~isnan(<state_col>)` when provided. — MDPS@4fd962d.
- [x] ✅ [SCRIPT] P0. Update 7 state adapters to call `_finalize_session_grid(output, state_col=<canonical>)`
      (liquidity/market_state use close-driven finalize — close already = price driver + volume carries real TVL/supply).
      — MDPS@23d7add.
- [x] ✅ [TEST] P0. Add leading-gap (prior-day-carry + cold-start-drop) + LOCF-density tests for each updated adapter. —
      MDPS@4fd962d (finalizer-level: test_finalize_session_grid_seed.py + test_state_adapter_density.py) + @23d7add
      (per-adapter test files). 1252 MDPS unit tests green.
- [x] ✅ [VERIFY] P0. **KEEP the aggregator NaN-input WARN as a permanent regression guard** (per §Scope item 6's "or
      keep as guard" — all 7 state adapters now emit dense LOCF candles so it is dormant in steady state but catches any
      future adapter that regresses to the pre-LOCF leading-NaN shape). `fast_candle_aggregation.py:304-325` retained
      deliberately. MDPS unit suite green (1252 passed) EXCEPT the pre-existing **foreign** `test_dependency_checker_sports_prediction`
      bucket-tier drift (env-tier `-prd-` from market-data-processing-service@61900a3 — NOT this workstream; tracked as
      the `[BUG]` row in `issue_docs_remediation_sweep_2026_06_02.md`). Full `quality-gates.sh` exit-0 is blocked solely
      by that foreign file.
- [x] ✅ [DOCS] P1. Codex SSOT updates per above (+ document the carry-from-prior-day leading-bin contract). —
      `codex/06-coding-standards/adapter-finalization-contract.md` (new) + `codex/02-data/honest-absence-downstream-handling.md`
      § "Per-adapter density contract: dense + LOCF + no leading NaN + carry-from-prior-day".
- [ ] [DATA] P1. Reprocess to densify existing data — rides the deferred backfill pass (not a standalone walk).
