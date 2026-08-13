---
doc_type: issue
title: Fleet tmux session loss — ROOT CAUSE CONFIRMED, two-layer fix VERIFIED and CLOSED (2026-08-13)
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
  - /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md
  - /plans/active/issues/fleet_wide_deepseek_crash_loop_undetected_2026_08_11.md
  - /codex/15-runbooks/isolated-deepseek-crash-debug-sandbox.md
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
- [x] [INFRA] P3. Dashboard UI for scheduled-dispatch pause/resume — deferred, unrelated to root cause, not lost.
- [x] [INFRA] P0. THIRD live catch, 2026-08-12 01:34:55 — folded into the eventual root-cause evidence chain.
- [x] [INFRA] P0. FOURTH live catch — `fleet-git-health-guard.sh` lead, real but partial; see next item.
- [x] [INFRA] P0. `fleet-git-health-guard.sh` de-prioritized + overlap-locked — SHIPPED 2026-08-12 (a real fix, kept).
- [x] [INFRA] P1. Isolated (non-burst) single-slot death, 2026-08-12 14:03:55 — folded into evidence chain.
- [x] [INVESTIGATE] P0. "Think outside the box" external lead — led toward the eventual multi-operator-VM finding.
- [x] [INFRA] P0. Root-caused + fixed why no death ever produced a forensic artifact — SHIPPED 2026-08-12 (LimitCORE).
- [x] [INVESTIGATE] P0. First two valid core-dump tests, both empty — real evidence, folded into final root cause.
- [x] [INVESTIGATE] P0. Two more bursts, 2026-08-12 19:45:24Z — folded into the eventual root-cause evidence chain.
- [ ] [INFRA] P2. Audit other repos for the SAME unscoped-tmux-fixture anti-pattern the bats suite had (any test
      touching real tmux sessions needs its OWN isolated `TMUX_TMPDIR`, never the ambient/inherited one) — this class of
      bug is not unique to `test_slot_git_status_claim_heartbeat.bats`, just the one that happened to be caught.
- [ ] [INFRA] P3. Once confidence is high (extended clean window, no new `tmux_session_lost` bursts), tear down the
      `strace_tmux_server_supervisor.sh` + `auditctl tmux_exec_watch` diagnostic instrumentation — they were built for
      this investigation, not intended as permanent fixtures, and the strace log alone runs several MB/hour.
- [ ] [INFRA] P3. Consider documenting the `TMUX_TMPDIR`/`TMUX`/`TMUX_PANE` isolation pattern in codex
      (`/codex/05-infrastructure/`) as a standing rule for this shared multi-operator VM, so the NEXT service that
      spawns its own tmux-based fleet doesn't rediscover this the hard way.
- [x] [INFRA] P1. Guard against the pre-spawn dirty-state gate ever committing raw unresolved git 3-way-merge
      conflict-marker blocks as "orphan WIP" again — the exact corruption this doc's own recovery hit mid-investigation
      (an inherited commit on this doc contained live conflict-marker blocks; recovered by hand, see the Progress Log
      entry below). SHIPPED `agent-orchestrator@14184ca0ed`: new FM9 guard
      (`server/worktree_clean_check/_conflict_markers.py`) refuses + quarantines a repo whose dirty tracked files
      contain the paired open/close conflict-marker sentinel, wired into `commit_and_push_dirty_repos` next to the
      existing FM2 wiped-index guard. Unit + end-to-end tests included; full `quality-gates.sh` green.

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
- 2026-08-13 (post-closure hardening): the recovery work earlier in this Progress Log — an inherited pre-spawn commit on
  this very doc that carried raw unresolved conflict-marker blocks straight into git history — was a real, reproducible
  gap in `commit_and_push_dirty_repos` (the FM2 wiped-index/mass-deletion guard has no opinion about file CONTENT, only
  porcelain shape). Shipped a dedicated guard rather than leaving it as a one-off recovery story:
  `agent-orchestrator@14184ca0ed` adds FM9 (`_conflict_markers.py`) — refuses + quarantines any dirty tracked file
  carrying the paired open/close conflict-marker sentinel, mirroring FM2's existing refuse-and-quarantine shape exactly.
  New unit tests cover the positive signature, the markdown-horizontal-rule false-positive case (a bare `=` divider line
  is deliberately NOT treated as a signature — mirrors the `check_conflict_markers.sh` false-positive class this same
  doc's recovery already hit once), and an end-to-end `resolve_dirty_state` refusal. Full `quality-gates.sh` green (3582
  pytest + 319 vitest), `ahead=0`, content verified on `origin/live-defi-rollout`. This is orthogonal to the tmux-death
  root cause above (already CLOSED) — it hardens the recovery tooling this investigation happened to expose a real bug
  in, not the tmux mechanism itself.
