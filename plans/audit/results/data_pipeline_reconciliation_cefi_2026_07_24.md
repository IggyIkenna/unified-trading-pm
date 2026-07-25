---
doc_type: audit-result
title: "Data-pipeline reconciliation — cefi (2026-07-24), raw-tick layer"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=cefi, raw-tick layer, over PROD buckets only (read-only,
  Phases 0->2). Headline: CeFi raw-tick CAPTURE (both live and batch) is measurably HALTED — manifest capture_status by
  date shows captured rows collapsing from a steady ~1,000-1,200/day baseline to 5 (2026-07-21) then ZERO (07-22/23/24),
  the corpus-wide `attempted_at` maximum across all 9,045,162 cefi manifest rows is 2026-07-24T01:31:59Z (~23h stale at
  probe time), and a direct GCP check found the twice-daily batch-download Cloud Run Job
  (`uts-prod-market-tick-data-service-cefi-t1-recon`, 4 CPU/8Gi) crash-looping on signal 9 (SIGKILL/OOM) within ~10-40s
  of every execution since at least 2026-07-23, before any venue download begins. This is NOT documented in the actively
  -worked cefi migration issue docs reviewed this run (which discuss OOM kills of a SEPARATE manifest-dedup script on
  shared dev/VM infra) — filed as a new BIG finding + issue doc. Positive findings: the machine oracle's id-form check
  now independently covers cefi (`_ID_FORM_CHECKED_ASSET_GROUPS={"cefi","defi"}`, corroborating the defi run's
  correction) — re-tested directly, both documented "false-clean" demo strings now correctly return violations;
  `reachable_coverage` measured 52.61% (LOWER BOUND, up from 44.85% on 2026-07-20, though the denominator itself shrank
  ~12% via an intervening manifest dedup); the `chain` column's F8 hygiene finding from 2026-07-20 is RESOLVED (dropped
  to 0/9,045,162 by operator directive, not a regression); `instrument_type` COLUMN casing measured 100% UPPERCASE (0
  lowercase), ahead of the register's "migration_pending" framing. LIGHTER-ZKSYNC bare-integer filenames and the 4-row
  post-cutover blank-`pipeline_mode` BYBIT rows persist unchanged from 2026-07-20 (both already tracked). No delete
  suggestions rise above `unknown`; orphans NOT ASSESSED (no whole-corpus walk this run).
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, four-surface, cefi, non-canonical-paths, manifest, id-form, capture-halt, oom]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
    cefi-capture-universe,
    data_pipeline_reconciliation_cefi_2026_07_20,
    data_pipeline_reconciliation_defi_2026_07_24,
    canonical_path_oracle_blind_to_filename_stem_2026_07_20,
    cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24,
    cefi_high_attempted_failed_batch_cluster_2026_07_23,
    cefi_batch_download_oom_crashloop_capture_halt_2026_07_24,
  ]
created: 2026-07-24
resulting_plan:
lib_version:
  "unified-api-contracts 0.72.1.dev578+gc2b303f7e / unified-trading-library 0.56.1.dev354+gf9c23a238 /
  market-tick-data-service 0.92.1.dev848+g3fb95eafa.d20260724"
doc_versions_checked:
audited_scope:
  "asset_group=cefi, layer=raw-tick, PROD (-prd-) bucket only, read-only, Phases 0->2 per the
  /data-pipeline-reconciliation skill; full manifest aggregate read (9,045,162 rows) + prefix-scoped S1/S2 probes on 6
  shards across eras/venues + cefi-scoped inventory sweep + a direct GCP Cloud Scheduler/Cloud Run/Logging check
  triggered by an anomaly the manifest read surfaced"
date: 2026-07-24
auditor: /data-pipeline-reconciliation (dispatched sub-agent run)
parent_epic: infrastructure_master
severity: P0
skill: data-pipeline-reconciliation
run_date: 2026-07-24
generated_at: 2026-07-25T00:50:00+00:00
---

# Data-pipeline reconciliation — cefi (2026-07-24), raw-tick layer

**Read-only.** No GCS writes, no manifest writes, no deletes, no backfills, no VM launches, no `--apply`. Deletes below
are SUGGESTIONS only; every prod-bucket delete is a human-only hard stop. This run is Phases 0→2 only,
`--layer raw-tick` (default; candles explicitly out of scope per dispatch). The GCP Cloud Scheduler/Cloud Run/Logging
checks in §9 are also read-only (`describe`/`list`/`logging read`) — no job was paused, resumed, or triggered by this
run.

## 0. Phase-0 reachability probe (skill-required, run independently of the dispatch's pre-verification)

Non-recursive top-level listing, all 5 buckets named in the dispatch, confirmed reachable at probe time
(`2026-07-25T00:20Z`):

| asset_group           | kind resolved                                     | bucket                                               | reachable                                                                                                                                                                                                     |
| --------------------- | ------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| cefi (primary target) | `market-data`                                     | `market-data-tick-cefi-prd-central-element-323112`   | ✅ (9 root prefixes: `_index/`, `_migration_backup/`, `_migration_backups/`, `_quarantine/`, `_remediation_backups/`, `_vm_staging/`, `backfill-logs/`, `processed_candles/`, `raw_tick_data/`; 0 root blobs) |
| tradfi                | `market-data`, `asset_group=tradfi`               | `market-data-tick-tradfi-prd-central-element-323112` | ✅ (not otherwise probed — out of scope)                                                                                                                                                                      |
| defi                  | `market-data`, `asset_group=defi`                 | `market-data-tick-defi-prd-central-element-323112`   | ✅ (not otherwise probed — out of scope)                                                                                                                                                                      |
| sports                | `market-data`, `asset_group=sports`               | `market-data-tick-sports-prd-central-element-323112` | ✅ (not otherwise probed — out of scope)                                                                                                                                                                      |
| prediction            | `market-data-tick-prediction` (no `asset_group=`) | `market-data-tick-pred-prd-central-element-323112`   | ✅ (not otherwise probed — out of scope)                                                                                                                                                                      |

Consistent with the dispatch's own pre-verification. `GCP_PROJECT_ID=central-element-323112` set in env;
`resolve_bucket_name(cloud="gcp", kind=..., asset_group="cefi", deployment_env="prd")` used throughout — never an inline
`gs://`, never env-mutated for tier.

## 1. Declared sample scope (honest partial pass)

Not a full-corpus four-surface walk (2,674 days on disk, 2019-03-30→2026-07-24; the live consolidated `_index` is 171.6
MB / 9,045,162 rows). Sampled to exercise every reference-sheet hazard plus an anomaly this run's own Phase-0 manifest
read surfaced:

1. **Surface 3 (manifest) — FULL index aggregate**, column-projected (`capture_status`, `pipeline_mode`, `source`,
   `instrument_type`, `chain`, `instrument_id`, `underlying`, `quote_asset`, `margin_type`, `asset_group`, `venue`,
   `data_type`, `date`, `error_reason`, `row_count`, `attempted_at`) via
   `read_availability_index(..., filters=[("asset_group","==","cefi")])`. This is a manifest read, not a corpus walk;
   20.9s wall time.
2. **Surface 1+2 (path + content) — 6 prefix-scoped shards** across eras/venues:
   `HYPERLIQUID perpetual/trades @2026-07-20` (canonical, flat), `ASTER perpetual/trades @2026-07-20` (canonical, flat),
   `DERIBIT perpetual/trades @2020-01-06` (legacy wire, re-tested against the oracle),
   `LIGHTER-ZKSYNC perpetual/derivative_ticker @2026-07-14` (bare-integer, re-tested),
   `DERIBIT future/book_snapshot_5 @2026-07-20` (dated futures, now flat-per-contract — no chain-bundle tail found),
   `OKX-FUTURES future @2026-07-20` (chain-bundle prefix existence check only).
3. **Machine oracle** `canonical_path_violations()` run at BOTH `require_pipeline_mode` settings on every probed
   object + the two documented wire-named demo strings (`ADAF0:USTF0.parquet`,
   `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet`) — direct re-test of whether the 2026-07-20 report's "oracle-blind"
   finding still holds.
4. **Distinct-value census (manifest side, G1)** — full-corpus `venue` and `instrument_type` distinct sets from the
   Step-1 read, compared against `unified_api_contracts.registry.market_data_categories.VENUES_BY_ASSET_GROUP["cefi"]`
   (26 venues) and the canonical `InstrumentType` vocabulary.
5. **Phase-2 inventory sweep** — the cefi-scoped rows of `non-canonical-path-inventory.md` (rows 1, 16, 23) re-verified
   by live probe, plus a top-level + one-level-deep bounded sweep for reality→register candidates.
6. **A triggered, targeted GCP infra check (§9)** — the manifest's own `capture_status` × `date` pivot and
   `attempted_at` maximum surfaced a hard capture cliff; followed up with **read-only**
   `gcloud scheduler jobs list/describe`, `gcloud run jobs describe/executions list`, and `gcloud logging read` against
   `central-element-323112` (admin ADC, per workspace governance) to characterize — not fix — the anomaly. This is the
   skill's "grep-then-READ, not grep-then-conclude" discipline applied to an in-manifest signal rather than a doc claim.

**NOT sampled (declared coverage gaps — see §11):** the full filename id-form distribution across the corpus (needs a
walk); orphan enumeration (needs the single walk — route 3, none available to reuse this run — see §11); the
per-instrument S4 catalogue↔manifest window join; `instruments-store-cefi` phantom coverage (H5, structurally absent
from the phantom tool, per the 2026-07-20 report — not re-verified); OKX-FUTURES/OPTIONS chain-bundle CONTENT (S2) not
read this run, only S1 prefix existence.

## 2. Bucket paths table

All resolved via `resolve_bucket_name(cloud="gcp", kind=..., asset_group="cefi", deployment_env="prd")` over
`cloud-providers.yaml`.

| Layer / purpose               | `kind`              | Resolved bucket                                     | Reachability                                    | Read targeted                                                                                                                                                                  |
| ----------------------------- | ------------------- | --------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| raw tick (S1/S2/S3)           | `market-data`       | `market-data-tick-cefi-prd-central-element-323112`  | ✅ REACHABLE                                    | `raw_tick_data/by_date/`, `_index/`, `_index/snapshots/`, `_index/per_vm/`, `_migration_backup(s)/`, `_remediation_backups/`, `_vm_staging/`, `backfill-logs/`, `_quarantine/` |
| raw tick (alias check)        | `tick-data`         | `market-data-tick-cefi-prd-central-element-323112`  | ✅ REACHABLE — resolves identically             | alias confirmation only                                                                                                                                                        |
| reference / catalogue (S4)    | `instruments-store` | `instruments-store-cefi-prd-central-element-323112` | ✅ REACHABLE                                    | `prod/catalog.parquet` (freshness), top-level prefix listing                                                                                                                   |
| features (folded)             | `features`          | `features-cefi-prd-central-element-323112`          | ✅ REACHABLE                                    | top-level prefix listing only                                                                                                                                                  |
| legacy flat raw-tick (inv r1) | n/a (literal)       | `market-data-tick-cefi-central-element-323112`      | **404 / gone** (`exists()=False`) — as expected | —                                                                                                                                                                              |
| legacy flat instr (inv r1)    | n/a (literal)       | `instruments-store-cefi-central-element-323112`     | **404 / gone** (`exists()=False`) — as expected | —                                                                                                                                                                              |

No resolved name carried `-test-`. No prod bucket was unreachable.

## 3. Index freshness / lock state

- `_index/consolidator.lock` — **NOT held** at probe time (unlike the concurrent defi run this session, which found the
  lock held).
- `_index/latest.json` — last consolidator run **2026-07-25T00:20:51Z**,
  `verdict=empty, no_op=true, shards_scanned=1, rows_out=0` — the consolidator ran cleanly but found only **1** per-VM
  shard to scan (see §9 — this is itself evidence for the capture-halt finding: a healthy pipeline should be feeding it
  far more than 1 shard/run).
- `_index/availability_index.parquet` — **171.6 MB, age 28.6s at first probe** (well under the 120s fresh/stale-fallback
  threshold) — this run's Step-1 read was against the **fully consolidated** view, not a per-VM-shard fallback. Every S3
  count below is a **direct read of the consolidated index**, not a lower-bound fallback merge.
- `_index/phantom_audit_latest.json` — `phantom_count=0`, `generated_at=2026-07-18T15:52:21Z` — **read, not re-run**, 7
  days stale relative to this probe.
- `_index/reprobe_audit_latest.json` — `generated_at=2026-07-14T06:19:32Z`, all-zero deltas — **read, not re-run**, 11
  days stale.
- `_index/per_vm/` — contains exactly **1 file**, `_legacy_seed.parquet` (4.89 MB, `updated=2026-07-24T23:30:12Z`) —
  this is the Surface-C v2 dedup apply's own output artifact
  (`cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 7: "wrote... `per_vm/_legacy_seed.parquet`
  (320,344 rows)"), **not** a live capture writer's staging shard. Corroborates §9.
- `_index/snapshots/` — 3 dated snapshots present; `pre_d4_20260724T232332Z/` (the Surface-C v2 apply's pre-write
  snapshot, 189.3 MB, **10,600,381 cefi rows**) was downloaded and read directly for §7's `chain`-column diff.

**Consequence: this run's S3 numbers are a direct, current, fully-consolidated read — the highest-confidence S3 read
this skill's reports have produced for cefi to date** — but see §9: freshness of the INDEX is not the same as freshness
of the DATA it indexes, and the data itself has stopped moving.

## 4. Suppression inputs loaded

- `canonical-cutover-register.md` §2 (`require_pipeline_mode` effective-from 2026-05-19, all AGs), §3c (C2a
  `instrument_type` COLUMN — RULED UPPERCASE target, `migration_pending`, compared case-insensitively, no finding), §6c
  (cefi chain-tail v6 — RULED, `migration_pending`, both v5/v6 tails accepted, fork reported once not per-shard).
- `reconciliation-finding-taxonomy.md` §4 AE-2 (tradfi/cefi-analogous `combo` bare-underlying carve-out — cefi's 13,065
  `COMBO` rows are NOT flagged), §5.1 (C2a — measured this run at 0% lowercase, see §8 FIND-04).
- `non-canonical-path-inventory.md` (cefi rows 1, 14, 16, 17, 23) — reconciled in §7.

## 5. The machine oracle — id-form check now COVERS cefi (major correction from 2026-07-20)

`canonical_path_violations()` is the sole authority (never re-implemented). The 2026-07-20 cefi report's headline
finding was that the oracle is **structurally blind** to filename id-form for cefi ("Shards B and C return 0 oracle
violations... despite non-canonical filenames"). **Re-tested directly this run — that is no longer true.**

| Test object                                                                    | require_pm=False          | require_pm=True | 2026-07-20 result      | This run                  |
| ------------------------------------------------------------------------------ | ------------------------- | --------------- | ---------------------- | ------------------------- |
| `ADAF0:USTF0.parquet` (documented demo string)                                 | **1 violation** (id-form) | **1 violation** | `[]` — false-clean     | **CAUGHT**                |
| `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet` (documented demo string)      | **1 violation**           | **1 violation** | `[]` — false-clean     | **CAUGHT**                |
| `DERIBIT/.../BTC-PERPETUAL.parquet` (real 2020-01-06 wire object, shard B)     | **1 violation** (id-form) | **1 violation** | `[]` — false-clean     | **CAUGHT**                |
| `LIGHTER-ZKSYNC/.../0.parquet` (real 2026-07-14 bare-integer object, shard C)  | **1 violation** (id-form) | **1 violation** | `[]` — false-clean     | **CAUGHT**                |
| `HYPERLIQUID/.../HYPERLIQUID:PERPETUAL:AAVE-USD@LIN.parquet` (real, canonical) | `[]`                      | `[]`            | `[]` — correctly clean | **still correctly clean** |

Root cause, confirmed via direct import:
`unified_api_contracts.canonical.partition_paths._ID_FORM_CHECKED_ASSET_GROUPS = frozenset({"defi", "cefi"})` (present
in `unified-api-contracts 0.72.1.dev578+gc2b303f7e`, the exact version this run's venv carries). **This is the identical
correction the concurrent 2026-07-24 defi reconciliation run flagged as FIND-09** (that report tested only defi and
tradfi's demo string; this run independently confirms the SAME shipped fix also covers cefi, closing the "is it
cefi-specific" question). **`four-surface-reconciliation-procedure.md` §4/§4.3, `reconciliation-finding-taxonomy.md`
§2.2, and `CLAUDE.md`'s domain index all still describe the oracle as tradfi-only for id-form — all three are STALE as
of this run** (not just the defi run — this is now confirmed on a second asset_group, strengthening the case to correct
the SSOTs rather than treat it as a one-off).

**Practical effect on this report:** every "canonical" verdict below that also shows `[]` from the oracle is now a
**structure-AND-id-form** clean verdict, not structure-only — a strictly stronger claim than the 2026-07-20 report could
make.

## 6. Per-surface verdict per shard (four surfaces = four bits, never collapsed)

Legend: `OK` · `NON-CANON` · `ABSENT` · `SUPPRESSED` (accepted exception) · `NOTE` (observation) · `NOT-READ`.

| #   | shard atom                                                                                | S1 structure                                                        | S1 id-form                                              | S2 content                                                                    | S3 manifest                                                            | S4                                        | notes                                                                                                                                                                                                                                                                |
| --- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A   | HYPERLIQUID perpetual/trades `@2026-07-20`                                                | OK (0 viol)                                                         | OK                                                      | NOT-READ (flat filename == expected canonical form, not independently opened) | `captured` (per manifest aggregate)                                    | ~ (bucket reachable, window join not run) | **CANONICAL** — flat pattern #1, matches 2026-07-20's shard A                                                                                                                                                                                                        |
| B   | ASTER perpetual/trades `@2026-07-20`                                                      | OK (0 viol)                                                         | OK                                                      | NOT-READ                                                                      | `captured`                                                             | ~                                         | **CANONICAL** — flat, e.g. `ASTER:PERPETUAL:1000BONK-USDT@LIN.parquet`                                                                                                                                                                                               |
| C   | DERIBIT perpetual/trades `@2020-01-06` (`BTC-PERPETUAL.parquet`, `ETH-PERPETUAL.parquet`) | OK structure (0 struct viol)                                        | **NON-CANON — now CAUGHT by the oracle** (§5)           | `instrument_id=DERIBIT:PERPETUAL:BTC-PERPETUAL` (double-wrapped, S2≠S1 stem)  | `captured` (manifest carries the canonical re-key per 2026-07-20's F2) | NOT-READ                                  | legacy wire era, `unknown-vintage` per the cutover register (id-form axis effective-from UNKNOWN) — **not a fresh finding**, but NOW machine-detectable                                                                                                              |
| D   | LIGHTER-ZKSYNC perpetual/derivative_ticker `@2026-07-14` (`0.parquet` etc.)               | OK structure                                                        | **NON-CANON — now CAUGHT by the oracle** (§5)           | `instrument_id=LIGHTER-ZKSYNC:PERPETUAL:0` (S1==S2, both non-canonical)       | `captured`                                                             | NOT-READ                                  | **ALREADY TRACKED** — `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` item 6 ("LIGHTER-ZKSYNC numeric-stem GCS rename backfill... resolver code SHIPPED, dry-run+apply never attempted"). Identical defect, unresolved, persisting since 2026-07-20. |
| E   | DERIBIT future/book_snapshot_5 `@2026-07-20` (dated futures)                              | OK (0 viol)                                                         | OK — e.g. `DERIBIT:FUTURE:BTC-USD@INV-20260724.parquet` | NOT-READ                                                                      | `captured`                                                             | NOT-READ                                  | **CANONICAL, and STRUCTURALLY CHANGED since 2026-07-20**: no chain-bundle `underlying=/ticks.parquet` tail found — this venue/day is now flat-per-contract, full canonical id including expiry suffix. See §8 FIND-02 (S3 vocabulary fold).                          |
| F   | OKX-FUTURES future `@2026-07-20` (prefix only)                                            | prefix exists, `instrument_type=future/` only (no `futures_chain=`) | NOT-READ (no object opened)                             | NOT-READ                                                                      | `captured`/mixed                                                       | NOT-READ                                  | consistent with shard E — no lingering `futures_chain`/`options_chain` PATH segment found on this sample day for either venue checked                                                                                                                                |

**Chain-tail v5/v6 hazard (register §6c) — sampled, not resolved.** Neither venue sampled this run (HYPERLIQUID/ASTER —
flat singles; DERIBIT/OKX-FUTURES dated futures — flat-per-contract) currently emits the
`underlying=/quote=/margin=/ticks.parquet` bundle tail at all on the sampled day; the register's v5/v6 fork applies to
whichever shards still route through the bundle-per-underlying pattern (#2) — this run's manifest-side check (§8
FIND-02) shows those rows still exist (keyed on `underlying`, blank `instrument_id` by design) but the register's
specific v5-vs-v6 PATH tail shape was **not independently re-probed on an actual bundle object this run** — declared
gap, §11.

## 7. Corpus-scale reference — full manifest aggregate (9,045,162 rows, 2019-03-30→2026-07-24)

**`reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`**, `empty_confirmed`
**EXCLUDED** (the live CK3-certified formula, `honest-coverage-model.md`).

| capture_status       | rows          | % of total |
| -------------------- | ------------- | ---------- |
| captured             | 3,425,645     | 37.87%     |
| empty_confirmed      | 2,533,470     | 28.01%     |
| expected_unattempted | 2,026,577     | 22.40%     |
| attempted_failed     | 1,059,470     | 11.71%     |
| **total**            | **9,045,162** | 100%       |

`reachable_coverage = 3,425,645 / (3,425,645 + 1,059,470 + 2,026,577) = 3,425,645 / 6,511,692 = ` **52.61%** (LOWER
BOUND — all 5 AGs gate Layer-2 `instrument_gates_download=true`).

**Trend vs 2026-07-20 (44.85%) — up +7.76pp, but the comparison is NOT apples-to-apples.** The manifest's total row
count itself **dropped from 10,282,640 (2026-07-20) to 9,045,162 (this run) — a net -1,237,478 rows (-12.0%)**. This is
**not data loss**: it is traced directly to the **"Surface C v2 manifest apply"** documented in
`cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` Finding 7, which ran **2026-07-24 ~23:20-23:30Z**
(confirmed via this run's own snapshot read, §3) — a legitimate manifest-dedup canonicalization pass that folds
duplicate/collision-prone `PIN_ATOM` groups. The pre-apply snapshot (`_index/snapshots/pre_d4_20260724T232332Z/`,
downloaded and read directly this run) shows **10,600,381** cefi rows immediately before the apply, and the issue doc
records the post-apply write at **9,069,094** rows; this run's live read (~90 min later) shows **9,045,162** — a further
-23,932 organic drift consistent with continued dedup/consolidation, not a new incident. **Do not quote the 44.85%→
52.61% delta as pure coverage improvement without this caveat** — a shrinking, cleaner denominator mechanically raises
the ratio even before any new capture.

**Attempted_failed top causes** (of 1,059,470): `Tardis HTTP 403` family (`UNCLASSIFIED:Tardis HTTP 403` 562,997 +
`Tardis HTTP 403` 224,508 + `Tardis HTTP 403 code=274 concurrent-IP-lock` 9,818 = **797,323, 75.3%**) — **ALREADY
TRACKED**, matches `tardis_concurrent_ip_lockout_2026_07_12.md` /
`cefi_high_attempted_failed_batch_cluster_ 2026_07_23.md`'s own diagnosis; not re-filed. `VENUE_FETCH_FAILED` 219,071
(20.7%) not independently root-caused this run.

## 8. Distinct-value census + typed findings (taxonomy names, diffable against the 2026-07-20 report)

`suppressed_by` uses AE-n / `migration_pending` labels from `reconciliation-finding-taxonomy.md`. `[ELEVATED]` / `[BIG]`
marks a severity override with reason stated. `[SUPERSEDED]` marks a 2026-07-20 finding this run measured differently.

| #       | type                                                                                    | severity                                      | shard/location                                                                                                                                               | surfaces        | detector                                                                  | delete_elig | suppressed_by                                                                    | status                                                                    |
| ------- | --------------------------------------------------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------- | ------------------------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| FIND-00 | `divergent_empty`-shaped, taxonomy-gap (live capture-halt)                              | **[BIG] HIGH**                                | corpus-wide: `capture_status` by `date`, `attempted_at` max, Cloud Run job crash-loop                                                                        | S3 + live infra | manifest pivot + `attempted_at` max + `gcloud scheduler/run/logging` (§9) | n/a         | none                                                                             | **NEW — see §9, issue doc filed**                                         |
| FIND-01 | `non_canonical_path` (id-form leg) — **corroboration, not new**                         | MEDIUM (date-conditional / `unknown-vintage`) | DERIBIT legacy wire 2020, LIGHTER-ZKSYNC bare-integer (live)                                                                                                 | S1 (id-form)    | oracle re-test, §5                                                        | NO          | none (LIGHTER-ZKSYNC is ALREADY TRACKED as a fix-pending defect, not suppressed) | **PERSISTS + newly machine-caught**                                       |
| FIND-02 | shard-atom vocabulary fold (taxonomy-gap)                                               | MEDIUM                                        | manifest `instrument_type` column: `FUTURES_CHAIN`→`FUTURE`, `OPTIONS_CHAIN`→`OPTION` (post Surface-C canonicalize)                                          | S3              | census (§ below)                                                          | NO          | none                                                                             | **NEW — see discussion below**                                            |
| FIND-03 | `non_canonical_axis_value` (S3, minor)                                                  | LOW                                           | 3 non-UAC-registry venues in manifest: blank-venue (6 rows), `OKX-OPTIONS` (9 rows), `BYBIT-FUTURES` (3 rows) — 18/9,045,162 = 0.0002%                       | S3              | census vs `VENUES_BY_ASSET_GROUP["cefi"]`                                 | NO          | none                                                                             | NEW (bounded, tiny)                                                       |
| FIND-04 | `[SUPERSEDED]` C2a casing — measured CONVERGED, not `migration_pending`-mixed           | INFO                                          | manifest `instrument_type` column: **0/9,045,162 (0.00%) lowercase** — full UPPERCASE                                                                        | S3              | census                                                                    | n/a         | C2a (§5.1, but see caveat)                                                       | **NEW measurement — recommend register update, see discussion**           |
| FIND-05 | `[SUPERSEDED]` F8 (2026-07-20) `chain` column hygiene — now **RESOLVED**, not a finding | INFO                                          | manifest `chain` column: 0/9,045,162 populated (was 817,505 on 2026-07-20)                                                                                   | S3              | census + snapshot diff                                                    | n/a         | n/a — intentional                                                                | **RESOLVED, see discussion**                                              |
| FIND-06 | shard-atom integrity (blank KEY, single-pattern)                                        | LOW-MED                                       | 525 post-cutover rows with blank `instrument_id` AND blank `underlying` on `PERPETUAL`/`SPOT_PAIR`/`FUTURE`/`OPTION` types (up from 294 on 2026-07-20, +78%) | S3              | manifest, disambiguated via `underlying` populate-state (see FIND-02)     | NO          | none                                                                             | **PERSISTS, growing**                                                     |
| FIND-07 | `non_canonical_path` (pipeline_mode)                                                    | LOW                                           | 4 BYBIT rows, post-2026-05-19 (dates 2026-05-19..05-22), blank `pipeline_mode`                                                                               | S3              | manifest, date-split vs cutover register                                  | NO          | none                                                                             | **PERSISTS, EXACT SAME 4 ROWS** as 2026-07-20's F6 — unfixed 5 days later |
| FIND-08 | `source=` write-wiring gap (H6, known condition)                                        | KNOWN-CONDITION                               | 2,441,255 rows (26.99%) blank `source`                                                                                                                       | S3              | census                                                                    | NO          | none                                                                             | PERSISTS (was 27.3% on 2026-07-20)                                        |
| FIND-09 | shard-atom integrity (blank instrument_type on captured)                                | MEDIUM                                        | 5,232 captured rows w/ blank `instrument_type`                                                                                                               | S3              | manifest                                                                  | NO          | none                                                                             | **PERSISTS, IDENTICAL COUNT** to 2026-07-20                               |
| FIND-10 | observation — `COMBO` row-count growth                                                  | INFO                                          | DERIBIT `COMBO`: 662 (2026-07-20) → 13,065 (this run), all dates 2026-02-05..2026-07-20                                                                      | S3              | census                                                                    | n/a         | AE-2 (bare-underlying carve-out)                                                 | NEW observation, cause not independently confirmed this run (see §11)     |
| FIND-11 | `catalogue-freshness`                                                                   | INFO                                          | `prod/catalog.parquet` updated 2026-07-22 (3d old, reasonably fresh); `data-catalogue.instruments-service.yaml` NOT re-opened this run                       | S4              | blob metadata                                                             | NO          | none                                                                             | standing condition, unverified-since-2026-07-20 for the yaml leg          |
| FIND-12 | `masked_empty_row`                                                                      | MEDIUM (historical)                           | 127,606 `empty_confirmed` rows (5.04% of 2,533,470) with blank `error_reason`, latest 2026-04-18                                                             | S3              | manifest                                                                  | NO          | historical, pre-guard (taxonomy §2.5)                                            | HISTORICAL-ONLY, no post-guard occurrence found — not a fresh finding     |

### Discussion — FIND-02 (shard-atom vocabulary fold erases the pattern-#1/#2 distinction at S3)

The Surface-C v2 dedup's `_canonicalize_blob` step (per `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`
Finding 5's own description) folds the raw leaked `FUTURES_CHAIN`/`OPTIONS_CHAIN` `instrument_type` values into
post-canonicalisation `FUTURE`/`OPTION`. Measured this run: **the manifest column no longer carries the literal values
`futures_chain`/`options_chain`/`FUTURES_CHAIN`/`OPTIONS_CHAIN` anywhere** (full census: `PERPETUAL` 5,910,688,
`SPOT_PAIR` 1,989,366, `FUTURE` 571,286, `OPTION` 441,972, blank 118,785, `COMBO` 13,065 — six values total, all
UPPERCASE). This is **not itself wrong** — the fold is real progress toward one clean vocabulary — but it means a
`FUTURE`/`OPTION` row's `instrument_type` value **alone** no longer tells a downstream consumer whether the row is
pattern #1 (flat single, `instrument_id` required) or pattern #2 (bundle-per-underlying, `instrument_id` legitimately
`NULL` by design). This run had to fall back to checking `underlying` populate-state to disambiguate FIND-06's residual
(§ above) from the much larger, entirely-legitimate bundle population (6,256 of 6,781 post-cutover blank-`instrument_id`
`FUTURE`/`OPTION` rows have `underlying` populated — genuine pattern-#2 bundle rows, not a defect). **Any OTHER
consumer/gate that keys off `instrument_type ∈ {FUTURE, OPTION}` ⇒ "expect non-null instrument_id" will now
false-positive across the whole bundle population** unless it independently checks `underlying`. No closed taxonomy name
fits this precisely (it is a vocabulary-fold side-effect on the disambiguation surface, not a value that's outside the
canonical enum) — reported as a taxonomy-gap candidate, `shard_atom_grain_ambiguity_after_fold` or similar; flagged for
the taxonomy maintainer, not silently absorbed.

### Discussion — FIND-04 (C2a casing measured fully converged for cefi)

`reconciliation-finding-taxonomy.md` §5.1 / `canonical-cutover-register.md` §3c describe cefi's `instrument_type` COLUMN
casing as `migration_pending` (2026-07-20 measurement: ~99.41% adjusted upper, i.e. still mixed). **This run's direct
full-corpus census finds 0 lowercase rows — 100.00% UPPERCASE.** Per the skill's C2a suppression rule this axis is
compared case-insensitively regardless, so **no finding is emitted either way** — but the measurement itself is worth
recording because it may mean cefi's leg of the D1 migration has effectively completed. **Caveat, not asserted as
proven**: this run cannot rule out that the 100% figure is an incidental side-effect of the SAME Surface-C
`_canonicalize_blob` pass that produced FIND-02's fold (i.e., the dedup script may itself be uppercasing
`instrument_type` as part of its own canonicalization, independent of and prior to any dedicated D1 casing-migration
script actually running against cefi). Recommend whoever owns the D1 migration re-verify against
`instruments-service@555ddf1c`'s own dry-run/apply state before updating the register — this run did not check whether
that specific script has been applied to cefi.

### Discussion — FIND-05 (chain column drop — RESOLVED, not a regression)

The 2026-07-20 report's F8 flagged 817,505 cefi rows carrying a populated `chain` content column as a "display-column
residue... noted for hygiene," LOW severity. This run measured **0/9,045,162** populated. Investigated directly (not
assumed): the pre-apply snapshot (`pre_d4_20260724T232332Z/`) already showed only 2,701 populated (i.e. most of the
reduction pre-dates today's apply — an intervening, unidentified process already reduced 817,505→2,701 sometime between
2026-07-20 and 2026-07-24 23:23Z), and the Surface-C v2 apply itself finished the job to 0. Root cause confirmed by
reading `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py` directly: `--keep-chain` CLI flag,
`help="Keep the chain column. Default DROPS it for cefi (operator directive 2026-07-20: derive from UAC venue→chain on demand)."`
— **this is an intentional, operator-directed drop**, not silent data loss; the script's own docstring argues `chain` is
functionally dependent on `venue` for cefi (each perp-DEX venue maps to exactly one chain) so the UAC venue→chain
mapping can re-derive it on demand. **F8 is RESOLVED, not re-flagged.** Caveat: this run did not independently grep
every downstream reader of the manifest `chain` column to confirm none depends on the stored value rather than
re-deriving it — a "grep-then-READ" gap, declared in §11.

## 9. BIG FINDING — CeFi raw-tick capture appears HALTED since ≥2026-07-21, likely OOM-crash-looping since ≥2026-07-23

**This is the headline finding of this run and is being escalated per the workspace's data-pipeline-correctness HARD
RULE.** Evidence chain, in the order it was discovered:

**(a) Manifest `capture_status` × `date` pivot (2026-07-10 through 2026-07-24):**

| date       | attempted_failed | captured | empty_confirmed | expected_unattempted |
| ---------- | ---------------- | -------- | --------------- | -------------------- |
| 2026-07-18 | 127              | 1,204    | 1,765           | 16,606               |
| 2026-07-19 | 112              | 1,203    | 1,789           | 16,581               |
| 2026-07-20 | 118              | 1,227    | 1,745           | 16,571               |
| 2026-07-21 | **0**            | **5**    | 1,193           | 17,481               |
| 2026-07-22 | **0**            | **0**    | 1,182           | 17,484               |
| 2026-07-23 | **0**            | **0**    | 1,182           | 17,484               |
| 2026-07-24 | **0**            | **0**    | 1,182           | 17,484               |

A steady ~1,000-1,200 `captured`/day baseline (with normal `attempted_failed` noise ~110-140/day) collapses to 5 on
07-21, then **exactly 0 of BOTH `captured` and `attempted_failed`** for three consecutive days — zero of both, not just
zero success, means no write attempt of any kind landed, not merely that attempts are failing.

**(b) Corpus-wide `attempted_at` maximum: `2026-07-24T01:31:59.195992+00:00`** — across all 8,901,202 non-blank
`attempted_at` values in the full 9,045,162-row cefi manifest. At probe time (`~2026-07-25T00:41Z`) this is **~23 hours
stale**. No manifest row of ANY kind (success, failure, or migration-script write) has been attempted in that window.

**(c) `_index/per_vm/` staging (§3) contains exactly 1 file, and it is the migration script's own artifact** — not a
live capture writer's output. A healthy pipeline continuously deposits per-VM shard files here for the consolidator to
merge; this run found none.

**(d) Direct, read-only GCP checks (admin ADC, `central-element-323112`), triggered by (a)-(c):**

- `gcloud scheduler jobs list --location=asia-northeast1 | grep cefi` — the primary batch trigger
  `uts-prod-market-tick-data-service-cefi-t1-schedule` (`0 6 * * *`, ENABLED) and `market-tick-daily-trigger`
  (`0 9 * * *`, ENABLED) both show `lastAttemptTime` firing on schedule through 2026-07-24 (06:00:01Z / 09:00:06Z) —
  **the crons themselves are enabled and firing**. (A separate, differently-named job,
  `market-tick-cefi-daily-download`, is `PAUSED` since `2026-07-16T07:46:21Z` — over a week before the capture cliff —
  almost certainly a pre-existing, superseded/legacy job, not the cause; noted for hygiene, not escalated.)
- `gcloud run jobs executions list --job=uts-prod-market-tick-data-service-cefi-t1-recon` — the Cloud Run Job this
  trigger invokes shows `FAILED_COUNT=1` for **every** execution from at least 2026-07-15 through 2026-07-24 (20
  executions checked) — this specific count is **not new** and does not by itself explain the cliff (captures were
  healthy through 07-20 despite it).
- `gcloud logging read` on that job for 2026-07-24 09:00-09:04Z: the container logs ~15 lines of normal bootstrap
  (`ServiceRuntime: op=download mode=batch`, `ApiKeyReloader started: 24 venues`,
  `API keys validated for 3 data source(s): ['aster', 'hyperliquid', 'tardis']`) and then
  **`WARNING: Container terminated on signal 9`** — twice within the same execution window (a retry also killed) —
  **before any per-venue download work begins**. The identical pattern repeats at 2026-07-24 06:01-06:02Z, and at
  2026-07-23 06:01-06:02Z and 09:01-09:02Z. **Signal 9 is SIGKILL, consistent with an OOM kill.** The job's configured
  Cloud Run resources: **4 CPU / 8Gi memory** (`gcloud run jobs describe`).
- **The exact same "signal 9" text was searched for and NOT found in the 2026-07-20/21/22 logs** for this job — those
  earlier failures show only a single bare `ERROR`-severity log entry per execution with **no accompanying INFO
  bootstrap output at all** (unlike 07-23/24's ~15 lines before death) — i.e. a **different, earlier-stage failure
  signature**, not independently root-caused this run. **Do not read this as proof the 07-21/22 failures are the same
  OOM regression as 07-23/24** — flagged as an open sub-question, not asserted.

**What this run does NOT claim**: the exact code/config change that increased this job's memory footprint past 8Gi
starting ~2026-07-23 was not identified (would require reading `market-tick-data-service`'s recent commits/deploys — out
of this reconciliation's scope). Whether this Cloud Run job's container memory pressure is related to, or entirely
independent of, the _separate_ memory pressure `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md` documents
for the Surface-C dedup script (Finding 6: OOM-killed on a **shared operator dev host** and, separately, on a
**dedicated e2-standard-8 VM** — both explicitly DIFFERENT infrastructure from this isolated, 8Gi-limited Cloud Run Job)
was **not established** — they may be coincidental (same week, same general "heavy migration work" period) rather than
causally linked. **This finding is NOT documented anywhere in the cefi migration issue docs reviewed this run** — those
docs discuss the dedup script's OOMs on shared/VM infra, never this Cloud Run job's own crash-loop.

**Consequence:** CeFi raw-tick capture (live AND batch) has produced **zero new data** for at least 3 full days
(2026-07-22 through 2026-07-24) and is trending toward a 4th (2026-07-25, not yet elapsed at probe time). Every day this
continues is honest, permanent gap in the historical record for `expected_unattempted`/`empty_confirmed` cells that
should have converted to `captured`/`attempted_failed` — not recoverable by a later backfill of "today," since the
live/near-real-time capture window will have passed. **Filed as an issue doc**:
`plans/active/issues/cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md`. **Operator notified in this run's
final response per the data-pipeline-correctness HARD RULE.**

## 10. Phase-2 non-canonical inventory sweep (cefi-scoped) + delete dispositions

**Register → reality (re-verified live, this run):**

| inv # | location                                                                                                          | register disposition                                           | this run's verdict                                                                                                                                                                                                                    |
| ----- | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | legacy flat `market-data-tick-cefi-{pid}`, `instruments-store-cefi-{pid}`                                         | buckets gone (404)                                             | **CONFIRMED** — both `exists()=False`, unchanged since 2026-07-20.                                                                                                                                                                    |
| 16    | `instrument_availability/by_date/day={D}/venue={V}/instruments.parquet` FLAT (no `pipeline_mode=`/`asset_group=`) | `migration_pending` (R2, hive-grammar target ruled 2026-07-21) | **CONFIRMED still flat** — `instrument_availability/by_date/day=2026-07-19/venue=ASTER/instruments.parquet` etc., no hive keys. Unchanged.                                                                                            |
| 17    | `features-cefi-prd/delta_one/day=…` (no `by_date/`)                                                               | `migration_pending` (R1, ruled 2026-07-21)                     | Not independently re-probed this run (bucket top-level only listed — `_index/`, `delta_one/` present, consistent) — declared gap, §11.                                                                                                |
| 23    | dual `_migration_backup/` + `_migration_backups/`                                                                 | `unknown`                                                      | **CONFIRMED both still present**, PLUS the third spelling `_remediation_backups/` first flagged NEW by the 2026-07-20 report is **STILL present, 5 days later, still not folded into the register** — register-accuracy gap persists. |

**Delete suggestions: NONE rise above `unknown`.** No cefi-scoped location classifies as `legacy_duplicate` or `junk`
with a five-part proof this run. The legacy wire-named objects (shard C, §6) are `no-migrate-first` by definition — the
manifest holds a canonical re-key but the OBJECT is the only copy of that content; never delete. Prod-bucket deletes are
a human-only hard stop regardless.

**Orphans: NOT ASSESSED (no whole-corpus walk in this run, and no fresher pre-computed cefi orphan sweep was found to
reuse this run — unlike the concurrent defi run, which reused a 2026-07-23 sweep).** The pre-computed
`_index/audit/orphan_sweep_cefi.parquet`, if still current, was not re-checked for freshness this run — declared gap.

### Reality→register (new — register-patch stanza, per the concurrency clause; NOT applied inline this run)

```
| NEW | `market-data-tick-cefi-prd-{pid}/_vm_staging/{migration,mtds_backfill}/` | one-off migration-support codebase tarballs + backfill staging | canonical twin: n/a (operational, not data) | still-written-by: the Surface-C dedup/migration scripts (confirmed this run — `per_vm/_legacy_seed.parquet` under `_index/per_vm/`, a sibling operational tree) | disposition: `unknown` |
| NEW | `market-data-tick-cefi-prd-{pid}/backfill-logs/{feb-2020,jan-31-2020,missing-2020,nov-dec-2020,rest-of-2020,rest-of-2021,rest-of-2022,rest-of-2024}/` | operational log prefix at bucket root, 8 dated sub-trees, outside bucket-isolation-model's data namespaces | canonical twin: n/a | still-written-by: UNVERIFIED this run | disposition: `unknown` |
| NEW | `market-data-tick-cefi-prd-{pid}/_remediation_backups/{kraken_futures_collision_2026_07_08,kraken_futures_fi_ff_margin_collision_2026_07_10}/` | third operational-backup spelling, first surfaced by the 2026-07-20 report, still not in the register 5 days later | canonical twin: n/a | still-written-by: one-off remediation scripts (named by content) | disposition: `unknown` — recommend folding into inv row 23's existing "which spelling wins" open question rather than a fresh row |
| NEW | `market-data-tick-cefi-prd-{pid}/_quarantine/processed_candles/` | candle-LAYER quarantine tree — OUT OF SCOPE for this raw-tick dispatch | not evaluated | not evaluated | hand off to `--layer candles` |
```

## 11. Suppressed accepted-exceptions + coverage-gap section

**Suppressed (mandatory — counts, not re-listed as findings):**

| exception                                  | applies to cefi? | suppressed count / note                                                                                                                    |
| ------------------------------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| **C2a — `instrument_type` COLUMN casing**  | YES              | 0 lowercase found this run (see FIND-04 discussion — measured fully converged, still compared case-insensitively per the rule regardless). |
| **AE-2 — bare-underlying combo carve-out** | YES              | 13,065 `COMBO` rows (all DERIBIT) not flagged for their bare-underlying tail.                                                              |
| AE-1 sports blank pipeline_mode/source     | NO               | sports-only, N/A.                                                                                                                          |
| AE-5 / decision-D defi `LENDING`           | NO               | defi-only, N/A.                                                                                                                            |
| `masked_empty_row` historical-only rule    | YES              | 127,606 pre-guard rows (FIND-12), latest 2026-04-18 — no post-guard occurrence, not flagged.                                               |

**Coverage gaps (declared — what this run did NOT reach):**

1. **Filename id-form full distribution** — only 6 shards S1-sampled; the oracle now machine-checks id-form (§5) but a
   corpus-wide id-form % was NOT computed this run (would need the single walk, route 3 — none available to reuse).
2. **Orphans — NOT ASSESSED.** No fresher pre-computed cefi orphan sweep found to reuse; a fresh walk was out of scope
   (single-walk discipline + this run's time budget).
3. **Chain-tail v5/v6 (register §6c)** — NOT independently confirmed on an actual bundle-shaped object this run; only
   the manifest-side (blank-`instrument_id`, populated-`underlying`) signal was checked (§8 FIND-02 discussion).
4. **S4 per-instrument catalogue↔manifest window join** — not run (venue/day-grain-only bucket reachability check).
5. **H5 — `instruments-store-cefi` phantom coverage** — absent from the phantom reconciler's bucket map (per the
   2026-07-20 report); not independently re-verified this run.
6. **`features-cefi-prd/delta_one/`** (inv row 17) — top-level presence only, not re-probed for the `by_date/` migration
   state this run.
7. **`chain`-column downstream-reader grep** (FIND-05 discussion) — this run confirmed the DROP is
   operator-directed/intentional via the script's own docstring, but did NOT independently grep every consumer of the
   manifest `chain` column to confirm nothing still reads the now-blank value expecting it populated.
8. **`COMBO` row-count growth (662→13,065, FIND-10)** — measured, not root-caused; could be legitimate capture growth, a
   re-key side-effect of the same canonicalization pass that produced FIND-02, or something else.
9. **The 2026-07-21/22 capture-halt failure signature** (§9) — NOT confirmed to be the same "signal 9" OOM pattern as
   07-23/24; the underlying application code change (if any) that increased the Cloud Run job's memory footprint was NOT
   identified.
10. **No coverage percentage computed per-day** — §7's `reachable_coverage` is over the FULL manifest, not scoped to any
    particular day-window; a day-scoped MVP coverage figure (comparable to `cefi-capture-universe.md`'s
    operator-accepted ceiling) was not recomputed this run.

## 12. Verdict

**Is asset_group=cefi 100% canonical? No — and the more urgent finding this run surfaced is that the estate has stopped
GROWING, not just that it isn't yet clean:**

- **Structural + id-form canonicality (this run's own oracle re-test, sampled — not a corpus claim):** the machine
  oracle now covers BOTH surfaces for cefi (§5) and found genuine, already-tracked id-form defects (LIGHTER-ZKSYNC
  bare-integer filenames, legacy DERIBIT wire-named 2020 objects) alongside genuinely clean flat-pattern shards
  (HYPERLIQUID, ASTER, DERIBIT dated futures). A corpus-wide id-form % was not computed this run (needs the single walk)
  — the 2026-07-20 report's independently-measured **20.82%** filename-id-form figure is the most recent corpus-scale
  number available, and it predates this run's discovery that the oracle can now measure it directly going forward.
- **Coverage:** `reachable_coverage` = **52.61%** (LOWER BOUND), up from 44.85% on 2026-07-20 — but driven partly by a
  **12.0% shrinkage in the manifest denominator** from an intervening dedup, not purely new capture (§7).
- **The single most decision-relevant fact for whoever owns cefi operationally right now**: raw-tick capture
  (live+batch) has written **zero new manifest rows of any kind** for the last ~23 hours as of this probe, and **zero
  `captured` rows for 3 straight days** (2026-07-22 through 2026-07-24), with a Cloud Run job crash-looping on apparent
  OOM (signal 9) on every attempt since at least 2026-07-23. **This is not a canonicalisation gap — it is a live
  production capture outage**, and it is not mentioned in any of the actively-worked cefi migration docs this run
  reviewed. See §9 and the filed issue doc.
- Smaller, real, persisting defects: the exact-same 4 post-cutover blank-`pipeline_mode` BYBIT rows as 2026-07-20
  (unfixed 5 days later); a growing (294→525) residual of blank-KEY singles; the known Tardis-403 attempted_failed
  cluster (already tracked); a register-accuracy gap on `_remediation_backups/` (flagged 2026-07-20, still unfolded).
- **Positive, resolved, or superseded since 2026-07-20**: the `chain`-column hygiene finding (F8) is RESOLVED
  (intentional operator-directed drop); `instrument_type` COLUMN casing measured fully converged (0% lowercase); the
  DERIBIT dated-futures chain-bundle shape appears to have migrated to flat-per-contract (no chain-tail found on the
  sampled day); the oracle's id-form blindness for cefi is CLOSED.
- **No new delete is authorized.** No cefi-scoped location clears the five-part proof this run.
