---
doc_type: audit-result
title: "P8 candle-canonicalisation post-migration verification — tradfi (2026-07-23)"
summary: >-
  Independent verification (P8) of the TRADFI processed_candles/ canonical-path migration
  (market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py), run AFTER the migration's own P7d
  apply+retry reported 0 non-success outcomes. A FRESH sharded enumeration of processed_candles/by_date/ (884
  day-prefixes, 24-way parallel listing) found 534,679 live objects — far fewer than the pre-migration P0 census total
  of 7,646,831, which is EXPECTED (not a discrepancy): the census's dominant class, NEEDS_CONTENT_TRADFI_ID (6,487,045 /
  84.8%), resolved during the actual apply run mostly via CONTENT_REPAIR_UNRESOLVED_QUARANTINED (moved OUT of
  processed_candles/by_date/ to _quarantine/, per the issue doc's own 2026-07-23 progress log), plus
  SPLIT_BRAIN_DUPLICATE dedup and empty-stem bundle consolidation, all of which reduce object COUNT without leaving
  anything non-canonical behind. Running the migration script's own --dry-run classifier against this fresh enumeration
  (the tool's inverse ground-truth check) over the full 534,679 objects returned a disposition histogram of 100%
  CANONICAL_NOOP, 0 ORPHAN, and 0 in every other class (MIGRATE / SPLIT_BRAIN_DUPLICATE / any NEEDS_CONTENT_* /
  QUARANTINE_CORRUPT / EMPTY_STEM_*). No batch_massive pipeline_mode objects exist in the namespace (0 found) —
  consistent with the documented Massive purge, not a finding. VERDICT: CLEAN.
status: pass
nature: record
asset_group: [tradfi]
stage: [data]
repos: [market-data-processing-service, unified-trading-pm]
scope: [engineer, admin]
tags: [reconciliation, canonicalisation, candles, tradfi, migration-verification, p8, processed_candles]
related: [candle_feature_canonical_path_divergence_2026_07_20]
created: 2026-07-23
auditor:
  "P8 independent post-migration verification (fresh sharded GCS enumeration + migrate_candle_canonical_2026_07.py
  --dry-run classify)"
parent_epic: infrastructure_master
severity: P1
audited_scope:
  "asset_group=tradfi, processed_candles/by_date/ ONLY (raw_tick_data/ and the rest of the bucket are OUT OF SCOPE),
  PROD bucket (market-data-tick-tradfi-prd-central-element-323112), read-only throughout, ONE sanctioned bounded walk of
  this prefix (not a whole-corpus walk)"
date: 2026-07-23
resulting_plan:
lib_version:
doc_versions_checked:
---

# P8 candle-canonicalisation post-migration verification — `asset_group=tradfi` (PROD, read-only)

## What this is

This is the 4th (and largest) of 4 parallel P8 post-migration verifications for the candle canonical-path migration
described in `plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md` — the migration that added
`instrument_type=` to `processed_candles/` object paths, fixed empty-stem/split-brain/TradFi-artifact-id defects, and
purged/quarantined the old shapes. TRADFI was migrated LAST (largest corpus, ~99% id-canonicalisation load) and its P7d
apply+retry pass was reported DONE 2026-07-23 with "0 outstanding legacy-path objects" after a retry converged all 229
transient stragglers from run 1. This P8 check does **not** trust that self-report — it re-derives ground truth from a
brand-new enumeration of the live bucket and runs the migration tool's own classifier (its inverse operation) against
it.

## Bucket resolved

```python
from unified_trading_library import resolve_bucket_name
bucket = resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="tradfi", deployment_env="prd")
# -> market-data-tick-tradfi-prd-central-element-323112
```

Confirmed reachable via a non-recursive top-level `list_blobs(..., delimiter="/")` probe before the real enumeration.

## Fresh enumeration (sharded, `processed_candles/by_date/` only)

Given TRADFI's scale (~7.6M objects pre-migration), the enumeration was sharded to avoid a single serial listing call:

1. Cheap delimiter-descent of `processed_candles/by_date/` (prefix-only, not objects) found **884** `day=YYYY-MM-DD/`
   child prefixes (`2020-01-01` → `2026-07-22`).
2. A `ThreadPoolExecutor(max_workers=24)` listed objects under each day-prefix in parallel
   (`google.cloud.storage.Client.list_blobs(bucket, prefix="processed_candles/by_date/day=<D>/")`, paginated), streaming
   each shard to its own resumable per-day file, then concatenated into one enumeration file.
3. **Result: 534,679 objects enumerated** across all 884 days, 0 malformed lines (every line is a valid `gs://` URI),
   covering exactly the 884 expected day-prefixes. Wall-clock: enumeration ran ~1,009s (~17 min); confirmed complete
   only by the process's own `NOT_RUNNING` exit + a terminal `FINAL ENUMERATION WRITTEN` log line (not a guess).

Enumeration file: `p8_tradfi_enumeration.txt` (534,679 lines, scratchpad-local, not committed).

### Why 534,679 and not ~7.6M — expected, not a discrepancy

The P0 pre-migration census (issue doc, measured 2026-07-22) found TRADFI's `processed_candles/` corpus at **7,646,831**
objects, disposition-classified as:

| MIGRATE | SPLIT_BRAIN_DUPLICATE | QUARANTINE_CORRUPT | EMPTY_STEM (w/ underlying) | EMPTY_STEM (w/o) | NEEDS_CONTENT_TRADFI_ID | CANONICAL_NOOP | ORPHAN |
| ------: | --------------------: | -----------------: | -------------------------: | ---------------: | ----------------------: | -------------: | -----: |
|       0 |               724,214 |                  0 |                    428,792 |            6,780 |               6,487,045 |              0 |      0 |

The dominant class — `NEEDS_CONTENT_TRADFI_ID` at 6,487,045 (84.8% of the corpus) — required a real parquet content
read + `_renormalize_legacy_instrument_ids` to resolve a migration-artifact id
(`E1AF0_C3200_migrated_20260418T131054Z.parquet`-style) to a real canonical instrument id. The issue doc's own
2026-07-23 progress log, taken from the live `run.log` of the actual P7d apply shards, states the observed disposition
mix was **"as expected for TRADFI's content-repair-heavy profile (`CONTENT_REPAIR_UNRESOLVED_QUARANTINED` dominant,
consistent with the P0 census's 84.8% `NEEDS_CONTENT_TRADFI_ID` figure)"** — i.e. most of that class did NOT resolve to
a real id and was QUARANTINED (moved to a top-level `_quarantine/` prefix, disjoint from `processed_candles/by_date/`,
never deleted) rather than migrated in place. Additionally, `SPLIT_BRAIN_DUPLICATE` dedup collapses duplicate pairs to
one canonical copy, and empty-stem "with underlying" objects consolidate into a single bundled `ticks.parquet` per shard
(many-to-one). All three mechanisms reduce the LIVE object count under `processed_candles/by_date/` without leaving
anything non-canonical there — which is exactly what this P8 check is verifying. (Quantifying the `_quarantine/` count
precisely was NOT attempted here — it is a separate prefix, out of this check's scope, and a fresh full walk of it would
be a second whole-corpus GCS walk not authorized under this task.)

## Dry-run classify (the tool's own inverse ground-truth check)

```bash
cd market-data-processing-service
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u scripts/migrate_candle_canonical_2026_07.py \
  --dry-run \
  --enumeration p8_tradfi_enumeration.txt \
  --out p8_tradfi_mapping.tsv
```

Read-only throughout — `--dry-run` (never `--apply`), no `--quarantine`/`--content-repair` gates passed (irrelevant to
dry-run; those only matter under `--apply`). Ran to real process exit (confirmed via `ps` liveness check + the script's
own terminal `DRY-RUN complete —` log line), not a guessed/estimated completion. Runtime: seconds (classify-only pass
over already-fetched enumeration; the tool's separate manifest-sibling/target-index passes scan the full 534,679-line
enumeration unsharded, per its own documented design).

### Full disposition histogram (measured, `p8_tradfi_mapping.tsv.reconcile.txt`)

```
TOTAL objects classified: 534,679

=== disposition histogram ===
     534,679  CANONICAL_NOOP

MIGRATE (incl. split-brain): 0  |  CONTENT_REPAIR pending: 0  |  QUARANTINE: 0  |  CANONICAL_NOOP: 534,679
SUM(dispositions) = 534,679  |  TOTAL = 534,679  |  match=True
ORPHAN count = 0  (PASS — total map)
```

Every one of the 8 non-canonical disposition classes (`MIGRATE`, `SPLIT_BRAIN_DUPLICATE`,
`NEEDS_CONTENT_INSTRUMENT_TYPE`, `NEEDS_CONTENT_TRADFI_ID`, `NEEDS_CONTENT_CEFI_WIRE_ID`, `EMPTY_STEM_WITH_UNDERLYING`,
`EMPTY_STEM_WITHOUT_UNDERLYING`, `QUARANTINE_CORRUPT`) is **exactly 0**. The tool's own hard safety invariant — every
enumerated object gets exactly one disposition, sum(dispositions) == total, or the run aborts loudly — held
(`match=True`). `ORPHAN = 0` (the "MUST BE ZERO" line): the disposition map is total over the live corpus.

### Supplementary checks (from the enumeration + mapping TSV, no extra GCS walk)

- **`batch_massive` pipeline_mode**: **0 objects** anywhere in the 534,679-line enumeration
  (`grep -c "pipeline_mode=batch_massive"` → 0). Consistent with the documented, deliberate Massive-purge exception
  (Massive removed as a tradfi source 2026-07-19) — this is a non-finding, matching the task's explicit expectation, not
  something to flag.
- **Distinct `pipeline_mode` values present**: `batch_databento`, `batch_yahoo` only — matches the codex
  (`tradfi-databento-sourcing-ssot.md`: Databento = batch source of truth, Yahoo = daily).
- **Distinct `instrument_type` values present**: `COMBO`, `EQUITY`, `ETF`, `FUTURE`, `INDEX`, `OPTION`, `SPOT_PAIR`,
  `UD` — all recognised TRADFI instrument-type tokens, no stray/garbage values.
- **Mapping TSV disposition column**: `cut -f2 p8_tradfi_mapping.tsv | sort -u` → exactly one value, `CANONICAL_NOOP`,
  across all 534,679 rows.

## Verdict: **CLEAN**

Zero non-canonical TRADFI candle objects remain under `processed_candles/by_date/` as of this fresh enumeration
(2026-07-23). The migration's own dry-run classifier — run independently against a brand-new listing of the live bucket,
not against any cached/prior enumeration — returns 100% `CANONICAL_NOOP` with 0 `ORPHAN` and 0 in every
migrate/repair/quarantine class. This matches the expected TRADFI outcome stated in the task (essentially 100%
`CANONICAL_NOOP`, 0 `MIGRATE`/`SPLIT_BRAIN_DUPLICATE`/`NEEDS_CONTENT_*`/ `QUARANTINE_CORRUPT`/`ORPHAN`) and corroborates
the P7d progress log's "0 outstanding legacy-path objects" claim with an independent, fresh, tool-classified
re-enumeration rather than trusting the migration's own self-report.

No new non-canonical location was found, so there is no register-patch stanza to propose for
`/codex/02-data/non-canonical-path-inventory.md`.

## Reproducibility

```bash
# 1. Resolve bucket (market-data-processing-service/.venv)
cd market-data-processing-service
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -c "
from unified_trading_library import resolve_bucket_name
print(resolve_bucket_name(cloud='gcp', kind='market-data', asset_group='tradfi', deployment_env='prd'))"

# 2. Delimiter-descent day-prefix listing (google.cloud.storage list_blobs, delimiter='/')
#    -> 884 day=YYYY-MM-DD/ prefixes under processed_candles/by_date/

# 3. Sharded parallel enumeration (ThreadPoolExecutor(24), one list_blobs(prefix=day_prefix) per day)
#    -> 534,679 gs:// URIs, one enumeration file

# 4. Dry-run classify
GCP_PROJECT_ID=central-element-323112 .venv/bin/python -u scripts/migrate_candle_canonical_2026_07.py \
  --dry-run \
  --enumeration <enumeration file> \
  --out <mapping.tsv>
# -> <mapping.tsv>.reconcile.txt has the disposition histogram above
```

No `--apply` was ever passed. No deletes, no writes, no mutation of GCS state at any point in this check.
