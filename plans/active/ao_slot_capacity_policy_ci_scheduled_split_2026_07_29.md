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
last_updated: 2026-07-29
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
- [ ] [SCRIPT] P2. **Fleet-wide rollout of the same fix** to 5 more repos with the identical latent bug
      (`alerting-service`, `market-data-processing-service`, `market-tick-data-service`, `ml-service`,
      `strategy-service` — confirmed via grep, none currently broken but the next dependency floor-bump will hit the
      same failure). A dispatched sub-agent started this and hit the session's API rate limit mid-way (before shipping
      any of the 5) — re-dispatch using `instruments-service@4c05f2d3`'s Dockerfile + cloudbuild.yaml as the reference
      implementation, same verification discipline (local build with a real token, then a real Cloud Build trigger +
      `gcloud logging read` scoped to the build id).

### 2. The 3/2/10 slot-reserve split (code, ready to ship)

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

- [ ] [SCRIPT] P0. Ship `server/config.py` + `server/autospawn.py` + `server/plan_health.py` +
      `tests/test_autospawn.py` + `tests/test_plan_health.py` via
      `quickmerge --agent --files 'server/config.py server/autospawn.py server/plan_health.py tests/test_autospawn.py tests/test_plan_health.py'`
      (scoped explicitly — do NOT include `server/dedup_state.py`, see the WIP note below). Verify CI green post-push.

### 3. ⚠️ Found + preserved: unrelated pre-existing uncommitted work in this checkout

While editing `server/autospawn.py`, discovered it (and `tests/test_autospawn.py`, and `server/dedup_state.py`) already
had **substantial uncommitted work** entangled with my edits — a "fleet-wide critical pool headroom halt" feature
(`_CRITICAL_POOL_HEADROOM_PCT`, `best_account_used_pct()`, `is_pool_critically_exhausted()`,
`_maybe_alert_pool_critical_halt()`, wired into `_run_one_tick` + `dedup_state.pool_critical_halt_path()`), with code
comments citing "operator ruling 2026-07-29" — i.e. apparently legitimate, recent, deliberate work, NOT mine, sitting
uncommitted in this slot before I started.

**Not destroyed** — separated safely via two named git stashes so it's fully recoverable and never at risk of being
silently shipped as part of an unrelated commit:

- `stash@{1}`: `foreign-pool-critical-halt-wip-found-entangled-with-slot-reserve-split-2026-07-29`
  (`server/autospawn.py`'s foreign hunks)
- `stash@{0}`: `foreign-pool-critical-halt-tests-entangled-with-slot-reserve-split-2026-07-29`
  (`tests/test_autospawn.py`'s foreign hunks)
- `server/dedup_state.py`'s `pool_critical_halt_path()` addition (7 lines, 100% foreign, I never touched this file) is
  untouched in the working tree, not stashed, not committed — still sitting there.

- [ ] [OPERATOR] P1. **Whoever owns the "fleet-wide critical pool headroom halt" feature should reclaim it** —
      `git stash list` in `.tabs/1/agent-orchestrator` shows both stashes by name; `git stash pop     stash@{N}`
      restores each (pop the autospawn.py one, then re-apply the matching test stash, then decide whether to
      finish/verify/ship it — it looked substantially complete but was never run through quality-gates.sh in this
      session). If this was actually MY OWN work from earlier in this same session that fell out of context, same
      recovery path applies; if it's dead/abandoned, it's still recoverable from the stash indefinitely (not on any TTL)
      but should eventually be either finished or dropped deliberately rather than left in `git stash list` forever.

### 4. Live orchestrator VM correction — NOT done, needs a decision

The running orchestrator VM has `ORCHESTRATOR_FLEET_WORKER_CAP=12` (found via earlier research) — doesn't match the
target of 10. My code change fixes `DEFAULT_FLEET_WORKER_CAP`'s value (already 10) and the reserve semantics, but
doesn't touch this specific live env override, and the OLD `ORCHESTRATOR_ESCALATION_SLOT_RESERVE` env var (if the VM has
one set) becomes inert dead config once this ships (the field no longer exists) — the new defaults (3 + 2) apply
automatically UNLESS the live VM's `.env.local` also needs the two new env vars added explicitly for
clarity/auditability.

- [ ] [OPERATOR] P1. **Decide + execute the live correction**: SSH/SSM into the orchestrator VM (`i-0c9b283b31d6b5ca7`),
      fix `ORCHESTRATOR_FLEET_WORKER_CAP` (12→10 or remove the override entirely so the code default applies) in
      `.env.local`, optionally add explicit `ORCHESTRATOR_CI_ESCALATION_SLOT_RESERVE=3` /
      `ORCHESTRATOR_SCHEDULED_TASK_SLOT_RESERVE=2` for clarity, restart the orchestrator service to pick up both the new
      code (once deployed) and the env change. Not done autonomously this session — restarting the live orchestrator
      affects every currently active worker slot fleet-wide, a materially bigger blast radius than anything else done
      today; flagged for operator go-ahead rather than assumed.

### 5. Scheduled-task benchmark — not started, needs a real-data-first approach

Operator's theory: scheduled skills (e.g. `/ag-closeout-audit`, `/na-eligibility-audit`) may run in shards needing up to
9 slots each; wants real per-skill/per-shard timing to check whether a 2-hour block is enough, before assuming resource
availability. Operator's own caveat: historical human-planning-VM logs likely conflate scheduled-skill time with other
work happening in between, so may not be a clean benchmark; asked me to check what AO itself has first.

- [ ] [DATA] P2. Check whether AO has ever actually **successfully completed** a full scheduled-task run (not just
      dispatched one) — query the AO escalation/plan_health dispatch history via `/check-agent-orchestrator` or direct
      SSM (`GET /api/plan_health/...` or equivalent), looking for `result` posts with real durations, not just
      `dispatched` rows. State plainly whether usable historical timing exists or not — don't assume either way.
- [ ] [DATA] P2. If real historical completions exist with clean start→result timestamps, extract per-tranche duration
      distributions from those (cheap, no new compute). If not, or if they're too sparse/noisy, plan (don't necessarily
      run today, given the multi-hour real cost) a clean live benchmark: dispatch a small number of tranches (not all 9
      at once) with `force=True`, time each start→result independently, and extrapolate — flag the real wall-clock/token
      cost estimate to the operator before running the full 9-tranche sweep live.

### 6. Still-open from today's live CI-capacity incident (confirmed as in-scope by operator)

From `/plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` (P1, still open):

- [ ] [BACKEND] P2. Re-measure the protected-6 self-hosted repos' `ldr_qg_failure` retry-attempt counts via the AO
      escalation API (`GET /api/escalations/active`, SSM) now that the host was resized + swap added — confirms whether
      the 2026-07-29 operator ruling (stay self-hosted, re-measure before further change) is holding, or whether
      46/78-attempt-style escalations are recurring.
- [ ] [BACKEND] P2. Diagnose whether PM's `plan_health` escalation queue (44 active at last check, none resolving)
      shares the `ldr_qg_failure` host-contention root cause, or whether a `plan_health` worker type simply isn't being
      spawned/claiming slots at all — a structurally different failure mode from "slow due to contention".

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — updated 2026-07-29 with the split-reserve
  mechanics.
- `/codex/08-workflows/ci-cd-flow.md` — Cloud Build / quickmerge / CI-verification conventions this session followed.

## Progress Log

- **2026-07-29 (interactive, slot 1)**: Cloud Build fix shipped + verified live. Slot-reserve split implemented, tested,
  quality-gates green, ready to ship. Foreign WIP found + safely stashed (not shipped, not destroyed). Live-VM
  correction and the scheduled-task benchmark deliberately left as tracked todos rather than executed unilaterally,
  given their larger blast radius / cost.
