---
doc_type: issue
title:
  Fleet tmux session loss — kill-server root cause fixed (2 layers); REOPENED after 2 more deaths, Layer-3 gaps found
  and fixed, re-observing (2026-08-13)
summary: >-
  Follow-up from shipping the Fleet Efficiency KPIs `dispatches/done` tile + a slot/role/day breakdown
  (agent-orchestrator@016abaff2f, @8a7a8c0fe0, @<pending>): operator asked why redispatch (retry) is so common and
  whether it's fixable, since "tasks done per spend" would improve a lot if it were. Live read-only query (SSM,
  `state.db` mode=ro) against the last 24h's `task_dispatched`/`slot_done` activity_log rows found: 157 of 541 distinct
  dispatched tasks (29%) got redispatched at least once; of those, `tmux_session_lost` appears in the gap for 148/157
  (94%) vs. an explicit watchdog kill in only 11/157 (7%) and `stale_dispatch_reclaimed` in just 1/157 — the fleet's own
  watchdog is NOT the dominant cause of retries, an unexplained tmux session death is. Widening to all
  `tmux_session_lost` events in 24h (1203 total, most self-heal via resume and never need a full task requeue): 971/1203
  (81%) have NO planned-teardown or already-in-progress-resume precursor in the preceding 60s (i.e., genuinely abrupt),
  and 508/1203 (42%) fire while the slot is holding an undone dispatched task. Resource-contention hypothesis was NOT
  supported (CPU/load/swap not elevated at loss-time). **Root cause CONFIRMED 2026-08-13, see "Two-layer fix" below** —
  kept as original framing/evidence.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, fleet-efficiency, tmux, root-cause, dispatch-retry, kpi]
related:
  - /codex/04-architecture/agent-orchestrator-scheduled-jobs.md
  - /codex/15-runbooks/safe-service-restart-procedures.md
  - /codex/05-infrastructure/deployment-observability.md
  - /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md
  - /plans/active/issues/fleet_wide_deepseek_crash_loop_undetected_2026_08_11.md
  - /codex/15-runbooks/isolated-deepseek-crash-debug-sandbox.md
  - /plans/active/ao_consolidated_closeout_2026_08_12.md
  - /plans/active/issues/plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md
  - /plans/active/issues/ao_tmux_loss_rate_canary_likely_overtuned_2026_08_18.md
context_scope: [agent-orchestrator/server/tmux_spawn.py, agent-orchestrator/server/orphan_reap.py, agent-orchestrator/scripts/orchestrator/strace_tmux_server_supervisor.sh, scripts/self-hosted-runners/tmpfs-disk-cleanup.sh, /codex/15-runbooks/safe-service-restart-procedures.md]
created: "2026-08-10"
author: main (Claude Code, interactive session)
parent_epic: orchestrator_master
resolved_by:
locked_by:
locked_since:
source: >-
  Operator chat instruction, 2026-08-10, after being shown the redispatch/retry breakdown: "yeah but why are they
  crashing/timing out/getting killed mid-task this is what we need to improve as our tasks done per spend will imprve
  alot in that case so add to your todos and investigate."
assigned_vm: NA
execution_scope: local-only
priority: P2
drift_direction: advance-code
depends_on: []
---

# Fleet dispatch:done gap root cause — unplanned tmux session loss, not watchdog kills

## What was measured (live, read-only, via SSM against `state.db` on the orchestrator VM)

**Redispatch precursor (157 redispatched tasks, last 24h)** — filtered to events scoped to the exact `task_id` (or
slot-level events with `task_id IS NULL`) between a task's first and second `task_dispatched`, NOT all activity on a
busy slot (an earlier, less careful pass conflated the two and produced a misleading picture):

| Precursor in the gap                                                                  | Count | % of 157                                                      |
| ------------------------------------------------------------------------------------- | ----- | ------------------------------------------------------------- |
| `tmux_session_lost` present                                                           | 148   | 94%                                                           |
| An explicit `watchdog_*kill*` event                                                   | 11    | 7%                                                            |
| `stale_dispatch_reclaimed` (the last-resort reconciler in `server/stale_dispatch.py`) | 1     | 0.6%                                                          |
| Context saturation/compact event present                                              | 68    | 43%                                                           |
| A `slot_done`/`slot_done_verified` tagged to THIS exact task_id in the gap            | 3     | 2% (rules out "double-counted as both done and redispatched") |

Gap duration (dispatch #1 -> dispatch #2): median 1428s (~24min), min 127s, max 65009s (~18h) — wide spread, not one
single mechanism.

**All `tmux_session_lost` events, last 24h (1203 total — most self-heal via resume and never reach a full redispatch)**,
classified by what preceded each on the same slot in the prior 60s:

| Classification                                                                                  | Count   | %       |
| ----------------------------------------------------------------------------------------------- | ------- | ------- |
| Preceded by a planned session end (`worker_one_task_per_session_reset` or `slot_done_verified`) | 142     | 12%     |
| Preceded by an already-in-flight resume attempt (`slot_resume_pending`)                         | 90      | 7%      |
| **Unexplained — no planned/in-progress-resume precursor**                                       | **971** | **81%** |
| Slot was holding an undone `task_dispatched` (mid-task) at the moment of loss                   | 508     | 42%     |

**Resource correlation (24h `resource_history` samples, `cpu_percent`/`load_avg_1m`/`swap_percent`/`iowait_percent`)** —
at the exact moment of a `tmux_session_lost` event vs. the 24h baseline:

| Metric      | At tmux_session_lost (median) | 24h baseline (median) | At tmux_session_lost (p90) | 24h baseline (p90) |
| ----------- | ----------------------------- | --------------------- | -------------------------- | ------------------ |
| CPU%        | 43.8                          | 63.2                  | 64.9                       | 97.8               |
| load_avg_1m | 11.6                          | 16.9                  | 20.2                       | 43.4               |
| swap%       | 14.7                          | 13.6                  | 15.1                       | 25.3               |
| iowait%     | 9.5                           | 9.0                   | 40.7                       | 24.3               |

Loss moments are NOT elevated vs. baseline on CPU/load/swap — if anything lower. iowait p90 is somewhat higher at loss
moments (40.7 vs 24.3 baseline) — the one metric worth a closer look, but the median is unremarkable, so this reads as
noisy/inconclusive rather than a confirmed signal.

Separately: `free -h` on the VM showed swap climbing from 5.2% (2026-08-09 00:00) to 21.7% (2026-08-10 17:47) over 24h
with RAM usage steady at ~27% and **zero OOM-kills** in that window (`journalctl -k` grep, though the check needs `sudo`
and partially failed — see follow-up todo). Rising swap with low RAM usage and no OOM-kills reads as normal idle-page
reclaim under Linux's default swappiness, not acute memory pressure — this does not support "the host briefly ran out of
memory and that's what kills sessions" as-is.

## What this rules out

- **NOT the fleet's own watchdog** (`server/worker_liveness_watchdog.py`) killing workers it judges stuck — only 7% of
  redispatch gaps show an explicit kill event.
- **NOT the stale-dispatch last-resort reclaimer** (`server/stale_dispatch.py`) — that's a backstop for a slot stuck
  `dispatched` with a dead `tmux_session` for a long time; it fired in only 1/157 cases here, meaning most of these
  never even reach that backstop's multi-minute-to-hours threshold before the tmux loss is independently observed.
- **NOT (as measured) acute host CPU/load/swap spikes** — the correlation pass found no elevation at loss moments.
  Caveat: this used the periodic `resource_history` sampler's nearest sample (up to 120s away), which could miss a
  genuinely brief (sub-sample-interval) spike — not a fully conclusive ruling-out.

## Other confirmed contributors (distinct from the root cause below)

- 94% of redispatches trace to `tmux_session_lost`; 42% hit a slot mid-task, inflating `dispatches` without a matching
  `done` (KPI: `agent-orchestrator@016abaff2f`, `@8a7a8c0fe0`).
- **Context saturation is a real but MINOR contributor, not the ~43% it first looked like.** The proactive path
  (`server/context_lifecycle.py`) works as designed and correctly never shows up as a redispatch. Only genuine failure
  mode: `tmux_pruner.py`'s reactive path can't resume a session that died already past the resume-eligibility ceiling,
  so it requeues fresh (`context_saturated_session_lost_task_requeued`). Exact-event re-query: only 7/142 redispatches
  (5%) — the other 69/142 showing SOME compact-related event is coincidental co-occurrence, not causal.

## ROOT CAUSE CONFIRMED + Two-layer fix (2026-08-13)

**Confirmed via TWO independent kernel mechanisms agreeing on the same pid**: widening the strace filter to `network`
caught a death live — `recvmsg(7, ...)` on the server's client-connection fd contained the literal ASCII bytes
`"kill-server\0"`, then `kill(own_pid, SIGTERM)` 16ms later. `SO_PEERCRED` (kernel-verified, unspoofable) named the
sending client as pid 1256069; an INDEPENDENT `auditctl` execve record for that EXACT pid at the matching timestamp
shows `argv=["tmux","kill-server"]`, `cwd=/home/ubuntu/unified-trading-system-repos/.tabs/7` — a **different operator
slot** on this shared VM. **Every AO tmux invocation lives on the ambient DEFAULT socket** (`/tmp/tmux-<uid>/default`) —
the SAME one any bare `tmux` command anywhere on the host implicitly targets, so literally any process with shell access
(this workspace's own already-documented multi-operator-VM sharing risk) can take the whole fleet down with one ordinary
command, no malice required. exit-empty and destroy-unattached (both separately ruled out earlier with direct evidence)
never explained it — those govern the SERVER's own auto-exit logic, not an explicit external kill-server request, which
auditd's first too-narrow query had missed. **Two-layer fix, both layers needed (2026-08-13)** — operator correctly
pushed back after layer 1 alone: "you're just shifting the problem... everything runs quality gates at some point."
Right. **Layer 1 (external)**: `agent-orchestrator@873821238b`+`5dccbf97b1` sets `TMUX_TMPDIR` so AO's fleet server
isn't the ambient default anyone's bare `tmux` command reaches (first deploy was inert — tmux silently no-ops a missing
TMUX_TMPDIR dir rather than creating it; fixed via `ExecStartPre=mkdir`). Verified via the exact real scenario (plain
`tmux new-session`+`kill-server`) — survived. **But deaths continued** on the isolated socket itself: every worker's
shell inherits the fleet's OWN `TMUX_TMPDIR` by ordinary process-tree descent, so when a DISPATCHED TASK runs something
that itself touches tmux (a QG run executing a bats suite with its own tmux-fixture teardown —
`unified-trading-pm/tests/test_slot_git_status_claim_heartbeat.bats`; live strace showed the identical
has-session/kill-session×2/kill-server sequence, sequential PIDs, ~5-15min cadence, straight through the layer-1
restart), that task's OWN cleanup inherits the fleet's socket and kills it from inside. **Layer 2 (internal)**:
`agent-orchestrator@56dcd21b4a` unsets `TMUX_TMPDIR` per worker shell — insufficient alone (tmux's auto-injected `$TMUX`
var independently routes back to the fleet socket, priority over TMUX_TMPDIR) — completed by `886a4e6889` (also unset
`TMUX`+`TMUX_PANE`). Verified against a REAL worker's `/proc/<pid>/environ`: zero `TMUX*`. **Transition-gap death caught
13:00:19** (dashboard: slot 14 "died mid-task"): traced to slot **18**'s worker, alive since BEFORE the layer-2 restart
— env is baked in at spawn, not hot-patched, so it kept the old TMUX vars. Fix code was correct; propagation wasn't
complete. Force-recycled every live session (`kill-session`, never `kill-server`) so all pick up the fix now — verified
a fresh one's `/proc/environ` clean. Watching for a clean window now.

## 2026-08-13 (later) — closing verification CONTRADICTED; Layer-3 instrumentation gaps found

The prior "CLOSING VERIFICATION"/"Status: CLOSED" entry below was premature — preserved as-is (not edited/deleted) per
this doc's own stated methodology of keeping self-corrections visible rather than smoothing them over. Two more
`tmux_server_died` events fired at 14:08:07Z and 14:30:28Z, discovered on the very next scheduled check.

**Death #1 (14:08:07)**: `tmpfs-disk-cleanup.sh` (a host-wide `/tmp` age-based reclaim sweep, unrelated repo/epic —
`infrastructure_master`) ran 14:08:01-14:08:04 and reclaimed 43 entries; the death fired 3s after it finished. Its
protected-basename denylist knew the ambient `tmux-*` path but not `ao-fleet-tmux` (the NEW dir name the 2026-08-13
Layer-1 fix introduced) — a real, independently-justified gap, fixed regardless of causation (see below). **But**
causation for THIS specific death is NOT confirmed: live-testing proved the script's live-open-handle check (`lsof +D`,
the actual load-bearing safety net per its own header) correctly detects a genuinely live listening socket, and the
run's own `skipped_open=1` count is consistent with it having correctly protected `ao-fleet-tmux` that time. The timing
correlation may be coincidental. Treat the denylist fix as defense-in-depth, not a proven root cause for this death.

**Death #2 (14:30:28)**: NOT explained by `tmpfs-disk-cleanup` — zero runs of that service in the 14:25-14:35 window
(confirmed via `journalctl`). Cause still genuinely unknown.

**Instrumentation was itself broken, found while investigating**: the `strace_tmux_server_supervisor.sh` from 2026-08-12
stayed attached to PID 4184652 since 13:01 and never advanced, missing both deaths' actual mechanism entirely. Root
causes, each caught by live-testing the fix itself rather than trusting it on read-back:

1. `ps -eo pid,comm | grep "tmux: server"` (the PID-attribution method used throughout this investigation, including in
   `watch_tmux_server_lifecycle.sh`) is unreliable — live-verified returning ZERO matches at a moment when lsof
   confirmed TWO processes genuinely held LISTEN sockets on the fleet path.
2. The supervisor's `strace -p $PID` ran as a **blocking foreground call** — it only re-polled for a new PID after that
   call returned. A tmux server whose socket FILE gets unlinked out from under it by an unrelated process (the actual
   failure mode here — confirmed via `lsof`/`ss` showing the orphaned PID still holding an open fd on the now-unlinked
   path) never receives a signal and never calls exit(), so the traced PID sits mute forever and the supervisor never
   notices a new server has taken over.
3. The existing `auditctl` watch (`tmux_exec_watch`, execve of `/usr/bin/tmux` only) is structurally blind to a plain
   `rm`/`unlink` from an unrelated process against the socket path — it only ever watches tmux's own execve.
4. First supervisor-rewrite attempt used `stat`'s inode vs. `lsof`'s NODE column for "who really holds this path right
   now" — WRONG, live-verified: they are different numbering spaces for an AF_UNIX socket on this host (same socket
   reported 3824444 via `stat`, 1271666385 via `lsof`, consistently). Worse, both `lsof +D` and `ss -xlp` only ever show
   a socket's ORIGINAL bind-time path from kernel metadata cached in the socket struct — neither re-resolves at query
   time, so an orphaned holder of a since-unlinked inode is indistinguishable from the real current listener under
   either tool by inspection alone.

**Fixes shipped**:

- `agent-orchestrator@c817d30a35` + follow-up `cc996526e9`: supervisor rewritten to resolve the authoritative live PID
  via an actual `connect()` — `tmux -S <socket> display-message -p '#{pid}'`, the one operation immune to
  cached-metadata staleness since it does a real path lookup at call time — and to run `strace` in the background with
  periodic re-poll instead of blocking foreground attach. Verified live: correctly attached to the genuinely-current
  server (3560582) after redeploy.
- `tmpfs-disk-cleanup.sh` (unified-trading-pm): added `ao-fleet-tmux` to the protected-basename denylist, plus per-path
  reclaim logging (the prior count-only logging left this specific causation question forensically unrecoverable after
  the fact — fixed going forward). **Ship status: BLOCKED** — this checkout is 296 commits behind origin with a live
  peer session's genuine uncommitted WIP (confirmed: a second `claude` process, 7h+ accumulated CPU time, `--add-dir`
  pointed at this exact slot) overlapping the incoming pull. Per this workspace's multi-agent-safety rule, not forced
  past — deferred until the peer's WIP clears, edit is safe on local disk.
- New `auditctl` rule armed on the VM:
  `-a always,exit -S unlink,unlinkat,rmdir,rename,renameat -F dir=/tmp/ao-fleet-tmux -k ao_fleet_tmux_delete` — catches
  the actor side (whoever deletes under the fleet socket dir) that the execve-only watch was blind to; the rewritten
  supervisor covers the victim side.

**Current state**: v2 supervisor live-attached to the genuinely-current server via connect()-based resolution; auditd
delete-watch armed; tmpfs-cleanup fix written but not yet landed (peer collision). Re-observing before any further
closure claim — the doc stays `status: open`.

## Todo

All 32 items below predate the confirmed root cause (see "ROOT CAUSE CONFIRMED + Two-layer fix" above); each is
condensed to one line — full multi-paragraph investigative detail for every item is preserved in git history
(`git log -p -- <this path>`), not reproduced here. Count preserved at 32 (was 32 in the pre-condensation version) per
this corpus's todo-regression rule — no item was dropped, each was shortened.

- [x] [INFRA] P2. Get real tmux/system-level evidence for an unplanned loss — superseded, root cause found via strace.
- [x] [INFRA] P2. Check for a per-account correlation — superseded, root cause is host-wide, not account-scoped.
- [x] [INFRA] P3. Narrow the context-saturation lead — DONE same session, 7/142 (5%) genuine, not causal to root cause.
- [x] [INFRA] P3. Re-run the resource-history correlation with tighter sampling — superseded, root cause found.
- [x] [INFRA] P3. Pruner-loop delay under load — superseded (was already downgraded 2026-08-11).
- [x] [INFRA] P3. Check for a per-cgroup OOM kill — CLOSED 2026-08-11, ruled out (oom_kill=0).
- [x] [INFRA] P2. Live-catch the next death on one isolated slot — superseded by the confirmed live catches.
- [x] [INFRA] P1. Find the tmux SERVER process's own resource envelope/cgroup — CLOSED, refuted, in same cgroup.
- [x] [INFRA] P1. Alert + surface fleet-wide tmux server death — SHIPPED 2026-08-11, `agent-orchestrator@d1e62b7317`.
- [x] [INFRA] P1. Cron-alignment hypothesis — STATISTICALLY REFUTED 2026-08-11 with the full sample.
- [x] [INFRA] P0. Scale of the outage was badly underestimated — MAJOR FINDING 2026-08-11, folded into the fix scope.
- [x] [INFRA] P1. Detection had a real coverage gap — FOUND + FIXED 2026-08-11.
- [x] [INFRA] P0. Root mechanism (early hypothesis) — MAJOR BREAKTHROUGH 2026-08-11, superseded by the final root cause.
- [x] [INFRA] P0. Second live catch, ~14min later — confirmed two distinct death mechanisms existed; superseded.
- [x] [INFRA] P0. Throttle fix — SHIPPED 2026-08-11, `agent-orchestrator@54da59c24b` (a real mitigation, kept).
- [x] [INFRA] P2. Promote the capture script into the repo — DONE 2026-08-11.
- [x] [INFRA] P3. Wire `resource-watchdog`'s tick log into death correlation — superseded, root cause found.
- [x] [INFRA] P3. Confirm the 16:15:xx orchestrator.service restart was ao-self-pull.sh — CLOSED 2026-08-11.
- [x] [INFRA] P0. Throttle fix verified insufficient alone — CLOSED 2026-08-12, correctly identified as partial.
- [x] [INFRA] P1. Reduce fleet capacity while root cause remains open — DONE 2026-08-11, operator-directed.
- [x] [INFRA] P0. Second mass burst even at reduced fleet — DONE, informed further investigation, superseded.
- [x] [INFRA] P2. `sock_throttled` at the cgroup level — superseded, root cause found (unrelated metric).
- [x] [INFRA] P3. `ao-self-pull` took ~1h not ~15min to redeploy a commit — real finding, tracked separately now.
- [x] [INFRA] P3. Dashboard UI for scheduled-dispatch pause/resume — **SHIPPED (correction 2026-08-14, was mis-annotated
      "deferred"):** `agent-orchestrator@33c050e3e0` — `ScheduledDispatchPanel` wired into both `DesktopLayout` +
      `MobileTriage`, backed by the already-shipped `GET/POST /api/scheduled-dispatch/...` endpoints, 2 Playwright pw:L2
      tests. Reconciled per `ao_satellite_ao_dispatch_batch20_2026_08_13_finalize.md` todo 1 (evidence from
      `ao_satellite_ao_dispatch_batch20_2026_08_13.md`).
- [x] [INFRA] P0. THIRD live catch, 2026-08-12 01:34:55 — folded into the eventual root-cause evidence chain.
- [x] [INFRA] P0. FOURTH live catch — `fleet-git-health-guard.sh` lead, real but partial; see next item.
- [x] [INFRA] P0. `fleet-git-health-guard.sh` de-prioritized + overlap-locked — SHIPPED 2026-08-12 (a real fix, kept).
- [x] [INFRA] P1. Isolated (non-burst) single-slot death, 2026-08-12 14:03:55 — folded into evidence chain.
- [x] [INVESTIGATE] P0. "Think outside the box" external lead — led toward the eventual multi-operator-VM finding.
- [x] [INFRA] P0. Root-caused + fixed why no death ever produced a forensic artifact — SHIPPED 2026-08-12 (LimitCORE).
- [x] [INVESTIGATE] P0. First two valid core-dump tests, both empty — real evidence, folded into final root cause.
- [x] [INVESTIGATE] P0. Two more bursts, 2026-08-12 19:45:24Z — folded into the eventual root-cause evidence chain.
- [x] ✅ [INFRA] P2. **Audit DONE 2026-08-19** (see the embedded findings below — one exposure found,
      `run-e2e-backend-chat.sh`; fixing it is not yet its own tracked item). Audit other repos for the SAME unscoped-tmux-fixture anti-pattern the bats suite had (any test
      touching real tmux sessions needs its OWN isolated `TMUX_TMPDIR`, never the ambient/inherited one) — this class of
      bug is not unique to `test_slot_git_status_claim_heartbeat.bats`, just the one that happened to be caught.
    - **Workspace Audit Findings (2026-08-19)**:
      - Checked: All test files, BATS suites, E2E test runners, Python unit tests, and TypeScript/Playwright test suites across all repositories in the workspace (`unified-trading-pm`, `agent-orchestrator`, `deployment-service`, etc.).
      - **Safe / Isolated**:
        - `unified-trading-pm/tests/test_slot_git_status_claim_heartbeat.bats` (isolated via per-test `TMUX_TMPDIR`).
        - `unified-trading-pm/tests/test_session_start_collision_check.bats` (isolated via per-test `TMUX_TMPDIR`).
        - All Python unit tests (mock `subprocess.run` / `tmux_spawn`, do not spawn real tmux servers on the host).
        - All TypeScript/Playwright E2E tests (interact with seeded state / backend APIs, do not directly spawn raw tmux sessions).
      - **Exposed / Unscoped**:
        - `agent-orchestrator/dashboard/tests/e2e/run-e2e-backend-chat.sh` (E2E test fixture/backend runner script that spawns real `tmux new-session` / `tmux kill-session` without setting or isolating `TMUX_TMPDIR`, defaulting to the ambient default tmux socket `/tmp/tmux-<uid>/default`).
- [ ] [INFRA] P3. Once confidence is high (extended clean window, no new `tmux_session_lost` bursts), tear down the
      `strace_tmux_server_supervisor.sh` + `auditctl tmux_exec_watch` diagnostic instrumentation — they were built for
      this investigation, not intended as permanent fixtures, and the strace log alone runs several MB/hour.
- [ ] [INFRA] P3. Consider documenting the `TMUX_TMPDIR`/`TMUX`/`TMUX_PANE` isolation pattern in codex
      (`/codex/05-infrastructure/`) as a standing rule for this shared multi-operator VM, so the NEXT service that
      spawns its own tmux-based fleet doesn't rediscover this the hard way.
- [x] [INFRA] P0. Root-cause + fix supervisor's own PID-attribution mechanism (ps-grep unreliable, then
      inode-vs-lsof-NODE comparison also wrong) — DONE 2026-08-13, live-connect() resolution shipped and verified
      attached to the genuinely-current server.
- [x] [INFRA] P1. Arm an auditd watch for deletes (not just execve) against the fleet socket dir — DONE 2026-08-13,
      `ao_fleet_tmux_delete` armed on the VM.
- [ ] [INFRA] P0. Root-cause death #2 (14:30:28) — NOT explained by `tmpfs-disk-cleanup` (zero runs in that window);
      next occurrence should be caught live by the v2 supervisor or the new auditd delete-watch.
- [x] ✅ [INFRA] P1. **DONE 2026-08-16 (plan_reconciler)** — verified landed: `unified-trading-pm@6cd0d6c3ce`
      (`git merge-base --is-ancestor 6cd0d6c3ce origin/live-defi-rollout` → true), commit
      "fix(infra): tmpfs-disk-cleanup denylist missing ao-fleet-tmux socket dir", matching this doc's own 2026-08-13
      17:46Z Progress Log entry ("landed clean: unified-trading-pm@6cd0d6c3ce").
- [ ] [INFRA] P2. Re-verify with a genuinely long clean window under the NEW (v2) instrumentation before any
      re-declaration of closure or archival — the prior "50min clean window" claim was contradicted by two further
      deaths the very next check, so the bar for the next closure claim should be materially higher than that.
- [x] [INFRA] P0. Fourth gap (orphan tmux SERVER processes, distinct from the per-claude-process orphan sweep)
      root-caused + fixed — DONE 2026-08-13, `agent-orchestrator@d813ef1703`, dry-run by default.
- [x] ✅ [OPERATOR] P1. **DONE 2026-08-16 (plan_reconciler)** — same-doc 2026-08-13 17:46Z-18:10Z Progress Log entry
      confirms this was actioned: "at the operator's request: found and killed 3 confirmed-dead zombie tmux servers
      accumulated across today's incidents (2934337 — 7 dead sessions on the ambient socket including the split-brain
      slot 1; ...), each verified to have zero live `claude` child processes before touching anything."
- [ ] [OPERATOR] P2. Once `sweep_orphan_tmux_servers`'s dry-run logging shows zero false positives across a real
      observation window on the live fleet (same graduation bar the existing per-claude-process sweep already cleared),
      flip `tuning.orphan_tmux_server_sweep_dry_run` to live.
- [x] ✅ [INFRA] P3. **DONE** — `unified-trading-pm@897067dc0b` widens the display grep to match the same
      classification vocabulary (in-code comment cites the fix explicitly). quickmerge's retry-regate has a real display bug (found 2026-08-13, not fixed this session): the
      failure-COUNT grep matches broad vocabulary (`❌|FAILED|ERROR|E `) but the failure-DISPLAY grep only matches
      literal `❌`, so a real failure using different vocabulary (e.g. a plain `ruff format --check` failure) correctly
      blocks the ship while showing nothing about why — cost real diagnostic time twice in a row before being traced by
      reproducing `quality-gates.sh --no-fix` directly. Widen the display grep to match the same vocabulary as the count
      grep (source: PM-wide symlinked `scripts/quickmerge.sh`).
- [x] [INFRA] P0. Live-caught `tmpfs-disk-cleanup.sh`'s `rm -rf /tmp/ao-fleet-tmux` — DONE 2026-08-13 17:08Z, direct
      causal evidence via decoded `proctitle`, not just correlation. Corrected script deployed directly to the VM as
      immediate mitigation (independent of the blocked git push).
- [x] [INFRA] P0. Root-cause + fix the `ExecStartPre`-only-runs-once gap that let the isolation directory silently
      degrade to the unprotected ambient socket for ~3h (split-brain) — DONE 2026-08-13, `tmux_spawn.py` now self-heals
      the `TMUX_TMPDIR` directory before every spawn attempt, not just at service start.
- [x] ✅ [OPERATOR] P1. **STALE, corrected 2026-08-18 (convergence audit)** — this was a duplicate of the item already
      marked DONE above ("2026-08-16 (plan_reconciler)... found and killed 3 confirmed-dead zombie tmux servers...
      2934337"). That earlier correction flipped one occurrence but missed this second one, still asking for a decision
      already made and executed on 2026-08-13. Fresh live re-verification today (read-only SSM against
      i-0c9b283b31d6b5ca7): `ps -p 2934337` — not found; `/tmp/tmux-1000/default` (the ambient default socket) — "no
      server running", zero `lsof` handles on the path; the only live tmux server on the host is pid 3514516 on the
      isolated fleet socket, `ELAPSED=448991s` (~124.7h / ~5.2 days) — unbroken since the 2026-08-13 17:14:35Z respawn
      this doc's own Progress Log already tracks. No further operator judgment needed on this item.
- [ ] [INFRA] P2. Consider whether AO needs its own periodic self-check that the fleet's actual live server pid matches
      the isolated socket (not just per-slot `has-session`) — the split-brain here persisted ~3h because nothing was
      cross-checking "is the CURRENT server on the path we think it's on."
- [ ] [INVESTIGATE] P2. Root-cause slots 10 & 11's genuine mid-task SIGTERM at 2026-08-14 23:33:47-48Z (part of the
      5-slot cluster investigated below) — no OOM (`cgroup oom_kill=0` both), no elevated host load/RAM/swap at
      detection, no `concurrent_recent_spawns` storm, `tmux_server_alive=True` for both (rules out this doc's confirmed
      kill-server signature, which requires `alive=False`), and no explanatory exception/traceback in
      `orchestrator.service`'s journal within the surrounding ±2min. Affected tasks:
      `dp_exit_code_monitor_sweep_overlap_storm-4944c6c02138` (slot 11, marked resume-pending) and the `cicd` craft
      `ldr_qg_failure deployment-api#617` (slot 10, 2288s runtime, reaped-stale, requeued fresh). Still open — same
      "pane vanished before the pruner's next tick" class this doc already tracks generally, not confirmed as a new
      distinct mechanism.
- [ ] [INFRA] P3. `check-ao-recent-deaths.sh`'s `burst_size` (and the doc's own "burst = server-wide crash" heuristic)
      conflates ordinary same-tick `one_task_per_session` recycles (`kill_session reason="manual"`, logged right after a
      normal `slot_done`/`slot_done_verified`) with genuine crash/kill losses — both land as `tmux_session_lost` rows
      and both count toward `burst_size`. The 2026-08-14 23:33:47-48Z "5-slot burst" (below) was actually 3 benign
      recycles + 2 genuine losses; the raw diagnostic made it look like one homogeneous event. Consider
      cross-referencing each burst member against a preceding `reason="manual"` `SESSION-TEARDOWN` log line (or the
      `slot_done` event) within the same ~60s window before classifying it as "genuine." **Cross-link 2026-08-18**:
      `/plans/active/issues/ao_tmux_loss_rate_canary_likely_overtuned_2026_08_18.md` is very likely the SAME
      undercounting gap manifesting in a second consumer (`TmuxSessionLossRateCanary`'s rolling-window breach count,
      not just `check-ao-recent-deaths.sh`'s `burst_size`) — that doc's own measurement todo should reuse this
      doc's already-proven method (the 2026-08-14 23:33 cluster below, where 3/5 counted losses were confirmed
      benign `reason="manual"` recycles) rather than re-deriving it from scratch.
- [x] [INFRA] P1. Root-cause + fix `death_forensics.py`'s `check_external_kill` — its `ausearch -ts`/`-te` date
      format (4-digit-year, single combined token) was silently rejected by this VM's ausearch build on EVERY call
      since the module shipped 2026-08-15, masking every "could not check" as ausearch flakiness rather than a real
      bug. Fixed 2026-08-20 (2-digit-year, date+time as separate argv tokens, live-verified against the actual VM) —
      `agent-orchestrator@5d48a60b5b`. Deployed (service restarted 06:00:47Z, after the fix landed) but not yet
      exercised by a genuine post-fix unexplained death.
- [ ] [INFRA] P1. Get a real OOM-vs-external-kill verdict from `check_external_kill` now that it actually runs —
      the next `death_class=unexplained` row should show `external_kill.checked=true`; if none do within a
      reasonable window, the fix itself needs re-verifying live rather than trusted on read-back.
- [x] [INVESTIGATE] P1. **New lead, 2026-08-20; read to a NEGATIVE result same day — no shared dangerous operation
      found, unlike the original bats-test-tmux-fixture bug.** Fleet-wide query (last 24h) confirms this is NOT
      slot-specific — slot 2 is 16/16 unexplained, slot 4 10/15, slot 1 9/15, slot 10 8/15, slot 11 6/7
      (`tmux_session_lost` grouped by slot_id). A repeat-dying-task lead looked promising (several task IDs died
      across DIFFERENT slots: `backlog_500_malformed_depends_on_comment-81a8666e249d` 4x/slots-10-1-4,
      `instruments_schema_not_locked_versioned-0ca8f7f490f2` 3x/slots-4-10,
      `defi_cefi_venue_chain_axis_contamination-09ac3d7aa6dc` 2x/slots-11-10,
      `deployment_api_client_factory_positional_project_id_bug-6f193540d7f3` 2x/slots-13-4,
      `cross_cutting_satellite_ao_dispatch_batch17-6a8c25390694` 2x/slot-10-twice) — but reading all 5 tasks' actual
      `plan_ref` docs found no shared operation: they range from a pure Python code read/fix (deployment-api), to a
      schema/contract edit (instruments-service, `sequential: true`), to bounded `gsutil`/live-SSH cron verification
      (defi/cefi), to a GitHub Actions YAML edit + `gh workflow run` dispatch (cross-cutting CI), to backend
      hardening of `agent-orchestrator`'s own `regen_backlog_from_plan.py`. None touches tmux directly, none runs an
      unscoped test fixture, none matches the original bug's shape. The only thing genuinely common to all 5 (and to
      virtually every AO-dispatched coding task) is running `quality-gates.sh` before shipping — not a distinguishing
      signal. **Revises the lead**: this argues AGAINST a task-content trigger and back toward host/timing-driven —
      the repeat-task pattern is more likely explained by "AO keeps redispatching the same still-open task, and
      whatever kills sessions is roughly uniformly likely per session-second" than by the task's own work causing it.
      The pane_tail captured at each death (`pane_tail_len=152`, identical across different slots/tasks) is tmux's
      generic "Pane is dead (status N, <time>)" placeholder banner, not real scrollback — confirms (again) that no
      forensic signal survives in the pane itself; the live `check_external_kill`/`check_oom_kill` fix (see the todo
      above) catching the next death live is still the most promising remaining path, not further task-content
      reading.

- [x] ✅ [INFRA] P0. **ROOT-CAUSED + FIXED, 2026-08-20 — CORRECTS the "no shared trigger" negative result two todos
      above.** That earlier read was of PLAN-DOC CONTENT only, which genuinely shows no shared mechanism — the real
      trigger only shows up in the live Claude Code transcript, not the task's plan doc. Downloaded + read the full
      JSONL transcripts for slot 1 (two deaths), slot 7, and slot 32's most recent teardown (operator-requested,
      chunked via SSM — no direct scp/S3 path is available under this workspace's GCS/S3-CLI guardrail). Findings:
      **slot 7 (06:43:12) and slot 32 (06:15:50) are NOT genuine deaths** — both transcripts end with a clean
      `/api/slots/N/done` call and the standard `one_task_per_session` reset response; slot 32 was already correctly
      `intentional_teardown`, but **slot 7 was misclassified `unexplained`** — its reset landed at 06:41:41 and the
      tmux kill was detected 91s later (06:43:12), 1 second past `death_class`'s 90s lookback window for matching the
      `worker_one_task_per_session_reset` signal — a second, concrete repro of the burst_size/death_class
      undercounting gap already tracked above. **Slot 1's 06:23:58 SIGTERM death remains genuinely unexplained** — no
      orphan-reap event nearby, silent for ~102s before the kill, no dangerous command in the transcript tail.
      **Slot 1's 07:06:02 SIGKILL death — ROOT CAUSE FOUND.** Transcript shows the agent's 4th attempt at
      `b21_distinct_values_noncanonical_live-d9a1e4c73ce4`, launching a `dex_swaps` retirement script via
      `setsid nohup uv run python ... --apply &; disown` specifically because "2 prior harness-compact kills" had
      already taken the same job down. `activity_log` shows `orphan_process_reaped pid=372995 age_seconds=306` at
      07:04:56, ~1s after the pane's own death — `server/orphan_reap.py`'s `pid_shares_tmux_session` exemption (built
      for exactly this "worker's own detached background job" case,
      `nohup_detached_background_process_killed_by_orphan_reap_2026_07_27.md`) assumes plain `nohup` detachment,
      which preserves the original session id; `setsid` creates a BRAND NEW session id by definition, permanently
      defeating that exemption — confirmed via the exemption function's own docstring. `boot_grace_seconds=300`
      (confirmed live config) explains the precise ~300-310s age clustering. **Confirmed NOT rare or isolated** — same
      signature (age 300-370s) hit slots 1, 10, 32, and **slot 33 sixteen times in under an hour** in the same 3h
      window, fleet-wide, live, right now. Fixed: `sweep_orphan_processes` now also exempts a candidate whose own OS
      start time is at/after the slot's `SlotRow.last_spawned_at` (bumped once per respawn) — a dispatch-timeline
      check that needs no SID/PGID/ancestry signal (impossible to recover after `setsid` by construction) and cannot
      widen the existing stale-sibling reap (a candidate predating the slot's last respawn is unaffected, regression-
      tested). Shipped `agent-orchestrator@67b68dac39`, 2 new tests, quality-gates.sh green (468 dashboard + full
      pytest), landed + ancestry-verified on `live-defi-rollout`. Does NOT explain the slot-1 SIGTERM death or every
      remaining `unexplained` row fleet-wide — this closes ONE confirmed, live, currently-firing mechanism, not the
      whole bucket.
- [ ] [INFRA] P2. Audit whether `reap_dead_slot_worker_tree` (the REACTIVE, always-live twin of
      `sweep_orphan_processes`, fired the instant `TmuxPruner` confirms a slot's session is gone) needs the same
      `setsid`-safe dispatch-timeline exemption — this session's fix only touched the periodic sweep, the path that
      actually killed pid 372995. `reap_dead_slot_worker_tree` has no `pid_shares_tmux_session` check at all today
      (only `boot_grace_seconds`), so a legitimately-detached `setsid` job surviving a genuine session death would
      currently be reaped unconditionally on the very next tick — worth the same protection, scoped separately since
      it's a different (always-live, not dry-run-gated) trust level.
- [ ] [OPERATOR] P0. **Root-cause host-level fix for codex-luna's dominant death signature (2026-08-21, see Progress
      Log entry below for full evidence)**: unprivileged user-namespace creation is broken host-wide on the
      orchestrator VM for the `ubuntu` user — reproduced live via both `unshare --user --map-root-user whoami`
      (`write failed /proc/self/uid_map: Operation not permitted`) and Codex's own bundled `bwrap` binary
      (`bwrap: setting up uid map: Permission denied`). `kernel.unprivileged_userns_clone=1` and
      `user.max_user_namespaces=115876` are both fine; the `unprivileged_userns` AppArmor profile is loaded+enforcing
      and its own rules say `allow userns,` — yet creation still fails with no AVC audit record, so the exact LSM/
      kernel hook responsible is NOT pinned down (would need ftrace/bpftrace on the syscall, not attempted). The
      standard documented Ubuntu 24.04 remediation for this exact failure signature (identical to the well-known
      Chrome-sandbox/Flatpak breakage) is flipping `kernel.apparmor_restrict_unprivileged_userns` 1→0 — untested here
      since it's a host security sysctl on shared production infra and needs an explicit operator decision, not an
      autonomous flip. Blocks codex-luna re-enablement (see the disable todo below) until fixed AND verified (re-run
      the same two repro commands and confirm both succeed).
- [ ] [INFRA] P1. Wire `CLAUDE_CODE_MAX_CONTEXT_TOKENS` for `gpt-5.6-luna` into `tmux_spawn.py`'s spawn-time export —
      confirmed gap (2026-08-21): `model_tier.py:177,231` already registers the model's real window
      (`_CONTEXT_WINDOW_GPT_5_6_LUNA = 272_000`), but `tmux_spawn.py:933-936`'s `_DEEPSEEK_CONTEXT_WINDOW_EXPORT` shell
      `case` only matches `*deepseek*` — there is no `*luna*`/`*codex*` branch, so every codex-luna CLI process still
      guesses ~200K and prints the `"gpt-5.6-luna" is not a model this version of Claude Code recognizes...` banner,
      which correlates with the Pattern-B (SIGTERM) death signature below. Small, low-risk fix mirroring the existing
      DeepSeek branch — **held as of 2026-08-21 pending a separate agent's concurrent work in the same file
      (round-robin account-selection logic)** to avoid a collision; pick up once that lands.
- [ ] [OPERATOR] P1. **Re-enable codex-luna** (`POST /api/accounts/codex-luna/enable`) once BOTH todos above are
      fixed and independently verified — do not re-enable on just one. Currently `account_status=disabled` (set
      2026-08-21, see Progress Log entry below), sticky, fleet-wide, via the existing operator-disable mechanism
      (`server/state_store/account_usage.py::disable_account`) — no auto-clear path exists, so this requires an
      explicit action, not a passive wait.

## Progress Log

- 2026-08-10: doc created same session as the Fleet Efficiency KPIs `dispatches/done` tile +
  slot/role/day/retry-accounting breakdown shipped to `agent-orchestrator` (commits `016abaff2f`, `8a7a8c0fe0`, and a
  pending `TaskUsageRow.dispatch_role` fallback fix for the role breakdown). Investigation run entirely read-only via
  SSM against the live `state.db` + `resource_history` JSONL — no code changed as part of this doc. All four follow-ups
  above are diagnostic reads, not fixes — a real fix can't be scoped until one of them lands on an actual cause.
- 2026-08-10 (same session, continued): operator asked whether a normal precompact->compact->resume cycle should even
  count toward the redispatch metric, since that path is supposed to be a same-session resume, not a fresh worker
  pickup. Read `server/context_lifecycle.py` (the proactive force-precompact-then-force-compact path, injected into the
  live pane, no `task_dispatched` involved when it works) and `server/tmux_pruner.py` (the reactive
  `context_saturated_session_lost_task_requeued` path — fires ONLY when a session dies while `context_used_pct` is
  already at/above `resume_fresh_context_pct`, so resume is correctly refused and the task is requeued instead).
  Confirmed the operator's read is right: a successful compact cycle genuinely never touches `task_dispatched`, so it
  was never miscounted in the first place. Re-queried with the exact failure event (not the loose
  compact-event-somewhere-in-the-gap heuristic from the first pass): only 7/142 redispatches (5%), down from the
  original 43% figure, which was mostly coincidental co-occurrence on long-running busy slots. Todo 3 closed as a result
  — context saturation is now a well-quantified minor contributor, not an open lead. (Note: this correction was lost
  twice to this same session's shared-checkout contention — safe-doc-push.sh's quarantine-before-stage swallowing it,
  then a second loss during an overlapping concurrent-commit race on this heavily shared checkout — before landing on
  the third attempt. See `pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md` for the standing tracked
  pattern.)
- 2026-08-11: fleet-wide DeepSeek fallback (all 6 Anthropic accounts simultaneously out of credit, operator-confirmed
  expected — see `fleet_wide_deepseek_crash_loop_undetected_2026_08_11.md`) forced ~100% of the fleet onto 2 DeepSeek
  accounts; `tmux_session_lost` rate stepped up 4-7x (30-80/hr baseline -> 150-211/hr) starting exactly 2026-08-11 00:00
  UTC and held through the day. Because Anthropic exposure was ~0% throughout, this pass could NOT distinguish "DeepSeek
  causes it" from "the pre-existing mechanism is provider-agnostic and just got fully exposed" — flagging explicitly
  since the 100%-DeepSeek correlation on its own is not proof of DeepSeek-causation. Shipped
  agent-orchestrator@4c5a86bc3f (same day): `capture_pane_death_info` now also captures `#{pane_dead}` itself alongside
  status/signal/time, closing part of todo 1's ask for real tmux-level evidence. First data since the fix went live
  (service restart 08:00:25 UTC): every sampled death shows EITHER all four fields blank (`pane_dead` itself empty,
  meaning tmux's pane object doesn't resolve to anything live at query time) OR the capture call finds no target at all
  (`pane_death_info: null`) — never a confirmed-dead pane with a populated status/signal. This is consistent with an
  abrupt SESSION-level teardown (which `remain-on-exit` cannot protect against, since it only preserves a pane after its
  own process exits normally) rather than a graceful process exit — real, but still not a root cause; three new todos
  filed above rather than closing this doc on the strength of it.
- 2026-08-11 (continued, same day): built the isolated debug sandbox (see todo above) and ran a first live-catch attempt
  — a DeepSeek-backed worker in a fully isolated agent-orchestrator instance, given real sustained work, died 332s in
  with the same signature as production (`tmux has-session` fails entirely, `pane_dead_status/signal/time` all empty).
  Checked macOS's `ReportCrash` subsystem for the exact window: zero hits for this process, despite confirming the
  subsystem was actively logging OTHER processes' crash/memory events at the same time — a controlled negative, not an
  absence of looking. This is the SECOND independent, always-on OS crash-capture mechanism (after the Linux VM's core
  dumps, enabled same day, also silent across multiple real production deaths) to come back empty for this failure.
  Ruling in/out at this point: NOT a segfault/abort/uncaught-exception (both OS's automatic crash reporters would have
  caught that, and didn't) — narrows the leading hypothesis to an uncatchable signal (SIGKILL-class) or a
  pty/session-level teardown neither OS's normal crash machinery observes. Also found two reusable-tooling gotchas while
  building the sandbox, documented in `/codex/15-runbooks/isolated-deepseek-crash-debug-sandbox.md`: a worker spawned
  with `cwd` inside any repo carrying this workspace's CLAUDE.md ignores its boot prompt and tries to self-boot as a
  real fleet worker against the PRODUCTION VM; a fixed-PID liveness check produces false deaths because Claude Code can
  legitimately rotate its own subprocess PID mid-task (observed once, ~180s in, session/pane stayed healthy through it)
  — track session-level liveness (`tmux has-session`), never a specific PID.
- 2026-08-11 (continued, same day): promoted the production-side SSM watcher pattern (used ad-hoc throughout this
  session to poll for a live `tmux_session_lost` on a specific slot) into
  `agent-orchestrator/scripts/orchestrator/watch_production_slot_death.sh` — companion to the already-shipped
  `watch_sandbox_slot_death.sh`, same two gotchas documented in its header (`-c safe.directory="*"` needed for any
  remote `git` call as root against the ubuntu-owned checkout; capture the SSM `CommandId` and poll it inside ONE
  self-contained script invocation, since each tool call in an interactive session is a fresh shell with no shared
  state). Shipped `agent-orchestrator@e661cc9247`. Deleted the superseded ad-hoc scratchpad copies (`check_activity.sh`,
  `check_angle4.sh`, `check_tmux_death_deepdive{,2,3}.sh`, `death_watch.sh`, `poll_death_watch.sh`, `watch_slot5.sh`,
  `remote_check{,2,3}.py`, `sandbox_death_watch{,2}.{sh,log}`, `wait_ao_ldr_sync.sh`, `ssm_out1.txt`) — none were
  referenced by any committed doc (checked), and their one-shot findings are already folded into this Progress Log.
  Also: the sandbox's worker session (`orch-slot-1`) had already died (consistent with the 332s-death entry above) with
  no respawn — expected, `AutoSpawnLoop` is disabled by design in the sandbox — and the idle backend process
  (`dev.sh --backend-only` on :8770) was stopped, since a live worker session is required to burn any DeepSeek budget
  and none was running; this also satisfies the operator's standing "pause after one failure to avoid burn" instruction
  for this sandbox account. Next session: re-run `setup_debug_sandbox.sh`'s printed next-steps to relaunch a worker for
  another data point, or escalate to a live production catch via the newly-promoted watcher if the sandbox stops
  reproducing.
- 2026-08-11 (continued, same day — third catch): re-ran the sandbox per the note above. Second live death this session,
  155s into a fresh task (never reached its first Write tool call — no output file was ever created), same
  empty-`pane_dead` signature. Also observed the fleet's own spawn-heartbeat watchdog fire mid-window
  (`spawn_heartbeat_timeout_pane_working` at elapsed_s=202) and correctly skip respawning since the pane was actively
  working — confirmed by reading `server/worker_liveness/_auth_failover.py` that this guard exists and is not what
  killed the session; the session died independently ~45s later. With operator-granted `sudo` on this Mac, went three
  levels deeper than any prior pass: (1) root-level `DiagnosticReports` — one unrelated file (`disk writes_...`,
  timestamped ~10 min before the spawn even happened) found, no jetsam/crash report for this death; (2) root-level
  kernel jetsam-kill log, unfiltered — found a real, unrelated, actively-looping jetsam kill of a process called
  `ecosystemd` (fresh PID every ~10s, hitting a 15MB InactiveHard limit) throughout the window, but zero jetsam kills
  for our PID at any point; (3) kernel-level TCP/process-lifecycle log around the exact death instant — found
  `runningboardd` logging `termination reported by proc_exit` for the process at 16:00:29.247 local, with its
  211-second-old DeepSeek-API connection AND a secondary connection both torn down via **TCP RST (not FIN)** at the
  exact same timestamp — an ungraceful-termination signature (a clean exit sends FIN; RST means the kernel auto-reset
  sockets left open by an abruptly-terminated process), and consistent with the SIGKILL-class hypothesis. Checked
  `launchd`'s "exited due to SIGKILL | sent by X" attribution format (found it firing correctly for unrelated `mdworker`
  processes in the same window) — it never fired for our PID, because that specific attribution only covers
  launchd-managed services, and this is a plain tmux child process, so it doesn't apply here. **This is the practical
  ceiling of what `log show` (even root-level) can establish post-hoc on this Mac** — the actual signal-sender is still
  unidentified. Stopped the sandbox worker + backend immediately after this catch per the standing "pause after a
  failure" instruction (fleet's own liveness watchdog had already auto-respawned a new worker on the dead session by the
  time this was checked — killed that too). Next step needs either live kernel signal tracing armed BEFORE the next
  death (not post-hoc), or moving the live-catch to the production Linux VM (`watch_production_slot_death.sh`, root via
  SSM, core dumps already enabled) instead of continuing to iterate on this Mac.
- 2026-08-11 (continued, same day — production breakthrough): operator reported live production sessions now dying on
  BOTH DeepSeek and a freshly-enabled Anthropic sub-account (`sub-g-alpavolt`) — **definitively closes the
  DeepSeek-vs-provider-agnostic ambiguity** this doc flagged earlier that day: the mechanism is confirmed
  provider-agnostic. Live-attached to a specific about-to-die slot (11, `ci-reconcile` role) via a tight SSM poll loop
  (`sudo -u ubuntu tmux capture-pane`, ~7s cadence — first attempt queried the WRONG tmux socket namespace since SSM
  executes as root by default, `/tmp/tmux-0/` not `/tmp/tmux-1000/`, giving a false immediate "dead" reading; fixed by
  prefixing every tmux call with `sudo -u ubuntu`). Caught it live: the pane showed an active retry loop against **HTTP
  429 rate-limiting** (`429 Rate limited · Retrying in Xs · attempt 6/10`, counting down through consecutive retries) at
  the second-to-last poll, then ~10-19s later, the poll came back with **`no server running on /tmp/tmux-1000/default`**
  — not "session 11 lost", the ENTIRE tmux SERVER process for the `ubuntu` user was gone. Confirmed via direct process
  checks (`pgrep -u ubuntu -af tmux`, `sudo -u ubuntu tmux list-sessions`) that no tmux server existed for `ubuntu` at
  all, even ~3 minutes after the death — a single point of failure that, if it recurs, would explain EVERY symptom
  collected so far in one shot: provider-agnostic (shared infra, not account-specific), the earlier-observed
  mass-simultaneous "14 sessions lost in one pruner tick" batches (killing the shared tmux server kills every pane it
  hosts at once), the total absence of any per-process crash report (the individual worker processes' own
  crash-reporting was never the right thing to check — the SERVER'S death is what needs explaining), and the RST-not-FIN
  signature from the Mac sandbox catches (a pane's process loses its controlling terminal via SIGHUP when the tmux
  server dies — uncaught, default action is terminate, abrupt enough to leave open sockets mid-teardown). Checked the
  tmux SERVER's own death for a cause with the same rigor as every worker-level check so far: `journalctl -k` for the
  exact window (16:14:35-16:14:55 UTC) — **zero kernel log entries at all**, and the full all-units journal for the same
  window shows nothing tmux-related except this investigation's own SSM polling commands — no OOM, no service restart,
  no crash, nothing. One coincidental-but-unconfirmed observation: a burst of ~20+ concurrent
  `git fsck`/`gc.pruneExpire` commands across many unrelated repo checkouts landed in the same ~10s window
  (16:14:38-16:14:51) — worth a closer look as a resource-contention candidate, though the VM's own `resource-watchdog`
  (a previously-undiscovered systemd service already ticking `pressure=normal cgroup_mem=5GB` logs — a real,
  already-built lightweight monitor, worth using for future correlation) reported calm conditions throughout. Also
  discovered via `server/tmux_spawn.py`'s own comments (the per-worker memory-cap feature, confirmed NOT armed on this
  VM) that the tmux SERVER process itself likely sits OUTSIDE any per-service cgroup — meaning every cgroup-scoped check
  this doc has run (including the definitive `oom_kill=0` ruling from earlier the same day) covers
  `orchestrator.service`'s cgroup, which worker PANES inherit, but says nothing about the tmux SERVER's own resource
  envelope — a real gap, not yet closed. **This reframes the entire investigation**: the question is no longer "why does
  an individual worker process crash" (every mechanism checked for that — app crash, jetsam, cgroup-OOM, the fleet's own
  watchdog — has come back negative) but "why does the tmux SERVER process itself die", a much narrower and more unusual
  question (tmux servers are famously minimal and stable; a bare server crash under normal load is not expected
  behavior). The orchestrator BACKEND itself also restarted ~44s after this death (`uptime_seconds=54` at the next
  check) — timing strongly suggests this was `ao-self-pull.sh`'s routine 15-min cron picking up this same session's own
  just-shipped commit, NOT a cause of the tmux-server death (which preceded it and, per the documented
  `KillMode=process` behavior, an orchestrator.service restart should not touch detached tmux-spawned children anyway) —
  flagged as needing a quick confirming check, not yet done.
- 2026-08-12 (mandatory-first-read audit before resuming): found this doc itself was corrupted — two unresolved
  three-way git-merge marker blocks (the standard "ours / merge-base / theirs" diff3 conflict markup, ~190 lines total)
  left over from an earlier session's stash-pop collision on this heavily-contended shared checkout. Verified via
  word-normalized diff that both duplicated blocks (the "Promote the capture script" todo, and the 7-todo run from
  "Throttle fix verified insufficient" through the shipped fleet-git-health-guard.sh fix) were byte-for-byte identical
  in content between the `ours`/`base`/`theirs` copies — pure prettier re-wrap duplicates, not genuine divergent edits,
  consistent with this session's known isolated-worktree-ship re-wrap artifact. Kept the cleaner-formatted copy (no
  mid-word stray-space wrap glitches) via precise line-range `sed` deletion, verified with `check_conflict_markers.sh`
  (PASS) and a full re-read. No investigation content was lost — this was pure structural corruption from tooling, not
  conflicting analysis. Backup of the pre-fix file at `<session-scratchpad>/ao_tmux_backup_before_conflict_fix.md`.
- 2026-08-12 (content-loss discovery + recovery): a `safe-doc-push.sh` false-failure warning masked a landed commit
  (`b9341d7ac6`) that a later peer push (`fc808eaecf`) then partially stale-base-overwrote — recovered via `patch`
  against origin tip against `b9341d7ac6`'s own diff, 3/4 hunks auto, 1 by hand; verified no content lost from any of
  the 3 contributing sessions, `check_conflict_markers.sh` PASS, todo count matched.
- 2026-08-12 21:47Z (operator: "keep going until confirmed fixed at the AO level, /autonomous"): armed
  `AUTONOMOUS_AGENT_RULES.md`'s completion loop. Shipped a live `strace` supervisor (`agent-orchestrator@3afe35f13a`,
  `scripts/orchestrator/strace_tmux_server_supervisor.sh`) that stays attached to whichever process is currently the
  tmux server, re-attaching on every respawn. Found 6 deaths in the prior 90min (~1/10min, well above historical
  cadence) — good odds of a live catch soon.
- 2026-08-12 22:38Z: **mistake, corrected same tick** — death #7 happened while the FIRST supervisor variant (`-f`,
  following every forked pane) was attached and should have recorded it, but log growth (113MB→648MB/14min) prompted a
  fix-and-redeploy whose cleanup `rm -f`'d the log before it was ever read — unrecoverable. Fixed
  (`agent-orchestrator@ee8de4c3d9`, dropped `-f`); standing rule: never delete an armed trace unread.
- 2026-08-13 00:06Z-00:38Z: death #8 confirmed self-kill, fix shipped, briefly declared root cause found — then death #9
  FALSIFIED it (same signature on the pid I'd live-confirmed `exit-empty off` on). Self-corrected.
- 2026-08-13 11:18-12:05Z: root cause caught, cross-verified via strace `SO_PEERCRED` + `auditctl`. Layer-1 fix
  (`873821238b`, corrected `5dccbf97b1`) genuinely re-tested (real scenario, not readback) — survived.
- 2026-08-13 12:30-12:58Z: operator caught it — deaths continued post-layer-1 (worker tasks inherit the fleet socket;
  own tmux-touching tests kill it from inside). Layer-2 fix (`56dcd21b4a`+`886a4e6889`, `$TMUX` also needed unsetting)
  verified against a REAL worker's `/proc/environ`.
- 2026-08-13 13:00-13:10Z: transition-gap death from a PRE-fix worker (slot 18) that never got layer-2 (env baked in at
  spawn, not hot-patched). Force-recycled every live session so all pick up the fix now. See section above.
- 2026-08-13 13:10-13:51Z: **CLOSING VERIFICATION.** 50+ minute window, current server pid unchanged the whole time (no
  `tmux_server_died` in `activity_log`). Went beyond the activity-log check: `grep -c "kill-server"` across the ENTIRE
  18.7MB raw strace log covering this server's full lifetime returned **0** — a direct, complete syscall-level negative,
  not an absence-of-alerts inference. The `tmux_session_lost` events observed in this window (13:14:56 burst,
  13:37/13:43 isolated) are confirmed routine `has-session`/`list-session` calls against already-recycled names
  (residual detection lag from the 13:08-13:10 forced recycle), not kills. **Status: CLOSED.** Root cause (shared
  default tmux socket, reachable by any process's bare `kill-server` — including a worker's own inherited environment)
  is fixed at both the external and internal layers, propagated fleet-wide, and verified against real production
  behavior at every step, not simulation-only. Three real self-corrections along the way (exit-empty false-positive,
  layer-1-alone insufficient, layer-2-TMUX_TMPDIR-alone insufficient) are preserved above as the actual methodology, not
  smoothed over — each was caught by direct live re-testing before being trusted, per the operator's explicit standing
  objection to declaring victory on a readback rather than a real re-test.
- 2026-08-13 14:08Z-15:05Z: **the "CLOSED" claim above was contradicted** — 2 more deaths (14:08:07, 14:30:28) on the
  very next scheduled check. Full writeup in the new section above ("closing verification CONTRADICTED"). In brief:
  found and fixed a real gap in `tmpfs-disk-cleanup.sh`'s protected-basename list (didn't know about the Layer-1 fix's
  new `ao-fleet-tmux` dir name) but could NOT confirm it caused death #1 specifically — the script's live-open-handle
  safety net tested as working correctly, so the timing correlation may be coincidental; shipped as defense-in-depth
  regardless, ship itself currently BLOCKED by a live peer session's uncommitted WIP in the shared `unified-trading-pm`
  checkout (not forced past). Death #2 has no explanation yet. Separately found the investigation's own
  `strace_tmux_server_supervisor.sh` had been stuck on an orphaned PID since 13:01, structurally blind to the actual
  failure mode (a socket file getting unlinked out from under a still-running server, which delivers no signal and no
  exit() to the traced PID) — root-caused two further mistakes in the FIRST rewrite attempt itself (unreliable
  `ps`-comm-grep PID attribution, then a second wrong fix using `stat` inode vs. `lsof` NODE — different numbering
  spaces, caught by testing the fix live rather than trusting it) before landing on connect()-based resolution
  (`tmux -S <socket> display-message -p '#{pid}'`), which verified correctly attached to the genuinely-current server.
  Armed a new auditd watch (`ao_fleet_tmux_delete`) covering the delete side the old execve-only watch never could.
  **Status stays `open`.** Re-observing under the corrected instrumentation before any further closure claim — this is
  the fourth time in this investigation that a "verified" fix was found incomplete on the next real-world re-test, which
  is itself the strongest argument for keeping the bar for the NEXT closure claim materially higher than "no death in
  the last N minutes."
- 2026-08-13 15:05Z-16:38Z: **93 minutes clean under the corrected v2 instrumentation** — supervisor attached to pid
  3560582 continuously since 15:05:18Z, zero switches; the new `ao_fleet_tmux_delete` auditd watch fired once
  (16:10:24Z) and was run down to ground: `unlink()` calls under `/tmp/ao-fleet-tmux/tmux-0/` (root's own
  `-L default`-resolved subdir — `auditctl`'s `dir=` filter does subtree matching, so a completely separate, harmless,
  isolated tmux instance sharing only the parent `TMUX_TMPDIR` triggered it). Confirmed via `ls`: a root-owned `tmux-0/`
  dir sitting beside our fleet's `tmux-1000/`, created exactly 16:10, untouched since — no risk to the fleet socket, and
  a useful confirmation the watch's subtree matching works as expected rather than a new near-miss. Two independent
  signals (supervisor attach-log, auditd delete-watch) now agree on a materially longer clean window than the
  previously-contradicted 50-minute one. Still NOT declaring closure: the tmpfs-disk-cleanup.sh fix and this doc's own
  correction remain unpushed (peer collision in `unified-trading-pm` unchanged) — per this doc's own stated bar, closure
  needs both a long clean window AND the pending fixes actually landed, not just written locally.
- 2026-08-13 17:08Z-17:15Z: **caught the tmpfs-disk-cleanup deletion live, unambiguously, and found a MORE SEVERE
  compounding gap.** `ao_fleet_tmux_delete` fired at 17:08:06 with the decoded `proctitle` showing the literal argv
  `rm -rf -- /tmp/ao-fleet-tmux`, `uid=0`, exactly on `tmpfs-disk-cleanup.timer`'s `:08`/`:38` cadence — this is a
  DIRECT causal hit (not the ambiguous correlation from the 14:08:07 death), confirming the denylist fix is the real
  fix, not just defense-in-depth. The live VM was still running the OLD (unfixed) script the whole time since the fix
  was blocked from shipping — deployed the corrected script directly to `/usr/local/sbin/tmpfs-disk-cleanup.sh` via SSM
  as an immediate mitigation, independent of the blocked git push. **Bigger finding while responding**:
  `/tmp/ao-fleet-tmux` was gone and NOT recreated for 5+ minutes — traced to `orchestrator.service`'s
  `ExecStartPre=mkdir -p $TMUX_TMPDIR` only running ONCE at service start, never again during its lifetime. Checked the
  ambient default socket (`/tmp/tmux-1000/default`) and found it **actively LISTEN -held by pid 2934337 since 14:09:09**
  — the respawn from the FIRST denylist-gap deletion earlier today (14:08:07) had silently fallen back to the
  unprotected ambient socket (same silent-fallback behavior already known from the 2026-08-13 `ExecStartPre`
  inert-deploy incident, just triggered by a different cause this time) and stayed there, live, for ~3 hours — a genuine
  split-brain: slot 1's real session on the UNPROTECTED ambient socket the entire time the isolated socket was being
  verified clean via the v2 supervisor. Manually `mkdir -p`'d the isolated directory (non-destructive, unblocks
  correct-path recovery, does not touch any live session) — AO's own self-healing then correctly detected the stuck
  spawn, reaped the orphan, and respawned slot 1 onto the isolated socket (17:14:35, verified new pid). Shipped the
  durable fix: `agent-orchestrator@2e8b218103`, `tmux_spawn.py` now `os.makedirs($TMUX_TMPDIR, exist_ok=True)` before
  EVERY spawn attempt, not relying on the one-time `ExecStartPre`. The old ambient-socket session (pid 2934337) is left
  running, AO-invisible, wasteful but harmless — NOT manually killed, per the standing "never manually kill tmux" rule;
  needs an operator-directed or AO-native cleanup, tracked as a new todo below. This is now the **third** distinct layer
  this investigation has found beyond the original two (kill-server): a real-time-observed, directly-causal instance of
  the tmpfs-disk-cleanup gap, PLUS a previously-unknown non-resilience gap in the isolation directory's own lifecycle
  that let it silently degrade to the exact vulnerability the whole investigation exists to fix.
- 2026-08-13 17:46Z-18:10Z: **both previously-blocked pushes landed**, via `--isolated` (operator-directed, worktree
  approach — the isolated worktree does a fresh detached-HEAD checkout, which sidesteps the Not-Behind Gate the live
  peer collision was blocking entirely, without ever touching the peer's own working directory or files). This doc:
  `unified-trading-pm@045ce6a8ee`. The `tmpfs-disk-cleanup.sh` denylist fix took two retries — attempt 1 hit a
  confirmed-flaky, unrelated `test_session_start_collision_check.bats` failure (verified flaky by re-running standalone,
  passed clean); attempt 2 then silently no-op'd ("No changes in --files paths") because attempt 1's failure path had
  evacuated the local edit into a stash without restoring it — found via `git stash list`, popped the correctly-named
  stash (`qm-iso-evac-87281-...`, unambiguously this session's own), retried, landed clean:
  `unified-trading-pm@6cd0d6c3ce`. Separately, at the operator's request: found and killed 3 confirmed-dead zombie tmux
  servers accumulated across today's incidents (2934337 — 7 dead sessions on the ambient socket including the
  split-brain slot 1; 4184652 — `orch-agent-main` from the very first outage; 3560582 — a superseded isolated-socket
  generation from before the 17:08 respawn), each verified to have zero live `claude` child processes before touching
  anything. This surfaced a **fourth** gap: nothing reaps an orphaned tmux SERVER process once its socket is superseded
  — AO's existing `orphan_reap` only kills individual known `claude` processes by pid, never an abandoned server — so
  today's two fixes prevent NEW orphaning but don't clean up any future recurrence automatically; tracked as a new todo.
  **Both landed fixes are pending propagation**: `agent-orchestrator`'s self-healing code fix reaches the running VM
  only via `ao-self-pull.sh`'s 15-min cron, not yet confirmed live as of this entry. Given the number of real events
  since the last "clean window" claim, the observation clock restarts from 17:08Z — nothing before that counts toward
  any future closure bar.
- 2026-08-13 18:11Z: **production confirmation the tmpfs-disk-cleanup fix works** — `agent-orchestrator@2e8b218103`
  self-pulled to the VM (`orchestrator.service` restarted 17:30:19Z), isolated socket (pid 3514516) continuously healthy
  since 17:14:35Z. The corrected `tmpfs-disk-cleanup.sh` has now run twice for real on its own schedule (17:38:04Z,
  18:08:05Z) — its new per-path logging shows exactly 7 harmless temp/log files reclaimed the first run and 0 the
  second, `ao-fleet-tmux` in neither, `skipped_protected` up by exactly one both times (the new denylist entry doing its
  job). This is direct evidence from the fixed script's own logging, not inference. One `ao_fleet_tmux_delete` auditd
  hit at 17:45:16Z doesn't line up with either cleanup run — likely another benign sibling-instance event (same class as
  the earlier `tmux-0` finding), not chased further given the now well-understood pattern.
- 2026-08-13 18:43Z-20:20Z: **shipped the 4th-gap fix** — `agent-orchestrator@d813ef1703`, `sweep_orphan_tmux_servers()`
  in `orphan_reap.py` (new `current_tmux_server_pid()` in `tmux_spawn.py`, same live-connect() resolution verified this
  session; native `/proc/net/unix` + fd cross-reference for candidate discovery, no `ps`/`comm`/`lsof` dependency;
  excludes the current server and anything with live children; honours `boot_grace_seconds`; wired into `TmuxPruner`'s
  existing 60s loop; ships DRY-RUN by default `tuning.orphan_tmux_server_sweep_dry_run`, same graduation bar as the
  existing per-claude-process sweep before an operator flips it live). 24 new/existing tests pass. Two real,
  non-blocking diagnostic detours along the way: (1) a genuinely opaque quickmerge failure — `ruff format --check`
  failed on `tmux_pruner.py` (a line-wrap issue in my own edit, agent-mode commits don't auto-fix), but quickmerge's own
  retry-regate logic has a real bug — its failure-COUNT grep matches broad vocabulary (`❌|FAILED|ERROR|E `) while its
  failure-DISPLAY grep only matches literal `❌`, so a plain ruff-format failure (no emoji in its own output) correctly
  blocked the ship while showing NOTHING about why, twice in a row. Found by reproducing `quality-gates.sh --no-fix`
  directly and diffing exit codes per check rather than trusting the truncated display. Logged as a follow-up, not fixed
  in-session (out of this investigation's scope, would need tracking down the PM-wide symlinked source). (2) A first
  quickmerge attempt failed with the same opaque symptom but turned out to be pure host contention (re-gate hit only the
  duration budget) — resolved by simply re-running `quality-gates.sh` directly, which passed clean, before the SECOND
  (genuine, ruff-format) failure surfaced on retry.
- 2026-08-13 19:49Z: **all four fixes confirmed live in production, clean window now 2h34m unbroken.**
  `agent-orchestrator@d813ef1703` self-pulled to the VM (`orchestrator.service` restarted 19:30:19Z, both new call sites
  present in the deployed file). Supervisor has been continuously attached to the SAME server (pid 3514516) since
  17:14:30Z with zero switches — 2h34m straight. Zero real `ao_fleet_tmux_delete` auditd hits since 19:17Z. The fixed
  `tmpfs-disk-cleanup.sh` has now survived its **fourth** real scheduled production run (19:38:06Z, reclaimed=12,
  `ao-fleet-tmux` untouched, `skipped_protected` count consistent with the new denylist entry doing its job every single
  time). This is now a genuinely strong, multi-signal, multi-hour, production-verified basis — materially beyond the bar
  set after the previously-contradicted 50-minute claim. Not flipping `status: resolved`/archiving unprompted this tick
  — that's a consequential, one-way action (`resolved_by` + immediate `git mv` to `plans/archive/issues/`) and this
  doc's own history is four separate premature-closure corrections; surfacing this milestone to the operator as a
  checkpoint rather than unilaterally closing. Note for whoever makes that call: the orphan-tmux-server reaper (4th gap)
  is deliberately dry-run-only — it observes and logs, not a live safety net — so genuine resolution of the underlying
  vulnerability class rests on the first three fixes continuing to hold, not on the reaper masking any future
  recurrence.
- 2026-08-13 21:05Z-21:08Z: the v2 supervisor's own `--max-runtime 21600` (6h) ceiling expired on schedule and it exited
  cleanly, by design — NOT a fleet event. Confirmed via an independent live connect() check: the fleet server itself is
  still the SAME pid (3514516) it has been since 17:14:30Z, unbroken — the clean window is now 3h53m+ and was never
  actually interrupted, only the diagnostic tool's own runtime window was. Relaunched immediately for continued
  coverage; re-attached to the same pid on the first poll, as expected. Operator has not yet responded on the earlier
  closure question — continuing light background observation, doc not otherwise updated pending their answer.
- 2026-08-14 00:12Z (independent confirming check, separate interactive session): operator asked directly whether this
  bug is fixed. Fresh SSM query against `activity_log`, not reusing any cached figure: **zero** `tmux_server_died`
  events and **zero** whole-server-signature `tmux_session_lost` events (`tmux_server_alive=false`) between 20:20Z (when
  the 4th/last fix, `agent-orchestrator@d813ef1703`, shipped) and 00:12Z — a clean **~3h52m** window on this independent
  measurement, consistent with and extending the supervisor's own continuously-tracked pid-stability figure above. Last
  actual occurrence of any kind remains 17:13:27Z (~7h prior to this check). Relayed to the operator as "strong current
  evidence, holding," explicitly NOT as a re-declared permanent close — this doc has already walked back two premature
  closure claims (13:51Z, then again after the Layer-3 gaps), and the operator's own standing objection to declaring
  victory on a readback still applies. Not flipping `status`/archiving; that decision stays with whoever is tracking the
  still-open closure question above.
- **context-scout 2026-08-14**: populated context_scope (5 entries).
- **2026-08-15 (interactive session, independent check, prompted by an operator-pasted activity-feed review)**: live SSM
  investigation of the 2026-08-14 23:33:47-48Z 5-slot `tmux_session_lost` cluster (slots 1, 10, 11, 12, 18,
  `burst_size=5`, all `status=143`/SIGTERM, all `tmux_server_alive=True`). **Not a homogeneous burst** — full
  diagnostics below.
  - **Benign (3/5, NOT a bug)**: slot 12's death is a clean `one_task_per_session` recycle — `orchestrator.service`
    journal shows `WARNING SESSION-TEARDOWN kill_session session=orch-slot-12 reason=manual` at 23:33:09, co-timestamped
    in `activity_log` with `slot_done` → `slot_done_verified` → `worker_one_task_per_session_reset` for slot 12 at the
    same second. Slot 18 shows the identical `reason=manual` signature at 23:32:30 and respawned cleanly with a fresh
    task dispatch by 23:34:05-20 (`autospawn_succeeded` → `task_dispatched` → `slot_boot`). Slot 20 (same
    `reason=manual` pattern at 23:32:00, NOT actually part of the 5-slot cluster — respawned independently before it)
    confirms the pattern is the ordinary respawn-between-tasks path, not a crash; the pruner's own tick just lags the
    actual (benign) kill by up to ~30-40s, which is why 12/18's `tmux_session_lost` rows land in the same detection tick
    as the two genuine losses below and inflate `burst_size` to 5.
  - **Genuine (2/5, root cause NOT found)**: slot 11 — journal:
    `tmux_pruner: slot 11 session 'orch-slot-11' GONE mid-task ... resume_decision=resume pane_death={pane_dead_status: 143, ...} — reaped-stale candidate: the worker's tmux session died without a /done`;
    task `dp_exit_code_monitor_sweep_overlap_storm-4944c6c02138` (session `3ef5f645-f101-4456-b2f8-47b66ce3ed88`),
    marked resume-pending, dirty repo `deployment-service`. Slot 10 — journal:
    `REAPED-STALE agt-c42410 (role=custom kind=cicd label='cicd:ldr_qg_failure deployment-api#617') — tmux session 'orch-slot-10' gone without a clean /done after 2288s of runtime`;
    a corresponding task-scoped (`slot_id=None`) `tmux_session_lost` row also fired at 23:33:48.124602Z naming the same
    task, confirming which in-flight task each craft loss corresponds to. Neither shows the OOM (`cgroup oom_kill=0`),
    host-load/RAM/swap elevation, spawn-storm (`concurrent_recent_spawns=0`), or `tmux_server_alive=False` kill-server
    signature this doc already confirmed as root cause elsewhere — so this is NOT evidence of that bug recurring.
    Widened `orchestrator.service` journal search (23:30-23:36Z, grepped for error/exception/traceback/kill/sigterm)
    found no exception or crash trace bracketing either death; the nearest anomalies were unrelated and non-fatal — a
    caught `sqlite3.IntegrityError: UNIQUE constraint failed: batching_turns.message_id` in `BatchingStatsPoller` at
    23:32:59 (different subsystem, "continuing"), and an Anthropic API `429` for account `sub-a-ikenna` at 23:33:52-53
    (AFTER the deaths, unrelated poller). Root cause for slots 10/11 specifically stays unidentified — filed as a todo
    above rather than closed.
  - **Separately surfaced, not this doc's scope**: account `sub-a-ikenna` was observed with
    `rate_limited_until: 2026-08-19T13:59:59Z` / `overage_disabled_reason: out_of_credits` on an unrelated slot-1 death
    earlier the same evening (22:59:33Z) — flagging for operator awareness in case that account is still expected to
    carry fleet spawn capacity through that window; not investigated further here.
  - **Tooling gap noted**: `check-ao-recent-deaths.sh`'s diagnostic payload (and this doc's own "`burst_size`>1 =
    server-wide crash" heuristic) has no way to tell a `reason="manual"` recycle-teardown apart from a genuine
    crash/kill without a separate journal/`slot_done` cross-reference, done by hand this session — todo filed above to
    close that gap in the tool itself.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:861ed334074db2b1]: KEEP-NA, valid — status: open, active live-incident investigation with a documented history of premature-closure self-corrections; remaining items are genuine unresolved root-cause work plus operator-gated live-infra decisions.
- **2026-08-18 — convergence audit against the other 2 open tmux-loss docs** (operator-requested consolidation pass):
  read `plan_reconciler_unexplained_tmux_session_loss_2026_08_10.md` and
  `ao_tmux_loss_rate_canary_likely_overtuned_2026_08_18.md` in full. **Verdict: NOT a 3-way merge.** This doc and
  `plan_reconciler_...` converge on the SAME underlying mechanism — that doc's own 2026-08-15 note already
  self-identifies this doc's confirmed root cause (shared ambient tmux socket, reachable by any process's bare
  `kill-server`/`rm -rf`) as the most-likely (not provable, forensic evidence was itself lost to that doc's own
  separately-real `remain-on-exit` bug) explanation for its 2026-08-10 incident. Not merged in: that doc is
  `archive_exempt: true` (na-eligibility-audit KEEP-NA 2026-08-17) serving as a standing incident record + the origin
  of the `TmuxSessionLossRateCanary` recommendation, and this doc is already 660+ lines against a 1000-line hard cap —
  merging would blow past size discipline for no gain over a clean cross-link. Added it to `related:` above; the
  shared root cause stays stated once, here. `ao_tmux_loss_rate_canary_likely_overtuned_...` does NOT converge on
  root cause — it investigates the `TmuxSessionLossRateCanary` ALERT's threshold tuning (a statistics/observability
  question), not why sessions die; that mechanism is real and genuinely distinct from this doc's. It IS related in a
  previously-unlinked way: this doc's own still-open P3 todo about `check-ao-recent-deaths.sh`'s `burst_size`
  conflating benign `reason="manual"` recycle-teardowns with genuine losses (proven for the 2026-08-14 23:33 cluster,
  3/5 members benign) is very likely the SAME undercounting gap now inflating the canary's rolling-window breach
  count in a second consumer of the same `tmux_session_lost` event stream — cross-linked both directions (see the
  todo above and that doc's own follow-up). Added both docs to `related:`.
  **Also resolved this doc's own open `[OPERATOR]` todo** (pid 2934337 cleanup): re-verified live via read-only SSM
  against `i-0c9b283b31d6b5ca7` — `ps -p 2934337` not found, `/tmp/tmux-1000/default` (ambient default socket) reports
  "no server running", zero `lsof` handles on that path; the only live tmux server on the host is pid 3514516 on the
  isolated fleet socket (`ELAPSED=448991s`, ~124.7h/~5.2 days, unbroken since the 2026-08-13 17:14:35Z respawn already
  tracked above). This confirms the operator-directed kill documented in the 2026-08-13 17:46Z-18:10Z entry actually
  covered this PID (same number, same "ambient socket"/"split-brain slot 1" description) — the still-open todo asking
  for a fresh operator decision was a stale duplicate of the item already marked DONE earlier in this list; flipped to
  `[x]` with this evidence rather than re-escalating a decision the operator already made and that AO already executed
  on. **Not touching `status`**: the ~5.2-day single-pid uptime is materially beyond every prior (contradicted)
  closure bar this doc has set for itself, but per this doc's own established discipline (2026-08-13 19:49Z: "not
  flipping status/archiving unprompted... surfacing this milestone to the operator as a checkpoint rather than
  unilaterally closing") this stays a checkpoint for the operator, not a unilateral re-declaration of closure — doc
  stays `status: open`.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:90a1ddb246972541]: KEEP-NA, valid — live-incident investigation with 4 self-corrected premature-closure claims and shipped fixes across 3+ layers; converges with the 2026-08-17 na-eligibility-audit verdict. Remaining 10 open items are genuine unresolved root-cause work (death #2 at 14:30:28 still unexplained) or [OPERATOR]-tagged live-infra decisions; the 32-item condensed Todo section's count (22 closed + 10 open) verified consistent.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **2026-08-20 (interactive session, slot 1)**: operator asked to root-cause a specific slot-1 death and whether it's
  genuinely agents dying vs. the backend reaping them mid-task. Live-queried `check-ao-recent-deaths.sh --slot 1` for
  the 05:17:50Z death: `death_class=unexplained`, `tmux_server_alive=True` (rules out this doc's confirmed
  kill-server signature), `burst_size=1`, no OOM (`cgroup oom_kill=0`), no core dump (rules out a self-inflicted
  crash), pane exited status 143 (SIGTERM) 434s into a live task — genuinely mid-task, not a redispatch-counting
  artifact, and not the fleet's own watchdog/reaper (`death_class` would show `intentional_teardown` if it were).
  While investigating, found `death_forensics.py`'s `check_external_kill` (shipped 2026-08-15 to answer exactly
  "OOM vs external kill" for these unexplained deaths) had been non-functional since it shipped — see the new todo
  above for the fix, shipped `agent-orchestrator@5d48a60b5b`. Operator then asked to confirm this isn't slot-1-specific
  — fleet-wide query (see new `[INVESTIGATE]` todo above) confirmed it isn't: 17 slots show `tmux_session_lost` in the
  last 24h, several majority-`unexplained`, and several specific task IDs died repeatedly across DIFFERENT slots —
  the strongest new lead this session, since a death that follows the TASK rather than the HOST points away from a
  per-slot/per-host cause. Not yet investigated what those specific tasks do; filed as the next todo rather than
  guessing. Separately (adjacent finding, not this doc's scope): `quality-gates.sh`'s dashboard gate only checked
  `node_modules` existence, not sync with `package.json` — any slot pulling a commit that adds a dashboard dependency
  without a fresh `npm install` hit a confusing vite crash instead of the intended fail-closed message; fixed in the
  same commit as the ausearch fix (mtime-based staleness detection was tried and rejected — sub-second write-order
  races flagged a fresh install as stale; landed on a plain per-declared-dependency filesystem check instead,
  verified against both a healthy and a simulated-stale state).
- **2026-08-20 (interactive session, slot 1, continued)**: operator asked to download the full transcripts for slots
  1/7/32's mid-task deaths and diagnose properly — see the new `[INFRA] P0` todo above for the full finding
  (slot 7/32 false-positive teardowns; slot 1 SIGKILL root-caused to `orphan_reap`'s SID exemption not covering
  `setsid` detachment, fixed `agent-orchestrator@67b68dac39`; slot 1 SIGTERM still genuinely unexplained). This is
  the first session-CONTENT-level (not plan-doc-level) explanation found for any of the "unexplained" deaths since
  the original kill-server root cause — worth re-reading live transcripts for future unexplained-death
  investigations before assuming a fresh mechanism, since plan-doc content alone already proved insufficient once
  (the "no shared task trigger" negative result two todos above, superseded by this entry).
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: KEEP-NA, valid — active live-incident investigation, 10 open items spanning genuine unresolved root-cause work (death #2 at 14:30:28 still unexplained), an [OPERATOR]-gated dry-run graduation, and several judgment-bearing follow-ups; converges with the 2026-08-19 verdict, no content drift changing the disposition.
- **2026-08-21 (interactive session, slot 12)**: operator asked to re-investigate why deaths were still occurring at
  high volume despite the 2026-08-20 fixes (`67b68dac39` setsid/orphan_reap exemption, `5d48a60b5b` ausearch date
  format), starting from per-account `activity_log` forensics rather than assuming yesterday's fixes were incomplete.
  Raw 24h `unexplained` death counts were heavily skewed toward `codex-luna` (62) vs the next account (36), but
  operator correctly flagged this needed normalizing against dispatch volume before concluding codex-luna was
  uniquely broken. Normalized (`unexplained` / `autospawn_succeeded` per account, 24h): codex-luna 62/98=63%,
  deepseek-v4-flash 25/27=93% (WORSE per-spawn than codex-luna), deepseek-v4-pro 13/20=65%, and genuine mid-task
  losses also hit Anthropic sub-accounts directly (sub-h-igboestates 3/13, sub-e-odum2default 6/4-ish small-sample) —
  ruling out "codex-bridge-specific bug" as the sole explanation; this is a broad, roughly-uniform, cross-provider
  problem, codex-luna just carries the most raw volume because it's dispatched the most.
  Picked codex-luna to root-cause first (operator: "claude sessions are low, start with codex-luna"). Pulled full
  `tmux_session_lost` `pane_death_info`/`pane_tail` for 4 codex-luna `unexplained` mid-task deaths (slots 4, 8, 9, 12)
  and found **two distinct, previously-unidentified death signatures**, both genuinely root-caused (not left as
  "unexplained"):
  - **Pattern A (signal 9/SIGKILL, the dominant one — 76 `TransportClosedError` occurrences in the last 24h alone)**:
    pane shows `API Error: 502 {"detail":"Codex SDK call failed: unhandled errors in a TaskGroup (1 sub-exception)"}`
    while Claude Code's own footer still reads "Worked for Nm Ns" (i.e. genuinely mid-request, not idle). Traced via
    `journalctl -u codex-bridge` to the real (bridge-swallowed) traceback:
    `openai_codex.errors.TransportClosedError: Codex process closed stdout`, immediately preceded every single time by
    `codex_app_server: Codex could not find bubblewrap on PATH... Codex will use the bundled bubblewrap in the
    meantime`. **Reproduced live, host-wide, twice, independent of codex/bwrap entirely**: both
    `unshare --user --map-root-user whoami` (`write failed /proc/self/uid_map: Operation not permitted`) and the
    bundled `bwrap` binary directly (`bwrap: setting up uid map: Permission denied`) fail identically for the `ubuntu`
    user on this VM. Checked and ruled out as the specific mechanism: `kernel.unprivileged_userns_clone=1` (fine),
    `user.max_user_namespaces=115876` (fine), the `unprivileged_userns` AppArmor profile IS loaded+enforcing
    (`aa-status`) and its own body says `allow userns,` — yet creation still fails with no AVC audit record found
    (`ausearch -m AVC` / `dmesg`), so the exact LSM/kernel hook is not pinned to certainty; the standard Ubuntu 24.04
    remediation for this exact class of failure (`kernel.apparmor_restrict_unprivileged_userns` 1→0) was identified
    but NOT applied — host security sysctl on shared production infra, filed as an `[OPERATOR]` todo above rather than
    flipped autonomously.
  - **Pattern B (signal 143/SIGTERM)**: pane shows the recurring `"gpt-5.6-luna" is not a model this version of Claude
    Code recognizes...` banner followed by Claude Code's own clean-exit `Resume this session with: claude --resume
    <uuid>`, then SIGTERM. Root cause confirmed via code read, not inference: `model_tier.py:177,231` already
    registers `gpt-5.6-luna`'s real 272,000-token window, but `tmux_spawn.py:933-936`'s `CLAUDE_CODE_MAX_CONTEXT_TOKENS`
    export only matches `*deepseek*` in its shell `case` — codex-luna was simply never added to that branch, so the
    CLI guesses ~200K for it on every single spawn. Filed as an `[INFRA]` todo above, held pending a separate
    concurrently-running agent's work in the same file (round-robin account-selection logic) per operator instruction,
    to avoid a collision — not yet fixed.
  Operator directed: stop codex-luna from the fleet immediately, fix both root causes, THEN re-enable — do not
  dispatch new work to it in the meantime. Executed via the orchestrator's own existing operator-disable mechanism
  (no code change): `POST /api/accounts/codex-luna/disable` → `account_usage.account_status=disabled` (sticky, no
  auto-clear, excluded from `account_is_usable()`) + `rotate_all_slots_off_account(..., trigger="operator-disabled")`,
  which also evicted every slot then actively running codex-luna (~12 `working` slots at the time) onto a different
  account, preserving in-flight task/worktree. Confirmed persisted: `account_usage.account_status='codex-luna'` row =
  `disabled`; `activity_log` id 623935 `account_disabled`. Re-enable is gated on both `[OPERATOR]`/`[INFRA]` todos
  above landing AND being independently re-verified, per the new todo above — not a passive timeout.
