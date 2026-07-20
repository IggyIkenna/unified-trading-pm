# reference-sports — per-AG expansion for `/data-pipeline-reconciliation --asset-group sports`

Expansion of the `sports` row in [`SKILL.md`](SKILL.md) § 3d. Pointers + hazards only — the durable rules live in codex.

> ⚠️ **sports is the STRUCTURAL EXCEPTION. There is no `asset_group=` hive key anywhere in the reference tree.** A
> generic pass flags the entire estate as non-canonical. Read H1 before probing anything.

## Path grammar (this AG) — reference layer

```
sports_reference/by_date/day={D}/pipeline_mode={mode}_{source}/entity={E}/league={L}/{E}.parquet
```

**No `asset_group=` key.** Four layouts coexist:

| Layout               | Shape                                                             |
| -------------------- | ----------------------------------------------------------------- |
| `PER_DAY_PER_LEAGUE` | the default, above                                                |
| `PER_DAY_PER_SEASON` | `…/entity={E}/league={L}/season={S}/…`                            |
| `PER_DAY_BARE`       | `…/entity={E}/` with no `league=`                                 |
| `FLAT`               | `sports_reference/{E}/{E}.parquet` — **no date partition at all** |

Example:
`sports_reference/by_date/day=2026-07-01/pipeline_mode=batch_footystats/entity=footystats_odds/league=EPL/footystats_odds.parquet`

## Path grammar — raw tick layer

Shard atom `(asset_group=sports, source, data_type, league, day)` with `fixture_id` as a **ROW column**, not a path
segment. Post-canonicalisation, `source` becomes a **COLUMN** and `pipeline_mode=` is added to the path.

**`data_type` is UPPER for sports ONLY** — operator K0-DECISION (b), 2026-07-18. Every other AG lowercases it. A
case-normalising generic comparison inverts the verdict here.

## Buckets — resolve, never hand-build

`resolve_bucket_name(cloud, kind, asset_group="sports", deployment_env="prd")`:

| Layer     | `kind`                                                                        | Resolves to                          |
| --------- | ----------------------------------------------------------------------------- | ------------------------------------ |
| raw tick  | `market-data` (or alias `tick-data`)                                          | `market-data-tick-sports-prd-{pid}`  |
| reference | `instruments-store`                                                           | `instruments-store-sports-prd-{pid}` |
| features  | `features-sports` — **its own flat yaml key**, NOT the per-AG `features` dict | `features-sports-prd-{pid}`          |

Verified at `unified-trading-pm/configs/cloud-providers.yaml:93-102` (`market-data` / `instruments-store` carry a
`SPORTS` key) and `:81` (`features-sports` as a standalone key). Note the `features` per-AG dict at `:59-63` has **no**
`SPORTS` entry — passing `kind="features", asset_group="sports"` will not resolve. Use `kind="features-sports"`.

**Layout quirk:** `market-data-tick-sports-prd-{pid}` uses `processed/`, not `processed_candles/` like the other AGs.

**Legacy flat-named buckets** `instruments-store-sports-central-element-323112` and
`market-data-tick-sports-central-element-323112` are delete targets, but a live probe returns **404 for both** — already
deleted on GCP. Do not emit a delete suggestion for them; record as already-resolved.

## Shard atom + (KEY)

Reference layer: `[pipeline_mode, day, entity, league[, season], source]`. Raw tick:
`[asset_group=sports, source, data_type, league, day]`. Neither uses `instrument_id` as the key — sports does not fit
the three (KEY) grain patterns cleanly, which is exactly why a generic loop mis-keys it.

## Instrument-id grammar

Sports has no venue-composed instrument id in the cefi/tradfi/defi sense. Identity is carried by
`(entity, league[, season], day)` on the reference side and by the `fixture_id` **row column** on the raw-tick side.
**Do not synthesize a `VENUE:TYPE:SYMBOL` id for sports** — there is no such grammar to compare against.

## Catalogue (surface 4) — TWO different artifacts, don't conflate them

1. `instruments-store-sports-prd-{pid}/prod/catalog.parquet` — the sports-fixture block in `CATALOG_COLUMNS`.
2. `data-catalogue.instruments-service.yaml` `shard_status` — a **different** artifact: the live genesis map read by
   deployment-api `reference_scope.py`. `last_updated: 2026-02-06`, `auto_refreshed: null`. Per `SKILL.md` § 3c, report
   that staleness as a **catalogue-freshness** finding **once per run**, not once per shard.

## HAZARDS

### H1 — `entity=` is NEVER a `data_type`, and the names are non-obvious (HARD RULE)

The `entity=` folder name is a source-shaped label, not a semantic data_type. Mapping one to the other silently
mis-classifies the whole tree:

| Semantic data_type | Actual `entity=` folder         |
| ------------------ | ------------------------------- |
| `ODDS`             | `entity=footystats_odds`        |
| `PREDICTIONS`      | `entity=footystats_predictions` |
| `FIXTURE_STATS`    | `entity=fixture_stats`          |
| `XG`               | `entity=understat_xg`           |
| `PLAYER_VALUES`    | `entity=player_values`          |
| `WEATHER`          | `entity=weather`                |

> **Folder-map SSOT = `unified_api_contracts/canonical/domain/sports/gcs_paths.py::SPORTS_DATA_TYPE_TO_FOLDER` — READ
> it, do not trust example folder names verbatim.** The prior version of this table was wrong on all three examples
> (`ODDS_SNAPSHOT`→ there is no such key, it is `ODDS`; `FIXTURE_STATS`→`fixture_stats` not `fixture_statistics`;
> `WEATHER`→`weather` not `open_meteo_forecasts`) — verified against the SSOT 2026-07-20. Probing a wrong folder is the
> exact false-absence this hazard warns against.

`entity=fixtures` is **FROZEN**, split into `fixtures_schedule` + `fixtures_outcomes` (2026-05-23) — see H2 for why that
split is a live divergence.

### H2 — LIVE manifest-atom mismatch: the 2026-05-23 fixtures split never reached the writer

The fixtures writer still emits the hardcoded umbrella `data_type="FIXTURES"` — **333,697 rows, last written
2026-07-20T18:01Z** (re-measured; still active today) — with **ZERO** `FIXTURES_SCHEDULE` / `FIXTURES_OUTCOMES` rows.
This is an active writer defect, not historical residue. Report it; do not fix it here (it belongs to that service's
plan — `SKILL.md` § 4c).

> Note: the UAC `gcs_paths.py::SPORTS_DATA_TYPE_TO_FOLDER` code comment (`:40-46`) asserts the writer "cut FIXTURES
> over" on 2026-07-14 with "zero `fixtures` objects" — that comment is **stale/aspirational**; the measured writer never
> cut over. `canonical-cutover-register.md` § 6 (which records this as a live regression) is correct; the UAC docstring
> is not. Flagged doc-vs-reality contradiction for the orchestrator.

### H3 — ACCEPTED EXCEPTION: 19,274 pre-2026-07-08 rows with blank `pipeline_mode` + `source`

Operator-accepted as **permanently untyped** — **BLK-d48acae4, decision A**. These are `instruments-store-sports` rows
predating 2026-07-08. A cleanliness gate must treat them as a **known exception, not a fresh finding**. Suppress with a
count + pointer per `SKILL.md` § 5; re-reporting them destroys the report's signal.

> The **19,274** is a baseline ceiling — the count can only DECREASE under the exit rule. Measured **13,903 on
> 2026-07-20** (≤ baseline, no alarm). Also: the AE-1 exit trigger `attempted_at >= 2026-07-08` is imprecise — the
> migration's own tail writes land 2026-07-08 00:00–01:30 UTC and trip a false "exception broken" alarm on ~18 boundary
> rows; gate on `> 2026-07-08T02:00Z` (or a fresh `written_at`), not the bare partition boundary. Boundary-wording is a
> flagged codex fix for the taxonomy/register.

### H4 — cross-AG bleed INTO this bucket

**4,097 `asset_group="prediction"` rows** (plus 2 cefi/defi) are physically in the **sports** bucket manifest, dates
2026-06-26 → 2026-07-18. Root cause **unlocated** as of 2026-07-20. A sports-scoped manifest read will pick them up —
filter by `asset_group` explicitly and report the count. Cross-link [`reference-prediction.md`](reference-prediction.md)
H5.

### H5 — legacy and canonical are TWO INDEPENDENT CAPTURE GENERATIONS. The delete decision is BUCKET-DEPENDENT.

No migration ever transformed legacy rows — `migrate_sports_canonical_v9.py` is a **byte-identical copy**. So:

| Bucket            | Which generation is richer                                                                                                                                                                             |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| instruments-store | **canonical is RICHER**                                                                                                                                                                                |
| market-data-tick  | **canonical is NET POORER by 6,721,872 rows** — 6,372,806 (89.5%) are genuine legacy-only pre-match quotes confined to 2022-03-07 → 2023-04-30, a window where canonical holds only **7.8%** of legacy |

**A uniform "delete legacy" verdict destroys 6.37M rows of pre-match quotes.** Any delete suggestion must be scoped per
bucket **and** per date window, and still carries the five-part proof (`SKILL.md` § 4b). Legacy bucket cutover is 45/49
done.

### H6 — K2 casing migration: scope corrected, and the decision is NOT recorded as made

~1.83M lower-case `data_type` rows await K2. The **dominant** one is `trades` = **1,806,553 rows (91.5% of the
bucket)**, **not** the ~20k odds family as earlier scoped. Whether `trades` migrates with the odds family is **not
recorded as decided**. K1 (the live writer fix) must ship before K2. Report the open decision; do not pick a side
(`SKILL.md` § 3e).

### H7 — the sports shard path is hand-rolled with no guard and no UAC builder

MTDS `_build_sports_shard_path` is a hand-rolled f-string with **no canonical guard** and **no UAC builder** behind it.
Combined with the tradfi-only write-time guard
(`market-tick-data-service/market_tick_data_service/engine/orchestrator/partitioned_writer.py:258-259`), sports path
regressions fail entirely silent.

### H8 — four parallel reference layouts + executable code in a data bucket

- `instruments-store-sports` carries **four** coexisting reference layouts: `sports_reference/`, `sports_reference_v2/`,
  `legacy_football/`, and `availability_index/` vs `instrument_availability/`. Enumerate all four before declaring a
  location absent.
- Executable Python (`fetch_missing_odds.py`, `oddspapi_*.py`) lives at `market-data-tick-sports-prd/scripts/` — **code
  in a data bucket**. Report as a finding; it is neither canonical data nor an orphan object in the usual sense.
- Also open: T2.9 MDT schema drift, T2.10 47,253 phantom rows, and the RED `source=` write-wiring gap.

### H9 — `pipeline_mode=` interposition + `fetched_at_hour=` wildcard (the #1 sports false-absence generator)

The canonical reference layout interposes `pipeline_mode={mode}` **between** `day=` and `entity=`:
`…/day={D}/pipeline_mode={m}/entity={E}/…`. `candidate_parquet_paths(...)` **defaults `pipeline_mode=None`**, which
emits the PRE-cutover paths and **MISSES all post-cutover data** — ALWAYS pass the manifest row's `pipeline_mode`. This
exact slip produced FOUR false absences in the 2026-07-20 run.

- **`entity=fixtures` is the exception** — the FIXTURES umbrella (H2) still writes at the **bare** `entity=fixtures/`
  path with NO `pipeline_mode=` segment, so a single generic pass mis-handles it either way. Probe fixtures bare and
  everything else under `pipeline_mode=`.
- **`footystats_odds` / `footystats_predictions` add a `fetched_at_hour=*` sub-partition.** `candidate_parquet_paths`
  emits a literal `fetched_at_hour=*` string that `blob.exists()` **cannot** expand — you MUST **prefix-list** those,
  not call `exists()` on the wildcard.

### H10 — WEATHER layout drift: UAC says `PER_DAY_BARE`, the writer emits `PER_DAY_PER_LEAGUE` (drift_axis_false_positive)

`SPORTS_DATA_TYPE_LAYOUT["WEATHER"] = PER_DAY_BARE` (`gcs_paths.py:139`), but the writer emits
`entity=weather/league={L}/weather.parquet` (PER_DAY_PER_LEAGUE) — verified across 3 days 2026-07-20. So
`candidate_parquet_paths` **false-absents every captured WEATHER shard** and the phantom auditor manufactures phantoms
for it. Report as `drift_axis_false_positive`; the cross-repo fix is the UAC layout table or the IS writer (do not fix
here). Precedent: the PLAYER_VALUES layout had the identical drift (see the `gcs_paths.py:70-79` comment) and was
realigned to the writer's truth — WEATHER is the same class, unfixed.

## Known-good spot-check — run BEFORE trusting any absence result

**Sports has its own dispatcher — `canonical_path_templates` will hand you an EMPTY LIST and that is correct.**

```python
if ag == SPORTS:
    return []
```

— `unified-api-contracts/unified_api_contracts/registry/possible_manifest.py:372-373`. Its docstring is explicit: sports
is "intentionally template-less here — it has its own UAC SSOT (`unified_api_contracts.sports.candidate_parquet_paths`);
a sports consumer dispatches there. Returned as an empty list for `sports` so a caller treats it as 'use the sports
dispatcher', never 'no paths'."

**An empty list is a routing instruction, not zero coverage.** Treating it as "no canonical paths exist" is the sports
equivalent of the defi `solana_amm_pool` false negative.

1. Dispatch to `candidate_parquet_paths(...)` —
   `unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py:173`.
2. **Iterate the FULL returned list.** Its docstring warns: "Callers MUST iterate the full list — early-return on
   `cands[0]` only is wrong for layouts that emit multiple plausible paths (PER_DAY_PER_SEASON probes 3 seasons)"
   (`:186-188`). Early-return is how you manufacture a false absence across three of the four layouts.
3. Confirm your `entity=` value is the **actual folder name** from `SPORTS_DATA_TYPE_TO_FOLDER`, not the semantic
   data_type (H1). Probing `entity=ODDS` returns zero; the folder is `entity=footystats_odds`. Also pass the row's
   `pipeline_mode=` (H9) and, for `footystats_*`, prefix-list the `fetched_at_hour=*` sub-partition.
4. Confirm you are comparing `data_type` in **UPPER** case for sports (K0-DECISION (b)).
5. Pick one `(day, entity, league)` known-captured from the manifest and confirm your probe returns non-zero.
6. Only then treat a zero as a finding.

## Cross-links

`SKILL.md` · [`reference-prediction.md`](reference-prediction.md) (H4 bleed) ·
`codex/02-data/four-surface-reconciliation-procedure.md` · `codex/02-data/reconciliation-finding-taxonomy.md` ·
`codex/02-data/canonical-cutover-register.md` · `codex/02-data/non-canonical-path-inventory.md` ·
`codex/02-data/gcs-and-manifest-delete-safety-protocol.md` · `codex/02-data/orphan-object-detection.md` ·
`codex/02-data/service-shard-status-catalogue.md` · `codex/05-infrastructure/bucket-isolation-model.md`
