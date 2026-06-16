---
scope: [engineer, admin]
title: DEFI_WEETH_DEPEG Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when weETH/ETH peg deviation exceeds tolerance. weETH is core LST collateral for the
  carry_staked_basis archetype; depeg events compound HF risk.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/defi_health_factor_critical.md
  - codex/15-runbooks/alerting/kill_switch_defi_liquidation_risk.md
---

# `DEFI_WEETH_DEPEG` Runbook

> **What this is:** weETH (or sister LST: jitoSOL, mSOL, bSOL, stETH) traded too far from its underlying ETH peg. LSTs
> are core collateral for `carry_staked_basis`; a depeg compresses HF and may invalidate the carry thesis.

## TL;DR

weETH/ETH cross-rate (live AMM mid) deviated from the redemption-rate peg by more than the tolerance threshold (default
50bps). Depeg events typically resolve within hours but can amplify HF risk on Aave positions using weETH as collateral.
Operator should reduce LST exposure if depeg widens; pre-emptive deleverage if HF is also declining.

## Trigger condition

- **Code:** `DEFI_WEETH_DEPEG` (UAC `AlertCode`).
- **Pattern (fnmatch):** `DEFI_WEETH_DEPEG`.
- **Threshold key:** `defi_weeth_depeg_bps`.
- **Default value:** 50 bps (0.5% from peg). weETH historical max-depeg under normal conditions ≈ 30bps; 50bps catches
  abnormal events without firing on normal chop. See [`threshold-tuning.md`](./threshold-tuning.md) for citation.
- **Emitter(s):** `features-service (onchain family)` (LST-peg deviation calculator, 30s polling).
- **Upstream signal:** `(weETH_amm_price / weETH_redemption_rate) - 1` exceeds threshold (in absolute value) sustained
  ≥30s.
- **De-dup window:** 300s.

## Severity + paging

- **Severity:** `CRITICAL`.
- **Paging channels:** `PAGERDUTY`, `TELEGRAM`.
- **Triggers kill-switch:** **FALSE** (escalates indirectly via `KILL_SWITCH_DEFI_LIQUIDATION_RISK` if HF compresses).
- **PagerDuty service:** `uts-prod-live-trading` P1.

## Diagnosis (first 5 minutes)

1. **Acknowledge** within 5 min.
2. **Pull alert payload:**
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
   Note: `payload.lst` (weeth/jitosol/etc.), `payload.amm_price`, `payload.redemption_rate`, `payload.depeg_bps`,
   `payload.exposure_usd` (our exposure).
3. **Cross-check on-chain** via direct AMM read + redemption-rate read. For weETH on Curve:
   ```bash
   # weETH/WETH Curve pool
   cast call 0xDB74dfDD3BB46bE8Ce6C33dC9D82777BCFc3dEd5 "get_dy(int128,int128,uint256)(uint256)" \
     0 1 1000000000000000000 --rpc-url ${ETH_RPC_URL}
   # ether.fi redemption rate (eETH per weETH)
   cast call 0x35fA164735182de50811E8e2E824cFb9B6118ac2 "getRate()(uint256)" --rpc-url ${ETH_RPC_URL}
   ```
   Compute the ratio; compare to alert payload's `depeg_bps`.
4. **Check broader market context** — is this a single-LST event or sector-wide? Compare to other LSTs:
   ```bash
   # stETH/ETH on Curve
   cast call 0x21E27a5E5513D6e65C4f830167390997aA84843a "get_dy(int128,int128,uint256)(uint256)" \
     0 1 1000000000000000000 --rpc-url ${ETH_RPC_URL}
   ```
   If multiple LSTs depeg simultaneously → potential ETH-staking-wide event (validator-exit queue surge, slashing
   incident, regulatory).
5. **Check correlated codes** — `DEFI_HEALTH_FACTOR_CRITICAL` very likely co-fires (weETH-as-collateral worth less in
   USD as it depegs). `DEFI_RATE_DEVIATION` may also co-fire (oracle-vs-DEX divergence).

## Resolution paths

### Path 1 — Depeg is transient (resolves within 1h)

If diagnosis step 3 confirms depeg ≤ 70bps AND no broader sector event AND no co-firing HF alert, monitor without
action:

```bash
watch -n 60 "cast call 0xDB74dfDD3BB46bE8Ce6C33dC9D82777BCFc3dEd5 \
  \"get_dy(int128,int128,uint256)(uint256)\" 0 1 1000000000000000000 --rpc-url \${ETH_RPC_URL}"
```

Most weETH depegs resolve within 1-4h via arbitrageurs.

**Success:** depeg < threshold sustained 30 min.

### Path 2 — Reduce LST exposure (depeg widening)

If depeg is widening OR HF is declining, partially unwind LST collateral:

1. Open DART → Manual Trade Gate → "Reduce LST Exposure" wizard.
2. Wizard proposes: swap weETH → ETH on AMM (best-rate router) + repay debt to maintain HF.
3. Operator reviews slippage; expect 30-100bps slippage on a depegged AMM (the depeg IS the cost of unwind).
4. Sign + execute.

Verify exposure reduced in PBM:

```bash
curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" \
  https://${PBM_URL}/positions?asset=weETH | jq '.positions[].size'
```

**Success:** weETH exposure reduced to operator-target level + HF ≥ 1.30.

### Path 3 — Full LST exit (sector-wide event)

If multiple LSTs depeg simultaneously (sector-wide event), exit all LST positions:

1. Operator + tier-3 strategy lead joint decision.
2. DART → Manual Trade Gate → "LST Sector Exit" wizard. All LST positions queued for unwind.
3. Execute in priority order: largest exposure first, lowest-liquidity AMM last.
4. Verify positions zero in PBM.

**Success:** all LST exposure → 0 (or operator-target floor) + carry_staked_basis archetype halted via DART.

## Rollback

- **Undoing exits:** no rollback. Re-establish positions via normal strategy flow once depeg resolves.

## Common false-positives

- **Single-block AMM read snapshot:** AMM price reads from a single block can deviate 30+bps from VWAP if a large swap
  just landed. Symptom: depeg_bps in alert payload is much wider than minute-VWAP. Action: re-read after 30s; if
  resolved, ack + log.
- **Oracle-vs-AMM diff (NOT actual depeg):** `defi_weeth_depeg` measures AMM mid vs redemption rate; if the alert source
  incorrectly reads oracle-USD vs AMM-USD, this is a code bug not a real depeg. Action: investigate features-service
  (onchain family) emitter.

If FP > 5% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 + tier-4 when:

- Depeg > 200bps (sector-wide event likely).
- Multiple LSTs depeg simultaneously.
- HF co-fires AND on-chain liquidity for unwind is < 5x exposure.

## Success criteria

- Depeg < threshold sustained 30 min OR exposure unwound.
- DART Active Alerts shows alert `resolved`.
- Post-incident write-up filed if real-money action taken.

## Post-incident

Required if Path 2 or 3 used. Action items: LST diversification policy review, depeg-tolerance threshold review,
on-chain liquidity audit per LST.

## Cross-references

- **Cascade target:** [`kill_switch_defi_liquidation_risk.md`](./kill_switch_defi_liquidation_risk.md).
- **Co-firing:** [`defi_health_factor_critical.md`](./defi_health_factor_critical.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Threshold tuning:** [`threshold-tuning.md`](./threshold-tuning.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
