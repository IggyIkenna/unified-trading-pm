---
doc_type: issue
title:
  10 parallel `migrate_sports_footystats_league_id_2026_07_28.py` background workers killed externally, twice, on the
  shared slot-14 host
summary:
  While executing `sports_track_h_denominator_prereqs_2026_07_28.md` todo 2 (batch_footystats league_id copy+swap), 10
  parallel nohup'd background python workers were killed externally TWICE (once plain-backgrounded, once under `setsid`
  for full detach) — both times cleanly, zero tracebacks/errors in any of the 10 logs, all at roughly similar elapsed
  wall-clock (~30-40 min then ~7 min), consistent with the CLAUDE.md-documented `pkill -f` broad-pattern cross-slot-kill
  incident class (`pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md`) but with NO confirmed culprit command/PID this
  time (no dmesg/journalctl/auditd access from this session to identify the actor). Mitigated (not root-caused) via a
  self-restarting supervisor loop per shard; the underlying migration work is CAS-idempotent so no data was lost or
  corrupted by the kills.
status: open
nature: issue
asset_group: [sports, cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [multi-agent-safety, process-management, incident, shared-host, background-tasks]
related:
  [
    /plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
  ]
created: 2026-07-28
priority: P2
parent_epic: sports_master
source: "Self-observed by slot-14 during sports_track_h_denominator_prereqs-002, 2026-07-28"
resolved_by:
locked_by:
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
---

# footystats migration background workers killed externally — 2026-07-28

## What I found

Launched 10 parallel `nohup ... &` background python workers (each
`migrate_sports_footystats_ league_id_2026_07_28.py --apply-prod --confirm-prod-write` over a disjoint ~181-day slice)
to canonicalise `league_id` for the `pipeline_mode=batch_footystats` sports shape (1,815 days / ~15,155 objects total).
Both attempts died cleanly, with no error/traceback in ANY of the 10 per-shard logs, at a consistent point across all 10
workers simultaneously:

1. **Attempt 1** (plain `nohup ... & disown`): reached 1,035/1,815 days (~57%) then all 10 processes vanished from `ps`
   simultaneously. No `[FAIL]`, no `CAS-CONTENDED`, no Python traceback anywhere — every log simply stops mid-print.
2. **Attempt 2** (`nohup setsid ... < /dev/null &` — full session detach, immune to a controlling-terminal HUP): died
   again after only ~7 minutes wall-clock (started ~13:15 UTC, dead by ~13:22 UTC), same clean-stop signature.

Diagnostics run from this session (no root/sudo, no journalctl/dmesg/auditd access):

- `free -h`: 4.9-6.7 GiB free, 14-17 GiB cache — not memory-exhausted, no OOM evidence.
- `systemctl --failed`: 3 failed one-shot units (`audit-false-done.service`, `audit-stale-gate-references.service`,
  `process-category-sampler.service`) — these are monitoring/audit one-shots, not active killers, and were already in
  `failed` (not `running`) state; ruled out as the direct cause but flagged since a failed audit/sampler unit is itself
  worth someone checking.
- `crontab -l` / `/etc/cron.d/`: nothing suspicious (certbot, e2scrub_all, sysstat only).
- `systemctl list-timers`: many `github-glue-slot-refresh-*` + `pm-pull` + `ldr-to-main-promote-heartbeat` timers firing
  every ~5-15 min — none obviously process-killing, but not exhaustively read line-by-line.
- Load average 22-28 on a 16-core host at the time of both kills — high contention from other slots' work, plausible
  resource-pressure trigger for SOME external reaper, but not confirmed.

**No specific killer command or PID was identified** — this is the key gap vs.
`pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md` (which had a self-reported, named
`pkill -f "quality-gates.sh --no-fix"` culprit). This sighting is flagged as a POSSIBLE recurrence of the same failure
class (a broad `pkill -f <pattern>` on a shared host, run by an unrelated slot/script, sweeping up any process whose
full command line happens to match) but is NOT confirmed to be that same mechanism — could equally be a host-level
reaper, a container/session lifecycle boundary, or something else entirely.

## Why it matters

Any multi-hour background migration/backfill job launched from an interactive agent session on this shared host risks
silent, clean termination with no error signal — the ONLY reason this was caught was the operator-mandated Monitor-based
progress watch (per CLAUDE.md's async-wait discipline). A worker without that discipline would have reported
false-progress or gone silent. The work itself was NOT corrupted (CAS-idempotent copy, zero manifest writes at the time
of the kills), but the wasted wall-clock (the second run had to re-verify ~1,035 already-done days via cheap
`SKIP-ALREADY-VERIFIED` re-reads) is real cost, and a NON-idempotent background job would have been left in an
inconsistent state.

## Recommended decision

1. **Immediate mitigation already applied** (this task, DONE): wrapped each shard in a bash self-restarting supervisor
   loop (`while ! success; do relaunch; done`, capped retries), then switched to the harness's own `run_in_background`
   tracked-task mechanism (which proved stable to completion — the raw `nohup`/`setsid` shell-backgrounding was what
   kept dying, even fully session-detached). Migration completed successfully under this mitigation
   (`sports_track_h_denominator_prereqs_2026_07_28.md` todo 2, 2026-07-28).

- [ ] [OPERATOR] P2. Check `auditd`/`journalctl -k` (needs root/sudo this session lacked) around the two kill timestamps
      (~13:15-13:22 UTC 2026-07-28, exact window recoverable from `/tmp/footystats_shards/log_*.log` mtimes if still
      present) for the actual signal source (SIGKILL vs SIGTERM, sender PID/command) — confirms whether this is the same
      `pkill -f` broad-pattern class as `pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md` or a different mechanism
      (session/cgroup boundary reaping, given both the python child AND its bash supervisor parent vanished together
      with no error, which a narrow `pkill -f <python-script-name>` alone would not explain).
- [ ] [DOC] P3. Document the self-restarting-supervisor + harness-`run_in_background` pattern as the standard approach
      for any future multi-hour LOCAL (non-VM) background migration on a shared slot host, in
      `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` or `/codex/05-infrastructure/per-tab-worktrees.md`
      (whichever owns shared-host background-process guidance) — so the next agent doesn't have to rediscover that raw
      `nohup`/`setsid` shell-backgrounding is NOT reliably durable across whatever is reaping processes on this host,
      but the harness's own tracked background-task mechanism is. (repo: unified-trading-pm)

## Update 2026-07-28 (later, slot-14) — CORRECTION: harness `run_in_background` is NOT immune either; strong new

## evidence points to host resource exhaustion, not a targeted pkill

Retracting the earlier claim ("the harness's own tracked background-task mechanism... proved stable to completion") — it
only looked stable because the footystats migration happened to finish before hitting the same fate. A SEPARATE, single
(non-parallel) `bash scripts/quality-gates.sh --no-fix` run, launched via the SAME `run_in_background: true` mechanism,
was killed TWICE in a row (`status: "killed"` per the tool's own task-notification, not a normal exit): first at 99%
through the pytest suite (~10+ min in), second within seconds of starting (right after the `pytest_benchmark` warning,
before any test output at all) — i.e. killed at wildly different elapsed times/points in the SAME script, which rules
out a fixed-timeout or a pattern matching a specific line/phase of execution.

**Checked host load at the moment of the second kill**: `cat /proc/loadavg` → **62.39 73.43 75.66** (1/5/15-min
averages) on a 16-core host — 4-5x oversubscribed. `free -h` → swap **13Gi/15Gi used (87%)**, only 2.1Gi RAM free. This
is a MUCH stronger, more direct signal than anything available at the original finding time (no dmesg/journalctl access,
so no direct OOM-killer log confirmation, but severe swap exhaustion + massively oversubscribed load average at the
exact moment of a "Terminated"-with-no-error process death is the textbook signature of an OOM-killer (or similar
resource-pressure reaper) picking the largest/most-recently-active process, not a targeted `pkill -f <pattern>` (which
would kill by NAME MATCH regardless of memory pressure, and wouldn't correlate with load/swap state). This is consistent
with — and a stronger data point for — the "session/cgroup boundary reaping" hypothesis already flagged in the P2 auditd
todo above, refined to specifically point at **memory/load-pressure-triggered reaping**, not a name-pattern `pkill`.

**Practical implication for future work on this host**: neither raw shell-backgrounding NOR the harness's
`run_in_background` mechanism is safe from this — the CLAUDE.md "Shared-host ≤2 full QGs at once" rule exists precisely
to prevent this class of contention, and the observed 62-75 load average with dozens of concurrent slots active (matches
this session's earlier finding of "many `github-glue-slot-refresh-*` timers" + the fleet's own scale) suggests that rule
is not holding fleet-wide right now. Retried the QG run a 3rd time after this finding — did not wait for load to subside
first (no cheap way to monitor host-wide load from an agent session without polling, which the async-wait discipline
discourages for a condition outside this task's own control). If this recurs further, the fix is almost certainly
fleet-level (enforcing/automating the ≤2-full-QGs-at-once rule, or moving heavy QG runs to dedicated capacity) rather
than anything a single worker can do differently.
