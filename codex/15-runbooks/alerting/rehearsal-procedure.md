---
title: Alerting Rehearsal Procedure
status: ready
created: 2026-05-07
updated: 2026-05-23
authoritative_for:
  Phase 8 pre-May-23 dry-run rehearsal procedure. Operator runs inject_synthetic_alert.py
  for each of the 15 monitored AlertCodes and verifies end-to-end routing, DART display,
  ack/escalate/resolve flows, and runbook deep-links. The KILL_SWITCH path is exercised
  end-to-end including circuit-breaker propagation.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/alert-code-taxonomy.md
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/threshold-tuning.md
---

# Alerting Rehearsal Procedure

> **Phase 8 — May-23 pre-cutover dry-run.** The 15 core alert codes must pass end-to-end
> verification before the live-DeFi cutover on 2026-05-23 09:00 UTC. This doc is the
> operator-facing rehearsal guide. Record outcomes in
> `codex/15-runbooks/alerting/REHEARSAL_2026_05_<date>.md` (one per rehearsal date).

## Prerequisites

Before starting the rehearsal, verify all prerequisites are green:

- [ ] `alerting-service` deployed and running (Cloud Run or VM in staging)
- [ ] `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` set (GCP/AWS Secret Manager or `.act-secrets`)
- [ ] DART UI accessible at `http://localhost:5183` (or staging URL)
- [ ] `inject_synthetic_alert.py` script present at `alerting-service/scripts/inject_synthetic_alert.py`
- [ ] Phase 7 quietness baseline complete (48h staging run with <5% FP rate)
- [ ] PagerDuty test service configured (or PD suppressed for Telegram-only rehearsal)
- [ ] `execution-service` and `strategy-service` running (needed for KILL_SWITCH end-to-end)

## Tools

| Tool | Purpose |
| ---- | ------- |
| `python alerting-service/scripts/inject_synthetic_alert.py --code <CODE>` | Emit one synthetic alert |
| `python alerting-service/scripts/inject_synthetic_alert.py --all` | Emit all 76 registered codes |
| `python alerting-service/scripts/inject_synthetic_alert.py --verify-kill-switch` | KILL_SWITCH end-to-end |
| DART Active Alerts panel | `http://localhost:5183` bell icon |
| Telegram staging channel | UTS Staging Noise (`-5209487754`) |

## Rehearsal checklist — 15 core alert codes

For each code: inject → observe → verify all 6 criteria. Mark pass/fail.

### Verification criteria (a)-(f)

- **(a) Channel routing** — alert appears in the correct channel per `LIVE_ALERT_RULES[code].channels`
- **(b) DART panel** — bell badge increments; alert in dropdown with correct code/severity/payload
- **(c) Ack flow** — Ack in DART; alert moves to `acknowledged`; badge decrements
- **(d) Escalate flow** — Escalate in DART; synthetic PD page fires (or escalation event logged)
- **(e) Runbook deep-link** — alert in DART opens correct codex runbook URL
- **(f) Auto-resolve** — synthetic resolve event; alert removed from active list

### Code-by-code checklist

| # | AlertCode | Severity | Channels | (a) | (b) | (c) | (d) | (e) | (f) | Notes |
|---|-----------|----------|----------|-----|-----|-----|-----|-----|-----|-------|
| 1 | KILL_SWITCH_DEFI_LIQUIDATION_RISK | CRITICAL | PD+TG | | | | | | | See kill-switch section |
| 2 | KILL_SWITCH_PORTFOLIO_DRAWDOWN | CRITICAL | PD+TG | | | | | | | See kill-switch section |
| 3 | KILL_SWITCH_VENUE_DISCONNECT | CRITICAL | PD+TG | | | | | | | See kill-switch section |
| 4 | CIRCUIT_BREAKER_OPEN | CRITICAL | PD+TG | | | | | | | |
| 5 | DEFI_HEALTH_FACTOR_CRITICAL | CRITICAL | PD+TG | | | | | | | |
| 6 | DEFI_WEETH_DEPEG | CRITICAL | PD+TG | | | | | | | |
| 7 | DEFI_AAVE_UTILIZATION_SPIKE | HIGH | PD+TG | | | | | | | |
| 8 | DEFI_FUNDING_RATE_FLIP | HIGH | Telegram | | | | | | | |
| 9 | DEFI_FEATURE_STALE | WARN | Telegram | | | | | | | |
| 10 | PREFLIGHT_FAILED | HIGH | PD+TG | | | | | | | |
| 11 | SERVICE_DEGRADED | HIGH | Email | | | | | | | |
| 12 | BALANCE_DRIFT | WARN | Telegram | | | | | | | |
| 13 | ORDER_REJECTION_SPIKE | HIGH | PD+TG | | | | | | | |
| 14 | MARGIN_THRESHOLD_BREACH | HIGH | PD+TG | | | | | | | |
| 15 | POSITION_DRIFT | WARN | Telegram | | | | | | | |

### Injection commands

```bash
cd alerting-service

# Single code:
python scripts/inject_synthetic_alert.py --code DEFI_WEETH_DEPEG

# All codes (smoke — ALERT_SUPPRESSED_SYNTHETIC for each):
python scripts/inject_synthetic_alert.py --all

# Kill-switch end-to-end:
python scripts/inject_synthetic_alert.py --verify-kill-switch
```

## Kill-switch end-to-end verification

Required per plan Phase 8: KILL_SWITCH_DEFI_LIQUIDATION_RISK end-to-end with circuit-breaker
propagation to execution-service and strategy-service.

### Steps

1. Start `execution-service` + `strategy-service` in staging mode (subscribed to kill-switch-bus).

2. Run:
   ```bash
   python alerting-service/scripts/inject_synthetic_alert.py --verify-kill-switch
   ```
   Expected:
   ```
   [KILL_SWITCH_DEFI_LIQUIDATION_RISK] KillSwitchEvent emitted — scope=GLOBAL ... PASS
   [KILL_SWITCH_PORTFOLIO_DRAWDOWN]    KillSwitchEvent emitted — scope=GLOBAL ... PASS
   [KILL_SWITCH_VENUE_DISCONNECT]      KillSwitchEvent emitted — scope=VENUE  ... PASS
   ```

3. Check execution-service halt:
   ```bash
   gcloud logging read "resource.type=cloud_run_revision AND textPayload:KILL_SWITCH_EVENT_RECEIVED" \
     --project central-element-323112 --limit 5 --format="value(textPayload)"
   ```

4. Verify DART shows strategy in `HALTED` state.

5. Send deactivate event; verify services resume within 15s.

### Pass criteria

- All 3 KILL_SWITCH codes emit `KillSwitchEvent` within 5s.
- execution-service stops new orders within 10s.
- DART shows strategy `HALTED`.
- Deactivation resumes within 15s.

## Sign-off document

After completing the rehearsal, create:
`codex/15-runbooks/alerting/REHEARSAL_2026_05_<DD>.md`

Template:

```markdown
# Alerting Rehearsal Sign-off — 2026-05-<DD>

Operator: <name>
Date: 2026-05-<DD> <HH:MM> UTC
Environment: staging

## Per-code results
| # | AlertCode | (a) | (b) | (c) | (d) | (e) | (f) | Notes |
<fill from checklist above>

## Kill-switch end-to-end
Result: PASS / FAIL
Evidence: <log snippet or script output>

## Issues found
<list failures, routing mismatches, threshold observations>

## Decision
[ ] GO — all 15 codes PASS + kill-switch PASS
[ ] NO-GO — <reason + remediation plan>

Signed: <operator name> <date>
```

## Quarterly cadence (post-May-23)

- First Monday of each quarter
- Rotate codes across quarters (all 15 covered in 4 quarters)
- Unpublished schedule within each quarter (prevents memorisation)
- Write-up owner: designated rehearsal coordinator (not necessarily the on-call)
