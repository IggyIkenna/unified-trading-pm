---
title:
  "Instruments-service manifest + data canonicalisation (audit-first single-walk) — L3 owner for the instruments I/O
  surface"
created: 2026-06-01
parent_epic: instruments_master
assigned_vm: vm-cross-cutting
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - defi_manifest_canonicalisation_2026_06_01.md §MASTER (per-service canonicalisation axis — instruments was uncovered)
  - canonical_form_cross_service_audit_checklist.md (CF-1…CF-12 — the invariants this walk lands)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Instruments-service manifest + data canonicalisation (L3 owner for the instruments I/O surface)

> **⛔ COORDINATED — you are G1, the ROOT (2026-06-07)** —
> `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` registers this (with
> `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`) as the **IS-catalogue / could-exist-universe foundation**
> that gates every AG's denominator-completeness. IS + UAC together define what COULD exist, so every downstream honest
> denominator + preflight (⑥/⑦) + `expected_unattempted` seed depends on this being GREEN FIRST. G1 lifecycle = code
> (`build_instrument_catalogue` + `enumerate_expected_universe` v2) → per-AG dry-run → `--apply-write` seed (GATED on IS
> backfill complete + accurate UAC + this plan's v9 indices) → daily catalogue scheduler. See the coordinator's "G1
> expanded" section.

> **🔴 P0 GATE (operator 2026-06-05) — the v9 `--apply` here is BLOCKED until
> `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` Phase 0 (code) is GREEN.** Single-walk
> discipline: this corpus walk must carry the new manifest columns — `live_<source>`/`replay_<source>` form, populated
> `source`, `cadence`, `transport` — so running `--apply` before that code lands bakes in the old model + forces a
> banned second whole-corpus walk. **Dry-runs are NOT gated; only the irreversible `--apply`.** (Instruments is
> cross-cutting: reference/fixtures write `batch_<source>` + cadence `scheduled_recurring`, and the IS catalogue FEEDS
> the M3 per-shard availability registry — so IS is also a Phase-0.3 producer, not only a migration target.)

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, per-service axis). Instruments-service is the
> **input (I/O) side** of the data pipeline — it owns reference data (instrument records, universe, fixtures, capability
> snapshots) that everything downstream reads. Its `_index`(es) + objects need the SAME canonical form as the MTDS tick
> buckets. **Single-walk discipline (HARD RULE)**: one bundled walk per instruments bucket — bundle every CF invariant
> (CF-1…CF-12 in `canonical_form_cross_service_audit_checklist.md`). Do NOT open a second walk;
> `pipeline_mode_partition_migration` + `data_source_provenance` ride THIS walk.

> **🟡 FINDING CALLOUT (2026-06-16) — data-status tab audit surfaced download + universe blockers that touch THIS
> migration.** Audit: `plans/audit/results/data_status_tab_and_instruments_download_audit_2026_06_16.md`; remediation
> todos (deployment-api/ui/UAC, NOT owned here): `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md`.
> Three items intersect this plan: (1) **DeFi instruments CSV download 502s** — the deployment-api downloader rebuilds
> the GCS path with the SPLIT manifest venue (`venue=AAVE_V3`) + drops chain, while the writer stores the COMBINED token
> (`venue=AAVE_V3-ETHEREUM`) — the same writer/manifest venue-split this canonicalisation owns; verify the v9 path shape
> keeps writer-object ↔ manifest-row reconstructable. (2) **CeFi universe is a curated allowlist missing EIGEN + 16
> coins** (`unified-api-contracts/.../registry/cefi_instrument_universe.py:19`) — extending it widens the could-exist
> denominator the G1 gate depends on ("GATED on … accurate UAC"); coordinate before the catalogue `--apply-write` seed.
> (3) The audit independently re-confirms this plan's DATA-STATE (v8 flat, ~40% null-`capture_status`-with-count>0,
> capture freeze ~2026-05-21) as the **to-100% path** — no new work, just cross-evidence.

## Why this exists — the per-AG plans cover MTDS, not the instruments surface

The per-AG manifest-canonicalisation plans (defi/cefi/tradfi/sports/prediction) canonicalise the **MTDS**
`market-data-tick-{ag}` buckets. Instruments-service writes a **separate** surface (`instruments-store-{ag}` +
reference/instrument-record indices) that no per-AG plan covers — yet it carries the same legacy debt: `category=` not
`asset_group=`, no `pipeline_mode=` partition, schema_version spread (read DATA-STATE — `pipeline_mode_partition`
already lists `instruments` as pending), `source` in path/blank not column, untyped empty reasons, possible
date-impossible phantom rows. This plan is the instruments analogue of the AG §C single-walk, **audit-first** (we read
the actual instruments `_index` state before migrating — manifest-v8 lesson).

## Scope boundary — no overlap with the per-AG walks

- **`instruments-store-sports`** canonical FORM rides the SPORTS walk: `sports_manifest_canonicalisation_2026_06_01.md`
  (the **slot-4 sports-vertical MASTER orchestrator** — owns ALL sports across IS/MTDS/MDPS/features/execution) already
  claims the sports reference surface + owns the sports-specific CF-5 typed-reason relabel (fixture/season/
  transfer-window/genesis via the sports coverage oracle). This plan does NOT re-walk the sports instruments bucket — it
  provides the cross-service CF audit coverage and owns the **non-sports** AG instruments-store buckets
  (`instruments-store-{cefi,defi,tradfi,prediction}`) + the cross-AG instrument-record/universe indices.
- **`source` write-path code** for sports `FIXTURES` (multi-source) already shipped (instruments-service@6bbd6919 per
  `data_source_provenance` Phase 4); this plan re-consolidates source into the instruments `_index` as a RIDER.
- **MTDS tick buckets** are NOT in scope (per-AG plans own them).

## Sequencing — gate before any instruments backfill (inherits master HARD RULE)

No instruments backfill / writer relaunch until each in-scope instruments bucket's walk is C-GREEN (master L3-gates-L5).
L0 tarball-prune blocker (`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must be fixed first if run on a
VM. Runs behind the pre-migration drain.

## Canonical target form (instruments-service) — per CF-1…CF-12

| Dimension       | Legacy / now                                    | Canonical (target)                                                           | CF    |
| --------------- | ----------------------------------------------- | ---------------------------------------------------------------------------- | ----- |
| Bucket          | `instruments-store-{ag}-{project}` (verify env) | `instruments-store-{ag}-{env}-{project}` (env-split, `resolve_bucket_name`)  | CF-9  |
| asset-group key | `category=` (paths + rows)                      | `asset_group=` (paths + manifest rows)                                       | CF-2  |
| pipeline_mode   | absent in path (`pipeline_mode` pending here)   | `pipeline_mode=` hive partition                                              | CF-3  |
| schema_version  | read DATA-STATE spread                          | v9 (data-state verified)                                                     | CF-1  |
| source          | path/blank                                      | `source` COLUMN (multi-source `FIXTURES`=2 rows; co-mingled, not a path key) | CF-4  |
| empty reason    | blank / mislabeled                              | typed `EmptyConfirmedReason` (sports fixture set rides the sports plan)      | CF-5  |
| names           | possible drift                                  | canonical data_type (underscore) + entity/league keys                        | CF-7  |
| available_at    | per-row (verify)                                | preserve / honest poll-time (no lookahead)                                   | CF-8  |
| phantom         | possible date-impossible rows                   | object-backed captured only                                                  | CF-10 |

## Phased execution

### P0 — instruments canonical-form AUDIT (run the SSOT checklist for the instruments surface)

> **Scope is a prior, not a ceiling — fix-fully-autonomously (HARD RULE)**: there is no headline cell-count here, but
> the same rule binds — read DATA-STATE and fix EVERY CF-RED the audit surfaces in this one walk (the cefi precedent: a
> bucket framed "~complete" was actually 100% v8 / no source / no asset_group / blank pipeline_mode). NOT descoped,
> deferred, post-cutover, or `BLOCKED-OPERATOR-DECISION` (a data-state gap is not a design fork). SSOT:
> `canonical_form_cross_service_audit_checklist.md` § "Audit scope is a PRIOR, not a ceiling".

- [x] ✅ [DATA] P0. CF-1…CF-12 data-state run (slot-3 tool `cf_manifest_audit_2026_06_01.py`, 2026-06-01) on the
      non-sports instruments-store indexes — **identical systemic debt to the MTDS AGs** (uniform across the corpus): -
      **instruments-store-cefi-prd** (30,803 rows): CF-1 RED 100% v8 · CF-2 vacuous (no AG col) · CF-3 RED blank
      pipeline_mode · CF-4 RED no source col · CF-8 RED no available_at · CF-5 GREEN · **legacy-only 23 cells** (2025-10
      BITGET/OKX/COINBASE/HYPERLIQUID, blank data_type) · paths flat (no asset_group=/pipeline_mode=). -
      **instruments-store-tradfi-prd** (20,264 rows): CF-1 RED 100% v8 · CF-3/CF-4/CF-8 RED · CF-5 GREEN · **legacy-only
      60 cells** (2026-03 NASDAQ/NYSE/CME/ICE, blank data_type) · paths flat. - **instruments-store-pred-prd** (493
      rows): CF-1 RED 100% v8 · pipeline_mode col ABSENT · CF-4/CF-8 RED · paths flat. (legacy
      `instruments-store-prediction-central` is long-form; re-diff in walk.) - **CF-7 note**: instruments-store cells
      carry **blank `data_type`** (keyed on date+venue) — verify/relabel intent in the walk. Feeds
      `instruments_master_audit_instructions.md` Canonical-form section. All CF-RED bundled into the per-bucket
      single-walk (prior-not-ceiling).
- [x] ✅ [DATA] P0. Bucket inventory: all instruments-store indexes are **AG-partitioned** (one `_index` per
      `instruments-store-{ag}-prd`); cefi/defi/tradfi/pred/sports each have `_index/availability_index.parquet`.
      **Five-slot asset-group split (operator 2026-06-03)** — each AG's instruments-store reference slice rides its AG
      slot: **defi→slot 2** (`instruments-store-defi` tracked in `defi_manifest_canonicalisation_2026_06_01.md` §H),
      **cefi→slot 3**, **sports→slot 4** (rides the sports master), **prediction→slot 5**, **tradfi→slot 6**. This plan
      (vm-cross-cutting) stays PRIMARY owner and drives the **cross-AG reference/instrument-record/universe indices** +
      coordinates each AG slice with its slot (referenced, not edited per-AG here). Object counts resolved per-bucket in
      the C0 walk.

### C — single-walk (bundled CF-1…CF-12) per in-scope instruments bucket

- [x] ✅ [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: enumerate ALL
      top-level trees + nested layouts in each in-scope instruments-store bucket before the walk; classify duplicate vs
      complementary. — **DONE 2026-06-07 (vm-cross-cutting), instruments-service@febb899e**: probed all 5
      `instruments-store-{ag}-prd` buckets (`gcloud storage ls`). Data-bearing tree is uniform + FLAT: non-sports =
      `instrument_availability/by_date/day={D}/venue={V}/instruments.parquet` (NO `asset_group=`/`pipeline_mode=`/
      `data_type=`; defi venue = co-mingled `{VENUE}-{CHAIN}`); sports =
      `sports_reference/by_date/day={D}/[pipeline_mode=/]entity={E}/league={L}/{folder}.parquet`. `_index` row counts:
      cefi 30,803 (100% v8) / tradfi 20,388 (170 v9) / defi 125,242 / pred 493 / sports 2,681,044 (735 v9). NO legacy
      `category=` PATH variants (paths are flat, not `category=`). SSOT: `cf_data_state_audit_slot3_2026_06_01.md` §
      Phase 0.

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract".

- [ ] [DATA] P0. C0 ONE bundled walk per non-sports instruments bucket: `category=`→`asset_group=` (paths + rows,
      CF-2) + `pipeline_mode=` partition (CF-3, RIDER — satisfies `pipeline_mode_partition_migration` instruments row) +
      v9 re-version (CF-1, data-state asserted) + env-split (CF-9) + canonical names (CF-7) + `available_at` preserve
      (CF-8) + phantom relabel (CF-10). Server-side `gcs_copy_object`, layout-aware. RUN ON A VM (gated on L0) or local
      if P0 says small.
- [ ] [DATA] P1. C-source RIDER (CF-4): re-consolidate the `source` column into the instruments `_index` (multi-source
      `FIXTURES`=2 rows). Folds `data_source_provenance` instruments-side re-consolidation — no separate walk.
- [ ] [CODE] P1. C-reasons (CF-5): instruments writers emit typed `EmptyConfirmedReason` (non-sports AGs) so future
      writes are honest; fetch-failure → `attempted_failed` not `empty_confirmed` (CF-11 swallow sweep).

### Verify + handoff to decommission

- [ ] [DATA] P0. Post-walk: re-run the P0 CF audit → all CF GREEN (data-state) for every in-scope instruments bucket; 0
      legacy-only cells vs canonical. C-GREEN signal for `bucket_name_ssot…` L6 instruments legacy decommission.

## Execution checklist (grounded — next session, finish in full)

> CF debt is in the `_index` MANIFEST + object PATHS. See `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md`
> § MECHANISM + layout map. Scope = non-sports instruments-store (cefi/tradfi/pred); sports reference rides the sports
> plan. instruments-store cells carry **blank `data_type`** (keyed date+venue) — verify intent.
>
> ⚠️ **IRREVERSIBLE — E6 DELETES the legacy instruments-store buckets permanently.** Do not run E2–E6 until the
> canonical target (v9, `asset_group=`, pipeline_mode, source, available_at) is CONFIRMED CORRECT at verify. One pass,
> no confusion.

- [x] ✅ [DATA] P0. E1 Phase-0 layout audit on `instruments-store-{cefi,tradfi,pred}-prd` (+ defi/sports); record
      per-bucket layouts + object counts. — **DONE 2026-06-07, instruments-service@febb899e** (see C-section Phase 0
      flip above for the grounded layout map + row counts; no separate legacy-named bucket observed — the `-prd` buckets
      are canonical-named already).
- [x] ✅ [DATA] P0. E2 Build/extend the instruments migrator (perf-contract) per bucket: `category=`→`asset_group=` +
      `pipeline_mode=` partition + canonical names; relabel blank-`data_type` legacy cells (cefi/tradfi/pred). — **DONE
      2026-06-07, instruments-service@febb899e**: `scripts/migrate_instruments_store_v9.py` — AG-parametric
      (`--asset-group {cefi,defi,tradfi,sports,prediction}`), DRY-RUN default / `--apply` GATED (G4). ONE bundled walk
      rewrites BOTH the `_index` rows AND object paths to v9: CF-1 schema*version=9 (reads ACTUAL dist, not the
      constant) · CF-2 `asset_group` col + `asset_group=` path key (drops `category` col) · CF-3
      `pipeline_mode=batch_instruments_service` col + path key (reference provenance — a venue \_listing* is reference,
      not a Tardis tick) · CF-4 `source=instruments_service` col · CF-TRANSPORT `transport=rest` col · CF-5 typed
      `EmptyConfirmedReason` (blank → `SOURCE_RETURNED_ZERO`; captured-but-`instrument_count==0` → empty) · CF-7 blank
      `data_type`→`instruments` (pred/sports typed values preserved) · CF-8 `available_at`=`written_at` · CF-9
      `resolve_bucket_name` (no inline gs://) · CF-10 honest `capture_status` from the writer's own `instrument_count`
      (null+count>0→captured; count==0→empty — never a silent placeholder). Index rewrite is deterministic from the
      recorded columns (no GCS probe) → fully offline-testable; object-path rewrite is idempotent server-side
      `gcs_copy_object`. **sports is structural-only** (its `capture_status`/`data_type`/reasons are
      enumerator-authoritative — 194k captured cells legitimately carry `instrument_count==0`; the sports owner does the
      CF-5 relabel via the coverage oracle). Perf-contract: `ThreadPoolExecutor` + `--workers`/`--start-date`/
      `--end-date` day-shard + per-object isolation. 14 credential-free unit tests
      (`tests/unit/scripts/test_migrate_instruments_store_v9.py`); QG `--no-fix` exit 0. **DRY-RUN green for all 5 AGs**
      on the real prod `_index` files (all CF-1/2/3/4/5/7/8 GREEN by construction). `--apply` RUN is E4/G4 (gated on
      coordinator G0 + Phase-0 writer-code + pre-migration drain; each AG owner runs `--apply`).
- [ ] [DATA] P0. E3 Confirm instruments writer drained; snapshot each `_index`.
- [ ] [DATA] P0. E4 Dry-VM → timing → optimise → run (small: 30k/20k/493 rows — likely fast; still no fire-and-forget).
- [ ] [DATA] P0. E5 Manifest rebuild per bucket: `ManifestWriter` stamping `source` + `pipeline_mode` + `available_at` +
      typed reasons → consolidator → v9. Writer-fix CF-5/CF-11 so future writes are honest.
- [ ] [DATA] P0. E6 Verify: `cf_manifest_audit_2026_06_01.py` per instruments-store bucket → CF-1…CF-12 GREEN; flip
      CF-coverage in `instruments_master_audit_instructions.md`. ⚠️ IRREVERSIBLE — only after GREEN: hand C-GREEN to L6
      → **delete the legacy instruments-store buckets permanently**.

## Success criteria

- Every in-scope instruments `_index` = v9 + `asset_group=` + `pipeline_mode=` partition + `source` column + typed
  reasons + canonical names + honest `available_at` (CF-1…CF-12 GREEN, data-state).
- Sports instruments surface confirmed owned by the sports plan (no double-walk); cross-AG instruments indices
  canonical.
- Hands C-GREEN to `bucket_name_ssot…` L6 → legacy instruments buckets deletable; instruments writer relaunch unblocked.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — instruments canonical form.
- `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` — the CF checklist this walk lands +
  `instruments_master_audit_instructions.md` Canonical-form coverage section.
