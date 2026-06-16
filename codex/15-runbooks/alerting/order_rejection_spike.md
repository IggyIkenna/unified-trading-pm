---
scope: [engineer, admin]
title: ORDER_REJECTION_SPIKE Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when venue order-reject rate spikes above threshold. Indicates venue health degradation before the
  circuit breaker has tripped.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/circuit_breaker_open.md
  - codex/15-runbooks/alerting/preflight_failed.md
---

# `ORDER_REJECTION_SPIKE` Runbook

> **What this is:** sustained spike in venue order rejects per minute. Distinct from `PREFLIGHT_FAILED` — these orders
> WERE submitted; the venue rejected them. Early-warning of venue health.

## TL;DR

Per-minute order-reject rate from a venue exceeded threshold (default 10/min over 5min window). Each reject is a
venue-side rejection AFTER the order was sent — could be rate limit, risk-engine throttling, post-only-rejected.

## Trigger condition

- **Code:** `ORDER_REJECTION_SPIKE` (UAC `AlertCode`).
- **Pattern (fnmatch):** `ORDER_REJECTION_SPIKE`.
- **Threshold key:** `order_rejection_spike_per_min`.
- **Default value:** 10 rejects/minute, 5min rolling window. Sub-noise vs typical CeFi reject rate (< 1/min normal). See
  [`threshold-tuning.md`](./threshold-tuning.md).
- **Emitter(s):** `execution-service` (rejection-tracker per venue, 1m polling).
- **Upstream signal:** `count(rejected_orders) over 5min / 5 > threshold` for a single (venue, archetype).
- **De-dup window:** 300s.

## Severity + paging

- **Severity:** `WARN`.
- **Paging channels:** `TELEGRAM`.
- **Triggers kill-switch:** **FALSE**.
- **PagerDuty service:** N/A.

## Diagnosis (first 5 minutes)

1. **Acknowledge** in Telegram.
2. **Pull alert payload** via PubSub. Note: `payload.venue`, `payload.archetype`, `payload.reject_count_5m`,
   `payload.top_reject_reasons`.
3. **Pull rejection messages from execution-service events:**
   `gcloud storage cat gs://${PROJECT_ID}-events/events/execution-service/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl | jq -c "select(.event==\"ORDER_REJECTED\")" | tail -20`.
4. **Triage by reject_reason:**
   - `RATE_LIMIT_EXCEEDED` → throttling; reduce request rate.
   - `RISK_ENGINE_THROTTLED` → venue-side risk throttling.
   - `POST_ONLY_REJECTED` → orders crossed the spread; possible signal-staleness.
   - `INSUFFICIENT_BALANCE` → margin issue; cross-check `BALANCE_DRIFT`.
   - `INSTRUMENT_HALTED` / `MAX_POSITION` → venue-side state.
5. **Check correlated codes** — `CIRCUIT_BREAKER_OPEN` will fire if rate stays high.

## Resolution paths

### Path 1 — Reduce request rate (rate-limit-driven)

If `RATE_LIMIT_EXCEEDED`:

1. Tune execution-service request rate via DART → Execution Config. Reduce 25%; observe 15 min.
2. If venue offers higher-tier API plan, evaluate upgrade.

**Success:** reject rate drops below threshold sustained 15 min.

### Path 2 — Wait for venue health recovery

If `RISK_ENGINE_THROTTLED` / `INSTRUMENT_HALTED`, wait:
`watch -n 60 "curl -sH 'Authorization: Bearer ...' https://${EXECUTION_SERVICE_URL}/health | jq '.venues.<venue>.reject_rate_1m'"`.

**Success:** reject rate < threshold sustained 15 min.

### Path 3 — Pause archetype on this venue

If rejections continue > 1h AND can't tune:

1. DART → Strategy Config → "Pause Venue for Archetype". Other venues continue.
2. Investigate venue-specific issue with venue support.

**Success:** Telegram noise stops; archetype runs on remaining healthy venues.

## Rollback

- **Undoing rate reduction:** revert in DART → Execution Config.
- **Undoing pause-by-venue:** un-pause via DART once venue health recovers.

## Common false-positives

- **Funding-time burst:** some venues throttle/reject during funding settlement.
- **Aggressive signal cadence:** strategy signal rate exceeds venue's reasonable inflow.

If FP > 30% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 strategy lead when:

- Multi-venue simultaneous spike (correlated upstream issue).
- Reject rate > 100/min (likely systemic).
- Path 1 + 2 + 3 all blocked.

## Success criteria

- Reject rate < threshold sustained 15 min.
- Telegram alert no longer re-firing.

## Post-incident

Required if Path 3 was used.

## Cross-references

- **Cascade target:** [`circuit_breaker_open.md`](./circuit_breaker_open.md).
- **Co-firing:** [`balance_drift.md`](./balance_drift.md), [`preflight_failed.md`](./preflight_failed.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
