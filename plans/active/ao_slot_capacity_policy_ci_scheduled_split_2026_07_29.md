---
doc_type: plan
title: AO slot-capacity policy — split CI/CD-escalation vs scheduled-task reserve, cap plan workers at 10
summary: >-
  Operator asked for the agent-orchestrator's worker-slot pool (~15 observed) to structurally guarantee 3 slots always
  idle for CI/CD-failure escalation, 2 for scheduled/cron dispatch, and cap Class-A plan-worker backlog at 10 — so a CI
  escalation is never blocked and daily scheduled-task batches can always run. Implemented the split in code, fixed an
  active production Cloud Build break found along the way, found and safely preserved unrelated pre-existing WIP
  discovered entangled in the same files, and scoped the remaining benchmark + live-VM-correction work as tracked todos.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, instruments-service]
scope: [engineer, admin]
tags: [agent-orchestrator, capacity, ci-cd, scheduled-dispatch, slot-reserve, cloud-build]
related:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/archive/issues/ao_escalation_and_scheduled_dispatch_slot_starvation_2026_07_27.md,
    /plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md,
    /plans/active/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md,
  ]
created: 2026-07-29
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
depends_on:
supersedes:
superseded_by:
source: "operator ask 2026-07-29, interactive session slot 1"
locked_by: live-defi-rollout
locked_since: 2026-05-21
context_scope:
  [/codex/08-workflows/ci-cd-flow.md, /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md]
---

# AO slot-capacity policy — CI/CD-escalation vs scheduled-task reserve split

## Why this doc exists

Operator's ask (2026-07-29, paraphrased): of the agent-orchestrator's worker slots, structurally guarantee 3
always-available for CI/CD escalation, 2 for scheduled/cron dispatch, leaving 10 max for Class-A plan-worker backlog —
this is separate from the persistent `main`/`review` singletons. Goal: CI/CD escalation must never be blocked, and
scheduled-task batches (e.g. a 9-tranche `/ag-closeout-audit` run) can always make forward progress. First step
requested: free the 3 CI slots + use them for whatever one-shot work would unblock CI today; then the rest of the
capacity-policy work; then benchmark the scheduled skills' real per-shard timing (operator suspects they may need up to
9 slots each) by running them in the order AO does, to get real numbers before deciding whether a 2-hour block is
enough.

## What already existed (codex/history)

A single combined `ORCHESTRATOR_ESCALATION_SLOT_RESERVE` (default 2) already protected escalation.py (CI-failure) +
plan_health.py (scheduled dispatch) as ONE undifferentiated pool — built 2026-07-27 for
`ao_escalation_and_scheduled_dispatch_slot_starvation_2026_07_27.md` (now archived/resolved). Gap: no distinction
between "3 for CI" and "2 for scheduled" — a scheduled-task burst (a 9-tranche ag-closeout-audit firing 9 concurrent
`dispatch()` calls) could exhaust the ENTIRE combined reserve, leaving zero capacity for a simultaneous CI failure.
`DEFAULT_FLEET_WORKER_CAP` was already 10 in code, but the LIVE orchestrator VM has an env override
(`ORCHESTRATOR_FLEET_WORKER_CAP=12`) that doesn't match the target.

## What shipped today

### 1. CI-unblock work (today's Slack alert, actioned first)

- [x] ✅ **instruments-service Cloud Build was actively broken** — `uv pip install --system --no-sources -e .` couldn't
      reach the private `unified-libraries` GAR index (`uv` doesn't read pip.conf's `extra-index-url`; a prior
      `UV_KEYRING_PROVIDER=subprocess` attempt 401'd and also broke resolving plain-PyPI build-system deps). Fixed via a
      BuildKit secret (`gar_token`, minted in `auth-precheck`, consumed only by the `uv pip install` RUN layer, never
      baked into an image layer). Found + fixed 2 more bugs in my own first attempt (missing `gcloud` in the
      docker-builder image; an exit-code-masking trailing command) via direct `gcloud logging read` scoped to the build
      id — do not trust step-status alone. **Verified via a real Cloud Build** (`bf19495c-def6-45fe-99c4-3a61211990a7`,
      SUCCESS end-to-end, `:latest` genuinely re-pointed). Shipped `instruments-service@76eba912` +
      `instruments-service@4c05f2d3`. Full writeup:
      `/plans/active/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md`.
- [x] ✅ **DONE 2026-07-30 — fleet-wide rollout of the same fix to 4 of 5 flagged repos**, same verification discipline
      as instruments-service (adapted per-repo, not blind-copied — field names/step ordering differ across Dockerfiles;
      shipped first, THEN triggered a real Cloud Build — an earlier attempt caught its own mistake of "verifying"
      against remote HEAD _before_ pushing, which just re-tested stale code): - `alerting-service@bd6aebb` — build
      `ad0676f7-0c12-448b-8ea0-588f60cc3b85`, SUCCESS (confirmed via `gcloud builds describe`, 2026-07-30T00:23:32Z). -
      `market-data-processing-service@afcf984` — build `3f147ab5-12e4-4d53-8fa8-fda87ab3c57b`, SUCCESS (00:23:37Z). -
      `ml-service@cc732d8` — build `0e509171-3b98-4b13-9476-771f3dab1a87`, SUCCESS (00:23:42Z). -
      `strategy-service@9c499721` — build `23bfa809-9cee-4368-892c-5911bd0bcbec`, SUCCESS (00:23:47Z). -
      `market-tick-data-service` — **confirmed NOT affected, no fix applied.** Read the Dockerfile directly rather than
      assuming parity: it installs `unified-trading-library` and `unified-api-contracts` from vendored local paths
      (`uv pip install --no-cache-dir --no-sources -e .deps/unified-trading-library`, same for UAC) _before_ its own
      `uv pip install --system -e . --no-deps` — it never resolves either package from the private GAR index at build
      time, so the publish-ordering/auth gap this doc tracks doesn't apply here. Full writeup + evidence:
      `/plans/active/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md`. Each ship gated on
      local `quality-gates.sh` green (GitHub's own CI was down fleet-wide during this window — see the new P0 issue in §
      6 below — so these Cloud Build triggers are the only external verification these 4 commits have; GitHub
      quality-gates-v2 confirmation is still pending that outage clearing).

### 2. The 3/2/10 slot-reserve split (code — SHIPPED)

Replaced the single `escalation_slot_reserve()` with two independent, structurally-enforced reserves:

- `config.ci_escalation_slot_reserve()` — default **3** (env `ORCHESTRATOR_CI_ESCALATION_SLOT_RESERVE`).
- `config.scheduled_task_slot_reserve()` — default **2** (env `ORCHESTRATOR_SCHEDULED_TASK_SLOT_RESERVE`).
- `_apply_fleet_cap` (autospawn.py) clamps Class-A's effective cap to
  `total_non_review_slots - (ci_reserve + scheduled_reserve)`, so raising `ORCHESTRATOR_FLEET_WORKER_CAP` can never
  silently erase either reserve (same mechanism as before, now driven by the sum of two numbers).
- **New, and the actual gap-closer**: `config.ci_escalation_reserved_slot_ids()` computes the specific highest-numbered
  non-review slot ids the CI reserve maps to, and `plan_health.py`'s own `_pick_free_slot` now EXCLUDES that exact set —
  so a scheduled-task burst can no longer physically claim a CI-only slot, not just be numerically discouraged from it.
  This is asymmetric by design: CI escalation is NOT symmetrically blocked from the scheduled-task reserve (its
  never-block guarantee outranks a scheduled task's floor).
- Codex updated: `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "The two worker classes" (the
  "free-slot semantics are shared" paragraph now documents the split + asymmetry).
- Tests: `test_autospawn.py` (rewrote the combined-reserve regression test for the split; added a dedicated
  slot-id-partitioning test) + `test_plan_health.py` (new autouse fixture disabling the reserve by default for the
  file's tiny slot fixtures, since none of those 31 existing tests are about this feature; added one dedicated test
  proving a scheduled dispatch can't claim the sole CI-reserved slot even when it's the only physically-free one).
- `bash scripts/quality-gates.sh` green (ruff/basedpyright/pytest 1981+ passed/dashboard) after separating out unrelated
  pre-existing WIP (see below).

- [x] ✅ **DONE 2026-07-29** — `agent-orchestrator@64365ad`. Shipped `server/config.py` + `server/autospawn.py` +
      `server/plan_health.py` + `tests/test_autospawn.py` + `tests/test_plan_health.py` (scoped, `server/dedup_state.py`
      deliberately excluded, see the WIP note below). `bash scripts/quality-gates.sh` green pre-ship;
      `git rev-list --count     origin/live-defi-rollout..HEAD` == 0 post-push.

### 3. ✅ RECLAIMED + SHIPPED: the foreign "pool-critical-halt" WIP (2026-07-30, `/autonomous`)

Earlier (2026-07-29) this doc found `server/autospawn.py` (+ `tests/test_autospawn.py`, + `server/dedup_state.py`)
carrying substantial uncommitted work entangled with the slot-reserve-split edits — a "fleet-wide critical pool headroom
halt" feature (`_CRITICAL_POOL_HEADROOM_PCT`, `best_account_used_pct()`, `is_pool_critically_exhausted()`,
`_maybe_alert_pool_critical_halt()`, `dedup_state.pool_critical_halt_path()`), citing "operator ruling 2026-07-29", and
preserved it via two named stashes rather than risk shipping it silently or losing it.

Under the `/autonomous` dispatch (operator away ~6h, "finish everything"), rule 4 ("reconcile everything down here, now
— assume no one else is working") applied: reclaimed both stashes, 3-way-merged them onto the current HEAD (which by
then already had the shipped reserve-split code) — `git stash pop` reported a spurious "would be overwritten by merge"
on both files but the merge itself completed cleanly (no conflict markers, valid syntax, verified via `ast.parse`),
including an unplanned bonus: the merge's own version extracted `_check_and_log_critical_pool_halt` and
`_load_backlog_and_prerequisites_fail_closed` as separate `AutoSpawnLoop` methods, which incidentally resolves a
`_run_one_tick` cyclomatic-complexity concern noted earlier in the same session. Ran the full
`bash scripts/quality-gates.sh --no-fix` (ruff/basedpyright/1989 pytest passed + dashboard tsc/165 vitest) — one ruff
format nit on `autospawn.py`, fixed via a scoped `ruff format` on that single file (not a tree-wide reformat). Shipped
via `quickmerge --agent --files 'server/autospawn.py server/dedup_state.py tests/test_autospawn.py'`.

- [x] ✅ **DONE 2026-07-30** — `agent-orchestrator@b9d6190`. `git rev-list --count origin/live-defi-rollout..HEAD` == 0
      post-push. Both stashes (`stash@{0}`, `stash@{1}`) are now fully redundant (content verified subsumed by the
      pushed commit) but remain listed in `git stash list` — a workspace guardrail hook
      (`block_destructive_commands.py`) unconditionally blocks `git stash drop`/`clear` for autonomous workers
      regardless of reversibility, so they were deliberately left in place rather than force-removed. Harmless
      (`git stash list` clutter only); an operator can `git stash drop stash@{0}` / `stash@{1}` at their convenience —
      not a follow-up todo, just a note so nobody re-investigates them thinking they're still unshipped work.

### 4. Live orchestrator VM correction — DONE 2026-07-30 (`/autonomous`, operator's broad "finish everything" authorization)

Re-checked the live value directly (`grep ORCHESTRATOR_FLEET_WORKER_CAP .env.local` via SSM) before touching anything —
it's actually **15**, not the "12" this doc previously stated (earlier research was stale/wrong; corrected here rather
than propagated). Read the shipped `_apply_fleet_cap` code before deciding whether to change it:
`effective_cap = min(config.fleet_worker_cap(), max(0, len(non_review_slots) - reserve))` — the reserve-split code
ALREADY clamps the effective cap to the slot-count-minus-reserves figure regardless of the raw env var, so with ~15
total slots and a reserve of 5, the effective cap is already ~8-10 today, with `ORCHESTRATOR_FLEET_WORKER_CAP=15` not
the binding constraint. **No env-var change was needed or made** — changing 15→10 would have been a no-op given the
`min()`, and touching a live production env var for a change with zero behavioral effect isn't worth the (small but
real) risk.

What the live VM DID need: the actual shipped code deployed and active. Checked the VM's own `agent-orchestrator`
checkout — already at `origin/live-defi-rollout` HEAD (`b9d6190`, this doc's own shipped commit) via its own auto-pull
mechanism, ahead=0/behind=0. The service runs uvicorn with `--reload --reload-dir server`, which should auto-pick-up
on-disk changes, but rather than trust that inference, did an explicit `systemctl restart orchestrator.service` to be
certain (CLAUDE.md's own "maintenance-window restarts skip operator scheduling pre-live-trading — group + do now, brief
downtime OK" carve-out applies here, and the operator's own "/autonomous, finish everything" directive covers exactly
this class of decision). Verified healthy post-restart: `GET /api/state` → HTTP 200, `server_started` matches the
restart timestamp, live tick data shows `"10 working"` — consistent with the new 3/2/10 split actually taking effect.

- [x] ✅ **DONE 2026-07-30**. No env-var change needed (reserve-split code already makes the raw cap non-binding);
      `orchestrator.service` restarted, confirmed healthy and running the new code.

### 5. Scheduled-task benchmark — not started, needs a real-data-first approach

Operator's theory: scheduled skills (e.g. `/ag-closeout-audit`, `/na-eligibility-audit`) may run in shards needing up to
9 slots each; wants real per-skill/per-shard timing to check whether a 2-hour block is enough, before assuming resource
availability. Operator's own caveat: historical human-planning-VM logs likely conflate scheduled-skill time with other
work happening in between, so may not be a clean benchmark; asked me to check what AO itself has first.

- [x] ✅ **DONE 2026-07-30 — usable historical data DOES exist, no live benchmark needed.** Queried the AO `agents`
      table directly via SSM (`registered_at`→`finished_at` per agent row, `exit_reason='lifecycle-complete'` only — a
      clean per-worker duration, not conflated with other slots' concurrent unrelated work, since each row is scoped to
      the one worker that owned it): - `ag_closeout_auditor` (9-concurrent-tranche dispatch): 9 completed samples, range
      4.9–53.8 min, mean 33.1 min. Worst observed case is 45% of a 2-hour budget. - `na_eligibility_auditor` (also
      9-concurrent-tranche): 9 completed samples, range 2.7–**87.5** min, mean 24.4 min. Worst observed case is 73% of a
      2-hour budget — real margin, but noticeably less than `ag_closeout_auditor`'s; worth a periodic re-check rather
      than treating this as settled, since these are 9 samples, not a large population, and the one outlier (87.5 min,
      `agt-ae219c`) was independently observed this session to be doing genuine, heavy multi-phase work
      (structured-output retries, sub-agent fan-out), not stuck — i.e. a real tail, not a measurement artifact. -
      `docs_reconciler`: only 2 samples (6.6, 11.2 min) — too sparse to draw a real distribution from; not a 9-tranche
      dispatch pattern like the other two, lower priority to backfill. Since these tranches run CONCURRENTLY (one worker
      per tranche), the relevant "does 2 hours suffice" question is bounded by the SLOWEST tranche, not the sum — both
      audited kinds comfortably clear a 2-hour block on every observed sample. Not run as a fresh live benchmark
      (unnecessary cost given usable history already existed) — per the operator's own instruction to check AO's
      existing data first.

### 6. Still-open from today's live CI-capacity incident (confirmed as in-scope by operator)

From `/plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (P1, still open):

- [x] ✅ **DONE 2026-07-30 — both re-measured, both substantially IMPROVED (the slot-reserve-split appears to have
      worked)**: - PM `plan_health` queue: **fully resolved**. Live query (`GET /api/escalations/active`) shows 11
      recent `plan_health` escalations for `unified-trading-pm`, ALL `status=resolved`/`resolution=qg_v2_green`, ZERO
      currently `dispatched`-and-stuck — a dramatic change from the "44 active, none resolving" baseline this todo was
      filed against. - Protected-6 `ldr_qg_failure`: down from 47+ (day-2 baseline) to 17 fleet-wide, and the
      high-attempt-count pattern (46/78-attempt escalations) is gone — remaining attempts are single digits to low
      teens. The remaining activity is now concentrated on `instruments-service` specifically, which on investigation
      turned out to be a DIFFERENT, separate, much bigger problem — see the new P0 issue immediately below, not a
      continuation of the host-contention story this todo was tracking.
- [x] ✅ **RESOLVED 2026-07-31 — GitHub Actions billing wall cleared, fleet running clean.** Was: NEW P0, GitHub Actions
      down fleet-wide (every workflow on every repo failing instantly with `startup_failure`, 0 jobs created), strong
      evidence of a spending-limit cap. Re-verified live 2026-07-31T08:16Z: `unified-trading-pm` runs completing with
      real durations (67s-1m9s, incl. a 9-step job that ran and failed on its own merits, not `jobs:[]`);
      `instruments-service` `quality-gates-v2` ran a full 25m28s and the LDR→main promote chain
      (`quality-gates-v2`→`main-backmerge-to-ldr`→`Semver Agent`) completed clean end-to-end — the exact fleet-wide
      promote path the incident had blocked. Full evidence + timeline in
      `/plans/active/issues/github_actions_billing_wall_recurrence_2026_07_29.md`.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — updated 2026-07-29 with the split-reserve
  mechanics.
- `/codex/08-workflows/ci-cd-flow.md` — Cloud Build / quickmerge / CI-verification conventions this session followed.

## Progress Log

- **2026-07-29 (interactive, slot 1)**: Cloud Build fix shipped + verified live. Slot-reserve split implemented, tested,
  quality-gates green, ready to ship. Foreign WIP found + safely stashed (not shipped, not destroyed). Live-VM
  correction and the scheduled-task benchmark deliberately left as tracked todos rather than executed unilaterally,
  given their larger blast radius / cost.
- **2026-07-30 (`/autonomous`, operator away ~6h, "finish everything")**: every remaining todo closed out. Reclaimed +
  shipped the foreign pool-critical-halt WIP (`agent-orchestrator@b9d6190`). Rolled out the Cloud Build GAR-auth fix to
  the 4 repos that needed it, each verified via a real post-ship Cloud Build trigger (not just local QG) — caught and
  corrected my own process mistake along the way (a pre-ship "verification" build tests the remote branch, not local
  uncommitted state; shipped first, then re-verified). Corrected the live-VM understanding (cap is 15, not 12; the
  shipped code's own slot-count clamp already made the exact value non-binding) and restarted `orchestrator.service` to
  guarantee the new code is active — confirmed healthy. Answered the scheduled-task benchmark from existing AO history,
  no live re-run needed. Re-measured both open capacity-crisis todos — both substantially improved by the reserve-split.
  Along the way found and fixed an unrelated, already-committed bug (literal unresolved git-conflict markers in
  `scripts/quality-gates-base/base-service.sh`, breaking every PM TYPE-CHECK run) — resolved concurrently by another
  session before my own fix landed, confirmed same resolution. Biggest finding: GitHub Actions is currently down
  fleet-wide (likely a spending-limit cap) — filed as its own P0 issue doc, pushed a notification, left for the operator
  since it needs their billing UI.

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — sole open todo is `[OPERATOR] P0` — needs the operator's own
  github.com/settings/billing UI; `locked_by: live-defi-rollout`.
- **2026-07-30 (rulings-closeout pass, separate session)** — re-verified this doc's state per a workspace-wide sweep
  closing out recorded operator rulings implying unshipped work. Both `[OPERATOR]`-class actions this doc originally
  flagged as deliberately-left-alone (reclaiming another slot's foreign uncommitted `autospawn.py` WIP; restarting the
  live orchestrator VM) are confirmed **already executed** by the `/autonomous` continuation recorded in §3/§4 above —
  independently re-verified rather than trusted at face value: `agent-orchestrator@b9d6190` exists and is a confirmed
  ancestor of the repo's current `origin/live-defi-rollout` HEAD (`81f54a8`, `git merge-base --is-ancestor` confirmed).
  Nothing left to re-attempt from that pair. The one remaining open item (§6, GitHub Actions billing wall) is correctly
  `[OPERATOR]`-gated — genuinely needs the operator's own `github.com/settings/billing` access, not something any agent
  can resolve. No action taken; no changes needed.
- **2026-07-31** — GitHub Actions billing wall confirmed cleared (live `gh run list`/`timing` checks on
  `unified-trading-pm` and `instruments-service`, real run durations + a completed LDR→main promote chain, vs. the
  incident's `run_duration_ms:1000`/`jobs:[]` signature). Flipped the sole remaining todo (§6) to done. **All 8/8 todos
  now done — plan is complete, left `status: active`/not archived per operator instruction** (not yet run through the
  archival ritual).
