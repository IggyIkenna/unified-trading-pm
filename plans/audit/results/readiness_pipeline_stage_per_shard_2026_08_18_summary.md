---
doc_type: audit-result
title: Readiness pipeline-stage per shard — 2026-08-18
summary:
  Per-shard (venue x asset_group x mode) BATCH/PAPER/LIVE pipeline-only readiness stage (declared,
  instruments_service, market_tick_data, market_data_processing, features legs — excludes strategy/execution),
  derived live via the readiness-state-dump skill against 2026-08-18's coverage manifest — 288 venues x 3 modes =
  864 rows, 0 ready / 624 not_ready / 240 unverified. Satisfies batch15 item 8's Tuesday-checkpoint done-when (a
  per-shard stage table committed covering every asset group).
status: pass
nature: record
asset_group: [cross-cutting]
stage: [data]
repos: []
scope: [engineer, admin]
tags: [audit, readiness, data-pipeline, honest-coverage, tuesday-checkpoint]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/epics/system_readiness_master.md,
    /cursor-configs/skills/readiness-state-dump/SKILL.md,
  ]
created: 2026-08-18
audited_scope:
  Every (venue, asset_group) pair present in the readiness-state-dump universe, across BATCH/PAPER/LIVE modes,
  scoped to the instruments-service-through-features-service pipeline legs only.
date: 2026-08-18
auditor: backend_engineer-slot8
parent_epic: system_readiness_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
---

# Readiness pipeline-stage per shard — 2026-08-18

Source: `cursor-configs/skills/readiness-state-dump` live run against
`gs://central-element-323112-honest-coverage/2026-08-18/coverage.json (date=2026-08-18)`. 288 venues x 3 modes = 864
rows. Scope: instruments-service through features-service legs only (declared, instruments_service,
market_tick_data, market_data_processing, features) — strategy/execution are a distinct gate set
(`data_pipeline_completion_2026_08_21.md`) and NOT folded into this stage.

Full per-shard row table (every venue x asset_group x mode, with per-leg state):
`readiness_pipeline_stage_per_shard_2026_08_18.json` (this file's JSON sibling).

`unverified` is a legitimate recorded value where no real check exists — not a gap in this dump.

## Per-asset-group x mode stage counts

| asset_group | mode | ready | not_ready | unverified | total |
| --- | --- | --- | --- | --- | --- |
| UNKNOWN | BATCH | 0 | 16 | 8 | 24 |
| UNKNOWN | PAPER | 0 | 16 | 8 | 24 |
| UNKNOWN | LIVE | 0 | 16 | 8 | 24 |
| cefi | BATCH | 0 | 5 | 19 | 24 |
| cefi | PAPER | 0 | 3 | 21 | 24 |
| cefi | LIVE | 0 | 3 | 21 | 24 |
| defi | BATCH | 0 | 133 | 47 | 180 |
| defi | PAPER | 0 | 133 | 47 | 180 |
| defi | LIVE | 0 | 133 | 47 | 180 |
| prediction | BATCH | 0 | 0 | 1 | 1 |
| prediction | PAPER | 0 | 0 | 1 | 1 |
| prediction | LIVE | 0 | 0 | 1 | 1 |
| sports | BATCH | 0 | 49 | 1 | 50 |
| sports | PAPER | 0 | 49 | 1 | 50 |
| sports | LIVE | 0 | 49 | 1 | 50 |
| tradfi | BATCH | 0 | 9 | 0 | 9 |
| tradfi | PAPER | 0 | 5 | 4 | 9 |
| tradfi | LIVE | 0 | 5 | 4 | 9 |

## Overall rollup (all asset groups, all modes)

- ready: 0
- not_ready: 624
- unverified: 240
- total rows: 864

## Findings surfaced by this dump (not previously named elsewhere)

- **`UNKNOWN` asset_group (8 venues, 24 rows across the 3 modes)** — venues present in the coverage manifest but not
  attributable to a known asset_group by this dump's classification. Worth a follow-up to identify these venues and
  either fix their asset_group attribution or confirm they are a genuine unclassified residual.
- **Zero shards reach pipeline-only `ready`** even excluding strategy/execution — every shard has at least one
  `not_ready` leg among declared/instruments_service/market_tick_data/market_data_processing/features. Consistent
  with the full-chain rollup already recorded in `system_readiness_master.md` W1 (0 ready / 844 not_ready / 20
  unverified across all 8 legs), so this is not a new gap — it confirms the data-pipeline-only view doesn't hide a
  false positive the full-chain view would have caught.
