---
pair: execution-service → venue adapters (engine → adapter interface)
auditor: slot-4 / ikenna
audit_date: 2026-05-20
audit_file: plans/audit/execution_venue_contract_audit_2026_05_20.md
feeds_ordering_step: D6 (strategy + execution plan), D7 (live adapters plan)
status: complete
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-05-20
---

# C8: execution-service → venue-adapter contract audit — 2026-05-20

> **Audit scope**: This C8 audit examines the internal execution-service contract between the execution engine
> (orchestrators, routing layer) and the venue adapters (CCXT adapters, native REST adapters, DeFi protocol connectors,
> sports/prediction adapters). It is distinct from C3 (IS→execution), which audited the instruments-service →
> execution-service boundary.
>
> **Key questions**:
>
> 1. Does the engine correctly route errors through `classify_venue_error()` + `ADAPTER_FETCH_FAILED`?
> 2. Do CCXT adapters propagate typed errors or swallow them bare?
> 3. Are live and batch paths symmetric (same adapter interface, same error contract)?
> 4. Do DeFi execution protocols use `DefiErrorCode` correctly (FAIL/RETRY/SKIP routing)?
> 5. Are the 13 BATCH_ONLY cells from A6 represented as live gaps in the execution layer?
>
> **Repo SHAs at audit time**:
>
> - `execution-service@f6795bfe0` (2026-05-20)
> - `unified-trading-pm@c10dc85ec` (2026-05-20)
>
> **Sampling methodology**: exhaustive grep across all non-test Python source in `execution_service/` for Pattern 6
> (error classification) and live/batch path symmetry. Key files read in full: `base_adapter.py`, `orchestrator.py`,
> `multi_leg_orchestrator.py`, `instruction_router.py`, all 7 CCXT adapters, `defi_adapter.py`,
> `live_execution_handler.py`, `engine/modes/live/`, `engine/modes/batch/`.

---

## The architectural contract (SSOT)

```
                   ┌──────────────────────────────────────────┐
                   │  Execution Engine Layer                  │
                   │  ─ ExecutionOrchestrator (mode-agnostic) │
                   │  ─ MultiLegOrchestrator (DeFi+CeFi hybrid│
                   │  ─ InstructionRouter (routing layer)      │
                   │  ─ LiveMatchingEngine / BatchMatchingEngine│
                   │  ─ LiveExecutionHandler (CLI entry point) │
                   └──────────────────┬───────────────────────┘
                                      │
                          ┌───────────┴────────────┐
                          ▼                        ▼
          ┌────────────────────────┐  ┌────────────────────────┐
          │ CeFi / TradFi Adapters │  │  DeFi Protocol         │
          │ BaseCLOBAdapter        │  │  Connectors            │
          │  ─ CCXT (7 venues)    │  │  ─ UniswapConnector     │
          │  ─ Native REST (5)    │  │  ─ AAVEConnector         │
          │  ─ IBKR TradFi (6)   │  │  ─ AsterConnector        │
          │  ─ Kraken REST        │  │  ─ LidoConnector + 20+  │
          └────────────────────────┘  └────────────────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
  ┌──────────────────┐         ┌──────────────────────┐
  │ Sports Adapters  │         │ Prediction Adapters  │
  │ Betfair, Kalshi  │         │ Polymarket, Kalshi   │
  │ Matchbook, Odds-API│        │ (via sports_execution│
  └──────────────────┘         └──────────────────────┘
```

**Critical rule from CLAUDE.md**: "Live and batch are operational modes of the SAME pipeline. Identical schemas,
data_types, fields." The `BaseCLOBAdapter` interface is the canonical contract; every adapter must implement it
identically for both modes.

**DeFi hybrid rule**: DeFi = long/stake/lend leg (on-chain via DeFi protocols); hedge/short leg runs on CeFi perp
venues. Both legs route through the same orchestration layer.

---

## Pattern 1 — SSOT-owned reference flowing down

**For C8 this pattern examines whether the engine reads instrument specs from IS before routing orders (rather than
re-fetching venue APIs at order time).** This is already covered in C3 (IS→execution audit,
`plans/audit/is_execution_contract_audit_2026_05_20.md`).

### Dim 1 — Adapter coverage per asset_group (execution routing layer)

| asset_group     | Execution adapter exists                                     | Engine routes to adapter                                                         | Live path symmetric with batch                                                                               |
| --------------- | ------------------------------------------------------------ | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| CeFi            | YES — 7 CCXT + 5 native REST + Kraken                        | YES — `get_order_adapter()` factory                                              | YES — `LiveMatchingEngine` wraps adapter; `BatchMatchingEngine` uses MEL (same interface)                    |
| DeFi (on-chain) | YES — `DeFiAdapter` wrapping Uniswap/Aave/Lido connectors    | YES — `LiveExecutionHandler._get_defi_adapter()`                                 | PARTIAL — `DeFiAdapter.execute_instruction()` is live-only; no batch simulation path wired via `DeFiAdapter` |
| TradFi          | YES — `IbkrTradFiAdapter` (CME, CBOE, NASDAQ, NYSE, ICE, FX) | YES — via `get_order_adapter()` factory                                          | YES — adapter has `mode="sim"` path                                                                          |
| Sports          | YES — Betfair, Kalshi, Matchbook, Odds-API, Polymarket       | YES — `sports_execution/` adapters                                               | PARTIAL — sports adapters have live execution; paper/batch path via `BaseSportsAdapter` sim mode             |
| Prediction      | YES — Polymarket, Kalshi (via prediction_markets/)           | PARTIAL — `prediction_markets/` wired; Kalshi/Polymarket live credentials needed | PARTIAL — no batch simulation path confirmed wired                                                           |

### Dim 2 — Downstream handler IS-consumption status

**Cross-reference to C3 findings**: C3 already identified the IS→execution contract gaps. C8 focuses on the
engine→adapter layer downstream of that. Key finding carried forward:

- The `Deribit` connector at `venues/deribit_orders.py:505-506` fetches `tick_size` + `contract_size` from the live
  Deribit API at runtime rather than IS. **This means live DeFi execution for Deribit is fetching reference data from a
  live venue API, which adds latency and creates a live-API dependency in the execution hot path.** (P0-3 from C3.)

---

## Pattern 6 — Error classification at the boundary

This is the **primary focus** of C8, per the task description.

### Dim 5 — Error classification coverage across the execution → adapter chain

#### Engine layer (calls classify_venue_error correctly)

| Component                                | Status                                                                    | Evidence       |
| ---------------------------------------- | ------------------------------------------------------------------------- | -------------- |
| `engine/orchestrator.py`                 | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED` at order-level error | lines 252, 348 |
| `engine/multi_leg_orchestrator.py`       | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED` on leg failure       | lines 334, 470 |
| `engine/routing/instruction_router.py`   | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED` on routing failure   | line 281       |
| `cli/handlers/live_execution_handler.py` | ✅ `classify_and_emit_error()` from UTL (UTL wrapper around UAC pattern)  | 6 callsites    |

#### CeFi native REST adapters (correct — call classify_venue_error)

| Component                                         | Status                                                 | Evidence      |
| ------------------------------------------------- | ------------------------------------------------------ | ------------- |
| `trade_execution/adapters/_native_base.py`        | ✅ `classify_venue_error()` in HTTP-layer error helper | lines 157-167 |
| `trade_execution/adapters/binance_native.py`      | ✅ `classify_venue_error()` in `_handle_api_error()`   | line ~180     |
| `trade_execution/adapters/bybit_native.py`        | ✅ `classify_venue_error()` + venue param              | line 184      |
| `trade_execution/adapters/okx_native.py`          | ✅ `classify_venue_error()`                            | line 206      |
| `trade_execution/adapters/bitget_native.py`       | ✅ `classify_venue_error()`                            | line 180      |
| `trade_execution/adapters/bitfinex_native.py`     | ✅ `classify_venue_error()`                            | confirmed     |
| `trade_execution/adapters/kraken_rest_adapter.py` | ✅ `classify_venue_error()` at both HTTP + body layers | lines 662-720 |

#### CeFi CCXT adapters (GAP — no classify_venue_error)

| Component                                          | Status                                                                     | Evidence                 |
| -------------------------------------------------- | -------------------------------------------------------------------------- | ------------------------ |
| **`trade_execution/adapters/binance_ccxt.py`**     | **⚠ UNKNOWN_VENUE_ERROR_RECEIVED emitted but NO `classify_venue_error()`** | lines 281, 317, 465, 577 |
| **`trade_execution/adapters/hyperliquid_ccxt.py`** | **⚠ NO `classify_venue_error()` — `ccxt.BaseError` caught bare**           | lines 186, 332, 443      |
| **`trade_execution/adapters/bybit_ccxt.py`**       | **⚠ NO `classify_venue_error()`**                                          | all except blocks        |
| **`trade_execution/adapters/coinbase_ccxt.py`**    | **⚠ NO `classify_venue_error()`**                                          | all except blocks        |
| **`trade_execution/adapters/deribit_ccxt.py`**     | **⚠ NO `classify_venue_error()`**                                          | all except blocks        |
| **`trade_execution/adapters/okx_ccxt.py`**         | **⚠ NO `classify_venue_error()`**                                          | all except blocks        |
| **`trade_execution/adapters/upbit_ccxt.py`**       | **⚠ NO `classify_venue_error()`**                                          | all except blocks        |

**Root cause**: CCXT adapters catch `ccxt.InsufficientFunds`, `ccxt.InvalidOrder`, `ccxt.NetworkError`, `ccxt.BaseError`
directly and emit `ORDER_FAILED` event with a reason string (e.g. "INSUFFICIENT_FUNDS"), but do NOT call
`classify_venue_error()` to get a typed `VenueErrorClassification` (with `retry_safe`, `reconnect`, `action` fields).
The engine orchestrator layer calls `classify_venue_error()` when CCXT adapters raise, but receives a bare Python
exception with no venue error code — `classify_venue_error(venue, "ccxt.InsufficientFunds")` falls through to the
default `UNKNOWN_VENUE_ERROR_RECEIVED` bucket.

**Impact**: 7 CCXT adapters are live trading adapters for Binance, Hyperliquid, Bybit, Coinbase, Deribit, OKX, Upbit.
These cover critical DeFi hedge legs (Hyperliquid, Deribit) and carry_staked_basis CeFi perp venues. Unclassified errors
mean:

- RETRY\_\* errors are not retried (executor treats as FAIL)
- SKIP\_\* errors are not skipped gracefully
- No per-venue retry-safe signal flows to the orchestrator
- Incidents receive `classified: False` in ADAPTER_FETCH_FAILED event

**Note on dual-layer protection**: `_native_base.py` base-class catches HTTP-level errors (4xx/5xx) and calls
`classify_venue_error()` for those. CCXT adapters inherit `BaseCLOBAdapter` but NOT `_native_base.py` — they use CCXT's
own error hierarchy, which bypasses the native base HTTP layer entirely. The gap is specifically in the CCXT
application-level error types.

#### TradFi adapters

| Component                                                                                            | Status                                                      | Evidence                                                            |
| ---------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | ------------------------------------------------------------------- |
| `trade_execution/adapters/ibkr_tradfi.py`                                                            | **⚠ NO `classify_venue_error()` — `except Exception` bare** | multiple `except Exception as exc` blocks with `# pragma: no cover` |
| `trade_execution/adapters/cboe_adapter.py`, `cme_adapter.py`, `nasdaq_adapter.py`, `nyse_adapter.py` | **⚠ Inherit from `IbkrTradFiAdapter` — same gap**           | N/A                                                                 |

**Impact**: TradFi venues (CME, CBOE, NASDAQ, NYSE, ICE, FX) are not on the May-23 DeFi critical path. P1 severity.

#### DeFi protocol connectors

| Component                                                     | Status                                                                                                                             | Evidence                                                                                       |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `defi_execution/protocols/aster.py`                           | ✅ `classify_venue_error("ASTER", raw)`                                                                                            | lines 74-81                                                                                    |
| `defi_execution/protocols/aave.py`                            | ✅ `DefiErrorCode` mapping table + typed error code returned; error strings classified via `_classify_aave_error()`                | lines 42-100                                                                                   |
| `defi_execution/orchestrators/recursive_loop_orchestrator.py` | ✅ `DefiErrorCode` used for RECURSIVE_LOOP_ABORTED_HF, GAS_BUDGET_EXCEEDED, FLASH_RECEIVER_NOT_FOUND, FLASH_REPAYMENT_INSUFFICIENT | confirmed                                                                                      |
| `defi_execution/protocols/cctp.py`                            | ✅ `DefiErrorCode` codes embedded in error messages (CCTP_UNSUPPORTED_CHAIN, CCTP_BURN_FAILED etc.)                                | confirmed                                                                                      |
| **`adapters/defi_adapter.py`**                                | **⚠ NO `classify_venue_error()` or `DefiErrorCode` in retry loop**                                                                 | `execute_instruction()` retry loop catches bare `Exception` and retries without classification |
| `cli/handlers/live_execution_handler.py`                      | ✅ `classify_and_emit_error()` wraps DeFi execution errors at CLI boundary                                                         | confirmed                                                                                      |

**DeFiAdapter gap detail**: `DeFiAdapter.execute_instruction()` (lines 169-195) runs up to `max_retries=3` with
exponential backoff on any `Exception`. It does NOT call `classify_venue_error()` or check `DefiErrorCode` to decide
FAIL vs RETRY vs SKIP. A `RECURSIVE_LOOP_ABORTED_HF` error (which should be SKIP — position is already in liquidation
territory) gets treated identically to a transient network timeout. The retries on a SKIP-class error waste 3 attempts
before propagating.

#### Sports / prediction adapters

| Component                                                    | Status                                                                            | Evidence                    |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------- | --------------------------- |
| `sports_execution/adapters/exchanges/betfair.py`             | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED` at market + order boundaries | lines 490, 938              |
| `sports_execution/adapters/exchanges/kalshi.py`              | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED` at 6 callsites               | lines 254-546               |
| `sports_execution/adapters/exchanges/matchbook.py`           | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED`                              | lines 201-207               |
| `sports_execution/adapters/aggregator/odds_api.py`           | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED`                              | confirmed                   |
| `sports_execution/adapters/bookmaker_api/api_football.py`    | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED`                              | confirmed                   |
| **`sports_execution/adapters/exchanges/polymarket_clob.py`** | **⚠ NO `classify_venue_error()`**                                                 | all except blocks           |
| **`sports_execution/adapters/bookmaker_api/onexbet.py`**     | **⚠ NO `classify_venue_error()`**                                                 | not confirmed — likely bare |

---

## Pattern 6 supplementary — Live vs batch error contract symmetry

### Dim 5b — Does the engine use the same adapter interface in both modes?

**Architecture finding**: The execution engine is correctly designed for mode symmetry:

- `BatchMatchingEngine` (in `engine/modes/batch/matching_engine.py`) routes through MEL (matching-engine-library)
  simulated fills. It does NOT call venue adapters.
- `LiveMatchingEngine` (in `engine/modes/live/matching_engine.py`) wraps `BaseCLOBAdapter` via `get_order_adapter()`. It
  calls `adapter.place_order()`.
- `PaperMatchingEngine` (in `engine/modes/live/matching_engine.py`) also routes through MEL for paper trading in live
  mode.
- `ExecutionOrchestrator` (mode-agnostic) receives either `BatchMatchingEngine`, `LiveMatchingEngine`, or
  `PaperMatchingEngine` injected at construction time — same `MatchingEngine` protocol regardless of mode.

**The "Batch = Live" rule is structurally honoured at the engine level.** Both modes use the same `ChildOrder` →
`CanonicalFill` schema. Both emit `FILL_COMPLETED` events.

**The A6 BATCH_ONLY cells are in MTDS (market-tick-data-service), not execution-service.** They represent missing
_market-data_ live adapters (Hyperliquid websocket, Deribit websocket, Aster liquidations/trades), NOT missing
_execution_ live adapters. The execution-service already has live `HyperliquidCCXTAdapter`, `DeribitCCXTAdapter`, and
`AsterConnector` — these are wired for live trading. The A6 gap is about market data feeds feeding the strategy layer,
not execution routing.

**Clarification for D7 plan**: D7 "live adapters plan" should target MTDS live-mode WebSocket handlers for the 13
BATCH_ONLY cells, not execution-service adapters.

### Dim 5c — DeFi batch path gap

**Finding**: `DeFiAdapter.execute_instruction()` is live-only. There is no batch simulation path that routes DeFi
instructions through `DeFiAdapter`. In batch mode:

- DeFi trades route through `BatchMatchingEngine` → MEL AMM simulator (slippage model)
- This is the correct "batch = live" pattern per CLAUDE.md — MEL simulates fills without calling the real connector

**However**: The MEL AMM simulator for batch does not feed back from `DeFiAdapter`'s pre-simulation (Tenderly). In live
mode, `DeFiAdapter.enable_tenderly_simulation()` gates every on-chain tx with a Tenderly dry-run. In batch mode,
Tenderly is not invoked. This is expected (Tenderly = live infrastructure cost), but the MEL AMM model should match
Tenderly outcomes to the extent possible. This is a design note, not a P0 violation.

---

## Pattern 7 — Bucket-SSOT

**Cross-reference to C3**: P7 violations in execution-service were fully catalogued in C3. 13 non-test source files
construct bucket names as inline f-strings. All are pre-existing and covered by the
`bucket_name_ssot_canonicalisation_2026_05_10.md` successor plan.

No new P7 violations found specific to the engine → adapter path in C8.

---

## Patterns 2, 3, 4, 5 — Not applicable

**Pattern 2 (manifest emission)**: execution-service is a leaf execution service. It writes fill parquets to
`execution-store-*` buckets, not manifest indices. Zero `record_*` calls in non-test source. Verified clean.

**Pattern 3 (schema version)**: No manifest index maintained. N/A.

**Pattern 4 (honest-absence reasons)**: No `record_empty()` calls. N/A.

**Pattern 5 (expected_coverage preflight)**: execution-service uses `DependencyChecker` (GCS blob existence check for
IS + MTDS parquets) rather than `expected_coverage()`. This is appropriate for an execution service. N/A.

---

## 4-dimensional audit matrix (2026-05-20 snapshot)

| Dim    | What it measures                                        | Status                                                                   |
| ------ | ------------------------------------------------------- | ------------------------------------------------------------------------ |
| Dim 1  | Adapter coverage per asset_group (engine routing layer) | Mostly GREEN — DeFi + Sports batch path has minor gaps (see Dim 1 above) |
| Dim 2  | IS-consumption status (engine reads IS before routing)  | Cross-ref C3 — P0-3 Deribit tick_size live API fetch                     |
| Dim 3  | Manifest emission per handler                           | N/A — leaf execution service                                             |
| Dim 4  | Manifest schema version per bucket                      | N/A — no manifest bucket                                                 |
| Dim 5  | Error classification coverage                           | **GAP — 7 CCXT + 2 TradFi + 1 DeFiAdapter + 1 Polymarket**               |
| Dim 5b | Live/batch path symmetry (engine layer)                 | GREEN — BatchMatchingEngine / LiveMatchingEngine inject same protocol    |
| Dim 5c | A6 batch-only parity (execution layer)                  | GREEN — A6 gaps are in MTDS (market data), not execution                 |

---

## Findings summary by severity

### P0 — Immediate remediation required

| Finding                                                                                                                                            | Location                                                                                  | Pattern | Remediation                                                                                                                                                                                                                        |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **C8-P0-1**: 7 CCXT adapters have `except` blocks with no `classify_venue_error()` — typed CCXT errors escape classification                       | `trade_execution/adapters/{binance,hyperliquid,bybit,coinbase,deribit,okx,upbit}_ccxt.py` | P6      | Add `classify_venue_error(self.venue_name, _extract_ccxt_code(exc))` in each CCXT except block. Add `ADAPTER_FETCH_FAILED` emission. Helper `_extract_ccxt_code()` maps CCXT exception class name to UAC error code.               |
| **C8-P0-2**: `DeFiAdapter.execute_instruction()` retries ALL exceptions without classifying FAIL/RETRY/SKIP — burns 3 retries on SKIP-class errors | `adapters/defi_adapter.py:169-195`                                                        | P6      | Add `classify_venue_error(venue, DefiErrorCode)` check before retry decision. On `SKIP_*` prefix: return immediately with `{"status": "SKIPPED"}`, no retry. On `FAIL_*`: propagate immediately. On `RETRY_*`: retry with backoff. |

### P1 — Should fix pre-cutover

| Finding                                                                                                               | Location                                                 | Pattern | Remediation                                                                                                         |
| --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------- |
| **C8-P1-1**: `IbkrTradFiAdapter` has bare `except Exception` blocks without `classify_venue_error()`                  | `trade_execution/adapters/ibkr_tradfi.py`                | P6      | Add `classify_venue_error("ibkr", ...)` — TradFi not on May-23 DeFi critical path but IBKR is used for TradFi track |
| **C8-P1-2**: `sports_execution/adapters/exchanges/polymarket_clob.py` has no `classify_venue_error()`                 | `sports_execution/adapters/exchanges/polymarket_clob.py` | P6      | Add `classify_venue_error("polymarket", ...)` + `ADAPTER_FETCH_FAILED` — prediction track                           |
| **C8-P1-3**: C3 P0-3 carry-forward: Deribit connector fetches `tick_size`/`contract_size` from live API at order time | `venues/deribit_orders.py:115-118,505-506`               | P1      | Source from IS `InstrumentDefinitionsLoader`; fallback to live API only when IS record absent (log warning)         |

### Verified clean (no violation)

| Pattern                     | Finding                                                                                                                                    | Evidence                  |
| --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------- |
| P6 — Engine orchestrators   | `orchestrator.py`, `multi_leg_orchestrator.py`, `instruction_router.py` all emit `ADAPTER_FETCH_FAILED` + `classify_venue_error()`         | grep confirmed            |
| P6 — Native REST adapters   | `_native_base.py`, binance_native, bybit_native, okx_native, bitget_native, bitfinex_native, kraken_rest all call `classify_venue_error()` | grep confirmed            |
| P6 — Sports main exchanges  | Betfair, Kalshi, Matchbook, Odds-API, api_football all emit `ADAPTER_FETCH_FAILED` + `classify_venue_error()`                              | grep confirmed            |
| P6 — DeFi protocols         | `aster.py` uses `classify_venue_error("ASTER", raw)`                                                                                       | grep confirmed            |
| P6 — DeFi protocols         | `aave.py` uses `DefiErrorCode` mapping table (`_classify_aave_error()`)                                                                    | grep confirmed            |
| P6 — DeFi orchestrators     | `recursive_loop_orchestrator.py` uses `DefiErrorCode` for 4 specific error conditions                                                      | grep confirmed            |
| Live/batch engine symmetry  | `ExecutionOrchestrator` is mode-agnostic; `BatchMatchingEngine`/`LiveMatchingEngine` inject same `MatchingEngine` protocol                 | code read                 |
| A6 execution-layer symmetry | A6 BATCH_ONLY gaps are in MTDS market-data adapters, not execution adapters                                                                | A6 summary confirmed      |
| DeFi batch simulation       | Batch mode routes DeFi via MEL AMM simulator (correct "batch = live" architecture)                                                         | code read                 |
| P2/P3/P4/P5                 | N/A — leaf execution service                                                                                                               | 0 `record_*` hits         |
| Writegate Phase 6.7         | `ExecutionOrchestrator._submit_orders_with_timing()` uses `publish_with_policy()` emission gate for `order_intent` + `fill_confirmation`   | `orchestrator.py:286-305` |

---

## A6 execution-layer clarification (for D7 plan)

The task description references A6's 13 BATCH_ONLY cells (aster, deribit, hyperliquid among execution-facing venues).
This C8 audit confirms:

| A6 BATCH_ONLY venue                                                    | Execution adapter status                                                   | Live execution path                                                          |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| aster (liquidations, trades)                                           | `AsterConnector` in `defi_execution/protocols/aster.py`                    | Live: `classify_venue_error()` ✅; live order execution via `_place_order()` |
| deribit (trades)                                                       | `DeribitCCXTAdapter` in `trade_execution/adapters/deribit_ccxt.py`         | Live: CCXT adapter wired; `classify_venue_error()` ⚠ GAP (C8-P0-1)           |
| hyperliquid (book_snapshot_5, derivative_ticker, liquidations, trades) | `HyperliquidCCXTAdapter` in `trade_execution/adapters/hyperliquid_ccxt.py` | Live: CCXT adapter wired; `classify_venue_error()` ⚠ GAP (C8-P0-1)           |

**The A6 BATCH_ONLY cells are MTDS market-data gaps, not execution gaps.** The execution-service already has live
order-routing adapters for aster, deribit, and hyperliquid. The D7 plan should target MTDS live-mode WebSocket handlers,
not execution adapters.

---

## Known-findings reconciliation

From task description known findings:

| Finding                                                                                     | Status                                                                                                  | Detail                                     |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| C3: 12 CCXT adapters missing `classify_venue_error()` (uses `UNKNOWN_VENUE_ERROR_RECEIVED`) | CONFIRMED AND REFINED — 7 CCXT trade adapters + 1 Polymarket sports = 8 confirmed gaps                  | C8-P0-1 (CCXT trade), C8-P1-2 (Polymarket) |
| A6: 13 BATCH_ONLY cells including aster/deribit/hyperliquid                                 | CLARIFIED — execution-service HAS live adapters for these venues; A6 gaps are in MTDS market-data layer | See A6 table above                         |
| C3: Deribit connector fetches tick_size/contract_size from live API                         | CONFIRMED CARRY-FORWARD — C8-P1-3                                                                       | `venues/deribit_orders.py:505-506`         |

---

## QG-ratchet phase

### Phase Q — QG enforcement gaps for execution-service → adapter contract

| Pattern                                | QG script                                       | Status in execution-service QG                                                                  |
| -------------------------------------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| P6 — Error classification (CCXT gap)   | `no_adapter_contract_regression.sh` (STEP 5.83) | **WIRED — but CCXT adapters are below ratchet floor (floor=0 calls → no trigger)**              |
| P6 — DeFiAdapter retry classification  | No specific QG step                             | **GAP — add AST check for bare `except Exception` in retry loops without classify_venue_error** |
| P1 — SSOT URL (connectivity constants) | `no_hardcoded_venue_urls.sh`                    | **NOT wired in execution-service QG** (see C3)                                                  |
| P7 — Bucket SSOT                       | `check_inline_bucket_uri.py` (STEP 5.69)        | **WIRED via base-service.sh — pre-existing violations in ratchet baseline**                     |

**Gap action for CCXT P6**: STEP 5.83 ratchets on `classify_venue_error` count per file. CCXT adapters were created
without `classify_venue_error()`, so the ratchet floor is 0 — meaning existing gaps are within the current ratchet and
do not trigger a QG failure. To enforce compliance: (a) add `classify_venue_error()` calls to all 7 CCXT adapters, (b)
update the STEP 5.83 ratchet baseline to require ≥1 call per file.

**Gap action for DeFiAdapter**: Add a QG check that scans retry loops in `defi_adapter.py` for the presence of
`classify_venue_error()` or `DefiErrorCode` routing logic. This can be a simple
`rg 'except Exception' --include defi_adapter.py` + verify `classify_venue_error` appears.

---

## Continuous-verification column

| Pattern                               | Continuous-verification path                                      | Cadence                 | Last verified           |
| ------------------------------------- | ----------------------------------------------------------------- | ----------------------- | ----------------------- |
| P6 — Engine error classification      | `no_adapter_contract_regression.sh` (STEP 5.83)                   | every push              | 2026-05-20 (QG wired)   |
| P6 — CCXT adapter gap                 | **NONE — not covered by ratchet**                                 | **GAP**                 | —                       |
| P6 — DeFiAdapter retry classification | **NONE**                                                          | **GAP**                 | —                       |
| P6 — Native adapters (healthy)        | `no_adapter_contract_regression.sh` (STEP 5.83)                   | every push              | 2026-05-20 (QG wired)   |
| P6 — Sports adapters (healthy)        | `no_adapter_contract_regression.sh` (STEP 5.83)                   | every push              | 2026-05-20 (QG wired)   |
| Live/batch path symmetry              | Mode-agnostic `ExecutionOrchestrator` + injected `MatchingEngine` | every backtest/live run | 2026-05-20 (code audit) |
| Writegate Phase 6.7                   | `publish_with_policy()` gates in `ExecutionOrchestrator`          | every order submission  | 2026-05-20 (confirmed)  |

---

## Phased execution DAG

```
Phase 1 — C8-P0-1: Add classify_venue_error to 7 CCXT adapters
   │  Add _extract_ccxt_code() helper in ccxt_common.py
   │  Each adapter except block: classify + emit ADAPTER_FETCH_FAILED
   │
   ├── Phase 2 — C8-P0-2: DeFiAdapter retry classification
   │  Route FAIL/RETRY/SKIP from classify_venue_error in retry loop
   │  Add SKIP_class early-return to execute_instruction()
   │
   ├── Phase 3 — C8-P1-1: IbkrTradFiAdapter classify_venue_error
   │  Lower priority — TradFi not on May-23 DeFi critical path
   │
   ├── Phase 4 — C8-P1-2: Polymarket classify_venue_error
   │  One callsite per except block; prediction track
   │
   └── Phase Q — QG ratchet floor update
      Raise CCXT adapter ratchet floor from 0 → ≥1 in STEP 5.83
      Add DeFiAdapter retry-loop check

Phase D — Codex SSOT update after Phase Q
```

**Foundation-completion-gate**: C8-P0-1 is the critical path for May-23 DeFi live trading. The DeFi hedge leg
(carry_staked_basis) routes through `HyperliquidCCXTAdapter` and potentially `DeribitCCXTAdapter`. Unclassified RETRY
errors on these adapters in live trading means lost retry opportunities and incorrect FAIL propagation to the
orchestrator.

---

## Scope exclusions

- **P1 (SSOT-owned reference)**: Connectivity URL constants (`_BINANCE_BASE_URL` etc.) are not IS violations per C3
  verdict. Deribit `tick_size`/`contract_size` live API fetch IS a violation — carried forward as C8-P1-3.
- **P2 / P3 / P4 / P5**: execution-service is a leaf execution service. All N/A. Verified clean with 0 `record_*` hits
  in non-test source.
- **A6 BATCH_ONLY cells in execution-service**: No execution-layer BATCH_ONLY gaps found. The 13 A6 cells are MTDS
  market-data adapter gaps.

---

## Temporary states + their canonical follow-up plans

- CCXT adapters lack `classify_venue_error()` — pre-existing since adapter creation. Remediation target: Phase 1 of this
  plan. Named successor: `execution_adapter_contract_remediation_<date>.md` (TBD — to be created under D6 plan).
- `DeFiAdapter` retry loop classifies no errors — pre-existing design. Successor: same D6 plan.
- TradFi IBKR adapter bare except — pre-existing. Successor: TradFi epic `epics/tradfi_master.md`.
- Polymarket `classify_venue_error()` gap — pre-existing. Successor: Predictions epic `epics/predictions_master.md`.

---

## Codex SSOT updates required

- `/codex/04-architecture/defi-execution-overview.md`: add section on `DeFiAdapter` retry logic and requirement to route
  `FAIL`/`RETRY`/`SKIP` via `classify_venue_error()` before retrying. Cross-ref `DefiErrorCode` taxonomy.
- `/codex/04-architecture/defi-execution-overview.md`: clarify that A6 BATCH_ONLY gaps are in MTDS (market-data layer),
  not execution-service. Execution already has live adapters for aster/deribit/hyperliquid.
- `codex/06-coding-standards/` (adapter conventions): document that CCXT adapters MUST call
  `classify_venue_error(self.venue_name, _extract_ccxt_code(exc))` in every except block — `ccxt.BaseError` and
  subclasses are not exempt.

---

## Cross-references

- C3 (IS→execution): `plans/audit/is_execution_contract_audit_2026_05_20.md` — 3 P0 findings
- A6 (batch-live parity): `plans/audit/results/batch_live_adapter_parity_2026_05_20_summary.md` — 13 BATCH_ONLY cells
  (MTDS layer)
- D6 (strategy + execution plan): `plans/active/` — TBD, consumes C5/C6/C7/C8
- D7 (live adapters plan): `plans/active/` — TBD, consumes C4/C8 live-mode rows
- Bucket SSOT canonicalisation plan: `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`
- TradFi epic: `plans/epics/tradfi_master.md`
- Predictions epic: `plans/epics/predictions_master.md`
- Mega-audit progression: `plans/active/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md`
