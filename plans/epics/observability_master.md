---
name: observability_master
title: "Observability Master"
type: epic
tier: L4
status: active
priority: P0
assigned_vm: vm-cross-cutting
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-23
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - ../archive/2026_05/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md
  - ../archive/2026_05/alerting_service_live_rules_2026_05_07.md
  - ../active/global_ledger_pnl_attribution_discovery_2026_05_21.md
  - ../archive/incident_gateway_and_state_machine_2026_05_23.plan.md
  - ../archive/2026_05/agent_recovery_controller_layer0_deterministic_2026_05_23.md
  - ../archive/ai_recovery_audit_signoff_agent_2026_05_23.plan.md
  - ../archive/reconciliation_age_tracking_and_escalation_2026_05_23.plan.md
  - ../archive/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.plan.md
  - ../archive/2026_05/connectivity_dependency_buffer_policy_2026_05_23.md
  - ../archive/2026_05/audit_acknowledgement_sla_and_state_2026_05_23.md
  - ../archive/independent_fallback_twilio_voice_2026_05_23.plan.md
  - ../archive/2026_05/physical_pager_research_and_webhook_prototype_2026_05_23.md
  - ../archive/2026_05/incident_runbooks_and_evidence_store_2026_05_23.md
  - ../archive/2026_05/deployment_ui_safety_ops_tab_2026_05_23.md
---

# Observability Master

**Owns**: alerting-service + monitoring + telemetry + **Incident Gateway state machine** + **Agent Recovery Controller
(Layer-0 deterministic scripts)** + **LLM recovery-audit-signoff agent (Layer-1)** + **reconciliation age tracking** +
**drawdown + liquidation policy + strategy risk config** + **connectivity dependency buffers** + **alert-provider
health + Twilio voice fallback (Layer-3)** + **physical pager layer (Layer-4)** + **audit acknowledgement SLA
(Layer-5)** + **deployment-UI Safety Ops tab (manual override)** + 3am-auto-recovery agent + QG snapshot cron + runbook
governance.

**Status**: P0-expanded 2026-05-23 — 11 new active plans landed from
[`../audit/results/observability_disaster_recovery_audit_2026_05_23.md`](../audit/results/observability_disaster_recovery_audit_2026_05_23.md)
(gap analysis vs target model in [`../active/issues/disaster_recovery.md`](../active/issues/disaster_recovery.md)).
Total ~86 cal AI-days dispatched across slots for May-23 cutover.

See [`README.md`](README.md) for the canonical epic frontmatter schema + body structure.

## Codex SSOTs

| Doc                                                         | Owns                                                                                                                          |
| ----------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `codex/05-infrastructure/live-deployment-monitoring.md`     | Per-archetype heartbeat thresholds; STARTED/progress/STOPPED/FAILED event cadence; cross-cloud event-stream parity            |
| `codex/03-observability/alerting.md`                        | AlertSeverity enum (CRITICAL/HIGH/WARN/INFO) → PagerDuty P-tier → routing channels                                            |
| `codex/04-architecture/kill-switch-circuit-breaker.md`      | Kill-switch alerting; circuit-breaker trigger → auto-STOPPED event; alert escalation on arm                                   |
| `codex/04-architecture/autonomous-recovery-matrix.md`       | Decision tree — every failure scenario × every recovery action                                                                |
| `codex/04-architecture/incident-gateway-state-machine.md`   | **NEW 2026-05-23** — 13-state incident lifecycle (DETECTED → … → CLOSED); audit-ack queue; dedup-key                          |
| `codex/04-architecture/recovery-defence-in-depth-layers.md` | **NEW 2026-05-23** — 5-layer model: L0 Python → L1 LLM audit → L2 PagerDuty → L3 Twilio voice → L4 pager → L5 human audit ack |
| `codex/05-infrastructure/disaster-recovery.md`              | RTO/RPO targets, Tier 0-3 recovery, restore from manifest (existing — extended 2026-05-23)                                    |
| `codex/05-infrastructure/physical-pager-layer.md`           | **NEW 2026-05-23** — Pager device comparison, webhook prototype, Twilio voice bridge                                          |
| `codex/15-runbooks/alerting/pagerduty-escalation-policy.md` | Ikenna 14:30–02:30 UK / Harsh 02:30–14:30 UK; PagerDuty escalation ladder                                                     |
| `codex/15-runbooks/alerting/audit-acknowledgement-flow.md`  | **NEW 2026-05-23** — 6h audit-ack SLA + secondary-human + founder fallback                                                    |
| `codex/05-infrastructure/manifest-consolidator-ssot.md`     | Manifest consolidator freshness alerts; silence > 120s → CRITICAL                                                             |
| `codex/02-data/data-pipeline-correctness-hard-rule.md`      | Layer freeze on RED data audit; slot-reassignment trigger                                                                     |

## Assigned active plans

_13 active plans declare `parent_epic: observability_master` in their frontmatter. Workers pick up in priority order (P0
first). Auto-populated by `scripts/plans/populate_epic_bodies_2026_05_21.py`._

## P0 — must complete before next foundation gate (May-23 cutover)

### Recon-freeze publisher dispatch (slot 7, 2026-06-01 — from `recon_freeze_armed_never_published_2026_05_27.md`)

- [x] ✅ [CODE] P0. **G12 — alerting-service recon-freeze publisher (IN-SCOPE for May-23).** Operator decision
      2026-06-01: per-incident-type granularity — **symbol-scoped** for symbol-level recon breaks, **account-wide** for
      account-level SEV0s. — alerting-service@`a04bbf2` (QG exit 0, 780+ tests). `recon_freeze_publisher.py`
      (`publish_recon_freeze_armed`/`lifted` via `publish_coordination_event`; `arm_recon_freeze_for_alerts()` —
      CRITICAL recon-age + 3 symbol-scoped SEV0s → symbol freeze; the 4 account-level SEV0s (UNKNOWN_NET_EXPOSURE /
      MATERIAL_BALANCE_MOVEMENT_UNEXPLAINED / MARGIN_COLLATERAL_SAFETY_UNCERTAIN / KILL_SWITCH_CANNOT_CONFIRM_CANCEL) →
      account-wide `instrument="*"` + account_id/client_id) +
      `recon_freeze_event_handler.handle_reconciliation_age_payload` (wires the previously-orphan
      `evaluate_recon_age`/`evaluate_immediate_sev0` → route CRITICAL to PD+Telegram → arm freeze) + synthetic test.
      **Execution-side subscriber + per-incident emit remain `execution_master` G12 P1** (consume `RECON_FREEZE_ARMED` →
      `ReconFreezeChecker.arm()`). Repo: alerting-service.

### [`alerting_service_live_rules_2026_05_07`](../archive/2026_05/alerting_service_live_rules_2026_05_07.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-9 complete: AlertCode taxonomy + LIVE_ALERT_RULES + DART Active Alerts
panel + 15 per-AlertCode runbooks + Phase 7 quietness baseline VM running. Phase 8 rehearsal + Telegram token rotation +
PagerDuty setup BLOCKED-OPERATOR. · **estimate**: 13.2 cal AI-days (class: design)

### [`incident_gateway_and_state_machine_2026_05_23`](../archive/incident_gateway_and_state_machine_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped. 13-state machine + dedup + audit_ack_queue +
recovery_verifier + router refactor + Twilio fallback wired. · **estimate**: 10.8 cal AI-days (class: design)

### [`agent_recovery_controller_layer0_deterministic_2026_05_23`](../archive/2026_05/agent_recovery_controller_layer0_deterministic_2026_05_23.md)

**status**: ✅ ARCHIVED 2026-05-26 — All items completed. · **estimate**: 14.0 cal AI-days (class: brand-new) · **NEW
2026-05-23** — 10 closed-set deterministic recovery scripts
(restart/redeploy/resize/failover/pause/cancel/disable-venue/safe-mode/readonly-recon)

- structured AgentActionEvent.

### [`ai_recovery_audit_signoff_agent_2026_05_23`](../archive/ai_recovery_audit_signoff_agent_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped (UAC schema + UTL library + agent template + DISPUTE wiring +
DART feed + Playwright). Prod-VM launch + staging smoke are OPERATOR actions tracked in P3 below. · **estimate**: 12.0
cal AI-days (class: brand-new)

### [`reconciliation_age_tracking_and_escalation_2026_05_23`](../archive/reconciliation_age_tracking_and_escalation_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped. Age fields + 12 dimensions + 3-band escalation + 7
immediate-SEV0 overrides + ReconFreezeChecker. Smoke + game-day are OPERATOR actions tracked in P3 below. ·
**estimate**: 4.0 cal AI-days (class: refactor)

### [`drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23`](../archive/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped. UAC schemas + config loader validation + drawdown investigation
report + liquidation detectors + close-all scripts + smoke tests. Smoke + game-day live runs are OPERATOR actions
tracked in P3 below. · **estimate**: 9.6 cal AI-days (class: design)

### [`connectivity_dependency_buffer_policy_2026_05_23`](../archive/2026_05/connectivity_dependency_buffer_policy_2026_05_23.md)

**status**: ✅ ARCHIVED 2026-05-26 — All items completed. · **estimate**: 4.8 cal AI-days (class: design) · **NEW
2026-05-23** — 5-class dependency taxonomy

- per-dependency YAML policy + expected_time + buffer escalation rule.

### [`audit_acknowledgement_sla_and_state_2026_05_23`](../archive/2026_05/audit_acknowledgement_sla_and_state_2026_05_23.md)

**status**: ✅ ARCHIVED 2026-05-26 — All items completed. · **estimate**: 4.8 cal AI-days (class: design) · **NEW
2026-05-23** — 6h default SLA + per- severity override + secondary-human + founder fallback +
operational-ack-vs-audit-ack distinction.

### [`independent_fallback_twilio_voice_2026_05_23`](../archive/independent_fallback_twilio_voice_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All implementable phases shipped (Twilio notifiers + router fallback + health
probe). Operator-action items (Twilio account creation + SM creds push + live smoke) tracked in P3 below. ·
**estimate**: 4.8 cal AI-days (class: infra)

### [`physical_pager_research_and_webhook_prototype_2026_05_23`](../archive/2026_05/physical_pager_research_and_webhook_prototype_2026_05_23.md)

**status**: ✅ ARCHIVED 2026-05-26 — All items completed. · **estimate**: 4.8 cal AI-days (class: research) · **NEW
2026-05-23** — comparison matrix (4-6 candidates) + webhook prototype + Twilio voice bridge as permanent fallback.

### [`incident_runbooks_and_evidence_store_2026_05_23`](../archive/2026_05/incident_runbooks_and_evidence_store_2026_05_23.md)

**status**: ✅ ARCHIVED 2026-05-26 — All items completed. · **estimate**: 8.4 cal AI-days (class: design) · **NEW
2026-05-23** — 22 incident-level runbooks (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT) + evidence store schema +
config_hash + code_version + runbook_version linked per incident.

### [`deployment_ui_safety_ops_tab_2026_05_23`](../archive/2026_05/deployment_ui_safety_ops_tab_2026_05_23.md)

**status**: ✅ ARCHIVED 2026-05-26 — All items completed. · **estimate**: 8.0 cal AI-days (class: brand-new) · **NEW
2026-05-23** — Safety Ops tab in deployment-ui/DART surfacing every Layer-0 + Layer-1 action as manual buttons with
typed-confirm pattern; manual actions also flow through the incident state machine.

## P1 — important; post-current-gate

_(no plans currently assigned at this priority. Post-cutover audits will spawn P1 items here.)_

## P2 — useful; opportunistic

### [`alerting_runbook_and_operator_ux_post_cutover_2026_05_12`](../archive/2026_05/alerting_runbook_and_operator_ux_post_cutover_2026_05_12.md)

**status**: in archive (status: active in frontmatter — needs archival sweep; link corrected 2026-05-22) · **estimate**:
2.4 cal AI-days (class: design)

## P3 — backlog; revisit quarterly

> **MIGRATED FROM:** `alerting_service_live_rules_2026_05_07.md` (archived 2026-05-23) — Phases 1-9 complete. Phase 7
> quietness baseline VM ran until ~2026-05-24. Operator soak + rehearsal tasks below.

> **MIGRATED FROM:** `independent_fallback_twilio_voice_2026_05_23.md` (archived 2026-05-25) — code shipped;
> operator-action items below.

> **MIGRATED FROM:** `alerting_fp_rate_analysis_2026_05_23.md` (archived 2026-06-02) — Phase-7 quietness baseline
> confirmed 21 codes 0-FP; the 8 uncovered thresholds (5 ML codes + leverage/concentration/drawdown risk rules +
> per-venue `tick_staleness`) are `NEEDS-LIVE`, not an operator decision: they cannot be empirically baselined until
> `ml-inference-service` + live MTDS/MDPS feeds are running. Defaults stand in UAC `thresholds.py` until then. (The
> doc's other two action items already shipped: GCS structured FP-log path → alerting-service@`e2163a5`
> `write_quietness_report`; risk-rule AlertCode mapping → alerting-service@`9279d82`.)

- [ ] [DATA] `NEEDS-LIVE` P3. **Re-baseline the 8 uncovered alert thresholds once ML inference + live feeds are up.**
      Run a 48h targeted quietness baseline against live `ml-inference-service` emission + live MTDS/MDPS feeds; record
      results in UAC `ALERT_THRESHOLDS[*].quietness_baseline_date` for the 5 ML codes (`ML_SIGNAL_STALENESS`,
      `ML_MODEL_DRIFT_DETECTED`, `ML_PNL_DEVIATION`, `ML_INFERENCE_LATENCY_BREACH`, `ML_MODEL_VERSION_MISMATCH`), the
      leverage/concentration/drawdown risk rules, and per-venue `tick_staleness`; tune off the empirical FP rate. Auto-
      resumes when those subsystems go live (no operator decision needed — defaults hold meanwhile). Repo:
      alerting-service + UAC. **MIGRATED FROM:** `alerting_fp_rate_analysis_2026_05_23.md` § "Operator action required".

- [ ] [OPERATOR] P3. **Twilio account creation** — create dedicated Twilio account; obtain voice-capable phone number
      (UK +44 or similar). Cost: ~$1/number + $0.013/min voice. Per SSOT:
      `codex/04-architecture/recovery-defence-in-depth-layers.md` § Layer 3. **MIGRATED FROM:**
      `independent_fallback_twilio_voice_2026_05_23.md` Phase 1 P0.1.
- [ ] [OPERATOR] P3. **Push 7 Twilio SM credentials** — `alerting-twilio-account-sid`, `alerting-twilio-auth-token`,
      `alerting-twilio-from-number`, `alerting-twilio-to-number-primary/secondary/founder` to BOTH GCP
      `central-element-323112` SM AND AWS `427895769566` SM. CRITICAL: NEVER log auth_token in URL. **MIGRATED FROM:**
      `independent_fallback_twilio_voice_2026_05_23.md` Phase 1 P0.2-P0.3.
- [ ] [OPERATOR+AGENT] P3. **Twilio live smoke tests** (requires Phase 1 creds + staging stack) — inject
      KILL_SWITCH_DEFI_LIQUIDATION_RISK IncidentEnvelope → assert Twilio voice delivers within 90s; monkeypatch
      PagerDuty 503 → assert fallback_mode + Twilio fires. **MIGRATED FROM:**
      `independent_fallback_twilio_voice_2026_05_23.md` Phase 5 P0.12-P0.14.

> **MIGRATED FROM:** `ai_recovery_audit_signoff_agent_2026_05_23.md` (archived 2026-05-25) — code shipped;
> operator-action items below.

- [ ] [OPERATOR] P3. **Launch recovery-audit LLM agent** on long-lived GCE VM (asia-northeast1-c, e2-standard-2). Model
      = `claude-opus-4-7` (max thinking). Pre-flight: confirm AGENT_ORCHESTRATOR_URL + GH_PAT + AUDIT_STORE_BUCKET in
      SM. **MIGRATED FROM:** `ai_recovery_audit_signoff_agent_2026_05_23.md` Phase 5 P0.12.
- [ ] [OPERATOR+AGENT] P3. **Recovery-audit synthetic smoke + DISPUTE game-day** (requires staging infrastructure) —
      inject AgentActionEvent(action_status=FAILED) → assert Layer-1.5 backup fires within 90s; run scenario
      02_defi_chain_rpc_outage_solana.md → assert ESCALATE_TO_HUMAN verdict + 1h ack. **MIGRATED FROM:**
      `ai_recovery_audit_signoff_agent_2026_05_23.md` Phase 5 P0.13-P0.14.

> **MIGRATED FROM:** `reconciliation_age_tracking_and_escalation_2026_05_23.md` (archived 2026-05-25) — code shipped;
> operator-action items below.

- [ ] [OPERATOR+AGENT] P3. **Reconciliation smoke + game-day** (operator action required) — inject position-recon delta
      aged 20min → assert SEV1 fires; age to 40min → assert SEV0 + freeze armed + order preflight rejects. Run scenario
      11_handshake_integration.md → assert age fields populate + recovery fires. **MIGRATED FROM:**
      `reconciliation_age_tracking_and_escalation_2026_05_23.md` Phase 6 P0.15-P0.16.

> **MIGRATED FROM:** `drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md` (archived 2026-05-25) — code
> shipped; operator-action items below.

- [ ] [OPERATOR+AGENT] P3. **Drawdown + liquidation live smoke tests** — synthetic carry_staked_basis PnL drop to
      investigation threshold → assert report written + DART shows it; auto-close threshold → assert dry-run plan
      generated. Inject LIQUIDATION_EVENT_DETECTED → assert LiquidationInvestigationReport written + SEV1;
      cause-unknown=True → assert SEV0 escalation. Run scenario 15_liquidation_proximity_auto_deleverage.md. **MIGRATED
      FROM:** `drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md` Phase 6 P0.16-P0.18.

- [ ] [OPERATOR] P3. **Rotate Telegram bot token** — CRITICAL: token exposed in Tab L httpx log. Rotate via @BotFather →
      update Secret Manager `TELEGRAM_BOT_TOKEN` (GCP + AWS) + redeploy alerting-service.
- [ ] [OPERATOR] P3. **Set `TELEGRAM_CHAT_ID_OPS` GHA repo variable** in alerting-service repo settings so CI smoke
      alerts route to ops channel (not the default).
- [ ] [OPERATOR] P3. **PagerDuty escalation policy** — define in PD console: tier-1 (email) → tier-2 (SMS 5min) → tier-3
      (voice 10min). Wire `PAGERDUTY_ROUTING_KEY` Secret Manager key. Slack credential push post-Phase-7 baseline.
- [ ] [OPERATOR+AGENT] P3. **Alert rehearsal session** — run `inject_synthetic_alert.py` for all 15 alert codes + fill
      sign-off doc `REHEARSAL_2026_05_23.md`. CRITICAL-severity simulation (position > 10× threshold).
- [ ] [OPERATOR] P3. **48h FP baseline review** — if FP > 10%/24h post-cutover, file threshold-adjustment task. 7-day
      soak daily review; threshold re-tune if needed.
- [ ] [AGENT] P3. **Harsh pair-review PR** — alerting-service is Harsh's repo; raise PR for Tab L diff + get Harsh's
      sign-off before merging to main.

## Archived plans

### [`alerting_service_live_rules_2026_05_07`](../archive/2026_05/alerting_service_live_rules_2026_05_07.md)

**status**: ✅ ARCHIVED 2026-05-23 — Phases 1-9 complete. Deferred operator tasks migrated to P3 above.

### [`incident_gateway_and_state_machine_2026_05_23`](../archive/incident_gateway_and_state_machine_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped.

### [`ai_recovery_audit_signoff_agent_2026_05_23`](../archive/ai_recovery_audit_signoff_agent_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All implementable phases shipped. Operator-action items in P3.

### [`reconciliation_age_tracking_and_escalation_2026_05_23`](../archive/reconciliation_age_tracking_and_escalation_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped. Operator smoke in P3.

### [`drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23`](../archive/drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — All phases shipped. Operator smoke in P3.

### [`independent_fallback_twilio_voice_2026_05_23`](../archive/independent_fallback_twilio_voice_2026_05_23.plan.md)

**status**: ✅ ARCHIVED 2026-05-25 — Code shipped. Twilio account creation + creds in P3.
