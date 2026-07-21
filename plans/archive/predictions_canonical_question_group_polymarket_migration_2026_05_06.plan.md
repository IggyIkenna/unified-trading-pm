---
doc_type: plan
title: Predictions Canonical-Question-Group SSOT + Polymarket Migration + Lifecycle Timing — Plan
summary:
status: drafted
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-ui,
    execution-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-06
type: plan
locked_by: live-defi-rollout
locked_since: 2026-05-06
parent_plan: writegate_honest_coverage_endtoend_2026_05_06.plan.md
companion_handover: shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md
---

## Deferred work — migrated to: `plans/active/data_completion_prediction_2026_07_15.md`,

`plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md` — successor:
data_completion_prediction_2026_07_15, predictions_other_bucket_and_ui_drilldown_2026_06_20 (the instruments-service
lifecycle + MTDS adapter + manifest-canonicalisation clusters route through `plans/epics/predictions_master.md`'s
"Workstream routing" table to the first plan (the prediction slice split from M-1 2026-07-15); the deployment-api/
deployment-ui panel cluster routes to the second plan, which still carries the live remainder (3 open items). The
features/strategy reader-migration + lookahead + e2e-smoke cluster already shipped, archived complete at
`plans/archive/2026_07/predictions_lookahead_and_reader_migration_2026_06_20.md`. Two Phase-5 integration-test items
(cluster-validation + lifecycle-gating tests) are AMBIGUOUS — no direct evidence found either way, recommend an operator
spot-check of the `market-tick-data-service` test suite rather than a blind close. NOTE: `locked_by: live-defi-rollout`
was never cleared at archival — flagged for operator `[unlock-plan]` cleanup.)

# Predictions Canonical-Question-Group SSOT + Polymarket Migration + Lifecycle Timing — Plan

**Branch:** `live-defi-rollout` **Goal:** Build the UAC `canonical_question_group` SSOT for prediction markets; capture
per-market lifecycle timestamps (`market_created_at`, `resolution_time`, `settlement_time`) in instruments-service;
migrate Polymarket from `data_type=<base_asset>` (BTC/ETH/SPX/FOOTBALL/OTHER) to the canonical shard atom
`(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` with
per-market_id bundles; populate the `PREDICTION_GROUPS` cluster registry that writegate-honest-coverage reserved as an
empty slot.

This plan resolves writegate-honest-coverage Tracked Open Questions §1 (canonical_question_group SSOT) + §10 (Polymarket
shard-key sequencing) + the migration run-status item for residual `category=prediction` GCS objects.

---

## Workflow note for the executing agent

**Direct git workflow, NOT quickmerge.** Confirmed by user 2026-05-06: `bash scripts/quality-gates.sh` per-repo on the
touched files, then `git add` + `git commit` + `git push origin live-defi-rollout` directly. Skip `quickmerge`.
Reasoning: multi-week multi-repo plan; quickmerge per commit is friction without benefit.

**Before every commit + push:** `git fetch origin` → list incoming commits with
`git log HEAD..origin/live-defi-rollout --pretty='%h %ae %s'` → for each incoming commit decide: compatible (rebase +
continue) / touches plan files (read diff, adapt or flag) / direct conflict (DO NOT revert silently — flag back to user
with hash + author + file:line + summary, pause that file, continue on unaffected files). After push, re-check for
race-incoming commits.

**Concurrent-stream awareness**: writegate-honest-coverage plan + sports phantom recovery stream are running in
parallel. Predictions work overlaps writegate's `BUNDLED_DATA_TYPES` reservation but uses an independent registry slot.
Coordinate with the agent executing writegate plan if both modify UAC `honest_coverage.py` simultaneously.

**Workspace concurrency rule (CLAUDE.md `§ Per-VM shard isolation`)**: Phase 3 reconciler VMs each set
`VM_NAME=<unique>` + `MANIFEST_PER_VM_SHARDS=true`.

---

## Why this plan exists

The current Polymarket adapter (per audit 2026-05-06) shards at `data_type=<base_asset>` — BTC, ETH, FOOTBALL, OTHER.
That's 5 buckets across thousands of underlying markets, with per-market identity collapsed at write-time. Three
concrete failure modes:

1. **Cluster validation cannot fire** — without per-canonical-group axes, there's no shard-level "expected market_ids
   per day" to validate. `attempted_failed[reason=ClusterCoverageError]` is impossible.
2. **Lifecycle is invisible** — Polymarket markets have lifecycle (`market_created_at` → `resolution_time` →
   `settlement_time`). Capturing CLOB data for a market AFTER it settled is wasteful AND introduces look-ahead bias if a
   feature consumes post-settlement ticks. The current shard atom carries no lifecycle, so MTDS captures whatever the
   venue WS emits including post-resolution data.
3. **LookaheadBiasError cannot enforce per-market** — a feature at time T should only consume ticks from markets with
   `market_created_at <= T`. Without per-market axes in the manifest + parquet, the enforcer can't tell.

Plus the writegate-honest-coverage plan reserved `prediction_canonical_question_group` in `BUNDLED_DATA_TYPES` with
`PREDICTION_GROUPS = {}` empty registry as a documented temporary state pointing to this plan as its named successor.
Until this plan lands, any caller using that data_type fails the cluster guard — feature, not bug, since the SSOT
doesn't exist yet.

---

## Cross-cutting principles binding this plan

Per workspace CLAUDE.md (codified 2026-05-06):

1. **Live = batch — same data, same fields, same timing semantics, different sources OK.** Live prediction capture and
   historical replay both produce identical schemas; differ only in source (Polymarket WS for live; Polymarket REST
   historical archive for replay).
2. **No double SSOT in data-saving methodology.** One canonical_question_group registry in UAC; all consumers
   (instruments-service, MTDS, features-prediction, strategy-service) import from there.
3. **Cluster validation MANDATORY at `record_captured` for bundled shards.** Per-canonical_question_group expected
   market_ids enforced at write time.
4. **`available_at` is per-row, write-time, equal to live-pipeline-arrival.** Each CLOB tick stamps
   `available_at = tick_timestamp + scrape_latency`. Each market metadata row stamps `available_at = market_created_at`
   (we couldn't have known about the market before it was listed).
5. **Prediction market lifecycle timing — instrument definitions capture `market_created_at` / `resolution_time` /
   `settlement_time`.** MTDS respects lifecycle bounds (no capture before created, no new capture after settlement).
6. **Schema, manifest, GCS, code rewrites sanctioned where the SSOT requires.** No compat shims. Per-base_asset
   Polymarket parquets get migrated, not preserved.
7. **>99% backfill means real >99%.** Honest empty when source had no markets resolving on a date; honest failed when
   classifier confidence below threshold; never silent placeholder.
8. **Temporary state must have named successor plan** — none deferred from this plan; it ships the full shape.

---

## Pre-audit blast radius

### instruments-service

| File / surface                                                                        | Concern                                                                                                                                                                                                                                                                                  |
| ------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `engine/orchestrator.py:1990–1995`                                                    | POLYMARKET writer currently sets `data_type = <base_asset>`. Migration target: `data_type="prediction_canonical_question_group"`, `instrument_id=<canonical_group_name>`, `metadata.market_id=<conditionId>`, `metadata.lifecycle={market_created_at, resolution_time, settlement_time}` |
| `engine/orchestrator.py:2497–2524`                                                    | `_extract_prediction_shard` / `_compute_prediction_shards` — currently extracts shard by base-asset keyword matching. Replace with `unified_api_contracts.predictions.classify_market_to_canonical_group(market_metadata) -> CanonicalQuestionGroup`.                                    |
| `engine/orchestrator.py:4099–4147`                                                    | `_validate_predictions_null_rates` (FootyStats-only inline NaN gate). Tagged for Plan B lift; out of scope here, but flag if behaviour changes for predictions specifically.                                                                                                             |
| `engine/orchestrator.py:4980`                                                         | "ManifestWriter v5" stale comment — unrelated, fix in writegate plan.                                                                                                                                                                                                                    |
| `polymarket_adapter.py` (or wherever the source classifier lives — verify in Phase 0) | Word-boundary crypto-keyword regex (commits `b336834`, `d7bd17f`) is the seed for the new classifier. Lift to UAC + extend with stability hash.                                                                                                                                          |

### unified-api-contracts (UAC)

| Surface | New / changed | |
--------------------------------------------------------------------------------------------------------------- |
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| --------------------------------------------------------------------- | |
`unified_api_contracts/predictions/__init__.py` (new module) | Public facade: `CanonicalQuestionGroup`,
`classify_market_to_canonical_group()`, `lifecycle_for_market()`, `expected_market_ids_for_canonical_group()`,
`is_market_active_at()`. | | `unified_api_contracts/canonical/domain/predictions/canonical_groups.py` (new) |
`CanonicalQuestionGroup` enum + `CANONICAL_GROUP_METADATA` registry (cadence, expected_active_count, resolution_basis).
| | `unified_api_contracts/canonical/domain/predictions/classifiers.py` (**ALREADY SHIPPED — wraps internal SSOT**) |
Verified 2026-05-06: file exists, exported via `unified_api_contracts/predictions/__init__.py:37`. Per **Citadel Import
Rules** facade pattern (CLAUDE.md "UAC Citadel Architecture"): the canonical-facade `classifiers.py` re-exports from
internal SSOT `unified_api_contracts/internal/schemas/_prediction_market_taxonomy.py` (130-entry rule set, 78 tests, 13+
direct callers including `internal/schemas/contracts.py` 5 imports). NOT duplication — this IS the architecture. Plan
work is bug-fix + canonical_question_group naming wired through the existing internal taxonomy, NOT creating new
modules. |
None`; word-boundary regex + token rules + classifier stability hash. | | `unified_api_contracts/canonical/domain/predictions/condition_id_overrides.py`(new)                            |`POLYMARKET_CONDITION_ID_TO_GROUP:
dict[str,
CanonicalQuestionGroup]`— hand-curated overrides for headline markets where automated classification is wrong; long tail uses classifier.                                                                                                                                                                                                                                                                                                                                                                                                                               | |`unified_api_contracts/canonical/domain/predictions/ticker_overrides.py`(new)                                  |`KALSHI_TICKER_TO_GROUP:
dict[str,
CanonicalQuestionGroup]`— same pattern.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | |`unified_api_contracts/canonical/domain/predictions/lifecycle.py`(new)                                         |`MarketLifecycle`dataclass:`market_id`, `canonical_group`, `market_created_at`, `resolution_time`, `settlement_time`, `current_status`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | | `unified_api_contracts/canonical/crosscutting/honest_coverage.py`                                              |`PREDICTION_GROUPS`registry populated (currently empty per writegate plan). Schema:`{canonical_group:
{expected_market_ids_per_day_by_cadence:
...}}`.                                                                                                                                                                                                                                                                                                                                                                                                                                                              | | `unified_api_contracts/canonical/crosscutting/availability_semantics.py`                                       | Add`("prediction",
"prediction_canonical_question_group")`→`event_time`(per-row tick timestamp); add`("prediction",
"MARKET_LIFECYCLE")`→`market_created_at`for the metadata table.                                                                                                                                                                                                                                                                                                                                                                                                                           | |`unified_api_contracts/canonical/crosscutting/source_priority.py`                                              | Add`("prediction",
"prediction_canonical_question_group")`→`["polymarket_ws_live", "polymarket_rest_archive", "kalshi_ws_live",
"kalshi_rest_archive"]`. |

### market-tick-data-service (MTDS)

| File                            | Concern                                                                                                                                                                                                                                                                                                                   |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `polymarket_adapter.py:454–602` | Shard at `condition_id` currently. Migrate to `(canonical_question_group, condition_id)` bundle: shard atom = `(asset_group=prediction, venue=POLYMARKET, data_type=prediction_canonical_question_group, canonical_question_group, day)`; rows within the shard carry `market_id` (= conditionId) for cluster validation. |
| `kalshi_adapter.py:242–269`     | Same migration: shard at `(canonical_question_group, ticker)` bundle.                                                                                                                                                                                                                                                     |
| `umi_tick_provider.py:225`      | Replace `category="prediction_market"` with `asset_group="prediction"` (also flagged in writegate plan).                                                                                                                                                                                                                  |
| Lifecycle gating                | MTDS adapter must call `unified_api_contracts.predictions.is_market_active_at(market_id, tick.timestamp)` before accepting the tick. NO ticks before `market_created_at`, NO new ticks after `settlement_time`.                                                                                                           |
| Bundle write-gate               | `record_captured(expected_root_clusters=PREDICTION_GROUPS[canonical_group][day], cluster_extractor=lambda row: row["market_id"])` — enforces all expected market_ids for the day are represented.                                                                                                                         |

### features-\* + strategy-service

| File | Concern | | ------------------------------------------------------------------------------------------ |
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| ---                                                                                                                     |
| ----------------------------------------------------------------------------------------------------------------------- |
| ------------------------------------------------------------------------------                                          |                               | `features-cross-instrument-service`      |
| (likely owner of prediction features — verify Phase 0)                                                                  | Reader paths currently key on |
| `(venue, data_type=BTC                                                                                                  | ETH                           | ...)`.                                   |
| Migrate to `(venue, data_type=prediction_canonical_question_group, canonical_question_group=BTC_UP_DOWN_HOURLY          | ...)`.                        |
| Per-market drill-down for features that operate at single-market level.                                                 |                               | `strategy-service` prediction archetypes |
| Archetype configs reference `data_type=BTC` etc. Migrate to canonical_group references.                                 |                               | `LookaheadBiasError`                     |
| Per-market lifecycle gating: feature at T can only consume ticks where `tick.market_id`'s `market_created_at <= T`. UTL |
| `assert_lifecycle_respected(feature_t, market_lifecycle)` helper (extends existing `assert_available_at_present`).      |

### deployment-api / deployment-ui

| Surface                                     | Change                                                                                                                                                                                                                                                                                        |
| ------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Data-status panel — predictions asset_group | Drill-down shape: `canonical_question_group → market_id → day → leaf_parquet`. canonical_question_group is the per-cohort rollup (HOURLY shows 24 markets per day, DAILY shows 1, ELECTION shows progression over months); market_id is the per-market detail with lifecycle states surfaced. |
| New columns                                 | `markets_active`, `markets_resolved`, `markets_settled` per (canonical_group, day).                                                                                                                                                                                                           |
| Lifecycle visualisation                     | Per-canonical_group timeline showing market cohorts: created → active → resolved → settled.                                                                                                                                                                                                   |

### GCS

| Bucket / path                                                                                       | Concern                                                                                                                                                                                                                                                 |
| --------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `gs://{pid}-mtds-prediction/raw_tick_data/` (or wherever Polymarket parquets live — verify Phase 0) | Existing parquets at `data_type=BTC` / `ETH` / etc. need migration: read each, lookup conditionId → canonical_group via UAC classifier, regroup by `(canonical_group, day)`, write new parquets at canonical path, delete old paths after verification. |
| Residual `category=prediction` legacy hive vocab                                                    | `migrate_polymarket_canonical.py` (MTDS) — confirm run status; complete if not done.                                                                                                                                                                    |

---

## Phase DAG

```
Phase 0 (audit)
  │
  ▼
Phase 1A (UAC SSOTs — sequential, blocks all)  ──┐
Phase 1B (CLAUDE.md if any new rules)          ──┤── Phase 2 (parallel: 2A instruments-service, 2B MTDS adapters, 2C features-* readers)
                                                  │
                                                  ▼
                                            Phase 3 (Retrospective: classifier-derived re-grouping, GCS migration, manifest reflip)
                                                  │
                                                  ▼
                                            Phase 4 (UI + alerts) ── parallel with Phase 2 once UAC lands
                                                  │
                                                  ▼
                                            Phase 5 (Validation + honest-coverage baseline for predictions)
```

QG gates between every phase.

---

## Phase 0 — Pre-audit

- [x] [AUDIT] P0. Polymarket conditionId universe — **Done 2026-05-06.** See "Phase 0 audit findings — Polymarket
      conditionId universe" below.
- [x] [AUDIT] P0. Kalshi ticker universe — **Done 2026-05-06.** See "Phase 0 audit findings — Kalshi pipeline status"
      below.
- [x] [AUDIT] P0. Existing classifier behaviour — **Done 2026-05-06.** **MAJOR PLAN-PREMISE CORRECTION**: the classifier
      the plan describes as greenfield UAC work ALREADY EXISTS at
      `unified_api_contracts/internal/schemas/_prediction_market_taxonomy.py:540` `classify_polymarket_market()`. See
      "Phase 0 audit findings — existing UAC classifier" below.
- [ ] [AUDIT] P0. Canonical-question-group taxonomy — **PARTIAL** via classifier audit + GCS findings. See "Phase 0
      audit findings — canonical-question-group taxonomy seed (partial)" below. Final taxonomy still requires Ikenna
      sign-off on per-cadence expected counts + naming convention (HOURLY/DAILY suffix policy).
- [x] [AUDIT] P0. Lifecycle field availability — **Done 2026-05-06.** See "Phase 0 audit findings — lifecycle field
      availability" below. CRITICAL: `PolymarketGammaMarket` schema silently drops `createdAt` and `closedTime` due to
      `extra="ignore"`; one-line UAC fix unblocks `market_created_at` and event-level resolution proxy.
- [x] [AUDIT] P0. Downstream consumer inventory — **Done 2026-05-06.** 28 Python/TypeScript files + 4 shell/test files;
      12 RESHAPE / 12 RENAME / 3 DELETE / 1 out-of-scope. See "Phase 0 audit findings — downstream consumer
      blast-radius" below.
- [ ] [AUDIT] P0. Classifier stability hash design — **PENDING.** Audit-3 documented the existing classifier shape
      (130-entry slug-prefix map + 26-entry keyword map + 6-pass cascade). Stability hash = SHA-256 of sorted-keys of
      `(SLUG_PREFIX_MAP ∪ KEYWORD_TO_CATEGORY ∪ OUTCOME_TO_MARKET_TYPE ∪ _RANGE_BRACKET_TOKENS ∪ _MONTHLY_TOKENS ∪     _WEEKLY_TOKENS ∪ _QUARTERLY_TOKENS)` +
      `CLASSIFIER_VERSION` constant. Stored as `CLASSIFIER_STABILITY_HASH` module-level constant alongside the
      classifier; manifest rows record this hash so reclassification only fires when the hash changes.

QG between Phase 0 and Phase 1: audit outputs reviewed by user; canonical-question-group taxonomy signed off; classifier
stability hash agreed.

---

## Phase 0 audit findings (2026-05-06 Claude session)

### Phase 0 audit findings — Polymarket conditionId universe

Direct GCS listing of `gs://market-data-tick-prediction-central-element-323112/` confirms the on-disk shape is **ALREADY
richer than the plan assumed**.

**Plan premise**: shards at `data_type=<base_asset>` (BTC/ETH/SPX/FOOTBALL/OTHER) — 5 buckets across thousands of
underlying markets, with per-market identity collapsed at write-time.

**Actual on-disk shape** (verified 2026-05-06):

```
day=YYYY-MM-DD/category=prediction/data_source=POLYMARKET_CLOB/venue=POLYMARKET/chain=POLYGON/
  market_category={CRYPTO_PRICE|MACRO|CULTURE|MISC|POLITICS_INTL|POLITICS_US|TECH|WEATHER}/
  underlying={BTC|ETH|SOL|DOGE|KANYE|FEAR_GREED|TRUMP|TEMPERATURE|EPSTEIN|ELON_MUSK|...}/
  market_type={binary|range_bracket}/
  resolution_period={hourly|daily|weekly|monthly|event}/
  data_type=trades/{condition_id}.parquet
```

Per-market identity IS preserved (one parquet per condition_id). Per-`market_category` + per-`underlying` +
per-`market_type` + per-`resolution_period` hive partitions ALREADY exist. The shape is essentially the v6 canonical
manifest row already.

**Universe size**:

- 2025-03-14: 85 distinct condition_ids
- 2025-09-01: 424 distinct condition_ids
- 2026-01-15: 1,848 distinct condition_ids (~21x growth in 10 months)
- 2026-04-29: 0 (newest day; 1 partition dir created but not populated)

**Date coverage**: 352 days (2025-03-14 → 2026-04-29).

**Hive vocab transition mid-flight**: older days (2025-03-14) use legacy `category=prediction`; newer days (2026-04-27+)
use canonical `asset_group=prediction`. Migration partially in-flight.

**Implications**:

- The plan's "migrate from per-base_asset shard to per-canonical-group bundle" is already mostly done at the GCS level —
  what's missing is (a) the canonical-group label as a hive key, (b) lifecycle metadata, (c) cluster-coverage validation
  at the bundle level.
- Migration scope is smaller than plan estimated: per-(market_category, underlying, market_type, resolution_period) hive
  keys already capture the essence of canonical_question_group; new work is a single composition step (4-tuple →
  canonical group name) rather than a structural reshape.

### Phase 0 audit findings — Kalshi pipeline status

**Status: WIRED-BUT-UNVERIFIED.** Code-complete at every layer; operational blocker only.

- `KalshiAdapter` (`market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py:49-278`) — full
  implementation; uses public `https://trading-api.kalshi.com/trade-api/v2/markets/{ticker}/trades` (no auth needed for
  public reads).
- Venue dispatch wired: `umi_tick_provider.py:54` `_PREDICTION_VENUES = frozenset({"POLYMARKET", "KALSHI"})`.
- Factory wired: `factory.py:165` `"kalshi": ("prediction_market", KalshiAdapter)`.
- Instruments-service wired: `engine/orchestrator.py:937-939` adds KALSHI to venues.
- **Blocker**: UAC `data_type_capability.py:600-605` says `"# KALSHI excluded — no US account yet."` — operational not
  architectural. Public read endpoints work without account.

**Ticker format**: `market_ticker` (leaf, e.g. `KXBTC-26MAR21-T95000`); `series_ticker` (e.g. `KXBTC`) is the
canonical-group analog; `event_ticker` (e.g. `KXBTC-26MAR21`) is event-level. The shard ID written to GCS is
`market_ticker`.

**Lifecycle fields confirmed**: `open_time` ✓, `close_time` ✓, `expiration_time` ✓, `expected_expiration_time` ✓ (all
present in `KalshiMarket` schema + verified in cassette `markets.yaml:17`). `settlement_timestamp` is in
`KalshiHistoricalCutoff` (bulk cutoff) but NOT per-market — use `expiration_time` as proxy.

**Risk for Plan A**: can ship Polymarket-only Phase 1 without Kalshi; Kalshi migration is near-zero-delta when
operational unblock lands.

### Phase 0 audit findings — existing UAC classifier (PLAN PREMISE CORRECTION)

**The plan's Phase 1A "build canonical_question_group classifier" is significantly overspec'd — most of the work is
already done.**

**Existing SSOT**: `unified-api-contracts/unified_api_contracts/internal/schemas/_prediction_market_taxonomy.py` exists
and is already consumed by:

- `market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py:32` (production)
- `market_tick_data_service/scripts/migrate_polymarket_canonical.py:115` (migration)

**Function**:
`classify_polymarket_market(slug, event_slug, title, outcome) → (category, underlying, market_type, resolution_period)`

**Output schema** (already production-grade):

- 13 categories (`PredictionShardCategory`): CRYPTO_PRICE / EQUITY_INDEX / COMMODITY / FX / MACRO / POLITICS_US /
  POLITICS_INTL / SPORTS_FOOTBALL / SPORTS_OTHER / CULTURE / TECH / WEATHER / MISC
- 5 market types: binary / scalar / categorical / ranked / range_bracket
- 8 resolution periods: intraday / hourly / daily / weekly / monthly / quarterly / yearly / event

**Rule-set**:

- 130-entry `SLUG_PREFIX_MAP` (lines 117-306) — most-specific-first ordered dict; first match wins
- 26-entry `KEYWORD_TO_CATEGORY` (lines 311-338) — substring fallback
- 6-pass resolution cascade (slug-prefix → event-slug-prefix → slug-token → event-slug-token → title-keyword →
  event-slug-keyword)
- `_RANGE_BRACKET_TOKENS` / `_WEEKLY_TOKENS` / `_MONTHLY_TOKENS` / `_QUARTERLY_TOKENS` for type/period inference
- 78 unit tests, 4 commits of evolution; commit `c600954` reduced MISC category from 45% → 3.5% (weighted) on real
  Polymarket data.

**What's NOT yet built (real Plan A scope)**:

1. **Composition wrapper**: `classify_market_to_canonical_group() → CanonicalQuestionGroup | None` that composes the
   4-tuple `(category, underlying, market_type, resolution_period)` into a canonical group name (e.g.
   `BTC_UP_DOWN_HOURLY`).
2. **`CLASSIFIER_STABILITY_HASH` constant** — currently absent. Required for manifest rows to record which classifier
   version produced the label.
3. **Bug fix**: `_MONTHLY_TOKENS` is missing `"may"` (3-letter and full-name set both miss it).
   `"bnb-up-or-down-may-15"` resolves to `YEARLY` instead of `MONTHLY`.
4. **7 edge-case tests** to add (Airbnb / archBitcoin / solar / house-price / fed-ex / bnb-may-15 / fear-factor).
5. **Hybrid long-form / short-ticker pattern** from instruments-service `b336834`/`d7bd17f` — currently in
   `instruments_service/reference_data/adapters/prediction/polymarket.py` (separate question-text classifier). Port to
   UAC if KEYWORD_TO_CATEGORY is extended to question-text matching.

**Plan amendment needed**: Phase 1A scope drops by ~70% — UAC work is "wrap + bug-fix + add stability hash" (~1-2 days),
not "design and build classifier from scratch" (~1 week).

### Phase 0 audit findings — canonical-question-group taxonomy seed (partial)

The existing UAC classifier produces the 4-tuple foundation. Composing into canonical group names:

**Cadenced markets** (4-tuple → group):

- `(CRYPTO_PRICE, BTC, range_bracket, hourly)` → `BTC_UP_DOWN_HOURLY` (24/day expected)
- `(CRYPTO_PRICE, BTC, range_bracket, daily)` → `BTC_UP_DOWN_DAILY` (1/day expected)
- Same shape for ETH/SOL/XRP/DOGE/BNB/HYPE/SUI/ADA/LTC/AVAX/LINK (12 cryptos in `SLUG_PREFIX_MAP`)
- `(EQUITY_INDEX, SPX, range_bracket, daily)` → `SPX_UP_DOWN_DAILY`; same for NDX/DJIA
- `(COMMODITY, GOLD, range_bracket, daily)` → `GOLD_UP_DOWN_DAILY`; same for SILVER/CRUDE_OIL/NAT_GAS

**Macro events** (irregular cadence):

- `(MACRO, FED_FUNDS, categorical, event)` → `FED_RATE_DECISION_PER_FOMC` (8/year expected per FOMC schedule)
- `(MACRO, CPI, scalar, event)` → `CPI_RELEASE_PER_MONTH` (12/year expected)
- Same for GDP/UNEMPLOYMENT/NONFARM_PAYROLLS/PPI/PCE/JOBLESS

**Election / long-lifecycle**:

- `(POLITICS_US, US_ELECTION, categorical, yearly)` → `ELECTION_PRESIDENT_{year}` (1 active at a time)
- `(POLITICS_US, US_SENATE, categorical, yearly)` → `ELECTION_SENATE_{year}`
- `(POLITICS_US, US_HOUSE, categorical, yearly)` → `ELECTION_HOUSE_{year}`
- `(CULTURE, OSCARS, categorical, yearly)` → `OSCARS_{year}`; same for GRAMMYS/EMMYS

**Sports**: cross-references the writegate plan's sports per-fixture sharding. Per-fixture canonical group =
`(SPORTS_FOOTBALL, EPL, categorical, event)` → `SPORTS_EPL_FIXTURE_{fixture_id}` etc.

**MISC**: classifier returns `category=MISC, underlying="UNKNOWN"` → canonical_group = `None`. These markets get
`attempted_failed[reason=ClassifierConfidenceLow]`; cluster gate fires loud.

**Open questions for Ikenna**:

1. Naming convention: `BTC_UP_DOWN_HOURLY` vs `BTC_HOURLY` vs `CRYPTO_BTC_HOURLY`?
2. Per-cadence expected_market_ids_per_day source: hardcoded constants in the registry, or dynamic from manifest row
   counts?
3. Election year suffix: explicit year (`ELECTION_PRESIDENT_2028`) or floating (`ELECTION_PRESIDENT_NEXT`)?
4. Sports fixture canonical groups: align with writegate plan's `SPORTS_FIXTURE_CLUSTERS`? Same registry or separate?

**2026-05-06 cadence-count probe — concrete proposal for Ikenna sign-off**:

Probed `_prediction_market_taxonomy.py` `_infer_resolution_period()` cascade (lines 568-616), `polymarket/schemas.py`
lifecycle hints, MTDS `polymarket_adapter.py`, and the on-disk inventory referenced in the 2026-04-29 audit (1,848
distinct condition_ids; 352 days; resolution periods observed = hourly / daily / weekly / monthly / event). Concrete
cadence-count proposal:

| canonical_question_group                                | cadence      | expected_markets_per_day     | evidence                                                                                           | confidence |
| ------------------------------------------------------- | ------------ | ---------------------------- | -------------------------------------------------------------------------------------------------- | ---------- |
| `BTC_UP_DOWN_HOURLY`                                    | HOURLY       | 24                           | classifier `_infer_resolution_period:578-579` (hour/hourly token); slug pattern present            | HIGH       |
| `BTC_UP_DOWN_DAILY`                                     | DAILY        | 1                            | classifier `:587-588` (daily/day tokens); slug `btc-up-or-down-april-15`                           | HIGH       |
| `ETH_UP_DOWN_HOURLY`                                    | HOURLY       | 24                           | symmetric with BTC pattern                                                                         | HIGH       |
| `ETH_UP_DOWN_DAILY`                                     | DAILY        | 1                            | symmetric with BTC pattern                                                                         | HIGH       |
| `SOL/XRP/DOGE/BNB/HYPE/SUI/ADA/LTC/AVAX/LINK_UP_DOWN_*` | HOURLY+DAILY | 24+1                         | 12 cryptos in `SLUG_PREFIX_MAP`                                                                    | HIGH       |
| `SPX_UP_DOWN_DAILY`                                     | DAILY        | 1                            | classifier `:143-145` (spx-/sp500-/s-and-p-500- → EQUITY_INDEX)                                    | HIGH       |
| `NDX/DJIA_UP_DOWN_DAILY`                                | DAILY        | 1                            | symmetric with SPX                                                                                 | HIGH       |
| `GOLD_UP_DOWN_DAILY`                                    | DAILY        | 1                            | classifier `:151` (gold- → COMMODITY)                                                              | MEDIUM     |
| `SILVER/CRUDE_OIL/NAT_GAS_UP_DOWN_DAILY`                | DAILY        | 1                            | symmetric with GOLD                                                                                | MEDIUM     |
| `FED_RATE_DECISION_PER_FOMC`                            | EVENT        | 1 per FOMC date              | classifier `:166-168` (fed-rate-/fomc-); 8 FOMC meetings/year hardcoded                            | MEDIUM     |
| `CPI_RELEASE_PER_MONTH`                                 | MONTHLY      | 1                            | MONTHLY tokens at `:369-395`; 12/year                                                              | MEDIUM     |
| `GDP/UNEMPLOYMENT/NFP/PPI/PCE/JOBLESS_*`                | varies       | varies                       | release schedule per macro indicator                                                               | MEDIUM     |
| `ELECTION_PRESIDENT_2028`                               | EVENT_LONG   | 1 (active over months/years) | classifier `:615` (default EVENT for politics); SLUG_PREFIX_MAP shows trump-/harris- → POLITICS_US | MEDIUM     |
| `WEATHER_HURRICANE_*`                                   | EVENT        | variable per storm           | classifier `:296` (hurricane-/weather- → WEATHER); EVENT default                                   | MEDIUM     |

**Recommended Ikenna decisions on the 4 open questions** (formed from the probe + workspace conventions):

1. **Naming convention**: `{UNDERLYING}_UP_DOWN_{CADENCE}` for cadenced range-bracket markets (BTC*UP_DOWN_HOURLY);
   `{UNDERLYING}*{EVENT}\_{SUFFIX}`for events (FED_RATE_DECISION_PER_FOMC, ELECTION_PRESIDENT_2028). Rationale:`UP_DOWN`
   is meaningful (range-bracket markets resolve binary up/down vs a strike), and the cadence suffix is the
   cluster-validator's expected-count key.
2. **Expected count source**: hardcoded in registry. Dynamic-from-manifest is tempting but creates a chicken-and-egg
   with the cluster validator (it'd bootstrap from incomplete data). Hardcoded = honest expectation; manifest row counts
   diverging from hardcoded = honest gap → investigate.
3. **Election year suffix**: explicit year (`ELECTION_PRESIDENT_2028`). Floating `_NEXT` makes historical readback
   ambiguous and breaks training pipelines.
4. **Sports fixture canonical groups**: separate registry — different cluster identity (per-fixture per-bookmaker vs
   per-canonical-group per-market_id). Both can live in `unified_api_contracts.canonical.crosscutting.honest_coverage`
   under `PREDICTION_GROUPS` and `SPORTS_FIXTURE_CLUSTERS` slots.

Sources verified during probe:

- `unified-api-contracts/unified_api_contracts/internal/schemas/_prediction_market_taxonomy.py:98-615`
- `unified-api-contracts/unified_api_contracts/external/polymarket/schemas.py:49-365`
- `market-tick-data-service/.../polymarket_adapter.py:1-676`

### Phase 0 audit findings — lifecycle field availability

**Polymarket — partial coverage with one zero-effort UAC fix**:

| Plan field | Source field | Status | Action | | -------------------------- |
---------------------------------------------------------------------------- | ------------------------------- |
------------------------------------------------------------------------------------------------------------------- |
-------------------------------------------------------------------------------------------------------- | |
`market_created_at` | `PolymarketGammaMarket.createdAt` (raw JSON has it; Pydantic model drops it) | **CRITICAL ONE-LINE
FIX** | Add
`created_at: str                                                                                                | None = Field(None, alias="createdAt")`to`PolymarketGammaMarket`(UAC`external/polymarket/schemas.py:289`)
| | `resolution_time` (actual) | `PolymarketMarketResult.resolution_time` (separate REST endpoint) | Available via
second API call | One-extra-call-per-resolved-market in instruments-service Phase 1B | | `resolution_time` (proxy) |
`PolymarketGammaMarket.end_date_iso` | Available; scheduled-not-actual | Use as
`lifecycle_confidence="low_scheduled_end_date"` for unresolved markets | | `settlement_time` | NO direct field |
UNAVAILABLE | Always derive: `resolution_time + settlement_lag` (2h UMA undisputed; 48-72h disputed); confidence column
mandatory |

**Kalshi — full coverage**:

- `market_created_at` ← `open_time` ✓ confirmed in cassette
- `resolution_time` ← `close_time` ✓
- `settlement_time` ← `expiration_time` ✓ (often equal to `close_time`; settlement lag often zero)
- ~3-month historical window only on trades; metadata endpoint persistence needs runtime verification.

**Test fixtures available**: Polymarket `gamma_events_cassette.json` confirms raw JSON has `createdAt`/`closedTime` on
per-market sub-objects (lines 59, 61); UAC model just doesn't capture them. Kalshi `markets.yaml` confirms full
lifecycle.

### Phase 0 audit findings — downstream consumer blast-radius

**Total: 28 Python/TypeScript files + 4 shell/test files** across 9 repos.

**Distribution by migration action**: | Action | Count | Notes | |---|---|---| | RESHAPE | 12 | Core data path —
structural change required | | RENAME | 12 | String-literal swap; low risk; can batch | | DELETE | 3 | Superseded
scripts post-migration | | Out of scope | 1 | execution-service `gcs_creator.py` — base_asset is CeFi currency not
prediction |

**12 high-risk RESHAPE files** (require design before implementation):

1. `instruments-service/instruments_service/engine/orchestrator.py:2052-2086, 2580-2616` — `_extract_prediction_shard()`
   write path
2. `instruments-service/instruments_service/reference_data/adapters/prediction/polymarket.py:55-145, 777-892` — separate
   question-text classifier with b336834/d7bd17f hybrid regex
3. `market-tick-data-service/.../prediction/polymarket_adapter.py:59-112, 494-560, 606-660` — tick shard + lifecycle
   gating + GCS reader
4. `market-tick-data-service/.../prediction/kalshi_adapter.py:254-262, 288` — parallel migration
5. `market-data-processing-service/.../dependency_checker.py:21-24, 442-445` — pre-flight gate uses
   `instrument_type=BTC|ETH|FOOTBALL|OTHER` blob tokens
6. `features-cross-instrument-service/.../batch_handler.py:62-102` — GCS blob filter on old data_type path
7. `deployment-api/services/data_status_drilldown.py:509-511, 545-546, 919-941, 987-1049` — entire
   `instrument_type=OTHER` special-casing for POLYMARKET
8. `deployment-api/services/data_status_service.py:848-910` — `PREDICTION_DATA_TYPE_META` shard_dim tuple + expected
   coverage logic
9. `deployment-ui/src/components/DataStatusTab.tsx:4719-4750` — instrument_type guess `"OTHER"` for POLYMARKET
   drill-down
10. `deployment-ui/tests/unit/components/DataStatusDrilldown.test.tsx:78-389` — all test fixtures use old shape
11. `unified-api-contracts/.../_prediction_market_taxonomy.py` — existing taxonomy enum supersession plan
12. `unified-api-contracts/canonical/domain/prediction/prediction_mapping.py:17-27, 54-74` — overlapping
    `PredictionMarketCategory` enum needs alignment with new `CanonicalQuestionGroup`

**12 RENAME files** (post-Phase-1A batch update): `umi_tick_provider.py`, `canonical_writer.py`,
`features_cross_instrument_service/{config.py, engine/orchestrator.py, calculators/__init__.py, schemas/feature_builder_registry.py}`,
`strategy_service/{archetype_slot_resolver.py, target_universe/catalog.py, migration/legacy_strategy_mapping.py, cli/handlers/batch_utils.py}`,
`execution-service/mock_data_provider.py`, `deployment-ui/DataStatusDrilldown.tsx` (labels),
`deployment-api/routes/data_status.py` (comments), `launch-mtds-prediction-backfill-vm.sh` (comment).

**3 DELETE files** (post-migration cleanup):
`instruments-service/scripts/{patch_prediction_shards.py, rescan_prediction_v4.py, split_prediction_by_market.py}` —
superseded entirely by canonical migration script.

**Test fixtures** (flagged separately): 4 test files — most just need fixture-string updates.

### Plan amendments surfaced (post Phase 0)

| # | Amendment | Status | Owner | | --- |
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
---------------------------------------------------------------------------------------------------------------------------------

| -------------------------------------------- | ---------------------- | | α | Phase 1A scope reduction: existing
classifier IS the SSOT — wrap + bug-fix + add stability hash, not greenfield build (~70% effort drop) | Surfaced — needs
Ikenna sign-off on revised scope | Ikenna | | β | One-line UAC fix:
`PolymarketGammaMarket.created_at: str                                                                                                                                                                                                           | None = Field(None, alias="createdAt")`+
same for`closedTime`. Unblocks `market_created_at`and event-level`resolution_time` proxy. | **Trivial — Claude can ship
after sign-off** | Claude (with sign-off) | | γ | Bug fix: add `"may"` to `_MONTHLY_TOKENS` in
`_prediction_market_taxonomy.py` (currently missing from both 3-letter and full-name sets). | Trivial bug fix | Claude
(with sign-off) | | δ | 7 edge-case tests to add for the existing classifier (Airbnb / archBitcoin / solar / house-price
/ fed-ex / bnb-may-15 / fear-factor — see audit-3 §F3). | Test coverage | Claude (with sign-off) | | ε | Migration scope
reduction: GCS hive partitions ALREADY include `market_category` / `underlying` / `market_type` / `resolution_period`.
Migration is a single composition step (4-tuple → canonical_group name) + lifecycle metadata add, NOT a structural
reshape. | Surfaced | Ikenna | | ζ | Open question: canonical-group naming convention (`BTC_UP_DOWN_HOURLY` vs
`BTC_HOURLY` vs `CRYPTO_BTC_HOURLY`)? | Pending | Ikenna | | η | Open question: per-cadence
`expected_market_ids_per_day` — hardcoded constants in registry, or dynamic from manifest row counts? | Pending | Ikenna
| | θ | Open question: election year suffix — explicit (`ELECTION_PRESIDENT_2028`) or floating
(`ELECTION_PRESIDENT_NEXT`)? | Pending | Ikenna | | ι | Open question: sports fixture canonical groups — align with
writegate plan's `SPORTS_FIXTURE_CLUSTERS` registry, or separate? | Pending — coordination point with writegate | Ikenna
|

---

## Phase 1A — UAC SSOTs (sequential, blocks all)

- [x] [SCRIPT] P0. New module `unified_api_contracts/canonical/domain/predictions/canonical_groups.py`: ```python class
      CanonicalQuestionGroup(StrEnum): BTC_UP_DOWN_HOURLY = "BTC_UP_DOWN_HOURLY" BTC_UP_DOWN_DAILY =
      "BTC_UP_DOWN_DAILY" # ... (per Phase 0 taxonomy) OTHER = "OTHER"

      @dataclass(frozen=True)
              class CanonicalGroupMetadata:
                  group: CanonicalQuestionGroup
                  cadence: Literal["hourly", "daily", "weekly", "monthly", "irregular", "single"]
                  expected_market_ids_per_day: int | Callable[[date], int]  # int for fixed cadence, callable for irregular
                  resolution_basis: Literal["price_threshold", "binary_outcome", "multi_outcome"]
                  settlement_lag: timedelta  # typical settlement_time − resolution_time

              CANONICAL_GROUP_METADATA: dict[CanonicalQuestionGroup, CanonicalGroupMetadata] = {...}
              ```

- [x] [SCRIPT] P0. New module `unified_api_contracts/canonical/domain/predictions/classifiers.py`: -
      `classify_market_to_canonical_group(market_metadata: PolymarketMarketMetadata | KalshiMarketMetadata) -> CanonicalQuestionGroup | None`
      — returns None for sub-threshold confidence; caller marks shard as
      `attempted_failed[reason=ClassifierConfidenceLow]`. - Internal: word-boundary regex rules + token-overlap
      scoring + `POLYMARKET_CONDITION_ID_OVERRIDES` / `KALSHI_TICKER_OVERRIDES` lookup-first. - Stability hash:
      `CLASSIFIER_STABILITY_HASH` constant computed at import time from regex pattern source + override dict hashes.
      Manifest writes carry this hash; re-runs skip re-classification when hash unchanged.
- [x] [SCRIPT] P0. New module `unified_api_contracts/canonical/domain/predictions/lifecycle.py`: ```python
      @dataclass(frozen=True) class MarketLifecycle: market_id: str venue: str # "POLYMARKET" / "KALSHI"
      canonical_group: CanonicalQuestionGroup market_created_at: datetime resolution_time: datetime settlement_time:
      datetime current_status: Literal["created", "active", "resolved", "settled"]

      def is_market_active_at(lifecycle: MarketLifecycle, ts: datetime) -> bool:
                  return lifecycle.market_created_at <= ts < lifecycle.settlement_time

              def expected_market_ids_for_canonical_group(
                  group: CanonicalQuestionGroup, day: date, lifecycles: Iterable[MarketLifecycle]
              ) -> set[str]:
                  # Returns market_ids whose [created, settled) window overlaps the day.
                  ...
              ```

- [x] [SCRIPT] P0. Populate `unified_api_contracts/canonical/crosscutting/honest_coverage.py` `PREDICTION_GROUPS`
      registry (was empty per writegate plan): - For each `CanonicalQuestionGroup`, derive the expected
      market_ids_per_day from lifecycle metadata. - `cluster_extractor` for prediction shards:
      `lambda row: row["market_id"]`. - `min_rows_per_cluster`: per-cadence (HOURLY → expect ~1000 ticks per market over
      its 1-hour life; DAILY → expect ~10000 ticks over 24h; etc., refine per Phase 0 audit data).
- [x] [SCRIPT] P0. Update `unified_api_contracts/canonical/crosscutting/availability_semantics.py`: -
      `("prediction", "prediction_canonical_question_group")` → `event_time` (per-row tick timestamp). -
      `("prediction", "MARKET_LIFECYCLE")` (the metadata table) → `market_created_at` (we couldn't have known about the
      market before it was listed).
- [x] [SCRIPT] P0. Update `unified_api_contracts/canonical/crosscutting/source_priority.py`: -
      `("prediction", "prediction_canonical_question_group")` →
      `["polymarket_ws_live", "polymarket_rest_archive", "kalshi_ws_live", "kalshi_rest_archive"]` (live sources rank
      above archives per "live = batch" rule; archive falls back when historical replay needed).
- [x] [SCRIPT] P0. New facade `unified_api_contracts/predictions/__init__.py` re-exports all of the above for consumer
      ergonomics:
      `python     from unified_api_contracts.predictions import (         CanonicalQuestionGroup,         classify_market_to_canonical_group,         MarketLifecycle,         is_market_active_at,         expected_market_ids_for_canonical_group,     )     `
- [x] [TEST] P0. UAC tests: - Every `CanonicalQuestionGroup` has a metadata entry. - Classifier handles every
      conditionId in the Phase 0 audit `conditionid_universe.csv` — assert classification + expected-group match curated
      overrides for headline markets. - Stability hash deterministic; changes only when regex / overrides change. -
      Lifecycle helpers: `is_market_active_at` returns False before `market_created_at`, True during
      `[created, settled)`, False after. - `PREDICTION_GROUPS` registry: every group has `cluster_extractor` +
      `min_rows_per_cluster` + valid `expected_market_ids_per_day`.

QG between Phase 1A and Phase 2: UAC tests green; UAC pushed to `live-defi-rollout`; downstream consumers rebuild
against new UAC.

---

## Phase 1B — CLAUDE.md (no new rules; predictions lifecycle rule already added 2026-05-06)

- [x] [DOCS] P0. **Already shipped 2026-05-06** — workspace `unified-trading-pm/cursor-configs/CLAUDE.md`
      `§ Prediction market lifecycle timing` rule added pre-merge of this plan. No additional CLAUDE.md edits required
      from this plan.

---

## Phase 2 — Service forward fixes (parallel after Phase 1A)

### Phase 2.A — instruments-service

- [ ] [SCRIPT] P0. Lifecycle ingestion — for every conditionId / ticker, capture all three lifecycle timestamps: -
      Polymarket: `market.created_at`, `market.resolution_time`, `market.settlement_time` from the REST
      `/markets/{conditionId}` endpoint. - Kalshi: same shape from the Kalshi market metadata endpoint. - Workaround if
      a source doesn't expose `settlement_time`:
      `settlement_time = resolution_time + CANONICAL_GROUP_METADATA[group].settlement_lag` with
      `settlement_time_confidence = "low_lifecycle_default"` audit column.
- [ ] [SCRIPT] P0. New writer path in `engine/orchestrator.py`:
      `_write_prediction_market_lifecycle(market_id, lifecycle)` writes one row per market into a `MARKET_LIFECYCLE`
      data_type parquet keyed by `(asset_group=prediction, venue, data_type=MARKET_LIFECYCLE, market_id, ingest_day)`.
      `available_at = market_created_at` (we couldn't have known about the market before it was listed).
- [ ] [SCRIPT] P0. Update `_extract_prediction_shard` / `_compute_prediction_shards` (orchestrator.py:2497–2524) to call
      `unified_api_contracts.predictions.classify_market_to_canonical_group(market_metadata)` instead of base-asset
      keyword matching. Markets where classifier returns None → `record_failed[reason=ClassifierConfidenceLow]`.
- [ ] [SCRIPT] P0. Replace POLYMARKET writer at `orchestrator.py:1990–1995`: - Old: `data_type = <base_asset>` (BTC /
      ETH / SPX / FOOTBALL / OTHER) - New: `data_type = "prediction_canonical_question_group"`,
      `instrument_id = <canonical_group_name>`, `metadata.market_id = <conditionId>`,
      `metadata.lifecycle = MarketLifecycle(...)`, `metadata.classifier_stability_hash = CLASSIFIER_STABILITY_HASH`.
- [ ] [TEST] P0. instruments-service unit + integration tests for lifecycle ingestion + classifier integration.

### Phase 2.B — MTDS

- [ ] [SCRIPT] P0. Polymarket adapter (`polymarket_adapter.py:454–602`) migration: - Read lifecycle from
      instruments-service `MARKET_LIFECYCLE` table (per writegate plan: instruments-service is the SoT for reference
      data; MTDS reads via `instruments_store_defi_*` analog). - Per-tick gating:
      `if not is_market_active_at(lifecycle, tick.timestamp): record_failed(...)` — never accept ticks outside
      lifecycle. - Shard atom:
      `(asset_group=prediction, venue=POLYMARKET, data_type=prediction_canonical_question_group, canonical_question_group, day)`.
      Bundle inside = ticks across all market_ids belonging to that canonical_group on that day. -
      `record_captured(expected_root_clusters=PREDICTION_GROUPS[group][day], cluster_extractor=lambda row: row["market_id"], symbol_column="market_id")`
      — enforces all expected market_ids for the day are represented (HOURLY → 24, DAILY → 1, etc.). - `available_at`
      per row = `tick.timestamp + scrape_latency` (per source priority registry).
- [ ] [SCRIPT] P0. Kalshi adapter (`kalshi_adapter.py:242–269`) — same migration shape.
- [ ] [SCRIPT] P0. `umi_tick_provider.py:225` — replace `category="prediction_market"` with `asset_group="prediction"`
      per workspace vocabulary. (Also flagged in writegate plan; coordinate.)
- [ ] [TEST] P0. MTDS unit tests: lifecycle gating (pre-created tick rejected, post-settled tick rejected); cluster
      validation (incomplete bundle → `attempted_failed[ClusterCoverageError]`); per-market `available_at` stamping.

### Phase 2.C — features-cross-instrument-service (or wherever prediction features live)

- [ ] [SCRIPT] P0. Reader migration: `data_type=BTC|ETH|...` callsites →
      `data_type=prediction_canonical_question_group, canonical_question_group=...`.
- [ ] [SCRIPT] P0. Per-market lifecycle gating in feature compute: `LookaheadBiasError` extension — feature at time T
      can only consume ticks where `tick.market_id`'s `market_created_at <= T`. UTL helper
      `assert_lifecycle_respected(feature_t, market_lifecycles)` (depends on UTL extension in this plan's Phase 1A or
      follow-up — verify with UTL owner).
- [ ] [SCRIPT] P0. Strategy-service prediction archetypes: archetype configs reference canonical_group directly. Migrate
      config files.
- [ ] [TEST] P0. End-to-end smoke: pick 1 canonical_group (`BTC_UP_DOWN_HOURLY`), 1 day; run feature compute at
      `kickoff − 60min` (or whatever the prediction-specific lookahead window is); assert no input tick has
      `market_id`'s `market_created_at > target_ts`.

QG between Phase 2 and Phase 3: every Phase 2 service has QG green; live-mode smoke run end-to-end produces honest
manifest verbs across instruments-service + MTDS + features for a 1-day predictions test run.

---

## Phase 3 — Retrospective migration

### Phase 3.A — Classifier-derived re-grouping of existing per-base_asset parquets

- [ ] [SCRIPT] P0. New script `mtds_migrate_polymarket_per_base_asset_to_canonical_group.py` (in
      `market-tick-data-service/scripts/`): - Iterate every existing parquet under
      `gs://{pid}-mtds-prediction/.../venue=POLYMARKET/data_type={BTC|ETH|SPX|FOOTBALL|OTHER}/...`. - For each row:
      lookup `market_id` (= conditionId) in instruments-service `MARKET_LIFECYCLE` (Phase 2.A output) to get
      `canonical_group`. - Group rows by `(canonical_group, day)`; write new parquets at canonical path
      `gs://{pid}-mtds-prediction/.../venue=POLYMARKET/data_type=prediction_canonical_question_group/canonical_question_group={canonical_group}/day={day}/`. -
      Carry `available_at`, `market_id`, `classifier_stability_hash` into new parquets. - Cluster validation runs at
      write time per Phase 2.B contract → partial bundles → `attempted_failed[ClusterCoverageError(historical)]`. -
      Audit report at `gs://{pid}-reconciler-audit/{run_id}/migration_per_base_asset_to_canonical.csv` listing every
      (old_path, new_path, n_rows, classifier_stability_hash, status).
- [ ] [SCRIPT] P0. Manifest reflip script `mtds_reflip_polymarket_per_base_asset.py`: - Old
      `(venue, data_type=BTC|ETH|...)` rows → `attempted_failed[reason=ShardSchemaMigrated]` for cleanup (or delete
      entirely if no operational reason to keep). - New
      `(venue, data_type=prediction_canonical_question_group, canonical_question_group, market_id, day)` rows written as
      `captured` (or `attempted_failed[ClusterCoverageError(historical)]` for partial bundles). - Per-VM shard write per
      workspace concurrency rule.
- [ ] [SCRIPT] P0. Old parquet deletion — only AFTER (a) new parquets verified by hand-inspection (sample 10 random
      shards, assert ticks present + lifecycle bounds respected + cluster-complete) AND (b) downstream features +
      strategy compute against new parquets succeeds end-to-end.
- [ ] [SCRIPT] P0. Backfill any missing canonical_groups — markets in `conditionid_universe.csv` that classifier maps to
      a canonical_group but have no on-disk data → `attempted_failed[reason=NeverCaptured]` for re-attempt; queue MTDS
      adapter run on those.

### Phase 3.B — Residual `category=prediction` legacy hive vocab

- [ ] [SCRIPT] P0. Confirm `migrate_polymarket_canonical.py` (MTDS — referenced in workspace memory) has run for all
      existing `category=prediction` GCS objects → migrate to canonical `asset_group=prediction` paths.
- [ ] [SCRIPT] P0. After confirmation: delete the `category=prediction` legacy fallback reader in MTDS (no compat shim
      per CLAUDE.md no-double-SSOT rule).

### Phase 3.C — Reconciler observability

- [ ] [SCRIPT] P0. Every reconciler script wraps work in `unified_trading_library.run_lifecycle.run_lifecycle(...)`.
- [ ] [SCRIPT] P0. Each reconciler supports `--max-flips-per-run=10000` halt safety; operator confirms first 10k flips
      look right before lifting cap.
- [ ] [SCRIPT] P0. CSV audit at `gs://{pid}-reconciler-audit/{run_id}/`.

QG between Phase 3 and Phase 4: every reconciler has run end-to-end on a 1-week sample; audit reports reviewed; no
anomalies.

---

## Phase 4 — Data-status UI + alerts (parallel with Phase 2)

### Phase 4.A — deployment-api

- [ ] [SCRIPT] P0. Predictions asset_group panel — drill-down shape
      `canonical_question_group → market_id → day → leaf_parquet`.
- [ ] [SCRIPT] P0. New columns per (canonical_group, day): `markets_active`, `markets_resolved`, `markets_settled`,
      `markets_classifier_low_confidence`.
- [ ] [SCRIPT] P0. Per-market lifecycle visualisation endpoint — returns timeline of cohorts: created → active →
      resolved → settled.
- [ ] [SCRIPT] P0. Per-pillar write-gate failure breakdown for predictions: `ClusterCoverageError` (incomplete bundle),
      `ClassifierConfidenceLow`, `ShardSchemaMigrated`, `NeverCaptured`.

### Phase 4.B — deployment-ui (unified-trading-system-ui)

- [ ] [SCRIPT] P0. Predictions asset-group panel — render canonical_question_group rollup with per-market drill-down.
- [ ] [SCRIPT] P0. Lifecycle states color-coded: created (gray) → active (green) → resolved (blue) → settled (slate).
- [ ] [SCRIPT] P0. Classifier confidence indicator per market_id (high / medium / low / failed).

QG between Phase 4 and Phase 5: UI smoke renders against seeded fixtures.

---

## Phase 5 — Validation + honest-coverage baseline

- [ ] [SCRIPT] P0. Per-canonical_group coverage measurement (post-reconcile): - Denominator: expected market_ids across
      canonical_group's [created, settled) windows, clipped per `SOURCE_COVERAGE_START` for each venue. - Numerator:
      `count(manifest_rows where capture_status == "captured")` for
      `(venue, data_type=prediction_canonical_question_group, canonical_question_group, market_id, day)`. - Honest
      empty: market in lifecycle window but no ticks (rare for liquid markets; possible for low-liquidity tail). -
      Failed: classifier-low-confidence + cluster-incomplete + never-captured.
- [ ] [SCRIPT] P0. Document baseline at
      `unified-trading-pm/codex/02-data/honest_coverage_baseline_predictions_2026_05.md`: - Per-canonical_group baseline
      %. - Per-error_reason breakdown. - Set as ratchet floor.
- [ ] [SCRIPT] P0. LookaheadBiasError end-to-end smoke for predictions: pick 1 strategy / 1 canonical_group; run feature
      compute at fixture / decision time T; assert no consumed tick has `market_id`'s `market_created_at > T`.
- [ ] [SCRIPT] P0. Cluster-validation integration test: feed an incomplete bundle (HOURLY canonical_group with 18 of 24
      expected market_ids on a day) → assert `record_failed(ClusterCoverageError)` + no parquet written.
- [ ] [SCRIPT] P0. Lifecycle gating integration test: feed a tick with `tick.timestamp < market_created_at` → assert
      rejection + `MarketNotYetCreatedError` raised.
- [ ] [QG] P0. Workspace-wide QG on every repo touched (UAC, UTL, instruments-service, MTDS, features-cross-instrument,
      strategy-service, deployment-api, deployment-ui, unified-trading-pm).

QG end-of-plan: user signs off on baseline document; ratchet floor activated for predictions.

---

## Coordination with sibling plans

- **`writegate_honest_coverage_endtoend_2026_05_06.plan.md`** — this plan populates the empty `PREDICTION_GROUPS`
  registry slot reserved by writegate Phase 1B. After this plan lands, writegate's "Temporary states + their canonical
  follow-up plans" entry for `prediction_canonical_question_group` becomes "active".
- **`shard_granularity_ssot_propagation_2026_05_06.plan.md` Phase 1 Tier 1 #1 (MDPS 1440-NaN, paused)** — superseded by
  writegate plan. Indirectly relevant: this plan's MTDS adapter migration must respect the three-category empty-output
  decision tree from writegate Phase 1A + CLAUDE.md.
- **Plan B (UTL/UAC lift triple)** — `assert_lifecycle_respected` UTL helper this plan needs may either land here OR in
  Plan B's NaN-ratio-gate scope. Coordinate.
- **Plan C (pre-flight + concurrency hardening)** — UTL `check_shard_freshness` tightening (Plan C scope) interacts with
  MTDS prediction adapter pre-flight. Sequence: Plan C lands first, this plan benefits from the tightened freshness
  check; OR coordinate so this plan's MTDS pre-flight doesn't regress when Plan C lands.
- **Plan D (multi-source merge)** — predictions have multi-source potential (Polymarket WS + Polymarket REST archive +
  Kalshi WS + Kalshi REST archive). Phase 1A seeds SOURCE_PRIORITY top-entry only; Plan D extends to multi-source
  merge + per-field provenance.

---

## Tracked open questions / temporary states (none deferred)

This plan ships the full shape. No partial implementations passed forward. If a reviewer finds a hidden temporary state
during execution, file as a plan-amendment todo before merging.

---

## Estimated timeline

- Phase 0: 3-4 days (audit; conditionId universe enumeration is the long pole)
- Phase 1A + 1B: 1 week (UAC build + classifier seeding + lifecycle module + tests)
- Phase 2: 1 week parallel across 3 services (instruments-service / MTDS / features-cross-instrument)
- Phase 3: 4-5 days (classifier-derived re-grouping is compute-heavy; runs on GCE)
- Phase 4: 1 week parallel with Phase 2 (UI + alerts)
- Phase 5: 2-3 days (baseline + ratchet)

**Total: ~3 weeks of focused work + reconciler runtime.**

---

## Success criteria

- ✓ UAC `canonical_question_group` SSOT exists with `CanonicalQuestionGroup` enum + classifier + lifecycle module +
  `PREDICTION_GROUPS` cluster registry.
- ✓ instruments-service captures all three lifecycle timestamps per conditionId / ticker; canonical_group classification
  with stability hash.
- ✓ MTDS adapter writes prediction shards at
  `(asset_group, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` bundle with
  cluster validation enforced.
- ✓ Per-market lifecycle gating: NO ticks before `market_created_at`, NO new ticks after `settlement_time`.
- ✓ LookaheadBiasError per-market-aware: feature at T can only consume ticks where `tick.market_id`'s
  `market_created_at <= T`.
- ✓ All existing per-base_asset Polymarket parquets migrated to canonical-group shape; partial bundles flipped to
  `attempted_failed[ClusterCoverageError(historical)]` for re-attempt.
- ✓ Residual `category=prediction` legacy hive vocab migrated; legacy fallback reader deleted.
- ✓ Data-status UI surfaces per-canonical_group + per-market drill-down + lifecycle states.
- ✓ Honest coverage baseline measured per canonical_group; ratchet floor activated.
- ✓ Workspace-wide QG green.
- ✓ writegate plan's `PREDICTION_GROUPS = {}` empty registry temporary state resolved.
