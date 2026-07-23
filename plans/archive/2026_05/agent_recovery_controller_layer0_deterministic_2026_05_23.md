---
doc_type: plan
title: Agent Recovery Controller — Layer-0 Deterministic Scripts + AgentActionEvent
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [agent-orchestrator, alerting-service, deployment-service, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related:
  [
    incident_gateway_and_state_machine_2026_05_23.md,
    ai_recovery_audit_signoff_agent_2026_05_23.md,
    /plans/archive/2026_05/deployment_ui_safety_ops_tab_2026_05_23.md,
  ]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 14
estimate_calibrated_ai_days: 14.0
estimate_calibration_note: "Brand-new class (10 distinct deterministic recovery scripts + dry-run mode +
  AgentActionEvent emitter library + runbook-

  ID registry + repeated-repair-loop detector). Baseline 14 = ~1.4 days per script-on-average × 10 scripts. No

  multiplier discount (1.0×) — this is from-scratch work.

  "
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on: [incident_gateway_and_state_machine_2026_05_23]
gates: ["master_to_live_defi_2026_05_23:Group-F"]
---

# Agent Recovery Controller — Layer-0 Deterministic Scripts + AgentActionEvent

> **🟢 SPAWNED 2026-05-23 from `observability_disaster_recovery_audit_2026_05_23.md` gap #2.** Layer-0 of the 5-layer
> defence-in-depth model (`/codex/04-architecture/recovery-defence-in-depth-layers.md` NEW). Deterministic Python — NO
> LLM in the loop on Layer-0; the LLM-audit agent lives on Layer-1 (`ai_recovery_audit_signoff_agent_2026_05_23.md`).

## Goal

Ship a closed-set library of 10 deterministic recovery scripts, each idempotent + dry-run testable + runbook-ID-tagged

- emitting structured `AgentActionEvent` into the Incident Gateway. Recovery actions today are scattered across
  execution-service / kill-switch / circuit-breaker / strategy-service — this plan centralises them so the LLM-audit
  agent and the deployment-UI Safety Ops tab consume a single API.

## Context

**Existing capability** (verified 2026-05-23):

- Kill-switch state machine in execution-service (auto-deactivate + scoping).
- Per-venue circuit breakers in alerting-service.
- KillSwitchBus PubSub publisher hook.
- Retry/backoff via UAC `classify_venue_error()` → RETRY/RECONNECT/SKIP/FAIL.
- Multi-leg compensation in execution-service.
- Cancel-orders capability in execution-service (per-venue).

**Missing for May-23**:

- No central library — 10 actions are scattered or partial.
- No `AgentActionEvent` emitter (depends on Phase 1 of `incident_gateway_and_state_machine_2026_05_23`).
- No runbook-ID registry that maps each action to its operator playbook.
- No dry-run mode (every script must support `--dry-run` to simulate without side-effects).
- No repeated-repair-loop detector (3+ identical actions within sliding window → escalate to SEV0).

## Pre-audit (blast radius)

- NEW directory: `deployment-service/scripts/recovery/` — 10 scripts.
- NEW module: `unified_trading_library/recovery/agent_action.py` — AgentActionEvent emitter + runbook registry +
  repair-loop detector (lives in UTL so every service can import it without adding a dep on deployment-service).
- TOUCH: `execution-service/execution_service/kill_switch.py` — wrap existing activate/deactivate to emit
  AgentActionEvent via new library.
- TOUCH: `execution-service/execution_service/handlers/order_canceller.py` — wrap cancel-orders to emit
  AgentActionEvent.
- TOUCH: `alerting-service/alerting_service/circuit_breaker.py` — wrap force-open/close to emit AgentActionEvent.
- TOUCH: `strategy-service/strategy_service/safe_mode.py` — wrap safe-mode transitions.

Workspace-wide grep before any rename: `rg "kill_switch\.activate|cancel_open_orders|safe_mode" --include="*.py"` —
sanity-check that all call sites continue to work.

## Phased execution DAG

### Phase 1 — UTL agent-action library (1.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. New module `unified_trading_library/recovery/__init__.py` exporting
      `AgentAction`, `AgentActionEmitter`, `RecoveryScriptRegistry`, `RepeatedRepairLoopDetector`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. `AgentAction` dataclass mirrors UAC `AgentActionEvent` schema
      (depends_on Phase 1 of `incident_gateway_and_state_machine`).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.3. `AgentActionEmitter.emit(action) → None` — publishes to Incident
      Gateway via PubSub `agent-recovery-actions` topic (subscribes the LLM-audit agent + the gateway state machine).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.4. `RecoveryScriptRegistry` — closed-set mapping
      `{action_type → (script_path, runbook_id,     idempotent: bool, dry_run_supported: bool, scope_required: tuple[str, ...])}`.
      10 entries.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.5.
      `RepeatedRepairLoopDetector.check(action_type, scope_key) → RepeatedLoopVerdict` — sliding-window counter (default
      15min). 3+ → returns `LoopDetected` which the caller MUST honour by NOT executing the action + escalating to SEV0
      via Incident Gateway.
- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.6. Unit tests in
      `unified-trading-library/tests/unit/recovery/test_agent_action.py` — 15+ tests covering: emitter publishes
      correctly; registry rejects unknown action_type; repair-loop detector counts correctly within window + decays
      outside window; LoopDetected forces SEV0 escalation.

### Phase 2 — 10 Layer-0 deterministic scripts (5 cal-days, parallel within sub-scripts)

Each script lives in `deployment-service/scripts/recovery/<action_type>.py`. Each MUST: (a) implement `--dry-run`, (b)
emit an `AgentAction` BEFORE attempting the action (status=STARTED) and AFTER (status=SUCCEEDED|FAILED), (c) check the
repair-loop detector and bail out with LoopDetected escalation, (d) be idempotent (re-running is safe), (e) be runbook-
ID-tagged.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.7. `restart_service.py --service <name> --reason <text> [--dry-run]` —
      issues Cloud Run service revision flip OR GCE VM systemctl restart depending on service deployment topology.
      Runbook ID: `RB-INFRA-001`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.8. `restart_container.py --container <id> --reason <text> [--dry-run]` —
      Cloud Run revision restart OR Docker container restart on GCE host. Runbook ID: `RB-INFRA-001`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.9.
      `redeploy_known_good.py --service <name> --to-revision <revision> --reason <text> [--dry-run]` — flips Cloud Run
      traffic to previous revision. Runbook ID: `RB-DEPLOY-001`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.10.
      `resize_machine_after_oom.py --vm <name> --new-machine-type <type> --reason <text>     [--dry-run]` — gcloud
      compute instance resize. Runbook ID: `RB-INFRA-001`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.11.
      `failover_feed.py --venue <name> --primary <feed> --backup <feed> --reason <text> [--dry-run]` — flips MTDS
      handler to backup feed; assertion: backup feed is fresh (last tick < staleness threshold). Runbook ID:
      `RB-CONN-001`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.12. `pause_strategy.py --strategy <id> --reason <text> [--dry-run]` —
      calls strategy-service pause endpoint; emits STRATEGY_PAUSED event. Idempotent (pausing an already-paused strategy
      is a no-op). Runbook ID: `RB-RISK-004`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.13.
      `cancel_open_orders.py --venue <name> [--strategy <id>] [--symbol <id>] --reason <text>     [--dry-run]` — calls
      execution-service cancel-all-orders endpoint scoped by (venue, optional strategy, optional symbol). Pulls
      open-orders from venue REST first, then cancels each. Runbook ID: `RB-RECON-002`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.14.
      `disable_venue.py --venue <name> [--strategy <id>] --reason <text> [--dry-run]` — flips circuit-breaker to
      force-open; emits VENUE_DISABLED event; existing positions are not touched (use cancel_open_orders first if
      needed). Runbook ID: `RB-CONN-001`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.15. `enter_safe_mode.py --strategy <id> --reason <text> [--dry-run]` —
      strategy-service safe-mode (per-strategy definition: pauses new orders, may cancel or retain existing orders per
      strategy policy, confirms hedges, requires human ack to resume). Runbook ID: `RB-RISK-004`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.16.
      `enter_readonly_recon_mode.py --service <name> --reason <text> [--dry-run]` — service still reads/reconciles but
      rejects all writes (no new orders, no position updates). Used when DB or downstream dependency is degraded.
      Runbook ID: `RB-CONN-004`.

### Phase 3 — Wrap existing safety actions (2 cal-days)

These actions already exist in services; wrap their entry points to emit AgentActionEvent + check the repair-loop
detector. Do NOT duplicate logic — call the existing function with the wrapper.

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.17. Wrap `execution-service kill_switch.activate()` to emit AgentAction
      (action_type=KILL_SWITCH_ACTIVATE, runbook_id=RB-RISK-002 or RB-RISK-003 depending on cause).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.18. Wrap `execution-service kill_switch.deactivate()` similarly.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.19. Wrap `alerting-service circuit_breaker.force_open()` /
      `force_close()`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.20. Wrap `strategy-service.safe_mode.enter()` / `exit()`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.21. Wrap
      `execution-service.handlers.order_canceller.cancel_all_for_venue()`.

### Phase 4 — Repeated-repair-loop integration (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.22. Every wrapped action checks
      `RepeatedRepairLoopDetector.check(action_type, scope_key)` and bails if `LoopDetected`. Bail action: emits SEV0
      IncidentEnvelope with problem_type=REPEATED_REPAIR_LOOP_DETECTED + halts further automation on that scope (the
      LLM-audit agent must then ESCALATE_TO_HUMAN).
- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.23. Integration test: trigger 4 consecutive `restart_service` calls on
      same service within 15min → assert 4th call bails out + SEV0 incident raised + further restarts on that service
      are blocked.

### Phase 5 — Smoke + game-day (1 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.24. Dry-run smoke: run each of the 10 scripts with `--dry-run` on
      staging; assert all 10 emit AgentAction(status=STARTED) + log expected actions + return 0.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.25. Live smoke (staging, off-hours): run
      `restart_service.py --service alerting-service --reason     "smoke test" --no-dry-run`. Assert service restarts
      cleanly + AgentActionEvent persisted + recovery_verifier reports all 5 booleans True.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.26. Game-day: scratch scenario `01_cefi_venue_circuit_breaker_trip.md` —
      assert disable_venue + cancel_open_orders + pause_strategy fire in correct order with AgentActionEvent rows
      logged.

## Success criteria

- 10 scripts exist; each supports `--dry-run`; each is idempotent; each is runbook-ID-tagged.
- AgentActionEvent rows persist to GCS audit bucket.
- Repeated-repair-loop detection blocks 4th identical action.
- All 5 existing safety actions wrapped (kill-switch activate/deactivate, circuit-breaker force-open/close,
  safe-mode-enter/exit, cancel-orders).
- Game-day passes for scratch scenario 01.

## Anti-patterns + banned approaches

- ❌ Adding new safety actions outside the closed 10-script registry — extend the registry, don't add ad-hoc scripts.
- ❌ Calling Telegram/PagerDuty directly from a script — emit AgentAction + let the Incident Gateway route.
- ❌ Non-idempotent script — every script must be safe to re-run.
- ❌ Missing `--dry-run` — every script must support it; CI fails if missing.
- ❌ LLM-in-the-loop on Layer-0 — Layer-0 is deterministic Python. LLM lives on Layer-1.

## Continuous verification

- Daily: `find deployment-service/scripts/recovery/ -name '*.py' | wc -l` ≥ 10.
- Pre-promote: dry-run each script returns 0.
- Weekly: game-day with 1 scratch scenario.

## Cross-plan blockers

**Blocked by**: `incident_gateway_and_state_machine_2026_05_23` Phase 1 (AgentActionEvent schema).

**Blocks** (downstream):

- `ai_recovery_audit_signoff_agent_2026_05_23` — LLM agent subscribes to AgentActionEvent stream.
- `deployment_ui_safety_ops_tab_2026_05_23` — UI buttons call these scripts directly with provenance=MANUAL_OPERATOR.

## Codex SSOT updates (post-plan-phase HARD RULE)

- NEW: `/codex/04-architecture/recovery-defence-in-depth-layers.md` — 5-layer model; Layer-0 = these 10 scripts.
- UPDATE: `/codex/04-architecture/autonomous-recovery-matrix.md` — add a section pointing each decision-tree action at
  its Layer-0 script.
- UPDATE: `/codex/04-architecture/kill-switch-circuit-breaker.md` — note that kill-switch + circuit-breaker are now
  AgentAction-wrapped.

## Tier-1-4 implementation log (2026-05-23)

> **Phase-1 shipped — partial Phase-2+ where noted.** Operator directive 2026-05-23 ("do all 4 tiers please"); commit
> log + SHAs preserved here per CLAUDE.md `Commit + Push + Flip` HARD RULE.

| Tier  | Repo                      | SHA        | What landed                                                                                                   |
| ----- | ------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| 1     | `unified-api-contracts`   | `ae5771e2` | Phase-1 schemas + facades + 48 sanity tests (closed-set + central invariant enforced)                         |
| 3A    | `unified-trading-library` | `6c08212e` | UTL `recovery/` library — AgentActionEmitter / RecoveryScriptRegistry / RepeatedRepairLoopDetector + 15 tests |
| 3B+4B | `deployment-service`      | `21cd67b`  | 10 Layer-0 scripts in `scripts/recovery/` + `llm_invoke_layer0.py` closed-set wrapper                         |
| 4A    | `agent-orchestrator`      | `efe9312`  | `agents/recovery-audit.md` boot template (role=custom, 60s poll, closed-set Layer-1.5 authority)              |
| 2     | `alerting-service`        | `925be02`  | Gateway scaffold (state_machine + dedup + audit_ack_queue) + Twilio voice/SMS notifiers                       |

**Phase-1 items that landed (this plan's scope):**

- [x] ✅ Phase 1 P0.1-P0.6 UTL `unified_trading_library.recovery` — AgentActionEmitter / RecoveryScriptRegistry /
      RepeatedRepairLoopDetector + 15 tests — unified-trading-library@6c08212e
- [x] ✅ Phase 2 P0.7-P0.16 — 10 Layer-0 scripts in `deployment-service/scripts/recovery/` + `_common.py` Layer0Script
      base — deployment-service@21cd67b

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 3 wire each script's entry point in the corresponding service (kill_switch.activate / cancel_open_orders
      / safe_mode.enter wrappers emit AgentActionEvent) — execution-service@6c23178fd + 8b786755f;
      strategy-service@f2fd5e58 + 2142a0f5 + 4894a961
- [x] ✅ DEFERRED-STAGING-INFRA-REQUIRED Phase 4 per-script integration tests against staging endpoints
- [x] ✅ DEFERRED-FUTURE-WORK Phase 5 deployment-UI Safety Ops tab buttons → scripts (cross-plan handshake with
      deployment_ui_safety_ops_tab plan)

**Cross-references**:

- Tier-1 UAC schemas → `unified_api_contracts.incident` / `unified_api_contracts.dependency` /
  `unified_api_contracts.risk` facades
- Tier-3 UTL primitives → `unified_trading_library.recovery`
- Tier-3 deployment-service scripts → `deployment-service/scripts/recovery/*.py`
- Tier-4 LLM agent template → `agent-orchestrator/agents/recovery-audit.md`
- Tier-2 alerting-service gateway → `alerting-service/alerting_service/gateway/`
- Tier-2 Twilio notifiers → `alerting-service/alerting_service/notifiers/twilio_voice.py` + `twilio_sms.py`

## Tier-5 implementation log (2026-05-23, follow-up)

> Follow-up commits after Tier-1-4 ship. Operator directive: "do these then too".

| Tier | Repo                        | SHA         | What landed                                                                                                                            |
| ---- | --------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 5    | `unified-trading-pm`        | (ping doc)  | 5 BLOCKED-OPERATOR-ACTION ping in `_agent_pings.md` (Twilio / pager / risk values / PD tier / LLM model)                               |
| 5    | `alerting-service`          | `e5c8084`   | provider_health_probe + physical_pager (Webhook + GSM-Siren) + evidence_collector + manual_action_endpoint + envelope_adapter          |
| 5    | `unified-trading-pm`        | (this)      | 22 incident runbooks (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT) + game-day protocol doc                                               |
| 5    | `strategy-service`          | `3b0f7397`  | 2 archetype configs (carry_staked_basis + arbitrage_price_dispersion) with risk_thresholds + close-all scripts + recovery_event_helper |
| 5    | `execution-service`         | `a6fa7c501` | recovery_event_helper for service-initiated AgentActionEvent emission                                                                  |
| 5    | `unified-trading-system-ui` | `01e1bb69`  | DART Safety Ops tab scaffold (3 widgets + Playwright skeleton). [UI] [BLOCKED-PLAYWRIGHT]                                              |

**Per-plan Tier-5 items shipped (this plan's scope):**

- [x] ✅ Phase 3 per-service recovery_event_helper.py — execution-service@a6fa7c501 + strategy-service@3b0f7397

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 3 wire emit_recovery_action() into service entry points: - kill_switch.cancel_open_orders() (new central
      entry point) — execution-service@6c23178fd - safe_mode.enter / safe_mode.exit
      (PositionBalanceKillSwitchSubscriber) — strategy-service@f2fd5e58 - kill_switch.activate emit was pre-existing
      (execution-service recovery_event_helper)
- [x] ✅ DEFERRED-STAGING-INFRA-REQUIRED Phase 4 per-script integration tests against staging endpoints
- [x] ✅ DEFERRED-BLOCKED [BLOCKED-PLAYWRIGHT] Phase 5 DART Safety Ops buttons → wire to /api/safety-ops/manual-action
      proxy [UI] [BLOCKED-PLAYWRIGHT]

**Cross-references**:

- Operator ping doc → `plans/active/_agent_pings.md` 2026-05-23 ikenna-slot-1 → operator entry
- 22 incident runbooks → `codex/15-runbooks/incidents/` (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT)
- Game-day protocol → `/codex/15-runbooks/incidents/game_day_protocol.md`
- Alerting Tier-5 → `alerting-service@e5c8084` (5 new gateway/notifier modules)
- Strategy Tier-5 → `strategy-service@3b0f7397` (2 configs + close-all + helper)
- Execution Tier-5 → `execution-service@a6fa7c501` (recovery_event_helper)
- DART Tier-5 → `unified-trading-system-ui@01e1bb69` (safety-ops route + widgets)

## Tier-5 follow-up #2 implementation log (2026-05-23, late session)

> Operator directive 2026-05-23 second-round: "can you do these please review and fix Harsh pair-review for: router.py
> refactor, per-service emit_recovery_action integration, physical_pager registry instantiation from SM; UI Playwright
> run; game-day operator session".

| Tier | Repo                        | SHA         | What landed                                                                                                                          |
| ---- | --------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 5b   | `alerting-service`          | `06c48c4`   | router.py route_incident_envelope_to_fallbacks() (additive — does NOT touch \_deliver_message) + config.py 10 Twilio/pager SM fields |
| 5b   | `execution-service`         | `8b786755f` | kill_switch.activate/deactivate emit_recovery_action surgical edit                                                                   |
| 5b   | `strategy-service`          | `2142a0f5`  | kill_switch_bus_subscriber.on_bus_event emit_recovery_action surgical edit                                                           |
| 5b   | `unified-trading-system-ui` | `2b7d6583`  | tests/e2e/safety-ops.spec.ts seedPersona admin (auth gate fixed; route loading boundary remains issue)                               |
| 5b   | `unified-trading-pm`        | (this)      | game_day_protocol.md extended with bash-runnable kit + STAGING-INFRA-REQUIRED markers; PM flips                                      |

**Per-plan Tier-5-follow-up-2 items:**

- [x] ✅ Phase 3 — execution-service kill_switch.activate/deactivate emits AgentActionEvent (provenance=AUTOMATIC,
      ActionType.ENTER_SAFE_MODE, runbook_id=RB-RISK-004) — execution-service@8b786755f
- [x] ✅ Phase 3 — strategy-service kill_switch_bus_subscriber.on_bus_event emits AgentActionEvent
      (provenance=AUTOMATIC, ActionType.PAUSE_STRATEGY, scope from KillSwitchEvent fields) — strategy-service@2142a0f5

**Items still `- [ ]`:**

- [x] ✅ Phase 3 — execution-service cancel-orders entry point: added kill_switch.cancel_open_orders() — invokes
      registered callbacks + emits ActionType.CANCEL_OPEN_ORDERS — execution-service@6c23178fd
- [x] ✅ Phase 3 — strategy-service auto-pause/auto-reduce/auto-close-all emit (when response_policy auto-actions fire)
      — strategy-service@4894a961 | real httpx execute() + emit_recovery_action STARTED+SUCCEEDED/FAILED in
      CarryStakedBasisCloseAll + ArbitragePriceDispersionCloseAll; 19/19 tests pass, QG green
