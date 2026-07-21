---
doc_type: audit-result
title: "Data-pipeline reconciliation — defi (2026-07-20)"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=defi over PROD buckets only (read-only). Representative
  sample scoped to day=2026-04-14 (frozen Solana relic day) plus the legacy top-level trees. All three prod buckets
  reachable; oracle behaves as documented; two unruled axes (C2a instrument_type column case, decision-D lending keying)
  REFUSED; dex_pools/ + lending_indices/ delete = no-migrate-first (twin-less SOLEND/KAMINO confirmed).
status: partial
nature: record
asset_group: [defi]
stage: [data]
repos:
  [
    unified-trading-pm,
    unified-api-contracts,
    unified-trading-library,
    market-tick-data-service,
    instruments-service,
    execution-service,
  ]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, four-surface, defi, delete-safety, non-canonical-paths, manifest]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
    defi_dex_pools_delete_order_stale_2026_07_20,
  ]
created: 2026-07-20
resulting_plan:
lib_version:
doc_versions_checked:
audited_scope:
  "asset_group=defi, PROD (-prd-) buckets only, read-only; sample = day=2026-04-14 four-surface + legacy top-level sweep"
date: 2026-07-20
auditor: /data-pipeline-reconciliation (first real execution + acceptance test)
parent_epic: infrastructure_master
severity: P1
skill: data-pipeline-reconciliation
run_date: 2026-07-20
generated_at: 2026-07-20T00:00:00+00:00
---

# Data-pipeline reconciliation — defi (2026-07-20)

**Read-only.** No GCS writes, no manifest writes, no deletes, no backfills, no VM launches, no `--apply`. Deletes below
are SUGGESTIONS only; every prod-bucket delete is a human-only hard stop.

## 0. Declared sample scope (honest partial pass)

This is **not** a full-corpus reconciliation (neither possible nor desired in one pass — the live `_index` is 51.9M rows
/ 1.66 GiB). The sample was chosen to exercise **every surface and every reference-sheet hazard (H1–H8)** and to
confirm/refute each inventory entry scoped to defi.

**Sampled:**

1. `day=2026-04-14`, `pipeline_mode=batch_onchain_subgraph`, `asset_group=defi` — the frozen Solana relic day used by R5
   and the dex_pools issue doc. Four surfaces compared for venues ORCA, RAYDIUM, KAMINO, PHOENIX, YEARN_V3, YEARNV3.
2. Manifest `_index` scoped read: **64,009 rows** for `(date=2026-04-14, asset_group=defi)` (predicate pushdown, 6s) —
   full 4-state census for that day.
3. Machine oracle (`canonical_path_violations`) run on 8 real/derived paths at both `require_pipeline_mode` settings.
4. Legacy top-level trees `dex_pools/` + `lending_indices/` (H2 five-part proof inputs).
5. Catalogue `prod/catalog.parquet` (11,827 rows) + the `prd/` shadow (S4).
6. Top-level (non-recursive) sweep of all three defi prod buckets (Phase-0 reachability + inventory rows 2, 7, 8, 23,
   24).

**NOT sampled (declared gaps, see §7):** the other ~2,300 defi days; every non-Solana venue's four-surface content (S2
read only for ORCA + KAMINO); features-defi `onchain/` content; a whole-corpus orphan walk (route-3, not run — orphans
therefore `NOT ASSESSED`, per `orphan-object-detection.md` §3).

## 1. Bucket paths table (auto-derived from the resolver + probes)

Every bucket resolved via `resolve_bucket_name(cloud="gcp", kind=<k>, asset_group="defi", deployment_env="prd")` over
`configs/cloud-providers.yaml` (project via `GCP_PROJECT_ID=central-element-323112`; tier passed explicitly, never
env-mutated). No `-test-` name resolved.

| Surface / layer          | `kind`                    | Resolved bucket                                     | Reachable?           | Read targeted                                              |
| ------------------------ | ------------------------- | --------------------------------------------------- | -------------------- | ---------------------------------------------------------- |
| raw tick (S1/S2)         | `market-data`             | `market-data-tick-defi-prd-central-element-323112`  | YES (top-level ls=0) | raw_tick_data/, dex_pools/, lending_indices/               |
| raw tick alias           | `tick-data`               | `market-data-tick-defi-prd-central-element-323112`  | YES (same bucket)    | —                                                          |
| manifest (S3)            | (same market-data bucket) | `market-data-tick-defi-prd-central-element-323112`  | YES                  | `_index/availability_index.parquet` (1.66 GiB, 51.9M rows) |
| reference/catalogue (S4) | `instruments-store`       | `instruments-store-defi-prd-central-element-323112` | YES                  | `prod/catalog.parquet`, `prd/catalog.parquet`              |
| features                 | `features`                | `features-defi-prd-central-element-323112`          | YES (top-level ls=0) | top-level only (`onchain/`, `_index/`)                     |

**Removed per-datatype kinds** (`dex-pools`, `lst-rates`, `gas-fees`, …) correctly **RAISE** `BucketNamingError` — the
consolidated `market-data-tick-defi` bucket is the one live defi data bucket (reference sheet confirmed). **No bucket
was unreachable.**

## 2. Machine oracle behaviour (structure only — id-form NOT machine-checked)

`canonical_path_violations()` is the sole authority; probed vocabulary enumerated from
`canonical_path_templates("defi")` (22 templates) + the writer (`dex_pools_handler.py:231-233`). **The oracle drops the
leaf filename and validates STRUCTURE only; no defi id-form checker exists** (§4.3 stem rule is tradfi-gated). Surface-A
id-form was therefore **not machine-checked** for defi — reported as `unknown-vintage` per cutover register §5 (defi
leaf axis effective-from = UNKNOWN, writer not resumed).

| Path (real / derived)                                | require_pm=False | require_pm=True    | Verdict                             |
| ---------------------------------------------------- | ---------------- | ------------------ | ----------------------------------- |
| canonical ORCA `solana_amm_pool/dex_pool_state`      | CANONICAL        | CANONICAL          | structure OK                        |
| canonical KAMINO `lending/lending_indices`           | CANONICAL        | CANONICAL          | structure OK                        |
| `venue=YEARNV3/…` (glued V-digit; **objects exist**) | glued-V flagged  | glued-V flagged    | `non_canonical_path`                |
| `venue=AAVEV3/…` (glued V-digit)                     | glued-V flagged  | glued-V flagged    | `non_canonical_path`                |
| `venue=MORPHOVAULTS/…` (spelling dup, no digit)      | CANONICAL        | CANONICAL          | structurally clean; venue-vocab dup |
| legacy `dex_pools/…` top-level                       | prefix violation | prefix violation   | `non_canonical_path`                |
| legacy glued `venue={V}-{CHAIN}/ticks_migrated` (H5) | venue-chain glue | glue + missing pm  | `non_canonical_path`                |
| bare no-`pipeline_mode`                              | CANONICAL        | pm-missing flagged | §4.1 gate-weaker-than-codex         |

Cutover gate used for the sampled day: `require_pipeline_mode=False` (day=2026-04-14 **< 2026-05-19** defi
`require_pipeline_mode` effective-from). All sampled canonical cells carry `pipeline_mode=` regardless.

## 3. Per-surface verdict per shard (four surfaces = four bits, never collapsed)

Legend: `OK` · `NON-CANON` · `ABSENT` · `SUPPRESSED` (accepted exception) · `NOTE` (data-quality observation) ·
`NOT-READ` (outside sample) · `REFUSED` (unruled axis).

| #   | shard atom (day=2026-04-14, pm=batch_onchain_subgraph)                      | S1 path                          | S2 content                                                            | S3 manifest                                                                                                | S4 catalogue                         | notes                                                         |
| --- | --------------------------------------------------------------------------- | -------------------------------- | --------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------ | ------------------------------------------------------------- |
| 1   | `ORCA/SOLANA/solana_amm_pool/dex_pool_state` (14,094 obj)                   | OK (id-form unknown-vintage)     | SUPPRESSED (two-id, AE-3) + NOTE `canonical_instrument_id` col absent | NOTE `captured` but `row_count=0`                                                                          | OK (ORCA 132 rows, canon spelling)   | leaf=raw address; S2 col=`ORCA-SOLANA:SOLANA_AMM_POOL:<addr>` |
| 2   | `RAYDIUM/SOLANA/solana_amm_pool/dex_pool_state` (100 obj)                   | OK                               | NOT-READ                                                              | NOTE dual vocab: `solana_amm_pool` captured **+** `pool` expected_unattempted (never satisfiable)          | OK                                   | expected-universe seeded with wrong writer vocab (H1 class)   |
| 3   | `KAMINO/SOLANA/lending/lending_indices` (47 obj)                            | OK                               | SUPPRESSED (`SOLANA_LENDING` id, AE-5)                                | REFUSED (decision D) + NOTE `it=pool/POOL` noise rows                                                      | OK (KAMINO 114 rows)                 | flat LENDING keying — do not flag                             |
| 4   | `PHOENIX/SOLANA/solana_amm_pool/dex_pool_state` (3 obj)                     | OK                               | NOT-READ                                                              | `captured` row_count=0 NOTE                                                                                | NOT-READ                             | —                                                             |
| 5   | `YEARN_V3/ETHEREUM/yield_bearing/vault_share_price` (canonical spelling)    | OK                               | NOT-READ                                                              | NOTE blank `instrument_id`, rows nan; **pm↔source desync** (`pm=batch_onchain_rpc` src=`onchain_subgraph`) | OK (6 rows)                          | —                                                             |
| 6   | `YEARNV3/ETHEREUM/yield_bearing/vault_share_price` (**non-canon spelling**) | **NON-CANON** (glued-V)          | NOT-READ                                                              | `captured`, blank `instrument_id`, rows nan                                                                | **ABSENT** (no YEARNV3 in catalogue) | `non_canonical_path` + `manifest_only`                        |
| 7   | legacy `dex_pools/{kamino,orca,raydium}/SOLANA/date=2026-04-14/` (2 ea)     | **NON-CANON** (top-level prefix) | not content-verified here (R5 did)                                    | ABSENT (no manifest row)                                                                                   | n/a                                  | `non_canonical_path`; delete=`no-migrate-first`               |
| 8   | legacy `lending_indices/{kamino,solend}/SOLANA/date=2026-04-14/` (1 ea)     | **NON-CANON** (top-level prefix) | not content-verified here                                             | ABSENT                                                                                                     | n/a                                  | `non_canonical_path`; delete=`no-migrate-first`               |

## 4. Typed findings (taxonomy names only — diffable)

Formula for any coverage %: `reachable_coverage = captured / (captured + attempted_failed + expected_unattempted)`,
`empty_confirmed` **EXCLUDED** (honest-coverage-model, CK3-certified). Every % is a **LOWER BOUND**
(`instrument_gates_download=true` for all AGs).

| #   | type                                                        | severity                          | shard / location                                                                                                                                                                 | surfaces      | detector                                       | delete_elig            | notes                                                                                           |
| --- | ----------------------------------------------------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------- | ---------------------------------------------- | ---------------------- | ----------------------------------------------------------------------------------------------- |
| F1  | `non_canonical_path`                                        | MEDIUM                            | `venue=YEARNV3` (glued-V) + `venue=AAVEV3`; **objects exist** (YEARNV3=4 parquet/day)                                                                                            | S1            | `canonical_path_violations` (oracle-confirmed) | NO                     | canonical twins `YEARN_V3`/`AAVE_V3` exist same day → coverage fragmentation                    |
| F2  | `non_canonical_path`                                        | MEDIUM                            | legacy top-level `dex_pools/` + `lending_indices/` (8 obj/day)                                                                                                                   | S1            | oracle (prefix clause) + live probe            | NO (not on this alone) | see F3 for delete disposition                                                                   |
| F3  | `legacy_duplicate`                                          | LOW (correctness) / MEDIUM (cost) | `dex_pools/{orca,raydium}` + `lending_indices/kamino` (twin present, PARTIAL)                                                                                                    | S1↔S3         | live twin re-probe + issue doc R5              | YES (eligible only)    | **disposition = `no-migrate-first`**; Parts 1/2/4 fail — see §5                                 |
| F4  | `orphan_real` (candidate)                                   | HIGH                              | `dex_pools/kamino` (solana_vault twin=0), `lending_indices/solend` (twin=0)                                                                                                      | S1, S3 absent | live twin re-probe                             | **NO — only copy**     | legacy is the sole copy; DO-NOT-DELETE                                                          |
| F5  | `catalogue_gap` / `manifest_only`                           | MEDIUM                            | dup-spelling venues (YEARNV3, MORPHOVAULTS, MORPHO_VAULTS, AAVEV3, COMPOUND) present on disk+manifest, **absent from catalogue**                                                 | S4↔S3         | catalogue vs manifest venue set                | NO                     | catalogue carries canonical spellings only                                                      |
| F6  | `divergent_empty`-adjacent (expected-universe vocab desync) | HIGH                              | RAYDIUM `it=pool` rows `expected_unattempted` vs writer `it=solana_amm_pool` `captured`                                                                                          | S3 vs writer  | scoped manifest read + writer code             | NO                     | `pool`/`POOL` expected rows never satisfiable (H1 class on expected side); inflates denominator |
| F7  | `manifest_infra`                                            | INFO                              | `_index/consolidator.lock` present; `latest.json` last run `verdict=empty, error_reason="locked", shards_scanned=0` (2026-07-20)                                                 | S3            | JSON read                                      | NO                     | corroborates H4 (rebuild/consolidator stalled; capture STOPPED)                                 |
| F8  | `phantom`                                                   | HIGH                              | defi `phantom_count=1558` (published `_index/phantom_audit_latest.json`, 2026-07-19)                                                                                             | S3↔S1         | read published audit (not re-run)              | NO                     | flip captured→attempted_failed remediation (not this skill)                                     |
| F9  | data-quality NOTE (row_count)                               | MEDIUM                            | sampled `captured` rows carry `row_count=0`/`nan` while parquet has content (ORCA parquet = 3 rows)                                                                              | S3 vs S2      | scoped read + parquet read                     | NO                     | manifest `row_count` not populated; NOT a confirmed phantom (content present)                   |
| F10 | pipeline_mode↔source desync                                 | MEDIUM                            | YEARN_V3 row `pipeline_mode=batch_onchain_rpc` but `source=onchain_subgraph`                                                                                                     | S3            | scoped read                                    | NO                     | breaks SOURCE-AWARE `{mode}_{source}` invariant                                                 |
| F11 | catalogue-freshness / orphan                                | LOW                               | `instruments-store-defi-prd/prd/catalog.parquet` (single stale object @2026-06-28) shadowing live `prod/`                                                                        | S4            | top-level ls                                   | NO (human-only)        | inventory row 2 confirmed; report once                                                          |
| F12 | S2 contract gap NOTE                                        | MEDIUM                            | defi parquet content lacks a `canonical_instrument_id` column; only `instrument_id` (= symbolic composite) present; catalogue `canonical_instrument_id` holds bare `0x…` address | S2 vs S4      | parquet read + catalogue read                  | NO                     | cross-surface id-form inconsistency; AE-3-adjacent — see critique                               |

## 5. Delete suggestions (SUGGESTIONS ONLY — all prod-bucket deletes human-only)

Only `legacy_duplicate` + `junk` are ever delete-eligible. The one eligible candidate this run touched:

```
Location:            gs://market-data-tick-defi-prd-.../dex_pools/ + lending_indices/  (legacy top-level, day=2026-04-14 relic)
Part 1 twin probe:   dex_pools/{orca}=14094, {raydium}=100  RESOLVE; SOLEND lending=0, KAMINO solana_vault dex_pool=0 -> None (ABSENT)
Part 2 content:      NOT re-verified this run (R5 measured: legacy=98 canon=99 intersection=66, 32 legacy-only high-TVL) -> FAIL by default
Part 3 writers:      NONE-FOUND (write_defi_rows emits canonical; dex_pools_handler docstring is STALE, code READ)
Part 4 readers:      execution-service/.../solana_amm_depth_provider.py:41 _DEX_POOLS_PATH_TEMPLATE + :258 -> READS (code, not docstring) -> FAIL
Part 5 twin coverage: PARTIAL (<100%) — SOLEND lending + KAMINO dex_pool have NO twin
Disposition:         no-migrate-first
Hard stop:           prod-bucket + defi-dex_pools (human-only, two live plan docs' delete order is STALE)
```

**Verdict: `no-migrate-first` — DO NOT DELETE.** Parts 1, 2, 4 all fail. Fold order per
`defi_dex_pools_delete_order_stale_2026_07_20.md` (content-union → repoint execution-service + fix its raising
`resolve_bucket_name` call → only then consider delete).

## 6. Suppressed accepted-exceptions (suppression is mandatory — shown as counts, not re-listed)

| AE             | condition                                                                         | suppressed occurrences in sample                                                  |
| -------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| AE-3           | defi two-id POOL divergence (`instrument_id`≠`canonical_instrument_id`, Option A) | all POOL/`solana_amm_pool` rows sampled (ORCA 14,094 + RAYDIUM 100 + PHOENIX 3)   |
| AE-5           | defi interim flat `LENDING`/`SOLANA_LENDING` on market/event data_types           | KAMINO lending cell (47 obj) + all `lending`/`liquidation` manifest rows this day |
| AE-1/AE-2/AE-4 | sports/tradfi exceptions                                                          | 0 (out of defi scope)                                                             |

## 7. REFUSED axes (unruled — no finding, no migration proposed)

- **[C2a] manifest `instrument_type` COLUMN casing** — REFUSED. Confirmed LIVE in defi: the sampled day carries BOTH
  `LENDING`/`lending`, `POOL`/`pool`, `PERPETUAL`/`perpetual`, `SPOT_PAIR`/`spot_pair`, `STAKING`/`staking`,
  `YIELD_BEARING`/`yield_bearing`. Compared case-insensitively; no casing migration proposed (>12M-row blast radius,
  both sides cite the same operator/date). Path segment (lowercase) + id middle segment (UPPER) remain settled/enforced.
- **[decision D] defi market/event `LENDING` keying** — REFUSED. `lending_indices`/`liquidation_events` etc. keyed to
  market-level `LENDING`/`SOLANA_LENDING`; not flagged.

## 8. Coverage gap section (what was NOT reached + why)

1. **Orphans: `NOT ASSESSED`** — orphan enumeration requires the route-3 whole-corpus walk
   (`migration_orphan_sweep.py`), which was **not run** (single-walk discipline; no new whole-corpus walk). Per
   `orphan-object-detection.md` §3 the honest verdict is `NOT ASSESSED`, never `0 orphans`. F4 candidates were found via
   targeted twin re-probe, not enumeration.
2. **Temporal**: only `day=2026-04-14` compared four-surface; ~2,300 other defi days not scanned. The 64,009-row scoped
   manifest census is for that one day.
3. **S2 content**: read for ORCA + KAMINO only; RAYDIUM/PHOENIX/YEARN(V3) content not read.
4. **features-defi**: top-level reachability only; `onchain/` content not reconciled.
5. **H5 legacy glued-flat `ticks_migrated_*.parquet` tree**: NOT reproduced under `day=2026-04-14/asset_group=defi/` —
   inventory row 9 remains UNVERIFIED (needs a probe on its own frozen day; discovery=0 by construction).
6. **Manifest rebuild**: consolidator is LOCKED/no-op (F7); the live `_index` reflects the last successful
   consolidation, not a fresh rebuild (H4 — rebuild crashes on `MalformedRowKeyError`).

### Coverage number (formula named, lower bound)

`reachable_coverage(day=2026-04-14, defi) = 40,724 / (40,724 + 193 + 16,806) = 70.55%` — `empty_confirmed=6,286`
EXCLUDED. **LOWER BOUND** (`instrument_gates_download=true`). This is a single-day sample figure, **not** a corpus
coverage. The defi denominator basis is the per-shard manifest 4-state; the corpus `expected_unattempted` seed is 63.9M
(H7) — **not** the understated 1.38M — and no coverage % here is derived from 1.38M.

## 9. Inventory reconcile (register ⇄ reality, defi-scoped)

| inv row | location                               | register disposition   | this run                                                        |
| ------- | -------------------------------------- | ---------------------- | --------------------------------------------------------------- |
| 2       | `prd/catalog.parquet` shadow           | yes-after-verify       | CONFIRMED present (single stale object @2026-06-28)             |
| 7       | `dex_pools/` top-level                 | no-migrate-first 🔴    | CONFIRMED; twins re-probed (ORCA/RAYDIUM present, KAMINO dex=0) |
| 8       | `lending_indices/` top-level           | no-migrate-first 🔴    | CONFIRMED; SOLEND twin=0, KAMINO lending twin=47                |
| 9       | glued-flat `ticks_migrated` tree       | no-migrate-first       | NOT reproduced on sampled day — UNVERIFIED stands               |
| 16      | `instrument_availability/` flat writer | no-still-authoritative | top-level present; content not deep-probed                      |
| 23      | dual `_migration_backup(s)/`           | unknown                | CONFIRMED both present, distinct contents                       |
| 24      | `_needs_attribution/day=…/`            | unknown                | CONFIRMED (`day=2021-02-24/…`)                                  |

**Reality→register (new):** F10 (pipeline_mode↔source desync) and F6 (expected-universe `pool` vs writer
`solana_amm_pool` vocab desync producing permanently-unsatisfiable `expected_unattempted` rows) are not in the register
as defi-scoped rows; both should be appended by the register's maintenance contract (not done in this read-only run —
flagged as follow-up).

## 10. Verdict

defi is **structurally canonical on the sampled canonical cells** (oracle clean) but **NOT id-form-verified** (no defi
leaf id-form oracle; leaf = address/UUID, `unknown-vintage`). Live non-canonical residue is real and bounded: glued-V
venue spellings (F1), the DO-NOT-DELETE legacy Solana trees (F2/F3/F4), catalogue↔manifest venue-spelling divergence
(F5), and two manifest data-quality defects (F6 vocab-desync, F10 pm↔source, plus F9 row_count). Capture is STOPPED and
the consolidator is stalled (F7/H4), so recency gaps are expected, not findings. Two axes REFUSED pending operator
ruling. No delete is authorized: the one eligible candidate is `no-migrate-first`.
