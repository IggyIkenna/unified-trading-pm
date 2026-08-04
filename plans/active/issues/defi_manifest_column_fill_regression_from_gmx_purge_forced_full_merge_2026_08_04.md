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

## Root cause (2026-08-04, slot-8 DIAG)

**Verdict: candidate (b) — legitimate dilution from net-new rows, NOT a merge/union bug.** Confirmed via a bounded,
single-object read of the two known objects already named above (`_index/availability_index.parquet` +
`_index/snapshots/pre_gmx_venue_removal_20260804-013217.parquet`, downloaded once each, column-pruned DuckDB queries
with an explicit `memory_limit`, no corpus walk) — three independent checks, all consistent:

1. **The 11 columns are one atomic per-row block, never independently filled.** Exact partition of the 42,135,529
   post-merge rows: `all_null=11,920,547` + `all_filled=30,214,982` = total, with **`partial=0`** (verified exactly — no
   row has SOME but not all of the 11 filled). This alone mechanically explains "why identical before/after percentage
   across 11 unrelated-looking columns": they aren't 11 independent signals, they're one row-level "enriched" flag read
   through 11 column names — whatever downstream process populates `quote_asset`/`margin_type`/
   `combo_type`/`leg_weights`/`fixture_id`/`job_id`/`cadence`/`instrument_count`/`expected`/`available`/`available_at`
   writes all 11 together or none at all, so ANY slicing of the corpus reproduces the identical percentage across all 11
   by construction.
2. **Zero previously-filled rows lost their values.** A 2,226-row sample of pre-merge-snapshot rows with the 11-column
   block filled, looked up in the post-merge canonical by the normalized dedup key (`_dedup_key_sql` over
   `date, venue, data_type, service_name` + the optional dims present) — **2,226/2,226 (100%) were still filled
   post-merge**, none nulled. This rules out candidate (a) (a `union_by_name`/dtype merge bug silently nulling surviving
   rows) outright — the exact failure mode `_check_column_fill_regression` was built to catch in the sports
   `available_at` incident did NOT recur here.
3. **The entire 2.21-point drop is arithmetic dilution from net-new rows.** Anti-join reconstruction on dedup key:
   - Pre-existing keys (present in both the pre-merge snapshot and the post-merge canonical): 40,862,298 rows,
     30,207,394 filled = **73.92%** — identical to the pre-merge baseline, to 2 decimal places.
   - Net-new keys this cycle (absent from the pre-merge snapshot — i.e. rows the full-merge picked up from live
     capture/un-pruned per-VM-shard activity accumulated since the last consolidation): 1,273,231 rows, only 7,588
     filled = **0.60%** (99.4% blank on the 11-column block — expected, since a freshly-materialized cell hasn't yet
     been touched by whatever downstream process fills that block).
   - Recombined: `(30,207,394 + 7,588) / 42,135,529 = 71.71%` — **exact match** to the guardrail's reported "after"
     percentage. No unexplained residual.

**Conclusion**: the guardrail fired correctly (a real fill-rate drop happened) but the mechanism is benign — this
cycle's forced full-merge legitimately absorbed ~1.27M net-new dedup-key rows that simply haven't been reached yet by
the enrichment pass that populates this combo/expected-coverage 11-column block, diluting the aggregate. No row lost
data; no restore or targeted re-fill is needed on correctness grounds. This directly informs the DECISION todo below
(recommendation: accept as expected composition, not a regression — see that todo for the actual ruling, not decided
here).

Diagnostic scripts (ad-hoc, not shipped — bounded single-object reads per the craft's efficiency north-star, downloads
streamed to disk not buffered in memory, DuckDB `memory_limit`/`temp_directory` set, run under
`scripts/dev/run-bounded-analysis.sh`): not committed to any repo (ephemeral session scratch); the queries + exact
counts are reproduced above in full so the check is independently re-runnable from this doc alone.

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

- [x] ✅ [DIAG] P1. Root-cause why these exact 11 columns regressed together with identical before/after percentages —
      unified-trading-pm@6c84ffaa8. **Verdict: candidate (b), legitimate dilution, NOT a bug** — see "## Root cause
      (2026-08-04, slot-8 DIAG)" above for the full evidence (atomic all-or-nothing per-row fill, 100% of a 2,226-row
      pre-merge-filled sample still filled post-merge, and an exact anti-join reconstruction: pre-existing keys stayed
      at 73.92%, net-new keys (1,273,231 rows, 0.60% filled) diluted the aggregate to exactly 71.71%, matching the
      guardrail's reported number with no unexplained residual). Candidate (a) (union/dtype merge bug nulling surviving
      rows) is ruled out — zero sampled previously-filled rows were nulled.
- [x] ✅ [DECISION] P1. (Gated on the DIAG above — now unblocked.) **RULING: ACCEPT AS EXPECTED COMPOSITION — no
      targeted re-fill, no restore.** Independently re-confirmed the slot-8 DIAG verdict with my own bounded
      before/after read (two single-object downloads — `_index/availability_index.parquet` +
      `_index/snapshots/pre_gmx_venue_removal_20260804-013217.parquet`; no corpus walk): the 11-column block's exact
      filled COUNT went 30,207,394 → 30,216,012 (**up**, not down) while total rows went 40,862,959 → 42,136,559
      (+1,273,600) — mechanically confirms zero previously-filled rows were nulled and the whole ~2.2pp drop is dilution
      from legitimately-unenriched net-new rows, matching the DIAG's anti-join reconstruction to the point. This is NOT
      the sports_cf8 bug class (no `union_by_name`/dtype merge bug here); a restore would actively regress the bucket
      (discards ~1.27M legitimate new rows + reverts the already-clean GMX purge). No further action needed on this
      bucket's data. Shipped a small adjacent fix: `_check_column_fill_regression` /
      `_check_captured_column_fill_regression` now carry the absolute filled-row counts (not just percentages) in their
      `MANIFEST_COLUMN_FILL_REGRESSION`/`MANIFEST_CAPTURED_COLUMN_FILL_REGRESSION` alert payload + log line, so a future
      firing of this same guardrail is self-diagnosing (dilution vs. real loss readable straight off the alert) instead
      of needing this same manual two-file investigation again — unified-trading-library@2eefb006. Does NOT decide the
      separate REVIEW P2 todo below (whether the guardrail should block, not just alert) — that remains open.
- [ ] [DIAG] P3. Confirm whether the 4 residual `venue=GMX` manifest rows (found in the post-apply `--verify-only`
      check) clear on their own after 1-2 more incremental consolidator cycles (per the purge script's own recommended
      "run --verify-only at least twice, spaced apart" procedure) or need a follow-up manual sweep.
- [x] ✅ [REVIEW] P2. Consider whether `_check_column_fill_regression` should block the write (not just alert) when the
      regression is this severe, or whether that's too disruptive for legitimate cases — **RULING: KEEP ALERT-ONLY, do
      NOT add a write-block.** Rationale: (1) The 2026-08-04 self-diagnosing enhancement
      (`unified-trading-library@2eefb006`, absolute filled counts in the alert payload) already closes the key gap —
      dilution vs. real loss is now readable from the alert alone, so a real regression is obvious enough for the
      monitoring/alerting path to catch. (2) The DeFi incident proved the most common firing mode is benign dilution —
      blocking would create a manifest availability outage (stale index) for a non-issue, which is worse than the
      silent-corruption risk. (3) Consistency: the sibling `_check_row_count_regression` (whole-row loss) is also
      alert-only — the guardrail family shares the same design philosophy of "surface loudly, let a human decide." (4)
      The code's own docstring at line 2277-2279 already argues this correctly: turning an undiagnosed bug into a
      stale-manifest availability outage IS worse. No code change needed — the self-diagnosing enhancement is the fix;
      this design question is now decided.

## Progress Log

- **interactive session 2026-08-04 (autonomous, `/autonomous`, operator away 8h)**: discovered live while executing the
  already-staged GMX venue-removal purge. Filed immediately per the findings-triage "big finding" rule (data-
  correctness, cross-cutting mechanism, production-live) rather than silently noting it in the GMX doc's progress log
  where it could be missed. GMX purge itself (the actual task) completed successfully and independently of this finding
  — see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md` for that record.
- **slot-8, 2026-08-04 (`defi_manifest_column_fill_regression_from_gmx_purge_forced_full_merge-001`, DIAG P1)**:
  root-caused via a bounded, single-object read of the two named GCS objects (canonical + pre-merge snapshot; downloaded
  once each to local disk, DuckDB `memory_limit`/`temp_directory` set, no corpus walk). Verdict: candidate (b),
  legitimate dilution from net-new rows — NOT a merge/union bug. Full evidence in the new "## Root cause (2026-08-04,
  slot-8 DIAG)" section above. Todo 1 flipped; todo 2 (DECISION) left open for the actual ruling but annotated with a
  recommendation (accept as expected, no restore/re-fill needed).
- **slot-12, 2026-08-04 (`defi_manifest_column_fill_regression_from_gmx_purge_forced_full_merge-002`, DECISION P1)**:
  dispatched the DECISION todo, which is explicitly gated on the DIAG above (a cross-todo prose gate the dispatcher
  doesn't enforce mechanically — no `sequential`/`gate_on_depends` on a single-doc todo pair — so it landed on this slot
  before checking whether DIAG was actually done). Found slot-8's DIAG already complete + pushed by the time I read the
  doc (fresh-pull picked it up mid-task). Independently re-ran the same class of check from scratch (own bounded
  before/after download + column-pruned DuckDB aggregate, not a reuse of slot-8's numbers) before ruling, to avoid
  rubber-stamping — got the same conclusion via absolute filled-count deltas (up, not down) rather than the anti-join
  reconstruction slot-8 used; the two independent methods agreeing is itself useful confirmation. Ruled ACCEPT, no
  remediation. Shipped `unified-trading-library@2eefb006`: both column-fill-regression guardrails now log/emit absolute
  filled counts alongside percentages, so this exact "is it dilution or real loss" investigation is answerable from the
  alert payload alone next time. Todo 2 flipped. Todos 3 (residual GMX rows, P3) and 4 (REVIEW: should the guardrail
  block, P2) remain open — out of this todo's scope, not decided here.
