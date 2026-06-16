---
scope: [engineer, admin]
title: POSITION_DRIFT Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when position drifts from target weight by more than the threshold. Rebalance trigger; common
  industry standard ~1% from target.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/balance_drift.md
execution:
  owner:
    alerting-service maintainer (alert emission) + position-balance-monitor-service maintainer (drift detection) +
    on-call rotation (operator response)
  cadence: continuous (PBMS reconciliation loop emits `POSITION_DRIFT` per `position_drift_bps` threshold)
  verifier:
    alert routes to Telegram + CRITICAL severity → PagerDuty + auto STOP_NEW_ONLY per `autonomous-recovery-matrix.md`
    G4; WARN noise-floor `position_drift_bps=100`
  last_executed: NEVER (live PBMS reconciliation activation pending master plan Group F)
---

# `POSITION_DRIFT` Runbook

> **What this is:** a position's actual weight in the portfolio drifted from the target by more than the per-archetype
> rebalance threshold. WARN-severity. Rebalance is auto-handled by strategy-service in normal operation; this alert
> fires only when auto-rebalance is gated or stuck.

## TL;DR

A position's actual size diverged from the strategy-service target by more than the rebalance threshold (default 100bps
= 1% of target). If auto-rebalance is healthy this resolves naturally. If the alert is sustained, auto- rebalance is
blocked (kill-switch active, venue disconnected, signal stale) and operator should investigate.

## Trigger condition

- **Code:** `POSITION_DRIFT` (UAC `AlertCode`).
- **Pattern (fnmatch):** `POSITION_DRIFT`.
- **Threshold key:** `position_drift_bps`.
- **Default value:** 100 bps (1% from target weight; common industry standard for rebalance trigger). See
  [`threshold-tuning.md`](./threshold-tuning.md).
- **Emitter(s):** `position-balance-monitor-service` (drift monitor, 1m polling per archetype).
- **Upstream signal:** `abs(actual_weight - target_weight) × 10000 > threshold_bps` sustained ≥ 5 min.
- **De-dup window:** 600s.

## Severity + paging

- **Severity:** `WARN`.
- **Paging channels:** `TELEGRAM`.
- **Triggers kill-switch:** **FALSE**.
- **PagerDuty service:** N/A.

## Diagnosis (first 5 minutes)

1. **Acknowledge** in Telegram.
2. **Pull alert payload** via PubSub. Note: `payload.archetype`, `payload.symbol`, `payload.target_weight_pct`,
   `payload.actual_weight_pct`, `payload.drift_bps`, `payload.duration_seconds`.
3. **Check whether auto-rebalance is firing:**
   ```bash
   gcloud storage cat gs://${PROJECT_ID}-events/events/strategy-service/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl \
     | jq -c "select(.event==\"REBALANCE_SIGNAL_EMITTED\" and .metadata.details.archetype==\"<name>\")" | tail -5
   ```
   If no recent signals: auto-rebalance gated (cause: kill-switch / venue disconnect / signal stale).
4. **Verify position state in PBM:**
   ```bash
   curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" \
     "https://${PBM_URL}/positions?archetype=<name>" | jq '.positions[] | {symbol, size, target_size, weight_pct}'
   ```
5. **Check correlated codes** — `KILL_SWITCH_*` if rebalance gated by kill-switch; `BALANCE_DRIFT` may co-fire if drift
   is downstream of a missed event.

## Resolution paths

### Path 1 — Wait for auto-rebalance

If diagnosis step 3 shows recent rebalance signals are firing AND drift is decreasing, no operator action — let it run:

```bash
watch -n 60 "curl -sH 'Authorization: Bearer \$(gcloud auth print-access-token)' \
  'https://\${PBM_URL}/positions?archetype=<name>' | jq '.positions[] | .weight_pct'"
```

**Success:** drift_bps < threshold sustained 5 min.

### Path 2 — Resolve auto-rebalance gating

If auto-rebalance is gated:

- **Kill-switch active:** check `KILL_SWITCH_*` runbooks; resume kill-switch first.
- **Venue disconnected:** check [`kill_switch_venue_disconnect.md`](./kill_switch_venue_disconnect.md); reroute to
  backup venue.
- **Signal stale:** check `STALE_SIGNAL` rejections in execution-service events; restart strategy-service if needed.

**Success:** auto-rebalance signals resume; drift reduces.

### Path 3 — Manual rebalance via DART

If auto-rebalance can't be resumed quickly AND drift is widening:

1. Operator → DART → Manual Trade Gate → "Manual Rebalance" wizard. Wizard computes the trade(s) to bring weight back to
   target.
2. Execute.

**Success:** drift_bps < threshold post-trade.

## Rollback

- **Undoing manual rebalance:** none — fresh trades. Re-enter via auto-rebalance once gating clears.

## Common false-positives

- **Mark-price gap:** mark-price moves can cause weight calculation to drift even without actual position change.
  Symptom: drift driven entirely by price, not by size. Action: ack + log; rebalance threshold may need to use
  size-based not weight-based metric.
- **Mid-rebalance snapshot:** alert fires while a rebalance is in flight. Symptom: drift resolves within 5 min
  naturally.

If FP > 25% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 strategy lead when:

- Drift > 5x threshold (e.g. > 5%).
- Drift sustained > 1h with auto-rebalance not firing.
- Multi-archetype simultaneous drift.

## Success criteria

- Drift_bps < threshold sustained 5 min.
- Telegram alert no longer re-firing.

## Post-incident

NOT required for transient drift. Required if Path 3 (manual rebalance) was used.

## Cross-references

- **Co-firing:** [`balance_drift.md`](./balance_drift.md),
  [`kill_switch_venue_disconnect.md`](./kill_switch_venue_disconnect.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
