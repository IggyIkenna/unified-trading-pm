---
name: questions-directory
overview:
  Architectural Q&A staging — operator questions become canonical plans via audit + back-and-forth + codex SSOT
  alignment.
type: process
status: active
created: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

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
3. **Q&A back-and-forth** — operator + agent iterate on the question. Operator adds insight + direction; agent
   re-audits gaps; both converge on the ideal shape. Iterations live in `## Operator notes` + `## Iteration log`
   sections of the question doc.
4. **Plan extraction** — once shape is converged, the question doc spawns a canonical plan in
   `plans/active/<slug>_<YYYY_MM_DD>.md` (or fold-into existing master / epic). Plan body cites the question doc as
   `spawned_from:`.
5. **Codex SSOT alignment** — plan body lists every codex doc that NEW or UPDATE describes the architecture being
   built. Plan-of-record links to the codex SSOTs; codex SSOTs back-link to the plan.

The question doc itself stays in `plans/questions/` as the **archaeology layer** — it preserves the question + the
audit findings + the back-and-forth that informed the plan. Don't archive the question doc when the plan ships;
archive it when the plan ships AND the codex SSOTs are durable.

## What an "audit" actually checks (the "real prod-readiness" bar)

Per the workspace HARD RULE _"Plans Run To Actual Completion, Not Smoke-Test Green"_ — the audit is NOT a code-grep.
It must answer all of:

- **Code shipped?** Symbols exist, tests pass locally + on remote CI.
- **Data on disk?** If the question involves data flow, the manifest has captured rows + sample parquets are populated
  (not 1440-NaN placeholders).
- **End-to-end run?** A VM, cron, or operator has actually run the full path against real infra — not just CI smoke
  against mocks.
- **Production-mode runnable today?** Could the operator launch this against real AWS/GCP, real venue keys, real
  wallet, real client data **right now** — or are there blockers (missing IAM, missing UI surface, missing alerting
  wire, missing reconciler, missing operator approval)?
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

| Date         | Author              | Change           |
| ------------ | ------------------- | ---------------- |
| <YYYY-MM-DD> | <agent / operator>  | <what changed>   |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: <plans/active/<slug>_<date>.md or plans/epics/<slug>.md>
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
- **Cross-link aggressively** — `related_codex:` + `related_plans:` frontmatter so search surfaces overlap with
  existing work.
- **Commit on creation** — uncommitted question docs have been lost twice this week to parallel-agent shared-tree
  activity. The `git add <doc> && git commit --no-verify -m "..." && git push` cycle is part of the question-doc
  creation logical unit, not a separate task.

## Composes with

- **Plan Format SSOT** (`plans/PLAN_FORMAT.md`) — the canonical plan that gets spawned from a question doc follows
  this shape.
- **Citadel-Grade Planning Standards** (CLAUDE.md § "Citadel-Grade Planning Standards") — pre-audit + phased DAG +
  no tech debt + parallelization + success criteria + downstream consumer updates + SSOT discipline. The audit pass
  in step 2 IS the pre-audit.
- **Plans Run To Actual Completion HARD RULE** (CLAUDE.md) — the audit checks for real-infra completion, not
  code-shipped.
- **Post-Plan-Phase Codex Audit HARD RULE** (CLAUDE.md) — the codex SSOT alignment in step 5 is the codification
  surface.
- **Findings Triage Discipline** (CLAUDE.md) — findings during the audit pass route per case 1-5.
- **Commit + Push + Flip HARD RULE** (CLAUDE.md) — every shippable unit (including a brand-new question doc) commits +
  pushes immediately. Drafting in working tree without committing is the loss-of-work foot-gun this directory has hit
  twice already.

## Active backlog

Question docs land here as the operator raises them. Active set as of 2026-05-10:

| Doc                                                                                                                                            | Topic                                                                                                                                                                                                                                                                                                                                                                                                            | Status              |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| [`api_keys_wallets_accounts_readiness_2026_05_08.md`](api_keys_wallets_accounts_readiness_2026_05_08.md)                                       | Credential audit — every API key, wallet, service account, IAM role, secret, custody endpoint across AWS + GCP infra, all venues, Copper + CEFFU custody, all DeFi chains + RPC + Tenderly + flash-loan receivers, all data sources, all auxiliary services, scoped per mode (paper/batch/live) and per archetype                                                                                              | plan-spawned        |
| [`backfill_manifest_schema_freeze_gate_2026_05_08.md`](backfill_manifest_schema_freeze_gate_2026_05_08.md)                                     | Manifest schema freeze gate — when can we promise downstream consumers a stable manifest contract                                                                                                                                                                                                                                                                                                                | drafting            |
| [`batch_live_design_symmetry_2026_05_08.md`](batch_live_design_symmetry_2026_05_08.md)                                                         | Batch=Live design symmetry — every place where backtest and live diverge architecturally + how to reconcile                                                                                                                                                                                                                                                                                                      | drafting            |
| [`client_reporting_pnl_attribution_2026_05_08.md`](client_reporting_pnl_attribution_2026_05_08.md)                                             | Client reporting API + UI: NAV / PnL / metrics per client, invoicing, PnL attribution (internal-strategy vs external-strategy via API keys), service-offerability                                                                                                                                                                                                                                              | drafting (re-spawned 2026-05-10) |
| [`codex_vs_citadel_infrastructure_specs_2026_05_08.md`](codex_vs_citadel_infrastructure_specs_2026_05_08.md)                                   | Fresh-eyes audit: codex / 67-repo / CLAUDE.md / runtime architecture vs an idealised Citadel-grade non-HFT combination system optimised for alpha velocity + error-free correctness. KEEP / LIFT / CONSOLIDATE / DELETE / ADD per area                                                                                                                                                                          | iterating           |
| [`defi_readiness_catalogue_2026_05_08.md`](defi_readiness_catalogue_2026_05_08.md)                                                             | DeFi venue / asset / pool / LST / lending / perp catalogue + per-venue data-type taxonomy + Solana coverage + AMM slippage + rate-impact + governance-sim primitives + RPC + MEV protection + Tenderly hookups; cross-asset-group catalogue gap-check                                                                                                                                                          | audit-in-progress   |
| [`defi_recursive_borrow_archetypes_2026_05_08.md`](defi_recursive_borrow_archetypes_2026_05_08.md)                                             | DeFi recursive-borrow archetype family — leveraged LST / leveraged staking with per-iteration risk model + flash-loan unwind path                                                                                                                                                                                                                                                                                | drafting            |
| [`disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md`](disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md)           | Disaster-recovery + reconciliation + circuit-breaker wire-up across asset_groups + venues + custody, with SSOT-best-possible bar                                                                                                                                                                                                                                                                                | drafting            |
| [`paper_vs_live_workflow_maturity_2026_05_08.md`](paper_vs_live_workflow_maturity_2026_05_08.md)                                               | Paper-vs-live workflow maturity — per-archetype paper-readiness + execution-seam + mock-data carve-out + master Group F/G fold-in                                                                                                                                                                                                                                                                                | iterating           |
| [`risk_simulations_limits_alerting_2026_05_08.md`](risk_simulations_limits_alerting_2026_05_08.md)                                             | Risk monitor vs risk simulations vs risk alerts vs pre-flight risk checks: wire-up across system, dimensions (venue/account/strategy/client), per instrument-type + strategy-family/archetype, consequences of failure (block vs monitor vs test). Owner of canonical circuit-breaker rule taxonomy                                                                                                            | drafting (re-spawned 2026-05-10, low-fidelity) |
| [`topology_features_strategy_ml_execution_2026_05_08.md`](topology_features_strategy_ml_execution_2026_05_08.md)                               | Topology audit: features → strategy → ML → execution data flow + service boundaries + lookahead bias surfaces                                                                                                                                                                                                                                                                                                    | iterating           |
| [`wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md`](wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md)             | End-to-end client lifecycle — onboarding → treasury / wallet / custody → allocation across 50+ archetypes × share-class derivatives → post-trade settlement + reconcile + fee accrual + perf-fee crystallization + statements + withdrawal — per asset_group                                                                                                                                                  | drafting            |

Add new rows as question docs land. Update `Status` column when a doc moves through the lifecycle phases.
