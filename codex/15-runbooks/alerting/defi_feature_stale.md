---
scope: [engineer, admin]
title: DEFI_FEATURE_STALE Runbook
status: active
created: 2026-05-08
authoritative_for:
  Operator response when a DeFi feature (LST yield, gas-fee read, on-chain rate) hasn't refreshed within the SLA window.
  Stale features compound lookahead-bias risk + may drive bad signals.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/circuit_breaker_open.md
---

# `DEFI_FEATURE_STALE` Runbook

> **What this is:** an LST-yield read or other DeFi feature hasn't refreshed within the SLA. Strategy decisions made on
> stale features can be confidently-wrong. WARN-severity.

## TL;DR

A DeFi feature (LST yield read for `carry_staked_basis`, gas-fee estimate, or on-chain rate) is older than the freshness
SLA (default 15 min). The downstream calculator may be making decisions on stale data. Operator confirms the upstream
source is up + restarts the feature compute if needed.

## Trigger condition

- **Code:** `DEFI_FEATURE_STALE` (UAC `AlertCode`).
- **Pattern (fnmatch):** `DEFI_FEATURE_STALE`.
- **Threshold key:** `defi_feature_stale_minutes`.
- **Default value:** 15 min. LST yields update on epoch boundaries (≈12 min Solana, ≈12s Ethereum); 15 min is a generous
  lower bound. See [`threshold-tuning.md`](./threshold-tuning.md).
- **Emitter(s):** `features-service (onchain family)` (feature-staleness watchdog, runs every 5 min).
- **Upstream signal:** `now() - feature.available_at > threshold_minutes` for any feature in the `carry_staked_basis` or
  `leveraged_funding_arb` required-feature set.
- **De-dup window:** 600s.

## Severity + paging

- **Severity:** `WARN`.
- **Paging channels:** `TELEGRAM`.
- **Triggers kill-switch:** **FALSE** (DEFERRED post-cutover — when sustained > 30 min, should escalate to a
  `KILL_SWITCH_DEFI_FEATURE_BLACKOUT` code; not yet in UAC; tracked under `plans/epics/observability_master.md`).
- **PagerDuty service:** N/A.

## Diagnosis (first 5 minutes)

1. **Acknowledge** in Telegram.
2. **Pull alert payload:**
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
   Note: `payload.feature_name` (e.g. `lst_yield_jitosol`), `payload.feature_group` (e.g. `lst_yields`),
   `payload.last_update_at`, `payload.staleness_minutes`, `payload.upstream_source`.
3. **Verify upstream source is reachable** (varies by feature):
   - **LST yield (Solana):** ping Pyth Hermes:
     ```bash
     curl -s "https://hermes.pyth.network/api/latest_price_feeds?ids[]=0x..."
     ```
   - **LST yield (Ethereum):** ping Lido / RocketPool / EtherFi APIs:
     ```bash
     curl -s "https://stake.lido.fi/api/apy"
     ```
   - **Gas fee:** ping the chain RPC directly:
     ```bash
     cast gas-price --rpc-url ${ETH_RPC_URL}
     ```
4. **Check features-service (onchain family) health endpoint:**
   ```bash
   curl -sH "Authorization: Bearer $(gcloud auth print-access-token)" \
     https://${FEATURES_ONCHAIN_URL}/health | jq '.data_freshness'
   ```
   `data_freshness` callback per the workspace ServiceBootstrap pattern returns last-update-per-feature.
5. **Check correlated codes** — `CIRCUIT_BREAKER_OPEN` on the upstream venue/RPC often co-fires (feature staleness is
   downstream of source-fetch failure).

## Resolution paths

### Path 1 — Auto-recovery (next compute cycle succeeds)

If diagnosis step 3 shows upstream source is healthy AND step 4 shows features-service (onchain family) is running, the
next compute cycle (typically every 5 min) should resolve the staleness:

```bash
# Watch the feature freshness via health endpoint
watch -n 60 "curl -sH 'Authorization: Bearer \$(gcloud auth print-access-token)' \
  https://\${FEATURES_ONCHAIN_URL}/health | jq '.data_freshness.<feature_name>'"
```

**Success:** `staleness_minutes < threshold` sustained 5 min.

### Path 2 — Restart features-service (onchain family) (compute hung)

If the service is running but the compute is hung (e.g. waiting on a dead RPC handle):

```bash
# Find the running VM or Cloud Run revision
gcloud run services list --platform=managed --format=json \
  | jq '.[] | select(.metadata.name | contains("features-onchain"))'

# Force redeploy = fresh compute pods
gcloud run services update features-service (onchain family) --region=asia-northeast1 \
  --update-env-vars=FORCE_RESTART=$(date +%s)
```

Wait for the rollout (~60s); confirm via Path 1's health check.

**Success:** `staleness_minutes < threshold` after restart.

### Path 3 — Pause downstream archetype (feature unrecoverable)

If upstream source is down for > 30 min AND no workaround exists (e.g. Pyth Solana feed offline + no Switchboard
fallback):

1. Operator pauses the affected archetype via DART → Strategy Config → "Pause Archetype" with reason
   `feature_blackout: <feature_name>`.
2. Existing positions hold flat-only; no new entries.
3. Resume when upstream source returns + features-service (onchain family) `data_freshness` recovers.

**Success:** archetype paused; Telegram noise stops.

## Rollback

- **Undoing restart:** none needed; restart is non-destructive.
- **Undoing pause:** un-pause via DART once upstream recovers.

## Common false-positives

- **Compute-cycle skew:** if the watchdog runs at 14:59 and the feature compute completed at 14:44, staleness is exactly
  15 min — boundary case, may fire then immediately resolve. Action: ack + log.
- **VM cold-start:** during a deploy or VM bounce, feature freshness can briefly exceed SLA. Symptom: alert timestamp
  aligns with deploy / VM-restart event. Action: ack + verify deploy completed.

If FP > 20% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md) — staleness window may need
widening OR upstream-source SLA enforcement.

## Escalation criteria + targets

Escalate to tier-3 strategy lead when:

- Staleness > 30 min AND upstream is unreachable.
- Multiple features stale simultaneously (likely upstream-wide event).
- Path 1 + 2 + 3 all blocked.

## Success criteria

- Feature freshness < threshold sustained 5 min OR archetype paused.
- Telegram alert no longer re-firing.

## Post-incident

Required if Path 3 (archetype pause) was used. Action items: upstream-source SLA review, fallback-source plan,
features-service (onchain family) health-check tightening.

## Cross-references

- **Cascade target (post-cutover):** `KILL_SWITCH_DEFI_FEATURE_BLACKOUT` alert code (not yet in UAC;
  `plans/epics/observability_master.md`).

> **[DELTA 2026-05-22]** **Current state:** No auto-escalation from `DEFI_FEATURE_STALE` to kill-switch. Sustained
> 30-min feature blackout sends Telegram WARN only; no PagerDuty P1; no kill-switch arm. **Planned delta:**
> `plans/epics/observability_master.md` — add `KILL_SWITCH_DEFI_FEATURE_BLACKOUT` to UAC `AlertCode` + wire auto-trigger
> at 30-min sustained staleness. **Target:** Sustained 30-min feature blackout auto-arms kill switch with Telegram +
> PagerDuty P1.

- **Co-firing:** [`circuit_breaker_open.md`](./circuit_breaker_open.md).
- **Operator playbook:** [`operator-playbook.md`](./operator-playbook.md).
- **Threshold tuning:** [`threshold-tuning.md`](./threshold-tuning.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
