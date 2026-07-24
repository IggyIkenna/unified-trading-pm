---
doc_type: plan
title: Shard-Granularity SSOT Propagation — Plan
summary:
status: phase-1-tier-1-partial-shipped
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
created: "2026-05-06"
type: plan
companion_handover: shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md
locked_by: live-defi-rollout
locked_since: 2026-05-06
owner: harsh
auditor: claude
---

## Deferred work — migrated to: `plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md`,

`plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md`,
`plans/active/issues/manifest_writer_record_captured_available_at_never_persisted_2026_07_13.md`,
`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md` — successor:
writegate_honest_coverage_endtoend_2026_05_06, sports_p2_features_history_to_ml_ready_2026_06_27,
manifest_writer_record_captured_available_at_never_persisted_2026_07_13,
mtds_available_at_cross_asset_backfill_2026_07_13 (the Phase 0→1 gate + MDPS 1440-NaN repro are stale
process/superseded-shipped; the sports raw-tables `available_at` migration is actively owned by
`sports_p2_features_history_to_ml_ready_2026_06_27.md`; the Phase-2 validation checklist's `available_at` end-to-end
smoke item is owned by the two `available_at` plans above, and its remaining 6 generic acceptance-criteria items are
distributed across current canonicalisation plans rather than independently orphaned. No genuinely orphaned items found.
NOTE: `locked_by: live-defi-rollout` was never cleared at archival — flagged for operator `[unlock-plan]` cleanup.)

# Shard-Granularity SSOT Propagation — Plan

**Branch:** `live-defi-rollout` **Status:** Phase 0 audit in progress (started 2026-05-06). **Companion handover:**
`shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`

---

## Context

Most of the v5 manifest + shard-granularity work already shipped across prior plans. **This plan is a redo-and-test
verification pass to confirm end-to-end consistency, not greenfield.** Goal: every shard atom is identical across (a)
writer atomicity, (b) manifest row key, (c) data-status display, (d) downstream pre-flight gate, (e) deployment-UI
drill-down. Drift between any two = silent correctness bug.

Triggering incidents (see handover for detail):

- TradFi MVP partial bundles (ES.OPT 18/839 historical bundles passed manifest as captured)
- MDPS empty-placeholder bars (1440 NaN OHLC bars/day/venue for years)
- Databento per-schema silent drop on 429

Co-evolving streams (do NOT duplicate — handover Items 1/2/3):

1. Cluster-aware bundle validation (lands in UTL `ManifestWriter.record_captured`)
2. Databento 429 silent-drop fix (MTDS `databento_adapter.download_batch_df`)
3. VIX forward-poll wiring (`umi_tick_provider.py`)

**Coordination rule:** if audit findings overlap Items 1 or 2, comment in this plan + continue auditing — don't ship a
parallel fix.

---

## Phase 0 — Per-Service Audit (in progress)

Audit only. No code changes in this phase. Findings appended to `## Audit Findings` below as each service completes.
Format per service:

- ✓ items that match target shape
- ❌ items that don't match (writer / pre-flight / available_at / write-gate / migration / UI)
- 🔀 items implemented in the wrong layer
- ❓ items where verification needs codex pointer or clarification

### Audit DAG

```
Phase 0.1 (sequential, anchors row-key shape)
    └── instruments-service

Phase 0.2 (parallel after 0.1 establishes baseline)
    ├── market-tick-data-service (MTDS)
    ├── market-data-processing-service (MDPS)
    └── features-onchain-service / features-sports-service / features-delta-one-service

Phase 0.3 (synthesis)
    ├── Consolidated migration list (manifest drift instances + estimated shape)
    ├── Consolidated UTL-lift list (utilities currently duplicated per-service)
    └── Prediction canonical-question-group SSOT check in UAC
```

### Phase 0 Todos

- [x] [AUDIT] P0. instruments-service — writer / pre-flight / available_at / write-gates / dual-vocab probe /
      per-instrument progress events
- [x] [AUDIT] P0. market-tick-data-service — same checklist + scan every adapter for `except: continue` swallowing
      per-schema/per-instrument failures (skip databento_adapter.py — being fixed in parallel)
- [x] [AUDIT] P0. market-data-processing-service — same + reader-vs-writer drift (1440-empty-bars incident pattern)
- [x] [AUDIT] P0. features-onchain-service — same + LookaheadBiasError coverage + DAG-input pre-flight granularity
- [x] [AUDIT] P0. features-sports-service — same + sports temporal availability stamping rules (lineups / injuries /
      pre-match odds / post-match / weather)
- [x] [AUDIT] P0. features-delta-one-service — same + LookaheadBiasError coverage
- [x] [AUDIT] P0. UAC prediction canonical-question-group SSOT — verify mapping raw Polymarket market_id → canonical
      question group exists; flag as build item if missing
- [x] [AUDIT] P0. Consolidated migration list — manifest drift instances per service + estimated migration shape
- [x] [AUDIT] P0. Consolidated UTL-lift list — cross-service utilities currently inlined per-service

### QG between phases

- [ ] Phase 0 → Phase 1: handover sign-off on audit findings; user converts findings into per-service fix todos in Phase
      1 below.

---

## Phase 1 — Per-Service Fixes (in progress)

Phased fix work derived from Phase 0 findings. Each fix is tagged with placement layer (`[UAC]`, `[UTL]`,
`[per-service]`, `[deployment-api]`, `[deployment-ui]`). Items overlapping co-evolving Items 1/2 stay in the parallel
stream — not added here.

### Phase 1 Tier 1 — Ship-blocker correctness bugs

#### Shipped 2026-05-06 (Claude session)

- [x] **#2 instruments-service per-league pre-flight** — `instruments_service/engine/orchestrator.py` switched from
      coarse `_should_skip_shard(row_key={date, data_type})` to `_should_skip_date_for_per_league(...)` for
      **SFI_PROGRESSIVE_STATS** and **PLAYER_VALUES**. Same shape as 2026-05-05 MATCHES 18%-coverage incident. Behavior
      change: dates with N/M expected leagues captured now re-attempt until all M are captured (costs more API calls
      during convergence; stops permanent per-league lockout). SFI_STANDINGS retracted from fix list — code path is
      dead. Repo: `instruments-service@live-defi-rollout` commit `7bfa877`.
- [x] **#3 MTDS umi per-instrument silent drops** — `market_tick_data_service/adapters/umi_tick_provider.py:583/740/925`
      book-snapshot `except: continue` swallows replaced with `PerLeafFailureRouter.record(...)` calls that route
      per-coin failures through the new UTL helper. Same fix applied to parallel HTTP-non-200 silent paths.
      `logger.debug` → `logger.warning` at all 6 sites for immediate visibility. Orchestrator constructs per-venue
      router, aggregates into `failed_per_instrument_by_venue`, flushes into `writer_manifest` after sentinel pass so
      each per-coin failure becomes a `record_failed` row + `ADAPTER_FETCH_FAILED` event. Repo:
      `market-tick-data-service@live-defi-rollout` commit `1258d5c`.
- [x] **#4 features-sports PIT enforcement loud in batch** — `features_sports_service/data/writer.py:65-66`
      `try/except LookaheadBiasError:     pass` swallow removed; `PointInTimeEnforcer(strict=False)` switched to
      `strict=True`. Future-timestamped observations now raise `LookaheadBiasError` on the first leaking row instead of
      being logged-and- ignored. Behavior change: batches with leaks fail loud rather than silently producing leaky
      features. Repo: `features-sports-service@live-defi-rollout` commit `03b05f5`.

#### Paused — needs direction (cross-service contract change)

> **2026-05-06 update — SUPERSEDED by
> [`writegate_honest_coverage_endtoend_2026_05_06.plan.md`](./writegate_honest_coverage_endtoend_2026_05_06.plan.md).**
> User direction landed 2026-05-06: option (a) typed exception expanded into a three-category A/B/C decision tree (path
> A `record_empty`, path B `UpstreamTimestampBiasError` with paired MTDS partitioner-validation fix, path C
> `MalformedTickFieldError`). `_create_empty_output` deleted entirely from `base_adapter`. All 53 callsites converted in
> writegate plan Phase 2.A. Item 1 cluster validation folded into the same plan as a unified contract change to
> `record_captured`. Sports per-fixture_id shard-granularity (was deferred Q #9) also moved in-scope. Sports raw-tables
> `available_at` migration (Phase 1 Tier 2 below) likewise moved into the writegate plan Phase 2.C/2.D. Track all
> execution there; the todos below are kept for traceability.

- [ ] **#1 MDPS 1440-NaN reproduction path** — `market-data-processing-service`
      `app/adapters/defi/swap_adapter.py:106` + `app/adapters/cefi/trades_adapter.py:74` (15 more sites suspect)
      actively producing 1440 NaN OHLC bars when ticks are present but all fall outside valid intervals. Fix needs a
      contract change between adapter (`CandleOutput` return) and orchestrator (`record_empty` routing). Three candidate
      shapes:

      | Shape | Pros | Cons |
                                  |---|---|---|
                                  | **(a) Typed exception** `EmptyAfterIntervalFilter` raised in adapter, caught in orchestrator → `record_empty(row_key=...)` | • CandleOutput shape stays invariant (no downstream consumer changes) <br>• Mirrors how MDPS already shard-isolates per-instrument failures via `continue` <br>• One change site per adapter (raise instead of return placeholder) <br>• Honest: clearly signals "tried, no usable data" not "fake bars" | • Adds a new exception type that orchestrator must catch in 2-3 spots |
                                  | (b) Zero-row CandleOutput | • No exception machinery <br>• Already legal Python | • Every consumer of CandleOutput has to handle empty case (audit found 5+ sites that don't currently) <br>• Easy to confuse "intentional empty" with "bug returning zero" |
                                  | (c) `is_empty: bool` flag on CandleOutput | • Backward-compat with current callers | • Every consumer must check the flag → high risk of "forgot to check" silent leak <br>• Same anti-pattern as the bug we're fixing |

                                  **Claude recommends (a) typed exception**. ~2-3 adapters need the raise;
                                  orchestrator's `_handle_empty_tick_data` extends to also catch the typed
                                  exception. `defi/swap_adapter.py:106` + `cefi/trades_adapter.py:74` are the
                                  confirmed reproduction paths; the 15 other suspect `_create_empty_output` sites
                                  get audited before/while shipping.

                                  Overlaps Item 1 (cluster validation) `record_captured` surface — handover
                                  coordination rule says ping first. **AWAITING USER DIRECTION** on contract
                                  shape choice + whether to ship now or stage with parallel-stream Item 1.

### Phase 1 Tier 2 — UTL/UAC lifts that unblock multiple services

#### Shipped 2026-05-06 (Claude session)

- [x] **LIFT-7 PerLeafFailureRouter** — UTL helper for shard-level failure isolation. Lifts the canonical pattern from
      `market-tick-data-service/cli/handlers/_defi_manifest.py:DefiManifestRecorder.     record_failed` into a
      row_key-shape-agnostic helper. Replaces workspace-wide `except: continue` + `logger.debug` anti-pattern. API:
      `router.record(row_key=...,     error=exc, context=...)` inside per-leaf loops, `router.flush_to_manifest(writer)`
      once after; emits one `record_failed` row + one `ADAPTER_FETCH_FAILED` event per leaf with venue-classified error
      code. Best-effort flush (manifest write errors warn-logged; `log_event` `RuntimeError` swallowed). 9 unit tests
      cover classification fallbacks, multi-leaf flush, single-leaf failure isolation, attempted_at handling, top-level
      export, smoke integration with real `ManifestWriter`. Exported from `unified_trading_library`. Already consumed by
      MTDS umi (#3 above). Repo: `unified-trading-library@live-defi-rollout` commit `ab94432`.
- [x] **LIFT-3 availability_stamping** — UTL per-source `available_at` stamping helpers implementing the handover's
      sports temporal-availability table. Functions: `stamp_available_at_lineups(df, kickoff_col=, pre_kickoff_offset=)`
      (kickoff-60min default), `stamp_available_at_event_time(df, event_time_col=)` (generic for injuries / pre-match
      odds / weather forecast-issue),
      `stamp_     available_at_post_match(df, match_end_col=, kickoff_col=, default_match_     duration=)`
      (match*end_time with kickoff+120min fallback for NaT rows),
      `stamp* available_at_offset(df, kickoff_col=,     offset=)`(generic kickoff+offset),
      `stamp_available_at_explicit(df,     when=)`(one-shot snapshot pulls). All raise `AvailableAtStampingError`loud on
      missing columns / all-NaT results — no silent midnight fallbacks. All return copies (never mutate input). 22 unit
      tests cover every helper + edge cases (empty df, naive datetime, fallback paths, custom offsets). Exported
      from`unified_trading_library`. Repo: `unified-trading-     library@live-defi-rollout`commit`cf312f6`.
- [x] **features-sports `_ensure_timestamp` deprecation marker** —
      `features_sports_     service/cli/handlers/batch_handler.py:_ensure_timestamp` docstring updated with
      `⚠️ DEPRECATED INTERIM SHIM` warning + per-export-fn migration guide listing the canonical LIFT-3 helper for each
      source category (lineups → `stamp_available_at_     lineups`; injuries/odds/weather → `_event_time`; post-match
      (xG/fixture_stats/ results/sfi_progressive/derived_features/fixture_features) → `_post_match`). Function body
      unchanged (still writes midnight UTC) — actual removal requires per-export-fn surgery to inject the right
      `available_at` column at source. Repo: `features-sports-service@live-defi-rollout` commit `4db8f36`.

### Phase 1 Tier 2 — Remaining (next session)

- [x] **odds_features** (`features-sports-service@d8ef4c3`) — `_pivot_bucketed_to_fixture` derives
      `available_at = max(bm_time)` per fixture/horizon group; `export_odds_features` merges it back from the pivoted
      snapshot after `compute_odds_batch`.
- [x] **derived_features** (`features-sports-service@19cbc74`) — merges `kickoff_utc` from `target_fixtures` per
      `fixture_id` and renames to `available_at` after metadata stamping. `_filter_completed_before` already excludes
      any historical input that hasn't ended, so kickoff_utc is the conservative-correct upper bound.
- [x] **fixture_features** (`features-sports-service@ef4a483`) — both `_build_row` and `_null_row` paths set
      `row[available_at] = kickoff_utc` mirroring the existing `timestamp` column.
- [ ] **Raw tables migration (next slice — needs design)** — 14 entries in `TABLE_TO_EXPORT`. Source-of-truth gap:
      `fetch_runner` doesn't expose a `fetch_completed_at` timestamp, and the post-match raw schemas (FIXTURE_STATS /
      FIXTURE_EVENTS / FIXTURE_LINEUPS / FIXTURE_PLAYER_STATS) don't include `kickoff_utc`. Two options for cleaning
      this up:

      | | Option A (extend fetch_runner) | Option B (extend schemas with kickoff_utc) |
                                  |---|---|---|
                                  | **Touch points** | `_fetch_runner.py` (add `_FETCH_COMPLETED_AT: dict[str, datetime]` module-level cache + `get_fetch_completed_at(table_name)` accessor; populate inside each `run_fetch_*`) + per-export `stamp_available_at_explicit(...)` calls in `exports.py` | Each fixture-keyed schema (FIXTURE_STATS_COLUMNS, FIXTURE_EVENTS_COLUMNS, FIXTURE_LINEUPS_COLUMNS, FIXTURE_PLAYER_STATS_COLUMNS, INJURIES_COLUMNS) gets `kickoff_utc` added; fetch_runner joins fixtures cache when populating each table; per-export uses `stamp_available_at_post_match` |
                                  | **Honesty for post-match** | Wrong: stamps the *fetch time* (when we discovered the data), not match_end_time. Fetch could happen weeks after match end → over-stamps available_at later than truth | Correct: per-fixture match_end_time |
                                  | **Honesty for reference data** | Right: snapshot fetch time | Wrong: reference data has no fixture |
                                  | **Schema migration** | None — purely additive runtime metadata | Schema bump for 5 schemas → potential downstream consumer breakage |
                                  | **Verdict** | Fine for reference data (8 tables: players, venues, leagues, teams, referees, coaches, standings, rounds) but wrong for post-match (5 tables) | Right for post-match, wrong for reference |

                                  **Claude recommends a hybrid**: Option A for the 8 reference tables,
                                  Option B for the 5 post-match tables (FIXTURE_STATS, FIXTURE_EVENTS,
                                  FIXTURE_LINEUPS, FIXTURE_PLAYER_STATS, INJURIES). The 1 remaining
                                  (`fixtures` itself) already has `kickoff_utc` — trivial.

                                  **Blast-radius confirmed 2026-05-06**: `rg` across the workspace for
                                  `FIXTURE_STATS_COLUMNS|FIXTURE_EVENTS_COLUMNS|FIXTURE_LINEUPS_COLUMNS|FIXTURE_PLAYER_STATS_COLUMNS|INJURIES_COLUMNS`
                                  finds matches **only inside features-sports-service** (the schema module
                                  itself, `exports.py`, and two test files). No MDPS / strategy-service /
                                  features-onchain / instruments-service / market-tick-data-service
                                  consumer reads these schema column constants. Schema bump for Option B
                                  is therefore a free contained change — no cross-repo coordination
                                  required. **Hybrid (A for 8 reference, B for 5 post-match) is the
                                  go-ahead for next session**; the only remaining pre-work is implementing
                                  the `_FETCH_COMPLETED_AT` cache in `_fetch_runner` (Option A) and adding
                                  `kickoff_utc` to the 5 fixture-keyed schemas + their fetch_runner
                                  population paths (Option B).

                                  Note: the batch_handler `_stamp_available_at` dispatcher
                                  (commit `52602fe`) ALREADY applies the right rule for both buckets at
                                  the per-export-call site — the source-of-truth fix here is making the
                                  stamp use a real timestamp (fetch-time for reference, match-end for
                                  post-match) rather than the conservative `target_date + 23:59 UTC`
                                  fallback. Until the per-export sources land, the dispatcher's fallback
                                  is honest-conservative (over-stamps available_at slightly later than
                                  truth, never earlier — so it never leaks).

- [ ] **Delete `_ensure_timestamp` shim** — once all 14 raw tables migrate, drop the midnight UTC fallback at
      `batch_handler.py:_ensure_timestamp` entirely.

#### Phase 1 Tier 2 — Additional Shipped 2026-05-06

- [x] **features-sports `manifest.write` swallow** — `batch_handler.py:642-663` previously caught `Exception` with only
      `logger.warning`; a single GCS hiccup silently dropped ALL of the day's manifest rows. Now: narrow except to
      `(ConnectionError, TimeoutError,     OSError, ValueError, RuntimeError)`, log at ERROR with row count lost, route
      through `classify_and_emit_error` with `ErrorCategory.INFRASTRUCTURE` / `ErrorSeverity.HIGH`, and `return False`
      so the caller knows the day failed (shard-level failure isolation preserved — no raise into the per- table loop).
      Repo: `features-sports-service@live-defi-rollout` commit `fc0f297`.
- [x] **MTDS solana_defi datapoint silent drops** — `solana_defi_handler.py:687` (Marginfi TVL) and `:810` (Solend
      chart) previously swallowed parse errors with `except (TypeError, ValueError):     continue` + no count or log.
      Now both sites: count drops per category, debug-log each error with the offending raw value, and emit warn-level
      summary when drop rate is significant (>5% or >5 absolute for TVL; any parse error preventing pool match for
      Solend). Lower severity than umi (per-datapoint corruption of aggregates, not whole-instrument loss) —
      observability fix proportionate to scope. Repo: `market-tick-data-     service@live-defi-rollout` commit
      `7fedfe5`.

### Open dependencies / coordination

- **MDPS empty-placeholder fix (Phase 1 #1)** — needs contract-shape decision; see "Paused — needs direction" above.
- **Cluster validation (Item 1 from handover)** — touches the same `record_captured` surface as MDPS empty-placeholder
  fix. The two should ship together to avoid double- edits to `ManifestWriter.record_captured` semantics.
- **UAC `canonical_question_group` SSOT (BUILD-PRED1..4)** — greenfield UAC build required for Polymarket / Kalshi
  shard-correctness. Independent of the above; can start in parallel.

---

## Phase 2 — Validation (TBD)

- [ ] All affected downstream consumers updated in this plan (no "fix later")
- [ ] Manifest reads + writes use same shard key for every (service, data_type)
- [ ] Data-status surfaces match writer granularity (audit report only — UI fix tracked separately)
- [ ] No fallback paths remain for migrated manifests
- [ ] Tests cover write-gates: row=0 → fail loud, high NaN → fail loud, schema mismatch → fail loud
- [ ] `available_at` end-to-end smoke: write feature at t-24, verify no input row consumed has
      `available_at > kickoff - 24h`
- [ ] QG green per repo touched

---

## Audit Findings

_Findings appended per service as audit progresses. Each section follows the ✓ / ❌ / 🔀 / ❓ structure._

### instruments-service — Shard-Granularity Audit Findings

Audit pass 2026-05-06. Source files: `instruments_service/engine/orchestrator.py` (6107 lines),
`instruments_service/cli/instruments_handler.py` (214 lines), plus 14 manifest-touching scripts under `scripts/`.

#### ✓ Matches target

- **v5 row-key API exists in UTL** — `ManifestWriter.record_captured` / `record_empty` / `record_failed` accept full v5+
  row_key shape including `chain`, `instrument_type`, `instrument_id`, `league_id`, `feature_group`, `model_family`,
  `quote_asset`, `margin_type`, `combo_type`, `leg_weights` (`unified_trading_library/manifest_writer.py:1048-1188`,
  `_ROW_KEY_COLUMNS` at line 383).
- **Pre-launch guard is built into `add()`** — UAC `is_pre_launch_date(data_type, date)` short-circuits writes for
  pre-`SOURCE_COVERAGE_START` / pre-`DATA_TYPE_COVERAGE_START` rows (`manifest_writer.py:708-720`). Comment cites the
  2026-05-04 incident (229,224 pre-launch rows purged).
- **Honest-coverage trio used** — orchestrator distinguishes `record_empty` (legitimate empty, e.g.
  `orchestrator.py:4032`, `4475`, `5206-5218`) from `record_failed` (exception, e.g. `4053`, `4496`, `5395-5409`).
  Failure routes through `_classify_adapter_failure → classify_venue_error` (line 530-543).
- **`_should_skip_date_for_per_league` helper exists and is correctly used in some sites** — solves the per-league
  honest-coverage gap for FOOTYSTATS PREDICTIONS (line 3897) and FOOTYSTATS MATCHES (line 4258 area). Comment at line
  506 documents the 2026-05-05 MATCHES 18%-coverage incident this fixes.
- **Sports per-league `record_empty` for in-season-but-zero-fixtures** — API_FOOTBALL FIXTURES
  (`orchestrator.py:1956-1970`), SFI_PROGRESSIVE_STATS (5335-5343, 5352-5360, 5368-5376) — leagues whose season covers
  the date but had zero output get explicit `record_empty(row_key={..., league_id=lid})` rows. Without this, mid-week
  per-league gaps render as red `missing` instead of `empty_confirmed`.
- **`_classify_adapter_failure` routes through UAC `classify_venue_error`** — error reasons are categorical, not raw
  exception strings (`orchestrator.py:530-543`).
- **TradFi non-trading-day handling is honest** — `is_non_trading_day(venue, date)` from `venue_trading_calendar`
  produces 0-count manifest rows for weekends/holidays (`orchestrator.py:1799-1830`, `2010-2028`). No naive weekday
  filters.
- **PIT `data_available_at` stamped at write-time per source** for sports adapters. Examples:
  - FootyStats predictions: `kickoff_utc - 72h` (line 3918) — verified against 2026-04-17 probe
  - FootyStats odds: `kickoff_utc - 72h` (line 4377)
  - API Football injuries/fixtures: `date + 12h` / `kickoff + 17h` (line 3135, 3271, 3325, 3446)
  - SFI progressive: `kickoff_15:00 + timer_seconds` (line 5283)
  - Pred (Polymarket UP_DOWN): `kickoff_utc - 72h` (line 3918)

#### ❌ Mismatches

- **[pre-flight]** `orchestrator.py:5013-5018` — SFI_PROGRESSIVE_STATS pre-flight reads coarse
  `row_key={"date": date, "data_type": "SFI_PROGRESSIVE_STATS"}` but the writer at `5293-5313` (and the per-league
  `record_empty` at `5210-5218`, `5335-5343`, `5352-5360`, `5368-5376`) writes per-league rows including
  `league_id=...`. Result: if the coarse date-row is captured but a league is missing, the date-level skip permanently
  locks out per-league re-fetch. Same pattern as the 2026-05-05 MATCHES 18%-coverage incident; should use
  `_should_skip_date_for_per_league` like FOOTYSTATS PREDICTIONS (line 3897) does. Fix layer: **[per-service]**.
- ~~**[pre-flight]** SFI_STANDINGS~~ — **RETRACTED on re-read 2026-05-06**: the SFI_STANDINGS code path at
  `orchestrator.py:5133-5168` is gated by `if _filtered_sfi_ids and _want_sfi_standings` and the comment at line
  5134-5136 says "Currently unreachable — `_want_sfi_standings` is hard-coded False because SFI has no standings
  endpoint." Writer only emits one coarse manifest row (5163-5167), no per-league writes outside the dead branch. Not a
  real bug.
- **[pre-flight]** `orchestrator.py:4747-4750` — PLAYER_VALUES (Transfermarkt) pre-flight at coarse
  `row_key={"date": date, "data_type": "PLAYER_VALUES"}`; writer at `4946-4951` records `record_empty` per-league. Fix
  layer: **[per-service]**.
- **[write-gate]** `orchestrator.py:3946-3952` + `4064-4112` — `_validate_predictions_null_rates` is inlined per-data-
  type with hardcoded thresholds (5% for core cols, 20% for potentials). Violations emit a `logger.warning(...)` but the
  parquet is **written anyway** ("writing anyway" comment line 3949). This is the carry-tracer pattern; threshold
  source-of-truth should be UAC per `feature_group`, and violations should produce `attempted_failed` not silent warn.
  Fix layer: **[UTL]** (lift to shared write-gate helper) + **[UAC]** (per-feature_group thresholds).
- **[write-gate]** Workspace-wide gap — no row-count==0 / NaN-ratio / schema-match gate fires at the write boundary.
  `record_captured`'s `_maybe_validate` does schema-only check (warn-only by default; strict mode is opt-in via
  `MANIFEST_STRICT_SCHEMA_VALIDATION=true`). Row-count and NaN-ratio gates absent. Fix layer: **[UTL]** (extend
  `_maybe_validate` or add sibling gate) + **[UAC]** (per-feature_group NaN thresholds).
- **[available_at]** `orchestrator.py:5279-5285` — SFI progressive PIT stamp uses `15:00 UTC` as a **hardcoded common
  match hour** because no per-match kickoff lookup is wired in. This is approximation, not stamping-at-write-time. Late
  matches (e.g. 21:00 UTC kickoff) get `available_at` 6h too early — potential look-ahead leak for downstream features.
  Fix layer: **[per-service]** (lookup `kickoff_utc` from API_FOOTBALL fixtures bucket) or **[UAC]** (sports temporal
  availability helper that fetches kickoff_utc).
- **[available_at]** `orchestrator.py:1990-1995` — Polymarket per-market manifest write uses `data_type=_mkt_str` (e.g.
  `"BTC"`, `"FOOTBALL"`) which **overloads `data_type` with shard-name**. The handover explicitly forbids overloading
  dimensions. The shard-name should be `instrument_id` or a new `canonical_question_group` column, not `data_type`. Fix
  layer: **[UAC]** + **[per-service]**.
- **[migration]** `orchestrator.py:1988-1995` Polymarket manifest write uses `_extract_prediction_shard` (line 2497)
  which does inline `base_asset.split(":")` parsing with hardcoded shard patterns (`UP_DOWN`, `FOOTBALL`). This is the
  canonical-question-group SSOT gap the handover flagged. **No UAC SSOT exists** for raw Polymarket market_id →
  canonical question group (verified by grep). Fix layer: **[UAC build]**.

#### 🔀 Wrong layer

- **[UTL → per-service drift]** `_validate_predictions_null_rates` (orchestrator.py:4064) is a service-local NaN-ratio
  gate that should live in UTL alongside `ManifestWriter` write-gates. Other services likely have a similar inlined gate
  (audit pending — flagged for synthesis phase).
- **[UTL → per-service drift]** `_classify_adapter_failure` (orchestrator.py:530-543) is small but is exactly the kind
  of cross-service utility that should be a shared UTL helper since EVERY adapter does this same try/UAC-classify/
  fallback dance. Verify other services aren't duplicating; if they are, lift.
- **[per-service → UAC]** `_extract_prediction_shard` (orchestrator.py:2497) — the canonical-question-group taxonomy is
  a UAC SSOT concern, not per-service parsing logic.

#### ❓ Couldn't verify

- Whether downstream consumers (MTDS prediction adapter, features-\* prediction calculators) read the Polymarket per-
  market manifest at the same `data_type=_mkt_str` shape, or whether they expect a different column. If they expect
  `instrument_id`, the writer is silently writing rows the readers don't find — phantom equivalent. Cross-check pending
  in MTDS audit.
- Whether the 14 scripts under `instruments-service/scripts/` (rebuild*sports_manifest, rescan*_, fill*missing*_,
  patch_prediction_shards, fix_manifest_venue_casing, etc.) follow the manifest concurrency principle (read-once + TTL
  freshness check + write-time CAS). Backfill scripts that bypass it can mass-overwrite concurrent worker writes. Spot-
  check pending.
- Per-instrument progress events (`INSTRUMENT_PROCESSED` with row_count) — orchestrator emits `PROCESSING_COMPLETED` per
  date and `ADAPTER_FETCH_FAILED` on errors, but I did not verify whether per-instrument or per-shard events with row
  counts exist for the silent-success-with-zero-output detection pattern. Pending.
- Manifest drift on disk — would need to actually list a few canonical bucket prefixes to confirm v5 column shape in
  production parquet. Audit only inspected source-code writers, not on-disk artifacts.

#### Migration items (instruments-service contribution)

- **MIG-1**: Add `canonical_question_group` column to v5 manifest schema (UAC + UTL); migrate Polymarket on-disk rows
  from `data_type=BTC|ETH|...` overload to `canonical_question_group=BTC|ETH|...` + `data_type=PREDICTION_INSTRUMENTS`
  (or similar). Migration script precedent: `instruments-service/scripts/migrate_local_sfi_to_canonical.py`.
- **MIG-2**: SFI_PROGRESSIVE `available_at` rows currently stamped against `kickoff = 15:00 UTC` placeholder need a
  one-time migration to back-fill from `kickoff_utc` once the per-match lookup is wired in. Mark old rows with a
  `available_at_quality=approximate` flag or re-stamp.

#### UTL-lift items (instruments-service contribution)

- **LIFT-1**: NaN-ratio + row-count==0 + schema-match write-gate trio. Single helper
  `validate_shard_or_fail(df, *, feature_group, data_type, threshold_source=UAC) → ValidationResult` lifted to UTL.
  Replaces inlined `_validate_predictions_null_rates` and equivalent logic in other services.
- **LIFT-2**: `_classify_adapter_failure` (orchestrator.py:530-543) — try `classify_venue_error` then fall back to
  exception class name. Probably duplicated across MTDS/features-\*.
- **LIFT-3**: `_should_skip_date_for_per_league` (orchestrator.py:490-527) is service-local but the per-league-skip
  pattern applies anywhere a writer produces per-leaf rows under a coarser key. Generalise to
  `_should_skip_date_for_per_leaf(manifest, date, data_type, expected_leaf_dim, expected_leaf_values, force)`.

### features-delta-one-service — Shard-Granularity Audit Findings

Audit pass 2026-05-06. Source files: `features_delta_one_service/engine/orchestrator.py` (733 lines),
`features_delta_one_service/engine/delta_one_validity_engine.py` (269 lines), 30+ calculators under
`features_delta_one_service/app/calculators/`.

#### ✓ Matches target

- **Shard-level failure isolation** — `_safe_process_instrument` (orchestrator.py:341+) catches errors per-instrument,
  doesn't raise inside the per-instrument loop.
- **`resolve_data_type_for_feature_group`** uses UAC SSOT (`orchestrator.py:339`) with per-asset-group overrides.
- **`validate_batch_completeness`** is called pre-write (orchestrator.py:295) — at least one cross-instrument
  completeness check exists.

#### ❌ Mismatches

- **[writer]** `orchestrator.py:316-326` — `writer.add()` is called **TWICE** with the same payload (lines 316-321 with
  `timeframe=`, lines 322-326 without). Writes **2 manifest rows per processing cycle** for the same shard. Almost
  certainly a refactor leftover. One of these is a bug; either `timeframe=` is required everywhere (delete 322-326) or
  not used (delete 316-321). Fix layer: **[per-service]**.
- **[writer]** Service uses **only `manifest.add()`**. No `record_captured` / `record_empty` / `record_failed` calls
  anywhere in the source tree. The honest-coverage trio is not implemented for delta-one features. So:
  - Failed shards → no manifest row at all (silently absent — line 292 conditions write on `success_count > 0`).
  - Empty/sparse shards → no `record_empty` distinction; if `success_count == 0`, no row written.
  - The 4-pillar write-gate (row=0 / NaN / schema / cluster) does NOT fire — `add()` skips schema validation. Fix layer:
    **[per-service]** (rewrite write-path) + **[UTL]** (the `record_captured` API exists already).
- **[pre-flight]** No `_should_skip_shard` lookup anywhere. Recompute happens unconditionally per-instrument — only
  `force_reprocess` flag governs (same as no skip). Means concurrent backfill / re-run will redo all work since manifest
  isn't consulted. Fix layer: **[per-service]**.
- **[write-gate]** `validate_batch_completeness` returns `(is_complete, missing)`. On incomplete: code logs warning at
  line 303 then **skips manifest write entirely** (line 309 — `else` branch wrapping the writer). So a 50%-complete
  batch leaves **zero manifest rows** for both completed AND missing shards. Anti-pattern. Should `record_captured`
  per-completed-shard + `record_failed` per-missing-shard. Fix layer: **[per-service]**.
- **[write-gate]** `orchestrator.py:328-329` — manifest write failure caught with bare
  `except (ConnectionError, TimeoutError, OSError, ValueError, RuntimeError)` and warning-logged. If GCS hiccups, the
  whole shard becomes invisible to data-status. Should be fatal or `record_failed` route. Fix layer: **[per-service]**.
- **[lookahead] CRITICAL** — `grep -rn LookaheadBiasError` in features-delta-one returned **zero hits**. The 30+
  calculators (`moving_averages.py`, `momentum.py`, `vwap.py`, `economic_events.py`, `kurtosis.py`, etc.) do NOT raise
  `LookaheadBiasError`. The only `available_at` check in the workspace lives in features-onchain `feature_writer.py`.
  Per the handover: "extend to every features-\* calculator." This is the largest single lookahead-bias gap in the
  workspace. Fix layer: **[per-service]** (per-calculator) + **[UTL/UAC]** (mandatory `LookaheadBiasError` extension via
  shared base-class + `feature_group → required_inputs` DAG SSOT).
- **[available_at]** No service-level write of `available_at` column observed in the orchestrator write-path. Need to
  spot-check one calculator (e.g. `vwap.py`) to confirm whether each writes its own `available_at` — high probability it
  doesn't, given the LookaheadBiasError gap. Fix layer: **[per-service]**.

#### 🔀 Wrong layer

- **[per-service]** `validate_batch_completeness` (used at orchestrator.py:295, imported from somewhere — likely
  `unified_trading_library`) sounds like the right utility for completeness validation, but its current usage drops the
  manifest write on incomplete which is the wrong action. The action on incomplete should be `record_failed` per-missing
  shard, not "skip the manifest entirely" — that policy decision is encoded at the call site, not in the helper. Tag as
  per-service rewrite.

#### ❓ Couldn't verify

- Whether ANY of the 30+ calculators stamp `available_at` at write-time. Would need spot-check 3-5 calculators (vwap,
  moving_averages, momentum, kurtosis, economic_events) to confirm or contradict. Listed under per-calculator fix items
  in Phase 1.
- Whether `delta_one_validity_engine.py` (269 lines, not yet read) does any PIT or lookahead enforcement that wraps the
  calculator outputs. If yes, the LookaheadBiasError gap might be partially closed. If no, the gap is total.
- Per-instrument progress events (`INSTRUMENT_PROCESSED`) — orchestrator emits a `BATCH_COMPLETED`-style event after the
  full batch (the `log_event(...)` at line 273-289 includes counts); per-instrument granular events with row counts not
  confirmed. Pending.

#### Migration items (features-delta-one-service contribution)

- **MIG-DO1**: Switch `writer.add()` calls (orchestrator.py:316-326) to `record_captured` / `record_empty` /
  `record_failed`. Delete the duplicate `add()` call.
- **MIG-DO2**: All 30+ calculators need `available_at` stamping at write-time. Per-calculator review + add
  `available_at = compute_input.timestamp + calc_horizon` (or per-source rule).

#### UTL-lift items (features-delta-one-service contribution)

- **LIFT-DO1**: Mandatory `LookaheadBiasError` enforcement across all features-\* calculators — UTL helper that wraps
  every calculator's compute call with PIT enforcement. Currently only features-onchain `feature_writer.py` does this.
  This needs to lift to a shared `feature_calculator_base.py` in UTL that all features-\* services inherit, so
  LookaheadBiasError raises become structural rather than per-service additions.
- **LIFT-DO2**: Manifest write-on-incomplete-batch policy — a UTL helper
  `record_partial_batch(manifest, completed, failed)` that does the right thing (record_captured for completed +
  record_failed for missing), instead of services re-implementing the conditional + dropping the manifest entirely on
  incomplete.

### UAC prediction canonical-question-group SSOT — Audit Finding

Audit pass 2026-05-06. Files inspected: `unified_api_contracts/canonical/domain/prediction/prediction_mapping.py`,
`unified_api_contracts/external/polymarket/`.

#### ❌ Greenfield gap (confirmed)

- **Existing module is a different abstraction**: `prediction_mapping.py` defines `CanonicalPredictionMarket` (per-
  market `PRED:{category}:{hash12}` IDs) and `PredictionMarketCrossVenueMapping` (cross-venue event linking with
  `underlying`, `timeframe`, `strike`). Categories are 7 coarse buckets: POLITICS / FINANCIAL / SPORTS / CRYPTO /
  WEATHER / ENTERTAINMENT / OTHER. Useful but **NOT the shard-atom SSOT the handover specifies**.
- **Missing**: A function `polymarket_market_id_to_canonical_question_group(market_id) → str` returning a stable
  identifier like `BTC_UP_DOWN_1D`, `SPX_UP_DOWN_1D`, `EPL_MATCH_ODDS`, etc. This is the bundling axis equivalent to
  `options_chain` for derivatives. Service-side proxy (`instruments-service/orchestrator.py:_extract_prediction_shard`,
  line 2497) does inline parsing with hardcoded patterns (`UP_DOWN`, `FOOTBALL`).
- **Missing**: A registry of expected `canonical_question_group` values per (venue, day) so write-gates can detect
  partial bundles (e.g. "expected 6 BTC UP_DOWN strikes, only got 4" → `record_failed(ClusterCoverageError)`).
- **Missing**: Cross-venue normalization — Polymarket BTC up/down vs Kalshi BTC up/down should map to the SAME
  `canonical_question_group_id` for downstream cross-venue alpha capture.

#### Build items (UAC prediction SSOT)

- **BUILD-PRED1**: New module `unified_api_contracts/canonical/domain/prediction/canonical_question_group.py` with:
  - `CanonicalQuestionGroup` dataclass: `(group_id, underlying, instrument_type, timeframe, expiry_class)` — parallel to
    `options_chain` shape.
  - `polymarket_market_to_canonical_group(condition_id, question_text, resolution_date) → CanonicalQuestionGroup`.
  - `kalshi_market_to_canonical_group(market_ticker, ...) → CanonicalQuestionGroup`.
  - `EXPECTED_QUESTION_GROUPS_PER_DAY[(venue, date)] → set[group_id]` for cluster-coverage validation.
  - Migration helper to back-fill `canonical_question_group` column on existing on-disk manifest rows, mapping from the
    legacy `data_type` overload (e.g. `data_type=BTC` → `canonical_question_group=BTC_UP_DOWN_1D`).
- **BUILD-PRED2**: Wire `canonical_question_group` as a v6 manifest column (UTL `_ROW_KEY_COLUMNS` already accepts
  optional dimensions; add via plan's manifest schema migration).
- **BUILD-PRED3**: Update `instruments-service/scripts/aggregate_processed_options_to_chain_bundle.py` precedent pattern
  to a sibling `aggregate_polymarket_to_canonical_group_bundle.py` for prediction.
- **BUILD-PRED4**: Update MTDS prediction adapter (`polymarket_adapter.py`, `kalshi_adapter.py`) to read at
  `canonical_question_group` granularity, not `data_type=_mkt_str`.

### features-onchain-service — Shard-Granularity Audit Findings

Audit pass 2026-05-06 by Sonnet sub-agent. Source files: `features_onchain_service/engine/orchestrator.py`,
`features_onchain_service/app/core/feature_writer.py`, `dependency_checker.py`, `mtds_canonical_reader.py`,
`schemas/feature_builder_registry.py`, 25+ calculators under `app/calculators/`.

#### ✓ Matches target

- **Write-gate trio fires** — `OnChainFeatureWriter.write_features` (`feature_writer.py:119-133`) returns False on empty
  DataFrame; `FeatureWriteGate` from UTL evaluated at every write (`feature_writer.py:154-178`); timestamp-date
  alignment validated at 99% (`feature_writer.py:326-348`). Three of the four pillars are honored at the writer.
- **`LookaheadBiasError` from UTL** — imported and raised via `_enforce_point_in_time` (`feature_writer.py:270-324`).
  Strict in production, warn-only in mock mode. The currently-firing case for `lst_yields` is here.
- **Per-day write isolation** — `_process_daily_feature_group` writes one parquet per day with `date=cur` so a single
  bad day doesn't poison the whole window. The pre-2026-05 concat-all-write-once anti-pattern has been fixed.
- **Shard-level failure isolation** — `batch_handler.py:112-136` per-feature-group try/except.
- **Honest progress events** — `LST_DAY_PROCESSED` per-day row counts (`orchestrator.py:654-665`),
  `FEATURE_GROUP_WINDOW_SUMMARY` aggregates, `PERSISTENCE_STARTED/COMPLETED` from actual write site.
- **Domain types from UAC** — `models.py` is a re-export facade over `unified_api_contracts.internal`.
- **Canonical MTDS path probe + dual-vocab fallback** — `mtds_canonical_reader.py` uses `build_defi_partition_path` from
  UAC; legacy `category=defi/` fallback limited to that single substitution.

#### ❌ Mismatches

- **[writer]** `orchestrator.py:163-172` — `ManifestWriter.add` called with only
  `(processing_date, row_count, feature_group)`. **No `chain`, no `venue`, no `instrument_id`, no `data_type`.** DeFi
  target shard is `(asset_group=defi, chain, venue/protocol, data_type, instrument_id_or_protocol_id, day)`. Current
  writer collapses every `(feature_group, day)` to a single row regardless of how many chains × protocols were
  processed. Same partial-bundle bug class as the handover incidents. Fix layer: **[per-service]**.
- **[pre-flight]** `orchestrator.py:108-113` —
  `check_shard_freshness(bucket, date, service_name, expected_venues=[feature_group])` is at `(date, feature_group)`
  only. If `lending_rates` was previously written for ETHEREUM and Arbitrum data arrives later, skip-if-fresh
  **incorrectly reports the shard as fresh**. Pre-flight coarser than writer = silent partial coverage. Fix layer:
  **[per-service]**.
- **[record_empty / record_failed]** — Never called anywhere. Empty-loader days silently `continue`
  (`orchestrator.py:1119-1121`, `_process_lst_yields` at `510-513`). The honest-coverage trio is unused. Fix layer:
  **[per-service]**.
- **[available_at]** — `_add_timestamp_out` (`feature_writer.py:238-268`) adds `timestamp_out` (observation + synthetic
  500ms delay), NOT `available_at`. No calculator stamps `available_at` on output. Downstream consumers reading these
  parquets have no column to check `<= kickoff_or_target_ts - N`. Fix layer: **[per-service]** + **[UAC]** (semantics).
- **[lookahead]** — `LookaheadBiasError` only checks **output observation timestamps vs `as_of_date + 1 day`**, not
  **input rows' `available_at` vs `target_ts - N`**. Structural gap: no calculator can input-check because
  `available_at` is absent from upstream MTDS parquets. The currently-passing lst_yields case is the writer's
  output-side guard, not the input-side rule the handover requires. Fix layer: **[per-service]** + **[UTL]** + upstream
  **MTDS** must stamp `available_at`.
- **[NaN threshold]** `feature_writer.py:61` — `nan_threshold=0.95` hardcoded. Per-feature-group thresholds belong in
  UAC. Fix layer: **[UAC]** + **[UTL]** (`FeatureWriteGate` accept per-group lookup).
- **[feature_group → required_inputs DAG]** `feature_builder_registry.py:59-76` — service-local `_metadata` dict
  declares deps (`aave_rate_impact: [aave_lending_rates, aave_utilization]`, etc.). DAG belongs in UAC SSOT so
  downstream pre-flight checks can also import without duplication. Fix layer: **[UAC]**.
- **[downstream pre-flight checks one upstream bucket, not all DAG inputs]** `dependency_checker.py:41-63` —
  `UPSTREAM_DEPS` is a fixed dict checking MDPS bucket existence + 3 optional MTDS buckets. Does NOT consult the
  feature_group DAG. `rate_impact` can run even if `lending_rates` produced zero rows that day. Fix layer:
  **[per-service]**.
- **[CanonicalDefiShard service-local]** `mtds_canonical_reader.py:39-51` — used by 5 calculators. Cross-cutting shard
  identity descriptor, belongs in `unified_api_contracts.defi` or UTL. Fix layer: **[UAC]**.
- **[manifest concurrency]** No TTL-cached per-date freshness check. Multi-day window processing has no per-day
  re-check. Concurrent workers will duplicate work. Fix layer: **[per-service]** (apply the
  `_refresh_captured_cache + _is_now_captured` pattern from PM CLAUDE.md).
- **[classify_venue_error / ADAPTER_FETCH_FAILED absent]** `data_loader.py` and adapters wrap exceptions with
  `EnhancedError` but never call `classify_venue_error()` or emit `ADAPTER_FETCH_FAILED`. Workspace rule violation. Fix
  layer: **[per-service]**.
- **[CLI/registry inconsistency]** `parser.py:24` `CATEGORIES = ["CEFI", "DEFI"]` but `dependency_checker.py:76`
  references `"TRADFI": "features-onchain-{project_id}"`. Either dead code or missing CLI choice. Fix layer:
  **[per-service]** trim or extend.

#### 🔀 Wrong layer

- `CanonicalDefiShard` (`mtds_canonical_reader.py:39-51`) → UAC.
- `FEATURE_GROUPS` list (`cli/parser.py:9-22`) + `_metadata` DAG (`feature_builder_registry.py:58-76`) → UAC.
- `_MTDS_OUTPUT_BUCKET_DOMAINS` + `_PATH_DATA_TYPE` (`mtds_output_config.py:33-53`) — module docstring acknowledges
  pending UAC migration. Lift.
- `WRITE_GATE_CONFIG` `nan_threshold=0.95` (`feature_writer.py:52-65`) — per-group thresholds → UAC.

#### ❓ Couldn't verify

- Whether UTL `check_shard_freshness` accepts a `chain=` filter argument (currently supports `league_id=` only). Even
  after writer fix, pre-flight would need API change.
- Whether `add()` path sets `capture_status="captured"` vs leaving blank — affects data-status rendering.
- Whether downstream strategy-service pre-flight reads features-onchain manifest at the right granularity.
- Whether Phase 8 calculators (`block_priority_gas_distribution`, `concentrated_liquidity_il_realised`,
  `vault_share_price_apy`, `pool_invariant_drift`) have actual MTDS partitions on disk — they currently silently produce
  zero-row outputs when partitions don't exist (no `record_empty`).

#### Lookahead-bias coverage matrix (features-onchain)

| Calculator                                                                                                                                                                                         | LookaheadBiasError raised | available_at checked | Notes                                                                    |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------- | -------------------- | ------------------------------------------------------------------------ |
| `lst_yields` (orchestrator inline)                                                                                                                                                                 | ✓ via writer              | ❌                   | Output-observation check vs as_of+1d, NOT input.available_at vs target-N |
| `lending_rates`, `utilization`, `rewards`, `risk_params`, `flash_loan_availability`, `health_factor`, `liquidation_events`, `onchain_perps`, `macro_sentiment`, `rate_impact`                      | ✓ via writer (same path)  | ❌                   | Same: output-side only                                                   |
| `aave_*_calculator.py` (lending/rate_impact/risk/utilization)                                                                                                                                      | ❌                        | ❌                   | Calculator's `calculate_features` doesn't check lookahead at all         |
| Phase 8: `block_priority_gas_distribution`, `concentrated_liquidity_il_realised`, `vault_share_price_apy`, `pool_invariant_drift`                                                                  | ❌                        | ❌                   | Not yet wired to dispatch; no guard                                      |
| `defillama_tvl`, `fear_greed`, `macro_sentiment_calculator`, `cryptoquant_exchange_flow`, `eigen_rewards`, `protocol_rewards`, `flash_loan_calculator`, `lst_staking`, `onchain_regime_calculator` | ❌                        | ❌                   | No lookahead guard in any                                                |

**Summary**: 11 feature_groups go through the shared writer's `_enforce_point_in_time` (output-side check only, not the
input-side rule). 14+ calculators have no lookahead guard at all. The structural gap is missing `available_at` on MTDS
upstream parquets — until that lands, calculators can't input-check.

#### Migration items (features-onchain-service contribution)

- None for this service's own historical writes — manifest rows are at `(feature_group, day)` granularity, which is too
  coarse but not a v4-vs-v5 schema-version drift. **Corrective action is to expand the writer key, not migrate existing
  rows.** Once writer is fixed, on-disk multi-chain coverage will be visible immediately.

#### UTL-lift items (features-onchain-service contribution)

- **LIFT-OC1**: `CanonicalDefiShard` (mtds_canonical_reader.py) → UAC `unified_api_contracts.defi`.
- **LIFT-OC2**: `_MTDS_OUTPUT_BUCKET_DOMAINS` + `_PATH_DATA_TYPE` (mtds_output_config.py) → UAC.
- **LIFT-OC3**: `feature_group → required_inputs` DAG (`_metadata` dict in feature_builder_registry.py) → UAC
  `ONCHAIN_FEATURE_GROUP_DEPS`.
- **LIFT-OC4**: NaN threshold from per-group UAC lookup, not service-hardcoded.

### features-sports-service — Shard-Granularity Audit Findings

Audit pass 2026-05-06 by Sonnet sub-agent. Source files: `features_sports_service/engine/batch_handler.py`, `writer.py`,
`orchestrator.py`, `data/gcs_reader.py`, exporters, calculators, `compute/coverage_gate.py`,
`tracking/feature_builder_registry.py`.

#### ✓ Matches target

- **Shard-level failure isolation** — per-table/per-feature-group try/except never raises in
  `batch_handler.py:370, 457, 520, 590`.
- **Honest-coverage trio used** — `record_empty` for legitimately-empty (`batch_handler.py:357, 450, 513, 583`),
  `record_failed` for exceptions (`379, 465, 528, 598`), `manifest.add()` for captured.
- **`FeatureWriteGate`** applied (`writer.py:125`) with NaN 50%, alignment 90%, leakage check.
- **`PointInTimeEnforcer`** + `LookaheadBiasError` imported (`writer.py:17, 53`).
- **Live-mode lookahead re-raise** — `orchestrator.py:140-151` re-raises `PointInTimeViolation` after
  `LOOKAHEAD_BIAS_VIOLATION` event.
- **HT-odds PIT gate** — `odds_features_exporter.py:43-116` drops post-HT-break odds rows.
- **Dual-vocab read** — `gcs_reader.py:39-41, 940-941` tries `asset_group=sports` canonical first then `category=sports`
  legacy.
- **`validate_batch_no_leakage`** strict=True (`orchestrator.py:156-212`).
- **`asof_lookup`** filters `timestamp_col <= as_of` (`pipeline/_asof.py:81`).
- **UAC `FEATURE_UPSTREAM_REQUIREMENTS` / `in_coverage`** imported in `compute/coverage_gate.py:44-48`.
- **Per-league GCS write sharding** — `_write_per_league` (`batch_handler.py:176-231`) groups by league_id.
- **`manifest.add(league_id=...)`** — captured rows at `batch_handler.py:615-628`.

#### ❌ Mismatches

- **[writer]** `batch_handler.py:615-628` — captured rows use legacy `manifest.add()` not
  `record_captured(row_key=...)`. `add()` capture_status default is unclear (need to read manifest_writer.py:636-685
  fully). v6 SSOT method is `record_captured`. All 3 feature groups + all 14+ raw tables go through this path. Fix
  layer: **[per-service]**.
- **[pre-flight]** `batch_handler.py:304-308` — pre-flight `manifest.lookup` row_key = `{date, feature_group}` only.
  Missing `fixture_id`, `league_id`, `timeframe`. Day-level captured-status will skip recompute for ALL leagues even if
  individual leagues failed. Coarser than writer's per-league sharding. Fix layer: **[per-service]**.
- **[writer]** `manifest.add()` for captured rows does NOT include `timeframe` or `fixture_id` even when writer shards
  by league_id. Per-fixture drill-down impossible. Fix layer: **[per-service]**.
- **[writer]** `batch_handler.py:40-44` `_FEATURE_GROUP_TO_DATA_TYPE` maps **only 3 of 14+ feature groups** to canonical
  data_type. Remaining 11 raw table groups (fixture_stats, fixture_events, lineups, player_stats, injuries, players,
  venues, fixtures, leagues, teams, referees, coaches, standings, rounds) write `data_type=""` — invisible to data-
  status reader filtered by data_type. Fix layer: **[per-service]**.
- **[available_at] CRITICAL** — `_ensure_timestamp` (`batch_handler.py:146-151`) sets
  `timestamp = datetime(year, month, day, tzinfo=UTC)` (midnight UTC) for any DataFrame lacking timestamp. Midnight
  passes the 23:59:59 PIT enforcer silently → every output table's `available_at` is artificial midnight, NOT
  source-specific availability. Specifically:
  - **Lineups**: should be `kickoff - 60min`; actual midnight. ❌
  - **Injuries**: should be event-time of injury report; actual midnight. `injury_impact_calculator.py` does not filter
    by prior-fixture timing. ❌
  - **Pre-match odds**: `bm_time` / `bm_minutes_to_kickoff` used for HT-gate filtering only, NOT propagated as
    `available_at` column on output. ❌
  - **Post-match (xG, fixture_stats, sfi_progressive, results)**: should be `match_end_time`; actual midnight. Midnight
    is BEFORE kickoff for same-day post-match data → leak risk. ❌
  - **Weather**: should be forecast-issue time; no `forecast_issue_time` column in output. ❌ Fix layer:
    **[per-service]** + **[UTL]** (per-source availability stamping helper).
- **[writer]** `writer.py:65-66` — `except LookaheadBiasError: pass` in `_enforce_pit_sports` with `strict=False`. The
  enforcer warns then raises; writer's `pass` eats it. **Future-timestamped observations never block batch writes.**
  `strict=False` is intentional per comment but means PIT enforcer is informational-only in batch. Fix layer:
  **[per-service]**.
- **[writer]** `batch_handler.py:492` — `export_derived_features(date_str)` called **without `horizon=`**. The horizon
  gate (`apply_horizon_gate`) and `validate_pit_compliance` at `584-594` are never called. Post-match actuals
  (home_goals, away_xg) are included in flat daily parquet without horizon gating. Downstream ML training reading this
  can access post-match data for same-day fixtures. Fix layer: **[per-service]**.
- **[pre-flight]** `_table_exists_in_gcs` (`batch_handler.py:154-173`) — `except Exception: return False` swallows GCS
  auth failure → unnecessary recompute. Fix layer: **[per-service]**.
- **[writer]** `batch_handler.py:629-631` — `manifest.write()` failure caught with `except Exception`, only warning. If
  it fires for the whole batch day, **no manifest rows for any table** — entire day invisible to data-status. Fix layer:
  **[per-service]**.
- **[path-SSOT]** `gcs_reader.py:651, 675, 697, 1186, 1192` — hardcodes `sports_reference/by_date/day=.../entity=...`
  paths inline (5+ sites). CLAUDE.md SSOT requires `from unified_api_contracts.sports import candidate_parquet_paths` —
  no such import anywhere. Per-league fallback at line 697 partially re-implements UAC
  `SportsPathLayout.PER_DAY_PER_LEAGUE`. Fix layer: **[per-service]**.
- **[coverage_gate not wired]** `compute/coverage_gate.py` exists, imports UAC correctly, but
  `check_calculator_coverage()` is **never called** in `derived_features_exporter.py` or `batch_handler.py`. Dispatch
  uses only `if not data.empty:` guards. Module is dead code. Fix layer: **[per-service]**.
- **[direct google.cloud import]** `gcs_reader.py:662, 946, 1082, 1179` —
  `from google.cloud import storage as gcs_storage` directly. UCI `get_storage_client()` exists and is imported at line
  34 but bypassed for bulk reference reads. Fix layer: **[per-service]**.
- **[progress events]** No `INSTRUMENT_PROCESSED` / `FIXTURE_PROCESSED` structured events with row counts. SSE
  `emit_feature_ready` exists at `batch_handler.py:198, 221` but isn't `log_event` to the events bucket. Silent-success-
  with-zero-output detection from event stream impossible. Fix layer: **[per-service]**.

#### 🔀 Wrong layer

- `_ensure_timestamp` (`batch_handler.py:146-151`) — midnight UTC fallback workaround for missing `available_at`. Should
  not exist; replace with per-source stamping. **[UTL lift]**.
- `_validate_feature_quality` (`batch_handler.py:94-143`) — inline all-NaN counter + classify_and_emit_error. Subset of
  `FeatureWriteGate` already used in writer.py. Duplicate inline gate; delete. **[UTL]**.
- `tracking/feature_builder_registry.py` `BuilderEntry` `required_inputs` DAG → UAC. **[UAC]**.
- Dual-vocab `_MTDS_RAW_ODDS_ASSET_GROUP_SEGMENT` / `_MTDS_RAW_ODDS_LEGACY_HIVE_CATEGORY_SEGMENT`
  (`gcs_reader.py:939-941`) → 7th+ inlined copy of dual-vocab probe across workspace. **[UTL]**.
- Horizon sidecar `_write_horizon_schema_sidecar` (`writer.py:164-207`) — bare `except Exception` swallows failures.
  Horizon metadata should be parquet schema or UTL-backed contract, not best-effort JSON sidecar. **[UTL/UAC]**.

#### ❓ Couldn't verify

- Whether `add()` defaults `capture_status="captured"` or leaves blank.
- Whether UAC `FEATURE_UPSTREAM_REQUIREMENTS` covers all calc names (e.g. `elo`, `injury_impact`) or falls through to
  `READY` for uncatalogued calcs.
- Whether `compute_sfi_progressive_only.py` (`features_sports_service/scripts/`) is on canonical code path or one-off.
  Uses finer per-league granularity than `batch_handler.py`.

#### available_at stamping per source (features-sports)

| Source                                                | Calculator                                         | Stamping rule                                                                              | Matches handover?                   |
| ----------------------------------------------------- | -------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------- |
| Lineups                                               | derived_features via `compute_player_lineup_batch` | `_ensure_timestamp` → midnight UTC                                                         | NO — should be `kickoff - 60min`    |
| Injuries                                              | derived_features via `compute_injury_impact_batch` | midnight; not filtered by prior-fixture timing                                             | NO — should be event-time           |
| Pre-match odds                                        | odds_features_exporter                             | `bm_time` used for HT filter only, NOT on output                                           | NO — `publication_time` not stamped |
| Post-match (xG/fixture_stats/results/sfi_progressive) | derived_features                                   | midnight; `_filter_completed_before` correct for history but stamps midnight not match_end | NO — CRITICAL leak risk             |
| Weather                                               | `compute_weather_for_fixtures`                     | midnight; no `forecast_issue_time`                                                         | NO — distinction not maintained     |

#### Lookahead-bias coverage matrix (features-sports)

| Calculator / context                         | LookaheadBiasError raised                            | Notes                                                                                                |
| -------------------------------------------- | ---------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `orchestrator.py` live mode                  | ✓ (re-raises PointInTimeViolation)                   | Correct                                                                                              |
| `writer.py` batch mode `_enforce_pit_sports` | ❌ (`except LookaheadBiasError: pass`, strict=False) | Silently downgrades all to warning                                                                   |
| `derived_features_exporter.py` (22+ calcs)   | ❌                                                   | No per-input `available_at <= kickoff - N` guard                                                     |
| `odds_features_exporter.py`                  | PARTIAL — HT break only                              | Other horizons not gated                                                                             |
| `export_derived_features` horizon gate       | DEAD IN BATCH                                        | `validate_pit_compliance` only fires when `horizon` arg passed; `batch_handler.py:492` calls without |

#### Hardcoded sports paths (path-SSOT violations)

All in `features_sports_service/data/gcs_reader.py`:

- Line 651: `sports_reference/by_date/day={date}/entity={entity}/{entity}.parquet`
- Line 675: same template (inside 7-day lookback loop)
- Line 697: `sports_reference/by_date/day={date}/entity={entity}/league=` — partially re-implements UAC layout
- Line 1186: `prefix = "sports_reference/by_date/day="`
- Line 1192: `if "/entity=fixtures/fixtures.parquet" not in path:`

#### Migration items (features-sports-service contribution)

1. **MIG-FS1**: All `manifest.add()` calls for captured rows (`batch_handler.py:615-628`) → `record_captured`.
2. **MIG-FS2**: Add `timeframe` + `fixture_id` to all manifest row_keys.
3. **MIG-FS3**: Extend `_FEATURE_GROUP_TO_DATA_TYPE` to all 14 raw table groups.
4. **MIG-FS4**: Replace hardcoded sports paths with `candidate_parquet_paths()`.
5. **MIG-FS5**: Stamp `available_at` per source rules at write-time (needs UTL `availability_stamping.py`).
6. **MIG-FS6**: Pass `horizon=` to `export_derived_features` in batch.
7. **MIG-FS7**: Wire `coverage_gate.check_calculator_coverage()` into dispatch.
8. **MIG-FS8**: Replace direct `from google.cloud import storage` with `get_storage_client()`.
9. **MIG-FS9**: Make `manifest.write()` failure fatal or emit FAILED event.

#### UTL-lift items (features-sports-service contribution)

- **LIFT-FS1**: `_validate_feature_quality` (batch_handler.py:94-143) — duplicate of `FeatureWriteGate`; delete.
- **LIFT-FS2**: `tracking/feature_builder_registry.py` `required_inputs` DAG → UAC.
- **LIFT-FS3**: `_ensure_timestamp` (batch_handler.py:146-151) → delete; replace with per-source `available_at` stamping
  from UTL `availability_stamping.py`.
- **LIFT-FS4**: Dual-vocab `_MTDS_RAW_ODDS_*_SEGMENT` (gcs_reader.py:939-941) → UTL `hive_vocab.py` (7th workspace
  copy).

### market-tick-data-service (MTDS) — Shard-Granularity Audit Findings

Audit pass 2026-05-06 by Sonnet sub-agent. Source files: `engine/orchestrator.py`, `cli/handlers/_defi_manifest.py`,
`cli/handlers/perp_funding_handler.py`, `cli/handlers/tick_data_handler.py`, `cli/handlers/schema_validation.py`,
`market_interface/adapters/prediction/{polymarket,kalshi}_adapter.py`, `adapters/umi_tick_provider.py`,
`adapters/hyperliquid_s3.py`, `cli/handlers/solana_defi_handler.py`, `cli/handlers/vault_share_price_handler.py`,
`reader.py`, `raw_tick_hive.py`. Databento adapter explicitly excluded (parallel-stream Item 2).

#### ✓ Matches target

- **Writer granularity — CeFi/TradFi v6** — `engine/orchestrator.py:1918`:
  `writer_manifest.add(processing_date, row_count, venue, chain, data_type, league_id, instrument_type, underlying, quote_asset, margin_type)`
  — full v6 7-tuple. Matches v6 spec.
- **Tier-3 per-instrument sentinel** — `engine/orchestrator.py:2194` emits `record_empty` / `record_failed` per
  `instrument_id` for non-captured instruments after main loop.
- **Dual-vocab hive key SSOT** — `raw_tick_hive.py` defines `RAW_TICK_ASSET_GROUP_HIVE_KEY="asset_group"` +
  `RAW_TICK_ASSET_GROUP_HIVE_KEY_LEGACY="category"`. Reader probes canonical first (`reader.py:160`).
- **Write-gates wired for DeFi handlers** — `validate_before_write()` called pre-write in
  `perp_funding_handler.py:322,463,615` etc. Required cols (hard fail), NaN ratio > 0.5 (warn), row count > 0.
- **DeFi `record_empty` / `record_failed` route through UTL** — `cli/handlers/_defi_manifest.py` correctly delegates to
  `ManifestWriter.record_empty/record_failed` with proper row_key dicts + capture_status.
- **`INSTRUMENT_PROCESSED` event schema known** — `lending_indices_handler.py:458` is the sole-but-correct example;
  emits `rows_written, parquet_path`. Pattern exists; just needs propagation.

#### ❌ Mismatches

- **[writer]** `cli/handlers/_defi_manifest.py:120` — `DefiManifestRecorder.record_captured()` calls
  `self._writer.add(..., venue, chain, data_type, instrument_type)` — **`instrument_id` omitted entirely**.
  `_build_row_key()` at line 300 only keys `{date, venue, chain, data_type}` — missing `instrument_id` AND
  `instrument_type`. DeFi shards collapse to `(venue, chain, data_type, date)`, losing per-instrument visibility. Fix
  layer: **[per-service]**.
- **[writer]** `polymarket_adapter.py:534, 541` shards per raw `condition_id`; `kalshi_adapter.py` shards per `ticker`.
  Neither maps to a `canonical_question_group`. UAC has no such constant yet (confirmed greenfield in instruments-svc
  audit). Fix layer: **[UAC]** first, then **[per-service]**.
- **[writer]** `engine/orchestrator.py:1771` — sports shard key is `(bookmaker_str, "trades", league_str, "odds", "")` —
  5-tuple with NO `fixture_id`. Per-fixture granularity absent. Fix layer: **[per-service]**.
- **[pre-flight]** `cli/handlers/tick_data_handler.py:173` — outer
  `check_shard_freshness(bucket, date, expected_venues=...)` is at `(bucket, date, venue)` only. No data_type, no
  instrument_id. **Far coarser than v6 writer**. Fix layer: **[per-service]**.
- **[pre-flight]** `engine/orchestrator.py:1394-1425` — inner pre-flight reads `read_availability_index(bucket)` and
  filters by `(venue, data_type)` only. Misses `instrument_type`, `instrument_id`, `quote_asset`, `margin_type`.
  Mismatches writer granularity. Fix layer: **[per-service]**.
- **[available_at]** Zero occurrences of `available_at` column in ANY MTDS write path (orchestrator, DeFi handlers,
  sports, prediction). Fix layer: **[UTL]** (extend `ManifestWriter.add()`/`record_captured()` to accept
  `available_at`) + **[per-service]** plumbing.
- **[write-gate]** CeFi/TradFi/Sports/Prediction orchestrator path has NO NaN-ratio / required-col / row-count guard
  before flush. `validate_before_write()` is **DeFi-only**. Other asset_groups can write zero-row or all-NaN parquets
  and record `captured`. Fix layer: **[UTL lift]** + **[per-service]** apply.
- **[write-gate]** No cluster-coverage gate anywhere in MTDS. CeFi options/futures chains, Sports bookmaker aggregates
  can record bundle-level `captured` without checking ≥N instruments captured. Fix layer: **[UTL]** new gate +
  **[per-service]**.
- **[INSTRUMENT_PROCESSED]** Only `PROCESSING_COMPLETED` at end-of-date in `engine/orchestrator.py:2289`. NO per-
  instrument row-count events in CeFi/TradFi/Sports/Prediction/DeFi main loops. Zero-output runs undetectable from event
  stream. Fix layer: **[per-service]**.
- **[manifest v6 combo_type / leg_weights]** UTL `ManifestWriter.add()` accepts these. **Zero MTDS call sites pass
  them.** Multi-leg / combo instrument types untracked. Fix layer: **[per-service]** (when introduced).
- **[manifest shape]** `perp_funding_handler.py:225` —
  `chain_for_manifest = protocol.upper() if protocol in ("hyperliquid", "aster") else ""`. **GMX written with
  `chain=""`** — non-queryable by chain. Should be `chain="ARBITRUM"` or `"AVALANCHE"`. Fix layer: **[per-service]**.

#### 🔀 Wrong layer

- `cli/handlers/schema_validation.py` `validate_before_write` — should be in UTL `write_gates` for re-use across MDPS /
  features-\* / strategy-service. **MTDS is the reference impl; lift.**
- `engine/orchestrator.py:1880-1908` — hardcoded 27-entry tuple of DeFi protocol prefixes (`uniswap`, `aave`, `gmx`,
  ...) for `PROTOCOL-CHAIN` venue split. Belongs in UAC `registry/capability_declarations/_defi.py` next to
  `CHAIN_RPC_TEMPLATES`. **[UAC]**.
- Multiple docstrings + inline comments in `engine/orchestrator.py` reference legacy `category=` partition paths.
  Documentation drift only; clean up.

#### ❓ Couldn't verify

- Whether `canonical_question_group` is partially implemented elsewhere (it isn't, per UAC audit).
- Whether sports-service backfill pipeline (parallel) will deliver fixture_id before MTDS consumes it.
- Whether TradFi `chain` column equates to exchange MIC or empty (databento adapter excluded).

#### `except: continue` sweep — NEW HIGH-SEVERITY FINDINGS

| File                                        | Line     | Loop body                                   | Swallows                                        | Severity                                                              |
| ------------------------------------------- | -------- | ------------------------------------------- | ----------------------------------------------- | --------------------------------------------------------------------- |
| `adapters/umi_tick_provider.py`             | **581**  | per-coin book snapshot, PACIFICA-SOLANA     | `aiohttp.ClientError, TimeoutError` debug-only  | **HIGH** — per-instrument net-fail silently drops; no `record_failed` |
| `adapters/umi_tick_provider.py`             | **737**  | per-symbol book snapshot, EXTENDED-STARKNET | same                                            | **HIGH**                                                              |
| `adapters/umi_tick_provider.py`             | **921**  | per-symbol orderbook fetch, LIGHTER         | same                                            | **HIGH**                                                              |
| `cli/handlers/solana_defi_handler.py`       | 687      | TVL time-series datapoint parse             | `TypeError, ValueError` silent drop             | **MED** — corrupts TVL aggregates silently, no count                  |
| `cli/handlers/solana_defi_handler.py`       | 810      | APY timestamp parse                         | `ValueError` silent drop                        | **MED**                                                               |
| `adapters/hyperliquid_s3.py`                | 245, 265 | per-hour S3 + per-line decode               | NoSuchKey + JSON decode                         | **LOW** — documented intent, acceptable                               |
| `cli/handlers/vault_share_price_handler.py` | 338      | per-protocol-group Alchemy init             | tracked in `per_group_errors` → `record_failed` | **LOW** — mitigated                                                   |
| `reader.py`                                 | 171, 184 | GCS prefix probe                            | path-not-exist, try next vocab                  | **LOW** — canonical pattern                                           |

**3 NEW HIGH-severity sites** (`umi_tick_provider.py:581/737/921`) not listed in prior Phase 0 inventory.

#### MTDS migration items

- **MIG-MTDS1**: Backfill `instrument_id` + `instrument_type` to all DeFi manifest rows (currently dropped). Migration
  script per drift axis.
- **MIG-MTDS2**: Re-stamp GMX manifest rows with `chain="ARBITRUM"`/`"AVALANCHE"`.
- **MIG-MTDS3**: When `canonical_question_group` ships from UAC, migrate Polymarket+Kalshi prediction shards.

#### MTDS UTL-lift items

- **LIFT-MTDS1**: `validate_before_write` (`schema_validation.py`) → UTL `write_gates`.
- **LIFT-MTDS2**: DeFi protocol-prefix list → UAC `_defi.py`.

### market-data-processing-service (MDPS) — Shard-Granularity Audit Findings

Audit pass 2026-05-06 by Sonnet sub-agent. Source files: `orchestration_scanner.py`, `live_workers.py`,
`batch_workers.py`, `orchestration_writer.py`, `orchestration_service.py`, `canonical_writer.py`,
`candle_write_mixin.py`, `adapters/{cefi,tradfi,defi,sports}/...`.

#### ✓ Matches target

- **Reader path-template hive-key-agnostic** — `orchestration_scanner.py` lists `raw_tick_data/by_date/day={date}/` and
  walks all blobs; picks up both `category=` and `asset_group=` variants. **No drift from the 2026-05-05
  ticks.parquet-vs-per-instrument incident.** Chain-bundle parquets routed to `_process_chain_bundle_streaming` via
  `_chain_bundle_likely_from_path`. Per-instrument routed via `extract_instrument_id_from_blob_path`.
- **Per-instrument file-level skip** — `_check_existing_outputs` in scanner uses path-based instrument_id extraction.
- **`INSTRUMENT_PROCESSED` events with non-null column counts** — `live_workers.py:112-162`
  `_emit_instrument_processed_event` with `_TRACKED_NON_NULL_COLUMNS` per-column counts; called inside
  `_process_all_timeframes` at lines 702-709. **Silent-success-with-zero-output detectable from event stream** for the
  standard path.
- **Honest empty handling for non-TRADFI** — `batch_workers.py:189-228` `_handle_empty_tick_data` returns
  `success=True, candles_generated=0` with NO parquet + NO manifest row. Correct honest gap (data-status shows missing,
  not phantom).
- **Partition-required gate** — `orchestration_scanner.py:75-82` `_data_type_requires_partition` prevents fallback
  aggregation across mismatched instrument types for 46 DeFi/CeFi data types.
- **Intentional closed-market NaN candles labelled** — `_create_closed_market_candle` and
  `_create_full_day_empty_output` set `market_state=CLOSED` distinguishing intentional placeholders.
- **OOM fix for chain bundles** — `_process_chain_bundle_streaming` uses Polars predicate pushdown per-symbol (no full
  chain-bundle parquet load).

#### ❌ Mismatches

- **[CRITICAL — M1] MRO shadow: `CandleOrchestrationWriter._write_candles` hides `CandleWriteMixin._write_candles`** —
  `orchestration_writer.py:328` defines its own `_write_candles` that calls `self.storage_client.upload_bytes()`
  directly (raw GCS upload, line 390). `CandleWriteMixin._write_candles` (which calls
  `canonical_writer.write_candle_parquet → ManifestWriter.add()`) is **NEVER reached** in production. Consequence:
  `canonical_writer.py:313-326` `ManifestWriter.add()` call is **dead code in production**. All manifest rows come only
  from `_write_manifest_records` (see M3) which is v3-shaped. Fix layer: **[per-service]** CRITICAL.
- **[CRITICAL — empty placeholder reproduction path]** Every adapter's
  `_create_empty_output(timeframe, instrument_info) → CandleOutput` returns `n_candles = get_candles_per_day(timeframe)`
  rows with `open=high=low=close=volume=NaN`. The `_handle_empty_tick_data` guard only intercepts at `tick_data.empty` —
  does NOT intercept "ticks present but all outside valid intervals". **Highest-risk confirmed path:**
  - `defi/swap_adapter.py:106` — non-empty tick_data, all ticks outside valid swap intervals → 1440 NaN bars + manifest
    `expected=True, available=True` → data-status `captured` → downstream 1440 garbage. **2026-05-05 incident exact
    reproduction path active today.**
  - `cefi/trades_adapter.py:74` — same pattern.
  - 15+ other `_create_empty_output` sites across `adapters/{cefi,tradfi,defi,sports}/` (full table in agent report;
    most "Unknown if guarded" — needs spot-check). Fix layer: **[per-service]** CRITICAL.
- **[M2]** `canonical_writer.py:313-326` uses legacy `.add()` not `record_captured()` — no `capture_status`,
  `attempted_at`, `error_reason`. Comments at lines 5, 187, 299 say "v4 manifest row"; UTL is v5/v6. (Moot until M1
  fixed — this code is dead.)
- **[M3]** `orchestration_service.py:283-388` `_write_manifest_records` writes v3-shaped coarse summaries —
  `(date, venue, data_type, row_count)` with NO `instrument_type`, `chain`, `instrument_id`, `timeframe` at instrument
  level. Three variants all coarser than the shard atom. Pre-flight `_should_skip_shard` cannot match at instrument
  granularity. Fix layer: **[per-service]**.
- **[M4]** `orchestration_service.py:160-184` calls `check_shard_freshness(expected_venues=data_types, ...)` — at
  `(date, data_types)` only. Missing instrument-level dims. Fix layer: **[per-service]**.
- **[M5] `record_empty` / `record_failed` never called from main service code paths** — only used in
  `scripts/reprocess_sports_odds.py`. Three failure modes:
  - Adapters returning `_create_empty_output` (NaN rows) write parquets and `.add()` rows with `expected=True` —
    manifest shows `captured`, downstream reads 1440 NaN. **2026-05-05 pattern.**
  - Write failures caught in `candle_write_mixin.py:141-143` (`except ... as e: logger.error; return None`) emit no
    manifest row at all — shard permanently invisible.
  - Per-symbol failures in `_iter_chain_symbol_dfs` swallowed with `continue` — no `record_failed`, no
    `ADAPTER_FETCH_FAILED`, no manifest entry. Fix layer: **[per-service]** CRITICAL.
- **[M6] available_at** — Zero occurrences in any MDPS output parquet schema or manifest row. `canonical_writer.py:110`
  schema columns are `[open, high, low, close, volume, vwap, trade_count, market_state, timeframe]`. Fix layer:
  **[per-service]** + **[UTL]**.
- **[M7] No NaN-ratio write gate** — `ParquetSchemaEnforcer` checks column presence + dtype only. No code checks
  `df[['open','high','low','close']].isna().mean() > threshold`. **A 1440-NaN parquet passes schema enforcement.** Fix
  layer: **[UTL]** lift + **[per-service]** apply.
- **[M8] Streaming chain-bundle path has NO `INSTRUMENT_PROCESSED` events** — `live_workers.py:1033-1079`
  `_streaming_write_per_tf` calls `_write_candles` per symbol per timeframe but never calls
  `_emit_instrument_processed_event`. **Chain bundle runs (options chains, futures chains) emit zero per-instrument
  progress events.** Fix layer: **[per-service]**.

#### 🔀 Wrong layer

- `_normalise_timeframe` inline in `canonical_writer.py:59-67` — UTL-level normalization. Lift.
- "v4 manifest row" comments — documentation drift; clean up.

#### ❓ Couldn't verify

- Whether `CandleOrchestrationWriter._write_candles` is actually invoked in production vs
  `CandleWriteMixin._write_candles` (MRO analysis strongly indicates the shadow but didn't run service to confirm
  empirically).
- Whether `ManifestWriter.add()` v3 API still exists in current UTL (likely backwards-compat shim; confirmed at
  instruments- service audit it does).
- Exact `_create_empty_output` call sites that bypass `tick_data.empty` guard — `defi/swap_adapter.py:106` and
  `cefi/trades_adapter.py:74` confirmed; remaining 15 sites need exhaustive trace.
- Whether DeFi adapters `liquidity`/`market_state`/`fx_rates` are actually registered (confirmed NOT in
  `adapters/__init__.py` top-level; uncertain whether other import paths trigger registration).

#### Empty-placeholder hunt — adapter inventory

17 sites in `adapters/{cefi,tradfi,defi,sports}/...` call `_create_empty_output` / `_create_full_day_empty_output`.
Confirmed reproduction path: `defi/swap_adapter.py:106`, `cefi/trades_adapter.py:74`. Remaining 15 sites need spot-check
(full table embedded in audit transcript).

#### MDPS migration items

- **MIG-MDPS1**: Fix MRO shadow — delete `CandleOrchestrationWriter._write_candles` (or refactor inheritance) so
  `CandleWriteMixin._write_candles` is the production write path. Critical.
- **MIG-MDPS2**: Replace ALL `_create_empty_output` returning NaN-filled DataFrames with returning `None` /
  `CandleOutput(n_candles=0, ...)`; ensure upstream flow routes empty-tick + ticks-outside-valid-intervals to
  `record_empty`, NOT to write+`record_captured`.
- **MIG-MDPS3**: Migrate `_write_manifest_records` from `(date, venue, data_type, row_count)` v3 shape to per-instrument
  v5/v6 shape with `chain, instrument_type, instrument_id, timeframe`.
- **MIG-MDPS4**: One-time scan of existing parquets to detect 1440-NaN-bar phantoms; flip manifest rows to
  `attempted_failed` or delete parquets + write `record_empty`. (Same pattern as instruments-service phantom audit.)

#### MDPS UTL-lift items

- **LIFT-MDPS1**: `_normalise_timeframe` (`canonical_writer.py:59-67`) → UTL.
- **LIFT-MDPS2**: NaN-ratio write gate (currently absent) → UTL `write_gates`.

---

## Phase 0 Synthesis

### Cross-cutting findings (workspace-wide patterns)

The following anti-patterns appear in **3+ services** and represent the highest-leverage fixes:

| Pattern                                                            | Services affected                                                                                                                                                   | Severity | Fix layer                                   |
| ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ------------------------------------------- |
| **`available_at` not stamped at write-time**                       | MTDS, MDPS, features-onchain, features-sports, features-delta-one (5/5 audited)                                                                                     | CRITICAL | UTL stamping helper + per-service plumbing  |
| **`record_empty` / `record_failed` not called in main paths**      | MDPS, features-onchain, features-delta-one (3/5)                                                                                                                    | CRITICAL | per-service rewrite                         |
| **Pre-flight coarser than writer granularity**                     | instruments-service (3 sites), MTDS (2 sites), MDPS, features-onchain, features-sports (5/6)                                                                        | CRITICAL | per-service                                 |
| **`LookaheadBiasError` only on output-side, not input-side**       | features-onchain (writer-only), features-sports (eaten in batch), features-delta-one (zero) (3/3 features-\* audited)                                               | HIGH     | UTL base-class lift + per-service inherit   |
| **NaN-ratio gate inlined per-service or absent**                   | instruments-service (inlined per-data-type), MTDS (DeFi-only), MDPS (absent), features-onchain (hardcoded 0.95), features-sports (subset of FeatureWriteGate) (5/5) | HIGH     | UTL lift + UAC per-feature_group thresholds |
| **Empty placeholders that look populated (1440 NaN bars pattern)** | MDPS confirmed (defi/swap_adapter.py:106, cefi/trades_adapter.py:74), 15 more sites suspect                                                                         | CRITICAL | per-service                                 |
| **Manifest write swallowed by bare except**                        | features-delta-one, features-sports (manifest.write batch_handler.py:629-631)                                                                                       | HIGH     | per-service                                 |
| **Hardcoded sports paths bypass UAC SSOT**                         | features-sports (5+ sites in gcs_reader.py)                                                                                                                         | MED      | per-service                                 |
| **Dual-vocab probe inlined per-service**                           | features-sports (`_MTDS_RAW_ODDS_*_SEGMENT`) — 7th workspace copy                                                                                                   | MED      | UTL `hive_vocab.py`                         |
| **`feature_group → required_inputs` DAG self-declared**            | features-onchain (`_metadata` dict), features-sports (`feature_builder_registry.py`)                                                                                | HIGH     | UAC SSOT                                    |
| **`except: continue` swallows per-instrument failures**            | MTDS umi_tick_provider.py:581/737/921 (3 NEW HIGH sites), solana_defi_handler.py:687/810 (2 MED)                                                                    | HIGH     | per-service                                 |
| **No `INSTRUMENT_PROCESSED` events with row counts**               | MTDS (1 of N exists), MDPS streaming-chain-bundle path, features-onchain (only window summaries), features-sports (SSE only), features-delta-one (only batch-level) | MED      | per-service                                 |

### Consolidated migration list

#### v5/v6 manifest schema migrations (per-service)

- **MTDS DeFi**: backfill `instrument_id` + `instrument_type` to all DeFi manifest rows (currently dropped at
  `_defi_manifest.py:120,300`).
- **MTDS GMX**: re-stamp manifest rows from `chain=""` to `chain="ARBITRUM"`/`"AVALANCHE"`.
- **MDPS**: replace `_write_manifest_records` v3-shaped rows with per-instrument v5/v6 shape; one-time scan-and-rewrite.
- **MDPS phantom audit**: scan existing OHLC parquets for 1440-NaN-bar phantoms; flip manifest to `attempted_failed` or
  delete parquet + `record_empty`.
- **instruments-service Polymarket**: migrate `data_type=BTC|ETH|...` overload to
  `canonical_question_group=BTC_UP_DOWN_1D|...` (depends on UAC build).
- **instruments-service SFI_PROGRESSIVE `available_at`**: re-stamp from `15:00 UTC` placeholder to actual `kickoff_utc`
  once API_FOOTBALL fixture lookup is wired.
- **features-sports**: switch `manifest.add()` calls (`batch_handler.py:615-628`) to `record_captured` with full row_key
  including `timeframe` + `fixture_id` + `data_type` for all 14+ raw table groups.

No service has v4-vs-v5 schema-version drift on disk that needs migration. **Corrective action everywhere is to expand
writer keys + start using `record_captured/empty/failed`, not migrate existing rows.**

### Consolidated UTL-lift list

| ID      | Lift                                                                                   | Currently inlined in                                                                                                                                                                               | Target layer                             |
| ------- | -------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| LIFT-1  | NaN-ratio + row-count + schema write-gate trio (extend `FeatureWriteGate`)             | instruments-service (`_validate_predictions_null_rates`), features-sports (`_validate_feature_quality`), features-onchain (hardcoded 0.95), MTDS (`schema_validation.py` DeFi-only), MDPS (absent) | UTL                                      |
| LIFT-2  | Cluster-coverage gate for bundled shards                                               | absent everywhere                                                                                                                                                                                  | UTL (new) + UAC clusters                 |
| LIFT-3  | Per-source `available_at` stamping helper                                              | features-sports (`_ensure_timestamp` midnight workaround), all others (absent)                                                                                                                     | UTL                                      |
| LIFT-4  | `_should_skip_date_for_per_leaf` (generalised from `_should_skip_date_for_per_league`) | instruments-service only                                                                                                                                                                           | UTL                                      |
| LIFT-5  | `_classify_adapter_failure` (try-classify-fallback dance)                              | instruments-service `orchestrator.py:530-543`                                                                                                                                                      | UTL (likely duplicated in MTDS adapters) |
| LIFT-6  | Mandatory `LookaheadBiasError` enforcement at calculator base-class                    | features-onchain (writer-only), all others absent                                                                                                                                                  | UTL `feature_calculator_base`            |
| LIFT-7  | `record_partial_batch(manifest, completed, failed)` policy helper                      | features-delta-one, features-sports (drop manifest on incomplete)                                                                                                                                  | UTL                                      |
| LIFT-8  | `feature_group → required_inputs` DAG SSOT                                             | features-onchain (`_metadata` dict), features-sports (`feature_builder_registry.py`)                                                                                                               | **UAC** (not UTL)                        |
| LIFT-9  | Dual-vocab `category=` vs `asset_group=` probe utility (5 phantom-audit drift axes)    | features-sports (7th copy), instruments-service `reconcile_phantom_manifest_rows_all.py`                                                                                                           | UTL `hive_vocab.py`                      |
| LIFT-10 | DeFi protocol-prefix list                                                              | MTDS `engine/orchestrator.py:1880-1908`                                                                                                                                                            | UAC `_defi.py`                           |
| LIFT-11 | `CanonicalDefiShard` dataclass                                                         | features-onchain `mtds_canonical_reader.py:39-51` (used by 5 calcs)                                                                                                                                | UAC `unified_api_contracts.defi`         |
| LIFT-12 | `_normalise_timeframe`                                                                 | MDPS `canonical_writer.py:59-67`                                                                                                                                                                   | UTL timeframe utils                      |
| LIFT-13 | MTDS bucket / data-type maps                                                           | features-onchain `mtds_output_config.py:33-53` (acknowledged pending)                                                                                                                              | UAC                                      |

### Consolidated UAC build items

- **BUILD-PRED1..4**: Polymarket+Kalshi `canonical_question_group` SSOT (greenfield — see UAC prediction finding).
- **BUILD-NAN-THRESH**: `FEATURE_GROUP_NAN_THRESHOLDS` per-feature_group in UAC.
- **BUILD-DAG**: `FEATURE_GROUP_REQUIRED_INPUTS` DAG SSOT (lifts from features-onchain + features-sports).

### Phase 1 priority (suggested ordering)

Three tiers of urgency:

**Tier 1 — Ship-blocker correctness bugs**:

1. MDPS MRO shadow + `_create_empty_output` 1440-NaN-bar reproduction path (CRITICAL — actively producing bad data).
2. instruments-service SFI_PROGRESSIVE / SFI_STANDINGS / PLAYER_VALUES coarser-pre-flight bug (per-league coverage
   permanently locked out — same shape as 2026-05-05 MATCHES 18%-coverage incident).
3. MTDS `umi_tick_provider.py:581/737/921` per-instrument silent-drop swallows.
4. features-sports `writer.py:65-66 except LookaheadBiasError: pass` — disables PIT enforcement in batch.
5. features-sports `_ensure_timestamp` midnight UTC for post-match data — leak risk.

**Tier 2 — UTL/UAC lifts that unblock multiple services**:

1. LIFT-1 (NaN-ratio + row-count + schema gate trio) — unblocks MTDS+MDPS+features-\* write-gate enforcement.
2. LIFT-3 (per-source `available_at` stamping helper) — unblocks all 5 services.
3. LIFT-6 (mandatory LookaheadBiasError at base-class) — unblocks 30+ delta-one calculators + 25+ onchain calculators
   - 22+ sports calculators.
4. BUILD-PRED1..4 (canonical_question_group SSOT) — unblocks Polymarket+Kalshi shard-correctness.
5. LIFT-8 (feature_group DAG in UAC) — unblocks downstream pre-flight checks.

**Tier 3 — Hygiene**:

1. Per-service writer key expansion to v6 row_key everywhere.
2. Replace `add()` with `record_captured/empty/failed` everywhere.
3. Hardcoded sports paths (features-sports `gcs_reader.py`).
4. `INSTRUMENT_PROCESSED` event propagation.
5. Dual-vocab probe utility lift (LIFT-9).

### What this audit did NOT cover

- **strategy-service**, **execution-service**, **deployment-api**, **deployment-ui** — not in audit scope.
- **On-disk parquet inspection** — audit was source-code only. The phantom-audit recipe in PM CLAUDE.md should run as a
  pre-Phase-1 step to enumerate live drift.
- **Spot-check of MDPS adapter `_create_empty_output` sites 3-17** — only 2 of 17 confirmed as 1440-NaN reproduction
  path; remaining 15 marked "Unknown if guarded" need verification before Phase 1.
- **DeFi adapter registration verification** — `liquidity`/`market_state`/`fx_rates` adapters confirmed NOT in
  `adapters/__init__.py` top-level; whether they're imported via another path uncertain.
- **`canonical_question_group` retroactive mapping** for existing on-disk Polymarket/Kalshi data — depends on
  BUILD-PRED1 design.

<!-- AUDIT_FINDINGS_INSERT_BELOW -->
