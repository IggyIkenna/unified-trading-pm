---
doc_type: issue
title:
  "gas-fees manifest/data-status scanner reads an empty bucket the writer never populates — likely under-reporting real
  gas-fees coverage; lst-rates has a matching reader/writer split"
summary:
  "Surfaced as a side effect of the 2026-07-10 GCS bucket estate audit ([[gcs_bucket_estate_cleanup_2026_07_10]]):
  gas_fee_handler.py (market-tick-data-service) writes gas-fees rows into the shared market-data-tick-defi-prd bucket
  (via get_write_bucket_name('market_data','defi')), but data_manifest_handler.py's data-status/coverage scan resolves
  kind='gas-fees' — a DIFFERENT, dedicated bucket (gas-fees-{env}-{project_id}) that the writer never touches. The
  dedicated bucket is confirmed empty. If the manifest/data-status layer is genuinely reading that bucket for gas-fees
  coverage reporting, it would show 0% coverage for real, present data. lst-rates has the identical writer-vs-kind split
  (writer uses market-data bucket; an e2e reader script uses kind='lst-rates'). Neither the writer's real target bucket
  nor the reader's expected bucket were changed by this doc — root-caused only, not fixed, since the correct fix depends
  on which side (manifest scanner target, or writer's actual write path) reflects the intended DeFi reference-data
  manifest architecture, which needs a read of manifest-consolidator-ssot.md + operator/codeowner input before choosing
  a direction."
status: open
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-trading-library, e2e-testing]
scope: [engineer, admin]
tags: [gcs, manifest, data-status, gas-fees, lst-rates, data-pipeline-correctness, bucket-mismatch]
related: [/plans/archive/2026_07/gcs_bucket_estate_cleanup_2026_07_10.md]
created: "2026-07-10"
parent_epic: infrastructure_master
priority: P1
source:
  "Discovered during the 2026-07-10 GCS bucket estate audit/cleanup — a parallel research agent tracing why
  gas-fees-{env}-{project_id} and 7 sibling DeFi reference-data buckets were empty found the writer/manifest-scanner
  bucket mismatch while confirming the buckets were safe to delete."
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
assigned_vm:
resolved_by:
---

# gas-fees manifest/data-status scanner reads an empty bucket the writer never populates

## What was found

While auditing which GCS buckets in `central-element-323112` are actually used by live code (full estate cleanup, see
[[gcs_bucket_estate_cleanup_2026_07_10]]), a parallel research pass traced 9 of 11 DeFi reference-data "kinds" declared
in `deployment-service/configs/cloud-providers.yaml` (`dex-pools`, `dex-swaps`, `evm-defi`, `solana-defi`,
`lending-indices`, `lst-rates`, `oracle-prices`, `gas-fees`, `liquidations`) and found that **their writers never
resolve their own declared bucket kind** — real data for all of them lands in the shared
`market-data-tick-defi-{env}-{project_id}` bucket instead, via
`get_write_bucket_name("market_data", asset_group="defi")`. For 7 of the 9 this is just orphaned storage (the dedicated
bucket + its own env-tiered variants sit empty, safe to delete, and were deleted as part of the cleanup). **Two of the
nine are not just orphaned storage — they're an actual reader/writer split that could be causing a live
incorrect-coverage-reporting bug:**

### gas-fees

- **Writer**: `market-tick-data-service/market_tick_data_service/.../gas_fee_handler.py:419,757,842` — writes rows via
  `get_write_bucket_name("market_data", asset_group="defi")`, i.e. into `market-data-tick-defi-{env}-{project_id}`.
- **Manifest/data-status scanner**: `market-tick-data-service/.../data_manifest_handler.py:215` — resolves
  `resolve_bucket_name(kind="gas-fees", asset_group="defi")`, i.e. `gas-fees-{env}-{project_id}` — **a different bucket
  the writer never touches.**
- **Confirmed empty**: `gas-fees-prd-central-element-323112` and `gas-fees-test-central-element-323112` (both had 0
  objects on a full shallow listing, deleted as part of this cleanup). The flat `gas-fees-central-element-323112` had
  legacy data (a pre-migration artifact, NOT deleted — see the parent cleanup plan's "orphaned but has data" list) but
  is not what the current manifest scanner path resolves to either (it resolves the env-tiered form).

**If `data_manifest_handler.py`'s gas-fees scan is genuinely wired into a live data-status/coverage-reporting surface
(deployment-ui, deployment-api `/data-status`, an honest-coverage report, etc.), it would report 0% / RED coverage for
gas-fees data that is actually present and captured — just in the wrong bucket from the scanner's perspective.** This
wasn't verified end-to-end (out of scope for the bucket-cleanup pass that found it) — the next step is confirming
whether this scanner path is actually invoked by a live coverage report, and if so, what it's currently showing.

### lst-rates

Same structural split, one-sided verification only:

- **Writer**: `market-tick-data-service/.../lst_rates_handler.py:311,355,381,429` — also writes via
  `get_write_bucket_name("market_data", asset_group="defi")`.
- **Reader**: `e2e-testing/scripts/defi/staked_basis_funding_scan.py:198` — reads via `kind="lst-rates"` (the dedicated
  `lst-rates-{env}-{project_id}` bucket).
- The dedicated bucket's env-tiered form was confirmed empty and deleted. This e2e script — if actually run — would be
  reading stale/nonexistent data instead of the real lst-rates history that lives in the market-data bucket.

## Why this wasn't fixed here

Two structurally different fixes are possible and the correct one depends on the intended DeFi reference-data manifest
architecture (not established during the bucket-cleanup pass):

1. **Point the readers (manifest scanner, e2e script) at the market-data bucket** — i.e. accept that
   `gas-fees`/`lst-rates` were never meant to be their own manifest-tracked "kind"; they're properly a slice of the
   `market-data` asset_group=defi corpus, and the dedicated bucket-kind declarations in `cloud-providers.yaml` /
   `bucket_config.yaml` are themselves stale (matching the pattern of the other 7 confirmed-dead DeFi kinds in this same
   family).
2. **Make the writer dual-write** (or point it at the dedicated bucket instead of market-data) — i.e. the dedicated
   `gas-fees`/`lst-rates` bucket kind is the INTENDED manifest-tracked unit, and the writer's current behavior (writing
   into the shared market-data bucket) is itself the bug.

Choosing between these requires reading `/codex/05-infrastructure/manifest-consolidator-ssot.md` and understanding
whether DeFi reference-data types are meant to have their own per-kind manifest, or whether they're deliberately folded
into the `market-data` asset_group=defi manifest (in which case `gas-fees`/`lst-rates`/the other 7 dead kinds'
`cloud-providers.yaml` declarations should probably be removed entirely, not just have their empty buckets deleted).

## Recommended next step

Read the manifest-consolidator SSOT + check whether `data_manifest_handler.py`'s gas-fees scan actually feeds a live
coverage report today (grep deployment-api/deployment-ui for a gas-fees-specific coverage display, or check if the
honest-coverage model even surfaces gas-fees separately from market-data). If it does and is currently reporting
false-RED/0% coverage, that's an active user-facing bug worth its own fix plan. If it's dead/unused code entirely
(possible, given the same family's other 7 kinds turned out to be fully orphaned), the fix may simply be deleting the
`gas-fees`/`lst-rates` kind resolution calls in `data_manifest_handler.py` and the e2e script, consistent with folding
DeFi reference data fully into the `market-data` manifest.

## Resolution (2026-07-12) — gas-fees + lst-rates production scanner fixed; e2e script still pending

Operator direction: option 1 (point the readers at the market-data bucket) — confirmed correct AND necessary once
verified end-to-end.

**`data_manifest_handler.py` fixed** (both gas-fees and lst-rates) — `market-tick-data-service@8b730664`. Turned out the
fix needed to be more than "just point at the shared bucket": gas-fees/lst-rates captures span MULTIPLE venues per
data_type (gas_fees: ALCHEMY/LIDO/ETHERFI; lst_rates: AAVE_V3/COMPOUND_V3/BALANCER/LIDO/UNISWAP_V3/...), and `data_type`
lives only as a parquet COLUMN, never as a distinguishing GCS path segment — raw blob-path listing (pointed at the
shared bucket or not) genuinely cannot isolate them. Implemented `_scan_via_availability_index(data_type, description)`,
which reads the canonical availability index (`unified_trading_library.read_availability_index()`) and filters by the
real `data_type` column instead. Verified directly against production: the canonical index holds 49,575 real gas_fees
rows and 222,836 real lst_rates rows (back to 2018-01-01) — this data was ALWAYS there, just invisible to both the old
(dead-bucket) and an initially considered (shared-bucket-but-still-raw-listing) fix. Full write-up + the collision-risk
investigation that shaped the fix direction: [[eigenlayer_manifest_availability_index_collision_2026_07_12]].

**`e2e-testing/scripts/defi/staked_basis_funding_scan.py`'s `_lst_bucket()` reader — NOT fixed, still open.** It still
resolves `kind="lst-rates"` (the dead, deleted dedicated bucket) and expects a prefix shape
(`day={day}/asset_group=defi/venue={protocol}/chain={chain}/instrument_type=lst/data_type=lst_rates/`) that doesn't
match what was actually found in the shared bucket during this investigation
(`raw_tick_data/by_date/day={date}/pipeline_mode={mode}/asset_group=defi/venue={VENUE}/...`, no `chain=`/
`instrument_type=`/`data_type=` path segments observed at the depth explored). This script's assumed layout was NOT
verified against real production paths before this issue closes — needs its own investigation before touching it, since
guessing wrong here risks silently returning `None` (no exchange rate found) instead of a loud error, exactly the
"silent placeholder" anti-pattern the workspace rules ban. Lower urgency than the production handler (this is a
research/e2e script, not a live coverage report), but still open.

## Status

`data_manifest_handler.py` side: **resolved** 2026-07-12, shipped + verified against real production data.
`staked_basis_funding_scan.py` side: **still open** — flagged above, needs its own path-structure verification before a
safe fix.
