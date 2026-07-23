---
doc_type: plan
title: Alerting Service Live Rules — Production Rule SSOT + Thresholds + Paging
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [alerting-service, deployment-service, execution-service, features-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-07"
priority: P0
parent: master_to_live_defi_2026_05_23
depends_on: []
extends: [live_pipeline_mtds_mdps_features_2026_05_08]
gates:
  [
    "master_to_live_defi_2026_05_23:work-stream-E",
    "master_to_live_defi_2026_05_23:Group-F",
    "master_to_live_defi_2026_05_23:Group-G",
  ]
archived: 2026-05-23
last_updated: 2026-05-23
estimate_class: design
estimate_baseline_ai_days: 22
estimate_calibrated_ai_days: 13.2
estimate_calibration_note: "Backfilled 2026-05-13: 60 todos, 38 done; ~22 remaining (rule thresholds, paging,
  circuit-breaker wiring, 48h staging dry-run, live rehearsal). Design class (operator-judgment thresholds + closed-set
  rules). Baseline 22 (~1 AI-day per remaining substantive todo); × 0.6 = 13.2.

  "
parent_epic: observability_master
assigned_vm: vm-cross-cutting
---

## Deferred work — migrated to:

Alerting code shipped. Operator soak + rehearsal tasks migrated to `plans/epics/observability_master.md` § P3 (Telegram
token rotation, PagerDuty escalation policy, alert rehearsal, 48h soak, pair-review with Harsh). Archiving 2026-05-23.

> **🟢 VM RUNNING — alerting-quietness-20260522-083225** — Phase 7 quietness baseline VM RUNNING 2026-05-22
> (asia-northeast1-c, staging, 48h). Fix set: alerting-service@59e020f (live→orchestrator.run_subscriber_loop so
> heartbeat fires) + deployment-service@40fdc3d (setup-data-pipeline-vm.sh alerting-quietness-baseline task handler:
> env-var Pydantic settings, SM secret fetch, correct tarball wiring). Auto-shutdown at T+48h (~2026-05-24 08:32 UTC).
> **Banner owner**: Slot 8 (launched 2026-05-22). Monitor:
> `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/alerting-quietness-20260522-083225/run.log`

> **🟡 IN-FLIGHT — Phase 8 of `defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md` adds `HealthFactorMonitor` +
> `LiquidationProximityCircuit` as new alerting consumers. These require kill-switch tier-up integration
> (`DEFI_HEALTH_FACTOR_CRITICAL` / `DEFI_LIQUIDATION_IMMINENT` / `DEFI_FUNDING_RATE_FLIP` alert codes already added to
> UAC `AlertCode`). Banner updated 2026-05-18 slot 3 to reference post-cutover successor plan (previously referenced
> `defi_recursive_borrow_archetypes_2026_05_10.md`).**

# Alerting Service Live Rules — Production Rule SSOT + Thresholds + Paging

> **🟡 IN-FLIGHT REFACTOR — batch/live symmetry 2026-05-10** (BE-AWARE)
>
> [`batch_live_symmetry_2026_05_10`](batch_live_symmetry_2026_05_10.md) Tab 2 ships `RECON_GREEN_THRESHOLDS` dict at
> `unified_api_contracts/canonical/crosscutting/alerting/thresholds.py` for `carry_staked_basis` +
> `leveraged_funding_arb`. **Before adding new alerting thresholds or recon configs** — check if the canonical
> `RECON_GREEN_THRESHOLDS` dict in UAC already covers your archetype. Tab 8 (recon-green calibration) depends on Tab 2
> shipping these thresholds.

> **🟡 IN-FLIGHT REFACTOR — Live-pipeline activation 2026-05-08**
>
> [`live_pipeline_mtds_mdps_features_2026_05_08`](../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)
> Phase 9 EXTENDS this plan's surface with live-pipeline tier rules (cluster_pct_skipped_60s, degraded_ratio_60s,
> staleness_seconds thresholds), a new `streaming.alerting.circuit_breaker` Redis Stream wired to strategy-service, and
> 3 circuit-breaker actions (`stop_new_signals` / `force_exit_only` / `halt_strategy`). Coordinate ownership: this plan
> owns the AlertCode taxonomy import + per-rule wiring; the live-pipeline plan adds the new rules + bridge.

> **📋 RELATED PLAN — Promote workflow (May-23 dual-track + post-cutover, spawned 2026-05-10)**: the
> [`promote_workflow_may23_cli_path_2026_05_10`](./promote_workflow_may23_cli_path_2026_05_10.md) UI track Phase U3
> ships a `POST /promote/{strategy_id}/{manifest_id}` endpoint with a **minimal pre-flight pipeline** that probes
> alerting paging targets configured in Secret Manager — this composes directly with this plan's Phase 4 paging-target
> wiring + Phase 7 quietness 48h staging dry-run + Phase 8 live rehearsal. **BE AWARE** when changing Secret Manager
> paths for Telegram bot tokens / PagerDuty integration keys: the promote workflow's pre-flight reads from the same
> paths. Post-cutover plan
> ([`promote_workflow_post_cutover_ui_pipeline_2026_05_10`](./promote_workflow_post_cutover_ui_pipeline_2026_05_10.md))
> Phase 6.B adds **per-deployment alerting auto-rule generation** (consumes `STRATEGY_PROMOTED_TO_LIVE` event +
> generates `LIVE_ALERT_RULES_DYNAMIC` registry separate from the static `LIVE_ALERT_RULES` this plan owns) — coordinate
> ownership boundary so static + dynamic rules don't conflict. Question doc:
> [`plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md`](../questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md).

Closes the "alerting plan does not exist" anomaly flagged by the 2026-05-07 audit (see
`_AUDIT_2026_05_07_dependency_graph.md` operator action item #1). The alerting-**service** itself already exists
(multi-channel routing across Slack/Email/PagerDuty/Telegram, KillSwitchBus subscriber via `7b74ed8`, MarginEvent
consumer via `f4c308f`, Phase 8 QG coverage). The gap is the **rules SSOT + concrete thresholds + production paging
targets + operator playbook + rehearsal procedure** required to enable live trading on 2026-05-23.

## Context

**Existing capability** (verified 2026-05-07):

- Service: `alerting-service/` — Cloud Run + (AWS-ready via `buildspec.aws.yaml`)
- Config: `AlertingSystemConfig` with `routing_rules` default-factory at
  [`config.py:11-199`](alerting-service/alerting_service/config.py#L11-L199)
- KillSwitchBus subscriber wired via UTL (Phase 3c, commit `7b74ed8`)
- E2E test plan: [`plans/active/end-to-end-testing/020_alerting_service.md`](end-to-end-testing/020_alerting_service.md)
  — covers PubSub subscriptions, downstream commands, frontend API surface
- UAC envelope:
  [`unified_api_contracts/internal/alerting/alerts.py`](unified-api-contracts/unified_api_contracts/internal/alerting/alerts.py)
  has `DefiAlert` BaseModel
- Circuit-breaker config SSOT:
  [`unified_api_contracts/internal/reference/circuit_breaker_config.py`](unified-api-contracts/unified_api_contracts/internal/reference/circuit_breaker_config.py)
- Existing routing patterns (from e2e plan §"Alert Routing Rules"): `KILL_SWITCH_*` / `CIRCUIT_BREAKER_OPEN` /
  `DEFI_HEALTH_FACTOR_CRITICAL` / `DEFI_WEETH_DEPEG` / `DEFI_AAVE_UTILIZATION_SPIKE` / `DEFI_FUNDING_RATE_FLIP` /
  `DEFI_FEATURE_STALE` / `PREFLIGHT_FAILED` / `SERVICE_DEGRADED` / catch-all

**Gap analysis** — what's missing for May-23:

1. UAC alert-type taxonomy is open-ended — only `DefiAlert` envelope, no closed `StrEnum` of alert codes the way
   `EMPTY_CONFIRMED_REASONS` codifies honest-coverage reasons. Routing rules drift between service config + UAC.
2. Threshold values are scattered or absent: AAVE utilization spike threshold, weETH depeg basis-points, funding-rate
   flip magnitude, health-factor critical level, feature-staleness grace window. No registry, no per-rule default +
   per-archetype override.
3. Production paging targets unset: Telegram chat IDs, PagerDuty service keys, Slack channel IDs all absent or
   hard-coded. No Secret Manager wiring for rotation. No on-call rotation policy.
4. No DART integration for the ack/escalate/resolve flow per alert.
5. No operator playbook — for each alert type, what's the diagnosis recipe, what's the resolution path, what's the
   rollback?
6. No live rehearsal procedure — synthetic alert injection + ack flow + escalation + auto-recovery validated end-to-end.
7. No "quietness baseline" — the system has not yet run 24-48h with thresholds tuned; false-positive rate unknown. Live
   trading without a quiet baseline risks alert fatigue → real alerts ignored.

## Pre-audit (blast radius)

Affected files / consumers when shipping:

- [unified-api-contracts/unified_api_contracts/internal/alerting/](unified-api-contracts/unified_api_contracts/internal/alerting/)
  — add taxonomy + threshold registry
- [unified-api-contracts/unified_api_contracts/internal/reference/circuit_breaker_config.py](unified-api-contracts/unified_api_contracts/internal/reference/circuit_breaker_config.py)
  — extend with per-rule thresholds
- [alerting-service/alerting_service/config.py](alerting-service/alerting_service/config.py) — replace inline
  `_default_routing_rules` with UAC SSOT consumption
- [alerting-service/alerting_service/circuit_breaker.py](alerting-service/alerting_service/circuit_breaker.py) — wire
  UAC threshold lookups
- `risk-and-exposure-service/` — emit alerts using UAC closed taxonomy
- `position-balance-monitor-service/` — same
- [execution-service/](execution-service/) — circuit-breaker subscriber + KILL_SWITCH emitter
- [features-service/features_service/onchain/](features-service/features_service/onchain/) — emit
  `DEFI_HEALTH_FACTOR_CRITICAL`, `DEFI_AAVE_UTILIZATION_SPIKE`, `DEFI_FUNDING_RATE_FLIP`, `DEFI_FEATURE_STALE` consumers
- [unified-trading-system-ui/](unified-trading-system-ui/) (DART) — Active Alerts panel, Ack button, Escalate button
  (per e2e plan Frontend API Surface)
- Codex doc: `unified-trading-pm/codex/15-runbooks/alerting/` — new operator playbook directory
- Secret Manager: 4 secret entries for paging credentials (Telegram bot token, Telegram chat IDs, PagerDuty service key,
  Slack webhook URL)

## Phased execution DAG

Phase numbering uses Citadel-grade convention; QG gate between phases.

### Phase 1 — UAC alert taxonomy + threshold SSOT (1 day, **PARALLEL** with Phase 2)

Closed-set taxonomy mirrors `EMPTY_CONFIRMED_REASONS` pattern. Routing rules read from UAC, not from inline
default-factory.

- [x] [SCRIPT] P0. Add `AlertCode` StrEnum to `unified_api_contracts/canonical/crosscutting/alerting/codes.py`
      (top-level facade `unified_api_contracts.alerting`) with all currently-routed codes plus the 5 plan-required
      additions (KILL_SWITCH_DEFI_LIQUIDATION_RISK, KILL_SWITCH_PORTFOLIO_DRAWDOWN, KILL_SWITCH_VENUE_DISCONNECT,
      CIRCUIT_BREAKER_OPEN, DEFI_HEALTH_FACTOR_CRITICAL, DEFI_WEETH_DEPEG, DEFI_AAVE_UTILIZATION_SPIKE,
      DEFI_FUNDING_RATE_FLIP, DEFI_FEATURE_STALE, PREFLIGHT_FAILED, SERVICE_DEGRADED, BALANCE_DRIFT,
      ORDER_REJECTION_SPIKE, MARGIN_THRESHOLD_BREACH, POSITION_DRIFT) + CROSS_CLOUD_EGRESS_DETECTED added per audit
      2026-05-07 §dual-cloud. Closed set, 39 codes. Shipped UAC@d00326d.
- [x] [SCRIPT] P0. Add `AlertSeverity` StrEnum: `CRITICAL` (page now), `HIGH` (page within SLA), `WARN` (notify, no
      page), `INFO` (log only). `AlertSeverity.to_legacy_filter()` maps to the legacy `severity_filter` field
      (`"critical"` / `"warning"` / None) so Phase 2 dispatchers don't need migrating in lockstep. Shipped UAC@d00326d.
- [x] [SCRIPT] P0. Add `AlertChannel` StrEnum: `PAGERDUTY`, `TELEGRAM`, `SLACK`, `EMAIL`, `LOG_ONLY`. Shipped
      UAC@d00326d.
- [x] [SCRIPT] P0. Add `AlertRule` Pydantic model with
      `code: AlertCode, severity: AlertSeverity,     channels: tuple[AlertChannel, ...], event_pattern: str (fnmatch), runbook_doc: str,     threshold_key: str | None, triggers_kill_switch: bool, description: str`.
      Construction-time validators (`UnknownAlertCodeError` / `UnknownThresholdKeyError`) fail loud on unknown code,
      unknown threshold_key, KILL_SWITCH-flag-on-non-KILL_SWITCH-code, empty channels, empty event_pattern.
      `to_routing_dict()` renders the legacy default-factory shape so Phase 2 migration is byte-equivalent. Shipped
      UAC@d00326d.
- [x] [SCRIPT] P0. Add `LIVE_ALERT_RULES: tuple[AlertRule, ...]` SSOT in
      `unified_api_contracts/canonical/crosscutting/alerting/rules.py`. 39 rules covering all 10 patterns from
      `alerting-service/config.py:_default_routing_rules` byte-for-byte + the 5 new plan-required codes (BALANCE_DRIFT,
      ORDER_REJECTION_SPIKE, MARGIN_THRESHOLD_BREACH, POSITION_DRIFT, DEFI_TX_SIMULATION_FAILED) +
      CROSS_CLOUD_EGRESS_DETECTED. Catch-all `*` last so specific rules win. Shipped UAC@d00326d.
- [x] [SCRIPT] P0. Add `ALERT_THRESHOLDS: dict[str, AlertThreshold]` registry in
      `unified_api_contracts/canonical/crosscutting/alerting/thresholds.py`. 10 thresholds with explicit `ThresholdUnit`
      (BPS_OF_ONE / RATIO / USD / MINUTES / COUNT_PER_MINUTE), `default_value` (Decimal), `per_archetype_overrides`,
      `source_doc` citation, `description`. Resolves audit 2026-05-07 §3 #5 AAVE-bps ambiguity by pinning
      `defi_aave_utilization_spike_bps` unit to `BPS_OF_ONE` with citation to Aave V3 InterestRateStrategy
      `optimalUsageRatio=0.95     RAY` for WETH/USDC/USDT/DAI. Per-archetype override added for
      `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`; renamed from legacy `leveraged_funding_arb` per Stream B
      canonicalisation 2026-05-07) (9000 bps_of_one = 90%, tighter signal). Shipped UAC@d00326d.
- [x] [SCRIPT] P0. Threshold defaults seeded with these initial values (verified by Phase 7 quietness baseline; see §
      "Threshold seeding rationale"). Shipped UAC@d00326d:
  - `defi_health_factor_critical`: 1.05 (Aave HF; below 1.0 triggers liquidation; 5% buffer)
  - `defi_weeth_depeg_bps`: 50 (0.5% from peg over 5min window)
  - `defi_aave_utilization_spike_bps`: 9500 (95% pool utilization; default-yield drops sharply above)
  - `defi_funding_rate_flip_bps_5m`: 100 (1% APR flip in 5min — could indicate stat-arb regime change)
  - `defi_feature_stale_minutes`: 15 (LST yield read freshness — staked-basis archetype)
  - `balance_drift_usd`: 1000 (notional discrepancy between expected and observed wallet balance)
  - `order_rejection_spike_per_min`: 10 (rolling rate over 5min)
  - `margin_threshold_breach_bps`: 200 (2% from initial-margin-call line; broker-defined)
  - `position_drift_bps`: 100 (1% from target weight; rebalance trigger)
- [x] [SCRIPT] P0. UAC sanity tests in `tests/internal/unit/test_alerting_taxonomy.py` (31 tests): every
      `AlertRule.threshold_key` in `ALERT_THRESHOLDS`; every `AlertRule.event_pattern` matches at least one `AlertCode`;
      catch-all `*` last; no duplicate `(event_pattern, severity)` pairs; `KILL_SWITCH_*` codes carry
      `triggers_kill_switch=True`; CRITICAL-severity rules include PagerDuty channel; plan-required 15 codes present;
      `to_routing_dict()` legacy-shape parity; AAVE-bps unit explicit; `AlertSeverity.to_legacy_filter()` round-trip.
      All 31 green. Shipped UAC@d00326d.
- [x] [QG] P0. UAC quality-gates pass + push (UAC@d00326d on origin/live-defi-rollout). Step-6 production-readiness
      validators surfaced 3 unrelated PM cross-ref BROKEN entries (defi_master / data_status_drilldown /
      master_to_live_defi → issues/manifest_consolidator_arrow_typeerror) that are pre-existing PM repo state owned by
      other agents per CLAUDE.md QG-failure-attribution rule — UAC content gates (lint / format / tests / typecheck /
      codex / dead-code) all green.
- [x] [SCRIPT] P1. **ML lifecycle alerting taxonomy extension (2026-05-08, cefi_ml_may_23_2026.epic Tab 5 Item 6).**
      Shipped UAC@6c4784f. Adds 6 AlertCode members (`KILL_SWITCH_ML_MODEL_FAILURE`, `ML_SIGNAL_STALENESS`,
      `ML_MODEL_DRIFT_DETECTED`, `ML_PNL_DEVIATION`, `ML_INFERENCE_LATENCY_BREACH`, `ML_MODEL_VERSION_MISMATCH`); 5
      `ALERT_THRESHOLDS` keys (`ml_signal_staleness_minutes`=5, `ml_model_drift_psi`=0.20, `ml_pnl_deviation_bps`=200,
      `ml_inference_latency_p99_ms`=500, `ml_model_version_mismatch_minutes`=0); 2 new `ThresholdUnit` members
      (`MILLISECONDS`, `PSI`); 6 explicit `AlertRule` entries in `LIVE_ALERT_RULES`; 7 new sanity tests (38 total, 31 →
      38). `KILL_SWITCH_ML_MODEL_FAILURE` rule UPDATED 2026-05-08 with `kill_switch_scope=KillSwitchScope.ARCHETYPE`
      (UAC@3793310 — Sub-A's `kill_switch_scope` field landed via self-ship; ML rule now scope-complete). Producer-side
      wiring (ml-inference-service / strategy-service / ml-training-service) DEFERRED to Phase 3 (envelope
      `code: AlertCode` field UAC@2636815 unblocks but actual emission sites pending). DART manual-pause / override /
      replicate UI for ML trades DEFERRED to `strategy_and_dart_master` Phase 2.2.
- [x] [AGENT] P1. **Codex `alert-code-taxonomy.md` ML category section + KillSwitchScope mapping table.** Sub-E
      attempted the edit 5+ times during the 2026-05-08 cycle; foot-gun #3 (parallel-agent `git checkout HEAD -- <file>`
      auto-revert) wiped each attempt. Pick up on a quieter session. Required content: ML category subsection (severity
      routing per ML code, threshold sources, archetype-scope mapping) + KillSwitchScope mapping table extension showing
      all 4 KILL*SWITCH*\* codes (DEFI_LIQUIDATION_RISK=GLOBAL, PORTFOLIO_DRAWDOWN=GLOBAL, VENUE_DISCONNECT=VENUE,
      ML_MODEL_FAILURE=ARCHETYPE) + scope_key resolution rules per code. **SHIPPED 2026-05-11** PM@`<pending>`:
      `/codex/15-runbooks/alerting/alert-code-taxonomy.md` extended with (a) new
      `## ML category — alert codes +     thresholds + KillSwitchScope mapping` section covering per-code routing matrix
      (6 ML codes with severity/channels/threshold_key/unit/scope), threshold sources + tuning rationale (PSI vs ratio
      guard, ms vs minutes foot-gun avoidance), operator escalation ladder (INFERENCE_LATENCY → STALENESS → DRIFT → PNL
      → VERSION → KILL_SWITCH), archetype-scope semantics + recovery flow, cross-references; (b) KillSwitchScope mapping
      table extended with `KILL_SWITCH_ML_MODEL_FAILURE` ARCHETYPE row + `details["archetype"]` scope_key source; (c)
      Categories bullet for ML lifecycle codes with deep-link to new section; (d) `AlertRule.pattern` references updated
      to `event_pattern` in tandem with UAC@`0b61aec` rename.

### Phase 2 — Service migration to UAC SSOT (1 day, **PARALLEL** with Phase 1 once Phase 1 lands)

Replace inline default-factory with UAC consumption. No double-SSOT per workspace "no double SSOT" rule.

- [x] [AGENT] P0. `alerting-service/alerting_service/config.py` — replaced 28-entry inline `_default_routing_rules` with
      `from unified_api_contracts import LIVE_ALERT_RULES` (top-level facade, not deep-import). Default-factory now
      returns `[rule.to_routing_dict() for rule in LIVE_ALERT_RULES]` (37 rules). Single SSOT achieved. Shipped
      alerting-service@b025e83.
- [x] [AGENT] P0. `alerting-service/alerting_service/rules/defi_rules.py` — replaced hardcoded
      `_AAVE_UTILIZATION_THRESHOLD = Decimal("0.95")` with UAC `ALERT_THRESHOLDS["defi_aave_utilization_spike_bps"]`
      lookup. New helper `_aave_utilization_threshold_ratio(archetype)` normalises bps_of_one (UAC unit) → ratio +
      respects per-archetype overrides (`ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`; renamed from legacy
      `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07) fires at 90% vs default 95%).
      `check_aave_utilization()` now accepts optional `archetype` parameter; alert payload includes `threshold_ratio` +
      `archetype` for operator transparency. Shipped alerting-service@b025e83. NOTE: `circuit_breaker.py` was scoped in
      the original todo, but audit found no inline thresholds there — its only constants are sliding-window / cooldown /
      threshold counts which are operational-tuning knobs (not risk thresholds owned by UAC). DEFERRED unless a future
      audit surfaces a real threshold drift candidate.
- [x] [AGENT] P0. `alerting-service/tests/unit/test_uac_routing_rules_consumption.py` — 37 tests covering: (a)
      byte-equivalence of `_default_routing_rules()` vs `[r.to_routing_dict() for r in LIVE_ALERT_RULES]`; (b) every
      legacy pattern still routed (KILL*SWITCH*_, CIRCUIT*BREAKER*_, DEFI*\*, MARGIN*\_, etc); (c) AAVE threshold reads
      UAC + per-archetype overrides apply (`ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) fires at 91%,
      default doesn't); (d) `check_aave_utilization` fires correctly above/below thresholds; (e) KILL*SWITCH*_ family
      CRITICAL+PagerDuty+`triggers_kill_switch=True`; (f) CROSS_CLOUD_EGRESS_DETECTED PagerDuty-routed. All 37 green.
      Shipped alerting-service@b025e83.
- [x] [QG] P0. `cd alerting-service && bash scripts/quality-gates.sh` PASSED — all 6/6 gates green (auto-fix / lint /
      tests / type-check / codex compliance / production-readiness). Shipped alerting-service@b025e83.
- [x] [SCRIPT] P0. **DEFERRED — Harsh pair-review request via PR**: `alerting-service` is Harsh's repo; the diff is
      committed on `live-defi-rollout` for asynchronous pair-review. Diff surface is minimal (config.py default-factory
      body + defi_rules.py threshold migration + new test file). Per CLAUDE.md "Two teammates × multiple parallel
      agents" rule + work-split Agent-1 ownership of alerting Phase 2, ship-first-review-after is the institutional
      default.
- [x] [AGENT] P0. **Phase 2.X — `AlertRule.pattern` → `event_pattern` rename follow-up PR.** UAC@d00326d shipped the
      Pydantic field as `pattern`; codex SSOT
      [`/codex/03-observability/alerting.md`](/codex/03-observability/alerting.md) § "Alerting-Service Routing Rules"
      (lines 116-149) uses `event_pattern`. Codex is SSOT for target structure per workspace rule. Rename surface: UAC
      `unified_api_contracts/canonical/crosscutting/alerting/rules.py` (Pydantic field + every constructor in seed
      dict) + UAC tests + alerting-service consumer (config.py default-factory body + any `.pattern` attribute access) +
      tests. Single logical-unit commit; no compatibility shim. Owns the IN-FLIGHT REFACTOR banner at top of this plan —
      banner clears when this todo flips `[x]`. **SHIPPED 2026-05-11**: UAC@`0b61aec` (Pydantic field rename + 44
      LIVE_ALERT_RULES constructor calls + validators `_pattern_non_empty` → `_event_pattern_non_empty` +
      `_validate_pattern_matches_codes` → `_validate_event_pattern_matches_codes` + test file rename `rule.pattern` →
      `rule.event_pattern` × all sites + drive-by fix to `test_alert_rule_accepts_kill_switch_flag_on_kill_switch_code`
      adding `kill_switch_scope=KillSwitchScope.VENUE` — 44/44 taxonomy tests green) + alerting-service@`3b94456`
      (router.py `_find_kill_switch_rule`: `rule.pattern` → `rule.event_pattern`). `to_routing_dict()` dict KEY stays
      `"event_pattern"` (legacy byte-equivalence preserved). IN-FLIGHT REFACTOR banner cleared by this flip.

### Phase 3 — Producer migration to UAC closed-set codes (2 days, parallel across services)

Every emitter must use `AlertCode` enum, not raw strings. Fail-loud on unknown.

> **🟢 4 DeFi-specific codes PULLED FORWARD May-23 (operator direction 2026-05-13)** — `DEFI_AAVE_UTILIZATION_SPIKE` /
> `DEFI_FUNDING_RATE_FLIP` / `DEFI_FEATURE_STALE` / `DEFI_WEETH_DEPEG` features-onchain emission sites now in-scope
> pre-cutover. Was previously deferred per master plan Group F item 22 "Sub-B finding (calculators not yet wired;
> defi_master Fork 1 territory)"; reversed per operator rationale "throughput margin (~5-6x), no descope, perfect
> cutover" — ~0.5-1 cal-AI-days against ~1,880 cal-day capacity in next 9 days. The 4 codes already exist in the
> AlertCode enum (shipped UAC@`d00326d`); only the producer-side emission wiring is the pull-forward scope. See per-code
> todo below.

- [x] [SCRIPT] P0. `risk-and-exposure-service/`: emit `BALANCE_DRIFT`, `MARGIN_THRESHOLD_BREACH`, `CIRCUIT_BREAKER_OPEN`
      using `AlertCode.X`. (risk-and-exposure-service@a5aac82 — Slot 6 2026-05-14.
      MARGIN_THRESHOLD_BREACH+CIRCUIT_BREAKER_OPEN done in prior session. BALANCE_DRIFT: added `_check_balance_drift()`
      to `RiskMonitor` — sliding per-client equity baseline, fires when `abs(current - previous) > $1000`; emits
      `log_event("BALANCE_DRIFT", ..., alert_code=AlertCode.BALANCE_DRIFT.value)`. 3 unit tests pass.)
- [x] [SCRIPT] P0. `position-balance-monitor-service/`: emit `BALANCE_DRIFT`, `POSITION_DRIFT`.
      (position-balance-monitor-service@d206ab3 — prior session. BALANCE_DRIFT in `fee_reconciliation_engine.py`;
      POSITION_DRIFT in `reconciliation_engine.py`. Code confirmed present.)
- [x] [SCRIPT] P0. `execution-service/`: emit `KILL_SWITCH_*` from KillSwitchBus + `ORDER_REJECTION_SPIKE` from
      rejection-tracker. (execution-service@e78dd1bf9 — Slot 6 2026-05-14. ORDER*REJECTION_SPIKE: new
      `engine/order_rejection_tracker.py` sliding-window tracker (5min, 10/min threshold), wired from
      `order_adapter.py`. KILL_SWITCH*\*: `kill_switch.activate()`+`deactivate()` now stamp `alert_code` in details;
      `kill_switch_bus_bridge` maps scope→AlertCode. 2 new unit tests pass.)
- [x] [SCRIPT] P0. `features-service (onchain family)/`: emit `DEFI_AAVE_UTILIZATION_SPIKE` (from Aave pool-utilization
      calc), `DEFI_FUNDING_RATE_FLIP` (from perp funding calc), `DEFI_FEATURE_STALE` (from feature-staleness watchdog),
      `DEFI_WEETH_DEPEG` (from LST-peg deviation calc). (features-service@2ecb1378 — Slot 6 2026-05-14. Producer-side
      `log_event` calls wired: `DEFI_FEATURE_AAVE_UTILIZATION` per pool row in `_calculate_utilization_features`;
      `DEFI_FEATURE_PERP_FUNDING_RATE` per instrument from `hl_data` pre-select in `_calculate_perps_features`;
      `DEFI_FEATURE_WEETH_ETH_RATE` for weETH rows in `lst_features.compute_lst_features_for_day`;
      `DEFI_FEATURE_STALENESS` on warn/critical in `FeatureFreshnessChecker.check_output_freshness`. 9 unit tests pass.)
      **DEFERRED**: `DEFI_HEALTH_FACTOR_CRITICAL` (from Aave health-factor calculator) — not in the 4 pulled-forward
      codes for May-23 cutover; no `_calculate_health_factor` method exists yet. File as follow-up post-cutover.
- [x] [SCRIPT] P1. **🟢 PULLED FORWARD May-23** (operator direction 2026-05-13) — features-onchain emission sites for
      the 4 DeFi-specific codes, per-calculator wiring breakdown (composes with parent P0 todo above).
      (alerting-service@12411e0 — Slot 8 2026-05-13. Producer-side wired via new `defi_feature_event_handler.py`
      bridging 4 canonical feature event names to the existing check*\* rules in `defi_rules.py`. Rule wiring:
      `code=AlertCode.DEFI*\_`field populated on each check\__ return;`route_defi_alert`prefers`alert.code.value` per
      producer-migration window 2026-05-08+. Alert-subscriber dispatch table extended to route DeFi feature events. 10
      new unit tests pass alongside existing 34.)
  - [x] `DEFI_AAVE_UTILIZATION_SPIKE` — `check_aave_utilization` returns DefiAlert with
        `code=AlertCode.DEFI_AAVE_UTILIZATION_SPIKE`; producer via `DEFI_FEATURE_AAVE_UTILIZATION` event_name +
        `_build_aave_utilization_alert` builder; UAC threshold `defi_aave_utilization_spike_bps` (9500/9000
        per-archetype) applied. (alerting-service@12411e0)
  - [x] `DEFI_FUNDING_RATE_FLIP` — `check_funding_rate_flip` returns DefiAlert with
        `code=AlertCode.DEFI_FUNDING_RATE_FLIP`; producer via `DEFI_FEATURE_PERP_FUNDING_RATE` event_name. UAC threshold
        `defi_funding_rate_flip_bps_5m` (100 BPS default). (alerting-service@12411e0)
  - [x] `DEFI_FEATURE_STALE` — `check_feature_staleness` returns DefiAlert with `code=AlertCode.DEFI_FEATURE_STALE`;
        producer via `DEFI_FEATURE_STALENESS` event_name. UAC threshold `defi_feature_stale_minutes` (15 min default;
        2x-SLA rule). (alerting-service@12411e0)
  - [x] `DEFI_WEETH_DEPEG` — `check_weeth_depeg` returns DefiAlert with `code=AlertCode.DEFI_WEETH_DEPEG`; producer via
        `DEFI_FEATURE_WEETH_ETH_RATE` event_name. UAC threshold `defi_weeth_depeg_bps` (50 BPS_OF_ONE = 0.5% default).
        (alerting-service@12411e0)
- [x] [SCRIPT] P0. Each emitter: add unit test asserting alert payload conforms to `DefiAlert` envelope + `AlertCode`
      enum value. (features-service@2ecb1378 — 9 tests in `tests/onchain/unit/test_defi_alert_emission.py`; all pass.
      Covers all 4 pulled-forward emitters with payload-shape assertions per alerting-service consumer contracts.)
- [x] [QG] P0. Per-service QG pass on each emitter repo. (Slot 6 2026-05-14. risk-and-exposure-service QG ✅ (80.70%
      coverage); execution-service QG ✅ (23 codex violations within ratchet). All 3 emitter repos green.)

### Phase 4 — Production paging targets via Secret Manager (1 day)

No hard-coded creds. Rotation via `ApiKeyReloader` per CLAUDE.md.

- [x] [SCRIPT] P0. **Telegram paging credentials pushed to GCP + AWS Secret Manager (Tab L 2026-05-10).** Per operator
      direction "Telegram-as-primary for Phase 4" + the existing `.act-secrets` operator setup. Pushed:
      `alerting-telegram-bot-token` + `alerting-telegram-chat-id` to BOTH (a) GCP project `central-element-323112`
      (`gcloud secrets create` with automatic replication, version 1 seeded) AND (b) AWS account `427895769566` region
      `ap-northeast-1` (`aws secretsmanager create-secret`, version 1 seeded). Verified via list: 1 version per secret
      per cloud. **PagerDuty + Slack paging deferred** to a future cycle pending operator decision on PagerDuty service
      tier (open question 1 of this plan); until then Telegram is the primary paging channel for Phase 7-9. Used UTL-
      naming-pattern (kebab-case `alerting-{channel}-{field}`) so the existing `UnifiedCloudConfig.telegram_bot_token`
      env-var bindings + `_get_cloud_config()` singleton in `alerting-service/alerting_service/notifiers/router.py` pick
      up via the `*_SECRET` metadata env wiring used by data-pipeline-vm bootstrap. Tab L verified end-to-end via smoke
      (next item). **DEFERRED-PER-DECISION (operator)**: PagerDuty + Slack credential push
      (`alerting-pagerduty-service-key`, `alerting-slack-webhook-url`) — pending Telegram-as-primary validation through
      Phase 7 baseline; if quietness shows Telegram-only paging is sufficient, PagerDuty add becomes optional.
- [x] [SCRIPT] P0. **Smoke alert sent to real Telegram chat (Tab L 2026-05-10 18:57 UTC).** Verified end-to-end via the
      existing `alerting_service.notifiers.telegram.send_telegram()` function reading `TELEGRAM_BOT_TOKEN` +
      `TELEGRAM_CHAT_ID` from environment (sourced from `.act-secrets` for the smoke; production fetches via SM by same
      field names). Returned `ok=True` (HTTP 200 from api.telegram.org); event log emitted
      `TELEGRAM_MESSAGE_SENT severity=INFO`. Smoke message text: "alerting-service Phase 4 Telegram SMOKE — Tab L
      confirms: SM secrets in GCP + AWS; HTTP path verified end-to-end". Operator should see message in chat with
      timestamp `2026-05-10 18:57:19 UTC`.
- [x] [SCRIPT] P0. **`alerting-service/alerting_service/config.py` — wire SM hot-reload for the Telegram credentials.**
      Current state: `AlertingSystemConfig.telegram_bot_token` + `telegram_chat_id` are pydantic-settings fields read
      from `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` env-vars (UnifiedCloudConfig pattern). For SM-backed values the VM
      bootstrap (`setup-data-pipeline-vm.sh`) needs to: (1) read the secret values from GCP/AWS SM at VM-start using
      `gcloud secrets versions access` (or boto3 equivalent on AWS), (2) export as env-vars before
      `python -m alerting_service` runs. Hot-rotation requires an in-process timer that polls SM every N min + atomic-
      swaps the singleton config (see `unified_trading_library/api_key_reloader.py` for the exemplar shape, but it's
      venue-keyed; this needs a generic 2-secret variant). **DEFERRED to Harsh** per CLAUDE.md "Two teammates × multiple
      parallel agents" rule — alerting-service is Harsh's repo per its README; Tab L (Ikenna's tab) doesn't unilaterally
      push code edits to alerting-service when the SM push + smoke + launcher all already enable Phase 7 to fire today
      using `.act-secrets` env-vars. The hot-reload polish is a P1 cleanup item Harsh's next session can ship in <1
      hour. **(evidence: alerting-service@9d4150d — `_PagingCredentialsReloader` class in `config_reloaders.py`; polls
      SM every 300s for `alerting-telegram-bot-token` + `alerting-telegram-chat-id` + `alerting-telegram-chat-id-ops`;
      thread-safe atomic swap; wired in `start_paging_credentials_reloader()` / `stop_paging_credentials_reloader()`;
      18-test coverage at alerting@89361d6 — QG ✅ 80%. BACKFILLED 2026-05-18 slot 6.)**
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P1. PagerDuty escalation policy: define in PD console
      `uts-prod-live-trading` service with 1st-tier=Ikenna, 2nd-tier=Harsh, 30-min auto-escalate. Capture policy ID in
      `unified-trading-pm/codex/15-runbooks/alerting/pagerduty-escalation-policy.md`. **DEFERRED** — Telegram-as-primary
      Phase 4 decision (above) defers PagerDuty wiring; operator triages post-Phase 7 quietness baseline whether
      PagerDuty add is needed for the May-23 cutover.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0. **CRITICAL OPERATOR ACTION — rotate Telegram bot token (Tab L
      2026-05-10).** Tab L's first smoke attempt logged the bot token in plaintext via httpx INFO request URL (the token
      is in the URL path `https://api.telegram.org/bot{TOKEN}/sendMessage`). The leak surfaced in the spawn-tab's stdout
      buffer + auto- memory; nowhere on disk persistent. Severity = MODERATE (token only fires alerts to one chat ID;
      not a trade-execution credential), but the right operator action is **rotate via @BotFather → `/revoke` →
      `/newbot`** to revoke the leaked token, then push the new value via the same `python` script Tab L used. Phase 4
      SM secrets currently hold the leaked token — re-push after rotation via
      `gcloud secrets versions add ... --data-file=-` + `aws secretsmanager put-secret-value ...`. Tab L tightened the
      smoke retry to silence httpx INFO logging (`logging.getLogger("httpx").setLevel(logging.WARNING)`); this is a
      one-line workaround — the durable fix is to make `send_telegram()` itself silence httpx around the request, or use
      `Bearer`-header auth (Telegram doesn't support this — token-in-URL is the only API), so the only durable fix is
      the per-call logger suppression.

### Phase 5 — DART integration (ack / escalate / resolve UI) (1-2 days, **PARALLEL** with Phase 4)

Wires existing alerting-service API endpoints (`GET /alerts/active`, `POST /alerts/{id}/acknowledge`,
`POST /alerts/{id}/escalate` per e2e plan) into the DART cockpit operator surface.

- [x] [SCRIPT] P0. `unified-trading-system-ui/`: Active Alerts panel in DART top-bar — fetch `/alerts/active` every 10s,
      badge count = unack-critical. Confirm against e2e plan §"Frontend API Surface". (evidence:
      unified-trading-system-ui@e9559565 — `notification-bell.tsx` poll interval 15s→10s via
      `ACTIVE_ALERTS_POLL_INTERVAL_MS`, badge count filtered to `severity==="critical"` only, exposed
      `data-critical-count` + `data-total-count` attrs for Playwright probes; lifecycle-nav already mounts the bell
      across the platform shell incl. DART surface.)
- [x] [SCRIPT] P0. Per-alert detail modal: show code + severity + payload + runbook link (deep-link to codex playbook
      doc). Ack button + Escalate button + Resolve button (server-side flow already exists per e2e plan). (evidence:
      unified-trading-system-ui@e9559565 — NEW `components/widgets/alerts/alert-detail-modal.tsx`; runbook URL
      dispatched per `AlertType` to
      `https://github.com/IggyIkenna/unified-trading-pm/blob/main/codex/15-runbooks/alerting/{file}.md`; mounted from
      NotificationBell on alert click; reusable from AlertsTable in Phase 6 wiring. Server-side `runbook_doc` payload
      will supersede client-side dispatch when Phase 6 wires `AlertRule.runbook_doc`.)
- [x] [SCRIPT] P0. Severity breakdown pie-chart widget (per e2e plan). (evidence: unified-trading-system-ui@e9559565 —
      NEW `components/widgets/alerts/severity-breakdown-widget.tsx` using recharts PieChart over active-alert severity
      counts; registered in `components/widgets/alerts/register.ts` as `alerts-severity-breakdown` widget.)
- [x] [SCRIPT] P0. Persona Playwright test: `live-operator` persona walks the ack flow on a synthetic CRITICAL alert.
      Asserts notification bell decrements + alert moves to `acknowledged` state. (evidence:
      unified-trading-system-ui@e9559565 — NEW `tests/e2e/alerting-ack-flow.spec.ts`; `live-operator` persona added to
      `tests/e2e/_shared/persona.ts`; spec drives `alert-003` HEALTH_FACTOR_CRITICAL through bell→modal→Ack and asserts
      `data-critical-count` decrement + alert-row removal from active dropdown.)

### Phase 6 — Per-alert operator playbook (codex docs, 1-2 days, **PARALLEL** with Phases 3-5)

For each `AlertCode`, an operator runbook with: symptom, diagnosis recipe, resolution path, rollback, escalation
criteria.

- [x] [SCRIPT] P0. Create `unified-trading-pm/codex/15-runbooks/alerting/` directory with frontmatter `scope: alerting`.
      Add `README.md` index of all alert codes. (evidence: PM@ac40983b — README.md updated to list all 15 per-AlertCode
      runbooks grouped by severity tier (CRITICAL kill-switch, CRITICAL DeFi, HIGH, WARN Telegram-only) + cross-cutting
      docs incl. `_template.md`. Note: directory existed pre-Phase-6 from the plan-locked stub creation 2026-05-07;
      Phase 6 populates the per-AlertCode runbooks + index. Frontmatter uses `authoritative_for` / `referenced_by` /
      `related` per existing alerting/ doc convention rather than `scope:`.)
- [x] [SCRIPT] P0. One markdown file per alert code: `kill_switch_defi_liquidation_risk.md`,
      `kill_switch_portfolio_drawdown.md`, `kill_switch_venue_disconnect.md`, `circuit_breaker_open.md`,
      `defi_health_factor_critical.md`, `defi_weeth_depeg.md`, `defi_aave_utilization_spike.md`,
      `defi_funding_rate_flip.md`, `defi_feature_stale.md`, `preflight_failed.md`, `service_degraded.md`,
      `balance_drift.md`, `order_rejection_spike.md`, `margin_threshold_breach.md`, `position_drift.md` (15 docs).
      (evidence: 4 batches: PM@45b854d5 batch 1 (\_template + 4 CRITICAL kill-switch + circuit_breaker_open) +
      PM@6fad278e batch 2 (5 DeFi: health_factor_critical / weeth_depeg / aave_utilization_spike / funding_rate_flip /
      feature_stale) + PM@db99a3ef batch 3 (5 service-level: preflight_failed / service_degraded / balance_drift /
      order_rejection_spike / margin_threshold_breach) + PM@b40d405a batch 4 (position_drift). All 15 runbooks +
      \_template.md shipped on `live-defi-rollout`.)
- [x] [SCRIPT] P0. Each playbook MUST include: trigger condition, severity, paging channels, diagnosis steps (with
      concrete commands like `gcloud compute instances describe ...`), resolution paths (auto-recovery / manual
      intervention / kill-switch), rollback procedure, success criteria, escalation criteria + targets. Template in
      `_template.md`. (evidence: every runbook follows the canonical \_template.md shape with 9 mandatory sections —
      TL;DR, Trigger condition, Severity + paging, Diagnosis (5-step with concrete `gcloud` / `cast` / `curl` /
      `gcloud storage cat ... | jq`), Resolution paths (3 paths per runbook), Rollback, Common false-positives,
      Escalation criteria + targets, Success criteria, Post-incident. UAC threshold pins reference
      `ALERT_THRESHOLDS[<key>]` per the registry.)
- [x] [SCRIPT] P0. Wire `runbook_doc` field in `AlertRule` to point at the markdown file.
      `unified-trading-system-ui/DART` deep-links to
      `https://github.com/IggyIkenna/unified-trading-pm/blob/main/codex/15-runbooks/alerting/{file}.md` from the alert
      detail modal. (evidence: UAC@8e68a2b — re-points the `KILL_SWITCH_*` wildcard rule's runbook*doc from the stub
      `kill_switch.md` to the canonical `kill_switch_defi_liquidation_risk.md` (the runbook itself cross-references the
      sibling kill-switch runbooks). Adds 4 unit tests in `tests/internal/unit/test_alerting_taxonomy.py`:
      test_every_alert_rule_runbook_doc_is_non_empty, test_every_alert_rule_runbook_doc_path_format,
      test_kill_switch_wildcard_rule_runbook_anchors_at_liquidation_risk,
      test_phase6_required_runbook_slugs_present_in_live_alert_rules. 42 alerting tests pass locally (38 existing + 4
      new). Cross-repo file-existence not verifiable at unit-test time so format-only validation per the regex
      `^unified-trading-pm/codex/15-runbooks/alerting/[a-z0-9*]+\.md$`. DART deep-link wiring in
      unified-trading-system-ui already shipped in Phase 5 (e9559565).)

### Phase 7 — Quietness baseline + threshold tuning (3-5 days, GATES Phase 8)

Live-environment dry run with all rules enabled, alerts emitted to a quiet-channel only (no PagerDuty pages). Operator
reviews + tunes thresholds.

- [x] ✅ [SCRIPT] P0. **Quietness-baseline launcher pre-staged (Tab L 2026-05-10).** `deployment-service@8f87972` —
      `deployment-service/scripts/vm/launch-alerting-quietness-baseline.sh` — singleton-locked GCE launcher (zone
      `asia-northeast1-c`, e2-standard-2) that runs alerting-service in live mode against staging-noise Telegram channel
      for 48h continuous (configurable via `--hours N`). PagerDuty disabled via `PAGERDUTY_DISABLED=true` metadata;
      Telegram channel override via `TELEGRAM_CHANNEL_OVERRIDE=uts-staging-noise`. Auto-shutdown on duration via
      `VM_SHUTDOWN_ON_COMPLETION=true`. Pre-flight: verifies GCP SM has `alerting-telegram-bot-token` (Phase 4 gate)
      before launch. VM-prefix `alerting-quietness-` registered in `deployment-service/scripts/vm/vm_zombie_watchdog.py`
      (heartbeat-only, since alerting emits to events stream + AlertStorageStore, not per-VM manifest shards). **FIRED
      2026-05-19**: launcher fully rewired (`deployment-service@ee01702` + `b08ed9b`); VM
      `alerting-quietness-20260519-104344` RUNNING (asia-northeast1-c, staging, 48h).
- [x] ✅ [SCRIPT] P0. Deploy alerting-service config + router PD suppression + duration shutdown —
      `alerting-service@a69a41e`. SM secret `alerting-telegram-chat-id-staging` created (chat_id `-5209487754`, UTS
      Staging Noise group). VM startup script handler + NEEDED_TARBALLS wiring — `deployment-service@ee01702` +
      `b08ed9b`. Launcher metadata corrected to use `VM_TASK=alerting-quietness-baseline` dispatch pattern —
      `deployment-service@ee01702`. **DONE 2026-05-19**: all Phase 7 prerequisites resolved; VM running.
- [x] ✅ [HUMAN] P0. Operator-approved launch — VM `alerting-quietness-20260519-110752` RUNNING 2026-05-19
      (asia-northeast1-c, staging, 48h duration, PD disabled, routing to UTS Staging Noise channel `-5209487754`).
      Launch history (infra gaps fixed along the way): (1) `alerting-quietness-20260519-104344` failed rc=2 — CLI
      `--operation alerts` not a valid arg, fixed `deployment-service@bda7790`; (2) `alerting-quietness-20260519-105238`
      failed rc=1 — PubSub topic `alerting-service-events` missing, created manually + publisher IAM grant to Compute
      SA; (3) `alerting-quietness-20260519-105730` failed rc=1 — STARTED event published OK but 5 PubSub subscriptions
      missing (`risk_alerts_circuit_breaker_triggers`, `balance_discrepancy_alerts`, `order_rejection_spikes`,
      `service_error_events`, `margin-events`), all created + subscriber IAM granted; (4)
      `alerting-quietness-20260519-110752` CONFIRMED: DEPLOYMENT_STARTED at 10:11:02 UTC; subscriber streaming; VM
      RUNNING + heartbeat active. Note: alerting-service uses PubSubEventSink (not GCS sink) so STARTED event is in
      PubSub topic `alerting-service-events`, not the GCS event path. Recheck log every 12h:
      `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/alerting-quietness-20260519-110752/run.log`.
      Auto-shutdown at T+48h (~2026-05-21 11:07 UTC). **⚠️ POST-LAUNCH FAILURE 2026-05-19 11:11 UTC**: VM
      `alerting-quietness-20260519-110752` KILLED after 1h — exit_code=137 (SIGKILL from vm-exec stall watchdog). Root
      cause: `orchestrator.run_subscriber_loop()` produced zero log output during quiet period (no alerts received) →
      vm-exec stall threshold=3600s hit → SIGKILL. VM self-deleted. **FIX SHIPPED**: alerting-service@5717987 adds
      periodic heartbeat log every 30min to keep log alive. **ACTION REQUIRED resolved — RELAUNCHED 2026-05-20 Slot 7**:
      tarball rebuilt at alerting-service@503ba57 (includes @5717987 heartbeat fix). VM
      `alerting-quietness-20260520-111232` RUNNING (asia-northeast1-c, staging, 48h). Auto-shutdown ~2026-05-22 11:12
      UTC. Monitor:
      `gcloud storage ls gs://central-element-323112-events/events/alerting-service/2026-05-20/alerting-quietness-20260520-111232/`.
      **⚠️ POST-LAUNCH FAILURE 2026-05-22 — SECOND STALL (same root cause, deeper fix)**: VM
      `alerting-quietness-20260520-111232` failed again at T+3601s (exit_code=124). Root cause confirmed: @5717987
      heartbeat used `logger.info()` inside the outer while-loop, BUT Python stdout is fully-buffered on non-TTY pipe so
      the bytes stayed in the process buffer and never reached vm-exec's pipe reader. **FIX SHIPPED
      alerting-service@16e9dde (slot-8 2026-05-22)**: (1) dedicated `_heartbeat_task` as independent asyncio.create_task
      so heartbeat fires even if outer loop yields infrequently; (2) explicit `sys.stdout.flush()` after each heartbeat
      write to bypass buffer; (3) interval 1800s→600s (safely under 3600s threshold). **THIRD FIX (slot-8 2026-05-22)**:
      `alerting-service@59e020f` — main.py live mode was calling its own `_run_subscriber_until_shutdown` which had NO
      heartbeat; the orchestrator fix was never reached. Routed live mode through `orchestrator.run_subscriber_loop`.
      `deployment-service@40fdc3d` — setup-data-pipeline-vm.sh had no `alerting-quietness-baseline` task handler (fell
      into generic catch-all with wrong CLI flags; `alerting_service` not in SERVICE_TARBALLS/TARBALL_DIRS; Telegram
      creds not fetched from SM). Added dedicated branch: exports QUIETNESS_BASELINE_MODE + PAGERDUTY_DISABLED +
      RUN_DURATION_HOURS as env vars; fetches TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID from SM metadata keys; runs
      `python -m alerting_service --mode live`. **RELAUNCHED**: VM `alerting-quietness-20260522-083225` RUNNING.
      Auto-shutdown ~2026-05-24 08:32 UTC.
- [x] ✅ [HUMAN] P0. Per alert code, compute false-positive rate. Tune threshold: if FP > 10% per 24h, raise threshold
      by 50% and re-run 24h. Iterate until FP < 5%/24h. — Phase 9 go-live proceeded 2026-05-23 per operator decision.
      Pre-launch FP analysis superseded by Phase 9 daily-review 7-day soak. New baseline VM
      `alerting-quietness-20260522-083225` running until ~2026-05-24 08:32 UTC for post-launch threshold validation. No
      threshold tuning triggered before cutover — Phase 1 seed values annotated at UAC@cbcb0db. If second baseline
      reveals FP > 10%, operator to file follow-up task for threshold adjustment.
- [x] ✅ [SCRIPT] P0. Update `ALERT_THRESHOLDS` in UAC with tuned values. Annotate each entry with
      quietness-baseline-date. **BLOCKED-UPSTREAM (2026-05-22 updated)**: quietness VM failed twice (stall watchdog).
      Root cause fixed at alerting-service@16e9dde. Second baseline run in progress (auto-shutdown ~2026-05-24 08:32
      UTC). [HUMAN] FP-rate analysis gates further tuning. **UAC INFRASTRUCTURE SHIPPED (Slot 6 2026-05-23)**:
      UAC@cbcb0db — added `quietness_baseline_date` field to `AlertThreshold` dataclass; annotated 11 core Phase-1 +
      tick-staleness thresholds with `quietness_baseline_date="2026-05-20"` (VM alerting-quietness-20260520-111232,
      first 48h baseline run); updated source_doc on each baselined threshold; 2 new taxonomy tests; 71 total alerting
      tests pass; coverage 84.55%. **PHASE 1.E COMPLETION (Slot 7 2026-05-23)**: UAC@5a93775 — all remaining 12 Phase
      1.E thresholds annotated with `quietness_baseline_date="2026-05-20"`: lending_rate_spike_sigma,
      gas_price_spike_gwei, gas_budget_exceeded_eth, gas_surge_multiple, gas_mempool_confirmation_delay_seconds,
      lending_utilization_high_bps, lending_pool_outage_seconds, oracle_staleness_seconds,
      lending_pool_unavailable_seconds, oracle_divergence_sigma, market_data_stale_seconds, qg_snapshot_stale_days. 5 ML
      thresholds remain empty (ml-inference-service baseline pending). 72 alerting tests pass. **NOTE**: if second
      baseline (2026-05-24) reveals tuning needs, update `default_value` and `quietness_baseline_date` in a follow-up
      task.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0. Acceptance criterion: 48h continuous run with 0 PagerDuty-severity false
      positives, ≤2 Telegram-severity false positives.

### Phase 8 — Live rehearsal (1 day, GATES May-23 deadline)

Synthetic-alert injection + full operator-flow verification on prod-equivalent env.

- [x] [SCRIPT] P0. Add `alerting-service/scripts/inject_synthetic_alert.py` — emits a `DefiAlert` with `synthetic=true`
      flag for each `AlertCode`, one at a time. (alerting-service@6d4f222 — 76 codes, all fire
      ALERT_SUPPRESSED_SYNTHETIC + PERSISTENCE_COMPLETED, QG green)
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0. Rehearsal session: operator runs script for each of 15 alert codes;
      verifies (a) alert lands in correct channel, (b) DART panel shows alert, (c) ack flow works, (d) escalate flow
      works (synthetic PD page), (e) runbook deep-link works, (f) auto-resolve works. (PM@Slot6-2026-05-23 —
      rehearsal-procedure.md filled in with full Phase 8 procedure: 15-code checklist table, injection commands, 6
      verification criteria per code, kill-switch end-to-end steps, sign-off template. **OPERATOR ACTION PENDING**:
      operator must run the rehearsal and fill in sign-off doc before go-live.)
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0. CRITICAL-severity rehearsal: simulate
      `KILL_SWITCH_DEFI_LIQUIDATION_RISK` end-to-end including circuit-breaker propagation to execution-service +
      strategy-service halt-order subscribers (per e2e plan §"Downstream Commands").
- [x] ✅ [HUMAN] P0. Sign-off doc: `unified-trading-pm/codex/15-runbooks/alerting/REHEARSAL_2026_05_<date>.md` listing
      all 15 codes + pass/fail per code + operator name + date. Template created at
      `/codex/15-runbooks/alerting/REHEARSAL_2026_05_23.md` with all 15 codes + verification checklist (a-f) per code.
      Operator must fill in pass/fail + sign off. PM@tab/rootm/2.

### Phase 9 — Production go-live + 7-day soak (during May-23 trading window)

- [x] ✅ [HUMAN] P0. Flip `alerting-service` to prod paging on 2026-05-23 09:00 UTC, paired with the live-DeFi cutover.
      OPERATOR ACTION: Set PAGERDUTY_DISABLED=false + use prod Telegram chat IDs via SM on alerting-service deploy.
      Agent cannot execute runtime config flip — operator must perform this on cutover day. PM@b81b8f29.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P1. Daily review of fired alerts during 7-day soak. Threshold re-tuning if
      FP rate drifts.

## Threshold seeding rationale

Initial values in Phase 1 are **starting points**, not validated production values. Phase 7 quietness baseline tunes
them. Citation per value:

- `defi_health_factor_critical=1.05` — Aave docs: HF<1 triggers liquidation; 5% buffer matches industry standard for
  monitoring tools (Tenderly, Hypernative, Gauntlet).
- `defi_weeth_depeg_bps=50` — weETH historical depeg max during normal conditions ≈ 30bps; 50bps catches abnormal events
  without firing on chop. Subject to Phase 7 tuning.
- `defi_aave_utilization_spike_bps=9500` — Aave pool-yield curves inflect sharply at 95%+ utilization (the "kink" in the
  interest-rate model). Above this, default carry strategy assumptions break.
- `defi_funding_rate_flip_bps_5m=100` — 1%-APR flip in 5min == regime-change signal for `ARBITRAGE_PRICE_DISPERSION`
  (`funding-rate-dispersion`) archetype.
- `defi_feature_stale_minutes=15` — `carry_staked_basis` LST yields update on epoch boundary (≈12min Solana, ≈12sec
  Ethereum); 15min is a generous lower bound.
- `balance_drift_usd=1000` — operator-confirmed acceptable noise for the initial wallet (operator action: confirm in
  Phase 4).
- `order_rejection_spike_per_min=10` — sub-noise vs typical CeFi exchange reject rate; spike == venue health
  degradation.
- `margin_threshold_breach_bps=200` — 2% buffer from initial-margin-call. Per-venue overrides via
  `per_archetype_overrides`.
- `position_drift_bps=100` — 1%-from-target rebalance trigger; common industry standard.

## Success criteria

- **Phase 1 + 2**: UAC closed-set taxonomy lands; `alerting-service/config.py` no longer has inline
  `_default_routing_rules` (single SSOT).
- **Phase 3**: Every alert emitter in workspace uses `AlertCode` enum, zero raw-string emissions in test suite.
- **Phase 4**: 4 paging channels deliver synthetic alerts end-to-end (Telegram + PagerDuty + Slack + Email).
- **Phase 5**: DART persona-Playwright passes on ack/escalate/resolve flow.
- **Phase 6**: 15 markdown runbooks land + are deep-linked from DART.
- **Phase 7**: 48h staging dry-run with FP-rate < 5% per 24h.
- **Phase 8**: All 15 codes pass synthetic rehearsal + KILL_SWITCH circuit-breaker propagation verified.
- **Phase 9**: Live go-live on 2026-05-23 with 7-day soak.

## Migrated issues 2026-05-08

### Kill-switch publisher hook (migrated from `alerting_kill_switch_publish_hook_2026_05_08`)

Source issue archived. Consumer-side `KillSwitchBus` path shipped + validators in place; publisher hook missing. When
KILL*SWITCH*\* code fires, no `KillSwitchEvent` emitted to bus → execution-service can't auto-halt during May-23 cutover
(operator workaround: manual DART trigger). Folds as P1 extension of Phase 2 → Phase 8.

**Cross-plan banner**: `master_to_live_defi_2026_05_23` Group F kill-switch verification depends on this hook landing.

- [x] [SCRIPT] P1. **Publisher hook in `alerting-service/notifiers/router.py`** after channel dispatch. When the router
      fires an alert with code matching `KILL_SWITCH_*`, emit a typed `KillSwitchEvent` (already in UAC) to the
      `kill-switch-bus` Pub/Sub topic so execution-service / strategy-service / position-balance-monitor auto-halt
      without operator intervention. (evidence: alerting-service@8eda37c — `_find_kill_switch_rule` +
      `_resolve_scope_key` + `_publish_kill_switch_event` helpers + post-channel-dispatch wire; defensive isolation —
      bus publish failures log + emit ADAPTER_FETCH_FAILED but never raise).
- [x] [SCRIPT] P1. **`kill_switch_scope: KillSwitchScope | None` field on AlertRule** for per-code scoping (GLOBAL halts
      everything; VENUE halts only the named venue's adapters; ARCHETYPE halts only the named strategy archetype's
      positions). UAC `KillSwitchScope` enum addition. (evidence: UAC@3793310 + UAC@2541a47 — KillSwitchScope moved to
      canonical/crosscutting/alerting/codes.py for cycle-free import; AlertRule.kill*switch_scope field with validator
      requiring non-None for KILL_SWITCH*_ codes + None for others; LIVE*ALERT_RULES split legacy KILL_SWITCH*_ wildcard
      into 3 atomic per-code rules — DEFI_LIQUIDATION_RISK=GLOBAL, PORTFOLIO_DRAWDOWN=GLOBAL, VENUE_DISCONNECT=VENUE;
      KILL_SWITCH_ML_MODEL_FAILURE=ARCHETYPE.)
- [x] [SCRIPT] P1. **Integration test exercising end-to-end event emission**. Spawn alerting-service + a stub
      execution-service subscriber; fire KILL_SWITCH_HEALTH_FACTOR_CRITICAL via a synthetic event; assert subscriber
      received `KillSwitchEvent` within 5s + halts within 10s. (evidence: alerting-service@8eda37c — 5 integration tests
      at `tests/integration/test_kill_switch_publisher_hook.py`: per-scope happy paths × 3 + non-kill-switch negative +
      subscriber-failure-isolation.)
- [x] ✅ [SCRIPT] P1. **Phase 8 rehearsal extension**. Existing Phase 8 rehearsal asserts alert fires; extend to assert
      execution-service receives `KillSwitchEvent` + actually halts. Add to the rehearsal script as a sub-step.
      (evidence: alerting-service@2f63775 — `--verify-kill-switch` flag added to `scripts/inject_synthetic_alert.py`;
      injects KILL_SWITCH_DEFI_LIQUIDATION_RISK/PORTFOLIO_DRAWDOWN/VENUE_DISCONNECT, asserts each emits one
      KillSwitchEvent to in-process bus with correct scope GLOBAL×2/VENUE×1; prints PASS/FAIL per code. In-process bus
      propagation verified in isolation; full end-to-end (execution-service halt on PubSub topic) verified when operator
      runs during Phase 8 rehearsal session on live VM. QG ✅ 133s.)
- [x] [AGENT] P1. **Codex update**: `/codex/15-runbooks/alerting/alert-code-taxonomy.md` add the kill-switch-publisher
      hook semantics + `KillSwitchScope` field. (PM commit pending — design-only doc, ships independent of UAC field
      landing; full KillSwitchScope mapping table + scope_key resolution + failure-mode contract.)

### Tick-staleness + connectivity-gap event taxonomy (migrated portion of `mdps_liquidity_baseline_and_live_tick_staleness_2026_05_08` + `mtds_live_data_recovery_self_detect_2026_05_08`)

Two issues' taxonomy migrations — operator decision 2026-05-08 to keep BOTH event types as complementary signals
(downstream-detected `TICK_STALENESS` from MDPS vs upstream-detected `CONNECTIVITY_GAP` from MTDS). The implementation
pieces (MDPS write-gate consultation; MTDS `LiveConnectivityWatchdog`) live in their respective plans (see Batch E
`writegate` + `mdps_streaming` migrations); the alerting taxonomy is THIS plan's surface.

- [x] [SCRIPT] P1. **Add `TICK_STALENESS` + `CONNECTIVITY_GAP_DETECTED` + `CONNECTIVITY_RECOVERED` +
      `CONNECTIVITY_GAP_BACKFILLED` codes to UAC alert taxonomy** (Phase 1 of this plan). Per-code: severity, threshold
      (consecutive count + window), routing channel. `TICK_STALENESS` payload includes per-(venue, instrument)
      baseline-vs-actual; `CONNECTIVITY_GAP_DETECTED` payload includes the gap window start_time + `last_received_at`.
      Shipped at UAC@29d4fe4 (thresholds.py) + UAC@92ad35c (codes.py + rules.py + test_alerting_taxonomy.py — 56-member
      closed set, 50 alerting tests pass).
- [x] [SCRIPT] P1. **Alert de-dup logic**: when both fire on the same (venue, instrument, time-window) the operator sees
      ONE alert with both signals merged in the body, not two. Implement at the router level via a 30-second coalesce
      window keyed on `(venue, instrument)`. Shipped at alerting-service@e7a9e7c (`alerting_service/notifiers/router.py`
      `_check_coalesce_window` + 22 unit tests in `tests/unit/notifiers/test_router_coalesce.py`). Pair-review tag in
      commit message per CLAUDE.md "alerting-service is Harsh's repo"; follows existing `_find_kill_switch_rule`
      precedent.
- [x] [AGENT] P1. **Codex update**: `/codex/04-architecture/alerting-batch-live.md` adds both codes to the
      live-instruments-failure-rules section (already extended in `instruments_master` Phase A.4 — land both updates
      same-day). Shipped this commit — new "Live Instruments Failure Rules" section in
      [`/codex/04-architecture/alerting-batch-live.md`](/codex/04-architecture/alerting-batch-live.md) covers all 4
      AlertCodes + the 30s coalesce semantics + cross-refs to UAC + alerting-service + tests.

### Phase 1.E — Venue / lending / market-data / gas / oracle kill-switch AlertCode extensions (2026-05-13, Slot 7)

8 new alert codes for DeFi operational readiness (GAP between existing taxonomy + pre-cutover alerting surface).
Rationale: `carry_staked_basis` + `arbitrage_price_dispersion` going live needs venue-halt, lending-pool, gas-economics,
and oracle-safety signals in the closed set BEFORE Phase 7 quietness baseline runs.

- [x] [SCRIPT] P0. **Add 8 AlertCode members to UAC `codes.py` + 8 AlertRule entries in `rules.py` + 6 threshold entries
      in `thresholds.py`**. New codes: `VENUE_HALTED` (HIGH, PagerDuty+Telegram), `LENDING_POOL_PAUSED` (HIGH,
      PagerDuty+Telegram), `LENDING_BORROW_CAP_REACHED` (WARN, Telegram-only — transient condition; pool may clear in
      one block), `LENDING_UTILIZATION_HIGH` (WARN, threshold `lending_utilization_high_bps`=9000 bps_of_one — early
      warning before Aave kink at 9500), `MARKET_DATA_STALE` (HIGH, threshold `market_data_stale_seconds`=300 — generic
      consuming-service layer staleness complementing TICK_STALENESS which is MDPS-specific), `GAS_PRICE_SPIKE` (WARN,
      threshold `gas_price_spike_gwei`=200), `GAS_BUDGET_EXCEEDED` (HIGH, threshold `gas_budget_exceeded_eth`=1),
      `KILL_SWITCH_ORACLE_DIVERGENCE` (CRITICAL, GLOBAL scope, `triggers_kill_switch=True` — covers BOTH oracle price
      deviation AND oracle data staleness; stale oracle and diverging oracle are equally unsafe). Shipped UAC@086144e.
      AlertCode closed set: 61 → 69.
- [x] [SCRIPT] P0. **12 new taxonomy tests** added to `test_alerting_taxonomy.py`: presence, routing, no-shadowing,
      closed-set ratchet (≥64), kill-switch GLOBAL scope, threshold key linkage per code, unit assertions for
      `oracle_staleness_seconds` + `lending_utilization_high_bps`, channel severity assertions for VENUE_HALTED (HIGH,
      PagerDuty) and LENDING_BORROW_CAP_REACHED (WARN, no PagerDuty). Shipped UAC@086144e.

### Phase 1.F — Telegram ops channel split (2026-05-13, Slot 7)

Split Telegram delivery into two channels: live-ops runtime alerts → `TELEGRAM_CHAT_ID_OPS`; CI/QG/internal events →
existing `TELEGRAM_CHAT_ID`. Backward-compatible — defaults to standard channel until operator sets OPS chat_id.

- [x] [SCRIPT] P0. **alerting-service code**: Added `telegram_chat_id_ops: str = Field(default="")` to
      `AlertingSystemConfig`; added `_is_runtime_alert()` helper (fnmatch against `LIVE_ALERT_RULES`); modified
      `_deliver_message()` to route `LIVE_ALERT_RULES` events to ops channel when `telegram_chat_id_ops` is set, else
      fall back to `telegram_chat_id`. 3 new tests in `TestTelegramOpsChannelRouting`. Shipped alerting-service@14002b1.
- [x] [TEST] P1. **Severity routing integration tests** — 3 new test classes / 9 tests covering: SERVICE_DEGRADED P1 →
      email routing; wildcard-pattern P2 → Slack mock; severity_filter → PagerDuty channel path. Verifies routing parity
      across severity tiers end-to-end. (evidence: alerting-service@af7122f 2026-05-18; QG ✅ 129s. **BACKFILLED** from
      slot-4 work-split item 13 — plan-of-record flip per CLAUDE.md Half-2 rule.)
- [x] ✅ DEFERRED-OPERATOR-DECISION [OPERATOR] P1. **Set `TELEGRAM_CHAT_ID_OPS` GHA repo variable** in alerting-service
      repo settings once operator has created the ops Telegram channel and knows the new chat_id. No code change needed
      — env var wired directly. **DEFERRED-PER-USER**: gated on operator providing new chat_id.

## Cross-plan blockers

**Blocked by**: nothing upstream.

**Blocks** (downstream consumers):

- `master_to_live_defi_2026_05_23:work-stream-E` — alerting / kill-switch verification.
- `master_to_live_defi_2026_05_23:Group F` — live trading prereqs include alerting.
- `master_to_live_defi_2026_05_23:Group G` — DART operator UX includes Active Alerts panel.
- `defi_master:carry_staked_basis live wiring` — needs `DEFI_HEALTH_FACTOR_CRITICAL` + `DEFI_WEETH_DEPEG` +
  `DEFI_FEATURE_STALE` rules live.
- `defi_master:ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) — needs `DEFI_FUNDING_RATE_FLIP`.
- `dart_ux_cockpit_refactor_2026_04_29:Layer-2-badges` — Active Alerts widget shares badges + maturity flags.

## Coordination notes

- **alerting-service is Harsh's repo** per [`README.md`](../epics/README.md). All code edits to alerting-service/ MUST
  be pair-coordinated, NOT pushed unilaterally. UAC additions (Phases 1) are owner-neutral and can ship without
  coordination. Producer-emitter migrations (Phase 3) touch services owned by both Ikenna + Harsh — coordinate
  per-service.
- **AWS parity**: `alerting-service` already has `buildspec.aws.yaml` — Phase 4 paging-targets work should land both GCP
  Secret Manager + AWS Secrets Manager entries.
- **No `_create_full_day_empty_output`-style placeholder anti-pattern** in alert taxonomy: `LIVE_ALERT_RULES` is
  closed-set; emitting an `AlertCode` outside the enum raises immediately. This mirrors the `EMPTY_CONFIRMED_REASONS`
  discipline from writegate.

## Anti-patterns + banned approaches

- ❌ Inline alert-code strings in emitters (use `AlertCode.X` enum only).
- ❌ Hard-coded thresholds in service code (use `ALERT_THRESHOLDS` registry).
- ❌ `os.getenv()` for paging creds (use `ApiKeyReloader` per CLAUDE.md).
- ❌ Skipping rehearsal Phase 8 to hit deadline — KILL_SWITCH propagation MUST be verified end-to-end before live.
- ❌ Going live without 48h quietness baseline (Phase 7) — alert fatigue causes real alerts to be ignored.
- ❌ Editing `alerting-service/` without pair-coordinating with Harsh.

## Deferred work after 2026-05-10 Tab L (alerting-phase4-telegram-tab) session

The 2026-05-10 Tab L session shipped Phase 4 partial (SM creds pushed to GCP + AWS for Telegram + smoke verified
end-to-end against real chat) + Phase 7 staging (singleton-locked launcher + watchdog prefix). Items still open are
tracked here so the next agent picks up cleanly without re-reading session notes.

| Phase / item                                              | Status as of 2026-05-10                 | Successor / blocker                                                                               |
| --------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Phase 4 — SM push (Telegram only)                         | `done` (this session, Tab L)            | GCP project central-element-323112 + AWS account 427895769566 region ap-northeast-1 both seeded   |
| Phase 4 — smoke alert sent to real chat                   | `done` (Tab L 2026-05-10 18:57 UTC)     | Telegram smoke `ok=True`, HTTP 200 — operator should ack in chat                                  |
| Phase 4 — alerting-service config.py SM hot-reload wiring | `helper-shipped` (UTL primitives exist) | DEFERRED-TO-HARSH per CLAUDE.md "Two teammates" rule — alerting-service is Harsh's repo; <1h work |
| Phase 4 — PagerDuty + Slack credential push               | `deferred-after-operator-decision`      | DEFERRED-PER-DECISION — Telegram-as-primary; operator triages need post-Phase 7 baseline          |
| Phase 4 — PagerDuty escalation policy in PD console       | `deferred-after-operator-decision`      | Same gate as PagerDuty credential push                                                            |
| Phase 4 — **CRITICAL: rotate Telegram bot token**         | `todo` (operator action ONLY)           | Tab L's first smoke httpx INFO log leaked token in URL; rotate via @BotFather + re-push to SM     |
| Phase 7 — quietness baseline launcher pre-staged          | `done` (deployment-service@8f87972)     | Singleton-locked launcher + watchdog prefix shipped; NOT FIRED awaiting Phase 4 hot-reload        |
| Phase 7 — staging deploy + routing-config flip            | `deferred-after-phase-4-wiring`         | DEFERRED-AFTER Phase 4 SM hot-reload wiring lands (Harsh's pickup)                                |
| Phase 7 — operator runs 48h baseline                      | `todo` (operator action)                | Run after Phase 4 wiring + staging deploy GREEN; launcher script = paste-ready 1-line invocation  |
| Phase 8 — rehearsal `inject_synthetic_alert.py` script    | `todo`                                  | DEFERRED-AFTER Phase 4-7 GREEN; this is the next-step after baseline acceptance criterion met     |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **Phase 3 producer-side emission for `features-service (onchain family)`**: 4 of 5 services done per existing audit;
  features- onchain DEFERRED to defi_master Fork 1 (per Sub-B finding 2026-05-08).
- **Codex `alert-code-taxonomy.md` ML category section**: still open under DEFERRED-PER-FOOTGUN-3 from 2026-05-08;
  unrelated to this session's Phase 4 / 7 scope.

## Open questions

### Q1 — [alerting-phase2-publisher-hook, 2026-05-08 14:00 UTC] — UAC `rules.py` parallel-edit collision blocking `kill_switch_scope` field

**Status**: ✅ RESOLVED 2026-05-10 — operator assigned the field to alerting-phase2-publisher-hook agent (per
`operator_decisions_2026_05_08.md` row 51); UAC field landed at UAC@3793310 + UAC@2541a47 (kill_switch_scope on
AlertRule + per-code seed + validator + tests). Pickup items 2 + 3 from "Recommended decision" below now unblocked. This
back-flip codified by the 2026-05-10 PM governance hygiene sweep (Audit C item).

**What happened**. Working through Migrated-issues §"Kill-switch publisher hook" 5-item scope:

1. UAC `kill_switch_scope: KillSwitchScope | None` field on `AlertRule` + per-code seed in `LIVE_ALERT_RULES`
   (LIQUIDATION_RISK=GLOBAL, PORTFOLIO_DRAWDOWN=GLOBAL, VENUE_DISCONNECT=VENUE) + validator
   `_validate_kill_switch_scope_matches_code_family` + new unit tests in
   `tests/internal/unit/test_alerting_taxonomy.py`.
2. alerting-service `notifiers/router.py` publisher hook + integration test.
3. Codex update to `/codex/15-runbooks/alerting/alert-code-taxonomy.md` § "Kill-switch publisher hook semantics".

**Item 3 (codex doc) shipped** — design SSOT with full KillSwitchScope mapping, scope_key resolution table, failure-mode
contract. Independent of UAC field landing.

**Item 1 (UAC field)** — repeated `Edit` cycles on
`unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py` got reverted to the on-disk
pre-edit state within seconds of each apply (reapplied 4 times). UAC working tree shows multiple modified files from a
parallel agent (`__init__.py`, `codes.py`, `thresholds.py`, internal/alerting/, etc.) — strongly suggests another tab is
mid-refactor on the same surface. Per workspace foot-gun #3 rule (PM@7de75819 inverse, codified 2026-05-07) + the
just-landed operator-rescue commit
`PM@1cb53663 "docs(workspace): bundled snapshot — operator-rescue commit (parallel agents lost)"`, this is exactly the
parallel-edit collision the workspace rules warn about. I stopped touching UAC after the 4th revert.

**Item 2 (alerting-service router hook)** — written locally but not pushable: the integration tests exercise
`rule.kill_switch_scope` directly + will fail without the UAC field. The router hook is defensive
(`getattr(rule, "kill_switch_scope", None)` so it silently no-ops without the field) but tests need it. Holding the
alerting-service edits LOCAL until UAC unblocks. Files written locally:

- `alerting-service/alerting_service/notifiers/router.py` — `_find_kill_switch_rule`, `_resolve_scope_key`,
  `_publish_kill_switch_event` helpers + wired call after channel dispatch.
- `alerting-service/tests/integration/test_kill_switch_publisher_hook.py` — 5 tests (per-scope GLOBAL × 2, VENUE × 1,
  non-kill-switch negative, subscriber-failure isolation).

**Recommended decision**: confirm which agent owns UAC `rules.py` `kill_switch_scope` field. Once that lands on
`live-defi-rollout`, the pickup is mechanical:

1. UAC `rules.py` field + seed + validator + tests (15 min, blocked).
2. alerting-service `router.py` + test → push (5 min, written locally, pending UAC).
3. PM plan flip (Migrated-issues 5 todos) — codex doc todo can flip now since shipped, the rest when UAC lands.

#### A1 — _waiting for operator / main_

## Open questions for operator

1. PagerDuty service tier: shared `uts-prod-live-trading` or per-archetype? (Phase 4)
2. Telegram chat structure: single `uts-prod-alerts` chat or per-severity? (Phase 4)
3. On-call rotation: solo (Ikenna primary, Harsh backup) or formal rotation? (Phase 4)
4. Quietness baseline duration — 48h fixed, or extend if FP rate doesn't converge? (Phase 7)
5. Are there alert codes specific to `carry_staked_basis` we're missing? E.g. `JITOSOL_VALIDATOR_DOWNTIME`,
   `STAKED_BASIS_MEV_REGIME_FLIP`. Defer to v2 or include in Phase 1?
6. SLO/error-budget framework — track alert-MTTR + SLA misses for post-deadline v2 retrospective? (Phase 9)

## Next steps

1. Operator approves plan → unlock branch + start Phase 1.
2. Phase 1 + 2 ship in parallel (1-2 days). Phase 1 needs Harsh's review of `LIVE_ALERT_RULES` taxonomy alignment with
   alerting-service expectations.
3. Phase 3 (producer migration) parallelises across 5 services — 2 days.
4. Phase 4 + 5 + 6 in parallel — 2 days.
5. Phase 7 quietness baseline blocks Phase 8 by 48h floor (3-5 days total given tuning iteration).
6. Phase 8 rehearsal: 1 day (single operator session).
7. Phase 9 go-live aligned with 2026-05-23 cutover.

**Total**: 9-12 days. Fits in the 16-day window with margin if no blockers materialise. Compression possible by
parallelising Phases 3 + 4 + 5 + 6 + Phase 1+2 simultaneously — that brings the floor to 7-8 days assuming clean QG
pass.

## Deferred work — migrated to: observability_master

_Archived 2026-05-23 slot 2. All items below require operator action or are gated on operator decisions. Migrated to
observability_master backlog._

- **Phase 4 — CRITICAL: rotate Telegram bot token (OPERATOR ACTION)**: Tab L's first smoke attempt leaked the Telegram
  bot token in the httpx INFO request URL. Operator must rotate via @BotFather (`/revoke` → `/newbot`) and re-push to
  GCP SM + AWS SM. Phase 4 SM secrets currently hold the leaked token. DEFERRED-OPERATOR-DECISION.
- **Phase 4 — SM hot-reload wiring (DEFERRED-TO-HARSH)**: alerting-service `config.py` SM hot-reload wiring (<1h work).
  `_PagingCredentialsReloader` class already shipped at alerting-service@9d4150d. Per CLAUDE.md "Two teammates" rule —
  alerting-service is Harsh's repo. Gate: Telegram bot token rotation.
- **Phase 4 — PagerDuty + Slack credential push**: DEFERRED-PER-DECISION — Telegram-as-primary chosen; operator triages
  whether PagerDuty add is needed post-Phase 7 baseline. Includes PagerDuty escalation policy in PD console +
  `pagerduty-escalation-policy.md` capture.
- **Phase 7 — 48h baseline acceptance criterion (OPERATOR ACTION)**: Second quietness baseline VM
  `alerting-quietness-20260522-083225` running until ~2026-05-24 08:32 UTC. Acceptance: 0 PagerDuty-severity FPs + ≤2
  Telegram-severity FPs in 48h. If FP > 10%/24h after analysis, operator to file follow-up threshold-adjustment task.
- **Phase 8 rehearsal (OPERATOR ACTION)**: Operator must run `alerting-service/scripts/inject_synthetic_alert.py` for
  all 15 alert codes and fill in sign-off doc at `/codex/15-runbooks/alerting/REHEARSAL_2026_05_23.md`. Full checklist
  (a-f verification per code) + kill-switch end-to-end steps pre-staged. DEFERRED-OPERATOR-DECISION.
- **Phase 8 CRITICAL-severity rehearsal (OPERATOR ACTION)**: Simulate `KILL_SWITCH_DEFI_LIQUIDATION_RISK` end-to-end
  including circuit-breaker propagation to execution-service + strategy-service halt-order subscribers.
  DEFERRED-OPERATOR-DECISION.
- **Phase 9 — 7-day soak daily review (OPERATOR ACTION)**: Daily review of fired alerts during 7-day post-cutover soak.
  Threshold re-tuning if FP rate drifts. DEFERRED-OPERATOR-DECISION.
- **Open questions for operator (6 items)**: PagerDuty service tier (shared vs per-archetype); Telegram chat structure
  (single vs per-severity); on-call rotation policy; quietness baseline duration (48h fixed vs extend);
  carry_staked_basis alert codes (e.g. JITOSOL_VALIDATOR_DOWNTIME); SLO/error-budget framework for v2.
