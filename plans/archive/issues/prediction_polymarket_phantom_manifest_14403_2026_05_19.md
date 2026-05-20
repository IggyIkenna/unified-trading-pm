---
title:
  "🚨 P0 MIGRATION REGRESSION: Phase 3 GCS migration converted real captures to phantoms for tradfi (245,907) and
  prediction (14,403) — systematic root cause under investigation; DO NOT run Phase 6 --apply"
created: 2026-05-19
author:
  ikenna-slot-3 (Phase 3.6 post-migration phantom audit; discovered 2026-05-19 ~16:14 UTC, severity upgraded ~16:35 UTC)
source:
  - "instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group prediction --dry-run (run
    2026-05-19 16:13 UTC)"
  - "instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run (run 2026-05-19
    16:32 UTC)"
  - "Gate 3 phantom audit (PM@bf47123f, 2026-05-17 14:32-14:42 UTC) — baseline showing all were real captures"
  - "gs://central-element-323112-phantom-triage/triage_prediction_20260519_151357.jsonl (14403 records)"
  - "gs://central-element-323112-phantom-triage/triage_tradfi_20260519_153300.jsonl (245907 records)"
  - "gcs_migration_bundle_pipeline_mode_2026_05_08.md Phase 3.6 phantom gate"
locked_by: live-defi-rollout
locked_since: 2026-05-19
severity:
  P0 — data integrity. Phase 3 migration converted 14,403 prediction + 245,907 tradfi real captures into phantoms. Gate
  3 (May 17) confirmed both were CLEAN before migration. Sports (559,961 real captures) survived migration intact. DeFi
  + CeFi audits still in progress. Root cause under investigation — GCS path probes running to determine if parquets
  were moved, lost, or have path-format mismatch. Phase 6 --apply is BLOCKED until root cause confirmed.
---

> **🟡 COVERED BY**
> [../gcs_migration_bundle_pipeline_mode_2026_05_08.md](../gcs_migration_bundle_pipeline_mode_2026_05_08.md) +
> [../gate_3_phantom_audit_runbook_2026_05_13.md](../gate_3_phantom_audit_runbook_2026_05_13.md) — P0 migration
> regression owned by Phase 3.6 of the migration plan + the phantom-audit runbook (slot-1 triage 2026-05-20). Phase 6
> `--apply` BLOCKED until root cause confirmed. Mega-audit Phase A3 divergence report will also surface this class.
> Archive when parent plans close.

## What I found

Post-migration Phase 3.6 audit (`reconcile_phantom_manifest_rows_all.py --asset-group prediction --dry-run`) returned
14,403 phantom rows in `gs://market-data-tick-prediction-central-element-323112/_index/availability_index.parquet`:

```
2026-05-19 16:13:56,423 INFO Audit summary (forward — captured rows missing parquet):
2026-05-19 16:13:56,423 INFO   Real captures:    0
2026-05-19 16:13:56,424 INFO   Phantom captures: 14403  ← will flip to attempted_failed

data_type
trades               11943
prediction_trades     2460

venue
POLYMARKET    14235
               168    (blank venue)
```

All 14,403 rows have `capture_status=captured` in the manifest but **no corresponding parquets exist** at any probed GCS
path. `Real captures: 0` means not a single POLYMARKET parquet has ever been written to this bucket.

Triage JSONL: `gs://central-element-323112-phantom-triage/triage_prediction_20260519_151357.jsonl` (14,403 records). Run
was DRY-RUN only — manifest NOT modified.

This finding was discovered immediately after all 31 Phase 3 migration VMs completed (prediction-2025 TERMINATED 14:39
UTC + prediction-2026 TERMINATED ~16:01 UTC, both exit status 0).

## SEVERITY UPGRADE — 2026-05-19 ~16:35 UTC (CORRECTION)

**Original diagnosis was WRONG. Gate 3 phantom audit evidence corrects this.**

Gate 3 runbook (`gate_3_phantom_audit_runbook_2026_05_13.md`, run 2026-05-17 14:32-14:42 UTC, PM@bf47123f) showed
`prediction` asset_group had **14,403 REAL captures and 0 phantoms** as of May 17 — two days before Phase 3 migration:

| Asset Group | Real Captures | Phantom Captures |
| ----------- | ------------- | ---------------- |
| prediction  | 14,403        | **0**            |

The Phase 3 migration (2026-05-19 13:52 → 16:01 UTC) converted all 14,403 real captures into phantoms. This is **a
migration regression, not a pre-existing condition.**

**HOLD: Do NOT run Phase 6 `--apply` until root cause is confirmed. Running --apply would destroy the manifest evidence
needed to diagnose whether the parquets were moved, lost, or paths corrupted.**

Root cause investigation in progress (2026-05-19 ~16:35 UTC):

1. GCS listing: probing `gs://market-data-tick-prediction-central-element-323112/` for POLYMARKET-keyed paths (are the
   parquets still on disk at old or new paths?)
2. Manifest path audit: downloading post-migration manifest to inspect what paths the 14,403 rows now record (old-format
   vs new pipeline_mode= format)

If parquets exist on GCS but manifest paths are wrong → fixable manifest path correction (no data loss). If parquets
don't exist on GCS at any path → data loss event → operator must decide recovery path.

## Why it matters

**Diagnosis — MIGRATION-INDUCED (corrected from original "pre-existing").** Gate 3 (May 17) confirmed 14,403 POLYMARKET
prediction captures were real (parquets existed). Phase 3 migration (May 19) converted all to phantoms. This means the
migration either:

- (a) Moved POLYMARKET parquets to new `pipeline_mode=` paths AND updated the manifest to new paths, but there's a
  path-format mismatch between what the reconciler probes and where the files actually landed, OR
- (b) Updated the manifest to new `pipeline_mode=` paths but FAILED to move the parquets (files still at old paths), OR
- (c) Some combination of partial state from prediction-2026 VM processing

Evidence state (as of 16:35 UTC — investigation running):

- `Real captures: 0` in Phase 3.6 audit — no parquets found at manifest-recorded paths
- Gate 3 showed these were all real 2 days ago
- GCS listing and manifest path inspection tasks running in background

**🚨 SYSTEMATIC MIGRATION REGRESSION — tradfi is also affected:**

Phase 3.6 tradfi audit (completed 2026-05-19 16:32 UTC) found 245,907 phantoms:

```
Real captures:    0
Phantom captures: 245907

data_type:  ohlcv_1m=241201  ohlcv_24h=2808  ohlcv_15m=1607  options_chain=291
venue:      NYSE=122494  CME=83089  NASDAQ=33672  FX=2808  ICE=2237  CBOE=1607
```

Gate 3 (May 17) showed tradfi had exactly **245,907 real captures and 0 phantoms** — the Phase 3 migration converted all
of them to phantoms. Same pattern as prediction.

Sports audit confirmed **0 phantoms** — sports survived the migration intact with all 559,961 real captures preserved.

**Gate impact:**

- Phase 3.6 phantom gate requires 0 phantoms across all 5 asset_groups. Both prediction AND tradfi are failing.
- Defi and cefi audits still running (task IDs: defi=bt2z59y9n, cefi=b60wk5m8q) — may be similarly affected.
- Phase 6 `--apply` is **BLOCKED** — do NOT run until root cause is confirmed. Running --apply would flip real-but-
  mispathed captures to `attempted_failed`, destroying the manifest's ability to self-heal once paths are corrected.
- May-23 gate at risk: tradfi data is on the critical path for multiple archetypes.

**ROOT CAUSE CONFIRMED (2026-05-19 ~17:00 UTC):**

GCS probe verified: tradfi parquets exist at
`raw_tick_data/by_date/day=*/pipeline_mode=batch_databento/asset_group=tradfi/venue=*/` paths. Example:
`day=2024-01-15/pipeline_mode=batch_databento/asset_group=tradfi/venue=CME/data_type=options_chain/6AG4_migrated_20260419T131639Z.parquet`.
**No data loss.** The migration moved files correctly.

Root cause: the reconciler's `ASSET_GROUP_CONFIG["tradfi"]["prefix_tpls"]` (and same for cefi/defi/prediction) only
probe pre-migration path shapes (without `pipeline_mode=`). The post-migration canonical path adds
`pipeline_mode=batch_databento/` BEFORE `asset_group=`. Since the reconciler never probes that new shape, it reports all
migrated files as phantoms.

**Fix shipped (instruments-service):** Added `pipeline_mode=batch_databento/` (and other relevant batch sources) to
`prefix_tpls` for all 4 affected asset groups in `reconcile_phantom_manifest_rows_all.py`. Sports unaffected because it
uses the UAC `candidate_parquet_paths()` dispatcher which has different path logic.

**Re-run the Phase 3.6 audit after the fix ships** — all 4 asset groups should return 0 phantoms.

**NOT a migration correctness bug** on data integrity IF the parquets still exist at new paths. They do — confirmed.

## Recommended decision (updated post root-cause investigation)

**Root cause: reconciler bug (Axis-10 missing), NOT a manifest or data problem.**

The 14,403 prediction "phantoms" and 245,907 tradfi "phantoms" are FALSE POSITIVES from the pre-fix reconciler. The
actual parquets exist at the new `pipeline_mode=batch_databento/` (tradfi) and `pipeline_mode=batch_polymarket_*/`
(prediction) paths — the reconciler's static templates didn't know to probe there.

**Required action:**

1. ✅ **SHIPPED (2026-05-19)**: `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` — Axis-10 fix adds
   `pipeline_mode=batch_*/` template variants to all 4 affected asset groups (cefi/defi/tradfi/prediction).

2. **Re-run Phase 3.6 audit** with the fixed reconciler (after QG passes + code ships):

   ```bash
   cd instruments-service && python scripts/reconcile_phantom_manifest_rows_all.py \
     --asset-group tradfi --dry-run
   cd instruments-service && python scripts/reconcile_phantom_manifest_rows_all.py \
     --asset-group prediction --dry-run
   # repeat for cefi, defi
   ```

   Expected result: 0 phantoms across all 5 asset_groups → Phase 3.6 gate passes.

3. **DO NOT run Phase 6 `--apply`** on these phantom rows — they are FALSE POSITIVES. The parquets exist at the new
   paths. Phase 6 --apply would flip real captured rows to `attempted_failed` (data regression).

4. Once re-audit confirms 0 phantoms → operator can proceed with Phase 3 step 7 sign-off per asset_group.

**Blocking gate status (UPDATED 2026-05-19 18:55 UTC — ALL 5 CONFIRMED):**

- Phase 3.6 all asset_groups: ✅ COMPLETE — 0 phantoms across all 5 asset_groups
  - prediction: 0/14,403 real ✅ (re-audit 2026-05-19)
  - sports: 0/559,961 real ✅ (re-audit 2026-05-19)
  - tradfi: 0/245,907 real ✅ (re-audit 2026-05-19)
  - defi: 0/311,602 real ✅ (re-audit 2026-05-19 18:42 UTC)
  - cefi: 0/1,290,707 real ✅ (re-audit 2026-05-19 18:55 UTC; 224,994 GCS prefixes)
- Phase 6 --apply: 🚫 NOT NEEDED (phantoms were false positives; all parquets confirmed at new paths)
- Operator sign-off: ⏳ AWAITING HUMAN ACTION — step 7 per-asset-group checkboxes in gcs_migration plan § Phase 3

**Code location**: `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` § `ASSET_GROUP_CONFIG` —
`prefix_tpls` for cefi/defi/tradfi/prediction.

## Escalation

Filed as operator ping in `ikenna_orchestrator/pings/slot_3.md` — section "Phase 3.6 OPERATOR ESCALATION — prediction
Polymarket phantoms 2026-05-19".

Related:

- `plans/active/issues/kalshi_polymarket_classify_venue_error_missing_2026_05_18.md` — Polymarket error classification
  gap
- `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 3 step 6 + Phase 6
- `plans/active/issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`
