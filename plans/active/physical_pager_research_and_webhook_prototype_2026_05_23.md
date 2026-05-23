---
title: "Physical Pager Layer (Layer-4) — Research + Webhook Prototype + Twilio Bridge"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: |
  Research class — operator buys the device; AI researches candidate devices, ships a webhook prototype that any
  candidate's API can hit, hooks up Twilio voice as permanent bridge fallback. Baseline 4 × 1.2 research = 4.8 cal-
  days. The "research" is genuine (comparing 4-6 vendor options with current pricing + reliability data).
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on:
  - independent_fallback_twilio_voice_2026_05_23 # Twilio voice is the permanent bridge while device is selected
gates:
  - master_to_live_defi_2026_05_23:Group-F
related_plans:
  - independent_fallback_twilio_voice_2026_05_23.md
  - incident_gateway_and_state_machine_2026_05_23.md
---

# Physical Pager Layer (Layer-4) — Research + Webhook Prototype + Twilio Bridge

> **🟢 SPAWNED 2026-05-23 from operator directive + `disaster_recovery.md` §13.** Operator-only purchase decision; this
> plan provides the research + working webhook prototype + Twilio bridge so the alert path works the moment the device
> arrives — and works _now_ via Twilio voice (which already survives phone-on-DND).

## Goal

Research 4-6 candidate physical pager devices, produce a comparison matrix with current 2026 pricing + alert-API path +
pros/cons + recommended pick. Ship a generic `PhysicalPagerNotifier` interface in alerting-service that any candidate's
webhook API can hit (drop-in token swap when operator buys). Until the device arrives, Twilio voice (from
`independent_fallback_twilio_voice_2026_05_23.md`) serves as the permanent Layer-4 equivalent — voice survives DND.

## Context

**Why this matters**: phone on silent / battery dead / network outage / push notifications delayed / asleep with phone
too quiet to wake / travelling with poor signal / alert provider failure are all failure modes that defeat phone-based
alerting (Telegram + PagerDuty + Twilio voice all rely on the phone). A dedicated physical device on a different network
adds defence-in-depth.

**Existing capability**: Twilio voice (Layer-3, ships in `independent_fallback_twilio_voice_2026_05_23`) survives DND on
iPhone if it's a recognized contact (operator configures this). Voice still requires mobile signal + battery. A physical
pager closes the residual gap.

## Phased execution DAG

### Phase 1 — Candidate research (1 cal-day)

- [ ] [SCRIPT] P0.1. **Webfetch + assess 4-6 candidates** — write `codex/05-infrastructure/physical-pager-layer.md` with
      a comparison matrix. Each candidate covered with: name, vendor, current 2026 price, alert path (webhook URL,
      email-to-pager, SMS-to-pager, satellite uplink), power requirements, network independence, pros/cons,
      recommended-for-which-scenario.

      Candidates to evaluate:
      - **(1) Dedicated SIM-only on-call phone** (Nokia 2660 Flip or similar — £50, separate carrier from operator's
        primary, always-charged, DND-bypass, loud ringtone): cheap, reliable, but still mobile-network-dependent.
      - **(2) LoRa pager** (e.g. Meshtastic mesh-network pager, ~$80; or commercial Spok pager via paging carrier
        subscription, ~$15/mo): independent network; range limited; subscription required.
      - **(3) GSM siren alarm box with separate SIM** (e.g. Eshion GSM alarm or DAYTECH M5; ~£30-50): wall-mounted,
        very loud, SMS-triggered; survives phone failure entirely; requires SIM card on different carrier.
      - **(4) Cellular smartwatch with dedicated SIM** (Apple Watch Cellular w/ separate eSIM ~£500 + £5/mo; or
        Galaxy Watch LTE): wearable; PagerDuty app installed; expensive.
      - **(5) Satellite messenger / hotspot** (Garmin inReach Mini 2 ~£350 + £15/mo Iridium plan; or Starlink Mini
        + roaming SIM): travel-resilient, works in no-signal; expensive + monthly fee.
      - **(6) Hosted IoT button / panic alarm** (e.g. AlertMedia panic device, RingAlarm with SIM backup): less
        relevant — needs operator action vs alerting operator.

- [ ] [SCRIPT] P0.2. Recommended pick: **(1) + (3) combo**: dedicated SIM-only phone on Voda + GSM siren on EE. Total
      ~£100 hardware + £15/mo airtime. Survives PagerDuty/Telegram/Twilio outage by phone-network diversification, and
      the wall-mounted siren survives operator-phone-dead. Mark as RECOMMENDED in the matrix; flag (5) as travel-
      additional for operator's longer trips.
- [ ] [HUMAN] P0.3. **OPERATOR ACTION**: pick a candidate (or combo) from the matrix; place purchase. Estimated lead
      time 2-7 days. Until device arrives, Twilio voice (Layer-3) is the equivalent.

### Phase 2 — Generic PhysicalPagerNotifier interface (1.5 cal-day)

- [ ] [AGENT] P0.4. `alerting-service/alerting_service/notifiers/physical_pager.py` — abstract base:
      `python     class PhysicalPagerNotifier:         name: str         endpoint_url: str  # webhook OR email-to-pager OR SMS-to-pager         auth_header_secret: str | None  # SM key for auth header         payload_template: str  # Jinja2 template for the body         send(self, severity, message_text, context_dict) -> PagerNotifierResult     `
- [ ] [AGENT] P0.5. Concrete implementations for each likely vendor: `PhysicalPagerNotifierLoRa`,
      `PhysicalPagerNotifierGSMSiren`, `PhysicalPagerNotifierSpokWebhook`, `PhysicalPagerNotifierAppleWatchPushover`
      (Pushover already supports cellular-watch push). Each subclass overrides `send()` for its API shape.
- [ ] [AGENT] P0.6. Add `AlertChannel.PHYSICAL_PAGER` to UAC AlertChannel StrEnum.
- [ ] [SCRIPT] P0.7. SM key placeholders (zero-value until operator buys): `alerting-physical-pager-endpoint-url`,
      `alerting-physical-pager-auth-header`, `alerting-physical-pager-vendor-name`. Notifier checks for non-empty
      endpoint URL; if empty, logs warning + skips (no exception — Twilio voice still fires as Layer-3 bridge).

### Phase 3 — Physical-alert-only-for-SEV0-no-ack trigger (1 cal-day)

- [ ] [AGENT] P0.8. Router rule: PhysicalPagerNotifier fires ONLY when one of 5 closed-set conditions per target
      §13.3: - SEV0 unacked after primary + secondary escalation. - Primary provider down during SEV0. - Liquidation
      risk active + no ack. - Kill switch failed + no ack. - Reconciliation breach beyond hard threshold.
- [ ] [AGENT] P0.9. Coordinates with `audit_acknowledgement_sla_and_state_2026_05_23.md` Phase 2 ack-escalation cron:
      PhysicalPager is triggered as the LAST step in the escalation ladder (after secondary-human + founder have been
      paged without ack).

### Phase 4 — Twilio voice bridge as permanent fallback (0.5 cal-day)

- [ ] [SCRIPT] P0.10. Until physical device arrives + endpoint URL is configured, the SEV0-no-ack trigger ALSO escalates
      to Twilio voice (which already lives in `independent_fallback_twilio_voice_2026_05_23.md`). After device arrives,
      BOTH fire (defence-in-depth) — Twilio voice is not retired.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [ ] [HUMAN] P0.11. Synthetic SEV0-no-ack smoke: inject SEV0 → don't ack within 30min → assert (a) secondary PagerDuty
      pages + Twilio voice fires (Layer-3), (b) at founder-after-window, Twilio voice fires to founder number + Twilio
      bridge to physical-pager-equivalent.
- [ ] [HUMAN] P0.12. Once device arrives (post-May-23): assert webhook reaches device + audible alert.

## Success criteria

- Comparison matrix doc lands with 4-6 candidates + recommended pick.
- PhysicalPagerNotifier interface + 4 vendor subclasses ship in alerting-service.
- AlertChannel.PHYSICAL_PAGER in UAC.
- Router rule fires PhysicalPager only on 5 closed-set conditions.
- Twilio voice bridge fires until device arrives (no gap).
- Synthetic smoke green for SEV0-no-ack ladder.

## Anti-patterns + banned approaches

- ❌ Physical pager on same network as primary phone — defeats the diversification purpose.
- ❌ Physical pager triggered for every SEV0 — operator-alert-fatigue defeats the device's purpose. Only the 5
  closed-set conditions trigger.
- ❌ Skipping the Twilio bridge — must work _now_ (cutover today).

## Continuous verification

- Monthly: physical-pager device test (operator triggers synthetic SEV0-no-ack from DART; assert device alerts).
- Per-device-change: re-run vendor comparison matrix; update doc if pricing/availability changed.

## Cross-plan blockers

**Blocked by**: `independent_fallback_twilio_voice_2026_05_23` (Twilio voice is the bridge).

**Blocks**: none upstream.

## Codex SSOT updates

- NEW: `codex/05-infrastructure/physical-pager-layer.md` — comparison matrix + recommended pick + webhook contract +
  Twilio bridge.
- UPDATE: `codex/04-architecture/recovery-defence-in-depth-layers.md` — Layer-4 is this layer.
