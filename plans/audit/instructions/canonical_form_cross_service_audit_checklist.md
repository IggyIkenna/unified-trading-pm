# Canonical-Form Cross-Service Audit Checklist (SSOT)

> **Everlasting SSOT — never archive.** This file enumerates EVERY canonical data+manifest invariant the 2026-06-01
> canonicalisation programme enforces, and maps each one to the per-service audit-instruction file that owns the
> concrete check. **Goal (operator 2026-06-01)**: re-running the per-service audits — which need NOT be the same audit,
> but MUST collectively cover this list — proves the whole data pipeline is in canonical form across every service. A
> canonical-form item with no owning audit is a **coverage gap** and is review-blocking.
>
> **Driving plans** (the work this checklist audits): `defi_manifest_canonicalisation_2026_06_01.md` (§MASTER
> coordinator) + the per-AG L3 walks (`cefi`/`tradfi`/`sports`/`prediction`\_manifest_canonicalisation) + the
> per-service walks (`instruments`/`downstream_services`\_manifest_canonicalisation) + the riders
> (`data_source_provenance_all_asset_groups`, `pipeline_mode_partition_migration`).

## Audit scope is a PRIOR, not a ceiling — fix-fully-autonomously (HARD RULE, codified 2026-06-01)

> Every canonicalisation plan's headline scope (cell counts, "legacy-only", "~complete", "verify-only") is a **prior**
> from a coarse pre-audit — **NOT a ceiling**. The audit-first P0 reads **DATA-STATE** (never a code constant — the
> manifest-v8 lesson). When it surfaces MORE canonical-form debt than the headline implied, that debt is **fixed FULLY
> and AUTONOMOUSLY in the same single bundled walk**. Discovery NEVER shrinks scope; it expands the walk.
>
> **Reference incident (2026-06-01)**: cefi was framed "~complete, 838-cell gap-fill". The data-state audit found the
> canonical cefi `_index` is **100% v8 (not v9)**, has **no `source` column**, **no `category`/`asset_group` column**,
> and **blank `pipeline_mode`** — i.e. a FULL re-canonicalisation across the whole corpus, vastly bigger than 838 cells.
> The headline was a prior; the data-state is the truth. The walk fixes all of it.
>
> **Banned responses to an expanded finding** (every one is review-blocking):
>
> - descope to the headline number ("the plan said 838 cells, I'll just do those");
> - defer the extra to a follow-up plan / mark it post-cutover;
> - stamp it `BLOCKED-OPERATOR-DECISION` (a data-state gap is NOT a design fork — just fix it);
> - "verify-only" when the verify itself proves the form is wrong.
>
> **Required response**: (1) capture the expanded finding as additional `- [ ]` todos in the plan (Capture Discoveries
> As Plan Todos) + bake it into a **reusable audit tool** that reads the full schema signal (schema_version,
> `source`/`category`/`asset_group`/`pipeline_mode` column presence, `error_reason` for CF-5, object paths for
> CF-2/3/9); (2) bundle the fix into the SAME single-walk (no second `_index` walk); (3) acceptance = **CF-1…CF-12 GREEN
> on the ACTUAL data-state**, whatever that turns out to require. The ONLY legitimate non-completion is the genuine
> operator-gated closed set: `BLOCKED-CREDENTIALS` / `BLOCKED-OPERATOR-DECISION` (a real design fork, not a data gap) /
> `BLOCKED-UPSTREAM-OUTAGE` / `BLOCKED-PLAYWRIGHT`. Composes with CLAUDE.md "Data Pipeline Correctness Is The Heartbeat"
>
> - "Plans Run To Actual Completion" + "Complete, don't defer".

## The matrix being audited — (service × asset_group) cells

Every cell in this matrix has a manifest `_index` + data objects that MUST be in canonical form. The per-AG MTDS plans
cover the **MTDS** row; the per-service plans cover the rest:

| Service ↓ / AG →    | defi | cefi | tradfi | sports | prediction | Owning canonicalisation plan                               |
| ------------------- | ---- | ---- | ------ | ------ | ---------- | ---------------------------------------------------------- |
| instruments-service | ✓    | ✓    | ✓      | ✓      | ✓          | `instruments_manifest_canonicalisation_2026_06_01`         |
| MTDS (raw tick)     | ✓    | ✓    | ✓      | ✓      | ✓          | per-AG `*_manifest_canonicalisation_2026_06_01`            |
| MDPS (candles)      | ✓    | ✓    | ✓      | ✓      | ✓          | `downstream_services_manifest_canonicalisation_2026_06_01` |
| features-service    | ✓    | ✓    | ✓      | ✓      | ✓          | `downstream_services_manifest_canonicalisation_2026_06_01` |
| strategy-service    | ✓    | ✓    | ✓      | ✓      | ✓          | `downstream_services_manifest_canonicalisation_2026_06_01` |
| execution-service   | ✓    | ✓    | ✓      | ✓      | ✓          | `downstream_services_manifest_canonicalisation_2026_06_01` |

## Canonical-form invariants (CF-1 … CF-21)

Each invariant lists the **canonical target**, the **audit method** (read DATA-STATE, never trust a code constant — the
manifest-v8 lesson: a constant said v8 while 0% of 7.4M rows were v8), and **which services it applies to**.

| ID    | Invariant (canonical target)                                                                                                                                                                                                                                                                                                                                                                                                            | Audit method (data-state)                                                                                                                                                                                 | Applies to                                                                                                           |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| CF-1  | **schema_version = v9** on every manifest row + parquet                                                                                                                                                                                                                                                                                                                                                                                 | Read the actual `schema_version` distribution from prod `_index` + a sample of parquets. NOT the `MANIFEST_SCHEMA_VERSION` constant.                                                                      | every service with a manifest                                                                                        |
| CF-2  | **`asset_group=` not `category=`** on BOTH object PATHS and manifest `_index` ROWS                                                                                                                                                                                                                                                                                                                                                      | grep object paths for `category=`; read `_index` rows for a `category` field. (CODE side already emits `asset_group=` — archived `venue_axis_asset_group_vocabulary`.)                                    | every service                                                                                                        |
| CF-3  | **`pipeline_mode=` hive partition** on object paths (column already shipped)                                                                                                                                                                                                                                                                                                                                                            | path-list `pipeline_mode=batch*` / `pipeline_mode=live*`; confirm the partition segment exists (not just the column).                                                                                     | mtds · mdps · instruments · features                                                                                 |
| CF-4  | **`source` COLUMN** stamped on every external cell (column, NOT a path key — co-mingled, same read path); multi-source = 2 rows; computed/service outputs exempt                                                                                                                                                                                                                                                                        | Read the `source` column distribution; assert **zero blank on every external cell**. Confirm `source` is a column not a path segment.                                                                     | external ingest: mtds · mdps · instruments · sports-fixtures. **Exempt (computed)**: features · strategy · execution |
| CF-5  | **Typed `EmptyConfirmedReason`** on every empty cell; no blank / mislabeled `SOURCE_RETURNED_ZERO`                                                                                                                                                                                                                                                                                                                                      | Read the empty-reason histogram; assert 0 blank/untyped. Service-specific reason sets below.                                                                                                              | every service that records empty                                                                                     |
| CF-6  | **`expected_unattempted` 4th state materialised** (writer/orchestrator pre-flight reads the IS manifest + records owed cells)                                                                                                                                                                                                                                                                                                           | Run a prod batch on the post-Phase-1+2 code; confirm owed rows generate with `EXPECTED_OUTSIDE_PROCESSING_SCOPE` / `EXPECTED_UPSTREAM_EMPTY`.                                                             | mtds · mdps · features (downstream propagate)                                                                        |
| CF-7  | **Canonical names**: underscore data_type · flat `venue` + populated `chain` · `{VENUE}_V{N}` underscore-canonical; no legacy drift                                                                                                                                                                                                                                                                                                     | grep handler `data_type=`/`_DATA_TYPE` literals + read corpus venue/data_type strings; confirm no hyphen / `VENUE-CHAIN` / glued `_V{N}`.                                                                 | mtds · instruments (market + reference)                                                                              |
| CF-8  | **`available_at` per-row**, preserve-or-honest-derive; never lookahead / migration-time / read-time                                                                                                                                                                                                                                                                                                                                     | Read `available_at` vs day boundary; assert batch=live derivation parity (top `SOURCE_PRIORITY` entry's live `available_at`).                                                                             | every service                                                                                                        |
| CF-9  | **env-split bucket** `{kind}-{env}-{project}` (`-prd`/`-test`); resolved via `resolve_bucket_name()`                                                                                                                                                                                                                                                                                                                                    | grep for inline `gs://` f-strings (QG STEP 5.69); confirm every bucket lookup is env-tiered + canonical.                                                                                                  | every service                                                                                                        |
| CF-10 | **No phantom / date-impossible `captured`** (pre-genesis / pre-launch with no backing object; post-launch captured object-backed)                                                                                                                                                                                                                                                                                                       | captured-vs-objects walk per (chain/venue, date); relabel any object-less captured row honestly.                                                                                                          | mtds · instruments                                                                                                   |
| CF-11 | **fetch-failure → `attempted_failed`, never `empty_confirmed`** (no `except: return []` swallow)                                                                                                                                                                                                                                                                                                                                        | per-adapter grep for `except … return []` / `return {}`; trace to the `record_*` call. (defi A7 precedent.)                                                                                               | every ingesting service                                                                                              |
| CF-12 | **batch = live symmetry** — identical schema / data_types / fields; `available_at` not derived at read-time; no live-only data_types                                                                                                                                                                                                                                                                                                    | diff batch vs live schema + data_type set per AG; confirm one code path.                                                                                                                                  | every service                                                                                                        |
| CF-13 | **pipeline*mode is SOURCE-AWARE `{mode}*{source}[_{transport}]`, NOT coarse `batch`/blank** (extends CF-3) — migrator/rebuild/enumerator stamp it; readers union-aware across modes; manifest + data-status carry pipeline_mode + source + cadence axes                                                                                                                                                                                 | grep migrators/rebuild/enumerator for a coarse `pipeline_mode="batch"`/blank stamp (defi `rebuild_defi_manifest.py:302` precedent); confirm `live_<source>`/`replay_<source>` form + union-aware readers. | mtds · mdps · instruments · features (the ⑨ readiness check; gated by G0 of the master coordinator)                  |
| CF-14 | **IS-catalogue could-exist ROOT is GREEN** (the foundation of CF-6) — the AG's `build_instrument_catalogue` roll-up + `enumerate_expected_universe` v2 are GREEN, gated on IS backfill complete + accurate UAC (genesis/launch/coverage), with the daily catalogue scheduler live                                                                                                                                                       | confirm the per-AG catalogue dry-run+run seeded `expected_unattempted` from the IS×UAC could-exist universe; confirm the daily scheduler is wired (not just cefi).                                        | instruments (root) → mtds/mdps/features denominators (the ⑧ readiness check; gated by G1 of the master coordinator)  |
| CF-15 | **Possible-manifest registry is the canonical could-exist SSOT** — one `unified_api_contracts/registry/possible_manifest.py` (`enumerate_possible_shard_keys` / `is_valid_shard_key` / `canonical_path_templates`) composes axis-names (`SHARD_AXIS_MATRIX`) × value-domains (`data_type_capability`) × validity; every consumer (denominator, phantom `prefix_tpls`, enumerator, orphan scan) reads it — NO per-consumer re-derivation | confirm the module exists + is the single import; grep that `enumerate_expected_universe` / deployment-api denominator / phantom `prefix_tpls` derive from it (no bespoke cross-product).                 | uac (root) → instruments · mtds · mdps · features · deployment-api                                                   |
| CF-16 | **Catalogue-seeded denominator at ZERO captured data** — a `(venue, data_type, instrument_type)` with instruments listed but no market data shows a fully-enumerated `expected_unattempted` denominator (NOT silent absence); CeFi + Prediction enumerators FULL (not STUB)                                                                                                                                                             | pick a venue/data_type with 0 captured rows; assert the could-exist universe still materialises `expected_unattempted` rows from the IS catalogue. CeFi/Prediction non-stub.                              | instruments → mtds/mdps/features denominators                                                                        |
| CF-17 | **Bidirectional manifest ≡ GCS + full bucket prefix taxonomy** — `phantom_count==0` (manifest→GCS) AND `orphan_class_E==0` (GCS→manifest: real data with no row); EVERY bucket prefix labelled {service-data, manifest-infra, logs, run-artifact, terraform, tarball, unknown}; non-data paths (VM logs etc.) understood + NEVER deleted; byte/object sizing rolled up                                                                  | run the orphan sweep (GCS→manifest) + phantom reconciler (manifest→GCS); assert both zero; assert 0 `unknown` prefixes; emit the sizing rollup. Non-data ≠ delete.                                        | every service with a data bucket                                                                                     |
| CF-18 | **Schema-attribute completeness — no silent column truncation** — every column the SOURCE/legacy parquet physically carries is represented in the v9 canonical contract OR explicitly operator-acked-dropped; zero silent attribute loss (invisible to row-count/schema checks)                                                                                                                                                         | sample recent source parquets per (AG, data_type, venue); union their footer columns; diff vs the v9 UAC contract; any uncarried column is RED until carried or acked.                                    | mtds · mdps · instruments · features                                                                                 |
| CF-19 | **Candle edge-timestamp convention** — every external OHLCV/candle source is left-edge (open) vs right-edge (close) labelled per `codex/02-data/bar-boundary-candle-edge-convention.md`; one normalization point; batch==live agree                                                                                                                                                                                                     | per external OHLCV source × timeframe, confirm the stored timestamp edge vs the SSOT + an independent reference bar; a 1-interval shift is invisible to row/schema checks.                                | mtds · mdps (external candle ingest)                                                                                 |
| CF-20 | **Data-status / deployment-UI render the v9 manifest correctly** — coverage % + 4-state + could-exist denominator + pipeline_mode/source drilldowns render from a clean read of the canonical `_index` (composes with the G3 UNION view)                                                                                                                                                                                                | point data-status at the canonical (or projected) v9 `_index`; assert coverage %, denominator, drilldowns match the manifest (no re-derived genesis/launch).                                              | deployment-api · deployment-ui                                                                                       |
| CF-21 | **Verified-delete safety for legacy/duplicate objects** — a legacy-shape object is deleted ONLY if its canonical twin is in the manifest (`captured`) AND `crc32c(legacy)==crc32c(canonical)`; never delete the only copy of real data; non-data paths exempt                                                                                                                                                                           | dry-run the legacy-twin cleanup; assert every delete candidate passes the in-manifest + crc32c-identity gate; 0 deletes of class (C)/(C2)/(E).                                                            | mtds · mdps · instruments (migration cleanup)                                                                        |

> **CF-15 … CF-21 (added 2026-06-10)** come from the `migration_verification_orphan_safety_2026_06_10` plan (audit:
> `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md`). They are written in **steady-state
> form** — "assert the v9 corpus holds X", re-runnable after the migration completes — so a future regression (a new
> adapter reintroducing the candle-edge bug, a new writer creating orphans, a dropped attribute) is caught by re-running
> this checklist rather than rediscovered. CF-15/CF-17/CF-21 own the orphan/registry/cleanup surface; CF-19 the
> candle-edge; CF-16/CF-18/CF-20 the denominator/schema/render surface.

> **CF-13 + CF-14 (added 2026-06-07) are the ⑨ + ⑧ readiness checks** from
> `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` (the data-layer coordinator). Their
> cross-AG ownership + the upstream gating (G0 pipeline_mode model, G1 IS catalogue) live in that coordinator's
> registry, not duplicated here — this checklist just adds the per-cell invariant so an AG's audit fails RED until they
> hold.

### CF-5 service-specific typed-reason sets (the empty cell must carry the RIGHT reason)

- **defi**: `EXPECTED_PRE_GENESIS_CHAIN` · `EXPECTED_PRE_VENUE_LAUNCH` (UAC `DEFI_VENUE_LAUNCH_DATES`) ·
  `SOURCE_RETURNED_ZERO` only when genuinely empty.
- **sports** (schedule-driven — the keystone): `EXPECTED_NO_FIXTURE` · `EXPECTED_PRE_SEASON` · `EXPECTED_POST_SEASON` ·
  `EXPECTED_PAUSED_LEAGUE` · `EXPECTED_OUTSIDE_TRANSFER_WINDOW` · `EXPECTED_SOURCE_DOES_NOT_COVER_LEAGUE` ·
  `EXPECTED_FIXTURE_POSTPONED` · `EXPECTED_FIXTURE_CANCELLED` · `EXPECTED_KNOWN_SOURCE_GAP` · `EXPECTED_NO_MAPPING`
  (oracle: `clip_dates_to_source_coverage()` / `is_in_known_gap()`).
- **cefi / tradfi / prediction**: `EXPECTED_KNOWN_SOURCE_GAP` (documented outage) · `SOURCE_RETURNED_ZERO` (genuine) ·
  `EXPECTED_OUTSIDE_PROCESSING_SCOPE`.
- **all**: `EXPECTED_DEPRECATED_DATA_TYPE` for retired types; `EXPECTED_UPSTREAM_EMPTY` for downstream-derived.

## Per-service audit ownership (which audit-instruction file checks which CF item)

Each per-service audit-instruction file MUST carry a "Canonical-form coverage" section that cites this SSOT and lists
the CF items it owns with a concrete check. ✓ = owns the live check; (prop) = propagates upstream value; n/a = exempt.

| Audit instruction file                                         | CF-1 | CF-2 | CF-3  | CF-4 | CF-5              | CF-6   | CF-7 | CF-8 | CF-9 | CF-10 | CF-11 | CF-12 |
| -------------------------------------------------------------- | ---- | ---- | ----- | ---- | ----------------- | ------ | ---- | ---- | ---- | ----- | ----- | ----- |
| `mtds_mdps_master` (MTDS+MDPS)                                 | ✓(g) | ✓    | ✓     | ✓(j) | ✓(f)              | ✓      | ✓    | ✓    | ✓(d) | ✓     | ✓(i)  | ✓     |
| `instruments_master`                                           | ✓    | ✓    | ✓     | ✓    | ✓                 | ✓      | ✓    | ✓    | ✓    | ✓     | ✓     | ✓     |
| `features_and_ml_master`                                       | ✓    | ✓    | ✓     | n/a  | ✓                 | (prop) | ✓    | ✓    | ✓    | n/a   | ✓     | ✓     |
| `strategy_master`                                              | ✓    | ✓    | (n/a) | n/a  | ✓                 | n/a    | ✓    | ✓    | ✓    | n/a   | n/a   | ✓     |
| `execution_master`                                             | ✓    | ✓    | (n/a) | n/a  | ✓                 | n/a    | ✓    | ✓    | ✓    | n/a   | n/a   | ✓     |
| `manifest_master` (cross-cutting SSOT home)                    | ✓    | ✓    | ✓     | ✓    | ✓                 | ✓      | —    | ✓    | ✓    | ✓     | ✓     | ✓     |
| per-AG (`defi`/`cefi`/`tradfi`/`sports`/`predictions`\_master) | ✓    | ✓    | ✓     | ✓    | ✓ (AG reason set) | ✓      | ✓    | ✓    | ✓    | ✓     | ✓     | ✓     |

**Reading the matrix**: every CF column has at least one ✓ owner → the union of the audits covers everything. A column
that goes all-n/a or all-blank is a coverage gap — file the missing check in the most-relevant service audit before
declaring this checklist green.

## How to run the combined audit (operator)

1. Run each per-service audit instruction's "Canonical-form coverage" section (per the triggers in that file).
2. Each emits a per-CF GREEN/RED with the data-state evidence (distribution reads, not constants).
3. Aggregate: every (service × AG × CF) cell GREEN → the pipeline is canonical end-to-end → legacy buckets are
   decommission-ready (hands C-GREEN to `bucket_name_ssot_legacy_dual_write_remediation` L6).
4. Any RED → route to the owning canonicalisation plan's single-walk (never a second walk on the same `_index`).

## Composes with

- `defi_manifest_canonicalisation_2026_06_01.md` §MASTER — the cross-plan coordinator this checklist audits.
- `codex/02-data/availability-manifest-and-data-status.md` — the canonical 4-state manifest contract.
- Single-walk discipline + Data-Pipeline-Correctness HARD RULE (CLAUDE.md).
