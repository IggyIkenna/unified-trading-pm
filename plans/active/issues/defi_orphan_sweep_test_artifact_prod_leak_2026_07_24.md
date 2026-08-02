---
doc_type: issue
title:
  Orphan-E backfill never checked the sweep's own "unknown prefix" taxonomy — 8 defi test-artifact objects would have
  been canonised, and cefi's ALREADY-LANDED backfill double-counted 4 cells via KRAKEN-FUTURES remediation backups
summary: >-
  While triaging defi's terminal orphan-sweep report (orphan_class_E=15,865,384, unknown_prefixes=8) before running
  backfill_orphan_class_e.py --apply, found the sweep's own bucket-prefix-taxonomy pass flagged exactly 8 objects under
  an unrecognised top-level prefix agent-sample-test-jupiter/ (all 8 also classified E_orphan_real) — full
  JUPITER/SOLANA/dex_pool/dex_quote paths dated day=2026-07-22, an agent's own ad-hoc smoke-test write that leaked into
  the PROD market-data-tick-defi-prd-central-element-323112 bucket instead of a -test- bucket. Cross-validated against
  the sweep's own class-count arithmetic (A+B+D+E == service-data taxonomy count + 8, exact match) — this is the
  COMPLETE population, not a sample estimate: exactly 8 of 15,865,384 class-E rows (0.00005%), and no other unrecognised
  top-level prefix exists anywhere in the 24.89M-object walk. migration_orphan_sweep.py's classify_object() does not
  check the sweep's own "unknown prefix" taxonomy signal before classifying an object E_orphan_real, so
  backfill_orphan_class_e.py --apply would otherwise have record_captured these 8 rows as genuine production data. Fixed
  with a general safety net (instruments-service@9a491b23): a new split_unknown_prefix_rows() excludes any class-E row
  whose top-level bucket prefix the sweep's own taxonomy could not attribute to real service data, before backfill plans
  are built — covers this exact leak and any future recurrence of the same class, not just this one literal prefix
  string. The 8 objects themselves are a SEPARATE, human-gated prod-bucket delete candidate (not deleted by this doc).
  Checking whether the same defect class hit the three OTHER asset_groups' already-completed sweeps found cefi's
  `unknown_prefixes=170` is a DIFFERENT, real instance of the identical root cause: 98 of those 170 objects are stale
  server-side backups under `_remediation_backups/kraken_futures_collision_2026_07_08/` (pre-fix copies made before an
  in-place column-level fix — see the archived `canonical_id_p0_kraken_futures_collision_2026_07_08.md`), and cefi's
  backfill ALREADY landed `--apply` (2026-07-22, before this fix existed) — measured 4 manifest cells with `row_count`
  inflated ~180-199% (29,735,610 rows over-counted) by summing the backup copies alongside their canonical twins into
  one cell. Metadata-only (real objects untouched, honest-coverage stats affected), not blocking, filed as a follow-up
  todo.
status: resolved
nature: issue
asset_group: [defi, cefi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    defi,
    cefi,
    orphan-sweep,
    test-artifact,
    prod-bucket-leak,
    data-correctness,
    manifest-completeness,
    backfill-safety,
    row-count-inflation,
  ]
related:
  [
    /plans/active/issues/estate_orphan_assessment_2026_07_21.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/canonical_id_p0_kraken_futures_collision_2026_07_08.md,
    /codex/02-data/orphan-object-detection.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-07-24
last_updated: 2026-08-02
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: instruments-service@016c5ab2
source:
  found while triaging estate_orphan_assessment_2026_07_21.md todo 3's defi backfill (operator flagged the risk from a
  25-row log sample; this doc measures the true, full-population scope)
depends_on: []
context_scope:
  [
    instruments-service/scripts/backfill_orphan_class_e.py,
    instruments-service/scripts/migration_orphan_sweep.py,
    /plans/archive/2026_07/canonical_id_p0_kraken_futures_collision_2026_07_08.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

# defi orphan-sweep test-artifact prod-bucket leak (2026-07-24)

## What I found

Defi's terminal orphan-sweep (`orphan-sweep-defi-20260723-043605`, 6th attempt, completed 2026-07-23 21:04:37 UTC after
a 16h25m full clean walk of 24,890,959 objects) printed:

```
=== ACCEPTANCE: orphan_class_E=15865384 (target 0), unknown_prefixes=8 (target 0) ===
```

The run.log's own bucket-prefix-taxonomy section (which counts EVERY object in the bucket, not a sample) shows the
**entire** `unknown_prefixes=8` is one single label:

```
unknown:agent-sample-test-jupiter/ 8
```

And the "first 25 orphan-E objects" warning block printed exactly those same 8 URIs, all shaped:

```
gs://market-data-tick-defi-prd-central-element-323112/agent-sample-test-jupiter/raw_tick_data/by_date/
  day=2026-07-22/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=JUPITER/chain=SOLANA/
  instrument_type=dex_pool/data_type=dex_quote/{SOL_to_USDC_0,SOL_to_USDC_6,SOL_to_USDC_62,SOL_to_USDC_625,
  USDC_to_SOL_100,USDC_to_SOL_1000,USDC_to_SOL_10000,USDC_to_SOL_100000}.parquet
```

This reads as an agent's own ad-hoc smoke-test of the Jupiter DEX adapter (quote-size sweep pattern: 0, 6, 62, 625 SOL
and 100, 1000, 10000, 100000 USDC — a geometric probe, not real trading activity) that wrote directly to the **PROD**
bucket under a throwaway top-level prefix instead of a `-test-` bucket. `grep -rl "agent-sample-test"` across every repo
in the workspace (`.py`/`.sh`/`.md`) returns zero hits — the writer script is not currently in the repo (either a
one-off interactive snippet, or since deleted), so there is no live code path to fix at the writer side; this doc exists
to (a) quantify the leak precisely, (b) make sure the backfill never canonises it, and (c) flag the prod-bucket delete
candidate.

## Measured scope — the COMPLETE population, not a sample

The operator's own spot-check (25-row log sample) found 9/25 lines matching `agent-sample-test-jupiter` and flagged it
as a possible "meaningful fraction" risk worth verifying before any backfill. The full-population count from the sweep's
own taxonomy pass settles this precisely:

- **8 objects total**, all under `agent-sample-test-jupiter/`, all classified `E_orphan_real` (valid hive-shaped path,
  real rows, no manifest coverage — the sweep's classifier does not require the top-level prefix to be a recognised
  service-data prefix before returning E).
- **8 / 15,865,384 = 0.00005%** of defi's total class-E population. Not a meaningful fraction — negligible in scale, but
  real, and correctly flagged as a distinct defect class (a backfill would have silently canonised fabricated test data
  as genuine production capture, corrupting the manifest with the exact harm this whole effort exists to prevent).
- **Zero other unrecognised top-level prefixes exist anywhere in the bucket.** Cross-validated by arithmetic on the
  sweep's own printed class counts:
  `A_canonical_manifested(7,675,460) + B_legacy_duplicate(1,080) + D_junk(136,635) + E_orphan_real(15,865,384) = 23,678,559`,
  and the taxonomy's `service-data` label count is `23,678,551` — the difference is exactly `8`, i.e. every
  class-A/B/D/E object outside the 8 `agent-sample-test-jupiter/` objects sits under a recognised
  `raw_tick_data/`/`day=` service-data prefix. A full grep of the run.log for `test|sample|sandbox|mock|debug|scratch`
  (case-insensitive) returns matches ONLY for this one prefix. This is measured against the sweep's full 24.89M-object
  walk, not inferred from the 25-row sample.

## Why this needed a code fix, not just a manual filter

`instruments-service/scripts/migration_orphan_sweep.py`'s `classify_object()` only checks the infra/non-data label list
(`_prefix_label()`) before parsing hive segments — it never checks whether the object's TOP-LEVEL path prefix is one of
the two recognised service-data prefixes (`raw_tick_data/`, `day=`) before returning `E_orphan_real`. The sweep's OWN
separate bucket-taxonomy pass (`_taxonomy_label()`, the "0 unknown is the acceptance bar" check) DOES compute this
signal — it just was never consulted by the backfill tool. `backfill_orphan_class_e.py --apply` would therefore have
`record_captured`'d these 8 rows as genuine defi captures, exactly the corruption this whole closeout effort exists to
prevent.

## Fix shipped

`instruments-service@9a491b23` (`scripts/backfill_orphan_class_e.py`): new `split_unknown_prefix_rows(bucket, rows)`
excludes any class-E row whose `_sweep._taxonomy_label(object_path)` starts with `"unknown:"` — i.e. any row the sweep
itself could not attribute to a recognised service-data prefix — before `build_plans()` runs, mirroring the existing
`split_dex_pools_fake_history()` exclude-before-plan pattern. Wired into `main()` right after the fake-history split,
with the same logged-and-counted shape (`N unknown-top-level-prefix EXCLUDED`, first 10 URIs printed at WARNING). This
is a GENERAL safety net (keyed on the sweep's own taxonomy signal, not a hardcoded `agent-sample-test-jupiter` string) —
it will also catch any future similar leak under a different throwaway prefix without needing a code change. Regression
test `TestSplitUnknownPrefixRows` added (`tests/scripts/test_backfill_orphan_class_e.py`), full `quality-gates.sh`
green, shipped via quickmerge.

## Todos

- [x] 1. [CODE] P2. **Add the unknown-top-level-prefix exclusion to `backfill_orphan_class_e.py`** — DONE, see "Fix
      shipped" above. `instruments-service@9a491b23`.
- [x] ✅ 2. [SCRIPT] P3. **DONE 2026-07-29 — deleted.** **Prod-bucket delete of the 8 `agent-sample-test-jupiter/`
      objects** — confirmed test artifacts, not production data, sitting in
      `gs://market-data-tick-defi-prd-central-element-323112/agent-sample-test-jupiter/` (exact 8 object paths listed in
      this doc's "What I found" section). Reversibility-verified per finding T (604800s GCS Soft Delete retention
      confirmed live on `market-data-tick-defi-prd-central-element-323112`), a prefix-scoped delete of an exact, named
      8-object list, not a whole-bucket destroy. Live-listed the prefix first (confirmed exactly 8 objects, matching
      this doc's list byte-for-byte), deleted each via UTL `gcs_delete_object` (never subprocess gcloud/gsutil), then
      re-listed the same prefix: **0 objects remaining.**
- [x] 3. [DATA] P3. **Spot-check whether the same leak class exists in cefi/tradfi/prediction's completed orphan
      sweeps** — DONE. tradfi (`orphan_sweep_tradfi`) and prediction (`orphan_sweep_prediction`) both show
      `unknown_prefixes=0` — clean. **cefi shows `unknown_prefixes=170`, ALL under `unknown:_remediation_backups/`** —
      NOT test contamination (a different, real finding — see todo 4).

- [x] ✅ 4. [DATA] P2. **cefi's ALREADY-COMPLETED backfill (`backfill-orphan-e-cefi-20260722-213220`, apply landed
      2026-07-22 23:12 UTC, BEFORE the `split_unknown_prefix_rows` fix existed) double-counted 4 manifest cells'
      `row_count` by summing the KRAKEN-FUTURES collision-remediation server-side BACKUP copies alongside their
      canonical twins.** Root cause: `_remediation_backups/kraken_futures_collision_2026_07_08/` (see
      `plans/archive/2026_07/canonical_id_p0_kraken_futures_collision_2026_07_08.md`) holds pre-fix, byte-identical
      copies of 125 real KRAKEN-FUTURES parquet files, backed up server-side before an in-place column-level fix
      overwrote the live objects at their normal canonical path. Both the backup copy and its canonical twin parse to
      the IDENTICAL shard-key (venue/instrument_type/data_type/day — `underlying` is blank for both, since
      KRAKEN-FUTURES pre-hive filenames carry no `underlying=` hive segment) — and for 3 of the 5 collision days that
      plan's own progress log already flagged a PRE-EXISTING, unrelated manifest-recording gap ("these captures bypassed
      record_shard_count/record_instrument bookkeeping entirely"), so BOTH the canonical object and its backup twin read
      as uncovered class-E and both got swept into the same `record_captured` cell (
      `backfill_orphan_class_e.py::record_cells()` sums `row_count` across every result sharing a cell key, by design —
      the correct behavior for cefi's normal many-objects-per-cell coarse grain, just never guarded against a stale
      BACKUP object sharing that same cell). **Measured** (downloaded + read `orphan_backfill_cefi.parquet`, 33.2 MiB,
      935,714 rows): exactly 4 cells affected — `(2024-02-01, book_snapshot_5)`: canonical=2,199,192 rows,
      backup=3,888,915 rows recorded on top (177% over); `(2024-02-01, trades)`: canonical=1,490, backup=+2,728 (183%
      over); `(2025-01-10, book_snapshot_5)`: canonical=14,141,726, backup=+25,805,763 (182% over);
      `(2025-01-10, trades)`: canonical=19,206, backup=+38,204 (199% over). **Total 29,735,610 rows over-counted**
      across these 4 cells' `record_captured` `row_count` field. **Severity calibration**: this is a MANIFEST METADATA
      defect (the `row_count` field used for honest-coverage/monitoring stats), not a
      data-loss/corruption-of-real-content defect — the real parquet objects at both paths are untouched and readable;
      only the aggregate row-count number attached to 4 manifest cells is inflated. Not blocking, but should be
      corrected: re-derive the TRUE canonical-only row_count for these 4 cells (footer-sum the
      non-`_remediation_backups/` objects only) and issue a corrective `record_captured` (or a targeted manifest row
      patch) so cefi's honest-coverage numbers for 2024-02-01/2025-01-10 KRAKEN-FUTURES book_snapshot_5/trades are
      accurate. `split_unknown_prefix_rows` (this doc's fix, `instruments-service@9a491b23`) prevents this exact class
      from recurring on any FUTURE backfill run (defi/tradfi/prediction all still pending, and any cefi re-run) — it is
      retroactive protection only, it does not correct the 4 cells already recorded before it shipped. — **DONE
      2026-08-02**, `instruments-service@016c5ab2`. **Live-manifest re-verification found the state had already moved on
      from what this todo describes**: the LIVE `_index/availability_index.parquet` currently carries ZERO rows from
      `service_name="instruments-service"` for `venue=KRAKEN-FUTURES` on either affected date, at ANY `capture_status` —
      the inflated `captured` row is not the row present today (its per-VM shard, which would have lived at
      `_index/per_vm/orphan-backfill-cefi*.parquet`, no longer exists — already merged-and-dropped or never durably
      flushed; the only physical rows at this key are 72 unrelated pre-existing `attempted_failed`/count=0
      `market-tick-data-service` rows from a separate, older per-underlying bookkeeping gap, a different `service_name`
      so the consolidator's dedup never partitions them against an instruments-service row anyway). Net effect is the
      same either way: shipped `scripts/correct_cefi_kraken_futures_rowcount_2026_08_02.py`, which re-derives the TRUE
      canonical-only row_count FRESH from GCS on every run (bounded per-cell prefix listing — never trusts the stale
      `orphan_backfill_cefi.parquet` report; footer-sums every canonical, non-backup object) and records the corrected
      `captured` cell via the normal `ManifestWriter.record_captured` path (mirrors `record_cells()`'s cefi RECORD_ONLY
      shape, minus the backup-inclusion bug). Fresh footer-sums exactly matched this doc's independently-measured
      canonical figures: `(2024-02-01, book_snapshot_5)`=2,199,192 (14 objects), `(2024-02-01, trades)`=1,490 (10
      objects), `(2025-01-10, book_snapshot_5)`=14,141,726 (20 objects), `(2025-01-10, trades)`=19,206 (17 objects).
      Applied live (`VM_NAME=cefi-kraken-futures-rowcount-fix`), verified the resulting per-VM shard
      (`_index/per_vm/cefi-kraken-futures-rowcount-fix.parquet`) carries all 4 corrected `captured` rows with the true
      `instrument_count`. 4 unit tests added (`tests/scripts/test_correct_cefi_kraken_futures_rowcount_2026_08_02.py`),
      full `quality-gates.sh` green, shipped via quickmerge.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (4 entries).
