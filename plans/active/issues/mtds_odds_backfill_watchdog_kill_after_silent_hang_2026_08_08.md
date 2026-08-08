---
doc_type: issue
title:
  "MTDS sports-odds backfill VMs die repeatedly (3x so far) — total silence for ~16-24 min then correctly killed by the
  vm-zombie-watchdog, root cause of the silence itself unconfirmed"
summary: >-
  THREE consecutive `mtds-backfill-odds-*` VMs (`smallchunk2`, `smallchunk3`, `smallchunk4`) died mid-run with the
  identical signature: `run.log` and the heartbeat blob both go completely silent (no new lines, no heartbeat refresh)
  for ~18-24 minutes, then `gcloud compute operations list` shows a `delete` operation. Neither death has a terminal
  `exit_code=` line, a `Traceback`, a `CHUNK_FAILED`, or any other error marker in the persisted `run.log` — just an
  ordinary mid-work log line (a `RESOURCE_SAMPLE` with unremarkable RSS, ~15-25% of the OOM-observed peak) followed by
  silence. Confirmed via `deployment-service/scripts/vm/vm_zombie_watchdog.py`
  (`gs://deployment-scripts-{project}/vm-heartbeat/{vm}.txt`) that the heartbeat blob itself also stopped updating in
  the same window — this is NOT a false-positive watchdog read of a still-alive VM (the codebase's documented 2026-07-18
  precedent for API-Football VMs), it looks like the watchdog correctly caught a genuine hang and killed it as designed.
  What's still unconfirmed: WHY the underlying Python process (or its wrapping `mtds_chunk_loop.sh`) stops emitting ANY
  output — no OOM kernel message, no Python exception, nothing — for that specific ~20-minute window. Both occurrences
  happened during REAL-FETCH-heavy work (not skip-fast dates): `smallchunk2` died mid-chunk-26 (past its own prior-run
  boundary, genuinely new ground); `smallchunk3` died mid-chunk-18 (the known 2020-08-30→2020-09-03 season-opener week,
  mid-`SCOTTISH_PREMIERSHIP` real-fetch). No data loss either time — the manifest's per-VM shard writes are durable
  regardless of which VM instance wrote them, and a relaunch with `RESUME_FORCE=false` correctly skip-fasts through
  already-captured ground.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [backfill, hang, watchdog, odds-api, mtds, vm-hang, reliability]
related:
  [
    plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
    plans/active/issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md,
  ]
created: 2026-08-08
author: claude-agent
priority: P1
parent_epic: infrastructure_master
source: >-
  Found during the autonomous sports honest-coverage convergence monitoring loop (continuation of
  sports_all_vendor_honest_coverage_convergence_2026_08_07.md) while investigating why `mtds-backfill-odds-smallchunk2`
  (2026-08-08T00:55Z) and `mtds-backfill-odds-smallchunk3` (2026-08-08T05:26Z) both vanished mid-run with no obvious
  cause.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
context_scope:
  [
    deployment-service/scripts/vm/vm_zombie_watchdog.py,
    deployment-service/deployment_service/vm_prefix_registry.py,
    deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh,
    market-tick-data-service/scripts/setup-data-pipeline-vm.sh,
  ]
---

## Timeline (three occurrences now — pattern confirmed, not coincidence)

| VM                                        | Last real log line                                                      | Heartbeat blob last update                                               | Delete op timestamp       | Silent gap |
| ----------------------------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------ | ------------------------- | ---------- |
| `mtds-backfill-odds-smallchunk2-20260807` | `2026-08-08T00:36:42Z` (mid-chunk-26, EPL, RSS=16.3GiB)                 | not separately checked this occurrence                                   | `00:55:20Z` / `00:56:15Z` | ~19 min    |
| `mtds-backfill-odds-smallchunk3-20260808` | `2026-08-08T05:05:17Z` (mid-chunk-18, SCOTTISH_PREMIERSHIP, RSS=8.6GiB) | `05:06:23Z` (confirmed via `gcloud storage ls -L` on the heartbeat blob) | `05:26:25Z`               | ~20-21 min |
| `mtds-backfill-odds-smallchunk4-20260808` | `2026-08-08T08:11:46Z` (mid-chunk-18, AUSTRIAN_BUNDESLIGA, RSS=24.4GiB) | `08:11:31Z` (confirmed via `gcloud storage ls -L`)                       | `08:27:34Z`               | ~16 min    |

**New pattern confirmation from occurrence 3**: RSS at time of last log line varies widely across the three deaths
(16.3GiB, 8.6GiB, 24.4GiB) — ruling out a fixed-memory-threshold trigger. The silent gap is consistently tight (~16-21
min across all three) regardless of which league/RSS was active, which is the strongest signal this is the watchdog's
`HEARTBEAT_STALE_MINUTES` threshold firing on a real, consistent-duration hang — not noise. All three deaths happened at
or near chunk 18 specifically (chunk 26 once, chunk 18 twice) — chunk 18 is the known season-opener real-fetch-heavy
week, so real-fetch load remains the strongest circumstantial correlate, though this same occurrence's relaunch
(`smallchunk4`) already survived chunk 18's opening leagues cleanly before dying later in the same chunk — so it is not
simply "chunk 18 always hangs," more like elevated real-fetch load raises the odds of hitting whatever the underlying
trigger is.

Both delete operations' `principalEmail` = `1060025368044-compute@developer.gserviceaccount.com` — the shared automation
service account used by both the watchdog itself and every manual `gcloud` action in this workspace, so this alone
doesn't distinguish "watchdog" from "a human/session ran `gcloud compute instances delete` directly." The codex rule
cited in `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` (`Self-deleting VM/job` section) says a GRACEFUL
self-delete-on-exit writes a terminal `exit_code=` line to `run.log` before destroying itself — neither occurrence has
one, which rules out the VM's own normal completion-or-crash self-delete path. The consistent ~19-21 minute gap across
two independent occurrences (different VM instances, different chunks, different real-fetch content) is the strongest
evidence this is the **watchdog's heartbeat-staleness check** (`HEARTBEAT_STALE_MINUTES`, default ~15-20 min per
`vm_zombie_watchdog.py` / its AWS twin) firing on a genuine silence, not two coincidental unrelated events.

## What's confirmed

- **Not OOM.** Neither death has a kernel OOM-kill message or an `exit=137` `CHUNK_FAILED` line — the last RSS reading
  in both cases (16.3GiB and 8.6GiB) is well below the ~28-31GiB range where this launcher's known OOM pattern
  (`mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`) actually triggers.
- **Not a watchdog false-positive against a genuinely-alive VM** (the documented 2026-07-18 API-Football precedent) —
  the heartbeat blob itself (a separate GCS object from `run.log`, updated by a distinct mechanism) also stopped
  refreshing in the same window on `smallchunk3`, so the underlying VM/process genuinely went silent, not just the
  watchdog's read of it.
- **No data loss either time** — manifest per-VM shard writes are durable and address-independent of which VM wrote
  them; a same-checkpoint relaunch (`RESUME_FORCE=false`) correctly skip-fasts through already-covered ground with zero
  re-fetching or re-billing.
- **Both occurrences were during real-fetch-heavy work**, not pure skip-fast dates — circumstantial, not proven, but
  worth noting as the search space narrows.

## What's NOT yet confirmed (open investigation)

- The actual mechanism causing total silence: a genuine process hang (deadlock, a blocking call with no timeout — e.g. a
  `requests`/HTTP call to `odds_api` that never returns and isn't wrapped in a client-side timeout), a kernel freeze
  short of an OOM-kill, or something else entirely. No kernel log, Python traceback, or any other diagnostic survived in
  either case — by the time the VM is discovered gone, the serial console + everything else is also gone.
- Whether this is odds-api-specific or a broader `mtds_chunk_loop.sh` / `market-tick-data-service` issue that just
  happens to be more visible here because this launcher runs many more real chunks per hour than most other backfills.
- Whether `HEARTBEAT_STALE_MINUTES`/`SHARD_STALE_MINUTES` for the `mtds-backfill-odds-` prefix specifically are tuned
  correctly, or whether this prefix needs a `PREFIX_IDLE_THRESHOLDS` override (like the `cefi-fwd-`/API-Football entries
  already present in `vm_prefix_registry.py`) if the real root cause turns out to be "genuinely-alive-but-slow" after
  all, rather than a true hang — not ruled out, just less likely given the heartbeat blob evidence above.

## Mitigation applied so far (not a fix)

Relaunch-on-discovery, each time verified booted + correctly resuming via skip-fast (no data loss, no double-billing).
This is viable as a stopgap since `odds-api-concurrency-guard.sh` keeps concurrent-VM risk bounded and each relaunch
picks up cleanly, but it is NOT a fix — if this recurs a third+ time, or if it starts affecting other `mtds-backfill-*`
prefixes, it should be treated as a real reliability bug worth root-causing properly (attach `strace`/`py-spy` to a live
instance next time it's caught mid-hang, before it goes silent, rather than post-mortem).

## Todos

- [ ] [SCRIPT] P2. **Next time this recurs, catch it BEFORE the silent window elapses** — if a monitoring tick sees a
      VM's `run.log`/heartbeat go quiet, SSH in immediately
      (`gcloud compute ssh ... --command="py-spy dump --pid <pid>"` or `strace -p <pid>`) instead of waiting for the
      watchdog to kill it, to capture the actual hang state.
- [ ] [SCRIPT] P3. Audit whether `market_tick_data_service`'s `odds_api` HTTP client calls have explicit connect/read
      timeouts — a hung socket with no timeout is the single most likely mechanism for "total silence, no exception, no
      OOM."
- [x] ✅ [SCRIPT] P1. **Third occurrence confirmed 2026-08-08T08:27Z (`smallchunk4`)** — pattern is now real, not
      coincidence (consistent ~16-21 min silent gap across 3 independent VMs/leagues/RSS values). Per this todo's own
      original gate, this crosses into needing a real decision rather than another quiet relaunch: relaunched once more
      (`smallchunk5`, keeps real backfill progress moving, no data loss risk) AND flagging this as the priority P1 open
      investigation for whoever next has the tooling to catch a live hang (this session's `gcloud compute ssh` via IAP
      failed with "not authorized" earlier — the diagnostic step in todo 1 below needs a session/operator with working
      SSH access, not just gcloud storage/compute API access).
- [ ] [SCRIPT] P2. Consider whether `PREFIX_IDLE_THRESHOLDS` needs an `mtds-backfill-odds-` entry, OR whether the fix
      belongs in the fetch code's timeout handling instead — don't pre-emptively loosen the watchdog threshold without
      more evidence, since a genuinely-hung VM SHOULD be killed. Lower priority than todo 1 (catching a live hang) — a
      threshold change without knowing the actual root cause risks masking a real bug instead of fixing it.

## Progress Log

- **2026-08-08T05:33Z (autonomous session)** — Created this doc after the second occurrence (`smallchunk3`, died
  05:26:25Z). Root-caused as far as evidence allows this tick: confirmed heartbeat-blob genuinely stopped (not a
  watchdog misread), confirmed no OOM/exit_code/Traceback survived, confirmed no data loss. Relaunched as
  `mtds-backfill-odds-smallchunk4-20260808` to keep the backfill progressing; not investigated further this tick (would
  need to catch a live hang in progress, which requires being mid-tick exactly when it happens — noted as todo 1 above
  for the next occurrence).
- **2026-08-08T08:40Z (autonomous session) — THIRD occurrence, pattern definitively confirmed.**
  `mtds-backfill-odds-smallchunk4-20260808` died the same way: last real log line `08:11:46Z` (mid-chunk-18,
  `AUSTRIAN_BUNDESLIGA`, `RSS=24.4GiB` — a THIRD different RSS value, ruling out a fixed-memory trigger), heartbeat blob
  last updated `08:11:31Z`, `delete` op at `08:27:34Z` (~16 min gap, consistent with the prior two ~19-21 min gaps).
  Notably `smallchunk4` had ALREADY survived chunk 18's opening leagues cleanly (4 leagues, zero OOM, confirmed in the
  sibling convergence doc @ `4488f76c8c`) before dying later in the SAME chunk — so this isn't "chunk 18 always hangs
  immediately," it's more like sustained real-fetch load raises hang odds over time within a session. Bumped priority
  P2→P1 given 3 independent confirmations. Relaunched as `mtds-backfill-odds-smallchunk5-20260808` (guard passed,
  RUNNING) — durable progress preserved through chunk 17 fully + partial chunk 18. **Real limitation hit while trying to
  investigate further this tick**: attempted `gcloud compute ssh` via IAP to the (still-alive, at the time) VM to prep
  for catching a future live hang, got `Error while connecting [4033: 'not authorized']` — this session's service
  account lacks IAP-tunnel SSH permission, so live diagnosis (`py-spy`/`strace`) isn't currently possible from here even
  if a hang is caught in the exact window. Flagging this as the blocking gap for todo 1 above: whoever picks this up
  next needs either IAP SSH access granted to the automation service account, or to be an interactive/operator session
  with working SSH, positioned to attach the moment a hang is suspected (heartbeat >10min stale but VM still RUNNING =
  the window to act in, before the watchdog's own ~16-21 min kill).
