---
doc_type: audit-result
title: "Data-pipeline reconciliation — tradfi (2026-07-20)"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=tradfi over PROD buckets only (read-only). Representative
  sample: full 5.2M-row manifest census + full 1.39M-row catalogue census + Databento-lane four-surface probe on
  day=2026-07-01 (CME chains/combo/options) + legacy-shape probes. All three prod buckets reachable; oracle behaves as
  documented (structure + tradfi single-stem). KEY REFUTATION of reference-tradfi.md: catalogue is ~92% canonical
  id-form and manifest ~81% structured — NOT the "0 canonical" the reference sheet asserts (catalogue rebuilt
  2026-07-20). Genuine residue: legacy hyphen/massive trees, quote/margin manifest-column population gap on chains, H4
  garbage-underlying quarantine, mixed instrument_type casing. batch_massive = human-only purge (suppressed). C2a +
  parked B1/B2/B4 REFUSED. No delete authorized.
status: partial
nature: record
asset_group: [tradfi]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, four-surface, tradfi, delete-safety, non-canonical-paths, manifest, databento]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
    tradfi-databento-sourcing-ssot,
    tradfi_canonical_path_migration_design_2026_07_19,
  ]
created: 2026-07-20
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=tradfi, PROD (-prd-) buckets only, read-only; sample = full manifest+catalogue census + day=2026-07-01
  Databento four-surface + legacy-shape probes"
date: 2026-07-20
auditor: /data-pipeline-reconciliation (first tradfi execution + acceptance test)
parent_epic: infrastructure_master
severity: P1
skill: data-pipeline-reconciliation
run_date: 2026-07-20
generated_at: 2026-07-20T19:00:00+00:00
---

# Data-pipeline reconciliation — tradfi (2026-07-20)

**Read-only.** No GCS writes, no manifest writes, no deletes, no backfills, no VM launches, no `--apply`. Deletes below
are SUGGESTIONS only; every prod-bucket delete and the `batch_massive` purge are human-only hard stops.

## 0. Declared sample scope (honest partial pass)

This is **not** a full-corpus object walk (the reference sheet's H5 census of 2,734,646 objects across 95 legacy shapes
is not re-enumerated — single-walk discipline). It IS a full **manifest** census (5,209,585 rows) and a full
**catalogue** census (1,391,725 rows), plus a targeted four-surface probe of the live Databento lane and each legacy
shape named in the reference sheet.

**Sampled (what each surface was read from):**

1. **S3 manifest** — the entire `_index/availability_index.parquet` (5,209,585 rows): 4-state census, casing census,
   pipeline_mode/source/venue/instrument_type/data_type distributions, and the day=2026-07-01 CME shard rows.
2. **S4 catalogue** — the entire `prod/catalog.parquet` (1,391,725 rows): id-form measurement against the canonical
   grammar, plus the deployment-api reference-scope leg (known-stale, reported once).
3. **S1 path** — Databento lane `day=2026-07-01/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME`
   (futures_chain, combo, options_chain leaf tails) via prefix-scoped + delimited listing; the legacy hyphen tree
   `by_date/day-2026-01-01/`; one `batch_massive` object under `day=2024-01-02`; the machine oracle on 8 real/derived
   paths at both `require_pipeline_mode` settings.
4. **S2 content** — the `underlying=COPPER` futures_chain bundle parquet (2,107 rows, 15 contracts) — content columns
   read directly.
5. Manifest status JSONs (`latest.json`, `phantom_audit_latest.json`, `consolidator_stall_state.json`,
   `reprobe_audit_latest.json`); expected-universe (`expected_universe_ranges.parquet`, 58,434 rows); non-recursive
   top-level sweep of all three tradfi prod buckets.

**NOT sampled (declared gaps, see §8):** the ~2,040 other days' object-level four-surface content; S2 content of every
non-COPPER shard; a whole-corpus orphan walk (route-3, **not run** — orphans therefore `NOT ASSESSED` per
`orphan-object-detection.md` §3); the physical object counts behind the H5 disposition map (inherited, not re-measured).

## 1. Bucket paths table (auto-derived from the resolver + probes)

Every bucket resolved via `resolve_bucket_name(cloud="gcp", kind=<k>, asset_group="tradfi", deployment_env="prd")` over
`configs/cloud-providers.yaml` (project `central-element-323112`; tier passed explicitly via `deployment_env=`, never
env-mutated). No `-test-` name resolved (asserted in code). Auth: `unified-trading-sa@…` ADC.

| Surface / layer          | `kind`                    | Resolved bucket                                       | Reachable?         | Read targeted                                                                   |
| ------------------------ | ------------------------- | ----------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------- |
| raw tick (S1/S2)         | `market-data`             | `market-data-tick-tradfi-prd-central-element-323112`  | YES (top-level=11) | `raw_tick_data/` day/pm/venue/it/dt tails; legacy `day-`/`batch_massive` probes |
| raw tick alias           | `tick-data`               | `market-data-tick-tradfi-prd-central-element-323112`  | YES (same bucket)  | —                                                                               |
| manifest (S3)            | (same market-data bucket) | `market-data-tick-tradfi-prd-central-element-323112`  | YES                | `_index/availability_index.parquet` (74.5 MiB, 5,209,585 rows) + 4 status JSONs |
| reference/catalogue (S4) | `instruments-store`       | `instruments-store-tradfi-prd-central-element-323112` | YES (top-level=5)  | `prod/catalog.parquet` (18.9 MiB, 1,391,725 rows)                               |
| features                 | `features`                | `features-tradfi-prd-central-element-323112`          | YES (top-level=1)  | top-level only — **only `_index/` exists; no computed tradfi features on disk** |

**Negative resolver checks (defence against fragment-as-kind):** `market-data-tick-tradfi`, `dex-pools`, `lst-rates` all
correctly **RAISE `BucketNamingError`** — they are bucket-name fragments, not yaml keys. **No bucket was unreachable.**
tradfi instruments-store has **NO `prd/` short-form shadow** (inventory row 2 is defi+pred only, not tradfi — CONFIRMED
here).

## 2. Machine oracle behaviour (structure + tradfi single-stem; probed vocabulary enumerated, not assumed)

`canonical_path_violations()` is the sole authority. Probe vocabulary enumerated from
`canonical_path_templates("tradfi")` (**10 templates** returned; `pipeline_mode=batch_massive` prefix CONFIRMED present
— reference-sheet H2 spot-check step 2 passes, so no false-flag of Massive objects) and from the live writer's emitted
`data_type` values (`ohlcv_1m`/`ohlcv_1s`, **not** `trades` — the assumed `data_type=trades` returned zero; corrected by
enumeration before treating the zero as a finding). Unlike cefi/defi, tradfi **does** have a filename-stem oracle clause
(clause 8, tradfi-gated), so surface-A id-form is **partially machine-checked** for single-instrument shards.

| Path (real / derived)                                                 | rpm=False        | rpm=True           | Verdict                                              |
| --------------------------------------------------------------------- | ---------------- | ------------------ | ---------------------------------------------------- |
| futures_chain COPPER `…/quote=USD/margin=linear/ticks.parquet` (real) | CANONICAL        | CANONICAL          | structure + chain tail OK                            |
| combo COPPER **+quote/margin tail** (real, day=2026-07-01)            | CANONICAL        | CANONICAL          | oracle tolerates combo with OR without the tail      |
| combo BARE `underlying=/ticks.parquet` (H3 doc-shape)                 | CANONICAL        | CANONICAL          | both accepted → H3 "bare only" is imprecise (see F8) |
| single EQUITY `NASDAQ:EQUITY:AAPL-USD.parquet`                        | CANONICAL        | CANONICAL          | stem-rule PASS (contains `:`)                        |
| single EQUITY `AAPL.parquet` (bare symbol)                            | stem violation   | stem violation     | `non_canonical_path` (id-form)                       |
| single EQUITY `ticks.parquet` (symbol-less fan-in)                    | stem violation   | stem violation     | `non_canonical_path` (id-form)                       |
| legacy HYPHEN `by_date/day-2026-01-01/data_type-tbbo/…` (real)        | 3 violations     | 4 violations (+pm) | `non_canonical_path` (F2)                            |
| `batch_massive/…` (real object present)                               | RAISED forbidden | RAISED forbidden   | **SUPPRESSED — AE-4** (human-only purge)             |

Cutover gate: tradfi `require_pipeline_mode` effective-from **2026-05-19** (cutover register §2); `chain tail`
effective-from **2026-07-19** (§4). The Databento lane sampled (day=2026-07-01, written after both) is a live-writer
lane and is held to `require_pipeline_mode=True` — it passes clean. Legacy hyphen/massive objects predate the guard and
are migration state, not live regressions (H1 — the tradfi write guard RAISES, so a canonical-lane regression cannot be
silently written).

## 3. Per-surface verdict per shard (four surfaces = four bits, never collapsed)

Legend: `OK` · `NON-CANON` · `PARTIAL` · `ABSENT` · `SUPPRESSED` (accepted exception) · `NOTE` · `NOT-READ` (outside
sample) · `REFUSED` (unruled axis).

| #   | shard atom                                                                        | S1 path                     | S2 content                                                                                     | S3 manifest                                                                                                                                          | S4 catalogue                           | notes                                                              |
| --- | --------------------------------------------------------------------------------- | --------------------------- | ---------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------------------------------ |
| 1   | `CME/futures_chain/ohlcv_1m/underlying=COPPER` (day=2026-07-01, batch_databento)  | **OK** (oracle canon, tail) | **OK** — `instrument_id=CME:FUTURE:COPPER@LIN-YYYYMMDD` (15 contracts), `symbol=HGF7` retained | **PARTIAL** — `captured`; `instrument_id`=null (OK, pattern-#2); **`quote_asset`/`margin_type` BLANK while path has `quote=USD/margin=linear`** (F3) | OK (COPPER futures canon in catalogue) | canonical bundle; only manifest quote/margin axis unpopulated      |
| 2   | `CME/combo/ohlcv_1m/underlying=COPPER` (day=2026-07-01)                           | **OK** (oracle canon)       | NOT-READ                                                                                       | `captured`; `it=COMBO` (UPPER); quote/margin blank                                                                                                   | OK (COMBO canon ids, B2 parked)        | combo written WITH quote/margin tail — see F8 + AE-2 adjacent (F9) |
| 3   | `CME/options_chain/ohlcv_1m` (day=2026-07-01)                                     | **OK**                      | NOT-READ                                                                                       | mixed `empty_confirmed`/`expected_unattempted`/`captured`; `it=options_chain` (lower)                                                                | OK (OPTION canon ids)                  | expected_unattempted for trades/tbbo (databento paired-schema)     |
| 4   | single EQUITY (e.g. `NASDAQ:EQUITY:NVDA-USD`)                                     | OK (stem rule) [derived]    | NOT-READ                                                                                       | **OK** — `instrument_id=NASDAQ:EQUITY:NVDA-USD` (canonical cash, -USD present)                                                                       | OK                                     | manifest id-form canonical for singles (refutes "0 canonical")     |
| 5   | legacy HYPHEN `day-2026-01-01/data_type-tbbo/` (real)                             | **NON-CANON** (3–4 viol.)   | NOT-READ                                                                                       | (not manifested at this shape — migration state)                                                                                                     | n/a                                    | `non_canonical_path` / `MIGRATE_HYPHEN`; date-bound legacy (F2)    |
| 6   | `batch_massive/…venue=CME/data_type=options_chain/6AH4_migrated_….parquet` (real) | **SUPPRESSED** (AE-4)       | NOT-READ                                                                                       | `batch_massive` = 686,005 rows (SUPPRESSED)                                                                                                          | n/a                                    | human-only purge; NOT flagged (F-suppressed)                       |
| 7   | H4 garbage-`underlying=` (`12`/`13`/`23`, `GN`/`VT`/`3W`)                         | (in `_quarantine/`)         | NOT-READ                                                                                       | present in manifest as underlying values (F5)                                                                                                        | n/a                                    | `quarantine` disposition — never canonicalize, never delete        |

## 4. Typed findings (taxonomy names only — diffable)

Formula for any coverage %: `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`,
`empty_confirmed` **EXCLUDED** (honest-coverage-model, CK3-certified). Every % is a **LOWER BOUND**
(`instrument_gates_download=true` for all AGs).

| #   | type                                                           | severity | shard / location                                                                                                                                                                                                                                                                                       | surfaces                  | detector                                                                   | delete_elig | notes                                                                                                                                                                            |
| --- | -------------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------- | -------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F1  | `phantom`                                                      | HIGH     | tradfi `phantom_count=1635` (published `_index/phantom_audit_latest.json`, generated 2026-07-14)                                                                                                                                                                                                       | S3↔S1                     | read published audit (not re-run)                                          | NO          | flip captured→attempted_failed remediation (not this skill); triage jsonl in `central-element-323112-phantom-triage`                                                             |
| F2  | `non_canonical_path`                                           | MEDIUM   | legacy hyphen tree `raw_tick_data/by_date/day-2026-01-01/data_type-tbbo/` (live, oracle-flagged 3–4 clauses); `MIGRATE_HYPHEN` 100,698 (inherited)                                                                                                                                                     | S1                        | `canonical_path_violations` (oracle-confirmed)                             | NO          | date-bound legacy migration state, not a live regression (H1 guard prevents new ones); disposition = `no-migrate-first` (inv row 11)                                             |
| F3  | manifest atom-axis gap (NOTE)                                  | MEDIUM   | chain rows carry `quote_asset=''`/`margin_type=''` while the **path** carries `quote=USD/margin=linear` (measured on CME COPPER)                                                                                                                                                                       | S1↔S3                     | scoped manifest read vs live S1 path                                       | NO          | shard-atom `quote·margin` axes unpopulated in manifest column for chains → S1/S3 atom keys diverge on those axes                                                                 |
| F4  | catalogue-freshness                                            | LOW      | deployment-api `data-catalogue.instruments-service.yaml` (`shard_status[…].start_date`) — SUPERSEDED schema; `data-catalogue.*.yaml` staleness is a standing known condition                                                                                                                           | S4                        | procedure §3c (`service-shard-status-catalogue.md`)                        | NO          | report ONCE (not per-shard); the `prod/catalog.parquet` leg itself is FRESH (2026-07-20)                                                                                         |
| F5  | `quarantine` (H4)                                              | LOW      | garbage `underlying=` in manifest: numeric Globex `12`(3,908)/`13`(3,706)/`23`(3,681) + CBOE opaque `GN`(3,913)/`VT`(3,911)/`3W`(3,760); `_quarantine/raw_tick_data/` tree present                                                                                                                     | S3, S1                    | scoped manifest read + top-level probe                                     | **NO**      | `QUARANTINE_GARBAGE_UL` (14,633 inherited) — no defensible canonical id; never fake-canonicalize, never delete                                                                   |
| F6  | expected-universe casing NOTE                                  | LOW      | `expected_universe_ranges.parquet` seeds `instrument_type` LOWERCASE (`equity`,`futures_chain`,`etf`) while captured rows are mixed UPPER/lower (`EQUITY`…)                                                                                                                                            | S3 (expected vs captured) | expected + index read                                                      | NO          | a C2a manifestation on the expected side; if the coverage join is case-sensitive it could seed unsatisfiable `expected_unattempted` — folded into C2a REFUSED (§7), not migrated |
| F7  | `manifest_only` (venue) NOTE                                   | LOW      | manifest carries `venue=BARCHART` (9,119) + `pipeline_mode=batch_barchart` (4,655) — retired vendor                                                                                                                                                                                                    | S3                        | manifest venue/pm dist                                                     | NO          | parked axis **B4** (§7) — reported, not migrated                                                                                                                                 |
| F8  | reference-sheet drift (NOTE)                                   | MEDIUM   | live combo emits the FULL `quote=/margin=/ticks.parquet` tail (day=2026-07-01), contradicting reference-tradfi.md H3 "combo keeps the **bare** `underlying=/ticks.parquet` fan-in"                                                                                                                     | S1                        | live S1 probe + oracle (both shapes canonical)                             | NO          | oracle accepts both; the reference sheet H3 wording is imprecise — see critique (b)/(e)                                                                                          |
| F9  | cross-repo writer/reader (AE-2 adjacent)                       | HIGH     | combo written underlying-partitioned (with quote/margin tail) but the MTDS reader probes combo as a single-instrument shard (`reader.py:62` excludes combo from the underlying-partition set)                                                                                                          | S1↔reader                 | inherited from taxonomy AE-2 ⚠; corroborated by live combo path shape here | NO          | **NOT absorbed into AE-2** — HIGH cross-repo finding; combo shards are written to a path the reader will not find (belongs to MTDS plan, not fixed here)                         |
| F10 | reference-sheet + catalogue REFUTATION (data-correctness NOTE) | MEDIUM   | reference-tradfi.md + cutover-register §4 assert tradfi "canonical on FILENAMES only … manifest measures 0 canonical … catalogue 0 of 1,111,322 rows canonical." **MEASURED 2026-07-20: catalogue 1,391,725 rows, ~92% space-free structured canonical ids; manifest ~81% of non-null ids structured** | S3, S4                    | full catalogue + full manifest census                                      | NO          | catalogue rebuilt 2026-07-20T01:05 (fresh); the "0 canonical" claim is STALE — surface 4 does NOT fail wholesale                                                                 |

## 5. Delete suggestions (SUGGESTIONS ONLY — all prod-bucket deletes human-only)

Only `legacy_duplicate` + `junk` are ever delete-eligible. **This run produced NO candidate above `unknown`.** The one
large tradfi delete class (`batch_massive`) is an enumerated human-only hard stop and is suppressed, not suggested:

```
Location:            gs://market-data-tick-tradfi-prd-.../raw_tick_data/by_date/day=*/pipeline_mode=batch_massive/...
Part 1 twin probe:   NOT EVALUATED (single-walk: no per-object twin enumeration this run)
Part 2 content:      NOT EVALUATED
Part 3 writers:      NONE-FOUND (routing removed uac@a2beed46 + mtds@362a487e) — grep, not proof
Part 4 readers:      YES — batch_massive PipelineMode + possible_manifest READ recognition deliberately KEPT
Part 5 twin coverage: <100% — 571 Massive-only shards have NO Databento twin yet (inherited)
Disposition:         unknown (AE-4 accepted exception; recognition kept until gated purge)
Hard stop:           batch_massive purge (HUMAN-ONLY) + prod-bucket
```

Legacy hyphen (F2) and quarantine (F5) are both `no-migrate-first` / `quarantine` — neither delete-eligible. No delete
is authorized by this run.

## 6. Suppressed accepted-exceptions (suppression is mandatory — counts, not re-listed)

| AE             | condition                                                                                   | suppressed occurrences in sample                                                                                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AE-4           | `batch_massive` read-recognition kept until gated purge (Massive source removed 2026-07-19) | **686,005 manifest rows** (`pipeline_mode=batch_massive`) + all objects under `…/pipeline_mode=batch_massive/` (≈1.5M inherited, not re-counted) — oracle RAISES on each; NOT reported as finding/orphan |
| AE-2           | tradfi `combo` bare-underlying carve-out (outside the full-id filename guard)               | all `combo` shards sampled (day=2026-07-01 CME + 63,319 catalogue COMBO rows) — bare tail NOT flagged `non_canonical_path` (⚠ the adjacent writer/reader defect is F9, HIGH, NOT suppressed)             |
| AE-1/AE-3/AE-5 | sports/defi exceptions                                                                      | 0 (out of tradfi scope)                                                                                                                                                                                  |

## 7. REFUSED axes (unruled / parked — no finding, no migration proposed)

- **[C2a] manifest `instrument_type` COLUMN casing** — **REFUSED**. Confirmed LIVE in tradfi: the column carries BOTH
  UPPER and lower simultaneously — `EQUITY` 1,685,476 vs `equity` 81,145; `FUTURE` 410,110 vs `future` 15,913; `ETF`
  223,915 vs `etf` 10,873; `COMBO` 1,480,449 vs `combo` 10,008; `INDEX` 407 vs `index` 188 (plus chain types
  `options_chain`/`futures_chain` only-lower, and `None` 511,564 / blank 85,350). Compared case-insensitively; **no
  casing migration proposed.** ⚠ **SSOT CONTRADICTION surfaced, not resolved:** the finding-taxonomy §5.1 and this
  task's constraints class C2a as UNRULED-REFUSE, while `canonical-cutover-register.md` §3c and
  `four-surface-reconciliation-procedure.md` §7 (O2) class it as **RULED UPPERCASE (D1, 2026-07-20)** and instruct
  ENFORCE. This run follows the taxonomy/task (REFUSE) and flags the contradiction (critique (c)).
- **[B1] etf vs equity** — parked; `etf` kept distinct (223,915 UPPER + 10,873 lower rows measured). Not resolved.
- **[B2] combo top-level id shape** — parked; 63,319 catalogue COMBO rows carry unsettled leg-id grammar
  (`ICE:COMBO:G FMX0020-G FMQ0025`, `CBOE:COMBO:VX/N5:1:S - VX/V5:1:B`). Not migrated.
- **[B4] retired-vendor barchart** — parked; `venue=BARCHART` 9,119 + `batch_barchart` pipeline_mode 4,655 + source
  `barchart` 4,655. Reported (F7), not migrated.

## 8. Coverage gap section (what was NOT reached + why)

1. **Orphans: `NOT ASSESSED`** — orphan enumeration requires the route-3 whole-corpus walk
   (`migration_orphan_sweep.py`), **not run** this pass (single-walk discipline). Per `orphan-object-detection.md` §3
   the honest verdict is `NOT ASSESSED`, never `0 orphans`.
2. **Object-level four-surface**: only day=2026-07-01 (Databento CME) probed to leaf + one legacy day + one massive
   object; the other ~2,040 days' objects were not listed. S3/S4 are full-census; S1/S2 are sampled.
3. **S2 content**: read for the COPPER futures_chain bundle only; every other shard's parquet content is `NOT-READ`.
4. **features-tradfi**: top-level reachability only — the bucket holds **only** `_index/` (no computed features on
   disk); nothing to reconcile at leaf grain.
5. **H5 disposition-map object counts** (2,734,646 objects / 95 shapes; PURGE_MASSIVE 1,696,166, MIGRATE_CHAIN_ADDQM
   528,961, etc.) are **inherited, not re-measured** — re-measuring is a walk this run must not open.
6. **`_needs_attribution/raw_tick_data/`, `_quarantine/raw_tick_data/`, `_migration_backup/`, `configs/patches/`,
   `databento-batch-registry/`** confirmed present at bucket top level (non-recursive) but their contents were not
   deep-probed.

### Coverage number (formula named, lower bound)

`reachable_coverage(tradfi, all-history manifest) = captured / (captured + attempted_failed + expected_unattempted)`
`= 1,616,450 / (1,616,450 + 307,049 + 388,874) = 1,616,450 / 2,312,373 = 69.90%`. `empty_confirmed = 2,897,212`
**EXCLUDED**. **LOWER BOUND** (`instrument_gates_download=true`). This is the corpus-wide manifest figure (5,209,585
rows), not a single-day sample.

## 9. Inventory reconcile (register ⇄ reality, tradfi-scoped)

| inv row | location                                                         | register disposition   | this run                                                                                              |
| ------- | ---------------------------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------------- |
| 2       | `prd/catalog.parquet` shadow                                     | yes-after-verify       | **REFUTED for tradfi** — tradfi instruments-store has NO `prd/` object, only `prod/` (defi+pred only) |
| 10      | `pipeline_mode=batch_massive` (1,696,166 obj)                    | no-migrate-first 🔴    | CONFIRMED — 686,005 manifest rows; one object re-probed present; HUMAN-ONLY purge (AE-4)              |
| 11      | tradfi legacy shapes (`day-` hyphen, chain-missing-qm, singles)  | no-migrate-first       | CONFIRMED — live hyphen tree `day-2026-01-01/data_type-tbbo/` probed + oracle-flagged (F2)            |
| 19      | `databento-batch-registry/{sha256}.json`                         | no-still-authoritative | CONFIRMED present (sha256-keyed json at bucket top level) — accepted-exception candidate              |
| 22      | tradfi QUARANTINE (garbage `underlying=` 14,633 + corrupt 1,180) | unknown                | CONFIRMED garbage underlyings live in manifest (12/13/23, GN/VT/3W) + `_quarantine/` tree (F5)        |
| 23      | dual `_migration_backup(s)/`                                     | unknown                | PARTIAL — `_migration_backup/manifest_dedup_2026_07_10/` + `_migration_backup_2026_07_09/` present    |
| 24      | `_needs_attribution/` nesting (tradfi = `raw_tick_data/`)        | unknown                | CONFIRMED — `_needs_attribution/raw_tick_data/` (tradfi nesting) present                              |
| 28      | `configs/patches/` in data bucket                                | unknown                | CONFIRMED — `configs/patches/` present at tradfi-prd top level                                        |

**Reality→register (new, to be appended by the register's maintenance contract — NOT done in this read-only run):** F3
(manifest chain rows carry blank `quote_asset`/`margin_type` while the path carries `quote=`/`margin=`) and F10 (the
catalogue+manifest are now ~92%/~81% canonical id-form, refuting the "0 canonical" claim inherited into cutover-register
§4 and reference-tradfi.md) are not register rows yet; both should be appended.

## 10. Verdict

tradfi's **live Databento lane is canonical on all four surfaces** for the sampled day (S1 oracle-clean chain tail, S2
canonical per-contract `CME:FUTURE:COPPER@LIN-…` content ids, S4 catalogue canonical, S3 captured) — with one measured
manifest gap (F3: chain `quote_asset`/`margin_type` columns unpopulated). The reference sheet's headline claim
("canonical on FILENAMES only; manifest + catalogue 0 canonical") is **REFUTED as of 2026-07-20**: the catalogue was
rebuilt (2026-07-20T01:05) to ~92% canonical id-form and the manifest is ~81% structured. Real residue is bounded and
known: the legacy hyphen tree (F2), the H4 garbage-underlying quarantine (F5), retired-vendor barchart (F7/B4), mixed
instrument_type casing (C2a, REFUSED), and the phantom count of 1635 (F1). The `batch_massive` estate (686,005 manifest
rows, human-only purge, AE-4) is suppressed. One HIGH cross-repo finding (F9: combo writer/reader path disagreement) is
reported for the MTDS plan, not fixed here. **No delete is authorized.** C2a + parked B1/B2/B4 REFUSED pending operator
ruling; the C2a taxonomy↔cutover-register contradiction is surfaced for the operator.
