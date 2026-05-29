---
name: mdps_state_adapter_leading_nan_audit
title: "MDPS state adapter leading-NaN bins + NaN volume — multi-adapter audit"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
created: 2026-05-29
author: harsh + claude (session dab322c6)
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 1.2
status: BLOCKED-OPERATOR-DECISION
source:
  - market-data-processing-service/market_data_processing_service/app/adapters/cefi/derivative_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/cefi/futures_chain_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/cefi/options_chain_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/defi/liquidity_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/defi/market_state_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/cefi/book_snapshot_adapter.py
  - market-data-processing-service/market_data_processing_service/app/adapters/tradfi/tbbo_adapter.py
---

## What I found

While verifying the user's LOCF requirement during the pure-Polars Stage 4
sweep (2026-05-29), I audited every MDPS adapter for density + NaN +
leading-gap semantics. Per-adapter table:

| Adapter | finalize_session_grid | apply_locf_fill | OHLC leading | Volume |
| --- | --- | --- | --- | --- |
| `cefi/trades_adapter` | ✓ | — | dropped | dense | 
| `tradfi/trades_adapter` | ✓ | — | dropped | dense |
| `tradfi/ohlcv_passthrough` | ✓ | — | dropped | dense |
| `defi/fx_rate_adapter` | ✓ (fixed 2026-05-29) | — | dropped | zero |
| `defi/swap_adapter` | ✓ (fixed 2026-05-29) | — | dropped | dense |
| `cefi/derivative_adapter` | ✗ | mark/index/funding/OI | NaN (pre-first-obs) | NaN throughout |
| `cefi/futures_chain_adapter` | ✗ | mark/index/last/basis/OI | NaN (pre-first-obs) | NaN throughout |
| `cefi/options_chain_adapter` | ✗ | mark/index/IV/greeks | NaN (pre-first-obs) | NaN throughout |
| `defi/liquidity_adapter` | ✗ | tvl/reserves/prices/liquidity | NaN (pre-first-obs) | NaN throughout |
| `defi/market_state_adapter` | ✗ | supply/borrow/liquidity/fee | NaN (pre-first-obs) | NaN throughout |
| `cefi/book_snapshot_adapter` | ✗ | none | NaN throughout (no LOCF) | — |
| `tradfi/tbbo_adapter` | ✗ | none | NaN-init | varies |

Empirical verification (`/tmp/test_locf_nan.py` 2026-05-29): a state-only
adapter with leading NaN bins propagates through the 15s → 1m polars
aggregator as 15 NaN minute candles + 1440 NaN-volume rows.

## Why it matters

The user's stated requirement (2026-05-29 — codified in
[[feedback_locf_dense_candles_no_nan]]):

> lets say that an illiquid instrument have no trades for 2 hours straight
> so those 2 hours candles across the timeframe should be forward fill and
> their volume should be 0 and oi should be same and the same for other
> columns which are supported for that data type. I dont expect any nan
> values in the output.

The 7 state-only adapters above produce candle output with NaN — both
leading-edge NaN (pre-first-obs bins not dropped) and structural NaN
(volume column never filled). Downstream consumers (features-service,
strategy-service) either:

1. Trip on the NaN (correctness bug), OR
2. Carry a NaN-handling shim that masks the underlying density bug.

The pure-Polars Stage 4 aggregator now logs a WARN when it sees NaN in
input (fast_candle_aggregation.py 2026-05-29 commit) — this gives the
operator visibility into which adapter+data_type combos are violating
the contract in production.

## Why this is BLOCKED-OPERATOR-DECISION (not fixed inline)

`_finalize_session_grid` in `base_adapter.py` is currently
**close-trigger only**: it uses `~np.isnan(close)` to find the first
observation. For state-only adapters where close is structurally NaN
(no trades — these are derivative_ticker / liquidity / market_state
snapshot streams), the existing helper returns
`_make_empty_candle_output()` → would silently drop legitimate state-only
parquets.

A correct fix requires either:

- **Option A**: Extend `_finalize_session_grid` to accept a `state_col`
  parameter that names the "first-observation driver" column for
  state-only adapters (e.g. `mark_price` for derivative_adapter,
  `tvl` for liquidity_adapter). Pre-first-state-obs bins dropped;
  post-first LOCF carried; volume zeroed.
- **Option B**: Write a separate `_finalize_state_grid(output, *, state_col, flow_cols)` helper
  and dispatch from each adapter.
- **Option C**: Operator-acked decision that state-only adapters are
  exempt from the no-NaN contract (downstream consumers do their own
  NaN handling).

Each option ripples to 7 adapters × downstream consumers. Operator
needs to pick A/B/C before agents touch state adapter code.

## Recommended decision

**Option A** (extend `_finalize_session_grid` with a `state_col` kw
parameter). It keeps the single-helper SSOT, requires the smallest
adapter-side change (each state-only adapter passes one extra kwarg),
and surfaces a consistent contract: every adapter calls
`_finalize_session_grid` before returning.

## Scope (when unblocked)

1. Add `state_col: str | None = None` to `_finalize_session_grid`.
2. When `state_col` is provided, use `~np.isnan(<state_col>)` as the
   "first observation" mask instead of `~np.isnan(close)`.
3. Add `flow_cols: tuple[str, ...] | None = None` for zero-fill columns
   (default to `("volume", "trade_count", "buy_volume", "sell_volume",
   "buy_trade_count", "sell_trade_count", "total_volume", "swap_count",
   "volume_quote_usd")` if `state_col` provided and not overridden).
4. Update 7 state adapters to call `_finalize_session_grid(output, state_col=<canonical>)`.
5. Update tests to reflect dense LOCF semantic (no leading NaN, no NaN volume).
6. Remove the WARN log from `fast_candle_aggregation.py` once the
   adapters are clean (or keep as guard).

Tests in scope:
- `tests/unit/test_more_defi_adapters.py` — liquidity + market_state
- `tests/unit/test_futures_chain_adapter.py`
- `tests/unit/test_cefi_derivative_adapter.py`
- Add coverage for the leading-gap case in each.

## Codex SSOT updates

- `codex/02-data/honest-absence-downstream-handling.md` — add §
  "Per-adapter density contract: dense + LOCF + no leading NaN".
- `codex/06-coding-standards/adapter-finalization-contract.md` — new
  doc tying every adapter to `_finalize_session_grid` (or its state-col
  variant). Code-review checklist item.

## Composes with

- [[feedback_locf_dense_candles_no_nan]] — the user-visible contract.
- [[feedback_no_fallback_one_engine]] — fix at the adapter, not via
  aggregator post-processing.
- [[feedback_fix_bugs_you_find_not_just_yours]] — surfaced during a
  pure-Polars migration; not artificially scoped out.
- workspace `Manifest + honest absence` — shard-level honest absence
  is unchanged; this is a within-series density contract.

## Phase 1 unblock

- [ ] [DECISION] P0. Operator picks A / B / C
- [ ] [SCRIPT] P0. If A or B: extend `_finalize_session_grid` (or write `_finalize_state_grid`) helper
- [ ] [SCRIPT] P0. Update 7 state adapters to call new helper
- [ ] [TEST] P0. Add leading-gap + LOCF-density tests for each updated adapter
- [ ] [VERIFY] P0. Remove aggregator WARN log + re-run full MDPS test suite
- [ ] [DOCS] P1. Codex SSOT updates per above
