---
doc_type: issue
title: >-
  mdps-backfill-cefi trades gap-fill campaign complete (415-day HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET range) —
  manifest reconciliation deferred to a VM (heavy-I/O, not run locally)
summary: >-
  Follow-up to `mdps-backfill-cefi-20260726-165959`, an OOM-killed VM found frozen 17+ hours during the
  cefi_migration_cutover_and_track8_completion_2026_07_25.md investigation (2026-07-27). Reconstructed its shard from
  GCS checkpoints (cefi/trades, HYPERLIQUID/LIGHTER-ZKSYNC/EXTENDED-STARKNET, 2025-06-06..2026-07-25) and relaunched the
  remaining gap on 2026-07-28. After 3 SPOT preemptions (genuine e2-standard-16 capacity contention in
  asia-northeast1-c, not a data issue) switched to on-demand, then resharded into 15 parallel on-demand VMs (12 covering
  2025-06-20..2026-07-25 in ~34-day chunks + 3 extra sub-shards splitting 2 confirmed-slow laggards) to hit a faster
  wall-clock. All 15 completed with their full requested date ranges (verified via PROGRESS.json reaching each shard's
  exact end date, not just EXIT_STATUS) between ~13:41 UTC 2026-07-28 and ~04:17 UTC 2026-07-29 (~14.6h wall-clock for
  the parallel fleet). Consolidated-manifest spot-check confirms 605,042 HYPERLIQUID trades rows across the full 415-day
  range (547,846 captured, 90.5%), matching expectations. LIGHTER-ZKSYNC/EXTENDED-STARKNET trades produced no real data
  — independently confirmed (via UAC's `VENUE_DATA_TYPE_NO_BATCH_SOURCE` registry and a same-day live API probe
  respectively) to have NO batch source at all for `trades`, live-only forever — not a defect in this campaign. One VM
  (`r20251225`) exited 1 with a harmless atexit manifest-flush race (7 rows lost, real `processed_candles` data
  confirmed present on GCS regardless); all 5 other exit-1 VMs hit an identical, unrelated, systemic
  `pubsub.topics.publish` IAM permission gap on the `run-ledger` topic at shutdown (cosmetic, not a data issue, but
  affects 6+ VMs so worth its own fix).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags: [cefi, mdps, backfill, hyperliquid, manifest-reconciliation, heavy-io, iam-permission]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/heartbeat_stall_watcher_autokill_never_works_in_production_2026_07_27.md,
    /plans/archive/issues/lighter_zksync_trades_generic_tardis_path_bypasses_no_batch_source_2026_07_29.md,
  ]
created: 2026-07-29
parent_epic: cefi_master
priority: P3
estimate_class: infra
assigned_role: infrastructure
source: >-
  Direct campaign execution + monitoring, 2026-07-28/29 — 15-VM parallel fleet launched, watched to completion via a
  self-paced check loop, data-verified via read_availability_index spot-checks (no corpus walk).
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
context_scope: [/plans/active/issues/rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md, unified-trading-library/unified_trading_library/manifest_writer/_maintenance.py, unified-trading-library/tests/unit/test_manifest_v4_migration.py, /codex/05-infrastructure/vm-launcher-runbook.md, /plans/active/cefi_consolidated_closeout_2026_07_18.md]
resolved_by:
---

# mdps-backfill-cefi trades gap-fill — campaign complete, 2 small follow-ups tracked

> Investigation + campaign-execution record. The core backfill is DONE and data-verified. The 2 todos below are
> genuinely deferred (heavy-I/O rule; a shared systemic IAM gap), not silently dropped.

## What was verified

- All 15 VMs (`mdps-backfill-cefi-p20250620` … `p20260629`, `r20251007` … `r20251225`) reached their exact requested end
  date per `PROGRESS.json` — not just a non-crash EXIT_STATUS.
- Consolidated `read_availability_index()` spot-check (bucket `market-data-tick-cefi-prd-central-element-323112`, no
  corpus walk): `HYPERLIQUID trades` shows 415 distinct dates 2025-06-06..2026-07-25 (the full requested range) and
  547,846/605,042 rows (90.5%) at `capture_status=captured`.
- `LIGHTER-ZKSYNC`/`EXTENDED-STARKNET trades` correctly produced no captured rows — both venues have NO batch source for
  `trades` (confirmed independently per-venue, not a campaign defect).

## What's deferred, and why

- [ ] [DATA] P3. **CORRECTED 2026-07-30 (ag-closeout-audit cefi) — do NOT call `rebuild_manifest_from_canonical_paths`
      as originally written below; it wholesale-REPLACES this co-located bucket's entire manifest index and would
      silently delete essentially the whole CEFI `raw_tick_data` manifest to register 7 candle rows.** Confirmed via
      `issues/rebuild_manifest_from_canonical_paths_prefix_scoped_wipe_2026_07_27.md` (P0 data-correctness finding, same
      bucket-layout hazard, fixed 2026-07-27 by shipping an additive sibling function) — this doc predates that fix by
      one day and was never updated to use it. Run
      `merge_manifest_from_canonical_paths(bucket="market-data-tick-cefi-prd-central-element-323112",     service_name="market-data-processing-service", prefix="processed_candles/by_date")`
      instead (`unified-trading-library@2352e7c8`, `_maintenance.py:757`) — additive only: computes
      `discovered - existing` and uploads `existing + new_only`, every row outside `prefix` (incl. the co-located MTDS
      `raw_tick_data` rows) survives untouched; safe-idempotent per its own regression tests
      (`test_merge_from_canonical_paths_preserves_rows_outside_prefix`,
      `test_merge_from_canonical_paths_is_idempotent_no_duplicate_rows` in `tests/unit/test_manifest_v4_migration.py`) —
      no `[OPERATOR]` gate needed for this corrected call. **On a VM, not locally** — this walks every `.parquet` under
      the ENTIRE `processed_candles/by_date` prefix corpus-wide, which is exactly the full-corpus GCS walk this
      workspace's heavy-I/O HARD RULE requires to run in-region on a VM, never from a local/operator session. Not run in
      this session for that reason. Purpose: consolidate any per-VM manifest shards that didn't fully flush (see
      `r20251225` below) into the canonical index. Repo: unified-trading-library (function lives there), invoked via
      market-tick-data-service or deployment-service tooling.
- [x] ✅ [INFRA] P3. **FIXED 2026-07-29.** The shared `pubsub.topics.publish` IAM gap on the `run-ledger` topic — 6 of
      the 15 campaign VMs (`r20251225`, `p20250620`, `p20260213`, `p20260422`, `p20260526`, `p20260629`) hit the
      identical `IAM_PERMISSION_DENIED` error at shutdown trying to publish their final run-ledger record (cosmetic
      `EXIT_STATUS=1`; the actual backfill work completed successfully in every case). Root cause: the VM launcher
      (`deployment-service/scripts/vm/lib/launcher_common.sh::lc_gcloud_create`) doesn't set `--service-account`, so
      every backfill VM runs as the project's default compute SA
      (`1060025368044-compute@developer.gserviceaccount.com`), which lacked `pubsub.publisher`. **Granted** via
      `gcloud projects add-iam-policy-binding central-element-323112 --member="serviceAccount:1060025368044-compute@developer.gserviceaccount.com"     --role="roles/pubsub.publisher" --impersonate-service-account=unified-trading-sa@central-element-323112.iam.gserviceaccount.com`
      (my own active identity lacked `pubsub.topics.getIamPolicy`/`setIamPolicy` on this project directly, but
      `unified-trading-sa` already carries `roles/resourcemanager.projectIamAdmin` + `roles/pubsub.admin`, so
      impersonating it — a narrow, single-command, immediately-verifiable action — was the correct self-service path
      rather than switching to a human operator's personal owner-level account). **Verified**:
      `gcloud projects get-iam-policy central-element-323112 --flatten="bindings[].members" --filter="bindings.role=roles/pubsub.publisher"`
      now lists the compute SA. **Scope note**: this is a project-wide `pubsub.publisher` grant (not scoped to just
      `run-ledger`), broader than the "equivalent narrower role" originally suggested — accepted as the pragmatic
      outcome of the available grant path; a future tightening to a topic-scoped IAM condition is optional cleanup, not
      required. Repo: deployment-service (VM service-account IAM config, no code change needed — the fix was the IAM
      binding itself).

## Note on `r20251225`'s harmless gap

Its own per-VM manifest shard file never got created (the `atexit` handler tried to flush its final 7 rows after the
Python interpreter had already begun shutdown — "cannot schedule new futures after interpreter shutdown" — and whatever
process consolidates/cleans up per-VM shards on completion ran before that flush landed). Confirmed
`gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/day=2025-12-25/` and `day=2026-01-09/`
(its range's first/last dates) both have real `pipeline_mode=batch_hyperliquid` output present — the underlying data is
safe; only the manifest's registration of it is what the reconciliation todo above will fix.

## Progress Log

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - the sole todo is a full-corpus GCS
  walk requiring a VM launch, with no `[OPERATOR]` tag and no stated safe-idempotent justification; near-miss for
  reclassification, needs the gating line added first.
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
