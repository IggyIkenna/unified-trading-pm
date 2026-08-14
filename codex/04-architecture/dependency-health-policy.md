---
doc_type: codex-ssot
title: Dependency Health Policy
summary:
  Closed-set 5-class DependencyClass taxonomy + per-dependency health-policy YAML (recovery/warning/escalation buffers)
  evaluated by alerting-service into severity-graded WARN/SEV1/SEV0 alerts.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags: [dependency-health, alerting, escalation, monitoring, registry, observability]
related:
  [
    /codex/03-observability/data-feed-sla-registry.md,
    /codex/04-architecture/alerting-batch-live.md,
    /codex/03-observability/alerting.md,
  ]
created: 2026-05-26
authoritative_for: [DependencyClass taxonomy and dependency-health-policy escalation rule]
referenced_by:
owner:
last_reviewed: 2026-05-29
code_refs:
---

# Dependency Health Policy

Shipped: 2026-05-23. Plan: `plans/active/connectivity_dependency_buffer_policy_2026_05_23.md` (archived).

## Overview

Every internal and external dependency is codified under a closed-set 5-class taxonomy. Each dependency declares a
`dependency_health_policy` YAML entry with expected recovery time, warning buffer, and hard-escalation rule. The
alerting-service evaluates these policies in real-time and fires severity-graded alerts.

## DependencyClass taxonomy (5 members)

> **CORRECTED 2026-08-14 — every one of the five names in the previous version of this table was WRONG.** It listed
> `EXTERNAL_API` / `EXTERNAL_BLOCKCHAIN_RPC` / `INTERNAL_SERVICE` / `INFRASTRUCTURE` / `MARKET_DATA_FEED`; none of those
> members exists. The table below is read from the enum. This mattered: an agent reasoning about live-path failure
> handling quoted "INTERNAL_SERVICE" back to the operator as though our own microservices were classified, which they
> are not (see the coverage note below).

Defined in `unified_api_contracts.canonical.crosscutting.dependency.health_policy.DependencyClass`:

| Class                           | What it covers                       | Registered examples                        |
| ------------------------------- | ------------------------------------ | ------------------------------------------ |
| `EXECUTION_CRITICAL_EXTERNAL`   | venues/protocols an order depends on | binance_rest, bybit_rest, uniswap_v3, aave |
| `MARKET_DATA_CRITICAL_EXTERNAL` | price/oracle feeds                   | pyth_solana, chainlink_ethereum            |
| `INTERNAL_CONTROL_PLANE`        | cloud primitives that run the fleet  | gcp_cloud_run, aws_ecs, gcp_secret_manager |
| `INTERNAL_DATA_PLANE`           | cloud data primitives                | gcp_bigquery, redis_primary, gcp_cloud_sql |
| `ALERTING_AND_OBSERVABILITY`    | the notification path itself         | pagerduty, telegram_bot, twilio_voice_sms  |

The classes are criticality-graded by design, which is the useful property: `EXECUTION_CRITICAL_EXTERNAL` losing a venue
is not the same event as `ALERTING_AND_OBSERVABILITY` losing Telegram.

### Coverage gap — OUR OWN SERVICES ARE NOT REGISTERED (2026-08-14)

All **27** registered dependencies are external venues, RPCs, cloud primitives, or notification channels. **Zero** are
our own microservices: there is no entry for execution-service, strategy-service, risk, or reconciliation. "INTERNAL"
here means _cloud infrastructure we depend on_, NOT _our services depending on each other_. So a silent strategy-service
breaches no policy, because no policy describes it.

Tracked in `/plans/active/issues/live_path_has_no_stale_producer_revocation_2026_08_14.md`.

## YAML schema (per-dependency entry)

Registry: `deployment-service/configs/dependency_health_policies.yaml` (27 entries as of ds@47426ee).

```yaml
dependency_id: string # unique slug (e.g. "ethereum-rpc-primary")
dependency_class: DependencyClass
expected_recovery_time_seconds: int # vendor SLA or historical median
warning_buffer_seconds: int # added to expected before WARN fires
human_investigation_buffer_seconds: int # default 900 (15 min)
hard_escalation_seconds: int # absolute outage length → SEV0
fallback_available: bool
protected_mode_available: bool
owner: string # team slug
runbook_doc: string # path in codex/15-runbooks/
test_method: string # pytest mark or description
```

## Escalation rule

Evaluated by `alerting_service.rules.evaluate_dependency_health(event_details, policy)`:

```
outage < expected_recovery_time                                          → None (no alert)
outage in [expected, expected + warning_buffer]                          → WARN
outage in [warning+buffer, warning+buffer + human_inv_buffer (900s)]     → SEV1
outage >= hard_escalation_seconds                                        → SEV0
outage >= expected_recovery_time AND fallback_available=False            → SEV0
```

**No-fallback is a severity floor, not a duration bypass (fixed 2026-08-13)**: `fallback_available=False` alone no
longer escalates to SEV0 on any `outage > 0` — that shipped bug would have paged on a single failed probe for the 10
policies with `fallback_available: false`. It now requires the outage to have already reached
`expected_recovery_time_seconds` before "no fallback" raises severity to SEV0.

## Status — WIRED end-to-end (2026-08-13)

This was contract-and-config-only through 2026-08-12 (rule + schema + YAML shipped, but nothing produced
`outage_seconds` or called the rule — see the now-closed
`/plans/archive/2026_08/issues/dependency_health_alerting_never_wired_2026_08_12.md`). As of 2026-08-13 the path is
wired:

- **Rule** (with the duration-floor fix above): `alerting-service@324ffa5`
- **Producer + subscriber**: `alerting-service@42347de` — `dependency_health_prober.py` (probe-driven, dispatches on
  each policy's `test_method`, N-consecutive-failure gate before the outage clock starts) +
  `dependency_health_event_handler.py`, registered in `subscribers/alert_subscriber.py` under `DEPENDENCY_DEGRADED` /
  `DEPENDENCY_RECOVERED`
- **Integration test proving the wire, not just the arithmetic**: `alerting-service@7291bee`
  (`tests/integration/test_dependency_health_wiring.py`) — drives a simulated outage through the real
  producer→handler→rule→router chain (only the router boundary mocked); the pre-existing unit tests of
  `evaluate_dependency_health` alone would still pass with the path fully unwired.

## Enforcement

- Startup: `deployment-service/scripts/load_dependency_policies.py` parses YAML + validates against Pydantic schema
- Runtime: alerting-service buffers + escalates per policy; wires into `connectivity_rules.py`
- Tests: `@pytest.mark.dependency_fallback_<dep_id>` suite; CI: `pytest -m dependency_fallback`
- Nightly: dependency-fallback suite must be green

## This policy ALERTS. It does not ACT. (2026-08-14)

The escalation ladder above produces WARN / SEV1 / SEV0 **alerts**. Nothing consumes it to change behaviour:
`rg -l 'health_policy|DependencyHealth'` over execution-service (1384 `.py`) and strategy-service (1033 `.py`) returns
**zero**. A SEV0 on a dependency pages a human and halts nothing — no retry policy is driven from it, no kill-switch
scope is armed by it, no admission is held.

That is worth stating plainly because the fields read like they govern behaviour: `expected_recovery_time_seconds`,
`hard_escalation_seconds`, `fallback_available` and `protected_mode_available` all describe what SHOULD happen, and none
of it is wired. The batch/data-pipeline side hit the identical failure mode — a complete, tested policy with no
actuator, which reads as finished — see `/plans/active/revocation_arming_2026_08_14.md`.

Until an actuator exists, treat this document as a paging contract, not a control contract.

## Anti-patterns

- Hard-coded thresholds in service code — all thresholds must be registry-driven via `dependency_health_policies.yaml`
- Adding a new integration without a corresponding YAML entry
