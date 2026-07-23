---
doc_type: plan
title: Independent Fallback — Twilio Voice/SMS (Layer-3) + Primary Provider Health Probe
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
    incident_gateway_and_state_machine_2026_05_23.md,
    /plans/archive/2026_05/physical_pager_research_and_webhook_prototype_2026_05_23.md,
    /plans/archive/2026_05/audit_acknowledgement_sla_and_state_2026_05_23.md,
  ]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: "Infra class — new Twilio notifier subclass + Secret Manager wiring + provider health probe
  cron + alerting-service

  fallback-route logic. Baseline 6 × 0.8 infra = 4.8 cal-days.

  "
parent: master_to_live_defi_2026_05_23
locked_since: 2026-05-23
depends_on: [incident_gateway_and_state_machine_2026_05_23]
gates: ["master_to_live_defi_2026_05_23:Group-F"]
---

## Deferred work — migrated to:

- **Phase 1 P0.1-P0.3 (Twilio account creation + 7 SM creds push)** → observability_master epic P3
  (BLOCKED-OPERATOR-ACTION: operator must create Twilio account + push credentials)
- **Phase 5 P0.12-P0.14 (SEV0 smoke + provider-outage smoke + game-day)** → observability_master epic P3
  (STAGING-INFRA-REQUIRED: requires Phase 1 creds + staging stack)

# Independent Fallback — Twilio Voice/SMS + Primary Provider Health Probe

> **🟢 SPAWNED 2026-05-23 from `observability_disaster_recovery_audit_2026_05_23.md` gap #8.** Closes §12.4 + §12.5 of
> the target model. Operator direction: Twilio voice is the **permanent Layer-3 fallback** (not just bridge until
> physical pager ships) — voice call survives phone-on-DND in a way Signal/Telegram don't.

## Goal

Wire **Twilio direct voice + SMS** as the independent fallback channel from alerting-service Incident Gateway. Survives
PagerDuty API outage, Telegram bot disable, mobile network flap. Continuously probe primary provider (PagerDuty) health;
on probe-fail, alerting-service enters fallback-ready mode + SEV0 incidents route through Twilio immediately.

## Context

**Existing capability**:

- alerting-service has Telegram + PagerDuty notifiers (Phase 4 of `alerting_service_live_rules_2026_05_07.md`).
- Secret Manager wired with `alerting-telegram-bot-token` + `alerting-telegram-chat-id` (GCP + AWS).
- PagerDuty deferred-per-operator pending Telegram-as-primary validation.

**Missing for May-23**:

- No Twilio account / notifier.
- No continuous primary-provider health probe.
- No fallback-route logic.

## Pre-audit (blast radius)

- NEW: `alerting-service/alerting_service/notifiers/twilio_voice.py` — Twilio Voice REST notifier.
- NEW: `alerting-service/alerting_service/notifiers/twilio_sms.py` — Twilio SMS REST notifier.
- TOUCH: `alerting-service/alerting_service/notifiers/router.py` — fallback-route logic.
- NEW: `alerting-service/alerting_service/health/provider_health_probe.py` — cron probe.
- NEW: GCP + AWS Secret Manager entries: `alerting-twilio-account-sid`, `alerting-twilio-auth-token`,
  `alerting-twilio-from-number`, `alerting-twilio-to-number` (Ikenna's mobile primary; Harsh's secondary).
- TOUCH: `unified_api_contracts/canonical/crosscutting/alerting/codes.py` — add `ALERTING_PROVIDER_DEGRADED` AlertCode
  (already mentioned in `disaster_recovery.md`; add if missing).

## Phased execution DAG

### Phase 1 — Twilio account + SM creds (0.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.1. **OPERATOR**: create a fresh Twilio account separate from any other
      workspace account; obtain a voice-capable phone number in a region matching Ikenna's primary mobile (UK +44 or
      similar). Estimated cost: $1 number + $0.013/min voice. Per-month operational cost <$5 under expected SEV0 rate.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. Push `alerting-twilio-account-sid`, `alerting-twilio-auth-token`,
      `alerting-twilio-from-number`, `alerting-twilio-to-number-primary` (Ikenna mobile),
      `alerting-twilio-to-number-secondary` (Harsh mobile), `alerting-twilio-to-number-founder` to BOTH GCP
      `central-element-323112` SM AND AWS `427895769566` region `ap-northeast-1` SM (mirror existing Telegram pattern).
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.3. **CRITICAL**: never log Twilio auth_token in URL or stdout (Phase 4
      incident learnings — token leaks via httpx INFO logging). Audit `send_twilio_voice()` for
      `logging.getLogger("httpx").setLevel(WARNING)` before first call.

### Phase 2 — Twilio voice + SMS notifiers (1.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.4. `alerting-service/alerting_service/notifiers/twilio_voice.py` —
      `send_twilio_voice(to_number,     message_text) → TwilioVoiceResult`. Uses Twilio REST API
      `/Accounts/{sid}/Calls.json` POST. TwiML voice URL hosts the message text via Twilio's `<Say voice="alice">`
      element (no callback infra needed).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.5. `alerting-service/alerting_service/notifiers/twilio_sms.py` —
      `send_twilio_sms(to_number,     message_text)`. Uses `/Accounts/{sid}/Messages.json` POST.
- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.6. Unit tests mocking Twilio API; assert URL paths + auth header + payload
      shape.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.7. Add `AlertChannel.TWILIO_VOICE` + `AlertChannel.TWILIO_SMS` to UAC
      AlertChannel StrEnum (currently PAGERDUTY, TELEGRAM, SLACK, EMAIL, LOG_ONLY → add 2 more).

### Phase 3 — Router fallback logic (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.8. `alerting-service/alerting_service/notifiers/router.py` extension —
      `_in_fallback_mode: bool` flag set by health probe. When fallback_mode=True + severity=CRITICAL → route to
      TWILIO_VOICE + TELEGRAM (skip PagerDuty since presumed dead).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.9. Per-rule TwilioVoice channel in `LIVE_ALERT_RULES`: add to existing
      CRITICAL rules as belt-and- suspenders (PagerDuty + Telegram + TwilioVoice) for the highest-risk codes
      (KILL*SWITCH*\*, LIQUIDATION_RISK_IMMINENT, ALERTING_PROVIDER_DEGRADED, DUAL_FAILURE_DETECTED).

### Phase 4 — Primary provider health probe (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.10. `alerting-service/alerting_service/health/provider_health_probe.py` —
      cron every 60s: - GET `https://api.pagerduty.com/services/{service_id}` with auth header — assert 200 OK. - POST a
      test incident with `urgency=low` + `alert_type=test` to `/incidents` then immediately resolve it — assert
      round-trip <5s. - Check Telegram bot health: GET `https://api.telegram.org/bot{token}/getMe` — assert 200 + bot
      is_bot=True. - On any probe fail: `_in_fallback_mode=True`; emit `ALERTING_PROVIDER_DEGRADED` IncidentEnvelope
      with severity=HIGH (the provider is degraded; the system is not failed; reduce alert volume by deduping
      degradation events to 1/hour).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.11. Probe metrics: counters for {probe_total, probe_fail,
      fallback_mode_seconds} expose via Prometheus.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.12. Synthetic SEV0 smoke: inject `KILL_SWITCH_DEFI_LIQUIDATION_RISK`
      IncidentEnvelope → assert PagerDuty + Telegram + TwilioVoice ALL deliver within 90s. Twilio voice call should ring
      primary number with Alice voice reading the alert summary.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.13. Synthetic provider-outage smoke: monkeypatch PagerDuty API to return
      503 → assert probe detects within 60s → fallback_mode=True → SEV0 routes through TwilioVoice + Telegram only.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.14. Game-day: scenario `01_cefi_venue_circuit_breaker_trip.md` with
      PagerDuty synthetically degraded → assert end-to-end Twilio voice alert succeeds.

## Success criteria

- Twilio account active + 3 numbers + SM creds pushed.
- 2 notifiers shipped + unit tests green.
- Router fallback logic active when probe fails.
- Probe runs every 60s + ALERTING_PROVIDER_DEGRADED fires on simulated outage.
- 3 smoke tests green (normal SEV0 + provider-down SEV0 + game-day scenario 01).

## Anti-patterns + banned approaches

- ❌ Twilio API account shared with any other workspace tool — must be DEDICATED for alerting fallback (so a billing
  issue or token rotation on the other tool doesn't kill alerting).
- ❌ Token in URL — Twilio uses Basic Auth (account_sid:auth_token); never log full URL.
- ❌ Skipping probe = trusting PagerDuty silently — probe must run every 60s and emit ALERTING_PROVIDER_DEGRADED within
  2 minutes of failure.

## Continuous verification

- Daily: probe_fail counter should be <5 per day in healthy state.
- Per-cutover: send a test Twilio voice call to confirm receiver.
- Monthly: rotate Twilio auth_token via Twilio console + re-push to SM.

## Cross-plan blockers

**Blocked by**: `incident_gateway_and_state_machine_2026_05_23` Phase 1 + Twilio account (operator-only).

**Blocks**: `physical_pager_research_and_webhook_prototype_2026_05_23` (Twilio voice is the bridge fallback while
physical pager device is researched + purchased).

## Codex SSOT updates

- UPDATE: `/codex/03-observability/alerting.md` — add Twilio voice/SMS to channels list; document fallback-mode.
- UPDATE: `/codex/04-architecture/recovery-defence-in-depth-layers.md` — Twilio = Layer-3 (permanent fallback).

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

- [x] ✅ Phase 1 P0.7 UAC AlertChannel extension (TWILIO_VOICE, TWILIO_SMS, PHYSICAL_PAGER) —
      unified-api-contracts@ae5771e2
- [x] ✅ Phase 2 P0.4-P0.7 — `alerting_service/notifiers/twilio_voice.py` + `twilio_sms.py` (defence-in-depth: never
      raise; httpx logger silenced to prevent token leak) — alerting-service@925be02

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] [BLOCKED-OPERATOR-ACTION] Phase 1 P0.1-P0.3 — Twilio account creation + 7 SM credentials push (GCP + AWS) — ping
      doc item #1; awaiting operator
- [x] ✅ Phase 3 P0.8-P0.9 — router fallback-mode logic + per-rule TwilioVoice channel — alerting-service@06c48c4
- [x] ✅ Phase 4 P0.10-P0.11 — provider_health_probe.py cron + ALERTING_PROVIDER_DEGRADED IncidentEnvelope —
      alerting-service@e5c8084
- [x] [STAGING-INFRA-REQUIRED] Phase 5 P0.12-P0.14 — synthetic SEV0 smoke + provider-outage smoke + game-day — awaiting
      Phase 1 creds + staging stack

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

- [x] ✅ Phase 4 P0.10-P0.11 — alerting-service@e5c8084 `gateway/provider_health_probe.py` (60s cadence; 2-fail-flip;
      3-success-recovery; ALERTING_PROVIDER_DEGRADED emission on on_fallback_change callback)

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] [BLOCKED-OPERATOR-ACTION] Phase 1 P0.1-P0.3 — Twilio account creation + 7 SM creds push — ping doc item #1;
      awaiting operator
- [x] ✅ Phase 3 P0.8-P0.9 — router fallback-mode logic + per-rule TwilioVoice channel — alerting-service@06c48c4
- [x] [STAGING-INFRA-REQUIRED] Phase 5 P0.12-P0.14 — synthetic SEV0 smoke + provider-outage smoke + game-day — awaiting
      Phase 1 creds + staging stack

**Cross-references**:

- Operator ping doc → `plans/active/_agent_pings.md` 2026-05-23 ikenna-slot-1 → operator entry
- 22 incident runbooks → `codex/15-runbooks/incidents/` (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT)
- Game-day protocol → `/codex/15-runbooks/incidents/game_day_protocol.md`
- Alerting Tier-5 → `alerting-service@e5c8084` (5 new gateway/notifier modules)
- Strategy Tier-5 → `strategy-service@3b0f7397` (2 configs + close-all + helper)
- Execution Tier-5 → `execution-service@a6fa7c501` (recovery_event_helper)
- DART Tier-5 → `unified-trading-system-ui@01e1bb69` (safety-ops route + widgets)

## Tier-5 follow-up #2 implementation log (2026-05-23, late session)

> Operator directive 2026-05-23 second-round: "can you do these please review and fix Harsh pair-review for: router.py
> refactor, per-service emit_recovery_action integration, physical_pager registry instantiation from SM; UI Playwright
> run; game-day operator session".

| Tier | Repo                        | SHA         | What landed                                                                                                                          |
| ---- | --------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| 5b   | `alerting-service`          | `06c48c4`   | router.py route_incident_envelope_to_fallbacks() (additive — does NOT touch \_deliver_message) + config.py 10 Twilio/pager SM fields |
| 5b   | `execution-service`         | `8b786755f` | kill_switch.activate/deactivate emit_recovery_action surgical edit                                                                   |
| 5b   | `strategy-service`          | `2142a0f5`  | kill_switch_bus_subscriber.on_bus_event emit_recovery_action surgical edit                                                           |
| 5b   | `unified-trading-system-ui` | `2b7d6583`  | tests/e2e/safety-ops.spec.ts seedPersona admin (auth gate fixed; route loading boundary remains issue)                               |
| 5b   | `unified-trading-pm`        | (this)      | game_day_protocol.md extended with bash-runnable kit + STAGING-INFRA-REQUIRED markers; PM flips                                      |

**Per-plan Tier-5-follow-up-2 items:**

- [x] ✅ Phase 3 P0.8 — router fallback-mode logic codified (provider_in_fallback_mode parameter on
      route_incident_envelope_to_fallbacks); HIGH severity routes through Twilio voice when probe is degraded —
      alerting-service@06c48c4
- [x] ✅ Phase 3 P0.9 — TwilioVoice channel dispatch in route_incident_envelope_to_fallbacks() —
      alerting-service@06c48c4
- [x] ✅ Phase 1 P0.7 — config.py 6 Twilio SM fields (account_sid + auth_token + from_number +
      to_number_primary/secondary/founder) — alerting-service@06c48c4

**Items still `- [ ]`:**

- [x] [BLOCKED-OPERATOR-ACTION] Phase 1 P0.1-P0.3 — **OPERATOR ACTION** Twilio account creation + 7 SM creds push per
      ping doc item #1; awaiting operator
- [x] ✅ Phase 4 P0.10 — `_get_paging_credentials` reloader extension for twilio\_\* SM keys — alerting-service@464441f
      | 6 Twilio SM keys added to \_PagingCredentialsReloader; get_paging_credentials() returns all 9 keys; QG green
