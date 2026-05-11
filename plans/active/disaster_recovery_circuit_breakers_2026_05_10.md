---
title: Disaster recovery + reconciliation + circuit breakers + kill switches — cutover-MVP
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to:
  master_to_live_defi_2026_05_23.md (Group F item 20 circuit breakers + kill switches + alerting + auto-recovery, item
  21 batch-vs-live reconciliation)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/active/risk_simulations_limits_alerting_2026_05_10.md
  - plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md
  - plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md
  - plans/active/defi_catalogue_chain_primitives_2026_05_10.md
  - plans/active/defi_simulation_realism_2026_05_10.md
related_codex:
  - codex/04-architecture/kill-switch-circuit-breaker.md
  - codex/04-architecture/autonomous-recovery-matrix.md
  - codex/04-architecture/mev-protection.md
  - codex/03-observability/alerting.md
  - codex/04-architecture/capital-efficiency-patterns.md
---

# Disaster recovery + reconciliation + circuit breakers + kill switches — cutover-MVP

> **🟡 IN-FLIGHT REFACTOR — § 7 SSOT reconciliation seam mandate adopted 2026-05-10 PM.** This plan touches the same 5
> canonical risk SSOTs as
> [`risk_simulations_limits_alerting_2026_05_10.md:44-81`](risk_simulations_limits_alerting_2026_05_10.md) (kill-switch
> taxonomy / 8-event lifecycle / circuit-breaker / alerting rules / strategy kill-switch behaviour). Per the risk plan's
> § 7 mandate, every Phase 1 Pydantic class docstring in this plan MUST include a "§ 7 SSOT reconciliation" subsection
> identifying which of the 5 SSOTs the class composes with + how the seam is preserved. Reviewer rejects Phase 1 PRs
> that omit it.
>
> **🟡 CROSS-PLAN BANNER — Risk plan Phase 1 active (UAC@945ad5d landed 2026-05-11).** Phase 0+1+2.G of
> [`risk_simulations_limits_alerting_2026_05_10`](./risk_simulations_limits_alerting_2026_05_10.md) shipped the
> `RiskRuleId` / `RiskRuleScope` / `RiskRuleConsequence` enums + `RiskRule` Pydantic + `StrategyFamilyId` registry + 6
> new `AlertCode` members (closed-set 39 → 45). **Coordinate ownership** of `BreakerRecoveryMode` +
> `BREAKER_RECOVERY_DEFAULTS` (this plan's Phase 1.A) — the risk plan's Phase 1.F flip is a cross-reference to that
> work; do NOT duplicate the enum + dict in `risk_rule.py`. Sub-A's `event_pattern` rename also landed
> (UAC@0b61aec) — all new `AlertRule` entries MUST use `event_pattern=`, never legacy `pattern=`.
>
> **🟢 CROSS-PLAN COORDINATION — Phase 7.B kill-switch tab vs `deployment_ui_lifecycle_tabs_2026_05_08.md` 6-tab
> shell.** Phase 7.B below ships a NEW deployment-ui kill-switch tab. The lifecycle plan
> ([`deployment_ui_lifecycle_tabs_2026_05_08.md:152-160`](deployment_ui_lifecycle_tabs_2026_05_08.md)) currently
> declares a 6-tab shell (Deploy / Monitor / Data Status / Builds / Readiness / Config). Decision 2026-05-10 PM:
> kill-switch lands as the **7th lifecycle-managed tab** (NOT folded into Monitor — kill-switches are safety-critical
> and need top-level visibility per CLAUDE.md "Service Infrastructure Requirements"). The lifecycle plan's Phase B.1
> table will be revised to 7 tabs when this plan's Phase 7.B ships; sequencing handled in lifecycle plan's cross-plan
> coordination banner. Until then both plans hold their scope; no other consumer of either plan is blocked.

## Why this plan exists

May-23 cutover gates on Group F item 20 (circuit breakers + kill switches + alerting + auto-recovery) + item 21
(batch-vs-live reconciliation). Today scattered pieces exist (UTL `batch_live_reconciler` shipped Tab 2 2026-05-08;
alerting-service rules plan in flight; matching engine has internal aborts) but no unified taxonomy + matrix +
kill-switch event bus + per-state-surface reconciler suite. This plan ships the cutover-MVP: every state surface has a
reconciler, every named circuit breaker has a typed event + auto-recovery rule, kill-switch arming is an
event-bus-driven action with provenance, and a chaos-drill cron runs nightly. Multi-week DR drills + cross-region
failover beyond cutover archetypes are deferred post-cutover.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. UAC circuit-breaker rule taxonomy: `CircuitBreakerId`, `BreakerScope` (per-venue / per-archetype / per-account /
   per-asset_group / global), `BreakerTrigger` (typed conditions), `BreakerAction` (BLOCK_NEW / CANCEL_OPEN / SCALE_DOWN
   / KILL_ALL), `BreakerRecoveryRule`.
2. UAC kill-switch event taxonomy: `KillSwitchId`, `KillSwitchArmRequest`, `KillSwitchArmedEvent`,
   `KillSwitchDisarmEvent`. Provenance closed enum (operator / breaker / scenario / scheduled).
3. UTL kill-switch event bus: `KillSwitchBus.arm/disarm` + per-service consumer subscription pattern.
4. Per-state-surface reconcilers (cutover-scope): positions / balances / custody / on-chain / events / manifest /
   order-state / PnL / clock / batch-vs-live (the last extends UTL@908b1647).
5. Auto-recovery rules per breaker: declared as `BreakerRecoveryRule` with named guard + retry policy.
6. Chaos-drill cron VM: nightly runs a representative subset of `simulation_scenarios_topology_price_shocks_2026_05_09`
   scenarios that exercise breakers + recovery; reports green/red.
7. Codex SSOTs: 2 NEW + 3 UPDATE.
8. Real-VM cutover-archetype DR drill green.

### Non-goals (post-cutover)

- Cross-region failover (AWS↔GCP active-active) beyond catalogue declaration — post-cutover ops plan.
- Full multi-week chaos-drill cadence (weekly / monthly drills) — cutover ships nightly minimum, full cadence post.
- Recovery playbooks for non-cutover venues / chains — covered as scenarios are added post-cutover.

## Pre-audit / blast radius

| Repo                               | Surface                                                                            |
| ---------------------------------- | ---------------------------------------------------------------------------------- |
| `unified-api-contracts`            | NEW: `canonical/crosscutting/circuit_breaker.py`, `kill_switch.py`; registry seeds |
| `unified-trading-library`          | NEW: `kill_switch/bus.py`; reconciler suite under `reconcile/`                     |
| `risk-and-exposure-service`        | UPDATE: every breaker fires the typed event; recovery rule consumed                |
| `execution-service`                | UPDATE: matching engine subscribes to kill-switch bus; cancel-on-arm wired         |
| `position-balance-monitor-service` | UPDATE: reconcilers consume position events; per-surface diff emit                 |
| `alerting-service`                 | UPDATE: breaker + kill-switch events route to severity tier                        |
| `deployment-api` + `deployment-ui` | NEW: kill-switch arm/disarm UI; reconciler dashboard                               |
| `unified-trading-pm`               | NEW + UPDATE codex docs                                                            |

## Phased execution DAG

```text
0 (pre-audit, parallel) → 1 (UAC breaker + kill-switch taxonomy) → 2 (UTL kill-switch bus) → 3 (per-state-surface reconcilers, parallel)
→ 4 (per-service breaker + bus integration, parallel) → 5 (auto-recovery rules) → 6 (chaos-drill cron) →
7 (deployment-api+ui kill-switch surface) → 8 (codex SSOTs) → 9 (real-VM DR drill) → 10 (cutover gate)
```

## Phase 0 — Pre-audit (Day 1, ~1 AI-day, 4 parallel sub-agents)

- [x] [AGENT] P0. **0.A Existing breaker audit.** Walk risk-and-exposure-service + execution-service + alerting-service
      for every existing breaker / abort condition; classify per scope. Shipped 2026-05-11 by Sub-C; findings in
      § Audit findings (execution-service has a 3+1-state per-venue CB + DEGRADED extension; risk-and-exposure-service
      has the kill-switch decision engine; alerting-service has the notifier path). UAC@a7a99b5.
- [x] [AGENT] P0. **0.B Reconciler audit.** UTL `batch_live_reconciler.py` shipped Tab 2 2026-05-08 (covers
      batch-vs-live). No per-state-surface reconcilers exist for positions / balances / custody / on-chain / events /
      manifest / order-state / PnL / clock — full gap. Phase 3 covers.
- [x] [AGENT] P0. **0.C Kill-switch audit.** UTL `kill_switch/bus.py` (KillSwitchBus singleton, scope-keyed
      arm/disarm, in-process pub-sub) ALREADY EXISTS at HEAD — predates this plan. Phase 2's "UTL kill-switch bus"
      scope reduces to: typed UAC event taxonomy adoption (UAC@a7a99b5), audit-log persistence (Phase 2.A),
      cross-process transport adapter (Phase 2 stretch, post-cutover OK).
- [x] [SCRIPT] P0. **0.D Banners on cross-plan files.** Master plan + alerting plan + risk plan already carry
      cross-references via Q8 + Q9 ratification 2026-05-10. Operator-side surface landed via the ratification commit
      chain. No additional banner pass needed for Phase 0.

**Full-execution criterion**: § Audit findings populated; banners on 4 plans.

## Phase 1 — UAC breaker + kill-switch taxonomy (Days 2-4, ~2 AI-days)

- [x] [AGENT] P0. **1.A `CircuitBreakerId` + `BreakerScope` + `BreakerTrigger` + `BreakerAction` enums.** Closed sets.
      Shipped UAC@a7a99b5 (`canonical/crosscutting/circuit_breaker.py`) with `BreakerRecoveryMode` closed enum +
      `BREAKER_RECOVERY_DEFAULTS` SSOT per Q8 ratification. Every Pydantic class docstring cites the § 7 SSOT
      reconciliation seam per risk-plan mandate.
- [x] [AGENT] P0. **1.B Per-archetype breaker registry seed.** Shipped UAC@a7a99b5
      (`registry/circuit_breakers/carry_staked_basis.py` + `arbitrage_price_dispersion.py`). 10 `BreakerConfig` +
      10 `BreakerRecoveryRule` per archetype = 20 breakers × 20 recovery rules registered.
- [x] [AGENT] P0. **1.C `KillSwitchId` registry.** Shipped UAC@a7a99b5 (`canonical/crosscutting/kill_switch.py`)
      with `KILL_ALL_LIVE` + 2 cutover archetypes + 6 perp venues (Bybit/Deribit/Binance/OKX/Hyperliquid/Aster) + 2
      asset groups (cefi/defi).
- [x] [AGENT] P0. **1.D Provenance closed enum.** Shipped UAC@a7a99b5
      `KillSwitchProvenance ∈ {OPERATOR_MANUAL, BREAKER_AUTO, SCENARIO_SYNTHETIC, SCHEDULED_DRILL}`. Plus
      `KillSwitchArmRequest` + `KillSwitchArmedEvent` + `KillSwitchDisarmEvent` Pydantic models with
      `recovery_mode` + `cooldown_seconds_elapsed` fields.
- [x] [AGENT] P0. **1.E `BreakerRecoveryRule` Pydantic.** Shipped UAC@a7a99b5
      (`canonical/crosscutting/circuit_breaker.BreakerRecoveryRule`) — `(breaker_id, guard_description,
      retry_policy ∈ {exponential|linear|none}, auto_disarm_after_seconds)`. Frozen + extra-forbid.
- [x] [AGENT] P0. **1.F Tests.** Shipped UAC@dc4c9f0 (after autofmt absorbed test files):
      `tests/internal/unit/test_circuit_breaker_taxonomy.py` (38 tests) +
      `tests/internal/unit/test_kill_switch.py` (23 tests) = **61 unit tests total**, all passing locally. Closed-set
      sanity, validator semantics, default-fill, per-archetype registry coverage, KILL_ALL → no auto-disarm
      invariant, § 7 seam citation enforcement, facade re-export verification.

**Full-execution criterion**: UAC PR pushed; QG green; ≥10 breakers × 2 archetypes registered. UAC@a7a99b5 +
UAC@dc4c9f0 landed; 20 breakers + 20 recovery rules + 11 kill-switch IDs + 4 provenances + 61 tests.

## Phase 2 — UTL kill-switch bus (Days 4-5, ~1 AI-day)

- [ ] [AGENT] P0. **2.A `unified_trading_library/kill_switch/bus.py`.** `KillSwitchBus` with
      `arm(switch_id, provenance, metadata)` + `disarm` + `subscribe(callback)`. Backed by Redis Stream + parquet audit
      log.
- [ ] [AGENT] P0. **2.B Subscriber pattern.** `KillSwitchSubscriber` base class; per-service callback.
- [ ] [AGENT] P0. **2.C Tests.** ≥20 unit tests; arm-disarm idempotency; multi-subscriber broadcast; audit-log
      persistence.

**Full-execution criterion**: UTL PR pushed; QG green; integration test arms+disarms across 3 stub subscribers.

## Phase 3 — Per-state-surface reconcilers (Days 5-8, ~3 AI-days, 8 parallel sub-agents)

- [ ] [AGENT] P0. **3.A Position reconciler.** Diffs position-balance state vs venue REST + custody endpoint. Drift >
      tolerance fires breaker.
- [ ] [AGENT] P0. **3.B Balance reconciler.** Per-account total balance reconcile.
- [ ] [AGENT] P0. **3.C Custody reconciler.** Copper + CEFFU pings + balance reconcile.
- [ ] [AGENT] P0. **3.D On-chain reconciler.** Wallet on-chain balance vs internal state.
- [ ] [AGENT] P0. **3.E Event reconciler.** Event-stream count + sequence vs expected per service.
- [ ] [AGENT] P0. **3.F Manifest reconciler.** Phantom audit (per CLAUDE.md "Manifest phantom audit") wired as nightly
      cron — extends existing script.
- [ ] [AGENT] P0. **3.G Order-state reconciler.** Internal order state vs venue order state.
- [ ] [AGENT] P0. **3.H PnL + clock + batch-vs-live reconcilers.** PnL invariant + clock-skew + UTL@908b1647
      batch-vs-live extension.

**Full-execution criterion**: 8 reconcilers shipped; per-reconciler test green; aggregate dashboard endpoint returns 8
reconciler statuses.

## Phase 4 — Per-service breaker + bus integration (Days 8-10, ~2 AI-days, 4 parallel sub-agents)

- [ ] [AGENT] P0. **4.A risk-and-exposure-service.** Every breaker registered against UAC registry; firing emits typed
      event.
- [ ] [AGENT] P0. **4.B execution-service.** Matching engine subscribes to KillSwitchBus; cancel-on-arm wired per scope;
      new-order-block on arm.
- [ ] [AGENT] P0. **4.C position-balance + alerting consumers.** Subscribe to breaker + kill-switch events; severity
      routing.
- [ ] [AGENT] P0. **4.D strategy-service.** On `KILL_PER_ARCHETYPE` for owned archetype, signal generator stops; on
      `KILL_ALL_LIVE`, all archetypes stop.

**Full-execution criterion**: per-repo QG green; integration test fires a breaker → arms a kill switch → strategy stops
→ execution cancels — within named SLA.

## Phase 5 — Auto-recovery rules (Days 10-11, ~1 AI-day)

- [ ] [AGENT] P0. **5.A Per-breaker recovery rule.** Each `BreakerRecoveryRule` declared with named guard (e.g. "oracle
      deviation < 5σ for 5min" → auto-disarm). **Two recovery modes wired (Q8 ratification)**: (1) `manual_unkill` —
      breaker armed state persists until operator action via deployment-UI or `kill-switch unkill` CLI; recovery emits
      `KILL_SWITCH_MANUAL_UNKILLED` alert with `unkilled_by_operator_id`. (2) `auto_cooldown` — guard predicate
      re-evaluated every `cooldown_seconds`; on N consecutive green readings the breaker auto-disarms; emits
      `KILL_SWITCH_AUTO_RECOVERED` alert with `recovered_after_seconds` + guard-evaluation trail. Per-action defaults
      drive selection per Phase 1.A `BREAKER_RECOVERY_DEFAULTS`; per-breaker override via `BreakerConfig.recovery_mode`.
- [ ] [AGENT] P0. **5.B Recovery test matrix.** Per breaker × per recovery rule, integration test exercises the recovery
      path.

**Full-execution criterion**: ≥10 recovery rules per archetype; recovery test matrix green.

## Phase 6 — Chaos-drill cron (Day 11, ~0.5 AI-day)

- [ ] [SCRIPT] P0. **6.A Cron VM `disaster-drill-cron-`.** Nightly runs subset of
      `simulation_scenarios_topology_price_shocks_2026_05_09` `OPERATIONAL` + `VENUE_OUTAGE` + `PRICE_SHOCK` scenarios
      per cutover archetype.
- [ ] [AGENT] P0. **6.B Drill report.** Pass/fail per scenario; alerting rule on red >24h.

**Full-execution criterion**: cron VM RUNNING; first nightly drill emits a `disaster_drill_report.parquet`; alert rule
registered.

## Phase 7 — deployment-api + ui kill-switch surface (Day 12, ~0.5 AI-day)

- [ ] [AGENT] P0. **7.A `/api/kill-switch/{id}/arm` + `/disarm` endpoints.** Operator-auth-gated; emits
      `KillSwitchArmRequest` to bus.
- [ ] [AGENT] P0. **7.B deployment-ui Kill-switch tab.** Per-switch state + arm/disarm button + audit-log view +
      reconciler dashboard.

**Full-execution criterion**: operator can arm a kill switch from UI; UI confirms within named SLA; audit log shows
entry.

## Phase 8 — Codex SSOTs (Day 12, ~0.5 AI-day)

- [ ] [AGENT] P0. **8.A NEW `codex/04-architecture/circuit-breaker-rule-taxonomy.md`.**
- [ ] [AGENT] P0. **8.B NEW `codex/04-architecture/kill-switch-event-bus.md`.**
- [ ] [AGENT] P0. **8.C UPDATE `kill-switch-circuit-breaker.md`** — wired to new taxonomy + bus.
- [ ] [AGENT] P0. **8.D UPDATE `autonomous-recovery-matrix.md`** — per-breaker recovery rule cross-link.
- [ ] [AGENT] P0. **8.F NEW `codex/04-architecture/risk-breaker-seam.md` (co-owned with risk_simulations Phase 7.E per
      Q9 ratification 2026-05-10).** Distinct-enums-with-escalation-seam architecture: `RiskRuleConsequence` and
      `BreakerAction` are SEPARATE enums (different triggers, different layers). Seam: N consecutive
      `RiskRuleConsequence.SCALE_DOWN` fires on same `(venue, asset_group)` within window W →
      `BREAKER_ESCALATION_REQUESTED` event consumed by execution-service breaker. UAC SSOT
      `RISK_TO_BREAKER_ESCALATION_MAP` declares thresholds. Breaker state machine subscribes to the event + transitions
      per its own rules (Phase 4.B execution-service integration). Per-action `BreakerRecoveryMode` (Phase 1.A) wires
      both manual + auto-cooldown paths.
- [ ] [AGENT] P0. **8.E UPDATE `mev-protection.md`** — MEV-driven breaker entry.

**Full-execution criterion**: 2 NEW + 3 UPDATE; cross-references resolve.

## Phase 9 — Real-VM DR drill (Day 13, ~1 AI-day)

- [ ] [SCRIPT] P0. **9.A Cutover-archetype DR drill VM `dr-drill-cutover-`.** Per archetype: arm `KILL_PER_ARCHETYPE`,
      verify all components stop within SLA; arm `KILL_ALL_LIVE`, verify global stop; trigger 5 named breakers in
      sequence; verify each fires + recovers per rule.
- [ ] [AGENT] P0. **9.B Evidence capture.**

**Full-execution criterion**: per-archetype DR drill log green; ≥15 breaker fires + recoveries per archetype within SLA.

## Phase 10 — Cutover gate (Day 13, ~0.25 AI-day)

- [ ] [AGENT] P0. **10.A Master plan rows.** Group F item 20 + 21 rows green.
- [ ] [AGENT] P0. **10.B Banners removed.**

**Full-execution criterion**: master plan rows green; banners gone.

## Cross-plan coordination

- `simulation_scenarios_topology_price_shocks_2026_05_09` — synthetic scenarios drive the chaos-drill cron + Phase 9
  drill.
- `risk_simulations_limits_alerting_2026_05_10` — risk rule taxonomy is the upstream vocabulary; this plan consumes +
  composes via the **risk-breaker escalation seam (Q9 ratification 2026-05-10)**: distinct enums (`RiskRuleConsequence`
  ≠ `BreakerAction`), coupled by `BREAKER_ESCALATION_REQUESTED` event + UAC `RISK_TO_BREAKER_ESCALATION_MAP`. Phase 1.A
  here ships `BreakerConfig.recovery_mode` + `cooldown_seconds`; risk plan Phase 1.F ships `BreakerRecoveryMode` +
  `BREAKER_RECOVERY_DEFAULTS` UAC. Banner mutually with explicit Q8 + Q9 tags.
- `alerting_service_live_rules_2026_05_07` — breaker + kill-switch events route through alerting; banner reciprocal.

## Deferred work after 2026-05-10 plan-creation session

| Item                                               | Status            | Successor / blocker                          |
| -------------------------------------------------- | ----------------- | -------------------------------------------- |
| Cross-region failover (AWS↔GCP active-active)     | DEFERRED-PER-USER | Post-cutover ops plan                        |
| Full chaos-drill cadence (weekly / monthly drills) | DEFERRED-PER-USER | Post-cutover; nightly cutover MVP runs first |
| Non-cutover venue / chain recovery playbooks       | DEFERRED-PER-USER | Post-cutover                                 |

## Done definition

1. ✅ Phases 0-10 every checkbox flipped with evidence.
2. ✅ UAC + UTL + 5 service repos + UI + PM green.
3. ✅ ≥10 breakers × 2 archetypes; ≥10 recovery rules; 8 reconcilers; nightly chaos-drill cron RUNNING.
4. ✅ Real-VM DR drill log green per archetype.
5. ✅ Master plan Group F items 20 + 21 rows green.

## Audit findings

### 0.A — Existing breaker / abort-condition inventory (Sub-C 2026-05-11)

**execution-service** (`execution-service/execution_service/engine/`):

- `circuit_breaker.py` — per-venue 3+1-state state machine (CLOSED / OPEN / HALF_OPEN + DEGRADED extension).
  Tracks failure rate over rolling 20-sample window; transitions to DEGRADED at 30% / OPEN at 60%. Reads thresholds
  from `CircuitBreakerConfigRegistry` (UAC-internal) per-venue-type at startup.
- `kill_switch.py` — local kill-switch state primitive (consumer-side wiring for the UTL bus).
- `kill_switch_bus_bridge.py` — bridges UTL `KillSwitchBus` events into the local kill-switch state.
- `venue_failover.py` + `venue_cascade_monitor.py` — venue-failure aggregation that escalates to circuit-breaker.
- `recon_gate.py` + `drain_mode.py` — reconciliation-gated trading + drain-mode unwind.

**risk-and-exposure-service** (`risk_and_exposure_service/`):

- `kill_switch_bus_subscriber.py` — UTL bus subscriber.
- `v2/kill_switch_rules.py` — 3-set `KillSwitchDecision` engine
  (`DELTA_NEUTRAL_EXIT` / `REDUCTIONS_ONLY` / `HUMAN_REQUIRED`) keyed on
  `unified_api_contracts.internal.KillSwitchReason` (DAILY_LOSS_BREACH / MAX_DRAWDOWN_BREACH / DATA_STALE / ...).
- `cli/main.py` — exposes operator-side kill-switch arm/disarm CLI.

**alerting-service** (`alerting_service/`):

- `circuit_breaker.py` — internal circuit-breaker monitor (notifier-side observability).
- `kill_switch_bus_subscriber.py` — UTL bus subscriber for fanout-to-channel routing.
- `error_event_handler.py` + `subscribers/alert_subscriber.py` — event → AlertCode classification + dispatch.

**Classification**: 7 per-venue breakers (execution-service `circuit_breaker.py` registry), 1 cross-venue cascade
monitor, 0 per-archetype breakers (full gap — Phase 1 fills via UAC seed), 0 typed-event breaker emission (gap;
Phase 4.A wires).

### 0.B — Reconciler audit (Sub-C 2026-05-11)

UTL has `batch_live_reconciler.py` (shipped Tab 2 2026-05-08; covers batch-vs-live P&L parity). Per-state-surface
gap: 0/9 reconcilers exist for positions, balances, custody, on-chain, events, manifest, order-state, PnL, clock.
Phase 3 scope unchanged from plan.

### 0.C — Kill-switch path audit (Sub-C 2026-05-11)

UTL `kill_switch/bus.py` ships a `KillSwitchBus` singleton with scope-keyed arm/disarm + in-process pub-sub.
Backed by `KillSwitchScope` (canonical SSOT moved here from `internal/domain/deployment_service/isolation.py`
2026-05-08). Phase 2's bus work reduces to: typed UAC event vocab adoption (UAC@a7a99b5), audit-log persistence
(Phase 2.A), cross-process transport (Phase 2 stretch, post-cutover OK).

### 0.D — Cross-plan banners (Sub-C 2026-05-11)

Verified Q8 + Q9 ratification banners already in place on master plan + alerting plan + risk plan. No additional
banner pass needed for Phase 0.

## DONE block

### 2026-05-11 — Sub-C Phase 0 + Phase 1 (UAC layer)

- **UAC@a7a99b5** — `feat(uac): circuit-breaker + kill-switch taxonomy + per-archetype registry seeds`
  - `canonical/crosscutting/circuit_breaker.py` — 20 `CircuitBreakerId` + 5 `BreakerScope` + 4 `BreakerAction` +
    2 `BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` SSOT + `BreakerTrigger` + `BreakerConfig` (with
    cooldown/recovery validators) + `BreakerRecoveryRule`.
  - `canonical/crosscutting/kill_switch.py` — 11 `KillSwitchId` + 4 `KillSwitchProvenance` +
    `KillSwitchArmRequest` + `KillSwitchArmedEvent` + `KillSwitchDisarmEvent`.
  - `registry/circuit_breakers/{carry_staked_basis,arbitrage_price_dispersion}.py` — 10 `BreakerConfig` + 10
    `BreakerRecoveryRule` per archetype.
  - `unified_api_contracts/__init__.py` — facade re-exports for the 13 new public symbols.
- **UAC@dc4c9f0** — `style(uac): ruff fixes on risk_rule + strategy_family + tests` — the autofmt sweep landed
  Sub-C's test files (38 + 23 = 61 tests) alongside Sub-B's ruff-format work.
- Phase 0.A-D + Phase 1.A-F flipped to `- [x]` with evidence cites.

Risk-plan Phase 1.F coordination unblocked: `BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` shipped at
UAC@a7a99b5. The master coordinator (or Sub-B's next push) flips
[`risk_simulations_limits_alerting_2026_05_10.md`](risk_simulations_limits_alerting_2026_05_10.md) Phase 1.F with
cross-reference to UAC@a7a99b5.

### 2026-05-11 — Slot 7 master coordinator (LIVE_ALERT_RULES seed for kill-switch recovery codes)

- `unified-api-contracts@c96447b` — Master coordinator seeded `KILL_SWITCH_AUTO_RECOVERED` + `KILL_SWITCH_MANUAL_UNKILLED`
  rule entries in `LIVE_ALERT_RULES` (alongside the 4 RISK_RULE_* entries from the risk plan). Both recovery codes use
  `kill_switch_scope=KillSwitchScope.GLOBAL` (validator requires scope for `KILL_SWITCH_*` prefix) but
  `triggers_kill_switch=False` — they REPORT past kill-switch state changes, not arm new ones. Test
  `test_kill_switch_rules_trigger_kill_switch_flag` updated to exempt RECOVERY codes from the
  `triggers_kill_switch=True` invariant via explicit `_RECOVERY_CODES` set. 160/160 tests pass workspace-wide.

The risk-plan Phase 1.F flip is now live with the actual UAC@a7a99b5 + UAC@c96447b commit citations (no longer the
placeholder "TBD" cross-reference).
