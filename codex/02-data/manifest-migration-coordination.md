---
title: Manifest Migration Coordination
status: active
created: 2026-05-07
last_updated: 2026-05-12
authoritative_for:
  How a workspace-wide manifest migration (schema bump, vocab change, hive-key change) coordinates across cross-asset
  rescan jobs, per-VM shard isolation, and the consolidator daemon. Defines safe-window protocol + rollback procedure so
  concurrent agents don't clobber the migration.
referenced_by:
  - plans/epics/manifest_migration_master_2026_05_07.md
  - plans/active/manifest_schema_final_gate_2026_05_09.md
related:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/02-data/pipeline-mode-partition.md
---

# Manifest Migration Coordination

> **Status (refreshed 2026-05-12 per codex audit D-12):** ACTIVE. Body expanded from outline-only stub. Owns the
> sequencing contract for the v7 → v8 cutover (`MANIFEST_SCHEMA_VERSION` constant bump + `None`-default removal +
> reader-fallback retirement). Current runtime SSOT: `MANIFEST_SCHEMA_VERSION = 7` in
> `unified-trading-library/unified_trading_library/manifest_writer.py:131` (transitional; column shape is already v8 —
> see [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md) § "Schema v8 (current;
> ratified 2026-05-09)" Temporary-state block).

## Purpose

When the manifest schema or canonical row shape changes (the precedent: v3 → v5 with `capture_status` + `error_reason`
columns), there is a multi-day window where adapters on `live-defi-rollout` write the new shape, the consolidator daemon
merges per-VM shards, and any concurrent backfill VMs in flight could write the OLD shape. This doc is the SSOT for
sequencing that change so we never have a moment where canonical manifest drifts irrecoverably.

## Scope

- Schema bumps to `_index/availability_index.parquet` (column adds, drops, renames).
- Vocab changes (e.g. asset-group rename, chain-key change).
- Hive-key changes (e.g. `category=` → `asset_group=`).
- Consolidator daemon coordination — pause / drain / resume.
- Rollback procedure when a migration is found broken mid-flight.

## Migration phases — preflight → freeze → migrate → verify → unfreeze

### Phase 1 — Preflight (T−24h)

- Owner agent posts a cross-plan banner (`> **🟡 IN-FLIGHT REFACTOR — manifest v7→v8 cutover starts <YYYY-MM-DD HH:MM
  UTC>**`) on every active plan whose work touches manifest reads or writes (per CLAUDE.md "Cross-Plan Coordination
  Banners" rule).
- Pre-flight grep workspace-wide for `MANIFEST_SCHEMA_VERSION` literal + `record_captured(...)` callsites missing the
  v8 kwargs; the pre-audit manifest goes into the active plan body.
- Snapshot `_index/availability_index.parquet` (GCS object-versioning is the snapshot mechanism).
- Confirm zombie watchdog has drained all per-VM shard backfills; `gcloud compute instances list` shows zero
  manifest-writing VMs in either region.

### Phase 2 — Freeze (T0)

- Pause consolidator daemon: SIGTERM `manifest-consolidator-*` VM in both `asia-northeast1` (GCP) and `ap-northeast-1`
  (AWS). Confirm `STOPPED` event in `gs://{pid}-events/events/manifest-consolidator/...`.
- Reject new manifest writes at writer-layer guard: `ManifestWriter.__init__` raises `ManifestFrozenForMigrationError`
  when a sentinel file `gs://{pid}-manifest/_index/MIGRATION_IN_PROGRESS.lock` is present. The lock file carries the
  freeze-start ISO timestamp + owner agent's plan filename.
- Reads continue (UI + downstream consumers); `read_availability_index()` is not affected.

### Phase 3 — Migrate (T0 → T0+freeze-window)

- Run the one-shot migration script (idempotent + CAS-on-write — precedent:
  `instruments-service/scripts/migrate_local_sfi_to_canonical.py`). For v7→v8: explicit-or-fail removal of the four
  `None`-default kwargs from `record_*` (`pipeline_mode` / `service_emission_state` / `last_emission_decision_at` /
  `expected_window_completeness_fraction`), driven by
  [`plans/active/manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md)
  Phase 4.DEFAULT-REMOVAL.
- Drain `_index/per_vm/*.parquet` per-VM shard files into canonical `_index/availability_index.parquet` FIRST; assert
  empty after (`gsutil ls _index/per_vm/` returns no objects). Multi-worker per-VM shard isolation contract is in
  [`availability-manifest-and-data-status.md`](./availability-manifest-and-data-status.md) § "Per-VM shard isolation".

### Phase 4 — Verify

- Schema check: post-migration `_index/availability_index.parquet` columns set-equals the v8 column set declared in
  `AvailabilityRecord`. `MANIFEST_SCHEMA_VERSION` constant in UTL is now `8`.
- Per-asset-group row-count parity vs pre-migration snapshot (≤0.01% drift; any drift > 0 requires explicit owner
  acknowledgement in the active plan body).
- Downstream-consumer smoke: deployment-api `/api/data-status/shard-detail?service=&category=&day=&...` returns
  success on a sample (asset_group, venue, data_type, day) tuple per asset_group (5 samples; one per asset_group).
- Sample-parquet inspection per asset_group: read 3 random rows × 5 asset_groups, assert non-NaN core columns
  (`available_at`, `pipeline_mode`, `service_emission_state`). Reference-incident gate (2026-05-05 MDPS 1440-NaN
  bars): row-count alone is insufficient.

### Phase 5 — Unfreeze

- Delete `gs://{pid}-manifest/_index/MIGRATION_IN_PROGRESS.lock`.
- Resume consolidator daemon (relaunch `manifest-consolidator-*` VMs).
- Owner agent removes the `🟡 IN-FLIGHT REFACTOR` banner from every plan it was added to (same logical unit as the
  unfreeze commit).
- Backfill VMs resume from their stored checkpoints; QG STEP 5.66 (per-VM shard isolation) continues to enforce.

### Reader fallback removal (T0+30d)

Once verification holds for 30 calendar days AND the `READER_FELL_BACK_TO_LEGACY_PATH` event-count is zero for 7
consecutive days, the v7-shape fallback in `read_availability_index()` is deleted (workspace rule "manifest migration
NOT fallback" — also see [`pipeline-mode-partition.md`](./pipeline-mode-partition.md) § "Reader fallback chain"). The
deletion is the final phase of
[`plans/active/manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md)
Phase 7.

## Rollback procedure

If verification (Phase 4) detects drift > 0.01% OR any sample parquet returns NaN core columns OR any downstream-smoke
endpoint returns 5xx:

1. Re-acquire the `MIGRATION_IN_PROGRESS.lock` (writes stay frozen).
2. Restore `_index/availability_index.parquet` from GCS object-versioning to the pre-migration snapshot.
3. Revert `MANIFEST_SCHEMA_VERSION` constant in UTL to `7` + re-add the `None`-default kwargs in `record_*` methods.
4. Notify operator immediately (the rollback IS the "big finding" per CLAUDE.md "Findings Triage Discipline" rule).
5. File a post-mortem under `plans/active/issues/manifest_v7_v8_rollback_<YYYY_MM_DD>.md` with the rollback diagnostic
   + root cause + corrective plan reference.

Rollback window: pre-migration snapshot retained in GCS object-versioning for 7 days post-migration.

## Multi-agent coordination

- Freeze window broadcast: cross-plan banner (see Phase 1 above) + `plans/active/_agent_pings.md` entry tagged
  `[manifest-migration]`.
- Verify no rogue backfill VM at freeze-start: `gcloud compute instances list` + `aws ec2 describe-instances` both
  return zero matching `*-mtds-*` / `*-mdps-*` / `*-features-*` / `*-instruments-*` running instances.
- The freeze window IS a Plans-Run-To-Actual-Completion gate (per CLAUDE.md HARD RULE) — code-shipped migration is not
  operationally-shipped until Phase 5 unfreeze + Phase 4 verification both pass.

## Cross-references

- **Plan(s) implementing this:**
  [`manifest_migration_master`](../../plans/epics/manifest_migration_master_2026_05_07.md).
- **Related codex SSOTs:** [`availability-manifest-and-data-status`](./availability-manifest-and-data-status.md),
  [`honest-absence-downstream-handling`](./honest-absence-downstream-handling.md).
- **Code:** `unified-trading-library/manifest_writer.py`, consolidator daemon under `manifest-consolidator-*` VM,
  migration scripts in `instruments-service/scripts/`.

## Open questions

- Typical freeze-window duration is plan-specific; precedent: v3→v5 was ~2 hours; v7→v8 estimate documented in
  [`manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md) Phase 4.
- Shadow-consolidator parallel run: implement as future-work if v7→v8 verification fails on first attempt; not in
  scope for the v7→v8 cutover itself.
- Rollback window: GCS object-versioning is canonical (7 days); full backup-bucket copy is NOT required.
- Staging-environment dry-run: full-fidelity manifest copy lives in staging GCS; dry-run sequencing is the same
  Phase 1-5 with staging buckets — owner agent runs once before prod.
