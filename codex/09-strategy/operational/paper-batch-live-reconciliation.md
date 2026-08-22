---
doc_type: codex-ssot
title: Paper ⟷ Batch ⟷ Live Reconciliation — the Determinism Spine
summary:
  The determinism-spine SSOT for trade-by-trade paper↔batch↔live reconciliation — paper(W) MUST equal batch-rerun(W)
  (ε=0 PROOF, any diff is a bug), live↔paper delta IS execution alpha; specifies the four as-if-filled ledgers, the
  two-fill-realities model, the RunManifest as-of snapshot, reconcile_day, and the G1-G5 gap list.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    e2e-testing,
    execution-service,
    features-service,
  ]
scope: [engineer, admin]
tags: [reconciliation, determinism, ledger, live-trading, backfill, execution, defi]
related:
  [
    /codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md,
    /codex/09-strategy/operational/cli-promote-paths.md,
    ../../04-architecture/global-ledger-architecture.md,
    ../architecture-v2/cross-cutting/pnl-attribution.md,
  ]
created: 2026-06-19
authoritative_for: [
    paper↔batch↔live determinism spine (trade-by-trade reconciliation + four as-if-filled ledgers + two-fill-realities
    model),
  ]
referenced_by:
  [
    /codex/02-data/live-data-persistence-and-event-log.md,
    /codex/04-architecture/multi-mode-wallet-isolation.md,
    /codex/04-architecture/trading-agent-service-directive-pipeline.md,
    /codex/08-workflows/t1-batch-dag.md,
    /codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md,
    /codex/09-strategy/operational/cli-promote-paths.md,
    /plans/archive/2026_08/multi_leg_execution_systems_execution_2026_08_10.md,
  ]
owner:
last_reviewed: 2026-06-22
code_refs:
---

# Paper ⟷ Batch ⟷ Live Reconciliation — the Determinism Spine

> **Status**: partially shipped (G3/G4/G5 DONE; G1/G2/G6 open — G6 newly found 2026-08-21, see § 7 for detail).
> Plan-of-record:
> `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md` (parent epic `batch_live_symmetry_master`).
> Composes with `/codex/04-architecture/global-ledger-architecture.md`,
> `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`,
> `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`, and the existing aggregate recon
> (`/codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md`). This doc is the SSOT for the
> **trade-by-trade** extension and the **as-if-filled ledger**.
>
> **owner**: vm-cross-cutting · **cadence**: per-paper-run (daily ledger) + T+1 (daily recon) · **verifier**:
> `reconcile_day` determinism verdict + the daily ledger digest · **last_executed**: `paper-20260620002237-378a3735`
> (2026-06-20 — real 7-day `carry_staked_basis` run, 7 instructions / 21 fills, ε=0 determinism verified)

---

## 0. The operator invariant (the thesis)

> "If we paper-trade 19→26 and then backtest 19→26, **every trade in the backtest should also say we did it** — the only
> diff being execution fills. And if our execution assumptions in paper differ from batch, **that's bad**." — operator,
> 2026-06-19.

The three trading modes are **the same program**. The decision path (`V2EngineOrchestrator.on_tick()`) is already shared
across batch / paper / live (the workspace "Batch = Live" HARD RULE). The operator's ask extends that identity **through
the fill and into the ledger**:

- **`paper(W)` MUST equal `batch-rerun(W)` trade-for-trade.** Same code + same inputs + same fill model ⇒ byte-identical
  instructions AND fills. The paper↔batch reconciliation is therefore a **determinism PROOF, not a tolerance check** —
  any non-zero diff is a **bug** (one of: non-determinism in the decision path, an input-capture gap, or fill-model
  drift), never "within threshold".
- **Corollary — PAPER ALWAYS CONSUMES THE LIVE MARKET-DATA FEED, never a testnet feed (operator ruling
  2026-08-19).** Testnet is a paper _execution_ sub-mode: it changes where orders go, never where prices come from.
  A testnet market-data feed is a different price series from live, so paper run against it could not reconcile
  against a batch rerun over live history — the determinism proof above would fail by construction, and the
  `live↔paper` delta would stop measuring execution quality and start measuring feed divergence. Where a venue
  offers a testnet data feed, it is **still not** the paper input. This is what makes "testnet is a sub-mode of
  paper" coherent rather than a fourth mode.
- **The only intentional divergence lives at the LIVE fill boundary.** Live introduces real venue fills (real slippage /
  fees / partials / latency); the **`live↔paper` delta IS the execution-quality measurement** (alpha decay), expected
  non-zero — not a bug.
- Therefore the full chain **decomposes**:

  ```
  live − batch  =  (paper − batch)        +  (live − paper)
                   └ determinism: ≈ 0 ┘      └ execution alpha ┘
                      a BUG if not 0           the measurement we want
  ```

  Reconciling live→paper→batch is the same as reconciling live→batch, with the determinism leg isolated so a real
  execution gap can never hide behind a simulation gap (the exact failure the operator named).

This is the spine: **make paper and batch provably identical, and the only thing left to measure is how well live
executes against that shared simulation.**

---

## 1. What "Citadel-grade paper trading" means (the complete state)

A paper run over a window must produce, for every tick and as an end-state, the **complete** book — not just a desired
target. The operator's list maps onto four ledgers + their derived views:

| Operator ask                                              | Where it lives                                                                             |
| --------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **All money movements**                                   | `InstructionLedger` + `TreasuryLedger` (LedgerRow `event_type` ∈ TRADE/TRANSFER/DEPOSIT/…) |
| **Balances** (per venue/instrument/share_class)           | `PositionLedger` = `Σ delta GROUP BY (account, asset, venue, instrument)`                  |
| **P&L**                                                   | derived from `PositionLedger` marks + realised closes (`PnLFactor` waterfall)              |
| **PnL attribution**                                       | `PnLAttributionRow` (factor × layer × venue × instrument × strategy)                       |
| **Venues / instruments breakdown**                        | `InstrumentRecord` join on `instrument_key`; balances/PnL grouped by venue + instrument    |
| **Historical trade ledger** ("eyeball the trades we did") | `InstructionLedger`, append-only                                                           |
| **Positions ledger** ("update as if filled")              | `PositionLedger`, the current as-if-filled state                                           |
| **Slack log**                                             | daily ledger digest + daily T+1 recon verdict → alerting-service                           |

The two operator-facing ledgers are **`InstructionLedger`** (the historical trade tape) and **`PositionLedger`** (the
live as-if-filled positions/balances). `PassiveLedger` (funding / staking / lending accruals) and `PricingLedger`
(marks) feed PnL but are not the primary eyeball surfaces.

---

## 2. The existing system — what we build ON (EXISTS)

**The decision path is already shared** (the foundation the whole design rests on):

| Mode           | Entry point                                                                             | Calls                            |
| -------------- | --------------------------------------------------------------------------------------- | -------------------------------- |
| batch (grid)   | `strategy-service/scripts/run_2yr_config_grid_backtest.py` → `V2BatchHarness.on_tick()` | `V2EngineOrchestrator.on_tick()` |
| batch (proper) | `strategy_service/engine/backtest/runner.py` `GroupBRunner._process_tick()`             | `V2EngineOrchestrator.on_tick()` |
| paper / live   | `strategy_service/colocated_engine.py` `StrategySupervisor` → `ClientWorker`            | `V2EngineOrchestrator.on_tick()` |

Same stateless orchestrator, same `on_tick` signature — **the instructions are already identical across modes given
identical inputs.** The divergence is entirely downstream (fills + ledger).

**Canonical data model (UAC) — all EXISTS:**

- `unified_api_contracts.canonical.crosscutting.ledger.LedgerRow` (57-field frozen model; `_ledger_row.py`) + 4 aliases
  `InstructionLedger` / `PassiveLedger` / `TreasuryLedger` / `PricingLedger` + 5 StrEnums (`EventOrigin`, `EventType`
  [39 in code — taxonomy doc stale at 37, missing `COLLATERAL_POSTED` + `MARGIN_RELEASED`], `AssetClass` [17],
  `Direction` [12], `OptionRight` [2]). `CrossClientTransferForbiddenError` raised at construction.
- `PnLAttributionRow` / `PnLAttribution` + `PnLFactor` (DELTA/FUNDING/BASIS/CARRY/FEES/SLIPPAGE/…) + `PnLLayer`
  (STRATEGY/EXECUTION) — `unified_api_contracts/internal/risk.py:943`. Emitter
  `unified_trading_library/pnl_attribution/emitter.py:76` (writes parquet to `client-reports`).
- HWM — three simultaneous methods (TWR / Notional / PnL-recovery): `HighWaterMarkLedgerRow`
  (`internal/domain/hwm_ledger.py:40`), invariants `unified_trading_library/post_trade/hwm_invariants.py`, seeds
  `client-reporting-api/core/hwm_seeds.py`. **Never `max(equities)`** (CLAUDE.md HARD RULE).
- Wallet hierarchy keyed by `share_class` (`/codex/04-architecture/wallet-hierarchy-and-capital-flow.md`).
- `InstrumentRecord` + per-venue enumeration (`instruments_service/engine/orchestrator/venue_core.py:227`); canonical
  `instrument_key = VENUE:INSTRUMENT_TYPE:SYMBOL`.

**Canonical SSOT derivation — never hand-threaded metadata maps (HARD RULE, operator 2026-06-19).** The spine integrates
via the canonical UAC/UTL SSOT, NOT a bolt-on. Every fill carries the canonical `instrument_key`
(`VENUE:INSTRUMENT_TYPE:SYMBOL`, built by the engine via the UAC `instrument_type_for_action` SSOT — the instrument type
is intrinsic to the action), and the ledger writers DERIVE the ledger asset identity from it:
`derive_ledger_asset_fields(instrument_key)` → `(asset_symbol, asset_canonical_id, asset_class)` where
`asset_class = asset_class_for_instrument_type(InstrumentType)` (the `InstrumentType → LedgerAssetClass` SSOT). All
three live in UAC `internal/reference/ledger_asset_resolution.py` (`asset_class_for_instrument_type` /
`instrument_type_for_action` / `derive_ledger_asset_fields`). **BANNED on the spine**: threading
`instrument_type_of`/`asset_symbol_of`/`asset_canonical_id_of`/`asset_class_of` dicts through `write_run_ledger` /
`write_paper_run` / `rerun_from_manifest` / `ledger_emit`, a hardcoded `_DEFAULT_INSTRUMENT_TYPE`, or any per-caller
metadata map the canonical `InstrumentKey`/`InstrumentRecord`/registry can derive. `BenchmarkFillRecord.instrument_key`
is REQUIRED (no empty-string default — a blank key is a determinism-spine bug). Shipped 2026-06-19:
`unified-api-contracts@f8e87a8` (the SSOT) + `unified-trading-library@944ea341` (run_writer derives) +
`strategy-service@c90dab73` (engine + ledger_emit/paper_run_emit/batch_rerun) + `client-reporting-api@669fd4d` +
`e2e-testing@151d5a1` (the ε=0 proof still green on the canonical shape). Future strategies + agents build on the main
infra, not on a re-invented local dict.

**Execution + fill machinery — EXISTS (but divergent, see §3):**

- `colocated_engine.py` paper/live shell: `SharedState.positions` (qty/avg_price/realized_pnl per instrument), realised
  - unrealised + funding + interest PnL via `strategy_service.pnl.engine.breakdown.compute_pnl_breakdown()`, async
    `GCSSink` parquet flush (fills/positions/pnl/transfers, 60 s). Paper vs live differ ONLY in the fill provider
    (`benchmark`/`tenderly`/`solana-devnet` vs `copper`/`local_key`).
- `strategy_service/engine/backtest/benchmark_fills.py` `BenchmarkFillEngine.settle()` (TWAP/VWAP/PASSIVE_BBO/
  ARRIVAL_MID/POOL_MID_AT_BLOCK/FUNDING_SNAPSHOT/LIQUIDATION_BONUS per `BenchmarkFillMode`).
- `execution-service` `PaperMatchingEngine` (real AMM curve math + slippage gates) / `LiveMatchingEngine` (real venue
  adapters) / `GasCostModel` / `pnl_calculator.py`.

**Reconciliation + Slack + data — EXISTS:**

- `batch-live-reconciliation-service` — T+1 pipeline, **stage 3b** (paper-vs-live) + **stage 3c** (batch-vs-paper).
  `ReconReport` / `StageReport` / `DeviationRecord` (`models/recon_report.py`). **Aggregate only** — date-level averages
  (`alpha_pnl_gap`, `fill_rate_delta`, `slippage_delta_bps`); the event files carry **no trade identity**, and
  `DeviationRecord.instrument_id` is always `None`.
- Slack via **alerting-service** (`notifiers/slack.py` `send_message` + `core/slack_dispatcher.py`
  `build_slack_blocks(AlertEvent, dashboard_url)`; `#uts-live-alerts` webhook). A new harness POSTs an `AlertEvent` to
  alerting-service (no cross-service Python import).
- GCS market data immutable per day; features carry `feature_group_version` hive key → **point-in-time replay is
  achievable** but must be explicitly pinned. `DATA_SOURCE=gcs_complete` (strategy-service `config.py:506`) reads dumped
  canonical GCS data instead of live snapshots.

---

## 3. The five gaps that break the invariant (the design targets)

| #      | Gap (MISSING / divergent today)                                                                                                                                                                                                                                            | Why it breaks the invariant                                                                                                                                          |
| ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **G1** | **THREE divergent fill models**: APY-haircut (`run_2yr_config_grid_backtest.py:453`, `slippage_cap_bps*4/365`) vs `BenchmarkFillEngine` (Group B) vs `PaperMatchingEngine` (real AMM). Paper and batch use **different** fill code.                                        | This is **exactly** the "paper sim ≠ batch sim" bug the operator named. paper↔batch can never be identical while two fill engines exist.                             |
| **G2** | **No per-trade identity in execution events** — each event line is a float-metric dict (`realized_pnl`, `fill_rate`, `slippage_bps` AVERAGES); no `order_id`/`client_order_id`/`instrument_key`/`timestamp`.                                                               | Trade-by-trade matching is impossible; recon can only average. The operator wants to "eyeball every trade".                                                          |
| **G3** | **Ledgers unmaterialised** — no `PositionLedger` schema/writer; no `InstructionLedger` writer from fills; no `PassiveLedger` synthesiser; `realized_pnl` hardcoded `"0.00"` (`client-reporting-api attribution.py:189`); balances come from CCXT snapshots, not `Σ delta`. | There is no complete as-if-filled ledger to eyeball or reconcile; "balances/PnL/attribution" are mock or absent.                                                     |
| **G4** | **No point-in-time input capture / as-of snapshot** — no run manifest records which event files, feature versions, and code shas the paper run consumed.                                                                                                                   | A batch rerun might read revised data / a different feature version → a **spurious** paper↔batch diff that looks like a determinism bug but is an input-capture bug. |
| **G5** | **Recon is aggregate + single-date** — `_compute_metrics()` is `abs(mean_a − mean_b)`; one `date: str` per call; no daily-T+1 trade-level recon; no determinism verdict (ε=0 expectation for paper↔batch).                                                                 | The harness cannot express "every trade matches" nor isolate the determinism leg from the execution leg.                                                             |

---

## 4. The target architecture (the map)

### 4.1 The determinism contract

`paper(W) ≡ batch-rerun(W)` holds **iff** all three are pinned and shared:

1. **Same code** — the run manifest pins the code shas of every repo on the decision+fill path (strategy-service,
   execution-service, UAC, UTL, features). A batch rerun checks out those shas (or asserts equality).
2. **Same inputs** — the paper run **captures its exact input stream** (the per-tick `MarketStateSnapshot` / features it
   consumed) to an immutable GCS as-of snapshot, pinned by `feature_group_version` + the raw-data day partitions. The
   batch rerun replays **that snapshot**, not "today's view of that week".
3. **Same fill model** — **one** canonical simulation fill engine, imported by BOTH batch and paper (§4.2).

Given all three, the emitted instructions AND the simulated fills are deterministic functions of the snapshot ⇒
trade-for-trade identical. This is the contract `reconcile_day` proves.

### 4.2 The fill model — three concepts, two simulated, one real (G1 — the core fix)

There are **three distinct fill concepts**, not two competing engines. Per strategy instruction (which carries its
**signal candle**):

1. **Benchmark fill — the strategy's ASSUMED fill (the yardstick).** Liquidity-adjusted, priced at the **close of the
   signal candle** that produced the instruction. Deterministic by construction (a pure function of the signal candle +
   a liquidity haircut). Strategy-service `BenchmarkFillEngine` (Group B); execution-service knows it as the reference.
   It is the reference both other fills measure against — **not** itself the booked simulation fill.
2. **Smart-matching fill — EXECUTION-SERVICE's job, and its alone ("contained and specific").** The semi-realistic fill
   the matching engine produces, with realism bounded by the **market-data fidelity** of the window: OHLCV (just the
   candle → ≈ benchmark) → BBO (top of book) → L2 depth → trades tape → full L3 market-by-order (most realistic).
   Execution-service **"benchmarks around"** the benchmark: **execution alpha = smart_fill − benchmark**. Paper books
   this via `PaperMatchingEngine`; batch MUST book it via the SAME execution-service matching (Group C) on the same
   data.
3. **Real venue fill — live only** (`LiveMatchingEngine`). `live execution alpha = real_fill − benchmark`.

Plus **rate-matching** for DeFi yield legs (Aave / Compound / Lido / staking): the "fill" is the observed lending /
staking **rate accrual** (priced 1.0 + the rate captured separately), not order-book matching.

**The determinism requirement:** paper and batch run the **same benchmark (1) AND the same execution-service smart
matching (2)** on the same data ⇒ identical fills. The ONLY intentional divergence is **live swapping (2) for real venue
fills (3)**.

**The actual G1 gaps** (corrected 2026-06-19 per operator):

- **Batch must run the same smart matching as paper.** Today batch (`GroupBRunner`) stops at the **benchmark** and does
  NOT run execution-service's Group C smart matching — so batch ≠ paper (paper has the smart-matching layer, batch
  doesn't). **Completing `GroupCRunner` (P1.4) is the linchpin** — it gives batch the same matching layer paper has.
  (NOT "make paper drop to the benchmark" — paper's `PaperMatchingEngine` is correct.)
- **The benchmark reference must agree** across strategy-service `BenchmarkFillEngine` and the execution-service
  `v2/benchmark_fills` registry — unified to one UAC pricing SSOT (P1.1, shipped). A `PASSIVE_BBO` convention divergence
  exists at the benchmark layer (strategy-service LONG→ask vs UAC buy→bid) — a latent edge mode since the benchmark is
  normally the signal-candle close, but a real drift to correct.
- **Retire the APY-haircut shortcut** in the grid script — it is a crude per-day haircut, not the benchmark and not the
  smart matching; the grid must run the real `GroupBRunner` + `GCSFeatureProvider` path on real GCS data (P1.3).

> **Design rule (new HARD RULE candidate):** there are exactly **two fill REALITIES** — the **simulated** path
> (benchmark `BenchmarkFillEngine` + execution-service smart matching, used IDENTICALLY by batch AND paper) and **real
> venue fills** (`LiveMatchingEngine`, live only). The benchmark is the shared reference both realities measure against,
> never a third reality. A third _simulation_ on the batch/paper path — or batch and paper using _different_ matching
> engines — is review-blocking (it re-creates the divergence).

### 4.2.1 Multi-leg (`LEADER_HEDGE`) sequencing — a named, checkable invariant (2026-08-10)

**The invariant.** Every multi-leg instruction with an inter-leg dependency — `AtomicExecutionMode.LEADER_HEDGE`
(leader-first → hedge(s) within deadline → compensate on failure) — MUST be settled in paper/batch through the SAME
leader/hedge/unwind sequencing semantics the live executor uses (`execution-service` `v2/atomic_leg_executor.py`
`AtomicLegExecutor.execute()`), with benchmark-simulated fills (the IBKR-MEL synthetic-adapter shape: same sequencing,
real vs synthetic source). A flat per-leg loop that prices each leg independently — the pre-2026-08-10 behavior of
`BenchmarkFillEngine.settle()` — is a determinism-spine defect: it silently fills both legs with no model of sequencing
risk, so an **unhedged position** (the exact failure multi-leg execution exists to avoid) is invisible in paper/batch
results. A _parallel_ leader/hedge model inside the benchmark engine is equally a violation — a second implementation of
safety-critical sequencing semantics that diverges from the live executor and breaks `paper(W) == batch-rerun(W)` (audit
verdict 2026-08-10: option (a), route benchmark settlement through the real sequencing; (b) REJECTED; SSOT
`/plans/archive/2026_08/multi_leg_execution_systems_execution_2026_08_10.md`).

**The mechanism (strategy-service `engine/backtest/benchmark_fills.py`).** `BenchmarkFillEngine.settle()` →
`compute_benchmark_fill` → `_compute_atomic_fill` (`:546`) branches on `execution_mode`:

- **`LEADER_HEDGE`** → `_compute_atomic_leader_hedge_fill` (`:476`): the leader leg fills FIRST; each hedge leg must
  have usable `MarketStateSnapshot` data (missing/invalid state = the deterministic model of a failed/timed-out hedge
  fill — no `KeyError`, no silent both-leg fill). On any hedge failure the `compensation_policy` fires:
  `CLOSE_LEADER_IF_HEDGE_FAILS` unwinds the now-naked leader at a 50 bps penalty (`_compute_unwind_fill` `:440`,
  `_UNWIND_PENALTY_BPS` `:69`); `HOLD_LEG_AND_ALERT` / `RETRY_HEDGE_UNTIL_DEADLINE` leave the leader open — the naked
  position visible as a fill record missing its hedge leg. Control-plane actions (TRANSFER/BRIDGE/CANCEL/CONVERT_DUST)
  settle at zero cost in benchmark space (`_NO_FILL_ACTIONS` `:53`) — skipped, not failures.
- **`ATOMIC` / `ATOMIC_ON_CHAIN` / `SEQUENCED_WITH_PACING`** → flat per-leg loop (no inter-leg dependency; a missing leg
  is still a hard `KeyError` — batch=live demands deterministic legs).

**The checkable verification — the regression tests name the invariant
(`strategy-service/tests/unit/engine/backtest/test_benchmark_fills.py`, shipped `strategy-service@aae2ae064d` /
`11e23c5fb7` / `5a8a014eed`, 2026-08-10):**

| Test (line)                                                          | Proves                                                                                                              |
| -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `test_atomic_missing_leg_state_models_hedge_failure` (`:380`)        | LEADER_HEDGE with a missing hedge-leg snapshot → leader + 50 bps unwind fill, not `KeyError`/silent both-leg fill.  |
| `test_paper_settle_surfaces_unhedged_risk_when_hedge_fails` (`:468`) | The exact paper/batch path (`settle()`) surfaces unhedged risk when the hedge fails; deterministic across runs.     |
| `test_paper_settle_hold_leg_alert_exposes_naked_position` (`:516`)   | Under `HOLD_LEG_AND_ALERT` the naked position is exposed (leader with no hedge/unwind) — never hidden.              |
| `test_paper_batch_rerun_epsilon0_on_real_sequencing` (`:552`)        | ε=0 determinism STILL holds (keyed trade-by-trade, citadel methodology) against the REAL sequencing in both passes. |

**Live parity note.** `AtomicLegExecutor` is paper-default by construction (`create_sports_adapter(mode)` defaults to
`OperationalMode.PAPER`, `atomic_leg_executor.py:9-10`); live wires the same executor through the EventTransport spine
(`/codex/02-data/live-data-persistence-and-event-log.md`). Paper/batch settle LEADER_HEDGE via the benchmark counterpart
of that same sequencing — simulated fills, real sequencing — so `paper(W) == batch-rerun(W)` now validates the real
multi-leg risk path, not a parallel shortcut. The live publish/subscribe seam
(`strategy-service/engine/strategies/v2/live_routing.py::publish_atomic_instruction[_sync]` →
`execution-service/v2/atomic_instruction_router.py::route_atomic_instructions`) was wired into dispatch 2026-08-10
(`strategy-service@4ca4385c` / `execution-service@27a4bd59`).

### 4.3 The ledger pipeline (G3)

Every simulated (and live) fill emits a `LedgerRow`, materialising the four ledgers:

```
instruction (V2EngineOrchestrator.on_tick)
   → fill (BenchmarkFillEngine | LiveMatchingEngine)         carries order_id, instrument_key, ts, side, qty, price, fees
      → LedgerRow(event_type=TRADE, delta=±qty, price, fees) → InstructionLedger   (append-only historical tape)
      → LedgerRow(event_type=TRANSFER/DEPOSIT/…)             → TreasuryLedger      (money movements)
   accruals (funding/staking/lending, per period)            → PassiveLedger       (synthesiser — NEW)
   marks (per tick)                                          → PricingLedger
        ┌──────────────────────────────────────────────────────────────────────┐
        │ PositionLedger = Σ delta GROUP BY (account, asset, venue, instrument) │  ← derived, the as-if-filled state
        └──────────────────────────────────────────────────────────────────────┘
            → balances (per venue / instrument / share_class)
            → PnL (realised closes + unrealised marks, PnLFactor waterfall)
            → PnLAttributionRow (factor × layer × venue × instrument × strategy)
            → HWM (TWR / Notional / PnL-recovery)
```

The same writer runs in paper (benchmark fills) and live (real fills); batch produces the same ledger from a replay.

**Shipped writer seams (P10.1 / P10.2, 2026-06-21).** The TreasuryLedger leg is the UTL SSOT
`unified_trading_library.ledger.write_run_transfer_ledger` + `transfer_ledger_row` (writes
`{ledger_root}/ledger_type=transfer/{run_id}.jsonl`; capital-movement `LedgerRow`s with a money-movement `event_type` —
DEPOSIT / TRANSFER / STAKE / COLLATERAL_POSTED — a single `client_id` and `counterparty_client_id=None`, funds-isolation
HARD RULE; asset identity derived canonically from each leg's `instrument_key` via `derive_ledger_asset_fields`, no
metadata maps). `strategy-service` `engine/backtest/paper_run_transfers.py` builds the carry deploy flow (USDC deposit →
spot swap → stake → perp-margin posting) per spec and `run_paper()` writes one merged transfer ledger for the run. The
**multi-dimensional PnLAttributionRow** is produced by `engine/backtest/paper_run_attribution.py`: per held day it emits
CARRY + BASIS + FEES at the staking venue and FUNDING at the perp venue (so `by venue` ≠ `by layer`), all at
`PnLLayer.STRATEGY` (EXECUTION layer = 0 in a paper run — benchmark fills); FEES is an HONEST explicit 0 and the
price/DELTA leg is omitted (no spot-price column) rather than fabricated. The `emit_attribution_parquet` SSOT partitions
by `strategy_id` / `client_id` / `date` so per-venue + per-strategy + per-day are queryable. Verified end-to-end on run
`paper-20260621105146-e7545ddb` (8 transfer rows = 4 legs × 2 strategies; 56 attribution rows = 7 days × 4 factors × 2
strategies, 4 venues, 2 strategy_ids; batch rerun ε=0, 42 fills, 0 deviations). The client-reporting-api `/transfers`
reader still scans only `ledger_type=instruction` — pointing it at `ledger_type=transfer` is the open downstream item.
`realized_pnl` is computed (not `"0.00"`), `PositionLedger` is the materialised `Σ delta` view (not a CCXT snapshot),
and `PassiveLedger` accruals are synthesised (not dropped).

### 4.4 The run manifest (G4 — the as-of snapshot)

Each paper run writes an immutable manifest pinning everything a deterministic rerun needs:

```
RunManifest:
  run_id, window_start, window_end, mode (paper|batch|live), client_id, strategy_ids[]
  code_shas: {strategy-service, execution-service, unified-api-contracts, unified-trading-library, features-service}
  input_snapshot:
    market_data_days: [gs://…/processed_candles/by_date/day=…/pipeline_mode=…]   (immutable object refs)
    feature_group_versions: {group: N}                                            (pinned hive keys)
    captured_tick_stream: gs://…/runs/{run_id}/ticks/                             (exact MarketStateSnapshots consumed)
  fill_model: benchmark | live                                                    (which §4.2 reality)
  ledger_root: gs://…/runs/{run_id}/ledger/{instruction,passive,position,pricing}/
```

A batch rerun takes a paper run's manifest, asserts the code shas, replays `captured_tick_stream`, and writes its own
ledger under a new `run_id` with `mode=batch` + a back-reference to the paper `run_id`.

### 4.5 The reconciliation harness (G2 + G5)

A new keyed, daily-T+1 stage (`stage3d` / a standalone harness in batch-live-reconciliation-service):

```python
def reconcile_day(paper: RunManifest, batch: RunManifest, live: RunManifest | None) -> DailyReconReport:
    # match on the deterministic key: (instrument_key, strategy_instruction_id, tick_timestamp)
    # paper↔batch  → DETERMINISM verdict: expect ε = 0 on (side, qty, fill_price, fees); ANY mismatch = a bug,
    #                classified {NON_DETERMINISM | INPUT_CAPTURE_GAP | FILL_MODEL_DRIFT}
    # live↔paper   → EXECUTION verdict: per-trade fill_price_delta_bps / qty_delta / timing_delta_ms = execution alpha
    # roll up per (venue, instrument, strategy, factor); per-day totals (a week = 7 daily reports)
    # emit AlertEvent(severity=INFO|CRITICAL) → alerting-service → #uts-live-alerts
```

`DeviationRecord` gains a populated `instrument_id` + a per-trade `trade_key`. The paper↔batch verdict is binary
(deterministic or bug); the live↔paper verdict is the calibrated tolerance check that already exists
(`batch-live-reconciliation-threshold-calibration.md`), now per-trade instead of per-date-average.

> **Verified NON-finding (UTL/UAC reuse audit, 2026-07-13)**: `batch-live-reconciliation-service/models/recon_report.py`
> (`ReconReport` / `StageReport` / `DeviationRecord`, one row per pipeline stage — `config_pull` / `data_pipeline_recon`
> / `ml_recon` / `strategy_recon` / `execution_recon` / `paper_live_recon` / `batch_paper_recon`) is marked
> `SCHEMA_PROVENANCE_EXEMPT` and is CORRECT-LOCAL: these are the service's private per-stage T+1 pipeline result types,
> not a cross-service contract — the cross-service resolution-workflow contract already lives in
> `unified-internal-contracts` (`ReconciliationAgeFields` / `ReconciliationDimension`). Do not re-flag the stage-grain
> schemas as a UAC-migration candidate in a future reuse audit. SSOT:
> `plans/archive/2026_07/utl_uac_reuse_consolidation_remediation_2026_06_10.md` § Verified NON-findings.

### 4.6 Per-archetype canonical data source (P11.11) — read the real corpus, never fake

The paper engine drives each archetype's PRODUCTION engine (`factory.py`) off the data type that archetype's signal
needs, read directly from its **dedicated canonical GCS bucket** (resolved via `resolve_bucket_name` — never an inline
`gs://`). This is wiring the production engine to a second data source, NOT a fork:

| Archetype                                       | Engine                                 | Feature / data type                      | Canonical bucket (kind)   | Provider                       |
| ----------------------------------------------- | -------------------------------------- | ---------------------------------------- | ------------------------- | ------------------------------ |
| `CARRY_STAKED_BASIS`                            | `CarryBasisStakedEngine`               | `lending_rates`                          | `features-onchain` (defi) | `GCSFeatureProvider`           |
| `CARRY_BASIS_PERP` / `CARRY_FUNDING_DISPERSION` | `CarryBasisPerpEngine` / `…Dispersion` | `perp_funding` (+ `perp_daily_ctx` mark) | `perp-funding` (defi)     | `CanonicalPerpFundingProvider` |

`CARRY_BASIS_PERP` reads `funding_rate_annualised_bps` + `mid_price` (mark); `CARRY_FUNDING_DISPERSION` adds a
cross-sectional `funding_rank_pct` computed from the day cohort (deterministic). Funding is annualised hourly×8760×1e4
(the SOL*BASIS convention). Honest absence (HARD RULE): a spec whose VENUE has no real data for the window is SKIPPED at
RUNTIME (`run_paper` → `no_gcs_data_in_window`), never faked; an archetype whose corpus/tick-shape is not yet wired
(`ARBITRAGE_PRICE_DISPERSION` / `DEFI_LP*\*`need`dex_pool_state` + a different tick shape) is a STATIC skip
(`engine_tick_builder_unwired`). New data-backed archetypes auto-populate when their feature group + tick builder land —
no code change to the run loop.

**FLAT/CLOSE is a valid fill side (UTL ledger SSOT).** The carry/funding engines emit a position close as
`direction="FLAT"` (a `TradeInstruction` Literal LONG/SHORT/FLAT). UTL `_signed_delta` (`ledger/materialize.py`) +
strategy-service `_direction_side` (`benchmark_fills.py`) recognise FLAT/CLOSE → the carried (signed) delta / a
mid-priced benchmark; a zero-unit flatten is a no-op 0 delta. (Before P11.11 these raised "Unknown fill side 'FLAT'",
crashing any funding-archetype run that closed a position.)

**ε=0 allocator-denominator invariant (HARD).** `resolve_paper_universe` sizes each spec's capital off the allocator
denominator = the FULL static-drivable universe (config × `specs_for_archetype` minus engine/config skips), NOT the
post-data-skip survivor set (the data-skip happens at RUNTIME, after selection). So `resolve_selection_for_slot_labels`
(batch rerun) MUST re-derive that same full-universe selection and FILTER to the manifest's slot ids — allocating over
only the survived ids uses a smaller denominator → larger per-spec weight → larger capital → larger qty → a spurious ε≠0
(the 6.5× qty deviation incident, 2026-06-21). SSOT code: `strategy_service/cli/handlers/paper_universe.py` +
`paper_run_handler.py` + `engine/core/canonical_perp_funding_provider.py`.

---

## 5. The operator workflow — DAILY T+1 (19→26 concretely)

**Cadence: DAILY T+1** (matching the existing batch-live-reconciliation-service T+1 pipeline). A "week" is just 7 of
these daily runs — there is no separate weekly reconciliation.

1. **Paper (each day 19→26)** — launch `colocated_engine` paper (the funding/basis ensemble or any promoted strategy) on
   the live feed with the benchmark fill model. Each tick: emit instructions → benchmark fills → write the 4 ledgers +
   append the captured tick to the run snapshot. **Daily**: a Slack digest of `PositionLedger` (balances per
   venue/instrument), the day's `InstructionLedger` tape, PnL + attribution, HWM.
2. **T+1 (each next morning) — rerun batch for the PRIOR trading day over its pinned snapshot.**
   `reconcile_day(paper, batch)` → the **determinism verdict** for that day. Expected: ε=0 (every paper trade appears in
   the batch with identical side/qty/fill/fees). A non-zero diff STOPS and is diagnosed as one of the three bug classes
   — never accepted as "within tolerance". (Over 19→26 this produces 7 daily determinism reports; drift is caught the
   morning after, not a week later.)
3. **Live** — same machinery with real venue fills; the daily T+1 `reconcile_day(paper, batch, live)` reports
   `live↔paper` as execution alpha and confirms `live↔batch = determinism(≈0) + execution(measured)`.

---

## 6. Reconciliation semantics (the verdict table)

| Pair              | Verdict type | Expected     | A non-zero result means                                                                              |
| ----------------- | ------------ | ------------ | ---------------------------------------------------------------------------------------------------- |
| **paper ↔ batch** | DETERMINISM  | **ε = 0**    | **a bug** → {non-determinism, input-capture gap, fill-model drift} — STOP + diagnose                 |
| **live ↔ paper**  | EXECUTION    | non-zero     | execution alpha (real slippage/fees/partials/latency) — the measurement                              |
| **live ↔ batch**  | COMPOSITE    | = exec alpha | should equal `live↔paper` (since `paper↔batch ≈ 0`); a discrepancy re-implicates the determinism leg |

Match key: `(instrument_key, strategy_instruction_id, tick_timestamp ± ε)`. Per-trade diff fields: `side_match`,
`qty_delta`, `fill_price_delta_bps`, `fees_delta`, `timing_delta_ms`. Roll up per venue/instrument/strategy/`PnLFactor`.

---

## 7. EXISTS / MISSING inventory (the precise gap list)

Last updated: 2026-08-21 (G3/G4/G5 landed; G1/G2/G6 still open — G6 newly found this date).

| Component                                                  | Status              | Location / commit                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| ---------------------------------------------------------- | ------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Shared decision path (`V2EngineOrchestrator.on_tick`)      | EXISTS              | strategy-service (batch + paper + live)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `LedgerRow` + 4 aliases + 5 enums                          | EXISTS              | `uac …/crosscutting/ledger/`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `PnLAttributionRow` / `PnLFactor` / `PnLLayer` + emitter   | EXISTS              | `uac internal/risk.py` + `utl pnl_attribution/emitter.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| HWM (3 methods) + invariants + seeds                       | EXISTS              | `utl post_trade/hwm_invariants.py` + `client-reporting-api`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| `BenchmarkFillEngine` (sim fills)                          | EXISTS              | `strategy_service/engine/backtest/benchmark_fills.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| aggregate recon (stage 3b/3c)                              | EXISTS              | `batch-live-reconciliation-service`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| Slack via alerting-service (`AlertEvent`)                  | EXISTS              | `alerting-service notifiers/slack.py` + `core/slack_dispatcher.py`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| immutable GCS market data + feature versioning             | EXISTS              | `uts-prod-market-data-*` + `feature_group_version` hive key                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **`InstructionLedger` writer FUNCTION** (batch/paper only) | **EXISTS** (P3.1)   | `utl ledger/materialize.py::ledger_row_from_trade_fill`, called only by `write_run_ledger` — UTL@41d50461. **Callers are exclusively `strategy-service`'s `batch_rerun.py`/`engine/backtest/ledger_emit.py` (CLI/backtest paths) — `execution-service` has ZERO calls into it.**                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **Live-fill → `InstructionLedger` wiring**                 | **MISSING (G6)**    | Confirmed 2026-08-21 (T4 tranche, walkthrough_feedback_remediation_2026_08_21.md): a LIVE `FILL_COMPLETED` event (`execution-service engine/orchestrator.py` → `log_event`) is consumed by `strategy-service/strategy_service/position/core/fill_event_consumer.py`, which updates the position store only — it never constructs a `TradeFillRecord`/calls `write_run_ledger`. **No live trade of any kind (manual or strategy-driven) is represented in the real GCS `InstructionLedger` today** — only batch-rerun/paper-simulation runs write it. `recon_excluded` (built same session) is consequently a no-op for live fills — the flag reaches `TradeFillRecord`/`LedgerRow` schema correctly and BLRS's skip logic is real/tested, but nothing writes a live `LedgerRow` for it to act on. Needs an operator/design decision on where a live event-driven ledger-writer path lives (parallel writer vs. extending `fill_event_consumer.py`'s subscription vs. other) before implementation. |
| **`PassiveLedger` synthesiser**                            | **EXISTS** (P3.2)   | `utl ledger/materialize.py::passive_ledger_row` + `accrue_funding` — UTL@09885861                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| **`PositionLedger` materialiser (avg-cost P&L)**           | **EXISTS** (P3.3)   | `utl ledger/materialize.py::materialize_position_ledger` — UTL@41d50461                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| **realised-PnL computation**                               | **EXISTS** (P3.4)   | `client-reporting-api core/ledger_views.py::compute_ledger_views` — CRA@0d9b1bec                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **per-venue/instrument balance from ledger**               | **EXISTS** (P3.4)   | `client-reporting-api core/ledger_views.py` (by_venue/by_instrument rollups) — CRA@0d9b1bec                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| **marks join by canonical `instrument_key`**               | **EXISTS** (P1-fix) | `utl ledger/run_writer.py::pricing_ledger_jsonl` stamps key; `materialize_position_ledger` joins on it — UTL@68540e7a (fixes phantom $700K uPnL when two legs share `asset_canonical_id`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **run manifest / as-of snapshot**                          | **EXISTS** (P4.1)   | `utl ledger/run_writer.py::write_run_manifest` + `read_run_manifest`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| **trade-by-trade keyed diff + daily T+1 recon**            | **EXISTS** (P4.2)   | `blrs engine/trade_recon.py::reconcile_day` + `engine/daily_determinism_stage.py` — BLRS@4b611db                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| **daily T+1 recon verdict → AlertEvent (INFO/CRITICAL)**   | **EXISTS** (P6.2)   | `blrs engine/recon_alert_client.py::post_recon_alert` called by `cli/handlers/daily_determinism_handler.py` — BLRS@0fabc9c                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **Single shared fill model** (batch≡paper)                 | **MISSING (G1)**    | P1.6 open — `GroupCRunner` smart-matching not yet wired in paper path                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| **Per-trade identity in execution events**                 | **MISSING (G2)**    | P2.1/P2.2 open — events are date-level float dicts; `trade_key` not yet on execution events                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |

---

## 8. Cross-references

- Plan-of-record: `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`.
- Composes with: `/codex/04-architecture/global-ledger-architecture.md` (the 4 SSOT ledgers + the materialisation gaps),
  `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`,
  `/codex/02-data/pipeline-mode-and-batch-live-reconciliation.md`,
  `/codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md` (the live↔paper tolerance leg),
  `/codex/04-architecture/wallet-hierarchy-and-capital-flow.md`, `/codex/09-strategy/operational/cli-promote-paths.md`
  (the paper→live promote path this reconciliation gates).
- Parent epic: `plans/epics/batch_live_symmetry_master.md` (owns "Batch = Live" + reconciliation);
  ledger-materialisation phases compose with `plans/epics/global_ledger_pnl_attribution_master.md`.
