---
scope: [engineer, admin]
title: CIRCUIT_BREAKER_OPEN Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when an execution-service per-(service, venue) circuit breaker transitions to OPEN. Service
  degrades; new orders blocked on that venue + service path. Auto-recovers via half-open retry; manual override only
  when auto-recovery flaps.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/kill_switch_venue_disconnect.md
  - codex/15-runbooks/alerting/order_rejection_spike.md
execution:
  owner: on-call operator (Ikenna / Harsh by rotation)
  cadence: on-demand (incident response only; fires when CIRCUIT_BREAKER_OPEN alert pages)
  verifier: circuit breaker transitions CLOSED within SLO window; orders resume on affected venue
  last_executed: never
---

# `CIRCUIT_BREAKER_OPEN` Runbook

> **What this is:** the per-(service, venue) circuit transitioned from CLOSED → OPEN. Indicates venue health degraded
> beyond the failure-rate threshold. Auto-recovers on half-open retry success. Operator only intervenes when half-open
> retries flap repeatedly OR the OPEN state lasts > 5min (which trips the kill-switch).

## TL;DR

A circuit breaker opened on one of the execution-service or features-service per-venue paths. The breaker is
operating-as-designed: it's protecting the venue (and us) from a flapping connection. Auto-half-open retry will close it
if the venue recovers within ~60s. Operator only acts if (a) the breaker stays OPEN for > 5 min (then
`KILL_SWITCH_VENUE_DISCONNECT` cascades), or (b) the breaker flaps OPEN-CLOSED-OPEN repeatedly within minutes.

## Trigger condition

- **Code:** `CIRCUIT_BREAKER_OPEN` (UAC `AlertCode`).
- **Pattern (fnmatch):** `CIRCUIT_BREAKER_OPEN`.
- **Threshold key:** none (binary state transition).
- **Default value:** N/A — circuit breaker's own internal failure-rate config drives this; see
  `unified-api-contracts/unified_api_contracts/internal/reference/circuit_breaker_config.py`.
- **Emitter(s):** `execution-service`, `features-service (onchain family)`, `features-cross-service`,
  `market-tick-data-service` — any service that wraps a venue adapter via the standard circuit-breaker decorator emits
  this.
- **Upstream signal:** ≥ N consecutive failures within window (default 5 in 60s) on the venue adapter — see
  `circuit_breaker_config.py` for per-adapter overrides.
- **De-dup window:** 30s — flapping breaker emits one alert per 30s window.

## Severity + paging

- **Severity:** `CRITICAL`.
- **Paging channels:** `PAGERDUTY`, `TELEGRAM`.
- **Triggers kill-switch:** **FALSE** (binary alert; the upstream `KILL_SWITCH_VENUE_DISCONNECT` fires separately if the
  OPEN persists > 5 min).
- **PagerDuty service:** `uts-prod-live-trading` P1.

## Diagnosis (first 5 minutes)

1. **Acknowledge** within 5 min.
2. **Pull alert payload:**
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
   Note: `payload.service` (e.g. `execution-service`), `payload.venue` (e.g. `bybit`), `payload.failure_count`,
   `payload.failure_window_seconds`, `payload.last_error_message`.
3. **Check half-open retry status** by tailing the service's events:
   ```bash
   gcloud storage cat gs://${PROJECT_ID}-events/events/<service>/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl \
     | jq -c "select(.metadata.details.venue==\"<venue>\")" | tail -10
   ```
   Look for `CIRCUIT_HALF_OPEN` followed by `CIRCUIT_CLOSED` (recovery, UAC `LifecycleEvent` names) or a re-emitted
   `CIRCUIT_OPEN` with an incremented backoff cycle counter (failed retry — alerting-service then routes the
   `CIRCUIT_BREAKER_BACKOFF_ESCALATING` AlertCode based on the counter).
4. **Identify root cause via last_error_message** in the payload. Common patterns:
   - `429 Too Many Requests` → rate-limit hit; auto-recovery via backoff usually works.
   - `502 Bad Gateway` / `503 Service Unavailable` → venue-side outage; wait for half-open success.
   - `401 Unauthorized` → API key rotated upstream; needs manual intervention.
   - `Connection timeout` / `DNS resolution failed` → local connectivity issue.
   - `SSL handshake failed` → upstream cert change; needs manual cert refresh.
5. **Cross-check with status page** + ping (per [`kill_switch_venue_disconnect.md`](./kill_switch_venue_disconnect.md)
   diagnosis step 3).

## Resolution paths

### Path 1 — Auto-recovery (half-open retry succeeds)

If diagnosis step 3 shows `CIRCUIT_HALF_OPEN` then `CIRCUIT_CLOSED` (UAC `LifecycleEvent` names) within 60-120s, no
operator action required. Watch:

```bash
watch -n 30 'gcloud storage cat gs://${PROJECT_ID}-events/events/<service>/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl \
  | jq -c "select(.event==\"CIRCUIT_CLOSED\" and .metadata.details.venue==\"<venue>\")" | tail -1'
```

**Success:** `CIRCUIT_CLOSED` event for the venue + a successful order/fetch within 60s thereafter.

### Path 2 — API key / cert / DNS fix

If `last_error_message` indicates a credentials / cert / DNS issue (per diagnosis step 4):

1. **API key:** rotate via Secret Manager:
   ```bash
   echo "<new_key>" | gcloud secrets versions add <venue>-api-key --data-file=-
   ```
   `ApiKeyReloader` in execution-service picks up new version within 60s; circuit auto-closes once next half-open retry
   succeeds.
2. **Cert:** trigger a DNS / cert refresh:
   ```bash
   gcloud compute ssh <service>-vm --zone=asia-northeast1-c \
     --command="sudo systemctl restart systemd-resolved"
   ```
3. **DNS poisoning:** investigate VPC DNS config; consider failing over to backup DNS (8.8.8.8) temporarily.

**Success:** circuit auto-closes within 5 min after fix; verify per Path 1.

### Path 3 — Manual circuit reset (last resort)

If half-open retry fails repeatedly AND root cause is not credentials / cert / DNS, force-close the circuit. Risky —
only use when you're confident the venue is healthy:

```bash
# Use execution-service admin endpoint (requires admin token)
curl -X POST -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://${EXECUTION_SERVICE_URL}/admin/circuit-breaker/reset" \
  -d '{"service":"<service>","venue":"<venue>"}'
```

If the reset works but circuit re-opens within minutes, the venue is genuinely unhealthy — escalate to
[`kill_switch_venue_disconnect.md`](./kill_switch_venue_disconnect.md) Path 3 (hedge roll to backup).

**Success:** circuit CLOSED + 5+ successful operations + no re-open within 5 min.

## Rollback

- **Undoing manual reset:** none — if the reset was wrong, the breaker will re-open on the next failure burst, which is
  the correct safety behaviour.
- **Undoing API-key rotation:** previous version is still in Secret Manager; pin via:
  ```bash
  gcloud secrets versions enable <previous_version_id> --secret=<venue>-api-key
  ```

## Common false-positives

- **Burst of 5+ failures during a benign rate-limit:** some venues throttle aggressively for ~30s after a quota refresh
  boundary. Symptom: circuit opens then auto-closes within 60s. Action: ack + log.
- **Breaker opens during deploy:** rolling restart of a service may cause a momentary failure burst. Symptom: alert
  timestamp aligns with deploy window. Action: ack + verify deploy completed cleanly.

If FP > 10% per 24h sustained on the same venue, raise via [`threshold-tuning.md`](./threshold-tuning.md) — circuit
config (failure window or N) likely needs widening.

## Escalation criteria + targets

Escalate to tier-3 strategy lead when:

- Circuit OPEN > 5 min (means `KILL_SWITCH_VENUE_DISCONNECT` will cascade).
- Multiple venues open simultaneously (correlated upstream issue).
- Path 1 + 2 + 3 all fail.

## Success criteria

- Circuit `CLOSED` for the (service, venue) pair.
- 5+ successful operations within 5 min after CLOSED.
- DART Active Alerts shows alert `resolved`.
- For >5 min OPEN events: post-incident write-up filed.

## Post-incident

Required for circuit-breaker events that lasted > 5 min OR cascaded to KILL_SWITCH_VENUE_DISCONNECT. Action items:
circuit-config tuning, venue health-monitoring improvements, backup-venue routing review.

## Cross-references

- **Cascade target:** [`kill_switch_venue_disconnect.md`](./kill_switch_venue_disconnect.md).
- **Related:** [`order_rejection_spike.md`](./order_rejection_spike.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Circuit-breaker config:**
  `unified-api-contracts/unified_api_contracts/internal/reference/circuit_breaker_config.py`.
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
