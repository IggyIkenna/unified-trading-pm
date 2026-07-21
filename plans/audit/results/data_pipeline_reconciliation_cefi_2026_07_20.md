---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-07-20)"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=cefi over PROD buckets only (read-only). All three prod
  buckets resolve to -prd- tier and are reachable; the consolidated manifest is fresh (consolidator ran 2026-07-20,
  10,282,640 rows, phantom_count=0). Representative sample exercises every reference-sheet hazard H1-H6. Key measured
  results: reachable_coverage 44.85% (LOWER BOUND); the machine oracle is BLIND to the filename id-form (confirmed on
  real wire-named cefi objects); a live post-cutover adapter (LIGHTER-ZKSYNC) emits non-canonical bare-integer
  instrument ids on BOTH filename and content surfaces (H4 re-drift); cefi options_chain/futures_chain shards are 0%
  captured so the H1 v5/v6 chain-tail fork is a latent code path with no captured data behind it (measured: 17,042 chain
  atoms, all v5, 0 v6); instrument_type COLUMN casing is mixed and REFUSED (C2a, unruled). No delete suggestions rise
  above unknown; orphans NOT ASSESSED (no whole-corpus walk).
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, four-surface, cefi, non-canonical-paths, manifest, id-form, chain-tail]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
    cefi-capture-universe,
    canonical_path_oracle_blind_to_filename_stem_2026_07_20,
  ]
created: 2026-07-20
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=cefi, PROD (-prd-) buckets only, read-only; sample = manifest full-index aggregate + prefix-scoped S1/S2
  probes on 5 shards across eras/venues + cefi-scoped inventory sweep"
date: 2026-07-20
auditor: /data-pipeline-reconciliation (first real execution + acceptance test)
parent_epic: infrastructure_master
severity: P1
skill: data-pipeline-reconciliation
run_date: 2026-07-20
generated_at: 2026-07-20T00:00:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-07-20)

**Read-only.** No GCS writes, no manifest writes, no deletes, no backfills, no VM launches, no `--apply`. Deletes below
are SUGGESTIONS only; every prod-bucket delete is a human-only hard stop.

## 0. Declared sample scope (honest partial pass)

This is **not** a full-corpus reconciliation. The live cefi `_index` is **10,282,640 rows** spanning **2019-03-30 →
2026-07-20** (2,670 days, 25 venues). No new whole-corpus GCS walk was opened (review-blocking). All object reads were
manifest-driven or prefix-scoped (sanctioned no-walk route 1). The sample was chosen to exercise every reference-sheet
hazard (H1–H6) and to confirm/refute every inventory entry scoped to cefi.

**Sampled (what this run actually measured):**

1. **Surface 3 (manifest) — FULL index aggregate.** Every one of the 10,282,640 `_index` rows was read (column-scoped)
   for `capture_status`, `pipeline_mode`, `source`, `instrument_type`, `chain`, `instrument_id`, `underlying`,
   `quote_asset`, `margin_type`. This is a manifest read, not a corpus walk.
2. **Surface 1+2 (path + content) — 5 prefix-scoped shards** across eras and lanes:
   `HYPERLIQUID perpetual/trades @2026-07-20` (canonical), `DERIBIT perpetual/trades @2020-01-06` (legacy wire),
   `LIGHTER-ZKSYNC perpetual/derivative_ticker @2026-07-10` (live drift), `COINBASE-CDE future/trades @2026-07-10`
   (canonical), `DERIBIT futures_chain/trades @2026-07-20` (chain, absent).
3. **Machine oracle** `canonical_path_violations()` run at BOTH `require_pipeline_mode` settings on every probed
   object + the two documented wire-named demo strings.
4. **Phase-2 inventory sweep** — the five cefi-scoped rows of `non-canonical-path-inventory.md` (rows 1, 14, 16, 17, 23)
   re-verified by live probe.

**NOT sampled (declared coverage gaps — see §6):** the full filename id-form distribution across the corpus (needs a
walk); orphan enumeration (needs the single walk — route 3); the per-instrument S4 catalogue↔manifest window join;
`instruments-store-cefi` phantom coverage (H5, structurally absent from the phantom tool); features/processed corpora.

## 1. Bucket paths table (which bucket each read targeted)

All resolved via `resolve_bucket_name(cloud="gcp", kind=…, asset_group="cefi", deployment_env="prod")` over
`cloud-providers.yaml` — never an inline `gs://`. `GCP_PROJECT_ID=central-element-323112`.

| Layer / purpose               | `kind`              | Resolved bucket                                     | Tier     | Reachability                                    |
| ----------------------------- | ------------------- | --------------------------------------------------- | -------- | ----------------------------------------------- |
| raw tick (S1/S2/S3)           | `market-data`       | `market-data-tick-cefi-prd-central-element-323112`  | ✅ -prd- | REACHABLE (top-level delimited listing)         |
| raw tick (alias check)        | `tick-data`         | `market-data-tick-cefi-prd-central-element-323112`  | ✅ -prd- | REACHABLE — alias resolves identically          |
| reference / catalogue (S4)    | `instruments-store` | `instruments-store-cefi-prd-central-element-323112` | ✅ -prd- | REACHABLE                                       |
| features (folded)             | `features`          | `features-cefi-prd-central-element-323112`          | ✅ -prd- | REACHABLE                                       |
| legacy flat raw-tick (inv r1) | n/a (literal)       | `market-data-tick-cefi-central-element-323112`      | un-tier  | **404 / gone** (`exists()=False`) — as expected |
| legacy flat instr (inv r1)    | n/a (literal)       | `instruments-store-cefi-central-element-323112`     | un-tier  | **404 / gone** (`exists()=False`) — as expected |

No resolved name carried `-test-`. No prod bucket was unreachable. Manifest consolidator freshness
(`_index/latest.json`): last run **2026-07-20T18:31:25Z**, `success=true`, `verdict=produced`, `rows_out=10,282,640` —
Surface 3 is FRESH, not stale, so no shard is INCONCLUSIVE on manifest-unavailability grounds.

## 2. Coverage — formula named, LOWER BOUND

**`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`**, `empty_confirmed`
**EXCLUDED** (the live CK3-certified formula, `honest-coverage-model.md`).

| capture_status       | rows       |
| -------------------- | ---------- |
| captured             | 3,235,764  |
| empty_confirmed      | 3,067,920  |
| expected_unattempted | 2,768,047  |
| attempted_failed     | 1,210,909  |
| **total**            | 10,282,640 |

`reachable_coverage = 3,235,764 / (3,235,764 + 1,210,909 + 2,768,047) = 3,235,764 / 7,214,720 = ` **44.85%**.

- This is a **LOWER BOUND**: all 5 asset_groups gate Layer-2 (`instrument_gates_download=true`), so every `coverage_pct`
  understates.
- **Denominator scope note.** This 44.85% is over the **entire cefi manifest** (all 2,670 days, all venues, incl.
  non-MVP historical rows), so it is NOT directly comparable to the operator-accepted **~50.79%** figure in
  `cefi-capture-universe.md`, which is measured against the **MVP-scoped `expected_unattempted` denominator** at a point
  in time. Reported here to name the formula, not to re-open the accepted ceiling (operator 2026-07-17, Tardis N=1).
- The alternate include-`empty_confirmed` formula quoted in `cefi-capture-universe.md`
  (`captured/(captured+empty_confirmed+attempted_failed+expected_unattempted)`) would read **31.47%** — reported only to
  show the formula matters; the CK3 formula above is authoritative.

## 3. Per-surface verdict per shard (four bits — never collapsed)

`S1` = GCS path/filename · `S2` = parquet content id · `S3` = manifest atom · `S4` = catalogue render.
`✓`=canonical/present · `✗`=non-canonical · `~`=partial/not-fully-checked · `∅`=absent (honest) · `n/a`.

| #   | Shard (prefix-scoped)                                    | S1 structure  | S1 id-form    | S2 content id                        | S3 manifest               | S4  | Verdict                                                        |
| --- | -------------------------------------------------------- | ------------- | ------------- | ------------------------------------ | ------------------------- | --- | -------------------------------------------------------------- |
| A   | HYPERLIQUID perpetual/trades `@2026-07-20`               | ✓ (0 viol)    | ✓ 6/6         | ✓ `HYPERLIQUID:PERPETUAL:0G-USD@LIN` | ✓ captured                | ~   | **CANONICAL** (filename==content; oracle clean)                |
| B   | DERIBIT perpetual/trades `@2020-01-06`                   | ✓ (0 viol)    | ✗ wire        | ✗ `DERIBIT:PERPETUAL:BTC-PERPETUAL`  | ✓ `…:BTC-USD@INV` (canon) | n/a | **THREE-WAY DIVERGENCE** — S1 wire ≠ S2 double-wrap ≠ S3 canon |
| C   | LIGHTER-ZKSYNC perpetual/derivative_ticker `@2026-07-10` | ✓ (0 viol)    | ✗ `0.parquet` | ✗ `LIGHTER-ZKSYNC:PERPETUAL:0`       | ~ (chain-col populated)   | n/a | **NON-CANONICAL id-form (LIVE adapter)** — S1==S2 but both ✗   |
| D   | COINBASE-CDE future/trades `@2026-07-10`                 | ✓ (0 viol)    | ✓ 6/6         | ~ (not read)                         | ~                         | n/a | **CANONICAL** (filename id-form)                               |
| E   | DERIBIT futures_chain/trades `@2026-07-20`               | ∅ (0 objects) | n/a           | n/a                                  | expected_unattempted      | n/a | **HONEST ABSENCE** (S1∅ + S3 expected_unattempted)             |

**Oracle-blindness, MEASURED (four-surface-procedure §4.3).** Shards B and C return **0 oracle violations at both
`require_pipeline_mode` settings** despite non-canonical filenames — the oracle drops the last path segment and only
tradfi single-instrument shards have a stem rule, so a wire-named CeFi object reads FALSE-CLEAN. The two documented demo
strings confirm it: `ADAF0:USTF0.parquet` → `[]` and `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet` → `[]`. **Every
"canonical" verdict from the path oracle in this report is STRUCTURE-ONLY; id-form was checked separately by sampling
the filename stem + reading the S2 `instrument_id` column.**

## 4. Typed findings (taxonomy names only)

Severity per `reconciliation-finding-taxonomy.md` §2 defaults unless justified.

| ID  | type                                           | severity        | surfaces          | shard_atom / scope                                       | detail                                                                                                                                                                                                                                                                                                                                                                                                                                        | delete_eligible |
| --- | ---------------------------------------------- | --------------- | ----------------- | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------- |
| F1  | `non_canonical_path` (id-form)                 | MEDIUM          | S1,S2             | LIGHTER-ZKSYNC perpetual, live `@2026-07-10`             | Live post-cutover adapter emits bare-integer market-index filenames (`0.parquet`) + content id `LIGHTER-ZKSYNC:PERPETUAL:0` — the base-quote segment is a raw index, never resolved to `BASE-QUOTE@MARGIN`. Oracle blind. This is H4 "new writes re-drift" MEASURED (only ~4/63 adapters route through the shared canonical-id builder). Detector: prefix-scoped S1 listing + S2 read.                                                        | NO              |
| F2  | `non_canonical_path` (id-form) + id divergence | MEDIUM          | S1,S2,S3          | DERIBIT perpetual `@2020-01-06` (legacy era)             | Three-way identity divergence: S1 filename `BTC-PERPETUAL.parquet` (wire) ≠ S2 content `DERIBIT:PERPETUAL:BTC-PERPETUAL` (double-wrapped) ≠ S3 manifest `DERIBIT:PERPETUAL:BTC-USD@INV` (canonical). The v9/canonical migration re-keyed the MANIFEST but not the object filename/content. Date-gate: id-form axis cutover is UNKNOWN (`canonical-cutover-register` §3a) → **unknown-vintage**, migration-state (H4), NOT a fresh regression. | NO              |
| F3  | `divergent_empty` / coverage                   | LOW             | S3                | cefi `options_chain`+`futures_chain` (17,042 atoms)      | **0% captured** — 10,430 `empty_confirmed` + 6,612 `expected_unattempted`, zero `captured`. All 17,042 are v5-tail (blank quote/margin); **0 v6-tail** in the manifest. H1's v5/v6 chain-tail writer fork is therefore a LATENT code path with no captured data behind it — reported as ONE finding per `canonical-cutover-register` §7, not per-shard. (Option data is captured as `option` singles, not `options_chain` bundles.)           | NO              |
| F4  | shard-atom integrity (taxonomy-gap)            | MEDIUM          | S3                | 5,232 CAPTURED rows w/ blank `instrument_type`           | 130,130 rows carry a blank `instrument_type` axis (69,748 attempted_failed, 55,150 empty_confirmed, **5,232 captured**). A captured row missing a non-KEY atom axis is a malformed shard atom. No clean taxonomy name — reported as a taxonomy-gap candidate.                                                                                                                                                                                 | NO              |
| F5  | shard-atom integrity (missing KEY)             | LOW-MED         | S3                | 36,865 single rows w/ blank `instrument_id` KEY          | The `(KEY)` for singles is `instrument_id`; 36,865 single rows carry it blank (36,571 pre-2026-05-19 / **294 post**). Mostly legacy; the 294 post-cutover rows are the live-attention subset.                                                                                                                                                                                                                                                 | NO              |
| F6  | `non_canonical_path` (pipeline_mode)           | LOW             | S3 (implied path) | 4 BYBIT rows, post-2026-05-19                            | 218,492 rows carry blank `pipeline_mode`; date-split against the cutover (`canonical-cutover-register` §2, effective 2026-05-19): **218,488 pre-cutover = legitimately historical (NOT a finding)**, only **4 post-cutover** (BYBIT, blank source) = regression candidate. The H3 `.replace()` bolt-on is guarded by a `raise` in the W1 lane, which is why this is ~0.                                                                       | NO              |
| F7  | `source=` write-wiring gap (H6)                | KNOWN-CONDITION | S3                | 2,810,078 rows (27.3%) blank `source`                    | Reported ONCE per H6: cefi cells land with `source=""`. Not a per-shard data defect; the known crosscutting wiring gap. Non-blank sources: tardis 6.49M, aster 711k, hyperliquid 182k, extended 90k, + long tail.                                                                                                                                                                                                                             | NO              |
| F8  | manifest content-column anomaly                | LOW             | S3                | 817,505 cefi rows w/ non-null `chain` column             | The cefi atom has NO `chain` axis and the path grammar has no `chain=` segment, yet the `chain` content column is populated for the on-chain perp DEXes: ASTER 582,225 · HYPERLIQUID 130,414 · EXTENDED-STARKNET 90,046 · LIGHTER-ZKSYNC 14,820. Display-column residue, not a path/atom canonicality defect; noted for hygiene.                                                                                                              | NO              |
| F9  | `catalogue-freshness`                          | INFO            | S4                | deployment-api `data-catalogue.instruments-service.yaml` | Reported once per run per SKILL §3c standing condition (`last_updated` 2026-02-06, `auto_refreshed: null`). **UNVERIFIED this run** — the yaml was not re-opened; the `prod/catalog.parquet` (8.99 MB) IS present and fresh.                                                                                                                                                                                                                  | NO              |

## 5. Phase-2 non-canonical inventory sweep (cefi-scoped) + delete dispositions

**Register → reality (re-verified live 2026-07-20):**

| inv # | location                                                                                                          | register disposition                                          | re-verify verdict                                                                                                                                                            |
| ----- | ----------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | legacy flat `market-data-tick-cefi-{pid}`, `instruments-store-cefi-{pid}`                                         | buckets gone (404); code-literal is the live entry            | **CONFIRMED** — both `exists()=False`. Delete already DONE; the register entry is the code literals (row 14), not the buckets.                                               |
| 14    | 21 module-level un-tiered bucket TEMPLATE literals                                                                | live code, baselined open                                     | Not re-audited at code level this run (cross-AG, live) — disposition unchanged.                                                                                              |
| 16    | `instrument_availability/by_date/day={D}/venue={V}/instruments.parquet` FLAT (no `pipeline_mode=`/`asset_group=`) | `no-still-authoritative` — the LIVE writer emits flat two-key | **CONFIRMED** — `…/by_date/day=2026-07-19/venue=DERIBIT/…`, no `pipeline_mode=`/`asset_group=` segment. Live writer output; NOT a delete candidate.                          |
| 17    | `features-cefi-prd/delta_one/day=…` (no `by_date/` level)                                                         | `no-still-authoritative` — no SSOT for post-fold root         | **CONFIRMED** — `delta_one/day=2026-05-02/` (+ a `delta_one/processed_candles/` subtree). Open post-fold-root question stands.                                               |
| 23    | `market-data-tick-cefi-prd` dual `_migration_backup/` AND `_migration_backups/`                                   | `unknown` — which spelling wins / retention?                  | **CONFIRMED** both present. **NEW (reality→register): a THIRD spelling `_remediation_backups/` is also present** at the raw-tick top level — not in register row 23. See §7. |

**Delete suggestions:** **NONE rise above `unknown`.** No cefi-scoped location classified as `legacy_duplicate` or
`junk` with a five-part proof this run. The legacy wire-named objects (F2) are `no-migrate-first` by definition (the
manifest already holds the canonical id but the objects are the only copy of their content) — never delete. Prod-bucket
deletes are a human-only hard stop regardless.

**Orphans: NOT ASSESSED (no whole-corpus walk in this run).** Per `orphan-object-detection.md` §3 corollary, a
manifest-driven pass MUST NOT report `0 orphans`. Enumeration rides route 3 (`migration_orphan_sweep.py`'s single walk),
not performed here. The pre-computed `_index/audit/orphan_sweep_cefi.parquet` (21.7 MB) exists and could be READ in a
follow-up without a new walk.

## 6. Suppressed accepted-exceptions + REFUSED axes

**Suppressed (mandatory — shown as counts, not re-listed as findings):**

| exception                                 | applies to cefi?  | suppressed count / note                                                                                                                                                                                                                                                                                                                                                                                            |
| ----------------------------------------- | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **C2a — `instrument_type` COLUMN casing** | YES — **REFUSED** | Measured MIXED case: `PERPETUAL` 7,220,102 (upper) + `perpetual` 9,146 (lower); `FUTURE/OPTION/SPOT_PAIR/COMBO` upper; `futures_chain/options_chain/spot` lower. Both sides cite the same operator on 2026-07-18; >12M-row blast radius. **NOT reported as a finding; no casing migration proposed.** Compared case-insensitively. The PATH segment (lowercase) and id-middle (UPPER) remain settled and enforced. |
| AE-1 sports blank pipeline_mode/source    | NO                | sports bucket only — N/A for cefi.                                                                                                                                                                                                                                                                                                                                                                                 |
| AE-2 tradfi `combo` bare-underlying       | analogous         | cefi carries 662 `combo` rows + `DERIBIT-COMBO` venue; combo id format is unsettled workspace-wide (`partition_paths.py:271-273` excludes combo) — its bare tail is NOT flagged.                                                                                                                                                                                                                                   |
| AE-5 / decision-D defi `LENDING`          | NO                | defi market/event only — N/A for cefi.                                                                                                                                                                                                                                                                                                                                                                             |

**REFUSED axes (skill §3e) — stated, not decided:** only **C2a** applies to cefi (above). Decision-D (defi lending
keying) is defi-only and does not touch this asset_group.

## 7. Coverage gaps (declared — what this run did NOT reach)

1. **Filename id-form full distribution.** Only 5 shards were S1-sampled. Confirmed non-canonical filenames exist
   (DERIBIT 2020 wire; LIGHTER-ZKSYNC 2026 bare-integer) and canonical ones exist (HYPERLIQUID, COINBASE-CDE 2026). The
   full corpus id-form % is NOT machine-checked — independent measurement in `four-surface-reconciliation-procedure.md`
   §4 puts the CeFi filename surface at **20.82% canonical by id-form**; measuring it exactly needs the single walk
   (route 3), out of scope for a read-only manifest-driven pass.
2. **Orphans** — NOT ASSESSED (§5).
3. **H5 — `instruments-store-cefi` phantom coverage.** The bucket is absent from the phantom reconciler's
   `_BUCKET_KIND_MAP`, so its rows have NEVER been phantom-checked. Absence of phantom findings there is **absence of
   evidence**, not evidence of absence.
4. **S4 per-instrument catalogue↔manifest window join** — the catalogue `prod/catalog.parquet` is present + fresh, but
   the per-instrument `available_from`→`available_to` vs manifest atom comparison was not run (venue/day-grain S4
   in-scope check only).
5. **NEW register-append owed (reality→register):** `_remediation_backups/` in `market-data-tick-cefi-prd` is a third
   operational-backup spelling not in `non-canonical-path-inventory.md` row 23. Per the register maintenance contract it
   should be appended (disposition `unknown`). This run did NOT edit the shared register (concurrent sibling-AG agents
   may be editing the same doc; git is orchestrator-owned) — flagged here for the orchestrator/operator to land.

## 8. Acceptance criteria (this run)

1. Every prod bucket resolved via `resolve_bucket_name` (no inline `gs://`) and confirmed `-prd-` tier — PASS.
2. Reachability proven per bucket; unreachable ones declared — PASS (none unreachable).
3. Manifest freshness confirmed (not stale) before trusting S3 — PASS (consolidator ran 2026-07-20).
4. Four surfaces reported as four independent bits per sampled shard — PASS (§3).
5. Every % carries its named formula + LOWER-BOUND marker — PASS (§2).
6. Machine oracle used for structure; id-form checked separately and blindness stated — PASS (§3).
7. C2a REFUSED, not reported as a finding; suppression shown as counts — PASS (§6).
8. Delete suggestions gated; none above `unknown`; orphans NOT ASSESSED, not 0 — PASS (§5).
9. Coverage gaps declared honestly — PASS (§7).
