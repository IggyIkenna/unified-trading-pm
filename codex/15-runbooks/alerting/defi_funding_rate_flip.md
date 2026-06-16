---
scope: [engineer, admin]
title: DEFI_FUNDING_RATE_FLIP Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when a perp funding rate flips sign within a short window. Regime change signal for
  leveraged_funding_arb archetype; may invalidate carry assumptions.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/defi_aave_utilization_spike.md
---

# `DEFI_FUNDING_RATE_FLIP` Runbook

> **What this is:** a perp venue's funding rate flipped sign by more than the threshold in a 5-minute window. Funding-
> arb strategies depend on consistent funding direction; a flip is a regime-change signal. WARN-severity (Telegram
> only).

## TL;DR

A perp's funding rate (annualized) shifted by > 100 bps in 5min, and the new rate has the opposite sign of the prior
rate. The `leveraged_funding_arb` archetype's carry-direction assumption is now invalid — operator reviews whether to
re-pole or exit. Telegram-only; not a paging alert because funding flips can be transient and self-correcting.

## Trigger condition

- **Code:** `DEFI_FUNDING_RATE_FLIP` (UAC `AlertCode`).
- **Pattern (fnmatch):** `DEFI_FUNDING_RATE_FLIP`.
- **Threshold key:** `defi_funding_rate_flip_bps_5m`.
- **Default value:** 100 bps APR magnitude flip in 5 min, with sign change. See
  [`threshold-tuning.md`](./threshold-tuning.md) for citation.
- **Emitter(s):** `features-service (onchain family)` (perp funding-rate calc; reads from venue REST + on-chain perp
  protocols like Hyperliquid/Aster).
- **Upstream signal:**
  `sign(funding_rate_t) != sign(funding_rate_t-5m) AND |funding_rate_t − funding_rate_t-5m| × 365 × 24 × 12 > 100 bps`.
- **De-dup window:** 600s.

## Severity + paging

- **Severity:** `WARN`.
- **Paging channels:** `TELEGRAM`.
- **Triggers kill-switch:** **FALSE**.
- **PagerDuty service:** N/A.

## Diagnosis (first 5 minutes)

1. **Acknowledge** in Telegram.
2. **Pull alert payload:**
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
   Note: `payload.venue` (e.g. `bybit`, `hyperliquid`), `payload.symbol` (e.g. `ETH-PERP`), `payload.prior_funding_apr`,
   `payload.current_funding_apr`, `payload.flip_window_minutes`, `payload.archetype_position` (current size if any).
3. **Cross-check current funding via venue API:**
   ```bash
   # Bybit example
   curl -s "https://api.bybit.com/v5/market/funding/history?category=linear&symbol=ETHUSDT&limit=5" \
     | jq '.result.list[] | {fundingRateTimestamp, fundingRate}'
   # Hyperliquid example
   curl -s -X POST https://api.hyperliquid.xyz/info -H 'Content-Type: application/json' \
     -d '{"type":"meta"}' | jq '.universe[] | select(.name=="ETH") | .funding'
   ```
4. **Identify driver** — flip can be triggered by: (a) large directional flow on a single venue, (b) cross-venue
   arbitrage closing a basis, (c) macro event (Fed, CPI, ETF flow). Check venue's recent open-interest changes.
5. **Check correlated codes** — `DEFI_AAVE_UTILIZATION_SPIKE` may co-fire if the flip drives borrowing-side rebalance.
   `MARGIN_THRESHOLD_BREACH` may fire if the position's mark-price moved against us.

## Resolution paths

### Path 1 — Funding mean-reverts (transient flip)

Most short-window flips revert within 30-60 min as the next funding window prices in:

```bash
# Watch funding evolution
watch -n 60 "curl -s 'https://api.bybit.com/v5/market/funding/history?category=linear&symbol=ETHUSDT&limit=2' \
  | jq '.result.list[] | {fundingRateTimestamp, fundingRate}'"
```

**Success:** funding magnitude returns to within 50bps of prior 24h average sustained 30 min.

### Path 2 — Re-pole position (sustained flip = real regime change)

If the flip persists > 1h AND magnitude is > 200 bps APR opposite the original direction, the regime has flipped:

1. Operator reviews `leveraged_funding_arb` thesis: is the new funding direction profitable to the OPPOSITE pole?
2. If yes: open DART → Strategy Config → "Re-Pole leveraged_funding_arb" wizard. Wizard unwinds current pole + opens
   opposite pole.
3. If no: pause the archetype (Path 3).

Verify position direction in PBM:

```bash
curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" \
  "https://${PBM_URL}/positions?archetype=leveraged_funding_arb" | jq '.positions[] | {symbol, side, size}'
```

**Success:** position aligned with new funding direction + net carry positive.

### Path 3 — Pause archetype (regime unclear)

If the flip is sustained but the new direction's magnitude is too small to be profitable:

1. Open DART → Strategy Config → "Pause Archetype" → `leveraged_funding_arb`.
2. strategy-service stops emitting signals; existing positions held flat-only.
3. Resume after the funding-rate environment stabilizes (operator judgment, typically 24-72h).

**Success:** archetype paused + Telegram noise stops.

## Rollback

- **Undoing re-pole:** open DART → Re-Pole back to original direction; execution-service unwinds + re-establishes.
- **Undoing pause:** un-pause via DART.

## Common false-positives

- **Funding-window boundary:** funding rates settle at fixed intervals (e.g. 8h on Binance, 1h on Hyperliquid). The flip
  may align exactly with a settlement boundary causing a brief spike. Symptom: alert timestamp aligns with
  funding-settlement timestamp. Action: re-read after the next window.
- **Single-venue outlier:** if only one venue shows the flip but others show consistent funding, it's a venue-specific
  flow, not a regime change. Action: if archetype trades on multiple venues with consistent funding elsewhere, ack +
  log.

If FP > 30% per 24h sustained (this alert is noisy by design — funding moves), raise via
[`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate to tier-3 (strategy lead) when:

- Multi-venue funding flip (3+ venues simultaneously) with magnitude > 500 bps APR.
- Re-pole would require unwinding > 100k USD position (size justifies a sanity check).

## Success criteria

- Funding stabilized OR position re-poled OR archetype paused.
- Telegram alert no longer re-firing.

## Post-incident

NOT required for transient flips. Required if Path 2 was used (real money moved). Action items: regime-detection
threshold review, funding-curve forecast model audit.

## Cross-references

- **Co-firing:** [`defi_aave_utilization_spike.md`](./defi_aave_utilization_spike.md),
  [`margin_threshold_breach.md`](./margin_threshold_breach.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Threshold tuning:** [`threshold-tuning.md`](./threshold-tuning.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
