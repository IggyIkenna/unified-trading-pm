---
title: Alert Code Taxonomy
status: active
created: 2026-05-07
updated: 2026-05-07
authoritative_for: The UAC `AlertCode` StrEnum SSOT — the closed set of alert codes the alerting-service may emit. Each code maps to a stable operator runbook entry, threshold owner, and severity. Phase 1 shipped UAC@d00326d; Phase 2 (alerting-service consumption) shipped alerting-service@b025e83.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.plan.md
related:
  - codex/14-playbooks/alerting/operator-playbook.md
  - codex/14-playbooks/alerting/threshold-tuning.md
  - codex/05-infrastructure/live-deployment-monitoring.md
---

# Alert Code Taxonomy

> **Status:** ACTIVE — Phase 1 (UAC SSOT) shipped 2026-05-07 at UAC@d00326d. Phase 2
> (alerting-service consumption) shipped 2026-05-07 at alerting-service@b025e83. Phase 7 (quietness
> baseline) + Phase 8 (rehearsal) remaining before May-23 go-live.

## Purpose

Every alert raised by the alerting-service carries a stable, machine-readable `AlertCode`. This doc is the SSOT for
what the closed-set values are, what each means, and which severity tier they fall into. Operator runbooks key off
these codes; threshold tuning is filed against these codes.

## Where it lives

The `AlertCode` enum + supporting types live in
[`unified_api_contracts.canonical.crosscutting.alerting`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/),
re-exported through both:

- The top-level facade — `from unified_api_contracts import AlertCode, ...` (preferred for consumer
  services per UAC import-surface rules).
- A dedicated facade — `from unified_api_contracts.alerting import AlertCode, ...`.

Sources:

- [`codes.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/codes.py)
  — `AlertCode` (StrEnum, closed set) + `AlertSeverity` (CRITICAL/HIGH/WARN/INFO) + `AlertChannel`
  (PAGERDUTY/TELEGRAM/SLACK/EMAIL/LOG_ONLY) + `ALERT_CODES` frozenset.
- [`thresholds.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/thresholds.py)
  — `AlertThreshold` dataclass + `ThresholdUnit` (BPS_OF_ONE/RATIO/USD/MINUTES/COUNT_PER_MINUTE) +
  `ALERT_THRESHOLDS` dict.
- [`rules.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py)
  — `AlertRule` Pydantic model + `LIVE_ALERT_RULES` tuple. `to_routing_dict()` renders the legacy
  `(event_pattern, channels, severity_filter)` shape consumed by alerting-service.

## Severity tiers

| Severity   | Legacy filter | Paging behaviour                                   |
| ---------- | ------------- | -------------------------------------------------- |
| `CRITICAL` | `"critical"`  | PagerDuty P1 page + Telegram + 24/7 SLA.           |
| `HIGH`     | `"warning"`   | PagerDuty P2 + Telegram, business-hours SLA OK.    |
| `WARN`     | `None`        | Telegram only, no page.                            |
| `INFO`     | `None`        | Log / dashboard signal, no notification.           |

`AlertSeverity.to_legacy_filter()` maps to the legacy `severity_filter` field consumed by the
notifier dispatchers (Telegram / PagerDuty / Slack / Email). When DART (Phase 5) ships, dispatchers
will consume `AlertSeverity` directly and the legacy filter mapping can be deleted.

## Closed set (39 codes as of 2026-05-07)

Adding a new code requires:

1. Append to `AlertCode` in `codes.py`.
2. Add an `AlertRule` to `LIVE_ALERT_RULES` in `rules.py` (or extend an existing wildcard rule's
   pattern coverage).
3. Author the operator playbook entry under [`operator-playbook.md`](./operator-playbook.md).
4. Include the code in the next quarterly rehearsal scope
   ([`rehearsal-procedure.md`](./rehearsal-procedure.md)).

The closed-set sanity test `tests/internal/unit/test_alerting_taxonomy.py` enforces (1) ↔ (2):
every `AlertRule.pattern` must match at least one `AlertCode` member.

### Categories

- **Kill-switch family (`KILL_SWITCH_*`)** — three codes: `KILL_SWITCH_DEFI_LIQUIDATION_RISK`,
  `KILL_SWITCH_PORTFOLIO_DRAWDOWN`, `KILL_SWITCH_VENUE_DISCONNECT`. All `triggers_kill_switch=True`,
  all CRITICAL + PagerDuty + Telegram.
- **Circuit-breaker (`CIRCUIT_BREAKER_*`)** — `OPEN` (CRITICAL), `BACKOFF_ESCALATING` (HIGH),
  `DEGRADED` / `CLOSED` (WARN).
- **DeFi-specific (`DEFI_*`)** — health-factor / weETH-depeg / aave-utilization-spike /
  funding-rate-flip / feature-stale / position-liquidated / rate-deviation / tx-simulation-failed.
  Severity varies; thresholds anchored in UAC `ALERT_THRESHOLDS`.
- **Margin ladder (`MARGIN_*`)** — `LIQUIDATION` / `CRITICAL` (CRITICAL), `WARNING` /
  `THRESHOLD_BREACH` (HIGH). Thresholds come from UAC `LIQUIDATION_PARAMS_REGISTRY` (PBM
  canonical).
- **Position / reconciliation** — `POSITION_DRIFT` / `POSITION_DRIFT_DETECTED` /
  `POSITION_CRITICAL_DISCREPANCY` / `POSITION_CORRECTION_DISPATCHED` /
  `PORTFOLIO_REBALANCE_TRIGGERED` / `BALANCE_DRIFT` / `RECON_DEGRADED` / `RECON_DEGRADED_CLOSE`.
- **Order / execution** — `ORDER_REJECTION_SPIKE` / `ORDER_ORPHANED` / `ORDER_RECOVERY_INITIATED` /
  `ORDER_RECOVERY_COMPLETED` / `ORDER_RECOVERY_FAILED` (CRITICAL).
- **Multi-leg execution risk** — `UNHEDGED_POSITION_ALERT` / `MULTI_LEG_COMPENSATION_FAILED` /
  `DUAL_FAILURE_DETECTED` (all CRITICAL).
- **Service health** — `SERVICE_ERROR` / `SERVICE_ERROR_CRITICAL` / `SERVICE_DEGRADED` /
  `PREFLIGHT_FAILED`.
- **Cross-cloud safety net** — `CROSS_CLOUD_EGRESS_DETECTED` (HIGH, audit 2026-05-07
  §dual-cloud-active). Threshold:
  `cross_cloud_egress_bytes_per_request` = 1 MiB.

## Construction-time validation

`AlertRule` Pydantic validators raise:

- `UnknownAlertCodeError` when a `pattern` matches no `AlertCode` member (rule is dead, would never
  fire).
- `UnknownThresholdKeyError` when `threshold_key` is not in `ALERT_THRESHOLDS`.
- A plain `ValueError` when `triggers_kill_switch=True` is set on a non-`KILL_SWITCH_*` code, or
  when `pattern` / `channels` is empty.

Pydantic v2 wraps these in `ValidationError` for downstream consumers, but the typed-error classes
remain importable for direct programmatic use.

## Adding a new severity

`AlertSeverity` should not grow lightly — operators interpret severity vs paging-channel matrix
muscle-memory. If a new tier is needed (e.g. `OBSERVE` between `WARN` and `INFO`), update both
`AlertSeverity` AND `AlertSeverity.to_legacy_filter()` AND the dispatchers' severity-filter
expectation in `alerting-service/alerting_service/notifiers/`.

## Cross-references

- **Plan(s) implementing this:**
  [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.plan.md).
- **Related codex SSOTs:** [`operator-playbook`](./operator-playbook.md),
  [`threshold-tuning`](./threshold-tuning.md),
  [`rehearsal-procedure`](./rehearsal-procedure.md),
  [`live-deployment-monitoring`](../../05-infrastructure/live-deployment-monitoring.md).
- **Code:** UAC `unified_api_contracts.canonical.crosscutting.alerting.AlertCode` (top-level
  facade `unified_api_contracts.AlertCode`).

## Open questions

- Do we treat data-pipeline alerts (e.g. backfill stalled) as the same severity tier as trading
  alerts (e.g. risk-limit breached)? Currently no data-pipeline-specific codes exist; recommend
  adding under a `DATA_PIPELINE_*` category in v2 with `WARN` defaults.
- Should custody-related alerts (Copper/CEFFU webhook stale) be PAGE-by-default given May-23 live
  trading scope? Currently no custody codes — to be added in Phase 3 producer migration when
  position-balance-monitor wires custody monitoring.
- How do we handle alerts that need different severity per-archetype (e.g. funding-arb stall is
  PAGE, sports tip-stall is WARNING)? Threshold per-archetype overrides exist; severity per-archetype
  doesn't yet — requires extending `AlertRule` or duplicating rules per-archetype. DEFERRED until
  Phase 7 quietness baseline surfaces real-world need.
