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
sequential: true
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
- [x] ✅ [DOC] P2. **Populate `arbitrage-structural.md`** with the same section, category `Low`, distinguishing stat-arb
      vs. cross-exchange arb's inter-leg execution gap explicitly (two legs on two different venues — the gap is the
      real risk surface). **Done**: `unified-trading-pm@b62348bb59` — formal `## Latency Requirements` section added
      (category `Low`, archived Statistical Arb / Cross-Exchange Arb / Sports Arbitrage rows confirmed as the baseline,
      segment budgets <200ms / <300ms / <2s E2E, UI-dashboard latency monitor cited), a
      `### Decision latency vs.     inter-leg execution gap` subsection distinguishing the stat-arb/ATOMIC sub-profile
      (atomicity bounds the gap) from cross-exchange arb's two-legs-two-venues leg-and-hedge gap (the real risk surface;
      `max_hedge_delay_ms: 500` = abort ceiling, operating target ms-realm per the 2026-08-10 operator ruling), and the
      Low→`co_located_vm` deployment implication flagging the current `client-isolation-sla-and-runtime-profiles.md` § 6
      `ARBITRAGE_STRUCTURAL` topology_requirements row (co-location `no` / min SLA `standard`) as a discrepancy the
      deployment-profile derivation todo resolves. Same commit fixed a pre-existing dangling `related:` frontmatter
      reference (`market-making.md` → leading-slash path) flagged by plan-hygiene.
- [x] ✅ [DOC] P2. **Populate `carry-and-yield.md`** (basis/staking-basis family) with the same section, category `Low`
      per the operator correction above — explicitly document the spot-leg/perp-hedge-leg inter-leg gap requirement, not
      just a decision-latency number. **Done**: `unified-trading-pm@47c6b8ffd6` — formal `## Latency Requirements`
      section added (category `Low`, decision-cycle Tol.-to-Signal <5 s / Signal-to-Order <2 s / Order-to-Fill
      venue-dep. / inter-leg execution gap ms-realm <500 ms operating target / Total E2E <40 s CeFi, block-time + <5 s
      DeFi staked), archived Delta-One Basis Medium baseline CORRECTED per the operator ruling at
      `/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md` frontmatter `source:`, including
      a `### Decision latency vs. inter-leg execution gap` subsection breaking down all 10 archetypes (8 multi-leg
      basis/ staking-basis variants at ms-realm gap, 2 single-sided yield/staking variants inherit Medium), the Low→
      `co_located_vm` deployment implication flagging the current `CARRY_BASIS_PERP`/`CARRY_STAKED_BASIS`
      topology_requirements discrepancy (co-location `no` / min SLA `standard`), and a pre-existing reference-path fix
      (`market-making.md` → leading-slash path in `related:` frontmatter).
- [x] ✅ [DOC] P2. **Populate `ml-directional.md`** with the same section, category `Low` per operator correction — this
      family doc currently has ZERO latency content, so this is greenfield within the doc (not a correction of existing
      numbers). **Done**: `unified-trading-pm@d631674085` — formal `## Latency Requirements` section added (category
      `Low`; greenfield — archived `latency-profiles.md` has no ML Directional row, so the segment budgets are derived
      from the archived internal pipeline budgets: features <100ms single-instrument / warm ml-inference <50ms /
      strategy eval <20ms / execution submit <50ms + the sports venue-latency table). 3-row per-expression table
      (continuous single-instrument / continuous options expression / event-settled → totals <200ms / <200ms / <1s, all
      `Low`), the `### Decision latency vs. inter-leg execution gap` subsection (options synthetics + delta hedges bound
      at ms-realm inter-leg timing per the operator ruling
      (`/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md` frontmatter `source:`);
      event-settled cross-venue best-odds freshness), and the Low→`co_located_vm` deployment implication flagging the
      current `ML_DIRECTIONAL_CONTINUOUS` / `ML_DIRECTIONAL_EVENT` § 6 topology_requirements rows (`no` co-location /
      min SLA `standard`) as a discrepancy the deployment-profile derivation todo resolves.
- [x] ✅ [DOC] P2. **Populate `rules-directional.md`** with the same section, category `Low` per operator correction —
      same greenfield situation as ml-directional. **Done**: `unified-trading-pm@a7bc00e23c` — formal
      `## Latency Requirements` section added (category `Low`; greenfield — archived `latency-profiles.md` has no Rules
      Directional row; closest analogs `Momentum` < 7s Medium / `Mean Reversion` < 3s Medium, the pre-v2 docs mapped to
      `RULES_DIRECTIONAL_CONTINUOUS`, are superseded by the 2026-08-10 operator ms-realm ruling). Segment budgets
      derived from the archived internal pipeline budgets (features <100ms single-instrument / strategy rule-evaluator
      <20ms / execution submit <50ms + the sports venue-latency table) — with the family's **no model-inference leg**
      noted as the differentiator from ml-directional (rule fires directly off features; tick-to-signal is
      feature-update-dominated). 3-row per-expression table (continuous single-instrument / continuous options
      expression / event-settled → totals <200ms / <200ms / <1s, all `Low`), the
      `### Decision latency vs. inter-leg execution gap` subsection (options synthetics + delta hedges at ms-realm
      inter-leg timing per the operator ruling
      (`/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md` frontmatter `source:`); in-play
      event-settled rules bounded by odds/feature freshness), and the Low→`co_located_vm` deployment implication
      flagging the current `RULES_DIRECTIONAL` § 6 topology_requirements row (`no` co-location / min SLA `basic` — the
      weakest of any latency-relevant family) as a discrepancy the deployment-profile derivation todo resolves. Same
      commit fixed a pre-existing bare-filename `related:` frontmatter reference (`ml-directional.md`/`event-driven.md`
      → leading-slash paths) flagged by plan-hygiene.
- [x] ✅ [DOC] P2. **Populate `stat-arb-pairs.md`** with the same section, category `Low`. **Done**:
      `unified-trading-pm@0004728881` — formal `## Latency Requirements` section added (category `Low`, archived
      Statistical Arb row confirmed as the baseline: <100ms / <100ms / venue-dep. / <200ms E2E; the cross-venue /
      cross-asset fixed-pair row borrows the archived Cross-Exchange Arb <300ms E2E ceiling; the cross-sectional row
      notes its rank-update-driven decision cadence), the `### Decision latency vs. inter-leg execution gap` subsection
      (same-venue ATOMIC pairs bounded by the family's Atomic multi-leg execution primitive; cross-venue / leader-lagger
      pairs the real risk surface — ms-realm operating target per the 2026-08-10 operator ruling
      (`/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md` frontmatter `source:`)), and
      the Low→`co_located_vm` deployment implication flagging the current `STAT_ARB_PAIRS` § 6 `topology_requirements`
      row (co-location `no` / min SLA `standard`) as a discrepancy the deployment-profile derivation todo resolves. Same
      commit fixed a pre-existing bare-filename `related:` frontmatter reference (`ml-directional.md` → leading-slash
      path) flagged by plan-hygiene.
- [x] ✅ [DOC] P3. **Populate `vol-trading.md`, `event-driven.md`, `portfolio.md`** with the same section — derive
      category from the archived doc's closest analog per the rubric table above; state the derivation reasoning inline
      in each doc so a future reader can see it wasn't a guess. **Done**: `unified-trading-pm@1fced39e8f` — formal
      `## Latency Requirements` sections added to all three family docs. vol-trading → `Medium` (archived Volatility Arb
      row confirmed as baseline: <10 s / <5 s / venue-dep. / <15 s E2E; intra-family fast subset `VOL_MARKET_MAKING` +
      `VOL_0DTE_GAMMA_SCALPING` flagged as the delta-hedge/inter-leg ms-realm edge for the derivation todo).
      event-driven → `Medium` (Momentum closest analog; pre-positioned + time-bounded content confirms seconds-scale
      decision, fast-urgency execution). portfolio → `High` (doc's own `latency_budget_ms` = 60 000 / 10 000 content
      decisive; archived Yield Optimization analog). All three carry the segment-budget table, the
      Medium/High→`distributed` deployment implication, and the `### Decision latency vs. inter-leg execution gap`
      subsection. Same commit fixed 2 pre-existing bare-filename `related:` frontmatter refs (`market-making.md` /
      `ml-directional.md` → leading-slash paths) flagged by plan-hygiene.
- [x] ✅ [DATA] P2. **Derive each archetype's required `deployment_profile`** (`co_located_vm` vs `distributed`) from
      the now-populated latency categories per the Low→co_located_vm / Medium+High→distributed rubric above — **Done**:
      `unified-trading-pm@41d6947e9c` — complete per-archetype deployment_profile derivation table written to
      `/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` (57 archetypes across 9 families); 7 INCONSISTENT §6 rows
      identified (all currently co-loc no → should be yes, SLA standard/basic → should be premium), ~37 MISSING rows
      flagged, 2 intra-family edge cases noted (VOL_MARKET_MAKING, VOL_0DTE_GAMMA_SCALPING), SLA-tier implication
      documented (all Low→co_located_vm require min SLA premium), decision-latency-vs-inter-leg-gap distinction per the
      2026-08-10 operator ruling at `/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`
      frontmatter `source:`.
- [x] ✅ [DATA] P2. **Check whether `isolation_policies.strategy-service`'s existing SLA-tier framework already accounts
      for `Low`-category archetypes needing more than the `premium` tier's 40ms budget provides** — some archived-doc
      figures (MM <100ms total E2E) fit inside 40ms; verify the others (arb <200-300ms, and the newly ms-realm-ruled
      basis/ML-directional/rules-based) against the `premium` tier's 40ms number and flag explicitly if any family's
      real requirement EXCEEDS what even the `premium` SLA tier currently promises — that's a real
      SLA-tier-vs-archetype-requirement gap worth surfacing, not silently absorbing. **Done**:
      `unified-trading-pm@9257f75c4c` — verdict: **NO, the framework does NOT account for it** — every Low family's real
      E2E requirement (MM <100ms / arb <200-300ms / basis+ML+rules+stat-arb ms-realm inter-leg gap) EXCEEDS premium's
      40ms `latency_budget_ms` (the brief's own "MM <100ms fits inside 40ms" example is arithmetically off — 100 > 40);
      the 40ms total-E2E promise is physically unachievable for live venue trades (order-to-fill floor 20-70ms alone);
      the 40ms metric does not address the inter-leg execution gap that drives `co_located_vm`; and
      `topology_enforcement.py` never cross-checks archetype `latency_budget_ms` vs tier budget. Full per-family
      comparison + the stale archetype-frontmatter finding (150-500ms / standard-basic for the corrected Low families) +
      5 invalid `min_sla_tier` enum values written to `/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md` for the
      execution plan / todo 10.
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
- **quant_dev (slot 11) 2026-08-10T15:21Z**: Todo 2 done. Added formal `## Latency Requirements` to
  `arbitrage-structural.md` (`unified-trading-pm@b62348bb59`): category `Low` — archived Statistical Arb /
  Cross-Exchange Arb / Sports Arbitrage rows confirmed as baseline (sub-second E2E), with the
  `### Decision latency vs. inter-leg execution gap` subsection distinguishing stat-arb/ATOMIC (atomicity bounds the
  gap) from cross-exchange arb's two-legs- on-two-venues leg-and-hedge gap (the real risk surface;
  `max_hedge_delay_ms: 500` = abort ceiling, operating target ms-realm) per the 2026-08-10 operator ruling, and the
  Low→`co_located_vm` deployment implication flagging the current `ARBITRAGE_STRUCTURAL` topology_requirements row (`no`
  co-location / min SLA `standard`) as a discrepancy the deployment-profile derivation todo resolves. Same commit fixed
  a pre-existing dangling `related:` frontmatter reference (`market-making.md` → leading-slash path).
- **quant_dev (slot 8) 2026-08-10T15:47Z**: Todo 4 done. Added formal `## Latency Requirements` to `ml-directional.md`
  (`unified-trading-pm@d631674085`): category `Low` — greenfield (archived `latency-profiles.md` has no ML Directional
  row; closest analogs `Mean Reversion`/`Prediction Contrarian` superseded by the 2026-08-10 operator ms-realm ruling),
  segment budgets derived from the archived internal pipeline budgets (features <100ms / warm ml-inference <50ms /
  strategy eval <20ms / execution submit <50ms) + sports venue-latency table. 3-row per-expression table (continuous
  single-instrument / continuous options expression / event-settled → totals <200ms / <200ms / <1s, all `Low`),
  `### Decision latency vs. inter-leg execution gap` subsection (options synthetics + delta hedges at ms-realm inter-leg
  timing; event-settled cross-venue best-odds freshness), and Low→`co_located_vm` deployment implication flagging the
  `ML_DIRECTIONAL_CONTINUOUS` / `ML_DIRECTIONAL_EVENT` § 6 topology_requirements rows (`no` co-location / min SLA
  `standard`) as a discrepancy the deployment-profile derivation todo resolves.
- **quant_dev (slot 8) 2026-08-10T16:10Z**: Todo 5 done. Added formal `## Latency Requirements` to
  `rules-directional.md` (`unified-trading-pm@a7bc00e23c`): category `Low` — greenfield (archived `latency-profiles.md`
  has no Rules Directional row; closest analogs `Momentum` < 7 s Medium / `Mean Reversion` < 3 s Medium, the pre-v2 docs
  mapped to `RULES_DIRECTIONAL_CONTINUOUS`, superseded by the 2026-08-10 operator ms-realm ruling), segment budgets
  derived from the archived internal pipeline budgets (features <100ms single-instrument / strategy rule-evaluator <20ms
  / execution submit <50ms) + sports venue-latency table, with the family's **no model-inference leg** noted as the
  differentiator from ml-directional (a rule fires directly off features; tick-to-signal is feature-update-dominated).
  3-row per-expression table (continuous single-instrument / continuous options expression / event-settled → totals
  <200ms / <200ms / <1s, all `Low`), `### Decision latency vs. inter-leg execution gap` subsection (options synthetics +
  delta hedges at ms-realm inter-leg timing; in-play event-settled rules bounded by odds/feature freshness), and Low→
  `co_located_vm` deployment implication flagging the current `RULES_DIRECTIONAL` § 6 topology_requirements row (`no`
  co-location / min SLA `basic`) as a discrepancy the deployment-profile derivation todo resolves. Same commit fixed a
  pre-existing bare-filename `related:` frontmatter reference (`ml-directional.md`/`event-driven.md` → leading-slash
  paths) flagged by plan-hygiene.
- **quant_dev (slot 8) 2026-08-10T16:26Z**: Todo 6 done. Added formal `## Latency Requirements` to `stat-arb-pairs.md`
  (`unified-trading-pm@0004728881`): category `Low` — archived Statistical Arb row confirmed as the baseline (<100ms /
  <100ms / venue-dep. / <200ms E2E; the cross-venue / cross-asset fixed-pair row borrows the archived Cross-Exchange Arb
  <300ms E2E ceiling, the cross-sectional row noting its rank-update-driven decision cadence),
  `### Decision latency vs. inter-leg execution gap` subsection (same-venue ATOMIC pairs bounded by the family's Atomic
  multi-leg execution primitive; cross-venue / leader-lagger pairs the real risk surface with an ms-realm operating
  target per the 2026-08-10 operator ruling), and Low→`co_located_vm` deployment implication flagging the current
  `STAT_ARB_PAIRS` § 6 topology_requirements row (`no` co-location / min SLA `standard`) as a discrepancy the
  deployment-profile derivation todo resolves. Same commit fixed a pre-existing bare-filename `related:` frontmatter
  reference (`ml-directional.md` → leading-slash path) flagged by plan-hygiene.
- **quant_dev (slot 11) 2026-08-10T17:05Z**: Todo 7 done. Populated the final three family docs
  (`unified-trading-pm@1fced39e8f`): vol-trading / event-driven → `Medium`, portfolio → `High`, each with the derived
  category reasoning stated inline (not a guess) per the audit rubric, the segment-budget table, the
  Medium/High→`distributed` deployment implication, and the `### Decision latency vs. inter-leg execution gap`
  subsection. vol-trading: archived Volatility Arb row (<10 s / <5 s / venue-dep. / <15 s E2E) confirmed as baseline;
  intra-family fast subset (`VOL_MARKET_MAKING`, `VOL_0DTE_GAMMA_SCALPING`) + the delta-hedge inter-leg gap flagged as
  the ms-realm edge for the derivation todo. event-driven: Momentum closest analog; pre-positioned entry + time-bounded
  minutes window confirms seconds-scale decision, fast-urgency execution policy during the window. portfolio: the doc's
  own `latency_budget_ms` = 60 000 / 10 000 (Alpha thesis) is decisive → `High`, archived Yield Optimization analog
  confirms. Deployment implications note current § 6 `topology_requirements` state: `VOL_TRADING` row already consistent
  with `distributed` (no discrepancy, unlike the Low families); no `EVENT_DRIVEN` / `PORTFOLIO` row exists yet —
  derivation todo should add them at `distributed`-consistent settings. Same commit fixed 2 pre-existing bare-filename
  `related:` frontmatter refs (`market-making.md` / `ml-directional.md` → leading-slash paths) flagged by plan-hygiene.
- **data_engineering (slot 6) 2026-08-10T19:01Z**: Todo 8 done. Checked `isolation_policies.strategy-service`'s existing
  SLA-tier framework vs the `premium` tier's 40ms `latency_budget_ms` against every Low-category family's populated
  latency requirement (`unified-trading-pm@9257f75c4c`, full section appended to
  `/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`). Verdict: **NO — the framework does not account for Low
  archetypes needing more than premium's 40ms provides**; every Low family's real E2E requirement EXCEEDS 40ms (MM
  <100ms, arb <200-300ms, basis/ML/rules/stat-arb ms-realm inter-leg gap; even the brief's own "MM <100ms fits inside
  40ms" example is off — 100 > 40). Also surfaced: (1) premium's 40ms total-E2E is physically unachievable for live
  venue trades (order-to-fill floor 20-70ms on CeFi venues per the same family docs), (2) the 40ms metric does not
  address the inter-leg execution gap that actually drives `co_located_vm`, (3) `topology_enforcement.py` parses the
  archetype `latency_budget_ms` but never cross-checks it against the active tier budget, (4) the runtime-enforced
  archetype frontmatter (`archetypes/*.md` `topology_requirements`) is STALE for the corrected Low families —
  `CARRY_BASIS_PERP`/`ML_DIRECTIONAL_CONTINUOUS`/`STAT_ARB_PAIRS_FIXED` at 150ms-standard,
  `RULES_DIRECTIONAL_CONTINUOUS` at 500ms-basic, all `co_location: []` — contradicting Low→`co_located_vm`→premium, so
  the runtime gate currently PERMITS these on the wrong tier without co-location, and (5) 5 archetype docs declare
  `min_sla_tier` values outside the UAC `SLATier` enum (`high` ×4 arbitrage-mev-*, `ultra-premium` ×1
  market-making-queue-microstructure) that raise on the `SLATier()` cast under enforcement. All captured as input to the
  execution plan / todo 10 decision artifact.
