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
priority: P0
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

## 🔴 ESCALATION 2026-07-28 (later still, slot-14) — load average now 185-259, this slot's whole SESSION died mid-task,

## priority bumped P2->P0

**Severity has escalated materially since the entries above.** While running a LIGHTWEIGHT (GCS-listing/verification,
not CPU-heavy) marker-purge dry-run for an unrelated task (`defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` todo
5), this agent's entire session died mid-task — not just the one background process (which was also killed,
`exit code 144`, no `EXIT_CODE=` sentinel written), but the session itself required a full resume
(`"You are worker slot 14, RESUMED after your session died mid-task"`). `cat /proc/loadavg` immediately after resume
showed **185.17 259.50 252.63** — roughly **16x oversubscribed** on this 16-core host, an order of magnitude worse than
the already-severe 62-75 recorded ~30 min earlier in this same session. This is no longer "elevated contention" — it is
a host-wide capacity crisis actively taking down agent sessions, not just individual heavy processes.

**Bumping this issue's priority P2 → P0** and flagging for operator visibility: if load is genuinely 185-259 sustained,
EVERY slot on this shared host is likely experiencing degraded reliability right now (killed processes, possible session
death), not just this one. This is beyond what a single worker can diagnose or mitigate (no root/sudo access to identify
what's consuming capacity, no ability to reduce fleet-wide concurrency from within one session). Recommending the
operator check overall host/fleet health directly (host-level monitoring, VM sizing, or whether an unbounded process on
this shared host is the root cause) rather than treating this as N independent per-task incidents.

**Silver lining — no data lost**: the marker-purge dry-run's resume-log survived on local disk (8,903 markers already
processed, resumable) and `market-tick-data-service`/all other repos in this slot show a clean `git status` — nothing
uncommitted was lost by the session death, confirming the CAS/resume-log-based idempotent design pattern this workspace
already favors is doing its job even under this failure mode.

## Update 2026-07-28 (later still, slot-14) — load partially receded (185-259 → 66-95) but STILL killed a 4/4-worker resume after only 130 markers; crisis is ongoing, not a one-off spike

Waited for load to decline before retrying (per the P0 escalation's own recommendation), then resumed the SAME
category-1 marker-purge dry-run (`defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` todo 5) from its 8,903-entry
resume-log with workers reduced further (`--discover-workers 4 --verify-workers 4`, down from the already-reduced 8/8).
Pre-launch check: load `69.30 85.48 139.79`, `free -h` showed 4.6Gi free / 19Gi available, swap 7.8Gi/15Gi (52%) —
meaningfully better than the 185-259/87%-swap crisis point, so this was a considered retry, not a blind one.

**Result: killed again.** Discovery completed cleanly (54.2s, 328,994 markers scanned, 23,588 in the
CURVE/SUSHISWAP/TRADER_JOE_V2/VELODROME_V2 × dex_pool_state scope, 14,685 remaining to process) — discovery itself is
apparently light enough to survive. But the verification phase died silently after only ~130 more markers (resume-log
grew 8,903 → 9,033) with **no traceback, no error, no `SUMMARY` block** — the exact same clean-kill signature as every
prior incident in this doc. Post-mortem host state: load `66.33 72.43 113.95`, **free memory only 1.7Gi** (worse than
the 4.6Gi seen pre-launch — other slots' concurrent work consumed it in the interim), swap 8.5Gi/15Gi (57%).
`ps --sort=-%mem` showed no single runaway process — the pressure is aggregate, from dozens of concurrent `claude`
sessions + several other slots' `pytest -n 1/2` QG runs, consistent with the fleet exceeding CLAUDE.md's "≤2 full QGs at
once" rule broadly, not narrowly.

**New data point this adds**: even a 2x-more-conservative (4/4 vs 8/8) worker count, on a HOST STATE that looked
meaningfully recovered at launch time, still died — confirming this is a genuinely fluctuating, ongoing fleet-wide
resource crisis (available headroom can evaporate within the ~1-2 minutes between a pre-launch check and the process
actually running), not a fixed threshold a worker can safely time around by checking load once before launching. The
session itself survived this time (only the backgrounded process was reaped, not the whole `claude` process) — a smaller
blast radius than the earlier full-session death, but the same root mechanism.

**No data lost, still resumable**: resume-log now at 9,033/23,588 entries, all repos in this slot clean. Not retrying
again immediately — will back off and re-check host state before the next attempt, per this doc's own async-wait
guidance, rather than repeatedly relaunching into the same condition.

## Update 2026-07-28 (later still, slot-14) — LIKELY MECHANISM IDENTIFIED: nohup+disown detachment, not host load, is the proximate trigger for this specific class of kill

A third resume attempt (`--discover-workers 2 --verify-workers 2 --limit 3000`, same `nohup ... & disown` launch pattern
as the two prior attempts) died the same way — resume-log grew only 9,033 → 9,080 (47 more markers) before silent death,
with load at the time actually LOWER (`49.23 64.89 105.83`) than either prior attempt. A fixed launch pattern dying at a
similar small item-count/wall-clock position regardless of load level and regardless of worker count (130 → 47 markers
processed across three attempts, all within roughly 1-3 minutes of the verification phase starting) does not fit a
load-proportional OOM/reaper model — it fits a **fixed-duration or session/cgroup-boundary reap of nohup+disown-detached
processes specifically**, independent of host load.

**Test**: relaunched the identical script (`--discover-workers 4 --verify-workers 4 --limit 5000`) with NO
`nohup`/`disown` at all — run directly in the foreground of the agent harness's own tracked background-task mechanism
(`run_in_background: true` on the tool call itself, the process staying attached to that tracked task rather than being
detached into an orphaned session). **Result: survived well past the ~1-3 minute death window that killed every
nohup-detached attempt** — confirmed still running and making real progress (9,080 → 9,476 resume-log entries, i.e. 396
markers processed) after 11+ minutes of wall-clock, at a similar/slightly worse host load (`69.54 76.20 85.45`) to the
attempts that died in under 3 minutes.

**Practical implication, refining this doc's own P3 recommendation**: this does NOT contradict the earlier
`quality-gates.sh` finding that harness `run_in_background` is "not immune either" (that was a genuinely
CPU/memory-heavy pytest run, plausibly a real OOM-killer victim by RSS/CPU badness score) — the two findings are about
DIFFERENT process weight classes hitting DIFFERENT kill mechanisms. For a LIGHTWEIGHT, long-running, I/O-bound script
(like this GCS-listing/verification purge), avoid `nohup ... & disown` entirely and run it directly under the harness's
own tracked `run_in_background` — it appears meaningfully more durable for this weight class specifically. Still
monitoring whether this run completes cleanly before treating this as fully confirmed rather than a promising single
data point.

**Confirmed sustained (not just a promising start)**: as of ~25 minutes wall-clock, the harness-tracked run is still
alive and healthy — resume-log climbing steadily (9,080 → 9,899, i.e. 819/5,000 processed this batch), disposition
counts sane (`SAFE_NEEDS_ATTRIBUTION_COVERED=4, SAFE=462, FLAGGED_NO_SIBLINGS_NO_BACKUP=34` at the 500-mark, no
unexplained categories), host load still elevated (`77-83`) throughout with zero further kills. Per-item throughput is
slow (~1.5s/marker, ~2h projected for this 5,000-item batch) — a contention-driven slowdown, not a stall (CPU time on
the process climbs steadily, `ps` shows healthy RSS ~150MB, not swapping). Letting it run to completion rather than
interrupting a working approach; will relaunch subsequent batches (~9,500 markers remain after this one) the same way
(direct `run_in_background`, no `nohup`) once this one lands.

## Update 2026-07-28 (later still, slot-14) — harness-tracked run DID eventually die too, but survived ~10x longer than nohup-detached attempts; refining the mechanism theory, not discarding it

After restarting once more at doubled concurrency (`--discover-workers 8 --verify-workers 8`, no `--limit`, still no
`nohup`) to process the full remaining ~13k-marker scope in one run, the process ran healthily for a long stretch —
resume-log climbed steadily from 10,620 through 14,538 (3,918 markers processed) over roughly 90+ minutes of wall-clock,
well past the earlier confirmed-sustained checkpoint. It then went silent: the harness itself returned a
`status: "stopped"` task-notification with **no completion record** ("may have been stopped via the UI, Monitor timeout,
or agent teardown — these leave no transcript marker, or it may have been running when the previous Claude Code process
exited"). `ps aux` confirmed the process is genuinely gone. Resume-log survived intact at 14,538 entries — no data lost,
safely resumable per the established contract.

**Host state at the moment this was discovered** (checked immediately after the notification, not assumed):
`cat /proc/loadavg` → `93.52 74.77 69.15` (1-min spiking back up while 5/15-min were still elevated-but-lower — a fresh
spike, not a sustained plateau) and, critically, `free -h` → **swap 15Gi/15Gi used (100%, only 275Mi free)**, RAM free
only 1.1Gi. This is the MOST severe memory-pressure reading of this entire incident sequence — every prior reading had
at least some swap headroom (52-87% used); this one shows swap **fully exhausted**. A fully-exhausted swap is the
textbook precondition for the kernel OOM-killer to activate aggressively regardless of any single process's own
footprint, and is consistent with either the specific tracked process being reaped OR (per the notification's own
wording) the surrounding session/tooling layer itself being torn down under the same pressure.

**Refining, not discarding, the nohup-detachment theory**: the harness-tracked (non-nohup) approach survived roughly
**10x longer** than any nohup-detached attempt (90+ minutes vs. 1-3 minutes) before finally succumbing to what looks
like a genuine, severe resource-exhaustion event (100% swap) rather than the earlier session/cgroup- boundary pattern
(which killed nohup'd processes at a consistent short duration regardless of load level). Both mechanisms are real:
nohup+disown detachment is a near-immediate, load-independent kill; sustained/peak host resource exhaustion is a
separate, less frequent but still real risk that eventually catches even a properly harness-tracked background process.
Avoiding `nohup` remains clearly worth doing (it moved the failure mode from "minutes" to "an hour-plus"), but does not
make a long-running local process on this host bulletproof against a genuine capacity spike.

**Next step**: NOT retrying into a 100%-swap host immediately. Waiting for swap/load to show real recovery before the
next resume attempt (same recipe: harness `run_in_background`, no `nohup`, `--resume-log` pointed at the same
14,538-entry checkpoint).

## Update 2026-07-28 (later still, slot-14) — checked ~20 min later expecting recovery; instead WORSE — new peak, host-wide crisis is not self-resolving

Re-checked host state before considering a resume attempt, expecting some recovery after a ~20-minute wait. Instead:
`cat /proc/loadavg` → **180.00 305.13 324.96** — a NEW peak, higher than the previous worst reading in this doc (185.17
259.50 252.63). `free -h` → RAM 26Gi/30Gi used, only **669Mi free** / 4.3Gi available; swap **15Gi/15Gi used (100%, only
23Mi free)** — swap has now been at or near full exhaustion across two consecutive checks roughly 20 minutes apart, not
a transient spike that self-clears. Resume-log unchanged at 14,538 (no attempt made this check — correctly held off per
the prior update's own guidance).

**This is not resolving on its own.** Two independent severe readings 20 minutes apart, one of them a new all-time peak
for this doc, strongly suggests a sustained fleet-wide condition (many concurrent slots' heavy work, consistent with the
earlier-corroborated "31 concurrent full QGs vs. a 4-QG cap" finding from an unrelated slot) rather than a transient
burst that will clear itself shortly. Continuing to hold off on any new local background launch on this host. Given this
has now degraded to a NEW worst-recorded state while multiple workers (this one included) are deliberately backing off
and waiting, the mitigation available to a single worker (waiting) does not appear to be converging — this may need
operator-level intervention (identifying/throttling whatever is driving the fleet-wide over-concurrency, e.g. enforcing
the existing "≤2 full QGs at once" rule, or reducing total active slot count) rather than more individual workers
independently waiting it out.
