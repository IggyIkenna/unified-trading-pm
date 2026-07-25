---
doc_type: audit-result
title: "Data-pipeline reconciliation — defi (2026-07-24), raw-tick layer"
summary: >-
  Four-surface canonicalisation reconciliation of asset_group=defi, raw-tick layer, over PROD buckets only (read-only,
  Phases 0->2). Headline: DeFi capture is NOT stopped — batch writers are actively producing NEW objects through
  day=2026-07-24 (today), contradicting the register's "capture STOPPED, no new writes" premise. The shipped
  write_defi_rows() leaf-naming (R1, market-tick-data-service@4ca2640d) writes the bare SYMBOL as the filename, not the
  ruled full canonical_instrument_id, so the UAC oracle's id-form check (shipped uac@d40c5d7d 2026-07-20, refined
  @1cd27478 2026-07-23) now flags every sampled EVM single-instrument object as non-canonical (13/13 sampled). Reusing
  the most recent full-corpus orphan sweep (2026-07-23, read not re-run): only 30.84% of defi's 24.89M raw-tick objects
  are canonical_manifested; 63.74% are orphan_real (present on disk, zero manifest coverage, never delete-eligible).
  Several findings corroborate already-open plan/issue-doc work (KALSHI_PERP/POLYMARKET_PERP misclassification,
  MORPHOVAULTS/MORPHO_VAULTS vocab desync); two are new (the write_defi_rows leaf defect, and a register-accuracy
  correction on `_needs_attribution/`). No deletes executed or newly authorized; dex_pools/lending_indices legacy trees
  reconfirmed at 0 objects (2026-07-21 delete holds).
status: partial
nature: record
asset_group: [defi]
stage: [data]
repos:
  [unified-trading-pm, unified-api-contracts, unified-trading-library, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, four-surface, defi, delete-safety, non-canonical-paths, manifest, raw-tick]
related:
  [
    four-surface-reconciliation-procedure,
    reconciliation-finding-taxonomy,
    gcs-and-manifest-delete-safety-protocol,
    non-canonical-path-inventory,
    canonical-cutover-register,
    orphan-object-detection,
    data_pipeline_reconciliation_defi_2026_07_20,
    defi_track01_per_instrument_and_canon_id_2026_07_24,
    defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23,
    defi_orphan_sweep_test_artifact_prod_leak_2026_07_24,
  ]
created: 2026-07-24
resulting_plan:
lib_version:
  "unified-api-contracts 0.72.1.dev578+gc2b303f7e / unified-trading-library 0.56.1.dev347+g14301571d /
  market-tick-data-service 0.92.1.dev848+g3fb95eafa.d20260724"
doc_versions_checked:
audited_scope:
  "asset_group=defi, layer=raw-tick, PROD (-prd-) bucket only, read-only, Phases 0->2 per the
  /data-pipeline-reconciliation skill; sampled days 2026-07-22 (primary four-surface), 2026-07-23/2026-07-24
  (corroboration spot-reads), 2020-06-15 (historical census sample)"
date: 2026-07-24
auditor: /data-pipeline-reconciliation (dispatched sub-agent run)
parent_epic: infrastructure_master
severity: P0
skill: data-pipeline-reconciliation
run_date: 2026-07-24
generated_at: 2026-07-25T00:14:00+00:00
---

# Data-pipeline reconciliation — defi (2026-07-24), raw-tick layer

**Read-only.** No GCS writes, no manifest writes, no deletes, no backfills, no VM launches, no `--apply`. Deletes below
are SUGGESTIONS only; every prod-bucket delete is a human-only hard stop. This run is Phases 0→2 only,
`--layer raw-tick` (default; candles explicitly out of scope per dispatch).

## 0. Declared sample scope (honest partial pass)

Not a full-corpus four-surface walk (2,397 days on disk, 2020-01-01→2026-07-24; the live consolidated `_index` is ~1.15
GiB). Sampled to exercise every surface plus the specific hazards this run's Phase-0 census surfaced:

1. **`day=2026-07-22`** — primary four-surface day. Manifest scoped read: **2,644 rows** (predicate-pushdown, per-VM-
   shard fallback — see §2). GCS census via bounded delimiter descent (**198 `list_blobs` calls**, no parquet bytes, no
   leaf names read for the census itself — no-walk route #2).
2. **`day=2026-07-24` (today) + `day=2026-07-23`** — targeted spot-reads to establish write recency (object
   `time_created`) and confirm/refute the register's "capture STOPPED" premise.
3. **`day=2020-06-15`** — one historical (pre-cutover) day, census only, to surface any pre-hygiene vocabulary drift.
4. **13 real on-disk parquet objects** fetched for S1↔S2 comparison + oracle id-form testing (UNISWAP_V3
   `dex_pool_swaps` ×5, UNISWAP_V2 `dex_pool_state` ×8) — well under the Tier-1 ≤500-object cap. **SAMPLED, not the full
   corpus.**
5. **Reused** the most recent full-corpus artifact available (2026-07-23 terminal orphan sweep, `24,890,959` objects)
   via its published results in `plans/active/issues/defi_orphan_sweep_test_artifact_prod_leak_2026_07_24.md` — **read,
   not re-run** (single-walk discipline, sanctioned route #3).
6. Top-level (non-recursive) + one-level-deep bounded sweep of the defi prod bucket (Phase-0 reachability + Phase-2
   register reconciliation).

**NOT sampled (declared gaps, §8):** the other ~2,394 defi days at four-surface grain; S4 catalogue (not independently
re-probed this run — see the 2026-07-20 report for the last direct read); a Tier-2 100%-corpus id/schema VM campaign
(this run stayed Tier-1 by default, not dispatched under `/autonomous`).

## 1. Bucket paths table

Resolved via `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi", deployment_env="prd")` over
`cloud-providers.yaml` (`GCP_PROJECT_ID=central-element-323112` set in env; tier passed explicitly via
`deployment_env=`, never env-mutated). No `-test-` name resolved.

| Surface / layer  | `kind`                                                                                          | Resolved bucket                                    | Reachable?                                                       | Read targeted                                                                                                                                                                                                     |
| ---------------- | ----------------------------------------------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| raw tick (S1/S2) | `market-data`                                                                                   | `market-data-tick-defi-prd-central-element-323112` | **YES** — non-recursive top-level ls, 12 prefixes / 0 root blobs | `raw_tick_data/by_date/`, `_index/`, `dex_pools/`, `lending_indices/`, `_needs_attribution/`, `_vm_staging/`, `agent-sample-test-jupiter/`, `backfill-logs/`, `configs/`, `_migration_backup(s)/`, `_quarantine/` |
| manifest (S3)    | (same bucket)                                                                                   | `market-data-tick-defi-prd-central-element-323112` | YES                                                              | `_index/availability_index.parquet` (slim, column-projected, date-filtered reads)                                                                                                                                 |
| S4 catalogue     | not read this run — see 2026-07-20 report (`instruments-store-defi-prd-central-element-323112`) | —                                                  | NOT RE-PROBED                                                    | declared coverage gap, §8                                                                                                                                                                                         |

**Dispatch-provided pre-verification** ("All 5 buckets confirmed reachable... at dispatch time") is consistent with this
run's own independent reachability probe for the defi bucket specifically (top-level listing succeeded, resolved name
matches the dispatch note exactly).

## 2. Index freshness / lock state — every S3 count in this report is a LOWER BOUND

This is a Phase-0 gate item, not a footnote — the consolidator was **actively contended for the entire duration of this
run**:

- `_index/consolidator.lock` — **HELD** at probe time:
  `{"started_at": "2026-07-24T23:52:40.380244+00:00", "instance": "1-52d4b36b"}` (a different process/instance than this
  audit).
- `_index/latest.json` — last consolidator run at `2026-07-24T23:54:47.121864+00:00`:
  `verdict=empty, no_op=true, error_reason="locked", shards_scanned=0` — the consolidator itself bailed because another
  instance held the lock.
- `_index/availability_index.parquet` — last **updated** `2026-07-24T23:52:16.213000+00:00` (fresh, <5 min old at first
  probe), but **this run's own slim read logged**:
  `"consolidated blob age 562.1s > 120s threshold — falling back to per-VM shards"` (`ManifestReader`, captured verbatim
  from the day=2026-07-22 scoped read at `2026-07-25T00:01:38Z`).
- `_index/phantom_audit_latest.json` — `{"phantom_count": 1558, "generated_at": "2026-07-19T12:31:33.737819Z"}` —
  **read, not re-run**.
- `_index/reprobe_audit_latest.json` — `generated_at=2026-07-14T11:20:14Z`,
  `new_empties=0, disagreements=0, ambiguous=0, proven=0, reclassified=0` (stale relative to this run — over 10 days
  old).

**Consequence:** every S3 row-count / capture_status distribution in this report was read via the **per-VM-shard
fallback merge**, not the fully-consolidated view, because the index was locked/stale throughout. Per the skill's own
Phase-0(d) rule, this makes every count here a **lower bound**, and a re-read once the concurrent consolidation
(whatever process holds `1-52d4b36b`) completes could show materially different numbers — possibly the very
canonicalisation/migration work this report references.

## 3. Suppression inputs loaded

- `canonical-cutover-register.md` §2 (`require_pipeline_mode` effective-from 2026-05-19 for defi) and §5 (defi leaf axis
  effective-from **UNKNOWN**, premised on "DeFi capture is fully STOPPED... there are no new defi writes") — **§9 below
  measures this premise as FALSE for batch writers**, which materially affects how §5's classification rule should be
  applied going forward (flagged, not silently overridden).
- `reconciliation-finding-taxonomy.md` §4 AE-1..AE-6 and §5 (C2a casing, decision-D `LENDING` — both
  `migration_pending`, compared case-insensitively / not flagged).
- `non-canonical-path-inventory.md` (defi rows 2, 7, 8, 9, 12, 23, 24, 28) — reconciled in §7.

## 4. The machine oracle — structure clean on the sample; id-form NOT clean

`canonical_path_violations()` is the sole authority (never re-implemented). Probed against
`canonical_path_templates("defi")` (23 templates confirmed) and 13 real fetched objects, at both `require_pipeline_mode`
settings.

| Path class (real, day=2026-07-22/24)                                                                                                      | require_pm=False                 | require_pm=True                  | Verdict                                                       |
| ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- | -------------------------------- | ------------------------------------------------------------- |
| `venue=UNISWAP_V2/chain=ETHEREUM/instrument_type=pool/data_type=dex_pool_state/COMP-WETH-30.0.parquet` (real, day=2026-07-24)             | **NON-CANONICAL** (id-form)      | **NON-CANONICAL** (id-form)      | structure OK; filename stem ≠ canonical instrument_id         |
| `venue=UNISWAP_V3/chain=ETHEREUM/instrument_type=pool/data_type=dex_pool_swaps/1INCH-LINK-30.0.parquet` (real, day=2026-07-22, 5 objects) | **NON-CANONICAL** (id-form), 5/5 | **NON-CANONICAL** (id-form), 5/5 | same defect class                                             |
| `venue=KALSHI_PERP/chain=KALSHI_PERP/instrument_type=perpetual/data_type=perp_funding/foo.parquet` (constructed, mirrors real shape)      | NON-CANONICAL (id-form)          | NON-CANONICAL (id-form)          | id-form fails too, independent of the chain-value defect (§9) |

**Every one of the 13 real single-instrument objects fetched this run (13/13) fails the oracle's id-form check.** Root
cause traced to source (§9, FIND-01) — this is **not** a stale-vintage artifact; these objects were created within the
last 24-72h of the audit.

**Correction to the SSOT this run is required to surface** (per the skill's own contract — see §9, FIND-03): the
oracle's id-form checking is **NOT** tradfi-only as `four-surface-reconciliation-procedure.md` §4/§4.3 and
`reconciliation-finding-taxonomy.md` §2.2 currently state. `_ID_FORM_CHECKED_ASSET_GROUPS = frozenset({"cefi", "defi"})`
(`unified-api-contracts/unified_api_contracts/canonical/partition_paths.py:760`, shipped `@d40c5d7d` 2026-07-20, refined
`@1cd27478` 2026-07-23) — **tradfi is not even in the set**. Re-tested the docs' own worked example directly:
`ADAF0:USTF0.parquet` (the "0 violations == CANONICAL, false-clean" example cited in three codex docs) now returns a
real violation. Those docs are stale as of this audit.

## 5. Per-surface verdict per shard (four surfaces = four bits, never collapsed)

Legend: `OK` · `NON-CANON` · `ABSENT` · `SUPPRESSED` (accepted exception) · `NOTE` (data-quality observation) ·
`NOT-READ` (outside sample) · `MIGRATION_PENDING`.

| #   | shard atom (day=2026-07-22 unless noted)                                                     | S1 path                                                                                   | S2 content                                                                                                                                                                                         | S3 manifest (per-VM-shard fallback)                                                                       | S4 catalogue | notes                                                                                             |
| --- | -------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------ | ------------------------------------------------------------------------------------------------- |
| 1   | `UNISWAP_V3/ETHEREUM/pool/dex_pool_swaps` (740 manifest rows this day)                       | OK (structure) / **NON-CANON** (id-form)                                                  | `instrument_id` present + symbolic (`UNISWAP_V2-ETHEREUM:POOL:...`); `canonical_instrument_id` **MISSING**; `asset_group`/`pipeline_mode`/`source`/`schema_version` **MISSING** (sampled 1 object) | `captured`                                                                                                | NOT-READ     | filename stem ≠ `instrument_id` column (§9 FIND-01)                                               |
| 2   | `UNISWAP_V2/ETHEREUM/pool/dex_pool_state` (day=2026-07-24, real, created 1h13m before probe) | OK (structure) / **NON-CANON** (id-form)                                                  | same defect class                                                                                                                                                                                  | NOT-READ this day                                                                                         | NOT-READ     | proves capture is ACTIVE today, not stopped (§9 FIND-00)                                          |
| 3   | `KALSHI_PERP/KALSHI_PERP/perpetual/perp_funding` (`KXBCHPERP` etc., day=2026-07-23)          | **NON-CANON** — `chain=KALSHI_PERP` not a MAINNET_CHAIN_IDS member                        | NOT-READ this run                                                                                                                                                                                  | `captured`, `source=hyperliquid` (mislabeled)                                                             | NOT-READ     | ALREADY TRACKED — `defi_track01_per_instrument_and_canon_id_2026_07_24.md` open todo (§9 FIND-02) |
| 4   | `POLYMARKET_PERP/POLYMARKET_PERP/-/perp_funding`                                             | NOT-READ (S1) this run                                                                    | NOT-READ                                                                                                                                                                                           | `attempted_failed`, `source=hyperliquid`                                                                  | NOT-READ     | same root cause as #3                                                                             |
| 5   | `MORPHO_VAULTS/ETHEREUM/-/vault_share_price` (S1 spelling)                                   | OK (structure)                                                                            | NOT-READ                                                                                                                                                                                           | manifest carries `MORPHOVAULTS` (no underscore) for the same-looking rows — **`shard_atom_vocab_desync`** | NOT-READ     | PERSISTS from the 2026-07-20 report's F5, unresolved 4 days later                                 |
| 6   | `venue=ETHEREUM/chain=ETHEREUM/spot_asset/gas_fees` (day=2020-06-15, historical)             | **NON-CANON** — `venue=ETHEREUM` not in `VENUES_BY_ASSET_GROUP['defi']` bare-protocol set | NOT-READ                                                                                                                                                                                           | NOT-READ this day                                                                                         | NOT-READ     | historical, single-day sample — not a corpus claim (§9 FIND-04)                                   |
| 7   | `dex_pools/{orca,raydium,kamino,solend}/SOLANA/date=…/` (legacy top-level)                   | **CONFIRMED 0 objects**                                                                   | n/a                                                                                                                                                                                                | n/a                                                                                                       | n/a          | register rows 7/8 delete claim VERIFIED ACCURATE (§7)                                             |
| 8   | `lending_indices/{...}` (legacy top-level)                                                   | **CONFIRMED 0 objects**                                                                   | n/a                                                                                                                                                                                                | n/a                                                                                                       | n/a          | same                                                                                              |
| 9   | `_needs_attribution/day=2021-02-24/…` (10 objects sampled)                                   | **PRESENT** (`time_created=2026-07-19`)                                                   | not read                                                                                                                                                                                           | n/a (operational tree, not raw-tick data)                                                                 | n/a          | register row 24 "DELETED 2026-07-21" claim CONTRADICTED for defi (§7 FIND-07)                     |

## 6. Corpus-scale reference — reused from the 2026-07-23 terminal orphan sweep (read, not re-run)

Single-walk discipline forbids opening a new whole-corpus walk. The most recent one
(`orphan-sweep-defi-20260723- 043605`, 6th attempt, completed 2026-07-23T21:04:37Z, full clean walk of **24,890,959
objects**) is published inside `plans/active/issues/defi_orphan_sweep_test_artifact_prod_leak_2026_07_24.md` — reusing
its printed class counts (sanctioned route #3) gives the best available answer to "how canonical is defi, at full-corpus
scale, right now":

| Class                                    | Count      | % of 24,890,959 | Delete-eligible                           |
| ---------------------------------------- | ---------- | --------------- | ----------------------------------------- |
| **A** canonical_manifested               | 7,675,460  | **30.84%**      | n/a (this is the "good" bucket)           |
| **B** legacy_duplicate                   | 1,080      | 0.004%          | YES-eligible only (5-part proof required) |
| **D** junk                               | 136,635    | 0.55%           | YES-eligible only (5-part proof required) |
| **E** orphan_real                        | 15,865,384 | **63.74%**      | **NO — NEVER** (backfill target only)     |
| C / C2 (infra / non-data, by difference) | 1,212,400  | 4.87%           | NO                                        |

**This number pre-dates and is orthogonal to** the id-form defect measured in §4/§9 — the orphan sweep's "canonical"
classification is a path-STRUCTURE + manifest-PRESENCE test (whatever oracle settings the sweep script used, run
2026-07-23, i.e. _after_ the id-form check shipped `@d40c5d7d`), not a byte-for-byte proof that class-A's 7.68M objects
also pass the newer id-form check. **Do not conflate the two figures** — they measure different surface pairs
(S1-structure↔S3-presence vs S1-idform); reported separately, both sourced.

## 7. Non-canonical inventory reconcile (register ⇄ reality, defi-scoped)

| inv row | location                     | register disposition                                | this run                                                                                                                                                                                                                                                                                            |
| ------- | ---------------------------- | --------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 7       | `dex_pools/` top-level       | RESOLVED — DELETED 2026-07-21                       | **CONFIRMED — 0 objects.** Claim holds.                                                                                                                                                                                                                                                             |
| 8       | `lending_indices/` top-level | RESOLVED — DELETED 2026-07-21                       | **CONFIRMED — 0 objects.** Claim holds.                                                                                                                                                                                                                                                             |
| 23      | dual `_migration_backup(s)/` | `unknown`                                           | CONFIRMED both still present (`_migration_backup/`, `_migration_backups/`); disposition unchanged.                                                                                                                                                                                                  |
| 24      | `_needs_attribution/day=…/`  | RETIRED — DELETED 2026-07-21 (both internal shapes) | **CONTRADICTED for defi.** 10 objects sampled under `_needs_attribution/day=2021-02-24/` through many other `day=` subdirs; `time_created=2026-07-19T07:05:...` — i.e. **created BEFORE** the register's claimed 2026-07-21 delete date, and still present at probe time (2026-07-25). See FIND-07. |
| 28      | `configs/patches/`           | `unknown`                                           | CONFIRMED present, unchanged.                                                                                                                                                                                                                                                                       |

### Reality→register (new — register-patch stanza for the maintainer to apply serially, per the concurrency clause)

This session did not edit `non-canonical-path-inventory.md` directly (shared file, concurrent sessions active — see §10
git notes). Proposed new rows:

```
| NEW | `market-data-tick-defi-prd-{pid}/_vm_staging/{defi_expansion,dex_pools,eigenlayer_rewards,gas_fees,...}/` | one-off migration-support codebase tarballs + backfill logs (~8MB each), `time_created≈2026-05-12` | canonical twin: n/a (operational, not data) | still-written-by: NOT independently grepped this run (bounded single-session budget) — UNVERIFIED | disposition: `unknown` |
| NEW | `market-data-tick-defi-prd-{pid}/backfill-logs/{2020-2024,december-2025,test-2025-12-01}/` | operational log prefix at bucket root, outside bucket-isolation-model's data namespaces | canonical twin: n/a | still-written-by: UNVERIFIED | disposition: `unknown`; note the `test-2025-12-01/` sub-name is itself a mild test-naming leak into a prod path |
| NEW | `market-data-tick-defi-prd-{pid}/_quarantine/processed_candles/...` | candle-LAYER quarantine tree — OUT OF SCOPE for this raw-tick dispatch, flagged for the candle-layer reconciliation to pick up | not evaluated | not evaluated | not evaluated — hand off to `--layer candles` |
```

`agent-sample-test-jupiter/` is **already fully tracked** —
`plans/active/issues/defi_orphan_sweep_test_artifact_prod_leak_2026_07_24.md` (fix shipped
`instruments-service@9a491b23`; delete queued as a P3 human-gated todo). Not re-filed; not re-counted as new.

## 8. Typed findings (taxonomy names — diffable)

`suppressed_by` uses the AE-n / migration_pending labels from `reconciliation-finding-taxonomy.md`. Severities elevated
above the taxonomy default are marked `[ELEVATED]` with the reason stated.

| #       | type                                                                   | severity                                                                                                                                     | shard / location                                                                                                                                                                                                               | surfaces              | detector                                                                                                                | delete_elig | suppressed_by                                            | status                                                                     |
| ------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------- | ----------------------------------------------------------------------------------------------------------------------- | ----------- | -------------------------------------------------------- | -------------------------------------------------------------------------- |
| FIND-00 | **taxonomy-gap** — planning-premise contradiction, no closed type fits | **[BIG] HIGH**                                                                                                                               | register `canonical-cutover-register.md` §5 + `defi-canonical-naming-ssot.md` WRITE-MODEL banner premise "capture STOPPED, no new defi writes"                                                                                 | cross-doc vs live GCS | direct `time_created` probe on real objects, 2026-07-24 (today)                                                         | n/a         | none                                                     | **NEW — see §9**                                                           |
| FIND-01 | `non_canonical_path` (id-form leg, §4.3)                               | **[ELEVATED] HIGH** (taxonomy default MEDIUM; elevated — active, growing, spans 6/7 shipped write_defi_rows handlers per R1's own changelog) | EVM defi single-instrument shards estate-wide (dex_pool_state/dex_pool_swaps/oracle_prices/risk_params/lending_indices/lst_rates)                                                                                              | S1 (id-form)          | `canonical_path_violations()` on 13 real objects (13/13 fail)                                                           | NO          | none                                                     | **NEW — see §9**                                                           |
| FIND-02 | `non_canonical_axis_value` (S1 chain, S3 asset_group/source)           | HIGH                                                                                                                                         | `venue=chain=KALSHI_PERP` / `POLYMARKET_PERP` under `asset_group=defi`                                                                                                                                                         | S1, S3                | census + manifest sample + code read (`_perp_funding_kalshi_polymarket.py:319-320`)                                     | NO          | none (open bug, not an accepted exception)               | **ALREADY TRACKED**, corroborated + extended (§9)                          |
| FIND-03 | `shard_atom_vocab_desync`                                              | HIGH                                                                                                                                         | `MORPHOVAULTS` (S3 manifest) vs `MORPHO_VAULTS` (S1 GCS path)                                                                                                                                                                  | S1↔S3                 | census comparison                                                                                                       | NO          | none                                                     | **PERSISTS** from 2026-07-20 report F5                                     |
| FIND-04 | `non_canonical_axis_value` (S1)                                        | MEDIUM (date-conditional, historical day only)                                                                                               | `venue=ETHEREUM`, `venue=POLYGON` (bare chain name in venue slot), day=2020-06-15                                                                                                                                              | S1                    | census, single historical day                                                                                           | NO          | none — but scope is a single-day sample, not corpus-wide | NEW (bounded)                                                              |
| FIND-05 | registry-drift observation (not itself an estate defect)               | INFO/LOW                                                                                                                                     | 12-13 actively-captured defi protocols absent from `VENUES_BY_ASSET_GROUP['defi']` (ACROSS, ALCHEMY, ANKR, BLAZESTAKE, FLASHBOTS, FRAX, MAKER, MANTLE, MORPHO_VAULTS, STADER, STAKEWISE, SWELL; `LST` is ambiguous/suspicious) | S1 vs UAC registry    | census cross-check vs `market_data_categories.VENUES_BY_ASSET_GROUP`                                                    | n/a         | none                                                     | NEW — registry maintenance, false-positive risk for automated census gates |
| FIND-06 | schema `missing_column` (G3, content-grain)                            | MEDIUM (Tier-1 SAMPLED, 1 object)                                                                                                            | v9 metadata columns absent from sampled parquet: `asset_group`, `pipeline_mode`, `source`, `schema_version`, `canonical_instrument_id` (only `available_at` present)                                                           | S2                    | direct parquet read                                                                                                     | NO          | none                                                     | NEW (sampled, not corpus-wide)                                             |
| FIND-07 | register-accuracy correction                                           | MEDIUM                                                                                                                                       | `_needs_attribution/day=…/` in defi bucket — register claims DELETED 2026-07-21, objects present with `time_created=2026-07-19`                                                                                                | S1 vs register        | direct object listing + timestamp check                                                                                 | n/a         | none                                                     | **NEW**                                                                    |
| FIND-08 | register-new locations (Phase 2 reality→register)                      | INFO/LOW                                                                                                                                     | `_vm_staging/`, `backfill-logs/` (see §7 patch stanza)                                                                                                                                                                         | S1                    | bounded top-level sweep                                                                                                 | unknown     | none                                                     | NEW                                                                        |
| FIND-09 | codex-currency correction                                              | INFO                                                                                                                                         | `four-surface-reconciliation-procedure.md` §4/§4.3, `reconciliation-finding-taxonomy.md` §2.2, `CLAUDE.md` domain index all state the oracle skips filename id-form except for tradfi                                          | doc vs code           | direct re-test of the docs' own `ADAF0:USTF0.parquet` example against live `unified-api-contracts@d40c5d7d`+`@1cd27478` | n/a         | none                                                     | **NEW** — see §9                                                           |
| FIND-10 | `manifest_infra` (index contention)                                    | INFO (but materially affects every count above)                                                                                              | `_index/consolidator.lock` held throughout this run                                                                                                                                                                            | S3                    | JSON reads                                                                                                              | NO          | none                                                     | see §2                                                                     |

## 9. Discussion of the two BIG findings (data-correctness + cross-repo + SSOT contradiction)

### FIND-00 — "DeFi capture is STOPPED" is measurably false for batch writers, right now

`canonical-cutover-register.md` §5 and `defi-canonical-naming-ssot.md`'s WRITE-MODEL banner both state DeFi capture is
fully stopped pending the per-instrument writer fix, with the consequence that "post-2026-07-20 defi objects at the old
batch leaf are not a writer regression — there are no new defi writes," and that defi leaf-shape findings should
therefore be classified `unknown-vintage`. **Directly measured, this run:**

- `raw_tick_data/by_date/day=2026-07-24/pipeline_mode=batch_onchain_subgraph/.../UNISWAP_V2/.../COMP-WETH-30.0.parquet`
  — `time_created=2026-07-24T22:46:34Z`, i.e. created **today**, ~1h13m before this probe.
- `pipeline_mode` values actively producing new objects through `day=2026-07-24`: `batch_onchain_subgraph`,
  `batch_chainlink`, `batch_onchain_rpc`, `batch_aave`. `batch_kalshi_perp` produced new objects through
  `day=2026-07-23` (zero for `day=2026-07-24` at probe time — could still land later that day).
- These are `pipeline_mode=batch_*` (not `live_*`) — i.e. ongoing **batch/backfill jobs**, not a resumed live websocket
  feed. That distinction matters for the fix: it means an active batch/backfill process is _continuing to write the
  pre-target leaf shape_ rather than the corpus being frozen while the writer fix ships.

**Consequence:** the register's premise ("no new defi writes" ⇒ leaf-shape findings are `unknown-vintage`, not
regressions) does not hold for the batch lane. Every day this continues, the id-form-non-canonical population (§9
FIND-01) grows, and the migration backlog the defi close-out plan is sequenced around gets larger, not static. This is a
planning-input correction, not merely a data annotation — it belongs on the operator's radar because it affects how
urgently the writer fix (R1's leaf-naming, not R1's fan-out mechanism, which IS shipped) needs to land.

### FIND-01 — `write_defi_rows()` writes the bare SYMBOL as the leaf filename, not the canonical_instrument_id

Root cause, read directly
(`market-tick-data-service/market_tick_data_service/market_interface/adapters/defi/ canonical_write.py`, current HEAD,
in `write_defi_rows()`):

```python
for _inst_id, group in df.groupby("instrument_id", sort=True):
    group_df = group.reset_index(drop=True)
    group_symbol = str(group_df[resolved_symbol_column].iloc[0])
    leaf = f"{_sanitize_defi_symbol(group_symbol)}.parquet"
```

The loop groups by the **full** `instrument_id` (`_inst_id`) but then discards it (leading underscore — deliberately
unused) and rebuilds the leaf from only the raw `symbol` column. Measured on 13 real fetched objects: content
`instrument_id = "UNISWAP_V2-ETHEREUM:POOL:COMP-WETH-30.0"`; on-disk filename = `COMP-WETH-30.0.parquet`. This
contradicts:

- pattern #1's hard rule ("filename stem == instrument_id column == manifest key, byte-identical",
  `cross-asset-canonical-target-ssot.md` §0/§1, `four-surface-reconciliation-procedure.md` §2).
- the SAME plan's own "Confirmed decisions (operator 2026-07-18)" bullet, 8 lines above the R1 "✅ SHIPPED" checkbox in
  `plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`: _"shard key = the symbolic
  canonical_instrument_id (human-readable filename `AAVE_V3-ETHEREUM:A_TOKEN:aUSDC.parquet`...)"_ — the shipped code
  produces `aUSDC.parquet`, not that.

R1's changelog states 6/7 defi handlers already route through `write_defi_rows` (dex_pools / dex_swaps / oracle_prices /
risk_params / lending_indices / lst_rates), so this is not one venue's bug — it is the estate-wide leaf convention for
every EVM single-instrument shard being written today. This is a genuine gap between a recorded operator decision and
the code that's marked shipped against it — **not itself flagged anywhere in the plan text I read** (verified via grep
for `sanitized_symbol` / "bare symbol" / "leaf.*canonical_instrument_id" across the relevant plan + closeout docs — no
hits describing this specific divergence).

Both findings are filed under this run's report rather than a fresh issue doc, given the operator-notification
requirement below covers them; recommend the findings-triage "outside every plan" default
(`plans/active/issues/ <slug>_2026_07_24.md`) if the operator wants them tracked as a standalone fix — see the issue doc
filed alongside this report.

## 10. Suppressed accepted-exceptions (mandatory suppression — counted, not re-listed)

| AE / axis                                | condition                                                                  | suppressed occurrences this run                                                                                                                                                                                                                                                                                                                                                                                       |
| ---------------------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AE-3 (defi two-id POOL divergence)       | `instrument_id` ≠ `canonical_instrument_id` on POOL rows is NOT a finding  | **N/A this run** — the sampled objects don't have a `canonical_instrument_id` column AT ALL (FIND-06), which is a stronger defect than AE-3's covered divergence-case; AE-3 does not apply to a missing column, so this is reported as FIND-06, not suppressed under AE-3.                                                                                                                                            |
| AE-5 (defi interim flat `LENDING`)       | `lending`/`solana_lending` on market/event data_types not flagged          | 377 manifest rows (day=2026-07-22 sample, `instrument_type=lending`) — suppressed, not flagged.                                                                                                                                                                                                                                                                                                                       |
| C2a (instrument_type COLUMN casing)      | compared case-insensitively during `migration_pending`, no finding emitted | **0 casing-divergent rows observed** in the day=2026-07-22 sample (`instrument_type` values found: `pool, lending, spot_asset, lst, yield_bearing, perpetual` — all lowercase, no uppercase variants in this slice); consistent with defi's 2026-07-24 per-value carve-out (`cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`) but this is a single-day, single-slice observation, not a corpus claim. |
| decision-D (defi market/event `LENDING`) | not flagged                                                                | same 377 rows as AE-5 (same axis, restated per taxonomy's dual naming)                                                                                                                                                                                                                                                                                                                                                |

## 11. Coverage-gap section (what was NOT reached, and why)

1. **Orphans**: not independently re-walked this run (single-walk discipline) — §6 reuses the 2026-07-23 terminal
   sweep's published numbers instead of re-deriving them.
2. **Temporal**: 1 primary four-surface day (2026-07-22) + 2 spot-corroboration days (2026-07-23/24) + 1 historical
   census day (2020-06-15) out of ~2,397 days on disk. No claim is made about days outside this sample.
3. **S4 catalogue**: NOT independently re-probed this run. The 2026-07-20 report's S4 findings (F5 catalogue↔manifest
   venue-spelling divergence, F11 `prd/`-vs-`prod/` shadow) were not re-verified — treat as
   `unverified-since- 2026-07-20`, not reconfirmed.
4. **S2 content**: read on 14 objects total (13 for oracle/S1↔S2 testing + 1 for schema-column testing), all EVM `pool`
   shards. Solana `solana_amm_pool`, `lending` (`A_TOKEN`/`DEBT_TOKEN`), `lst`, `spot_asset`, `perpetual` content NOT
   independently read this run.
5. **Tier-2 100% id/schema VM campaign**: NOT dispatched — this run stayed Tier-1 (default; not invoked under
   `/autonomous`).
6. **`_vm_staging/` and `backfill-logs/` still-written-by**: NOT grepped exhaustively this run — flagged `unknown` in
   the register-patch stanza (§7), not resolved.
7. **No coverage percentage (`reachable_coverage`) computed this run** — the day=2026-07-22 manifest read did not
   project `expected_unattempted`, so the formula `captured / (captured + attempted_failed + expected_unattempted)`
   cannot be computed from this sample. Reported instead: raw `capture_status` distribution for day=2026-07-22
   (per-VM-shard-fallback read, lower bound): `captured=1620 (61.3%)`, `empty_confirmed=1019 (38.5%)`,
   `attempted_failed=5 (0.2%)` of 2,644 sampled rows — **this is a snapshot distribution, not the honest-coverage
   formula, and must not be quoted as a coverage %.**

## 12. Verdict

**Is asset_group=defi 100% canonical? No, and not close, on every surface pair this run could measure:**

- **At full-corpus scale** (reusing the 2026-07-23 orphan sweep, 24,890,959 objects): only **30.84%** are
  `canonical_manifested` (path-structure canonical AND manifested); **63.74%** are `orphan_real` — present on disk, zero
  manifest representation, never delete-eligible, requiring a `record_captured` backfill per taxonomy.
- **On the id-form leg** (this run's own direct oracle testing, sampled — not a corpus claim): **0/13 (0%)** of real,
  currently-being-written EVM single-instrument objects pass the filename id-form check, because the shipped
  `write_defi_rows()` leaf convention (bare symbol) diverges from the ruled target (full `canonical_instrument_id`).
  This is a _live, currently-shipping_ writer producing non-canonical filenames on every write, not a historical residue
  — DeFi capture (batch lane) is active through today, contradicting the register's "capture stopped" premise.
- Additional, smaller-scale but real defects persist across measurable axes: venue/chain misclassification for
  Kalshi/Polymarket perp data landing in the defi estate (already tracked, open), a manifest↔path vocabulary desync for
  Morpho Vaults (persisting since the 2026-07-20 run), missing v9 metadata columns in sampled content, and a
  register-accuracy gap on `_needs_attribution/`.
- **No new delete is authorized.** `dex_pools/`/`lending_indices/` remain confirmed empty (2026-07-21 delete holds); no
  other location in this report clears the five-part proof.

This run's single most decision-relevant fact for whoever owns the defi close-out sequencing: **the assumption that
capture has paused while the per-instrument writer is fixed does not hold for the batch lane** — the fix needs to land
against a moving target, not a frozen one.
