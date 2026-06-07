---
title:
  "Sports manifest + data canonicalisation (v9 + pipeline_mode partition + fixture-dependent typed reasons single-walk)
  — slot-4 MASTER orchestrator for the ENTIRE sports vertical (IS + MTDS + MDPS + features + execution + UI/bucket)"
created: 2026-06-01
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
master:
  SELF — this plan is the slot-4 MASTER orchestrator for the sports vertical
  (defi_manifest_canonicalisation_2026_06_01.md remains the workspace-wide canonical-SSOT coordinator the sports walk
  conforms to)
role: sports-vertical master orchestrator (slot 4)
orchestrates:
  - sports_retired_data_types_code_cleanup_2026_05_13.md
  - epics/sports_master.md
  - "sports slices of: mdps_backfill_phase3 · mtds_backfill_phase3 · instruments_backfill_phase3 ·
    features_backfill_phase3 · data_source_provenance_all_asset_groups_2026_06_01 ·
    bucket_name_ssot_legacy_dual_write_remediation_2026_06_01"
---

# Sports manifest + data canonicalisation — slot-4 MASTER orchestrator for the sports vertical

> **⛔ COORDINATED + APPLY-GATED (2026-06-07)** — cross-AG sequencing is owned by
> `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md`. This AG's `--apply` (manifest +
> data/schema) is GATED on the coordinator's **G0** (pipeline*mode source-aware
> `{mode}*{source}[_{transport}]`model + doc coherence — this plan PREDATES the 2026-06-05 standard, reconcile per M-COORD-1/2) + **G1** (IS catalogue could-exist SSOT: IS/fixtures backfill complete + accurate UAC; sports`instruments-store-sports`2.68M-row surface rides G1) + **G2** (scripts + 7+2-point audit + dry-run) + **G3** (deployment UNION view) all GREEN. The migrator/manifest-rebuild/enumerator MUST stamp source-aware pipeline_mode (NOT coarse`batch`/blank)
> BEFORE apply. Readiness audit adds ⑧ (IS/fixtures-catalogue) + ⑨ (pipeline_mode source-aware).

> **🔴 P0 GATE (operator 2026-06-05) — the v9 `--apply` here is BLOCKED until
> `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` Phase 0 (code) is GREEN.** Single-walk
> discipline: this corpus walk must carry the new manifest columns — `live_<source>`/`replay_<source>` form, populated
> `source`, `cadence`, `transport` — so running `--apply` before that code lands bakes in the old model + forces a
> banned second whole-corpus walk. **Dry-runs are NOT gated; only the irreversible `--apply`.** (Sports note:
> FIELD_UNION multi-source is unaffected by the reconciliation precedence, but cadence (`scheduled_recurring` for
> fixtures) + the column-mirror still apply.)

> **🔴 FOUNDATION GATE (2026-06-04) — the proper instrument catalogue (incl. sports FIXTURES) blocks the sports MTDS
> `--apply`.** Before the sports MarketTick-data migration `--apply` runs,
> `plans/active/proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` (P0, vm-cross-cutting) must be GREEN — the
> could-exist-universe SSOT (`expected_unattempted` / coverage denominators), built by rolling up the per-date
> definitions. Sports fixtures are first-class in that plan (same instruments-service, same `by_date/` shape).
> **Dry-runs (migrator + manifest-rebuild) are NOT gated** — only the irreversible `--apply`. Depends on
> `instruments_manifest_canonicalisation`. Cross-ref: defi master coordinator §MASTER.

> ## 🎬 SLOT PICKUP PROMPT (clean handoff — paste verbatim into the slot-4 sports lane; 2026-06-01, slot pinned 2026-06-03)
>
> You are **slot 4 — the dedicated sports slot**, and this plan is your **MASTER orchestrator plan for the ENTIRE sports
> vertical** (operator 2026-06-03, clean asset-group split). Your lane is **everything sports across every service** —
> IS (`instruments-store-sports` reference) + MTDS (`market-data-tick-sports`) + MDPS + features + execution + the
> sports deployment-UI/menu/bucket/data/manifest surfaces. **All of it, end to end.** prediction / cefi / tradfi are
> **slot 3** (incl. the non-sports parts of instruments + downstream); defi is **slot 2**. Do not touch them.
>
> **As master orchestrator you also OWN the sports cross-references**: every other sports plan/issue and every orphaned
> sports cross-reference attaches here (see § "Orchestrated sports sub-plans & cross-references" below) — when you find
> a dangling sports item in another plan, pull it in or cross-link it to this master rather than leaving it orphaned.
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

## Orchestrated sports sub-plans & cross-references (master role — slot 4)

As of 2026-06-03 this plan is the **MASTER orchestrator for the whole sports vertical** (operator: "slot 4 has
everything sports — IS, MTDS, MDPS, features, all downstream, all bucket/data/manifest/UI — with the canonicalisation
manifest plan as the master orchestrator for all those other plans and issues"). Slot 4 drives, sequences, and keeps
green the following — **and any orphaned sports cross-reference found in another plan is pulled in / cross-linked here,
not left dangling**:

| Sub-plan / surface                                              | Sports scope it carries                                                                   | Relationship                      |
| --------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------- |
| `epics/sports_master.md`                                        | 25,652 `MISSING_EXPECTED` odds-cell coverage backfill (bookmaker coverage)                | orchestrated (coverage, not FORM) |
| `sports_retired_data_types_code_cleanup_2026_05_13.md`          | `TRANSFERMARKT_LEAGUES` / `SFI_LEAGUES` retirement (88,779 rows → `EXPECTED_DEPRECATED…`) | orchestrated                      |
| `mtds_backfill_phase3` / `mdps_backfill_phase3`                 | sports MTDS/MDPS odds-tick rows + the MDPS sports routing/output-bucket tests             | sports slice rides slot 4         |
| `instruments_backfill_phase3`                                   | `instruments-store-sports` reference (fixtures + 20 ref data_types, 2.68M rows)           | sports slice rides slot 4         |
| `features_backfill_phase3` / features-service sports            | sports features rows + sports `_index`                                                    | sports slice rides slot 4         |
| `data_source_provenance_all_asset_groups_2026_06_01.md` Phase 4 | sports `source` path→column backfill                                                      | RIDER of this single walk         |
| `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`  | sports bucket-name SSOT + decommission of every other sports bucket                       | orchestrated (bucket surface)     |

"Orchestrated" = slot 4 owns sequencing + green-ness + cross-link, even where the body executes in the sub-plan. The
single canonical walk below executes the FORM/honest-absence/RIDER work inline; coverage backfill + retired-type cleanup
execute in their own plans but report up to this master.

## Scope boundary — what this master coordinates vs executes inline (no double-execution)

These ride **separate sub-plans** (executed there, tracked here — see the orchestration table above); this plan does NOT
re-execute their bodies inline:

- **The 25,652 `MISSING_EXPECTED` odds cells** (BET365/BETFAIR/DRAFTKINGS/FANDUEL/ODDS_API/PINNACLE × odds_snapshot +
  odds_movement, absorbed 2026-05-20) — coverage backfill in **`epics/sports_master.md`** (not canonicalisation). This
  plan canonicalises the FORM + relabels honest-absence; it does NOT backfill missing bookmaker coverage.
- **Retired-data-type cleanup** (`TRANSFERMARKT_LEAGUES` / `SFI_LEAGUES`, 88,779 rows → `EXPECTED_DEPRECATED_DATA_TYPE`)
  — `sports_retired_data_types_code_cleanup_2026_05_13.md`.
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

> **✅ REAL-GCS DRY-RUN VERIFIED — closes the "VM-pending / no GCS access locally" caveats on the items below (slot-6
> 2026-06-04, ADC on `central-element-323112`).** All scans dry (`copied=0`, no writes), run serially (GCS
> connection-pool saturation lesson). **① Migrator (`migrate_sports_canonical_v9.py --surface {mdps,instruments}`):**
> mdps TOTAL **planned=617,271** (prd raw 231,533 + processed 109,312 + legacy raw 276,426); instruments TOTAL
> **planned=753,402**. 0 net errors. **② Rebuild
> (`rebuild_sports_manifest_v9.py --surface {mdps,instruments} --dry-run`):** mdps → **584,177 empty_confirmed + 202,067
> captured + 164 existing attempted_failed** (CF-11 step 6.7: **0** match-day-empties upgraded on mdps; 100% league_id
> resolution). instruments → **1,909,553 empty_confirmed (151,786 → attempted_failed via CF-11) + 586,597 captured +
> 178,025 existing attempted_failed**; 8-step oracle {relabel_no_fixture_truthset 1,002,757 · relabel 231,810 ·
> mark_attempted_failed 151,786 · keep_src_zero 424,014 · relabel_retired 56,624 · relabel_free_text 22,978 · keep_typed
> 19,584}; **15,694 unresolved league_ids (0.8%) stay SOURCE_RETURNED_ZERO** (top SCOTTISH_LEAGUE_CUP_185 15,609). The
> per-item "VM dry-run needed for real counts" caveats below are now SATISFIED.

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

- [x] ✅ [CODE] P0. **Read/write path canonicalisation sweep (sports — all repos)**: confirm EVERY sports bucket lookup
      routes through `resolve_bucket_name(…, asset_group="sports", env=…)` → `-prd-` canonical. —
      unified-trading-library@b3b70c13 + e2e-testing@b418afc | sports_fixtures.py keystone truthset reader +
      instruments_preflight/**init**.py docstring + e2e scripts → canonical resolve_bucket_name / prd hardcode.
      Regression gate: tests/unit/test_sports_fixtures_bucket.py asserts -prd- form, no-env form fails QG. **CROSS-AG
      items NOT touched (need coordination):** - **UTL `instrument_lifecycle_loader.py:46,54`**
      `"sports":"instruments-store-sports-{pid}"` (shared cross-AG map cefi/defi/tradfi/sports/prediction — do NOT fix
      from sports lane, workspace-wide coordination gate). - **UAC FACADE ROOT — `sports.gcs_paths.bucket_name(...)`
      returns the NO-ENV form** (`market-data-tick-sports-{PID}` / `instruments-store-sports-{PID}`), pinned by
      `unified-api-contracts/tests/unit/test_gcs_paths_facade.py:30,49,50,72`. CROSS-AG (UTL `resolve_bucket_name` SSOT
      → `-prd-`; UAC `bucket_name` facade → no-env) — coordinate at `defi_manifest…` §MASTER; sports READERS already
      fixed to use `resolve_bucket_name` instead of the facade.
- [x] ✅ [CODE] P0. **deployment-api data-status = ALREADY CANONICAL (sports slot verified 2026-06-02)**: the
      data-status bucket resolution `build_bucket_name()` (`data_status_drilldown.py:103-115`) + `batch_config_utils.py`
      route through `resolve_bucket_name(cloud="gcp", kind=…, asset_group=…)` → canonical env-tiered `-prd-` (via
      `SERVICE_TO_KIND` + cloud-providers.yaml). `data_status_hierarchical.py:364` calls the same `build_bucket_name`.
      The `data_status_mock.py` SPORTS entry (`features-sports-service`) is a service→AG map, NOT a bucket → no
      dead-bucket exposure. **No fix needed in deployment-api.** ONE UI mirror —
      `unified-trading-system-ui/context/api-contracts/canonical-schemas/     domain/sports/mapping_resolver.py:40`
      ("Resolve the instruments-store-sports bucket name") — mirrors the UAC gcs_paths facade → **rides the cross-AG UAC
      `bucket_name` facade fix** (coordinate at `defi_manifest…` §MASTER; not a unilateral sports-lane change). UI
      data-status views read the (canonical) deployment-api → no separate UI fix.
- [x] ✅ [CODE] P0. **Tests-feeding-QG use canonical buckets/paths (sports)** — VERIFIED ALREADY SATISFIED 2026-06-03.
      Comprehensive grep of every features-service test (unit + integration) for legacy sports bucket/path literals
      (`instruments-store-sports-central` / `market-data-tick-sports-central` / `category=sports` / no-env
      `gs://…sports` forms) returned **zero hits** — the sports tests already route through
      `resolve_bucket(kind=…, asset_group="sports")` / the canonical `-prd-` form, and
      `tests/sports/unit/test_gcs_paths_and_reader_deps.py` IS the self-enforcing regression guard (its only "legacy
      form" mentions are docstrings describing what it guards against). No change needed; the mechanism is in place.
- [x] ✅ [DATA] P0. **League rewrite table — ENUMERATED ON REAL DATA (sports-slot 2026-06-02; no dry-run needed — read
      the prod `_index` + UAC registry directly)**. The "278k suffixed rows" is **mostly LEGIT tier leagues**
      (`LIGUE_1`, `LIGUE_2`, `BUNDESLIGA_2`, `K_LEAGUE_1/2`, `LIGA_3`, `GREEK_SUPER_LEAGUE_2`, `LIGA_PORTUGAL_2` — full
      form resolves → correct, leave). Of 52 suffixed unique league*ids, the actual rewrite need is TINY: - **SAFE
      (3-digit season-id suffix, base resolves)**: `SCOTTISH_LEAGUE_CUP_185`→`SCOTTISH_LEAGUE_CUP` (15,702 rows). Rule =
      strip trailing
      `*<digits>`iff base resolves AND digits ≥ 100 (3-digit AF/season id, never a 1–2-digit       tier). → **extend`canonicalize*league_id`with this rule** (safe; handles all 3-digit-suffix registered leagues).     - **AMBIGUOUS — operator/registry decision**:`LA_LIGA_2`(3,465 rows) is likely **Segunda División** (real tier-2,       AF id 141), NOT a La-Liga season suffix → must map to the canonical Segunda key, NOT strip to LA_LIGA.      `FRANCE_NATIONAL_1` (2 rows) same shape. Do NOT auto-rewrite these — verify the canonical tier key.     - **REGISTRY-GAP (base doesn't resolve)**: 41 obscure leagues, **47 rows total** (`CONGO_DR_LIGUE_1`,       `BRAZIL_CARIOCA_1`, `DENMARK_DENMARK_SERIES_GROUP*\*`…) — negligible volume; add to UAC`provider_league_ids`
      OR leave (47 rows). Not a migration blocker. Net: CF-7 league-canon is essentially DONE; only the
      SCOTTISH_LEAGUE_CUP_185 3-digit rule + the LA_LIGA_2 tier disambiguation remain (both doable pre-migration;
      LA_LIGA_2 needs the canonical-Segunda-key confirmation). — uac@dc76f1a6 |
      SCOTTISH_LEAGUE_CUP_185→SCOTTISH_LEAGUE_CUP via Step 3a (num>=100 rule); LA_LIGA_2/BUNDESLIGA_2/LIGUE_1 unchanged
      (already canonical at step 2); 13 tests green.
- [x] ✅ [DATA] P1. **LA_LIGA_2 → SEGUNDA_DIVISION RESOLVED (registry investigation 2026-06-02)**: `LA_LIGA_2` (3,465
      rows) IS Segunda División; the **canonical registered key is `SEGUNDA_DIVISION`** (has the `LeagueDefinition` in
      `league_data.py` + provider maps understat `f5e5596b0efdef8e` / footystats `ES2` / season `15066` + team-count
      seed 22). `LA_LIGA_2` is an INCONSISTENT alias in some `provider_league_ids.py` reverse maps with NO
      `LeagueDefinition` (`get_league("LA_LIGA_2")`→None). FIX (UAC): add explicit alias `LA_LIGA_2`→`SEGUNDA_DIVISION`
      in `canonicalize_league_id` + correct the reverse maps emitting `LA_LIGA_2` to emit `SEGUNDA_DIVISION`
      (born-canon). `FRANCE_NATIONAL_1` (2 rows): `FRANCE_NATIONAL` unregistered → registry-gap, negligible. —
      unified-api-contracts@40c92900 | \_LEAGUE_ALIASES map + 15 FOOTYSTATS_HISTORICAL_SEASON_IDS entries corrected +
      tests updated; QG green

> ## OPERATOR DIRECTIVE 2026-06-02 (round 2) — PERFECT, PRE-MIGRATION, NO DEFERRALS
>
> "Do them ALL pre-migration, I want it perfect." Scope additions (all P0, all before the migration runs):

- [x] ✅ [CODE] P0. **Cross-AG bucket canonicalisation — DO IT NOW (not defer to master)**: make UAC
      `gcs_paths.bucket_name(asset_group,…)` return the **canonical env-tiered `-prd-`** form (route through / match
      `resolve_bucket_name`) for ALL AGs; fix UTL `instrument_lifecycle_loader._BUCKETS`/`_INSTRUMENTS_STORE_BUCKETS` +
      `instruments_preflight/__init__.py:23` to call `resolve_bucket_name` (NOT hardcode — operator pointed at the
      hardcoded line); update the pinning tests (`test_gcs_paths_facade.py` etc.) to assert canonical. Touches all lanes
      — coordinate via the master callout but EXECUTE (operator is the cross-lane authority). QG all affected repos. —
      uac@dc76f1a6 + utl@fd91ee74 | UAC canonical/gcs_paths.py + sports/domain/gcs_paths.py templates now emit
      -prd-{project_id} (env param, default prd). UTL instrument_lifecycle_loader replaces hardcoded dicts with
      \_resolve_instruments_store_bucket() -> resolve_bucket_name(). instruments_preflight docstring updated.
      Pre-existing QG failures in test_cassette_orphan_checker.py (5 tests, not caused by this change — unrelated
      cassette scanner).
- [x] ✅ [CODE] P0. **Ban `category=` EVERYWHERE — v9 canonical only, no fallback** — deployment-api@41fa120 | QG 3847
      passed (1 pre-existing fail unrelated). Fixed: trading_axis.py (removed category fallback from mapping reads),
      shard_management.py (3 sites), data_status_drilldown.py (GCS path building now asset_group=), mock_data.py
      (asset_group key). Added test_no_category_asset_group_fallback.py QG ratchet. storage_facade.list_objects
      transparently fans out to legacy category= paths for on-disk GCS reads (correct — no data loss). OTHER repos
      (MTDS, instruments-service, features-service) still have category= usages — captured as todos below; NOT touched
      (separate agent context). UI repos clean (no category= as asset-group key).
- [x] ✅ [CODE] P1. **MTDS: ban `category=` in production source — replace with `asset_group=`**: grep-report 2026-06-02
      found `category=` in MTDS scripts (not production service source — most are in migration/reconcile scripts reading
      legacy paths, which is correct). Production source to audit:
      `market_tick_data_service/engine/orchestrator.py:1791` passes `category=cat` to `get_expected_bookmakers()` —
      check if this kwarg name is a column key or just a function parameter; if column key, rename. Migration scripts
      (`restructure_tradfi_files.py`, `rebuild_mtds_manifest.py`, `migrate_to_per_instrument.py`,
      `migrate_cefi_instrument_types.py`) use `category=` to build legacy GCS paths for migration — these are
      intentional (reading legacy paths) and should stay as-is OR add comment
      `# QG-allow: reading legacy category= paths`. `smoke_matrix.py:206` probes both `asset_group=` and `category=` —
      leave as-is (dual-probe is correct for transition). Repo: `market-tick-data-service`. QG that repo after any
      source change. — DIAGNOSIS (2026-06-02): `orchestrator.py:1791` `category=cat` is a `BookmakerCategory` function
      param (not a GCS path key) — LEFT AS-IS. Migration scripts confirmed transition-necessary legacy reads → added
      `# QG-allow: reading legacy category= paths` comments to all 4 scripts. `smoke_matrix.py:206` dual-probe is
      correct. QG exit 0. — market-tick-data-service@0e9ad63f
- [x] ✅ [CODE] P1. **instruments-service: ban `category=` in production source — replace with `asset_group=`**:
      grep-report 2026-06-02 found `category=` in IS orchestrator at multiple sites (e.g. lines 2304, 2402, 3194, 3208,
      4041, 4109, etc. in `instruments_service/engine/orchestrator.py`) — these pass `category="sports"` /
      `category="prediction"` as kwargs, likely to UTL `record_captured` / `record_empty`. If those are UTL kwargs that
      accept `asset_group` instead, rename them. If they are legacy param names that UTL still reads as `category`, this
      is a UTL contract issue — file a UTL upgrade todo. Script `aggregate_legacy_es_opt_trades.py:229` passes
      `category="tradfi"` — check kwarg name. Repo: `instruments-service`. QG that repo after any source change. —
      **DIAGNOSIS COMPLETE (2026-06-02)**: ALL IS `category=` in IS orchestrator + sports_fixtures_daily_repoll.py are
      kwargs to UTL `record_captured(category: str, ...)` — the UTL parameter is literally named `category` (maps
      internally to `asset_group` at UTL manifest_writer.py:1800/2451/2794). Renaming IS callers requires a coordinated
      UTL contract upgrade. Filed as UTL-contract todo below. `base_adapter.py:185` is `ErrorCategory` enum (different
      axis — not an asset-group column). `sports_fixtures_daily_repoll.py:43` is a docstring. No IS renames needed; UTL
      must rename its `category` param to `asset_group` — see UTL-contract upgrade todo. — instruments-service@8958a2ae
- [x] ✅ [CODE] P1. **UTL contract upgrade: rename `record_captured(category=…)` param to `asset_group=` — HARD ATOMIC
      CUT, ZERO ALIAS (operator directive 2026-06-02, dispatched to a dedicated session)**:
      `unified_trading_library/manifest_writer.py:2629` declares `category: str`; internally maps to `asset_group`
      (1800/2451/2794). Operator: do it NOW workspace-wide, **no lingering deprecated alias** — the shipped end-state
      has NO `category` kwarg in any ManifestWriter signature; a missed caller must FAIL LOUD (TypeError), never
      silently forward. Approach = ONE coordinated sweep: (1) UTL adds `asset_group=` + transiently accepts both; (2)
      update EVERY caller across ALL repos (instruments-service ~18 sites + sports*fixtures_daily_repoll, MTDS,
      features, strategy, execution, alerting, deployment-api, e2e, migration scripts) `category=`→`asset_group=`; (3)
      UTL commit that REMOVES `category` — lands in the SAME sweep so zero alias ships. NEW QG ratchet fails on any
      `category=` at a ManifestWriter call site. Leave unrelated `ErrorCategory`/`market_category`/`BookmakerCategory`.
      Provenance: instruments-service@8958a2ae diagnosis. ✅ DONE 2026-06-02 (dedicated session) — shipped
      workspace-wide, ZERO alias. UTL@9db7fd69 (rename + tests, no `category` kwarg in any ManifestWriter signature).
      Callers `asset_group=`: instruments-service@3ade065b (20 sites incl orchestrator x17 + repoll + 2 scripts),
      MTDS@d0dad2da (3), MDPS@b67afaa (2), execution-service@0eb6b945a (2), strategy-service@882da071 (1). 91 sites
      total (28 callers + 63 UTL tests). features/alerting/deployment-api/e2e: **0** ManifestWriter `category=`
      callsites per workspace-wide AST audit — no change needed (the repo list was speculative). QG ratchet **STEP
      5.92** `check_no_category_kwarg_at_manifest_write.py` (PM@60a27debe) bans any regression; the existing
      tradfi-source ratchet was updated to read `asset_group=` (else the rename would silently disable it).
      Event-payload observability dict keys kept as `category` for dashboard stability (write \_param* only).
- [ ] [CODE] P1. **features-service: ban `category=defi` in on-disk GCS path reads**: **GATED ON DEFI MIGRATION —
      VERIFIED STILL-REQUIRED 2026-06-04 (slot-4)**, NOT sports. Corrected file paths (files live in the `onchain/`
      subtree, not `delta_one/app/*`): `features_service/onchain/adapters/mtds_canonical_reader.py` (`_legacy_twin()` at
      L71-72 + the candidate builder L82-123) explicitly builds the legacy `category=defi/` twin alongside the canonical
      `asset_group=defi/` for backward-compatible reads of un-migrated on-disk data;
      `features_service/onchain/app/calculators/eigen_rewards_calculator.py:53-54` lists both the canonical
      `asset_group=defi/` and legacy `category=defi/` suffixes. `ErrorCategory.*` (e.g. eigen L205) is the unrelated
      error-classification enum — leave alone. **STAYS GATED**: `defi_manifest_canonicalisation_2026_06_01.md` still has
      40 open todos incl. `[DATA] P0 C0 path+bucket canonicalisation (the foundational migration) — RUN ON A VM` (the
      defi C0 walk has NOT run → legacy `category=defi/` parquets are still on disk → removing the twin now would break
      defi reads). Removal is a clean one-shot once defi C0 reaches C-GREEN. **DEFERRED** — named successor:
      `defi_manifest_canonicalisation_2026_06_01.md` § C0/C-GREEN; not a sports-track blocker.
- [x] ✅ [CODE] P0. **Upstream pre-flight data-check audit + batch=live symmetry (ALL sports services)** — AUDIT
      COMPLETE 2026-06-02. Per-service table below; gaps captured as P1/P2 todos beneath. Every service either VERIFIED
      GREEN or has a tracked gap-todo. Evidence: this slot, reading code in-repo (grep-then-read across 5 services).

  **Per-service audit table (2026-06-02)**

  | Service                         | SSOT bucket (-prd-)?                                                                                                                                                                                                                                                                                                                                       | v9 cols checked?                                                                                | 0vol/NaN/empty-shard detect?                                                                                                                                                                | manifest marks incomplete-expected?                                                                                                                                                            | batch=live symmetric?                                                                                                                                                                            | live circuit-breaker?                                                                                                                                                                   |
  | ------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | instruments-service             | ❌ GAP — `sports_dependency.py:66` calls `get_write_bucket_name("instruments","SPORTS",project)` with explicit project_id → skips yaml SSOT → returns legacy `instruments-store-sports-{pid}` (no -prd-); IS orchestrator itself writes to `-prd-` via `resolve_bucket_name`                                                                               | ❌ NO — blob existence only, no column/schema checks                                            | ✅ YES — raises `DependencyError` on missing api-football fixtures blob                                                                                                                     | ✅ YES — `record_failed` on partial/full fetch fail (CF-11 fix @ceab7720); `record_empty(EXPECTED_*)` via oracle (@608e7ca7)                                                                   | ✅ YES — same `sports_dependency.check_api_football_dependency()` + `classify_venue_error()` path in both modes                                                                                  | ❌ NO live circuit-breaker beyond DependencyError (post-May-23 scope per preflight.py comment)                                                                                          |
  | market-tick-data-service (MTDS) | ✅ OK — `get_bucket_name("instruments","sports")` with no explicit project_id → yaml SSOT → `-prd-` form; catalog reader correct                                                                                                                                                                                                                           | ❌ NO — no v9 column checks on sports manifest reads at preflight                               | ✅ YES — `failed_shards` dict + sentinel pass → `record_failed`; `OddsApiAdapter` CF-11 fix (@c96245b7) re-raises on API errors                                                             | ✅ YES — sentinel pass emits typed honest absence; fixture-existence gated                                                                                                                     | ✅ PARTIAL — detection logic same; action diverges (live → ADAPTER_FETCH_FAILED + `record_failed`; batch → same). No separate live-only code path                                                | ❌ NO explicit sports live circuit-breaker; relies on `failed_shards` sentinel only                                                                                                     |
  | features-service                | ❌ GAP — `gcs_paths.resolve_instruments_bucket()` calls `get_bucket_name("instruments","sports",project_id=_project_id())` with explicit project_id → skips yaml SSOT → returns `instruments-store-sports-{pid}` (legacy no-env); `resolve_tick_data_bucket()` uses unmapped domain `"market-data-tick-sports"` → also falls through to legacy no-env form | ❌ NO — no v9 column checks; reads parquet and returns empty DataFrame silently on missing blob | ❌ PARTIAL — `gcs_reader.read_reference_entity()` returns `pd.DataFrame()` silently on missing blob; logs WARNING but does NOT raise `DependencyError` or emit `record_empty/record_failed` | ❌ NO — features-service sports does NOT write manifest rows (no `ManifestWriter` usage in `features_service/sports/`); upstream emptiness is silently propagated as an empty output DataFrame | ❌ PARTIAL — `gcs_reader.py` behaviour is batch-only; live runner is `AssetScopedFeaturesRunner` (UTL); no sports-specific NaN/0-volume detection or degraded-propagation in sports compute path | ❌ NO live circuit-breaker wired for sports                                                                                                                                             |
  | strategy-service                | ❌ GAP — `DependencyChecker.UPSTREAM_DEPS` bucket_template `"instruments-store-{asset_group_lower}-{project_id}"` with explicit project_id in `BaseDependencyChecker` → legacy no-env form for sports; NOT via `resolve_bucket_name`                                                                                                                       | ❌ NO — existence-only check via `BaseDependencyChecker`; no v9 column/schema validation        | ✅ YES — raises `DependencyError` + emits `emit_preflight_skip` when required deps missing                                                                                                  | ✅ PARTIAL — `DependencyError` raised stops the run (doesn't emit manifest rows; strategy-service is not a manifest writer for sports)                                                         | ✅ YES — same `_check_dependencies()` called in both batch and live path                                                                                                                         | ✅ YES — `VenueCircuitBreaker` in `preflight.py` (trip after 3 failures / 5-min window / 15-min cooldown; logs `VENUE_CIRCUIT_TRIPPED`). Post-May-23 PubSub alerting hook noted in code |
  | execution-service               | N/A — no sports source code in `execution_service/` source; sports execution only in `tests/sports_execution/` test fixtures                                                                                                                                                                                                                               | N/A                                                                                             | N/A                                                                                                                                                                                         | N/A                                                                                                                                                                                            | N/A                                                                                                                                                                                              | N/A — sports P&L execution is via CeFi perp; no sports-upstream data preflight in service                                                                                               |

- [x] [CODE] P1. **IS `sports_dependency.py` — fix bucket to canonical -prd- form**: `_resolve_sports_bucket()` at
      `instruments_service/reference_data/sports_dependency.py:66` passes explicit `project_id` to
      `get_write_bucket_name` → skips yaml SSOT → returns legacy `instruments-store-sports-{pid}`. After the migration,
      IS orchestrator writes to `-prd-` but this preflight reads from the wrong (deleted) bucket. Fix: replace with
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")` (same call as the orchestrator
      at line 7365). Repo: `instruments-service`. QG that repo. — instruments-service@fd7b72a7 | resolve_bucket_name
      SSOT route + tests updated; QG 3047/3047 new tests pass (2 pre-existing fails unrelated)
- [x] ✅ [CODE] P1. **features-service sports `gcs_paths.py` — fix both bucket resolvers to canonical form**:
      `resolve_instruments_bucket()` passes `project_id=_project_id()` → skips yaml SSOT → returns
      `instruments-store-sports-{pid}` (legacy). `resolve_tick_data_bucket()` uses unmapped domain
      `"market-data-tick-sports"` → legacy. Fix both: (a) `resolve_instruments_bucket()` → call
      `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")` (no explicit project_id); (b)
      `resolve_tick_data_bucket()` → call `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="sports")`
      (the yaml-mapped domain). File: `features-service/features_service/sports/data/gcs_paths.py`. QG features-service.
      — features-service@e0ddde68 | both resolvers now call resolve_bucket() from features_service.common; 4 unit tests
      verify env-tiered (-prd-/-test-) form; QG ALL GATES PASSED
- [x] ✅ [CODE] P1. **strategy-service `DependencyChecker` — fix bucket_template to canonical form for sports**:
      `UPSTREAM_DEPS["instruments-service"]["bucket_template"]` = `"instruments-store-{asset_group_lower}-{project_id}"`
      with explicit project_id substitution → legacy no-env. Fix: remove explicit project_id from template + route
      through `resolve_bucket_name` inside `BaseDependencyChecker.check_dependencies` (or override in the
      sports-specific check path). Also affects `features-delta-one-service` template. Repo: `strategy-service` (+ UTL
      `BaseDependencyChecker` if template substitution is there). QG strategy-service. — strategy-service@ecc7cc0f | all
      3 upstream deps (ml-predictions-store, features-delta-one, instruments-store) now routed via resolve_bucket_name;
      affects all AGs (expected); QG exit 0
- [x] ✅ [CODE] P2. **features-service sports — add `DependencyError` raise on missing fixtures blob**:
      `gcs_reader.read_reference_entity()` at `features_service/sports/data/gcs_reader.py:170-178` returns
      `pd.DataFrame()` silently when the upstream instruments-store blob is missing. For the `"fixtures"` entity
      specifically (not slow-moving fallback entities), a missing blob for a requested date WITHIN UAC coverage bounds
      indicates a real upstream gap — should raise `DependencyError` (or at minimum emit a structured preflight-skip
      event) rather than silently returning empty. Batch=live symmetry: the live path should additionally trigger the
      sports circuit-breaker. Repo: `features-service`. — features-service@e0ddde68 | DependencyError raised for
      fixtures date>=2018-01-01 (api_football coverage start); re-raised before generic except-Exception; 4 unit tests:
      within-coverage raises, pre-coverage returns empty, non-required entity returns empty, blob-present returns data;
      QG ALL GATES PASSED
- [x] ✅ [CODE] P2. **features-service sports — wire `assert_consolidator_healthy` for live mode** — DONE 2026-06-03
      (features-service@this-branch). `features_service/sports/live/runner.py` `build_runner` now runs
      `_assert_upstream_manifest_healthy(asset_group)` before building — gates **BOTH** sports upstreams (`market-data`
      tick = MDPS odds/candles AND `instruments-store` = IS fixtures; sports has two upstreams vs delta_one's one),
      raising `ManifestConsolidatorStaleError` to fail-to-start. Regression test
      `tests/common/test_live_runner.py::test_sports_wrapper_build_runner_gates_on_consolidator` (monkeypatches the
      gate, asserts both sports-scoped buckets fire). **Caught a latent bug**: the delta_one pattern I mirrored used the
      INVALID `kind="market-data-tick"` (raises `BucketNamingError` — valid kind is `"market-data"`); see next item.
- [x] ✅ [CODE] P1. **Cross-family latent bug — `resolve_bucket_name(kind="market-data-tick")` is INVALID, raises
      `BucketNamingError`** (found 2026-06-03 via the sports consolidator-gate test). The canonical tick-bucket kind is
      `"market-data"` (yaml-keyed; aliased `"tick-data"`), used by 10+ consumers (sports/onchain/volatility/delta_one
      config). Three live-mode call sites used the invalid string — would crash at runtime, **untested** (no test mocked
      the kind) — FIXED features-service@this-branch: `delta_one/cli/handlers/live_handler.py:41` (candle-freshness
      gate), `cefi/cli/handlers/perp_funding_handler.py:83` + `cefi/calculators/perp_funding_rates.py:72` (perp-funding
      preflight). Data-correctness fix per the heartbeat rule; provenance: slot-4 sports e2e session.
- [x] ✅ [CODE] P2. **IS + MTDS sports — add v9 schema column checks to upstream preflight** — BOTH DONE 2026-06-02: IS:
      `sports_dependency.py` has `check_sports_manifest_v9_columns(manifest_df)` (SPORTS_V9_ENFORCED field in
      `InstrumentsServiceConfig`). MTDS: `_check_sports_v9_columns()` helper + `SPORTS_V9_ENFORCED` field in
      `MarketTickDataServiceConfig`; called from `process_ticks()` after the try/except block (so RuntimeError
      propagates in enforcement mode). Auto-detect uses `_SPORTS_V9_NEW_COLS` (asset_group/source/available_at, NOT
      pipeline_mode which was already in v8) to avoid false-positives on pre-migration fixtures. 5 unit tests
      (non-enforced warn+pass, enforced-via-flag raises, enforced-via-autodetect raises, all-cols-present silent,
      empty-index noop). QG exit 0 (all 2434 tests pass). — instruments-service@8958a2ae |
      market-tick-data-service@40c1be5a

### PRE-DRY-RUN CODE MILESTONE (sports-slot 2026-06-02) — all doable-before-dry-run code SHIPPED + QG-swept

> Operator directive "do all the code to the dry-run, then QG sweep (time-consuming)". The QG sweep ran **per-repo in
> parallel** across every touched repo (each sub-agent ran its repo's `quality-gates.sh` → exit 0, only unrelated
> pre-existing failures). **Pre-dry-run code is COMPLETE.** Shipped this cycle:
>
> | Area                                                                                                                                                            | Repos@sha                                         |
> | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
> | Keystone composite classifier + FIXTURES-truthset + CF-11 match-day→attempted_failed + re-emit attempted_failed                                                 | mtds@680dff5f, 699c58e9, 8ffb2acd                 |
> | CF-11 write-path (IS partial-fail-mask bug FIXED + MTDS ingest discovery-mask FIXED)                                                                            | is@ceab7720, mtds@c96245b7                        |
> | Legacy-instruments reconcile migrator + schema spot-check                                                                                                       | mtds@50a43aa7                                     |
> | CF-7 league canon (UAC fn + 3-digit season-rule) + wired migrator/rebuilder/IS-writer                                                                           | uac@409753bd+dc76f1a6, mtds@df391e7c, is@db187587 |
> | Cross-AG bucket canonicalisation: UAC `bucket_name` facade → `-prd-`; UTL maps/preflight + sports_fixtures keystone reader → `resolve_bucket_name`; e2e scripts | uac@dc76f1a6, utl@b3b70c13+fd91ee74, e2e@b418afc  |
> | Pre-flight dead-bucket fixes (IS/features/strategy passed explicit project_id → legacy) → `resolve_bucket_name`                                                 | is@fd7b72a7, features@e0ddde68, strategy@ecc7cc0f |
> | features-service silent-empty → `DependencyError` (batch=live symmetry)                                                                                         | features@e0ddde68                                 |
> | `category=` ban in deployment-api data-status + QG ratchet                                                                                                      | deployment-api@41fa120                            |
>
> **Correctly NOT done pre-dry-run (sequencing, not skipped)**: (a) `category=` READER fan-outs / migration-script
> legacy reads in MTDS/IS/features — the migration MUST read `category=` paths to move that data; removing pre-migration
> breaks the walk → POST-migration cleanup. (b) v9 schema-column checks at preflight — would fail on v8 data NOW →
> POST-walk regression guard. (c) `LA_LIGA_2` Segunda-vs-season disambiguation — operator/registry decision (3,465
> rows). (d) IS orchestrator `category=` kwargs — per-site UTL-contract check (P1). All tracked above; none block the
> dry-run.

### Post-migration LIVE-WRITER + downstream-reader readiness gaps (slot-4 cross-service audit 2026-06-03)

> **Why this section exists.** The migration (C-walk + `migrate_sports_canonical_v9.py`) canonicalises the EXISTING
> sports corpus to v9. But the **live writers + downstream readers** that produce/consume NEW data going forward (MTDS /
> MDPS / features / strategy) must ALSO emit/probe the canonical v9 form — else after the migration runs, new writes
> DIVERGE from migrated data and consumers miss it. A 5-service read-only audit (2026-06-03, dimensions: pre-flight /
> missing-partial-reasons / read-write paths) found the writers were only **HALF-migrated**: `category=`→ `asset_group=`
> was done, but the **`pipeline_mode=` path segment and the `source=` column were never added**, and several output
> buckets are still hardcoded legacy f-strings. **Ground truth (resolved a doc contradiction):** `pipeline_mode` IS
> canonical for sports — the sports SSOT `candidate_parquet_paths()`
> (`unified_api_contracts/canonical/domain/sports/gcs_paths.py:153`) emits the `pipeline_mode=`-aware path as its
> Level-1 probe, and `migrate_sports_canonical_v9.py` produces `pipeline_mode=batch_odds_api/asset_group=sports/…`
> (2026-06-03 dry-run confirmed). The CLAUDE.md "sports uses `candidate_parquet_paths()` (unaffected)" note means
> "sports has its OWN path helper, not the generic raw_tick prober" — NOT "sports has no pipeline_mode".
> **execution-service is effectively N/A** (event-driven venue-API order placement, no GCS sports reads) — 2 minor
> non-blocking items noted at the end.

**P0 — hard breaks (new writes diverge from migrated data, or land in dead buckets):**

- [x] ✅ [CODE] P0. **DONE mtds@4fbc0730 — sports raw-tick write path now carries `pipeline_mode=` (verified vs
      migration `_canon_mdps_raw_prd` SSOT + path-shape/source= tests; on LDR).** Original gap: MISSING `pipeline_mode=`
      — repo: `market-tick-data-service`, `market_tick_data_service/engine/orchestrator.py:2740-2758` (the inline sports
      odds path builder). It writes `day={D}/asset_group=sports/data_source={SRC}/venue=…` with NO `pipeline_mode=`
      segment, while the non-sports builder `_build_partition_path_for_asset_group` (orchestrator.py:980-994) inserts
      `pipeline_mode={pm}/` via `derive_pipeline_mode_for_row(venue, ag, data_type)`. Post-migration, migrated data
      lives at `pipeline_mode=batch_odds_api/asset_group=sports/…` but new live writes land at `asset_group=sports/…` →
      divergent paths. **Fix**: insert `pipeline_mode={derive_pipeline_mode_for_row(...)}/` after `day={D}/` in BOTH the
      per-fixture and league-aggregate branches; add a path-shape unit test asserting the segment is present.
- [x] ✅ [CODE] P0. **DONE mdps@3dd3f15 — sports processed writer (`scripts/reprocess_sports_odds.py`, the actual sports
      candle writer) now embeds `pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/` (verified vs
      migration `_canon_mdps_candle` SSOT + path-shape test; on tab).** Original gap: MISSING
      `pipeline_mode=`/`asset_group=` hive keys — repo: `market-data-processing-service`, `…/config.py:131`
      (`get_processed_path`) + `…/output_path_helpers.py:53-75` (`build_processed_candle_path`). The blob key is
      `processed_candles/by_date/day=/timeframe=/data_type=/venue=/…` — no `pipeline_mode=batch_*/` (the
      `partition_path` passed to UTL validation has `asset_group=` but the actual GCS blob key does not). Post-migration
      v9 readers won't find new sports processed candles. **Fix**: embed `pipeline_mode={pm}/asset_group=sports/` in the
      processed blob prefix (align with the migration target + `candidate_parquet_paths`); path-shape test.
- [x] ✅ [CODE] P0. **DONE mtds@4fbc0730 + mdps@3dd3f15 — sports captured rows now stamp `source=` (MTDS: `odds_api` via
      source-map; MDPS: `mdps_odds_horizon_bucket` via `_resolve_primary_source_for_candle`, None-fallback for unwired
      AGs preserves cefi/defi/tradfi behaviour). Tests assert source= on captured rows.** Original gap: OMIT `source=` —
      repos: `market-tick-data-service` (`engine/orchestrator.py:3084-3121`, `record_captured_from_counts`/`add()` for
      sports) + `market-data-processing-service` (`…/canonical_writer.py:1426`, `record_captured`). v9 requires `source`
      on every captured cell (operator 2026-06-01, crosscutting — cefi/defi/sports are RED per CLAUDE.md). Without it
      sports rows lack the column the v9 walk adds → `MissingSourceError` / null-source breaks
      `select_primary_available_source`. **Fix**: pass `source=get_primary_source("sports", data_type)` (e.g.
      `odds_api`) to `record_captured`/`add`/`record_empty` for sports shards in both services. (Composes with
      `data_source_provenance_all_asset_groups_2026_06_01.md` §Phase 1 — this is the sports write-path slice that plan
      left RED.)
- [x] ✅ [CODE] P0. **DONE features-service@78a9a26f — all 3 sports output call sites now use
      `resolve_bucket(kind="features-sports", asset_group="sports")` (env-tiered `-prd-` form) + 3 tests. (Also
      unblocked 2 foreign QG gates: a 51L method from 933b8747 + a uv.lock desync.)** Original gap: bucket f-string
      drops env-tier — repo: `features-service`, `features_service/sports/cli/handlers/batch_handler.py:722` +
      `…/cli/handlers/live_handler.py:108` + `…/app/pubsub/subscriber.py:65`:
      `bucket or f"features-sports-{project_id}"` produces `features-sports-central-element-323112` but the canonical
      bucket is `features-sports-prd-central-element-323112` (`cloud-providers.yaml`). Post-migration the non-env-tiered
      bucket does not exist → **all sports feature writes hard-fail**. **Fix**: replace all 3 with
      `resolve_bucket(kind="features-sports", asset_group="sports")` (the migration script
      `features_sports_reconcile_available_at.py:261` already uses the correct form).
- [x] ✅ [CODE] P0. **DONE strategy-service@7025bedc + deployment-service@5ad0951 — `VenueBalanceTracker` now resolves
      via `resolve_bucket_name` (allocation → flat `strategy-store`, shared by all non-prediction AGs; positions → new
      `position-store-sports` kind registered in cloud-providers.yaml GCP+AWS) + regression test.** Original gap:
      hardcoded legacy no-env buckets — repo: `strategy-service`,
      `strategy_service/position/core/venue_balance_tracker.py:57-58`: `f"strategy-store-sports-{project_id}"` +
      `f"position-store-sports-{project_id}"`. Used by `load_allocation()` (:414), `save_eod_snapshot()` (:478),
      `load_snapshot()` (:508) → **404 post-migration**. **Fix**: resolve via
      `resolve_bucket_name(cloud=…, kind="strategy-store"/"position-store", asset_group="sports")` (register the kinds
      in `cloud-providers.yaml` if absent — verify first). Same anti-pattern as the `ecc7cc0f` DependencyChecker fix.

- [x] ✅ [CODE] P0. **DONE features-service@fd1a2b17 (probing mechanism) + @7baba0d4 (per-entity value via UAC SSOT).
      Sports reads now probe the migration's `pipeline_mode=` path + legacy fallback: raw odds → explicit
      `pipeline_mode=batch_odds_api/asset_group=sports/` candidate; sports_reference →
      `candidate_parquet_paths(pipeline_mode=pipeline_mode_for_sports_entity(entity))` (per-entity). Read tests assert
      canonical + legacy hits.** Original gap: **READ paths don't probe the migration's `pipeline_mode=` path (the
      writers were fixed, the readers were NOT)** — repo: `features-service`. The sports READERS hand-construct exact
      paths and `blob_exists`-probe them, bypassing the `pipeline_mode`-aware UAC SSOT `candidate_parquet_paths`:
      `sports/data/gcs_reader.py::read_odds_data` (~:326) probes `raw_tick_data/by_date/day={D}/asset_group=sports/…`
      then `…/category=sports/…` — **neither has `pipeline_mode=`**; the `sports_reference` entity reads
      (`_singleton_path`/`_league_prefix` ~:99-128) similarly build `sports_reference/by_date/day={D}/entity=…` with no
      `pipeline_mode=`. After the migration writes `pipeline_mode=batch_odds_api/asset_group=sports/…` (and
      `sports_reference/by_date/day=/pipeline_mode=/entity=…`), these readers look for the NON-pipeline_mode path →
      **MISS all migrated data** (silent empty reads → false honest-absence). **No sports reader calls
      `candidate_parquet_paths`** (the SSOT that emits the Level-1 `pipeline_mode`-aware probe + Level-2 legacy
      fallback). **DISCOVERED 2026-06-03 (the prior 5-service audit wrongly concluded "pipeline_mode N/A for sports
      reads").** (MDPS `orchestration_scanner._list_instrument_files` is OK — it
      `list_blobs(prefix="raw_tick_data/by_date/day={D}/")`, which is `pipeline_mode`-agnostic, so it finds migrated
      data.) **Fix**: route the features sports readers through
      `candidate_parquet_paths(data_type, day, league_id,     pipeline_mode=…)` (it already returns the migration's path
      as Level-1 + legacy as fallback), OR add the `pipeline_mode=`-prefixed candidates to the `blob_exists` lists. Add
      a read-path test asserting the reader finds a `pipeline_mode=batch_odds_api/asset_group=sports/…` object. **Pairs
      with the P0 writer fixes — writes + reads MUST use the identical migration path.**
- [x] ✅ [CODE] P0. **DONE instruments-service@4459799d — IS sports_reference object path now carries `pipeline_mode=`
      (source-derived, == manifest) + `source=` on captured rows; reads probe canonical-first + legacy fallback;
      `path==manifest` invariant test.** (`pipeline_mode` value-consistency across migration+reader finalized by the
      keystone UAC-SSOT P0 below.) Original gap: **instruments-service WRITER (the 6th service — NOT in the original
      5-service audit) object path is MISSING `pipeline_mode=` + omits `source=`** — repo: `instruments-service`,
      `instruments_service/engine/orchestrator.py`. The IS writer of the `instruments-store-sports` `sports_reference`
      surface stamps `pipeline_mode=` on the MANIFEST row (`record_captured_from_counts(pipeline_mode=…)` ~:1589/1771,
      `_pipeline_mode_for_sports_data_type`) BUT writes the OBJECT to
      `sports_reference/by_date/day={D}/entity={E}/league={L}/…` (~:3664/3711/3774/3838/3921) with **NO `pipeline_mode=`
      in the object path** → path≠manifest invariant violated; and `record_captured_from_counts` does **not** pass
      `source=`. The migration `_canon_instr_reference` (`migrate_sports_canonical_v9.py`) writes the canonical target
      `sports_reference/by_date/day={D}/pipeline_mode={PM}/entity={E}/…` (PM derived from entity via
      `_pipeline_mode_for_source`) — so post-migration the IS writer's new objects DIVERGE from the migrated layout, and
      the candidate_parquet_paths SSOT probes the `pipeline_mode=` path. **DISCOVERED 2026-06-03** (instruments-service
      was the upstream writer overlooked by the MTDS/MDPS/features/strategy/execution audit). **Fix**: (a) insert
      `pipeline_mode={_pipeline_mode_for_sports_data_type(entity)}/` after `day={D}/` in EVERY IS sports_reference
      object write path (match `_canon_instr_reference` exactly); (b) pass `source=` to
      `record_captured_from_counts`/`add` for sports cells (derive the same way the migration's `_source_from_row` does
      — entity→source). (Typed empty reasons already DONE — is@608e7ca7. Consolidator preflight is N/A — IS is the
      pipeline SOURCE, no upstream manifest to gate.) Add a path-shape + source= test. **The IS reads must also probe
      the `pipeline_mode=` sports_reference path — verify under the read-path P0 above (IS is both writer and reader of
      its reference surface).**
- [x] ✅ [CODE] P0. **RESOLVED 2026-06-03 — ONE UAC SSOT `pipeline_mode_for_sports_entity` (uac@a16c0808, 16 entities,
      unknown→batch_instruments_service) now used by ALL FOUR: migration `_canon_instr_reference` (mtds@6ee55b40), IS
      writer (is@855e4172, replaced its local map), features reader (features@7baba0d4, replaced fixed value), and the
      IS/rebuild manifest path. VERIFIED end-to-end:
      `pipeline_mode_for_sports_entity(entity) == _canon_instr_reference path PM` for
      fixtures(batch_api_football)/understat_xg(batch_understat)/player_values(batch_transfermarkt)/footystats_predictions(batch_footystats)/venues(batch_instruments_service)
      — all OK. Migration object-path == manifest == writer == reader. 7+6+2 tests across the repos.** Original gap:
      **CRITICAL — the `pipeline_mode` value for instruments-store `sports_reference` is DERIVED 3 DIFFERENT WAYS that
      DISAGREE (path ≠ manifest ≠ reader); needs ONE shared UAC SSOT.** Repos: `unified-api-contracts` (new SSOT) +
      `market-tick-data-service` (migration) + `instruments-service` (writer) + `features-service` (reader). DISCOVERED
      2026-06-03. The entity folders on disk are **data-type-named** (`entity=fixtures`, `fixture_events`, `teams`,
      `xg`…), NOT provider-named. The three derivations:
  - **Migration object-path** `migrate_sports_canonical_v9.py::_canon_instr_reference` maps `entity` through an
    `entity_to_source` dict that ONLY contains provider names (`api_football`/`footystats`/…) → data-type entities miss
    → **falls back to `batch_instruments_service`**. WRONG.
  - **Migration manifest-rebuild** `rebuild_sports_manifest_v9.py` (:740/:865) stamps
    `pipeline_mode_for_source(_source_from_row(row))` → source-derived → **`batch_api_football`** for fixtures. So the
    migration's OWN object-path ≠ its OWN manifest (path≠manifest violation IN the migration).
  - **IS writer** `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` (orchestrator.py:158) →
    `FIXTURES/FIXTURE_EVENTS/TEAMS → BATCH_API_FOOTBALL`, `XG → BATCH_UNDERSTAT`, `PLAYER_VALUES → BATCH_TRANSFERMARKT`
    … (manifest = `batch_api_football`).
  - **features reader** (`gcs_reader.py` `_SPORTS_REF_PIPELINE_MODE`, fd1a2b17) uses a FIXED `batch_instruments_service`
    → matches the BUGGY migration object-path, NOT the manifest/writer → would MISS the correctly-migrated data.
    **CANONICAL DECISION (slot-4, justified by the manifest-rebuild + IS-writer agreement + the "path==manifest"
    invariant): `pipeline_mode` is SOURCE-derived per data_type/entity** (`fixtures→batch_api_football`,
    `xg→batch_understat`, …), NOT the generic `batch_instruments_service`. **Fix (coordinated, ONE SSOT)**: (1) UAC —
    add `pipeline_mode_for_sports_entity(entity)` / `…_data_type(data_type)` = the SSOT (lift
    `_SPORTS_DATA_TYPE_TO_PIPELINE_MODE` into UAC). (2) migration `_canon_instr_reference` → use it
    (entity→data_type→pipeline_mode), so object-path == manifest. (3) IS writer object-path → use it (== its manifest
    row). (4) features reader → probe with the per-entity value from it (replace the fixed `batch_instruments_service`).
    Re-run the instruments dry-run to confirm the NEW path shape. **This is the keystone of "everything the same in
    reality" for the instruments surface — until it's fixed, the migration mislocates every instruments object's
    pipeline_mode and the reader can't find the correctly-stamped ones.**
- [x] ✅ [DATA/CODE] P1. **CONFIRMED 2026-06-03 (mtds@3f45d38d, mdps@43cabc2) — no column drift.** Both the live writer
      (`writer.add(source=, pipeline_mode=)` / `record_empty(reason=, pipeline_mode=)`) and the migration rebuild
      (`rebuild_sports_manifest_v9._rebuild_manifest`, same kwargs) go through the SAME UTL `ManifestWriter`, so the v9
      column set + dtypes match structurally; verified the live writer passes the same kwargs the rebuild does.
      Regression tests added. Original: **Schema/column PARITY pass — verify the v9 manifest column set + dtypes are
      IDENTICAL across writer ⇄ migration ⇄ reader** (operator: "same columns, no schema types, everything the same").
      Writers now stamp `source`+`pipeline_mode` (P0.3) and MTDS `_check_sports_v9_columns` enforces the new-col set at
      preflight, but no end-to-end check confirms EVERY v9 column (`schema_version=9`, `asset_group`, `source`,
      `pipeline_mode`, `available_at`, `capture_status`, typed `error_reason`) is present AND the same dtype in: the
      live writer's `record_captured`/`add`, the migration's `rebuild_sports_manifest_v9` emission, and the downstream
      data-status/feature readers. **Fix**: write a parity assertion (or extend `cf_manifest_audit`) comparing the
      column schema of a live-written sports `_index` row vs a migration-rebuilt row vs the reader's expected schema;
      reconcile any drift.
- [x] ✅ [DATA/CODE] P1. **CONFIRMED 2026-06-03 (mtds@3f45d38d, mdps@43cabc2) — per-shard emission correct, no blanket
      collapse.** MTDS builds `captured_sports_shards` from `shard_counts` (only actually-captured
      `(bookmaker,league,fixture)`), the sentinel loop skips captured shards → captured shards `add()`, uncaptured →
      `record_empty`/`record_failed`. MDPS `reprocess_sports_odds` emits a fine-grain `add()` per `(league,horizon)`
      shard. Regression tests added (partial day: league A captured + league B off-season-empty → TWO rows, A captured /
      B empty_confirmed-typed). Original: **Partial-capture manifest correctness for sports — confirm** (operator:
      "handling partial data correctly"). MTDS handles partial at write (per-shard captured-set, partial venues not
      skipped) + MDPS/features track calculator partial status, but no explicit confirmation that a day where SOME
      leagues/venues captured and OTHERS legitimately empty produces the CORRECT per-shard manifest rows (captured rows
      for the present shards + typed-empty rows for the absent-but-expected, NOT a single blanket cell). **Fix**: a
      partial-day test (e.g. EPL captured + off-season league empty on the same day) asserting per-shard rows are
      emitted with the right capture_status/reason per shard (4-pillar cluster-coverage validation).

**P1 — correctness/safety (silently compute/trade on stale or mislabelled data):**

- [x] ✅ [CODE] P1. **DONE 2026-06-03 — consolidator pre-flight added: MTDS@a75f021a (`process_ticks` after the v9-col
      check), MDPS@fc64192 (`dependency_checker`), features-service@4b628d1a (batch_handler via new shared
      `_manifest_preflight`, mirroring the live runner); loud-fails `ManifestConsolidatorStaleError`, gated by
      `not force`.** Original gap: No `assert_consolidator_healthy` pre-flight in MTDS / MDPS / features-BATCH — repos:
      `market-tick-data-service` (`engine/orchestrator.py` `process_ticks()` before `read_availability_index`),
      `market-data-processing-service` (`…/orchestration_service.py` startup / `_check_dependencies`),
      `features-service` (`features_service/sports/cli/handlers/batch_handler.py` `BatchHandler.run()` — the **live**
      runner gate shipped 2026-06-03 features-service@ae75b44b but batch has none). **Fix**: add the shared UTL gate
      before each upstream manifest read (template: features `sports/live/runner.py:_assert_upstream_manifest_healthy`);
      loud-fail (`ManifestConsolidatorStaleError`) on a stale/missing index when per-VM shards exist.
- [x] ✅ [CODE] P1. **DONE 2026-06-03 — live writers now emit TYPED `EmptyConfirmedReason` via the SAME UAC
      `is_expected_for_source` (+ `footystats_season_status_for_day`) SSOT that `rebuild_sports_manifest_v9.py`'s CF-5
      classifier uses — NO parallel taxonomy. MTDS@a75f021a (oracle steps 4+5 in the sentinel path), MDPS@fc64192
      (`classify_sports_empty_reason`); `SOURCE_RETURNED_ZERO` only when a fixture WAS expected but source returned
      zero; CF-11 attempted_failed split intact.** Original gap: Blanket `SOURCE_RETURNED_ZERO` instead of TYPED
      fixture/season reasons (going-forward writers) — repos: `market-data-processing-service` (`…/batch_workers.py:178`
      `_handle_empty_tick_data`, default `canonical_writer.py:1668`) + `market-tick-data-service`
      (`engine/orchestrator.py:3586,3635` per-fixture sentinels). The migration RELABELS the existing corpus (keystone
      classifier, SHIPPED), but the LIVE writers still emit blanket `SOURCE_RETURNED_ZERO` for no-fixture/off-season
      days → re-introduces the silent-lie the walk fixes. **Fix**: at empty-write time, look up the sports fixture
      calendar (`get_league_fixture_calendar` / FIXTURES truth set) and emit the typed `EmptyConfirmedReason`
      (`EXPECTED_NO_FIXTURE` / `EXPECTED_PAUSED_LEAGUE` / coverage/transfer-window/genesis) — the write-path twin of the
      migration's CF-5 classifier.
- [x] ✅ [CODE] P1. **DONE strategy-service@c2793217 — (8a)
      `check_allocation_manifest(date, features_bucket,     asset_group="sports")` wired into the sports batch
      allocation loop (`batch_handler._run_handle_prechecks`): skip on `empty_confirmed`/`attempted_failed` (batch), log
      `UPSTREAM_FEATURES_FAILED` on attempted_failed (live). (8b) `SportsFeatureSubscriber` now gates on honest-empty
      (`_is_honest_empty_vector` — returns early, no signal/publish). QG exit 0; 5+9 tests.** ⚠️ **Contract gap (8b)**:
      the FSS Pub/Sub event does NOT carry `capture_status` (it lives in the GCS manifest) — the subscriber uses an
      implied-probability heuristic; the real fix is adding `capture_status` to the UAC `SportsFeatureEvent` contract
      (captured as a follow-up below). Original gap: allocation-guard orphaned for sports + PubSub subscriber has no
      capture_status gate.

**Follow-ups surfaced by the P1 work (2026-06-03):**

- [x] ✅ [CODE] P2. **DONE 2026-06-03 — `capture_status` now carried on the FSS→strategy sports PubSub payload.** Wire
      trace: that path is raw PubSub JSON (a dict), NOT the Redis-cascade `FeaturesComputedEvent` — so `capture_status`
      was added as a **sports-payload key** (UAC `SPORTS_FEATURE_PAYLOAD_CAPTURE_STATUS_KEY` +
      `SportsFeatureCaptureStatus` Literal in `canonical/domain/sports/live.py`, uac@ec947a7e+b24baa7d), NOT on the
      generic cross-AG event (avoids all-families blast radius — correct scoping). features-service@e2249fd9 stamps it
      on every emitted record (`subscriber._classify_record_capture_status`); strategy-service@fb3f8f7f reads it first
      and gates on `empty_confirmed`/`attempted_failed`, keeping `_is_honest_empty_vector` as a pre-rollout fallback
      only. 3 (UAC) + 9 (features) + 12 (strategy) tests. Original gap: allocation-guard's subscriber had no real
      capture_status signal.
- [x] ✅ [CODE] P3. **DONE features-service@e2249fd9** — `sports/live/runner.py` now imports + re-exports
      `assert_upstream_manifest_healthy` from the shared `sports/cli/handlers/_manifest_preflight.py`; the duplicate
      `_assert_upstream_manifest_healthy` deleted (ONE gate impl). `test_live_runner.py` monkeypatch retargeted to
      `_manifest_preflight.assert_consolidator_healthy`. No behaviour change.

**Non-blocking / N/A (documented for completeness, no migration break):**

- [x] ✅ [CODE] P3. **execution-service minor manifest hygiene — DONE 2026-06-04 (separate sports-execution-store,
      operator-approved)** — execution-service@1ae2de968 + deployment-service@1a5331f. Both cosmetic items fixed: (1)
      execution-result manifest rows now stamp the real `asset_group` (was `asset_group=""`) — `LiveCloudStorageSink`
      carries `asset_group`, `record_captured(asset_group=self.asset_group)` (`engine/modes/live/data_sink.py`); (2)
      `get_bucket_for_asset_group()` accepts `sports`/`prediction` (was hard-raise), a typed `asset_group` config field
      (`EXECUTION_ASSET_GROUP`/`VM_ASSET_GROUP`) + `execution_sink_bucket_sports`/`_prediction` fields drive it, and
      `_get_or_create_live_sink()` resolves bucket + asset_group from config (no hardcoded `"cefi"`). Sports execution
      results now route to a dedicated `execution-store-sports-{pid}` bucket — registered in `cloud-providers.yaml`
      execution-store map (GCP+AWS, non-env-split to match the family + the config construction); verified
      `resolve_bucket_name(kind=execution-store, asset_group=sports) -> execution-store-sports-{pid}`. 5 regression
      tests (sink asset_group threading, manifest-row stamp, sports/prediction bucket resolution, invalid-AG still
      raises) — execution-service QG green @c513a6d9. **Promotion note**: both commits landed on LDR via the tab-mirror;
      the staging PR drains via the staging→main automation once `unified-api-contracts` clears the dep-tier gate
      (quickmerge LDR→staging was dep-order-blocked on UAC's unstaged LDR backlog, not on this change).
- [x] ✅ [CODE] P3. **Prediction execution-store config/SSOT mismatch — config side RESOLVED 2026-06-04 (slot-4)** —
      execution-service@419895ed7. Surfaced while wiring the sports execution-store: the execution-service config
      constructed `execution-store-prediction-{pid}` (non-env-split) for prediction, but the canonical SSOT is
      **env-split** — `cloud-providers.yaml:173/327` flat key `execution-store-prediction` →
      `execution-store-pred-${DEPLOYMENT_ENV_SHORT}-${pid}`, AND `terraform/gcp/main.tf:1575` provisions
      `execution-store-prediction-${environment}-${project_id}` (yaml + terraform AGREE on env-split). The config's
      generic non-env construction was the wrong side. **Fix**: `ExecutionServicesConfig.get_bucket_for_asset_group` now
      EXCLUDES prediction (valid-set back to `cefi/tradfi/defi/sports`) and **raises** for it rather than constructing a
      wrong non-env bucket — with an inline note that prediction execution must resolve via
      `resolve_bucket_name(kind='execution-store-prediction')`. Removed the `execution_sink_bucket_prediction` field +
      flipped the unit test to `test_prediction_execution_bucket_raises`. Sports unaffected (config fallback == yaml
      SSOT, both non-env). basedpyright clean. **Residual for slot-3** (below) — wiring prediction execution itself.
- [x] ✅ [CODE] P3. **HANDOFF→PREDICTION: prediction execution-store wired via the canonical env-split bucket — DONE
      (execution-service@d1bd640ab, slot-5 2026-06-05).** `get_bucket_for_asset_group('execution','prediction')` now
      resolves via `resolve_bucket_name(kind='execution-store-prediction')` → `execution-store-pred-${env}-${pid}`
      (env-split), instead of the fail-loud raise — the generic `{prefix}-{group}-{pid}` construction can't produce the
      env tier, so it's resolved via the SSOT (NOT re-added to the generic construction, per the handoff). Other
      prediction bucket_types still raise (only the execution store is env-split-wired). Latent today (no prediction
      execution process running) but ready so a future prediction-execution process is a no-op. Test flipped: prediction
      execution resolves via the SSOT (mocked) + non-execution still raises; basedpyright clean; QG exit 0
      (sentinel==HEAD). parent_epic: mtds_mdps_master.

### Post-migration read-path regressions — slot-4 e2e readiness audit (2026-06-04)

> A fresh 7-dimension e2e readiness audit (slot-4, 2026-06-04, ahead of the real migrate/rebuild apply runs) re-verified
> the whole sports vertical and found the prior "reads fixed" P0 claims (@fd1a2b17/@7baba0d4) were **INCOMPLETE**: three
> sports READERS + one cross-AG startup gate still spoke the pre-migration / wrong canonical path and would regress at
> cutover (the operator's "code must not regress by association with dead buckets" class — these only bite once the
> legacy objects are dropped or on the canonical-only layout, so they pass a dual-layout smoke test today). All four are
> fixed + regression-tested + on LDR. The **migrator dry-run** (MDPS 2-day window 2026-06-04, `copied=0`, 0 errors)
> independently validated the canonical target paths these fixes now probe (raw → `pipeline_mode=batch_odds_api/`;
> candle →
> `pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/.../league_id=/timeframe=/bucketed.parquet`).
> Otherwise the audit confirmed dims ③ (4-state consolidator pre-flight), ④ (typed honest-absence + CF-11 + downstream
> capture_status gating), ⑥ (IS/UAC guardrails + FIXTURES truthset), ⑦ (deployment-api coverage uses the UAC
> fixtures/leagues universe as the denominator, not manifest-rows) all GREEN; the remaining open items are the VM-gated
> E3–E8 operational runs (unchanged).

- [x] ✅ [CODE] P0. **MDPS `reprocess_sports_odds` raw-odds read prefix was `pipeline_mode=batch_api_football` for a
      `data_source=ODDS_API` path** — the MTDS writer + migration `_canon_mdps_raw_prd` emit source-derived
      `batch_odds_api`, so the reader matched neither the migrated NOR (post-`--drop-stale`) any object → silent-empty.
      Fixed → `batch_odds_api`; regression test asserts the constant. — market-data-processing-service@6105699
- [x] ✅ [CODE] P0. **features `read_bucketed_odds` read a single bare
      `processed/.../data_type=odds_horizon_bucket/bucketed.parquet`** — real layout is per-`(league_id,timeframe)`
      shards, migrated under `pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/` → the single-blob read
      missed BOTH the per-shard split AND the migrated path (silent-empty odds features at the live
      `odds_features_exporter` consumer). Fixed to list+concat every `bucketed.parquet` under the canonical prefix then
      legacy fallback; 4 tests. — features-service@88cbb844
- [x] ✅ [CODE] P1. **IS `check_api_football_dependency` exact-probed a bare `entity=fixtures/fixtures.parquet`** — the
      IS writer + migration write FIXTURES per-league under
      `pipeline_mode=batch_api_football/entity=fixtures/league={L}/` → exact probe matched neither the per-league layout
      nor `pipeline_mode` → spurious `DependencyError` post-migration. Fixed to list the canonical pipeline_mode prefix
      then the legacy prefix (any object = fixtures present); 3 tests. — instruments-service@4631b469
- [x] ✅ [CODE] P0. **CROSS-AG — strategy-service GAP-5 live-startup consolidator gate passed
      `kind="market-data-tick"`** (NOT a registered `resolve_bucket_name` kind/alias) → uncaught `BucketNamingError`
      (the `except` caught only `ManifestConsolidatorStaleError`) → crashed the live trade-loop startup for EVERY
      asset_group (cefi/defi/tradfi/sports), regardless of consolidator health. Same class as the features-service
      ae75b44b fix; the prior test mocked `resolve_bucket_name`'s return so never exercised the kind. Fixed →
      `kind="market-data"` + regression test asserting the kind. — strategy-service@85864b22

**Follow-ups (P2/P3 — captured per Capture-Discoveries; NOT migration-blocking):**

- [x] ✅ [CODE] P2. **MDPS sports candle empty-handler `league_id=""` → SRZ — RESOLVED (mdps@dd5def4, 2026-06-05):
      honest-safe, documented (NOT a derivation)** — the sports `instrument_id` at this candle layer is MARKET-specific
      (not league-encoded) + the tick DataFrame is empty, so league_id is genuinely unresolvable here; SRZ is the honest
      fallback (fabricating EXPECTED_NO_FIXTURE without fixture context would be a false claim). Typed path is
      `reprocess_sports_odds`. Comment clarified. ~~repo:~~ `market-data-processing-service`,
      `app/core/batch_workers.py:191-198` `_handle_empty_tick_data`. For a SPORTS empty shard routed through the generic
      tick→candle empty-handler, `classify_sports_empty_reason(league_id="")` short-circuits to SRZ
      (`canonical_writer.py:1717`) so the typed fixture/season oracle never runs. The in-code comment documents this as
      a conservative fallback (this layer carries only `instrument_id`, not `league_id`); sports odds primarily flow
      through `reprocess_sports_odds`/`record_empty_for_shard` (typed-correct), so it is off the primary path. Fix:
      derive `league_id` from `instrument_id` so the oracle runs for any sports shard reaching this handler. Provenance:
      slot-4 e2e audit 2026-06-04 (dim ④).
- [x] ✅ [CODE] P2. **features-service `batch_write.py` no-env default bucket → resolve_bucket — DONE
      (features@8086b5cc, 2026-06-05)** — repo: `features-service`. The 3 primary sports output call sites were fixed to
      `resolve_bucket` (@78a9a26f) but this CLI default fallback still yields the no-env form → 404 post-migration when
      the batch-write CLI is invoked without `--bucket`. Fix:
      `resolve_bucket(kind="features-sports", asset_group="sports")`. Provenance: slot-4 e2e audit 2026-06-04 (dim ⑤/⑥).
- [x] ✅ [DOC] P3. **codex doc drift — `get_league_fixture_calendar` — DONE (PM@d910cabbb, 2026-06-05): corrected to
      "active-season day grid" + denominator note.** ~~is described as "Dates with actual fixtures" in~~
      `codex/02-data/availability-manifest-and-data-status.md` but the impl returns the active-season DAY GRID
      (`league_data.py:356-394`) → the sports coverage DENOMINATOR is marginally generous (safe direction — over-counts
      expected, never hides a gap). Correct the doc wording OR tighten the helper to actual scheduled-fixture days.
      Provenance: slot-4 e2e audit 2026-06-04 (dim ⑦).
- [x] ✅ [TEST] P3. **deployment-api ratchet — sports `_shard_prefix` no-category pin — DONE (deployment-api@9d20681,
      2026-06-05): 2 tests added.** ~~`test_no_category_asset_group_fallback.py` doesn't parametrize the sports~~
      `per_venue_day_bundle` `_shard_prefix` branch\*\* (`data_status_drilldown.py:905-913` — correct by construction,
      no `asset_group=`/`category=` key, but unpinned by the ratchet). Add a sports case. Provenance: slot-4 e2e audit
      2026-06-04 (dim ⑦).

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
  - **SHARDING + PERFORMANCE SCOPING (slot-4 dry-runs 2026-06-03, no `--apply`):** Dry-run (list+plan, no copy) timings:
    **MDPS** 30-day window (2025-09 across prd + legacy-no-env raw + processed trees) = **16,544 objects in 19 s**; data
    is sparse (~7-9 active days/month — sports doesn't write every day). **Instruments** 3-day window = 10,083 planned,
    dominated by the `instrument_availability` tree (**119,858 objects walked**); full surface = **2.68 M rows**.
    Extrapolated object counts: MDPS ≈ **0.9-1.1 M objects** (786 k index rows), instruments-store ≈ **2.5-2.7 M**.
    **Recommended shard axis = `day=`** (the natural partition both `migrate_sports_canonical_v9.py` surfaces already
    iterate; `--start-date/--end-date` shard cleanly with NO overlap). **Recommended fleet**: shard the full range
    (2019→2026) **by year** across ~7-8 in-region (`asia-northeast1`) ephemeral VMs (one year each), `--workers 32-64`
    (`gcs_copy_object` REST ~100 ms, GIL-released → ~640 obj/s at 64w). Est. `--apply` copy time: MDPS ≈ **25-30 min
    single-VM** (≈ **4 min/VM** at 7-way), instruments-store ≈ **70 min single-VM** (≈ **10 min/VM**). Instruments is
    the long pole — shard it **by year × entity-tree** (`sports_reference` vs `instrument_availability`) if finer
    parallelism is needed. **Per-VM shard isolation** (`VM_NAME=` + `MANIFEST_PER_VM_SHARDS=true`) so the manifest
    consolidator merges per-VM shards after. No fire-and-forget (STARTED<60s + hourly progress + STOPPED at exit). The
    dry-run already validates the dest-path transform per object, so E4's "optimise" step is mainly tuning `--workers`
    against the live REST 429-rate. **Gated on E3 drain; the scoping above needs no data download (list+plan only).**
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

## Slot-4 sports 7-criteria completion audit 2026-06-04 (operator-requested; cross-service, 4 read-only agents + verify)

> VERDICT: **all 7 criteria COMPLETE** for the sports asset_group at the CODE level (the full migration WALK stays
> operator-gated). Two agent-flagged "gaps" were verified as grep-then-conclude artifacts (already-wired / N/A).

- [x] ✅ **① Migrator dry-run** — `migrate_sports_canonical_v9.py`: dry-by-default + `--apply`; idempotent
      (`gcs_describe_object` skip); server-side `gcs_copy_object`; path transforms via the UAC `candidate_parquet_paths`
      SSOT; no import-time risk.
- [x] ✅ **② Manifest-rebuild dry-run** — `rebuild_sports_manifest_v9.py`: `--dry-run` (default) previews per-
      `capture_status` counts + the reason-relabel histogram + action distribution, NO `_index` write.
- [x] ✅ **③ 4-state preflight on every service IS→execution (respective sports buckets)** — IS
      (`sports_dependency.py`), MTDS (`market_interface/sports/registry.py`), MDPS (`dependency_checker.py`
      `validate_can_run` — dual `assert_consolidator_healthy` on market-data-tick-sports + instruments-store-sports),
      features (`sports/cli/handlers/_manifest_preflight.py` — same dual gate, live==batch). strategy/execution do NOT
      read sports MARKET-DATA canonically (strategy reads features via strategy-store; execution is event-driven) → the
      consolidator gate is correctly absent there (N/A, not a gap).
- [x] ✅ **④ Empty/partial honest + downstream handles (batch==live)** — API error on an EXISTING fixture →
      `record_failed` (attempted_failed), NOT empty_confirmed; no-fixture / pre-season / off-season → typed
      `EmptyConfirmedReason.EXPECTED_NO_FIXTURE` / `EXPECTED_PRE_SEASON` (IS `orchestrator.py:1628/1903` +
      `sports_fixtures_daily_repoll.py:314` via the fixture oracle — NO blank reasons); manifest 4-state explains every
      zero; batch and live emit identical schema (features `_manifest_preflight.py` is the shared live==batch gate).
- [x] ✅ **⑤ Read/write paths match post-migration everywhere** — migrator, rebuild, live raw-writer, live candle-writer
      (MDPS) and downstream readers (features `sports/data/gcs_reader.py`) all derive pipeline_mode via the UAC
      `pipeline_mode_for_sports_entity` / `pipeline_mode_for_source` SSOT family — NO local-map drift (the sports
      keystone was already unified; the prediction-style drift does not exist in sports). All readers probe via
      `candidate_parquet_paths()`.
- [x] ✅ **⑥ IS + UAC guardrails vs instruments/fixtures that cannot exist** — UAC `clip_dates_to_source_coverage()` +
      `is_in_known_gap()` (`canonical/domain/sports/league_data.py`) DEFINED + USED across IS orchestrator / features
      `honest_coverage_report.py` / MTDS rebuild / deployment-api; the per-league preflight derives the EXPECTED league
      universe from UAC `get_expected_leagues_for_source()` (NOT hardcoded); out-of-coverage / pre-existence / known-gap
      (date,league) → typed empty (`EXPECTED_KNOWN_SOURCE_GAP` / `EXPECTED_NO_FIXTURE`), never
      attempted/flagged-missing.
- [x] ✅ **⑦ deployment-api/UI numerator/denominator = the could-exist universe (IS+UAC+manifest)** — deployment-api
      `data_status_service.py` `_sports_honest_coverage` (≈L841-899): denominator = the EXPECTED set from
      `get_league_fixture_calendar()` (the canonical league×date universe, source-agnostic), numerator = manifest rows
      with captured / typed-empty status. **Instruments-exist-but-backfill-not-run is in the denominator but NOT the
      numerator → shows as MISSING (under-coverage), never silently excluded** (no false 100%). UI renders the v9
      4-state sports drilldown.

## G2 WAVE-2 readiness verdict — slot-4 re-verify on WAVE-1 code (2026-06-07)

> Re-ran every sports dry-run against the **current LDR** (post-WAVE-1: source-aware migrators + shape-aware G1-ENUM
> producer `is@6ea46565` + AG-parametric G1-V8 instruments-store migrator `is@febb899e`). **All read-only on real prod
> GCS.** Verdict: **sports migration CODE is dry-run GREEN; one code bug found + fixed (UAC); two data-state gaps
> captured below; `--apply` stays G4-gated.**

**① MTDS migrator dry-run — GREEN** (`migrate_sports_canonical_v9.py --surface mdps --dry-run`, 2026-02-20..21 window,
real `market-data-tick-sports-prd`): 401 raw + 137 processed objects in scope, copied=0 (dry-run). Projected dest paths
are canonical + **source-aware**: raw `category=sports/data_source=ODDS_API/…` →
`pipeline_mode=batch_odds_api/asset_group=sports/venue=…/league_id=…/instrument_type=odds/data_type=trades/` (CF-2
`category`→`asset_group` ✅, CF-3/CF-13 source-aware `pipeline_mode=batch_<source>` ✅); processed candles →
`pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/…` ✅. The source-aware `pipeline_mode` values passed
UAC's closed-set `pipeline_mode_for_source()` (no ValueError).

**② Instruments-store v9 migrator dry-run — GREEN**
(`migrate_instruments_store_v9.py --asset-group sports --skip-objects`, real `instruments-store-sports-prd` `_index`,
the G1-V8 tool `is@febb899e`): **2,681,044 rows → 100% v9** (v8_before 2,680,309 + v9_before 735). CF-1 v9 ✅ · CF-2
`asset_group=sports` (2,667,868 stamped) ✅ · CF-13 source-aware `pipeline_mode` {`batch_api_football` 2.03M,
`batch_footystats` 352K, `batch_open_meteo` 105K, `batch_transfermarkt` 81K, `batch_soccer_football_info` 77K,
`batch_understat` 25K, `batch_odds_api` 6.6K} ✅ · CF-4 `source` column (api_football/footystats/…) ✅ · CF-TRANSPORT
`transport=rest` (100%) ✅ · CF-8 `available_at` filled (2,667,868) ✅ · CF-7 canonical data_types
(STANDINGS/FIXTURES/INJURIES/…) ✅. Sample row v9-canonical. So cf_manifest_audit(instruments-store-sports) goes
**CF-GREEN under projection**; the `--apply` RUN stays G4-gated.

**③ Manifest-rebuild dry-run — code proven, data-state gated**
(`rebuild_sports_manifest_v9.py --surface mdps --dry-run`): the rebuild reads via UTL `read_availability_index`
(consolidated/per-VM view) and today loaded **0 rows** ("Empty index — nothing to rebuild" — honest, no crash, no
placeholder). The prd mdps `_index/availability_index.parquet` main file has **786,408 rows** (pandas direct read:
empty_confirmed 584,177 + captured 202,067 + attempted_failed 164, schema_version 100% v8, columns
`asset_group`/`source`/`transport` ABSENT, `pipeline_mode` None/blank — the expected PRE-migration v8 state). Slot-6's
earlier rebuild read the full 786K (its 584,177+202,067 histogram matches this file exactly), so the **rebuild code is
proven**; today's 0 is a per-VM/consolidation-state gap (the main file was rewritten 2026-06-07T20:45; `_index/per_vm/`
holds only a 196KB `_legacy_seed`). Captured as a data-state finding below; the `--apply` is already
E3-drain+consolidate-gated.

**④ Catalogue + enumerate (shape-aware, league-grain) — matrix slice VERIFIED + a CODE BUG FIXED.** The slot-7 G1-ENUM
producer (`is@6ea46565`) preserved the sports league-grain `_enumerate_v2_sports` / `_SPORTS_PRESENT_COLS` /
`build_sports_catalogue_dataframe` (`is@99a5fbf5`). **But its new `_row_data_types` validity filter consulted the UAC
matrix `("sports","league")` slice, which was WRONG** — it listed the lowercase MTDS odds market-data types instead of
the reference-data `SPORTS_DATA_TYPE_TO_SOURCE` keys, so the producer **silently DROPPED `ODDS`** (it is both a
`SPORTS_DATA_TYPE_TO_SOURCE` key AND a `DATA_TYPES_BY_ASSET_GROUP["sports"]` member → failed both arms of the filter).
Empirically confirmed (16/17 league reference data_types kept, `ODDS` dropped). **FIXED** —
`valid_data_types_for_instrument_type` now DERIVES the sports/league set from `SPORTS_DATA_TYPE_TO_SOURCE` (mirroring
the DeFi lazy-derivation pattern; eliminates the hand-written-literal drift), the wrong static literal removed, +3
regression tests; verified all 17 keys kept + impossible odds-types still rejected + 132 IS enumerate/catalogue consumer
tests green. **Shipped: uac@aff80339 (PR#95 → staging, auto-merge).** The full catalogue+enumerate prod re-run is
list-bound (>15 min — the existing PERF P2 list-cost finding) → VM/scheduler-class; mechanism is unit-test-proven
post-fix.

**Remaining gates for the sports `--apply` (G4):** G0 (coordinator) + the instruments-store v9 walk (G1-V8 `--apply` on
a VM) + IS instrument backfill (`by_date` capture freeze) + the two findings below + pre-migration drain. Sampled (not
walked): the migrator object dry-run used a 2-day window; the instruments-store v9 + manifest reads were full-corpus
(2.68M / 786K). Remaining gaps = the gated VM `--apply` walks.

### Apply-readiness verdict — slot-4 7+2 audit on LDR (2026-06-07, no sports code changed since uac@aff80339)

> **Sports migration code is APPLY-READY (CF-1…CF-14 all GREEN under dry-run as of is@cbcf55e8).** The last sports-owned
> blocker, CF-14 (the IS-catalogue could-exist denominator), is **FIXED + real-prod dry-run-verified** (catalogue 606 ⊇
> manifest 606, 0 over-seed). Its prior RED was MIS-CHARACTERISED (the "392 missing / union entities" framing); the real
> root cause (raw-numeric `entity=leagues` vs canonical manifest namespace) is resolved by deriving the universe from
> the manifest. **The ONLY remaining sports gates are OPERATIONAL** (G0 · G3 union view (slot-7) · the IS
> instruments-store v9 walk RUN · IS instrument backfill · pre-migration drain) + the staging-lock unblock for
> is@cbcf55e8. Two data-quality findings (6,869 blank `capture_status`, mdps consolidated-index-reads-0) remain P1 but
> are not over-seed/correctness-of-denominator blockers.

CF-by-CF (sampled vs walked stated per row):

- **CF-1 v9** ✅ projection — instruments-store v9 dry-run = 2,681,044 rows → 100% v9 (full-corpus walk).
- **CF-2 `asset_group=`** ✅ — migrator path `category`→`asset_group=sports` (2-day sample) + IS v9 column (walk).
- **CF-3 `pipeline_mode=` partition** ✅ — migrator inserts `pipeline_mode=batch_<source>/` in path (sample).
- **CF-4 `source` column** ✅ — IS v9 stamps `source` (api*football/footystats/…); MTDS migrator `batch*<source>`
  (walk/sample).
- **CF-5 typed empty reasons** ◑ — typed reasons wired (E6/keystone), BUT the **6,869 blank `capture_status` IS rows**
  (P1 below) are an open CF-5 gap; mdps rebuild reason-relabel proven by slot-6 (today's read returned 0 — consolidation
  state, P1 below).
- **CF-6 `expected_unattempted`** ✅ — unblocked by the CF-14 fix (is@cbcf55e8); the could-exist seed now materialises
  the namespace-correct league universe (the `--apply-write` RUN is the gated operational step).
- **CF-7 canonical names** ✅ — IS v9 data_types canonical uppercase (walk); migrator `canonicalize_league_id` wired.
- **CF-8 `available_at`** ✅ — IS v9 `available_at_filled` 2,667,868 (walk).
- **CF-9 env-split bucket** ✅ — `resolve_bucket_name` used; `-prd` tier confirmed.
- **CF-10 no phantom captured** ◑ — not separately walked this pass (the IS `by_date` capture freeze is the upstream
  gate).
- **CF-11 fetch-fail→attempted_failed** ✅ — match-day guaranteed-type relabel shipped (mtds@8ffb2acd).
- **CF-12 batch=live** ✅ — shared `candidate_parquet_paths()` / `pipeline_mode_for_sports_entity` SSOT (prior audit).
- **CF-13 pipeline_mode source-aware** ✅ — `batch_odds_api`/`batch_<source>` in path+column (sample/walk).
- **CF-14 IS-catalogue could-exist ROOT** ✅ **FIXED is@cbcf55e8** — the sports rollup now derives the could-exist
  league universe from the **manifest** (namespace-correct superset) + the enumerator gates by
  `get_entity_league_coverage`. Real-prod dry-run verified: catalogue 606 == manifest 606 (⊇, 0 missing), 0 false
  numeric over-seed, XG within Understat coverage; +3 tests; IS QG green. Was RED (raw-numeric `entity=leagues`, 131/606
  coverage, over-seed). Staging promotion queued behind the fleet staging-lock. **No remaining sports-owned correctness
  blocker** — the rest are operational gates.

**Operational gates (not sports-code):** G0 (coordinator) · G3 union view (slot-7) · the IS instruments-store v9 walk
RUN (G1-V8, VM) · IS instrument backfill (capture freeze) · pre-migration drain. **Sports-code gate:** the CF-14
catalogue fix (P0 below) must land + dry-run-prove `seeded leagues == manifest current-dt leagues` (0 numeric over-seed)
BEFORE the apply-write. No sports migrator/rebuild/UAC code changed since the WAVE-2 pass (uac@aff80339) → CF-1…CF-13
dry-runs are unchanged-green (instruments-service + market-tick-data-service worktrees clean).

- [ ] [DATA] P1. **6,869 sports instruments-store `_index` rows carry BLANK `capture_status`** (CF-5 honest-absence
      violation) — surfaced by the G1-V8 dry-run
      (`capture_status: {empty_confirmed 1,909,553, captured 586,597,     attempted_failed 178,025, '' 6,869}`). The
      `migrate_instruments_store_v9` migrator PRESERVES the blank → it would ride into v9 unless relabelled. **Diagnosed
      (slot-4 2026-06-07)**: all 6,869 blanks are `service_name=instruments-service` with **blank `data_type`** + NaN
      `feature_group` (schema_version 8) — i.e. instrument-definition / reference rows, NOT market-data capture cells.
      Decide the canonical 4-state for a definition-only row (either a typed `expected_unattempted`/`empty_confirmed`
      reason, or exclude from the capture-status denominator if reference rows are status-exempt by design) and stamp it
      in the same single walk. Gates the sports IS `--apply`. Co-owner: slot-7 (the AG-parametric
      `migrate_instruments_store_v9` central tool) + slot-4 (sports relabel semantics). Repo: instruments-service.
      parent_epic: mtds_mdps_master. Provenance: slot-4 WAVE-2 verify 2026-06-07.
- [ ] [DATA] P1. **prd mdps consolidated `_index` reads 0 via `read_availability_index` despite 786K main-file rows** —
      the live `_index/availability_index.parquet` (786,408 v8 rows) was rewritten 2026-06-07T20:45 but
      `read_availability_index` (per-VM-consolidated view) returns 0; `_index/per_vm/` holds only a 196KB
      `_legacy_seed`. Slot-6's run read the full 786K, so this is a post-20:45 consolidation/per-VM-state regression,
      NOT rebuild code. Confirm the 20:45 writer (which process?) did not leave the per-VM consolidated view empty; the
      mdps rebuild `--apply` is E3-drain+consolidate-gated which would refresh it, but verify the main-file 786K rows
      survive the consolidation (do not lose them). Repo: market-tick-data-service / unified-trading-library
      (consolidator). Owner: vm-sports + cross-cutting. parent_epic: mtds_mdps_master. Provenance: slot-4 WAVE-2 verify
      2026-06-07.
- [ ] [INFRA] P1. **`quickmerge --agent` is structurally broken for LIBRARY repos — sentinel mechanism gap
      (cross-cutting, surfaced shipping uac@aff80339)**: `base-library.sh` writes ONLY `.qg_content_sentinel`, never
      `.qg_last_passed_sha` (unlike `base-service.sh:2697`), but `quickmerge.sh` STAGE 3 `--agent` fast-path checks ONLY
      `.qg_last_passed_sha` (`:1039`, no content-sentinel fallback) → a library QG-green tree always reads
      `Sentinel: <missing>` and quickmerge `--agent` hard-refuses. Workaround used here: hand-wrote
      `.qg_last_passed_sha = HEAD` after a verified full green run (safe for a library — no cross-repo dep state; full
      tests ran, not a content-HIT). **Fix**: either make `base-library.sh` write `.qg_last_passed_sha` on a complete
      non-HIT green run (mirror `base-service.sh:2696-2702`), OR teach `quickmerge.sh` STAGE 3 to accept
      `.qg_content_sentinel` for library repos. Blocks EVERY library ship via `quickmerge --agent` (UAC / UTL). Repo:
      unified-trading-pm (`quality-gates-base/` + `quickmerge.sh`). **Migrate to**
      `qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md` (the sentinel-contract plan) on next touch — parked
      here as the surfacing record. Owner: vm-cross-cutting. parent_epic: mtds_mdps_master. Provenance: slot-4 WAVE-2
      ship 2026-06-07.

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

## ⑦ Coverage-denominator could-exist seed — cross-AG note (filed by slot-5 2026-06-04)

> Operator 2026-06-04 (point ⑦): the deployment-api/ui coverage **denominator** must reflect the **could-exist
> universe** (instruments/fixtures that exist in IS but whose backfill has NOT run), not just rows that exist in the
> manifest. **The seeding mechanism already exists** — `instruments-service/scripts/enumerate_expected_universe.py` (v2
> expected-universe enumerator) cross-joins the IS catalog × dates × data_types, subtracts existing manifest rows, and
> seeds `record_expected_unattempted` for the residual; deployment-api `data_status_hierarchical` already counts
> `expected_unattempted` in the 4-state denominator. Slot-5 fixed the cross-cutting blocker: the enumerator's default
> bucket map was stale for ALL 5 AGs (missing the `-prd-` env tier) → now resolves via `resolve_bucket_name`
> (instruments-service, ⑦ in `prediction_manifest_canonicalisation_2026_06_01.md`). **Remaining for sports:**

> **🔴 G1.dry-run FINDING (slot-4, 2026-06-07) — the GENERIC `build_instrument_catalogue.py --asset-group sports`
> produces a 0-row (empty) catalogue → it CANNOT seed the sports could-exist universe. Confirmed on real prod GCS
> (`instruments-store-sports-prd-central-element-323112`). Two independent reasons, both proven:**
>
> 1. **Raw provider columns, not canonical.** `sports_reference/by_date/day=*/entity=*/` parquets carry RAW provider
>    schemas — `entity=fixtures` → `af_fixture_id`/`af_league_id`; `entity=leagues` → `league_id`/`name`/`country`;
>    `entity=teams` → `team_id`/`available_at` — **NONE** has the `instrument_key`/`instrument_id` column the generic
>    `_row_id`/`build_catalogue_dataframe` (build_instrument_catalogue.py:101,144) requires. Deterministic proof:
>    `_row_id` → 0 non-null on real fixtures(13)/fixture_events(55) rows;
>    `build_catalogue_dataframe([fixtures, fixture_events]) → 0 catalogue rows`. `run_rollup` has a `prediction` branch
>    but **no `sports` branch** (falls into the generic path). A plain run would promote an EMPTY catalogue.
> 2. **Grain mismatch (bundled-atom — the exact slot-7 concern; ANSWER to "confirm sports grain before a plain run").**
>    The sports captured atom in the canonical `_index` (586,597 captured rows) is
>    per-**`(league_id, data_type, date)`** — `league_id` populated 95% (1,614 leagues), `instrument_id` blank 95%,
>    `venue` blank 93%, `instrument_type` blank ~100%. So **sports could-exist grain = per-LEAGUE, NOT per-fixture**: a
>    fixture-grain catalog would never match the league-grain manifest present_set → every entry seeds
>    `expected_unattempted` → massively inflated denominator.
>
> **Required producer (gated CODE, repo=instruments-service)**: add a `build_sports_catalogue_dataframe` branch to
> `build_instrument_catalogue.py` (mirror `build_prediction_catalogue_dataframe`), entity-aware + **league-grain** —
> roll up `sports_reference/by_date/entity=leagues` → one row per league: `instrument_id=league_id` (or league_id col),
> `instrument_type="league"`, `venue=<source>`, `available_from`/`available_to` = first/last day the league appears.
> Then make `_enumerate_v2_sports`'s present_set match league-grain (`present_cols=["data_type","league_id","date"]`,
> blank-tolerant on venue/instrument_id/instrument_type) so it matches the manifest atom.

- [x] ✅ [CODE] P1. ⑦ sports could-exist denominator seed — instruments-service@99a5fbf5 (QG-green, exit 0; on LDR).
      Added `build_sports_catalogue_dataframe` (league-grain roll-up of `sports_reference/by_date/entity=leagues` → one
      row per league: `instrument_id=league_id`, `instrument_type="league"`, `venue=""` to match the venue-blank
      captured atom, `available_from`/`available_to` lifecycle) + `sports` branch in `run_rollup` (default prefix
      `sports_reference/by_date`). Rewrote `_enumerate_v2_sports` to LEAGUE-grain: present-set match on
      `(data_type, league_id, date)` ONLY (`_SPORTS_PRESENT_COLS`, blank-tolerant on venue/instrument_id/instrument_type
      via `_present_cols_for`, applied in `_build_present_set` + v1/v2 main paths), iterates the captured provider
      data_types (`_sports_data_types()` = `SPORTS_DATA_TYPE_TO_SOURCE` keys, NOT the MTDS odds types), per-data_type
      `get_source_coverage_start` skips pre-coverage dates (owned by v1, no double-emit), yields the seeded
      `expected_unattempted` with blank venue/instrument_id/instrument_type so the atom matches captured. Verified on
      the real prod `_index` (2.68M rows): data_types = STANDINGS/FIXTURES/XG/… (the 17 `SPORTS_DATA_TYPE_TO_SOURCE`
      keys), league_id nonblank 97.6%, venue/instrument_id/instrument_type ~blank. Unit tests
      (`test_build_instrument_catalogue.py`: producer league-grain + producer→`enumerate_v2(sports)` emits
      `expected_unattempted` vs a league-grain present_set + skips captured + skips pre-coverage +
      superset-never-shrinks regression). Repo: instruments-service. parent_epic: mtds_mdps_master.
- [ ] [INFRA] P2. ⑦/⑧ sports catalogue-regen scheduler — **NOT LIVE (slot-4 verified 2026-06-07)**: the TF jobs
      `catalogue-regen-nightly` (catalogue_regen_scheduler.tf, sports in `for_each`) +
      `instrument-catalogue-regen-nightly` (instrument_catalogue_scheduler.tf) are absent from the live prod scheduler
      (`gcloud scheduler jobs list     --location=asia-northeast1` — only consolidator +
      `instruments-service-daily-trigger` are ENABLED). So the daily catalogue aggregation is wired in TF for sports but
      **not deployed** for ANY AG. Blocked behind the league-grain producer regardless (a scheduled sports regen today
      would emit a 0-row catalogue). Cross-AG infra owned by vm-cross-cutting
      (`master_data_canonicalisation_migration_catalogue_2026_06_07.md` G1.schedule); this row tracks the sports-slice
      verification. Repo: deployment-service (terraform). parent_epic: mtds_mdps_master.
- [ ] [DATA] P1. ⑦ sports apply-write run — **GATED** (producer DONE instruments-service@99a5fbf5; these gates still
      UNMET as of slot-4 2026-06-07): (a) slot-7 PART C G1-foundation code GREEN
      (`proper_instrument_catalogue_lifecycle_rollup_2026_06_04` — 2/7 done at check); (b) sports IS instrument backfill
      complete (`by_date` capture FROZEN ~2026-05-21 fleet-wide per that plan's FINDING); (c) the canonical
      `instruments-store-sports-prd` `_index` is v9 (TODAY it is **v8** — v9=735/2,681,044=0.0%; rides the gated E4
      single-walk, NOT yet run). When all met: build the catalog →
      `enumerate_expected_universe.py --asset-group sports --enumerator-version v2 --catalog-path <catalog> --apply-write`
      on a VM (`MANIFEST_PER_VM_SHARDS=true`, `VM_NAME=<tag>`; GCS flaky locally) so the raw-tick denominator ==
      could-exist universe; add a regression (IS-universe ⊃ manifest ⇒ denominator doesn't shrink). The mechanism +
      bucket fix are done. parent_epic: mtds_mdps_master.
- [x] ✅ [DATA] **P0. ⑦/CF-14 sports could-exist catalogue — FIXED is@cbcf55e8 (slot-4 2026-06-07; real-prod dry-run
      verified).** The sports rollup now derives the could-exist league universe from the **manifest** (the
      namespace-correct superset), and `_enumerate_v2_sports` gates each `(league, data_type)` by
      `get_entity_league_coverage`. **Real-prod validation**
      (`build_instrument_catalogue --asset-group sports --dry-run` → 606 rows in ~8s, was >15min; in-process enumerate
      over a 2-day window): **catalogue 606 == manifest current-dt leagues 606 → catalogue ⊇ manifest, 0 missing**;
      **every seeded league ∈ the manifest (0 false numeric over-seed**, vs the old 1,228 phantom-numeric leagues); **XG
      seeds only within Understat coverage**. +3 regression tests; IS `quality-gates.sh --no-fix` exit 0.
      (Implementation note: the manifest-derived universe lives in the producer `build_sports_catalogue_from_manifest`
      reading the `_index` directly — not `read_availability_index`, which has returned 0 mid-rewrite — scoped to
      current `SPORTS_DATA_TYPE_TO_SOURCE` data_types; the old `entity=leagues` `build_sports_catalogue_dataframe` is
      superseded.) **Residual (honest, NOT a silent drop)**: api-football leagues LISTED but never captured aren't added
      (needs a numeric→canonical `api_football_id` map; gated on the IS backfill anyway). **Staging promotion of
      is@cbcf55e8 is queued behind the fleet staging-lock** (UAC 0.2.0 cascade) — committed to LDR, drains via the
      staging→main automation on unlock. Original diagnosis ↓ retained for context:
  - **The catalogue emits RAW NUMERIC api-football `league_id`s** (`_league_id_of` → `str(row["league_id"])`, e.g.
    `"4"`/`"21"`/`"62"`), but the manifest captured atom uses the **canonical** sports league namespace. Measured on
    real prod (`day=2025-01-01 entity=leagues` × the prod `_index`): `entity=leagues` has 1,228 raw league_ids;
    `canonicalize_league_id()` is a **NO-OP** on them (0% changed — it only strips name-suffixes/aliases, it does NOT
    map a numeric api_football_id → canonical id); and the canonicalised set covers **only 131 / 606** distinct manifest
    current-data_type leagues → **475 missing**. So entity=leagues is NOT a reliable superset of the manifest leagues.
  - **Severity is OVER-seed, not under-seed**: on an `--apply-write`, `_enumerate_v2_sports` iterates the 1,228 numeric
    catalog leagues × ~17 data_types; none match the canonical present-set → it would seed **millions of FALSE
    `expected_unattempted`** rows (numeric leagues that have no manifest counterpart) — the exact denominator-distortion
    CF-14 exists to prevent. (The dry-run is scan-only so prod is untouched.)
  - **The could-exist universe for CURRENT data_types = 606 leagues across 6 sources** (api_football 542, footystats
    160, transfermarkt 87, open_meteo 85, soccer_football_info 33, understat 19) — all in the canonical namespace.
    `LEAGUES`/`TRANSFERMARKT_LEAGUES`/`SFI_LEAGUES` (the numeric/hex namespaces) are **RETIRED data_types** (not in
    `SPORTS_DATA_TYPE_TO_SOURCE`) → correctly NOT in the current denominator.
  - **UAC SSOTs found for the fix**: `SPORTS_ENTITY_LEAGUE_COVERAGE` / `get_entity_league_coverage(entity)` (most
    current entities cover ALL leagues = `None`; `XG`/`XG_SHOTS` cover only understat's ~5 leagues via
    `does_understat_cover()`); `get_sports_entity_start_date(entity)` (per-entity coverage-start).
    `_enumerate_v2_sports` currently applies **NEITHER** → it would also seed XG for every league (wrong).
  - **CORRECT FIX (the reliable superset is the manifest itself)**: derive the sports could-exist league universe from
    the **manifest present-set per source** (a captured league provably could-exist; namespace-correct by construction;
    guarantees catalogue ⊇ manifest leagues). The enumerator already loads the full manifest (`_build_present_set`). Two
    parts: (1) build the sports `catalog` from the distinct manifest `league_id`s (lifecycle = first/last present date),
    NOT from `entity=leagues` numeric roll-up — so `build_sports_catalogue_dataframe`/the sports v2 catalog source must
    switch to the manifest-present leagues (the `entity=leagues` listing is only an optional add for api-football
    listed-but-never-captured leagues, a follow-up refinement); (2) in `_enumerate_v2_sports`, gate each
    `(league, data_type)` by `get_entity_league_coverage(data_type)` + `get_sports_entity_start_date` (skip XG outside
    understat's set — `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE`). Repo: instruments-service
    (`build_instrument_catalogue.py` + `enumerate_expected_universe.py`); validate by a real-prod dry-run asserting the
    seeded league set == the 606 manifest current-dt leagues (catalogue ⊇ manifest, 0 numeric over-seed) + unit tests on
    synthetic per-source present-sets. parent_epic: mtds_mdps_master. Provenance: slot-4 apply-ready re-diagnosis
    2026-06-07.
- [x] ✅ [PERF] P2. ⑦ sports league-catalogue roll-up list-cost — **OBSOLETE as of is@cbcf55e8** (slot-4 2026-06-07):
      the manifest-derived producer reads the single `_index/availability_index.parquet` (one object) in **~8 s**
      instead of `list_blobs`-ing the whole `sports_reference/by_date/` tree (>15 min) —
      `_iter_sports_by_date_snapshots` is no longer on the sports rollup path. The `StorageClient.list_prefixes`
      common-prefixes enhancement remains a generic UTL nice-to-have for the other AGs' by-date iterators (not
      sports-blocking) — re-file under the relevant AG if still wanted. parent_epic: mtds_mdps_master.
