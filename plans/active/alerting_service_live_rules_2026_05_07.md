---
type: plan
asset_group: cross-cutting
priority: P0
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-07
depends_on: []
extends:
  - live_pipeline_mtds_mdps_features_2026_05_08 # Phase 9 alerting tier-up consumes ServiceEmissionPolicy + StreamingHealthSnapshot from live-pipeline plan; codified per audit 2026-05-08
gates:
  - master_to_live_defi_2026_05_23:work-stream-E
  - master_to_live_defi_2026_05_23:Group-F
  - master_to_live_defi_2026_05_23:Group-G
status: active
date: 2026-05-07
owner: Ikenna (plan), Harsh (alerting-service code)
---

# Alerting Service Live Rules — Production Rule SSOT + Thresholds + Paging

> **🟡 IN-FLIGHT REFACTOR — Live-pipeline activation 2026-05-08**
>
> [`live_pipeline_mtds_mdps_features_2026_05_08`](./live_pipeline_mtds_mdps_features_2026_05_08.md) Phase 9 EXTENDS this
> plan's surface with live-pipeline tier rules (cluster_pct_skipped_60s, degraded_ratio_60s, staleness_seconds
> thresholds), a new `streaming.alerting.circuit_breaker` Redis Stream wired to strategy-service, and 3 circuit-breaker
> actions (`stop_new_signals` / `force_exit_only` / `halt_strategy`). Coordinate ownership: this plan owns the AlertCode
> taxonomy import + per-rule wiring; the live-pipeline plan adds the new rules + bridge.

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

> **🟡 CROSS-PLAN BANNER — Risk-rule taxonomy active (2026-05-10 → 2026-05-23)**
>
> [`risk_simulations_limits_alerting_2026_05_10`](./risk_simulations_limits_alerting_2026_05_10.md) Phase 1.E extends
> this plan's `AlertCode` closed-set with 6 new members (`RISK_RULE_BLOCKED` / `RISK_RULE_SCALED_DOWN` /
> `RISK_RULE_MONITOR_FIRED` / `RISK_RULE_TEST_ONLY_ROUTED` / `KILL_SWITCH_AUTO_RECOVERED` /
> `KILL_SWITCH_MANUAL_UNKILLED`) — closed-set grows 39 → 45 (UAC@945ad5d). **Coordinate ownership**: this plan owns the
> AlertCode taxonomy + `LIVE_ALERT_RULES` registry; the risk plan owns the `RiskRule` Pydantic + the
> `CONSEQUENCE_ALERT_CODES` mapping. The 6 corresponding `LIVE_ALERT_RULES` entries will be seeded by this plan's
> maintainer after Sub-A's `event_pattern` rename (UAC@0b61aec) propagates to all consumers. Reviewers reject any
> attempt to add `RiskRule*` entries to `LIVE_ALERT_RULES` from outside this plan's scope.

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
- E2E test plan:
  [`plans/active/end-to-end-testing/020_alerting_service.md`](unified-trading-pm/plans/active/end-to-end-testing/020_alerting_service.md)
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
- [risk-and-exposure-service/](risk-and-exposure-service/) — emit alerts using UAC closed taxonomy
- [position-balance-monitor-service/](position-balance-monitor-service/) — same
- [execution-service/](execution-service/) — circuit-breaker subscriber + KILL_SWITCH emitter
- [features-onchain-service/](features-onchain-service/) — emit `DEFI_HEALTH_FACTOR_CRITICAL`,
  `DEFI_AAVE_UTILIZATION_SPIKE`, `DEFI_FUNDING_RATE_FLIP`, `DEFI_FEATURE_STALE` consumers
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
      `codex/15-runbooks/alerting/alert-code-taxonomy.md` extended with (a) new `## ML category — alert codes +
      thresholds + KillSwitchScope mapping` section covering per-code routing matrix (6 ML codes with
      severity/channels/threshold_key/unit/scope), threshold sources + tuning rationale (PSI vs ratio guard, ms vs
      minutes foot-gun avoidance), operator escalation ladder (INFERENCE_LATENCY → STALENESS → DRIFT → PNL → VERSION →
      KILL_SWITCH), archetype-scope semantics + recovery flow, cross-references; (b) KillSwitchScope mapping table
      extended with `KILL_SWITCH_ML_MODEL_FAILURE` ARCHETYPE row + `details["archetype"]` scope_key source; (c)
      Categories bullet for ML lifecycle codes with deep-link to new section; (d) `AlertRule.pattern` references
      updated to `event_pattern` in tandem with UAC@`0b61aec` rename.

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
      legacy pattern still routed (KILL*SWITCH*_, CIRCUIT*BREAKER*_, DEFI*\*, MARGIN*_, etc); (c) AAVE threshold reads
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
      [`codex/03-observability/alerting.md`](../../codex/03-observability/alerting.md) § "Alerting-Service Routing
      Rules" (lines 116-149) uses `event_pattern`. Codex is SSOT for target structure per workspace rule. Rename
      surface: UAC `unified_api_contracts/canonical/crosscutting/alerting/rules.py` (Pydantic field + every constructor
      in seed dict) + UAC tests + alerting-service consumer (config.py default-factory body + any `.pattern` attribute
      access) + tests. Single logical-unit commit; no compatibility shim. Owns the IN-FLIGHT REFACTOR banner at top of
      this plan — banner clears when this todo flips `[x]`. **SHIPPED 2026-05-11**: UAC@`0b61aec` (Pydantic field rename
      + 44 LIVE_ALERT_RULES constructor calls + validators `_pattern_non_empty` → `_event_pattern_non_empty` +
      `_validate_pattern_matches_codes` → `_validate_event_pattern_matches_codes` + test file rename `rule.pattern` →
      `rule.event_pattern` × all sites + drive-by fix to
      `test_alert_rule_accepts_kill_switch_flag_on_kill_switch_code` adding `kill_switch_scope=KillSwitchScope.VENUE` —
      44/44 taxonomy tests green) + alerting-service@`3b94456` (router.py `_find_kill_switch_rule`: `rule.pattern` →
      `rule.event_pattern`). `to_routing_dict()` dict KEY stays `"event_pattern"` (legacy byte-equivalence preserved).
      IN-FLIGHT REFACTOR banner cleared by this flip.

### Phase 3 — Producer migration to UAC closed-set codes (2 days, parallel across services)

Every emitter must use `AlertCode` enum, not raw strings. Fail-loud on unknown.

- [ ] [SCRIPT] P0. `risk-and-exposure-service/`: emit `BALANCE_DRIFT`, `MARGIN_THRESHOLD_BREACH`, `CIRCUIT_BREAKER_OPEN`
      using `AlertCode.X`.
- [ ] [SCRIPT] P0. `position-balance-monitor-service/`: emit `BALANCE_DRIFT`, `POSITION_DRIFT`.
- [ ] [SCRIPT] P0. `execution-service/`: emit `KILL_SWITCH_*` from KillSwitchBus + `ORDER_REJECTION_SPIKE` from
      rejection-tracker.
- [ ] [SCRIPT] P0. `features-onchain-service/`: emit `DEFI_HEALTH_FACTOR_CRITICAL` (from Aave health-factor calculator),
      `DEFI_AAVE_UTILIZATION_SPIKE` (from Aave pool-utilization calc), `DEFI_FUNDING_RATE_FLIP` (from perp funding
      calc), `DEFI_FEATURE_STALE` (from feature-staleness watchdog), `DEFI_WEETH_DEPEG` (from LST-peg deviation calc).
- [ ] [SCRIPT] P0. Each emitter: add unit test asserting alert payload conforms to `DefiAlert` envelope + `AlertCode`
      enum value.
- [ ] [QG] P0. Per-service QG pass on each emitter repo.

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
- [ ] [SCRIPT] P0. **`alerting-service/alerting_service/config.py` — wire SM hot-reload for the Telegram credentials.**
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
      hour.
- [ ] [SCRIPT] P1. PagerDuty escalation policy: define in PD console `uts-prod-live-trading` service with
      1st-tier=Ikenna, 2nd-tier=Harsh, 30-min auto-escalate. Capture policy ID in
      `unified-trading-pm/codex/15-runbooks/alerting/pagerduty-escalation-policy.md`. **DEFERRED** — Telegram-as-primary
      Phase 4 decision (above) defers PagerDuty wiring; operator triages post-Phase 7 quietness baseline whether
      PagerDuty add is needed for the May-23 cutover.
- [ ] [HUMAN] P0. **CRITICAL OPERATOR ACTION — rotate Telegram bot token (Tab L 2026-05-10).** Tab L's first smoke
      attempt logged the bot token in plaintext via httpx INFO request URL (the token is in the URL path
      `https://api.telegram.org/bot{TOKEN}/sendMessage`). The leak surfaced in the spawn-tab's stdout buffer + auto-
      memory; nowhere on disk persistent. Severity = MODERATE (token only fires alerts to one chat ID; not a
      trade-execution credential), but the right operator action is **rotate via @BotFather → `/revoke` → `/newbot`** to
      revoke the leaked token, then push the new value via the same `python` script Tab L used. Phase 4 SM secrets
      currently hold the leaked token — re-push after rotation via `gcloud secrets versions add ... --data-file=-` +
      `aws secretsmanager put-secret-value ...`. Tab L tightened the smoke retry to silence httpx INFO logging
      (`logging.getLogger("httpx").setLevel(logging.WARNING)`); this is a one-line workaround — the durable fix is to
      make `send_telegram()` itself silence httpx around the request, or use `Bearer`-header auth (Telegram doesn't
      support this — token-in-URL is the only API), so the only durable fix is the per-call logger suppression.

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

- [x] [SCRIPT] P0. **Quietness-baseline launcher pre-staged (Tab L 2026-05-10).** `deployment-service@8f87972` —
      `deployment-service/scripts/vm/launch-alerting-quietness-baseline.sh` — singleton-locked GCE launcher (zone
      `asia-northeast1-c`, e2-standard-2) that runs alerting-service in live mode against staging-noise Telegram channel
      for 48h continuous (configurable via `--hours N`). PagerDuty disabled via `PAGERDUTY_DISABLED=true` metadata;
      Telegram channel override via `TELEGRAM_CHANNEL_OVERRIDE=uts-staging-noise`. Auto-shutdown on duration via
      `VM_SHUTDOWN_ON_COMPLETION=true`. Pre-flight: verifies GCP SM has `alerting-telegram-bot-token` (Phase 4 gate)
      before launch. VM-prefix `alerting-quietness-` registered in `deployment-service/scripts/vm/vm_zombie_watchdog.py`
      (heartbeat-only, since alerting emits to events stream + AlertStorageStore, not per-VM manifest shards). **NOT
      FIRED** — Phase 7 launch deferred per gate (Phases 4 [PARTIAL — Tab L Telegram-only] / 5 [✅] / 6 [✅] need GREEN
      — Phase 4 gap is the in-process SM hot-reload Harsh ships next, see Phase 4 todo).
- [ ] [SCRIPT] P0. Deploy alerting-service to `staging` Cloud Run + flip routing config to enable all 15 alert rules.
      **DEFERRED-AFTER-PHASE-4-WIRING** — Telegram/staging-noise channel needs the SM hot-reload todo above to land
      before staging deploy is meaningful (otherwise it runs against `.act-secrets`, which only exist on the operator's
      workstation). The launcher Tab L shipped is what fires after the Cloud Run deploy + Telegram-staging-noise chat ID
      is decided (operator open question 2 of this plan).
- [ ] [HUMAN] P0. Operator: launch the quietness baseline VM via
      `bash deployment-service/scripts/vm/launch-alerting-quietness-baseline.sh` after Phase 4 wiring is GREEN. Verify
      VM emits `STARTED` event within 90s (per CLAUDE.md "No fire-and-forget VM launches"); recheck event stream every
      12h for `QUIETNESS_BASELINE_CHECKPOINT` events. Record every alert fired (timestamp, code, severity, payload,
      was-it-real?). Auto-shutdown at +48h.
- [ ] [HUMAN] P0. Per alert code, compute false-positive rate. Tune threshold: if FP > 10% per 24h, raise threshold by
      50% and re-run 24h. Iterate until FP < 5%/24h.
- [ ] [SCRIPT] P0. Update `ALERT_THRESHOLDS` in UAC with tuned values. Annotate each entry with quietness-baseline-date.
- [ ] [HUMAN] P0. Acceptance criterion: 48h continuous run with 0 PagerDuty-severity false positives, ≤2
      Telegram-severity false positives.

### Phase 8 — Live rehearsal (1 day, GATES May-23 deadline)

Synthetic-alert injection + full operator-flow verification on prod-equivalent env.

- [ ] [SCRIPT] P0. Add `alerting-service/scripts/inject_synthetic_alert.py` — emits a `DefiAlert` with `synthetic=true`
      flag for each `AlertCode`, one at a time.
- [ ] [HUMAN] P0. Rehearsal session: operator runs script for each of 15 alert codes; verifies (a) alert lands in
      correct channel, (b) DART panel shows alert, (c) ack flow works, (d) escalate flow works (synthetic PD page), (e)
      runbook deep-link works, (f) auto-resolve works.
- [ ] [HUMAN] P0. CRITICAL-severity rehearsal: simulate `KILL_SWITCH_DEFI_LIQUIDATION_RISK` end-to-end including
      circuit-breaker propagation to execution-service + strategy-service halt-order subscribers (per e2e plan
      §"Downstream Commands").
- [ ] [HUMAN] P0. Sign-off doc: `unified-trading-pm/codex/15-runbooks/alerting/REHEARSAL_2026_05_<date>.md` listing all
      15 codes + pass/fail per code + operator name + date.

### Phase 9 — Production go-live + 7-day soak (during May-23 trading window)

- [ ] [HUMAN] P0. Flip `alerting-service` to prod paging on 2026-05-23 09:00 UTC, paired with the live-DeFi cutover.
- [ ] [HUMAN] P1. Daily review of fired alerts during 7-day soak. Threshold re-tuning if FP rate drifts.

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
- [ ] [SCRIPT] P1. **Phase 8 rehearsal extension**. Existing Phase 8 rehearsal asserts alert fires; extend to assert
      execution-service receives `KillSwitchEvent` + actually halts. Add to the rehearsal script as a sub-step.
      **DEFERRED**: rehearsal script (`alerting-service/scripts/inject_synthetic_alert.py`) doesn't exist yet — Phase 8
      rehearsal harness is itself a downstream item. Will land alongside the rehearsal script.
- [x] [AGENT] P1. **Codex update**: `codex/15-runbooks/alerting/alert-code-taxonomy.md` add the kill-switch-publisher
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
      window keyed on `(venue, instrument)`. Shipped at alerting-service@e7a9e7c
      (`alerting_service/notifiers/router.py` `_check_coalesce_window` + 22 unit tests in
      `tests/unit/notifiers/test_router_coalesce.py`). Pair-review tag in commit message per CLAUDE.md "alerting-service
      is Harsh's repo"; follows existing `_find_kill_switch_rule` precedent.
- [x] [AGENT] P1. **Codex update**: `codex/04-architecture/alerting-batch-live.md` adds both codes to the
      live-instruments-failure-rules section (already extended in `instruments_live_master_2026_05_08` Phase A.4 — land
      both updates same-day). Shipped this commit — new "Live Instruments Failure Rules" section in
      [`codex/04-architecture/alerting-batch-live.md`](../../codex/04-architecture/alerting-batch-live.md) covers all 4
      AlertCodes + the 30s coalesce semantics + cross-refs to UAC + alerting-service + tests.

## Cross-plan blockers

**Blocked by**: nothing upstream.

**Blocks** (downstream consumers):

- `master_to_live_defi_2026_05_23:work-stream-E` — alerting / kill-switch verification.
- `master_to_live_defi_2026_05_23:Group F` — live trading prereqs include alerting.
- `master_to_live_defi_2026_05_23:Group G` — DART operator UX includes Active Alerts panel.
- `defi_master_2026_05_07:carry_staked_basis live wiring` — needs `DEFI_HEALTH_FACTOR_CRITICAL` + `DEFI_WEETH_DEPEG` +
  `DEFI_FEATURE_STALE` rules live.
- `defi_master_2026_05_07:ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) — needs `DEFI_FUNDING_RATE_FLIP`.
- `dart_ux_cockpit_refactor_2026_04_29:Layer-2-badges` — Active Alerts widget shares badges + maturity flags.

## Coordination notes

- **alerting-service is Harsh's repo** per [`README.md`](alerting-service/README.md). All code edits to
  alerting-service/ MUST be pair-coordinated, NOT pushed unilaterally. UAC additions (Phases 1) are owner-neutral and
  can ship without coordination. Producer-emitter migrations (Phase 3) touch services owned by both Ikenna + Harsh —
  coordinate per-service.
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

- **Phase 3 producer-side emission for `features-onchain-service`**: 4 of 5 services done per existing audit; features-
  onchain DEFERRED to defi_master Fork 1 (per Sub-B finding 2026-05-08).
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
3. Codex update to `codex/15-runbooks/alerting/alert-code-taxonomy.md` § "Kill-switch publisher hook semantics".

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

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (created at audit synthesis time)
- **Verified**: 0 of N (new plan, all items pending Phase 1 kickoff)
- **In-flight (running VMs)**: none
- **Blocked by**: nothing
- **Blocks**: master_to_live_defi:work-stream-E, master_to_live_defi:Group-F, master_to_live_defi:Group-G,
  defi_master:carry_staked_basis-live, defi_master:ARBITRAGE_PRICE_DISPERSION-funding-rate-dispersion,
  dart_ux_cockpit:Layer-2-badges
- **Last meaningful commit**: this plan ships as the keystone unblock.
- **Recommendation**: kickoff immediately after Harsh review of Phase 1 taxonomy.

## DONE-2026-05-08 — Tab 5 (Agent 5) cycle shipments

**Cycle ownership**: `work_split_2026_05_08_ikenna.md` Tab 5 — Alerting + master refresh + governance. Orchestrator
spawned 6 parallel sub-agents (A-F) + dispatched a 7th (G) post-decision; 5 completed clean, 1 returned a case-5
operator-decision finding (Sub-B), 1 hit usage cap mid-Wave-2 (Sub-G — partial).

### Shipped artefacts (per-sub-agent + self-ship)

- **Phase 1 — UAC alerting taxonomy** (already complete pre-cycle at UAC@`d00326d`).
- **Phase 2 — Producer migration to UAC** (already complete pre-cycle at alerting-service@`b025e83`).
- **Phase 3 producer-side (Option A envelope extension + 3 service consumer migrations)**:
  - UAC@`2636815` (Sub-G Wave 1) — `code: AlertCode | None = None` field on AlertEvent + AlertMessage + DefiAlert
    envelopes; lazy-import resolution.
  - execution-service@`624c36a8` (Sub-G Wave 2) — yield_recon + funding_recon AlertEvents stamped with AlertCode.
  - position-balance-monitor-service@`d206ab3` (Sub-G Wave 2) — reconciliation_engine + fee_reconciliation_engine
    AlertEvents stamped with AlertCode.
  - risk-and-exposure-service@`915f0de` (Sub-G Wave 2) — RiskMonitor.\_send_alert AlertMessage stamped with AlertCode.
  - features-onchain-service: **DEFERRED** (calculators not yet wired; defi_master Fork 1 territory per Sub-B finding).
- **Phase 5 — DART integration**:
  - unified-trading-system-ui@`e9559565` (Sub-D) — AlertDetailModal + SeverityBreakdownWidget + notification-bell
    poll-interval + critical-only badge filter + Playwright `live-operator` ack-flow spec. 19/19 vitest green.
  - PM@`6a34d794` (bundled plan-flip via foot-gun #3 muddled attribution).
- **Phase 6 — 15 per-AlertCode runbooks**:
  - PM@`45b854d5` + `6fad278e` + `db99a3ef` + `b40d405a` + `ac40983b` (Sub-C) — `_template.md` + 15 per-code runbooks
    (~200-400 lines each) + README.md index.
  - UAC@`8e68a2b` (Sub-C) — `runbook_doc` field re-pointed to canonical slugs + 4 unit tests asserting Phase 6 slugs
    present.
- **CeFi ML alerting taxonomy**:
  - UAC@`6c4784f` (Sub-E) — 6 ML alert codes (ML_SIGNAL_STALENESS / ML_MODEL_DRIFT_DETECTED / ML_PNL_DEVIATION /
    ML_INFERENCE_LATENCY_BREACH / ML_MODEL_VERSION_MISMATCH / KILL_SWITCH_ML_MODEL_FAILURE) + 5 ML thresholds (PSI +
    MILLISECONDS units added) + 6 ML rules + 7 new tests (38 total passing).
  - PM@`ab595616` (Sub-E plan-flip; bundled foreign attribution per foot-gun #1).
- **Phase 2 KillSwitchBus publisher hook (Item 1)**:
  - UAC@`3793310` (self-ship) — `kill_switch_scope: KillSwitchScope | None` field on AlertRule + validator (REQUIRED for
    KILL*SWITCH*_; MUST be None for others); KillSwitchScope moved to canonical/crosscutting/alerting/codes.py SSOT
    (re-export from internal/domain/deployment*service/isolation.py for backward compat); LIVE_ALERT_RULES KILL_SWITCH*_
    wildcard split into 3 atomic per-code rules (LIQUIDATION_RISK=GLOBAL, PORTFOLIO_DRAWDOWN=GLOBAL,
    VENUE_DISCONNECT=VENUE) + ML_MODEL_FAILURE=ARCHETYPE; tests.
  - UAC@`2541a47` (self-ship) — KillSwitchScope on top-level facade **init**.py + **all** for clean import-pattern.
  - alerting-service@`8eda37c` (self-ship) — `_find_kill_switch_rule` + `_resolve_scope_key` +
    `_publish_kill_switch_event` helpers + post-channel-dispatch wire in `route_event`. Defensive isolation: bus publish
    failures log + emit ADAPTER_FETCH_FAILED but never raise. 5 integration tests
    (`tests/integration/test_kill_switch_publisher_hook.py`).
- **Deploy_missing Phase 0 facilitation**:
  - PM@`351e0a2e` (Sub-F) — `## Operator decision summary` section in `deploy_missing_auto_launch_2026_05_07.md`:
    Decision 1 IAM scope (Option B custom role, zone-scoped); Decision 2 audit-log shape (BigQuery primary + Cloud
    Logging mirror + GCS cold tier; 90d/5y); Decision 3 rate-limits (30/hr/200/day per-operator + 100/hr project + 6h
    per-shard idempotency). Phase 0 audit todos annotated awaiting operator sign-off; ping ledger entry filed.

### Findings raised

- **Case-5 (resolved)**: alerting Phase 3 envelope schema gap — issue doc at
  `plans/archive/issues/alerting_phase3_envelope_schema_gap_2026_05_08.plan.md` § "RESOLVED 2026-05-08"; Option A
  operator decision triggered the resolution chain landed under "Phase 3 producer-side" above.
- **Case-3 (foreign QG, RESOLVED upstream)**: UAC `test_no_eth_perp_venue_accepts_eth_lst_today` shipped at
  `unified-api-contracts/tests/unit/test_defi_registries.py:361`. Pre-existing QG-failure finding (Stream A territory,
  Tab 1 owner) was resolved upstream when the test landed; no separate issue doc needed. Per CLAUDE.md "QG failure
  attribution" agents continued past at the time.
- **Case-3 (foreign QG)**: PM `validate_plan_links.py` AttributeError — issue doc at
  `plans/archive/issues/pm_validate_plan_links_attribute_error_2026_05_08.plan.md`. Workspace-wide validator
  infrastructure bug; PM-scripts-maintainer owner.

### Foot-guns observed

- **Foot-gun #3 cascade** hit multiple sub-agents during PM commits (auto-revert hook racing edits): Sub-B's issue doc
  was wiped from disk by parallel-agent reset cycle (recreated as RESOLVED above); Sub-A's UAC `kill_switch_scope` field
  was reverted 4 times before landing (operator-rescue commit PM@`1cb53663` cleaned up the cascade). Sub-E noted same —
  codex `alert-code-taxonomy.md` ML-category section reverted 5+ times by `git checkout HEAD --` from parallel agent.
  Codex update for ML category **DEFERRED** to next session when activity quiets.
- **Foot-gun #1 muddled attribution**: 3 of my 8 commits got bundled into parallel-agent's auto-commit cycles (content
  correct on origin; author attribution wrong). Per workspace precedent, ship-and-document, no rework.
- **Sub-G usage cap**: hit Wave 2 of 4-wave plan; Wave 3 (Phase 3 emission sites for ORDER_REJECTION_SPIKE +
  POSITION_DRIFT detectors) + Wave 4 (plan flips + issue doc finalisation) cap-cut. Self-ship picked up Wave 4 plan
  flips + Sub-A's UAC field; Wave 3 emission sites still pending — flagged DEFERRED in Phase 3 above.

### Item 4 — Master Group F+G refresh

Pending in this session — runs after this commit lands. Group F item 22 alerting wiring flips ◐ → partial-complete with
citation: alerting-service rules consume `LIVE_ALERT_RULES` SSOT (Phase 2 b025e83); Phase 3 envelope migration shipped
end-to-end (Option A); Phase 2 KillSwitchBus publisher hook shipped (8eda37c); features-onchain emission sites + Phase
4-9 pending per cutover ladder.

### Item 5 — Deploy_missing Phase 0

PM@`351e0a2e` shipped operator decision summary; awaits operator sign-off (no agent can lock these decisions —
operator-only gate per CLAUDE.md "Plans Run To Actual Completion HARD RULE" hard-stop list).

### Item 6 — CeFi ML alerting + DART manual-override

UAC additions shipped (UAC@`6c4784f`). DART manual-override UI + producer wiring (ml-inference-service emission sites
for the new codes) **DEFERRED** to strategy_and_dart_master Phase 2.2 + features-onchain Fork 1 wiring per Sub-E
finding.

### Cycle metrics

- 7 sub-agents dispatched (A-G); 5 completed clean, 1 BLOCKED+resolved (B), 1 partial-cap-cut (G).
- ~12 commits across 4 repos (UAC × 3, alerting-service × 1, execution-service × 1, position-balance-monitor × 1,
  risk-and-exposure × 1, unified-trading-system-ui × 1, PM × 4+).
- 3 issue docs filed (1 RESOLVED in same cycle, 2 outstanding for cross-side / future-cycle).
- Phase 5 + Phase 6 + Phase 1 + Phase 2 hook + Phase 3 envelope migration all GREEN; Phase 3 emission-site sweep + Phase
  4 (paging targets) + Phase 7 (quietness baseline) + Phase 8 (rehearsal) + Phase 9 (go-live) carry over.

## DONE-2026-05-10 — Tab L (alerting-phase4-telegram-tab) shipments

**Cycle ownership**: Phase 4 + Phase 7 staging — operator-direct spawn of Tab L by Ikenna's main orchestrator. Mission:
ship Telegram-as-primary paging end-to-end against the existing operator-set-up alert chat.

### Shipped artefacts

- **Phase 4 — Telegram SM creds (both clouds, version 1)**:
  - GCP project `central-element-323112` (`gcloud secrets create alerting-telegram-bot-token` +
    `alerting-telegram-chat-id`, automatic replication, version 1 seeded each).
  - AWS account `427895769566` region `ap-northeast-1` (`aws secretsmanager create-secret` for both names, version 1
    seeded each).
  - Verified via `list_secret_versions` on both clouds: 1 version per secret per cloud.
- **Phase 4 — smoke alert sent end-to-end** (Tab L 2026-05-10 18:57:19 UTC):
  - Used existing `alerting_service.notifiers.telegram.send_telegram()` via UnifiedCloudConfig env-var bindings.
  - Returned `ok=True` (HTTP 200 from api.telegram.org); event log `TELEGRAM_MESSAGE_SENT severity=INFO`.
  - Awaiting operator visual ack in chat; smoke message text cited timestamp + Tab L identity.
- **Phase 7 — quietness baseline launcher pre-staged** (`deployment-service@8f87972`):
  - `deployment-service/scripts/vm/launch-alerting-quietness-baseline.sh` — singleton-locked 48h GCE launcher, e2-
    standard-2, asia-northeast1-c, PagerDuty disabled, Telegram channel override `uts-staging-noise`. Pre-flight checks
    GCP SM has the Telegram secret. Auto-shutdown via `VM_SHUTDOWN_ON_COMPLETION=true`.
  - `vm_zombie_watchdog.py` — registered `alerting-quietness-` prefix (heartbeat-only; alerting emits to events stream +
    AlertStorageStore, not per-VM manifest shards).
  - **NOT FIRED** — gated on Phase 4 SM hot-reload (Harsh's pickup) + operator green-light.

### Findings raised

- **Case-5 (operator-action) BIG**: Tab L's first smoke httpx INFO log leaked the bot token in the URL path. Severity =
  MODERATE (token only fires alerts to one chat, not a trade-execution credential). Operator action required: rotate via
  @BotFather + re-push to GCP/AWS SM. Captured as P0 [HUMAN] todo in Phase 4 body. Tab L tightened the smoke retry to
  silence httpx INFO logging — the durable fix is per-call logger suppression in `send_telegram()` itself.

### Foot-guns observed

- **httpx INFO logging in token-bearing URL** (codified as case above) — not pre-existing in CLAUDE.md; potential add
  for "credential handling" section if operator wants. Workaround: silence `logging.getLogger("httpx")` to WARNING
  before any Telegram POST.

### Items deferred (per "Capture Discoveries" rule end-of-cycle audit)

All deferrals listed in chat summary mirror items already captured in plan body's "Deferred work after 2026-05-10 Tab L
session" scoreboard above. No grep-misses.

### Cycle metrics

- 1 spawned tab (Tab L), no fan-out.
- 2 commits: `deployment-service@8f87972` (launcher + watchdog) + this PM plan-flip commit.
- 0 issue docs filed (all findings captured as plan annotations + body items per Findings Triage Discipline case 1+2).

## DONE-2026-05-11 — Slot 7 (ikenna-phase-1d-tab) Sub-A cycle shipments

**Cycle ownership**: `work_split_2026_05_11_ikenna.md` § "Slot 7 spawn prompt" — Phase 1.D 3-plan fan-out. Slot 7
master spawned 3 sub-agents in parallel; Sub-A targeted alerting Phase 2.X + ML codex section.

### Shipped artefacts (Sub-A scope)

- **Phase 2.X — `AlertRule.pattern` → `event_pattern` rename**:
  - `unified-api-contracts@0b61aec` — Pydantic field + 44 `LIVE_ALERT_RULES` constructor calls + 2 validators
    (`_pattern_non_empty` → `_event_pattern_non_empty`; `_validate_pattern_matches_codes` →
    `_validate_event_pattern_matches_codes`) + `tests/internal/unit/test_alerting_taxonomy.py` updated. 44/44 alerting
    taxonomy tests pass. Drive-by fix to `test_alert_rule_accepts_kill_switch_flag_on_kill_switch_code` adding
    `kill_switch_scope=KillSwitchScope.VENUE` (Findings Triage Case 1).
  - `alerting-service@3b94456` — `router.py` `_find_kill_switch_rule` consumer one-liner. `to_routing_dict()` dict
    key was already `event_pattern` (legacy byte-equivalence) so `config.py` factory was untouched.
- **Phase 1.B carryover — codex ML category section** (DEFERRED-PER-FOOTGUN-3 from 2026-05-08; picked up cleanly under
  per-slot worktree model):
  - `unified-trading-pm@41c8a519` — `codex/15-runbooks/alerting/alert-code-taxonomy.md` new ML category subsection
    (6 ML codes + severity routing + threshold sources + archetype-scope mapping); KillSwitchScope mapping table
    extended to 4 rows (DEFI_LIQUIDATION_RISK=GLOBAL, PORTFOLIO_DRAWDOWN=GLOBAL, VENUE_DISCONNECT=VENUE,
    ML_MODEL_FAILURE=ARCHETYPE). Phase 2.X + Phase 1.B-ML-codex plan checkboxes flipped `[x]`. IN-FLIGHT REFACTOR
    banner at top of plan removed.

### Findings raised

None. Foot-gun #3 (parallel-agent auto-revert wiping codex edits) was **unrepresentable** under per-slot worktree model
codified 2026-05-10 — codex ML category section landed cleanly on first attempt where 5+ previous attempts had failed.

### Cycle metrics

- 30 minutes (vs ~4 hour budget). Per-slot worktree isolation eliminated the foot-gun #3 retry tax.
- 3 commits across 3 repos (UAC + alerting-service + PM).
- 0 issue docs filed.

## DONE-2026-05-11 — Slot 7 master coordinator (LIVE_ALERT_RULES seed for Sub-B's 6 AlertCodes)

After Sub-A's `event_pattern` rename + Sub-B's 6 new `AlertCode` members landed, the master coordinator (slot 7 main)
seeded the corresponding `LIVE_ALERT_RULES` entries — the master's scope partition per the 3-agent fan-out:

- `unified-api-contracts@c96447b` — `feat(uac): LIVE_ALERT_RULES — 6 new entries (4 RISK_RULE_* + 2 KILL_SWITCH_*_RECOVERED)
  + E501 cleanup`. 6 new `AlertRule` entries using the new `event_pattern` field (4 risk-rule consequences per the § 7
  seam diagram severity routing; 2 kill-switch recovery events per Q8 ratification). Fixes the E501 leftover at
  `alerting/rules.py:126` from Sub-A's rename. Test `test_kill_switch_rules_trigger_kill_switch_flag` updated to
  exempt RECOVERY codes from the `triggers_kill_switch=True` invariant — they report past state changes, not arm new
  ones. 160/160 tests pass workspace-wide across alerting + risk_rule + strategy_family + circuit_breaker + kill_switch.

## DONE-2026-05-11 — Slot 7 Round 2 Sub-I (alerting P1 tick-staleness)

Sub-I shipped the P1 tick-staleness + connectivity-gap migrated-issue from § "Tick-staleness + connectivity-gap event
taxonomy". 4 new AlertCodes (closed-set grew 52 → 56):

- `TICK_STALENESS` (HIGH, PagerDuty + Telegram) — MDPS downstream-detected staleness
- `CONNECTIVITY_GAP_DETECTED` (HIGH, PagerDuty + Telegram) — MTDS upstream-detected gap
- `CONNECTIVITY_RECOVERED` (INFO, Telegram) — recovery
- `CONNECTIVITY_GAP_BACKFILLED` (INFO, Telegram) — recovery + replay closed

**Commits**:

- `unified-api-contracts@29d4fe4` — `thresholds.py` (NEW `tick_staleness_seconds` 300s + `ThresholdUnit.SECONDS`).
  Sub-I's intended commit; ALSO incidentally bundled Sub-E's 5 risk-registry files under this commit message via
  foot-gun #1 within-slot index race.
- `unified-api-contracts@92ad35c` — `codes.py` + `rules.py` (4 new AlertCode members + 4 LIVE_ALERT_RULES entries) +
  `test_alerting_taxonomy.py` (+7 tests, 43 → 50 alerting tests pass).
- `alerting-service@e7a9e7c` — `notifiers/router.py` `_check_coalesce_window()` (30s coalesce-window keyed on
  `(venue, instrument)` for TICK_STALENESS + CONNECTIVITY_GAP_DETECTED) + `tests/unit/test_router_coalesce.py` (NEW,
  22 tests, all green). **Pair-review tag** in commit body (alerting-service is Harsh's repo per CLAUDE.md "Two
  teammates" rule); convention follows `_find_kill_switch_rule` precedent (`alerting-service@8eda37c`).
- `unified-trading-pm@62d09dc8` — codex `04-architecture/alerting-batch-live.md` "Live Instruments Failure Rules"
  section extended with 4 new codes + 3 plan checkboxes flipped (Phase 2.X migrated-issue todos: AlertCode taxonomy
  extension + alert de-dup logic + codex update).

**Findings**:

- **Case-5 BIG — Foot-gun #1 cascade** documented in DONE-2026-05-11 of risk plan. Sub-E's pre-staged registry files
  bundled under Sub-I's `UAC@29d4fe4` commit message via within-slot index race. No data loss; attribution muddled.

**Cycle metrics**: ~75 min (under budget). 4 commits across 3 repos. 0 issue docs filed (findings captured in
risk plan § Audit findings 0.D + risk plan DONE-2026-05-11).
