---
doc_type: issue
title:
  "Cross-AG bleed — asset_group=prediction rows are physically in the instruments-store-sports availability index (6,597
  and growing), root cause unlocated"
summary: >-
  Independently measured by BOTH the /data-pipeline-reconciliation sports run (F4) and the prediction run (F1) on
  2026-07-20. The instruments-store-sports-prd _index holds at least 6,597 rows carrying asset_group=prediction (KALSHI
  6,562, POLYMARKET 35; trades 6,484, prediction_canonical_question_group 113), dated 2026-07-16 to 2026-07-19 with
  written_at up to 2026-07-20 13:10 — i.e. the bleed is ACTIVE, not a frozen relic. It has GROWN from the 4,097 rows
  documented in the reference sheets (2026-06-26 to 07-18), so it is worsening. A prediction shard belongs in the
  prediction estate, never the sports reference index; this is a manifest-writer cross-AG misattribution that corrupts
  both estates' coverage denominators. Root cause was NOT located in either read-only run. This is a taxonomy gap (no
  closed reconciliation type fits a cross-bucket asset_group bleed) escalated per the findings-triage HARD RULE, not a
  finding either read-only skill could fix. Measurement caveat — the sports index was in stale per-VM-shard fallback so
  6,597 is a recent-weighted lower bound.
status: open
nature: issue
asset_group: [sports, prediction]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [data-correctness, cross-ag-bleed, manifest, asset-group, sports, prediction, denominator, taxonomy-gap]
related:
  [
    data_pipeline_reconciliation_sports_2026_07_20,
    data_pipeline_reconciliation_prediction_2026_07_20,
    dp_catalog_not_running_sports_prediction_2026_07_15,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "/data-pipeline-reconciliation sports (F4) + prediction (F1) runs, 2026-07-20; both independently measured the same
  bleed at 6,597 rows via scoped manifest reads"
resolved_by:
---

# Cross-AG bleed — `asset_group=prediction` rows in the `instruments-store-sports` index

> **⚠️ BIG FINDING (data-correctness — cross-AG / cross-bucket).** Operator-notify per the findings-triage HARD RULE.
> Independently measured by two 2026-07-20 reconciliation runs (sports F4 + prediction F1). Filed as a tracked open
> issue; the read-only reconciliation skills could not root-cause it and neither could fix it.

## What was measured (two independent audits, same number)

- `instruments-store-sports-prd` `_index/availability_index.parquet` holds **≥ 6,597** rows with
  `asset_group=prediction` — KALSHI 6,562, POLYMARKET 35; by data_type: `trades` 6,484,
  `prediction_canonical_question_group` 113 (+ 1 cefi + 1 defi row noted by the sports run).
- Dates span **2026-07-16 → 2026-07-19**; `written_at` up to **2026-07-20 13:10** — the bleed is **active**, not a
  historical relic.
- It has **GROWN** from the **4,097** rows the reference sheets documented (2026-06-26 → 07-18) — worsening over time.
- **Measurement caveat (both runs):** the `instruments-store-sports` index was in stale per-VM-shard fallback
  (consolidated blob age > 120s), so 6,597 is a partial recent-weighted count and a **lower bound**. The
  `market-data`(tick)/sports manifest was not read for further bleed.

## Why it matters

A prediction shard atom lives in the prediction estate. Its physical presence in the SPORTS reference index means:

- The sports coverage denominator is inflated by rows that are not sports data (the sports run notes its reference-lane
  `captured` count is contaminated by cross-lane rows).
- The prediction estate under-accounts for shards that landed in the wrong bucket.
- Any consumer that trusts `instruments-store-sports` as sports-only reads prediction rows as sports.

Both are silent corruptions of the honest-coverage denominators the whole Foundation-gate rests on.

## Not covered elsewhere

Not the same as `dp_catalog_not_running_sports_prediction_2026_07_15.md` (that is catalogue-staleness alerts on the
`prod/catalog.parquet` writers, a different surface and a different failure). No existing issue doc tracks the
asset_group bleed itself; the reference sheets carry only the count, and both reconciliation runs explicitly deferred
the register/root-cause work as out of read-only scope.

## Investigation direction (root cause unlocated — do NOT guess-fix)

The writer that lands rows in the `instruments-store-sports` index is stamping some prediction (KALSHI/POLYMARKET)
shards with the sports bucket/index target. Likely candidates to trace: a shared manifest writer or per-VM-shard
uploader whose `asset_group` / bucket resolution is not scoped to the shard's true asset_group, or a KALSHI/prediction
job whose manifest target resolves to the sports instruments-store bucket. The KALSHI concentration (6,562 of 6,597)
plus the recent, still-growing dates are the strongest lead.

## Todos

- [ ] 1. [DATA] P1. Pin the true full count and composition — read the `instruments-store-sports` index after a fresh
      consolidation (not the stale per-VM fallback), grouped by `asset_group` × `venue` × `data_type` × `written_at`,
      and also check the `market-data`(tick)/sports manifest for the same bleed (repo: instruments-service).
- [ ] 2. [BACKEND] P1. Locate the writer — trace which job/uploader writes `asset_group=prediction` rows into the
      `instruments-store-sports` index (grep the manifest-writer / per-VM-shard upload path for where the bucket/index
      target is resolved vs the shard's asset_group; the KALSHI concentration and the 2026-07-16→ dates bound the
      search) (repos: instruments-service, market-tick-data-service).
- [ ] 3. [BACKEND] P1. Fix the misattribution at the writer so a prediction shard's manifest row lands only in the
      prediction estate; add a regression/guard test that a prediction shard can never write into a sports index (repos:
      instruments-service, market-tick-data-service, unified-api-contracts).
- [ ] 4. [DATA] P2. Remediate the already-written bleed rows — decide whether to relocate them to the prediction index
      or delete the mis-targeted rows (manifest-write, human-gated), and re-measure both estates' coverage denominators
      after (repo: instruments-service).
