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

Defined in `unified_api_contracts.dependency` (UAC):

| Class                     | Description                     | Examples                                    |
| ------------------------- | ------------------------------- | ------------------------------------------- |
| `EXTERNAL_API`            | Third-party REST/gRPC endpoints | Pyth, Alchemy, Helius, Sportradar           |
| `EXTERNAL_BLOCKCHAIN_RPC` | On-chain RPC providers          | Ethereum RPC, Solana RPC                    |
| `INTERNAL_SERVICE`        | Internal microservices          | instruments-service, MTDS, alerting-service |
| `INFRASTRUCTURE`          | Cloud platform primitives       | GCS, PubSub, BigQuery, Cloud KMS            |
| `MARKET_DATA_FEED`        | Real-time market data streams   | Bybit WS, Binance WS, Hyperliquid WS        |

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

Evaluated by `alerting_service.rules.evaluate_dependency_health(dependency_id, current_outage_seconds)`:

```
outage < expected_recovery_time                              → None (no alert)
outage in [expected, expected + warning_buffer]              → WARN
outage in [warning+buffer, warning+buffer + human_inv_buffer (900s)] → SEV1
outage > hard_escalation_seconds                                  → SEV0
outage >= expected_recovery_time AND fallback_available=False     → SEV0
```

Ships as: `alerting-service@839cb5f` (`evaluate_dependency_health()` + `evaluate_dependency_recovered()`).

## Enforcement

- Startup: `deployment-service/scripts/load_dependency_policies.py` parses YAML + validates against Pydantic schema
- Runtime: alerting-service buffers + escalates per policy; wires into `connectivity_rules.py`
- Tests: `@pytest.mark.dependency_fallback_<dep_id>` suite; CI: `pytest -m dependency_fallback`
- Nightly: dependency-fallback suite must be green

## Anti-patterns

- Hard-coded thresholds in service code — all thresholds must be registry-driven via `dependency_health_policies.yaml`
- Adding a new integration without a corresponding YAML entry
