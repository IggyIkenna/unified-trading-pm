---
doc_type: issue
title: alerting-service KillSwitchBus publish-side hook + integration test deferred (Phase 2 closeout gap)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
author: ikenna
source:
  [
    plans/active/alerting_service_live_rules_2026_05_07.md (Phase 2),
    plans/active/work_split_2026_05_07_ikenna_5tab_layout.md (Agent 1 done definition item 2),
    "unified-api-contracts/unified_api_contracts/canonical/crosscutting/alerting/rules.py
    (AlertRule.triggers_kill_switch field, UAC@d00326d)",
    alerting-service/alerting_service/kill_switch_bus_subscriber.py (consumer-side only),
    alerting-service/alerting_service/notifiers/router.py (where the publish hook would land),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# alerting-service KillSwitchBus publish-side hook + integration test deferred

> **Severity**: P1 — gates Group F (live trading prerequisites: kill-switch verification) on 2026-05-23 master plan;
> alerting-service can declaratively mark a rule as kill-switch-triggering but cannot actually fire the bus event yet,
> so execution-service halt subscribers won't see anything when a `KILL_SWITCH_*` AlertCode fires.
>
> **Blast radius**: alerting-service (publisher) + execution-service / strategy-service / position-balance-monitor
> (consumers via existing `KillSwitchEvent` subscriber path) + integration test.
>
> **Suggested owner**: Harsh (alerting-service is Harsh's repo per its README) with Ikenna available for pair-review of
> the publisher diff, OR a future session within Agent-1's scope.

## What's already shipped (Phase 1 + 2 of alerting plan)

- UAC@d00326d — `AlertCode` closed-set (39 codes, 3 in `KILL_SWITCH_*` family) + `AlertRule.triggers_kill_switch: bool`
  field with construction-time validator that REJECTS `triggers_kill_switch=True` on a non-`KILL_SWITCH_*` code. The
  single `LIVE_ALERT_RULES` entry covering the wildcard `KILL_SWITCH_*` is marked `triggers_kill_switch=True`.
- alerting-service@b025e83 — `_default_routing_rules` consumes `LIVE_ALERT_RULES` from UAC, so the kill-switch routing
  CONFIG is shipped (PagerDuty + Telegram + `severity="critical"`).
- alerting-service `kill_switch_bus_subscriber.py` (existing, Harsh's prior work) — CONSUMER-side path: when a
  `KillSwitchEvent` lands on the bus, it boosts alert priority + switches routing to on-call. Already wired via
  `ServiceBootstrap`'s `kill_switch_subscriber=on_bus_event` hook.

## What's missing — the publish-side closure

When an alert with code in the `KILL_SWITCH_*` family fires through `route_event` (or wherever alerting-service's
event-routing path lands), no `KillSwitchEvent` is emitted onto the bus. The chain breaks here:

```
emitter (e.g. risk-and-exposure or features-onchain)
  → emits AlertCode.KILL_SWITCH_DEFI_LIQUIDATION_RISK
  → alerting-service routes to PagerDuty + Telegram   ✅ (this works)
  → alerting-service publishes KillSwitchEvent         ❌ (missing — this issue)
  → execution-service KillSwitchEventSubscriber halts  ❌ (cannot trigger without the publish)
```

Net: pages reach the on-call human, but execution-service does NOT auto-halt; the human has to manually trigger the kill
switch via DART. For the May-23 cutover that's an acceptable temporary state (operators are watching live), but it's not
the institutional shape.

## Why I deferred

1. **`alerting-service/` is Harsh's repo per its README + plan coordination note**: "All code edits to alerting-service/
   MUST be pair-coordinated, NOT pushed unilaterally." The minimal Phase 2 diff (config.py default-factory body +
   defi_rules.py threshold migration) is small enough for asynchronous pair-review on a committed branch. Adding a
   publisher introduces a new architectural seam between `route_event` and the UTL `KillSwitchBus` — it's a reasonable
   pair-review-first item.
2. **The right insertion point isn't trivial**: candidates are
   `alerting-service/alerting_service/notifiers/router.py:route_event` (after a successful dispatch), or a new dedicated
   `alerting_service/kill_switch_publisher.py` module wired alongside the dispatchers. I don't want to make the
   architectural call without Harsh.
3. **`triggers_kill_switch=True` is the declarative half**: the UAC closed-set + validator guarantees only
   `KILL_SWITCH_*` codes can ever trip the publish hook, so when the publisher ships it just reads the field — no risk
   of misuse.

## What I found

- `alerting-service/alerting_service/kill_switch_bus_subscriber.py` is consumer-only (verified 2026-05-07, ~50 LOC
  `_EscalationRegistry` + `_HANDLERS` dispatch).
- `alerting-service/alerting_service/notifiers/router.py:route_event` is the central pattern-match-and-dispatch path.
  The publish hook plausibly lives at the end of that function, after channel dispatch, when the matched rule has
  `triggers_kill_switch=True`.
- UTL provides `KillSwitchEvent` + `KillSwitchEventType` + `KillSwitchScope` as the publish surface; the bus interface
  is already used by execution-service / strategy-service / position-balance-monitor on the consumer side. No UTL
  changes required.
- The `AlertRule` Pydantic model currently exposes `triggers_kill_switch` but does NOT include the `KillSwitchScope`
  axis (GLOBAL / VENUE / CLIENT / STRATEGY / INSTRUMENT). The publisher will need to either (a) hard-code
  `KillSwitchScope.GLOBAL` for all `KILL_SWITCH_*` codes, or (b) add a `kill_switch_scope: KillSwitchScope` field to
  `AlertRule` so per-code scoping is declarative.

## Why it matters

- **Master plan Group F (`master_to_live_defi_2026_05_23` — kill-switch verification)** is a May-23 live-only
  prerequisite. Without the publisher, "kill switch fires automatically when health factor breaches" cannot be validated
  end-to-end.
- **Alerting plan Phase 8 (live rehearsal)** explicitly calls out "CRITICAL-severity rehearsal: simulate
  `KILL_SWITCH_DEFI_LIQUIDATION_RISK` end-to-end including circuit-breaker propagation to execution-service +
  strategy-service halt-order subscribers" — that pass/fail test will fail without this hook.
- **Mitigation**: operator-on-call human can manually fire the kill switch via DART when paged. Acceptable for the first
  7-day soak with humans watching, NOT acceptable as the institutional steady state.

## Recommended decision

Ship the publish-side hook as a small follow-up commit on alerting-service:

1. **UAC**: add `kill_switch_scope: KillSwitchScope | None = None` field to `AlertRule` (None defaults to GLOBAL for
   `triggers_kill_switch=True` rules; explicit per-code scope supported for the future `KILL_SWITCH_VENUE_DISCONNECT`
   family which should scope to the venue, not globally). Update `LIVE_ALERT_RULES` so `KILL_SWITCH_VENUE_DISCONNECT`
   carries `kill_switch_scope=KillSwitchScope.VENUE`.
2. **alerting-service**: new `kill_switch_publisher.py` with a single
   `publish_kill_switch_event(rule: AlertRule, payload: dict[str, str | int | float | bool])` function that emits a
   `KillSwitchEvent` via the existing UTL bus client. Call it from `notifiers/router.py:route_event` AFTER successful
   channel dispatch, gated on `rule.triggers_kill_switch`.
3. **Integration test**: `tests/integration/test_kill_switch_publish.py` — fake bus client, fire a
   `KILL_SWITCH_DEFI_LIQUIDATION_RISK` event through `route_event`, assert exactly one `KillSwitchEvent` lands on the
   bus with `scope=GLOBAL` + the expected payload.
4. **Phase 8 rehearsal addition**: extend the rehearsal script's `KILL_SWITCH_*` test to assert execution-service
   receives + halts on the bus event.

Estimated effort: 30-45 minutes for steps 1-3, additional 15 minutes for step 4. Scope-bounded

- low-blast-radius given the UAC `triggers_kill_switch` validator + `KillSwitchScope` enum already exist.

## Cross-references

- Plan: [`alerting_service_live_rules_2026_05_07`](../alerting_service_live_rules_2026_05_07.md) Phase 2 (declarative
  half shipped) + Phase 8 (rehearsal still pending).
- Master plan blocker: [`master_to_live_defi_2026_05_23`](../master_to_live_defi_2026_05_23.md) Group F (kill-switch
  verification).
- Work-split parent: [`work_split_2026_05_07_ikenna_5tab_layout`](../work_split_2026_05_07_ikenna_5tab_layout.md) Agent
  1 done-definition item 2 ("KillSwitchBus integration test passes") explicitly flagged.
- Codex SSOT: [`codex/14-playbooks/alerting/alert-code-taxonomy`](/codex/14-playbooks/alerting/alert-code-taxonomy.md).
