---
doc_type: plan
title:
  AO worker lifecycle — read-the-file boot cutover + stale-content correctness + runtime hardening (2026-07-10 audit)
summary:
  Sibling to the task-lifecycle plan — this audits the WORKER lifecycle (spawn → boot → liveness → teardown) across the
  role boot prompts, the runtime loops, the activity log and the state DB, and fixes what drifted. Headline — a markdown
  fence mismatch in agents/worker.md has silently truncated EVERY worker's boot prompt by ~50 lines for ~7 weeks
  (dropping the idle-loop self-recovery recipe + the "Start now — call /boot" closer), and no test caught it. FIX
  APPROACH (operator, 2026-07-10) — instead of patching the fence, remove the whole copy-paste/truncation class — cut
  over to a read-the-file boot mechanism (inject only per-session + escalation vars; point workers at the canonical role
  + RULES files, relocated into the PM repo; guardrail = read-from-root, operate-only-in-slot; /boot gated on
  read-confirmation). Plus stale-content correctness (RULES.md tab-branch, main.md path + dead-DAG, escalation_to) so
  agents can't trip on stale info, and four runtime hygiene gaps (teardown orphan leak; idle_blocker_inferred +
  slot_released_prereq_blocked log spam; the worker_kick_failed artifact; proactive-spawn churn). Runtime is HEALTHY now
  — this is latent drift, not an incident.
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
    boot-cutover,
    read-the-file,
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
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 2.4
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

# AO worker lifecycle — read-the-file boot cutover + stale-content correctness + runtime hardening

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
   **→ FIX: the read-the-file boot cutover (§2) removes the extraction/paste step entirely, so this fence bug (and the
   whole truncation class) becomes structurally impossible — no interim fence fix.**

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

## 2. Design decision — read-the-file boot mechanism (operator-approved 2026-07-10)

Rather than fix the fence bug in isolation, we remove the copy-paste / paste-truncation class entirely. **No interim
fence fix — the plan ships the final mechanism directly.** New boot model:

- **Inject only the DYNAMIC per-session values** — per-worker vars (`<SLOT_ID>`, `<SERVER_URL>`, `<SLOT_ROLE>`,
  `<LOOP_SECONDS>`, worktree/model/account) AND escalation incident vars (`<DISPATCH_ID>`, `<PR_NUMBER>`, `<WALL_TYPE>`,
  source/target branches…). These CANNOT come from a static file, so they stay in the injected stub. (Escalation prompts
  are short + one-shot → low truncation risk anyway.)
- **Point, don't paste, for the STATIC playbook** — the boot stub tells the worker to READ its role file + RULES.md,
  composed PER ROLE (a backend worker → read `backend-engineer.md` + `worker.md` + `RULES.md`; a cicd escalation worker
  → read `cicd.md` + `RULES.md`). No extraction regex, no render, no truncation — the file on disk IS the instruction.
- **Canonical source = the root PM clone where the AO backend runs** (always current — avoids per-slot staleness).
  **Relocate the role/rules files into the PM repo**: agents already read plans/tasks from PM and need no AO files
  unless working an AO plan item, so PM is the natural single home. (Cross-repo move — settle exact PM path + repoint
  `role_registry`/`prompts` during A1 design.)
- **Guardrail: read-from-root, operate-only-in-your-slot.** Reading the canonical files means reading OUTSIDE the slot
  worktree; the stub + RULES.md must state explicitly that reads from root are read-only and the worker WRITES/operates
  ONLY in its assigned `.tabs/<N>/` slot. (Rogue-in-root is low-likelihood — no agent has done it — but the instruction
  must be unambiguous.)
- **Preserve the in-context guarantee** — the paste gave "content is in context" for free; reading does not. Gate the
  existing `/boot` handshake on read-confirmation: a worker cannot proceed to dispatch until it confirms it has read its
  role file + RULES.md.
- **Reconcile the three boot timers.** A spawn-heartbeat watchdog already exists (`SPAWN_HEARTBEAT_TIMEOUT_SECONDS`,
  default 180s → kill+respawn on no `/boot`|`/heartbeat`, 2 retries; `_auth_failover.check_spawn_heartbeat_timeouts`)
  alongside `boot_grace_seconds` (300s, added 2026-07-09). The cutover ADDS boot latency (the worker must `Read` its
  role file + RULES.md before `/boot`), which risks tripping the 180s as a FALSE respawn of an alive-but-slow booter.
  Split the signal — an early lightweight "boot-started" ping for the 180s liveness check vs. the full read-confirmed
  `/boot` as the dispatch gate — and align 180s ↔ 300s.

**Orthogonal (still first-class):** the stale-content fixes (RULES.md tab-branch, main.md path + dead-DAG,
escalation_to) stand regardless — a file that's read directly must still be CORRECT, or agents trip on stale info. They
fold into the role-file rewrite (A4).

## 3. Tasks

### Phase A — Boot mechanism cutover (read-the-file) + stale-content correctness

- [ ] [DESIGN] P0. Design the read-the-file boot mechanism (supersedes any fence fix — no interim). Specify: the
      per-role DYNAMIC STUB (per-session vars + escalation incident vars + per-role read-pointers); the canonical
      location (root PM clone; exact PM-repo path for the relocated role/rules files); the `/boot` read-confirmation
      handshake; the read-from-root/operate-only-in-slot guardrail; AND the boot-timer reconciliation
      (`spawn_heartbeat_timeout` 180s ↔ `boot_grace` 300s ↔ `/boot` read-confirmation — the cutover's Read latency must
      not trip a false spawn-respawn; consider an early "boot-started" ping vs. the full `/boot`). Output: a short
      design note appended here + the file-move list + the module/caller list to refactor.
- [ ] [CODE] P0. Implement the stub + refactor `server/prompts.py` + `server/role_registry.py`: STOP extracting/pasting
      the `text` template; compose a per-role boot stub (dynamic vars + escalation vars + read-pointers). Keep var
      injection. Point `AGENTS_DIR` (or its replacement) at the canonical PM-repo location. Update every spawn caller
      (`autospawn.py`, `tmux_spawn.py`, manual `/api/agents/spawn`, escalation, plan-health dispatch).
- [ ] [CODE] P0. Add the `/boot` read-confirmation gate — a worker cannot proceed to dispatch until it confirms (via
      `/boot`) it has READ its role file + RULES.md. Restores the in-context guarantee the paste gave for free.
- [ ] [CODE] P1. Diagnose-on-boot-timeout + alert-at-cap (`_auth_failover.check_spawn_heartbeat_timeouts`): on
      spawn-heartbeat timeout, CAPTURE the pane (liveness + tail) and classify WHY it hasn't booted (alive-but-slow /
      stuck at a startup prompt / crashed / mid-read) BEFORE the blind respawn; and page the operator when the 2-retry
      cap (`_SPAWN_HEARTBEAT_MAX_RETRIES`) is hit (today it goes silent). Depends on the boot-timer reconciliation (A1).
- [ ] [CODE] P0. Rewrite the role/rules files into STANDALONE readable docs (worker.md, RULES.md, main/review/monitor +
      craft + escalation): dynamic values referenced as "given in your boot message" (no inline `<SLOT_ID>`); keep the
      "NEVER exit on your own / Start now: /boot" semantics but with the client-vs-server idle-loop question RESOLVED
      (operator, 2026-07-10, cost-driven): **MINIMAL/NO client self-poll — DROP the aggressive every-60s client bash
      poll; rely on server-owned liveness** (idle-lingering reclaim reaps idle workers in ~2 min + spawn-on-demand
      within ~60s when work lands). A worker polling an empty queue burns Claude credits for nothing; the server already
      reaps+respawns. Add the explicit "operate ONLY in your assigned `.tabs/<N>/` slot; root reads are read-only"
      guardrail. Relocate to the canonical PM-repo path.
- [ ] [CODE] P1. Stale-content fixes folded into the rewrite (so agents can't trip on stale info): RULES.md tab-branch →
      Path-B (`git clone --reference` on `live-defi-rollout`, no tab branch); main.md backlog path (3×
      `orchestrator/data/config/…` → `data/config/…`); `escalation_to` on `plan-health.md` + `data_pipeline_failure.md`
      (`cicd` → `operator`/`plan-reconciler` + `main`) — verify the dashboard AGENT TYPES panel renders right.
- [ ] [CODE] P2. `main.md` dead Phase -2…14 phase-DAG removal (source epic says "provenance only"; fix the
      `plans/active/` → `plans/epics/` dir error). **[OPERATOR-REVIEW] — main.md is the main orchestrator's brain;
      surface the proposed diff before committing.**
- [ ] [CODE] P2. Doc-drift sweep: `status: draft`→`active` on the 4 wired craft roles (or a `doc_type: agent-role`
      carve-out); remove the deprecated/nonexistent `backup`-role refs in `monitor.md:48,54,185`; refresh the stale
      "server-side TODO" in `WORKER_SPAWN_PREREQUISITES.md:131-209` (Kicker shipped; add the Watchdog); repoint the 5
      archived/dead SSOT footers; fix the "~150/175 lines" RULES.md size claims; SUPERSEDED banner on
      `MAIN_AGENT_CUTOVER_REVIEW.md` + drop the `main.md:108-109` boot-step wiring to it.
- [ ] [CODE] P1. Regression tests for the new mechanism (replaces the old "rendered template contains sentinel" test):
      the boot stub composes per role + resolves the canonical path; role files are placeholder-free in their read-raw
      sections; a spawned worker's `/boot` confirms it read its files. There is no extraction regex left to truncate.

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

### Phase D — Fleet dashboard + slot-state correctness (backend-owned)

_Root cause (2026-07-10, operator screenshot): the FLEET table shows STALE plan/task/context/ping/message for
idle+killed slots, and PLAN ≠ TASK on working slots (slot 7 = deployment task but shows a tradfi plan)._

- [ ] [CODE] P1. Fix the PLAN column derivation (`server/routes/state.py:219-224`): derive `plan_ref` from
      `slot.current_task` (join `TaskRow.task_id == slot.current_task`), NOT `dispatched_to == slot_id LIMIT 1`
      (unordered → picks a stale prior-dispatch task's plan). Guarantees PLAN always matches TASK and clears when idle.
      (Slot-7/8 mismatch = an orphaned tradfi/sports task still carrying `dispatched_to == slot`.)
- [ ] [CODE] P1. Central `reset_slot_worker_state(slot)` helper: clear `current_task`, `last_msg`, `context_used_pct`→0,
      and RELEASE the task's `dispatched_to`; call it from EVERY teardown path (`tmux_pruner`, the watchdog kills at
      `worker_liveness_watchdog.py:1016/1361/1498/1593/1643`, autospawn idle). Today killed/idle slots retain stale
      message/context/ping/plan (grep-confirmed: `last_msg`/`last_ping`/`context_used_pct` are never blanked on kill).
      Non-alive slots then read as blank naturally.
- [ ] [CODE] P1. STATUS column = computed lifecycle PHASE (backend-owned, per "backend populates"): surface the real
      phase — `pre-boot → booting → working → idle/blocked/done/paused/stale/killed` — adding the new
      `pre_boot`/`booting` states (fed by the boot-timer "boot-started" signal from A1). Backend computes the phase; the
      dashboard renders it. (Today the enum is flat: idle/working/dispatched/blocked/done/stale/paused/killed.)
- [ ] [UI] P2. Dashboard belt-and-suspenders (`dashboard/src/layout.tsx`): for non-alive slots (killed /
      idle-no-session) dim/blank CONTEXT · PING · LAST MESSAGE · PLAN · TASK so a dead row can never read as live even
      if a backend field lags. `[UI]` + a `pw:L2` regression spec on the FLEET table.

### Phase C — Verify

- [ ] [VERIFY] P1. Live verification with evidence per fix: a freshly-spawned worker's `/boot` confirms it read its role
      file + RULES.md (in-context), the boot stub carries the correct per-session + escalation vars, and it operates
      only in its slot; no extraction/paste step remains; teardown reap leaves 0 new orphans after a kill;
      `idle_blocker_inferred` / `slot_released_prereq_blocked` / `worker_kick_failed` rates drop in the activity log;
      dashboard escalation_to renders correctly; the FLEET table shows PLAN==TASK on working slots, blank
      context/ping/message on killed+idle slots, and the lifecycle phase in STATUS. Cite `agent-orchestrator@<sha>` +
      `unified-trading-pm@<sha>` (relocated files) + activity-log deltas.

## 4. Codex SSOTs (read before touching each area — plan↔codex drift is review-blocking)

- `codex/12-agent-workflow/agent-orchestrator-overview.md` — worker lifecycle + loops (update for the new boot
  mechanism)
- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — single-VM / role-dispatch (the model
  main.md's dead DAG predates)
- `codex/05-infrastructure/per-tab-worktrees.md` — Path-B clone model (the correct RULES.md text) + commit identity +
  the read-from-root/operate-in-slot guardrail
- `codex/04-architecture/runtime-deployment-topology.md` — central-VM + slots topology
- `../epics/orchestrator_master.md` (parent epic); `ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md`
  (sibling — the task-lifecycle half)

## 5. Progress Log

- **2026-07-10 ~05:40Z** — Plan created from the worker-lifecycle exploration (operator-requested). Four surfaces
  audited (role prompts, runtime loops, activity log, state DB). Runtime confirmed healthy post-2026-07-09-restart
  (autospawn_failed 0, kick_failed ~1.5/hr, 6 boots, queue drained, workers reaped). Headline finding: worker.md fence
  truncation (CRITICAL, ~7 weeks, whole fleet, no test) — independently re-verified via the real `_extract_template`
  (483/536 lines, all 5 boot sentinels absent).
- **2026-07-10 ~06:10Z** — Design pivot (operator): instead of a fence fix, cut over to a READ-THE-FILE boot mechanism
  that removes the copy-paste/truncation class entirely (§2). Inject only per-session + escalation vars; point workers
  at the canonical role/RULES files relocated into the PM repo; guardrail = read-from-root/operate-only-in-slot; gate
  `/boot` on read-confirmation to preserve the in-context guarantee. No interim fence fix. Stale-content correctness
  kept first-class (agents must not trip on stale info). Phase A reworked around the cutover; estimate bumped
  (cross-repo refactor + file relocation + role-file rewrite).
- **2026-07-10 ~06:30Z** — Operator Q on idle-worker economics. Confirmed against live config + state: AutoSpawn is
  already gated on DISPATCHABLE (prereq-met) work (`_has_queued_work`, prereq_blocked_spawn_thrash 2026-06-30) — no work
  ⇒ no spawn (14 idle slots currently `tmux_session=None`, zero idle credit burn). Idle-with-session workers reaped in
  ~2 min (`watchdog_idle_session_ticks=2` × 60s watchdog); boot_grace 300s shields fresh spawns; AutoSpawn wakes a slot
  within ~60s when work lands. Cadences: worker idle-poll 60s, kicker 45s, watchdog 60s, autospawn 60s/300s-cooldown.
  DECISION (cost-driven): the cutover's role-file rewrite keeps the idle-loop SEMANTICS but drops the aggressive
  every-60s client self-poll — server-owned liveness (reap+respawn-on-demand) is cheaper than a worker polling an empty
  queue. Folded into the role-file-rewrite task.
- **2026-07-10 ~06:45Z** — Operator flagged FLEET-table data-correctness (screenshot): PLAN ≠ TASK on working slots
  (slot 7 = deployment task but tradfi plan), and killed/idle slots retain stale plan/context/ping/message. Root-caused:
  (1) PLAN joins `dispatched_to == slot_id LIMIT 1` (unordered) → picks a stale prior-dispatch task, should join
  `current_task`; (2) teardown never blanks `last_msg`/`last_ping`/`context_used_pct` nor always releases the task's
  `dispatched_to`; (3) STATUS is a flat enum with no pre-boot/booting phase. Added **Phase D — fleet dashboard +
  slot-state correctness (backend-owned)**: fix PLAN derivation, a central `reset_slot_worker_state` on every teardown,
  a computed lifecycle-phase STATUS, and a UI blank-dead-rows guard.
