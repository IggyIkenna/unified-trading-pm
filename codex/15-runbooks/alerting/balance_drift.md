---
scope: [engineer, admin]
title: BALANCE_DRIFT Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when wallet balance drifts from expected ledger state by more than the threshold. Indicates a missed
  event (fee, withdrawal, deposit) or PBM ledger bug.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/preflight_failed.md
  - codex/15-runbooks/alerting/margin_threshold_breach.md
execution:
  owner:
    alerting-service maintainer (alert emission) + position-balance-monitor-service maintainer (drift detection) +
    on-call rotation (operator response)
  cadence:
    continuous (custody-ping loop emits `BALANCE_DRIFT` per 5min; threshold review quarterly per `threshold-tuning.md`)
  verifier:
    alert routes to Telegram + HIGH severity → PagerDuty; resolved via PBMS reconciliation API; WARN noise-floor
    `balance_drift_usd=1000`
  last_executed: NEVER (live custody-ping activation pending master plan Group F-19 Copper+CEFFU)
---

# `BALANCE_DRIFT` Runbook

> **What this is:** position-balance-monitor's expected wallet balance differs from venue/wallet's reported by > USD
> threshold. Could be a missed fee event, an unledgered withdrawal, or PBM bug. WARN-severity.

## TL;DR

Wallet balance reconciliation found a notional discrepancy > USD 1000 (default) between PBM expected and venue reported.
Operator investigates the delta source + reconciles. Doesn't pause trading unless drift accelerates.

## Trigger condition

- **Code:** `BALANCE_DRIFT` (UAC `AlertCode`).
- **Pattern (fnmatch):** `BALANCE_DRIFT`.
- **Threshold key:** `balance_drift_usd`.
- **Default value:** 1000 USD (operator-confirmed acceptable noise floor — see
  [`threshold-tuning.md`](./threshold-tuning.md)).
- **Emitter(s):** `position-balance-monitor-service` (per-wallet reconciliation, every 5 min).
- **Upstream signal:** `abs(expected_balance_usd - venue_reported_balance_usd) > threshold` sustained ≥ 5 min.
- **De-dup window:** 600s.

## Severity + paging

- **Severity:** `WARN`.
- **Paging channels:** `TELEGRAM`.
- **Triggers kill-switch:** **FALSE**.
- **PagerDuty service:** N/A.

## Diagnosis (first 5 minutes)

1. **Acknowledge** in Telegram.
2. **Pull alert payload** via PubSub. Note: `payload.wallet_id`, `payload.venue` (or `chain`),
   `payload.expected_balance_usd`, `payload.reported_balance_usd`, `payload.drift_usd`, `payload.drift_direction`.
3. **Verify reported balance independently:**
   - **CeFi:**
     `curl -sH "X-API-KEY: $(gcloud secrets versions access latest --secret=<venue>-readonly-api-key)" https://api.<venue>.com/v5/account/wallet-balance | jq`
   - **DeFi:** `cast balance <wallet_address> --rpc-url ${ETH_RPC_URL}` and
     `cast call <token_address> "balanceOf(address)(uint256)" <wallet_address> --rpc-url ${ETH_RPC_URL}`
4. **Pull recent fills + transfers from PBM:**
   `curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" "https://${PBM_URL}/wallets/<wallet_id>/recent-events?limit=50" | jq`.
5. **Check correlated codes** — `MARGIN_THRESHOLD_BREACH` may co-fire if drift impacted margin.

## Resolution paths

### Path 1 — Identify the missed event

Common drift drivers:

- **Funding payment** (CeFi perp): venue debited / credited funding; PBM didn't capture. Reconcile via PBM
  `/reconcile/funding`.
- **Fees:** CeFi taker/maker + DeFi gas. Reconcile via PBM `/reconcile/fees`.
- **Liquidation / partial close:** venue's risk engine closed a position; check sister runbook.
- **Withdrawal / deposit:** operator manually moved funds; ledger needs the operation logged via DART.

**Success:** post-reconciliation, drift_usd < threshold.

### Path 2 — PBM ledger bug

If venue/chain side checks out AND PBM appears to have lost a tx:

1. File issue in `unified-trading-pm/plans/active/issues/pbm_ledger_drift_<date>.md` with wallet + tx hash.
2. PBM author investigates; rerun reconcile after fix.

**Success:** root cause identified + ledger patched.

### Path 3 — Manual ledger override (last resort)

Only when Paths 1 + 2 take > 1h AND drift is blocking trades:

1. Operator + tier-3 lead joint sign-off.
2. DART → Manual Ledger Override.
3. Audit log records override.

**Success:** drift cleared; full forensic later.

## Rollback

- **Undoing manual override:** revert in DART; previous version persists in audit log.

## Common false-positives

- **Mid-tx race:** between PBM read + venue read, a tx clears.
- **Venue rounding:** some venues round balances to N decimals, PBM tracks full precision.

If FP > 25% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 + tier-4 (custody) when:

- Drift > 10x threshold (e.g. > 10k USD).
- `drift_direction == NEGATIVE` (we have less than expected — possible loss).
- Multi-wallet simultaneous drift.

## Success criteria

- Drift cleared OR ledger patched.
- Telegram alert no longer re-firing.

## Post-incident

Required for any drift > 5x threshold OR Path 2/3 used.

## Cross-references

- **Co-firing:** [`margin_threshold_breach.md`](./margin_threshold_breach.md),
  [`preflight_failed.md`](./preflight_failed.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
