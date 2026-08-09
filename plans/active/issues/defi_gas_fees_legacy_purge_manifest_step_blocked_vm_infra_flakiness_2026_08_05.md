---
doc_type: issue
title: gas_fees legacy-prefix purge — GCS objects 100% deleted, manifest purge blocked by VM-boot infra flakiness
summary: >-
  purge_gas_fees_legacy_venue_prefixes_2026_08_04.py's GCS-object-delete phase is CONFIRMED COMPLETE (0/10 target venues
  have remaining objects, independently verified twice via a direct 10-venue-wide match_glob check). The
  manifest-row-purge phase (drop the 12,425 now-orphaned manifest rows + force-consolidate) has NOT completed after 15
  VM-launch attempts across ~3 hours — 3 real IAM gaps were found+fixed+shipped along the way (all narrow, IaC-tracked
  grants), 2 safe SPOT preemptions happened mid-delete (no data risk, backups verified per-object), a discovery-phase
  reliability issue was fixed (added --skip-discovery-verified-empty since 0 objects remain makes discovery pure
  overhead), and the last 3 consecutive on-demand attempts died silently within ~20min with ZERO run.log ever uploaded —
  confirmed via serial console on one attempt to be a hung `gsutil` subprocess during early VM boot/setup (the
  launcher's own EXIT_STATUS-write-at-start step), not anything in this script. This looks like a real,
  currently-active, shared VM-launcher infra reliability issue, not a script bug — stopping further blind retries here;
  resumed the (never-touched) consolidator cron rather than leave DeFi-wide consolidation paused indefinitely for a
  stalled one-off task.
status: open
nature: issue
asset_group: [defi, infrastructure]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [gas_fees, gcs-delete, manifest-purge, vm-launcher, gsutil, infra-flakiness, gmx]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/archive/issues/defi_gas_fees_historical_venue_path_migration_2026_07_28.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: "2026-08-05"
author: interactive session (/autonomous)
priority: P1
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  ["defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md item 1, interactive session continuation, 2026-08-05"]
drift_direction: advance-code
context_scope:
  [
    market-tick-data-service/scripts/one_offs/purge_gas_fees_legacy_venue_prefixes_2026_08_04.py,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
    deployment-service/scripts/vm/vm_zombie_watchdog.py,
    deployment-service/scripts/vm/heartbeat_daemon.py,
    deployment-service/scripts/vm/lib/launcher_common.sh,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
  ]
---

# gas_fees legacy purge — object-delete done, manifest-purge blocked by infra flakiness

## What's actually done (verified, not claimed)

- **GCS object deletion: 100% COMPLETE.** Direct 10-venue-wide `match_glob` check
  (`raw_tick_data/by_date/day=*/**/venue={V}/chain={V}/instrument_type=spot_asset/data_type=gas_fees/**` for each of the
  10 `TARGET_VENUES`) returned **0 objects** across ALL venues, run twice independently (fresh each time, not cached).
  This is ground truth from GCS directly, not inferred from script logs. Every deleted object was backed up first
  (`_purge_backups/2026_08_04_gas_fees_legacy_venue_purge/`, size+crc32c-verified before delete) per the script's own
  safety protocol — confirmed via `gcloud storage ls` showing 6,000+ backup objects.
- **3 real IAM gaps found + fixed, all narrow/IaC-tracked, all shipped:**
  1. `uts-prd-sa` lacked `roles/iam.serviceAccountUser` on `uts-prd-sa` itself for the default compute SA caller —
     `deployment-service@c22d9200` (mirrors the honest-coverage fix's precedent, re-checked the sibling de-privileging
     plan first per that same reasoning).
  2. `uts-prd-sa`/`uts-test-sa`/`uts-migration-sa` lacked `roles/cloudscheduler.viewer` (needed for the script's own
     `_assert_consolidator_paused()` precondition check) — `deployment-service@9b5a718c`.
  3. `uts-prd-sa` lacked `roles/storage.legacyBucketReader` (bucket-METADATA read, distinct from object read — needed
     for `gcs_bucket_soft_delete_retention_seconds()`) on the tick-defi bucket — `deployment-service@612b2ea6`.
- **2 real code fixes, both shipped (dirty-deps carve-out — 2 pre-existing unrelated test failures on this tree each
  time, verified via `git stash` both times):**
  1. `market-tick-data-service@2f27d3d0` + `be5eda4b`: per-100-day discovery progress logging + reduced
     `--discover-workers` 16→4 (the 1881-day discovery scan was silent between start and finish, making genuine-but-slow
     progress indistinguishable from a hang to both this session's monitoring and the fleet zombie-watchdog).
  2. `market-tick-data-service@a201b16b` + `deployment-service@5f5ff2ec`: `--skip-discovery-verified-empty` flag +
     launcher wiring, since discovery was independently proven to always find 0 objects at this point — skips ~18,810
     now-redundant `list_blobs` calls entirely.
  3. `market-tick-data-service@6f98eae1`: added logging around the manifest-purge snapshot upload / serialize /
     new-index upload steps (also silent between the row-count confirmation and either success marker).

## What's NOT done

- **Manifest purge**: the 12,425 orphaned rows (matching the 3-part TARGET signature — see the script's own
  MANTLE-collision docstring warning) are still present in
  `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet`. `_purge_manifest_rows()` +
  the force-consolidate-restamp have never completed in any of 15 launch attempts.
- **Consolidator cron resumed** (`uts-prod-manifest-consolidator-market-data-defi-cron`, `asia-northeast1`) — it was
  paused for the entire session (correctly, per the script's own precondition), and since the manifest was NEVER
  actually mutated (still exactly 12,425 matching rows, unchanged throughout), there was nothing to protect by leaving
  it paused indefinitely while this session stops attempting further launches. Resumed 2026-08-05 rather than leave
  DeFi-wide manifest consolidation stalled for an unrelated stuck one-off task.

## The real blocker: VM-boot-level infra flakiness (NOT a script bug)

The last 3 consecutive on-demand launch attempts (`canonical-migration-defi-gas-fees-legacy-purge-`
`20260805-{135600,144329,150534}`) each ran for ~19-24 minutes then were deleted (by the compute default SA's own
identity — i.e. the fleet zombie-watchdog, `deployment-service/scripts/vm/` `vm_zombie_watchdog.py`, default 15min
heartbeat-staleness) with **zero `run.log` content ever uploaded** — not even the very first "Event logging initialized"
line the Python script always emits within its first ~1s. `get-serial-port-output` on the first of these (before it was
reaped) showed the task genuinely launched (`Task launched PID: 7474`, `=== VM setup complete ===`), then a
`snap.google-cloud-cli.gsutil-...scope` started and **never showed a "Deactivated successfully" line** before the
console output went quiet — consistent with a hung `gsutil` subprocess call during the launcher's own early
`echo "RUNNING" | gsutil -q cp - "$GCS_EXIT_URI"` marker write
(`deployment-service/scripts/vm/lib/launcher_common.sh:1169`), which happens as part of the shared
`vm-exec-with-gcs-tee.sh` wrapper BEFORE the Python task's own logging path is reached.

This is NOT scoped to this one-off script — `launcher_common.sh`/`vm-exec-with-gcs-tee.sh` are shared by every VM
launcher in this repo. If this `gsutil` hang is a currently-active, general reliability issue (vs. a one-off fluke that
happened to recur 3 times), it could silently be affecting OTHER VM launches too. Not confirmed either way — flagging as
the highest-priority open question.

## Todos

- [x] ✅ [DIAG] P1. **DID NOT RECUR 2026-08-06 — inconclusive, not fixed, but no longer the active blocker.** Two fresh
      launch attempts today (`canonical-migration-defi-gas-fees-legacy-purge-20260806-155449`, `-161030`) both booted
      cleanly with full `run.log` content from the very first line — the exact VM-boot-level silent-early-death pattern
      from 2026-08-05 did not reproduce. The raw unbounded `gsutil -q cp` call sites this todo flagged
      (`launcher_common.sh`'s `lc_log_upload_trap_block`, `vm-exec-with-gcs-tee.sh`) were NOT changed — this is a
      negative result (transient/cleared), not a fix. Left open as a real latent risk since the underlying
      unbounded-gsutil code is unchanged and could recur; not re-opening the active-investigation P1 given 2/2 fresh
      attempts were clean.
- [x] ✅ [DIAG]/[DATA] P1. **NEW root cause found + fixed 2026-08-06: genuine OOM, not boot flakiness.**
      `_purge_manifest_rows()` (`purge_gas_fees_legacy_venue_prefixes_2026_08_04.py:594`) does an unbounded, all-columns
      `pq.read_table(io.BytesIO(raw))` on the FULL canonical DeFi manifest — now 75,184,124 rows / 2.41 GiB compressed
      (confirmed via `gsutil du -h`) — the exact `allow_oversized_legacy_write`-guarded OOM signature class documented
      elsewhere in this workspace (`mtds_manifest_consolidator_inline_unbounded_memory_cli`, 639MiB→44.4GB), just not
      guarded in this one-off script. `canonical-migration-defi-gas-fees-legacy-purge-20260806-161030` (e2-standard-8,
      32GB) was SIGKILL'd (`rc=137`) within ~15s of the sanity-check log line, before `_purge_manifest_rows()`'s own
      first log line ever printed — confirming the crash happened during the initial full-table decode. Relaunched with
      `MACHINE_TYPE=e2-highmem-8` (64GB) — `canonical-migration-defi-gas-fees-legacy-purge-20260806-162248` got PAST the
      crash point cleanly (`[attempt 1] index generation=...: 12425 TARGET-signature row(s) (of 75184124 total)` —
      the exact line that never printed before). Machine-size fix confirmed effective for the OOM specifically (see next
      todo for what happened after).
- [x] ✅ [DIAG] P1. **ROOT-CAUSED + code-fixed 2026-08-06 by a separate (infra-craft) dispatch — CONFIRMED 2026-08-07,
      but the fix is DORMANT.** Candidate (a) — zombie-watchdog heartbeat-staleness miscalibration — is the confirmed
      cause, not (b). `deployment-service@0e94ceee1` (slot-4/planning, 2026-08-06T20:16:36Z) added
      `"canonical-migration-": (90.0, 360.0)` to `vm_zombie_watchdog.py`'s `PREFIX_IDLE_THRESHOLDS` (was falling through
      to the 15-min global default; the whole-index download+filter+serialize+upload+verify genuinely takes 30-60min)
      AND `STALL_TIMEOUT_SEC=7200` on the internal stall-watchdog in `launch-canonical-migration-vm.sh` (was 1800s
      default, and `STALL_PROGRESS_REGEX` never fires in full mode since `--skip-discovery-verified-empty` is always
      set). Both fixes verified present in the current `live-defi-rollout` checkout. `-162248`'s specific death (16-17
      min in) is inside the OLD 15-min-default window, so the external zombie-watchdog is the proximate killer for that
      run; the internal stall-watchdog's 1800s default hadn't yet elapsed. `heartbeat_daemon.py` is NOT the failing
      mechanism — correcting this doc's own framing: the purge script never calls it directly; it's an unrelated
      background sidecar writing to UTL's `DeploymentsRegistry`, a different store than the `vm-heartbeat/{vm}.txt` blob
      the zombie-watchdog actually reads (which is written by an untracked `vm_heartbeat_sidecar.sh`, not present in
      this repo). **BUT — same exact "fix shipped, daemon not relaunched" gap this workspace has hit before on this
      identical daemon** (`zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md` §"Incident 2 follow-up",
      2026-07-18): `launch-vm-zombie-watchdog.sh` uploads `vm_zombie_watchdog.py` to GCS and downloads it into
      `/tmp/watchdog.py` **once, at VM boot**, before entering its `while true` poll loop — confirmed via direct read of
      the launcher script, never re-fetched mid-loop. The currently-running daemon
      (`vm-zombie-watchdog-20260805-125558`, created 2026-08-05T07:26:02Z per `gcloud compute instances list`) booted
      **more than a day before** the 2026-08-06T20:16:36Z fix commit — confirmed via serial-console tail
      (`gcloud compute instances get-serial-port-output`) still actively polling every ~5min in real (non-dry-run) mode
      as of 2026-08-07T05:07Z ("watchdog complete: killed 0/0 zombies" — real-mode, just hasn't hit a
      `canonical-migration-` VM since booting). It is running the OLD `PREFIX_IDLE_THRESHOLDS` in memory — a fresh
      relaunch of the purge VM TODAY would almost certainly be reaped again by the stale 15-min default, reproducing
      this exact failure a 16th time. **Relaunching the watchdog daemon itself is explicitly OUT OF `data_engineering`
      craft scope** (this doc's own precedent, "Incident 2 follow-up": "killing/relaunching vm-zombie-watchdog-\* is a
      shared cross-cutting infra action (monitors the ENTIRE VM fleet, not just this task's backfill), outside
      data_engineering craft scope"; also `agents/data_engineering.md` STEP 0.5 `does_not: infra/VM launches (→ infra)`)
      — AND real-mode relaunches of this specific daemon have twice caused confirmed live-VM kills when done without
      extreme care (9 VMs on 2026-06-23; 3 more on 2026-07-18 via a then-latent `_blob_age_minutes()` bug, escalated to
      main at the time: "real-mode relaunch is a separate operator-gated decision, not part of this task"). **Not doing
      the relaunch myself** — filing as the blocking dependency for the [DATA] P1 relaunch todo below, same pattern as
      the 2026-07-18 precedent:
  - [x] ✅ [INFRA] P0. Relaunch the `vm-zombie-watchdog` daemon VM (`bash scripts/vm/launch-vm-zombie-watchdog.sh`,
        default real-mode; repo: deployment-service) so it picks up `deployment-service@0e94ceee1`'s
        `canonical-migration-` threshold — **DONE 2026-08-07**: relaunched as `vm-zombie-watchdog-20260807-075242`
        (created 2026-08-07T07:52:45Z, asia-northeast1-c), boot-clean; first real-mode poll at 08:02:58Z logged
        "Watchdog summary: 26 alive / 0 zombie / 3 too_young" → "watchdog complete: killed 0/0 zombies" +
        "terminated-reaper: reaped 0/0" — live fleet intact. Dry-run validated safe (2 clean cycles, zero reaps) BEFORE
        cutover; stale daemon `vm-zombie-watchdog-20260805-125558` deleted. Operator authorized the relaunch to main at
        2026-08-07T07:30Z; executed by main. Cited here + `zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`
        on close.
- [x] ✅ [DATA] P1. **DONE 2026-08-07 17:26Z — stale-check re-verified 2026-08-09.** The 09:17Z death of VM
      `canonical-migration-defi-gas-fees-legacy-purge-20260807-082535` (dispatch #7) described below was superseded the
      SAME day by a later, successful relaunch under the streaming-download fix (`market-tick-data-service@eb380b71b`):
      VM `canonical-migration-defi-gas-fees-legacy-purge-20260807-170630` completed the purge cleanly — manifest
      confirmed **0 of 12,425 TARGET rows remain** (index generation `1786119981126589`, read at 17:08:59Z, 0 matching
      of 75,665,201 total rows); GCS fresh-confirmed 0 objects across all 10 TARGET_VENUES at 17:26Z; consolidator cron
      re-ENABLED (`*/1 min`) and ran ≥17 clean post-resume `--verify-only` cycles since 17:08Z; heartbeat watcher cron
      resumed 17:26Z. Closed and cited (with full evidence) by `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s
      `[DIAG] P1` + `[INFRA] P0` todos (`defi_satellite_ao_dispatch_batch9-018`, infra slot 5) — this doc's own checkbox
      was simply never flipped to match. **Original (superseded) 09:17Z-death account, kept for the record:** dispatch
      #7 (`data_engineering`, slot 10): VM `canonical-migration-defi-gas-fees-legacy-purge-20260807-082535` (launched by
      infra dispatch #6) booted cleanly but DIED at ~09:17Z (47 min in) without completing — no EXIT_STATUS written,
      manifest NOT modified (still from 2026-08-06). Root cause: `_download_index_chunked()`'s range-request approach
      (20 × 128 MiB chunks × 300s timeout each, 3 outer retry attempts) hung on the 3RD consecutive 2.46 GiB download
      inside `_purge_manifest_rows()`. The first 2 downloads (`_days_with_legacy_gas_fees()` at 08:29:14Z +
      `_assert_sane_target_row_count()` at 08:29:37Z) both completed in ~20s; the 3rd hung for 47 min until timeout
      budget exhausted. `_download_index_chunked()` was designed for operator's local-network 256 MiB proxy cutoff (see
      its own comment) — not for GCS VMs where a single streaming response is more robust. Code fix shipped:
      `market-tick-data-service@eb380b71b` — `_purge_manifest_rows()` now uses `blob.download_as_bytes(timeout=900)`
      (single streaming response via `_raw_client()`) instead of `_download_index_chunked()` (range-request chunks) —
      this is the exact fix that made the later `-170630` relaunch succeed.
- [ ] [DATA] P2. Update `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 1 once the manifest purge
      actually completes (its current entry cites a different, never-committed script name
      `delete_legacy_gas_fees_venue_2026_08_04.py` with different numbers — likely stale/abandoned WIP from an earlier,
      since-lost session; this doc's script + numbers are the real, shipped, adversarially-reviewed lineage).

## Progress Log

- **na-eligibility-audit 2026-08-09** (infra tranche) [body-hash:b72408acd156806a]: KEEP-NA, valid — the `[DATA] P1`
  relaunch item is `[x]` (see stale-check entry below). Sole remaining item (`[DATA] P2`, update the sibling defi-domain
  doc's numbers) reads as bounded but is flagged `MISCLASSIFIED_LIKELY_AO_ELIGIBLE` rather than RECLASSIFYed outright —
  doc is dual-tagged `[defi, infrastructure]` and ownership (infra vs. defi tranche) should be settled before promoting;
  not actioned this run.
- **stale-check re-verify 2026-08-09 (infra tranche, KEEP-NA staleness re-check)**: the `[DATA] P1` relaunch todo was
  flipped `[x]` — genuinely done since **2026-08-07 17:26Z**, three separate na-eligibility-audit passes (08-07) never
  caught it because the doc's own text described only the intermediate 09:17Z dispatch-#7 failure, not the later
  same-day successful relaunch. Verified by reading `defi_satellite_ao_dispatch_batch9_2026_08_06.md`'s own `[DIAG] P1`
  - `[INFRA] P0` todos (both `[x]`, evidence: manifest 0/12,425 TARGET rows at 17:08:59Z, GCS 0 objects all 10 venues
    17:26Z, consolidator cron ≥17 clean cycles since) — commit history confirms `market-tick-data-service@eb380b71b`
    (the fix that enabled the successful relaunch) is a real ancestor of `origin/live-defi-rollout`. The `[DATA] P2`
    item (update `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 1) remains genuinely open —
    re-checked that doc's row 1 directly 2026-08-09, it still shows the old pre-fix text. Doc stays open on that one
    item. (The 2026-08-09 `/ag-closeout-audit infra` run's own parked-findings doc reached a different, more cautious
    read of this same todo — treating it as "evolved further" rather than closed — but its own text shows it was reading
    the doc's latest PROSE, not cross-referencing batch9's dated completion evidence the way the 2026-08-08 run's
    finding 21 did; this entry supersedes that caution with the direct evidence above.)
- **interactive session 2026-08-06**: resumed this doc's own P1 todos rather than leave them stale-deferred. Two fresh
  attempts today, each hitting a genuinely NEW failure mode (not the original boot-hang, which did not recur): (1)
  `-155449` hard-aborted cleanly on a pre-existing in-flight consolidator lock (~20min old, expected — waited for it to
  clear naturally, then relaunched); (2) `-161030` (e2-standard-8) OOM'd (`rc=137`) inside `_purge_manifest_rows()`'s
  unbounded full-manifest `pq.read_table()` — root-caused via the 2.41 GiB compressed / 75,184,124-row size (confirmed
  via `gsutil du -h`) against the machine's 32GB RAM, matching a known OOM signature class already documented elsewhere
  in this workspace; (3) relaunched on `e2-highmem-8` (64GB) — confirmed the OOM fix worked (got past the exact crash
  point), but the run then went silent and the VM disappeared with no completion/error log and no actual manifest
  mutation (ground-truth verified via the index blob's unchanged `Update time`) — a NEW, distinct, not-yet-root-caused
  issue, most likely a heartbeat/zombie- watchdog miscalibration reaping a legitimately-slow-but-alive process (same
  failure SHAPE as this session's separate finding: the DeFi consolidator's own stale-lock alert threshold mismatch).
  Stopped after this 3rd distinct failure mode today rather than blind-retry a 4th time, per this exact workspace's own
  established precedent for this class of problem. Consolidator cron resumed (paused for both attempts, unchanged
  manifest, no risk). GCS-object-delete phase re-confirmed 0/10 venues have remaining objects (fresh check, not reused
  from 2026-08-05).
- **na-eligibility-audit 2026-08-06 (infra tranche)**: KEEP-NA, valid — [DIAG]/[DATA] P1s: VM-boot gsutil hang
  root-cause + concurrent-launch pattern check + relaunch + manifest-purge verification; infra-flakiness diagnosis +
  VM-launch execution, not bounded worker dispatch.
- **interactive session 2026-08-05 (`/autonomous` continuation)**: 15 VM-launch attempts across ~3 hours. Confirmed
  GCS-object-delete phase 100% complete via direct verification (not inferred). Found + fixed 3 real IAM gaps (all
  shipped, IaC-tracked). Found + fixed 2 real script reliability issues (discovery-phase silence,
  skip-discovery-verified-empty optimization once proven safe, manifest-purge-phase silence). Found (but did not yet
  root-cause or fix) a VM-boot-level `gsutil` hang that killed the last 3 consecutive attempts before the Python task
  even started logging — filing this doc rather than continuing to blind-retry against what looks like active infra
  flakiness. Resumed the consolidator cron (never mutated, no risk in doing so) rather than leave DeFi-wide
  consolidation paused indefinitely.
- **context-scout 2026-08-05**: populated context_scope (5 entries) — the purge script + the actual `gsutil`-hang
  suspect files (`launcher_common.sh`, `vm-exec-with-gcs-tee.sh`) the P1 root-cause todo targets, plus the sibling
  dispatch doc the P2 todo updates.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) — the 2026-08-06 findings superseded the original
  gsutil-hang theory (did not recur) with two NEW root causes (an in-script OOM, now fixed; an open
  zombie-watchdog/heartbeat-staleness miscalibration theory) — swapped `vm-exec-with-gcs-tee.sh` out for
  `vm_zombie_watchdog.py` + `heartbeat_daemon.py` (the current open [DIAG] P1's actual suspects), kept
  `launcher_common.sh` as the still-live latent-risk file.
- **AO dispatch 2026-08-07 (`data_engineering`, slot 12)**: dispatched to root-cause the open [DIAG] P1. Confirmed via a
  read-only sub-agent investigation + independent spot-verification (commit read, `PREFIX_IDLE_THRESHOLDS`/
  `STALL_TIMEOUT_SEC` grep, `gcloud compute instances list` + serial-console tail) that candidate (a) is correct and the
  code fix already shipped same-session-adjacent (`deployment-service@0e94ceee1`, 2026-08-06T20:16:36Z, a different
  slot-4/planning dispatch) — but is dormant: the live watchdog daemon (`vm-zombie-watchdog-20260805-125558`) booted
  2026-08-05T07:26:02Z, over a day before the fix, and `launch-vm-zombie-watchdog.sh` only fetches
  `vm_zombie_watchdog.py` once at boot (confirmed by direct script read), never mid-loop — an exact recurrence of this
  same daemon's own documented 2026-07-18 "fix shipped, daemon not relaunched" gap
  (`zombie_watchdog_relaunch_reaped_live_backfills_2026_06_23.md`). Also corrected this doc's own `heartbeat_daemon.py`
  framing: the purge script never integrates with it directly; it's an unrelated sidecar. **Did NOT relaunch the
  watchdog daemon** (out of `data_engineering` craft scope per this doc's own precedent + `agents/data_engineering.md`
  STEP 0.5; two prior real-mode relaunches of this exact daemon caused confirmed live-VM kills, most recently escalated
  to an explicit operator-gated ruling) and did **NOT** relaunch the purge VM either, since doing so before the daemon
  is refreshed would very likely reproduce the exact same reap a 16th time — filed the daemon relaunch as a new blocking
  `[INFRA] P0` todo above rather than force either action past this session's craft boundary. No GCS/VM/cron mutations
  performed this session — read-only investigation only (git log/show,
  `gcloud compute instances list`/`get-serial-port-output`, source reads).
- **AO dispatch 2026-08-07 (`data_engineering`, slot 7)**: independent re-verification only — no code/GCS/VM/cron
  mutations. Confirmed: (1) watchdog daemon `vm-zombie-watchdog-20260805-125558` STILL RUNNING as of 2026-08-07T05:37Z
  (unchanged from slot 12 — `[INFRA] P0` daemon relaunch has NOT been done); (2) code fix CONFIRMED IN LDR —
  `vm_zombie_watchdog.py` `PREFIX_IDLE_THRESHOLDS["canonical-migration-"] = (90.0, 360.0)` +
  `launch-canonical-migration-vm.sh` `STALL_TIMEOUT_SEC=7200` (both in `deployment-service@0e94ceee1`); (3) GCS objects
  spot-checked 0 for ETHEREUM + ARBITRUM at 2026-08-07T05:37Z (`gcloud storage ls` → "no objects found", consistent with
  earlier verifications). Did NOT relaunch the daemon or purge VM. Posting /blocked to determine dispatch path for the
  operator-gated `[INFRA] P0` daemon relaunch.
- **AO re-dispatch 2026-08-07 (`data_engineering`, slot 7, third dispatch)**: Daemon confirmed STILL stale —
  `vm-zombie-watchdog-20260805-125558` RUNNING (gcloud compute instances list). The `[INFRA] P0` remains in this doc
  with `assigned_vm: NA`, so it is not being auto-dispatched. Posting /blocked with a concrete escalation path:
  recommend operator create an `assigned_role: infra` dispatch plan to route the [INFRA] P0 into the AO backlog.
- **AO re-dispatch 2026-08-07 (`data_engineering`, slot 7, fourth dispatch)**: same daemon, still stale, re-verified
  once more. Instead of a fourth identical `/blocked` recommendation, created
  `plans/archive/2026_08/infra_vm_zombie_watchdog_relaunch_2026_08_07.md` (created `status: draft`,
  `assigned_role: infra`; archived 2026-08-07 once its one todo completed) — a single-todo plan that mirrors this doc's
  own `[INFRA] P0` todo with an `assigned_vm: planning` home, so it can actually enter the AO backlog once the operator
  flips it `active`. The `[INFRA] P0` todo below is unchanged (still the source of truth for the fix's intent); the new
  plan is a dispatch-routing wrapper around it, not a duplicate decision. No VM/GCS/cron mutation performed this
  session.
- **2026-08-07 (AO dispatch #7, `data_engineering`, slot 10)**: VM `20260807-082535` (launched by infra dispatch #6)
  confirmed DEAD via background monitor (STOPPING at 09:17Z, GONE at 09:20Z, no EXIT_STATUS written). Root cause:
  `_download_index_chunked()` range-request approach hung for ~47 min during the 3rd consecutive 2.46 GiB download
  inside `_purge_manifest_rows()`. Evidence: WATCHDOG_TRACE.log only had iter=1 (watchdog itself died after first check
  at ~08:29:48Z); vm-heartbeat last write at 08:29:44Z; run.log 19 lines / 3148 bytes last uploaded 08:29:57Z (never
  grew); manifest last modified 2026-08-06T20:34:22Z (NOT updated); no pre-purge snapshot in `_index/snapshots/` from
  2026-08-07; VM STOPPING at 09:17Z (47 min after `_purge_manifest_rows()` started at 08:29:37Z). Code fix shipped:
  `market-tick-data-service@eb380b71b` — `_purge_manifest_rows()` now uses `blob.download_as_bytes(timeout=900)` (single
  streaming response) instead of `_download_index_chunked()` (range requests). QG green, landed on live-defi-rollout.
  Consolidator cron still PAUSED (needs resume if next infra dispatch delayed). Posting /blocked for another infra
  relaunch.
- **2026-08-07 (main, operator-authorized relaunch)**: operator authorized the real-mode relaunch at 07:30Z; main drove
  it via an infra sub-agent. Dry-run validated safe first (2 clean cycles, zero reaps), then cutover: stale
  `vm-zombie-watchdog-20260805-125558` deleted, new instance `vm-zombie-watchdog-20260807-075242` created
  2026-08-07T07:52:45Z (asia-northeast1-c), serial-console confirmed boot-clean, first real-mode poll at 08:02:58Z
  logged "Watchdog summary: 26 alive / 0 zombie / 3 too_young" → "watchdog complete: killed 0/0 zombies" +
  "terminated-reaper: reaped 0/0" — live fleet intact, `deployment-service@0e94ceee1`'s `canonical-migration-`
  `PREFIX_IDLE_THRESHOLDS` fix now live. Flipped the `[INFRA] P0` todo `[x]` above with this evidence (mirrored in
  `infra_vm_zombie_watchdog_relaunch_2026_08_07.md`, now archived). The `[DATA] P1` relaunch-the-purge-VM todo directly
  below is now UNBLOCKED — annotated it accordingly, left `[ ]` for the next worker on
  `defi_satellite_ao_dispatch_batch9-003` to execute.
- **2026-08-07 (AO dispatch #9, `infra`, slot 8)**: relaunched VM `20260807-100248` per dispatch #8's resume point.
  Found it GONE (deleted 10:55:51Z) despite the `vm_zombie_watchdog.py` fix being confirmed live — **this is a SECOND,
  previously-unknown killer, not a recurrence of the fix's own gap.** Cloud Audit Log
  (`protoPayload.requestMetadata.callerSuppliedUserAgent="python-requests/2.34.2"` +
  `serviceAccountDelegationInfo.firstPartyPrincipal=service-1060025368044@serverless-robot-prod.iam.gserviceaccount.com`,
  a Cloud Run identity — NOT the VM-side watchdog) plus the watchdog's own serial-console log (independently confirmed
  "killed 0/0 zombies" across sweep cycles 10:53→10:58Z, spanning the exact kill) together PROVE the delete came from
  `deployment-service/deployment_service/data_pipeline_monitors/heartbeat_stall_watcher.py`'s Cloud-Run `sweep()` — a
  SEPARATE mechanism (`_kill_stalled_vm` calls the watchdog's `_kill_vm` primitive directly, bypassing
  `PREFIX_IDLE_THRESHOLDS`) with its own flat `DEFAULT_KILL_MINUTES=45.0`, which the 2026-08-06 fix never touched even
  though `canonical-migration-` is explicitly in this sweep's watched-prefix list (`_is_backfill_vm` docstring). Fixed
  by adding `PREFIX_KILL_MINUTES = {"canonical-migration-": 90.0}` + `_resolve_kill_minutes()` (mirrors
  `vm_zombie_watchdog._resolve_idle_thresholds`) to `heartbeat_stall_watcher.py`'s `sweep()` loop, + 2 new regression
  tests. Manifest generation confirmed UNCHANGED by the failed run (CAS never fired) — safe to retry, no partial state.
  QG in flight at time of writing; ships via quickmerge once green, then relaunches the purge VM a 3rd time under this
  new fix. See `defi_satellite_ao_dispatch_batch9_2026_08_06.md` Progress Log for the mirrored full write-up.
- **2026-08-07 (AO dispatch #9 continued, `infra`, slot 8)**: `heartbeat_stall_watcher.py` fix **SHIPPED**
  `deployment-service@14240378194039fe5a2cfb5e2d86dbed6cffe8d8` — `quality-gates.sh` full run green (246s, 0 failures),
  landed on `live-defi-rollout` via `quickmerge.sh --agent`, post-push ancestry verified (ahead=0). Proceeding to the
  purge VM's 3rd relaunch attempt with fresh pre-flight re-verification.
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA, valid — both open todos ([DATA] P1 relaunch the purge VM
  under the newly-shipped fix; [DATA] P2 update the sibling dispatch doc once it completes) are live, in-flight
  operational work on an active incident with a fresh failure mode found and fixed within the last hour of this same
  session — not worker-determinable ahead of the next relaunch's real outcome.
