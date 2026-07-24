---
doc_type: plan
title: manifest-v7-schema-migration-design-2026-05-08
summary:
status: complete
nature: record
asset_group: cross-cutting
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related:
  [
    live_pipeline_mtds_mdps_features_2026_05_08,
    writegate_honest_coverage_endtoend_2026_05_06,
    gcs_migration_bundle_pipeline_mode_2026_05_08,
  ]
created: 2026-05-08
type: plan
plan_type: design
owner: ikenna
priority: P0
last_updated: 2026-05-08
parent: gcs_migration_bundle_pipeline_mode_2026_05_08
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

> **🔴 SUPERSEDED 2026-05-10 by [`manifest_schema_final_gate_2026_05_09.md`](manifest_schema_final_gate_2026_05_09.md)**
> — the no-fallback maximalist path supersedes this plan's 30-day grace strategy. See final-gate plan Phase 1.A for
> ratified `ServiceEmissionStateEnum` + Phase 7 for migration sequencing. This file remains in `plans/active/` for
> design archaeology only; **not actionable**. Per Audit B governance sweep 2026-05-10.

> **🟡 FOLDED INTO UMBRELLA — `manifest_evolution_master_2026_05_08`** (codified 2026-05-08)
>
> This plan's manifest-touching scope MUST execute as part of the umbrella's gate sequence — NOT in isolation. Operator
> direction: "manifest, code, and data migrate in the same group plan to avoid collision risk; force batch execution;
> don't allow execution in isolation." Three-axis invariant: schema (UAC) + writer code (UTL + adapter callsites) + GCS
> data layout co-evolve.
>
> Child of: [`plans/epics/manifest_evolution_master_2026_05_08.md`](../epics/manifest_evolution_master_2026_05_08.md)
>
> This plan's phases land in gate(s): **G4** (v8 schema atomic rename + immutable service_emission_state — fallback
> grace period REJECTED per CLAUDE.md SSOT)

# Manifest v7 → v8 schema migration — design (2026-05-08, Tab 3 separate scope)

> **STATUS — DRAFT.** Pending Tab 2 (live_pipeline) Phase 11 slice b spec for the exact `ServiceEmissionStateEnum` value
> set + manifest-read protocol. This doc captures the column shape Tab 3 owns; Tab 2's slice b will fill the closed-set
> values + the read protocol.

## Why

`v6` extended the manifest with `quote_asset / margin_type / combo_type / leg_weights` (DERIBIT inverse vs linear
disambiguation + multi-leg synthetic instruments). `v7` already shipped per UTL@`ed658e9b` adding `fixture_id` (sports
per-fixture shard atom) + `job_id` (ML / strategy / execution experiment-keyed services). The next bump (`v8`) needs to
formalise per-`(shard_key, day)` `ServiceEmissionPolicy` state ties to writegate Phase 4 typed-error rendering +
live_pipeline Phase 12 batch-vs-live reconciliation gate. The
[gcs_migration bundle](gcs_migration_bundle_pipeline_mode_2026_05_08.md) Phase 1A already added `pipeline_mode` as a
manifest column; that lands as part of the v8 schema upgrade.

## v8 columns (proposed)

| Column                             | Type                               | Nullability    | Source / setter                                        |
| ---------------------------------- | ---------------------------------- | -------------- | ------------------------------------------------------ |
| `pipeline_mode`                    | `str` (UAC `PipelineMode` enum)    | `None` allowed | Writer at `record_*` time (Phase 1B kwarg, shipped).   |
| `service_emission_state`           | `str` (`ServiceEmissionStateEnum`) | `None` allowed | Emission-policy hook at write-and-publish boundary.    |
| `last_emission_decision_at`        | timestamp ISO-8601                 | `None` allowed | Same hook; ms precision UTC.                           |
| `expected_window_completeness_pct` | `float` 0.0–1.0                    | `None` allowed | Hook computes `actual_rows / expected_rows` per shard. |

`ServiceEmissionStateEnum` (closed-set, owned by UAC; values pending Tab 2 Phase 11 slice b spec):

- `PUBLISHED_OK` — full window observed, normal cascade fan-out.
- `PUBLISHED_DEGRADED` — partial window with declared-degraded policy (live_pipeline tier-up wiring).
- `STALE_DATA_HEARTBEAT_ONLY` — emission policy decided to suppress rather than publish stale.
- `BLOCKED` — circuit breaker tripped; downstream paused.

Default for unseeded `(service, output_data_type)` pairs is `STRICT_FAIL` (per UAC@58c3b61 service_emission_policy.py).
Migration of existing v7 rows: backfill `service_emission_state=None`, `last_emission_decision_at=None`,
`expected_window_completeness_pct=None`. Reader treats `None` as "v7 row, pre-policy hook" — preserves backward-compat
during the migration window per CLAUDE.md "Manifest migration, NOT fallback" rule.

## Migration strategy (1-time script + reader removal)

Precedent: `instruments-service/scripts/migrate_local_sfi_to_canonical.py` +
`unified_trading_library/manifest_migrations` helpers (`ManifestMigrator`, `chunked_date_ranges`, `RescanScanner`,
`LegacyRowPurger`) already in use by the `gcs_migration_bundle_2026_05_08.py` Phase 2 script.

Steps:

1. **Stage 1 — schema-bump commit**: UTL `manifest_writer.py` adds 3 new columns to `_ROW_KEY_COLUMNS` +
   `AvailabilityRecord`; readers behind feature-flag gate (`MANIFEST_V8_READS=true` env var) tolerate missing columns.
2. **Stage 2 — migration script**: `unified-trading-pm/scripts/migration/manifest_v7_to_v8_2026_05_XX.py` walks the
   canonical `_index/availability_index.parquet` per bucket, adds 3 NULL columns to every existing row, writes a per-VM
   shard at `_index/per_vm/v7_to_v8_migrate_{VM_NAME}.parquet`. Per-VM shard isolation MANDATORY
   (`MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique>`).
3. **Stage 3 — manifest consolidator merges per-VM shards into canonical**: existing daemon. Last-writer-wins on
   row_key.
4. **Stage 4 — service emission policy hooks wire**: writegate Phase 4 + live*pipeline Phase 11 slice c sweep adds
   policy-hook calls at every `record*\*` site that should populate the 3 new columns.
5. **Stage 5 — reader feature-flag flip**: `MANIFEST_V8_READS=true` becomes default; v7-only readers raise
   `ManifestVersionMismatchError`.
6. **Stage 6 — fallback removal (T+30d)**: per workspace "no double SSOT" rule. `MANIFEST_V8_READS` flag deleted.

## Reader fallback strategy (≤30 days post-Stage-5)

v8 readers fall back to v7 reads if any of the 3 new columns is missing on disk; emit
`READER_BACKFILLED_V8_COLUMNS_AS_NULL` event so we monitor when fallbacks are no longer needed. After 30 days of zero
events, the fallback is deleted. Mirrors the gcs_migration plan's Phase 5.1 + Phase 8 contract for the `pipeline_mode=`
partition.

## Cross-tab dependency — 🟡 BLOCKED

Tab 2 (live_pipeline) Phase 11 slice b owns the manifest-read protocol coupled to `ServiceEmissionPolicy`. Specifically
this design needs slice b to specify:

1. The exact `ServiceEmissionStateEnum` value set (proposed 4-value above is a starting point).
2. The semantics of `expected_window_completeness_pct` (denominator = catalog × dates? × data_types? Per shard atom?).
3. The read-time priority when v8 row has `service_emission_state=BLOCKED` (consumer skips? error-out? read with a
   degraded flag?).

Until slice b ships, this design stays DRAFT and Stage 1 schema-bump commit is gated on slice b's enum + read protocol.

## Codex SSOT updates (when not DRAFT)

Per CLAUDE.md "Post-Plan-Phase Codex Audit HARD RULE":

- **UPDATE** `/codex/02-data/availability-manifest-and-data-status.md` — add v8 section after v8 `pipeline_mode` block;
  describe the 3 new columns + reader migration window.
- **NEW** `/codex/04-architecture/service-emission-policy.md` — describe the 4-state lifecycle, hook insertion points,
  consumer behaviour. Stub created at slice-a ship; expanded here.
- **UPDATE** `codex/00-SSOT-INDEX.md` — register the new emission-policy doc.
- **CROSS-LINK** `/codex/02-data/pipeline-mode-partition.md` Shipped Progress table to point at this v8 design once it
  exits DRAFT.

## Temporary states + their canonical follow-up plans

- `ServiceEmissionStateEnum` value set is **PROPOSED** here (4 values). Final closed set lands in UAC after Tab 2 slice
  b spec — this design ratifies the slice b output. Successor: live_pipeline_mtds_mdps_features_2026_05_08 Phase 11
  slice b.
- Stage 1 schema-bump is GATED on slice b. Once slice b ships, this design moves DRAFT → ACTIVE and Stage 1 commits.

## Open questions

- Q1 [tab3-gcs-migration, 2026-05-08] — Tab 2 Phase 11 slice b spec status? Need closed-set values for
  `ServiceEmissionStateEnum`. **Status**: 🟡 BLOCKED — waiting on Tab 2 sub-agent / live_pipeline plan flip for slice b.
- Q2 [tab3-gcs-migration, 2026-05-08] — `expected_window_completeness_pct` denominator: catalog cross-product or
  shard-atom-specific? Defer to Tab 2 slice b.

## Cross-plan coordination

- `live_pipeline_mtds_mdps_features_2026_05_08` Phase 11 slice b — STRICT BLOCKER on this design exiting DRAFT.
- `writegate_honest_coverage_endtoend_2026_05_06` Phase 4 (typed-error rendering) consumes
  `service_emission_state=BLOCKED` to switch UI from "missing" to "circuit-breaker" semantics.
- `gcs_migration_bundle_pipeline_mode_2026_05_08` Phase 1A — `pipeline_mode` column shipped here; v8 includes it.
- `infrastructure_master_2026_05_07` umbrella — folds-in this v8 design once not DRAFT.
