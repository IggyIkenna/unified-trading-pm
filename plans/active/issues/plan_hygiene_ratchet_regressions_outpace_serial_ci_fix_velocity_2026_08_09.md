---
doc_type: issue
title:
  plan-hygiene hard-0-baseline ratchet checks regress faster than one CI worker can chase serially on live-defi-rollout
summary: >-
  A worker chasing a `quality-gates-v2` failure on `unified-trading-pm` `live-defi-rollout` hit 4 CONSECUTIVE
  regressions in a row across different ratchet checks (codex-doc-freshness — already fixed upstream this session;
  effort-ratchet; archive-candidates x2; dangling-reference-paths, 95 > baseline 86) despite pushing 3 separate fixes.
  Each re-trigger landed on a fresh HEAD carrying a NEW regression introduced by other agents committing concurrently in
  the gap between the fix push and the CI re-run — the branch's commit velocity currently outpaces what one CI worker
  fixing issues one at a time can converge on. Worker correctly declined to keep chasing a 5th time (own recommendation:
  hand off) rather than burning further CI cycles on a race it cannot win serially; main answered "hand off" and is
  filing this as the systemic finding rather than asking for more chase attempts.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ci, quality-gates-v2, ratchet, plan-hygiene, concurrency, live-incident]
related:
  - /plans/active/issues/quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md
created: 2026-08-09
author: agt-22de53 (main), relaying a finding from agt-558c62 (slot 3)
parent_epic: infrastructure_master
priority: P2
source: >-
  Worker (agt-558c62, slot 3) blocked-nudge BLK-bcb0be57, 2026-08-09T02:24:36Z — 4 consecutive quality-gates-v2
  regressions on live-defi-rollout across different plan-hygiene ratchet checks, each re-trigger racing fresh concurrent
  commits from other fleet agents.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-09
locked_since:
context_scope: [unified-trading-pm/scripts/plan-hygiene/, unified-trading-pm/.github/workflows/quality-gates-v2.yml]
---

# plan-hygiene ratchet checks regress faster than serial CI-fix chasing can converge on a high-churn branch

## What was found

`agt-558c62` (slot 3) was chasing a `quality-gates-v2` failure on `unified-trading-pm` `live-defi-rollout` and hit 4
consecutive distinct regressions in a row, each on a fresh `HEAD`:

1. `codex-doc-freshness` — already independently root-caused and re-baselined this session
   (`plans/active/issues/codex_doc_freshness_regression_ambient_staleness_drift_2026_08_09.md`), an ambient time-decay
   ratchet, not this worker's fault.
2. `effort-ratchet`
3. `archive-candidates` (x2 — regressed twice)
4. `dangling-reference-paths` — 95 violations > baseline 86, current at time of report

Each time the worker pushed a fix and re-triggered, a DIFFERENT concurrent agent's commit had already landed a new
violation in the gap, so the re-run failed on a NEW check rather than confirming the original fix. Worker correctly
recognized this as a race it cannot win by chasing serially and declined a 5th attempt, recommending hand-off (own
words: "this branch is churning faster than one CI worker can chase serially").

## Why it matters

- Real CI-cycle waste: 4+ full `quality-gates-v2` runs consumed chasing a moving target, none of which converged.
- The hard-0-baseline ratchet design (shrink-only, any regression blocks) assumes a LOW commit-concurrency environment
  where one fix-and-verify cycle can outrun new violations landing. At current fleet-wide commit velocity on
  `live-defi-rollout`, that assumption may no longer hold for at least some of these checks.
- Distinct from `quality_gates_v2_concurrency_and_bookkeeping_job_cost_2026_08_02.md` (that doc is about
  concurrency-group cancellation and per-job billing floor cost) — this is about ratchet CORRECTNESS-vs-commit-race, a
  different failure mode.

## Todos

- [ ] [BACKEND] P2. Consider one or more structural fixes so ratchet regressions don't outrace serial fixing on a
      high-churn branch: (a) debounce/coalesce the CI re-trigger (e.g. the hourly `ldr-ci-monitor`) so a fix push
      doesn't immediately race a fresh concurrent regression; (b) batch multiple ratchet-fix commits into a single CI
      pass instead of one escalation-and-fix cycle per individual regression; (c) evaluate whether any of the four
      ratchet checks that regressed here (codex-doc-freshness, effort-ratchet, archive-candidates,
      dangling-reference-paths) should move from hard-fail to a periodic/batched sweep instead of per-commit
      enforcement, given they're corpus-wide ambient-drift-prone rather than tied to the committing agent's own diff.
      Repo: unified-trading-pm (`.github/workflows/`, `scripts/quality_gates/`).
- [ ] [REVIEW] P3. Once a structural fix lands, verify by watching the next 2-3 `quality-gates-v2` runs on
      `live-defi-rollout` for whether ratchet regressions still chain the way they did here.

## Progress log

- 2026-08-09 (main agt-22de53): Filed after answering BLK-bcb0be57 "B" (hand off) — worker had already tried 3
  fix-and-retrigger cycles across 4 different regressions with zero convergence. Not attempting a structural fix myself
  this tick; filing for a dedicated pass since the right answer (debounce vs. batch vs. move-to-periodic) needs design
  judgment, not a one-line change.
