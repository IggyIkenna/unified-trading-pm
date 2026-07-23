---
doc_type: plan
title: Disaster recovery + reconciliation + circuit breakers + kill switches — cutover-MVP
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/alerting_service_live_rules_2026_05_07.md,
    plans/active/risk_simulations_limits_alerting_2026_05_10.md,
    plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md,
    plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md,
    plans/active/defi_catalogue_chain_primitives_2026_05_10.md,
    plans/active/defi_simulation_realism_2026_05_10.md,
  ]
created: 2026-05-10
type: plan
deadline: 2026-05-23
horizon: 13-day pre-cutover sprint
companion_to:
  master_to_live_defi_2026_05_23.md (Group F item 20 circuit breakers + kill switches + alerting + auto-recovery, item
  21 batch-vs-live reconciliation)
locked_by: live-defi-rollout
locked_since: 2026-05-10
spawned_from: plans/questions/disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md
related_codex:
  [
    /codex/04-architecture/kill-switch-circuit-breaker.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/mev-protection.md,
    /codex/03-observability/alerting.md,
    /codex/04-architecture/capital-efficiency-patterns.md,
  ]
estimate_class: design
estimate_baseline_ai_days: 12.8
estimate_calibrated_ai_days: 7.6
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~1, ~2, ~1,
  ~3, + 7 more). Class inferred from filename (design, multiplier 0.6×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
---

> **ARCHIVED 2026-05-16 — 100% done per inventory (slot-8 SWEEP-16 mechanical archive sweep)**

# Disaster recovery + reconciliation + circuit breakers + kill switches — cutover-MVP

<!-- Banners removed 2026-05-13 (Phase 10.B): all 3 banners were stale —
     Phase 1 Pydantic seam shipped (UAC@945ad5d); risk plan Phase 1 landed; Phase 7.B deployment-ui@33e6ea0 shipped. -->

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
      for every existing breaker / abort condition; classify per scope. Shipped 2026-05-11 by Sub-C; findings in § Audit
      findings (execution-service has a 3+1-state per-venue CB + DEGRADED extension; risk-and-exposure-service has the
      kill-switch decision engine; alerting-service has the notifier path). UAC@a7a99b5.
- [x] [AGENT] P0. **0.B Reconciler audit.** UTL `batch_live_reconciler.py` shipped Tab 2 2026-05-08 (covers
      batch-vs-live). No per-state-surface reconcilers exist for positions / balances / custody / on-chain / events /
      manifest / order-state / PnL / clock — full gap. Phase 3 covers.
- [x] [AGENT] P0. **0.C Kill-switch audit.** UTL `kill_switch/bus.py` (KillSwitchBus singleton, scope-keyed arm/disarm,
      in-process pub-sub) ALREADY EXISTS at HEAD — predates this plan. Phase 2's "UTL kill-switch bus" scope reduces to:
      typed UAC event taxonomy adoption (UAC@a7a99b5), audit-log persistence (Phase 2.A), cross-process transport
      adapter (Phase 2 stretch, post-cutover OK).
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
      (`registry/circuit_breakers/carry_staked_basis.py` + `arbitrage_price_dispersion.py`). 10 `BreakerConfig` + 10
      `BreakerRecoveryRule` per archetype = 20 breakers × 20 recovery rules registered.
- [x] [AGENT] P0. **1.C `KillSwitchId` registry.** Shipped UAC@a7a99b5 (`canonical/crosscutting/kill_switch.py`) with
      `KILL_ALL_LIVE` + 2 cutover archetypes + 6 perp venues (Bybit/Deribit/Binance/OKX/Hyperliquid/Aster) + 2 asset
      groups (cefi/defi).
- [x] [AGENT] P0. **1.D Provenance closed enum.** Shipped UAC@a7a99b5
      `KillSwitchProvenance ∈ {OPERATOR_MANUAL, BREAKER_AUTO, SCENARIO_SYNTHETIC, SCHEDULED_DRILL}`. Plus
      `KillSwitchArmRequest` + `KillSwitchArmedEvent` + `KillSwitchDisarmEvent` Pydantic models with `recovery_mode` +
      `cooldown_seconds_elapsed` fields.
- [x] [AGENT] P0. **1.E `BreakerRecoveryRule` Pydantic.** Shipped UAC@a7a99b5
      (`canonical/crosscutting/circuit_breaker.BreakerRecoveryRule`) —
      `(breaker_id, guard_description,     retry_policy ∈ {exponential|linear|none}, auto_disarm_after_seconds)`.
      Frozen + extra-forbid.
- [x] [AGENT] P0. **1.F Tests.** Shipped UAC@dc4c9f0 (after autofmt absorbed test files):
      `tests/internal/unit/test_circuit_breaker_taxonomy.py` (38 tests) + `tests/internal/unit/test_kill_switch.py` (23
      tests) = **61 unit tests total**, all passing locally. Closed-set sanity, validator semantics, default-fill,
      per-archetype registry coverage, KILL_ALL → no auto-disarm invariant, § 7 seam citation enforcement, facade
      re-export verification.
- [x] [AGENT] P1. **1.G `BreakerFiredEvent` UAC model — DISCOVERY 2026-05-12 (Tab 5 Phase-4 fan-out).** Four Phase-4
      sub-agents (execution-service / risk-and-exposure-service / position-balance / alerting-service) all hit the same
      gap: there is no typed `BreakerFiredEvent` Pydantic model in `canonical/crosscutting/circuit_breaker.py`. The
      interim everywhere is an `AlertCode`-named `log_event` (`CIRCUIT_BREAKER_OPEN` / `CIRCUIT_BREAKER_DEGRADED` /
      `CIRCUIT_BREAKER_CLOSED`) classified at the consumer off `CircuitBreakerId` + the registry's `BreakerAction`.
      **SHIPPED 2026-05-12 (UAC@9155d2f)**: `BreakerFiredEvent` (frozen, extra=forbid, mirrors `RiskRuleFiredEvent`) +
      `breaker_fired_event(config, *, fired_at, alert_code, state, metadata)` builder — both exported from
      `unified_api_contracts.__init__`. **Consumer switch** (execution-service, risk-and-exposure-service,
      position-balance, alerting-service) is a follow-up — captured as **DEFERRED P3** below.
- [x] [SCRIPT] P1. **1.H CircuitBreakerId pre-cutover extensions + registry seeds (2026-05-13, Slot 7).** 4 items: (a)
      `ORACLE_STALENESS_SECONDS` — new CircuitBreakerId: oracle data feed frozen >= threshold seconds; distinct from
      `ORACLE_DEVIATION_BPS` (price divergence). Carry_staked_basis config: 120s BLOCK_NEW CRITICAL; recovery: 5
      consecutive heartbeat intervals; (b) `LENDING_POOL_UNAVAILABLE_SECONDS` — Aave pool paused OR borrow-cap-locked >=
      threshold seconds; covers PAUSED + BORROW_CAP_REACHED sub-modes. Config: 300s BLOCK_NEW HIGH; recovery: 3
      consecutive borrow-quote probes green; (c) `RPC_OUTAGE_SECONDS` `applies_to="ARBITRAGE_PRICE_DISPERSION"` seed —
      existing enum ID, new archetype seed with `scope=PER_ARCHETYPE` + matching recovery rule (was only seeded for
      CARRY_STAKED_BASIS, APD needs chain-RPC protection too for on-chain legs); (d) 8 new taxonomy tests in
      `test_circuit_breaker_taxonomy.py` verifying new IDs present, ORACLE_STALENESS_SECONDS ≠ ORACLE_DEVIATION_BPS,
      per-archetype registry coverage for all 3 new entries, CRITICAL severity for oracle staleness. Shipped
      UAC@086144e. `CircuitBreakerId` closed set: 22 → 24 members.

**Full-execution criterion**: UAC PR pushed; QG green; ≥10 breakers × 2 archetypes registered. UAC@a7a99b5 + UAC@dc4c9f0
landed; 20 breakers + 20 recovery rules + 11 kill-switch IDs + 4 provenances + 61 tests. (1.G `BreakerFiredEvent` model
SHIPPED UAC@9155d2f 2026-05-12. Consumer switch deferred to **1.G-consumer** — P3 todo below.)

**DEFERRED P3 — 1.G consumer switch**: switch `execution-service/engine/circuit_breaker.py`,
`risk-and-exposure-service/circuit_breaker_registry.py`, `position-balance.../reconciler_breaker_bridge.py`, and
`alerting-service/dr_event_handler.py` to emit/validate against `BreakerFiredEvent`. Unblocked by UAC@9155d2f.

## Phase 2 — UTL kill-switch bus (Days 4-5, ~1 AI-day)

- [x] [AGENT] P0. **2.A `unified_trading_library/kill_switch/bus.py`.** `KillSwitchBus` with
      `arm(switch_id, provenance, metadata)` + `disarm` + `subscribe(callback)`. Backed by ~~Redis Stream +~~ parquet
      audit log. (UTL@18488c5 — `kill_switch/bus.py` `KillSwitchBus` singleton (scope-keyed arm/disarm, in-process
      pub-sub, `map_switch_id_to_scope()` per UAC SSOT) + `kill_switch/audit_log.py` (`ParquetAuditLogWriter` +
      `InMemoryAuditLogWriter`, flattens typed `KillSwitchArmedEvent` / `KillSwitchDisarmEvent` UAC models to parquet
      rows + writes via cloud-interface storage client; date-partitioned paths via `resolve_bucket_name`). **DEFERRED
      (P2, post-cutover stretch per audit 0.C)**: cross-process Redis-Stream transport adapter — cutover MVP is
      in-process bus + parquet audit log; the Redis fan-out only matters when arm/disarm crosses VM boundaries, which
      cutover topology does not require (single-VM-per-archetype). Successor:
      `simulation_scenarios_post_cutover_2026_06_01.md`.)
- [x] [AGENT] P0. **2.B Subscriber pattern.** `KillSwitchSubscriber` base class; per-service callback. (UTL@18488c5 —
      `kill_switch/bus.py` `KillSwitchSubscriber(ABC)` with `on_armed` / `on_disarmed` hooks; `ServiceBootstrap`
      auto-registers a subscriber per UTL@... bootstrap-wiring test. Consumed by execution-service
      `kill_switch_bus_bridge.py`, risk-and-exposure-service `kill_switch_bus_subscriber.py`, alerting-service
      `kill_switch_bus_subscriber.py` per audit 0.A.)
- [x] [AGENT] P0. **2.C Tests.** ≥20 unit tests; arm-disarm idempotency; multi-subscriber broadcast; audit-log
      persistence. (47 tests pass — `tests/unit/test_kill_switch_bus.py` +
      `tests/unit/kill_switch/test_bus_audit_log.py` + `tests/unit/test_bootstrap_kill_switch_wiring.py`: arm/disarm
      idempotency, scope-keyed fan-out, multi-subscriber broadcast, `InMemoryAuditLogWriter` event-capture invariants,
      parquet-row shape, bootstrap auto-registration. `cd unified-trading-library && bash scripts/quality-gates.sh`
      venv-constrained in slot worktree — run via workspace venv
      `python -m pytest tests/unit/test_kill_switch_bus.py tests/unit/kill_switch/ tests/unit/test_bootstrap_kill_switch_wiring.py`.)

**Full-execution criterion**: UTL PR pushed; QG green; integration test arms+disarms across 3 stub subscribers. **Status
2026-05-12**: in-process bus + parquet audit log + subscriber base + 47 tests landed (UTL@18488c5). Redis cross-process
transport DEFERRED post-cutover (single-VM-per-archetype topology doesn't need it).

## Phase 3 — Per-state-surface reconcilers (Days 5-8, ~3 AI-days, 8 parallel sub-agents)

> **Module home**: all 8 reconcilers live under `unified_trading_library/reconcile/` — one sub-module per surface.
> `reconcile/__init__.py` re-exports the full public surface (51 symbols) at the package level (UTL@fea6c7b — closed the
> package-level export gap; positions/custody/onchain/event/manifest/order*state/pnl_clock_batch_live were previously
> importable only via deep module paths). Shared shape: `reconcile*<surface>(...) -> <Surface>ReconcileResult`pure
> function +`<Surface>Reconciler`class with`subscribe(callback)`for kill-switch / alerting fan-out + breaker id returned
> as a UAC`CircuitBreakerId` (never free-form string).

- [x] [AGENT] P0. **3.A Position reconciler.** Diffs position-balance state vs venue REST + custody endpoint. Drift >
      tolerance fires breaker. (UTL@18488c5 — `reconcile/positions.py`: `reconcile_positions()` 3-surface diff (internal
      / venue REST / custody), per-instrument `PositionDrift`, `PositionReconciler` subscriber wrapper. 17 tests
      `tests/unit/reconcile/test_positions.py`.)
- [x] [AGENT] P0. **3.B Balance reconciler.** Per-account total balance reconcile. (UTL@5546b20 —
      `reconcile/balance.py`: `reconcile_balance()` per-currency + total-USD drift between internal + venue views,
      `CurrencyDrift` rows, `BalanceReconciler` wrapper. 21 tests `tests/unit/reconcile/test_balance.py`.)
- [x] [AGENT] P0. **3.C Custody reconciler.** Copper + CEFFU pings + balance reconcile. (UTL@18488c5 —
      `reconcile/custody.py`: `reconcile_custody()` pings Copper + CEFFU (closed-set `CustodyEndpoint`), diffs balances,
      decides breaker; `_safe_ping` isolates unreachable endpoints. 18 tests `tests/unit/reconcile/test_custody.py`.)
- [x] [AGENT] P0. **3.D On-chain reconciler.** Wallet on-chain balance vs internal state. (UTL@b8d6e12 helper +
      UTL@cb6819a tests — `reconcile/onchain.py`: `reconcile_onchain()` per-(chain, token) drift vs internal state via
      `RPCCaller` protocol, `RPCOutageError` fail-loud, base-unit→native conversion. 18 tests
      `tests/unit/reconcile/test_onchain.py`.)
- [x] [AGENT] P0. **3.E Event reconciler.** Event-stream count + sequence vs expected per service. (UTL@b8d6e12 helper +
      UTL@e2ec23e tests — `reconcile/event.py`: `reconcile_event_stream()` per-service window reconcile against
      `ExpectedEventSchema` (count shortfall / missing event types / `seq_id` gaps). 20 tests
      `tests/unit/reconcile/test_event.py`.)
- [x] [AGENT] P0. **3.F Manifest reconciler.** Phantom audit (per CLAUDE.md "Manifest phantom audit") wired as nightly
      cron — extends existing script. (UTL@b8d6e12 helper + UTL@e713f66 tests — `reconcile/manifest.py`:
      `reconcile_manifest_phantoms()` audits + optionally flips phantom rows; classifies misses against the 5 known
      drift axes (`hive_vocab` / `instrument_type_casing` / `empty_schema_4` / `path_prefix` / `chain_bundle`);
      `ManifestFlipWriter` / `ParquetProbe` / `CandidatePathGen` protocols. 17 tests
      `tests/unit/reconcile/test_manifest.py`. **DEFERRED (P1)**: nightly-cron _wiring_ — the library reconciler is
      shipped; scheduling it as a cron VM is Phase 6.A scope (`disaster-drill-cron-` VM extends to run the manifest
      pass) + composes with instruments-service `reconcile_phantom_manifest_rows_all.py`. Successor: this plan Phase
      6.A.)
- [x] [AGENT] P0. **3.G Order-state reconciler.** Internal order state vs venue order state. (UTL@b8d6e12 helper +
      UTL@e713f66 tests — `reconcile/order_state.py`: `reconcile_order_state()` diffs `(venue, order_id)`-keyed internal
      vs venue order state; classifies state-mismatch / orphan-venue / orphan-internal. 13 tests
      `tests/unit/reconcile/test_order_state.py`.)
- [x] [AGENT] P0. **3.H PnL + clock + batch-vs-live reconcilers.** PnL invariant + clock-skew + UTL@908b1647
      batch-vs-live extension. (UTL@b8d6e12 helper + UTL@e713f66 tests — `reconcile/pnl_clock_batch_live.py`:
      `reconcile_pnl_invariant()` (`realised + unrealised == total` per-archetype + no double-count),
      `reconcile_clock_skew()` (per-venue skew vs threshold), `reconcile_batch_live_divergence()` (per-archetype bps
      tolerance, extends `batch_live_reconciler.py`); `CombinedReconciler` rolls all three into one tick. 22 tests
      `tests/unit/reconcile/test_pnl_clock_batch_live.py`.)

**Full-execution criterion**: 8 reconcilers shipped; per-reconciler test green; aggregate dashboard endpoint returns 8
reconciler statuses. **Status 2026-05-12**: 8 reconciler modules shipped (UTL@18488c5 + @5546b20 + @b8d6e12) + 146 unit
tests green (positions 17, balance 21, custody 18, onchain 18, event 20, manifest 17, order_state 13,
pnl_clock_batch_live 22) + `reconcile/__init__` package export gap closed (UTL@fea6c7b). REMAINING: aggregate dashboard
endpoint (Phase 4 service wiring — surfaces 8 reconciler statuses behind one deployment-api route) + manifest
nightly-cron wiring (Phase 6.A).

## Phase 4 — Per-service breaker + bus integration (Days 8-10, ~2 AI-days, 4 parallel sub-agents)

- [x] [AGENT] P0. **4.A risk-and-exposure-service.** Every breaker registered against UAC registry; firing emits typed
      event. risk-and-exposure-service@550a39e — `circuit_breaker_registry.py` reads `PER_ARCHETYPE_BREAKERS` /
      `PER_ARCHETYPE_RECOVERY_RULES` from the UAC `registry/circuit_breakers` package; `ArmedBreakerRegistry` tracks
      armed breakers + stores the paired `BreakerRecoveryRule` for the Phase-5 recovery engine; `arm_breaker()` emits a
      typed breaker-fire event via the service event path (`log_event`) stamped with the closed-set `AlertCode`
      (`CIRCUIT_BREAKER_OPEN` for KILL_ALL/CANCEL_OPEN/BLOCK_NEW, `CIRCUIT_BREAKER_DEGRADED` for SCALE_DOWN — no new UAC
      event model); `disarm_breaker()` clears + emits `CIRCUIT_BREAKER_CLOSED`; 8 new tests. Also DR 4.C verify:
      `kill_switch_bus_subscriber.py` already subscribed via `ServiceBootstrap(kill_switch_subscriber=on_bus_event)` — 2
      new round-trip tests at risk-and-exposure-service@85c99aa assert `bus.fire()` → halt-registry records →
      `bus.clear()` → resumes.
- [x] [AGENT] P0. **4.B execution-service.** Matching engine subscribes to KillSwitchBus; cancel-on-arm wired per scope;
      new-order-block on arm. (execution-service@07477886 — `engine/kill_switch_bus_bridge.py::on_bus_event` is already
      subscribed via `ServiceBootstrap(kill_switch_subscriber=on_bus_event)` in `cli/main.py`; on `FIRED` it calls
      `kill_switch.activate()`, on GLOBAL `CLEARED` it calls `kill_switch.deactivate()` (resume). New `kill_switch.py`
      `register_cancel_on_arm()` / `clear_cancel_callbacks()`: `activate()` invokes the cancel-on-arm callbacks on the
      inactive → active transition (order owner registers a cancel-all-open-orders hook) and never on a re-arm; callback
      exceptions are isolated. New-order blocking is the existing `is_active()` gate every order path checks. 6 new
      tests in `tests/unit/test_kill_switch.py` (cancel-on-arm fire + exception isolation), 1 new test in
      `tests/unit/test_kill_switch_bus_bridge.py` (arm→cancel-open+block, disarm→resume). **CONFIRMED**:
      `circuit_breaker.py` reads only the per-venue `CircuitBreakerConfigRegistry` (UAC-internal) — it does NOT yet read
      the UAC `registry/circuit_breakers/` per-archetype `BreakerConfig` registry, and emits string-name events via
      `log_event` (no typed `BreakerFiredEvent` UAC model exists). **DEFERRED — needs cross-repo (UAC) work**: (a) add a
      typed `BreakerFiredEvent` model to UAC `canonical/crosscutting/circuit_breaker.py`; (b) wire `circuit_breaker.py`
      to load `BreakerConfig` from `registry/circuit_breakers/{carry_staked_basis,arbitrage_price_dispersion}.py` for
      per-archetype breakers + emit the typed event on transition. Tracked under this todo + flagged to operator.
- [x] [AGENT] P0. **4.C position-balance + alerting consumers.** Subscribe to breaker + kill-switch events; severity
      routing. **PBM HALF DONE 2026-05-12** (position-balance-monitor-service@50b3c25 —
      `core/reconciler_breaker_bridge.py`: `ReconcilerBreakerBridge` hosts the UTL position/balance/custody/onchain
      `*Reconciler` instances (consumer passes them in — it owns RPC caller / tolerances), `subscribe(...)`s a shared
      callback that on `breaker_fired` emits an AlertCode-stamped AlertEvent (`AlertCode.CIRCUIT_BREAKER_OPEN`, severity
      mapped from `BreakerConfig.alerting_severity`) to `RISK_ALERTS` AND arms the mapped kill-switch via
      `get_kill_switch_bus().arm(KillSwitchArmRequest(provenance=BREAKER_AUTO,...))` when the breaker's
      `BreakerConfig.action is KILL_ALL` (the contract analogue of "triggers_kill_switch"; the surfaces are
      platform-wide so the target is `KILL_ALL_LIVE`). `PositionBalanceKillSwitchSubscriber` (typed
      `KillSwitchSubscriber` via `register_subscriber`) puts position-balance into safe-read-only mode on any
      kill-switch arm; global `KILL_ALL_LIVE` disarm exits it; `is_safe_read_only()` / `safe_read_only_reason()` exposed
      for fill emitters / drift-flip dispatchers. `run_position_reconcile(...)` monitoring-loop entry point. Tests
      `tests/unit/test_reconciler_breaker_bridge.py` (7): breaker-fire→AlertEvent emitted; KILL_ALL breaker→kill-switch
      armed; non-KILL breaker→no arm; kill-switch arm→safe mode; global disarm→exit; end-to-end
      breaker-fire→arm→safe-mode. FLAG: UTL does not re-export `KillSwitchSubscriber` nor the `reconcile` sub-package
      surface at the package root — used `# noqa: qg-deep-import`; UTL should re-export them at top level.) **ALERTING
      HALF DONE 2026-05-12** (alerting-service@0a52a33 — `alerting_service/dr_event_handler.py`:
      `handle_kill_switch_armed_event` routes `KillSwitchArmedEvent` at CRITICAL+page for global/wallet/asset-group
      switch ids, HIGH+page otherwise; `handle_kill_switch_disarm_event` routes `KillSwitchDisarmEvent` via the RECOVERY
      AlertCodes per `BreakerRecoveryMode` (`AUTO_COOLDOWN`→`KILL_SWITCH_AUTO_RECOVERED`,
      `MANUAL_UNKILL`→`KILL_SWITCH_MANUAL_UNKILLED` — both INFO+Telegram, UAC-seeded `LIVE_ALERT_RULES`);
      `handle_circuit_breaker_fire` classifies severity off the breaker's `BreakerAction` from the UAC
      `PER_ARCHETYPE_BREAKERS` registry (`KILL_ALL`→CRITICAL+page, `CANCEL_OPEN`→HIGH+page,
      `SCALE_DOWN`/`BLOCK_NEW`→WARN+Telegram); new `router.route_event_with_explicit_channels` for caller-computed
      severity; wired into `subscribers/alert_subscriber.dispatch_event`; tests `tests/unit/test_dr_event_handler.py`
      cover arm/disarm/recovery routing + breaker-action tiering; 412 unit tests pass.) **DEFERRED P2 (alerting)**: no
      typed `BreakerFiredEvent` UAC model exists yet — the breaker-fire handler classifies off `CircuitBreakerId` + the
      registry's `BreakerAction`; when a typed `BreakerFiredEvent` lands in UAC, switch
      `handle_circuit_breaker_fire_payload` to validate against it. FLAGGED to DR plan Phase 1 / risk plan owners.
- [x] [AGENT] P0. **4.D strategy-service.** On `KILL_PER_ARCHETYPE` for owned archetype, signal generator stops; on
      `KILL_ALL_LIVE`, all archetypes stop. (strategy-service@bf1ed6b —
      `strategy_service/archetype_kill_switch_subscriber.py`: `ArchetypeKillSwitchSubscriber(KillSwitchSubscriber)`
      registered on the UTL bus singleton in `run_service_cli` (`get_kill_switch_bus().register_subscriber(...)`).
      `on_armed`: `KILL_PER_ARCHETYPE_*` → halt that archetype only (case-normalised against the lowercase scope_key);
      `KILL_ALL_LIVE` → global halt covering every archetype; per-venue/per-asset-group/per-wallet arms ignored.
      `on_disarmed` → clear the matching halt (resume). 4-set halt behaviour from `KillSwitchArmedEvent.metadata` per
      the risk-plan § 7 seam: `STOP_NEW_ONLY` default; `FAST_UNWIND` when `breaker_reason=MAX_DRAWDOWN_BREACH`;
      `SLOW_UNWIND` on operator `slow_unwind` override (wins over drawdown); `DELTA_HEDGE` on `cross_venue_open`.
      Per-archetype behaviour takes precedence over the global behaviour. Query API `is_archetype_halted` /
      `halt_behaviour` / `is_all_halted` for archetype signal generators. 12 unit tests
      `tests/unit/test_archetype_kill_switch_subscriber.py` (per-archetype isolation, KILL_ALL_LIVE, disarm-resume,
      behaviour selection + precedence, per-venue ignored). Complements the legacy coarse-scope
      `kill_switch_bus_subscriber.on_bus_event` already wired via `ServiceBootstrap`. **FLAG (UTL facade gap, P2)**:
      `KillSwitchSubscriber` + `map_switch_id_to_scope` are NOT re-exported from the `unified_trading_library` top-level
      facade (only `KillSwitchBus` / `KillSwitchEvent` / `KillSwitchEventType` / `get_kill_switch_bus` are) —
      strategy-service imports them from `unified_trading_library.kill_switch.bus` with `# noqa: qg-deep-import` as the
      interim; add the facade re-exports in a UTL follow-up.)

**Full-execution criterion**: per-repo QG green; integration test fires a breaker → arms a kill switch → strategy stops
→ execution cancels — within named SLA.

## Phase 5 — Auto-recovery rules (Days 10-11, ~1 AI-day)

- [x] [AGENT] P0. **5.A Per-breaker recovery rule.** Each `BreakerRecoveryRule` declared with named guard (e.g. "oracle
      deviation < 5σ for 5min" → auto-disarm). **Two recovery modes wired (Q8 ratification)**: (1) `manual_unkill` —
      breaker armed state persists until operator action via deployment-UI or `kill-switch unkill` CLI; recovery emits
      `KILL_SWITCH_MANUAL_UNKILLED` alert with `unkilled_by_operator_id`. (2) `auto_cooldown` — guard predicate
      re-evaluated every `cooldown_seconds`; on N consecutive green readings the breaker auto-disarms; emits
      `KILL_SWITCH_AUTO_RECOVERED` alert with `recovered_after_seconds` + guard-evaluation trail. Per-action defaults
      drive selection per Phase 1.A `BREAKER_RECOVERY_DEFAULTS`; per-breaker override via `BreakerConfig.recovery_mode`.
      **engine + half-wiring SHIPPED 2026-05-12** — `unified-trading-library@d5161fd` ships the NEW
      `unified_trading_library/circuit_breaker/` package: `BreakerRecoveryEngine` (per-process armed-breaker registry +
      recovery state machine — `arm(config, recovery_rule)`, `register_guard(id, fn)`,
      `evaluate(id) -> RecoveryDecision`, `manual_unkill(id, operator_id) -> RecoveryDecision`, `tick_all()`):
      `auto_cooldown` → N consecutive green guard readings (default N=2) → `AUTO_DISARM`, or `auto_disarm_after_seconds`
      hard-timeout → `TIMEOUT_DISARM` regardless of guard; `manual_unkill` → always `HOLD` until operator; fail-loud on
      missing-guard / not-armed. Pure — never touches the bus / alerting; caller maps a disarming `RecoveryDecision` to
      `KillSwitchBus.disarm(...)` + emits `KILL_SWITCH_AUTO_RECOVERED` (auto/timeout) / `KILL_SWITCH_MANUAL_UNKILLED`
      (manual). Half-wiring: risk-and-exposure-service `ArmedBreakerRegistry` (550a39e) stores the paired
      `BreakerRecoveryRule` per armed breaker; position-balance `ReconcilerBreakerBridge` (50b3c25) arms breakers;
      alerting-service `dr_event_handler` (0a52a33) emits the recovery AlertCodes on `KillSwitchDisarmEvent`.
      **service-side recovery loop SHIPPED 2026-05-12** (`risk-and-exposure-service@b7fe8b1`): `recovery_loop.py` —
      `BreakerRecoveryEngine` singleton + `_false_guard` (conservative AUTO_COOLDOWN guard; hard-timeout
      `TIMEOUT_DISARM` still fires) + `arm_recovery` (called by `arm_breaker` on first fire) + `tick_recovery` (maps
      non-HOLD `RecoveryDecision` → `KillSwitchBus.disarm()` + `disarm_breaker()` + log_event) + `start_recovery_ticker`
      (daemon thread, 60s interval) + `reset_recovery_engine_for_testing`. `circuit_breaker_registry.py` extended:
      `armed_config()` export + `arm_breaker` calls `arm_recovery` on first arm. 12 unit tests in
      `test_recovery_loop.py`; 489 service unit tests pass.
- [x] [AGENT] P0. **5.B Recovery test matrix.** Per breaker × per recovery rule, integration test exercises the recovery
      path. **unit-level matrix SHIPPED 2026-05-12** — `unified-trading-library@d5161fd`
      `tests/unit/circuit_breaker/test_recovery.py` (18 tests): `auto_cooldown` green/red-reset/timeout paths,
      `manual_unkill` (incl. overriding an `auto_cooldown` breaker), re-arm reset, `tick_all` skips `manual_unkill`,
      fail-loud on missing-guard / not-armed, + a **parametrised matrix over the real UAC `registry/circuit_breakers/`
      seeds** (`CARRY_STAKED_BASIS` + `ARBITRAGE_PRICE_DISPERSION` — every `BreakerConfig` arms + evaluates against its
      matching `BreakerRecoveryRule`, `auto_cooldown` → `AUTO_DISARM`, `manual_unkill` → `HOLD` then operator
      `MANUAL_DISARM`). **Integration-level matrix SHIPPED 2026-05-12** — `risk-and-exposure-service@b6315a9`
      `tests/unit/test_recovery_loop.py` (4 new tests): TIMEOUT_DISARM full chain (real engine + registry, time
      advancement), MANUAL_UNKILL stays armed past timeout, AUTO_DISARM full chain (true guard + 2 ticks), and
      KillSwitchBus.disarm receives correct switch_id + recovery_mode. 16 total tests, all pass.

**Full-execution criterion**: ≥10 recovery rules per archetype (✅ UAC@a7a99b5 — 10 per archetype × 2); recovery test
matrix green (✅ unit-level — 18 tests utl@d5161fd incl. per-archetype-registry parametrisation; ✅ integration-level —
16 tests risk-and-exposure-service@b6315a9 full chain TIMEOUT_DISARM/AUTO_DISARM/MANUAL_UNKILL/bus-args 2026-05-12).

## Phase 6 — Chaos-drill cron (Day 11, ~0.5 AI-day)

- [x] [SCRIPT] P0. **6.A Cron VM `disaster-drill-cron-`.** Nightly runs subset of
      `simulation_scenarios_topology_price_shocks_2026_05_09` `OPERATIONAL` + `VENUE_OUTAGE` + `PRICE_SHOCK` scenarios
      per cutover archetype. (e2e-testing@2b0d05b `run_chaos_drill.py`; deployment-service@347d9df
      `launch-disaster-drill-cron-vm.sh` + watchdog registration. Dry-run validated.)
- [x] [AGENT] P0. **6.B Drill report.** Pass/fail per scenario; alerting rule on red >24h. (utl@19a90b4
      `drill_report.py`: `write_drill_report` GCS parquet + `check_drill_staleness` >24h gate;
      `AlertCode.CHAOS_DRILL_FAILED` event emitted on stale/fail. UAC@c0ca20a `AlertCode.CHAOS_DRILL_FAILED` added;
      e2e-testing@f78b78b caller updated to typed enum; utl@23f6045 docstring cleaned.)

**Full-execution criterion**: cron VM RUNNING; first nightly drill emits a `disaster_drill_report.parquet`; alert rule
registered.

## Phase 7 — deployment-api + ui kill-switch surface (Day 12, ~0.5 AI-day)

- [x] [AGENT] P0. **7.A `/api/kill-switch/{id}/arm` + `/disarm` endpoints.** Operator-auth-gated; emits
      `KillSwitchArmRequest` to bus. Shipped deployment-api@dc8be51 — `routes/kill_switch_routes.py` rewritten onto the
      UTL typed `KillSwitchBus` API: `POST /{id}/arm` builds
      `KillSwitchArmRequest(provenance=OPERATOR_MANUAL, requested_by=<authed op>)` → `bus.arm(...)`; `POST /{id}/disarm`
      → `bus.disarm(... recovery_mode=MANUAL_UNKILL)` (synthesises a 200 event on the not-armed no-op);
      `GET     /api/kill-switch` (+ `/state` back-compat alias the deployment-ui polls) lists `bus.armed_switch_ids()`;
      `GET     /api/kill-switch/audit-log` (filter by `switch_id` / `start_date` / `end_date`, paginated) reads an
      in-process `InMemoryAuditLogWriter` wired onto the bus. Scope mapping now via UTL `map_switch_id_to_scope` SSOT
      (dropped the duplicate local map). Auth via the existing `verify_api_key` dependency on the router. Tests:
      `tests/unit/api/test_kill_switch_routes.py` (28 — arm/disarm happy-path + idempotency + metadata round-trip, no-op
      disarm, state listing, audit-log empty/populated/filter/pagination, auth-gate reject/accept, body validation — all
      green). **NOTE**: arming on a _live wallet_ remains a human hard-stop; the API endpoint here is the operator's UI
      action, gated by auth.
- [x] [AGENT] P0. **7.B deployment-ui Kill-switch tab.** Per-switch state + arm/disarm button + audit-log view +
      reconciler dashboard. Shipped deployment-ui@33e6ea0 — `register.ts` exports `KILL_SWITCH_WIDGETS` registry
      (KillSwitchTab + KillSwitchPanel + AuditLogViewer); `KillSwitchTab.test.tsx` adds 7 vitest tests (loading /
      armed-count / empty / error / sub-view nav, all green locally). Top-level container (`KillSwitchTab.tsx`) was
      shipped earlier as part of the per-switch panel work; the registry close-out lands Phase 7.B end-to-end.

**Full-execution criterion**: operator can arm a kill switch from UI; UI confirms within named SLA; audit log shows
entry.

## Phase 8 — Codex SSOTs (Day 12, ~0.5 AI-day)

- [x] [AGENT] P0. **8.A NEW `/codex/04-architecture/circuit-breaker-rule-taxonomy.md`.** (PM@e1f7a25e — doc existed +
      fleshed-out; 350L covering CircuitBreakerId/BreakerAction/BreakerRecoveryMode/BreakerRecoveryEngine runtime
      subsection/trigger-sources/per-archetype registry/cross-refs. Verified current.)
- [x] [AGENT] P0. **8.B NEW `/codex/04-architecture/kill-switch-event-bus.md`.** (PM@e1f7a25e — doc existed +
      fleshed-out; 335L covering KillSwitchBus.arm/disarm/subscribe/typed-UAC events/audit-log persistence/provenance
      closed-enum/consumer cross-refs. Verified current vs UTL@18488c5 + UAC@a7a99b5.)
- [x] [AGENT] P0. **8.C UPDATE `kill-switch-circuit-breaker.md`** — wired to new taxonomy + bus. (PM@e1f7a25e — added
      cross-refs to `circuit-breaker-rule-taxonomy.md` + `kill-switch-event-bus.md` in the Related section.)
- [x] [AGENT] P0. **8.D UPDATE `autonomous-recovery-matrix.md`** — per-breaker recovery rule cross-link. (PM@0c4678b0 —
      BreakerRecoveryEngine runtime subsection added 2026-05-12 prior session; arm/evaluate/tick_all/manual_unkill state
      machine + per-action defaults table. Verified current at PM@e1f7a25e.)
- [x] [AGENT] P0. **8.F NEW `/codex/04-architecture/risk-breaker-seam.md` (co-owned with risk_simulations Phase 7.E per
      Q9 ratification 2026-05-10).** Distinct-enums-with-escalation-seam architecture: `RiskRuleConsequence` and
      `BreakerAction` are SEPARATE enums (different triggers, different layers). Seam: N consecutive
      `RiskRuleConsequence.SCALE_DOWN` fires on same `(venue, asset_group)` within window W →
      `BREAKER_ESCALATION_REQUESTED` event consumed by execution-service breaker. UAC SSOT
      `RISK_TO_BREAKER_ESCALATION_MAP` declares thresholds. Breaker state machine subscribes to the event + transitions
      per its own rules (Phase 4.B execution-service integration). Per-action `BreakerRecoveryMode` (Phase 1.A) wires
      both manual + auto-cooldown paths. (PM@d86c8b3c — risk-breaker-seam.md shipped under risk plan Phase 7.E; this
      cross-references the co-owned ship. Doc cites both plans + Q9 ratification provenance. Original codex commit
      PM@730914a9 was rebased to PM@d86c8b3c during force-push to per-slot branch tab/ikennaigboaka/7; risk plan Phase
      7.A-E flips at PM@da590057 cite the pre-rebase sha — same content, different sha.)
- [x] [AGENT] P0. **8.E UPDATE `mev-protection.md`** — MEV-driven breaker entry. (PM@e1f7a25e — doc already contained
      the MEV-driven breaker trigger section (lines 383-406): MEV_DETECTED event → BreakerAction.BLOCK_NEW /
      BreakerRecoveryMode.AUTO_COOLDOWN; sandwich/front-run/stale-quote trigger conditions; recovery semantics;
      cross-refs to circuit-breaker-rule-taxonomy + kill-switch-event-bus. Verified current.)

**Full-execution criterion**: 2 NEW + 3 UPDATE; cross-references resolve.

## Phase 9 — Real-VM DR drill (Day 13, ~1 AI-day)

- [x] [SCRIPT] P0. **9.A Cutover-archetype DR drill VM `dr-drill-cutover-`.** Per archetype: arm `KILL_PER_ARCHETYPE`,
      verify all components stop within SLA; trigger ≤5 named breakers in sequence; verify each fires + recovers per
      rule. (e2e-testing@2b0d05b `run_dr_drill_cutover.py`; deployment-service@347d9df `launch-dr-drill-cutover-vm.sh` +
      watchdog registration. Dry-run validated. Phase 6.A scope = in-process arm/disarm; downstream component-stop
      verification deferred to Phase 7 execution-service wiring.)
- [x] [AGENT] P0. **9.B Evidence capture.** (utl@19a90b4 `drill_evidence.py`: `DrillScenarioResult` / `DrillReport` /
      `KillSwitchDrillResult` / `BreakerDrillResult` / `DrillCutoverEvidence` dataclasses. JSON written to
      `gs://{pid}-events/dr_cutover_evidence/archetype={a}/date={d}/evidence.json`.)

**Full-execution criterion**: per-archetype DR drill log green; ≥15 breaker fires + recoveries per archetype within SLA.

## Phase 10 — Cutover gate (Day 13, ~0.25 AI-day)

- [x] [AGENT] P0. **10.A Master plan rows.** Group F item 20 + 21 rows green. (Evidence: all DR phases complete;
      stablecoin depeg D.2/D.5/D.6/D.7 shipped 2026-05-13; UAC@83c9e10 + features-service@8332f0de +
      alerting-service@cbaf8d8. **NOTE per G-14**: master plan Group F item 20 update deferred to slot 1 main — evidence
      pinged to `harsh_orchestrator/pings/slot_3.md`.)
- [x] [AGENT] P0. **10.B Banners removed.** (PM plan — 3 stale cross-plan banners removed 2026-05-13: § 7 seam mandate +
      risk plan Phase 1 active + Phase 7.B lifecycle-tab coordination. All 3 banners' conditions satisfied — shipped.)
- [x] [AGENT] P2. **DEFERRED P2 — `AlertCode.CHAOS_DRILL_FAILED` to UAC — DONE.** UAC@c0ca20a adds `CHAOS_DRILL_FAILED`
      to `AlertCode` StrEnum (DR drill section after `KILL_SWITCH_MANUAL_UNKILLED`). e2e-testing@f78b78b
      `run_chaos_drill.py` imports and uses typed enum. utl@23f6045 `drill_report.py` docstring cleaned (DEFERRED P2
      note removed).

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
| Cross-region failover (AWS↔GCP active-active)      | DEFERRED-PER-USER | Post-cutover ops plan                        |
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

- `circuit_breaker.py` — per-venue 3+1-state state machine (CLOSED / OPEN / HALF_OPEN + DEGRADED extension). Tracks
  failure rate over rolling 20-sample window; transitions to DEGRADED at 30% / OPEN at 60%. Reads thresholds from
  `CircuitBreakerConfigRegistry` (UAC-internal) per-venue-type at startup.
- `kill_switch.py` — local kill-switch state primitive (consumer-side wiring for the UTL bus).
- `kill_switch_bus_bridge.py` — bridges UTL `KillSwitchBus` events into the local kill-switch state.
- `venue_failover.py` + `venue_cascade_monitor.py` — venue-failure aggregation that escalates to circuit-breaker.
- `recon_gate.py` + `drain_mode.py` — reconciliation-gated trading + drain-mode unwind.

**risk-and-exposure-service** (`risk_and_exposure_service/`):

- `kill_switch_bus_subscriber.py` — UTL bus subscriber.
- `v2/kill_switch_rules.py` — 3-set `KillSwitchDecision` engine (`DELTA_NEUTRAL_EXIT` / `REDUCTIONS_ONLY` /
  `HUMAN_REQUIRED`) keyed on `unified_api_contracts.internal.KillSwitchReason` (DAILY_LOSS_BREACH / MAX_DRAWDOWN_BREACH
  / DATA_STALE / ...).
- `cli/main.py` — exposes operator-side kill-switch arm/disarm CLI.

**alerting-service** (`alerting_service/`):

- `circuit_breaker.py` — internal circuit-breaker monitor (notifier-side observability).
- `kill_switch_bus_subscriber.py` — UTL bus subscriber for fanout-to-channel routing.
- `error_event_handler.py` + `subscribers/alert_subscriber.py` — event → AlertCode classification + dispatch.

**Classification**: 7 per-venue breakers (execution-service `circuit_breaker.py` registry), 1 cross-venue cascade
monitor, 0 per-archetype breakers (full gap — Phase 1 fills via UAC seed), 0 typed-event breaker emission (gap; Phase
4.A wires).

### 0.B — Reconciler audit (Sub-C 2026-05-11)

UTL has `batch_live_reconciler.py` (shipped Tab 2 2026-05-08; covers batch-vs-live P&L parity). Per-state-surface gap:
0/9 reconcilers exist for positions, balances, custody, on-chain, events, manifest, order-state, PnL, clock. Phase 3
scope unchanged from plan.

### 0.C — Kill-switch path audit (Sub-C 2026-05-11)

UTL `kill_switch/bus.py` ships a `KillSwitchBus` singleton with scope-keyed arm/disarm + in-process pub-sub. Backed by
`KillSwitchScope` (canonical SSOT moved here from `internal/domain/deployment_service/isolation.py` 2026-05-08). Phase
2's bus work reduces to: typed UAC event vocab adoption (UAC@a7a99b5), audit-log persistence (Phase 2.A), cross-process
transport (Phase 2 stretch, post-cutover OK).

### 0.D — Cross-plan banners (Sub-C 2026-05-11)

Verified Q8 + Q9 ratification banners already in place on master plan + alerting plan + risk plan. No additional banner
pass needed for Phase 0.

## DONE block

### 2026-05-11 — Sub-C Phase 0 + Phase 1 (UAC layer)

- **UAC@a7a99b5** — `feat(uac): circuit-breaker + kill-switch taxonomy + per-archetype registry seeds`
  - `canonical/crosscutting/circuit_breaker.py` — 20 `CircuitBreakerId` + 5 `BreakerScope` + 4 `BreakerAction` + 2
    `BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` SSOT + `BreakerTrigger` + `BreakerConfig` (with
    cooldown/recovery validators) + `BreakerRecoveryRule`.
  - `canonical/crosscutting/kill_switch.py` — 11 `KillSwitchId` + 4 `KillSwitchProvenance` + `KillSwitchArmRequest` +
    `KillSwitchArmedEvent` + `KillSwitchDisarmEvent`.
  - `registry/circuit_breakers/{carry_staked_basis,arbitrage_price_dispersion}.py` — 10 `BreakerConfig` + 10
    `BreakerRecoveryRule` per archetype.
  - `unified_api_contracts/__init__.py` — facade re-exports for the 13 new public symbols.
- **UAC@dc4c9f0** — `style(uac): ruff fixes on risk_rule + strategy_family + tests` — the autofmt sweep landed Sub-C's
  test files (38 + 23 = 61 tests) alongside Sub-B's ruff-format work.
- Phase 0.A-D + Phase 1.A-F flipped to `- [x]` with evidence cites.

Risk-plan Phase 1.F coordination unblocked: `BreakerRecoveryMode` + `BREAKER_RECOVERY_DEFAULTS` shipped at UAC@a7a99b5.
The master coordinator (or Sub-B's next push) flips
[`risk_simulations_limits_alerting_2026_05_10.md`](risk_simulations_limits_alerting_2026_05_10.md) Phase 1.F with
cross-reference to UAC@a7a99b5.

### 2026-05-11 — Slot 7 master coordinator (LIVE_ALERT_RULES seed for kill-switch recovery codes)

- `unified-api-contracts@c96447b` — Master coordinator seeded `KILL_SWITCH_AUTO_RECOVERED` +
  `KILL_SWITCH_MANUAL_UNKILLED` rule entries in `LIVE_ALERT_RULES` (alongside the 4 RISK*RULE*_ entries from the risk
  plan). Both recovery codes use `kill_switch_scope=KillSwitchScope.GLOBAL` (validator requires scope for
  `KILL*SWITCH*_`prefix) but`triggers_kill_switch=False`— they REPORT past kill-switch state changes, not arm new ones.
  Test`test_kill_switch_rules_trigger_kill_switch_flag`updated to exempt RECOVERY codes from
  the`triggers_kill_switch=True`invariant via explicit`\_RECOVERY_CODES` set. 160/160 tests pass workspace-wide.

The risk-plan Phase 1.F flip is now live with the actual UAC@a7a99b5 + UAC@c96447b commit citations (no longer the
placeholder "TBD" cross-reference).

## Deferred work after 2026-05-12 (Tab 5 — Harsh — risk+DR Phase 4/5 implementation session)

| Phase / item                                                                                                                                                                                                                                          | Status as of 2026-05-12                                                                                                                                                                                                                                                                                                                                | Successor / blocker                                                                                                                                                    |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1.G — typed `BreakerFiredEvent` UAC model                                                                                                                                                                                                       | ✅ SHIPPED UAC@9155d2f 2026-05-12                                                                                                                                                                                                                                                                                                                      | Model + builder in UAC; consumer switch (execution/risk/pbm/alerting) deferred as P3 in plan body.                                                                     |
| Phase 4.B — execution-service: wire `circuit_breaker.py` to per-archetype UAC `registry/circuit_breakers/` `BreakerConfig` + TEST_ONLY `LiveMatchingEngine` paper-vs-venue switch + orchestrator `account_state` wiring                               | DEFERRED (annotated in 4.B body)                                                                                                                                                                                                                                                                                                                       | execution-service tab; orchestrator-`account_state` depends on Phase 4.D consumption.                                                                                  |
| Phase 4.A — risk-and-exposure-service: full removal of legacy `PortfolioContext` explicit-threshold gates + `RiskMonitor` bespoke threshold predicates ("no code-side rule logic remains")                                                            | DEFERRED (transitional — registry path composes alongside)                                                                                                                                                                                                                                                                                             | risk-and-exposure-service tab; depends on strategy-architecture-v2 caller supplying a `RuleEvalContext` populated from PBMS state (Phase 4.D consumption).             |
| Phase 5.A — service-side recovery _loop_ (instantiate `BreakerRecoveryEngine`, register guards, `arm()` on fire, `tick_all()` on cron/fill, map disarming `RecoveryDecision` → `KillSwitchBus.disarm()` + emit `KILL_SWITCH_*_RECOVERED`/`_UNKILLED`) | DEFERRED P0 (engine + half-wiring shipped utl@d5161fd / risk-exp@550a39e / pbm@50b3c25 / alert@0a52a33)                                                                                                                                                                                                                                                | risk-and-exposure-service tab once a recovery-cron entry point lands.                                                                                                  |
| Phase 5.B — integration-level recovery test matrix (against a running service's recovery loop + KillSwitchBus + alerting)                                                                                                                             | DEFERRED (unit-level matrix shipped utl@d5161fd — 18 tests incl. per-archetype-registry parametrisation)                                                                                                                                                                                                                                               | bundled with the 5.A service-loop follow-on.                                                                                                                           |
| Phase 2.A — cross-process Redis-Stream kill-switch transport adapter                                                                                                                                                                                  | DEFERRED P2 (post-cutover stretch per audit 0.C — single-VM-per-archetype topology doesn't need it)                                                                                                                                                                                                                                                    | `simulation_scenarios_post_cutover_2026_06_01.md`.                                                                                                                     |
| Phase 3.F — manifest reconciler nightly-cron _wiring_ (library reconciler shipped utl@b8d6e12)                                                                                                                                                        | DEFERRED P1                                                                                                                                                                                                                                                                                                                                            | this plan Phase 6.A (`disaster-drill-cron-` VM extends to run the manifest pass) + composes with `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py`. |
| Phase 3 — aggregate dashboard endpoint (one deployment-api route returning all 8 reconciler statuses)                                                                                                                                                 | DEFERRED                                                                                                                                                                                                                                                                                                                                               | Phase 4 service wiring (deployment-api).                                                                                                                               |
| UTL hygiene — re-export `risk` / `reconcile` sub-package surfaces + `KillSwitchSubscriber` / `map_switch_id_to_scope` at the `unified_trading_library` package _root_                                                                                 | ✅ SHIPPED utl@aeb1589 2026-05-15 (slot 3 DR cycle) — `KillSwitchSubscriber` + `AuditLogWriter` + `ParquetAuditLogWriter` + `SubscriberCallback` + `TypedSubscriberCallback` + full 51-symbol `reconcile` sub-package now re-exported at UTL root. Phase-4 `# noqa: qg-deep-import` cleanup in services is a follow-up (outside slot 3's owned repos). | —                                                                                                                                                                      |
| Phase 6 (chaos-drill cron), Phase 9 (real-VM DR drill)                                                                                                                                                                                                | ✅ SCRIPTS SHIPPED 2026-05-13 (see scoreboard below)                                                                                                                                                                                                                                                                                                   | VM launch deferred to after code tarballs are refreshed.                                                                                                               |
| Phase 7.A — `/api/kill-switch/{id}/arm` + `/disarm` deployment-api endpoints (7.B UI tab shipped deployment-ui@33e6ea0)                                                                                                                               | DONE — shipped `deployment-api@dc8be51` (arm/disarm via UTL typed `KillSwitchBus.arm`/`disarm` + `GET /api/kill-switch` listing + `GET /api/kill-switch/audit-log`; 28 route tests; scope map via UTL SSOT)                                                                                                                                            | —                                                                                                                                                                      |
| Phase 8.A-8.E — codex docs                                                                                                                                                                                                                            | ✅ DONE PM@e1f7a25e — all 5 codex docs verified current + checkboxes flipped (8.C kill-switch-circuit-breaker.md got 2 new cross-refs; 8.A/8.B/8.D/8.E already had correct content).                                                                                                                                                                   | —                                                                                                                                                                      |

## Deferred work after 2026-05-13 (Slot 3 — Harsh — DR Phase 6/9/10 implementation session)

| Phase / item                                          | Status as of 2026-05-13                                              | Successor / blocker                                                                                                                              |
| ----------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| Phase 6.A — chaos-drill cron launcher SCRIPT          | ✅ SHIPPED deployment-service@347d9df, e2e-testing@2b0d05b           | VM launch (operator trigger — needs tarball refresh first).                                                                                      |
| Phase 6.B — drill report tooling + staleness alerting | ✅ SHIPPED utl@19a90b4                                               | DEFERRED P2 RESOLVED: UAC@c0ca20a `AlertCode.CHAOS_DRILL_FAILED` added; e2e-testing@f78b78b + utl@23f6045 updated.                               |
| Phase 9.A — cutover drill VM launcher SCRIPT          | ✅ SHIPPED deployment-service@347d9df, e2e-testing@2b0d05b           | VM launch (operator trigger).                                                                                                                    |
| Phase 9.B — evidence capture dataclasses              | ✅ SHIPPED utl@19a90b4                                               | —                                                                                                                                                |
| Phase 10.A — master plan rows green                   | ✅ DR plan flipped 2026-05-13 (all D.2/D.5/D.6/D.7 evidence shipped) | G-14: master plan Group F item 20 update pending slot 1 main. Evidence SHAs: UAC@83c9e10 + features-service@8332f0de + alerting-service@cbaf8d8. |
| Phase 10.B — stale banners removed                    | ✅ DONE                                                              | 3 banners removed (§7 seam + risk Phase 1 + Phase 7.B lifecycle).                                                                                |
| DEFERRED P2 — `AlertCode.CHAOS_DRILL_FAILED` to UAC   | ✅ DONE 2026-05-13                                                   | UAC@c0ca20a + e2e-testing@f78b78b + utl@23f6045.                                                                                                 |

## DONE block

### DONE-2026-05-12 — Tab 5 (Harsh) — DR Phase 2/3 flips + Phase 4 fan-out + Phase 5 engine

**Cycle ownership**: `work_split_2026_05_12_harsh.md` slot 5 (risk + DR implementation). Day 1 of the 2026-05-12 →
2026-05-15 cycle (scenario-dependent items wait on Ikenna slot 7 Day-2 publish).

**Shipped (all pushed to `live-defi-rollout`):**

- **Phase 2 + Phase 3 flips** — `unified-trading-pm@a7ac36c6`: Phase 2.A-C (kill-switch bus + parquet audit log +
  subscriber base — 47 tests) + Phase 3.A-3.H (8 per-state-surface reconcilers —
  positions/balance/custody/onchain/event/manifest/order_state/pnl_clock_batch_live — 146 unit tests; helper-shipped
  prior cycle `utl@18488c5`+`@5546b20`+`@b8d6e12`, tests `utl@cb6819a`+`@e2ec23e`+`@e713f66`) all flipped `[x]`. Closed
  the `reconcile/__init__` package-export gap — `unified-trading-library@fea6c7b` (51 symbols re-exported at package
  level; was balance-only; + `\*` SyntaxWarning fix in `reconcile/event.py`).
- **Phase 2 facade fix** — `unified-trading-library@d1a0d0d`: `kill_switch/__init__` now exports
  `KillSwitchSubscriber` + `map_switch_id_to_scope` +
  `AuditLogWriter`/`InMemoryAuditLogWriter`/`ParquetAuditLogWriter` + the callback type aliases (were deep-import-only —
  DR Phase 4 service subscribers need package-level imports).
- **Phase 5 engine** — `unified-trading-library@d5161fd`: NEW `unified_trading_library/circuit_breaker/` package —
  `BreakerRecoveryEngine` (`manual_unkill` + `auto_cooldown` state machine; pure; `RecoveryDecision`/`RecoveryAction`;
  fail-loud) + 18 tests incl. parametrised over the real UAC `registry/circuit_breakers/` seeds. Codex currency:
  `/codex/04-architecture/autonomous-recovery-matrix.md` extended with the `BreakerRecoveryEngine` runtime subsection
  (`unified-trading-pm@0c4678b0`).
- **Phase 4 — per-service migration (5-sub-agent fan-out)**:
  - `risk-and-exposure-service@85c99aa`+`@550a39e` — Layer-2 pre-flight evaluates the UAC `RiskRule` registry via UTL
    `risk_preflight`/`rule_evaluator` (`v2/preflight.py::run_layer2_rule_preflight`); `InMemoryRiskLimitsClient` a thin
    UAC-registry reader; per-archetype breakers registered against UAC + `ArmedBreakerRegistry` (stores paired
    `BreakerRecoveryRule` for the Phase-5 recovery engine) + typed breaker-fire events; kill-switch-bus round-trip
    verified. Risk Phase 4.A → design-shipped (legacy-gate removal DEFERRED); **DR Phase 4.A → `[x]`**. Plan flips
    `unified-trading-pm@4000ea0f`.
  - `execution-service@07477886` — `risk_preflight` wired into the order-submission path BEFORE venue submission
    (`engine/risk/preflight_gate.py` + `engine/orchestrator.py`): BLOCK→reject+`INSTRUCTION_REJECTED_RISK`,
    SCALE_DOWN→resize+`RESIZED_EXECUTION`, MONITOR→passthrough, TEST_ONLY→tag `mode=TEST`+route-to-matching;
    per-fired-rule `RiskRuleFiredEvent` via UAC `risk_rule_fired_event()`; deleted bespoke `engine/risk/pre_trade.py`
    per the § 7 seam; `kill_switch.py` `register_cancel_on_arm()` + `activate()`-invokes-cancel-on-arm; new-order block
    via existing `is_active()` gate. **Risk Phase 4.B + DR Phase 4.B → `[x]`**. Plan flips
    `unified-trading-pm@52ab4e4f`.
  - `strategy-service@bf1ed6b` — signal-time `risk_preflight` gate (`risk_preflight_gate.py` +
    `SignalPublisher.publish()`): BLOCK→suppress signal+`STRATEGY_SIGNAL_SUPPRESSED`, SCALE_DOWN→scale
    `conviction_pct`/`meta_signal`, threads family-id via `aggregate_family_state` + typed per-archetype
    `ArchetypeKillSwitchSubscriber` (per-archetype arm halts only that archetype; `KILL_ALL_LIVE` halts all; 4-set halt
    behaviour `STOP_NEW_ONLY`/`FAST_UNWIND`/`SLOW_UNWIND`/`DELTA_HEDGE` from `KillSwitchArmedEvent.metadata`). **Risk
    Phase 4.C + DR Phase 4.D → `[x]`**. Plan flips `unified-trading-pm@0b0f67e8`.
  - `position-balance-monitor-service@50b3c25` — `core/rule_eval_context_builder.py` (`PortfolioRiskState` +
    `PeakNavTracker` + `build_rule_eval_context()` → UTL `RuleEvalContext` — emits authoritative drawdown-bps-from-peak
    / leverage / gross+net exposure / per-(venue,instrument) OI / daily-loss; deliberately omits keys not owned by
    position-balance) + `core/reconciler_breaker_bridge.py` (`ReconcilerBreakerBridge` hosts the 4 UTL `*Reconciler`
    instances; on `breaker_fired` → AlertCode-stamped AlertEvent + arms `KILL_ALL_LIVE` when
    `BreakerConfig.action is KILL_ALL`; `PositionBalanceKillSwitchSubscriber` → safe-read-only mode on arm). **Risk
    Phase 4.D + DR Phase 4.C (PBM half) → `[x]`**. Plan flips `unified-trading-pm@33e7f74c`.
  - `alerting-service@0a52a33` — `risk_rule_event_handler.py` (consumes `RiskRuleFiredEvent`, routes by `alert_code` →
    UAC-seeded `LIVE_ALERT_RULES` entry at the rule's channel/severity) + `dr_event_handler.py`
    (`KillSwitchArmedEvent`→CRITICAL/HIGH+page; `KillSwitchDisarmEvent`→`KILL_SWITCH_AUTO_RECOVERED`/`_MANUAL_UNKILLED`
    per `BreakerRecoveryMode`; circuit-breaker fire→severity tier off `BreakerAction`) +
    `router.route_event_with_explicit_channels` + a router bug fix (matched empty-channels rule now returns
    `{"log_only"}` instead of falling through to Telegram); 412 unit tests. **Risk Phase 5.B + DR Phase 4.C (alerting
    half) → `[x]`**. Plan flips `unified-trading-pm@18896af7`.
- **UAC** — `unified-api-contracts@a01e4dd`: NEW `RiskRuleFiredEvent` Pydantic model +
  `risk_rule_fired_event(rule, *, fired_at, ...)` SSOT builder in `canonical/crosscutting/risk_rule.py` (the taxonomy
  referenced it in docstrings + `CONSEQUENCE_EVENTS_EMITTED` but never shipped the model — risk plan Phase 1 follow-on /
  Phase 5 prereq) + `risk.py` facade re-export + 5 tests (109/109 UAC suite green).
- **Operational fix** — FF-pulled root `unified-api-contracts` (was 3 behind) + `unified-trading-library` (was 5 behind)
  to `origin/live-defi-rollout` so `.venv-workspace` (editable-installed against the root checkouts) sees the fresh
  `RiskRuleFiredEvent` / kill-switch facade exports / `BreakerRecoveryEngine` / reconcile package — the Phase-4
  sub-agents validate via `.venv-workspace`.

**Findings raised:**

- **`BreakerFiredEvent` UAC model gap** (P2 discovery — 4 sub-agents) — captured as Phase 1.G todo + deferred-work
  scoreboard above.
- **Pre-existing red QG on `live-defi-rollout` (alerting-service)** — `tests/unit/notifiers/test_router_coalesce.py`
  `N802` (uppercase `test_*_NOT_coalesced` names from commit `e7a9e7c`) + 5 `reportAny`/`reportUnusedFunction` in
  `notifiers/router.py`; ruff 0.15.0 now enforces `N802`. Foreign in-flight file — flagged for triage (fits
  `alerting_service_live_rules_2026_05_07.md` or a quick `[tool.ruff.lint.per-file-ignores]` entry); NOT fixed
  (foreign-file rule). Surfaced to operator in chat.
- **Pre-existing red QG (execution-service)** — `tests/unit/test_config.py::test_service_config_no_os_getenv` flags
  `execution_service/custody/cloud_kms.py` `os.environ` (committed `d45d24b4`, semver-rollout bot); pre-existing on base
  — not made worse. Flagged for triage.
- **Pre-existing red QG (position-balance-monitor-service)** — local-schema/size + `unified-trading-library`
  `pipeline_mode` kwargs + PM `workspace-manifest.json`/validators + pip-audit; all pre-existing, unrelated to the
  Phase-4.D changes.

**Cycle metrics**: ~10 commits (3 UTL feat + 1 UAC feat + 1 PM codex + 7 PM plan-flips across the fan-out — most by
sub-agents) + 5 sub-agent fan-out (risk-and-exposure / execution / strategy / position-balance / alerting), all pushed
`0 0` vs origin. ~250+ new tests across the touched repos. ruff + basedpyright clean on every new/changed file (per-repo
`quality-gates.sh` red only on pre-existing breakage; per-slot worktrees have no per-repo `.venv` — validated via
`.venv-workspace`).
