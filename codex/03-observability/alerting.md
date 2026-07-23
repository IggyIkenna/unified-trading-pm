---
doc_type: codex-ssot
title: Alerting
summary:
  "Alerting SSOT: every autonomous recovery action must alert (nothing silent) — delivery via Telegram (primary) /
  PagerDuty (critical) / Twilio voice+SMS (permanent Layer-3 fallback); Slack deprecated. Full autonomous-recovery
  alert-tier matrix (T1 CRITICAL–T4 INFO) + Incident Gateway routing; routing rules are UAC-driven (~56 AlertRule
  entries), first-match-wins with a * fallback."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, deployment-service, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [alerting, escalation, monitoring, self-healing, observability, live-trading]
related:
  [
    /codex/03-observability/data-feed-sla-registry.md,
    /codex/03-observability/lifecycle-events.md,
    /codex/03-observability/coordination-events.md,
    /codex/04-architecture/autonomous-recovery-matrix.md,
    /codex/04-architecture/incident-gateway-state-machine.md,
  ]
created: 2026-03-27
authoritative_for: [autonomous-recovery alert matrix, alert delivery channels]
referenced_by:
  [
    /codex/03-observability/coordination-events.md,
    /codex/03-observability/data-feed-sla-registry.md,
    /codex/03-observability/lifecycle-events.md,
    /codex/03-observability/monitoring-control-plane.md,
    /codex/03-observability/slos.md,
    /codex/04-architecture/dependency-health-policy.md,
    /codex/04-architecture/incident-gateway-state-machine.md,
    /codex/04-architecture/kill-switch-event-bus.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Alerting

## Principle

**Every autonomous recovery action MUST generate an alert.** Autonomous recovery is by definition unusual — the system
is self-healing because something broke. Even if recovery succeeds, the operator must know it happened. Different
severities route to different channels, but nothing is silent.

Alert delivery channels: **Telegram** (primary, all alerts), **PagerDuty** (critical trading events), and **Twilio
voice/SMS** (permanent Layer-3 fallback — survives PagerDuty API outage + phone-on-DND). Slack is deprecated.

> **Incident Gateway (2026-05-23)**: all alerts now flow through the central `alerting-service` Incident Gateway as
> structured `IncidentEnvelope` events with 13-state lifecycle tracking, dedup-key storm collapse, and 6h audit-ack
> queue. See `/codex/04-architecture/incident-gateway-state-machine.md` for the SSOT. The 5-layer defence-in-depth model
> (Layer-0 scripts → Layer-1 LLM agent → Layer-2 PagerDuty → Layer-3 Twilio → Layer-4 physical pager) is in
> `/codex/04-architecture/recovery-defence-in-depth-layers.md`.

> **🟡 SLACK DEPRECATION RECONCILIATION (AL-6 PRE_CUTOVER 2026-05-12, slot 8 audit)** — this doc declares Slack
> deprecated; downstream references still treating Slack as a live channel are tracked for follow-up: (a)
> `/codex/04-architecture/alerting-batch-live.md:18` lists "PagerDuty / Telegram / Slack"; (b)
> `/codex/15-runbooks/alerting/operator-playbook.md:48` references "pinned in the Slack channel"; (c)
> `/codex/15-runbooks/alerting/alert-code-taxonomy.md:189-190` ML routing matrix lists SLACK as a live channel; (d)
> code: `AlertChannel.SLACK` exists in `codes.py:271`; `alerting-service/notifiers/slack.py` + sibling modules still
> ship. Operator-declared direction: Telegram + PagerDuty only. Code-removal + ML-routing updates routed to
> alerting-service maintainer (cross-ref slot 8 ALERTING AL-6 PRE_CUTOVER follow-up).

---

## Alert Severity Tiers

> **Severity vocabulary SSOT** — see
> [`15-runbooks/alerting/README.md` § Severity glossary](/codex/15-runbooks/alerting/README.md#severity-glossary) for
> the canonical mapping between the UAC `AlertSeverity` codex enum (CRITICAL / HIGH / WARN / INFO), PagerDuty incident
> priorities (P0 / P1 / P2 / P3), time-to-ack targets, routing channels, and worked examples. The tier labels used in
> the recovery matrix below (`T1 CRITICAL` / `T2 HIGH` / `T3 WARNING` / `T4 INFO`) are display aliases for the codex
> enum members of the same name.

`T3 WARNING` in the matrix below corresponds to `AlertSeverity.WARN` in code (the codex enum spells it `WARN`, not
`WARNING`). All other display names match the enum.

---

## Autonomous Recovery Alert Matrix

Every autonomous recovery action the system takes, mapped to its alert tier:

### Retry & Reconnection (T3-T4)

| Event                               | Severity   | Alert                | Why                                    |
| ----------------------------------- | ---------- | -------------------- | -------------------------------------- |
| First retry on transient error      | T4 INFO    | Telegram             | Normal, but operator should see volume |
| Retry exhausted (3 attempts failed) | T3 WARNING | Telegram             | Error persisted through retries        |
| Reconnection attempt                | T3 WARNING | Telegram             | Connection was lost                    |
| Reconnection succeeded              | T4 INFO    | Telegram             | Recovery confirmation                  |
| Reconnection failed                 | T2 HIGH    | PagerDuty + Telegram | Venue unreachable                      |

### Circuit Breaker (T2-T1)

| Event                         | Severity    | Alert                       | Why                                         |
| ----------------------------- | ----------- | --------------------------- | ------------------------------------------- |
| DEGRADED (30% failure rate)   | T3 WARNING  | Telegram                    | Venue health declining, throttling orders   |
| OPEN (60% failure rate)       | T1 CRITICAL | PagerDuty P1 + Telegram     | Venue blocked, orders queued                |
| BACKOFF_ESCALATED (cycle > 1) | T2 HIGH     | PagerDuty P2 + Telegram     | Recovery failing repeatedly                 |
| HALF_OPEN probe               | T4 INFO     | Telegram                    | Testing recovery                            |
| CLOSED (recovery)             | T3 WARNING  | Telegram                    | Recovery confirmed — operator should review |
| ORDER_THROTTLED               | T4 INFO     | Telegram (suppressed >10/s) | Individual order dropped                    |

### Multi-Venue Cascade (T1)

| Event                           | Severity    | Alert                   | Why                             |
| ------------------------------- | ----------- | ----------------------- | ------------------------------- |
| >50% venues OPEN for a strategy | T1 CRITICAL | PagerDuty P1 + Telegram | Auto STOP_NEW_ONLY activated    |
| All venues OPEN                 | T1 CRITICAL | PagerDuty P1 + Telegram | Firm-wide kill switch activated |

### Kill Switch (T1)

| Event                        | Severity    | Alert                   | Why                                     |
| ---------------------------- | ----------- | ----------------------- | --------------------------------------- |
| KILL_SWITCH_ACTIVATED        | T1 CRITICAL | PagerDuty P1 + Telegram | All trading halted                      |
| KILL_SWITCH_DEACTIVATED      | T3 WARNING  | Telegram                | Trading resumed                         |
| KILL_SWITCH_AUTO_DEACTIVATED | T2 HIGH     | PagerDuty P2 + Telegram | Timer expired, trading auto-resumed     |
| KILL_SWITCH_BLOCKED_STARTUP  | T1 CRITICAL | PagerDuty P1 + Telegram | Service started with active kill switch |

### Multi-Leg Compensation (T1-T2)

| Event                         | Severity    | Alert                   | Why                                               |
| ----------------------------- | ----------- | ----------------------- | ------------------------------------------------- |
| UNHEDGED_POSITION_ALERT       | T1 CRITICAL | PagerDuty P1 + Telegram | Partial fill, compensation attempting             |
| Compensation trade succeeded  | T2 HIGH     | PagerDuty P2 + Telegram | Position unwound, but incident occurred           |
| MULTI_LEG_COMPENSATION_FAILED | T1 CRITICAL | PagerDuty P1 + Telegram | Unhedged position exists, circuit breaker tripped |

### Position Drift (T2-T1)

| Event                              | Severity    | Alert                   | Why                           |
| ---------------------------------- | ----------- | ----------------------- | ----------------------------- |
| POSITION_DRIFT_DETECTED (WARNING)  | T3 WARNING  | Telegram                | Drift 2-5%, monitoring        |
| POSITION_DRIFT_DETECTED (CRITICAL) | T1 CRITICAL | PagerDuty P1 + Telegram | Drift >5%, auto STOP_NEW_ONLY |

### Health Factor / Margin (T2-T1)

| Event                 | Severity    | Alert                   | Why                         |
| --------------------- | ----------- | ----------------------- | --------------------------- |
| HF 1.5-2.0 (ELEVATED) | T3 WARNING  | Telegram                | Strategy reducing exposure  |
| HF 1.2-1.5 (WARNING)  | T2 HIGH     | PagerDuty P2 + Telegram | Strategy paused new entries |
| HF 1.0-1.2 (CRITICAL) | T1 CRITICAL | PagerDuty P1 + Telegram | Auto-deleverage triggered   |
| HF < 1.0 (EMERGENCY)  | T1 CRITICAL | PagerDuty P1 + Telegram | Emergency close all         |

### Reconciliation (T2-T1)

| Event                                | Severity    | Alert                   | Why                               |
| ------------------------------------ | ----------- | ----------------------- | --------------------------------- |
| Reconciliation break detected        | T3 WARNING  | Telegram                | Operator should investigate       |
| RECON_DEGRADED close (closing blind) | T2 HIGH     | PagerDuty P2 + Telegram | Closing without verified state    |
| DUAL_FAILURE_DETECTED                | T1 CRITICAL | PagerDuty P1 + Telegram | Can't reconcile AND can't execute |

### Order Recovery (T2-T3)

| Event                    | Severity    | Alert                   | Why                                  |
| ------------------------ | ----------- | ----------------------- | ------------------------------------ |
| ORDER_RECOVERY_INITIATED | T3 WARNING  | Telegram                | Startup scanning for orphaned orders |
| ORDER_ORPHANED           | T2 HIGH     | PagerDuty P2 + Telegram | Found order not in our state         |
| ORDER_RECOVERY_COMPLETED | T4 INFO     | Telegram                | Recovery finished                    |
| ORDER_RECOVERY_FAILED    | T1 CRITICAL | PagerDuty P1 + Telegram | Could not resolve orphaned orders    |

---

## One freshness home — `tick_staleness_seconds` cross-validation (2026-06-20)

`ALERT_THRESHOLDS["tick_staleness_seconds"]` in `unified_api_contracts/canonical/crosscutting/alerting/thresholds.py` is
the coarse alerting floor for tick-staleness alerts (default 300 s). The per-venue freshness thresholds that govern
whether a specific feed is actually stale live in `MARKET_TICK_FRESHNESS` inside
`unified_api_contracts/internal/reference/data_freshness.py` — the feed-SLA registry SSOT
(`/codex/03-observability/data-feed-sla-registry.md`).

The two values are **cross-validated, not import-time-derived** (import-time derivation would create an
alerting↔reference circular import). The enforcement is the CI test:

```
unified-api-contracts/tests/internal/unit/test_freshness_ssot_agreement.py
```

This test asserts `ALERT_THRESHOLDS["tick_staleness_seconds"]` ≥ strictest real-time per-venue `max_age_seconds` in
`MARKET_TICK_FRESHNESS` and pins the 300 s regression guard. Any change that makes the alert threshold stricter than the
per-venue contract fails CI immediately. Never change `tick_staleness_seconds` without also verifying the per-venue
contracts are consistent — the test is the single enforcement point.

---

## Alerting-Service Routing Rules

> **SSOT note (AL-3 reconciliation 2026-05-12).** Routing rules are **UAC-driven**, not an inline python block in this
> codex doc. The runtime loads `[rule.to_routing_dict() for rule in LIVE_ALERT_RULES]` from `alerting_service/config.py`
> (line 12-34), where `LIVE_ALERT_RULES` lives in UAC `unified_api_contracts/canonical/crosscutting/alerting/rules.py`
> and ships **~56 `AlertRule(...)` entries** spanning kill-switch / circuit-breaker / ML / risk-rule-consequence /
> kill-switch-recovery / tick-staleness / connectivity-gap / DeFi / margin / position-recon / order-recovery / multi-leg
> / service-health / cross-cloud-egress codes. Operator overrides flow via `AlertingSystemConfig.routing_rules`. The
> closed AlertCode set is governed in
> [`/codex/15-runbooks/alerting/alert-code-taxonomy.md`](/codex/15-runbooks/alerting/alert-code-taxonomy.md); the
> [`AlertRule._validate_kill_switch_scope_matches_code_family`](/codex/15-runbooks/alerting/alert-code-taxonomy.md#construction-time-validation)
> validator enforces per-rule consistency.
>
> Routing-rule philosophy (preserved verbatim): **first-match-wins** on `event_pattern` glob, with a `*` fallback
> guaranteeing nothing is silent. T1 CRITICAL → PagerDuty P1 + Telegram; T2 HIGH → PagerDuty P2 + Telegram; T3 WARN →
> Telegram only; T4 INFO → Telegram fallback. The per-code routing matrix lives in UAC `LIVE_ALERT_RULES` — see the
> per-code playbook entries in `15-runbooks/alerting/operator-playbook.md` rather than re-deriving here.

---

## Infrastructure Alerts

| Alert           | Trigger                        | Detection                                                                                                                                                      | Response                  | Status      |
| --------------- | ------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | ----------- |
| OOM Death Loop  | Serial log OOM >= 5 times      | deployment-service VM watchdog + `vm-exec-with-gcs-tee.sh` serial-log scrape (AL-9 PRE_CUTOVER 2026-05-12 refresh; "UTD v2" naming retired per Ops audit O-13) | VM terminated             | IMPLEMENTED |
| Startup Timeout | No SERVICE_STARTED after 5 min | deployment-service VM watchdog + event-stream STARTED check (AL-9 PRE_CUTOVER 2026-05-12 refresh)                                                              | VM terminated             | IMPLEMENTED |
| Memory Critical | memory_percent > 90%           | PerformanceMonitor (30s)                                                                                                                                       | Log ERROR, resource_alert | IMPLEMENTED |
| Memory Warning  | memory_percent > 85%           | PerformanceMonitor (30s)                                                                                                                                       | Log WARNING               | IMPLEMENTED |

## Pipeline Alerts

| Alert             | Trigger                  | Detection       | Response                     | Status      |
| ----------------- | ------------------------ | --------------- | ---------------------------- | ----------- |
| Service Failed    | FAILED event             | Event parser    | Shard state failed, Telegram | IMPLEMENTED |
| Stage Timeout     | No STOPPED within 30 min | Time comparison | Investigation alert          | IMPLEMENTED |
| Validation Failed | VALIDATION_FAILED event  | Event parser    | Check upstream deps          | IMPLEMENTED |

## Live Trading Alerts

| Alert                | Trigger                | Detection               | Response                | Status      |
| -------------------- | ---------------------- | ----------------------- | ----------------------- | ----------- |
| Position Drift       | Deviation > threshold  | PBMS background loop    | Telegram + PagerDuty    | IMPLEMENTED |
| Circuit Breaker Trip | Failure rate > 60%     | Per-venue state machine | PagerDuty P1 + Telegram | IMPLEMENTED |
| Kill Switch          | Manual or automatic    | Execution-service       | PagerDuty P1 + Telegram | IMPLEMENTED |
| Unhedged Position    | Multi-leg partial fill | Compensation handler    | PagerDuty P1 + Telegram | IMPLEMENTED |
| Dual Failure         | Recon + exec both down | PBMS health check       | PagerDuty P1 + Telegram | PLANNED     |
| Margin Emergency     | HF < 1.0               | PBMS margin monitor     | PagerDuty P1 + Telegram | IMPLEMENTED |

---

## Alert Flow Architecture

```
Event Sources (execution-service, PBMS, strategy-service, etc.)
  |
  |-- log_event("EVENT_NAME", severity="...", details={...})
  |
  v
Pub/Sub topic: lifecycle-events
  |
  v
alerting-service (subscriber + Incident Gateway)
  |
  |-- Wrap legacy alert into IncidentEnvelope (envelope_adapter)
  |-- Incident dedup by stable incident_key (hash over service+component+problem_type+venue+strategy)
  |-- State machine transition (DETECTED → AUTO_ACTION_STARTED → ... → RESOLVED)
  |-- Route: match event_pattern against routing rules (first match wins)
  |-- Deliver to matched channels:
  |     |
  |     +-- Telegram (HTML format, bot API)
  |     +-- PagerDuty (Events API v2, severity mapped)
  |     +-- Twilio Voice (Layer-3 fallback — fires on SEV0 + when PagerDuty probe fails)
  |     +-- Twilio SMS  (Layer-3 fallback — parallel with voice)
  |
  |-- Persist IncidentEnvelope + AgentActionEvent to GCS audit-store (1yr retention)
  |-- Persist AlertDeliveryRecord to GCS (audit trail)
  |
  v
Operator sees alert in Telegram / PagerDuty / Twilio voice / DART Safety Ops tab
```

---

## Configuration

| Parameter                             | Default        | Description                                    |
| ------------------------------------- | -------------- | ---------------------------------------------- |
| Telegram bot token                    | Secret Manager | Primary alert channel                          |
| Telegram chat ID                      | Secret Manager | Target chat for alerts                         |
| PagerDuty routing key                 | Secret Manager | For critical trading events                    |
| `alerting-twilio-account-sid`         | Secret Manager | Twilio Account SID (Layer-3 fallback)          |
| `alerting-twilio-auth-token`          | Secret Manager | Twilio auth token — NEVER log in URL or stdout |
| `alerting-twilio-from-number`         | Secret Manager | Twilio caller number                           |
| `alerting-twilio-to-number-primary`   | Secret Manager | Ikenna mobile (primary)                        |
| `alerting-twilio-to-number-secondary` | Secret Manager | Harsh mobile (secondary)                       |
| `alerting-twilio-to-number-founder`   | Secret Manager | Founder escalation number                      |
| Alert dedup TTL                       | 60s            | Suppress duplicate events                      |
| OOM kill threshold                    | 5              | OOM patterns before VM termination             |
| Startup timeout                       | 300s           | Seconds before startup timeout                 |

---

## CI-bot Telegram contract (AL-12 — added 2026-05-13)

Workspace-CI delivery to operators runs through a dedicated Telegram bot, **separate from the alerting-service runtime
delivery surface above**. Documenting the contract here so agents don't conflate the two channels.

**Trigger:** every `git push` to a branch that triggers remote CI (pushes to `main` + PRs targeting `main`). Pushes to
`live-defi-rollout` and other `feat/*` branches DO NOT trigger remote CI — quality is enforced locally via
`bash scripts/quality-gates.sh` before push.

**Payload contract:** the CI bot reports the underlying repo's QG status, not its own delivery result.

| `client_payload.status` | Telegram severity | Body shape                                                                        |
| ----------------------- | ----------------- | --------------------------------------------------------------------------------- |
| `FAILING`               | ❌ `CRITICAL`     | Failure excerpt inline (last 30 lines QG output, ANSI-stripped, in `<pre>` block) |
| anything else           | ✅ `INFO`         | Repo + commit + status summary                                                    |

**Operator response cadence:** CI failures on `live-defi-rollout` and `main` are NOT issues to flag — fix in real time.
Red CI on `live-defi-rollout` blocks workspace.

**Watcher pattern:** after a CI-triggering push, set up a background watcher (sub-agent OR `ScheduleWakeup` ~3-5min
after push) checking `gh run list --branch <branch> --repo <owner>/<repo> --limit 5`. Continue with other work; react
asynchronously.

**Diagnosis on fail:** `gh run view <run-id> --log-failed --repo <owner>/<repo>` (NOT local re-run; only run
quality-gates locally on the SPECIFIC files in your diff).

**SSOT for the rule:** workspace `CLAUDE.md` § "CI Verification After Every Push (HARD RULE)". The § above mirrors the
contract for cross-agent discoverability inside the codex (per AL-12
codex_doc_currency_and_consolidation_post_cutover_2026_05_12 Sweep 3).

---

## Related

- `03-observability/data-feed-sla-registry.md` — feed-SLA SSOT (`DataFreshnessContract` / `ALL_FRESHNESS_CONTRACTS`);
  one freshness home; `refetch_action` binding
- `04-architecture/autonomous-recovery-matrix.md` — full decision tree for failure scenarios
- `04-architecture/kill-switch-circuit-breaker.md` — kill switch and circuit breaker mechanics
- `04-architecture/recovery-defence-in-depth-layers.md` — **NEW 2026-05-23** the 5+1 layer recovery model (Layer-0
  deterministic Python → Layer-1 LLM audit/signoff → Layer-2 PagerDuty cascade → Layer-3 Twilio voice → Layer-4 physical
  pager → Layer-5 human audit ack)
- `04-architecture/incident-gateway-state-machine.md` — **NEW 2026-05-23** 13-state incident lifecycle + dedup-key +
  audit-ack queue
- `15-runbooks/physical-pager-layer.md` — **NEW 2026-05-23** Layer-4 device comparison + webhook prototype
- `15-runbooks/alerting/audit-acknowledgement-flow.md` — **NEW 2026-05-23** Layer-5 ack SLA + escalation ladder
- `05-infrastructure/disaster-recovery.md` — RTO/RPO targets + Tier 0-3 recovery
- `03-observability/lifecycle-events.md` — mandatory event sequences
- `03-observability/coordination-events.md` — service-to-service event wiring
