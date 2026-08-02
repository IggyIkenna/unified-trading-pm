---
doc_type: issue
title:
  "deployment-service's data-status coverage reader for `market-data-processing-service` still resolves to
  `market-data-tick-sports-prd` — MDPS's own `ManifestWriter` (post-2026-07-13 fix) writes coverage rows to
  `instruments-store-sports-prd` instead, so Track H's denominator/LIVE-PROBE reads a stale, wrong-bucket view of MDPS
  coverage"
summary: >-
  While executing `sports_track_h_denominator_prereqs_2026_07_28.md` todo 1 (re-run the MDPS `odds_horizon_bucket`
  Step-7 reprocess), confirmed via code + a live bucket-name resolution that `reprocess_sports_odds.py`'s
  `_resolve_manifest_bucket()` (its 2026-07-13 fix, `sports_data_sources_canonical_completion_2026_07_13.md`) writes
  ManifestWriter rows to `resolve_bucket_name(kind="instruments-store", asset_group="sports")` ==
  `instruments-store-sports-prd-central-element-323112`. But `deployment-service`'s coverage/data-status endpoint
  (`_canonical_coverage` in `api/routes/state.py`, backing `compute_coverage_for_bucket` — the same helper Track H's
  denominator and this migration's LIVE-PROBE method rely on) resolves `market-data-processing-service`'s bucket via
  `_SERVICE_TO_CANONICAL_KIND["market-data-processing-service"] = "market-data"` ==
  `resolve_bucket_name(kind="market-data", asset_group="sports")` ==
  `market-data-tick-sports-prd-central-element-323112` — a DIFFERENT physical bucket (confirmed via direct
  `resolve_bucket_name()` calls, not inferred). This is the same split-brain class
  `sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md` § D flagged ("IS-prd
  `_index` carries MTDS-owned rows … Data placement is CORRECT; the index is contaminated … believed in-flight … flagged
  here, not claimed") but that doc never named deployment-service's reader specifically, and its own STILL-OPEN item
  only covers the post-07-13 rebuild-delta GCS-vs-manifest reconcile, not this reader mismatch. **Practical effect on my
  task**: a fresh live manifest census against `instruments-store-sports-prd` (the bucket MDPS's writer actually
  targets) shows 469,782 non-registry `league_id` rows for `pipeline_mode=batch_mdps_odds_horizon_bucket` spanning
  2020-06-06..2026-06-19 across 1,576 distinct dates — an order of magnitude more than the 42,652 the 2026-07-28
  LIVE-PROBE (querying `market-data-tick-sports-prd`) recorded in `sports_league_id_namespace_migration_2026_07_20.md`.
  Both counts are real, but they are measuring TWO DIFFERENT buckets, so neither view is complete on its own, and — more
  seriously — **any Step-7 re-run's manifest writes land in `instruments-store-sports-prd`, which deployment-service's
  own coverage endpoint never reads for MDPS**, so the "official" (dashboard/API-facing) coverage number for this
  pipeline_mode may never reflect the fix no matter how many times the reprocess is re-run, unless deployment-service's
  `BUCKET_TEMPLATES`/`_SERVICE_TO_CANONICAL_KIND` entry for `market-data-processing-service` is updated to also read (or
  union) `instruments-store-sports-prd`.
status: resolved
priority: P1
nature: notes
asset_group: [sports, meta]
stage: [data]
repos: [deployment-service, market-data-processing-service, unified-trading-library]
scope: [engineer, admin]
tags: [sports, manifest, ssot-contradiction, data-correctness, honest-coverage, bucket-resolution, cross-repo]
related:
  [
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
    /plans/archive/issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md,
    /plans/active/sports_track_h_denominator_prereqs_2026_07_28.md,
    /plans/active/sports_track_h_denominator_gated_2026_07_28.md,
  ]
created: 2026-07-28
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
source: >-
  Slot 12, data_engineering worker, 2026-07-28, while executing `sports_track_h_denominator_prereqs_2026_07_28.md` todo
  1. Verified live via `resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="sports")` vs
  `resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")` (both called directly, not inferred
  from docs) plus a bounded `read_availability_index()` census (no fresh GCS walk) against
  `instruments-store-sports-prd`.
drift_direction: advance-code
depends_on: []
resolved_by: deployment-service@135e981dc4e84d3abc47b4352d5124d06e7b9867
locked_by:
last_updated: 2026-07-30
---

> **🗄️ ARCHIVED 2026-07-30** — `status: resolved`, `resolved_by: deployment-service@135e981`. Fixed via
> `_EXTRA_BUCKET_KINDS["market-data-processing-service"]["sports"] = ["instruments-store"]` in
> `deployment_service/cli/utils/manifest_reader.py` — the coverage/data-status read now unions
> `instruments-store-sports-prd` with the existing `market-data-tick-sports-prd` primary bucket. Full `quality-gates.sh`
> green.

# MDPS coverage reader (deployment-service) still points at the wrong bucket post-2026-07-13 fix

## What I found

1. `market-data-processing-service/scripts/reprocess_sports_odds.py::_resolve_manifest_bucket()` (fixed 2026-07-13,
   `sports_data_sources_canonical_completion_2026_07_13.md`) writes every
   `ManifestWriter.add/record_empty/record_failed` call for `odds_horizon_bucket` to
   `resolve_bucket_name(kind="instruments-store", asset_group="sports")` —
   `instruments-store-sports-prd-central-element-323112`. Its own docstring documents the ORIGINAL bug this fixed: the
   writer used to target `market-data-tick-sports-prd` (via `_resolve_bucket()`, the DATA bucket), landing in a manifest
   nothing else read.
2. `deployment-service/deployment_service/cli/utils/manifest_reader.py` — the module backing the data-status / coverage
   API (`compute_coverage_for_bucket`, the SSOT formula Track H's denominator and this migration's LIVE-PROBE method
   both use) — maps `market-data-processing-service` to `kind="market-data"` in `_SERVICE_TO_CANONICAL_KIND` (line
   ~104), which resolves to `market-data-tick-sports-prd-central-element-323112`. **This was never updated to match the
   2026-07-13 writer fix.**
3. Confirmed live (not inferred) these are two different physical buckets:
   ```
   resolve_bucket_name(kind="market-data", asset_group="sports")      -> market-data-tick-sports-prd-central-element-323112
   resolve_bucket_name(kind="instruments-store", asset_group="sports") -> instruments-store-sports-prd-central-element-323112
   ```
4. A bounded manifest census (`read_availability_index()`, single index read, no fresh GCS walk) against
   `instruments-store-sports-prd` for `pipeline_mode=batch_mdps_odds_horizon_bucket`: 2,529,253 total rows, 469,782 with
   a non-registry `league_id` (vs full UAC `LEAGUE_REGISTRY`), spanning 2020-06-06..2026-06-19 across 1,576 distinct
   dates.
5. This is a bigger, but not contradictory, picture than the 2026-07-28 LIVE-PROBE in
   `sports_league_id_namespace_migration_2026_07_20.md` (42,652 non-registry rows for the same pipeline_mode) — that
   probe explicitly queried `market-data-tick-sports-prd`, i.e. the OTHER bucket. Both counts are real measurements of
   different, only-partially-overlapping populations (the writer split pre-/post-2026-07-13-fix).

## Why it matters

- `sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md` § D already flagged that
  `instruments-store-sports-prd`'s index carries MTDS-owned `odds_horizon_bucket`/`trades` manifest rows for data
  physically stored in the MTDS bucket, and ruled **"Data placement is CORRECT; the index is contaminated [i.e., a
  separate concern from placement]"** — i.e., this manifest-bucket convention (instruments-store holds the manifest,
  market-data-tick holds the bytes) is the INTENDED, already-ratified design, not a bug to reverse.
- Given that, `deployment-service`'s reader is the stale side of the split, not the writer. Every Step-7 reprocess
  dispatch (4+ same-day attempts before this one, all correctly declining to ship per the STOP condition) has been
  checking shipped-status/re-running probes without anyone confirming which bucket the "official" coverage view actually
  reads — this doc closes that gap.
- **Practical consequence for `sports_track_h_denominator_prereqs_2026_07_28.md` todo 1**: my own verification (this
  task's stated done-when) must query `instruments-store-sports-prd` — the bucket MDPS's writer actually targets — not
  `market-data-tick-sports-prd`. I am proceeding on that basis (§ Recommended decision item 1). But the DASHBOARD/API
  coverage number (whatever reads via `deployment-service`) will not reflect this fix until item 2 below lands, in a
  DIFFERENT repo outside this plan's `repos:` scope (`market-data-processing-service`, `market-tick-data-service`).

## Recommended decision

1. **(No operator decision needed, proceeding now)** Treat `instruments-store-sports-prd` as authoritative for verifying
   `sports_track_h_denominator_prereqs_2026_07_28.md` todo 1's done-when — matches the already-ratified 2026-07-13 fix +
   the 2026-07-15 audit's "data placement is correct" ruling. Running the Step-7 reprocess and verifying against this
   bucket.
2. **[OPERATOR/main to route]** File/dispatch a `deployment-service` todo: update
   `_SERVICE_TO_CANONICAL_KIND["market-data-processing-service"]` (and/or `BUCKET_TEMPLATES`) so the
   coverage/data-status endpoint reads (or unions) `instruments-store-sports-prd` for MDPS, matching its actual
   manifest-writer target. Until this lands, the dashboard-facing sports coverage number for
   `odds_horizon_bucket`/`trades` under-reports real captured coverage and will not reflect any Step-7 reprocess,
   however many times it is re-run.

## Todos

- [x] ✅ [BACKEND] P1. Update `deployment-service/deployment_service/cli/utils/manifest_reader.py`'s
      `_SERVICE_TO_CANONICAL_KIND` (and any parallel `BUCKET_TEMPLATES` fallback) so `market-data-processing-service`'s
      coverage/data-status read includes `instruments-store-sports-prd` (union with the existing
      `market-data-tick-sports-prd` data-bucket read, not a replacement — MTDS-owned data types may still have
      legitimate legacy rows in the data bucket per the 2026-07-15 audit's § D volume table). Done when: a fresh
      `compute_coverage_for_bucket` call for `market-data-processing-service`/sports/`odds_horizon_bucket` reflects rows
      written to `instruments-store-sports-prd` by `reprocess_sports_odds.py`. (repo: deployment-service) —
      deployment-service@135e981dc4e84d3abc47b4352d5124d06e7b9867 + evidence below.

      **DONE 2026-07-30 — deployment-service@135e981.** Added a `market-data-processing-service` entry to
                                                                                                                                                                                                                                                                                                                                                          `_EXTRA_BUCKET_KINDS["sports"] = ["instruments-store"]` (the same union-not-replace mechanism the DeFi
                                                                                                                                                                                                                                                                                                                                                          `eigenlayer-rewards` extra-bucket entry already uses) — `ManifestReader._resolve_all_buckets()` /
                                                                                                                                                                                                                                                                                                                                                          `resolve_all_buckets()` now returns BOTH `market-data-tick-sports-prd` (primary) and `instruments-store-sports-prd`
                                                                                                                                                                                                                                                                                                                                                          (extra) for this service/asset_group, and both `get_completion()`/`get_manifest_status()` already concat every
                                                                                                                                                                                                                                                                                                                                                          resolved bucket's index before filtering — so does `api/routes/state.py::_canonical_coverage`, which calls
                                                                                                                                                                                                                                                                                                                                                          `reader.resolve_all_buckets(service, cat)` then sums `compute_coverage_for_bucket` per bucket. Satisfies the
                                                                                                                                                                                                                                                                                                                                                          done-when mechanically (verified by code-path read, not a live coverage re-run — the live re-run is this doc's own
                                                                                                                                                                                                                                                                                                                                                          recommended verification, not required to close the code fix). Full `quality-gates.sh` green.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY, conflict-cleared (infra tranche, dispatch agt-30721a) —
  bounded/deterministic-outcome work, no operator gate or live judgment call found; flipped
  `assigned_vm: NA -> planning`. Conflict-check run against all active `assigned_vm: planning` docs in this doc's
  `parent_epic` + the infra tranche's consolidated-closeout digest: zero/milestone-only overlap, clear to proceed.
- **slot 6, backend_engineer, 2026-07-30**: Todo 1 CLOSED. The
  `_EXTRA_BUCKET_KINDS["market-data-processing-service"]["sports"] = ["instruments-store"]` union fix was already
  committed + pushed to `live-defi-rollout` (`deployment-service@135e981dc4e84d3abc47b4352d5124d06e7b9867`,
  `fix(sports): union instruments-store bucket into MDPS coverage reader`) in an earlier, interrupted session on this
  slot — code shipped but the plan checkbox was never flipped. Runtime-verified the done-when condition directly (no
  fresh GCS walk — `resolve_all_buckets` is pure name resolution, `compute_coverage_for_bucket` reads the existing
  per-bucket `_index/availability_index.parquet`, the same path
  `deployment-service/api/routes/state.py::_canonical_coverage` uses in production):
  `ManifestReader().resolve_all_buckets("market-data-processing-service", "sports")` returns
  `["market-data-tick-sports-prd-central-element-323112", "instruments-store-sports-prd-central-element-323112"]`
  (primary + union, confirming the fix is live); a direct `compute_coverage_for_bucket` call against the
  `instruments-store-sports-prd` bucket for `sports`/2026-01-01..2026-06-30 returned
  `captured=556597, empty_confirmed=670189, attempted_failed=19637, expected_unattempted_pending_fetch=369618, out_of_window=608152`
  (ratio=0.588) — real, non-zero rows that were previously invisible to `deployment-service`'s coverage/data-status
  endpoint. `_canonical_coverage` in `state.py` sums per-bucket counts across every bucket `resolve_all_buckets`
  returns, so the API-facing coverage number for `market-data-processing-service`/sports now includes these rows. Item 2
  (the operator/main routing note in this doc's § Recommended decision) is now fully resolved by this same commit — no
  separate follow-up needed.
