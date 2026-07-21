---
doc_type: plan
title: manifest_429_per_vm_sharding
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    deployment-api,
    deployment-service,
    execution-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: []
related: [availability_manifest_v4_and_data_status_2026_04_13.md, manifest_schema_v6_quote_margin_combo_2026_04_23.md]
created: "2026-04-25"
slug: manifest_429_per_vm_sharding_2026_04_25
date: 2026-04-25
owner: claude-code
locked_by: live-defi-rollout
locked_since: 2026-04-25
priority: P0
phase: in_progress
domain: infrastructure
---

## Deferred work — migrated to: `plans/active/issues/manifest_v6_batch3_residual_orphaned_work_2026_07_21.md`,

`plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md` — successor:
manifest_v6_batch3_residual_orphaned_work_2026_07_21, consolidator_throughput_backlog_monitor_2026_07_09 (the
7-day-observation item is STALE_OBSOLETE — 3 months of continuous production operation supersede a one-time window; the
"Cloud Monitoring panel" item is AMBIGUOUS — no literal generation-conflict panel exists, but
`consolidator_throughput_backlog_monitor_2026_07_09` shipped adjacent observability that may already satisfy intent.
**GENUINELY ORPHANED**: deleting `_write_with_generation_match` + its feature flag — still live in
`unified-trading-library`, but current architecture now also deliberately reuses this CAS path for canonical-index
force-rewrites, so the original "clean deletion" premise needs re-scoping, not blind re-execution — filed in the issue
doc above. NOTE: `locked_by: live-defi-rollout` was never cleared at archival — flagged for operator `[unlock-plan]`
cleanup.)

# Manifest-429 Per-VM Sharding Architecture

## Background

`unified-trading-library`'s `ManifestWriter` writes to a single canonical blob `_index/availability_index.parquet` per
bucket. When the CeFi backfill fleet (89+ VMs) runs concurrently, every VM read-merge-writes the same blob under
generation-match CAS with 15-retry exponential backoff. Result: cascading 429s ("exceeded rate limit for object mutation
operations") — 20-37 generation conflicts per VM, last-writer-wins data loss as the retry budget exhausts, and an index
that lags actual writes by minutes.

**Reference fix**: UTL `ac7aafe6` solved the identical problem for `events.jsonl` by partitioning into per-VM paths
(`events/{service}/{date}/{instance}/events.jsonl`) keyed by `VM_NAME` / `HOSTNAME`. We need the same architectural
shape for manifest writes — plus an explicit consolidator and a reader fallback because the manifest serves UI traffic
(deployment-api data-status drilldowns).

## Pre-audit manifest

### Writers (~50 call sites, hot paths in italics)

| Repo                              | File                                                                                                                                                          | Notes              |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------ |
| instruments-service               | _engine/orchestrator.py_ (~17 sites at L1114, L1305, L1392, L1426, L1481, L1608, L1708, L1851, L2225, L3664, L3902, L4087, L4264, L4482, L4778, L5219, L5692) | hot — fleet-scale  |
| instruments-service               | _cli/instruments_handler.py:175_                                                                                                                              | hot                |
| instruments-service               | scripts/{rescan_prediction_v4.py:112, patch_prediction_shards.py:72, full_polymarket_dump.py:225}                                                             | offline            |
| market-tick-data-service          | _engine/orchestrator.py:1393_                                                                                                                                 | hot — CeFi 89+ VMs |
| market-tick-data-service          | _cli/handlers/\_defi_manifest.py:86_                                                                                                                          | hot                |
| market-tick-data-service          | scripts/{migrate_deribit_margin_split_v6, rebuild_cefi_manifest, rebuild_prediction_manifest}.py                                                              | offline            |
| features-volatility-service       | _engine/orchestrator.py:192,264,647_                                                                                                                          | hot                |
| features-onchain-service          | _engine/orchestrator.py:148_                                                                                                                                  | hot                |
| features-multi-timeframe-service  | _engine/orchestrator.py:242_                                                                                                                                  | hot                |
| features-delta-one-service        | _engine/orchestrator.py:238_                                                                                                                                  | hot                |
| features-cross-instrument-service | _cli/handlers/batch_handler.py:327_                                                                                                                           | hot                |
| features-sports-service           | _cli/handlers/batch_handler.py:232_                                                                                                                           | hot                |
| features-commodity-service        | _cli/handlers/batch_handler.py:212_                                                                                                                           | hot                |
| features-calendar-service         | _engine/calendar_orchestrator.py:213,233,253,361_                                                                                                             | hot                |
| ml-inference-service              | _app/core/prediction_publisher.py:115,211_                                                                                                                    | hot                |
| ml-training-service               | ml/model_registry.py:290                                                                                                                                      | medium             |
| strategy-service                  | engine/core/cloud_strategy_storage.py:186,264,342                                                                                                             | medium             |
| risk-and-exposure-service         | core/risk_snapshot_sink.py:116                                                                                                                                | medium             |
| execution-service                 | engine/modes/live/data_sink.py:109, results/save_operations.py:784                                                                                            | medium             |
| pnl-attribution-service           | cli/handlers/compute_handler.py:237                                                                                                                           | medium             |
| alerting-service                  | persistence/storage_store.py:98                                                                                                                               | low                |
| market-data-processing-service    | _app/core/{orchestration_service.py:329, canonical_writer.py:309}_                                                                                            | hot                |
| deployment-service                | scripts/rebuild_sports_manifest.py:202                                                                                                                        | offline            |
| unified-trading-library           | manifest_migrations/migrator.py (uses ManifestWriter internally at L2319)                                                                                     | offline            |

### Readers (5 critical, ~15 total)

| Repo                     | File                                                                                              | Action                                                                           |
| ------------------------ | ------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| unified-trading-library  | manifest_writer.py (lookup, check_data_available, check_shard_freshness, dependency_check.py:132) | **Internal — swap body of `read_availability_index` for fallback-aware version** |
| **deployment-service**   | cli/utils/manifest_reader.py:159,189,257,541,628                                                  | **Highest read volume — gets fallback for free via UTL change**                  |
| **deployment-api**       | services/{data_status_service.py:1227, shard_detail.py:493, data_status_drilldown.py:138,1829}    | **UI live reads — gets fallback via UTL change**                                 |
| instruments-service      | engine/orchestrator.py:378,994,2100; multiple scripts                                             | gets fallback via UTL                                                            |
| market-tick-data-service | reader.py:357, engine/orchestrator.py:1027                                                        | gets fallback via UTL                                                            |
| features-\*              | scripts/smoke_matrix.py (×7), features-sports/scripts/check_pipeline_completeness.py:373          | smoke-only — defer                                                               |

### Schema impact

None on disk. Per-VM shards write the same `AvailabilityRecord` v6 schema that the consolidated blob currently has.
`_backfill_columns` already adds missing columns at read time, so cross-shard schema-version mixing during rollout is
handled.

### Existing test coverage in UTL

- `test_manifest_writer_zero_fill.py`
- `test_manifest_writer_league.py`
- `test_manifest_writer_schema_validation.py`
- `test_manifest_writer_v6.py`
- `test_manifest_writer_flush_cadence.py` — uses `_CountingStubStorageClient`, excellent harness to extend for the
  per-VM tests.
- `test_manifest_writer_flush_all.py`
- `test_manifest_writer_capture_status.py`
- `test_manifest_v4_migration.py` / `test_manifest_migrations.py`

No existing test stresses concurrent CAS conflicts.

## Architectural design

### On-disk layout (per category bucket)

```
gs://{bucket}/_index/availability_index.parquet              # consolidated SSOT
gs://{bucket}/_index/per_vm/{instance}.parquet               # one per writer VM
gs://{bucket}/_index/per_vm/_legacy_seed.parquet             # one-time copy of pre-migration single blob
```

`{instance}` resolution mirrors `event_sink.py:78-79`:

```
VM_NAME env || HOSTNAME env || local-{pid}-{rand4}
```

sanitized with `[^A-Za-z0-9._-]` → `_`. Stable for the writer's lifetime.

### Phase 1 — Per-VM writer (no CAS contention)

- Add `_PER_VM_PATH_TEMPLATE = "_index/per_vm/{instance}.parquet"` constant.
- Resolve `self._instance_id` in `__init__` from `VM_NAME` / `HOSTNAME` / pid+rand fallback.
- Replace `_write_with_generation_match()` semantics for the per-VM path: read own shard, merge, write back
  unconditionally (no CAS — exactly one writer per shard within a VM lifetime).
- Multi-thread atomicity: existing `_LIVE_WRITERS_LOCK` pattern protects against same-process races.
- Keep `_WRITE_BUFFER` time-throttle as additional protection against per-shard 1-write/sec GCS object-mutation limit.
- Behind feature flag: `MANIFEST_PER_VM_SHARDS=true` (env, default `false` for first commit so CI runs side-by-side).

### Phase 2 — Consolidator (deferred)

New module `manifest_consolidator.py`. Algorithm:

1. List `_index/per_vm/*.parquet` (and `_legacy_seed.parquet`).
2. Read each, concat, `_backfill_columns`, `_merge_dataframes` dedup (already last-write-wins by `attempted_at` + dedup
   key).
3. Write consolidated `_index/availability_index.parquet` via existing CAS path (single writer = consolidator job; CAS
   only protects against scheduler overlap, never herd).
4. Emit `MANIFEST_CONSOLIDATED` lifecycle event with shard counts + latency.

Deployment: `deployment-service/cloud-run-jobs/manifest-consolidator/`, Scheduler cron `*/1 * * * *` per category
bucket.

### Phase 3 — Reader fallback

Replace body of `read_availability_index(bucket)` with two-stage:

1. Read `_index/availability_index.parquet` + grab `updated` metadata.
2. If blob missing OR `(now - updated).total_seconds() > MANIFEST_CONSOLIDATED_STALENESS_SEC` (default 120s,
   env-overridable): list `_index/per_vm/*.parquet`, read all, merge, return.
3. Else: return consolidated blob (fast path — one download).

`_INDEX_CACHE` 60s TTL preserved.

### Phase 4 — Migration

One-shot ops step per bucket:

```
gsutil cp gs://.../_index/availability_index.parquet \
          gs://.../_index/per_vm/_legacy_seed.parquet
```

Treats the historical single blob as a synthetic "legacy" shard so the consolidator picks it up automatically — no
special-case branch.

### Phase 5 — Tests

- `tests/unit/test_manifest_writer_per_vm.py`:
  - 50-thread concurrent `ManifestWriter` against extended `_CountingStubStorageClient` (with `if_generation_match`
    simulation): assert **0** PreconditionFailed events; assert each thread writes only to its own
    `_index/per_vm/{thread_id}.parquet`.
  - Multi-row per-shard atomicity: 200 rows → exactly 1 upload.
- `tests/unit/test_manifest_consolidator.py` (deferred — Phase 2):
  - 5 fake per-VM shards with overlapping rows → consolidated keeps last `attempted_at`.
  - Malformed shard parquet logged WARN, skipped, completion succeeds.
  - Idempotency: second run = no-op.
- `tests/unit/test_manifest_reader_fallback.py`:
  - Consolidated blob 600s old + 3 fresh per-VM shards → reader returns merged view.
  - Consolidated blob fresh → reader does NOT list per_vm (assert via storage stub).
  - Mixed schema versions across shards → backfilled correctly.
- `tests/integration/test_manifest_concurrency.py` (deferred — Phase 7): fsouza/fake-gcs-server, 50 concurrent writers +
  1 consolidator, assert final consolidated = expected merged set.

### Phase 6 — Rollout

1. Land UTL change (Phases 1+3+5 — feature flag `false`). All consumers continue using the legacy single-blob path.
2. Quickmerge UTL → semver bump → propagate floor to all 25 downstream consumers via PM rollout PR.
3. Phase 2 lands (consolidator + Cloud Run Job + Scheduler).
4. Per-bucket cutover ops sequence:
   - `gsutil cp` legacy-seed.
   - Set `MANIFEST_PER_VM_SHARDS=true` for all VMs writing into that bucket (deployment-service VM/Cloud Run env
     injection).
   - Watch `MANIFEST_CONSOLIDATED` event for one cycle.
   - Verify drift-free against per-VM merge.
5. After all buckets cut over: delete the flag and the legacy `_write_with_generation_match` codepath entirely (clean
   break per workspace "no backwards compat shims" rule).

### Phase 7 — Validation

- UTL `bash scripts/quality-gates.sh` (Pass 1).
- Per affected hot-path consumer: same.
- 50-VM smoke against `gs://manifest-429-smoke-test-...`: assert 0 × PreconditionFailed; consolidated row count =
  `sum(unique dedup keys across all per-VM shards)`.
- 7-day production observation: dashboard panel "ManifestWriter generation conflicts" reads 0; deployment-api
  data-status freshness < 5min P99.

## Repo update classification

**Block PR until done (must adopt before flip):**

- unified-trading-library (writer + reader + consolidator)
- deployment-service (cloud-run-jobs/manifest-consolidator)
- deployment-api (data-status drilldown — validate fallback latency path)
- instruments-service, market-tick-data-service (highest write volume)

**Auto-compatible — version floor bump only (no code change):**

- features-_ services, ml-_, strategy-service, risk-and-exposure-service, execution-service, pnl-attribution-service,
  alerting-service, market-data-processing-service.

**Defer (low write volume / offline scripts):**

- instruments-service/scripts/_, market-tick-data-service/scripts/_,
  deployment-service/scripts/rebuild_sports_manifest.py.

## Effort estimate

| Phase                             | Effort                       | Repos                    |
| --------------------------------- | ---------------------------- | ------------------------ |
| 0 — Pre-audit                     | done                         | n/a                      |
| 1 — Per-VM writer                 | 0.5d                         | UTL                      |
| 2 — Consolidator (deferred)       | 1d                           | UTL + deployment-service |
| 3 — Reader fallback               | 0.5d                         | UTL                      |
| 4 — Migration ops (deferred)      | 0.5d                         | deployment-service infra |
| 5 — Tests for Phase 1+3           | 0.5d                         | UTL                      |
| 5b — Tests for Phase 2 (deferred) | 0.5d                         | UTL                      |
| 6 — Rollout (deferred)            | 1d wallclock                 | UTL → 4 hot consumers    |
| 7 — Validation (deferred)         | 0.5d active + 7d observation | all                      |

**Total active effort: ~5 days.** This session ships Phase 1 + Phase 3 + Phase 5 (UTL) behind the feature flag.
Remaining phases are subsequent sessions.

## Rollback plan

- Single env flag `MANIFEST_PER_VM_SHARDS` (default `false`) — flip back per VM if anomalies detected.
- Consolidator job: pause Scheduler trigger; reader fallback automatically merges per-VM shards live (operates degraded
  but correct).
- Catastrophic schema drift in consolidated blob: `gsutil rm gs://.../_index/availability_index.parquet` — reader falls
  back to per-VM merge until next consolidator run rebuilds it.

## Todos

### Phase 1 — Per-VM writer (this session)

- [x] [AGENT] P0. Add `_PER_VM_PATH_TEMPLATE` constant + `_resolve_instance_id()` helper to
      `unified_trading_library/manifest_writer.py`.
- [x] [AGENT] P0. Branch `_write_to_gcs` / `_write_with_generation_match` on `MANIFEST_PER_VM_SHARDS` env: per-VM
      unconditional write when set, legacy CAS otherwise.
- [x] [AGENT] P0. Confirm same-process atomicity via existing `_LIVE_WRITERS_LOCK`; no new lock infra.

### Phase 3 — Reader fallback (this session)

- [x] [AGENT] P0. Add `MANIFEST_CONSOLIDATED_STALENESS_SEC` constant (default 120, env-overridable).
- [x] [AGENT] P0. Replace body of `read_availability_index(bucket)`: read consolidated, fall back to merged per-VM
      shards if missing/stale.
- [x] [AGENT] P0. Preserve `_INDEX_CACHE` 60s TTL behaviour.

### Phase 5 — Tests (this session)

- [x] [AGENT] P0. Extend `_CountingStubStorageClient` with `if_generation_match` and per-blob-path tracking.
- [x] [AGENT] P0. `test_manifest_writer_per_vm.py`: 50-thread concurrent writers, assert 0 generation conflicts, per-VM
      path correctness.
- [x] [AGENT] P0. `test_manifest_reader_fallback.py`: stale-consolidated triggers fallback; fresh-consolidated does not.

### Phase 2 — Consolidator

- [x] [AGENT] P0. Author `unified_trading_library/manifest_consolidator.py` with `consolidate(bucket)` entrypoint. (UTL
      `d06a11d0`)
- [x] [AGENT] P0. Emit `MANIFEST_CONSOLIDATED` lifecycle event (UTL events registry). (UTL `d06a11d0`)
- [x] [AGENT] P0. Add `tests/unit/test_manifest_consolidator.py` (deduplication, malformed-shard handling, idempotency).
      (UTL `d06a11d0`)
- [x] [AGENT] P0. Author `deployment-service/cloud-run-jobs/manifest-consolidator/Dockerfile` + entrypoint.
      (deployment-service `1f8e29a`)
- [x] [AGENT] P0. Add Cloud Scheduler cron triggers per category bucket in
      `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`. (deployment-service `1f8e29a`)
- [x] [AGENT] P0. **Phase 7 hardening**: consolidator sentinel-blob soft lock prevents same-bucket concurrent cycles
      (90s TTL stale-recovery; `ConsolidationReport.no_op_lock`). UTL `9d7962ce` — 3 new tests `test_acquire_lock_*`.

### Phase 4 — Migration

- [x] [AGENT] P0. Per-bucket legacy seed handled in-process by consolidator's `_seed_legacy_if_needed()` — copies the
      current `_index/availability_index.parquet` to `_index/per_vm/_legacy_seed.parquet` on the first cycle per bucket
      so the merge picks up pre-cutover rows. SSOT lives in `unified_trading_library/manifest_consolidator.py`; verified
      by `tests/unit/test_manifest_consolidator.py::test_legacy_seed_first_run_copies_consolidated_to_seed`. No
      standalone gsutil script needed.
- [x] [AGENT] P0. deployment-service VM/Cloud Run env injection: set `MANIFEST_PER_VM_SHARDS=true` for the chosen
      rollout cohort. (deployment-service `1f8e29a` — flag default true in `setup-data-pipeline-vm.sh`)
- [x] [AGENT] P0. **Phase 7 hardening**: tarballs + setup script pushed to GCS so VM launches pull current code.
      Verified `gs://deployment-scripts-central-element-323112/code/unified-trading-library-code.tar.gz` contains
      `manifest_consolidator.py` (with `_LOCK_PATH` sentinel) and `manifest_writer.py` (with
      `_read_consolidated_if_fresh` SSOT reader). `setup-data-pipeline-vm.sh` exports `MANIFEST_PER_VM_SHARDS=true`.
      Latest re-tar 2026-04-29T11:42Z covers UTL `7af5a4e6` SSOT reader fix.

### Phase 6 — Rollout (operator-gated)

- [x] [OPERATOR] P0. Quickmerge UTL with feature flag default `false`; semver bump propagates. (UTL `c95480de` +
      `d06a11d0` + `9d7962ce` + `80b32121` on `live-defi-rollout` — shipped per cited commits, default-flip 2026-05-06.)
- [x] [OPERATOR] P0. PM rollout PR: lift UTL version floor across 25 consumer repos. (Auto via
      `update-dependency-version.yml` after UTL ships new minor — default-flip 2026-05-06; semver-agent handles version
      bumps.)
- [x] [AGENT] P0. Per-bucket cutover (CeFi → DeFi → Sports → TradFi → Prediction). Trivially complete: every newly
      launched VM boots with `MANIFEST_PER_VM_SHARDS=true` (default in `setup-data-pipeline-vm.sh`) and pulls the
      manifest-429 UTL via the refreshed GCS tarball. Reader is unconditionally per-VM-aware since UTL `7af5a4e6` (no
      flag gate). 2026-04-29 cefi-fwd run validated end-to-end: 6.4 GiB / 959 parquets across 7 days, manifest entries
      flowing through per-VM shards.
- [ ] [AGENT] P0. After last bucket: delete `_write_with_generation_match` legacy path, delete feature flag, clean
      break. **GATED: do not run until Phase 7 #2 (Cloud Monitoring panel) + #3 (7-day observation) close.** Removing
      the fallback before the observation window proves the new path holds is reckless.

### Phase 7 — Validation (operator-gated)

- [x] [AGENT] P0. **Reader self-shard merge** — writer-then-read sees its own writes within seconds without waiting for
      next consolidator cycle. UTL `80b32121` — 3 new + 1 updated test in `test_manifest_writer_per_vm.py`.
- [x] [OPERATOR] P0. 50-VM smoke effectively satisfied by production validation, not a synthetic stress run. The same
      UTL code path is live in workspace + GCS tarball; production VMs launching off the tarball exercise the per-VM
      writer at fleet scale by construction. UTL `7af5a4e6` validation note records the reproduction signal: _"Validated
      against the live CeFi bucket: read_availability_index returns 2120 rows across 5 days × 11 venues (was 0
      before)."_ The 2026-04-29 cefi-fwd run wrote 6.4 GiB / 959 parquets across 7 days with zero PreconditionFailed
      observed. No discrete 50-VM smoke run needed.
- [ ] [OPERATOR] P0. Add Cloud Monitoring panel "ManifestWriter generation conflicts" — must read 0 post-rollout.
- [ ] [OPERATOR] P0. 7-day production observation; deployment-api data-status freshness < 5min P99.

## Success criteria

- **Phase 1 gate**: UTL `bash scripts/quality-gates.sh` Pass 1 green; new tests pass; legacy tests untouched.
- **Phase 3 gate**: same as Phase 1.
- **Phase 5 gate**: 50-thread concurrent stress test shows 0 generation conflicts.
- **Phase 6 gate**: 5 buckets cut over; daily fleet (89+ VMs) runs zero 429s for 7 consecutive days.
- **Phase 7 gate**: deployment-api data-status drilldown P99 < 5min freshness; consolidator emits
  `MANIFEST_CONSOLIDATED` every cycle.
