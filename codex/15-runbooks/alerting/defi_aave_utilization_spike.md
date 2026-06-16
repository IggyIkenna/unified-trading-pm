---
scope: [engineer, admin]
title: DEFI_AAVE_UTILIZATION_SPIKE Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when an Aave pool utilization crosses the kink point. Above the kink, borrow APR rises sharply +
  carry-strategy assumptions break.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/defi_health_factor_critical.md
  - codex/15-runbooks/alerting/defi_funding_rate_flip.md
---

# `DEFI_AAVE_UTILIZATION_SPIKE` Runbook

> **What this is:** Aave pool utilization crossed the InterestRateStrategy kink (default 95% for WETH/USDC/USDT/DAI on
> V3). Above the kink, borrow APR scales steeply with utilization, eroding carry-strategy edge. Operator decides:
> tighten exposure or tolerate.

## TL;DR

An Aave reserve's `total_debt / total_supply > 95%` (per UAC `defi_aave_utilization_spike_bps=9500`). Borrow rate from
this point spikes; the carry trade's debt cost may exceed the staking yield. WARN-severity (Telegram only) — not a
paging alert because borrow-rate spikes can be transient.

## Trigger condition

- **Code:** `DEFI_AAVE_UTILIZATION_SPIKE` (UAC `AlertCode`).
- **Pattern (fnmatch):** `DEFI_AAVE_UTILIZATION_SPIKE`.
- **Threshold key:** `defi_aave_utilization_spike_bps`.
- **Default value:** 9500 (95.00% in `BPS_OF_ONE` units). Per-archetype override: `leveraged_funding_arb=9000` (90% —
  tighter signal). See [`threshold-tuning.md`](./threshold-tuning.md) for citation to Aave V3 InterestRateStrategy
  `optimalUsageRatio=0.95 RAY` for WETH/USDC/USDT/DAI.
- **Emitter(s):** `features-service (onchain family)` (Aave pool-utilization calc, 1m polling).
- **Upstream signal:** `getReserveData(asset).totalDebt / (totalDebt + availableLiquidity)` exceeds threshold sustained
  ≥ 60s.
- **De-dup window:** 600s.

## Severity + paging

- **Severity:** `WARN`.
- **Paging channels:** `TELEGRAM`.
- **Triggers kill-switch:** **FALSE**.
- **PagerDuty service:** N/A (Telegram only).

## Diagnosis (first 5 minutes)

1. **Acknowledge** in Telegram (no PagerDuty page).
2. **Pull alert payload:**
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
   Note: `payload.asset` (e.g. WETH), `payload.utilization_pct`, `payload.current_borrow_apr`, `payload.archetype`
   (which archetype is exposed).
3. **Verify on-chain via direct Aave read:**
   ```bash
   # Aave V3 PoolDataProvider
   cast call 0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3 \
     "getReserveData(address)(uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint256,uint40)" \
     <asset_address> --rpc-url ${ETH_RPC_URL}
   # totalAToken (supply) is field 2; totalVariableDebt is field 6
   ```
4. **Estimate borrow-rate trajectory** — at 95% utilization, V3 rate model:
   `rate = optimal_rate + (utilization − optimal) / (1 − optimal) × jump_rate`. With current jump_rate ≈ 60% APR, every
   1% utilization above kink adds ~12% APR.
5. **Check correlated codes** — typically a benign WARN with no co-fires. If `DEFI_HEALTH_FACTOR_CRITICAL` co-fires,
   utilization is compounding HF risk via debt accrual.

## Resolution paths

### Path 1 — Wait + monitor (utilization recedes)

Pool utilization typically recedes within hours as new supply / repayments arrive. Telegram-only alert means low
operator-action pressure. Monitor:

```bash
# Loop over the asset's utilization
watch -n 120 "cast call 0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3 \
  \"getReserveData(address)\" <asset_address> --rpc-url \${ETH_RPC_URL} | head"
```

**Success:** utilization < threshold − 200bps (e.g. < 93%) sustained 30 min.

### Path 2 — Tighten archetype exposure (utilization remains high)

If utilization stays > 95% for > 1h AND the archetype's net carry has flipped negative:

1. Operator calculates current net carry: `(staking_yield_apr − borrow_apr) × leverage`. Negative means we're paying the
   spread — exit candidate.
2. Open DART → Strategy Config → "Reduce Archetype Exposure" wizard for `carry_staked_basis` / `leveraged_funding_arb`.
   Reduce target leverage by ~25% per click.
3. strategy-service emits exit signals proportional to leverage reduction; execution-service unwinds.
4. Verify positions in PBM:
   ```bash
   curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" \
     "https://${PBM_URL}/positions?archetype=<name>" | jq '.positions[] | {asset, size, leverage}'
   ```

**Success:** archetype leverage at new target + net carry returns positive (or at-zero).

### Path 3 — Pause archetype (utilization stays high indefinitely)

If utilization stays > 95% for > 12h AND borrow APR exceeds staking yield by > 200bps sustained:

1. Tier-3 strategy lead reviews the archetype's continuing-viability.
2. Operator pauses the archetype via DART → Strategy Config → "Pause Archetype". strategy-service stops emitting new
   entry signals; existing positions held until the rate normalizes.

**Success:** archetype paused + Telegram noise from this code stops.

## Rollback

- **Undoing exposure reduction:** re-increase target leverage in DART once utilization recedes; strategy-service resumes
  adding exposure on next signal.
- **Undoing pause:** un-pause via DART; strategy-service resumes signal emission.

## Common false-positives

- **Liquidity migration on the kink:** brief 95.5%→94.5% oscillation can fire then resolve in 5 min. Symptom: alert
  fires + auto-resolves quickly. Action: ack + log.
- **Single-block utilization snapshot:** large supply / repay tx can briefly show >95%. Action: re-read after 60s.

If FP > 25% per 24h sustained (this is a noisy alert by design), raise via
[`threshold-tuning.md`](./threshold-tuning.md) — likely needs a higher threshold or longer sustaining window.

## Escalation criteria + targets

Escalate to tier-3 (strategy lead) when:

- Utilization > 99% (rate model in extreme region).
- Net carry negative > 24h continuous.

## Success criteria

- Utilization < threshold sustained 30 min OR archetype paused.
- Telegram alert no longer re-firing.

## Post-incident

NOT required for transient utilization spikes. Required if Path 3 (archetype pause) was used — action items:
archetype-viability review, exposure-limit policy review.

## Cross-references

- **Co-firing:** [`defi_health_factor_critical.md`](./defi_health_factor_critical.md),
  [`defi_funding_rate_flip.md`](./defi_funding_rate_flip.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Threshold tuning:** [`threshold-tuning.md`](./threshold-tuning.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
