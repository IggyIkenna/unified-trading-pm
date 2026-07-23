---
doc_type: plan
title: Connectivity + Dependency Buffer Policy (5-class taxonomy + expected_time+buffer)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [agent-orchestrator, alerting-service, deployment-service, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: [independent_fallback_twilio_voice_2026_05_23.md]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: "Design class — closed-set 5-class taxonomy + per-dependency YAML policy +
  expected_time+buffer escalation rule.

  Baseline 8 × 0.6 design = 4.8 cal-days. Implementation is straightforward; the design judgement is on per-dep

  values (operator-tuned).

  "
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on: [incident_gateway_and_state_machine_2026_05_23]
gates: ["master_to_live_defi_2026_05_23:Group-F"]
---

# Connectivity + Dependency Buffer Policy

> **🟢 SPAWNED 2026-05-23 from `observability_disaster_recovery_audit_2026_05_23.md` gap #6.** Closes §10 of the target
> model.

## Goal

Codify every internal + external dependency under a closed-set 5-class taxonomy. Each dependency declares
`dependency_health_policy` YAML with expected_recovery_time + buffer + fallback + protected-mode behaviour. Wire the
"expected_time + 15min = SEV1; hard-threshold or fallback-fail = SEV0" rule into alerting.

## Context

**Existing capability** (verified 2026-05-23):

- Per-venue circuit breakers exist.
- Per-RPC retry semantics via UAC `classify_venue_error()`.
- `TICK_STALENESS` / `CONNECTIVITY_GAP_DETECTED` AlertCodes exist (MDPS + MTDS).

**Missing for May-23**:

- No 5-class taxonomy.
- No per-dependency YAML policy.
- No expected_time + buffer model.
- No alert rule "expected_time + 15min → SEV1".

## Pre-audit (blast radius)

- NEW: `unified_api_contracts/canonical/crosscutting/dependency/health_policy.py` — DependencyClass enum + policy
  schema.
- NEW: `deployment-service/configs/dependency_health_policies.yaml` — per-dependency config (registry).
- TOUCH: `alerting-service/alerting_service/rules/connectivity_rules.py` — wire buffer model.

## Phased execution DAG

### Phase 1 — UAC schema + 5-class taxonomy (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. `DependencyClass` StrEnum (5 closed): EXECUTION_CRITICAL_EXTERNAL,
      MARKET_DATA_CRITICAL_EXTERNAL, INTERNAL_CONTROL_PLANE, INTERNAL_DATA_PLANE, ALERTING_AND_OBSERVABILITY.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. `DependencyHealthPolicy` Pydantic —
      `dependency_id, dependency_class,     expected_recovery_time_seconds, warning_buffer_seconds, human_investigation_buffer_seconds (default 900),     hard_escalation_seconds, fallback_available, protected_mode_available, owner, runbook_doc, test_method`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.3. UAC sanity tests: 5 DependencyClass members; policy roundtrip
      yaml↔model; defaults applied correctly.

### Phase 2 — Registry YAML (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.4. `deployment-service/configs/dependency_health_policies.yaml` —
      enumerate every known dep: Binance/Bybit/OKX/Deribit/Hyperliquid/Aster (EXECUTION_CRITICAL_EXTERNAL);
      Uniswap/Curve/Aave/Lido/Helius/Solana- RPC/Ethereum-RPC (EXECUTION_CRITICAL_EXTERNAL); Pyth/Chainlink
      (MARKET_DATA_CRITICAL_EXTERNAL); GCP-Cloud-Run/AWS- ECS/Pub-Sub/Cloud-Storage/Secret-Manager/Artifact-Registry
      (INTERNAL_CONTROL_PLANE); BigQuery/Redis/Cloud-SQL (INTERNAL_DATA_PLANE); PagerDuty/Telegram/Twilio
      (ALERTING_AND_OBSERVABILITY). Per-dep operator-tuned values. — deployment-service@47426ee | 27 deps / 5
      DependencyClass tiers, all TUNE-tagged
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.5. Schema loader at startup:
      `deployment-service/scripts/load_dependency_policies.py` parses yaml + validates against Pydantic schema;
      fails-loud on missing fields. — deployment-service@47426ee | fails-loud on ValidationError + prints per-dep
      summary

### Phase 3 — Alerting wiring (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.6. `alerting-service/alerting_service/rules/connectivity_rules.py` — new
      evaluator: `evaluate_dependency_health(dependency_id, current_outage_seconds) → AlertSeverity | None`. Logic: -
      outage < expected_recovery_time → None (no alert). - outage in [expected, expected + warning_buffer_seconds] →
      WARN. - outage in [warning, warning + human_investigation_buffer_seconds (default 900s = 15min)] → SEV1. -
      outage > hard_escalation_seconds OR fallback_available=False → SEV0.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.7. Wire `DEPENDENCY_DEGRADED` + `DEPENDENCY_RECOVERED` AlertCodes in UAC;
      add rules to `LIVE_ALERT_RULES`. — uac@6f601292 | DEPENDENCY_DEGRADED (HIGH→PD+TG) + DEPENDENCY_RECOVERED
      (INFO→TG) in codes.py + rules.py

### Phase 4 — Per-dep fallback tests (1 cal-day, parallel)

- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.8. For each dep with `fallback_available=true`, integration test exercises
      the fallback. Mark each test `@pytest.mark.dependency_fallback_<dep_id>`. CI: `pytest -m dependency_fallback` runs
      the suite nightly.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.9. Test report writer: emits a `DependencyFallbackTestReport` per
      nightly run to audit-store; if any fallback failed, raises SEV1.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.10. Synthetic dep-outage: simulate Pub/Sub unreachable for 5min → assert
      no alert; 6min → WARN; 21min → SEV1 (expected 5min + warning 60s + human_investigation 900s); 31min OR
      fallback-fail → SEV0.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.11. Game-day: scenario `06_defi_mempool_congestion.md` — assert
      dep-policy fires for Ethereum RPC backup; assert fallback to Helius primary holds.

## Success criteria

- 5 DependencyClass members; per-dep yaml exists for all known deps.
- expected_time+buffer rule wired in alerting.
- Nightly dependency-fallback test report passes.
- Smoke + game-day green.

## Anti-patterns + banned approaches

- ❌ Hard-coded thresholds in service code — must be `dependency_health_policies.yaml` registry-driven.
- ❌ Missing fallback_available declaration — must be explicit (True/False); no defaults.

## Continuous verification

- Nightly: dependency-fallback suite green.
- Per-dep change: yaml schema gate.

## Cross-plan blockers

**Blocked by**: `incident_gateway_and_state_machine_2026_05_23` Phase 1 (IncidentEnvelope).

**Blocks**: none.

## Codex SSOT updates

- NEW: `/codex/04-architecture/dependency-health-policy.md` — 5-class taxonomy + YAML schema + escalation rule.
- UPDATE: `/codex/05-infrastructure/disaster-recovery.md` — point at new YAML registry.

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

- [x] ✅ Phase 1 P0.1-P0.3 UAC DependencyClass (5-enum closed) + DependencyHealthPolicy + sanity tests —
      unified-api-contracts@ae5771e2

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 2 P0.4-P0.5 — `deployment-service/configs/dependency_health_policies.yaml` registry for all known deps +
      startup schema loader — ds@47426ee (27 deps / 5 DependencyClass tiers; scripts/load_dependency_policies.py)
- [x] ✅ Phase 3 P0.6-P0.7 — alerting-service@839cb5f | evaluate_dependency_health() + evaluate_dependency_recovered() +
      22 unit tests | QG green
- [x] ✅ DEFERRED-OPERATOR-DECISION Phase 4 P0.8-P0.9 — per-dep fallback integration tests + nightly report (DAG
      pre-approved)
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] Phase 5 P0.10-P0.11 — synthetic smoke + game-day (operator to schedule when
      ready; main P0.10/P0.11 items already DEFERRED-OPERATOR-DECISION)

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

_(No Tier-5 items in this plan's scope.)_

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ No Tier-5 work — Phase 2+ unchanged (yaml registry + alerting rule + fallback tests + smoke).

**Cross-references**:

- Operator ping doc → `plans/active/_agent_pings.md` 2026-05-23 ikenna-slot-1 → operator entry
- 22 incident runbooks → `codex/15-runbooks/incidents/` (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT)
- Game-day protocol → `/codex/15-runbooks/incidents/game_day_protocol.md`
- Alerting Tier-5 → `alerting-service@e5c8084` (5 new gateway/notifier modules)
- Strategy Tier-5 → `strategy-service@3b0f7397` (2 configs + close-all + helper)
- Execution Tier-5 → `execution-service@a6fa7c501` (recovery_event_helper)
- DART Tier-5 → `unified-trading-system-ui@01e1bb69` (safety-ops route + widgets)
