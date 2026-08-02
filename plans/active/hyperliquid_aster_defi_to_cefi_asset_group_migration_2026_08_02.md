---
doc_type: plan
title: Migrate frozen HYPERLIQUID + ASTER legacy asset_group=defi corpus to asset_group=cefi
summary:
  HYPERLIQUID and ASTER were removed from ALL_DEFI_VENUES/DEFI_VENUE_PHASE on 2026-06-21 (both are code-classified pure
  CEFI today), but a frozen historical corpus written before that cutover still sits under asset_group=defi in
  GCS/manifest. Migrate it to asset_group=cefi so data agrees with the code-level classification, mirroring the
  solana_defi_legacy_migration_2026_05_27 gate pattern.
status: draft
nature: process
asset_group: [cefi, defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags: [migration, asset-group, canonicalisation, cefi, defi, hyperliquid, aster, manifest]
related:
  [
    plans/active/issues/defi_code_codex_drift_2026_05_27.md,
    /plans/archive/2026_07/solana_defi_legacy_migration_2026_05_27.md,
    /plans/archive/2026_07/aster_cefi_data_defi_bucket_migration_2026_07_13.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-02
parent_epic: mtds_mdps_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  [
    plans/active/issues/defi_code_codex_drift_2026_05_27.md (D15),
    operator decision 2026-07-27 (keep HYPERLIQUID/ASTER pure CEFI; migrate the frozen legacy defi-labeled corpus),
  ]
context_scope:
  [
    /plans/active/issues/defi_code_codex_drift_2026_05_27.md,
    /plans/archive/2026_07/solana_defi_legacy_migration_2026_05_27.md,
    /plans/archive/2026_07/aster_cefi_data_defi_bucket_migration_2026_07_13.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
last_updated: 2026-08-02
locked_by:
locked_since:
supersedes:
superseded_by:
---

# Migrate frozen HYPERLIQUID + ASTER legacy `asset_group=defi` corpus → `asset_group=cefi`

> **🟡 STATUS: draft — NOT dispatched.** Per CLAUDE.md "Plan destination — ASK BEFORE CREATING (HARD RULE)", a new plan
> defaults to a human plan (`assigned_vm: NA`) unless the operator explicitly asks for AO dispatch. This plan scopes
> D15's remaining work (`plans/active/issues/defi_code_codex_drift_2026_05_27.md`); flip `status: active` +
> `assigned_vm: planning` once the operator confirms AO dispatch is wanted (this is heavy-GCS-I/O + VM-launch work —
> `execution_scope`/delete-safety still apply either way).

## Background

`defi_code_codex_drift_2026_05_27.md` D15: HYPERLIQUID and ASTER were fully removed from `ALL_DEFI_VENUES`/
`DEFI_VENUE_PHASE` on 2026-06-21 (`unified-api-contracts@0d0e00a89`, fixing a 48.5k `attempted_failed` regression) and
`perp_funding_handler` itself was retired 2026-07-08. Operator decision (2026-07-27, pre-June-1 stale-plans audit): keep
both venues pure CEFI in code (do not dual-classify in UAC). Confirmed live 2026-08-02 (`unified-api-contracts` registry
grep): neither venue appears in the DeFi venue/capability registries anymore; both are CEFI-classified
(`data_availability.py`, `cefi_instrument_universe.py`, `cefi_perp_venue_endpoints.py`).

**This is a DIFFERENT bug class than `aster_cefi_data_defi_bucket_migration_2026_07_13.md` (archived, complete)** — that
plan fixed ASTER data that was correctly _labeled_ `asset_group=cefi` but landed in the wrong _bucket_. This plan's
corpus is _labeled_ `asset_group=defi` (wrong label, an artifact of the pre-2026-06-21 DeFi classification) and needs
relabeling, not just a bucket move.

## Verified live (2026-08-02, bounded per-day targeted prefix checks — NOT a whole-corpus walk)

`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day={D}/pipeline_mode={batch_hyperliquid|batch_aster}/asset_group=defi/venue={HYPERLIQUID|ASTER}/...`

| Venue       | Chain       | Sample day with data                                                           | First confirmed zero-object day                                                |
| ----------- | ----------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| HYPERLIQUID | HYPERLIQUID | 2026-05-30 (`perp_daily_ctx`, 231 objs), 2026-06-05 (`perp_funding`, 231 objs) | 2026-06-20 (checked through 2026-08-01, all zero)                              |
| ASTER       | BSC         | 2026-06-05 (`perp_funding`, 458 objs)                                          | 2026-05-30 has 0 (data starts later in the window), 2026-06-20 onward all zero |

Confirms: **the corpus is frozen, not actively growing** — safe for a one-time migration with no live-write race to
coordinate with (unlike the Solana precedent, which had to pause a live cron first). At least two `data_type`s exist per
venue (`perp_funding`, `perp_daily_ctx` seen for HYPERLIQUID) — Phase 1 Todo 1 below does the full enumeration. D15
cites row-count estimates from its 2026-07-27 pass (HYPERLIQUID/HYPERLIQUID: 3.77M rows through 2026-05-31; ASTER/BSC:
1.07M rows through 2026-05-31) — treat as directional pending Phase 1's fresh count.

## Gates (mirrors `solana_defi_legacy_migration_2026_05_27` — HARD-ORDERED, do not delete legacy before verified)

### Phase 1 — Confirm scope + build the migration script (P1)

- [ ] [DATA] P1. Full day-by-day, data_type-by-data_type object count for both venues across the entire
      `asset_group=defi` window (targeted prefix listing per day — reuse the per-day-parallel pattern from
      `scripts/audit_aster_cefi_in_defi_bucket_scope_2026_07_13.py`, NOT a whole-bucket scan). Write result to
      `_index/audit/hyperliquid_aster_defi_asset_group_scope_2026_08_0X.parquet` (mirrors that script's output
      convention). Confirm exact first/last day with data per venue + enumerate every `data_type` present (at least
      `perp_funding` + `perp_daily_ctx` confirmed above; check for `derivative_ticker`/`trades` too — the retired
      `_perp_funding_hl_aster.py` staged more than one leg per the archived ASTER-bucket plan's root-cause note).
- [ ] [DATA] P1. Confirm the canonical CEFI-bucket target path shape for these two venues + data_types (same
      `resolve_bucket_name(asset_group="cefi")` pattern the ASTER-bucket-placement migration used) and whether a
      canonical-twin already exists anywhere (parity check by `(size, crc32c)`, never existence-only — same rule the
      ASTER precedent enforced after finding per-day symbol gaps even in its "near-100%-duplicated" window).
- [ ] [DATA] P1. Write the migration script (new sibling under `market-tick-data-service/scripts/`, e.g.
      `migrate_hyperliquid_aster_defi_asset_group_2026_08_0X.py`) — same-bucket-or-cross-bucket copy (whichever the
      Phase-1-Todo-2 answer requires) from `asset_group=defi` to `asset_group=cefi`, same relative
      day/pipeline_mode/venue/chain/instrument_type/data_type partitions otherwise unchanged unless the canonical
      CEFI-bucket shape differs. `--dry-run` default, `--apply` to mutate, idempotent parity-checked skip — same
      convention as every prior `migrate_*` script in this dir (`migration_common.py` helpers). Never deletes the
      `asset_group=defi` source (Phase 4, separate operator-gated step).

### Phase 2 — Execute the migration (P1, VM — heavy I/O, not local-machine)

- [ ] [OPERATOR] [INFRA] P1. Launch a dedicated VM (or reuse an existing backfill-class launcher pattern) to run the
      Phase-1 script `--apply` against the full window. No live cron to pause first (corpus confirmed frozen above).
      Verify STARTED <60s + ≥1 progress/hr + a terminal STOPPED/completion signal (no fire-and-forget). Cite the VM
      name + zone + run.log path here on completion.
- [ ] [DATA] P1. Post-migration parity re-verification: sample-inspect migrated rows in the CEFI-bucket target (correct
      `instrument_id`, correct partition path, row/byte counts match Phase 1's audit).

### Phase 3 — Manifest reconcile (P1)

- [ ] [DATA] P1. Force-fire (or wait for) the manifest consolidator on the affected buckets; confirm the availability
      index shows the migrated rows under `asset_group=cefi` for HYPERLIQUID/ASTER, and that the stale
      `asset_group=defi` manifest rows for these two venues are flagged for pruning in Phase 4 (do not prune before
      Phase 4's GCS delete — manifest and object state must move together, per the delete-safety protocol).

### Phase 4 — Delete legacy `asset_group=defi` originals (P0, OPERATOR-GATED)

- [ ] [OPERATOR] [DATA] P0. After Phase 2/3 verified GREEN, delete the migrated `asset_group=defi` HYPERLIQUID/ASTER
      objects (via `gcs_delete_object`, never subprocess `gcloud`/`gsutil`) + prune the corresponding manifest rows.
      Cite `Evidence:` per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — this is a real prod-bucket
      delete on canonical data, human-gated per CLAUDE.md's delete-safety rule (no reversibility shortcut applies here —
      this isn't a soft-delete-retention-window case, it's an intentional permanent removal of the duplicate).

### Phase 5 — Close-out (P2)

- [ ] [DOC] P2. Flip D15 in `defi_code_codex_drift_2026_05_27.md` to ✅ RESOLVED, citing this plan's completion
      evidence. Update `/codex/02-data/defi-data-pipeline.md` / `defi-canonical-naming-ssot.md` if either still
      documents HYPERLIQUID/ASTER as dual-classified or `asset_group=defi`-resident.

## Not in scope

- Any change to the CURRENT (post-2026-06-21) CEFI collection path for HYPERLIQUID/ASTER — that is already correct and
  unaffected by this migration (this plan only touches the frozen pre-cutover legacy corpus).
- The `aster_cefi_data_defi_bucket_migration_2026_07_13` bucket-placement bug — already fixed + archived, unrelated
  mechanism (that corpus was mislabeled by bucket, this corpus is mislabeled by `asset_group`).

## Progress Log

- 2026-08-02: Plan authored (slot 10, data_engineering task `defi_code_codex_drift-001`) to scope D15's remaining work
  per its own "not yet scoped — stays [~] until migration plan exists" note. Verified live: HYPERLIQUID + ASTER absent
  from all DeFi UAC registries (pure CEFI in code); frozen legacy `asset_group=defi` corpus confirmed still present in
  GCS (bounded per-day checks, not a full walk) with writes stopped between 2026-06-05 and 2026-06-20. Filed
  `status: draft` / `assigned_vm: NA` per the ask-before-creating default (no operator round-trip available in this
  dispatch).
