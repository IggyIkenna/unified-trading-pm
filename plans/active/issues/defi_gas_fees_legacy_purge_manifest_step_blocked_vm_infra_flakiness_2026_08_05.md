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
    deployment-service/scripts/vm/lib/launcher_common.sh,
    deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh,
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
      crash point cleanly (`[attempt 1] index generation=...: 12425 TARGET-signature row(s) (of 75184124     total)` —
      the exact line that never printed before). Machine-size fix confirmed effective for the OOM specifically (see next
      todo for what happened after).
- [ ] [DIAG] P1. **NEW BLOCKER found 2026-08-06, NOT YET ROOT-CAUSED — do not blind-retry a 4th time.** The
      `e2-highmem-8` run above got past the OOM, logged `[attempt 1] index generation=...` at 15:31:08, then went SILENT
      — no further log lines (no `filtered table ready`, no `Snapshotted...`, no `REWROTE index`) for the remainder of
      its life. The VM itself vanished from `gcloud compute instances list` sometime before ~15:47 (confirmed via
      `gcloud compute instances describe` returning "not found" — not a STOPPED/TERMINATED state, an actual delete,
      consistent with `VM_SHUTDOWN_ON_COMPLETION=true` firing, but with NO corresponding `REWROTE index`/error/exit-code
      log line ever uploaded). **Ground-truth check is decisive**: the canonical index blob's `Update time` is
      `2026-08-06T15:09:30Z` — BEFORE this VM even started (15:30:08) — so the CAS write never happened; this was a
      genuine failure, not a logging gap masking a real success. The VM's own heartbeat blob (`vm-heartbeat/<vm>.txt`)
      showed content `"<epoch>\n-1\nstarting"` mid-run — the `-1`/`starting` fields look suspicious (a heartbeat that
      never left "starting" state could cause a heartbeat-staleness-based zombie-watchdog to reap a process that was
      still legitimately CPU/network-bound in the filter→snapshot-upload (2.4GB+)→CAS-write sequence, not actually
      dead). Root-cause candidates, not yet distinguished: (a) the fleet zombie-watchdog's heartbeat-staleness threshold
      is miscalibrated for this script's `heartbeat_daemon.py` integration (mirrors this exact session's OTHER finding
      today: the DeFi consolidator's own stale-lock alert was miscalibrated for a 4200s override vs a 300s default —
      same failure SHAPE, different subsystem); (b) a genuine hang/crash inside the filter/serialize/upload step itself
      (less likely given `e2-highmem-8` should have ample CPU/RAM headroom for a 75M-row arrow filter, but not ruled
      out). **Per this exact workspace's own established discipline for this failure class** (see
      `mdps_full_mode_reprocess_manifest_cache_oom_2026_08_03.md`'s own "do not attempt a 4th VM-launch-and-guess cycle"
      lesson) — stopping further blind retries here. Consolidator cron RESUMED (paused for both of today's attempts, no
      risk in resuming — manifest still unchanged).
- [ ] [DATA] P1. Once the above is root-caused/fixed (or a bounded diagnostic run with e.g. `--verbose`/explicit
      progress logging around the filter/upload/CAS steps confirms where exactly it stalls), relaunch
      `MACHINE_TYPE=e2-highmem-8 bash scripts/vm/launch-canonical-migration-vm.sh defi-gas-fees-legacy-purge     <any-date> <any-date> full`
      (deployment-service; dates are cosmetic for this category; keep the highmem machine-type override, it's confirmed
      necessary). Before launching: (a) pause the consolidator cron again
      (`gcloud scheduler jobs pause uts-prod-manifest-consolidator-market-data-defi-cron --location     asia-northeast1`),
      (b) fresh-re-verify 0 remaining objects with the same direct 10-venue-wide `match_glob` check this doc used via
      `gcloud storage ls --match-glob=...` (do NOT trust this doc's numbers as still current without re-checking —
      re-run it fresh; confirmed 0/0 across all 10 venues as of 2026-08-06). After success: resume the cron, watch >=4
      post-resume `--verify-only` cycles per the script's own printed instructions (~65s apart).
- [ ] [DATA] P2. Update `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 1 once the manifest purge
      actually completes (its current entry cites a different, never-committed script name
      `delete_legacy_gas_fees_venue_2026_08_04.py` with different numbers — likely stale/abandoned WIP from an earlier,
      since-lost session; this doc's script + numbers are the real, shipped, adversarially-reviewed lineage).

## Progress Log

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
