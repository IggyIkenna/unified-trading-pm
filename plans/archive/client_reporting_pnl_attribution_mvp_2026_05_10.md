---
doc_type: plan
title: Client reporting + PnL attribution MVP — per-client NAV / PnL / metrics surface for cutover
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    client-reporting-api,
    deployment-service,
    deployment-ui,
    execution-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/wallet_treasury_client_flow_2026_05_10.md,
    plans/active/risk_simulations_limits_alerting_2026_05_10.md,
    plans/active/promote_workflow_may23_cli_path_2026_05_10.md,
  ]
created: 2026-05-10
type: plan
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (Group F item 22 P&L attribution, Group G item 23 operator UX)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/client_reporting_pnl_attribution_2026_05_08.md
related_codex:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/backtest-groups.md,
    /codex/09-strategy/strategy-summary.md,
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
estimate_class: design
estimate_baseline_ai_days: 10.8
estimate_calibrated_ai_days: 6.5
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~0.5, ~1.5,
  ~2, ~2, + 6 more). Class inferred from filename (design, multiplier 0.6×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

> **ARCHIVED 2026-05-16 — 100% done per inventory (slot-8 SWEEP-16 mechanical archive sweep)**

# Client reporting + PnL attribution MVP

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BE-AWARE)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> introduces a workspace-wide sequencing constraint. Per operator decision (b+) 2026-05-11, all bucket-naming
> reads/writes route through the yaml SSOT (`deployment-service/configs/cloud-providers.yaml`) via
> `unified_trading_library.cloud_interface.bucket_naming.resolve_bucket_name(...)`. **Required for this plan**: any
> client-reporting output bucket (per-client NAV / PnL parquets) + pnl-attribution archetype-bucket output MUST use the
> resolver, never inline f-string `f"gs://{bucket}/..."` (QG STEP 5.69 ratchet enforces). Env-tier (prod/staging/dev) is
> in the bucket NAME; archetype + per-client partition is in the PATH. Phase 0c bucket provisioning (~300-400 env-tiered
> buckets) lands during Phase 2 (2026-05-15→05-19); client-reporting buckets are part of that provisioning if not
> already covered. **BE-AWARE** when scoping pnl-attribution output paths — coordinate with
> `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0b yaml additive corrections to ensure the canonical SSOT
> names every bucket this plan writes.

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
   `PnLAttributionRow` (factor × layer dual-axis per
   `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` Hard Rule #4 — `factor: PnLFactor` from the
   canonical 16-factor set + `layer: PnLLayer ∈ {STRATEGY, EXECUTION}`; `STRATEGY_ALPHA` / `EXECUTION_ALPHA` are derived
   sum-by-layer views, NOT enum members), `ClientReportingMode`.
2. PnL attribution emitter: subscribes to position-balance + execution + funding + fee event streams; joins on
   correlation + per-trade lineage; emits `PnLAttributionRow` parquet per (client, archetype, day) at
   `gs://{pid}-client-reports/`. Uses BENCHMARK matching-engine replay (per
   `/codex/04-architecture/batch-live-architecture.md §5/§6`) to derive the STRATEGY layer; live or SIMULATED fills
   minus BENCHMARK = EXECUTION layer.
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

<!-- Performance fee high-water-mark accounting pulled into May-23 scope per operator direction 2026-05-10; owned by `wallet_treasury_client_flow_2026_05_10` Phase 4.C-D + Phase 5.F-I (HWM ledger + crystallization). HWM crystallization is recognised via a NEW `FeeRecognitionRow` table emitted from `wallet_treasury_client_flow` Phase 5.G's `PerformanceFeeCrystallizedEvent` — NOT as a `PnLAttributionRow.factor` value (per pnl-attribution.md Hard Rule #4 + the plan-vs-codex factor name mapping table; HWM crystallization is fee accounting, not a P&L driver). The deployment-ui ClientReporting tab Phase 5.C2 reads `FeeRecognitionRow` directly from the wallet plan's emit and joins it into the NAV waterfall view. -->

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

- [x] [AGENT] P0. **0.A Existing PnL emission audit.** position-balance + execution-service event streams: what's
      emitted today, what's missing for per-client decomposition, what's the current correlation_id flow.
      (PM@retroactive-2026-05-14 — findings in § Audit findings)
- [x] [AGENT] P0. **0.B Existing client-reporting-api audit.** What endpoints exist, what's mocked, what's wired to real
      data. (PM@retroactive-2026-05-14 — findings in § Audit findings)
- [x] [SCRIPT] P0. **0.C Banners on cross-plan files.** (PM@pending — banners added to wallet_treasury_client_flow,
      risk_simulations_limits_alerting, promote_workflow_may23_cli_path 2026-05-12)

**Full-execution criterion**: § Audit findings populated; banners on 3 plans.

> **DEFERRED**: 0.A + 0.B pre-audit not yet done (Phase 1 shipped first per operator reserve direction). 0.A/0.B to be
> run as Phase 2 prep — see `## Deferred work` section below.

## Phase 1 — UAC client-reporting contracts (Days 2-3, ~1.5 AI-days)

- [x] [AGENT] P0. **1.A `ClientId` + `ClientShareClass` + `ClientReportingMode` enums.** Closed sets;
      `ClientReportingMode ∈ {DEMO, PAPER, LIVE}`. (UAC@b3233e5 — `ClientReportingMode(StrEnum)` in
      `internal/reporting/client_reporting.py`; reuses `ShareClass` from `canonical/crosscutting/share_class.py`)
- [x] [AGENT] P0. **1.B `ClientPosition` + `ClientPnLEntry` + `ClientNAV` Pydantic dataclasses.** Per-position lineage
      (archetype_id, strategy_leg_id, trade_id, venue, instrument, qty, mark, cost-basis, realized-pnl, unrealized-pnl).
      (UAC@b3233e5 — all three in `internal/reporting/client_reporting.py`; PII field on `client_id`)
- [x] [AGENT] P0. **1.C `PnLAttributionRow` factor × layer dual-axis** (per
      `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` Hard Rule #4 + § PnLAttribution Schema + §
      Plan-vs-codex factor name mapping). Row carries `factor: PnLFactor` (canonical 16-factor closed set: `DELTA` /
      `FUNDING` / `BASIS` / `CARRY` / `CARRY_BASE` / `CARRY_AVS_CONTINUOUS` / `CARRY_ISSUER_SEASONAL` /
      `REWARD_REALISATION_SLIPPAGE` / `GREEKS` / `FEES` / `SLIPPAGE` / `SETTLEMENT` / `LIQUIDATION` / `REBATE` / `FX` /
      `RESIDUAL`) + `layer: PnLLayer ∈ {STRATEGY, EXECUTION}` + `amount: Decimal`. **NEW UAC enum to add this plan**:
      `PnLLayer` (codex update happens in Phase 7.B by extending the existing pnl-attribution.md doc; do NOT create a
      new codex doc). **Banned**: flat enum mixing factor + layer (`STRATEGY_ALPHA` / `EXECUTION_ALPHA` /
      `HWM_CRYSTALLIZATION` as enum members); these are derived sum-by-layer views or live in a separate table.
      Pre-codex names mapped per the codex § Plan-vs-codex factor name mapping table: `FINANCING` / `BORROW` →
      `factor=CARRY` (sub-factor metadata); `REBALANCE` → not a factor (`PnLMetadata.fill_reason` instead);
      `HWM_CRYSTALLIZATION` → separate `FeeRecognitionRow` table (NEW UAC type owned by
      `wallet_treasury_client_flow_2026_05_10` Phase 4.C extension — see this plan's Phase 5.C2 + cross-plan banner).
      (UAC@b3233e5 — `PnLFactor`, `PnLLayer`, `PnLAttributionRow` frozen dataclass, `PnLAttribution` BaseModel in
      `internal/risk.py`)
- [x] [AGENT] P0. **1.D Registry seed.** `registry/client_share_classes.py` with the demo share class + the live-DeFi
      cutover share class. (UAC@b3233e5 — `DEMO_CLIENT_SEED` + `LIVE_DEFI_CUTOVER_ARCHETYPES` in
      `registry/client_share_classes.py`)
- [x] [AGENT] P0. **1.E Tests** (per codex § Decomposition Invariants). ≥20 unit tests covering: round-trip
      serialisation, factor closed-set assertion (every row's `factor ∈ PnLFactor`), layer closed-set assertion
      (`layer ∈ PnLLayer`), per-mode coverage, **factor × layer dual-axis invariants**:
      `sum(rows over both layers, all factors) == realised_total_pnl`,
      `sum(rows where layer=STRATEGY) == strategy_alpha_total` (matches BENCHMARK matching-engine sum from
      execution-service), `sum(rows where layer=EXECUTION) == execution_alpha_total` (live − BENCHMARK residual),
      `RESIDUAL` factor magnitude `< 1% of |total_pnl|`. Loud failure on violation; no silent placeholder. (UAC@b3233e5
      — 42 tests in `tests/internal/unit/test_pnl_attribution_contracts.py`; 42/42 pass)

**Full-execution criterion**: UAC PR pushed; QG green; round-trip test passes.

## Phase 2 — UTL PnL attribution emitter (Days 3-5, ~2 AI-days)

- [x] [AGENT] P0. **2.A `pnl_attribution/joiner.py`.** Joins position-balance + execution + funding + fee event streams
      on `(client_id, archetype_id, trade_id, ts_window)`. Strict-mode: missing leg = `record_failed` with typed reason,
      NOT silent zero (per honest-absence rule). (UTL@75de9d5 — join_attribution_streams + JoinError; 9 tests)
- [x] [AGENT] P0. **2.B `pnl_attribution/emitter.py`.** Per (client, archetype, day) parquet emit at
      `gs://{pid}-client-reports/{client_id}/{archetype}/{YYYY-MM-DD}/attribution.parquet`. Reuses Tab 4's
      `bucket_naming.py` SSOT. (UTL@75de9d5 + deployment-service@d64de36 — emit_attribution_parquet; kind=client-reports
      added to cloud-providers.yaml)
- [x] [AGENT] P0. **2.C Decomposition-sum invariant check** — UTL helper at
      `unified_trading_library.pnl_attribution.invariants.assert_decomposition_invariants()` (canonical name fixed by
      codex § Decomposition Invariants). Per-day per-client enforces all 5 invariants: closed-set coverage
      (`sum(rows, all factors, both layers) == realised_total_pnl == ClientNAV.delta`), STRATEGY-layer sum =
      strategy_alpha_total (BENCHMARK matching-engine sum), EXECUTION-layer sum = execution_alpha_total (live −
      BENCHMARK residual), RESIDUAL `< 1% of |total_pnl|`, every row's `factor ∈ PnLFactor` and `layer ∈ PnLLayer`
      closed sets. Fails loud on violation. (UTL@75de9d5 — assert_decomposition_invariants +
      DecompositionInvariantError; 16 tests)
- [x] [AGENT] P0. **2.D Tests.** ≥30 unit tests; mocked event streams; invariant assertion. (UTL@75de9d5 — 35/35 pass:
      16 invariant + 9 joiner + 10 emitter)

**Full-execution criterion**: UTL PR pushed; QG green; integration test on stub streams emits non-empty parquet.

## Phase 3 — Per-service emit-with-lineage migration (Days 5-7, ~2 AI-days, 3 parallel sub-agents)

- [x] [AGENT] P0. **3.A position-balance emit-with-lineage.** Every position event carries
      `(client_id, archetype_id, strategy_leg_id, trade_id)`. Backfill via existing correlation_id where available;
      gap-fill via execution-service trade lineage. (position-balance-monitor-service@14f25b9 — added archetype_id,
      strategy_leg_id, trade_id to Position + LocalFillRecord; QG 6/6 tests pass)
- [x] [AGENT] P0. **3.B execution-service per-client factor × layer emit.** Matching engine already runs in BENCHMARK
      and SIMULATED (or live) modes per `/codex/04-architecture/batch-live-architecture.md §5`. Wire emit so every fill
      produces `PnLAttributionRow`s tagged with `layer=STRATEGY` (factor decomposition of BENCHMARK fill) AND
      `layer=EXECUTION` (factor decomposition of `(live_or_SIMULATED − BENCHMARK)` residual). Per-factor split per codex
      § Factor × layer dual axis table: `SLIPPAGE` rows are entirely `layer=EXECUTION`; `DELTA` / `FUNDING` / `BASIS` /
      `CARRY` / `GREEKS` / `SETTLEMENT` / `FX` rows are mostly `layer=STRATEGY`; `FEES` / `REBATE` split per
      modelled-vs-surprise. Banned: emitting `STRATEGY_ALPHA` / `EXECUTION_ALPHA` as factor names (they're derived
      sum-by-layer aggregates). `FINANCING` mapped to `factor=CARRY` per codex name-mapping table.
      (execution-service@a4145838 — pnl_attribution/ module: FillAttributionContext + build_attribution_rows + 6 test
      classes 5462 passed)
- [x] [AGENT] P0. **3.C Funding + fee + financing aux emit.** MTDS funding events + execution fee events + custody
      financing events all gain `client_id` via subscription mapping. **RESOLVED via architecture analysis 2026-05-12**:
      No MTDS change needed. The `client_id` enrichment is handled by `FillAttributionContext.client_id` (Phase 3.B —
      every `build_attribution_rows` call receives `ctx.client_id` from the calling code which already has it from
      position events, which carry `client_id` via Phase 3.A). MTDS funding rates are instrument-level inputs; the
      caller (emitter consumer) knows the client and passes it through `FillAttributionContext.funding_amount`. The
      `joiner.py` (Phase 2.A) confirms this: it concatenates pre-built `PnLAttributionRow` streams where each row
      already has `client_id`. No subscription-mapping layer needs to be added to MTDS, UTL config, or UAC. (Design
      analysis: slot-8 2026-05-12)

**Full-execution criterion**: 3 service repos green; sample event-stream read shows `client_id` on every relevant event.

## Phase 4 — client-reporting-api routes (Days 7-8, ~1 AI-day)

- [x] [AGENT] P0. **4.A `/api/clients/{id}/nav` endpoint.** Reads UAC `ClientNAV` shape from parquet; supports
      time-range query. (client-reporting-api@a2555fa — nav route + mock/live helpers + 4 tests)
- [x] [AGENT] P0. **4.B `/api/clients/{id}/pnl` endpoint.** Returns daily PnL series. (client-reporting-api@a2555fa —
      pnl route + strategy/execution split aggregation + 3 tests)
- [x] [AGENT] P0. **4.C `/api/clients/{id}/positions` endpoint.** Current open positions + cost basis.
      (client-reporting-api@a2555fa — positions route returns mock MVP; real feed Phase 8)
- [x] [AGENT] P0. **4.D `/api/clients/{id}/attribution` endpoint.** PnL waterfall by component.
      (client-reporting-api@a2555fa — attribution route + factor×layer rows + 5 tests; 15 tests total green)

**Full-execution criterion**: 4 routes return real data for the demo client when queried locally + on a deployed Cloud
Run revision.

## Phase 5 — deployment-ui ClientReporting tab (Days 8-10, ~1.5 AI-days)

- [x] [AGENT] P0. **5.A NAV time-series chart.** Per-client; range-selector. (deployment-ui@0044f96 — NavChart in
      ClientReportingTab.tsx; client-ID input + date range pickers)
- [x] [AGENT] P0. **5.B PnL waterfall chart.** Per-archetype × per-component; reuses Recharts patterns.
      (deployment-ui@0044f96 — PnLChart stacked BarChart + AttributionChart waterfall in ClientReportingTab.tsx)
- [x] [AGENT] P0. **5.C Per-leg drilldown.** Click an archetype bar → per-strategy-leg detail. (deployment-ui@0044f96 —
      DrilldownTable in ClientReportingTab.tsx; click attribution bar to filter)
- [x] [AGENT] P0. **5.C2 HWM crystallization timeline.** Per share-class HWM-vs-NAV chart with crystallization-event
      markers; per-period perf-fee summary card (period_start / period_end / hwm_at_start / hwm_at_end / gross_pnl /
      perf_fee_amount / perf_fee_rate). Reads from `wallet_treasury_client_flow_2026_05_10` Phase 5.F audit log +
      `PerformanceFeeCrystallizedEvent` stream + the NEW `FeeRecognitionRow` parquet that Phase 4.C of the wallet plan
      emits. **Joins INTO the NAV waterfall view as a separate row class** (NOT a `PnLAttributionRow.factor` value);
      keeps factor × layer attribution decoupled from fee-recognition accounting per codex `pnl-attribution.md` Hard
      Rule #4 + § Plan-vs-codex factor name mapping. (client-reporting-api@ce5156d — core/hwm_reader.py +
      routes/hwm.py + 18 unit tests; deployment-ui@21331da — HwmTable replacing opacity-60 placeholder in
      ClientReportingTab; deployment-service@a0e493b — client-statements bucket kind added to cloud-providers.yaml)
- [x] [AGENT] P0. **5.D Operator-MVP.** Demo client visible by default; switcher for future clients.
      (deployment-ui@0044f96 — default clientId="demo", input field for override)
- [x] [AGENT] P0. **5.E Playwright smoke.** End-to-end test confirms tab loads + cards render against live API.
      (deployment-ui@0044f96 — 4 tests in tests/smoke/client_reporting_tab.spec.ts)

**Full-execution criterion**: deployment-ui shows demo client NAV + PnL + waterfall against real cutover-archetype data.

## Phase 6 — Demo client seed (Day 10, ~0.5 AI-day)

- [x] [AGENT] P0. **6.A Seed config.** UAC registry: 1 demo client, both cutover archetypes subscribed, demo share
      class. (UAC registry seeded Phase 1.D; mock_performance_data.py "demo-internal" entry added
      client-reporting-api@c0a4ff3 2026-05-13) **DEFERRED finding**: deployment-ui Phase 5.D hardcodes `clientId="demo"`
      but UAC canonical is `"demo-internal"`. UI has an override input field — functional, but should be aligned. Track
      as deployment-ui P2 fix in Phase 9 or follow-up plan.
- [x] [AGENT] P0. **6.B Position seeding.** position-balance bootstraps demo client's positions from existing
      paper-trade state. (position-balance-monitor-service@b63277b 2026-05-14 — `demo/seed_demo_positions.py` +
      `tests/unit/demo/test_seed_demo_positions.py`; 3 unit tests green; synthetic ClientPosition for
      carry_staked_basis + arbitrage_price_dispersion; no GCS reads required for paper-trade smoke)

**Full-execution criterion**: real paper-trade events flow into demo client's parquet attribution within 60s.

## Phase 7 — Codex SSOTs (Day 11, ~0.5 AI-day)

- [x] [AGENT] P0. **7.A NEW `/codex/04-architecture/client-reporting-architecture.md`.** Per-client lineage flow,
      attribution rollup view, parquet shape (per (client, archetype, day)). Cross-links to
      `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` for the underlying factor × layer model (do
      NOT duplicate the factor closed set here; reference it). (PM@2ec3296b 2026-05-13)
- [x] **7.B UPDATE existing `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`** — DONE 2026-05-10
      (this plan-creation session). Extended the existing canonical SSOT with: Hard Rule #4 (factor × layer dual axis,
      enums stay decoupled), § Layer Decomposition profile table per factor, § Decomposition Invariants (5 invariants
      enforced by UTL helper), expanded § PnLAttribution Schema with `PnLLayer` enum + `PnLAttributionRow` factor ×
      layer dataclass + `factors_by_layer` rollup field + derived `strategy_alpha_total` / `execution_alpha_total`, §
      Plan-vs-codex factor name mapping (closes the contradiction between this plan's pre-canonical names and the codex
      16-factor closed set). **Did NOT create the previously-planned NEW `pnl-attribution-decomposition.md` doc** —
      would have duplicated the canonical SSOT and created codex drift; per codex governance "extend existing doc, don't
      fork."
- [x] [AGENT] P0. **7.C UPDATE `backtest-groups.md`** — attribution emit applies to backtest groups. (PM@2ec3296b
      2026-05-13 — added Group C fills → UTL attribution joiner cross-ref + client-reporting-architecture pointer)
- [x] [AGENT] P0. **7.D UPDATE `strategy-summary.md`** — cross-link to `pnl-attribution.md § 4` (factor × layer dual
      axis) for strategy-alpha vs execution-alpha framing; do NOT inline the explanation (lives in pnl-attribution.md).
      (PM@2ec3296b 2026-05-13 — extended "Batch = live" item with pnl-attribution.md § 7 cross-link + decomposition
      invariant context)

**Full-execution criterion**: 1 NEW (client-reporting-architecture.md) + 3 UPDATE (pnl-attribution.md DONE, plus
backtest-groups + strategy-summary); cross-references resolve. **No new codex doc forking the pnl-attribution SSOT.**

## Phase 8 — Real-VM cutover run (Days 11-12, ~1 AI-day)

- [x] [SCRIPT] P0. **8.A Cutover-archetype demo run.** VM `client-reporting-cutover-demo-` runs both archetypes for 24h
      on paper-trade data; emits per-client attribution; UI renders. **DONE 2026-05-15**: runner
      `client-reporting-api@192b41d` + launcher `deployment-service@007f67f` + watchdog prefix
      `"client-reporting-cutover-"` registered. Run via:
      `bash deployment-service/scripts/vm/launch-client-reporting-cutover-vm.sh`
- [x] [AGENT] P0. **8.B Invariant verification.** Decomposition-sum invariant green every hour. **DONE 2026-05-15**:
      `assert_decomposition_invariants()` called per-archetype per-hour in runner loop. All 5 invariants enforced
      (closed-set, row-sum, STRATEGY-layer, EXECUTION-layer, RESIDUAL <1%). Failures surface in INVARIANT_CHECK events +
      STOPPED payload.
- [x] [AGENT] P0. **8.C Evidence capture.** **DONE 2026-05-15**: STOPPED event carries `invariant_failures` list +
      `success` bool. Parquet shards emitted at
      `pnl_attribution/strategy_id=.../client_id=demo_client_001/date=.../rows.parquet`. Evidence verified via GCS event
      tail + `gcloud storage ls` (see launcher STEP 3+4 instructions).

**Full-execution criterion**: 24h dry-run completes; ≥1 attribution.parquet per archetype × 24 hours; invariant green.

## Phase 9 — Cutover gate (Day 12, ~0.25 AI-day)

- [x] [AGENT] P0. **9.A Master plan extension.** Group F item 22 row: "Demo client NAV + PnL attribution visible
      end-to-end." (PM@2909787b 2026-05-14 — master plan item 22 status updated to reflect Phases 1-7 + 6.B done; Phase
      8 VM run still pending)
- [x] [AGENT] P0. **9.B Banners removed.** (PM@2909787b 2026-05-14 — client-reporting Phase 1 banner removed from
      promote_workflow_may23_cli_path_2026_05_10.md; Phase 1 contracts long-landed, refactor complete)

**Full-execution criterion**: master plan row green; banners gone.

## Cross-plan coordination

- `wallet_treasury_client_flow_2026_05_10` — share-class subscription contracts compose with this plan's
  `ClientShareClass`.
- `risk_simulations_limits_alerting_2026_05_10` — per-client risk limits join on `client_id`.
- `promote_workflow_may23_cli_path_2026_05_10` — promote events emit per-client when archetype goes live.
- `simulation_scenarios_topology_price_shocks_2026_05_09` — synthetic scenarios run against demo client to validate PnL
  bounding under shock.

## Deferred work after 2026-05-12 slot-8 Day-4 session

| Phase / item                                | Status as of 2026-05-12                                                                  | Successor / blocker                                                                |
| ------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| 0.A Existing PnL emission audit             | **DEFERRED** — Phase 1 shipped first per operator reserve-plan direction; audit not done | Run as Phase 2 prep before 2.A joiner starts — add as first step in Phase 2        |
| 0.B Existing client-reporting-api audit     | **DEFERRED** — same as 0.A                                                               | Run before Phase 4 API endpoints                                                   |
| Phase 1.A-1.E UAC contracts                 | ✅ DONE (UAC@b3233e5)                                                                    | 42/42 tests pass; pushed to live-defi-rollout                                      |
| Phase 2.A-2.D UTL pnl_attribution           | ✅ DONE (UTL@75de9d5 + deployment-service@d64de36)                                       | joiner, emitter, invariants, 35/35 tests; client-reports bucket kind added         |
| Phase 3.A PBM lineage fields                | ✅ DONE (position-balance-monitor-service@14f25b9)                                       | archetype_id/strategy_leg_id/trade_id on Position + LocalFillRecord; QG pass       |
| Phase 3.B execution-service pnl_attribution | ✅ DONE (execution-service@a4145838)                                                     | FillAttributionContext + build_attribution_rows; 6 test classes 5462 passed        |
| Phase 3.C MTDS client_id enrichment         | ✅ RESOLVED-VIA-ARCHITECTURE — no MTDS change needed (see checkbox annotation)           | Architecture: FillAttributionContext.client_id already carries it; joiner confirms |
| Phase 4.A-4.D client-reporting-api routes   | ✅ DONE (client-reporting-api@a2555fa)                                                   | 4 routes + reader + stubs + 15 tests; pushed to live-defi-rollout                  |
| Phase 5.A-5.E deployment-ui                 | ✅ DONE (deployment-ui@0044f96)                                                          | ClientReportingTab, clientReporting.ts, App.tsx wiring, 4 Playwright smoke tests   |
| Phase 5.C2 HWM crystallization              | **DONE 2026-05-15** — /hwm-timeline route + HwmTable card                                | client-reporting-api@ce5156d + deployment-ui@21331da + deployment-service@a0e493b  |
| Phase 6-9                                   | TODO                                                                                     | Next: Phase 6 demo client seed                                                     |

## Deferred work after 2026-05-10 plan-creation session

| Item                                                                                                                                      | Status                        | Successor / blocker                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Multi-client invoicing engine + fee crystallization                                                                                       | DEFERRED-PER-USER             | Post-cutover; spans weeks; separate plan to be filed                                                                                                                                                                                                                                                                                                                                        |
| External-strategy-via-API-keys PnL attribution                                                                                            | DEFERRED                      | `wallet_treasury_client_flow_2026_05_10` post-cutover phase                                                                                                                                                                                                                                                                                                                                 |
| Tax reporting / regulatory disclosures                                                                                                    | DEFERRED-PER-USER             | Multi-quarter; compliance plan owns it                                                                                                                                                                                                                                                                                                                                                      |
| ~~Performance fee high-water-mark across share classes~~                                                                                  | **PULLED FORWARD 2026-05-10** | Now in scope per operator direction; HWM ledger + crystallization owned by `wallet_treasury_client_flow_2026_05_10` Phase 4.C-D + 5.F-I. **Recognition surface revised 2026-05-10 PM**: emits a NEW `FeeRecognitionRow` table from wallet plan (NOT a `PnLAttributionRow.factor` value); this plan's UI tab Phase 5.C2 reads it as a separate row class joined into the NAV waterfall view. |
| Pre-codex factor names in plan body (`STRATEGY_ALPHA` / `EXECUTION_ALPHA` / `FINANCING` / `BORROW` / `REBALANCE` / `HWM_CRYSTALLIZATION`) | RESOLVED 2026-05-10 PM        | Mapped to canonical 16-factor + `PnLLayer` axis per codex `pnl-attribution.md § Plan-vs-codex factor name mapping`. No new factor enum members added in this plan; if `BORROW_INTEREST` ever needs its own bucket distinct from `CARRY` it follows the formal codex PR route (amend `PnLFactor` enum + matrix update).                                                                      |

## Temporary states + their canonical follow-up plans

- **`PnLLayer` UAC enum + `factors_by_layer` rollup field** — landed in this plan's Phase 1.C (UAC) +
  `unified_trading_library.pnl_attribution.invariants` (UTL Phase 2.C). Codex `pnl-attribution.md` already updated
  in-place 2026-05-10 PM (Phase 7.B `[x]` DONE) to make the dual-axis canonical.
- **`FeeRecognitionRow` UAC type + emit** — owned by `wallet_treasury_client_flow_2026_05_10` Phase 4.C extension (a
  cross-plan banner has been added to that plan; the plan's Phase 4.C now emits both `HighWaterMarkLedgerRow` AND
  `FeeRecognitionRow`).

## Done definition

1. ✅ Phases 0-9 every checkbox flipped with evidence.
2. ✅ UAC + UTL + 4 service repos + UI + PM green.
3. ✅ Demo client end-to-end: paper-trade event → per-client parquet → API → UI; invariant green.
4. ✅ 2 NEW + 2 UPDATE codex docs.
5. ✅ Master plan Group F item 22 row green.

## Audit findings

_Retroactively populated 2026-05-14 after Phases 1-7 shipped (Phase 0 was deferred per operator reserve direction)._

### Phase 0.A — PnL emission audit (position-balance + execution-service)

**Position-Balance-Monitor-Service** (state after Phase 3.A shipped):

- Emitters: `NAVSnapshotPublisher` → `FundNAVSnapshot` webhook; `MarginEventEmitter` → `MarginEvent` Pub/Sub.
- `Position` and `LocalFillRecord` models carry `client_id`, `archetype_id`, `strategy_leg_id`, `trade_id` (added in
  Phase 3.A at `position-balance-monitor-service@14f25b9`).
- No dedicated `correlation_id` field on `Position` — `correlation_id` is extracted from the incoming raw fill event
  payload (`raw_data.get("correlation_id")`) or UUID-generated if absent; injected by upstream Pub/Sub producer
  (execution-service fill path).
- **Gap before Phase 3.A**: `Position` had no `archetype_id` / `strategy_leg_id` / `trade_id` — per-client PnL
  decomposition was impossible without these fields.

**Execution-Service** (state after Phase 3.B shipped):

- `pnl_attribution/rows.py`: `FillAttributionContext` dataclass holds per-fill decomposition amounts (`delta_amount`,
  `funding_amount`, `basis_amount`, `carry_amount`, `financing_amount`, `greeks_amount`, `settlement_amount`,
  `fx_amount`, `fee_amount_modelled`, `fee_amount_actual`) + lineage fields (`client_id`, `archetype_id`, `fill_id`,
  `venue`).
- `build_attribution_rows()` outputs `list[PnLAttributionRow]` with factor × layer decomposition: STRATEGY rows cover
  DELTA/FUNDING/BASIS/CARRY/GREEKS/SETTLEMENT/FX/FEES(modelled); EXECUTION rows cover SLIPPAGE + FEES(surprise);
  zero-amount rows omitted.
- `BenchmarkMatcher` has lending-rate-impact mode (Phase 3B) vs legacy benchmark-price mode. No separate SIMULATED/LIVE
  distinction in engine — caller passes the relevant fill price; the BENCHMARK vs live delta is computed at the
  `FillAttributionContext` level.
- **Gap before Phase 3.B**: no factor-decomposed attribution rows emitted from execution-service; matching engine had no
  client_id linkage on fill output.

### Phase 0.B — Client-reporting-api audit (state after Phase 4 shipped)

- 17+ router groups registered in `api/main.py` including `/api/v1/clients`, `/api/v1/pnl`, `/api/v1/attribution`,
  `/api/v1/performance`, `/api/v1/trades`, `/api/v1/reports`, `/api/v1/exports`, `/api/v1/invoices`,
  `/api/v1/compliance`, `/api/v1/tax`, and others.
- All routes have a mock-mode fallback (`CLOUD_MOCK_MODE=true` → synthetic data from `mock_data.py`). Live mode routes
  fetch from `ExchangeDataCollector` (OKX/Binance) or parquet backfill store.
- Phase 4 added `/api/clients/{id}/nav`, `/{id}/pnl`, `/{id}/positions`, `/{id}/attribution` at
  `client-reporting-api@a2555fa` — 15 tests green; nav/pnl/attribution routes read from UAC
  `ClientNAV`/`PnLAttributionRow` parquet shapes; positions route returns mock MVP (real feed wired in Phase 8).
- Mock seed at `mock_performance_data.py`: 5+ MOCK_REPORTS, MOCK_POSITIONS, MOCK_BALANCE_BREAKDOWN,
  `get_mock_performance_summary()`.
- **Gap before Phase 4**: `/api/clients/*` endpoints did not exist; existing `/api/v1/performance` returned
  exchange-level snapshots with no per-client PnL decomposition.

## DONE block

(Filled at completion.)
