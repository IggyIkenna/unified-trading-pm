---
doc_type: plan
title: LLM Recovery-Audit-Signoff Agent (Layer-1) + Layer-1.5 Backup Actuator
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-service, e2e-testing, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related:
  [
    incident_gateway_and_state_machine_2026_05_23.md,
    /plans/archive/2026_05/agent_recovery_controller_layer0_deterministic_2026_05_23.md,
    /plans/archive/2026_05/audit_acknowledgement_sla_and_state_2026_05_23.md,
  ]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: brand-new
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 12.0
estimate_calibration_note: "Brand-new class. New `agent-orchestrator/agents/recovery-audit.md` agent template + new
  RecoveryAuditSignoff UAC

  schema + scoped script-execution authority. Baseline 12 = ~1 day per phase across 5 phases of careful safety-critical

  work. No multiplier — operator-added requirement; not in original target model.

  "
parent: master_to_live_defi_2026_05_23
locked_since: 2026-05-23
depends_on: [incident_gateway_and_state_machine_2026_05_23, agent_recovery_controller_layer0_deterministic_2026_05_23]
gates: ["master_to_live_defi_2026_05_23:Group-F"]
---

## Deferred work — migrated to:

- **Phase 5 P0.12 (launch recovery-audit agent on GCE VM)** → observability_master epic P3 (OPERATOR action: prod-VM
  launch + model=claude-opus-4-7 resolved; agent-orchestrator@10cee2b)
- **Phase 5 P0.13-P0.14 (synthetic smoke + DISPUTE game-day)** → observability_master epic P3 (STAGING-INFRA-REQUIRED:
  requires staging infrastructure + Twilio creds from operator)

# LLM Recovery-Audit-Signoff Agent (Layer-1) + Layer-1.5 Backup Actuator

> **🟢 SPAWNED 2026-05-23 from operator directive (gap audit + Q&A).** The operator's added requirement beyond
> `disaster_recovery.md`: "ai/lmm needs to be able to use scripts to drive things like restarts in case automation
> fails. AI audit every risk and recovery related event and sign off". This plan codifies that.

## Goal

A scoped LLM agent registered in `agent-orchestrator` as `role: custom, label: recovery-audit-signoff` that:

1. **Audits** every `AgentActionEvent` emitted by Layer-0 (the deterministic scripts from
   `agent_recovery_controller_layer0_deterministic_2026_05_23`).
2. **Signs off** by writing a `RecoveryAuditSignoff` doc to the audit-store per incident; verdict ∈
   `{APPROVED, APPROVED_WITH_NOTES, ESCALATE_TO_HUMAN, DISPUTE_AUTOMATED_ACTION}`.
3. **Acts as Layer-1.5 backup actuator** when Layer-0 deterministic script fails (action_status=FAILED) — has
   scope-limited authority to invoke the same closed-set of 10 Layer-0 scripts (no arbitrary shell, no new code
   execution). If LLM cannot recover, falls through to Layer-2 PagerDuty cascade.
4. **Disputes automated actions** when the audit reveals automation was wrong — `DISPUTE_AUTOMATED_ACTION` verdict
   forces incident state machine to `SAFE_MODE_ACTIVE` + SEV0 escalation regardless of recovery-confirmed signal.

The agent is NEVER on the critical path for Layer-0 (deterministic always runs first). It is a parallel observer +
backup actuator.

## Context

**Existing capability** (verified 2026-05-23):

- `agent-orchestrator/agents/monitor.md` — custom-role monitor pattern (watches external thing, posts chat to role=main
  on threshold breach). Template ready.
- `agent-orchestrator/agents/backup.md` — standby agent pattern.
- `agent-orchestrator` supports `role: custom` + CronCreate trigger every 60s + chat messaging.
- ScheduleWakeup pattern for cron-style polling.

**Missing for May-23**:

- No `recovery-audit.md` agent template.
- No `RecoveryAuditSignoff` UAC schema.
- No scope-limited script-execution authority for the LLM agent.
- No DISPUTE_AUTOMATED_ACTION → SAFE_MODE escalation path.

## Pre-audit (blast radius)

- NEW: `agent-orchestrator/agents/recovery-audit.md` — agent template.
- NEW: `unified_api_contracts/canonical/crosscutting/incident/recovery_audit.py` — `RecoveryAuditSignoff` Pydantic
  model + `SignoffVerdict` StrEnum.
- NEW: `deployment-service/scripts/recovery/llm_invoke_layer0.py` — wrapper that the LLM agent runs to invoke any of the
  10 Layer-0 scripts; enforces closed-set + emits provenance=LLM_LAYER15 on AgentActionEvent.
- TOUCH: `alerting-service/alerting_service/gateway/state_machine.py` — DISPUTE_AUTOMATED_ACTION verdict triggers forced
  transition to SAFE_MODE_ACTIVE.

## Phased execution DAG

### Phase 1 — UAC schema + audit-store path (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1.
      `unified_api_contracts/canonical/crosscutting/incident/recovery_audit.py`: - `SignoffVerdict` StrEnum: APPROVED |
      APPROVED_WITH_NOTES | ESCALATE_TO_HUMAN | DISPUTE_AUTOMATED_ACTION (closed 4-set). - `RecoveryAuditSignoff`
      Pydantic:
      `event_id, parent_incident_key, agent_id, timestamp, verdict, narrative,       layer0_action_event_ids: list[str], evidence_links: list[str], recommended_next_action: str | None,       confidence: float | None, llm_model: str, llm_session_id: str`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. Audit-store write path: `RecoveryAuditSignoff` writes to GCS via
      `resolve_bucket_name(kind='kill-switch-audit', ...)` with prefix
      `incidents/{YYYY-MM-DD}/{incident_key}/signoffs/{signoff_event_id}.json`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.3. UAC sanity tests: SignoffVerdict closed; DISPUTE_AUTOMATED_ACTION
      reachable from any `verdict`; confidence ∈ [0,1] if non-None.

### Phase 2 — agent-orchestrator template (2 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.4. New `agent-orchestrator/agents/recovery-audit.md` — modelled on
      `monitor.md`. Sections: - STEP 0: read `agents/RULES.md` +
      `/codex/04-architecture/recovery-defence-in-depth-layers.md`. - STEP 1: register as
      `role: custom, label: recovery-audit-signoff` on the machine running this Claude session. - STEP 2: subscribe to
      PubSub `agent-recovery-actions` topic (via gateway audit-store polling — every 30s). - STEP 3: for each new
      `AgentActionEvent`, fetch the parent IncidentEnvelope; read recent context (incident history, runbook,
      recovery_verification result); decide verdict; write RecoveryAuditSignoff; if verdict ≠ APPROVED, post chat to
      `role=main`. - STEP 4: every 60s tick — heartbeat with `last_msg="watching recovery actions"`. - STEP 5: if
      action_status=FAILED on most recent AgentActionEvent → enter Layer-1.5 mode: invoke
      `deployment-service/scripts/recovery/llm_invoke_layer0.py <action_type> <scope_args>` via Bash. NO arbitrary
      shell; only the wrapper script.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.5. Closed-set authority guard: `llm_invoke_layer0.py` validates that
      `action_type` is one of the 10 registered actions in `RecoveryScriptRegistry`; emits AgentActionEvent with
      `provenance=LLM_LAYER15`; rejects unknown action types with non-zero exit.

### Phase 3 — DISPUTE escalation path (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.6. `alerting-service/alerting_service/gateway/state_machine.py`:
      subscribe to RecoveryAuditSignoff stream. On verdict=DISPUTE_AUTOMATED_ACTION: force the parent incident to
      `SAFE_MODE_ACTIVE`; raise severity_hint to SEV0; immediately invoke `pause_strategy.py` for the affected strategy
      (Layer-0 script call with provenance=GATEWAY_DISPUTE).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.7. On verdict=ESCALATE_TO_HUMAN: ensure
      `human_operational_ack_required=True` + audit-ack-due-at is shortened to 1h (vs default 6h) so the human is paged
      sooner.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.8. On verdict=APPROVED_WITH_NOTES: incident continues to RESOLVED but the
      notes appear in DART Active Alerts panel as an info banner.
- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.9. Integration test: simulate AgentActionEvent for `enter_safe_mode` →
      assert LLM agent picks it up, writes signoff doc; force DISPUTE verdict → assert state machine transitions to
      SAFE_MODE_ACTIVE + pause_strategy invoked.

### Phase 4 — DART surface (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.10.
      `unified-trading-system-ui/components/widgets/safety/recovery-audit-feed.tsx` — shows last 50 RecoveryAuditSignoff
      entries; color-coded by verdict; deep-links to the parent incident.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.11. Each ack-queue row shows the LLM signoff verdict alongside the
      incident — operator's ack decision is informed by LLM verdict.

### Phase 5 — Launch + game-day (1 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.12. Launch the recovery-audit agent on the live-defi VM (e.g.
      `recovery-audit-20260523-100000` GCE instance, asia-northeast1-c, e2-standard-2, auto-shutdown disabled, runs
      indefinitely). Pre-flight: confirm AGENT_ORCHESTRATOR_URL + GH_PAT + AUDIT_STORE_BUCKET secrets in SM.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.13. Synthetic smoke: inject AgentActionEvent(action_type=restart_service,
      action_status=FAILED) → assert LLM agent (a) writes RecoveryAuditSignoff within 90s, (b) invokes
      `llm_invoke_layer0.py restart_service ...` as Layer-1.5 backup, (c) emits a new AgentActionEvent with
      provenance=LLM_LAYER15.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.14. Game-day: scenario `02_defi_chain_rpc_outage_solana.md` — Layer-0
      fails to failover (Solana RPC all-down) → assert LLM agent ESCALATE_TO_HUMAN verdict + Layer-1.5 attempts an
      alternate RPC + audit-ack shortened to 1h.

## Success criteria

- RecoveryAuditSignoff UAC schema lands + tests green.
- Agent registers + heartbeats + writes signoffs in staging.
- DISPUTE verdict forces SAFE_MODE transition.
- Layer-1.5 backup actuator can invoke Layer-0 scripts but only via the wrapper (no arbitrary shell).
- Synthetic smoke passes end-to-end.
- Game-day scenario 02 passes.

## Anti-patterns + banned approaches

- ❌ LLM agent runs arbitrary `bash` — only `llm_invoke_layer0.py` wrapper with closed-set action_type.
- ❌ LLM agent on Layer-0 critical path — Layer-0 is deterministic. LLM is parallel observer + Layer-1.5 backup only.
- ❌ APPROVED verdict short-circuits human audit ack — even APPROVED verdict still requires the 6h human ack per
  `audit_acknowledgement_sla_and_state_2026_05_23.md` HARD RULE per operator.
- ❌ Multiple recovery-audit agents — exactly ONE registered at a time (use `agent-orchestrator/agents/backup.md`
  pattern for hot-standby).
- ❌ LLM agent reads private keys, wallet seeds, signing secrets — closed-set audit-store + Layer-0 wrapper read-only
  scope.

## Continuous verification

- Daily: `curl <orchestrator>/api/agents | jq '.[] | select(.label=="recovery-audit-signoff")'` returns 1 row with
  `last_seen` < 5min ago.
- Daily: `gcloud storage ls gs://<audit-store>/incidents/$(date +%Y-%m-%d)/*/signoffs/ | wc -l` > 0 if any incidents
  occurred.
- Weekly: synthetic AgentActionEvent → verify signoff lands within 90s.

## Cross-plan blockers

**Blocked by**: `incident_gateway_and_state_machine_2026_05_23` Phase 1 (RecoveryAuditSignoff fits in the same UAC
incident schema directory) + `agent_recovery_controller_layer0_deterministic_2026_05_23` Phase 1-2 (Layer-0 scripts are
what the LLM audits and invokes).

**Blocks** (downstream):

- `audit_acknowledgement_sla_and_state_2026_05_23` — LLM signoff verdict feeds the audit-ack flow (informs human's 6h
  ack decision).
- `deployment_ui_safety_ops_tab_2026_05_23` — Safety Ops tab shows LLM verdict alongside manual override buttons.

## Codex SSOT updates

- NEW: `/codex/04-architecture/recovery-defence-in-depth-layers.md` — Layer-1 is this agent; Layer-1.5 is the backup
  actuator path.
- UPDATE: `agent-orchestrator/agents/RULES.md` — add `recovery-audit-signoff` to the canonical role list with
  scope-limited authority callout.

## Open questions

- Q1: Should the LLM agent run on Opus 4.7 (max thinking) or Sonnet 4.6 (cheaper but possibly less judgment-rich)?
  Recommendation: Sonnet 4.6 for the 60s polling tick, Opus 4.7 sub-spawn for DISPUTE candidates (i.e. when initial
  Sonnet read flags concern, escalate to Opus for the deeper analysis before posting verdict). Defer to operator.
- Q2: Should Layer-1.5 backup actuator be authorised to invoke ALL 10 Layer-0 scripts, or only the read-only subset
  (recon, freshness-check) with destructive scripts (cancel-orders, disable-venue) requiring human confirmation?
  Recommendation: all 10 with audit-event-prov=LLM_LAYER15 — but require typed-confirm-string from operator BEFORE LLM
  invokes `cancel_open_orders` / `enter_safe_mode` (in DART Safety Ops tab). Defer to operator.

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

- [x] ✅ Phase 1 P0.1-P0.3 UAC RecoveryAuditSignoff + SignoffVerdict (4-enum) + GCS audit-store path —
      unified-api-contracts@ae5771e2
- [x] ✅ Phase 2 P0.4 agent-orchestrator boot template `agents/recovery-audit.md` — agent-orchestrator@efe9312
- [x] ✅ Phase 2 P0.5 closed-set wrapper `deployment-service/scripts/recovery/llm_invoke_layer0.py` —
      deployment-service@21cd67b

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 3 P0.6-P0.9 DISPUTE_AUTOMATED_ACTION wiring — GatewayState.process_signoff forces SAFE_MODE_ACTIVE + SEV0
      via shortest allowed transition path; ESCALATE_TO_HUMAN shortens ack to 1h; POST /safety-ops/signoffs ingests
      verdicts; +tests. — alerting-service@39b6650
- [x] ✅ Phase 4 P0.10-P0.11 DART RecoveryAuditFeed widget — ui@a6f3924c+c9189563 (llm-audit-verdicts-feed.tsx, pw:L2 ✓)
- [x] ✅ DEFERRED-OPERATOR-ACTION Phase 5 P0.12-P0.14 launch agent on long-lived GCE VM + synthetic smoke + game-day
      scenario 02 DEFERRED 2026-05-23: requires prod-VM launch (operator action) + staging infrastructure. See lines
      267/272.

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

- [x] ✅ Phase 4 P0.10-P0.11 DART LLM Audit Verdicts feed widget SCAFFOLD — unified-trading-system-ui@01e1bb69 [UI]
      [BLOCKED-PLAYWRIGHT]

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 3 P0.6-P0.9 DISPUTE_AUTOMATED_ACTION wiring shipped — GatewayState.process_signoff + state_machine drive
      to SAFE_MODE_ACTIVE+SEV0 via shortest allowed path (BFS over ALLOWED_TRANSITIONS). — alerting-service@39b6650
- [x] ✅ Phase 5 P0.12 (model choice) — operator decided 2026-05-23: recovery-audit agent pinned to `claude-opus-4-7`
      (max thinking, 1M context) in the template. — agent-orchestrator main@10cee2b
- [x] ✅ DEFERRED-OPERATOR-ACTION Phase 5 P0.12 (launch) — launch recovery-audit agent on long-lived GCE VM — **OPERATOR
      action** (prod-VM launch; model now resolved = claude-opus-4-7). DEFERRED 2026-05-23.
- [x] ✅ Phase 5 P0.13-P0.14 (scripts) — game-day injection scripts shipped incl the DISPUTE→SAFE_MODE path
      (`inject_oracle_deviation.sh`, scenario 04) which exercises the recovery-audit DISPUTE verdict end-to-end in mock.
      — e2e-testing@b3401e5 + alerting-service@39b6650
- [x] ✅ DEFERRED-OPERATOR-ACTION Phase 5 P0.13-P0.14 (live run) — operator runs the DISPUTE scenario with `--staging`
      (STAGING-INFRA-REQUIRED). DEFERRED 2026-05-23: requires staging infrastructure.

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

- [x] ✅ Phase 4 P0.10-P0.11 DART RecoveryAuditFeed test infrastructure — seedPersona admin pattern in
      tests/e2e/safety-ops.spec.ts — unified-trading-system-ui@2b7d6583

**Items still `- [ ]`:**

- [x] ✅ Phase 4 — Playwright pw:L2 ✓ (4/4). LlmAuditVerdictsFeed renders the seeded RecoveryAuditSignoff entries
      (APPROVED + DISPUTE asserted). Backed by the real alerting-service `GET /safety-ops/recovery-audit-signoffs`
      endpoint (@53fb493) + the dev:mock fixtures; prior block was widgets crashing on the `{}` non-array, fixed via
      mock-handler seeding + `Array.isArray`. — unified-trading-system-ui@a6f3924c + alerting-service@53fb493 | pw:L2 ✓
      | regression: tests/e2e/safety-ops.spec.ts
