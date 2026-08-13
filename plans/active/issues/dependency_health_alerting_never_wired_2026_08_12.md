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
assigned_vm: planning
execution_scope: orchestrator-agent
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

- [x] [BACKEND] P1. **Decide the producer — RESOLVED 2026-08-12: (b), a probe-driven producer in alerting-service,
      dispatched on the policy's own `test_method` field.** See "Producer decision" below for the evidence and the
      trade-off accepted.
- [x] [BACKEND] **P0. Put a duration floor on the no-fallback branch BEFORE any producer is wired.** As written,
      `evaluate_dependency_health` ORs `not policy.fallback_available` into the CRITICAL branch with no minimum outage:
      any `outage > 0` — a single failed probe, 1 second — returns SEV0 `pagerduty+telegram`. **10 of 27 policies set
      `fallback_available: false`** (aave_v3, lido, gcp_pubsub, gcp_cloud_storage, gcp_secret_manager,
      gcp_artifact_registry, gcp_bigquery, redis_primary, gcp_cloud_sql, twilio_voice_sms), so wiring a prober today
      turns one flaky probe against Secret Manager into a 3am page. Fix: require N consecutive failed probes AND
      `outage >= expected_recovery_time_seconds` before the no-fallback escalation, so "no fallback" raises SEVERITY,
      never bypasses DURATION. This is a correctness bug in the shipped rule, independent of the wiring. — ✅ **DONE**:
      duration floor added — `no-fallback` now SEV0 only at `outage >= expected_recovery_time_seconds`;
      N-consecutive-probes gate documented as producer contract. `alerting-service@324ffa5` (rule + tests),
      `unified-api-contracts@6f63637d` (schema docstring), `deployment-service@c5a8f4b6` (loader string + yaml ladder).
- [ ] [BACKEND] P1. Wire the subscriber once the producer exists — a `*_event_handler.py` importing
      `evaluate_dependency_health` + `evaluate_dependency_recovered`, registered in `subscribers/alert_subscriber.py`,
      following the `recon_freeze_event_handler` pattern.
- [ ] [BACKEND] P1. **Add an integration test that fails if the path is unwired**, not another unit test of the
      function. It must drive a simulated outage from the producer's entry point and assert a routed alert. The existing
      unit test would pass unchanged today with the feature completely dead.
- [ ] [DOCS] P2. `/codex/04-architecture/dependency-health-policy.md` reads as though the rule is live ("Ships as:
      `alerting-service@839cb5f`"). Add a status line stating it is contract-and-config only until the todos above land,
      so the next reader is not misled the way this doc misled me.

## Producer decision (2026-08-12)

**Chosen: (b) — a probe-driven producer inside alerting-service, dispatching on each policy's `test_method`.**

The choice as originally framed ("dependency owner emits on transition" vs "poller tracks last-healthy") turned out not
to be a live choice, for three reasons found in the code:

1. **(a) is structurally impossible here.** All 27 policies are EXTERNAL venues/chains (binance_rest, uniswap_v3,
   helius_solana_rpc), cloud infrastructure (gcp_pubsub, redis_primary, gcp_cloud_sql) or third-party alerting
   (pagerduty, twilio). **Not one is an internal service of ours.** There is no "dependency owner" to emit a transition
   event — Binance will not publish our `CONNECTIVITY_DEGRADED`. The emitter would have to be whichever of our services
   happens to call the venue, and several call the same one, so outage state would be computed multiple times with
   conflicting clocks.
2. **The config already specifies the producer.** Every policy carries `test_method`, and it takes six distinct values —
   `synthetic_probe`, `healthcheck_endpoint`, `probe_publish_subscribe`, `probe_read_write`, `probe_query`,
   `probe_ping`. That field is a prober dispatch table; it has no other possible consumer. The original design intended
   a prober and the field survived while the prober did not.
3. **`CONNECTIVITY_DEGRADED` does not exist.** The rule's docstring says it consumes that event, but a fleet-wide `rg`
   finds the string in exactly one place: that docstring. It is not an `EventType`, not an `AlertCode`, not a schema.
   Option (a) would mean inventing the event type as well as the emitters.

**Shape**: an async prober in alerting-service, one `_dispatch` on `test_method` returning a per-dependency result, and
last-healthy timestamps kept per `dependency_id` so `current_outage_seconds` is derived rather than reported. Model it
on `unified_trading_library/treasury/custody_pinger.py`, which is the same pattern already working in this workspace
(`CustodyPinger.ping_all` → `_dispatch(source, config)` → per-source `_ping_*`). Keeping the prober in alerting-service
co-locates outage state with the evaluation that consumes it and adds no cross-service contract.

**Trade-off accepted — write this down where operators will read it**: a synthetic probe measures _the prober's_ view of
reachability, not the trading path's. An unauthenticated probe can succeed against a venue whose authenticated order
path is failing, and it can fail from one egress IP while the execution path is healthy. So probe-derived
`DEPENDENCY_DEGRADED` is a floor on dependency health, never a statement that execution is fine, and its absence must
never be read as "the venue is good". The corroborating signal — the execution path's own `classify_venue_error()`
results, which already exist — should be folded in as a second input later; it is deliberately out of scope here because
it would re-introduce the multi-emitter clock problem that ruled out (a).

## Progress Log

**na-eligibility-audit 2026-08-13**: RECLASSIFY_WHOLE — every open todo bounded/deterministic, flipped
`assigned_vm: NA -> planning` after full-sweep classification + conflict review (see run report).

- 2026-08-12 — Filed. Found while correcting `live-deployment-monitoring.md`, which listed `DEPENDENCY_DEGRADED` in its
  lifecycle-events table. It is an alerting-service AlertCode, not a lifecycle event a workload emits — a category
  error. Chasing which of the two was right surfaced that neither producer nor consumer exists.
- 2026-08-12 — Producer decided (see above): probe-driven, dispatched on `test_method`, modelled on `CustodyPinger`.
  Reading the config to make that call surfaced a **P0 correctness bug in the already-shipped rule** — the no-fallback
  branch escalates to SEV0 with no duration floor, so the 10 `fallback_available: false` policies would page on a single
  failed probe. That bug is latent only because the feature is dead; wiring the producer without fixing it first would
  convert a dormant defect into a pager storm. Ordering is now: floor → producer → subscriber → integration test.
- 2026-08-12 — Fixed two pointers that actively mislead the next implementer: `connectivity_rules.py` documented
  `CONNECTIVITY_DEGRADED` as its input event (no such event exists anywhere in the fleet), and
  `dependency_health_policies.yaml` cited the schema as `unified_api_contracts.canonical.crosscutting.dependency…` — a
  `canonical.*` path that is workspace-BANNED and not the real import (`unified_api_contracts.dependency`). Both also
  pointed at the owning plan as `plans/active/…` when it was archived to `plans/archive/2026_05/` in May. Shipped:
  `alerting-service@79beb47b0f` (docstring: NOT-WIRED banner + real input contract) and `deployment-service@2cd96940c8`
  (yaml header: real schema path + CONFIG-ONLY status).
