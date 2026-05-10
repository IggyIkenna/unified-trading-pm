---
title: Client reporting + PnL attribution MVP — per-client NAV / PnL / metrics surface for cutover
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (Group F item 22 P&L attribution, Group G item 23 operator UX)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/client_reporting_pnl_attribution_2026_05_08.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/wallet_treasury_client_flow_2026_05_10.md
  - plans/active/risk_simulations_limits_alerting_2026_05_10.md
  - plans/active/promote_workflow_backtest_to_live_2026_05_10.md
related_codex:
  - codex/04-architecture/backtest-groups.md
  - codex/09-strategy/strategy-summary.md
  - codex/04-architecture/capital-efficiency-patterns.md
  - codex/02-data/honest-absence-downstream-handling.md
---

# Client reporting + PnL attribution MVP

## Why this plan exists

May-23 cutover requires that the operator can show — for the live paper-trade demo client — a real-time NAV + PnL +
per-archetype attribution + per-strategy-leg attribution + per-execution-quality (slippage / latency / fees) split. The
matching engine already produces strategy-alpha vs execution-alpha decomposition (CLAUDE.md "Batch = Live"); the
position-balance + execution event streams already carry the underlying numbers. What's missing is the (a) UAC
client-reporting contracts, (b) client-reporting-api routes that aggregate per-client, (c) deployment-ui ClientReporting
tab, (d) PnL attribution emitter that joins strategy + execution + funding + fee streams into a single per-client
parquet, (e) demo client seeded end-to-end. This plan ships the cutover MVP — single demo client, real PnL streams,
operator-visible UI — and defers multi-client invoicing + share-class accounting breadth to post-cutover.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. UAC client-reporting contracts: `ClientId`, `ClientShareClass`, `ClientPosition`, `ClientPnLEntry`, `ClientNAV`,
   `PnLAttributionRow` (strategy / execution / funding / fee / slippage / financing), `ClientReportingMode`.
2. PnL attribution emitter: subscribes to position-balance + execution + funding + fee event streams; joins on
   correlation + per-trade lineage; emits `PnLAttributionRow` parquet per (client, archetype, day) at
   `gs://{pid}-client-reports/`.
3. client-reporting-api routes: `/api/clients/{id}/nav`, `/{id}/pnl`, `/{id}/positions`, `/{id}/attribution`.
4. deployment-ui ClientReporting tab: NAV time-series, PnL waterfall, per-archetype attribution, per-leg drilldown.
5. Demo client seed: 1 internal demo client with both cutover archetypes subscribed; full flow works end-to-end on real
   paper-trade data.
6. Codex SSOTs: 2 NEW + 2 UPDATE.
7. Real-VM cutover-archetype run with the demo client + readiness gate.

### Non-goals (post-cutover)

- Multi-client invoicing engine + fee crystallization across share classes — owned by separate post-cutover plan.
- External-strategy-via-API-keys flow PnL attribution — owned by `wallet_treasury_client_flow` post-cutover phase.
- Tax reporting / regulatory disclosures — multi-quarter, separate plan.
<!-- Performance fee high-water-mark accounting pulled into May-23 scope per operator direction 2026-05-10; owned by `wallet_treasury_client_flow_2026_05_10` Phase 4.C-D + Phase 5.F-I (HWM ledger + crystallization). This plan's `PnLAttributionRow` gains a `HWM_CRYSTALLIZATION` component to attribute the perf-fee accrual to the correct period. -->

## Pre-audit / blast radius

| Repo                                     | Surface                                                                                             |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`                  | NEW: `canonical/domain/client_reporting/`; `registry/client_share_classes.py`                       |
| `unified-trading-library`                | NEW: `pnl_attribution/emitter.py`, `pnl_attribution/joiner.py`                                      |
| `position-balance-monitor-service`       | UPDATE: emit per-client per-trade lineage on every position event                                   |
| `execution-service`                      | UPDATE: emit per-client per-trade execution-alpha decomposition (already partly in matching engine) |
| `client-reporting-api` (existing)        | NEW endpoints + Pydantic models from UAC                                                            |
| `deployment-ui` (or dedicated client UI) | NEW ClientReporting tab; reuse chart components                                                     |
| `unified-trading-pm`                     | NEW + UPDATE codex docs                                                                             |

## Phased execution DAG

```text
0 (pre-audit) → 1 (UAC contracts) → 2 (PnL attribution emitter) → 3 (per-service emit-with-lineage migration, parallel)
→ 4 (client-reporting-api routes) → 5 (deployment-ui tab) → 6 (demo client seed) → 7 (codex SSOTs) →
8 (real-VM cutover run) → 9 (cutover gate)
```

## Phase 0 — Pre-audit (Day 1, ~0.5 AI-day, 3 parallel sub-agents)

- [ ] [AGENT] P0. **0.A Existing PnL emission audit.** position-balance + execution-service event streams: what's
      emitted today, what's missing for per-client decomposition, what's the current correlation_id flow.
- [ ] [AGENT] P0. **0.B Existing client-reporting-api audit.** What endpoints exist, what's mocked, what's wired to real
      data.
- [ ] [SCRIPT] P0. **0.C Banners on cross-plan files.**

**Full-execution criterion**: § Audit findings populated; banners on 3 plans.

## Phase 1 — UAC client-reporting contracts (Days 2-3, ~1.5 AI-days)

- [ ] [AGENT] P0. **1.A `ClientId` + `ClientShareClass` + `ClientReportingMode` enums.** Closed sets;
      `ClientReportingMode ∈ {DEMO, PAPER, LIVE}`.
- [ ] [AGENT] P0. **1.B `ClientPosition` + `ClientPnLEntry` + `ClientNAV` Pydantic dataclasses.** Per-position lineage
      (archetype_id, strategy_leg_id, trade_id, venue, instrument, qty, mark, cost-basis, realized-pnl, unrealized-pnl).
- [ ] [AGENT] P0. **1.C `PnLAttributionRow` closed-component decomposition.** Components: `STRATEGY_ALPHA`,
      `EXECUTION_ALPHA`, `SLIPPAGE`, `FEES`, `FUNDING`, `FINANCING`, `BORROW`, `REBALANCE`, `HWM_CRYSTALLIZATION` (added
      2026-05-10 — attributes per-period perf-fee crystallization to the correct period; sourced from
      `PerformanceFeeCrystallizedEvent` per `wallet_treasury_client_flow_2026_05_10` Phase 5.G). Per-row sums to per-day
      client PnL.
- [ ] [AGENT] P0. **1.D Registry seed.** `registry/client_share_classes.py` with the demo share class + the live-DeFi
      cutover share class.
- [ ] [AGENT] P0. **1.E Tests.** ≥20 unit tests; round-trip + decomposition-sum invariant + per-mode coverage.

**Full-execution criterion**: UAC PR pushed; QG green; round-trip test passes.

## Phase 2 — UTL PnL attribution emitter (Days 3-5, ~2 AI-days)

- [ ] [AGENT] P0. **2.A `pnl_attribution/joiner.py`.** Joins position-balance + execution + funding + fee event streams
      on `(client_id, archetype_id, trade_id, ts_window)`. Strict-mode: missing leg = `record_failed` with typed reason,
      NOT silent zero (per honest-absence rule).
- [ ] [AGENT] P0. **2.B `pnl_attribution/emitter.py`.** Per (client, archetype, day) parquet emit at
      `gs://{pid}-client-reports/{client_id}/{archetype}/{YYYY-MM-DD}/attribution.parquet`. Reuses Tab 4's
      `bucket_naming.py` SSOT.
- [ ] [AGENT] P0. **2.C Decomposition-sum invariant check.** UTL helper: per-day per-client
      `sum(PnLAttributionRow.amount) == ClientNAV.delta`. Fails loud on violation.
- [ ] [AGENT] P0. **2.D Tests.** ≥30 unit tests; mocked event streams; invariant assertion.

**Full-execution criterion**: UTL PR pushed; QG green; integration test on stub streams emits non-empty parquet.

## Phase 3 — Per-service emit-with-lineage migration (Days 5-7, ~2 AI-days, 3 parallel sub-agents)

- [ ] [AGENT] P0. **3.A position-balance emit-with-lineage.** Every position event carries
      `(client_id, archetype_id, strategy_leg_id, trade_id)`. Backfill via existing correlation_id where available;
      gap-fill via execution-service trade lineage.
- [ ] [AGENT] P0. **3.B execution-service per-client decomposition.** Matching engine emits per-trade `STRATEGY_ALPHA` +
      `EXECUTION_ALPHA` already (CLAUDE.md). Extend to emit `SLIPPAGE` / `FEES` / `FUNDING` / `FINANCING` separately.
- [ ] [AGENT] P0. **3.C Funding + fee + financing aux emit.** MTDS funding events + execution fee events + custody
      financing events all gain `client_id` via subscription mapping.

**Full-execution criterion**: 3 service repos green; sample event-stream read shows `client_id` on every relevant event.

## Phase 4 — client-reporting-api routes (Days 7-8, ~1 AI-day)

- [ ] [AGENT] P0. **4.A `/api/clients/{id}/nav` endpoint.** Reads UAC `ClientNAV` shape from parquet; supports
      time-range query.
- [ ] [AGENT] P0. **4.B `/api/clients/{id}/pnl` endpoint.** Returns daily PnL series.
- [ ] [AGENT] P0. **4.C `/api/clients/{id}/positions` endpoint.** Current open positions + cost basis.
- [ ] [AGENT] P0. **4.D `/api/clients/{id}/attribution` endpoint.** PnL waterfall by component.

**Full-execution criterion**: 4 routes return real data for the demo client when queried locally + on a deployed Cloud
Run revision.

## Phase 5 — deployment-ui ClientReporting tab (Days 8-10, ~1.5 AI-days)

- [ ] [AGENT] P0. **5.A NAV time-series chart.** Per-client; range-selector.
- [ ] [AGENT] P0. **5.B PnL waterfall chart.** Per-archetype × per-component; reuses Recharts patterns.
- [ ] [AGENT] P0. **5.C Per-leg drilldown.** Click an archetype bar → per-strategy-leg detail.
- [ ] [AGENT] P0. **5.C2 HWM crystallization timeline.** Per share-class HWM-vs-NAV chart with crystallization-event
      markers; per-period perf-fee summary card (period_start / period_end / hwm_at_start / hwm_at_end / gross_pnl /
      perf_fee_amount / perf_fee_rate). Reads from `wallet_treasury_client_flow_2026_05_10` Phase 5.F audit log +
      `PerformanceFeeCrystallizedEvent` stream.
- [ ] [AGENT] P0. **5.D Operator-MVP.** Demo client visible by default; switcher for future clients.
- [ ] [AGENT] P0. **5.E Playwright smoke.** End-to-end test confirms tab loads + cards render against live API.

**Full-execution criterion**: deployment-ui shows demo client NAV + PnL + waterfall against real cutover-archetype data.

## Phase 6 — Demo client seed (Day 10, ~0.5 AI-day)

- [ ] [AGENT] P0. **6.A Seed config.** UAC registry: 1 demo client, both cutover archetypes subscribed, demo share
      class.
- [ ] [AGENT] P0. **6.B Position seeding.** position-balance bootstraps demo client's positions from existing
      paper-trade state.

**Full-execution criterion**: real paper-trade events flow into demo client's parquet attribution within 60s.

## Phase 7 — Codex SSOTs (Day 11, ~0.5 AI-day)

- [ ] [AGENT] P0. **7.A NEW `codex/04-architecture/client-reporting-architecture.md`.** Per-client lineage flow,
      attribution decomposition, parquet shape.
- [ ] [AGENT] P0. **7.B NEW `codex/04-architecture/pnl-attribution-decomposition.md`.** Component closed enum, sum
      invariant, per-archetype expected ranges.
- [ ] [AGENT] P0. **7.C UPDATE `backtest-groups.md`** — attribution emit applies to backtest groups.
- [ ] [AGENT] P0. **7.D UPDATE `strategy-summary.md`** — strategy alpha vs execution alpha cross-link.

**Full-execution criterion**: 2 NEW + 2 UPDATE; cross-references resolve.

## Phase 8 — Real-VM cutover run (Days 11-12, ~1 AI-day)

- [ ] [SCRIPT] P0. **8.A Cutover-archetype demo run.** VM `client-reporting-cutover-demo-` runs both archetypes for 24h
      on paper-trade data; emits per-client attribution; UI renders.
- [ ] [AGENT] P0. **8.B Invariant verification.** Decomposition-sum invariant green every hour.
- [ ] [AGENT] P0. **8.C Evidence capture.**

**Full-execution criterion**: 24h dry-run completes; ≥1 attribution.parquet per archetype × 24 hours; invariant green.

## Phase 9 — Cutover gate (Day 12, ~0.25 AI-day)

- [ ] [AGENT] P0. **9.A Master plan extension.** Group F item 22 row: "Demo client NAV + PnL attribution visible
      end-to-end."
- [ ] [AGENT] P0. **9.B Banners removed.**

**Full-execution criterion**: master plan row green; banners gone.

## Cross-plan coordination

- `wallet_treasury_client_flow_2026_05_10` — share-class subscription contracts compose with this plan's
  `ClientShareClass`.
- `risk_simulations_limits_alerting_2026_05_10` — per-client risk limits join on `client_id`.
- `promote_workflow_backtest_to_live_2026_05_10` — promote events emit per-client when archetype goes live.
- `simulation_scenarios_topology_price_shocks_2026_05_09` — synthetic scenarios run against demo client to validate PnL
  bounding under shock.

## Deferred work after 2026-05-10 plan-creation session

| Item                                                     | Status                        | Successor / blocker                                                                                                                                                                                                            |
| -------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Multi-client invoicing engine + fee crystallization      | DEFERRED-PER-USER             | Post-cutover; spans weeks; separate plan to be filed                                                                                                                                                                           |
| External-strategy-via-API-keys PnL attribution           | DEFERRED                      | `wallet_treasury_client_flow_2026_05_10` post-cutover phase                                                                                                                                                                    |
| Tax reporting / regulatory disclosures                   | DEFERRED-PER-USER             | Multi-quarter; compliance plan owns it                                                                                                                                                                                         |
| ~~Performance fee high-water-mark across share classes~~ | **PULLED FORWARD 2026-05-10** | Now in scope per operator direction; HWM ledger + crystallization owned by `wallet_treasury_client_flow_2026_05_10` Phase 4.C-D + 5.F-I; this plan adds `HWM_CRYSTALLIZATION` component (Phase 1.C) + UI timeline (Phase 5.C2) |

## Done definition

1. ✅ Phases 0-9 every checkbox flipped with evidence.
2. ✅ UAC + UTL + 4 service repos + UI + PM green.
3. ✅ Demo client end-to-end: paper-trade event → per-client parquet → API → UI; invariant green.
4. ✅ 2 NEW + 2 UPDATE codex docs.
5. ✅ Master plan Group F item 22 row green.

## Audit findings

(Phase 0 sub-agents fill.)

## DONE block

(Filled at completion.)
