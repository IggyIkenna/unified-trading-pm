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
umbrella: true
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
    /plans/active/sports_consolidated_audit_2026_07_19.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/active/sports_legacy_bucket_cutover_2026_07_16.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/sports_master_closeout_2026_07_21.md,
    /plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
    /plans/active/sports_odds_exchange_fixed_fork_2026_07_18.md,
    /plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md,
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    /plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md,
  ]
created: "2026-07-19"
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm:
  NA # ⛔ DO NOT flip to `planning` directly (operator ruling 2026-07-23). This plan has 96 open todos
  # across multiple repos with REAL cross-todo dependencies (casing revert must land registry+writers before data;
  # K1 before K2; league_id migration before the honest-coverage denominator fix; several Track S2 items explicitly
  # warn "do NOT attempt step N before step M" in PROSE ONLY, not machine-enforced sequential:/depends_on+
  # gate_on_depends) — flipping this doc's own assigned_vm would violate task_template.md's "10-20 todos, never
  # more" AO-DISPATCHED hard cap AND risks naive concurrent dispatch corrupting exactly the sequencing this plan
  # exists to protect (per §4's "partial parallelism is NOT expressible inside one plan — SPLIT" rule). To actually
  # dispatch any of this work to AO: extract the specific ready todo(s) into a NEW child plan (10-20 todos,
  # `assigned_vm: planning`) with `depends_on: [sports_consolidated_closeout_2026_07_19]` +
  # `gate_on_depends: true` if it has a real prerequisite, or `sequential: true` if its own todos share files —
  # never by editing this field.
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days:
  46 # RECALCULATED 2026-07-23 (was 12) — the 2026-07-23 reconciliation session grew this
  # plan from ~40 to 96 open todos (19 P0 / 37 P1 / 33 P2 / 5 P3) across the casing revert, the 3-bug venue/
  # instrument_type/chain code fix, the league_id migration, the 4 absorbed fold-in plans' live work, and the
  # honest-coverage/CF-8/CAS-tooling/odds-pipeline-dormancy tracks. Methodology: weighted by priority (P0 ~1.2d,
  # P1 ~0.6d, P2 ~0.3d, P3 ~0.15d avg, reflecting multi-repo code+data-migration work at P0 vs cleanup at P2/P3) —
  # a reasoned re-estimate, not false precision; re-check after the first few tracks land.
estimate_calibrated_ai_days: 36.8 # 46 x 0.8 (infra multiplier, unchanged estimate_class)
locked_by:
locked_since:
supersedes:
superseded_by: # corrected 2026-07-21 (plan-reconcile) — this doc still has 51 open/11 done todos, real unexecuted
  # work (canonical-honesty fixes, ODDS-LEAK cleanup, honest-coverage backfill tracks). sports_master_closeout_2026_07_21.md
  # is an entry-point redirect only ("that plan + the audit remain the detailed backing" — its own words), not a
  # replacement; this doc stays status: active and is the live execution surface. See its related: list instead.
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

- **data_type = LOWER-case everywhere for sports — FINAL, reconciled 2026-07-23.** ~~The original operator K0-DECISION
  (b) (2026-07-18) said UPPER~~ — that was reversed 2026-07-22 (codex `sports-data-types-catalog.md`, citing a 7-agent
  GCS audit that found zero uppercase `ODDS` objects on disk) for the odds-family types. **This session's reconciliation
  (2026-07-23) extends that to the WHOLE vocabulary, including `trades`/`TRADES`**: sports now matches every other
  asset_group's lower-case convention with no UPPER exception at all. **This REVERTS Track C's K1/K2 work below**
  (market-tick-data-service@2536b91c / @ad4f1872, ~260,298 GCS objects physically copied to uppercase paths +
  manifest-swapped, "shipped+verified" 2026-07-22) — that migration must be undone, not extended. Root cause of the
  registry-level mixed state that made K1/K2 look consistent at the time: `unified-api-contracts`'s
  `market_data_categories.py::DATA_TYPES_BY_ASSET_GROUP["sports"]` (lines ~211-246) DUAL-registers both spellings for
  exactly two of the 9 sports data types — "odds" AND "ODDS" (comment: "Canonical uppercase form per mega-audit R2"),
  "trades" AND "TRADES" (comment: "Canonical uppercase form (K1, mtds@2536b91c, 2026-07-22)") — while
  odds_snapshot/odds_movement/arbitrage_opportunity/odds_horizon_bucket/markets/outcomes/settlements/trades_inplay never
  got a matching uppercase entry, which is exactly why the deployment-ui's Distinct Values panel shows a mixed
  canonical/non-canonical pattern today (ODDS and TRADES pass, ODDS_MOVEMENT/ODDS_SNAPSHOT/ARBITRAGE_OPPORTUNITY fail).
  **The revert (Track C, new todos below) must touch all three layers**: (1) the registry — delete the "ODDS"/"TRADES"
  uppercase entries from `DATA_TYPES_BY_ASSET_GROUP["sports"]`; (2) the writers — revert `market-tick-data-service`'s
  `odds_api_adapter.py:761` (literal `"data_type": "ODDS"`) and `engine/orchestrator/sentinels.py:308,350,420` (literal
  `"data_type": "TRADES"`) back to lower-case; (3) the DATA — migrate the ~260,298 GCS objects + manifest rows K1/K2
  already moved to uppercase back to lower-case (mirror the K1/K2 migration procedure in reverse). Sequencing matters:
  revert the registry+writers FIRST (else new rows keep arriving uppercase while old ones are being moved back), then
  migrate the data. **NOT YET EXECUTED** — this is a decision + plan only; the actual revert (GCS/manifest data
  movement) waits until this reconciliation pass is fully committed, per operator instruction.
- **Fixtures entity split**: `entity=fixtures_schedule` (schedule fields incl. `round`) + `entity=fixtures_outcomes`
  (scores/status), under `pipeline_mode=batch_api_football/`. The legacy bare `entity=fixtures/` is FROZEN (last real
  write 2026-05-23) and must not be read or written. **The manifest `data_type` must record the split entities, not the
  `"FIXTURES"` umbrella** (§ C1). **NOTE (2026-07-23): this freeze is currently violated by at least 3 live artifacts**
  — `sports_manifest_canonicalisation_2026_06_01.md` (treats bare `entity=fixtures/` as active as of 07-17),
  `sports_p2_history_apifootball_2015_to_present_2026_06_27.md` (shipped `_read_fixtures_entity_with_schedule_fallback`,
  an active fallback READ of the frozen path, `instruments-service@e1524d21`), and
  `sports_catalog_league_grain_only_scope_2026_07_08.md` (writes reference data to bare
  `entity={fixtures,teams, injuries}/` under a different namespace). See Track S/E's new todos below — these are being
  reconciled, not silently left contradicting this rule.
- **timeframe is its own column** — never baked into `data_type`. `odds_horizon_bucket_{15m,1h,4h,1d}` is a dead cohort.
- **Buckets** (via `resolve_bucket_name`, never string-interpolate): reference → `instruments-store-sports-prd`, odds →
  `market-data-tick-sports-prd` (the `market-data-sports-prd` name 404s — the real name carries a `tick-` infix),
  features → `features-sports-prd`.
- **Honest absence, never a placeholder**: `attempted_failed` is a real-failure signal — root-cause before any relabel
  (§ B2 precedent).
- **venue / instrument_type / chain — ROOT-CAUSED 2026-07-23, all three are the SAME bug class: asset_group-blind
  positional colon-parsing of the canonical id, written for CeFi/DeFi's 3-4-segment `VENUE:TYPE:SYMBOL` shape and never
  gated off before running on sports' 8-segment `SPORT:BOOKMAKER:MARKET:LEAGUE:SEASON:HOME-AWAY::SELECTION` id.**
  Confirmed via direct code read (not inferred), all in `market-data-processing-service`'s
  `app/core/canonical_writer_shaping.py` unless noted:
  - **`venue` reads `parts[0]` (the SPORT token, e.g. "FOOTBALL") instead of `parts[1]` (the BOOKMAKER token)** — the
    live sites (`live_workers.py:144,177,522`, `live_workers_chain.py:329`, `batch_workers.py:159`,
    `candle_write_mixin.py:290,351`) all do `instrument_id.split(":")[0]`, correct for CeFi/DeFi, wrong for sports. This
    is the direct mechanism producing the non-canonical `FOOTBALL` and `UNKNOWN` (the same call sites' fallback
    sentinel) venue values.
  - **`instrument_type` reads `parts[1]` (the BOOKMAKER token) via `_type_token_from_canonical_id`
    (`canonical_writer_shaping.py:257-266`)** — `len(parts) >= 3` fires on any 3+-segment id, not gated by asset_group;
    called unconditionally from `_infer_instrument_type` (`canonical_writer.py:252`). This is the confirmed mechanism
    producing the entire bookmaker-name-in-instrument_type cluster (PADDYPOWER, PINNACLE, betmgm, betway, bovada, coral,
    fanduel, ladbrokes_uk, skybet, unibet_uk, williamhill, plus bare `ODDS`/`odds`/`SPORT`) — **100% of today's 16
    distinct sports instrument_type values are non-canonical**, none are missing-from-registry; all 7 bookmaker names
    checked exist in the UAC venue registry already, just mis-cased/mis-placed.
  - **`chain` reads `parts[2]` (the MARKET token, e.g. "H2H"/"MATCH_ODDS"/"SPREADS") via `_infer_chain`
    (`canonical_writer_shaping.py:499-536`)** — fires whenever `len(parts) >= 4`, same missing asset_group gate.
    **Sports should NEVER populate `chain` at all** — confirmed via `unified-api-contracts`'s
    `_sports_prediction_contracts.py`: the `SPORTS_ODDS_TRADES` SchemaContract has no `chain` column in its definition,
    unlike `PREDICTION_PREDICTION_MARKET_*`'s contracts, which correctly declare `chain` as a required, STATICALLY
    per-venue-assigned column (`polymarket_adapter.py:591,667` hardcodes `"chain": "POLYGON"` — exactly the
    UAC-static-mapping-done-once pattern that's the right model, just correctly scoped to `prediction`, not `sports`).
    Sports' 3 non-canonical `chain` values (H2H, MATCH_ODDS, SPREADS) are 100% a bug, not a missing mapping to add.
  - **The fix (Track C, new todos below)**: gate all of the above on `asset_group`. For sports specifically: venue
    should resolve from `parts[1]` (bookmaker) — the same token `instrument_type` is wrongly reading today; `chain`
    should never be written for sports (null, matching its SchemaContract); `instrument_type` should resolve the MARKET
    token (`parts[2]`) through the existing `ODDS_API_MARKET_TO_CANONICAL` vocabulary (already UPPER on `market_key` —
    Track C's F2 already named promoting this vocabulary, this is now confirmed as the correct target, not merely a
    suggestion). Of the 9 non-canonical venue VALUES seen in Distinct Values: 4 are casing/aliasing variants of
    already-registered names (LADBROKES_UK→LADBROKES, UNIBET_UK/UNIBET_EU→UNIBET, SPORT888→BET888SPORT — simple
    alias-map or writer fix, no registry gap); 2 are the tracked cross-AG bleed (KALSHI, POLYMARKET — belong to
    `asset_group=prediction`, same class as the Track "Cross-AG finding" below); 1 is residual data from an
    explicitly-removed venue (SMARKETS — deleted from all repos per codex, no new rows should ever appear); 2 are the
    venue-from-parts[0] bug above (FOOTBALL, UNKNOWN). **Target: by the end of this closeout, the deployment-ui's sports
    Distinct Values panel (venues / instrument_types / data_types / chains) reads 0 non-canonical across all four
    axes.**

---

## Track F — FEATURES: the live data-correctness defect + the ML-ready re-run · P0 (FOUNDATION GATE)

- [x] [CODE] P0. ✅ §Z season_context fabrication FIXED — **features-service@c6eb1f38** (QG green). Gate derives
      matchday from `round`; `_competition_phase`/games_remaining honest `None` on NaN; 2 regression tests. The 8-VM
      re-run fleet writing the fabricated pattern was STOPPED.
- [x] [DATA] P0. ✅ **RE-SCOPED 2026-07-24 (was mis-scoped "2019→present" — 2017-2019 + pre-2020-06-06 2020 are now
      MOOT, already resolved by the 2020-06 floor wipe, not a re-run target).** Per the operator-ruled 2020-06-06 sports
      data floor (`/codex/02-data/sports-2020-06-data-floor.md`, `sports_master_closeout_2026_07_21.md` §1): pre-floor
      `derived_features` is fabrication-by-construction and gets DELETED, not regenerated. The pre-floor GCS wipe
      (`deployment-service@78a0aa4`, EXECUTED + VERIFIED 2026-07-21) already deleted 212,519 pre-floor
      `features-sports-prd` objects (2017-01-01…2020-06-05, spot-verified 0 pre-floor days remain) — this supersedes and
      moots the re-run work this todo originally scoped for 2017-2019 and Jan-Jun 2020. **Remaining live scope, per
      master_closeout §2-F: post-floor only** — the Jun-Dec 2020 residual + **2,821 fabricated cells measured inside
      2021-2026** (from the retracted-CLEAN-claim census below), which the pre-floor wipe does NOT touch (they postdate
      the floor and are real trading data, not fabrication-by-construction — they need re-run + targeted purge, not
      deletion-by-floor). Clean corpus-wide re-run, bounded per-year SPOT chunks; re-run ANY chunk **ON-DEMAND** instead
      if it hits the `--force`×SPOT within-year preemption-replay hazard (confirmed on 2019+2020 pre-floor-wipe testing)
      — does **NOT** depend on Track C's C1 fixtures-manifest-atom migration (unrelated instruments-service bookkeeping;
      this re-run reads fixture parquets, already correct via the 2026-07-18 round-derivation/catalogue-repoint/backfill
      sweep the audit confirmed terminal, plus its split-entity read fix) — gated only on the season_context-fabrication
      code fix (line above) + a fresh tarball (both done). Watchdog on a validated creation-time metric (whole-date
      filter, not an hour pattern — cf. codex async rule 1a). **⚠️ CORRECTION 2026-07-20 — the earlier "VERIFIED
      corpus-wide: 2021-2026 CLEAN" claim on this line was OVERSTATED and is RETRACTED** (it sampled only days the
      re-run had already rewritten). A creation-time census of all 124,554 objects + a 250-object stratified content
      sample found **100% fabrication among all pre-fix objects (249/250)** — 35,045 fabricated parquet objects total
      measured at the time, of which 2,821 are inside 2021-2026 (post-floor, still live scope) and the remainder is now
      moot (pre-floor, wiped). Structural gap this surfaced, still live: `--force` only overwrites days the run produces
      output for, so a fabricated object on a zero-output day survives any number of re-runs (observed `day=2019-04-20`,
      now moot — but the same defect could affect a post-floor zero-output day, so the PURGE todo below stays mandatory
      regardless of re-run coverage). Full evidence:
      `issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md`. **This todo is NOT done for the post-floor
      residue — the PURGE and re-verify todos below are NOT yet safe to dispatch until this one is done for Jun-Dec
      2020 + 2021-2026; no machine gate enforces that today (this plan is `assigned_vm: NA`, not currently
      AO-dispatched) — if this chain is ever extracted into its own AO-dispatched plan, give it `sequential: true`
      (task_template.md §4) rather than relying on this prose note.**
- [x] [DATA] P0. ✅ **RESOLVED VIA PRE-FLOOR WIPE, not a re-run (was: "Re-run 2017+2018 `derived_features`
      ON-DEMAND").** 2017 and 2018 are 100% pre-floor (before 2020-06-06) — the measured 26,089 fabricated parquet
      objects for these years (2018 alone 22,077, the corpus's largest year) were deleted by the pre-floor GCS wipe
      (`deployment-service@78a0aa4`, 2026-07-21, part of the same 212,519-object `features-sports-prd` deletion cited
      above), not regenerated. Regenerating fabricated pre-floor data would have re-created fabrication-by-construction
      — the floor ruling's whole point is that this population should not exist at all. No further action needed here.
- [ ] [DATA] P0. **PURGE the fabricated POST-FLOOR remainder (Jun-Dec 2020 + 2021-2026 only — 2017-2019 + pre-06-06 2020
      are moot, already deleted by the pre-floor wipe), only after the re-run todo above is done for that same
      post-floor scope** — overwriting alone is provably insufficient (a re-run never rewrites a day it produces no
      output for, so a fabricated object on a zero-output day survives). Snapshot the delete list FIRST (GCS soft-delete
      gives a 7-day recovery window), then delete every POST-FLOOR `derived_features` parquet still carrying a
      PRE-`2026-07-19` GCS creation timestamp — do NOT re-touch pre-floor dates, they're already handled by the wipe's
      own snapshot+delete. Honest absence beats an invented `competition_phase`
      (`/codex/02-data/honest-absence-downstream-handling.md`). **Not `[OPERATOR]`-gated** (unlike the K1/K2 GCS-delete
      below, which is): the soft-delete's 7-day recovery makes this reversible-for-a-week, not the irreversible class
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` reserves for human-only sign-off — the snapshot-first
      step is this todo's safety net.
- [ ] [DATA] P0. **Re-verify by CENSUS, not sampling, only after the PURGE todo above is done** — the terminal check is
      "zero pre-fix-dated POST-FLOOR `derived_features` objects remain" (pre-floor is separately verified 0 by the
      wipe's own census), decidable from object metadata alone (a GCS creation-time listing, not a content sample).
      Sampling is what produced the retracted CLEAN claim above. **Done when**: the census returns 0 post-floor objects
      with a pre-`2026-07-19` creation timestamp.
- [ ] [DIAG] P1. `sfi_progressive_features` is corpus-empty (1 manifest row) despite a documented 2020→today window —
      find why the backfill never ran, then run it. Without it every HT/progressive-SFI ML feature is unavailable.
- [ ] [DIAG] P2. `is_promotion_relegation` is hardcoded `False` (dead) — wire it from the standings relegation-zone
      classification (`_compute_league_batch` already computes it) or formally retire it + its points_at_stake
      multiplier.
- [ ] [DIAG] P2. Settle whether `clv_*`/`odds_movement_*` all-null in odds_features is honest-absence or a gap (wider
      multi-date spot-check) before relying on them for ML. **Likely-related lead, not yet confirmed**: Track H's
      R23-class finding below root-causes MDPS's `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` derived
      products as dead code (never scheduled — the only live sports MDPS job only touches `odds_horizon_bucket`); if
      `odds_features`'s `odds_movement_*` columns source from that same never-run adapter, their null-ness would be
      honest-absence by construction — but this doc never confirms that sourcing, and `clv_*` isn't obviously tied to
      the same mechanism, so don't assume it without checking. **Done when**: a written conclusion states which it is
      (honest-absence vs. gap), with sample dates + result counts cited, before these columns are used for ML training.
- [ ] [DATA] P2. Purge the 4 dead dimension groups still inflating the features manifest (players/coaches/referees/
      rounds, 4,216 rows each) — already operator-ruled, not a fresh decision (see
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md`'s §A2 ruling batch). **Done when**: a
      manifest census for these 4 dimension groups returns 0 rows.

## Track C — CANON: data_type LOWER-case + venue/instrument_type/chain + manifest atom · P0

- [ ] [CODE] P0. **C1 — migrate the fixtures manifest atom** from hardcoded `"FIXTURES"` to `FIXTURES_SCHEDULE`/
      `FIXTURES_OUTCOMES` across the 8 call sites (`sports_reference_fixtures.py:242,279`, `process_write.py`,
      `writers.py:219`, `catalogue.py:136`, `process_completeness.py`, `process_preflight.py`,
      `process_zero_records.py`, `sports_fixtures_daily_repoll.py`) so the manifest atom == the writer atom. Gates the
      F-track re-run. **9th call site found 2026-07-23 (codex fix pass on `honest-absence-downstream-handling.md`)**:
      `unified-api-contracts`'s `_honest_coverage_logic.py:293` —
      `SCHEDULE_DEFINING_DATA_TYPES = frozenset({"FIXTURES"})` — is a live-code consumer of the SAME atom this todo
      migrates, and this todo's own 8-file checklist omits it. Verified as of 2026-07-23 both the constant AND the
      manifest atom are still `"FIXTURES"` (not yet mismatched — this is a **forward-looking bug**, not a
      currently-firing one): if C1 ships the 8-file migration without also updating this constant +
      `is_resolved_schedule_empty()`'s consumers, `SCHEDULE_DEFINING_DATA_TYPES` silently stops matching anything
      post-migration. Add as a 9th call site.
- [ ] [VERIFY] P0. **BLOCKED-UPSTREAM (2026-06-24 — slot-23 GCS spot-check)**: After the writer populates Q5/Q6
      columns + the entity-split lands, confirm `FIXTURES_SCHEDULE` carries the 9 HT/ET/PEN phase-timestamp columns and
      `FIXTURES_OUTCOMES` carries the 11 score-distinction columns populated for completed fixtures (regulation /
      ET-only / ET+PEN cases; NEVER collapse pen-shootout score into a single field). Spot-check on real GCS rows for a
      completed matchweek across the Top-5 EU leagues. **[VERIFY][UI]** the deployment-ui schema modal renders both
      entity schemas — this touches a UI repo, so any tick requires `pw:L2 ✓`
      (`npx playwright test     --project=chromium tests/smoke/`) + a cited regression spec per CLAUDE.md UI
      playwright-gate HARD RULE; on a fleet VM with no dev server, keep `[BLOCKED-PLAYWRIGHT]`.
      <!-- BLOCKED-UPSTREAM evidence (2026-06-24 slot-23):
                                                                                                                                                                                                                                                                                                                                       GCS check: entity=fixtures_schedule + entity=fixtures_outcomes DO NOT EXIST in
                                                                                                                                                                                                                                                                                                                                       gs://instruments-store-sports-prd-central-element-323112/sports_reference/by_date/ — only entity=fixtures.
                                                                                                                                                                                                                                                                                                                                       Q5/Q6 columns absent from ALL sampled parquets: EPL 2026-05-17, Ligue1 2026-05-17, SerieA 2026-05-09,
                                                                                                                                                                                                                                                                                                                                       LaLiga 2026-05-09, Bundesliga 2026-05-10, Norway 2026-06-21 (written 2026-05-23 before Q5/Q6 deploy).
                                                                                                                                                                                                                                                                                                                                       Root cause: entity-split writer commit 254fb843 ("entity-split fixtures→fixtures_schedule+fixtures_outcomes;
                                                                                                                                                                                                                                                                                                                                       writegate strict mode") is on origin/live-defi-rollout as of 2026-06-24 but NOT yet on main.
                                                                                                                                                                                                                                                                                                                                       Q5/Q6 additive write path (48c54805, 2026-06-05) IS on main — but existing entity=fixtures parquets
                                                                                                                                                                                                                                                                                                                                       were all written before 2026-06-05 and the "old-path-copy" branch does not re-process them.
                                                                                                                                                                                                                                                                                                                                       Unblock: 254fb843 promotes main → IS Docker rebuild + VM relaunch → migrate_fixtures_split.py runs
                                                                                                                                                                                                                                                                                                                                       on real sports buckets → new entity=fixtures_schedule+fixtures_outcomes paths appear → re-run VERIFY. --> (FOLDED
      IN from sports_fixtures_schema_split_completion_2026_06_20, 2026-07-15, plan-reconcile §6 operator ruling)
      **MERGED here 2026-07-24** (plan-hygiene line-cap remediation, `plan_line_cap_remediation_2026_07_23.md` decision
      #6) from `sports_p2_features_history_to_ml_ready_2026_06_27.md`'s "Folded-in scope 2026-07-15" section — this
      closeout now owns the item going forward (it's the identical migration this Track's C1 targets). The source plan
      is archived, zero live work remaining, at
      `/plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md`, with its own copy of this todo
      flipped closed and pointing back here. This also resolves the §Track-S2 "Reconcile
      `sports_p2_features_history_to_ml_ready_2026_06_27.md`" todo below (its overlap concern is now moot — the item is
      merged, not duplicated).
- [x] [CODE] P0. ✅⏪ **K1 — emit UPPER at the LIVE writer SHIPPED + VERIFIED (2026-07-22) — SUPERSEDED 2026-07-23, MUST
      BE REVERTED.** (was: fix `_build_sports_shard_path` (`venue_fetch.py:871-900`) + the sentinel row-key builders per
      the dual-accept pre-step ordering this todo specified). The dual-accept pre-step shipped first as designed
      (`market-data-processing-service@fa4281d2`), then the atomic writer flip (`market-tick-data-service@2536b91c`, 7
      call sites). **This session's casing reconciliation (see Canonical target above) decided sports data_type is
      LOWER-case for ALL types, no UPPER exception — this todo's UPPER writer flip is now the WRONG direction and is
      tracked for revert in the new todo below, not extended.** Kept here (not deleted) as the historical record of what
      shipped and why it's being undone.
- [x] [DATA] P1. ✅⏪ **K2 — migrate the historical lower-case rows UP SHIPPED + VERIFIED (2026-07-22) — SUPERSEDED
      2026-07-23, MUST BE REVERTED.** K2's real, correct scope (the `batch_odds_api` axis K1 fixes) migrated: GCS copy
      260,298/260,298 objects (0 failures), manifest-swap 373,296 ADD / 320,469 REMOVE, VERIFY PASSED. **Same
      supersession as K1 above** — this data now needs to move back to lower-case, not stay UPPER. Full original
      evidence in `sports_master_closeout_2026_07_21.md`'s "fourth/fifth/sixth wave" Progress Logs; the revert procedure
      should mirror this same GCS-copy + manifest-swap + VERIFY pattern, in reverse.
- [ ] [DATA] P0. **NEW — revert K1/K2's casing migration: registry FIRST, then writers, then DATA LAST** (uppercase →
      lowercase; that order matters — data-last stops new rows arriving uppercase while the historical migration is
      still moving old ones back, which would re-dirty the corpus mid-migration). **NOT YET EXECUTED — decision + plan
      only, per operator's explicit "reconcile docs first, execute after" instruction (2026-07-23).** (1) Registry:
      delete the "ODDS"/"TRADES" uppercase entries from `unified-api-contracts`'s
      `market_data_categories.py::DATA_TYPES_BY_ASSET_GROUP["sports"]` (currently lines ~213, ~224) — keep only the
      lower-case "odds"/"trades" entries. (2) Writers: revert `market-tick-data-service`'s `odds_api_adapter.py:761`
      (literal `"data_type": "ODDS"`) and `engine/orchestrator/sentinels.py:308,350,420` (literal
      `"data_type": "TRADES"`) back to lower-case literals. (3) Data: migrate the 260,298 GCS objects + 373,296 manifest
      rows K1/K2 moved to uppercase back to lower-case (GCS copy + manifest-swap + VERIFY, mirroring K1/K2's own
      procedure in reverse). **Done when**: a corpus-wide `data_type` census for sports returns zero UPPER-case values
      and the QG assertion todo below passes.
- [ ] [CODE] P0. **NEW — fix 3 asset_group-blind positional-parse bugs in `market-data-processing-service` (F1/F2
      SHARPENED 2026-07-23: 3 bugs, not 2): gate venue/instrument_type/chain on asset_group.** For sports: venue ←
      `parts[1]` (the bookmaker token — not the SPORT token `parts[0]` it wrongly reads today); `instrument_type` ← the
      MARKET token `parts[2]` resolved through `ODDS_API_MARKET_TO_CANONICAL` (lower-cased to match the casing decision
      above — not the BOOKMAKER token `parts[1]` it wrongly reads today); `chain` ← never written for sports, always
      null (not the MARKET token `parts[2]` it wrongly reads today — sports has no `chain` column in
      `SPORTS_ODDS_TRADES`'s SchemaContract at all). Apply the same fix to `build_instrument_catalogue.py:723-739`'s
      `_instrument_type_from_id` (IS catalogue side) together, same session. Confirmed via direct code read (see
      Canonical target section above for full detail + line numbers): (a) venue via
      `live_workers.py`/`live_workers_chain.py`/`batch_workers.py`/`candle_write_mixin.py`'s
      `instrument_id.split(":")[0]` — produces the non-canonical `FOOTBALL`/`UNKNOWN` venue values; (b) instrument_type
      via `_type_token_from_canonical_id` (`canonical_writer_shaping.py:257-266`, called from `canonical_writer.py:252`)
      — produces 100% of today's 16 distinct instrument_type values as non-canonical (the bookmaker-name cluster + bare
      ODDS/odds/SPORT); (c) chain via `_infer_chain` (`canonical_writer_shaping.py:499-536`, called from
      `canonical_writer.py:253`). Contrast `PREDICTION_PREDICTION_MARKET_*`, which correctly declares `chain` as a
      required STATIC per-venue constant (e.g. `polymarket_adapter.py:591,667` hardcodes `"chain": "POLYGON"`) — that's
      the right UAC-static-mapping model, already correctly built, just correctly scoped to `prediction`, not `sports`.
      Do NOT touch the deliberate `mdps_odds_horizon_bucket` `venue=ODDS_API` aggregate (124,294 rows, reconciled
      2026-07-14) — that's a different, intentional aggregate identity, not this bug. **Done when**: the Distinct Values
      panel + the QG assertion todo below both read 0 non-canonical for all three axes.
- [ ] [DATA] P1. **NEW — venue vocabulary cleanup, 4 distinct dispositions for the 9 non-canonical values** (once the
      parse-bug fix above stops new pollution — fix the parser FIRST, re-stamp SECOND, same ordering lesson as the
      original F1/F2 note): (1) casing/aliasing rewrite — LADBROKES_UK→LADBROKES, UNIBET_UK/UNIBET_EU→UNIBET,
      SPORT888→BET888SPORT (all 4 already exist correctly-cased in the UAC venue registry, this is a pure re-stamp, no
      registry gap); (2) cross-AG bleed — KALSHI, POLYMARKET rows belong to `asset_group=prediction`; same remediation
      pattern as the "Cross-AG finding" section below (root-cause the write path, then purge); (3) residual-only —
      SMARKETS is an explicitly deleted venue (codex: "removed from all repos, no manifest rows should be expected") —
      any remaining rows are stale residue to purge, not a registry gap; (4) parse-bug residue — FOOTBALL/UNKNOWN clear
      once the venue-parts[0] fix above ships and existing rows are re-stamped. Also still fix the original footystats
      legacy bundle mislabel (`venue=ODDS_API`→`FOOTYSTATS`, 42,476 rows) — unrelated to the parse bug, a separate
      writer defect.
- [ ] [CODE] P0/P1. **EXCHANGE_ODDS vs FIXED_ODDS fork — ABSORBED 2026-07-23, full 9-step sequence** (was a 1-line
      placeholder; `sports_odds_exchange_fixed_fork_2026_07_18.md` is now archived/superseded, all 10 of its todos
      pulled in below verbatim — priority CORRECTED from this section's earlier P2 to match the source plan's real P0/P1
      mix, which includes a live OPERATOR block):
  - [ ] [OPERATOR] P0. Confirm the ambiguous EXCHANGE_ODDS/FIXED_ODDS venue→class mapping: bare `BETFAIR` (33 rows),
        `ODDS_API` (33, an aggregator fitting neither class), and `PINNACLE` (32,616 rows — sportsbook by mechanism, but
        UAC models it `PINNACLE_AS_LINE` in `_SNAPSHOT_VENUES`, so confirm FIXED_ODDS vs a PINNACLE_AS_LINE special
        case) remain BLOCKED-OPERATOR-DECISION. Non-ambiguous poles may proceed to design without waiting: EXCHANGE_ODDS
        = `BETFAIR_EX_UK`/`BETFAIR_EX_EU`/`SMARKETS`/`MATCHBOOK`; FIXED_ODDS = `BETFAIR_SB_UK`/`BETMGM`.
  - [ ] [DATA] P0. Pre-drain the sports odds writers before any GCS object move — `odds` (pre-fork instrument_type,
        561,260 rows) is written live; stop all sports odds-writing jobs both clouds + snapshot first.
  - [ ] [DATA] P1. Add UAC contract entries for EXCHANGE_ODDS/FIXED_ODDS BEFORE touching data (contracts-first,
        deliberately — manifest-first previously caused the tradfi CME manifest↔disk↔registry divergence, repaired
        `@bd115230`, must not repeat). Keep the legacy `odds` contract entry live for the dual-read window.
  - [ ] [DATA] P1. Dual-read `odds` + `EXCHANGE_ODDS`/`FIXED_ODDS` in `lookup_contract` during the migration window; add
        a UAC unit test covering both paths.
  - [ ] [DATA] P1. Move the `instrument_type=odds/` GCS objects to `exchange_odds/`/`fixed_odds/` per the venue→class
        map via UTL `gcs_copy_object`/`gcs_delete_object` (never subprocess gsutil); snapshot → move → independent
        re-read count; idempotent + resumable.
  - [ ] [DATA] P1. Update MDPS `dependency_checker`'s hive-token matcher for the new instrument_type partitions —
        confirm no consumer of the legacy `odds` hive token goes orphaned.
  - [ ] [DATA] P1. Reconcile the availability manifest to the new partitions LAST, only after GCS move + dual-read are
        proven — verify the shard atom is identical across writer/manifest/status/gate.
  - [ ] [DATA] P2. Cut the live sports odds writers over to the new instrument_types and un-drain.
  - [ ] [DATA] P2. Retire the legacy `odds` contract entry + the dual-read path once no object/manifest row remains
        under `odds` and a full corpus re-read confirms parity.
  - [ ] [REVIEW] P2. Post-phase codex audit: update `availability-manifest-and-data-status.md` + the sports
        canonical-naming doc with the new instrument_types + migration order.
- [ ] [REVIEW] P1. QG assertion: sports `data_type` ∈ the UAC lower-case sports vocabulary (no UPPER entries once the
      revert above ships), `venue` ∈ the UAC venue registry (never a vendor casing variant, never a prediction-market
      venue, never a deleted venue), `instrument_type` ∈ the declared sports vocabulary (never a bookmaker name),
      `chain` is always null/absent for sports — so this whole class cannot silently return. **This is the
      QG-enforceable version of the Distinct Values target**: the deployment-ui's sports panel for venues /
      instrument_types / data_types / chains should read 0 non-canonical across all four axes once Track C lands.

## Track S — STORE: bucket hygiene + legacy path elimination · P1

- [ ] [DATA] P1. Complete `sports_legacy_bucket_cutover_2026_07_16` T2.9 (MDT schema drift) + T2.10 (47,253 phantom
      `api_football×trades` rows) + its post-phase codex audit.
- [ ] [CODE] P2. Eliminate (or document) the legacy bare `entity=fixtures/` (no `pipeline_mode=`) write path still
      active today alongside the canonical split writer (5-league subset).
- [ ] [CLEANUP] P2. Snapshot-then-cull the dead `sports_reference_v2/by_date/` dual-layout (frozen 2026-04-20, no
      entities). Confirm no reader consumes it first.
- [ ] [DOC] P2. **Finding C correction (2026-07-23): this was mis-scoped, downgraded from the original P1/HIGH.**
      `sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md` is `status: resolved` (corpus-destroying
      risk already remediated, byte-exact GCS soft-delete restore verified) — only its 1 remaining open todo needs
      merging in: correct the cutover runbook's canonical-is-a-superset premise for raw odds on early dates.
      `sports_canonical_migrated_odds_mistamped_footystats` has no standalone issue doc — it's the footystats
      legacy-bundle mislabel already tracked as its own Track C todo above (venue vocabulary cleanup, `venue=ODDS_API`→
      `FOOTYSTATS`, 42,476 rows). **Done when**: the cutover runbook is corrected and cites this doc.
- [ ] [DIAG] P2. **NEW 2026-07-23 (decision 16) — investigate 2 unfiled loose ends from the OR-1 investigation.** (1)
      standings/teams season-2026 data being written under historical `day=` partitions across ~3,050 days in both
      buckets; (2) an unidentified writer producing a cartesian-junk `player_values` object on 2026-06-22. Root cause
      unknown for both — operator decision: investigate now rather than deferring, since both are currently unowned and
      could be actively recurring. Detail: see the OR-1/player_stats-union issue doc's own RE-TRIAGE (2026-07-23).

## Track E — ENTITY-SPLIT: repoint every remaining stale consumer · P1 (sports-specific, no defi analog)

- [ ] [CODE] P1. Repoint the remaining stale `entity=fixtures` consumers (sweep §R's ~9-file list:
      `sports_dependency.py`, `sports_fixtures_daily_repoll.py`, `backfill_weather.py:154`,
      `backfill_sports_fixture_stats_manifest.py:91`, `rescan_sports_fixtures_canonical.py:328,452`,
      `enumerate_expected_universe.py:1902`, `migrate_sports_per_league.py`,
      `reconcile_sports_blank_empty_reason_2026_06_24.py`) to `fixtures_schedule` (+`fixtures_outcomes` where scores are
      needed).
- [ ] [CODE] P1. **Wire the T0/T1 dependency gate for real: make every real caller of the pre-flight pass `date=`.**
      Currently the pre-flight only fires `if date is not None` and no caller passes it, so the fail-loud boundary is
      unreachable (`sports_t0_t1_dependency_gate_never_wired_2026_07_15`). **Done when**: a T0-before-T1 ordering
      violation actually raises in a test (not just "the code path exists but is never hit").

## Track O — ODDS-LEAK: post-kickoff contamination + the B2 dead-zone · P1

- [x] [DATA] P0. ✅ **RETENTION CLIFF DISSOLVED — the restore was never the right recovery, and no deadline applies.**
      Operator approved the controlled-window restore (2026-07-20); executing it measured-first showed the premise was
      **wrong on two counts**, so it was NOT run. **(1) The soft-deleted generation does not hold the true values.** The
      v9 clobber ran FOUR times, each rebuild re-stamping the previous stamp — measured across the live index + 8
      `_index/snapshots/` objects: | index state | `attempted_at` window (BETFAIR/MATCHBOOK/PINNACLE) | verdict | | ---
      | --- | --- | | `pre_migration_v9_2026-07-12_availability_index.parquet` (07-12T22:19Z) | 2026-06-21 14:23:10 →
      22:41:51 (29,922s) | ✅ TRUE | | `pre_migration_v9_2026-07-13…` / `pre_force_consolidate_…06_36` | 2026-07-12
      23:17:54 → 23:18:04 (10s) | clobber #1 | | `pre_cf8_backfill_20260713T210725Z` | 2026-07-13 06:16:02 → 06:16:12
      (10s) | clobber #2 | | `pre_cf8_backfill_retry_20260713T233900Z` | 2026-07-13 21:23:42 → 21:23:49 (7s) | clobber
      #3 | | LIVE `availability_index.parquet` | 2026-07-13 23:56:41 → 23:56:48 (7s) | clobber #4 | The soft-deleted
      generation `#1783986822147154` was created 2026-07-13T23:53:42Z — **between clobber #3 and #4** — so restoring it
      would have yielded the 21:23 window: another clobbered value mistaken for the truth. **(2) The true values need no
      restore at all.** They survive in `_index/snapshots/pre_migration_v9_2026-07-12_availability_index.parquet` — an
      ordinary LIVE object (112,278 triplet rows, 8.3h spread), no soft-delete, no retention deadline, readable with a
      plain `cp`. **Also measured**: pausing the consolidator cron would have fired an ERROR-level page —
      `consolidator_liveness.py` has an explicit `REASON_SCHEDULER_PAUSED` branch ("deterministically dead, will NOT
      self-recover") on a `*/2` watchdog, wired to PagerDuty/Telegram. The approved op would have paged an away
      operator, risked a live 5.3M-row index, and recovered nothing. Evidence: `scratchpad/verify_preclobber.py`,
      `scratchpad/ladder.py`.
- [ ] [DATA] P1. **Repair `attempted_at` on the 112,277 rows from the named pre-clobber snapshot** (source above).
      DELIBERATELY NOT done unsupervised: the write races the same every-60s consolidator, and with the cliff gone there
      is no longer any reason to take that risk without a human watching. Do it in a normal window: verify whether the
      consolidator carries forward existing index rows (it merges per-VM shards; these rows have no new shards) — if it
      does, the edit persists and no pause is needed at all.
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
- [ ] [DIAG] P1. **NEW 2026-07-23 (decision 15) — investigate + fix the MTDS live-odds fixture_id-blank collapse.**
      Flagged 🔴 NOTIFY-OPERATOR as an ongoing live issue, last directly observed 2026-06-20 — status since then is
      unconfirmed. Operator decision: investigate and fix now, not just re-check status, since it was already flagged as
      a live NOTIFY-OPERATOR item a month ago. Detail: see the SFI/HT-odds pit-gate issue doc's own RE-TRIAGE
      (2026-07-23).

## Track H — HONEST-COVERAGE: manifest honesty + denominators · P1

- [ ] [DIAG] P0. **NEW 2026-07-23 (decision 8) — get AWS IAM access now and investigate the sports ODDS_API (TRADES)
      capture pipeline dormancy** — do not defer, THE single highest-priority item in this whole closeout. Zero sports
      manifest writes observed for ~12h+ at last check; the only odds-adjacent Cloud Run jobs last ran 2026-03-29 (~4
      months ago); no matching GCP Cloud Scheduler entry found; AWS-side scheduling (EventBridge/ECS) and
      persistent-VM-internal crontabs could NOT be checked (IAM-denied) — that access is what this todo needs first. If
      confirmed dormant, every other honest-coverage/backfill claim in this closeout is being measured against a dataset
      that may not be growing — this matters more than any single casing/naming fix above. Detail:
      `issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`.
- [ ] [DIAG] P1. Why do `reason`/`error_code`/`empty_reason`/`classified_error` read back blank for the sports odds
      manifest (schema gap or C5-class silent-empty) — blocks root-causing Track O's two open `[DIAG]` items below (the
      112,277 `attempted_failed` triplet root-cause and the 139,620 `empty_confirmed` emitter identification).
- [ ] [DIAG] P2. Confirm sports genuinely never emits `expected_unattempted` in the odds manifest (0 of 1.97M) by
      design, or fix the miscoercion into `empty_confirmed`.
- [ ] [DATA] P1. Fix `AG_STALENESS_BUDGET_SEC["sports"]` at **≥1800s** (the observed refresh cadence, per
      `sports_manifest_read_staleness_budget_missing_2026_07_15`'s own ~11-min blob-age swing measurement), not 180-240s
      (**citation corrected 2026-07-24**: the conflicting merge-duration-derived value is from sweep §J, NOT from the
      issue doc — `sports_manifest_read_staleness_budget_missing_2026_07_15` actually already recommends 1800s, matching
      this line's own target value; this line previously misattributed §J's rejected 180-240s value to the issue doc.
      See the correct attribution already present in this same file's "Staleness budget — same defect as sweep §J,
      conflicting fix values" entry below) — merge §J's and the issue doc's fix into this one change.
- [ ] [REVIEW] P2. Honest-coverage atom regrade to per-calculator grain (already operator-decided, implementation
      pending) + league_id namespace reconciliation (check the Track V/H league_id migration todo first — may be the
      same namespace-mismatch problem already partly fixed there) + `fixture_stats` 708-failure root-cause.
- [ ] [CODE] P1. **NEW 2026-07-23 (decision 6) — implement in `compute_coverage_for_bucket()` (deployment-api) ONLY
      AFTER the league_id migration (Track V's prod-apply, still pending) — shipping first produces wrong/unstable
      numbers.** The registry-aware honest-coverage denominator: sports coverage % must reflect "captured / UAC registry
      universe," per the 2026-07-20 operator decision (decision 2 in the ANSWERED section above), not "captured / raw
      manifest." A registry-membership test cannot be correct while 328,999+ manifest rows still carry non-registry-form
      `league_id` strings — that's why the ordering matters, not just a preference.
- [ ] [DIAG] P2. **NEW 2026-07-23 (decision 10) — grep `features-service`/`strategy-service` for any consumer of
      `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` before deciding MDPS's 3 dead derived-odds products' fate;
      operator ruling: wire up for real if something downstream needs them — do NOT retire.** Root cause already
      diagnosed (dead code, never scheduled — the only live sports MDPS Cloud Run job runs `reprocess_sports_odds.py`,
      hardcoded to `odds_horizon_bucket` only); this grep determines the actual wire-up scope.
- [ ] [CODE] P2. **NEW 2026-07-23 (decision 12) — design + build the missing cross-object-CAS safety mechanism** for the
      1,066,231-row manifest purge/reclassify. Root-cause fix shipped, all 4 related operator decisions already ruled —
      the ONLY remaining blocker is that this safety tooling doesn't exist yet (harder than the league_id migration's
      pure scheduling gate — nothing to schedule until this is built). Detail: see the issue doc's own §7 (re-triaged
      2026-07-23).
- [ ] [DESIGN] P2. **NEW 2026-07-23 (decision 13) — implement RAISE-on-all-NaT for `AvailableAtStampingError`
      (operator-ruled), not skip-with-record.** Fail loud at the shard that can't be stamped — catches a CF-8-class
      regression the moment it starts instead of accumulating a silent ~40-50% fill-rate gap for weeks. Wire this into
      the same code path CF-8's fix touches (Track H's CF-8 todo below) so both land together.
- [ ] [CODE] P1. **NEW 2026-07-23 (decision 11) — schedule + run the CF-8 available_at maintenance window.** Fix is
      built + unit-tested, never run in production; CF-8 stays ~40-50% `available_at` fill until it does. Lift operator
      stop `BLK-d9137d48` and clear the still-false backlog parking-gate condition
      (`sports-cf8-maintenance-window-scheduled`) to run it. Detail:
      `sports_cf8_available_at_backfill_regression_     2026_07_13.md`.

## Track V — COVERAGE: backfill to honest-100% · P1 (operator-gated where noted)

- [ ] [DATA] P1. Round-derivation residual: run the retargeted backfill for the reachable in-window pairs already scoped
      — respects the answered pre-2019-out-of-scope decision below (§T) and stays within the round-derivation mechanism
      the 2026-07-18 sweep already confirmed terminal (a 3rd label, §W, was cited alongside §T here in the original
      audit with no recovered meaning — dropped rather than carried forward bare, per finding D); the cup-vs-league
      classification is resolved (they are blank-round leagues, fetchable). **Done when**: the backfill's corpus-wide
      census shows 0 remaining blank-round rows in the in-window, registry-member population.
- [x] [OPERATOR] P1. ✅ **§U decision — ANSWERED 2026-07-20** (see "Operator decisions — ANSWERED 2026-07-20" above,
      decision 2): stop capturing non-registry leagues; the 489-pair/10,869-row population is excluded from the
      denominator and is a purge candidate — **but the purge is STILL BLOCKED** on the league_id namespace migration
      (Track V's own note below + the "Newly-actionable todos" section above) — do not confuse "decided" with
      "executed." ~~BLOCKED-OPERATOR-DECISION~~ was stale framing, corrected 2026-07-23.
- [x] [OPERATOR] P2. ✅ **§T decision — ANSWERED 2026-07-20** (decision 3): pre-2019 (2013–2018) is OUT OF SCOPE,
      intentionally excluded, no further api-football spend. ~~BLOCKED-OPERATOR-DECISION~~ was stale framing, corrected
      2026-07-23. Remaining work is documentation-only — see the new [DOC] todo below.
- [ ] [DATA] P0. **NEW 2026-07-23 (decision 14) — execute the pre-floor wipe now.** 83,541 pre-floor
      (2014-01-01..2020-06-05) `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` rows fall before the established 2020-06-06
      sports data floor (`/codex/02-data/sports-2020-06-data-floor.md` — pre-floor odds data is fabrication-by-
      construction and gets wiped; this population is the fixtures-side analog). Root-cause fix already shipped
      (UAC@46d865df per the earlier audit); only the disposition ruling + actual wipe execution remain. Snapshot first
      (GCS soft-delete gives a 7-day recovery window), same procedure as the Track F derived_features purge.
- [ ] [DOC] P3. Document pre-2019 (2013–2018) as an intentional, explained exclusion (§T decision 3, now answered) in
      the audit's gap table so the remaining-blanks arithmetic reads clean.
- [ ] [DATA] P1. Execute the open residual work from archived `sports_p2_history_apifootball_2015_to_present`'s own
      todos + the 94-league enrichment backfill from `sports_canonical_universe_and_apifootball_reference_expansion`
      (**CORRECTED 2026-07-24** — only `sports_p2_history_apifootball_2015_to_present` is archived/superseded into this
      closeout; `sports_canonical_universe_and_apifootball_reference_expansion` is NOT — it is still `status: active`
      with its own ~9-11 open `- [ ]` todos, per
      `/plans/active/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md`. This is still the literal
      engineering work, not a text-merge — see the new tracking todo directly below).
- [ ] [DOC] P2. **NEW 2026-07-24 (reconcile correction)** —
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` is a SATELLITE plan this closeout
      references but does not fold in (unlike the 4 plans archived in Track X below): it carries its own ~9-11 open
      `- [ ]` todos not duplicated here — UAC canonical registry build/refine, define + backfill the curated ~300-league
      reference set, drop the residual out-of-curated rows, eliminate the bare/legacy dual-layout, the retention-floor
      cleanup, the 2 out-of-universe numeric `league=` dirs, and the E8 legacy-delete stub (the 94-league enrichment
      backfill item is already covered by the bullet directly above — do not double-track it). Both docs now cross-link
      via `related:` frontmatter and the satellite doc carries its own banner. **Done when**: an operator either
      formally folds its remaining todos into this closeout (archive it, like the Track X fold-ins) or confirms
      satellite-plan status is the intended long-term shape — this bullet only fixes the tracking/visibility gap, it
      does not decide that.
- [ ] [OPS] P2. Re-roll `build_instrument_catalogue.py --asset-group sports --since 2019-01-01` to pick up the +26,894
      round rows produced by the pre-2019-scope (§T) + registry-membership (§U) decisions and the 2026-07-18
      round-derivation sweep — the catalogue snapshot predates all of them.
- [ ] [CODE] P2. Upgrade the catalogue `player` grain from `entity=injuries` (injured-only) to `entity=fixture_lineups`
      (full roster, now carries 100% player/coach identity).

## Track K — SMOKE + SPEED + right-days · P1

- [x] [CODE] P0. ✅ CONTENT assertion shipped — **features-service@84cb4613 + @0ae9f460**.
      `_verify_sports_feature_content()` asserts `matchday` populated on numbered rounds, `competition_phase` not
      single-valued (§Z), and `round_name` / `coach_id` not 100% null (§V, checked first so it fails on its own).
      **@0ae9f460 also fixed a path bug in my own @84cb4613**: the layout is `day=<D>/league=<N>/feature_group=<G>/` —
      the league segment sits BETWEEN day and feature_group, so the original `day=<D>/feature_group=<G>/` prefix matched
      nothing and the check passed vacuously. Measured against the live bucket.
- [x] [CODE] P1. ✅ `SPORTS_SMOKE_DATES` pinned — **features-service@84cb4613 + @0ae9f460** (busy `2025-12-20` / thin
      `2025-12-24` / known_buggy_odds `2025-12-18` / known_buggy_fixtures `2024-03-09`; league-shard counts measured
      2026-07-19). @0ae9f460 added the enforcement half: for SPORTS, `empty_confirmed` PASSes only on the pinned thin
      date — a busy slate returning empty is now a FAIL.
- [ ] [CODE] P1. Promote the existing golden window (2025-09-01…11-30) to a shared "right days" SSOT module both smoke
      tests and backfill launches import — the "speed / right days" pillar.
- [ ] [CODE] P1. Build a sports pipeline-check for the IS→tick→MDPS→features middle leg with CONTENT assertions, NOT
      just presence (none exists today, unlike cefi/tradfi's `/data-pipeline-check-mtds`/`/data-pipeline-check-mdps`).
      **Done when**: the check fails on a real "right days" busy date (`2025-12-20`) if any leg's output is empty or
      shape-wrong, not just missing.

## Track D — CODEX: doc alignment · P1

- [x] [DOC] P1. ✅ **ACTUALLY FIXED 2026-07-23 (not just re-marked — body rewrites confirmed, not more banners).**
      Original claim ("CORRECTION BANNERS added to all 9 drifted codex docs... full body rewrites are a deliberate
      follow-up") was inaccurate: a 2026-07-23 audit found 3 docs with NO banner at all and 3 more "banner-fixed" docs
      with stale bodies beneath their own banners. All 6 fixed for real this pass, body content verified against the
      current canonical facts (fixtures split, casing revert, the 3-bug venue/instrument_type/chain root cause), not
      just banner text: `sports-adapter-dependency-order.md` (§1/§3/§4.1/§5 rewritten — split entities + T0/T1 gate
      honestly described as non-firing), `sports-scheduling-and-sharding.md` (§9 diagram + schema note rewritten to the
      split layout), `sports-fixtures-lifecycle.md` (available_at table now split by entity),
      `honest-absence-downstream-handling.md` (banner added + `SCHEDULE_DEFINING_DATA_TYPES` verified against live UAC
      source — still `{"FIXTURES"}`, flagged as the forward-looking C1 gap now added above), `sports-batch-live.md`
      (banner added + source table casing/entity fixed), `pipeline-coverage-matrix.md` (confirming banner added +
      league_id/entity annotations). Also picked up the rest of the original Track D scope in the same pass:
      `sports-integration-plan.md` got a SUPERSEDED banner + frontmatter flip, `sports-live-odds-connectivity.md`'s §3
      deleted-scrapers section was rewritten past-tense (14 retired adapters, corrected from the doc's stale "13").
- [ ] [DOC] P2. **Verify `sports-data-source-coverage-matrix.md`'s body isn't stale-under-banner (same failure mode as
      the 6 docs above — a decent 2026-07-19 banner doesn't guarantee the body matches) + fix the 5 broken `related:`
      paths in `sports_master.md`.** Neither was touched by the 2026-07-23 codex pass above. **Done when**: both files'
      bodies match their banners and every `related:` path in `sports_master.md` resolves.

## Track X — CLEANUP + plan reconciliation · P2

- [x] [SCRIPT] P2. ✅ Flipped 10 sports issue docs `open` → `resolved` (PM@b659c768d) — every one re-verified as 0 open
      todos / >0 done / citing a real commit, with `resolved_by` populated from the cited `<repo>@<sha>`. **Zero
      resolved-but-open sports issue docs remain.** (The sweep's "~30" was the estimate; the measured set with genuinely
      zero remaining todos is 10 — the rest still have open items and are correctly left open.) ~~Flip
      `status: resolved` on the ~30 fully-checked-but-open sports issue docs~~ (list in the audit's reconciliation) —
      pure hygiene.
- [x] [PLAN] P1. ✅ **DONE 2026-07-23 — all 4 fold-in plans archived, live content extracted.** ~~Archive the fold-in
      plans... keep the 2 near-done KEEP-ACTIVE plans standalone~~ was this session's original framing; operator
      decision overrode it: archived all 4 (`sports_manifest_canonicalisation_2026_06_01`,
      `sports_pipeline_to_100pct_golden_window_first_2026_06_27`, `sports_odds_exchange_fixed_fork_2026_07_18`,
      `sports_p2_history_apifootball_2015_to_present_2026_06_27`), each now `status: superseded` /
      `superseded_by: sports_consolidated_closeout_2026_07_19.md` with its own banner pointing back here. Live content
      extracted and pulled in: the EXCHANGE_ODDS/FIXED_ODDS 9-step sequence landed in Track C above; the remaining ~20
      extracted items (CF-8/E8 gate, IS L6 index regression, live SPOT VM tracking, the
      `_read_fixtures_entity_with_schedule_fallback` live freeze-contradiction, P2a/P2b/P2c/P2d, etc.) landed in the new
      "Track S2 — FOLD-IN ABSORPTION" section below, organized by source plan for traceability.
- [x] [PLAN] P1. ✅ **DONE 2026-07-23 — all 5 orphan sports plans linked + reconciliation todos filed.**
      (`sports_catalog_league_grain_only_scope_2026_07_08`, `sports_odds_bookmaker_coverage_enumeration_2026_06_20`,
      `sports_odds_feature_naming_canonicalization_2026_07_21`, `sports_p2_features_history_to_ml_ready_2026_06_27`,
      `sports_predictions_live_mode_activation_readiness_2026_07_21`) — each now carries
      `sports_consolidated_     closeout_2026_07_19.md` in its `related:` list + a cross-reference banner. The 5
      reconciliation todos:
  - [ ] [REVIEW] P1. Reconcile `sports_catalog_league_grain_only_scope_2026_07_08.md`'s active fixture-grain work
        against this closeout: (1) it writes reference data under a bare `entity={fixtures,teams,injuries}/` path — a
        second naming collision on the string this closeout declares FROZEN since 2026-05-23; (2) it's independently
        designing a competing manifest-schema extension for per-fixture-grain capture tracking that depends on
        `league_id` resolution, which Track V flags as an unresolved P0 that plan doesn't cite. Do not resolve
        unilaterally in either doc.
  - [ ] [REVIEW] P1. **Fold `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`'s open `LEAGUE_ID_TO_TIER`
        mapping + 28-unmapped-league_ids gap-analysis into this closeout's league_id migration BEFORE either doc's
        league_id items proceed** — reconciles the underlying conflict too: this closeout treats registry form (`EPL`)
        as canonical, that plan labels raw strings (`PREMIER_LEAGUE`/`BUNDESLIGA`/`SERIE_A`/`LA_LIGA`) as canonical, and
        the fold-in is where that gets settled once, not twice.
  - [ ] [DOC] P2. Update the sports issue-doc index above: it still lists
        `sports_odds_feature_naming_four_way_     mismatch_2026_07_21.md` as merely open/P2, but
        `sports_odds_feature_naming_canonicalization_2026_07_21.md` already has a DECIDED (2026-07-23) naming scheme +
        scoped 3-repo migration in flight — a fresh agent shouldn't re-litigate the naming decision or start a duplicate
        migration.
  - [x] [PLAN] P2. ✅ **DONE 2026-07-24 (plan-hygiene line-cap remediation)** — Reconcile
        `sports_p2_features_history_to_ml_ready_2026_06_27.md` against this closeout: its `last_updated` was stale
        against its own Progress Log; it carried an open P0 VERIFY todo re-confirming `FIXTURES_SCHEDULE`/
        `FIXTURES_OUTCOMES` column population post-split — the IDENTICAL migration Track C1/F claims as canonical target
        — and documented live paths still using `data_type=odds_horizon_bucket` (dead cohort) and raw-form
        `league_id=SOCCER_RUSSIA_PREMIER_LEAGUE` (same class as Track V's unresolved P0). Resolution: the VERIFY todo is
        now merged verbatim into Track C above (immediately after C1); the `odds_horizon_bucket` dead-cohort concern was
        already independently tracked (Track V's "Purge the 1,337 dead `odds_horizon_bucket_{15m,1h,4h,1d}` manifest
        rows" todo); the raw-form `league_id` concern is already independently tracked under Track V's
        league_id-namespace migration. Nothing new to action — the source plan is archived at
        `/plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md`.
  - [x] [REVIEW] P0. ✅ **ANSWERED 2026-07-24 — it is NOT durable.** A fresh live read found the bleed's exact
        pre-remediation row set (11,727 rows, same venue/date breakdown) back in the sports index, despite round-2's
        "VERIFY PASSED: 0 remaining" claim — see the reopened
        `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` "RE-TRIAGE ROUND 3" section. This
        is now a hard BLOCKER, not just an unconfirmed pre-req, for
        `sports_predictions_live_mode_activation_readiness_2026_07_21.md`'s go-live todo — do not proceed past it until
        round 4 confirms a fix holds across a real consolidation cycle.
- [x] [DOC] P2. ✅ **FLIPPED 2026-07-23 (adversarial-review finding C — stale checkbox next to its own completion
      evidence).** **NEW 2026-07-23 (decision 9) — formalize `sports_master_closeout_2026_07_21.md`'s entry-point
      relationship.** ✅ **DONE 2026-07-23 (frontmatter only) + 2026-07-24 (in-body prose).** Added a new
      `entry_point_for: [target-plan-slug]` field to `plans/PLAN_FORMAT.md`'s frontmatter schema (distinct from
      `supersedes`/`superseded_by` — signals "these two plans are intentionally co-live," not "safe to archive the
      target"). Applied to `sports_master_closeout_2026_07_21.md`:
      `entry_point_for: [sports_consolidated_closeout_2026_07_19]`, and its summary reworded from "Supersedes..." to "Is
      the entry-point index for...". **Correction 2026-07-24**: the 2026-07-23 pass only touched the frontmatter — the
      SAME file's title, H1 heading, and its `/autonomous` copy-paste prompt still asserted itself as sole "single
      source of truth" and never named this closeout doc (finding P5,
      `issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md`), so the prose-vs-field self-contradiction was only
      half-resolved by the earlier pass, not fully as this line previously claimed. The title/H1/prompt prose (+ a stale
      `/autonomous`-prompt script reference to the confirmed-broken
      `rebuild_sports_manifest.py::_clean_stale_league_entries`) were fixed 2026-07-24.
- [ ] [CLEANUP] P3. Drop the frozen 2018-2020 `markets`/`outcomes`/`settlements`/`arbitrage_opportunity` scaffolding;
      correct `SPORTS_INSTRUMENTS.md` stale "Known gaps" (lineups player-id strip claim is false); add a junk-symbol
      guard for non-ASCII characters in fixture names (the "§D" pointer this line originally cited could not be
      recovered — dropped rather than carried forward bare, per finding D; the action itself is fully stated above).

## Track S2 — FOLD-IN ABSORPTION: live items extracted from the 3 archived plans not covered above (2026-07-23)

Track C above already absorbed `sports_odds_exchange_fixed_fork_2026_07_18`'s full 9-step sequence. The remaining 3
archived fold-in plans' still-live content, organized by source plan for traceability — none of this has been executed,
it is extraction + tracking only:

**From `sports_manifest_canonicalisation_2026_06_01` (archived):**

- [ ] [DATA] P0. **Sports E8 — legacy bucket delete gate still RED, blocked by CF-8 captured-row backfill.** The
      IRREVERSIBLE delete of the legacy `market-data-tick-sports` + `instruments-store-sports` buckets stays BLOCKED —
      `cf_manifest_audit_2026_06_01.py` is RED on both surfaces. Primary live blocker = CF-8 (`available_at`): aggregate
      backfill hit ~85-88% fill but `capture_status='captured'` rows specifically are still only ~40-60% — root cause is
      the manifest consolidator's dedup key includes `service_name`, so a backfill rewrite under one fixed service_name
      can never dedupe-supersede rows written under a different one (code fix shipped
      `market-tick-data-service@af627b5b`, unit-tested only, **not yet run in production** — same CF-8 window as Track
      H's todo above, run together). Do not re-dispatch the audit itself until that window runs — 30+ prior re-audits
      reproduced identical RED with zero new information. Separately, the `L6-legacy-only == 0` gate criterion needs
      redefining — unreachable by design, doesn't exempt the operator-accepted `instrument_count=0` phantom class.
      Detail: `sports_cf8_available_at_backfill_regression_     2026_07_13.md`.
- [ ] [DATA] P0. **Sports IS L6 index regression — fix IN ORDER ONLY: (1) IS base-image rebuild, (2) resume the 4
      schedulers, (3) ONLY AFTER the `af-backfill-20260714-*` VM fleet completes, re-consolidate — (3) before (1)/(2)
      silently reverts the write again.** Fixtures-job direct-write race vs. the manifest consolidator (repos:
      market-tick-data-service, unified-trading-library, instruments-service). The
      `uts-prod-instruments-service-sports-fixtures` Cloud Scheduler job direct-writes the
      `instruments-store-sports-prd` manifest index, racing the ~1-min consolidator cron — regressed the IS L6
      legacy-vs-canonical gate from 28 to 3,316 legacy-only cells by silently dropping 328,292 previously-migrated rows.
      Containment shipped (per-VM-shard mode, `ManifestIndexShrinkRefusedError` guard at
      `unified-trading-library@45a43438`, `InvalidCompletenessFractionError` fix at `instruments-service@a25cf70d`) but
      NOT closed out — the 3 numbered steps above are what remains: (1) an IS base-image digest bump/rebuild carrying
      both fixes; (2) resume the four `uts-prod-sports-fixtures-*-t1-schedule` schedulers, confirm green execution; (3)
      re-run the targeted manifest re-emission + force-consolidate, verify 0 regressed-legacy-only. Detail:
      `sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`.
- [ ] [DATA] P0. **Legacy no-env `instruments-store-sports` bucket decommission — DO NOT EXECUTE, cross-reference
      only.** Ownership moved to `sports_legacy_bucket_cutover_2026_07_16.md` — a destructive, strictly-sequential,
      Terraform-touching cutover explicitly scoped out of autonomous dispatch, mid-execution against live prod state.
      Track/resolve via that plan, not by re-deriving this item independently (risk of a concurrent, conflicting
      mutation against the same live GCS objects / manifest index / Terraform state).
- [ ] [DATA] P2. **Sports IS dedup-cleanup — 88 orphan rows need manual review + a cross-surface bug-class check.**
      During the 2026-07-13 cleanup of 683,592 duplicate rows (mis-keyed `rebuild_sports_manifest_v9.py` E4 apply-pass
      bug, fixed going forward `market-tick-data-service@55f9e961`, historical dupes removed
      `instruments-service@2f56038e`), 88 rows (0.01%) had no canonical twin to dedupe against and were left untouched.
      Two follow-ups never completed: (a) manual review of those 88 rows' disposition; (b) check whether the same
      mis-keyed-duplicate bug class hit the `mdps` surface or any other bucket rebuilt via the same script family.
- [ ] [CODE] P1. **Mis-filed DEFI item, not sports — relocate, do not lose.** "features-service: ban `category=defi` in
      on-disk GCS path reads" (`mtds_canonical_reader.py::_legacy_twin()` L71-72, `eigen_rewards_calculator.py:53-54`)
      was tracked in the now-archived sports plan under a BLOCKED-PREREQUISITES marker. Its real gating plan
      (`defi_manifest_canonicalisation_2026_06_01.md`) was itself folded into
      `data_completion_to_100_all_ag_2026_06_21.md`, which as of last report still shows defi as NOT full C-GREEN.
      **Re-home this to track against that defi plan, not the sports closeout** — flagged here only so it isn't silently
      dropped during archival.

**From `sports_pipeline_to_100pct_golden_window_first_2026_06_27` (archived):**

- [ ] [DATA] P1. **Sports P2a — API-Football fixtures history 2015→present, never started.** 3 sub-items: (a) G1
      non-canonical-league NOISE wipe — purge ~1,437 non-canonical leagues (~106k rows); (b) G2 2015–2017 zero-captured
      diagnosis — subscription-tier limit vs. backfill bug, then fix/backfill; (c) G2 40,041 FIXTURES `attempted_failed`
      re-run for 2018/2021/2023. **Its original dispatch target
      (`sports_p2_history_apifootball_2015_to_present_2026_06_27`) is ALSO archived in this same batch** — this work has
      no surviving plan home other than this closeout.
- [ ] [DATA] P1. **Sports P2b — reference sources + odds history 2015→present, never started.** Extend the
      golden-window-proven honest-coverage recipe (weather, soccerfootball_info, transfermarkt, understat, footystats,
      odds-api) to full 2015→present within each source's own `coverage_start`; season-aware smart-skip only (typed
      `EXPECTED_*` reasons, never blanket re-fetch).
- [ ] [DATA] P2. **Sports P2c — features history backfill to ML-ready, blocked on P2a+P2b, never started.** Extend the
      features-service sports feature matrix from the golden window (2025-09-01..11-30) to 2015→present once P2a/P2b
      land.
- [ ] [REVIEW] P2. **Sports P2d — final e2e gate stamp, deliberately deferred, blocked on P2a/P2b/P2c.** R3-daily/ R4/R5
      sub-items already shipped/verified; R1/R2/R3-history remain BLOCKED pending P2a+P2b+P2c — re-run this gate once
      those land, don't mark it DONE early.
- [ ] [OPERATOR] P2. **Unresolved cefi-before-sports gate TENSION, never ruled** (flagged 2026-07-14, still open).
      `instruments_foundation_completeness_2026_06_24.md` states sports does NOT start its G1→G5 until cefi is DONE, but
      cefi's own G4/G5 were still open when this coordinator's G1 noise-wipe work executed (2026-06-28). Unclear whether
      the 2026-06-27 re-homing was an implicit operator override — get a ruling, don't assume.

**From `sports_p2_history_apifootball_2015_to_present_2026_06_27` (archived):**

- [ ] [INFRA] P0. **2 SPOT VMs RUNNING as of 2026-07-22, months-to-years from their gate — track to completion or
      dead-shard-detect + relaunch.** `af-backfill-20260721-033537` (FIXTURE_EVENTS, ~1y of walk remaining at observed
      pace) and `af-backfill-20260722-033350` (FIXTURE_STATS, ~5y8mo remaining, itself a same-day relaunch of a
      preempted predecessor). Must clear before any full-history AF enrichment gate can be evaluated.
- [ ] [CODE] P0. **Live contradiction with this closeout's FROZEN-legacy-path declaration** —
      `instruments-service@e1524d21` shipped `_read_fixtures_entity_with_schedule_fallback` (wired into
      `_read_fixture_ids_from_gcs`, `_find_stale_fixture_leagues_for_date`, `_build_fixture_league_map_from_gcs`,
      `instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py`), which tries
      `entity=fixtures_schedule/` first and FALLS BACK to the legacy bare `entity=fixtures/` path for pre-migration
      dates. This closeout declares that path frozen since 2026-05-23 — needs an explicit decision: grandfather the
      fallback for genuinely pre-migration dates, or remove/redirect it at the source.
- [ ] [VERIFY] P0. **FINAL full-history zero-missing (R1/R2/R3) — BLOCKED-PREREQUISITES, bounced 6× as of last check.**
      Gate: 0 `expected_unattempted_pending_fetch`, 0 blank-reason, 0 un-evidenced `attempted_failed` for every (source,
      data_type) within coverage windows, plus features ML-ready. Do NOT fetch the `api_football × ODDS eu=89,073` slice
      if it resurfaces — impossible-not-fetchable denominator pollution pending a purge/retype pass, not real work.
- [ ] [DATA] P1. **LINEUPS/PLAYER_STATS need a new 2026-05-10→present catch-up window launched.** Prior fleet completed
      cleanly but only to a fixed end date, not "to present" (~73+ days uncovered as of last check); blocked until the
      P0 FIXTURE_EVENTS/FIXTURE_STATS VMs above clear the api_football singleton launcher lock.
- [ ] [DATA] P1. **INJURIES (2021-01-01→present) and STANDINGS (2018-01-01→present) full-history windows never
      launched** — blocked by the same api_football singleton launcher lock; launch once it clears.
- [ ] [DATA] P2. **Features recompute for enriched dates, not yet run** — after full-history AF enrichment lands, re-run
      sports features with force/no-skip for the enriched dates (`derived_features` + `fixture_features` only;
      `odds_features` unaffected).
- [ ] [VERIFY] P2. **ML-readiness re-verify, not yet run** — transitively gated behind the features recompute above.
- [ ] [DATA] P2. **TEAMS full-history backfill gated on an external dedup-key fix** —
      `sports_data_sources_canonical_completion_2026_07_13.md`'s consolidator NULL/empty-string dedup-key fix must land
      first; TEAMS stays out of the enrichment fleet's scope until then.
- [ ] [INFRA] P2. **Open question: does the aggregate manifest gate ever see a legacy-CAS (non-per-VM-shard) write?** A
      one-off closer script closed 5,288 cells via legacy CAS write, verified correct at the cell level 3×
      independently, but the shard-fallback aggregate gate never reflected it even after a full consolidator-cadence
      window — possible the consolidator's shard-only rebuild path structurally never folds in prior CAS writes. Needs
      someone to read `unified_trading_library.manifest_consolidator`'s merge-source code to confirm, then either force
      reconciliation or fix the gate tooling. Also ~205-227 genuine gap cells from that closer's dry-run still need a
      normal targeted re-fetch.
- [ ] [INFRA] P2. **`exit_code_fleet_monitor` CLEAN-misclassification risk is fleet-wide, not just this plan's VMs.** A
      no-exit-code + captured-climbed VM always resolves to silent CLEAN regardless of whether a SPOT preemption marker
      was actually written (confirmed root cause of a ~22h undetected-dead-shard incident on this plan's own VMs).
      Filed: `exit_code_fleet_monitor_clean_misclassifies_premature_kill_2026_07_21.md` — implicates
      `deployment-service/exit_code_fleet_monitor.py` beyond this one fleet.
- [ ] [DATA] P3. **Season-cache-0-fixtures gap investigation narrowed but not closed** — a full-season cache fetch can
      return zero fixtures on a date the manifest claims one exists; scope may be larger than the 394-cell count
      currently reported and/or double-counting the same league across numeric/canonical `league_id` representations at
      the entity-split boundary. Filed:
      `api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency_2026_07_19.md`.
- [ ] [DATA] P3. **Bogus api_football ODDS rows still need a purge/retype pass.** Root cause fixed (restored
      `("sports","ODDS")` to `SOURCE_PRIORITY`, `unified-api-contracts@57bcc7c5`), stopping new bad rows, but
      already-written rows (94-league cross-product, `source=api_football` on data api_football never actually serves)
      are deliberately deferred until the in-flight P0 index repair (Track C) settles. Filed:
      `sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md` §B.

---

## Contradiction resolution (sports, 2026-07-19)

From a dedicated contradiction sweep (56 issue docs + 11 plans + 9 codex docs + the epic, all read directly, plus 6
GCS/parquet measurements). Matches the `defi_consolidated_closeout` "Contradiction resolution" pattern. **Two of these
are self-contradictions in THIS closeout / the audit — both now fixed** (marked ✅).

### DOC-vs-DOC

1. **112,277 `attempted_failed` triplet — ALREADY root-caused, and TIME-CRITICAL.** Audit §2.5 / Track O called it
   "root-cause needed"; `sports_trades_venue_fetch_failed_2026_07_15` already traced it (v9-rebuild `attempted_at`
   clobber, fix @6fad6565) with a ~2026-07-20 retention cliff. → escalated as the Track O P0 OPERATOR item above.
2. **Staleness budget — same defect as sweep §J, conflicting fix values.** Both target
   `AG_STALENESS_BUDGET_SEC["sports"]` in `_staleness_budget.py`. §J proposed 180–240s (merge-duration); the issue doc
   proposed 1800s (observed ~11-min blob-age swing). The read gate checks blob AGE → §J's value would still false-trip.
   **RESOLUTION**: merge into one fix; size off the observed refresh interval (≥1800s) or re-measure current cadence.
   (HONEST-COVERAGE track.)
3. **`sports-adapter-dependency-order.md` §5 "gate is the one correct DependencyError" ↔
   `sports_t0_t1_dependency_gate_never_wired`**: grep-verified every T1 caller omits `date=`, so the gate never fires
   (confirmed: understat has captured rows 2014-2017 where api-football has zero fixtures — impossible if the gate
   fired). Codex is stale. (ENTITY-SPLIT/CODEX.)
4. **`sports_dependency_check_manifest_vs_gcs_path` measures 11-25 min cost of the same function #3 shows is
   unreachable.** Either the cost was measured via a synthetic `date=`-passing path or the optimization solves a
   non-materializing cost. NOT resolved — reconcile the 5 named call sites against the 11 enumerated in the gate doc.
   (ENTITY-SPLIT.)

### DOC-vs-REALITY (settled by direct measurement)

5. **Manifest atom is literally `"FIXTURES"`** — measured: 333,594 rows, max `written_at` 2026-07-19T10:11:33Z (today),
   ZERO `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES`. Confirms Track C1 objectively. (CANON C1.)
6. ✅ **SELF-CONTRADICTION in the audit (FIXED)**: §2.1 said `entity=fixtures` FROZEN, §2.6 said "still active today".
   Measured: every file incl. today's `day=` partition has `Creation Time 2026-05-23T20:35:42Z` — FROZEN. §2.6 conflated
   pre-fetched future-dated file _presence_ with active writing. Audit §2.6 reworded to "stale, not actively written".
7. ~~**`sports-data-types-catalog.md` still documents lower-case sports data_types** — contradicts K0-(b). Exact quote
   captured. (CODEX.)~~ **INVERTED BY THIS SESSION'S 2026-07-23 RECONCILIATION**: that doc's lower-case content is now
   the CORRECT, settled answer — K0-(b)'s UPPER decision is what's superseded (see Canonical target section above). This
   item is retained struck-through so the history of "which one contradicted which" stays legible.
8. ✅ **SELF-CONTRADICTION in THIS closeout (FIXED)**: K2's "~20,339 rows, one bucket" excluded `trades` = 1,806,553
   rows (91.5%, lower-case) that K1 commits to fixing at the writer. K2 scope corrected above to name the ~1.8M `trades`
   decision explicitly.

### STALE-SUPERSEDED

9. `sports_fixture_round_not_captured_competition_phase_unknown_2026_07_17` headline "3.2%" superseded by measured 70.6%
   (§R-FIXED); status still open. Residual NOT captured elsewhere: audit the sibling `status_long` "Unknown" default
   (same bug class). (COVERAGE/CLEANUP.)
10. Two FOLD plans still list `sports_reference_v2/` as "migrate-worthy" — it's confirmed dead (frozen 2026-04-20). Add
    a retraction note at fold-in. (STORE.)
11. Codex `sports-scheduling-and-sharding.md` §9/§12, `sports-live-odds-connectivity.md` §3 (13 deleted scrapers),
    `sports-integration-plan.md` (mislabeled current) — all confirmed drifted with specifics. (CODEX.)

### NOT-duplicates (explicit, to prevent a future false-merge)

12. Sweep **§B2** (615-min TIER1 dead-zone → EMPTY output) vs `sports_odds_stale_fixture_reinjection` (frozen board
    re-bucketed → OVER-population; Russia-PL zombie class still open, partial fix MDPS@3bf56ff). Different mechanisms,
    same module. Do NOT merge. (ODDS-LEAK — add the reinjection item.)

### Aggregation-completeness gaps — open work NOT in the tracks above (now folded in)

- **A [largest] — the elo/travel/read_historical_fixtures gap-fill campaign is entirely absent from both docs** (grep-0
  for `elo`/`travel`/`read_historical_fixtures`/"521 date"). 4 issue docs, all shipped-in-body but `status: open`:
  `sports_elo_calculator_tz_naive_season_boundary_silent_skip` (@04274b6a),
  `sports_travel_calculator_home_venue_coords_never_resolved` (@6efefde2,@9923b0d8),
  `sports_travel_calculator_tz_aware_kickoff_crash` (@d878f11a,@81036512),
  `sports_read_historical_fixtures_series_ambiguous` (@538c233e,@4be73e2a — a ~521-date recompute fleet ran). **Confirm
  this 521-date gap-fill and the §Z re-run are ONE combined recompute, not dropped against each other.** → FEATURES.
- **B** — the ⏰ 112,277 retention cliff (finding #1) → Track O P0 above.
- **C** — `sports_odds_ownership_registry_split_brain`: ✅ **DONE 2026-07-16** (corrected 2026-07-24 — was stale here).
  The DEFERRED PURGE (123,149 bogus `api_football×ODDS` rows, re-measured at execution time vs. the originally-estimated
  127,018) + "did the re-seed stop" verify both completed via `sports_legacy_bucket_cutover_2026_07_16.md` T3.1/T3.2; 0
  rows remain, independently re-verified 2026-07-23/24. → CANON/ODDS-LEAK.
- **D** — `sports_manifest_null_vs_empty_dedup_double_count`: unexplained consolidator incremental-dedup gap + 612,682
  blank-`error_reason` `empty_confirmed` residue. → HONEST-COVERAGE.
- **E** — `sports_index_recency_masked_captured_atoms`: redeploy `expected-universe-v2-sports` Cloud Run image + P3
  cross-AG seeder-over-captured sweep. → HONEST-COVERAGE.
- **F** — `sports_odds_team_name_alias_gap_south_america`: Chile PRIMERA_DIVISION Odds-API aliases missing (57% match).
  → CANON/COVERAGE.
- **G** — `sports_odds_stale_fixture_reinjection` Russia-zombie half (finding #12). → ODDS-LEAK.
- **H** — `status_long` "Unknown" default audit (finding #9). → CLEANUP.
- **I** — `sports_derived_features_per_league_layout_unread_by_ml_loader`: features-bucket path SSOT codex doc +
  `odds_api_team_mapping` coverage. → CODEX/CANON.
- **J** — `sports_dependency_check_manifest_vs_gcs_path`: manifest-slice replacement for `check_api_football_dependency`
  (finding #4). → ENTITY-SPLIT.
- **K** — `sports_reference_function_size_qg_regression`: 3 functions over the QG size ratchet. → CLEANUP.
- **L** — `sports_cf8_available_at_backfill_regression`: RED on both surfaces, parked pending an operator window. →
  operator decisions.
- **M** — `sports_halftime_odds_sfi_vs_inplay`: `_apply_ht_odds_pit_gate` default-cutoff branch is dead code; 12,463 T-0
  rows at `bm<-55` flow ungated. → ODDS-LEAK.
- **N** — `sports_is_manifest_eu_regression_overwrite`: footystats MATCHES (5,641) + PREDICTIONS (44,163) residuals not
  root-caused at the writer. → HONEST-COVERAGE.
- **O** — ~~`sports_legacy_canonical_row_gap` OR-1 Option D (player_stats-only union + fixture_events re-fetch) never
  executed~~ **CORRECTED 2026-07-23 (re-triage)**: OR-1 Option D WAS executed the same day as this audit
  (`sports_legacy_bucket_cutover_2026_07_16.md` T2.4, 388,825 rows / 4,015 cells recovered) — this line was stale from
  authoring, not a real gap; see `issues/sports_legacy_canonical_row_gap_2026_07_16.md`'s RE-TRIAGE section for the
  exact match. The 3 unfiled loose ends (canonical player_stats 2x dup; standings/teams writing 2026 live under
  historical `day=`; 640-row cartesian player_values) were NOT re-verified today — still presumed open. → STORE.

### Duplicate/merge + status-flip recommendations

- Merge `sports_manifest_read_staleness_budget_missing` → sweep §J. Merge `sports_trades_venue_fetch_failed` → the
  112,277 item. Flip `sports_golden_window_attempted_failed_remediation` +
  `sports_is_odds_capture_code_incomplete_reversal` → resolved, pointing at `sports_odds_ownership_registry_split_brain`
  (terminal). **~20+ issue docs are shipped-in-body but still `status: open`** — the Track X status-flip sweep should
  cover the full list, not a sample.

## Cross-AG finding (belongs to a prediction/tick close-out, tracked here for visibility)

- [x] [DIAG] P1. ✅ **STALE CHECKBOX FLIPPED 2026-07-23 (adversarial-review finding C)** — this todo's own document
      already shows it fully resolved further down (root-caused, fixed, and remediated — see the checked item below and
      the "re-triage" section's `mtds@a7ff45f9`/`@299ef540` entries). Original text retained for history: **4,097 live
      `asset_group="prediction"` rows (+2 cefi/defi) physically in the sports bucket manifest** (Kalshi/Polymarket,
      `service=market-tick-data-service`, dates 2026-06-26…07-18). Two write paths ruled out; next:
      `ingest_kalshi_bulk_to_canonical.py`, `rebuild_prediction_manifest.py`, the sentinel fan-out. Cross-repo/SSOT
      class — NOTIFY OPERATOR (done in-session 2026-07-19).

## Operator decisions — ANSWERED 2026-07-20 (no longer blocking)

All four resolved in interactive chat. These are now actionable, not gated:

1. **Cross-AG bleed → ROOT-CAUSE FIRST, THEN PURGE.** Locate the third emitter writing `asset_group=prediction` rows
   into the sports manifest (two paths already ruled out: MTDS Kalshi/Poly write paths resolve
   `instruments-store-prediction` correctly; `websocket_runner.py:77` fails loud). Candidates to check:
   `ingest_kalshi_bulk_to_canonical.py`, `rebuild_prediction_manifest.py`, the `SportsCatalogReader`/`FixtureIdResolver`
   sentinel fan-out. Fix the writer, THEN purge the 4,097 rows — purging while the emitter is live just means they
   return (same ordering as K1-before-K2).
2. **§U registry gap → STOP CAPTURING NON-REGISTRY LEAGUES** (operator chose to narrow capture, NOT to extend the
   registry). Target state is **captured == intended**: the sports capture universe is the UAC registry, full stop.
   Implementation: narrow the capture/enumeration path to the registry universe so no non-registry league is fetched
   again; then decide the disposition of the ALREADY-captured non-registry rows (10,869 blank-round rows across 489
   league-seasons) — they must be excluded from the coverage denominator at minimum, and are purge candidates since they
   are by definition out-of-universe. **Consequence: "sports backfilled 100%" becomes literally true against the
   registry denominator**, because the unreachable rows stop being part of the universe.
3. **§T pre-2019 → OUT OF SCOPE.** The window stays 2019-01-01..present. The 122,864 pre-2019 blank-round rows
   (2013–2018) are **intentionally excluded** — document them as a known, explained exclusion, not a gap. No further
   api-football spend.
4. **K2 casing → MIGRATE ALL ~1.8M `trades` → `TRADES`.** ~~Full canonical consistency; the bucket ends UPPER everywhere
   per K0-(b).~~ **SUPERSEDED 2026-07-23**: K0-(b) itself is now superseded (see Canonical target section above) —
   sports data_type is being reconciled to LOWER-case for ALL types, so K2's UPPER direction is being reverted, not the
   other way around. This decision's scoping-correction half still stands (the "~20,339 rows, one bucket" estimate
   wrongly excluded `trades` = 91.5% of the bucket) — only the casing DIRECTION it targeted is now wrong. This
   supersedes the original "~20,339 rows, one bucket" scoping. **K1 (live writer emits UPPER) must ship BEFORE K2** or
   the migration re-dirties on the next write — this ordering lesson is REUSED, not retracted, for the revert:
   registry+writers before data (see Track C's new revert todo).

### Newly-actionable todos from these decisions

- [x] [DIAG] P1. ✅ **STALE CHECKBOX FLIPPED 2026-07-23 (adversarial-review finding C)** — root-caused, fixed
      (`mtds@5581dcf9`, then the manifest-bucket sibling bug via `mtds@299ef540`), and remediated (`mtds@a7ff45f9`,
      VERIFY PASSED, 0 remaining) — see this doc's own 2026-07-23 re-triage section. This checkbox was never flipped
      despite the resolution being recorded further down in this same document. Original text retained for history:
      Root-cause the cross-AG emitter (decision 1), then purge. **MEASURED 2026-07-20 — it is LIVE and GROWING, and
      larger than the audit said**: 4,097 (audit, 07-19) → **6,597 now**, +2,500 added TODAY alone (07-17: 1,756 ·
      07-19: 2,341 · 07-20: 2,500, newest `written_at` 00:54:58Z). So a DAILY job is still writing. Fingerprint (from a
      direct read of `instruments-store-sports-prd/_index/availability_index.parquet`):
      `service_name=market-tick-data-service`, `pipeline_mode` batch_kalshi (6,562) / batch_polymarket_clob (35),
      `venue` KALSHI/POLYMARKET, `data_type` trades (6,484) + prediction_canonical_question_group (113),
      `capture_status` captured (6,567) / empty_confirmed (30), schema_version 9, DATA dates 2026-07-16..07-19
      (forward/recent, i.e. the LIVE capture path — not a historical migration). Plus 1 cefi + 1 defi row
      (BITGET-FUTURES / UNISWAP_V3-BASE, service=instruments-service). **RULED OUT**: (a)
      `ingest_kalshi_bulk_to_canonical.py` and `canonicalize_prediction_manifest_2026_07_18.py` both resolve
      `market-data-tick-prediction` correctly; (b) `websocket_runner.py:451` resolves `instruments-store-prediction`;
      (c) the current per-VM shards in the sports bucket — they contain only sports + blank-`asset_group` rows, NO
      prediction rows. **FALSE LEAD, discarded (do not re-chase)**: the two live `af-backfill-*` per-VM shards hold
      ~100k rows with EMPTY-STRING `asset_group` — that is BENIGN, the consolidator fills asset_group from bucket
      context on merge (consolidated index has **0** blank-asset_group rows). Blank `venue` is likewise normal (4.3M
      sports reference rows have none). **NEXT**: the emitter writes to the sports instruments-store manifest on a DAILY
      cadence from the live Kalshi/Polymarket capture path, bypassing the per-VM shard route. Find the live prediction
      capture job's ManifestWriter bucket resolution (anything resolving `kind="instruments-store"` with a
      defaulted/sports asset_group while writing prediction rows), fix it, THEN purge (purging first = they return
      tomorrow). **✅ ROOT-CAUSED 2026-07-20 — NOT manifest-only: REAL TRADE PARQUET BYTES are in the wrong bucket.**
      Emitter = Cloud Run Job `mtds_fast_t1_recon_job`
      (`deployment-service/terraform/gcp/audit03_cron_provisioning.tf:69`, daily `30 0 * * *` per
      `t1_batch_scheduler.tf:128-131` — matches the newest write 2026-07-20T00:54:58Z), which runs
      `--asset-group SPORTS PREDICTION` in ONE invocation. Bug:
      `market_tick_data_service/engine/orchestrator/__init__.py:680-682` sets `primary_asset_group = next(...)` =
      **"SPORTS" (first element) for the WHOLE run**; `_manifest_bucket.py:49-52`'s sports carve-out then routes the
      manifest to instruments-store-sports for EVERY venue incl. KALSHI/POLYMARKET. Worse, `venue_fetch.py:506,633-635`
      writes the DATA to that same run-level `state.bucket`, so parquet lands in `market-data-tick-sports-prd-*`. The
      row's `asset_group` COLUMN is stamped correctly by the per-venue `_resolve_asset_group` (`venue_fetch.py:614`) —
      so **bucket resolution is PER-RUN while asset_group resolution is PER-VENUE. That inconsistency is the whole
      bug.** CONFIRMED LIVE: 6,451 KALSHI + 3 POLYMARKET real trade parquet files physically under
      `gs://market-data-tick-sports-prd-.../raw_tick_data/by_date/day=2026-07-16|18|19/.../venue=KALSHI/`. Isolated to
      this job (TRADFI already excluded for the analogous mis-stamp reason; CEFI/DEFI have dedicated jobs). Downstream:
      prediction readers looking only at the prediction bucket are BLIND to this data. **The 1 cefi + 1 defi rows are a
      DIFFERENT cause** (`service_name=instruments-service`) — own look, do not assume shared root cause.
- [ ] [INFRA] P2. **Defense-in-depth (no longer urgent — the code fix removes the need)**: split
      `mtds_fast_t1_recon_job` into two jobs (`--asset-group SPORTS` and `--asset-group PREDICTION` separately),
      mirroring the existing `mtds_cefi_t1_recon_job` isolation. Config-only.
- [x] [CODE] P1. ✅ **FIXED — market-tick-data-service@5581dcf9** (QG green). Resolves data buckets **per-venue** in
      `process_ticks()` (reuse the per-venue `_resolve_asset_group(venue, asset_groups)` at `venue_fetch.py:614`)
      instead of one run-level bucket.
- [x] [DATA] P1. ✅ **CROSS-AG DATA REMEDIATION COMPLETE (2026-07-20)** — executed in the safe order, every step
      verified, nothing orphaned: (a) **Snapshotted both manifests** first →
      `_index/backups/pre_crossag_remediation_20260720T103143Z.parquet` in BOTH `instruments-store-sports-prd` and
      `market-data-tick-pred-prd`. (b) **Relocated 6,454 objects** (6,451 KALSHI + 3 POLYMARKET, days 2026-07-16/18/19)
      sports→prediction tick bucket via UTL `gcs_copy_object` (server-side): **6,454/6,454 crc32c-VERIFIED, 0 missing, 0
      mismatch, 0 fail**. (c) **Upgraded the PREDICTION manifest**: wrote per-VM shard
      `_index/per_vm/crossag_relocation_20260720.parquet` with **6,560 genuinely-new rows** (37 of the 6,597 already
      existed and were correctly deduped on `date/venue/data_type/instrument_type/instrument_id`) — read-back verified
      (KALSHI 6,526 / POLYMARKET 34). (d) **Purged the sports manifest**: 6,597 `asset_group=prediction` rows removed,
      **0 remaining** (5,377,593 → 5,370,996). The 1 `cefi` + 1 `defi` rows were deliberately LEFT — different root
      cause (`service_name=instruments-service`), purging them blind could mask a separate bug. (e) **Deleted the
      sports-bucket duplicates**: 6,454 removed, **0 skipped**, with a per-file re-verify that the prediction copy
      existed with matching crc32c immediately before each delete. Final sweep: **0 `asset_group=prediction` objects
      remain in the sports tick bucket.** Ordering mattered: prediction manifest rows were written BEFORE deleting the
      sports originals, so the data was never unlisted in either direction.
- [x] [CODE] P1. ✅ **ALREADY SHIPPED (2026-07-13) — no new work needed.** `_is_in_canonical_write_universe`
      (`orchestrator/sports.py`) already gates per-league captured writes to the registry universe and is WIRED at 9+
      live call sites (`sports_reference_core.py:431,507,594`, `footystats.py:203,613,991`, `sports_fixtures.py:431`,
      `understat.py:190,470`). The 2026-07-13 24-league de-registration ruling set "the sports universe is EXACTLY the
      registered-league set" and the catalogue gates on `_sports_league_registered` too. Decision 2's _forward_ half is
      done.
- [ ] [DIAG] **P0 — ⛔ BLOCKS decision 2's purge half. LEAGUE_ID NAMESPACE MISMATCH, measured 2026-07-20.** The
      manifest's `league_id` namespace does NOT match the canonical registry's:

      | manifest `league_id` (raw) | canonical registry key |
                                                                                                                                                                                                                                                                                                                                  | -------------------------- | ---------------------- |
                                                                                                                                                                                                                                                                                                                                  | `PREMIER_LEAGUE`           | `EPL`                  |
                                                                                                                                                                                                                                                                                                                                  | `CHAMPIONSHIP`             | `ENG_CHAMPIONSHIP`     |
                                                                                                                                                                                                                                                                                                                                  | `PRIMERA_DIVISION`         | `LA_LIGA`              |
                                                                                                                                                                                                                                                                                                                                  | `2._BUNDESLIGA`            | `BUNDESLIGA_2`         |
                                                                                                                                                                                                                                                                                                                                  | `FIRST_DIVISION_A`         | (no registry entry)    |

                                                                                                                                                                                                                                                                                                                                  Measured: **328,999 manifest rows carry a `league_id` absent from `LEAGUE_REGISTRY`, and 265,134 of them were
                                                                                                                                                                                                                                                                                                                                  written ON/AFTER the 2026-07-13 gate ruling** (statuses: captured 213,861 / empty_confirmed 50,975 /
                                                                                                                                                                                                                                                                                                                                  attempted_failed 298). Verified there is NO alias — `PREMIER_LEAGUE`/`PRIMERA_DIVISION`/`2._BUNDESLIGA`/
                                                                                                                                                                                                                                                                                                                                  `FIRST_DIVISION_A` appear nowhere in any registry entry's definition (only `CHAMPIONSHIP` partially matches
                                                                                                                                                                                                                                                                                                                                  `ENG_CHAMPIONSHIP`/`SCOTTISH_CHAMPIONSHIP`/`USL_CHAMPIONSHIP` as a substring, which is itself ambiguous).

                                                                                                                                                                                                                                                                                                                                  **⛔ CONSEQUENCE: executing decision 2's "purge the non-registry rows" against the SYMBOLIC `league_id` would
                                                                                                                                                                                                                                                                                                                                  DELETE core trading data — Premier League, La Liga, the Championship.** Those are not out-of-universe leagues;
                                                                                                                                                                                                                                                                                                                                  they are in-universe leagues recorded under a different naming convention. The purge MUST NOT run until the
                                                                                                                                                                                                                                                                                                                                  namespace is reconciled.

                                                                                                                                                                                                                                                                                                                                  NOTE this is a DIFFERENT axis from §U's 489-pair finding, which compared NUMERIC `af_league_id` against the
                                                                                                                                                                                                                                                                                                                                  registry's `api_football_id` set (sound, numeric-vs-numeric). Both are real; do not conflate them. This is the
                                                                                                                                                                                                                                                                                                                                  §C2 "league_id namespace reconciliation" item, now measured and escalated to P0.

- [x] [CODE] P0. ✅ **WRITE PATH CANONICALISED — operator chose canonicalise-at-write (2026-07-20); shipped
      market-tick-data-service@ad4f1872.** `_canonical_league_id()` resolves via the NUMERIC `api_football_id`; all 30
      write-path prediction leagues resolve (0 unresolved), 13 of 30 change value; unresolvable ids fall back to the raw
      name so an unregistered league still captures. The `--leagues` filter now accepts BOTH forms — it previously
      compared the raw value, so every existing launcher invocation would otherwise have silently fetched nothing.
      **Measurement proved the alias-map alternative would have CORRUPTED data**: six raw names are ambiguous
      (`BUNDESLIGA` German+Austrian, `SERIE_A` Italian+Brasileirao, `SERIE_B`, `CHAMPIONSHIP` English+Scottish,
      `PRIMERA_DIVISION` Argentina+Chile, `SUPER_LEAGUE` Greek+Swiss) — a name-keyed map MERGES them. 3 regression
      tests, incl. one asserting the collisions resolve to DISTINCT slugs. Design + history plan:
      `issues/sports_league_id_namespace_migration_2026_07_20.md`.
- [x] [DATA] P0. ✅ **RE-TRIAGE 2026-07-24 (live GCS + manifest verification): this IS the same work as
      `sports_master_closeout_2026_07_21.md`'s executed COPY+SWAP — this item was STALE, describing the pre-migration
      state.** Migrate the 214,842 historical non-canonical manifest rows (75,432 of them ambiguous, resolved via
      per-row `sport_key` classification — see `issues/sports_league_id_namespace_migration_2026_07_20.md` for the full
      design). **Status, independently re-verified this session (not re-derived from the doc's prose alone):** (1) GCS
      COPY relocation EXECUTED — 275,136/275,136 target objects verify=PASS, 54,835,957 rows written (mtds@b2a49317,
      24-VM fleet, 2026-07-21/22); I re-aggregated all 24 raw shard-report JSONs directly from
      `gs://deployment-scripts-central-element-323112/canonical-migration-sports-reloc/reports/` this session and
      independently reproduced the exact same totals (275,136 objects / 54,835,957 rows) — not just trusting the doc's
      claim. (2) The manifest ADD/REMOVE swap for this relocation EXECUTED 2026-07-22 (folded into the combined K1/K2
      casing swap per master_closeout's "fourth/sixth wave" log: ADD 373,296 keys, of which 275,135 were this
      relocation's canonical rows; REMOVE dropped the stale raw-keyed rows; VERIFY PASSED stale_remaining=0). (3) Live
      spot-check this session (`day=2020-06-30/venue=BETVICTOR`): canonical
      `league_id=EPL/instrument_type=ODDS/     data_type=TRADES/ticks.parquet` exists; the OLD raw-keyed
      `league_id=PREMIER_LEAGUE/` GCS prefix is STILL PRESENT for the same cell — confirms COPY+SWAP is done, the
      GCS-object DELETE genuinely has not run. **Only the human-gated delete of the old raw-keyed GCS objects remains**
      — already tracked in `sports_master_closeout_2026_07_21.md`'s own P0 "RUN THE MANIFEST-SWAP TOOL FOR REAL, then
      DELETE" todo (its 5-part-proof checklist), gated on confirming the K1 live-writer casing fix (shipped same
      session) has actually stopped new non-canonical writes before the delete candidate set stops growing. This
      closeout doc does not need its own duplicate delete todo — point here, don't re-track. Detail:
      `issues/sports_league_id_namespace_migration_2026_07_20.md`.
- [ ] [CODE] P1. **LIVE BUG — canonicalise the bookmaker-league coverage registry.** Measured 2026-07-20: the sports v2
      sentinel calls `is_bookmaker_league_covered(bm, _canon_lid)` with a CANONICAL id (`sentinels.py:319`) but
      `BOOKMAKER_LEAGUE_COVERAGE` (`unified-api-contracts/.../sports_bookmaker_league_coverage.py`) is keyed on RAW
      names — independently confirmed `is_bookmaker_league_covered("BETFAIR_EX_EU","EPL")==False` vs
      `…,"PREMIER_LEAGUE")==True`. So every not-yet-captured (bookmaker, canonical-league, fixture) shard is mis-stamped
      `EXPECTED_BOOKMAKER_NO_LEAGUE_COVERAGE` instead of surfacing as a real gap — a standing coverage false-negative
      TODAY, independent of the relocation. Fix: regenerate the registry JSON from `ODDS_API_DISPLAY_TO_CANONICAL` (or
      re-run `refresh_sports_bookmaker_league_coverage_2026_06_21.py` after the manifest is canonical).
- [x] [CODE] P1. ✅ instruments-service per-fixture path — **SHIPPED instruments-service@815ad06c.**
      `sports_reference_fixtures.py` always took the `fx.league.league_id` branch, making the numeric-id `elif` dead
      code (`CanonicalLeague` always carries `league_id`, so the first branch always won). Precedence inverted to
      resolve by numeric `api_football_id` first, falling back to the raw value only for an unregistered league (honest
      absence, not a vanished map entry). 2 regression tests pin the precedence. Earlier blocked by another worker's
      divergent defi WIP in the clone (AUTOSTASH_POP_CONFLICT); verified green on the clean origin base via a sibling
      worktree (160 tests incl. the previously-foreign golden/dedup failures now fixed upstream), then shipped once the
      clone reconciled — foreign WIP never touched. Companion to the write-path fix mtds@ad4f1872.
- [ ] [DATA] P2. Dispose of the genuinely-out-of-universe rows (decision 2): exclude from the denominator; purge only
      once confirmed. **UNBLOCKED 2026-07-24** — the historical migration above has its manifest-side COPY+SWAP executed
      and verified (stale_remaining=0), so the manifest's `league_id` values for Premier League / La Liga / the
      Championship are now canonical and a registry-membership test correctly classifies them as in-registry; the purge
      is no longer at risk of deleting core trading data on that account. Snapshot before any delete regardless.
- [ ] [DOC] P3. Document pre-2019 (2013–2018) as an intentional, explained exclusion (decision 3) in the audit's gap
      table so the remaining-blanks arithmetic reads clean.
- [x] [DATA] P1. ~~K2 scope is now ALL lower-case rows incl. ~1.8M `trades` (decision 4) — gated on K1 shipping first.~~
      **SUPERSEDED 2026-07-23**: K1/K2 shipped the OPPOSITE direction (migrated `trades` UP to `TRADES`, not "all
      lower-case"). This session's casing reconciliation now supersedes decision 4 itself — see the Canonical target
      section's data_type entry above: the target is all-lower including `trades`, and K1/K2's uppercase migration is
      being reverted, not extended. This todo's original wording is now moot.

<!-- REMOVED 2026-07-23 (reconciliation pass): the "## Operator decisions needed (blocking)" section that lived here
     listed §U and §T as still-blocking, but the "Operator decisions — ANSWERED 2026-07-20" section above already
     resolved both, and Track O's P0 retention-cliff item is separately marked done — this was a stale leftover
     carried unedited from the parent audit doc through three later revision passes. Deleted per operator decision;
     current genuinely-open operator items are tracked in the "Operator decisions needed (blocking) — 2026-07-23"
     section further down, right after the 2026-07-23 root-cause sweep. -->

## Codex SSOTs (read before touching a track)

`/codex/02-data/sports-gcs-path-ssot.md`, `…/sports-data-types-catalog.md`, `…/sports-data-source-coverage-matrix.md`,
`…/sports-adapter-dependency-order.md`, `…/availability-manifest-and-data-status.md`,
`…/honest-absence-downstream-handling.md`, `…/pipeline-mode-partition.md`,
`/codex/04-architecture/sports-batch-live.md`, `/codex/05-infrastructure/spot-vms-for-backfill.md`,
`/codex/12-agent-workflow/async-wait-and-poll-discipline.md` (rule 1a). Plan↔codex drift is review-blocking.

## Aggregated source docs (referenced, not duplicated — every other active sports + sports-touching plan/issue)

> Completeness check: `grep -l '^asset_group:.*sports' plans/active/*.md plans/active/issues/*.md` (run 2026-07-24),
> cross-referenced against this doc's own `related:` list and `ls plans/active/ | grep -i sports`. **5 fold-in plans are
> intentionally OMITTED** — `sports_manifest_canonicalisation_2026_06_01.md`,
> `sports_p2_history_apifootball_2015_to_present_2026_06_27.md`, `sports_p2_features_history_to_ml_ready_2026_06_27.md`
> (all 3 archived to `plans/archive/2026_07/`), plus `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` and
> `sports_odds_exchange_fixed_fork_2026_07_18.md` (still in `plans/active/` but `status: superseded`) — all 5 carry
> `superseded_by: sports_consolidated_closeout_2026_07_19.md`; their live content is already absorbed into Track C/S2
> above, so re-listing them here would be pure duplication. Only unchecked `- [ ]` top-level todos are counted below;
> `status: resolved` issue docs with residual unchecked boxes are listed as-is (resolved ≠ the file has zero open
> checkboxes — flagged per-doc).

- **Entry-point / progress-log companions**:
  - [`plans/active/sports_master_closeout_2026_07_21.md`](/plans/active/sports_master_closeout_2026_07_21.md) —
    companion entry-point doc, not a subordinate — see its own frontmatter
    `entry_point_for: [sports_consolidated_closeout_2026_07_19]`. Its own open todos (6, not the "96+" figure quoted in
    its body — that figure refers to THIS closeout, not itself):
    - **[DATA] P0.** league_id relocation — run the manifest-swap tool for real, then delete
    - **[DATA] P0.** Clean the already-accumulated cross-AG prediction bleed rows before reconciliation
    - **[DATA] P1.** Prune the twin-delete phantom manifest rows (7,295 lowercase)
    - **[DATA] P2.** Peripheral-bucket vocabulary contamination (`ENGLAND_PREMIER_LEAGUE`/`LA_LIGA_2`/`UNKNOWN`)
    - **[CODE] P2.** Ship the 2 parked, verified-correct changes sitting unshipped in worktrees
    - **[DATA] P3.** File an issue doc for the QG structural finding (2 quality-gates.sh steps)
  - [`plans/active/sports_master_closeout_progress_log_2026_07_24.md`](/plans/active/sports_master_closeout_progress_log_2026_07_24.md)
    — 0 open todos (append-only progress-log companion, record-only).

- **Audit / doc-health reconciliation**:
  - [`plans/active/sports_consolidated_audit_2026_07_19.md`](/plans/active/sports_consolidated_audit_2026_07_19.md) — 0
    open todos (the 6-agent audit that fed this closeout; fully absorbed).
  - [`plans/active/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md`](/plans/active/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md)
    (13 open — doc-corpus self-consistency findings):
    - **[DOC] P0.** `authoritative_for` collision, code-verified (`sports-batch-live.md` in-play claim)
    - **[DOC] P1.** `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` is not a clean auto-archive
    - **[DOC] P1.** `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`'s re-triage undercounts open work
    - **[DOC] P1.** `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` falsely claimed
    - **[DOC] P1.** `sports-gcs-path-ssot.md`'s SPORTS-CANON ALIGNMENT note frames legacy no-env stale
    - **[DOC] P1.** `kelly.md`/`staking-methods.md` (archived pre-v2 strategy docs) missing 2 of 9 sibling refs
    - **[DOC] P1.** `unified-sports-reference-interface.yaml` (archived audit yaml) still says `status: "active"`
    - +6 more P2 (data-status catalog claims, `runtime-deployment-topology.md` USEI self-contradiction,
      `sports-2020-06-data-floor.md`/`sports-data-types-catalog.md` enum-value drift) — see file for the rest.

- **Fixtures / catalogue / reference universe**:
  - [`plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`](/plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md)
    (11 open):
    - **[DATA] P0.** Eliminate the bare/legacy dual-layout
    - **[DATA] P0.** Retention floor = the existing per-source genesis registry, not a blanket 2015 delete
    - **[DATA] P0.** Odds-granularity nice-to-have watch-item
    - **[DATA] P0.** 2 out-of-universe numeric `league=` dirs (`14231`/`315`) — fold into hybrid residual-drop
    - **[DATA] P0.** 94-league enrichment backfill (genuine missing enrichment)
    - **[CODE] P1.** UAC canonical registry build/refine (league/cup canonical + ids + is-cup + country + season)
    - **[DATA] P1.** Define the curated ~300-league reference set
    - **[DATA] P1.** Legacy-delete (E8) — `--drop-stale` is an unimplemented stub
    - **[DATA] P1.** Enrichment backfill 2015→present for the 94 leagues
    - +2 more P2 (curated-universe backfill, drop residual out-of-curated rows) — see file for the rest.
  - [`plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md`](/plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md)
    (4 open):
    - **[DATA] P2.** Design the manifest schema for fixture-grain (operator-confirmed 2026-07-14)
    - **[DATA] P2.** Write the fixture-grain catalog build implementation
    - **[DATA] P3.** Extend the catalog build to fixture-grain
    - **[REVIEW] P3.** Post-decision codex alignment check if the manifest/catalog grain changes
  - [`plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md`](/plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md)
    (3 open):
    - **[BACKEND] P2.** Switch `deployment-api/services/fixtures_browser.py` to the single catalogue
    - **[DATA] P2.** Freshness caveat — catalogue regenerated by rollup job (decide before/with P10-B)
    - **[UI] P3.** `FixturesBrowser.tsx` window note + span-cap warning update (once P10-B backend lands)
  - [`plans/active/data_completion_sports_2026_07_24.md`](/plans/active/data_completion_sports_2026_07_24.md) (4 open):
    - **[SCRIPT] P1.** Run the ramp-to-429 calibration probe on an ephemeral VM (operator-gated)
    - **[DATA] P1.** Post-backfill relabel (after the 6 running backfill VMs finish)
    - **[SCRIPT] P2.** Relaunch features-sfi-progressive (code fix shipped, SPORTS re-run pending)
    - **[DATA] P2.** Enrichment completed clean at ~30-34% honest, ~70k unattempted/entity = API-Football daily-cap

- **Odds / feature-naming / coverage**:
  - [`plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`](/plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md)
    — 0 open todos.
  - [`plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md`](/plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md)
    (8 open):
    - **[DATA] P1.** New compute (not a rename) — per-bookmaker raw decimal-odds retention
    - **[DATA] P1.** Update UAC `OddsFeaturesMixin`/`SportsFeatureVector` fields to the chosen names
    - **[DATA] P2.** Migrate `odds_columns.py`'s `ODDS_COLUMNS` + odds-features
    - **[BACKEND] P2.** Close the silent-agnostic gap in `SportsFeatureLoaderMixin`
    - **[BACKEND] P2.** Migrate `SportsValueBettingEngine` + `SportsArbDutchingEngine`
    - **[BACKEND] P2.** Migrate the legacy `sports_feature_subscriber.py`
    - **[REVIEW] P3.** FSS-output ↔ ml-service-input ↔ strategy-service-input parity test (after todos 2-6)
    - **[REVIEW] P3.** Cross-reference against the "wire sports end-to-end" plan
  - [`plans/active/issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md`](/plans/active/issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md)
    (2 open):
    - **[DOCS] P3.** Codex: state odds=MTDS-domain (footystats exception in IS is PREDICTIONS, not ODDS)
    - **[VERIFY] P2.** Reconcile the post-07-13 rebuild delta (`PLAYER_VALUES` −10,934, `ODDS` −3,180 cells)
  - [`plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`](/plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md)
    (3 open):
    - **[CODE] P1.** Stop stale/zombie ticks at bucket assignment (fix locus: MDPS, not MTDS raw ingestion)
    - **[DATA] P2.** MTDS: sweep for the extent of the contamination
    - **[DATA] P3.** Re-run `verify_ml_readiness.py` after the P1/P2 fix
  - [`plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`](/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md)
    — `status: resolved` but 5 residual unchecked todos:
    - **[CODE] P1.** `_apply_ht_odds_pit_gate`'s default-cutoff branch unreachable in production
    - **[DATA] P1.** The blank-`fixture_id` raw generation is still being written — fix upstream writer
    - **[DATA] P1.** Re-calibrate `verify_ml_readiness.py`'s 95% non-NULL threshold against the honest matrix
    - **[DATA] P1.** Reconcile the market-data-sports manifest for the 2,436 deleted T-0 shards
    - **[ML] P2.** Retrain the CLV models after the ODDS_FEATURES recompute
  - [`plans/active/sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md`](/plans/active/sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md)
    (2 open, both P0):
    - **[DATA] P0.** T2.9 — MDT `(sports, odds, trades)` schema contract drifted from reality (BIG FINDING)
    - **[DATA] P0.** T2.10 — 47,253 phantom `api_football × trades` `captured` rows in the MDT canonical index
  - [`plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`](/plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md)
    — 0 open todos.
  - [`plans/active/issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md`](/plans/active/issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md)
    — 0 open todos.
  - [`plans/active/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`](/plans/active/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md)
    — 0 open todos.

- **Live-mode / execution / arb readiness**:
  - [`plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md`](/plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md)
    (6 open, all P3):
    - **[OPERATOR] P3.** Decide whether to pursue a live sports-odds ingestion path at all
    - **[INFRA] P3.** Once P3-1 is a yes: scope the MTDS live-odds connector
    - **[INFRA] P3.** Once the MTDS connector lands: build `launch-mtds-live-sports.sh`
    - **[DATA] P3.** Build the FSS live handler for the sports feature family (currently batch-only)
    - **[REVIEW] P3.** Run a sports archetype through the CLI-primary promote workflow
    - **[OPERATOR] P3.** Final explicit go-ahead to flip sports (and prediction) live
  - [`plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`](/plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md)
    — `status: resolved`, 0 open todos.
  - [`plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`](/plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md)
    (8 open, all P3 — design-spec questions, not yet implementable):
    - **[DESIGN] P3.** Define the decay-window STATISTIC precisely
    - **[DESIGN] P3.** Define the WINDOW boundaries (signal-time to first-leg/last-leg fill)
    - **[DESIGN] P3.** Define the DATA SOURCE (signal-time odds snapshot)
    - **[DESIGN] P3.** Define the OUTPUT shape (decay curve, edge_bps_remaining vs elapsed_ms)
    - **[DESIGN] P3.** Define the GATE STATISTIC
    - **[DESIGN] P3.** Define the MINIMUM SAMPLE SIZE + soak duration
    - **[DESIGN] P3.** Define the PASS/FAIL threshold VALUE and where it lives
    - **[DESIGN] P3.** Define the ACCEPTANCE TEST for this design
  - [`plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md`](/plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md)
    (5 open, all P3):
    - **[BACKEND] P3.** Add `run_sports_backtest(args, config, config_path) -> int`
    - **[BACKEND] P3.** Wire a data source (reuse the Group-B fixture dataset)
    - **[DESIGN] P3.** Resolve `SportsMatchingEngine` vs `L0Matcher` duplication
    - **[SCRIPT] P3.** Add a hermetic test asserting a non-trivial `execution_alpha_bps`
    - **[DESIGN] P3.** Once the harness runs, decide its place in routine backtest-groups verification

- **Legacy cutover / manifest / league_id / data correctness**:
  - [`plans/active/sports_legacy_bucket_cutover_2026_07_16.md`](/plans/active/sports_legacy_bucket_cutover_2026_07_16.md)
    — 0 open todos.
  - [`plans/active/sports_legacy_cutover_closeout_tasks_2026_07_24.md`](/plans/active/sports_legacy_cutover_closeout_tasks_2026_07_24.md)
    (2 open):
    - **[REVIEW] P1.** T6.7 — post-phase codex audit (HARD RULE)
    - **[INFRA] P2.** T6.8 — retire the one-offs + the dead knob + the false-progress tick
  - [`plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md`](/plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md)
    — 0 open todos.
  - [`plans/active/issues/sports_legacy_canonical_row_gap_2026_07_16.md`](/plans/active/issues/sports_legacy_canonical_row_gap_2026_07_16.md)
    — `status: resolved`, 0 open todos.
  - [`plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md`](/plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md)
    — 0 open todos. ⚠️ near-duplicate name of `sports_legacy_canonical_row_gap_2026_07_16.md` above — not verified
    whether these are the same finding filed twice or genuinely distinct; flagging, not resolving.
  - [`plans/active/issues/mdt_t2_6_league_case_duplicate_population_2026_07_16.md`](/plans/active/issues/mdt_t2_6_league_case_duplicate_population_2026_07_16.md)
    — 0 open todos.
  - [`plans/active/issues/sports_legacy_duplicate_triage_2026_07_22.md`](/plans/active/issues/sports_legacy_duplicate_triage_2026_07_22.md)
    (5 open):
    - **1. [OPERATOR] P1.** Rule on the 1,492 v2 pre-floor rows
    - **2. [DATA] P2.** Migrate-forward the 58 v2 post-floor rows (16 days) into canonical `entity=fixtures`
    - **3. [CODE] P2.** Repoint or retire the two flat-legacy readers
    - **4. [REVIEW] P3.** Rescan `migration_orphan_sweep_sports.py --bucket reference`
    - **5. [REVIEW] P3.** Cross-file the pending "MANIFEST prune" deferred task against `sports_master_closeout`
  - [`plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md`](/plans/active/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md)
    — `status: resolved`, 1 residual:
    - **[VERIFY] P2.** BLOCKED-PREREQUISITES (2026-07-06, slot-6 planning) — re-run task 007
  - [`plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md`](/plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md)
    (3 open):
    - **[DATA] P1.** Add `"sports": 1800` to `AG_STALENESS_BUDGET_SEC`
    - **[DATA] P1.** Mirror the same into `_AG_STALENESS_BUDGET_SEC`
    - **[DATA] P2.** Grep the fleet for scripts hardcoding `MANIFEST_CONSOLIDATED_STALENESS_SEC` for sports
  - [`plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`](/plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md)
    (6 open):
    - **[DATA] P2.** Design a manifest-slice-based replacement for `check_api_football_dependency()`
    - **[DATA] P2.** New follow-up finding — `_build_fixture_league_map_from_gcs` gap (flagged not fixed)
    - **[DATA] P2.** Design a separate cached/batched fix for `sports_fixtures.py:356`
    - **[DATA] P2.** Share path-template constants between the real fixtures writer and this checker
    - **[VERIFY] P2.** Confirm real backfill speedup against a real multi-month/full-year run
    - **[DATA] P2.** (duplicate-worded) manifest-slice-based replacement todo — verify not a literal dupe in-file
  - [`plans/active/issues/sports_t0_t1_dependency_gate_never_wired_2026_07_15.md`](/plans/active/issues/sports_t0_t1_dependency_gate_never_wired_2026_07_15.md)
    (1 open):
    - **[SCRIPT] P2.** Thread `date` through every T1 call site of `create_sports_reference_adapter()`
  - [`plans/active/sports_prelaunch_cf5_verify_residual_2026_07_24.md`](/plans/active/sports_prelaunch_cf5_verify_residual_2026_07_24.md)
    (2 open, both P1):
    - **[DATA] P1.** Sports CF-5 oracle relabel = zero — root-caused + fixed (code), preserved to a wip branch
    - **[DATA] P1.** Sports pre-launch-window corpus decision (C3, 10,345 objects — operator-gated)
  - [`plans/active/issues/sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md`](/plans/active/issues/sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md)
    (3 open):
    - **2. [OPERATOR] P1.** Disposition ruling needed on the 83,541 pre-floor `FIXTURES_SCHEDULE` rows
    - **3. [DATA] P2.** Once ruled, run the delete-safety protocol's 5-part proof + execute the wipe
    - **4. [REVIEW] P2.** Re-run `migration_orphan_sweep_sports.py --bucket reference --dry-run` after the wipe
  - [`plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`](/plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md)
    (4 open):
    - **[INFRA] P1.** Redeploy the `expected-universe-v2-sports` Cloud Run job image
    - **[CODE] P1.** Extend the "never emit empty_confirmed over a captured atom" guard to regular sports instruments
    - **[DATA] P3.** Sweep other asset groups for the same seeder-over-captured pattern
    - **[INFRA] P3.** Downgrade, don't drop, the original "redeploy" todo
  - [`plans/active/issues/sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`](/plans/active/issues/sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md)
    — `status: resolved`, 2 residual:
    - **[DATA] P0.** Re-run the targeted L6 manifest re-emission for the regressed cells
    - **[DATA] P1.** Forensics (open question) — what wrote pre-launch captured rows into the IS canonical
  - [`plans/active/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`](/plans/active/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md)
    (8 open, cross-AG with prediction):
    - **1. [DATA] P1.** Pin the true full count and composition of the bleed
    - **2. [BACKEND] P1.** Locate the writer that puts `asset_group=prediction` rows into the sports index
    - **3. [BACKEND] P1.** Fix the misattribution at the writer
    - **4. [DATA] P2.** Remediate the already-written bleed rows
    - **5. [DATA] P0.** Read the UTL manifest consolidator to confirm the actual mechanism
    - **6. [DATA] P0.** Check whether the round-2 remediation script ran
    - **7. [DATA] P0.** Confirm whether a consolidation cycle has run since the 2026-07-23 remediation
    - **8. [DATA] P0.** Once todos 5-7 pin the mechanism, re-run the remediation

- **Features layer / ML readiness / derived data**:
  - [`plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md`](/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md)
    (73 open — 18 P0 / 40 P1 / 14 P2 / 1 P3, capped hard here given the scale; see file for the full list):
    - **[DIAG] P0.** Verify whether the round writer fix (instruments-service@19ae5890) is even reachable
    - **[OPS] P0.** Let the FIXTURES backfill run to completion (watchdog v4 keyed on `entity=fixtures_schedule`)
    - **[ASK] P0.** Operator decision on K1/K2 normalisation direction — K2 is BLOCKED on this
    - **[DATA] P0.** Rebuild the sports catalogue
    - **[CODE] P0.** Implement derive-then-fetch for round population (score date→round per league/season)
    - **[CODE] P0.** Repoint `SPORTS_FIXTURE_ENTITY` to `fixtures_schedule`
    - **[DATA] P0.** Sports features must be RE-RUN — every pre-cutover row was computed from the stale legacy frame
    - **[DATA] P0.** Corpus-wide `derived_features` re-run required (clean, replaces the stopped fleet)
    - +10 more P0 (staleness audits across ~9 stale-entity consumers, backfill pilot follow-through, full-corpus dry-run
      gating), +40 P1, +14 P2, +1 P3 — see file for the complete 73-item breakdown.
  - [`plans/active/issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md`](/plans/active/issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md)
    — 0 open todos.
  - [`plans/active/issues/sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md`](/plans/active/issues/sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md)
    — `status: resolved`, 2 residual:
    - **[DOC] P3.** Write the features-bucket path SSOT (codex/02-data)
    - **[DATA] P3.** instruments-service: `odds_api_team_mapping` coverage gap (found during the P2 fix)
  - [`plans/active/issues/sports_features_rerun_stopped_writing_2026_07_21.md`](/plans/active/issues/sports_features_rerun_stopped_writing_2026_07_21.md)
    — `status: superseded`, excluded (0 open todos, folded forward into the findings-sweep doc above).
  - [`plans/active/issues/sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md`](/plans/active/issues/sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md)
    — `status: resolved`, 0 open todos.
  - [`plans/active/issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`](/plans/active/issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md)
    (3 open):
    - **1. [DATA] P1.** Confirm the writer's intended WEATHER layout is `PER_DAY_PER_LEAGUE`
    - **2. [CODE] P1.** Align `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` to match
    - **3. [DATA] P1.** After the fix, re-run the sports phantom audit and confirm WEATHER false positives drop
  - [`plans/active/sports_prediction_mvp_writetime_precompute_2026_07_24.md`](/plans/active/sports_prediction_mvp_writetime_precompute_2026_07_24.md)
    (1 open):
    - **[DATA] P2.** Precompute `mvp: bool` for sports/prediction (traced + designed, not yet implemented)
  - [`plans/active/issues/sports_reference_function_size_qg_regression_2026_07_16.md`](/plans/active/issues/sports_reference_function_size_qg_regression_2026_07_16.md)
    — `status: resolved`, 3 residual:
    - **[BACKEND] P3.** Decompose `_AfManifestHooks.emit_empty_gaps_for_entity()` (89L → ≤50L)
    - **[SCRIPT] P3.** Root-cause why the size gate didn't block the introducing commit
    - **[SCRIPT] P3.** Re-run a full (non-sliced) `quality-gates.sh` and confirm phase 5

- **API-Football / source-adapter correctness**:
  - [`plans/active/issues/api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md`](/plans/active/issues/api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md)
    — 0 open todos.
  - [`plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`](/plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md)
    (2 open):
    - **[DATA] P1.** Re-fetch backfill the ~3,116 undocumented api_football `attempted_failed` rows
    - **[DATA] P2.** Remove/relabel 1 defi/UNISWAP_V3-BASE row mis-filed in the sports manifest
  - [`plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md`](/plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md)
    (1 open):
    - **[DATA] P2.** BLOCKED-PREREQUISITES — re-verify + re-dispatch footystats backfill VM
  - [`plans/active/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md`](/plans/active/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md)
    — `status: resolved`, 0 open todos.
  - [`plans/active/issues/sports_trades_attempted_failed_2026_07_23.md`](/plans/active/issues/sports_trades_attempted_failed_2026_07_23.md)
    (2 open):
    - **[DESIGN] P3.** Flag `check_high_attempted_failed` owner (deployment-service) re: same-day manifest
    - **[VERIFY] P3.** Once `sports_master_closeout`'s K1/K2 fully flip + the DELETE lands, re-verify
  - [`plans/active/issues/sports_trades_venue_fetch_failed_2026_07_15.md`](/plans/active/issues/sports_trades_venue_fetch_failed_2026_07_15.md)
    — `status: resolved`, 0 open todos.
  - [`plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md`](/plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md)
    (4 open):
    - **[CODE] P2.** understat per-league 404 scoping — expose which leagues errored
    - **[CODE] P3.** 3-way understat absence split (EXPECTED_NO_PROVIDER_COVERAGE) — BLOCKED on a coverage source
    - **[DATA] P2.** odds-api backfill gaps surfaced by the wipe (3 leagues odds_api doesn't carry)
    - **[CODE] P2.** `candidate_parquet_paths` path-shape gap (forward phantom over-flag)
  - [`plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md`](/plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md)
    (1 open):
    - **[DATA] P1.** Once the TEAMS/STANDINGS deployment question is resolved, proceed with the fix
  - [`plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`](/plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md)
    — 0 open todos.
  - [`plans/active/issues/sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`](/plans/active/issues/sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md)
    — `status: resolved`, 1 residual:
    - **[DOCS] P1.** Correct the cutover runbook's canonical-is-a-superset premise for raw odds on early dates
  - [`plans/active/issues/sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md`](/plans/active/issues/sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md)
    — `status: resolved`, 0 open todos.
  - [`plans/active/issues/sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md`](/plans/active/issues/sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md)
    — `status: resolved`, 4 residual:
    - **1. [SCRIPT] P1.** Grep-then-READ every `"odds"`/`"trades"` lowercase literal in `sentinels.py`
    - **2. [SCRIPT] P1.** Make the 3 confirmed call-site changes (venue_fetch.py x2, manifest_finalize.py x1)
    - **3. [REVIEW] P2.** Once shipped + deployed, re-verify empirically against a live day
    - **4. [DATA] P2.** Only after todos 1-3 land AND verify live: re-scope the gated delete of old non-canonical
  - [`plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`](/plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md)
    — 0 open todos.
  - [`plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md`](/plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md)
    — 0 open todos.
  - [`plans/active/issues/sports_source_mdps_instruments_service_not_leakage_2026_07_16.md`](/plans/active/issues/sports_source_mdps_instruments_service_not_leakage_2026_07_16.md)
    — `status: resolved`, 0 open todos.
  - [`plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md`](/plans/active/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md)
    — 0 open todos.
  - [`plans/active/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`](/plans/active/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md)
    — `status: resolved`, 2 residual (cross-AG with prediction, also referenced in
    `prediction_consolidated_closeout_2026_07_18.md`):
    - **[OPS] P2.** Verify the next scheduled `lifecycle-catalogue-regen-sports` run
    - **[INFRA] P3.** Grant `lifecycle-catalogue-regen@central-element-323112.iam.gserviceaccount.com`

- **Cross-cutting infra (shared across asset groups, sports-tagged too — primary tracking in the owning domain/sibling
  closeout, listed here only for discoverability)**:
  `/plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`,
  `/plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`,
  `/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`,
  `/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`,
  `/plans/active/issues/estate_orphan_assessment_2026_07_21.md`,
  `/plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md`,
  `/plans/active/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`,
  `/plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md`,
  `/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`,
  `/plans/active/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`,
  `/plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`,
  `/plans/active/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`,
  `/plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`,
  `/plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
  `/plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md`,
  `/plans/active/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`,
  `/plans/active/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`,
  `/plans/active/issues/vm_backfill_data_correctness_findings_2026_06_29.md`,
  `/plans/active/candle_canonical_path_migration_execution_2026_07_24.md`,
  `/plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md`,
  `/plans/active/data_pipeline_check_mdps_features_2026_07_20.md`,
  `/plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md`.

- **Sibling closeouts / cross-AG (own primary tracking elsewhere, linked here for awareness only)**:
  `/plans/active/defi_consolidated_closeout_2026_07_18.md` (in this doc's own `related:` — cross-AG link, not sports
  scope), `/plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md` (downstream ML, gated, prediction-primary
  with a sports feeder dependency).

- **Folded-in, excluded from the digest above (all `superseded_by: sports_consolidated_closeout_2026_07_19.md`, live
  content absorbed into Track C/S2 — see the callout at the top of this section for the full list of 5)**.

## Progress Log

- 2026-07-19 — Plan authored from the 6-agent audit. §Z (Track F P0) already FIXED (features-service@c6eb1f38); the
  writing fleet was stopped; corpus re-run pending behind the C1 manifest-atom fix. All other tracks open.
- 2026-07-22/23 — K1 (live writer casing) + K2 (historical casing migration) + the phantom `soccer_*` manifest-row prune
  ALL SHIPPED + VERIFIED complete for their scope (`batch_odds_api`/TRADES axis: 373,297 canonical rows, 0 remaining
  lowercase, 0 remaining phantom rows). Full evidence + SHAs: `plans/active/sports_master_closeout_2026_07_21.md`
  fourth/fifth/sixth-wave Progress Log. Track C's K1/K2 todos above are flipped with evidence.
- **2026-07-23 (interactive reconciliation session) — this closeout had drifted into internal contradiction and lost
  track of 9 sibling plans; both fully reconciled.** A 2-pass multi-agent audit (covering every related plan/issue/
  codex doc, ~85 documents total) plus direct code verification found: a critical unreconciled casing conflict (this doc
  said UPPER, a same-day codex reversal said lower for the odds-family, K1/K2 shipped UPPER anyway ~19h after the
  reversal landed); a stale "Operator decisions needed" section contradicting its own ANSWERED section 150 lines above
  it (same stale pattern ALSO found duplicated inside Track V's §U/§T todos — both fixed); 4 plans this doc claimed to
  "fold in" that were never actually archived and had live contradicting content; 5 more live sports plans with real
  scope overlap this doc never knew existed; a Track D "done" checkbox certifying codex banners that a fresh read showed
  were incomplete (3 docs with no banner, 3 more stale under their own banner); and — via a live Distinct Values read
  from the deployment-ui pasted by the operator mid-session — confirmation that sports' venue/instrument_type/chain
  non-canonical rates (9/17, 16/16, 3/3 respectively) trace to 3 sibling positional-parse bugs in
  `market-data-processing-service` that were only partially root-caused before (instrument_type's mechanism was known;
  chain's was assumed-same-function but is actually a sibling function with a different bug shape; venue's
  parts[0]-misread was undiscovered). The operator was walked through every conflict interactively (16 numbered
  decisions) and ruled on each — see the new "2026-07-23 — full contradiction + confusion-risk reconciliation" section
  further down for the complete decision record, and the Tracks above for the resulting new todos. **Per explicit
  operator instruction, this entire pass is DOCS-AND-PLANS ONLY — no code shipped, no data migrated, no GCS/manifest
  writes executed.** The next session should start from Track C's data_type-revert + 3-bug-fix todos (P0, gates
  everything else) and Track H's odds-pipeline-dormancy investigation (P0, the single highest-priority unknown).
- **2026-07-23 (reconciliation session, completion) — all mechanical reconciliation work landed.** Ran to completion via
  a follow-up multi-agent workflow: (1) all 4 fold-in plans archived (`status: superseded`,
  `superseded_by: sports_consolidated_closeout_2026_07_19.md`, each with its own banner) with live content extracted and
  pulled in — the EXCHANGE_ODDS/FIXED_ODDS 9-step sequence into Track C, the remaining ~20 items into the new "Track S2
  — FOLD-IN ABSORPTION" section; (2) all 5 orphan plans linked (`related:` + banner) with a reconciliation todo each,
  now in Track X; (3) 9 codex docs fixed with real body rewrites (not just banners):
  `sports-adapter-dependency-order.md`, `sports-scheduling-and-sharding.md`, `sports-fixtures-lifecycle.md`,
  `honest-absence-downstream-handling.md` (new finding: `SCHEDULE_DEFINING_DATA_TYPES` is a 9th C1 call site, added
  above), `sports-batch-live.md`, `pipeline-coverage-matrix.md`, `sports-integration-plan.md`,
  `sports-live-odds-connectivity.md`; (4) `sports_master_closeout_2026_07_21.md`'s entry-point self-contradiction
  resolved via a new `entry_point_for:` frontmatter field (added to `plans/PLAN_FORMAT.md`'s schema); (5) the
  odds-feature four-way-naming decision (new deliberate naming, full data+manifest migration) + a generative naming
  scheme recorded in `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s Progress Log. **Still nothing
  executed** — every item above is a documentation/plan edit; no code shipped, no GCS/manifest write, no data moved. A
  fresh session can now execute top-to-bottom without hitting any of the contradictions this pass found.

## 2026-07-23 — root-cause sweep on sports odds honest coverage (session continuation)

Answering an operator Q&A thread on sports MDPS/MTDS honest-coverage tracking surfaced 3 real findings, all investigated
to a root cause (not just symptom-documented) and either fixed or properly scoped:

- [x] [DATA] P0. ✅ **api_football wrong-source manifest rows (1,266,874) — root-caused + fixed + wiped.** Root cause:
      `SOURCE_PRIORITY` had no `("sports","TRADES")` entry, so `derive_pipeline_mode_for_row()` fell through to the
      sports asset-group's `api_football` default, mislabeling every sports TRADES sentinel row. Fixed:
      `unified-api-contracts@44623d25`. Wiped (CAS-safe, manifest-only): `market-tick-data-service@e9d9dec0`
      (1,266,874/1,266,874 removed, VERIFY PASSED). GCS-object deletion for the ~7,251 captured cells remains a
      SEPARATE, operator-gated step (prod-bucket delete = human-only). Full detail:
      `issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md` (resolved). This SAME wipe
      also removed the exact 58,016-row dead-residue population `issues/sports_trades_attempted_failed_2026_07_23.md` (a
      concurrent agent's independent DP_RUN_MOSTLY_EMPTY alert triage) had just diagnosed — that doc's todo #1 (restore
      historical `attempted_at`) is now superseded (rows deleted, not restored).
- [x] [DATA] P2. ✅ **MDPS `odds_movement`/`odds_snapshot`/`arbitrage_opportunity` zero-production-objects —
      root-caused: dead code.** The only live sports MDPS Cloud Run job (`uts-prod-mdps-odds-horizon-bucket`) runs a
      standalone script (`reprocess_sports_odds.py`) hardcoded to `odds_horizon_bucket` only — never touches
      `CandleAdapterRegistry`, the generic path these 3 adapters are registered under. No other job/scheduler/VM reaches
      them. Registered in `SOURCE_PRIORITY`/`DATA_TYPES_BY_ASSET_GROUP` (aspirational), never actually scheduled.
      Operator decision needed: wire them up for real, or retire the registrations. Detail:
      `issues/sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md` (resolved — the "why" is answered; the
      "what to do about it" is an open P2 decision).
- [ ] [DATA] P1. **NEW, bigger finding: sports ODDS_API (TRADES) capture pipeline scheduling status UNKNOWN.** While
      verifying the api_football fix had reached running instances, found ZERO sports manifest writes of any kind for
      ~12h+ at time of check, the historical `oddspapi-w01/w02/w03` Cloud Run jobs last ran 2026-03-29 (~4 months ago),
      and no GCP Cloud Scheduler entry or running VM currently drives sports odds capture. Could NOT check AWS-side
      scheduling (IAM-denied) or persistent-VM-internal crontabs. **Genuinely unknown whether new sports odds data is
      arriving at all right now** — this matters more than the two findings above, since fixing label-correctness of
      data that has stopped arriving is far less valuable than it looks. NOT resolved — needs its own dedicated
      investigation with proper infra access. Detail:
      `issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`.
- [x] [VERIFY] P1. ✅ **Sentinel fan-out for TRADES honest-coverage — verified mechanism exists + looks correct.**
      `sentinels.py::_emit_sports_v2_sentinels` fans out over every (bookmaker × league × fixture) from the
      instruments-service fixture catalog, checks UAC `is_bookmaker_league_covered_exact()`, and resolves EVERY combo to
      `record_failed`/`record_zero_rows`(empty_confirmed)/captured — nothing left silently untracked, by design. Could
      not observe it actually firing in production (ties to the dormant-pipeline finding above) — the current manifest
      shows 373,297/373,297 = 100% `captured`, 0 empty/failed for the `batch_odds_api` scope, which is consistent with
      either genuine completeness or the mechanism simply not having run recently enough to surface any gaps. Re-verify
      once the dormant-pipeline question above is resolved.
- [ ] [OPERATOR] P0. **The separate, irreversible, 5-part-proof-gated DELETE of old non-canonical K1/K2 GCS objects**
      (and now also the ~7,251 `api_football` captured-cell objects) remains human-only per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3#1 — evidence prepared, not executed, not something
      to do autonomously regardless of confidence.

### Sports issue-doc index (swept 2026-07-23 — every `plans/active/issues/sports_*.md` not already linked above)

Not individually triaged/re-verified today (that is its own large effort) — listed here so nothing is orphaned from
discovery. Priorities are each doc's own self-assessed value; treat as a starting point, not a re-confirmed ranking.

## Track Y — PLAN-QUALITY REMEDIATION (2026-07-23, adversarial-review findings A/B/D/E/F/G)

A second independent agent adversarially reviewed this doc's AO-dispatch-readiness (findings lettered A-G; finding C — 2
stale checkboxes — was fixed directly above, in place, with evidence). The remaining findings are real defects in THIS
document, tracked here rather than silently fixed under time pressure so nothing is lost:

- [x] [DOC] P0. ✅ **Finding A — PARTIAL FIX 2026-07-23.** Rewrote all 4 flagged Track F todos (re-run, 2017+2018
      re-run, PURGE, re-verify) + the Track C revert todo (3 layers were buried past line 1) + the F1/F2 parse-bug fix
      todo (the actual fix was buried past a problem-only line 1) so the complete instruction — action, method, and any
      hard constraint like ON-DEMAND vs SPOT — is now on line 1 of each. **Not yet exhaustive**: a background sweep of
      Tracks H/K/D/X/S2 for the same pattern is in progress (dispatched same session) — this checkbox reflects the Track
      F/C fix, not a doc-wide guarantee yet; see the follow-up todo below once that sweep reports.
- [x] [DOC] P0. ✅ **Finding B — FIXED 2026-07-23.** The re-run todo now states its own dependency exactly once ("does
      NOT depend on Track C's C1... gated only on the season_context fix + a fresh tarball") with an explicit "this is
      the ONE place this is stated" guard; the PURGE and re-verify todos now each open with "only after <predecessor> is
      done." **Not machine-enforced** — this plan is `assigned_vm: NA` (not currently AO-dispatched), so
      `sequential: true`/`gate_on_depends` wiring is deliberately deferred until this chain is actually extracted for
      dispatch (consistent with the operator's 2026-07-23 "a guard comment is enough for now" ruling on the broader
      child-plan-split question) — the prose guard is the interim safety net, not a permanent substitute.
- [x] [DOC] P1. ✅ **Finding D — FIXED for every open-todo first-use 2026-07-23.** Resolved each label's real meaning by
      reading `sports_consolidated_audit_2026_07_19.md` directly rather than guessing: §Q/§R/§T/§U/§W = "the round work
      from the 2026-07-18 sweep... confirmed terminal" (round-derivation/catalogue-repoint/backfill, per the audit's own
      headline verdict) — T/U further specialize into the two now-answered operator decisions (pre-2019 scope; registry
      membership); §V = the split-entity read fix; §A2 = `plan_reconciliation_operator_decisions_2026_07_11.md`'s own
      §A2 ruling batch (a different doc, cited correctly now). §C2/C3/C6/§R/§B2 turned out to already state their fact
      adjacent to the label (citation-only, not load-bearing) — left as-is. **§W's meaning could not be recovered**
      anywhere in this doc or the audit — dropped rather than carried forward bare (stated explicitly in place, not
      silently).
- [x] [DOC] P2. ✅ **Finding E — FIXED for both flagged instances 2026-07-23.** Track S's "Absorb
      `sports_canonical_migrated_odds_mistamped_footystats` + `sports_canonical_raw_truncated_rederive_destroys_corpus`"
      reworded to the literal action — and downgraded from HIGH once checked: the rederive-risk doc is
      `status:     resolved` with 1 real open todo (runbook correction) to merge; the footystats doc doesn't exist
      standalone, it's already Track C's venue-cleanup todo. Track V's "Absorb `sports_p2_history_apifootball...`"
      reworded to "execute the open residual work from archived `...`'s own todos."
- [x] [DOC] P2. ✅ **Finding F — FIXED 2026-07-23, with reasoning, not a blind tag.** The PURGE todo is deliberately
      **not** `[OPERATOR]`-tagged (unlike the K1/K2 GCS-delete, which is) — stated explicitly in place: GCS soft-delete
      gives a 7-day recovery window, making this reversible-for-a-week rather than the irreversible class
      `gcs-and-manifest-delete-safety-protocol.md` reserves for human-only sign-off.
- [x] [DOC] P2. ✅ **Finding G — FIXED for both named examples 2026-07-23**, plus 4 more todos gained a done-criterion
      along the way (the casing revert, the F1/F2 fix, the round-derivation residual, the dimension-group purge). T0/T1
      gate: "done when a T0-before-T1 violation actually raises in a test." Tick/MDPS pipeline-check: "done when the
      check fails on a real busy date if any leg's output is empty or shape-wrong." **Not exhaustive** — no full sweep
      of every remaining todo across Tracks H/K/D/X/S2 for a missing done-criterion was performed this pass.
- [ ] [REVIEW] P1. **Follow-up once the Track H/K/D/X/S2 background sweeps (Finding A + Finding C, dispatched
      2026-07-23) report back**: apply their findings the same way as above — fix directly if small and clear, or
      re-open a scoped todo here if not. Do not let the sweep's own output sit unconsumed.
- [ ] [REVIEW] P1. **Full finding-C sweep** — only 2 stale-checkbox instances were found+fixed (the cross-AG emitter
      todo, the 4,097-row finding). A second independent agent found these by spot-check, not an exhaustive pass —
      re-sweep the WHOLE doc for any other todo whose own body (or a later section) already shows it resolved, and flip
      it with evidence, so AO never re-investigates an already-solved problem.

**P0 (open, 6):** `sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`,
`sports_cf8_available_at_backfill_regression_2026_07_13.md`, `sports_features_rerun_stopped_writing_2026_07_21.md`,
`sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`,
`sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`,
`sports_is_manifest_eu_regression_overwrite_2026_06_29.md`,
`sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md`, `sports_legacy_canonical_row_gap_2026_07_16.md`.

**P1 (open, 11):** `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`,
`dp_catalog_not_running_sports_prediction_2026_07_15.md`,
`sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md`,
`sports_index_recency_masked_captured_atoms_2026_07_13.md`, `sports_legacy_duplicate_triage_2026_07_22.md`,
`sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md` (superseded by K1 completion above — worth a
formal status flip, not done here), `sports_manifest_read_staleness_budget_missing_2026_07_15.md`,
`sports_odds_stale_fixture_reinjection_2026_07_14.md`,
`sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md`,
`sports_shard_enumeration_cartesian_blowup_2026_07_20.md`,
`sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`.

**P2 (open, 8):** `sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`,
`sports_golden_window_attempted_failed_remediation_2026_06_24.md`,
`sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`,
`sports_odds_team_name_alias_gap_south_america_2026_07_09.md`,
`sports_phantom_audits_reference_not_marketdata_2026_07_14.md`,
`sports_t0_t1_dependency_gate_never_wired_2026_07_15.md`, `sports_trades_venue_fetch_failed_2026_07_15.md` (see the
2026-07-23 finding above — partially resolved by the api_football wipe), `sports_trades_attempted_failed_2026_07_23.md`
(today's DP_RUN_MOSTLY_EMPTY triage, resolved — metric artifact of the K1/K2 swap, not a regression).

**P3 (open, 3):** `sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`,
`sports_reference_function_size_qg_regression_2026_07_16.md`,
`sports_source_mdps_instruments_service_not_leakage_2026_07_16.md`.
(`features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21.md` resolved + archived 2026-07-24 — see
`/plans/archive/issues/features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21.md`.)

**Recommended next item for a fresh session:** the dormant-pipeline investigation
(`sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`) — it gates whether any of the honest-coverage
work above is measuring a live, growing dataset or a frozen one, and needs infra access this session didn't have (AWS
IAM, persistent-VM inspection).

- [ ] [DOC] P3. **Triaged against `/home/ubuntu/unified-trading-system-repos/sports_plan_changes.md` (2026-07-23) — a
      reference-only "AO-ready instruction-clarity model" rewrite of an earlier version of this closeout, built by a
      different session/agent, `status: draft` + `assigned_vm: NA` (never dispatched, not in `plans/active/`).**
      Verdict: it predates this session's interactive casing-revert ruling — its Track C still frames data_type/
      instrument_type as UPPER (the K1/K2 decision this closeout has since REVERTED to all-lower) — do not adopt that
      framing, this closeout is the more-current, more-canonical side on that specific point. It independently converges
      on nearly the same 6 defect classes Track Y above already fixed (first-line completeness, single-place ordering,
      resolved section-shorthand, literal-verb instructions, consistent delete-tagging, stated done-when) — treat that
      convergence as validation, not a reason to import its content. **One real structural technique worth adopting as
      its own follow-up (not done here, scope is ~150 todos across this whole doc)**: stable per-track todo IDs (`F-3`,
      `C-4`, `N-8`, …) so a `Prerequisite: F-3, F-4` note can name an exact todo instead of prose ("after the
      re-runs...") — this would make Finding B-class ordering issues structurally harder to reintroduce. Lower-value,
      higher-risk, not recommended: regrouping scattered Progress-Log narrative into new named tracks (its Track
      N/R23/T23) — would require moving already-correct, already-cited content with real risk of dropping evidence in
      transit, for a mostly-cosmetic gain.

## 2026-07-23 — re-triage of the full sports issue-doc index (6 parallel agents)

Every doc in the swept index above was individually re-verified against CURRENT code/data state (not just re-read) — 30
docs total, each check backed by a live grep/query/commit citation, not assumption. Result: **13 resolved** (fixes
shipped and verified working), **1 superseded** (a fix landed with the opposite disposition than the doc recommended,
tracked separately), **~15 confirmed still open and accurate**, **1 confirmed still open and getting worse than the last
recorded state**. Full per-doc verdicts are in each file's own `## RE-TRIAGE (2026-07-23)` section. SHAs:
`pm@bd88f337c`, `pm@d510c0938`, `pm@c864972b1`, `pm@1bda5148f`, `pm@2b5a3f623`, `pm@63c765a1c`.

**Two findings from the re-triage needed escalation — both dug into further the same day, one fully resolved, one
corrected to a properly-scoped code fix:**

- [ ] [DATA] P0. **`cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` — REOPENED 2026-07-24,
      round-2's "RESOLVED" claim below does not hold.** Root-caused precisely (round 2): the 07-20 "complete" claim
      fixed the raw-data-bucket bug (`mtds@5581dcf9`) but missed the MANIFEST-bucket's own copy of the same bug
      (`orchestrator/__init__.py::_resolve_manifest_bucket`, resolving once per RUN not per-venue), not fixed until
      `mtds@299ef540` (2026-07-22T02:01:44Z) — during that ~39.5h gap the manifest bug kept writing fresh bleed rows
      even though the raw data was already routing correctly. Confirmed zero bleed rows written after `299ef540` (writer
      bug fixed + holding) before remediating. Executed `market-tick-data-service@a7ff45f9`: CAS-safe ADD 5,056 + REMOVE
      11,727 across both manifests, snapshot-first, **VERIFY PASSED at the time** (0 remaining, 0 still missing).
      **RE-TRIAGE ROUND 3 (2026-07-24)**: a fresh live read of the SAME index found the **exact same 11,727 rows, exact
      same venue/date breakdown**, back in place — round-2's remediation has NOT held. Confirmed metadata-only (no
      physical objects found in the sports bucket) and ruled out the obvious stale-per-VM-shard hypothesis
      (`_index/per_vm/` holds only an unrelated 18KB seed file dated 2026-06-28). Root cause of the REVERSION is
      unconfirmed — working hypothesis is a consolidator rebuild path that re-merges a surface round-2's remediation
      never touched. **Do NOT re-flip this to resolved** — full detail + next-step investigation plan in the issue doc's
      own "RE-TRIAGE ROUND 3 (2026-07-24)" section.
- [x] [DATA] P1. ✅ **`sports_index_recency_masked_captured_atoms_2026_07_13.md` — root cause CORRECTED, redeploy todo
      was targeting the WRONG job.** Traced the actual 04:06:54Z masking write via Cloud Run execution history instead
      of assuming: it's `uts-prod-instruments-service-sports-fixtures` (generic instruments-service batch capture,
      `--operation=instruments --mode=batch`), NOT `expected-universe-v2-sports` (which ran hours earlier, 01:30Z) — a
      completely different code path from where the `ba306543` oscillation guard lives. Redeploying
      `expected-universe-v2-sports` would have fixed nothing. Also checked whether the shipped reader-side tie-break
      neutralizes this — it doesn't, this masking is explicitly cross-dedup-key. Real fix needed: extend the guard to
      the batch-capture emission path (`instruments-service`, new P1 CODE todo in the issue doc) — genuine code work,
      correctly left for a fresh session rather than rushed here.

**Also found**: `sports_consolidated_closeout_2026_07_19.md`'s own item **O** (a stale claim from this doc's own
2026-07-19 authoring) was corrected in place above — OR-1 Option D WAS executed the same day, contrary to what was
recorded. And a near-duplicate doc outside this sweep,
`issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md`, was found resolved by the same commit as
`sports_reference_function_size_qg_regression_2026_07_16.md` but never updated — annotated, not fully flipped (2 of its
3 sub-todos remain genuinely open).

## 2026-07-23 — full contradiction + confusion-risk reconciliation (interactive, 16 operator decisions)

A dedicated multi-pass audit (2 workflow passes across every related plan/issue/codex doc + direct code verification)
found this closeout had drifted into internal self-contradiction and had lost track of several live sibling plans. The
operator was walked through every point of conflict interactively and ruled on each — this section is the consolidated
record. **Per explicit operator instruction: everything below is DECIDED and being written into docs/ plans NOW; none of
the data-moving or code-shipping work has been EXECUTED yet** — that is deliberate, so a fresh agent (or a future
session) picks up a fully reconciled, non-contradictory plan rather than doing archaeology on which of two conflicting
SSOT claims is current.

**Decisions made (ruling → what it changed):**

1. **data_type casing** → ALL-LOWER for every sports data_type, reverting K1/K2's TRADES-to-UPPER migration. See
   Canonical target section + Track C's new revert todo.
2. **Stale "Operator decisions needed (blocking)" header** → deleted (was contradicted by the ANSWERED section 150 lines
   above it).
3. **4 fold-in plans never actually archived** → archive all 4 now, pulling their live content into this closeout first
   (`sports_manifest_canonicalisation_2026_06_01`, `sports_pipeline_to_100pct_golden_window_first_2026_06_27`,
   `sports_odds_exchange_fixed_fork_2026_07_18`, `sports_p2_history_apifootball_2015_to_present_2026_06_27`) — see the
   new todos this pulled in below.
4. **5 orphan plans with real overlap, never linked to this closeout** (corrected 2026-07-24 — was miscounted "6" here,
   already correctly "5" elsewhere in this doc, e.g. line ~606) → link all + file a reconciliation todo each
   (`sports_catalog_league_grain_only_scope_2026_07_08`, `sports_odds_bookmaker_coverage_enumeration_2026_06_20`,
   `sports_odds_feature_naming_canonicalization_2026_07_21`, `sports_p2_features_history_to_ml_ready_2026_06_27`,
   `sports_predictions_live_mode_activation_readiness_2026_07_21`) — see the new todos below.
5. **Track D's "9 docs banner-fixed" claim was inaccurate** → do the full body rewrites now, not more banners (6 docs:
   `sports-adapter-dependency-order.md`, `sports-scheduling-and-sharding.md`, `sports-fixtures-lifecycle.md`,
   `honest-absence-downstream-handling.md`, `sports-batch-live.md`, `pipeline-coverage-matrix.md`), see Track D.
6. **Honest-coverage UI denominator** → implement the registry-aware fix in `compute_coverage_for_bucket()` now (not
   just a doc caveat) — new Track H todo below. Sequenced AFTER the league_id migration (decision 7) since a
   registry-membership test can't be correct until that lands.
7. **League_id historical migration (214,842 rows)** → schedule the monitored prod-apply + human-only delete session now
   — see Track V, still the same P0, now explicitly scheduled rather than indefinitely deferred.
8. **Sports ODDS_API capture pipeline dormancy** → investigate now, get the AWS IAM access this session lacked — new
   Track H todo below, explicitly the single highest-priority NEXT action across this whole closeout.
9. **`sports_master_closeout_2026_07_21.md`'s summary-vs-supersedes self-contradiction** → formalize a real entry-point
   relationship field in the plan frontmatter schema rather than just rewording prose — new Track D/X todo below
   (touches `plans/PLAN_FORMAT.md`, may need a schema discussion, not a same-session mechanical fix).
10. **MDPS's 3 dead derived-odds products** → wire them up for real (not retire) — new Track H todo below, gated on
    confirming downstream demand first (features-service/strategy-service consumer check).
11. **CF-8 available_at fix** → schedule the maintenance window now, lift operator stop `BLK-d9137d48` — Track H.
12. **1,066,231-row manifest purge** → design + build the missing cross-object-CAS safety tooling now — new Track H todo
    below (harder blocker than league_id's pure scheduling gate — nothing to schedule until this exists).
13. **AvailableAtStampingError write-abort contract** → raise on all-NaT (fail loud), not skip-with-record — new Track H
    design todo below, to prevent a future CF-8-class silent regression.
14. **83,541 pre-floor FIXTURES_SCHEDULE/FIXTURES_OUTCOMES rows** → execute the wipe now (consistent with the
    already-established 2020-06-06 sports data floor policy) — new Track V todo below.
15. **MTDS live-odds fixture_id-blank collapse** → investigate + fix now, don't just re-check status — new Track O todo
    below.
16. **OR-1's 2 unfiled loose ends** (standings/teams season-2026 under historical `day=` partitions; unidentified junk
    `player_values` writer) → investigate both now — new Track S todo below.
17. **Sports live-mode prediction trading go/no-go** → GO, gated explicitly on confirming the cross-AG bleed fix
    (`mtds@a7ff45f9`, see the 2026-07-23 re-triage section above) is durable, not just verified-once — new todo on
    `sports_predictions_live_mode_activation_readiness_2026_07_21.md` (linked in decision 4 above).
18. **Odds-feature naming (BLK-a1ce4719's remaining field-name call)** → new deliberate naming, not adopted from any
    single existing convention, full data+manifest migration so every real consumer's need is met. Scheme + gap analysis
    recorded in `sports_odds_feature_naming_canonicalization_2026_07_21.md`'s Progress Log (2026-07-23).

**New evidence folded in during this pass (not from the original audit)**: a live "Distinct Values" read from the
deployment-ui's sports Instruments Service view showed 9/17 non-canonical venues, 16/16 (100%) non-canonical
instrument_types, 3/11 non-canonical data_types, and 3/3 (100%) non-canonical chains. Root-caused to 3 separate
asset_group-blind positional-parse bugs in `market-data-processing-service` (see Canonical target section + Track C's
new todos). **Target, stated explicitly for the first time**: by the end of this closeout, that Distinct Values panel
reads 0 non-canonical across all four axes for sports.

## Operator decisions needed (blocking) — 2026-07-23

Genuinely still-open items needing operator input or a monitored/gated execution window (replaces the deleted stale
section above, which conflated answered and open items):

- **League_id migration prod-apply + delete** (decision 7) — scheduling, not a question, but the actual window needs
  picking.
- **CF-8 maintenance window** (decision 11) — same, scheduling.
- **Sports ODDS_API capture pipeline dormancy investigation** (decision 8) — needs AWS IAM access this session didn't
  have; genuinely the top-priority next action.
- **§O diagnoses before any relabel** (Track O's `[DIAG]` items, lines ~299-302) — root-cause the 112,277
  `attempted_failed` triplet and the 139,620 `empty_confirmed` emitter before relabeling either; these are engineering
  diagnosis work, not a pure operator ask, but flagged here since a premature relabel would be irreversible-adjacent.
- ~~`sports_master_closeout_2026_07_21.md` entry-point relationship field (decision 9)~~ — **stale, this was DONE** (see
  Track X's decision-9 todo above, `[x]` since 2026-07-23) — no operator input was actually needed, the
  `entry_point_for:` field addition was mechanical. Left struck-through rather than deleted so the "this section used to
  list it" fact stays visible (finding C, caught in the same pass as the Track X flip).
