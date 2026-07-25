---
doc_type: plan
title: Instruments-store CF canonicalisation — inherited single-walk lineage
summary:
  Split 1 of 3 from instruments_mtds_subset_consistency_remediation_2026_06_17.md (2026-07-24 line-cap remediation,
  clean-partition). Carries the instruments-store canonical-form (CF-1..CF-12) single-walk code-remediation lineage --
  the parent's own INSTRUMENTS-STORE bucket legacy-GCS audit + `_index` canonicalisation (DONE 2026-06-18), plus the
  still-open CF-numbered single-walk items (C0/C-source/C-reasons/E3-E6) migrated in 2026-06-26 from two archived
  sibling plans (`instruments_manifest_canonicalisation_2026_06_01`,
  `issues/instruments_service_audit_findings_2026_06_08`).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [deployment-api, deployment-service, e2e-testing, features-service, instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    instruments,
    manifest,
    canonicalisation,
    single-walk,
    canonical-form,
    audit,
    backfill,
    pipeline-mode,
    data-correctness,
  ]
related:
  [
    instruments_mtds_subset_consistency_remediation_2026_06_17,
    instruments_mtds_consistency_remediation_residuals_2026_07_24,
    mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24,
    plans/audit/results/instruments_mtds_subset_and_consistency_audit_2026_06_17.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: "2026-07-24"
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only # was: orchestrator-agent — corrected 2026-07-25, apply_batch_12: assigned_vm NA => local-only (per instruments_foundation_completeness_2026_06_24.md's 2026-07-14 ruling + task_template.md's pairing table)
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  [
    "instruments_mtds_subset_consistency_remediation_2026_06_17.md (split 1 of 3, plan-hygiene line-cap remediation,
    2026-07-24)",
    "plans/active/issues/plan_line_cap_remediation_2026_07_23.md",
  ]
drift_direction: advance-code
---

# Instruments-store CF canonicalisation — inherited single-walk lineage

> **Split provenance (2026-07-24).** This file is split 1 of 3 out of
> `plans/active/instruments_mtds_subset_consistency_remediation_2026_06_17.md` (2168 lines, over the 1000-line hard-fail
> cap) per `plans/active/issues/plan_line_cap_remediation_2026_07_23.md`'s bucket-(c) clean-partition classification
> (that plan was locked `live-defi-rollout`; operator granted `[unlock-plan]` for this specific split). Content below is
> moved **verbatim** from the parent -- no rewriting, no summarization. The parent plan is trimmed to a coordination
> index pointing here + to the other 2 siblings (`instruments_mtds_consistency_remediation_residuals_2026_07_24.md`,
> `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md`). Two source line ranges from the parent are
> concatenated here: the "INSTRUMENTS-STORE buckets" section (parent L660-734) and the "Folded-in (I-2 consolidation
> 2026-06-26)" section (parent L1910-2003).

## INSTRUMENTS-STORE buckets — legacy GCS audit + `_index` canonicalisation COMPLETE (2026-06-18)

> Operator-granted: delete legacy twins once 100%-verified canonical twin (`gcs_describe`). This is the
> **instruments-store** (reference-data) analogue of the market-data delete work above — a DISTINCT bucket set
> (`instruments-store-{cefi,defi,tradfi,sports}-prd-…` + `instruments-store-pred-prd-…`), NOT the `market-data-tick-*`
> buckets (those are mid-delete and were NOT touched here).

**KEY FINDING — instruments-store has NO `pipeline_mode=`/`asset_group=` twin model.** It is reference data (one AG per
bucket, no batch/live mode): canonical shapes are `prod/catalog.parquet` +
`instrument_availability/by_date/day={D}/.../instruments.parquet` (cefi/defi/tradfi/pred partition by `venue=`; sports
by `league=`/`venue=`). So the market-data "insert `pipeline_mode={mode}_{src}/asset_group={ag}/` twin" model **does not
apply**. A "legacy" object here is a data parquet OUTSIDE those canonical prefixes. READ-ONLY audit:
`instruments-service/scripts/audit_instruments_store_legacy_gcs_delete_list.py` (per-AG delete-list parquet →
`gs://<bucket>/_index/audit/instruments_store_legacy_delete_list_{ag}.parquet`).

| AG         | canonical | control | legacy[bare_day, dash] | SAFE-TO-DELETE | UNMAPPABLE residue (NOT deleted) | manifest `_index` |
| ---------- | --------- | ------- | ---------------------- | -------------- | -------------------------------- | ----------------- |
| cefi       | 28,524    | 7       | 0, 0                   | 0              | 0                                | canonical ✅      |
| defi       | 66,894    | 6       | 0, 0                   | 0              | 0                                | canonical ✅      |
| tradfi     | 11,648    | 8       | 0, 0                   | 0              | 0                                | canonical ✅      |
| sports     | 110,138   | 778,010 | 2, 9,721               | 0              | 9,723 (0.146 GB)                 | canonical ✅      |
| prediction | 4,932     | 50      | 0, 0                   | 0              | 0                                | canonical ✅      |

**Migrate-first + delete: nothing to do (safe outcome).** cefi/defi/tradfi/pred are 100% canonical — zero legacy
objects, nothing to migrate or delete. Sports' two non-canonical shapes are **superseded orphan data from older sports
pipelines, NOT twins of the canonical reference data**, so they are honest-absence residue (excluded from the
delete-list, reported only — never deleted):

- bare top-level `day=2026-03-21/venue=BETFAIR/<hash>.parquet` (n=2): a BETFAIR odds-instrument write (different venue
  than the canonical `venue=API_FOOTBALL_FIXTURES`, no `league=` key → no canonical-rename twin).
- `instrument_availability/by-date/day-{D}/{soccer_slug}/instruments.parquet` (n=9,721, dates 2020-06-06..2025-12-15, 52
  league-slugs): the legacy **dash-separator odds-api source** (`bookmaker_key`/`odds_api_market_id`/`market`/
  `selection` schema; venues ONEXBET/PADDYPOWER/PINNACLE/BETFAIR/UNIBET — from `oddspapi_historical_backfill.py`). The
  canonical `by_date/` (underscore) shape is api-football FIXTURES reference (different data source + schema + a
  non-translatable `soccer_germany_bundesliga`→`BUNDESLIGA` league-slug map), and it COVERS the same date range + is
  written more recently (tip 2026-05-13 > legacy tip 2025-12-15) → the dash shape is superseded, not a twin. Deleting it
  needs an operator/explicit decision (it is orphan stale data, but has no canonical replacement to verify against).
  **MIGRATE-FIRST=0 mappable** — the only "legacy" is unmappable by construction (no canonical-rename target exists).

**`_index` (manifest) canonicalisation — now COMPLETE for ALL 5 AGs** (the N2 2x-per-cell + blank-status v4 shadow
defect). `canonicalize_instruments_store_index.py` was already applied to tradfi+sports; I applied it to **cefi**
(15,933 blanks classified, 12 dups dropped → 28,586→28,574 rows) and **defi** (127,140 blanks classified, 121,109 dups
dropped → 196,987→75,878 rows), and re-ran tradfi idempotently (dropped 3 residual dups → 11,674). Re-verified: **every
AG now has blank_status=0 AND dup_cells=0.** prediction was already clean (500 rows, 0 blank, 0 dup).

- [x] ✅ [SCRIPT] P1. **instruments-store legacy GCS audit + per-AG delete-list** — DONE
      instruments-service@`audit_instruments_store_legacy_gcs_delete_list.py`. cefi/defi/tradfi/pred 100% canonical (0
      legacy); sports 9,723 unmappable-superseded (excluded, reported); SAFE-TO-DELETE=0 fleet-wide → no delete needed.
      Delete-list parquets written to each `_index/audit/`. — instruments-service
- [x] ✅ [SCRIPT] P1. **instruments-store `_index` blank-status/dedup canonical for ALL 5 AGs** — DONE (cefi+defi+tradfi
      `--apply`'d; sports/prediction already clean). Every AG blank_status=0 + dup_cells=0. **⚠ï¸ This was the DEDUP
      pass, NOT the v9 COLUMN pass — see the new v9-column item below.** — instruments-service
- [x] ✅ [SCRIPT] P1. **instruments-store `_index` v9 COLUMN-population for cefi/defi/tradfi/prediction** (the dedup
      pass above was NOT this — audited 2026-06-19, the live IS `_index` was a v4/v8/v9 MIX with `source` 0%,
      `asset_group` column ABSENT, `pipeline_mode` mostly blank). `populate_is_index_v9_2026_06_19.py` row-preservingly
      stamps `schema_version=9` + `asset_group` + `pipeline_mode` (blank→`batch_instruments_service`) + `source`
      (DERIVED PER CELL via `source_string_for(pipeline_mode)`, NOT a default). DeFi additionally venue-canonicalised
      91→58 (PROTOCOL-CHAIN SSOT) + 861 captured spelling-dedup. **APPLIED cefi/defi/prediction** (verified live:
      schema_v9=100%, source/asset_group/pipeline_mode=100%; captured preserved — cefi 36,062 / pred 791 / defi 75,081 =
      −861 legitimate spelling-dedup).

      **tradfi v9-column apply DEFERRED until the running DBEQ/CBOE per-date backfills
                                                                                                              finish** (avoid clobbering their in-flight per-VM-shard writes; the consolidator merges them). Snapshots →
                                                                                                              `_index/snapshots/pre_is_v9_{ag}_2026_06_19`. WRITER ROOT-FIX so new captures don't regress source-blank:
                                                                                                              UTL@f8ec9096 `_stamp_producer_source` stamps `source_string_for(pipeline_mode)` on blank batch producer rows
                                                                                                              (C-#6-identity-safe; +3 regression tests). — instruments-service@7a63be9 + unified-trading-library@f8ec9096

- [ ] [SCRIPT] P3. **`canonicalize_instruments_store_index.py` can't resolve the prediction bucket** — `_bucket_for`
      calls `resolve_bucket_name(kind="instruments-store", asset_group="prediction")` which raises `BucketNamingError`
      (prediction uses the flat `instruments-store-prediction` kind, no per-AG key). Harmless today (prediction `_index`
      is already canonical — 500 rows, 0 blank, 0 dup → nothing to canonicalize), but the `--asset-group prediction`
      choice is a dead path. Fix `_bucket_for` to route prediction →
      `kind="instruments-store-prediction",     asset_group=None` if prediction ever needs re-canonicalisation.
      **NICE-TO-HAVE** (provenance: 2026-06-18 instruments-store audit). — instruments-service

## Folded-in (I-2 consolidation 2026-06-26)

> Open todos migrated here from 2 archived plans during the instruments/MTDS plan consolidation
> (`instruments_mtds_plan_consolidation_2026_06_26.md`). This survivor (I-2) is now the live home for the
> instruments-store canonical-form single-walk (CF-1…CF-12) + the IS-side audit-finding code remediation. Full detail
> lives in the archived sources under `archive/2026_06/` and `archive/issues/`.

### From `instruments_manifest_canonicalisation_2026_06_01` (archived — G1 canonicalisation ROOT)

- [ ] [DATA] P0. **C0 — ONE bundled single-walk per non-sports instruments bucket**: `category=`→`asset_group=` (CF-2) +
      `pipeline_mode=` partition (CF-3) + v9 re-version (CF-1) + env-split (CF-9) + canonical names (CF-7) +
      `available_at` preserve (CF-8) + phantom relabel (CF-10). Server-side `gcs_copy_object`, layout-aware; run on a VM
      (gated on L0). (MIGRATED FROM: `instruments_manifest_canonicalisation_2026_06_01`.)
- [ ] [DATA] P1. **C-source RIDER (CF-4)** — re-consolidate the `source` column into the instruments `_index`
      (multi-source `FIXTURES` = 2 rows); folds the `data_source_provenance` instruments-side re-consolidation (no
      separate walk). (MIGRATED FROM: same.)
- [ ] [CODE] P1. **C-reasons (CF-5)** — instruments writers emit typed `EmptyConfirmedReason` (non-sports AGs);
      fetch-failure → `attempted_failed` not `empty_confirmed` (CF-11 swallow sweep). (MIGRATED FROM: same.)
- [ ] [DATA] P0. **E3** — confirm instruments writer drained; snapshot each `_index`. (MIGRATED FROM: same.)
- [ ] [DATA] P0. **E4** — dry-VM → timing → optimise → run (small: 30k/20k/493 rows; no fire-and-forget). (MIGRATED
      FROM: same.)
- [ ] [DATA] P0. **E5** — manifest rebuild per bucket: `ManifestWriter` stamps `source` + `pipeline_mode` +
      `available_at` + typed reasons → consolidator → v9; writer-fix CF-5/CF-11 so future writes are honest. (MIGRATED
      FROM: same.)
- [ ] [DATA] P0. **E6 + post-walk CF audit** — `cf_manifest_audit_2026_06_01.py` per instruments-store bucket →
      CF-1…CF-12 GREEN, 0 legacy-only cells vs canonical; flip CF-coverage in
      `instruments_master_audit_instructions.md`. ⚠ï¸ IRREVERSIBLE: only after GREEN, hand C-GREEN to L6
      (`bucket_name_ssot…`) → delete the legacy instruments-store buckets permanently. (MIGRATED FROM: same.)

### From `issues/instruments_service_audit_findings_2026_06_08` (archived — IS download→manifest audit)

- [ ] [UTL] P2. **Confirm UTL `record_captured_from_counts` auto-stamps `default_source` for single-source cells** —
      else 9 IS callsites (`orchestrator.py:1730,1916,2080,2693,3588,6910,7702,7895,8137`) write blank-source captured
      cells (CF-4 RED); thread `source=` per callsite if not. Repo: unified-trading-library + instruments-service.
      (MIGRATED FROM: `issues/instruments_service_audit_findings_2026_06_08`.)
- [ ] [MTDS] P2. **`engine/orchestrator.py:4271` `_af_record_empty(reason="")`** — make `reason` a required typed
      `EmptyConfirmedReason` (latent `LegacyBlankErrorReasonError`). Repo: instruments-service. (MIGRATED FROM: same.)
- [ ] [MTDS] P2. **Narrow the broad excepts at `orchestrator.py:3794, 7821`** — `:3794` swallows all on a
      canonical-vs-legacy GCS blob probe then returns legacy (catch `NotFound` only; fix `:3791`
      `# type: ignore[union-attr]`); `:7821` swallows weather-merge errors then writes new-only. `:7673` is NOT a bug
      (safe fallback). Repo: instruments-service. (MIGRATED FROM: same.)
- [ ] [MTDS] P2. **Residual bar-edge fallback-to-open** — `cefi/hyperliquid.py:257`, `cefi/ccxt_adapter.py:310-312`,
      `tradfi/polygon.py:243` fall to the open edge on unknown timeframe; make close-edge derivation total (raise/skip).
      Repo: instruments-service. (MIGRATED FROM: same.)
- [x] ✅ [MTDS] P2. **De-duplicate the IS venue universe** — make the cefi/tradfi/prediction fetch path read UAC
      `VENUES_BY_ASSET_GROUP` instead of hardcoded mirrors. **SHIPPED by `instrument_universe_registry_consolidation`
      Phase 1 — `instruments-service@4da6fe8`** (verified live 2026-06-30): `_CEFI_VENUES`/`_TRADFI_VENUES` DELETED from
      `engine/orchestrator/venue_core.py` (only descriptive comments of the FORMER state remain at :105/:139); cefi
      reads UAC via the named `expand_cefi_tardis_endpoints()` grain-adapter, tradfi via UAC minus
      `_TRADFI_NON_VENUE_KEYS={YAHOO_FINANCE}`, prediction reads `VENUES_BY_ASSET_GROUP[prediction]`;
      `TestVenueProducerUACInvariant` is the regression gate. **`_DEFI_VENUES` (`_build_defi_venues()`) is INTENTIONALLY
      KEPT** — defi is operator-decided EXEMPT from set-equality (registry-consolidation Decision D / A6), with a UAC
      drift-guard (`VENUES_BY_ASSET_GROUP[defi] == get_venues_for_asset_groups(["DEFI"])`). The stale
      `orchestrator.py:1028` line ref no longer holds those mirrors. (MIGRATED FROM: same.)
- [ ] [MTDS] P3. **MTDS prefix-map mirror → read UAC `VENUE_PREFIX_TO_PROTOCOL`** — MTDS
      `cli/handlers/_instruments_metadata.py` keeps a hand-mirror of the venue-prefix→protocol map whose comment cites
      the IS `_SUBGRAPH_VENUE_PREFIX_TO_PROTOCOL` DELETED by registry-consolidation Phase 2 (2026-07-03,
      `unified-api-contracts@9eb5518` moved it to UAC as `VENUE_PREFIX_TO_PROTOCOL`). Swap the mirror for the UAC import
      — exactly the silent-drift class the consolidation kills. Also cosmetic: `unified-trading-system-ui`
      `lib/types/defi.ts:226` comment names the deleted `CANONICAL_VENUE_TO_ADAPTER` — update on next touch. Repo:
      market-tick-data-service (+ UI comment). (Provenance: `instrument_universe_registry_consolidation_2026_06_29`
      close-out.)
- [ ] [MTDS] P2. **Replace `os.environ["DEPLOYMENT_ENV"]="test"` runtime mutation** (`orchestrator.py:8033-8041`,
      `sports_dependency.py:90-98`) with an explicit `env=` param to `resolve_bucket_name` (thread-safety). Repo:
      instruments-service (+ UTL if the param doesn't exist). (MIGRATED FROM: same.)
- [ ] [MTDS] P2. **IBKR systemic-failure hardening (LATENT)** — `tradfi/ibkr.py:337-348` per-symbol isolation is
      correct; harden the systemic case (`_ib is None`/all-fail → `[]` no raise) when/if IBKR becomes a live reference
      venue (not in `_TRADFI_VENUES` today). Repo: instruments-service. (MIGRATED FROM: same.)
- [ ] [INFRA] P2. **Prediction catalogue bucket mismatch** —
      `deployment-service/terraform/gcp/lifecycle_catalogue_scheduler.tf:40-44` targets `instruments-store-prediction-…`
      vs SSOT `instruments-store-PRED-…`; reconcile to the SSOT bucket. Repo: deployment-service. (MIGRATED FROM: same.)
- [ ] [CLAUDE-MD] P2. **Correct the over-broad "instruments-service owns all venue URLs via `InstrumentRecord`" line** —
      `InstrumentRecord` carries only `source_archive_url_template` + coverage windows; live REST/WS endpoints are UAC
      registries. (MIGRATED FROM: same.)
- [ ] [AUDIT] P2. **Fix `instruments_master_audit_instructions.md` item (g)** — "`rg URDI` → 0 hits" is wrong;
      `urdi_reference_provider.py` is the LIVE fetch spine. Replace with "no NEW URDI refs" + fix the stale error
      message at `urdi_reference_provider.py:116` (points to a deleted repo). (MIGRATED FROM: same.)
- [ ] [MTDS] P3. **Investigate systemic schema-drift dup** (`scripts/dedupe_manifest_schema_drift.py`): 16% of shards
      have >1 manifest row (multi-schema-version + `instrument_type` casing + capture_status collisions). Fix
      WRITER-side row-key idempotency + instrument_type normalization so the ~76/96 repair scripts stop being needed.
      Repo: unified-trading-library (writer) + instruments-service. (MIGRATED FROM: same.)
- [x] ✅ [MTDS] P3. **Split the `instruments-service` `engine/orchestrator.py` (8,192 lines, 9Ã the 900 cap)** into
      focused modules (buckets/emission/weather/fixtures/manifest). Repo: instruments-service. **NB: distinct from the
      MTDS `engine/orchestrator.py` (4,219L) split tracked in M-2 — same filename, different repo; do not conflate.**
      (MIGRATED FROM: same.) — instruments-service@cb51c98a0: split into `engine/orchestrator/` package (22 focused
      modules + thin `__init__`).
- [ ] [SCRIPT] P3. **Script-tier cloud-agnostic sweep** — ~60 scripts `from google.cloud import storage`/`boto3` →
      `get_storage_client()`; ~30 inline legacy bucket literals → `resolve_bucket_name`;
      `enumerate_expected_universe.py:1381` hardcoded `/tmp/` → `tempfile.gettempdir()`. Repo: instruments-service.
      (MIGRATED FROM: same.)
- [ ] [PLAN] P3. **Delete the orphaned static-snapshot catalogue path** (`reference_data/catalogue/catalogue_builder.py`
      `CatalogueBuilder` + `orchestrator.py refresh_catalogue`) — superseded by `build_instrument_catalogue.py`, no
      CLI/TF/test caller. Repo: instruments-service. (MIGRATED FROM: same.)
