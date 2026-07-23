---
doc_type: codex-runbook
title: Physical Pager Layer (Layer-4)
summary:
  "SSOT for the Layer-4 physical alert device — a dedicated wake-up channel on a DIFFERENT network from the operator's
  primary phone, firing only on 5 closed trigger conditions (SEV0 unacked, alert-provider down, liquidation risk,
  kill-switch failed, reconciliation breach). Vendor-agnostic PhysicalPagerNotifier interface (device swap = SM
  credential swap). Recommended combo: dedicated SIM phone + GSM siren box on different carriers; Twilio voice bridges
  until configured."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service]
scope: [admin, engineer]
tags: [alerting, monitoring, escalation, infrastructure, runbook, observability]
related: [/codex/04-architecture/recovery-defence-in-depth-layers.md]
created: 2026-05-23
authoritative_for: [physical-pager-comparison, webhook-prototype, twilio-bridge]
referenced_by:
  [
    /codex/04-architecture/recovery-defence-in-depth-layers.md,
    plans/active/physical_pager_research_and_webhook_prototype_2026_05_23.md,
    plans/active/independent_fallback_twilio_voice_2026_05_23.md,
  ]
owner: ikenna
last_reviewed: 2026-05-23
code_refs:
cadence: on-demand
verifier: operator
last_executed: never
---

# Physical Pager Layer (Layer-4)

> SSOT for the physical alert device. **Operator-only purchase decision.** This doc maintains the candidate comparison
> matrix; the `PhysicalPagerNotifier` interface in alerting-service is vendor-agnostic so a device swap is a
> SM-credentials swap, not a code change.

## Why this layer exists

Layers 2 + 3 (PagerDuty + Telegram + Twilio voice) all rely on the operator's primary phone. The phone has failure modes
that defeat phone-based alerting:

- Battery dead (not on charger when on-call).
- Phone lost / left in another room.
- Phone on silent / Focus Mode / DND misconfigured.
- Mobile network outage on operator's primary carrier.
- Push notifications delayed by carrier or Apple/Google relay.
- User asleep + phone vibration insufficient to wake.
- User travelling with poor signal.
- Alert provider failure (PagerDuty + Telegram both down).

A dedicated physical device on a **different network from the primary phone** closes the residual gap.

## Trigger conditions (closed set, 5)

Physical alert fires ONLY when one of the following is true (per `disaster_recovery.md` §13.3):

1. SEV0 incident unacked after primary + secondary PagerDuty escalation.
2. Primary alert provider (PagerDuty) is down during a SEV0 incident.
3. Liquidation risk active + no operator ack.
4. Kill switch failed (e.g. `KILL_SWITCH_CANNOT_CONFIRM_CANCEL`) + no ack.
5. Reconciliation breach beyond hard threshold (e.g. `unreconciled_age_seconds > 1800` OR any of the 7 immediate-SEV0
   overrides + no ack).

The physical layer is NOT triggered for every SEV0 — alert fatigue defeats the device's purpose. It is the last-resort
wake-up mechanism.

## Candidate comparison (2026-05-23)

| #   | Candidate                                 | Vendor / Model                          | Price (one-off)      | Monthly fee              | Alert path                           | Network independence                        | Pros                                                            | Cons                                                           | Recommended?          |
| --- | ----------------------------------------- | --------------------------------------- | -------------------- | ------------------------ | ------------------------------------ | ------------------------------------------- | --------------------------------------------------------------- | -------------------------------------------------------------- | --------------------- |
| 1   | Dedicated SIM-only on-call phone          | Nokia 2660 Flip + UK Voda/EE/O2 SIM     | ~£50 + £5 SIM        | £5-10                    | Telegram bot + Twilio voice + SMS    | Different carrier from operator primary     | Cheap; reliable; loud ringtone; DND-bypass works                | Still mobile-network-dependent (single carrier)                | **YES (combo)**       |
| 2   | LoRa pager (mesh network)                 | Meshtastic + ATAK / Spok subscription   | ~$80-150             | $0-15                    | LoRa-mesh push from a base station   | Independent radio network (LoRa 868/915MHz) | Network-independent; long-range; no cellular dependency         | Range limited; needs LoRa base station; less common in UK      | NO (for now)          |
| 3   | GSM siren alarm box                       | Eshion GSM-alarm / DAYTECH M5           | ~£30-50              | £5 SIM                   | SMS-trigger → audible siren          | Different carrier SIM (e.g. Three or EE)    | VERY LOUD (~120dB); wall-mounted; survives operator-phone-dead  | Needs power outlet OR battery backup; SMS latency ~5-15s       | **YES (combo)**       |
| 4   | Cellular smartwatch                       | Apple Watch Ultra (Cellular) + eSIM     | ~£800 + £5/mo        | £5-10                    | PagerDuty app / Pushover push        | Different eSIM carrier                      | Wearable; haptic-bypass-DND; works without phone present        | Expensive; eSIM availability per carrier; daily charge cycle   | OPTIONAL (luxury)     |
| 5   | Satellite messenger / hotspot             | Garmin inReach Mini 2 + Iridium plan    | ~£350 + £15/mo       | £15-50                   | Webhook → Iridium SBD message        | Satellite (independent of all cellular)     | Survives complete cellular outage; works in no-signal locations | Slow latency (1-5min); subscription required; one-way out only | OPTIONAL (for travel) |
| 6   | Pushover Emergency Priority on dumb phone | Existing Pushover + Nokia 2660 + UK SIM | ~£50 (covered above) | $0 (Pushover one-off $5) | Pushover app on the dedicated device | Same as candidate 1                         | Cheap if 1 already in place                                     | App needs to stay running; phone needs Pushover-supported OS   | NO (redundant with 1) |

## Recommended setup

**Combo 1 + 3** for May-23 cutover:

- **Dedicated SIM-only phone** (candidate 1) running Telegram + PagerDuty app on a SIM with a **different carrier** from
  operator's primary mobile (e.g. operator primary on EE → dedicated phone on Three or Voda).
- **GSM siren box** (candidate 3) wall-mounted near sleeping/working area, on its own SIM with a **third carrier** (e.g.
  O2). SMS-triggered from alerting-service `PhysicalPagerNotifier`.

Total: ~£100 hardware + £15/mo airtime. Diversifies across 2 carriers (one for phone, one for siren) + the siren is
audibly different from any phone alert (operator can't mistake it).

**Travel-additional**: Garmin inReach Mini 2 (candidate 5) for when operator travels to no-signal areas (e.g. mountains,
remote properties). Pre-configured webhook → Iridium uplink.

**Future luxury**: cellular smartwatch (candidate 4) if budget allows; haptic-bypass-DND on wrist adds a 4th channel.

## PhysicalPagerNotifier interface

`alerting-service/alerting_service/notifiers/physical_pager.py`:

```python
class PhysicalPagerNotifier(ABC):
    name: str                         # e.g. "gsm_siren_box"
    endpoint_url: str                 # webhook OR SMS-to-pager OR email-to-pager
    auth_header_secret: str | None    # SM key for auth header
    payload_template: str             # Jinja2 template for the body

    @abstractmethod
    def send(self, severity: AlertSeverity, message_text: str,
             context_dict: dict) -> PagerNotifierResult: ...
```

Concrete subclasses ship pre-built per vendor:

- `PhysicalPagerNotifierGSMSiren` — POSTs to gateway service that SMSes the device SIM.
- `PhysicalPagerNotifierLoRa` — POSTs to Meshtastic gateway HTTP API.
- `PhysicalPagerNotifierSpokWebhook` — POSTs to Spok paging carrier webhook.
- `PhysicalPagerNotifierPushover` — uses Pushover Emergency Priority API.

The `AlertChannel.PHYSICAL_PAGER` enum value in UAC routes through whichever notifier is configured per the SM secret
`alerting-physical-pager-vendor-name`.

## SM secret schema

```
alerting-physical-pager-vendor-name:    # closed-set: GSMSiren | LoRa | Spok | Pushover | Twilio (bridge)
alerting-physical-pager-endpoint-url:   # vendor-specific webhook
alerting-physical-pager-auth-header:    # vendor-specific (optional)
alerting-physical-pager-to-number:      # for SMS-trigger devices
```

Until operator buys + configures, the SM keys are empty + notifier no-ops with a warning log. Twilio voice (Layer-3)
serves as the permanent Layer-4 bridge.

## Twilio voice bridge

Even when the physical device is configured, Twilio voice continues to fire alongside (defence-in-depth). Twilio voice
is NOT retired when the physical pager arrives. The two channels are independent:

- Twilio voice: routes via Twilio API; reaches operator's primary mobile (which may have DND-bypass for Twilio number).
- Physical pager: routes via vendor-specific path; reaches dedicated device on different network.

## Testing cadence

- **Monthly**: operator triggers synthetic SEV0-no-ack from DART Safety Ops tab; assert physical device emits audible
  alert; log `last_executed` in this doc's frontmatter.
- **Quarterly**: rotate Twilio auth_token via Twilio console + re-push to SM.
- **Pre-cutover**: send a test alert through every configured PhysicalPagerNotifier subclass; receivers confirm.

## Related

- `04-architecture/recovery-defence-in-depth-layers.md` — the 5+1 layer model; this doc owns Layer-4.
- `plans/active/physical_pager_research_and_webhook_prototype_2026_05_23.md` — implementation plan.
- `plans/active/independent_fallback_twilio_voice_2026_05_23.md` — Layer-3 + bridge.
- `disaster_recovery.md` §13 (target operating model) — physical fallback principles.
