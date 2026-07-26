---
doc_type: codex-ssot
title: Post-Plan Reality — Pointer for Fresh Agents (2026-05-06)
summary:
  Fresh-agent override pointer for the 2026-05-06 writegate-honest-coverage work-package — lists the 10 cross-cutting
  principles (honest coverage, single-SSOT, live=batch, A/B/C empty-output tree, mandatory cluster validation, per-VM
  shard isolation) and enumerates every stale codex + per-service doc carrying a banner back to it.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    features-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags:
  [honest-coverage, data-correctness, ssot-audit, manifest, cluster-validation, single-walk, live-trading, migration]
related: [02-data/availability-manifest-and-data-status.md, 06-coding-standards/validation-and-errors.md]
created: 2026-05-06
authoritative_for: [2026-05-06 writegate post-plan reality (10 cross-cutting principles + stale-doc banner registry)]
referenced_by: [/codex/10-audit/MASTER_READINESS_LIVE_DEFI_2026_05_23.md]
owner:
last_reviewed:
code_refs:
type: stale-doc-pointer
---

# Post-Plan Reality — Pointer for Fresh Agents (2026-05-06)

**STOP** — if you're a fresh agent reading codex / per-service docs to make a code or doc change, read this FIRST.
Several codex docs and per-service docs predate the writegate-honest-coverage work-package landing 2026-05-06 and will
lead you to undo work-in-progress that's already been agreed with the user. This doc tells you (a) what changed at the
principle level, (b) which docs are stale and how, (c) where to read the canonical post-plan reality.

---

## The 10 cross-cutting principles codified 2026-05-06

These are now in workspace `unified-trading-pm/cursor-configs/CLAUDE.md` (search for the section names below). Per-repo
`CLAUDE.md` symlinks inherit them. Any doc in the codex or in a service that contradicts one of these is stale and needs
to be read with this doc as the override.

1. **Production-grade `>99%` means real `>99%`.** No silent NaN placeholder rows. No partial bundles passing manifest as
   `captured`. No silent per-schema drops on bundled writes. Coverage % is honest only when the denominator is clipped
   to legitimately-coverable shards AND the numerator counts only honest captures.
2. **Single SSOT only — no double-SSOT in data-saving methodology.** Where two paths produce the same outcome, one is
   deleted. Killed coexistence: `_create_empty_output()` AND `_handle_empty_tick_data()` (writegate Phase 2.A);
   `_ensure_timestamp` shim AND per-source `stamp_available_at_*` (writegate Phase 2.C); v3-shape
   `_write_manifest_records` AND v6 canonical writer (writegate Phase 2.A); inline NaN-ratio gate AND UTL
   `write_gate_helper` (Plan B); per-service phantom-audit drift probe AND UTL `manifest_audit` (Plan B).
3. **Schema, manifest, GCS, code rewrites sanctioned wherever the SSOT requires.** No backwards-compatibility shims. No
   fallback readers for legacy shapes (one documented exception: hive-vocab `category=` → `asset_group=` per existing
   CLAUDE.md asset-group section). Migration scripts replace fallback readers; fallback readers get deleted.
4. **Live = batch — same data, same fields, same timing semantics, different sources OK.** Only the SOURCE differs.
   Historical writes timestamped with the `available_at` we'd actually have in live mode (the
   `unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY` top entry's emission time, NOT the
   canonical historical archive's slower archive time). Banned: separate live-only data_types like `LINEUPS_PRE_MATCH`
   vs `LINEUPS_POST_MATCH`; field sets that diverge between live + batch parquets.
5. **`available_at` is per-row, write-time, equal to live-pipeline-arrival.** Per-source rules in UAC
   `availability_semantics.AVAILABILITY_AT_SEMANTICS`. NEVER derived at read-time. UTL `record_captured` calls
   `assert_available_at_present` internally.
6. **Cluster validation MANDATORY at `record_captured` for bundled shards.** No opt-out. No helper-call-pattern. Runtime
   guard (UTL `MissingClusterValidationError`) + static guard (QG STEP 5.64). Bundled types: `options_chain` (ES.OPT
   11-cluster), `futures_chain` (per-root spreads/butterflies), `prediction_canonical_question_group`
   (per-canonical-group market_id sets), `ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE` (per-league-tier expected
   bookmaker sets).
7. **Three-category empty-output decision tree.** Every condition that could produce an empty result resolves to ONE of:
   **A. Source returned 0 ticks for window** → `record_empty(row_key, attempted_at)` (honest absence); **B. Source
   returned ticks; ALL fall outside the requested day after `interval_idx` filter** →
   `record_failed(UpstreamTimestampBiasError)` (UPSTREAM bug — partition mislabeled OR source replay covered wrong
   window OR clock-skew; paired upstream MTDS partitioner-validation fix); **C. Rows in window but downstream calc
   dropped due to malformed source fields** → `record_failed(MalformedTickFieldError)`. NO fourth category. NO silent
   NaN placeholder rows. `_create_empty_output()` is BANNED from `base_adapter` and equivalents.
8. **Temporary state must have named successor plan.** No silent "fix later." Every partial implementation lists its
   named successor plan in a `## Temporary states + their canonical follow-up plans` section. Reviewers reject any
   partial implementation lacking a successor reference.
9. **Per-VM shard isolation for concurrent backfills.** Every multi-worker backfill sets `VM_NAME=<unique>` +
   `MANIFEST_PER_VM_SHARDS=true` per worker. Runtime guard (UTL) + QG STEP 5.66.
10. **Prediction market lifecycle timing.** Instrument definitions in instruments-service capture `market_created_at` /
    `resolution_time` / `settlement_time` per market_id. MTDS respects lifecycle bounds (no capture before created, no
    new capture after settlement). LookaheadBiasError per-market-aware.

---

## Active plans (CANONICAL post-plan reality lives here)

Read these before any doc edit + before any code change in the affected scopes:

- [`writegate_honest_coverage_endtoend_2026_05_06.md`](plans/active/writegate_honest_coverage_endtoend_2026_05_06.md) —
  primary contract change to `ManifestWriter.record_captured` covering MDPS empty-output A/B/C, cluster validation
  mandatory, sports per-fixture_id sharding, sports `available_at` correctness, MDPS v6 columns wiring, retrospective
  migration. Status: drafted, Phase 0 audit synthesised, Phase 2.B amendment F pending Ikenna review.
- [`predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md`](plans/archive/predictions_canonical_question_group_polymarket_migration_2026_05_06.plan.md)
  — Polymarket + Kalshi shard migration to canonical_question_group; UAC `CanonicalQuestionGroup` enum + classifier with
  stability hash; per-market lifecycle timestamps in instruments-service; MTDS adapter migration with cluster
  validation; GCS migration of existing per-base_asset parquets.
- [`_writegate_plan_rationale_and_followup_design_2026_05_06.md`](/plans/ai/_writegate_plan_rationale_and_followup_design_2026_05_06.md)
  — meta document explaining design rationale + 4-plan packaging (A=predictions, B=UTL/UAC lift triple, C=pre-flight +
  concurrency, D=multi-source merge) + end-to-end production-grade execution requirements + anti-patterns this
  work-package rejects.
- [`shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`](plans/active/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md)
  — parent HANDOVER. Phase 0 audit findings synthesised. Item 1 (cluster validation) and parent Phase 1 Tier 1 #1 +
  Phase 1 Tier 2 raw-tables marked SUPERSEDED with link to writegate plan.
- [`shard_granularity_ssot_propagation_2026_05_06.plan.md`](plans/archive/shard_granularity_ssot_propagation_2026_05_06.plan.md)
  — parent plan. Some phases superseded (linked).

---

## Per-asset-group post-plan reality

### CeFi (spot/perp/options/futures)

- **Spot/perp**: shard atom `(asset_group, venue, data_type, instrument_type, instrument_id, day)` — per-instrument.
  `quote_asset` + `margin_type` v6 columns wired at MTDS write (DERIBIT inverse vs linear disambiguation). MDPS adapters
  wire same columns at `canonical_writer.add()` per writegate Phase 2.A.
- **Options/futures**: shard atom `(asset_group, venue, data_type, options_chain|futures_chain, root, day)` — bundled by
  root. Cluster validation MANDATORY: `expected_root_clusters` per-root cluster taxonomy in UAC. ES.OPT 11-cluster
  taxonomy is the seed; futures_chain greenfield (per writegate plan). `combo_type` + `leg_weights` v6 columns wired at
  MTDS write.
- **Empty-output handling**: 37 `_create_empty_output` callsites in MDPS being migrated to A/B/C decision tree per
  writegate Phase 2.A. `_create_empty_output` deleted from `base_adapter`. Banned pattern.

### TradFi (futures / options / ETFs / VIX)

- **Futures (ES/MES/BTC/ETH/MBT/MET on CME)**: bundled by root. Cluster validation per `FUTURES_CLUSTERS` registry in
  UAC (greenfield seed in writegate Phase 1B; ES + MES seeds; expand per-root). Non-trading-day pre-skip via
  `venue_trading_calendar` + `record_empty`.
- **Options (ES.OPT 11-cluster)**: bundled by root. Cluster validation per `OPTIONS_CLUSTERS` registry (lifted from
  instruments-service to UAC per writegate Phase 1B). Combo spreads carry `combo_type` + `leg_weights`.
- **ETFs (IBIT/ETHA on NASDAQ)**: per-instrument shard (not bundled). MVP universe trimmed: BATS/Arca ETFs dropped per
  existing memo `project_tradfi_mvp_etf_scope_reduction_2026_05_05.md`.
- **VIX 15m**: 3-region source layering (Barchart historical preload Jan 2020 → Nov 2025; Yahoo 60d rolling; honest gap
  Nov 2025 → today−60d). Already in CLAUDE.md `§ VIX 15m source layering`.
- **Databento weekly-series**: requires UAC enrichment `DatabentoClassification.root_cluster: str` field for E1A/EW1/EOM
  cluster extraction (writegate Phase 2.B in-scope todo).
- **Futures expiry_bucket**: requires UAC helper `derive_expiry_bucket(symbol, today)` for cluster validation (writegate
  Phase 2.B in-scope todo).

### DeFi (per-chain protocols)

- **Shard atom**: `(asset_group=defi, chain, venue/protocol, data_type, instrument_id_or_protocol_id, day)` — `chain` is
  a first-class v5 axis. Pre-genesis dates per chain → `empty_confirmed`.
- **`category=defi` legacy on disk**: preserved per CLAUDE.md asset-group section; readers try canonical
  `asset_group=defi` first, fall back to legacy. Do NOT rekey on-disk data.
- **GMX multi-chain**: currently `chain=""`; per-chain Tier-2 fan-out per writegate Phase 2.B. (GMX removed 2026-07-25 —
  see `plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`; this line is now moot.)
- **Empty-output handling**: same A/B/C decision tree as CeFi for any DEX adapter.

### Sports (per-fixture)

- **Shard atom**: `(asset_group=sports, source, data_type, league_id, day)` — `fixture_id` is a row-level column inside
  the parquet, NOT a shard axis (per Q1 resolution; supersedes the earlier 2026-05-06 per-fixture sharding proposal).
  Per-fixture `data_types` (`ODDS_SNAPSHOT`, `ODDS_MOVEMENT`, `ARBITRAGE`, `FIXTURE_STATS`, `FIXTURE_EVENTS`,
  `FIXTURE_LINEUPS`, `FIXTURE_PLAYER_STATS`, `INJURIES`) use cluster validation
  (`cluster_extractor=lambda row: row["fixture_id"]` or `bookmaker` for ODDS\*\*) to enforce per-fixture coverage within
  the parquet. Aggregate data_types: `STANDINGS`, `LEAGUES`, `TEAMS`, `REFEREES`, etc. share the same shard atom (no
  cluster validation needed for inherently-aggregate data). Avoids ~10× manifest-row inflation vs treating `fixture_id`
  as a shard axis.
- **`available_at` per data_type**:
  - `fixtures` → `announced_at` (currently low-confidence `kickoff_utc − 7d` fallback; named successor
    `sports_forward_poll_timestamps_2026_<TBD>.plan.md`)
  - `fixture_lineups` → `kickoff_utc − 60min` (live = batch; conservative — actual is at LEAST 60min before, often 1-2h)
  - `fixture_events` → per-row `event_time` derived from `kickoff_utc + elapsed_min × 60s`
  - `injuries` → `report_time` / `occurrence_time` per row (currently low-confidence
    `kickoff_utc − injury_lead_time_estimate` fallback; named successor as above)
  - `fixture_stats` / `fixture_player_stats` → `match_end_time` (detected via cascade: api_football native → SFI
    progressive-stats freeze → footystats / understat → low-confidence `kickoff_utc + 120min` fallback)
  - 8 reference tables (players / venues / leagues / teams / referees / coaches / standings / rounds) →
    `fetch_completed_at` from `_FETCH_COMPLETED_AT` cache in `_fetch_runner.py`
- **Cluster validation**: `ODDS_SNAPSHOT` / `ODDS_MOVEMENT` / `ARBITRAGE` bundled with
  `cluster_extractor=lambda row: row["bookmaker"]` and `SPORTS_FIXTURE_CLUSTERS` per league-tier (UAC seeds tier-1 EU
  football; expand per follow-up).
- **4 stub exports silently writing empty parquets** (Phase 0 audit finding 2026-05-06): `fixture_lineups`,
  `fixture_player_stats`, `coaches`, `rounds` — wire each to `record_empty(row_key)` if source has no data, OR implement
  source fetch (writegate Phase 2.C prerequisites).
- **`_ensure_timestamp` shim**: scheduled for deletion per writegate Phase 2.C. Do not add new callsites.
- **Sports phantom recovery (concurrent stream)**: live VM `af-backfill-20260506-135454` running ~10h FIXTURES
  backfill + chain runner queues 5 follow-on entity VMs. Don't kill or revert without coordination. Per writegate plan
  §"Concurrent in-flight stream".

### Prediction (Polymarket / Kalshi)

- **Current shard atom**: `data_type=<base_asset>` (BTC / ETH / SPX / FOOTBALL / OTHER). **Stale**.
- **Post-plan shard atom**:
  `(asset_group=prediction, venue, data_type=prediction_canonical_question_group, canonical_question_group, day)` —
  `market_id` is a row-level column inside the parquet, NOT a shard axis (per Q1 resolution). Cluster validation with
  `cluster_extractor=lambda row: row["market_id"]` enforces per-canonical-question coverage within the bundle. Migration
  in Plan A predictions.
- **Canonical question groups**: `CanonicalQuestionGroup` enum (UAC) — `BTC_UP_DOWN_HOURLY` (24/day),
  `BTC_UP_DOWN_DAILY`, `SPX_UP_DOWN_DAILY`, `ELECTION_PRESIDENT_2028`, etc. Long tail handled by classifier with
  stability hash; headline markets handled by `POLYMARKET_CONDITION_ID_TO_GROUP` / `KALSHI_TICKER_TO_GROUP` overrides.
- **Lifecycle**: per-market `market_created_at` + `resolution_time` + `settlement_time` captured in instruments-service.
  MTDS respects lifecycle bounds (no capture before created, no new capture after settlement).
- **`available_at` per row** = tick timestamp + scrape latency (live = batch).
- **NEW BUG**: orchestrator prediction empty path returns `success=True, candles_generated=0` with NO manifest record
  (Phase 0 audit finding 2026-05-06). Fix in writegate Phase 2.A scope expansion.
- **Polymarket residual `category=prediction` GCS objects**: `migrate_polymarket_canonical.py` migration runbook in
  writegate Phase 3.B + Plan A Phase 3.B.

---

## Stale codex docs — banner-pointer added

The following codex docs have a banner at top pointing here. The banner does NOT mean the doc is wrong about everything
— only that there are sections that contradict the post-plan reality. Read the banner + this doc + the active plans
before believing anything specific in the linked doc.

| Doc                                                | Stale because                                                                                                                                                                                         |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `02-data/availability-manifest-and-data-status.md` | Doesn't reflect 4-pillar write-gate (row-count + NaN-ratio + schema + cluster-coverage), `record_empty` / `record_failed` typed reasons, per-VM shard isolation rule, per-fixture sharding for sports |
| `02-data/per-asset-group-bucket-layouts.md`        | Uses `category=` legacy hive vocab. `asset_group=` is canonical; `category=` is legacy-preserved.                                                                                                     |
| `02-data/sports-scheduling-and-sharding.md`        | Pre-(per-fixture sharding) — needs update to reflect `(source, data_type, league_id, fixture_id \| day-aggregate, day)` v5/v6 shard atom                                                              |
| `02-data/sports-data-source-coverage-matrix.md`    | Pre-`SOURCE_PRIORITY` registry; doesn't list multi-source merge rules                                                                                                                                 |
| `02-data/mtds-data-source-coverage-matrix.md`      | Same — missing `SOURCE_PRIORITY` SSOT reference                                                                                                                                                       |
| `02-data/canonical-schema-groups.md`               | Doesn't list `available_at` as a required column on every row                                                                                                                                         |
| `02-data/prediction-schema-paths.md`               | Pre-canonical_question_group; describes per-base_asset Polymarket sharding                                                                                                                            |
| `04-architecture/sports-integration-plan.md`       | Pre-(per-fixture sharding)                                                                                                                                                                            |
| `04-architecture/asset-class-ownership.md`         | Sports section pre-(per-fixture sharding)                                                                                                                                                             |
| `06-coding-standards/validation-and-errors.md`     | Merged 2026-05-08 (D.5) — supersedes the legacy `error-handling.md` / `validation-patterns.md` / `schema-validation.md`. 4-category empty-output decision + cluster validation pillar both included.  |
| `00-SSOT-INDEX.md`                                 | Top-level pointer doc — needs to surface this post-plan doc + the active plans                                                                                                                        |

---

## Stale per-service docs — banner-pointer added

| Doc                                                                                             | Stale because                                                                                                                                                          |
| ----------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruments-service/docs/PREDICTION_INSTRUMENTS.md` (renamed from `POLYMARKET_PREDICTION.md`)  | **RESOLVED 2026-07-08** — fully rewritten as part of the 17→7 docs consolidation, no longer stale                                                                      |
| `instruments-service/docs/SPORTS_INSTRUMENTS.md`                                                | **RESOLVED 2026-07-08** — fully rewritten as part of the 17→7 docs consolidation, no longer stale                                                                      |
| `market-tick-data-service/docs/ARCHITECTURE.md`                                                 | Pre-3-category empty-output + pre-cluster-validation-mandatory                                                                                                         |
| `market-tick-data-service/docs/DATA_TYPE_DECISIONS.md`                                          | Pre-`SOURCE_PRIORITY` + missing per-fixture sharding for sports adapter                                                                                                |
| `market-tick-data-service/docs/DATABENTO_FUTURES_DOWNLOAD.md` + `DATABENTO_OPTIONS_DOWNLOAD.md` | Missing `DatabentoClassification.root_cluster` weekly-series cluster note                                                                                              |
| `market-tick-data-service/docs/DEFI_DOWNLOAD_STRATEGY.md`                                       | Missing GMX multi-chain Tier-2 fan-out (moot — GMX removed 2026-07-25, see `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`); pre-3-category empty-output |
| `market-data-processing-service/docs/ARCHITECTURE.md`                                           | Describes `_create_empty_output` flow that's being deleted                                                                                                             |
| `market-data-processing-service/docs/ERROR_HANDLING.md`                                         | Pre-3-category empty-output decision tree                                                                                                                              |
| `features-service (sports family)/docs/ARCHITECTURE.md`                                         | Missing 4 stub-export wiring + `_FETCH_COMPLETED_AT` cache + per-table `available_at` semantics                                                                        |
| `features-service (sports family)/docs/SCHEMA_VALIDATION.md`                                    | Missing `available_at` column required + per-row stamping rules                                                                                                        |
| `deployment-service/docs/ARCHITECTURE.md`                                                       | Missing per-VM shard isolation rule (`MANIFEST_PER_VM_SHARDS=true` + unique `VM_NAME`) for concurrent backfills                                                        |

---

## Workflow note for the fresh agent

Direct git workflow, NOT quickmerge — confirmed user direction 2026-05-06. `git add` + `git commit` +
`git push origin live-defi-rollout` directly. Skip the two-pass model. Skip `quickmerge`.

Before every commit + push: `git fetch origin` → list incoming commits → for each: compatible (rebase + continue),
touches plan files (read diff, adapt or flag), direct conflict (DO NOT revert silently — flag with hash + author +
file:line + summary, pause that file, continue on unaffected files).

If you're working on a task that overlaps the writegate or predictions plan scope, READ THE PLAN FIRST. If the plan says
something different from this doc or another codex doc, the plan wins. If the plan and CLAUDE.md disagree, flag it to
Ikenna — don't decide unilaterally.
