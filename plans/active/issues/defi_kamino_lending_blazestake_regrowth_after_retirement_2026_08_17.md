---
doc_type: issue
title: >-
  DeFi `KAMINO_LENDING` (80 captured) and `BLAZESTAKE` (1 captured) regrew from 0 after their 2026-08-05/07
  retirements — same recurrence class as the tracked POOL-uppercase/dex_pools regrowths, not yet root-caused
summary: >-
  Live 2026-08-17 honest-coverage rollup (`gs://central-element-323112-honest-coverage/2026-08-17/coverage.json`,
  generated_at 2026-08-17T00:49:33Z, partial=false) shows `venue=KAMINO_LENDING` at `captured=80` (out of 645 total,
  565 `attempted_failed`) and `venue=BLAZESTAKE` at `captured=1` (out of 1,405 total, 1,404 `empty_confirmed`).
  `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 7 verified `KAMINO_LENDING` at 0 captured on
  2026-08-05/07 (`retire_kamino_lending_legacy_venue_2026_08_05.py --apply`, verified against the freshly-written
  index) and row 6 verified `BLAZESTAKE` at 0 captured on 2026-08-06 (`relabel_retire_blazestake_venue_2026_08_06.py`,
  1,406 objects relabeled to `SOLBLAZE-SOLANA`). Both have since regrown small nonzero `captured` populations — the
  same "capture_status-flip retirement undone once a writer/rebuild re-touches the legacy label" mechanism already
  root-caused for `dex_pools` (see `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`'s Progress Log
  2026-08-12 entry: the 2026-08-10/11 defi manifest rebuild re-registered all 454,014 previously-retired `dex_pools`
  rows back to `captured`) and for `instrument_type=POOL` (see
  `defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` — root-caused to a live `market-data-processing-service`
  writer defect, fix shipped `market-data-processing-service@94215e9cd9`, not yet confirmed live in production).
  Filed while reconciling `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04_finalize.md` todo 1 — small
  scale (80 + 1 rows) but the SAME correctness pattern, not yet investigated for these two specific venues.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, market-data-processing-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, kamino-lending, blazestake, manifest, recurrence, data-correctness]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04_finalize.md,
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
  ]
created: "2026-08-17"
author: slot-4 (backend_engineer, adopted review craft for this dispatch)
last_updated: "2026-08-20"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.3
source: >-
  Live re-verification of defi_distinct_values_zero_noncanonical_dispatch_2026_08_04_finalize.md todo 1
  ("re-run the axis's zero-non-canonical check"), 2026-08-17.
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/defi_kamino_lending_blazestake_regrowth_after_retirement_finalize_2026_08_17.md,
  ]
---

# DeFi `KAMINO_LENDING`/`BLAZESTAKE` small regrowth after retirement (2026-08-17)

## What I found

Live query against the freshest honest-coverage rollup (`2026-08-17/coverage.json`, `generated_at:
2026-08-17T00:49:33Z`, `partial: false`) via `unified_trading_library.get_storage_client`:

- `venue=KAMINO_LENDING`: `captured=80`, `attempted_failed=565`, `total=645`. The 2026-08-05 retirement
  (`market-tick-data-service` `relabel_kamino_lending_venue_2026_08_05.py` + `retire_kamino_lending_legacy_venue_
  2026_08_05.py`) drove this to 0 captured / 565 retired, verified directly against the freshly-written index at the
  time (`defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 7).
- `venue=BLAZESTAKE`: `captured=1`, `empty_confirmed=1404`, `total=1405`. The 2026-08-06 retirement
  (`relabel_retire_blazestake_venue_2026_08_06.py`) drove this to 0 captured, verified against the canonical index
  (same source doc, row 6).

Both are small in absolute row count but represent the SAME recurrence mechanism already confirmed at much larger
scale for two sibling axes this session cross-referenced:

- `dex_pools` (454,014 rows) — the 2026-08-10/11 `canonical-migration-defi-rebuild` VM re-scanned legacy on-disk
  objects and re-registered them `captured`, undoing the 2026-08-05 retirement (root-caused, documented in
  `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`'s 2026-08-12 Progress Log entry).
- `instrument_type=POOL` (uppercase, up to 7.9M rows across two recurrences) — root-caused to a live
  `market-data-processing-service` writer defect (`canonical_writer.py`'s GCS path builder not lowercasing
  `instrument_type`), fix shipped `market-data-processing-service@94215e9cd9` 2026-08-16, NOT yet confirmed live in
  production as of the same doc's 2026-08-17 entry.

Not yet investigated for `KAMINO_LENDING`/`BLAZESTAKE` specifically: whether the same rebuild-rescans-legacy-objects
mechanism (dex_pools' cause) or the same MDPS writer-casing-conflation class (POOL's cause) applies here, or a third,
distinct mechanism (e.g. a live cron still emitting the old bare-venue label for a subset of rows, a data source that
re-lists at the pre-fix venue name for a small slice of shards).

## Why it matters

Small today (81 rows combined), but the recurrence PATTERN is now confirmed present on at least 3 independent defi
axes (dex_pools 454K, POOL-casing up to 7.9M, and now these two at much smaller scale) — a capture_status-flip
retirement is evidently not durable fleet-wide while legacy GCS objects/writers persist. Left uninvestigated, this
specific pair could regrow the same way `dex_pools`/`POOL` did (0 → hundreds of thousands) the next time a rebuild VM
or an affected writer touches these venues.

## Recommended decision

Root-cause via the same playbook already proven for `dex_pools`/POOL (physical-object sampling to rule in/out a
rebuild-rescan vs a live writer defect), then either apply the same durable fix class or file a fresh, more urgent
doc if the row count is found to be growing rather than static. Not urgent enough to interrupt the higher-priority
P0 POOL-recurrence work already in flight.

## Todos

- [ ] [DIAG] P3. Root-cause the `KAMINO_LENDING` (80 captured) and `BLAZESTAKE` (1 captured) regrowth since their 2026-08-05/06 retirements by sampling the regrown rows' underlying GCS objects directly (`gcs_describe_object`) — line-1-completeness fix 2026-08-19, `/plan-reconcile manifest_master` (method moved up from line 2).
      Goal: determine whether they correspond to real physical objects at the legacy venue path (rebuild-rescan class,
      like `dex_pools`) or are manifest-column-only artifacts from a live writer defect (like POOL-uppercase).
      Re-check row counts first (may have grown since 2026-08-17) before designing a fix. (repo:
      market-tick-data-service or market-data-processing-service, per whichever mechanism is found)

## Progress Log

- **2026-08-17 (slot-4, backend_engineer, review-craft dispatch)**: filed while reconciling
  `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04_finalize.md` todo 1's live axis re-check. Not
  investigated further — out of scope for the reconciliation task, small enough to defer without blocking anything
  higher-priority.
- **na-eligibility-audit 2026-08-17 (defi tranche, dispatch agt-f4fef7) [body-hash-pending]**: RECLASSIFY, whole-doc,
  conflict-clear — sole open todo (`[DIAG] P3`, root-cause the small regrowth) is a bounded, worker-determinable
  diagnostic (sample the regrown rows' underlying GCS objects directly, compare against the two already-confirmed
  recurrence mechanisms) with no operator judgment call gating it. Conflict-check against the 4 required surfaces
  clear: (a) `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04_finalize.md`'s 2 open `[REVIEW]` todos are
  about reconciling/archiving that plan, not this investigation — and that finalize doc's own text (line ~107-110)
  explicitly says this finding was "not previously tracked" and cites THIS doc as where it was filed; (b) no sibling
  batch/finalize doc drafted this run; (c) zero mention in `defi_consolidated_closeout_2026_07_18.md`; (d) zero
  competing claim in any `status: draft` satellite batch (`defi_satellite_ao_dispatch_batch11_2026_08_09.md`'s
  BLAZESTAKE mentions are prior-art citations of its retirement SCRIPT pattern for an unrelated venue retirement,
  not a claim on this regrowth). Flipped `assigned_vm: NA -> planning`, `execution_scope -> orchestrator-agent` in
  place (no rename); `assigned_role: data_engineering` already correct. Paired with
  `plans/active/defi_kamino_lending_blazestake_regrowth_after_retirement_finalize_2026_08_17.md` (`depends_on` +
  `gate_on_depends: true`, `status: active`).
- **context-scout 2026-08-17**: populated context_scope (4 entries) — the two sibling recurrence-mechanism docs, the
  delete-safety protocol the root-cause todo's GCS sampling must follow, and the paired gating finalize plan.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries) — unchanged, still accurate
