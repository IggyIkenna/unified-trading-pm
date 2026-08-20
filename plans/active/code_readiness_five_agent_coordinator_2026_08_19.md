---
doc_type: plan
title: Code readiness — five-agent coordinator and launch prompts
summary: >-
  Coordinator for the five-agent code-readiness push. Carries the tranche map, the shared goalpost, the
  cross-tranche dependency edges and the ready-to-paste launch prompt for each of the five parallel agents.
  Every one of the 892 active plan and issue docs is allocated to exactly one tranche.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [code-readiness, coordinator, five-agent, launch-prompts, tranche-map]
related:
  [
    /plans/epics/system_readiness_master.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md,
    /plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md,
  ]
created: 2026-08-19
last_updated: 2026-08-20
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 210
estimate_calibrated_ai_days: 84
locked_by:
locked_since:
context_scope:
  [
    /plans/epics/system_readiness_master.md,
    /plans/audit/results/code_completion_scope_2026_08_19.md,
    /plans/audit/results/code_readiness_allocation_2026_08_19.json,
    /codex/05-infrastructure/per-tab-worktrees.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
supersedes:
superseded_by:
depends_on:
source: >-
  Operator directive 2026-08-19 — allocate every active plan and issue across five parallel autonomous agents and
  drive the four client artefacts to code-ready, excluding manifest migration and data backfills.
assigned_role: project_management
effort: high # coordination + launch doc; the heavy reasoning lives in the five tranche plans
drift_direction: advance-code
---

# Code readiness — five-agent coordinator

> **The goalpost.** Everything is complete **in code**. The only things that may still be pending are (1) backfills
> still running, (2) venue connectivity — private and public feed, orders and trades, (3) market data live,
> (4) testnets where they exist, (5) strategy archetypes code-ready for batch/paper/live pending real-data testing.
> Anything else not code-complete is remaining work. SSOT: `/plans/epics/system_readiness_master.md` § "Definition
> of done".

## The acceptance test

Four client-sendable artefacts must stop carrying `pending`, `planned`, `partial`, `not built` or `unverified` on
any claim outside those five states. Measured 2026-08-19 at authoring:

| Artefact | unverified | partial | pending | planned | not yet | not built | missing |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `platform-external-api-walkthrough.html` | 29 | 17 | 28 | 17 | 14 | 5 | 6 |
| `strategy-service-deep-dive.html` | 51 | 15 | 2 | 3 | 7 | 1 | 1 |
| `strategy-service-walkthrough.html` | 3 | 23 | 3 | 3 | 11 | 1 | 1 |
| `platform-architecture.html` | 0 | 18 | 1 | 2 | 7 | 1 | 1 |

Their status markers carry `owner: W1`…`W22` tags binding each claim to a workstream in the epic. **Closing a
W-item is what clears its marker — never clear one by editing the HTML.** The headline number to move is the
readiness matrix: **288 venues × 3 modes = 864 rows, today 0 ready / 844 not_ready / 20 unverified.**

## Tranche map — repo-disjoint by construction

Two agents never edit the same file, because no repo appears in two tranches.

| Tranche | Owns repos | Docs | Spine | Open todos | Plan |
| --- | --- | ---: | ---: | ---: | --- |
| **T1** contracts, library, external API | unified-api-contracts, unified-trading-library, unified-trading-api, deployment-api, deployment-ui, unified-trading-system-ui | 62 | 11 | 130 | `/plans/active/code_readiness_t1_contracts_library_externalapi_2026_08_19.md` |
| **T2** reference and market data | instruments-service, market-tick-data-service, market-data-processing-service | 293 | 28 | 753 | `/plans/active/code_readiness_t2_refdata_marketdata_2026_08_19.md` |
| **T3** features, ML, strategy | features-service, ml-service, strategy-service | 77 | 25 | 338 | `/plans/active/code_readiness_t3_features_ml_strategy_2026_08_19.md` |
| **T4** execution and settlement | execution-service, batch-live-reconciliation-service, fund-administration-service, greeks-service, client-reporting-api, trading-agent-service, ibkr-gateway-infra | 27 | 11 | 203 | `/plans/active/code_readiness_t4_execution_settlement_2026_08_19.md` |
| **T5** readiness, observability, artefacts | deployment-service, alerting-service, e2e-testing, system-integration-tests, unified-trading-ci, agent-orchestrator, unified-trading-pm | 433 | 19 | 1180 | `/plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md` |

**892 docs, 2,604 open todos, 94 spine docs** — allocation is machine-derived and reproducible via
`scripts/plan-hygiene/allocate_code_readiness_tranches.py`, output at
`/plans/audit/results/code_readiness_allocation_2026_08_19.json`. "Spine" = the doc backs a claim in one of the
four artefacts or in the epic; work spine first, tail second.

**Doc counts are not workload.** T5 holds 433 docs but only 19 spine — its tail is AO, CI and plan-hygiene tooling
that does not make the artefacts code-ready. T4 holds 27 docs but owns the single check that unblocks 844 rows.

## Critical path — launch T1 first

```
T1 (contracts) ──┬─→ T4 QuoteInstruction: delta / gamma / underlying_instrument_id
                 ├─→ T3 + T4 StrategyInstructionEnvelope: reference_position + credit
                 └─→ T4 OrderState 9-state machine

T3 strategy position adapters ──→ T5 readiness dump  (gates 840 of the 844 not_ready rows)
T4 per-venue execution-instruction check ──→ T5 readiness dump  (real, but moves 0 rows on its own)
T2 instrument_type / data_type coverage axes ──→ T5 coverage dump at finer grain
```

**T1 is upstream of everyone and is the smallest spine (11 docs).** Start it first; its contract extensions cost
nothing unconsumed but stall two agents if missing.

> ### ⚠️ CORRECTED 2026-08-20 (T5, measured) — the highest-leverage item is T3, not T4
>
> This section previously read: _"T4's instruction-path check is the highest-leverage single item in the whole
> effort — it is the structural reason every readiness row currently reads `unverified`."_ **Both halves are wrong,
> measured against a live full-fleet dump** (288 venues × 3 modes = 864 rows, `coverage.json` date 2026-08-19,
> grain `instrument_type`).
>
> 1. **The rows do not read `unverified` — they read `not_ready`** (0 ready / 844 not_ready / 20 unverified, which
>    matches the artefacts' quoted headline exactly).
> 2. **The dominant failing leg is `strategy`, at 840 `not_ready`** — `position_read_mode_availability(venue).<mode>
>    = none`, which lives in **strategy-service (T3)**. `execution_instruction` is `unverified` on all 864 rows, but
>    the rollup lets any `not_ready` dominate, so **closing the instruction leg entirely would move zero rows off
>    `not_ready`.**
>
> Per-leg counts from that run:
>
> | leg | ready | not_ready | unverified |
> | --- | ---: | ---: | ---: |
> | `strategy` | 24 | **840** | 0 |
> | `execution_transfers` | 0 | 768 | 96 |
> | `market_tick_data` | 109 | 470 | 285 |
> | `execution_instruction` | 0 | 0 | 864 |
>
> T4's instruction-path check is still genuinely needed (T5 has filed the request with the groundwork done) — it
> just is not what unblocks the headline number. **Re-point the effort at strategy position-adapter coverage.**
> Evidence: `/plans/active/code_readiness_t5_readiness_observability_presentations_2026_08_19.md` Progress Log,
> 2026-08-20.
>
> Caveat on the same run: the execution-service capability probe exited 1 (no project ID), so all four
> execution-service legs reported `unverified=864`. The same probe succeeds single-venue, so those counts are a
> FLOOR, not a capability measurement. Tracked as a T5 P1.

## Exclusions — standing, all tranches

- **No backfill runs, no manifest migrations, no corpus sweeps, no GCS deletes.** Fixing the manifest-writer,
  path-registry and capture-status **code** is in scope; launching the data movement is not. 46 docs are flagged
  `excluded_data_movement` in the allocation JSON.
- **No credential or API-key requests.** Build the full code path, mark `BLOCKED-CREDENTIALS`, never descope.
- **Never edit a repo your tranche does not own.** Use the `## Inbound requests` section of the owning tranche's
  plan instead.

## Launch prompts — one per agent

Each agent runs in its OWN slot (`.tabs/N`) so the per-slot-worktree model holds — separate `.git`, no index
contention, correct commit attribution. **Do not run two of these in one slot.** Replace `<N>` with the slot number.

```text
Read /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/<N>/CLAUDE.md and then
/Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/<N>/unified-trading-pm/plans/active/code_readiness_<PLAN>.md
in full — that plan is your work order and your handoff document.

You are one of five agents running in parallel on disjoint repos. Edit ONLY the repos your plan says you own.
Work the spine docs first in priority order, then the tail, until every todo is [x] or carries an explicit
BLOCKED-OPERATOR / BLOCKED-CREDENTIALS tag with a stated reason.

Standing rules: do not run backfills, manifest migrations or GCS deletes (code fixes only). Do not request API
keys — build the path and mark BLOCKED-CREDENTIALS. Commit, push and flip the checkbox in the SAME turn with
<repo>@<sha> evidence. Ship code only via quickmerge --agent from a quality-gates.sh-green tree; doc-only edits via
scripts/dev/safe-doc-push.sh. Append to the Progress Log at every shippable unit — if your context ends, that log
is what the next agent resumes from.

You may spawn sub-agents. Paste unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md at the top of every
sub-agent prompt and set model= explicitly; if that injection fails the sub-agent must not proceed.

/autonomous
```

Substitute per agent:

| Agent | `<PLAN>` |
| --- | --- |
| 1 | `t1_contracts_library_externalapi_2026_08_19` |
| 2 | `t2_refdata_marketdata_2026_08_19` |
| 3 | `t3_features_ml_strategy_2026_08_19` |
| 4 | `t4_execution_settlement_2026_08_19` |
| 5 | `t5_readiness_observability_presentations_2026_08_19` |

## Todos

- [ ] [OPERATOR] P0. Launch agent 1 (T1 — contracts) in its own slot. Start this one first; four blocking edges
      terminate here.
- [ ] [OPERATOR] P0. Launch agent 4 (T4 — execution) in its own slot. Its per-venue instruction-path check unblocks
      844 of the 864 readiness rows.
- [ ] [OPERATOR] P0. Launch agent 2 (T2 — reference and market data) in its own slot.
- [ ] [OPERATOR] P0. Launch agent 3 (T3 — features, ML, strategy) in its own slot.
- [ ] [OPERATOR] P0. Launch agent 5 (T5 — readiness and artefacts) in its own slot.
- [ ] [AGENT] P1. Re-run `scripts/plan-hygiene/allocate_code_readiness_tranches.py` weekly so newly-authored docs
      are allocated rather than orphaned. New docs land in a tranche automatically; docs that scored wrong get an
      entry in the script's hand-verified `OVERRIDES` table.
- [ ] [AGENT] P1. Track the four artefacts' marker counts against the table above as the shrinking metric for the
      whole effort. Falling counts are the only honest progress signal — todo checkboxes are a proxy.
- [ ] [OPERATOR] P1. **Resolve the `assigned_vm: NA` corpus ratchet breach.** Measured 2026-08-19:
      494 NA docs / 1,851 NA open todos against a baseline+buffer of 479 / 1,664 —
      `check_na_corpus_ratchet.py` fails the hygiene sweep. **The breach was already there before this effort**
      (+9 docs / +14 todos pre-existing); these six coordinator/tranche docs take it to +15 / +187. Two honest
      exits — shrink the NA tail via `/na-eligibility-audit`, or make a reviewed decision to
      `--update-baseline` for this sanctioned push. Do NOT silently re-baseline; the ratchet exists to stop
      exactly that.
- [ ] [AGENT] P2. When all five tranche plans reach zero open todos, archive them together with this coordinator per
      the 6-step ritual. SSOT: `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

## Progress Log

> Append-only. Each tranche keeps its own log; this one records cross-tranche events only — a dependency landing, a
> tranche completing, a re-allocation.

- 2026-08-19 — Coordinator and five tranche plans authored. Allocation derived over the 892-doc active corpus
  (2,604 open todos, 94 spine). No agent launched yet, no code work started.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
