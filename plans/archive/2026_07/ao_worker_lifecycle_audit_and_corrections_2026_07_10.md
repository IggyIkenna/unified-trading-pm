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
status: complete
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
related:
  [
    ../epics/orchestrator_master.md,
    /plans/archive/2026_07/ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md,
  ]
created: 2026-07-10
last_updated: 2026-07-15
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
assigned_role: backend_engineer
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

11. **MED — AutoSpawn spawn-gate BYPASS via the raw-count fallback (reconciled 2026-07-10 audit).** The
    dispatchable-work gate ALREADY EXISTS (`_has_queued_work`, prereq-aware, prereq_blocked_spawn_thrash 2026-06-30) —
    yet slots still got spawned into a 1-blocked-task queue (slot 2 @ 05:04, slot 3 @ 01:03) then reaped. Verified
    mechanism (`autospawn.py:1476-1494`): if EITHER the backlog read OR the prerequisites read throws, the gate passes
    `None` and falls back to the RAW queued count — which counts prereq-BLOCKED tasks as work. With a queue of exactly 1
    blocked task, any transient read failure spawns a worker that parks and gets reaped. Fix = diagnose + harden the
    fallback (make it fail-closed for spawn purposes, or at minimum log loudly when it engages), NOT re-adding a gate
    that exists.

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

### 2.1 A1 design note (2026-07-10, executed)

**Canonical location.** New top-level dir **`unified-trading-pm/agents/`** (15 files: RULES.md + 14 role files; AO
`docs/` stays in AO). Workers + the AO server read the ROOT PM clone at
`/home/ubuntu/unified-trading-system-repos/unified-trading-pm/agents/` (kept current by the FF-pull cron). Server knob:
`ORCHESTRATOR_AGENTS_DIR` (default `<workspace_root>/unified-trading-pm/agents`); `role_registry` keeps parsing
frontmatter (escalation_to → dashboard) from the new path, read-fresh (no restart needed for doc updates). AO `agents/`
copies are DELETED in the same commit as the code cutover (no shims).

**Boot stub** (composed in `prompts.py` as plain Python — no markdown template, no fence extraction, nothing left that
can truncate): identity block (slot, role, server URL, worktree `.tabs/<N>/`, account, model/effort/thinking) + numbered
boot sequence: **STEP 0** — immediately `POST /api/slots/<N>/heartbeat {"message":"boot-started (reading role files)"}`
(the liveness signal; `/heartbeat` sets `last_ping`, satisfying the 180s spawn-heartbeat check — verified: it keys on
`last_ping >= last_spawned`); **STEP 1** — READ (read-only) the canonical files in order: `RULES.md` → base role file
(`worker.md` / `main.md` / …) → craft file if `assigned_role` set; **STEP 2** — `POST /boot` with `read_files: [...]`.
Guardrail line: "root-repo reads are READ-ONLY; ALL work happens in your `.tabs/<N>/` slot." Escalation spawns append
the incident block (dispatch id, wall type, PR, branches) + their role/RULES read-pointers.

**`/boot` read-confirmation.** `BootRequest` gains `read_files: list[str]`; the server checks the role's expected set ⊆
`read_files` → on miss responds **428** with the exact missing paths (self-correcting: the worker reads them and
re-boots) + logs `boot_read_unconfirmed`. Enforcement behind `ORCHESTRATOR_BOOT_READ_CONFIRM` (default ON).

**Boot timers (reconciled).** `spawn_heartbeat_timeout` stays **180s** — cleared by the STEP-0 boot-started ping (<60s),
so the cutover's Read latency cannot false-respawn an alive booter. `boot_grace` stays **300s** — covers CLI start +
reads + `/boot`. New stored status **`booting`** set at spawn, cleared by `/boot` (feeds Phase D; a `pre-boot` sub-state
is not stored — too transient). Boot-started-but-no-`/boot` past boot_grace → the A3 diagnose path.

**Refactor list (verified callers).** `prompts.py` (compose stub; delete `_extract_template`/`_FENCE_RE`),
`role_registry.py` (path + read-fresh), `config.py` (2 knobs), `routes/slots_worker.py` (/boot gate),
`autospawn.py:1073/1075`, `routes/agents.py:93/135`, `server.py:764` (+ `render_worker` craft fix + drop retired
tab-branch var), `main_agent_keeper.py:701`, `tmux_spawn.py` boot-marker check (`_boot_landed` sentinel must match the
stub), tests (`test_prompts.py`, `test_role_registry.py`, spawn-flow tests).

**Rollout order (fleet-safe).** (1) rewritten files land in PM `agents/` (reviewed); (2) AO code cutover + AO `agents/`
deletion in ONE commit, QG-green, quickmerge; (3) ~~FF-pull root AO → WatchFiles reload = deploy~~ **CORRECTED
2026-07-12** (operator ruling, finding 224, verification complete —
`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2): deploy is the pre-existing
`ao-self-pull.sh` 15-min root cron (agent-orchestrator@589b711, 2026-06-01; hardened by `d16d737` stale-process guard +
`5462959` wedge alert) FF-pulling the root AO checkout and `systemctl restart orchestrator`-ing it on HEAD change — the
"WatchFiles reload" framing was wrong, the installed systemd unit runs uvicorn WITHOUT `--reload`; log evidence for the
cron back to 2026-06-16; SSOT already correct at `../epics/orchestrator_master.md:381-386`. The manual ff-pulls narrated
later in this plan's Progress Log (see the 2026-07-10 ~09:40Z/~11:45Z entries, the Phase-A3+B+D ship note, and the
repo-blocker ship note below) were redundant-with, not instead-of, this always-running automation; (4) live-verify one
spawned worker end-to-end (boot-started ping → reads → 428-if-missing → `/boot` 200); main.md cutover for the MAIN agent
is operator-review-gated (A6) and can lag the worker cutover.

## 3. Tasks

### Phase A — Boot mechanism cutover (read-the-file) + stale-content correctness

- [x] 1. ✅ [DESIGN] P0. Design the read-the-file boot mechanism — design note at §2.1 (canonical
      `unified-trading-pm/agents/` + `ORCHESTRATOR_AGENTS_DIR`; Python-composed stub with STEP-0 boot-started heartbeat
      / STEP-1 reads / STEP-2 `/boot`; 428 read-confirmation gate; timers reconciled 180s↔300s + new `booting` status;
      verified caller list + fleet-safe rollout order). Evidence: §2.1 in this plan (PM commit below).
- [x] 2. ✅ [CODE] P0. Implement the stub + refactor `server/prompts.py` + `server/role_registry.py`: STOP
      extracting/pasting the `text` template; compose a per-role boot stub (dynamic vars + escalation vars +
      read-pointers). Keep var injection. Point `AGENTS_DIR` (or its replacement) at the canonical PM-repo location.
      Update EVERY `prompts.render*` call site — verified list (2026-07-10 plan audit; an un-migrated caller HARD-BREAKS
      post-cutover because `_extract_template` raises on a template-less role file): `autospawn.py:1073/1075`
      (autospawn; escalation + plan-health funnel through it), `routes/agents.py:93/135` (manual spawn),
      **`server.py:764` (`spawn_with_account_bg` — the account-failover respawn; MISSED by the original list)**, and
      **`main_agent_keeper.py:701` (main-agent spawn; MISSED)** (was: presented here as added/covered by this cutover —
      **corrected 2026-07-14, finding 194**: `git log -- server/main_agent_keeper.py` shows the file was NOT actually
      touched by this cutover's commits — it kept its pre-cutover `rendered.replace('"role": "main"', ...)`
      agent_id-injection surgery unchanged, which silently broke because that literal substring stopped existing in the
      post-cutover slot-less stub, so the keeper's `_spawn()` returned `False` every tick and main was never actually
      respawned for ~3 days; the real fix landed 2026-07-13 in
      `active/main_agent_spawn_surgery_regression_2026_07_13.md`, agent-orchestrator@43dc13d). (`tmux_spawn.py` is the
      tmux layer — it never renders; mislabel removed.) While touching `server.py:764`, fix two pre-existing defects on
      that path: it calls `render("worker")` not `render_worker(assigned_role, …)` (failover respawns silently LOSE the
      craft-role block today) and passes the RETIRED `branch=tab/<op>/<slot>` var (`server.py:771`) — finding 2's
      staleness, live in code.
- [x] 3. ✅ [CODE] P0. Add the `/boot` read-confirmation gate — a worker cannot proceed to dispatch until it confirms
      (via `/boot`) it has READ its role file + RULES.md. Restores the in-context guarantee the paste gave for free.
- [x] 10. ✅ [CODE] P1. Diagnose-on-boot-timeout + alert-at-cap — agent-orchestrator@3f1d0ef09.
      `_diagnose_unbooted_pane` captures liveness + classification + an 8-line pane tail BEFORE any respawn; an
      actively-WORKING pane skips the kill without burning a retry (`spawn_heartbeat_timeout_pane_working`; the kicker's
      spinner pass refreshes last_ping); the diagnosis rides on every `spawn_heartbeat_retry` event; at the 2-retry cap
      a ONE-TIME latched `spawn_retry_cap_reached` event + `notify_spawn_failed` Slack page fire with the pane tail
      (latch cleared on a post-spawn heartbeat). Tests: test_spawn_heartbeat_liveness.py (6, incl. cap-dedup +
      pane-working-skip + latch-clear; hermetic tmux — a live orch-slot-7 flipped a run mid-QG). A1 boot-timer
      dependency was satisfied 2026-07-10 by the cutover.
- [x] 4. ✅ [CODE] P0. Rewrite the role/rules files into STANDALONE readable docs (worker.md, RULES.md,
      main/review/monitor + craft + escalation): dynamic values referenced as "given in your boot message" (no inline
      `<SLOT_ID>`); keep the "NEVER exit on your own / Start now: /boot" semantics but with the client-vs-server
      idle-loop question RESOLVED (operator, 2026-07-10, cost-driven): **MINIMAL/NO client self-poll — DROP the
      aggressive every-60s client bash poll; rely on server-owned liveness** (idle-lingering reclaim reaps idle workers
      in ~2 min + spawn-on-demand within ~60s when work lands). A worker polling an empty queue burns Claude credits for
      nothing; the server already reaps+respawns. Add the explicit "operate ONLY in your assigned `.tabs/<N>/` slot;
      root reads are read-only" guardrail. Relocate to the canonical PM-repo path.
- [x] 5. ✅ [CODE] P1. Stale-content fixes folded into the rewrite (so agents can't trip on stale info): RULES.md
      tab-branch → Path-B (`git clone --reference` on `live-defi-rollout`, no tab branch); main.md backlog path (3×
      `orchestrator/data/config/…` → `data/config/…`); `escalation_to` on `plan-health.md` + `data_pipeline_failure.md`
      (`cicd` → `operator`/`plan-reconciler` + `main`) — verify the dashboard AGENT TYPES panel renders right.
- [x] 19. ✅ [CODE] P2. `main.md` phase-DAG removal + OPERATOR REVIEW DONE (2026-07-10) — unified-trading-pm@017c03799
      (rewrite) + unified-trading-pm@8fdf17656 (review amendments). The operator reviewed the full old-vs-new diff
      in-session and directed 3 amendments, applied same-day: (1) the DAG's provenance/anti-resurrection note is dropped
      entirely — a fresh main agent derives priorities from active plans; teaching it history it never saw is noise; (2)
      spawning is documented as BACKEND-owned (AutoSpawn + operator dashboard; endpoints in agent-orchestrator
      `docs/SLOTS_AGENTS_AND_FLEET.md`, not the role file) — the "operator's gesture" framing predated AutoSpawn; (3)
      backlog.yaml consistently framed as a DERIVED artifact (`PlanRegenLoop` every 30 min + `POST /api/backlog/regen`
      on demand) — main authors PLAN todos, never yaml; the rewrite had carried over hand-authoring instructions
      ("that's where you author", overnight step 4 author+reload) that contradicted the workspace never-hand-edit HARD
      RULE. Goes live at the next main-agent recycle.
- [x] 18. ✅ [CODE] P2. Doc-drift sweep — split across the two ships: draft→active on the 4 craft roles + backup-role
      refs removed + archived SSOT footers repointed + size claims dropped were all part of the
      unified-trading-pm@017c03799 agents/ rewrite (verified: `rg backup unified-trading-pm/agents/` clean, no
      CUTOVER_REVIEW wiring in the rewritten main.md). agent-orchestrator@3f1d0ef09 finishes it:
      `WORKER_SPAWN_PREREQUISITES.md` Kicker section gets a SHIPPED-historical banner naming the current package layout
      (Kicker + Watchdog + spawn-heartbeat watchdog) and the post-cutover contract drift (no busy-poll, task-less idle
      never kicked); `MAIN_AGENT_CUTOVER_REVIEW.md` gets the 🔴 SUPERSEDED banner (living runbook = PM agents/main.md);
      `/api/spawn/preview` drops the retired `branch=tab/…` var (routes/agents.py:100 — the last live producer of
      finding-2 staleness).
- [x] 6. ✅ [CODE] P1. Regression tests for the new mechanism (replaces the old "rendered template contains sentinel"
      test): the boot stub composes per role + resolves the canonical path; role files are placeholder-free in their
      read-raw sections; a spawned worker's `/boot` confirms it read its files. There is no extraction regex left to
      truncate.

### Phase B — Runtime lifecycle hardening (server code)

- [x] 11. ✅ [CODE] P1. Teardown reaping — agent-orchestrator@3f1d0ef09. `kill_session` now reaps the pane's DESCENDANT
      process tree before `tmux kill-session` (single choke point — every reclaim/prune/respawn caller funnels through
      it): one atomic ps snapshot → strict-descendants BFS from the pane pids → SIGTERM → 0.5s grace → SIGKILL
      survivors; guards = descendants-of-THIS-pane only, never the orchestrator or its ancestor chain, never pid 0/1;
      best-effort (reap failure never blocks the session kill). Tests: test_pane_tree_reap.py (10 — tree math,
      cycle-safety, protected-set, reap-before-kill ordering). ONE-TIME SWEEP DONE (host action, 2026-07-10 ~12:1xZ):
      the 4 known orphans (tm_vm_monitor 12d, understat_monitor 11d, wait_and_reclass 11d, slot-1 gcloud monitor 17d) +
      their sleep children TERM'd and verified gone; scan also found + killed a 5th — a dead slot-3 worker's
      `idle_heartbeat.sh` (2.4d) still curl-POSTing `/api/slots/3/heartbeat` every 60s, i.e. FAKING LIVENESS for the
      current slot-3 occupant; the live tmux server (pid 3988487, retains the first spawn's cmdline) was
      identity-checked and untouched. Post-sweep scan: 0 remaining `.sh` orphans reparented to init.
- [x] 12. ✅ [CODE] P1. Kick-window fix — agent-orchestrator@3f1d0ef09. Both operator-preferred variants, not the
      blanket rule: (1) verification is an attempt-bounded re-poll (5 × 2s ≈ 10s window) instead of one 2s snapshot; (2)
      a heartbeat STATE-DELTA — `last_ping` advancing past its pre-kick value — counts as success even if the spinner
      was missed between polls (fast-turn case); a genuinely ignored kick (no spinner AND no ping advance) still logs
      `worker_kick_failed` + escalates. PLUS the live-confirmed root fix: a task-less IDLE slot is never kicked at all
      (the quiet prompt IS the read-the-file contract — slot 14 was kicked at 11:46:26Z while waiting quietly as
      prescribed); an idle-STATUS slot still holding a task stays kickable; the idle-kick text drops the retired "poll
      /heartbeat for your next task" busy-poll phrasing. Events carry `ping_advanced` + `verify_window_s`. Tests:
      test_worker_liveness.py 35 green (taskless-idle-skip, idle-with-task-kick, ping-advance-success,
      no-advance-failure-escalates).
- [x] 13. ✅ [CODE] P1. Spawn-gate fallback hardening — agent-orchestrator@3f1d0ef09. The raw-count fallback at the old
      autospawn.py:1476-1494 is GONE: a backlog/prereq read failure now fails CLOSED for spawn purposes — the tick skips
      worker spawning only (resume pass + escalation drain unaffected; next tick retries in 60s) and logs a loud
      `spawn_gate_fallback_engaged` activity event (`backlog_read_ok`/`prereqs_read_ok`/`action=fail_closed_skip_tick`).
      The gate is never again consulted with degraded inputs, so prereq-BLOCKED tasks can no longer masquerade as
      spawnable work (the slot-2/3 spawn-into-blocked-queue churn). Test: test_tick_fails_closed_on_gate_read_failure
      (asserts gate not consulted, no spawn, one engaged event).
- [x] 14. ✅ [CODE] P2. `idle_blocker_inferred` dedup — agent-orchestrator@3f1d0ef09. Dedicated per-kicker last-value
      memory `_last_idle_blocker: dict[slot, (summary, ts)]` with log-on-CHANGE-or-hourly semantics; `slot.last_msg`
      keeps being refreshed for the dashboard but heartbeat contention on that shared field no longer re-fires the event
      (the old guard compared against last_msg — `_git_alerts.py:95`). Tests: TestIdleBlockerDedup (fires-once +
      dedups-despite-last_msg-overwrite + hourly still-blocked re-fire).
- [x] 7. ✅ [CODE] P2. `slot_released_prereq_blocked` no-op fix — skip the event when nothing is actually released
      (`held_task is None and not had_session`); collapse the fleet-wide "everything blocked on X" case into ONE
      fleet-level signal instead of a per-slot hourly no-op (`worker_liveness_watchdog.py:1207-1245`).
- [x] 15. ✅ [CODE] P3. Quarantine log-throttle + preserve-path VERIFIED — agent-orchestrator@3f1d0ef09. (a) VERIFIED
      against the live activity log (data/state/state.db, read-only): 525 `autospawn_failed` rows on 2026-07-09 alone,
      ALL `dirty-state quarantined (FM2/FM8)`, last at 15:21:32Z — and ZERO since, so the 2026-07-09 preserve-path fix
      holds (>21h clean). (b) The FM2/FM8 red herring is fixed: the error string now carries `outcome.detail` (the
      resolver's truthful per-repo reason), not just the resolver tag. (c) `autospawn_failed` activity rows are
      throttled per slot with log-on-change-or-hourly semantics (`_last_failure_logged`, re-armed on a clean spawn);
      flap counters + summary counts still record every attempt; the Slack path already had its own dedup. Test:
      test_repeat_spawn_failure_activity_log_throttled. (The plan's "454" figure undercounted: 525.)

### Phase B2 — Blocked-wait lifecycle (added 2026-07-10 PM, operator-directed after the slot-9 incident)

_Incident (2026-07-10 12:03-14:05Z, slot 9 / BLK-61ebf85f): a worker with a staged diff asked an operator-gated
ship-vs-hold question. Main correctly partial-answered ("do the coordination half now; ship-vs-hold awaits operator") —
but the partial answer CLOSED the blocked row (`answered_at` set, slot back to `working`), so NO surface tracked the
still-pending operator half; the operator was chat-pinged once and never re-prompted. The worker then wait-looped ~2h
while the kicker fought it: its pane carried unsubmitted planner text ("check on BLK-61ebf85f again in a bit"), which
classifies FROZEN → "— proceed now" kick → tiny "still waiting, iteration N" turn → re-frozen ~90s later. **55 kicks in
~100 min**, each a full model turn at 55% context. Recurring class per operator._

- [x] [CODE] P1. ✅ DONE (2026-07-15) — agent-orchestrator@f821840 + PM `agents/main.md` — Pending-operator visibility:
      a partial answer must NOT close the pending half. Shipped: `AnswerRequest.disposition` (`final`|`partial`);
      `partial_answer_blocked()` records the interim answer + sets `authority: operator_pending` and LEAVES
      `answered_at` null so the row stays in the blocked queue; `answer_blocked_endpoint` branches on disposition
      (delivers interim guidance + unblocks the worker on partial, logs `blocked_partial_answer`); the operator-gated
      re-alert now covers `operator_pending` rows; `agents/main.md` rubric instructs partial answers to use
      `disposition: partial`, never a plain answer. Tests: `test_blocked_partial_answer.py` (2) + full QG green (1282
      passed). Fixes the invisible 2h wait.
- [ ] [CODE] P2. 🟡 DEFERRED (operator 2026-07-15 → next behavior-drift audit) — (NARROWED 2026-07-10 PM — the
      repo-blocker waiter suppression in todo 20 covers the incident class; remaining scope only) Generic wait-loop kick
      suppression for NON-blocker waits, plus the phantom-frozen `classify_pane` shape: unsubmitted planner text (e.g.
      "check on X again in a bit") left in the input box between turns reads as frozen input today. DEFERRED: a fuzzy
      semantic heuristic on the kill-decision path (highest fleet-brick risk) — the next audit round re-derives the
      actual drift + right-fit before implementing.
- [x] 20. ✅ [CODE] P1. Repo-blocker mechanism — the operator-designed backend-owned resolution of the recurring "agent
      A shipped a commit that turned the repo QG red; agent B can't ship" wait (design principle: depend LEAST on an
      agent relaying the green signal, MOST on the backend). Shipped: `repo_blockers` registry (`RepoBlockerRow`,
      deduped per repo+kind, waiters JSON, green-condition `repo-<repo>-qg-green` flipped false-on-declare /
      true-on-resolve); `POST/GET /api/repo-blockers` + `POST /{id}/resolve` (fixer fast-path); declare auto-fires the
      `ldr_qg_failure` cicd escalation with the declarer's diagnosis as context; `RepoHealthWatcher` daemon (300s, env
      `ORCHESTRATOR_REPO_HEALTH_INTERVAL_SECONDS`, zero-cost while no blocker open) polls `server.ci_status` per unique
      repo and on green resolves + outbox-messages EVERY waiter — no agent relay anywhere on the path; kicker suppresses
      kicks on fresh-ping waiters (slot-9 class: 55 kicks/100min); worker.md § 4b carries the declare-verify-file-wait
      contract (wait-quietly posture, no self-poll; supersedes the separate blocked-wait-contract todo) and cicd.md's
      ldr_qg_failure wall gained the fast-path resolve step. Tests: test_repo_blockers.py (6) + 2 kicker-suppression
      cases. Evidence: agent-orchestrator@b46613d; worker.md §4b + cicd.md fast-path shipped in the same PM commit as
      this flip.

- [ ] [CODE] P2. 🟡 DEFERRED (operator 2026-07-15 → next behavior-drift audit) — `worker_polling_dead` false alarms on
      PRESCRIBED-idle workers (found 2026-07-10 PM, 15 events that day): every event was an IDLE slot (`task=None`,
      queue holding only a prereq-blocked task — "idle: 1 task(s) blocked on footystats-mp-complete") tripping
      health.py's 300s heartbeat-silence alarm. Under the read-the-file contract an idle worker sends ONE final
      heartbeat and waits quietly, so >300s silence is the DESIGNED posture, not death — the alarm predates the
      no-busy-poll cutover. Fix BOTH halves: (a) health.py must not fire polling-dead for a task-less idle slot with a
      live tmux session (that state belongs to the idle reclaim); (b) diagnose WHY those sessions lingered for HOURS
      instead of being reaped by the 2-tick idle reclaim (slots 1/2/3/4 repeatedly re-tripped the alarm 12:33-16:30Z —
      either the reclaim isn't firing, its ticks reset on each alarm/kick, or something respawns idle workers into a
      queue with zero dispatchable work, burning spawn cycles). DIAGNOSIS COMPLETE (2026-07-10 ~16:45Z, slot-2
      timeline): the slots are the ESCALATION/PLAN-HEALTH dispatch pool — 8 escalation + 7 plan-health dispatches landed
      on slot 2 alone 13:05-16:30 (all legitimate: the cicd agents resolved ~10 real ldr_qg_failure walls today, mostly
      1 attempt, resolution=qg_v2_green — the firefighting fleet is HEALTHY). The waste is the AFTERMATH of each
      one-shot: (a) the finished worker's session lingers at the prompt with its own final planner text ("exit cleanly,
      no next task" / "go idle" / "wait for the next dispatch") — the kicker reads that ghost text as FROZEN and burns
      kick-turns on a FINISHED worker; (b) the idle-reclaim's 300s boot-grace plus the 300s polling-dead threshold
      guarantee the FALSE alarm always fires before the reclaim can reap a short-lived one-shot (alarm at silence +300s;
      reclaim earliest at spawn +300s + 2 ticks); (c) at least some kick-escalation respawns boot a GENERIC worker into
      a queue with ZERO dispatchable work (11 slot_boot + 11 boot_read_unconfirmed on slot 2 with no dispatchable task
      all afternoon) — the auto-respawn path does NOT consult the AutoSpawn dispatchable-work gate. Fixes: exempt
      task-less idle+live-session slots from polling_dead/idle_stale (the reclaim owns them); start idle-reclaim ticks
      at IDLE-TRANSITION time, not spawn time, for finished one-shots; gate the kick-escalation respawn on
      `_has_queued_work` (same fail-closed gate as AutoSpawn); teach `classify_pane` the finished-one-shot ghost-text
      shape (same phantom-frozen family as the narrowed suppression todo above — fix together).

### Phase D — Fleet dashboard + slot-state correctness (backend-owned)

_Root cause (2026-07-10, operator screenshot): the FLEET table shows STALE plan/task/context/ping/message for
idle+killed slots, and PLAN ≠ TASK on working slots (slot 7 = deployment task but shows a tradfi plan)._

- [x] 8. ✅ [CODE] P1. Fix the PLAN column derivation (`server/routes/state.py:219-224`): derive `plan_ref` from
      `slot.current_task` (join `TaskRow.task_id == slot.current_task`), NOT `dispatched_to == slot_id LIMIT 1`
      (unordered → picks a stale prior-dispatch task's plan). Guarantees PLAN always matches TASK and clears when idle.
      (Slot-7/8 mismatch = an orphaned tradfi/sports task still carrying `dispatched_to == slot`.)
- [x] 9. ✅ [CODE] P1. Central `reset_slot_worker_state(slot)` helper: clear `current_task`, `last_msg`,
      `context_used_pct`→0, and RELEASE the task's `dispatched_to`; call it from EVERY teardown path (`tmux_pruner`, the
      watchdog kills at `worker_liveness_watchdog.py:1016/1361/1498/1593/1643`, autospawn idle). Today killed/idle slots
      retain stale message/context/ping/plan (grep-confirmed: `last_msg`/`last_ping`/`context_used_pct` are never
      blanked on kill). Non-alive slots then read as blank naturally.
- [x] 16. ✅ [CODE] P1. STATUS = computed lifecycle PHASE — agent-orchestrator@3f1d0ef09. Backend-computed `phase` field
      on SlotView (no stored-enum migration): a LIVE session (tmux_alive) with no post-spawn ping reads `pre_boot`;
      STEP-0's "boot-started (reading role files)" heartbeat message still current reads `booting`; everything else
      mirrors status, terminal states never overridden — derived entirely from the boot contract's own signals
      (last_spawned_at/last_ping ordering + the prescribed STEP-0 message). StatusBadge renders the phase (tooltip shows
      the underlying status). Tests: test_slot_phase.py (6 — incl. stale-pre-spawn-ping and dead-session guards). The
      stored enum stays flat; the operator-visible column now shows
      `pre_boot → booting → working → idle/blocked/paused/stale/killed`.
- [x] 17. ✅ [UI] P2. Dashboard dead-row blanking — agent-orchestrator@3f1d0ef09. `slotRowIsDead()` (killed, or idle
      with neither tmux_alive nor worker_alive) blanks TASK · PLAN · LAST MESSAGE · CONTEXT · PING and dims the row
      (opacity 0.55), so a dead row can never read as live even when a backend field lags; prescribed wait-quietly idle
      (worker still heartbeating) and mid-boot (tmux alive, worker silent) rows are explicitly NOT blanked. Regression
      spec: layout.test.ts `slotRowIsDead` describe-block (5 cases) — this dashboard has NO Playwright harness
      (vitest+tsc only, per its package.json), so the cited regression spec is the vitest suite (84 green) +
      `npm run build` clean; pw:L2 does not exist in this repo's toolchain. `[UI]` gates satisfied: tsc --noEmit clean,
      vitest 84/84, prettier clean, vite build clean.

### Phase C — Verify

- [ ] [VERIFY] P1. 🟡 DEFERRED (operator 2026-07-15 → post-deploy soak, next audit) — Live verification with evidence
      per fix: a freshly-spawned worker's `/boot` confirms it read its role file + RULES.md (in-context), the boot stub
      carries the correct per-session + escalation vars, and it operates only in its slot; no extraction/paste step
      remains; teardown reap leaves 0 new orphans after a kill; `idle_blocker_inferred` / `slot_released_prereq_blocked`
      / `worker_kick_failed` rates drop in the activity log; dashboard escalation_to renders correctly; the FLEET table
      shows PLAN==TASK on working slots, blank context/ping/message on killed+idle slots, and the lifecycle phase in
      STATUS. Cite `agent-orchestrator@<sha>` + `unified-trading-pm@<sha>` (relocated files) + activity-log deltas.

## Final disposition at archival (2026-07-15)

Todo 1 (pending-operator visibility) SHIPPED — agent-orchestrator@f821840 + PM `agents/main.md`, 2 tests + full QG green
(1282 passed); fixes the invisible 2h wait. Todos 2 (phantom-frozen `classify_pane` / generic wait-loop suppression), 3
(`worker_polling_dead` false alarms), and 4 (post-deploy soak VERIFY) are **DEFERRED to the next behavior-drift audit**
(operator 2026-07-15): 2 + 3 are fleet-critical, interdependent, and partly a fuzzy heuristic on the kill-decision path
— rather than guess, the next audit round re-derives the actual drift + right-fit from code/codex before implementing;
4's rate-drop evidence needs a live soak after 2/3 ship. Plan ARCHIVED with these three carried forward.

## 4. Codex SSOTs (read before touching each area — plan↔codex drift is review-blocking)

- `/codex/04-architecture/agent-orchestrator-overview.md` — worker lifecycle + loops (update for the new boot mechanism;
  PATH CORRECTED 2026-07-10 — the plan previously cited a non-existent `12-agent-workflow/` location)
- `/codex/04-architecture/agent-orchestrator-worker-liveness.md` +
  `/codex/12-agent-workflow/local-slot-host-symmetric-worker-model.md` — liveness triggers + the slot/worker model
  (replaces the non-existent `single-vm-architecture.md` cite)
- **[2026-07-12 correction — findings 220/351/225, §A2 B-queue ruling]**
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` NOW EXISTS — created 2026-07-12 by operator
  ruling (`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` `codex-gap` row) as the SSOT for
  dispatch/regen/role-based single-VM topology. The "non-existent" characterization in the two bullets above (was: "the
  plan previously cited a non-existent `12-agent-workflow/` location" / "replaces the non-existent
  `single-vm-architecture.md` cite") was accurate only as of 2026-07-10; as of 2026-07-12 that path is a live, current
  codex-ssot and MAY be cited again alongside `agent-orchestrator-overview.md` +
  `local-slot-host-symmetric-worker-model.md`. Downstream citations of this path in
  `ao_dispatch_correctness_regen_reconcile_2026_07_07.md:265`,
  `ao_task_lifecycle_done_gate_resume_and_slot_identity_2026_07_09.md:153`, and
  `active/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md:26` are now CORRECT and were left unedited (no
  fix needed there).
- `/codex/05-infrastructure/per-tab-worktrees.md` — Path-B clone model (the correct RULES.md text) + commit identity +
  the read-from-root/operate-in-slot guardrail
- `/codex/04-architecture/runtime-deployment-topology.md` — central-VM + slots topology
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
- **2026-07-10 ~07:05Z** — Independent plan audit (second agent) verified every checkable finding against the code
  (reproduced the fence-regex capture to the character) and flagged 2 defects + 1 minor; all re-verified by me and
  AMENDED: (1) the Phase B "spawn-on-demand" task ordered work that already exists — the gate is real
  (`_has_queued_work`, prereq-aware); the actual bug is the RAW-COUNT FALLBACK at `autospawn.py:1476-1494` (backlog/
  prereq read failure → prereq-blocked tasks count as work → the observed slot-2/3 churn). Task rewritten as
  diagnose+harden-the-fallback (fail-closed + loud event); finding 11 reconciled. (2) The A2 caller list missed two
  render call sites that would HARD-BREAK post-cutover (`_extract_template` raises on template-less files):
  `server.py:764` (`spawn_with_account_bg` failover respawn) + `main_agent_keeper.py:701` (main spawn); added, and
  `tmux_spawn.py` removed (tmux layer, never renders). My re-verification also found a BONUS defect on `server.py:764`:
  it renders `render("worker")` (loses the craft-role block on failover respawn) and passes the RETIRED
  `branch=tab/<op>/<slot>` var (`server.py:771`) — folded into A2. (3) Kick-window task reordered to prefer
  settle-lengthening / state-delta over blanket success (blanket would mask a genuinely ignored kick).
- **2026-07-10 ~09:40Z** — **CUTOVER SHIPPED.** PM: 15 rewritten role/RULES files landed at `unified-trading-pm/agents/`
  — `unified-trading-pm@017c03799` (quickmerge, PR #899 auto-merging to main). AO: read-the-file boot mechanism —
  `agent-orchestrator@5eaea2933` (quickmerge, QG green, 1152+ tests): prompts.py = composed stub (no extraction regex
  remains), AGENTS_DIR → sibling PM clone (+ ORCHESTRATOR_AGENTS_DIR), /boot 428 read-confirmation gate
  (ORCHESTRATOR_BOOT_READ_CONFIRM, rejects pre-upsert, logs boot_read_unconfirmed), AO agents/ templates DELETED,
  frontmatter QG repointed at CI-safe tests/fixtures/agents, spawn_with_account_bg craft+tab-branch defects fixed. Phase
  D shipped in same commit: PLAN column from current_task (+ stale-dispatch regression test), reset_slot_worker_state on
  terminal teardowns (done-task-protected), display-blanking on kill sites, prereq-release no-op spam fix. Flipped todos
  2-9. **A6 NOTE (operator review pending):** the rewritten main.md replaces the dead Phase DAG with a plan-driven
  paragraph while PRESERVING the send-keys BAN + account-failover triggers; content is committed but only takes effect
  at the next MAIN-agent recycle — operator can veto/adjust before then (diff: unified-trading-pm@017c03799
  agents/main.md vs agent-orchestrator@041ea00 agents/main.md). Remaining: deploy (ff-pull root AO) + live e2e verify;
  A3 boot-timeout diagnosis; Phase B remainder; Phase D booting-status + UI. [2026-07-12 correction: "deploy" here was a
  manual acceleration of the already-live `ao-self-pull.sh` automation (see §2.1 rollout-order correction above), not a
  manual-restart step that needed doing — the next entry below shows it landing regardless.]
- **2026-07-10 ~11:45Z** — **LIVE E2E VERIFIED (deployed server + real worker).** Deploy: root AO ff-pulled to
  `5eaea29`, WatchFiles reload clean (14 loops supervised, no tracebacks), AO `agents/` gone from disk. [2026-07-12
  correction: "WatchFiles reload" is stale framing — the installed unit runs uvicorn WITHOUT `--reload`; this deploy was
  a manual acceleration of the already-live `ao-self-pull.sh` cron + `systemctl restart orchestrator`, not evidence of
  an autoreload mechanism.] Evidence chain: (1) deployed `/api/spawn/preview` composes the stub with absolute canonical
  PM paths; (2) `/boot` WITHOUT `read_files` → **HTTP 428** with the exact missing list + self-correcting hint
  (`boot_read_unconfirmed` logged); (3) `/boot` WITH `read_files` → **HTTP 200** (basename match); (4) REAL worker
  spawned on slot 14 (`slot_spawned` 11:41:04Z): pre-spawn dirty-state resolver inherited 1 dirty repo (sibling-plan
  preserve path working), worker followed the stub — `/boot` with correct `read_files` FIRST TRY at 11:41:12Z (no 428
  between spawn and boot), then the rewritten worker.md's prescribed final idle heartbeat ("idle, no dispatchable work")
  and waiting quietly — the cost-driven no-busy-poll decision observed live in the pane ("heartbeat and wait quietly
  rather than busy-polling"). Boot-timer interplay confirmed: /boot landed well inside the 180s spawn-heartbeat window.
  **Reap + blank-row (Phase D) verified live 11:50Z:** the idle worker was reaped ~5 min post-spawn (boot-grace 300s
  honored, then idle-lingering reclaim) and slot 14's row read
  `status=idle, current_task=None, last_msg=None, context_pct=0, tmux=None` — the reset_slot_worker_state blank-row
  behavior, observed in production. (Side observation: the kicker kicked the quietly-idle worker at 11:46:26 just before
  reclaim — expected under current tuning; the Phase B kick-window item stays open.)

### 2026-07-10 (slot-16 session, continued) — Phase A3 + B + D hardening shipped in one QG-green batch

**Ship**: `agent-orchestrator@3f1d0ef09` (quickmerge, landed on LDR; strict-quickmerge clean vs 5eaea2933; pytest 1180
passed / 1 skipped, dashboard vitest 84/84, tsc + vite build + prettier clean). Todos 10-18 flipped above with per-item
evidence. Deployed to the root AO clone by ff-pull (WatchFiles reload) immediately after this flip. [2026-07-12
correction: no WatchFiles/`--reload` is installed on the orchestrator unit — this was a manual ff-pull +
`systemctl restart orchestrator`, an acceleration of the already-live `ao-self-pull.sh` cron, which would have picked
the change up within 15 min regardless.]

**Host actions (not in any commit)**:

- Orphan sweep: the 4 known 11-17-day orphan monitors + their sleep children TERM'd + verified gone; found + killed a
  FIFTH orphan the audit missed — a dead slot-3 worker's `idle_heartbeat.sh` (2.4 days old, from scratchpad session
  3bb4d28e) still curl-POSTing `/api/slots/3/heartbeat` with "idle, polling" every 60s, i.e. injecting FAKE liveness
  into whatever occupies slot 3 (would mask a dead worker from the watchdog — exactly the polluted-liveness class the
  ao_task_lifecycle plan fought). Identity-verified every pid via /proc cmdline before TERM; the tmux server (pid
  3988487 — ps shows it under the first spawn's cmdline, easy to misread as an orphan) was verified via
  `tmux display-message '#{pid}'` and untouched.
- Live-DB verification (read-only): 525 `autospawn_failed` on 2026-07-09 (all the generic FM2/FM8 string, confirming
  both the spam volume and the red-herring detail), latest 15:21:32Z, ZERO since → the 2026-07-09 preserve-path fix
  holds; recorded in todo 15.

**Session-learned gotchas**: (1) `_diagnose_unbooted_pane` initially read the HOST's real tmux in tests — a live
`orch-slot-7` spawned mid-QG and flipped the healthy-retry test's pane diagnosis to "working"; every
`check_spawn_heartbeat_timeouts` test now patches `has_session` explicitly (hermetic tmux). (2) The kick-verify loop is
attempt-bounded (5×2s), not wall-clock-deadline — a monotonic deadline under patched `time.sleep` hot-spins in tests.
(3) This dashboard has no Playwright harness; its `[UI]` regression layer is vitest + tsc + vite build (noted in todo 17
in lieu of the plan's pw:L2 ask).

**Still open**: main.md phase-DAG removal ([OPERATOR-REVIEW] — the rewritten main.md at PM@017c03799 already carries the
fix, inert until the next main recycle; veto window open), and Phase C [VERIFY] (needs a ~24h soak for activity-log rate
deltas: `worker_kick_failed`, `idle_blocker_inferred`, `autospawn_failed`, `boot_read_unconfirmed`, plus one observed
teardown with 0 new orphans and a `pre_boot → booting → working` phase transition in the fleet table).

### 2026-07-10 (slot-16, operator-directed) — full boot-prompt drift audit shipped

All 15 `agents/*.md` audited against the DEPLOYED AO code (every endpoint / threshold / mechanism claim verified in
`server/`). Shipped @unified-trading-pm@5020c08e after operator review of the uncommitted diffs: RULES.md + main.md
cited a non-existent `POST /api/conditions/<name>` (real surface: `POST /api/prerequisites/{name}`, which UPSERTS);
RULES.md §4 reframed API-first (conditions never need a YAML edit to exist; parking = tuning a derived entry; the
per-task `prereqs.conditions` attachment documented as the one yaml-only tuning left — regen cannot derive it from plans
yet, candidate future todo); main.md overnight step 4 ordering claim corrected to plan-frontmatter mechanisms
(`depends_on`/`gate_on_depends`, `sequential`/`plan_order`); monitor.md gained the from_role-constraint note (the
`[monitor: <name>]` prefix is the real identity) + a slot-local audit-log path replacing unwritable `/var/log`. Verified
clean with no edits: worker.md, review.md, plan-health, plan-reconciler, cicd, conflict-resolver, data_pipeline_failure,
and all 5 craft files. (Slot-discipline note: from this entry on, ALL PM work happens in the slot-16 clone — earlier
same-day PM commits were made from the root clone, acknowledged as a violation.)

### 2026-07-10 (slot-16, late PM) — slot-9 incident closed live + repo-blocker mechanism shipped

- **Slot-9 resolution (operator decision, delivered via outbox)**: told slot 9 the golden-drift fixes had shipped
  (-002@047df6906/-003@23d53f69/-004@7048ae7e) → it re-ran full QG (green), shipped the slot-3-reconciled S2 diff, and
  /done'd `coinbase_bare_name_migration-002` @ instruments-service@db33ded7. Total limbo: ~2h; root causes recorded in
  the Phase B2 narrative above.
- **Repo-blocker mechanism SHIPPED + DEPLOYED** (todo 20): agent-orchestrator@b46613d (registry + routes +
  RepoHealthWatcher + kicker waiter-suppression; `/api/repo-blockers` verified serving live, watcher zero-cost while
  empty) + unified-trading-pm@b56110c87 (worker.md § 4b contract, cicd.md fast-path resolve, this plan's flip). Root PM
  propagation verified — agents booting from now on read the new contract. [2026-07-12 correction: "DEPLOYED" here was a
  manual acceleration of the already-live `ao-self-pull.sh` cron restart, not a WatchFiles autoreload — same correction
  as §2.1's rollout-order note above.]
- **New finding while verifying**: the `worker_polling_dead` false-alarm class on prescribed-idle workers + the
  lingering-idle-session mystery — filed as the new Phase B2 P2 todo above (investigation notes included there so
  nothing rides on session memory).
- Quickmerge gotcha worth remembering: a `+` inside a conventional-commit scope (`docs(agents+plans):`) fails the
  conventional-pre-commit hook with a misleading "commit failed" — scope must be a plain word.

### 2026-07-14 (slot-16) — stuck-BOOTING phase fix (Phase D follow-up)

Operator observed (recurring): slot 7 showed phase=booting + "boot-started (reading role files)" for 37 min while
visibly working its dispatched task. Root cause: the todo-16 phase inference keys `booting` off `last_msg`, which only
the worker's own /progress updates — a worker that works a long first stint without heartbeating leaves the STEP-0
message on display, and the kicker's spinner pass refreshes `last_ping` without touching the message, masking it. Fix
(agent-orchestrator@4da164c, per the backend-populates principle): `/boot` itself now stamps `last_msg` on EVERY outcome
branch ("booted — starting <task>" / resuming / idle / rate-limited / account-rotating) — the server knows booting ended
the moment it processes the boot; plus a belt-and-braces guard: phase never reads `booting` for a slot holding a
`current_task` (covers pre-fix stale rows). Tests: test_boot_last_msg_stamp.py (3 outcome stamps) + test_slot_phase.py
slot-7 regression case. Deployed via root ff-pull same session. (Side note: the slot-16 AO clone's .venv had vanished
between 07-10 and 07-14 — rebuilt with `uv sync --frozen`; worth watching whether a cleanup sweep is deleting slot
venvs.)
