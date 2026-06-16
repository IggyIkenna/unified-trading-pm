---
type: audit-result
title: Observability — Disaster-Recovery Target-Model Gap Audit (2026-05-23)
epic: observability_master
auditor: claude + operator
date: "2026-05-23"
status: RED
instructions_ref: ../instructions/observability_master_audit_instructions.md
name: observability_disaster_recovery_audit_2026_05_23
audit_instructions: ../instructions/observability_master_audit_instructions.md
target_model_source: ../../active/issues/disaster_recovery.md
assigned_vm: vm-cross-cutting
tier: L4
last_updated: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
---

# Observability — Disaster-Recovery Target-Model Gap Audit (2026-05-23)

> **Sources audited**: workspace as of 2026-05-23 (cutover day). Target model =
> `plans/active/issues/disaster_recovery.md` (operator-supplied target operating model, 1637 lines, sections 1-22).
> Current production = read of `alerting-service/`, `execution-service/`, `strategy-service/`,
> `batch-live-reconciliation-service/`, `unified-trading-system-ui/`, `agent-orchestrator/`, codex SSOTs
> (`autonomous-recovery-matrix.md`, `kill-switch-circuit-breaker.md`, `alerting.md`, `disaster-recovery.md`), and 17
> scratch scenarios in `plans/active/scratch_scenarios_day1/`.

## Executive summary

The workspace already ships a strong **Layer-0 deterministic** safety surface (kill-switch state machine, per-venue
circuit breakers, KillSwitchBus publisher hook, ~76 closed-set AlertCode taxonomy, 56 LIVE_ALERT_RULES, multi-leg
compensation, autonomous-recovery decision tree codex doc, batch-live-reconciliation-service, DART kill-switch UI
panel). What is **missing for the May-23 cutover** is the layer ABOVE Layer-0:

1. A central **Incident Gateway** state-machine that owns incident lifecycle, dedup, audit-ack queue, and recovery-
   verification (separate from `AUTO_ACTION_SUCCEEDED`).
2. An **Agent Recovery Controller** that owns the closed-set recovery actions as named, dry-run-testable scripts with
   runbook-IDs and structured `AgentActionEvent` reports — TODAY these actions are scattered across services.
3. An **LLM recovery-audit-signoff agent** (the operator's added requirement) that audits every automated recovery
   action, signs off, can dispute, and acts as Layer-1.5 backup actuator when Layer-0 fails.
4. **Reconciliation age tracking** (first_seen_at + oldest-unreconciled-age) with 15-min / 30-min escalation thresholds
   and immediate-SEV0 overrides.
5. **Drawdown + liquidation policy** declared per-strategy as a closed 7-threshold set, with strategy-specific close-
   all scripts.
6. **Connectivity dependency_health_policy** — expected_recovery_time + buffer model per dependency, with auto-
   escalation rules.
7. **Audit-acknowledgement SLA + state** (6h default + per-severity override + secondary human + founder fallback).
8. **Independent fallback** — Twilio direct voice/SMS for primary-provider-down + SEV0-no-ack cases.
9. **Physical pager layer** — operator-purchased device + webhook prototype + Twilio voice bridge.
10. **22 incident runbooks** with governance fields + linked evidence store.
11. **Deployment-UI Safety Ops tab** consolidating manual overrides for every Layer-0 + Layer-1 action.

**Verdict**: RED. 11 P0 gaps → 11 active plans spawned (this audit), totalling **~86 calibrated AI-days** across
parallel slots. With full-P0 fan-out the entire scope ships within the May-23 cutover window without cutting corners.

## Coverage transparency

This audit walked: (a) every file under `alerting-service/`, `execution-service/`, `strategy-service/`, and
`batch-live-reconciliation-service/` for incident/recovery/alerting patterns; (b) every codex doc referenced from the
observability epic; (c) UAC `canonical/crosscutting/alerting/` + `internal/alerting/` + `internal/reconciliation.py`;
(d) DART/`unified-trading-system-ui/components/widgets/{alerts,risk}/`; (e) `agent-orchestrator/agents/*.md`; (f) 17
scratch-scenario specs. **Sampled** (did not exhaustively grep): `mtds`, `mdps`, `features-service` for the emission
side beyond the 4 pulled-forward DeFi codes (Phase 3 of `alerting_service_live_rules_2026_05_07.md` audited those
already + flipped them ✓).

## Gap-by-section against `disaster_recovery.md` target model

### §3 — Main components (target = 10; current = 6 + partial)

| Component (target)                | Current state                                                                                                              | Gap                                                                                        | Owner active plan                                                                                    |
| --------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- |
| 1. Incident Gateway               | alerting-service has routing+dedup+notify; no incident state machine or audit-ack queue                                    | **GAP** — central state machine + dedup-key + audit-ack queue + recovery-verification gate | `incident_gateway_and_state_machine_2026_05_23`                                                      |
| 2. Agent Recovery Controller      | Recovery logic scattered: kill-switch in execution-service, circuit-breaker in alerting-service, retries in venue handlers | **GAP** — central Layer-0 deterministic script library + runbook-ID + AgentActionEvent     | `agent_recovery_controller_layer0_deterministic_2026_05_23`                                          |
| 3. Reconciliation Service         | `batch-live-reconciliation-service/` exists; no age fields, no escalation thresholds                                       | **GAP** — age tracking + 12 dimensions + 15/30-min thresholds                              | `reconciliation_age_tracking_and_escalation_2026_05_23`                                              |
| 4. Risk + PnL Monitor             | `risk-and-exposure-service/` + `position-balance-monitor-service/` partial; drawdown policy not closed-set                 | **GAP** — per-strategy 7-threshold closed set + investigation report                       | `drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23`                                    |
| 5. Connectivity Health Monitor    | per-venue circuit breakers exist; no dependency_health_policy YAML                                                         | **GAP** — 5-class taxonomy + expected_time+buffer policy                                   | `connectivity_dependency_buffer_policy_2026_05_23`                                                   |
| 6. Audit Event Store              | AlertDeliveryRecord persisted; no incident-keyed audit store                                                               | **GAP** — incident-keyed, queryable, durable evidence store                                | `incident_runbooks_and_evidence_store_2026_05_23`                                                    |
| 7. Primary Incident Provider      | PagerDuty wired (Phase 4 of `alerting_service_live_rules_2026_05_07.md`)                                                   | OK — Telegram + PagerDuty live; provider-health probe needed                               | `alerting_service_live_rules_2026_05_07` (existing) + `independent_fallback_twilio_voice_2026_05_23` |
| 8. Slack Notification Layer       | **Deprecated** per `codex/03-observability/alerting.md` line 14-15                                                         | OK — Slack is deprecated; references being swept                                           | n/a                                                                                                  |
| 9. Independent Emergency Fallback | None — PagerDuty + Telegram only                                                                                           | **GAP** — Twilio direct voice/SMS (separate billing, separate API)                         | `independent_fallback_twilio_voice_2026_05_23`                                                       |
| 10. Physical Alert Layer          | None                                                                                                                       | **GAP** — operator purchase + webhook prototype + Twilio voice bridge                      | `physical_pager_research_and_webhook_prototype_2026_05_23`                                           |

### §5 — Severity model (SEV0/1/2/3)

Current `AlertSeverity` enum (UAC) ships CRITICAL/HIGH/WARN/INFO. Display aliases T1/T2/T3/T4 documented. Mapping to
SEV0/1/2/3 is **implicit but undocumented** — no closed-set router rule asserting that
`AUTO_ACTION_SUCCEEDED + recovery_confirmed=True` → SEV2 (audit-ack-only, no wake-up); only routes by event_pattern. The
7 immediate-SEV0 overrides (unknown net exposure, unconfirmed open orders, kill-switch can't confirm cancellation,
venue/internal balance mismatch, position exists externally unknown internally, material balance movement unexplained,
margin/collateral safety uncertain) are NOT codified anywhere. **GAP — addressed in
`incident_gateway_and_state_machine_2026_05_23.md` Phase 3.**

### §6 — Human acknowledgement model (operational ack vs audit ack)

Current: DART Active Alerts has "Acknowledge" button. **GAP — one button, no distinction between operational ack ("I'm
investigating") and audit ack ("I've reviewed the report after the system handled it")**. No 6h SLA enforcement. No
secondary-human escalation when primary on-call doesn't ack within window. Addressed in
`audit_acknowledgement_sla_and_state_2026_05_23.md`.

### §7 — Reconciliation policy

Current `batch-live-reconciliation-service/` reconciles, but spot-check shows: no `first_seen_at`, no
`oldest_unreconciled_age_seconds`, no 12-dimension separation (orders / fills / positions / balances / funding / fees /
transfers / borrow-lending / collateral / margin-mode-and-leverage / strategy-allocation / account-aggregate). No 15-
min escalation threshold. No freeze-on-recon-risk. **GAP — addressed in
`reconciliation_age_tracking_and_escalation_2026_05_23.md`.**

### §8 — PnL drawdown + strategy risk policy

Current: each strategy has bespoke drawdown logic. No closed-set 7-threshold model
(warning/investigation/human_escalation/auto_pause/auto_reduce/auto_close_all/liquidation_risk). No
`expected_drawdown_model` closed-set basis enum. No `response_policy` 5-flag declaration. No drawdown investigation
report template. Per-strategy close-all scripts exist as ad-hoc; not idempotent + dry-run-testable by contract. **GAP —
addressed in `drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md`.**

### §9 — Liquidation policy

Current: HF thresholds (1.5/1.2/1.0) exist for DeFi recursive-borrow; CeFi liquidation event detection partial. No
liquidation investigation report template. Liquidation-risk pre-detection partial (HF-based only, no margin-ratio,
ADL/insurance-fund, venue-API-margin-state-uncertain triggers). **GAP — folded into
`drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md`.**

### §10 — Connectivity + dependency policy

Current: per-venue circuit breakers; per-RPC retry. No 5-class taxonomy (execution-critical-external,
market-data-critical-external, internal-control-plane, internal-data-plane, alerting-and-observability). No
`dependency_health_policy` YAML per dependency. No expected_recovery_time + buffer model. **GAP — addressed in
`connectivity_dependency_buffer_policy_2026_05_23.md`.**

### §11 — Restart / OOM / redeploy / scaling policy

Current: OOM detection via `vm-exec-with-gcs-tee.sh` serial-log scrape (existing); resize-after-OOM partial; redeploy
audit-event partial. Repeated repair loop detection NOT codified ("3+ restarts in M minutes → SEV1"). **GAP — split
across `agent_recovery_controller_layer0_deterministic_2026_05_23.md` (deterministic scripts) +
`incident_gateway_and_state_machine_2026_05_23.md` (loop detection in incident state).**

### §12 — Alert provider + notification tooling

Current: PagerDuty + Telegram + ~76 closed-set codes + dedup. **GAP — no continuous primary-provider health probe**
(can-reach-API, can-create-test-incident, billing-active, escalation-policy-enabled, on-call-populated, recent-incident-
callbacks). Addressed in `independent_fallback_twilio_voice_2026_05_23.md` (provider-health probe is paired with the
independent-fallback work).

### §13 — Physical fallback layer

Current: none. **GAP — addressed in `physical_pager_research_and_webhook_prototype_2026_05_23.md`** with comparison
matrix (4-6 candidate devices) + working webhook prototype + Twilio voice bridge as permanent fallback.

### §14 — Incident payload schema

Current: `DefiAlert` envelope (UAC `internal/alerting/alerts.py`); structured AgentActionEvent NOT codified.
IncidentEnvelope per §14.1 of target model NOT codified — fields like `incident_key`, `risk_state`, `capital_at_risk`,
`auto_action_allowed`, `recovery_confirmed`, `human_audit_ack_required`, `audit_ack_due_at`, `runbook_id`,
`config_hash`, `code_version` not present in any UAC schema. **GAP — addressed in
`incident_gateway_and_state_machine_2026_05_23.md` Phase 1 (UAC schema).**

### §15 — Required runbooks (22)

Current: 15 per-AlertCode runbooks (existing from `alerting_service_live_rules_2026_05_07.md` Phase 6 —
`kill_switch_*.md`, `defi_*.md`, etc.). **GAP — 22 incident-level runbooks (RB-INC-001/002/003, RB-RECON-001/002/003,
RB-RISK-001/002/003/004, RB-CONN-001/002/003/004/005, RB-DEPLOY- 001, RB-INFRA-001/002/003, RB-ALERT-001/002/003)**
distinct from per-AlertCode runbooks — these are **procedure-oriented** (how to handle each kind of incident regardless
of which AlertCode fired). Addressed in `incident_runbooks_and_evidence_store_2026_05_23.md`.

### §16 — Configuration requirements

Current: strategy config exists; no strategy-level closed-set risk_thresholds + expected_drawdown_model +
response_policy declared per `disaster_recovery.md` §16.1. Venue + dependency configs similarly partial. **GAP — fold
into the per-section plans above.**

### §17 — Dashboards + evidence

Current: DART has Active Alerts, kill-switch panel, circuit-breakers widget, severity-breakdown widget, alerts-kill-
switch widget. **GAP — global live-trading-health dashboard + audit-ack-queue dashboard + alert-provider-health
dashboard + manual safety-ops tab.** Addressed in `deployment_ui_safety_ops_tab_2026_05_23.md`.

### §18 — Agent audit checklist (10 sub-sections)

Updated audit-instructions file (`observability_master_audit_instructions.md` this commit) now covers all 10 sub-
sections (renamed Sections B-N) plus the operator-added §N for the LLM recovery-audit-signoff agent.

### §19 — Implementation roadmap (target = 5 phases)

Target phase 1 (minimum safe alerting) is **already done** via `alerting_service_live_rules_2026_05_07.md`. Target
phases 2-5 fold into the 11 new plans (gap-by-section above). Phase 5 (governance + regular testing — monthly game days,
SEV0 wake-up flow test, provider-down fallback test, physical alert test, liquidation-risk scenario, etc.) is covered by
the existing 17 scratch-scenarios in `plans/active/scratch_scenarios_day1/` + the pre-cutover game-day acceptance
criterion in §M of audit instructions.

### §20 — Key design decisions (14)

Cross-referenced against current codex SSOTs:

| #   | Target decision                                                               | Current state | Where codified                                                                                 |
| --- | ----------------------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------- |
| 1   | One primary incident provider                                                 | ✓ OK          | `codex/03-observability/alerting.md`                                                           |
| 2   | Slack for low/medium visibility                                               | ✗ Slack DEP   | Slack deprecated; new line on Twilio voice instead                                             |
| 3   | Independent fallback only for primary-down or SEV0 no-ack                     | **GAP**       | New plan + `codex/04-architecture/recovery-defence-in-depth-layers.md`                         |
| 4   | Agents can act immediately where delay increases risk                         | ✓ OK          | `codex/04-architecture/autonomous-recovery-matrix.md`                                          |
| 5   | Human approval NOT required before ordinary approved recovery actions         | ✓ OK          | Layer-0 deterministic scripts                                                                  |
| 6   | Human ack required AFTER material production actions                          | **GAP**       | New plan: `audit_acknowledgement_sla_and_state_2026_05_23`                                     |
| 7   | Audit ack SLA defaults to 6h                                                  | **GAP**       | Same plan                                                                                      |
| 8   | Unreconciled positions/orders use age buffers, not instant escalation         | **GAP**       | New plan: `reconciliation_age_tracking_and_escalation_2026_05_23`                              |
| 9   | 15-min unresolved threshold forces human investigation                        | **GAP**       | Same plan                                                                                      |
| 10  | PnL drawdown thresholds are strategy-specific                                 | **GAP**       | New plan: `drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23`                    |
| 11  | Liquidations never normal + always require human investigation                | partial       | Same plan                                                                                      |
| 12  | Physical alerting reserved for SEV0 or severe no-ack                          | **GAP**       | New plan: `physical_pager_research_and_webhook_prototype_2026_05_23`                           |
| 13  | Recovery verification separate from action completion                         | **GAP**       | New plan: `incident_gateway_and_state_machine_2026_05_23` (`AUTO_ACTION_SUCCEEDED ≠ RESOLVED`) |
| 14  | Every material incident links to evidence, config_hash, code_version, runbook | **GAP**       | New plan: `incident_runbooks_and_evidence_store_2026_05_23`                                    |

### Operator-added decisions (beyond target model)

| #   | Operator decision (2026-05-23)                                                                                                                                           | Codified in                                                                 |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| 15  | LLM agent audits every recovery + signs off; can ESCALATE if it thinks automation was wrong; acts as Layer-1.5 backup actuator when Layer-0 fails                        | New plan: `ai_recovery_audit_signoff_agent_2026_05_23`                      |
| 16  | Even when LLM signs off as APPROVED, human audit ack required within 6h (or stricter per severity)                                                                       | `audit_acknowledgement_sla_and_state_2026_05_23` + the LLM agent plan       |
| 17  | Deployment-UI gets a Safety Ops tab that exposes every Layer-0 + Layer-1 action as a manual button (typed-confirm pattern)                                               | New plan: `deployment_ui_safety_ops_tab_2026_05_23`                         |
| 18  | Twilio voice bridge as PERMANENT fallback (not just bridge until physical pager ships)                                                                                   | `independent_fallback_twilio_voice_2026_05_23`                              |
| 19  | Layered defence: deterministic Layer-0 → LLM-audit Layer-1 → PagerDuty Layer-2 → Twilio Layer-3 → physical pager Layer-4 → human audit ack Layer-5 (cascading on no-ack) | New codex SSOT: `codex/04-architecture/recovery-defence-in-depth-layers.md` |

## Gap list — prioritised (11 P0 active plans)

Plans are listed in dispatch order; the dispatcher (slot 1 main) reads this section and assigns slots in this order.

| #   | Active plan                                                       | Class     | Baseline AI-days | Calibrated | Est. dispatch slot |
| --- | ----------------------------------------------------------------- | --------- | ---------------- | ---------- | ------------------ |
| 1   | `incident_gateway_and_state_machine_2026_05_23`                   | design    | 18               | 10.8       | slot 3             |
| 2   | `agent_recovery_controller_layer0_deterministic_2026_05_23`       | brand-new | 14               | 14.0       | slot 4             |
| 3   | `ai_recovery_audit_signoff_agent_2026_05_23`                      | brand-new | 12               | 12.0       | slot 5             |
| 4   | `reconciliation_age_tracking_and_escalation_2026_05_23`           | refactor  | 10               | 4.0        | slot 6             |
| 5   | `drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23` | design    | 16               | 9.6        | slot 7             |
| 6   | `connectivity_dependency_buffer_policy_2026_05_23`                | design    | 8                | 4.8        | slot 8 (ikenna)    |
| 7   | `audit_acknowledgement_sla_and_state_2026_05_23`                  | design    | 8                | 4.8        | slot 3 (harsh)     |
| 8   | `independent_fallback_twilio_voice_2026_05_23`                    | infra     | 6                | 4.8        | slot 4 (harsh)     |
| 9   | `physical_pager_research_and_webhook_prototype_2026_05_23`        | research  | 4                | 4.8        | slot 5 (harsh)     |
| 10  | `incident_runbooks_and_evidence_store_2026_05_23`                 | design    | 14               | 8.4        | slot 6 (harsh)     |
| 11  | `deployment_ui_safety_ops_tab_2026_05_23`                         | brand-new | 8                | 8.0        | slot 7 (harsh)     |
|     | **TOTAL**                                                         |           |                  | **86.0**   |                    |

With 16 parallel slots (8 ikenna + 8 harsh) the total fits within the May-23 cutover window at ~5.4 cal AI-days per
slot. With Half-1+2 commit-push-flip discipline (CLAUDE.md HARD RULE) the work runs concurrently.

## Existing-plan handshakes

- **`alerting_service_live_rules_2026_05_07.md`** (P0, in flight) — already owns AlertCode taxonomy + LIVE_ALERT_RULES
  - paging targets + DART Active Alerts panel + 15 per-AlertCode runbooks + Phase 7 quietness baseline + Phase 8
    rehearsal. New plans EXTEND this surface; coordinate with Harsh on alerting-service edits per CLAUDE.md "alerting-
    service is Harsh's repo" rule. Specifically:
  * Plan 1 (Incident Gateway) extends `alerting-service/config.py` + `notifiers/router.py` with the state machine; the
    UAC schema additions (IncidentEnvelope + AgentActionEvent + IncidentState enum) are owner-neutral.
  * Plan 2 (Layer-0 scripts) is mostly `deployment-service/scripts/recovery/` (cross-cutting).
  * Plan 7 (audit-ack SLA) wires into the existing DART Active Alerts panel + alerting-service ack endpoint.
  * Plan 8 (Twilio voice) lands a new notifier subclass in alerting-service.
- **`master_to_live_defi_2026_05_23.md` Group F + Group G** — alerting / kill-switch verification + DART operator UX.
  Plans 1, 11 (Safety Ops tab) feed into Group G.
- **`scratch_scenarios_day1/01-17`** — pre-cutover game-day scenarios. Audit instructions §M cross-cutting verification
  asserts at least 3 scenarios pass with the full Layer-0..5 stack.

## Per-plan readiness criteria (extracted into each plan's frontmatter)

Each of the 11 active plans declares:

- `parent_epic: observability_master`
- `estimate_class` / `estimate_baseline_ai_days` / `estimate_calibrated_ai_days` per `Estimate Calibration` CLAUDE.md
  HARD RULE
- `Pre-Audit Before Execution` blast radius (workspace-wide grep before any rename/removal)
- `Phased Execution DAG` with QG gates between phases
- `Success Criteria` per phase (UAC tests / per-service QG / integration tests / smoke tests)
- `Downstream Consumer Updates` for every removed/renamed public symbol
- `Single Source of Truth` (types in UAC or `unified_api_contracts.internal`)
- `Continuous Verification` path per item (master plan Continuous-Verification Column HARD RULE)

## Verification protocol (post-plan-shipping)

After each plan ships its P0 phases:

1. Run `bash scripts/quality-gates.sh` in the touched repo.
2. Re-run this audit (`observability_master_audit_instructions.md`) — checklist items flip from `- [ ]` to `- [x]`.
3. Run the game-day acceptance criterion (at least 3 of 17 scratch scenarios). Each scenario asserts the full Layer-
   0..5 stack fires.
4. Operator signs off via `audit_acknowledgement_sla_and_state_2026_05_23` flow (eat our own dogfood).

## Sign-off

| Field           | Value                                                                                      |
| --------------- | ------------------------------------------------------------------------------------------ |
| Audit owner     | claude (slot 1 main, this session)                                                         |
| Audit date      | 2026-05-23                                                                                 |
| Status          | RED — 11 P0 gaps; plans spawned + dispatched in this session                               |
| Operator review | _pending — slot 1 main appends [ack-by: ikenna] when operator acks the audit + plan-flips_ |
| Next audit      | After all 11 plans flip to status: complete (estimated within May-23 cutover window)       |
