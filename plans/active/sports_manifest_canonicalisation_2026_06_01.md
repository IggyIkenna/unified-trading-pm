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

> ## 🎬 SLOT PICKUP PROMPT (clean handoff — paste verbatim into a fresh sports slot, 2026-06-01)
>
> You are the **sports** slot for the non-DeFi data+manifest canonicalisation. Your lane is **sports ONLY** — prediction
> is slot-3's proving ground (done/in-flight), cefi/tradfi are other slots, defi is slot-2. Do not touch them.
>
> **FIRST**: read `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` and follow ALL rules.
> `git pull --ff-only origin live-defi-rollout` before starting. You are a slot on `tab/<operator>/<N>` —
> Commit+Push+Flip every shippable unit in the same turn.
>
> **READ FIRST (in order):**
>
> 1. `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` — THE SSOT. Read the **"CROSS-AG EXECUTION LESSONS"**
>    section in full (10 traps the prediction build surfaced — they ALL apply to sports): UAC `candidate_parquet_paths`
>    is the path SSOT (`day=/pipeline_mode=/asset_group=/…`, pipeline_mode LEFT of asset_group=, byte-exact batch=live);
>    multi-source completeness (compute legacy-only AND canon-only, never copy-bigger-into-smaller); headline counts are
>    priors—read data-state; normalise CF-7 BEFORE computing overlap/dedup; sample overlap CONTENT not just cell keys;
>    "unique" cells are often drift—diagnose; `row_count` NaN ≠ phantom; reconcile manifest GRANULARITY (read parquet
>    columns the canonical path dropped); `source` authoritative from parquet/path; only the DELETE is
>    irreversible+gated.
> 2. `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` — CF-1…CF-12 acceptance + "Audit scope
>    is a PRIOR, not a ceiling".
> 3. `codex/05-infrastructure/gcs-object-operations.md` § Migration-script performance contract (ThreadPoolExecutor
>    walk, wired `--workers`/`--start-date`/`--end-date`, `gcs_copy_object` for path-only moves, `python -u`, per-object
>    try/except continue, idempotent).
> 4. **THIS plan** (`sports_manifest_canonicalisation_2026_06_01.md`) — P0 audits flipped; the **E1–E8 execution
>    checklist** is your work list. Also `sports_master_audit_instructions.md` (CF-coverage rows to flip GREEN) +
>    `epics/sports_master.md`.
> 5. Reference migrator to extend: `market-tick-data-service/.../scripts/migrate_sports_canonical.py` (extend to FULL
>    v9)
>    - `migrate_sports_hive_key.py`. Reuse the prediction migrator (`migrate_prediction_to_pred_prd_v9.py`) as the
>      pattern for UAC-SSOT paths + dual-source reconciliation + CF-7 normalisation baked into the transform.
>
> **MISSION — execute `sports_manifest_canonicalisation` to CF-1…CF-12 GREEN on REAL data-state, then hand C-GREEN to
> `bucket_name_ssot…` L6 for the legacy delete.** Sports specifics:
>
> - **KEYSTONE (CF-5)**: 584,177 empties are blanket-mislabeled `SOURCE_RETURNED_ZERO` on a schedule-driven AG → relabel
>   to typed fixture/season/transfer-window/genesis reasons via the UAC coverage oracle
>   (`clip_dates_to_source_coverage()` / `is_in_known_gap()` / `unified_api_contracts.sports.candidate_parquet_paths`).
> - **CF-2**: `category=`→`asset_group=sports` on BOTH paths and the rebuilt `_index` (stamp asset_group as a COLUMN,
>   not just the path — the CF-2 gotcha).
> - **CF-4**: lift `data_source=` (in path) → `source` COLUMN.
> - **CF-1/3/8**: v9 + `pipeline_mode=` partition + `available_at` via the `ManifestWriter` rebuild.
> - **CF-7**: ODDS case-drift (`ODDS`/`ODDS_SNAPSHOT` upper vs `odds_horizon_bucket` lower) + blank venue — normalise IN
>   the migrator before dedup.
> - Sports object layout: `processed/by_date/day=/data_type=/league_id=/timeframe=` (+ `instruments-store-sports-prd`).
>
> **GATES**: VM-only whole-corpus walks (asia-northeast1, no fire-and-forget: STARTED<60s + progress/hr + STOPPED +
> T+10min describe); per-AG writer drain before `--apply`; Phase-0 layout audit is MANDATORY+blocking before the walk;
> additive `--apply` copy is safe to run, only the legacy DELETE (E8) is IRREVERSIBLE + gated on CF-GREEN-on-real-data +
> the fleet drain (shared w/ slot-2). Capture every new finding as a plan todo + as a cross-AG lesson in the SSOT doc.
> **DONE** = every (sports × CF-1…CF-12) GREEN on real data-state + handed to L6 + legacy bucket deleted (single SSOT).

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

> **Scope is a prior, not a ceiling — fix-fully-autonomously (HARD RULE)**: the headline ("0 legacy-only / DATA complete
> / verify-only") is a coarse prior. Read DATA-STATE. If the audit finds MORE form debt than implied (e.g. cefi turned
> out 100% v8 / no source / no asset_group / blank pipeline_mode — a full re-canonicalisation), fix ALL of it in this
> one walk — NOT descoped, deferred, post-cutover, or `BLOCKED-OPERATOR-DECISION` (a data-state gap is not a design
> fork). SSOT: `canonical_form_cross_service_audit_checklist.md` § "Audit scope is a PRIOR, not a ceiling".

- [x] ✅ [DATA] P0. Live sports `_index` DATA-STATE (slot-3 tool, 2026-06-01): **100% v8** (0/786,408 v9 — CF-1 RED); no
      `category`/`asset_group` col (CF-2 rows vacuous); **`pipeline_mode` blank 0/786,408 (CF-3 RED)**; **no `source`
      column (CF-4 RED)**; **no `available_at` column (CF-8 RED — only `written_at`)**. capture_status: empty_confirmed
      **584,177** / captured 202,067 / attempted_failed 164. **KEYSTONE FINDING — CF-5 RED-by-mislabel: ALL 584,177
      empties are labeled `SOURCE_RETURNED_ZERO`** (a single blanket reason on a schedule-driven AG) — these are exactly
      the no-fixture/off-season/out-of-window/uncovered-league cells the C-reasons rider must relabel to typed UAC
      reasons via the coverage oracle. (My generic tool scores CF-5 "GREEN=non-blank", but blanket SOURCE_RETURNED_ZERO
      on sports IS the mislabel — treat CF-5 RED until the oracle relabel lands.)
- [x] ✅ [DATA] P0. ~~**0 legacy-only cells confirmed**~~ **CORRECTED 2026-06-01 (sports-slot, operator "did we check
      ALL buckets" review)**: the "0 legacy-only / verify-only" claim was **MDPS-ONLY** (`market-data-tick-sports`
      legacy: 32,755 cells, overlap 32,755, 0 legacy-only ✓). It was **NEVER true for the instruments-store surface** —
      the legacy no-env `instruments-store-sports-central-element-323112` (which I had NOT diffed) has **316 LEGACY-ONLY
      cells MISSING from prd** (`2018-*, '', ODDS|PREDICTIONS` — early reference data). Deleting that legacy bucket
      without migrating these = permanent data loss — the exact DeFi/TradFi "missed bucket with real data" trap. ⇒
      sports is **NOT FORM-only**; the instruments-store walk MUST diff+migrate legacy→prd (the 316 cells + any
      sports_reference{,\_v1_archive,\_v2} objects not in prd) BEFORE E8. See § "FULL sports bucket inventory" below.
- [x] ✅ [DATA] P0. Object-path scheme (sports slot reconfirm, 2026-06-01 — direct `gcloud ls` probe): MDPS-prd
      `processed/by_date/day=/data_type=/league_id=/timeframe=/` + `raw_tick_data/by_date/day=…/` (deeper hive) — has
      `day=`/`data_type=`/`league_id=`/`timeframe=` hive BUT **no `asset_group=` and no `pipeline_mode=` segment** (CF-2
      paths + CF-3 partition RED). Parquet rows DO carry `source` + `data_source` columns (layout audit). The C0 walk
      adds `asset_group=sports` + `pipeline_mode=` to all object paths; `source` lifts path→col (already in col too).
- [x] ✅ [DATA] P1. data_type/venue canonical drift CONFIRMED (CF audit 2026-06-01). MDPS data_type CASE DRIFT —
      `ODDS`/`ODDS_MOVEMENT`/`ODDS_SNAPSHOT` (upper) vs `odds_horizon_bucket*`/`odds`/`odds_movement`/`odds_snapshot`
      (lower) + `trades`/`ARBITRAGE_OPPORTUNITY`; venue has blank `''` + suspicious non-bookmaker `FOOTBALL` + `KALSHI`
      (prediction venue) — CF-7 relabel + CF-10 diagnose in the walk (E7). instruments-store has its OWN drift (below).

> **🔎 SCOPE-IS-A-PRIOR EXPANSIONS (sports slot CF data-state audit 2026-06-01 — fix ALL in-walk, NOT descoped)**: the
> two-surface CF + layout audit surfaced MORE form debt than the MDPS-786k headline implied. Per the HARD RULE these are
> captured as todos + fixed in the SAME single walk. Evidence: `/tmp/cf_sports_{mdps,instr,layout}.log` (reproduce via
> `cf_manifest_audit_2026_06_01.py <bucket> [--legacy …]` + `cf_layout_audit_2026_06_01.py`).

- [ ] [DATA] P0. **instruments-store-sports-prd is 2,681,044 rows / 1,909,553 empties** (MUCH bigger than the MDPS 786k
      keystone headline) — CF-1 RED (2,680,309 v8 + 735 v9 = 0.0% v9), CF-3 RED (pipeline_mode 0%), CF-4 RED (no
      `source` col), CF-8 RED (no `available_at`). asset_group COL present (CF-2 rows GREEN) but paths have NO hive
      (`day=2026-03-21/venue=BETFAIR/{uuid}.parquet` bare top-level + `sports_reference/by_date|fixtures|mappings|…`).
      The keystone reason-relabel + v9 rebuild apply to BOTH surfaces — this surface carries the bulk of the empties.
- [ ] [DATA] P0. **NON-CANONICAL free-text error_reason on instruments-store: 22,978 rows labeled
      `flipped_via_recover_fixtures_from_truthset_20260506-165630__truth_says_empty`** (NOT a closed-set
      `EmptyConfirmedReason` — violates `EMPTY_CONFIRMED_REASONS`; the generic CF-5 "non-blank=GREEN" heuristic missed
      it). The truthset said the fixture is empty → relabel to `EXPECTED_NO_FIXTURE` (truthset-confirmed no-fixture) in
      the keystone rebuild. instruments-store empty dist: SOURCE_RETURNED_ZERO 1,866,991 + this 22,978 +
      EXPECTED_PRE_SOURCE_COVERAGE_START 13,176 + EXPECTED_NO_FIXTURE 6,408 (the last two already typed — preserve).
- [ ] [DATA] P1. **instruments-store CF-10 phantom probe: 6,869 rows with `capture_status=None`** (malformed/phantom
      manifest rows — neither captured/empty/failed). Diagnose object-backed vs phantom at rebuild; honest-drop the
      object-less ones (never migrate a manifest row with no backing object). Also `attempted_failed` 178,025 (separate
      coverage/health concern — surface to `epics/sports_master.md`, not a canonicalisation blocker).
- [ ] [DATA] P1. **instruments-store CF-7 drift**: blank `data_type=''`, retired types still present
      (`SFI_LEAGUES`/`SFI_PROGRESSIVE_STATS`/`SFI_STANDINGS`/`TRANSFERMARKT_LEAGUES` — owned by
      `sports_retired_data_types_code_cleanup_2026_05_13.md`, relabel→`EXPECTED_DEPRECATED_DATA_TYPE` here), venue
      CASE+alias drift (`API_FOOTBALL`/`api_football`/`API_FOOTBALL_FIXTURES`, `odds_api`, `footystats`, `open_meteo`,
      `soccer_football_info`, `transfermarkt`, `mdps_odds_horizon_bucket`). Normalise in the migrator BEFORE dedup
      (CF-7).
- [ ] [DATA] P1. **Multi-layout reality on instruments-store (Phase-0 must enumerate ALL)**: top-level trees =
      `sports_reference/{by_date,fixtures,footystats_league_ids,mappings}/` + `sports_reference_v1_archive/` + a BARE
      `day=YYYY-MM-DD/venue=…/{uuid}.parquet` tree + `instrument_availability/` + `availability_index/`. The migrator is
      layout-dispatching across ALL of these (slot-2 DeFi "audit ALL layouts" lesson) — a single-tree walk
      under-migrates.

## FULL sports bucket inventory + decommission scope (sports-slot 2026-06-01 — operator "delete EVERY other sports bucket; did we miss any?" review)

> The end-state is a SINGLE SSOT: every legacy/duplicate sports bucket DELETED. So we must enumerate EVERY sports
> bucket + classify keep/migrate/delete BEFORE any delete (the DeFi/TradFi "missed-bucket-with-real-data" trap).
> `gcloud storage ls | grep -i sport` (central-element-323112) returned **~35 sports buckets**, NOT the 2 surfaces the
> plan originally scoped:

| Bucket family                                                                                   | env variants                            | data state (2026-06-01 probe)                                                                                 | disposition                                                                    |
| ----------------------------------------------------------------------------------------------- | --------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `market-data-tick-sports`                                                                       | no-env(legacy) · prd · dev · stg · test | MDPS odds; prd 786k rows; legacy 0 legacy-only ✓                                                              | **migrate→prd FORM; delete legacy no-env + test after**                        |
| `instruments-store-sports`                                                                      | no-env(legacy) · prd · dev · stg · test | reference; prd 2.68M; **legacy no-env has 316 LEGACY-ONLY cells + full sports_reference{,\_v1_archive,\_v2}** | **migrate legacy→prd (data-loss gate!) then delete legacy no-env + test**      |
| `features-{sports,delta-one,mtf,volatility,xinstrument}-sports`                                 | no-env · prd · dev · stg                | **ALL EMPTY (idx=0, no objects)** — confirmed, no data run                                                    | delete empty legacy + keep canonical prd as future write target (no migration) |
| `risk-store-sports` / `risk-store-*-sports` / `positions-store-*-sports` / `pnl-store-*-sports` | various                                 | downstream store buckets — NOT YET PROBED                                                                     | **TODO: probe + classify before any sports-bucket-decommission sweep**         |

- [x] ✅ [DATA] P0. **Migrate the legacy no-env `instruments-store-sports` → prd BEFORE E8** (data-loss gate): 316
      legacy-only `(2018-*, '', ODDS|PREDICTIONS)` cells + reconcile its `sports_reference` /
      `sports_reference_v1_archive` / `sports_reference_v2` / `day=/venue=` / `instrument_availability` trees against
      prd (compute legacy-only AND canon-only — union, never copy-bigger-into-smaller). The migrator's
      `--surface instruments` MUST take a `--legacy-bucket` and walk BOTH. (Mirror the MDPS prd-vs-legacy reconcile.) —
      market-tick-data-service@50a43aa7 | --legacy-bucket arg added; per-tree legacy-only+prd-only sets computed (shard
      key strips pipeline_mode/asset_group); 3-version entity×schema map + SAME-vs-COMPLEMENTARY verdict; schema
      spot-check (PRD_LOSES_COLS_OR_ROWS flag); phantom-verify sample (gcs_describe_object); idempotent gcs_copy_object;
      ThreadPoolExecutor; dry-run default; QG GREEN. VM production dry-run pending E3 drain (GCS inaccessible locally —
      consolidator shards).
- [x] ✅ [DATA] P1. **Store buckets probed — ALL 7 EMPTY → delete-safe** (sports-slot 2026-06-01):
      `risk-store-sports{,-test}` + `risk-store-{,-test}-sports` + `positions-store-{,-test}-sports` +
      `pnl-store-test-…-sports` all have 0 objects. Neither naming convention is in `cloud-providers.yaml` (canonical
      would be `risk-store-sports-${ENV}-…` per the defi pattern) → both are legacy/non-canonical → safe for the L6/L7
      decommission sweep, no data-loss risk. **Cross-plan + Codex sports-alignment audit also done** (18 sports-touching
      files): 14 already correct on the post-migration future; 4 stale/confused fixed —
      `per-asset-group-bucket-layouts.md` + `sports-gcs-path-ssot.md` + `epics/sports_master.md` (PM@e71f4ded9),
      `e2e/011_features_sports_service.md` (PM@49f701ec1). The legacy-bucket-delete end-state is consistently reflected
      across plans/codex.
- [x] ✅ [DATA] P1. **Schema spot-check across dual-path same-data_type shards** (operator directive — pick union/best
      of both): where the same `(date, league, data_type)` exists in two layouts — MDPS prd(`category=`) vs legacy
      (`asset_group=`); instruments `sports_reference` vs `sports_reference_v2` vs `_v1_archive`; prd vs legacy-no-env —
      sample-compare parquet SCHEMAS + row counts per shard; if the "winner" has fewer cols/rows, switch dedup to
      keep-larger / column-union (CROSS-AG LESSON #5/#8). Capture the per-tree schema diff before the walk picks a
      winner. — market-tick-data-service@50a43aa7 | \_sample*schema() downloads+inspects parquet for \_SCHEMA_SAMPLE_N
      overlap shards per tree; logs per-shard verdict (PRD_LOSES_COLS_OR_ROWS / PRD_RICHER / schemas_match + row
      counts); per-tree entity-set verdict (SAME_ENTITIES / COMPLEMENTARY_ENTITIES) for the 3 sports_reference versions.
      **ACTUAL SCHEMA SPOT-CHECK RUN (sports-slot, real GCS data 2026-06-01)** on `entity=fixtures` 2018-01-02:
      `v1_archive` fixtures (41 cols: home_xg/away_xg + shots/corners/fouls/possession/passes + home_team/away_team +
      league/source/status/match_week) vs `v2` fixtures (32 cols: AF-native
      `af*_\_id`, score breakdowns     extratime/halftime/penalty, status_long/short, venue_id/city/name, round, timestamp) = **NEITHER is a superset**     (alarm) — BUT v1_archive's 41 cols ARE fully covered by the UNION of (`v2
      fixtures`∪`v2
      fixture_stats`(xG +     shots/corners/possession) ∪ current`understat_xg` (58 cols incl. team-detail + xG)); only 3 differ and they are     naming variants (`home_team`→`home_team_name`, `away_team`→`_\_name`, `league`→`league_name`).
      **VERDICT: v1_archive is COLUMN-superseded by the current split (understat_xg + v2 fixtures + v2 fixture_stats);
      v2 fixtures + understat_xg + fixture_stats are COMPLEMENTARY → keep all. No column-level data loss from treating
      v1_archive as superseded.**
- [ ] [DATA] P0. **v1_archive ROW-coverage gate (before E8 — sports-slot 2026-06-01)**: column-superseded ≠
      row-superseded. Before DROPPING `sports_reference_v1_archive`, verify its `(date, league, fixture_id)` ROW set ⊆
      the current split's rows (the v1_archive date-range/leagues are all present in
      `v2 fixtures`/`understat_xg`/`fixture_stats`). If v1_archive has older history or leagues the current split lacks
      → migrate those rows first (the reconcile's legacy-only computation must run at ROW granularity, not just
      entity/column). This is the row-level analogue of the column check above; do NOT drop v1_archive on
      column-coverage alone.

### CF-11 completeness — fetch-failure must be `attempted_failed`, NOT `empty_confirmed` (operator directive 2026-06-02)

> Operator: "when there is an API issue somewhere in IS or MTDS for sports, is it correctly doing `attempted_failed`
> where the attempt makes sense by fixtures / instrument / UAC bounds — RATHER THAN `empty_confirmed` which would not be
> complete?" This is CF-11 (the defi A7 fetch-swallow bug) with a sports twist: a **fixture EXISTED but the derived
> shard is empty** is almost certainly a masked fetch failure → `attempted_failed` (retry/backfill), NOT a false
> `empty_confirmed` that claims "we know there's nothing" and freezes the gap forever.

- [x] ✅ [DATA] P0. **Rebuild classifier: add match-day-empty → `attempted_failed`** (`rebuild_sports_manifest_v9.py`).
      Currently STEP 8 (line ~475) sends a match-day empty (`(league,date)` IN fixtures truthset) on a per-fixture
      derived data_type to `keep_src_zero` → `SOURCE_RETURNED_ZERO` `empty_confirmed`. FIX: if fixture EXISTS +
      data_type is **guaranteed-when-fixture-exists** (FIXTURES / FIXTURE_STATS / FIXTURE_EVENTS / STANDINGS — NOT
      INJURIES / cards / PLAYER_VALUES which can legitimately be zero) + within UAC source-coverage bounds + not a
      known-gap → classify as **`attempted_failed`** (`record_failed`) so it backfills, NOT `empty_confirmed`.
      Conservative per-data_type guarantee set (a wrongly-upgraded INJURIES-empty is a false failure; a wrongly-kept
      FIXTURE_STATS match-day empty is silent incompleteness — the operator's stated priority is the latter is worse). —
      market-tick-data-service@8ffb2acd | step 6.7 added to \_classify_empty_row; \_FIXTURE_GUARANTEED_DATA_TYPES
      (FIXTURES/FIXTURE_STATS/FIXTURE_EVENTS/FIXTURE_LINEUPS/STANDINGS/ODDS/ODDS_SNAPSHOT/ODDS_MOVEMENT); conservative
      exclusions: INJURIES/PLAYER_STATS/XG/trades/etc stay SOURCE_RETURNED_ZERO; write loop calls record_failed with
      error=CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE; dry-run histogram reports mark_attempted_failed count separately. QG
      GREEN. VM dry-run needed for real counts (VM-pending — no GCS access locally).
- [x] ✅ [DATA] P0. **Rebuild: re-emit existing `attempted_failed` rows v9** (status preserved). The rebuild currently
      only re-emits empty_confirmed + captured (line ~679); the `other` (attempted_failed: 164 MDPS + 178,025
      instruments) rows are left v8. Re-emit them via the writer with `attempted_failed` status preserved so they're
      v9 + still flagged for backfill (NEVER silently relabel a failure to empty). — market-tick-data-service@8ffb2acd |
      other_df loop added after captured_df loop; iterates other_mask rows filtered to attempted_failed; calls
      record_failed(error=existing_error_reason or UNKNOWN_FETCH_FAILURE_PRESERVED_FROM_V8); dry-run reports
      reemit_attempted_failed count. QG GREEN. VM dry-run needed for real counts (VM-pending).
- [x] ✅ [CODE] P0. **Write-path CF-11 audit + fix (IS + MTDS sports adapters)**: on a genuine API error
      (timeout/5xx/429/auth) for a `(league,date)` where a fixture exists / instrument valid / within UAC coverage
      bounds, the handler MUST `record_failed` (→ `attempted_failed`) via `classify_venue_error()`, NOT `record_empty`.
      Grep the sports fetch paths in instruments-service (`sports_fixtures_daily_repoll.py` + the per-entity handlers in
      `orchestrator.py`) + MTDS sports handlers for `except … record_empty` / bare `return []` swallows; trace each to
      its `record_*` call; gate the empty-vs-failed decision on fixture-existence + UAC bounds (the writer analogue of
      the rebuild fix above). The 2026-06-01 writer fix (instruments-service@608e7ca7) handled the typed-EMPTY path;
      this verifies the FAILED path is not masked as empty. **IS PORTION DONE** — instruments-service@ceab7720 | trigger
      path (sports_fixtures_daily_repoll.py) already correct from 608e7ca7; **orchestrator.py batch path had a REAL
      CF-11 BUG** in the per-fixture entity zero-rows branch — a PARTIAL failure (`_fail_count > 0` but
      `< len(fixture_ids)`, total 0 rows) fell through to `empty_confirmed(EXPECTED_NO_FIXTURE)` instead of
      `record_failed` → masked a real gap as confirmed-empty (frozen, never backfilled). Fixed: any `_fail_count > 0` +
      zero rows → `record_failed`. 3 unit tests (all-fail / partial-fail / all-succeed). QG GREEN.
- [x] ✅ [CODE] P0. **Write-path CF-11 — MTDS sports-ingest portion** (separate from the IS fix above): audit the MTDS
      sports MDPS odds-ingest handlers for the same masked-failure pattern — on an odds-API error for a (bookmaker,
      league, fixture-day) cell, `record_failed` not `record_empty`; gate empty-vs-failed on fixture-existence + UAC
      coverage. Mirror the IS orchestrator fix (instruments-service@ceab7720). Repo: `market-tick-data-service`. FIXED:
      `OddsApiAdapter._discover_fixtures()` was swallowing `aiohttp.ClientResponseError` / `ClientError` and returning
      `[]` on any error — only HTTP 422 (legitimate "no historical data") now returns `[]`; all other errors re-raise so
      the exception propagates through `download_batch()` → `_process_sports_venue_with_leagues()` →
      `failed_shards[venue]` → manifest sentinel pass → `record_failed(attempted_failed)` instead of `record_empty`.
      Already-correct paths: orchestrator sentinel pass (lines 3353-3466) already routes `failed_shards` to
      `record_failed`; per-timestamp `aiohttp.ClientResponseError` `continue` is partial-day (acceptable — only full
      discovery failure was masked). 5 unit tests (422→empty, 5xx raise, 401 raise, ClientError raise, 200 OK
      no-regression). QG GREEN. — market-tick-data-service@c96245b7 | CF-11 MTDS odds_api \_discover_fixtures re-raises
      on API errors (not just 422)

### KEYSTONE redesign — FIXTURES are the truth set (operator directive 2026-06-01)

> Operator: "fixtures should be the truth set… sports is derived data from instruments; everything per-fixture should
> use the API-Football fixtures ALREADY IN cloud storage as canonical, WITHOUT re-querying." This SUPERSEDES the
> season-window approach for the no-fixture determination (season-window can't catch in-season no-match days, and fails
> on provider-suffixed/cup leagues that don't resolve via `get_league`).

- [x] ✅ [DATA] P0. **Rebuild keystone: join the instruments-store `FIXTURES` truthset (API-Football, in GCS) for the
      no-fixture relabel — BOTH surfaces.** For every empty `(league_id, date, per-fixture-data_type)` cell: if NO
      fixture exists in the FIXTURES truthset for that (league, date) → `EXPECTED_NO_FIXTURE`; else (fixture existed but
      this derived shard empty) → `SOURCE_RETURNED_ZERO` / appropriate reason. Keep season-window only for
      `PRE_SEASON`/`POST_SEASON` framing. Read the FIXTURES parquets from `instruments-store-sports-prd` (do NOT
      re-query API-Football). This fixes BOTH P1 refinements at once: (a) MDPS in-season no-match days, (b) the
      provider-suffixed/cup leagues (`SCOTTISH_LEAGUE_CUP_185` etc.) that don't resolve via the registry — the truthset
      is keyed by the SAME league_id as the manifest, so resolution is N/A. — market-tick-data-service@699c58e9 | step
      6.5 FIXTURES truthset join: truth set built ONCE from loaded index (FIXTURES captured UNION per-fixture-derived
      captured); raw league_id (upper+stripped) used for lookup (NOT canonicalised — catches SCOTTISH_LEAGUE_CUP_185
      etc.); --fixtures-index-bucket for MDPS cross-surface load. Synthetic verification (instruments surface, 2579
      dates, 80 match days): 14,994 SRZ→EXPECTED_NO_FIXTURE (relabel_no_fixture_truthset), 3,059 stay SRZ (match days —
      correct). SCOTTISH_LEAGUE_CUP_185 8-date sample: no-match days→EXPECTED_NO_FIXTURE; match days→SRZ; FIXTURES
      itself→SRZ (circular protection). EPL mid-week no-match→EXPECTED_NO_FIXTURE. QG GREEN. VM production dry-run
      pending E3 drain (GCS index inaccessible locally — consolidator shards). Expected real-data shift: ~15,609
      instruments SRZ→EXPECTED_NO_FIXTURE for SCOTTISH_LEAGUE_CUP_185 alone; MDPS in-season no-match days via
      instruments cross-load.
- [x] ✅ [DATA] P1. **"15,700 unresolved leagues" DIAGNOSED**: it is NOT 15k unique leagues — it is **ONE league**
      (`SCOTTISH_LEAGUE_CUP_185`, API-Football league id 185) × **2,579 unique dates** × 8 per-fixture data_types
      (FIXTURES/FIXTURE_EVENTS/FIXTURE_LINEUPS/FIXTURE_STATS/INJURIES/LEAGUES/PLAYER_STATS/STANDINGS) = 15,702 rows
      (15,609 empty / 93 captured). It is a **CUP** that plays a handful of days/year → ~2,500 of those days are
      genuinely no-fixture (→ `EXPECTED_NO_FIXTURE` once the FIXTURES-truthset join lands). The `_185` is the raw
      API-Football provider id — the league_id was **never canonicalised** (CF-7 write-path gap: 278,268 manifest rows
      carry provider-id-suffixed league_ids). Two fixes: (1) FIXTURES-truthset relabel (above) resolves the empties
      regardless of canon; (2) **CF-7 league-id canonicalisation** todo below for the writer + migrator.
- [x] ✅ [DATA] P1. **CF-7 league_id canonicalisation — UAC SSOT done** (unified-api-contracts@409753bd):
      `canonicalize_league_id(raw: str) -> str` added to `provider_league_ids.py`, exported from
      `canonical/domain/sports/__init__.py` + `sports.py` facade. Provider-id-verified suffix strip: strips `_<digits>`
      only when the digit matches a registered provider id (api_football / footystats / understat / transfermarkt /
      soccer_football_info) for the base canonical key. **Registry-gap finding**: `SCOTTISH_LEAGUE_CUP_185` is NOT
      auto-stripped — 185 is a historical AF season id, NOT the canonical `api_football_id=182`; function returns
      unchanged conservatively. IS writer + MTDS migrator must use a **direct rewrite table** for these 278,268 rows.
      Import path: `from unified_api_contracts.sports import canonicalize_league_id`. 8 unit tests pass (QG green,
      basedpyright 0 errors). **Consumers (IS writer + MTDS migrator) wire next — tracked below.**
- [x] ✅ [DATA] P1. **CF-7 league_id canonicalisation — IS writer (done)**: wired `canonicalize_league_id` into
      `_canonical_league_id()` choke-point in `instruments_service/engine/orchestrator.py` as a second pass after the
      numeric api_football id lookup. All 28+ per-league write sites (FIXTURES, FIXTURE_STATS, STANDINGS, INJURIES,
      ODDS, XG, PLAYER_STATS, per-fixture entity walks) now born-canonical. 8 unit tests in `TestCanonicalLeagueIdCF7`
      (provider-suffixed strip, unresolved passthrough, numeric pass1→pass2, idempotent, whitespace). QG green. —
      instruments-service@db187587 | canonicalize_league_id wired into \_canonical_league_id choke-point (Pass 2 after
      numeric resolution). **MTDS migrator + rebuilder DONE** — market-tick-data-service@df391e7c: wired
      `canonicalize_league_id` into `_canon_mdps_raw_prd()` in `migrate_sports_canonical_v9.py` (applied to
      `league_id_raw` BEFORE dedup so canonical ids land in migrated GCS paths) + `_canonicalize_row_key_league_id()`
      helper in `rebuild_sports_manifest_v9.py` (applied in all 3 write loops: empty_confirmed, captured,
      attempted_failed; truthset lookup still uses RAW league_id per comment at step 6.5 — correctly catches
      SCOTTISH_LEAGUE_CUP_185). Conservative passthrough preserved: unresolved season-suffix ids (e.g.
      SCOTTISH_LEAGUE_CUP_185) unchanged. 7 + 9 unit tests. QG GREEN.

### C — single-walk (v9 + partition + typed reasons + source path→column + canonical verify)

- [x] ✅ [DATA] P0. **Phase 0 — layout audit DONE (shallow-signature pass, sports slot 2026-06-01)** via
      `cf_layout_audit_2026_06_01.py` on all 3 surfaces (MDPS-prd + MDPS-legacy + instruments-store-prd). **Full layout
      map below**; per-layout object counts come with the VM walk's progress counters. Findings that EXPAND the migrator
      design (scope-is-a-prior): (1) MDPS-prd raw is STILL `category=sports` while MDPS-**legacy** raw is `asset_group=`
      — INVERTED AG key, like prediction (the canonical-named bucket is LESS canonical on the AG segment → the migrator
      converges both onto `asset_group=`); (2) instruments-store has **8 distinct layouts** incl. 3 reference versions
      (`sports_reference` current / `sports_reference_v1_archive` / `sports_reference_v2`) needing
      reconcile-to-freshest, a bare `day=/venue=/{uuid}` instrument tree, a hyphen-delim
      `instrument_availability/by-date/day-…`, a legacy `availability_index/instruments-service.parquet` (OLD manifest
      format, superseded by `_index/`), + `_audits`/ `_smoke_test` ARTIFACT trees (skip — not data). The migrator is
      layout-dispatching across ALL non-artifact trees.

> **📐 Phase-0 LAYOUT MAP (sports slot 2026-06-01, `cf_layout_audit` shallow-signature pass)** — the migrator MUST
> handle every non-artifact layout or it under-migrates (slot-2 DeFi lesson):
>
> | Surface          | Tree                                              | Layout signature                                                                     | Disposition                                                        |
> | ---------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
> | MDPS-prd (canon) | `processed/by_date/`                              | `day=/data_type=/league_id=/timeframe=`                                              | candles → add `asset_group=`+`pipeline_mode=`                      |
> | MDPS-prd (canon) | `raw_tick_data/by_date/`                          | `day=/category=sports/data_source=/venue=/league_id=/instrument_type=/data_type=`    | **`category=`→`asset_group=`** + insert `pipeline_mode=`           |
> | MDPS-legacy      | `raw_tick_data/by_date/`                          | `day=/asset_group=sports/data_source=/venue=/league_id=/instrument_type=/data_type=` | near-canon (missing `pipeline_mode=`); reconcile vs prd (INVERTED) |
> | instr-store-prd  | `day=YYYY-MM-DD/venue=/{uuid}.parquet`            | bare top-level instrument defs                                                       | → canonical reference layout                                       |
> | instr-store-prd  | `sports_reference/by_date/`                       | `day=/entity=` (live reference)                                                      | freshest → canonical                                               |
> | instr-store-prd  | `sports_reference_v2/by_date/`                    | `day=/entity=` (richer fixture_stats)                                                | complementary → migrate                                            |
> | instr-store-prd  | `sports_reference_v1_archive/by_date/`            | `day=/entity=`                                                                       | archived → superseded (verify no canon-only)                       |
> | instr-store-prd  | `instrument_availability/by-date/day-…/{league}/` | hyphen-delim                                                                         | reconcile / verify                                                 |
> | instr-store-prd  | `availability_index/instruments-service.parquet`  | OLD manifest format                                                                  | superseded by `_index/` (drop after verify)                        |
> | instr-store-prd  | `_audits/` · `_smoke_test/` · `_catalogue/`       | artifacts                                                                            | **SKIP — not data**                                                |
>
> Evidence: `/tmp/cf_sports_layout.log` (reproduce:
> `cf_layout_audit_2026_06_01.py market-data-tick-sports-prd-… market-data-tick-sports-… instruments-store-sports-prd-…`).

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
      locally if scope is small (P0 decides). **SCRIPTS READY** — `migrate_sports_canonical_v9.py` (E2) +
      `rebuild_sports_manifest_v9.py` (E5/E6) at market-tick-data-service@eb5eaad2. Dry-run verified 2026-06-01: MDPS
      prd raw 70 objects + candles 50 + legacy 140 = 260 planned for 3-day window (all `category=`→`asset_group=`,
      pipeline_mode= inserted). VM execution pending E3 drain.
- [ ] [DATA] P0. C-reasons RIDER (the keystone) — **CODE NOW COMPLETE; VM production run still pending E3 drain.**
      Composite 9-step classifier: steps 1–7 (season/deprecated/free-text/source-gates/calendar) SHIPPED @680dff5f;
      **step 6.5 FIXTURES truthset join SHIPPED @699c58e9** (operator directive 2026-06-01). Instruments dry-run
      @680dff5f: 368,036 relabels (288k season + 57k deprecated + 23k free-text); ~15,700 stayed SRZ (unresolved
      leagues). Step 6.5 will catch those ~15,700 on the VM run. MDPS: with step 6.5 + cross-surface instruments load,
      in-season no-match days will now relabel to EXPECTED_NO_FIXTURE (quantity determined by VM run). Re-flip this todo
      to DONE only after the VM production run shows EXPECTED_NO_FIXTURE > 0 on MDPS and instruments SRZ ≈ 0 (only
      genuine zero-data match days remain). Original intent: relabel every blank / mislabeled empty row to the correct
      typed UAC reason via the coverage oracle (`clip_dates_to_source_coverage` / `is_in_known_gap` / season /
      transfer-window / fixture-status / league-coverage) — the table in § Sports honest-absence. Snapshot-protected,
      idempotent, oracle-driven (never re-derived per consumer). — market-tick-data-service@680dff5f | composite 8-step
      classifier shipped: step4=is_expected_for_source, step5=footystats_season_status_for_day (ALL sources),
      step6=get_league_fixture_calendar, step7=is_in_known_gap, step8=SOURCE_RETURNED_ZERO; data_type→source bridge via
      SPORTS_DATA_TYPE_TO_SOURCE; league_id canon via get_league(.upper()); QG GREEN. —
      market-tick-data-service@699c58e9 | step 6.5 FIXTURES truthset join: builds truth set from FIXTURES captured UNION
      per-fixture-derived captured; raw league_id lookup (bypasses get_league() so provider-suffixed IDs like
      SCOTTISH_LEAGUE_CUP_185 match); --fixtures-index-bucket for MDPS cross-load; QG GREEN. Synthetic verified (2579
      dates, 80 match days): 14,994 SRZ→EXPECTED_NO_FIXTURE; 3,059 stay SRZ; circular protection correct. **DRY-RUN
      results (2026-06-01, instruments @680dff5f — step 6.5 NOT yet in that run)**: MDPS (584,177 empties): 0 relabels.
      Instruments (1,909,553 empties): 288,434→PRE/POST_SEASON + 56,624→DEPRECATED + 22,978→NO_FIXTURE + 13,176
      preserved = 368,036 total. ~15,700 stayed SRZ (unresolved leagues — will be caught by step 6.5).
- [ ] [DATA] P1. **MDPS in-season no-fixture refinement (open before E8 CF-5 verify — sports-slot 2026-06-01)**: the
      season oracle is season-WINDOW granularity, so it marks every in-season day as a fixture day → it CANNOT catch
      in-season days with no actual match (most leagues play 1–2 days/week), which should be `EXPECTED_NO_FIXTURE`, not
      `SOURCE_RETURNED_ZERO`. The 584,177 MDPS empties all kept SRZ on that basis. **Resolve before declaring CF-5 GREEN
      on MDPS**: (a) read the MDPS odds writer's row-creation logic — does it attempt EVERY in-season day or only actual
      fixture days? If only fixture days → SRZ is genuinely correct (an attempted fixture the bookmaker didn't price) →
      CF-5 GREEN, document + close. (b) If it attempts every in-season day → join the instruments-store FIXTURES
      truthset (actual per-day fixtures) to relabel the genuine no-match in-season days → `EXPECTED_NO_FIXTURE` (the
      keystone bites on MDPS too). Either outcome is fine but MUST be DETERMINED + documented — an undiagnosed 584k SRZ
      block is exactly the "blanket reason" the keystone exists to eliminate.
- [ ] [DATA] P1. **Unresolved-league residual (CF-7 / NO_MAPPING — before E8)**: ~15,700 instruments-store rows
      (`SCOTTISH_LEAGUE_CUP_185` 15,609 + 86 singleton leagues) failed `get_league()` resolution → stayed SRZ with a
      logged tally. Diagnose: are these canonical leagues missing from the UAC `provider_league_ids` registry (→ add
      mapping so the oracle classifies them) OR provider-league-id artifacts (→ `EXPECTED_NO_MAPPING`)? Resolve so 0
      empties stay SRZ purely because the league didn't resolve.
- [ ] [DATA] P1. C-source RIDER (`data_source_provenance` Phase 4): path→column migration — read `source` from the path
      segment (`data_source=…`, `pipeline_mode=batch_…`), write it into the `source` column on every row, re-consolidate
      into the `_index` (multi-source `FIXTURES` = two rows). Executed in THIS walk — do NOT run a separate sports
      source walk. **SCRIPT READY** — `rebuild_sports_manifest_v9.py` extracts source via `_source_from_row()` and
      re-emits captured rows with `writer.add(source=...)`. VM execution pending E3 drain.
- [x] ✅ [CODE] P1. C-writer: instruments-service sports handlers emit the typed fixture/season/transfer-window reasons
      at write time (writer analogue of defi A1/A2b) so future writes are honest — no blank/`SOURCE_RETURNED_ZERO` for a
      no-fixture / off-season / out-of-window / uncovered-league day. — instruments-service@608e7ca7: wired
      `is_expected_for_source` oracle into `sports_fixtures_daily_repoll.py` zero-fixture path; per-league
      EXPECTED_PRE_SOURCE_COVERAGE_START / EXPECTED_NO_FIXTURE / SOURCE_RETURNED_ZERO emitted; 3 new unit tests; QG
      GREEN.

### Dead-bucket regression gate — refactor read/write paths to canonical BEFORE the delete (operator directive 2026-06-02)

> Operator: "have we refactored read AND write cloud-storage paths across the board to match the new canonical form for
> the asset groups we cover — in the CODE + the tests that feed quality gates — to avoid regression? Even though the
> migrations haven't run, the code itself must not regress by association with DEAD buckets once they're deleted. Same
> for data-status in the deployment API + UI, which resolve many bucket names / menu conventions / data_type conventions
> / manifest-reading conventions." The legacy buckets get DELETED at E8 → any code/test/UI still resolving the no-env
> sports buckets (`market-data-tick-sports`, `instruments-store-sports`, `features-*-sports`) or stale manifest/path
> conventions will BREAK. This gate is BEFORE the dry-run/delete: the code must already speak ONLY canonical.

- [ ] [CODE] P0. **Read/write path canonicalisation sweep (sports — all repos)**: confirm EVERY sports bucket lookup
      routes through `resolve_bucket_name(…, asset_group="sports", env=…)` → `-prd-` canonical. **REAL DEAD-BUCKET
      EXPOSURE FOUND (sports-slot grep 2026-06-02 — these read the NO-ENV legacy buckets E8 DELETES → BREAK on delete)**:
      - **UTL `unified_trading_library/sports_fixtures.py:9`** reads the FIXTURES truthset from
        `gs://instruments-store-sports-{pid}/…` (NO ENV) — **the keystone truthset depends on this**; legacy delete
        breaks the no-fixture relabel. → env-tiered.
      - **UTL `instruments_preflight/__init__.py:23`** `bucket="instruments-store-sports-{pid}"` (no env).
      - **UTL `instrument_lifecycle_loader.py:46,54`** `"sports":"instruments-store-sports-{pid}"` (no env) (+ `:47`
        prediction no-env — slot-3 lane, flag don't fix).
      - **UAC FACADE ROOT — `sports.gcs_paths.bucket_name(...)` returns the NO-ENV form**
        (`market-data-tick-sports-{PID}` / `instruments-store-sports-{PID}`), pinned by
        `unified-api-contracts/tests/unit/test_gcs_paths_facade.py:30,49,50,72`. CROSS-AG inconsistency (UTL
        `resolve_bucket_name` SSOT → `-prd-`; UAC `bucket_name` facade → no-env) affecting prediction/defi/cefi/tradfi →
        **coordinate at `defi_manifest…` §MASTER; do NOT unilaterally change the cross-AG facade from the sports lane** —
        fix sports READERS to use `resolve_bucket_name` instead of the facade.
      - **e2e sports scripts hardcode no-env**: `e2e-testing/scripts/sports/run_weekly_pipeline.py:43` +
        `audit_production_vs_e2e.py:36`. → canonical.
      Fix the sports-scoped readers/scripts/tests; flag the cross-AG UAC facade for coordination.
- [ ] [CODE] P0. **deployment-api + UI data-status canonical resolution (sports)**: the data-status surface resolves
      MANY bucket names / menu conventions / data_type conventions / manifest-reading conventions per asset_group — audit
      `deployment-api/deployment_api/services/data_status*.py` (+ the `data_status_mock.py` SPORTS map) + the
      deployment-ui/unified-trading-system-ui data-status views for any sports bucket/path/data_type/manifest convention
      that resolves a to-be-deleted legacy bucket or a stale (v8/`category=`/no-`pipeline_mode=`) layout. Point them ALL
      at the canonical `-prd-` v9 form. UI changes need the playwright gate (`pw:L2 ✓` + regression spec) per PLAN_FORMAT §9.
- [ ] [CODE] P0. **Tests-feeding-QG use canonical buckets/paths (sports)**: every sports test (unit + integration) that
      references a bucket/path/manifest convention must use the canonical `-prd-` v9 form, so QG REGRESSION-CATCHES any
      future dead-bucket association. Grep sports tests for legacy bucket/path literals; update to canonical. (This is the
      mechanism that makes the regression gate self-enforcing — a reverting change fails QG.)
- [ ] [DATA] P1. **278k provider-season-suffixed league_ids rewrite table** (dry-run-informed): `canonicalize_league_id`
      conservatively leaves `SCOTTISH_LEAGUE_CUP_185` etc. unchanged (185 = AF SEASON id, not the league id 182). After
      the dry-run enumerates the actual `{LEAGUE}_{seasonid}` set, build a direct rewrite table (strip the season suffix
      when the base resolves + the suffix is a known AF season id for that league) → canonical. Not guessed pre-dry-run.

### Verify + handoff to decommission

- [ ] [DATA] P0. Post-walk: fresh `_index` read — `schema_version=9` (data-state) for 100% of rows; `pipeline_mode=`
      partition present + non-null; `source` column populated (path→column complete; multi-source = two rows); venue/
      league/data_type canonical only; **0 blank/untyped empty reasons** (every empty cell carries a typed fixture/
      season/transfer-window/genesis reason); `available_at` honest. 0 legacy-only cells. C-GREEN signal for
      `bucket_name_ssot…` Phase 6/7 sports legacy bucket decommission.

## Execution checklist (grounded — next session, finish in full)

> CF debt is in the `_index` MANIFEST + object PATHS, NOT the raw tick parquets. See
> `plans/audit/results/cf_data_state_audit_slot3_2026_06_01.md` § MECHANISM + layout map. sports raw = full hive
> `day=/category=/data_source=/venue=/league_id=/instrument_type=/data_type=` (parquet already has
> `source`+`data_source` cols). **Keystone**: 584,177 empties are blanket `SOURCE_RETURNED_ZERO` — relabel to typed
> fixture/season reasons.
>
> ⚠️ **IRREVERSIBLE — E8 DELETES legacy `market-data-tick-sports` permanently.** Do not run E2–E8 until the canonical
> target (v9, `day=/pipeline_mode=/asset_group=sports/…`, source col, typed reasons) is CONFIRMED CORRECT at verify. One
> pass, no confusion — once legacy is deleted it is gone.

- [x] ✅ [DATA] P0. E1 Phase-0 layout audit DONE on all 3 surfaces (`market-data-tick-sports-prd` + `-sports` legacy +
      `instruments-store-sports-prd`) via `cf_layout_audit_2026_06_01.py` + CF data-state via `cf_manifest_audit`. Full
      layout map + scope-expansions captured in § P0 above (MDPS raw `category=` vs legacy `asset_group=` INVERTED;
      instr-store 8 layouts; 2.68M instr rows / 1.9M empties; non-canonical free-text reason; CF-7 drift). Evidence:
      `/tmp/cf_sports_{mdps,instr,layout}.log` — PM@07f7ace03.
- [x] ✅ [DATA] P0. E2 Build/extend `migrate_sports_canonical.py` to v9-canonical (perf-contract):
      `category=`→`asset_group=sports`, add
      `pipeline_mode=batch_{api_football,footystats,odds_api,understat,transfermarkt,…}`; keep `source` col (already
      present). — market-tick-data-service@1036de20 | `migrate_sports_canonical_v9.py` (new) layout-aware: MDPS
      raw+candle, instruments-store 5 trees, CF-7 normalise, ThreadPoolExecutor + gcs_copy_object, dry-run default
- [ ] [DATA] P0. E3 Confirm `sports-scheduler` writer drained; snapshot the sports `_index`(es).
- [ ] [DATA] P0. E4 Dry-VM → timing → optimise → full-VM run (786k index rows; no fire-and-forget).
- [ ] [DATA] P0. E5 **KEYSTONE reason relabel** (CF-5): composite 9-step classifier now FULLY SHIPPED (instruments 368k
      relabels from 8-step + step 6.5 FIXTURES truthset join for ~15,700 unresolved-league rows). VM production run
      pending E3 drain. — market-tick-data-service@680dff5f | composite 8-step classifier: instruments 368,036 relabels;
      MDPS 0. QG GREEN. — market-tick-data-service@699c58e9 | step 6.5 FIXTURES truthset join SHIPPED: truth set from
      FIXTURES captured UNION per-fixture-derived captured; raw league_id lookup (SCOTTISH_LEAGUE_CUP_185 etc. now
      matched); --fixtures-index-bucket for MDPS cross-load. Synthetic-verified: no-match days→EXPECTED_NO_FIXTURE,
      match days→SRZ, circular protection correct. QG GREEN. VM run pending E3 drain + E4.
- [x] ✅ [DATA] P0. E6 Manifest rebuild: `ManifestWriter` stamping `source` (path→col lift) + `pipeline_mode` +
      `available_at` → consolidator → v9. ~~Also fix the writer to emit typed reasons going forward (CF-5 write-path) —
      DONE (C-writer@instruments-service@608e7ca7).~~ — market-tick-data-service@1036de20 |
      `rebuild_sports_manifest_v9.py` re-emits captured rows via writer.add(source=, pipeline_mode=) + relabelled
      empties via record_empty; ManifestWriter(per_vm_shards=True).flush()
- [ ] [DATA] P1. E7 CF-7 relabel: ODDS case-drift (`ODDS`/`ODDS_SNAPSHOT` upper vs `odds_horizon_bucket` lower) + blank
      venue.
- [ ] [DATA] P0. E8 Verify: `cf_manifest_audit_2026_06_01.py` on both sports surfaces → CF-1…CF-12 GREEN (esp. 0 blanket
      SOURCE_RETURNED_ZERO); flip CF-coverage in `sports_master_audit_instructions.md`. ⚠️ IRREVERSIBLE — only after
      GREEN: hand C-GREEN to L6 → **delete legacy `market-data-tick-sports` permanently**.

## Deferred work after 2026-06-01 (sports-slot pickup session)

| Item                                                         | State                     | Evidence / next owner                                                                                                              |
| ------------------------------------------------------------ | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| E1 Phase-0 layout + CF audit (both surfaces)                 | ✅ DONE                   | PM@07f7ace03 — full layout map + scope-expansions (instr-store 8 layouts / 2.68M rows / inverted AG)                               |
| E2 v9 migrator (`migrate_sports_canonical_v9.py`)            | ✅ BUILT + dry-run        | mtds@eb5eaad2 — 260 objs/3-day window; layout-aware; gcs_copy_object; **VM `--apply` pending E3 drain**                            |
| E5/E6 rebuilder + composite keystone classifier              | ✅ CODE COMPLETE (9-step) | mtds@680dff5f (8-step) + mtds@699c58e9 (step 6.5 truthset join) — synthetic-verified; **VM rebuild pending E3 drain**              |
| E6 write-path (typed reasons going forward)                  | ✅ SHIPPED                | instruments-service@608e7ca7                                                                                                       |
| FIXTURES truthset join (step 6.5)                            | ✅ SHIPPED (code)         | mtds@699c58e9 — no-match days→EXPECTED_NO_FIXTURE via truth set; MDPS cross-load via --fixtures-index-bucket; VM run pending E3+E4 |
| MDPS in-season no-fixture refinement                         | 🟡 ADDRESSED by step 6.5  | truthset join now handles in-season no-match days when MDPS cross-loads from instruments-store; confirm on VM run                  |
| Unresolved-league residual (~15,700)                         | 🟡 ADDRESSED by step 6.5  | SCOTTISH_LEAGUE_CUP_185 (raw league_id lookup bypasses get_league()) now classified by truthset; confirm on VM run                 |
| E3 fleet drain (shared w/ slot-2)                            | ⛔ GATED                  | pre-migration drain GCP+AWS writers → consolidate → snapshot; coordinated at `epics/mtds_mdps_master`                              |
| E4 VM dry → full walk (786k + 2.68M)                         | ⛔ GATED                  | VM asia-northeast1, no fire-and-forget; after E3                                                                                   |
| E7 CF-7 relabel + E8 verify + **IRREVERSIBLE legacy delete** | ⛔ GATED                  | only after CF-1…CF-12 GREEN on real data-state + drain + operator gate                                                             |

**Net**: all CODE (migrator + rebuilder + composite keystone + writer-fix) is built, QG-green, dry-run-verified, and on
LDR. The remaining work is OPERATIONAL (VM whole-corpus walk under the fleet drain) + 2 P1 keystone refinements — none
of which is bypassable by an interactive slot. The IRREVERSIBLE legacy-bucket delete (E8) stays gated on
CF-GREEN-on-real- data + the fleet drain + operator.

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
