---
doc_type: plan
title: State fabric — UAC foundation (declarations, capability gate, resolver)
summary: >-
  The foundation plan for the 27 state-fabric rulings of 2026-08-20. Owns everything that must be DECLARED in
  unified-api-contracts before any other repo can consume it — the venue manifest extension, the StateEnvelope, source
  tiers, recovery-quality levels, feature bootstrap types, kill-condition detector declarations, the MQP capability
  field — plus the capability gate and its shrinking-ratchet baseline that make a declaration verifiable. Every other
  state-fabric repo plan gates on this one.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer]
tags: [state-fabric, uac, capability-gating, registry, declarations, ssot]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/audit/results/state_fabric_reconciliation_dispatch_2026_08_20.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
  ]
created: 2026-08-20
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 15
estimate_calibrated_ai_days: 9
locked_by:
locked_since:
depends_on: []
supersedes:
superseded_by:
source:
context_scope:
  [
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/epics/system_readiness_master.md,
    /codex/12-agent-workflow/measurement-claims-discipline.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
---

# State fabric — UAC foundation

> **Why this plan exists.** Twenty-seven rulings landed 2026-08-20 in
> [/codex/04-architecture/cross-domain-state-fabric.md](/codex/04-architecture/cross-domain-state-fabric.md). Roughly
> half had **no tracked work behind them** — they became SSOT and stopped there. Measured 2026-08-20: nine distinct
> concepts (capability gate, MQP field, warm-up declarations, bootstrap types, recovery-quality levels, source tiers,
> kill-condition detectors, `RedisStreamTransport` wiring, the Wave-0 rulings) had **zero** matching open todos
> anywhere in `plans/active/`. This plan and its siblings close that.
>
> **This is the gating plan.** Under R17 every other repo consumes declarations that live here. Sibling plans set
> `depends_on: [state_fabric_uac_foundation_2026_08_20]` with `gate_on_depends: true`.

## Codex SSOTs

- [/codex/04-architecture/cross-domain-state-fabric.md](/codex/04-architecture/cross-domain-state-fabric.md) —
  R1-R27, the two axes, the three profiles, StateEnvelope, capability gating, position vectors.
- [/codex/04-architecture/autonomous-recovery-matrix.md](/codex/04-architecture/autonomous-recovery-matrix.md) —
  kill arming/resume authority; the state-fabric doc owns the declaration/detection/reaction split.

## The rule this plan is built on

**R17 — declare what is possible, configure what is desired, resolve at runtime, fail closed and loud when desired is
not a subset of possible.** Adding a venue, chain, archetype or mode becomes adding a row, not editing a branch.

**R20 — build the missing implementation; never delete the declaration to pass the gate.** Deleting passes the gate
while moving the platform further from target state.

## Todos

### Declarations

- [ ] [BACKEND] P0. **Extend the venue capability registry with the manifest fields** (R10/R11) — `semantic_profile`,
      `ordering_key`, timestamp semantics, `finality_model`, retraction behaviour, recovery procedure, action verbs,
      latency SLO, transport profile. Profile defaults for most; **`finality_model` and `ordering_key` have NO default
      and must be declared explicitly per venue**. Extends the EXISTING registry — a fourth parallel venue registry is
      forbidden (three already disagreed, filed 2026-08-19).
- [ ] [BACKEND] P0. **Define `StateEnvelope`** with every invariant field: `logical_position` (profile-specific
      ordering key, not a timestamp), `correction_or_retraction_of`, `received_in_region`, `account_scope` as a hard
      boundary, `effective_from`/`effective_until`, `finality_state`, `action_mask`, `uncertainty`.
- [ ] [BACKEND] P0. **Declare the `block_ledger` finality ladder** as a typed enum —
      `observed -> included -> canonical -> confirmed -> finalized` with a `retracted/reorged` branch — and the
      per-stage action permissions the manifest configures. `included` and `confirmed` must not be collapsible.
- [ ] [BACKEND] P1. **Declare source tiers 0-3** (may move actionable state / confirmation only / recovery-fallback /
      research-only). Orthogonal to action permissions: tiers say what a source may INFLUENCE, permissions say what
      actions it may AUTHORISE. Both are needed; neither substitutes for the other.
- [ ] [BACKEND] P1. **Declare recovery-quality levels** — event-exact / state-exact / economically-reconciled /
      provisional / unavailable. Measured absent 2026-08-20.
- [ ] [BACKEND] P1. **Declare feature bootstrap types** — `CURRENT_SNAPSHOT` / `FINITE_WINDOW` /
      `RECURSIVE_SUFFICIENT_STATE` / `EVENT_EXACT` / `CROSS_FEED_ALIGNED` / `SESSION_LIFETIME`. Measured 2026-08-20:
      warm-up today is an untyped period count (`lookback_candles`, `max_lookback_periods`), always effectively
      `FINITE_WINDOW`-shaped, with no way to say "needs only the current snapshot" or "needs the whole session".
- [ ] [BACKEND] P1. **Add the mass-quote-protection capability field per venue** (R22) — whether the venue pulls
      remaining quotes when one trades, and its parameters. `q_worst` is DERIVED from this, not assumed: with MQP the
      worst case is "one fills, rest cancel"; without it, "everything fills". Deribit / CME / Eurex have it, most
      crypto spot does not.
- [ ] [BACKEND] P1. **Declare each kill condition's detector and latency class** (R21). Infrastructure conditions
      (feed staleness, sequence gap, position divergence, venue disconnect, clock breach, ack timeout, model trust
      breach) are platform-detected; economic conditions (drawdown, exposure, concentration) are strategy-detected.
- [ ] [BACKEND] P2. **Declare per-channel recovery capability** — snapshot support, replay/cursor support, retention,
      source sequence identifiers, checksums, REST backfill limits, duplicate identifiers, correction/finality
      behaviour, timestamp meanings, max expected gaps. Measured 2026-08-20: three registries exist and **none carries
      any of these**; there is nowhere today to record "this channel's REST backfill is capped at 1000 rows".

### The resolver and the gate

- [ ] [BACKEND] P0. **Build the capability resolver** (R17) — one resolver, one vocabulary: eligibility = desired
      intersect possible, raising a typed error when desired is not a subset of possible. Never a plausible default.
      Model it on the `classify_venue_asset_group()` fix (unified-api-contracts@d4cded41b8), which replaced a silent
      `"cefi"` fallback with a loud error naming both registries it missed.
- [ ] [BACKEND] P0. **Build the capability gate** (R18) — a declared capability with no reachable implementation FAILS
      the quality gate. This is the check that would have caught `OrderRecoveryEngine` (zero production call sites),
      `PostgreSQLOrderPersistence` (every method raises `NotImplementedError`), `RedisStreamTransport` (zero call
      sites) and `HealthFactorMonitor` (no production entry point) — four measured instances as of 2026-08-20.
- [ ] [BACKEND] P0. **Baseline the gate as a shrinking ratchet** (R19) — count current violations, block anything NEW,
      require the number to go DOWN. Same mechanism as the DTZ / TID251 / fallback-import baselines. **Never raise the
      baseline.** Without this the gate fails everything on day one and gets disabled.
- [ ] [BACKEND] P1. **Add declared-vs-measured divergence alerting** (R12 generalised by R18) — a declared SLO that
      continuous measurement contradicts raises an alert.
- [ ] [DOC] P1. **Record the disposition rule where the gate reports it** (R20) — a violation is cleared by BUILDING
      the missing implementation, never by removing the declaration. The gate message should say so, because the wrong
      fix is the easy one and it passes.

### Verification

- [ ] [REVIEW] P1. **Add invariant tests for every new declaration**, matching the pattern that closed the chain-
      registry drift (`tests/unit/test_chain_registry_ssot.py`, 7 containment tests). A declaration with no invariant
      test is the next silent drift.
- [ ] [REVIEW] P2. **Re-measure the three-registry overlap after the manifest extension** — confirm the extension did
      not create a fourth vocabulary by accident, which is the specific failure this plan is meant to prevent.

## Progress Log

**2026-08-20 — authored.** No code written. Created because a measured coverage check found nine ruling-derived
concepts with zero tracked todos: the rulings had become codex SSOT without becoming work. Human plan
(`assigned_vm: NA`) per operator ruling — several items need judgement as they land.

- **na-eligibility-audit 2026-08-21** (cross-cutting tranche, batch 3/3): KEEP-NA, valid — foundational UAC
  architecture-declaration plan for a brand-new concept ("27 state-fabric rulings") that every other state-fabric
  repo plan gates on; the doc's own frontmatter/Progress Log states explicit operator intent ("Human plan
  (`assigned_vm: NA`) per operator ruling — several items need judgement as they land"). All 16 open todos are
  first-declarations of new invariant vocabulary (StateEnvelope, finality ladder, recovery-quality levels,
  capability gate/resolver) requiring design coherence across the whole concept, not isolated bounded tasks.
