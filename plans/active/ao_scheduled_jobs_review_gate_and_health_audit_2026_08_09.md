---
doc_type: plan
title: AO scheduled-jobs review-gate backlog drain + cross-job sharding/health audit
summary:
  Two tracks. (A) Drain the 25 remaining plan_reconciler review-branch PRs stuck open since 2026-08-02 (0 merged, 0
  reviewed) after graduating plan_reconciler to steady-state direct-push — each needs real per-PR judgment (rebase +
  re-verify vs. close as superseded), not a blind force-merge. (B) Audit the other 7 AO scheduled-jobs (ag-closeout-
  auditor, cefi-mtds-smoke, cefi-reconciliation, context-scout, docs-reconcile, escalation-queue-reconciler,
  na-eligibility-auditor) for the same failure-class plan_reconciler just had — corpus-wide unsharded runs vs. bounded
  shards, measured time-to-complete, whether it still routes through a review-branch/PR gate (silently starving its own
  escalation mechanism the same way), and whether an [OPERATOR]-tagged escalation actually reaches a resolved, archived
  state or quietly stalls.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [ao, scheduled-jobs, plan_reconciler, review-gate, escalation, sharding, audit, plan-hygiene]
related:
  [
    /plans/active/issues/plan_reconciler_findings_2026_08_08.md,
    /plans/active/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  "interactive session, 2026-08-09 — follow-up from the plan_reconciler steady-state graduation + PR-backlog discovery"
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
    agents/plan_reconciler.md,
    agent-orchestrator/server/regen_backlog_from_plan.py,
    agent-orchestrator/scripts/scheduled_job_already_ran.py,
    /plans/active/issues/plan_reconciler_findings_2026_08_08.md,
    /plans/active/issues/ao_scheduled_job_reserve_and_staggering_2026_08_04.md,
  ]
---

# AO scheduled-jobs review-gate backlog drain + cross-job sharding/health audit

## Background

An interactive session on 2026-08-09 traced why no `plan_reconciler_findings_<tranche>_<date>.md` docs were visible in
`plans/active/issues/` despite the systemd timer clearly firing (28 `plan_reconciler/agt-*` review-branch PRs existed on
GitHub). Root cause: `agents/plan_reconciler.md` put every run through a "PROVING PHASE" review-branch + PR gate into
`live-defi-rollout` (added 2026-06-17 after an early version died before pushing) with an explicit graduation criterion
— "≥2 clean proven runs, operator-enabled" — that nobody ever pulled the trigger on. 28+ consecutive runs
(2026-08-02→08-09) each completed cleanly end-to-end with zero mid-flight deaths, but every one sat in an unreviewed,
unmerged PR. Worse: `regen_backlog_from_plan.py` only ever snapshots `origin/live-defi-rollout` (never a local checkout,
never an open PR branch) — so any `[OPERATOR]`-tagged todo filed inside one of those findings docs could NEVER surface
as a `BLK-op-*` dashboard row, never get asked, never resolve. Not a missing hookup — a starved one.

Fixed same session: `plan_reconciler` graduated to steady state (direct push, no review branch/PR —
`unified-trading-pm@9df4d0b69f`). 3 of the 28 stuck PRs merged cleanly (#2396, #2400, #2421 — each touched only its own
findings doc). The other 25 have real conflicts from up to a week of corpus drift and need actual per-PR judgment, not a
blind force-merge — that's Track A below. Given this exact failure class (unsharded-run reliability +
review-gate-starves-escalation) could easily exist in AO's other 7 scheduled jobs and nobody has checked, Track B audits
each one.

## Track A — drain the 25 stuck plan_reconciler PRs

For each: `gh pr checkout <n>`, `git fetch origin live-defi-rollout && git rebase origin/live-defi-rollout`, resolve
conflicts by re-reading both sides (the PR's finding vs. whatever landed on `live-defi-rollout` since) — if the PR's
content is stale/superseded by later work, close it and delete the branch (zero blast radius, per the agent's own PR
description); if still valid, re-verify the finding against current corpus state before pushing the rebase and merging.
Done-when for each: PR is either MERGED (content re-verified correct post-rebase) or CLOSED (with a one-line reason —
superseded / stale / duplicate).

- [ ] [REVIEW] P1. Triage PR #1998 (`plan_reconciler/workflow-undefined`, opened 2026-08-02, 54 files changed) —
      **anomalous, needs extra scrutiny before anything else in this track**: the branch name itself shows a `$TRANCHE`
      substitution bug (literal "undefined"), and its file scope is far wider than any other run in this batch (every
      other PR touches only its own findings doc or a small cluster). Read the PR diff in full before deciding whether
      to rebase or close — do not treat it as routine.
- [ ] [REVIEW] P2. Triage PR #2327 (`plan_reconciler/agt-4fdce1`, opened 2026-08-06).
- [ ] [REVIEW] P2. Triage PR #2395 (`plan_reconciler/agt-d4d31f`, opened 2026-08-06).
- [ ] [REVIEW] P2. Triage PR #2397 (`plan_reconciler/agt-24f4b0`, opened 2026-08-06).
- [ ] [REVIEW] P2. Triage PR #2398 (`plan_reconciler/agt-bf8439`, opened 2026-08-06).
- [ ] [REVIEW] P2. Triage PR #2399 (`plan_reconciler/agt-65e60a`, opened 2026-08-06).
- [ ] [REVIEW] P2. Triage PR #2401 (`plan_reconciler/agt-903867`, opened 2026-08-06).
- [ ] [REVIEW] P2. Triage PR #2402 (`plan_reconciler/agt-6c6359`, opened 2026-08-06).
- [ ] [REVIEW] P2. Triage PR #2413 (`plan_reconciler/agt-ec6642`, opened 2026-08-07).
- [ ] [REVIEW] P2. Triage PR #2415 (`plan_reconciler/agt-a2268a`, opened 2026-08-07).
- [ ] [REVIEW] P2. Triage PR #2416 (`plan_reconciler/agt-cf1afa`, opened 2026-08-07).
- [ ] [REVIEW] P2. Triage PR #2418 (`plan_reconciler/agt-c6e8c7`, opened 2026-08-07).
- [ ] [REVIEW] P2. Triage PR #2419 (`plan_reconciler/agt-e7f024`, opened 2026-08-07).
- [ ] [REVIEW] P2. Triage PR #2420 (`plan_reconciler/agt-985cf1`, opened 2026-08-07).
- [ ] [REVIEW] P2. Triage PR #2423 (`plan_reconciler/agt-6eb8c5`, opened 2026-08-07).
- [ ] [REVIEW] P2. Triage PR #2522 (`plan_reconciler/agt-2add8d`, opened 2026-08-08 — whole-corpus `all` run; note its
      findings doc content is already independently merged onto `live-defi-rollout` via a different path, so this PR is
      very likely pure duplicate — verify and close if so, don't re-merge the same content twice).
- [ ] [REVIEW] P2. Triage PR #2630 (`plan_reconciler/agt-8af81b`, opened 2026-08-09).
- [ ] [REVIEW] P2. Triage PR #2631 (`plan_reconciler/agt-1a9b86`, opened 2026-08-09).
- [ ] [REVIEW] P2. Triage PR #2644 (`plan_reconciler/agt-2d9a32`, opened 2026-08-09).
- [ ] [REVIEW] P2. Triage PR #2645 (`plan_reconciler/agt-c3a27f`, opened 2026-08-09).
- [ ] [REVIEW] P2. Triage PR #2647 (`plan_reconciler/agt-fe4564`, opened 2026-08-09).
- [ ] [REVIEW] P2. Triage PR #2649 (`plan_reconciler/agt-c80749`, opened 2026-08-09).
- [ ] [REVIEW] P2. Triage PR #2650 (`plan_reconciler/agt-733350`, opened 2026-08-09).
- [ ] [REVIEW] P2. Triage PR #2652 (`plan_reconciler/agt-a3e83c`, opened 2026-08-09).
- [ ] [REVIEW] P2. Triage PR #2653 (`plan_reconciler/agt-a398c9`, opened 2026-08-09).
- [ ] [REVIEW] P2. Once all 25 above are resolved (merged or closed), re-run
      `gh pr list --state open --search "head:plan_reconciler"` and confirm zero remain (except any opened fresh by a
      new run in the interim, which is expected/fine now that steady state pushes directly and shouldn't itself open
      PRs) — record the final count in this plan's Progress Log.

## Track B — audit the other 7 scheduled jobs for the same failure class

Per job: (1) read its `install-<job>-timer.sh` — is it sharded or does it run its full corpus unsharded on every fire;
(2) find its most recent 3-5 run-findings/report docs (or dashboard scheduled-jobs history if reachable) and note actual
measured wall-clock + any `reaped-stale`/`timeout`/`error` outcomes; (3) grep its own agent/skill boot prompt for a
review-branch + PR pattern like the one just fixed — if present, is there a clean graduation path defined, and has
anyone checked whether it's actually still gated; (4) if the job files `[OPERATOR]`-tagged or `BLOCKED-*` findings, pick
2-3 recent examples and trace whether they actually reached a `BLK-op-*` dashboard row and got resolved, or whether
they're sitting the same way plan_reconciler's were. Where a dedicated skill already exists for the job (several do),
run it or read its most recent output rather than re-deriving from scratch — this track is about the JOB'S OWN
reliability/escalation shape, not re-running its normal audit content.

- [ ] [REVIEW] P2. Audit `ag-closeout-auditor` (`install-ag-closeout-auditor-timer.sh`, `/ag-closeout-audit` skill) —
      sharding shape, measured run time, review-gate check, escalation-resolution trace. Record findings inline below.
- [ ] [REVIEW] P2. Audit `cefi-mtds-smoke` (`install-cefi-mtds-smoke-timer.sh`) — same 4 checks.
- [ ] [REVIEW] P2. Audit `cefi-reconciliation` (`install-cefi-reconciliation-timer.sh`) — same 4 checks.
- [ ] [REVIEW] P2. Audit `context-scout` (`install-context-scout-timer.sh`, `/context-scout` skill) — same 4 checks;
      this one is read-mostly (populates `context_scope`) so the review-gate question may not apply — confirm either way
      rather than assuming.
- [ ] [REVIEW] P2. Audit `docs-reconcile` (`install-docs-reconcile-timer.sh`, `/docs-reconcile` skill) — same 4 checks.
- [ ] [REVIEW] P2. Audit `escalation-queue-reconciler` (`install-escalation-queue-reconciler-timer.sh`,
      `/escalation-queue-reconcile` skill) — same 4 checks; note this job watches OTHER jobs' escalation health, so also
      check whether IT would have caught the plan_reconciler PR-backlog problem itself, and if not, why not (is there a
      gap in what it watches worth folding into that skill separately).
- [ ] [REVIEW] P2. Audit `na-eligibility-auditor` (`install-na-eligibility-auditor-timer.sh`, `/na-eligibility-audit`
      skill) — same 4 checks.
- [ ] [REVIEW] P1. Synthesize Track B's 7 audits into a single findings doc under `plans/active/issues/` (slug
      `ao_scheduled_jobs_health_audit_findings_<date>`) — one row per job: sharded y/n, typical run time, review-gate
      present y/n (+ stuck backlog count if yes), escalation-resolution health. File a `- [ ]` follow-up todo (here or
      in a new plan, operator's call per the ask-before-creating-AO-plan rule) for any job found with the SAME
      review-gate-starving-escalation bug plan_reconciler had — do not silently fix it inline without the same evidence
      bar (≥2 clean proven runs) this plan's Background section used.

## Progress Log

- **2026-08-09 (interactive session)**: plan authored following the operator's explicit "human plan" ruling on this
  exact scope. Track A's 25-PR list and Track B's 7-job list both pulled live from `gh pr list` / the installer-script
  directory listing this same session, immediately before authoring.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — first audit pass on this doc.
  Its own `source:` frontmatter and body state it was authored "following the operator's explicit 'human plan' ruling on
  this exact scope" — a citable dated ruling on citation alone. Independently, every open todo is genuine per-item human
  judgment (Track A: rebase-and-re-verify vs. close-as-superseded per PR, 25 individual calls; Track B: a 7-job
  reliability/escalation-health audit), not mechanical/bounded work.

- **context-scout 2026-08-15**: populated/refreshed context_scope (6 entries) — trimmed from 17 to the shared root-cause
  files (`plan_reconciler.md`, `regen_backlog_from_plan.py`, `scheduled_job_already_ran.py`), the scheduled-jobs codex
  SSOT, and the 2 related issue docs already in `related:`; dropped the 7 individual `install-<job>-timer.sh` scripts
  (each already named inline in its own Track B todo) plus the plan-reconcile skill doc, `operator_gated_options.py`,
  and the single-vm-architecture codex ref.
