---
title: "Connectivity + Dependency Buffer Policy (5-class taxonomy + expected_time+buffer)"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: |
  Design class — closed-set 5-class taxonomy + per-dependency YAML policy + expected_time+buffer escalation rule.
  Baseline 8 × 0.6 design = 4.8 cal-days. Implementation is straightforward; the design judgement is on per-dep
  values (operator-tuned).
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on:
  - incident_gateway_and_state_machine_2026_05_23
gates:
  - master_to_live_defi_2026_05_23:Group-F
related_plans:
  - independent_fallback_twilio_voice_2026_05_23.md
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

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. `DependencyClass` StrEnum (5 closed): EXECUTION_CRITICAL_EXTERNAL, MARKET_DATA_CRITICAL_EXTERNAL,
      INTERNAL_CONTROL_PLANE, INTERNAL_DATA_PLANE, ALERTING_AND_OBSERVABILITY.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. `DependencyHealthPolicy` Pydantic —
      `dependency_id, dependency_class,     expected_recovery_time_seconds, warning_buffer_seconds, human_investigation_buffer_seconds (default 900),     hard_escalation_seconds, fallback_available, protected_mode_available, owner, runbook_doc, test_method`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.3. UAC sanity tests: 5 DependencyClass members; policy roundtrip yaml↔model; defaults applied
      correctly.

### Phase 2 — Registry YAML (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.4. `deployment-service/configs/dependency_health_policies.yaml` — enumerate every known dep:
      Binance/Bybit/OKX/Deribit/Hyperliquid/Aster (EXECUTION_CRITICAL_EXTERNAL); Uniswap/Curve/Aave/Lido/Helius/Solana-
      RPC/Ethereum-RPC (EXECUTION_CRITICAL_EXTERNAL); Pyth/Chainlink (MARKET_DATA_CRITICAL_EXTERNAL); GCP-Cloud-Run/AWS-
      ECS/Pub-Sub/Cloud-Storage/Secret-Manager/Artifact-Registry (INTERNAL_CONTROL_PLANE); BigQuery/Redis/Cloud-SQL
      (INTERNAL_DATA_PLANE); PagerDuty/Telegram/Twilio (ALERTING_AND_OBSERVABILITY). Per-dep operator-tuned values.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.5. Schema loader at startup: `deployment-service/scripts/load_dependency_policies.py` parses yaml +
      validates against Pydantic schema; fails-loud on missing fields.

### Phase 3 — Alerting wiring (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.6. `alerting-service/alerting_service/rules/connectivity_rules.py` — new evaluator:
      `evaluate_dependency_health(dependency_id, current_outage_seconds) → AlertSeverity | None`. Logic: - outage <
      expected_recovery_time → None (no alert). - outage in [expected, expected + warning_buffer_seconds] → WARN. -
      outage in [warning, warning + human_investigation_buffer_seconds (default 900s = 15min)] → SEV1. - outage >
      hard_escalation_seconds OR fallback_available=False → SEV0.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.7. Wire `DEPENDENCY_DEGRADED` + `DEPENDENCY_RECOVERED` AlertCodes in UAC; add rules to
      `LIVE_ALERT_RULES`.

### Phase 4 — Per-dep fallback tests (1 cal-day, parallel)

- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.8. For each dep with `fallback_available=true`, integration test exercises the fallback. Mark each test
      `@pytest.mark.dependency_fallback_<dep_id>`. CI: `pytest -m dependency_fallback` runs the suite nightly.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.9. Test report writer: emits a `DependencyFallbackTestReport` per nightly run to audit-store; if any
      fallback failed, raises SEV1.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.10. Synthetic dep-outage: simulate Pub/Sub unreachable for 5min → assert no alert; 6min → WARN; 21min →
      SEV1 (expected 5min + warning 60s + human_investigation 900s); 31min OR fallback-fail → SEV0.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.11. Game-day: scenario `06_defi_mempool_congestion.md` — assert dep-policy fires for Ethereum RPC
      backup; assert fallback to Helius primary holds.

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

- NEW: `codex/04-architecture/dependency-health-policy.md` — 5-class taxonomy + YAML schema + escalation rule.
- UPDATE: `codex/05-infrastructure/disaster-recovery.md` — point at new YAML registry.
