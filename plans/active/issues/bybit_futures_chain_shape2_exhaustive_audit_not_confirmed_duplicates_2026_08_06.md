---
doc_type: issue
title:
  "BYBIT futures_chain shape-2 exhaustive audit refutes Phase 1's safe-to-delete verdict — 624/1114 flat objects carry
  data absent from any same-day canonical form (~3.7M rows at risk under the old Phase 4 assumption)"
summary: >-
  The exhaustive shape-2 duplicate verification (batch4 todo 1, run 2026-08-06, slot 8) diffs every
  bare_flat/bundled_flat BYBIT futures_chain object against its same-day hive/canonical counterpart across all 546 scope
  days. Phase 1's 5-day sample concluded shape-2 flat files are pure duplicates, safe to supersede-then-delete. The
  exhaustive run shows that conclusion holds for only 490/1114 objects (44%): 290 objects carry 125–38,407 rows absent
  from their same-day counterpart (1,151,992 rows total unique to the flat form) and 334 objects have no same-day
  counterpart at all (2,597,103 rows exist only in flat form that day). Phase 4's cleanup gate must be re-gated: merge
  unique flat rows into the canonical underlying= form (or confirm cross-day duplication) before any deletion; only the
  490 confirmed duplicates are safe as Phase 1 assumed.
status: open
nature: findings
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [bybit, futures_chain, shape-2, duplicate-audit, data-correctness, phase4-gating]
related:
  [
    /plans/active/issues/bybit_futures_chain_write_shape_2026_07_13.md,
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/archive/2026_07/bybit_futures_chain_write_shape_migration_2026_07_13.md,
  ]
created: 2026-08-06
author: slot-8
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    "Exhaustive shape-2 duplicate verification run 2026-08-06 (cefi_satellite_ao_dispatch_batch4_2026_07_31.md todo 1,
    slot 8) — audit parquet _index/audit/bybit_futures_chain_shape2_duplicate_verify_2026_07_13.parquet (1114 rows),
    script market-tick-data-service/scripts/audit_bybit_futures_chain_shape2_duplicates_2026_07_13.py.",
  ]
assigned_vm: NA
execution_scope: local-only
model_tier: sonnet-doable
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# BYBIT futures_chain shape-2 exhaustive audit — 56% of flat objects NOT confirmed same-day duplicates

> **🟡 OPERATOR — data-correctness finding.** The Phase 4 cleanup gate of
> `bybit_futures_chain_write_shape_migration_2026_07_13.md` (already `BLOCKED-OPERATOR-DECISION`) rests on a Phase 1
> sample-based premise this exhaustive audit refutes. See "Why it matters" below before acting on any Phase 4 deletion.

## What I found

The full-scope audit (`_index/audit/bybit_futures_chain_shape2_duplicate_verify_2026_07_13.parquet`, **1114 objects**
across all **546 days** classified `bare_flat_only`/`bundled_flat_only`/`mixed`, 2023-04-05 → 2025-09-23) row-level
diffs each shape-2 flat object against its same-day hive/canonical counterpart using Phase 1 Todo 2's columns. Results:

| verdict        | objects | %   | flat rows | meaning                                                                         |
| -------------- | ------- | --- | --------- | ------------------------------------------------------------------------------- |
| duplicate      | 490     | 44% | 4,434,598 | every flat row key is present in the same-day counterpart (0 unique)            |
| not_duplicate  | 290     | 26% | 2,039,531 | **1,151,992 rows (per-object 125–38,407) absent** from the same-day counterpart |
| no_counterpart | 334     | 30% | 2,597,103 | **no same-day hive/canonical form exists** — data unique that day               |

Day-level (546 days): duplicate=220, not_duplicate=175, no_counterpart=151. All 290 not_duplicate objects are on `mixed`
days (bare_flat=146, bundled_flat=144). The 334 no_counterpart objects sit on bare_flat_only days (190 objects),
bundled_flat_only days (41), and 103 objects on mixed days. Robustness: 0/80 sampled objects flip verdict under a strict
`(timestamp, id)` key — the results are not a column-precision artifact.

## Why it matters

Phase 4 of the archived migration plan (now folded into `data_completion_to_100_all_ag_2026_06_21.md`, still
`BLOCKED-OPERATOR-DECISION`) plans to delete the non-canonical (glued + bare-underlying) originals once parity
verification is green. Phase 1 Todo 2's **5-day sample** concluded shape-2 flat files are "a pre-existing PARTIAL
duplicate... never a source of genuinely unique trades... safe to supersede-then-delete". The exhaustive audit shows
that conclusion does **not** generalize:

- **290 objects carry ~1.15M rows absent from their same-day hive/canonical counterpart.** E.g.
  `day=2023-04-24 ETH.parquet` holds 3,245 rows of `ETH-30JUN23` (a contract entirely missing from that day's hive
  file); `day=2024-12-01 ticks.parquet` holds 7,409 rows of BTC contracts its bare_flat siblings don't cover.
- **334 objects have no same-day canonical counterpart at all** — 2.6M rows exist only in flat form that day.
- Combined, ~3.7M rows are not recoverable from any same-day canonical file. Deleting these flat objects under Phase 1's
  assumption would lose them (unless a cross-day duplication exists — not verified; the audit is same-day by design).

## Recommended decision

Re-gate Phase 4 before any deletion:

1. For each of the 290 `not_duplicate` objects, **merge the unique flat rows into its canonical
   `underlying={U}/ticks.parquet` target** — the same concat+dedupe merge pattern already proven in
   `reshape_bybit_futures_chain_glued_to_hive_2026_07_13.py` (Phase 3.5 remediation). The audit parquet is the
   source-of-truth object list.
2. For the 334 `no_counterpart` objects, decide their fate (backfill to canonical `underlying=` form, or keep as-is) —
   an operator decision, since it determines what happens to 2.6M rows of unique data.
3. Only the 490 confirmed-duplicate objects are safe to supersede-then-delete as Phase 1 assumed.

## Todos

- [ ] [DATA] P1. **Re-gate BYBIT futures_chain Phase 4 cleanup per the exhaustive shape-2 audit**: merge the **1,151,992
      unique rows** of the 290 `not_duplicate` shape-2 flat objects into their canonical `underlying=` hive targets
      (source-of-truth object list = `_index/audit/bybit_futures_chain_shape2_duplicate_verify_2026_07_13.parquet`;
      reuse the Phase 3.5 concat+dedupe merge pattern), so Phase 4 deletion is safe for them. (repo:
      market-tick-data-service)
- [ ] [OPERATOR] P1. **Rule on the 334 `no_counterpart` shape-2 flat objects** (2,597,103 rows existing only in flat
      form on bare_flat_only/bundled_flat_only/mixed days): backfill to canonical `underlying=` form, or keep — this
      determines Phase 4's treatment of those objects. (repo: market-tick-data-service)
