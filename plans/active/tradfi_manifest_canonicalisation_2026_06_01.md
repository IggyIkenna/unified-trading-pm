---
title: "TradFi manifest + data canonicalisation (v9 + pipeline_mode partition single-walk) — L3 owner for tradfi"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-tradfi
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - defi_manifest_canonicalisation_2026_06_01.md §MASTER CONFLICT-2 (tradfi NOT L3-green: v9 + partition owe a walk)
  - tradfi_massive_dual_source_2026_05_28.md (source col + v8→v9 constant shipped; re-consolidation BLOCKED on drain)
  - _index comparison 2026-06-01 (tradfi DATA ~complete: overlap 12,944/12,948 → only 4 legacy-only cells)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# TradFi manifest + data canonicalisation (L3 owner for tradfi)

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, tradfi lane — resolves **CONFLICT-2**). This
> plan is the tradfi analogue of `defi_manifest`'s §C single-walk. **Single-walk discipline (HARD RULE)**: ONE bundled
> walk on the tradfi `_index` — bundle v8→v9 + `pipeline_mode=` partition + venue/data_type canonical verify +
> `available_at` preserve/backfill, AND absorb the still-owed `source`-field manifest re-consolidation
> (`tradfi_massive_dual_source` Task -031) into THIS same walk. Do NOT open a second walk;
> `pipeline_mode_partition_migration` rides THIS walk.

## Why this exists — tradfi DATA is ~complete but the canonical FORM is NOT landed (CONFLICT-2)

The 2026-06-01 `_index` comparison (legacy `market-data-tick-tradfi-central-element-323112` vs canonical
`market-data-tick-tradfi-prd-…`): legacy `(date,venue,data_type)` cells are ~fully a subset of canonical (overlap
**12,944 / 12,948** → only **4 legacy-only cells**). So at the data-copy level tradfi is **verify-only** — no legacy→
canonical data-loss migration is needed.

**But tradfi is NOT L3-green** (master CONFLICT-2):

- `tradfi_massive_dual_source` reports `source` column + the UTL `MANIFEST_SCHEMA_VERSION=9` **constant** done, but its
  **manifest re-consolidation was `BLOCKED-DEPENDENCY deferred`** (Task -031, blocked on the operator pre-migration
  drain Task -029) — so the LIVE canonical tradfi `_index` still reads **v8** (the manifest-v8 lesson: a constant bump ≠
  data state; read the actual rows).
- The **`pipeline_mode=` on-disk partition** is NOT on the tradfi object paths (`pipeline_mode_partition_migration` is a
  RIDER that must bundle into this walk per master CONFLICT-1).
- Venue / data_type canonical names need a verify pass (the canonical set is already underscore — `trades` / `tbbo` /
  `ohlcv_1m` / `ohlcv_15m` / `options_chain` / `futures_chain` — but the corpus must be confirmed clean of any legacy
  drift before decommission, same discipline as defi C2/C3/C12).
- `available_at` must be preserved where present / backfilled (never regenerated to migration-time) — the lookahead-bias
  invariant.

The hard-to-find-ness IS the bug (master rationale): one bundled walk makes data + manifest + `_index` + data-status all
canonical so the next audit is one pass.

## Scope boundary — what this plan does NOT own (no overlap)

- **`source` write-path + parquet-column backfill** is owned by `tradfi_massive_dual_source_2026_05_28.md` (Phase 5) +
  `data_source_provenance_all_asset_groups_2026_06_01.md` (Phase 7). Per **master CONFLICT-4**, `data_source_provenance`
  **SKIPS tradfi** (source already shipped). This plan only **re-consolidates the already-stamped `source` into the
  `_index`** as a RIDER of the same walk (so the v9 re-consolidation and the owed `source` re-consolidation are ONE
  walk, never two — that is exactly `tradfi_massive` Task -031, executed here).
- **Massive REST connector / dual-source backfill ingestion** stays in `tradfi_massive` (its Phase 5 + Phase 7).
- **Live / WebSocket Massive connector** stays deferred (`tradfi_massive` named successor `tradfi_massive_live_ws_…`).

## Sequencing — canonical migration is a GATE before any tradfi backfill (inherits master HARD RULE)

No tradfi backfill / writer relaunch until this walk is C-GREEN (master L3-gates-L5 + `bucket_name_ssot…` Phase 4). The
walk runs **behind / folded into** the tradfi pre-migration drain (`tradfi_massive` Task -029: drain GCP+AWS writers →
consolidate → snapshot `_index/snapshots/pre_migration_2026_06_01.parquet` → walk → re-consolidate → resume). L0
tarball-prune blocker (`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must be fixed first if run on a
VM.

## Canonical target form (tradfi)

| Dimension       | Legacy / now                                           | Canonical (target)                                                                                 |
| --------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| Bucket          | `market-data-tick-tradfi-{project}` (no env)           | `market-data-tick-tradfi-prd-{project}`                                                            |
| asset-group key | `category=tradfi`                                      | `asset_group=tradfi`                                                                               |
| pipeline_mode   | absent in path                                         | `pipeline_mode=` hive partition (`batch_databento`/`batch_massive`/`batch_yahoo`/`batch_barchart`) |
| schema_version  | live `_index` reads **v8** (constant says 9)           | v9 (re-consolidated — data-state verified, not constant)                                           |
| data_type name  | underscore-canonical (verify clean)                    | `trades`/`tbbo`/`ohlcv_1m`/`ohlcv_15m`/`options_chain`/`futures_chain`                             |
| venue           | ticker / exchange symbol (verify canonical)            | canonical ticker/symbol — flat `venue`                                                             |
| source          | column shipped (`tradfi_massive`); `_index` field owed | `source` re-consolidated into `_index` (RIDER; multi-source = two rows)                            |
| available_at    | per-row exists                                         | preserve where present; backfill only missing from day EOD UTC                                     |

## Phased execution

### P0 — pre-walk audit + scope

- [ ] [DATA] P0. Read the LIVE canonical `tradfi-prd` `_index` **actual `schema_version` distribution** (per-row, not
      the constant — manifest-v8 lesson) + confirm the 4 legacy-only cells are real (objects exist) or phantom. Record
      the row count to re-version.
- [ ] [DATA] P0. Confirm `available_at` is non-null across the corpus (it should be — `tradfi_massive` shipped per-row
      `available_at`); list any null rows the walk must backfill from day EOD UTC.
- [ ] [DATA] P1. Verify the corpus venue / data_type strings are already underscore-canonical (no legacy drift); record
      any non-canonical rows to relabel in the walk (do NOT bulk-rename ambiguous strings — diagnose first).

### C — single-walk (v9 + partition + canonical verify + source re-consolidate)

- [ ] [DATA] P0. C0 ONE bundled walk on the tradfi `_index` + objects: (a) `pipeline_mode=` hive partition added to
      object paths (`pipeline_mode_partition_migration` RIDER — satisfied here, do NOT run separately); (b) re-version
      manifest rows to **v9** (data-state — assert the rewritten rows actually carry 9, not just the constant); (c)
      **`category=`→`asset_group=` across BOTH object PATHS and manifest `_index` ROWS** + env-split bucket for any
      legacy-form rows that remain (CODE side — writers emit `asset_group=` — already shipped via archived
      `venue_axis_asset_group_vocabulary_2026_04_25`; this is historical data+manifest only); (d) venue/data_type
      canonical relabel for any drift found in P0; (e) `available_at` preserve-or-backfill (never migration-time). RUN
      ON A VM via the canonical-migration launcher (gated on L0 tarball-prune fix) — small data scope (≈12,948 cells)
      may run locally if P0 confirms.
- [ ] [DATA] P0. C-source RIDER (absorbs `tradfi_massive` Task -031): re-consolidate the already-stamped parquet
      `source` into the `_index` in THIS walk — every tradfi `_index` row carries `source`; multi-source cells (the 6
      databento+massive/yahoo/barchart cells) emit two rows. Coordinate so `tradfi_massive`'s deferred re-consolidation
      is NOT run as a separate walk.
- [ ] [DATA] P0. C-pipeline_mode RIDER: confirm the `pipeline_mode=` partition for tradfi lands in THIS walk (satisfies
      `pipeline_mode_partition_migration_2026_06_01.md` for tradfi).

### Verify + handoff to decommission

- [ ] [DATA] P0. Post-walk: fresh `_index` read — `schema_version=9` for 100% of rows (data-state), `pipeline_mode=`
      partition present + non-null, venue/data_type canonical only, `source` populated (multi-source = two rows),
      `available_at` non-null. **0 legacy-only cells** (re-run the `(date,venue,data_type)` comparison). This is the
      C-GREEN signal `bucket_name_ssot…` Phase 6/7 waits on for the legacy `market-data-tick-tradfi-…` decommission.
- [ ] [DATA] P1. Notify `tradfi_massive_dual_source` to flip its Task -031 (manifest re-consolidation) — executed here
      as the C-source rider; cross-link both ways.

## Success criteria

- Canonical `tradfi-prd` `_index` = **v9** (data-state verified) + `pipeline_mode=` partition + `source` populated +
  `available_at` non-null; venue/data_type canonical only.
- 0 legacy-only tradfi cells; `tradfi_massive` Task -031 closed (re-consolidation done here).
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy `market-data-tick-tradfi-…` deletable; tradfi writer relaunch
  unblocked (writes canonical-only).

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — tradfi canonical form (v9 + pipeline_mode partition).
