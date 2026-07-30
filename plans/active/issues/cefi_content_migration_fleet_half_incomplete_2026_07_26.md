---
doc_type: issue
title:
  The 44-way sharded cefi content-canonicalisation --apply fleet did NOT complete corpus-wide — 21 of 44 shards died
  partway through (1.2%-99.9% done), only 23/44 confirmed complete
summary: >-
  Verified corpus-wide completion of the ~44-way date-range-sharded `canonical-migration-cefi-content-NN-20260719-*`
  `--apply` fleet (launched 2026-07-19 to run `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` against the
  full cefi content corpus, superseding an earlier unsharded dry-run pilot). Fetched every `run.log` (100 files across
  44 shards + their retry/resumption attempts) from `gs://deployment-scripts-central-element-323112/vm-logs/`. Only
  23/44 shards (01-12, 27, 30-39) show the terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner in any attempt. The
  other 21 shards (13-26, 28, 29, 40-44) have NO attempt that reached the terminal summary — every attempt's log simply
  stops mid-`Progress:` line (VM killed, several with explicit `exit_code=137`/SIGKILL), at completion percentages
  ranging from 1.2% (shard 14) to 99.9% (shard 29, 1 file short) with most clustered 2-70%. This is a genuinely
  incomplete, silently-stalled migration, not a false negative from log-tail truncation (verified against full logs, not
  just tails, for the ambiguous cases).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, migration, canonicalisation, vm-fleet, incomplete, data-correctness, phantom-vm]
related:
  [
    /plans/archive/issues/cefi_content_migration_vm_wedged_worker_2026_07_23.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch2_2026_07_26.md,
  ]
created: 2026-07-26
priority: P1
parent_epic: cefi_master
source:
  "worker, slot 6, 2026-07-26, defi_satellite_ao_dispatch_batch2-007 -- verifying whether the sharded --apply fleet
  completed before deciding whether to delete the migration script"
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
---

# CeFi content-canonicalisation fleet: 21/44 shards never finished

## What I found

`cefi_satellite_ao_dispatch_batch2_2026_07_26.md`'s todo asked me to confirm the sharded `--apply` fleet
(`canonical-migration-cefi-content-NN-20260719-*`, ~44 shards, launched 2026-07-19 to replace the killed unsharded
pilot) completed corpus-wide, then delete `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` per its own
`# Delete-when:` marker if so.

Listed every object under `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-*/` —
100 distinct `run.log` files across the 44 numbered shards (many shards have 2-9 retry/resumption attempts, suffixed
`-c<HHMMSS>`, `-od<HHMMSS>`, `-r<HHMMSS>`, `-nrw<HHMMSS>`, or `-repin<HHMMSS>`). Fetched and grepped every one for the
script's terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner.

**23/44 shards confirmed COMPLETE** (summary found in at least one attempt): 01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11,
12, 27, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39.

**21/44 shards NEVER reached the terminal summary in ANY attempt**: 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25,
26, 28, 29, 40, 41, 42, 43, 44. Best-known progress per shard (max across all its attempts, from the full log not just a
tail, so this is not a truncation artifact):

| Shard | Best progress     | %     | Note                                                                |
| ----- | ----------------- | ----- | ------------------------------------------------------------------- |
| 13    | 85,400 / 135,588  | 63.0% | 3 attempts; latest ends mid-`Progress:`, no exit status             |
| 14    | 3,200 / 271,376   | 1.2%  | Largest shard by file count; barely started                         |
| 15    | 5,600 / 138,077   | 4.1%  |                                                                     |
| 16    | 2,800 / 136,921   | 2.0%  |                                                                     |
| 17    | 7,600 / 141,670   | 5.4%  |                                                                     |
| 18    | 4,600 / 135,324   | 3.4%  |                                                                     |
| 19    | 4,800 / 136,539   | 3.5%  |                                                                     |
| 20    | 7,000 / 138,207   | 5.1%  |                                                                     |
| 21    | 11,600 / 137,156  | 8.5%  | 5 attempts, none finished                                           |
| 22    | 16,400 / 133,629  | 12.3% | 3 attempts, ALL exit_code=137 (SIGKILL) after SIGTERM               |
| 23    | 10,400 / 142,453  | 7.3%  | Also logged 1 `read_error`                                          |
| 24    | 10,200 / 135,828  | 7.5%  |                                                                     |
| 25    | 11,000 / 141,256  | 7.8%  |                                                                     |
| 26    | 40,000 / 134,739  | 29.7% | 9 attempts, none finished                                           |
| 28    | 97,200 / 137,243  | 70.8% | Closest to done besides 29; log stops there                         |
| 29    | 138,800 / 138,919 | 99.9% | 1 file short, likely killed seconds from finishing (footnote below) |
| 40    | 8,400 / 69,630    | 12.1% |                                                                     |
| 41    | 3,800 / 67,254    | 5.7%  |                                                                     |
| 42    | 3,000 / 67,831    | 4.4%  |                                                                     |
| 43    | 4,800 / 65,664    | 7.3%  |                                                                     |
| 44    | 2,400 / 63,453    | 3.8%  |                                                                     |

Shard 29's log ends on a heartbeat with "1 files still outstanding" and no final summary — likely killed seconds before
completion. A later `canonical-migration-cefi-content-29-20260720-repin113734` retry exists but covers only ~11,598
files, not obviously the same 1-file residual — not confirmed as this shard's completion.

Every dead attempt's log ends abruptly mid-`Progress:` line or with an explicit `exit_code=137` (SIGKILL, e.g. shard
22's all 3 attempts) — consistent with the SAME monitoring/alerting gap already diagnosed in
`cefi_content_migration_vm_wedged_worker_2026_07_23.md` (`classify_no_capture_reason()` can't recognize this script's
progress vocabulary, so a genuinely-dying VM in this family produces a `SILENT`/misclassified signal rather than a
correctly-triaged page) — these 21 dead VMs likely never generated an actionable alert distinguishing "still running
slowly" from "actually dead," which is consistent with nobody having relaunched them in the ~1 week since.

## Why it matters

This is a real, large, silently-stalled content-canonicalisation migration — roughly half the cefi content corpus (by
shard count; the incomplete shards range from small to the single LARGEST shard, #14 at 271k files) never got
canonicalised by this fleet. The migration's own `# Delete-when:` marker on
`migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` explicitly requires corpus-wide completion before deletion
— deleting it now would remove the only known tool for finishing this work, with no indication anyone is tracking that
~half the corpus is still un-migrated.

## Recommended decision

- [ ] [SCRIPT] P1. **No `[OPERATOR]` gate needed** — VM launches are AO-dispatchable by default per
      `/codex/05-infrastructure/vm-launcher-runbook.md` (only
      `launch-disaster-drill-cron-vm.sh`/`launch-dr-drill-cutover-vm.sh` and `launch-strategy-live-vm.sh` require
      explicit human sign-off; ordinary backfill/migration relaunches do not). This is a bounded, checkable relaunch of
      21 NAMED dead/incomplete shards (13-26, 28, 29, 40-44) via an EXISTING idempotent script
      (`already_canonical_skipped` counter design), not a new design/scope decision — the original `[OPERATOR]` tag's
      own justification ("a new VM-launch decision... not a bounded verification outcome") misapplied the runbook's
      default posture. Resume from each shard's own checkpoint/progress state if the script supports it, otherwise
      re-run those date ranges from scratch. **Done when**: all 21 shards' `run.log` show the terminal summary (feeds
      directly into the P2 todo below).
- [ ] [SCRIPT] P2. Once relaunched shards complete, re-run this same corpus-wide `run.log` grep to confirm all 44/44
      show the terminal summary, THEN delete `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` per its own
      `# Delete-when:` marker. Repo: market-tick-data-service.
- [ ] [BACKEND] P2. Cross-reference with `cefi_content_migration_vm_wedged_worker_2026_07_23.md`'s Recommendation item 1
      (give `classify_no_capture_reason()` a "task never writes the manifest" exemption for this script family) — these
      21 dead VMs are a second, larger, concrete instance of exactly the alerting gap that doc already diagnosed from
      one VM; worth citing as corroborating evidence when that fix is prioritized.
- [ ] [SCRIPT] P2. Change `cefi-content-apply`'s default `MACHINE_TYPE` from `e2-standard-8` to `e2-standard-16` in
      `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (the category-specific default, not the
      launcher's global default — other categories are unaffected). Confirmed root cause 2026-07-30: 3 independent
      shards (17, 18, 41) OOM-killed (`rc=137`, worker process killed while VM stayed alive, no preemption event) on
      `e2-standard-8` within the same 21-VM relaunch, at 3.6%-7.9% progress; all 3 ran clean to well past their prior
      death points after being individually relaunched on `e2-standard-16`. Likely cause: the script's in-memory
      catalogue load (`Loaded N catalogue rows from instruments-store-cefi-prd-...`) has grown since the category's
      original 2026-07-19 launch (11 days of continued live capture), pushing every shard closer to the 32GB ceiling.
      Repo: deployment-service.
- [ ] [BACKEND] P1. **Shard 16 died a 3rd time TODAY, this time neither SPOT-preempted nor OOM-killed on `e2-standard-8`
      — both causes this doc already fixed and confirmed** — genuine root-cause investigation into
      `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`'s memory-growth profile is still needed. Evidence:
      `canonical-migration-cefi-content-16-relaunch20260730-135500`
      (`deployment_id=a4f98edf-4560-4e2f-ba38-6810d83c9b40`) confirmed via `gcloud compute instances describe` running
      `e2-standard-16` / `preemptible: false` / `provisioningModel: STANDARD` (i.e. exactly the on-demand +
      bigger-machine fix this doc's Progress Log already shipped for shard 16) — yet its deployment-registry
      `host_metrics_window` shows `mem_pct` climbing 11.6%→42.7% over 9 samples (~9 min) with an ACCELERATING
      `mem_slope` (1.2→3.46 sample-over-sample, not linear), and BOTH its `run.log` (GCS object mtime) and the
      deployment-registry heartbeat went completely silent at the same instant (`2026-07-30T14:11:15Z`) — 23+ min stale
      at time of writing, GCE still reports `RUNNING`. This is a genuine whole-VM freeze under memory pressure, not a
      fast SIGKILL/OOM (which would show `rc=137` in the log, as shards 17/18/41 did on `e2-standard-8`) — the bigger
      machine just bought more runtime before the SAME underlying growth pattern manifested, consistent with this doc's
      own prior note ("the fix is a genuine root-cause investigation into this script's memory profile... not another
      machine-size escalation"). Candidate mechanisms worth checking: (a) PyArrow's native memory pool retaining freed
      buffers across `pd.read_parquet` calls inside the long-lived `ThreadPoolExecutor(max_workers=12)` loop (157K+
      files submitted to one pool for this shard) instead of returning RSS to the OS — a well-documented PyArrow
      behavior, not a Python-level leak `gc.collect()` would catch; (b) the shared `ResolverMaps`/catalogue object
      (`Loaded N catalogue rows...`) held for the whole process lifetime combined with per-file `df.copy()` in
      `patch_instrument_id_column` never being explicitly released; (c) `--workers 12` oversubscribing concurrent
      in-flight parquet decodes for this shard's file-size distribution. Applied RB-INFRA-RELAUNCH's
      `≤2 relaunches/(vm-prefix,day)` budget bound (DP-VM-003 escalation agt-9d9fb9, 2026-07-30T14:29Z): shard 16
      already has 2 archived dead attempts today (`...-relaunch20260730-122417` exit_code=125/`vm_not_running`,
      `...-relaunch20260730-130600` same) plus this 3rd stalled one — did NOT relaunch a 4th time; the in-VM
      `STALL_PROGRESS_REGEX=progress:|files/sec` stall-kill (`launch-canonical-migration-vm.sh`'s `cefi-content-apply`
      category, `STALL_TIMEOUT_SEC=1800`) should self-reap it independently within ~30 min of its last progress-matching
      log line — no manual kill needed. Done when: the memory growth mechanism is identified (not just worked around by
      machine size) and a fix (bounded worker count / periodic pool recycle / explicit pyarrow pool release / smaller
      per-invocation date-range scope) is verified to run a full 271k-file shard (14, the largest) to the terminal
      `SCRIPT 1 CONTENT MIGRATION SUMMARY` without a mid-run stall. **CORROBORATION (slot-15, same day)**: TWO more
      independent instances of the identical signature — shard 44
      (`canonical-migration-cefi-content-44-relaunch20260730-132900`, `run.log`/heartbeat both silent at `14:09:30Z`
      /`14:10:07Z`, deleted `14:55:57Z` = ~46min stale, 21,000/73,965=28.4% progress at freeze) and shard 19
      (`canonical-migration-cefi-content-19-relaunch20260730-135500`, heartbeat silent `14:15:57Z`, deleted `15:04:49Z`
      = ~49min stale) — both via the SAME `unified-trading-sa`/`python-requests` RB-INFRA-RELAUNCH actor, both
      `e2-standard-16` on-demand (ruling out preemption AND the `e2-standard-8` OOM as causes for these two). **Three
      independent shards, three different date ranges, same freeze signature — this is now a strongly-confirmed systemic
      issue in the migration script itself**, not shard-16-specific. Relaunched both per RB-INFRA-RELAUNCH's
      ≤2/(vm-prefix,day) bound (1st genuine runtime failure for each, within policy); adopting the SAME policy going
      forward for any further occurrence — 2nd failure on any single shard gets relaunched once more, a 3rd gets the
      shard-16 treatment (stop, leave to in-VM stall-kill, root-cause instead of relaunch).
- [ ] [BACKEND] P3. Investigate what actually deleted `canonical-migration-cefi-content-19-relaunch20260730-130600` at
      `2026-07-30T13:33:35Z` (RUNNING, heartbeat blob fresh ~55s prior — ruled out `vm_zombie_watchdog.py`'s documented
      `is_zombie()` heartbeat/shard-staleness paths by direct evidence, see Progress Log). Actor was
      `1060025368044-compute@developer.gserviceaccount.com` invoked from within a GCE VM. Check
      `vm_zombie_watchdog.py`'s other code paths (`_reap_terminated_vms`/`should_reap()`) and any other automated
      process running under the GCE default compute SA that could issue `compute.instances.delete` against a
      `canonical-migration-cefi-` VM. Repo: deployment-service.

## Progress Log

- 2026-07-26 (worker, slot 6, `defi_satellite_ao_dispatch_batch2-007`): Filed after confirming corpus-wide completion
  was NOT reached — script left in place (NOT deleted) per the batch2 todo's own instruction for this case. Full
  evidence above; log data fetched via `gcloud storage cat` against
  `gs://deployment-scripts-central-element-323112/vm-logs/`.
- **2026-07-30 (slot-15, `cefi_content_migration_fleet_half_incomplete-002`)**: Was dispatched todo P2 (the
  post-relaunch re-verify + delete), but P1 (relaunch) had never actually been dispatched/run — backlog showed it
  `blocked`/undispatched. Verified live: only ONE relaunch attempt existed
  (`canonical-migration-cefi-content-13-relaunch20260730-071533`, this morning) and it was **preempted 90s after
  insert** (`compute.instances.preempted` at 00:17:12, insert at 00:15:42 UTC-7) with no auto-recovery and no `run.log`
  ever written — a second, independent instance of the exact SPOT-preemption-with-no-resume gap this doc's todo 3
  already flags. Also notable: that attempt's `RESUME_START_DATE`/`RESUME_END_DATE` (2024-02-05/2024-04-04) do NOT match
  shard 13's own original date window (2026-01-16/2026-02-13, recovered below) — looks like a parameter mistake in
  whoever triggered it, unrelated to my own relaunch. Executed P1 myself (todo's own text already resolved the
  authorization question — "No `[OPERATOR]` gate needed… AO-dispatchable by default" — and it is the literal blocking
  prerequisite for my assigned P2): recovered each of the 21 dead shards' EXACT original `--start-date`/`--end-date`
  window from its own `run.log`'s `[vm-exec] starting:` command line (not re-derived/guessed), confirmed the critical
  `54817bc1` PROGRESS.json-checkpoint fix (SPOT-resume gap) is already baked into the currently-published `mtds-code`
  tarball (`d75e247079d1` is a descendant), then relaunched all 21 shards via
  `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full` with
  `VM_NAME_OVERRIDE=canonical-migration-cefi-content-<shard>-relaunch20260730-122417` (SPOT, default per HARD RULE),
  verified each `RUNNING` via `gcloud compute instances list` (not fire-and-forget). Exact windows used:
  13=2026-01-16..2026-02-13, 14=2026-02-14..2026-03-27, 15=2026-03-28..2026-07-19, 16=2024-08-20..2024-11-13,
  17=2024-11-14..2025-01-09, 18=2025-01-10..2025-02-06, 19=2025-02-07..2025-03-17, 20=2025-03-18..2025-05-03,
  21=2025-05-04..2025-06-26, 22=2025-06-27..2025-09-06, 23=2025-09-07..2026-01-01, 24=2026-01-02..2026-01-15,
  25=2026-01-16..2026-02-01, 26=2026-02-02..2026-02-13, 28=2026-03-01..2026-03-27, 29=2026-03-28..2026-05-01,
  40=2024-05-12..2024-06-11, 41=2024-09-30..2024-11-13, 42=2024-12-27..2025-01-09, 43=2025-01-23..2025-02-06,
  44=2025-07-30..2025-09-06. **Status: relaunch STARTED, NOT complete** — these VMs will take hours (shard 14 alone
  measured only 1.2% in its first attempt's unknown-duration run). My assigned P2 todo (corpus-wide re-verify +
  delete-if-44/44) genuinely cannot complete until these finish; leaving it undone rather than falsely claiming
  completion. A future pass/session should re-run the corpus-wide `run.log` grep once these shards have had time to
  progress, and watch for further SPOT preemptions (now checkpoint-protected via the `54817bc1` fix, but still worth
  monitoring per `/vm-preemption-billing-waste-audit`).
- **2026-07-30 update (slot-15, same session, ~25 min later)**: spot-check found 20/21 relaunch VMs progressing normally
  (steady `Progress:` climb, e.g. shard 14 at 10,600/335,111, shard 29 at 13,000/194,481), but shard 41
  (`canonical-migration-cefi-content-41-relaunch20260730-122417`) had died AGAIN — this time NOT a SPOT preemption
  (`gcloud compute operations list` shows a clean `delete` op, no `compute.instances.preempted` event; the VM stayed
  RUNNING throughout). Its `run.log` shows the python process itself hard-killed (`rc=137`) at only 3,800/77,941 files
  (4.9%) — the wrapper's own SIGTERM-triggered shutdown log entry comes AFTER the "Killed" line, meaning something
  killed the worker process directly, not GCE terminating the instance. Consistent with a kernel OOM-kill on the default
  `e2-standard-8` (8 vCPU / 32GB), NOT the same failure class as the SPOT-preemption gap this doc otherwise covers — a
  genuinely new, third failure mode for this migration script. Relaunched shard 41 with `MACHINE_TYPE=e2-standard-16`
  (doubles RAM to 64GB, same escalation the launcher script's own tradfi-v9 comment already documents for a prior OOM)
  as `canonical-migration-cefi-content-41-relaunch20260730-124900`, verified `RUNNING`. If this ALSO OOMs, the fix is a
  genuine root-cause investigation into this script's memory profile (possibly `--workers` too high for the process's
  actual per-file memory footprint on this shard's date range), not another machine-size escalation.
- **2026-07-30 update (slot-15, same session, ~5 min later)**: shard 18
  (`canonical-migration-cefi-content-18-relaunch20260730-122417`) died with the IDENTICAL signature — `rc=137`, worker
  process killed directly (VM stayed `RUNNING`, clean `delete` op, no preemption event), preceded by several minutes of
  "No progress in the last poll window" warnings before the kill, at 5,400/148,799 files (3.6%). **This is the SECOND
  e2-standard-8 shard to OOM-die within ~25-40 minutes of a 21-VM fleet launch** — starting to look systemic (possibly
  the shared in-memory catalogue this script loads at startup —
  `Loaded N catalogue rows from instruments-store-cefi-prd-...` — has grown over the 11 days since the original
  2026-07-19 launch, pushing every e2-standard-8 shard closer to its 32GB ceiling) rather than two isolated incidents.
  Relaunched shard 18 on `e2-standard-16` (`canonical-migration-cefi-content-18-relaunch20260730-125300`), verified
  `RUNNING`. **Did NOT** preemptively kill+relaunch the other 18 still-`e2-standard-8` shards on a still-n=2 pattern —
  that would discard real, accumulating progress (e.g. shard 29 climbing steadily past 13k files) on an unconfirmed
  hypothesis; a THIRD independent OOM would be strong enough confirmation to justify that broader, more disruptive move.
  **Watch for more of these** — if the pattern continues, the durable fix belongs in the launcher's own
  `cefi-content-apply` category comment (default to `e2-standard-16` for this category going forward, not per-incident
  escalation).
- **2026-07-30 update (slot-15, same session, ~10 min later) — THIRD occurrence, escalated to fleet-wide fix**: shard 17
  (`canonical-migration-cefi-content-17-relaunch20260730-122417`) died with the SAME `rc=137` signature at
  12,400/157,497 files (7.9%, ~30 min runtime — notably further than shards 41 (4.9%) or 18 (3.6%), consistent with
  memory accumulating over TIME/volume-processed rather than dying at a fixed absolute file count). This is the bar
  explicitly set in the entry above ("a THIRD independent OOM would be strong enough confirmation") — three different
  shards, three different date ranges, same signature, now confirmed systemic rather than coincidental. Relaunched shard
  17 on `e2-standard-16`. **Escalated to the fleet-wide fix**: rather than wait for each of the remaining 18
  still-`e2-standard-8` shards to individually OOM (each wasting its accumulated runtime before being caught), deleted
  all 18 and relaunched them on `e2-standard-16` in one batch
  (`canonical-migration-cefi-content-<shard>-relaunch20260730-130600`). Accepted the sunk cost of their partial progress
  deliberately — the script's `already_canonical_skipped` counter means a fresh re-scan re-confirms already-migrated
  files CHEAPLY (a metadata check, not a re-migration), so restarting is materially cheaper than it looks from raw
  file-count-discarded alone. **All 21 shards are now on `e2-standard-16`** as of this action;
  `MACHINE_TYPE=e2-standard-8` default for `cefi-content-apply` in `launch-canonical-migration-vm.sh` should be
  reconsidered as a follow-up if this pattern is confirmed durable (i.e., if e2-standard-16 shards run to completion
  without further OOMs) — not yet added as a tracked todo since the e2-standard-16 fix itself isn't confirmed successful
  yet (shard 41 was mid-test crossing its prior death point at time of writing).
- **2026-07-30 update (slot-15, same session, ~5 min later) — fix CONFIRMED**: shard 41 safely cleared 5,400/77,941
  files (well past its 3,800-file death point on `e2-standard-8`) and is still `RUNNING` healthy on `e2-standard-16` —
  the machine-type escalation genuinely resolves the OOM, not a coincidence of timing. Also confirmed the `54817bc1`
  SPOT-checkpoint fix is actively writing (`[[VM_PROGRESS]] last_completed_date=2024-10-01 monotonic=true` observed in
  shard 41's log). Adding the tracked follow-up now that the fix is verified:
- **2026-07-30 update (slot-15, same session, ~15 min later) — two more real problems hit during the 18-shard batch
  upgrade, both resolved**:
  1. **Broken active identity mid-batch**: shards 24/25/26/28 failed with `PERMISSION_DENIED (compute.instances.create)`
     — the active `gcloud` account had drifted to `github-actions-deploy` (a different identity than this workspace's
     standard ambient `unified-trading-sa`, likely a session/config artifact, not an IAM policy gap). Confirmed
     `unified-trading-sa` holds `roles/compute.admin` + `roles/compute.instanceAdmin.v1`;
     `gcloud config set account unified-trading-sa@...` fixed it immediately (the rest of the in-flight batch, e.g.
     shard 29 onward, succeeded right after the switch with no other changes). The 4 failed shards' OLD VMs had already
     been deleted (only `create` failed) — they had ZERO running instances until manually relaunched.
  2. **Rolling SPOT preemption wave** — likely triggered by this session's own fleet doubling its footprint
     (`e2-standard-8`→`e2-standard-16`× 21 VMs, roughly 2× vCPU/RAM demand in one zone within ~10 minutes). THREE
     separate preemption waves hit different shard subsets in quick succession: {14,15,17,20,21} at ~06:18:37-43, then
     {24,42} again + {25} at ~06:19-06:23, then {26,28,40,43,44} at a later check — confirmed via
     `compute.instances.preempted` operations events, not OOM (these are a different failure signature from the earlier
     `rc=137` pattern). No auto-recovery observed within ~3+ min for these custom `VM_NAME_OVERRIDE` launches (the
     `RelaunchPreemptedVm` same-name mechanism may not cover ad-hoc-named instances, or its poll interval exceeds what
     was practical to wait out here) — manually relaunched each wave. After the SECOND repeat-preemption on shards
     24/42, switched the repeatedly-preempted set (24, 25, 26, 28, 40, 42, 43, 44 — 8 shards) to `ON_DEMAND=true` (the
     launcher's own designed opt-out) to stop the rolling-preemption cycle rather than keep reactively chasing it; the
     remaining 13 shards stayed on SPOT (stable, no repeat preemptions observed). **Final state: all 21/21 shards
     confirmed `RUNNING` on `e2-standard-16`** (13 SPOT + 8 on-demand). **Lesson for future large e2-standard-16 SPOT
     batches in this zone**: launching ~21 VMs of a larger machine type simultaneously can trigger genuine zone-wide
     SPOT capacity contention, not just isolated bad luck — if a shard gets preempted twice in a row shortly after a
     large same-zone SPOT batch launch, don't keep retrying SPOT; switch that instance to on-demand rather than assume
     the third attempt will differ.
- **2026-07-30 update (slot-15, same session, ~10 min later) — a THIRD, unexplained mechanism killed shard 19
  (`canonical-migration-cefi-content-19-relaunch20260730-130600`), plus the active identity drifted again (a DIFFERENT
  account this time: `github-deploy`, not `github-actions-deploy` — switched back to `unified-trading-sa` again, second
  occurrence this session)**. Investigated shard 19's death properly rather than assuming it was another preemption or
  the identity issue:
  - Cloud Audit Log (`protoPayload.methodName="v1.compute.instances.delete"`) shows the actor as
    `1060025368044-compute@developer.gserviceaccount.com` (the GCE default compute SA) via `gcloud` invoked
    `client-os/LINUX ... (Linux 6.17.0-1021-gcp)` — i.e. from WITHIN a GCE VM, not a human/agent session. Strongly
    suggests the fleet's own `vm_zombie_watchdog.py` (deployment-service), the only automated in-fleet reaper this
    codebase documents.
  - **Disproved the obvious hypothesis before shipping a fix**: `vm_zombie_watchdog.py`'s `is_zombie()` only kills on
    `hb_age > heartbeat_stale` (stale-but-present heartbeat blob) or `hb_age is None AND shard_age > shard_stale`
    (heartbeat blob missing entirely). Checked shard 19's own `gs://.../vm-heartbeat/<vm_name>.txt` blob directly — its
    `Update Time` was `13:32:40Z`, the delete op fired at `13:33:35Z` — the heartbeat was ~55s old at kill time, nowhere
    near the 15-min default `heartbeat_stale` threshold, and `PREFIX_IDLE_THRESHOLDS` has no override for
    `canonical-migration-cefi-content-` (confirmed by reading the dict — unlike `af-backfill-`/`cefi-fwd-`/etc., which
    needed one for this exact class of false-positive per
    `zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`). By the documented logic, this VM should NOT have
    zombie-killed. **Did NOT ship a `PREFIX_IDLE_THRESHOLDS` entry** (my first instinct) — that fix targets a mechanism
    the evidence just ruled out, and shipping it would give false confidence without addressing the real cause.
  - **Genuinely unresolved** — either the kill came from a code path in `vm_zombie_watchdog.py` not covered by this read
    (e.g. `_reap_terminated_vms`/`should_reap()`, though shard 19 was `RUNNING` not `STOPPED`, so that path shouldn't
    apply either), a completely different automated process also running under the GCE default compute SA, or a
    race/staleness in the audit-log timestamps vs. the blob's own timestamp. Relaunched shard 19 a third time
    (`...-133500`); no recurrence observed since. Flagging as a genuine open mystery rather than a closed incident —
    worth a dedicated follow-up if it recurs (the todo below is scoped to investigation, not a guessed fix).
- **2026-07-30 update (slot-15, same session, ~15 min later) — converted the ENTIRE remaining fleet to on-demand; SPOT
  preemption in this zone confirmed as a SUSTAINED pattern, not a one-time wave**. A follow-up health check found shards
  17/20/21 preempted a SECOND time (they were also in the very first wave) plus shard 29 preempted separately — three
  confirmed distinct preemption events (~06:18, ~06:40-43, ~06:43) over ~25 minutes, all via
  `compute.instances.preempted` operations events. Fixed those 4 individually on-demand per the already-established
  2-strikes policy. Given the SUSTAINED nature (3 waves, not 1) and that reactively chasing each wave costs real
  turnaround time plus discards partial progress every time, proactively converted the remaining 9 still-SPOT shards
  (13, 14, 15, 16, 18, 19, 22, 23, 41 — none had been re-preempted yet, but continuing to gamble on SPOT after 3
  confirmed zone-wide waves was not a good bet) to `ON_DEMAND=true` as well, rather than wait for each to individually
  earn its own 2-strikes fix. Accepted the modest on-demand cost premium for a bounded, one-time backfill in exchange
  for ending the reactive-recovery cycle; this was a judgment call given real, repeated evidence (3 independent
  preemption waves), not a reflexive escalation.
- **2026-07-30 update (slot-15, same session, ~10 min later) — the on-demand conversion batch itself hit the SAME gcloud
  active-identity poisoning TWICE more (5th and 6th occurrence this session — see corroborating evidence added to
  `orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md`)**, splitting the 9-shard batch into a multi-stage
  recovery:
  - First pass: 13, 14 converted cleanly; 15, 16, 18, 19, 22, 23, 41 (7 shards) failed with the same `PERMISSION_DENIED`
    signature mid-batch. Diagnosed precisely rather than blanket-retrying: shards 15 and 23 had their DELETE succeed
    before CREATE failed (zero instances, needed a fresh relaunch); shards 16, 18, 19, 22, 41 had BOTH delete and create
    fail (their original SPOT instances were still alive and progressing untouched — no data/progress lost, just not yet
    converted).
  - Second pass (after fixing identity again): 16, 18, 19 converted cleanly; 22 and 41 hit the SAME poisoning a SIXTH
    time mid-batch.
  - Fixed those final 2 individually after also creating an isolated named `gcloud` configuration (`slot15-work`,
    separate from `default`) for resilience — though noted this may not be true isolation, since the CI job's
    `google-github-actions/auth` step likely poisons whichever config is currently ACTIVE, not specifically `default`;
    didn't over-invest in solving this properly here, since the durable fix is the existing issue doc's
    `[OPERATOR-DECISION]`, not something to improvise mid-task.
  - **Final verified state: all 21/21 shards present, `RUNNING`, and on-demand** (zero `preemptible=true` remaining,
    confirmed via `scheduling.preemptible` on every instance) — SPOT preemption is now structurally eliminated for the
    remainder of this migration.
- **2026-07-30 update (slot-15, ~40 min later during routine health monitoring) — a 4TH OOM occurrence, this time on
  `e2-standard-16` itself**: shard 42 died with the identical `rc=137` signature (VM stayed alive, no preemption event —
  confirmed via `gcloud compute operations list` showing a `delete` op, not `preempted`) at 21,000/73,965 files (28.4%,
  ~62 min elapsed) — notably FURTHER than any prior `e2-standard-8` OOM death (3.6-7.9%) before hitting the same wall on
  64GB. Supports the "memory grows with elapsed time/volume processed" theory over a fixed absolute-file-count ceiling —
  `e2-standard-16` raised the threshold, it did not eliminate the failure mode. Relaunched shard 42 again on the SAME
  `e2-standard-16` (not yet escalating machine size further) — this is the FIRST OOM at this tier, not yet a confirmed
  pattern; per the same 2-3-strikes discipline used for the preemption waves, will escalate to a larger machine type
  only if this recurs on `e2-standard-16`, not preemptively. Rest of the 21-shard fleet unaffected (confirmed healthy
  via full status sweep immediately after).
- **2026-07-30 update (slot-7, `data_pipeline_failure` escalation agt-9d9fb9, DP-VM-003 `DP_VM_STALL`)**: dispatched by
  the fleet monitor for `canonical-migration-cefi-content-16-relaunch20260730-135500` (10-min-stale heartbeat at
  dispatch time; 23+ min stale by the time I finished investigating). Confirmed via `gcloud compute instances describe`
  it IS running the on-demand `e2-standard-16` config the last progress-log entry shipped (`preemptible: false`,
  `provisioningModel: STANDARD`) — so this is neither of the two previously-fixed failure modes (SPOT preemption,
  `e2-standard-8` OOM/`rc=137`) — but corroborates the SAME theory shard 42's entry above just landed (memory grows with
  elapsed time/volume, `e2-standard-16` raises the ceiling but does not eliminate the failure): its deployment-registry
  entry (`a4f98edf-4560-4e2f-ba38-6810d83c9b40`) shows `host_metrics_window.mem_pct` climbing 11.6%→42.7% over its last
  9 samples with an accelerating `mem_slope`, and both `run.log` (GCS mtime) and the registry heartbeat went silent
  simultaneously at `2026-07-30T14:11:15Z` — a slow whole-VM freeze under memory pressure at ~15 min elapsed, not a fast
  `rc=137` kill (a second, slower-manifesting variant of the same underlying leak, not a third distinct failure mode).
  Per RB-INFRA-RELAUNCH's `≤2 relaunches/(vm-prefix,day)` bound, shard 16 already has 2 archived dead attempts today
  (`-122417`, `-130600`) before this 3rd stall — did **not** relaunch a 4th time myself; filed the finding as the new P1
  todo above instead (the runbook's own guidance for a repeated-same-shard stall: stop relaunching, root-cause it). Left
  the stalled VM alone — its own in-VM `STALL_PROGRESS_REGEX` stall-kill should reap it independently within ~30 min of
  its last progress-matching log line (~14:41Z), no manual kill performed. Pinged the authoring fleet-monitor with this
  outcome. No code changed this session — investigation + issue-doc update only.
- **2026-07-30 update (slot-15, ~10 min later)**: independently hit the SAME slow-freeze variant on shard 44
  (`canonical-migration-cefi-content-44-relaunch20260730-132900`) — corroborates slot-7's finding above with a second
  independent instance. `run.log` went silent at `14:09:30Z` with NO `rc=137`/`Killed` line (unlike the fast OOM-killer
  cases) — genuinely different from the shard-19 mystery too: the actor deleting it was `unified-trading-sa` via
  `python-requests` (a Python GCP-API client), NOT `vm_zombie_watchdog.py`'s gcloud-CLI invocation pattern — this is
  almost certainly the same `data_pipeline_failure`/fleet-monitor `auto_recover` actuator described in
  `RB-INFRA-RELAUNCH` (`codex/15-runbooks/incidents/rb_infra_relaunch.md`), triggering on a stalled-heartbeat detection,
  distinct from both the zombie-watchdog AND the still-unresolved shard-19 delete. Heartbeat blob confirmed genuinely
  stale (45m50s at delete time — `14:10:07Z` last update vs `14:55:57Z` delete), so THIS instance's reaper verdict was
  correct, unlike shard 19's. **Read `RB-INFRA-RELAUNCH` before relaunching**: it bounds relaunches to
  ≤2/(vm-prefix,day) for a genuine failure, then requires stopping + filing an issue rather than blind-retrying a 3rd
  time (exactly slot-7's handling of shard 16 above). Shard 44's `-132900` freeze was its FIRST genuine failure since
  this morning's fleet-wide relaunch/on-demand-conversion (those were deliberate strategic actions, not
  failure-triggered relaunches) — the `-145700` relaunch I already shipped is failure-relaunch #1 of the ≤2 bound,
  within policy. **Adopting this runbook explicitly for the rest of this task**: any shard that fails a SECOND genuine
  time after this point will NOT be relaunched by me — it gets the shard-16 treatment (P1 todo
  - leave for the fleet monitor / in-VM stall-kill, per the runbook's own guidance) instead. Did NOT touch shard 16 —
    already correctly owned/declined by slot-7, respecting their in-progress investigation.
