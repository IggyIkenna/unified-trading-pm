---
doc_type: issue
title: >-
  DEFI:onchain dependency-checker's required `perp_funding` MTDS dep is permanently unsatisfiable — every live
  perp_funding venue is CEFI-classified, not DeFi
summary: >-
  Root-caused the `collect-perp-funding` scheduler/manifest gap named in
  `data_pipeline_check_mdps_features_2026_07_20.md` and
  `issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md`. The Cloud Scheduler job and
  `perp_funding_handler.py` are NOT broken — they run daily and write real data + real manifest rows. The gap is that
  `features_service/onchain/app/core/dependency_checker.py::UPSTREAM_DEPS_DEFI`'s `market-tick-data-service-perp` entry
  checks the DEFI bucket (`market-data-tick-defi-prd-{project}`) for a `perp_funding` manifest row with `required:
  True`, but every currently-live perp_funding venue (HYPERLIQUID, KALSHI_PERP, POLYMARKET_PERP) is CEFI-classified per
  UAC's own `VENUE_TO_ASSET_GROUP` registry and 3 independent operator rulings (HYPERLIQUID DeFi->CeFi 2026-07-06;
  KALSHI_PERP/POLYMARKET_PERP fixed to the cefi write-path 2026-07-26; GMX — the last venue with any DeFi angle —
  removed entirely 2026-07-25). Every byte the job writes lands in `market-data-tick-cefi-prd-{project}` instead. This
  DEFI dependency can never be satisfied again under current (correct) venue classification — it is not a freshness gap,
  it is a stale check that predates the reclassifications.
status: resolved
nature: issue
asset_group: [defi, cefi]
stage: [data, features]
repos: [features-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [defi, cefi, onchain, mtds, dependency-checker, manifest, perp_funding, gate, stale-check]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/archive/issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md,
    /plans/archive/issues/cefi_perp_funding_kalshi_polymarket_residual_and_capture_gap_2026_07_30.md,
    /plans/active/issues/defi_hyperliquid_perp_funding_derivative_ticker_divergence_2026_07_28.md,
  ]
created: 2026-07-31
priority: P2
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
sequential: false
depends_on: []
drift_direction: advance-code
source:
  [
    "slot-15, data_engineering, 2026-07-31, dispatched via defi_satellite_ao_dispatch_batch6-013 ([DIAG] P1 root-cause
    the collect-perp-funding gap, source:
    issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md)",
  ]
resolved_by:
  features-service@eaaa935f, features-service@a0d4e6e4, unified-trading-library@b6714ed3, deployment-service@b301c41
locked_by:
locked_since:
---

> **✅ ARCHIVED 2026-08-01** — all 3 todos shipped (Option B bucket-fix + venue-scoped known-outage tolerance in
> `dependency_checker.py`, both live-verified against production; the stale terraform `"perp-funding"` op description
> corrected). 0 open todos, unlocked. Moved to `plans/archive/issues/`.

# DEFI:onchain `perp_funding` dependency is permanently unsatisfiable — stale post-reclassification check

## What I found

Live-verified today's `uts-prod-mtds-collect-perp-funding-cron` execution end-to-end (switched to `unified-trading-sa`
for `gcloud` reads after `github-actions-deploy` hit `PERMISSION_DENIED` on `cloudscheduler.jobs.get` — an
explicitly-excluded identity per `RULES.md` § 5, so escalated to the ambient `unified-trading-sa` identity rather than
self-granting `github-actions-deploy` more roles):

1. **The scheduler is healthy and firing on schedule.** `state: ENABLED`, `schedule: 15 1 * * *`,
   `lastAttemptTime: 2026-07-31T01:15:01Z`. The last 5 Cloud Run Job executions (2026-07-27 through 2026-07-31) all
   completed successfully (56s-2m34s each) — no silent failures, candidate (a) from the source issue doc ruled out.
2. **The handler writes real data and registers real manifest rows — just not where the dependency checker looks.**
   Today's execution log (`gcloud logging read`, `resource.labels.job_name="uts-prod-mtds-collect-perp-funding"`,
   2026-07-31T01:15-01:20Z):
   ```
   Hyperliquid: wrote 5568 funding rate rows for 2026-07-30 across 232 instrument shard(s) to
     gs://market-data-tick-cefi-prd-central-element-323112
   ManifestWriter: per-VM shard updated (1 total entries, 1 new, process_final=False) at
     market-data-tick-cefi-prd-central-element-323112/_index/per_vm/local-1-082f.parquet
   kalshi_perp: wrote 39 funding rate rows for 2026-07-30 across 13 instrument shard(s) to
     gs://market-data-tick-cefi-prd-central-element-323112
   polymarket_perp: BLOCKED-UPSTREAM-OUTAGE — perps-api.polymarket.com DNS NXDOMAIN (2026-06-21) -> attempted_failed
   ManifestWriter: per-VM shard updated (3 total entries, 2 new, process_final=True) at
     market-data-tick-cefi-prd-central-element-323112/_index/per_vm/local-1-082f.parquet
   Perp funding collection complete for 2026-07-30: 5607 records across 3 protocols
   ```
   Every write and every manifest registration targets `market-data-tick-cefi-prd-central-element-323112` — the CEFI
   bucket. Zero bytes land in `market-data-tick-defi-prd-central-element-323112`, the bucket
   `features_service/onchain/app/core/dependency_checker.py::UPSTREAM_DEPS_DEFI`'s `market-tick-data-service-perp` entry
   checks (`bucket_template: "market-data-tick-{asset_group_lower}-prd-{project_id}"` resolved with `asset_group=defi`,
   `data_type: "perp_funding"`, `required: True`). Candidate (b) from the source issue doc confirmed — but as a correct
   writer decision, not a registration bug.
3. **This is not a regression — it is the settled, operator-ruled state of venue classification.** Read
   `market_tick_data_service/cli/handlers/perp_funding_handler.py`'s module docstring directly:
   - HYPERLIQUID: "reclassified DeFi->CeFi 2026-07-06" (predates even the 2026-07-14 comment in `dependency_checker.py`
     that still claims these handlers write via `get_write_bucket_name("market_data", "defi")` — that comment was
     already stale the day it was written, for this one data_type).
   - KALSHI_PERP / POLYMARKET_PERP: "UAC's own registry classifies both `cefi`
     (`unified_api_contracts/registry/venue_constants.py` `VENUE_TO_ASSET_GROUP`). Fixed 2026-07-26
     (`defi_track01_per_instrument_and_canon_id_2026_07_24.md`): this handler now writes + records both venues via a
     cefi-classified path... instead of the DeFi-only `write_defi_rows`."
   - GMX (the one venue with a genuine on-chain angle): removed entirely 2026-07-25 — "its entire captured history was a
     synthetic OI-imbalance proxy, not real funding-rate observations."
   - dYdX: named in the `defi_collection_scheduler.tf` job description ("Hyperliquid + dYdX + GMX perpetual funding
     rates") but does not appear anywhere in `perp_funding_handler.py`'s live venue set (`hyperliquid`, `kalshi_perp`,
     `polymarket_perp`) — that terraform description is itself stale and should be corrected alongside the fix below.
   - The docstring also confirms the _only_ still-independent on-chain angle for HYPERLIQUID/ASTER (`derivative_ticker`,
     via `collect-onchain-perp-batch` / `onchain_perp_batch_handler.py`) ALSO writes with `asset_group="cefi"` hardcoded
     (`_ASSET_GROUP` constant, verified by direct read) — there is no live MTDS collector today that writes
     perp-funding-shaped data under `asset_group=defi` at all.
4. **This reconciles the original contradiction cleanly.** `data_completion_defi_2026_07_15.md`'s
   `perp_funding=12,500 captured` count is real, historical data that landed in the DEFI bucket BEFORE the 2026-07-06
   HYPERLIQUID reclassification (and before GMX's 2026-07-25 removal) — not a "since-broken code path" (source issue
   doc's candidate (c)), but a legitimate historical population that correctly stopped growing the moment the
   classification was corrected. The `UPSTREAM_DEPS_DEFI` entry was never updated to match.

## Why it matters

`DEFI:onchain`'s dependency check requires ALL 5 deps (`required: True` on all, per
`data_pipeline_check_mdps_features_2026_07_20.md` line ~762) — `perp_funding` being permanently unsatisfiable means
`DEFI:onchain`'s real-throughput measurement gate (the parent todo this was split off from) can **never** pass on any
future day either, not just the 12 tested ones. Every future picker-upper who re-runs the 12-day style sweep will
rediscover the identical zero and burn another session concluding "still broken" unless the dependency list itself is
corrected. This is a scoping/architecture question (does `DEFI:onchain` feature computation genuinely still need a
perp-funding signal, given the venues that used to supply it are now CEFI data?) rather than a pure mechanical bug —
flagging for the operator/main rather than unilaterally dropping a feature-readiness dependency, since it touches gating
behavior other in-flight plans reference.

## Recommended decision

Two non-exclusive options, either of which unblocks the gate:

- **(A) Remove `perp_funding` from `UPSTREAM_DEPS_DEFI`'s required set** (or the whole `market-tick-data-service-perp`
  entry) — the clean fix if DEFI:onchain feature computation does not actually need a perp-funding signal (CEFI's own
  perp_funding data type already exists for cross-asset-group features to consume if needed via the normal cross-service
  read path, not as a same-asset-group required dependency).
- **(B) Point the check at the CEFI bucket instead** (`asset_group=cefi` override for this one entry) — only correct if
  DEFI:onchain feature computation is SUPPOSED to consume perp_funding from HYPERLIQUID/KALSHI_PERP/POLYMARKET_PERP
  cross-asset-group (unusual for a same-`asset_group`-scoped dependency list, worth confirming intent before doing
  this).
- Either way: fix the stale terraform description (`deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s
  `"perp-funding"` operation still says "Hyperliquid + dYdX + GMX" — dYdX was never implemented here and GMX was removed
  2026-07-25) and the stale 2026-07-14 comment block in `dependency_checker.py` that still claims all 4
  on-chain-snapshot deps (including perp_funding) write via the DeFi bucket.

## Todos

- [x] [CODE] P2. ✅ Applied Option B (cross-asset-group intent CONFIRMED, not just presumed) —
      features-service@`eaaa935f`. `dependency_checker.py::UPSTREAM_DEPS_DEFI["market-tick-data-service-perp"]`'s
      `bucket_template` is now hardcoded to `market-data-tick-cefi-prd-{project_id}` (was templated off
      `{asset_group_lower}`, which resolved to the DEFI bucket no live perp_funding writer has touched since
      2026-07-06). Resolved the operator/main framing by finding a decisive fact rather than guessing: DEFI:onchain
      already has a REAL, wired consumer for this exact signal —
      `features_service/onchain/calculators/perp_funding_rates_defi.py::compute_defi_funding_rates` (the
      `perp_funding_rates` feature-group calculator, called from `orchestrator.py:772`) reads Hyperliquid ETH funding
      specifically — so DEFI:onchain genuinely IS supposed to consume perp_funding cross-asset-group from CEFI; Option B
      matches existing intent, Option A would have been the wrong call. That calculator's own bucket resolution
      (`_resolve_mtds_defi_perp_bucket()`) and its needle filter (`asset_group=defi/` → `asset_group=cefi/`, matching
      `perp_funding_handler.py`'s actual write path) had the SAME stale-bucket bug and are fixed in the same commit —
      fixing only `dependency_checker.py` would have made the gate pass while the actual feature stayed permanently
      empty, which is exactly the kind of gate-says-healthy-but-nothing-computes gap CLAUDE.md's data-pipeline-
      correctness rule exists to prevent. Test fixtures in `tests/onchain/unit/test_perp_funding_rates_defi.py` updated
      to match (`asset_group=defi/` → `asset_group=cefi/` in the 3 fixture blob paths). **Live-verified against
      production** (`unified-trading-sa`, `DependencyChecker(test_mode=False).check_dependencies`) across 2026-06-10,
      2026-06-15, 2026-07-25, 2026-07-27, 2026-07-28, 2026-07-29, 2026-07-30, 2026-07-31: the check now correctly finds
      REAL manifest rows on every day MTDS actually wrote (2026-07-27 through 2026-07-30 all show real row counts, e.g.
      "MTDS perp_funding: 3 manifest rows... 1 attempted_failed" on 2026-07-30) — before this fix it reported
      `no MTDS manifest ... has not run` on 100% of days, unconditionally, because it was checking a bucket that
      permanently receives zero perp_funding writes. **`DEFI:onchain`'s dependency check still cannot show
      `available=True` on any of the 8 tested days** — NOT because the bucket fix is wrong, but because
      `_check_mtds_manifest`'s "any attempted_failed shard fails the whole dependency" semantic combines with
      POLYMARKET_PERP's separate, DELIBERATE, already-tracked DNS outage
      (`issues/cefi_perp_funding_kalshi_polymarket_residual_and_capture_gap_2026_07_30.md`, ongoing since 2026-06-21) —
      even on days HYPERLIQUID + KALSHI_PERP both captured successfully. This is a genuinely different, newly-surfaced
      root cause outside this todo's original scope; filed as its own follow-up todo below rather than crammed into this
      fix. `data_pipeline_check_mdps_features_2026_07_20.md`'s gating todo (line ~752) updated to reflect both facts
      (bucket-resolution bug fixed + verified; residual gate-never-passes symptom has a different, tracked cause).
- [x] [CODE] P2. ✅ **New, scoped from the P2 fix above's live-verification finding.** Decided + implemented a targeted
      fourth option, not literally (a)/(b)/(c) as originally framed but closest to (a) made venue-scoped rather than
      blanket: `_check_mtds_manifest` now excludes ONLY POLYMARKET-PERP's own `attempted_failed` rows from the pass/fail
      decision for `market-tick-data-service-perp` (svc-scoped via a new `_KNOWN_OUTAGE_VENUES_BY_SVC` constant), while
      staying fully sensitive to a failure on HYPERLIQUID or KALSHI-PERP — features-service@`a0d4e6e4` (+ a
      `venue`-column projection fix in `read_manifest_rows` that the check depends on —
      unified-trading-library@`b6714ed3`). Rejected (a) as literally described (blanket "≥1 non-failed row passes")
      because it would mask a genuine multi-venue outage as healthy, exactly the risk the todo flagged; rejected (b)
      (dropping POLYMARKET_PERP from `DEFAULT_PROTOCOLS`) because `perp_funding_handler.py`'s own docstring frames its
      daily collection attempt as a deliberate scaffold ("BLOCKED-UPSTREAM-OUTAGE ... activates when endpoint resolves")
      — removing it from collection would silence that auto-recovery signal, the opposite of the established pattern
      here; rejected (c) (accept permanently blocked) because it leaves the gate permanently RED for a known,
      already-tracked, non-actionable cause, contradicting the reason this whole issue doc exists (unblock a
      permanently-unsatisfiable dependency). 4 new unit tests added
      (`tests/onchain/unit/test_dependency_checker_known_outage_tolerance.py`): POLYMARKET-PERP-alone failure passes, a
      HYPERLIQUID failure still fails (tolerance is venue-scoped, not blanket), all-POLYMARKET-PERP-rows-only still
      fails (no false-healthy from excluding everything), and the tolerance doesn't leak to an unrelated MTDS dep.
      **Live-verified against production** (`unified-trading-sa`,
      `DependencyChecker(test_mode=False).check_dependencies`, project `central-element-323112`) across
      2026-07-27..2026-07-31: `available=True` on 2026-07-29 and 2026-07-30 with message
      `"... (1 known-outage rows on ['POLYMARKET-PERP'] excluded)"` — confirming the gate now passes exactly as designed
      on days HYPERLIQUID/KALSHI-PERP both captured; `available=False` on 2026-07-27/07-28 due to non-Polymarket
      `attempted_failed` shards (3 and 1 respectively — a genuinely different, real failure the tolerance correctly does
      NOT mask) and on 2026-07-31 (no manifest row at all yet, MTDS hadn't run for that date as of this check) —
      done_definition's demonstrable-real-day-pass bar is met. The 07-27/07-28 non-Polymarket failures are a separate,
      unscoped finding — not folded into this fix; worth a follow-up root-cause if it recurs, but out of scope here
      since this todo's job was the outage-tolerance mechanism, not auditing every historical failure day.
- [x] [DOCS] P3. ✅ Fixed `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s `"perp-funding"` operation
      description — deployment-service@`b301c41`. Corrected both the header stagger-table comment (line ~59) and the
      per-op `description` field (line ~150) from the stale "Hyperliquid + dYdX + GMX perpetual funding rates" to the
      real live venue set (Hyperliquid + Kalshi-Perp + Polymarket-Perp), noting dYdX was never implemented in
      `perp_funding_handler.py` and GMX was removed 2026-07-25. `terraform fmt -check` clean; QG green
      (`.qg_last_passed_sha=b301c41`). This closes the last open todo in this issue doc.

## Progress Log

- **2026-07-31 (slot-15, data_engineering)**: Filed after root-causing `defi_satellite_ao_dispatch_batch6-013` ([DIAG]
  P1, source: `issues/features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md`'s P2 follow-up todo).
  Live evidence gathered via `gcloud scheduler jobs describe` / `gcloud run jobs executions list` /
  `gcloud logging read` (switched from `github-actions-deploy` to `unified-trading-sa` for the GCP reads after a
  `PERMISSION_DENIED` — `github-actions-deploy` is an explicitly-excluded identity per `RULES.md` § 5, escalated to the
  ambient `unified-trading-sa` identity rather than self-granting) + direct source reads of `perp_funding_handler.py`,
  `onchain_perp_batch_handler.py`, and `dependency_checker.py`. Root cause is fully evidenced: the scheduler/handler are
  healthy and correct; the DEFI:onchain dependency check itself is stale post-reclassification. Filed as a scoped
  follow-up per this task's own done_definition rather than unilaterally editing a cross-plan gating dependency.
- **2026-08-01 (slot-12)**: Applied Option B — see the flipped P2 todo above for the full evidence chain (cross-
  asset-group intent confirmed via `perp_funding_rates_defi.py`'s real wired consumer, not guessed; both the dependency
  check AND the calculator's stale DEFI-bucket resolution fixed in the same commit; live-verified against production
  across 8 days). Discovered a second, genuinely separate blocker while live-verifying (POLYMARKET_PERP's deliberate DNS
  outage + `_check_mtds_manifest`'s all-or-nothing failure semantic) — filed as its own new P2 todo rather than folding
  into this fix, since it needs its own operator/main call on 3 real options. Also updated
  `data_pipeline_check_mdps_features_2026_07_20.md`'s gating todo (line ~752) to reflect both facts.
- **2026-08-01 (slot-10)**: Closed the follow-up P2 todo — see the flipped item above for the full decision rationale
  and live-verification evidence. Shipped `unified-trading-library@b6714ed3` (adds `venue` to `read_manifest_rows`'s
  column projection) + `features-service@a0d4e6e4` (venue-scoped known-outage tolerance in `_check_mtds_manifest`,
  extracted via a module-level `_evaluate_manifest_rows`/`_exclude_known_outage_rows` pair to stay under the 50-line
  class-method cap; 4 new unit tests). Both QG-green, both verified on `origin/live-defi-rollout`. This closes every
  open todo in this issue doc except the P3 terraform-description fix.
- **2026-08-01 (slot-4)**: Closed the last open todo — fixed
  `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s stale `"perp-funding"` operation description (both
  the header stagger-table comment and the per-op `description` field still said "Hyperliquid + dYdX + GMX"; corrected
  to the real live venue set Hyperliquid + Kalshi-Perp + Polymarket-Perp, noting dYdX was never implemented and GMX was
  removed 2026-07-25) — `deployment-service@b301c41`, `terraform fmt -check` clean, QG green, verified on
  `origin/live-defi-rollout`. All 3 todos now `[x]`, unlocked — archiving per the
  plan-completion-and-archival-discipline HARD RULE (6-step ritual: no deferred prose to migrate; archived-banner +
  `status: resolved` + `resolved_by` added above; no codex contract changed by this doc's closure — the
  dependency-checker fix's contract already lives in `features_service/onchain/app/core/dependency_checker.py` itself,
  not a codex doc; referrers in `defi_satellite_ao_dispatch_batch6_2026_07_30.md`,
  `data_pipeline_check_mdps_features_2026_07_20.md`, and the already-archived
  `features_defi_onchain_mtds_ingestion_claim_needs_reverify_2026_07_29.md` all cite this doc's PATH only — no
  standalone fact/number needing pre-archive migration — repointed to the new archive path in the same commit).
