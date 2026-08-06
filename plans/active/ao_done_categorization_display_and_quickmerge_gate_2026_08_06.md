---
doc_type: plan
title:
  AO Done-categorization display (Fleet + Backlog Detail) + missing-quickmerge /done gate + mtds dirty-worktree root
  cause
summary:
  Three related fixes, all discovered from one operator session on the AO dashboard's Done ✓/✗ split (commit 41035a5,
  agent-orchestrator) — surfacing it in Fleet + Backlog Detail (it currently only lives in the separate Activity rail
  panel), a new /done-time gate that catches a missing-quickmerge commit at the source instead of hours later at
  promotion-PR time, and the actual root cause behind 82% of live dirty-worktree done-rejections.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, market-tick-data-service]
scope: [engineer]
tags: [agent-orchestrator, dashboard, done-gate, quickmerge, provenance, dirty-worktree]
related:
  [
    /codex/05-infrastructure/agent-orchestrator-deploy.md,
    /codex/08-workflows/ci-cd-flow.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
created: "2026-08-06"
last_updated: "2026-08-06"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
context_scope:
  [
    agent-orchestrator/dashboard/src/layout.tsx,
    agent-orchestrator/dashboard/src/App.tsx,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/worktree_clean_check/_artifacts.py,
    agent-orchestrator/server/verify.py,
    unified-trading-pm/scripts/cicd/check_strict_quickmerge.py,
    unified-trading-pm/scripts/cicd/promotion_lag_monitor.py,
    market-tick-data-service/tests/market_interface/schema_validation/conftest.py,
  ]
supersedes:
superseded_by:
depends_on:
source:
  "operator ask 2026-08-06, interactive session slot 1 — pivoted from a dashboard-display question into a live
  root-cause dig after the operator flagged the sheer volume of repeated dirty-worktree /done rejections in a screenshot"
assigned_role: backend_engineer
drift_direction: advance-code
---

# AO Done-categorization display + missing-quickmerge /done gate + mtds root cause

## Why this doc exists

The operator asked why a previously-shipped feature — the Activity panel's Done ✓/✗ split (`agent-orchestrator@41035a5`)
— wasn't visible in the Fleet slot table or the Backlog Detail modal. Investigation confirmed the feature is genuinely
live in production (verified against the served JS bundle directly), it's simply scoped to a third, separate panel
neither of those two components share. Scoping the fix to show it in both places surfaced two adjacent, higher-value
findings worth fixing in the same pass:

1. Live activity data showed the dirty-worktree done-rejection category is dominated (82% of a 60-row sample) by one
   specific, fixable root cause, not general WIP-hygiene noise.
2. The operator's request to add a "didn't run quickmerge" done-failure reason led to discovering the detection +
   self-heal tooling for this already exists (`check_strict_quickmerge.py`, `reprovenance_bypass.sh`, the
   `quickmerge-provenance` promotion-PR gate) — the actual gap is that it only fires at push-time (bypassable via
   `--no-verify`) or promotion-PR time (hours later, disconnected from the worker who caused it), never at `/done` time
   where the responsible worker is still active to fix it immediately.

## Track A — mtds dirty-worktree root cause (fixes 82% of live dirty-worktree done-rejections)

`market-tick-data-service`'s `tests/market_interface/schema_validation/conftest.py::_write_health_artifact` rewrites
`tests/schema_artifacts/{binance,bybit,okx}_schema_health.json` on every test run ("for UAC CI artifact download"), but
the files are tracked in git, not gitignored — so any task that runs the mtds test suite ends up with a dirty repo at
`/done` time regardless of what it actually worked on. Confirmed live (SSM read of the last 60
`slot_done_rejected_dirty` activity rows: 49/60 are these exact 3 files) and locally (identical diff sitting in this
session's own mtds clone).

- [x] 1. ✅ [BACKEND] P0. In `market-tick-data-service`, stop tracking `tests/schema_artifacts/*.json` in git.
      Done-when: `git status --porcelain` after running the schema_validation test suite locally shows the 3 files as
      untracked-and-ignored, not modified. — **already shipped**: `market-tick-data-service@a8c590a0` ("chore(tests):
      stop tracking generated schema_health artifacts", same author identity, landed 2026-08-05 23:52 — ~8.5h before
      this session, via quickmerge). Not caught by this plan's pre-authoring grep (no plan/issue doc existed for it — it
      was a prior interactive one-off fix, invisible to a plans-corpus search). Discovered the hard way: my own
      redundant attempt at the identical fix collided with it during `quickmerge.sh`'s internal
      `git pull --rebase     --autostash` (delete/modify conflict on the same 3 paths, surfaced as a raw
      `error: could not write index ...     needs merge` that quickmerge's own error handling didn't structure-catch).
      Recovered clean: dropped my now-redundant `.gitignore` addition (confirmed `git diff --cached` was non-empty —
      mine used a narrower `*.json`-scoped pattern under a different section than HEAD's `tests/schema_artifacts/` —
      genuinely redundant, not a no-op, so explicitly discarded rather than assumed-safe), resolved the conflicted json
      files by finalizing HEAD's existing deletion (`git rm --cached -f`), and unstaged (not discarded) the unrelated
      Dockerfile/cloudbuild.yaml changes that `--autostash` swept in — pre-existing dirty WIP not touched by this
      session, restored to exactly its prior unstaged state. Verified post-recovery:
      `git diff     origin/live-defi-rollout -- tests/schema_artifacts/ .gitignore` is empty (working tree exactly
      matches the already-shipped fix); ran the full 20-test `schema_validation` suite locally, zero dirty diff
      afterward — the 82%-cause is confirmed gone.
- [x] 2. ✅ [BACKEND] P2. Investigated widening `GENERATED_ARTIFACT_ALLOWLIST`
      (`server/worktree_clean_check/_artifacts.py`) — determined NOT needed and not done. The module's own docstring
      states the established convention explicitly: "Belt-and-suspenders `git rm --cached` + .gitignore lives in the
      repos that emit these ... tracked here is the allowlist" — i.e. the allowlist is the backstop for emitting repos
      that HAVEN'T been source-fixed, not something to also populate once a repo has been. Todo 1 already source-fixes
      mtds (gitignored + untracked files never appear in `git status --porcelain` at all), so adding
      `tests/schema_artifacts/` here would be dead code exercising a path that can no longer trigger. No code changed
      for this todo — closing as a documented no-op rather than forcing unnecessary defensive work.

## Track B — new `/done`-time missing-quickmerge gate

Reuses `unified-trading-pm/scripts/cicd/check_strict_quickmerge.py`'s existing detection (don't reimplement the
carve-out logic — merge/reconcile commits, already-promoted commits, bot/`[skip ci]` authors, non-source-only commits
are all already correctly exempted there). Mirrors the shape of the existing `_enforce_done_clean_gate` in
`server/routes/slots_worker.py:1108` (structured 409, task stays `dispatched`, never a silent block).

- [x] 1. ✅ [BACKEND] P1. Added `_enforce_done_quickmerge_provenance_gate(slot_id, req, slot_worktree, verification)` in
      `server/routes/slots_worker.py`, called right after the M9 origin gate. Resolves the sibling PM worktree via the
      existing `verify._detect_sibling_pm_worktree` helper, shells out to
      `check_strict_quickmerge.py --range <sha>~1..HEAD --block` in the repo the task's `sha` resolves to (NOT
      `origin/live-defi-rollout..sha` as originally scoped — the gate's own test suite caught that this always produces
      an empty range, since by /done time the worker's own push has already advanced its local
      `origin/live-defi-rollout` tracking ref past the reported commit; `{sha}~1..HEAD` is immune to that and still lets
      a later `Reprovenance:` blessing commit forgive it). On a violation: logs `slot_done_rejected_no_quickmerge` and
      raises the same structured 409 shape as the sibling gates, naming the tip-vs-mid-history remedy.
      `done_require_quickmerge_provenance` defaults **False** (warn-only first rollout, mirroring
      `done_require_origin`'s own graduation precedent) — flip after a clean measurement period, same ratchet.
      Done-when: `tests/test_done_gate_quickmerge_provenance.py` (4 cases: tip-bypass warns by default, tip-bypass 409s
      when enabled + names the quickmerge remedy, mid-history bypass 409s + names the reprovenance_bypass.sh remedy, a
      properly Quickmerge-trailered commit is never flagged) — all green, plus the full existing done-gate test family
      (94 tests) still green. — agent-orchestrator@ef59837
- [x] 2. ✅ [BACKEND] P2. Registered `slot_done_rejected_no_quickmerge` in `DONE_FAILED_TYPES`
      (`dashboard/src/layout.tsx`) plus its tone/label/summary text, so it renders in the Activity "Done ✗" tab with its
      own label ("done failed · no quickmerge") and is picked up by Track C's Fleet badge + Backlog Detail done-failed
      tab automatically (no separate wiring needed there — both consume the same `DONE_FAILED_TYPES` set). Done-when:
      `activity.test.ts` case asserting the new type's label + summary text (both tip and mid-history remedy phrasing) —
      green, 42/42 tests pass. — agent-orchestrator@ef59837
- [ ] [REVIEW] P3. `_(stretch, optional)_` File a follow-up LOCAL todo (not built in this plan) for wiring
      `promotion_lag_monitor.py`'s existing `provenance_blocked` finding into an auto-filed AO backlog task (P0,
      `[BACKEND]`) instead of Slack-only — this plan intentionally does NOT auto-execute `reprovenance_bypass.sh` from
      an unattended monitor (it pushes a commit to a shared branch; keep a worker/operator in the loop), but a standing
      Slack-only alert for something this rare and high-impact is easy to miss. Scope the exact trigger condition +
      backlog-task shape as its own small LOCAL plan before dispatching.

## Track C — Fleet + Backlog Detail done-categorization display

Operator-confirmed scope (interactive session 2026-08-06): Fleet gets a per-slot badge (not expand-only, not skipped);
Backlog Detail gets all three of retry-count-on-done, rejection-count-on-dispatched, and a new `done failed` tab.

- [x] 1. ✅ [UI] P1. `dashboard/src/layout.tsx` `SlotTable`: added a `DoneBadge` component + `latestDoneOutcomeBySlot`
      helper — a new "Done" column showing a ✓/✗ pill per slot row, reflecting that slot's most recent `slot_done` vs.
      any `DONE_FAILED_TYPES` event (correlated by `slot_id` + highest `id`, deliberately ignoring `slot_done_verified`
      as a non-outcome companion event), with the reason on hover. `SlotCards` (the secondary, non-default view)
      intentionally left out of scope — Table is the default `slotLayout` and matches what the operator's own
      screenshots showed; cards parity is a natural follow-up if wanted later, not silently dropped. Done-when: 5 new
      vitest cases for `latestDoneOutcomeBySlot` — 217/217 dashboard tests green. — agent-orchestrator@e761cb1
- [x] 2. ✅ [UI] P1. `BacklogDetailModal`, "done" tab: per completed task row, a retry-count indicator ("· N rejected")
      next to the status pill — counts `DONE_FAILED_TYPES` activity events for that `task_id`. Built as a single bulk
      client-side correlation (one `/api/activity?types=...&limit=500` fetch alongside the existing `/api/backlog`
      fetch, via `Promise.all`, grouped into a `Map<task_id, count>`) rather than a new backend endpoint — avoids the
      N+1 the plan worried about without needing a server change. Done-when: a Playwright e2e case (fixture: 2 seeded
      `slot_done_rejected_dirty` events on E2E-DONE) asserts "· 2 rejected" renders — green, stable across repeated
      runs. — agent-orchestrator@e761cb1
- [x] 3. ✅ [UI] P2. Same rejection-count indicator on the "dispatched" tab's still-in-flight tasks. Done-when: a
      Playwright e2e case (fixture: 1 seeded `slot_done_rejected_no_plan_flip` event on E2E-DISPATCHED) asserts "· 1
      rejected" renders on the dispatched row — green. — agent-orchestrator@e761cb1
- [x] 4. ✅ [UI] P1. New `BacklogDetailModal` tab (button label "rejected" — NOT "done failed": that label's own
      `/^done\b/`-style test selector collided with the pre-existing "done" tab button, a real bug caught by running the
      e2e suite, not just typecheck) listing rejected-attempt _events_ via a dedicated `DoneFailedTab` component — same
      column set as "done" where a matching `task_id` is still in the currently-loaded backlog, falling back to "(task
      not in current backlog.yaml)" otherwise. Done-when: a Playwright e2e case asserts the tab's row count (3) matches
      the sum of seeded `DONE_FAILED_TYPES` events, split correctly 2/1 across the two source tasks — green. —
      agent-orchestrator@e761cb1
- [x] 5. ✅ [REVIEW] P2. Full verification pass, all green: dashboard `npx tsc --noEmit` + `npx vitest run` (217/217) +
      the full `backlog-detail.spec.ts` suite (9/9, repeated ×2 for stability) + the adjacent
      `fleet-token-cache-badge.spec.ts`/`mobile-backlog.spec.ts` suites (5/5, no regression) + `ruff check` +
      `basedpyright` clean on every touched Python file + the broader
      `pytest -k "done_gate or verify or     backlog_detail or slots_worker"` suite (129 passed, 2 pre-existing skips).
      Two REAL bugs found and fixed during this pass (both by actually running the e2e suite, not just trusting
      typecheck): the tab-label selector collision above, and a genuine pre-existing e2e-fixture gap —
      `seed_e2e_state.py`'s `SlotRow(slot_id=1, ...)` never set `current_task="E2E-DISPATCHED"`, so
      `WorkerLivenessWatchdog._reclaim_orphaned_dispatched_tasks` (120s grace, well under this fixture's
      `dispatched_at=now-5m`) deterministically reclaimed the fixture task back to "queued" on the very first tick — NOT
      a timing flake (confirmed via `git stash` A/B against the pristine baseline: reproduced 2/2 there too), a genuine
      one-line fixture bug that also silently broke two PRE-EXISTING tests (`backlog-detail.spec.ts`'s timestamp-columns
      and chronological-sort cases) before this session ever touched the file. Fixed as part of this same commit since
      it's the identical fixture row Track C already depends on. One separate, unrelated flake observed and diagnosed
      (NOT fixed, out of scope): running the FULL e2e suite serially, `deepseek-per-turn-metrics.spec.ts`'s
      per-turn-efficiency case occasionally loses a race against `DeepSeekUsagePoller`'s background recompute of
      `avg_turns_per_task` — confirmed pre-existing (reproduces on pristine baseline too) and confirmed NOT caused by
      this plan's code (passes 3/3 in isolation; the poller never touches anything this plan changed) — a general
      full-suite-timing fragility, not a Track C regression. — agent-orchestrator@e761cb1

## Codex SSOTs

- `/codex/05-infrastructure/agent-orchestrator-deploy.md` — dashboard is a Vite SPA auto-deployed via
  `.github/workflows/deploy-dashboard.yml` on every push to `live-defi-rollout` (Firebase Hosting); no manual deploy
  step needed once Track C ships.
- `/codex/08-workflows/ci-cd-flow.md` — quickmerge / strict-quickmerge / LDR-is-SSOT / promotion gate set.
- `/codex/04-architecture/agent-orchestrator-alerting.md` — Slack alert conventions the Track B message text should stay
  consistent with.

## Progress Log

- **2026-08-06 (interactive session)**: Plan authored. Root cause for Track A and the existing-tooling landscape for
  Track B verified live (SSM read of 60 `slot_done_rejected_dirty` rows; read of
  `check_strict_quickmerge.py`/`reprovenance_bypass.sh`/`ldr-to-main-promote.yml`/`promotion_lag_monitor.py`) before
  writing any todo — see chat transcript for the full evidence trail. Track C scope confirmed via operator Q&A in the
  same session (Fleet: badge on row; Backlog Detail: both retry-count-on-done and rejection-count-on-dispatched, plus a
  new done-failed tab — 3 additions, not either/or).
- **2026-08-06 (same interactive session, close-out)**: All three tracks shipped. Track A: discovered already-fixed by a
  prior same-day commit (`market-tick-data-service@a8c590a0`), recovered a quickmerge rebase conflict cleanly with zero
  data loss. Track B: `agent-orchestrator@ef59837` — new `/done`-time quickmerge-provenance gate, warn-only default, 4
  new unit tests + full existing done-gate suite (94 tests) green; the test suite itself caught and fixed a real
  range-computation bug (`origin/live-defi-rollout..sha` is always empty by /done time — fixed to `{sha}~1..HEAD`)
  before it ever shipped. Track C: `agent-orchestrator@e761cb1` — Fleet done badge + Backlog Detail retry/rejection
  counts + new "rejected" tab, 9/9 e2e tests green (stable across repeats), 217/217 vitest green; running the real e2e
  suite (not just typecheck) caught two more real bugs pre-ship: a tab-label test-selector collision, and a genuine
  pre-existing `seed_e2e_state.py` fixture gap (missing `SlotRow.current_task`) that was silently breaking two OTHER,
  unrelated pre-existing tests before this session ever touched the file — fixed as part of the same commit. One
  separate flake (`deepseek-per-turn-metrics.spec.ts` racing a background usage poller) diagnosed as pre-existing and
  NOT caused by this plan (confirmed via `git stash` A/B against the pristine baseline) — left unfixed, out of scope.
  Remaining open item: Track B's `[REVIEW] P3` stretch/optional follow-up (auto-filing an AO backlog task from
  `promotion_lag_monitor.py`'s `provenance_blocked` finding) — intentionally left as a scoping note, not built this
  session; plan stays `active` (not archived) until that's either scoped into its own todo or explicitly dropped.
