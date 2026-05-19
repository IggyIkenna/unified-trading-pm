---
title:
  "prediction asset_group: 14,403 POLYMARKET phantom manifest rows — capture_status=captured but 0 parquets written;
  blocks Phase 3.6 phantom gate for prediction"
created: 2026-05-19
author:
  ikenna-slot-3 (Phase 3.6 post-migration phantom audit; discovered 2026-05-19 ~16:14 UTC during CO-DUTY monitoring)
source:
  - "instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group prediction --dry-run (run
    2026-05-19 16:13 UTC)"
  - "gs://central-element-323112-phantom-triage/triage_prediction_20260519_151357.jsonl (14403 records)"
  - "gcs_migration_bundle_pipeline_mode_2026_05_08.md Phase 3.6 phantom gate — phantom count must be 0 post-migration"
locked_by: live-defi-rollout
locked_since: 2026-05-19
severity:
  P1 — blocks Phase 3.6 gate for prediction asset_group, therefore blocks operator sign-off (Phase 3 step 7), Phase 6
  --apply for prediction, and downstream Phase 9 final QG sweep. Other 4 asset_groups (defi/cefi/sports/tradfi)
  unblocked independently once their audits complete.
---

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

## Why it matters

**Diagnosis — pre-existing, not migration-induced.** The Phase 3 migration walks EXISTING parquets on disk and
renames/moves them to add `pipeline_mode=` hive partition. If no POLYMARKET parquets existed before the migration (which
is what `Real captures: 0` confirms), the migration VM would find no files to move for POLYMARKET entries. The manifest
phantom rows would remain unchanged. These 14,403 rows were almost certainly created during Polymarket adapter
development/testing but the actual data ingestion pipeline was never run.

Evidence for pre-existing:

- `Real captures: 0` — zero POLYMARKET parquets in the entire bucket, not just post-migration
- Prediction migration VMs completed with 0 errors (prediction-2026 MIGRATION_SUMMARY shows only non-POLYMARKET rows in
  the moved count)
- The 5 drift-axes the migration fixes (path-prefix, hive-vocab, instrument_type casing, schema-4 empty instrument_type,
  chain-bundle equivalence) are ALL about renaming/moving existing parquets, not about phantom manifest rows

**Gate impact:**

- Phase 3.6 phantom gate requires **0 phantoms across ALL 5 asset_groups**. Prediction having 14,403 fails this gate.
- Phase 3 step 7 (operator per-asset-group sign-off) requires Phase 3.6 to pass.
- Phase 6 `--apply` for prediction requires Phase 3.6 gate and operator sign-off.
- Defi/cefi/sports/tradfi sign-off is INDEPENDENT of prediction — operator can sign off those 4 as soon as their audits
  confirm 0 phantoms (audits still running at time of this doc; task IDs: defi=bt2z59y9n, cefi=b60wk5m8q,
  sports=bdr7rr817, tradfi=buecm6jby).

**Not a migration correctness bug.** The migration ran cleanly. This is a data-never-captured condition for Polymarket
data that pre-dates the migration.

## Recommended decision

**Option A (recommended):** Run Phase 6 `--apply` for prediction now (agent-owned, `[AGENT]` tag, ADC perms cover infra
ops). This flips all 14,403 rows from `capture_status=captured` → `capture_status=attempted_failed` with a typed reason.
This is the correct state — the manifest was lying; `attempted_failed` triggers the Polymarket data pipeline to retry.

```bash
cd instruments-service && python scripts/reconcile_phantom_manifest_rows_all.py \
  --asset-group prediction --apply
```

After --apply, the prediction phantom count will be 0 → Phase 3.6 gate clears for prediction → operator can sign off
prediction inline.

Downstream effect: any Polymarket consumer (MTDS prediction handler, features-service prediction compute) will see
`attempted_failed` entries and will schedule retries for dates that were previously being silently skipped (because the
manifest claimed the data was already captured). This is the intended behavior per CLAUDE.md "Manifest phantom audit".

Per workspace rules (CLAUDE.md § "Plans Run To Actual Completion"): `attempted_failed` rows for Polymarket prediction
data are the correct terminal state UNLESS the Polymarket adapter is wired and credentials available. Check:
`plans/active/issues/kalshi_polymarket_classify_venue_error_missing_2026_05_18.md` for current Polymarket adapter
status.

**Option B (if operator wants to investigate first):** Hold Phase 6 --apply for prediction; proceed with Phase 3/6/9
sign-off for the other 4 asset_groups (defi/cefi/sports/tradfi) independently. Prediction Phase 6 runs after operator
confirms whether the 14,403 are truly pre-existing (they are, but a quick
`gcloud storage ls -r gs://market-data-tick-prediction-central-element-323112/` confirms zero POLYMARKET-keyed paths).

**Blocking gate status:**

- Phase 3.6 prediction: 🔴 BLOCKED — 14,403 phantoms (pre-existing Polymarket; Phase 6 --apply will clear)
- Phase 3.6 defi/cefi/sports/tradfi: ⏳ AUDITS RUNNING (task IDs above)
- Operator sign-off prediction: 🔴 BLOCKED until Phase 3.6 passes
- Phase 6 prediction: 🔴 BLOCKED until operator decision on Option A vs B above

**Recommended operator action**: `[ack] Option A — run prediction Phase 6 --apply` in slot_3.md ping.

## Escalation

Filed as operator ping in `ikenna_orchestrator/pings/slot_3.md` — section "Phase 3.6 OPERATOR ESCALATION — prediction
Polymarket phantoms 2026-05-19".

Related:

- `plans/active/issues/kalshi_polymarket_classify_venue_error_missing_2026_05_18.md` — Polymarket error classification
  gap
- `plans/active/gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phase 3 step 6 + Phase 6
- `plans/active/issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`
