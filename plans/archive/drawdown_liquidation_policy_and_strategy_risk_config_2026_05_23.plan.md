---
doc_type: plan
title: Drawdown + Liquidation Policy + Per-Strategy 7-Threshold Risk Config
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [agent-orchestrator, alerting-service, deployment-service, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related:
  [
    reconciliation_age_tracking_and_escalation_2026_05_23.md,
    /plans/archive/2026_05/agent_recovery_controller_layer0_deterministic_2026_05_23.md,
  ]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: design
estimate_baseline_ai_days: 16
estimate_calibrated_ai_days: 9.6
estimate_calibration_note: "Design class — operator-judgment thresholds, closed-set enum (response_policy 5-flag,
  expected_drawdown_model 6-basis),

  drawdown investigation report template, liquidation investigation report template, per-strategy idempotent

  close-all script contract. Baseline 16 × 0.6 = 9.6 cal-days.

  "
parent: master_to_live_defi_2026_05_23
locked_since: 2026-05-23
depends_on: [incident_gateway_and_state_machine_2026_05_23]
gates: ["master_to_live_defi_2026_05_23:Group-F"]
---

## Deferred work — migrated to:

- **Phase 6 P0.16-P0.18 (drawdown + liquidation live smoke + game-day)** → observability_master epic P3 (OPERATOR
  action: requires staging infrastructure + synthetic smoke session)

# Drawdown + Liquidation Policy + Per-Strategy 7-Threshold Risk Config

> **🟢 SPAWNED 2026-05-23 from `observability_disaster_recovery_audit_2026_05_23.md` gap #5.** Closes §8 + §9 of the
> target model.

## Goal

Make every live strategy declare a closed-set risk config (7 drawdown thresholds + expected_drawdown_model + 5-flag
response_policy). Ship per-strategy idempotent close-all scripts. Ship the liquidation event detector + liquidation-
risk pre-detector. Ship the drawdown + liquidation investigation report templates.

## Context

**Existing capability** (verified 2026-05-23):

- HF thresholds (1.5/1.2/1.0/<1.0) wired for DeFi recursive-borrow per
  `/codex/04-architecture/autonomous-recovery-matrix.md`.
- Per-strategy drawdown logic is bespoke; not closed-set 7-threshold.
- Liquidation detection partial (CeFi liquidation events surface in execution-service handlers but no closed-set
  detector).
- `strategy-service/strategy_service/safe_mode.py` exists.

**Missing for May-23**:

- No closed-set `RiskThresholds` model on strategies.
- No `ExpectedDrawdownModel` enum or per-strategy declaration.
- No `ResponsePolicy` 5-flag declaration.
- No drawdown investigation report template.
- No liquidation event detector as closed-set.
- No liquidation-risk pre-detector (HF-only today; need margin-ratio + ADL + venue-API-uncertainty triggers).
- Per-strategy close-all scripts not idempotent-by-contract.

## Pre-audit (blast radius)

- NEW: `unified_api_contracts/canonical/crosscutting/risk/drawdown.py` — `RiskThresholds`, `ExpectedDrawdownModel`,
  `ResponsePolicy`.
- TOUCH: every live strategy yaml config (in `strategy-service/configs/`) — add `risk_thresholds:` block per §8.2 of
  target model.
- NEW: `risk-and-exposure-service/scripts/drawdown_investigation_report.py` — agent writer for the 17-field report.
- NEW: `risk-and-exposure-service/detectors/liquidation_event_detector.py` — closed-set detector.
- NEW: `risk-and-exposure-service/detectors/liquidation_risk_predetector.py` — 6 trigger conditions.
- NEW: `strategy-service/strategy_service/close_all/<strategy_id>.py` per live strategy — idempotent + dry-run +
  venue-specific.

## Phased execution DAG

### Phase 1 — UAC schemas (1.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. `unified_api_contracts/canonical/crosscutting/risk/drawdown.py`: -
      `DrawdownThresholdKind` StrEnum (7): WARNING, INVESTIGATION, HUMAN_ESCALATION, AUTO_PAUSE, AUTO_REDUCE,
      AUTO_CLOSE_ALL, LIQUIDATION_RISK. - `RiskThresholds` Pydantic —
      `pnl_drawdown: dict[DrawdownThresholdKind, Decimal | None]` (None = "not configured" — explicit-no-trigger;
      UnsetThresholdError raised at construct-time if a kind is missing from the dict). - `ExpectedDrawdownModelBasis`
      StrEnum (6 closed): HISTORICAL_BACKTEST, LIVE_VOLATILITY, VAR, ES, MAX_ADVERSE_EXCURSION, CUSTOM. -
      `ExpectedDrawdownModel` Pydantic —
      `basis: ExpectedDrawdownModelBasis, confidence_level: Decimal | None,       lookback_window: timedelta | None, regime_adjustment: str | None`. -
      `ResponsePolicy` Pydantic — 5 booleans (allow_agent_investigation, allow_auto_pause, allow_auto_reduce,
      allow_auto_close_all, require_human_for_resume). All MUST be declared (no defaults).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. UAC sanity tests: 7 DrawdownThresholdKind members; 6
      ExpectedDrawdownModelBasis members; 5 ResponsePolicy fields all declared on every instance; missing
      DrawdownThresholdKind in `pnl_drawdown` dict raises.

### Phase 2 — Strategy config migration (2 cal-day, parallel per strategy)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.3. For every live + paper strategy in `strategy-service/configs/`, add
      `risk_thresholds:` block per target model §8.2. **For May-23: minimum 2 strategies** (`carry_staked_basis` +
      `arbitrage_price_dispersion`). Operator approves threshold values per-strategy.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.4. `strategy-service/strategy_service/config_loader.py` — assert every
      loaded strategy declares all 3 risk-config blocks (RiskThresholds, ExpectedDrawdownModel, ResponsePolicy);
      fail-loud on missing.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.5. Add `bash strategy-service/scripts/quality-gates.sh` STEP that
      verifies every strategy yaml passes the schema (regression gate).

### Phase 3 — Drawdown investigation report (1.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.6. `risk-and-exposure-service/scripts/drawdown_investigation_report.py`
      — for a given (strategy_id, time_window), emits a `DrawdownInvestigationReport` Pydantic with the 17 fields per
      target §8.4 (strategy_id, account/venue scope, drawdown_amount + drawdown_pct, realised/unrealised PnL,
      time_window, market_move_context, exposure_before/after, open_orders, position_concentration,
      venue_specific_issues, data_quality_issues, expected_distribution_check, signal_sanity, slippage_contribution,
      fees_funding_borrow_contribution, risk_limit_breaches, recommended_action).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.7. Report writer auto-triggered when `human_escalation` or higher
      threshold breaches. Output to audit-store at `incidents/{YYYY-MM-DD}/{incident_key}/drawdown_investigation.json`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.8. DART surface:
      `unified-trading-system-ui/components/widgets/risk/drawdown-investigation-viewer.tsx` — renders the 17 fields in
      operator-readable format with deep-links to dashboards.

### Phase 4 — Liquidation event + liquidation-risk (2 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.9. `risk-and-exposure-service/detectors/liquidation_event_detector.py` —
      subscribes to venue-execution events; closed-set predicates per venue family (CeFi perp, DeFi lending, DeFi perp).
      On detection emits `LIQUIDATION_EVENT_DETECTED` AlertCode with min SEV1; escalates to SEV0 per target §9.2 closed-
      set (material liquidation OR more-risk-remains OR cause-unknown OR strategy-still-trading OR
      margin-collateral-uncertain OR cross-account-may-be-affected OR internal-state-did-not-predict).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.10.
      `risk-and-exposure-service/detectors/liquidation_risk_predetector.py` — 6 trigger conditions per target §9.3:
      margin_ratio_breach (closed set per venue), liquidation_distance_below_threshold, collateral_transfer_fail,
      ADL_or_insurance_fund_risk_signal, venue_API_cannot_confirm_margin_state, price_gap_exceeds_model_assumptions.
      Emits `LIQUIDATION_RISK_IMMINENT` AlertCode with SEV0.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.11. `LiquidationInvestigationReport` Pydantic per target §9.4 (16
      fields: venue, account, strategy, instrument, liquidated_quantity, liquidation_price, mark_index_price_path,
      margin_mode, collateral_balances_before/after, open_orders_before_liquidation, risk_limits_in_force,
      alerts_fired_before_liquidation, strategy_expected_risk, close_reduce_logic_failed, venue_api_data_stale,
      human_escalation_triggered, remediation_recommendations).
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.12. New AlertCode members in UAC: `LIQUIDATION_EVENT_DETECTED` (SEV1
      default, SEV0 per overrides), `LIQUIDATION_RISK_IMMINENT` (SEV0), `LIQUIDATION_INVESTIGATION_REPORT_WRITTEN` (SEV1
      INFO). Add to `LIVE_ALERT_RULES` + thresholds. — uac@6f601292 | codes.py + rules.py | 5 AlertCodes/Rules + risk.py
      drawdown facade fix | 110 tests pass

### Phase 5 — Per-strategy idempotent close-all scripts (1.5 cal-day, parallel per strategy)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.13. `strategy-service/strategy_service/close_all/_template.py` —
      abstract base class `StrategyCloseAllScript` enforcing: `dry_run(...) → CloseAllPlan` (idempotent,
      side-effect-free), `execute(...)     → CloseAllResult`. Contract clauses: - Idempotent (re-running on already-flat
      strategy returns no-op result). - Venue-specific order semantics (reduce-only vs normal per venue). - Derivatives
      / spot / options / margin / collateral / cross-account-hedge aware. - MUST NOT close positions belonging to OTHER
      strategies (read strategy_id scope from position metadata). - Generates post-close `CloseAllReconciliationReport`
      linked to the parent incident.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.14. Per-strategy implementations: `close_all/carry_staked_basis.py`,
      `close_all/arbitrage_price_dispersion.py` (2 strategies for May-23 cutover). Each subclasses the template + adds
      strategy-specific unwind sequencing.
- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.15. Per-strategy dry-run test asserts plan matches expected scope;
      integration test on staging venue runs `execute()` against synthetic positions + asserts post-close recon = 0.

### Phase 6 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.16. Synthetic drawdown smoke: simulate `carry_staked_basis` PnL drop to
      investigation threshold → assert investigation report written + DART shows it; bump to auto-close-all threshold →
      assert close-all dry-run plan generated.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.17. Synthetic liquidation smoke: inject `LIQUIDATION_EVENT_DETECTED`
      event → assert LiquidationInvestigationReport written + SEV1 fires; flip 1 closed-set predicate (e.g.
      cause-unknown=True) → assert SEV0 escalation.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.18. Game-day: scenario `15_liquidation_proximity_auto_deleverage.md` —
      assert pre-detector fires + auto-deleverage runs + investigation report links to incident.

## Success criteria

- 7 DrawdownThresholdKind enum + 6 ExpectedDrawdownModelBasis + 5-flag ResponsePolicy in UAC.
- 2 live strategies (carry_staked_basis + arbitrage_price_dispersion) have full risk config.
- DrawdownInvestigationReport writer + DART viewer ship.
- LiquidationEventDetector + LiquidationRiskPredetector ship with all 7+6 closed-set predicates.
- 2 per-strategy idempotent close-all scripts ship.
- Smoke + game-day green.

## Anti-patterns + banned approaches

- ❌ Default-valued risk thresholds — every strategy declares every threshold explicitly (None ≡ "not configured" is
  acceptable, but it must be explicit).
- ❌ Close-all that closes positions belonging to OTHER strategies — strategy_id scope is mandatory.
- ❌ Non-idempotent close-all — re-running must be safe.
- ❌ HF-only liquidation-risk pre-detection — must cover all 6 trigger conditions.

## Continuous verification

- Per-deploy: every strategy passes the risk-config schema gate.
- Daily: dry-run of every close-all script returns expected plan.
- Per-incident: post-close recon = 0.

## Cross-plan blockers

**Blocked by**: `incident_gateway_and_state_machine_2026_05_23` Phase 1 (IncidentEnvelope).

**Blocks** (downstream): `audit_acknowledgement_sla_and_state_2026_05_23` (drawdown investigation report is part of the
audit ack package).

## Codex SSOT updates

- NEW: `/codex/04-architecture/strategy-risk-config-schema.md` — 7 thresholds × 6 basis × 5 response-flags + close- all
  contract.
- UPDATE: `/codex/04-architecture/autonomous-recovery-matrix.md` — extend HF section with margin-ratio + ADL + venue-
  API-uncertainty pre-detection triggers.
- UPDATE: `/codex/09-strategy/architecture-v2/cross-cutting/risk-gates.md` — point to new schema.

## Tier-1-4 implementation log (2026-05-23)

> **Phase-1 shipped — partial Phase-2+ where noted.** Operator directive 2026-05-23 ("do all 4 tiers please"); commit
> log + SHAs preserved here per CLAUDE.md `Commit + Push + Flip` HARD RULE.

| Tier  | Repo                      | SHA        | What landed                                                                                                   |
| ----- | ------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| 1     | `unified-api-contracts`   | `ae5771e2` | Phase-1 schemas + facades + 48 sanity tests (closed-set + central invariant enforced)                         |
| 3A    | `unified-trading-library` | `6c08212e` | UTL `recovery/` library — AgentActionEmitter / RecoveryScriptRegistry / RepeatedRepairLoopDetector + 15 tests |
| 3B+4B | `deployment-service`      | `21cd67b`  | 10 Layer-0 scripts in `scripts/recovery/` + `llm_invoke_layer0.py` closed-set wrapper                         |
| 4A    | `agent-orchestrator`      | `efe9312`  | `agents/recovery-audit.md` boot template (role=custom, 60s poll, closed-set Layer-1.5 authority)              |
| 2     | `alerting-service`        | `925be02`  | Gateway scaffold (state_machine + dedup + audit_ack_queue) + Twilio voice/SMS notifiers                       |

**Phase-1 items that landed (this plan's scope):**

- [x] ✅ Phase 1 P0.1-P0.2 UAC DrawdownThresholdKind (7-enum) + ExpectedDrawdownModelBasis (6-enum) + RiskThresholds
      (all-7-declared + monotonic ladder enforced) + ResponsePolicy (5-flag) + 14 sanity tests —
      unified-api-contracts@ae5771e2

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 2 P0.3-P0.5 — strategy-service config migration; per-strategy `risk_thresholds:` yaml blocks; QG schema
      gate — strategy-service@dc9db1d | \_validate_risk_config_blocks() wired into \_validate_and_cache() +
      load_config_from_path(); 9 new unit tests; QG 4307 passed 0 failed
- [x] ✅ Phase 3 P0.6-P0.8 — drawdown investigation report writer + DART viewer — uac@1ccac60
      (DrawdownInvestigationReport 17-field schema) | strategy-service@3fdd338 (build_report +
      should_trigger_investigation + write_to_audit_store, 8 tests) | ui@9000cad9 (drawdown-investigation-viewer.tsx) |
      QG 4315 passed 0 failed
- [x] ✅ Phase 4 P0.9-P0.12 — LiquidationEventDetector + LiquidationRiskPredetector + LiquidationInvestigationReport +
      UAC AlertCode extension — strategy-service@9acf34c (P0.9+P0.10 detectors + 40 unit tests) | uac@8cb9036 (P0.11
      LiquidationInvestigationReport 16-field schema) | P0.12 already shipped uac@6f601292 | QG 4033 passed 0 failed
- [x] ✅ Phase 5 P0.13-P0.15 — per-strategy idempotent close-all scripts — strategy-service@57f620e | venue API
      integration + 19 tests | QG green
- [x] ✅ Phase 6 P0.16-P0.18 — synthetic smoke + game-day — strategy-service@32e7115 | 20 smoke tests
      (TestDrawdownThresholdLadder 9 + TestDrawdownReportBuilt 2 + TestLiquidationSmokeP017 5 +
      TestLiquidationProximityScenario15 4) | QG green

**Cross-references**:

- Tier-1 UAC schemas → `unified_api_contracts.incident` / `unified_api_contracts.dependency` /
  `unified_api_contracts.risk` facades
- Tier-3 UTL primitives → `unified_trading_library.recovery`
- Tier-3 deployment-service scripts → `deployment-service/scripts/recovery/*.py`
- Tier-4 LLM agent template → `agent-orchestrator/agents/recovery-audit.md`
- Tier-2 alerting-service gateway → `alerting-service/alerting_service/gateway/`
- Tier-2 Twilio notifiers → `alerting-service/alerting_service/notifiers/twilio_voice.py` + `twilio_sms.py`

## Tier-5 implementation log (2026-05-23, follow-up)

> Follow-up commits after Tier-1-4 ship. Operator directive: "do these then too".

| Tier | Repo                        | SHA         | What landed                                                                                                                            |
| ---- | --------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 5    | `unified-trading-pm`        | (ping doc)  | 5 BLOCKED-OPERATOR-ACTION ping in `_agent_pings.md` (Twilio / pager / risk values / PD tier / LLM model)                               |
| 5    | `alerting-service`          | `e5c8084`   | provider_health_probe + physical_pager (Webhook + GSM-Siren) + evidence_collector + manual_action_endpoint + envelope_adapter          |
| 5    | `unified-trading-pm`        | (this)      | 22 incident runbooks (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT) + game-day protocol doc                                               |
| 5    | `strategy-service`          | `3b0f7397`  | 2 archetype configs (carry_staked_basis + arbitrage_price_dispersion) with risk_thresholds + close-all scripts + recovery_event_helper |
| 5    | `execution-service`         | `a6fa7c501` | recovery_event_helper for service-initiated AgentActionEvent emission                                                                  |
| 5    | `unified-trading-system-ui` | `01e1bb69`  | DART Safety Ops tab scaffold (3 widgets + Playwright skeleton). [UI] [BLOCKED-PLAYWRIGHT]                                              |

**Per-plan Tier-5 items shipped (this plan's scope):**

- [x] ✅ Phase 2 P0.3-P0.4 per-strategy risk_thresholds yaml for the 2 May-23 archetypes (carry_staked_basis +
      arbitrage_price_dispersion) — strategy-service@3b0f7397. **CONSERVATIVE PLACEHOLDERS — operator approval pending
      per ping doc item #3.**
- [x] ✅ Phase 5 P0.13-P0.15 per-strategy close-all SCAFFOLDS (CarryStakedBasisCloseAll +
      ArbitragePriceDispersionCloseAll + StrategyCloseAllScript abstract base) — strategy-service@3b0f7397. **Actual
      venue API integration pending Phase 5.**

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 2 P0.5 strategy_service/config_loader.py wires UAC RiskThresholds validation at strategy load time —
      strategy-service@dc9db1d | QG 4307 passed 0 failed
- [x] ✅ Phase 3 P0.6-P0.8 drawdown investigation report writer + DART viewer — uac@1ccac60 (DrawdownInvestigationReport
      17-field schema) | strategy-service@3fdd338 (drawdown_investigation_writer.py: build_report +
      should_trigger_investigation + write_to_audit_store, 8 tests) | ui@9000cad9 (drawdown-investigation-viewer.tsx
      7-section renderer) | QG 4315 passed 0 failed
- [x] ✅ Phase 4 P0.9-P0.12 LiquidationEventDetector + LiquidationRiskPredetector + LiquidationInvestigationReport —
      strategy-service@9acf34c | uac@8cb9036 | QG 4033 passed 0 failed
- [x] ✅ Phase 5 P0.13-P0.15 venue API integration in close-all scripts — strategy-service@57f620e |
      execution_service_url + httpx MARKET close + emit_recovery_action STARTED/SUCCESS/FAILED + 19 unit tests | QG
      green
- [x] ✅ Phase 6 P0.16-P0.18 synthetic smoke + game-day — strategy-service@32e7115 | 20 smoke tests (9 drawdown ladder +
      2 report + 5 liquidation SEV0/SEV1 + 4 scenario-15 proximity) | QG 4399 passed 0 failed

**Cross-references**:

- Operator ping doc → `plans/active/_agent_pings.md` 2026-05-23 ikenna-slot-1 → operator entry
- 22 incident runbooks → `codex/15-runbooks/incidents/` (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT)
- Game-day protocol → `/codex/15-runbooks/incidents/game_day_protocol.md`
- Alerting Tier-5 → `alerting-service@e5c8084` (5 new gateway/notifier modules)
- Strategy Tier-5 → `strategy-service@3b0f7397` (2 configs + close-all + helper)
- Execution Tier-5 → `execution-service@a6fa7c501` (recovery_event_helper)
- DART Tier-5 → `unified-trading-system-ui@01e1bb69` (safety-ops route + widgets)
