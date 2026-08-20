---
doc_type: audit-result
title: State-fabric reconciliation audit — dispatch brief (one tranche per repo, no delegation)
summary: >-
  The dispatch brief for reconciling six repos plus codex, plans, issues and the client artefacts against the
  cross-domain state fabric SSOT shipped 2026-08-20 (unified-trading-pm@986205da45). Seven independent tranches, each
  scoped to one repo or surface, each forbidden from spawning sub-agents. Records the shared preamble every tranche
  must receive and the per-tranche briefs.
status: pass
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    features-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
    unified-trading-library,
  ]
scope: [engineer, admin]
tags: [audit, dispatch, state-fabric, reconciliation, ssot, codex-drift]
related:
  [
    /codex/04-architecture/cross-domain-state-fabric.md,
    /plans/audit/results/external_hft_factor_repricing_spec_2026_08_20.md,
    /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-20
last_updated: "2026-08-20"
date: 2026-08-20
severity: P0
parent_epic: system_readiness_master
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope: >-
  Dispatch brief only — no audit findings are recorded here. The tranches themselves write findings into
  plans/active/issues/ and their own plans.
auditor: >-
  Interactive session slot 6, authored 2026-08-20 immediately after the state-fabric SSOT landed.
---

# State-fabric reconciliation — dispatch brief

## Why this exists

Sixteen operator rulings landed 2026-08-20 in
[/codex/04-architecture/cross-domain-state-fabric.md](/codex/04-architecture/cross-domain-state-fabric.md). They change
what "correct" means for six repos, for several codex docs, for the in-flight plans, and for the client-facing
artefacts. Nothing in the codebase has been changed to match — this brief is how that gets reconciled.

## Hard rule for every tranche

**Each tranche audits ONE repo or ONE surface and MUST NOT use the Agent tool.** A corpus-wide brief issued on
2026-08-19 spawned 17 nested agents and produced zero output across roughly 500k tokens. One agent, one scope, no
delegation.

**This is an AUDIT, not a refactor.** Tranches write findings — issue docs, plan todos, codex corrections. They do not
implement the rulings. Where a tranche can fix a doc it misled itself on, it fixes that doc in the same pass (the
standing "a doc that misled you is a finding" rule).

## Shared preamble — paste at the top of EVERY tranche

```
Read these three documents in full before doing anything else:

  1. /codex/04-architecture/cross-domain-state-fabric.md
       The SSOT. Two orthogonal axes (semantic profile x performance tier), the three profiles,
       the StateEnvelope, the four double-reaction barriers, source tiers, component ownership,
       the cross-region delay estimator, and the R1-R16 operator ruling register in section 9.

  2. /plans/audit/results/external_hft_factor_repricing_spec_2026_08_20.md
       The external engineering specification, verbatim. It is a CONTINUOUS-QUOTE PROFILE spec
       using BTC as its worked example. Do NOT treat it as an implementation spec for 192 venues
       or 60 archetypes, and do NOT edit it.

  3. /plans/active/issues/execution_delta_proxy_repricer_generalization_2026_08_18.md
       Sections 11-16. The in-flight design and what section 16 changed.

Then read SUB_AGENT_MANDATORY_RULES.md and follow it. If it was not provided to you, STOP.

Three corrections that supersede anything you read elsewhere:
  - The Taylor factor-state form F_i is the CONTINUOUS-QUOTE KERNEL, not a universal valuation
    formula. The universal invariant is "evaluate current absolute state against an immutable
    reference generation."
  - Semantic profile and performance tier are ORTHOGONAL. Profile bounds the achievable tier
    (block time is a floor) but does not determine it. Never hard-code "continuous quote = fast".
  - Retraction/correction is ONE envelope operation across all profiles. A chain reorg, a sports
    scoring correction and a voided market are the same mechanism, not three.

Measurement discipline: 0 grep hits is NOT evidence of absence — a symbol can be resolved at
runtime, or live under a different vocabulary. State what you searched. A claim must never exceed
what you measured. If you are uncertain, say so rather than rounding to a clean answer.

Do NOT use the Agent tool. Do NOT spawn sub-agents. One agent, one scope.
```

## The seven tranches

| # | Scope | Central question |
| - | ----- | ---------------- |
| T1 | `unified-api-contracts` | Does the venue capability registry carry the manifest fields (R10/R11)? What breaks if `finality_model` and `ordering_key` become undefaultable? Where would `StateEnvelope` live? |
| T2 | `market-tick-data-service` **(live path first)** | RX-time + region capture (R4) — measured absent, confirm and scope. Feed semantic registry: are the four double-reaction barriers distinguishable today, especially barrier 2 (trade/BBO/depth as ONE match event)? |
| T3 | `features-service` + `greeks-service` | The R7 fold. What is the actual boundary today, what does each own, and what is the migration surface? Where would the slow generation (`z_0`, loadings, covariance) be published from? |
| T4 | `strategy-service` | Which side declares vs detects each kill-switch condition? Slow/fast split of risk, dust policy, `exit_mode` playbooks. Does anything here derive its own fair value (it must not)? |
| T5 | `execution-service` | Kill-switch **arming** path (reaction is confirmed wired; detection is not). The `action_mask` = scoped-kill unification. Dust avoidance in the order-state diff. DeFi finality ladder + reorg retraction — measured ZERO `reorg` hits. |
| T6 | `unified-trading-library` | `EventTransport` / `KillSwitchBus` / `BreakerRecoveryEngine` against the StateEnvelope invariants. Does the event log carry enough to replay per-region (R4)? |
| T7 | codex + plans + issues + client artefacts | Drift sweep: which codex docs the rulings invalidate, which plans assume the superseded design, which client artefacts state something the rulings contradict. |

**T7 runs LAST** — it reconciles the documentation against what T1-T6 measured, so running it first would reconcile against assumptions.

**T1-T6 are independent and touch different repos**, so they may run concurrently. T5 and T4 both touch the kill-switch question from opposite ends; they must not edit each other's repo.

## Deliverable shape, identical for every tranche

1. A findings section appended to this tranche's own plan (never a chat summary).
2. Every deferral is a `- [ ]` todo with tag, priority, evidence and provenance. Never prose.
3. Findings outside every existing plan become `plans/active/issues/<slug>_2026_08_20.md`.
4. A doc that misled the tranche gets corrected in the same pass, with what was verified stated.
5. Anything requiring an operator decision is tagged `[OPERATOR]` with options and a recommendation
   — never silently deferred.

## Known-open questions the tranches must NOT resolve unilaterally

- Position vectors: `q_confirmed` / `q_pricing` (fill-probability-weighted) / `q_worst`.
- The five Wave-0 rulings (CloudKmsCustodyProvider wallet check, UAC `__init__` scope, instruments
  catalogue ratification, instrument-universe hot-swap safety, venue-eligibility shape).
- Whether the fast nowcast component deploys colocated with MTDS + execution-service.
- Scheduled vs unscheduled discrete events as a manifest axis (raised 2026-08-20, not yet ruled).

## Todos

- [ ] [OPERATOR] P0. **Dispatch T1-T6 concurrently, T7 after they land.** Each with the shared
      preamble verbatim and its own single-repo scope.
- [ ] [REVIEW] P1. **Check tranche collision with in-flight agent work** before dispatch — agents are
      already running refactor tasks and must not have their repos audited out from under them mid-edit.
