---
doc_type: issue
title: Sports data capture gap — EPL 2025 absent from GCS availability index
status: active
asset_group: [sports]
created: 2026-06-29
author: slot-5 (data_engineering, claude-sonnet-4-6)
source: [plans/active/issues/verify_p1_prereq_dag_2026_06_29.md, verify_p1_prereq_dag-003]
assigned_vm: planning
---

# Finding 3 — Sports data capture gap: EPL 2025 absent from GCS manifest

Filed from the [VERIFY] P1 run of `run_live_verify_sports`
(verify_p1_prereq_dag-003, 2026-06-29) after the Finding-2 semantic fix.

## What I found

```
Run: run_live_verify_sports --today 2025-12-01 --league-id EPL --season-year 2025
GCP project: central-element-323112

Result: INSUFFICIENT_HISTORY (4/4 shards)
  api_football  FIXTURES    captured=0  missing_rows=123
  footystats    MATCH_STATS captured=0  missing_rows=123
  odds_api      ODDS        captured=0  missing_rows=123
  understat     XG          captured=0  missing_rows=123

Window: [2025-08-01, 2025-12-01] (semantic fix confirmed — window_end=today ✓)
Bucket: tick-data / sports
```

The semantic fix (Finding-2, unified-api-contracts@0d7805a8) is working correctly:
the required window now clips to `today` (2025-12-01) instead of the full season
end (2026-05-31). The `INSUFFICIENT_HISTORY` verdict is now due to a genuine data
gap — the availability index contains zero captured rows for EPL 2025 across all
4 sports data types.

## Why it matters

EPL 2025 sports data (api_football FIXTURES, understat XG, odds_api ODDS,
footystats MATCH_STATS) is the only clean AG in the VERIFY P1 prereq DAG (other
AGs are gated on phantom-reconciliation plans). If the sports capture pipeline
has never run for EPL 2025 or its output isn't merged into the consolidated
availability index, the smoke harness cannot produce a RUNNABLE verdict even with
the semantic fix applied.

This gates the [VERIFY] P1 milestone: RUNNABLE for sports is blocked until the
capture gap is resolved.

## Recommended decision

Operator to determine which of the following applies:
1. The sports capture pipeline ran but writes to a path not covered by the
   availability index bucket (path-prefix mismatch). → Fix: re-index or
   widen the prefix template.
2. The sports capture pipeline has not been run for EPL 2025 yet. → Fix:
   trigger a sports backfill run for EPL 2025, verify manifest rows appear.
3. The consolidated manifest index was last built before the sports captures
   landed. → Fix: re-run the manifest consolidator for the sports bucket.

## Actionable follow-ups

- [ ] [INVESTIGATE] P1. Check if EPL 2025 sports capture files exist in GCS
      (tick-data/sports bucket); distinguish missing-capture from
      missing-index. (repo: e2e-testing)
- [ ] [FIX] P1. Based on investigation: either trigger backfill run for EPL
      2025 sports OR re-index the manifest consolidator for the sports
      bucket. (repo: market-tick-data-service)
- [ ] [VERIFY] P1. Re-run `run_live_verify_sports --today 2025-12-01` after
      fix → expect RUNNABLE for all 4 EPL 2025 shards. (repo: e2e-testing)
