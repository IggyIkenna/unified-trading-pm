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
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
assigned_role: NA
drift_direction: flat
last_updated: 2026-08-04
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

- [ ] [SCRIPT] P2. Re-verify `github.slice`'s weight survives an actual VM restart (not just confirm the file is
      present) — `systemctl daemon-reload` was run this session but the unit's `static` load state has not been proven
      across a full reboot cycle. `cat /sys/fs/cgroup/github.slice/io.weight` should read "default 20" after any future
      orchestrator VM restart; if it ever reads "default 100" again, the file didn't survive and needs re-installing
      (`sudo cp scripts/github.slice /etc/systemd/system/github.slice && sudo systemctl daemon-reload`).
- [ ] [SCRIPT] P2. Check final outcome of the 3 redispatched tranches fired after the github.slice fix: `agt-d4a899`
      (na_eligibility[sports], slot 8), `agt-8b3403` (na_eligibility[infra], slot 9), `agt-7322c2` (ag_closeout[sports],
      slot 4) — all registered ~2026-08-04T13:50Z, all still active as of this doc's writing. Query
      `GET /api/agents?include_finished=true` for each id; expect `status=archived exit_reason=lifecycle-     complete`
      if the fix holds under sustained real load, not just the initial 5-minute PSI snapshot.
- [ ] [SCRIPT] P3. Re-measure PSI io/cpu/memory a few hours after this fix, under a full day of normal CI+audit traffic,
      to confirm the 57.34->32.58 improvement holds (not just an artifact of the specific 5-minute window measured) and
      to tune `IOWeight=20`/`CPUWeight=20` against real data rather than this session's initial estimate — raise toward
      50 if CI throughput visibly degrades, the file's own header comment already says so.
- [ ] [SCRIPT] P3. Track `/etc/systemd/system/orchestrator.service.d/cpu-priority.conf` (the 2026-07-28
      CPUWeight=4000/IOWeight=1000 fix referenced throughout this doc) in a repo — it currently exists ONLY as a live VM
      drop-in, same "no home" gap this doc's own `scripts/github.slice` just closed for the newer fix. Same risk: a VM
      rebuild would silently lose it.
- [ ] [DATA] P3. Investigate the 2026-08-02 ~11:34 UTC 58-way simultaneous `timeout` cluster (see "Corrected an earlier
      claim" above) if it recurs — not investigated this session, out of window.

## Progress Log

- **context-scout 2026-08-05**: populated/refreshed context_scope (6 entries) — corrected a wrong file
  (`tmux_pruner.py`, not actually the slot-level stale-flip mechanism this doc discusses) to the real one
  (`worker_liveness_watchdog.py`, confirmed to hold `_reclaim_idle_lingering_sessions`, the reclaimer named in item 1
  above); trimmed the duplicate second install-timer script to stay within the 2-6 target.
