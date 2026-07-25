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
    /plans/archive/2026_07/sports_master_closeout_2026_07_21.md,
    /plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /plans/active/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
    /plans/active/sports_odds_exchange_fixed_fork_2026_07_18.md,
    /plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md,
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    /plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md,
    /plans/active/sports_legacy_fixtures_path_migration_2026_07_24.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
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

> **`sports_master_closeout_2026_07_21.md` ARCHIVED 2026-07-24** (its 6 open todos folded into this doc — see Track C /
> Track S / Track X / the "Operator decisions — ANSWERED" section below). Its full 2020-06 data-floor ruling narrative,
> landmine-contradiction history, and issue-doc catalogue are preserved as historical record at
> `/plans/archive/2026_07/sports_master_closeout_2026_07_21.md`; the codex SSOT for the floor itself is
> `/codex/02-data/sports-2020-06-data-floor.md`.

> **First AO-dispatch batch extracted 2026-07-24 — ✅ ARCHIVED-AND-COMPLETE 2026-07-24**:
> `/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md` (21 todos shipped — 20 hand-picked + todo 1's
> mid-execution split into a CODE + a DATA todo, both mapping to the same Track C1 checkbox below) carried 20 todos
> hand-picked from Tracks F/C/O/H/V/K/D/X below for genuine independence (no unmet prerequisite, no file overlap). All
> 20 corresponding checkboxes below are now flipped `[x]` with independently-verified evidence
> (`sports_closeout_batch1_finalize_2026_07_24.md`). Do not re-extract any of these items into a batch 2 — check the
> archived plan's todo list first if in doubt.

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
    axes.** **Cross-AG note (operator, 2026-07-24)**: this target already implies literal 100% canonical
    `instrument_type` for sports, consistent with the cross-AG standard applied to tradfi/cefi/prediction (see
    `plans/active/issues/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`) — the
    `ODDS_API_MARKET_TO_CANONICAL` target vocabulary this fix resolves through is already UPPER on `market_key` (line
    above), so no separate casing migration is needed here once the parts[]-index bug itself is fixed; this is a
    content-correctness fix that happens to land on the same casing target, not a distinct casing todo. DeFi is the sole
    exception to the 100%-UPPERCASE standard (genuinely mixed per-instrument_type) — sports is NOT exempt.

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
- [x] [DIAG] P1. ✅ Root-caused + backfilled — `batch1_ao_ready` todo 5. Two stacked bugs (unrun Phase-0.6 backfill + a
      deleted legacy-bucket launcher) fixed; 2020-01-01→2026-07-24 re-run shipped (16,661 rows, was 1).
      `features-service@89a2ac9d`, `deployment-service@826ca68`, `instruments-service@47c1ffb3` (verified via
      `git log`). Spun off `issues/manifest_reader_silent_empty_on_missing_project_id_2026_07_24.md` (open, real gap).
- [x] [DIAG] P2. ✅ Wired from standings relegation-zone classification — `batch1_ao_ready` todo 12.
      `features-service@34b53186` (verified via `git log`).
- [x] [DIAG] P2. ✅ **HONEST-ABSENCE, BY DESIGN** — `batch1_ao_ready` todo 13. This line's own "likely-related lead" was
      wrong (not MDPS-sourced); real mechanism: `T-0` is never in any `FEATURE_HORIZONS` visible-horizon list, so these
      columns are structurally null in every row. Live-confirmed across 3 dates, 0/12 sampled non-null. No commit.
- [x] [DATA] P2. ✅ Purged — `batch1_ao_ready` todo 14. `features-service@bf088de1` (verified via `git log`), 16,868
      rows purged (snapshotted first). Post-purge census: 0 rows for all 4 groups.

## Track C — CANON: data_type LOWER-case + venue/instrument_type/chain + manifest atom · P0

- [x] [CODE] P0. ✅ **C1 — migrated the fixtures manifest atom** (all 9 call sites incl. `_honest_coverage_logic.py`'s
      `SCHEDULE_DEFINING_DATA_TYPES`) via `batch1_ao_ready` todos 1+2 (split mid-execution: CODE + DATA backfill). CODE:
      `instruments-service@e19c5a7a` + `unified-api-contracts@6d9c7b59` (constant kept ADDITIVE per
      `unified-api-contracts@c2b303f7` — a protective fix for a real `deployment-api` denominator-test regression; do
      not narrow back to exact-set until the DATA residual below is 0). DATA: `instruments-service@47c1ffb3` (pre-flight
      leak fixes) + `instruments-service@e92efc78` (vectorized restamp, OOM-fix). All 4 SHAs verified via `git log`.
      **PARTIAL — 282,231/337,464 legacy rows restamped; 55,233 dedup-key collisions could NOT be safely restamped** —
      tracked open: `issues/fixtures_manifest_duplicate_collision_residual_2026_07_24.md` +
      `issues/fixtures_manifest_legacy_backfill_2026_07_24.md` (both open, correctly not resolved).
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
- [ ] [REVIEW] P1. Re-verify any existing K1/K2 delete-candidate GCS object list against the CURRENT casing state before
      it's used — it may predate the lowercase→UPPER-case K1/K2 migration (itself now slated for revert above) and could
      be stale either way. **Done when**: a fresh object-level census confirms the candidate list matches the corpus's
      actual casing as of the check date, or a corrected list is produced.
- [x] [CODE] P0. ✅ **NEW — fixed via `batch1_ao_ready` todo 3** — `market-data-processing-service@51502c3` +
      `instruments-service@f46e553e` (verified via `git log`); every non-sports asset_group verified byte-identical.
      **Not independently verified**: the literal done-when (Distinct Values panel on fresh LIVE writes) needs a
      post-fix write to land. Pre-existing finding surfaced (not caused by this fix):
      `mdps_canonical_writer_adapter_contract_baseline_regression_2026_07_24.md` (resolved). Original scope: gate
      venue/instrument_type/chain on asset_group. For sports: venue ← `parts[1]` (the bookmaker token — not the SPORT
      token `parts[0]` it wrongly reads today); `instrument_type` ← the MARKET token `parts[2]` resolved through
      `ODDS_API_MARKET_TO_CANONICAL` (lower-cased to match the casing decision above — not the BOOKMAKER token
      `parts[1]` it wrongly reads today); `chain` ← never written for sports, always null (not the MARKET token
      `parts[2]` it wrongly reads today — sports has no `chain` column in `SPORTS_ODDS_TRADES`'s SchemaContract at all).
      Apply the same fix to `build_instrument_catalogue.py:723-739`'s `_instrument_type_from_id` (IS catalogue side)
      together, same session. Confirmed via direct code read (see Canonical target section above for full detail + line
      numbers): (a) venue via `live_workers.py`/`live_workers_chain.py`/`batch_workers.py`/`candle_write_mixin.py`'s
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
- [ ] [CODE] P0/P1. **EXCHANGE_ODDS vs FIXED_ODDS fork — ABSORBED 2026-07-23, full 10-step sequence** (was a 1-line
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
  - **Ordering caveat** (task_template.md §4 "Verify an Ordering note" rule): the 10 steps above state a strict sequence
    (confirm mapping → drain writers → contracts-first → dual-read → GCS move → dependency_checker update → manifest
    reconcile → cutover → retire legacy) but no machine gate enforces it — this plan is `assigned_vm: NA`, not currently
    AO-dispatched, so this prose ordering is not a dispatch gate. If any step here is ever extracted into an
    AO-dispatched child plan, encode the real ordering via `sequential: true` rather than relying on this note.
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
- [ ] [DATA] P1. **Prune the 7,295 phantom `league_id=soccer_*` lowercase twin-delete manifest rows** (NEW 2026-07-24,
      folded in from archived `sports_master_closeout_2026_07_21.md`). The already-deleted 6,110-object subset is now
      PHANTOM (drift, not a coverage gap — the real data is still covered by the `SOCCER_*` uppercase twins). Clean via
      the GCS-walk rebuild, NOT a session hand-edit (a manual index write with the consolidator running is where
      corruption happens); subsumed by the relocation manifest-swap. Same population as the "FOLD IN" note on the
      league_id-relocation DELETE todo above (Operator decisions section) — one pass, not two.

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
- [x] [DATA] P0. ✅ Ran via `batch1_ao_ready` todo 4 — real verdict all 3 dates: `attempted_failed`/
      `ADAPTER_RETURNED_EMPTY_OUTPUT`, not the predicted split. Live consolidator kept resurrecting the corrected row
      (TOCTOU race) — resolved via slot-4's paused-consolidator CAS write (stable ≥2 cycles) +
      `unified-trading-library@14301571` closing the race (verified via `git log`). Both root-cause issue docs confirmed
      resolved, 0 open todos: `sports_odds_manifest_consolidator_captured_outranks_resurrection_2026_07_24.md`,
      `sports_odds_manifest_captured_outranks_blocks_legacy_leak_correction_2026_07_24.md`.
- [x] [DATA] P1. ✅ Purged via `batch1_ao_ready` todo 6 — 28 legacy T-0 shards deleted (not 27 as estimated),
      snapshot-first; reader check confirmed `read_bucketed_odds()` was live-consuming the leaked path (no reader fix
      needed). Pure data op, no commit; post-delete listing confirmed 0 objects remain for these 3 dates.
- [ ] [DIAG] P1. Root-cause the 112,277 `attempted_failed` rows confined to exactly BETFAIR/MATCHBOOK/PINNACLE (all 6
      years) — likely `_SNAPSHOT_VENUES` CLV completeness, not primary capture. Do NOT relabel without root-cause.
- [ ] [DIAG] P1. Locate the emitter of the 139,620 `venue=ODDS_API, source=api_football, empty_confirmed` rows (not
      `_emit_sports_v1/v2_sentinels`) before folding into K2.
- [ ] [DIAG] P2. Corpus-wide scan for other low-fixture dates whose only in-window odds fall in the T-12h↔T-24h
      615-minute dead-zone; consider adding a T-18h horizon or widening the T-24h staleness cap; investigate why the
      multi-shot `TIER_1_OFFSETS` loop apparently didn't run on the quiet 2025-12 days (only 1 fetch_utc observed).
- [x] [DATA] P2. ✅ **ALREADY DONE 2026-07-22** (predates `batch1_ao_ready` todo 15's own authoring, confirmed via a
      fresh census, not just re-marked): re-stamped via `market-tick-data-service@2f3fb7cc` (verified via `git log`),
      1,337 restamped / 0 escalated. Confirming census: all 4 legacy suffixes=0; canonical bare form=125,400.
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
- [x] [DIAG] P1. ✅ **SCHEMA GAP, not a silent-empty write bug** — `batch1_ao_ready` todo 7,
      `unified-trading-pm@577be4f40` (verified via `git log`). None of the 4 names is a manifest column — the schema
      declares one field, `error_reason`; each of the 4 names is a different adjacent symbol a reader could mistake for
      a stored column. Unblocks Track O's two `[DIAG]` items below — query the real `error_reason` column.
- [x] [DIAG] P2. ✅ **BY DESIGN, not a bug** — confirmed via `batch1_ao_ready` todo 16 (pure DIAG, no commit). Sports's
      venue key is structurally unreachable through the preflight-skip path, the only call site of
      `record_expected_unattempted`. Live-data confirmed: 0 `expected_unattempted` rows in the 563,384-row consolidated
      index.
- [x] [DATA] P1. ✅ Fixed via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 8 —
      `unified-trading-library@fd87daa1` (verified via `git log`), added `"sports": 1800` to `AG_STALENESS_BUDGET_SEC`,
      4 new unit tests. Original target (the observed refresh cadence, per
      `sports_manifest_read_staleness_budget_missing_2026_07_15`'s own ~11-min blob-age swing measurement), not 180-240s
      (**citation corrected 2026-07-24**: the conflicting merge-duration-derived value is from sweep §J, NOT from the
      issue doc — `sports_manifest_read_staleness_budget_missing_2026_07_15` actually already recommends 1800s, matching
      this line's own target value; this line previously misattributed §J's rejected 180-240s value to the issue doc.
      See the correct attribution already present in this same file's "Staleness budget — same defect as sweep §J,
      conflicting fix values" entry below) — merge §J's and the issue doc's fix into this one change.
- [ ] [REVIEW] P2. Honest-coverage atom regrade to per-calculator grain (already operator-decided, implementation
      pending) + league_id namespace reconciliation (check the Track V/H league_id migration todo first — may be the
      same namespace-mismatch problem already partly fixed there) + `fixture_stats` 708-failure root-cause.
- [ ] [CODE] P1. **Implement the registry-aware honest-coverage denominator in `compute_coverage_for_bucket()`**
      (deployment-api; NEW 2026-07-23, decision 6): sports coverage % must reflect "captured / UAC registry universe"
      per the 2026-07-20 operator decision (decision 2 above), not "captured / raw manifest." **ONLY AFTER** the
      league_id migration (Track V's prod-apply, now largely executed — verify current status there before shipping): a
      registry-membership test cannot be correct while any manifest rows still carry non-registry-form `league_id`
      strings — shipping before that lands produces wrong/unstable numbers.
- [x] [DIAG] P2. ✅ **Conclusion: CONFIRMED EMPTY — zero real consumers in either repo.** Grepped via
      `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 17 (pure DIAG, no commit). Exact-literal grep of both repos
      for `"odds_movement"`/`"odds_snapshot"`/`"arbitrage_opportunity"` (as a `data_type` value/path/adapter class)
      returns 0 hits in both — the `odds_movement_home/_draw/_away` hits in `features-service` are a different,
      unrelated FEATURE COLUMN concept, confirmed false-positive by the exact-literal check. Per the operator ruling
      this todo cites: nothing downstream needs them, so retirement (out of this todo's scope) is unblocked.
- [ ] [CODE] P1. **RESTORED 2026-07-24** (dropped with no surviving checkbox in a prior line-cap trim) — canonicalise
      `BOOKMAKER_LEAGUE_COVERAGE` (`unified-api-contracts`, keyed on RAW league names while the sports v2 sentinel calls
      it with a CANONICAL id — a standing coverage false-negative). Fix: regenerate the registry JSON from
      `ODDS_API_DISPLAY_TO_CANONICAL` or re-run `refresh_sports_bookmaker_league_coverage_2026_06_21.py`. Detail:
      archive history doc's "Newly-actionable todos" section.
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
      `sports_cf8_available_at_backfill_regression_2026_07_13.md`.

## Track V — COVERAGE: backfill to honest-100% · P1 (operator-gated where noted)

- [x] [DATA] P1. ✅ Run to full closure via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 9 (pure data-op,
      instruments-service, no code change) — two-stage: corpus-wide re-run (270,938 rows scanned, 374 newly closed) + a
      corpus census isolating the residual to 486 in-window registry-member blank rows, resolved via a targeted backfill
      against the 2 reachable pairs. **Done-when interpretation**: literal "0 remaining" is not achievable given genuine
      honest-absence (393 rows, season not yet published) + fetch-miss residue (7 rows) — both already the sweep's own
      accepted terminal classes — plus a NEW 86-row writer bug (structurally unreachable by the canonical-folder-scoped
      mechanism), filed as its own issue doc:
      `plans/active/issues/sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24.md` (status: open, 1
      open todo, correctly not resolved by this todo's scope). Also spun off (found incidentally):
      `plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` (status: open, 1 open todo). The
      mechanism itself ran to full closure with zero remaining ambiguity — every row has a specific, verified reason.
- [x] [OPERATOR] P1. ✅ **§U decision — ANSWERED 2026-07-20** (see "Operator decisions — ANSWERED 2026-07-20" above,
      decision 2): stop capturing non-registry leagues; the 489-pair/10,869-row population is excluded from the
      denominator and is a purge candidate. **UNBLOCKED 2026-07-24** (corrects the stale "STILL BLOCKED" framing this
      line carried before today) — the league_id migration's manifest COPY+SWAP executed and was independently
      re-verified (275,136/275,136 verify=PASS, stale_remaining=0, `mtds@b2a49317`; full detail: archive history doc's
      "Newly-actionable todos" section, `/plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md`), so
      Premier League/La Liga/Championship now classify correctly in-registry. Snapshot before any delete regardless.
- [ ] [DATA] P0. **RESTORED 2026-07-24** (dropped with no surviving checkbox in a prior line-cap trim) — execute the
      `[OPERATOR]`-only, irreversible, 5-part-proof-gated DELETE of the old raw-keyed league_id GCS objects (the
      COPY+SWAP above is done; only this delete remains). Detail: archive history doc's "Newly-actionable todos"
      section, `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3#1.
- [ ] [OPERATOR] P0. **RESTORED 2026-07-24** (dropped with no surviving checkbox in a prior line-cap trim) — the
      separate, irreversible, 5-part-proof-gated DELETE of old non-canonical K1/K2 GCS objects + the ~7,251 api_football
      captured-cell objects, human-only per the same protocol §3#1. Detail: archive history doc's 2026-07-23
      root-cause-sweep section.
- [x] [OPERATOR] P2. ✅ **§T decision — ANSWERED 2026-07-20** (decision 3): pre-2019 (2013–2018) is OUT OF SCOPE,
      intentionally excluded, no further api-football spend. ~~BLOCKED-OPERATOR-DECISION~~ was stale framing, corrected
      2026-07-23. Remaining work is documentation-only — see the new [DOC] todo below.
- [ ] [DATA] P0. **NEW 2026-07-23 (decision 14) — execute the pre-floor wipe now.** 83,541 pre-floor
      (2014-01-01..2020-06-05) `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` rows fall before the established 2020-06-06
      sports data floor (`/codex/02-data/sports-2020-06-data-floor.md` — pre-floor odds data is fabrication-by-
      construction and gets wiped; this population is the fixtures-side analog). Root-cause fix already shipped
      (UAC@46d865df per the earlier audit); only the disposition ruling + actual wipe execution remain. Snapshot first
      (GCS soft-delete gives a 7-day recovery window), same procedure as the Track F derived_features purge.
      **Duplicate-tracking note (2026-07-24):** the same 83,541-row population is independently tracked in
      `issues/sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md` — this bullet is canonical, that doc's
      remaining todos 2-4 (operator disposition + wipe + re-verify) are the SAME work, not a second population.
- [x] [DOC] P3. ✅ Documented via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 20 —
      `unified-trading-pm@ef78bfffb` (verified via `git log`), updated the audit's §6 "Operator decisions needed" §T
      bullet to state the exclusion explicitly with the exact ruling citation.
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
- [ ] [DATA] P2. Determine which launcher ran the most recent sports features backfill — serial
      `launch-features-sports-backfill-vm.sh` or parallel `launch-features-sports-parallel-backfill-vm.sh` — via VM
      launch history/logs; if serial, file a follow-up todo requiring the parallel launcher for every future sports
      features backfill. **Done when**: the launcher used is named with its citing VM log/dispatch record.

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
- [x] [CODE] P1. ✅ Promoted via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 10 — new SSOT
      `unified_api_contracts/canonical/domain/sports/right_days.py`: `unified-api-contracts@a02a71e0` +
      `instruments-service@a80b3ad2` + `features-service@00547173` (all 3 verified via `git log`). Both real
      literal-constant duplicates found in a full-workspace search now import from the UAC module.
- [x] [CODE] P1. ✅ Built via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 11 — `features-service@7ea10aaa`
      (verified via `git log`; corrected citation — an earlier `4639106a` never reached origin, confirmed unresolvable
      in this repo's `git log`). New `pipeline_middle_leg_check.py` asserts real CONTENT at each leg (not just
      presence); 19 unit tests incl. one deliberate-break case per leg, each confirming the overall report fails while
      other legs still run (shard-level isolation).
- [ ] [BACKEND] P2. Confirm whether any primary sports entrypoint (not a one-off script) exposes a genuine fixture-level
      targeting flag for shard-splitting a backfill run; if none does, file a todo to add one to the primary
      features/MDPS backfill CLI. **Done when**: either a cited flag + file is named, or the add-flag todo exists with a
      named target CLI.
- [ ] [DATA] P1. Run + cite 3 dated checkpoints (pre-backfill baseline, mid-backfill spot-check, post-backfill final
      gate) for EACH of the 5 required mechanisms (`data-pipeline-check-is`/`-mtds`/`-mdps`/`-features` +
      `/data-pipeline-reconciliation`) against sports — currently ZERO real run-todos exist for any of the 5 despite all
      5 already supporting sports's shard atoms (task_template.md §3 finding K). **Done when**: each of the 5 mechanisms
      has 3 dated runs cited by report path/dispatch_id, baseline through final.

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
- [x] [DOC] P2. ✅ Fixed via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 18 — `unified-trading-pm@bfb77b46c`
      (verified via `git log`). Found + fixed real staleness (FIXTURES-migration banner claim, the LEAGUE_REGISTRY
      expected-league-count table drift 102→103). `sports_master.md` had 7 broken paths (not 5) — all fixed + verified
      resolving.

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
      `sports_consolidated_closeout_2026_07_19.md` in its `related:` list + a cross-reference banner. The 5
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
        `sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` as merely open/P2, but
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
- [x] [CLEANUP] P3. ✅ All 3 sub-parts resolved via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 19 — full
      writeup + evidence at `plans/active/issues/sports_closeout_batch1_task018_partial_progress_2026_07_24.md` (status:
      resolved, 0 open todos — verified). (1) 2018-2020 scaffolding: the initial "verified-absent" ruling only checked
      GCS objects and was half right — 26,352 dead `empty_confirmed` MANIFEST rows found + purged via
      `instruments-service@019cbae0` (verified via `git log`). (2) `SPORTS_INSTRUMENTS.md` doc fix —
      `instruments-service@97fbea22`. (3) Junk-symbol guard — `unified-api-contracts@a6346f95`. All 3 SHAs verified.
- [ ] [BACKEND] P2. Audit adapters under instruments-service's `.../adapters/sports/adapters/`, market-tick-data-
      service's `.../adapters/sports/`, and execution-service's `.../sports_execution/adapters/` for dead code, silent
      fallbacks, and duplicated logic — cite `/codex/06-coding-standards/adapter-dead-code-and-fallback-ban.md`. **Done
      when**: a written per-repo finding list (or an explicit "none found") exists, each finding citing a symbol.
- [ ] [DOC] P3. Add `data_completion_sports_history_2026_07_24.md` (0 open todos) as a bulleted entry to
      `/plans/active/sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s Aggregated-source-docs index — it
      is not currently listed there. **Done when**: the entry appears in that file's index with its open-todo count
      noted.

**Folded in from archived `sports_master_closeout_2026_07_21.md` (2026-07-24)** — the 3 remaining open todos from that
doc with no existing equivalent elsewhere in this closeout (the other 3 of its original 6 were folded into existing
todos above — see Track C/S and the "Operator decisions — ANSWERED" section):

- [ ] [DATA] P2. **Peripheral-bucket vocabulary contamination.** A SECOND, DISTINCT non-canonical league vocabulary
      (country-prefixed `ENGLAND_PREMIER_LEAGUE`/`LA_LIGA_2`/`UNKNOWN`, not the api-football-display-name axis the
      league_id relocation fixes) in `features-sports-prd` (30 objects, live to 2026-07-11) +
      `instruments-store-sports-prd` (9,733 objects / 172 values). Root cause + writer UNVERIFIED. MUST NOT be folded
      into the league_id relocation — needs its own writer-trace/fix-at-write/migrate. Detail:
      `issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md` (its "Required work" list is
      numbered prose, not `- [ ]` checkboxes, which is why it undercounts as "0 open todos" in the Aggregated source
      docs digest below — this bullet is the actual live tracking entry).
- [ ] [CODE] P2. **Ship the 2 parked, verified-correct changes sitting unshipped in worktrees.** (1)
      `deployment-service` — 3 launcher `START_DATE` clamp hardening edits + a new
      `launch-sports-league-id-relocation-vm.sh` launcher, in worktree `deployment-service-sports-wt`. (2)
      `market-tick-data-service` — a `--shard-of`/`--shard-index` filter on the relocation executor (verified but
      ultimately unneeded — data-partitioning achieved the same result), in worktree
      `market-tick-data-service-sports-wt`. Both re-verified correct as of 2026-07-22; blocked only by the structural QG
      path-resolution problem below, not by their own content — ship via the normal path once the shared MAIN clones
      quiet down (`git status` each MAIN clone first).
- [x] [DATA] P3. ✅ Filed via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 21 — `unified-trading-pm@749312622`
      (verified via `git log`):
      `plans/active/issues/qg_backfill_disk_and_lint_checks_resolve_via_main_clone_not_worktree_2026_07_24.md`.
      **Correction (this reconciliation pass, 2026-07-24)**: the batch-1 todo predicted this doc would "stay
      `status:     open`... NOT resolved by this reconciliation pass" — that premise is now STALE. Separate, later work
      (not part of batch-1's own scope) root-caused AND fixed the underlying bug — `unified-trading-pm@e70a0d18e`
      (verified via `git log`), a worktree-identity guard shipped to `qg-common.sh`. The doc is genuinely
      `status: resolved` (0 open todos, re-verified). A narrower follow-up (12 repos' deployed QG copies still carry the
      older vulnerable pattern) remains correctly open:
      `plans/active/issues/qg_workspace_root_template_drift_12_repos_2026_07_24.md` (status: open, 2 open todos).

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
      Detail: `sports_cf8_available_at_backfill_regression_2026_07_13.md`.
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
- [ ] [REVIEW] P0. **RESOLVED-BY-FORK 2026-07-24 — track to completion in
      `sports_legacy_fixtures_path_migration_2026_07_24.md`.** Was: "live contradiction with this closeout's
      FROZEN-legacy-path declaration" (`instruments-service@e1524d21`'s `_read_fixtures_entity_with_schedule_fallback`
      actively reads the frozen legacy `entity=fixtures/` path). A live 2026-07-24 measurement found this is NOT solved
      by the 2020-06-06 floor purge (242,688 legacy-shaped rows survive it; ~72,357 carry real data across 2,319 dates)
      — operator ruled scope a real migration, not a grandfather. Forked to the named plan (Phase 1 measures the exact
      load-bearing subset before any data moves). **Done when**: that plan's last todo ships and this line is flipped
      citing its completion commit.
- [ ] [VERIFY] P0. **FINAL full-history zero-missing (R1/R2/R3) — BLOCKED-PREREQUISITES, bounced 6× as of last check.**
      Gate: 0 `expected_unattempted_pending_fetch`, 0 blank-reason, 0 un-evidenced `attempted_failed` for every (source,
      data_type) within coverage windows, plus features ML-ready. Do NOT fetch the `api_football × ODDS eu=89,073` slice
      if it resurfaces — impossible-not-fetchable denominator pollution pending a purge/retype pass, not real work.
- [ ] [DATA] P1. **LINEUPS/PLAYER_STATS need a new 2026-05-10→present catch-up window launched.** Prior fleet completed
      cleanly but only to a fixed end date, not "to present" (~73+ days uncovered as of last check); blocked until the
      P0 FIXTURE_EVENTS/FIXTURE_STATS VMs above clear the api_football singleton launcher lock.
- [ ] [DATA] P1. **Launch the INJURIES (2021-01-01→present) and STANDINGS (2018-01-01→present) full-history windows —
      never launched**, blocked by the same api_football singleton launcher lock; launch once it clears.
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
- [x] ✅ [DATA] P3. **Bogus api_football ODDS rows purge/retype pass.** Root cause fixed (restored `("sports","ODDS")`
      to `SOURCE_PRIORITY`, `unified-api-contracts@57bcc7c5`). **STALE CHECKBOX, corrected 2026-07-24** — this todo
      described the purge as still deferred; it had already shipped: purge DONE 2026-07-16T13:09Z (T3.1 in
      `sports_legacy_bucket_cutover_2026_07_16.md`), 123,149 rows removed (re-measured, not the 127,018 estimate), 0
      remained after, snapshot-first, independently re-verified 2026-07-23/24. Filed:
      `sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md` §B.
- [ ] [VERIFY] P2. **Reconcile the post-07-13 rebuild delta** (`PLAYER_VALUES` −10,934, `ODDS` −3,180 captured cells vs
      the 2026-07-12 verified state) against real GCS objects — phantom-correction or data loss. The one genuinely
      remaining open item in
      `sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md` §D (everything else
      in that doc is done). Gate: per-key manifest-vs-GCS diff for the missing keys.
- [ ] [DATA] P2. **Mirror the staleness-budget fix + drop hardcoded workarounds.** Track H's staleness-budget todo above
      only covers the UTL-side `AG_STALENESS_BUDGET_SEC` add. Two sibling sub-items from
      `sports_manifest_read_staleness_budget_missing_2026_07_15.md` are untracked: (1) mirror `"sports": 1800` into
      deployment-api's `_AG_STALENESS_BUDGET_SEC` (cockpit consolidator-health view), (2) grep the fleet for hardcoded
      `MANIFEST_CONSOLIDATED_STALENESS_SEC` sports workarounds and drop them once the override lands.
- [ ] [DATA] P3. **WEATHER layout mismatch.** Align `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` to the writer's true
      `PER_DAY_PER_LEAGUE` layout (currently registered as bare `entity=weather/weather.parquet`, causing phantom-audit
      false positives). Filed: `sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md` (3
      todos).
- [ ] [DATA] P3. **sports/trades DP_RUN_MOSTLY_EMPTY runbook note + post-DELETE re-check.** Not a live defect (the 87.2%
      ratio spike is a K1/K2 denominator-shrink artifact on already-dead residue, not a new outage), but 2 small
      follow-ups remain: a `check_high_attempted_failed` runbook note for deployment-service (so a future on-call
      doesn't re-diagnose this from scratch) and a re-check once the K1/K2 legacy-object DELETE executes. Filed:
      `sports_trades_attempted_failed_2026_07_23.md`.
- [ ] [DOC] P2. **`sports_features_layer_findings_sweep_2026_07_18.md` is NOT closed by this plan.** 73 open todos (18
      P0/40 P1/14 P2/1 P3), features-layer correctness findings — this closeout's Tracks are deliberately NOT duplicated
      against it (too large to fold into an already-956-line plan that has already been through 2 line-cap extraction
      passes with nothing left to trim). Do not treat sports feature-layer correctness as done when this closeout
      archives — that doc tracks its own, separate completion.

---

> **2026-07-24 line-cap trim (2nd pass, umbrella-exemption removal ruling):** the "Contradiction resolution", "Cross-AG
> finding", "Operator decisions — ANSWERED", and "Progress Log" sections (all resolved/historical, zero open todos)
> moved verbatim to `/plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md`. The "Aggregated source
> docs" discoverability index moved verbatim to
> `/plans/active/sports_consolidated_closeout_aggregated_sources_2026_07_24.md`. Nothing was dropped or summarized — see
> those two docs for full content. This parent retains every genuinely open Track (F/C/S/E/O/H/V/K/D/X/S2), the Codex
> SSOTs, and the still-open "Operator decisions needed (blocking)" section.

## MVP universe

Sports MVP scope is canonically defined at `/codex/02-data/mvp-scope-canonical.md` § Sports — read it before scoping any
backfill/coverage/ML-ready claim in this closeout as "done."

## Codex SSOTs (read before touching a track)

`/codex/02-data/sports-gcs-path-ssot.md`, `…/sports-data-types-catalog.md`, `…/sports-data-source-coverage-matrix.md`,
`…/sports-adapter-dependency-order.md`, `…/availability-manifest-and-data-status.md`,
`…/honest-absence-downstream-handling.md`, `…/pipeline-mode-partition.md`,
`/codex/04-architecture/sports-batch-live.md`, `/codex/05-infrastructure/spot-vms-for-backfill.md`,
`/codex/12-agent-workflow/async-wait-and-poll-discipline.md` (rule 1a). Plan↔codex drift is review-blocking.

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
