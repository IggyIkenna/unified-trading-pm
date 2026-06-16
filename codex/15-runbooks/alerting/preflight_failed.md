---
scope: [engineer, admin]
title: PREFLIGHT_FAILED Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when execution-service preflight check rejects an order before submission. Indicates a risk /
  position / margin / instrument-state guard caught a malformed or unsafe order.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/order_rejection_spike.md
---

# `PREFLIGHT_FAILED` Runbook

> **What this is:** an order failed execution-service preflight before submission to the venue. Order NOT sent.
> WARN-severity (Telegram only). Operator investigates whether upstream signal generator is broken.

## TL;DR

execution-service rejected an order during preflight (margin / risk / position / instrument-state checks). The order
never reached the venue, so no monetary loss. Operator inspects rejection reason + verifies whether real bug or expected
guard.

## Trigger condition

- **Code:** `PREFLIGHT_FAILED` (UAC `AlertCode`).
- **Pattern (fnmatch):** `PREFLIGHT_FAILED`.
- **Threshold key:** none (binary event).
- **Default value:** N/A.
- **Emitter(s):** `execution-service` (preflight checker).
- **Upstream signal:** preflight check returns `reject` reason.
- **De-dup window:** 60s on `(rejection_reason, archetype, symbol)`.

## Severity + paging

- **Severity:** `WARN`.
- **Paging channels:** `TELEGRAM`.
- **Triggers kill-switch:** **FALSE**.
- **PagerDuty service:** N/A.

## Diagnosis (first 5 minutes)

1. **Acknowledge** in Telegram.
2. **Pull alert payload** via PubSub:
   `gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts --auto-ack --limit=1 --format=json`.
3. **Triage by rejection_reason:**
   - `MARGIN_INSUFFICIENT` → not enough margin; confirm wallet balance + retry smaller.
   - `INSTRUMENT_HALTED` → venue paused trading; expected during halts.
   - `POSITION_LIMIT_EXCEEDED` → strategy emitted signal beyond per-archetype limit; check config drift.
   - `KILL_SWITCH_ACTIVE` → expected — kill-switch gating new orders.
   - `PRICE_OFF_BAND` → requested price too far from market mid; possible stale signal.
   - `STALE_SIGNAL` → signal age exceeds max allowed.
4. **Inspect upstream signal in PubSub.**
5. **Check correlated codes** — `MARGIN_THRESHOLD_BREACH` may co-fire on margin-driven rejections.

## Resolution paths

### Path 1 — Expected guard (kill-switch active / instrument halted)

If rejection_reason consistent with current system state, no operator action — system is doing its job.

**Success:** Telegram noise stops once root cause clears.

### Path 2 — Strategy / signal generator bug

If rejection is `POSITION_LIMIT_EXCEEDED` / `STALE_SIGNAL` / `PRICE_OFF_BAND` and recurring:

1. Inspect strategy-service events:
   `gcloud storage cat gs://${PROJECT_ID}-events/events/strategy-service/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl | jq -c "select(.event==\"SIGNAL_EMITTED\")" | tail -10`.
2. Compare signal payload with archetype config in DART.
3. Fix config drift OR file an issue.

**Success:** PREFLIGHT_FAILED rate falls below noise floor.

### Path 3 — Wallet / margin issue

If rejection is `MARGIN_INSUFFICIENT`:

1. Check venue wallet via PBM:
   `curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" "https://${PBM_URL}/wallets/<venue>" | jq`.
2. If real balance < expected: reconcile via DART → Wallet Reconcile.
3. Top up margin OR reduce target leverage.

**Success:** wallet/leverage adjusted; next signal passes preflight.

## Rollback

- **Undoing config change:** revert in DART → Strategy Config.

## Common false-positives

- **Race condition mid-fill:** position fills + reduces available margin between strategy emit + preflight check.
- **Funding-boundary halt:** brief venue halt during funding settlement.

If FP > 30% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 when:

- > 50 PREFLIGHT_FAILED in 1h on same archetype (signal generator likely broken).
- Rejection_reason is novel / unrecognized.

## Success criteria

- Rejection root cause identified.
- Telegram alert no longer re-firing OR re-firing only on expected guards.

## Post-incident

NOT required for transient rejections. Required if Path 2 led to config / code change.

## Cross-references

- **Co-firing:** [`order_rejection_spike.md`](./order_rejection_spike.md), [`balance_drift.md`](./balance_drift.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
