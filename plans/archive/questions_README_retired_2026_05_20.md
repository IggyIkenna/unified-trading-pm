---
doc_type: plan
title: questions-directory
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
overview:
  Architectural Q&A staging — operator questions become canonical plans via audit + back-and-forth + codex SSOT
  alignment.
type: process
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# `plans/questions/` — Architectural question staging

This directory is the **pre-plan staging surface** for big architectural topics the operator wants worked through
end-to-end before they become canonical plans in `plans/active/` or `plans/epics/`.

The workflow exists because the operator has a backlog of architectural questions (client reporting, risk, custody,
treasury, ML lifecycle, etc.) that aren't ready to be plans yet — they need an audit-and-discuss cycle first to surface
what already exists, what's actually production-ready (vs code-shipped-but-never-run), and what the right shape is.

## Lifecycle of a question doc

Each question doc moves through 5 phases:

1. **Question written** — operator (or main agent on operator's behalf) drafts the question doc using the template
   below. The doc captures intent + sub-questions + scope, NOT answers. **Commit immediately on creation** per the
   workspace Commit+Push+Flip HARD RULE — uncommitted question docs have been lost twice this week (2026-05-08
   wallet_treasury + 2026-05-10 client_reporting/risk_simulations/README) to parallel-agent shared-tree activity. See
   [`plans/active/issues/missing_question_docs_orphan_references_2026_05_10.md`](../active/issues/missing_question_docs_orphan_references_2026_05_10.md)
   for the canonical incident reference.
2. **Audit pass** — agent runs a real-state audit across the workspace: code, codex docs, plans (active + archived),
   data on disk, manifest state, deployed services, test coverage, end-to-end completion evidence. **Audit must answer
   "can I run this today against real data, outside mock?" — not "does the code exist?"** Findings go into the
   `## Audit findings` section of the question doc.
3. **Q&A back-and-forth** — operator + agent iterate on the question. Operator adds insight + direction; agent re-audits
   gaps; both converge on the ideal shape. Iterations live in `## Operator notes` + `## Iteration log` sections of the
   question doc.
4. **Plan extraction** — once shape is converged, the question doc spawns a canonical plan in
   `plans/active/<slug>_<YYYY_MM_DD>.md` (or fold-into existing master / epic). Plan body cites the question doc as
   `spawned_from:`.
5. **Codex SSOT alignment** — plan body lists every codex doc that NEW or UPDATE describes the architecture being built.
   Plan-of-record links to the codex SSOTs; codex SSOTs back-link to the plan.

The question doc itself stays in `plans/questions/` as the **archaeology layer** — it preserves the question + the audit
findings + the back-and-forth that informed the plan. Don't archive the question doc when the plan ships; archive it
when the plan ships AND the codex SSOTs are durable.

## What an "audit" actually checks (the "real prod-readiness" bar)

Per the workspace HARD RULE _"Plans Run To Actual Completion, Not Smoke-Test Green"_ — the audit is NOT a code-grep. It
must answer all of:

- **Code shipped?** Symbols exist, tests pass locally + on remote CI.
- **Data on disk?** If the question involves data flow, the manifest has captured rows + sample parquets are populated
  (not 1440-NaN placeholders).
- **End-to-end run?** A VM, cron, or operator has actually run the full path against real infra — not just CI smoke
  against mocks.
- **Production-mode runnable today?** Could the operator launch this against real AWS/GCP, real venue keys, real wallet,
  real client data **right now** — or are there blockers (missing IAM, missing UI surface, missing alerting wire,
  missing reconciler, missing operator approval)?
- **Codex SSOT covers it?** Is there a codex doc describing the architecture, or is the system implicit-knowledge-only?
- **Service-readiness checklist coverage** (per master plan Groups A-G, 23 items) — which gates are green per the
  affected service?

If the audit says "code shipped but never run against real data" — that's a finding. If "ran once 3 weeks ago but no
continuous verification" — that's a finding. If "lives only in one operator's head" — that's a finding.

## Question-doc template (paste into new question docs)

```markdown
---
name: <topic-slug>
overview: <one-line — what's the question>
type: question
status: drafting | audit-in-progress | iterating | plan-spawned | closed
created: <YYYY-MM-DD>
operator: <ikenna | harsh>
locked_by: live-defi-rollout
locked_since: <YYYY-MM-DD>
spawned_plan: <path to plan once it exists, else null>
related_codex:
  - <codex doc path that describes the area today, if any>
related_plans:
  - <existing master / epic / sub-plan that touches this scope>
---

# <Title>

## Intent

2-4 paragraphs: what's the topic, why it matters, why the operator is raising it now. NO answers — only the framing.

## Question

The operator's question, broken into sub-questions. Each sub-question explicit enough that an audit pass can produce
findings against it. Use bullets / numbered lists; don't try to write prose at this stage.

## What "answered" looks like

3-6 bullet points enumerating what would close the question:

- a canonical plan exists in `plans/active/`
- codex SSOT(s) at <paths> describe the architecture
- a real-data run / e2e completion has shipped (or is scheduled with named owner + cron)
- service-readiness checklist gates are X / Y / Z green
- alerting / reconciliation rules wired
- UI surface visible / operator can self-serve

## Audit findings (to be filled by audit pass)

For each sub-question:

- **Code state**: <what exists in repos, file:line citations>
- **Data state**: <manifest rows, sample parquets, real-data evidence>
- **Run state**: <when last ran end-to-end against real infra, who, what was the outcome>
- **Codex state**: <which codex docs cover it, drift vs current code, gaps>
- **Gap analysis**: <what's missing for the "answered" criteria>

## Operator notes / answers

Iterative — operator adds direction, decisions, context the audit can't surface.

## Iteration log

| Date         | Author             | Change         |
| ------------ | ------------------ | -------------- |
| <YYYY-MM-DD> | <agent / operator> | <what changed> |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: <plans/active/<slug>\_<date>.md or plans/epics/<slug>.md>
- **Plan type**: code / infra / business / mixed
- **Owner side**: ikenna / harsh / both
- **Codex SSOTs touched** (list every NEW + UPDATE):
  - <codex doc path> — NEW / UPDATE — <one-line shape>
- **Cross-plan dependencies**:
  - <plan path> — <how it composes>
- **Estimated scope**: <AI-day estimate>

## Plan extraction record

Filled when the plan ships:

- Plan path: <plans/active/...>
- Spawned commit: <PM@sha>
- Codex updates committed: <list of codex@sha>
- Question doc closes (status: closed) when: <criterion>
```

## Conventions

- **Filename**: `<topic-slug>_<YYYY_MM_DD>.md` — same convention as plans, kebab-case, dated.
- **Status field** drives discovery: `status: drafting` (just written, no audit yet), `audit-in-progress`, `iterating`,
  `plan-spawned` (active plan exists, question doc is reference), `closed` (plan shipped + codex aligned + question doc
  archaeology only).
- **Don't write the answer at draft time** — the audit + operator iteration is the value. A question doc with answers
  pre-written is a plan in disguise; ship it as a plan.
- **One topic per doc** — if a question has 3 unrelated sub-areas, it's 3 question docs. Folding multiple topics into
  one doc breaks SSOT discipline + complicates plan extraction.
- **Cross-link aggressively** — `related_codex:` + `related_plans:` frontmatter so search surfaces overlap with existing
  work.
- **Commit on creation** — uncommitted question docs have been lost twice this week to parallel-agent shared-tree
  activity. The `git add <doc> && git commit --no-verify -m "..." && git push` cycle is part of the question-doc
  creation logical unit, not a separate task.

## Composes with

- **Plan Format SSOT** (`plans/PLAN_FORMAT.md`) — the canonical plan that gets spawned from a question doc follows this
  shape.
- **Citadel-Grade Planning Standards** (CLAUDE.md § "Citadel-Grade Planning Standards") — pre-audit + phased DAG + no
  tech debt + parallelization + success criteria + downstream consumer updates + SSOT discipline. The audit pass in step
  2 IS the pre-audit.
- **Plans Run To Actual Completion HARD RULE** (CLAUDE.md) — the audit checks for real-infra completion, not
  code-shipped.
- **Post-Plan-Phase Codex Audit HARD RULE** (CLAUDE.md) — the codex SSOT alignment in step 5 is the codification
  surface.
- **Findings Triage Discipline** (CLAUDE.md) — findings during the audit pass route per case 1-5.
- **Commit + Push + Flip HARD RULE** (CLAUDE.md) — every shippable unit (including a brand-new question doc) commits +
  pushes immediately. Drafting in working tree without committing is the loss-of-work foot-gun this directory has hit
  twice already.

## Status as of 2026-05-10 — directory is now archaeology

> **🟢 ALL QUESTIONS PLAN-SPAWNED.** Every doc in this directory has a corresponding active plan in `plans/active/` (or
> a multi-plan fold-in for cross-cutting questions) with a complete-by-2026-05-23 phased process, full-execution
> criteria per phase, codex SSOT updates enumerated, and cutover-gate integration. Per operator direction 2026-05-10
> (_"questions directory is pointless and active has all the answers and the processes to complete everything before
> 23rd May, no exceptions"_), this directory is no longer the staging surface — the active plans are. New architectural
> questions should land directly as active plans (or as `plans/active/issues/<slug>_<date>.md` issue docs if scope isn't
> owner-clear yet, per Findings Triage Discipline). The question docs preserved here are the **archaeology** — they
> record the operator's framing + the audit findings + the back-and-forth that informed the plan, but the active
> orchestration surface is the spawned plan(s).
>
> Every active plan listed below carries the May-23 deadline, full-execution criterion per phase per the _"Plans Run To
> Actual Completion, Not Smoke-Test Green"_ HARD RULE, and a deferred-work table for breadth that physically cannot ship
> in the 13-day cutover sprint (multi-quarter compliance, full multi-client invoicing, full chaos-drill cadence, etc. —
> each named with a successor plan).

## Active backlog (all plan-spawned)

| Doc                                                                                                                                  | Topic                                                                                                                                                                                                             | Spawned plan(s)                                                                                                                                                                                                                                                                                                                                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`api_keys_wallets_accounts_readiness_2026_05_08.md`](api_keys_wallets_accounts_readiness_2026_05_08.md)                             | Credential audit — keys / wallets / service accounts / custody across AWS+GCP, venues, Copper+CEFFU, DeFi RPCs+receivers, data sources, aux. Per-mode + per-archetype.                                            | [`api_keys_wallets_accounts_readiness_2026_05_10`](../active/api_keys_wallets_accounts_readiness_2026_05_10.md)                                                                                                                                                                                                                                                                                                                             |
| [`backfill_manifest_schema_freeze_gate_2026_05_08.md`](backfill_manifest_schema_freeze_gate_2026_05_08.md)                           | Manifest schema freeze gate — stable downstream contract.                                                                                                                                                         | [`manifest_schema_final_gate_2026_05_09`](../active/manifest_schema_final_gate_2026_05_09.md) (+ manifest_v7 + gcs_migration_bundle siblings)                                                                                                                                                                                                                                                                                               |
| [`batch_live_design_symmetry_2026_05_08.md`](batch_live_design_symmetry_2026_05_08.md)                                               | Batch=Live total design-path symmetry across services / events / UI / analytics / manifest schema / static enforcement.                                                                                           | [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) + [`live_pipeline_mtds_mdps_features_2026_05_08`](../active/live_pipeline_mtds_mdps_features_2026_05_08.md) + [`writegate_honest_coverage_endtoend_2026_05_06`](../active/writegate_honest_coverage_endtoend_2026_05_06.md) + [`simulation_scenarios_topology_price_shocks_2026_05_09`](../active/simulation_scenarios_topology_price_shocks_2026_05_09.md) |
| [`client_reporting_pnl_attribution_mvp_2026_05_10.md`](../archive/client_reporting_pnl_attribution_mvp_2026_05_10.md)                | Client reporting API + UI: NAV / PnL / metrics per client, invoicing, PnL attribution (internal vs external strategy), service-offerability.                                                                      | [`client_reporting_pnl_attribution_mvp_2026_05_10`](../archive/client_reporting_pnl_attribution_mvp_2026_05_10.md)                                                                                                                                                                                                                                                                                                                          |
| [`codex_vs_citadel_infrastructure_specs_2026_05_08.md`](codex_vs_citadel_infrastructure_specs_2026_05_08.md)                         | Fresh-eyes audit: codex / 67-repo / CLAUDE.md / runtime architecture vs Citadel-grade non-HFT combination system. KEEP / LIFT / CONSOLIDATE / DELETE / ADD per area.                                              | [`codex_vs_citadel_infrastructure_audit_2026_05_10`](../active/codex_vs_citadel_infrastructure_audit_2026_05_10.md)                                                                                                                                                                                                                                                                                                                         |
| [`defi_readiness_catalogue_2026_05_08.md`](defi_readiness_catalogue_2026_05_08.md)                                                   | DeFi venue / asset / pool / LST / lending / perp / oracle / bridge catalogue + Solana + AMM slippage + RPC + MEV + Tenderly + cross-asset-group catalogue gap-check.                                              | [`defi_catalogue_chain_primitives_2026_05_10`](../active/defi_catalogue_chain_primitives_2026_05_10.md) + [`defi_simulation_realism_2026_05_10`](../active/defi_simulation_realism_2026_05_10.md)                                                                                                                                                                                                                                           |
| [`defi_recursive_borrow_archetypes_2026_05_08.md`](defi_recursive_borrow_archetypes_2026_05_08.md)                                   | DeFi recursive-borrow archetype family — leveraged LST / leveraged staking with per-iteration risk model + flash-loan unwind.                                                                                     | [`defi_recursive_borrow_archetypes_2026_05_10`](../active/defi_recursive_borrow_archetypes_2026_05_10.md)                                                                                                                                                                                                                                                                                                                                   |
| [`disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md`](disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md) | DR + reconciliation across positions / balances / custody / on-chain / events / manifest, circuit-breaker taxonomy, recovery playbooks per failure scenario, chaos-drill cadence.                                 | [`disaster_recovery_circuit_breakers_2026_05_10`](../active/disaster_recovery_circuit_breakers_2026_05_10.md)                                                                                                                                                                                                                                                                                                                               |
| [`mock_data_pipeline_benchmarking_2026_05_10.md`](mock_data_pipeline_benchmarking_2026_05_10.md)                                     | Synthetic-data path to benchmark feature / ML / strategy / execution-backtest bottlenecks on a VM today — schema knowledge, generators, harness, per-stage profile, VM-shape sizing.                              | [`mock_data_pipeline_benchmarking_2026_05_10`](../active/mock_data_pipeline_benchmarking_2026_05_10.md)                                                                                                                                                                                                                                                                                                                                     |
| [`paper_vs_live_workflow_maturity_2026_05_08.md`](paper_vs_live_workflow_maturity_2026_05_08.md)                                     | Paper-vs-live workflow maturity per archetype + execution-seam + DART visualization toggle + automated-vs-manual e2e setting.                                                                                     | [`master_to_live_defi_2026_05_23`](../active/master_to_live_defi_2026_05_23.md) (Group F items 17/18/20/21/22 + Group G item 23 sub-items)                                                                                                                                                                                                                                                                                                  |
| [`promote_workflow_backtest_to_paper_to_live_2026_05_08.md`](promote_workflow_backtest_to_paper_to_live_2026_05_08.md)               | Promote workflow re-audit: backtest → score → rank → click → candidate → paper → live. State machine, events, DART gate, configuration capture, custody+risk+alerting wire-up, rollback. May-23 cutover-critical. | [`promote_workflow_may23_cli_path_2026_05_10`](../active/promote_workflow_may23_cli_path_2026_05_10.md) + [`promote_workflow_post_cutover_ui_pipeline_2026_05_10`](../active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)                                                                                                                                                                                                       |
| [`risk_simulations_limits_alerting_2026_05_10.md`](../archive/risk_simulations_limits_alerting_2026_05_10.md)                        | Risk monitor / simulations / alerts / pre-flight checks. Per-archetype × per-venue × per-account × per-client × per-asset_group. Consequences closed enum (BLOCK / SCALE_DOWN / MONITOR / TEST).                  | [`risk_simulations_limits_alerting_2026_05_10`](../archive/risk_simulations_limits_alerting_2026_05_10.md) + [`disaster_recovery_circuit_breakers_2026_05_10`](../active/disaster_recovery_circuit_breakers_2026_05_10.md) (composes for breakers + recovery)                                                                                                                                                                               |
| [`topology_features_strategy_ml_execution_2026_05_08.md`](topology_features_strategy_ml_execution_2026_05_08.md)                     | Topology Q-group: features / strategy ensemble / ML / execution × batch / live / paper.                                                                                                                           | [`live_pipeline_mtds_mdps_features_2026_05_08`](../active/live_pipeline_mtds_mdps_features_2026_05_08.md) + [`features_repo_consolidation_2026_05_08`](../active/features_repo_consolidation_2026_05_08.md) + epics under `plans/epics/`                                                                                                                                                                                                    |
| [`wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md`](wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md)   | Client lifecycle: onboarding → treasury (Copper + CEFFU + DeFi PK + sub-accounts) → allocation → post-trade settlement + reconcile + fee accrual + statements + withdrawal — per asset_group.                     | [`wallet_treasury_client_flow_2026_05_10`](../active/wallet_treasury_client_flow_2026_05_10.md)                                                                                                                                                                                                                                                                                                                                             |

**Net result.** 13 question docs → 13 plan-spawned. Cross-cutting questions (batch_live_design_symmetry, paper_vs_live,
topology, risk-with-DR-overlap) fold into multiple plans rather than spawning a single new plan — the principle is
"every question has a complete-by-May-23 process," not "every question gets a 1:1 plan." All cutover-MVP scope ships by
2026-05-23; breadth that physically cannot ship in 13 days lives in the per-plan `## Deferred work` tables with named
successor plans.

**Plus the simulation-scenarios plan** that is plan-only-no-question-doc:
[`simulation_scenarios_topology_price_shocks_2026_05_09`](../active/simulation_scenarios_topology_price_shocks_2026_05_09.md)
— synthetic adversarial-condition injection (topology gaps + staleness + price shocks + venue outages) through prod
codepaths; per-archetype regression matrix gating cutover.

## New questions

If you have a new architectural question after 2026-05-10, prefer one of:

1. **Drop it directly as a plan in `plans/active/<slug>_<date>.md`** (or `plans/epics/<slug>.md` for an umbrella) using
   `plans/PLAN_FORMAT.md`. Most questions about real surfaces are now plans-in-disguise; spend the 30 min auditing what
   exists and ship the plan.
2. **Drop it as an issue doc in `plans/active/issues/<slug>_<date>.md`** if scope isn't owner-clear yet — per Findings
   Triage Discipline. Issue docs triage to (1) within ≤7 calendar days.
3. **Question doc only as a last resort** — when the topic is genuinely too unstructured to plan against today and needs
   an audit pass first. Even then, the question doc must close to a plan within 7 days; longer-lived question docs are
   themselves a finding.
