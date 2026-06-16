---
scope: [engineer, admin]
title: KILL_SWITCH_VENUE_DISCONNECT Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when one of the 6 perp hedge venues (Bybit, Deribit, Binance, OKX, Hyperliquid, Aster) loses
  connectivity for sustained period. Halts the affected archetype's signal generation; positions become unhedged risk.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/circuit_breaker_open.md
  - codex/15-runbooks/alerting/kill_switch_portfolio_drawdown.md
---

# `KILL_SWITCH_VENUE_DISCONNECT` Runbook

> **What this is:** an extended venue outage on a hedge leg. Without the perp hedge, the spot/DeFi leg of the carry
> trade is naked-long. Halt strategy-service for the affected archetype; operator decides flat-the-leg vs hedge-on-
> backup-venue.

## TL;DR

A perp venue critical to one of the carry archetypes lost connectivity for > 5 min sustained (heartbeat misses + REST

- WS both failing). The carry trade's hedge leg is now stale or unfilled, leaving the spot/DeFi leg as unhedged
  exposure. Kill-switch halts strategy-service for the affected archetype only — other archetypes continue. Operator
  diagnoses outage source + decides hedge-roll-to-backup vs flat-the-leg.

## Trigger condition

- **Code:** `KILL_SWITCH_VENUE_DISCONNECT` (UAC `AlertCode`).
- **Pattern (fnmatch):** `KILL_SWITCH_*`.
- **Threshold key:** `venue_disconnect_seconds` (TBD — Phase 7 to lift to UAC; current default is 300s in
  `execution-service` heartbeat watchdog).
- **Default value:** 300s sustained heartbeat-miss + REST-failure + WS-disconnect simultaneously.
- **Emitter(s):** `execution-service` (per-venue heartbeat watchdog) — emits when 3 health checks fail in succession.
- **Upstream signal:** circuit-breaker on the venue adapter has been OPEN for > 300s.
- **De-dup window:** 600s — single venue outage doesn't re-fire even if heartbeat flaps.

## Severity + paging

- **Severity:** `CRITICAL`.
- **Paging channels:** `PAGERDUTY`, `TELEGRAM`.
- **Triggers kill-switch:** **TRUE** — `KillSwitchEvent(scope=VENUE_DISCONNECT, venue=<name>, archetype=<name>)`.
  Subscribers: strategy-service halts the affected archetype only; execution-service blocks new orders on that venue;
  DART shows venue disconnect banner.
- **PagerDuty service:** `uts-prod-live-trading` P1.

## Diagnosis (first 5 minutes)

1. **Acknowledge** within 5 min.
2. **Pull alert payload:**
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
   Note: `payload.venue` (e.g. `bybit`), `payload.last_successful_heartbeat`, `payload.affected_archetype`,
   `payload.unhedged_exposure_usd`.
3. **Confirm venue is actually down** by hitting their status page + a direct ping. e.g.:
   ```bash
   # Check upstream status
   curl -s https://status.bybit.com/api/v2/status.json | jq '.status'
   # Direct ping (REST):
   curl -s -w "\n%{http_code}\n" https://api.bybit.com/v5/market/time
   ```
   If status page is green AND direct ping returns 200, the issue is local (firewall / DNS / IAM). Skip to Path 2.
4. **Cross-check unhedged exposure** — pull the affected archetype's position state from PBM:
   ```bash
   curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" \
     "https://${PBM_URL}/positions?archetype=<name>&include_legs=true" | jq
   ```
   Identify which legs are filled (spot/DeFi) vs unfilled or unconfirmed (perp hedge on the disconnected venue).
5. **Check correlated codes** — `CIRCUIT_BREAKER_OPEN` co-fires for the affected venue; `MARGIN_THRESHOLD_BREACH` may
   follow if the unhedged position moves against us.

## Resolution paths

### Path 1 — Venue recovers

If the venue's status page returns to green AND direct ping returns 200:

1. Wait for execution-service circuit-breaker to transition CLOSED (typical: 60s after first successful health check).
2. Verify by tailing events:
   ```bash
   gcloud storage cat gs://${PROJECT_ID}-events/events/execution-service/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl \
     | jq -c 'select(.event=="CIRCUIT_CLOSED" and .metadata.details.venue=="<venue>")' | tail -3
   ```
3. Operator publishes `KillSwitchEvent(scope=VENUE_DISCONNECT, venue=<name>, action=RESUME)` via DART.
4. strategy-service ack's resume; archetype emits signals again. Watch first hedge order land successfully:
   ```bash
   gcloud storage cat gs://${PROJECT_ID}-events/events/execution-service/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl \
     | jq -c "select(.event==\"ORDER_FILLED\" and .metadata.details.venue==\"<venue>\")" | tail -3
   ```

**Success:** venue circuit-breaker CLOSED + first hedge order filled within 5 min.

### Path 2 — Local connectivity issue (venue is up)

Likely causes: VPC firewall change, DNS poisoning, IAM credential rotation, IP allowlist drift. Walk through each:

1. **Check VM-side DNS:**
   ```bash
   gcloud compute ssh execution-service-vm --zone=asia-northeast1-c --command="nslookup api.bybit.com"
   ```
2. **Check IAM / API-key validity:**
   ```bash
   # Hit a private endpoint that requires auth
   curl -sH "X-BYBIT-API-KEY: $(gcloud secrets versions access latest --secret=bybit-api-key)" \
     -w "\n%{http_code}\n" https://api.bybit.com/v5/account/wallet-balance?accountType=UNIFIED
   ```
   401/403 = key rotated upstream; 200 = key valid.
3. **Check IP allowlist:** If venue requires IP-allowlist, confirm execution-service VM's egress IP is on the allowlist
   (check the venue console's API-key-management page).
4. Apply fix (rotate secret / update allowlist / update DNS); confirm via direct ping; then follow Path 1 resume.

**Success:** local fix applied + direct ping returns 200 + execution-service circuit-breaker CLOSED.

### Path 3 — Hedge roll to backup venue (venue down for hours)

If Path 1 + 2 are blocked AND outage is expected to last hours:

1. Operator + tier-3 strategy lead joint decision: roll the hedge leg to a backup venue.
2. Backup venues (per archetype): `carry_staked_basis` → Deribit / Binance; `leveraged_funding_arb` → OKX / Hyperliquid.
   Confirm backup venue is healthy.
3. Open DART → Manual Trade Gate → "Hedge Roll" wizard. Pick affected archetype + outage venue + backup venue.
4. Execute spot-equivalent unwind on outage venue (queued; will fire when venue recovers) + fresh hedge entry on backup
   venue.
5. Verify hedge ratio in PBM is back at target.

**Success:** hedge ratio in PBM at target ± 5%; strategy-service can resume on archetype with updated venue mapping.

## Rollback

- **Undoing hedge roll:** no clean rollback. Closing the backup-venue hedge + re-opening on the outage venue is two
  fresh trades — re-execute via DART once outage venue recovers if operator wants to revert (typically not done; venue
  diversification is good).

## Common false-positives

- **Brief venue maintenance window:** Some venues have scheduled maintenance < 5 min. If the outage is < 300s, the alert
  shouldn't fire — but if threshold tuning is too aggressive, false fires happen. Action: raise via
  [`threshold-tuning.md`](./threshold-tuning.md).
- **VPC route flap:** Cloud-side network blips < 60s. Symptom: alert fires, then circuit-breaker auto-closes within 60s.
  Action: ack + log; investigate the underlying VPC issue with cloud-infra.

## Escalation criteria + targets

Escalate to tier-3 + tier-4 when:

- Outage > 30 min sustained AND `unhedged_exposure_usd` > 25k.
- Multiple venues disconnect simultaneously (correlated outage = potentially upstream provider issue, e.g. Cloudflare).
- Path 3 hedge roll fails (backup venue also unhealthy).

## Success criteria

- Venue circuit-breaker CLOSED OR hedge rolled to backup.
- Affected archetype resumed and emitting signals.
- DART Active Alerts shows alert `resolved`.
- Post-incident write-up filed.

## Post-incident

Mandatory. Action items typically include: backup-venue test cadence, IP-allowlist review, DNS resilience config,
heartbeat-watchdog threshold review.

## Cross-references

- **Sibling kill-switches:** [`kill_switch_defi_liquidation_risk.md`](./kill_switch_defi_liquidation_risk.md),
  [`kill_switch_portfolio_drawdown.md`](./kill_switch_portfolio_drawdown.md).
- **Co-firing alerts:** [`circuit_breaker_open.md`](./circuit_breaker_open.md),
  [`margin_threshold_breach.md`](./margin_threshold_breach.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
