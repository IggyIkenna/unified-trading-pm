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
author: unknown
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
context_scope:
  [
    /plans/active/issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md,
    /plans/archive/2026_08/issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md,
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    market-tick-data-service/scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
  ]
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
      directly into the P2 todo below). **EXTRACTED → `cefi_satellite_ao_dispatch_batch20_2026_08_16.md`** (same
      live destination as the P2 todo below's open `[SCRIPT] P2` corpus-wide re-verify+relaunch todo; status: active;
      "settle 44/44, flip both target docs, delete the migration script" — subsumes this original 21-shard-relaunch
      recommendation now that later waves + shard 24's 2026-08-15 completion have moved the count forward; do not
      re-dispatch both).
- [ ] [SCRIPT] P2. BLOCKED-ON:cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31 (still
      open — slot-4 confirmed round-3 remains in flight, see below). **EXTRACTED `cefi_satellite_ao_dispatch_batch20_2026_08_16.md`**
      (2026-08-18, plan_reconciler, hedge-pointer confirmed): this exact todo (re-run the corpus-wide grep across all
      44 shards, flip both target docs, delete the migration script) is now the LIVE dispatchable copy at that plan's
      open `[SCRIPT] P2` todo ("Re-run the corpus-wide GCS
      VM-log grep (Script 1, cefi content-migration summary) across all 44 cefi-content-migration shards...") —
      neither this doc nor `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md`
      (its BLOCKED-ON target) previously reflected the extraction, so both still read as independently open. This
      line stays open here as the accounting record; the dispatchable copy lives in batch20 — do not re-dispatch
      both. Once relaunched shards complete, re-run this same
      corpus-wide `run.log` grep to confirm all 44/44 show the terminal summary, THEN delete
      `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` per its own `# Delete-when:` marker. Repo:
      market-tick-data-service. **2026-07-31T08:05Z (slot-15)**: re-ran grep (fleet empty, 392 objects) — 27/44 (was
      26), 17 shards remain: 13, 15-25, 40-44. Stays open. **13:04Z (slot-12)**: re-verified, IDENTICAL (27/44, same
      17). Detail split to `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md` (line
      cap). **13:24Z (slot-8)**: re-verified again, IDENTICAL (27/44, same 17, fleet still empty) — see split doc for
      full evidence. Genuinely blocked on relaunch round 3 (tracked as its own queued backlog task,
      `cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed-001`) — not flipping, not relaunching
      myself (out of this todo's scope). **~14:0xZ (slot-4)**: round 3 has since launched (13 of 17 relaunched, 4
      skipped on `RB-INFRA-RELAUNCH` budget, pending operator decision) — of those 13, 9 still running, 4 (19, 40,
      43, 44) already died/preempted again. Still not 44/44; still not flipping. Full detail in the split doc's Progress
      Log. **14:19Z (slot-4, re-check)**: same 9/13 still `RUNNING` with genuinely advancing `Progress:` counters (no
      new deaths, no stalls), same 8 shards still dead/not-relaunched. Still not 44/44; still not flipping. Full detail
      in the split doc's Progress Log.
- [x] [SCRIPT] P2. ✅ **Relaunch the 18 shards still incomplete after this session's wave** (13, 15, 16, 17, 18, 19, 20,
      21, 22, 23, 24, 25, 29, 40, 41, 42, 43, 44), now using the fixed tarball (`market-tick-data-service@9f4098b1`,
      merged 2026-07-30T18:04:44Z) which should clear the memory-leak freeze class that killed most of them. Recover
      each shard's exact `--start-date`/`--end-date` window from its own most-recent `run.log`'s `[vm-exec] starting:`
      line (same method as the original 2026-07-30 relaunch above — do NOT re-derive/guess), launch via
      `launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full` per the shard, SPOT default per HARD
      RULE. Note shard 29's specific "1 file remaining" freeze signature (Progress Log, 17:53Z entry) may need separate
      investigation if it recurs — flag rather than silently re-relaunching it a 3rd+ time if so. **No `[OPERATOR]` gate
      needed** for the same reason as the original P1 todo above (VM launches are AO-dispatchable by default). Repo:
      deployment-service (launch) + market-tick-data-service (verify). Done — see 2026-07-31T03:30Z Progress Log entry.
- [x] [BACKEND] P2. ✅ Cross-referenced with `cefi_content_migration_vm_wedged_worker_2026_07_23.md`'s Recommendation
      item 1. **Verified live**: `deployment-service/.../_gcs.py:809-819` `_PROGRESS_RE` already matches
      `would_patch`/`already_canonical_skipped`/`SCRIPT 1 CONTENT MIGRATION SUMMARY` (shipped
      `deployment-service@559ca9a` et al, DONE 2026-07-26). Added this doc's 21-dead-shard corroboration to that doc's
      item 1 directly — no further code change needed. — slot 11, 2026-07-31.
- [x] [SCRIPT] P2. ✅ Change `cefi-content-apply`'s default `MACHINE_TYPE` from `e2-standard-8` to `e2-standard-16` in
      `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` (the category-specific default, not the
      launcher's global default — other categories are unaffected). Confirmed root cause 2026-07-30: 3 independent
      shards (17, 18, 41) OOM-killed (`rc=137`, worker process killed while VM stayed alive, no preemption event) on
      `e2-standard-8` within the same 21-VM relaunch, at 3.6%-7.9% progress; all 3 ran clean to well past their prior
      death points after being individually relaunched on `e2-standard-16`. Likely cause: the script's in-memory
      catalogue load (`Loaded N catalogue rows from instruments-store-cefi-prd-...`) has grown since the category's
      original 2026-07-19 launch (11 days of continued live capture), pushing every shard closer to the 32GB ceiling.
      Repo: deployment-service. **Shipped `deployment-service@9e6004a`** (`agt-ad6632`, slot 11, 2026-07-31, DP-VM-003)
      — evidence in the split-out doc `cefi_content_migration_shard17_default_bump_2026_07_31.md` (this doc is at its
      line cap).
- [x] [BACKEND] P1. ✅ **Shard 16 died a 3rd time TODAY, this time neither SPOT-preempted nor OOM-killed on
      `e2-standard-8` — both causes this doc already fixed and confirmed** — root cause IDENTIFIED + fix SHIPPED
      (market-tick-data-service@9f4098b1, 2026-07-30, slot 2) — see "2026-07-30 root cause + fix shipped" note below.
      **Full-run verification against shard 14 is a SEPARATE follow-up todo below** (this scope — identify the
      mechanism + ship a fix — is genuinely complete; holding this slot for the multi-hour verification would repeat the
      exact monitoring-hostage pattern already flagged as an operator-escalation anti-pattern elsewhere in this same
      doc). Original evidence this todo was filed against: `canonical-migration-cefi-content-16-relaunch20260730-135500`
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
      shard-16 treatment (stop, leave to in-VM stall-kill, root-cause instead of relaunch). **FOURTH instance (slot-15,
      ~10 min later)**: shard 40 (`canonical-migration-cefi-content-40-relaunch20260730-132900`) — identical signature,
      heartbeat silent `14:15:49Z`, deleted `15:06-15:08Z` (~50min stale), froze at 23,000/76,685=30.0% progress.
      **Critical new observation: all 4 instances (16, 19, 40, 44) froze within a similar ~45-50 MINUTE elapsed-runtime
      window, regardless of shard size (63k-137k files) or date range** — this points toward a TIME-based resource leak
      (e.g. slot-7's PyArrow-pool-retention hypothesis accruing per-call, or a connection/handle leak), not a
      size/volume-based one. This is a strong, actionable diagnostic clue for the root-cause investigation — worth
      testing directly (does a deliberately small, fast-completing shard's canary run finish within the ~45min window
      before any other symptom appears, or does the same script hang at ~45min even on a trivially small input?).
      Relaunched shard 40 (1st genuine failure, within policy).
- [x] [SCRIPT] P1. ✅ **Verify the pyarrow-pool-release fix (market-tick-data-service@9f4098b1) against a full shard-14
      run** — VERIFIED. `canonical-migration-cefi-content-14-verify20260730-221322` (relaunched by slot-7 at `22:13:43Z`
      once the pre-fix VM naturally concluded) reached the terminal `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner at
      `2026-07-31T07:57:09Z`, `rc=0`, all 335,111/335,111 files processed, 0 errors, `STOP-ON-SURPRISE bounds: ok=True`,
      `bytes_allocated=0` at every periodic release throughout the run (no leak growth at any point) — 34,794s (~9.66h)
      elapsed, comfortably past the ~45-50min freeze window that killed the old code on shards 16/19/40/44. Fix is
      confirmed working. Evidence:
      `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-14-verify20260730-221322/run.log`.
      Repo: market-tick-data-service (verification only — no code iteration needed).
- [x] [BACKEND] P3. ✅ **Investigate what actually deleted
      `canonical-migration-cefi-content-19-relaunch20260730-130600`** — **VM self-deleted** via
      `VM_SHUTDOWN_ON_COMPLETION=true` mechanism in `vm-exec-with-gcs-tee.sh:444-472`. Root cause: the Python migration
      script was OOM-killed by the Linux kernel (`rc=137` = SIGKILL) at ~13:32Z after 23min of processing (7,600/153,655
      files, `bytes_read=34GB` on 32GB `e2-standard-8`). The `vm-exec-with-gcs-tee.sh` cleanup path detected the
      workload exit, wrote EXIT_STATUS, then fired `gcloud compute instances delete` from inside the VM — the GCE
      default compute SA (`1060025368044-compute@developer.gserviceaccount.com`) was the ambient credential used by the
      in-VM `gcloud` command. NOT the zombie watchdog: `is_zombie()` heartbeat/shard-staleness paths already ruled out
      (heartbeat fresh), `_reap_terminated_vms` targets only TERMINATED VMs, and `zombie_finished_not_shutdown` would
      have required a pre-existing EXIT_STATUS — the EXIT_STATUS was written by the cleanup sequence triggered by this
      same OOM kill. EXIT_STATUS=137 confirmed in GCS. Evidence: run.log tail shows `Killed ... rc=137` →
      `DEPLOYMENT_FAILED` → `VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete`. The OOM was the same
      `e2-standard-8` memory-exhaustion class later fixed by the `e2-standard-16` default bump
      (`deployment-service@9e6004a`, 2026-07-31) and the pyarrow-pool-release fix (`market-tick-data-service@9f4098b1`).
      Repo: deployment-service (investigation only, no code change).
- [x] [BACKEND] P2. ✅ **Investigate shard 16's fast-OOM anomaly in its date range (2024-08-20..2024-11-13)** — this is
      now its 2nd distinct OOM on `e2-standard-16` itself (03:41Z entry: 706s/3.4% before death; 2026-07-31 03:27-03:41Z
      entry below: also fast, ~14min, `mem_pct` jumping 20.0%→51.7% in a single ~1min sample). Both are far too fast for
      the slow pyarrow-pool-creep the shipped fix (`market-tick-data-service@9f4098b1`) targets — the diagnostic line
      confirms the fix IS firing on this shard, so this is a DIFFERENT, unaddressed failure mode, most likely a single
      anomalously large/malformed file early in this window causing a one-time in-memory spike. **Done when**: either
      the poison-pill file is identified + handled (streamed/chunked read, or a size-based skip-and-flag), or a 3rd
      clean relaunch on `e2-standard-16` completes past the point of this pattern recurring twice, confirming it was
      transient. **Budget note**: shard 16 has now used its full `RB-INFRA-RELAUNCH` `≤2/(vm-prefix,day)` allowance for
      2026-07-31 (1 dead attempt + 1 relaunch in flight) — do NOT relaunch a 3rd time today if this one also fails; page
      per the runbook instead. Repo: market-tick-data-service. **2026-07-31T04:02Z update**: the "single anomalously
      large/malformed file" hypothesis is now CONFIRMED for shard 23 (a 3rd shard hitting this same fast-OOM pattern) —
      its `run.log` shows an explicit
      `ERROR read failed .../venue=DERIBIT/instrument_type=perpetual/data_type=trades/XRP_USDC-26SEP25-4D6-C.parquet: Could not open Parquet input source '<Buffer>': Couldn't deserialize thrift: TProtocolException: Exceeded size limit`
      immediately before its OOM-kill. This is very likely the SAME mechanism killing shards 16 and 44 (no corresponding
      ERROR line survived in their truncated tails, but the fast/anomalous-spike signature matches exactly).
      **Recommended fix approach**: wrap the per-file `pd.read_parquet`/pyarrow open call in a try/except that catches
      `pyarrow.lib.ArrowInvalid`/thrift-deserialize errors, logs the specific file path, and SKIPS it (flagged for
      separate manual repair) rather than letting it propagate into whatever retry/buffer-growth path is causing the
      OOM. Repo: market-tick-data-service. **2026-08-01T08:15Z (slot-16)**: found the read-catch already existed
      (`except Exception` around `read_parquet_bytes`, confirmed firing live in shard 23's log) — the missing piece was
      that pyarrow's native memory pool never released the buffer allocated during the failed read attempt, so it
      accumulated toward the next 200-file checkpoint (or the OOM-killer, whichever came first) — matches shard 44's
      confirmed ~7x `bytes_allocated` spike immediately preceding its kill. **Shipped
      `market-tick-data-service@031a2b81`**: immediate `pa.default_memory_pool().release_unused()` at every per-file
      failure site (read failure, corrupt-file failure, and `run()`'s outer per-future exception handler) instead of
      waiting for the periodic checkpoint; also classifies thrift/`ArrowInvalid` size-limit errors as a distinct
      `corrupt_file_skipped` outcome (vs generic `read_error`) so poison-pill files are identifiable in the log for
      separate manual repair, surfaced in the STOP-ON-SURPRISE summary line. Verified: standalone unit-level smoke test
      (mocked `read_parquet_bytes` raising the exact confirmed thrift error) returns `corrupt_file_skipped` and fires
      the pool-release path; full `quality-gates.sh` green on this exact SHA (sentinel-verified). Live full-shard
      verification (does a relaunch on this fix clear shard 16's specific date range without recurring) is a separate
      follow-up, not blocking this todo's own scope (identify the mechanism + ship a fix, same completion bar this doc's
      `-006` root-cause todo used for the slow-creep mechanism above).
- [x] [SCRIPT] P1. ✅ **Fixed the wedge-detection defect behind failure mode (3) (the pre-fix silent-freeze pattern
      recurring despite `9f4098b1`)** — `market-tick-data-service@55d051bd` (`data_pipeline_failure` escalation
      `agt-3e0b8d`, slot 3, 2026-07-31, dispatched on the SAME shard-17/`-032349` freeze slot-15 flagged monitoring-only
      at 05:03Z above). Root cause: `run()`'s wedged-worker force-exit `hard_deadline` was `5s * total_files_discovered`
      — for shard 17's 157,497 files that evaluates to **~9.1 days**, so the safety valve meant to force-exit a stuck
      `ThreadPoolExecutor` pool never actually fires for any realistically-sized shard. This is orthogonal to the
      pyarrow-pool-release fix (which targets memory GROWTH) — it explains why a genuinely wedged thread (network hang,
      GIL contention, or an infinite retry loop against a corrupt file) still can't self-heal even with that fix
      applied: the deadline itself was defeated. Replaced it with a fixed 15-min time-since-last-progress STALL timeout
      (`_STALL_TIMEOUT_SEC = 900.0`), independent of corpus size. Verified shard 17 was still genuinely frozen (26+ min
      silent, incl. the always-on `PIPELINE_HEARTBEAT` line, which fires "regardless of whether the real workload is
      alive") before acting; deleted the wedged VM, republished the `mtds-code` tarball (was stale at `d74984b0`, now
      `55d051bd`), relaunched as `canonical-migration-cefi-content-17-relaunch20260731-050700` on the fixed tarball,
      confirmed `RUNNING` + heartbeat at T+40s. Registry-verified relaunch budget for this vm-prefix today (2026-07-31):
      the frozen `-032349` VM was itself the day's 1st relaunch (per the earlier 03:23Z/03:30Z batch entries) — this
      makes 2/2, within `RB-INFRA-RELAUNCH`'s bound but now exhausted for today; a 3rd death today should page rather
      than relaunch again. **Does NOT address failure modes (1) corrupt-file spike-OOM or (2) zero-allocation
      slow-timing-OOM** (both still open per the P2 todo above and the 04:18Z Progress Log entry) — this fix only
      shortens recovery time for a genuine wedge/freeze, it doesn't change what causes one. Repo:
      market-tick-data-service. Full diagnosis + PROGRESS/T+10min verification in the Progress Log below.
- [x] ✅ [OPERATOR] P0. **RESOLVED-MOOT (governance-sweep stale-tag cleanup, 2026-08-06).** The deadlock this todo
      describes (`-002` starving `-006` of the plan's one in-flight slot) no longer exists: `-006` (the P1 root-cause
      leak-investigation todo above) completed and shipped `market-tick-data-service@9f4098b1` (see the already-`[x]`
      "Shard 16 died a 3rd time" item above, and the "2026-07-30 root cause + fix shipped" Progress Log entry) — it was
      never actually starved to death, it dispatched and finished. The sibling doc
      (`cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31.md`, § "worker, slot 12,
      2026-07-31") independently confirms: "`-006` has since completed and shipped
      (`market-tick-data-service@9f4098b1`)... and this session's `-002` dispatch completed in under an hour without
      holding anyone up." No cancel/defer/split action was ever taken or needed — the condition self-resolved before an
      operator acted on it. Checkbox was never flipped; closing now as a bookkeeping correction, not a live decision.

## Progress Log

- Progress Log entries from 2026-07-26 (initial filing) through 2026-07-30T17:53Z (initial 21-shard relaunch, three
  SPOT-preemption waves, repeated `gcloud` identity poisoning, the `e2-standard-8` OOM class, the still-unresolved
  shard-19 delete mystery, the P0 dispatch-deadlock escalation) archived VERBATIM (no rewrite) to
  `/plans/archive/issues/cefi_content_migration_fleet_half_incomplete_progress_log_archive_2026_07_31.md` — parent doc
  line-cap management (slot-8, 2026-07-31T13:24Z), mirroring this doc's own established split-when-at-cap pattern.
  (Archived 2026-08-04 by na-eligibility-audit, cefi tranche — path updated from its pre-archive `plans/active/issues/`
  location.)

## 2026-07-30 root cause + fix shipped (slot 2, `cefi_content_migration_fleet_half_incomplete-006`)

Dispatched the P1 root-cause todo. Read `migrate_cefi_content_instrument_id_catalogue_2026_07_17.py` in full (610
lines). Confirmed pyarrow 23.0.1 is installed and pandas' default parquet engine (`pd.io.parquet.get_engine('auto')`)
resolves to `PyArrowImpl`, so every `pd.read_parquet`/`df.to_parquet` call in this script routes through pyarrow's
`default_memory_pool()` — measured `backend_name=mimalloc` on this fleet. **mimalloc is a well-documented case of
exactly the diagnostic signature already gathered here**: it caches freed native buffers for reuse instead of returning
them to the OS via `munmap`/`madvise`, so process RSS creeps upward across many small parquet read/write calls even
though pyarrow's own `bytes_allocated()` (the LOGICAL in-use count) stays bounded — this native- level caching is
invisible to Python's `gc` (it operates below the Python object layer entirely, so `gc.collect()` cannot reclaim it).
This matches this doc's own confirmed evidence precisely: deployment-registry `host_metrics_window.mem_pct` climbing
with a CONTINUOUSLY POSITIVE `mem_slope` across every freeze-class death (shard 16, 19, 40, 44, and the slot-2
escalation's own read of shard 19's `-150600` death: "70.2%→93.7%... never negative or flat") — a pattern that already
ruled OUT a one-time upfront allocation (the ThreadPoolExecutor futures dict, hypothesis already disconfirmed in this
doc) and pointed at hypothesis (a), PyArrow native buffer retention, as the most likely mechanism.
`pyarrow.default_memory_pool().release_unused()` (confirmed present on this pyarrow version) is the documented fix for
exactly this mimalloc/jemalloc RSS-creep class.

**Fix shipped**: `market-tick-data-service@9f4098b1`. Two changes: (1) a periodic
`pa.default_memory_pool().release_unused()` call on the same cadence as the existing progress log (every 200 files),
with a diagnostic log line reporting `bytes_allocated()` before each release; (2) `patch_instrument_id_column()` was
doing an unconditional `df.copy()` even when `changed == 0` — every caller discards that result unread in the no-op case
(`migrate_one_file`'s `already_canonical_skipped` early-return, `_verify`'s `changed == 0` check), so this was a wasted
per-file native-buffer allocation on the majority-outcome path for much of this corpus (adds pressure to the exact
mechanism the fix targets). Manually verified (mocked `resolve_tagged`, no GCS/live deps needed) that both the no-op
case (`out is df`, original untouched) and the changed case (`out is not df`, independent copy, original untouched)
preserve identical return semantics to before — no caller-visible behavior change. Full `quality-gates.sh` ran clean on
the FIRST attempt except two hard-fail STEPs from an unrelated, freshly-introduced regression in
`market_tick_data_service/live/websocket_runner.py` (a genuine, valuable data-loss fix from a concurrent commit pushed
it from exactly 900 to 916 lines) — verified pre-existing via a clean-tree stash test, declared repo- blocker
RB-608160be rather than touch that unfamiliar live-capture file, which resolved ~15 min later via an unrelated commit
(`ec86b995`, extracted the file back to 898 lines). Rebased cleanly onto that fix (disjoint files) and shipped via the
normal quickmerge flow once QG was fully green (2113+ tests, lint, basedpyright all clean).

**Verification status — genuinely NOT yet done, tracked as a separate follow-up todo below** (not this todo's scope): at
fix-ship time, the only live shard-14 VM (`canonical-migration-cefi-content-14-relaunch20260730-134900`) had been
running since 13:49Z — well before the fix landed (~18:20Z) — so it is running the OLD, unfixed code and its outcome
(success or failure) proves nothing about the fix. Did NOT kill it (alive, potentially still succeeding, no protective
purpose per RB-INFRA-RELAUNCH's own no-gratuitous-kill posture) — filed the actual verification (relaunch shard 14 fresh
once this VM naturally concludes, confirm it clears the ~45-50min freeze window and reaches the terminal summary on the
full 271,376-file scope) as its own dispatchable todo instead of holding this slot for the multi-hour wait, which would
repeat the exact monitoring-hostage anti-pattern the `-006`/`-002` dispatch-deadlock entry above already flagged as an
operator escalation. This todo's own scope (identify the mechanism + ship a fix) is complete; flipping its checkbox
accordingly.

## Progress Log (continued)

- **2026-07-30T19:15Z (slot-15)**: shard 26 (`-132900`) **genuinely COMPLETED** — full
  `SCRIPT 1 CONTENT MIGRATION SUMMARY` terminal banner, `rc=0`, all 143,281/143,281 files (115 patched, 0 errors). Ran
  20,779s (~5.77h) — notably longer than the ~45-50min freeze window that killed most other shards under the old code,
  though this VM was launched at `-132900` (13:29Z), before the fix landed (~18:20Z), so it can't be credited to the fix
  — it simply didn't hit the leak's tipping point this run. Second confirmed full success this session (after shard 28).
  Fleet at 2 shards (14, 42) once this self-delete completes. Also hit the `gcloud` identity-poisoning issue again
  (config-flip variant), fixed the same way.
- **2026-07-30T19:54Z (data_pipeline_failure escalation `agt-9bcc1c`, slot 4)**: dispatched via a DP-VM-003
  heartbeat-stall alert on `canonical-migration-cefi-content-42-relaunch20260730-152000`
  (`deployment_id=2fd61aeb-8762-4564-81fa-e3ba437d3a29`, per `rb_infra_relaunch.md`). Registry archive check found this
  is already the **5th relaunch attempt of shard 42 today** (archived: `-122417` exit_code=125/`vm_not_running`,
  `-130600` exit_code=125/`vm_not_running`, `-132600` exit_code=137/SIGKILL, `-143200` exit_code=137/SIGKILL; this one
  started `15:18:11Z`) — already far past both RB-INFRA-RELAUNCH's `≤2/(vm-prefix,day)` bound and this doc's own "3rd
  instance → stop, leave to in-VM stall-kill" policy (line ~178-180 above). **Did NOT relaunch a 6th time.**
  `run.log`/heartbeat/PIPELINE_HEARTBEAT all went silent together at `19:16:57Z`/`19:17:15Z` (last recorded
  `mem_pct=88.4%`) — the identical whole-VM-freeze signature this doc already diagnosed. Confirmed this VM was launched
  (`15:18:11Z`) **before** the fix landed (`market-tick-data-service@9f4098b1`, committed `18:04:44Z` same day,
  confirmed merged onto `origin/live-defi-rollout`) — so, same as shard 14's still-live pre-fix attempt noted above,
  this run cannot be credited to the fix and its outcome doesn't verify it either way. **New observation not yet in this
  doc**: as of `19:54:55Z` (~38min past last activity, ~8min past its own `STALL_TIMEOUT_SEC=1800` in-VM stall-kill
  deadline) GCE still reports `RUNNING` and neither `EXIT_STATUS` nor `STALL_BREADCRUMB` exist yet in
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-42-relaunch20260730-152000/`
  — the `STALL_PROGRESS_REGEX=progress:|files/sec` self-reap that killed shards 17/18/41/etc. on schedule has NOT yet
  fired here past its own deadline. Did not SSH in to investigate further (out of this one-shot escalation's scope);
  flagging as a possible second watchdog-timing gap worth a follow-up look if it recurs, but could equally just be a few
  more minutes of measurement lag — not asserting a firm diagnosis. **Recommendation**: once this VM is confirmed dead
  (self-reaped or naturally exits), shard 42 should get the SAME one-time fix-verification relaunch already queued for
  shard 14 above (fresh tarball pull = post-fix code) rather than being folded into the existing shard-14-only todo
  silently — posted a bounded `/blocked` question to main/operator per RB-INFRA-RELAUNCH's bound-exceeded escalation
  rule instead of deciding this alone.
- **2026-07-30T20:04Z (slot-15)**: confirming slot-4's flagged watchdog-timing gap resolved on its own — shard 42 now
  shows `STOPPING` in `gcloud compute instances list` (the delayed in-VM stall-kill fired, just later than its own
  deadline). Fleet down to 1 shard: 14 (the pre-fix run being tracked by the separate fix-verification todo). No action
  taken (monitoring-only, deferring the shard-42 fix-verification-relaunch recommendation to whoever owns that todo per
  slot-4's note above).
- **2026-07-30T22:06Z (slot-15)**: shard 14 (`-134900`) **genuinely COMPLETED** — full
  `SCRIPT 1 CONTENT MIGRATION SUMMARY` terminal banner, `rc=0`, all 335,111/335,111 files (this fleet's single LARGEST
  shard by file count), ran 29,633s (~8.23h). This run predates the fix (launched 13:49Z, fix landed ~18:20Z) so it
  can't be credited to the fix, same caveat as shards 26/28 — it simply never hit the leak's tipping point across this
  run. **The fleet is now fully empty (0 VMs running)** — every one of this session's 21 relaunches has now either
  completed or died. Per this todo's own done_definition ("once relaunched shards complete, re-run this same corpus-wide
  `run.log` grep"), re-ran the corpus-wide grep NOW rather than waiting further, since "relaunched shards complete" now
  literally holds (nothing left running): fetched all 363 `run.log` objects across
  `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-*/` (16-way parallel, same
  method as the original 2026-07-26 audit) and grepped each for the terminal summary banner. **Result: 26/44 shards now
  confirmed complete** (added 14, 26, 28 this session on top of the original 23: 01-12, 27, 30-39) — **18 shards still
  have NO attempt reaching the terminal summary**: 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 29, 40, 41, 42, 43,
  44 (a 45th directory, `canonical-migration-cefi-content-20260719-121302`, is the original unsharded pilot mentioned in
  this doc's own "What I found" section — not a numbered shard, excluded). **NOT yet 44/44 — this todo's done_definition
  is not met.** Per standing self-correction: not relaunching the 18 remaining shards myself. Real progress made (23→26,
  confirmed via direct evidence not assumption) but the corpus is still genuinely incomplete; the natural next action is
  a relaunch round of the 18 remaining shards using the now-fixed tarball (post-`market-tick-data-service@9f4098b1`),
  which should be dispatched as its own todo/decision rather than done by me unilaterally given the standing
  dispatch-deadlock/monitoring-hostage concerns already on record above.
- **2026-07-31T00:41Z (slot-15)**: **positive signal on the fix-verification todo** —
  `canonical-migration-cefi- content-14-verify20260730-221322` (a fresh shard-14 relaunch someone else dispatched,
  post-fix tarball) is now at 8632s elapsed (~2.4h), 76,800/335,111 files (22.9%) — well past the ~45-50min freeze
  window that killed nearly every pre-fix run this session. `run.log` shows the fix's new diagnostic line
  (`pyarrow pool release: bytes_allocated=X (before release_unused call)`) firing on the established every-200-files
  cadence, confirming the fix code is genuinely deployed and active on this run, not just merged. Not conclusive yet
  (needs to reach the terminal summary to fully verify), but this is the strongest direct evidence so far that the
  periodic-pool-release fix works. Monitoring-only, not touching this VM (it's the dedicated verification todo's run,
  not mine).
- **2026-07-31T03:56Z (`data_pipeline_failure` escalation `agt-c52482`, slot 10, DP-VM-001 `DP_VM_EXIT_NONZERO`)**:
  dispatched by the fleet monitor for `canonical-migration-cefi-content-16-relaunch20260731-032349` (`exit_code=137`,
  `deployment_id=51dc4590-72f2-4c5c-9f21-88875febcba0`) per `rb_infra_relaunch.md` — the SAME death slot-15 already
  logged above at `03:41Z` ("notable exception to the fix's otherwise-good track record"); the alert and slot-15's
  monitoring converged on the same VM, not a new event. Confirmed via `DeploymentsRegistry.host_metrics_window` this was
  a genuine, fast, accelerating memory spike, not a slow creep: `mem_pct` 13.6%→15.6%→16.8%→20.0%→**51.7%** across the
  last 5 samples (`mem_slope` jumping from ~1.0-1.3 to 4.54 on the final sample before death at `03:41:14Z`) —
  corroborates slot-15's "distinct cause... one-time spike" hypothesis over the pyarrow-creep mechanism the shipped fix
  targets. **Registry-verified relaunch budget for this vm-prefix TODAY (2026-07-31)**: only this one dead attempt on
  record (the 3 earlier `exit_code=125` attempts are from 2026-07-30, a different calendar day — budget resets daily per
  `RB-INFRA-RELAUNCH`) — 1/2 used, within bound. Relaunched shard 16 on the SAME `MACHINE_TYPE=e2-standard-16` /
  `--start-date 2024-08-20 --end-date 2024-11-13 full` config (matching slot-13's 03:30Z batch — this is genuinely a 2nd
  try at an already-correctly-sized machine, not a fresh escalation, since e2-standard-16 was already in use when it
  died) as `canonical-migration-cefi-content-16-relaunch20260731-035409`, verified `RUNNING` via
  `gcloud compute instances describe` at dispatch+~2min. This is now shard 16's 2nd relaunch today — budget exhausted;
  do **not** relaunch a 3rd time today if this one also dies (page instead, per the runbook). Added a tracked P2 todo
  above for the actual root-cause investigation (poison-pill file in this shard's date range) — genuinely out of this
  one-shot escalation's scope. Pinging the authoring fleet-monitor slot with this outcome; no code changed.
- **2026-07-31T03:23Z (slot-15)**: **relaunch-remaining-18 todo appears dispatched** — 4 new VMs appeared
  (`canonical-migration-cefi-content-{13,15,16,17}-relaunch20260731-032349`), all `RUNNING`, using the shared `-032349`
  launch-batch suffix (someone else's dispatch, not mine). These are 4 of the 18 shards this doc's corpus-wide re-verify
  (22:06Z entry) found still incomplete. Fleet now at 6 total (the 4 new + the ongoing shard-14 verify run).
  Monitoring-only — not launching the remaining 14, not touching these VMs. **Attribution note (added by slot-13 below):
  this WAS slot-13's own dispatch, mid-flight** — the first foreground launch batch (7/18 shards) hit the harness's
  2-min command timeout right as it finished shard 20, so at 03:23Z only 4-7 of the 18 had appeared yet; the remaining
  11 launched via a background batch immediately after, see the next entry for the full picture.
- **2026-07-31T03:30Z (slot-13, `cefi_content_migration_fleet_half_incomplete-009`)**: dispatched this todo (the
  18-shard relaunch on the fixed tarball). Pre-flight: `gcloud compute instances list` confirmed none of the 18 target
  shards had a live VM (only the pre-existing `canonical-migration-cefi-content-14-verify20260730-221322`
  fix-verification run was up), and `gcloud config get-value account` confirmed the active identity was the correct
  `unified-trading-sa@…` (no poisoning this time). Recovered each shard's exact `--start-date`/`--end-date` window from
  its own most-recent `run.log`'s `[vm-exec] starting:` line (18 separate `gcloud storage cat` reads, not re-derived) —
  all 18 windows matched this doc's own original 2026-07-30 table exactly, confirming no drift. Launched all 18 via
  `MACHINE_TYPE=e2-standard-16 VM_NAME_OVERRIDE=<name> bash launch-canonical-migration-vm.sh cefi-content-apply <start> <end> full`
  (SPOT default, no `ON_DEMAND`) — `e2-standard-16` chosen deliberately over the category's still-`e2-standard-8`
  default: this doc's own evidence already confirmed 3 independent `e2-standard-8` OOM deaths from the (separate,
  unrelated) catalogue-load-size growth issue, which the pyarrow-pool-release fix does NOT address, so launching on
  `e2-standard-8` would reintroduce an already-diagnosed failure class the fix was never meant to fix. Two launch
  batches (foreground hit the harness's 2-min timeout after 7/18; re-ran the remaining 11 in the background) — both
  batches' `gcloud compute instances create` calls returned exit=0 for all 18. **Verified via
  `gcloud compute instances list` (not fire-and-forget)**: all 18 —
  `canonical-migration-cefi-content-{13,15,16,17,18,19,20,21,22,23,24,25,29,40,41,42,43,44}-relaunch20260731- {032349|032606}`
  — confirmed `RUNNING` on `e2-standard-16`/`preemptible: true`. This todo's own scope (relaunch the 18 shards on the
  fixed tarball) is complete; ongoing health monitoring + the eventual corpus-wide re-verify grep are the separate P1
  (shard-14 fix-verification) and P2 (corpus-wide re-verify+delete) todos already tracked above, not duplicated here.
- **2026-07-31T03:41Z (slot-15) — notable exception to the fix's otherwise-good track record**: shard 16 (`-032349`,
  relaunched on the fixed tarball, `e2-standard-16`) OOM-killed (`rc=137`) very early — only 706s elapsed (~12min),
  5,400/157,328 files (3.4%). `run.log` confirms the fix's `pyarrow pool release` diagnostic WAS firing
  (`bytes_allocated` staying low, e.g. `172992` at the last release before death) — so this is NOT the same slow-creep
  mechanism the fix targets; it died far too fast and far too early for that pattern. Possible distinct cause: an
  anomalously large/malformed file early in this shard's date range (2024-08-20..2024-11-13) causing a one-time spike,
  unrelated to the periodic-leak fix. Contrast with the concurrent shard-14 verify run (same fix, same machine type, now
  past 4.7h/46% with zero issues) — the fix is clearly working in general, this looks like a shard-specific anomaly
  worth a closer look if it recurs on retry. No action taken (monitoring-only).
- **2026-07-31T03:57Z (slot-15)**: shard 44 (`-032606`) also OOM-killed (`rc=137`) early — 1465s (~24min), 11,800/80,026
  files (14.7%). **Different signature from shard 16**: `bytes_allocated` was actively RISING right before death
  (`41,878,784` → `274,933,504` across the last 3 release calls, ~7x growth in ~90s) rather than staying near-zero —
  this looks more consistent with the original slow-leak mechanism hitting a burst, not a one-off anomalous file.
  Possible read: the periodic release cadence (every 200 files) may not be tight enough for shards with unusually large
  individual files/batches. Fleet still at 19 (someone relaunched shard 16 separately, `-035409`, now `RUNNING`). No
  action taken (monitoring-only) — flagging both early-death shards (16, 44) together as worth the root-cause owner's
  attention if this pattern repeats across more shards.
- **2026-07-31T04:02Z (slot-15) — likely explains the early-death pattern**: shard 23 (`-032606`) also OOM-killed
  (`rc=137`) early — 1699.5s (~28min), 18,200/218,799 files (8.3%). Unlike 16/44, this one logged an explicit `ERROR`
  immediately before death:
  `read failed raw_tick_data/by_date/day=2025-09-15/.../venue=DERIBIT/instrument_type=perpetual/data_type=trades/ XRP_USDC-26SEP25-4D6-C.parquet: Could not open Parquet input source '<Buffer>': Couldn't deserialize thrift: TProtocolException: Exceeded size limit`.
  This is a genuinely CORRUPT/malformed parquet file (thrift metadata block exceeds pyarrow's size sanity-check), not a
  data-volume leak — and pyarrow's error-handling path for a corrupt file is a plausible mechanism for the OTHER two
  early deaths too (16, 44): a malformed file could cause an internal retry/buffer-growth loop before finally erroring,
  consistent with 44's observed `bytes_allocated` spike. **Recommendation for whoever owns further investigation**:
  check shards 16/23/44's date windows for other corrupt files via a targeted `pyarrow.parquet.ParquetFile()` open-only
  sanity pass (no full read) before the next relaunch attempt — a corrupt file will keep killing any relaunch regardless
  of the memory-leak fix. No action taken (monitoring-only); not attempting the file-corruption scan myself (out of
  scope for continued fleet monitoring).
- **2026-07-31T04:10Z (slot-15)**: shard 19 (`-032349`) is a 4th shard hitting this fast-OOM pattern — `rc=137` at 2435s
  (~40min), 19,000/153,655 files (12.4%). `bytes_allocated` jumped from `32,936,256` to `2,539,327,808` (~32MB → ~2.5GB)
  in a single release-cycle right before death — the largest single-step spike observed yet, further reinforcing the
  corrupt-file theory over the original slow-leak mechanism (no explicit `ERROR` line survived in the tail this time,
  but the magnitude/suddenness matches shard 23's confirmed-corrupt-file pattern, not a gradual creep). Fleet now (13,
  14-verify, 15, 17, 18, 20, 21, 22, 24, 25, 29, 40, 41, 42, 43) = 14 shards + the verify run. No action taken
  (monitoring-only).
- **2026-07-31T04:20Z (slot-7, `cefi_content_migration_fleet_half_incomplete-008`, this todo's own dispatched worker —
  attribution for the "someone else's dispatch" note in the 2026-07-31T00:41Z/03:23Z entries above)**: dispatched this
  P1 verification todo. The only live shard-14 VM at pickup
  (`canonical-migration-cefi-content-14-relaunch20260730-134900`) was running pre-fix code (launched 13:49Z, fix landed
  ~18:20Z) per this todo's own done-when — did NOT kill it (no gratuitous kill), instead launched a bounded background
  lifecycle monitor (`bash`, `run_in_background`, 5min poll, self-heartbeating to the orchestrator every cycle so the
  slot stays live without manual polling) that: (1) waited for that VM to naturally conclude, (2) relaunched shard 14
  fresh on the fixed tarball, (3) is now watching that fresh run for the terminal summary vs a stall. Timeline: old VM
  completed naturally at `22:06:07Z` (`exit_code=0`, full 335,111/335,111 — matches slot-15's `22:06Z` entry above, same
  VM, independently confirmed); relaunched fresh as `canonical-migration-cefi-content-14-verify20260730-221322` at
  `22:13:43Z` (T+60s confirmed `RUNNING` — the same VM slot-15's `00:41Z`/`03:41Z` entries above have been independently
  tracking as "someone else's dispatch"). **Confirmed crossing the ~45-50min old-code freeze window alive** at
  `22:55:10Z` (~45min elapsed, 22,400/335,111, 6.7%) — first direct evidence the fix clears the exact window that killed
  shards 16/19/40/44 under the old code. As of this entry (last poll `04:13:15Z`): still `RUNNING`, 190,000/335,111
  files (56.7%), steady ~9.0 files/sec, zero stalls/freezes across ~5.85h elapsed — well past the freeze window with no
  sign of the original slow-creep leak. **Not yet done**: this todo's "done when" requires the terminal
  `SCRIPT 1 CONTENT MIGRATION SUMMARY` banner on the full 335,111-file scope, which has not yet fired — leaving the
  checkbox unflipped. Checkpointing this entry now (session context approaching its compaction threshold) so the
  in-flight state survives independently of this session: **the VM itself
  (`canonical-migration-cefi-content-14-verify20260730-221322`) is the durable source of truth** — check
  `gcloud compute instances describe canonical-migration-cefi-content-14-verify20260730-221322 --zone=asia-northeast1-c`
  (NOTFOUND once it self-deletes) and
  `gcloud storage cat gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-content-14-verify20260730-221322/run.log`
  (grep for the terminal banner) directly — no dependency on this session's own background monitor script (a disposable,
  session-scratchpad polling wrapper around the same launcher, not committed) surviving. **Next action for whoever picks
  this up**: once that VM concludes (naturally or via its own `STALL_TIMEOUT_SEC=1800` self-reap), grep its final
  `run.log` for the terminal summary — SUCCESS ⇒ flip this todo's checkbox with the evidence line; STALL/freeze despite
  the fix ⇒ do NOT flip, instead revisit the periodic-release cadence (tighten below every-200-files) or hypothesis (c)
  (`--workers 12` oversubscription) per this todo's own text above. Separately: this session observed the parallel
  18-shard relaunch (todo `-009`, slot-13) hitting a DIFFERENT, seemingly corrupt-parquet-file early-death pattern
  (shards 16/23/44/19 per slot-15's 03:41Z-04:10Z entries above) — that is explicitly OUT OF SCOPE for this shard-14
  fix-verification todo (different shards, different failure signature, already flagged by slot-15 for the root-cause
  owner) and is not addressed here.
- **2026-07-31T04:18Z (slot-15) — a DIFFERENT death signature, possible second leak source**: shard 40 (`-032606`) also
  OOM-killed (`rc=137`), but this one does NOT fit the corrupt-file pattern — 2764s (~46min, matching the ORIGINAL
  ~45-50min freeze window this session's earliest diagnostics identified, not the fast 12-40min corrupt-file deaths),
  24,400/78,210 files (31.2%), and `bytes_allocated=0` at BOTH of the last two release calls before death (no spike at
  all, unlike 19/23/44). This suggests the periodic-release fix may only be PARTIALLY effective: it correctly tracks and
  releases pyarrow's own allocator pool, but if RSS is also growing somewhere the fix's `bytes_allocated()` check can't
  see (e.g. pandas-level object retention, `df.copy()` calls not fully captured by pyarrow's own accounting, or a
  different native allocator), the periodic release would show a healthy near-zero pool while the process still slowly
  OOMs at the original ~45-50min mark. **Flagging as a genuinely open question for the fix owner**: is there a second,
  non-pyarrow-pool leak source, or is this an unrelated one-off? Worth checking if this shard recurs at the same
  elapsed-time on a future attempt. No action taken (monitoring-only).
- **2026-07-31T04:18Z (`data_pipeline_failure` escalation `agt-c926ab`, slot 4, DP-VM-003 `DP_VM_STALL`)**: dispatched
  by the fleet monitor for `canonical-migration-cefi-content-41-relaunch20260731-032606` (heartbeat stale at dispatch).
  Confirmed genuine wedge, not just a stale heartbeat sample: `run.log` last progress line at `03:57:50Z` (13,000/77,941
  files, 16.7%, `bytes_allocated=415,329,600` — ~415MB — right before going silent, the same actively-rising-allocation
  signature as shards 44/19's fast-OOM deaths above, not a slow creep); `gcloud compute operations list` showed only the
  original `insert` op (no `compute.instances.preempted`), ruling out SPOT reclaim; GCE still reported `RUNNING`
  ~20.5min past last activity — neither the external zombie-watchdog nor the in-VM `STALL_PROGRESS_REGEX` self-kill
  (30min timeout, not yet due) had reaped it. **Registry-verified relaunch budget for this vm-prefix TODAY
  (2026-07-31)**: zero archived attempts (`DeploymentsRegistry.list_recent_archive` — the 4 archived `content-41`
  entries are all 2026-07-30) — this stalled VM was itself shard 41's only attempt today, so relaunching is squarely
  within `RB-INFRA-RELAUNCH`'s `≤2/(vm-prefix,day)` bound (this makes it the 1st genuine failure-triggered relaunch of
  the day for this shard). Read its `PROGRESS.json` checkpoint (`last_completed_date=2024-10-03, monotonic=true`) and,
  per the checkpoint-aware-resume HARD RULE, relaunched from `2024-10-04` (not a blind replay of the original
  `2024-09-30` start) — `MACHINE_TYPE=e2-standard-16` (matching the rest of this batch), SPOT default, same
  `cefi-content-apply` category, as `canonical-migration-cefi-content-41-relaunch20260731-042031`. **Verified, not
  fire-and-forget**: confirmed `RUNNING` at T+65s and polled until the first real progress line appeared — discovery
  completed in 40.4s (69,630 in-scope files across the narrowed 41-day window) and per-file migration progress
  (`Progress: 200/69630 files...`) is now emitting normally. Pinged the authoring fleet-monitor slot with this outcome;
  no `market-tick-data-service` code changed this session (relaunch + issue-doc update only).
- **2026-07-31T04:35Z (slot-15) — zero-`bytes_allocated` pattern now confirmed recurring, not a one-off**: shards 42 and
  22 (`-032606`, both) also OOM-killed (`rc=137`) with `bytes_allocated=0` at their last release call before death —
  shard 42 at 3763s (~62.7min, 28.1%), shard 22 at 3854s (~64.2min, 22.7%). Both fit the SAME pattern as shard 40 above
  (elapsed time well past the original ~45-50min diagnostic window, zero pool allocation at death, no spike). That's now
  **3 independent shards (40, 42, 22) showing the zero-allocation/slow-timing signature**, distinct from the **4 shards
  (16, 19, 23, 44) showing the corrupt-file/spike signature** — two genuinely separate failure modes surviving the fix,
  not one anomaly. Strengthens the open question raised in the 04:18Z entry: the periodic pyarrow-pool release may not
  be catching all memory growth. No action taken (monitoring-only).
- **2026-07-31T04:39Z (slot-15)**: shard 25 (`-032606`) is a 4th instance of the zero-`bytes_allocated`/slow-timing
  pattern — 3966s (~66min), 46,600/169,594 files (27.5%), `bytes_allocated=0` at last release. Tally now stands at 4
  shards (40, 42, 22, 25) for this signature vs 4 (16, 19, 23, 44) for the confirmed corrupt-file spike signature — a
  roughly even split across the 18-shard relaunch batch so far. No action taken (monitoring-only).
- **2026-07-31T05:03Z (slot-15) — a THIRD distinct signature reappears**: shard 17 (`-032349`) is genuinely frozen
  (silent, `run.log` `Update time` stuck at 04:18:20Z, ~45min stale at check time, `STOPPING` in `gcloud`), NOT an
  explicit `rc=137` kill — this is the original whole-VM-freeze pattern from this session's earliest diagnostics (no
  exit code, no OOM line, just goes silent), at 2989s (~49.8min elapsed, 19,400/157,497 files, 12.3%) — almost exactly
  the original ~45-50min freeze window this doc first identified before the fix shipped. Last `bytes_allocated` before
  going silent was `69,214,016` (~69MB, unremarkable). This is now a THIRD failure mode observed post-fix: (1)
  corrupt-file spike-OOM (16/19/23/44), (2) zero-allocation slow-timing OOM (40/42/22/25), and now (3) the pre-fix
  silent-freeze pattern recurring on at least one shard despite the fix. No action taken (monitoring-only) — will
  self-reap via the in-VM stall-kill per this doc's established pattern.
- **2026-07-31T05:10Z (slot-15) — a FOURTH distinct signature, genuinely non-memory-related**: shard 13 (`-032349`) died
  differently again — its `run.log` tail shows NO `rc=137`, no OOM, no silent freeze; instead explicit
  network-connectivity errors: `upload blocked >90.0s`, then `SSLEOFError` on a GCS upload, a 404 on its own
  deployment-manifest object, and finally
  `ERROR migrate failed .../venue=BYBIT/instrument_type=perpetual/data_type=book_snapshot_5/BYBIT:PERPETUAL:AXS-USDT@LIN.parquet: Connection reset by peer`.
  This looks like a genuine transient network blip on the VM/GCS side, unrelated to the script's own memory behavior —
  worth excluding from the memory-leak root-cause investigation entirely (it's an infra reliability issue, not a code
  issue). A fresh relaunch (`canonical-migration-cefi-content-apply-20260731- 051007`, no shard-number in the name — a
  different launcher naming convention, not mine) is already `RUNNING` (someone else's action). No action taken
  (monitoring-only).
- **2026-07-31T05:13Z (`data_pipeline_failure` escalation `agt-3e0b8d`, slot 3, DP-VM-003 `DP_VM_STALL`)**: dispatched
  by the fleet monitor for `canonical-migration-cefi-content-17-relaunch20260731-032349` (heartbeat 22min stale at
  dispatch) — the SAME failure-mode-(3) freeze slot-15 already flagged monitoring-only at 05:03Z above. Confirmed
  genuinely wedged before acting (26+ min fully silent, incl. `PIPELINE_HEARTBEAT`, at 19,400/157,497 files/12.3%,
  `run.log` object mtime frozen `04:18:20Z`; VM still `RUNNING`, not preempted). Root-caused it rather than just
  relaunching: `run()`'s `hard_deadline = 5s * total_files_discovered` evaluates to ~9.1 days for this shard's 157,497
  files, so the wedged-worker force-exit safety valve is defeated for any realistically-sized shard — independent of,
  and complementary to, the `9f4098b1` pyarrow-pool-release fix (that targets memory GROWTH; this is why a genuine wedge
  can still hang indefinitely even with that fix applied). **Fixed and shipped `market-tick-data-service@55d051bd`**:
  replaced the corpus-size-proportional deadline with a fixed 15-min time-since-last-progress `_STALL_TIMEOUT_SEC` —
  full diagnosis + todo checkbox above. Registry/day-budget check: the frozen `-032349` VM was itself today's 1st
  relaunch (03:23Z/03:30Z batch) — this action is the 2nd, exhausting today's `RB-INFRA-RELAUNCH` `≤2/(vm-prefix,day)`
  budget; a 3rd death today should page, not relaunch. Deleted the wedged VM, republished the `mtds-code` tarball (was
  stale at `d74984b0`, now pins `55d051bd`) — a first relaunch attempt without republishing would have deployed pre-fix
  code, silently defeating the whole point — then relaunched as
  `canonical-migration-cefi-content-17-relaunch20260731-050700` (same
  `RESUME_ASSET_GROUP=cefi-content-apply --start-date 2024-11-14 --end-date 2025-01-09 full`, SPOT default). **Verified,
  not fire-and-forget**: `RUNNING` + fresh heartbeat at T+40s; discovery phase scoped 89,904+ files within the first
  minute; first per-file `Progress: 200/157497 files` line confirmed at T+~4min via an armed background monitor, with
  the periodic pyarrow pool-release diagnostic firing normally (`bytes_allocated=61,239,168` at the next 200-file
  checkpoint) — both STARTED and PROGRESS checks per `rb_infra_relaunch.md` satisfied. Pinged the authoring
  fleet-monitor slot with this outcome.
- **2026-07-31T05:21Z (slot-15)**: shard 21 (`-032606`) is a 2nd instance of the same silent-freeze failure mode —
  `run.log` `Update time` frozen at 04:39:47Z (~42min stale at check time), no `rc=137`, at 4111s (~68.5min),
  32,000/159,027 files (20.1%), `bytes_allocated` near-zero throughout (not the OOM-spike pattern). Per slot-3's
  root-cause above (the `hard_deadline` scaling bug, now fixed in `market-tick-data-service@55d051bd`), this is almost
  certainly the SAME already-diagnosed-and-fixed bug, not a new mystery — this VM was launched (03:26Z, the `-032606`
  batch) before that fix shipped (~05:13Z), so it's running pre-fix code and was always going to hang indefinitely once
  wedged. No action taken myself (monitoring-only) — the correct remediation (delete + republish tarball + relaunch) is
  what slot-3 already did for shard 17; deferring to whoever picks up shard 21 next to do the same, and re-tagging my
  earlier "THIRD distinct failure mode" framing as RESOLVED/root-caused rather than open.
- **2026-07-31T05:20Z (`data_pipeline_failure` escalation `agt-1a06b5`, slot 2, DP-VM-003 `DP_VM_STALL`)**: dispatched
  by the fleet monitor for this exact VM (`canonical-migration-cefi-content-21-relaunch20260731-032606`, heartbeat 33min
  stale at dispatch) — this is the remediation slot-15's entry immediately above deferred to. Independently confirmed
  the same diagnosis before acting (genuine silent freeze, GCE `RUNNING`, ~11min past its own `STALL_PROGRESS_REGEX`
  30-min self-kill deadline which had not fired), plus one wrinkle worth flagging: the `DeploymentsRegistry` archive
  already carried this `deployment_id` (`c251e3f9`) as `status=failed`, `reap_reason=vm_not_running`,
  `completed_at=04:47:57Z` — 30+ min before I found it still genuinely `RUNNING` on GCE (single `insert` op only, no
  `preempted`/`delete` op; independent `vm-heartbeat/<vm>.txt` blob + `run.log` mtime both corroborate the freeze at
  `~04:39Z`, not a `04:48Z` reap). Did not trust the registry's stale/wrong verdict — cross-checked GCE + the heartbeat
  blob directly. Not filing a separate issue for this single mismatch (worth a look if `reap_stale()`'s
  `running_vm_names` check produces this false-positive again elsewhere). Fixed the recurring `gcloud` active-identity
  poisoning (`slot15-work` had drifted to `github-actions-deploy@…`; reset to `unified-trading-sa@…`, same as this doc's
  prior occurrences). **Registry-verified relaunch budget for this vm-prefix TODAY (2026-07-31)**: 1 prior dead attempt
  (`-032606` itself) — 1/2 used, within `RB-INFRA-RELAUNCH` bound; this is the 2nd and exhausts today's budget for shard
  21 — a 3rd death today should page, not relaunch. Deleted the wedged VM (protective — well past its own self-kill
  deadline, zero productive work, still billing), read its `PROGRESS.json` checkpoint
  (`last_completed_date=2025-05-13, monotonic=true`) and, per the checkpoint-aware-resume HARD RULE, relaunched from
  `2025-05-14` (not a blind replay of the original `2025-05-04` start; end unchanged `2025-06-26`) as
  `canonical-migration-cefi-content-21-relaunch20260731-052154` (`MACHINE_TYPE=e2-standard-16`, SPOT default). Confirmed
  the launch pulled the already-fixed `mtds-code@55d051bd` tarball fresh — slot-3's stall-timeout fix above had already
  republished it, so no separate republish was needed this time. **Verified, not fire-and-forget**: `RUNNING` confirmed
  at T+~15s; armed an 11-min bounded background monitor (`run_in_background`, self-heartbeating) rather than blocking
  synchronously — it confirmed genuine per-file `Progress: 1200/131776 files (11.5 files/sec, 104.7s elapsed)` at
  ~T+2min. Both STARTED and PROGRESS checks per `rb_infra_relaunch.md` satisfied. Pinged the authoring fleet-monitor
  slot with this outcome; no code changed this session (relaunch + issue-doc update only).
- **2026-07-31T05:22Z (`data_pipeline_failure` escalation `agt-5a8706`, slot 4, DP-VM-003)**: attributing the shard-13
  `-032349` relaunch (`canonical-migration-cefi-content-apply-20260731-051007`) slot-15 saw at `05:10Z` as "someone
  else" — that was me, checkpoint-resumed from `2026-01-18`, verified STARTED/PROGRESS. Root cause + a separate
  checkpoint-resume actuator bug fix (`deployment-service@b34e85a`) split into their own doc (this doc is near its line
  cap): `cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31.md`.
- **2026-07-31T05:58Z (`data_pipeline_failure` escalation `agt-e727b6`, slot 2, DP-VM-003)**: shard 41 (`-042031`), same
  silent-freeze wedge; checkpoint `monotonic=false` so resumed from its own original `2024-10-04` (not past the unsafe
  frontier) — 2nd relaunch today, within budget. 1st retry (`-054648`) preempted at 98s (unrelated); `-055259` verified
  STARTED+PROGRESS. gcloud active-identity poisoning recurred 2x this session — reset both times, no code changed.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- dropped the progress-log-archive doc, added the
  actual migration script + launcher (this doc's own context_scope had zero source-code paths despite being the primary
  write-up of a code-driven fleet failure).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **context-scout 2026-08-07 (batch11 independent re-verify)**: all 5 entries confirmed resolving on disk (2 sibling
  issue docs, the rb_infra_relaunch runbook, the migration script, the launcher); content unchanged.
- **2026-08-15T21:10Z (slot-3, review)**: Pointer, not a resolution of this doc's own still-open P1/P2 todos above.
  `cefi_content_migration_shard24_recurring_wedge_needs_diagnosis_2026_08_09.md` — the shard this doc's own history
  tracked as an ongoing holdout — now shows a confirmed clean completion (`EXIT_STATUS=0`, 52,519/52,519 files) as of
  2026-08-15T20:13:16Z, per `cefi_residual_ao_dispatch_2026_08_15.md`'s independently-verified todo 2. Did not re-run
  this doc's own corpus-wide 44-shard grep (out of scope for the task that surfaced this) — whoever picks up the P1/P2
  todos above should treat shard 24 as resolved and confirm the remaining count directly rather than assuming 44/44
  from this note alone.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) — re-verified all 5 entries resolve on
  disk and remain accurate; the 2026-08-15 shard-24-status pointer references a sibling doc that is independently
  context-scouted in its own right, not a new dependency here.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
