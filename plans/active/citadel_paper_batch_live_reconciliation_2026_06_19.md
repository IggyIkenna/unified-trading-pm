---
title: "Citadel-grade Paper ⟷ Batch ⟷ Live Reconciliation — the Determinism Spine"
parent_epic: batch_live_symmetry_master
assigned_vm: vm-cross-cutting
status: active
priority: P1
created: 2026-06-19
estimate_class: infra
estimate_baseline_ai_days: 48
estimate_calibrated_ai_days: 38
locked_by: live-defi-rollout
locked_since: 2026-06-19
related_plans:
  - plans/epics/batch_live_symmetry_master.md
  - plans/epics/global_ledger_pnl_attribution_master.md
  - plans/active/global_ledger_pnl_attribution_migration_2026_06_01.md
Codex SSOTs:
  - codex/09-strategy/operational/paper-batch-live-reconciliation.md
  - codex/04-architecture/global-ledger-architecture.md
  - codex/02-data/pipeline-mode-and-batch-live-reconciliation.md
  - codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md
---

# Citadel-grade Paper ⟷ Batch ⟷ Live Reconciliation

> **Design SSOT**: `codex/09-strategy/operational/paper-batch-live-reconciliation.md` (full architecture +
> EXISTS/MISSING map). This plan is the **phased execution DAG**. Read the SSOT first — do not act from this summary.

## The thesis (operator, 2026-06-19)

The three trading modes are **the same program**. `paper(W)` must equal `batch-rerun(W)` **trade-for-trade** (same
code + same inputs + same fill model); the **only** intentional divergence is real venue fills at the LIVE boundary. So:

```
live − batch = (paper − batch)      + (live − paper)
                └ determinism ≈ 0 ┘   └ execution alpha ┘
                   a BUG if not 0       the measurement
```

The paper↔batch reconciliation is a **determinism PROOF** (ε=0, any diff is a bug), not a tolerance check.
"Citadel-grade paper trading" = the complete as-if-filled state: all money movements, balances (per
venue/instrument/share_class), P&L, PnL attribution, venues + instruments breakdown — held in four ledgers
(`InstructionLedger` historical tape + `PositionLedger` as-if-filled state + `PassiveLedger` accruals + `PricingLedger`
marks), eyeball-able + Slack-summarised.

## The five gaps (design targets — see SSOT §3)

- **G1** — THREE divergent fill models (APY-haircut / `BenchmarkFillEngine` / `PaperMatchingEngine`); paper and batch
  use different fill code. **This is the "paper sim ≠ batch sim" bug the operator named.**
- **G2** — no per-trade identity in execution events (date-level float-metric dicts; no order_id/instrument_key/ts).
- **G3** — ledgers unmaterialised (no `PositionLedger` writer, no `InstructionLedger`-from-fills, no `PassiveLedger`
  synth, `realized_pnl` hardcoded `"0.00"`, balances from CCXT not `Σ delta`).
- **G4** — no point-in-time input capture / as-of run manifest (a rerun may read revised data → spurious diff).
- **G5** — recon is aggregate (`abs(mean_a−mean_b)`) + single-date; no trade-by-trade keyed diff, no weekly rollup, no
  determinism verdict.

## Pre-audit before execution (Citadel standard §1)

Before Phase 1, grep every consumer of: `BenchmarkFillEngine`, `PaperMatchingEngine`, `run_2yr_config_grid_backtest`,
the colocated_engine fill providers, the execution-service event-emission format, `compute_pnl_breakdown`,
`client-reporting-api` positions/pnl routes, and `batch-live-reconciliation-service` stage 3b/3c — embed the manifest in
this plan before changing a fill or event shape. (Phase 0 item P0.0.)

## Foundation-completion-gate ordering (Citadel standard §8)

Layered, each GREEN-audited before the next: **Phase 0 (contract) → Phase 1 (one fill model) → Phase 2 (trade identity)
→ Phase 3 (ledger materialisation) → Phase 4 (recon harness) → Phase 5 (views) → Phase 6 (Slack) → Phase 7 (the 19→26
dry-run)**. Phases 1–3 are the foundation; the harness (4) is meaningless until the fill model is unified (1) and trades
are identified (2) and the ledger exists (3).

---

## Phase 0 — Pin the determinism contract

- [x] ✅ [DESIGN] P0.0. **Pre-audit manifest** — DONE: 4 read-only Explore agents mapped every consumer of the fill
      engines / event format / ledger routes; the EXISTS/MISSING inventory is embedded in the codex SSOT §2+§7.
- [x] ✅ [SCHEMA] P0.1. **`RunManifest` UAC type** — `unified-api-contracts@12597d8`: `RunManifest` (run_id, window,
      mode, client_id, strategy_ids, `code_shas{}`, `market_data_days[]`, `feature_group_versions{}`,
      `captured_tick_stream`, `fill_model`, `ledger_root`, `parent_run_id`) + `TradingMode`/`FillModel` StrEnums in
      `internal/reconciliation.py`. The two-fill-realities rule is encoded in `FillModel` (BENCHMARK + LIVE_VENUE only).
      20 tests, QG green.
- [x] ✅ [SCHEMA] P0.2. **`PositionLedger` schema + GCS path** — `unified-api-contracts@12597d8`: `PositionLedgerRow`
      (the `Σ delta GROUP BY (account, asset, venue, instrument)` derived view; per-venue/instrument/share_class
      balance + realised/unrealised PnL) in `canonical/crosscutting/ledger/_position_ledger.py`, `ledger_type=position`
      partition, exported root + crosscutting + ledger facades.
- [x] ✅ [SCHEMA] P0.3. **Per-trade key + recon report** — `unified-api-contracts@12597d8`: `make_trade_key(
      instrument_key, strategy_instruction_id, tick_timestamp)` (deterministic, UTC-normalised) + `TradeFillRecord`
      (the keyed per-trade fill carrying correlation_id/client_order_id) + `TradeDeviation` + `WeeklyReconReport`
      (DETERMINISM/EXECUTION/COMPOSITE verdicts + `DeterminismBugClass`). `LedgerRow.trade_id` carries the key.

## Phase 1 — Unify the fill model (G1, the core fix)

- [ ] [CODE] P1.1. **Make `BenchmarkFillEngine` the single simulation SSOT** — unify the strategy-service
      `BenchmarkFillEngine` and execution-service `v2/benchmark_fills.py` pricing registry so they cannot drift (one
      import or a shared UAC fill-mode SSOT). Repo: strategy-service + execution-service + unified-api-contracts.
      **PARTIAL (2026-06-19)**: ✅ UAC pricing SSOT shipped (`unified-api-contracts@bc4c756` —
      `internal/architecture_v2/benchmark_fill_pricing.py`: `benchmark_fill_price()` + `DEFAULT_BENCHMARK_PRICING_FNS`,
      7 modes, 7 tests). ✅ execution-service rewired to a thin adapter over it (`execution-service@e11854e5` — duplicate
      primitives deleted). ⏳ **REMAINING — strategy-service `BenchmarkFillEngine` rewiring is a BEHAVIOURAL CORRECTION,
      not a mechanical lift**: it computes `PASSIVE_BBO` OPPOSITELY to the UAC SSOT (`_resolve_trade_benchmark:133` maps
      LONG→ask / SHORT→bid; UAC maps buy→bid / sell→ask — correct passive-maker semantics is buy@bid/sell@ask, so the
      strategy-service convention is mislabeled, taking the far touch). This is a **concrete instance of the paper-sim ≠
      batch-sim drift the operator named**. Correcting it changes historical backtest fill prices, so it MUST land with
      the Phase 4 `reconcile_week` harness validating paper≡batch afterward (do NOT rush it). The strategy-service
      engine also operates on a typed `MarketStateSnapshot` (raw TWAP/VWAP windows + None-fallbacks + ATOMIC per-leg)
      vs the UAC flat-dict ctx — the rewiring builds the ctx from the snapshot (pre-computing twap/vwap) then calls
      `benchmark_fill_price`, preserving the ARRIVAL_MID fallbacks. Until then P1.1 is NOT flipped.
- [ ] [CODE] P1.2. **Paper uses `BenchmarkFillEngine`, NOT `PaperMatchingEngine` real-AMM** — the colocated_engine
      benchmark provider routes through the SAME engine batch uses; paper IS "batch forward on the live feed". Delete
      the divergent paper-AMM fill path (no parallel old+new). Repo: strategy-service + execution-service.
- [ ] [CODE] P1.3. **Retire the APY-haircut shortcut** — `run_2yr_config_grid_backtest.py` must run the real
      `GroupBRunner` + `GCSFeatureProvider` on real GCS data (not synthetic LCG features + `slippage_cap_bps*4/365`); a
      "backtest of a real week" replays real parquets. Repo: strategy-service.
- [ ] [CODE] P1.4. **Complete `GroupCRunner` Phase 4** — measure execution alpha for SWAP/LEND/STAKE/ATOMIC, not only
      TRADE (so the live↔paper leg covers every action). Repo: execution-service.
- [ ] [DOC] P1.5. **Codify the two-fill-realities HARD RULE** (SSOT §4.2): exactly canonical-sim (`BenchmarkFillEngine`,
      batch+paper) + real-venue (`LiveMatchingEngine`, live); a third on the batch/paper path is review-blocking. Repo:
      unified-trading-pm (CLAUDE.md + SSOT).

## Phase 2 — Per-trade identity in execution events (G2)

- [ ] [CODE] P2.1. **Execution events gain `trade_key` + side/qty/price/fees** — replace the date-level float-metric
      event lines with per-trade keyed records (the `LedgerRow` is the natural carrier). Repo: execution-service.
- [ ] [CODE] P2.2. **colocated_engine fill records carry the key** — `fill_id` → the UAC `trade_key`; persist
      `correlation_id` (not a sequential int). Repo: strategy-service.

## Phase 3 — Materialise the four ledgers from fills (G3)

- [ ] [CODE] P3.1. **`InstructionLedger` writer from fills** — every sim/live fill emits
      `LedgerRow(event_type=TRADE,     delta=±qty, price, fees, …)` to `ledger_type=instruction/`; money movements →
      `TreasuryLedger`. Repo: strategy-service (writer) + unified-trading-library (emit helper).
- [ ] [CODE] P3.2. **`PassiveLedger` synthesiser** — funding/staking/lending accruals → `ledger_type=passive/` (the
      architecture flags this as not-yet-implemented). Repo: unified-trading-library + strategy-service.
- [ ] [CODE] P3.3. **`PositionLedger` materialiser** — `Σ delta GROUP BY (account, asset, venue, instrument)` →
      per-venue/per-instrument/per-share_class balances + the as-if-filled current state. Repo: strategy-service /
      client-reporting-api.
- [ ] [CODE] P3.4. **Realised-PnL computation** — replace the hardcoded `"0.00"`
      (`client-reporting-api     attribution.py:189`) with realised closes from `LedgerRow` deltas; wire the live
      positions route (currently mock). Repo: client-reporting-api.
- [ ] [CODE] P3.5. **HWM from the ledger** — drive TWR / Notional / PnL-recovery HWM off the materialised ledger (not
      `max(equities)`); assert `hwm_invariants`. Repo: unified-trading-library + client-reporting-api.

## Phase 4 — The trade-by-trade reconciliation harness (G5)

- [ ] [CODE] P2.4.1. **`reconcile_week(paper, batch, live)`** — keyed match on `trade_key`; paper↔batch DETERMINISM
      verdict (ε=0, classify a diff as {NON_DETERMINISM | INPUT_CAPTURE_GAP | FILL_MODEL_DRIFT}); live↔paper EXECUTION
      verdict (per-trade fill_price_delta_bps / qty_delta / timing_delta_ms). Repo: batch-live-reconciliation-service.
- [ ] [CODE] P2.4.2. **Populate `DeviationRecord.instrument_id` + a `trade_key`** + roll up per
      venue/instrument/strategy/`PnLFactor`; weekly aggregation (7 dates → one report). Repo:
      batch-live-reconciliation-service.
- [ ] [CODE] P2.4.3. **The batch-rerun-from-manifest path** — take a paper `RunManifest`, assert code shas, replay
      `captured_tick_stream`, write a `mode=batch` ledger back-referencing the paper run. Repo: strategy-service (CLI
      subcommand) + e2e-testing harness.

## Phase 5 — Balances / PnL / attribution / instruments-breakdown views

- [ ] [CODE] P2.5.1. **Per-venue + per-instrument balance + PnL + attribution views** off `PositionLedger` +
      `PnLAttributionRow`; join `InstrumentRecord` on `instrument_key` for the instruments breakdown. Repo:
      client-reporting-api.

## Phase 6 — Slack log

- [ ] [CODE] P2.6.1. **Daily ledger digest** (balances per venue/instrument, the day's `InstructionLedger` tape, PnL +
      attribution, HWM) → `AlertEvent(INFO)` → alerting-service → `#uts-live-alerts`. Repo: strategy-service /
      client-reporting-api (POST to alerting-service; no cross-service import).
- [ ] [CODE] P2.6.2. **Weekly recon verdict** → `AlertEvent` (INFO on ε=0 determinism + the execution-alpha summary;
      CRITICAL on a determinism bug). Repo: batch-live-reconciliation-service.

## Phase 7 — The 19→26 operator dry-run (runs to completion)

- [ ] [INFRA] P2.7.1. **Paper week** — run a promoted strategy (or the funding/basis ensemble) in `colocated_engine` paper
      with the benchmark fill model over a real week, writing the 4 ledgers + the `RunManifest`. Daily Slack digest.
      Repo: deployment-service (VM) + strategy-service.
- [ ] [INFRA] P2.7.2. **T+7 batch rerun + `reconcile_week`** — rerun batch over the SAME pinned snapshot; produce the
      determinism verdict. **Target: ε=0.** Any diff STOPS + is diagnosed (one of the three bug classes). Repo:
      batch-live-reconciliation-service.
- [ ] [INFRA] P2.7.3. **Live → reconcile to paper → (∴ to batch)** — same machinery with real venue fills; report
      live↔paper execution alpha + confirm `live↔batch = determinism(≈0) + execution(measured)`. Repo: (gated on live
      custody readiness — `BLOCKED-OPERATOR-DECISION` until a live wallet is approved).

## Codex SSOT updates (Citadel §6 / Post-Plan-Phase Codex Audit)

- [ ] [DOC] P3.8.1. Keep `codex/09-strategy/operational/paper-batch-live-reconciliation.md` in sync as each phase lands
      (EXISTS/MISSING table → EXISTS). Update `codex/04-architecture/global-ledger-architecture.md` when the
      `PositionLedger`/`PassiveLedger`/realised-PnL gaps close. Bump the `EventType` count in
      `codex/02-data/ledger-event-taxonomy.md` (39, not 37). Repo: unified-trading-pm.

## Success criteria (per phase: QG/basedpyright/ruff green + tests)

- **Determinism**: `reconcile_week(paper, batch)` returns ε=0 over a real week (P7.2) — the core acceptance.
- **Completeness**: the 4 ledgers materialise; balances/PnL/attribution are real (not mock/`"0.00"`), per
  venue+instrument.
- **One fill model**: no third fill model on the batch/paper path (`BenchmarkFillEngine` is the single sim SSOT).
- **Slack**: daily ledger digest + weekly recon verdict reach `#uts-live-alerts`.

## Temporary states + their canonical follow-up plans

- P7.3 (live leg) is `BLOCKED-OPERATOR-DECISION` until a live wallet/custody is approved (hard-stop: wallet keys are
  human-only). The paper↔batch determinism proof (P7.2) does not depend on it.

## Progress Log

### 2026-06-19 — Phase 0 SHIPPED (the determinism-spine contract)

`unified-api-contracts@12597d8` (UAC QG green, 20 unit tests). The foundation contract every later phase builds on:
`RunManifest` (as-of snapshot pin) · `make_trade_key` (deterministic match key) · `TradeFillRecord` · `WeeklyReconReport`
+ `TradeDeviation` · `TradingMode`/`FillModel`/`ReconVerdictType`/`DeterminismBugClass` StrEnums · `PositionLedgerRow`
(derived as-if-filled view). `FillModel` encodes the two-fill-realities rule (BENCHMARK=batch+paper, LIVE_VENUE=live).
Additive surface → no SIT cascade. Recon types live in `internal/reconciliation.py`; `PositionLedgerRow` in the ledger
package (root-exposed).

**Next — Phase 1 (the core fix): unify the fill model.** Both `BenchmarkFillEngine` (strategy-service) and the
execution-service `BenchmarkFillRegistry` already share the UAC `BenchmarkFillMode` enum, but duplicate the per-mode
pricing primitives (twap/vwap/arrival_mid/pool_mid_at_block/passive_bbo/funding_snapshot). Plan: lift the pricing
primitives to a single UAC SSOT both engines call (no drift), route the colocated_engine paper provider through
`BenchmarkFillEngine` (not `PaperMatchingEngine` real-AMM), and retire the `run_2yr_config_grid_backtest.py`
APY-haircut shortcut in favour of the real `GroupBRunner` + `GCSFeatureProvider` path.

### 2026-06-19 — Phase 1 P1.1 PARTIAL + a real drift finding

Shipped the single benchmark-pricing SSOT (`unified-api-contracts@bc4c756`) + rewired execution-service to a thin
adapter over it (`execution-service@e11854e5`, duplicate primitives deleted, QG green). **Finding (the operator's exact
fear, concretely):** the strategy-service `BenchmarkFillEngine` computes `PASSIVE_BBO` OPPOSITELY to the UAC SSOT
(LONG→ask/SHORT→bid vs the correct buy@bid/sell@ask) — so paper-sim ≠ batch-sim TODAY for any passive-BBO fill. The
strategy-service rewiring therefore corrects a fill convention (changes historical backtest prices) and must land with
Phase 4's `reconcile_week` proving paper≡batch afterward — sequenced deliberately, not rushed. P1.1 stays open until that
correction lands. **Next concrete step**: rewire `strategy_service/engine/backtest/benchmark_fills.py`
`_resolve_*_benchmark` to build the dict ctx from `MarketStateSnapshot` + call `benchmark_fill_price` (correct
PASSIVE_BBO, preserve ARRIVAL_MID None-fallbacks), update the strategy-service benchmark-fill tests to the corrected
convention, QG, ship → then flip P1.1.
