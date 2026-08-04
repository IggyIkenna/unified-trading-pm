---
doc_type: issue
title: >-
  GMX purge's forced full-merge triggered MANIFEST_COLUMN_FILL_REGRESSION on the DeFi bucket (11 columns, 73.92%→71.71%)
  — same guardrail class as sports_cf8, NOT yet root-caused for this bucket, live in production
summary: >-
  Executing the already-staged `purge_gmx_venue_removal_2026_07_25.py --apply` (see
  `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`) — GCS object delete (90/90 verified) and the CAS
  manifest rewrite (660 `venue=GMX` rows dropped) both succeeded cleanly. The script's OWN designed next step,
  force-consolidate (to re-stamp `consolidator_content_write_at`, which the CAS write strips), then hit
  `unified_trading_library.manifest_consolidator`'s `_check_column_fill_regression` guardrail — the SAME general check
  built in response to `/plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md` (the sports
  `available_at` incident) — which fired CRITICAL on the DeFi bucket for the first time: 11 columns' fill rate dropped
  from 73.92% to 71.71% (exceeds the 1-point alert threshold) during a from-scratch 30-shard merge
  (`market-data-tick-defi-prd-central-element-323112`, `rows_in=46,231,706 -> rows_out=42,135,529`, dedup_dropped
  4,096,177). The guardrail is ALERT-ONLY (logs CRITICAL + emits `MANIFEST_COLUMN_FILL_REGRESSION`) — it does NOT block
  the write, so the regressed index was persisted to `_index/availability_index.parquet` at 2026-08-04T03:15:40 and is
  now the live canonical for this bucket. NOT root-caused or remediated here — filed for operator/infra-owner attention
  given the CLAUDE.md data-pipeline-correctness "big finding" bar (data-correctness, silent, production-live).
status: open
nature: issue
asset_group: [defi, cross-cutting]
stage: [data]
repos: [unified-trading-library, market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, manifest-consolidator, column-fill-regression, data-correctness, gmx, cross-asset-group, big-finding]
related:
  [
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-04"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.8
source: >-
  Discovered live during the GMX venue-removal purge execution (interactive session 2026-08-04, /autonomous dispatch,
  operator away). Not anticipated — the purge script's own docstring only names a "resurrection-window" risk from
  skipping force-consolidate, not this regression class; this is a NEW manifestation, not something the script's authors
  could have known about in advance.
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
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
    /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md,
  ]
---

# DeFi manifest column-fill regression from the GMX purge's forced full-merge (2026-08-04)

## What happened, in order (all timestamps 2026-08-04 UTC)

1. `purge_gmx_venue_removal_2026_07_25.py --apply` ran (this session, `/autonomous` dispatch): 90/90 GCS objects backed
   up + deleted (verified), 660 `venue=GMX` manifest rows dropped via a CAS-safe Arrow rewrite (generation
   `1785805598514113` → `1785808285089945`, 40,862,959 → 40,862,299 rows). **This step is clean and not in question.**
2. The CAS write strips the canonical's `consolidator_content_write_at` custom-metadata marker (documented, expected —
   the script's own docstring names this and compensates with step 3).
3. The script's step-3 force-consolidate ran immediately after, per design. Because the marker was absent, the
   consolidator logged `merge cutoff UNPROVABLE: merging all 29 shard(s), pruning NOTHING this cycle` and did a
   **from-scratch full merge** of all 30 raw per-VM shards (`rows_in=46,231,706`) instead of its normal incremental path
   — this is the FIRST time in a while this bucket has taken the full-merge code path (routine cron cycles are
   incremental).
4. `_check_column_fill_regression()` (`unified_trading_library/manifest_consolidator.py`) fired CRITICAL:

   ```
   columns(before%->after%) = {
     'quote_asset': (73.92, 71.71), 'margin_type': (73.92, 71.71), 'combo_type': (73.92, 71.71),
     'leg_weights': (73.92, 71.71), 'fixture_id': (73.92, 71.71), 'job_id': (73.92, 71.71),
     'cadence': (73.92, 71.71), 'instrument_count': (73.92, 71.71), 'expected': (73.92, 71.71),
     'available': (73.92, 71.71), 'available_at': (73.92, 71.71)
   }
   ```

   Note ALL 11 columns show the IDENTICAL before/after percentage pair — suspicious in itself (a genuine per-column
   independent regression would be unlikely to land on the exact same two numbers across 11 unrelated columns; more
   consistent with one shared upstream cause, e.g. a specific shard or row-batch losing ALL of these columns together).

5. **The guardrail is alert-only** — logging + a `MANIFEST_COLUMN_FILL_REGRESSION` event, no write-block. The merge
   proceeded and wrote `_index/availability_index.parquet` (42,135,529 rows) at `03:15:40`. **This is now the live
   production canonical for the DeFi bucket.**
6. A subsequent `--verify-only` GMX-scoped check found 0 remaining GCS objects (clean) but 4 residual `venue=GMX`
   manifest rows — plausibly a resurrection-window artifact (a shard written between the CAS-rewrite's snapshot
   generation and the full-merge's shard-scan) rather than related to the column-fill regression; not yet confirmed.

## Why this is filed separately from `sports_cf8_available_at_backfill_regression_2026_07_13.md`

That doc (931 lines, still open) is where `_check_column_fill_regression` was BUILT, in response to a much more severe
sports-specific regression (`available_at` 62.9%→15.7%) that was fully root-caused (a writer-serializer bug,
`unified-trading-library@f5f15e3a`, already fixed) and is not the same mechanism here — the sports fix was specific to
`available_at` not being threaded through `_records_to_dataframe()`; that fix is presumably still in place and doesn't
explain 10 OTHER, non-`available_at` columns regressing together on a completely different bucket. This is the general
guardrail firing on a NEW asset group for what looks like a DIFFERENT, not-yet-diagnosed cause — extending the known
blast radius of "full-merge can silently drop column fill," not a recurrence of the already-fixed bug. That doc is
930/1000 lines (near its hard cap) — not a good target for the full investigation write-up; cross-referenced instead.

## What I did NOT do (and why)

- **Did not attempt to root-cause the exact mechanism** — this needs either a synthetic DuckDB repro (mirroring the
  method `sports_cf8`'s slot-3 touch used) or a targeted before/after row-level diff on a sample, and this session's
  remaining scope/time didn't allow a careful-enough investigation to avoid guessing.
- **Did not attempt a snapshot restore.** A pre-merge snapshot exists
  (`market-data-tick-defi-prd-central-element-323112/_index/snapshots/pre_gmx_venue_removal_20260804-013217.parquet`,
  taken before BOTH the GMX row-drop and the regression), but restoring it would also undo the legitimate GMX cleanup
  and discard the ~5.4M new rows this merge legitimately picked up from live capture activity since the last
  consolidation — a restore needs to be scoped to JUST the regressed columns/rows, not the whole index, and that scoping
  work isn't done. A blind full restore risks trading a small, bounded regression for a larger, less understood one.
- **Did resume the DeFi consolidator cron** (`uts-prod-manifest-consolidator-market-data-defi-cron`) — leaving it paused
  doesn't undo the already-persisted regression and has its own real cost (blocking ALL future consolidation for this
  bucket, not just GMX-related). Confirmed re-`ENABLED`.

## Todos

- [ ] [DIAG] P1. Root-cause why these exact 11 columns regressed together with identical before/after percentages.
      Candidates: (a) one or more of the 30 raw per-VM shards has a schema that's missing all 11 columns, and DuckDB's
      `union_by_name` merge is padding NULL for rows sourced from that shard in a way that ALSO nulls out rows from
      OTHER shards that previously had these columns filled (a genuine union/join bug, not just "new rows are
      unpopulated" — the fill % of the WHOLE 42M-row set dropped, meaning previously-filled rows lost their values, not
      just that new unfilled rows diluted the average — confirm this distinction with a row-level check before
      concluding); (b) a legitimate but non-obvious explanation (e.g., dedup_dropped=4,096,177 rows removed by the
      merge's tie-break happened to be disproportionately the ones that HAD these columns filled, and the SURVIVING rows
      are legitimately less-filled — this would NOT be a bug, just needs confirming). Use a bounded, single-object read
      of the pre-merge snapshot vs. the new canonical for a sample of dedup-key groups, not a full corpus walk.
- [ ] [DECISION] P1. (Gated on the DIAG above.) If confirmed a real bug: decide remediation — targeted re-fill of the
      affected columns/rows (preferred, mirrors the sports precedent) vs. a scoped restore vs. accept as low-severity
      residue (2.2-point drop on already-sparse ~74%-filled columns is a much smaller blast radius than the sports
      62.9%→15.7% case that triggered a full restore).
- [ ] [DIAG] P3. Confirm whether the 4 residual `venue=GMX` manifest rows (found in the post-apply `--verify-only`
      check) clear on their own after 1-2 more incremental consolidator cycles (per the purge script's own recommended
      "run --verify-only at least twice, spaced apart" procedure) or need a follow-up manual sweep.
- [ ] [REVIEW] P2. Consider whether `_check_column_fill_regression` should block the write (not just alert) when the
      regression is this severe, or whether that's too disruptive for legitimate cases — this doc doesn't decide that,
      flagging it as a design question given this is now the SECOND time (after sports_cf8) the guardrail fired without
      preventing the regression from landing in production.

## Progress Log

- **interactive session 2026-08-04 (autonomous, `/autonomous`, operator away 8h)**: discovered live while executing the
  already-staged GMX venue-removal purge. Filed immediately per the findings-triage "big finding" rule (data-
  correctness, cross-cutting mechanism, production-live) rather than silently noting it in the GMX doc's progress log
  where it could be missed. GMX purge itself (the actual task) completed successfully and independently of this finding
  — see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md` for that record.
