---
scope: [engineer, admin]
title: KILL_SWITCH_PORTFOLIO_DRAWDOWN Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when total-portfolio drawdown crosses the kill-switch threshold. Halts all strategies + execution-
  service order entry; positions roll to flat-only mode pending operator review.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/kill_switch_defi_liquidation_risk.md
  - codex/15-runbooks/alerting/balance_drift.md
execution:
  owner: on-call operator (Ikenna / Harsh by rotation)
  cadence: on-demand (incident response) + quarterly DR drill
  verifier:
    all strategies halted (strategy-service event log); positions in flat-only mode; operator sign-off before re-arm
  last_executed: never
---

# `KILL_SWITCH_PORTFOLIO_DRAWDOWN` Runbook

> **What this is:** the global P&L-stop. Total portfolio NAV dropped below the day-start NAV by the configured drawdown
> threshold. Halts everything; operator + tier-3 strategy lead jointly decide resume.

## TL;DR

Total portfolio drawdown breached the day-start cap. Strategy-service stops emitting signals; execution-service rejects
new orders (flat-only mode); position-balance-monitor takes a forensic snapshot. Operator + strategy lead must jointly
confirm resume. This is NOT a runaway-loss alarm — it's a "we hit the daily risk budget" alarm.

## Trigger condition

- **Code:** `KILL_SWITCH_PORTFOLIO_DRAWDOWN` (UAC `AlertCode`).
- **Pattern (fnmatch):** `KILL_SWITCH_*`.
- **Threshold key:** `portfolio_drawdown_pct` (TBD — Phase 1 seeded as inline constant in risk-and-exposure-service;
  raise to UAC `ALERT_THRESHOLDS` as part of Phase 7 quietness baseline).
- **Default value:** 3% intra-day drawdown from day-start NAV (operator-configurable per archetype; default
  workspace-wide is conservative until Phase 7 tuning).
- **Emitter(s):** `risk-and-exposure-service` (drawdown calculator running 1Hz against position-balance-monitor NAV
  feed).
- **Upstream signal:** `current_nav / day_start_nav - 1 < -drawdown_threshold` sustained ≥10s.
- **De-dup window:** 300s — single drawdown event collapses repeated tick crossings.

## Severity + paging

- **Severity:** `CRITICAL`.
- **Paging channels:** `PAGERDUTY`, `TELEGRAM`.
- **Triggers kill-switch:** **TRUE** — `KillSwitchEvent(scope=PORTFOLIO_DRAWDOWN)`. Subscribers: strategy-service (halt
  all archetypes), execution-service (flat-only — only close-existing orders allowed), position-balance-monitor
  (forensic snapshot trigger), DART (drawdown banner with current pct).
- **PagerDuty service:** `uts-prod-live-trading` P1.

## Diagnosis (first 5 minutes)

1. **Acknowledge** within 5 min.
2. **Pull alert payload:**
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
   Note: `payload.day_start_nav_usd`, `payload.current_nav_usd`, `payload.drawdown_pct`,
   `payload.contributing_archetypes`.
3. **Confirm NAV** by reading the position-balance-monitor canonical state directly:
   ```bash
   curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://${PBM_URL}/positions/nav | jq
   ```
   Cross-check against the alert payload — significant divergence (>0.5%) indicates a stale snapshot.
4. **Decompose by archetype** — which strategies contributed:
   ```bash
   curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" \
     "https://${PBM_URL}/pnl/decomposition?since_day_start=true" | jq '.archetypes[] | {name, pnl_usd, pct_contribution}'
   ```
5. **Check correlated codes** — common co-fires: `MARGIN_THRESHOLD_BREACH` (CeFi side blowing up),
   `DEFI_POSITION_LIQUIDATED` (DeFi forced sell), `DEFI_WEETH_DEPEG` (LST collateral break).

## Resolution paths

### Path 1 — Drawdown is mark-to-market noise (NAV recovers)

If post-alert NAV recovers within 5 min and the drawdown pct dips below the kill-switch threshold, this was a
mark-to-market spike (e.g. wide bid-ask snapshot). Action:

- Wait for `position-balance-monitor` to publish 3 consecutive 10s NAV reads above threshold.
- Operator reviews `pnl_decomposition` for any actually-realized losses.
- If realized losses are minimal (< 0.5% of NAV), follow resume procedure (below).

**Success:** drawdown pct ≥ -threshold for 60s + operator + tier-3 sign-off + halt cleared.

### Path 2 — Real drawdown, plan exit

If realized + unrealized losses confirm real drawdown:

1. Operator + tier-3 strategy lead joint review of `pnl_decomposition` to identify the bleeding archetype.
2. Decision: full flat (close all positions) OR partial flat (close just the bleeding leg).
3. Operator queues exit orders via DART manual-trade-gate (kill-switch-halt blocks normal strategy-driven orders, so
   exits MUST go through manual gate).
4. Verify positions reduce in PBM:
   ```bash
   watch -n 10 'curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://${PBM_URL}/positions | jq ".positions | length"'
   ```

**Success:** PBM positions count → 0 (full flat) or target subset (partial flat) + drawdown stops accelerating.

### Path 3 — Cascading failure (Path 1 + 2 both blocked)

If exits are blocked (e.g. venue disconnect, tx-revert spike) AND drawdown is accelerating:

- Tier-3 strategy lead + tier-4 custody contact MUST be on the call.
- Consider venue-by-venue manual cancel (DART → Order Management → Cancel All by Venue).
- For DeFi, consider the flash-loan-receiver auto-deleverage path (see
  [`kill_switch_defi_liquidation_risk.md`](./kill_switch_defi_liquidation_risk.md) Path 2).

**Success:** drawdown stabilizes (rate-of-change → 0) + strategy lead approves resume planning.

## Resume-from-halt procedure

1. Operator + tier-3 strategy lead joint review of post-incident position state.
2. Confirm drawdown rate-of-change ≤ 10bps/min for 15 min.
3. Re-set day-start NAV to current NAV (via DART → Risk Config → "Reset Day Window") so the halt doesn't immediately
   re-fire.
4. Publish `KillSwitchEvent(scope=PORTFOLIO_DRAWDOWN, action=RESUME)` via DART.
5. strategy-service + execution-service ack resume.
6. Watch for 30 min — if no re-fire, ack alert.

## Rollback

- **Undoing exits:** no rollback; exits are realized P&L. Only re-establishing positions via normal strategy flow once
  resumed is "rollback-equivalent" but at fresh-trade prices.
- **Undoing day-start NAV reset:** no rollback. Document the reset in operator-action log.

## Common false-positives

- **Funding-time NAV shock:** Some perp venues mark P&L at funding instants causing a 1-tick spike. Symptom: drawdown
  pct in alert payload normalizes within 60s. Action: ack + log.
- **Oracle TWAP staleness:** Stale Chainlink TWAP can mark a DeFi position at the wrong price for ~30s. Symptom: NAV
  reads diverge between PBM and live RPC. Action: ack if NAV recovers within 5 min.

If FP > 5% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 + tier-4 immediately when ANY of:

- Drawdown pct breaches 2× the threshold (e.g. > 6% if threshold is 3%).
- Path 1 + 2 both blocked.
- Realized loss > USD 50k.

## Success criteria

- Drawdown pct stable ≤ -threshold for 60s.
- Tier-3 strategy lead has approved resume.
- DART Active Alerts shows alert `resolved`.
- Post-incident write-up filed.

## Post-incident

Mandatory. Action items typically include: position-size limit review, archetype P&L attribution audit, threshold-tuning
review.

## Cross-references

- **Sibling kill-switches:** [`kill_switch_defi_liquidation_risk.md`](./kill_switch_defi_liquidation_risk.md),
  [`kill_switch_venue_disconnect.md`](./kill_switch_venue_disconnect.md).
- **Co-firing alerts:** [`margin_threshold_breach.md`](./margin_threshold_breach.md),
  [`balance_drift.md`](./balance_drift.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
