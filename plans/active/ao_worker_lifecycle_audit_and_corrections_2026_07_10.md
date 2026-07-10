---
doc_type: plan
title: AO worker lifecycle — boot-instruction corrections + runtime hardening (2026-07-10 audit)
summary:
  Sibling to the task-lifecycle plan — this audits the WORKER lifecycle (spawn → boot → liveness → teardown) across the
  role boot prompts, the runtime loops, the activity log and the state DB, and fixes what drifted. Headline — a markdown
  fence mismatch in agents/worker.md has silently truncated EVERY worker's boot prompt by ~50 lines for ~7 weeks
  (dropping the idle-loop self-recovery recipe + the "Start now — call /boot" closer), and no test caught it. Plus a
  cluster of role-prompt drift (RULES.md still teaches the retired tab-branch model, main.md cites a non-existent
  backlog path + carries a dead phase-DAG, escalation_to renders wrong in the dashboard) and four runtime hygiene gaps
  (teardown never reaps worker background jobs → 10-17-day orphan leak; idle_blocker_inferred +
  slot_released_prereq_blocked log spam; the worker_kick_failed measurement artifact; proactive-spawn churn). Runtime is
  HEALTHY now — this is latent drift, not an incident.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    worker-lifecycle,
    boot-prompt,
    role-instructions,
    watchdog,
    autospawn,
    teardown,
    log-hygiene,
    audit,
  ]
related: [../epics/orchestrator_master.md, ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md]
created: 2026-07-10
last_updated: 2026-07-10
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
depends_on:
supersedes:
superseded_by:
source:
  [operator request 2026-07-10 — worker-lifecycle exploration (drift / sloppy work in spawn→boot→liveness→teardown)]
assigned_role: backend-engineer
drift_direction: advance-code
---

# AO worker lifecycle — boot-instruction corrections + runtime hardening

> **Status: ACTIVE — operator approved 2026-07-10; executing in SLOT 16 (interactive session, claimed + `paused` so
> AutoSpawn never spawns over it). `execution_scope: local-only` — the AO fleet does NOT execute this plan (it patches
> the AO's own boot prompts + spawn/watchdog path; a bad edit could break the very workers that would run it).**
>
> Sibling to `ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md` (that plan fixed the TASK lifecycle —
> done-gate, resume, preserve-on-handoff; this one fixes the WORKER lifecycle — boot prompt, teardown, liveness noise).

## 1. Findings — evidence from the 2026-07-10 worker-lifecycle exploration

Investigated four surfaces: the role boot prompts (`agents/*.md` + `docs/*.md`), the runtime loops (`server/`), the
activity log and the state DB (`data/state/state.db`), all on the planning VM. **The runtime is healthy right now** —
since the 2026-07-09 18:30Z restart: `autospawn_failed`=0 (was 469/24h pre-restart), `worker_kick_failed`=16 (~1.5/hr,
was 773), `slot_boot`=6 (was 287); queue drained (141 done / 1 queued, blocked on `footystats-mp-complete`); all 14 idle
slots `tmux_session=None` (workers correctly reaped). Everything below is LATENT drift, not an on-fire incident.

### 1a. Boot-instruction findings (role prompts) — verified by running the real extractor + reading the files

1. **CRITICAL — `agents/worker.md` fence mismatch silently truncates EVERY worker's boot prompt (~7 weeks).** The
   extractor in `server/prompts.py::_extract_template` requires the CLOSING backtick-fence to be the same length as the
   opening one. `worker.md` line 53 opens the template with a 4-backtick `text` fence, so the extractor looks for the
   next 4-backtick line to close it. Line 537 is a stray 4-backtick line (it should be 3, closing the inner bash example
   opened at line 533), so the extractor closes the template THERE instead of at the intended line 590. **Verified by
   running the actual production extractor**: it captures 483 of the intended ~536 template lines (26,872 / 34,158
   chars); the render ends mid-example at the `/progress` curl. Dropped content (lines 538-588, read directly): the
   entire idle-loop resilience recipe (the 5×60s heartbeat self-poll written to fix the "died silently 5× on 2026-05-19"
   incident), the "WHEN IDLE poll /heartbeat every 60s" section, "The worker NEVER exits on its own", and the closing
   "Start now: call /boot." — all five sentinels confirmed ABSENT from the rendered prompt. `render_worker` uses
   `worker.md` as the base for EVERY worker (plain + all 5 craft roles), so the whole fleet is affected. Introduced by
   commit `df011af2` (2026-05-20). **No test catches it** — `tests/test_prompts.py` only compares equally-truncated
   renders against each other. A second latent instance of the same 3-vs-4 mismatch sits at lines 600/604 (inert only
   because 537 fires first). **Connection to runtime**: the dropped block is the worker's CLIENT-side self-recovery at
   task boundaries — its absence is plausibly WHY workers go silent after `/done`, exactly what the server-side kicker +
   heartbeat-silent watchdog + boot-grace have been compensating for. (Hypothesis; the truncation itself is certain.)

2. **HIGH — `agents/RULES.md:26-29` teaches the RETIRED tab-branch model as current fact.** The STEP-0 file every role
   is told to read FIRST states "Each repo's worktree is on branch `tab/<operator>/<SLOT_ID>` (e.g. `tab/hk/4`)" — the
   exact model CLAUDE.md calls RETIRED, and contradicted by `worker.md`'s own Path-B section. RULES.md never says "clone
   --reference" or "Path-B" anywhere. A fresh agent forms its git mental model from this doc.

3. **HIGH — `agents/main.md` cites a non-existent backlog path (3×).** Lines 85, 158, 702 say
   `orchestrator/data/config/backlog.yaml`; verified the real path is `data/config/backlog.yaml` (exists) and the
   `orchestrator/`-prefixed path does NOT (`ls` fails). Leftover from the `orchestrator`→`agent-orchestrator` rename.
   Main-agent's literal cold-start step 1 → "No such file."

4. **HIGH — `agents/main.md:631-789` is ~160 lines of dead phase-DAG campaign content.** The source epic
   (`plans/epics/mtds_mdps_master.md`) frontmatter says its own Phase -2…14 table is "provenance only", but main.md
   still instructs "read this top-down every poll cycle" and cites the WRONG directory (`plans/active/` — lines 646,704
   — the file is in `plans/epics/`). Predates the single-VM pivot ("VM fleet" plural framing, fixed per-phase slot
   ownership). SENSITIVE — main.md is the main orchestrator's brain; the ~160-line removal is operator-review-gated.

5. **MED-HIGH — `escalation_to: cicd` is wrong on two roles AND rendered live in the dashboard.**
   `agents/plan-health.md:29` + `agents/data_pipeline_failure.md:29` set `escalation_to: cicd`, contradicting both
   files' own bodies (should be `operator`/`plan-reconciler` and `main`); all 7 sibling roles use `main`/`operator`.
   Consumed by `server/routes/roles.py:32` → rendered in the dashboard AGENT TYPES panel
   (`dashboard/src/layout.tsx:3107-3109`).

6. **MED — role-prompt doc-drift cluster** (one sweep task): `status: draft` on 4 fully-wired, actively-dispatched craft
   roles (`ui-developer`/`backend-engineer`/`quant-dev`/`infra`; sibling `data_engineering` = `active`);
   `agents/monitor.md:48,54,185` treats the deprecated + nonexistent `backup` role as a live peer (contradicts
   `server/orm.py:285`; no `agents/backup.md` exists); `docs/WORKER_SPAWN_PREREQUISITES.md:131-209` frames the
   already-shipped `WorkerLivenessKicker` as a "server-side TODO" and never mentions the sibling
   `WorkerLivenessWatchdog`; 5 SSOT footer pointers cite archived/dead plans (`cicd.md:55`,
   `conflict-resolver.md:49-50`, `plan-health.md:52,57,59`, `plan-reconciler.md:53`,
   `WORKER_SPAWN_PREREQUISITES.md:133`); RULES.md size claimed "~150/175 lines" in 3 files (`worker.md:58`,
   `monitor.md:84`, `MAIN_AGENT_CUTOVER_REVIEW.md:63,318`) — actually 264; `main.md:108-109` wires the wholly-historical
   `MAIN_AGENT_CUTOVER_REVIEW.md` §8 into the live boot sequence.

Full audit report retained in the session; all HIGH/CRITICAL findings independently re-verified (not relayed on faith).

### 1b. Runtime findings (server loops / DB) — verified against live state

7. **MED — teardown never reaps a worker's background jobs → multi-day orphan leak.** `tmux_spawn.py:156` `kill_session`
   is a bare `tmux kill-session` (no child/process-group reap). Worker background jobs escape the pane and reparent to
   `orchestrator.service`. Confirmed orphans still alive under the service cgroup: `tm_vm_monitor.sh` 12.3 days,
   `understat_monitor.sh` 11.4 days, `wait_and_reclass.sh` 10.8 days, a slot-1 shell 17.6 days — infinite poll loops
   that never self-exit, burning CPU + gcloud calls. Fed the pre-restart 56 GB cgroup peak + 15 GB swap (real
   orchestrator RSS is only 512 MB — the memory is fleet + leaks under one shared cgroup).

8. **MED — `idle_blocker_inferred` dedup guard is defeated → 657 identical rows for one slot.** The change-guard
   `if slot.last_msg != summary` (`server/worker_liveness/_git_alerts.py:95`) is real, but `slot.last_msg` is an
   overloaded field ping-ponged every tick by ≥3 writers (RED-repo nudge, git-staleness alert, idle-infer), so it
   re-logs every ~57s for any persistently-idle-blocked slot. Slot 3 alone = 657 rows (85% of the event) since restart.

9. **LOW-MED — `slot_released_prereq_blocked` is an hourly no-op.** The release path
   (`server/worker_liveness_watchdog.py:1207-1245`) is real (requeue + kill + free) but every fire had
   `released_task:null, killed_session:false` — it fires for idle slots holding NOTHING, then resets its own timer
   (line 1245) → re-fires hourly per idle slot whenever the queue is prereq-blocked (~10/slot across slots 4-15). Should
   be ONE fleet-level "queue 100% prereq-blocked on X" signal.

10. **LOW — `worker_kick_failed` measurement artifact** (already scoped). Post-restart residual 16 (~1.5/hr) = the P3
    fast-responder window (worker responds + returns idle inside the 2s post-kick snapshot; every event
    `submit_verified=True`). The 773/24h was the pre-restart storm.

11. **DISCUSS — proactive-spawn vs spawn-on-demand.** With the queue drained to 1 blocked task, slots still get spawned
    (slot 2 @ 05:04, slot 3 @ 01:03) then reaped. Reaping WORKS — so the "reap task-less workers" idea is really "don't
    proactively spawn when nothing is dispatchable." Kills the churn at the source.

12. **DORMANT — autospawn dirty-state-quarantine log spam + resolution latency.** Pre-restart: 454 "dirty-state
    quarantined — not spawning over it" failure-logs in one morning (cooldown-bounded, dedup-alerted — not runaway), but
    a slot sat starved 6-9h. **Root cause was fixed by the 2026-07-09 sibling plan** (the fix-commit-identity hook
    rejection → preserve path with `--no-verify` + identity); 0 since restart. Remaining: log-throttle so a recurring
    quarantine doesn't spam, + confirm the sibling fix holds.

## 2. Tasks

### Phase A — Boot-instruction correctness (role prompts / docs)

- [ ] [CODE] P0. Fix the `agents/worker.md` fence mismatch (FENCE-ONLY per operator decision 2026-07-10): correct the
      stray 4-backtick closers at `worker.md:537` and `worker.md:604` to 3 backticks so the full intended template
      (through line 590) renders. Verify with the real extractor (`_extract_template` captures the "Start now: call
      /boot." sentinel). ADD a regression test to `tests/test_prompts.py` asserting the rendered `worker` template
      CONTAINS "Start now: call /boot" (and ideally the idle-loop sentinel) so a future truncation fails loudly.
- [ ] [CODE] P1. worker.md idle-loop CONTENT decision (the deferred call): decide whether the now-restored client-side
      bash idle-poll loop stays (belt-and-suspenders with the server kicker) or is pruned as superseded by the
      server-owned liveness stack (kicker + watchdog + boot-grace). Prune/keep + reconcile the wording with the current
      architecture. _(gated on the fence fix landing first)_
- [ ] [CODE] P1. `agents/RULES.md:26-29` — replace the retired `tab/<op>/<SLOT_ID>` worktree description with the
      current Path-B model (each slot = `git clone --reference` at `.tabs/<N>/<repo>` on `live-defi-rollout`, own
      `.git`, NO tab branch). Align with `codex/05-infrastructure/per-tab-worktrees.md`.
- [ ] [CODE] P1. `agents/main.md` — fix the backlog path at lines 85, 158, 702 (`orchestrator/data/config/backlog.yaml`
      → `data/config/backlog.yaml`); grep main.md + all role files for any other stale `orchestrator/`-prefixed path.
- [ ] [CODE] P2. `agents/main.md:631-789` — remove/replace the dead Phase -2…14 phase-DAG section (source epic says
      "provenance only"; fix the `plans/active/` → `plans/epics/` dir error if any of it is kept as a pointer).
      **[OPERATOR-REVIEW] — main.md is the main orchestrator's brain; surface the proposed diff before committing.**
- [ ] [CODE] P2. `escalation_to` correction — `agents/plan-health.md:29` and `agents/data_pipeline_failure.md:29` from
      `cicd` to the value each body actually documents (`operator`/`plan-reconciler` and `main` respectively). Verify
      the dashboard AGENT TYPES panel then renders correctly.
- [ ] [CODE] P2. MED doc-drift sweep (one commit): `status: draft`→`active` on the 4 wired craft roles (or document a
      `doc_type: agent-role` carve-out); remove the deprecated `backup`-role references in `monitor.md:48,54,185`;
      refresh the stale "server-side TODO" framing in `docs/WORKER_SPAWN_PREREQUISITES.md:131-209` (Kicker shipped; add
      the Watchdog); repoint the 5 archived/dead SSOT footers; correct the "~150/175 lines" RULES.md size claims; add a
      SUPERSEDED/historical banner to `MAIN_AGENT_CUTOVER_REVIEW.md` and drop the `main.md:108-109` boot-step wiring to
      it.

### Phase B — Runtime lifecycle hardening (server code)

- [ ] [CODE] P1. Teardown reaping — make `tmux_spawn.kill_session` (or the reclaim/prune callers) reap the worker's
      background/child processes (pane process-group) before/with `tmux kill-session`, so background jobs don't reparent
      to the orchestrator cgroup. Include a one-time sweep of the existing 10-17-day orphans. Guard against killing
      shared/host processes (scope to the pane's pgid only).
- [ ] [CODE] P1. Kick-window fix (`worker_kick_failed` artifact, operator-approved): treat `submit_verified=True` +
      `post_kick=idle` on a finished/idle worker as SUCCESS (or lengthen the 2s post-kick settle) so a fast responder
      isn't logged as a kick failure.
- [ ] [CODE] P1. Spawn-on-demand (operator-approved): gate proactive AutoSpawn on "≥1 dispatchable (prereqs-met) task
      exists (or an affinity/handoff reason)"; don't spawn a worker into an empty/fully-blocked queue only to reap it.
- [ ] [CODE] P2. `idle_blocker_inferred` dedup fix — give the inference a DEDICATED last-value field (or a
      time-throttle, e.g. log-on-change-or-hourly) so the shared-`last_msg` contention stops defeating the guard
      (`_git_alerts.py:95`).
- [ ] [CODE] P2. `slot_released_prereq_blocked` no-op fix — skip the event when nothing is actually released
      (`held_task is None and not had_session`); collapse the fleet-wide "everything blocked on X" case into ONE
      fleet-level signal instead of a per-slot hourly no-op (`worker_liveness_watchdog.py:1207-1245`).
- [ ] [CODE] P3. autospawn quarantine log-throttle + verify the 2026-07-09 preserve-path fix holds (0 dirty-quarantine
      failures since restart); add a spawn-attempt failure-log throttle/backoff so a recurring quarantine can't spam 454
      failure-logs, and confirm the quarantine `detail` string names the real error (not the FM2/FM8 red herring).

### Phase C — Verify

- [ ] [VERIFY] P1. Live verification with evidence per fix: worker.md render contains the boot sentinels (extractor +
      new test green); a spawned worker's boot pane shows the full prompt; teardown reap leaves 0 new orphans after a
      kill; `idle_blocker_inferred` / `slot_released_prereq_blocked` / `worker_kick_failed` rates drop in the activity
      log; dashboard escalation_to renders correctly. Cite `agent-orchestrator@<sha>` + activity-log deltas.

## 3. Codex SSOTs (read before touching each area — plan↔codex drift is review-blocking)

- `codex/12-agent-workflow/agent-orchestrator-overview.md` — worker lifecycle + loops
- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — single-VM / role-dispatch (the model
  main.md's dead DAG predates)
- `codex/05-infrastructure/per-tab-worktrees.md` — Path-B clone model (the correct RULES.md text) + commit identity
- `codex/04-architecture/runtime-deployment-topology.md` — central-VM + slots topology
- `../epics/orchestrator_master.md` (parent epic); `ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md`
  (sibling — the task-lifecycle half)

## 4. Progress Log

- **2026-07-10 ~05:40Z** — Plan created from the worker-lifecycle exploration (operator-requested). Four surfaces
  audited (role prompts, runtime loops, activity log, state DB). Runtime confirmed healthy post-2026-07-09-restart
  (autospawn_failed 0, kick_failed ~1.5/hr, 6 boots, queue drained, workers reaped). Headline finding: worker.md fence
  truncation (CRITICAL, ~7 weeks, whole fleet, no test) — independently re-verified via the real `_extract_template`
  (483/536 lines, all 5 boot sentinels absent). Operator decisions: LOCAL/human plan (slot 16, not fleet-dispatched);
  worker.md fix = FENCE-ONLY now, client-vs-server idle-loop content call deferred to task A2.
