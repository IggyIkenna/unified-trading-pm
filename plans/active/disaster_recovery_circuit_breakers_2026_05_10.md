---
title: Disaster recovery + reconciliation + circuit breakers + kill switches — cutover-MVP
type: plan
status: active
created: 2026-05-10
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to: master_to_live_defi_2026_05_23.md (Group F item 20 circuit breakers + kill switches + alerting + auto-recovery, item 21 batch-vs-live reconciliation)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/active/risk_simulations_limits_alerting_2026_05_10.md
  - plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md
  - plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md
  - plans/active/defi_readiness_catalogue_2026_05_10.md
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
> taxonomy / 8-event lifecycle / circuit-breaker / alerting rules / strategy kill-switch behaviour). Per the risk
> plan's § 7 mandate, every Phase 1 Pydantic class docstring in this plan MUST include a "§ 7 SSOT reconciliation"
> subsection identifying which of the 5 SSOTs the class composes with + how the seam is preserved. Reviewer rejects
> Phase 1 PRs that omit it.
>
> **🟢 CROSS-PLAN COORDINATION — Phase 7.B kill-switch tab vs `deployment_ui_lifecycle_tabs_2026_05_08.md` 6-tab shell.**
> Phase 7.B below ships a NEW deployment-ui kill-switch tab. The lifecycle plan
> ([`deployment_ui_lifecycle_tabs_2026_05_08.md:152-160`](deployment_ui_lifecycle_tabs_2026_05_08.md)) currently
> declares a 6-tab shell (Deploy / Monitor / Data Status / Builds / Readiness / Config). Decision 2026-05-10 PM:
> kill-switch lands as the **7th lifecycle-managed tab** (NOT folded into Monitor — kill-switches are safety-critical
> and need top-level visibility per CLAUDE.md "Service Infrastructure Requirements"). The lifecycle plan's Phase B.1
> table will be revised to 7 tabs when this plan's Phase 7.B ships; sequencing handled in lifecycle plan's cross-plan
> coordination banner. Until then both plans hold their scope; no other consumer of either plan is blocked.

## Why this plan exists

May-23 cutover gates on Group F item 20 (circuit breakers + kill switches + alerting + auto-recovery) + item 21
(batch-vs-live reconciliation). Today scattered pieces exist (UTL `batch_live_reconciler` shipped Tab 2 2026-05-08;
alerting-service rules plan in flight; matching engine has internal aborts) but no unified taxonomy + matrix + kill-switch
event bus + per-state-surface reconciler suite. This plan ships the cutover-MVP: every state surface has a reconciler,
every named circuit breaker has a typed event + auto-recovery rule, kill-switch arming is an event-bus-driven action
with provenance, and a chaos-drill cron runs nightly. Multi-week DR drills + cross-region failover beyond cutover
archetypes are deferred post-cutover.

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

| Repo                                  | Surface                                                                                                                |
| ------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`               | NEW: `canonical/crosscutting/circuit_breaker.py`, `kill_switch.py`; registry seeds                                    |
| `unified-trading-library`             | NEW: `kill_switch/bus.py`; reconciler suite under `reconcile/`                                                         |
| `risk-and-exposure-service`           | UPDATE: every breaker fires the typed event; recovery rule consumed                                                    |
| `execution-service`                   | UPDATE: matching engine subscribes to kill-switch bus; cancel-on-arm wired                                              |
| `position-balance-monitor-service`    | UPDATE: reconcilers consume position events; per-surface diff emit                                                     |
| `alerting-service`                    | UPDATE: breaker + kill-switch events route to severity tier                                                            |
| `deployment-api` + `deployment-ui`    | NEW: kill-switch arm/disarm UI; reconciler dashboard                                                                    |
| `unified-trading-pm`                  | NEW + UPDATE codex docs                                                                                                |

## Phased execution DAG

```text
0 (pre-audit, parallel) → 1 (UAC breaker + kill-switch taxonomy) → 2 (UTL kill-switch bus) → 3 (per-state-surface reconcilers, parallel)
→ 4 (per-service breaker + bus integration, parallel) → 5 (auto-recovery rules) → 6 (chaos-drill cron) →
7 (deployment-api+ui kill-switch surface) → 8 (codex SSOTs) → 9 (real-VM DR drill) → 10 (cutover gate)
```

## Phase 0 — Pre-audit (Day 1, ~1 AI-day, 4 parallel sub-agents)

- [ ] [AGENT] P0. **0.A Existing breaker audit.** Walk risk-and-exposure-service + execution-service + alerting-service for every existing breaker / abort condition; classify per scope.
- [ ] [AGENT] P0. **0.B Reconciler audit.** UTL `batch_live_reconciler` + any per-service reconciler scripts; coverage gap per state surface.
- [ ] [AGENT] P0. **0.C Kill-switch audit.** Today: ad-hoc operator-via-Telegram / manual API call. Document the existing path before refactoring.
- [ ] [SCRIPT] P0. **0.D Banners on cross-plan files.**

**Full-execution criterion**: § Audit findings populated; banners on 4 plans.

## Phase 1 — UAC breaker + kill-switch taxonomy (Days 2-4, ~2 AI-days)

- [ ] [AGENT] P0. **1.A `CircuitBreakerId` + `BreakerScope` + `BreakerTrigger` + `BreakerAction` enums.** Closed sets.
      **Plus `BreakerRecoveryMode` closed enum `{manual_unkill, auto_cooldown}` + `BREAKER_RECOVERY_DEFAULTS` SSOT —
      RATIFIED 2026-05-10 cross-plan audit Q8 (both modes wired; per-action config picks default).** Per-action defaults
      mapping: `BLOCK_NEW → auto_cooldown` (least-restrictive; auto-resume safe when metric clears),
      `CANCEL_OPEN → manual_unkill` (cancelled orders are gone — auto-recovery doesn't restore),
      `SCALE_DOWN → auto_cooldown` (partial unwind has natural inverse),
      `KILL_ALL → manual_unkill` (full unwind needs operator sign-off). `BreakerConfig.recovery_mode` overrides default
      per-breaker; `cooldown_seconds: int | None` (None when manual). Wiring coordinated with
      [`risk_simulations_limits_alerting_2026_05_10.md`](risk_simulations_limits_alerting_2026_05_10.md) Phase 1.F (UAC
      shipping). Plus 2 NEW AlertCodes shipped via that plan: `KILL_SWITCH_AUTO_RECOVERED` + `KILL_SWITCH_MANUAL_UNKILLED`
      — distinct alert events (Policy B larger-set-wins).
- [ ] [AGENT] P0. **1.B Per-archetype breaker registry seed.** ≥10 breakers per cutover archetype (oracle deviation, RPC outage, gas surge, position-limit, drawdown, liquidation cascade, venue outage, custody disconnect, manifest phantom, batch-live divergence).
- [ ] [AGENT] P0. **1.C `KillSwitchId` registry.** Closed enum: `KILL_ALL_LIVE`, `KILL_PER_ARCHETYPE_<name>`, `KILL_PER_VENUE_<name>`, `KILL_PER_ASSET_GROUP_<name>`.
- [ ] [AGENT] P0. **1.D Provenance closed enum.** `KillSwitchProvenance ∈ {OPERATOR_MANUAL, BREAKER_AUTO, SCENARIO_SYNTHETIC, SCHEDULED_DRILL}`.
- [ ] [AGENT] P0. **1.E `BreakerRecoveryRule` Pydantic.** Per-breaker guard + retry-policy + auto-disarm-condition.
- [ ] [AGENT] P0. **1.F Tests.** ≥30 unit tests; registry completeness; per-archetype breaker coverage.

**Full-execution criterion**: UAC PR pushed; QG green; ≥10 breakers × 2 archetypes registered.

## Phase 2 — UTL kill-switch bus (Days 4-5, ~1 AI-day)

- [ ] [AGENT] P0. **2.A `unified_trading_library/kill_switch/bus.py`.** `KillSwitchBus` with `arm(switch_id, provenance, metadata)` + `disarm` + `subscribe(callback)`. Backed by Redis Stream + parquet audit log.
- [ ] [AGENT] P0. **2.B Subscriber pattern.** `KillSwitchSubscriber` base class; per-service callback.
- [ ] [AGENT] P0. **2.C Tests.** ≥20 unit tests; arm-disarm idempotency; multi-subscriber broadcast; audit-log persistence.

**Full-execution criterion**: UTL PR pushed; QG green; integration test arms+disarms across 3 stub subscribers.

## Phase 3 — Per-state-surface reconcilers (Days 5-8, ~3 AI-days, 8 parallel sub-agents)

- [ ] [AGENT] P0. **3.A Position reconciler.** Diffs position-balance state vs venue REST + custody endpoint. Drift > tolerance fires breaker.
- [ ] [AGENT] P0. **3.B Balance reconciler.** Per-account total balance reconcile.
- [ ] [AGENT] P0. **3.C Custody reconciler.** Copper + CEFFU pings + balance reconcile.
- [ ] [AGENT] P0. **3.D On-chain reconciler.** Wallet on-chain balance vs internal state.
- [ ] [AGENT] P0. **3.E Event reconciler.** Event-stream count + sequence vs expected per service.
- [ ] [AGENT] P0. **3.F Manifest reconciler.** Phantom audit (per CLAUDE.md "Manifest phantom audit") wired as nightly cron — extends existing script.
- [ ] [AGENT] P0. **3.G Order-state reconciler.** Internal order state vs venue order state.
- [ ] [AGENT] P0. **3.H PnL + clock + batch-vs-live reconcilers.** PnL invariant + clock-skew + UTL@908b1647 batch-vs-live extension.

**Full-execution criterion**: 8 reconcilers shipped; per-reconciler test green; aggregate dashboard endpoint returns 8 reconciler statuses.

## Phase 4 — Per-service breaker + bus integration (Days 8-10, ~2 AI-days, 4 parallel sub-agents)

- [ ] [AGENT] P0. **4.A risk-and-exposure-service.** Every breaker registered against UAC registry; firing emits typed event.
- [ ] [AGENT] P0. **4.B execution-service.** Matching engine subscribes to KillSwitchBus; cancel-on-arm wired per scope; new-order-block on arm.
- [ ] [AGENT] P0. **4.C position-balance + alerting consumers.** Subscribe to breaker + kill-switch events; severity routing.
- [ ] [AGENT] P0. **4.D strategy-service.** On `KILL_PER_ARCHETYPE` for owned archetype, signal generator stops; on `KILL_ALL_LIVE`, all archetypes stop.

**Full-execution criterion**: per-repo QG green; integration test fires a breaker → arms a kill switch → strategy stops → execution cancels — within named SLA.

## Phase 5 — Auto-recovery rules (Days 10-11, ~1 AI-day)

- [ ] [AGENT] P0. **5.A Per-breaker recovery rule.** Each `BreakerRecoveryRule` declared with named guard (e.g. "oracle
      deviation < 5σ for 5min" → auto-disarm). **Two recovery modes wired (Q8 ratification)**: (1) `manual_unkill` —
      breaker armed state persists until operator action via deployment-UI or `kill-switch unkill` CLI; recovery emits
      `KILL_SWITCH_MANUAL_UNKILLED` alert with `unkilled_by_operator_id`. (2) `auto_cooldown` — guard predicate
      re-evaluated every `cooldown_seconds`; on N consecutive green readings the breaker auto-disarms; emits
      `KILL_SWITCH_AUTO_RECOVERED` alert with `recovered_after_seconds` + guard-evaluation trail. Per-action defaults
      drive selection per Phase 1.A `BREAKER_RECOVERY_DEFAULTS`; per-breaker override via `BreakerConfig.recovery_mode`.
- [ ] [AGENT] P0. **5.B Recovery test matrix.** Per breaker × per recovery rule, integration test exercises the recovery path.

**Full-execution criterion**: ≥10 recovery rules per archetype; recovery test matrix green.

## Phase 6 — Chaos-drill cron (Day 11, ~0.5 AI-day)

- [ ] [SCRIPT] P0. **6.A Cron VM `disaster-drill-cron-`.** Nightly runs subset of `simulation_scenarios_topology_price_shocks_2026_05_09` `OPERATIONAL` + `VENUE_OUTAGE` + `PRICE_SHOCK` scenarios per cutover archetype.
- [ ] [AGENT] P0. **6.B Drill report.** Pass/fail per scenario; alerting rule on red >24h.

**Full-execution criterion**: cron VM RUNNING; first nightly drill emits a `disaster_drill_report.parquet`; alert rule registered.

## Phase 7 — deployment-api + ui kill-switch surface (Day 12, ~0.5 AI-day)

- [ ] [AGENT] P0. **7.A `/api/kill-switch/{id}/arm` + `/disarm` endpoints.** Operator-auth-gated; emits `KillSwitchArmRequest` to bus.
- [ ] [AGENT] P0. **7.B deployment-ui Kill-switch tab.** Per-switch state + arm/disarm button + audit-log view + reconciler dashboard.

**Full-execution criterion**: operator can arm a kill switch from UI; UI confirms within named SLA; audit log shows entry.

## Phase 8 — Codex SSOTs (Day 12, ~0.5 AI-day)

- [ ] [AGENT] P0. **8.A NEW `codex/04-architecture/circuit-breaker-rule-taxonomy.md`.**
- [ ] [AGENT] P0. **8.B NEW `codex/04-architecture/kill-switch-event-bus.md`.**
- [ ] [AGENT] P0. **8.C UPDATE `kill-switch-circuit-breaker.md`** — wired to new taxonomy + bus.
- [ ] [AGENT] P0. **8.D UPDATE `autonomous-recovery-matrix.md`** — per-breaker recovery rule cross-link.
- [ ] [AGENT] P0. **8.F NEW `codex/04-architecture/risk-breaker-seam.md` (co-owned with risk_simulations Phase 7.E
      per Q9 ratification 2026-05-10).** Distinct-enums-with-escalation-seam architecture: `RiskRuleConsequence` and
      `BreakerAction` are SEPARATE enums (different triggers, different layers). Seam: N consecutive
      `RiskRuleConsequence.SCALE_DOWN` fires on same `(venue, asset_group)` within window W →
      `BREAKER_ESCALATION_REQUESTED` event consumed by execution-service breaker. UAC SSOT
      `RISK_TO_BREAKER_ESCALATION_MAP` declares thresholds. Breaker state machine subscribes to the event +
      transitions per its own rules (Phase 4.B execution-service integration). Per-action `BreakerRecoveryMode`
      (Phase 1.A) wires both manual + auto-cooldown paths.
- [ ] [AGENT] P0. **8.E UPDATE `mev-protection.md`** — MEV-driven breaker entry.

**Full-execution criterion**: 2 NEW + 3 UPDATE; cross-references resolve.

## Phase 9 — Real-VM DR drill (Day 13, ~1 AI-day)

- [ ] [SCRIPT] P0. **9.A Cutover-archetype DR drill VM `dr-drill-cutover-`.** Per archetype: arm `KILL_PER_ARCHETYPE`, verify all components stop within SLA; arm `KILL_ALL_LIVE`, verify global stop; trigger 5 named breakers in sequence; verify each fires + recovers per rule.
- [ ] [AGENT] P0. **9.B Evidence capture.**

**Full-execution criterion**: per-archetype DR drill log green; ≥15 breaker fires + recoveries per archetype within SLA.

## Phase 10 — Cutover gate (Day 13, ~0.25 AI-day)

- [ ] [AGENT] P0. **10.A Master plan rows.** Group F item 20 + 21 rows green.
- [ ] [AGENT] P0. **10.B Banners removed.**

**Full-execution criterion**: master plan rows green; banners gone.

## Cross-plan coordination

- `simulation_scenarios_topology_price_shocks_2026_05_09` — synthetic scenarios drive the chaos-drill cron + Phase 9 drill.
- `risk_simulations_limits_alerting_2026_05_10` — risk rule taxonomy is the upstream vocabulary; this plan consumes +
  composes via the **risk-breaker escalation seam (Q9 ratification 2026-05-10)**: distinct enums
  (`RiskRuleConsequence` ≠ `BreakerAction`), coupled by `BREAKER_ESCALATION_REQUESTED` event + UAC
  `RISK_TO_BREAKER_ESCALATION_MAP`. Phase 1.A here ships `BreakerConfig.recovery_mode` + `cooldown_seconds`; risk plan
  Phase 1.F ships `BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` UAC. Banner mutually with explicit Q8 + Q9 tags.
- `alerting_service_live_rules_2026_05_07` — breaker + kill-switch events route through alerting; banner reciprocal.

## Deferred work after 2026-05-10 plan-creation session

| Item                                                | Status              | Successor / blocker                                                       |
| --------------------------------------------------- | ------------------- | ------------------------------------------------------------------------- |
| Cross-region failover (AWS↔GCP active-active)       | DEFERRED-PER-USER   | Post-cutover ops plan                                                     |
| Full chaos-drill cadence (weekly / monthly drills)  | DEFERRED-PER-USER   | Post-cutover; nightly cutover MVP runs first                              |
| Non-cutover venue / chain recovery playbooks        | DEFERRED-PER-USER   | Post-cutover                                                              |

## Done definition

1. ✅ Phases 0-10 every checkbox flipped with evidence.
2. ✅ UAC + UTL + 5 service repos + UI + PM green.
3. ✅ ≥10 breakers × 2 archetypes; ≥10 recovery rules; 8 reconcilers; nightly chaos-drill cron RUNNING.
4. ✅ Real-VM DR drill log green per archetype.
5. ✅ Master plan Group F items 20 + 21 rows green.

## Audit findings

(Phase 0 sub-agents fill.)

## DONE block

(Filled at completion.)
