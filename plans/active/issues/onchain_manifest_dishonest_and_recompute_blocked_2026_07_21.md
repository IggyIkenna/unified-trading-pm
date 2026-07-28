---
doc_type: issue
title: >-
  onchain feature manifest is dishonest (11 of 13 rows falsely `captured`), and the operator-authorized mark→recompute
  is blocked on two upstream defects: a frozen index/consolidator and missing MTDS chain-field collection
summary: >-
  Operator authorized (2026-07-21) marking the 6 false-captured + 5 feature-less onchain manifest rows to
  attempted_failed and then recomputing. Investigation found BOTH halves are blocked by deeper defects. MARK is blocked:
  the onchain availability_index has 13 rows all frozen at date=2026-01-25 all `captured`, despite GCS objects through
  2026-05-22 — the index-update/consolidator path is broken (measured no-op, shards_scanned=1/rows_in=0 against 723 live
  objects), so a proper ManifestWriter.record_failed cannot reach the index and a raw parquet edit is banned + fragile
  (a future consolidator run would clobber it). RECOMPUTE is blocked: the 5 feature-less calculators require input
  columns (ltv, liquidation_threshold, flash_loan_liquidity, health/collateral, reward_rate) that the upstream MTDS
  lending source does NOT collect — so rerunning produces the same empty shards. The producer-honesty fix already
  shipped (features-service@907e17b4) stops NEW runs from writing these as captured; the durable close is fix
  consolidator → mark via API → build the missing MTDS collectors → recompute.
status: open
nature: issue
asset_group: [defi]
stage: [data, features]
repos: [features-service, market-tick-data-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest-honesty, consolidator, recompute-blocked, upstream-gap, defi, coverage-correctness]
related:
  [
    /plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
    /plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md,
  ]
created: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: backend
drift_direction: advance-code
depends_on: []
source:
  [
    "operator ruled mark→recompute 2026-07-21; investigating the mark mechanism + recompute feasibility found both
    blocked by a frozen consolidator and a missing MTDS collection gap",
  ]
resolved_by:
locked_by:
---

# onchain manifest dishonest + mark→recompute blocked

## The 13 index rows (onchain/\_index/availability_index.parquet), all `date=2026-01-25`, all `captured`

| feature_group           | instrument_count | GCS objects    | verdict                             |
| ----------------------- | ---------------- | -------------- | ----------------------------------- |
| lending_rates           | 14,630,914       | real (15 cols) | ✅ correct                          |
| lst_yields              | 1,602            | real (8 cols)  | ✅ correct                          |
| health_factor           | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| rewards                 | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| liquidation_events      | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| risk_params             | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| flash_loan_availability | 14,630,914       | feature-less   | ❌ should be attempted_failed       |
| perp_funding_rates      | 0                | none           | ❌ should be attempted_failed/empty |
| macro_sentiment         | 0                | none           | ❌ should be attempted_failed/empty |
| lst_native_rates        | 0                | none           | ❌ should be attempted_failed/empty |
| rate_impact             | 0                | none           | ❌ should be attempted_failed/empty |
| onchain_perps           | 0                | none           | ❌ should be attempted_failed/empty |
| utilization             | 0                | none           | ❌ should be attempted_failed/empty |

(The identical `instrument_count=14,630,914` across five different groups AND lending_rates is itself implausible as a
per-group count — a separate count-provenance bug, not chased here.)

## Blocker 1 — MARK cannot be applied cleanly (frozen index / broken consolidator)

The index is frozen at a single day (`2026-01-25`) while GCS objects exist through `2026-05-22` (118 day partitions).
The index-update/consolidator path is broken: measured `shards_scanned=1 / rows_in=0` against 723 live objects — it has
stopped scanning and stopped self-correcting. Consequences for the mark:

- `ManifestWriter.record_failed` (writes `capture_status="attempted_failed"`) writes to the per-run/per-shard manifest
  layer that must be CONSOLIDATED into the index. With the consolidator no-op, a fresh `record_failed` never reaches the
  13-row index — so marking via the supported API is inert here.
- A raw rewrite of the 11 rows in `availability_index.parquet` is banned (manifest writes go through the writer/shard
  discipline, never a raw parquet edit) AND fragile: if the consolidator is ever repaired and re-runs, it would clobber
  the hand-edit (or loud-fail on the shape mismatch). Band-aiding a broken manifest masks the real defect.

**So the honest mark requires fixing the onchain index-update/consolidator FIRST**, then re-deriving the index from the
producer-honest shards (the producer fix `features-service@907e17b4` already emits the correct `attempted_failed` /
`empty_confirmed` states going forward). Diagnosing why the consolidator went no-op (and why onchain writes stopped at
2026-05-22) is the prerequisite.

## Blocker 2 — RECOMPUTE cannot produce features (missing MTDS collection)

The 5 feature-less calculators read input columns that the upstream source does not carry (verified against
`orchestrator_calculators.py` + the live `lending_rates` parquet schema):

| feature_group           | calculator needs (input cols)                  | present in source? |
| ----------------------- | ---------------------------------------------- | ------------------ |
| risk_params             | `ltv`, `liquidation_threshold`                 | **no**             |
| flash_loan_availability | `flash_loan_liquidity` / `available_liquidity` | **no**             |
| health_factor           | health/collateral fields                       | **no**             |
| liquidation_events      | liquidation fields                             | **no**             |
| rewards                 | `reward_rate`                                  | **no**             |

The `lending_rates` source carries only `aave_supply_apy` / `aave_borrow_apy` / `aave_utilization` /
`aave_liquidity_index` / `aave_borrow_index` / `aave_reserve_factor` / `rate_spread` — none of the fields above. So the
calculators correctly produce nothing, and **rerunning them yields the same empty shards.** Recompute is not a rerun —
it is NEW upstream work: MTDS (or the onchain collectors) must capture `ltv` / `liquidation_threshold` / reserve
`reward_rate` / flash-loan liquidity / the health-factor inputs from chain before these five groups can be real.

## The fix chain (durable close, in order)

1. **Diagnose + fix the onchain index-update/consolidator** (why frozen at 2026-01-25, why no-op vs 723 objects, why
   writes stopped 2026-05-22). Prerequisite to any honest coverage number.
2. **Re-derive the index from producer-honest shards** — with `907e17b4` shipped, the 11 groups then render
   `attempted_failed` / `empty_confirmed` honestly (this IS the "mark", done correctly via the pipeline, not by hand).
3. **Build the missing MTDS chain-field collectors** (ltv / liquidation_threshold / reward_rate / flash_loan_liquidity /
   health-factor inputs) — the real unblock for the 5 feature-less groups.
4. **Recompute** the five groups once their inputs exist.

## Recommendation

Do NOT hand-edit the frozen prod index (fragile band-aid on a broken subsystem). Treat step 1 (consolidator) as the
gating fix; the producer honesty is already shipped. Steps 3–4 are genuinely new scope (upstream collection), not a
rerun — size them as their own work, not as part of "mark→recompute". This reframes the operator's "mark now" as "fix
the consolidator so the already-shipped producer honesty propagates."

## Update 2026-07-28 (slot-12, `data_engineering`) — ROOT CAUSE FOUND: not a broken consolidator, an orphaned migration artifact

**The premise in "The fix chain" step 1 above is corrected by this investigation: there is no broken/frozen live
consolidator process for this bucket.** Direct evidence (read-only `gcloud storage`/`gcloud storage cat` against
`gs://features-defi-prd-central-element-323112`, `unified-trading-sa` identity, 2026-07-28):

1. **The 13 rows this doc's table describes live at a path that is DEAD migration debris, not a manifest any
   consolidator or reader consults.**
   `gs://features-defi-prd-central-element-323112/onchain/_index/availability_index.parquet` (25 columns, pre-v9-ish
   shape) holds exactly those 13 rows, all `date=2026-01-25`, all `capture_status=captured` — byte-identical to this
   doc's table. This nested `onchain/_index/` tree (also has its own `onchain/_index/per_vm/_legacy_seed.parquet` +
   `onchain/_index/latest.json` stamped `2026-07-18T11:02:44Z`) is a **verbatim carry-over of the legacy
   `features-onchain-defi-{pid}` bucket's own root manifest**, produced by [[bucket_fold_features_2026_07_17]]'s
   2026-07-18 migration step ("Reconcile the features-onchain-defi twin THEN parity migrate" —
   `onchain-defi(727, 977MB)→features-defi-prd/onchain/`). That migration did an "Index-only SKIP" for several OTHER
   legacy per-kind buckets (delta-one-{defi,tradfi}, volatility-{cefi,tradfi}, mtf-cefi — buckets that held only
   consolidator artifacts, no real data) but **onchain-defi genuinely had real `by_date/` data (727 objects) that needed
   migrating, so its whole object tree was copied wholesale — including its own `_index/` subtree**, which should have
   been excluded the same way the empty legacy buckets' indexes were. The result: the old bucket's frozen manifest
   snapshot rode along under a `{kind}/` prefix in the new bucket, where it has sat, unreferenced, ever since — no
   consolidator (live or one-off) has touched it since the copy, because a consolidator cycle takes a real GCS **bucket
   name**, never a sub-prefix, so `features-defi-prd-.../onchain` was never (and can never be) a valid `--bucket`
   target.

2. **The bucket's ACTUAL root manifest — the one every consolidator cycle, reader, and data-status surface consults — is
   alive and current, not frozen.** `gs://features-defi-prd-central-element-323112/_index/availability_index.parquet`
   (41 columns, current schema) holds exactly **one** onchain-family row:
   `date=2026-07-26, feature_group=rate_impact, capture_status=captured, instrument_count=71, service_name=features-service`.
   `_index/latest.json` at the SAME root shows `last_run_at=2026-07-28T09:22:39Z` (minutes before this check),
   `shards_scanned=1, rows_in=0, incremental=true, no_op=true` — a genuinely fresh, healthy cron tick.
   `shards_scanned=1` is just the root `_index/per_vm/_legacy_seed.parquet` (the one-time fold-created seed, correctly
   EXCLUDED from every merge per `manifest_consolidator.py`'s own legacy-seed-exclusion-once-canonical-exists logic —
   see module docstring 2026-07-15 fix) — i.e. `rows_in=0` is the CORRECT, designed answer given the current write
   pattern, not a symptom of breakage. The onchain feature-writer's production write path evidently uses the **legacy
   CAS path** (`_resolve_per_vm_shards()` → `manifest_per_vm_shards` not set for this Cloud Run workload → writes go
   straight to the canonical, bypassing per-VM shards + the consolidator entirely) rather than per-VM shards —
   consistent with zero real per-VM shards ever appearing at bucket root.

3. **`onchain/by_date/` itself is current and growing** — 724 real `features.parquet` objects span `day=2026-01-25`
   through `day=2026-07-26` (re-measured today; the original "GCS objects exist through 2026-05-22" figure above is now
   itself stale — writes have continued for two more months). So the feature-COMPUTE pipeline is demonstrably alive and
   writing data today; what's missing is that only ONE of its feature_groups (`rate_impact`) has ever registered a
   manifest row at the live root — the other 12 groups (including the two legitimately-captured
   `lending_rates`/`lst_yields`) have **no root-manifest presence at all**, honest or otherwise. Their only manifest
   "record" is the dead 2026-01-25 nested snapshot.

**Track 8 reconciliation (explicitly required by this todo): NOT a genuine contradiction.** Track 8's 2026-07-22
correction (`defi_consolidated_closeout_2026_07_18.md`) verified, via read-only `gcloud scheduler jobs list/describe`,
that `uts-prod-manifest-consolidator-market-data-defi-cron` + the `instruments-defi`/`features-defi` consolidator jobs
are **ENABLED, running every 1 minute** — a claim about **Cloud Scheduler job state**. That is TRUE and independently
re-confirmed here (`_index/latest.json`'s `last_run_at` is minutes old). This doc's 2026-07-21 "frozen at 2026-01-25 /
measured no-op" finding is a claim about **manifest CONTENT at a specific object path** — and that path
(`onchain/_index/availability_index.parquet`) turns out to be a disconnected legacy artifact the live, correctly-
running scheduler was never wired to touch. Both claims are correct; they are not measuring the same thing, so there is
no contradiction to resolve — just a wrong assumption (in this doc's original framing) about which file the "13 rows"
lived in and what process was responsible for it.

**Root cause, stated plainly:** the 2026-07-18 bucket-fold migration's bulk copy of `features-onchain-defi-{pid}` →
`features-defi-prd/onchain/` carried the legacy bucket's own stale manifest index along with its real data, creating an
orphaned duplicate manifest tree with no live owner. Separately (and not a "brokenness" — just a coverage gap), the live
root manifest was never backfilled with honest rows for the historical `onchain/by_date/` corpus (Jan 25 – present) — it
only starts accumulating real rows going forward, one write at a time, for whichever feature_group's writer actually
runs (`rate_impact` so far).

**No trivial one-line fix exists.** Closing this honestly requires a genuine design/migration decision, not a code
change: (a) delete the orphaned `onchain/_index/` tree (pure migration debris — GCS delete, needs the standard
delete-safety check + likely `[OPERATOR]` per this repo's delete-gating rule, since it is a prod bucket write) AND (b)
decide how the historical `onchain/by_date/` corpus (724 objects, Jan 25–Jul 26) should be honestly registered into the
LIVE root manifest — a bulk one-time backfill of `record_captured`/`record_empty`/`record_failed` rows per (date,
feature_group) re-validated against real GCS content (the same captured-vs-featureless split this doc's own table
already worked out for the 13 legacy rows), which is new scope, not a rerun of anything broken. Per this todo's own
contract, remediation stays open pending that design decision; this Update is the required documented diagnosis.
Recommend the operator/main decide between: (i) fold this into the existing fix-chain's step 2 ("re-derive the index
from producer-honest shards") but retarget it explicitly at the ROOT manifest instead of the dead nested one, or (ii)
treat it as new scope requiring its own plan given it's now a full historical backfill-registration job, not a
consolidator fix.

## Update 2026-07-28 (slot-13, `data_engineering`) — `instrument_count=14,630,914` root cause TRACED: NOT a live-code bug, no fix applicable

Per this doc's line 69-70 parenthetical ("a separate count-provenance bug, not chased here") and the corresponding
[[defi_satellite_ao_dispatch_batch1]] todo ("Diagnose (and fix ONLY if a clear code bug) the implausible identical
`instrument_count=14,630,914`"). Traced the count-aggregation/derivation code path end-to-end (features-service,
unified-trading-library — read-only; no MTDS involvement, the plan's repo list undercounted features-service as the
actual site). **Verdict: no live broadcast/join bug exists to fix.** The shared value is a fully-explained,
deterministic byproduct of two already-diagnosed defects compounding on a dead artifact — documenting as
legitimate/non-actionable per this todo's own done-when clause, not shipping a fix (there is nothing live left to fix).

**This corroborates, via independent code-level tracing, the live-bucket verification already recorded in the sibling
issue doc** `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md` § "VERIFIED 2026-07-28 (slot-7)"
(lines 197-266) — that section did the authoritative GCS/parquet-level proof (byte-exact md5 comparison across groups,
`num_rows` metadata summation across 118 day-partitions); this Update independently re-derives the same mechanism purely
from reading the current code, and the two agree exactly.

**Where `instrument_count` is set (current, live code) — correctly per-`(date, feature_group)`-scoped, not shared:**

- `features-service/features_service/onchain/engine/orchestrator_manifest.py:89-96` (`_write_feature_group_manifest`)
  calls `ManifestWriter.add(row_count=self._last_record_count, feature_group=feature_group, ...)` →
  `unified-trading-library/unified_trading_library/manifest_writer/_writer_ingest.py:358-361` maps `row_count` straight
  to `AvailabilityRecord.instrument_count`. This is the only onchain manifest-write path (no separate onchain-specific
  writer).
- `self._last_record_count` is reset to `0` at the top of `process_feature_group()` **before** dispatch
  (`orchestrator.py:177`), reset again inside the shared per-day loop helper `_process_daily_feature_group()`
  (`orchestrator_daily_loop.py:202`), accumulated only for that one call (`orchestrator_daily_loop.py:144`), and written
  back immediately after that group's own dispatch completes. `process_feature_group()` is awaited serially per
  feature_group (no concurrent mutation of `self`) — **this rules out a live cross-group state-leak.**
- UTL's dedup keys are also correctly group-scoped: `_BASE_DEDUP_COLS` + `_OPTIONAL_DEDUP_COLS` includes `feature_group`
  (`manifest_consolidator.py:523-537`, added `7a72049a` 2026-05-26); `_merge_dataframes()`
  (`unified_trading_library/manifest_writer/_writer_io.py:1220-1269`) dedups on the same keys. No `ffill`/cross-row
  merge path exists anywhere in `manifest_consolidator.py`/`_writer_io.py`/`_read_index.py` that could leak one group's
  count into another's.

**Why the shared value exists anyway — two compounding, already-diagnosed causes, not a new bug:**

1. **The already-fixed calculator column-projection bug** (`features-service@907e17b4`, shipped 2026-07-20, this doc's
   §"Blocker 2" / the sibling issue doc's §1). The 5 feature-less calculators
   (`_calculate_rewards_features`/`_calculate_risk_params_features`/`_calculate_flash_loan_features`/
   `_calculate_health_factor_features`/`_calculate_liquidation_features`, `orchestrator_calculators.py:293-405`) all
   consume the SAME `load_rate_indices()` source that `lending_rates` also consumes (`orchestrator.py:560-643` dispatch,
   `data_loader.py:459` loader), and defensively project down to base columns only (`timestamp`, `instrument_id`)
   because none of their real feature columns (`reward_rate`/`ltv`/
   `liquidation_threshold`/`flash_loan_liquidity`/health-factor fields) exist in the raw AAVE rate-indices frame — a
   **row-for-row, row-count-preserving** projection, not a row-reducing one. Result: all 6 groups have identical row
   cardinality, day for day, corpus-wide (5 by dropping columns not rows; `lending_rates` keeps its real columns and
   also drops no rows).
2. **The frozen orphaned legacy-seed manifest artifact** (this doc's own 2026-07-28 slot-12 Update above,
   `_LEGACY_SEED_PATH = "_index/per_vm/_legacy_seed.parquet"`, `manifest_consolidator.py:177,1493-1529`) — a
   permanently-frozen, never-pruned bootstrap-seed shard, confirmed dead migration debris with no live consolidator
   owner. Its `instrument_count=14630914` is a **whole-corpus cumulative SUM**, not a per-day count: summing
   `flash_loan_availability`'s real per-day row count (parquet `num_rows` metadata) across all 118 real day-partitions
   on disk (`day=2026-01-25`..`day=2026-07-26`) gives exactly 14,630,914 — an exact match. It was stamped onto one
   synthetic `date=2026-01-25` row per group at some past (undated, script not found) bootstrap/seed time.

Because cause (1) makes all six groups' daily row counts identical, their independently-computed 118-day sums are
**mathematically bound** to land on the same total — hence one shared value across exactly the 6 groups that route
through `_process_daily_feature_group()` with real GCS objects, and no others. This is not a copy-paste/shared-variable
bug in whatever process produced the seed; it is signal (b) surfacing the same already-fixed §"Blocker 2" defect from
the manifest-count side rather than the row-content side.

**Disposition: no fix shipped, none applicable.** The live orchestrator/UTL code is correctly per-group scoped today;
the producer bug that gives the six groups identical row cardinality is already fixed (`907e17b4`); the artifact
carrying the stale shared count is dead, orphaned, unconsulted data, not a currently-running code path. Remediation
stays exactly the fix chain this doc already names above (delete the orphaned `onchain/_index/` tree + backfill honest
root-manifest registration) — nothing new to add to it from this diagnosis. No `[OPERATOR]`-gated action taken (this
Update is diagnosis-only, per the sourcing todo's own scope).

## Todos

- [ ] [DATA] P1. **Retagged from [OPERATOR] 2026-07-28, split into the two halves per the doc's own two stated options —
      no fresh operator ask needed for either.** (a) **Delete the orphaned `onchain/_index/` tree**
      (`gs://features-defi-prd-central-element-323112/onchain/_index/`, dead migration debris with no live consolidator
      owner, confirmed by the 2026-07-28 slot-12 Update above): run a FRESH `gcs_bucket_soft_delete_retention_seconds()`
      against `features-defi-prd-central-element-323112` as part of executing this todo — if it returns `>=604800s`,
      that same-run check satisfies delete-safety-protocol §3a (finding T), proceed with the delete citing the check's
      own output as evidence, no separate operator sign-off required; if it returns below the threshold or errors, STOP
      and escalate to the operator with the measured value. (b) **Bulk-register the historical `onchain/by_date/`
      corpus** (724 objects, Jan 25–Jul 26) into the LIVE root manifest via
      `record_captured`/`record_empty`/`record_failed` rows per (date, feature_group), re-validated against real GCS
      content (the same captured-vs-featureless split this doc's own table already worked out for the 13 legacy rows) —
      **dispatched as its own new-scope backfill (option (ii) from the doc's two stated options)**, not folded into a
      "fix chain step 2" rerun, since the Update above is explicit this is new registration scope, not a rerun of
      anything broken. Mirror the established `record_captured`-per-instrument registration recipe used for the
      2026-07-21 defi dex_pools/lending_indices fold
      (`/plans/archive/issues/defi_fold_manifest_registration_pending_2026_07_21.md`) rather than inventing a new
      registration mechanism.
