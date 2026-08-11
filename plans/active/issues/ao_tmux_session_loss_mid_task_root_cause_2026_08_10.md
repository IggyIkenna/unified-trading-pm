---
doc_type: issue
title: >-
  Fleet dispatch:done gap is driven by unplanned tmux session loss mid-task, not watchdog kills — root cause not yet
  found
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
      `launchd`-attributed "exited due to SIGKILL sent by X" line exists for this PID — that attribution only covers
      launchd-managed services, not a plain tmux child process, so the actual signal-sender remains unidentified via
      `log show` alone. **Practical ceiling reached for post-hoc unified-log archaeology on this Mac** — getting the
      actual sender needs either live kernel signal tracing (`dtrace`/`ktrace`, needs SIP considerations) attached
      BEFORE the next death, or shifting the live-catch to the production Linux VM where core dumps are already enabled
      and root access is available via SSM. **Done when**: a live-caught death's underlying cause is identified from
      OS-level evidence (not just "confirmed absent again"), or enough sandbox runs accumulate that a pattern (timing,
      account, task shape) emerges. Repo: agent-orchestrator.
- [ ] [INFRA] P1. **New lead (2026-08-11, production breakthrough): find the tmux SERVER process's own resource envelope
      and monitor IT specifically, distinct from every check so far.** Live-caught a death where the ENTIRE tmux server
      for `ubuntu` vanished, not one pane (see Progress Log) — every cgroup/OOM check this doc has run (including the
      definitive `orchestrator.service` `oom_kill=0` ruling) covers the cgroup worker PANES inherit, never the
      freestanding tmux SERVER process itself, which per `server/tmux_spawn.py`'s own comments on the (unarmed)
      per-worker memory-cap feature likely sits outside any per-service cgroup entirely. **Done when**: (a) confirm what
      cgroup/slice the tmux server process actually runs under on a live check
      (`cat     /proc/<tmux-server-pid>/cgroup`), (b) if it's unconfined or under a DIFFERENT slice than
      orchestrator.service, check that slice's own `memory.events` oom_kill counter for a nonzero reading correlated
      with known death timestamps. Repo: agent-orchestrator.
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
- [ ] [INFRA] P1. **Root mechanism still open — cron ruled out, resource pressure and the per-slot check's own
      reliability under load are the two live candidates.** Two competing explanations remain, not yet disambiguated:
      (a) the tmux SERVER process genuinely dies/restarts under real resource pressure that scales with production load
      (explains the 08-11 00:37 step-change coinciding with live trading starting, and is now confirmed real via the
      shipped `tmux_server_running()` alert catching 3 genuine `tmux list-sessions`-fails-with-server-gone instances);
      (b) some/most of the OTHER large `tmux_session_lost` bursts are an artifact of the per-slot `has_session()` sweep
      itself becoming unreliable/slow under load (CPU/subprocess-spawn contention from a much busier fleet), reporting
      false "session gone" for panes that are actually still alive, without the server itself ever going down — the
      now-fixed detection gap above could not distinguish these until this fix ships and accumulates more paired
      samples. The abandoned cron-alignment hypothesis at least correctly identified the RIGHT class of cause (something
      tied to fleet-wide load), just not the right trigger. **Done when**: (a) with the detection-gap fix live, collect
      a larger paired sample of `tmux_server_died` vs. large `tmux_session_lost` bursts to see if the gap between them
      closes (supports mechanism (a) more cleanly) or stays open (points at (b)); (b) capture the tmux server's own
      PID/FD/thread count and `has_session()` call latency DURING an active burst (not post-recovery) — still not done,
      needs a live burst to sample against, paused per operator instruction pending resumed production dispatch. Repo:
      agent-orchestrator.
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
