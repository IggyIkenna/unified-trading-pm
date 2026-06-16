---
scope: [engineer, admin]
title: KILL_SWITCH_DEFI_LIQUIDATION_RISK Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when the DeFi liquidation-risk kill-switch fires. Halts execution-service DeFi connectors + paper-
  trade strategies + auto-deleverages collateral when health-factor approaches 1.0. Highest-impact alert in the live-
  DeFi pipeline; tier-1 page + circuit-breaker propagation.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/active/master_to_live_defi_2026_05_23.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/alert-code-taxonomy.md
  - codex/15-runbooks/alerting/defi_health_factor_critical.md
  - codex/15-runbooks/alerting/circuit_breaker_open.md
  - codex/04-architecture/flash-loan-receiver.md
execution:
  owner: on-call operator (Ikenna / Harsh by rotation)
  cadence: on-demand (incident response) + quarterly DR drill
  verifier: DeFi connectors halted; collateral deleverage tx confirmed on-chain; health-factor >1.3 before re-arm
  last_executed: never
---

# `KILL_SWITCH_DEFI_LIQUIDATION_RISK` Runbook

> **What this is:** the most severe DeFi alert. An open Aave (or other money-market) position is approaching
> liquidation. The kill-switch publishes a `KillSwitchEvent` to halt every downstream subscriber and triggers
> auto-deleveraging via flash-loan receiver. Operator confirms safety + signs off on resume.

## TL;DR

A wallet position's health factor crossed the critical threshold (default HF ≤ 1.05; liquidation at HF < 1.0). Aave
liquidators get a 5% bonus when liquidating below HF=1.0, so we have ~5% buffer before forced sale. The kill-switch
auto-halts strategy-service signal generation, blocks new position-opens in execution-service, and stages an auto-
deleverage tx via the flash-loan receiver. Operator MUST confirm the auto-deleverage executed before resume.

## Trigger condition

- **Code:** `KILL_SWITCH_DEFI_LIQUIDATION_RISK` (UAC `AlertCode`).
- **Pattern (fnmatch):** `KILL_SWITCH_*` (one wildcard rule covers all 3 KILL*SWITCH*\* codes — see
  [`alert-code-taxonomy.md`](./alert-code-taxonomy.md)).
- **Threshold key:** `defi_health_factor_critical`.
- **Default value:** 1.05 (Aave HF; below 1.0 triggers liquidation; 5% buffer matches Tenderly / Hypernative / Gauntlet
  industry default — see [`threshold-tuning.md`](./threshold-tuning.md)).
- **Emitter(s):** `features-service (onchain family)` (Aave HF calculator); `risk-and-exposure-service` (cross-position
  aggregator).
- **Upstream signal:** Real-time Aave `getUserAccountData(user)` call returning `healthFactor` < 1.05e18 (RAY units).
- **De-dup window:** 60s — bursty oracle reads collapse to one alert.

## Severity + paging

- **Severity:** `CRITICAL` (UAC `AlertSeverity.CRITICAL`).
- **Paging channels:** `PAGERDUTY`, `TELEGRAM`.
- **Triggers kill-switch:** **TRUE** — publishes `KillSwitchEvent(scope=DEFI_LIQUIDATION_RISK)` to the bus. Subscribers:
  execution-service (halt new DeFi orders), strategy-service (halt signal emission for `carry_staked_basis` +
  `leveraged_funding_arb`), DART (display halt banner).
- **PagerDuty service:** `uts-prod-live-trading` P1.

## Diagnosis (first 5 minutes)

1. **Acknowledge the page** within 5 minutes. PagerDuty auto-escalates to Harsh after 30min.
2. **Pull the alert payload** from DART Active Alerts:
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
   Note: `payload.health_factor`, `payload.wallet_address`, `payload.chain`, `payload.collateral_usd`,
   `payload.debt_usd`.
3. **Verify on-chain HF in real time** (do NOT trust the cached event — read the chain directly):
   ```bash
   # For Ethereum mainnet (replace RPC with your prod RPC):
   cast call 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 \
     "getUserAccountData(address)" <wallet_address> \
     --rpc-url ${ETH_RPC_URL} | xargs -I{} python3 -c "import struct,sys; print('HF:',int(sys.argv[1][130:194],16)/1e18)" {}
   ```
   If HF reads ≥1.10 the alert was a transient oracle blip — proceed to "Common false-positives." If HF < 1.05 continue.
4. **Check whether auto-deleverage already fired** by tailing execution-service events:
   ```bash
   gcloud storage cat gs://${PROJECT_ID}-events/events/execution-service/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl \
     | jq -c 'select(.event=="DEFI_AUTO_DELEVERAGE_EXECUTED")' | tail -3
   ```
   Look for `tx_hash` + `status=success`. If found and HF post-tx is ≥1.20, alert is resolving — proceed to Path 1.
5. **Check correlated codes** — `DEFI_HEALTH_FACTOR_CRITICAL` always co-fires; if `DEFI_WEETH_DEPEG` ALSO fires this is
   a likely LST-collateral event (peg break inflated debt-to-collateral ratio). Search:
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --limit=20 --format=json | jq '.[].message.data | @base64d | fromjson | {code,severity,timestamp}'
   ```

## Resolution paths

### Path 1 — Auto-deleverage succeeded

If diagnosis step 4 returned a successful `DEFI_AUTO_DELEVERAGE_EXECUTED` event AND step 3 shows HF ≥ 1.20, the
flash-loan receiver has unwound the at-risk leg. Action:

```bash
# Verify positions in DART
open https://dart.uts.example.com/positions?wallet=<wallet>

# Confirm strategy-service stopped + execution-service halted (heartbeat events)
gcloud storage cat gs://${PROJECT_ID}-events/events/strategy-service/$(date -u +%Y-%m-%d)/*/hour=*/*.jsonl \
  | jq -c 'select(.event=="STRATEGY_HALT_ACKNOWLEDGED")' | tail -3
```

**Success:** HF ≥ 1.20 sustained for 5 min, all subscribers ack'd halt, no re-fire of `KILL_SWITCH_*`. Operator may then
follow the **resume-from-halt** procedure (below).

### Path 2 — Manual deleverage (auto failed)

If auto-deleverage did NOT fire (e.g. flash-loan-receiver contract not deployed or oracle paused), the operator must
manually unwind via DART manual-trade-gate. Each step requires a DART operator-action confirmation.

1. Open DART → Manual Trade Gate → "DeFi Deleverage" wizard. Pick the wallet from the alert payload.
2. Wizard computes minimum collateral-withdrawal + debt-repay split to bring HF ≥ 1.30. Operator reviews the slippage
   estimate (warn if > 1%) + signs.
3. Tx executes via execution-service `UniswapConnector.swap_exact_input` for the asset swap leg + `AaveConnector.repay`
   for the debt-repay leg.
4. Verify resolution:
   ```bash
   # HF post-trade
   cast call 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 \
     "getUserAccountData(address)" <wallet_address> \
     --rpc-url ${ETH_RPC_URL}
   ```

**Success:** HF ≥ 1.30 + DART confirms position update.

### Path 3 — Full halt (auto + manual both fail)

Only when Path 1 + 2 are blocked (e.g. RPC outage, flash-loan-receiver not deployed, Aave pool paused). Operator
manually flips the platform-wide kill-switch via DART:

```bash
# DART → Manual Trade Gate → Platform Halt → DEFI scope
# OR: direct kill-switch-bus publish (audit-trail goes to operator-action log)
gcloud pubsub topics publish projects/${PROJECT_ID}/topics/kill-switch-bus \
  --message='{"scope":"DEFI_PLATFORM","reason":"manual_halt_liquidation_risk_unresolvable","operator":"<name>"}'
```

**Success:** execution-service halts new DeFi orders within 10s. Operator notifies tier-3 (strategy lead) immediately
because positions are exposed to liquidation without auto-recovery.

## Resume-from-halt procedure

After ANY resolution path:

1. Confirm HF ≥ 1.30 sustained for ≥5 min (`watch -n 30 cast call ...`).
2. Confirm no other `KILL_SWITCH_*` alerts active in DART.
3. Operator publishes `KillSwitchEvent(scope=DEFI_LIQUIDATION_RISK, action=RESUME)` via DART manual-trade-gate.
4. strategy-service + execution-service ack the resume; DART halt banner clears.
5. Monitor for re-fire 30 min — if no re-fire, ack the alert.

## Rollback

- **Undoing manual deleverage:** there is no clean rollback for an executed swap — it's an on-chain tx. The right
  rollback is a fresh trade in the opposite direction, executed via DART manual-trade-gate. Do NOT attempt without
  operator + tier-3 sign-off (P&L impact).
- **Undoing platform halt:** publish `KillSwitchEvent(scope=DEFI_PLATFORM, action=RESUME)` per resume procedure above.

## Common false-positives

- **Oracle stale read:** Chainlink oracle's last-update timestamp > 1h old. Symptom: HF in alert payload ≠ HF on
  direct-RPC read. Action: ack + raise via [`threshold-tuning.md`](./threshold-tuning.md) — likely needs an oracle-
  staleness pre-check in features-service (onchain family).
- **HF dip during a borrowing tx:** during a leverage-up tx the HF temporarily dips before rebalance. If diagnosis step
  4 shows the alert's wallet was mid-tx (`PENDING_TX_DETECTED` event within 30s prior), this is benign. Action: ack +
  log; do NOT page tier-2.

If FP rate exceeds 5% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md) review.

## Escalation criteria + targets

Escalate to tier-3 (strategy lead) immediately when ANY of:

- HF < 1.02 (15bps from liquidation; auto-deleverage may not complete in time).
- `DEFI_POSITION_LIQUIDATED` co-fires (already liquidated — post-mortem time).
- Path 1 + 2 both fail.
- Total at-risk USD > 50k (operator judgment).

Tier-4 (custody) ONLY for >250k USD at risk.

## Success criteria

- HF ≥ 1.30 sustained 5 min.
- DART Active Alerts shows alert `resolved`.
- All `KILL_SWITCH_*` subscribers ack'd resume.
- Post-incident write-up filed within 24h.

## Post-incident

Mandatory for every CRITICAL true-positive. Template at [`operator-playbook.md`](./operator-playbook.md) §
post-incident. Action items typically include: oracle-staleness pre-check, HF threshold review, flash-loan-receiver
deploy-state audit, position-size limit review.

## Cross-references

- **AlertCode taxonomy:** [`alert-code-taxonomy.md`](./alert-code-taxonomy.md).
- **Threshold rationale:** [`threshold-tuning.md`](./threshold-tuning.md).
- **Operator playbook (high-level):** [`operator-playbook.md`](./operator-playbook.md).
- **Sibling kill-switches:** [`kill_switch_portfolio_drawdown.md`](./kill_switch_portfolio_drawdown.md),
  [`kill_switch_venue_disconnect.md`](./kill_switch_venue_disconnect.md).
- **Co-firing alerts:** [`defi_health_factor_critical.md`](./defi_health_factor_critical.md),
  [`defi_weeth_depeg.md`](./defi_weeth_depeg.md).
- **Flash-loan-receiver:**
  [`codex/04-architecture/flash-loan-receiver.md`](../../04-architecture/flash-loan-receiver.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
