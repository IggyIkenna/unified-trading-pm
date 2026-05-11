---
title: Alert Code Taxonomy
status: active
created: 2026-05-07
updated: 2026-05-07
authoritative_for:
  The UAC `AlertCode` StrEnum SSOT — the closed set of alert codes the alerting-service may emit. Each code maps to a
  stable operator runbook entry, threshold owner, and severity. Phase 1 shipped UAC@d00326d; Phase 2 (alerting-service
  consumption) shipped alerting-service@b025e83.
referenced_by:
  - plans/active/alerting_service_live_rules_2026_05_07.md
related:
  - codex/15-runbooks/alerting/operator-playbook.md
  - codex/15-runbooks/alerting/threshold-tuning.md
  - codex/05-infrastructure/live-deployment-monitoring.md
---

# Alert Code Taxonomy

> **Status:** ACTIVE — Phase 1 (UAC SSOT) shipped 2026-05-07 at UAC@d00326d. Phase 2 (alerting-service consumption)
> shipped 2026-05-07 at alerting-service@b025e83. Phase 7 (quietness baseline) + Phase 8 (rehearsal) remaining before
> May-23 go-live.

## Purpose

Every alert raised by the alerting-service carries a stable, machine-readable `AlertCode`. This doc is the SSOT for what
the closed-set values are, what each means, and which severity tier they fall into. Operator runbooks key off these
codes; threshold tuning is filed against these codes.

## Where it lives

The `AlertCode` enum + supporting types live in
[`unified_api_contracts.canonical.crosscutting.alerting`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/),
re-exported through both:

- The top-level facade — `from unified_api_contracts import AlertCode, ...` (preferred for consumer services per UAC
  import-surface rules).
- A dedicated facade — `from unified_api_contracts.alerting import AlertCode, ...`.

Sources:

- [`codes.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/codes.py) —
  `AlertCode` (StrEnum, closed set) + `AlertSeverity` (CRITICAL/HIGH/WARN/INFO) + `AlertChannel`
  (PAGERDUTY/TELEGRAM/SLACK/EMAIL/LOG_ONLY) + `ALERT_CODES` frozenset.
- [`thresholds.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/thresholds.py)
  — `AlertThreshold` dataclass + `ThresholdUnit` (BPS_OF_ONE/RATIO/USD/MINUTES/COUNT_PER_MINUTE) + `ALERT_THRESHOLDS`
  dict.
- [`rules.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py) —
  `AlertRule` Pydantic model + `LIVE_ALERT_RULES` tuple. `to_routing_dict()` renders the legacy
  `(event_pattern, channels, severity_filter)` shape consumed by alerting-service.

## Severity tiers

| Severity   | Legacy filter | Paging behaviour                                |
| ---------- | ------------- | ----------------------------------------------- |
| `CRITICAL` | `"critical"`  | PagerDuty P1 page + Telegram + 24/7 SLA.        |
| `HIGH`     | `"warning"`   | PagerDuty P2 + Telegram, business-hours SLA OK. |
| `WARN`     | `None`        | Telegram only, no page.                         |
| `INFO`     | `None`        | Log / dashboard signal, no notification.        |

`AlertSeverity.to_legacy_filter()` maps to the legacy `severity_filter` field consumed by the notifier dispatchers
(Telegram / PagerDuty / Slack / Email). When DART (Phase 5) ships, dispatchers will consume `AlertSeverity` directly and
the legacy filter mapping can be deleted.

## Closed set (39 codes as of 2026-05-07)

Adding a new code requires:

1. Append to `AlertCode` in `codes.py`.
2. Add an `AlertRule` to `LIVE_ALERT_RULES` in `rules.py` (or extend an existing wildcard rule's pattern coverage).
3. Author the operator playbook entry under [`operator-playbook.md`](./operator-playbook.md).
4. Include the code in the next quarterly rehearsal scope ([`rehearsal-procedure.md`](./rehearsal-procedure.md)).

The closed-set sanity test `tests/internal/unit/test_alerting_taxonomy.py` enforces (1) ↔ (2): every
`AlertRule.event_pattern` must match at least one `AlertCode` member.

### Categories

- **Kill-switch family (`KILL_SWITCH_*`)** — three codes: `KILL_SWITCH_DEFI_LIQUIDATION_RISK`,
  `KILL_SWITCH_PORTFOLIO_DRAWDOWN`, `KILL_SWITCH_VENUE_DISCONNECT`. All `triggers_kill_switch=True`, all CRITICAL +
  PagerDuty + Telegram.
- **Circuit-breaker (`CIRCUIT_BREAKER_*`)** — `OPEN` (CRITICAL), `BACKOFF_ESCALATING` (HIGH), `DEGRADED` / `CLOSED`
  (WARN).
- **DeFi-specific (`DEFI_*`)** — health-factor / weETH-depeg / aave-utilization-spike / funding-rate-flip /
  feature-stale / position-liquidated / rate-deviation / tx-simulation-failed. Severity varies; thresholds anchored in
  UAC `ALERT_THRESHOLDS`.
- **Margin ladder (`MARGIN_*`)** — `LIQUIDATION` / `CRITICAL` (CRITICAL), `WARNING` / `THRESHOLD_BREACH` (HIGH).
  Thresholds come from UAC `LIQUIDATION_PARAMS_REGISTRY` (PBM canonical).
- **Position / reconciliation** — `POSITION_DRIFT` / `POSITION_DRIFT_DETECTED` / `POSITION_CRITICAL_DISCREPANCY` /
  `POSITION_CORRECTION_DISPATCHED` / `PORTFOLIO_REBALANCE_TRIGGERED` / `BALANCE_DRIFT` / `RECON_DEGRADED` /
  `RECON_DEGRADED_CLOSE`.
- **Order / execution** — `ORDER_REJECTION_SPIKE` / `ORDER_ORPHANED` / `ORDER_RECOVERY_INITIATED` /
  `ORDER_RECOVERY_COMPLETED` / `ORDER_RECOVERY_FAILED` (CRITICAL).
- **Multi-leg execution risk** — `UNHEDGED_POSITION_ALERT` / `MULTI_LEG_COMPENSATION_FAILED` / `DUAL_FAILURE_DETECTED`
  (all CRITICAL).
- **Service health** — `SERVICE_ERROR` / `SERVICE_ERROR_CRITICAL` / `SERVICE_DEGRADED` / `PREFLIGHT_FAILED`.
- **Cross-cloud safety net** — `CROSS_CLOUD_EGRESS_DETECTED` (HIGH, audit 2026-05-07 §dual-cloud-active). Threshold:
  `cross_cloud_egress_bytes_per_request` = 1 MiB.
- **ML lifecycle (`ML_*` + `KILL_SWITCH_ML_MODEL_FAILURE`)** — 6 codes added 2026-05-08 (cefi_ml_may_23_2026.epic Tab 5
  Item 6). See [ML category section](#ml-category--alert-codes--thresholds--killswitchscope-mapping) below for the
  per-code severity routing, threshold sources, and archetype-scope mapping.

## Construction-time validation

`AlertRule` Pydantic validators raise:

- `UnknownAlertCodeError` when an `event_pattern` matches no `AlertCode` member (rule is dead, would never fire).
- `UnknownThresholdKeyError` when `threshold_key` is not in `ALERT_THRESHOLDS`.
- A plain `ValueError` when `triggers_kill_switch=True` is set on a non-`KILL_SWITCH_*` code, or when `event_pattern` /
  `channels` is empty.

Pydantic v2 wraps these in `ValidationError` for downstream consumers, but the typed-error classes remain importable for
direct programmatic use.

## Kill-switch publisher hook semantics

When an `AlertCode` matching `KILL_SWITCH_*` fires through alerting-service `route_event`, the router emits a typed
`KillSwitchEvent` to the in-process `KillSwitchBus` (UTL `unified_trading_library.kill_switch`) **after channel
dispatch**. Subscribers (the live execution-service halt-pump in production, plus strategy-service +
position-balance-monitor in co-located deployments) consume the bus event and halt the correctly-scoped surface.

### When the hook fires

- After PagerDuty + Telegram dispatch completes (paging is the contract; halting is best-effort).
- Skipped in batch mode (`set_batch_mode(True)`) — kill-switch firing is a live-mode operational concern; batch replay
  records routing audit only.
- Skipped if the matching `AlertRule.triggers_kill_switch` is `False` (non-kill-switch code).
- Skipped with a loud `logger.warning` if the matching rule has `triggers_kill_switch=True` but `kill_switch_scope` is
  `None` — defensive against UAC field version-skew. Channel dispatch still succeeds.

### KillSwitchScope mapping per code

Per operator decision 2026-05-08 (recorded in
[`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md)
Migrated-issues §"Kill-switch publisher hook"):

| `AlertCode`                         | `KillSwitchScope` | scope_key source                                 |
| ----------------------------------- | ----------------- | ------------------------------------------------ |
| `KILL_SWITCH_DEFI_LIQUIDATION_RISK` | `GLOBAL`          | `None` (GLOBAL is platform-wide)                 |
| `KILL_SWITCH_PORTFOLIO_DRAWDOWN`    | `GLOBAL`          | `None`                                           |
| `KILL_SWITCH_VENUE_DISCONNECT`      | `VENUE`           | `details["venue"]` (alert payload field)         |
| `KILL_SWITCH_ML_MODEL_FAILURE`      | `ARCHETYPE`       | `details["archetype"]` (e.g. `cefi_carry_arb`)   |

Adding a new `KILL_SWITCH_*` code MUST also pick a `KillSwitchScope` and document it here. The
`AlertRule._validate_kill_switch_scope_matches_code_family` validator rejects construction without a scope on a
`KILL_SWITCH_*` code, and rejects a scope on any non-kill-switch code (closed-set discipline mirrors the
`triggers_kill_switch` validator).

### scope_key resolution

For non-`GLOBAL` scopes, the router resolves the scope_key from the alert `details` payload:

| scope        | `details` field |
| ------------ | --------------- |
| `VENUE`      | `venue`         |
| `CLIENT`     | `client_id`     |
| `STRATEGY`   | `strategy_id`   |
| `ARCHETYPE`  | `archetype`     |
| `INSTRUMENT` | `instrument_id` |

Missing field → log warning + fire with `scope_key=None` (over-broad halt is the safe default). Alert emitters MUST
populate the appropriate field; the operator playbook entry for each code documents the expected payload shape.

### Failure-mode contract

The publisher hook is **side-effect-free vs the channel dispatch**. If the bus publish raises (e.g. a subscriber
callback crashes, or an attribute-access bug in the rule lookup), the exception is swallowed + classified via UTL
`classify_and_emit_error` + emitted as `KILL_SWITCH_PUBLISH_FAILED` event. The `route_event` caller never sees the
exception. Rationale: paging on-call must always succeed (the human is the failsafe); a missed bus publish is
recoverable via operator manual DART trigger but a missed page is not.

`KillSwitchBus._deliver` itself catches subscriber callback exceptions — one bad subscriber does not abort delivery to
other subscribers. See UTL `tests/unit/test_kill_switch_bus.py` for the deliver-isolation guarantees.

## ML category — alert codes + thresholds + KillSwitchScope mapping

Added 2026-05-08 per `cefi_ml_may_23_2026.epic` Tab 5 Item 6 — pre-cutover surface for ML-model lifecycle observability.
6 codes total: 5 `ML_*` monitoring codes + 1 `KILL_SWITCH_ML_MODEL_FAILURE` halt code. All have closed-set sanity tests
in `tests/internal/unit/test_alerting_taxonomy.py` (Phase 1 SSOT enforcement).

### Per-code routing matrix

| AlertCode                       | Severity   | Channels                          | threshold_key                       | ThresholdUnit  | KillSwitchScope | scope_key source        |
| ------------------------------- | ---------- | --------------------------------- | ----------------------------------- | -------------- | --------------- | ----------------------- |
| `ML_MODEL_VERSION_MISMATCH`     | `CRITICAL` | PAGERDUTY + TELEGRAM              | `ml_model_version_mismatch_minutes` | `MINUTES`      | n/a             | n/a                     |
| `KILL_SWITCH_ML_MODEL_FAILURE`  | `CRITICAL` | PAGERDUTY + TELEGRAM              | n/a (binary halt)                   | n/a            | `ARCHETYPE`     | `details["archetype"]`  |
| `ML_MODEL_DRIFT_DETECTED`       | `HIGH`     | PAGERDUTY + TELEGRAM              | `ml_model_drift_psi`                | `PSI`          | n/a             | n/a                     |
| `ML_PNL_DEVIATION`              | `HIGH`     | PAGERDUTY + TELEGRAM              | `ml_pnl_deviation_bps`              | `BPS_OF_ONE`   | n/a             | n/a                     |
| `ML_SIGNAL_STALENESS`           | `WARN`     | TELEGRAM + SLACK                  | `ml_signal_staleness_minutes`       | `MINUTES`      | n/a             | n/a                     |
| `ML_INFERENCE_LATENCY_BREACH`   | `WARN`     | SLACK                             | `ml_inference_latency_p99_ms`       | `MILLISECONDS` | n/a             | n/a                     |

### Threshold sources + tuning rationale

- **`ml_signal_staleness_minutes`** (MINUTES) — staleness window before the signal is considered stale enough to
  investigate. Source: ML signal-freshness SLO per archetype; SSOT in UAC `ALERT_THRESHOLDS`. Investigate before
  escalating to `ML_MODEL_VERSION_MISMATCH` or `KILL_SWITCH_ML_MODEL_FAILURE`.
- **`ml_model_drift_psi`** (PSI — Population Stability Index, distinct from ratio) — industry rule of thumb: `< 0.10`
  stable, `0.10–0.25` moderate, `> 0.25` significant. Default `0.20`. Source: training-set baseline vs live inference
  output distribution. PSI is **NOT** a ratio — DO NOT compare against ratio thresholds; the unit guard in
  `test_ml_psi_threshold_unit_is_explicit` catches accidental mis-comparison.
- **`ml_pnl_deviation_bps`** (BPS_OF_ONE) — P&L deviation from expected baseline over 24h rolling window. Default per
  the strategy archetype's published expected-Sharpe band; see strategy-service archetype config for per-archetype
  overrides via `AlertThreshold.for_archetype()`.
- **`ml_inference_latency_p99_ms`** (MILLISECONDS — explicit unit guards against the 500-MIN-vs-500-MS foot-gun) — model
  server p99 latency SLO. Default `500ms`. Wrong unit (minutes) = 500-minute SLO = silent disaster; the
  `test_ml_inference_latency_threshold_unit_is_milliseconds` test catches drift.
- **`ml_model_version_mismatch_minutes`** (MINUTES) — grace window for the live strategy to detect an unexpected model
  version (model promotion lag tolerance). Default tight (`5 min`) — model-version mismatch is zero-tolerance
  regulatory + risk concern; a trade against an unapproved artefact is a P0 halt.

### Operator escalation ladder

The ML codes are designed to escalate progressively:

1. **`ML_INFERENCE_LATENCY_BREACH`** (WARN, Slack-only) — model server slowing; investigate before staleness escalates.
2. **`ML_SIGNAL_STALENESS`** (WARN, Telegram + Slack) — signal stale; could be latency, model crash, or upstream
   feature outage. Escalate to model-team if persists.
3. **`ML_MODEL_DRIFT_DETECTED`** (HIGH, PagerDuty P2) — model output distribution has shifted vs training baseline.
   Page model-team; may be regime change or stale model.
4. **`ML_PNL_DEVIATION`** (HIGH, PagerDuty P2) — strategy underperforming expected baseline. Could be model wrong OR
   execution degraded; correlate with execution-service alerts.
5. **`ML_MODEL_VERSION_MISMATCH`** (CRITICAL, PagerDuty P1) — strategy executing against unexpected model version. Halt
   archetype until artefact / promotion path resolved. No grace period — page immediately.
6. **`KILL_SWITCH_ML_MODEL_FAILURE`** (CRITICAL, PagerDuty P1 + bus.fire()) — model server unreachable / repeated
   inference failures. ARCHETYPE-scoped kill-switch halts the affected archetype only; other archetypes keep trading.
   Recovery: model-team restores server OR operator overrides via DART manual trigger.

### Archetype-scope semantics

`KILL_SWITCH_ML_MODEL_FAILURE` is the only ARCHETYPE-scoped kill-switch in the closed set. The `details["archetype"]`
payload field identifies WHICH archetype to halt — e.g. `"cefi_carry_basis"`, `"defi_leveraged_funding_arb"`. The
KillSwitchBus resolves this scope_key + halts only adapter/strategy instances tagged with that archetype. Other
archetypes (DeFi carry, sports, prediction) keep trading. Missing `details["archetype"]` → fallback to
wildcard-halt-all-archetypes for safety (over-broad halt is the safe default, mirroring the GLOBAL/VENUE scope
fallback semantics in [scope_key resolution](#scope_key-resolution)).

Recovery from an `ARCHETYPE` kill-switch halt requires either (a) the underlying alert condition clearing (model server
recovers, inference success rate restores) OR (b) operator manual DART override per the kill-switch runbook
(`unified-trading-pm/codex/15-runbooks/alerting/kill_switch_ml_model_failure.md`). The execution-service halt-pump
subscribes to the bus event + drains in-flight orders before halting; positions are NOT auto-flattened (operator
decides flatten vs hold-and-monitor).

### Cross-references for ML category

- Plan: [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md)
  Phase 1.B + Phase 1.B-ML covers the 6 codes, threshold registry seeds, and routing rules.
- ML-monitoring producer surface: lives in `ml-inference-service/ml_inference_service/monitoring/` (drift detector,
  staleness clock, latency sampler) — emits alerts through `alerting-service` via PubSub `defi_alerts` topic.
- Strategy-service consumer: subscribes to `KILL_SWITCH_ML_MODEL_FAILURE` bus events via UTL `KillSwitchBus`;
  per-archetype halt semantics in `strategy_service/lifecycle/kill_switch_subscriber.py`.
- Test SSOT: `tests/internal/unit/test_alerting_taxonomy.py` — `_ML_LIFECYCLE_CODES` tuple + `test_ml_*` suite (8
  tests) enforces closed-set membership, threshold units, KILL_SWITCH semantics.

### Reference plan + codex

- Plan: [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md)
  Migrated-issues §"Kill-switch publisher hook" + Phase 8 rehearsal extension.
- Code: `alerting-service/alerting_service/notifiers/router.py` — `_publish_kill_switch_event` /
  `_find_kill_switch_rule` / `_resolve_scope_key` helpers.
- Test: `alerting-service/tests/integration/test_kill_switch_publisher_hook.py` — per-scope happy path + non-kill-switch
  negative path + subscriber-failure isolation.
- UAC SSOT: `AlertRule.kill_switch_scope: KillSwitchScope | None` field +
  `_validate_kill_switch_scope_matches_code_family` validator.
- UTL SSOT: `unified_trading_library.kill_switch` — `KillSwitchBus`, `KillSwitchEvent`, `KillSwitchEventType`,
  `get_kill_switch_bus()`.
- Cross-cutting SSOT: `KillSwitchScope` lives in `unified_api_contracts.internal.domain.deployment_service.isolation`
  (workspace `isolation` SSOT paired with `runtime-topology.yaml`).

## Adding a new severity

`AlertSeverity` should not grow lightly — operators interpret severity vs paging-channel matrix muscle-memory. If a new
tier is needed (e.g. `OBSERVE` between `WARN` and `INFO`), update both `AlertSeverity` AND
`AlertSeverity.to_legacy_filter()` AND the dispatchers' severity-filter expectation in
`alerting-service/alerting_service/notifiers/`.

## Cross-references

- **Plan(s) implementing this:**
  [`alerting_service_live_rules`](../../../plans/active/alerting_service_live_rules_2026_05_07.md).
- **Related codex SSOTs:** [`operator-playbook`](./operator-playbook.md), [`threshold-tuning`](./threshold-tuning.md),
  [`rehearsal-procedure`](./rehearsal-procedure.md),
  [`live-deployment-monitoring`](../../05-infrastructure/live-deployment-monitoring.md).
- **Code:** UAC `unified_api_contracts.canonical.crosscutting.alerting.AlertCode` (top-level facade
  `unified_api_contracts.AlertCode`).

## Open questions

- Do we treat data-pipeline alerts (e.g. backfill stalled) as the same severity tier as trading alerts (e.g. risk-limit
  breached)? Currently no data-pipeline-specific codes exist; recommend adding under a `DATA_PIPELINE_*` category in v2
  with `WARN` defaults.
- Should custody-related alerts (Copper/CEFFU webhook stale) be PAGE-by-default given May-23 live trading scope?
  Currently no custody codes — to be added in Phase 3 producer migration when position-balance-monitor wires custody
  monitoring.
- How do we handle alerts that need different severity per-archetype (e.g. funding-arb stall is PAGE, sports tip-stall
  is WARNING)? Threshold per-archetype overrides exist; severity per-archetype doesn't yet — requires extending
  `AlertRule` or duplicating rules per-archetype. DEFERRED until Phase 7 quietness baseline surfaces real-world need.
