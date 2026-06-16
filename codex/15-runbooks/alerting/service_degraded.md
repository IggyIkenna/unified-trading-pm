---
scope: [engineer, admin]
title: SERVICE_DEGRADED Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when a workspace service emits SERVICE_DEGRADED — running but operating below full functionality.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/circuit_breaker_open.md
  - codex/15-runbooks/alerting/defi_feature_stale.md
---

# `SERVICE_DEGRADED` Runbook

> **What this is:** a service self-reported degraded mode via `data_freshness` callback or `health_router`. Alive but
> not fully functional — typically a downstream dependency is partially broken. WARN-severity.

## TL;DR

A service is running but in degraded mode (subset of features unavailable, cache stale, partial dependency failures).
Operator inspects the degradation reason; restart only if not auto-recovering.

## Trigger condition

- **Code:** `SERVICE_DEGRADED` (UAC `AlertCode`).
- **Pattern (fnmatch):** `SERVICE_DEGRADED`.
- **Threshold key:** none (event-driven).
- **Emitter(s):** any service via `make_health_router` from UTL — emits when internal health returns `degraded`.
- **Upstream signal:** service-specific (cache miss > 50%, feature compute > 2× expected, ledger reconciliation lag
  > 5min, > 1 venue circuit-breaker OPEN).
- **De-dup window:** 300s on `(service_name, degradation_reason)`.

## Severity + paging

- **Severity:** `WARN`.
- **Paging channels:** `TELEGRAM`.
- **Triggers kill-switch:** **FALSE**.
- **PagerDuty service:** N/A.

## Diagnosis (first 5 minutes)

1. **Acknowledge** in Telegram.
2. **Pull alert payload** via PubSub.
3. **Hit service health endpoint:**
   `curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" https://${SERVICE_URL}/health | jq`.
4. **Tail recent service events:**
   `gcloud storage cat gs://${PROJECT_ID}-events/events/<service>/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl | tail -50 | jq -c 'select(.metadata.severity=="WARNING" or .metadata.severity=="ERROR")'`.
5. **Check correlated codes** — `CIRCUIT_BREAKER_OPEN` very often co-fires.

## Resolution paths

### Path 1 — Wait for upstream to recover

If diagnosis identifies a downstream issue likely to recover quickly: `watch -n 60 "curl -sH ... | jq '.status'"`.

**Success:** `/health` returns `healthy` sustained 5 min.

### Path 2 — Restart the affected service

If degraded > 15 min AND upstream healthy:

```bash
gcloud run services update <service> --region=asia-northeast1 --update-env-vars=FORCE_RESTART=$(date +%s)
# OR VM-based:
gcloud compute instances reset <vm-name> --zone=asia-northeast1-c
```

Wait 60-120s; confirm via Path 1.

**Success:** post-restart `/health` returns `healthy` within 5 min.

### Path 3 — Failover / pause downstream consumers

If P0 service AND restart didn't help: tier-3 review, region failover or rollback.

**Success:** affected workflows isolated.

## Rollback

- **Undoing restart:** none needed.
- **Undoing rollback:** redeploy via standard CI/CD.

## Common false-positives

- **Health-check transient flap:** single slow query returns `degraded`, resolves within 60s.
- **Deploy window:** new pod cold-start briefly degraded.

If FP > 30% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 when:

- Service is execution-service / strategy-service / position-balance-monitor.
- Degradation > 30 min sustained.
- Restart didn't recover.

## Success criteria

- `/health` returns `healthy` sustained 5 min.
- Telegram alert no longer re-firing.

## Post-incident

Required if Path 2 (restart) or 3 (failover) was used.

## Cross-references

- **Co-firing:** [`circuit_breaker_open.md`](./circuit_breaker_open.md),
  [`defi_feature_stale.md`](./defi_feature_stale.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
