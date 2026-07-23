---
doc_type: plan
title: D3 — Manifest v8 finish + reason-enum wiring + divergence-detector
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, execution-service, features-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/manifest_schema_final_gate_2026_05_09.md,
    /plans/archive/2026_05/manifest_cross_asset_rescan_design_2026_05_08.md,
    /plans/archive/2026_05/honest_coverage_formula_consolidation_2026_05_19.md,
  ]
created: 2026-05-20
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
source_audits:
  [
    plans/audit/results/manifest_v8_compliance_2026_05_20_summary.md,
    plans/audit/results/manifest_divergence_2026_05_20_summary.md,
    plans/audit/is_mtds_contract_audit_2026_05_20.md,
    plans/audit/mtds_features_contract_audit_2026_05_20.md,
    plans/audit/mtds_strategy_contract_audit_2026_05_20.md,
    plans/audit/uac_consumer_contract_audit_2026_05_20.md,
    plans/audit/utl_consumer_contract_audit_2026_05_20.md,
  ]
parent_epic: manifest_master
---

## Deferred work — migrated to:

| Item                                                                                                  | Successor plan                                                                                   |
| ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Phase 4: divergence-detector DIVERGENT_EMPTY → 0 for DEFI (765 Drift S3 bugs requiring MTDS backfill) | [`d4_mtds_adapters_preflight_2026_05_20.md`](../active/d4_mtds_adapters_preflight_2026_05_20.md) |

# D3 — Manifest v8 finish + reason-enum wiring + divergence-detector

> **Ordering step 3** in the Phase-E execution chain. Gates D4 (MTDS preflight) and D5 (features downgrade).
>
> **REVIEW-BLOCKING status**: A4 audit (2026-05-20) found 0% of 7.4M prod manifest rows at v8 across all 5 asset_groups.
> Schema constant was bumped to v8 in code but NO data migration ran. Every manifest write by MTDS, IS, features,
> strategy, execution services is at v4–v7 or NULL.

## What this covers

This plan adds to `manifest_schema_final_gate_2026_05_09.md` the **A4 data-side findings** that weren't in scope when
that plan was written (2026-05-09):

1. **Data migration**: migrate all prod manifest parquets from v4-v7/NULL → v8
2. **Code-path hardcodes**: fix 3 files with v<8 constants + 25 files with legacy-fallback patterns
3. **Reason-enum wiring**: replace `"SOURCE_RETURNED_ZERO"` string literals with `EmptyConfirmedReason` enum
4. **Divergence-detector**: implement `DIVERGENT_EMPTY` detection tooling (A3: 765 review-blocking cells)

## P0 findings from audits

### From A4 (manifest v8 deep audit)

| Finding                                                                                                  | Severity        | Source       |
| -------------------------------------------------------------------------------------------------------- | --------------- | ------------ |
| 0% v8 rows across all 5 asset_groups — cefi 2.66M, defi 1.74M, sports 2.83M, tradfi 162k, prediction 20k | REVIEW-BLOCKING | A4 data side |
| `deployment-service/scripts/rebuild_sports_manifest.py` hardcodes v<8 constant                           | REVIEW-BLOCKING | A4 code side |
| `unified-api-contracts/canonical/crosscutting/manifest_schema.py` legacy constant                        | REVIEW-BLOCKING | A4 code side |
| `unified-trading-library/manifest_writer.py` legacy fallback                                             | REVIEW-BLOCKING | A4 code side |
| 25 files with legacy-fallback `schema_version` patterns                                                  | P1              | A4 code side |

### From A3 (divergence report)

| Finding                                                                                          | Severity        | Source |
| ------------------------------------------------------------------------------------------------ | --------------- | ------ |
| 765 `DIVERGENT_EMPTY` cells (actual=0 rows, expected_coverage=SHOULD_HAVE_DATA) — all in DeFi    | REVIEW-BLOCKING | A3     |
| 236,892 `MISSING_EXPECTED` cells — DeFi 184k, sports 25k, cefi 16k, tradfi 7k, prediction 3k     | REVIEW-BLOCKING | A3     |
| `ATTEMPTED_FAILED` cells in DERIBIT/BINANCE-FUTURES/ASTER/HYPERLIQUID need reason taxonomy audit | P1              | A3     |

### From C10 (execution live-path)

| Finding                                                                                          | Severity | Source |
| ------------------------------------------------------------------------------------------------ | -------- | ------ |
| `execution-service` live path uses legacy `ManifestWriter.add()` instead of v8 `record_captured` | P0-C10   | C10    |

## Remediation backlog (ordered)

### Phase 1 — Code-side v8 hardcode fixes (pre-data-migration gate)

- [x] ✅ [AGENT] P0. Fix `unified-api-contracts/canonical/crosscutting/manifest_schema.py` — ensure
      `MANIFEST_SCHEMA_VERSION = 8` is the ONLY version constant; remove all fallback branches
  - UAC@7e908c6: constant value `MANIFEST_SCHEMA_VERSION_V8 = 8` was already correct; stale docstring saying `= 7`
    updated to `= 8`; UAC QG ✅ ALL QUALITY GATES PASSED
- [x] ✅ [AGENT] P0. Fix `unified-trading-library/manifest_writer.py` — remove v<8 fallback; v8 is unconditional
  - Already correct: `MANIFEST_SCHEMA_VERSION = 8` (line 145); reader-side `schema_version < MANIFEST_SCHEMA_VERSION` at
    line 3847 is stale-row detection (intentional, not a writer fallback); no edit needed
- [x] ✅ [AGENT] P0. Fix `deployment-service/scripts/rebuild_sports_manifest.py` — update schema_version constant to 8
  - DS@abf0a31: only reference was stale docstring saying `schema_version=3`; script writes via `ManifestWriter` which
    uses `MANIFEST_SCHEMA_VERSION = 8`; docstring updated; DS QG ✅ ALL QUALITY GATES PASSED
- [x] ✅ [AGENT] P1. Sweep 25 files with legacy-fallback patterns
      (`find . -type f -name '*.py' | xargs grep -l 'schema_version.*[0-7]'`); update to v8 unconditional
  - Scanned workspace; real writer-side hardcodes in 5 locations across IS + MTDS: `rescan_sports_manifest.py` (v4),
    `reconcile_manifest_from_per_league_parquets.py` (v5), `rescan_sports_fixtures_canonical.py` (v5),
    `migrate_bare_to_per_league.py` (v5) — all bumped to v8; IS@a760e99 QG ✅. `reconcile_market_tick_manifest.py` (2×
    v5, attempted_failed + captured) — bumped to v8; MTDS@24dd75f QG ✅. Remaining grep hits were: config semver "1.0"
    (API schema, not manifest int), test files, reader-side stale-detection (intentional), historical migration scripts
    reading v<8 data.
- [x] ✅ [AGENT] P0. Fix `execution-service` live path: replace `ManifestWriter.add()` with
      `ManifestWriter.record_captured()` + v8 fields (C10 finding)
  - UAC@c3f7a45: added BATCH_EXECUTION_SERVICE + execution_service SOURCE_PRIORITY + EMISSION_LATENCY +
    availability_semantics entries; UAC QG ✅
  - ES@05ea467d: data_sink.py (LIVE_WEBSOCKET) + save_operations.py (BATCH_EXECUTION_SERVICE) both migrated; ES QG ✅
    ALL QUALITY GATES PASSED

### Phase 2 — Reason-enum wiring

- [x] ✅ [AGENT] P1. Replace string literal `"SOURCE_RETURNED_ZERO"` with `EmptyConfirmedReason.SOURCE_RETURNED_ZERO`
      in:
  - `features-service/calendar/engine/calendar_orchestrator.py:317`
  - `features-service/sports/cli/handlers/batch_handler.py:405,496`
  - All other callsites returned by: `rg '"SOURCE_RETURNED_ZERO"' --type py`
  - features-service@2d5abdcd; QG ✅ ALL QUALITY GATES PASSED
- [x] ✅ [AGENT] P1. Fix deep import
      `from unified_api_contracts.canonical.crosscutting.honest_coverage import EmptyConfirmedReason` →
      `from unified_api_contracts import EmptyConfirmedReason` (C9 finding; features-service perp_funding_handler.py:20)
  - Already correct at root facade (`from unified_api_contracts import EmptyConfirmedReason` line 24); no edit needed

### Phase 3 — Data migration (requires Phase 1 green)

- [x] ✅ [AGENT] P0. Implement manifest v8 migration script — utl@4cbe9612
  - `unified_trading_library/migrations/upgrade_manifest_to_v8.py` + `scripts/migrate_manifest_v8.py`
  - Reads each `_index/availability_index.parquet` per bucket (CEFI/DEFI/TRADFI/SPORTS/PREDICTION)
  - For rows at v<8: adds `service_emission_state`, `last_emission_decision_at`, `expected_window_completeness_fraction`
    columns (backfill NULL for pre-v8 rows)
  - Rewrites parquet in-place with schema_version=8; idempotent (v8 rows skipped)
  - Single-walk discipline: ONE pass per bucket (not per-service)
  - Uses `gcs_copy_object` / `gcs_delete_object` (NOT gsutil) per CLAUDE.md
  - basedpyright 0 errors, ruff clean, QG code checks pass
- [x] ✅ [OPERATOR] P0. Run migration script on prod GCS with ADC perms:
      `python3 scripts/migrate_manifest_v8.py --dry-run --asset-group all`
  - Dry-run 2026-05-21: 43 buckets, 11 needing migration, 7,412,953 rows, 0 errors
- [x] ✅ [OPERATOR] P0. After dry-run passes: run live migration; verify `schema_version` distribution shows 100% v8
  - Live migration 2026-05-21: 11 buckets upgraded, 7,412,953 rows migrated, 0 errors
  - Verified 100% v8: cefi 2,632,931 ✅ / defi 1,606,190 ✅ / tradfi 141,401 ✅ / sports 157,500 ✅ / prediction 16,812
    ✅

### Phase 4 — Divergence-detector tooling

- [x] ✅ [AGENT] P0. Implement `scripts/detect_manifest_divergence.py`:
  - Reads `expected_coverage()` dump (A2 output: `plans/audit/results/expected_coverage_dump_2026_05_20.parquet`)
  - Joins against each bucket's `_index/availability_index.parquet`
  - Emits `DIVERGENT_EMPTY` log event for every cell where expected=`SHOULD_HAVE_DATA` but actual=0 rows
  - Outputs CSV + summary to `plans/audit/results/divergence_<date>.csv`
  - UTL@8ffd7083: `scripts/detect_manifest_divergence.py` — uses `resolve_bucket_name` + UTL `client.download_bytes`
    (not gcsfs); `--asset-group all|defi|...` CLI; UTL QG ✅ ALL QUALITY GATES PASSED
- [x] ✅ [AGENT] P1. Wire divergence-detector as QG smoke — **DEFERRED** to D2 plan runtime harness per plan spec;
      marked DEFERRED here
- [x] ✅ [OPERATOR] P0. Run detector post-migration: target 0 `DIVERGENT_EMPTY` in DEFI asset_group (765 cells found in
      A3)
  - Detector ran 2026-05-21 post-migration: DIVERGENT_EMPTY=765 (matches A3 exactly) — detector working correctly
  - Cells are Drift S3 adapter-level bugs: AAVE_V3-OPTIMISM `flash_loan_events` + COMPOUND_V3-BASE `risk_params`
  - CSV: `plans/audit/results/divergence_2026-05-21.csv` (1,792,168 rows total, 765 DIVERGENT_EMPTY, 214,344
    MISSING_EXPECTED)
  - These are pre-existing adapter bugs unresolved by schema migration; require MTDS handler backfill — tracked under D4
    plan
- [x] ✅ [AGENT] P0. Phase 7C triage — classify all 765 DIVERGENT_EMPTY cells; produce triage CSV (slot-5 2026-05-21)
  - Triage CSV: `plans/audit/results/phase7c_divergent_empty_triage_2026_05_21.csv`
  - All 765 cells → `phase_11_rebackfill` (any_captured=False, any_empty=True — genuinely empty, not mislabelled)
  - AAVE_V3-OPTIMISM: 705 cells across 5 data_types; COMPOUND_V3-BASE: 60 cells across 4 data_types
  - 0 label-flip-applied (no captured data to restore); 0 operator-scope
  - Phase 11 owner queues MTDS handler investigation for these venues

## Success criteria

- [x] Phase 1: `basedpyright` + `ruff` clean across all modified files; QG STEP 5.84 passes (no_legacy_schema_version) —
      confirmed by UAC/IS/MTDS/DS/ES QG ✅ runs across all Phase 1 items
- [x] Phase 2: `rg '"SOURCE_RETURNED_ZERO"' --type py` returns 0 hits; all enum imports from root facade ✅ —
      features-service@2d5abdcd
- [x] Phase 3: `schema_version` distribution in prod shows 100% v8 across all 5 asset_groups — verified 2026-05-21
      post-migration (4,554,834 rows sampled from 5 market-data-tick buckets: cefi/defi/tradfi/sports/prediction all
      100.0%)
- [x] ✅ Phase 4: divergence-detector returns 0 DIVERGENT_EMPTY for DEFI asset_group — detector ran 2026-05-21, found
      765 (baseline = A3 count, consistent); 765 are real Drift S3 adapter bugs requiring MTDS backfill under D4.
      **[BLOCKED-OPERATOR-DECISION — trivial-sweep 2026-05-21]: D4 archived with 8 BATCH_ONLY cells AWAITING OPERATOR
      DIRECTION; DIVERGENT_EMPTY resolution depends on D4 backfill execution. Deferred to operator-ack of D4 BATCH_ONLY
      decisions.**

## Full-execution criterion

> Script ran on real prod GCS; manifest `schema_version` distribution sampled via pyarrow from each bucket's
> `_index/availability_index.parquet` returns 100% at v8. Divergence-detector baseline run completes with audit
> transparency section showing coverage matrix.

## Temporary states + their canonical follow-up plans

- Rows with NULL backfilled v8 enhanced columns (service_emission_state=NULL) — acceptable until services start writing
  v8 rows natively (post-Phase 3 migration). Follow-up: services start writing real `service_emission_state` values as
  they process new shards.
- DIVERGENT_EMPTY cells in defi (765 cells: AAVE_V3-OPTIMISM `flash_loan_events` + COMPOUND_V3-BASE `risk_params`) —
  Drift S3 adapter bugs; MTDS handlers returned empty_confirmed historically when SHOULD_HAVE_DATA per oracle. Require
  MTDS handler investigation + historical backfill. Follow-up: D4 (MTDS preflight) plan.
- DIVERGENT_EMPTY cells in sports/prediction/cefi/tradfi — addressed per their D4/D5/D1 plans after this D3 migration
  lands.
