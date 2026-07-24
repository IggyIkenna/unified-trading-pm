---
doc_type: audit-result
title: Manifest v8 Compliance Audit — 2026-05-20
summary:
  Manifest v8 compliance audit (data + code) — 0% of 7,412,946 prod MTDS+IS manifest rows are at v8 (max v7; 1,336,749
  NULL schema_version rows, mostly defi); code side flags deployment-service/scripts/rebuild_sports_manifest.py writing
  schema_version=3 and migrate_solana_defi_v4_to_v8.py never executed; 25 legacy-fallback files need sunset dates.
status: fail
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [agent-orchestrator, deployment-api, deployment-service, execution-service, features-service, instruments-service]
scope: [engineer, admin]
tags: [audit, manifest, data-correctness, migration, data-status, quality-gates]
related:
  [
    /plans/audit/results/archive/manifest_v8_compliance_2026_05_20_summary.md,
    /plans/audit/results/archive/manifest_v8_per_vm_shards_2026_05_20_summary.md,
  ]
created: 2026-05-20
audited_scope:
  All 10 MTDS+IS prod _index/availability_index.parquet files (full row count by schema_version) + workspace-wide code
  scan of manifest-consumer files for schema_version/capture_status/available_at usage and hardcoded v<8 constants
date: 2026-05-20
auditor: slot-3 sub-agent
parent_epic: manifest_master
severity: P0
resulting_plan:
lib_version:
doc_versions_checked:
---

# Manifest v8 Compliance Audit — 2026-05-20

_Produced by: slot-3 sub-agent (READ-ONLY). Scan timestamp: 2026-05-20._ _Data read from prod GCS via gsutil cp +
pandas. Code scanned via ripgrep + manual read._

---

## Audit scope

### What was scanned exhaustively

- **Data side**: All 10 `_index/availability_index.parquet` files for MTDS + IS across 5 asset groups (cefi, defi,
  tradfi, sports, prediction) were downloaded from prod GCS and read in full. Every row was counted and grouped by
  `schema_version`. No sampling — full corpus read.
- **Code side**: `rg` across all Python source files in TAB_ROOT (`.tabs/3/`) excluding `.venv*`, `__pycache__`,
  `node_modules`. Files matched: all files referencing `schema_version`, `capture_status`, `available_at` in service
  source and scripts. Key service directories examined: `market-tick-data-service`, `instruments-service`,
  `features-service`, `deployment-api`, `deployment-service`, `strategy-service`, `execution-service`,
  `unified-trading-library`, `unified-api-contracts`.

### Gaps in coverage

- **Code side**: `market-data-processing-service`, `agent-orchestrator`, `strategy-service/engine/strategies` deep trees
  were checked for `schema_version`/`capture_status` patterns but not read file-by-file (too many files; rg pattern scan
  is exhaustive for the specific patterns queried).
- **Data side**: The `solana-defi-*` buckets and `evm-defi-*` buckets were NOT checked — these are additional DeFi data
  stores separate from `market-data-tick-defi-prd`. A separate scan of those buckets is required (see Remediation
  section). The `features-*` and `strategy-store-*` buckets were not checked (those services write their own manifests;
  out of scope for MTDS + IS audit).
- An existing A4 scan script (`plans/audit/results/a4_manifest_v8_compliance.py`) was run earlier the same day
  (2026-05-20T10:30:27Z) and produced `_summary.md` + `_data.csv` + `_code.csv`. The data read in this audit fully
  corroborates those results (same row counts per bucket per schema_version). The `_summary.md` file has a discrepancy
  in its per-asset-group NULL row count rollup (shows 0 NULL rows for defi, tradfi, sports, prediction — but the raw
  `_data.csv` shows 1,286,260 NULL for defi + 35,033 NULL for tradfi + 13,176 NULL for sports + 2,280 NULL for
  prediction). The corrected totals are in the table below.

---

## Dimension 1 — Data side (schema_version distribution in prod manifests)

### Per-bucket, per-schema-version row counts

| asset_group | service | bucket                                              | schema_version |      rows |
| ----------- | ------- | --------------------------------------------------- | -------------: | --------: |
| cefi        | IS      | instruments-store-cefi-prd-central-element-323112   |              4 |    12,361 |
| cefi        | IS      | instruments-store-cefi-prd-central-element-323112   |              6 |    18,021 |
| cefi        | MTDS    | market-data-tick-cefi-prd-central-element-323112    |              4 |    16,224 |
| cefi        | MTDS    | market-data-tick-cefi-prd-central-element-323112    |              5 |    30,704 |
| cefi        | MTDS    | market-data-tick-cefi-prd-central-element-323112    |              6 | 2,246,785 |
| cefi        | MTDS    | market-data-tick-cefi-prd-central-element-323112    |              7 |   339,218 |
| defi        | IS      | instruments-store-defi-prd-central-element-323112   |              4 |    69,630 |
| defi        | IS      | instruments-store-defi-prd-central-element-323112   |              6 |    58,266 |
| defi        | MTDS    | market-data-tick-defi-prd-central-element-323112    |              6 |   308,330 |
| defi        | MTDS    | market-data-tick-defi-prd-central-element-323112    |              7 |    11,600 |
| defi        | MTDS    | market-data-tick-defi-prd-central-element-323112    |           NULL | 1,286,260 |
| tradfi      | IS      | instruments-store-tradfi-prd-central-element-323112 |              4 |    11,301 |
| tradfi      | IS      | instruments-store-tradfi-prd-central-element-323112 |              6 |     8,897 |
| tradfi      | MTDS    | market-data-tick-tradfi-prd-central-element-323112  |              4 |    16,656 |
| tradfi      | MTDS    | market-data-tick-tradfi-prd-central-element-323112  |              6 |    89,272 |
| tradfi      | MTDS    | market-data-tick-tradfi-prd-central-element-323112  |              7 |       440 |
| tradfi      | MTDS    | market-data-tick-tradfi-prd-central-element-323112  |           NULL |    35,033 |
| sports      | IS      | instruments-store-sports-prd-central-element-323112 |              2 |       434 |
| sports      | IS      | instruments-store-sports-prd-central-element-323112 |              4 |    11,752 |
| sports      | IS      | instruments-store-sports-prd-central-element-323112 |              5 |   481,109 |
| sports      | IS      | instruments-store-sports-prd-central-element-323112 |              6 | 1,409,896 |
| sports      | IS      | instruments-store-sports-prd-central-element-323112 |              7 |   759,329 |
| sports      | IS      | instruments-store-sports-prd-central-element-323112 |           NULL |    13,176 |
| sports      | MTDS    | market-data-tick-sports-prd-central-element-323112  |              4 |    17,288 |
| sports      | MTDS    | market-data-tick-sports-prd-central-element-323112  |              6 |   140,212 |
| prediction  | IS      | instruments-store-pred-prd-central-element-323112   |              4 |     3,145 |
| prediction  | IS      | instruments-store-pred-prd-central-element-323112   |              6 |       795 |
| prediction  | MTDS    | market-data-tick-pred-prd-central-element-323112    |              4 |    14,296 |
| prediction  | MTDS    | market-data-tick-pred-prd-central-element-323112    |              5 |         2 |
| prediction  | MTDS    | market-data-tick-pred-prd-central-element-323112    |              6 |       234 |
| prediction  | MTDS    | market-data-tick-pred-prd-central-element-323112    |           NULL |     2,280 |

**Note on NULL rows**: NULL `schema_version` means the row was written before the `schema_version` column was added
(pre-v5 manifest writer). These rows pre-date the column's introduction and their `capture_status` column is also
absent; the UTL read path coerces them to `capture_status="captured"` and `schema_version=1` (default=1 in `from_dict`).

### Per-asset-group rollup (corrected — including NULL rows in non_v8 count)

| asset_group |    total_rows | v8_rows |    v8_pct | non_v8_rows (v<8) | null_schema_version_rows |
| ----------- | ------------: | ------: | --------: | ----------------: | -----------------------: |
| cefi        |     2,663,313 |       0 |     0.00% |         2,663,313 |                        0 |
| defi        |     1,734,086 |       0 |     0.00% |           447,826 |                1,286,260 |
| tradfi      |       161,599 |       0 |     0.00% |           126,566 |                   35,033 |
| sports      |     2,833,196 |       0 |     0.00% |         2,819,844 |                   13,176 |
| prediction  |        20,752 |       0 |     0.00% |            18,472 |                    2,280 |
| **TOTAL**   | **7,412,946** |   **0** | **0.00%** |     **6,075,021** |            **1,336,749** |

### VERDICT — DATA SIDE: REVIEW-BLOCKING

**0% of 7,412,946 prod manifest rows are at v8.** Every single row is at v2/v4/v5/v6/v7 or NULL `schema_version`. The
manifest v8 migration has NOT been applied to any MTDS or IS production bucket.

The highest schema version present in any bucket is v7 (cefi/MTDS: 339,218 rows; defi/MTDS: 11,600 rows; tradfi/MTDS:
440 rows; sports/IS: 759,329 rows). The majority of rows are at v6 (cefi: 2,246,785 in MTDS alone). Pre-v5 rows (NULL
schema_version) account for 1,336,749 rows, almost all in the defi MTDS bucket (1,286,260).

---

## Dimension 2 — Code-path side (v8 consumer readiness)

### Code scan methodology

Scanned for: (a) `schema_version` references, (b) `capture_status` and `available_at` usage (v8 enhanced fields), (c)
hardcoded version literals <8, (d) legacy-fallback coercion patterns.

### Per-service v8 readiness summary

| service                         | key_files_checked                                                                                                                | reads_schema_version                                   | handles_pre_v8_rows                                                                                | uses_capture_status                             | uses_available_at                          | status                       |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------ | ---------------------------- |
| unified-trading-library (UTL)   | `manifest_writer.py`, `manifest_completeness.py`, `reconcile/manifest.py`                                                        | YES — `MANIFEST_SCHEMA_VERSION = 8` at line 145        | YES — `default=1` in `from_dict`, coerces `capture_status` on read; reader-fallback window comment | YES                                             | YES                                        | COMPLIANT-WITH-LEGACY-BRIDGE |
| market-tick-data-service (MTDS) | `cli/handlers/data_manifest_handler.py`                                                                                          | YES — hardcodes `"schema_version": 8` at line 530      | NO explicit pre-v8 branch in handler                                                               | YES (`capture_status` + `available_at` written) | YES                                        | V8-WRITER-COMPLIANT          |
| instruments-service (IS)        | `config_reloaders.py`, `scripts/*`                                                                                               | PARTIAL (scripts only; service source via UTL)         | YES (script coercions)                                                                             | YES (via UTL)                                   | YES (via UTL)                              | COMPLIANT-VIA-UTL            |
| features-service                | `scripts/sports/features_sports_reconcile_available_at.py`                                                                       | NO (reads `available_at` but not `schema_version`)     | YES (`capture_status` fallback for v4 rows in smoke_matrix.py)                                     | YES                                             | YES                                        | COMPLIANT-VIA-UTL            |
| deployment-api                  | `services/data_status_service.py`, `services/data_status_drilldown.py`, `services/shard_detail.py`, `services/coverage_drift.py` | YES (reads manifest `capture_status`)                  | YES — explicit fallback: `"capture_status" not in df.columns → default captured"` pre-v5 bridge    | YES                                             | YES (via `_compute_available_at_envelope`) | COMPLIANT-WITH-LEGACY-BRIDGE |
| strategy-service                | `strategy_service/manifest_allocation_guard.py`                                                                                  | NO (reads `capture_status` only, not `schema_version`) | YES — `capture_status="unknown"` on read errors; handles `attempted_failed`                        | YES                                             | NO (not needed for allocation guard)       | V8-FIELD-PARTIAL             |
| execution-service               | (no manifest consumer files found in source)                                                                                     | NO                                                     | N/A                                                                                                | NO                                              | NO                                         | NOT-A-MANIFEST-CONSUMER      |
| deployment-service              | `scripts/rebuild_sports_manifest.py`                                                                                             | YES — hardcodes `schema_version=3` (REVIEW-BLOCKING)   | N/A — script writes v3, not v8                                                                     | NO (script does not write `capture_status`)     | NO                                         | NON-COMPLIANT                |

### Hardcoded pre-v8 schema version constants (REVIEW-BLOCKING — 3 files)

| repo                    | file                                                              | line            | hardcoded_value    | context                                                                                                                                                                                |
| ----------------------- | ----------------------------------------------------------------- | --------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| deployment-service      | `scripts/rebuild_sports_manifest.py`                              | 4 (docstring)   | `schema_version=3` | Script writes sports manifest rows with `schema_version=3`; does NOT write `capture_status` or `available_at`. Docstring explicitly states "league_id populated and schema_version=3". |
| unified-api-contracts   | `unified_api_contracts/canonical/crosscutting/manifest_schema.py` | (via code scan) | v<8 literal        | Found by A4 script; needs direct read to confirm exact context.                                                                                                                        |
| unified-trading-library | `unified_trading_library/manifest_writer.py`                      | 2803            | `default=1`        | `schema_version=_i("schema_version", default=1)` in `from_dict` — this is the READER legacy-coercion path (correct: pre-column rows deserialise to v1). NOT a writer violation.        |

**Important note on UTL `manifest_writer.py`**: The `MANIFEST_SCHEMA_VERSION = 8` constant at line 145 is correct. The
`default=1` at line 2803 is the `from_dict` read-path default for rows that predate the `schema_version` column. This is
intentional backwards-compatibility, not a write-path error. The A4 scan script flagged it as a v<8 literal but in
context it is the correct coercion for legacy NULL rows.

**Unambiguous write-path violation**: `deployment-service/scripts/rebuild_sports_manifest.py` explicitly sets
`schema_version=3` when building new manifest rows. Any time this script is run it produces non-v8 rows in production.

### Legacy-fallback patterns requiring sunset dates (25 files)

The following files contain legacy-fallback code paths (handling pre-v5/pre-v8 rows, coercing absent `capture_status`,
accepting NULL `schema_version`). Per CLAUDE.md "Temporary state must have a named successor plan," each needs an
explicit sunset date or named follow-up plan:

| repo                           | file                                             | pattern                                                                  | sunset_plan                                                                |
| ------------------------------ | ------------------------------------------------ | ------------------------------------------------------------------------ | -------------------------------------------------------------------------- |
| unified-trading-library        | `manifest_writer.py`                             | `default=1` for schema_version read; `capture_status` coerce-to-CAPTURED | Named in manifest_schema_final_gate plan; sunset = Phase-7 walk completion |
| unified-trading-library        | `manifest_reader_fallback.py`                    | Explicit pre-v8 reader fallback                                          | READER_FALLBACK_WINDOW_DAYS — should have sunset date                      |
| unified-trading-library        | `manifest_migrations/v7_to_v8.py`                | Migration code (12 legacy-fallback counts)                               | One-shot migration; sunset = post-Phase-7 walk                             |
| deployment-api                 | `services/data_status_service.py`                | `"capture_status" not in df.columns` → default captured                  | No named successor plan identified                                         |
| deployment-api                 | `services/data_status_drilldown.py`              | `pre-v8 manifest rows lack these keys` comment + handling                | No named successor plan identified                                         |
| market-tick-data-service       | `engine/orchestrator.py`                         | Legacy-fallback (2 counts)                                               | No named successor plan identified                                         |
| market-tick-data-service       | `scripts/migrate_solana_defi_v4_to_v8.py`        | Reads v4 rows by design (migration script)                               | One-shot; `last_executed: NEVER` (script has never run)                    |
| instruments-service            | `scripts/reconcile_phantom_manifest_rows_all.py` | pre-v8 capture_status absent handling                                    | One-shot reconcile scripts                                                 |
| market-data-processing-service | `scripts/reprocess_sports_odds.py`               | Legacy-fallback (2 counts)                                               | No named successor plan identified                                         |

Full 25-file list is in `plans/audit/results/manifest_v8_compliance_2026_05_20_code.csv`.

### V8 enhanced fields usage (capture_status, available_at, schema_version)

All active service source paths (MTDS handler, IS, features-service, deployment-api, strategy-service) correctly consume
`capture_status`. The `available_at` field is consumed by deployment-api (shard_detail, compute_available_at_envelope)
and features-service. The `schema_version` field is used as a staleness gate in `manifest_writer.py`
(`row.get("schema_version", 1) < MANIFEST_SCHEMA_VERSION → stale`) — meaning **any row at v<8 in production is currently
treated as stale and will be re-fetched**, which is the correct behavior but also means the entire 7.4M row corpus
triggers stale-detection on every preflight pass.

---

## Summary — review-blocking findings

### FINDING 1 (REVIEW-BLOCKING — DATA): 0% v8 compliance across all 5 asset groups

**Severity: P0 — blocks all layer-N+1 work per foundation-completion-gate discipline.**

Zero rows at v8 in any of the 10 scanned prod manifests (MTDS + IS, all 5 asset groups). Total rows affected: 7,412,946.
Max schema_version present: v7. This confirms the reference incident described in CLAUDE.md "Data Pipeline Correctness"
rule: "0% of 7.4M prod manifest rows at v8 despite constant bump."

The v8 migration scripts exist (`market_tick_data_service/scripts/migrate_solana_defi_v4_to_v8.py`) with
`last_executed: NEVER`. The Phase-3 GCS migration (completed 2026-05-19) migrated parquet file paths/filenames but did
NOT update `schema_version` in the manifest index rows.

### FINDING 2 (REVIEW-BLOCKING — CODE): rebuild_sports_manifest.py writes schema_version=3

**Severity: P0 — actively creates non-v8 rows if script is re-run.**

`deployment-service/scripts/rebuild_sports_manifest.py` has `schema_version=3` hardcoded and does not write
`capture_status` or `available_at`. Re-running this script would further degrade v8 compliance.

### FINDING 3 (REVIEW-BLOCKING — DATA): 1,336,749 NULL schema_version rows

**Severity: P0 — these rows have neither `schema_version` nor `capture_status` columns.**

Concentrated in `market-data-tick-defi-prd` (1,286,260 rows). These pre-date the schema_version column introduction. The
UTL reader coerces them to `capture_status="captured"` with `schema_version=1` default, but they cannot be directly
validated for correctness. The stale-detection gate (`row.get("schema_version", 1) < MANIFEST_SCHEMA_VERSION`) treats
them as stale, causing unnecessary re-fetches.

### FINDING 4 (WARNING): migrate_solana_defi_v4_to_v8.py has never been executed

**Severity: P1 — the migration tool exists but has not run.**

`market_tick_data_service/scripts/migrate_solana_defi_v4_to_v8.py` has `last_executed: NEVER` in its runbook header. The
DeFi MTDS manifest bucket has 1,286,260 NULL rows + 319,930 v6/v7 rows that this script would migrate.

### FINDING 5 (WARNING): 25 legacy-fallback files lack named successor plans / sunset dates

**Severity: P2 — CLAUDE.md requires "temporary state must have a named successor plan."**

Some of these files (especially `deployment-api/services/data_status_service.py`,
`deployment-api/services/data_status_drilldown.py`, `market-tick-data-service/engine/orchestrator.py`) are active
service source paths (not one-shot scripts). They need explicit sunset dates or named successor plans documenting when
the legacy-fallback branches can be removed.

### FINDING 6 (INFO): \_summary.md per-asset-group rollup has incorrect NULL count

**Severity: P3 — documentation discrepancy in previously committed audit results.**

`plans/audit/results/manifest_v8_compliance_2026_05_20_summary.md` shows 0 NULL rows for all asset groups in the rollup
table, but the underlying `_data.csv` clearly shows NULL schema_version rows for defi (1,286,260), tradfi (35,033),
sports (13,176), prediction (2,280). This report contains the corrected counts.

---

## Remediation required

### P0 — Data migration (must complete before layer-N+1 work resumes)

1. **Execute manifest v8 migration across all 10 buckets** (MTDS + IS, all 5 asset groups). The migration must:
   - Set `schema_version=8` on all rows
   - Backfill `capture_status="captured"` for rows where it is absent (NULL schema_version rows)
   - Backfill `pipeline_mode=""` for rows where it is absent
   - Backfill `available_at` for rows where it is absent
   - Bundle with Phase 2 GCS migration walk per single-walk discipline (SSOT:
     `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md`)
   - Pre-migration drain: all running VMs stopped + manifest consolidated before migration begins

2. **Also check and migrate**: `solana-defi-*` buckets + `evm-defi-*` buckets (not in this audit scope but same
   migration requirement applies).

3. **After migration**: verify via
   `gsutil cat gs://<bucket>/_index/availability_index.parquet | python3 -c "import pandas as pd, sys; df=pd.read_parquet(sys.stdin.buffer); print(df.schema_version.value_counts())"`
   for each bucket.

### P0 — Code fix

4. **Fix `deployment-service/scripts/rebuild_sports_manifest.py`**: Update to write `schema_version=8`,
   `capture_status="captured"`, `available_at=<timestamp>`, `pipeline_mode=""`. Do not run the script again until fixed.

### P1 — Execute migration script

5. **Run `migrate_solana_defi_v4_to_v8.py`** with `--apply --confirm` (after operator authorization and VM drain).
   Update `last_executed` in the runbook header.

### P1 — UAC manifest_schema.py fix

6. **Verify and fix `unified-api-contracts/unified_api_contracts/canonical/crosscutting/manifest_schema.py`**: The A4
   code scanner flagged a v<8 literal in this file. Read the file, confirm whether this is a write-path constant or a
   test/migration artifact, and update to v8 if it's a writer constant.

### P2 — Legacy-fallback sunset planning

7. **Add named successor plan or sunset date** to active-service legacy-fallback files (deployment-api
   data_status_service.py, data_status_drilldown.py, market-tick-data-service engine/orchestrator.py). The
   migration-script fallbacks (v7_to_v8.py, migrate_solana_defi_v4_to_v8.py) are acceptable as one-shot utilities and
   can be archived post-execution.

### P2 — QG ratchet

8. **Add new QG step**: `scripts/quality_gates/no_legacy_schema_version.sh` (STEP 5.84 referenced in the mega-audit plan
   — confirm if already shipped or still pending) that scans workspace Python source for any write-path `schema_version`
   literal <8. The A4 scan already identified this need.

### P3 — Fix \_summary.md rollup table

9. **Correct the NULL row count** in `plans/audit/results/manifest_v8_compliance_2026_05_20_summary.md` (the
   per-asset-group rollup table shows 0 NULL rows for defi/tradfi/sports/prediction but the underlying data shows
   1,336,749 NULL rows total). This report (`manifest_v8_compliance_2026_05_20.md`) contains the corrected counts and
   supersedes the \_summary.md rollup.

---

## Appendix — how to run the data-side check post-migration

```bash
# Run after migration to verify 100% v8:
python3 << 'PYEOF'
import subprocess, tempfile, os
import pandas as pd

buckets = {
    'mtds-cefi': 'gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet',
    'mtds-defi': 'gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet',
    'mtds-tradfi': 'gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet',
    'mtds-sports': 'gs://market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet',
    'mtds-prediction': 'gs://market-data-tick-pred-prd-central-element-323112/_index/availability_index.parquet',
    'is-cefi': 'gs://instruments-store-cefi-prd-central-element-323112/_index/availability_index.parquet',
    'is-defi': 'gs://instruments-store-defi-prd-central-element-323112/_index/availability_index.parquet',
    'is-tradfi': 'gs://instruments-store-tradfi-prd-central-element-323112/_index/availability_index.parquet',
    'is-sports': 'gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet',
    'is-prediction': 'gs://instruments-store-pred-prd-central-element-323112/_index/availability_index.parquet',
}
tmpdir = tempfile.mkdtemp()
for name, gcs_path in buckets.items():
    local = os.path.join(tmpdir, f'{name}.parquet')
    subprocess.run(['gsutil', 'cp', gcs_path, local], check=True)
    df = pd.read_parquet(local)
    v8 = (df['schema_version'] == 8).sum()
    total = len(df)
    status = 'PASS' if v8 == total else 'FAIL'
    print(f'{status} {name}: {v8}/{total} ({100*v8/total:.1f}%)')
PYEOF
```
