---
title:
  "Sports manifest + data canonicalisation (v9 + pipeline_mode partition + fixture-dependent typed reasons single-walk)
  — L3 owner for sports"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-sports
status: active
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-01
source:
  - defi_manifest_canonicalisation_2026_06_01.md §MASTER (L3 sports lane — was "verify-only"; canonical FORM still owed)
  - _index comparison 2026-06-01 (sports DATA complete: 0 legacy-only cells)
  - data_source_provenance_all_asset_groups_2026_06_01.md Phase 4 (sports source path→column — rides this walk)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Sports manifest + data canonicalisation (L3 owner for sports)

> **🔎 CROSS-AG FINDING from defi (2026-06-01) — CHECK THE SAME HERE**: defi's CF data-state audit found the legacy
> `_index` **100% NOT v9** (v4/5/6/8 spread), with **no `source`/`asset_group`/`pipeline_mode` COLUMNS** and glued
> venues — a FULL re-canonicalisation, not the headline cell-count (same shape as the cefi reference incident). **CF-2
> gotcha**: the migrate tool emitted `asset_group=` to the object PATH but did NOT stamp it as a parquet COLUMN → the
> rebuilt `_index` lacked the column. Fix = stamp `asset_group` (+ `schema_version`/`source`/`pipeline_mode`) as
> COLUMNS, never rely on the consolidator deriving them from the path. **Action**: run a CF data-state audit on sports'
> two `_index` surfaces as pre-flight + verify (reusable:
> `market-tick-data-service/market_tick_data_service/scripts/audit_canonical_form.py` or
> `plans/audit/results/cf_manifest_audit_2026_06_01.py`) — trust the real data-state, never the v9 constant. If the same
> debt shows → fix fully in-walk (scope is a prior, not a ceiling). SSOT:
> `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md`.

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, sports lane). The master listed sports as
> "verify-only" because the DATA copy is complete (0 legacy-only cells) — but the canonical **FORM** + the
> **fixture-dependent typed honest-absence** are still owed. This plan is the sports analogue of `defi_manifest`'s §C
> single-walk. **Single-walk discipline (HARD RULE)**: ONE bundled walk on the sports `_index` — bundle v8→v9 +
> `pipeline_mode=` partition + venue/data_type canonical verify + **fixture/season/transfer-window/league-genesis typed
> empty-reasons** + source path→column + `available_at`. Do NOT open a second walk; `pipeline_mode_partition_migration`
>
> - `data_source_provenance` (sports) ride THIS walk.

## Why this exists — sports DATA is complete, but the FORM + honest absence are NOT canonical

The 2026-06-01 `_index` comparison (legacy `market-data-tick-sports-…` vs canonical `market-data-tick-sports-prd-…`):
**0 legacy-only cells** — so at the data-copy level sports is verify-only; no legacy→canonical data-loss migration.

**But sports is the asset group where honest absence is the keystone**, and it is not yet canonical:

- Sports is **derived/reference data whose presence depends on the real-world schedule** — a cell is legitimately empty
  not because a fetch failed but because _there was no fixture that day_, the _league was off-season / paused_, the date
  was _outside a FIFA transfer window_, the date was _before the source's coverage genesis_, or the _source does not
  cover that league_. Blank / `SOURCE_RETURNED_ZERO` rows that are really one of these are a **silent lie** about
  coverage (the same class as the defi A7 fetch-swallow bug, but schedule-driven). UAC already has the typed reasons —
  the manifest must carry them.
- The canonical **`pipeline_mode=` partition** is not on the sports object paths (`pipeline_mode_partition_migration`
  RIDER — bundles here per master CONFLICT-1).
- The live sports `_index` schema_version must be re-versioned to **v9** (data-state, not the constant — manifest-v8
  lesson).
- `source` is in the **path** (`data_source=ODDS_API/`, `pipeline_mode=batch_api_football/`) not the **column** — the
  path→column migration is owed (`data_source_provenance` Phase 4 — RIDER here). **`source` is a COLUMN, not a path
  key** (provenance plan SSOT): all sources co-mingle on the SAME read path, so the consumer-facing layout is unchanged
  ("data looks the same") — the column exists only so WE can identify where a row's data came from when we audit. Sports
  is the one AG that wrongly put source in the path; this walk lifts it into the column and drops the `data_source=`
  path segment.
- `available_at` (forecast-issue time for `WEATHER`, fixture-poll time for fixtures) must be preserved / honestly
  derived (lookahead-bias invariant) — folded per `available_at_lookahead_bias_completion_2026_05_08`.

The hard-to-find-ness IS the bug (master rationale): one bundled walk makes data + manifest + `_index` + data-status all
canonical — including the 4-state honest reason — so the next sports coverage audit is one pass.

## Two sports surfaces (both in scope for canonical FORM)

- **`market-data-tick-sports-prd-…`** (MDPS odds ticks: `odds_snapshot` / `odds_movement` / `odds_horizon_bucket`) — the
  bucket the remediation tracks for decommission.
- **`instruments-store-sports-{project}`** (instruments-service reference: fixtures + 20 canonical reference data_types)
  — layout `sports_reference/by_date/day={D}/entity={folder}/league={L}/…` (PER_DAY_PER_LEAGUE default;
  PER_DAY_PER_SEASON for `PLAYER_VALUES`; PER_DAY_BARE for `XG`/`WEATHER`/`LEAGUES`; FLAT for `VENUES`). The fixture-
  dependent typed reasons live HERE.

The bundled walk is **layout-aware** (per the remediation note that sports uses `processed/` + `sports_reference/`, not
the cefi/defi `raw_tick_data/by_date/` shape).

## Scope boundary — what this plan does NOT own (no overlap)

- **The 25,652 `MISSING_EXPECTED` odds cells** (BET365/BETFAIR/DRAFTKINGS/FANDUEL/ODDS_API/PINNACLE × odds_snapshot +
  odds_movement, absorbed 2026-05-20) — owned by **`epics/sports_master.md`** (coverage backfill, not canonicalisation).
  This plan canonicalises the FORM + relabels honest-absence; it does NOT backfill missing bookmaker coverage.
- **Retired-data-type cleanup** (`TRANSFERMARKT_LEAGUES` / `SFI_LEAGUES`, 88,779 rows → `EXPECTED_DEPRECATED_DATA_TYPE`)
  — owned by `sports_retired_data_types_code_cleanup_2026_05_13.md`.
- **`source` write-path code** — owned by `data_source_provenance` Phase 4 (already shipped the multi-source `FIXTURES`
  stamping at the instruments-service writers); this plan only runs the **path→column data backfill + re-consolidation**
  as a RIDER of the single walk.

## Sports honest-absence — the typed reasons the walk must materialise (keystone)

The single-walk relabels every blank / mislabeled-`SOURCE_RETURNED_ZERO` row to the correct UAC `EmptyConfirmedReason`,
driven by the UAC coverage oracle (`clip_dates_to_source_coverage()` + `is_in_known_gap()` + season/transfer-window/
fixture-status lookups in `unified_api_contracts.canonical.domain.sports.league_data`), never re-derived per consumer:

| Real-world cause                                  | Typed reason (UAC `honest_coverage.py`)                     |
| ------------------------------------------------- | ----------------------------------------------------------- |
| No fixture scheduled for (league, day)            | `EXPECTED_NO_FIXTURE`                                       |
| Date before season kick-off                       | `EXPECTED_PRE_SEASON`                                       |
| Date after season's final fixture                 | `EXPECTED_POST_SEASON`                                      |
| League off-season / suspension                    | `EXPECTED_PAUSED_LEAGUE`                                    |
| Outside FIFA transfer window (`transfer_records`) | `EXPECTED_OUTSIDE_TRANSFER_WINDOW`                          |
| Source genesis: before source coverage-start      | `EXPECTED_KNOWN_SOURCE_GAP` / clip to coverage              |
| Source does not cover this league (Understat → 5) | `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`                     |
| Fixture postponed (PST) / cancelled (CANC)        | `EXPECTED_FIXTURE_POSTPONED` / `EXPECTED_FIXTURE_CANCELLED` |
| Provider league mapping absent                    | `EXPECTED_NO_MAPPING`                                       |

The owner code (instruments-service sports handlers) must also emit these at write time so FUTURE writes are correct —
the writer analogue of defi's A1/A2b. (If a handler currently records blank/`SOURCE_RETURNED_ZERO` for a no-fixture day,
that is the write-path bug to fix; mirror the defi A7 "fetch-swallow ≠ empty" discipline.)

## Sequencing — canonical migration is a GATE before any sports backfill (inherits master HARD RULE)

No sports backfill / relaunch of `sports-scheduler` until this walk is C-GREEN (master L3-gates-L5 + `bucket_name_ssot…`
Phase 4 — the drained `sports-scheduler` must NOT relaunch until canonical). Runs behind the pre-migration drain (stop
GCP+AWS writers → consolidate → snapshot `_index/snapshots/pre_migration_2026_06_01.parquet`). L0 tarball-prune blocker
(`issues/pinned_tarball_prune_breaks_vm_deploys_2026_06_01.md`) must be fixed first if run on a VM.

## Canonical target form (sports)

| Dimension       | Legacy / now                                           | Canonical (target)                                                                                                                                                                              |
| --------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Bucket          | `market-data-tick-sports-{project}` (no env)           | `market-data-tick-sports-prd-{project}` (+ `instruments-store-sports-{env}-…`)                                                                                                                  |
| asset-group key | `category=sports`                                      | `asset_group=sports`                                                                                                                                                                            |
| pipeline_mode   | in path as `pipeline_mode=batch_api_football` (some)   | `pipeline_mode=` hive partition on ALL paths (`batch_api_football`/`batch_footystats`/`batch_odds_api`/`batch_understat`/`batch_transfermarkt`/`batch_soccer_football_info`/`batch_open_meteo`) |
| schema_version  | live `_index` reads v8                                 | v9 (re-consolidated — data-state verified)                                                                                                                                                      |
| data_type name  | underscore-canonical (verify clean; retired ones gone) | `FIXTURES`/`FIXTURE_EVENTS`/`INJURIES`/`ODDS`/`XG`/`PLAYER_VALUES`/… (20 canonical)                                                                                                             |
| venue / league  | league_id / bookmaker (verify canonical)               | canonical `league=` + flat bookmaker `venue`                                                                                                                                                    |
| source          | in PATH (`data_source=ODDS_API/`)                      | `source` COLUMN (path→column RIDER; multi-source `FIXTURES` = two rows)                                                                                                                         |
| empty reason    | blank / `SOURCE_RETURNED_ZERO` mislabel                | typed fixture/season/transfer-window/genesis reasons (table above)                                                                                                                              |
| available_at    | per-row exists                                         | preserve / honest forecast-issue + poll-time (lookahead-bias invariant)                                                                                                                         |

## Phased execution

### P0 — pre-walk audit + scope

> **Scope is a prior, not a ceiling — fix-fully-autonomously (HARD RULE)**: the headline ("0 legacy-only / DATA
> complete / verify-only") is a coarse prior. Read DATA-STATE. If the audit finds MORE form debt than implied (e.g. cefi
> turned out 100% v8 / no source / no asset_group / blank pipeline_mode — a full re-canonicalisation), fix ALL of it in
> this one walk — NOT descoped, deferred, post-cutover, or `BLOCKED-OPERATOR-DECISION` (a data-state gap is not a design
> fork). SSOT: `canonical_form_cross_service_audit_checklist.md` § "Audit scope is a PRIOR, not a ceiling".

- [x] ✅ [DATA] P0. Live sports `_index` DATA-STATE (slot-4 tool, 2026-06-01): **100% v8** (0/786,408 v9 — CF-1 RED);
      no `category`/`asset_group` col (CF-2 rows vacuous); **`pipeline_mode` blank 0/786,408 (CF-3 RED)**; **no `source`
      column (CF-4 RED)**; **no `available_at` column (CF-8 RED — only `written_at`)**. capture_status: empty_confirmed
      **584,177** / captured 202,067 / attempted_failed 164. **KEYSTONE FINDING — CF-5 RED-by-mislabel: ALL 584,177
      empties are labeled `SOURCE_RETURNED_ZERO`** (a single blanket reason on a schedule-driven AG) — these are exactly
      the no-fixture/off-season/out-of-window/uncovered-league cells the C-reasons rider must relabel to typed UAC
      reasons via the coverage oracle. (My generic tool scores CF-5 "GREEN=non-blank", but blanket SOURCE_RETURNED_ZERO
      on sports IS the mislabel — treat CF-5 RED until the oracle relabel lands.)
- [x] ✅ [DATA] P0. **0 legacy-only cells confirmed** (legacy 32,755 · canonical 32,869 · overlap 32,755) — sports DATA
      is complete; the walk is FORM-only (v9 + partition + source + typed reasons), no data-loss-gap copy needed.
- [ ] [DATA] P0. Object-path scheme (slot-4 probe): `processed/by_date/day=YYYY-MM-DD/data_type=…/league_id=…/
      timeframe=…` — has `day=`/`data_type=`/`league_id=`/`timeframe=` hive BUT **no `asset_group=` and no
      `pipeline_mode=` segment** (CF-2 paths + CF-3 partition RED). The C0 walk adds `asset_group=sports` +
      `pipeline_mode=` to all object paths; lift `data_source=` (where present) → `source` column.
- [ ] [DATA] P1. Verify venue/league/data_type strings are canonical: data-state shows data_type CASE DRIFT —
      `ODDS`/`ODDS_MOVEMENT`/`ODDS_SNAPSHOT` (upper) coexist with `odds_horizon_bucket*` (lower) + `trades`/
      `ARBITRAGE_OPPORTUNITY`; venue set looks canonical (bookmaker names) but blank `''` present. Diagnose/relabel the
      case drift + blank in the walk (retired data_types confirmed absent per `sports_retired_data_types_code_cleanup`).

### C — single-walk (v9 + partition + typed reasons + source path→column + canonical verify)

- [ ] [DATA] P0. **Phase 0 — layout audit (MANDATORY, blocking — slot-2 DeFi lesson 2026-06-01)**: enumerate ALL
      top-level trees + nested layouts across BOTH sports surfaces (`processed/by_date/…`, `sports_reference/by_date/…`,
      any `day=/category=` / `data_source=` variants) before the walk; classify duplicate (keep freshest) vs
      complementary (migrate all → canonical v9). Cover every in-scope layout or the walk is incomplete (review-blocking).
      SSOT: `plans/audit/results/cf_data_state_audit_slot4_2026_06_01.md` § grounded recipe Phase 0.

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: the walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. SSOT:
> `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script performance contract".

- [ ] [DATA] P0. C0 ONE bundled, layout-aware walk on the sports `_index` + objects: (a) `pipeline_mode=` hive partition
      on ALL paths (RIDER — `pipeline_mode_partition_migration`, satisfied here); (b) re-version manifest rows to **v9**
      (data-state asserted); (c) **`category=`→`asset_group=` across BOTH object PATHS and manifest `_index` ROWS** +
      env-split where legacy-form remains (CODE side — writers emit `asset_group=` — already shipped via archived
      `venue_axis_asset_group_vocabulary_2026_04_25`; this is historical data+manifest only); (d) venue/league/
      data_type canonical relabel for any P0 drift; (e) `available_at` preserve / honest derivation. Server-side
      `gcs_copy_object`, layout-aware (`sports_reference/` + `processed/`). RUN ON A VM (gated on L0 tarball-prune) OR
      locally if scope is small (P0 decides).
- [ ] [DATA] P0. C-reasons RIDER (the keystone): relabel every blank / mislabeled empty row to the correct typed UAC
      reason via the coverage oracle (`clip_dates_to_source_coverage` / `is_in_known_gap` / season / transfer-window /
      fixture-status / league-coverage) — the table in § Sports honest-absence. Snapshot-protected, idempotent,
      oracle-driven (never re-derived per consumer).
- [ ] [DATA] P1. C-source RIDER (`data_source_provenance` Phase 4): path→column migration — read `source` from the path
      segment (`data_source=…`, `pipeline_mode=batch_…`), write it into the `source` column on every row, re-consolidate
      into the `_index` (multi-source `FIXTURES` = two rows). Executed in THIS walk — do NOT run a separate sports
      source walk.
- [ ] [CODE] P1. C-writer: instruments-service sports handlers emit the typed fixture/season/transfer-window reasons at
      write time (writer analogue of defi A1/A2b) so future writes are honest — no blank/`SOURCE_RETURNED_ZERO` for a
      no-fixture / off-season / out-of-window / uncovered-league day.

### Verify + handoff to decommission

- [ ] [DATA] P0. Post-walk: fresh `_index` read — `schema_version=9` (data-state) for 100% of rows; `pipeline_mode=`
      partition present + non-null; `source` column populated (path→column complete; multi-source = two rows); venue/
      league/data_type canonical only; **0 blank/untyped empty reasons** (every empty cell carries a typed fixture/
      season/transfer-window/genesis reason); `available_at` honest. 0 legacy-only cells. C-GREEN signal for
      `bucket_name_ssot…` Phase 6/7 sports legacy bucket decommission.

## Execution checklist (grounded — next session, finish in full)

> CF debt is in the `_index` MANIFEST + object PATHS, NOT the raw tick parquets. See
> `plans/audit/results/cf_data_state_audit_slot4_2026_06_01.md` § MECHANISM + layout map. sports raw = full hive
> `day=/category=/data_source=/venue=/league_id=/instrument_type=/data_type=` (parquet already has `source`+`data_source`
> cols). **Keystone**: 584,177 empties are blanket `SOURCE_RETURNED_ZERO` — relabel to typed fixture/season reasons.
>
> ⚠️ **IRREVERSIBLE — E8 DELETES legacy `market-data-tick-sports` permanently.** Do not run E2–E8 until the canonical
> target (v9, `day=/pipeline_mode=/asset_group=sports/…`, source col, typed reasons) is CONFIRMED CORRECT at verify.
> One pass, no confusion — once legacy is deleted it is gone.

- [ ] [DATA] P0. E1 Phase-0 layout audit on both sports surfaces (`market-data-tick-sports-prd` + `instruments-store-sports-prd`)
      via `cf_layout_audit`; confirm `processed/` + `raw_tick_data/` (category=/data_source=) + `sports_reference/`.
- [ ] [DATA] P0. E2 Build/extend `migrate_sports_canonical.py` to v9-canonical (perf-contract): `category=`→`asset_group=sports`,
      add `pipeline_mode=batch_{api_football,footystats,odds_api,understat,transfermarkt,…}`; keep `source` col (already present).
- [ ] [DATA] P0. E3 Confirm `sports-scheduler` writer drained; snapshot the sports `_index`(es).
- [ ] [DATA] P0. E4 Dry-VM → timing → optimise → full-VM run (786k index rows; no fire-and-forget).
- [ ] [DATA] P0. E5 **KEYSTONE reason relabel** (CF-5): at manifest rebuild, relabel the 584,177 `SOURCE_RETURNED_ZERO`
      empties → typed UAC reasons (`EXPECTED_NO_FIXTURE`/`PRE_SEASON`/`POST_SEASON`/`PAUSED_LEAGUE`/`OUTSIDE_TRANSFER_WINDOW`/
      `SOURCE_DOES_NOT_COVER_LEAGUE`/`FIXTURE_POSTPONED|CANCELLED`/`KNOWN_SOURCE_GAP`/`NO_MAPPING`) via the UAC coverage
      oracle (`clip_dates_to_source_coverage`/`is_in_known_gap`/`league_data`) — never re-derived per consumer.
- [ ] [DATA] P0. E6 Manifest rebuild: `ManifestWriter` stamping `source` (path→col lift) + `pipeline_mode` + `available_at`
      → consolidator → v9. Also fix the writer to emit typed reasons going forward (CF-5 write-path).
- [ ] [DATA] P1. E7 CF-7 relabel: ODDS case-drift (`ODDS`/`ODDS_SNAPSHOT` upper vs `odds_horizon_bucket` lower) + blank venue.
- [ ] [DATA] P0. E8 Verify: `cf_manifest_audit_2026_06_01.py` on both sports surfaces → CF-1…CF-12 GREEN (esp. 0 blanket
      SOURCE_RETURNED_ZERO); flip CF-coverage in `sports_master_audit_instructions.md`. ⚠️ IRREVERSIBLE — only after
      GREEN: hand C-GREEN to L6 → **delete legacy `market-data-tick-sports` permanently**.

## Success criteria

- Canonical sports `_index` = v9 + `pipeline_mode=` partition + `source` column + canonical venue/league/data_type.
- Every empty sports cell carries a **typed** fixture/season/transfer-window/genesis/coverage reason — 0 blank /
  mislabeled `SOURCE_RETURNED_ZERO`; the writer emits them going forward.
- `sports-scheduler` relaunch unblocked (writes canonical-only); hands C-GREEN to `bucket_name_ssot…` L6 → legacy
  `market-data-tick-sports-…` deletable.
- No overlap: 25k odds `MISSING_EXPECTED` backfill stays with `epics/sports_master.md`; retired-data-type cleanup stays
  with `sports_retired_data_types_code_cleanup_2026_05_13.md`; `source` write-path stays with `data_source_provenance`.

## Codex SSOTs

- `codex/02-data/availability-manifest-and-data-status.md` — sports canonical form (v9 + pipeline_mode partition + the
  fixture-dependent typed empty-reason taxonomy).
- `codex/02-data/honest-absence-downstream-handling.md` — sports per-reason consumer policy (fixture/season/transfer-
  window/genesis reasons → ML/strategy skip rules).
