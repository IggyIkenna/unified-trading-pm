---
doc_type: audit-instruction
title: observability_master_audit_instructions
summary:
  Weekly observability audit — alerting-service, incident gateway (13-state lifecycle + audit-ack queue), the 5-layer
  recovery defence-in-depth (L0 deterministic Python → L1 LLM signoff → L2 PagerDuty → L3 Twilio voice → L4 pager → L5
  human ack), kill-switch/circuit-breaker, reconciliation-age tracking, alert-provider fallback, and runbook governance
  (owner/cadence/verifier/last_executed required); every service must emit STARTED/STOPPED/FAILED via ServiceBootstrap.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, alerting-service, deployment-service, deployment-ui, execution-service, strategy-service]
scope: [engineer, admin]
tags: [audit, observability, monitoring, self-healing, escalation, runbook, slack]
related: []
created: 2026-05-22
tier: L4
parent_epic: observability_master
cadence: weekly (minimum)
verifier:
lifespan:
type: audit-instructions
epic: observability_master
assigned_vm: vm-cross-cutting
last_updated: 2026-05-23
---

# Observability Master — Audit Instructions

## Epic Scope

alerting-service, monitoring hooks, telemetry pipeline, **incident gateway** (state machine + audit-ack queue), **agent
recovery controller** (Layer-0 deterministic scripts + Layer-1.5 LLM backup actuator), **LLM recovery-audit-signoff
agent**, **reconciliation age tracking**, **drawdown/liquidation policy + strategy risk config**, **connectivity
dependency buffers**, **alert-provider health + independent fallback (Twilio voice)**, **physical pager layer**,
**deployment-UI safety-ops tab**, 3am auto-recovery scripts, QG snapshot cron, runbook governance
(owner/cadence/verifier/last_executed fields required). Every service must emit STARTED/STOPPED/FAILED via
`ServiceBootstrap`.

Codex SSOTs governing this epic:

| Doc                                                          | Owns                                                                                                                                                |
| ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/codex/03-observability/alerting.md`                        | AlertSeverity (T1/T2/T3/T4 ↔ CRITICAL/HIGH/WARN/INFO) → channel routing                                                                             |
| `/codex/04-architecture/autonomous-recovery-matrix.md`       | Decision tree — every failure scenario × every recovery action                                                                                      |
| `/codex/04-architecture/kill-switch-circuit-breaker.md`      | Kill-switch state machine; circuit-breaker per-venue; auto-deactivation                                                                             |
| `/codex/04-architecture/recovery-defence-in-depth-layers.md` | **NEW 2026-05-23** — 5-layer model: L0 deterministic Python → L1 LLM audit/signoff → L2 PagerDuty → L3 Twilio voice → L4 pager → L5 human audit ack |
| `/codex/04-architecture/incident-gateway-state-machine.md`   | **NEW 2026-05-23** — 13-state incident lifecycle (DETECTED → … → CLOSED); audit-ack queue                                                           |
| `/codex/05-infrastructure/disaster-recovery.md`              | RTO/RPO targets, Tier 0-3 recovery, restore from manifest                                                                                           |
| `/codex/15-runbooks/physical-pager-layer.md`                 | **NEW 2026-05-23** — Pager device comparison, webhook prototype, Twilio voice bridge                                                                |
| `/codex/05-infrastructure/live-deployment-monitoring.md`     | Per-archetype heartbeat thresholds; STARTED/progress/STOPPED/FAILED event cadence                                                                   |
| `/codex/15-runbooks/alerting/pagerduty-escalation-policy.md` | Ikenna 14:30–02:30 UK / Harsh 02:30–14:30 UK; escalation ladder                                                                                     |
| `/codex/15-runbooks/alerting/audit-acknowledgement-flow.md`  | **NEW 2026-05-23** — 6h ack SLA + secondary-human-escalation + founder fallback                                                                     |
| `/codex/02-data/data-pipeline-correctness-hard-rule.md`      | Layer freeze on RED data audit; slot-reassignment trigger                                                                                           |

## Triggers

- Weekly (minimum cadence)
- After any recovery script change
- After any new alerting rule lands in UAC `LIVE_ALERT_RULES`
- After any new venue / archetype / strategy goes live
- After any production incident (post-incident retro feeds back into thresholds)
- When QG snapshot cron shows stale (last run > 24h ago)
- After any new service added to the workspace (must be wired to alerting + ServiceBootstrap)
- When the LLM recovery-audit-signoff agent posts a `RECOVERY_AUDIT_RED` event
- Pre-cutover snapshot before every promote to `live_full`

## Checklist

### Section A — Original baseline (5 items)

- [ ] (a) **QG snapshot cron healthy**: Cloud Scheduler job for QG snapshots is ENABLED and last run < 24h ago. Check:
      `qg_snapshot_cron_stale_2026_05_18.md`. Run: `gcloud scheduler jobs describe` for relevant job.
- [ ] (b) **3am auto-recovery tested**: recovery script runs end-to-end on dev VM without errors. Find:
      `rg "auto.recovery|3am" unified-trading-pm/scripts/ --include="*.sh" -l`. Run: script in dry-run mode if
      available.
- [ ] (c) **alerting-service covers strategy + execution failures**: alerting-service is wired to receive FAILED events
      from strategy-service and execution-service. Grep:
      `rg "alerting|alert_service" strategy-service/ execution-service/ --include="*.py"` — verify call sites.
- [ ] (d) **Telemetry covers ServiceBootstrap events**: STARTED / STOPPED / FAILED events from all services are picked
      up by the telemetry pipeline. Grep: `rg "ServiceBootstrap" --include="*.py"` across all service dirs.
- [ ] (e) **Runbook fields complete**: every runbook has `owner`, `cadence`, `verifier`, `last_executed` fields.

### Section B — Incident Gateway + state machine

- [ ] (B.1) **Incident Gateway lives in alerting-service**: exactly ONE central path that ingests structured incident
      events (`IncidentEnvelope`); no service bypasses with direct Slack/Telegram/PagerDuty calls. Grep:
      `rg "TelegramClient|PagerDutyClient|requests.*slack" --include="*.py" --glob '!alerting-service/**'` — count
      should be 0 outside alerting-service.
- [ ] (B.2) **13-state machine implemented**: DETECTED → AUTO_ACTION_STARTED → AUTO_ACTION_SUCCEEDED |
      AUTO_ACTION_FAILED → RECOVERY_VERIFICATION_STARTED → RECOVERY_CONFIRMED | RECOVERY_UNCERTAIN → SAFE_MODE_ACTIVE |
      HUMAN_OPERATIONAL_ACKED → AUDIT_REPORT_GENERATED → HUMAN_AUDIT_ACKED | ESCALATED → RESOLVED → CLOSED. Grep:
      `rg "class IncidentState|IncidentState\." --include="*.py"`. Verify: 13 distinct enum members.
- [ ] (B.3) **`AUTO_ACTION_SUCCEEDED ≠ RESOLVED`**: process-restart success does NOT auto-close incident; recovery
      verification is a separate gate. Test: integration test asserts that a clean restart fires
      `RECOVERY_VERIFICATION_STARTED` BEFORE incident state can transition to `RESOLVED`.
- [ ] (B.4) **Audit-ack queue**: incidents requiring `human_audit_ack_required=True` land in a queryable queue with
      `audit_ack_due_at` timestamp. Grep: `rg "audit_ack_due_at|audit_ack_queue" --include="*.py"`. UI surface: DART
      cockpit Active Alerts panel shows ack-due countdown.
- [ ] (B.5) **Incident dedup-key stability**: same root cause = same `incident_key` across retries. Test: 5 consecutive
      restarts on same service yield 1 incident with 5 action-event children, not 5 incidents.

### Section C — Agent Recovery Controller (5-layer defence-in-depth)

- [ ] (C.1) **Layer-0 deterministic scripts ship for closed-set actions**: restart-service, restart-container,
      redeploy-known-good, resize-machine-after-OOM, failover-feed, pause-strategy, cancel-open-orders, disable-venue,
      enter-safe-mode, enter-readonly-recon-mode. Each MUST be idempotent + dry-run testable + runbook-ID-tagged. Find:
      `find deployment-service/scripts/recovery/ -name '*.sh' -o -name '*.py'`. Count: 10 distinct scripts.
- [ ] (C.2) **Each recovery action emits structured `AgentActionEvent`**: with `action_type`, `runbook_id`,
      `pre_action_state`, `post_action_state`, `recovery_verification` (5 booleans). Grep:
      `rg "AgentActionEvent|emit_agent_action" --include="*.py"`.
- [ ] (C.3) **Layer-1 LLM audit agent registered**: a `role=custom` agent in `agent-orchestrator` named
      `recovery-audit-signoff` subscribes to AgentActionEvent stream + writes RecoveryAuditSignoff doc per event. Check:
      `curl <orchestrator>/api/agents` returns 1 agent with `label="recovery-audit-signoff"` and last_seen < 5min.
- [ ] (C.4) **Layer-1.5 LLM-as-backup-actuator**: when Layer-0 deterministic script fails (action_status=FAILED), the
      LLM recovery agent has explicit authority to execute the script directly via a worker subagent. Grep:
      `rg "AGENT_AUTHORITY_LAYER15|llm_recovery_backup" --include="*.py"`. Verify: scope-limited.
- [ ] (C.5) **Repeated repair loop detection**: 3+ identical recovery actions within sliding window → automatic
      escalation to SEV0 + halts further automation on that scope. Test: 4× simulated restart triggers SEV0 + pages
      on-call.

### Section D — Severity + routing model

- [ ] (D.1) **SEV0/SEV1/SEV2/SEV3 mapped to existing AlertSeverity (CRITICAL/HIGH/WARN/INFO)**: with the live-risk-vs-
      recovery-certainty matrix from `disaster_recovery.md` §5. Grep mapping consistency across UAC + alerting-service +
      DART.
- [ ] (D.2) **`AUTO_ACTION_SUCCEEDED + recovery_confirmed=True` ≠ wake-up**: routing rule asserts SEV2 (Telegram +
      audit-ack) when recovery proven, SEV0 (PagerDuty + escalation + Twilio voice + pager) when uncertain.
- [ ] (D.3) **Immediate SEV0 overrides codified**: closed-set 7 — UNKNOWN_NET_EXPOSURE, OPEN_ORDERS_UNCONFIRMABLE,
      KILL_SWITCH_CANNOT_CONFIRM_CANCEL, VENUE_INTERNAL_BALANCE_MISMATCH, POSITION_EXISTS_EXTERNALLY_UNKNOWN_INTERNALLY,
      MATERIAL_BALANCE_MOVEMENT_UNEXPLAINED, MARGIN_COLLATERAL_SAFETY_UNCERTAIN. Grep:
      `rg "ImmediateSev0Override|sev0_override" --include="*.py"`.

### Section E — Reconciliation policy

- [ ] (E.1) **Age-tracked reconciliation**: every reconciliation issue carries `first_seen_at`, `last_seen_at`,
      `event_time`, `venue_trade_time`, `internal_trade_time`, `last_successful_reconciliation_at`,
      `unreconciled_age_seconds`, `oldest_unreconciled_{trade,order,position}_age_seconds`.
- [ ] (E.2) **12 reconciliation dimensions tracked separately**: orders, fills, positions, balances, funding, fees,
      transfers, borrow/lending, collateral, margin-mode-and-leverage, strategy-allocation, account-aggregate. Grep:
      `rg "ReconciliationDimension|reconciliation_dimension" --include="*.py"`.
- [ ] (E.3) **15-minute human-investigation threshold**: unresolved > 15min auto-fires SEV1. Configurable per (venue,
      strategy, instrument_type, account).
- [ ] (E.4) **30-minute SEV0 threshold OR immediate-override-on-risk-live**.
- [ ] (E.5) **Reconciliation freezes affected scope**: new trading auto-freezes for (strategy, venue, symbol) tuple when
      recon risk is live.

### Section F — PnL drawdown + liquidation policy

- [ ] (F.1) **Per-strategy `risk_thresholds.pnl_drawdown` config**: 7 thresholds (warning, investigation,
      human_escalation, auto_pause, auto_reduce, auto_close_all, liquidation_risk). Every live strategy declares all 7.
- [ ] (F.2) **`expected_drawdown_model` per strategy**: closed-set basis (HISTORICAL_BACKTEST | LIVE_VOLATILITY | VAR |
      ES | MAX_ADVERSE_EXCURSION | CUSTOM) + confidence_level + lookback_window + regime_adjustment.
- [ ] (F.3) **`response_policy` per strategy**: 5 booleans declared (allow_agent_investigation, allow_auto_pause,
      allow_auto_reduce, allow_auto_close_all, require_human_for_resume).
- [ ] (F.4) **Drawdown investigation report**: agent emits 17-field report.
- [ ] (F.5) **Strategy-specific close-all script**: idempotent + dry-run testable + venue-specific + reduce-only-aware +
      cross-strategy-safe.
- [ ] (F.6) **Liquidation = always at least SEV1**: liquidation event detector with closed-set SEV0 escalation
      predicates.
- [ ] (F.7) **Liquidation investigation report** covers all 16 fields per `disaster_recovery.md` §9.4.
- [ ] (F.8) **Liquidation-risk pre-detection**: SEV0 on margin_ratio breach, liquidation_distance below threshold,
      collateral_transfer fail, ADL/insurance-fund risk, venue API margin uncertainty, price gap > model.

### Section G — Connectivity + dependency policy

- [ ] (G.1) **Dependencies classified into 5 classes**: EXECUTION_CRITICAL_EXTERNAL, MARKET_DATA_CRITICAL_EXTERNAL,
      INTERNAL_CONTROL_PLANE, INTERNAL_DATA_PLANE, ALERTING_AND_OBSERVABILITY.
- [ ] (G.2) **Per-dependency `dependency_health_policy` YAML**: every dependency declares dependency_id,
      dependency_class, expected_recovery_time_seconds, warning_buffer_seconds, human_investigation_buffer_seconds
      (default 900), hard_escalation_seconds, fallback_available, protected_mode_available.
- [ ] (G.3) **expected_time+15min escalation rule wired**: dep degraded > expected + 15min → SEV1; > hard OR fallback
      fails → SEV0.
- [ ] (G.4) **Fallback paths tested**: each `fallback_available=true` dep has an integration test.

### Section H — Restart / OOM / redeploy / scaling policy

- [ ] (H.1) **Clean restart with all-green recovery checks ≠ wake-up**: passes through audit-ack queue only.
- [ ] (H.2) **OOM with clean recovery = SEV2 + audit-ack-6h**.
- [ ] (H.3) **Repeated OOM (3+ in M minutes) or recovery uncertain = SEV1**.
- [ ] (H.4) **OOM affecting execution with exposure/order-state uncertain = SEV0**.
- [ ] (H.5) **Every redeploy event captures**: trigger_reason, previous_version, new_version, config_hash, image_digest,
      environment, services_affected, rollback_status, post_deploy_health_checks, reconciliation_status.

### Section I — Alert provider + notification tooling

- [ ] (I.1) **One primary incident provider** (PagerDuty per `alerting_service_live_rules_2026_05_07.md` Phase 4).
- [ ] (I.2) **Slack deprecated** per `/codex/03-observability/alerting.md`; verify no code path adds new Slack-only
      routes.
- [ ] (I.3) **Independent fallback = Twilio direct voice/SMS**: separate account + separate billing + direct API path
      from Incident Gateway. Verify: works when PagerDuty API is down (synthetic provider-outage test).
- [ ] (I.4) **Primary provider health checks**: continuous probe (can-reach-API, can-create-test-incident,
      billing-active, escalation-policy-enabled, on-call-populated). Emits `ALERTING_PROVIDER_DEGRADED` event when probe
      fails.

### Section J — Physical pager + final-mile fallback

- [ ] (J.1) **Comparison matrix docs**: `/codex/15-runbooks/physical-pager-layer.md` documents 4-6 candidates with
      price, webhook API path, pros/cons, recommended pick.
- [ ] (J.2) **Webhook prototype**: `PhysicalPagerNotifier` abstract interface + 4 vendor subclasses ship in
      alerting-service.
- [ ] (J.3) **Twilio voice bridge as permanent fallback**: Twilio voice triggers when SEV0 not acked within configured
      window — works even when device is not yet purchased.
- [ ] (J.4) **Physical-layer-only-for-SEV0-no-ack**: trigger rules explicit — physical alert fires ONLY for one of 5
      closed-set conditions.

### Section K — Audit acknowledgement + incident state

- [ ] (K.1) **6-hour audit-ack SLA default** + per-severity override (SEV0 minutes, SEV1 < 2h, SEV2 < 6h).
- [ ] (K.2) **Secondary-human escalation on unacked**: secondary → founder per escalation ladder.
- [ ] (K.3) **Operational ack vs audit ack distinct**: 2 distinct buttons + 2 distinct timestamps.

### Section L — Runbooks + evidence

- [ ] (L.1) **22 required runbooks present per `disaster_recovery.md` §15**: RB-INC-001/002/003, RB-RECON-001/002/003,
      RB-RISK-001/002/003/004, RB-CONN-001/002/003/004/005, RB-DEPLOY-001, RB-INFRA-001/002/003, RB-ALERT-001/002/003.
- [ ] (L.2) **Each runbook frontmatter has 4 governance fields**: owner, cadence, verifier, last_executed.
- [ ] (L.3) **Evidence store**: every material incident links to 14 evidence fields. Grep:
      `rg "IncidentEvidence|evidence_store" --include="*.py"`.

### Section M — Deployment-UI manual safety-ops tab

- [ ] (M.1) **Safety Ops tab exists in deployment-ui / DART**: surfaces 10 Layer-0 actions as buttons.
- [ ] (M.2) **Every manual safety action requires confirm-typed-string**.
- [ ] (M.3) **Every manual safety action creates an `IncidentEvent` with `provenance=MANUAL_OPERATOR`**.

### Section N — LLM recovery-audit-signoff agent

- [ ] (N.1) **Recovery-audit-signoff agent prompt template lives in `agent-orchestrator/agents/recovery-audit.md`**
      modeled on `monitor.md` + `backup.md`. Verifies `role: custom`, CronCreate trigger every 60s, scope-limited
      script-execution authority.
- [ ] (N.2) **Sign-off doc written to GCS audit bucket** per incident: `RecoveryAuditSignoff` carries verdict ∈
      {APPROVED, APPROVED_WITH_NOTES, ESCALATE_TO_HUMAN, DISPUTE_AUTOMATED_ACTION} + narrative + evidence links.
- [ ] (N.3) **DISPUTE_AUTOMATED_ACTION verdict auto-escalates**: forces SAFE_MODE_ACTIVE + SEV0 regardless of
      recovery-confirmed signal.
- [ ] (N.4) **LLM agent restart authority is scope-limited**: closed-set 10 Layer-0 scripts only; no arbitrary shell.

### Section O — End-to-End Defence-In-Depth Flow Verification (all 11 plans interlocking)

Each O-test exercises multiple plans simultaneously — these audits catch a plan shipping in isolation but failing to
compose with its neighbours.

#### O.1 — Normal-flow E2E (SEV2: auto-fixed, audit ack within 6h)

- [ ] (O.1.a) **Detection**: OOM watchdog emits IncidentEnvelope (provenance=AUTOMATIC, severity_hint=HIGH,
      problem_type=OOM_DETECTED, config_hash/code_version populated).
- [ ] (O.1.b) **Dedup-key stability**: 5 OOM events same service same 5-min window → 1 IncidentEnvelope with 5
      AgentActionEvent children.
- [ ] (O.1.c) **Layer-0 action**: `resize_machine_after_oom.py` invoked; AgentActionEvent STARTED → SUCCEEDED;
      recovery_verification 5-tuple recorded.
- [ ] (O.1.d) **State machine**: DETECTED → AUTO_ACTION_STARTED → AUTO_ACTION_SUCCEEDED → RECOVERY_VERIFICATION_STARTED
      → RECOVERY_CONFIRMED → AUDIT_REPORT_GENERATED. `AUTO_ACTION_SUCCEEDED → RESOLVED` direct transition FORBIDDEN.
- [ ] (O.1.e) **Layer-1 LLM signoff**: agent writes RecoveryAuditSignoff with APPROVED or APPROVED_WITH_NOTES.
- [ ] (O.1.f) **Audit-ack queue**: incident lands with `audit_ack_due_at = now + 6h`; DART Safety Ops shows countdown.
- [ ] (O.1.g) **Operator audit-acks within window**: HUMAN_AUDIT_ACKED → RESOLVED → CLOSED; Twilio voice + pager NOT
      triggered.

#### O.2 — Critical-flow E2E (SEV0: unresolved, full escalation ladder)

- [ ] (O.2.a) Recon age tracking fires: at 15min → SEV1; at 30min → SEV0 + freeze armed <5s.
- [ ] (O.2.b) Freeze enforced — execution preflight rejects new orders.
- [ ] (O.2.c) PagerDuty page to primary on-call.
- [ ] (O.2.d) No ack → secondary PagerDuty page after secondary_human_after_seconds.
- [ ] (O.2.e) Twilio voice fires at founder_after_seconds.
- [ ] (O.2.f) Physical pager fires (or Twilio bridge twice if device not configured).
- [ ] (O.2.g) LLM signoff verdict=ESCALATE_TO_HUMAN; audit-ack shortened to 1h.
- [ ] (O.2.h) Operator intervenes via Safety Ops tab; unfreeze succeeds.
- [ ] (O.2.i) Closure: HUMAN_AUDIT_ACKED → RESOLVED → CLOSED; evidence_store has all 14 fields.

#### O.3 — Dispute-flow E2E (LLM disputes automated action)

- [ ] (O.3.a) Layer-0 action fires → AgentActionEvent.
- [ ] (O.3.b) LLM signoff verdict=DISPUTE_AUTOMATED_ACTION + narrative.
- [ ] (O.3.c) State machine forces SAFE_MODE_ACTIVE regardless of recovery_verification; severity → SEV0.
- [ ] (O.3.d) pause_strategy invoked with provenance=GATEWAY_DISPUTE.
- [ ] (O.3.e) DART LLM Audit Verdicts panel shows DISPUTE entry.

#### O.4 — Layer-1.5 LLM-as-backup-actuator (Layer-0 script fails)

- [ ] (O.4.a) Layer-0 AgentActionEvent: action_status=FAILED.
- [ ] (O.4.b) LLM agent detects FAILED within 90s.
- [ ] (O.4.c) Layer-1.5 retry: LLM invokes `llm_invoke_layer0.py` wrapper; new AgentActionEvent with
      provenance=LLM_LAYER15.
- [ ] (O.4.d) **Closed-set authority enforced**: LLM cannot invoke arbitrary shell. Bogus action_type → non-zero exit +
      audit log flags attempt.
- [ ] (O.4.e) If Layer-1.5 fails: SEV0 + Layer-2/3/4 cascade.

#### O.5 — Alerting-provider-down E2E (Twilio takes over)

- [ ] (O.5.a) Provider health probe detects within 60s; emits `ALERTING_PROVIDER_DEGRADED`.
- [ ] (O.5.b) Router fallback-mode: SEV0 routes through Twilio voice + Telegram.
- [ ] (O.5.c) Operator gets voice call within 90s.
- [ ] (O.5.d) Probe returns 200 → fallback_mode=False → normal routing resumes.

#### O.6 — Repeated-repair-loop detection

- [ ] (O.6.a) First 3 restarts succeed individually.
- [ ] (O.6.b) 4th attempt blocked: LoopDetected; Layer-0 bails; SEV0 IncidentEnvelope.
- [ ] (O.6.c) Further restarts blocked; explicit operator override required.

#### O.7 — Drawdown auto-pause + investigation report

- [ ] (O.7.a) DrawdownEvent IncidentEnvelope; severity escalates per 7-threshold ladder.
- [ ] (O.7.b) Auto-pause (if response_policy.allow_auto_pause=True): Layer-0 pause_strategy.py fires.
- [ ] (O.7.c) DrawdownInvestigationReport with 17 fields lands in DART viewer.
- [ ] (O.7.d) LLM signoff verdicts APPROVED or DISPUTE based on report.
- [ ] (O.7.e) require_human_for_resume=True → auto-resume blocked.

#### O.8 — Liquidation event detection + investigation

- [ ] (O.8.a) LiquidationEventDetector fires SEV1 minimum.
- [ ] (O.8.b) Closed-set 7-trigger check → SEV0 if escalation predicate True.
- [ ] (O.8.c) LiquidationInvestigationReport written with 16 fields.
- [ ] (O.8.d) Liquidation cannot be silently ignored — AlertDeliveryRecord row MUST exist.

#### O.9 — Audit-ack SLA escalation ladder

- [ ] (O.9.a) At 2h SEV1: secondary-human PagerDuty page.
- [ ] (O.9.b) At 3h: founder Twilio voice call.
- [ ] (O.9.c) At 6h: physical pager fires.
- [ ] (O.9.d) Operator acks → escalation stops; audit_ack_escalation_history shows full ladder.

#### O.10 — Game-day across 3+ scratch scenarios (pre-cutover acceptance gate)

- [ ] (O.10.a) `01_cefi_venue_circuit_breaker_trip.md` — Layer-0 disable_venue / cancel_open_orders / pause_strategy.
- [ ] (O.10.b) `15_liquidation_proximity_auto_deleverage.md` — liquidation pre-detector + auto-deleverage.
- [ ] (O.10.c) `04_defi_oracle_deviation_30sigma.md` — KILL_SWITCH_ORACLE_DIVERGENCE + Twilio voice fallback.
- [ ] (O.10.d) Each scenario asserts ALL 7: Layer-0 acts within expected time; AgentActionEvent rows persist; LLM
      signoff lands non-DISPUTE; Layer-2/3 cascade fires if SEV0; ack-queue countdown with correct SLA; Safety Ops tab
      shows incident with manual override buttons; incident closes via HUMAN_AUDIT_ACKED.

### Section P — Inter-plan handshake checks (11 plans must compose)

- [ ] (P.1) **incident_gateway ↔ agent_recovery_controller**: AgentActionEvent schema (UAC) consumed by both; emitters
      vs consumers balanced.
- [ ] (P.2) **agent_recovery_controller ↔ ai_recovery_audit_signoff**: PubSub topic `agent-recovery-actions` has ≥1
      publisher + ≥1 subscriber.
- [ ] (P.3) **ai_recovery_audit_signoff ↔ incident_gateway**: DISPUTE verdict triggers SAFE_MODE_ACTIVE transition.
- [ ] (P.4) **reconciliation_age_tracking ↔ execution-service preflight**: RECON_FREEZE_ARMED event triggers freeze set
      update <5s.
- [ ] (P.5) **drawdown_liquidation_policy ↔ alerting-service**: per-strategy risk_thresholds load at strategy startup;
      LiquidationEventDetector subscribed to venue events.
- [ ] (P.6) **connectivity_dependency_buffer ↔ alerting-service**: dependency_health_policies.yaml drives the
      `evaluate_dependency_health` rule.
- [ ] (P.7) **audit_acknowledgement_sla ↔ ai_recovery_audit_signoff**: even APPROVED LLM verdict requires human audit
      ack — APPROVED incident NOT closed in audit-ack queue.
- [ ] (P.8) **independent_fallback_twilio ↔ incident_gateway**: TwilioVoice in AlertChannel; CRITICAL rules include it.
- [ ] (P.9) **physical_pager ↔ audit_acknowledgement_sla**: PhysicalPager triggered ONLY by 5 closed-set conditions
      reachable from the ack-escalation cron.
- [ ] (P.10) **incident_runbooks_evidence ↔ everything**: every IncidentEnvelope stamped with runbook_id + config_hash +
      code_version + runbook_version.
- [ ] (P.11) **deployment_ui_safety_ops ↔ incident_gateway**: manual actions flow through gateway (not direct service
      API calls).

### Section Q — Cross-domain audit composition

- [ ] (Q.1) Composes with `execution_master_audit_instructions.md`: kill-switch + cancel-orders Layer-0 wrappers
      cross-link with execution-service classify_venue_error checklist.
- [ ] (Q.2) Composes with `strategy_master_audit_instructions.md`: per-strategy risk_thresholds + close-all scripts
      integrate with strategy-service config schema.
- [ ] (Q.3) Composes with `dart_and_promote_master_audit_instructions.md`: Safety Ops tab lives in DART.
- [ ] (Q.4) Composes with `deployment_and_user_management_master_audit_instructions.md`: deployment-ui mirror of Safety
      Ops tab.

### Section R — Operator personae walkthroughs

- [ ] (R.1) **`live-operator` Cancel Open Orders flow**: opens modal, selects venue, types `CANCEL_ALL_binance`,
      confirms. Asserts IncidentEnvelope created with provenance=MANUAL_OPERATOR; AgentActionEvent persisted;
      RecoveryAuditSignoff written within 90s.
- [ ] (R.2) **`live-operator` DISPUTE flow**: triggers DISPUTE on an automated kill-switch activation. Asserts
      SAFE_MODE_ACTIVE + SEV0 escalation.
- [ ] (R.3) **`live-operator` audit-ack within window**: AuditAckButton click → countdown stops; HUMAN_AUDIT_ACKED →
      CLOSED.
- [ ] (R.4) **`live-operator` does NOT ack**: at 6h+10min, secondary PagerDuty page fires (synthetic clock).
- [ ] (R.5) **`founder` receives Twilio voice call** at the SLA window; narrates incident summary; operator drives
      Safety Ops tab from the call.

### Section S — Data-pipeline-correctness composition

- [ ] (S.1) **No incident-gateway change ships if data audit RED**: layer-freeze HARD RULE applies.
- [ ] (S.2) **Pre-cutover gate**: this audit MUST be GREEN before any new strategy promotes to `live_full`.
- [ ] (S.3) **Cross-audit reciprocity**: failure of an observability item is itself a Layer-N+1 work-blocker.

### Section T — Originally-stated cross-cutting verification

- (e2e-batch-live) **Batch-live round-trip**: pick one (venue, data_type) pair, run batch adapter → confirm manifest row
  → run live adapter → confirm same schema row.
- (mock-upstream) **Independent audit**: runnable with `CLOUD_MOCK_MODE=true`.
- (synthetic-failure-game-day) **Pre-cutover game day**: covered by Section O.10.

## Success Criteria

**Per-section** (all items in each section must be GREEN):

- Section A (baseline) — 5 items
- Section B (incident gateway) — 5 items
- Section C (agent recovery) — 5 items
- Section D (severity routing) — 3 items
- Section E (reconciliation) — 5 items
- Section F (drawdown + liquidation) — 8 items
- Section G (connectivity) — 4 items
- Section H (restart/OOM/redeploy) — 5 items
- Section I (alert provider) — 4 items
- Section J (physical pager) — 4 items
- Section K (audit ack) — 3 items
- Section L (runbooks) — 3 items
- Section M (safety-ops UI tab) — 3 items
- Section N (LLM audit-signoff) — 4 items

**End-to-end** (audit is NOT GREEN until ALL of these pass):

- Section O — 10 E2E flow tests (O.1–O.10) all pass; defence-in-depth stack proven across all 5 layers
- Section P — 11 inter-plan handshake checks (P.1–P.11) all pass
- Section Q — 4 cross-domain composition checks (Q.1–Q.4) pass
- Section R — 5 operator-persona walkthroughs (R.1–R.5) pass
- Section S — 3 data-pipeline-correctness composition checks (S.1–S.3) pass

**Smoke tests** (must pass within 60-90s):

- Alerting smoke (inject FAILED event → alert fires within 60s)
- Twilio voice smoke (synthetic SEV0 → voice call within 90s)
- LLM signoff smoke (synthetic AgentActionEvent → RecoveryAuditSignoff within 90s)
- Layer-1.5 backup actuator smoke (synthetic Layer-0 FAILED → LLM-driven retry within 90s)
- Recon-freeze smoke (30min recon breach → freeze armed → preflight rejects synthetic order within 5s)
- Manual safety-ops smoke (button click → IncidentEnvelope with provenance=MANUAL_OPERATOR within 30s)

**Operational gates**:

- QG snapshot cron ran within last 24h
- Pre-cutover game-day pass (3+ scenarios per O.10)
- All 11 active plans under `parent_epic: observability_master` have ≥ Phase 1+2 complete
- No orphan active plans under this epic (regen_inventory shows 0 orphans)

**Failure-stop conditions** (any one returns audit verdict = RED, not YELLOW):

- IncidentState machine allows `AUTO_ACTION_SUCCEEDED → RESOLVED` direct transition.
- LLM agent has unrestricted shell access (must be closed-set wrapper only).
- Manual Safety Ops action bypasses Incident Gateway (skips audit trail).
- Even-APPROVED-requires-human-ack rule violated (queue auto-closes APPROVED incidents).
- Physical pager fires for non-closed-set conditions (alert fatigue).

## Output Format

Result file at `plans/audit/results/observability_master_audit_YYYY_MM_DD.md`. Same structure as per `../README.md`.
Disaster-recovery-target-model-vs-prod gap audit lands at
`plans/audit/results/observability_disaster_recovery_audit_<date>.md`.

## Linked Results

| Date       | Result file                                           | Status                                                     |
| ---------- | ----------------------------------------------------- | ---------------------------------------------------------- |
| 2026-05-23 | `observability_disaster_recovery_audit_2026_05_23.md` | RED — 11 P0 gaps → 11 active plans spawned (see audit doc) |
