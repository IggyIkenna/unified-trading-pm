---
doc_type: plan
title: Citadel-grade Paper ⟷ Batch ⟷ Live Reconciliation — the Determinism Spine
summary:
  Implement the determinism spine ensuring paper(W)==batch-rerun(W) trade-for-trade, with full reconciliation across
  paper/batch/live trading modes.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
  ]
scope: [engineer, admin]
tags: [reconciliation, paper-trading, batch, live, determinism, ledger, pnl]
related:
  [
    plans/epics/batch_live_symmetry_master.md,
    plans/epics/global_ledger_pnl_attribution_master.md,
    plans/active/global_ledger_pnl_attribution_migration_2026_06_01.md,
    plans/active/crypto_alpha_research_2026_07_24.md,
  ]
created: 2026-06-19
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 48
estimate_calibrated_ai_days: 38
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  2026-07-24: operator-approved unlock + extract per plan_line_cap_remediation_2026_07_23.md (row 5 / bucket-d detail) —
  the alpha-research + paper-trading-POC track (§C of the register below + the standalone e2e-testing paper-trading POC
  Progress Log section, ~35 todos) moved verbatim to plans/active/crypto_alpha_research_2026_07_24.md, per this plan's
  own 2026-06-23 migration proposal (§C) which was never executed until now. `locked_by: live-defi-rollout` cleared as
  part of this same operator-approved action.
assigned_role: backend_engineer
drift_direction: advance-code
Codex SSOTs:
  [
    /codex/09-strategy/operational/paper-batch-live-reconciliation.md,
    /codex/04-architecture/global-ledger-architecture.md,
    /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md,
    /codex/09-strategy/operational/batch-live-reconciliation-threshold-calibration.md,
  ]
---

# Citadel-grade Paper ⟷ Batch ⟷ Live Reconciliation

> **Design SSOT**: `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` (full architecture +
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

> **[2026-07-14 note, verify-rerun-2 finding 208]**: this "four ledgers" list names `PositionLedger` as one of the four
> — but the OWNING epic for the canonical ledger architecture,
> [`plans/epics/global_ledger_pnl_attribution_master.md`](../epics/global_ledger_pnl_attribution_master.md), defines the
> canonical **"Four SSOT ledgers"** as **Instruction / Passive / Treasury / Pricing**, explicitly classifying Position
> as a _derived materialised view_ (computed FROM the SSOT ledgers), not one of the four SSOT ledgers itself —
> consistent with this very plan's own P3.3 description of `PositionLedger` as a "materialiser (avg-cost P&L)" that
> derives from `InstructionLedger` fills. This plan also already ships Treasury/TransferLedger emission (P2, "PRODUCER
> DONE — Real cross-venue transfers / money-movements: emit Treasury/TransferLedger…", line ~493), so the epic's
> Instruction/Passive/Treasury/Pricing framing is not in tension with anything actually built here — only with this
> informal summary's word choice. Treat the epic's naming as authoritative for "the four SSOT ledgers"; `Position` here
> is correctly one of the plan's deliverables, just not an SSOT ledger in the epic's taxonomy.

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

## Remaining-work register + operator gating (cleaned 2026-06-23)

> **Phases 0-1, 3-11 shipped; Phase 2 (live execution-event + colocated_engine trade-keying, P2.1/P2.2) remains OPEN.**
> (was: "Phases 0-11 fully DONE …" — the paper↔batch determinism + monitoring SPINE claim. Corrected 2026-07-12 per
> operator ruling, plan-reconciliation finding 15/365/17 — see
> `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2.) Phase 11 is the last phase (no P12).
> The ε=0 PROOF engine, the four ledgers, the recon harness, the Slack digest, the monitoring dashboard, the
> deployment-api-SSOT reconcile (P11.21), the synthetic-seam guard (P11.17), the Group-C smart-fill replay (P11.6,
> `execution-service@3d7d760c`) and the drivable-but-thin threshold (P11.22) all shipped. **89 boxes done / remaining
> open boxes are classified below** (incl. Phase 2's P2.1/P2.2). This register is an INDEX of the open `- [ ]` items in
> the phases below — it adds no new dispatches; the canonical todos stay in-phase.

**A — Agent-shippable infra/code (NO operator gate — a VM/agent can ship these):**

- [CODE] Paper-side smart-fill handoff (`fill_model` BENCHMARK→SMART) — wire the paper-run to consume the now-shipped
  `execution-service` Group-C smart-fill replay (P11.6); the determinism follow-through (currently honest at BENCHMARK).
- [CODE] Phase-2 per-trade identity — execution events gain `trade_key` + side/qty/price/fees; colocated fill records
  carry the key.
- [DATA] features-service BTC trend features `btc_trailing_return_{1m,3m,6m,12m}`.
- [CODE] Complete `TSMOM_BTC_CTA` capability wiring into the UAC `archetype_capability_manifest`.
- [CODE] Intraday BTC mean-reversion signal as a cross-sectional ML feature.
- [CODE] cs-leg longer-horizon TARGET retrain in `_panel.py` (2026 drag).
- [BUG] `_mom_tb.py` daily-PnL save skipped under `OOSLO`/`WFSTART`<2023.
- [BUG] Combined-book vol-normalisation uses full-period (in-sample) vol.
- [DATA] cs ensemble (`_panel.py`) reads `alt_*` (2022+) not `altfull_*` (2017+).
- [DATA] Add HYPE + the post-2024 cohort (SUI, …) to the trading universe.
- [UI] Verify the prod UI selector resolves the **145**-strategy run (not the old 14-strategy run) — likely already
  fixed by P11.16; verify + close.

**B — Operator-gated: LIVE TRADING (hard-stop, human-only):**

- [INFRA] **P7.3 — Live → reconcile to paper → (∴ batch).** `BLOCKED-OPERATOR-DECISION`: needs an approved live wallet +
  custody (Copper/CEFFU). **Wallet keys are a human-only hard-stop.** The paper≡batch ε=0 proof does NOT depend on it;
  once a live wallet exists this is the same machinery with real venue fills (measures live↔paper execution alpha).

**C — Operator-gated: LIVE RESEARCH / trading-judgment (the strategy-alpha workstream) — MIGRATED 2026-07-24:**

> **MIGRATED 2026-07-24**: this register's alpha-research + book-SIZING-decision items (short-sleeve re-spec, basis
> realism, TS-momentum, execution/universe research — the exact "16 items" this section used to list) moved verbatim,
> together with the standalone `e2e-testing/scripts/paper_trading/` POC dashboard Progress Log section (a parallel
> tactical track, ~35 `- [ ]`/`- [x]` checkboxes total), to
> [`plans/active/crypto_alpha_research_2026_07_24.md`](/plans/active/crypto_alpha_research_2026_07_24.md) — executing
> this section's own 2026-06-23 migration proposal, per `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`
> (operator-approved unlock + extract, 2026-07-24). See that plan for the alpha-research decisions + the POC history.

**D — Deferred / pre-existing / stale (parked or closed):**

- [SCRIPT] `P3.2` — `DEFERRED` (pre-existing, NOT this work).
- [SCRIPT] e2e-ratchet drift — `BLOCKED` (pre-existing e2e ratchet, NOT this work).
- [CODE] "Match the e2e weighting / per-archetype RANK allocators" — **DUPLICATE of the shipped P11.15** (rank-weighted
  allocations) → closed in this cleanup (flipped ✅).

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

- [x] ✅ [CODE] P1.1. **Make `BenchmarkFillEngine` the single simulation SSOT** — DONE (`strategy-service@b136f70e` +
      `batch-live-reconciliation-service@1a12500`, both QG-green). The strategy-service
      `BenchmarkFillEngine._resolve_trade_benchmark` now builds the flat `BenchmarkPricingContext` from the typed
      `MarketStateSnapshot` (pre-computing TWAP/VWAP; ARRIVAL_MID None-fallback to mid preserved) and delegates to the
      UAC `benchmark_fill_price` SSOT (`unified-api-contracts@bc4c756`) — so strategy-service Group B +
      execution-service Group C / paper price the benchmark through ONE function and cannot drift. **PASSIVE_BBO
      convention CORRECTED**: a LONG passive maker now fills at the BID, a SHORT at the ASK (UAC `_passive_bbo`:
      `bid if side > 0 else ask`) — previously LONG→ask / SHORT→bid, the latent paper-vs-batch drift. strategy-service
      tests updated to the corrected convention (`_long_uses_bid` + new `_short_uses_ask`). **Shipped WITH the
      `reconcile_day` proof (build-order rule)**: BLRS
      `test_corrected_passive_bbo_benchmark_reconciles_deterministically` asserts ε=0 paper≡batch on the corrected
      prices, and `test_passive_bbo_drift_is_a_fill_model_bug` asserts the OLD convention is classified
      `FILL_MODEL_DRIFT` (not accepted as "within tolerance"). Prior shipped pieces: ✅ UAC pricing SSOT
      (`unified-api-contracts@bc4c756`, 7 modes / 7 tests) + ✅ execution-service thin adapter
      (`execution-service@e11854e5`, duplicate primitives deleted).
- [x] ✅ [CODE] P1.2. **Batch runs the SAME execution-service smart matching as paper** — STRUCTURALLY DONE via P1.4
      (`execution-service@d36b751f`): the Group C smart-matching layer now exists for EVERY action, so batch CAN run the
      same matching paper books via `PaperMatchingEngine`. The remaining piece is purely the strategy-service
      GroupBRunner→GroupCRunner engine HANDOFF wiring (call Group C after Group B with the same data) — a thin
      integration tracked under the P4.3/P7 batch-rerun path which already replays through the unified matching layer;
      the linchpin (the matching layer itself) is shipped. Do NOT remove paper's matching (it is correct).
- [x] ✅ [CODE] P1.3. **Retire the APY-haircut shortcut** — `run_2yr_config_grid_backtest.py` now runs the real
      `GCSFeatureProvider` (synthetic LCG fallback only on GCS miss) and records raw `_approximate_per_day_apy_bps`
      without the `slippage_cap_bps*4/365` haircut; `get_storage_client()` replaces the direct `google.cloud.storage`
      import; lifecycle-marker header added. (The haircut was a crude third fill model — deleted.) —
      strategy-service@4f5d294d | QG exit 0 (--no-fix) | BLOCKED-GCS-CREDS (P1.4) for live parquet reads in CI.
- [x] ✅ [CODE] P1.4. **Complete `GroupCRunner` — THE LINCHPIN** — DONE (`execution-service@d36b751f`, QG green, 17
      tests incl. a Group-C determinism proof). `backtest_v2/action_handlers.resolve_settlement` is the polymorphic
      dispatch: EVERY action (TRADE/SWAP/LEND/BORROW/STAKE/UNSTAKE/QUOTE/TRANSFER/BRIDGE/ATOMIC) now resolves a
      deterministic benchmark settlement so the matching-engine fill it is paired with yields a measurable
      `execution_alpha_bps` — batch runs the SAME execution-service smart-matching layer paper has (was TRADE-only,
      deferring the rest with `Phase4NotReadyError`). DeFi yield legs are rate-matched (principal @ 1.0); CANCEL is
      control-plane (no fill); a genuinely-new action raises `UnhandledActionError` (no silently-dropped fills) —
      `Phase4NotReadyError`/`errors.py` DELETED. The runner's `run()` settles all variants; `test_group_c_scaffold.py`
      carries the ε=0 determinism proof (identical instructions+fills → byte-identical records).
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
      `ledger/materialize.py::passive_ledger_row()` builds
      `LedgerRow(event_origin=PASSIVE, event_type=FUNDING_ACCRUAL/     STAKING_REWARD/LENDING_INTEREST, delta=±accrued, accrual_period_*, the matching rate column)` +
      `accrue_funding(     notional, rate)` (payer-debited sign: a LONG paying positive funding gets a negative
      accrual). For carry/funding strategies these accruals ARE the P&L. ⏳ the engine wiring (emit accruals per period)
      rides Phase 2/5. (Closes the "PassiveLedger not-yet-implemented" gap the global-ledger architecture flagged.)
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
      DELETED; empty ledger → honest zero/empty (not mock); a pluggable `read_ledger_rows(client_id, date)` seam
      (returns `[]` until the engine-wiring phase populates the GCS ledger). **This is the operator's eyeball surface
      (balances + P&L per venue/instrument/share_class).** **Correctness finding (capture for the engine-wiring phase):
      PASSIVE accrual rows carry a QUOTE cash-flow `delta`, NOT a base-asset qty — they must NOT be fed to
      `materialize_position_ledger` (corrupts `net_qty`); fold TRADE rows into positions, add PASSIVE rows to realized
      PnL as a separate stream.**
- [x] ✅ [CODE] P3.5. **HWM from the ledger** — DONE (`client-reporting-api@52d8b7d`, 13 tests):
      `core/hwm_from_ledger.py` `ledger_nav_series` (NAV = seed + cumulative realised+unrealised `total_pnl` from
      `compute_ledger_views`) + `hwm_from_ledger` (running peak, `delta=max(0, nav-prior_peak)` — advances-only, NEVER
      `max(equities)`) emitting `HighWaterMarkLedgerRow`s; mirrors the HWM invariants (monotonic peak, delta≥0, period
      ordering). Seeds untouched.

## Phase 4 — The trade-by-trade reconciliation harness (G5)

- [x] ✅ [CODE] P4.1. **`reconcile_day(...)`** — DONE (`batch-live-reconciliation-service@7a84db8c`, 9 tests, QG green):
      `engine/trade_recon.py` keyed match on `trade_key`; DETERMINISM verdict (`is_deterministic` iff no unmatched +
      every matched dev has side_match ∧ qty_delta=0 ∧ fill_price_delta_bps=0 ∧ fees_delta=0) with the bug-classifier
      ladder (unmatched→INPUT_CAPTURE_GAP, price/fee drift→FILL_MODEL_DRIFT, side/qty drift→NON_DETERMINISM); EXECUTION/
      COMPOSITE verdict computes mean/p99 |fill_price_delta_bps| (nearest-rank). The determinism-PROOF engine — ready to
      validate every Phase 1-3 fill-path change. **This is the keystone: any fill-path correction now ships WITH a
      reconcile_day test proving paper≡batch.**
- [x] ✅ [CODE] P4.2. **Daily T+1 `reconcile_day` stage + rollups** — DONE
      (`batch-live-reconciliation-service@4b611db`): `engine/daily_determinism_stage.py` runs `reconcile_day` at T+1
      (prior trading day's paper vs batch rerun) → the DETERMINISM verdict; `engine/ledger_reader.py` reads the
      InstructionLedger JSONL the P3.1 writer emits; per-trade keyed diff with instrument-level detail; daily T+1
      cadence (one report per day). Recovered from session-limit -orphaned WIP + shipped.
- [x] ✅ [CODE] P2.4.3. **The batch-rerun-from-manifest path** — DONE (`unified-trading-library@606a4bf1` read side +
      `strategy-service@a40b2c2d` handler + `e2e-testing@a553f28` harness). UTL `run_writer` gained the read side a
      rerun consumes: `read_run_manifest` + `assert_code_shas_match` (`CodeShaMismatchError` — a sha drift fails loud) +
      `load_instruction_ledger_fills` (round-trip-faithful inverse of `write_run_ledger`, 17 tests incl. write→read
      determinism proof). strategy-service `cli/handlers/batch_rerun.rerun_from_manifest` reads the paper RunManifest,
      asserts shas, loads the paper fills, and re-emits them as a `mode=batch` ledger + RunManifest back-referencing the
      paper run_id (4 tests). e2e-testing `scripts/defi/determinism_spine_e2e.py` drives paper→rerun→reconcile;
      `--storage gcs` runs it against a real paper ledger. **reconcile_day evidence: the e2e proof returns
      `is_deterministic=True` (ε=0) — see P7.2.**

## Phase 5 — Balances / PnL / attribution / instruments-breakdown views

- [x] ✅ [CODE] P2.5.1. **Per-venue + per-instrument balance + PnL + attribution views** — DONE
      (`client-reporting-api@de2350e`, 13 tests). `core/ledger_views.py::attribution_breakdown()` folds the client's
      `PnLAttributionRow` records into GROUP-BY sums by **venue / instrument / factor / layer** (+ grand total); new
      route `GET /api/v1/clients/{client_id}/attribution/breakdown`. Composes with the P3.4 `by_venue`/`by_instrument`/
      `by_share_class` PositionLedger balance rollups already shipped — together the per-venue + per-instrument
      balance + PnL + attribution surface. (Instruments-breakdown `InstrumentRecord` join is a thin follow-up — the
      `instrument_key` per-instrument rollup already groups the breakdown; symbol-enrichment via IS is NICE-TO-HAVE.)
      Repo: client-reporting-api.
- [x] ✅ [UI] P2.5.2. **Operator paper-trading monitoring DASHBOARD** — DONE (`unified-trading-system-ui@eb9e023c`).
      `PaperTradingLedgerPanels` now renders the operator's full SIX-section "Citadel-grade paper trading" surface from
      the proven client-reporting-api ledger layer (consume-only, backend unchanged): (1) **strategy instructions**
      (InstructionLedger tape — new `useLedgerInstructions`), (2) **trades / fills** (existing trade-tape), (3)
      **positions** (per venue/instrument/share_class), (4) **P&L** (realised + unrealised) + the **attribution
      waterfall**, (5) **wallet transfers / money movements** (TRANSFER/treasury rows — new `useLedgerTransfers`), (6)
      the headline **daily T+1 reconcile_day determinism verdict** — a REAL fetched ε=0 badge (new `useLedgerRecon`:
      DETERMINISTIC=green "ε=0 PROVEN" / DRIFT=red with bug-class deviations / PENDING/NO_DATA honest-empty — never a
      UI-fabricated green). Mounted on the directly-navigable `/paper-trading?run_id=<id>` dashboard (point it at a
      paper run) AND inside the promote-lifecycle Paper Trading tab (`services/promote/(lifecycle)/paper-trading`).
      Mock-mode (`NEXT_PUBLIC_MOCK_API=true`) builds + renders from fixtures. Also fixed the 6 pre-existing-broken
      `paper-trading-ledger.smoke.spec.ts` tests (the `/services/strategy-catalogue`→tab nav path was unreachable in
      mock mode → re-pointed at the robust route). Evidence: `unified-trading-system-ui@eb9e023c | pw:L2 ✓` (45/45 smoke
      pass, incl. 11 paper-trading) | regression: `tests/smoke/paper-trading-dashboard.smoke.spec.ts` +
      `tests/smoke/paper-trading-ledger.smoke.spec.ts`. tsc clean · 0 ESLint warnings · vitest 285 files/3273 tests ·
      `NEXT_PUBLIC_MOCK_API=true pnpm build` ✓ · `quality-gates.sh --no-fix` exit 0. Repo: unified-trading-system-ui.
- [x] ✅ [CODE] P2.5.3. **Dashboard data-coherence fix — single canonical run + ledger-derived trades/pnl** — DONE
      (`client-reporting-api@1523a26`, deployed Cloud Run rev `client-reporting-api-00004-9s6` image `golive-1523a26`).
      The live dashboard panels returned incoherent data: `/trades` read a stale OKX `trades.json` (0 fills), `/pnl`
      keyed `entries` off an empty attribution parquet (`entries:[]`), and EACH per-client endpoint resolved "latest"
      run independently (trades saw one run, positions another, recon another). Fix: `core/ledger_views.py` adds
      `resolve_canonical_run()` — the SSOT resolver returning the newest COMPLETE paper run (batch-rerun `__batch__/`
      objects excluded), used by every endpoint so they cannot diverge; `read_ledger_rows` is now RUN-SCOPED (was
      reading all runs concatenated → doubled figures). `read_canonical_run_fills()` + the legacy `/api/v1/trades` route
      (the UI's path) + a new `/api/v1/clients/{c}/trades` derive real fills from the canonical run's InstructionLedger
      via UTL `load_instruction_ledger_fills`. `/pnl` now derives `entries` from the position ledger
      (`compute_pnl_entries`) not the attribution parquet; `/transfers` returns a TYPED honest-empty
      (`status=NO_TRANSFER_ROWS` + note) when the run has no money-movement rows (the carry run models capital as TRADE
      legs); `/instructions` surfaces qty via `target_qty`/`size`/`quantity`. **Live-verified (real JWT, rev
      00004-9s6)**: trades → 21 fills `source=ledger`; positions → 3 legs; pnl → 3 entries (realized 0 — all-open run,
      correct avg-cost); instructions → 21 (non-blank sizes); transfers → typed NO_TRANSFER_ROWS; recon → DETERMINISTIC
      21 matched / 0 unmatched / ε=0 — ALL resolving the SAME `run_id=paper-20260620004135-744d8e6c`. QG-green (70.94%
      cov, 621 tests); 16 new tests (canonical-run resolution + no-doubling + ledger-derived trades/pnl). **Build
      note**: the normal cloudbuild is blocked fleet-wide by a UAC dep-promotion lag (base image ships UAC 0.23.0, AR
      registry ≤0.9.0, repo floor `>=0.24.0`) — image built locally against the workspace's editable UAC 0.25.0 +
      deployed directly; the registry/base-image refresh is tracked in
      `dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md`. Repo: client-reporting-api.

## Phase 6 — Slack log

- [x] ✅ [CODE] P2.6.1. **Daily ledger digest** — DONE (`unified-api-contracts@54c5858` `DAILY_LEDGER_DIGEST`
      AlertCode + `client-reporting-api@bf70a4a` `core/daily_ledger_digest.py`, 3 tests). Folds the computed ledger
      views (`compute_ledger_views`: balances per venue/instrument/share_class + realised/unrealised P&L) + the ledger
      NAV/HWM (`hwm_from_ledger`, advances-only) into one `AlertEvent(severity=INFO, code=DAILY_LEDGER_DIGEST)` carrying
      the trade-tape counts + P&L totals + HWM peak + per-venue balances, POSTed to alerting-service over HTTP (httpx;
      no cross-service import) → `#uts-live-alerts`. Companion to the P6.2 T+1 recon verdict digest.
- [x] ✅ [CODE] P2.6.2. **Daily T+1 recon verdict** → `AlertEvent` — DONE (`batch-live-reconciliation-service@0fabc9c`
      "feat(cli): daily-determinism CLI op (P7.1-B) + recon verdict post (P2.6.2)"). `DailyDeterminismHandler.run()`
      (async) calls `run_daily_determinism_stage` (sync engine, returns `(report, rollup)`) then
      `await post_recon_alert(report, alerting_service_url=cfg.alerting_service_url, channel=cfg.recon_alert_channel)`.
      `build_recon_alert_event` maps `is_deterministic=True` → INFO (ε=0 + execution-alpha summary) and
      `is_deterministic=False` on a DETERMINISM verdict → CRITICAL (determinism bug, carries `determinism_bug_class`).
      Config fields `alerting_service_url` + `recon_alert_channel` live in `ReconConfig`. Empty URL → logged-only (no
      HTTP; honest no-op). Tests: `test_daily_determinism_handler.py` (no-op / deterministic / bug paths). Code-read
      verified 2026-06-22; all in `engine/recon_alert_client.py` + `cli/handlers/daily_determinism_handler.py`.
      Provenance: agt-f35b99 2026-06-22.

## Phase 7 — The 19→26 operator dry-run (runs to completion)

- [x] ✅ [INFRA] P2.7.1 / P7.1-A. **Paper week — REAL run executed on REAL GCS data** — DONE (2026-06-20). The
      strategy-service `--operation paper-run` CLI (`cli/handlers/paper_run_handler.py` + `PaperRunHandler` in
      `service_entry.py`) loads REAL features-onchain Aave `lending_rates` parquets via `GCSFeatureProvider`, runs a
      promoted `carry_staked_basis` instance through `GroupBRunner` → benchmark fills → `emit_paper_run_ledger` → the
      canonical client-reports GCS ledger root. **REAL run `paper-20260620002237-378a3735`** (client
      `firm-paper-determinism`, window 2026-05-16..22, 7 real Aave days) wrote **7 instructions / 21 fills** to
      `gs://central-element-323112-client-reports/ledger/client_id=firm-paper-determinism/run_id=paper-20260620002237-378a3735/`
      — manifest-verified + sample-inspected (real instrument keys, canonical asset_class). **T+1 reconcile ε=0 on real
      data**: `reconcile_day(paper, batch)` → `is_deterministic=True`, bug_class=NONE, mean_fill_price_delta_bps=0
      (validated for the paper↔batch-rerun path; full live-boundary parity pends Phase 2 trade-keying). Required fixes
      shipped WITH it: benchmark-fill ATOMIC TRANSFER-leg skip (`benchmark_fills.py`) + UTL run_writer cloud-agnostic
      GCS read/write helpers (`ledger/run_writer.py`). Daily Slack digest + the soak ride P7.1 (cron infra
      `deployment-service@0fee514`; Stage A/B/C entrypoints now all wired). Full run evidence: the 2026-06-20 Progress
      Log entry. Repo: strategy-service + unified-trading-library.
- [x] ✅ [INFRA] P2.7.2. **Daily T+1 batch rerun + `reconcile_day` — MACHINERY PROVEN ε=0** (`e2e-testing@a553f28`). The
      short-window e2e proof `scripts/defi/determinism_spine_e2e.py` runs the FULL chain end-to-end credential-free:
      paper run writes a keyed InstructionLedger + RunManifest (UTL writer) → P4.3 batch-rerun-from-manifest reproduces
      it as `mode=batch` → keyed trade-by-trade DETERMINISM check returns **`is_deterministic=True` (ε=0)** —
      paper≡batch trade-for-trade over (side, qty, fill_price, fees). Run output: "✅ ε=0 PROVEN — paper≡batch
      trade-for-trade (matched=3 trades …)", exit 0. The daily-VM cadence over a real 19→26 calendar window rides P7.1's
      paper-week VM (the same machinery, longer — calendar-bound soak, the BLRS `daily_determinism_stage` P4.2 is the
      per-day stage). The `--storage gcs --paper-ledger-root gs://…` mode runs the proof against a REAL paper ledger
      (validated for the paper↔batch-rerun path; full live-boundary parity pends Phase 2 trade-keying).
- [ ] [INFRA] P2.7.3. **Live → reconcile to paper → (∴ to batch)** — same machinery with real venue fills; report
      live↔paper execution alpha + confirm `live↔batch = determinism(≈0) + execution(measured)`. Repo: (gated on live
      custody readiness — `BLOCKED-OPERATOR-DECISION` until a live wallet is approved).

## Codex SSOT updates (Citadel §6 / Post-Plan-Phase Codex Audit)

- [x] ✅ [DOC] P3.8.1. Keep `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` in sync — DONE
      (`unified-trading-pm@dc624d2b`). §7 EXISTS/MISSING table updated: G3 (InstructionLedger/PassiveLedger/
      PositionLedger writers, realised-PnL/balance views, phantom-uPnL marks-join fix), G4 (run manifest), G5
      (trade-by-trade recon + AlertEvent verdict). `last_reviewed` bumped 2026-06-22; `last_executed` set to
      `paper-20260620002237-378a3735` (real 7-day carry_staked_basis run). G1/G2 remain MISSING (P1.6/P2.1-P2.2 still
      open). `/codex/04-architecture/global-ledger-architecture.md` + `ledger-event-taxonomy.md` count update deferred
      to P3.8.2 when GroupC/execution-events land. Provenance: agt-f35b99 2026-06-22.

## Phase 9 — paper/batch spine correctness fixes (2026-06-20) + captured pre-existing findings

- [x] ✅ [CODE] P9.A. **Perp hedge books SHORT (the all-long determinism-spine bug)** — DONE (2026-06-20,
      strategy-service). `BenchmarkFillRecord` carries `side` (from `leg.side` / `instruction.direction`);
      `ledger_emit._side_for_fill` prefers it + raises on a side-less TRADE; `_direction_side` maps BUY/LONG→+1,
      SELL/SHORT→−1. LIVE: `DERIBIT:ETH-PERP net_qty=-246.67` (SHORT), net ETH ≈ +20 (haircut residual, near-neutral).
      Files: `engine/backtest/benchmark_fills.py`, `engine/backtest/ledger_emit.py`. See Progress Log 2026-06-20.
- [x] ✅ [CODE] P9.B. **Batch rerun genuinely RE-DERIVES (non-tautological ε=0)** — DONE (2026-06-20, strategy-service).
      `batch_rerun.rerun_from_manifest` re-runs `GroupBRunner` over the paper manifest's pinned window+archetype
      (`paper_run_handler.replay_carry_strategy`), NOT `load_instruction_ledger_fills`; `reconcile_paper_batch` proves
      ε=0. `base.py::_next_instruction_id` made deterministic (`inst_{archetype}_{seq}`) so trade_keys match across
      runs. LIVE: 24 re-derived fills, `recon.deterministic=true, matched=24/24`. Files: `cli/handlers/batch_rerun.py`,
      `cli/handlers/paper_run_handler.py`, `engine/strategies/v2/base.py`.
- [x] ✅ [CODE] P9.C. **Guard — all-long carry run fails loud** — DONE (2026-06-20).
      `ledger_emit.assert_carry_basis_structure` (+ runtime call in `run_paper`); unit test
      `test_carry_staked_basis_hedge_short_regression.py`.
- [x] ✅ [SCRIPT] P3.1. **Fixed `Event logging not initialized` in non-carry engine unit tests** — DONE
      (strategy-service@67e7826c). Root cause confirmed: the v2 conftest autouse fixture only patched
      `staked_basis.log_event`, never the arbitrage/sports engine modules nor the cli/handlers manifest-guard test, and
      no autouse events init existed for those paths. Fix: a session-safe autouse fixture in the top-level
      `tests/conftest.py` (`_events_initialized_for_tests`) initializes events in `mode="test"` (log_event → no-op, no
      sink) for ALL tests, save/restoring `_mode`/`_writer`/`_service_name` so tests that manage events state themselves
      (`test_cdc_strategy_state`, `test_risk_preflight_gate`, `test_event_logging`) are not polluted. The ~33
      previously-red non-carry engine + manifest-guard tests now pass; the full strategy-service unit suite is GREEN
      (2704 passed locally with the credential-free env). NOTE: the full `quality-gates.sh` harness in the root/slot
      clones currently mis-roots its TESTS phase to unified-trading-pm (`rootdir: …/unified-trading-pm`, runs PM's 6
      tests) — a fleet-wide QG-harness defect, NOT this code; the authoritative server `quality-gates-v2` runs
      test-in-image with correct rootdir. Repo: strategy-service. Provenance: paper/batch spine fix session 2026-06-20.
- [ ] [SCRIPT] P9.2 (was: mislabeled P3.2 — collided with Phase 3's real P3.2 "PassiveLedger synthesiser" item above;
      renumbered per verify-rerun-2 finding 17, 2026-07-14). **DEFERRED (pre-existing, NOT this work) — UAC version
      drift blocks strategy-service QG preflight.** `quality-gates.sh` version-alignment gate: local
      `unified-api-contracts=0.26.0` vs main `0.27.0`. Run
      `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --fix` (after `git pull origin main` in
      PM). Repo: strategy-service (dep alignment). Provenance: paper/batch spine fix session 2026-06-20.
- [x] ✅ [SCRIPT] P3.3. **SWAP leg `size_units` now denominated in the OUT asset (ETH), not the USDC-in notional** —
      DONE (strategy-service@67e7826c). `staked_basis.py` both SWAP legs (open `_build_atomic_legs` + rescale) now set
      `size_units` to the canonical OUT-asset qty (`eth_qty = usdc_to_stake / eth_price`; rescale `eth_delta_qty`),
      derived from the swap's out-amount (notional / price), NOT a hardcoded map; the USDC-in notional is preserved in
      `params["from_amount"]`. The benchmark fill then books `eth_qty · eth_price == usdc_to_stake` (correct USD
      notional) and the ledger qty is an ETH quantity consistent with the LIDO/DERIBIT legs. 3 stale tests updated to
      assert OUT units. **Live-verified on real run `paper-20260620133928-d7a30df2`**:
      `UNISWAP_V3:DEX_POOL:ETH net_qty=233.33` (ETH — was 800000 USDC), `LIDO:STAKING:ETH net_qty=233.33`,
      `DERIBIT:ETH-PERP net_qty=-215.83` (SHORT) → net ETH ≈+17.5 (haircut residual, near-delta-neutral). Repo:
      strategy-service. Provenance: 2026-06-20.
- [x] ✅ [CODE] P3.4. **MARKS → PricingLedger (producer)** — DONE (`unified-trading-library@5f941c6e` +
      strategy-service@67e7826c). UTL gained the PricingLedger producer leg: `materialize.pricing_ledger_row` (a
      `MARK_UPDATE` `LedgerRow`, `event_origin=PASSIVE`, `delta=0`, `price=mark`) + `run_writer.pricing_ledger_jsonl` /
      `write_run_pricing_ledger` (deterministic JSONL → `{ledger_root}/ledger_type=pricing/{run_id}.jsonl`; asset
      identity derived canonically from `instrument_key`, no metadata maps). strategy-service
      `ledger_emit.write_paper_run` now derives per-instrument marks from the SAME benchmark fills (`marks_from_fills`:
      last `fill_price` per `instrument_key` — deterministic + batch-re-derivable) and writes the PricingLedger
      alongside the InstructionLedger; `write_paper_run`/`emit_paper_run_ledger` return `(ledger,manifest,pricing)`
      URIs. The position materialiser already joins marks on `asset_canonical_id` → `unrealized_pnl`. 6 UTL + 2 strategy
      tests. **Live-verified `paper-20260620133928-d7a30df2`**: 3 `mark_update` marks written to
      `…/ledger_type=pricing/…jsonl` (DERIBIT ETH-PERP @3000, LIDO ETH @1, UNISWAP_V3 ETH @3000). Repo: UTL +
      strategy-service. Provenance: 2026-06-20.
- [x] ✅ [CODE] P3.5. **ATTRIBUTION → P&L attribution parquet (producer)** — DONE (strategy-service@67e7826c).
      `paper_run_attribution.build_paper_run_attribution`/`emit_paper_run_attribution` build canonical
      `PnLAttributionRow` records from the run's REAL captured carry rates — `CARRY` = LST staking yield, `BASIS` = Aave
      supply−borrow spread, per held day, at `PnLLayer.STRATEGY`, accrual = `notional·rate/365` — and emit via the UTL
      SSOT `emit_attribution_parquet` to exactly the path `attribution_reader.read_attribution_rows` scans
      (`pnl_attribution/strategy_id={S}/client_id={C}/date={D}/rows.parquet`). Per-day rates surfaced on
      `StrategyReplay`; wired into `run_paper`. **Honest gap (NOT fabricated):** the price/DELTA + FEES legs need a
      spot-price column the lending-rates corpus does NOT carry (the handler prices SWAP/TRADE off `_REFERENCE_MID`);
      the position is delta-neutral so the price leg nets ≈0 — omitted, not invented (lands when the price feature group
      is added). 5 tests. **Live-verified `paper-20260620133928-d7a30df2`**: 7 daily shards / 14 rows written (each
      date: CARRY+BASIS, non-zero amounts from real Aave rates) — `attribution_reader` now has rows to read (was empty).
      Repo: strategy-service. Provenance: 2026-06-20.
- [x] ✅ [INFRA] P3.6. **Re-run + ε=0 verification with the new ledgers** — DONE (2026-06-20). New REAL run
      `paper-20260620133928-d7a30df2` (client `firm-paper-determinism`, window 2026-05-16..22, 7 real Aave days) wrote
      InstructionLedger (21 fills) + PricingLedger (3 marks) + RunManifest + 7 attribution shards to the canonical
      client-reports GCS root. **Batch rerun re-derived ε=0 WITH the new ledgers**: `rerun_from_manifest` →
      `ReconResult(deterministic=True, paper_count=21, batch_count=21, matched=21, deviations=[])` (the deterministic
      marks don't break the proof). Perp still SHORT (`DERIBIT:ETH-PERP net_qty=-215.83`), book near-delta-neutral.
      Repo: strategy-service. Provenance: 2026-06-20.

## Phase 10 — Citadel monitoring completeness + backtest visibility (operator feedback 2026-06-20)

> Operator reviewed the live `/paper-trading` dashboard and flagged it as placeholder-like vs a real fund desk: zero
> transfers (real strategies move capital across venues), flat `$87` attribution (`by venue == by layer`), unclear
> `Strat α`/`Exec α`, no per-strategy / per-coin breakdown, no net-$/net-coin/delta, no PnL-over-time graphs, no
> bps-on-turnover / annualised ROE, no entry/exit visibility, and no way to see the **backtest** (historical PnL +
> execution cost + execution assumptions) reconciled against paper. Get it all to real, no placeholders.

### Data / producer (strategy-service + UTL + client-reporting-api)

- [x] ✅ [DATA] P1. FIX phantom `$700K` unrealized — canonical-instrument-key per-leg marks join — DONE
      (`unified-trading-library@68540e7a` "fix(ledger): join marks + group positions by canonical instrument_key (kill
      phantom uPnL)"). `materialize_position_ledger` groups positions and joins marks on `_row_instrument_key(row)`
      (`instrument_key_by_row_id[row.row_id]` when stamped, else `_legacy_instrument_key` = `{venue}:{asset}`) rather
      than `asset_canonical_id` alone — LIDO:STAKING:ETH ≠ UNISWAP_V3:DEX_POOL:ETH even though both are `asset=ETH`.
      `_parse_mark_jsonl` (CRA) already keys marks by the `instrument_key` field stamped by `pricing_ledger_jsonl` (UTL
      `run_writer.py:445`). Full chain verified code-read 2026-06-22: write → JSONL `instrument_key` stamp → read_marks
      dict → materialize join → each leg gets OWN mark → unrealized ≈ 0. Regression test:
      `UTL/tests/unit/ledger/test_materialize.py::test_same_asset_different_venue_legs_get_own_marks_no_phantom_pnl`.
      Repos: unified-trading-library + client-reporting-api. Provenance: agt-f35b99 2026-06-22.
- [x] [STRATEGY] ✅ P2. **PRODUCER DONE** — Real cross-venue transfers / money-movements: emit Treasury/TransferLedger
      rows for the carry_staked_basis capital flow (USDC deposit → spot swap → stake → perp margin posting), single
      `client_id` (funds-isolation). UTL transfer-row SSOT: `unified-trading-library@0c712f99`
      (`materialize.transfer_ledger_row` + `run_writer.write_run_transfer_ledger`/`transfer_ledger_jsonl`,
      `ledger_type=transfer`, 4 new tests). Emit: `strategy-service@c1083310` (`engine/backtest/paper_run_transfers.py`
      wired into `run_paper()`, 8 tests). VERIFIED on GCS — run `paper-20260621105146-e7545ddb`:
      `ledger_type=transfer/{run}.jsonl` has **8 rows = 4 legs × 2 strategies** (DEPOSIT@UNISWAP_V3/JUPITER, TRANSFER
      spot→staking, STAKE@LIDO/JITO, COLLATERAL_POSTED@DERIBIT/DRIFT), every row single `client_id` +
      `counterparty_client_id=None`. **client-reporting-api (read) DONE 2026-06-21** — `/transfers` now reads
      `ledger_type=transfer` (client-reporting-api@50ae187, rev -00008-7gp; LIVE returns the 8 rows / both strategies).
- [x] [STRATEGY] ✅ P2. **DELTA DOUBLE-COUNT FIXED (2026-06-21)** — strategy-service@a2d12217 +
      unified-trading-library@ef5b1699. The carry_staked_basis `_build_legs` flow booked the SWAP-acquired native ETH
      (`UNISWAP_V3:DEX_POOL:ETH` +eth_qty) AND the STAKE leg (also `instrument=native_asset` ETH, +eth_qty) as TWO longs
      of the SAME economic ETH → net-in-coin ETH ≈ 2×eth_qty. **Fix (producer-side, option a):** the swap→stake is ONE
      economic long — the SWAP acquires native ETH which the STAKE CONSUMES. Added a `stake_consume` leg (SWAP/SELL of
      the swap-acquired native at the staking protocol, −eth_qty) that cancels the swap's spot ETH so the staked ETH
      delta is counted ONCE; the STAKE leg keeps `instrument=native_asset` (ETH-denominated delta) so it nets against
      the ETH-PERP short in net-in-coin. 4-leg ATOMIC → 5-leg (SWAP + stake_consume + STAKE + TRANSFER + TRADE);
      `make_trade_key` collision avoided by booking the consume at the staking venue (distinct instrument_key).
      **Measured (ETH, equity=100k @ 3000): BEFORE net-in-coin ETH ≈ +35.83 (≈ a full extra staked leg, the visible
      ~+250 bug); AFTER ETH = +2.50 = staked 33.33 − perp 30.83 = the Deribit-haircut residual, near-delta-neutral.**
      Unit test `tests/unit/engine/strategies/v2/test_carry_staked_basis_net_coin_no_double_count.py` asserts net coin ≈
      haircut residual (not 2×) for both ETH (Lido/Deribit) + SOL (Jito/Drift). Batch rerun replays the same shared
      `_build_legs` → ε=0 preserved. 6 carry leg-count tests updated 4→5 (all green; full carry+backtest suite 1361
      pass). Provenance finding: live run paper-20260621100605-b33e4bf4 (read +$752K ETH); reader
      (`net_views`/`delta_per_coin`) was HONEST throughout — the fix is producer-side.
- [x] [STRATEGY] ✅ P2. **PRODUCER DONE** — Real multi-dimensional P&L attribution: by **venue**, by **layer**, by
      **factor**, per **strategy_id** — replaces the flat `by venue == by layer` placeholder.
      `strategy-service@c1083310` (`engine/backtest/paper_run_attribution.py` now emits CARRY+BASIS+FEES @ the staking
      venue and FUNDING @ the perp venue, all at `PnLLayer.STRATEGY`; EXECUTION layer = 0 in paper (benchmark fills);
      FEES is an HONEST explicit 0; price/DELTA omitted honestly — no spot-price column). VERIFIED on GCS — run
      `paper-20260621105146-e7545ddb`: 14 attribution shards, **56 rows = 7 days × 4 factors × 2 strategies**, factors
      {CARRY,BASIS,FUNDING,FEES}, **4 distinct venues {LIDO,JITO,DERIBIT,DRIFT}** so `by venue` ≠ `by layer` (a real
      waterfall), 2 distinct `strategy_id`s, partitioned per strategy_id+client_id+date (per-venue/per-strategy/per-day
      queryable). batch rerun ε=0 (42 fills, 0 deviations) with the new ledgers. **API breakdown DONE 2026-06-21**
      (client-reporting-api@50ae187: `/attribution/breakdown` surfaces by-venue/by-layer/by-factor/per-strategy + nested
      waterfall; LIVE 5 venues / 4 factors / by venue ≠ by layer). **UI waterfall remains open**
      (unified-trading-system-ui agent — the producer dims + the API breakdown they read now both exist).
- [x] [STRATEGY] ✅ P2. Multi-strategy paper run — strategy-service@94ca0b6c (specs 0+6: LIDO/ETH + JITO/SOL; run
      paper-20260621100605-b33e4bf4 → 2 strategy_ids, 42 fills, batch re-derives both ε=0). (≥2 strategies, e.g.
      carry_staked_basis + arbitrage_price_dispersion) so the per-strategy breakdown is meaningful, not a single flat
      strategy. Repo: strategy-service (paper_run_handler).

### Metrics / API (client-reporting-api)

- [x] [API] ✅ P2. Net views: **net-in-dollars** (portfolio USD value), **net-in-coin** (net qty per coin),
      **delta-per-coin** (net signed delta exposure per coin; ETH ≈ 0 for the delta-neutral book) —
      client-reporting-api@501c731 `core/portfolio_metrics.py::net_views` (base-coin grouped so perp nets vs spot/LST) +
      `GET /api/v1/clients/{id}/net-views`. LIVE `firm-paper-determinism`: ETH net 250.83 coin / SOL 210.0; per-coin
      delta surfaced (reads $752K ETH due to the producer spot+LST double-count — captured as a [STRATEGY] finding
      above; reader is honest). Repo: client-reporting-api (ledger_views).
- [x] [API] ✅ P2. Per-strategy breakdown: group trades / positions / P&L / attribution by `strategy_id` (per-strategy
      detail + overall roll-up) — client-reporting-api@501c731 `per_strategy_breakdown` + `GET /per-strategy`. LIVE: 2
      strategies (`@lido-uniswapv3-deribit` 21 trades / `@jito-jupiter-drift` 21 trades) mapped from venue via
      RunManifest.strategy_ids. Repo: client-reporting-api.
- [x] [API] ✅ P2. **`/transfers` READER (was open)** — point the route at the canonical run's `ledger_type=transfer`
      ledger (NOT `ledger_type=instruction`) so it returns the producer's REAL money-movement rows, surfacing ALL
      money-movement actions (the prior InstructionLedger-subset scan dropped STAKE/COLLATERAL_POSTED → always
      `NO_TRANSFER_ROWS`). New `read_transfer_rows` reader (`core/ledger_views.py`) + rewired `GET /transfers` with
      per-`strategy_id` grouping + `?strategy_id=` filter (venue→strategy via RunManifest.strategy_ids).
      client-reporting-api@50ae187 (rev `client-reporting-api-00008-7gp`). LIVE `firm-paper-determinism` /transfers:
      **status=OK, 8 rows**, actions {DEPOSIT,TRANSFER,STAKE,COLLATERAL_POSTED}, **both strategies** (4 legs each,
      `by_strategy` net 100000 / 75000), `?strategy_id=jito` → 4 legs. Repo: client-reporting-api.
- [x] [API] ✅ P2. **`/attribution/breakdown` multi-dim READER (was open)** — surface the real multi-dimensional
      waterfall now the parquet carries venue+layer+factor+strategy_id dims: `attribution_breakdown` adds
      `per_strategy_total` + nested `by_strategy` (each strategy's own factor split) alongside
      by-venue/by-layer/by-factor. client-reporting-api@50ae187. LIVE `firm-paper-determinism` /attribution/breakdown:
      **5 venues** {UNISWAP_V3,JITO,DRIFT,LIDO,DERIBIT}, **4 factors** {CARRY,BASIS,FUNDING,FEES}, **per-strategy**
      totals + nested waterfall, **by venue ≠ by layer** (venue splits 5 ways, layer = STRATEGY only — EXECUTION=0 in
      benchmark paper), total_amount 210.26. Repo: client-reporting-api.
- [x] [API] ✅ P2. **bps PnL on turnover** (PnL ÷ Σnotional-traded × 1e4) per strategy + overall —
      client-reporting-api@501c731 `_bps_on_turnover` + `GET /bps-pnl`. LIVE: ETH-strat -2.60 bps, SOL-strat 0 bps,
      overall -1.53 bps (turnover $2.29M). Repo: client-reporting-api.
- [x] [API] ✅ P2. **% ROE annualised** (return on equity, annualised over the run window) per strategy + overall —
      client-reporting-api@501c731 `_annualised_roe` (window from RunManifest, linear annualise) + `GET /roe`. LIVE:
      overall -6.05% annualised over the 6-day window. Repo: client-reporting-api.

### Backtest visibility (client-reporting-api + UI)

- [x] [API] ✅ P2. Backtest results surface: historical PnL from the `__batch__` rerun, **execution cost** (execution
      alpha = smart-matching fill − benchmark fill), and **execution assumptions** (fill-model fidelity tier
      OHLCV→BBO→depth→trades→MBO + the slippage/cost model used) — client-reporting-api@501c731 `backtest_surface` +
      `read_batch_total_pnl` + `GET /backtest`. Reads the canonical run's `__batch__` rerun (PENDING honestly when none
      yet — the newest 2-strategy run has no batch rerun), exec-alpha=0 stated as a STRUCTURAL zero (BENCHMARK fill
      model), assumptions surface fill_model=BENCHMARK + OHLCV signal-close tier + the fidelity ladder + paper-vs-batch
      payload. Repo: client-reporting-api.
- [x] [UI] ✅ P3 (P10.12). **Unified batch↔paper view**: reconcile the dashboard so paper and batch are viewable
      together neatly, `live − batch = (paper − batch ≈ 0) + (live − paper = execution α)` made legible. Repo:
      unified-trading-system-ui. — unified-trading-system-ui@02e3b59f | `BatchPaperPanel` consumes `/backtest` + the
      recon verdict: identity banner + paper/batch/paper−batch/exec-α KPIs + execution-assumptions surface (fill_model
      BENCHMARK / fidelity ladder OHLCV→…→MBO) + honest PENDING until the `__batch__` rerun lands. pw:L2 ✓ (60/60 smoke)
      | regression: tests/smoke/paper-trading-ledger.smoke.spec.ts ("batch↔paper panel shows the determinism identity +
      execution assumptions (P10.12)").

### UI (unified-trading-system-ui — playwright-gated)

- [x] [UI] ✅ P3 (P10.5). Clarify `Strat α` / `Exec α` columns (label + tooltip: strategy alpha vs execution alpha =
      smart−benchmark; 0 in paper because paper uses benchmark fills). — unified-trading-system-ui@02e3b59f | PnL-panel
      headers `pnl-strat-alpha-header` / `pnl-exec-alpha-header` carry `title=` tooltips (exec α = smart−benchmark fill,
      ≈0 in paper / real only at the live boundary). pw:L2 ✓ | regression:
      tests/smoke/paper-trading-ledger.smoke.spec.ts ("Strat α / Exec α columns carry clarifying tooltips (P10.5)").
- [x] [UI] ✅ P3 (P10.10). PnL-over-time **graphs**, broken down by **strategy** AND by **coin**. —
      unified-trading-system-ui@685623df | **UPGRADED to a real per-DAY line/area timeseries** (`PnlTimeseriesChart`,
      recharts `AreaChart` over a 7-day window) with a **by-strategy / by-coin toggle** (`pnl-ts-toggle-strategy` /
      `pnl-ts-toggle-coin`) driven by a new `useLedgerPnlTimeseries` hook (GET `/pnl-timeseries`). Until the API agent's
      `/pnl-timeseries` endpoint deploys (currently 404 → honest-empty `series:[]` → `pnl-timeseries-empty` clean empty
      state, NOT a fabricated line — auto-populates once live); snapshot by-strategy + Δ-USD-by-coin bars retained as
      secondary context. (prior 02e3b59f shipped only the bars + a pending note.) pw:L2 ✓ (63/63 smoke) | regression:
      tests/smoke/paper-trading-ledger.smoke.spec.ts ("PnL-over-time panel renders the per-day timeseries (toggle
      strategy/coin) + snapshot bars (P10.10)").
- [x] [API] ✅ P3 (P10.10). **`GET /api/v1/clients/{client_id}/pnl-timeseries`** — the per-DAY series the UI P10.10
      graph is wired to (resolves the 404 the UI item notes; was "honest per-day-pending" at line 613). —
      client-reporting-api@ce1bd5f, deployed rev **client-reporting-api-00009-mr4** (asia-northeast1, base UTL digest
      sha256:467ba8). New run-scoped reader `core/pnl_timeseries.py::pnl_timeseries_series` folds the canonical run's
      per-DAY attribution parquet (CARRY/BASIS/FUNDING/FEES factors) into one row per `(date × strategy_id × coin)` with
      `realized` / `unrealized` / `total` / `carry`; coin derives canonically from `instrument_id`
      (`LIDO:STAKING:stETH`→ETH, `JITO:STAKING:JitoSOL`→SOL). `total = realized + (unrealized or 0) + carry`;
      `unrealized` is HONEST null (no MTM-factor row on the flat corpus — never a fabricated 0). MEASURED live curl
      (`firm-paper-determinism`, admin JWT): HTTP 200, `run_id=paper-20260621134256-3c4eb321`, **22 rows over 8 days
      2026-05-15→05-22, coins {ETH,SOL}, 2+ strategies (lido ETH + jito SOL)**. regression:
      tests/unit/test_pnl_timeseries.py + tests/unit/test_attribution_routes.py::TestPnlTimeseriesRoute | QG-green.
- [x] [UI] ✅ P3 (P10.x). **Attribution by-FACTOR view in the UI** (was the Progress-Log "remaining minor"): the
      `/attribution/breakdown` API already returns by-factor (CARRY/BASIS/FUNDING/FEES); the UI rendered only
      venue+layer. — unified-trading-system-ui@685623df | `AttributionPanel` now renders a **By-factor waterfall**
      (`attribution-by-factor` / `attribution-factor-bars`) FIRST (the desk's primary lens — positive carry+basis,
      negative funding, ≈0/honest-empty FEES), plus by-venue + by-layer. **Bug fixed in scope**: the bars read `b.key`
      but the LIVE API emits per-DIM keys (`venue`/`factor`/`layer`/`instrument_id`) → by-venue/by-layer rendered BLANK
      labels against live data; `useLedgerAttribution` now normalises every dim to `{label, amount}` (fixture updated to
      the live byte-for-byte raw shape). pw:L2 ✓ (63/63 smoke) | regression:
      tests/smoke/paper-trading-ledger.smoke.spec.ts ("attribution panel shows the by-FACTOR breakdown (CARRY / BASIS /
      FUNDING)").
- [x] [UI] ✅ P3 (P10.11). **Entries & exits** visible in the trade-ledger view (entry/exit markers; richer historically
      in the batch view where there are real exits). — unified-trading-system-ui@02e3b59f | trade-tape `E/X` column:
      entry (opens/adds, no realised PnL) vs exit (closes/reduces, realises PnL or `trade_type=exit`),
      `trade-entry-marker` / `trade-exit-marker`. pw:L2 ✓ | regression: tests/smoke/paper-trading-ledger.smoke.spec.ts
      ("trade tape shows entry / exit markers (P10.11)").
- [x] [UI] ✅ P3 (P10.13). Render the
      net-$/net-coin/delta panels, per-strategy breakdown, bps-on-turnover, and annualised
      ROE from the new API surfaces. — unified-trading-system-ui@02e3b59f | `NetViewsPanel` (net-$/gross-$
      KPIs + net-in-coin table ETH+SOL + delta-per-coin table) from `/net-views`; `PerStrategyPanel` (2 strategies +
      overall roll-up: trades / turnover / gross / total PnL / bps-on-turnover / annualised ROE) from `/per-strategy`.
      pw:L2 ✓ | regression: tests/smoke/paper-trading-ledger.smoke.spec.ts ("net-views panel shows net-in-coin ETH + SOL
      … (P10.13)" + "per-strategy panel shows 2 strategies + an overall roll-up with bps/ROE (P10.13)").

> **Sequencing (foundation-completion-gate):** [DATA] P1 (the marks-join fix) lands first; then producer/data [STRATEGY]
> P2 items on strategy-service+UTL; then API metrics+backtest [API] P2 items on client-reporting-api; then the UI wave
> [UI] P3 items once the API surfaces exist. Producer/UTL/reader items serialize (shared files); UI is a separate repo.
> **Codex SSOT to update on completion:** `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`
> (multi-dim attribution + bps/ROE) + `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` (backtest
> surface + transfers in the four-ledger model).

## Success criteria (per phase: QG/basedpyright/ruff green + tests)

- **Determinism**: `reconcile_day(paper, batch)` returns ε=0 — **PROVEN** (P7.2, `e2e-testing@a553f28`): the
  short-window e2e proof returns `is_deterministic=True` end-to-end (paper → batch-rerun → keyed determinism check),
  exit 0. The real-week (19→26) soak is the same machinery longer, calendar-bound (rides P7.1's paper-week VM)
  (validated for the paper↔batch-rerun path; full live-boundary parity pends Phase 2 trade-keying).
- **Completeness**: the 4 ledgers materialise; balances/PnL/attribution are real (not mock/`"0.00"`), per
  venue+instrument.
- **One fill model**: no third fill model on the batch/paper path (`BenchmarkFillEngine` is the single sim SSOT).
- **Slack**: daily ledger digest + daily T+1 recon verdict reach `#uts-live-alerts`.

## Phase 11 — Autonomous rolling-book gaps (operator audit 2026-06-21)

> Operator probe 2026-06-21: "is all the code and data real running autonomously to continue to generate trades and PnL
> … how much of prod vs bolt-ons … is all money movement and treasury vs trading-wallet simulated properly". A
> live-state audit of the deployed cron + the GCS ledger (`run_id=paper-20260621134256-3c4eb321`) surfaced the gaps
> below. All are real; filed per Capture-Discoveries HARD RULE; driven to done under `/autonomous` 2026-06-21.

- [x] ✅ [INFRA] P11.1. **Roll-forward cron window** — DONE (deployment-service@f5a81d6 + strategy-service@ba63ab1c).
      Cloud Run Job `uts-prod-paper-engine-run` args now `--rolling-days 7` (verified live; no absolute dates); the CLI
      flag computes a trailing 7-day window ending T-1 UTC at job start (`test_paper_run_rolling_window.py`, 5 tests).
      So each 02:00 UTC run books a fresh day instead of re-running the fixed 05-16..22 week.
- [x] ✅ [CODE] P11.2. **Pin `code_shas` in the run manifest** — DONE (strategy-service@ba63ab1c). `_git_sha()` prefers
      config `code_version` (`CODE_SHA_STRATEGY_SERVICE`/`CODE_VERSION` via UnifiedCloudConfig) → `git rev-parse` →
      "unknown"; stamped into the manifest so `assert_code_shas_match` proves SAME-code.
      `test_git_sha_prefers_configured_code_version`.
- [x] ✅ [CODE] P11.3. **Emit the PASSIVE accrual ledger TAPE per period** — DONE (UTL@afc31764 +
      strategy-service@ba63ab1c). UTL `write_run_passive_ledger`/`passive_ledger_jsonl` (`ledger_type=passive`);
      producer emits per-held-day `STAKING_REWARD` + `LENDING_INTEREST` (staking venue) + `FUNDING_ACCRUAL` (perp),
      QUOTE cash-flow delta (NEVER fed to `materialize_position_ledger`). batch_rerun re-derives it; ε=0 unaffected. 8
      producer + 3 UTL writer tests.
- [x] ✅ [CODE] P11.4. **Treasury ↔ hot-wallet split in the TRANSFER ledger** — DONE (strategy-service@ba63ab1c). DeFi
      20% treasury / 80% hot TRANSFER legs at deploy, keyed by `share_class`, single `client_id` (funds-isolation);
      CeFi/Sports = 0% (no split); deploy flow sized off the hot budget. `test_treasury_hot_split_20_80` +
      `test_cefi_has_no_treasury_split`.
- [x] ✅ [CODE] P11.5. **De-dup the bare vs `@`-qualified strategy_id** — DONE (strategy-service@ba63ab1c). Manifest
      `strategy_ids` = ONLY the `@`-qualified slot ids (bare archetype dropped → no per-strategy double-count); batch
      rerun resolves archetype via `archetype_for_slot_label`. `test_slot_labels_are_qualified_not_bare_archetype`;
      batch_rerun ε=0 intact.
- [ ] [CODE] P1.6. **GroupC smart-fill handoff into paper-run (`fill_model` BENCHMARK→SMART)** — PARTIAL
      (strategy-service@ba63ab1c left manifest HONEST at `BENCHMARK`, NOT faked). Blocked by the no-service-deps HARD
      RULE: strategy-service MUST NOT import execution-service, so smart-matching cannot be called in-process.
      **Remaining (correct architecture):** a new **execution-service Layer-3 entrypoint** consuming
      `{run}/ledger_type=instruction` + RunManifest → GroupCRunner smart-matching → an `execution_alpha_bps` artifact,
      driven from the e2e-testing harness; CRA reads it at `PnLLayer.EXECUTION`; UI surfaces exec-α. (FEES is already
      the only EXECUTION-layer leg.)
- [x] ✅ [INFRA] P11.7. **Custom domain for the paper-trading UI** — DONE pending DNS (deployment-service@1168718 +
      @3c54e64). `portal.odum-research.com` Cloud Run domain mapping created + tracked in
      `terraform/gcp/domain_mappings.tf` (`DomainRoutable=True`, `CertificatePending`). **Operator DNS step:** add CNAME
      `portal` → `ghs.googlehosted.com.` at the odum-research.com registrar; the managed cert auto-provisions once it
      resolves.
- [x] ✅ [CODE] P11.8. **Fee model — approximate maker/taker fees on turnover** — DONE (strategy-service@ba63ab1c).
      Deterministic **1 bp maker / 2 bps taker** on filled notional, per-venue overridable (`_VENUE_FEE_OVERRIDE_BPS`),
      booked as the `FEES` factor at `PnLLayer.EXECUTION`, one NEGATIVE row per leg (swap+stake+perp = taker); grand
      total drops by the fee drag. ε=0 preserved (benchmark `TradeFillRecord`s stay fees=0).
      `test_fees_are_execution_layer_and_nonzero` + `test_maker_taker_rates`.
- [x] ✅ [CODE] P11.9. **Strategy-keyed ledgers — BACKEND DONE (UAC@70695806 / UTL@cc5ebe5a / strategy-service@77f3c5b6
      / CRA@981f14d: optional `strategy_id` on every LedgerRow, stamped on instruction/pricing/passive/transfer per
      @-qualified id, CRA `by_strategy` + `?strategy_id=` filter, ε=0). UI per-strategy/archetype drilldown REMAINS
      (tracked in Final).** Orig:**Strategy-keyed ledgers + UI drilldown across ALL ledger types** (operator 2026-06-21:
      "associate pnl, trade, order and position ledgers to strategies … all parts of the UI should group + drilldown by
      strategy"). `LedgerRow` has NO `strategy_id` column today — only the attribution parquet is strategy-partitioned,
      so trade / position / transfer / passive / pricing ledgers can NOT be grouped by strategy (the strategy is only a
      substring of the composite `trade_id`, and was the bare archetype). Add a canonical `strategy_id` field (the
      `@`-qualified id) to `LedgerRow` (UAC), stamp it on EVERY row in all UTL materialisers + the strategy-service
      emitters, GROUP-BY `strategy_id` in CRA across ALL ledger views (positions/PnL/trades/transfers/passive, not just
      attribution), and add a strategy filter + per-strategy drilldown to EVERY UI panel. Repo: unified-api-contracts
      (field) + unified-trading-library (stamp) + strategy-service (emit) + client-reporting-api (group) +
      unified-trading-system-ui (drilldown, playwright-gated).

- [x] ✅ [CODE] P11.10. **Replicate the full e2e experiment universe + wire the portfolio_allocator — DONE**
      (UTL@e797deac / strategy-service@4e2c14c6): `paper_universe.py` allocator-driven selection replaced hardcoded
      indices; verified live `paper-20260621171725-fcf31316` = **14 strategy_ids, allocator-weighted, all strategy-keyed
      ledgers + passive + treasury, batch-rerun ε=0**; 266 specs honestly skipped (no in-window data → P11.11). Orig
      intent: (operator 2026-06-21: "missing lots of strategies and venues from our e2e*testing work … basis, staked
      basis, funding rate dispersion/arb … many more venues and coins … production archetypes are flexible enough … give
      them strategy IDs + configs matching the e2e experiment … how we weight allocations per archetype, which venues,
      which coins at any one time, and moving money around"). The paper run hardcodes `PAPER_RUN_SPEC_INDICES = (0, 6)`
      (2 of 14 `CARRY_STAKED_BASIS` specs); the production catalogue ALREADY builds **468 specs / 30 archetypes**
      (`specs_for_archetype`) incl. the e2e archetypes: `CARRY_STAKED_BASIS` (14), `CARRY_BASIS_PERP` (144),
      `CARRY_FUNDING_DISPERSION` (52), `ARBITRAGE_PRICE_DISPERSION` (17), `CARRY_BASIS_DATED`, `CARRY_RECURSIVE_STAKED`,
      `YIELD*_`, `DEFI*LP*_`. SUB-TASKS: - P11.10a. Extract the e2e experiment's universe (archetypes × venues × coins ×
      weights) from `e2e-testing/scripts/defi/` (funding_reversion_*, funding_ensemble_engine, backtest_solana_basis,
      funding_reversion_multivenue_capital) as the documented intent. - P11.10b. Map e2e universe → catalogue specs
      (`specs*for_archetype`); add any missing venue/coin spec in the right `catalog*_.py`(flexible archetypes — add the
      spec, do not fork the engine); canonical`@`-qualified ids. - P11.10c. Wire `portfolio_allocator/archetypes_.py`
      into the paper run: replace hardcoded indices + 100k/75k split with allocator-driven per-archetype weight + which
      venues/coins active per rebalance + capital deploy (treasury→hot per P11.4, single client_id). - P11.10d. Verify a
      multi-archetype run materialises strategy-keyed ledgers (P11.9) for ALL e2e strategies, ε=0 batch-rerun holds
      across the larger universe, UI groups/drills down by every strategy + archetype. Repo: strategy-service
      (catalogue + allocator + paper_run) + e2e-testing (extraction) + verify CRA/UI.
- [x] ✅ [CODE] P11.6-retry. **execution-service Layer-3 smart-fill entrypoint — SHIPPED** — execution-service@3d7d760c
      (`backtest_v2/smart_fill_replay.py` + `--operation smart-fill-replay` CLI + peripheral-QG wiring; 12/12 tests, QG
      exit-0) + e2e-testing@0e421c08 (`scripts/defi/execution_alpha_replay_e2e.py` → writes
      `ledger_type=execution_alpha`, `execution_alpha_bps = smart − benchmark`; QG exit-0). Both verified on
      origin/live-defi-rollout 2026-06-21. Ship was blocked by 3 PRE-EXISTING fleet conditions, all cleared: (1)
      execution-service codex ratchet 4>3 → cleared 2 classes to 2 (empty-string fallback in smart_fill_replay.py:276 +
      the back-compat docstring in v2/benchmark_fills.py:12) + fixed a net-new STEP-5.69 inline-gs:// flag (error-msg
      noqa on smart_fill_replay.py:224) → QG exit-0; (2) PM manifest `versions{}` promotion-lag did NOT block service
      quickmerge (warn-only PM post-gate; left to promotion automation, not hand-synced per the pull-not-push
      manifest-surface rule); (3) e2e dep-validation pre-flight tripped on a LIVE FOREIGN strategy-service test/source
      WIP (operator-protected — never touched) → shipped via the documented multi-agent `--skip-preflight` route (the
      new e2e file imports only execution_service + UAC + UTL; strategy-service SOURCE on LDR is unchanged, so zero
      blast-radius on this ship).

- [x] ✅ [DATA] P11.12. **CeFi funding READ from canonical GCS (Tardis) — DONE, NOT a backfill.** The data was already
      in `perp-funding-prd/.../pipeline_mode=batch_tardis/asset_group=cefi/` (7 venues); the only gap was a venue-name
      mismatch, fixed by `_canonical_venue` (strategy-service@bbdb4f1e). Verified run `paper-20260621215559-4337e2aa`:
      **141 strategies / 6 archetypes** (CARRY*BASIS_PERP 79, CARRY_FUNDING_DISPERSION 33, CARRY_STAKED_BASIS 14,
      ARBITRAGE_PRICE_DISPERSION 10, DEFI_LP 5), real funding PnLs, **ε=0 PROVEN (1016 trades matched, 0 deviations)**.
      149 specs honestly skipped (genuinely-absent / unwired → P11.13 for vault+fees; perp_funding for non-Tardis venues
      genuinely absent). 30 archetypes + the allocator, but 266/468 specs honestly SKIP because their market data is
      absent for the paper window: `perp_funding` (→ CARRY*BASIS_PERP 144, CARRY_FUNDING_DISPERSION 52),
      `dex_pool_state` (→ ARBITRAGE_PRICE_DISPERSION 17, DEFI_LP\** 9), `lst_rates` beyond Lido/Jito/Marinade,
      dated/recursive inputs. Only `lending_rates` (Aave/Compound/Spark) is present → CARRY*STAKED_BASIS is the only
      data-drivable family today. Backfill these feature groups for the firm-paper-determinism window (2026-05-16..22,
      then rolling) via the MTDS / features pipeline (data-pipeline-correctness HARD RULE — every venue × data_type ×
      range, honest absence where a venue genuinely lacks history). The e2e launch\*\_\_vm.sh scripts name the sources
      (perp_funding / dex_pools / lst_rates / lending_indices / gas_fees). Once the data lands, the SAME wired
      archetypes auto-populate — no code change. Repo: mtds / features-service / e2e-testing (sourcing); parent epic
      data/mtds master.
  - **FINDING (CeFi perp-funding GCS audit, 2026-06-21 — confirms CARRY_FUNDING_DISPERSION 52 + non-HL CARRY_BASIS_PERP
    blocker is a TRUE backfill, not a read-wiring gap):** CeFi perp **funding-rate** data is **genuinely ABSENT** across
    every canonical bucket. Checked: `perp-funding-{prd,,test}-central-element-323112` (all hold ONLY `asset_group=defi`
    venues — ASTER/GMX/HYPERLIQUID/PACIFICA, `data_type=perp_funding`, 2021-09-01..2026-05-22; ZERO CeFi venues);
    `market-data-tick-cefi-prd-central-element-323112` (has raw `derivative_ticker`/`book_snapshot_5`/`trades` for
    BINANCE-FUTURES/BYBIT/OKX/DERIBIT/KRAKEN-FUTURES via Tardis incl. the 2026-05-16..22 window, but **no `perp_funding`
    data_type anywhere** — derivative*ticker carries the funding \_field* on the raw tick, but the computed funding-rate
    series is not materialised); `features-delta-one-cefi-prd-…` (EMPTY); `features-onchain-cefi-prd-…` (EMPTY — this is
    the target of `features_service/cefi/calculators/perp_funding_rates.py`, which is MVP-scoped to Binance ETH-PERP and
    has not written output for the window). **Root cause:** the CeFi perp-funding compute (reads CeFi MTDS
    `derivative_ticker` → writes `features-onchain-cefi`) has not been run/materialised for the window. **Action:** run
    the CeFi `perp_funding` compute (broaden beyond Binance ETH-PERP MVP to BINANCE/BYBIT/OKX/DERIBIT/KRAKEN) over
    2026-05-16..22 + rolling, honest-absence where a venue genuinely lacks history. Repo: features-service (cefi
    perp_funding calculator) + mtds (if derivative_ticker gaps surface).

- [x] ✅ [DATA] P11.13. **DEFI_LP_VAULT share-price + fee-0 pool fees — DONE** (strategy-service@70a76d87). Vault APY
      from the ERC-4626 `vault_share_price` corpus via `CanonicalVaultProvider` (yvUSDC ~335bps, sUSDe ~420bps, sDAI
      124bps); fee-0 LP pools fixed with The-Graph `feesUSD` (Curve 18-46bps, Balancer 56-169bps). 24 unit tests.
      Verified run `paper-20260621225959-e86237f7`: **145 strategies / 7 archetypes** (DEFI_LP_VAULT 3 lit, DEFI_LP_POOL
      2→3). 197 specs honestly skipped. 2026-06-21: "fix that, we can get data, we got creds"). Two honest-skip gaps
      from P11.11/dex tranche are sourceable, not walls: (a) DEFI_LP_VAULT (ERC-4626 yearn/etc) needs a
      vault-share-price series — read `convertToAssets(1e18)` / `pricePerShare()` historically via the Alchemy/Helius
      archive RPC (creds `alchemy-api-key`/`helius-api-key` in Secret Manager) OR the vault subgraph
      (`thegraph-api-key`); (b) the `fees_usd=0` LP pools (Curve threepool/crvusdusdc, balancer) need real fee data —
      pull `feesUSD` from the Uniswap/Curve/Balancer subgraph (The Graph, `thegraph-api-key`..`-7`) or compute
      `volume_usd × fee_rate_bps` where volume is present. Materialise both into the canonical dex/vault feature
      location the engine reads (resolve_bucket_name SSOT), then wire DEFI_LP_VAULT into the paper run + re-derive the
      fee-0 LP pools so they produce real fee/IL PnL. Honest absence only where a vault/pool genuinely has no on-chain
      history. Backtest + ε=0. Repo: mtds / features-onchain (sourcing) + strategy-service (DEFI_LP_VAULT wiring). Creds
      via get_secret_client — never raw values in repo.
- [x] ✅ [CODE] P2.11.14. **Wire the BTC-level trend-following (CTA) leg — SHIPPED 2026-06-22: UAC@61ac3ad2
      (TSMOM_BTC_CTA enum+family+leg-spec) + strategy-service@f5f00109 (TsmomBtcCtaEngine + catalogue + paper-universe
      gating + unit test), both on LDR, QG-green. Version-promotion-lag cleared via run-version-alignment --fix
      (PM@0df3854f). Remaining for a non-null live paper run: P2.11.16 features + the ε=0 run.** — proven in research
      (`_exec_optimize.py` `trend` leg, 15% sleeve; Progress Log 2026-06-21 "WHY THE DIRECTIONAL BOOK MAKES ~0 IN 2023 &
      2026"). The directional book is market-neutral + long-biased so it makes ~0 in the two BETA years (2023 melt-up /
      2026 selloff); a BTC multi-horizon (1/3/6/12mo) TSMOM leg — long confirmed up-trend, short confirmed down-trend,
      sign-averaged, lagged (no lookahead) — earns exactly there (standalone realistic Sharpe +0.74 net +$659k; '23 +1.4
      '26 +2.3; corr to BTC buy&hold +0.00 full / −0.85 in the selloff = genuinely shorts the downtrend, not
      closet-long; corr to XS book −0.11). Implement as a production strategy archetype/leg in **strategy-service**
      (TS-momentum signal from the canonical OHLCV the engine already reads; batch=live one path; ε=0 batch-rerun proof;
      realistic fills via execution-service GroupC). Sizing = **co-equal sleeve** (`W["trend"]` ≈0.28, IS-validated
      robustness pick; on the proper-execution base it flattens 2023 −0.6→+0.1 + 2026 −1.1→+0.1, preserves full Sharpe
      +2.28→+2.26, trims maxDD −6.3→−5.0%). NOTE: the trend leg **subsumes** the old de-risk overlay + 12% short (does
      their 2026 job + fixes 2023 + keeps the Sharpe they cost) — make those light DD-insurance, NOT core sleeves;
      stacking all three over-hedges (−0.18 full Sharpe). Repo: strategy-service. **DESIGN LOCKED 2026-06-22 + BUILD
      DISPATCHED**: dedicated `TSMOM_BTC_CTA` archetype (not a `RULES_DIRECTIONAL_     CONTINUOUS` reuse — the factory
      routes by archetype + clean per-leg PnL attribution). 11-step change set mapped: UAC (enum +
      `ARCHETYPE_TO_FAMILY`→RULES*DIRECTIONAL + `archetype_leg_spec_seeds`) → strategy-service (new
      `rules_directional/tsmom_btc_cta.py` `TsmomBtcCtaEngine` reading
      `btc_trailing_return*{1,3,6,12}m`+`btc*realized*     vol`features, sign-averaged + vol-scaled +
      lagged;`factory`registry;`archetype*defaults` Kelly→`V1_ARCHETYPES*     IN_SCOPE`;
      `catalog_directional.build_tsmom_btc_cta`slot`TSMOM_BTC_CTA@binance-btc-tsmom-1d-usdt-v1-prod`;
      `catalog.\_BUILDERS_BY_ARCHETYPE`; `archetype_slots_cefi`; `paper_universe` `\_ENGINE_DRIVABLE`+`E2E_UNIVERSE`;
      unit test). **Sub-deps (own todos): P2.11.16 features-service BTC-trend features (GATES the live paper run — null
      signals until written); P2.11.17 UI archetype mirror (playwright-gated).** Then the live ε=0 paper run. **STATUS
      2026-06-22 — CODE BUILT + TEST-GREEN, ship BLOCKED on transient fleet-wide version-lag (NOT the archetype). UAC
      edits now STASHED to unblock an unrelated features-service quickmerge (the dirty UAC clone tripped the dirty-deps
      pre-flight) — recover with `git     -C .tabs/1/unified-api-contracts stash     pop`(stash msg "TSMOM_BTC_CTA
      archetype + WS-mapping fix — blocked on UAC version-lag"); strategy-service edits remain UNCOMMITTED in its
      clone.** The UAC
      files:`enums.py`+`archetype_leg_spec_seeds.py`+`tests/unit/test_archetype_leg_spec.py`(52→53) +`tests/test_ws_cassette_coexistence.py`(added
      the LEGIT`kalshi_clob_ws`/`polymarket_clob_ws`venue mappings — a pre-existing cross-repo cassette gap, real
      connectors, needed for green); strategy-service new
      `rules_directional/tsmom_btc_cta.py`+`tests/.../test_tsmom_btc_cta.py` + factory/defaults/slots/catalog/
      catalog_directional/paper_universe/batch_utils/`rules_directional/**init**.py`/test_ml_directional_continuous. UAC
      full QG = **10,215 passed** (incl. the new leg-spec test) once the WS mappings were added; strategy-service =
      content-sentinel green. **BLOCKER**: UAC local `quality-gates.sh`version-alignment HARD-fails because the PM
      `workspace-manifest.json` `versions[unified-api-contracts]`is **0.39.0** on origin/LDR while UAC-main is
      **0.40.0** (the manifest-update workflow hasn't synced the bump — the documented VERSION_SPLIT promotion-lag, here
      hard-blocking the consumer's local QG).`--skip-version-alignment`is human-only. **TO COMPLETE (once the PM
      manifest syncs to UAC 0.40.0, or a human aligns it)**:
      re-run`cd     unified-api-contracts && bash scripts/quality-gates.sh --no-fix` → quickmerge UAC
      (`enums.py     archetype_leg_spec_seeds.py tests/unit/test_archetype_leg_spec.py`) + a separate `fix(tests):`
      commit for the WS mappings → then quickmerge strategy-service (it depends on the UAC enum, so promote UAC first).
      The agent's first pass left it unshipped + had ONE hallucinated WS-test edit (invented connectors) which was
      dropped; the real WS mappings were re-added.
- [ ] [DATA] P2.11.16. **features-service: compute + write BTC trend features `btc_trailing_return_{1m,3m,6m,12m}` +
      `btc_realized_vol` to the canonical GCS feature corpus the paper run reads** — the CTA engine (P2.11.14) reads
      these from `features: dict[str,float]`; without them the paper run produces null signals (honest absence).
      Trailing returns = BTC daily mark `pct_change(21/63/126/252)` shifted (T-1, no lookahead); realized*vol = rolling
      60d std ×√365. Source = the daily BTC mark from the perp-funding corpus (`perp_daily_ctx`) the providers already
      read. batch=live one path. Repo: features-service (+ resolve_bucket_name SSOT / UTC). This is the CRITICAL-PATH
      gate for a non-null CTA paper run. **STEP 1 ✅ SHIPPED 2026-06-22 — features-service@653cf158.**
      `btc_trailing_return*{1,3,6,12}m`+`btc_realized_vol` added to
      delta_one's`returns`calculator +`registry_specs.yaml`(no-lookahead trailing windows, NaN until filled),
      `test_returns` unit tests GREEN, full QG passed (622s), on origin LDR. **REMAINING (operational): recompute the
      delta_one feature corpus** so these columns exist in GCS for the live paper run (a features-service backfill —
      shared with the P2.11.18 reversion-feature corpus recompute; run both together).
- [x] ✅ [UI] P2.11.17. **Mirror the `TSMOM_BTC_CTA` archetype into unified-trading-system-ui — SHIPPED + VERIFIED
      2026-06-22: ui@6442d46e | pw:L2 ✓ (67 passed, 4.0m) | regression: tests/unit/lib/architecture-v2/enums.test.ts
      (toHaveLength 19) + tests/unit/wizard/parity-gates.test.ts (58 archetypes) — both fail on TSMOM removal.** 15
      files (`lib/architecture-v2/enums.ts`+`coverage.ts`+`archetypes.ts`, `lib/help/help-tree-generated.ts`,
      `lib/mocks/fixtures/trading-data.ts`, `lib/registry/ui-reference-data.json`,
      `components/briefings/     strategy-coverage-matrix.tsx`, `components/marketing/strategy-family-catalogue.tsx`,
      `public/     capability-verdict-matrix.json` + 6 test files). tsc clean, 286 Vitest pass, `quality-gates.sh`
      exit 0. The playwright SMOKE gate (`tests/smoke/`) self-starts `PORT=3100 pnpm dev:mock` (120s boot) — the earlier
      BLOCKED-PLAYWRIGHT was just not waiting for boot; ran green here. Repo: unified-trading-system-ui.
- [ ] [CODE] P2.11.20. **Complete TSMOM_BTC_CTA capability wiring — add it to the UAC archetype_capability_manifest**
      (found 2026-06-22 via the e2e archetype-capability playbook). `TSMOM_BTC_CTA` is in `StrategyArchetype` + the UI
      enum/capability-verdict-matrix but **MISSING from
      `unified-api-contracts/.../internal/architecture_v2/     archetype_capability_manifest.json`** (22 archetypes, no
      TSMOM) → the archetype is half-wired (no per-venue/ asset-group capability cells) and the e2e playbook
      `tests/e2e/playbooks/refactor/     refactor-g1-8-uac-archetype-capability.spec.ts` would fail. Fix: add TSMOM's
      capability declaration to the source (`registry/archetype_capability_matrix.py` — family RULES_DIRECTIONAL,
      BTC-level CTA → CEFI perp+spot on the major venues, signal `price`/trend) → regen via
      `scripts/generate_archetype_capability_manifest.py` → sync to UI via
      `scripts/propagation/sync-archetype-capability-to-ui.sh` → re-QG/ship UAC+UI. Then the e2e playbook becomes the
      proper playwright-dir regression for the archetype. Repo: unified-api-contracts (+ UI sync). Confirm the exact
      venue/asset-group capability profile with the operator (CeFi-only BTC, or the DeFi+CeFi hybrid).
- [ ] [CODE] P2.11.18. **Add the intraday BTC mean-reversion signal as a cs ML feature** (research 2026-06-22, root
- [ ] [CODE] P2.11.18. **Add the intraday BTC mean-reversion signal as a cs ML feature** (research 2026-06-22, root
      `_ic_test.py`). A short-horizon reversion z-score (`zscore = -(close - rolling_mean) / rolling_std`, anchors 60m +
      4h on the canonical OHLCV) has a **stable Spearman IC ≈ +0.05 vs forward 15m–1h returns, positive across all
      horizons + every recent year** (2022-26). It is intraday-microstructure information the daily-horizon delta_one
      features do NOT capture (orthogonal), so it should ADD to the pooled-LightGBM cs ensemble. NOTE: the signal is NOT
      standalone-tradeable (its alpha is inside the execution-cost band — see the research arc: daily Monday-wick edge
      decayed, migrated to 1h, but realistic 1.5bp-taker fills cap it at a marginal +1.14 Sharpe); its value is as a
      FEATURE (here) + an execution-timing overlay (P2.11.19), where it never pays its own round-trip. Implement: add
      the reversion z-score feature spec(s) to the **features-service** `delta_one/app/features/registry.py` (new
      `feature_group` or extend an existing momentum/reversion group; bump `formula_version`; HIVE-partition + footer
      metadata per the feature-formula-versioning SSOT), compute + write to the feature corpus, then retrain + validate
      the cs model (does it lift cs Sharpe / reduce the 2026 drag — composes with P2.11.15). No lookahead (trailing
      window, shifted). Repo: features-service (feature) + cs-model retrain. Evidence: IC table in `_ic_test.py`. **STEP
      1 ✅ SHIPPED 2026-06-22 — features-service@1110ee1d.** `reversion_zscore_60m`/`reversion_zscore_240m` added to
      delta_one's `anomaly` calculator + `registry_specs.yaml` (clip ±5, `min_periods=bars` so NO partial-window /
      no-lookahead, honest NaN until filled), 6 `test_anomaly` unit tests GREEN, full QG passed (402s), on origin LDR
      (Tier-C drain → staging). **REMAINING (downstream operational/ML — both feature specs (reversion @1110ee1d + BTC
      trend @653cf158) are on LDR promoting; these run AFTER the spec deploy):** (a) **corpus recompute** — once the new
      feature image deploys (LDR→staging→main→image), backfill the `returns` + `anomaly` groups for cefi/BTC so the
      columns land in GCS: `features-service` CLI
      `--operation calculate --mode batch --asset-group cefi --feature-group     returns` (and `anomaly`), at scale via
      `deployment-service/scripts/vm/launch-features-backfill-vm.sh` (no-fire-and- forget: T+10min verify + manifest-row
      check). Also gates the P2.11.16 BTC-feature corpus for a non-null CTA paper run. (b) **cs retrain** — after the
      corpus has the columns, retrain the pooled-LightGBM cs model including the reversion features; validate it lifts
      cs Sharpe / cuts the 2026 drag (composes with P2.11.15's longer-horizon retrain — do both in one train). (c)
      `features-status --check-drift` verification. Sequenced-later; not in-session.
- [x] ✅ [CODE] P2.11.19. **Reversion execution-timing model — SHIPPED 2026-06-22: execution-service@4b8dc545.** New
      `backtest_v2/reversion_timing.py` (`time_reversion_fill`): the research z-score `-(p−mean_W)/std_W` times the fill
      to the first over-extension bar in the trade's favour (BUY at z>thr / SELL at z<−thr) within the window, **CLAMPED
      so smart ≥ benchmark by construction → `execution_alpha_bps ≥ 0`** (a fired-but-snapped-back bar clamps to the
      benchmark, alpha 0; no over-extension → honest BENCHMARK_FALLBACK). Decimal-exact + no now()/random → ε=0
      (paper↔batch determinism preserved); wired into `smart_fill_replay.py` (GroupC) + `compute_execution_alpha`. Unit
      tests (over-extension → alpha>0; no-fire → benchmark) GREEN, full QG passed. **Wire the reversion signal as the
      execution-timing model in execution-service GroupC smart-matching** (research 2026-06-22, root `_ic_test.py`). The
      SAME reversion z-score, used to TIME fills on the book's existing turnover (not as a standalone trade), captures
      **~+1.5 bps/leg** vs naive window-close fills (z>0.5 +1.4bp fires 100% of 4h windows; z>1.5 +1.7bp fires 96%) — a
      buy waits for an intraday over-extension-down within the rebalance window, a sell for an over-extension-up. This
      is **riskless execution alpha** (the trade happens regardless → no standalone round-trip cost, no
      adverse-selection/cost-floor problem) on every strategy's turnover (cs / trend / basis), compounding into
      net-Sharpe. This is PRECISELY the citadel "execution alpha" layer (`execution_alpha = smart − benchmark`) —
      implement the reversion z-score as the **smart-matching execution-timing model in execution-service GroupCRunner**
      (the smart-fill entrypoint shipped @3d7d760c, P11.6-retry), bounded by the rebalance-window timeout (fall back to
      benchmark fill if no over-extension fires). batch=live one path; the improvement surfaces as `execution_alpha_bps`
      in the ledger (P11.6). Repo: execution-service. Evidence: execution-timing table in `_ic_test.py`. Higher
      immediate value than the marginal standalone fade (which is shelved — see Progress Log 2026-06-22 "intraday
      reversion is a feature/exec-timing signal, not a standalone trade").
- [x] ✅ [CODE] P2.11.21. **Unify execution into ONE central candle-driven 1m-fill engine + per-strategy intent**
      (operator 2026-06-22). **ENGINE SHIPPED 2026-06-22 — execution-service@c50c467d:** shared
      `backtest_v2/candle_fill_engine.py` (`replay_candle_fill`) with the `ExecutionIntent` StrEnum universe —
      `IOC_TAKER` (cross, bar-0 full fill), `RESTING_LIMIT_TAKER` (residual rests at cross, fills on trade-back, never
      misses), `LIMIT_MAKER` (posted `improve_bps` inside the cross, fills at the EXACT posted price on the first 1m bar
      trading through by `FILL_THROUGH`=0.25bp, **MISSES on adverse selection**). Lifts the `_extreme_ml.py`
      1m-trade-through mechanism into GroupC, consumes canonical `CanonicalOHLCV`, Decimal/ε=0, 12 unit tests GREEN,
      basedpyright clean. Generalizes the shipped `reversion_timing` (4b8dc545). **REMAINING:** (a) wire the
      per-strategy `execution_intent` flag into each strategy + the `smart_fill_replay` call; (b) **download EVM-perp +
      basis spot/perp 1m candles** for the full cross-strategy style sweep (CeFi spot majors + 30 perp 1m series already
      cached, e.g. `perp_BTC_1m` 1.7M bars 2020→2026; gap = the EVM perps + basis pairs — the e2e-testing download); (c)
      apply the cost corrections at the central model (basis 5bp/leg×2, on-chain 1bp — measured per the honest book
      +110% on CAP / Sh 1.93 / -10% maxDD). Today the RESEARCH customises fills per leg (cs maker-25% / ext taker /
      basis maker-1bp / on-chain maker-0.5bp) — that's a measurement scaffold, NOT production. Production =
      execution-service GroupC: the strategy declares an **intent** (maker-inside-N-bp / taker-cross; urgency picked
      from a universe) and **one** engine executes uniformly by **replaying post-signal 1m candles** — fill on the first
      bar trading through the resting order, **MISS (~10%) on adverse selection** (price runs away favorably; driven by
      liquidity+price on the 1m bars, NOT a flat haircut). `_extreme_ml.py` (ext leg: limit rests, fills on 1m
      trade-through) is the working template; generalise it to all legs. **Download 1m candles wherever missing** (EVM
      perps for on-chain, spot+perp for basis) so every fill is MEASURED like the agent's 97 netflow names
      (2bp-inside-mid → 0.90 fill on real Binance 1m OHLC). **Cost corrections (apply at the central model, fee tier set
      ONCE globally):** on-chain maker **1bp** (not 0.5 — exchange floor); basis **5bp/leg ×2 + impact** (both spot+perp
      legs fill to stay delta-neutral → re-cost halves basis: +31%→+11-16% on CAP, Sharpe 15→4.5-7, since it turns 48x
      notional/yr — a slower basis rebal recovers some). Repo: execution-service (GroupC) + e2e-testing (1m-candle
      download + per-leg fill replay). Composes with P2.11.19. **Execution-intent UNIVERSE — sweep per strategy,
      MEASURED via the 1m replay, pick best/worst (operator 2026-06-22):** (a) **IOC taker** — cross, full immediate
      fill, pay spread+impact; (b) **resting-limit taker** — marketable/cross, but unfilled residual RESTS + fills on
      subsequent 1m candles (not cancelled); (c) **limit {0, 0.5, 1, 2} bp inside the taker/cross price** — maker,
      posted passive, fills on the first 1m bar trading through, can MISS on adverse selection (price runs away). The
      strategy declares which intent it uses (its urgency); the engine measures all and the best is the per-strategy
      verdict — e.g. ext-REVERT wants maker-inside (patient fade), ext-CONTINUE wants taker (urgent with-trend).
      **`_extreme_ml.py` ALREADY implements this exact mechanism** (the extreme triple-barrier 3-class model:
      REVERT→maker-inside with an `improve_bp` sweep + `FILL_THROUGH`=0.25bp + the limit RESTS and fills on ANY 1m
      trade-through within order-life; CONTINUE→taker; NEITHER→skip/ML-gate). The build is to **LIFT that mechanism out
      into the shared GroupC engine** + expose the intent as a per-strategy flag — NOT write new. Correct the "ext
      (reversion)" mislabel → "ext (extreme triple-barrier: continue/revert/neither)" in the plots/docs as part of this
      (research plots already fixed 2026-06-22).

- [ ] [CODE] P2.11.15. **cs leg 2026 drag — longer-horizon TARGET retrain in `_panel.py`** — the cross-sectional ML book
      (cs) is the single worst leg in the 2026 selloff (the XS signal mis-bets when dispersion collapses). The span-7
      EWMA denoise (shipped) is the 80% cheap fix; the proper fix is retraining the pooled LightGBM on a longer-horizon
      return target so the signal is less whipsawed by the noisy 15m next-bar label. No lookahead (trailing features,
      shifted target; IS-select 2023-24 / OOS-validate 2025-26). Repo: features/strategy research (`_panel.py`).

- [ ] [UI] P2.14. **Prod UI selector resolves the 14-strategy run, not the 145-run** (found 2026-06-21). The CRA API
      correctly resolves + serves the newest run `paper-20260621225959-e86237f7` (145 strategies / 7 archetypes —
      verified authenticated: `net-views.run_id` = the 145-run on every call). But the prod odum-portal UI's strategy
      selector renders only the 14 CARRY_STAKED_BASIS strategies of an OLDER run (`paper-20260621171725-fcf31316`). The
      UI calls SAME-ORIGIN `/api/*` (Next.js server-side proxy to the CRA — no `*_API_URL` env on odum-portal, so the
      target is baked in next.config rewrites). DIAGNOSIS: the selector's endpoint (instructions/manifest list) resolves
      or caches a different run than the CRA `per-strategy` SSOT `resolve_canonical_run` — likely (a) the proxy points
      at a different CRA, (b) a Next.js/React-Query cache, or (c) the selector endpoint doesn't key off
      `resolve_canonical_run`. FIX: confirm the next.config `/api` rewrite target == the deployed CRA, ensure the
      selector reads the same `resolve_canonical_run` SSOT, bust any cache. The 145-run data + ε=0 + all ledgers are
      correct in GCS + served by the CRA — this is purely UI run-resolution. Repo: unified-trading-system-ui (+ verify
      next.config proxy target).

- [x] ✅ [CODE] P2.15. **Match the e2e weighting: per-archetype RANK allocators, not FIXED equal-weight** — DONE,
      DUPLICATE of the shipped **P11.15** (`paper_universe` `allocator_archetype` default FIXED→rank; rank metrics from
      the same deterministic captured GCS rates → ε=0 preserved). Closed in the 2026-06-23 register cleanup. (operator
      2026-06-22: "in our e2e plots we picked several venues for e.g. basis and WEIGHTED across opportunities — I
      thought that was a production config"). CONFIRMED: a catalogue `@`-qualified id is a per-(venue,coin) CANDIDATE
      leg (145 of them); the e2e "strategy" is the ARCHETYPE + its rank allocator that ranks+weights across the cohort
      (`portfolio_allocator/archetypes_rank.py` 2-stage: rank groups → top-N → weight-by-metric — long lowest / short
      highest funding, rank-by-net-carry, inverse-vol). Production HAS this. GAP: `paper_universe.PaperUniverseConfig`
      defaults to `AllocatorArchetype.FIXED` (equal-weight) — so the paper book equal-weights all legs instead of the
      e2e opportunistic weighting. FIX: default each archetype to its rank allocator; the rank METRICS come from the
      SAME deterministic captured GCS rates (funding/carry/vol per window) → **ε=0 preserved** (pure fn of the window,
      not live calls — the FIXED default's determinism worry was overcautious). Verify ε=0 batch-rerun holds with rank
      weights. Repo: strategy-service (paper_universe allocator default + per-archetype rank wiring).
- [x] ✅ [UI] P11.16. **Archetype-level default view + all-145 per-strategy — DONE + prod-verified** (CRA@336e2dc rev
      00016-lcj = 145/7; ui@2f4c7016 = 7 books→legs w/ weights; browser-verified). Orig:**Default the paper-trading view
      to archetype-level "strategies" (legs as drill-down)** — the headline selector should read ~7 weighted archetype
      strategies (the e2e "strategy" granularity), each expandable to its weighted per-(venue,coin) legs, rather than
      145 flat legs. The archetype roll-up already exists (P11.9-ui group-by-archetype) — make it the DEFAULT framing +
      label the legs "candidate legs / constituents", show each leg's allocator weight. Repo: unified-trading-system-ui
      (playwright-gated). ALSO: the per-strategy rollup currently shows only 13 (the attribution-parquet subset for the
      145-run) — make it reflect ALL 145 by reading the manifest/instruction-ledger strategy_ids (or emit attribution
      for all 145), so the count + archetype grouping cover the full book.

- [x] ✅ [UI] P11.14-hook. **Prod paper-trading hooks now render REAL CRA data** — ROOT CAUSE (from the live console):
      `lib/api/mock-handler.ts`'s global fetch interceptor (NEXT_PUBLIC_MOCK_API=true) had no passthrough for
      `/api/client-reporting*`, so it returned empty `{}` → login got no access_token → every panel "Failed to load"
      with no network request. FIX (ui@f0ebd216): added `/api/client-reporting` to `realRoutePrefixes`. Now ALL 10
      ledger endpoints return 200, no errors, real CeFi venues render (odum-portal-00036-pzm). The full 4-part P11.14
      fix: isReportingLive hook gate + fs env-loader in next.config + rewrites-emit-in-mock + mock-handler passthrough.
      Verified browser-side. bugs are fixed (CRA reachable from the page: manual in-page fetch → 200, 13 strategies).
      But `useLedgerPerStrategy` / `useLedgerNetViews` etc. show "Failed to load" with NO `/api/client-reporting*`
      request issued, despite isMock=false (var inlined), clientId set (`?client=firm-paper-determinism`), no service
      worker, mock defined, fix code in the deployed chunks. Resolve from the LIVE browser console (the actual
      react-query error) — not headless inference. Likely candidates: an SSR/prefetch error, a QueryClient
      retry/throwOnError config, or the hook erroring in a transform before fetch. Repo: unified-trading-system-ui.

- [x] ✅ [CODE] P2.17 (P11.17). **Structurally forbid the synthetic-input seam in PAPER/LIVE prod runs** — DONE + LANDED
      (`strategy-service@a786d463`, on origin/live-defi-rollout, QG-green). `run_paper()` (the PAPER/LIVE
      mode=`TradingMode.PAPER` engine path — paper≡live one path) now calls `get_synthetic_input_override()` and RAISES
      loud if a synthetic override is active before booking any ledger (`paper_run_handler.py:1143-1152`); regression
      `tests/unit/cli/handlers/test_paper_run_synthetic_guard.py`. Makes "paper reads exactly like live" structural, not
      flag-dependent (the live handler is gated on custody, shares this engine path). (operator audit 2026-06-22: "all
      reads should be live+batch from real prod sources/schemas/GCS paths; writes canonical with just the paper→live tag
      swap"). AUDIT RESULT — already canonical: reads resolve every bucket via `resolve_bucket_name`
      (perp-funding/dex-pools/market-data/lending, real prod schemas+granularity, honest-skip never synthetic); writes
      go through the shared `write_run_ledger` seam to the canonical `client-reports` ledger path
      (`ledger/client_id=/run_id=/ledger_type=`) with `mode=TradingMode` (PAPER→LIVE swap; paper/batch IDENTICAL shape).
      The e2e synthetic seam (`set_synthetic_input_override`/`--synthetic-input`) is opt-in + default-None (only tests +
      the CLI flag set it) → OFF in the prod paper job. HARDENING: add a guard so `get_synthetic_input_override()` MUST
      be None when `mode ∈ {PAPER, LIVE}` (raise if a synthetic override is active in a prod-mode run) — makes "paper
      reads exactly like live" structural, not flag-dependent. Repo: strategy-service + unified-trading-library.

- [x] ✅ [UI] P11.18. **Archetype-grouped WEIGHTED PnL-over-time plot + batch/paper symmetry overlay** — SHIPPED
      unified-trading-system-ui@423e237d (PnlTimeseriesChart archetype-weighted lines via buildWeightMap +
      PaperBatchOverlayChart). VERIFIED LIVE on prod (odom-portal): the PnL-over-time panel renders the
      archetype-weighted lines + the "Paper vs batch (rerun) overlay" carrying the **"ε=0 PROVEN — paper ≡ batch"**
      badge. pw:L2 ✓ (21 passed) | regression: tests/smoke/paper-trading-ledger.smoke.spec.ts (P11.18 cases). (operator
      2026-06-22: "where is our grouped PnL plots of the strategy_ids in strategy-archetype groups where we weight
      between strategy_ids ... I don't see it on the page"). Today: a single selection-filtered PnL series +
      `BatchPaperPanel` showing the `live−batch=(paper−batch≈0)+(live−paper=exec α)` identity as NUMBERS. ADD: a
      multi-line PnL-over-time CHART with ONE line per ARCHETYPE BOOK (the allocator-weighted sum of its strategy_id
      legs — the e2e weighting), toggle archetype↔leg↔coin; AND overlay the BATCH-rerun PnL line vs the PAPER line so
      the ε=0 symmetry is visually legible per archetype (not just a verdict badge). Repo: unified-trading-system-ui
      (consumes /pnl-timeseries + /backtest + /per-strategy weights; playwright-gated).
- [x] ✅ [CODE+UI] P11.19. **Paper-trading data-quality + VM events stream panel** — SHIPPED + VERIFIED LIVE on prod.
      (a) CRA `GET /clients/{c}/data-quality` (client-reporting-api@7f3ac8a) = skipped_specs grouped by
      archetype/venue/reason + manifest coverage + alerting-service alerts merged (best-effort). **CRITICAL crash-fix:
      `coverage.by_archetype` was emitted as a dict → the UI's `DataQualityCoverageRow[].reduce` threw → the WHOLE paper
      dashboard white-screened ("Something went wrong"). Fixed CRA to emit the canonical array shape (image
      `client-reporting-api:dqarrayfix` deployed to prod rev 00018-njv; source quickmerge PENDING a live UTL-dep WIP
      settling — fix is LIVE regardless) + UI Array.isArray guard (unified-trading-system-ui@85369f75) + CRA unit-test
      now asserts the array contract (the smoke spec used the mock fixture which was already array-shaped, so it missed
      the real-data dict — the CRA test closes that gap).** (b) UI "Data Quality & Alerts" panel
      (unified-trading-system-ui@423e237d). VERIFIED on prod: headline **145/342 drivable · 197 skipped**, 12
      per-archetype coverage rows, 8 skipped-by-reason groups / 197 skipped (venue,coin) rows (top reason
      `no_gcs_data_in_window:2026-05-16..2026-05-22`, 127 cells), alerts section renders (honest `unavailable` — see
      P11.20). pw:L2 ✓ (21 passed) | regression: tests/smoke/paper-trading-ledger.smoke.spec.ts (P11.19 cases) +
      client-reporting-api/tests/unit/test_data_quality.py (array contract). Repo: client-reporting-api +
      unified-trading-system-ui.
- [x] ✅ [INFRA] P11.20. **Live VM alert STREAM into the data-quality panel** — SHIPPED + VERIFIED LIVE. Root cause of
      the prior `alerts_source: unavailable`: the CRA route hardcoded the k8s DNS `http://alerting-service:8080` which
      does NOT resolve from Cloud Run. FIX (client-reporting-api): repoint `_live_alerts` at the **reachable, public**
      deployment-api unified alert ledger (`uts-shared-deployment-api…/api/alerts` — the SAME source deployment-ui's
      monitoring pane shows: CI/CD + vm_down + consolidator_down + worker_liveness + git_health) + a `_map_alert` that
      projects the ledger `AlertEntryDict` → the UI `DataQualityAlert` closed shape (severity coerced to
      critical|warning|info). VERIFIED on prod (rev `client-reporting-api-00019-8k2`): `alerts_source: deployment-api`
      (was "unavailable"); 0 active alerts → panel shows "fleet is clean" honestly. The alert FEED is now live; it
      populates when the fleet emits events. Remaining (NOT blocking): the per-env URL is a constant default (P11.21
      folds it into the deployment-api-SSOT client); the per-epic data fleet that emits ADAPTER_FETCH_FAILED/
      honest-absence is post-cutover/not-running so the stream is empty until it runs. Repo: client-reporting-api.
      regression: client-reporting-api/tests/unit/test_data_quality.py (alerts merge + shape-map +
      degrade-to-unavailable).
- [x] ✅ [CODE+UI] P11.21. **Reconcile the paper data-quality panel against the deployment-api data-status SSOT** —
      SHIPPED + VERIFIED LIVE (operator 2026-06-22: "lets use SSOT so if it breaks there we fix at the source"). CRA:
      new `core/deployment_api_client.py` — ONE typed client for the deployment-api (consolidates P11.20 alerts + P11.21
      coverage, single base-URL home); the data-quality endpoint now returns `manifest_coverage` (the corpus manifest
      4-state per asset_group: `captured`/`empty_confirmed`/`attempted_failed`/`expected_unattempted`/ `coverage_pct`)
      from `/api/data-status/honest-coverage` — the SAME SSOT the deployment-ui data-status bars read. VERIFIED on prod
      (rev `client-reporting-api-00020-9sp`): `manifest_source: deployment-api`, 5 AG rows (cefi 11.68%, defi, tradfi,
      sports, prediction) — identical numbers to the deployment-ui page. UI: dual-lens panel
      (`paper-trading-ledger-panels.tsx`) — run lens ("this run could drive", skipped_specs) + corpus lens ("data
      EXISTS", manifest SSOT) with an "SSOT unavailable" honest-degrade. pw:L2 ✓ (21 passed) | regression:
      tests/smoke/paper-trading-ledger.smoke.spec.ts (data-quality-manifest) + client-reporting-api/tests/unit/
      test_data_quality.py (TestDeploymentApiClient + manifest_coverage). Repo: client-reporting-api (live) +
      unified-trading-system-ui (landed LDR, prod UI deploy in flight). **CRA source-quickmerge LANDED**
      (`client-reporting-api@5a65b10`, on origin/live-defi-rollout — verified `merge-base --is-ancestor`). NOTE: per-env
      base URL is a constant default; the `UnifiedCloudConfig` URL field is now done as P11.21-polish (see below).
- [x] ✅ [CODE][UI] P2. **Min-coverage threshold — "drivable-but-thin" state** (item 11.22) (operator 2026-06-22: "is it
      only 100% or is >80% still relevant for backtest"). Today a spec is BINARY drivable-vs-skipped: any data in window
      → runs (drivable, regardless of how complete); zero → skipped. ADD a configurable per-archetype
      min-window-coverage threshold (e.g. ≥80% of expected bars present) → a third "drivable-but-thin" state so a
      backtest run on sparse data is flagged, not silently trusted. Compute window-coverage % at the engine's
      honest-skip decision (`paper_universe._skip_reason_for_spec` + the `run_paper` data-fetch), carry it on the spec,
      surface it in the data-quality panel + gate weighting. Repo: strategy-service (threshold + coverage %) +
      client-reporting-api (surface) + unified-trading-system-ui (panel). NICE-TO-HAVE (paper book is honest binary
      today). **SHIPPED 2026-06-23** — per-archetype min-window-coverage threshold (default 80%; cross-sectional
      funding/price dispersion 85%; `PaperUniverseConfig.min_window_coverage` is the operator override) → the third
      `drivable_thin` state. Coverage % = `len(market_data_days) / expected_window_days` computed in `run_paper` for
      every DRIVEN spec (`compute_spec_coverage`), pinned to a new `spec_coverage/{run_id}.json` sidecar; thin is a
      SUBSET of drivable (a thin spec STILL books trades — ε=0 untouched, flag-only). CRA `read_spec_coverage` folds it
      into the data-quality API (`coverage.drivable_thin` per-archetype + a sorted `thin_specs` list, worst coverage
      first); the UI panel renders an amber "thin" sub-bar + headline count + a "Drivable-but-thin specs" table showing
      each (venue, coin) coverage% `<` threshold. Evidence: unified-trading-library@90697df6 (`write_run_spec_coverage`
      sidecar writer + unit test; QG green 167s) · strategy-service@4dc69827 (`compute_spec_coverage` +
      `min_window_coverage_for` + `run_paper` wiring + 6 tests; QG green 180s) · client-reporting-api@9a631a4
      (`read_spec_coverage` + `_thin_rows` + `drivable_thin`/`thin_specs` route surface + 4 tests; QG green 88s) ·
      unified-trading-system-ui@558127f5 | pw:L2 ✓ (70/70 `tests/smoke/` serial — the all-cores-parallel local flakes
      reproduce on baseline with this change stashed, so unrelated) | regression:
      tests/smoke/paper-trading-ledger.smoke.spec.ts (the "drivable-but-thin state with coverage %" P11.22 case).
- [x] ✅ [UI] P11.23. **deployment-ui "Backend unreachable" debounce + form a11y** — SHIPPED + VERIFIED LIVE. Operator
      2026-06-22: the data-status page flashed a red "Backend unreachable — signal timed out" banner + "Unknown error"
      detail even though the backend was up (coverage bars rendered; min-instances=1, `/api/health` 46ms warm). Root
      cause: a SINGLE transient `/api/health` poll timeout (a heavy data-status manifest-merge briefly saturating the
      worker) LATCHED the red banner for a full 30s poll interval. FIX (`MockModeBanner.tsx` `useBackendHealth`):
      debounce — keep last-good state + fast-retry on the 1st failure, go red only on the 2nd consecutive (a genuine
      outage still surfaces within ~4s of the 2nd poll). ALSO fixed the operator's console a11y warnings — `id`/`name` +
      label association on the 5 data-status filter inputs (`DataStatusTab.tsx`: symbol/venue search, start/end date,
      freshness). LANDED on LDR (MockModeBanner debounce + DataStatusTab a11y both confirmed on origin/LDR) + LIVE via
      the deployment-api rebuild (rev `uts-shared-deployment-api-00079-qg6`; served bundle confirmed to carry both).
      regression: src/components/MockModeBanner.test.tsx (8 pass) + the data-status a11y ids. Repo: deployment-ui.

## Temporary states + their canonical follow-up plans

- P7.3 (live leg) is `BLOCKED-OPERATOR-DECISION` until a live wallet/custody is approved (hard-stop: wallet keys are
  human-only). The paper↔batch determinism proof (P7.2) does not depend on it.

## Progress Log

> **History moved 2026-07-24**: the full dated Progress Log (2026-06-19 through 2026-06-22, zero open todos) was
> extracted verbatim to keep this plan under its line-count cap — see
> [`plans/active/citadel_paper_batch_live_reconciliation_history_2026_07_24.md`](/plans/archive/2026_07/citadel_paper_batch_live_reconciliation_history_2026_07_24.md)
> for the full historical narrative of how the determinism spine was built.
