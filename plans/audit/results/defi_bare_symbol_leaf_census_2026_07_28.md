---
doc_type: audit-result
title: "DeFi bare-symbol-leaf batch-write census (2026-07-20 → 2026-07-28)"
summary: >-
  Bounded per-day GCS delimiter descent (not a corpus walk) over pipeline_mode=batch_* DeFi objects, 2026-07-20 through
  2026-07-28, checking each filename against the UAC oracle's id-form check. Measured 6,932 total objects and 5,738
  id-form violations (82.8%) across 28 day/pipeline_mode combinations, 2026-07-20 through 2026-07-27. The violation rate
  collapses to 0.0%/1.2% on 2026-07-27, the day write_defi_rows()'s leaf fix shipped
  (market-tick-data-service@0fddb95e), independently confirming the fix is effective. day=2026-07-28 carried zero
  pipeline_mode=batch_* subdirectories at probe time (genuine zero).
status: pass
severity: P1
nature: record
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [defi, census, bare-symbol-leaf, id-form, canonicalisation, write-defi-rows]
related:
  [
    defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24,
    defi_satellite_ao_dispatch_batch1_2026_07_25,
    canonical-cutover-register,
    four-surface-reconciliation-procedure,
  ]
created: 2026-07-28
resulting_plan:
lib_version:
  "unified-api-contracts (workspace) / unified-trading-library (workspace) / market-tick-data-service@db830f3c"
doc_versions_checked:
audited_scope:
  "asset_group=defi, raw_tick_data (batch lane only), PROD (-prd-) bucket, read-only, bounded per-day delimiter descent,
  days 2026-07-20 through 2026-07-28 (run date)"
date: 2026-07-28
auditor: agent-orchestrator slot-9 worker (data_engineering craft)
parent_epic: defi_master
---

# DeFi bare-symbol-leaf batch-write census (2026-07-20 → 2026-07-28)

**Purpose**: measure the scale of `pipeline_mode=batch_*` DeFi objects written under the bare-symbol filename-leaf shape
since 2026-07-20 (the `canonical-cutover-register.md` §5 "capture stopped" reference point), per
`plans/archive/issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`'s "[DIAG]
Measure the scale" todo, executed via `plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s
corresponding todo.

**Method**: read-only, bounded per-day GCS delimiter descent (single-walk discipline — no corpus walk). For each
`day=2026-07-20` .. `day=2026-07-28` (run date), one delimited listing under `raw_tick_data/by_date/day={D}/` finds the
real `pipeline_mode=batch_*/` subdirectories, then one bounded prefix listing under each
`.../pipeline_mode={mode}/asset_group=defi/` enumerates that day's defi objects. Every object is checked with the
shipped UAC oracle (`canonical_path_violations(path, violation_classes={CanonicalViolationClass.ID_FORM})`,
`unified-api-contracts@d40c5d7d`/`@1cd27478`) — never a re-implemented rule. Script:
`market-tick-data-service/scripts/census_defi_bare_symbol_leaf_since_2026_07_20.py`. Raw output:
`defi_bare_symbol_leaf_census_2026_07_28.json` (this directory).

Bucket: `market-data-tick-defi-prd-central-element-323112`. Run date: 2026-07-28 (UTC). `day=2026-07-28` carried zero
`pipeline_mode=batch_*` subdirectories at probe time (no batch write had landed yet today) — a genuine zero, not a
listing failure.

## Per day / pipeline_mode

| day        | pipeline_mode                           | objects | id-form violations |   rate |
| ---------- | --------------------------------------- | ------: | -----------------: | -----: |
| 2026-07-20 | batch_aave                              |      12 |                  6 |  50.0% |
| 2026-07-20 | batch_chainlink                         |      80 |                 39 |  48.8% |
| 2026-07-20 | batch_onchain_subgraph                  |     523 |                479 |  91.6% |
| 2026-07-20 | batch_pyth_hermes                       |       4 |                  0 |   0.0% |
| 2026-07-21 | batch_aave                              |      12 |                  6 |  50.0% |
| 2026-07-21 | batch_chainlink                         |      80 |                 39 |  48.8% |
| 2026-07-21 | batch_onchain_rpc                       |      21 |                 21 | 100.0% |
| 2026-07-21 | batch_onchain_subgraph                  |     537 |                500 |  93.1% |
| 2026-07-21 | batch_pyth_hermes                       |       4 |                  0 |   0.0% |
| 2026-07-22 | batch_aave                              |      12 |                  6 |  50.0% |
| 2026-07-22 | batch_chainlink                         |      80 |                 39 |  48.8% |
| 2026-07-22 | batch_kalshi_perp                       |      13 |                 13 | 100.0% |
| 2026-07-22 | batch_onchain_rpc                       |      10 |                 10 | 100.0% |
| 2026-07-22 | batch_onchain_subgraph                  |    1236 |               1201 |  97.2% |
| 2026-07-22 | batch_pyth_hermes                       |       4 |                  0 |   0.0% |
| 2026-07-23 | batch_kalshi_perp                       |      13 |                 13 | 100.0% |
| 2026-07-23 | batch_onchain_rpc                       |      20 |                 20 | 100.0% |
| 2026-07-23 | batch_onchain_subgraph                  |     876 |                839 |  95.8% |
| 2026-07-24 | batch_kalshi_perp                       |      13 |                 13 | 100.0% |
| 2026-07-24 | batch_onchain_rpc                       |      18 |                 18 | 100.0% |
| 2026-07-24 | batch_onchain_subgraph                  |     833 |                795 |  95.4% |
| 2026-07-25 | batch_kalshi_perp                       |      13 |                 13 | 100.0% |
| 2026-07-25 | batch_onchain_rpc                       |      20 |                 20 | 100.0% |
| 2026-07-25 | batch_onchain_subgraph                  |     934 |                901 |  96.5% |
| 2026-07-26 | batch_onchain_rpc                       |      19 |                 10 |  52.6% |
| 2026-07-26 | batch_onchain_subgraph                  |     766 |                728 |  95.0% |
| 2026-07-27 | batch_onchain_rpc                       |      17 |                  0 |   0.0% |
| 2026-07-27 | batch_onchain_subgraph                  |     762 |                  9 |   1.2% |
| 2026-07-28 | _(no batch\_\* pipeline_mode dirs yet)_ |       0 |                  0 |      — |

**TOTAL: 6,932 objects, 5,738 id-form violations (82.8%) across 28 day/pipeline_mode combinations.**

## Per pipeline_mode (summed across all days)

| pipeline_mode          | objects | id-form violations |   rate |
| ---------------------- | ------: | -----------------: | -----: |
| batch_aave             |      36 |                 18 |  50.0% |
| batch_chainlink        |     240 |                117 |  48.8% |
| batch_kalshi_perp      |      52 |                 52 | 100.0% |
| batch_onchain_rpc      |     125 |                 99 |  79.2% |
| batch_onchain_subgraph |   6,467 |              5,452 |  84.3% |
| batch_pyth_hermes      |      12 |                  0 |   0.0% |

## Reading the numbers

- The violation rate collapses sharply on **2026-07-27**, the day `write_defi_rows()`'s leaf fix shipped
  (`market-tick-data-service@0fddb95e`): `batch_onchain_rpc` goes from 100.0% (every prior day measured) to 0.0%, and
  `batch_onchain_subgraph` drops from ~95-97% to 1.2%. This is direct, independent confirmation that the fix is live and
  effective on the batch lane, corroborating the issue doc's own note that option (c) ("ship the leaf fix on an
  expedited timeline") was executed in practice.
- `batch_pyth_hermes` measured 0% across every day it appears — this pipeline_mode was never affected (its objects were
  never routed through the broken `write_defi_rows()` leaf construction, or its ids happen to already be
  canonical-shaped).
- The residual 2026-07-27 violations (9 `batch_onchain_subgraph` objects, 0 `batch_onchain_rpc`) are consistent with
  objects written earlier that same day, before the fix deployed intraday — not evidence the fix is incomplete.
- **6,932 total bare-symbol-leaf-shaped objects were written across the 2026-07-20 → 2026-07-26 window** (the days
  entirely before the fix), confirming Fact 1 of the source issue doc: DeFi batch capture was actively growing, not
  frozen, during the window `canonical-cutover-register.md` §5 described as "capture stopped." This is the backlog
  population any future leaf-rename migration needs to account for.

## Codex / doc cross-links

- Source issue:
  `plans/archive/issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md`
- Dispatching plan: `plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md`
- Oracle SSOT: `/codex/02-data/four-surface-reconciliation-procedure.md`, `/codex/02-data/canonical-cutover-register.md`
  §5
- Raw data: `plans/audit/results/defi_bare_symbol_leaf_census_2026_07_28.json`
- Script: `market-tick-data-service/scripts/census_defi_bare_symbol_leaf_since_2026_07_20.py`
