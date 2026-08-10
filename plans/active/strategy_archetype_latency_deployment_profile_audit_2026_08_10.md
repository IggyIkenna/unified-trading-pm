---
doc_type: plan
title: Audit — populate per-archetype latency requirements and derive each archetype's required deployment profile
summary: >-
  `runtime-topology.yaml` v7 (unified-trading-pm/configs/) already has a mature deployment-profile/SLA-tier/isolation
  framework, and `isolation_policies.strategy-service` explicitly says per-archetype latency requirements live in
  `codex/09-strategy/architecture-v2/families/*.md` — but 2026-08-10 investigation found that pointer leads to an EMPTY
  well for exactly the archetypes the operator flagged as latency-sensitive (carry-and-yield/basis, ml-directional,
  rules-directional; arbitrage-structural has only an incidental mention). This plan populates the missing per-archetype
  latency specs using a defined rubric (not open-ended judgment) and derives each archetype's required
  deployment_profile from the populated data, producing a single decision artifact the paired execution plan implements
  against. Audit-only — no runtime-topology.yaml/family-doc wiring change ships from this plan.
status: active
nature: process
asset_group: [cross-cutting]
stage: [strategy]
repos: [unified-trading-pm, strategy-service, deployment-service]
scope: [engineer]
tags: [strategy, execution, latency, deployment-profile, archetype, sla, audit]
related:
  [
    /codex/09-strategy/architecture-v2/families/market-making.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/families/carry-and-yield.md,
    /codex/09-strategy/architecture-v2/families/ml-directional.md,
    /codex/09-strategy/architecture-v2/families/rules-directional.md,
    /codex/04-architecture/client-isolation-sla-and-runtime-profiles.md,
    /plans/active/strategy_archetype_latency_deployment_profile_execution_2026_08_10.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-10
last_updated: 2026-08-10
parent_epic: strategy_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
assigned_role: quant_dev
effort: high
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    unified-trading-pm/configs/runtime-topology.yaml,
    /codex/04-architecture/client-isolation-sla-and-runtime-profiles.md,
    codex/09-strategy/architecture-v2/families/,
    /codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md,
  ]
supersedes:
superseded_by:
source: >-
  Operator, 2026-08-10: "for ml directional and rules based and arbitrage based archetypes and stakes basis and basis
  related latency would matter there too at least should be in the ms realm" — a direct correction to the archived
  pre-v2 doc's Medium/High categorization of basis. Operator confirmed AO-dispatchable, audit phase forces the decision,
  execution phase implements it.
---

# Audit — per-archetype latency requirements + deployment-profile derivation

## Decision rubric (apply consistently — this is what makes the audit worker-determinable, not a judgment call)

**Latency category → deployment_profile mapping (already fixed by `runtime-topology.yaml`'s existing categories):**

- `Low` (sub-second E2E) → `co_located_vm`
- `Medium`/`High` (seconds-to-minutes E2E) → `distributed`

**Per-archetype-family latency category (operator ruling 2026-08-10 overrides the archived pre-v2 doc where they
conflict):**

| Family doc                   | Category | Why                                                                                                                                                                                        |
| ---------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `market-making.md`           | `Low`    | Already the archived doc's position (<100ms E2E) — operator did not correct this, confirm and formalize.                                                                                   |
| `arbitrage-structural.md`    | `Low`    | Archived doc already had stat-arb/cross-exchange at <200-300ms — operator confirmed, formalize.                                                                                            |
| `carry-and-yield.md` (basis) | `Low`    | **Operator correction** — archived doc had this at Medium/High; operator says inter-leg execution timing (not decision latency) must be ms-realm.                                          |
| `ml-directional.md`          | `Low`    | **Operator correction** — no archetype existed for this in the archived doc; operator says ms-realm.                                                                                       |
| `rules-directional.md`       | `Low`    | **Operator correction** — same as ml-directional.                                                                                                                                          |
| `vol-trading.md`             | inherit  | Not named by operator — audit worker derives from archived doc's closest analog (Volatility Arb, Medium) unless the doc's own content indicates otherwise; state the reasoning either way. |
| `event-driven.md`            | inherit  | Same treatment as vol-trading.                                                                                                                                                             |
| `portfolio.md`               | inherit  | Same treatment as vol-trading.                                                                                                                                                             |
| `stat-arb-pairs.md`          | `Low`    | Falls under the operator's "arbitrage-based" correction — statistical arb pairs trading.                                                                                                   |

**"Low" for a multi-leg archetype means the INTER-LEG execution timing budget, not necessarily the tick-to-signal
decision budget** — per operator: "to some extent can be latency on the decision to execute but we are executing two
legs of a trade... how are we ensuring the lag leg followed by the lead leg is ms timing." Each populated family doc's
latency section must distinguish these two things explicitly (decision latency vs. inter-leg execution gap) rather than
collapsing them into one number the way the archived doc did.

## Todos

- [x] ✅ [DOC] P2. **Populate `/codex/09-strategy/architecture-v2/families/market-making.md`** with a formal Latency
      Requirements section (tick-to-signal / signal-to-order / order-to-fill / total E2E / category = `Low`), citing the
      archived `_archived_pre_v2/cross-cutting/latency-profiles.md` table as the baseline, confirming or correcting its
      numbers against this doc's own existing (informal) latency mentions. **Done**: `unified-trading-pm@aa2a89a2d9` —
      formal `## Latency Requirements` section added (tick-to-signal <50ms / signal-to-order <50ms / order-to-fill
      venue-dep. / total E2E <100ms / category `Low`, archived baseline confirmed + cited with venue baselines), plus a
      `### Decision latency vs. inter-leg execution gap` subsection (options-MM delta-hedge + cross-venue quote legs at
      ms timing per the 2026-08-10 operator ruling,
      `/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md` frontmatter `source:`) and the
      Low→`co_located_vm` deployment implication referencing `runtime-topology.yaml` + the SLA-tier doc.
- [ ] [DOC] P2. **Populate `arbitrage-structural.md`** with the same section, category `Low`, distinguishing stat-arb
      vs. cross-exchange arb's inter-leg execution gap explicitly (two legs on two different venues — the gap is the
      real risk surface).
- [ ] [DOC] P2. **Populate `carry-and-yield.md`** (basis/staking-basis family) with the same section, category `Low` per
      the operator correction above — explicitly document the spot-leg/perp-hedge-leg inter-leg gap requirement, not
      just a decision-latency number.
- [ ] [DOC] P2. **Populate `ml-directional.md`** with the same section, category `Low` per operator correction — this
      family doc currently has ZERO latency content, so this is greenfield within the doc (not a correction of existing
      numbers).
- [ ] [DOC] P2. **Populate `rules-directional.md`** with the same section, category `Low` per operator correction — same
      greenfield situation as ml-directional.
- [ ] [DOC] P2. **Populate `stat-arb-pairs.md`** with the same section, category `Low`.
- [ ] [DOC] P3. **Populate `vol-trading.md`, `event-driven.md`, `portfolio.md`** with the same section — derive category
      from the archived doc's closest analog per the rubric table above; state the derivation reasoning inline in each
      doc so a future reader can see it wasn't a guess.
- [ ] [DATA] P2. **Derive each archetype's required `deployment_profile`** (`co_located_vm` vs `distributed`) from the
      now-populated latency categories per the Low→co_located_vm / Medium+High→distributed rubric above. Record this as
      a table in a new section of `runtime-topology.yaml`'s SSOT decisions doc
      (`/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` — read it first, follow its existing format) — **decision
      artifact only, do not modify `runtime-topology.yaml` itself from this plan** (that's the execution plan's job).
- [ ] [DATA] P2. **Check whether `isolation_policies.strategy-service`'s existing SLA-tier framework already accounts
      for `Low`-category archetypes needing more than the `premium` tier's 40ms budget provides** — some archived-doc
      figures (MM <100ms total E2E) fit inside 40ms; verify the others (arb <200-300ms, and the newly ms-realm-ruled
      basis/ML-directional/rules-based) against the `premium` tier's 40ms number and flag explicitly if any family's
      real requirement EXCEEDS what even the `premium` SLA tier currently promises — that's a real
      SLA-tier-vs-archetype-requirement gap worth surfacing, not silently absorbing.
- [ ] [DATA] P2. **Confirm whether `strategy-service`'s archetype registry or engine layer currently READS these family
      docs at runtime, or whether they're purely human-readable documentation today** — grep for any programmatic
      consumption of `codex/09-strategy/architecture-v2/families/*.md` content (unlikely, but confirm rather than
      assume) so the execution plan knows whether it's building a NEW runtime link from scratch or wiring into something
      that partially exists.
- [ ] [DOC] P2. **Write the final decision artifact**: a single new section in
      `/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` (or a new dedicated doc if that one is a poor fit — check
      first) mapping every archetype family → latency category → required deployment_profile → whether the current
      `premium` SLA tier's latency budget actually covers it. This is the artifact the paired execution plan
      (`strategy_archetype_latency_deployment_profile_execution_2026_08_10.md`, `depends_on` + `gate_on_depends` this
      plan) implements against — it must be unambiguous enough that the execution plan's todos don't require further
      judgment calls, only implementation.

## Progress Log

- 2026-08-10: Plan created following a same-day investigation that found `runtime-topology.yaml` v7 is real and mature,
  but its own pointer to per-archetype latency specs (`codex/09-strategy/architecture-v2/families/*.md`) leads to empty
  content for exactly the archetypes the operator flagged as latency-sensitive. Operator explicitly corrected the
  archived pre-v2 doc's categorization of basis (Medium/High → should be Low/ms-realm) and named
  ml-directional/rules-directional/arbitrage as needing the same treatment, distinguishing inter-leg execution timing
  from decision latency. AO-dispatchable per operator direction; this audit phase is gated to produce a forced,
  unambiguous decision so the execution phase requires no further architectural judgment.
- **quant_dev (slot 9) 2026-08-10T13:45Z**: Todo 1 done. Added formal `## Latency Requirements` to `market-making.md`
  (`unified-trading-pm@aa2a89a2d9`): category `Low`, tick-to-signal <50ms / signal-to-order <50ms / order-to-fill
  venue-dep. (with archived CeFi venue baselines cited) / total E2E <100ms — archived `latency-profiles.md` Market
  Making row confirmed, not corrected (consistent with the doc's existing sub-ms shadow + delta-proxy fast path +
  latency-spike kill switch). Includes the `### Decision latency vs. inter-leg execution gap` subsection (options-MM
  delta-hedge + cross-venue quote legs must track at ms timing per the 2026-08-10 operator ruling) and the
  Low→`co_located_vm` deployment implication cross-referencing `runtime-topology.yaml` and
  `client-isolation-sla-and-runtime-profiles.md` § 6 (MM = exec+strategy co-located, min SLA premium).
