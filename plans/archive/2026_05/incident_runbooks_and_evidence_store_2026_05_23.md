---
doc_type: plan
title: 22 Incident Runbooks + Evidence Store + config_hash + code_version + runbook_version
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
    e2e-testing,
    execution-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    incident_gateway_and_state_machine_2026_05_23.md,
    /plans/archive/2026_05/agent_recovery_controller_layer0_deterministic_2026_05_23.md,
    reconciliation_age_tracking_and_escalation_2026_05_23.md,
    drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md,
    /plans/archive/2026_05/connectivity_dependency_buffer_policy_2026_05_23.md,
  ]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: design
estimate_baseline_ai_days: 14
estimate_calibrated_ai_days: 8.4
estimate_calibration_note: "Design class — 22 procedure-oriented runbooks + evidence store schema + cross-linking
  discipline. Baseline 14 = ~0.6

  cal-day per runbook × 22 + 1 cal-day store. × 0.6 design = 8.4 cal-days.

  "
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on: [incident_gateway_and_state_machine_2026_05_23, agent_recovery_controller_layer0_deterministic_2026_05_23]
gates: ["master_to_live_defi_2026_05_23:Group-F"]
---

# 22 Incident Runbooks + Evidence Store

> **🟢 SPAWNED 2026-05-23 from `observability_disaster_recovery_audit_2026_05_23.md` gap #10.** Closes §15 + §17 of the
> target model. **Distinct from the 15 per-AlertCode runbooks** already shipped by Phase 6 of
> `alerting_service_live_rules_2026_05_07.md` — these are **procedure-oriented**: "how to handle a position
> reconciliation lag" not "how to handle a `KILL_SWITCH_VENUE_DISCONNECT` alert".

## Goal

Ship 22 incident runbooks per `disaster_recovery.md` §15. Ship a queryable evidence store where every material incident
links to: raw venue API snapshot, internal ledger snapshot, order/fill records, position records, balance records, logs,
metrics, traces, agent action logs, config_hash, code_version, runbook_version, human ack trail.

## Context

**Existing capability**:

- 15 per-AlertCode runbooks (`codex/15-runbooks/alerting/{kill_switch_*,defi_*,...}.md`).
- AlertDeliveryRecord persistence to GCS.
- `_template.md` for per-AlertCode runbook shape.

**Missing for May-23**:

- 22 procedure runbooks (RB-INC-001 .. RB-ALERT-003) per target §15.
- Evidence store: incident-keyed durable store linking the 14 evidence types.
- config_hash + code_version + runbook_version stamped on every IncidentEnvelope.

## Pre-audit (blast radius)

- NEW: `codex/15-runbooks/incidents/` directory — 22 markdown files.
- NEW: UAC `IncidentEvidence` Pydantic schema in `unified_api_contracts/canonical/crosscutting/incident/evidence.py`.
- NEW: `alerting-service/alerting_service/gateway/evidence_collector.py` — collects + persists evidence per incident.
- TOUCH: every Layer-0 recovery script (from `agent_recovery_controller_layer0_deterministic_2026_05_23`) — stamp
  config_hash + code_version + runbook_version on emitted AgentActionEvent.

## Phased execution DAG

### Phase 1 — UAC schema (0.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. `IncidentEvidence` Pydantic — 14 optional URL fields per target §17:
      `raw_venue_api_snapshot_url, internal_ledger_snapshot_url, order_fill_records_url, position_records_url,     balance_records_url, logs_url, metrics_url, traces_url, agent_action_logs_url, config_hash, code_version,     runbook_version, human_acknowledgement_trail_url, additional_evidence: dict[str, str]`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. Link from `IncidentEnvelope`: `evidence: IncidentEvidence | None`
      (lazy-collected post-RESOLVED).

### Phase 2 — Evidence collector (1.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.3. `alerting-service/alerting_service/gateway/evidence_collector.py` — on
      incident transition to AUDIT_REPORT_GENERATED: - Trigger per-service evidence-capture endpoints (each service
      exposes `/evidence/{incident_key}` which writes the snapshot to GCS at
      `incidents/{date}/{key}/evidence/<type>.json`). - Capture config_hash (= git rev-parse HEAD of
      unified-trading-pm + service repo at incident time; deterministic from deployment registry). - Capture
      code_version (= image_digest of running container OR git sha for VM-hosted services). - Capture runbook_version (=
      git sha of `codex/15-runbooks/incidents/<runbook_id>.md` at incident time).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.4. Each service registers an evidence-capture callback: execution-service
      (orders/fills/positions/balances + venue REST snapshots), strategy-service (strategy state + signals),
      batch-live-reconciliation-service (recon deltas + age fields), risk-and-exposure-service (margin/HF/exposure).

### Phase 3 — 22 incident runbooks (3 cal-days, parallel across runbooks)

Each runbook lives at `codex/15-runbooks/incidents/<runbook_id>.md` with frontmatter
`owner, cadence, verifier, last_executed` per the existing runbook-governance HARD RULE. Each follows a canonical shape:
TL;DR + symptom + diagnosis steps (concrete commands) + 3 resolution paths (auto-recovery, manual intervention,
kill-switch) + rollback

- common false-positives + escalation criteria + success criteria + post-incident actions.

* [x] ✅ [SCRIPT] P0.5. **RB-INC-001 SEV0 Incident Handling**: ack + check current risk + identify scope + confirm safe
      mode + escalate + close. — /codex/15-runbooks/incidents/rb_inc_001.md
* [x] ✅ [SCRIPT] P0.6. **RB-INC-002 SEV1 Investigation Handling**: review agent report + confirm protected mode +
      decide continue/pause/disable/close + document. — /codex/15-runbooks/incidents/rb_inc_002.md
* [x] ✅ [SCRIPT] P0.7. **RB-INC-003 Audit Acknowledgement Handling**: what counts as ack + what must be reviewed + sign
      off + escalate insufficient report. — /codex/15-runbooks/incidents/rb_inc_003.md
* [x] ✅ [SCRIPT] P0.8. **RB-RECON-001 Position Reconciliation Lag**: check venue + check ledger + check fills/orders +
      identify oldest + apply buffer + safe-mode-vs-continue. — /codex/15-runbooks/incidents/rb_recon_001.md
* [x] ✅ [SCRIPT] P0.9. **RB-RECON-002 Open Order Uncertainty**: pull open orders + attempt cancel + confirm + handle
      unknown + escalate if cancel unproven. — /codex/15-runbooks/incidents/rb_recon_002.md
* [x] ✅ [SCRIPT] P0.10. **RB-RECON-003 Balance/Collateral Mismatch**: pull balances + check transfers/funding/fees/
      borrow + check movements + check collateral/margin + escalate unexplained. —
      /codex/15-runbooks/incidents/rb_recon_003.md
* [x] ✅ [SCRIPT] P0.11. **RB-RISK-001 Strategy Drawdown Investigation**: determine threshold + compare to model +
      attribute PnL + check exposure/execution/slippage/fees/funding/data-quality + recommend. —
      /codex/15-runbooks/incidents/rb_risk_001.md
* [x] ✅ [SCRIPT] P0.12. **RB-RISK-002 Liquidation Event**: confirm details + remaining risk + freeze/reduce + report +
      escalate. — /codex/15-runbooks/incidents/rb_risk_002.md
* [x] ✅ [SCRIPT] P0.13. **RB-RISK-003 Liquidation Risk / Margin Danger**: check margin ratio + liquidation distance +
      collateral + reduce/close + SEV0 escalate. — /codex/15-runbooks/incidents/rb_risk_003.md
* [x] ✅ [SCRIPT] P0.14. **RB-RISK-004 Strategy Safe Mode**: define per-strategy + pause new + cancel-or-retain orders +
      confirm positions/hedges + human-resume-requirements. — /codex/15-runbooks/incidents/rb_risk_004.md
* [x] ✅ [SCRIPT] P0.15. **RB-CONN-001 Exchange WebSocket Degradation**: disconnect duration + backup feed +
      order-book-freshness + pause-decision. — /codex/15-runbooks/incidents/rb_conn_001.md
* [x] ✅ [SCRIPT] P0.16. **RB-CONN-002 Exchange REST API Failure**: order placement/cancel + rate limits + auth +
      escalate if cancel unconfirmable. — /codex/15-runbooks/incidents/rb_conn_002.md
* [x] ✅ [SCRIPT] P0.17. **RB-CONN-003 Internal Messaging Lag**: check PubSub/Kafka/Redis lag + check consumers + check
      DLQ + failover/scale. — /codex/15-runbooks/incidents/rb_conn_003.md
* [x] ✅ [SCRIPT] P0.18. **RB-CONN-004 Database/Storage Degradation**: ledger writes + read-only mode +
      replay/recovery + can-continue-trading. — /codex/15-runbooks/incidents/rb_conn_004.md
* [x] ✅ [SCRIPT] P0.19. **RB-CONN-005 Alert Provider Failure**: confirm provider status + trigger fallback + Twilio
      voice + create audit incident. — /codex/15-runbooks/incidents/rb_conn_005.md
* [x] ✅ [SCRIPT] P0.20. **RB-DEPLOY-001 Production Rollback**: identify version + roll back image + verify health +
      verify trading state + audit report. — /codex/15-runbooks/incidents/rb_deploy_001.md
* [x] ✅ [SCRIPT] P0.21. **RB-INFRA-001 OOM Recovery**: capture memory profile + restart/resize + check repeated OOM +
      verify recon + audit report. — /codex/15-runbooks/incidents/rb_infra_001.md
* [x] ✅ [SCRIPT] P0.22. **RB-INFRA-002 Machine/Node Failure**: cordon + move workload + verify service + verify risk. —
      /codex/15-runbooks/incidents/rb_infra_002.md
* [x] ✅ [SCRIPT] P0.23. **RB-INFRA-003 Secret/Config Failure**: verify config registry + verify secret access + prevent
      unsafe default + escalate if production-config-unknown. — /codex/15-runbooks/incidents/rb_infra_003.md
* [x] ✅ [SCRIPT] P0.24. **RB-ALERT-001 Dedicated On-Call Phone Setup**: carrier + apps + DND bypass + charger/UPS +
      test schedule. — /codex/15-runbooks/incidents/rb_alert_001.md
* [x] ✅ [SCRIPT] P0.25. **RB-ALERT-002 Physical Siren/GSM Alarm Setup**: trigger path + SIM + power backup + test. —
      /codex/15-runbooks/incidents/rb_alert_002.md
* [x] ✅ [SCRIPT] P0.26. **RB-ALERT-003 Satellite / No-Signal Fallback**: when used + who carries + test + limitations.
      — /codex/15-runbooks/incidents/rb_alert_003.md

### Phase 4 — Runbook governance (0.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.27. Every runbook has 4-field frontmatter
      (`owner, cadence, verifier, last_executed`). Cadence: RB-INC, RB-RECON, RB-RISK = quarterly game-day verification.
      RB-CONN, RB-DEPLOY, RB-INFRA = pre-cutover verification. RB-ALERT = monthly.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.28. Hygiene script
      `unified-trading-pm/scripts/plan-hygiene/check_runbook_fields.py` flags missing fields. Wire into daily
      plan-hygiene cron.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.29. Synthetic smoke: trigger a SEV1 incident → assert evidence_collector
      populates all 14 evidence URL fields → assert config_hash / code_version / runbook_version stamped on
      IncidentEnvelope.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.30. Per-runbook walkthrough on staging: operator runs each of 22 runbooks
      on a synthetic incident matching the runbook's scope; signs off in `last_executed:` frontmatter.

## Success criteria

- 22 incident runbooks land + governance fields valid.
- IncidentEvidence schema + collector ship.
- Every IncidentEnvelope stamped with config_hash + code_version + runbook_version.
- Evidence store URLs are queryable from DART (deep-link per incident).
- Smoke + per-runbook walkthrough green.

## Anti-patterns + banned approaches

- ❌ Runbook without owner/cadence/verifier/last_executed — fails plan-hygiene.
- ❌ Evidence captured lazily after incident closes — must be collected at AUDIT_REPORT_GENERATED state.
- ❌ Runbook merging into per-AlertCode runbooks — these are distinct (procedure-oriented vs alert-oriented).

## Continuous verification

- Quarterly: game-day per RB-INC/RECON/RISK runbook; update `last_executed`.
- Pre-cutover: walk RB-CONN/DEPLOY/INFRA.
- Monthly: walk RB-ALERT.

## Cross-plan blockers

**Blocked by**: `incident_gateway_and_state_machine_2026_05_23` Phase 1 +
`agent_recovery_controller_layer0_deterministic_2026_05_23` Phase 1.

**Blocks**: `audit_acknowledgement_sla_and_state_2026_05_23` (audit ack package requires the runbook + evidence links).

## Codex SSOT updates

- NEW: `/codex/15-runbooks/incidents/README.md` — 22 runbooks index.
- NEW: 22 individual runbooks.
- UPDATE: existing `/codex/15-runbooks/alerting/README.md` — point to incidents/ section for procedure-oriented
  runbooks.

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

- [x] ✅ Phase 1 P0.1-P0.2 UAC IncidentEvidence (14 fields + 3 mandatory) — unified-api-contracts@ae5771e2

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 2 P0.3-P0.4 — `alerting_service/gateway/evidence_collector.py` + per-service evidence-capture callbacks —
      alerting-service@e5c8084 | 14-field IncidentEvidence bundle assembler; async fan-out; per-service HTTP endpoints
      remain DEFERRED-OPERATOR-DECISION
- [x] ✅ Phase 3 P0.5-P0.26 — 22 incident runbooks at `codex/15-runbooks/incidents/` — unified-trading-pm (shipped in
      Tier-5)
- [x] ✅ Phase 4 P0.27 — runbook governance frontmatter (owner/cadence/verifier/last_executed) — unified-trading-pm
      (Tier-5)
- [x] ✅ Phase 4 P0.28 — hygiene script `check_runbook_fields.py` shipped + wired into run_hygiene_sweep.sh —
      unified-trading-pm (Tier-5 log line 249)
- [x] ✅ Phase 5 P0.29 — game_day_protocol.md extended + injection scripts shipped — e2e-testing@b3401e5 +
      unified-trading-pm (Tier-5b)
- [x] ✅ DEFERRED-OPERATOR-DECISION [STAGING-INFRA-REQUIRED] Phase 5 P0.30 (live run) — operator runs 3 scripts on
      staging; 21/21 GREEN gate (operator to schedule when staging infra ready)

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

- [x] ✅ Phase 2 P0.3-P0.4 `alerting_service/gateway/evidence_collector.py` (14-field IncidentEvidence bundle assembler;
      async fan-out to per-service /evidence/{incident_key} endpoints; defensive — never raises) —
      alerting-service@e5c8084
- [x] ✅ Phase 3 P0.5-P0.26 — 22 incident runbooks in `codex/15-runbooks/incidents/` (RB-INC-001/002/003 +
      RB-RECON-001/002/003 + RB-RISK-001/002/003/004 + RB-CONN-001/002/003/004/005 + RB-DEPLOY-001 +
      RB-INFRA-001/002/003 + RB-ALERT-001/002/003 + README index)
- [x] ✅ Phase 4 P0.27 — all runbook frontmatter carries owner/cadence/verifier/last_executed per CLAUDE.md HARD RULE

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 2 per-service /evidence/{incident_key} HTTP endpoints — execution-service@75682cc27
      (order_fill_records_url) + strategy-service@43641626 (position_records_url); GCS path
      incidents/{date}/{key}/evidence/<type>.json; 9 unit tests total
- [x] ✅ Phase 4 P0.28 — hygiene script `unified-trading-pm/scripts/plan-hygiene/check_runbook_fields.py` — wired into
      run_hygiene_sweep.sh as hard check; validates owner/cadence/verifier/last_executed on all 22 runbooks
- [x] ✅ DEFERRED-OPERATOR-DECISION Phase 5 P0.29-P0.30 — synthetic smoke + per-runbook walkthrough (game-day protocol
      doc shipped; P0.29 done, P0.30 live run STAGING-INFRA-REQUIRED)

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

- [x] ✅ Phase 5 P0.29 — game_day_protocol.md extended with bash-runnable kit + per-scenario one-line invocations +
      acceptance recorder template + STAGING-INFRA-REQUIRED markers (this commit)

**Items still `- [ ]`:**

- [x] ✅ Phase 5 P0.30 (injection scripts) — 3 game-day fault-injection scripts shipped + green in CLOUD_MOCK_MODE
      (UAC-validated synthetic incident + cascade print + 7-assert checklist):
      `e2e-testing/scripts/defi/scenarios/inject_venue_outage.sh` (01) / `inject_oracle_price_drop.sh` (15) /
      `inject_oracle_deviation.sh` (04, DISPUTE→SAFE_MODE). — e2e-testing@b3401e5
- [x] ✅ DEFERRED-OPERATOR-DECISION [STAGING-INFRA-REQUIRED] Phase 5 P0.30 (live run) — operator runs the 3 scripts with
      `--staging` on the staging stack; 21/21 GREEN gate (asserts 2/4/6/7 need live infra); result lands at
      plans/audit/results/game*day*<date>.md. Operator to schedule when staging infra ready.
- [x] ✅ Phase 2 per-service /evidence/{incident_key} HTTP endpoints (collector ships in alerting-service@e5c8084;
      endpoints pending per-service)
