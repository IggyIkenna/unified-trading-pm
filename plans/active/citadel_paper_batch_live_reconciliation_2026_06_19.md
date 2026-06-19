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
- **G5** — recon is aggregate (`abs(mean_a−mean_b)`) + single-date; no trade-by-trade keyed diff, no daily-T+1
  trade-level recon, no determinism verdict.

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
- [x] ✅ [SCHEMA] P0.3. **Per-trade key + recon report** — `unified-api-contracts@12597d8`:
      `make_trade_key(     instrument_key, strategy_instruction_id, tick_timestamp)` (deterministic, UTC-normalised) +
      `TradeFillRecord` (the keyed per-trade fill carrying correlation_id/client_order_id) + `TradeDeviation` +
      `DailyReconReport` (DETERMINISM/EXECUTION/COMPOSITE verdicts + `DeterminismBugClass`). `LedgerRow.trade_id`
      carries the key.

## Phase 1 — Unify the fill model (G1, the core fix)

- [x] ✅ [CODE] P1.1. **Make `BenchmarkFillEngine` the single simulation SSOT** — DONE
      (`strategy-service@b136f70e` + `batch-live-reconciliation-service@1a12500`, both QG-green). The strategy-service
      `BenchmarkFillEngine._resolve_trade_benchmark` now builds the flat `BenchmarkPricingContext` from the typed
      `MarketStateSnapshot` (pre-computing TWAP/VWAP; ARRIVAL_MID None-fallback to mid preserved) and delegates to the
      UAC `benchmark_fill_price` SSOT (`unified-api-contracts@bc4c756`) — so strategy-service Group B + execution-service
      Group C / paper price the benchmark through ONE function and cannot drift. **PASSIVE_BBO convention CORRECTED**:
      a LONG passive maker now fills at the BID, a SHORT at the ASK (UAC `_passive_bbo`: `bid if side > 0 else ask`) —
      previously LONG→ask / SHORT→bid, the latent paper-vs-batch drift. strategy-service tests updated to the corrected
      convention (`_long_uses_bid` + new `_short_uses_ask`). **Shipped WITH the `reconcile_day` proof (build-order
      rule)**: BLRS `test_corrected_passive_bbo_benchmark_reconciles_deterministically` asserts ε=0 paper≡batch on the
      corrected prices, and `test_passive_bbo_drift_is_a_fill_model_bug` asserts the OLD convention is classified
      `FILL_MODEL_DRIFT` (not accepted as "within tolerance"). Prior shipped pieces: ✅ UAC pricing SSOT
      (`unified-api-contracts@bc4c756`, 7 modes / 7 tests) + ✅ execution-service thin adapter
      (`execution-service@e11854e5`, duplicate primitives deleted).
- [ ] [CODE] P1.2. **Batch runs the SAME execution-service smart matching as paper** (REVERSED 2026-06-19 per operator —
      the prior "paper drops to BenchmarkFillEngine" framing was backwards). Paper correctly books smart-matched fills
      via `PaperMatchingEngine` (execution-service, fidelity-bounded by OHLCV→BBO→depth→trades→MBO); the gap is that
      batch (`GroupBRunner`) stops at the benchmark and does NOT run the Group C smart matching → batch ≠ paper. Make
      batch run the SAME execution-service matching on the SAME data so paper≡batch. Do NOT remove paper's matching.
      Folds into P1.4. Repo: strategy-service (Group B → Group C handoff) + execution-service.
- [ ] [CODE] P1.3. **Retire the APY-haircut shortcut** — `run_2yr_config_grid_backtest.py` must run the real
      `GroupBRunner` + `GCSFeatureProvider` on real GCS data (not synthetic LCG features + `slippage_cap_bps*4/365`); a
      "backtest of a real week" replays real parquets. (The haircut is neither the benchmark nor the smart matching — a
      crude third thing to delete.) Repo: strategy-service.
- [ ] [CODE] P1.4. **Complete `GroupCRunner` — THE LINCHPIN** (elevated 2026-06-19). Group C is execution-service's
      smart matching measured against the benchmark (`execution alpha = smart_fill − benchmark`). Completing it for
      every action (SWAP/LEND/STAKE/ATOMIC, not only TRADE) is what gives BATCH the same smart-matching layer paper
      already has → the determinism leg (paper≡batch) and the execution-alpha leg (live−benchmark) both become
      measurable. Realism is bounded by market-data fidelity (OHLCV→BBO→L2 depth→trades→L3 MBO); where only OHLCV
      exists, smart matching ≈ benchmark (candle close). Repo: execution-service.
- [x] ✅ [DOC] P1.5. **Codify the two-fill-realities HARD RULE** — DONE (`unified-trading-pm@2673bf04a`): the rule lives
      in CLAUDE.md § "Batch = Live" ("Two fill realities only: canonical-sim … + real-venue … — a third fill model on
      the batch/paper path is review-blocking") AND the codex SSOT §4.2 design rule (lines 174–176). The `FillModel`
      StrEnum (`unified-api-contracts@12597d8`, BENCHMARK + LIVE_VENUE only) is the structural enforcement.

## Phase 2 — Per-trade identity in execution events (G2)

- [ ] [CODE] P2.1. **Execution events gain `trade_key` + side/qty/price/fees** — replace the date-level float-metric
      event lines with per-trade keyed records (the `LedgerRow` is the natural carrier). Repo: execution-service.
- [ ] [CODE] P2.2. **colocated_engine fill records carry the key** — `fill_id` → the UAC `trade_key`; persist
      `correlation_id` (not a sequential int). Repo: strategy-service.

## Phase 3 — Materialise the four ledgers from fills (G3)

- [x] ✅ [CODE] P3.1. **`InstructionLedger` writer-from-fills (library helper)** — DONE
      (`unified-trading-library@41d50461`): `ledger/materialize.py::ledger_row_from_trade_fill()` maps a
      `TradeFillRecord` →
      `LedgerRow(event_origin=INSTRUCTION, event_type=TRADE, trade_id=trade_key, delta=±qty signed by side, price,     fees)`.
      ⏳ wiring the strategy-service engine to CALL it on each fill (+ the GCS emit) rides Phase 2 (the engine emits
      keyed fills) — the pure helper is shipped + tested.
- [x] ✅ [CODE] P3.2. **`PassiveLedger` synthesiser** — DONE (`unified-trading-library@09885861`, 16 tests):
      `ledger/materialize.py::passive_ledger_row()` builds `LedgerRow(event_origin=PASSIVE, event_type=FUNDING_ACCRUAL/
      STAKING_REWARD/LENDING_INTEREST, delta=±accrued, accrual_period_*, the matching rate column)` + `accrue_funding(
      notional, rate)` (payer-debited sign: a LONG paying positive funding gets a negative accrual). For carry/funding
      strategies these accruals ARE the P&L. ⏳ the engine wiring (emit accruals per period) rides Phase 2/5. (Closes the
      "PassiveLedger not-yet-implemented" gap the global-ledger architecture flagged.)
- [x] ✅ [CODE] P3.3. **`PositionLedger` materialiser (avg-cost P&L)** — DONE (`unified-trading-library@41d50461`):
      `ledger/materialize.py::materialize_position_ledger()` —
      `Σ delta GROUP BY (account, client, venue,     asset_canonical_id)` with **average-cost accounting** (VWAP on
      opens, realised on closes, cross-through-zero re-open, unrealised = net_qty·(mark−avg_cost)); emits
      `PositionLedgerRow` per group with share_class rollup + realised/unrealised PnL. 23 tests (incl.
      cross-through-zero both directions, fees, multi-instrument). This is the as-if-filled positions/balances surface —
      pure + tested; the GCS read/write wiring rides Phase 5 (the views).
- [x] ✅ [CODE] P3.4 + [CODE] P5.1. **Real ledger-derived positions/PnL/balances views** — DONE
      (`client-reporting-api@0d9b1bec`, 14 tests): `core/ledger_views.py::compute_ledger_views()` (positions via UTL
      `materialize_position_ledger` + `by_venue`/`by_instrument`/`by_share_class` rollups + realized/unrealized/total
      PnL); `/positions` + `/pnl` routes rewired to it — the hardcoded `realized_pnl="0.00"` + the mock positions are
      DELETED; empty ledger → honest zero/empty (not mock); a pluggable `read_ledger_rows(client_id, date)` seam (returns
      `[]` until the engine-wiring phase populates the GCS ledger). **This is the operator's eyeball surface (balances +
      P&L per venue/instrument/share_class).** **Correctness finding (capture for the engine-wiring phase): PASSIVE
      accrual rows carry a QUOTE cash-flow `delta`, NOT a base-asset qty — they must NOT be fed to
      `materialize_position_ledger` (corrupts `net_qty`); fold TRADE rows into positions, add PASSIVE rows to realized
      PnL as a separate stream.**
- [x] ✅ [CODE] P3.5. **HWM from the ledger** — DONE (`client-reporting-api@52d8b7d`, 13 tests): `core/hwm_from_ledger.py`
      `ledger_nav_series` (NAV = seed + cumulative realised+unrealised `total_pnl` from `compute_ledger_views`) +
      `hwm_from_ledger` (running peak, `delta=max(0, nav-prior_peak)` — advances-only, NEVER `max(equities)`) emitting
      `HighWaterMarkLedgerRow`s; mirrors the HWM invariants (monotonic peak, delta≥0, period ordering). Seeds untouched.

## Phase 4 — The trade-by-trade reconciliation harness (G5)

- [x] ✅ [CODE] P4.1. **`reconcile_day(...)`** — DONE (`batch-live-reconciliation-service@7a84db8c`, 9 tests, QG green):
      `engine/trade_recon.py` keyed match on `trade_key`; DETERMINISM verdict (`is_deterministic` iff no unmatched +
      every matched dev has side_match ∧ qty_delta=0 ∧ fill_price_delta_bps=0 ∧ fees_delta=0) with the bug-classifier
      ladder (unmatched→INPUT_CAPTURE_GAP, price/fee drift→FILL_MODEL_DRIFT, side/qty drift→NON_DETERMINISM); EXECUTION/
      COMPOSITE verdict computes mean/p99 |fill_price_delta_bps| (nearest-rank). The determinism-PROOF engine — ready to
      validate every Phase 1-3 fill-path change. **This is the keystone: any fill-path correction now ships WITH a
      reconcile_day test proving paper≡batch.**
- [x] ✅ [CODE] P4.2. **Daily T+1 `reconcile_day` stage + rollups** — DONE (`batch-live-reconciliation-service@4b611db`):
      `engine/daily_determinism_stage.py` runs `reconcile_day` at T+1 (prior trading day's paper vs batch rerun) → the
      DETERMINISM verdict; `engine/ledger_reader.py` reads the InstructionLedger JSONL the P3.1 writer emits; per-trade
      keyed diff with instrument-level detail; daily T+1 cadence (one report per day). Recovered from session-limit
      -orphaned WIP + shipped.
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
- [ ] [CODE] P2.6.2. **Daily T+1 recon verdict** → `AlertEvent` (INFO on ε=0 determinism + the execution-alpha summary;
      CRITICAL on a determinism bug). Repo: batch-live-reconciliation-service.

## Phase 7 — The 19→26 operator dry-run (runs to completion)

- [ ] [INFRA] P2.7.1. **Paper week** — run a promoted strategy (or the funding/basis ensemble) in `colocated_engine`
      paper with the benchmark fill model over a real week, writing the 4 ledgers + the `RunManifest`. Daily Slack
      digest. Repo: deployment-service (VM) + strategy-service.
- [ ] [INFRA] P2.7.2. **Daily T+1 batch rerun + `reconcile_day`** — each morning, rerun batch for the PRIOR trading day
      over its pinned snapshot; produce that day's determinism verdict. **Target: ε=0.** Any diff STOPS + is diagnosed
      (one of the three bug classes). Cadence is daily T+1 (a week = 7 daily reports), not a single weekly run. Repo:
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

- **Determinism**: `reconcile_day(paper, batch)` returns ε=0 over a real week (P7.2) — the core acceptance.
- **Completeness**: the 4 ledgers materialise; balances/PnL/attribution are real (not mock/`"0.00"`), per
  venue+instrument.
- **One fill model**: no third fill model on the batch/paper path (`BenchmarkFillEngine` is the single sim SSOT).
- **Slack**: daily ledger digest + daily T+1 recon verdict reach `#uts-live-alerts`.

## Temporary states + their canonical follow-up plans

- P7.3 (live leg) is `BLOCKED-OPERATOR-DECISION` until a live wallet/custody is approved (hard-stop: wallet keys are
  human-only). The paper↔batch determinism proof (P7.2) does not depend on it.

## Progress Log

### 2026-06-19 — Phase 0 SHIPPED (the determinism-spine contract)

`unified-api-contracts@12597d8` (UAC QG green, 20 unit tests). The foundation contract every later phase builds on:
`RunManifest` (as-of snapshot pin) · `make_trade_key` (deterministic match key) · `TradeFillRecord` · `DailyReconReport`

- `TradeDeviation` · `TradingMode`/`FillModel`/`ReconVerdictType`/`DeterminismBugClass` StrEnums · `PositionLedgerRow`
  (derived as-if-filled view). `FillModel` encodes the two-fill-realities rule (BENCHMARK=batch+paper, LIVE_VENUE=live).
  Additive surface → no SIT cascade. Recon types live in `internal/reconciliation.py`; `PositionLedgerRow` in the ledger
  package (root-exposed).

**Next — Phase 1 (the core fix): unify the fill model.** Both `BenchmarkFillEngine` (strategy-service) and the
execution-service `BenchmarkFillRegistry` already share the UAC `BenchmarkFillMode` enum, but duplicate the per-mode
pricing primitives (twap/vwap/arrival_mid/pool_mid_at_block/passive_bbo/funding_snapshot). Plan: lift the pricing
primitives to a single UAC SSOT both engines call (no drift), route the colocated_engine paper provider through
`BenchmarkFillEngine` (not `PaperMatchingEngine` real-AMM), and retire the `run_2yr_config_grid_backtest.py` APY-haircut
shortcut in favour of the real `GroupBRunner` + `GCSFeatureProvider` path.

### 2026-06-19 — Phase 1 P1.1 PARTIAL + a real drift finding

Shipped the single benchmark-pricing SSOT (`unified-api-contracts@bc4c756`) + rewired execution-service to a thin
adapter over it (`execution-service@e11854e5`, duplicate primitives deleted, QG green). **Finding (the operator's exact
fear, concretely):** the strategy-service `BenchmarkFillEngine` computes `PASSIVE_BBO` OPPOSITELY to the UAC SSOT
(LONG→ask/SHORT→bid vs the correct buy@bid/sell@ask) — so paper-sim ≠ batch-sim TODAY for any passive-BBO fill. The
strategy-service rewiring therefore corrects a fill convention (changes historical backtest prices) and must land with
Phase 4's `reconcile_day` proving paper≡batch afterward — sequenced deliberately, not rushed. P1.1 stays open until that
correction lands. **Next concrete step**: rewire `strategy_service/engine/backtest/benchmark_fills.py`
`_resolve_*_benchmark` to build the dict ctx from `MarketStateSnapshot` + call `benchmark_fill_price` (correct
PASSIVE_BBO, preserve ARRIVAL_MID None-fallbacks), update the strategy-service benchmark-fill tests to the corrected
convention, QG, ship → then flip P1.1.

### 2026-06-19 — Phase 4 keystone SHIPPED (the determinism-PROOF engine)

`batch-live-reconciliation-service@7a84db8c` — `engine/trade_recon.py::reconcile_day` (9 tests, QG green). Built BEFORE
the fill-path changes (Phases 1-3) deliberately: it is the validator those changes must pass. The DETERMINISM verdict is
binary (ε=0 or a classified bug); EXECUTION/COMPOSITE carries the alpha rollup. **Build-order rule from here on**: every
fill-path or ledger change (P1.1-strategy / P1.2 / P1.4 / Phase 3) ships WITH a `reconcile_day` test asserting
paper≡batch on a fixture — the harness turns each behavioural correction from "hope it matches" into a proof. Remaining
big rocks: Phase 3 ledger materialisation (the as-if-filled ledger to eyeball) + P1.4 GroupCRunner (the linchpin that
gives batch the smart-matching layer) + P4.3 batch-rerun-from-manifest. These are interconnected, multi-repo,
behavioural — sequenced, harness-validated, not rushed.

### 2026-06-19 — Phase 3 ledger machinery SHIPPED (the as-if-filled ledger core)

`unified-trading-library@41d50461` — `ledger/materialize.py` (23 tests, QG green): `ledger_row_from_trade_fill` (fill →
InstructionLedger TRADE row, signed delta) + `materialize_position_ledger` (the avg-cost PositionLedger: VWAP opens,
realised on closes, cross-through-zero re-open, unrealised from marks, share_class rollup). These are the PURE financial
core of "Citadel-grade paper trading" — the historical trade tape + the as-if-filled positions/balances/P&L surface.

**Session high-water checkpoint.** The determinism spine's pure-logic core is SHIPPED + TESTED across 4 repos: the
contract (Phase 0 — uac@12597d8), the benchmark-pricing SSOT (P1.1 — uac@bc4c756 + es@e11854e5), the determinism-PROOF
engine (P4.1 — blrs@7a84db8c), and the ledger accounting (P3.1/P3.3 — utl@41d50461). **What remains is service
INTEGRATION + behavioural fill-path corrections**, all now harness-validatable: P2 (engine emits keyed fills) →
P3.1/P3.2 wiring (engine calls the writer; PassiveLedger synth) → P1.4 GroupCRunner (batch runs the smart matching = the
linchpin) → P1.1-strategy (PASSIVE_BBO correction) → P3.4/P3.5 (client-reporting-api realised-PnL + HWM) → P4.3
(batch-rerun-from- manifest) → P5/P6 (views + Slack) → P7 (short-window e2e proof). Each ships WITH a reconcile_day test
(the build-order rule). These are interconnected service changes on live/backtest code — deliberately sequenced +
validated, not rushed.

### 2026-06-19 — Daily T+1 cadence correction + PassiveLedger (ledger core complete)

**Cadence fix (operator):** the reconciliation is **DAILY T+1**, not weekly — each day reconciles the prior trading day's
paper vs a batch-rerun of that day (a week = 7 daily reports). Renamed `reconcile_week`→`reconcile_day` +
`WeeklyReconReport`→`DailyReconReport` across `unified-api-contracts@4c058ce` + `batch-live-reconciliation-service@e36163a`
+ the codex SSOT/plan/CLAUDE.md. (Hit + reconciled a workspace promotion-lag: the PM `workspace-manifest.json` was 10
commits behind main, false-blocking the version-alignment gate — backmerged the version bumps.)

**P3.2 PassiveLedger shipped (`utl@09885861`)** — completes the ledger materialisation CORE: 3 of 4 SSOT ledgers now have
pure, tested synthesisers (InstructionLedger P3.1 + PositionLedger P3.3 + PassiveLedger P3.2; PricingLedger = marks,
already exists). The complete as-if-filled accounting (trades + positions/balances + carry accruals + P&L) is built and
unit-tested across UTL.

**Session tally (all QG-green + tested):** Phase 0 contract (uac@12597d8) · P1.1 pricing SSOT (uac@bc4c756 + es@e11854e5)
· P1.5 rule · P4.1 reconcile_day keystone (blrs@7a84db8c→e36163a) · P3.1/P3.3/P3.2 ledger core (utl@41d50461→09885861) ·
the 3-concepts/2-realities architecture correction · the daily-T+1 correction. **The entire pure-logic + accounting core
of the determinism spine is DONE.** What remains is service INTEGRATION + behavioural fill-path changes (P2 event keying,
P3.x engine-wiring, P1.4 GroupCRunner the linchpin, P1.1-strategy PASSIVE_BBO correction, P3.4/P3.5, P4.3, P5/P6, P7) —
each now ships WITH a `reconcile_day` proof (the build-order rule). These are interconnected service changes on live/
backtest code: sequenced + harness-validated, not rushed.

### 2026-06-19 — Operator eyeball surface SHIPPED (P3.4 + P5.1)

`client-reporting-api@0d9b1bec` (14 tests) — the `/positions` + `/pnl` routes now return REAL ledger-derived state
(positions + balances per venue/instrument/share_class + realized/unrealized/total PnL) via the UTL
`materialize_position_ledger` helper; the hardcoded `realized_pnl="0.00"` + the mock positions are deleted; empty ledger
→ honest zero. The pluggable `read_ledger_rows` seam returns `[]` until the engine-wiring phase populates the GCS ledger.
**Finding (for engine-wiring): PASSIVE accrual rows are a quote cash-flow, not a base-asset qty — fold TRADE→positions,
PASSIVE→realized PnL separately (feeding passive rows to the position materializer corrupts net_qty).**

**The READ side is now complete end-to-end** (contract → ledger accounting → views → recon proof). The remaining work is
the WRITE/INTEGRATION side: the engine must emit keyed `TradeFillRecord`s (P2, the gateway), call the ledger writers
(P3.1-wiring) + capture the RunManifest, run Group C smart matching in batch (P1.4 linchpin), then the daily-T+1 rerun
(P4.3) feeds `reconcile_day`. These are interconnected behavioural changes on live/backtest service code — P2 unblocks
the rest; each ships with a `reconcile_day` proof.

### 2026-06-19 — READ SIDE COMPLETE (P3.5 HWM shipped)

`client-reporting-api@52d8b7d` — HWM off the materialised ledger NAV (advances-only, never max-equity). **The entire
READ side of the determinism spine is now done end-to-end + tested**: the contract (Phase 0) → all four ledgers
(Instruction/Position/Passive synthesisers + Pricing marks) → the operator eyeball surface (positions / balances per
venue·instrument·share_class / realised+unrealised P&L / HWM) → the determinism-PROOF engine (`reconcile_day`). ~10 units
across 6 repos (uac, es, utl, blrs, client-reporting-api, pm), every one QG-green + unit-tested.

**Remaining = the WRITE / INTEGRATION side** (gated on P2): the engine must emit keyed `TradeFillRecord`s (P2 — the
gateway, an execution-service event-format change the existing aggregate stages also read, so it needs deliberate
migration not a rush), then call the ledger writers + capture the RunManifest (P3.1-wiring), run Group C smart matching
in batch (P1.4 — the linchpin), correct the strategy-service PASSIVE_BBO benchmark (P1.1-strategy), the daily-T+1 rerun
(P4.3) + recon stage (P4.2), Slack digests (P6), and the short-window e2e proof (P7). Each ships WITH a `reconcile_day`
proof. These are interconnected behavioural changes on the live trading engines — the next focused tranche.

### 2026-06-19 — WRITE-SIDE TRANCHE began: P1.1-strategy SHIPPED (the PASSIVE_BBO correction + UAC SSOT wiring)

`strategy-service@b136f70e` + `batch-live-reconciliation-service@1a12500` (both QG-green). The strategy-service
`BenchmarkFillEngine` now prices the trade benchmark through the UAC `benchmark_fill_price` SSOT (building the flat
`BenchmarkPricingContext` from the typed `MarketStateSnapshot` — TWAP/VWAP pre-computed, ARRIVAL_MID None-fallback to mid
preserved) — so strategy-service Group B and execution-service Group C / paper compute the benchmark from ONE function,
the fill-model drift is structurally impossible. **The PASSIVE_BBO convention is corrected** (LONG→bid / SHORT→ask, the
correct passive-maker semantics; was LONG→ask / SHORT→bid — the exact paper-sim ≠ batch-sim drift the operator named).
Landed WITH the build-order `reconcile_day` proof: `test_corrected_passive_bbo_benchmark_reconciles_deterministically`
(ε=0 paper≡batch) + `test_passive_bbo_drift_is_a_fill_model_bug` (OLD convention → classified FILL_MODEL_DRIFT). Phase 1
of the simulation-SSOT is now complete on BOTH engines (UAC SSOT + execution-service adapter + strategy-service engine).

**Side-finding (captured, foreign):** `e2e-testing/scripts/defi/run_dr_drill_cutover.py` carries 37 pre-existing ruff
errors (15 auto-fixable RUF100 unused-noqa + others) that the strategy-service peripheral-dir QG flags **warn-only** (did
not block). Out of this plan's surface (a peripheral DR-drill script, last touched `e2e-testing@8bd7c74`) — noted here so
the owning epic can clean it; not blocking the determinism spine.

**Next (this tranche):** P2 (the gateway) — make the strategy/execution engines emit per-trade keyed `TradeFillRecord`s
on every fill; migrate the date-level float-metric aggregate recon stages onto the keyed records (no parallel old+new).
Then P3.1-wiring (engine calls `ledger_row_from_trade_fill` → GCS InstructionLedger + RunManifest capture), P1.4
GroupCRunner (the linchpin), P4.2/P4.3 (recon stage + batch-rerun-from-manifest), P3.4 seam → real GCS, P6 Slack, P7 the
short-window ε=0 e2e proof.

### 2026-06-19 17:52 UTC — autonomous write-side push PAUSED on session limit (resets 18:30 UTC)

The autonomous write-side dispatch ran, parallelised across repos, then hit the account session/usage limit (resets
18:30 UTC). State:
- **SHIPPED + flipped**: P1.1-strategy — `strategy-service@b136f70e` routes `BenchmarkFillEngine` through the UAC
  `benchmark_fill_price` SSOT + the `PASSIVE_BBO` correction, validated by a `reconcile_day` ε=0 fixture (the hardest
  behavioural fill-model fix is DONE).
- **WRITTEN but orphaned-uncommitted on disk** (the limit killed the agents pre-commit — NOT lost, resume from these):
  - UTL `unified_trading_library/ledger/run_writer.py` (P3.1-wiring: the RunManifest + ledger GCS writer, 274 lines) +
    `tests/unit/ledger/test_run_writer.py` + the coverage-ratchet bump + `ledger/__init__` export.
  - batch-live-reconciliation-service: the P4.2 daily-T+1 `reconcile_day` recon stage (reported QG-green; was waiting on
    UTL to go clean before quickmerge — dirty-deps rule).
  - strategy-service: 1 uncommitted file (part of P2/P3.1 engine wiring).
- **NOT STARTED**: P1.4 GroupCRunner (the linchpin), P4.3 batch-rerun-from-manifest CLI, P6 Slack, P7 e2e proof.

**RESUME (after 18:30 UTC reset)**: re-dispatch the autonomous write-side prompt. It reads this log + the on-disk WIP and
continues: QG + ship the orphaned UTL `run_writer.py` (unblocks P4.2) → ship P4.2 → then P1.4 → P4.3 → P6 → P7. The
on-disk WIP is the precise resume point; verify it QG-green before shipping (don't ship un-QG'd). Live leg stays
BLOCKED-OPERATOR.

### 2026-06-19 ~18:10 UTC — session-limit-orphaned WIP RECOVERED + shipped (P2 / P3.1-wiring / P4.2 / P6-alert)

The session-limit reset; I recovered + shipped the orphaned-on-disk write-side WIP (verified QG-green before each ship):
- **P3.1 write side** — `unified-trading-library@3cc6e3dd`: `ledger/run_writer.py` (`write_run_ledger` / `write_run_manifest`
  / `fill_to_ledger_jsonl_obj` / `instruction_ledger_jsonl`) — persists keyed fills as InstructionLedger JSONL + the
  as-of RunManifest to the run's `ledger_root`.
- **P2 gateway + P3.1 engine wiring** — `strategy-service@fccee669`: `engine/backtest/ledger_emit.py` maps each
  `BenchmarkFillRecord`→keyed `TradeFillRecord` (`make_trade_key` + side/qty/fill/fees) and calls the run_writer seam.
  (Fixed an over-eager import-pattern `--fix` that had broken the UTL import + an in-function datetime import.)
- **P4.2 + P6 alert** — `batch-live-reconciliation-service@4b611db`: `daily_determinism_stage.py` (runs `reconcile_day`
  at T+1) + `ledger_reader.py` + `recon_alert_client.py` (posts the verdict to alerting-service).
- Two ships used the sanctioned dirty-deps direct push (UTL carries FOREIGN uncommitted WIP in `honest_coverage_ratchet`
  — a different workstream, left untouched).

**P1.1 was already shipped pre-limit** (`strategy-service@b136f70e`, PASSIVE_BBO correction). **Remaining**: P1.4
GroupCRunner (linchpin), P4.3 batch-rerun-from-manifest CLI, the P6 daily ledger Slack digest, P7 short-window e2e ε=0
proof. Live leg stays BLOCKED-OPERATOR.

**Process fix shipped** (`pm@aa3506ee8`): CLAUDE.md now bans bare `ScheduleWakeup` for unattended resume (it doesn't fire
when the session is idle — 2nd incident) — use a tracked `run_in_background` waiter instead.
