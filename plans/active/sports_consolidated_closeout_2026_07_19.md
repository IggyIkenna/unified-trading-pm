---
doc_type: plan
title: Sports consolidated close-out — canonical, honestly-covered, leakage-free, ML-ready (one pass through features)
summary: >-
  The single actionable plan that takes the sports asset_group all the way to ML-ready: canonical SSOT + naming, right
  buckets, codex migration, no-regression guards, honest-coverage backfill across instruments-service /
  market-tick-data-service / market-data-processing-service / features-service, smoke-test + speed enhancement, and zero
  leakage. Absorbs ~7 fold-in sports plans + ~17 issue docs (see the audit's reconciliation). Fed by
  sports_consolidated_audit_2026_07_19. Track-structured like defi_consolidated_closeout. LOCAL/human plan.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, canonical, honest-coverage, data-completion, ml-readiness, leakage, codex, close-out]
related:
  [
    sports_consolidated_audit_2026_07_19.md,
    sports_features_layer_findings_sweep_2026_07_18.md,
    sports_legacy_bucket_cutover_2026_07_16.md,
    sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-07-19"
last_updated: "2026-07-19"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 9.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
drift_direction: advance-code
---

# Sports consolidated close-out — one pass to canonical, honestly-covered, leakage-free, ML-ready

> **Read `sports_consolidated_audit_2026_07_19.md` first** — it is the measured evidence base (every claim here traces
> to a GCS/parquet/manifest measurement in that doc). This plan is the actionable projection: what to fix, in what
> order, to reach "everything sport-related is canonical with no SSOT confusion, backfills at honest-100% across all
> sources and downstream MDPS/features, no leakage, ready for ML training."

## Headline verdict — how sports differs from cefi/tradfi/defi

Sports is **light and mostly filled** (reference layer canonical, round work terminal), so — unlike the heavier AGs that
needed a separate `data_completion_*` plan — this goes **all the way through features in one plan**. What blocks
ML-ready is not bulk backfill; it is (1) one live data-correctness defect (now fixed, re-run pending), (2) a few
canonical-honesty gaps (manifest atom, cross-AG bleed, K-casing), and (3) the honest-coverage/leakage tail.

**Foundation gate**: the FEATURES corpus re-run (F-track) is the last thing before ML, and it must run AFTER the CANON
manifest-atom fix (C-track) and the ODDS-LEAK shard cleanup — else the re-run bakes in stale atoms again.

## Canonical target (the SSOT everything converges on)

- **data_type = UPPER everywhere** (operator K0-DECISION (b), 2026-07-18). Sports is the only AG that is UPPER; CF-7's
  UPPER→lower map is SUPERSEDED for sports. Reference layer already conformant; market-data-sports is the only mixed
  bucket.
- **Fixtures entity split**: `entity=fixtures_schedule` (schedule fields incl. `round`) + `entity=fixtures_outcomes`
  (scores/status), under `pipeline_mode=batch_api_football/`. The legacy bare `entity=fixtures/` is FROZEN (last real
  write 2026-05-23) and must not be read or written. **The manifest `data_type` must record the split entities, not the
  `"FIXTURES"` umbrella** (§ C1).
- **timeframe is its own column** — never baked into `data_type`. `odds_horizon_bucket_{15m,1h,4h,1d}` is a dead cohort.
- **Buckets** (via `resolve_bucket_name`, never string-interpolate): reference → `instruments-store-sports-prd`, odds →
  `market-data-tick-sports-prd` (the `market-data-sports-prd` name 404s — the real name carries a `tick-` infix),
  features → `features-sports-prd`.
- **Honest absence, never a placeholder**: `attempted_failed` is a real-failure signal — root-cause before any relabel
  (§ B2 precedent).

---

## Track F — FEATURES: the live data-correctness defect + the ML-ready re-run · P0 (FOUNDATION GATE)

- [x] [CODE] P0. ✅ §Z season_context fabrication FIXED — **features-service@c6eb1f38** (QG green). Gate derives
      matchday from `round`; `_competition_phase`/games_remaining honest `None` on NaN; 2 regression tests. The 8-VM
      re-run fleet writing the fabricated pattern was STOPPED.
- [ ] [DATA] P0. **Clean corpus-wide `derived_features` re-run** (2019→present, replaces the stopped fleet) — bounded
      per-year SPOT chunks (the `--force` × SPOT preemption-replay hard rule: a preempted force-run restarts at day one,
      so chunk it), watchdog on a validated creation-time metric (whole-date filter, not an hour pattern — cf. codex
      async rule 1a). MUST run AFTER § C1 (manifest atom) so shards record the split atom. Verify via corpus re-scan
      (matchday non-null ≈ round non-null; competition_phase a real early/mid/late spread, NOT 100% 'late').
- [ ] [DIAG] P1. `sfi_progressive_features` is corpus-empty (1 manifest row) despite a documented 2020→today window —
      find why the backfill never ran, then run it. Without it every HT/progressive-SFI ML feature is unavailable.
- [ ] [DIAG] P2. `is_promotion_relegation` is hardcoded `False` (dead) — wire it from the standings relegation-zone
      classification (`_compute_league_batch` already computes it) or formally retire it + its points_at_stake
      multiplier.
- [ ] [DIAG] P2. Settle whether `clv_*`/`odds_movement_*` all-null in odds_features is honest-absence or a gap (wider
      multi-date spot-check) before relying on them for ML.
- [ ] [DATA] P2. Purge the 4 dead dimension groups still inflating the features manifest (players/coaches/referees/
      rounds, 4,216 rows each) — the outstanding §A2 purge.

## Track C — CANON: data_type UPPER + venue/instrument_type + manifest atom · P0

- [ ] [CODE] P0. **C1 — migrate the fixtures manifest atom** from hardcoded `"FIXTURES"` to `FIXTURES_SCHEDULE`/
      `FIXTURES_OUTCOMES` across the 8 call sites (`sports_reference_fixtures.py:242,279`, `process_write.py`,
      `writers.py:219`, `catalogue.py:136`, `process_completeness.py`, `process_preflight.py`,
      `process_zero_records.py`, `sports_fixtures_daily_repoll.py`) so the manifest atom == the writer atom. Gates the
      F-track re-run.
- [ ] [CODE] P0. **K1 — emit UPPER at the LIVE writer**: fix `_build_sports_shard_path` (`venue_fetch.py:871-900`) + the
      sentinel row-key builders (`sentinels.py` v1:420-426, v2:305-311, skip-fan:180-197) to emit
      `DATA_TYPE=TRADES`/`INSTRUMENT_TYPE=ODDS`. This is the currently-running writer; must ship BEFORE K2.
- [ ] [DATA] P1. **K2 — migrate the historical lower-case rows UP** (only after K1): normalise `odds`→`ODDS` (20,331),
      `odds_movement`/`odds_snapshot` (4+4), + drop the dead `odds_horizon_bucket_{15m,1h,4h,1d}` cohort (1,337) — all
      from the one legacy `ticks_migrated_20260505` artifact; ~20,339 rows, one bucket. CF-7's UPPER→lower map is
      superseded for sports.
- [ ] [CODE] P1. **F1/F2 — venue/instrument_type cleanup**: fix the footystats legacy bundle mislabel
      (`venue=ODDS_API`→`FOOTYSTATS`, 42,476 rows); clean the `instrument_type` pollution (110,759 blank + 56,048 None +
      bookmaker-name rows). Do NOT touch the deliberate `mdps_odds_horizon_bucket` `venue=ODDS_API` aggregate (124,294,
      reconciled 2026-07-14).
- [ ] [CODE] P1. **Promote the existing market vocabulary** (`ODDS_API_MARKET_TO_CANONICAL`, already UPPER on
      `market_key`) to the `instrument_type` axis — K1's "introduce a betting-market vocabulary" already exists, just on
      a different column. Reconcile `canonical_writer_shaping.py:218`'s "instrument_type IS 'odds'" claim first.
- [ ] [CODE] P2. **EXCHANGE_ODDS vs FIXED_ODDS fork** — absorb `sports_odds_exchange_fixed_fork_2026_07_18` (§F2
      dimension-pollution): separate exchange (Betfair) from fixed-odds bookmaker prices in the canonical dimensions.
- [ ] [REVIEW] P1. QG assertion: sports `data_type` ∈ the UAC **UPPER** sports vocabulary, `venue` ∉ {vendor names},
      `instrument_type` ∈ the declared sports vocabulary — so this class cannot silently return.

## Track S — STORE: bucket hygiene + legacy path elimination · P1

- [ ] [DATA] P1. Complete `sports_legacy_bucket_cutover_2026_07_16` T2.9 (MDT schema drift) + T2.10 (47,253 phantom
      `api_football×trades` rows) + its post-phase codex audit.
- [ ] [CODE] P2. Eliminate (or document) the legacy bare `entity=fixtures/` (no `pipeline_mode=`) write path still
      active today alongside the canonical split writer (5-league subset).
- [ ] [CLEANUP] P2. Snapshot-then-cull the dead `sports_reference_v2/by_date/` dual-layout (frozen 2026-04-20, no
      entities). Confirm no reader consumes it first.
- [ ] [DATA] P1. Absorb `sports_canonical_migrated_odds_mistamped_footystats` +
      `sports_canonical_raw_truncated_rederive_destroys_corpus` (HIGH — corpus-destroying rederive risk; guard before
      any rederive).

## Track E — ENTITY-SPLIT: repoint every remaining stale consumer · P1 (sports-specific, no defi analog)

- [ ] [CODE] P1. Repoint the remaining stale `entity=fixtures` consumers (sweep §R's ~9-file list:
      `sports_dependency.py`, `sports_fixtures_daily_repoll.py`, `backfill_weather.py:154`,
      `backfill_sports_fixture_stats_manifest.py:91`, `rescan_sports_fixtures_canonical.py:328,452`,
      `enumerate_expected_universe.py:1902`, `migrate_sports_per_league.py`,
      `reconcile_sports_blank_empty_reason_2026_06_24.py`) to `fixtures_schedule` (+`fixtures_outcomes` where scores are
      needed).
- [ ] [CODE] P1. Wire the T0/T1 dependency gate for real (`sports_t0_t1_dependency_gate_never_wired_2026_07_15` — the
      pre-flight only fires `if date is not None` and no caller passes it, so the fail-loud boundary is unreachable).

## Track O — ODDS-LEAK: post-kickoff contamination + the B2 dead-zone · P1

- [ ] [DATA] P0. Run `reprocess_sports_odds.py --force` for 2025-12-18/24/31 through the REAL script so the manifest
      coarse row flips off the stale `captured` (from the legacy-path leak) to `attempted_failed` (18,31) /
      `empty_confirmed` (24) — the B2 diagnosis was never persisted.
- [ ] [DATA] P1. Purge/backup-delete the 27 leaked legacy-path (no `pipeline_mode=`) T-0 shards for 2025-12-18/24/31
      (100% post-kickoff) — confirm no live reader consumes the unprefixed path first (if one does, that reader leaks
      today).
- [ ] [DIAG] P1. Root-cause the 112,277 `attempted_failed` rows confined to exactly BETFAIR/MATCHBOOK/PINNACLE (all 6
      years) — likely `_SNAPSHOT_VENUES` CLV completeness, not primary capture. Do NOT relabel without root-cause.
- [ ] [DIAG] P1. Locate the emitter of the 139,620 `venue=ODDS_API, source=api_football, empty_confirmed` rows (not
      `_emit_sports_v1/v2_sentinels`) before folding into K2.
- [ ] [DIAG] P2. Corpus-wide scan for other low-fixture dates whose only in-window odds fall in the T-12h↔T-24h
      615-minute dead-zone; consider adding a T-18h horizon or widening the T-24h staleness cap; investigate why the
      multi-shot `TIER_1_OFFSETS` loop apparently didn't run on the quiet 2025-12 days (only 1 fetch_utc observed).
- [ ] [DATA] P2. Purge the 1,337 dead `odds_horizon_bucket_{15m,1h,4h,1d}` manifest rows.

## Track H — HONEST-COVERAGE: manifest honesty + denominators · P1

- [ ] [DIAG] P1. Why do `reason`/`error_code`/`empty_reason`/`classified_error` read back blank for the sports odds
      manifest (schema gap or C5-class silent-empty) — blocks root-causing § O findings.
- [ ] [DIAG] P2. Confirm sports genuinely never emits `expected_unattempted` in the odds manifest (0 of 1.97M) by
      design, or fix the miscoercion into `empty_confirmed`.
- [ ] [DATA] P1. Merge `sports_manifest_read_staleness_budget_missing_2026_07_15` into sweep §J's
      `AG_STALENESS_BUDGET_SEC["sports"]` fix (same defect, two docs).
- [ ] [REVIEW] P2. Honest-coverage atom regrade to per-calculator grain (sweep §C3, operator-decided) + league_id
      namespace reconciliation (§C2) + `fixture_stats` 708-failure root-cause (§C6).

## Track V — COVERAGE: backfill to honest-100% · P1 (operator-gated where noted)

- [ ] [DATA] P1. Round-derivation residual: run the retargeted backfill for the reachable in-window pairs already scoped
      (sweep §T/§W terminal state); the cup-vs-league classification is resolved (they are blank-round leagues,
      fetchable).
- [ ] [OPERATOR] P1. **§U decision** — 489 in-window (league,season) pairs / 10,869 rows in leagues ABSENT from the UAC
      registry: extend the registry or stop capturing. BLOCKED-OPERATOR-DECISION. "Backfilled 100%" can't be asserted
      until settled.
- [ ] [OPERATOR] P2. **§T decision** — pre-2019 blank-round rows (122,864) are outside the stated 2019→2026 window:
      confirm whether 2013–2018 is in scope. BLOCKED-OPERATOR-DECISION.
- [ ] [DATA] P1. Absorb `sports_p2_history_apifootball_2015_to_present` residuals + the 94-league enrichment backfill
      from `sports_canonical_universe_and_apifootball_reference_expansion`.
- [ ] [OPS] P2. Re-roll `build_instrument_catalogue.py --asset-group sports --since 2019-01-01` to pick up the §T/§U/§W
      +26,894 round rows (catalogue snapshot predates them).
- [ ] [CODE] P2. Upgrade the catalogue `player` grain from `entity=injuries` (injured-only) to `entity=fixture_lineups`
      (full roster, now carries 100% player/coach identity).

## Track K — SMOKE + SPEED + right-days · P1

- [ ] [CODE] P0. Extend `features-service/scripts/sports/smoke_matrix.py` beyond `feature_group="odds"` to assert
      `fixture_features`/`derived_features` (`round_name`, `matchday`, `competition_phase` spread, `coach_id` non-null)
      on a pinned pre-cutover date (`2024-03-09`) — the only way §V/§Z-class bugs get caught in CI.
- [ ] [CODE] P1. Pin a `SPORTS_SMOKE_DATES` constant (busy `2025-12-20` / thin `2025-12-24` / known-buggy `2025-12-18` +
      `2024-03-09`) instead of `resolve_latest_captured_date()`; only allow `empty_confirmed` to PASS on the thin date.
- [ ] [CODE] P1. Promote the existing golden window (2025-09-01…11-30) to a shared "right days" SSOT module both smoke
      tests and backfill launches import — the "speed / right days" pillar.
- [ ] [CODE] P1. Build a sports pipeline-check for the tick/MDPS middle leg (none exists) covering IS→tick→MDPS→features
      with CONTENT assertions, not just presence.

## Track D — CODEX: doc alignment · P1

- [ ] [DOC] P1. Rewrite `sports-adapter-dependency-order.md` (repoint to split entities; wire the T0/T1 gate note) +
      `sports-data-types-catalog.md` (UPPER per K0-(b); F3 timeframe) + `sports-gcs-path-ssot.md` (pipeline_mode + split
      entity rows).
- [ ] [DOC] P2. SUPERSEDED banner on `sports-integration-plan.md`; retire the deleted-scrapers §3 in
      `sports-live-odds-connectivity.md`; split-note `sports-scheduling-and-sharding.md`/`sports-fixtures-lifecycle.md`/
      `sports-batch-live.md`/`sports-data-source-coverage-matrix.md`; fix the 5 broken `related:` paths in
      `sports_master.md`.

## Track X — CLEANUP + plan reconciliation · P2

- [ ] [SCRIPT] P2. Flip `status: resolved` on the ~30 fully-checked-but-open sports issue docs (list in the audit's
      reconciliation) — pure hygiene.
- [ ] [PLAN] P1. Archive the fold-in plans as superseded-by this closeout
      (`sports_manifest_canonicalisation_2026_06_01`, `sports_pipeline_to_100pct_golden_window_first`) once their live
      items land here; keep the 2 near-done KEEP-ACTIVE plans standalone.
- [ ] [CLEANUP] P3. Drop the frozen 2018-2020 `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` scaffolding;
      correct `SPORTS_INSTRUMENTS.md` stale "Known gaps" (lineups player-id strip claim is false); junk-symbol guard for
      non-ASCII fixtures (sweep §D).

---

## Cross-AG finding (belongs to a prediction/tick close-out, tracked here for visibility)

- [ ] [DIAG] P1. **4,097 live `asset_group="prediction"` rows (+2 cefi/defi) physically in the sports bucket manifest**
      (Kalshi/Polymarket, `service=market-tick-data-service`, dates 2026-06-26…07-18). Two write paths ruled out; next:
      `ingest_kalshi_bulk_to_canonical.py`, `rebuild_prediction_manifest.py`, the sentinel fan-out. Cross-repo/SSOT
      class — NOTIFY OPERATOR (done in-session 2026-07-19).

## Operator decisions needed (blocking)

- **§U** registry-absent leagues (10,869 rows) · **§T** pre-2019 scope (122,864 rows) · **§O** the two
  `attempted_failed`/third-sentinel diagnoses before any relabel.

## Codex SSOTs (read before touching a track)

`codex/02-data/sports-gcs-path-ssot.md`, `…/sports-data-types-catalog.md`, `…/sports-data-source-coverage-matrix.md`,
`…/sports-adapter-dependency-order.md`, `…/availability-manifest-and-data-status.md`,
`…/honest-absence-downstream-handling.md`, `…/pipeline-mode-partition.md`, `codex/04-architecture/sports-batch-live.md`,
`codex/05-infrastructure/spot-vms-for-backfill.md`, `codex/12-agent-workflow/async-wait-and-poll-discipline.md` (rule
1a). Plan↔codex drift is review-blocking.

## Progress Log

- 2026-07-19 — Plan authored from the 6-agent audit. §Z (Track F P0) already FIXED (features-service@c6eb1f38); the
  writing fleet was stopped; corpus re-run pending behind the C1 manifest-atom fix. All other tracks open.
