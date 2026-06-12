---
title: "TradFi S&P ML + price-arb backtest readiness (ES feature runs + data-clean slice)"
parent_epic: tradfi_master
priority: P0
status: active
execution_scope: orchestrator-agent
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
locked_by: live-defi-rollout
locked_since: 2026-06-20
related_plans:
  - ../epics/tradfi_master.md
  - ./tradfi_manifest_canonicalisation_2026_06_01.md
  - ./tradfi_massive_dual_source_2026_05_28.md
  - ../active/master_to_live_defi_2026_05_23.md
---

> **Provenance**: extracted 2026-06-20 from the inline `tradfi_master` epic body during the asset-group-umbrella
> restructure (the L0 umbrellas had accumulated stale May-07/08 inline todos the backlog regen never scanned —
> `regen_backlog_from_plan.py` reads `plans/active/*.md`, never `plans/epics/`). This plan carries the **TradFi-owned,
> net-new** slice of the two folded May-23 deliverables (S&P prediction "deliverable A" + price-arbitrage "deliverable
> B"): the ES/VIX feature-calculator runs, the ml-training ES smoke, and the full S&P backtest run — the parts that are
> genuinely TradFi-data work and were never dispatched.
>
> **POINTERS, NOT extractions (do NOT duplicate):**
>
> - The **2-year backtest harness / matching-engine fidelity** (master plan Group F items 17 + 18) overlaps
>   `master_to_live_defi_2026_05_23` Group F + strategy-service + the archived
>   `trading_agent_service_architecture_unlock_2026_05_22` — that work and the **cutover gating** stay in master Group
>   F; this plan only RUNS the TradFi backtest against it once the data + features are clean.
> - The **strategy catalogue completeness** (S&P + price-arb archetypes × venue combos) is a cross-cutting concern owned
>   by master Group F's strategy-catalogue dependency, not here.
> - **Instrument / MTDS / MDPS data-clean** for ES/MES/BTC futures + S&P spot + ETFs (the "End-state at May 23"
>   data-clean criteria) is owned by
>   [`tradfi_manifest_canonicalisation_2026_06_01`](./tradfi_manifest_canonicalisation_2026_06_01.md) (manifest v9 +
>   pipeline_mode + honest-absence) and
>   [`tradfi_massive_dual_source_2026_05_28`](./tradfi_massive_dual_source_2026_05_28.md) (Massive/Databento source
>   column). This plan READS clean data; it does not re-do the canonicalisation walk.

## Context

The `sp_prediction_may_23_2026.epic` (deliverable A) and `price_arbitrage_may_23_2026.epic` (deliverable B) were folded
into `tradfi_master` 2026-05-08. Their design open-questions are all RESOLVED (C5 LightGBM model shape; daily retrain;
FOMC+NFP+CPI calendar features; hourly BTC features). What remained OPEN as inline epic todos — and was never dispatched
because the backlog regen does not scan `plans/epics/` — is the actual TradFi-data execution: run the feature
calculators for tradfi/ES + tradfi/CBOE-VIX, smoke the ES ml-training window, and run the full 2020→2026 S&P backtest.

Per master plan asset-group readiness, **TradFi is batch-only this cutover cycle** (no live trading by 2026-05-23) but
the ML pipeline must be running on a representative sample so a post-cutover archetype launch can flip live quickly.

## P0 — ES / VIX feature-calculator data-clean runs

- [ ] [AGENT] P0. Run `features-delta-one-service` for **tradfi/ES** across its calculators (continuous-series + roll-
      adjusted; `FuturesRollAdjuster` already shipped per epic). Confirm feature parquets land with no NaN-blanket
      placeholders and `available_at` correctly stamped per row (write-time). (Epic L245.)
- [ ] [AGENT] P0. Run `features-volatility-service` for **tradfi/ES + tradfi/CBOE-VIX** (realized-vol + skew;
      `compute_vix_features()` calculator already shipped per epic — level, contango proxy, momentum, vol-of-vol).
      Confirm feature parquets land clean. (Epic L247.)

## P3 — S&P ML + arb backtest exploration (gated on data-clean above)

- [ ] [AGENT] P3. Smoke `ml-training-service` on a 1-month ES window; confirm features land in the feature store and the
      C5 LightGBM model shape trains end-to-end (no skipped windows, no silent NaN-substitution). (Epic L303.)
- [ ] [AGENT] P3. Full S&P swing-high/low backtest **2020-01-01 → 2024-12-31 (train) / 2025-01-01 → 2026-05-05 (test)**.
      Report OOS Sharpe + max drawdown + top-20 feature importance. Run against the master Group F backtest harness
      (item 18) — do NOT build a TradFi-specific backtest engine (batch=live, one path). (Epic L305.)
- [ ] [AGENT] P3. Price-arb backtest readiness against the master Group F harness (item 17 fidelity): CME
      same-day-expiry arb (ES/MES/micros + BTC-futures variants), ETF↔future arb (SPY/IVV/VOO vs ES), cross-venue ETF
      arb. This plan supplies the **TradFi data + ES features**; the matching-engine / fee / microstructure fidelity +
      the cutover gating live in `master_to_live_defi_2026_05_23` Group F. Capture P&L variance per config dimension.
      (Epic deliverable-B L632-634.)

## Success criteria

- tradfi/ES + tradfi/CBOE-VIX feature parquets are clean (no NaN-blanket, `available_at` stamped, LookaheadBiasError
  strict-mode passes) on real GCS feature-store data — verified, not assumed.
- The C5 S&P ML model trains end-to-end on the representative window via the existing ml-training pipeline.
- The S&P + price-arb backtests RUN against the master Group F harness (no new asset-group backtest engine); OOS metrics
  captured.
- `bash scripts/quality-gates.sh` green on any `features-service` / `ml-training-service` change before commit.

**Full-execution criterion** (per "Plans Run To Actual Completion" HARD RULE): the feature-calculator runs + the
backtest execute on real infra against real data and produce verified parquets / metrics — code-shipped is not
operationally- shipped. The backtest-harness fidelity + the May-23 cutover decision are gated in master Group F, not
here.
