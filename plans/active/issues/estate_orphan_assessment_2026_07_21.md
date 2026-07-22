---
doc_type: issue
title:
  Estate orphan assessment 2026-07-21 — sports has 214K ORPHAN_REAL objects; defi/cefi/tradfi blocked on multi-GB
  manifest download (need a VM)
summary:
  Ran migration_orphan_sweep per asset_group (GCS→manifest, single-walk, read-only). SPORTS is measured — 214,319
  ORPHAN_REAL objects (real data with no manifest row — the silent-write gap) plus 34,385 LEGACY_DUPLICATE, reports
  written to the GCS audit parquets. prediction hung in the classification phase (30 min no progress, killed).
  defi/cefi/tradfi FAILED in-session on the multi-GB availability-index download (ChunkedEncodingError — defi index is
  ~1.8GB) — the assessment for those three needs the sanctioned VM run, not an in-session walk.
status: open
nature: issue
asset_group: [sports, defi, cefi, tradfi, prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags: [orphan, orphan-real, single-walk, manifest-completeness, silent-write, sports, migration-orphan-sweep]
related:
  [
    data_pipeline_reconciliation_skill_2026_07_20.md,
    ../../codex/02-data/orphan-object-detection.md,
    ../../codex/02-data/reconciliation-census-and-compute-tiers.md,
    migration_verification_orphan_safety_2026_06_10.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: operator request 2026-07-21 — "Orphans not assessed for any AG — lets assess then"
depends_on: []
---

# Estate orphan assessment 2026-07-21 (partial)

> **What ran:** `instruments-service/scripts/migration_orphan_sweep.py --asset-group <ag> --dry-run` (+ the
> sports-specific `migration_orphan_sweep_sports.py --bucket both --dry-run`). A GCS→manifest single-walk, read-only
> (never deletes), classifying every object A_canonical_manifested / B_legacy_duplicate / C_manifest_infra /
> **E_orphan_real** (valid shape, rows>0, NO manifest row → the silent-write / manifest-completeness gap).

## MEASURED — SPORTS (both indexes; reports durable in GCS)

| bucket                                     | A_canonical | B_legacy_dup | C_infra | **E_ORPHAN_REAL** | size      |
| ------------------------------------------ | ----------- | ------------ | ------- | ----------------- | --------- |
| `market-data-tick-sports-prd` (odds)       | 474,125     | 0            | 3,096   | **27,348**        | 12.99 GiB |
| `instruments-store-sports-prd` (reference) | 960,703     | **34,385**   | 165,603 | **186,971**       | 22.60 GiB |

**≈214,319 ORPHAN_REAL** (real sports data on disk with no manifest row) + **34,385 LEGACY_DUPLICATE** (reference).
Per-object detail written to `gs://{bucket}/_index/audit/orphan_sweep_sports.parquet` (DURABLE — re-read these, do not
re-walk). ORPHAN_REAL = the data exists but honest-coverage under-reports it (a manifest-completeness hole, the inverse
of a phantom); these must be back-filled with `record_captured` (never deleted). This is a data-correctness finding —
operator-notified 2026-07-21.

## NOT COMPLETED — the manifest-download scale wall

- **prediction** — swept 1.15M objects cleanly (~8.8k/s) but then HUNG in the classification/manifest-join phase (30 min
  with zero progress; process killed). No result.
- **defi / cefi / tradfi** — FAILED in-session at "loading manifest cells":
  `requests.exceptions.ChunkedEncodingError: Connection broken: IncompleteRead` pulling the multi-GB consolidated
  `_index/availability_index.parquet` (defi's is ~1.8GB; tradfi died the same way; cefi never got past the load). **This
  is not a code bug** — a single-process in-session download of a multi-GB manifest is unreliable; this single-walk is
  meant to run on a VM (robust network + memory), which is why the tool is the CF-17 deliverable of
  `migration_verification_orphan_safety_2026_06_10.md`.

## Todos

- [x] 1. [DATA] P1. **Back-fill the 214,319 sports ORPHAN_REAL rows** via `record_captured` (read the durable
      `orphan_sweep_sports.parquet` audit reports; NEVER delete — this is real data honest-coverage is missing). Verify
      the sports honest-coverage rises after. **DONE 2026-07-22** — found + excluded 83,541 pre-2020-06-06-floor
      `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` rows first (UAC registry gap, `unified-api-contracts@46d865df`, filed
      `sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md` for the operator-gated WIPE ask on those),
      wired a durable `split_pre_floor` filter into the backfill script (`instruments-service@fc5983a8`, regression test
      added), then ran `backfill_orphan_class_e_sports.py --apply --consolidate` for both buckets: **odds — 4 cells
      recorded** (27,323 of 27,348 report rows were already covered by normal capture since the 2026-07-21 audit);
      **reference — 97,606 cells recorded, 0 errors** (103,426 of 103,430 legitimate rows still orphan at apply-time).
      Consolidation deferred to the sibling cron (fresh lock present on both buckets at apply-time) — the per-VM-shard
      write is durable and already correct; the canonical blob will reflect it on the cron's next cycle.
- [x] 2. [DATA] P1. **Triage the 34,385 sports LEGACY_DUPLICATE** (reference bucket) — content-verify each has a
      manifested canonical twin (the 5-part proof), then the human-only delete disposition. **DONE 2026-07-22** — full
      5-part-proof triage at `sports_legacy_duplicate_triage_2026_07_22.md`. **0 of 34,385 rows pass** (no delete
      executed, none warranted yet): 4,735 are stale audit entries for objects already deleted by the independent
      2026-07-21 pre-floor wipe; 1,492 are real pre-floor objects that wipe missed (belongs in that scope, not here);
      28,100 are blocked by 2 confirmed live readers (`sports_reference_fixtures.py:139`,
      `data_status_sports.py:42,74`); 58 are blocked by content-incomplete twins (canonical holds ~2-10% of the legacy
      row count). See that doc's own todos for the recommended follow-up (fold into the wipe / migrate-forward / repoint
      readers) — none of which is a fresh delete decision.
- [ ] 3. [INFRA] P1. **Run the orphan sweep for defi / cefi / tradfi / prediction on a VM** — deployment-service@f8e885f
      shipped `launch-orphan-sweep-vm.sh` (registered `orphan-sweep-{ag}-` prefixes, SPOT, singleton-locked,
      tarball-freshness-checked) reusing the Tier-2 launcher machinery. First launch attempt 2026-07-22 04:22-04:23 UTC
      (`orphan-sweep-cefi-20260722-042242`, `-defi-20260722-042258`, `-tradfi-20260722-042317`,
      `-prediction-20260722-042333`) — **all 4 CRASHED within ~3 minutes (exit_code=2)**, caught by the armed heartbeat
      watchdog (30-min/5-min ticks), NOT silently missed. Root cause: `VM_TASK=orphan-sweep` had no dispatch branch in
      `setup-data-pipeline-vm.sh` (same recurring bug class as the datapoint-validation gap — see
      `datapoint_validation_results_bucket_missing_2026_07_21.md`; 4th known instance) — fell through to the generic
      `--operation orphan-sweep` builder, which `migration_orphan_sweep.py`'s CLI has no such flag for. **Fixed**:
      `deployment-service` — added the missing `elif [[ "$VM_TASK" == "orphan-sweep" ]]` branch (mirrors the
      datapoint-validation branch, consumes `VM_BACKFILL_CMD` as-is) — `deployment-service@74eca154`. Tarball +
      setup-script republished, relaunched 2026-07-22 05:04-05:05 UTC: `orphan-sweep-cefi-20260722-050405`,
      `-defi-20260722-050426`, `-tradfi-20260722-050445`, `-prediction-20260722-050511` (all RUNNING,
      asia-northeast1-c). The dispatch fix itself held (no crash) — but a follow-up check after a ~10hr real-world gap
      revealed the deeper truth the 30-min watchdog window couldn't see: **only tradfi actually completed** (fresh
      report written 2026-07-22, exit clean). **defi and prediction both hit a severe, reproducible throughput cliff at
      ~1.15-1.2M objects** (11,000/s → 582/s in one step, decaying continuously to ~51/s ten hours later, never
      recovering) and were still crawling-but-alive when SPOT-preempted, with no final report written. **cefi failed a
      SECOND time** — the relaunch (`orphan-sweep-cefi-20260722-055006`) reproduced the identical zero-output stall as
      the first attempt (confirmed via a focused 3rd watchdog), killed again. **This is a genuine, reproducible
      performance bug in `migration_orphan_sweep.py` itself**, filed in full with measured evidence at
      `migration_orphan_sweep_performance_decay_2026_07_22.md` — NOT relaunching defi/cefi/prediction again until that
      doc's todos 1-4 land a real fix (todo 4 below folds into that doc's scope). **Net measured state**: sports
      (2026-07-21) and tradfi (2026-07-22) are the only two asset_groups with a completed orphan-sweep report;
      defi/cefi/prediction remain genuinely unmeasured for orphan objects.

      **Update 2026-07-22 (later same day) — real fixes shipped, cefi now MEASURED.** Two fixes shipped
              (`instruments-service@d271dc3b` wires the sweep's dead `workers` concurrency param; `deployment-service@181daed1`
              bumps cefi to `e2-highmem-8`) — full detail + honest before/after in
              `migration_orphan_sweep_performance_decay_2026_07_22.md`. Relaunched all 3: **cefi (`orphan-sweep-cefi-20260722-161432`)
              COMPLETED** — full 8,501,253-object walk in ~40 min (previously hung indefinitely, twice), self-terminated clean.
              Real measured cefi orphan state: `A_canonical_manifested=3,575,143`, `B_legacy_duplicate=6`,
              `C_manifest_infra=66`, `C2_non_data=3,988,460`, `D_junk=1,864`, **`E_orphan_real=935,714`** (needs a
              `record_captured` backfill — same class as the sports 214K finding, not yet scoped/executed), `170` unknown
              prefixes (needs investigation). Report: `gs://market-data-tick-cefi-prd-central-element-323112/_index/audit/orphan_sweep_cefi.parquet`.
              defi (relaunched as `orphan-sweep-defi-20260722-165131` after an unrelated SPOT preemption at 1.25M objects) and
              prediction (`orphan-sweep-prediction-20260722-161520`) were both still running, healthy, past their old
              ~1.2M-object failure point at last check — **not yet complete; re-check before flipping this todo fully done.**
          **Later check (17:34 UTC, ~80 min after relaunch)**: both STILL running, STILL genuinely progressing — defi at
          1.95M objects (instantaneous rate settled ~280-370/s), prediction at 2.85M objects (instantaneous rate ~450/s,
          possibly stabilizing rather than still falling). Neither crashed, hung, or stalled across ~80 min of continuous
          observation. **At this rate each will likely take several more hours to finish** — this is CANNOT-BE-DONE-YET
          (needs elapsed real time), not blocked work. Stopped actively re-polling per the workspace's "don't over-watch"
          guidance now that the trend (real, if slow, forward progress) is well-established; check again later rather
          than arming another short watchdog.

- [ ] 4. [CODE] P2. **Make the manifest load resumable / streamed** in `migration_orphan_sweep.py` (chunked download
      with retry, or read the index in row-group batches) so a multi-GB index does not break a single connection — this
      is what blocked defi/cefi/tradfi in-session originally, and is now folded into
      `migration_orphan_sweep_performance_decay_2026_07_22.md` todo 2 (likely cefi's exact 2026-07-22 hang) alongside
      the separately-found defi/prediction throughput-decay bug (that doc's todos 1/3) — see that doc for the full,
      current scope; don't duplicate investigation here.

## Lesson (do not re-learn)

The in-session single-walk works for small AGs but the **manifest DOWNLOAD** (not the object walk) is the bottleneck at
scale: a ~1.8GB `availability_index.parquet` breaks a single-process HTTP read (`ChunkedEncodingError`). Run large-AG
orphan sweeps on a VM, or fix the loader to stream/resume. Object listing (`list_blobs`) was NOT the problem —
prediction swept 1.15M objects fine; it was the manifest join-load that hung/broke.
