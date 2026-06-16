---
scope: [engineer, admin]
title: "<AlertCode> Runbook (Template)"
status: template
created: 2026-05-08
authoritative_for:
  Canonical shape for per-AlertCode operator runbooks. Every runbook in this directory MUST conform to this template.
  Copy this file, replace `<AlertCode>` with the actual code, and fill in every section. Empty sections MUST be replaced
  with "N/A — <one-line reason>" rather than deleted.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/README.md
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/alert-code-taxonomy.md
  - codex/15-runbooks/alerting/threshold-tuning.md
---

# `<AlertCode>` Runbook

> **What this is:** the on-call operator's first stop when this alert fires. Read top-to-bottom on the page that comes
> up. Sections are ordered so the first 60 seconds (acknowledge + diagnose) are at the top, and the slow-burn pieces
> (post-mortem) are at the bottom.

## TL;DR

One paragraph: what the alert means in plain English, why we care, the single most important first action, and the
current default severity. Aim for ≤5 lines — the first thing a sleepy operator at 3am reads.

## Trigger condition

- **Code:** `<AlertCode>` (UAC closed-set, see [`alert-code-taxonomy.md`](./alert-code-taxonomy.md)).
- **Pattern (fnmatch):** `<exact pattern from LIVE_ALERT_RULES>`.
- **Threshold key:** `<threshold_key from ALERT_THRESHOLDS or N/A>`.
- **Default value:** `<value + unit>` — see [`threshold-tuning.md`](./threshold-tuning.md) for citation + per-archetype
  overrides.
- **Emitter(s):** `<service name(s) that publish this code>`.
- **Upstream signal:** What metric / event / state change drives the firing condition.
- **De-dup window:** `<seconds>`.

## Severity + paging

- **Severity:** `<CRITICAL | HIGH | WARN | INFO>` (UAC `AlertSeverity`).
- **Paging channels:** `<PAGERDUTY, TELEGRAM, SLACK, EMAIL, LOG_ONLY>`.
- **Triggers kill-switch:** `<true | false>`.
- **PagerDuty service:** `uts-prod-live-trading` (1st-tier Ikenna → 2nd-tier Harsh, 30-min auto-escalate).

## Diagnosis (first 5 minutes)

1. **Acknowledge the page** within 5 minutes. PagerDuty auto-escalates if missed.
2. **Pull alert payload** via DART or PubSub:
   ```bash
   gcloud pubsub subscriptions pull projects/${PROJECT_ID}/subscriptions/alerting-service-defi-alerts \
     --auto-ack --limit=1 --format=json | jq '.[].message.data | @base64d | fromjson'
   ```
3. **Inspect the emitter VM** via gcloud:
   ```bash
   gcloud compute instances describe <vm-name> --zone=asia-northeast1-c --format=json \
     | jq '{status, lastStartTimestamp, serviceAccounts}'
   ```
4. **Tail emitter's structured events:**
   ```bash
   LATEST=$(gcloud storage ls gs://${PROJECT_ID}-events/events/<service>/$(date -u +%Y-%m-%d)/<vm-name>/ \
     | tail -1)
   gcloud storage cat "${LATEST}*.jsonl" | tail -5 | jq '.event, .metadata.details'
   ```
5. **Check correlated codes** — search for related family in
   `gs://${PROJECT_ID}-events/events/alerting-service/$(date -u +%Y-%m-%d)/`.

## Resolution paths

### Path 1 — Auto-recovery (preferred)

What auto-recovery loop exists. Watching command:

```bash
<command>
```

**Success:** `<observable>`.

### Path 2 — Manual intervention (safe)

1. `<command 1>` — what it does.
2. `<command 2>` — same.
3. Verify resolution: `<command>`.

**Success:** `<observable>`.

### Path 3 — Kill-switch / halt (last resort)

```bash
<dart link or kill-switch publish command>
```

**Success:** `<observable>`.

## Rollback

- **Undoing Path 2 step N:** `<command>`.
- **Undoing kill-switch:** see [`kill_switch_defi_liquidation_risk.md`](./kill_switch_defi_liquidation_risk.md).

## Common false-positives

- **`<scenario>`:** what it looks like + operator action.

If FP rate exceeds 5% per 24h sustained, raise via [`threshold-tuning.md`](./threshold-tuning.md).

## Escalation criteria + targets

Escalate immediately when ANY of:

- `<criterion 1>`.
- `<criterion 2>`.

Targets:

- **Tier 1 (primary):** Ikenna (Telegram + PagerDuty).
- **Tier 2 (secondary):** Harsh (Telegram + PagerDuty 30-min auto-escalate).
- **Tier 3 (strategy lead):** Operator-defined.
- **Tier 4 (custody):** Operator-defined; >250k USD at risk only.

## Success criteria

- Trigger condition no longer satisfied.
- DART Active Alerts shows alert `acknowledged` or `resolved`.
- No re-fire within de-dup window.
- Post-incident write-up filed for any P0/P1 escalation.

## Post-incident

For any CRITICAL or HIGH true-positive: file write-up within 24h in
`unified-trading-pm/plans/active/issues/incident_<YYYY_MM_DD>_<short-name>.md`.

## Cross-references

- **AlertCode taxonomy:** [`alert-code-taxonomy.md`](./alert-code-taxonomy.md).
- **Threshold rationale:** [`threshold-tuning.md`](./threshold-tuning.md).
- **Operator playbook (high-level):** [`operator-playbook.md`](./operator-playbook.md).
- **Rehearsal procedure:** [`rehearsal-procedure.md`](./rehearsal-procedure.md).
- **Implementing plan:**
  [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
- **DART:** [DART playbook](../dart/).
- **UAC SSOT:** `unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/`.
