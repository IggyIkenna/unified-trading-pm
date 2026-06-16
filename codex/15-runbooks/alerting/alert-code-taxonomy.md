---
scope: [engineer, admin]
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
  — `AlertThreshold` dataclass + `ThresholdUnit`
  (BPS_OF_ONE/RATIO/USD/MINUTES/SECONDS/MILLISECONDS/COUNT_PER_MINUTE/PSI; 8+ members per slot 8 audit AL-7 PRE_CUTOVER
  refresh 2026-05-12 — SECONDS used by `tick_staleness_seconds`, MILLISECONDS added for 500-MIN-vs-500-MS guard, PSI
  used by ML drift) + `ALERT_THRESHOLDS` dict.
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

## Closed set (~69 codes as of 2026-05-13)

> **Recount (AL-4 reconciliation 2026-05-12; updated 2026-05-13 for Phase 1.E).** The "39 codes as of 2026-05-07"
> headline was last updated at the 2026-05-07 baseline; the closed set has since grown via shipments tracked below.
> Authoritative member-count is the length of `AlertCode` in
> `unified_api_contracts/canonical/crosscutting/alerting/codes.py`. Current breakdown (~69 members, UAC@`086144e`) —
> re-derive from `codes.py` rather than this prose if you need an exact number:
>
> - **5** Kill-switch family (`KILL_SWITCH_*` — +1 `KILL_SWITCH_ORACLE_DIVERGENCE` Phase 1.E); **4** Circuit-breaker;
>   **8** DeFi-original + **5** DeFi recursive-borrow archetype (2026-05-12 Phase 8); **4** Margin ladder; **8**
>   Position/reconciliation; **5** Order; **3** Multi-leg; **4** Service health; **1** Cross-cloud egress; **5** ML
>   lifecycle (2026-05-08); **4** Risk-rule consequence (2026-05-10); **2** Kill-switch recovery (2026-05-10); **4**
>   Tick-staleness / connectivity-gap (2026-05-11); **7** DeFi operational (Phase 1.E 2026-05-13: `VENUE_HALTED`,
>   `LENDING_POOL_PAUSED`, `LENDING_BORROW_CAP_REACHED`, `LENDING_UTILIZATION_HIGH`, `MARKET_DATA_STALE`,
>   `GAS_PRICE_SPIKE`, `GAS_BUDGET_EXCEEDED`).

Adding a new code requires:

1. Append to `AlertCode` in `codes.py`.
2. Add an `AlertRule` to `LIVE_ALERT_RULES` in `rules.py` (or extend an existing wildcard rule's pattern coverage).
3. Author the operator playbook entry under [`operator-playbook.md`](./operator-playbook.md).
4. Include the code in the next quarterly rehearsal scope ([`rehearsal-procedure.md`](./rehearsal-procedure.md)).

The closed-set sanity test `tests/internal/unit/test_alerting_taxonomy.py` enforces (1) ↔ (2): every
`AlertRule.event_pattern` must match at least one `AlertCode` member.

### Categories

- **Kill-switch family (`KILL_SWITCH_*`)** — five codes: `KILL_SWITCH_DEFI_LIQUIDATION_RISK`,
  `KILL_SWITCH_PORTFOLIO_DRAWDOWN`, `KILL_SWITCH_VENUE_DISCONNECT`, `KILL_SWITCH_ML_MODEL_FAILURE` (added 2026-05-08),
  `KILL_SWITCH_ORACLE_DIVERGENCE` (added 2026-05-13 Phase 1.E — GLOBAL scope, covers oracle deviation + staleness). All
  `triggers_kill_switch=True`, all CRITICAL + PagerDuty + Telegram.
- **Circuit-breaker (`CIRCUIT_BREAKER_*`)** — `OPEN` (CRITICAL), `BACKOFF_ESCALATING` (HIGH), `DEGRADED` / `CLOSED`
  (WARN).
- **DeFi-specific (`DEFI_*`)** — original 8: health-factor / weETH-depeg / aave-utilization-spike / funding-rate-flip /
  feature-stale / position-liquidated / rate-deviation / tx-simulation-failed. Family-1/2 recursive-borrow archetype
  added 2026-05-12 (5 more): `DEFI_LIQUIDATION_IMMINENT` / `DEFI_CROSS_VENUE_DELTA_DRIFT` / `DEFI_PERP_VENUE_OUTAGE` /
  `DEFI_ORACLE_STALE_PAUSE` / `DEFI_RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED`. Severity varies; thresholds anchored in UAC
  `ALERT_THRESHOLDS`.
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
- **ML lifecycle (`ML_*` + `KILL_SWITCH_ML_MODEL_FAILURE`)** — 5 `ML_*` codes added 2026-05-08 (`ML_SIGNAL_STALENESS` /
  `ML_MODEL_DRIFT_DETECTED` / `ML_PNL_DEVIATION` / `ML_INFERENCE_LATENCY_BREACH` / `ML_MODEL_VERSION_MISMATCH`) + the
  kill-switch family member `KILL_SWITCH_ML_MODEL_FAILURE` (`cefi_ml_may_23_2026.epic` Tab 5 Item 6). See
  [ML category section](#ml-category--alert-codes--thresholds--killswitchscope-mapping) below for the per-code severity
  routing, threshold sources, and archetype-scope mapping.
- **Risk-rule consequence (`RISK_RULE_*`)** — 4 codes added 2026-05-10 (`risk_simulations_limits_alerting` Phase 1.E +
  Policy B "larger-set-wins"): `RISK_RULE_BLOCKED` (severity per `RiskRule.alerting_severity` — typically HIGH or
  CRITICAL), `RISK_RULE_SCALED_DOWN` (WARN), `RISK_RULE_MONITOR_FIRED` (INFO/WARN), `RISK_RULE_TEST_ONLY_ROUTED` (INFO).
  Producer: risk-and-exposure-service `rule_evaluator`.
- **Kill-switch recovery** — 2 codes added 2026-05-10 (`risk_simulations_limits_alerting` Phase 1.F + DR plan Phase
  1.A): `KILL_SWITCH_AUTO_RECOVERED` (INFO — auto-cooldown path) and `KILL_SWITCH_MANUAL_UNKILLED` (INFO — operator DART
  unkill). Distinct events so dashboards distinguish auto-vs-operator recovery; producers: execution-service breaker
  - risk-and-exposure-service kill-switch on transition out of armed state.
- **Tick-staleness + connectivity-gap** — 4 codes added 2026-05-11 (alerting-service Phase 1+): `TICK_STALENESS` (HIGH —
  MDPS downstream-detected staleness), `CONNECTIVITY_GAP_DETECTED` (HIGH — MTDS upstream WS-disconnect /
  heartbeat-stale), `CONNECTIVITY_RECOVERED` (INFO — recovery), `CONNECTIVITY_GAP_BACKFILLED` (INFO — full backfill).
  30s coalesce window in `notifiers/router.py` keyed on `(venue, instrument)` merges concurrent `TICK_STALENESS` +
  `CONNECTIVITY_GAP_DETECTED` for the same window into ONE operator-visible alert.

## Construction-time validation

`AlertRule` Pydantic validators raise:

- `UnknownAlertCodeError` when an `event_pattern` matches no `AlertCode` member (rule is dead, would never fire).
- `UnknownThresholdKeyError` when `threshold_key` is not in `ALERT_THRESHOLDS`.
- A plain `ValueError` when `triggers_kill_switch=True` is set on a non-`KILL_SWITCH_*` code, or when `event_pattern` /
  `channels` is empty.

Pydantic v2 wraps these in `ValidationError` for downstream consumers, but the typed-error classes remain importable for
direct programmatic use.

## Event names vs AlertCodes — routing seam (AL-13 PRE_CUTOVER 2026-05-12, slot 8 audit)

The alerting router matches `event_pattern` globs against the **event name** string emitted by `log_event()`, NOT
against `AlertCode` enum members directly. The two vocabularies overlap but are not identical:

- **`AlertCode` closed set** (~63 members in `codes.py:21-227`) is the **stable code** new emitters should use.
- **Event names emitted by `log_event()`** are a SUPERSET. Legacy lifecycle events (`KILL_SWITCH_ACTIVATED`,
  `CIRCUIT_BREAKER_OPEN`) ship as event names in `unified_trading_library/events/event_types.py:165,210` +
  `events_interface/schemas.py:372` but are NOT `AlertCode` enum members. The router matches them via wildcard rules
  (`event_pattern="KILL_SWITCH_*"` matches both `KILL_SWITCH_ACTIVATED` event name + every `KILL_SWITCH_DEFI_*` /
  `KILL_SWITCH_PORTFOLIO_DRAWDOWN` / etc. `AlertCode`).

**New emitters should prefer `AlertCode` members** — they get closed-set validation + downstream threshold lookup.
Wildcard routing on legacy event names is supported for backward compatibility but should NOT be used for new code.

CLAUDE.md "Observability" mandates `CIRCUIT_BREAKER_OPEN` + `KILL_SWITCH_ACTIVATED` as required lifecycle events — they
remain valid emission targets even though they are NOT `AlertCode` enum members; the router handles them via the
wildcard path.

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

| `AlertCode`                         | `KillSwitchScope` | scope_key source                               |
| ----------------------------------- | ----------------- | ---------------------------------------------- |
| `KILL_SWITCH_DEFI_LIQUIDATION_RISK` | `GLOBAL`          | `None` (GLOBAL is platform-wide)               |
| `KILL_SWITCH_PORTFOLIO_DRAWDOWN`    | `GLOBAL`          | `None`                                         |
| `KILL_SWITCH_VENUE_DISCONNECT`      | `VENUE`           | `details["venue"]` (alert payload field)       |
| `KILL_SWITCH_ML_MODEL_FAILURE`      | `ARCHETYPE`       | `details["archetype"]` (e.g. `cefi_carry_arb`) |

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

| AlertCode                      | Severity   | Channels             | threshold_key                       | ThresholdUnit  | KillSwitchScope | scope_key source       |
| ------------------------------ | ---------- | -------------------- | ----------------------------------- | -------------- | --------------- | ---------------------- |
| `ML_MODEL_VERSION_MISMATCH`    | `CRITICAL` | PAGERDUTY + TELEGRAM | `ml_model_version_mismatch_minutes` | `MINUTES`      | n/a             | n/a                    |
| `KILL_SWITCH_ML_MODEL_FAILURE` | `CRITICAL` | PAGERDUTY + TELEGRAM | n/a (binary halt)                   | n/a            | `ARCHETYPE`     | `details["archetype"]` |
| `ML_MODEL_DRIFT_DETECTED`      | `HIGH`     | PAGERDUTY + TELEGRAM | `ml_model_drift_psi`                | `PSI`          | n/a             | n/a                    |
| `ML_PNL_DEVIATION`             | `HIGH`     | PAGERDUTY + TELEGRAM | `ml_pnl_deviation_bps`              | `BPS_OF_ONE`   | n/a             | n/a                    |
| `ML_SIGNAL_STALENESS`          | `WARN`     | TELEGRAM + SLACK     | `ml_signal_staleness_minutes`       | `MINUTES`      | n/a             | n/a                    |
| `ML_INFERENCE_LATENCY_BREACH`  | `WARN`     | SLACK                | `ml_inference_latency_p99_ms`       | `MILLISECONDS` | n/a             | n/a                    |

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
2. **`ML_SIGNAL_STALENESS`** (WARN, Telegram + Slack) — signal stale; could be latency, model crash, or upstream feature
   outage. Escalate to model-team if persists.
3. **`ML_MODEL_DRIFT_DETECTED`** (HIGH, PagerDuty P2) — model output distribution has shifted vs training baseline. Page
   model-team; may be regime change or stale model.
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
wildcard-halt-all-archetypes for safety (over-broad halt is the safe default, mirroring the GLOBAL/VENUE scope fallback
semantics in [scope_key resolution](#scope_key-resolution)).

Recovery from an `ARCHETYPE` kill-switch halt requires either (a) the underlying alert condition clearing (model server
recovers, inference success rate restores) OR (b) operator manual DART override per the kill-switch runbook
(`unified-trading-pm/codex/15-runbooks/alerting/kill_switch_ml_model_failure.md`). The execution-service halt-pump
subscribes to the bus event + drains in-flight orders before halting; positions are NOT auto-flattened (operator decides
flatten vs hold-and-monitor).

### Cross-references for ML category

- Plan: [`alerting_service_live_rules_2026_05_07`](../../../plans/active/alerting_service_live_rules_2026_05_07.md)
  Phase 1.B + Phase 1.B-ML covers the 6 codes, threshold registry seeds, and routing rules.
- ML-monitoring producer surface: lives in `ml-inference-service/ml_inference_service/monitoring/` (drift detector,
  staleness clock, latency sampler) — emits alerts through `alerting-service` via PubSub `defi_alerts` topic.
- Strategy-service consumer: subscribes to `KILL_SWITCH_ML_MODEL_FAILURE` bus events via UTL `KillSwitchBus`;
  per-archetype halt semantics in `strategy_service/lifecycle/kill_switch_subscriber.py`.
- Test SSOT: `tests/internal/unit/test_alerting_taxonomy.py` — `_ML_LIFECYCLE_CODES` tuple + `test_ml_*` suite (8 tests)
  enforces closed-set membership, threshold units, KILL_SWITCH semantics.

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
- Cross-cutting SSOT: `KillSwitchScope` lives in `unified_api_contracts.canonical.crosscutting.alerting.codes`
  (canonical-layer SSOT; moved here 2026-05-08 from `unified_api_contracts.internal.domain.deployment_service.isolation`
  so canonical `AlertRule` can carry a per-rule `kill_switch_scope` field without a circular import). The internal-layer
  location now re-exports the canonical symbol, so prior call sites (`unified_api_contracts.internal.KillSwitchScope`)
  keep resolving. The top-level facade is `unified_api_contracts.alerting.KillSwitchScope`.

## Synthetic-data filter (AL-10 PRE_CUTOVER 2026-05-12, slot 8 audit)

> **Codified 2026-05-12 per Alerting audit AL-10** (issue doc
> `plans/archive/issues/codex_audit_alerting_2026_05_12.md`). Source-of-truth pattern:
> `plans/active/mock_data_pipeline_benchmarking_2026_05_10.md` defines the synthetic-data taxonomy + slot 6 shipped the
> `synthetic-data generator taxonomy + per-asset_group registry` at UAC@`d47b232`. AL-10's synthetic-data filter design
> is: "alerting rules don't fire on synthetic / mock data by default".

### Why this filter exists

`alerting-service` ingests every event emitted by `log_event()` across the workspace. In live production this is the
cutover-relevant trading + risk surface. But in development / staging / rehearsal / `CLOUD_MOCK_MODE=true` deployments +
demo-mode seeds + matrix backtests, services emit the SAME event names (`KILL_SWITCH_*`, `CIRCUIT_BREAKER_OPEN`,
`PREFLIGHT_FAILED`, etc.) on top of synthetic data. Without a filter, a demo-mode or staging service emitting
`KILL_SWITCH_*` would page on-call. The only existing suppression is `set_batch_mode(True)` (`router.py:153` /
`main.py:113`) which suppresses _delivery_ in batch replay — but live-mode synthetic events are NOT in batch mode and
therefore fire.

### The filter pattern

Every alert rule consumes events; events carry an `is_synthetic: bool = False` field (from the synthetic-data taxonomy
at UAC@`d47b232`). Rules filter out synthetic by default. Operator can opt-in synthetic alerting for QA via per-rule
`allow_synthetic: bool = False` config flag.

**Three-tier filter precedence** (most-restrictive-wins):

1. **Event-payload tag** — `details["is_synthetic"]` / `details["synthetic"]` / `details["mock"]` truthy → drop the
   alert at routing time (NEVER emit to PagerDuty / Telegram). Rationale: the data-generator is the authoritative source
   for "this event is synthetic" — a downstream consumer can't decide otherwise.
2. **Source-environment tag** — `details["environment"] in {"development", "mock", "demo", "staging"}` → drop unless the
   matching `AlertRule.allow_synthetic` is True. Rationale: rehearsal procedures (per `rehearsal-procedure.md:181`
   `rehearsal=true` tag) opt-in synthetic alerting for the LIVE rehearsal-only window; default-drop everywhere else.
3. **Correlation-ID prefix** — `details["correlation_id"]` prefix matches the per-asset*group synthetic generator
   namespace (e.g.
   `synth_cefi*_`, `synth*defi*_` — per slot 6 generator taxonomy at UAC@`d47b232`) → drop unless `AlertRule.allow_synthetic`is True. Rationale: backstop for services that forget to populate`is_synthetic`.

### Per-rule opt-in (`AlertRule.allow_synthetic`)

Default: `allow_synthetic: bool = False`. Opt-in (synthetic alerts DO fire) per rule for these legitimate use cases:

- **Rehearsal procedures** — the chaos-cron + scheduled-drill rules need to fire on synthetic kill-switch arming to
  validate the rehearsal exercises the page-out path. Set on the rehearsal-scope rules only.
- **QA / staging validation** — pre-cutover staging environment runs a subset of `*_VALIDATION_FAILED` rules with
  `allow_synthetic=True` to confirm the alerting pipeline is wired end-to-end before the live cutover.
- **Synthetic-data pipeline integrity** — rules that fire WHEN the synthetic generator misbehaves (e.g. invalid
  synthetic feed schema, generator stall) inherently target synthetic data; `allow_synthetic=True` is required.

### Routing for synthetic-allowed alerts

Synthetic-allowed alerts NEVER route to PagerDuty + the production on-call Telegram group. Instead:

- **Default**: route to `data-pipeline-test` Telegram group (informational; per the pattern at AL-10 in the issue doc).
- **Rehearsal-only**: route to `rehearsal-observers` Telegram group + write a `RehearsalAuditLog` row; PagerDuty remains
  unrouted unless the operator explicitly invokes a "live-cutover dress rehearsal" mode.
- **Severity downgrade**: synthetic-allowed alerts have their severity downgraded one tier (CRITICAL → HIGH; HIGH →
  WARN; WARN → INFO) at routing time. The original severity is preserved in the audit-log row but the page-out path uses
  the downgraded tier. Operator can override via per-rule `synthetic_severity_override: AlertSeverity | None`.

### Anti-patterns

- **Don't filter synthetic at the emitter side**. The emitter doesn't know which downstream consumer cares; filtering
  belongs at the alerting-router seam where the page-out decision happens. The emitter's job is to TAG (set
  `details["is_synthetic"] = True`) — not to suppress.
- **Don't conflate synthetic with batch mode**. `set_batch_mode(True)` is a delivery-suppression for historical replay
  of REAL events; synthetic-filter is a content-filter for synthetic events in live mode. Both can compose (batch-replay
  of synthetic events is double-suppressed).
- **Don't use a global `allow_synthetic` flag**. Per-rule opt-in is the SSOT — a workspace-wide flag would mask
  forgotten opt-outs on individual rules. The `AlertRule.allow_synthetic` field's `False` default is the safety net.

### Cross-references (synthetic-data filter)

- **Plan**:
  [`mock_data_pipeline_benchmarking_2026_05_10`](../../../plans/active/mock_data_pipeline_benchmarking_2026_05_10.md) —
  defines the synthetic-data taxonomy.
- **UAC**: slot 6 `synthetic-data generator taxonomy + per-asset_group registry` at UAC@`d47b232`.
- **Rehearsal seam**: [`rehearsal-procedure.md`](./rehearsal-procedure.md) § "rehearsal=true tag" — first concrete
  consumer of the filter.
- **Issue doc**:
  [`codex_audit_alerting_2026_05_12.md`](../../../plans/archive/issues/codex_audit_alerting_2026_05_12.md) AL-10 —
  origin of this section.

## Recommended AlertCode additions (PRE_CUTOVER 2026-05-12, slot 8 audit cross-refs)

The following `AlertCode` members SHOULD be added to `unified_api_contracts.canonical.crosscutting.alerting.codes`
before the May-23 cutover. Each entry cites its issue-doc origin + the wire-in owner (the actual UAC PR is routed by
Findings Triage Discipline — this audit doc lists the shape; another slot ships the schema):

### `CUSTODY_KEY_ROTATION_OVERDUE` (or `CUSTODY_HEALTH_DEGRADED` per PB-18 cross-link) — AL-15

> **Origin**: [`codex_audit_alerting_2026_05_12.md`](../../../plans/archive/issues/codex_audit_alerting_2026_05_12.md)
> AL-15. **Source-of-truth pattern**: `CloudKmsCustodyProvider` at `execution-service@d45d24b4` + slot 4's
> `rotation-runbook.md` Phase 9.D. **Custody-stale** = "key rotation is overdue".

- **Code**: `CUSTODY_KEY_ROTATION_OVERDUE` (preferred) OR `CUSTODY_HEALTH_DEGRADED` (umbrella code per PB-18 cross-link
  if the operator decision is to bundle multiple custody-health signals — key-rotation-overdue + webhook- stale +
  Copper/CEFFU connectivity-loss — under a single category code).
- **Severity**: `HIGH` (operational risk; NOT `CRITICAL` because the key still works until the rotation deadline — the
  system is not down, but the rotation cadence has slipped).
- **Cadence**: emitted by the custody-ping loop (PB-18 cross-reference — the position-balance-monitor +
  `CloudKmsCustodyProvider` periodic key-age check). Threshold = `key_age_days > rotation_threshold_days` per slot 4
  rotation runbook.
- **KillSwitchScope**: `None` (this is a non-kill-switch operational alert; key rotation overdue does not arm a
  kill-switch — it's a degraded-mode signal that operator action is required within the rotation deadline window).
- **Routing**: Telegram (production on-call) + PagerDuty (P2 — "page within 30 min"). NOT the live-trading critical
  paging path; this is an operational-degradation signal.
- **Wire-in path**: slot 4 PRE_CUTOVER follow-up (NOT slot-8-owned per Findings Triage). The slot 4
  `rotation-runbook.md` Phase 9.D is the named successor for the wire-in; this audit doc only codifies the AlertCode
  shape.

### Anti-patterns for AlertCode additions

- **Don't ship the AlertCode without the matching `AlertRule`** — `LIVE_ALERT_RULES` (`rules.py`) must register the new
  code with `event_pattern` + `severity` + `channels` + `kill_switch_scope=None` (for non-kill-switch codes) +
  `allow_synthetic=False`. The construction-time validators reject codes without rules.
- **Don't ship the AlertCode without the operator-playbook entry** — the 4-step "Adding a new AlertCode" checklist
  (above) requires a playbook section + rehearsal-scope update. AL-11 (PRE_CUTOVER) raises the QG enforcement gap; in
  the interim, the AlertCode PR should include the playbook stub.

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

---

## Alert lifecycle audit (`STALE_OPEN_ALERT` meta-alert) — Group F of governance_qg_automation_gaps

> Added 2026-05-16 (slot-8) per
> [`governance_qg_automation_gaps_post_cutover_2026_05_12.md`](../../../plans/archive/governance_qg_automation_gaps_post_cutover_2026_05_12.md)
> § Group F. Codifies the closed-loop check that alerting-service must surface `STALE_OPEN_ALERT` when a fire→clear
> pair's clear is overdue. Implementation lives in alerting-service; this section is the contract.

### Contract

Every alert raised via `log_event("ALERT_FIRED", ...)` MUST be either:

1. **Self-clearing** (`alert_type: transient`) — fires once per occurrence, no clear expected. e.g. `BACKFILL_VM_FAILED`
   for one VM run. Listed in `TRANSIENT_ALERT_CODES` in alerting-service registry; lifecycle audit skips these.
2. **Pair-clearing** (`alert_type: paired`) — fires + must be followed by `log_event("ALERT_CLEARED", ...)` with
   matching `alert_id` within `clear_sla_seconds`. e.g. `CIRCUIT_BREAKER_OPEN` should clear when the breaker re-closes.

### `STALE_OPEN_ALERT` semantics

If a paired alert's clear doesn't arrive within `clear_sla_seconds` (default 3600s = 1h; per-code overrides allowed),
alerting-service raises a `STALE_OPEN_ALERT` meta-alert with:

```json
{
  "alert_code": "STALE_OPEN_ALERT",
  "severity": "WARNING",
  "details": {
    "stale_alert_id": "<original alert_id>",
    "stale_alert_code": "<original code>",
    "fired_at": "<ISO8601 of original fire>",
    "sla_seconds": 3600,
    "elapsed_seconds": 4523
  }
}
```

### Why this matters

Without this meta-alert: a paired-clearing alert that fires but never clears stays "open" in the operator dashboard
forever. The breaker may have actually closed; the manifest update / job recovery may have happened. Without a stale
detector, operators must manually walk the open-alert list every cutover-week to triage stale entries.

### Implementation surface

- **`alerting-service/alerting_service/lifecycle/stale_audit.py`** (NEW) — periodic scan of open alerts; emits
  `STALE_OPEN_ALERT` for any paired-clearing alert older than its `clear_sla_seconds`.
- **`alerting-service/alerting_service/registry/alert_metadata.py`** (NEW) — registry mapping each `AlertCode` to
  `{alert_type: transient|paired, clear_sla_seconds: int|None}`. Default for unspecified codes: `paired, 3600s`.
- **Cron**: stale-audit runs every 5 min via existing alerting-service scheduler (no new VM needed).

### Per-code SLA defaults (closed-set; extend in registry)

| Code class                                 | `alert_type` | `clear_sla_seconds`                      |
| ------------------------------------------ | ------------ | ---------------------------------------- |
| `CIRCUIT_BREAKER_*`                        | paired       | 1800 (30min)                             |
| `KILL_SWITCH_*`                            | paired       | 300 (5min — manual operator-acked clear) |
| `BACKFILL_VM_FAILED`                       | transient    | —                                        |
| `MANIFEST_*_DRIFT`                         | paired       | 7200 (2h — manifest consolidator cycle)  |
| `ML_SIGNAL_STALENESS`                      | paired       | 600 (10min)                              |
| `STALE_OPEN_ALERT` (the meta-alert itself) | transient    | —                                        |

### QG hook (deferred to alerting-service slot pickup)

A QG step (proposed STEP TBD) walks `alerting-service/alerting_service/registry/alert_metadata.py` + asserts every
`AlertCode` enum value has an entry. Missing entries fail loud — prevents new alert codes from silently defaulting to
`paired/3600s` if the author intended `transient`.
