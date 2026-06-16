---
scope: [engineer, admin]
title: MARGIN_THRESHOLD_BREACH Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when CeFi margin buffer crosses the pre-emptive threshold (default 200bps from initial-margin-call
  line). Pre-emptive notify; positions are not yet at risk but margin-call is approaching.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/balance_drift.md
  - codex/15-runbooks/alerting/kill_switch_portfolio_drawdown.md
---

# `MARGIN_THRESHOLD_BREACH` Runbook

> **What this is:** a CeFi venue's margin ratio entered the pre-emptive warning band (within 200bps of initial-margin-
> call line). HIGH-severity (PagerDuty + Telegram) but not a kill-switch event.

## TL;DR

Per-venue margin ratio dropped within the operator's pre-emptive buffer (default 2% from venue's initial-margin-call
line). Operator should consider topping up margin or partially unwinding before the venue's risk engine triggers a
margin-call. DeFi sibling: `DEFI_HEALTH_FACTOR_CRITICAL`.

## Trigger condition

- **Code:** `MARGIN_THRESHOLD_BREACH` (UAC `AlertCode`).
- **Pattern (fnmatch):** `MARGIN_THRESHOLD_BREACH`.
- **Threshold key:** `margin_threshold_breach_bps`.
- **Default value:** 200 bps (2% buffer from initial-margin-call line). Per-venue overrides via
  `per_archetype_overrides`. See [`threshold-tuning.md`](./threshold-tuning.md).
- **Emitter(s):** `position-balance-monitor-service` (margin-watch loop, 1m polling per venue).
- **Upstream signal:** `(margin_ratio - margin_call_threshold) × 10000 < threshold_bps` sustained ≥ 60s.
- **De-dup window:** 300s.

## Severity + paging

- **Severity:** `HIGH`.
- **Paging channels:** `PAGERDUTY`, `TELEGRAM`.
- **Triggers kill-switch:** **FALSE** (sister `MARGIN_LIQUIDATION` / `MARGIN_CRITICAL` are CRITICAL kill-switch).
- **PagerDuty service:** `uts-prod-live-trading` P2.

## Diagnosis (first 5 minutes)

1. **Acknowledge** within 5 min.
2. **Pull alert payload** via PubSub. Note: `payload.venue`, `payload.wallet_id`, `payload.margin_ratio`,
   `payload.margin_call_threshold`, `payload.buffer_bps`, `payload.archetype`.
3. **Cross-check margin via direct venue read:**
   `curl -sH "X-BYBIT-API-KEY: ..." https://api.bybit.com/v5/account/wallet-balance?accountType=UNIFIED | jq`. Returns
   marginRatio, totalEquity, totalInitialMargin, totalMaintenanceMargin.
4. **Identify drift driver** — mark-price-driven OR debt-driven? Recent position-mark events:
   `gcloud storage cat gs://${PROJECT_ID}-events/events/position-balance-monitor/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl | jq -c "select(.event==\"POSITION_MARKED\")" | tail -10`.
5. **Check correlated codes** — `BALANCE_DRIFT` may indicate underlying missed event; `KILL_SWITCH_PORTFOLIO_DRAWDOWN`
   if portfolio-wide.

## Resolution paths

### Path 1 — Wait + monitor (margin recovers)

If breach is from a single mark-price tick AND mark price is mean-reverting:
`watch -n 30 "curl -sH '...' https://api.bybit.com/v5/account/wallet-balance?accountType=UNIFIED | jq '.result.list[0].marginRatio'"`.

**Success:** buffer ≥ threshold + 100bps sustained 5 min.

### Path 2 — Top up margin (deposit)

If we have idle margin to deploy:

1. Operator → DART → Manual Wallet → "Transfer to Venue" wizard. Source: idle reserve. Target: affected venue.
2. Wait for venue confirmation (1-3 confirmations DeFi-bridged; instant for fiat / SPL within CEX).
3. Verify margin ratio.

**Success:** buffer ≥ threshold + 100bps after deposit confirmed.

### Path 3 — Partial unwind (no idle margin OR drift accelerating)

If margin not improving AND no idle margin:

1. Operator + tier-3 strategy lead joint review.
2. DART → Manual Trade Gate → "Reduce Position" wizard for largest at-risk position.
3. Execute partial close.

**Success:** buffer ≥ threshold + 100bps post-trade.

## Rollback

- **Undoing deposit:** initiate withdrawal once margin healthy.
- **Undoing partial unwind:** re-enter via normal strategy flow once stabilized.

## Common false-positives

- **Mark-price tick spike:** brief mark-price gap can momentarily breach.
- **Funding-time accounting:** some venues mark margin at funding boundaries differently.

If FP > 15% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 + tier-4 (custody) when:

- Buffer < 50bps (margin-call about to fire).
- Multi-venue simultaneous breach.
- Path 1 + 2 + 3 all blocked.

## Success criteria

- Buffer ≥ threshold + 100bps sustained 5 min.
- DART Active Alerts shows alert `resolved`.
- Post-incident write-up filed if real-money action taken.

## Post-incident

Required if Path 2 or 3 used.

## Cross-references

- **Cascade target:** `MARGIN_LIQUIDATION` (CRITICAL); `KILL_SWITCH_PORTFOLIO_DRAWDOWN` if portfolio-wide.
- **DeFi sibling:** [`defi_health_factor_critical.md`](./defi_health_factor_critical.md).
- **Co-firing:** [`balance_drift.md`](./balance_drift.md),
  [`kill_switch_portfolio_drawdown.md`](./kill_switch_portfolio_drawdown.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
