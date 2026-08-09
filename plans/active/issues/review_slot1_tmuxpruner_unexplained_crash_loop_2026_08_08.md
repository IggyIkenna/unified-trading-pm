---
doc_type: issue
title:
  Slot 1 (review role) crash-looping via unexplained TmuxPruner kills, ~20 of 22 in 2h with no context_recycle_requested
summary: >-
  Review-craft investigation (2026-08-08, ~14:30-16:30Z window) found slot 1's `agentkeeper_review_succeeded` events
  paired almost 1:1 with `tmux_session_lost` (TmuxPruner-attributed, externally-killed) — 22 pairs in ~2h — but only 2
  of the 22 deaths were preceded by a genuine `context_recycle_requested` event. The other ~20 are unexplained kills,
  not voluntary RECYCLE exits, meaning review continuity is fragmenting into many short-lived (1-6 min) sessions and
  burning real spawn overhead continuously. Checked against the 3 event types behind the previously-tracked fleet-wide
  post-spawn wedge pattern (`forced_compact_ineffective`, `slot_wedged_killed_for_resume`, `worker_kick_failed`) — zero
  hits for slot 1 on any of the 3, so this looks like a different mechanism, though a shared deeper root cause (e.g.
  host-level contention, per prior review/main joint findings on the tardis wedge cluster) cannot be ruled out without
  reading TmuxPruner/keeper source directly.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, tmux, review-role, crash-loop, live-incident, spawn-overhead]
related:
  - /plans/active/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
created: 2026-08-08
author: agt-22de53 (main), relaying a review-craft finding (msg 4310, from_role review)
parent_epic: infrastructure_master
priority: P1
source: >-
  Review-craft session, dispatched on unrelated work, independently noticed the pattern while investigating slot 1's own
  boot history and reported it to main via chat (msg 4310, 2026-08-08T16:36:22Z) rather than filing directly —
  doc-authoring/backlog is outside review's scope per its own role definition.
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-09
locked_since:
context_scope: [agent-orchestrator/server/routes/slots_worker.py, agent-orchestrator/server/state_store/cooldown.py]
---

# Slot 1 (review role) crash-looping via unexplained TmuxPruner kills

## What was found

Reporter (review craft, slot unspecified in the message, investigating slot 1's own history) queried
`GET /api/activity?slot=1` for the window 14:30-16:30Z on 2026-08-08 and found:

- 22x `agentkeeper_review_succeeded` events, paired almost 1:1 with 22x `tmux_session_lost` events (TmuxPruner
  attribution — externally-killed, not a voluntary exit).
- Of those 22 death events, only **2** were immediately preceded by a genuine `context_recycle_requested` event (the
  sanctioned self-compact/RECYCLE exit path). The remaining **~20** have no such precursor — unexplained kills.
- Cross-checked against the 3 event types known to drive the separately-tracked fleet-wide post-spawn wedge pattern
  (`forced_compact_ineffective`, `slot_wedged_killed_for_resume`, `worker_kick_failed`): **zero hits** for slot 1 on any
  of the 3 in this window. This suggests a distinct mechanism from that cluster, not a re-occurrence of it — though a
  shared deeper root cause (e.g. host-level resource contention) has not been ruled out; nobody has read
  TmuxPruner/keeper source or captured a live pane at the moment of death yet.

**Compounding, likely-related bug found in the same investigation**: ~6 of ~14 `slot_boot` cycles for slot 1 in the same
window hit `boot_read_unconfirmed` (428, missing `worker.md`) on the first `/boot` attempt — see
`/plans/active/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md` (Progress Log updated 2026-08-08 with
this same finding). Net effect of both bugs together: review continuity is fragmenting into many short-lived (often 1-6
min) sessions, which also explains the volume of distinct short-lived agent ids seen in `review-agent-checkpoint.md`'s
own Tick history.

## Why it matters

- Continuous spawn overhead: ~22 kill/respawn cycles in 2h on a single slot is real, ongoing waste (compute + boot
  round-trips), not a one-off.
- Degrades review quality/continuity: short-lived sessions cannot build up the multi-hour context a thorough review pass
  benefits from, and each restart re-pays the (separately buggy) boot-read-confirmation cost above.
- Unknown root cause: without keeper/TmuxPruner source inspection or a live pane capture at the moment of death, it is
  not yet known whether this is a liveness-probe false-positive, a resource-pressure kill, or something else.

## Todos

- [x] ✅ [BACKEND] P1. Read `TmuxPruner`'s kill logic (and whatever emits `tmux_session_lost`) in the agent-orchestrator
      server source and determine why it is concluding slot 1's tmux session is lost roughly every 5-10 minutes when the
      session is, in the large majority of cases, not exiting voluntarily (no preceding `context_recycle_requested`).
      Check specifically whether this is a liveness-probe timing/false-positive issue (e.g. a heartbeat threshold too
      tight for review-craft's actual work cadence) versus a genuine external kill (resource pressure, OOM, a supervisor
      restart). Repo: agent-orchestrator. — agent-orchestrator@e32d962 + Progress Log entry below.
- [x] ✅ [BACKEND] P2. If the root cause is a false-positive liveness probe: fix the threshold/detection logic. If it is
      a genuine resource-pressure kill: correlate against host memory/CPU metrics for the same window and file/link to
      the appropriate host-capacity issue if one already exists (check
      `/plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` first for a possible match
      before filing new). Repo: agent-orchestrator. — agent-orchestrator@e32d962 + Progress Log entry below.
- [x] ✅ [REVIEW] P3. **Re-verified (2026-08-09 ~19:16Z, slot 19) — NOT resolved, rate unchanged.** All 3 landed fixes
      (`e32d962`, `dd01255`, `5a163e7`) confirmed live for the full measured window; `tmux_session_lost` cadence for
      slot 1 is statistically indistinguishable from the pre-fix baseline (~1/8.6min vs the original ~1/5-8min). See
      Progress Log entry below for full methodology + data. New todo added below capturing the continued-investigation
      ask this negative result implies. Repo: unified-trading-pm (verification + checkbox flip only).
- [x] ✅ [BACKEND] P1. **Second, distinct root cause found (review, msg 4361, code-confirmed from live source, not
      guessed)**: `check_spawn_heartbeat_timeouts()` (`server/worker_liveness/_auth_failover.py:54`) gates a
      slot-bearing agent's liveness on `SlotRow.last_ping >= SlotRow.last_spawned_at` (line 96); past
      `SPAWN_HEARTBEAT_TIMEOUT_SECONDS` it only spares the slot if `pane_state=="working"` (line 122). But review's
      documented loop (`review.md` STEP 2) calls only `/api/agents/{id}/poll`, which writes `AgentRow.last_ping`
      (`server/routes/agents.py:784` → `state_store/agents.py:751`) — **never** `SlotRow.last_ping`. So a review
      session's `SlotRow.last_ping` freezes near spawn time and never advances; once `spawn_retry_count` hits cap=2,
      `spawn_retry_cap_reached` fires (a `_DEATH_SIGNAL_EVENT_TYPES` member, `worktree_clean_check/_liveness.py:70`) and
      the session is killed — repeatedly, for its entire life, not a one-time boot issue. `pane_state=="idle"`
      (legitimate "waiting quietly, nothing queued" between review ticks) is NOT exempted the way `"working"` is.
      Confirmed live: 5x `tmux_session_lost` since 23:44:42Z spanning BOTH the 23:45:40Z and 00:17:46Z `e32d962`-load
      restarts with unchanged cadence — the debounce fix does not touch this path. Pick ONE (review left scoping to the
      implementer, has not tested a fix): (a) have review's (and other slot-bearing agent-surface roles' — same
      `_AGENT_KIND_BY_PROMPT_TEMPLATE` set) loop also call a slot-level heartbeat endpoint once per tick so
      `SlotRow.last_ping` advances; (b) make `check_spawn_heartbeat_timeouts` consult `AgentRow.last_ping` too for those
      roles; (c) exempt `pane_state=="idle"` the same way `"working"` already is. Repo: agent-orchestrator. —
      agent-orchestrator@dd01255 (option (b), code-only fix, covers every chat-loop role uniformly regardless of pane
      state) + Progress Log entry below.
- [x] ✅ [BACKEND] P1. **Both prior fixes (`e32d962` debounce + `dd01255` heartbeat-exempt) confirmed live but the crash
      rate is UNCHANGED (msg 4372)** — review traced `GET /api/activity?slot=1` across a fresh 87min window
      (01:08-02:35Z, well after both fixes' restart) and found ~100% of review-role sessions still died via
      `tmux_session_lost` with zero `context_recycle_requested` precursors, survival 47s-14m12s, no improving trend.
      Most recent death (agt-2f893e) went STRAIGHT to `tmux_session_lost` with no preceding
      `spawn_heartbeat_timeout_pane_working`/`spawn_retry_cap_reached` at all — meaning `dd01255`'s own gated code path
      wasn't even implicated; the kill came from TmuxPruner's has-session debounce (`e32d962`'s target), which only
      absorbs ONE miss 0.25s apart. Corroborates the host-memory-pressure hypothesis already cross-linked to
      `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`: `orchestrator.service` cgroup at 19-23G/26G
      mem + 9.1G/16G swap (peak 13.6G), system-wide swap 9.3Gi in use at time of report. Plausible the shared tmux
      server itself stalls >0.25s under this load, defeating the debounce regardless of which slot-liveness logic gates
      on it — a 3rd logic-only patch is unlikely to help without host memory relief first. Repo: agent-orchestrator +
      cross-reference the host-memory doc for the actual remediation (memory bump / reduce concurrent slot count /
      investigate the swap source). **CPU-contention angle added (msg 4373, agt-9a70a7)**: load average 36/44/46 on an
      8-core box (nproc=8), `vmstat` runnable-queue depth 20/38/32 with %idle collapsing to 1% in 2 of 3 samples,
      context-switches/s spiking 48k-55k, 27 concurrent `claude` CLI processes host-wide — additive to, not a
      replacement for, the memory/swap hypothesis (manual `tmux has-session` calls returned <0.01s when checked, so it's
      plausibly scheduling-delay-under-contention on the orchestrator/tmux-client fork, not tmux itself being slow).
      Whoever picks this up: pull load-average/runnable-queue history (not just mem/swap) for the recorded death
      timestamps too. **Trend update (msg 4376, agt-45d610, 03:07Z): still worsening** — load avg now 65.56/62.12/55.86
      (up from 55/53/49 at 02:57Z, up from 36/44/46 at ~02:48Z — CPU %us+%sy 92-99% in 2 of 3 samples), 49 concurrent
      `claude` CLI processes, memory comparatively flat (~19.5/27.9GB cgroup). **New hypothesis worth investigating**: a
      possible self-reinforcing feedback loop — AutoSpawn's ~60s respawn design (meant to minimize downtime) may itself
      ADD CPU load at exactly the moment contention is already high, i.e. crash rate and contention could be mutually
      reinforcing rather than purely one-directional (contention→crashes). If confirmed, a respawn-rate backoff/throttle
      during a detected contention event could help more than waiting for organic host relief alone — flagged as a
      hypothesis for backend/operator judgment, not asserted as proven causation. **KEY UPDATE (msg 4403, agt-f56131,
      05:23Z): crash rate DECOUPLED from raw contention level.** Host load has eased ~75% since the 03:14Z peak (load
      avg now 14.29/13.30/18.86 vs 63-65; QG processes 5 vs 12-19; claude CLI processes 37 vs 49; swap 12Gi vs 14Gi) —
      but the kill CADENCE is completely unchanged: still 16x `tmux_session_lost`/0x `context_recycle_requested` in the
      ~2h16m window since the 03:07Z checkpoint, landing every ~5-8min regardless (04:39/04:47/04:55/05:03/
      05:08/05:15Z). This argues against "wait for host relief" being sufficient on its own, and toward either (a) a
      much lower actual trigger threshold than assumed (today's 2x-core oversubscription is apparently already enough,
      vs the peak's 7-8x), or (b) the standing feedback-loop hypothesis above (AutoSpawn's own respawn churn sustaining
      an independent load floor). No dmesg/journalctl access from any review sandbox session (confirmed
      permission-denied, consistently across sessions) to independently verify current kernel OOM-killer activity.
      **OPERATOR-CONFIRMED ESCALATION (msg 4377, 03:14Z)**: this is now a severe, ACTIVE, human-confirmed incident, not
      just review-role-scoped. Operator independently reported (and main independently re-confirmed at 03:15Z): 12-19
      concurrent `quality-gates.sh` processes, load avg 63.28/60.29/57.11, only 893Mi genuinely free RAM (`free -h`'s
      "available" 15Gi is reclaimable buff/cache, not true headroom), swap 14Gi/47Gi used. Genuine kernel OOM-killer
      activity confirmed — the operator's own bare `sleep 60` was killed before completing, meaning the reaper is not
      QG-specific, it's fleet-wide. Operator's own quickmerge ship is blocked (QG self-aborts via its own
      `qg-host-governor.sh` RAM watchdog near completion, after passing every substantive gate). **Nuance**:
      `qg-host-governor.sh`'s documented ≤2 cap (`max(2, floor(physical_cores/4))`) gates only the HEAVY phase
      (pytest/basedpyright) via flock tokens, not total `quality-gates.sh` script instances — so 12+ running processes
      is not automatically proof the governor itself is broken; unverified whether that many are concurrently holding a
      heavy-phase token vs sitting in lighter setup/lint phases. New todo added below to determine whether
      total-instance count (not just heavy-phase count) also needs a cap, since even light-phase QG steps compound with
      the ~20+ concurrent Claude CLI sessions already driving the CPU/memory picture documented above. **RESOLVED
      (backend, slot 23, agent-orchestrator@5a163e7)**: found the ACTUAL first detector (not TmuxPruner —
      `reap_orphan_agents`, undebounced, fires 30-45s earlier every time) and fixed it, then used a live PID capture to
      settle the false-positive-vs-genuine-death question this todo left open. Full method + evidence in the Progress
      Log entry below. Short version: the death IS genuine (process confirmed gone, not just detached from tmux), OOM
      and every AO-Python-code kill path are ruled out with hard evidence, and the fix shipped closes a real
      previously-unpatched gap but does not by itself explain the underlying death — see the new todo below.
- [x] ✅ [BACKEND] P1. **DONE 2026-08-09 (slot 33, review→backend_engineer craft) — HYPOTHESIS FALSIFIED, empirically
      tested exactly as specified.** Spawned a throwaway tmux session (`loop-hypothesis-test`, fresh `--session-id`,
      same `exec claude --dangerously-skip-permissions` shape the orchestrator itself uses), issued
      `/loop 60s reply with exactly the word: tick`, and captured the pane's PID every 10s across the full test (bounded
      background monitor, `run_in_background`, ~2.5 min).
  - **Mechanism found**: `/loop <N>s <task>` in this Claude Code version (2.1.202) is implemented via `CronCreate` — a
    session-scoped cron job (`*/1 * * * *` for `60s`) that fires INSIDE the existing process. The pane's own output
    confirms it verbatim:
    `"Scheduled: every minute (job 97d7b0ca)... Session-only — it stops if this session ends, and auto-expires after 7 days."`
    This is a fundamentally different mechanism than "tear down and relaunch" — it's an in-process timer, not an
    external respawn.
  - **PID result**: pane PID `1400154` (started `10:23:36`) was IDENTICAL across every 10s sample from spawn through
    BOTH the first tick (`"tick"` reply + `Worked for 7s`, ~10:24:47) and the second tick
    (`"Running scheduled task (Aug 9 10:25am)"` → `"tick"` reply, ~10:25:47) — zero PID changes, zero process restarts,
    for the full observed lifetime. **Hypothesis FALSIFIED**: `/loop` does NOT terminate the underlying OS process
    between ticks; no external relaunch mechanism exists to investigate on the `review.md` boot-prompt side. Test
    session cleanly exited (`/bye`) and the tmux session removed — no orphan left behind.
  - **Next step taken (per this todo's own fallback instruction)**: since the PID was stable, checked
    `dmesg`/`journalctl -k` access from this worker sandbox. `dmesg` itself still refuses (`Operation not permitted`,
    matches every prior session), but **`journalctl -k` WORKS from this slot's sandbox** — a capability gap this doc had
    recorded as universal (`"every session so far, review AND backend, has hit Operation not permitted on both"`) turns
    out to be `dmesg`-specific, not journald-wide. Queried `journalctl -k` for 4 independent, exact, just-confirmed
    `orch-slot-1` `tmux_session_lost` timestamps (10:26:19Z, 10:14:20Z, 10:09:04Z, 09:54:19Z, via a live
    `GET /api/activity?slot=1&type=tmux_session_lost`) — **zero kernel-log entries in any of the 4 windows**. This
    further rules out a kernel-level cause (OOM killer, cgroup enforcement, hardware fault) for these SPECIFIC deaths —
    a real kernel kill always logs via `journalctl -k`, and none did. Cross-referenced the most recent death (10:26:19Z)
    against `journalctl -u orchestrator` for the same window and found the actual proximate AO-side trigger:
    `AgentKeeper reaped 2 orphan agent record(s): [('agt-aa4070', 'dead-tmux-session'), ...]` at `10:26:16.429Z` — 2.6s
    BEFORE the `tmux_session_lost` activity event — i.e. `reap_orphan_agents` (the already-identified first detector,
    `agent-orchestrator@5a163e7`) fired first, confirming that fix's own diagnosis is still the correct proximate
    mechanism; this new data point doesn't change that conclusion, it adds a 4th kernel-log-negative sample to the
    "genuine death, not kernel-visible" evidence pile. New bounded follow-up todo added below capturing the
    `journalctl -k` access finding for whoever continues the root-cause hunt — did NOT chase the underlying "why does
    the process actually exit" question further myself; that's outside this todo's own scope (it only asked to
    falsify/confirm the `/loop` hypothesis and take the ONE next step its own text names). Repo: unified-trading-pm
    (this doc only — no code shipped, `/loop` behavior lives in the Claude Code CLI itself, not this repo).
- [x] ✅ [DOCS] P3. Correct the ~00:22Z progress-log entry below (12-slot simultaneous burst) — review (msg 4361) showed
      it's a batch-processing artifact of `check_spawn_heartbeat_timeouts()` scanning all slots in one pass per tick,
      NOT a tmux-server-level event as originally hypothesized; only the review-role entry in that burst was a real loss
      (the other 4 were already-finished scheduled jobs, `archived_lifecycle_complete:true`). Superseded-note only, keep
      the original entry for history — do not delete it. — unified-trading-pm (this doc) + Progress Log entry below.
- [x] ✅ [BACKEND] P1. **Operator-confirmed active incident (msg 4377)** — determine whether
      `quality-gates-base/qg-host-governor.sh`'s ≤2 heavy-phase cap needs to be extended to gate total
      `quality-gates.sh` script instances (not just pytest/basedpyright), given 12-19 concurrent instances were observed
      with only 893Mi genuine free RAM and confirmed fleet-wide kernel OOM-killer activity (a bare `sleep 60` was
      reaped). First step: check whether those 12+ processes are actually holding heavy-phase governor tokens (governor
      working as designed, cap is just too permissive) or running ungated in lighter phases (governor scope gap). Repo:
      unified-trading-pm (`scripts/quality-gates-base/qg-host-governor.sh`). Cross-reference the standing
      CPU-contention/respawn-loop hypothesis above — likely the SAME underlying host-capacity crisis, not a separate
      one. — unified-trading-pm@413f5aad3 + @f8fcd10f1 + Progress Log entry below (GOVERNOR SCOPE GAP confirmed, fixed).
- [x] ✅ [OPERATOR] P1. `agent-orchestrator@e32d962` (the TmuxPruner debounce fix) was committed but not loaded — the
      live uvicorn process (PID 885271) started at 23:15:22Z, ~11min BEFORE the 23:26:25Z commit. Main could not restart
      it (sandbox permission boundary: `sudo`/non-interactive `systemctl restart` both blocked). RESOLVED —
      `GET /api/state` now reports `server_started:2026-08-08T23:45:40Z` (after the commit); `git log` in the
      orchestrator checkout still confirms HEAD=e32d962. Someone/something with the right privilege restarted it. Todo 3
      (REVIEW re-verify) can now proceed.
- [x] ✅ [BACKEND] P2. **DONE 2026-08-09 ~20:10Z (infra→backend_engineer craft, slot 20) — access re-verified durable,
      standing correlation check code-ified, wider signal grep run against 10 fresh samples, zero matches.** All 3
      sub-asks resolved: (a) re-verified `journalctl -k` access from slot 20 (a different session than slot 33's
      original finding) — works with no `sudo`, `dmesg` still blocked (`Operation not permitted`) as before; durable,
      not a one-off quirk. (b) wired a standing script,
      `agent-orchestrator/scripts/orchestrator/check-tmux-session-lost-kernel-correlation.sh`, so future sessions don't
      re-derive the `journalctl -k` command from scratch — pulls `tmux_session_lost` events for a given slot via
      `GET /api/activity`, checks a kernel-log window around each, and classifies each as no-entries / signal-OOM-match
      / incidental-non-match. (c) ran it against 10 fresh `orch-slot-1` deaths (19:02-20:08Z) with the wider signal/OOM
      grep this todo asked for (`SIGKILL`/`SIGTERM`/`out of memory`/`invoked oom-killer`/
      `oom-kill`/`oom_kill`/`killed process`/cgroup-kill) — **zero signal/OOM matches across all 10**; 8/10 windows had
      no kernel-log entries at all, 2/10 had an incidental unrelated kernel line (another slot's own
      `strace -p ... -e trace=signal` ptrace-attach probe, not a match). Extends the sample from 4 to 14 total
      (cumulative with the original 4), all kernel-log-negative. Repo: agent-orchestrator@05acc62 (script) +
      unified-trading-pm (this doc) + Progress Log entry below.
- [x] ✅ [BACKEND] P1. **All 3 known fixes confirmed live with ZERO combined effect on kill cadence (review re-verify,
      2026-08-09 ~19:16Z, see Progress Log below) — the 3 tested mechanisms (transient has-session miss, frozen
      `SlotRow.last_ping`, undebounced `reap_orphan_agents`) are each individually patched but collectively explain none
      of the observed cadence.** Need a genuinely different investigative angle rather than a 4th single-cause guess:
      (a) repeat the `5a163e7` live-PID-capture method (proc-exists check at the instant of death) across MULTIPLE
      deaths in one sitting, not just one, to see whether the exit mechanism is uniform or mixed; (b) cross-reference
      each captured death's exact timestamp against the SQLite `database is locked` burst pattern from the ~07:54Z entry
      below (not yet checked against actual slot-1 kill timestamps) — a write-lock stall could plausibly cause a
      liveness probe to time out and misreport a live session as dead, which is a 4th, still-untested mechanism distinct
      from all 3 already patched; (c) check whether `has_session_debounced()`'s 0.25s recheck window is even sufficient
      under the observed CPU-contention levels (documented elsewhere in this doc reaching 5-8x core oversubscription) —
      a 0.25s window that felt generous at low load may itself be too short under contention, which would explain why
      the debounce fix moved the needle so little. Repo: agent-orchestrator. — DONE 2026-08-09 (slot 28,
      backend_engineer craft), all 3 sub-angles run empirically, see Progress Log entry below. (b) RULED OUT with hard
      data. (a) run cleanly (2/2 genuine deaths) and surfaced 2 new sub-findings (mixed first-detector, wide
      detection-lag variance). (c) not directly re-testable at today's calmer host load, but the lag data weakens it as
      the primary driver. New todo added below capturing the most concrete new lead this session found (a restart-window
      death despite `KillMode=process`).
- [x] ✅ [BACKEND] P1. **RULED OUT (backend, slot 20, 2026-08-09 ~19:55Z) — all 3 candidate systemd mechanisms checked,
      none explain the death; correlation is near-baseline chance. See Progress Log entry below.** Original lead text
      preserved below. **NEW LEAD (backend, slot 28, 2026-08-09 ~19:30Z): a captured genuine slot-1 death landed inside
      a `systemctl restart orchestrator` window DESPITE `KillMode=process` being deliberately configured (and confirmed
      via systemd's own log lines: "Unit process 599219 (claude) remains running after unit stopped" then "Found
      left-over process 599219 (claude) in control group while starting unit. Ignoring.") to spare tmux/claude worker
      children from exactly this.** PID 599219 was captured alive (via a live-PID poll) up to 19:30:25Z (systemd's own
      "remains running" log line) and confirmed GONE (`kill -0` fails, no `/proc` entry) at 19:30:32Z — 7s later, mid
      way through `ao-self-pull.sh`'s cron-triggered restart (old process SIGTERM'd 19:30:15Z, new process not fully
      ready until 19:30:37Z). Neither the old process (dead by 19:30:25Z) nor the new one (not yet running its
      AgentKeeper/TmuxPruner loops until ~19:30:35-37Z) can have been the direct killer via this repo's own Python reap
      paths — and `systemctl restart orchestrator` is a plain call (`scripts/ao-self-pull.sh`, no `pkill`/broader kill),
      so the mechanism is NOT in this repo's code. Full-day correlation (118 kills vs 28 restarts today):
      9.3%/13.6%/23.7% of kills fall within 120s/180s/300s of a restart respectively — a real but MINORITY factor
      (consistent with the doc's earlier ~15%/120s finding, not a new headline number), so this does not explain the
      steady ~5-9min drumbeat on its own, but it IS a concrete, reproducible anomaly against an explicit safety contract
      (`KillMode=process`'s whole documented purpose is "workers survive a backend restart"). Whoever picks this up: (1)
      reproduce deliberately — spawn a throwaway tmux+claude session, live-PID-poll it, trigger
      `systemctl restart orchestrator` (or wait for the next `ao-self-pull.sh` cron tick), see if it reliably dies; (2)
      if reproducible, check whether `ProtectSystem=strict`/mount-namespace teardown, `NoNewPrivileges`, or some other
      systemd sandboxing directive in `orchestrator.service` has a documented interaction with cgroup-resident but
      namespace-scoped child processes across a unit restart that could kill them despite `KillMode=process`; (3) if NOT
      reliably reproducible, treat this single capture as one more low-probability contributing factor rather than the
      root cause, and look elsewhere. Repo: agent-orchestrator (investigation) / `scripts/orchestrator.service` (if a
      systemd-config fix is found).
- [ ] [BACKEND] P1. **Next diagnostic step (backend, slot 20, 2026-08-09 ~19:55Z): capture the ACTUAL signal/exit status
      of a dying slot-1 process, not just its absence.** Every "genuine death" check so far (5a163e7's capture, this
      session's restart-window analysis) only confirmed the PID is GONE (`kill -0` fails / no `/proc` entry) — none
      captured HOW it died (which signal, or a clean exit). Kernel OOM, cgroup OOM, `journalctl -k`, and logind
      session-scoped kill are all now ruled out (see Progress Log below) with zero mechanism left that would explain a
      SIGKILL/SIGTERM landing on one worker's `claude` PID roughly every 5-9min fleet-wide, silently, in every log
      surface checked so far. Whoever picks this up: attach `strace -p <PID> -e trace=signal` (or equivalent, e.g. a
      tight `/proc/<pid>/stat` state-field poll, since a delivered-but-uncaught SIGKILL leaves no trace for the target
      process itself to log) to a live worker PID and wait for a natural death, to finally capture the actual signal
      number — this is the one piece of direct evidence no prior session in this doc has gathered. Also worth a fresh
      spot-check of `resource-watchdog.service`'s kill-relay log
      (`journalctl -u orchestrator | grep -i resource-watchdog` or wherever it logs) for slot 1 specifically, since the
      last check of it is now hours stale. Repo: agent-orchestrator (investigation only, unless a fix falls out of the
      captured signal).

## Progress log

- 2026-08-09 ~20:10Z (infra→backend_engineer craft, slot 20, agent-orchestrator@05acc62): Picked up the "`journalctl -k`
  is readable from a worker sandbox" BACKEND P2 todo (slot 33's original finding, 4 samples).

  **(a) Durability re-verified from a different session/slot.** `journalctl -k --since "10 minutes ago"` succeeded
  immediately from this slot-20 sandbox, no `sudo`/special grant, matching slot 33's finding exactly. `dmesg` itself
  still refuses (`Operation not permitted`) — the gap is specifically `dmesg` (reads the live kernel ring buffer
  directly) vs `journalctl -k` (reads the same data via journald, which apparently doesn't gate it the same way).

  **(b) Standing correlation check code-ified**: added
  `agent-orchestrator/scripts/orchestrator/check-tmux-session-lost-kernel-correlation.sh`. Runs directly on the
  orchestrator VM (no SSM relay needed — a worker session already runs there, confirmed via `/proc/self/cgroup` →
  `orchestrator.service`, unlike `check-ao-backlog-status.sh`/`check-on-origin-rate.sh` which are SSM-relayed for
  off-box dev machines). Pulls `tmux_session_lost` events for a target slot from `GET /api/activity`, and for each event
  runs `journalctl -k` over a `[-90s,+30s]` window (both configurable), classifying the result as
  `NO_KERNEL_LOG_ENTRIES` / `SIGNAL_MATCH` (matches a wide signal/OOM grep) / `INCIDENTAL_NON_SIGNAL_ENTRY` (a kernel
  line present but not a match — e.g. another slot's own `strace` ptrace-attach probe, so a human doesn't mistake "1
  line found" for "found the kill").

  **(c) Ran it with the wider grep this todo specifically asked for** (`SIGKILL`/`SIGTERM`/`out of memory`/
  `invoked oom-killer`/`oom-kill`/`oom_kill`/`killed process`/cgroup-kill — not just eyeballing a tail) against 10 fresh
  `orch-slot-1` `tmux_session_lost` timestamps spanning 19:02:45Z-20:08:03Z
  (`GET /api/activity?slot=1&type=tmux_session_lost`): **8/10 windows had zero kernel-log entries; 2/10 had exactly one
  incidental, unrelated kernel line each** (both were another slot's own `strace -p <pid> -e trace=signal` ptrace-attach
  probe — visible because the sibling strace/signal-capture investigation from the still-open P1 todo below happened to
  be running concurrently — not a signal delivered to the dying process). **Zero signal/OOM matches across all 10.**
  Combined with slot 33's original 4 samples, this brings the cumulative kernel-log-negative sample to 14/14 — still
  supports "genuine death, kernel not involved" over OOM/cgroup/hardware-fault causation, and now via a reusable,
  wider-grepping tool instead of a one-off manual command each session has to re-derive.

  **Unrelated observation, not chased further (out of this todo's scope)**: partway through this session the AO HTTP API
  (`localhost:8765`) briefly refused connections for ~20-30s (`curl: (7) Couldn't connect to server`) while the
  `uvicorn` process itself stayed alive (confirmed via `ps`) and host load read 16.67/14.11/14.54 — consistent with, but
  not investigated as, the same host-contention picture this doc already documents elsewhere; noted here only so a
  future session doesn't treat it as a fresh, unrelated data point if it recurs.

  Left for the next session (already captured in the existing P1 "capture the ACTUAL signal" todo below, not a new
  todo): this check only ever proves kernel non-involvement for the SAMPLED deaths — it is not, and isn't meant to be, a
  substitute for the `strace`/proc-state signal capture that todo already calls for.

- 2026-08-09 ~19:55Z (infra→backend_engineer craft, slot 20, unified-trading-pm — this doc only, no code shipped):
  Picked up the "NEW LEAD — restart-window death despite KillMode=process" BACKEND P1 todo. **RULED OUT all 3 candidate
  systemd mechanisms the todo asked about, via live evidence rather than a forced reproduction.**

  **Why no deliberate `systemctl restart orchestrator` was triggered**: that command kills the ENTIRE live fleet's
  liveness-probe surface for its duration (every slot, not just a throwaway test session) — a shared-system,
  hard-to-reverse action out of proportion to an experiment, and CLAUDE.md's own risk-assessment rule (destructive /
  shared-system actions need explicit authorization). Instead, this session used the fact that MY OWN process is itself
  cgroup-resident inside `orchestrator.service` (`cat /proc/self/cgroup` → `0::/system.slice/orchestrator.service`,
  parent PID 27677 = the shared tmux server every worker's `claude` process hangs off of) and that the orchestrator had
  JUST restarted at 19:30:25Z — the EXACT timestamp slot 28's own capture (PID 599219) was already anchored to — giving
  live, first-party access to the precise incident window without forcing a new one.

  **(1) Cgroup OOM during the restart, RULED OUT with hard evidence.**
  `cat /sys/fs/cgroup/system.slice/orchestrator.service/memory.events` → `oom 0`, `oom_kill 0`, `oom_group_kill 0` — and
  `journalctl -u orchestrator` for the exact 19:30:25Z restart line reads
  `Consumed 2h 35min 1.552s CPU time, 23.0G memory peak, 14.9G memory swap peak` (right at the `memory-cap.conf`
  drop-in's `MemoryHigh=23G` ceiling, `MemoryMax=26G`) — i.e. the cgroup came close enough to its cap for this exact
  restart to be a plausible OOM candidate, but the kernel's own cumulative oom_kill counter for this cgroup is zero.
  Confirmed the counter is genuinely cumulative-since-cgroup-creation, not reset by the restart: the cgroup directory's
  mtime is `13:22:23` (hours before 19:30:25Z) and `KillMode=process`'s whole design keeps leftover children resident,
  so the cgroup never goes empty across a restart and systemd never rmdir/recreates it — confirmed live via the SAME
  journal window: `Found left-over process 599219 (claude) in control group while starting unit. Ignoring.` alongside
  ~80 OTHER leftover processes (tmux server + every other slot's `claude`/`bash`/`git` children) surviving the exact
  same restart untouched. This directly reproduces and extends 5a163e7's prior "OOM ruled out" finding (which was scoped
  to a non-restart death) to the restart-window case specifically. **(2)
  `ProtectSystem=strict`/`NoNewPrivileges`/mount-namespace teardown, RULED OUT on mechanism grounds.** Read the full
  composed unit (`systemctl cat orchestrator`). Linux mount namespaces are reference-counted by the processes attached
  to them, not by unit-instance lifecycle — a surviving leftover process (already forked before the OLD ExecStart
  process exited) keeps its OWN reference to the namespace systemd set up at the OLD instance's start; a NEW unit
  instance starting gets a FRESH namespace for itself, and nothing in that transition unmounts or otherwise acts on the
  OLD namespace the leftover process still holds a reference to. No systemd directive in the composed unit
  (`ReadWritePaths=`, `ProtectSystem=strict`, `NoNewPrivileges=yes`, `PrivateTmp=no`) has any documented signal-sending
  side effect on out-of-scope (per `KillMode=process`) leftover processes during a sibling restart — these are
  namespace/syscall-filtering directives, not process-lifecycle directives. **(3) systemd-logind session-scoped kill
  (`KillUserProcesses=`), a NEW angle not previously checked in this doc, RULED OUT.** `loginctl list-sessions` →
  `No sessions.` — every orchestrator/worker process is pure `orchestrator.service`-cgroup-scoped (confirmed via
  `systemd-cgls`), never PAM/logind-session-scoped in the first place (no interactive login spawned them), so a logind
  session-teardown kill mechanism cannot apply regardless of the `KillUserProcesses` setting (which itself reads its
  default `no` in `/etc/systemd/logind.conf`, confirming it's not even armed). **(4) Base-rate sanity check on the
  correlation itself.** The todo's own numbers (118 kills vs 28 restarts on the day measured) imply, under a NULL
  hypothesis of independent uniformly-random kill/restart timing, an EXPECTED by-pure-chance proximity rate of
  ~7.8%/11.7%/19.4% at 120s/180s/300s windows (28 restarts × 2×window / 86400s-per-day). The OBSERVED 9.3%/13.6%/23.7%
  is only modestly above this baseline (+1.5 to +4.3 points at each window) — consistent with "a real but minority
  factor" as the todo itself already characterized it, not evidence of a dominant causal mechanism.

  **Conclusion**: per the todo's own branch (3) ("if NOT reliably reproducible, treat this single capture as one more
  low-probability contributing factor rather than the root cause, and look elsewhere") — all 3 named systemd mechanisms
  are ruled out with direct evidence, and the residual restart-correlation is statistically weak. This closes the
  restart-window angle specifically; it does NOT resolve the still-open root cause (the steady ~5-9min fleet-wide
  drumbeat, now ruled out against: OOM kernel+cgroup, `journalctl -k`, this repo's own kill paths, `/loop` process
  teardown, AND restart-window mechanisms). New follow-up todo added above capturing the one piece of direct evidence no
  session has captured yet — the actual delivered signal, via a live `strace`/proc-state capture on a natural death —
  since every prior "genuine death" confirmation (including this session's) has only ever proven the process is GONE,
  never HOW.

- 2026-08-09 ~09:16Z (backend, slot 23, agent-orchestrator@5a163e7): Picked up the standing "both prior fixes confirmed
  live but crash rate UNCHANGED" BACKEND P1 todo. Found + fixed the actual FIRST detector, then used a live empirical
  capture to settle the false-positive-vs-genuine-death question this doc had been circling for hours.

  **Method — the actual first detector.** Direct read-only SQLite query against the live `agents` table (every review
  incarnation is its own row — a fresh `register_agent` call with no known `agent_id` always inserts, never updates)
  shows EVERY observed non-superseded review-agent archival across the checked multi-hour window has
  `exit_reason='dead-tmux-session'` — the reason string ONLY `reap_orphan_agents` (`server/state_store/agents.py`)
  emits. Cross-checked against `journalctl -u orchestrator`: the "AgentKeeper reaped 1 orphan agent record(s):
  [('agt-...', 'dead-tmux-session')]" log line fires 30-45s BEFORE TmuxPruner's own "TmuxPruner cleared N stale
  tmux_session reference(s)" line, every single time sampled (checked 3 consecutive cycles: 08:10:18/08:11:02,
  08:17:56/08:18:58, 08:31:58/no separate cap-log that cycle — all same shape). `reap_orphan_agents` is called from
  `main_agent_keeper.AgentKeeper.tick_once()` (every ~60s, `main_agent_interval_seconds`) with
  `is_session_live=tmux_spawn.has_session` — the BARE, single-shot probe. TmuxPruner's own probe was debounced by
  `e32d962` (2-check, 0.25s apart); this parallel call site, doing the exact same "is this tmux session gone" job, was
  never patched — the same transient-miss class, unguarded, and (per the consistent 30-45s-earlier timing) the one
  actually driving every observed archival, not TmuxPruner.
  (`spawn_retry_cap_reached`/`spawn_heartbeat_timeout_pane_ working`, the `_auth_failover.py`/`dd01255` code path,
  checked too — their own `pane_state`/`session_alive` fields at fire-time show they're observing an ALREADY-dead
  session moments after the fact, i.e. lagging artifacts of the same death, not a second independent cause.)

  **Fix shipped (agent-orchestrator@5a163e7)**: added `tmux_spawn.has_session_debounced()` (shared SSOT, same
  0.25s-recheck-on-miss shape as TmuxPruner's existing debounce) and wired `main_agent_keeper.py`'s `reap_orphan_agents`
  call to it instead of the raw probe. 4 new tests (3 direct debounce-behavior tests in
  `test_tmux_spawn_has_session_debounce.py` + 1 wiring-regression guard in `test_main_agent_keeper.py` confirming
  `tick_once` actually passes the debounced variant, not just that `reap_orphan_agents` itself is debounce-capable).
  Full local `quality-gates.sh` green (2893 passed, 2 skipped, ruff/basedpyright clean).

  **Method — genuine death vs. false positive, settled empirically.** Set up a bounded (`run_in_background`, 30-min cap)
  monitor watching review's actual pane PID (755317, confirmed via the pane's start command using `exec claude ...` —
  the pane's shell IS the claude process, no wrapper to survive its exit) across a full death cycle: poll
  `tmux has-session` every 5s; the instant it misses, snapshot `kill -0 <PID>`, `/proc/<PID>/status`, `dmesg`,
  `journalctl -k`, and the orchestrator's own log for the preceding 90s. Result at 09:04:42Z: **PID 755317 IS GONE** (no
  `/proc` entry at all — the process genuinely exited, not merely detached from tmux). This definitively answers the
  false-positive-vs-genuine-kill branch in favor of genuine death — but genuine death by WHAT, since nothing in this
  repo's own code called `kill_session` on orch-slot-1 anywhere in the exact window (confirmed: OTHER slots'
  `kill_session(...)` calls in the SAME journal window ARE visible — orch-slot-31, orch-slot-8, orch-slot-11 — so this
  isn't a logging gap swallowing the evidence).

  **Ruled out, with hard evidence, not guesses:**
  - **OOM killer (kernel or cgroup)**, for the exact captured death:
    `cat /sys/fs/cgroup/system.slice/orchestrator.service/memory.events` → `oom_kill 0`, `oom_group_kill 0`, `max 0`
    (the cgroup never hit its hard ceiling, let alone triggered a kill) — `high 20580` confirms real, frequent soft-
    threshold PRESSURE (matches every prior "pressure=high" reading in this doc) but pressure alone kills nothing.
    Host-wide `/proc/vmstat` also read `oom_kill 0`. `systemctl is-active systemd-oomd.service` → `inactive`. **Caveat
    on scope**: `orchestrator.service` restarted at 09:00:24Z (4 min before the captured death) and the host itself has
    been up only since 08:31:14Z — both counters are fresh since those resets, so this is airtight for the 09:04:42Z
    death specifically but does NOT retroactively contradict the operator's independently-confirmed genuine OOM activity
    at 03:14Z (msg 4377 above) — that was a real event, from before this restart/reboot, at a much higher load (63-65
    vs. today's much calmer host). Two different windows, both readings stand.
  - **resource-watchdog** (the systemd RSS/swap/cpu killer, `scripts/infra/resource-watchdog/`): `claude` is NOT on its
    allowlist (`orchestrator uvicorn resource-watchdog pytest prek ruff basedpyright mypy npm vitest tsc` only), so it
    CAN target a claude process in principle — but live `ps` shows every `claude` CLI process on this host running
    ~250-400MB RSS, nowhere near its 4GB-at-high-pressure / 10GB-at-normal-pressure thresholds. 24h of
    `journalctl -u orchestrator` kill-relay logs show exactly 2 slots ever killed (14, 26) — both heavy
    `market_tick_data_service`/data-pipeline Python scripts, zero for slot 1, ever.
  - **Every explicit `kill_session()` call site in the codebase** (grepped all ~15): `WorkerLivenessWatchdog` explicitly
    exempts `review_slot_ids()` in its main reap loop AND `_reclaim_idle_lingering_sessions` AND
    `_release_prereq_blocked_slots`; `main_agent_keeper.py`'s own `kill_session` calls are ALL scoped to
    `MAIN_SESSION_NAME`; `ensure_review_agents`'s own heartbeat-silent killer (`review_agent_heartbeat_silent_respawn`)
    fired ZERO times across the full ~20h activity window checked (`GET /api/activity?slot=1&limit=500`).

  **Net effect**: the fix shipped closes a confirmed, real, previously-unpatched gap and should measurably reduce churn
  from the transient-miss class `e32d962` was built for (this call site had ZERO protection until now, not just a
  shorter debounce window) — but it does NOT explain, and will NOT fully resolve, the underlying genuine process death,
  since that death is now shown to originate OUTSIDE this repo's own Python code. Leading remaining hypothesis (Claude
  Code's fixed-interval `/loop` possibly tearing down the process between ticks) + a cheap deterministic test for it:
  new todo added above. Todo 3 (REVIEW re-verify) should stay open against a FRESH post-`5a163e7` window — expect the
  unexplained-kill RATE to drop (fewer `reap_orphan_agents`-driven pre-emptive archivals racing ahead of TmuxPruner) but
  likely not to zero, since the genuine-death mechanism itself is still unidentified.

  **Unrelated in-file fix while shipping the above**: the plan-hygiene commit-SHA-evidence pre-commit hook rejected this
  commit over slot 15's `unified-trading-pm@dab21e39c + @478105857` citation below (2 occurrences) — neither SHA
  resolves in this repo. `git log` shows the real commits are `413f5aad3` ("gate TOTAL quality-gates.sh instances, not
  just heavy phase") and `f8fcd10f1` ("wire the total-instance gate into base-service.sh/base-library.sh"), both
  timestamped 09:08:05Z — i.e. they landed ~13min AFTER slot 15's own 08:55Z doc-flip commit, so the citation was very
  likely written against a not-yet-landed SHA and never corrected once the real one existed. Corrected both citations in
  place (small, in-file, evidenced — findings-triage "in your file → fix in same commit"); no content/claim change, just
  the SHA.

- 2026-08-09 ~08:55Z (backend, slot 15, unified-trading-pm@413f5aad3 + @f8fcd10f1): Resolved the qg-host-governor
  BACKEND P1 todo (msg 4377). **Diagnosis (first step the todo asked for): GOVERNOR SCOPE GAP, not "cap too
  permissive."** Read `qg_governor_acquire`'s call site in `base-service.sh` — it brackets ONLY phase [3] TESTS + [4]
  TYPECHECK; BOOTSTRAP (uv sync), [1] AUTO-FIX, [2] LINT, and the large [5] CODEX COMPLIANCE phase (~2800 lines, lines
  1258-4081) all run with ZERO concurrency bound. Checked live host state (`bash qg-host-governor.sh --status`):
  `QG_GOVERNOR_MODE=reservation` is active fleet-wide (exported via `install-qg-governor-shell-env.sh` from
  `.env.local`, confirmed `env | grep QG_GOVERNOR_MODE` on this host), with CPU-slot admission capped at
  `cores(8) × QG_CPU_FRAC(0.80) = 6` — i.e. the governor's OWN admission logic structurally cannot admit more than 6
  concurrent heavy-phase reservations, host-wide, regardless of the todo's cited "≤2" (that number was token-mode's
  default; live state is reservation mode with K=6). Given that hard ceiling, the 12-19 concurrent `quality-gates.sh`
  PROCESSES reported in msg 4377 could not have all been holding heavy-phase tokens/reservations — at least 6-13 of them
  were structurally running ungated in BOOTSTRAP/lint/codex phases. This is direct, code-and-live-state-backed proof of
  the scope-gap branch, not the cap-too-permissive branch. **Fix shipped**: added `qg_governor_acquire_total_instance` /
  `qg_governor_release_total_instance` to `qg-host-governor.sh` — a second, independent flock-based token bucket (same
  bash-3.2-safe explicit-FD pattern as the existing heavy-phase gate, separate lock dir + FD range so the two coexist),
  default cap = physical cores (floored at 4, overridable via `QG_TOTAL_INSTANCE_CAP`), host-shared placement via the
  existing `_qg_shared_root` helper (so it works correctly across `.tabs` slot clones AND the glue-runner CI topology,
  matching the existing RAM ledger's placement rule). Wired into BOTH `base-service.sh` (services) and `base-library.sh`
  (libraries — unified-trading-library/UAC, the highest peak-RSS repos): acquired once, immediately after sourcing the
  governor (before BOOTSTRAP), released from the existing EXIT trap so every exit path (pass/fail/killed-by-signal)
  frees it — nests around the existing heavy-phase gate rather than replacing it. Also fixed a smaller adjacent gap
  found while touching `base-library.sh`'s trap: unlike `base-service.sh` (fixed 2026-07-31,
  `quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md`-adjacent trap hardening), `base-library.sh`'s
  `_qg_exit_handler` never called `qg_governor_release` on a failing/aborted exit either, so a failed library QG run
  could leak a heavy-phase reservation until the next acquirer's dead-PID sweep — fixed the same way. **Testing**: added
  `tests/test-qg-total-instance-gate.sh` (default-cap sizing incl. the cores-floor and explicit override,
  `QG_TOTAL_GOVERNOR_DISABLE` no-op, single-process acquire/release round-trip, and a REAL two-process concurrency proof
  — cap=2, two background holders fill both slots, a third acquirer genuinely blocks (verified via `timeout` rc=124)
  until a holder releases, then a fresh acquire succeeds promptly). Hit and fixed two classic bash test-harness bugs
  while building the concurrency proof (both instructive, left in the test's own comments): (1) a background job started
  inside a `$(...)` command substitution inherits the substitution's capture pipe, so the substitution silently blocks
  until that orphaned background job exits — serializing what needed to run concurrently; (2) the same subshell
  reparents the background PID away from the calling script, so `wait $pid` on it returns immediately without actually
  waiting. Fixed by backgrounding both holders directly at the script's top level (real, waitable children) instead of
  via a helper function invoked through command substitution. Re-ran the full existing governor test suite
  (`test-qg-reservation.sh`, `test-trap-release.sh`, `test-qg-watchdog.sh`, `test-qg-admit.sh`,
  `test-qg-host-capacity.sh`, `test-qg-ledger.sh`, `test-qg-mem-cap.sh`, `test-qg-governor-wait-time.sh`,
  `test-qg-running-marker.sh`, `test-qg-environment-resolution-parity.sh`, `test-qg-glue-runner-shared-root.sh`) — all
  pass except one pre-existing, unrelated timing flake in `test-qg-governor-wait-time.sh` ("contended acquire recorded
  wait=0"), confirmed pre-existing (not introduced by this change) via a clean-baseline stash comparison before touching
  any file. Also confirmed via a manual integration smoke test (source the real governor, acquire, check `--status`
  reflects the held token, simulate a crashing exit via the same trap pattern `base-service.sh` uses, confirm the token
  is released even on a non-zero exit). `quality-gates.sh` Pass-1 launched in the background per the mandatory
  non-blocking rule; will ship via quickmerge once green. Left unchecked: the standing P1 todo above this one
  (host-contention/respawn-loop feedback-loop hypothesis) is a SEPARATE, not-yet-closed investigation this fix does not
  resolve on its own — this fix bounds worst-case concurrent QG process count/RAM footprint, which should reduce (not
  eliminate) the severity of future host-capacity spikes, but the crash-cadence-vs-load DECOUPLING finding (msg
  4403/4407 above) means it is not expected to be a complete fix for the tmux-kill cadence by itself; whoever next reads
  that todo should treat this as a contributing mitigation, not a closure.
- 2026-08-09 (infra, slot 11, unified-trading-pm): Todo 6 (DOCS P3) — added a SUPERSEDED-NOTE directly under the ~00:22Z
  progress-log entry (the "12-slot simultaneous burst") correcting its "plausibly a genuine tmux-server-level event"
  hypothesis: per review's msg 4361 finding (already documented in the ~00:35Z entry below), the burst is a
  batch-processing artifact of `check_spawn_heartbeat_timeouts()` scanning all slots in one pass per tick, and only the
  review-role entry in that burst was a real loss (the other 4 were already-finished scheduled jobs,
  `archived_lifecycle_complete:true`). Original entry text kept verbatim for history, per the todo's own instruction —
  only appended a note, nothing deleted.
- 2026-08-09 ~05:25Z (main agt-22de53, relaying review msg 4403 from agt-f56131): Significant update — crash rate is
  DECOUPLED from raw host contention. Load has eased ~75% since the 03:14Z peak (14-19 vs 63-65) yet the ~5-8min kill
  cadence is completely unchanged (16 deaths in the ~2h16m window since the 03:07Z checkpoint, still 0
  `context_recycle_requested` precursors). Weakens "wait for host relief" as a sufficient fix on its own; points toward
  either a lower actual trigger threshold than assumed, or the standing feedback-loop hypothesis (AutoSpawn respawn
  churn sustaining its own load floor). Doc updated with full numbers in the BACKEND todo. No action beyond logging —
  genuinely useful data for whoever picks up the todo, not something main can resolve directly.
- 2026-08-09 ~03:16Z (main agt-22de53, relaying operator msg 4377): Severe active incident, human-confirmed and
  independently re-verified by main. 12 concurrent `quality-gates.sh` processes, load avg 63.28/60.29/57.11, 893Mi
  genuine free RAM, swap 14Gi/47Gi used, confirmed kernel OOM-killer reaping arbitrary processes (operator's own
  `sleep 60` killed). This is the same host-capacity crisis the standing BACKEND todo has been tracking via review's 4
  consecutive samples, now with the operator's own blocked task as direct evidence (QG self-aborting via its own RAM
  watchdog after passing every substantive gate). Added a new [BACKEND] P1 todo on whether `qg-host-governor.sh`'s
  heavy-phase-only cap needs to extend to total script-instance count. Replied to operator: confirmed severity, flagged
  the heavy-phase-vs-total-instance nuance (don't over-claim the governor is broken without checking held-token state
  first), suggested retrying the QG sentinel once load visibly drops rather than repeatedly mid-spike.
- 2026-08-09 ~03:10Z (main agt-22de53, relaying review msg 4376 from agt-45d610, the FOURTH review-role session in this
  window — predecessor agt-494734 died 03:02:28Z, only 2.5min before this session's own boot): trend still worsening
  (load avg 65.56/62.12/55.86, CPU %us+%sy 92-99%, 49 concurrent CLI processes) — added to the standing BACKEND todo
  along with a new hypothesis worth investigating: AutoSpawn's fast respawn design may itself be ADDING CPU load at
  exactly the moment contention is already high, i.e. a possible crash-rate/contention feedback loop, not purely
  one-directional. Not asserted as proven — flagged for whoever picks up the todo. No doc-status change.
- 2026-08-09 ~02:57Z (main agt-22de53, relaying review msg 4375 from agt-494734, the THIRD review-role session on slot 1
  in ~15min — predecessors agt-39fb1c and agt-9a70a7 both died zero-precursor `tmux_session_lost`): CPU contention trend
  is WORSENING, not stable — load average 55.23/53.25/49.41 (up from 36/44/46 in msg 4373), runnable-queue depth 39-53
  (5-6x nproc=8), 48 concurrent `claude` CLI processes (up from 27). Memory looks less acute this sample (cgroup
  ~18.7GiB/26GiB, system swap 8.4Gi used/39Gi free) — CPU/process-count is now the more acute and clearly-trending
  signal. No new mechanism, same standing conclusion (host-level relief needed, not a 3rd logic patch). No doc-status
  change.
- 2026-08-09 ~02:48Z (main agt-22de53, relaying review msg 4373 from agt-9a70a7, freshly booted on slot 1): Further
  corroboration + a new CPU-contention data point added to the open BACKEND todo (host load average 36-46 on an 8-core
  box, runnable-queue depth, context-switch spikes, 27 concurrent CLI processes) — additive to the memory/swap
  hypothesis, not a replacement. Own predecessor sessions on slot 1 died 2x since the current post-fix restart (14m12s
  and 9m39s survival), both zero-precursor `tmux_session_lost`. No doc-status change (still open, still tracking
  host-resource-pressure as primary hypothesis).
- 2026-08-09 ~02:40Z (main agt-22de53, relaying review msg 4372 from agt-2f893e's successor session): Todo 3 re-verify
  NOT resolved. Independently confirmed the ancestry claim: `dd01255` is a git-ancestor of the current root checkout
  HEAD (`6b57503`), and the running process (`systemctl status`, active since matches the restart window) postdates both
  fixes' commit times — so this is not another committed-but-not-loaded gap like the `e32d962` incident. Despite both
  fixes being genuinely live, the crash rate is unchanged (~100% unexplained kills across a fresh 87min window). Added a
  new [BACKEND] P1 todo capturing the host-memory-pressure pivot per review's recommendation — keeping todo 3 open, NOT
  marking it resolved, since a 3rd liveness-logic patch is unlikely to help without host memory relief first.

- 2026-08-09 (backend, slot 26, agent-orchestrator@dd01255): Fixed the second, distinct root cause (the "second,
  distinct root cause found" BACKEND P1 todo, review msg 4361) — picked option (b) from the 3 choices the todo left
  open: `check_spawn_heartbeat_timeouts()` (`server/worker_liveness/_auth_failover.py`) now also consults the bound
  `AgentRow.last_ping` (via `state_store.find_active_agent_for_session`, matched on `slot.tmux_session`) as a second
  evidence source before treating a slot as spawn-timed-out — same bar as the existing `SlotRow.last_ping` check (the
  agent's ping must postdate the spawn). Chose (b) over (a) (editing review.md/main.md/the typed-one-off prompt
  templates to add a slot-heartbeat call to every tick — more surface area, prompt-doc-enforced not code-enforced) and
  over (c) (exempting `pane_state=="idle"` alone — narrower, only covers the idle-pane symptom and not e.g. a case where
  the pane capture itself is transiently unavailable while the agent is demonstrably still polling). (b) is a single
  code-only change in the one function that owns this verdict, applies uniformly to review/main/any future chat-loop
  role without touching their prompt docs, and is fully unit-testable. Added
  `test_chat_loop_agent_last_ping_spares_slot_with_frozen_slot_ping` (proves a live AgentRow's fresh last_ping spares
  the slot even with `SlotRow.last_ping` frozen at spawn and `has_session` mocked False) and
  `test_stale_chat_loop_agent_last_ping_does_not_spare_slot` (proves an AgentRow ping that predates the spawn does NOT
  spare it — only a post-spawn ping counts, same bar as the SlotRow check) to `tests/test_spawn_heartbeat_liveness.py`.
  Full local `quality-gates.sh` green (2859 passed, ruff/basedpyright clean). Todo 3 (REVIEW re-verify) can now proceed
  against BOTH root causes (the debounce fix, todo 1/2, and this one) — still left for review craft per its own scope.
- 2026-08-09 ~01:04Z (main agt-22de53, relaying review msg 4365 from agt-252692, a fresh slot-1 session): Live, ongoing
  confirmation of todo 5 — `spawn_heartbeat_timeout_pane_working` firing repeatedly against THIS session
  (`00:58:59Z`/`00:59:41Z`/`01:01:04Z`/`01:02:13Z`, `elapsed_s` climbing 192→234→317→386s), `pane_state:working` each
  time (so still spared), confirming `SlotRow.last_ping` stays frozen despite the session's own `/api/agents/{id}/poll`
  calls, exactly as diagnosed. Reporter explicitly considered and correctly declined a self-mitigation
  (`/api/slots/1/heartbeat`) since that endpoint can dispatch a real backlog task to an idle review slot — unsafe,
  review must never pull backlog work. No new action from main; recording only, per the reporter's own request in case
  their session dies before they can log it themselves.
- 2026-08-09 ~00:35Z (main agt-22de53, relaying review msg 4361 from a fresh slot-1 session): Second, distinct
  root-cause hypothesis, code-confirmed (not guessed) from live agent-orchestrator source — see new todo 5 above for the
  full chain (`check_spawn_heartbeat_timeouts` gates on `SlotRow.last_ping`, which review's poll-only loop never
  advances; `pane_state=="idle"` isn't exempted like `"working"` is). This ALSO self-corrected my own ~00:22Z entry
  below: the "12-slot simultaneous burst" is a batch-processing artifact of that same function scanning all slots in one
  pass per tick, not a tmux-server-level event — see new todo 6. Confirmed via review's own slot-1 history: 5x
  `tmux_session_lost` since 23:44:42Z spanning both post-`e32d962` restarts with unchanged cadence, i.e. the debounce
  fix (todo 1/2, already shipped) addressed a different code path and does not resolve this. Reopened todo 3 (re-verify)
  explicitly — it must wait for todo 5, not just the already-shipped debounce fix. No action taken beyond documenting;
  review flagged this as read-only code+data analysis, scoping the actual fix is left to whoever picks up todo 5.
- 2026-08-09 ~00:22Z (main agt-22de53): Data point for the open REVIEW re-verify todo (todo 3) — a routine stall sweep
  found `GET /api/activity` reporting 12x `tmux_session_lost` (slots 1,4,5,11,12,13 + 6 unattributed) all at the EXACT
  same timestamp (`00:21:27.90x`Z, sub-millisecond apart), i.e. a simultaneous fleet-wide burst, at `00:21:27Z` — 4min
  AFTER the orchestrator restart at `00:17:31Z` that loaded `e32d962`. AutoSpawn already recovering normally (slot 4/8
  `autospawn_succeeded` + `slot_boot` within seconds, no `spawn_retry_cap_reached`/`slot_resume_exhausted`). Flagging
  because a simultaneous multi-slot burst at one instant is a DIFFERENT signature than the single-session
  has-session-miss the debounce fix targets — plausibly a genuine tmux-server-level event (not a per-session liveness
  false-positive), which the fix may not address. Leaving todo 3 to review's fresh-window judgment rather than
  pre-empting it, but wanted this specific data point on record before it ages out of the activity log.

  > **SUPERSEDED-NOTE (2026-08-09, per the ~00:35Z entry below and todo 6)**: the "genuine tmux-server-level event"
  > hypothesis above was WRONG. Review (msg 4361) determined the 12-slot simultaneous burst is a batch-processing
  > artifact of `check_spawn_heartbeat_timeouts()` scanning all slots in one pass per tick, not a tmux-server-level
  > event. Only the review-role entry in that burst was a real loss — the other 4 were already-finished scheduled jobs
  > (`archived_lifecycle_complete:true`). Kept for history, not deleted — see the corrected finding below.

- 2026-08-08 ~23:45Z (main agt-22de53): Review (msg 4359) found `agent-orchestrator@e32d962` shipped+`slot_done` at
  23:32Z but not live (`server_started:23:15:31Z` predates the commit) — corroborated by review's own slot-1 session
  hitting `tmux_session_lost` at 23:35:07Z (3min post-shipped) while genuinely alive, plus a fleet-wide kill burst
  23:25-23:35Z (slots 1-12). Verified independently: `systemctl status orchestrator` confirmed PID 885271 since
  23:15:22Z; `git log` in the orchestrator checkout confirmed HEAD=e32d962, clean. Attempted the restart myself — both
  `sudo systemctl restart orchestrator` and the sudoless form both blocked by this session's sandbox
  (`no new privileges`/`Interactive authentication required`), not a policy decision main is choosing not to act on.
  Added an `[OPERATOR]` todo above requesting the restart directly. Replied to review confirming the diagnosis and
  explaining why main couldn't self-serve it.
- 2026-08-08 (main agt-22de53): Filed from a review-craft chat report (msg 4310) that review declined to file itself
  (doc-authoring is outside review's scope). Not independently re-verified against `/api/activity` by main before filing
  — relaying the reporter's evidence as given, since it was already a direct, timestamped `/api/activity` query result,
  not a self-report needing corroboration. Cross-linked the compounding `boot_read_unconfirmed` finding into the
  existing `review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md` doc instead of duplicating it here.
- 2026-08-08 ~17:36Z (main agt-22de53): Live corroborating data point, NOT slot 1 — during a routine stale-slot check,
  slots 11 and 13 both independently hit the same `forced_precompact`→`forced_compact`→`worker_kick_failed` sequence
  within the same ~5min window (slot 11: kicks failed 17:33:54Z and 17:35:50Z, ~4min after its 17:31:53Z compact; slot
  13: one failed kick at 17:36:03Z, ~4min after its 17:31:55Z compact). This broadens the pattern from "review role /
  slot 1 only" to a fleet-wide post-compact respawn issue — same `worker_kick_failed` signature the todo above already
  asks to investigate. Slot 11 escalated via `reassign kill_worker:true` per standing policy (2 failed kicks, no
  recovery) — task `solana_dex_pool_swaps_indexer-002` returned to queue cleanly. Slot 13 held one more tick (only 1
  failed kick so far) before escalating. Does not change scope/priority of the existing todos, just adds evidence that
  the root-cause investigation (todo 1) should look at the post-compact respawn path generally, not review-role-specific
  logic.
- 2026-08-08 ~17:47Z (main agt-22de53): Possible task-affinity angle, worth todo-1's attention —
  `solana_dex_pool_swaps_ indexer-002` (the same task released from slot 11 above) was picked up by autospawn on slot 9
  at 17:41:55Z, then hit the identical
  `forced_compact_ineffective`(17:42:22Z)→`forced_precompact`→`forced_compact`(17:43:28Z) sequence, then went silent
  (`worker_alive` flipped false, `context_reading_stale` true, no further activity) for 5+ min with no explicit
  `worker_kick_failed` event ever logging — escalated on the `worker_alive:false` + staleness signal alone since the
  wedge was otherwise unambiguous. This is the SECOND consecutive wedge on this exact task across two different slots
  (11, then 9) — same as the standing `tardis_impossible_combinations` mitigation note (see
  `tardis_impossible_combinations_recorded_as_attempted_failed_2026_07_17.md`), a repeat-wedge on the same task across
  slots can mean `reassign`'s `affinity=high` re-poisons the next slot rather than the slot itself being at fault. Used
  `reassign kill_worker:true` again here (task returned to queue, `released_task_affinity:"high"`) — if this task wedges
  a THIRD slot, switch to `skip-current-task` instead of `reassign` per the tardis precedent, and consider filing a
  dedicated task-specific issue rather than continuing to treat it as generic fleet evidence here.
- 2026-08-08 ~17:49Z (main agt-22de53): Rate observation — since the 17:36Z entry above, the same confirmed signature
  (`slot_boot`→`forced_precompact`→`forced_compact`→silent/`worker_alive:false`, no recovery) has now hit slots 9, 24,
  25, and 26 across 5 consecutive ~60s ticks (17:36-17:49Z), i.e. roughly one new wedge per tick, each on a different
  task/slot with no task-family overlap between them (solana indexer, 2x sports_taxonomy, ao_satellite, citadel
  satellite) except the one same-task repeat already logged above. This reads as a genuine fleet-wide acceleration, not
  sporadic noise — every wedge escalated cleanly via `reassign kill_worker:true` with the task returned to queue, so
  there is no user-visible stall, but the respawn/compact churn rate is real and climbing. Not paging the operator
  separately (this doc is already P1 with a BACKEND todo assigned and the rate itself doesn't change root-cause scope),
  but flagging the acceleration here so whoever picks up todo 1 has the full frequency picture, not just the original
  3-instance sample.
- 2026-08-08 ~19:49Z (main agt-22de53, relaying review msg 4345): New evidence narrowing todo 1's liveness-probe-vs-
  genuine-kill question, specific to review-role (slot 1) sessions. Review's own live session logged a
  `tmux_session_lost` (`killed`) activity event at 19:37:43Z despite being continuously alive throughout — single agent
  registration, no respawn, review-tick work continuing uninterrupted both before and after the event, and `tmux_alive`
  staying `true` the whole time. Review's hypothesis: `worker_alive` tracks **backlog-worker heartbeat cadence**, which
  a review-tick session legitimately does not follow (review polls/ticks on its own cadence, not the standard
  dispatched-worker heartbeat) — so the kill classification may be a false positive specific to the review role's
  different heartbeat shape, not a genuine external kill or resource-pressure event. This is a concrete, first-party
  data point supporting the "liveness-probe timing/false-positive" branch of todo 1 (vs. the "genuine external kill"
  branch) — whoever reads the TmuxPruner/keeper source for todo 1 should specifically check whether the liveness check
  is worker-heartbeat-based (and thus structurally mismatched for the review role) rather than tmux-session-based.
  Review flagged but did not chase further this tick; not independently re-verified by main beyond relaying the report.
- 2026-08-08 ~20:22Z (main agt-22de53): Possible server-restart correlation, worth todo 1's attention. Observed a brief
  AO server connection-refused blip around ~20:15Z (uvicorn process PID changed between checks — 2920882 -> 3694559,
  `ss -tlnp` confirmed the new PID bound port 8765; recovered within ~15s, no fleet-visible gap). Shortly after, 3 slots
  (4, 7, 8) that all booted within the same ~5s window (20:17:23-20:17:28Z, autospawn_succeeded/task_dispatched/
  slot_boot all clustered) went completely silent afterward — no `forced_compact`, no `slot_progress`, nothing at all
  for 4:40+ min, a DIFFERENT failure signature from the tracked `forced_precompact`->`forced_compact`->silent pattern
  (no compact ever fired here). All 3 escalated cleanly via `reassign kill_worker:true`, tasks returned to queue, no
  user-visible stall. Hypothesis for whoever picks up todo 1: sessions that were mid-boot at the moment of the server
  restart may have had their initial heartbeat/registration silently dropped (server-side connection reset mid-boot),
  producing dead-on-arrival sessions with no compact signature since they never got far enough to need one — distinct
  from, but possibly a variant of, the main tracked pattern. Not independently confirmed (no access to server-side
  connection logs from main's vantage point), just flagging the timing correlation as a data point.
- 2026-08-08 ~21:02Z (main agt-22de53, relaying review msg 4348 from a fresh review session agt-3b8cf4): Substantial new
  evidence, WORKER-side this time (not review-role) — rules out the review-only heartbeat-mismatch hypothesis (msg 4345,
  ~19:49Z entry above) as the SOLE explanation, since these are standard dispatched workers on the normal `/progress`
  cadence, not review's odd cadence. Three findings:
  1. **Historical (04:35-14:21Z today, tasks now done)**: `sports_taxonomy_p1_capture_and_contracts-006/-008/-009` died
     mid-task via `tmux_session_lost` 20x/21x/18x respectively before finally completing — **59 total mid-task deaths**
     just from these 3 items, spread across ~16 different slots (2,3,4,5,7,8,9,10,12,13,14,15,16,19,21). Final shipped
     diffs for all 3 were small (contract-constant + test additions), so the deaths cluster in the research/exploration
     phase, not the fix itself. The sibling plan doc separately already cites a related but distinct Cloud-Run-side OOM
     crash-loop for `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01.md` (fixed via a memory bump) — this domain
     runs adjacent to memory-hungry ops generally, supporting a resource-pressure (not pure
     liveness-probe-false-positive) explanation for at least this cluster.
  2. **Live at report time**: `defi_venue_lst_rates_residual-001` (a heavy-I/O bare-SUSHISWAP GCS enumerate/migrate
     todo) died via `tmux_session_lost` 3x in a row — slot5@20:20:00Z, slot5@20:33:57Z, slot10@20:43:38Z — each within
     1-13 min of dispatch, always shortly after the worker spawned a research sub-agent to survey the venue registry
     (i.e., right at a resource-intensive step, consistent with the memory-pressure hypothesis). A 4th attempt (slot16,
     dispatched 20:53:19Z) was independently confirmed by main via `/api/activity` to have survived past a
     `worker_kicked` recovery at 20:56:31Z with no further death through 21:02Z — longer than any prior attempt. Only 2
     DISTINCT slots (5, 10) have actually failed so far, short of the standing 3-distinct-slot park threshold — main is
     letting this 4th attempt run rather than parking preemptively, will park if it also dies.
  3. **Lower-signal**: `cefi_chain_drop_root_cause_and_heavy_io_vm_rule-eb1bc482b1f7` tmux-died twice in the same window
     (slot10@20:21:02Z, slot12@20:24:14Z) but its 2 most recent encounters were clean explicit skips (correctly
     self-diagnosed as blocked on sibling issue docs), not crashes — mentioned for completeness only.

  Review checked `plans/active/issues/` for an existing doc on this specific worker-side pattern before reporting —
  found none beyond the two P1 docs already tracked here, so this is folded into THIS doc's log rather than a new
  filing. Review does not have dmesg/journalctl host access from its sandbox, so this remains activity-log pattern
  evidence, not a kernel-level OOM confirmation — todo 2's host-memory-exhaustion correlation check (against
  `orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md`) is the natural next step for whoever has host
  access. Acked back to review; not independently re-verified by main beyond the slot-16 activity-log cross-check.

- 2026-08-08 ~21:32Z (main agt-22de53): Strengthened server-restart correlation evidence — a CLEAN 3/3 confirmation,
  upgrading the ~20:22Z entry's "possible correlation" from a partial (3-of-many) sample to a complete cluster. A 4th
  brief AO connection-refused blip was observed ~21:29-21:30Z (uvicorn restart, ~9s downtime). All 3 slots that booted
  in the immediately-following ~65s window (18 @21:27:02Z, 19 @21:27:31Z, 20 @21:27:05Z) — no other slots booted in that
  window — went completely silent afterward and were escalated via `reassign kill_worker:true` at 4:00-4:47min
  post-boot, zero exceptions, zero survivors. Same signature as the ~20:22Z cluster (`slot_boot`->`task_dispatched`, no
  `forced_compact` ever fires, no `slot_progress`, nothing). This is now the SECOND independent full-cluster observation
  (100% failure rate both times) tying a boot-during/immediately-after-restart window to this silent-death variant —
  meaningfully stronger than a coincidence hypothesis. Whoever picks up todo 1 should specifically correlate `slot_boot`
  timestamps against AO server restart/redeploy timestamps (visible in systemd/journalctl for the uvicorn unit) as a
  primary lead, not just a background note.
- 2026-08-08 ~22:42Z (main agt-22de53, relaying review msg 4353 from a fresh review session agt-896798): Severe
  escalation of the original finding, sustained not resolved. Since the 16:45Z checkpoint (Tick 132, ~6h ago): 28x
  `tmux_session_lost` vs only 2x `context_recycle_requested` for slot 1 — the same ~93% unexplained-kill ratio,
  sustained far longer than the original 22-in-2h sample. New and more severe: 16+ distinct review-role
  `agent_registered` events in that same window, and **NONE completed a full tick cycle** —
  `review-agent-checkpoint.md`'s last entry is still Tick 132. That is 100% infant mortality for review continuity since
  16:45Z, not merely elevated churn — 3 review agents died in the last 30 min alone before this report's author. Review
  separately flagged (correctly, outside its own scope to act on) that todo 1 was `assigned_vm: NA` /
  `execution_scope: local-only`, meaning it was NEVER in the AO auto-dispatch pool despite being a bounded,
  determinable-outcome investigation (read TmuxPruner/keeper source, diagnose liveness-probe-false-positive vs
  genuine-kill) — likely why it sat untouched 6h. Main confirmed this diagnosis is correct (checked a comparable
  AO-dispatched issue doc's frontmatter convention: `assigned_vm: planning` pairs with
  `execution_scope: orchestrator-agent`, not `local-only`) and flipped this doc's frontmatter accordingly so a worker
  can now be auto-dispatched to todo 1. Given the severity (100% review-role continuity failure, sustained 6h, a real
  ongoing fleet-availability cost) this crossed the bar for a direct main-agent fix rather than just relaying — not a
  new-plan-creation decision (which defaults to human per the ASK-BEFORE-CREATING HARD RULE), just correcting an
  existing bounded, already-P1, already-approved investigation todo's dispatch eligibility.
- 2026-08-08 (backend, slot 2, agent-orchestrator@e32d962): Dispatched todo 2 (only todo in the AO-dispatch pool at
  pickup time — todo 1 sat `queued`/`target_slot: 3`/`affinity: high` unclaimed). Todo 2's own text branches on todo 1's
  root-cause finding, so did todo 1's investigation first as a prerequisite; flipping both here since both are now
  genuinely done (no `sequential: true`/`depends_on` linked them, which is why the dispatcher offered todo 2 before todo
  1 — worth noting for future conditional-todo authoring, but out of scope to fix here). **Root cause (todo 1)**:
  `tmux_session_lost` is emitted ONLY by `TmuxPruner.prune_once()` (`server/tmux_pruner.py`), gated purely on a single
  `tmux has-session` subprocess call returning nonzero — it does NOT consult `worker_alive`/heartbeat cadence at all
  (that field lives in `routes/state.py`/`stale_dispatch.py`, never read by TmuxPruner). Review's own
  `worker_alive`-heartbeat-cadence-mismatch hypothesis (msg 4345, ~19:49Z entry above) does not match this code path — a
  plausible-sounding but incorrect theory, worth flagging so it isn't re-chased. The actual first-party evidence in that
  SAME entry (a review session flagged killed while continuously alive, single agent registration, no respawn,
  `tmux_alive` true throughout) is direct proof of a transient `has-session` false-negative — a single miss on the
  shared tmux server (dozens of slots' spawn/capture-pane/ send-keys/has-session calls all racing one tmux server
  process) does not mean the session is actually gone. **Fix (todo 2, false-positive branch)**:
  `TmuxPruner._confirm_session_dead()` now requires a second `has-session` miss (0.25s later) before a slot/agent is
  declared dead, for both the slot and agent death paths in `prune_once()`. A genuinely dead session stays dead on the
  recheck (unaffected); a transient blip self-heals. Added `test_transient_has_session_miss_does_not_kill_live_slot`
  (proves the debounce absorbs one miss) and `test_sustained_has_session_miss_still_kills_slot` (proves a real death is
  still caught) to `tests/test_tmux_pruner_agent_reap.py`. Full local QG green (2823 passed). **Resource-pressure branch
  (todo 2)**: separately, review's worker-side evidence (sports_taxonomy/defi_venue heavy I/O tasks dying via
  `tmux_session_lost` clustered around memory-intensive research sub-agent spawns) is a DIFFERENT population from the
  review-role false positives above — consistent with genuine host memory pressure, not a liveness-probe bug. That
  population is already tracked (matches the "simultaneous tmux-session loss on slots 1/5/10" signature) in
  `/plans/active/issues/orchestrator_host_memory_exhaustion_4th_recurrence_2026_08_02.md` (open, P1) — no new issue doc
  filed, per todo 2's own instruction to check that doc first. The server-restart-correlated silent-death variant
  (~20:22Z/~21:32Z entries above, no `forced_compact` ever fires) is a THIRD distinct mechanism this fix does NOT
  address — it's a boot-time registration race with a uvicorn restart, not a `has_session()` false-negative on an
  established session. Left for a follow-up if it recurs; flagging here so todo 3's re-verification isn't surprised if
  that specific variant's rate doesn't drop. Todo 3 (independent re-verification via `/api/activity?slot=1` over a fresh
  2h+ window) is `[REVIEW]`-scoped — left unchecked for review craft to pick up now that a fix has actually landed.

- **context-scout 2026-08-09**: populated/refreshed context_scope (2 entries).
- 2026-08-09 ~05:24Z (review agt-f56131, relayed by main agt-22de53 msg 4403): Fresh decoupling data point against the
  host-resource-pressure hypothesis. Since Tick 134 checkpoint (~03:07Z) through ~05:23Z (~2h16m window): still 16x
  `tmux_session_lost` / 0x `context_recycle_requested` for slot 1 — 100% unexplained-kill rate, unimproved. Host
  contention has eased substantially since the operator's 03:16Z peak report: load avg now 14.29/13.30/18.86 (was
  63-65), `quality-gates.sh` processes now 5 (was 12-19), `claude` CLI processes 37 (was 49), swap 12Gi/47Gi used (was
  14Gi) — roughly a 75% drop from peak. But the kill CADENCE is unchanged: still landing every ~5-8min
  (04:39/04:47/04:55/05:03/05:08/05:15Z), same as during the peak-load window. This argues against "just wait for host
  relief" being sufficient on its own, and toward either (a) the actual trigger threshold being lower than assumed —
  today's still-elevated-but-much-lower load (~2x core oversubscription vs peak's 7-8x) is apparently already enough, or
  (b) the standing feedback-loop hypothesis (msg 4376, cited in an earlier entry above) where AutoSpawn's own respawn
  churn sustains a load floor independent of the wider host's swings. Reporting session had no dmesg/journalctl access
  (confirmed permission-denied) so could not independently check current kernel OOM-killer activity. Not asserting a new
  root cause — flagging the load/cadence decoupling as a fresh data point for whoever picks up the open `[BACKEND] P1`
  todos.
- 2026-08-09 ~05:39Z (review agt-457acf, relayed by main agt-22de53 msg 4407): STRONGER decoupling signal — host is now
  fully back to baseline, not just eased. Fresh session booted ~1min after the last kill (05:35:07Z). Load avg
  7.42/9.25/12.97 on nproc=8 — the 1-min figure is essentially AT capacity, no CPU oversubscription at all (vs
  14.29/13.30/18.86 at 05:24Z, vs 63-65 at the 03:14Z peak). `quality-gates.sh` processes 3 (was 5, was 12-19 at peak),
  `claude` CLI processes 36 (was 37), mem 9.4Gi/30Gi used with 21Gi available (genuinely healthy), swap 11Gi/47Gi (was
  12-14Gi). Slot-1 kill cadence over the trailing ~30min (all zero-precursor `tmux_session_lost`, via
  `/api/activity?slot=1`): 05:08:27, 05:15:49 (+7m22s), 05:25:19 (+9m30s), 05:35:07 (+9m48s) — spacing maybe very
  slightly widening (7-10min vs the earlier 5-8min) but still firing at essentially-baseline host load. This further
  weakens the pure host-contention hypothesis: the host is no longer oversubscribed on CPU AT ALL, yet the kill cadence
  continues largely unabated. Strengthens the standing feedback-loop hypothesis (msg 4376) relative to "wait for host
  relief" as the fix.
- 2026-08-09 ~07:54Z (main agt-22de53): New mechanism candidate, found via direct `journalctl -u orchestrator` access
  (main has this; review sessions have confirmed they don't). A burst of 30x
  `sqlite3.OperationalError: database is locked` fired across `WorkerLivenessWatchdog`, `PlanReconcilerLivenessCanary`,
  `RepoHealthWatcher`, and the auto-snapshot tick, all within a ~2min window (07:51:36-07:53:37Z), plus one
  `SQLite backup to S3 failed ... database or disk is full` at 07:52:51Z. Orchestrator process itself did NOT restart
  (same PID, uptime unaffected) — this is live lock contention on `data/state/state.db`, not a crash. `/tmp` (tmpfs) was
  at 89% used / 980M avail at check time — plausible source of the transient "disk is full" (the S3 backup likely stages
  a copy there); root disk itself is healthy (72%, 193G avail). Burst had already subsided by the time this was found
  (no recurrence in the trailing 5min). Correlates with this same tick's `/api/state` sweep showing MANY slots
  (2/3/12/13/15/18/21/23/24, not just the usual slot 1/26/27) simultaneously stale by 1.6-2.2h — plausibly
  WorkerLivenessWatchdog/heartbeat writes silently failing under this same lock contention rather than genuine per-slot
  staleness. Not claiming this IS the crash-loop root cause (the burst is minutes-scale, the kill cadence is a sustained
  hours-scale pattern), but it's a concrete, measurable shared-resource-contention mechanism worth checking against
  slot-1's specific kill timestamps if this recurs — unlike raw CPU load (already shown decoupled above), SQLite
  write-lock stalls could plausibly cause a liveness probe to time out and misreport a session as dead even while the
  underlying tmux session is fine.
- 2026-08-09 ~10:27Z (backend, slot 33, review→backend_engineer craft) — `/loop` PROCESS-TEARDOWN HYPOTHESIS FALSIFIED,
  EMPIRICALLY. Ran the exact test the standing BACKEND P1 todo specified: throwaway tmux session, fresh `--session-id`,
  `/loop 60s reply with exactly the word: tick`, PID sampled every 10s across 2 full ticks (~2.5 min). PID `1400154`
  never changed. `/loop` in Claude Code 2.1.202 is a session-scoped `CronCreate` job firing inside the live process, not
  a teardown/relaunch cycle — the pane's own output says so explicitly ("Session-only — it stops if this session ends").
  This rules out the CLI-level `/loop` mechanism entirely; no `review.md` boot-prompt fix or agent-orchestrator code fix
  is warranted from this angle. Per the todo's own fallback, checked `dmesg`/`journalctl -k` access from this sandbox:
  `dmesg` still blocked, but **`journalctl -k` works** — a previously-undiscovered capability. Checked 4 fresh, exact
  `orch-slot-1` `tmux_session_lost` timestamps (10:26:19Z, 10:14:20Z, 10:09:04Z, 09:54:19Z) against it: zero kernel-log
  entries in any window, adding 4 more kernel-negative samples to the "genuine death, not kernel-visible" evidence
  already established by `agent-orchestrator@5a163e7`'s live-PID-capture method. Cross-referenced the most recent death
  against `journalctl -u orchestrator` and confirmed the already-identified `AgentKeeper reap_orphan_agents`
  (`5a163e7`'s fix target) is still the correct proximate detector (fired 2.6s before the activity event, same shape as
  previously documented). New `[BACKEND] P2` todo added above capturing the `journalctl -k` access finding for the next
  investigator — did not chase the underlying "why does the process actually exit" question further, since that's
  outside this todo's own stated scope. No code shipped (this doc only) — the falsified hypothesis needed no fix, and
  the access finding is itself the deliverable for the next todo.
- 2026-08-09 ~19:16Z (review, slot 19) — **Todo 3 re-verified: NOT resolved, rate unchanged from pre-fix baseline.**
  Confirmed all 3 landed fixes are live for the ENTIRE measured window before pulling data:
  `git merge-base --is-ancestor` confirms `e32d962`/`dd01255`/`5a163e7` are all ancestors of the current
  `origin/live-defi-rollout` HEAD; `journalctl -u orchestrator` shows the orchestrator restarts roughly every 15-45min
  (21 restarts observed 09:00-19:00Z, itself a new data point — see below), and the first restart at/after `5a163e7`'s
  09:11:07Z commit time was 09:30:29Z, so used that as the clean-window start rather than the raw commit timestamp.

  **Data**: `GET /api/activity?slot=1&type=tmux_session_lost&since=2026-08-09T09:30:29Z` (paginated to `limit=500`, well
  under the cap) returned 67 events spanning 09:39:11Z → 19:15:20Z (9.6h). The matching `type=context_recycle_requested`
  query over the identical window returned **0** events — i.e. 100% of deaths in this fresh post-fix window are still
  unexplained kills, same as the original 22-in-2h sample that opened this doc. Cadence: median inter-kill gap 507s
  (~8.5min), min 64s, max ~21.5min, effectively 1 kill per 8.6min averaged over the full 9.6h — statistically
  indistinguishable from the documented pre-fix baseline (~5-8min) and from the post-`5a163e7`-but-pre-full-verification
  05:39Z sample (7-10min). **Verdict: the hoped-for "near-zero" outcome this todo was gated on did not materialize** —
  all 3 patched mechanisms (transient has-session miss debounce, frozen-`SlotRow.last_ping` heartbeat exemption,
  undebounced-first-detector fix) are confirmed live and combined produced no measurable change in kill cadence.

  **New angle checked, ruled minor**: cross-referenced the 67 kill timestamps against the 21 orchestrator restart
  timestamps in the same window (the doc's earlier ~20:22Z/~21:32Z entries flagged restart-proximity as a possible 3rd
  mechanism) — only 10/67 (~15%) fall within 120s of a restart, so frequent restarts are a contributing minority factor
  at most, not the dominant driver of the steady ~8.5min drumbeat.

  Per this todo's own "verification + checkbox flip only" scope, flipped the checkbox above with this finding rather
  than leaving it open indefinitely — the specific re-verification action asked for is conclusively complete (answer:
  no, not resolved), mirroring how todo 5's falsified-hypothesis result was checked off with its negative finding rather
  than left open. Added a new `[BACKEND] P1` todo above synthesizing next steps given all 3 single-cause hypotheses
  tested so far are individually patched with zero combined effect: multi-death live-PID capture in one sitting,
  cross-referencing kill timestamps against the SQLite lock-contention burst pattern (~07:54Z entry, not yet checked
  against actual slot-1 kill times), and questioning whether the existing 0.25s debounce window is itself too short
  under the CPU-contention levels documented elsewhere in this doc. Did not attempt a 4th fix myself — genuinely outside
  `[REVIEW]` scope and the remaining hypotheses need code-level investigation `[BACKEND]` craft owns.

- 2026-08-09 ~19:37Z (backend, slot 28) — Ran all 3 of the standing todo's sub-angles empirically. **(b) SQLite
  lock-contention correlation: RULED OUT.** Pulled all 118 `tmux_session_lost` timestamps for slot 1 today
  (`GET /api/activity?slot=1&type=tmux_session_lost&since=2026-08-09T00:00:00Z`) and all 20 distinct
  `database is locked` burst timestamps from `journalctl -u orchestrator` (deduped to the second; host confirmed
  `Etc/UTC` so no tz conversion needed) — **0/118 kills fall within 30s of any lock event**; the nearest gaps observed
  were 163-330s (2.7-5.5min), and lock bursts (20/day) are far rarer than kills (118/day) besides. This mechanism does
  not explain any material fraction of the observed cadence.

  **(a) Multi-death live-PID capture, run twice in one sitting.** This host's shared tmux server is directly reachable
  from this slot (same as `5a163e7`'s method), so ran a bounded (`run_in_background`, 30min cap) poll of
  `tmux has-session -t =orch-slot-1:` every 2s, snapshotting the pane's PID on every appearance and running
  `kill -0 <pid>` the instant the session vanished. Caught 2 fresh deaths: PID 599219 (alive 19:28:29Z-19:30:32Z,
  ~2m03s) and PID 754711 (alive 19:31:50Z-19:34:03Z, ~2m13s) — **both confirmed GENUINE process death** (`kill -0`
  fails, no `/proc/<pid>` entry), same verdict as `5a163e7`'s single sample. This answers the todo's own question: the
  exit mechanism is UNIFORM (2/2 genuine), not mixed, across this fresh sample.

  Two NEW sub-findings fell out of capturing exact death instants and comparing them to the recorded activity-log
  timestamps: **(i) the proximate detector is NOT consistently `reap_orphan_agents`** — both of these 2 deaths were
  actually reported by `TmuxPruner` ("TmuxPruner cleared N stale tmux_session reference(s)"), not AgentKeeper's
  `reap_orphan_agents` (which ran its own ticks at 19:30:37Z/19:31:57Z/19:33:17Z in this exact window but reaped
  unrelated agents each time) — contradicting `5a163e7`'s "every single time sampled" finding from its own 3-sample
  check. Both loops tick every 60s independently; which one's tick lands closer after a given death determines which one
  "wins" the race to report it, so the earlier finding was a real but non-universal pattern, not a fixed ordering.
  **(ii) Detection lag (true death → recorded activity-log timestamp) varies by roughly an order of magnitude**: 14s for
  the first death (activity ts 19:30:46.457Z vs true death 19:30:32.256Z) vs 102s for the second (activity ts
  19:35:45.331Z vs true death 19:34:03.473Z). This matters for angle (c) below and for any future timestamp-correlation
  analysis in this doc (like the DB-lock check above) — the recorded `tmux_session_lost` timestamp can lag the true
  death by well over a minute, so tight-window correlations against it carry that much slop. (The DB-lock ruling-out
  above still holds even after accounting for this: observed gaps of 163-330s exceed even the 102s worst-case lag by a
  wide margin.)

  **(c) Debounce-window-sufficiency: not directly re-testable today** — host load at test time was calm (load avg ~10-17
  on `nproc=16`, i.e. roughly at-to-slightly-over 1x, not the 5-8x oversubscription windows documented elsewhere in this
  doc), and a bare `tmux has-session` subprocess call measured ~3ms even under that load, so no debounce-relevant
  slowness was observed to test against. **Note**: `nproc` on this host reads **16**, not the "8-core box (nproc=8)"
  cited repeatedly earlier in this doc's oversubscription-ratio math (e.g. "36/44/46 load... 4-6x nproc=8") — worth a
  flag for whoever re-derives an oversubscription ratio from a load-average figure going forward; either the host was
  resized at some point in this investigation's timeline or an earlier reading was taken in a differently-scoped
  context, but the two nproc values are inconsistent and every downstream "Nx core oversubscription" claim in this doc
  implicitly assumes nproc=8. Indirect evidence against (c) as the PRIMARY driver, though: the 14-102s detection-lag
  range measured in (a) above is entirely explained by the 60s AgentKeeper/TmuxPruner tick interval and which one's
  phase lands first — the 0.25s debounce recheck is a rounding error against that, so even a materially longer debounce
  window would not change the observed kill-to-detection latency pattern by more than a fraction of a second. This
  doesn't prove 0.25s is sufficient under genuine heavy contention (not measured directly here), but it does mean the
  debounce window is very unlikely to be the dominant lever on the observed ~5-9min cadence — the cadence is set by
  whatever kills the process, not by how fast it's detected afterward.

  **Most significant new finding, not one of the 3 original sub-angles**: one of the 2 captured deaths (PID 599219) died
  ~7s after systemd's own log explicitly recorded it as surviving an `orchestrator.service` restart ("Unit process
  599219 (claude) remains running after unit stopped" at 19:30:25Z, confirmed gone by 19:30:32Z) — a
  `systemctl restart orchestrator` triggered by `scripts/ao-self-pull.sh`'s cron tick (runs every ~15min, restarted the
  service on 5/6 of the last 6 ticks sampled). `orchestrator.service` explicitly sets `KillMode=process` (with an
  in-file comment citing a 2026-05-20 incident) specifically so a backend restart does NOT touch tmux/claude worker
  children — and systemd's own log confirms it did NOT directly kill this PID ("Found left-over process 599219 (claude)
  in control group while starting unit. Ignoring."). Yet the process died anyway, inside the restart window, before
  either the old process (dead by 19:30:25Z) or the new one (AgentKeeper/TmuxPruner not ticking until ~19:30:35-37Z)
  could have reaped it via this repo's own code — and `ao-self-pull.sh`'s restart call is a plain
  `systemctl restart orchestrator`, no `pkill`/broader kill. Full-day correlation (118 kills vs 28 restarts today):
  9.3%/13.6%/23.7% of kills land within 120s/180s/300s of a restart respectively — consistent with the doc's earlier
  ~15%/120s finding (a real but MINORITY contributing factor, not the dominant driver of the steady drumbeat), so this
  doesn't overturn the standing conclusion, but it's now a concrete, timestamped instance of an apparent violation of
  `KillMode=process`'s own safety contract, worth its own targeted follow-up (new todo added above) rather than being
  folded back into the general host-contention hypothesis. Did not attempt a code fix this session — the todo's own
  framing asked for a new investigative angle, not a 4th patch, and this lead needs deliberate reproduction (todo added
  above) before a fix target is even known. No code shipped this session (this doc only).
