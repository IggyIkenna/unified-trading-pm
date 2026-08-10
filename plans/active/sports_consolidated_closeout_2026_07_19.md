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
    /plans/archive/2026_07/sports_consolidated_audit_2026_07_19.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/archive/2026_07/sports_legacy_bucket_cutover_2026_07_16.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/sports_master_closeout_2026_07_21.md,
    /plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
    /plans/archive/2026_07/sports_odds_exchange_fixed_fork_2026_07_18.md,
    /plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md,
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    /plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md,
    /plans/archive/2026_08/sports_legacy_fixtures_path_migration_2026_07_24.md,
    /plans/active/data_pipeline_e2e_milestones_gate_2026_07_24.md,
    /plans/archive/2026_07/sports_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md,
    /plans/archive/2026_08/sports_closeout_exchange_fixed_odds_fork_2026_07_25.md,
    /plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md,
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25.md,
    /plans/active/issues/sports_af_full_entity_completion_2026_08_03.md,
    /plans/active/issues/sports_api_football_live_odds_second_source_conflicts_with_wipe_ruling_2026_08_02.md,
  ]
created: "2026-07-19"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm:
  NA # ⛔ DO NOT flip to `planning` directly (operator ruling 2026-07-23). This plan spreads its open todos
  # across multiple repos with REAL cross-todo dependencies (casing revert must land registry+writers before data;
  # K1 before K2; league_id migration before the honest-coverage denominator fix; several Track S2 items explicitly
  # warn "do NOT attempt step N before step M" in PROSE ONLY, not machine-enforced sequential:/depends_on+
  # gate_on_depends) — flipping this doc's own assigned_vm risks naive concurrent dispatch corrupting exactly the
  # sequencing this plan exists to protect (per §4's "partial parallelism is NOT expressible inside one plan —
  # SPLIT" rule). COUNT NOTE (/plan-reconcile sports shard, 2026-07-26): the open-todo count is deliberately NOT
  # restated in this note — a hardcoded count re-stales on every flip; measure it from the file. This note read
  # "96 open todos" when authored 2026-07-23 and that number is stale (measured 2026-07-26: 37 open / 27 done,
  # matching this doc's own dated recount on `superseded_by:` below), so task_template.md's "10-100 todos, never
  # more" AO-DISPATCHED hard cap is no longer a standalone ground here — the SEQUENCING ground above is what keeps
  # the ⛔ standing, and it is unaffected. To actually
  # dispatch any of this work to AO: extract the specific ready todo(s) into a NEW child plan (10-100 todos,
  # `assigned_vm: planning`) with `depends_on: [sports_consolidated_closeout_2026_07_19]` +
  # `gate_on_depends: true` if it has a real prerequisite, or `sequential: true` if its own todos share files —
  # never by editing this field.
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days:
  46 # RECALCULATED 2026-07-23 (was 12) — the 2026-07-23 reconciliation session grew this
  # plan from ~40 to 94 open todos (19 P0 / 37 P1 / 33 P2 / 5 P3, corrected 2026-07-25 plan-reconcile — the
  # breakdown's own arithmetic summed to 94, not the stated 96) across the casing revert, the 3-bug venue/
  # instrument_type/chain code fix, the league_id migration, the 4 absorbed fold-in plans' live work, and the
  # honest-coverage/CF-8/CAS-tooling/odds-pipeline-dormancy tracks. Methodology: weighted by priority (P0 ~1.2d,
  # P1 ~0.6d, P2 ~0.3d, P3 ~0.15d avg, reflecting multi-repo code+data-migration work at P0 vs cleanup at P2/P3) —
  # a reasoned re-estimate, not false precision; re-check after the first few tracks land.
estimate_calibrated_ai_days: 36.8 # 46 x 0.8 (infra multiplier, unchanged estimate_class)
locked_by:
locked_since:
supersedes:
superseded_by: # recounted 2026-07-25 (plan-reconcile + consolidated-plan split pass) — 37 open/27 done post-split
  # (was 51 open/11 done as of 2026-07-21; this doc's own Track content was substantially relocated into 3 new child
  # plans on 2026-07-25, `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`,
  # `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md`, `sports_closeout_track_s2_foldin_2026_07_25.md`, so the lower
  # count reflects relocation, not just fresh unexecuted work draining down) — real unexecuted work (canonical-honesty
  # fixes, ODDS-LEAK cleanup, honest-coverage backfill tracks). sports_master_closeout_2026_07_21.md
  # is an entry-point redirect only ("that plan + the audit remain the detailed backing" — its own words), not a
  # replacement; this doc stays status: active and is the live execution surface. See its related: list instead.
depends_on:
  [
    sports_closeout_exchange_fixed_odds_fork_2026_07_25,
    sports_closeout_track_x_hygiene_2026_07_25,
    sports_closeout_track_s2_foldin_2026_07_25,
  ]
gate_on_depends:
  true # documents the real prerequisites this split created (Track X's league_id fold-in item must land
  # before this doc's OWN Track V league_id todos proceed; the EXCHANGE_ODDS/FIXED_ODDS fork changes the
  # instrument_type vocabulary this doc's OWN Track C QG-assertion todo checks against) — a no-op for
  # dispatch since this plan is `assigned_vm: NA` and never ingested, but correct documentation of the
  # dependency direction (this doc depends on its own forked-out children, not the reverse).
source:
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/epics/sports_master.md,
    /codex/02-data/sports-2020-06-data-floor.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer_shaping.py,
  ]
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

> **Split notice (2026-07-25) — this doc was over the 1000-line hard cap; 3 self-contained forks moved out.** Each is
> `status: draft`, `assigned_vm: planning`, with its own gated `_finalize` companion (never `active` until operator
> review — see each child's own file):
>
> - Track C's EXCHANGE_ODDS/FIXED_ODDS fork block → `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`
>   (`sequential: true`, 11 todos) — see the short pointer left in Track C below.
> - Track X (plan/doc hygiene + orphan-satellite reconciliation) →
>   `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` (4 todos, after excluding 3 items
>   `sports_consolidated_native_ao_extract_2026_07_25.md` already drafted from the same Track).
> - Track S2 (fold-in absorption from the 3 archived plans) → `sports_closeout_track_s2_foldin_2026_07_25.md` (after
>   excluding 7 items/sub-parts `sports_consolidated_native_ao_extract_2026_07_25.md` already drafted, and correcting 4
>   items that turned out to already be resolved — see that child's own staleness-correction note).
>
> Nothing was dropped: every open todo from the 2 forked Tracks lives in exactly one of the 3 children above (verify
> against each child's own file if in doubt) — this doc's own Tracks F/C(remainder)/S/E/O/H/V/K/D and the sections below
> are unchanged.

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
  movement) waits until this reconciliation pass is fully committed, per operator instruction. **This gating already
  proved load-bearing once** — `issues/sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25.md`
  (resolved) documents a real batch2 todo that initially targeted the OPPOSITE (uppercase) casing direction from this
  Track's revert before being caught and fixed.
- **Fixtures entity split**: `entity=fixtures_schedule` (schedule fields incl. `round`) + `entity=fixtures_outcomes`
  (scores/status), under `pipeline_mode=batch_api_football/`. The legacy bare `entity=fixtures/` is FROZEN (last real
  write 2026-05-23) and must not be read or written. **The manifest `data_type` must record the split entities, not the
  `"FIXTURES"` umbrella** (§ C1). **✅ RESOLVED for reads (2026-08-04): the freeze is now TRUE — no live reads of the
  legacy bare `entity=fixtures/` path remain.** The read fallback `_read_fixtures_entity_with_schedule_fallback` and its
  4 call sites in `sports_fixtures.py` were removed (`instruments-service@333c35d2`,
  `/plans/archive/2026_08/sports_legacy_fixtures_path_migration_2026_07_24.md` todo 5); a full Phase-1 census across all
  2,319 post-floor dates confirmed the fallback was never load-bearing (0 dates where canonical `fixtures_schedule/` was
  empty and legacy `fixtures/` had real data). The two remaining write-side artifacts from the original 2026-07-23 NOTE
  are still open — `sports_manifest_canonicalisation_2026_06_01.md` (treats bare `entity=fixtures/` as active as of
  07-17) and `sports_catalog_league_grain_only_scope_2026_07_08.md` (writes reference data to bare
  `entity={fixtures,teams, injuries}/` under a different namespace) — tracked via Track S/E's todos below. **SECOND
  CROSS-LINK (2026-07-25, `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` todo 1):** that same
  `sports_catalog_league_grain_only_scope_2026_07_08.md` also independently designs a manifest-schema extension for
  per-fixture-grain capture tracking (its own todos), a parallel, independently-designed fixture-grain redesign running
  alongside this closeout's own fixture-grain entity-split work (Track E), with neither doc aware of the other until
  now. That plan's fixture-grain design also depends on correct `league_id` resolution, which this closeout's Track V
  still tracks as unresolved (the raw-keyed `league_id` GCS object DELETE, blocked on Track C's lowercase-revert — see
  Track V above). Neither doc's design is decided by this note; it only makes the dependency visible in both places.
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
    `/plans/archive/2026_08/cross_ag_instrument_type_casing_100pct_directive_2026_07_24.md`) — the
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
- [x] ✅ [DATA] P0. **DONE — verified 2026-07-30 (satellite corpus-hygiene pass; independently confirmed by a concurrent
      `/na-eligibility-audit` sports-tranche pass the same day, same evidence, same conclusion), previously
      false-unchecked (see
      `/plans/archive/issues/ag_closeout_audit_sports_prefilter_covering_gap_and_false_unchecked_p0_2026_07_30.md`
      finding 2).** PURGE the fabricated POST-FLOOR remainder (Jun-Dec 2020 + 2021-2026 only — 2017-2019 + pre-06-06
      2020 are moot, already deleted by the pre-floor wipe), only after the re-run todo above is done for that same
      post-floor scope — overwriting alone is provably insufficient (a re-run never rewrites a day it produces no output
      for, so a fabricated object on a zero-output day survives). Snapshot the delete list FIRST (GCS soft-delete gives
      a 7-day recovery window), then delete every POST-FLOOR `derived_features` parquet still carrying a
      PRE-`2026-07-19` GCS creation timestamp — do NOT re-touch pre-floor dates, they're already handled by the wipe's
      own snapshot+delete. Honest absence beats an invented `competition_phase`
      (`/codex/02-data/honest-absence-downstream-handling.md`). Satisfied by
      `/plans/archive/2026_07/sports_derived_features_postfloor_residue_purge_2026_07_27.md` (`status: complete`, both
      todos `[x]`): its Todo 1 ran the exhaustive Tier-2 SPOT census (2400/2400 in-scope days scanned, Jun-Dec 2020 +
      2021-2026, 26,891 objects) and returned `total_delete=0` / `total_keep=26891` / `total_unparseable=0`; its Todo 2
      (the reversibility-verified purge, downgraded from `[OPERATOR]` 2026-07-27 per a fresh
      `gcs_bucket_soft_delete_retention_seconds()` check) resolved as a verified no-op because nothing was left to
      delete — every in-scope object already carries a `last_modified` on/after the 2026-07-19 cutoff. Sibling checkbox
      in `/plans/archive/issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md` closed on the same
      evidence (now archived). The reversibility framing below stays accurate and re-usable but was never load-bearing,
      since no delete was needed. **⚠️ Corrected 2026-07-27 — the prior "Not `[OPERATOR]`-gated ...
      reversible-for-a-week" framing here was an UNVERIFIED assertion (the canonical negative example
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a cites, alongside this same todo's duplicate copy
      in `sports_consolidated_native_ao_extract_2026_07_25.md`, which was independently corrected 2026-07-26).** Fixed
      then with an actual fresh check, not a re-assertion: this is an object-scoped delete (specific `derived_features`
      parquet objects filtered by creation timestamp, never the bucket) against
      `features-sports-prd-central-element-323112` — `gcs_bucket_soft_delete_retention_seconds(...)` returned `604800`
      (7 days) fresh-checked 2026-07-27 per §3a, so it genuinely qualifies for the reversibility carve-out (finding T,
      `task_template.md`) this time, verified rather than assumed.
- [x] ✅ [DATA] P0. **DONE — same evidence + timestamp as the PURGE todo above.** Re-verify by CENSUS, not sampling,
      only after the PURGE todo above is done — the terminal check is "zero pre-fix-dated POST-FLOOR `derived_features`
      objects remain" (pre-floor is separately verified 0 by the wipe's own census), decidable from object metadata
      alone (a GCS creation-time listing, not a content sample). Sampling is what produced the retracted CLEAN claim
      above. **Done when**: the census returns 0 post-floor objects with a pre-`2026-07-19` creation timestamp. — MET:
      the same exhaustive Tier-2 SPOT census cited above (2400/2400 days, 26,891 objects) IS this census-based
      re-verification; it returned 0 objects with a pre-`2026-07-19` creation timestamp in the post-floor scope
      (`total_delete=0`).
- [x] [DIAG] P1. ✅ Root-caused + backfilled — `batch1_ao_ready` todo 5. Two stacked bugs (unrun Phase-0.6 backfill + a
      deleted legacy-bucket launcher) fixed; 2020-01-01→2026-07-24 re-run shipped (16,661 rows, was 1).
      `features-service@89a2ac9d`, `deployment-service@826ca68`, `instruments-service@47c1ffb3` (verified via
      `git log`). Spun off `/plans/archive/issues/manifest_reader_silent_empty_on_missing_project_id_2026_07_24.md`
      (resolved + archived 2026-07-28, `unified-trading-library@0db19a72`).
- [x] [DIAG] P2. ✅ Wired from standings relegation-zone classification — `batch1_ao_ready` todo 12.
      `features-service@34b53186` (verified via `git log`).
- [x] [DIAG] P2. ✅ **HONEST-ABSENCE, BY DESIGN** — `batch1_ao_ready` todo 13. This line's own "likely-related lead" was
      wrong (not MDPS-sourced); real mechanism: `T-0` is never in any `FEATURE_HORIZONS` visible-horizon list, so these
      columns are structurally null in every row. Live-confirmed across 3 dates, 0/12 sampled non-null. No commit.
- [x] [DATA] P2. ✅ Purged — `batch1_ao_ready` todo 14. `features-service@bf088de1` (verified via `git log`), 16,868
      rows purged (snapshotted first). Post-purge census: 0 rows for all 4 groups.
- [ ] [DIAG] P1. Root-cause why the features-service `sfi_progressive` manifest group is corpus-empty (1 manifest row in
      `features-sports-prd`) despite a documented 2020→today backfill window — confirm whether it's a real
      unexecuted/failed backfill or a recording artifact of the CLI calculator-grain mismatch tracked in
      `issues/sports_features_layer_findings_sweep_2026_07_18.md` §C1, fix or fold into that doc's scope. Source:
      `plans/archive/2026_07/sports_consolidated_audit_2026_07_19.md` §1.4/§2.6 (relocated here per that now-archived
      snapshot doc's own convention that actionable work lives in this closeout).

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
- [x] ✅ [VERIFY] P0. **Retagged 2026-07-29 (corpus hygiene pass): resolved-by-reference — the cited BLOCKED-UPSTREAM
      condition (entity-split writer commit `254fb843` reaching main + an IS Docker rebuild) is resolved: the writer
      cutover completed by 2026-07-14, and `entity=fixtures_schedule`/`entity=fixtures_outcomes` objects are referenced
      as live, post-cutover data in newer docs (`features_sports_fixtures_split_reader_gap_2026_07_15.md`,
      `sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24.md`). This resolves only the reason the
      todo was blocked — the actual Q5/Q6 spot-check re-run described below was never explicitly re-executed and remains
      a genuine small open todo (not claimed done here).** **BLOCKED-UPSTREAM (2026-06-24 — slot-23 GCS spot-check)**:
      After the writer populates Q5/Q6 columns + the entity-split lands, confirm `FIXTURES_SCHEDULE` carries the 9
      HT/ET/PEN phase-timestamp columns and `FIXTURES_OUTCOMES` carries the 11 score-distinction columns populated for
      completed fixtures (regulation / ET-only / ET+PEN cases; NEVER collapse pen-shootout score into a single field).
      Spot-check on real GCS rows for a completed matchweek across the Top-5 EU leagues. **[VERIFY][UI]** the
      deployment-ui schema modal renders both entity schemas — this touches a UI repo, so any tick requires `pw:L2 ✓`
      (`npx playwright test     --project=chromium tests/smoke/`) + a cited regression spec per CLAUDE.md UI
      playwright-gate HARD RULE; on a fleet VM with no dev server, keep `[BLOCKED-PLAYWRIGHT]`.
      <!-- BLOCKED-UPSTREAM evidence (2026-06-24 slot-23): GCS check: entity=fixtures_schedule + entity=fixtures_outcomes DO NOT EXIST in gs://instruments-store-sports-prd-central-element-323112/sports_reference/by_date/ — only entity=fixtures. Q5/Q6 columns absent from ALL sampled parquets: EPL 2026-05-17, Ligue1 2026-05-17, SerieA 2026-05-09, LaLiga 2026-05-09, Bundesliga 2026-05-10, Norway 2026-06-21 (written 2026-05-23 before Q5/Q6 deploy). Root cause: entity-split writer commit 254fb843 ("entity-split fixtures→fixtures_schedule+fixtures_outcomes; writegate strict mode") is on origin/live-defi-rollout as of 2026-06-24 but NOT yet on main. Q5/Q6 additive write path (48c54805, 2026-06-05) IS on main — but existing entity=fixtures parquets were all written before 2026-06-05 and the "old-path-copy" branch does not re-process them. Unblock: 254fb843 promotes main → IS Docker rebuild + VM relaunch → migrate_fixtures_split.py runs on real sports buckets → new entity=fixtures_schedule+fixtures_outcomes paths appear → re-run VERIFY. -->
      (FOLDED IN from sports_fixtures_schema_split_completion_2026_06_20, 2026-07-15, plan-reconcile §6 operator ruling)
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
- [x] [DATA] P0. ✅ **Steps (1) registry + (2) writers DONE 2026-07-27 — step (3) data migration still open, see the new
      todo below.** Triggered by the operator's axis-value-census screenshot showing `odds`(563,754)/`ODDS`(88,339)
      duplicated on the sports `instrument_type` axis — traced to this exact K1/K2 flip still being live in
      `_build_sports_shard_path`. (1) Registry: `unified-api-contracts@bddd063e` removed the uppercase `TRADES` entry
      from `market_data_categories.py::DATA_TYPES_BY_ASSET_GROUP["sports"]` (the uppercase `ODDS` entry had already been
      dropped 2026-07-26, `uac@a32ad5fb`, under `sports_shard_enumeration_cartesian_blowup_2026_07_20.md` Part 2 §2.2 —
      see the correction note added to that doc's Progress Log) and reverted
      `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE`'s `("sports","odds")` value set from `{"trades","TRADES"}` to
      `{"trades"}`; kept `SOURCE_PRIORITY`'s `("sports","TRADES")` key as-is (it's a documented
      `derive_pipeline_mode_for_row()` case-fallback target, not a claimed-valid content value — reclassified in the
      reachability test as `SOURCE_PRIORITY_CASE_FALLBACK_KEY` rather than removed). (2) Writers:
      `market-tick-data-service@7ffabf77` reverted all 3 live call sites — `venue_fetch.py`'s `_build_sports_shard_path`
      path literals (:887,896) + `shard_counts` key tuple (:795-796), `manifest_finalize.py`'s
      `itype_key`/`data_type_key` branch gate (:347), and `sentinels.py`'s v1/v2/`EXPECTED_PAUSED_LEAGUE` row-key
      dicts + `_build_captured_shard_sets`'s match condition (4 total call sites in sentinels.py, one more than K1's own
      original text named — the archived `sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md` already
      flagged this exact gap under its "not fully audited" todo 1). 8 regression-lock tests updated (including the
      `SPORTS` shard-count pin, 88→80 — one fewer `data_type` × 8 venues). Both repos' `quality-gates.sh` green,
      confirmed via matching `.qg_last_passed_sha`. **Not touched (deliberately out of scope, confirmed inert)**:
      `odds_api_adapter.py:781`'s row-level `"data_type": "ODDS"` field — grep-confirmed never read downstream of
      `venue_fetch.py`'s shard grouping, so it doesn't reach the manifest `data_type` column; the archived K1 doc's own
      3-call-site list already excluded it for the same reason.
- [x] [DATA] P0. ✅ **Step (3) — data migration reverted**: 345,852/345,852 uppercase objects copy-verified to
      lowercase + manifest swap (ADD 344,912/REMOVE 215,041, `stale_remaining=0`) — `market-tick-data-service@fa6fd4cd`
      (on-demand run #4, 2026-07-28). Corpus-wide independent post-delete census (2243-day dry-run scan): zero
      UPPER-case `instrument_type=ODDS`/`data_type=TRADES` values remain anywhere. Full detail:
      `/plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md` "Recommended decision" todos
      1-2. **Adjacent finding STILL OPEN (2026-07-27, slot-8)**: 6 venues
      (`BETFAIR_EX_UK`/`BETFAIR_EX_EU`/`SMARKETS`/`MATCHBOOK`/ `BETFAIR_SB_UK`/`BETMGM`) have STALE pre-existing
      lowercase `odds`/`trades` duplicates left behind by an unrelated earlier fork
      (`sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` todo 5 moved their manifest-tracked shards to
      `exchange_odds`/`fixed_odds` but never touched these unregistered lowercase originals) — content-identical to data
      now correctly living at the fork target. NOT part of this K1/K2 revert (different population, no uppercase twin
      involved) — needs its own verify-then-delete pass, folded into the Track V delete todo at line ~698.
- [x] [REVIEW] P1. ✅ Superseded by actual execution — `delete_stale_uppercase_2026_07_27.py` fresh-re-verifies each
      object immediately before its own delete (never trusts a prior candidate list), and the population is now
      independently confirmed empty (0 uppercase objects, full-corpus post-delete scan). No stale-list risk remains.
- [x] ✅ [DIAG] P2. **CLOSED 2026-08-07 — that doc's todos closed.** The TOCTOU fix shipped 2026-07-24
      (`unified-trading-library@2f1582ee`), Round 8 removed all 11,727 bleed rows 2026-07-27, and a fresh independent
      re-check 2026-08-07 confirms 0 bleed rows holding 11 days later — see
      `plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` for full
      evidence (all 4 original todos + Round 7's follow-ups now closed).
- [x] [VERIFY] P1. ✅ **CLOSED 2026-07-27 — the parts[]-index fix's own stated verification gap is now satisfied.** Two
      independent read-only censuses (`read_availability_index` on `market-data-tick-sports-prd-central-element-323112`,
      columns=[instrument_type, written_at]) both found: 0 rows for all 15 bookmaker-name values the original finding
      measured (PADDYPOWER/PINNACLE/betmgm/betway/bovada/coral/fanduel/ladbrokes_uk/skybet/unibet_uk/williamhill/etc.);
      the residual 8 `SPORT` rows all carry `written_at` in `[2026-07-13T23:56:24Z, 2026-07-13T23:56:37Z]` — PRE-DATES
      the fix (shipped ~2026-07-23/24) by over a week, so these are pre-fix historical rows, not a live regression. The
      literal done-when ("Distinct Values panel on fresh LIVE writes") is met: no new bookmaker-name/`SPORT` rows have
      landed since the fix.
- [ ] [DIAG] P3. **PERPETUAL (1 row) / football (9 rows) in the sports `instrument_type` axis — 2 independent read-only
      censuses this session both found ZERO rows for either value**, against
      `market-data-tick-sports-prd-central-element-323112` (same `read_availability_index` reader the axis-census
      endpoint uses, no new GCS walk), ~15 min apart, with an IDENTICAL total row count (465,223) between the two reads
      — i.e. the corpus was stable in that window, this isn't a case of "checked mid-rewrite." The live distribution had
      also shifted dramatically from the operator's original screenshot in the same wider session (total rows 465,223
      vs. an implied 660K+ from the screenshot's top values; `ODDS` 275,136 / `odds` 20,785 vs. the screenshot's `odds`
      563,754 / `ODDS` 88,339) — consistent with substantial concurrent manifest-rewrite activity from OTHER sessions
      between the screenshot and this session (`mtds@e9d9dec0` wrong-source wipe + `mtds@f9f012cb` phantom `soccer_*`
      league_id prune are both cited elsewhere in this doc as recent sports-manifest writes, neither mine). Given
      2-for-2 non-reproduction with a stable total in between, the working conclusion is **already resolved by that
      concurrent activity or a stale deployment-api cache at screenshot time — downgraded from "investigate" to
      "watch."** **Done when**: either value reappears in a FUTURE dated read (re-open then, trace
      `written_at`/`service_name` on the specific row before treating as live), or this is struck as confirmed-dead
      after one more clean read on a later date.
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
      **CORRECTED 2026-07-27 (mdps_t1_recon_job_oom_failing_7_days_2026_07_26.md Phase 0-3)**: the line below used to
      read "Do NOT touch the deliberate `mdps_odds_horizon_bucket` `venue=ODDS_API` aggregate (124,294 rows, reconciled
      2026-07-14) — that's a different, intentional aggregate identity, not this bug." **That framing was WRONG for part
      of the population and is corrected here, not just flagged** — `reprocess_sports_odds.py` writes TWO distinct row
      shapes per captured day, and only ONE of them is a legitimate aggregate: (1) the COARSE per-day row (no
      `league_id`/`timeframe`) is genuinely a deliberate AGGREGATE SENTINEL — `venue=ODDS_API` there means "some
      bookmaker(s) captured this date", not a bookmaker claim, and it stays unchanged (both this script's own resume
      pre-flight and `instruments-service/scripts/enumerate_expected_universe.py`'s `_SPORTS_MANIFEST_VENUE_OVERRIDE`
      depend on that exact value); (2) the FINE per-`(league_id, timeframe)` row was ALSO stamped `venue=ODDS_API`
      pre-fix — genuinely wrong, the exact same conflation class as this todo's own venue/instrument_type/chain fixes,
      since the underlying `bucketed.parquet` shard already carries a real, 100%-present `bookmaker_key` column per row
      (`_materialise_bookmaker_identity`) that was simply never used. **Fixed 2026-07-27**:
      `market-data-processing-service@6f7422e` (forward-only writer fix — fine rows now split per real bookmaker, one
      manifest row per distinct bookmaker present in the shard; `_venue_breakdown_for_shard` + regression tests) +
      `market-data-processing-service@a047b29` (backfill migration script for the ~198,572 already-captured fine rows,
      dry-run-validated against real production data — see the issue doc for the VM-apply run + row-count-conservation
      evidence). `source=mdps_odds_horizon_bucket` was investigated too and confirmed CORRECT/unchanged (UAC's own
      `SOURCE_PRIORITY` entry deliberately names this service as the derived-product producer — a different axis from
      the raw-tick vendor `source=ODDS_API`; multiple other already-shipped scripts independently hardcode this exact
      value as protected). **Done when**: the Distinct Values panel + the QG assertion todo below both read 0
      non-canonical for all three axes.
- [ ] [DATA] P1. **NEW — venue vocabulary cleanup, dispositions for the 9 non-canonical values** (once the parse-bug fix
      above stops new pollution — fix the parser FIRST, re-stamp SECOND, same ordering lesson as the original F1/F2
      note): (1) casing/aliasing rewrite — LADBROKES_UK→LADBROKES, SPORT888→BET888SPORT (both already exist
      correctly-cased in the UAC venue registry, this is a pure re-stamp, no registry gap); **UNIBET_UK/UNIBET_EU are
      NOT part of this rewrite — struck 2026-08-02, see the disproof + pointer below**; (2) cross-AG bleed — KALSHI,
      POLYMARKET rows belong to `asset_group=prediction`; same remediation pattern as the "Cross-AG finding" section
      below (root-cause the write path, then purge); (3) **SMARKETS residual — struck 2026-08-02, see below**; (4)
      parse-bug residue — FOOTBALL/UNKNOWN clear once the venue-parts[0] fix above ships and existing rows are
      re-stamped. Also still fix the original footystats legacy bundle mislabel (`venue=ODDS_API`→`FOOTYSTATS`, 42,476
      rows) — unrelated to the parse bug, a separate writer defect. **RESOLVED 2026-08-02 (operator ruling on
      plan_reconcile_parked_operator_decisions_2026_08_02.md § 1a, option A): the UNIBET-fold and SMARKETS-purge clauses
      are STRUCK from disposition (1)/(3) above, not just banered** — both premises were DISPROVEN 2026-07-27, two days
      after this todo was authored, by measured evidence in
      [`/plans/active/sports_consolidated_native_ao_extract_2026_07_25.md:151-166`](/plans/active/sports_consolidated_native_ao_extract_2026_07_25.md).
      **(a) `UNIBET_UK`/`UNIBET_EU` → `UNIBET` is NOT a casing/alias fold** — a live content comparison proved they are
      genuinely distinct bookmaker feeds (a shared day/league/fixture/market shows DIFFERENT simultaneous odds), so the
      fold was ADDED to `SPORTS_VENUE_FOLD` and REMOVED the same day; it now contains ONLY
      `{"ladbrokes_uk": "LADBROKES", "sport888": "BET888SPORT"}`. Folding would silently conflate two distinct
      bookmakers' live data on every future capture. **(b) `SMARKETS` is NOT deleted-venue residue** — two independent
      live manifest census passes measured **1,113,644–1,652,384 rows** through 2026-07-26, and
      `/codex/01-domain/sports-instruments.md` § "VENUE COUNT CORRECTED 2026-07-24" lists SMARKETS among the 28 live
      registered ODDS_API bookmaker venues. It was never "removed from all repos"; a purge would destroy over a million
      rows of genuine live production data. The `LADBROKES_UK`/`SPORT888` re-stamps in (1), and dispositions (2) and
      (4), are UNAFFECTED and still stand. No worker can pick up the struck clauses anymore — they no longer exist in
      the todo text above, only this historical record of why they were removed.
- **[CODE] P0/P1.** EXCHANGE_ODDS vs FIXED_ODDS fork — **MOVED 2026-07-25** to its own child,
  `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` (`sequential: true`, 11 todos — the GCS-move step split into
  an immediately-dispatchable pass for the 5 already-unambiguous venues plus a separate `[OPERATOR]`-gated follow-on for
  the 3 still-ambiguous ones). See the Split notice near the top of this doc. Not a checkbox here anymore (finding H) —
  track completion via that child + its gated finalize plan.
- [ ] [REVIEW] P1. QG assertion: sports `data_type` ∈ the UAC lower-case sports vocabulary (no UPPER entries once the
      revert above ships), `venue` ∈ the UAC venue registry (never a vendor casing variant, never a prediction-market
      venue, never a deleted venue), `instrument_type` ∈ the declared sports vocabulary (never a bookmaker name),
      `chain` is always null/absent for sports — so this whole class cannot silently return. **This is the
      QG-enforceable version of the Distinct Values target**: the deployment-ui's sports panel for venues /
      instrument_types / data_types / chains should read 0 non-canonical across all four axes once Track C lands.
      **Forward-pointer (2026-07-25 split)**: once `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md` ships, its
      EXCHANGE_ODDS/FIXED_ODDS split changes the sports `instrument_type` vocabulary this assertion checks against —
      re-verify this assertion's vocabulary list includes the new split values before claiming this todo done.
      **2026-08-04 (§F league/fixture/betting-market audit):** census across all 3 sports manifests — `league_id` has 24
      `SOCCER_*`/`soccer_*` case-dupe pairs in MTDS (6,600 UPPER + 3,336 lower), 12 of same in instruments; features
      CLEAN. Fixture: no `fixture_id` column (structural). Betting-market: `instrument_type` CLEAN (40 values, 0 dupes);
      `data_type` casing already tracked above. Full detail: batch8 todo 5.

## Track S — STORE: bucket hygiene + legacy path elimination · P1

- [x] [DATA] P1. ✅ **DONE — via `sports_satellite_ao_dispatch_batch5_2026_07_26.md`**
      (`unified-api-contracts@82db8f8f` + `market-tick-data-service@f6ea0010`, 2026-07-26): T2.9 (MDT schema-contract
      drift) fixed, T2.10 (47,253 phantom `api_football×trades` rows) verified 0 remaining via the 2026-07-23 CAS-safe
      wipe. Post-phase codex audit (T6.7) separately closed in
      `plans/archive/sports_legacy_cutover_closeout_tasks_2026_07_24.md`. Found via `/ag-closeout-audit     sports`
      2026-07-27 — this checkbox was stale (real work done, never flipped here).
- [ ] [CODE] P2. Eliminate (or document) the legacy bare `entity=fixtures/` (no `pipeline_mode=`) write path still
      active today alongside the canonical split writer (5-league subset).
- [ ] [DATA] [CLEANUP] P2. **RETAGGED self-justified 2026-08-03** (operator ruling on
      `sports_v2_1492_row_copy_contradicts_floor_wipe_2026_08_03.md`, "agreed" — the sole-surviving-copy carve-out that
      forced this to `[OPERATOR]` on 2026-08-02 is resolved: the 764 pre-floor cells / 1,528 physical objects were
      WIPED, not preserved, via
      `deployment-service/scripts/wipe_pre_floor_sports_2026_07_21.py --root-prefix     sports_reference_v2/by_date --apply`
      — `{'DELETED': 1528, 'ERROR': 0}`, verified 0 pre-floor day dirs remain). **Remaining scope, still needs the
      original reader-check before proceeding**: 16 post-floor day dirs (2024-12-24..2026-04-20) remain in
      `sports_reference_v2/by_date/` — snapshot-then-cull THESE once confirmed no reader consumes the path (the original
      self-justified gate this todo had before 2026-08-02, now restored). Prod-bucket deletes on the remaining objects
      are still human-only unless reversibility-qualified per
      [`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`](/codex/02-data/gcs-and-manifest-delete-safety-protocol.md)
      § 3a.
- [ ] [DOC] P2. **Finding C correction (2026-07-23): this was mis-scoped, downgraded from the original P1/HIGH.**
      `sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md` is `status: resolved` (corpus-destroying
      risk already remediated, byte-exact GCS soft-delete restore verified) — only its 1 remaining open todo needs
      merging in: correct the cutover runbook's canonical-is-a-superset premise for raw odds on early dates.
      `sports_canonical_migrated_odds_mistamped_footystats` has no standalone issue doc — it's the footystats
      legacy-bundle mislabel already tracked as its own Track C todo above (venue vocabulary cleanup, `venue=ODDS_API`→
      `FOOTYSTATS`, 42,476 rows). **Done when**: the cutover runbook is corrected and cites this doc.
- [x] ✅ [DIAG] P2. **NEW 2026-07-23 (decision 16) — DONE 2026-08-04, `unified-trading-pm@09ce04535`** (batch7 todo 4).
      Both anomalies root-caused: standings cache writes current data to every processing date; transfermarkt writer
      emits Cartesian product of season×trigger-dates; phantom-audit STANDINGS/TEAMS shares the same cause
      (path-template mismatch). Issue doc + 3 follow-up todos:
      `/plans/archive/issues/sports_decision16_anomalies_investigation_2026_08_04.md`.
- [ ] [DATA] P1. **Prune the 7,295 phantom `league_id=soccer_*` lowercase twin-delete manifest rows** (NEW 2026-07-24,
      folded in from archived `sports_master_closeout_2026_07_21.md`). The already-deleted 6,110-object subset is now
      PHANTOM (drift, not a coverage gap — the real data is still covered by the `SOCCER_*` uppercase twins). Clean via
      the GCS-walk rebuild, NOT a session hand-edit (a manual index write with the consolidator running is where
      corruption happens); subsumed by the relocation manifest-swap. Same population as the "FOLD IN" note on the
      league_id-relocation DELETE todo above (Operator decisions section) — one pass, not two.

## Track E — ENTITY-SPLIT: repoint every remaining stale consumer · P1 (sports-specific, no defi analog)

- [ ] [CODE] P1. Repoint the remaining stale `entity=fixtures` consumers (sweep §R's ~9-file list, now 7:
      `backfill_weather.py:154` and `backfill_sports_fixture_stats_manifest.py:91` DROPPED — both files DELETED
      2026-07-26 per `sports_t6_8_oneoff_retirement_residual_2026_07_25.md` item 3 (their hardcoded target bucket
      `instruments-store-sports-central-element-323112` was confirmed 404/deleted 2026-07-16 T5.4, so the repoint here
      is moot for them): `sports_dependency.py`, `sports_fixtures_daily_repoll.py`,
      `rescan_sports_fixtures_canonical.py:328,452`, `enumerate_expected_universe.py:1902`,
      `migrate_sports_per_league.py`, `reconcile_sports_blank_empty_reason_2026_06_24.py`) to `fixtures_schedule`
      (+`fixtures_outcomes` where scores are needed).
- [x] [CODE] P1. ✅ **DONE — already shipped as this plan's own Track E entry, this todo was a stale duplicate never
      flipped.** `instruments-service@3c424e61` threaded `date=`/`bucket=` through every real T1 call site; a
      T0-before-T1 ordering violation now raises in `tests/unit/test_sports_t0_t1_gate_real_callers.py` (4 tests against
      the real orchestrator functions). Full evidence + Progress Log at
      `plans/active/sports_consolidated_native_ao_extract_2026_07_25.md:209-222` (Track E). Source issue archived:
      `/plans/archive/issues/sports_t0_t1_dependency_gate_never_wired_2026_07_15.md`. ~~Wire the T0/T1 dependency gate
      for real: make every real caller of the pre-flight pass `date=`. Currently the pre-flight only fires
      `if date is     not None` and no caller passes it, so the fail-loud boundary is unreachable. **Done when**: a
      T0-before-T1 ordering violation actually raises in a test (not just "the code path exists but is never hit").~~

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
- [x] [DIAG] P1. ✅ **HYPOTHESIS DENIED** — root-caused via `sports_consolidated_native_ao_extract_2026_07_25.md`'s
      Track O todo (`unified-trading-pm` plan-flip, this session): `_SNAPSHOT_VENUES` is inert dead code (zero runtime
      consumers), unrelated to any CLV snapshot pass. Real mechanism: a pre-2026-07-20 sentinel-scope defect in
      `_expected_sports_bookmakers()` (fixed `mtds@accd8aa4`) that only BETFAIR/MATCHBOOK/PINNACLE could pass
      `is_bookmaker_league_covered()` for, routing to `record_failed()`; stacked with a missing
      `SOURCE_PRIORITY[("sports","TRADES")]` entry (fixed `uac@44623d25`) that mislabeled the rows
      `source=api_football`. Both fixes already merged; the 112,277 figure is a historical pre-fix snapshot, not an
      ongoing failure. Full citation-backed finding in the native_ao_extract plan's Track O item. Not relabeled (out of
      scope, per this todo's own text).
- [ ] [DIAG] P1. Locate the emitter of the 139,620 `venue=ODDS_API, source=api_football, empty_confirmed` rows (not
      `_emit_sports_v1/v2_sentinels`) before folding into K2.
- [ ] [DIAG] P2. Corpus-wide scan for other low-fixture dates whose only in-window odds fall in the T-12h↔T-24h
      615-minute dead-zone; consider adding a T-18h horizon or widening the T-24h staleness cap; investigate why the
      multi-shot `TIER_1_OFFSETS` loop apparently didn't run on the quiet 2025-12 days (only 1 fetch_utc observed).
- [x] [DATA] P2. ✅ **ALREADY DONE 2026-07-22** (predates `batch1_ao_ready` todo 15's own authoring, confirmed via a
      fresh census, not just re-marked): re-stamped via `market-tick-data-service@2f3fb7cc` (verified via `git log`),
      1,337 restamped / 0 escalated. Confirming census: all 4 legacy suffixes=0; canonical bare form=125,400.
- [x] [DIAG] P1. ✅ **DONE — same root cause already fixed via `sports_satellite_ao_dispatch_batch2_2026_07_24.md`**
      (`market-tick-data-service@3401c0ab`, "fix fixture_id=NULL propagation in the odds_api backfill path" —
      `_build_fixture_rows()` never emitted a `fixture_id` key, forcing `""` and collapsing shards to league-level; the
      commit adds `"fixture_id": str(af_fixture_id) if af_fixture_id is not None else ""`). Found via
      `/ag-closeout-audit     sports` 2026-07-27 — same mechanism as this todo's SFI/HT-odds pit-gate observation. Not
      independently re-verified against a fresh live capture; flag for a light spot-check if this exact symptom (blank
      fixture_id collapsing odds rows) is ever seen again post-2026-07-24.

## Track H — HONEST-COVERAGE: manifest honesty + denominators · P1

- [x] [DIAG] P0. ✅ **DONE — resolved without AWS IAM, via a different investigation route
      (`sports_satellite_ao_dispatch_batch5_2026_07_26.md`, `unified-trading-pm@3d48c7a9b`).** NOT dormant: manifest
      writes were deliberately re-routed to `instruments-store-sports-prd` (architecture decision, code-enforced since
      2026-07-13); a separate 3-day GCS gap traced to an already-fixed future-date-guard bug. Source issue doc
      `issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md` now `status: resolved`. Found via
      `/ag-closeout-audit sports` 2026-07-27 — this was still the highest-priority-flagged open item in this closeout
      despite being genuinely resolved 2 days ago.
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
      cited in `/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md` todo 17: nothing downstream needs
      them, so retirement (out of this todo's scope) is unblocked.
- [x] ✅ [CODE] P1. **RESTORED 2026-07-24, SHIPPED 2026-07-27 — `unified-api-contracts@804858c9`** (batch7 todo 3). 25
      leagues double-keyed (358/1129 pairs); `canonicalize_odds_api_league_id()` + 10 regression tests; JSON regenerated
      1129→771 deduped.
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
      `sports_cf8_available_at_backfill_regression_2026_07_13.md`. **AUTHORIZED 2026-08-07** — `BLK-d9137d48` lifted;
      not executed this pass (prior regressions + a coordinate-first lesson mean real scheduling care), see that doc.

## Track V — COVERAGE: backfill to honest-100% · P1 (operator-gated where noted)

> **league_id-migration tracking merge (2026-07-27,
> `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` todo 2)**:
> `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`'s open `LEAGUE_ID_TO_TIER` mapping +
> 28-unmapped-`league_id` gap-analysis (its own P1 "gap-analysis follow-ups" todos 1-2) are now merged into
> `issues/sports_league_id_namespace_migration_2026_07_20.md` § "MERGED TRACKING 2026-07-27" — that section, not this
> Track, is the single settled location for the mapping + the 28 IDs. That plan's own "canonical namespace" label for
> raw display strings (`PREMIER_LEAGUE` etc.) and `SOCCER_*` machine keys is scoped to its own golden-window audit only
> — per this closeout's Canonical target section above, the UAC `LEAGUE_REGISTRY` slug (`EPL` etc.) remains canonical;
> no unflagged "raw string is canonical" claim survives in either doc after this merge.

- [x] [DATA] P1. ✅ Run to full closure via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 9 (pure data-op,
      instruments-service, no code change) — two-stage: corpus-wide re-run (270,938 rows scanned, 374 newly closed) + a
      corpus census isolating the residual to 486 in-window registry-member blank rows, resolved via a targeted backfill
      against the 2 reachable pairs. **Done-when interpretation**: literal "0 remaining" is not achievable given genuine
      honest-absence (393 rows, season not yet published) + fetch-miss residue (7 rows) — both already the sweep's own
      accepted terminal classes — plus a NEW 86-row writer bug (structurally unreachable by the canonical-folder-scoped
      mechanism), filed as its own issue doc:
      `plans/archive/issues/sports_fixtures_schedule_noncanonical_raw_league_id_folders_2026_07_24.md` (status: open at
      the time, 1 open todo, correctly not resolved by this todo's scope — that remaining todo was itself resolved
      separately 2026-07-26, `unified-trading-pm@554be628c`; doc now `status: resolved`, archived). Also spun off (found
      incidentally): `plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` (status: open, 1 open
      todo). The mechanism itself ran to full closure with zero remaining ambiguity — every row has a specific, verified
      reason.
- [x] [DATA] P1. ✅ **RETAGGED 2026-07-28 (stale-tag audit — already answered + executed, `[OPERATOR]` never removed).**
      §U decision — ANSWERED 2026-07-20 (decision 2): stop capturing non-registry leagues; the 489-pair/10,869-row
      population is excluded from the denominator, a purge candidate. **UNBLOCKED 2026-07-24**, **CORRECTED
      2026-07-25**: the manifest COPY+SWAP (`mtds@b2a49317`) was claimed re-verified 2026-07-24 but had actually
      silently reverted (TOCTOU race, pre-dated fix `unified-trading-library@14301571`). Re-applied + verified stable
      across 5 consolidator cycles; TRADES stable but **NOT casing-final** (Track C orders this population reverted —
      see DELETE todos below); `odds_horizon_bucket`/`batch_footystats` still un-migrated. Detail:
      `/plans/archive/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`.
- [ ] [DATA] P0. **RESTORED 2026-07-24** (dropped with no surviving checkbox in a prior line-cap trim) — execute the
      5-part-proof-gated DELETE of the old raw-keyed league_id GCS objects (the COPY+SWAP above is done; only this
      delete remains). **UNBLOCKED 2026-07-28**: Track C's lowercase-revert (the prerequisite) has landed — see the Step
      (3) todo above — so this delete is now actionable; the population is a DIFFERENT one from K1/K2's own casing
      (raw-keyed league_id, not instrument_type casing), so it still needs its own fresh candidate-list re-verify before
      running. **Reversibility-verified, no `[OPERATOR]` gate needed** (finding T, `task_template.md`): object-level
      delete only, target `market-data-tick-sports-prd-central-element-323112` —
      `gcs_bucket_soft_delete_retention_seconds(...)` returned `604800` (7 days) fresh-checked 2026-07-27 per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a. Re-query fresh before running, not from this
      citation. Detail: archive history doc's "Newly-actionable todos" section.
- [x] [DATA] P0. ✅ **RESTORED 2026-07-24, EXECUTED 2026-07-28** — the separate, 5-part-proof-gated DELETE of old
      non-canonical K1/K2 GCS objects: `market-tick-data-service@26201c44` (new `delete_stale_uppercase_2026_07_27.py`,
      generation-matched CAS delete, fresh-verify per object) + launcher wiring (`deployment-service@8b93ae7`).
      On-demand VM `canonical-migration-sports-k1k2-upper-del-20260728-152424`: 345,852/345,852 deleted, 0
      skipped/failed, `rc=0`; independently re-verified via a fresh full-corpus dry-run scan showing 0 uppercase objects
      remain. The ~7,251 api_football captured-cell objects half was already separately resolved (verified never existed
      on GCS — 0/197 relevant days + 0/16 direct probes — no delete action required; see
      `/plans/archive/issues/sports_k1k2_delete_bundled_with_twin_less_data_2026_07_27.md` "Note on the api_football
      half"). Full detail: same issue doc's todo 2 (also cites the archive history doc's 2026-07-23 root-cause-sweep
      section).
- [x] [DOC] P2. ✅ **RETAGGED 2026-07-28 (stale-tag audit — already answered, `[OPERATOR]` never removed).** §T decision
      — ANSWERED 2026-07-20 (decision 3): pre-2019 (2013–2018) is OUT OF SCOPE, intentionally excluded, no further
      api-football spend. ~~BLOCKED-OPERATOR-DECISION~~ was stale framing, corrected 2026-07-23. Remaining work is
      documentation-only — see the new [DOC] todo below.
- [x] ✅ [DATA] P0. **NEW 2026-07-23 (decision 14) — execute the pre-floor wipe now.** 83,541 pre-floor
      (2014-01-01..2020-06-05) `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` rows fall before the established 2020-06-06
      sports data floor (`/codex/02-data/sports-2020-06-data-floor.md` — pre-floor odds data is fabrication-by-
      construction and gets wiped; this population is the fixtures-side analog). Root-cause fix already shipped
      (UAC@46d865df per the earlier audit); only the disposition ruling + actual wipe execution remain. Snapshot first
      (GCS soft-delete gives a 7-day recovery window), same procedure as the Track F derived_features purge.
      **Duplicate-tracking note (2026-07-24):** the same 83,541-row population is independently tracked in
      `issues/sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md` — this bullet is canonical, that doc's
      remaining todos 2-4 (operator disposition + wipe + re-verify) are the SAME work, not a second population. — **DONE
      2026-07-27, `instruments-service@05c6a75f`**, executed via `sports_satellite_ao_dispatch_batch7_2026_07_27.md`
      todo 2 (full evidence there): fresh §3a retention check (604800s) + no-live-writer confirmed; the cited 83,541
      count was stale (the durable audit parquet backing it was regenerated 2026-07-25 after the registry fix,
      reclassifying this population out of its report) — a fresh bounded census at execution time measured the actual
      current population at 30,182 objects (15,233 `fixtures_schedule` + 14,949 `fixtures_outcomes`), which is what was
      snapshotted and deleted; post-delete census confirmed 0 remain.
- [x] [DOC] P3. ✅ Documented via `sports_closeout_batch1_ao_ready_2026_07_24.md` todo 20 —
      `unified-trading-pm@ef78bfffb` (verified via `git log`), updated the audit's §6 "Operator decisions needed" §T
      bullet to state the exclusion explicitly with the exact ruling citation.
- [ ] [DATA] P1. Execute the open residual work from archived `sports_p2_history_apifootball_2015_to_present`'s own
      todos + the 94-league enrichment backfill from `sports_canonical_universe_and_apifootball_reference_expansion`
      (**CORRECTED 2026-07-24** — only `sports_p2_history_apifootball_2015_to_present` is archived/superseded into this
      closeout; `sports_canonical_universe_and_apifootball_reference_expansion` is NOT — it is still `status: active`
      with its own ~9-11 open `- [ ]` todos, per
      `/plans/archive/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md`. This is still the literal
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

## Track D — CODEX: doc alignment · P1 (CLOSED, extracted 2026-07-25)

Fully closed (both items `[x]`) — extracted to
`/plans/archive/2026_07/sports_consolidated_closeout_track_d_history_2026_07_23.md` (line-cap remediation).

## Track X — CLEANUP + plan reconciliation · P2 (✅ DONE 2026-08-10)

All open work shipped via `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` (4 todos + the
split-out migration sub-todo): the `sports_catalog_league_grain_only_scope` cross-link
(`unified-trading-pm@dc8b142a4e`), the `sports_odds_bookmaker_coverage_enumeration` league_id fold-in merge
(`unified-trading-pm@69b8c3f7f3`), the peripheral-bucket league-vocabulary contamination fix
(`unified-api-contracts@f3f1bbe0` write-path fix + the 9,733-object migration `market-tick-data-service@b37b8553`), and
the 2 parked worktree changes (`market-tick-data-service@03b9ffd6` + `deployment-service` no-op clean). All cited
commits verified via `git log` (2026-08-10). 3 further items (the issue-doc index fix, the adapter dead-code/fallback
audit, the `data_completion_sports_history_2026_07_24.md` aggregated-sources index entry) were independently extracted
by `sports_consolidated_native_ao_extract_2026_07_25.md` before this split ran, so are not duplicated in the new child
either. Every item that was already `[x]` done at split time is preserved verbatim in
`/plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md`'s "2026-07-25 — Track X + Track S2 line-cap
split" section.

## Track S2 — FOLD-IN ABSORPTION: live items extracted from the 3 archived plans not covered above (2026-07-23) (MOSTLY MOVED 2026-07-25)

Open work forked to `sports_closeout_track_s2_foldin_2026_07_25.md` — see the Split notice near the top of this doc.
That child's own verification pass (finding C — check the doc doesn't already show it done) found 4 items this Track had
described as live open work were actually already resolved and archived (the IS L6 index regression 3-step fix, the
`exit_code_fleet_monitor` misclassification fix, the api_football gate-reader fix, and the WEATHER layout mismatch fix)
— carried there as closed digests citing the resolving commits, not re-manufactured as open todos. 7 further
items/sub-parts were independently extracted by `sports_consolidated_native_ao_extract_2026_07_25.md` before this split
ran. Every item that was already `[x]` done at split time is preserved verbatim in
`/plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md`'s "2026-07-25 — Track X + Track S2 line-cap
split" section.

---

> **2026-07-24 line-cap trim (2nd pass, umbrella-exemption removal ruling):** the "Contradiction resolution", "Cross-AG
> finding", "Operator decisions — ANSWERED", and "Progress Log" sections moved verbatim to
> `/plans/archive/2026_07/sports_consolidated_closeout_history_2026_07_24.md` — **correction: NOT "zero open todos" as
> claimed here; 12 checkboxes there are still open** (2 P0 items pulled back into Track V/Track H same day; that doc is
> the source of truth on the rest). The "Aggregated source docs" discoverability index moved verbatim to
> `/plans/archive/2026_07/sports_consolidated_closeout_aggregated_sources_2026_07_24.md`. Nothing was dropped or
> summarized — see those two docs for full content. **Correction (2026-07-25, 3rd trim pass)**: Track X and Track S2 are
> no longer fully retained here either — both were mostly forked out to
> `/plans/archive/2026_07/sports_closeout_track_x_hygiene_2026_07_25.md` /
> `sports_closeout_track_s2_foldin_2026_07_25.md` (see the Split notice near the top of this doc); this parent now
> retains Tracks F/C(remainder)/S/E/O/H/V/K/D in full, plus short pointers for X/S2, the Codex SSOTs, and the still-open
> "Operator decisions needed (blocking)" section.

## MVP universe

Sports MVP scope is canonically defined at `/codex/02-data/mvp-scope-canonical.md` § Sports — read it before scoping any
backfill/coverage/ML-ready claim in this closeout as "done."

## Codex SSOTs (read before touching a track)

`/codex/02-data/sports-gcs-path-ssot.md`, `…/sports-features-bucket-path-layout.md`, `…/sports-data-types-catalog.md`,
`…/sports-data-source-coverage-matrix.md`, `…/sports-adapter-dependency-order.md`,
`…/availability-manifest-and-data-status.md`, `…/honest-absence-downstream-handling.md`, `…/pipeline-mode-partition.md`,
`/codex/04-architecture/sports-batch-live.md`, `/codex/05-infrastructure/spot-vms-for-backfill.md`,
`/codex/12-agent-workflow/async-wait-and-poll-discipline.md` (rule 1a). Plan↔codex drift is review-blocking.

## Operator decisions needed (blocking) — 2026-07-23

Genuinely still-open items needing operator input or a monitored/gated execution window (replaces the deleted stale
section above, which conflated answered and open items):

- **League_id migration prod-apply + delete** (decision 7) — scheduling, not a question, but the actual window needs
  picking.
- **CF-8 maintenance window** (decision 11) — same, scheduling.
- ~~**Sports ODDS_API capture pipeline dormancy investigation** (decision 8) — needs AWS IAM access this session didn't
  have; genuinely the top-priority next action.~~ — **stale, DONE** (Track H's 1st `[DIAG] P0` todo, `[x]` since 07-27,
  resolved w/o AWS IAM, `pm@3d48c7a9b`; na-eligibility-audit 2026-08-08).
- **§O diagnoses before any relabel** (Track O's 2 `[DIAG]` items — "Root-cause the 112,277 `attempted_failed` rows..."
  and "Locate the emitter of the 139,620 `venue=ODDS_API, source=api_football, empty_confirmed` rows...") — root-cause
  the 112,277 `attempted_failed` triplet and the 139,620 `empty_confirmed` emitter before relabeling either; these are
  engineering diagnosis work, not a pure operator ask, but flagged here since a premature relabel would be
  irreversible-adjacent.
- ~~`sports_master_closeout_2026_07_21.md` entry-point relationship field (decision 9)~~ — **stale, this was DONE** (see
  Track X's decision-9 todo above, `[x]` since 2026-07-23) — no operator input was actually needed, the
  `entry_point_for:` field addition was mechanical. Left struck-through rather than deleted so the "this section used to
  list it" fact stays visible (finding C, caught in the same pass as the Track X flip).

- **2026-07-27** — Discoverability fix (`na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` Phase 4): 4
  sports-tagged docs reclassified `assigned_vm: NA → planning` this session were not mentioned anywhere in this hub —
  the "orphan invisible to sweep" bug class fixed twice before. Added here for future tranche-sweep discoverability:
  `issues/mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md`,
  `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`,
  `issues/qg_size_gate_sentinel_skip_root_cause_2026_07_25.md`,
  `issues/sports_clv_target_builder_family_route_likely_same_pit_gap_2026_07_26.md`. None were tracked in any Track
  above; all are now `assigned_vm: planning` and live in the AO backlog. (A 5th candidate,
  `issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`, was ALSO reclassified this session but no
  longer needs a Sources mention — a real AO worker already claimed, resolved, and archived it mid-session, per
  `unified-trading-pm@4be5cf08f`.)

## Progress Log

> **Line-cap remediation (2026-08-10)**: entries from the 2026-07-30 na-eligibility-audit marker through the 2026-08-08
> na-eligibility-audit marker were extracted verbatim to
> `/plans/archive/2026_08/sports_consolidated_closeout_progress_log_history_2026_08_10.md` to bring this doc back under
> the 1000-line hard cap. New entries append below the kept 2026-08-09 (round11) entry.

- **round11 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA, valid — re-confirmed the standing ⛔ 2026-07-23 operator
  ruling against a direct `assigned_vm` flip still holds (naive concurrent dispatch would corrupt this plan's own
  prose-only cross-track sequencing; citation + `gate_on_depends: true` on 3 forked children still present in the
  frontmatter). This closeout continues to be fed by the established per-item satellite-extraction cadence (batches
  1-12, most recently `sports_satellite_ao_dispatch_batch11_2026_08_09.md`/`batch12` today, both of which reference this
  doc's Tracks without duplicating them) rather than a whole-doc flip — consistent with every prior audit pass. No new
  extractable item found beyond what batch9-12 already claimed. No flip.
