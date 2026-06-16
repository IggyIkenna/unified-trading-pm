---
scope: [engineer, admin]
title: DEFI_HEALTH_FACTOR_CRITICAL Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when an Aave (or other money-market) position's health factor crosses the critical threshold but has
  NOT yet triggered the kill-switch. Pre-emptive deleverage candidate.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/kill_switch_defi_liquidation_risk.md
  - codex/15-runbooks/alerting/defi_weeth_depeg.md
execution:
  owner: on-call operator (Ikenna / Harsh by rotation)
  cadence: on-demand (incident response)
  verifier: health factor recovers above threshold; no kill-switch fired; position audit passes
  last_executed: never
---

# `DEFI_HEALTH_FACTOR_CRITICAL` Runbook

> **What this is:** an early-warning HF alert. The position's HF is below the per-archetype critical threshold but still
> above the kill-switch threshold. Operator can preemptively rebalance OR allow the kill-switch to fire. Lower- severity
> than `KILL_SWITCH_DEFI_LIQUIDATION_RISK` but on the same axis.

## TL;DR

Aave HF is in the warning band — operator should review the position before the kill-switch fires. Default critical
threshold is 1.05 (5% buffer above liquidation at HF=1.0). Pre-emptive deleverage via DART manual-trade-gate is
preferred over waiting for kill-switch auto-deleverage (saves slippage; preserves PnL). PagerDuty CRITICAL but not a
kill-switch event.

## Trigger condition

- **Code:** `DEFI_HEALTH_FACTOR_CRITICAL` (UAC `AlertCode`).
- **Pattern (fnmatch):** `DEFI_HEALTH_FACTOR_CRITICAL`.
- **Threshold key:** `defi_health_factor_critical`.
- **Default value:** 1.05 (Aave HF; below 1.0 triggers liquidation; 5% buffer = 5pp above liquidation). Per-archetype
  override for `leveraged_funding_arb` may be tighter (1.10) — see [`threshold-tuning.md`](./threshold-tuning.md).
- **Emitter(s):** `features-service (onchain family)` (Aave HF calculator, 5s polling).
- **Upstream signal:** Aave `getUserAccountData(user).healthFactor` < threshold sustained ≥ 30s.
- **De-dup window:** 60s.

## Severity + paging

- **Severity:** `CRITICAL`.
- **Paging channels:** `PAGERDUTY`, `TELEGRAM`.
- **Triggers kill-switch:** **FALSE** (ladder: HF < 1.05 emits THIS alert; HF < 1.02 also fires
  `KILL_SWITCH_DEFI_LIQUIDATION_RISK`).
- **PagerDuty service:** `uts-prod-live-trading` P1.

## Diagnosis (first 5 minutes)

1. **Acknowledge** within 5 min.
2. **Pull alert payload:**
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
   Note: `payload.health_factor`, `payload.wallet_address`, `payload.chain`, `payload.collateral_breakdown`,
   `payload.debt_breakdown`.
3. **Verify on-chain HF in real time** (do NOT trust the cached event):
   ```bash
   cast call 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 \
     "getUserAccountData(address)" <wallet_address> \
     --rpc-url ${ETH_RPC_URL} | xargs -I{} python3 -c "import sys; print('HF:',int(sys.argv[1][130:194],16)/1e18)" {}
   ```
4. **Identify drift driver** — collateral price drop OR debt accrual? Pull recent oracle reads:
   ```bash
   # WETH/USD oracle
   cast call 0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419 "latestAnswer()(int256)" --rpc-url ${ETH_RPC_URL}
   ```
   Compare to the price 1h ago via Coingecko / similar. >2% drop = collateral-price-driven; debt accrual otherwise.
5. **Check correlated codes** — `DEFI_WEETH_DEPEG` co-fires when LST collateral broke peg; `DEFI_AAVE_UTILIZATION_SPIKE`
   may co-fire if borrowing-cost surge accelerated debt growth.

## Resolution paths

### Path 1 — Wait + monitor (HF stabilizes / recovers)

If HF is stable above threshold ± 1pp AND the drift driver is benign (e.g. micro oracle blip), monitor for 10min without
action:

```bash
watch -n 30 "cast call 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 \
  \"getUserAccountData(address)\" <wallet_address> --rpc-url \${ETH_RPC_URL}"
```

**Success:** HF returns above threshold + 0.05 (e.g. 1.10 if threshold is 1.05) sustained 5 min.

### Path 2 — Pre-emptive deleverage via DART manual-trade-gate

Preferred when HF is trending down. Open DART → Manual Trade Gate → "DeFi Deleverage" wizard. Wizard computes minimum
unwind to bring HF ≥ 1.30. Operator reviews slippage estimate, signs.

```bash
# Wizard executes:
# 1. AaveConnector.repay(asset, amount) — debt-repay leg
# 2. UniswapConnector.swap_exact_input(...) — collateral-swap leg if needed
```

Verify post-trade HF:

```bash
cast call 0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2 \
  "getUserAccountData(address)" <wallet_address> --rpc-url ${ETH_RPC_URL}
```

**Success:** HF ≥ 1.30 confirmed on-chain + DART positions panel updated.

### Path 3 — Allow kill-switch to fire (least preferred)

If Paths 1 + 2 are blocked AND HF continues declining, the kill-switch (`KILL_SWITCH_DEFI_LIQUIDATION_RISK`) will fire
at HF < 1.02 and auto-deleverage via flash-loan-receiver. See
[`kill_switch_defi_liquidation_risk.md`](./kill_switch_defi_liquidation_risk.md) for the auto-deleverage path.

**Success:** kill-switch fires + auto-deleverage executes successfully + HF recovers.

## Rollback

- **Undoing pre-emptive deleverage:** none — fresh trades only. Re-establish position via normal strategy flow once
  conditions stabilize.

## Common false-positives

- **Cross-block HF read jitter:** HF reads may differ slightly between consecutive blocks due to interest-accrual
  rounding. Symptom: HF flips above/below threshold within 30s. Action: ack + log; threshold tuning may need hysteresis.
- **Oracle update boundary:** Chainlink updates at deviation thresholds; HF can step down sharply on oracle update.
  Symptom: HF dropped exactly at oracle-update timestamp. Action: confirm new oracle price reflects on-chain reality
  (CEX cross-check); if benign, ack + log.

If FP > 10% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 when:

- HF < 1.03 (kill-switch about to fire).
- Co-fires with `DEFI_WEETH_DEPEG` (LST collateral break).
- Total at-risk USD > 25k.

## Success criteria

- HF ≥ 1.30 sustained 5 min OR position unwound.
- DART Active Alerts shows alert `resolved`.
- Post-incident write-up filed if real-money action taken.

## Post-incident

Required if Path 2 was used (real money moved) OR if Path 3 cascade occurred. Action items: HF threshold review,
oracle-staleness pre-check audit, position-size policy review.

## Cross-references

- **Cascade target:** [`kill_switch_defi_liquidation_risk.md`](./kill_switch_defi_liquidation_risk.md).
- **Co-firing:** [`defi_weeth_depeg.md`](./defi_weeth_depeg.md),
  [`defi_aave_utilization_spike.md`](./defi_aave_utilization_spike.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Threshold tuning:** [`threshold-tuning.md`](./threshold-tuning.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
