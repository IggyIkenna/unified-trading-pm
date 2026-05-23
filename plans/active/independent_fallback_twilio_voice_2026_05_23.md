---
title: "Independent Fallback — Twilio Voice/SMS (Layer-3) + Primary Provider Health Probe"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: |
  Infra class — new Twilio notifier subclass + Secret Manager wiring + provider health probe cron + alerting-service
  fallback-route logic. Baseline 6 × 0.8 infra = 4.8 cal-days.
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on:
  - incident_gateway_and_state_machine_2026_05_23
gates:
  - master_to_live_defi_2026_05_23:Group-F
related_plans:
  - incident_gateway_and_state_machine_2026_05_23.md
  - physical_pager_research_and_webhook_prototype_2026_05_23.md
  - audit_acknowledgement_sla_and_state_2026_05_23.md
---

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

- [ ] [HUMAN] P0.1. **OPERATOR**: create a fresh Twilio account separate from any other workspace account; obtain a
      voice-capable phone number in a region matching Ikenna's primary mobile (UK +44 or similar). Estimated cost: $1
      number + $0.013/min voice. Per-month operational cost <$5 under expected SEV0 rate.
- [ ] [SCRIPT] P0.2. Push `alerting-twilio-account-sid`, `alerting-twilio-auth-token`, `alerting-twilio-from-number`,
      `alerting-twilio-to-number-primary` (Ikenna mobile), `alerting-twilio-to-number-secondary` (Harsh mobile),
      `alerting-twilio-to-number-founder` to BOTH GCP `central-element-323112` SM AND AWS `427895769566` region
      `ap-northeast-1` SM (mirror existing Telegram pattern).
- [ ] [HUMAN] P0.3. **CRITICAL**: never log Twilio auth_token in URL or stdout (Phase 4 incident learnings — token leaks
      via httpx INFO logging). Audit `send_twilio_voice()` for `logging.getLogger("httpx").setLevel(WARNING)` before
      first call.

### Phase 2 — Twilio voice + SMS notifiers (1.5 cal-day)

- [ ] [AGENT] P0.4. `alerting-service/alerting_service/notifiers/twilio_voice.py` —
      `send_twilio_voice(to_number,     message_text) → TwilioVoiceResult`. Uses Twilio REST API
      `/Accounts/{sid}/Calls.json` POST. TwiML voice URL hosts the message text via Twilio's `<Say voice="alice">`
      element (no callback infra needed).
- [ ] [AGENT] P0.5. `alerting-service/alerting_service/notifiers/twilio_sms.py` —
      `send_twilio_sms(to_number,     message_text)`. Uses `/Accounts/{sid}/Messages.json` POST.
- [ ] [TEST] P0.6. Unit tests mocking Twilio API; assert URL paths + auth header + payload shape.
- [ ] [SCRIPT] P0.7. Add `AlertChannel.TWILIO_VOICE` + `AlertChannel.TWILIO_SMS` to UAC AlertChannel StrEnum (currently
      PAGERDUTY, TELEGRAM, SLACK, EMAIL, LOG_ONLY → add 2 more).

### Phase 3 — Router fallback logic (1 cal-day)

- [ ] [AGENT] P0.8. `alerting-service/alerting_service/notifiers/router.py` extension — `_in_fallback_mode: bool` flag
      set by health probe. When fallback_mode=True + severity=CRITICAL → route to TWILIO_VOICE + TELEGRAM (skip
      PagerDuty since presumed dead).
- [ ] [AGENT] P0.9. Per-rule TwilioVoice channel in `LIVE_ALERT_RULES`: add to existing CRITICAL rules as belt-and-
      suspenders (PagerDuty + Telegram + TwilioVoice) for the highest-risk codes (KILL*SWITCH*\*,
      LIQUIDATION_RISK_IMMINENT, ALERTING_PROVIDER_DEGRADED, DUAL_FAILURE_DETECTED).

### Phase 4 — Primary provider health probe (1 cal-day)

- [ ] [AGENT] P0.10. `alerting-service/alerting_service/health/provider_health_probe.py` — cron every 60s: - GET
      `https://api.pagerduty.com/services/{service_id}` with auth header — assert 200 OK. - POST a test incident with
      `urgency=low` + `alert_type=test` to `/incidents` then immediately resolve it — assert round-trip <5s. - Check
      Telegram bot health: GET `https://api.telegram.org/bot{token}/getMe` — assert 200 + bot is_bot=True. - On any
      probe fail: `_in_fallback_mode=True`; emit `ALERTING_PROVIDER_DEGRADED` IncidentEnvelope with severity=HIGH (the
      provider is degraded; the system is not failed; reduce alert volume by deduping degradation events to 1/hour).
- [ ] [AGENT] P0.11. Probe metrics: counters for {probe_total, probe_fail, fallback_mode_seconds} expose via Prometheus.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [ ] [HUMAN] P0.12. Synthetic SEV0 smoke: inject `KILL_SWITCH_DEFI_LIQUIDATION_RISK` IncidentEnvelope → assert
      PagerDuty + Telegram + TwilioVoice ALL deliver within 90s. Twilio voice call should ring primary number with Alice
      voice reading the alert summary.
- [ ] [HUMAN] P0.13. Synthetic provider-outage smoke: monkeypatch PagerDuty API to return 503 → assert probe detects
      within 60s → fallback_mode=True → SEV0 routes through TwilioVoice + Telegram only.
- [ ] [HUMAN] P0.14. Game-day: scenario `01_cefi_venue_circuit_breaker_trip.md` with PagerDuty synthetically degraded →
      assert end-to-end Twilio voice alert succeeds.

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

- UPDATE: `codex/03-observability/alerting.md` — add Twilio voice/SMS to channels list; document fallback-mode.
- UPDATE: `codex/04-architecture/recovery-defence-in-depth-layers.md` — Twilio = Layer-3 (permanent fallback).
