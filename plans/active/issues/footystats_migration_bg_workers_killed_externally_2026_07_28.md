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

1. **Immediate mitigation already applied** (this task): wrapped each shard in a bash self-restarting supervisor loop
   (`while ! success; do relaunch; done`, capped retries) so the migration makes forward progress regardless of repeated
   external kills — this is a workaround, not a fix.
2. **Follow-up** (not done here — needs root/sudo or `auditd` access this session lacked): whoever has host access
   should check `auditd`/`journalctl -k` around the two kill timestamps (~13:xx UTC 2026-07-28, exact window recoverable
   from `/tmp/footystats_shards/log_*.log` mtimes if still present) for the actual signal source (SIGKILL vs SIGTERM,
   sender PID/command).
3. **Standing guidance gap**: CLAUDE.md's existing HARD RULE ("Process kills — exact PID only, never a name-based
   pattern") already covers the FIX for an agent's OWN pkill usage; it does NOT yet cover "how should a long background
   job on a shared host defend against an unknown external killer" — the self-restarting-supervisor pattern used here
   may be worth promoting to a documented convention for any future multi-hour local (non-VM) background migration, so
   the next agent doesn't have to rediscover it. Not resolving that guidance question here — flagging for whoever next
   authors/updates the async-wait-and-poll-discipline or per-tab-worktrees codex docs.
