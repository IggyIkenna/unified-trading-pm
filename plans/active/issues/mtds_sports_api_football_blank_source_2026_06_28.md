---
doc_type: issue
title: "MTDS sports: 10,716 batch_api_football rows missing source= field (CF-4 regression)"
summary: |
  E8 audit re-run 2026-06-28 (slot-3) found a NEW regression on the MTDS sports surface:
  10,716 rows with pipeline_mode=batch_api_football have blank source= field. Previously
  (slot-6 run) CF-4 was GREEN (0 blank). This is a write-path bug — the writer stamping
  batch_api_football pipeline_mode is not also stamping source=api_football.
status: open
severity: HIGH
created: 2026-06-28
repos:
  - market-tick-data-service
tags: [CF-4, sports, source, pipeline_mode, regression, manifest]
nature: process
asset_group: cross-asset
stage: [meta]
scope: [engineer, admin]
related: []
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# MTDS sports: batch_api_football rows missing source= (CF-4 regression)

## Finding

E8 audit re-run 2026-06-28 found CF-4 regression on `market-data-tick-sports-prd-central-element-323112`:

- **New rows**: +23,118 since slot-6 run (361,839 → 384,957)
- **Regression**: 10,716 of these new rows have `pipeline_mode=batch_api_football` but `source=''` (blank)
- Previous audit (slot-6, 2026-06-27): CF-4 was GREEN (0 blank source on MTDS surface)

CF-4 distribution (current):
```
source:
  'odds_api': 223,723
  'mdps_odds_horizon_bucket': 109,638
  'polymarket_clob': 20,785
  'footystats': 20,095
  '': 10,716   ← blank — all from batch_api_football rows
```

## Root Cause (to investigate)

The `batch_api_football` pipeline_mode is used by instruments-service for sports reference entities (fixtures,
leagues, etc.). These rows appear to have been written to the MTDS canonical bucket (`market-data-tick-sports-prd`)
without stamping `source=api_football`. Possible origins:

1. **migrate_sports_canonical_v9.py**: the IS→MTDS migrator may have written IS reference rows to the MTDS
   bucket with IS pipeline_mode but without copying the `source` field correctly.
2. **A new api_football sports data capture**: MTDS may have started capturing api_football fixture/odds data
   directly (unlikely but possible given recent sports expansion).
3. **recover/restamp scripts**: one of the recovery scripts from 2026-06-19 may have written rows without source.

## Required Fix

Find the writer that created these 10,716 rows and ensure it stamps `source=api_football` (or the correct source)
on every row. Then either:
- Fix the writer forward (for ongoing captures)
- Backfill the existing 10,716 rows to stamp `source=api_football`

## Gating

This is a **blocker for E8** (CF-4 must be GREEN on MTDS before the E8 checkbox can be flipped). However since
E8 is already blocked on E3 drain + E4 VM apply (operator-gated), this fix can be done in parallel.

## Evidence

- Audit run: `plans/audit/results/cf_manifest_audit_2026_06_01.py` 2026-06-28
- Plan section: `plans/active/sports_manifest_canonicalisation_2026_06_01.md` § "E8 Verify — audit re-run 2026-06-28"
