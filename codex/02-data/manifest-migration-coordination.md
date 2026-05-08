---
title: Manifest Migration Coordination
status: planned
created: 2026-05-07
authoritative_for:
  How a workspace-wide manifest migration (schema bump, vocab change, hive-key change) coordinates across cross-asset
  rescan jobs, per-VM shard isolation, and the consolidator daemon. Defines safe-window protocol + rollback procedure so
  concurrent agents don't clobber the migration.
referenced_by:
  - plans/epics/manifest_migration_master_2026_05_07.md
related:
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/02-data/honest-absence-downstream-handling.md
---

# Manifest Migration Coordination

> **Status:** PLANNED — stub created 2026-05-07 to anchor forward-references from active plans. Body to be filled in as
> the next manifest-schema bump (v7 → v8 — `pipeline_mode` + `service_emission_state` + `last_emission_decision_at` +
> `expected_window_completeness_pct` per
> [`manifest_v7_schema_migration_design_2026_05_08.md`](../../plans/active/manifest_v7_schema_migration_design_2026_05_08.md))
> is planned + executed. Current runtime SSOT: `MANIFEST_SCHEMA_VERSION = 7` in UTL
> `unified_trading_library/manifest_writer.py`.

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

## Outline (planned sections)

1. **Migration phases** — preflight → freeze → migrate → verify → unfreeze. Each with go/no-go criteria.
2. **Freeze window** — pause all backfill VMs (zombie watchdog drains them); only the migration script writes during
   freeze. Reads continue (UI + downstream consumers).
3. **Per-VM shard handling during freeze** — drain `_index/per_vm/*.parquet` into canonical first; assert empty after.
4. **Migration scripts** — one-time, idempotent, CAS-on-write. Precedent: `migrate_local_sfi_to_canonical.py`.
5. **Reader fallback removal** — once migration completes, the v5-or-v6 fallback reader is deleted (workspace rule
   "manifest migration NOT fallback").
6. **Verification** — schema check + per-asset-group row-count parity + downstream-consumer smoke (deployment-api
   `_gcs_metadata` returns success on a sample row).
7. **Rollback** — keep pre-migration snapshot of `_index/availability_index.parquet` for 7 days; restore by GCS object
   versioning if verification fails.
8. **Multi-agent coordination** — broadcast freeze window in cursor-configs / Slack; verify no rogue backfill VM at
   freeze-start.

## Cross-references

- **Plan(s) implementing this:**
  [`manifest_migration_master`](../../plans/epics/manifest_migration_master_2026_05_07.md).
- **Related codex SSOTs:** [`availability-manifest-and-data-status`](./availability-manifest-and-data-status.md),
  [`honest-absence-downstream-handling`](./honest-absence-downstream-handling.md).
- **Code:** `unified-trading-library/manifest_writer.py`, consolidator daemon under `manifest-consolidator-*` VM,
  migration scripts in `instruments-service/scripts/`.

## Open questions

- How long is a typical freeze window in practice? (precedent: v3→v5 was ~2 hours; for v5→v6 with much more data, hours
  or a full day?)
- Do we need a "shadow consolidator" running on the new schema in parallel before cutover for confidence?
- What is the rollback window — versioned objects or full backup-bucket copy?
- How do we test the migration without actually freezing prod? (recommend: stage env with full-fidelity manifest copy)
