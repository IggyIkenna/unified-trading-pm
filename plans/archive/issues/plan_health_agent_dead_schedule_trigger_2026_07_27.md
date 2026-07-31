---
doc_type: issue
title:
  plan-health-agent.yml's daily 02:00 UTC schedule trigger has fired exactly once since March — effectively dead despite
  a correctly-configured cron
summary:
  The workflow's schedule trigger (0 2 * * *) is syntactically correct and lives on the default branch (main), yet gh
  run list shows only 1 schedule-triggered run out of the last 200 (2026-07-26 03:02 UTC) against ~140+ days since the
  file was added 2026-03-07. A sibling daily cron (readiness-verifier.yml) fires reliably (~83%, matching the documented
  GHA schedule throttle) with the same schedule-trigger shape, so this is not the known throttle — something specific to
  this workflow is suppressing it. RESOLVED as moot — the schedule trigger itself was deliberately dropped from the
  workflow the very next day (RULE-11 prove-then-retire, unrelated to this investigation), superseded by the
  plan-reconciler.timer systemd job, independently confirmed alive and firing.
status: resolved
nature: issue
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, github-actions, schedule, cron, plan-health, daily]
related: []
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.5
assigned_role: NA
drift_direction: advance-code
depends_on: []
resolved_by: slot 8 (cicd→backend_engineer craft, task ci_satellite_ao_dispatch_batch2-010), 2026-07-31
locked_by:
supersedes:
superseded_by:
source:
  Dispatched as one of five parallel audit agents this session verifying whether /plan-reconcile and /ag-closeout-audit
  (the "orphan consolidated plan checking" skill) actually run daily via AO, per an operator-raised question ("not sure
  that scheduler is tested... theres 2 more daily tasks to check").
---

> **ARCHIVED (2026-07-31) — complete.** Both todos resolved as moot: the `schedule:` trigger under investigation was
> removed by an unrelated 2026-07-28 decision (`unified-trading-pm@481e72d6f`, RULE-11 prove-then-retire) before
> root-causing completed; its daily-hygiene function is fully superseded by `plan-reconciler.timer` (systemd,
> independently verified alive and firing). See `## Resolution — 2026-07-31` below.

# plan-health-agent.yml's dead schedule trigger — 2026-07-27

## What I found

The operator's underlying question (are `/plan-reconcile` and `/ag-closeout-audit` actually scheduled daily) resolved
cleanly for both: `plan-reconciler.timer` (systemd on the orchestrator VM, 01:00 UTC, confirmed real firing 2026-07-24)
and `ag-closeout-audit`'s own timer (05:00 UTC, deliberately staggered — the operator's "supposed to run at 1am"
assumption was wrong for this one specifically, it was designed for 05:00). The "2 more daily tasks" resolved to
`docs-reconciler.timer` (03:00 UTC, confirmed real firing) and `plan-health-agent.yml` (GitHub Actions,
`cron: "0 2 * * *"`) — the second of which turned out to be broken.

`.github/workflows/plan-health-agent.yml`'s `on:` block (`schedule: - cron: "0 2 * * *"`, `workflow_dispatch:`,
`pull_request: branches: [main]`) is syntactically correct and present identically on `main` (confirmed the default
branch via `gh repo view --json defaultBranchRef`) — satisfying the "a scheduled workflow fires only from the default
branch" requirement. Yet:

```
gh run list --workflow plan-health-agent.yml --limit 200 --json event
  -> 199 pull_request, 1 schedule
```

The one schedule-triggered run: `2026-07-26T03:02:26Z` (note: 1h2m after its own `02:00` cron target — GH Actions
best-effort scheduling delay, not itself unusual). The file was added `2026-03-07` per
`git log --follow --diff-filter=A` — so across ~140+ days this cron should have had ~140 opportunities to fire and had
exactly 1.

For comparison, `readiness-verifier.yml` (also `schedule:` + `workflow_dispatch:`, no `pull_request:` trigger) shows
`{schedule: 25, workflow_dispatch: 5}` out of its last 30 runs — a ~83% fire rate matching the documented GHA schedule
throttle (`/codex/04-architecture/ci-alerting.md`: hourly crons land ~90%). 1/200 is not that throttle — it's something
specific to this workflow.

**Not yet root-caused. UPDATE 2026-07-27 ~02:45 UTC** — two candidates now RULED OUT:

- **Workflow-disabled state**: `gh api repos/.../actions/workflows/242855945` reports `"state": "active"` — not manually
  disabled, not auto-disabled for inactivity.
- **Recently-added trigger**: `git log --follow -p` across the file's whole history shows the `schedule: - cron: "0 2
  - - *"`line present, unchanged, since the file's original commit (alongside an ORIGINAL`push: branches: [main], paths:
      [plans/active/**]`trigger that was later replaced by the current`pull_request: branches: [main]` — the schedule
      block itself was never touched). This has had ~140 real days to fire, not a handful.

Still not ruled in/out (need either a live observation at the NEXT 02:00 UTC fire, or GitHub support/status-page
escalation — neither completed this session):

- The `pull_request: branches: [main]` trigger — this workflow gets extremely high `pull_request` volume (dozens of
  runs/hour, matching this repo's commit velocity) that every OTHER workflow with a bare `schedule:` trigger doesn't
  share. Worth checking whether GitHub's scheduler deprioritizes/drops a scheduled run for a workflow it considers
  "already busy" — not a documented GH behavior, but worth testing empirically rather than assuming.
- ~~The workflow's own `concurrency:` group colliding with pull_request runs~~ — **RULED OUT**: sampled
  `pull_request`-event run `head_branch` values (`ci/clear-quarantine-recovery-2026-06-16`, `cicd-hardening-to-main`,
  `cicd/failopen-sit-gate-uncovered-repos`, ...) are all distinct feature/PR branches, never `main` itself — their
  concurrency-group ref genuinely differs from the schedule event's `refs/heads/main`, so no collision/cancellation is
  possible between them.
- The workflow file's own `updated_at` (`2026-06-08T21:10:50+01:00`, per the Actions API) shows no edits since ~49 days
  before this check — the trigger definition has been completely stable for that whole window, so this isn't an artifact
  of a recent change either.
- **Next concrete step**: the next scheduled fire is ~2026-07-28 02:00 UTC. Check
  `gh run list --workflow plan-health-agent.yml --limit 5 --json event,createdAt,conclusion` shortly after that time —
  either it fires (data point 2/~141, still worth explaining but less urgent) or it doesn't (stronger signal to escalate
  to GitHub support with the two ruled-out candidates above as context).

## Why it matters

`plan-health-agent.yml` is a plan-hygiene + contradiction-detection sweep — the kind of thing that's supposed to catch
corpus drift before it compounds. A schedule trigger that looks configured but essentially never fires is worse than an
honestly-absent one: nobody notices the gap because the workflow file itself looks correct.

## Resolution — 2026-07-31

**Moot, not root-caused-and-fixed.** The `schedule:` trigger this issue investigates was deliberately **removed
entirely** from `.github/workflows/plan-health-agent.yml` (and its workflow-templates twin) the very next day after this
doc was filed — `unified-trading-pm@481e72d6f` (2026-07-28 09:44 UTC), commit message: "RULE-11 prove-then-retire
executed: dropped the schedule: trigger + Haiku plan-health/notify job pair from
.github/workflows/plan-health-agent.yml + its template twin, keeping only the pull_request-triggered plan-health-gate
hard gate... superseded by the daily deep plan-reconciler agent (opus, effort max) on a systemd timer on the central
orchestrator VM." This was an **independent, unrelated decision** (RULE-11 prove-then-retire, tracked in
`plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md`, archived) — not a response to this investigation — that
happened to remove the exact trigger under study.

Verified 2026-07-31 (re-confirmed live, not just reading the commit):

- Current `.github/workflows/plan-health-agent.yml` `on:` block is `pull_request: branches: [main]` only — no
  `schedule:`, no `workflow_dispatch:`. Confirmed no `template/plan-health*` twin still carries a `schedule:` block
  either (`grep -rn "schedule.*cron" scripts/workflow-templates/` → 0 hits for this workflow).
- The replacement daily mechanism (`plan-reconciler.timer`, systemd, central orchestrator VM) is loaded, enabled, and
  actively firing: `systemctl status plan-reconciler.timer` shows `Active: active (waiting)`, last triggered 2026-07-31
  08:00:15 UTC. `journalctl -u plan-reconciler.service` over the prior 12h shows a genuine successful dispatch
  (`2026-07-31T00:01:38Z`, `{"ok":true,"dispatch_id":"agt-151fd0",...}|HTTP:200`) plus the hourly retry-until-capacity
  design correctly no-op'ing once dispatched (`"already dispatched successfully today"`) and correctly retrying past a
  couple of transient connect-timeout failures (`07:00:48Z` failed → `08:00:15Z` succeeded as a no-op, meaning the
  underlying dispatch from `00:01:38Z` was still valid) — this is a materially more reliable daily-hygiene mechanism
  than the 0.5%-firing GHA `schedule:` trigger this issue originally flagged.

The original root-cause question (was it `pull_request`-volume deprioritization, a GH scheduler bug, something else?) is
now **unanswerable and irrelevant** — there is nothing left to observe (the trigger no longer exists) and nothing left
to fix (its function was already replaced by a mechanism proven to work). No GitHub-support escalation is warranted for
a trigger that was intentionally retired.

## Todos

- [x] ✅ **Root-cause why the schedule trigger essentially never fires.** Resolved as MOOT, not diagnosed — see
      Resolution above: the trigger was removed by an unrelated 2026-07-28 decision one day after this doc was filed,
      before root-causing completed. No further diagnosis is possible or useful.
- [x] ✅ **Fix it.** No fix needed/applicable — the trigger's daily-hygiene function was already fully superseded by
      `plan-reconciler.timer`, independently verified alive and firing (see Resolution above). Nothing to ship.

## Codex SSOTs

- `/codex/04-architecture/ci-alerting.md` — documented GHA `schedule:` throttle baseline (~80-90%, re-measured
  2026-07-21) that this workflow's 0.5% rate is clearly NOT an instance of.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): **KEEP-NA-STALE (already-duplicated)** — both open todos
are extracted verbatim into `/plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md` todo 13 (combined (a)
root-cause + (b) fix, carrying this doc's already-ruled-out candidates and its 48-hour schedule-fired verification, and
citing this doc as Source). Citation recorded; `assigned_vm` deliberately NOT flipped — that would dispatch a duplicate.
