---
doc_type: issue
title:
  DEPENDENCY_DEGRADED can never fire — the rule, codes, thresholds and config all exist, but nothing produces or
  consumes them
summary: >-
  evaluate_dependency_health() is defined, unit-tested, documented in codex, and backed by AlertCodes, alert rules,
  thresholds, a DependencyHealthPolicy schema, a validated dependency_health_policies.yaml and a startup loader — and is
  called by NOTHING. No handler in alerting-service imports connectivity_rules; no code anywhere computes or emits
  outage_seconds. So a dependency can exceed its expected recovery time and its hard escalation ceiling with
  fallback_available=False, and no DEPENDENCY_DEGRADED alert is ever raised and nobody is paged. The owning plan
  (connectivity_dependency_buffer_policy_2026_05_23) was ARCHIVED with the wiring step never done, which is what made a
  70%-built feature invisible.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-service, unified-api-contracts]
scope: [engineer]
tags: [alerting, dependency-health, dead-code, silent-failure, unwired]
related:
  [
    /plans/archive/2026_05/connectivity_dependency_buffer_policy_2026_05_23.md,
    /codex/04-architecture/dependency-health-policy.md,
    /codex/05-infrastructure/live-deployment-monitoring.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-12
last_updated: "2026-08-12"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-12 while verifying live-deployment-monitoring.md, which listed DEPENDENCY_DEGRADED as a lifecycle event.
  It is not one — it is an alerting-service AlertCode — and chasing that category error surfaced that the whole path is
  unwired.
depends_on: []
context_scope:
  [
    alerting-service/alerting_service/rules/connectivity_rules.py,
    alerting-service/alerting_service/subscribers/alert_subscriber.py,
    deployment-service/configs/dependency_health_policies.yaml,
  ]
---

# DEPENDENCY_DEGRADED can never fire

## What exists (all of it verified 2026-08-12)

| piece                                                                              | state            |
| ---------------------------------------------------------------------------------- | ---------------- |
| `AlertCode.DEPENDENCY_DEGRADED` / `DEPENDENCY_RECOVERED` (UAC `alerting/codes.py`) | ✅ built         |
| Alert rules + thresholds (UAC `alerting/rules.py`, `thresholds.py`)                | ✅ built         |
| `DependencyHealthPolicy` schema (UAC `crosscutting/dependency/health_policy.py`)   | ✅ built         |
| `deployment-service/configs/dependency_health_policies.yaml`                       | ✅ built         |
| `load_dependency_policies.py` (fails loud on bad config)                           | ✅ built         |
| `evaluate_dependency_health()` + `tests/unit/rules/test_connectivity_rules.py`     | ✅ built + green |
| **a producer that computes `outage_seconds`**                                      | ❌ **absent**    |
| **a handler/subscriber that calls the rule**                                       | ❌ **absent**    |

## Evidence

- `rg "evaluate_dependency_health"` across the fleet, excluding tests, returns only its own definition plus DOC/comment
  mentions. No call site.
- No module under `alerting_service/` (excluding tests) references `dependency_id`, `dependency_class`, or
  `DEPENDENCY_`. Every other rule family is wired by an explicit import in a `*_event_handler.py` registered in
  `subscribers/alert_subscriber.py`; `connectivity_rules` is imported by nothing.
- `rg "outage_seconds"` excluding tests hits only the rule, the UAC contracts, the config, and docs — nothing MEASURES
  it.
- `load_dependency_policies.py`'s own docstring says it validates config "before the alerting-service **wires** the
  evaluate_dependency_health() rule" — the wiring was always a known future step.

## Why it stayed invisible

The unit test is green and always will be: it calls the function directly with synthetic `outage_seconds`, which proves
the ladder's arithmetic and nothing about whether the ladder is ever reached. Same shape as the other silent-coverage
failures found this week — a green unit test sitting beside a non-existent integration.

Archival is the second half. The owning plan was archived as complete while its last step was unbuilt, so the gap left
the active corpus without ever being done.

## Todos

- [ ] [BACKEND] P1. **Decide the producer.** Nothing computes dependency outage duration today. Options: (a) the
      dependency owner emits a lifecycle event on transition and alerting derives duration; (b) a poller in
      alerting-service tracks last-healthy timestamps per `dependency_id` and evaluates on a tick. (b) is self-contained
      and needs no changes in dependent services; (a) is more accurate but touches every dependency owner. Done-when:
      choice recorded here with its trade-off.
- [ ] [BACKEND] P1. Wire the subscriber once the producer exists — a `*_event_handler.py` importing
      `evaluate_dependency_health` + `evaluate_dependency_recovered`, registered in `subscribers/alert_subscriber.py`,
      following the `recon_freeze_event_handler` pattern.
- [ ] [BACKEND] P1. **Add an integration test that fails if the path is unwired**, not another unit test of the
      function. It must drive a simulated outage from the producer's entry point and assert a routed alert. The existing
      unit test would pass unchanged today with the feature completely dead.
- [ ] [DOCS] P2. `/codex/04-architecture/dependency-health-policy.md` reads as though the rule is live ("Ships as:
      `alerting-service@839cb5f`"). Add a status line stating it is contract-and-config only until the todos above land,
      so the next reader is not misled the way this doc misled me.

## Progress Log

- 2026-08-12 — Filed. Found while correcting `live-deployment-monitoring.md`, which listed `DEPENDENCY_DEGRADED` in its
  lifecycle-events table. It is an alerting-service AlertCode, not a lifecycle event a workload emits — a category
  error. Chasing which of the two was right surfaced that neither producer nor consumer exists.
