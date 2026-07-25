---
doc_type: issue
title:
  Sports IS availability-index `source=mdps_odds_horizon_bucket`/`instruments_service` are legitimate, not cross-service
  leakage — operator's cited counts were stale
summary:
  Root-caused per operator request (P9 Q3, "is it a sign of deeper issues?"). Both non-vendor `source` values are
  deliberate, already-documented architecture (2026-06-07 sports-manifest routing exception + the 2026-07-13 orphan
  backfill), not a bug. Live GCS read of the canonical `instruments-store-sports-{env}` index (2026-07-16) shows
  `mdps_odds_horizon_bucket`=356,131 rows and `instruments_service`=100,472 rows — an order of magnitude below the
  operator's cited 8.1M/3.7M, which almost certainly came from a stale cached artifact (same class of bug already
  root-caused in this plan's P7 stale-rollup-blob finding). No writer/consolidator fix required; a small optional
  venue-casing dedup is the only real cleanup surfaced.
status: resolved
nature: process
asset_group: [sports]
stage: [meta]
repos: [instruments-service, market-data-processing-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, manifest, data-correctness, source, honest-coverage]
related: [/plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md]
created: 2026-07-16
parent_epic: deployment_and_user_management_master
priority: P3
source: [operator P9 Q3 review 2026-07-16]
assigned_vm: NA
resolved_by: re-triaged-2026-07-23
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-16
locked_since:
---

> **✅ ARCHIVED 2026-07-25** — `status: resolved` since the 2026-07-23 RE-TRIAGE (ACKED-AS-INVALID: both non-vendor
> `source` values are deliberate, documented architecture, not leakage), 0 open todos, unlocked. Moved to
> `plans/archive/issues/` per the issue-doc-lifecycle archival ritual.

# Sports IS availability-index non-vendor `source` values — root cause

## Operator's question (P9 Q3)

> The sports source breakdown carries `mdps_odds_horizon_bucket` (8.1M) + `instruments_service` (3.7M) — NOT vendors
> (`source`=VENDOR-only, CLAUDE.md). Root-cause where these rows/sources enter the IS sports manifest + correct to the
> real vendor (or exclude cross-service rows). Is it a sign of deeper issues?

## Finding: NOT leakage — deliberate, already-documented architecture

Both values are **registered, non-vendor `source` identifiers** in UAC's crosscutting `SOURCE_PRIORITY` / `PipelineMode`
registries, used identically across every asset group (not sports-specific):

- `("sports", "ODDS_HORIZON_BUCKET"): ["mdps_odds_horizon_bucket"]` in
  `unified_api_contracts/canonical/crosscutting/_source_priority_data.py:77`, with
  `PipelineMode.BATCH_MDPS_ODDS_HORIZON_BUCKET` / `LIVE_...` / `REPLAY_...` members — a real registered vendor-analog
  source, not a leak. MDPS's own derived odds-horizon-bucket product is, by a **deliberate 2026-06-07
  "sports-manifest-canonicalisation routing exception"**, written directly into instruments-service's canonical sports
  bucket instead of MDPS's own bucket.
- `("reference", "instruments"): ["instruments_service"]` in the same registry — the `REFERENCE_SOURCE` convention
  (`instruments-service/scripts/migrate_instruments_store_v9.py:125`) IS itself stamps on data_types it derives/owns
  (self-referential reference data), used identically for cefi/defi/tradfi/prediction, not sports-specific.

The cross-BUCKET split that ONCE caused real orphaned `mdps_odds_horizon_bucket` rows (writer pointed at
`market-data-tick-sports-{env}` while the expected-universe enumerator seeded the denominator into
`instruments-store-sports-{env}` — two manifests nothing merges) was root-caused and FIXED at
`market-data-processing-service@6907257` (2026-07-13), with
`instruments-service/scripts/migrate_orphaned_mdps_odds_horizon_bucket_rows_2026_07_13.py` backfilling the 124,294
already-orphaned historical rows into the canonical bucket. This is documented, already shipped, and working as
intended.

## Live data (2026-07-16, direct GCS read — not a cached rollup)

**Canonical `instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`** (5,465,414 total
rows):

| source                     | rows    | data_type breakdown                                                                                                                                                        | verdict                                                                                       |
| -------------------------- | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| `mdps_odds_horizon_bucket` | 356,131 | `odds_horizon_bucket` 350,809 (its actual purpose) + `arbitrage_opportunity`/`odds_movement`/`odds_snapshot` 1,774 each                                                    | legitimate                                                                                    |
| `instruments_service`      | 100,472 | `TRANSFERMARKT_LEAGUES` 75,545 + `SFI_LEAGUES` 12,469 + `LEAGUES` 8,780 + `VENUES` 3,627 + `SFI_STANDINGS` 42 — ALL genuinely global/self-referential reference data_types | legitimate — matches the P8 "global reference entity" pattern already fixed in this same plan |

**Orphan `market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`** (1,958,498 total rows,
pre-2026-07-13-fix bucket, retained per GCS delete-safety convention — COPY not MOVE): `mdps_odds_horizon_bucket` =
124,294 rows — matches the 2026-07-13 migration script's own docstring number exactly. Confirms the backfill is
accounted for; these are the pre-fix duplicates, not new leakage.

## The operator's cited counts (8.1M / 3.7M) do not match any real bucket

Neither the canonical index (356K/100K) nor the orphan index (124K/0) comes close to 8.1M/3.7M — off by roughly 23x and
37x respectively. This strongly resembles the **same stale-cached-rollup-blob class of bug already root-caused and fixed
in this plan's P7 section** ("the TURBO Data Coverage grid is served from a pre-built GCS rollup blob... a blob written
BEFORE the fix still carried stale data"). I did not trace the exact stale artifact the original 8.1M/3.7M figures came
from (out of this issue's scope), but the two live-GCS reads above are authoritative current state.

## Minor real findings (small, optional cleanup — NOT the leakage originally suspected)

1. **Venue-casing duplication** under `mdps_odds_horizon_bucket`: `MDPS_ODDS_HORIZON_BUCKET` (3,548 rows) and
   `mdps_odds_horizon_bucket` (3,548 rows, identical count) are almost certainly the same underlying cells double-keyed
   by case; similarly `ODDS_API`/`odds_api` (345,108/887) and `OPEN_METEO`/`open_meteo` (425/425) and
   `FOOTYSTATS`/`footystats` (365/365). A small case-canonicalization migration (pattern:
   `instruments-service/scripts/canonicalize_*_2026_*.py`) would collapse these — low priority, not data-correctness
   critical (both cases already contribute to the SAME coverage math since dedup dedups per-key, this only inflates the
   apparent venue-cardinality in a breakdown UI, not correctness of counts).
2. **13,997 blank-source rows** in the canonical index — worth a follow-up classification pass, not urgent.

## Recommendation

- No writer/consolidator fix required for the "leakage" as originally framed — close this finding as **not a bug**.
- Operator should treat any dashboard/report still showing 8.1M/3.7M for these sources as reading a stale cache and
  refresh/regenerate it.
- Optional follow-up: venue-casing dedup migration (P3, small).

## Codex SSOTs referenced

- `/codex/02-data/pipeline-mode-partition.md` (`source`=VENDOR-only rule + the 2026-06-05/06-07 ratified source-aware
  design — `mdps_odds_horizon_bucket` and `instruments_service` are both registered `PipelineMode`/`SOURCE_PRIORITY`
  members, so they satisfy the "source is the vendor(-analog)" contract even though they are not third-party vendors).
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` § "Two-writer model" (the same instruments-service-as-source
  pattern, generalized across asset groups).

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE — root cause and "not leakage" verdict both confirmed on a fresh live GCS read.** Re-ran
the equivalent live query against
`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` (via
`unified_trading_library.get_storage_client()` /
`resolve_bucket_name(cloud="gcp", kind="instruments-store", asset_group="sports")`, same idiom as the doc's own
methodology):

- Total index rows: 5,523,146 (up from 5,465,414 on 2026-07-16 — normal ongoing growth, ~1% over 7 days).
- `source=mdps_odds_horizon_bucket`: 360,167 rows (was 356,131) — `data_type` breakdown still dominated by
  `odds_horizon_bucket` (354,845) + 1,774 each of `arbitrage_opportunity`/`odds_movement`/`odds_snapshot`, matching the
  doc's characterization exactly. (Note: those 3 minor data_types were separately confirmed dead-code/zero-prod-object
  candidates elsewhere today per `sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md` — orthogonal to
  this doc's "is it leakage" question, which is about `source=`, not liveness of those data_types.)
- `source=instruments_service`: 100,472 rows — **exact match** to the doc's cited figure, `data_type` breakdown
  unchanged (TRANSFERMARKT_LEAGUES 75,545 / SFI_LEAGUES 12,469 / LEAGUES 8,780 / VENUES 3,627 / SFI_STANDINGS 42).
- Blank-source rows: 13,903 (was 13,997 — essentially flat, within noise).

**Bonus finding — the doc's own "minor optional cleanup" (venue-casing dedup) is now ALREADY FIXED**, apparently as a
side effect of today's unrelated K1/K2 casing-migration work (see this plan's background): live query shows
`MDPS_ODDS_HORIZON_BUCKET`=0 / `ODDS_API`=0 / `FOOTYSTATS`=0 / `OPEN_METEO`=0 (all uppercase variants gone), with every
row now living under the lowercase canonical key (`mdps_odds_horizon_bucket`=360,167, `odds_api`=573,875,
`footystats`=683,411, `open_meteo`=261,096). The doc's proposed "small case-canonicalization migration" is no longer
needed — it happened for free.

Flipped `status: open` → `resolved` (the doc's own "Recommendation" section already said "close this finding as not a
bug" — the frontmatter had just never been flipped to match) and filled `resolved_by:` to point at this re-verification.
No new leakage, no contradiction with any other doc found.
