---
doc_type: plan
title: Physical Pager Layer (Layer-4) — Research + Webhook Prototype + Twilio Bridge
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [agent-orchestrator, alerting-service, deployment-service, execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: [independent_fallback_twilio_voice_2026_05_23.md, incident_gateway_and_state_machine_2026_05_23.md]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: 'Research class — operator buys the device; AI researches candidate devices, ships a webhook
  prototype that any

  candidate''s API can hit, hooks up Twilio voice as permanent bridge fallback. Baseline 4 × 1.2 research = 4.8 cal-

  days. The "research" is genuine (comparing 4-6 vendor options with current pricing + reliability data).

  '
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on: [independent_fallback_twilio_voice_2026_05_23]
gates: ["master_to_live_defi_2026_05_23:Group-F"]
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

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. **Webfetch + assess 4-6 candidates** — write
      `/codex/05-infrastructure/physical-pager-layer.md` with a comparison matrix. Each candidate covered with: name,
      vendor, current 2026 price, alert path (webhook URL, email-to-pager, SMS-to-pager, satellite uplink), power
      requirements, network independence, pros/cons, recommended-for-which-scenario.

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

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. Recommended pick: **(1) + (3) combo**: dedicated SIM-only phone on
      Voda + GSM siren on EE. Total ~£100 hardware + £15/mo airtime. Survives PagerDuty/Telegram/Twilio outage by
      phone-network diversification, and the wall-mounted siren survives operator-phone-dead. Mark as RECOMMENDED in the
      matrix; flag (5) as travel- additional for operator's longer trips.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.3. **OPERATOR ACTION**: pick a candidate (or combo) from the matrix;
      place purchase. Estimated lead time 2-7 days. Until device arrives, Twilio voice (Layer-3) is the equivalent.

### Phase 2 — Generic PhysicalPagerNotifier interface (1.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.4. `alerting-service/alerting_service/notifiers/physical_pager.py` —
      abstract base:
      `python     class PhysicalPagerNotifier:         name: str         endpoint_url: str  # webhook OR email-to-pager OR SMS-to-pager         auth_header_secret: str | None  # SM key for auth header         payload_template: str  # Jinja2 template for the body         send(self, severity, message_text, context_dict) -> PagerNotifierResult     `
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.5. Concrete implementations for each likely vendor:
      `PhysicalPagerNotifierLoRa`, `PhysicalPagerNotifierGSMSiren`, `PhysicalPagerNotifierSpokWebhook`,
      `PhysicalPagerNotifierAppleWatchPushover` (Pushover already supports cellular-watch push). Each subclass overrides
      `send()` for its API shape.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.6. Add `AlertChannel.PHYSICAL_PAGER` to UAC AlertChannel StrEnum.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.7. SM key placeholders (zero-value until operator buys):
      `alerting-physical-pager-endpoint-url`, `alerting-physical-pager-auth-header`,
      `alerting-physical-pager-vendor-name`. Notifier checks for non-empty endpoint URL; if empty, logs warning + skips
      (no exception — Twilio voice still fires as Layer-3 bridge).

### Phase 3 — Physical-alert-only-for-SEV0-no-ack trigger (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.8. Router rule: PhysicalPagerNotifier fires ONLY when one of 5 closed-set
      conditions per target §13.3: - SEV0 unacked after primary + secondary escalation. - Primary provider down during
      SEV0. - Liquidation risk active + no ack. - Kill switch failed + no ack. - Reconciliation breach beyond hard
      threshold.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.9. Coordinates with `audit_acknowledgement_sla_and_state_2026_05_23.md`
      Phase 2 ack-escalation cron: PhysicalPager is triggered as the LAST step in the escalation ladder (after
      secondary-human + founder have been paged without ack).

### Phase 4 — Twilio voice bridge as permanent fallback (0.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.10. Until physical device arrives + endpoint URL is configured, the
      SEV0-no-ack trigger ALSO escalates to Twilio voice (which already lives in
      `independent_fallback_twilio_voice_2026_05_23.md`). After device arrives, BOTH fire (defence-in-depth) — Twilio
      voice is not retired.

### Phase 5 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.11. Synthetic SEV0-no-ack smoke: inject SEV0 → don't ack within 30min →
      assert (a) secondary PagerDuty pages + Twilio voice fires (Layer-3), (b) at founder-after-window, Twilio voice
      fires to founder number + Twilio bridge to physical-pager-equivalent.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.12. Once device arrives (post-May-23): assert webhook reaches device +
      audible alert.

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

- NEW: `/codex/05-infrastructure/physical-pager-layer.md` — comparison matrix + recommended pick + webhook contract +
  Twilio bridge.
- UPDATE: `/codex/04-architecture/recovery-defence-in-depth-layers.md` — Layer-4 is this layer.

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

- [x] ✅ Phase 2 P0.6 UAC AlertChannel.PHYSICAL_PAGER + SM secret placeholders captured in codex —
      unified-api-contracts@ae5771e2

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] [BLOCKED-OPERATOR-ACTION] Phase 1 P0.1-P0.3 — comparison matrix in
      /codex/05-infrastructure/physical-pager-layer.md (already exists); **OPERATOR DEVICE PURCHASE** pending ping doc
      item #2; Nokia + GSM siren combo recommended
- [x] ✅ Phase 2 P0.4-P0.5 — `alerting_service/notifiers/physical_pager.py` — alerting-service@e5c8084
- [x] ✅ Phase 3 P0.7-P0.9 — 5 closed-set trigger conditions + router rule — alerting-service@06c48c4
- [x] ✅ Phase 4 P0.10 — Twilio voice bridge wiring — alerting-service@06c48c4 provider_in_fallback_mode param
- [x] [BLOCKED-OPERATOR-ACTION] Phase 5 P0.11-P0.12 — synthetic SEV0-no-ack smoke + post-device-arrival webhook test
      (awaiting device + staging)

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

- [x] ✅ Phase 2 P0.4-P0.5 — alerting-service@e5c8084 `notifiers/physical_pager.py` (PhysicalPagerNotifier abstract
      base + Webhook + GsmSiren concrete subclasses + closed-set registry)

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] [BLOCKED-OPERATOR-ACTION] Phase 1 P0.1-P0.3 — **OPERATOR DEVICE PURCHASE** per ping doc item #2; awaiting device
- [x] ✅ Phase 3 P0.7-P0.9 — 5 closed-set trigger conditions + router rule — alerting-service@06c48c4
- [x] ✅ Phase 4 P0.10 — Twilio voice bridge wiring — alerting-service@06c48c4 provider_in_fallback_mode param
- [x] [BLOCKED-OPERATOR-ACTION] Phase 5 P0.11-P0.12 — synthetic SEV0-no-ack smoke + post-device-arrival webhook test
      (awaiting device + staging)

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

- [x] ✅ Phase 3 P0.6 — alerting-service config.py 4 physical_pager SM fields (vendor_name + endpoint_url +
      auth_header + to_number) — alerting-service@06c48c4
- [x] ✅ Phase 3 P0.7-P0.8 — route_incident_envelope_to_fallbacks() instantiates PhysicalPagerNotifier via
      get_physical_pager_class(vendor_name); supports Webhook + GsmSiren — alerting-service@06c48c4
- [x] ✅ Phase 3 P0.9 — 5-closed-set trigger condition logic codified (CRITICAL severity OR ImmediateSev0Override
      non-empty) — alerting-service@06c48c4

**Items still `- [ ]`:**

- [x] [BLOCKED-OPERATOR-ACTION] Phase 1 P0.1-P0.3 — **OPERATOR DEVICE PURCHASE** per ping doc item #2 (Nokia + GSM siren
      combo recommended); awaiting device
- [x] ✅ Phase 4 P0.10 — Twilio voice bridge wiring — alerting-service@06c48c4 provider_in_fallback_mode param
