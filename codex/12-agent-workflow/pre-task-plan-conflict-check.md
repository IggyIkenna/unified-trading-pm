---
doc_type: codex-ssot
title: Pre-Task Plan/Issue Conflict Check
summary:
  SSOT for the point-in-time rule that every task START (not just the periodic corpus sweeps) must grep `plans/active/`
  + `plans/active/issues/` for existing/prior coverage before implementing, so work doesn't regress or duplicate
  something already done or superseded; explains why `/plan-reconcile` and the other daily/on-demand sweeps don't close
  this gap by themselves, and gives the concrete grep + verify procedure.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, orchestrator, frontmatter, regression-prevention]
related:
  [/codex/12-agent-workflow/plan-hygiene.md, /codex/12-agent-workflow/canonical-plan-flow.md, plans/PLAN_FORMAT.md]
created: 2026-07-28
authoritative_for: [pre-task plan/issue conflict-check procedure]
referenced_by: [CLAUDE.md § "Agent behavior"]
owner:
last_reviewed:
code_refs:
---

# Pre-Task Plan/Issue Conflict Check

> Operator ruling 2026-07-28 (Ikenna): "any task started must be checked against existing plans and issues such that we
> ensure our implementation is not a regression to previously done work — as some plans are older and may be superseded,
> even with `/plan-reconcile` and the other skills running daily."

## The gap this closes

`/plan-reconcile`, `/ag-closeout-audit`, `/na-eligibility-audit`, and `/plan-vintage-audit` all audit the plans/issues
corpus **on a cadence** — daily or on-demand sweeps. None of them run **at the moment a new task starts**. A plan can be
superseded, folded into another plan, or already fully implemented in the window between sweeps, or simply because the
sweep that would have caught it hasn't run yet today. Starting work without checking risks rebuilding, or regressing,
work that is already done — the sweeps converge the corpus over time; they don't protect the next hour.

## The rule

Before starting ANY task — writing a new plan, picking up an existing plan's todo, or doing ad hoc work — grep the
corpus for existing coverage FIRST:

```
rg -li '<topic keywords>' plans/active/ plans/active/issues/
rg -l '^asset_group:.*<asset_group>' plans/active/ | xargs grep -l '<topic keyword>'
```

- **0 hits ≠ clear.** Same grep-then-READ discipline as codex retrieval (`CLAUDE.md` § "Agent behavior") — a miss can
  mean the work is covered under different terminology, not that it's uncovered. Genuinely uncertain → ask, don't assume
  clear.
- **A hit → read it, don't just note it exists.** Check:
  - `status`: `draft`/`active` (live) vs an archived/superseded doc a stale cross-reference still points at.
  - `supersedes` / `superseded_by`: follow the chain to the CURRENT doc — an older plan's content may already be folded
    into a newer one.
  - The actual checkbox/prose state, not just the frontmatter — a doc can be `status: active` with the specific piece of
    work already done and simply left unchecked (a hygiene gap the daily sweeps track separately, not proof the work is
    outstanding).
- **Found doc already covers it and is current** → don't duplicate: verify the work is actually done rather than
  re-implementing it, or add to that plan rather than forking a parallel one.
- **Found doc is stale/superseded** → don't build against it: follow the chain to what replaced it, or — if nothing has
  replaced it yet — flag it for the next `/plan-reconcile`/`/plan-vintage-audit` pass rather than building on a dead
  doc.
- **Ambiguous** (multiple candidates, partial overlap, unclear supersession) → ask the operator. This is exactly the
  ambiguity the periodic sweeps exist to resolve on their own cadence; you're being asked to resolve it NOW, before
  acting.

## Why this isn't redundant with the periodic sweeps

| Mechanism               | Cadence                    | Catches                                                                                                   |
| ----------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------- |
| `/plan-reconcile`       | daily + on-demand          | corpus-wide contradictions, stale checkmarks, drift                                                       |
| `/ag-closeout-audit`    | on-demand, per asset-group | orphaned docs no active/dispatched plan covers                                                            |
| `/na-eligibility-audit` | on-demand                  | NA-classified docs that should be reclassified or archived                                                |
| `/plan-vintage-audit`   | on-demand, per date-range  | old docs whose work is already done/superseded/migratable                                                 |
| **This rule**           | **every task, at start**   | **the specific conflict for the work about to start, in the window before the next sweep would catch it** |

None of the periodic sweeps substitute for this rule, and this rule doesn't substitute for them — the sweeps converge
the whole corpus over time; this rule stops a single task from doing damage in the meantime.
