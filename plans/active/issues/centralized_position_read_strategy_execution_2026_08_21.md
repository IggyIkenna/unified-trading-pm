---
doc_type: issue
title:
  "Centralize position reads between strategy-service and execution-service via one DB-backed reader —
  operator architecture direction, 2026-08-21"
summary: >-
  Surfaced answering a question about why execution-venue and position-read-venue are separate, unvalidated
  fields in strategy config (found during a venue-capability-registry audit). Operator's direction: don't
  reconcile the two venue axes — instead centralize position READS through one DB-backed reader in
  strategy-service that both services are forced to use, eliminating the need for strategy<->execution
  position reconciliation entirely. The only remaining reconciliation is (a) venue-subscription lists, and
  (b) each service independently reconciling ITS OWN positions from its own trades against the position
  monitor. Not built — this is architecture direction to scope into buildable todos, not a shipped design.
status: open
nature: design
asset_group: [cefi, defi, tradfi]
stage: [strategy, execution]
repos: [strategy-service, execution-service]
scope: [engineer, admin]
tags: [position, architecture, centralization, operator-direction, db]
related:
  [
    /plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md,
    /plans/active/strategy_service_centralization_fixes_2026_08_16.md,
  ]
created: "2026-08-21"
author: unknown
last_updated: "2026-08-21"
source: operator-request-2026-08-21
parent_epic: security_and_cross_cutting_master
resolved_by:
locked_by:
context_scope:
  [
    strategy-service/strategy_service/position/storage/database.py,
    strategy-service/strategy_service/position/storage/position_store.py,
    strategy-service/strategy_service/position/api/main.py,
  ]
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.6
assigned_role: strategy_engineering
drift_direction: advance-code
---

# Centralize position reads between strategy-service and execution-service

## Context — how this surfaced

A venue-capability-registry audit (2026-08-21) found strategy-service's execution-venue field
(`VolSurfaceConfig.venue`, `CrossExchangeConfig.venue_a`/`venue_b`, etc.) and its position-read venue
subscriptions (`RiskInstrumentSubscriptions`, `PositionMonitorConfig.position_subscriptions`, etc.) are two
structurally separate, unvalidated axes with real, intentional divergence in places (e.g. `staked_basis.py`'s
LST_AS_MARGIN reads DeFi collateral via subscriptions while executing perp hedges on a different venue). Asked
the operator whether this needs validation or documentation.

## OPERATOR DIRECTION 2026-08-21 (verbatim)

> "why not just centralise position between strategy and execution services via the DB position is kept. a
> central reader in strategy service ensures a strategy is reading its position across all its accounts which
> is safest way to guarantee. execution services is forced to read the same way. so no actual need for
> reconciliation between them just reconciliation of venue subscriptions and they each reconcile their
> positions from trades vs the position monitor."

Translation / what this means architecturally:

1. **One DB-backed position reader, owned by strategy-service** — strategy-service reads a strategy's positions
   across ALL its accounts through ONE central reader, not scattered per-purpose subscription mechanisms.
2. **execution-service is FORCED to read positions the same way** — through the same central reader/DB, not
   its own independent position view. This is the key move that eliminates cross-service position
   reconciliation: if both services read the identical source, there's nothing to reconcile between them.
3. **What reconciliation remains, narrowed to two kinds**:
   - Venue-SUBSCRIPTION reconciliation (are the two services subscribed to consistent venue lists — NOT
     position values).
   - Each service independently reconciles ITS OWN positions-from-trades against the position monitor (a
     trades-vs-holdings self-check per service, not a cross-service position diff).

## What already exists (verify before building — not independently confirmed this session)

`strategy_service/position/storage/{database.py,position_store.py}` — a real DB-backed position store already
exists in strategy-service (confirmed present via grep, contents NOT read this session). `position/api/main.py`
+ `position/api/routes/` expose an API surface. This may already BE (or be close to) the "central reader" the
operator describes — or it may be one of several scattered mechanisms this direction wants collapsed into.
**First real task is to read this existing code and determine how far it already is from the target
architecture**, not assume either "already done" or "must build from scratch."

## Todos

- [ ] [BACKEND] P1. **Audit the current state of `strategy_service/position/storage/{database.py,
      position_store.py}` + `position/api/`** against the operator's target: is this already a real
      cross-account-aggregating central reader? Does execution-service read positions from it today (grep
      execution-service for any call into strategy-service's position API/DB), or does execution-service
      maintain its own independent position view (if so, where, and is IT the thing that should be deleted in
      favor of reading strategy-service's central store)?
- [ ] [BACKEND] P1. **Scope the "forced to read the same way" mechanism** — is this an execution-service code
      change (call strategy-service's position API instead of its own view), a shared library
      (`unified-trading-library`) read path both services import, or something else? Note this workspace's
      hard "NO service<->service dependency" rule (T4/execution-service depends only on UTL/UAC, integrates by
      API contract — `/codex/04-architecture/tier-and-import-architecture.md`) — a direct execution-service ->
      strategy-service API call may conflict with that rule; if so, the shared-library-reading-one-DB shape is
      likely the right one, confirm before building either way.
- [ ] [BACKEND] P2. **Design the venue-subscription reconciliation check** — what does "reconcile venue
      subscriptions" mean concretely: a periodic diff of each service's subscribed-venue list against a
      shared registry, alerting on drift? Scope once todo 1's audit is done.
- [ ] [BACKEND] P2. **Design each service's independent trades-vs-position-monitor reconciliation** — likely
      already partially exists (position monitors + trade ledgers exist in both services); confirm what's real
      today vs. what needs building once todo 1 lands.
- [ ] [REVIEW] P3. Once centralized, revisit the venue-eligibility resolver work
      (`venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md`) — a central position reader may
      change how venue capability should be declared/checked (one source of truth for "what venues does this
      strategy actually hold positions on" becomes available).

## Progress Log

- **2026-08-21** — Filed from an interactive session after the operator gave this architecture direction in
  response to a venue-capability audit question. Not investigated further this session (session/time
  constrained) — todo 1 is the real next step, not yet started.
