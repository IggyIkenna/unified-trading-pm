---
doc_type: issue
title: >-
  Fleet dispatch:done gap driven by tmux session loss mid-task — self-directed-signal mechanism CONFIRMED, but
  exit-empty fix FALSIFIED by live re-test; auditd tmux-execve watch now armed to find the real trigger
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
  and 508/1203 (42%) fire while the slot is holding an undone dispatched task — directly explaining a meaningful share
  of the retry/redispatch volume. Correlated against the orchestrator's own `resource_history` samples (24h,
  `data/state/resource_history/*.jsonl`): CPU%, load_avg_1m, and swap% at the moment of loss were NOT elevated vs. the
  24h baseline (if anything, median CPU at loss-time was LOWER than the 24h median) — a working hypothesis that acute
  host resource contention (the host runs ~15-20 concurrent `claude` worker processes plus other repos' heavy pytest/QG
  runs on one 16-vCPU/30GB box, with the box observed steadily swapping, 5%->21.6% swap-used over 24h with 0 OOM-kills
  logged) triggers the losses was NOT supported by this pass — swap is climbing gradually but RAM usage stays low
  (~27%), consistent with normal idle-page reclaim rather than genuine memory pressure. Root cause of the abrupt tmux
  session death itself (network/SSH layer? tmux server bug? underlying Claude CLI crash? per-account rate-limit
  teardown?) is UNRESOLVED — this doc exists to hand that off as tracked, evidence-backed next steps rather than losing
  the investigation to chat history.
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

## What's confirmed but not yet root-caused

- The proximate event immediately preceding almost every redispatch is `tmux_session_lost` (94%), and the large majority
  of ALL `tmux_session_lost` events (81%) have no planned-teardown explanation in the preceding minute — these are
  genuinely abrupt.
- 42% of all tmux losses hit a slot mid-task (not idle) — directly interrupting live work, which is exactly the
  mechanism inflating `dispatches` without a matching `done` (the `dispatches/done` and per-role/slot/day breakdown
  shipped this session: `agent-orchestrator@016abaff2f`, `@8a7a8c0fe0`).
- **Context saturation is a real but MINOR contributor, not the ~43% it first looked like — narrowed same session (see
  Progress Log).** The proactive path (`server/context_lifecycle.py`) works as designed: force `/pre-compact` (locates a
  resume point) then force `/compact`, injected into the SAME live pane — a successful cycle never touches
  `task_dispatched` at all (the task stays `dispatched` on the same session throughout), so it correctly does NOT show
  up as a redispatch. The only genuine failure mode is `tmux_pruner.py`'s reactive path: a session that dies WHILE
  already at/above `resume_fresh_context_pct` (the resume-eligibility ceiling) can't be resumed — resuming a session
  already past the ceiling would just re-hit it — so it's requeued fresh instead, logged distinctly as
  `context_saturated_session_lost_task_requeued`. Re-querying with the EXACT event (not any compact-flavored event
  nearby, which mostly just means "a routine successful compact also happened somewhere in a long gap on a busy slot"):
  only 7 of 142 redispatches (5%) show it. The other 69/142 (49%) that show SOME compact-related event are very likely
  coincidental co-occurrence, not causal.

## Mechanism CONFIRMED, root TRIGGER still open — exit-empty fix FALSIFIED (2026-08-13)

**Confirmed, reproduced twice via live `strace`**: the death is always a SELF-directed `kill(<own_pid>, SIGTERM)`
(si_pid matches the traced pid) then a clean `exit_group(0)` — never external SIGKILL/crash/OOM/cgroup, why no death
ever produced a core dump even post-LimitCORE. **Open: WHY it self-signals.** `exit-empty` looked confirmed but was
FALSIFIED by re-test: `agent-orchestrator@ef5ba1e2cc` + a live `set-option -g exit-empty off` (readback-confirmed) on
the exact pid that died the same way ~20min later anyway; both times the reaped children appear AFTER the self-kill
line, i.e. a consequence of shutdown, not sessions naturally reaching zero. Full-filesystem grep (repo + `/opt` +
`/etc/systemd` + `/usr/local` + crontab) found no `kill-server`/`pkill tmux` script anywhere. **Now armed**: `auditctl`
on every tmux execve (`tmux_exec_watch`) — if some process (maybe another session on this shared VM) runs
`tmux kill-server`, the next occurrence shows its full argv + parent ancestry. Cross-reference: the "n=3 utempter
pty-registration burst" finding further below in this doc is very likely the SAME phenomenon, not yet reconciled with
this trace evidence. `exit-empty off` KEPT as harmless hardening, no longer claimed sufficient.

## Todo

- [ ] [INFRA] P2. **Get real tmux/system-level evidence for an unplanned loss**, not just orchestrator-side activity_log
      inference. On the orchestrator VM (`i-0c9b283b31d6b5ca7`, read-only SSM only — see
      `scripts/orchestrator/check-ao-backlog-status.sh` for the access pattern): (a) fix the `journalctl -k` OOM check
      that partially failed this session (needed `sudo`, command errored before finishing — rerun cleanly and confirm 0
      OOM-kills over a longer window, not just 24h); (b) check `journalctl --user` or the tmux server's own log (if any)
      for the PIDs/session names tied to a sample of `tmux_session_lost` events with NO planned precursor; (c) check
      whether the underlying `claude` CLI process for a lost session is still alive (zombie/defunct) or fully gone at
      the moment of loss — distinguishes "tmux itself died" from "the CLI process crashed and took the pane with it."
      **Done when**: at least one genuinely unplanned loss has a confirmed process-level cause (CLI crash, tmux server
      issue, OOM-kill, SIGKILL from elsewhere, or ruled out entirely with real evidence). Repo: agent-orchestrator.
- [ ] [INFRA] P2. **Check for a per-account correlation** — do losses cluster on specific `account_id`s (e.g. one
      DeepSeek/Anthropic account rotating or rate-limiting more aggressively, which could force a session teardown
      independent of host load)? Join the 1203 `tmux_session_lost` events' `slot_id` against `SlotRow.account_id` at
      that time and look for a skew. **Done when**: either a specific account/provider is shown to explain a
      disproportionate share, or the loss rate is confirmed roughly uniform across accounts. Repo: agent-orchestrator.
- [x] [INFRA] P3. ~~Narrow the context-saturation lead~~ — **done same session**: only 7/142 redispatches (5%) show the
      exact `context_saturated_session_lost_task_requeued` failure event; the other 69/142 that show some
      compact-flavored event nearby are most likely coincidental. Context saturation is a minor contributor, not a major
      one — the proactive precompact->compact->resume path works in-place and correctly never shows up as a redispatch
      when it succeeds. No further action here; the 5% failure case is inherently rare-and-bounded (only fires when a
      session dies exactly while already past the resume ceiling) and not worth chasing further compared to the other
      three todos below.
- [ ] [INFRA] P3. **Re-run the resource-history correlation with tighter sampling** if the sampler's interval allows —
      the current pass could miss a spike shorter than the sample gap. Check `resource_history.SAMPLE_INTERVAL_SECONDS`
      and, if it's coarse (e.g. 60s+), consider whether a sub-interval spike is plausible given `iowait_percent`'s
      elevated p90 (40.7 vs 24.3 baseline) at loss moments — the one metric in this pass that wasn't clearly
      unremarkable. Repo: agent-orchestrator.
- [ ] [INFRA] P3. **Pruner-loop delay under load — DOWNGRADED 2026-08-11, likely superseded by the tmux-server-death
      finding below.** Live journal read (SSM, `journalctl -u orchestrator`) around a 25-session loss cluster
      (07:57:42-45 UTC) found a single `TmuxPruner: cleared 25 stale tmux_session reference(s)` line — one pruner TICK
      clearing a backlog of 25, not necessarily 25 sessions dying in the same instant. If the pruner's own loop was
      delayed/backed up (SQLite write contention under fleet load is a known pre-existing pattern per `tmux_pruner.py`'s
      own docstring on the `ensure_review_agents`-class lock contention it was refactored to avoid), losses that
      actually happened scattered over the PRECEDING window would only get detected+logged in one late batch, inflating
      the appearance of a synchronized mass-kill. A simpler, more direct explanation surfaced live the same day (see
      "production breakthrough" Progress Log entry): if the tmux SERVER process itself dies, every pane it hosts is lost
      in the SAME instant for real, no batching illusion needed — still worth confirming which (or both) explain the
      historical clusters, but no longer the leading hypothesis. **Done when**: pull successive
      `TmuxPruner: cleared     N` log-line timestamps over a longer window and check whether the gap between ticks is
      ever meaningfully wider than `tmux_prune_interval_seconds` (delay = real backlog) vs. consistently on-cadence (no
      delay = the 25 really were closely-clustered, still needing an explanation). A co-occurring
      `utempter: pututline: Permission denied` line at the same timestamp was investigated and is very likely a red
      herring — it also fires during the routine respawns immediately after, so it looks like constant/benign noise on
      this host's permission setup, not death-specific; note this here so it isn't re-chased as a lead. Repo:
      agent-orchestrator.
- [x] [INFRA] P3. ~~Check for a per-cgroup OOM kill~~ — **CLOSED 2026-08-11, ruled out.** All workers run under
      `orchestrator.service`'s systemd cgroup, which DOES have a real memory ceiling (`MemoryAccounting=yes`,
      `MemoryHigh=24.7GB`, `MemoryMax=26GB` — confirmed via `systemctl show`). Read the cgroup's own lifetime kill
      counter directly (`/sys/fs/cgroup/system.slice/orchestrator.service/memory.events`, root via SSM): `oom_kill 0`,
      `oom 0`, `max 0` — the cgroup crossed its soft `MemoryHigh` threshold 89,040 times (routine reclaim/throttle,
      consistent with the previously-observed climbing-swap pattern) but has NEVER triggered an actual kill. This is the
      cumulative counter, not a point-in-time sample, so it covers the whole recent elevated-death-rate window —
      definitively rules out cgroup-scoped OOM as the mechanism, closing the gap the host-wide-only check in todo 1
      couldn't see. Repo: agent-orchestrator.
- [ ] [INFRA] P2. **Live-catch the next death on one isolated slot** (todo 1's original ask — FURTHER PROGRESS
      2026-08-11, still open — mechanism narrowed further but the actual signal-sender still unidentified). Built a
      fully isolated agent-orchestrator sandbox (`/codex/15-runbooks/isolated-deepseek-crash-debug-sandbox.md`,
      `agent-orchestrator/scripts/orchestrator/{setup_debug_sandbox,watch_sandbox_slot_death}.sh`) specifically to catch
      a death live without ptrace overhead. First real run caught a genuine session-level death (332s into a real
      DeepSeek-backed task, same empty-`pane_dead` signature as production) and additionally checked macOS's built-in
      crash reporter (`ReportCrash`, confirmed actively working on the same run — it logged OTHER processes' events in
      the same window) — **zero crash report for this death**, ruling out segfault/abort/uncaught-exception as the
      mechanism with a second, independent, always-on crash-capture system (the Linux VM's now-enabled core dumps gave
      the same null result). A SECOND live catch (155s into a fresh task, same empty-`pane_dead` signature, see Progress
      Log) added: (a) ruled out the fleet's own spawn-heartbeat watchdog as the killer — read
      `server/worker_liveness/_auth_failover.py`'s working-pane guard, confirmed via the activity log it fired and
      correctly SKIPPED any respawn while the pane was actively producing output, with the death happening independently
      in the ~45s after that skip; (b) ruled out macOS jetsam/OOM — checked the ROOT-level kernel jetsam-kill log
      directly (`sudo log show --predicate 'sender == "kernel" AND eventMessage CONTAINS "jetsam"'`), which showed an
      unrelated `ecosystemd` process being jetsam-killed in a tight ~10s loop throughout the window but never touched
      our PID; (c) NEW positive signature — at the exact death instant, `runningboardd` logged
      `termination reported by proc_exit` for the process, and its long-lived (211s) DeepSeek-API TCP connection was
      simultaneously torn down via **RST, not FIN** — the signature of an abrupt, ungraceful termination (no time to
      close sockets), consistent with the standing uncatchable-signal hypothesis rather than a clean app exit; (d) no
      `launchd`-attributed "exited due to SIGKILL sent by X" line — sandbox macOS archaeology hit its practical ceiling
      here. **SUPERSEDED 2026-08-13** — root cause found via live `strace` on production (see "ROOT CAUSE FOUND"
      section): tmux's own `exit-empty` self-termination, not an external signal at all. Repo: agent-orchestrator.
- [x] [INFRA] P1. ~~New lead (2026-08-11, production breakthrough): find the tmux SERVER process's own resource
      envelope~~ — **CLOSED 2026-08-12, hypothesis REFUTED by direct live check.** `server/tmux_spawn.py`'s comments
      suggested the server likely sits OUTSIDE any per-service cgroup (unconfined) — checked directly the moment the
      server respawned after DeepSeek dispatch resumed (PID 3957305, started 11:57:18 UTC, checked at 46s old):
      `cat /proc/3957305/cgroup` → `0::/system.slice/orchestrator.service` — the tmux SERVER is in the exact SAME cgroup
      as every worker pane, not unconfined, not a different slice. This means the doc's own already-definitive
      `orchestrator.service` `oom_kill=0` ruling (which this todo assumed didn't cover the server) actually DOES cover
      it — there is no separate slice to check. `memory.events` read at the same moment: `oom_kill 0`, `oom 0`, `max 0`,
      `sock_throttled 4315179` (matches the earlier-noted 4,302,026-and-climbing reading, consistent trend). **Net**:
      this closes the "server sits in an unmonitored cgroup" hypothesis entirely — cgroup-scoped OOM of any kind is now
      ruled out for the server specifically, not just for panes. Whatever kills the server, it is not a cgroup memory
      action against a slice this investigation hasn't already checked. Repo: agent-orchestrator.
- [x] [INFRA] P1. ~~Alert + surface fleet-wide tmux server death~~ — **SHIPPED 2026-08-11,
      `agent-orchestrator@d1e62b7317`.** Operator ask: this class of outage needs Slack visibility, Activity Log
      visibility, and to colour the dashboard's "Multiple issues — eyes on this" HealthStrip, not just live silently
      alongside routine per-slot churn. Added `tmux_spawn.tmux_server_running()` (distinguishes "server gone" from
      "server up, this one session gone" via `tmux list-sessions`' stderr — the two known message variants observed live
      this session, Linux `no server running on <socket>` and macOS `error connecting to <socket>`); wired into
      `TmuxPruner.prune_once()` as a new fire-on-change + RESOLVED-bookend check (same shape as
      `WorkerLivenessWatchdog`'s dormancy alert — one page opens the episode, still-down ticks stay silent, a RESOLVED
      page closes it, latched on disk via `dedup_state.tmux_server_died_alerted_path()` so a restart mid-outage doesn't
      re-page); logs `tmux_server_died`/`tmux_server_recovered` fleet-wide (`slot_id=None`) activity events either way,
      so the Activity Log carries it even between Slack pages; pages `notify_tmux_server_died`/`_resolved` in
      `server/notifications/slack.py`; and surfaces `StateResponse.tmux_server_down` on the dashboard's HealthStrip —
      checked FIRST, ahead of even watchdog dormancy, since every other number on the strip is meaningless while the
      server itself is down. 6 new backend tests + 2 new dashboard tests. Caught and fixed one real bug in review before
      shipping: the first draft accidentally moved `agent_candidates`'s query outside its
      `with read_only_session_scope()` block and inside a conditional, which would have broken agent-reaping
      (`UnboundLocalError` whenever the fleet had zero worker sessions) — caught by the pre-existing pruner test suite,
      not by inspection.
- [x] [INFRA] P1. ~~Cron-alignment hypothesis~~ — **STATISTICALLY REFUTED 2026-08-11 with the full sample; correct DB
      path found.** The real path is `/home/ubuntu/unified-trading-system-repos/agent-orchestrator/data/state/state.db`
      (the earlier `/home/ubuntu/agent-orchestrator/...` 404 was a stale prefix — the actual clone lives one level
      deeper, under `unified-trading-system-repos/`; confirmed live via `-wal` mtime + growing size, the other 3
      candidate `*.db` files found nearby are all 0 bytes). Queried every `tmux_session_lost` burst-minute (≥4 distinct
      slots dying in the same minute) since 2026-06-27: **436 qualifying bursts total.** Grouping by `minute % 5` (the
      cron grid's period) gives `{0:73, 1:89, 2:87, 3:100, 4:87}` — essentially **uniform** (expected ~87.2/bucket if
      random; the largest bucket, offset 3 with 100, isn't even a cron-grid offset). Pre-2026-08-11-only slice:
      `{0:61, 1:68, 2:65, 3:77, 4:68}` — same shape. The original "3/3 today land on the grid" claim was a small-sample
      coincidence (n=3 is trivially likely to hit 2-of-5 minute-offsets by chance ~65% of the time); at n=436 there is
      no enrichment on either `slot-cron-ff-pull.sh`'s or `slot-git-status-report.sh`'s grid. **Retracting this as the
      leading hypothesis** — the two cron jobs are not implicated by this data. Repo: agent-orchestrator.
- [x] [INFRA] P0. ~~Scale of the outage was badly underestimated~~ — **MAJOR FINDING 2026-08-11, same query pass.** The
      doc's framing ("3 known deaths", isolated incidents) reflected only what the brand-new alert (shipped ~16:42) had
      caught in its first ~13 minutes. The full `tmux_session_lost` history tells a very different story: this fleet has
      had **hundreds of ≥4-slot simultaneous-loss bursts since 2026-06-27** (routine baseline: a handful of 4-15-slot
      bursts per day), and starting **2026-08-11 00:37 UTC — the same window the operator began using
      `alphavoltratrading@gmail.com` in production** — burst SIZE and FREQUENCY both stepped up sharply: 20-29 of the
      fleet's 34 configured slots losing their session simultaneously, recurring every 5-10 minutes **near-continuously
      for ~9 hours** (00:37-09:36), a quiet gap, then resuming 15:59-17:08 (the window the alert caught). This is not 3
      isolated incidents — it is the fleet spending large fractions of today in a degraded/wedged state at real
      production load. **Escalate**: this materially changes priority — the underlying mechanism (still open, see below)
      needs to be found, not just alerted on. Repo: agent-orchestrator.
- [x] [INFRA] P1. ~~Detection has a real coverage gap~~ — **FOUND + FIXED 2026-08-11, same pass (ships with this
      commit).** `TmuxPruner.prune_once()`'s fleet-liveness check (`_check_tmux_server_liveness`, shipped as
      `agent-orchestrator@d1e62b7317`) only ran ONCE, at the very top of the tick — before the per-slot
      `has_session()`/`_confirm_session_dead()` sweep that follows it, which is sequential across every candidate slot
      and (per the function's own docstring) can take "up to 2s each" plus a debounce re-check. On a large fleet this
      sweep can span many seconds. Pulled exact-microsecond timestamps for two representative bursts (2026-08-11 02:01,
      29 slots; 2026-08-09 08:32, 20 slots): both show **strictly ascending slot-ID order** with per-slot gaps of
      ~0.1-0.7s, spanning 3.3s and 14.3s respectively — a sequential scan discovering absence slot-by-slot, not one
      simultaneous instant. Cross-checking the shipped alert's own catch window (16:55-17:08) found 5 large
      `tmux_session_lost` bursts (19-25 slots each) but only 3 `tmux_server_died` alerts — meaning at least 2 of those
      bursts had the server confirmed UP at the up-front check, then losing 19+ sessions during the sweep that followed,
      with no re-check afterward to catch a mid-sweep death. **Fix**: added a second `_check_tmux_server_liveness()`
      call after the sweep completes, before the write pass (mirrors the existing dedup-latched
      fire-on-change/RESOLVED-bookend shape, so calling it twice per tick is safe — pages once per real transition
      regardless of how many times it's invoked while the state is unchanged). New regression test
      (`test_prune_once_catches_a_server_death_that_happens_mid_sweep`) simulates `tmux_server_running()` returning True
      then False within one tick and asserts the alert now fires. This closes the KNOWN gap but does not explain WHY the
      server dies — that mechanism is still open below. Repo: agent-orchestrator.
- [x] [INFRA] P0. ~~Root mechanism~~ — **MAJOR BREAKTHROUGH 2026-08-11, live-caught with a 1s-resolution capture.**
      Operator resumed production dispatch; launched a 20-minute VM-side loop sampling the tmux server's PID/thread
      count/FD count/`VmRSS`/cgroup plus a timed `tmux list-sessions` call, once per second
      (`/tmp/tmux_server_live_capture.log` on the VM — not yet promoted into the repo, see follow-up todo). Caught a
      real death at **2026-08-11 18:10:50** (`tmux_server_died`, 18 slots affected). The 55+ seconds immediately
      preceding it are **completely flat and healthy**: steady 1 thread, steady 33 FDs, `VmRSS` climbing normally
      (6.4MB->6.8MB, unremarkable), `tmux list-sessions` consistently fast at 9-12ms every single sample, load average
      fluctuating 6.5-7.3 with no trend toward any ceiling. Then, within 1.4s of the last healthy sample, the process
      (PID 3820711) is gone entirely — no degradation ramp, no slowdown warning, an instant vanish. This **rules out
      mechanism (b)** from the prior framing (per-slot health check becoming unreliable/slow under load) as the
      explanation for this instance — `tmux list-sessions` itself was fast and healthy right up to the edge, then
      genuinely started failing (`rc=1`). **New, sharper lead**: `journalctl` for the same window shows **27
      `utempter:     [ppid=3820711] pututline: Permission denied` messages, all landing within the SAME second
      (18:10:49)** — each one a child process the tmux server spawns to register a new pty in utmp whenever it creates a
      pane/session. That's a burst of ~27 near-simultaneous new-pane-creation calls hitting one tmux server process, one
      second before it died (5 `slot_boot` events also landed in the preceding 10s, though that alone doesn't account
      for all 27 — the rest likely came from a concurrent AutoSpawn/escalation dispatch wave catching up after the
      operator's pause, per the same window's `journalctl` showing active escalation-retry churn). **Working hypothesis,
      replacing the old resource-pressure-vs-flaky-check framing**: a burst of concurrent new-session/new-pane creation
      requests against a single tmux server process can crash it outright — not gradual exhaustion, a sudden failure
      correlated with a spawn spike. The `utempter` "Permission denied" itself is a separate, not-yet-investigated
      oddity (uncertain if it's causal, incidental, or has always been silently present on this VM). **This is n=1** —
      strong, clean, first-ever direct evidence, but one incident. **Done when**: (a) a second live catch with the same
      signature (flat-then-instant-death + coincident utempter/spawn burst) to confirm this isn't a one-off; (b) figure
      out whether `utempter`'s permission-denied failures are new/environmental (check if `/var/run/utmp` perms changed
      recently, or if this has always silently occurred) and whether they're incidental noise or somehow contribute to
      the crash; (c) if confirmed, the fix candidate is throttling/serializing concurrent new-pane creation against the
      tmux server rather than firing them all at once. Repo: agent-orchestrator.
- [x] [INFRA] P0. ~~Second live catch, ~14 minutes later~~ — **CONFIRMS TWO DISTINCT DEATH MECHANISMS, not one.** Same
      capture session, still running. Death #2: `tmux_server_died` at **2026-08-11 18:24:41** (21 slots). This one does
      NOT match death #1's flat-then-instant signature at all. Instead, `load average` (1m) climbs **steadily and
      continuously for ~9 minutes before the death**: 5.71 (18:15:00) -> 7.11 (18:16:09) -> 14.23 (18:16:45) -> 15.84
      (18:18:20) -> 20.31 (18:19:15) -> **70.92 (18:19:35)** -> 77.29 peak (18:22:00) -> 48.35 (18:23:56, last healthy
      sample) -> server gone (18:24:09). At 18:19:35 the capture script's own `tmux list-sessions` call — normally
      9-12ms every single time — took **6,815ms**, and the capture loop then MISSED its 1s cadence for ~~2.5 minutes
      (18:19:35 to 18:22:00, no samples at all) — the monitoring script's own subprocess calls were themselves too
      starved of scheduler time to complete on schedule. This is genuine, sustained, severe resource starvation, not an
      instant crash. A `ps -eo pid,ppid,pcpu,...--sort=-pcpu` snapshot taken seconds after the death (18:24:43, load
      still 30.82/38.32/22.47) names the actual load: **7+ concurrent `ssh git-upload-pack` fetches to the same repo**
      (`unified-trading-system-ui.git` — plausibly several different slots independently fetching it at once), **9+ live
      `claude` worker processes each at 18-25% CPU** (dozens of slots resuming work simultaneously post-pause), and
      **one `rg --no-config --files --hidden` recursive scan alone at 900% CPU** (a single file-listing tool call
      consuming up to 9 full cores). `top` also showed 16.1% iowait and swap in active use (5.2GB), consistent with
      genuine multi-resource contention (CPU + disk I/O), not one narrow bottleneck. **Revised model — two failure
      modes, one root class of trigger**: both death #1 (instant crash on a concurrent new-pane-creation burst) and
      death #2 (gradual death under sustained aggregate CPU/IO starvation) point at the SAME underlying condition — **a
      large number of slots becoming simultaneously active drives resource demand past the VM's capacity**, whether that
      shows up as an instant crash-on-spawn-storm or a multi-minute starvation death. This reframes the fix target away
      from "find and patch a tmux bug" toward **"the orchestrator dispatches more concurrent work than this VM can
      actually carry"** — a capacity/throttling problem, not a tmux-specific one. Notably, this ALSO retroactively
      explains why the earlier (now-refuted) cron-alignment hypothesis felt so plausible for 3/3 early samples: the two
      named cron jobs are ONE SOURCE of concurrent git load among MANY (7+ concurrent git fetches here came from
      ordinary slot work, not cron) — the real trigger was always "how much concurrent git/CPU load is the fleet
      generating right now," which cron ticks are only sometimes correlated with. **Done when**: (a) determine a safe
      concurrency ceiling — how many slots can be simultaneously active/spawning before the VM saturates (from this
      data: healthy at load~~6-7 with ~27 sessions live, catastrophic once concurrent NEW dispatch + git fetches pile on
      top); (b) throttle/stagger AutoSpawn's dispatch rate and/or cap concurrent git subprocess fetches fleet-wide
      rather than letting every slot fetch independently and simultaneously. Repo: agent-orchestrator,
      unified-trading-pm (cron/git tooling). **Correction (2026-08-11, same session)**: the `rg --hidden --files`
      process named above was investigated as a possible independent culprit and **measured, not assumed** — reproduced
      the identical call (`rg --no-config --files --hidden` against the full `.tabs/3` directory, 36 repos, 69,246 files
      including hidden/hidden-ignored paths) under current calm conditions: **59ms**. Without `--hidden`: 34,546 files,
      26ms. Neither is remotely expensive in isolation — ripgrep is fast even over a large multi-repo tree. This refutes
      it as an independent root cause: it was a normal tool-call caught in the same CPU contention that starved the tmux
      server, not a separate runaway pattern needing its own fix. No `.rgignore`/exclude change is warranted from this
      evidence. Dropping it from the throttle-fix scope — the fix is dispatch/git-fetch concurrency, not this.
- [x] [INFRA] P0. ~~Throttle fix~~ — **SHIPPED 2026-08-11, `agent-orchestrator@54da59c24b`.** Found the exact mechanism:
      `_do_spawns_concurrently()` (`server/autospawn.py`) ran its `ThreadPoolExecutor` with `max_workers=len(calls)` —
      fully unbounded. A burst of N slots needing respawn fired N `_do_spawn` calls (each doing multi-repo git
      branch-state/dirty-resolution checks + a tmux boot) ALL AT ONCE — exactly the mechanism behind both live-caught
      deaths above (death #1's ~27-wide utempter/pane-creation spike; death #2's 7+ simultaneous git fetches + climbing
      load). Added `tuning.autospawn_max_concurrent_spawns` (default 8) and capped `max_workers` at
      `min(len(calls), cap)`. Chosen to leave the common case (≤8 concurrent) at the exact same full-speed all-at-once
      behavior as before — including the original SLA-fix motivating case (5 slots) this function was built to unblock
      (`autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08`) — only throttling batches larger than that, which is
      precisely when it's dangerous. **8 is a starting point, not a proven ceiling** — no data exists between "8
      concurrent" and the 18-27-slot bursts that crashed the server twice; tune via this one config field (no code
      change needed) once more live bursts are observed under the fix. 2 new tests
      (`test_do_spawns_concurrently_never_exceeds_the_configured_cap`,
      `test_do_spawns_concurrently_batch_at_or_under_cap_is_unaffected` — the second locks in the "no slowdown for the
      common case" requirement explicitly). **Verification in progress**: `ao-self-pull.sh` redeploys from
      `live-defi-rollout` within ~15min of the push; relaunched the live-capture loop to watch whether the next real
      burst stays bounded now — see Progress Log for the result once caught. Repo: agent-orchestrator.
- [x] [INFRA] P2. ~~Promote the capture script into the repo~~ — **DONE 2026-08-11, same session.** Confirmed the exact
      durability problem live: the hand-authored `/tmp/tmux_live_capture.sh` got cleaned from `/tmp` between two uses in
      this SAME session, forcing a full re-author from the chat transcript before it could be relaunched to verify the
      throttle fix. Gave it a real home: `agent-orchestrator/scripts/orchestrator/tmux_server_live_capture.sh`
      (`launch`/`status`/`tail` subcommands, same lifecycle-marker + SSM-read-only-access conventions as
      `watch_production_slot_death.sh`; the remote loop is base64-transported to sidestep the JSON/nested-quote escaping
      hit repeatedly hand-authoring this over SSM this session). Also added a `spawns=` field to the capture (live
      `autospawn-do-spawn` thread count via `pgrep -c -f`) so the NEXT capture directly shows whether the throttle cap
      is holding, not just its downstream effects on load/FDs. Test-launched against production, confirmed working, and
      killed the stray duplicate instance it created alongside the still-running manually-launched one from earlier in
      this session. An always-on/systemd-timer variant was considered but not built — the one-shot 20-minute-window
      model has been sufficient for this investigation's on-demand catches; revisit only if continuous coverage becomes
      a real need. Repo: agent-orchestrator.
- [ ] [INFRA] P3. **Wire `resource-watchdog`'s existing tick log into future death correlation.** Discovered live
      2026-08-11 — a previously-undocumented-in-this-doc systemd service already logging periodic
      `pressure=<state> cgroup_mem=<val>` ticks. Confirm its log retention/location and whether it's worth pulling into
      the same enrichment path as the cgroup `memory.events` counters (Tier 1, already shipped
      `agent-orchestrator@4452cbb6da`) rather than re-discovering it ad hoc next time. Repo: agent-orchestrator.
- [x] [INFRA] P3. ~~Confirm the 16:15:xx orchestrator.service restart was ao-self-pull.sh~~ — **CLOSED 2026-08-11,
      confirmed.** `journalctl -u orchestrator` at 16:15:28 UTC:
      `orchestrator running checkout 4452cbb — 0     pre-existing tmux session(s): []` — the self-pull restart landing
      exactly as expected, ~43s after the tmux-server death, finding zero sessions (consistent with the server having
      died and not yet respawned by then, not causing it). Confirmed coincidental, not causal. Repo: agent-orchestrator.
- [x] [INFRA] P0. ~~Throttle fix verified insufficient alone~~ — **CLOSED 2026-08-12, LEADING HYPOTHESIS NOW n=3 via the
      utempter-burst signature — see below.** TWO earlier live catches (20:54, 21:11 on 2026-08-11) showed the SAME
      flat-then-instant-crash signature with the throttle fix active and AutoSpawn's own concurrent-spawn count
      confirmed at ZERO throughout. The 20:54 death: nsess=26, load=11.85 (moderate, not the pre-fix 40-77 danger zone),
      `tmux list-sessions` at 11-13ms right up to the last healthy sample, `spawns=0` — then instant vanish, 63s
      recovery. The 21:11 death: same shape, 92s recovery, `spawns=0` throughout. **AutoSpawn's
      `_do_spawns_concurrently` cap is confirmed NOT the trigger for this crash class** — it may still be preventing
      SOME deaths (the fix stands, unbounded concurrency was a real hazard regardless), but the dominant "instant,
      healthy-then-gone" mechanism needed a different signal. Extended the live-capture script with a broader `newsess=`
      counter (any `tmux new-session -d -s` process, not just AutoSpawn's thread-prefix) to catch
      escalation.py/worker_liveness_watchdog.py/plan_health.py's own uncapped direct `do_spawn`/`tmux_spawn.spawn()`
      calls, since they bypass AutoSpawn's cap entirely. **Measurement trap found + fixed in the same pass**: the first
      version of that counter was a false-positive generator — the running tmux SERVER's own `/proc/<pid>/cmdline`
      permanently retains its ORIGINAL `tmux new-session -d -s ...` invocation forever (Linux doesn't rewrite cmdline on
      a `comm`-only rename), so `pgrep -f "tmux new-session -d -s"` always matched the server's own PID as a permanent
      self-match. Fixed by excluding the already-known server PID from the count. Every `newsess=1` reading up to this
      fix was meaningless self-matching, not evidence of a genuine concurrent spawn — corrected before drawing any
      conclusion from it.

      **2026-08-12 — TWO live catches under the corrected counter, same 30-min capture window, closing this todo's
                          done-when with a DIFFERENT, sharper signal than the counter itself.** Both deaths read `spawns=0`, `newsess=0`
                          throughout the 1s-resolution capture — the corrected counter STILL saw nothing, which is itself the key finding
                          (see the new measurement-trap note below), but a parallel `journalctl` cross-check found what the counter
                          missed:

                          **Death (2026-08-12 12:05:21.030 UTC)**: last healthy sample 12:05:19.654 (load 2.76/2.96/2.02, ls_rc=0,
                          nsess=5) — server gone by 12:05:21.030 (ls_rc=1), a ~1.4s flat-then-instant vanish, load LOW throughout (not a
                          resource-starvation death). `journalctl` for the same second (12:05:20) shows a burst of **9
                          `utempter: pututline: Permission denied` lines**: 5 with `ppid=3957305` (the tmux SERVER's own live PID at that
                          moment), 2 with `ppid=190007`, 2 with `ppid=190322` (both short-lived child processes, gone before any capture
                          sample could catch them). Recovered by 12:06:05.859, new PID 241676 — 44.8s recovery, same
                          `orchestrator.service` cgroup as before.

                          **Death (2026-08-12 12:23:06.574 UTC)**: last healthy sample 12:23:05.310 (load 4.58/3.85/3.10, ls_rc=0,
                          nsess=5) — server gone by 12:23:06.574. `journalctl` for 12:23:05-06 shows a burst of **6 utempter
                          permission-denied lines**: 5 with `ppid=241676` (again, the tmux SERVER's own live PID), 2 with
                          `ppid=908530`, 2 with `ppid=908710`. This one has a clear proximate trigger in the same log window:
                          `ci-reconciler.service`'s systemd timer fired at 12:23:05, attempted a dispatch, and got a 503
                          (`mode 'ci_reconcile' is paused by operator`) — **the utempter burst fired regardless of the dispatch being
                          REJECTED**, meaning whatever creates these pty-registration attempts happens before or independent of the
                          API's pause-check, not only on a successful spawn. Recovered by ~12:24:16, new PID 942168 — ~78s recovery.

                          **Net**: this is now **n=3** for the identical signature (the original 2026-08-11 27-wide burst at
                          `ppid=3820711` [the server PID then], plus these two: 9-wide and 6-wide, both explicitly tracing to the
                          server's OWN live PID as parent of the majority of the burst). Every instance checked with per-second
                          resolution shows the same shape: a burst of 5+ near-simultaneous pty-registration attempts landing in the
                          SAME 1-2 second window immediately before the server vanishes, at LOW-to-moderate load (not the separate
                          gradual-starvation death class). This is now the best-evidenced, leading hypothesis in the whole
                          investigation — promoted from n=1 speculative lead to n=3 reproduced signature in one session.

                          **New measurement trap, found by this catch**: the corrected `newsess=` counter (self-match bug already fixed)
                          STILL read 0 through both deaths, even though `journalctl` proves genuine non-AutoSpawn pane-creation activity
                          was happening at that exact moment. Root cause: `pgrep`-based 1-second-interval sampling is structurally too
                          coarse for this signal — these child processes spawn, hit `utempter`'s permission-denied, and exit in well
                          under a second, so a once-per-second poll has a real chance of landing in the gap between two such processes'
                          entire lifetimes. `journalctl`'s persistent log lines are the reliable detector here, not a live `pgrep` sample
                          — the capture script's `newsess=` field should be treated as a lower bound / sanity check, never as proof of
                          absence.

                          **Also ruled out for both catches**: `sockthr_own`/`sockthr_sys` were completely FLAT (no increment at all)
                          through the entire pre-death window on both — the `sock_throttled` lead (open todo below) is NOT the trigger
                          for this specific crash class, at least not as an actively-incrementing signal in the second before death.

                          **Audit done + mitigation shipped 2026-08-12, `agent-orchestrator@c77a42ab54`.** Traced the mechanism precisely
                          rather than guessing:

                          - `ci-reconciler-dispatch.sh` itself is a pure HTTP client — it never touches tmux, and its death-B dispatch
                            attempt was rejected by `scheduled_dispatch_pause` (mode paused) BEFORE any spawn logic could run. Its
                            timing in the journalctl window was coincidental, not causal.
                          - The real mechanism is `escalation.py`'s `retry_queued_escalations()`: the outer queue-drain loop fetches up
                            to `limit*50` (≈100) queued escalations per tick and only stops early on a SUCCESSFUL dispatch count — a
                            FAILED spawn attempt just `continue`s to the next escalation with no cap. Separately, each individual
                            `escalate()` call has its OWN internal retry loop (`_MAX_SLOT_PICK_ATTEMPTS = 5`, mirrored identically in
                            `plan_health.dispatch()`): on a `"benign: slot raced by another spawn path"` TOCTOU failure it immediately
                            retries `do_spawn()` (→ `tmux new-session`) on a different slot, up to 5 times, synchronously, with NO delay
                            between attempts. Confirmed via code read (`server/escalation.py` ~L499-L737, mirrored in
                            `server/plan_health.py` ~L660-L810) that the ONE failure mode checked in detail — "repo already active on
                            another slot" — happens BEFORE `do_spawn`, so it doesn't itself create a pty; the 5x internal race-retry is
                            the cleaner, more direct explanation and needs only one escalation losing repeated slot races to produce a
                            multi-wide burst. journalctl confirmed the "thundering herd" precondition: 7-9 TTL-held escalations surfaced
                            in immediate succession right as the fleet resumed from the DeepSeek pause, with at least two independent
                            "slot-specific spawn failure... skipping to next queued wall" lines landing in the same 1-2s window as
                            death B.
                          - **Shipped as a mitigation** (narrows the window pending full root-cause confirmation, same rationale as the
                            fleet-git-health-guard.sh fix): (1) a configurable backoff (`tuning.spawn_race_retry_backoff_seconds`,
                            default 0.5s) between race-retries in BOTH `escalation.escalate()` and `plan_health.dispatch()`'s identical
                            loops, spreading a burst over more wall-clock time; (2) a cap
                            (`tuning.escalation_max_failed_spawn_attempts_per_tick`, default 5) on the outer queue-drain loop's failed
                            spawn attempts per tick, stopping the thundering-herd case early instead of burning through the whole ≈100
                            row headroom window; (3) `log_activity()` on every race-retry (`escalation_spawn_race_retry` /
                            `plan_health_spawn_race_retry`, both with escalation/dispatch id + attempt number) and on the cap being hit
                            (`escalation_failed_spawn_attempts_cap_hit`) — this exact condition happened three times before it was
                            caught, purely by luck of an active live-capture session; it is now visible in the Activity Log going
                            forward without needing one. (4) A new Slack alert, `notify_escalation_spawn_storm`, fires when the cap is
                            hit — explicitly named as "not proof of an imminent crash, but the same shape both confirmed live catches
                            showed," so it doesn't overclaim causation that is still unconfirmed. Tests:
                            `test_escalate_race_retry_logs_activity_and_backs_off`,
                            `test_escalate_exhausted_retries_backs_off_between_but_not_after_last_attempt`,
                            `test_retry_stops_early_at_failed_spawn_attempts_cap`,
                            `test_retry_failed_spawn_attempts_below_cap_does_not_trigger_storm_alert` (escalation.py), the mirrored
                            `test_dispatch_race_retry_logs_activity_and_backs_off` /
                            `test_dispatch_exhausted_retries_backs_off_between_but_not_after_last_attempt` (plan_health.py), and
                            `TestNotifyEscalationSpawnStorm` (slack.py) — full suite green, quality gates PASSED.
                          - **Not done / nice-to-have, not chased this pass**: `worker_liveness_watchdog.py`'s three `tmux_spawn.spawn()`
                            call sites (`_auth_failover.py`, `_respawn.py`, plus two more in the watchdog itself) call `tmux_spawn.spawn`
                            directly but WITHOUT this internal 5x-retry-on-race pattern (single-attempt each) — lower individual burst
                            risk, not touched here; worth a follow-up scan if a future live catch shows the watchdog as the source
                            instead. Also not done: instrumenting an actual live burst with this specific hypothesis armed (e.g. a
                            temporary per-attempt `escalation_id` + `do_spawn` correlation log) to CONFIRM escalation's retry loop —
                            rather than plan_health or watchdog — is the real source of a future burst, since the current evidence is a
                            strong structural match plus correlated timing, not a smoking-gun capture of `escalate()` itself mid-burst.
                          - **Still open**: whether a pane-creation burst is actually WHY the tmux server dies remains unconfirmed — this
                            mitigation narrows the window the same way the fleet-git-health-guard.sh fix did, it does not prove or
                            disprove causation. The next live catch (now with `escalation_spawn_race_retry` logging + the storm alert
                            armed) is the way to gather that evidence without needing another lucky manual capture session.

          **First real test (2026-08-12 16:28:37 UTC)**: a genuine death on a checkout descended from the fix.
          Zero `escalation_spawn_race_retry`/cap-hit/`plan_health_spawn_race_retry` events in the 9min before
          (weakens the race-retry hypothesis specifically) — but 7 `deepseek_spawn_selected` events landed in
          a ~50ms window 4-5s before death, most likely AutoSpawn's OWN routine refill (the ALREADY-THROTTLED
          `autospawn_max_concurrent_spawns` cap=8 path, shipped `agent-orchestrator@54da59c24b`) — 7 is
          suspiciously close to that cap. **Net**: this mitigation didn't touch what caused THIS death; the
          OLDER concurrent-spawn cap looks implicated again, and cap=8 may not be safe. Caller attribution
          (the "add a source field" done-when this originally asked for) shipped as part of
          `agent-orchestrator@64a559fe8e` below, closing that gap for future catches. Repo: agent-orchestrator.

          **2026-08-12/13, reconciled with the strace self-kill finding above.** Shipped
          `agent-orchestrator@e025b83d01` (removed a real wasted `select_account_for_spawn` call firing
          every ~60s regardless of queue state) and, per operator direction, **froze the fleet entirely**
          (33/34 slots + all 11 scheduled-dispatch modes paused). A death still occurred AFTER the freeze
          (22:36:57Z) with `activity_log` COMPLETELY EMPTY that window — every tmux-spawning code path
          verified to correctly exclude paused slots. **Weakens this whole hypothesis**: a burst can
          precede a death (n=4, PID tracing mostly to the server's own PID) without our dispatch code
          being the source. Given the self-kill finding above, likely reading now: **the utempter burst
          and the self-kill are the SAME event's two faces** — tmux forking shutdown children, not a
          pre-existing overload. This session's spawn-concurrency throttle + headroom-check fix are real
          fixes on their own merits, not claimed as addressing the actual death mechanism.

          **New tool, same gap as strace/auditd, from the syscall-adjacent side**:
          `agent-orchestrator@06bc8ee0b0` — `pty-burst-watchdog.service` (systemd --user, confirmed
          running + endpoint-verified live), tailing `journalctl -f` live and capturing
          `/proc/<ppid>/{comm,cmdline,status}` for the burst's parent PIDs THE INSTANT threshold crosses
          (>=3 in 3s) — prior catches needed slow post-hoc SSM archaeology by which point the parent was
          gone. Reports to `POST /api/internal/pty-burst-detected` -> `tmux_pty_creation_burst`
          activity_log row (dashboard-visible) + Slack, before a death, not just after. **Cross-ref for
          next pickup**: this watchdog's captured comm/cmdline read alongside `auditctl
          tmux_exec_watch`'s argv+ancestry on the next occurrence should show whether the utempter
          burst's parent IS the dying server's own shutdown fork (working guess) or a separate actor.
          Repo: agent-orchestrator.

- [x] [INFRA] P1. ~~Reduce fleet capacity while root cause remains open~~ — **DONE 2026-08-11, operator-directed.**
      Given the throttle fix alone hasn't stopped the crash class, and to slow credit burn during the ongoing
      investigation, operator directed reducing "planning worker count" by 8. Implemented via the existing
      `POST /api/slots/{id}/pause` (sets `status=paused`; already respected by `TmuxPruner`/`AutoSpawn` as operator
      intent — no code change needed, fully reversible via `POST /api/slots/{id}/resume`). Checked slot state first
      (`GET /api/state`, HS256 JWT minted on-VM per the `[[orch-dispatch-recipe]]` pattern — secret never leaves the
      VM): 25 idle, 9 working (`[7,12,13,14,15,16,24,32,33]`), 0 already paused. Paused the 8 highest-numbered IDLE
      slots (`[23,25,26,27,28,29,30,31]`) — zero active work disrupted. Fleet is now 26 active / 34 configured.
      **Operator's fallback plan if this doesn't help** (not yet executed, staged for if needed): kill all roles except
      escalation, confirm stable, re-add scheduled tasks, confirm stable, re-add planning workers — an incremental
      re-enablement to isolate which role/workload is the actual trigger. **Re-enlarge**: 8×
      `POST /api/slots/{id}/resume` on the same slot IDs once either root cause is found or the smaller fleet is
      confirmed not to help. Repo: agent-orchestrator (no code shipped — pure runtime state change).
- [x] [INFRA] P0. ~~Second mass burst even at reduced fleet + operator-directed scheduled-task shutdown~~ — **DONE
      2026-08-11/12.** A further mass `tmux_session_lost` (8 slots: 16,18,19,20,21,22,24,32,33) at 22:23:45 confirmed
      the 8-slot capacity cut alone had NOT stabilized things, and `orchestrator.service`'s own cgroup briefly hit
      `available: 2.9M` of its 26GB ceiling (load 41.44/37.75/28.13) — though `oom_kill` stayed 0 throughout (no actual
      kill fired; system-wide `free -h` still showed 18GB available — the cgroup's OWN ceiling was the binding
      constraint, not the host). Operator directed going further: stop ALL scheduled task dispatch, keep only
      escalations + the already-reduced planning pool. Built a NEW capability for this rather than a one-off action
      (operator ask: "make the dashboard have ability to pause all scheduled task individually by task type... so that
      an endpoint is exposed for it") — **SHIPPED `agent-orchestrator@7fb8581df7`**:
      `server/scheduled_dispatch_pause.py` (operator-toggleable pause registry, DB-persisted via `dedup_state`'s
      existing seen-keys pattern so a pause survives an orchestrator restart), gated at BOTH independent
      scheduled-dispatch chokepoints found (`plan_health.dispatch(mode=...)` — 10 of 11 modes — and
      `CIReconcileLoop.tick_once` separately, since it doesn't route through `plan_health.dispatch` at all), exposed via
      `POST /api/scheduled-dispatch/{mode}/pause`, `POST .../resume`, `GET /api/scheduled-dispatch/status` (mirrors the
      existing per-slot pause/resume shape). 24 new tests across 3 files. Applied live once `ao-self-pull` redeployed
      (~1h self-pull lag observed — worth investigating separately, see follow-up below): paused all 10 `plan_health`
      modes + `ci_reconcile`, left `escalation_reconcile` active (it maintains the escalation system itself, not a
      competing scheduled workload). **Dashboard UI toggle NOT built this pass** — the operator's concrete ask ("an
      endpoint is exposed for it") is satisfied; a UI wiring is a fast-follow, not done here to avoid shipping
      unpainted-Playwright-covered UI under this session's time pressure. **Observed after**: load 41.44 -> 2.20, cgroup
      Tasks 1183 -> 68, Memory 22.9G -> 2.3G (20.6G available) — a dramatic improvement, but ~2h of real elapsed time
      passed between the crisis reading and this one, so this is NOT cleanly attributable to the pause alone (the fleet
      could have settled on its own); the pause mechanism itself is proven correct and live (verified via
      `GET /api/scheduled-dispatch/status`), independent of whether it's what caused this specific recovery. Repo:
      agent-orchestrator.
- [ ] [INFRA] P2. **New lead found live: `sock_throttled` at the cgroup level.**
      `/sys/fs/cgroup/system.slice/     orchestrator.service/memory.events` carries a `sock_throttled` counter (not
      previously checked this investigation) that read **4,302,026** during the 22:35 load spike — an extremely high
      cumulative count of TCP-send-buffer memory-pressure throttle events at the cgroup level. Not yet connected to a
      specific death, but a promising NEW angle distinct from everything checked so far (cgroup OOM, host CPU/load,
      git-fetch concurrency, spawn concurrency) — socket-buffer throttling under memory pressure could plausibly affect
      tmux's own client/server IPC sockets specifically. **Done when**: correlate `sock_throttled`'s RATE OF CHANGE (not
      just the cumulative count) against known death timestamps, ideally with the live-capture script extended to sample
      it every second alongside load/spawns/newsess. Repo: agent-orchestrator.
- [ ] [INFRA] P3. **`ao-self-pull` took ~1h to redeploy a pushed commit, not the documented ~15min.** Confirmed via
      `/var/log/ao-self-pull.log`: `agent-orchestrator@7fb8581df7` landed on `live-defi-rollout` well before 22:45:01
      (its actual pickup time — the log shows
      `current (7fb8581) but running process predates HEAD...     restarting stale process` at exactly 22:45:01), but
      earlier `journalctl -u orchestrator` checks at 22:35 and 22:41 still showed the OLD checkout running — meaning
      either the push landed later than assumed, or the 15-min cron genuinely skipped 2-3 cycles. Not chased further
      this session (time pressure), but worth a dedicated look given a future urgent pause/config-toggle ship might need
      to actually confirm live sooner than "wait ~15min and hope." Repo: agent-orchestrator, unified-trading-pm (cron
      definition).
- [ ] [INFRA] P3. **Dashboard UI for scheduled-dispatch pause/resume.** The API
      (`POST     /api/scheduled-dispatch/{mode}/pause`/`/resume`, `GET .../status`) is shipped and live; a dashboard
      toggle (mirroring however per-slot pause is surfaced) was explicitly requested but not built this pass — needs its
      own `[UI]`-tagged todo with Playwright `pw:L2` coverage per the workspace's UI-testing HARD RULE, not bundled into
      this backend-only ship. Repo: agent-orchestrator (dashboard/).
- [ ] [INFRA] P0. **THIRD live catch, 2026-08-12 01:34:55 — happened WITH all scheduled tasks paused AND the reduced
      26-slot fleet.** `tmux_server_died`, 12+ slots/agents lost within 13s (`[1,5,12,14,15,16]` + 6 agent-scope). This
      is decisive: it rules out scheduled-task load as the sole/primary cause (none were dispatching — confirmed via the
      SAME window's log showing
      `scheduled-job drain: plan_reconciler:cefi... deferred (mode     'reconcile' is paused by operator)` and an
      external caller's `POST /api/plan-health/dispatch` correctly 503'd), and weakens the raw-fleet-size theory
      (already cut by 8). **New signature**: `journalctl` for 01:34:30-01:34:55 shows a STEADY stream of
      `POST /api/slots/N/git-status` calls sweeping nearly every slot (27,18,28,19,29,2,3,20,30,21,22...) roughly one
      every 1-2s, right up to the death — critically, from a MIX of `127.0.0.1` (local) AND external IPs
      (`103.251.212.47`, `152.37.120.206`), confirming **multiple physical hosts** are running their own
      `slot-git-status-report.sh` cron and hitting this ONE central endpoint concurrently, not just this VM's own copy.
      Checked the handler (`server/routes/git_health.py:224     post_slot_git_status`): cheap by design (client does the
      real `git status` work locally, server only writes one `SlotGitStatusRow` per call) — but every write still opens
      a real SQLite write transaction (`BEGIN IMMEDIATE`), so a ~30-wide burst of near-simultaneous writes from multiple
      hosts is real write-lock contention, the same class of problem `_do_spawns_concurrently`'s docstring cites as a
      PRIOR incident (143 "database is locked" errors, 2026-07-27). **Emerging pattern across all 3 live catches**: the
      EXACT signature differs every time (utempter/pane-creation burst #1; CPU/git-fetch/rg saturation #2; multi-host
      git-status POST storm #3) but all 3 share ONE thing — concurrent git/dispatch/spawn activity from MULTIPLE sources
      co-occurring with the death. No single mechanism has been proven causal yet (still correlation, not proof), but
      the common thread is now real signal, not noise. **Correction (2026-08-12, same investigation, operator pushback
      "why would that kill tmux?")**: checked part (a) — operator's own Mac crontab for `slot-git-status-report.sh` is
      `2,7,12,17,22,27,32,37,42,47,52,57 *     * * *`, IDENTICAL to the VM's own schedule (installed via the same
      self-updating cron-pull mechanism), i.e. **synchronized across hosts, not staggered**. This actually WEAKENS
      rather than confirms the git-status-storm hypothesis: if every host fires on the same grid, the 436-sample
      historical burst data should show a spike at that exact offset, and it didn't (uniform distribution, checked
      earlier this doc). `post_slot_git_status` itself is also a cheap DB write with no plausible mechanism to affect a
      separate OS process (tmux) at all. Retracting this as a causal candidate — the correlation for that one incident
      was likely a symptom (marker of high fleet activity), not a cause. Also verified, per the same pushback: `SlotRow`
      (the real fleet/tmux tracking table) has no host dimension and is written exclusively by VM-local processes;
      git-status reporting is separately keyed by `(host, slot_id)` — confirmed the operator's own local interactive
      sessions do NOT bleed into or get confused with the VM's real dispatched-worker slot tracking.
- [ ] [INFRA] P0. **FOURTH live catch, 2026-08-12 01:34:55 — new, stronger lead: `fleet-git-health-guard.sh` (root cron,
      `*/15 * * * *`, `agent-orchestrator/scripts/fleet-git-health-guard.sh`).** A broad (not just orchestrator-scoped)
      `journalctl` sweep at the exact death window (never done before this catch — always previously scoped to the
      orchestrator process's own log) found something new: at 01:34:40-01:34:41 — **14 seconds before**
      `tmux_server_died` at 01:34:55 — a rapid burst of `sudo git -C <repo> config     gc.pruneExpire never` immediately
      followed by `sudo git -C <repo> fsck --connectivity-only --no-progress`, repeating across many different repos in
      slots 20 and 23 in the log excerpt alone (instruments-service, unified-trading-library,
      market-data-processing-service, deployment-api, strategy-service, unified-trading-system-ui,
      client-reporting-api...). Unlike the retracted git-status theory, `git fsck     --connectivity-only` is genuinely
      expensive (a full object-graph traversal), and each repo needs TWO separate `sudo` invocations (PAM session
      open/close overhead each). The guard's own log (`/var/log/fleet-git-health-guard.log`) confirms a sweep started at
      01:30:01 — ~4m39s before the observed subprocess burst, consistent with a multi-minute sweep across ~1132
      directories × 2 sudo calls still being mid-flight at 01:34:40-41. **This is a genuinely different,
      previously-untested hypothesis** — the earlier cron-alignment refutation only tested the 5-minute grid
      (`slot-cron-ff-pull.sh`/`slot-git-status-report.sh`); this is a SEPARATE 15-minute root-cron with a MULTI-MINUTE
      active window, which a simple minute-offset test would never have caught. Rough fit against earlier live catches:
      18:10:50 is ~10-11min into the 18:00:01 run; 18:24:41 is ~9-10min into 18:15:01; 21:11:27 is ~11min into 21:00:01;
      all plausible if a full sweep can run 5-12 minutes depending on load — not yet independently confirmed (log
      timestamps are captured ONCE at run start and reused for both the "scanning" and "OK" lines, so run DURATION can't
      be read from the log directly; would need direct process-timing evidence like this catch's journalctl burst, for
      each historical death). **Correction (2026-08-12, same session, operator asked to contextualize the "never found a
      problem" claim)**: that claim was wrong as originally stated — it was based on a small recent `tail` sample, not
      the full log. The real log goes back to 2026-06-01 (6,720 total runs): 6,093 clean, ~600 runs (~9%) logged a
      `WARN:`. But the WARN history is NOT ongoing/organic corruption — it concentrates almost entirely in (a) the
      guard's own first ~4 days post-deploy (2026-06-01 to 06-04, expected bootstrap noise as fresh worktrees settled),
      (b) one already-separately-tracked rough day (07-13), and (c) a deliberately-named test fixture
      (`instruments-service.broken-empty-clone-20260805`) through 08-06. **Zero WARN lines in any run that overlapped
      with any of tonight's 3 known tmux deaths** — so fsck failures don't correlate with the deaths either. Net: the
      check has been genuinely clean for weeks; the original "no-op" framing was directionally right, just imprecisely
      stated.
- [x] [INFRA] P0. ~~fleet-git-health-guard.sh de-prioritized + overlap-locked, frequency cut to daily~~ — **SHIPPED
      2026-08-12, `agent-orchestrator@836d88fc52`, operator-directed.** **Major finding first**: live-measured a
      `--dry-run` full sweep on the VM — **16m55s elapsed**, LONGER than the 15-min cron interval this ran at until
      today. This is not a hypothesis anymore: consecutive invocations were **structurally guaranteed to overlap
      continuously** (a new sweep starting before the previous one finished), not as an occasional edge case — this
      alone is a genuine, independently-valuable finding regardless of whether it's THE tmux-death trigger. Shipped 4
      changes to `scripts/fleet-git-health-guard.sh`: (1) `nice -n19`/`ionice -c3` self-re-exec — this background
      maintenance work (100%-clean track record for weeks) should never compete with foreground tmux/orchestrator work
      for CPU/IO scheduling; (2) combined the two always-executed `sudo -u ubuntu` calls (git config + first fsck
      attempt) into one PAM session instead of two, halving that overhead for the common path; (3) a 0.5s stagger after
      each of the ~29 expensive main-clone fsck checks (NOT the ~986 cheap worktree root-owned-file checks, which stay
      tight); (4) an `flock`-based overlap lock (`-n`, fails fast rather than queuing) so a slow sweep skips the next
      tick cleanly instead of ever running two full sweeps at once — direct insurance for the 16m55s-vs-15min finding
      above, independent of frequency. **Also changed the root crontab** (surgical single-line edit, verified via `diff`
      before installing, backup saved to `/tmp/root_crontab_backup_*.txt`): `*/15 * * * *` -> `17 4 * * *` (once daily,
      04:17 UTC — picked to avoid the `:00`/`:03`/`:06`-hour boundaries several other daily/hourly jobs cluster on).
      **Validated live before shipping** (not just `bash -n`): self-test PASS (dedup state-machine logic unchanged), a
      full `--dry-run` completed clean, and a dedicated lock-contention test confirmed a second invocation correctly
      detects the held lock and exits near-instantly (0s) rather than starting an overlapping sweep. Repo:
      agent-orchestrator (script), root crontab (fleet-wide, not repo-scoped).
- [ ] [INFRA] P1. **New isolated (non-burst) single-slot death, 2026-08-12 14:03:55 UTC — slot 2, idle at the time,
      `pane_death_info` empty (session itself gone, same unrecoverable-via-pane-query signature as every prior catch).**
      Distinct from every catch above in one way worth tracking: `burst_size=1` — this one did NOT take any sibling
      slots with it, unlike the historical tmux-SERVER-death bursts (19-29 slots at once). Investigated read-only via
      SSM (`/api/activity?slot=2`) — no fleet-wide `tmux_server_died` alert fired in the same window, consistent with a
      genuine single-pane death rather than a server-wide one this time. **Shipped same session,
      `agent-orchestrator@<pending>`**: made every future `tmux_session_lost` event self-diagnosing instead of needing a
      manually-launched capture script in advance (todo above re: "Get real tmux/system-level evidence" — this automates
      that ask going forward). Added to `server/tmux_pruner.py`'s existing `capture_pane_death_info()` call site: (1)
      `host_snapshot` — load avg + RAM/swap % via a new stateless-only `host_resources.stateless_snapshot()`
      (deliberately excludes `cpu_percent()`/`iowait_percent()`, which mutate module-global delta state assumed
      single-caller by the externalized resource-history sampler — see that function's docstring); (2)
      `tmux_server_alive` (`tmux_server_running()`, reused); (3) `burst_size` (free — `len(dead_slots)` this tick); (4)
      `pane_tail` — scrollback off the dead pane via the already-imported `capture_pane()`, empty when the whole session
      was already gone but a real bonus (crash text, auth modal, rate-limit banner) whenever the pane object survived;
      (5) `rate_limit_in_tail` — reuses the file's own existing `_RATE_LIMIT_RE` (already proven live: the 2026-08-11
      "production breakthrough" catch above found an HTTP 429 retry loop directly preceding a tmux-server death) against
      that tail; (6) `account_id` + `account_snapshot` (`account_status`/`rate_limited_until`/`overage_status`/
      `overage_disabled_reason`/`auth_failed_at` via the existing `get_or_create_usage()`) — tests the standing
      account-level rate-limit/quota hypothesis (fleet_wide_deepseek_crash_loop_undetected_2026_08_11) automatically for
      every death, no manual DB join needed after the fact. **Done when**: the next several live deaths (isolated or
      burst) are compared against these new fields — specifically whether `rate_limit_in_tail`/`account_snapshot` shows
      unhealthy account state disproportionately, which would be the first direct evidence FOR the account-level
      hypothesis rather than the account-agnostic conclusions reached so far. Repo: agent-orchestrator.
- [ ] [INVESTIGATE] P0. **New external lead, 2026-08-12 (operator ask: "think outside the box... only so many ways a
      tmux session can die... use Context7 or the web").** Every check in this doc so far has assumed the cause is
      environmental (host load/OOM/cgroup/tmux-server-itself) or infra-adjacent (spawn storms, git-fsck bursts,
      DeepSeek-side instability). None of it has checked whether this is a KNOWN, still-open bug in the Claude Code CLI
      binary itself. A web search of `anthropics/claude-code` GitHub issues turned up a strong signature match:
      **anthropics/claude-code#27705, "[Bug] Crash on network interruption (VPN disconnect) with no session recovery"**
      (closed as `stale` — never fixed, just went inactive) — a VPN/network-path interruption produces a raw
      **`Abort trap: 6`** (SIGABRT) that kills the CLI process instantly, with NO graceful shutdown, no `SessionEnd`,
      and (per the reporter) all prior terminal output lost. This matches, feature-for-feature, every signature this
      investigation independently found the hard way: the "flat-then-instant-vanish, no degradation ramp" capture
      (healthy right up to the last 1s sample, then gone — exactly what a SIGABRT does, no drain/cleanup window); the
      RST-not-FIN abrupt socket teardown (an aborted process doesn't get to close sockets cleanly); the total absence of
      a macOS/Linux crash report in every check so far (a Bun-runtime-raised `abort()` may not register with
      `ReportCrash`/systemd-coredump the same way a segfault does — never specifically checked); and the 2026-08-11 live
      catch of an HTTP 429 retry loop (`Retrying in Xs · attempt 6/10`) immediately preceding a death — consistent with
      the CLI's own retry/network-error path being exactly where this class of bug lives. A DUPLICATE report,
      **anthropics/claude-code#27734** ("CLI crashes silently on intermittent network issues"), shows the same failure
      preceded by `AxiosError: timeout of 5000ms exceeded` / `ECONNABORTED` telemetry-export failures / 16 consecutive
      streaming-corruption errors in a 2-minute window — i.e. this is not VPN-specific, ANY network hiccup (which a
      fleet running dozens of concurrent workers doing heavy git/API traffic will produce routinely) can trigger it.
      Neither upstream issue has a confirmed fix or root-cause comment from Anthropic — both were closed by staleness
      bots, not resolved. **This reframes the search**: instead of continuing to chase host-level correlates, the
      fleet's own captured `pane_tail`s (new field shipped this session, see the todo above) should be grepped for
      `Abort trap`/`SIGABRT`/`ECONNABORTED`/the streaming-corruption message going forward — and the fleet's pinned
      Claude Code CLI version should be checked against whichever version (if any) eventually fixes #27705/#27734
      upstream. **Done when**: (a) a live death's `pane_tail` is grepped and shows one of these exact strings (confirms
      the match) or doesn't (weakens it); (b) the fleet's pinned CLI version is checked against the two upstream issues'
      reported versions (2.1.47, 2.1.50) to see if the fleet is even on an affected version; (c) if confirmed, consider
      filing a NEW upstream issue with this investigation's own evidence (SIGABRT specifically is more actionable for
      Anthropic than "tmux pane vanished") rather than waiting on the two stale-closed ones. Repo: agent-orchestrator
      (investigation), no code shipped for this lead itself this session — the two closed issues were surfaced via
      `gh issue view 27705/27734 --repo anthropics/claude-code`, not this fleet's own logs.
- [x] [INFRA] P0. ~~Root-caused + fixed why NO death ever produced a real forensic artifact~~ — **SHIPPED 2026-08-12,
      `agent-orchestrator@007995b3bd` + a live systemd drop-in.** Operator pushback on "no forensic trace" being treated
      as a dead end ("must be a way to figure out what's happened, can't just say it was random") led to checking the
      one thing never checked: whether core dumps were even POSSIBLE on this VM. They weren't — `ulimit -c` measured
      live as **0** for the whole `orchestrator.service` process tree, despite `kernel.core_pattern` already being
      correctly configured (`/tmp/core-%e-%p-%t`). Every SIGABRT/SIGSEGV-class death in this entire investigation had a
      real crash artifact available to produce and nothing was ever allowed to write it. **Fix**: `LimitCORE=infinity`
      added to `scripts/orchestrator.service` (repo template) — applied LIVE via a systemd drop-in
      (`/etc/systemd/system/orchestrator.service.d/override.conf`), NOT a raw file overwrite: the live installed unit
      differs from the repo template (`User=ubuntu`/path-substituted via `install-orchestrator-service.sh`, template
      still says `hk`) — cp'ing the template over it would have broken the live service. Limits inherit down the process
      tree at fork/exec, so every tmux session + `claude` worker this service spawns now gets it too — only processes
      spawned AFTER the restart, already-running workers keep the old (disabled) limit until their own next respawn.
      Wired `tmux_spawn.find_recent_core_dumps()` (broad `/tmp/core-*` glob within the last 120s, not pid-matched — most
      deaths have no known pid captured either, e.g. `pane_death_info is None`) into the same automatic per-death
      capture as the earlier host/account/pane fields, as `core_dumps_found`. Restarted live, verified healthy
      post-restart (`/api/healthz` uptime_seconds=47, real request traffic flowing, `LimitCORE=infinity` confirmed via
      `systemctl show`) — worker slots 14/16/17/26/27 posted successfully right through the restart, confirming
      `KillMode=process` protected them as designed. **Also added** (operator ask, the historically-manual `pgrep`-based
      `newsess=`/`spawns=` signal from the live-capture script): `concurrent_recent_spawns` — DB-only count of
      `SlotRow.last_spawned_at` within the last 60s, in the same capture, no subprocess needed. **Done when**: the next
      live death (isolated or burst) is checked for a populated `core_dumps_found` — that's the first real test of
      whether this VM's crash class actually produces a core at all (an uncatchable external SIGKILL, e.g. from the
      still-unconfirmed tmux-server-death mechanism, produces NO core regardless — cores only capture self-inflicted
      signals like SIGABRT/SIGSEGV/SIGBUS). 3 new tests. Repo: agent-orchestrator.
- [ ] [INVESTIGATE] P0. **First two GENUINELY VALID core-dump tests, 2026-08-12 — both came back empty, real evidence
      against a self-inflicted crash.** The `core_dumps_found=[]` on every death checked immediately after the
      `LimitCORE=infinity` fix landed (17:01:31Z) was NOT meaningful at first — checked spawn history directly for
      several of those deaths (slots 1, 2, 32) and found none had actually respawned since the fix; they were the same
      long-lived sessions from before it (`worker_one_task_per_session_reset` reuses one session across many tasks
      rather than forking fresh per-task, so "wait for natural rotation" doesn't cycle workers onto the fix quickly).
      Worse: a **tmux-SERVER-wide** crash needs the SERVER process itself (not the individual workers) to have inherited
      the limit, and the server is even more persistent than a worker — it only restarts when it crashes, which is the
      exact event under investigation. Built `scripts/orchestrator/watch_tmux_server_lifecycle.sh` (promoted this
      session, ao_tmux_session_loss root-cause follow-up) to track the tmux server's own PID across restarts and race to
      check `/tmp` the instant it changes. **First genuinely valid catch**: server PID 2489725 (started 18:16:30Z,
      confirmed live via `/proc/<pid>/limits` to have `Max core file size = unlimited`) transitioned to PID 3270796
      sometime before 18:45:22Z — `/tmp` checked immediately after: no core file. **Second catch**: PID 3270796 (also
      confirmed `unlimited`) transitioned to PID 168030 at 19:20:16Z — same immediate check: no core file either. Both
      transitions are clean, valid tests (the dying server confirmed running with core dumps enabled beforehand) — and
      both produced nothing. Since a core dump is ONLY ever produced by a self-inflicted signal
      (SIGABRT/SIGSEGV/SIGBUS/SIGILL/SIGFPE) and an external `SIGKILL` (OOM-killer, a cgroup enforcement action, or an
      external process explicitly killing it) never produces one regardless of `ulimit`, **this is real evidence
      pointing AWAY from a self-crash and TOWARD an external kill** — narrowing, not just re-confirming, the standing
      mystery. Still n=2 and still doesn't name the killer. **Caught live building the watcher**: the detection script's
      first version had two field-parsing bugs (`ps -eo ...,lstart,comm`'s multi-token date format, and the tmux
      server's own `comm` being the two-word string `"tmux: server"` with an embedded space) that together caused it to
      silently report "no server running" for 22 minutes while a real server was up the whole time — missed that
      server's actual death+respawn live as a direct result. Fixed (grep the literal substring, not any field-position
      match) and verified against live output before trusting it unattended again — full traps documented in the
      script's own header for the next person who edits this detection line. **Done when**: (a) a third+ clean catch
      either reinforces "always empty" (strengthening the external-kill case) or finally produces a core (pointing back
      toward self-crash for at least one instance — these need not share one mechanism); (b) if the external-kill case
      holds up, pivot the investigation from "why does the process crash" to "what has authority to SIGKILL the tmux
      server" — candidates not yet checked: the OOM-killer (previously ruled out via `oom_kill=0` in the
      `orchestrator.service` CGROUP's own counters, but the tmux SERVER may sit OUTSIDE that cgroup per this doc's
      earlier finding — check `cat /proc/<tmux-server-pid>/cgroup` and that slice's OWN `memory.events` next), a
      systemd/cgroup TasksMax or similar limit, or a still-unidentified external actor. Repo: agent-orchestrator.
- [ ] [INVESTIGATE] P0. **Two more bursts, 2026-08-12 19:45:24Z (7 slots, `affected_slot_ids` incl. 1/2/7/14/16/18/32)
      and 19:57:15Z (6 slots) — the "tmux SERVER sits outside the cgroup" hedge from the entry above is REFUTED, not
      just re-checked**: `/proc/<pid>/cgroup` for the live server (PID 1272011, born 19:57:22Z, right at the second
      recovery) reads `0::/system.slice/orchestrator.service` — it IS inside the service's own cgroup, same as every
      worker pane. `memory.events` for that cgroup AND its `system.slice` parent both read `oom_kill=0`; `dmesg -T` has
      zero OOM/segfault/kill lines anywhere near either timestamp; `host_snapshot` at both deaths shows ample headroom
      (ram~~10-16%, swap~~0.8%); `/proc/<pid>/limits` on the live server confirms `Max core file size: unlimited` — the
      `LimitCORE=infinity` fix is genuinely live on a tmux server process born AFTER it landed; fd usage is 14/1024 (no
      exhaustion) against 9 hosted panes. A broad post-death sweep (`/tmp`, `/var/crash`, `/var/lib/systemd/coredump`,
      -30min) found **zero core files anywhere on the host** — not just `/tmp`. This is the first AUTOMATICALLY-captured
      clean test (no live watcher needed — `tmux_server_died`/`_recovered` + `tmux_session_lost`'s `core_dumps_found`
      already caught it) and it's n=3 alongside the two manual catches, same result: self-crash, kernel OOM-killer,
      cgroup-OOM, low-memory, and fd-exhaustion are now ALL ruled out for this instance. Not a spot instance either
      (`instance-life-cycle`/`spot/instance-action` metadata both empty). **What's left**: an external SIGKILL from an
      actor that isn't the OOM-killer or a cgroup limit (unidentified), OR the tmux server exiting via its OWN internal
      fault path with no signal at all (a tmux-side bug/assertion under 6-9 concurrent heavy panes — plausible and NOT
      yet checked; would also produce no core and no dmesg trace). Passive log/state inspection is now exhausted — next
      step has to be a LIVE attach (`strace -p <tmux-server-pid> -e     trace=signal,exit_group` or similar, per
      `/codex/15-runbooks/isolated-deepseek-crash-debug-sandbox.md`'s own methodology) running continuously across a
      death to see the actual exit path in real time. Repo: agent-orchestrator.

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
- 2026-08-12 22:38Z: **mistake, corrected same tick** — death #7 (22:36:57Z→22:38:15Z) happened while the FIRST
  supervisor variant (`-f`, following every forked pane) was attached and should have recorded it, but its log growth
  (113MB→648MB/14min) prompted a fix-and-redeploy whose cleanup `rm -f`'d the log before it was ever read —
  unrecoverable. Fixed (`agent-orchestrator@ee8de4c3d9`, dropped `-f` — only the top-level pid's own signals matter) and
  added a standing rule: never kill/delete an armed trace without grepping it for a fatal-signal match FIRST.
- 2026-08-13 00:06Z-00:38Z: death #8 confirmed the self-kill mechanism, fix shipped, briefly declared root cause found —
  then death #9 FALSIFIED it (same signature on the exact pid I'd live-confirmed `exit-empty off` on, ~20min earlier).
  Self-corrected rather than let the wrong claim stand — full detail + next step (`auditctl` tmux-execve watch, now
  armed) in the "Mechanism CONFIRMED, root TRIGGER still open" section above. Kept the exit-empty fix (harmless either
  way), retracted the "verified" claim. Loop continues, not done.
