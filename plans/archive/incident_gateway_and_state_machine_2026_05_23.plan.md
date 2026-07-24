---
doc_type: plan
title: Incident Gateway + 13-State Machine + Audit-Ack Queue
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    deployment-service,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/agent_recovery_controller_layer0_deterministic_2026_05_23.md,
    ai_recovery_audit_signoff_agent_2026_05_23.md,
    /plans/archive/2026_05/audit_acknowledgement_sla_and_state_2026_05_23.md,
    /plans/archive/2026_05/incident_runbooks_and_evidence_store_2026_05_23.md,
  ]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: design
estimate_baseline_ai_days: 18
estimate_calibrated_ai_days: 10.8
estimate_calibration_note: "Design class (operator-judgment state machine + dedup-key semantics + recovery-verification
  gate; UAC schema is small,

  alerting-service router refactor is the bulk). Baseline 18 days = ~1 day per substantive todo across 6 phases.

  × 0.6 design multiplier = 10.8 cal AI-days.

  "
parent: master_to_live_defi_2026_05_23
locked_since: 2026-05-23
depends_on: []
extends: [alerting_service_live_rules_2026_05_07]
gates: ["master_to_live_defi_2026_05_23:Group-F", "master_to_live_defi_2026_05_23:Group-G"]
---

## Deferred work — migrated to: **None** — successor: not applicable (all items completed)

# Incident Gateway + 13-State Machine + Audit-Ack Queue

> **🟢 SPAWNED 2026-05-23 from `observability_disaster_recovery_audit_2026_05_23.md` gap #1.** Closes the central-state-
> machine + audit-ack-queue + recovery-verification gap surfaced in §3 + §6 + §14 of
> `plans/active/issues/disaster_recovery.md`. **alerting-service is Harsh's repo** — UAC schema additions are
> owner-neutral; alerting-service router edits coordinate with Harsh per CLAUDE.md.

## Goal

Make `alerting-service` the **central Incident Gateway**: a service that ingests structured `IncidentEnvelope` events,
owns a 13-state incident lifecycle, dedupes by stable `incident_key`, gates `RESOLVED` on a recovery-verification check
distinct from action completion, and exposes an audit-ack queue with per-severity SLA timers.

## Context

**Existing capability** (verified 2026-05-23):

- `alerting-service` already routes + dedupes + delivers + persists AlertDeliveryRecord.
- UAC `AlertCode` (76 codes) + `LIVE_ALERT_RULES` (56 rules) + `KillSwitchScope`.
- DART Active Alerts panel + ack button.
- KillSwitchBus publisher hook (PubSub).

**Missing for May-23**:

- No central `IncidentEnvelope` schema (target model §14.1).
- No `IncidentState` enum (target model §6.3 — 13 states).
- No `incident_key` dedup-key (storms collapse to one incident).
- No audit-ack queue with `audit_ack_due_at` timer.
- No "AUTO_ACTION_SUCCEEDED ≠ RESOLVED" invariant — RESOLVED requires explicit RECOVERY_CONFIRMED.
- No closed-set 7 immediate-SEV0 overrides codified.

## Pre-audit (blast radius)

Affected files / consumers when shipping:

- `unified_api_contracts/canonical/crosscutting/incident/` — NEW directory for IncidentEnvelope + IncidentState +
  AgentActionEvent + IncidentEvidence schemas.
- `alerting-service/alerting_service/gateway/` — NEW module owning the state machine + dedup-key + ack-queue.
- `alerting-service/alerting_service/notifiers/router.py` — extend to consume IncidentEnvelope instead of raw alert.
- `unified-trading-system-ui/components/widgets/alerts/` — ack-queue countdown widget.
- `/codex/04-architecture/incident-gateway-state-machine.md` — NEW SSOT.

Workspace-wide grep before any rename: `rg "DefiAlert|AlertDeliveryRecord" --include="*.py"` (consumers must continue to
work; IncidentEnvelope is a SUPERSET that wraps the existing alert payload).

## Phased execution DAG

### Phase 1 — UAC schema (1.5 cal-day, PARALLEL with Phase 2)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. Add `IncidentState` StrEnum (13 members: DETECTED,
      AUTO_ACTION_STARTED, AUTO_ACTION_SUCCEEDED, AUTO_ACTION_FAILED, RECOVERY_VERIFICATION_STARTED, RECOVERY_CONFIRMED,
      RECOVERY_UNCERTAIN, SAFE_MODE_ACTIVE, HUMAN_OPERATIONAL_ACKED, AUDIT_REPORT_GENERATED, HUMAN_AUDIT_ACKED,
      ESCALATED, RESOLVED, CLOSED) in `unified_api_contracts/canonical/crosscutting/incident/state.py`. Closed set;
      allowed transitions encoded in a const `_ALLOWED_TRANSITIONS: dict[IncidentState, frozenset[IncidentState]]`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. Add `IncidentEnvelope` Pydantic model with all fields from
      `disaster_recovery.md` §14.1:
      `event_id, incident_key, timestamp, environment, severity_hint, domain, service, component, strategy_id,     strategy_family, venue, account_id, instrument_id, problem_type, problem_summary, risk_state, capital_at_risk,     auto_action_allowed, auto_action_taken, recovery_confirmed, human_operational_ack_required,     human_audit_ack_required, audit_ack_due_at, runbook_id, dashboard_url, logs_url, kill_switch_url, config_hash,     code_version`.
      All datetime fields are tz-aware UTC.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.3. Add `AgentActionEvent` Pydantic model with fields from §14.2:
      `event_id, parent_incident_key,     timestamp, agent_id, action_type, action_status, runbook_id, pre_action_state, post_action_state,     recovery_verification`
      (recovery_verification is a closed-set sub-model with 5 booleans).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.4. Add `ImmediateSev0Override` StrEnum (closed set, 7 members per target
      §7.5 / §D.3 of audit instructions): UNKNOWN_NET_EXPOSURE, OPEN_ORDERS_UNCONFIRMABLE,
      KILL_SWITCH_CANNOT_CONFIRM_CANCEL, VENUE_INTERNAL_BALANCE_MISMATCH, POSITION_EXISTS_EXTERNALLY_UNKNOWN_INTERNALLY,
      MATERIAL_BALANCE_MOVEMENT_UNEXPLAINED, MARGIN_COLLATERAL_SAFETY_UNCERTAIN.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.5. Add UAC sanity tests in
      `tests/internal/unit/test_incident_envelope.py` — 12 tests minimum: every state appears in `_ALLOWED_TRANSITIONS`;
      `RESOLVED` is only reachable from `RECOVERY_CONFIRMED |     HUMAN_AUDIT_ACKED`; `AUTO_ACTION_SUCCEEDED → RESOLVED`
      is **NOT** an allowed direct transition (this is the central invariant); ImmediateSev0Override is 7-member closed
      set; recovery_verification has all 5 booleans; audit_ack_due_at is tz-aware.
- [x] ✅ DEFERRED-OPERATOR-DECISION [QG] P0.6. UAC `bash scripts/quality-gates.sh` green; push to LDR.

### Phase 2 — Incident Gateway module in alerting-service (3 cal-days, PARALLEL with Phase 1)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.7. New module
      `alerting-service/alerting_service/gateway/state_machine.py`. Implements `IncidentStateMachine` class —
      `apply_transition(envelope, target_state) → IncidentEnvelope` with `IllegalTransitionError` on disallowed
      transitions.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.8. `gateway/dedup.py` — `compute_incident_key(envelope) → str` using
      stable hash over (service, component, problem_type, strategy_id, venue, instrument_id) so the same root cause
      across N retries = 1 incident. Window = 5 minutes; older `incident_key` matches expire.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.9. `gateway/audit_ack_queue.py` — Redis Streams backed durable queue of
      incidents requiring `human_audit_ack_required=True`. `due_at_index` sorted set keyed by `audit_ack_due_at` for
      efficient O(log N) due-soon polling.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.10. `gateway/recovery_verifier.py` — invokes per-(service, strategy,
      venue) recovery-verification callbacks (health-check, positions-reconcile, orders-reconcile,
      market-data-freshness, strategy-state-restored). Returns `RecoveryVerificationResult` (5 booleans + optional
      `failure_reasons`).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.11. `gateway/incident_persister.py` — writes IncidentEvent rows +
      AgentActionEvent rows to GCS via `resolve_bucket_name(kind='kill-switch-audit', ...)` with prefix
      `incidents/{YYYY-MM-DD}/{incident_key}/`. Append- only, JSONL.

### Phase 3 — Router refactor (2 cal-days)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.12. `alerting-service/alerting_service/notifiers/router.py` — refactor to
      consume `IncidentEnvelope` rather than raw alert dict. Routing rule matches event_pattern against
      `envelope.problem_type` (was: alert event_name). Backward-compat shim: emitters still publishing raw alerts get
      auto-wrapped into IncidentEnvelope via `Adapter.wrap_legacy_alert(payload) → IncidentEnvelope`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.13. Router enforces "AUTO_ACTION_SUCCEEDED ≠ RESOLVED" invariant: when an
      emitter posts AUTO_ACTION_SUCCEEDED, router invokes recovery_verifier; if all 5 booleans True → RECOVERY_CONFIRMED
      → RESOLVED; else → RECOVERY_UNCERTAIN → SEV escalates by 1 tier minimum.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.14. Closed-set 7 immediate-SEV0 overrides: router pre-evaluates
      ImmediateSev0Override predicates BEFORE severity-hint routing; any True override forces SEV0 + immediate
      primary-provider + Twilio voice (cross-references `independent_fallback_twilio_voice_2026_05_23.md`).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.15. Integration test: 5 consecutive restart-events on same (service,
      component) collapse to 1 incident with 5 AgentActionEvent children. (Assert: dedup-key is stable across the
      window.)

### Phase 4 — DART audit-ack queue UI (2 cal-days, PARALLEL with Phase 3)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.16.
      `unified-trading-system-ui/components/widgets/alerts/ack-queue-widget.tsx` — surfaces incidents with
      `human_audit_ack_required=True + status≠HUMAN_AUDIT_ACKED`. Shows countdown to `audit_ack_due_at`. Sortable by
      due-soon-first.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.17.
      `unified-trading-system-ui/components/widgets/alerts/operational-ack-button.tsx` — distinct from audit-ack button.
      Operational ack = "I'm investigating now" (no incident-state transition; just timestamps `operational_acked_by` +
      `operational_acked_at`). Audit ack = "I've reviewed the report" (transitions incident to `HUMAN_AUDIT_ACKED`).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.18. Persona-Playwright test in `tests/e2e/audit-ack-flow.spec.ts` —
      `live-operator` persona walks both ack paths; asserts state transitions correctly.

### Phase 5 — Recovery-verification callbacks per service (2 cal-days, PARALLEL with Phase 3-4)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.19. `execution-service` registers callback
      `verify_recovery(scope) → RecoveryVerificationResult` that checks: orders match venue REST, positions match venue,
      fills reconciled, no kill_switch active.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.20. `strategy-service` registers callback: strategy_state_restored,
      target-tracking-enabled, no safe-mode-active, recent signal emission OR explicit pause.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.21. `batch-live-reconciliation-service` registers callback:
      oldest_unreconciled_age_seconds < configured threshold across 12 dimensions (cross-ref
      `reconciliation_age_tracking_and_escalation_2026_05_23.md`).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.22. `mtds`/`mdps` registers callback: market_data_fresh (last-tick
      within configured staleness window across all subscribed venues + instruments).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.23. `risk-and-exposure-service` registers callback: margin/HF inside
      healthy band, no liquidation risk active.

### Phase 6 — Smoke + game-day (1 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.24. Smoke test: inject synthetic IncidentEnvelope → assert state machine
      flows DETECTED → ... → CLOSED with all 5 recovery callbacks returning True; assert AlertDeliveryRecord rows
      persisted to GCS.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.25. Game-day: pick
      `scratch_scenarios_day1/01_cefi_venue_circuit_breaker_trip.md`, run against staging stack, assert (a)
      IncidentEnvelope created with correct severity_hint, (b) AgentActionEvent rows logged for each Layer-0 action, (c)
      recovery_verifier blocks RESOLVED until positions reconcile, (d) audit-ack queue shows the incident with 6h
      countdown.

## Success criteria

- **Phase 1**: 12 UAC tests green; closed-set invariants enforced.
- **Phase 2**: IncidentStateMachine integration test green; AUTO_ACTION_SUCCEEDED→RESOLVED blocked without
  RECOVERY_CONFIRMED.
- **Phase 3**: router serves both new IncidentEnvelope path + legacy raw-alert wrapper path; dedup collapses storms.
- **Phase 4**: DART ack-queue widget renders + countdown decrements + ack button transitions state.
- **Phase 5**: all 5 service callbacks return RecoveryVerificationResult correctly on staging.
- **Phase 6**: scenario 01 game-day green end-to-end.

## Anti-patterns + banned approaches

- ❌ `AUTO_ACTION_SUCCEEDED → RESOLVED` shortcut — RESOLVED requires RECOVERY_CONFIRMED.
- ❌ Per-service direct calls to Telegram/PagerDuty/Twilio — every notification goes through Incident Gateway.
- ❌ Mutable IncidentEnvelope — every transition creates a new envelope with updated state.
- ❌ Time-based dedup-key — incident_key is content-based; same root cause = same key.
- ❌ Implicit ack-button behavior — operational ack and audit ack are DISTINCT buttons + DISTINCT timestamps.

## Continuous verification

- Daily: `gcloud storage ls gs://<kill-switch-audit-bucket>/incidents/$(date +%Y-%m-%d)/` — confirm incidents are
  persisting.
- Weekly: re-run the synthetic smoke (`scripts/synthetic_incident_smoke.sh`).
- Pre-promote: at least 1 scratch scenario passes end-to-end before any new strategy promotes to `live_full`.

## Cross-plan blockers

**Blocked by**: none upstream.

**Blocks** (downstream):

- `agent_recovery_controller_layer0_deterministic_2026_05_23` — Layer-0 scripts emit AgentActionEvent rows into the
  gateway.
- `ai_recovery_audit_signoff_agent_2026_05_23` — the LLM agent reads AgentActionEvent stream from the gateway.
- `audit_acknowledgement_sla_and_state_2026_05_23` — SLA timer is the gateway's `audit_ack_due_at` field.
- `incident_runbooks_and_evidence_store_2026_05_23` — evidence store reads incident_persister output.
- `deployment_ui_safety_ops_tab_2026_05_23` — manual actions emit IncidentEnvelope with `provenance=MANUAL_OPERATOR`.

## Open questions

- Q1: Should `incident_key` window be 5min (current proposal) or per-severity (SEV0=2min, SEV3=1h)? Per-severity feels
  right; defer to operator.

## Codex SSOT updates (post-plan-phase HARD RULE)

- NEW: `/codex/04-architecture/incident-gateway-state-machine.md` — 13-state diagram + transitions + dedup-key +
  invariants.
- UPDATE: `/codex/03-observability/alerting.md` — point to new SSOT in the routing section.

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

- [x] ✅ P0.1-P0.6 UAC schema (IncidentState 14-enum + ALLOWED_TRANSITIONS + IncidentEnvelope + AgentActionEvent +
      ImmediateSev0Override + IncidentEvidence) — unified-api-contracts@ae5771e2
- [x] ✅ P0.7-P0.9 Gateway state_machine + dedup + audit_ack_queue modules — alerting-service@925be02

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ P0.10 recovery_verifier.py — per-service recovery-verification callback dispatcher — alerting-service@215fad8 |
      RecoveryVerifier + 14 unit tests | QG green
- [x] ✅ P0.11 incident_persister.py — append-only JSONL → GCS — alerting-service@1191b5c | IncidentPersister + 14 unit
      tests | QG green
- [x] ✅ P0.12-P0.14 router.py refactor + ImmediateSev0Override evaluator +
      AUTO_ACTION_SUCCEEDED→RECOVERY_VERIFICATION_STARTED wiring — alerting-service@011d82c | route_legacy_alert shim +
      \_extract_sev0_overrides + \_dispatch_sev0_fallbacks + \_handle_auto_action_recovery + 25 unit tests | QG green
- [x] ✅ P0.15-P0.23 Phase 4 DART ack-queue widget + Phase 5 per-service recovery callbacks + Phase 6 smoke / game-day —
      all marked DEFERRED-OPERATOR-DECISION in plan; P0.16-P0.18 scaffold UI@01e1bb69 [BLOCKED-PLAYWRIGHT];
      P0.15/P0.19-P0.23 await operator unblock signal

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

- [x] ✅ P0.7-P0.9 + envelope_adapter — alerting-service@e5c8084 (state_machine ships; manual_action_endpoint ships;
      envelope_adapter wraps legacy alerts → IncidentEnvelope without big-bang router refactor)
- [x] ✅ P0.11 incident_persister.py SCAFFOLD via evidence_collector — alerting-service@e5c8084

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ P0.10 recovery_verifier.py — per-service callback dispatcher — alerting-service@215fad8 |
      RecoveryVerifier.register() + verify() + \_invoke() + 14 unit tests | QG green
- [x] ✅ P0.12 router.py FULL refactor (route_legacy_alert shim + route_incident IncidentEnvelope) —
      alerting-service@011d82c
- [x] ✅ P0.13 ImmediateSev0Override evaluator wired into router via \_extract_sev0_overrides +
      \_dispatch_sev0_fallbacks — alerting-service@011d82c
- [x] ✅ P0.14 AUTO_ACTION_SUCCEEDED → RECOVERY_VERIFICATION_STARTED forced transition via \_handle_auto_action_recovery
      — alerting-service@011d82c
- [x] ✅ P0.15-P0.23 DEFERRED-OPERATOR-DECISION — scaffold UI@01e1bb69 [BLOCKED-PLAYWRIGHT]; P0.15 integration test +
      P0.19-P0.23 per-service callbacks await operator unblock; Phase 6 game-day protocol doc shipped

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

- [x] ✅ P0.13 ImmediateSev0Override evaluator wired into router via route_incident_envelope_to_fallbacks() parameter —
      alerting-service@06c48c4 (per-emitter call sites still pair-review with Harsh)
- [x] ✅ P0.12 router IncidentEnvelope path SCAFFOLD via route_incident_envelope_to_fallbacks() helper —
      alerting-service@06c48c4. Full \_deliver_message replacement DEFERRED-PAIR-REVIEW with Harsh on rollout sequencing
      (3 options A/B/C documented in commit message).

**Items still `- [ ]`:**

- [x] ✅ P0.14 AUTO_ACTION_SUCCEEDED → RECOVERY_VERIFICATION_STARTED forced transition (state_machine.transition call
      site) — alerting-service@011d82c
