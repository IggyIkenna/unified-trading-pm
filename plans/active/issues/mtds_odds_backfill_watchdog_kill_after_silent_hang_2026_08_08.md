---
doc_type: issue
title:
  "MTDS sports-odds backfill VMs die repeatedly (12x so far) — total silence for ~16-24 min then correctly killed by the
  vm-zombie-watchdog, root cause of the silence itself unconfirmed"
summary: >-
  TWELVE consecutive `mtds-backfill-odds-*` VMs (`smallchunk2`, `smallchunk3`, `smallchunk4`, `smallchunk5`,
  `smallchunk8`, `smallchunk10`, `smallchunk12`, `smallchunk13`, `smallchunk14`, `smallchunk15`, `smallchunk16`,
  `smallchunk17`) died mid-run with the identical signature: `run.log` and the heartbeat blob both go completely silent
  (no new lines, no heartbeat refresh) for ~16-24 minutes, then `gcloud compute operations list` shows a `delete`
  operation. Neither death has a terminal `exit_code=` line, a `Traceback`, a `CHUNK_FAILED`, or any other error marker
  in the persisted `run.log` — just an ordinary mid-work log line (a `RESOURCE_SAMPLE` with unremarkable RSS, ~15-25% of
  the OOM-observed peak) followed by silence. Confirmed via `deployment-service/scripts/vm/vm_zombie_watchdog.py`
  (`gs://deployment-scripts-{project}/vm-heartbeat/{vm}.txt`) that the heartbeat blob itself also stopped updating in
  the same window — this is NOT a false-positive watchdog read of a still-alive VM (the codebase's documented 2026-07-18
  precedent for API-Football VMs), it looks like the watchdog correctly caught a genuine hang and killed it as designed.
  What's still unconfirmed: WHY the underlying Python process (or its wrapping `mtds_chunk_loop.sh`) stops emitting ANY
  output — no OOM kernel message, no Python exception, nothing — for that specific ~16-21-minute window. Death chunks
  are now 18, 18, 26, 26, 26 — **chunk 26 / date≈2020-10-09 has now recurred a THIRD time** (`smallchunk8` died at
  exactly `date=2020-10-09`, same as `smallchunk2`'s "2020-10-09+"), re-strengthening a per-chunk-content correlation
  that had been downgraded after `smallchunk5` cleared chunk 26 cleanly once — worth a closer look if a 4th chunk-26
  death occurs. No data loss in any case — the manifest's per-VM shard writes are durable regardless of which VM
  instance wrote them, and a relaunch with `RESUME_FORCE=false` correctly skip-fasts through already-captured ground.
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

## Timeline (twelve occurrences now)

| VM                                         | Last real log line                                                             | Heartbeat blob last update                                               | Delete op timestamp       | Silent gap |
| ------------------------------------------ | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------ | ------------------------- | ---------- |
| `mtds-backfill-odds-smallchunk2-20260807`  | `2026-08-08T00:36:42Z` (mid-chunk-26, EPL, RSS=16.3GiB)                        | not separately checked this occurrence                                   | `00:55:20Z` / `00:56:15Z` | ~19 min    |
| `mtds-backfill-odds-smallchunk3-20260808`  | `2026-08-08T05:05:17Z` (mid-chunk-18, SCOTTISH_PREMIERSHIP, RSS=8.6GiB)        | `05:06:23Z` (confirmed via `gcloud storage ls -L` on the heartbeat blob) | `05:26:25Z`               | ~20-21 min |
| `mtds-backfill-odds-smallchunk4-20260808`  | `2026-08-08T08:11:46Z` (mid-chunk-18, AUSTRIAN_BUNDESLIGA, RSS=24.4GiB)        | `08:11:31Z` (confirmed via `gcloud storage ls -L`)                       | `08:27:34Z`               | ~16 min    |
| `mtds-backfill-odds-smallchunk5-20260808`  | `2026-08-08T13:11:01Z` (mid-chunk-26, LA_LIGA, RSS=13.5GiB)                    | not separately checked this occurrence                                   | `13:28:05Z`               | ~17 min    |
| `mtds-backfill-odds-smallchunk8`           | `2026-08-08T21:12:37Z` (mid-chunk-26, LA_LIGA, `date=2020-10-09`, RSS=19.9GiB) | `21:13:15Z` (confirmed via `gcloud storage ls -L`)                       | `21:28:57Z`               | ~15-16 min |
| `mtds-backfill-odds-smallchunk10-20260809` | `2026-08-09T12:50Z` (mid-chunk-26)                                             | `~12:50Z` (confirmed silent alongside run.log)                           | `13:07:57Z`               | ~18 min    |
| `mtds-backfill-odds-smallchunk12-20260809` | `2026-08-09T17:43:08Z` (mid-chunk-18, RSS=15.9GiB)                             | `17:43:30Z` (confirmed via `gcloud storage ls -L`)                       | `18:02:08Z`               | ~19 min    |
| `mtds-backfill-odds-smallchunk13-20260809` | `2026-08-09T20:08:14Z` (mid-chunk-18, SERIE_A, RSS=17.8GiB)                    | `20:08:26Z` (confirmed via `gcloud storage ls -L`)                       | `20:26:02Z`               | ~17.6 min  |
| `mtds-backfill-odds-smallchunk14-20260809` | `2026-08-09T22:56:06Z` (mid-chunk-18, LIGUE_1, RSS=17.3GiB)                    | `22:56:26Z` (confirmed via `gcloud storage ls -L`)                       | `23:13:38Z`               | ~17.3 min  |
| `mtds-backfill-odds-smallchunk15-20260810` | `2026-08-10T01:11:36Z` (mid-chunk-18, EPL, RSS=22.8GiB)                        | `01:11:53Z` (confirmed via `gcloud storage ls -L`)                       | `01:27:22Z`               | ~15.5 min  |
| `mtds-backfill-odds-smallchunk16-20260810` | `2026-08-10T03:26:39Z` (mid-chunk-18, EPL, RSS=21.5GiB)                        | `03:27:19Z` (confirmed via `gcloud storage ls -L`)                       | `03:46:30Z`               | ~19.8 min  |
| `mtds-backfill-odds-smallchunk17-20260810` | `2026-08-10T05:53:55Z` (mid-chunk-8, EPL, RSS=10.2GiB)                         | `05:53:33Z` (confirmed via `gcloud storage ls -L`)                       | `06:14:41Z`               | ~20.8 min  |

**New pattern confirmation from occurrence 4**: this one died at **chunk 26**, not chunk 18 — the second time chunk 26
specifically has been the death site (smallchunk2 also died there), further weakening any "chunk 18 is special" framing.
Across 4 occurrences the death chunks are now 18, 18, 26, 26 — genuinely spread, not clustered on one chunk's content.
RSS at death (16.3, 8.6, 24.4, 13.5 GiB) still rules out a fixed-memory trigger. Silent gap remains tight (~16-21 min
across all four) — still the strongest evidence this is the watchdog's `HEARTBEAT_STALE_MINUTES` check firing on a
genuine, consistent-duration hang, not noise or a chunk-specific trigger. **Working hypothesis downgraded**: real-fetch
load correlation is weaker than it looked after 3 occurrences — `smallchunk5` also survived chunk 18's opening cleanly
(see Progress Log) AND cleared it entirely (1h31m, 24 OOM, zero hangs) before eventually hanging 8 chunks later at
chunk 26. This now looks more consistent with a **time-since-VM-boot or total-real-fetch-volume-accumulated** trigger (a
slow leak/resource exhaustion that isn't memory-shaped) than a per-chunk content trigger — `smallchunk5` ran ~5h27m
(08:09Z boot → 13:28Z death) before hanging, the longest-lived instance yet, consistent with something accumulating
across the VM's lifetime rather than resetting per-chunk.

All four delete operations' `principalEmail` = `1060025368044-compute@developer.gserviceaccount.com` — the shared
automation service account used by both the watchdog itself and every manual `gcloud` action in this workspace, so this
alone doesn't distinguish "watchdog" from "a human/session ran `gcloud compute instances delete` directly." The codex
rule cited in `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` (`Self-deleting VM/job` section) says a GRACEFUL
self-delete-on-exit writes a terminal `exit_code=` line to `run.log` before destroying itself — none of the four
occurrences has one, which rules out the VM's own normal completion-or-crash self-delete path. The consistent ~16-21
minute gap across four independent occurrences (different VM instances, different chunks, different real-fetch content,
different RSS) is the strongest evidence this is the **watchdog's heartbeat-staleness check**
(`HEARTBEAT_STALE_MINUTES`, default ~15-20 min per `vm_zombie_watchdog.py` / its AWS twin) firing on a genuine silence,
not coincidental unrelated events.

## What's confirmed

- **Not OOM.** None of the four deaths has a kernel OOM-kill message or an `exit=137` `CHUNK_FAILED` line — the last RSS
  reading across all four (16.3GiB, 8.6GiB, 24.4GiB, 13.5GiB) is at or below the ~28-31GiB range where this launcher's
  known OOM pattern (`mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`) actually triggers, and varies too widely
  across the four to be a fixed-threshold trigger.
- **Not a watchdog false-positive against a genuinely-alive VM** (the documented 2026-07-18 API-Football precedent) —
  the heartbeat blob itself (a separate GCS object from `run.log`, updated by a distinct mechanism) also stopped
  refreshing in the same window on `smallchunk3` and `smallchunk4`, so the underlying VM/process genuinely went silent,
  not just the watchdog's read of it.
- **No data loss in any occurrence** — manifest per-VM shard writes are durable and address-independent of which VM
  wrote them; a same-checkpoint relaunch (`RESUME_FORCE=false`) correctly skip-fasts through already-covered ground with
  zero re-fetching or re-billing.
- **All four occurrences were during real-fetch-heavy work**, not pure skip-fast dates — circumstantial, not proven, but
  worth noting as the search space narrows.
- **Relaunching remains empirically effective despite the unknown root cause**: `smallchunk5` (occurrence 4's
  predecessor-relaunch) was the longest-lived instance yet (~5h27m) and made the furthest net progress of any single VM
  (cleared chunk 18's danger zone AND reached chunk 26) before hanging — the relaunch strategy converges the 451-chunk
  backfill over time via durable per-VM-shard progress even though no single VM instance survives to finish it. This is
  why the decision each occurrence has been relaunch-and-document rather than pause — pausing would stop genuine forward
  progress on a non-blocking backfill without actually resolving anything.

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
- **[SCRIPT] P3. Extracted to `/plans/active/sports_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1 (2026-08-09,
  satellite-batch-extraction pass) — audit whether `market_tick_data_service`'s `odds_api` HTTP client calls have
  explicit connect/read timeouts, and add them if missing. Tracked there (`assigned_vm: planning`), not duplicated here;
  that batch's finalize sibling reconciles this checkbox once it lands.**
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

- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — fresh P1 incident doc (created today),
  3 open todos. Considered against today's IAM-self-service precedent (grant yourself a missing role rather than
  treating `PERMISSION_DENIED` as operator-gated): the IAP-tunnel-SSH gap this doc's own text flags is real and
  self-serviceable in principle, but self-servicing it does not make the WHOLE doc's remaining work bounded/
  deterministic — todo 1 ("next time this recurs, catch it before the silent window elapses") is an opportunistic
  catch-a-live-event task with no schedulable done-when, and todo 3 (threshold tuning) is explicitly gated in its own
  text on not knowing the root cause yet ("a threshold change... risks masking a real bug"). Todo 2 (audit whether the
  `odds_api` HTTP client has explicit connect/read timeouts) IS a bounded, mechanical code-audit and would be a good
  RECLASSIFY candidate on its own, but `assigned_vm` flips whole-doc only and the other 2 todos are genuine
  judgment/opportunistic-gated work — not splitting this doc's todos across two `assigned_vm` values in this pass. Doc
  stays NA.
- **2026-08-08T13:38Z (autonomous session, operator away) — FOURTH occurrence, `smallchunk5`.** Died at chunk 26 this
  time (not 18) — `LA_LIGA`, RSS=13.5GiB, last log line `13:11:01Z`, delete op `13:28:05Z` (~17 min gap, consistent with
  all prior occurrences). This was the longest-lived instance yet (~5h27m from boot) and the furthest net progress
  (cleared chunk 18 fully in 1h31m/24 OOM/zero hangs, then made it 8 more chunks to chunk 26 before hanging) — genuinely
  useful evidence the trigger correlates more with elapsed runtime/cumulative real-fetch volume than any specific
  chunk's content (downgraded the chunk-18-correlation hypothesis in the Timeline section above). **Explicitly
  reconsidered pause-vs-relaunch at this 4th occurrence** (per the standing guidance from earlier ticks to weigh this
  seriously): decided to relaunch, not pause — the relaunch strategy is empirically working (each instance makes real
  forward progress before eventually hanging, and durable per-VM manifest shards mean no progress is ever lost), and
  odds_api progress doesn't block FIXTURE_STATS or the AF campaign, so continuing costs nothing but VM-hours. Relaunched
  as **`mtds-backfill-odds-smallchunk6-20260808`** (guard passed, RUNNING, tarballs fresh). Still no working SSH access
  this session to catch a live hang — todo 1's blocker is unchanged.

- **2026-08-08T16:05Z — SELF-CORRECTION: killed `smallchunk6` prematurely, mistaking the documented normal OOM-retry
  pattern for a new failure mode.** At chunk 18 again, `smallchunk6` showed 14 explicit
  `CHUNK_FAILED ... exit=137 reason=OOM_KILLED` lines over 45 min, one per league, each followed by an automatic
  `mtds_chunk_loop.sh` retry with a fresh subprocess. I initially read this (without re-reading this doc's own Progress
  Log first) as a NEW, dangerous "infinite crash-retry loop" distinct from the tracked silent-hang bug, and killed the
  VM. **This was wrong** — the entry immediately above already documents `smallchunk5` clearing this exact same chunk
  via 24 OOM-kill+auto-retry cycles over 1h31m before succeeding and moving on ("24 OOM/zero hangs"). Explicit
  `CHUNK_FAILED`/`exit=137` messages with continuous fresh restart activity is the OOM-retry-until-success mechanism
  working as designed — it is NOT the bug this doc tracks. The tracked bug is specifically the switch to **total
  silence** (no `CHUNK_FAILED`, no restart, no message at all — see the Timeline's "no terminal exit_code, no Traceback,
  just silence" framing). Practically, no real progress was lost by killing it (OOM-kill+retry doesn't carry partial
  state across attempts regardless of VM identity, so a fresh VM redoing the same retry-until-success dance at chunk 18
  costs only the ~2-3min skip-fast re-walk through chunks 1-17, not a full restart of real work). Relaunched as
  `mtds-backfill-odds-smallchunk7-20260808` as a result — an unnecessary intervention that happened to be low-cost, not
  a harmful one. **Correcting course**: going forward, `CHUNK_FAILED`/`exit=137`/OOM-kill-with-immediate-restart is NOT
  actionable — treat it as expected, self-recovering background noise (consistent with the 14-24+ retry range now
  observed at chunk 18 across two separate VMs). Only intervene on the confirmed silent-hang signature: heartbeat/log
  activity genuinely stops (no restart, no error line) for >10-15 min while the VM is still RUNNING.

- **2026-08-08T16:40Z — unrelated but adjacent mistake caught on `smallchunk7`: wrong chunk size, not a hang.** The
  relaunch that created `smallchunk7` (previous entry) omitted `--chunk-size`/`CHUNK_SIZE`, so the launcher silently
  used its default (250 days) instead of the 5-day convention every prior `smallchunk*` VM used. Result:
  `CHUNK_FAILED chunk=1/10 range=2020-06-06→2021-02-10 exit=137 reason=OOM_KILLED` on its very first attempt, repeated
  5x in ~20min — a 250-day span OOMs almost immediately, unlike the 5-day chunks which get well into double-digit chunk
  counts before needing retries. Not a new instance of this doc's tracked bug (no silent hang occurred — logs stayed
  active with explicit `CHUNK_FAILED` lines throughout). Fixed by confirming `CHUNK_SIZE=5` against
  `smallchunk5`/`smallchunk6`'s `LAUNCH_PARAMS.json` and relaunching as `mtds-backfill-odds-smallchunk8` with it
  explicit. Noted here since it could otherwise be mistaken for a worsening of the hang pattern by a future reader
  diffing chunk-progress speed.

- **2026-08-08T22:25Z (autonomous session) — FIFTH occurrence, `smallchunk8`.** Had been clean through chunk 24 with
  zero new OOMs (last confirmed-healthy check 20:52Z). Found gone entirely at this tick's check (`instances describe` →
  not found). Diagnosed via `run.log` + heartbeat blob (not assumed from the delete op alone, per rule 4a): last real
  log line `21:12:37Z` (mid-chunk-26, LA_LIGA, `date=2020-10-09`, RSS=19.9GiB), heartbeat blob last updated `21:13:15Z`,
  delete op `21:28:57Z` — **~15-16 min silent gap**, matching the signature exactly (no `CHUNK_FAILED`, no error, no
  restart — genuinely different from the OOM-retry pattern documented above). Verified NOT a delete-op-timestamp
  misread: cross-checked both `run.log`'s own last timestamp and the separately-updated heartbeat blob, both agree.
  **Notable**: died at chunk 26, `date=2020-10-09` — the THIRD time chunk 26 specifically (and the second time this
  exact date) has been the death site, re-strengthening the per-chunk-content hypothesis that was downgraded after
  `smallchunk5` cleared chunk 26 cleanly once. Relaunched immediately as `mtds-backfill-odds-smallchunk9` with
  `CHUNK_SIZE=5` explicit (learned from the smallchunk7 misconfiguration — never trust the launcher default). Still no
  working SSH access this session to catch a live hang — todo 1's blocker unchanged.

- **satellite-batch-extraction 2026-08-09 (sports tranche)**: extracted todo 2 (`[SCRIPT] P3`, `odds_api` HTTP client
  connect/read-timeout audit+fix) into `/plans/active/sports_satellite_ao_dispatch_batch11_2026_08_09.md` todo 1
  (`assigned_vm: planning`) — this is exactly the split the 2026-08-08 `na-eligibility-audit` entry above flagged as a
  good standalone RECLASSIFY candidate but declined to split out unilaterally in that pass. Todo 1 (catch a live hang
  before the silent window elapses) and todo 4 (`PREFIX_IDLE_THRESHOLDS` tuning, explicitly gated on this audit's
  finding) remain open here, untouched — doc stays `assigned_vm: NA`.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **2026-08-09T05:39Z — discovered an AUTOMATED relaunch mechanism, and a naming-convention gotcha that destroys
  forensic evidence.** `smallchunk9` (which had been cleanly alive through a long chunk-26 OOM-retry stretch, 51
  `CHUNK_FAILED`, heartbeat confirmed live at 05:11Z) was gone by the next check. `gcloud compute operations list`
  showed: deleted `05:26:17Z` (within the monitoring gap), then a NEW same-named instance created `05:32:25Z` by
  **`unified-trading-sa@central-element-323112.iam.gserviceaccount.com`** — a different principal than the
  `1060025368044-compute@...` account used for every manual action and (per the earlier-established pattern) the
  zombie-watchdog's own kills. This confirms a genuine, previously-unobserved **automated SPOT-preemption relaunch**
  (`RelaunchPreemptedVm`, per the launcher's header comment) operates on this campaign — future occurrences may
  self-heal without manual intervention. **Cannot determine cause of death this time**: `smallchunk8`/`smallchunk9`'s
  no-timestamp-suffix naming convention means `run.log`/`WATCHDOG_TRACE.log` live at name-keyed GCS paths — the new
  instance's startup completely overwrote the old one's history, destroying the evidence needed to distinguish this from
  a genuine silent hang vs an ordinary SPOT preemption. **Not counted as a confirmed 6th occurrence** — genuinely
  inconclusive, unlike 1-5 which all had clean heartbeat-blob death evidence. **Recommendation for future relaunches in
  this campaign**: reintroduce a timestamp suffix (matching the original `smallchunk2-20260807` convention) so
  same-named auto-relaunches don't erase the evidence trail — this directly affects todo 1's feasibility (catching a
  live hang is moot if the evidence gets overwritten before anyone reads it).

- **2026-08-09T07:15Z — a GENUINELY NEW failure mode, distinct from both the silent-hang pattern above AND the OOM-retry
  pattern: `run.log`'s own GCS-tee upload can silently stall while every other liveness signal stays live.** The
  (auto-relaunched) `smallchunk9` from the entry above had its `run.log` GCS object frozen at `2026-08-09T05:59:53Z`
  (confirmed via direct `gcloud storage ls -L` object metadata, not just eyeballing content) — yet its
  **`WATCHDOG_TRACE.log`** (a separate GCS object, `mode=size` iterations tracking the LOCAL on-VM file's byte count)
  showed continuous growth up to `07:15:16Z`, essentially live, ~76 minutes AFTER `run.log` stopped updating. This means
  the underlying VM process was very likely still running (something kept writing to the local log file the watchdog
  measures) — but the **upload path** that streams that local file to the `run.log` GCS object
  (`vm-exec-with-gcs-tee.sh`, per the file's own name) had broken specifically. The heartbeat blob (a third, even
  simpler mechanism) also stayed live throughout. **This is a blind spot in every diagnostic this doc has established so
  far**: "trust the heartbeat blob over run.log text staleness" (established after occurrence-adjacent false alarms)
  assumed run.log lag was always cosmetic/short — but here NONE of the 3 remote signals (run.log content, heartbeat
  blob, watchdog trace) could distinguish "genuinely still making chunk progress, just blind to me" from "stuck in a
  loop that keeps writing local bytes without real progress" — chunk 1 already had 9 `CHUNK_FAILED` (unusually high for
  a chunk that isn't 18/26) before the run.log freeze, adding to the uncertainty. Without SSH access (todo 1's standing
  blocker), there was no way to resolve this remotely. **Decision: killed the VM rather than continue trusting an
  unverifiable signal** — same billing-waste-avoidance reasoning as the FIXTURE_LINEUPS quota-exhaustion kill.
  Relaunched as `mtds-backfill-odds-smallchunk10-20260809` (timestamp-suffixed, preserving forensic history this time).
  **New open question for whoever investigates todo 1 next**: is the `run.log` GCS-tee upload mechanism itself prone to
  silently dying independent of the main backfill process? If so, `run.log` freshness alone is an insufficient health
  signal — the watchdog's own trace log (or a similar local-size-based check) may need to become part of the standard
  diagnostic, not just heartbeat blob + run.log content.
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — re-verified the 2 remaining open todos. Todo 1
  ("catch it before the silent window elapses") is still a genuine opportunistic catch-a-live-event task with no
  schedulable done-when — even if IAP-SSH access were self-serviced (per today's IAM-self-service default theme), the
  task itself still can't be given a bounded worker "done when" (it only fires IF a hang happens to be caught mid-tick).
  The `PREFIX_IDLE_THRESHOLDS` todo remains explicitly self-gated on root cause, which is now if anything LESS settled
  than before (the 2026-08-09T07:15Z entry above found a genuinely NEW failure mode — the `run.log` GCS-tee upload
  silently stalling independent of the main process — that the existing silent-hang/OOM-retry taxonomy doesn't cover).
  No new extraction candidate surfaced this pass; batch11's already-extracted timeout-audit item is the one bounded
  piece and stays there. Doc stays `assigned_vm: NA`.

- **2026-08-09T13:08Z (autonomous session) — SIXTH occurrence, `smallchunk10`, CONFIRMED with the cleanest evidence
  yet.** All 3 signals (`run.log`, heartbeat blob, `WATCHDOG_TRACE.log`) went silent together ~12:50Z; VM deleted
  `13:07:57Z` (~18 min gap, by the standard `1060025368044-compute@...` account — matches the watchdog's own established
  pattern exactly). Unlike the `smallchunk9` incident above (auto-relaunched under a different principal, evidence
  overwritten, genuinely inconclusive), this is unambiguous: same-principal delete, clean 3-signal silence, consistent
  ~16-21 min gap. Died at chunk 26 again — the fourth time chunk 26 specifically has been the death site across 6
  occurrences (18, 18, 26, 26, 26, 26), now the stronger pattern rather than 18. Relaunched as
  `mtds-backfill-odds-smallchunk11-20260809` (timestamp-suffixed). **Relaunch friction this cycle**: the first relaunch
  attempt aborted pre-VM-creation on `ERROR: auto-republish completed but tarball(s) still stale ... deployment-service`
  (an unrelated concurrent session's dirty file in that checkout) — the wrapper still returned `exit_code=0`, which
  would have been silently trusted as success without reading the actual output content (per the no-fire-and-forget
  discipline). Left the odds fleet fully down (`gcloud compute instances list` returned zero `smallchunk1*` matches) for
  ~65 min until this was caught and the tarball staleness had cleared; re-triggered — genuine boot/health verification
  still pending as of this entry (not yet trusted on exit_code alone). FIXTURE_LINEUPS unaffected throughout, healthy,
  far advanced.

- **2026-08-09T15:39Z (`data_pipeline_failure` escalation, `agt-adfeaf`, DP_VM_STALL on `smallchunk10` — STALE alert, no
  action taken).** Dispatched with `RELAUNCH vm=mtds-backfill-odds-smallchunk10-20260809` per `rb_infra_relaunch.md`.
  Before relaunching, checked live state per the runbook's own "read the registry, don't guess" procedure:
  `DeploymentsRegistry` shows `smallchunk10` already terminal (`status=failed`, `exit_code=125`,
  `reap_reason=vm_not_running`, `completed_at=13:10:02Z`) — this is the SAME sixth-occurrence death the entry directly
  above already documents, not a new one. The fleet had already self-healed past it by the time this escalation ran:
  `smallchunk11` (the relaunch logged above) has itself since been superseded by **`smallchunk12`**, confirmed
  `status=running`, `last_heartbeat_at=2026-08-09T15:35:11Z` — only ~4 min stale against `date -u` at check time
  (`15:39:24Z`), i.e. healthy. This also **closes the "genuine boot/health verification still pending" gap the entry
  above flagged** — `smallchunk11`→`smallchunk12`'s lineage did boot and is making progress. Confirmed via `run.log`
  tail for `smallchunk10` that the death mechanism is unchanged from prior occurrences (continuous `PIPELINE_HEARTBEAT`
  - climbing `RESOURCE_SAMPLE` RSS through chunk 26, one in-loop `CHUNK_FAILED exit=137 OOM_KILLED` retry, then total
    silence at `12:48:49Z` — no new evidence for the open P1 root-cause investigation). **Action: none** — relaunching
    an already-archived, already-superseded VM name is a no-op; the correct current state (a healthy `smallchunk12`)
    already exists. Did not touch `smallchunk12` or the P1 root-cause work. This entry exists so a future reader of this
    escalation-triggered doc doesn't mistake the stale `smallchunk10` alert for a still-open gap.

- **2026-08-09T18:07Z (autonomous session) — SEVENTH occurrence, `smallchunk12`, clean 3-signal evidence, chunk 18
  again.** All 3 signals (run.log, heartbeat blob, `WATCHDOG_TRACE.log`) went silent together `17:43:08Z`-`17:43:30Z`;
  VM deleted `18:02:08Z` (~19 min gap, standard `1060025368044-compute@...` watchdog account — matches the established
  pattern exactly). Died mid-chunk-18, RSS=15.9GiB (not OOM range). Updated death-chunk tally: 18, 18, 26, 26, 26, 26,
  **18** — chunk 18 and chunk 26 are now essentially tied (3 vs 4) as the two recurring danger zones; no new evidence on
  root cause. Relaunched immediately as `mtds-backfill-odds-smallchunk13-20260809` (timestamp-suffixed) — confirmed
  genuinely booted (chunk 1/451, correctly skip-fasting through already-covered dates), not just exit_code=0. Separately
  this tick: FIXTURE_LINEUPS (`af-backfill-20260809-020527`) was SPOT-preempted (`compute.instances.preempted`, routine
  — NOT this doc's tracked hang pattern) at `18:02:52Z` and auto-relaunched by the fleet's own recovery mechanism as
  `af-backfill-20260809-180612` within ~4 min, confirmed genuinely resuming (real fixture-lineup fetches, no data loss).
  Both fleets healthy as of this entry. Todo 1's blocker (no working SSH to catch a live hang) remains unchanged.

- **2026-08-09T20:34Z (autonomous session) — EIGHTH occurrence, `smallchunk13`, clean 3-signal evidence, chunk 18 again
  — now the clear majority death site.** All 3 signals (run.log, heartbeat blob, `WATCHDOG_TRACE.log`) went silent
  together `20:08:14Z`-`20:08:26Z`; VM deleted `20:26:02Z` (~17.6 min gap, standard `1060025368044-compute@...` watchdog
  account — matches the established pattern exactly). Died mid-chunk-18, SERIE_A, after 3 prior OOM-retries this chunk
  (EPL, LA_LIGA, BUNDESLIGA — self-recovering, not the cause), RSS 17.8GiB (not OOM range). Updated death-chunk tally:
  18, 18, 26, 26, 26, 26, 18, **18** — chunk 18 is now the clear majority (4/8) over chunk 26 (4/8), tied but chunk 18
  hit in back-to-back occurrences (12, 13) — worth noting for whoever picks up the open root-cause investigation.
  Relaunched immediately as `mtds-backfill-odds-smallchunk14-20260809` (timestamp-suffixed) — confirmed genuinely
  created and RUNNING via the launcher's own output (tarball fresh, guard passed); boot-health verification via run.log
  pending as of this entry (background poll in progress, not yet trusted on exit_code alone). Todo 1's blocker (no
  working SSH to catch a live hang) remains unchanged.

- **2026-08-09T21:52Z (`data_pipeline_failure` escalation, `agt-adfeaf`, slot 4) — a THIRD independent dispatch for the
  SAME escalation id, and a distinct discovery: `smallchunk10` is a separately-stuck shard, not the main lineage.**
  Dispatched with `RELAUNCH vm=mtds-backfill-odds-smallchunk10-20260809` per `rb_infra_relaunch.md` — the same
  escalation `agt-adfeaf` already closed as a stale no-op at `2026-08-09T15:39Z` (entry above) AND separately picked up
  by another concurrent session (slot 5, see
  `/plans/active/issues/mtds_backfill_odds_smallchunk10_relaunch_budget_bug_and_oom_2026_08_09.md`), which found + fixed
  a real `vm_prefix()` budget-collision bug (`deployment-service@6e6f509f`) and diagnosed `smallchunk10` failing twice
  independently (07:53-13:10Z exit_code=125, 17:21-17:40Z exit_code=1 following an in-loop OOM) before deferring a 3rd
  relaunch to the operator. I had not yet read either doc when I recovered `LAUNCH_PARAMS.json`/`PROGRESS.json` directly
  from GCS (a process gap — should have grepped `plans/active/issues/` for `smallchunk10`/`DP-VM-003` FIRST per the
  pre-task conflict-check HARD RULE; the boot `CONTEXT` field's "Filed issue: (none)" was stale by the time I acted) and
  relaunched `smallchunk10` a 3rd time (`deployment_id=dd4eb45f-26cc-45ba-8ddc-ea6fee1856e9`, started `21:33:35Z`,
  checkpoint `start_date=2020-08-29` — identical to both prior attempts, confirming NONE of the 3 `smallchunk10`
  attempts has ever advanced past its own first real-fetch date). It hung with this doc's tracked silent-hang signature
  (not OOM) ~2 min into real work: `run.log` froze at `21:34:37Z` (5126 bytes, mid chunk-1 BUNDESLIGA processing, one
  `RESOURCE_SAMPLE` at `mem_pct=73.1% mem_slope=17.4` — a rising-memory sample, consistent with this doc's "something
  accumulating" hypothesis, but not yet OOM range), registry `last_heartbeat_at` froze at `21:35:37Z`, GCS-blob
  heartbeat froze at `21:35:17Z`, and periodic `gcloud` snap activity (heartbeat/upload sidecars) stopped entirely after
  `21:35:26Z` — all 3 signals silent together, matching the established pattern. Deleted the wedged instance at `21:50Z`
  after ~13 min of confirmed non-progress (no fire-and-forget) rather than let it sit wedged burning SPOT compute. **New
  finding: `smallchunk10`-the-name is a DISTINCT, stuck shard from the main productive lineage, not a 9th occurrence of
  the same campaign hanging** — `gcloud compute instances list` at `21:49Z` showed the real, actively-progressing
  frontier is `mtds-backfill-odds-smallchunk14-20260809` (the lineage this doc already tracks, smallchunk2→…→14),
  confirmed genuinely healthy (`last_heartbeat_at=21:49:35Z`, ~0s stale, steady CPU/mem/network activity across 10
  consecutive samples). All 3 of `smallchunk10`'s attempts across ~14 hours (07:53Z, 17:21Z, 21:33Z) restarted from the
  SAME `start_date=2020-08-29` checkpoint and died before advancing past it — it is not resuming forward progress the
  way the `smallchunk2→14` lineage does, it is repeating the same stuck chunk every time it's relaunched. **Recommend to
  whoever resolves the `[OPERATOR]` todo in the sibling budget-bug doc: consider a path C — `smallchunk10` may simply be
  abandoned (not relaunched again) rather than resized, since the main campaign is already covering the identical date
  range successfully via the `smallchunk2→14` lineage; a 4th relaunch of `smallchunk10` specifically would very
  plausibly repeat the same stuck-chunk-1 death.** Bumped the local
  `/tmp/uts_stalled_relaunch_budget/mtds-backfill-odds-.json` sentinel to `count=2` (today's cap) to block a reflexive
  4th auto-relaunch of this prefix today. Also flagging as a process observation (not chased further here): escalation
  `agt-adfeaf` has now been dispatched to at least 3 separate sessions (15:39Z entry above, slot 5's doc, this entry)
  for what appears to be the same underlying WARN finding — worth a look by whoever owns escalation dispatch/dedup if it
  recurs.

- **2026-08-09T23:19Z (autonomous session) — NINTH occurrence, `smallchunk14`, clean 3-signal evidence, chunk 18 yet
  again — now the overwhelming majority death site (5/9).** All 3 signals (run.log, heartbeat blob,
  `WATCHDOG_TRACE.log`) went silent together `22:56:06Z`-`22:56:26Z`; VM deleted `23:13:38Z` (~17.3 min gap, standard
  `1060025368044-compute@...` watchdog account — matches the established pattern exactly). Died mid-chunk-18, LIGUE_1,
  RSS 17.3GiB (not OOM range). Updated death-chunk tally: 18, 18, 26, 26, 26, 26, 18, 18, **18** — 5 of 9 occurrences
  now at chunk 18 vs 4 at chunk 26, a clear majority forming. Relaunched immediately as
  `mtds-backfill-odds-smallchunk15-20260810` (timestamp-suffixed, new date since this landed just past UTC midnight) —
  confirmed genuinely created and RUNNING via the launcher's own output (tarball fresh, guard passed); boot-health
  verification via run.log pending as of this entry (background poll in progress, not yet trusted on exit_code alone).
  Todo 1's blocker (no working SSH to catch a live hang) remains unchanged.

- **2026-08-10T01:28Z (autonomous session) — TENTH occurrence, `smallchunk15`, clean 3-signal evidence, chunk 18 yet
  again (6/10 now) — for the first time this session, the STOPPING transition was caught live before full deletion,
  confirming the watchdog kill mechanism goes through an intermediate STOPPING state.** All 3 signals (run.log,
  heartbeat blob, `WATCHDOG_TRACE.log`) went silent together `01:11:36Z`-`01:12:33Z`; a background poll caught the
  instance in `status=STOPPING` at `01:27:33Z` (first time observed live rather than post-mortem), fully gone by
  `01:28:47Z`; delete op confirms `23:13:38Z`→`01:27:22Z` timestamp, standard `1060025368044-compute@...` watchdog
  account, ~15.5 min gap — matches the established pattern. Died mid-chunk-18, EPL (the same league smallchunk13 died
  on), RSS 22.8GiB (not OOM range). Chunk 18 is now the clear majority death site at 6/10 occurrences vs 4/10 at
  chunk 26. Relaunched immediately as `mtds-backfill-odds-smallchunk16-20260810` (timestamp-suffixed) — confirmed
  genuinely created and RUNNING via the launcher's own output (tarball fresh, guard passed); boot-health verification
  via run.log pending as of this entry (background poll in progress, not yet trusted on exit_code alone). Todo 1's
  blocker (no working SSH to catch a live hang) remains unchanged — though the STOPPING-state catch above is a small
  step toward "catching it before it's gone," even without SSH access to diagnose the hang itself. **Separately
  discovered while diagnosing an apparent INJURIES census stall this same tick**: the sports manifest consolidator for
  this bucket showed a static `rows_out` across >=5 real merges spanning 1h+, plus a `error=locked`-only streak across a
  15min sample — filed as `sports_manifest_consolidator_static_rows_out_injuries_2026_08_10.md` (P1), NOT specific to
  this odds/hang investigation but noting here since it affects how future ticks should interpret any census reading
  taken during a similar stall window (cross-check a VM's own progress marker, don't trust the canonical census alone).

- **2026-08-10T03:46Z (autonomous session) — ELEVENTH occurrence, `smallchunk16`, clean 3-signal evidence, chunk 18 yet
  again — now 7/11 (a clear 2:1 majority over chunk 26's 4/11), and the LONGEST silent gap observed so far.** All 3
  signals (run.log, heartbeat blob, `WATCHDOG_TRACE.log`) went silent together `03:26:39Z`-`03:27:19Z`; caught live in
  `status=STOPPING` at `03:46:52Z` (second time this session catching the transition before full deletion); delete op
  confirms insert `03:46:30Z`, ~19.8min gap — the longest confirmed gap yet (prior max was ~20-21min for `smallchunk3`,
  this is within that same range but at the upper edge, not a new outlier). Died mid-chunk-18, EPL (the same league
  smallchunk13 and smallchunk15 both died on — EPL has now recurred at chunk-18 death 3 times, worth a look if it recurs
  again), RSS 21.5GiB (mid-range, not OOM). This occurrence was watched LIVE across 3 consecutive monitoring ticks
  (03:12Z healthy at chunk 16 → 03:31Z flagged as a developing watch item at ~4.5min silent, deliberately NOT relaunched
  preemptively since the signature wasn't yet confirmed → 03:46Z confirmed via STOPPING transition) rather than
  discovered post-mortem, the first time this session has tracked one occurrence end-to-end in real time. Relaunched
  immediately as `mtds-backfill-odds-smallchunk17-20260810` via
  `CLOUDSDK_CORE_ACCOUNT=1060025368044-compute@developer.gserviceaccount.com bash deployment-service/scripts/vm/launch-mtds-sports-odds-backfill-vm.sh --vm-name mtds-backfill-odds-smallchunk17-20260810`
  — guard confirmed `0 running + 1 planned = 1 <= cap 1` (smallchunk16 already fully gone from the singleton check by
  relaunch time), tarballs fresh, VM created and RUNNING. Boot-health verification via run.log pending as of this entry.
  Todo 1's blocker (no working SSH to catch a live hang) remains unchanged — though watching this one live across ticks
  confirms the STOPPING-catch from occurrence 10 wasn't a fluke; the watchdog kill mechanism reliably goes through an
  observable STOPPING state for a short window before full deletion.

- **2026-08-10T06:14Z (autonomous session) — TWELFTH occurrence, `smallchunk17`, clean 3-signal evidence, NEW death site
  (chunk 8) — first time NOT chunk 18 or chunk 26, weakening any remaining per-chunk-content correlation.** All 3
  signals (run.log, heartbeat blob, `WATCHDOG_TRACE.log`) went silent together `05:51:56Z`-`05:53:55Z`; delete op
  confirms insert `06:14:41Z`, ~20.8min gap — the longest confirmed gap yet (prior max was ~19.8min for `smallchunk16`),
  still within the established ~16-24min range. Died mid-chunk-8, EPL, date=2020-08-31, RSS=10.2GiB (well below OOM
  range, unremarkable). Updated death-chunk tally: 18×7, 26×4, **8×1** — the first occurrence at a chunk other than 18
  or 26 in this campaign's history, meaningfully weakening any lingering per-chunk-content correlation hypothesis
  (already downgraded once before after smallchunk5 cleared both 18 and 26 cleanly) in favor of the time-since-boot /
  accumulated-real-fetch-volume hypothesis, or possibly just a wide, non-deterministic distribution with no real
  per-chunk correlation at all. Relaunch attempt via the standard launcher command timed out at the harness's 120s
  foreground limit and moved to background (cause, confirmed from the completed task's output: a stale-tarball republish
  step, NOT a launcher hang) — relaunched as `mtds-backfill-odds-smallchunk18-20260810`, confirmed created and
  `RUNNING`; `run.log` boot-health still pending as of this entry, not yet trusted on VM-created/RUNNING alone. Todo 1's
  blocker (no working SSH to catch a live hang) remains unchanged.
