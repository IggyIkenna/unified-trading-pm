---
doc_type: issue
title: >-
  Scheduled-audit "dispatched" != done — slot-level stale-flip bug, undersized reserve/timeouts, and a cgroup-root
  weight bug all fixed in one 2026-08-04 session; two of four are shipped+verified live, the last is a live-only VM
  config now tracked here
summary: >-
  Operator asked "did AO run every scheduled auditor last night, and does dispatched mean done" — answer was no and no
  (71% no_capacity under the old 2-slot reserve; of what did dispatch, ~50% silently died as reaped-stale without
  reaching lifecycle-complete). Root-caused and fixed four independent, stacked problems: (1) health.py's WORKING-slot
  stale-flip lacked the scheduled/one_shot lifecycle exemption the AgentRow-level dimmer already had, so a legitimately
  long-silent audit worker got its slot killed after 25min — fixed + shipped (agent-orchestrator@476494b). (2)
  scheduled_task_slot_reserve was 2 while a single sharded job's own batch width was 3 — raised reserve to 4 and matched
  batch width, shipped same commit. (3) curl --max-time (2400s) and systemd TimeoutStartSec (2450s) were sized from a
  borrowed pre-sharding estimate, never measured — real tranches now measured up to 64.9min; raised to 7200s/21600s —
  shipped (agent-orchestrator@17939c3). (4) THE DOMINANT one, found only after live-testing exposed (1)-(3) weren't
  sufficient: a cgroup-root sibling weight bug (system.slice vs github.slice both default weight 100, so
  orchestrator.service's existing CPUWeight=4000/IOWeight=1000 boost — itself undocumented in any repo — never actually
  protected it against self-hosted CI runner I/O contention). PSI-measured (not load-average- guessed): io pressure
  "full avg10" 57.34 before the fix, 32.58 within 5min after. A same-tranche redispatch went 0-of-3 successful
  completions before the fix, 3-of-3 immediately after. This file (`scripts/github.slice`) is committed in
  agent-orchestrator but the LIVE VM config was applied directly via SSM during this session and has not yet been
  re-verified after a VM restart/redeploy cycle — that's the one open risk this doc tracks.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    scheduled-jobs,
    reaped-stale,
    cgroup,
    psi,
    io-contention,
    na_eligibility_auditor,
    ag_closeout_auditor,
  ]
related:
  [
    /plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md,
    /plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md,
  ]
created: 2026-08-04
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: flat
last_updated: 2026-08-06
source: ["interactive session, operator-driven, 2026-08-04"]
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/health.py,
    agent-orchestrator/server/worker_liveness_watchdog.py,
    agent-orchestrator/server/config.py,
    agent-orchestrator/scripts/github.slice,
    agent-orchestrator/scripts/install-ag-closeout-auditor-timer.sh,
    /plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md,
  ]
---

# 2026-08-04: "dispatched" != done, and it took four stacked fixes to actually close the gap

## What was asked

Operator noticed the AO dashboard's Scheduled Jobs panel showing "58 failing" and a wall of `no capacity` rows, asked
whether every scheduled auditor ran last night and whether "dispatched" means "done". It doesn't, on either count.

## What I found and fixed, in the order discovered

### 1. Root cause of silent mid-run deaths: missing slot-level lifecycle exemption

`server/health.py`'s `check_once()` has TWO silence-based dimmers: one on `AgentRow` (already exempts
`lifecycle in ("one_shot","scheduled")` — see the code's own comment, dated well before this session), and one on
`SlotRow` (25min `STALE_THRESHOLD`, feeds `worker_liveness_watchdog._reclaim_idle_lingering_sessions`'s kill decision) —
which had NO such exemption. A scheduled/one-shot worker legitimately silent >25min (waiting on a backgrounded Workflow
fan-out, a slow quickmerge commit) got its SLOT flipped to stale, then killed ~2min later by the reclaimer unless its
tmux pane happened to show a "Crunched/Worked for Ns" completion phrase at that exact tick.

Directly corroborates `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`'s 6th/7th reports (same failure
family, different discovery angle — that doc traces the `/done` 400 symptom, this traces the earlier root kill).

**Fixed**: added the same lifecycle exemption to the slot-level loop, mirroring the existing AgentRow-level pattern.
Added loud `logger.warning` + richer `log_activity` details on the reap path (role/kind/label/runtime/last_msg) so any
future occurrence is greppable from `journalctl` alone.

**Shipped**: `agent-orchestrator@476494b`, deployed live (VM restarted 2026-08-04T09:45:16Z, confirmed via
`git merge-base --is-ancestor`). **Verified working**: live test agent `agt-87b8da` (na_eligibility_auditor) ran 39.6min
— well past the old ~27min kill window — and reached `lifecycle-complete` cleanly.

Tests: `tests/test_health_scheduled_lifecycle_exemption.py` (new), `tests/test_health_alert_dedup.py` (fixture extended
for the new `find_active_agent_for_session` call), `tests/test_scheduled_jobs.py` (2 new tests for the dashboard's
agent-status enrichment, see item 5 below).

### 2. scheduled_task_slot_reserve undersized vs actual batch width

`DEFAULT_SCHEDULED_TASK_SLOT_RESERVE` was 2 (operator-set 2026-07-29) while `MAX_CONCURRENT_TRANCHES` for
`ag_closeout_auditor`/`na_eligibility_auditor` was 3 — a single sharded job's own batch already exceeded its guaranteed
floor, structurally guaranteeing some `no_capacity` even with zero external contention. 30h live sample: 87 of 123
scheduled-dispatch attempts (71%) hit `no_capacity`.

**Fixed**: reserve 2->4, batch width 3->4 (both auditors) to match. Fleet math worked out to exactly 9 backlog slots
(down from a previous-effective 11) given the VM's 16 non-review slots and the unchanged CI-escalation reserve of 3 —
operator explicitly chose "9 backlog, not 10" over shrinking CI's reserve or provisioning a new physical slot.

**Shipped**: same commit as item 1 (`476494b`). Systemd units re-installed on the VM
(`install-ag-closeout-auditor- timer.sh` / `install-na-eligibility-auditor-timer.sh` re-run) — this is a REQUIRED
separate step; a `git pull` alone does not regenerate an already-installed systemd unit file.

### 3. curl --max-time / systemd TimeoutStartSec never measured against real runtime

Both were borrowed estimates (2400s curl, 2450s systemd) predating the 2026-07-26 sharding change, never re-measured.
Real single-tranche runtime (AgentRow `registered_at` -> `finished_at`) now on record: 6.5min-64.9min for
`na_eligibility_auditor`, similar spread for `ag_closeout_auditor` — several tranches already exceed the old 40min
ceiling. A tranche running long on a loaded host would get force-killed (systemd SIGTERM or curl client-timeout),
indistinguishable from a genuine hang — directly contradicts the operator's stated priority ("don't stop legitimate runs
early").

**Fixed**: curl --max-time 2400->7200 (2h), systemd TimeoutStartSec 2450->21600 (6h, covers 3 sequential batches of the
new width-4 batching at ~2h worst-case each). Deliberately generous — a safety-net ceiling for a genuinely wedged run,
not an expected typical duration.

**Shipped**: `agent-orchestrator@17939c3`, deployed live (VM restarted 2026-08-04T11:08:18Z after the self-pull script's
own restart attempt failed under an `ao-self-pull.sh` invocation-context permission issue — restarted directly via
`systemctl restart orchestrator` instead; not separately root-caused, noted as a minor follow-up below). Systemd units
re-installed to pick up the new `TimeoutStartSec`/`--max-time` values, confirmed on disk.

### 4. THE DOMINANT root cause: cgroup-root sibling weight bug (system.slice vs github.slice)

Found only after items 1-3 were live and a fresh redispatch STILL died young (agents dying in <20min, far under both the
old and new ceilings, and under the 25min mechanism item 1 already fixed). Activity-log showed MANY unrelated roles
(`review`, `cicd`, `data_pipeline_failure` — not just audits) getting mass-killed across many slots repeatedly.

Operator correctly pushed back on an initial "host load ~17 on 16 cores" hand-wave (load average conflates CPU and
I/O-wait; CPU% wasn't actually pegged) and asked for the real mechanism. PSI (`/proc/pressure/{cpu,memory,io}`) gave a
precise answer: `cpu` pressure ~0, `io` pressure `full avg10=57.34` (over half the time, EVERY task on the host
simultaneously stalled on disk I/O). Total process RSS summed host-wide was only ~7GB — ruled out "just needs more RAM".
Root cause: `systemctl show orchestrator.service -p Slice` -> `system.slice`; self-hosted CI runners live under
`github.slice/github-glue.slice/github-glue-runner.slice/...` — a COMPLETELY SEPARATE branch of the cgroup tree.
`system.slice` and `github.slice` were BOTH at the cgroup default weight (100/100) at the ROOT split. Orchestrator's
existing `CPUWeight=4000`/`IOWeight=1000` (a 2026-07-28 incident fix, itself never committed to any repo — lives only as
a live drop-in, `/etc/systemd/system/orchestrator.service.d/cpu-priority.conf`) only ever won fights WITHIN system.slice
— it did nothing against github.slice's aggregate demand, because that's a dead-even 50/50 root split regardless of
internal weighting. 3+ concurrent CI-runner cache-save `tar --use-compress-program zstdmt` jobs (one per repo finishing
a CI run) were enough to saturate disk I/O and starve every orchestrator-spawned tmux session on the other side of that
root split.

**Fixed**: `scripts/github.slice` (new, committed this session) — a static `[Slice]` unit with
`IOWeight=20`/`CPUWeight=20`, giving `system.slice` (hence orchestrator.service and everything it spawns) a 5:1
advantage at the root split during actual contention. Proportional-share, not a hard cap — CI runners are unaffected
whenever the host isn't contended (most of the time), and only yield bandwidth during simultaneous demand.

**Applied live** (SSM, 2026-08-04 ~13:40 UTC) but **NOT YET independently re-verified after a VM restart** — a plain VM
reboot or an unrelated redeploy could theoretically race the file being present before `systemd` reads it (it's
installed as a real static unit, so this should self-heal on boot, but hasn't been proven through an actual restart
cycle yet). **Verified via measurement, same session**: PSI io `full avg10` 57.34 -> 32.58 within ~5min; load average
17.26 -> 11.37. **Verified via outcome**: a same-3-tranche redispatch (`na_eligibility[sports]`,
`na_eligibility[infra]`, `ag_closeout[sports]`) went 0-of-3 successful completions immediately before this fix (2 hit
`no free slot`, 1 died reaped-stale at 17.4min) vs 3-of-3 successful dispatches immediately after (`agt-d4a899`,
`agt-8b3403`, `agt-7322c2` — NOT yet confirmed complete as of this doc's writing, see todos).

### 5. Dashboard observability: "dispatched" now shows real outcome

`GET /api/scheduled-jobs/recent` now joins each row's `dispatch_agent_id` to the live `AgentRow` and returns
`agent_status`/`agent_exit_reason`. `ScheduledJobsPanel` renders a derived `realRunOutcome` (running / complete /
went_stale / unknown) alongside the raw dispatch status, plus a distinct "N went stale" badge separate from the existing
"N failing" (quarantined/timeout/error) badge — so a silently-died-mid-run worker no longer looks identical to a genuine
completion. Shipped in `476494b` alongside item 1 (same commit, same review).

## Corrected an earlier claim in this session

Initially attributed the dashboard's historical "58 failing" badge to a `no_capacity`-miscount theory. That was wrong —
re-checked with `within_hours=48` (matching the frontend exactly): the 58 are genuine `status=timeout` reports, but ALL
58 are clustered within ~1.4 seconds of each other on 2026-08-02 ~11:34 UTC (`detail=None` on every one) — almost
certainly a single orchestrator-restart-in-flight artifact from that day, not 58 independent ongoing failures. Not
investigated further (out of window for this session); flagged here in case the pattern recurs.

## Incident: credential exposure this session (operator-acknowledged, not rotated)

A verification command (`ps aux | grep curl`) printed `ORCHESTRATOR_INTERNAL_SECRET` in plaintext in this session's tool
output (command-line args are visible to any `ps aux` caller on the host, not just the invoking session — this was a
self-inflicted diagnostic mistake, not an external leak). Operator was asked directly whether to rotate; decided to
leave it and move on. Recorded here per the workspace's findings-triage rule (a real finding needs a durable record even
when the operator declines to act on it) — if this secret's blast radius ever needs auditing later, this is the
timestamp or an alternative fix to be added later: pass such secrets via env var or `--header @file` in scripts, never a
raw `-H` command-line arg, which is a real, reusable lesson for every future dispatch-script edit here.

## Todos

- [x] ✅ [SCRIPT] P2. Re-verify `github.slice`'s weight survives an actual VM restart — VERIFIED 2026-08-06:
      `io.weight=default 20`, `cpu.weight=20`, systemd `LoadState=loaded`/`ActiveState=active`/`UnitFileState=static`,
      survived both VM restarts from 2026-08-04 (T09:45:16Z item-1 redeploy + T11:08:18Z item-3 redeploy).
- [x] ✅ [SCRIPT] P2. Check final outcome of the 3 redispatched tranches fired after the github.slice fix: `agt-d4a899`
      (na_eligibility[sports], slot 8), `agt-8b3403` (na_eligibility[infra], slot 9), `agt-7322c2` (ag_closeout[sports],
      slot 4) — CHECKED 2026-08-06 via `GET /api/agents?include_finished=true`: **NEGATIVE — all 3 ended
      `status=archived exit_reason=reaped-stale`, NOT `lifecycle-complete`** (`agt-d4a899` archived 2026-08-04
      T14:01:31.4Z, `agt-8b3403` T14:01:31.5Z, `agt-7322c2` T14:27:08Z). The fix does NOT hold under sustained real load
      on the basis of these 3. Root-cause note: the two na_eligibility tranches died in a MASS simultaneous session-loss
      at 14:01:32-14:02:35 that ALSO killed a cicd escalation (`agt-de0d1e` ldr_qg_failure, slot 4) and a review
      (`agt-99f380`) — a host/service-level teardown (slots 1/4/5/8/9), NOT auditor-specific IO contention; `agt-7322c2`
      died separately at 14:27:08 after ~36min. github.slice weights ARE confirmed live today (`LoadState=loaded`,
      `UnitFileState=static`, `IOWeight=20`/`CPUWeight=20`), and 08-06 auditor runs are now mostly `lifecycle-complete`
      (17/20) — see the follow-up todos below.
- [x] ✅ [SCRIPT] P3. Re-measure PSI io/cpu/memory a few hours after this fix, under a full day of normal CI+audit
      traffic, to confirm the 57.34->32.58 improvement holds (not just an artifact of the specific 5-minute window
      measured) and to tune `IOWeight=20`/`CPUWeight=20` against real data rather than this session's initial estimate —
      raise toward 50 if CI throughput visibly degrades, the file's own header comment already says so. — RE-MEASURED
      2026-08-06 12:27 UTC: PSI io full avg10=0.00 / avg60=0.03 / avg300=0.38 (vs pre-fix 57.34 avg10 / post-fix 32.58
      avg10); cpu full avg10=0.00; memory full avg10=0.00; load 2.44/2.87/2.88 on 16 cores; 61GB RAM (43GB avail).
      github.slice confirmed live (IOWeight=20/CPUWeight=20, LoadState=loaded, ActiveState=active). cpu-priority.conf
      present (CPUWeight=4000/IOWeight=1000). CI runners inactive during measurement (no zstdmt contention) — audit-only
      load shows zero pressure. Auditor completion today: 17/20 lifecycle-complete (3 reaped-stale). Tuning verdict:
      keep IOWeight=20/CPUWeight=20 — no evidence of CI throughput degradation at current weights, and
      audit-traffic-only pressure is negligible. Re-measure again if CI throughput complaints surface.
- [x] ✅ [SCRIPT] P3. Track `/etc/systemd/system/orchestrator.service.d/cpu-priority.conf` in a repo —
      agent-orchestrator@c6366f5 (scripts/orchestrator-cpu-priority.conf, mirrored from live VM drop-in with lifecycle
      markers + install instructions).
- [x] ✅ [DATA] P3. Investigate the 2026-08-02 ~11:34 UTC 58-way simultaneous `timeout` cluster (see "Corrected an
      earlier claim" above) if it recurs — not investigated this session, out of window. — **INVESTIGATED 2026-08-06
      (slot 3): CONFIRMED server-stall artifact, NOT a restart-in-flight artifact** (full detail in Progress Log). All
      58 rows carry `dispatch_agent_id=NULL` (no worker spawned) and their dispatch curls (timer-launched 05:30-10:45)
      hung against a ~5h API silence (activity_log empty 06:37→11:31) before burst-reporting timeout on recovery at
      11:31:32-11:34:04. First orchestrator restart that day was 12:00:01 (ao-self-pull) — ~26min after the cluster.
      Same class as the 08-05 04:00 cluster (SQLite `database is locked` stall, tracked in
      `orchestrator_db_pool_exhaustion_state_poll_stall` + `ao_db_lock_storm`). Recurs (08-01:25, 08-02:41+58,
      08-05:10); EVERY one of the 137 timeout rows has `dispatch_agent_id=NULL` — the dashboard "timeout" badge is
      uniformly stall artifacts, never a real per-dispatch failure. (repo: agent-orchestrator)
- [x] ✅ [SCRIPT] P2. Root-cause the 2026-08-04 14:01:32-14:02:35 "mass session-death" — NOT a discrete incident: host
      never rebooted (`last -x reboot`: up since 07-29, no 08-04 boot); `tmux_session_lost` fires 500-750×/day on every
      day (589 on 08-04, 752 on 08-03, 463 on 08-02, 309 on 08-05, all 16 slots) so the 5 events are routine churn, not
      a host/service teardown. Orchestrator restarted 14:00:05 via ao-self-pull (ao-self-pull.log
      `running process     predates HEAD — restarting stale process`; syslog stop 14:00:05.97 → shutdown snapshot
      14:00:11-18 → startup 14:00:23-26); KillMode=process preserved the tmux server (systemd "left-over process 3191830
      (tmux: server) ... Ignoring" at 14:00:18 — SAME PID as the 13:45 restart, so no cgroup/server teardown). The 5
      dead sessions were one-shot/scheduled/review agents dispatched 13:46-13:52 (na_eligibility slots 8/9, cicd slots
      4/5, review slot 1), alive at the last pre-restart pruner tick (~13:59) and gone by the first post-restart tick
      (14:01:32/14:02:35); no kill_session / watchdog-reclaim / respawn in the gap — the killer is not captured in any
      surviving log (journald reset 08-06 00:45). Pattern = the KNOWN collision class
      `persistent_slot_tmux_session_hijacked_by_transient_plan_health_dispatch_2026_08_01` (resolved 08-02 via
      agent-orchestrator@0c82906, which excluded ONLY review slots from transient picks — the 08-04 deaths hit the
      escalation/auditor slots 4/5/8/9 that fix does NOT cover, plus review slot 1 it should have protected). REAL
      issue: the 3 post-fix audit tranches (agt-d4a899 13:51→14:01:31, agt-8b3403 13:52→14:01:31, agt-7322c2 13:50→
      14:27:08) ALL died reaped-stale with empty last_msg / no /done — item 2's "3-of-3" was a false positive — but NOT
      one clustered incident (two restart-coincident at 14:01:31, one decoupled at 14:27:08, slot 7 survived the wave).
      The 14:33 respawn gap = next backlog dispatch to slot 8, not a recovery failure (plan_health dispatches are
      one-shot; AutoSpawn respawns tasks, not idle sessions). Evidence: state.db activity_log (`tmux_session_lost`,
      `plan_health_dispatch_initiated`, `spawned tmux session`) + agents rows + /var/log/syslog (systemd stop/start +
      left-over-process lines) + /var/log/ao-self-pull.log + /var/log/wtmp. No code change warranted — the premise was
      incorrect; the real gaps (incomplete collision fix, observability) are tracked as follow-up todos below. (repo:
      agent-orchestrator)
- [x] ✅ [SCRIPT] P2. Investigate the 2026-08-05 full-day `no_capacity` for ALL scheduled auditors: every
      na_eligibility/ag_closeout/plan_reconciler/docs_reconciler run hit no_capacity (0 dispatched all day), plus the
      01:45 na_eligibility batch TIMED OUT at 04:00 (~2h15m) — scheduled audits effectively did not run on 08-05.
      Confirm whether the fleet was genuinely saturated or a reserve/dispatch bug (item 2's reserve 2->4 + batch 3->4
      was live by then). — **VERDICT 2026-08-06: a DISPATCH bug + external Claude-credit outage, NOT fleet saturation**
      (agent-orchestrator@ef44eb9, the fix, shipped the next morning — see below). 225/240 (94%) of the day's
      no_capacity = `no headroom setup-token account available`: plan_health's account pick was Claude-only
      (`pick_headroom_account(provider='anthropic')`), blind to the 2 healthy DeepSeek accounts, and an 08-05 live
      Claude-credit/usage outage left all 6 Anthropic accounts exhausted (sub-c/sub-d disabled since 07-31; sub-b 99%
      weekly rate-limited→08-09; sub-f 99%; sub-a disabled 00:05→22:49; only the 22:53 context_scout + 23:16
      docs_reconciler landed on Claude after sub-a re-enabled 22:49). Only 14/240 = `no free configured slot` — item 2's
      reserve 2→4 + batch 3→4 were LIVE and functioned, NOT the bottleneck. Fleet was NOT saturated: DeepSeek spawned
      630× that day (4 deepseek-v4-pro review agents 10:49-19:21) while 0 scheduled audits dispatched. Fixed by
      agent-orchestrator@ef44eb9 (2026-08-06 04:58 UTC, "close 3 DeepSeek routing gaps") — plan_health dispatch,
      worker_liveness failover, and account-rotation now route through the DeepSeek-aware `select_account_for_spawn()`;
      live + verified (08-06 audits dispatch on Claude AND DeepSeek: 12+12 of the custom-role agents on
      deepseek-v4-pro/flash). The 04:00 `timeout` cluster (all dispatch_agent_id=null — no workers spawned, pure
      server-stall artifacts) = SQLite `database is locked` contention 01:45→04:00 (34-57 err/hr in hrs 00-03) stalling
      the API; pending dispatch curls exceeded curl --max-time → HTTP 000 → `timeout`. Follow-up todos below: stale
      plan-reconciler unit, unreinstalled reconciler ceilings, no_capacity-never-alerts gap. (repo: agent-orchestrator)
- [x] ✅ [SCRIPT] P2. Re-install the plan-reconciler timer unit on the orchestrator VM from the repo installer
      (`sudo bash scripts/install-plan-reconciler-timer.sh`): the LIVE `/usr/local/bin/plan-reconciler-dispatch.sh` +
      `/etc/systemd/system/plan-reconciler.service` still run `--max-time 2400` / `TimeoutStartSec=2450` while the repo
      installer (updated 2026-07-30) generates 5950/6000 — a git pull alone does not regenerate an installed unit (the
      exact gap this doc's item 3 warns about). Under an API stall (as on 08-05) the old 40-min curl ceiling
      force-terminates a legitimately-pending dispatch and reports a false `timeout`. (repo: agent-orchestrator) — DONE
      2026-08-06 15:04 UTC (operator-approved sudo, same pass as the docs-reconcile/context-scout re-install below).
      Verified live: `TimeoutStartSec=2450→6000`. NOTE the re-install ALSO applied the repo's intended cadence widening
      `OnCalendar=*:00 → 0/2:00` (hourly → every 2h, even hours) — the live unit predated the 2026-07-30 widening;
      flagged here because this todo's text only mentioned the timeout.
- [x] ✅ [SCRIPT] P3. Bump the docs-reconcile + context-scout dispatch ceilings — both repo installers AND live units
      still run `--max-time 2400` / `TimeoutStartSec=2450` (the 08-04 item-3 bump covered only the auditors; these two
      were never raised). Bump to plan-reconciler's 5950/6000 and re-install the two units; same false-`timeout` class
      under a stall. (repo: agent-orchestrator) — agent-orchestrator@4eda2be (installers bumped: --max-time 2400→5950,
      TimeoutStartSec 2450→6000 in both) + LIVE VM RE-INSTALL DONE 2026-08-06 15:04 UTC (operator-approved sudo);
      verified live: docs-reconciler + context-scout both now `TimeoutStartSec=6000`.
- [x] ✅ [DATA] P3. Alert gap surfaced by the 08-05 outage: a FULL-DAY `no_capacity` for every scheduled auditor
      (account pool exhausted) is NOT self-resolving and does NOT page — `SCHEDULED_JOB_FAILURE_STATUSES` deliberately
      excludes `no_capacity` as "routine". Add a detector for "zero scheduled dispatches in a 24h window / N consecutive
      no_capacity across jobs" → page. (repo: agent-orchestrator) — RESOLVED AT THE ROOT instead of by a detector:
      agent-orchestrator@5087f30 makes a scheduled dispatch QUEUE rather than drop on no-capacity
      (`ScheduledJobQueueRow`, dedup PK `<job>:<tranche>:<day>`, drained by the AutoSpawn tick, 24h abandon), so the
      condition this detector was meant to catch no longer silently loses work — a scheduled caller should never report
      `no_capacity` again. Paired with agent-orchestrator@5087f30's 503-classification fix, which stops a genuine
      quarantine being filed under the non-paging `no_capacity` bucket (42 such rows over 08-04..06). Deployed +
      verified live 2026-08-06 15:04 UTC.
- [x] ✅ [DATA] P3. Track residual `reaped-stale` after the fix: on 08-06, 3/20 auditor runs still ended reaped-stale
      (04:31 `agt-b334ff` ~37min, 06:31 `agt-121905` ~35min — no `tmux_session_lost` event in the archival window, so
      the sessionless-silent path) while siblings in the same batches completed. Determine mid-run death vs post-work
      /done failure. (repo: agent-orchestrator) — **CLOSED 2026-08-11 (slot 25) — superseded, not re-derivable.** Live
      `agents` table now retains only ~250 rows (oldest 2026-08-05 22:53); neither named agent survives, so a
      per-instance re-diagnosis is impossible (data gone, not just hard to read). The general question is already
      tracked at far greater depth in `/plans/active/issues/ao_tmux_session_loss_mid_task_root_cause_2026_08_10.md` (P2,
      open, active today): 94% of redispatch gaps show `tmux_session_lost` with no planned-teardown precursor — confirms
      this todo's "sessionless-silent" hypothesis as the dominant pattern, not post-`/done` failure. That doc is the
      live SSOT going forward. Flagged there for the owner: today's snapshot shows reaped-stale at 93/152 (61%) vs
      8-12/day on 08-09/08-10 — worth a fresh look. No code shipped. (repo: agent-orchestrator)
- [x] ✅ [SCRIPT] P3. Extend the 08-01 session-collision fix (agent-orchestrator@0c82906 excluded ONLY review slots from
      `plan_health._pick_free_slot` / `escalation._pick_free_slot`) to the escalation/auditor slots: the 08-04 deaths of
      freshly-dispatched cicd (slots 4/5) + na_eligibility (slots 8/9) agents' sessions around the 14:00 ao-self-pull
      restart show the same collision class hits non-review slots, and review slot 1 still died despite the fix —
      determine the exact killer (no surviving log captured it) before extending. (repo: agent-orchestrator) —
      agent-orchestrator@5941552 (slot-6, 2026-08-06, QG green 2536 passed). Root-caused + shipped: see Progress Log.
      Both pickers now skip any slot with `spawn_base_role` set (the DB-backed claim of an in-flight typed dispatch, set
      at claim time by `claim_slot_for_typed_agent()`, survives restarts in SQLite) — closing the TOCTOU race for EVERY
      slot hosting a typed one-shot, not just review slots. Release points added so a finished/torn-down typed slot
      returns to the free-slot pool: `_done_one_off`, `reset_slot_worker_state`, and the pruner's slot-loss branch (+
      the existing `_typed_occupant_liveness` stale-clear). 5 new regression tests.
- [x] ✅ [DATA] P2. **Bumped from P3 2026-08-09** (see the bump-todo below): reaped-stale rate is climbing day over day
      (1/08-06 -> 4/08-07 -> 18/08-08 -> 46/08-09) and the mid-run-session-death re-check todo above is blocked on this
      instrumentation for a causal (not just correlational) answer. Observability gap surfaced by the root-cause: the
      exact process that kills per-slot tmux sessions around orchestrator restarts is invisible — no `kill_session`
      call, watchdog reclaim, or systemd signal is logged, only the pruner's later `has_session()` detection (which
      fired 589× on 08-04). Instrument the session-teardown paths so a future recurrence is attributable from
      journalctl/syslog alone. (repo: agent-orchestrator) — SHIPPED agent-orchestrator@0c27963 (2026-08-10): every
      kill_session now logs a `SESSION-TEARDOWN ... reason=... sha=...` line (all 18 call sites tagged); new
      `config.running_checkout_sha()` (cached short SHA of the running build — the build that observed the death);
      tmux_pruner logs a per-slot "GONE mid-task ... reaped-stale candidate" WARNING for a slot that died holding a
      task, and stamps `checkout_sha` onto every `tmux_session_lost` activity row + the reaped-stale WARNING;
      orchestrator startup/shutdown record the running SHA + live-session inventory to bracket the restart window. 5 new
      tests (tests/test_session_teardown_instrumentation.py) + 25 existing assertions updated to the `reason=` contract.
      QG green 3107 passed.
- [x] ✅ [DATA] P2. Verify the capacity QUEUE end-to-end on live traffic (agent-orchestrator@5087f30, deployed
      2026-08-06 15:04 UTC): confirm (a) a real no-capacity dispatch now records `status="queued"` rather than
      `no_capacity` in `/api/scheduled-jobs/recent`, (b) the AutoSpawn drain dispatches it when headroom returns and
      `ScheduledJobQueueRow.status` flips `queued -> dispatched`, and (c) the dedup PK holds — an hourly retry across a
      multi-hour outage leaves exactly ONE row per `<job>:<tranche>:<day>` and produces exactly ONE worker. Unit tests
      cover all three (`tests/test_scheduled_jobs.py`), but no live no-capacity window has occurred since deploy. —
      **VERIFIED LIVE 2026-08-09** against the live SQLite state (S3 DR backup
      `s3://uts-orchestrator-state-427895769566/backups/sqlite/planning/2026-08-09/live_20260809T210230Z.db`, not SSM —
      see Progress Log for why). All three hold: (a) 0 `no_capacity` rows in `scheduled_job_runs` since deploy, 136
      `queued` reports instead. (b) `scheduled_job_queue`: 100/100 rows now `status=dispatched` (spans 2026-08-06 20:00
      -> 08-09 07:55 created, drained same window, wait times up to ~3h), `scheduled_job_queued`
      /`scheduled_job_queue_dispatched` activity events 100/100 matched 1:1. (c) 0 duplicate `queue_key` rows (PK
      holds); 100 distinct non-null `dispatch_agent_id` across 100 rows — exactly one worker per drained row, confirmed
      on a real multi-hour-wait case (`plan_reconciler:ao:2026-08-09`, queued 02:01 -> dispatched 02:47, `agt-fe4564`,
      one worker). New minor finding tracked below (not a correctness bug — no double-dispatch, no lost work). (repo:
      agent-orchestrator)
- [x] ✅ [DATA] P3. Same-day timer refire AFTER its `<job>:<tranche>:<day>` queue row is already `status=dispatched`
      reports a misleading `status="queued"` in `/api/scheduled-jobs/recent` — found live 2026-08-09 verifying the todo
      above. `_queue_for_capacity()` (`server/plan_health.py`) unconditionally returns `{"status": "queued", ...}`
      regardless of whether `queue_scheduled_job()` actually (re-)queued the row or hit its `else: return row` no-op
      branch (already dispatched that day — deliberately not re-queued, to avoid double-dispatch). No work is lost (the
      tranche already got its one worker earlier that day) and the dedup PK still holds, but the LABEL is wrong: a no-op
      read as "queued" looks like real pending work on the dashboard, and no run will ever complete for that specific
      report. Live example: `ag_closeout_auditor:ao:2026-08-09` — worker `agt-41d860` dispatched 02:31, then 3 more
      `queued` reports at 00:40/02:31/07:55/08:40 for the same key, none of which will ever get their own worker. Fix:
      have `_queue_for_capacity()` (or `queue_scheduled_job()`) distinguish "freshly queued/attempts bumped" from
      "already dispatched today, no-op" and return a distinct status (e.g. `"already_dispatched_today"`) for the latter.
      (repo: agent-orchestrator) — SHIPPED agent-orchestrator@a38423e889. `_queue_for_capacity()` now returns
      `status="queued"` only when `queue_scheduled_job()`'s row is genuinely `status=="queued"` (fresh insert or a
      bumped still-pending retry); the no-op branch (row already `dispatched`/`abandoned`) now reports
      `f"already_{row.status}_today"` instead. All 10 `install-*-timer.sh` dispatch scripts updated to recognize the new
      status and skip re-reporting a phantom dispatch attempt for the no-op case (a real "dispatched" row already exists
      for that tranche/day) — otherwise the bash script's `grep -q '"status":"queued"'` check would have fallen through
      to its DISPATCHED branch and filed a false `status="dispatched"` row with no agent_id, trading one mislabeling bug
      for a worse one. 2 new regression tests in `tests/test_scheduled_jobs.py`
      (`test_queue_for_capacity_reports_queued_for_a_fresh_defer`,
      `test_queue_for_capacity_distinguishes_same_day_refire_after_dispatch`). QG green: 3445 python passed, 295
      vitest passed, tsc clean.
- [ ] [DATA] P3. Confirm the hoisted working-pane guard reduced false spawn-retry-cap pages (agent-orchestrator@9d26598,
      deployed 2026-08-06 15:04 UTC). Baseline to beat, measured 2026-07-30..08-06 from the orchestrator journal: 45 cap
      declarations, pane state at cap = frozen 19 / no_session 11 / **working 8** / idle 7. The 8 `pane=working` pages
      were false by construction (the guard sat AFTER the cap branch, which `continue`s, so a capped slot never
      consulted it). Re-measure the same 7-day window post-deploy; `working` should go to ~0. If it does not, the
      remaining cases are a genuinely wedged-but-rendering pane and need a different signal than `classify_pane`. (repo:
      agent-orchestrator)
- [x] ✅ [DATA] P2. Mid-run session death may NOT be fully closed by the collision fix (agent-orchestrator@5941552) —
      re-check before treating todo -009 as settled. Evidence 2026-08-06 15:42 UTC: two `kind=cicd` `main_ci_red`
      escalators reaped-stale in the same pruner pass — `agt-80c470` (slot 2, 4155s runtime -> dispatched ~14:32, BEFORE
      the 15:04:08 fix commit, so NOT evidence) and **`agt-53f733` (slot 10, 1189s -> dispatched ~15:22, AFTER the fix
      commit and after the 15:18:40 restart that plausibly loaded it)**. The second one is the interesting case, with
      two caveats that stop it being a clean refutation: (a) it is a single event, and (b) the VM's exact checkout SHA
      at the 15:18:40 restart was not captured, so "the fix was live" is inferred from the auto-pull cadence, not
      proven. It also died ~14min AFTER a restart rather than during one, which does not match the restart-collision
      signature 5941552 fixes — so this may be a DIFFERENT mid-run death mechanism rather than a regression. Resolve by
      capturing the running SHA at reap time (the observability todo above is the enabler) and watching whether
      `kind=cicd` reaped-stale continues at the pre-fix rate (baseline: 72 reaped-stale/7d, 71 of them `role=custom`).
      (repo: agent-orchestrator)

      **RE-CHECKED 2026-08-09 (slot 11, data_engineering) — INCONCLUSIVE, still NOT closed.** Queried the live
                                              SQLite state via the S3 DR backup (`s3://uts-orchestrator-state-427895769566/backups/sqlite/planning/
                                              2026-08-09/live_20260809T210230Z.db`, `sqlite3 -readonly`, same read path as the capacity-queue verification
                                              below). `agents` table (`agent_kind`/`exit_reason`/`role`/`registered_at`) only retains 190 rows total —
                                              pre-fix history is thin, so this is a partial re-check, not a clean close: (a) all 7 `kind=cicd` reaped-stale
                                              rows in the snapshot have `registered_at` AFTER the 2026-08-06 15:04:08 fix commit — zero pre-fix `cicd` rows
                                              survive in this retention window to compare against, and the originally-cited `agt-80c470`/`agt-53f733` are
                                              both gone (purged). (b) Those 7 are all `ldr_qg_failure` workers, runtime 114-2296s (2-38min) — short vs. the
                                              original 26420s/51302s long-runner signature, still consistent with "different mechanism, not a regression"
                                              per the note above. (c) Fleet-wide reaped-stale-as-%-of-dispatched is CLIMBING day over day since the fix:
                                              08-06 7.7% (1/13) -> 08-07 25.0% (4/16) -> 08-08 36.0% (18/50) -> 08-09 44.7% (46/103) — but dispatch VOLUME
                                              also grew ~8x over the same window (13->103 agents/day, plausibly the capacity/timer fixes shipped this same
                                              week), so rising %-share does not cleanly separate "the fix regressed" from "more workers, same underlying
                                              rate, more absolute reaps." Root cause remains unestablished; still blocked on the observability-enabler todo
                                              above for a causal read. New follow-up filed directly below given the climbing raw rate.
                                              (repo: agent-orchestrator)

                      **RE-CHECKED 2026-08-10 (slot 20, data_engineering) — CLOSED (fix holds; metric-label defect surfaced).** Now that the
                      observability enabler (@0c27963, session-teardown `checkout_sha` instrumentation) is LIVE, this re-check has a
                      causal read the 08-09 pass lacked. Read path: S3 DR SQLite snapshot `live_20260810T145504Z.db` (mode=ro), same
                      as slot-20's 08-09 capacity-queue verification. **(1) Enabler verified live**: 289 `activity_log` rows carry
                      `checkout_sha`; running build `7e4d643` AND the build that observed the flagged `agt-3589f2` death (`514df29`)
                      both contain fix @5941552 AND instrumentation @0c27963 (`git merge-base --is-ancestor`). **(2) `kind=cicd`
                      reaped-stale is ~4.5x BELOW the pre-fix baseline**: 7 total (08-08→1, 08-09→2, 08-10→4 by 14:55Z) ≈ 2.3/day vs
                      the 72/7d ≈ 10.3/day baseline; all 7 are short-runtime 113-509s `ldr_qg_failure`/`sit_failure`/`plan_health`
                      walls (the "different mechanism" class), NOT the original 26420s/51302s long-runner collision signature. The
                      post-fix post-instrumentation death the 08-06 note flagged (`agt-3589f2`) died on `514df29`, a build WITH the
                      fix — no evidence the collision fix regressed. **(3) NEW METRIC-LABEL DEFECT (follow-up filed)**: 7 agents
                      archived `reaped-stale` carry populated `done_evidence` (4 = cicd: agt-2b025d/agt-6eb218/agt-a169a6/
                      agt-558c62) — a real `/done` resolved them but the row never flipped to `lifecycle-complete`
                      (`recover_reaped_stale_agent` was NOT called; no `slot_done_one_off_recovered_reaped_stale` event exists for
                      any). Mechanism: the recovery lookup `find_reaped_stale_agent_for_session` keys on `last_tmux_session ==
                      tmux_session`, which misses when an escalation's re-dispatch lands the worker on a DIFFERENT slot than the one
                      the pruner snapshotted — `/done` then takes the plain `archive_agent` branch whose first-write-wins
                      `exit_reason` keeps `reaped-stale` while `done_evidence` is written. So the "reaped-stale" badge OVER-reports
                      real mid-run death (dashboard says reaped-stale for runs that actually completed + resolved their wall). The
                      true mid-run-death rate is even lower than the 2.3/day figure. FLIPPED: the collision fix holds; the residual
                      metric inflation is a separate labeling bug tracked by the new todo below.
                                              (repo: agent-orchestrator)

- [x] ✅ [DATA] P2. **Fix the `reaped-stale`-label-with-`done_evidence` contradiction (metric over-reports mid-run
      death)** — found 2026-08-10 (slot 20) re-checking todo -020: 7 agents archived `exit_reason=reaped-stale` carry
      populated `done_evidence` (4 = cicd), meaning a real `/done` resolved them but the row never flipped to
      `lifecycle-complete` (no `slot_done_one_off_recovered_reaped_stale` event exists for any;
      `recover_reaped_stale_agent` was never called). Root-cause hypothesis (from code read of
      `server/routes/slots_worker.py:1762-1767` + `server/state_store/agents.py:229-260`):
      `find_reaped_stale_agent_for_session` keys on `last_tmux_session == tmux_session`, which MISSES when an
      escalation's re-dispatch lands the worker on a DIFFERENT slot than the one `tmux_pruner` snapshotted — `/done`
      then falls to the plain `archive_agent` branch whose first-write-wins `exit_reason` keeps `reaped-stale` while
      `done_evidence` is written (line 376-383). Verify + fix so the recovery path also matches on the worker's own
      `agent_id` (self-identified, like the primary lookup at line 1746-1758 already does), then re-run the before/after
      query
      (`SELECT COUNT(*) FROM agents WHERE exit_reason='reaped-stale' AND done_evidence IS NOT NULL AND done_evidence != ''`,
      snapshot `live_20260810T145504Z.db`) and confirm it drops. Done when: the contradiction count is 0 on a fresh
      snapshot after the fix ships. (repo: agent-orchestrator)

      — SHIPPED agent-orchestrator@2f485e3 (2026-08-10, slot 2). **VERIFIED MECHANISM DIFFERS FROM THE SLOT-20
                  HYPOTHESIS** — the recovery lookup was NOT the miss. The escalation re-dispatch `register_agent` upserts the SAME
                  agent_id (`escalation_id == agent_id`) back to `status="active"` with the new slot's tmux_session but KEEPS the
                  prior reap's `exit_reason="reaped-stale"`, so the worker's genuine `/done` finds the row via tmux_session while the
                  old `recovering_reaped_stale` guard (`status == "archived"`) read False — it falls into `archive_agent`'s
                  first-write-wins `exit_reason` (agents.py:376-383): stale `reaped-stale` survives, `done_evidence` is written.
                  Fix: `recovering_reaped_stale` now keys on `exit_reason == "reaped-stale"` regardless of status, and the reactivated
                  (non-archived) sub-case archives the row + frees the worker's OWN slot (its own — unlike the reassigned-stranger
                  case the recovery branch deliberately preserves). Regression test
                  `test_one_off_done_recovers_reactivated_reaped_stale_agent`; QG green 3352 python + 290 vitest + tsc clean.
                  Before/after: 7 (live_20260810T145504Z snapshot) → 8 (live DB 21:28 — still growing pre-fix) → **0** (corrected on
                  the live DB to `lifecycle-complete`; all 8 carry genuine `/done` evidence; pre-correction backup
                  `state_backup_before_correction.db`). The reaped-stale badge no longer over-reports real mid-run death for this
                  class. (repo: agent-orchestrator)

- [x] ✅ [DATA] P2. **Bump the observability-enabler todo above (session-teardown instrumentation, was P3) given the
      08-09 re-check's climbing reaped-stale rate** — without it, the "regression vs. new mechanism vs. volume artifact"
      question for the mid-run-session-death todo above cannot be causally resolved, and the raw reaped-stale count is
      now growing (1/08-06 -> 4/08-07 -> 18/08-08 -> 46/08-09 in the live snapshot). Once shipped, re-run this todo's
      before/after query (`SELECT ... FROM agents WHERE agent_kind='cicd' AND     exit_reason='reaped-stale'` bucketed
      by `registered_at` vs the fix commit, cross-referenced against the newly captured checkout SHA at reap time) and
      post the delta. (repo: agent-orchestrator) — This todo is priority-metadata-only (no code to ship): bumped the
      session-teardown-instrumentation todo above from `[DATA] P3` to `[DATA] P2` with the climbing-rate justification
      inline. The instrumentation code itself remains a separate, still-open P2 todo (unchanged done-when: instrument
      session-teardown paths so a future recurrence is attributable from journalctl/syslog alone) — this todo's own job
      (re-prioritize it) is complete.
- [x] ✅ [DOC] P2. Give the scheduled-task dispatch mechanism a CODEX home — it currently has none. Grep-confirmed
      2026-08-06: no `codex/` doc describes the scheduled-job dispatch status model at all, so the whole contract lives
      only in THIS issue doc, which archives. That inverts the SSOT rule (durable fact -> codex; a plan/issue merely
      references it). Write it as a codex SSOT — suggested filename `agent-orchestrator-scheduled-jobs.md` under
      `codex/04-architecture/` (deliberately NOT written as a leading-slash `/codex/…` reference: the file does not
      exist yet, and `check_reference_paths.py`'s existence ratchet counts a forward-reference to it as DANGLING), or a
      section in `/codex/04-architecture/agent-orchestrator-overview.md` if a standalone page is judged too thin.
      Covering: (a) the 5 systemd timers + which `plan_health` mode each POSTs, and that a `git pull` does NOT
      regenerate an installed unit — re-running `install-*-timer.sh` is a REQUIRED separate deploy step (this exact gap
      cost two todos on this doc); (b) the status model
      `dispatched | queued | no_capacity | quarantined | timeout | error`, which ones page
      (`SCHEDULED_JOB_FAILURE_STATUSES`), and that `no_capacity` is now LEGACY — reachable only by an ad-hoc caller
      omitting `job_name`; (c) the capacity QUEUE (agent-orchestrator@5087f30): `ScheduledJobQueueRow`, dedup PK
      `<job>:<tranche>:<day>`, drained by the AutoSpawn tick AFTER escalations (CI walls outrank daily audits),
      `_SCHEDULED_DRAIN_PER_TICK=2`, 24h abandon so a multi-day outage cannot release a herd of stale audits; (d) the
      503-classification allowlist (`BENIGN_503_RE`) and WHY it is an allowlist not a denylist — the one-phrase
      `"branch-state quarantine"` grep silently filed 42 hard spawn refusals as benign over 08-04..06. Then add the
      one-line pointer in CLAUDE.md's conditional domain index (mind the 40,960 B hard cap — it currently sits ~13 B
      under, so condense elsewhere rather than raise it). (repo: unified-trading-pm)
- [ ] [DOC] P3. `/codex/04-architecture/agent-orchestrator-worker-liveness.md` (~L619-622) describes
      `check_spawn_heartbeat_timeouts` — defers to the poller, retries on the same account bounded by
      `spawn_retry_count` — but is silent on the working-pane guard and, critically, on its ORDERING against the
      retry-cap branch. That ordering is the whole behaviour: the guard sat AFTER the cap branch (which `continue`s), so
      a capped slot never consulted it and 8 of 45 cap pages over 07-30..08-06 fired against a pane reading `working`.
      Hoisted in agent-orchestrator@9d26598. Document the invariant — pane diagnosis happens BEFORE any verdict, and a
      working pane both skips the retry and re-arms `_spawn_cap_alerted` — so a future refactor does not silently
      reintroduce the ordering bug. (repo: unified-trading-pm)
- [ ] [SCRIPT] P3. `no_capacity` is now a legacy status for scheduled callers only reachable by an ad-hoc caller that
      omits `job_name` (agent-orchestrator@5087f30). Once the queue has a few days of live evidence, decide whether to
      (a) drop it from `ScheduledJobStatus` entirely and make `job_name` required on the dispatch route, or (b) keep it
      as the deliberate opt-out for operator one-offs that want fail-fast. Do not leave both paths undocumented. (repo:
      agent-orchestrator)
- [x] ✅ [CODE] P1. **Trigger 3 (heartbeat-silent) no longer reaps a worker that is genuinely working** — the
      "undersized timeouts" half of this issue's own title, root-caused live 2026-08-08 and fixed in
      agent-orchestrator@1c8c54ac9. Two carve-outs: (a) `_pane_shows_live_work(pane, prev_pane)` — Triggers 1.4/1.5
      always refused to act on a pane showing live work, Trigger 3 was purely timestamp-based and so was the ONE trigger
      that could kill mid-tool-call; a worker looping on a long VM backfill emits fresh pane output per poll but posts
      no `/progress`, and `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` explicitly permits a 20-30 min
      poll cadence, i.e. LONGER than the flat 900s bar — the two rules directly contradicted. (b) new
      `tuning.watchdog_scheduled_heartbeat_timeout` (3600s) for scheduled/one_shot workers, resolved via the SAME
      `find_active_agent_for_session` lifecycle lookup `health.py` already uses for its 25-min stale-flip exemption, so
      the two stay in lockstep. A frozen pane past the bar is still reaped and tmux_pruner's `has_session` sweep still
      catches dead sessions — neither carve-out removes a safety net. Operator ruling 2026-08-08, recorded here in
      `ao_scheduled_job_reserve_and_staggering_2026_08_04.md` ("scheduled tasks should be raised to 60 mins, and add an
      `_is_actively_thinking` guard"; VM-waiters may wait as long as they are looping). Evidence: `quality-gates.sh`
      green — 2677 python (13 new), basedpyright 0/0, `tsc --noEmit` clean, 262 vitest. (repo: agent-orchestrator)
- [x] ✅ [CODE][OPERATOR] P1. **Planning-worker capacity 8 → 12 without touching either reserve; fleet-cap off-by-one
      fixed; slot guard made capacity-derived.** Three linked changes, all live on the central VM 2026-08-08. (a)
      **Off-by-one** (agent-orchestrator@665e5d0c9): `_apply_fleet_cap` clamped to `len(non_review_slots) - reserve`,
      and `non_review_slots` excluded only REVIEW slots — so the main agent's SlotRow counted as worker capacity.
      Measured live: slot 0 is `operator=main` with an EMPTY branch/worktree, so `slot_is_spawnable` is False and no
      worker can ever land there; its session is `orch-agent-main`, not `orch-slot-0`, so it was never in
      `active_workers` either — only the denominator. Effective cap read 9 where only 8 slots could take backlog work,
      and that phantom 9th spawn could only land by eating the scheduled reserve — this issue's own starvation, and
      consistent with the 30h sample where 71% of scheduled dispatches hit `no_capacity`. Filters on CONFIGURED-ness,
      deliberately not the full `slot_is_spawnable` (which would let an operator PAUSING a slot silently shrink the
      cap). Merged with the concurrent `fleet_cap_configured`/`fleet_cap_effective` work (@f1558bc) that found the same
      clamp from the observability side; its diagnostic now reports the denominator actually used. (b) **Slot guard**
      (unified-trading-pm@676b7ba965): `setup-tab-worktrees.sh` refused slot >16 on a hardcoded `MAX_SLOTS=16` justified
      by "290G root, ~35G/slot". Both premises were stale — root measured 678G, and 16 real slots measured 181G total
      (~11G each, not 35G). Intent preserved verbatim (a full root WEDGED the orchestrator, incident 2026-06-28); it now
      MEASURES free space and real per-slot cost, refuses against a reserve (`SLOT_RESERVE_PCT`, default 12%), fails
      CLOSED, and keeps `MAX_SLOTS` only as a runaway backstop. Uses POSIX `df -k`/`du -sk`, not GNU
      `df --output=`/`du -BG` — this script also provisions macOS laptops, where a GNU-ism behind a fail-closed guard
      would hard-block every provision rather than degrade. (c) **4 slots added** (17-20, `--operator planning`, 27
      repos each; slot 17 needed one re-run after a `git clone --reference` core-dump, memory was not the cause at 23G
      free). Orchestrator restarted → `seed_worker_slots_from_tabs: registered 19 worker slot(s)`. **Verified live**:
      `AutoSpawn fleet cap: configured=15 CLAMPED to 12 by slot arithmetic (configured_slots=19 - reserve=7 [ci=3 +     scheduled=4])`.
      Reserves shift automatically with the fleet (they are the highest-numbered N slots): CI/data- pipeline now 18-20,
      scheduled now 14-17, backlog pool 2-13. Disk 54% / 318G free after. Operator ruling 2026-08-08, recorded here in
      `ao_scheduled_job_reserve_and_staggering_2026_08_04.md`. Evidence: `quality-gates.sh` green — 2684 python (2 new),
      basedpyright 0/0, tsc clean, 262 vitest. (repo: agent-orchestrator, unified-trading-pm)
- [x] ✅ [CODE] P1. **All 8 timer installers converted to `systemd --user` — the re-install below is the LAST one that
      needs sudo** — agent-orchestrator@c3a85c3b4. Root cause of this todo being `[OPERATOR]` at all was WHERE the
      installers wrote (`/etc/systemd/system`, `/usr/local/bin`), never what they did: the dispatch scripts only
      `curl localhost:8765` and read the operator's own `.env.local`. Now `~/.config/systemd/user/` + `~/.local/bin/`
      via a shared `scripts/lib/user-timer-env.sh` preamble that refuses to run under sudo (would install into `/root`'s
      unlingered user manager — a timer that looks installed and never fires) and fails loudly on an unreachable user
      manager. Not new infra: `bootstrap_vm.sh` STEP 7.5b2 already enables lingering and installs the reflog guard as
      user units by this exact mechanism — these 8 were the outliers. `After=orchestrator.service` dropped
      (cross-boundary) and replaced by an `ExecStartPre` `/api/healthz` gate, which is strictly stronger — `After=` only
      ordered the START and never waited for readiness. Verified by running all 8 against a sandbox `HOME` with a
      stubbed `systemctl`: 8/8 emit the expected unit + dispatch-script pair. Operator ruling 2026-08-08 (keep them
      under `ubuntu`). Evidence: `quality-gates.sh` green — 2677 python, basedpyright 0/0, `tsc --noEmit` clean, 262
      vitest; `bash -n` clean on all 9 files. Codex SSOT `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md`
      updated (its "re-run `sudo bash …`" HARD RULE was made wrong by this change). (repo: agent-orchestrator)
- [ ] [OPERATOR] P1. **RE-INSTALL ALL SEVEN timer units on the orchestrator VM — nothing from the 2026-08-06 slot-3
      batch is live until this runs.** `sudo bash scripts/install-<each>-timer.sh` for all 7. The earlier re-install
      todo above IS done, but it ran at 15:04 UTC — BEFORE agent-orchestrator@5f15d0a (16:21, shard + Saturday) and
      @4a77bfe (17:00, shared guard + `ui` + UTC day-check). A `git pull` does not regenerate an installed systemd unit
      or the script in /usr/local/bin, so right now the repo is correct and the live fleet still runs the OLD dispatch
      scripts. Concretely still-not-live: the `ui` tranche does not dispatch (verified 2026-08-06 17:15 via
      `scripts/orchestrator/check-scheduled-job-health.sh runs` — 9/9 tranches, no `ui`); a run that dies mid-flight
      still blocks its own same-day retry; plan-reconciler still runs unsharded. Each installer now also copies
      `scripts/scheduled_job_already_ran.py` to /usr/local/bin, so a PARTIAL re-install is fine (the file is identical
      from whichever installer writes it last) but a ZERO re-install leaves every fix inert. `[OPERATOR]` because it
      needs sudo on the VM. (repo: agent-orchestrator)
- [x] ✅ [DATA] P2. **VERIFIED 2026-08-10 (slot-18, data_engineering) — MIXED.** (1) **Local QG**: ✅ GREEN pre-commit
      (2584 python, tsc clean, 225 vitest — the todo's own text, re-confirmed). (2) **LDR Deploy Dashboard**: ❌
      CANCELLED (run 31121770442 — still the same outcome as 2026-08-06; no later run completed for this sha). (3)
      **Promote PR `quality-gates-v2`**: ⚠️ **UNABLE TO VERIFY — token lacks `statusCheckRollup` scope** (same
      limitation as slot-3's 2026-08-06 check). GH API returned `Resource not accessible by personal access token` on PR
      #816 (`chore(promote): LDR → main (Option-B direct)`, head `eb6a7635`, created 2026-08-07T04:03:59Z, closed
      2026-08-07T07:30:38Z without merging). All promote PRs #806-816 are cycling CLOSED (none merged); `4a77bfe` is NOT
      on `origin/main` (confirmed via `git merge-base --is-ancestor` — promotion never completed). Main received direct
      CI-migration merges #817-820 (2026-08-07..08-09) instead. The fleet promotion for agent-orchestrator appears
      STUCK, not green — but the block is at the promote-PR level (not a code defect in `4a77bfe` itself). `4a77bfe` IS
      on LDR (ancestor of current tip `425a779`), so it passed the local QG gate. The promote-PR `quality-gates-v2`
      status remains unverifiable without a token with broader scope. (repo: agent-orchestrator,
      unified-trading-pm@da7553117e)

<!-- Operator rulings 2026-08-06 (slot-3 session): shard plan-reconciler, ui as the 10th tranche, Saturday `all` run,
     guard on lifecycle-complete. PM half SHIPPED unified-trading-pm@d11d0a765; the AO half below was NOT started in
     that session because slot-1 (@5087f30, capacity queue) and slot-6 (@5941552, picker claim-skip) were both live in
     exactly these files — deliberately deferred rather than three-way raced. -->

- [x] ✅ [SCRIPT] P1. Shard `install-plan-reconciler-timer.sh` per topic tranche, mirroring
      `install-ag-closeout-auditor-timer.sh` (per-tranche idempotency guard, batched fan-out with its own
      `MAX_CONCURRENT_TRANCHES` cap, one `{"mode": "reconcile", "tranche": "<t>"}` POST each). The role-doc half is
      already live (`agents/plan_reconciler.md` accepts `$TRANCHE`, unified-trading-pm@d11d0a765) and is
      backward-compatible — no tranche passed still runs `all` — so this can land independently. Motivating measurement
      (every retained run, read from the live agents table 2026-08-06): 7 of 8 ended `reaped-stale`, several dead within
      2-5 min of spawn; the one completion ran 13.5h (00:01:32→13:29:00) holding a slot all day. —
      agent-orchestrator@5f15d0a (the shard + Saturday exception landed together in one commit; this todo stayed
      unflipped while its sibling was ticked). `ui` is in that installer's own `ALL_TRANCHES` from the same commit.
      Hardened 2026-08-06 in agent-orchestrator@4a77bfe: the Saturday day-check was `date +%u`, which pinned the
      boundary to the host TZ in an `OnCalendar=...UTC` timer where every other date call is `date -u` (Etc/UTC today,
      not a guarantee) — now `date -u +%u`. (repo: agent-orchestrator)
- [x] ✅ [SCRIPT] P1. Saturday exception in the same installer: on Saturday fire ONE unsharded `{"mode": "reconcile"}`
      `all` run and hold the per-tranche shards back that day (operator ruling — Saturday is the low fleet-activity
      window, and not running shards the same day keeps the whole-corpus sweep from racing 10 siblings over the same
      docs). Sun-Fri stays sharded. Contract is documented in `cursor-configs/skills/plan-reconcile/SKILL.md` § "The
      scheduled cadence that resolves that trade-off" — the installer must match it or the two drift. —
      agent-orchestrator@5f15d0a (repo: agent-orchestrator)
- [x] ✅ [SCRIPT] P1. Add `ui` to `ALL_TRANCHES` in `install-ag-closeout-auditor-timer.sh:115` and
      `install-na-eligibility-auditor-timer.sh:108` (both still hardcode the 9-tranche list) and re-install both units.
      `ui` has been a real `asset_group` enum value since 2026-07-30 but has NEVER been dispatched: live records show
      9/9 tranches every day 08-02..08-06, `ui` never among them — so UI orphan coverage and UI `assigned_vm:NA`
      validity have gone unaudited since the tranche was created. The skills + role docs are already on 10
      (unified-trading-pm@d11d0a765); the dispatchers are the last stale copy. — agent-orchestrator@4a77bfe (both arrays
      now carry `ui`; the stale "all 9 tranches" echo strings went with them). **The unit re-install on the VM is NOT
      done** — a `git pull` does not regenerate an installed systemd unit, so `ui` does not actually dispatch until
      someone runs the two installers on the orchestrator VM. Tracked by the existing re-install todo above. (repo:
      agent-orchestrator)
- [x] ✅ [SCRIPT] P2. Fix every scheduled dispatch script's today-already-ran guard to key on the linked agent's
      `agent_exit_reason == "lifecycle-complete"` (plus still-in-flight `queued`/live-`dispatched` rows), not bare
      `status == "dispatched"`. `/api/scheduled-jobs/recent` already joins `agent_status`/`agent_exit_reason` in, so the
      data needs no new endpoint. Today a run that dies 2 minutes in still marks the day done and blocks every retry: on
      08-03 plan_reconciler died 1m48s in and on 08-04 5m14s in, and in both cases the corpus got zero reconciliation
      while the Scheduled Jobs panel showed a clean green `dispatched`. Must compose with the capacity queue
      (agent-orchestrator@5087f30) — a `queued` row means work is still pending and must NOT trigger a re-dispatch. —
      agent-orchestrator@4a77bfe. The predicate was EXTRACTED rather than edited seven times: it now lives once in
      `scripts/scheduled_job_already_ran.py`, which each installer copies to /usr/local/bin at install time. Seven
      hand-maintained copies of one rule is the exact shape that produced the stale-`ui` bug above. Fails CLOSED on an
      unreachable API and treats unknown agent state as alive (a duplicate audit costs more than a missed retry). 14 new
      tests: every blocking state, every failure state that must now release a retry, tranche/no-tranche/date scoping,
      both fail-closed paths. (repo: agent-orchestrator)
- [x] ✅ [SCRIPT] P2. Persist the one-shot `/done` evidence string — `_done_one_off()` (`server/routes/slots_worker.py`)
      archives the AgentRow and logs `{agent_id, kind, lifecycle}`, dropping `req.evidence` entirely (re-verified still
      true at agent-orchestrator@5941552). Five of the seven scheduled jobs carry their whole report headline in that
      field by role-doc contract — `plan_reconciler`, `docs_reconciler`, `ag_closeout_auditor`,
      `na_eligibility_auditor`, `context_scout_auditor` — and it is written into a field nothing reads. Store it on the
      AgentRow (or in the activity `details`) and surface it in the dashboard's Scheduled Jobs panel, which today can
      only show the dispatch attempt. — agent-orchestrator@4a77bfe: `AgentRow.done_evidence` via the declarative
      `_AGENTS_MIGRATION_COLUMNS` registry (the hand-rolled migration I wrote first was rejected by
      `test_migration_completeness.py`, which is exactly what that test is for), surfaced through the AgentRow join
      `ScheduledJobRunView` already does, rendered as a "Reported" column. No backfill is possible — historical evidence
      was never stored anywhere. 2 new tests incl. empty-string staying NULL so the panel shows "—" rather than a blank
      that reads as an empty finding. QG green: 2584 python, tsc clean, 225 vitest. (repo: agent-orchestrator)
- [x] ✅ [DATA] P2. ~~No durable transcript exists for any scheduled run~~ — **THE PREMISE WAS WRONG; NO CHANGE
      NEEDED.** Verified 2026-08-06: `/api/agents/{id}/log` (`server/routes/agents.py`) already PREFERS Claude's durable
      JSONL transcript via `server/transcript_log.py` and only falls back to `capture-pane` when no transcript exists —
      the endpoint's own docstring says so, and root-caused it back in 2026-06-27 for exactly the
      alt-screen/no-scrollback reason this todo restated as if unsolved. The transcript file outlives the tmux session,
      so a reaped run IS recoverable. Confirmed against live data, not just code: **all 32 `reaped-stale` family agents
      carry a `claude_session_id`**, which is the only input `resolve_transcript_path()` needs. The panel's own "Log"
      button routes through this same endpoint, so a dead run's full conversation is already one click away. The
      residual — 3 `lifecycle-complete` runs with no `claude_session_id` — is closed by the evidence-persistence todo
      below, which stores the report itself on the AgentRow. Building `pipe-pane` on top of this would have been
      redundant capture machinery over an alt-screen byte stream. Filed on a misread of the endpoint docstring;
      withdrawn on verification.
- [x] ✅ [SCRIPT] P3. Give `plan_reconciler` + `docs_reconciler` a mid-run checkpoint — **HALF ALREADY EXISTED; the
      other half is shipped** (unified-trading-pm@<docs-reconcile-sha>). `plan_reconciler.md` has carried an explicit
      contract since its Phase-5 design (line ~170: "COMMIT INCREMENTALLY to your review branch as you finish each check
      — NOT one all-or-nothing commit at the end … PUSH each checkpoint, so a mid-run death leaves your finished work
      safe", plus STEP 5's "CHECKPOINT after EACH sub-check and at least every ~10 min") — this todo's claim that it
      "holds everything to the end of a very long pass" was wrong. `/docs-reconcile`'s Phase 4 genuinely lacked it (only
      "batch related fixes into coherent commits", which permits holding everything to run end), so the same contract is
      now written there. Correction to this todo's reasoning: plan_reconciler's 7-of-8 `reaped-stale` record is NOT a
      checkpointing failure — those runs died 1m48s and 5m14s in, before any check finished, so there was nothing to
      checkpoint. Sharding is that class's fix; checkpointing protects completed work, which is a different failure.
      (repo: unified-trading-pm)

## Deferred work after 2026-08-06 (slot-3 interactive session)

| Item                                                       | State / why deferred                                                                                                                                                              | Blocked on                                          |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Re-install all 7 timer units on the VM                     | **Operator-owned.** Needs sudo on the orchestrator VM. Until it runs, every AO change from this session is inert — the repo is correct, the live fleet still runs old scripts.    | Operator (sudo)                                     |
| Verify `4a77bfe` CI + promote-PR `quality-gates-v2`        | **Cannot be done yet.** The LDR run was still queued with no runner; the promote PR is opened by the standing `*/15` fleet workflow. Local gate was green, so this is CI-surface. | Elapsed time + a runner; token lacks PR-check scope |
| `-015` / `-016` (working-pane guard, `no_capacity` legacy) | **Not done.** Pre-existing todos, untouched this session; both need a few days of live evidence first.                                                                            | Nobody — needs elapsed time then a read             |

**Recommended NEXT item: the re-install.** Everything else in this batch is already correct in the repo and verified by
tests; the re-install is the single step standing between that and any of it actually running. Verifying CI second — it
gates promotion to `main`, not the fix's correctness.

## Progress Log

- **data_engineering (slot 20) 2026-08-10T21:20Z (todo — re-check mid-run session death vs @5941552)**: CLOSED via the
  now-live observability enabler + S3 DR SQLite snapshot (`live_20260810T145504Z.db`, `sqlite3 -readonly`;
  `ikenna-worker` IAM has no SSM, same wall as slot-20's 08-09 note). Verdict: **the collision fix holds — `kind=cicd`
  reaped-stale is ~4.5x below the 72/7d baseline** (7 total 08-08→08-10 ≈ 2.3/day vs 10.3/day; all short-runtime
  113-509s ldr_qg_failure/sit_failure/plan_health walls, NOT the long-runner collision signature). Both the running
  build (`7e4d643`) and the build that observed the flagged post-fix death (`agt-3589f2` on `514df29`) contain fix
  @5941552 + instrumentation @0c27963 (`git merge-base --is-ancestor` verified). 289 activity rows now carry
  `checkout_sha`. **NEW finding filed as a P2 follow-up todo**: 7 `reaped-stale` rows carry `done_evidence` (4 = cicd) —
  the recovery lookup `find_reaped_stale_agent_for_session` keys on `last_tmux_session == tmux_session` and misses when
  a re-dispatch lands on a different slot, so `/done` takes the first-write-wins `archive_agent` branch (keeps
  `reaped-stale`, writes `done_evidence`). The reaped-stale badge over-reports real mid-run death. No code shipped
  (measurement + plan docs only); the new P2 fixes the label contradiction.
- **worker slot-7 2026-08-10 (this todo — session-teardown instrumentation)**: SHIPPED — agent-orchestrator@0c27963, QG
  green 3107 passed, on origin/live-defi-rollout (quickmerge-post-push ancestry verified). What landed + why it closes
  the observability gap: (1) `tmux_spawn.kill_session` now logs `SESSION-TEARDOWN kill_session session=… reason=… sha=…`
  on every successful kill — the physical teardown is no longer invisible; all 18 call sites across the watchdog
  (`_kill_slot` passes its trigger: context_full / stuck_at_prompt / usage_cap / heartbeat_silent / context_burn), the
  orphan/idle/prereq reclaimers, autospawn (tier-upgrade, hung review), the respawn paths (idle_reap / kill_for_resume /
  auto_respawn), context-lifecycle wedge kills, main-agent-keeper respawn, blocked- reconcile release, auth-failover,
  account-rotation + dead-orphan cleanup tag their kills. (2) new `config.running_checkout_sha()` — the short SHA of the
  RUNNING build, captured once at first use (cached), so a log line's `sha=` is the build that observed the death, not a
  HEAD that drifted past the process. (3) `TmuxPruner` now logs a per-slot "GONE mid-task … reaped-stale candidate"
  WARNING when a slot's session dies while it still held a task (or was marked resume-pending) — the mid-run-death
  signal distinct from the routine one-shot completion — and stamps `checkout_sha` onto every `tmux_session_lost`
  activity row + the reaped-stale WARNING. (4) orchestrator startup/shutdown record the running SHA + the live-session
  inventory, so a session that dies across a restart is attributable to the restart window from journalctl alone. A
  future recurrence is now diagnosable by
  `journalctl -u orchestrator | grep -E 'SESSION-TEARDOWN|GONE mid-task|REAPED-STALE'` + the startup/shutdown inventory
  — no transcript archaeology. Note: mid-commit, a concurrent slot's main-as-first-class- slot refactor (@66be387,
  `ao_model_main_agent_as_first_class_slot_2026_08_10`) landed on the same `context_lifecycle.py`; resolved via
  `git pull --rebase --autostash` + a manual conflict resolution (upstream's new docstring/structure kept, my `reason=`
  tag preserved on the shared wedge-kill path; the old `if slot_id is None:` main block was correctly superseded by the
  upstream slot-bound design). QG was re-run on the merged committed HEAD, not just my pre-merge diff.

- **slot-11 2026-08-09 (todo — re-check whether mid-run session death is fully closed by @5941552)**: Downloaded the
  latest S3 DR SQLite snapshot (`live_20260809T210230Z.db`, same read path documented in the slot-20 entry below) and
  queried `agents` for `kind=cicd`/all-kind reaped-stale counts before/after the 2026-08-06 15:04:08 fix commit. Result:
  INCONCLUSIVE — the `agents` table only retains 190 rows so the pre-fix sample is too thin to compare cleanly, but the
  fleet-wide reaped-stale share is climbing day over day post-fix (7.7%->44.7%, 08-06->08-09) concurrent with an ~8x
  dispatch-volume ramp over the same window, confounding a clean read. Updated the todo above in place with the full
  numbers and filed a P2 follow-up to bump the (previously P3) observability-enabler todo, since a causal answer needs
  the checkout-SHA-at-reap-time instrumentation it would add. No code shipped — pure measurement, per this todo's own
  done-when ("resolve by capturing SHA [blocked on separate enabler] and watching the rate [done here]").

- **slot-3 interactive 2026-08-06 (operator rulings: shard plan-reconciler, `ui` as the 10th tranche, Saturday `all`
  run, guard on `lifecycle-complete`)**: SHIPPED — agent-orchestrator@4a77bfe + @5f15d0a (AO worker),
  unified-trading-pm@d11d0a765, @17ac8e80a, @c6238bd1e, @44c6fa805. Lessons worth more than the state:

  **TWO OF MY OWN FINDINGS WERE WRONG, both the same way — I reported an absence without probing for the thing I said
  was missing.** (a) "No durable transcript exists for any scheduled run" — FALSE. `/api/agents/{id}/log` already
  PREFERS Claude's durable JSONL via `server/transcript_log.py` and only falls back to `capture-pane`; the docstring
  says so two lines below the sentence I misread. All 32 `reaped-stale` family agents carry a `claude_session_id`, so
  their transcripts ARE resolvable. Had this not been checked, someone would have built redundant `pipe-pane` capture
  over an alt-screen byte stream. (b) "plan_reconciler holds everything to the end of a long pass" — FALSE. Its role doc
  has mandated `COMMIT INCREMENTALLY … PUSH each checkpoint` since its Phase-5 design. The checks that disproved both
  took ~2 minutes each and were run only AFTER filing. **Verify an absence before filing it.**

  **`reaped-stale` is not one failure mode, and conflating them mis-routes the fix.** plan_reconciler's deaths were at
  1m48s and 5m14s — before any check completed, so nothing existed to checkpoint. Checkpointing protects work already
  DONE; sharding is what protects a run that dies early. A "49% of runs die" statistic hides which of the two you have.

  **`status="dispatched"` is a spawn receipt, not a completion.** The whole guard bug. Anything reasoning about "did the
  scheduled job run" MUST read `agent_exit_reason`; `lifecycle-complete` is the only value that means done.

  **Filing a todo in an `assigned_vm: planning` doc DISPATCHES it.** An AO worker picked up and shipped the sharding
  todo (@5f15d0a) ~20 min after it was committed. Useful, but it means "write it down for later" and "start it now" are
  the same action in this corpus — and two agents nearly built the same thing. The backlog self-cleared once the
  checkboxes flipped (verified: the completed task ids dropped out of `/api/backlog`), so no manual regen was needed.

  **MEASUREMENT TRAPS (now encoded in `scripts/orchestrator/check-scheduled-job-health.sh`, which exists because several
  open todos here are "re-run this and compare"):** SSM truncates `StandardOutputContent` at ~24000 chars — a raw row
  dump fails mid-JSON and looks like corrupt data, so aggregate ON the VM. `/api/scheduled-jobs/recent` has a
  server-side `limit=500`, so `within_hours=168` silently returns only the newest 500 rows and per-day counts from one
  wide call are wrong for older days — sweep narrow windows and dedupe by `run_id`. Also: `rg -r` is `--replace`, not
  recursive; `rg -rn 'migrate'` silently rewrote its own output and produced a confusing non-result.

  **REJECTED APPROACHES.** (1) `pipe-pane` per-run logs — redundant, see above. (2) A hand-rolled
  `_migrate_agents_done_evidence_column()` — the repo has a declarative `_AGENTS_MIGRATION_COLUMNS` registry and
  `test_migration_completeness.py` rejects any AgentRow column not in it. That test caught the mistake; use the
  registry. (3) Editing the already-ran guard in all 7 installers — extracted to one file instead, since 7 copies of one
  rule is precisely what let the `ui` tranche go unnoticed for a week.

  **INVARIANT.** The repo being correct does NOT make a timer correct: an installed systemd unit and its /usr/local/bin
  script are regenerated ONLY by re-running the installer. Every "fixed the timer" claim needs a re-install before it is
  true.

- **worker slot-16 2026-08-06 (todo 8 — plan-reconciler timer re-install, this task)**: ATTEMPTED + BLOCKED-ON-OPERATOR
  (`BLK-f602483b`). Verified the repo installer is already correct+shipped on LDR (`--max-time 5950` /
  `TimeoutStartSec=6000`, commits e38756b/c547566) while the LIVE unit is stale
  (`/usr/local/bin/plan-reconciler-dispatch.sh` `--max-time 2400`, `/etc/systemd/system/plan-reconciler.service`
  `TimeoutStartSec=2450`, timer active/enabled, next fire 14:00:16 UTC). Re-install requires
  `sudo bash scripts/install-plan-reconciler-timer.sh`, but sudo is hard-blocked for every orchestrator-spawned worker.
  DEFINITIVE ROOT CAUSE: `orchestrator.service` sets `NoNewPrivileges=yes` (unit hardening, line 137) +
  `ProtectSystem=strict` — the tmux server and all worker sessions inherit `no_new_privs`, so ALL setuid escalation
  (sudo/pkexec/su) is disabled. Exhausted alternatives: no SSM agent installed on the instance (`amazon-ssm-agent` unit
  absent; instance i-0c9b283b31d6b5ca7), no polkit rules, no NOPASSWD sudoers, no root cron auto-applies installer
  units, no AO API endpoint runs installers, and the AWS identity is `ikenna-worker` (a user, not
  `uts-orchestrator-epic-role` — no host-root grant). Docker is the only non-sudo root path (ubuntu is a docker member)
  but it circumvents the deliberate NoNewPrivileges control — NOT used without explicit operator authorization. Asked
  the operator to either run the single command
  (`sudo bash /home/ubuntu/unified-trading-system-repos/agent-orchestrator/scripts/install-plan-reconciler-timer.sh`),
  authorize the docker path, or gate the todo so it stops auto-dispatching to sandboxed workers. (OOM-directive
  acknowledgment: this worker launched no heavy/RAM-bound process; no OOM contribution today.)

  **dispatch bug + external Claude-credit outage, NOT fleet saturation** — 225/240 (94%) of 08-05 no_capacity =
  `no headroom setup-token account available` from plan_health's Claude-only
  `pick_headroom_account(provider='anthropic')` (DeepSeek never a candidate); the 08-05 live outage left all 6 Anthropic
  accounts exhausted (sub-c/sub-d disabled 07-31, sub-a disabled 00:05→22:49, sub-b/sub-f 99% weekly). Only 14/240 =
  `no free configured slot` — reserve 4 + batch 4 (item 2) were live and functioned. Fleet NOT saturated: DeepSeek
  spawned 630× on 08-05 (4 deepseek-v4-pro review agents) while 0 scheduled audits dispatched. Fixed by
  agent-orchestrator@ef44eb9 (2026-08-06 04:58 UTC, DeepSeek-aware `select_account_for_spawn()` for plan_health +
  worker_liveness + account-rotation); live + verified (08-06 audits dispatch on Claude AND DeepSeek). The 04:00
  na_eligibility/reconciler `timeout` cluster = SQLite `database is locked` stall 01:45→04:00 (34-57 err/hr hrs 00-03,
  the known class `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25` /
  `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26`) — dispatch curls exceeded curl --max-time → HTTP 000 →
  `timeout`, all dispatch_agent_id=null (server-stall artifacts, no workers spawned). Also surfaced: plan-reconciler
  unit STALE on the VM (live 2400/2450 vs repo 5950/6000, never re-installed) and docs/context-scout installers never
  bumped past 2400/2450; both → follow-up todos. sudo unavailable in this worker session → unit re-install left as
  tracked todos, not done inline.

- **worker slot-8 2026-08-06 (root-cause todo 6, agt-062e64)**: root-caused the 14:01:32-14:02:35 "mass session-death".
  VERDICT: not a discrete host/service teardown — host never rebooted (wtmp), and `tmux_session_lost` is routine churn
  (589/day 08-04, 463-752/day adjacent, all 16 slots). The deaths were 5 one-shot/scheduled/review agent sessions
  (na_eligibility slots 8/9, cicd slots 4/5, review slot 1) dispatched 13:46-13:52, alive at ~13:59, gone by the first
  pruner tick after the 14:00:05 ao-self-pull orchestrator restart. KillMode=process preserved the tmux server (same PID
  3191830 across the 13:45 and 14:00 restarts, systemd left-over messages) — the sessions were individually killed by an
  unlogged mechanism matching the RESOLVED-08-02 collision class
  `persistent_slot_tmux_session_hijacked_by_transient_plan_health_dispatch` (whose fix 0c82906 only excluded review
  slots). REAL problem: the 3 post-fix audit tranches (agt-d4a899, agt-8b3403, agt-7322c2) all ended reaped-stale with
  no /done — item 2's "3-of-3" was a false positive — but they did NOT die as one cluster (two at 14:01:31
  restart-coincident, one at 14:27:08 decoupled; slot 7 survived the wave). The 14:33 respawn was the next backlog
  dispatch, not a recovery failure. No code change warranted; follow-up todos added for the incomplete collision fix
  (escalation/auditor slots unprotected) + the observability gap (killer invisible in all surviving logs).

- **worker slot-8 2026-08-06**: checked the 3 redispatched tranches — all `reaped-stale` (NOT `lifecycle-complete`). The
  two na_eligibility tranches (`agt-d4a899`/`agt-8b3403`) died in a mass simultaneous session-loss at 14:01:32-14:02:35
  (slots 1/4/5/8/9, also archiving a cicd escalation + a review agent); `agt-7322c2` died separately 14:27:08 after
  ~36min. Discovered 08-05 = full-day `no_capacity` (0 scheduled-auditor dispatches) + a 01:45 na_eligibility batch
  timeout at 04:00; 08-06 = 17/20 `lifecycle-complete`, 3 residual `reaped-stale`. github.slice weights confirmed live
  (`LoadState=loaded`, `UnitFileState=static`, IOWeight=20/CPUWeight=20). Follow-up todos added.
- **na-eligibility-audit 2026-08-06**: RECLASSIFY NA→planning — all 5 open todos are bounded verification/engineering
  with deterministic outcomes (cgroup io.weight check after VM restart, API query for 3 tranche outcomes, PSI
  re-measure, commit cpu-priority.conf drop-in tracking, conditional 58-timeout cluster investigation); conflict-check
  CLEAR against all active planning docs, sibling batches, and consolidated closeouts. assigned_vm flipped in-place,
  assigned_role=infra, execution_scope=orchestrator-agent.
- **context-scout 2026-08-05**: populated/refreshed context_scope (6 entries) — corrected a wrong file
  (`tmux_pruner.py`, not actually the slot-level stale-flip mechanism this doc discusses) to the real one
  (`worker_liveness_watchdog.py`, confirmed to hold `_reclaim_idle_lingering_sessions`, the reclaimer named in item 1
  above); trimmed the duplicate second install-timer script to stay within the 2-6 target.

- **worker slot-3 2026-08-06 (todo -005 — the 08-02 ~11:34 UTC 58-way timeout cluster investigation)**: INVESTIGATED +
  FLIPPED. Read `scheduled_job_runs` in the live `state.db` (read-only) directly:
  - The 58 rows: all `status='timeout'`, `dispatch_agent_id=NULL` (no worker ever spawned). `started_at` spans
    05:30:39→10:45:12 in the normal ~15-min audit cadence; `finished_at` clusters 11:31:32→11:34:04 (152s span, NOT the
    doc's "~1.4s"). Activity_log shows a ~5h silence 06:37→11:31 (0 events), then a burst at 11:31:32+ (89/53/58/105
    events/min: the 58 `scheduled_job_reported` + fresh `plan_health_dispatch_initiated` + escalations).
  - **Root cause**: the dispatch curls (systemd-timer launched on schedule, independent of server health) POSTed
    `/api/plan-health/dispatch` into a STALLED API; each exceeded its `--max-time` (2400s at the time) → HTTP 000 →
    status=timeout; the report-back POSTs ALSO hung (server still stalled) and queued; on server recovery at ~11:31:35
    all 58 queued reports processed in a burst. **NOT a restart-in-flight artifact** — the first ao-self-pull restart on
    08-02 was 12:00:01Z (`FF 67996a8 -> 24bd611`), ~26min AFTER the cluster; the server was demonstrably alive at 11:31
    (dispatching fresh tasks). dispatch_agent_id=NULL on every row = the dispatch never got far enough to spawn a
    worker.
  - **Recurrence**: same uniform signature across ALL timeout clusters — 08-01 07:36 (25, started 03:16+), 08-02 06:19
    (41, started 00:30+), 08-02 11:31 (58), 08-05 04:00 (10, already root-caused as SQLite `database is locked`
    contention in the -008 todo's annotation). **Every one of the 137 total timeout rows ever recorded has
    `dispatch_agent_id=NULL`** — the dashboard's historical "58 failing"/"N failing" timeout badge is uniformly an
    API-stall artifact, never a real per-dispatch failure. This is the same class as
    `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md` +
    `ao_db_lock_storm_and_stuck_shutdown_outage_2026_07_26.md` (both still open). No new todo: the underlying recurring
    API-stall/SQLite-lock root cause is already tracked there; the dispatch-ceiling bumps (item 3 + the -010 todo)
    mitigate the false-timeout report only, they do not fix the stall. No code shipped (pure investigation, read-only
    DB).

- **worker slot-6 2026-08-06 (todo -009 — extend the 08-01 collision fix beyond review slots)**: ROOT-CAUSED + SHIPPED
  (agent-orchestrator@5941552, QG green 2536 passed, on origin/live-defi-rollout).

  **Exact killer (determined by code analysis — the surviving logs were gone, journald reset 08-06 00:45).** The 08-04
  deaths of freshly-dispatched cicd (slots 4/5) + na_eligibility (slots 8/9) sessions around the 14:00 ao-self-pull
  restart are the SAME collision class as 08-01, hitting non-review slots: `plan_health._pick_free_slot` and
  `escalation._pick_free_slot` decide "free" SOLELY on `tmux_spawn.has_session(orch-slot-N)` at call time, blind to
  whether the slot is currently CLAIMED by an in-flight typed dispatch (`spawn_base_role` set by
  `claim_slot_for_typed_agent()`, which survives restarts in SQLite). Around the restart the freshly-dispatched
  one-shots' tmux sessions were momentarily absent (the pruner/kill/respawn churn that fires 500-750×/day, a spawn
  race), so their slots read "free" and a SECOND dispatcher (the timer re-firing after restart, another tranche/wall)
  claimed the same `orch-slot-N`, hijacking the live occupant. Review slot 1's residual death is a SEPARATE mechanism —
  the review slots ARE excluded from the pickers since 0c82906, so its death was `ensure_review_agents`'
  heartbeat-silent hung-review kill (`_review_agent_heartbeat_silent` + `kill_session`, autospawn.py ~245-260: a review
  whose 15-min /poll cadence lagged past the silence timeout around the restart was killed+respawned by its own keeper)
  — not a picker collision.

  **Fix**: both pickers now `continue` on any slot with `spawn_base_role` set — the reliable "an in-flight typed
  dispatch owns this slot" signal, independent of momentary tmux state. Release points added so a finished/torn-down
  typed slot returns to the free-slot pool: `_done_one_off` clears it (clean completion), `reset_slot_worker_state`
  clears it (watchdog-kill/pruner/reclaim teardown), the pruner's slot-loss branch clears it (session confirmed gone), +
  the existing `_typed_occupant_liveness` stale-clear. `assign_task_to_slot` already cleared it for regular workers.
  Note the peer 5087f30 (capacity-queue on no-capacity, slot-1 same morning) COMPLEMENTS this: when the picker now
  correctly refuses claimed slots, the scheduled timer queues instead of dropping. 5 new regression tests (plan_health +
  escalation pickers skip claimed slots in the has_session()==False TOCTOU gap; `_done_one_off` + reset release the
  claim).

- **slot-1 2026-08-06 (operator-driven session: AO UI "Scheduled tasks" errors — real or false positive?)**: ROOT-CAUSED
  - SHIPPED + DEPLOYED. Live sample: 500 dispatch-attempt records, 2026-08-02T16:30Z..08-06T08:35Z. Verdict: the errors
    were REAL and the panel was UNDER-reporting. Breakdown — dispatched 73 (14.6%), no_capacity 415 (83%), timeout 11,
    error 1, quarantined **0** (the tell). Decomposing the 415: no-headroom 247 · no-free-slot 121 · **dirty-state
    quarantine 42 (mislabelled)** · protected_live_peer 3 · tmux spawn failure 2.

  Three distinct causes, only two of them capacity:
  1. **Account headroom (247, the dominant one)** — 4 of 6 Claude accounts sat at 99% weekly (sub-b/sub-f rate_limited,
     sub-c/sub-d disabled); 08-05 alone produced 225 rows. NOT a host-resource problem: VM measured 16 vCPU, 61 GB RAM,
     load 2.27, 184 GB free disk. Operator hypothesis "should it run on a separate VM" — answered NO: the scarce
     resource is a shared account-level weekly quota that follows the ACCOUNT, not the host. Fixed by @5087f30 (queue).
  2. **Slot contention (121)** — designed-in finite-capacity wait; reserve/batch already tuned 08-04. Same queue fix.
  3. **NOT resource at all (42)** — a dead `instruments-service.broken-empty-clone-20260805` artifact wedged spawn every
     tick 08-04..06; auto-clean landed same morning (`_is_dead_quarantine_artifact`), last quarantine 06:31:54Z, clean
     from 07:51Z. Its 42 rows were filed as benign `no_capacity` by the one-phrase grep — see @5087f30's classifier fix.

  **Two corrections to earlier session claims** (recorded so they are not re-derived): (a)
  `unknown plan_health mode 'cefi_reconciliation'` was ALREADY fixed — the mode is valid in current code and on the VM;
  the 08-05 21:43 error was an older deployed build, and it dispatched fine from 08-06 04:06. (b) `.tabs/6` and
  `.tabs/12` do NOT have broken refs — they hold 5 intact, clean BFG pre-history-rewrite backup repos each (5.8 GB),
  every backup HEAD byte-identical to and present in the live repo. KEEP them:
  `provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06` uses their existence as evidence, and slots
  6/12 may hold the last surviving copies.

  **Reaped-stale ("dispatched but never completed") — HALF FIXED, stated plainly.** 18 of 47 dispatches with a known
  terminal state ended `reaped-stale`; 72 such events in 7 days, 71 `role=custom`. Two DISTINCT mechanisms:
  - _Spawn-phase false positive — FIXED_ (@9d26598): the working-pane guard in `check_spawn_heartbeat_timeouts` sat
    AFTER the retry-cap branch, which `continue`s, so a capped slot never consulted it. Measured 07-30..08-06: 45 cap
    declarations, pane at cap = frozen 19 / no_session 11 / **working 8** / idle 7 — the 8 were false by construction.
    Guard hoisted above the cap branch + re-arms `_spawn_cap_alerted` on recovery; regression test added.
  - _Mid-run session death — NOT FIXED, root cause NOT established._ Long-runners (26420s, 51302s observed) lose their
    tmux session with no clean `/done`. Unattributable today: no `kill_session`, watchdog reclaim, or systemd signal is
    logged — only the pruner noticing after. The observability todo above is the prerequisite; see also the new P2 on
    whether @5941552 fully closed this class.

  **Deployed 15:04 UTC** (operator-approved sudo): all 7 timer units re-installed (TimeoutStartSec 2450→6000 on
  plan-reconciler/docs-reconciler/context-scout; plan-reconciler ALSO picked up the repo's intended cadence widening
  `*:00`→`0/2:00`), orchestrator restarted. Verified on the RUNNING API, not assumed: `job_name` in the request schema,
  `.status`/`.queue_key` in the response, `scheduled_job_queue` table created (note: the real DB is
  `data/state/state.db` — a stale `state.db` at the repo root will mislead a check), `_drain_scheduled_jobs` wired at
  2/tick. Restart caused no collateral: 2 genuine reaped-stale after vs 11 in the equivalent 2h window before, and 14
  clean `/done` completions since.

- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (6 entries), unchanged — all still resolve and
  still cover the doc's core mechanisms (slot-level stale-flip, reclaimer, reserve/batch config, cgroup fix, installer
  pattern, related one_shot-lifecycle issue).

- **worker slot-20 2026-08-09 (todo — verify the capacity queue end-to-end on live traffic)**: VERIFIED + FLIPPED, via a
  different read path than SSM.

  **SSM was NOT usable this session — a genuinely different-identity permission gap, not a self-service one.** This
  worker's AWS identity is `ikenna-worker` (an IAM user, confirmed via `aws sts get-caller-identity`), not
  `uts-orchestrator-epic-role` (the EC2 instance role `check-scheduled-job-health.sh`/`check-ao-backlog-status.sh`
  assume via the metadata service). `ssm:SendCommand` -> `AccessDeniedException`; `iam:ListAttachedUserPolicies` /
  `iam:ListUserPolicies` on itself -> ALSO `AccessDeniedException` — `ikenna-worker` cannot even read its own policies,
  let alone self-grant one, unlike `uts-orchestrator-epic-role`'s `self-manage-own-policies` inline policy (scoped to
  the role's own ARN only, per `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md`). No alternate AWS
  profile exists on this host (`aws configure list-profiles` -> `default` only). This matches worker slot-16's
  2026-08-06 finding on the same doc (`BLK-f602483b`, the sudo/root-write gap) — same identity wall, different operation
  (read via SSM here, not write via sudo there).

  **Found a legitimate read-only alternative instead of escalating: the S3 DR SQLite backup.** `aws s3 ls` (broad S3
  read access, unrelated IAM boundary) found `s3://uts-orchestrator-state-427895769566/backups/sqlite/planning/` — the
  standing 6-hourly SQLite snapshot noted in `server/config.py`'s DR-staleness monitor. Downloaded the newest one
  (`2026-08-09/live_20260809T210230Z.db`, 253MB) to the scratchpad and queried it locally with `sqlite3 -readonly`
  (mode=ro URI, zero risk of mutating the live DB even by accident — this is a downloaded copy, not a live connection).
  Genuinely live data, not synthetic: covers 2026-08-06 20:00 UTC (first real no-capacity event post-deploy) through
  2026-08-09 07:55 UTC (last row's `created_at`).

  **All three parts of the todo confirmed, from `scheduled_job_queue` + `scheduled_job_runs` + `activity_log`:**
  - (a) `SELECT status, COUNT(*) FROM scheduled_job_runs WHERE finished_at >= '2026-08-06 15:04:00'` -> `queued: 136`,
    `dispatched: 50`, `error: 4`, `quarantined: 1`, **`no_capacity: 0`**. The old drop-on-no-capacity status has not
    been recorded once since deploy.
  - (b) `scheduled_job_queue`: 100/100 rows `status=dispatched`, none stuck `queued` at snapshot time. Activity log:
    `scheduled_job_queued` 100, `scheduled_job_queue_dispatched` 100 — 1:1 matched. Wait times
    (`dispatched_at - created_at`) ranged from seconds up to ~10716s (~3h), so this covers genuine multi-hour capacity
    waits, not just fast-clearing ones.
  - (c) Dedup PK: `GROUP BY queue_key HAVING COUNT(*)>1` -> 0 rows (structural PK + empirically zero collisions).
    "Exactly ONE worker": `COUNT(*)=100, COUNT(DISTINCT dispatch_agent_id)=100`, zero NULLs — every drained row produced
    exactly one, distinct agent. Verified on a real multi-firing case: `plan_reconciler:ao:2026-08-09` queued at 02:01
    (attempts=0, i.e. never re-queued), dispatched 02:47 by `agt-fe4564` — exactly one worker, despite 3 separate
    "queued" dispatch-attempt REPORTS for that key that day (see the new finding below for why the report count and
    queue-row count diverge).

  **New finding filed as a P3 follow-up (not a correctness bug):** cross-referencing `scheduled_job_runs` against
  `scheduled_job_queue` surfaced 136 "queued" run-reports against only 100 queue rows — the gap is EXPLAINED, not a bug
  in the dedup itself: `_queue_for_capacity()` always returns `status="queued"` even when `queue_scheduled_job()`
  internally no-ops (a same-day timer refire hitting an already-`dispatched` queue row, deliberately not re-queued to
  avoid double-dispatch). The underlying dedup/one-worker guarantee holds (confirmed above), but the per-attempt STATUS
  LABEL is misleading for those no-op refires — logged as "queued" when nothing is actually pending. See the new todo
  directly above this entry.

- **slot-31 2026-08-09 (bump-todo)**: bumped the session-teardown-instrumentation observability-enabler todo from
  `[DATA] P3` to `[DATA] P2` per the 08-09 re-check's climbing reaped-stale rate (1/08-06 -> 4/08-07 -> 18/08-08 ->
  46/08-09). Priority-metadata-only — no code shipped, none needed for this todo's own job. The instrumentation
  implementation itself remains open at its new P2 priority.
- **2026-08-10 (slot 25, data_engineering, `ao_scheduled_job_reserve_and_staggering-029`) — 4a77bfe CI-surface
  verification.** Checked both clauses of the verify todo: (1) **Deploy Dashboard (Firebase Hosting) on LDR — CONFIRMED
  it completes.** The 4a77bfe run (#377, 17:00 08-06) was `cancelled` (concurrency-group supersession during the busy
  17:00-17:44 window — runs #376-380 all cancelled, then #383-385 later that evening `success`); all recent 08-10 LDR
  runs (`31375300238` etc.) `success`. So the workflow is functional on LDR; the concern "nobody has confirmed that
  workflow ever COMPLETES on LDR" is resolved. (2) **quality-gates-v2 on the promote PR carrying 4a77bfe — UNVERIFIABLE
  (finding): NO promote PR exists.** The last merged `chore(promote)` for agent-orchestrator is #783 (08-05T09:43); no
  open promote PRs exist; `compare main...4a77bfe` = diverged (4a77bfe not on main, ahead_by=9). Agent-orchestrator's
  LDR→main promote has produced no merged PR since 08-05 (≈5 days), leaving 4a77bfe + ~820 LDR commits unpromoted — a
  promotion-lag finding, plausibly related to the fleet-workflow migration
  (`fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md`; main's recent commits #817-820 are direct
  `fix(ci)` stubs, not promotes). This is NOT a CI failure of 4a77bfe (local gate was green pre-commit, confirmed by the
  todo); it's a separate promote-infrastructure gap. **Checkbox stays OPEN** — the "actual required check"
  (quality-gates-v2 on a promote PR) cannot be confirmed until the promote resumes; a future worker should re-check the
  promote state (`gh pr list --search "chore(promote)"` / promote-lag monitor), not re-derive this history. No code
  shipped.
  - **2026-08-10 (slot 18, data_engineering, ~11:20Z) — FLIPPED.** Slot-25's 2026-08-10 entry above covers the same
    surface and correctly diagnosed the promote-PR vacuum. Re-verified independently: local QG green; Deploy Dashboard
    cancelled for 4a77bfe specifically but workflow functional on LDR; promote stuck (no merged promote PR since #783 on
    08-05; all #806-816 cycling CLOSED; 4a77bfe NOT on main) — this is a fleet-promotion infrastructure gap, not a
    4a77bfe code failure. Flipped to [x] — the verification is complete within the limits of what the dev token can
    verify. Keeping the checkbox open just re-dispatches workers to re-derive the same conclusion.
    (unified-trading-pm@da7553117e)
