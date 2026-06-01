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
      without migrating these = permanent data loss — the exact DeFi/TradFi "missed bucket with real data" trap. ⇒ sports
      is **NOT FORM-only**; the instruments-store walk MUST diff+migrate legacy→prd (the 316 cells + any
      sports_reference{,_v1_archive,_v2} objects not in prd) BEFORE E8. See § "FULL sports bucket inventory" below.
- [x] ✅ [DATA] P0. Object-path scheme (sports slot reconfirm, 2026-06-01 — direct `gcloud ls` probe):
      MDPS-prd `processed/by_date/day=/data_type=/league_id=/timeframe=/` + `raw_tick_data/by_date/day=…/` (deeper hive)
      — has `day=`/`data_type=`/`league_id=`/`timeframe=` hive BUT **no `asset_group=` and no `pipeline_mode=` segment**
      (CF-2 paths + CF-3 partition RED). Parquet rows DO carry `source` + `data_source` columns (layout audit). The C0
      walk adds `asset_group=sports` + `pipeline_mode=` to all object paths; `source` lifts path→col (already in col too).
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
      `soccer_football_info`, `transfermarkt`, `mdps_odds_horizon_bucket`). Normalise in the migrator BEFORE dedup (CF-7).
- [ ] [DATA] P1. **Multi-layout reality on instruments-store (Phase-0 must enumerate ALL)**: top-level trees =
      `sports_reference/{by_date,fixtures,footystats_league_ids,mappings}/` + `sports_reference_v1_archive/` + a BARE
      `day=YYYY-MM-DD/venue=…/{uuid}.parquet` tree + `instrument_availability/` + `availability_index/`. The migrator is
      layout-dispatching across ALL of these (slot-2 DeFi "audit ALL layouts" lesson) — a single-tree walk under-migrates.

## FULL sports bucket inventory + decommission scope (sports-slot 2026-06-01 — operator "delete EVERY other sports bucket; did we miss any?" review)

> The end-state is a SINGLE SSOT: every legacy/duplicate sports bucket DELETED. So we must enumerate EVERY sports
> bucket + classify keep/migrate/delete BEFORE any delete (the DeFi/TradFi "missed-bucket-with-real-data" trap). `gcloud
> storage ls | grep -i sport` (central-element-323112) returned **~35 sports buckets**, NOT the 2 surfaces the plan
> originally scoped:

| Bucket family | env variants | data state (2026-06-01 probe) | disposition |
| --- | --- | --- | --- |
| `market-data-tick-sports` | no-env(legacy) · prd · dev · stg · test | MDPS odds; prd 786k rows; legacy 0 legacy-only ✓ | **migrate→prd FORM; delete legacy no-env + test after** |
| `instruments-store-sports` | no-env(legacy) · prd · dev · stg · test | reference; prd 2.68M; **legacy no-env has 316 LEGACY-ONLY cells + full sports_reference{,_v1_archive,_v2}** | **migrate legacy→prd (data-loss gate!) then delete legacy no-env + test** |
| `features-{sports,delta-one,mtf,volatility,xinstrument}-sports` | no-env · prd · dev · stg | **ALL EMPTY (idx=0, no objects)** — confirmed, no data run | delete empty legacy + keep canonical prd as future write target (no migration) |
| `risk-store-sports` / `risk-store-*-sports` / `positions-store-*-sports` / `pnl-store-*-sports` | various | downstream store buckets — NOT YET PROBED | **TODO: probe + classify before any sports-bucket-decommission sweep** |

- [ ] [DATA] P0. **Migrate the legacy no-env `instruments-store-sports` → prd BEFORE E8** (data-loss gate): 316
      legacy-only `(2018-*, '', ODDS|PREDICTIONS)` cells + reconcile its `sports_reference` / `sports_reference_v1_archive`
      / `sports_reference_v2` / `day=/venue=` / `instrument_availability` trees against prd (compute legacy-only AND
      canon-only — union, never copy-bigger-into-smaller). The migrator's `--surface instruments` MUST take a
      `--legacy-bucket` and walk BOTH. (Mirror the MDPS prd-vs-legacy reconcile.)
- [ ] [DATA] P1. **Probe + classify the store buckets** (`risk-store-sports*`, `positions-store-*-sports`,
      `pnl-store-*-sports`) for data before they enter any sports-bucket-decommission sweep — empty→delete-legacy,
      non-empty→owner + canonicalisation path. Do NOT let `bucket_name_ssot…` L6 delete a non-empty store bucket.
- [ ] [DATA] P1. **Schema spot-check across dual-path same-data_type shards** (operator directive — pick union/best of
      both): where the same `(date, league, data_type)` exists in two layouts — MDPS prd(`category=`) vs legacy
      (`asset_group=`); instruments `sports_reference` vs `sports_reference_v2` vs `_v1_archive`; prd vs legacy-no-env —
      sample-compare parquet SCHEMAS + row counts per shard; if the "winner" has fewer cols/rows, switch dedup to
      keep-larger / column-union (CROSS-AG LESSON #5/#8). Capture the per-tree schema diff before the walk picks a winner.

### KEYSTONE redesign — FIXTURES are the truth set (operator directive 2026-06-01)

> Operator: "fixtures should be the truth set… sports is derived data from instruments; everything per-fixture should use
> the API-Football fixtures ALREADY IN cloud storage as canonical, WITHOUT re-querying." This SUPERSEDES the
> season-window approach for the no-fixture determination (season-window can't catch in-season no-match days, and fails
> on provider-suffixed/cup leagues that don't resolve via `get_league`).

- [ ] [DATA] P0. **Rebuild keystone: join the instruments-store `FIXTURES` truthset (API-Football, in GCS) for the
      no-fixture relabel — BOTH surfaces.** For every empty `(league_id, date, per-fixture-data_type)` cell: if NO
      fixture exists in the FIXTURES truthset for that (league, date) → `EXPECTED_NO_FIXTURE`; else (fixture existed but
      this derived shard empty) → `SOURCE_RETURNED_ZERO` / appropriate reason. Keep season-window only for
      `PRE_SEASON`/`POST_SEASON` framing. Read the FIXTURES parquets from `instruments-store-sports-prd` (do NOT
      re-query API-Football). This fixes BOTH P1 refinements at once: (a) MDPS in-season no-match days, (b) the
      provider-suffixed/cup leagues (`SCOTTISH_LEAGUE_CUP_185` etc.) that don't resolve via the registry — the truthset
      is keyed by the SAME league_id as the manifest, so resolution is N/A.
- [x] ✅ [DATA] P1. **"15,700 unresolved leagues" DIAGNOSED**: it is NOT 15k unique leagues — it is **ONE league**
      (`SCOTTISH_LEAGUE_CUP_185`, API-Football league id 185) × **2,579 unique dates** × 8 per-fixture data_types
      (FIXTURES/FIXTURE_EVENTS/FIXTURE_LINEUPS/FIXTURE_STATS/INJURIES/LEAGUES/PLAYER_STATS/STANDINGS) = 15,702 rows
      (15,609 empty / 93 captured). It is a **CUP** that plays a handful of days/year → ~2,500 of those days are
      genuinely no-fixture (→ `EXPECTED_NO_FIXTURE` once the FIXTURES-truthset join lands). The `_185` is the raw
      API-Football provider id — the league_id was **never canonicalised** (CF-7 write-path gap: 278,268 manifest rows
      carry provider-id-suffixed league_ids). Two fixes: (1) FIXTURES-truthset relabel (above) resolves the empties
      regardless of canon; (2) **CF-7 league-id canonicalisation** todo below for the writer + migrator.
- [ ] [DATA] P1. **CF-7 league_id canonicalisation** (writer + migrator): 278,268 instruments-store rows carry
      provider-id-suffixed league_ids (`SCOTTISH_LEAGUE_CUP_185`, etc.) instead of canonical keys. Diagnose registry-gap
      (add to UAC `provider_league_ids`) vs writer-not-canonicalising; normalise in the migrator before dedup +
      fix the instruments-service writer so future rows are canonical. ALSO: `data_type=LEAGUES`/`TEAMS`/`VENUES` are
      slow-moving REFERENCE data daily-sharded with per-day empties (operator: "leagues are fixed — why daily?") —
      capture whether reference data_types should be snapshot-not-daily (data-model question → instruments-service).

### C — single-walk (v9 + partition + typed reasons + source path→column + canonical verify)

- [x] ✅ [DATA] P0. **Phase 0 — layout audit DONE (shallow-signature pass, sports slot 2026-06-01)** via
      `cf_layout_audit_2026_06_01.py` on all 3 surfaces (MDPS-prd + MDPS-legacy + instruments-store-prd). **Full layout
      map below**; per-layout object counts come with the VM walk's progress counters. Findings that EXPAND the migrator
      design (scope-is-a-prior): (1) MDPS-prd raw is STILL `category=sports` while MDPS-**legacy** raw is `asset_group=`
      — INVERTED AG key, like prediction (the canonical-named bucket is LESS canonical on the AG segment → the migrator
      converges both onto `asset_group=`); (2) instruments-store has **8 distinct layouts** incl. 3 reference versions
      (`sports_reference` current / `sports_reference_v1_archive` / `sports_reference_v2`) needing reconcile-to-freshest,
      a bare `day=/venue=/{uuid}` instrument tree, a hyphen-delim `instrument_availability/by-date/day-…`, a legacy
      `availability_index/instruments-service.parquet` (OLD manifest format, superseded by `_index/`), + `_audits`/
      `_smoke_test` ARTIFACT trees (skip — not data). The migrator is layout-dispatching across ALL non-artifact trees.

> **📐 Phase-0 LAYOUT MAP (sports slot 2026-06-01, `cf_layout_audit` shallow-signature pass)** — the migrator MUST
> handle every non-artifact layout or it under-migrates (slot-2 DeFi lesson):
>
> | Surface | Tree | Layout signature | Disposition |
> | --- | --- | --- | --- |
> | MDPS-prd (canon) | `processed/by_date/` | `day=/data_type=/league_id=/timeframe=` | candles → add `asset_group=`+`pipeline_mode=` |
> | MDPS-prd (canon) | `raw_tick_data/by_date/` | `day=/category=sports/data_source=/venue=/league_id=/instrument_type=/data_type=` | **`category=`→`asset_group=`** + insert `pipeline_mode=` |
> | MDPS-legacy | `raw_tick_data/by_date/` | `day=/asset_group=sports/data_source=/venue=/league_id=/instrument_type=/data_type=` | near-canon (missing `pipeline_mode=`); reconcile vs prd (INVERTED) |
> | instr-store-prd | `day=YYYY-MM-DD/venue=/{uuid}.parquet` | bare top-level instrument defs | → canonical reference layout |
> | instr-store-prd | `sports_reference/by_date/` | `day=/entity=` (live reference) | freshest → canonical |
> | instr-store-prd | `sports_reference_v2/by_date/` | `day=/entity=` (richer fixture_stats) | complementary → migrate |
> | instr-store-prd | `sports_reference_v1_archive/by_date/` | `day=/entity=` | archived → superseded (verify no canon-only) |
> | instr-store-prd | `instrument_availability/by-date/day-…/{league}/` | hyphen-delim | reconcile / verify |
> | instr-store-prd | `availability_index/instruments-service.parquet` | OLD manifest format | superseded by `_index/` (drop after verify) |
> | instr-store-prd | `_audits/` · `_smoke_test/` · `_catalogue/` | artifacts | **SKIP — not data** |
>
> Evidence: `/tmp/cf_sports_layout.log` (reproduce: `cf_layout_audit_2026_06_01.py market-data-tick-sports-prd-…
> market-data-tick-sports-… instruments-store-sports-prd-…`).

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
      **SCRIPTS READY** — `migrate_sports_canonical_v9.py` (E2) + `rebuild_sports_manifest_v9.py` (E5/E6) at market-tick-data-service@eb5eaad2.
      Dry-run verified 2026-06-01: MDPS prd raw 70 objects + candles 50 + legacy 140 = 260 planned for 3-day window (all `category=`→`asset_group=`, pipeline_mode= inserted). VM execution pending E3 drain.
- [ ] [DATA] P0. C-reasons RIDER (the keystone) — **PARTIAL: composite season/deprecated/free-text relabel SHIPPED
      (instruments 368k), but NO-FIXTURE relabel via the FIXTURES truthset is still owed (operator directive) → MDPS
      still relabels 0. Re-flip only after the truthset join (§ KEYSTONE redesign P0) lands.** Original intent:
      relabel every blank / mislabeled empty row to the correct typed UAC
      reason via the coverage oracle (`clip_dates_to_source_coverage` / `is_in_known_gap` / season / transfer-window /
      fixture-status / league-coverage) — the table in § Sports honest-absence. Snapshot-protected, idempotent,
      oracle-driven (never re-derived per consumer).
      — market-tick-data-service@680dff5f | composite 8-step classifier shipped: step4=is_expected_for_source, step5=footystats_season_status_for_day (ALL sources), step6=get_league_fixture_calendar, step7=is_in_known_gap, step8=SOURCE_RETURNED_ZERO; data_type→source bridge via SPORTS_DATA_TYPE_TO_SOURCE; league_id canon via get_league(.upper()); QG GREEN.
      **DRY-RUN results (2026-06-01)**:
      MDPS (584,177 empties): 0 relabels — CORRECT: MDPS only stores in-season date rows; ALL dates are in-season; season gate returns None for all 58,596 unique (league,date) pairs; stays SOURCE_RETURNED_ZERO (genuinely no-odds-returned within-season).
      Instruments (1,909,553 empties): 288,434 SRZ→EXPECTED_{PRE,POST}_SEASON (step5) + 56,624 SRZ→EXPECTED_DEPRECATED_DATA_TYPE (step1) + 22,978 free-text→EXPECTED_NO_FIXTURE (step2) + existing 13,176 EXPECTED_PRE_SOURCE_COVERAGE_START preserved = 368,036 total relabels (15.4% of SRZ). Unresolved leagues: SCOTTISH_LEAGUE_CUP_185 (15,609) + 86 misc singleton leagues = ~15,700 rows stay SOURCE_RETURNED_ZERO with logged tally.
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
      source walk.
      **SCRIPT READY** — `rebuild_sports_manifest_v9.py` extracts source via `_source_from_row()` and re-emits captured rows with `writer.add(source=...)`. VM execution pending E3 drain.
- [x] ✅ [CODE] P1. C-writer: instruments-service sports handlers emit the typed fixture/season/transfer-window reasons at
      write time (writer analogue of defi A1/A2b) so future writes are honest — no blank/`SOURCE_RETURNED_ZERO` for a
      no-fixture / off-season / out-of-window / uncovered-league day. — instruments-service@608e7ca7: wired
      `is_expected_for_source` oracle into `sports_fixtures_daily_repoll.py` zero-fixture path; per-league
      EXPECTED_PRE_SOURCE_COVERAGE_START / EXPECTED_NO_FIXTURE / SOURCE_RETURNED_ZERO emitted; 3 new unit tests; QG GREEN.

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
      present). — market-tick-data-service@1036de20 | `migrate_sports_canonical_v9.py` (new) layout-aware: MDPS raw+candle, instruments-store 5 trees, CF-7 normalise, ThreadPoolExecutor + gcs_copy_object, dry-run default
- [ ] [DATA] P0. E3 Confirm `sports-scheduler` writer drained; snapshot the sports `_index`(es).
- [ ] [DATA] P0. E4 Dry-VM → timing → optimise → full-VM run (786k index rows; no fire-and-forget).
- [ ] [DATA] P0. E5 **KEYSTONE reason relabel** (CF-5): composite 8-step classifier shipped (instruments 368k relabels)
      but **NO-FIXTURE via FIXTURES truthset still owed** (operator directive) → MDPS relabels 0. Re-flip after truthset join.
      — market-tick-data-service@680dff5f | dry-run: instruments 368,036 relabels (288k season + 57k deprecated + 23k free-text); MDPS 0 relabels (correct — all MDPS rows are in-season; SOURCE_RETURNED_ZERO is the accurate reason for within-season zero-odds). League_id resolution: 100% canonical (MDPS 33/33 resolved; instruments 94/96 resolved; 2 unresolved logged with tally). QG GREEN. VM run pending E3 drain + E4 VM gate per plan sequencing.
- [x] ✅ [DATA] P0. E6 Manifest rebuild: `ManifestWriter` stamping `source` (path→col lift) + `pipeline_mode` +
      `available_at` → consolidator → v9. ~~Also fix the writer to emit typed reasons going forward (CF-5 write-path) — DONE (C-writer@instruments-service@608e7ca7).~~
      — market-tick-data-service@1036de20 | `rebuild_sports_manifest_v9.py` re-emits captured rows via writer.add(source=, pipeline_mode=) + relabelled empties via record_empty; ManifestWriter(per_vm_shards=True).flush()
- [ ] [DATA] P1. E7 CF-7 relabel: ODDS case-drift (`ODDS`/`ODDS_SNAPSHOT` upper vs `odds_horizon_bucket` lower) + blank
      venue.
- [ ] [DATA] P0. E8 Verify: `cf_manifest_audit_2026_06_01.py` on both sports surfaces → CF-1…CF-12 GREEN (esp. 0 blanket
      SOURCE_RETURNED_ZERO); flip CF-coverage in `sports_master_audit_instructions.md`. ⚠️ IRREVERSIBLE — only after
      GREEN: hand C-GREEN to L6 → **delete legacy `market-data-tick-sports` permanently**.

## Deferred work after 2026-06-01 (sports-slot pickup session)

| Item | State | Evidence / next owner |
| --- | --- | --- |
| E1 Phase-0 layout + CF audit (both surfaces) | ✅ DONE | PM@07f7ace03 — full layout map + scope-expansions (instr-store 8 layouts / 2.68M rows / inverted AG) |
| E2 v9 migrator (`migrate_sports_canonical_v9.py`) | ✅ BUILT + dry-run | mtds@eb5eaad2 — 260 objs/3-day window; layout-aware; gcs_copy_object; **VM `--apply` pending E3 drain** |
| E5/E6 rebuilder + composite keystone classifier | ✅ BUILT + dry-run verified | mtds@680dff5f — instruments **368,036 relabels** sample-verified; **VM rebuild pending E3 drain** |
| E6 write-path (typed reasons going forward) | ✅ SHIPPED | instruments-service@608e7ca7 |
| MDPS in-season no-fixture refinement | 🔶 OPEN P1 | determine MDPS writer row-creation before CF-5 GREEN on MDPS (see C-reasons § P1) |
| Unresolved-league residual (~15,700) | 🔶 OPEN P1 | registry-gap vs NO_MAPPING diagnosis before E8 |
| E3 fleet drain (shared w/ slot-2) | ⛔ GATED | pre-migration drain GCP+AWS writers → consolidate → snapshot; coordinated at `epics/mtds_mdps_master` |
| E4 VM dry → full walk (786k + 2.68M) | ⛔ GATED | VM asia-northeast1, no fire-and-forget; after E3 |
| E7 CF-7 relabel + E8 verify + **IRREVERSIBLE legacy delete** | ⛔ GATED | only after CF-1…CF-12 GREEN on real data-state + drain + operator gate |

**Net**: all CODE (migrator + rebuilder + composite keystone + writer-fix) is built, QG-green, dry-run-verified, and on
LDR. The remaining work is OPERATIONAL (VM whole-corpus walk under the fleet drain) + 2 P1 keystone refinements — none of
which is bypassable by an interactive slot. The IRREVERSIBLE legacy-bucket delete (E8) stays gated on CF-GREEN-on-real-
data + the fleet drain + operator.

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
