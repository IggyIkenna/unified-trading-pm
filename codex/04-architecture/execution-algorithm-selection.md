---
doc_type: codex-ssot
title: Execution-algorithm selection — InstructionType taxonomy + selector contract
summary:
  "The InstructionType -> execution-algorithm taxonomy execution-service's select_algorithm() implements: which algos
  are valid per instruction type, the default per type, the ghost (declared-but-unimplemented) algorithms, and the
  manual-trading vs canonical-selector algo universes. Replaces the nonexistent UNIFIED_EXECUTION_DELTA.md that
  selector.py previously cited (F37)."
status: current
nature: ssot
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-api-contracts]
scope: [engineer, admin]
tags: [execution, algo-selection, instruction-type, ssot, capability-wizard]
related:
  [
    /plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md,
    /codex/04-architecture/execution-policy.md,
    /codex/04-architecture/paper-vs-live-execution-seam.md,
  ]
created: 2026-07-30
authoritative_for:
  [
    InstructionType -> valid execution-algorithm set,
    execution-algorithm selector default-per-type,
    ghost (unimplemented) execution-algorithm declarations,
    manual-trading vs canonical-selector algo universe split,
  ]
referenced_by: []
owner:
last_reviewed: 2026-07-30
code_refs:
  [
    execution-service/execution_service/algorithms/selector.py,
    execution-service/execution_service/utils/instruction_type.py,
    execution-service/execution_service/adapters/algorithm_factory.py,
    execution-service/execution_service/api/manual_instruction_helpers.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/algo_compatibility.py,
  ]
---

# Execution-algorithm selection — InstructionType taxonomy + selector contract

**Why this doc exists**: `execution_service/algorithms/selector.py` cited a doc named `UNIFIED_EXECUTION_DELTA.md` as
its taxonomy SSOT, but that file has never existed anywhere in the workspace — the selector code was the de-facto SSOT
with no written contract behind it (finding **F37**, `capability_wizard_analysis_findings_2026_06_11.md`). This doc is
that written contract, and the code now cites it instead.

## 1. InstructionType is the selection axis, not domain/venue

`execution_service/utils/instruction_type.py` classifies every instruction into one `InstructionType`
(`unified_api_contracts.internal.domain.execution_service.types.InstructionType`) via `infer_instruction_type` /
`infer_instruction_type_from_operation`:

| InstructionType   | Classified from                                                             |
| ----------------- | --------------------------------------------------------------------------- |
| `TRADE`           | CLOB venue (Binance, Hyperliquid, CME, …) — `CLOB_VENUES`                   |
| `SWAP`            | DEX venue (Uniswap, Curve, …) — `DEX_VENUES`; LP-provision instrument types |
| `ZERO_ALPHA`      | Lending/staking venue or op (LEND/BORROW/STAKE/…) — `ZERO_ALPHA_VENUES`     |
| `OPTIONS_COMBO`   | Options-combo instrument / operation                                        |
| `FUTURES_ROLL`    | Dated-future roll instrument / operation                                    |
| `PREDICTION_BET`  | Prediction-market bet                                                       |
| `SPORTS_BET`      | Sportsbook bet                                                              |
| `SPORTS_EXCHANGE` | Sports-exchange bet                                                         |

`ALGORITHMS_BY_INSTRUCTION_TYPE` (`selector.py`) is the closed valid-algo set per type; `DEFAULT_ALGORITHM` is the
selector's default per type when no algo is requested/configured. `select_algorithm()` is a 4-step priority chain: (1)
`ZERO_ALPHA` always forces `BENCHMARK_FILL`; (2) an explicitly requested algo is honored IFF valid for the type, else
falls through with a warning (never raises); (3) a config algo likewise; (4) else the type's default.

UAC's `unified_api_contracts.internal.architecture_v2.algo_compatibility` module transcribes this table declaratively
(`ALGOS_BY_INSTRUCTION_TYPE`, `DEFAULT_ALGO_BY_INSTRUCTION_TYPE`) so the capability wizard / verdict matrix can render +
block algo mismatches without a service-to-service import. Keep the two in sync when either changes.

## 2. Ghost algorithms — declared valid, no implementation class (F35)

`SEQUENTIAL_LEGS` (`OPTIONS_COMBO` default), `SPREAD_ROLL` (`FUTURES_ROLL` default), `BEST_PRICE` / `KELLY_STAKE`
(bet-type defaults) are valid selector outputs with **no `ExecAlgorithm` implementation class** in
`execution_service/algo_library/`. `BENCHMARK_FILL` (a mode flag, not a class) and `MAX_SLIPPAGE` (a matching-engine
order type, not an `ExecAlgorithm`) are likewise not real algorithm classes. This is intentional, honest taxonomy —
options/futures-roll/bet-type v2 engines are not registered today (see the verdict-matrix `not_registered(no_v2_engine)`
gate, `capability_wizard_analysis_findings_2026_06_11.md` F48), so nothing currently resolves these instruction types to
a live order. If a caller ever DOES route one of these instruction types through
`ExecutionOrchestrator.execute_instruction`, `algorithm_factory.get_algorithm()` returns `None` and the orchestrator
raises `ValueError("Unknown algorithm: ...")` — a fail-loud gap, not a silent misexecution. Building the real algorithm
classes is future strategy-service-scoped work, tracked separately; this doc's job is only to keep the gap honestly
declared (mirrors UAC's `EXECUTION_ALGOS[key].implemented` flag).

## 3. ICEBERG — two legitimate, separate algo universes (F33)

`ALGORITHMS_BY_INSTRUCTION_TYPE[TRADE]` deliberately excludes `ICEBERG` — the selector's own comment: "cannot be
realistically backtested (requires queue position modeling)". This exclusion is scoped to the **canonical,
automated/backtest-driven selector path** (`select_algorithm()`), which strategy-config-driven TRADE/SWAP instructions
resolve through and which the offline backtest harness must be able to simulate fills for.

`ICEBERG` remains legitimately available on two OTHER paths that never touch backtest-fill simulation, because it has a
real, working implementation (`execution_service/algo_library/algorithms/iceberg.py::IcebergAlgorithm`):

- **Manual/discretionary trading** — `execution_service/api/manual_instruction_helpers.py::_SUPPORTED_ALGOS` lists it
  for the manual-instruction API's algo-discovery endpoint. A human operator placing a live manual order gets a REAL
  fill from the exchange, not a simulated one — the backtest-realism concern does not apply.
- **The construction factory** — `execution_service/adapters/algorithm_factory.py::AlgorithmFactory._ALGO_MAP` can build
  a real `IcebergAlgorithm` instance from an `IcebergConfig` for any caller (manual path, future live-wiring) that needs
  one.

**This is not a bug to reconcile by adding/removing ICEBERG from one list to match another** — it is two distinct,
correctly-scoped universes: (a) the canonical, backtest-safe selector for automated strategy config, and (b) the
manual/live real-fill algo menu. A future change that wires `AlgorithmFactory` into the automated
`ExecutionOrchestrator.execute_instruction` path MUST NOT let `ICEBERG` reach a backtest run through that door — gate
any such wiring on `execution_mode != backtest`, or add ICEBERG to `ALGORITHMS_BY_INSTRUCTION_TYPE[TRADE]` only once a
queue-position-aware backtest fill model exists for it.

## 4. Naming — one algorithm, one canonical name (F34)

`AlgorithmFactory._ALGO_MAP` (the algo-library construction path) and `selector.py`'s `ALGORITHMS_BY_INSTRUCTION_TYPE`
(the canonical InstructionType path) independently named the smart-order-router differently: `"sor"` (factory, lowercase
generic) vs `"SMART_ORDER_ROUTER"` (selector, canonical). `AlgorithmFactory._ALGO_MAP` now carries BOTH keys (`"sor"`
kept for back-compat, `"smart_order_router"` added as the canonical alias — both resolve to `SORAlgorithm`), so a caller
that forwards `select_algorithm()`'s output straight into `AlgorithmFactory.create()` works without a translation layer.
New algo keys added to either registry should use the canonical UPPERCASE selector name as the primary identity;
`AlgorithmFactory.create()` already lowercases before lookup, so casing itself was never the issue — only the divergent
word choice was.

## 5. Dead code removed (F36)

`execution_service/engine/live/algo_selector.py::AlgoSelector` applied a quantity-threshold heuristic (`>=10` -> `TWAP`
else `MARKET`) that ignored `InstructionType` entirely. It was never instantiated anywhere in production code (confirmed
via repo-wide grep, zero call sites besides its own module and the package `__init__.py` re-export) and had zero test
coverage. Deleted 2026-07-30 rather than fixed in place — a bypass of the canonical selection contract with no live
callers is dead code, not a live contradiction to reconcile (workspace HARD RULE: delete deprecated code, no shims).

## 6. Change discipline

Any new `InstructionType`, algorithm key, or default MUST be added to BOTH `execution_service/algorithms/selector.py`
(the runtime SSOT) AND `unified_api_contracts.internal.architecture_v2.algo_compatibility` (the declarative
transcription the capability wizard reads) in the same change — the two are intentionally duplicated (service-to-service
imports are banned), not derived from one another.
