---
doc_type: audit-result
title: "Data-pipeline reconciliation — sports (2026-07-20)"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=sports over PROD buckets only (read-only). Representative
  sample: full manifest 4-state census of BOTH sports indexes (raw-tick + instruments-store) plus day=2026-07-10
  four-surface disk probes and multi-day WEATHER/ODDS spot-checks. All three prod buckets reachable, no -test- leak,
  legacy flat-named buckets confirmed 404. Sports is the structural exception (no asset_group= hive key; oracle is 100%
  false-positive on sports_reference/ + processed/). Key live findings: 721,154 instruments-store phantoms
  (stale/MEDIUM-confidence, dominated by cross-lane trades+odds_horizon_bucket, includes PROVEN layout-drift false
  positives); UAC WEATHER layout drift (declared PER_DAY_BARE, writer emits PER_DAY_PER_LEAGUE); FIXTURES umbrella
  writer still emitting today (zero SCHEDULE/OUTCOMES); cross-AG bleed grown to 6,597 prediction rows. AE-1 suppressed
  (13,903). C2a REFUSED; sports data_type K2 casing = migration_pending open decision.
status: partial
nature: record
asset_group: [sports]
stage: [data]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    unified-trading-library,
    market-tick-data-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, four-surface, sports, delete-safety, non-canonical-paths, manifest, phantom]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
  ]
created: 2026-07-20
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=sports, PROD (-prd-) buckets only, read-only; sample = full manifest 4-state census (both indexes) +
  day=2026-07-10 four-surface disk probes + multi-day WEATHER/ODDS spot-checks + top-level tree sweep"
date: 2026-07-20
auditor: /data-pipeline-reconciliation (first real execution + acceptance test — sports)
parent_epic: infrastructure_master
severity: P1
skill: data-pipeline-reconciliation
run_date: 2026-07-20
generated_at: 2026-07-20T00:00:00+00:00
---

# Data-pipeline reconciliation — sports (2026-07-20)

**Read-only.** No GCS writes, no manifest writes, no deletes, no backfills, no VM launches, no `--apply`. Deletes below
are SUGGESTIONS only; every prod-bucket delete is a human-only hard stop.

> **Sports is the STRUCTURAL EXCEPTION.** There is no `asset_group=` hive key in the reference tree, and the UAC machine
> oracle (`canonical_path_violations`) returns immediately for any path not under `raw_tick_data/by_date/` — so it is a
> **100% false-positive on `sports_reference/` and `processed/`** (measured, §2). Canonical-vs-non-canonical for the
> reference + MDPS-processed lanes is decided by the sports dispatcher `candidate_parquet_paths()`, never the oracle.
> `canonical_path_templates("sports") == []` (measured) is a routing instruction, not zero coverage.

## 0. Declared sample scope (honest partial pass)

This is **not** a full-corpus reconciliation. What was and was not done:

**Sampled / measured (complete where stated):**

1. **Full manifest 4-state census of BOTH sports indexes**, read whole: `market-data-tick-sports-prd` index (1,974,679
   rows, 48.4 MB, updated 2026-07-20 19:07) and `instruments-store-sports-prd` index (5,377,883 rows, 125 MB, updated
   2026-07-20 19:03). Every distribution below (asset_group, data_type, capture_status, pipeline_mode, source,
   instrument_type, blank-gate) is over the **entire** index, not a slice.
2. **Four-surface disk probes on `day=2026-07-10`** for ODDS, WEATHER, XG, TEAMS, PLAYER_VALUES, FIXTURE_STATS, FIXTURES
   — via `candidate_parquet_paths()` iterated over the FULL candidate list, then corrected for the `pipeline_mode=`
   interposition and the `fetched_at_hour=` wildcard (§3).
3. **Multi-day confirmation** of the WEATHER layout drift (days 2026-07-10 / 2026-07-05 / 2026-06-20) and ODDS presence
   (2026-07-10 / 2026-07-05).
4. **Full phantom-triage read** (`triage_sports_20260714_063147.jsonl`, all 721,154 lines) for data_type composition.
5. **Top-level (non-recursive, delimiter='/') tree sweep** of all three prod buckets (Phase-0 reachability + inventory
   rows 1/4/13/16).
6. **S4 catalogue** `prod/catalog.parquet` (164,771 rows) + `prd/`-shadow existence check.

**NOT sampled (declared gaps, see §8):** whole-corpus orphan walk (route-3 — **orphans NOT ASSESSED**); deep parquet
content/schema-pillar reads (S2 verified via existence + `parquet_row_count`, not column-level); S1 disk verification
beyond `day=2026-07-10` for the reference lane and beyond top-level for the raw-tick lane; `features-sports` content;
the H5 6.72M-row generational row-count comparison (carried from reference sheet, **not re-measured** — needs a walk);
`data-catalogue.instruments-service.yaml` staleness (deployment-api artifact, not in these buckets — **UNVERIFIED this
run**, carried from skill §3c).

## 1. Bucket paths table (auto-derived from the resolver + probes)

Every bucket resolved via `resolve_bucket_name(cloud="gcp", kind=<k>, asset_group="sports", deployment_env="prd")` over
`configs/cloud-providers.yaml` (project via `GCP_PROJECT_ID=central-element-323112`; tier passed explicitly via
`deployment_env=`, never env-mutated). No `-test-` name resolved.

| Surface / layer             | `kind`              | Resolved bucket                                       | Reachable?              | Read targeted                                                                    |
| --------------------------- | ------------------- | ----------------------------------------------------- | ----------------------- | -------------------------------------------------------------------------------- |
| raw tick (S1/S2/S3)         | `market-data`       | `market-data-tick-sports-prd-central-element-323112`  | YES (8 child prefixes)  | `raw_tick_data/`, `processed/`, `_index/availability_index.parquet`, `scripts/`  |
| raw tick alias              | `tick-data`         | `market-data-tick-sports-prd-central-element-323112`  | YES (same bucket)       | —                                                                                |
| reference/catalogue (S3/S4) | `instruments-store` | `instruments-store-sports-prd-central-element-323112` | YES (11 child prefixes) | `sports_reference/`, `prod/catalog.parquet`, `_index/availability_index.parquet` |
| features                    | `features-sports`   | `features-sports-prd-central-element-323112`          | YES (5 child prefixes)  | top-level only (`sports_features/`, `_index/`)                                   |

**Negative controls (correct behaviour):** `resolve_bucket_name(kind="features", asset_group="sports")` correctly
**RAISES** `BucketNamingError` (the per-AG `features` dict has no SPORTS key — reference sheet confirmed; must use
`kind="features-sports"`). **Legacy flat-named buckets** `instruments-store-sports-central-element-323112` and
`market-data-tick-sports-central-element-323112` both return **`exists=False` (404)** — already deleted, no delete
suggestion emitted (recorded as already-resolved). **No bucket was unreachable.**

## 2. Machine oracle behaviour (sports = structural exception; STRUCTURE-only where applicable)

`canonical_path_violations()` run on four real/derived sports paths at both `require_pipeline_mode` settings:

| Path (real, from disk)                                                                                  | require_pm=False | require_pm=True  | Verdict                                     |
| ------------------------------------------------------------------------------------------------------- | ---------------- | ---------------- | ------------------------------------------- |
| reference `sports_reference/…/entity=teams/league=COPPA_ITALIA/teams.parquet`                           | prefix-violation | prefix-violation | **oracle N/A** (not under `raw_tick_data/`) |
| reference bare `entity=fixtures/league=K_LEAGUE_2/fixtures.parquet` (H2 umbrella)                       | prefix-violation | prefix-violation | **oracle N/A**                              |
| raw-tick `raw_tick_data/by_date/day=…/pipeline_mode=batch_odds_api/asset_group=sports/venue=ODDS_API/…` | CANONICAL        | CANONICAL        | STRUCTURE OK (raw-tick lane)                |
| MDPS `processed/by_date/day=…/data_type=odds_horizon_bucket/bucketed.parquet`                           | prefix-violation | prefix-violation | **oracle N/A** (processed lane)             |

**Which question was machine-checked:** for the raw-tick lane (`raw_tick_data/`), path STRUCTURE was oracle-checked and
is CANONICAL. **id-form was NOT machine-checked** — sports has no `VENUE:TYPE:SYMBOL` id grammar (reference sheet:
identity is `(entity, league, day)` / `fixture_id` row column), and the oracle's only stem rule is tradfi-gated. For the
**reference** (`sports_reference/`) and **MDPS-processed** (`processed/`) lanes the oracle is inapplicable by
construction — canonicality there was decided by `candidate_parquet_paths()` dispatch (§3), which is the sports SSOT.

## 3. Per-surface verdict per shard (four surfaces = four bits, never collapsed)

Legend: `OK` · `NON-CANON` · `ABSENT` · `PRESENT` · `SUPPRESSED` · `NOTE` · `NOT-READ` · `REFUSED` · `oracle-N/A`.
Probed on `day=2026-07-10` unless noted. **The probe-vocabulary rule was live here** — the first probe pass produced
FOUR false absences (ODDS/WEATHER/PLAYER_VALUES/FIXTURE_STATS) because `candidate_parquet_paths()` was called without
`pipeline_mode=`; the canonical on-disk layout interposes `pipeline_mode=` **between** `day=` and `entity=`. Re-probed
with the manifest row's `pipeline_mode` (correct vocabulary).

| #   | shard (day=2026-07-10)                                       | S1 path                                                                                                      | S2 content            | S3 manifest                                        | S4 catalogue                   | notes                                                                    |
| --- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | --------------------- | -------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------ |
| 1   | `TEAMS` (COPPA_ITALIA, 107 rows)                             | **PRESENT** `…/pipeline_mode=batch_api_football/entity=teams/league=COPPA_ITALIA/teams.parquet` (oracle-N/A) | PRESENT (blob exists) | OK (`captured`)                                    | OK (`instrument_type=team`)    | canonical reference shape                                                |
| 2   | `PLAYER_VALUES` (PRIMEIRA_LIGA, 32 rows, PER_DAY_PER_SEASON) | **PRESENT** `…/pipeline_mode=batch_transfermarkt/entity=player_values/season=2025/player_values.parquet`     | PRESENT               | OK (`captured`)                                    | OK (`instrument_type=player`)  | full-list iteration found season=2025 (early-return would have missed)   |
| 3   | `ODDS` (footystats_odds, PER_DAY_PER_LEAGUE)                 | **PRESENT** under `entity=footystats_odds/fetched_at_hour=2026-07-12T06/footystats_odds.parquet`             | PRESENT (4 objs)      | NOTE `league_id=''` (blank) on a per-league type   | OK                             | `fetched_at_hour=` wildcard needs prefix-resolution, not `exists('*')`   |
| 4   | `WEATHER` (K_LEAGUE_2)                                       | **NON-CANON vs UAC** `…/entity=weather/league=K_LEAGUE_2/weather.parquet` (writer=PER_DAY_PER_LEAGUE)        | PRESENT               | OK (`captured`)                                    | n/a                            | **UAC declares WEATHER=PER_DAY_BARE → dispatcher false-absents it → F2** |
| 5   | `FIXTURES` (K_LEAGUE_2, 3 rows)                              | **PRESENT** bare `entity=fixtures/league=K_LEAGUE_2/fixtures.parquet` (NO `pipeline_mode=`)                  | PRESENT               | NOTE `data_type=FIXTURES` (superseded umbrella)    | OK (`instrument_type=fixture`) | **umbrella writer live (H2 → F3)**; zero SCHEDULE/OUTCOMES               |
| 6   | raw-tick `odds` / `trades` lane                              | **OK** (structure canonical, oracle-checked)                                                                 | NOT-READ (deep)       | 4-state census done                                | n/a                            | `raw_tick_data/by_date/day=/pipeline_mode=/asset_group=sports/…`         |
| 7   | manifest `instrument_type` COLUMN                            | n/a                                                                                                          | n/a                   | **REFUSED (C2a)** — 4.44M NULL + tiny mixed casing | n/a                            | sports barely uses instrument_type as an axis; compared case-insens.     |

## 4. Typed findings (taxonomy names only — diffable)

Coverage formula (any %): `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`,
`empty_confirmed` **EXCLUDED** (honest-coverage-model, CK3-certified). Every % is a **LOWER BOUND**
(`instrument_gates_download=true` for all AGs).

| #   | type                                                        | severity                                | shard / location                                                                                                                                                            | surfaces   | detector                                        | delete_elig    | notes                                                                                                                                                                                          |
| --- | ----------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- | ----------------------------------------------- | -------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F1  | `phantom`                                                   | HIGH (MEDIUM-confidence, drift-suspect) | `instruments-store-sports` `phantom_count=721,154` (published `_index/phantom_audit_latest.json`, 2026-07-14, **6 days stale**)                                             | S3↔S1      | read published triage (not re-run)              | NO             | dominated by cross-lane `trades` 561,048 + `odds_horizon_bucket` 143,594; **includes PROVEN false positives** (WEATHER 106, F2) → treat as ceiling, not truth. **Operator-notify.**            |
| F2  | `drift_axis_false_positive`                                 | HIGH (against tool)                     | UAC `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]=PER_DAY_BARE` but writer emits **PER_DAY_PER_LEAGUE** (`entity=weather/league={L}/weather.parquet`)                                 | S1 vs SSOT | `candidate_parquet_paths` vs disk (3-day proof) | NO             | dispatcher cannot find captured WEATHER → false phantom. **Cross-repo** (UAC layout table + IS writer). estate findings SUPPRESSED, tool fixed.                                                |
| F3  | `non_canonical_path` (data_type/entity axis)                | HIGH                                    | `data_type=FIXTURES` umbrella — writer STILL emitting (**333,697 rows, last_written 2026-07-20 18:01 = TODAY**), **zero** FIXTURES_SCHEDULE/FIXTURES_OUTCOMES               | S1+S3      | manifest census + disk (bare `entity=fixtures`) | NO             | 2026-05-23 split never reached the writer (H2). Oracle can't see it (§2). **instruments-service plan (§4c), not fixed here.**                                                                  |
| F4  | cross-AG bleed (taxonomy-gap → escalated)                   | HIGH                                    | `instruments-store-sports` manifest holds **6,597 `asset_group=prediction`** (KALSHI 6,562 / POLYMARKET 35) + 1 cefi + 1 defi rows                                          | S3         | scoped manifest read (`asset_group`)            | NO             | **grown from 4,097** (ref sheet); dates 2026-07-16→19, `written_at` up to 2026-07-20 13:10 = **active**. Root cause unlocated. **Operator-notify (cross-AG).**                                 |
| F5  | `manifest_only` (cross-lane misattribution)                 | HIGH                                    | `instruments-store-sports` manifest carries `trades` 568,728 + `odds_horizon_bucket` 354,255 — data_types owned by the **market-data-tick** raw-tick / MDPS-processed lanes | S3↔S1      | manifest census + phantom triage venues         | NO             | these are the F1 phantom mass (venues BETONLINEAG/ODDS_API, dates back to 2020); parquet lives in another bucket/lane. Structural.                                                             |
| F6  | AE-1 boundary NOTE                                          | MEDIUM                                  | 18 of the 13,903 blank-`pipeline_mode`+`source` rows carry `attempted_at` on **2026-07-08 00:00–01:30 UTC**                                                                 | S3         | blank-gate + attempted_at date                  | NO             | AE-1 exit trigger is `attempted_at >= 2026-07-08`; these 18 sit exactly on the boundary. Max attempted_at = 2026-07-08 01:30 (12 days stale) → live gap **NOT** reopened. Suppressed, flagged. |
| F7  | `manifest_infra` (consolidator locked)                      | MEDIUM                                  | `instruments-store-sports` `_index/consolidator.lock` present; `latest.json` `error_reason="locked"`, `no_op=true` (2026-07-20 19:08)                                       | S3         | JSON read                                       | NO             | live index (19:03) may not reflect latest per-VM shards. market-data-tick consolidator is **healthy** (empty no-op, not locked).                                                               |
| F8  | `non_data` (class C2)                                       | INFO                                    | `market-data-tick-sports-prd/scripts/` + `_legacy_migrated_scripts/` — executable Python in a DATA bucket (inventory row 4)                                                 | S1         | top-level ls                                    | **NO. Never.** | class-C2: "kept, labelled, NEVER deleted". Still must confirm no live VM bootstrap references (outside grep corpus).                                                                           |
| F9  | `manifest_only` / catalogue NOTE                            | LOW                                     | S4 `prod/catalog.parquet` (164,771 rows) has `data_type` column **100% NULL**; `instrument_type` is lowercase vocab (`fixture`/`player`/`team`/`league`)                    | S4         | catalogue read                                  | NO             | catalogue's own per-instrument grain; distinct vocabulary from the manifest — display-only for sports (no id grammar).                                                                         |
| F10 | `non_canonical_path` (domain-root) → no-still-authoritative | LOW                                     | `market-data-tick-sports-prd/processed/` (not `processed_candles/`) + half-applied `_legacy_migrated_processed/` (both `by_date/` + `processed/`) (inv row 13)              | S1         | top-level ls                                    | NO             | **DO-NOT-DELETE** — live MDPS sports odds-horizon lane writes here.                                                                                                                            |

**Catalogue-freshness (§3c obligation, once per run):** `data-catalogue.instruments-service.yaml` `shard_status`
staleness (`last_updated: 2026-02-06`, `auto_refreshed: null`) is a standing known condition. **UNVERIFIED this run** —
that file is a deployment-api artifact outside the three prod buckets; carried from skill §3c / reference sheet, not
re-read here.

## 5. Delete suggestions (SUGGESTIONS ONLY — all prod-bucket deletes human-only)

**No delete is authorized. Sports has zero delete-eligible candidates that clear the five-part proof.** Enumerated:

- **Legacy flat-named buckets** (`instruments-store-sports-central-element-323112`,
  `market-data-tick-sports-central-element-323112`) — already **404** (Phase 0). Nothing to delete; already-resolved.
- **`scripts/` + `_legacy_migrated_scripts/` (F8)** — `non_data` class C2 → **NEVER delete** (independent of any proof).
- **`processed/` (F10)** — `no-still-authoritative` (live MDPS lane). Never delete.
- **H5 market-data-tick legacy generational data** — **DO-NOT-DELETE.** Per reference sheet H5, the market-data-tick
  canonical estate is **NET POORER than legacy by 6,721,872 rows** (6,372,806 genuine legacy-only pre-match quotes in
  2022-03-07 → 2023-04-30, where canonical holds only 7.8%). A uniform "delete legacy" verdict destroys 6.37M rows. This
  run did **not** re-measure the 6.72M figure (would require a corpus walk) — carried from the reference sheet as a
  hard-stop hazard. Any delete here must be scoped per bucket AND per date window AND carry the five-part proof.

```
Location:            (no delete candidate cleared eligibility this run)
Disposition:         n/a — legacy buckets already 404; scripts/=non_data C2; processed/=no-still-authoritative; H5 legacy=DO-NOT-DELETE
Hard stop:           prod-bucket (all); legacy-after-copy (H5 generational data)
```

## 6. Suppressed accepted-exceptions (suppression is mandatory — counts, not re-listed)

| AE                  | condition                                                                               | suppressed occurrences in this run                                                                                                          |
| ------------------- | --------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **AE-1**            | sports IS rows with blank `pipeline_mode` **and** blank `source` (BLK-d48acae4, dec. A) | **13,903** (BELOW the 19,274 baseline — count decreased, consistent with partial backfill). See F6 for the 18 boundary rows. Not re-listed. |
| AE-2/AE-3/AE-4/AE-5 | tradfi/defi exceptions                                                                  | **0** (out of sports scope)                                                                                                                 |

AE-1 exit conditions checked: count 13,903 **< 19,274** (not exceeded); `attempted_at` max = 2026-07-08 01:30:57 UTC,
nothing fresh since (12 days) → the live write-path gap has **not** reopened. Suppressed. (The 18 rows exactly on the
`>= 2026-07-08` boundary are flagged as F6, not a fresh finding.)

## 7. REFUSED / open axes (unruled — no finding, no migration proposed)

- **[C2a] manifest `instrument_type` COLUMN casing** — **REFUSED.** Sports barely uses `instrument_type` as an axis:
  4,444,492 NULL + 562,102 `odds` (lower) + 364,665 blank + 16 `SPORT` (upper) + 9 `football` (lower). Compared
  case-insensitively; no casing migration proposed (both sides cite the same operator/date; >12M-row blast radius).
- **[decision D] defi market/event `LENDING` keying** — **N/A to sports** (defi-only axis). Stated for completeness.
- **[sports K2 data_type casing] — OPEN DECISION, reported not resolved.** Sports `data_type` UPPER is RULED
  (K0-DECISION b) but **K1 (the live-writer fix) is NOT shipped** (cutover register §6), so lowercase `data_type` is the
  **expected current writer output = `migration_pending`, NOT a regression**. Measured: `trades`=1,806,553 (91.5% of the
  market-data-tick bucket, matches reference sheet H6 exactly) plus `odds`/`odds_horizon_bucket`/`odds_movement`/etc all
  lowercase. **Whether `trades` migrates with the odds family under K2 is NOT recorded as decided** — reported as an
  open decision, no side picked (per SKILL §3e).

## 8. Coverage gap section (what was NOT reached + why)

1. **Orphans: `NOT ASSESSED`** — orphan enumeration requires the route-3 whole-corpus walk (`migration_orphan_sweep.py`
   / `_sports` variant), **not run** (single-walk discipline). Per `orphan-object-detection.md` §3 the honest verdict is
   `NOT ASSESSED`, never `0 orphans`.
2. **Temporal (disk)**: four-surface disk probes on `day=2026-07-10` (+ multi-day WEATHER/ODDS). The manifest 4-state
   census IS whole-index for both buckets, but S1/S2 disk verification was sampled.
3. **S2 content**: verified via object existence + `parquet_row_count` (from the phantom triage). No column-level /
   4-pillar schema read.
4. **market-data-tick raw-tick lane**: 4-state census + oracle structure check done; S1 disk spot-check limited to
   top-level + one day.
5. **features-sports bucket**: top-level reachability only; `sports_features/` content not reconciled.
6. **H5 6.72M-row generational comparison**: carried from reference sheet, **NOT re-measured** (needs a corpus walk).
7. **`data-catalogue.instruments-service.yaml`** staleness: UNVERIFIED this run (deployment-api artifact, out of bucket
   scope).

### Coverage numbers (formula named, LOWER BOUND)

- **Raw-tick lane** (`market-data-tick-sports-prd`, sports-scoped, whole index):
  `reachable = 592,835 / (592,835 + 112,277 + 0) = 84.08%` — `empty_confirmed=1,269,567` EXCLUDED,
  `expected_unattempted=0`.
- **Reference lane** (`instruments-store-sports-prd`, sports-scoped, whole index):
  `reachable = 1,705,641 / (1,705,641 + 637 + 220,190) = 88.54%` — `empty_confirmed=3,444,816` EXCLUDED.

Both are **LOWER BOUNDS** (`instrument_gates_download=true`). These are honest reachable-coverage over the full manifest
4-state per lane (not a day sample). NOTE F1: the reference lane's `captured` count is inflated by the cross-lane
`trades`/`odds_horizon_bucket` rows (F5) and depressed-in-truth by the 721,154 phantom ceiling (F1) — so the real
reachable coverage is bounded but not pinned by this figure.

## 9. Inventory reconcile (register ⇄ reality, sports-scoped)

| inv row | location                                                                 | register disposition              | this run                                                                                                                                                                  |
| ------- | ------------------------------------------------------------------------ | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1       | legacy flat-named sports buckets                                         | yes-twin-confirmed (already gone) | **CONFIRMED 404** both (`exists=False`) — already deleted, no suggestion                                                                                                  |
| 4       | `market-data-tick-sports-prd/scripts/` + `_legacy_migrated_scripts/`     | yes-after-verify                  | **CONFIRMED present** (top-level). Reader (VM bootstrap) UNKNOWN — outside grep corpus. → F8 `non_data`                                                                   |
| 13      | `market-data-tick-sports-prd/processed/` + `_legacy_migrated_processed/` | no-migrate-first                  | **CONFIRMED** — `processed/` present, NO `processed_candles/`; `_legacy_migrated_processed/` has both `by_date/` + `processed/`. Live lane → no-still-authoritative (F10) |
| 16      | `instrument_availability/…/instruments.parquet` flat                     | no-still-authoritative            | **CONFIRMED present** (top-level `instrument_availability/` + `availability_index/` both exist); content not deep-probed                                                  |

**Reality→register (new, to be appended by the register's maintenance contract — NOT done in this read-only run):**

- **F2** — UAC `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` PER_DAY_BARE vs writer PER_DAY_PER_LEAGUE (new drift_axis).
- **F4** — cross-AG prediction bleed grown 4,097 → 6,597 in `instruments-store-sports` (register carries the count;
  update it, and the dates 2026-07-16→19 / active `written_at` 2026-07-20).
- **F5** — cross-lane `trades`/`odds_horizon_bucket` manifest rows in `instruments-store-sports` (721k-phantom root).

## 10. Verdict

Sports is **pass-with-findings**. The raw-tick lane is structurally canonical (oracle-clean) where the oracle applies;
the reference lane is dispatcher-canonical for the entities probed once the correct probe vocabulary (`pipeline_mode=`
interposition + `fetched_at_hour=` wildcard) is used — the first probe pass produced four false absences, a live
demonstration of the probe-vocabulary rule. Real, bounded defects: a UAC↔writer WEATHER layout drift that manufactures
false phantoms (F2), the still-live FIXTURES umbrella writer with zero SCHEDULE/OUTCOMES (F3), an **active and growing**
cross-AG prediction bleed (F4), cross-lane manifest misattribution driving most of the 721,154-phantom ceiling (F1/F5),
and a locked instruments-store consolidator (F7). The published phantom count is a stale MEDIUM-confidence ceiling with
proven false positives inside it — **not** a confirmed estate defect count. No delete is authorized (legacy buckets
already 404; `scripts/`=non_data; `processed/`=live; H5 generational legacy=DO-NOT-DELETE). AE-1 suppressed (13,903 <
19,274). C2a REFUSED; sports K2 casing is `migration_pending` with an open trades-scope decision.

**Big findings notified to operator (data-correctness / cross-repo):** F2 (WEATHER UAC↔writer drift), F3 (live FIXTURES
umbrella regression), F4 (growing cross-AG bleed), F1/F5 (721k phantom ceiling = cross-lane misattribution).
