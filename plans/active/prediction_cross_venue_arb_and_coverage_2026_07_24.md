---
doc_type: plan
title: Prediction cross-venue Kalshi↔Polymarket arb detection + honest-coverage correctness
summary: >-
  The cross-venue Kalshi↔Polymarket arb detector (matcher, dispersion features, strategy engine, GCS arb-store, live
  dispatch), cqg canonicalization, the honest-coverage P0 correctness chain (43a-43d), and historical backfill/manifest
  work for prediction markets; split out of prediction_venue_perps_and_live_clob_depth_2026_06_20.md (plan line-cap
  remediation, 2026-07-24).
status: active
nature: process
asset_group: [prediction]
stage: [meta]
repos:
  [agent-orchestrator, deployment-api, deployment-service, e2e-testing, features-service, fund-administration-service]
scope: [engineer, admin]
tags: [prediction, kalshi, polymarket, arb, cross-venue, honest-coverage, cqg, backfill, manifest]
related:
  [
    # STALE-REF FIX (plan_reconciler, agt-4a2f8b, 2026-08-19): every entry below lacked the leading-slash
    # repo-root-relative form the cross-reference-path convention requires; 3 entries also pointed at the
    # wrong directory (all 3 confirmed archived via a fresh existence check before this fix).
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
  ]
created: "2026-07-24"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
last_updated: "2026-08-09"
locked_by:
locked_since:
supersedes: [prediction_venue_perps_and_live_clob_depth_2026_06_20]
superseded_by:
depends_on:
source: >-
  Split from prediction_venue_perps_and_live_clob_depth_2026_06_20.md (2354 lines / 87 todos, HARD over the 1000L
  line-cap) per plans/active/issues/plan_line_cap_remediation_2026_07_23.md row 23 — operator approved unlocking
  `locked_by: live-defi-rollout` and a 3-way clean-partition (parked perps track / live CLOB-depth capture infra /
  cross-venue arb+coverage). This file carries the cross-venue arb + honest-coverage third verbatim.
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /codex/04-architecture/cross-venue-prediction-arb-detection.md,
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_prediction_manifest.py,
  ]
---

# Prediction cross-venue arb detection + honest-coverage correctness

> **🟢 2026-07-24 — SPLIT FROM `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`.** That plan grew to 2354
> lines / 87 todos across three intertwined tracks and was flagged HARD over the 1000-line cap
> (`plans/active/issues/plan_line_cap_remediation_2026_07_23.md` row 23). Operator approved unlocking
> `locked_by: live-defi-rollout` and a 3-way clean-partition. **This file carries the cross-venue arb detection +
> honest-coverage correctness track verbatim** — every todo and Progress Log entry below was moved unchanged (never
> summarized or rewritten). Siblings from the same split:
> `plans/archive/2026_07/prediction_perps_kalshi_polymarket_parked_2026_07_24.md` (the parked crypto-PERPS venue track)
> and `plans/active/prediction_live_clob_depth_capture_2026_07_24.md` (the live+batch capture pipeline this arb detector
> and coverage math consume as input). The original plan is retained, frozen, at
> `plans/archive/2026_07/prediction_venue_perps_and_live_clob_depth_2026_06_20.md`.

## Progress Log

- **2026-08-04 (slot 6, data_engineering, backlog `prediction_satellite_ao_dispatch_batch4-003`) — cqg recent-window
  catalogue re-enumeration: VERIFIED ALREADY COMPLETE, premise stale (no re-run needed).** The `[SCRIPT] P2` "cqg
  partition-completeness — recent-window catalogue re-enumeration" item's premise ("catalogue refreshed for 2026-06-23
  only; 2026-06-20..22 need re-enumeration") is STALE: the same **2026-06-26 IS enumeration VM run**
  (`instr-backfill-pred-20260621`, this Progress Log's 2026-06-26 entry) that refreshed 2026-06-23 also enumerated
  2026-06-20..22 with the already-fixed classifier — the catalogue objects for all three target dates were created
  2026-06-26 16:04–18:28 GMT, **after** the classifier-fix tarball shipped (2026-06-23 21:08Z). Live read of
  `gs://instruments-store-pred-prd-central-element-323112/instrument_availability/by_date/canonical_question_group=*/day={D}/venue=*/instruments.parquet`
  (`CLOUDSDK_CORE_ACCOUNT=unified-trading-sa`, parquet-footer row counts, cqg is the path partition key — readers
  post-filter by path token, not an in-file column):

  | day                    | files | rows   | real cqg groups | OTHER share |
  | ---------------------- | ----- | ------ | --------------- | ----------- |
  | 2026-06-20             | 56    | 11,086 | 42              | 25.7%       |
  | 2026-06-21             | 57    | 12,052 | 42              | 23.5%       |
  | 2026-06-22             | 59    | 9,986  | 40              | 28.7%       |
  | 2026-06-23 (reference) | 62    | 15,330 | 41              | 21.6%       |

  Each target date carries the full real-cqg spread (BTC_UP_DOWN_DAILY / CPI_PRINT_PER_MONTH /
  FED_RATE_DECISION_PER_FOMC / SPORTS_MLB_MATCH / SPORTS_TENNIS_MATCH / WEATHER_TEMP_DAILY / …, 40–42 real groups per
  date), with the **same OTHER-fraction profile (~22–29%) as the verified-good 2026-06-23 baseline** — i.e. the target
  dates are not anomalous and OTHER is the expected residual for genuinely-unclassifiable markets, not a classifier
  failure. Done-when ("each of those 3 dates now carries populated `canonical_question_group` catalogue rows, count
  cited") is SATISFIED, verified live. **No code change and no re-run**: re-enumerating would only re-write
  byte-equivalent objects against prod GCS (data-engineering EFFICIENCY north-star — don't re-scan when the target state
  is already met). Closure mirrors this plan's todo #1 ("premise was stale — already shipped"). Deep history remains the
  bulk-tick-seed with no per-date catalogue (out of scope, unchanged).

- **na-eligibility-audit 2026-08-02 (prediction tranche, autonomous)**: KEEP-NA, **2 stale items cited** — 9 open, count
  unchanged, re-verified live (`grep -cE '^\s*- \[ \]'` = 9, matching the 9 verdicts below). In scope this run because
  of a real post-marker content change (`3798d1674`, 2026-07-31): the fixture-pairing residual todo gained a
  Partial-progress block recording that MLB shipped across `unified-api-contracts@1dddc680` /
  `instruments-service@62a8b1d8` / `strategy-service@d71c8aa4`, with the remaining team-name-canonicaliser half spun out
  as batch6's own `[DATA] P2` "team-name alias tables" todo. That item therefore already carries its extraction citation
  and needed no fix. **Two siblings did not**, both confirmed extracted verbatim by the Phase-2 conflict-check and both
  now cited in place: the `[UAC] P2` politics/geo item → batch6's `[UAC] P2` (whose own `Done when` ends "and the source
  doc's checkbox is flipped"), and the `[SCRIPT] P2` cqg recent-window re-enumeration → batch4's `[SCRIPT] P2` (sole
  owner since batch6's duplicate copy was resolved 2026-07-31). Rubric-3 citation fixes only — `assigned_vm` untouched,
  no checkbox flipped, zero backlog impact. The remaining six are re-confirmed genuinely NA on the 2026-07-30 marker's
  own reasoning, unchanged: the POLYMARKET instrument-lifecycle item is a self-declared BIG data-correctness finding
  spanning 3 repos plus a UAC taxonomy judgment; the rest are a deployment-service tarball-race design question, a
  per-instrument arb-pairing design call, and manifest polish riding the next single walk. **Also fixed this run
  (hygiene, same file)**: the (3c) sub-block and the 2026-07-31 partial-progress note had drifted to 32-60 spaces of
  leading indentation, which parses as an indented CODE BLOCK inside the list item — so prettier preserved it verbatim
  and every corpus-wide pass re-indented it deeper (measured +8 per pass across three commits, max line 189 chars in an
  898-line doc against the 1000-line hard cap). Re-indented to list-content depth so it renders as prose and prettier
  can normalise it. **Frontmatter note settled at the code level**: the `execution_scope: orchestrator-agent` +
  `assigned_vm: NA` pairing the prior marker reported as a contradiction is cosmetic —
  `regen_backlog_from_plan.py::_resolve_plan_vms()` maps the `NA` sentinel to an empty vm set, so ingestion is blocked
  regardless of `execution_scope`. Not a mis-dispatch hazard; no flip, no operator ruling needed.

- **na-eligibility-audit 2026-07-30 (prediction tranche)**: KEEP-NA, valid — 9 open. Three (fixture-pairing residual,
  politics/geo canonicalization, cqg recent-window re-enumeration) are CONFLICT: claimed verbatim by
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` todos 7/8/9 (and the cqg one doubly, by `batch4` todo 3 — see
  `issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md` Finding 2). The remaining six are genuinely
  NA: the POLYMARKET instrument-lifecycle item is a self-declared BIG data-correctness finding spanning 3 repos plus a
  UAC taxonomy judgment (does `EXPECTED_INSTRUMENT_NOT_LISTED` belong in `EMPTY_CONFIRMED_REASONS`?) plus a manifest
  re-walk; the rest are a deployment-service tarball-race design question, a per-instrument pairing design call, and
  NICE-TO-HAVE manifest polish riding the next single walk. Frontmatter note: this doc declares
  `execution_scope: orchestrator-agent` with `assigned_vm: NA` — reported as part of a 7-doc contradiction class in this
  run's summary, not silently flipped.

### 2026-06-24 (autonomous /autonomous) — FULL ARB-DETECTOR STACK SHIPPED (4 repos) + operational findings

All four code units of the live cross-venue arb detector dispatch are SHIPPED to LDR:

| Unit                                             | Repo@sha                          | What                                                                                               |
| ------------------------------------------------ | --------------------------------- | -------------------------------------------------------------------------------------------------- |
| Detector (kernel+fee-model+runner+CLI)           | features-service@ef7cd58c         | paper-mode loop, PURE/QUOTABLE taxonomy, fee-net, GCS arb-store, 24 tests                          |
| Producer trades-fix                              | market-tick-data-service@ef01a055 | data_type-aware factories + real Kalshi `trade`/Polymarket `last_trade_price` connectors, 25 tests |
| VM launcher + dispatch + watchdog/classification | deployment-service@e9f7092        | `launch-prediction-arb-detector.sh` (LONG_LIVED_LIVE) + `prediction-arb-detect` VM_TASK            |
| Lifecycle-telemetry best-effort                  | unified-trading-library@5011dbc9  | ServiceBootstrap STARTED/STOPPED/FAILED no longer crash a service on an event-sink publish failure |

**Detector VERIFIED end-to-end on live GCS (smoke, batch single-tick):** `run_prediction_cross_venue_dispersion` over
real prod data → the UAC matcher produced **8,932 Kalshi↔Polymarket cross-venue mappings**, then HONESTLY reported **0
two-sided-book overlap** (`two_way_on_both_ticks=0`, `pure_arb=0`, `quotable_arb=0`) — the known thin-Polymarket-crypto
liquidity gate, exactly the design-SSOT's "truthful 0 crossings, N mappings" outcome, NOT a bug. The detector is the
canonical home + reuses the shipped matcher→feature chain unchanged.

**Operational arc (no-fire-and-forget T+10 caught 3 real infra gaps across relaunches — each fixed):**

1. VM ran the wrong module (`features_service` not `features_service.cross_instrument`) — a concurrent fleet
   `create-code-tarballs` overwrote my GCS `setup-data-pipeline-vm.sh` upload with the committed (pre-dispatch) version
   because my dispatch was still uncommitted. Fixed by committing (e9f7092) so fleet rebuilds converge.
2. `ServiceBootstrap` `log_event("STARTED")` crashed (rc=1) — the `features-service-events` PubSub topic **did not
   exist** (created it; only data topics + `market-tick-data-service-events` were provisioned).
3. With the topic created, `log_event` then hit `IAM_PERMISSION_DENIED` (the freshly-created topic lacks the VM compute
   SA's publisher binding; my `unified-trading-sa` gcloud auth lacks IAM-admin to grant it). FIXED at the right layer:
   UTL best-effort lifecycle events (5011dbc9) — telemetry publish never crashes a service.

- [x] [OPS] P1. **Provision the `features-service-events` PubSub topic IAM (compute SA publisher) via terraform** — the
      topic was missing entirely (created manually 2026-06-24) and its IAM lacks the VM compute SA publisher binding (so
      lifecycle events fall back to the best-effort warn path, utl@5011dbc9). Add it to the events-topic terraform
      alongside `market-tick-data-service-events` so features-service lifecycle events actually publish. Repo:
      deployment-service (terraform). Provenance: detector VM launch 2026-06-24. ✅ deployment-service@7bb33c1 —
      `features_service_events_pubsub.tf` added: topic resource (with import block for hand-created topic) + publisher
      IAM for default compute SA (manually-launched VMs) + publisher IAM for t1_batch SA (Cloud-Scheduler Cloud Run
      Jobs). QG green. 2026-06-26.

- [ ] [OPS] P2. **Tarball-overwrite race: a concurrent fleet `create-code-tarballs` (from a clone behind LDR) clobbers a
      freshly-rebuilt GCS tarball/setup-script before a new VM's boot-fetch** (hit repeatedly 2026-06-24 launching the
      detector). Mitigated by committing the code so fleet rebuilds converge, but a launch in the race window still gets
      stale code. Consider SHA-pinned tarball fetch (`VM_*_SHA`) in the launchers for just-shipped code, or a
      build-lock. Repo: deployment-service. Provenance: detector launch 2026-06-24.

> **2026-08-16 (slot-30, `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize` P3)** — re-verified: this is
> the ONLY open todo left in this doc. Not shipped, not yet promoted to a batch/`[OPERATOR]` todo — real, genuine
> residual (deployment-service infra race), open-ended enough ("consider X or Y") that it needs a scoping pass
> before it's cleanly AO-dispatchable. Doc stays `active` on this residual alone; not archived this session.
>
> **CORRECTED 2026-08-16 (plan_reconciler, prediction-tranche Phase -1)** — the "ONLY open todo" claim above is
> stale: this doc also carries a `[~]` partial "Fixture-level cross-venue PAIRING" todo (2026-06-23 session, further
> up this Progress Log) with a nested `- [ ]` "Fixture-pairing RESIDUAL — registry-resolution + mapping-population +
> arb wiring" sub-todo that is still genuinely open. 2 open items total, not 1 — both real, neither shipped.

> **Extracted 2026-08-09** — twelve fully-closed dated Progress Log sessions (2026-06-20, 2026-06-21, 2026-06-23 x3,
> 2026-06-25 x4, 2026-06-27 x3) moved verbatim to
> `plans/archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md` to bring this doc back under its
> line-count soft cap (`plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md`). The
> 2026-06-24 session above and the 2026-06-23 fixture-linking session below were LEFT IN PLACE because each still
> carries an open checkbox; the 2026-06-26 session was LEFT IN PLACE because a later entry in this Progress Log
> references it by name ("this Progress Log's 2026-06-26 entry"); the tail of the 2026-06-27 (~10:10 UTC) session's own
> most-recent audit-trail bullets (2026-07-30 onward, below) were LEFT IN PLACE as current status, not archived history.

### 2026-06-23 (autonomous) — fixture-level cross-venue linking is FEASIBLE (Kalshi event tickers encode teams+date)

Operator: there's a lot more cross-venue sports/politics we can DIRECTLY link via fixture ids (tennis/NFL/NBA/soccer).
Confirmed feasible — Kalshi GAME-series EVENT tickers encode the fixture cleanly: `KXMLBGAME-26JUN251945AZSTL` =
`KX{LEAGUE}GAME-{YY}{MON}{DD}{HHMM}{AWAY}{HOME}` (title "Arizona vs St. Louis"). So a canonical fixture key
`(league, {away,home} normalized, date)` is extractable per venue. **UAC schema already supports this** —
`PredictionMarketCrossVenueMapping` (`kalshi_event_ticker`/`polymarket_condition_id`/`api_football_fixture_id`/
`odds_api_event_id`/`canonical_event_id`) + `CanonicalPredictionMarket.mapped_sport_event_id` exist but are unpopulated.

- [~] [DESIGN] P1. **Fixture-level cross-venue PAIRING — parse fixture identity from both venues + link to the sports
  canonical fixture registry**: parts (1)+(2)+(4-guard) **✅ SHIPPED — UAC@3effe2fc** (parts (3) registry-resolution +
  mapping-population + the arb-layer wiring REMAIN; split to the focused residual sub-todo below). (1) ✅ Kalshi —
  `parse_kalshi_sports_fixture(event_ticker, title)` in UAC `canonical/domain/predictions/fixture_parsing.py` →
  `SportsFixtureKey(league, away, home, fixture_date, start_time)`. **Key design correction (verified vs REAL live
  tickers 2026-06-23):** the per-league team-code split is UNRELIABLE — MLB is 3+3 with an HHMM time
  (`KXMLBGAME-26JUN261910SEACLE`), but **NFL has NO time + VARIABLE 2-3-char codes** (`KXNFLGAME-26SEP14DENKC`=DEN+KC,
  `WASPHI`=WAS+PHI) → a fixed-offset split breaks NFL. So teams are derived from the human `title` "Away vs Home"
  (deterministic across leagues); the ticker supplies league (`kalshi_sports_league_for_ticker`, new public accessor
  over `_KALSHI_SPORTS_PREFIX_TO_LEAGUE`) + date (+ MLB HHMM). Season-futures (`KXNBA-27`/`KXNHL-27`) carry no
  GAME/MATCH token → `None` (NO false pairs). Tennis is a player-pair (`KXATPMATCH-26JUN24HUMBRO`→Humbert vs Brooksby).
  (2) ✅ Polymarket — `parse_polymarket_sports_fixture(league, event_title, slug, resolution_date)` → same
  `SportsFixtureKey`; date from the slug's ISO suffix else the resolution date. (4) ✅ guard —
  `SportsFixtureKey.pairing_key()` is the order-independent `(league, sorted(away,home), date)` join; same-game
  Kalshi↔Polymarket prove-equal (test). 14 regression tests vs REAL samples; UAC QG-green (sentinel bc2be9d3).
  Provenance: operator "parse fixture ids for tennis/nfl/nba/soccer" 2026-06-23. (Supersedes the earlier P2
  per-instrument-pairing todo with the concrete fixture-encoding evidence.)
  - [ ] [DESIGN] P1. **Fixture-pairing RESIDUAL — registry-resolution + mapping-population + arb wiring** (parser
        shipped UAC@3effe2fc): (3a) resolve each `SportsFixtureKey` to a canonical sport fixture via the existing
        **sports domain** registry (api-football `fixture_id` / odds-api `event_id` — reuse the
        `ApiFootballAdapter.get_fixtures` cross-ref already in `polymarket/parsing.py::_cross_reference_fixture`) keyed
        on `(league, away, home, date)`; (3b) populate `CanonicalPredictionMarket.mapped_sport_event_id` (IS enum, on
        the sports-prediction instrument record) + `PredictionMarketCrossVenueMapping` (the
        `kalshi_event_ticker`/`polymarket_condition_id`/`api_football_fixture_id` join row).

    (3c) the arb-layer consumer (features/strategy) groups the two venues' instruments by
    `SportsFixtureKey.pairing_key()` WITHIN the shared `SPORTS_{LEAGUE}_{BETTYPE}` cqg → the same-game arb pair. Needs a
    cross-venue team-name canonicaliser (Kalshi "Seattle" ↔ Polymarket "Seattle Mariners"/"Mariners") — extend the
    existing `get_canonical_team_for_polymarket` maps with Kalshi city/abbrev aliases, validated vs REAL paired samples
    (no false pairs — operator). Repos: unified-api-contracts (mapping populate + team canon) + instruments-service
    (sports-event link on prediction enum) + features-service/strategy-service (arb grouping). Provenance: operator
    "parse fixture ids" 2026-06-23 (residual after parser UAC@3effe2fc).

    **Partial progress 2026-07-31 (`prediction_satellite_ao_dispatch_batch6-008`, slot 14)** — real, tested code shipped
    for MLB across 3 repos (`unified-api-contracts@1dddc680`, `instruments-service@62a8b1d8`,
    `strategy-service@d71c8aa4`; full evidence in batch6's own Progress trail): (3a)/(3b) `_build_mapping()` now stamps
    `PredictionMarketCrossVenueMapping.api_football_fixture_id` (was computed then silently discarded); Kalshi's
    `_parse_market` now stamps `canonical_instrument_id` via `build_fixture_id`/`build_team_id` for every sports league
    (was Polymarket-only); (3c) `strategy-service`'s arb-layer consumer needed NO new grouping logic
    (`_on_tick_cross_venue_prediction` was already fully venue/league-agnostic) — only a live `PREDICTION_ARB_MLB`
    catalogue slot to route MLB ticks into it. `mapped_sport_event_id` (`CanonicalPredictionMarket`, the field this
    item's (3b) originally named) was investigated and found to be DEAD/unwired in production — a separate
    `PredictionMarketMapper.map_market()` pipeline, never called by `build_cross_venue_mapping` or any of its consumers,
    only ever populated by test code — so populating it would not have advanced the real arb-pairing mechanism;
    `api_football_fixture_id` on `PredictionMarketCrossVenueMapping` is the field this pairing pipeline actually
    reads/writes, and that one is now populated. **Still open**: the team-name canonicaliser this sub-item explicitly
    calls for was NOT built — confirmed via direct code reads that NO alias registry exists for MLB/NFL/NBA/tennis
    anywhere in this codebase (only soccer has one); building it unvalidated would risk exactly the false-pair outcome
    this item's own text warns against. Tracked as its own new todo:
    `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s `[DATA] P2` "team-name alias tables" item.

    **Team-name-canonicaliser CLEARED 2026-08-09 (batch9 finalize P2)**: the canonicaliser the "Still open" note above
    named as the remaining gap has SHIPPED — batch6's `[DATA] P2` "team-name alias tables" todo is DONE 2026-08-05
    (`unified-api-contracts@41c13454`, `strategy-service@217e5b0e`; SHA verified reachable on origin,
    `unified_api_contracts/external/sports/team_mappings.py` confirmed present on disk), so the citation above is closed
    at the source: per-league alias dicts (MLB/NFL/NBA/Tennis) + arb catalogue slots for NFL/NBA/Tennis now exist
    alongside the pre-existing MLB slot. This does NOT resolve the separate open provenance question this doc's own
    2026-08-09 na-eligibility-audit note below flags ("Finding 5" — whether `instruments-service@62a8b1d8` covers 3a/3b
    for every league or MLB only) — parent checkbox stays unchecked pending that independent verification.

    **INDEPENDENT VERIFICATION 2026-08-10 (slot 7, review, task
    `meta_plan_corpus_hygiene_ao_dispatch_batch1-f41c803633f5`) — per-part verdict against the real diff of
    `instruments-service@62a8b1d8` (2 files, +59 lines: `kalshi.py` +25, `test_prediction_adapters_comprehensive.py`
    +34):**

    - **3a (registry-resolution — resolve `SportsFixtureKey` to canonical sport fixture via sports-domain registry):**
      PARTIALLY COVERED. The commit stamps `canonical_instrument_id` via
      `build_fixture_id(league, build_team_id(home), build_team_id(away), date)` — a LOCAL, deterministic computation
      with NO network call to api-football or odds-api. This is NOT the external-registry resolution 3a's plan text
      describes ("reuse the `ApiFootballAdapter.get_fixtures` cross-ref"). However, it is the SAME approach the
      already-shipped Polymarket adapter uses (`polymarket/parsing.py::_build_instrument_id`), and the partial-progress
      note above already accepted this as the 3a implementation. Verdict: covers what was actually built and accepted as
      3a; does NOT match the plan text's original registry-resolution spec. No code change needed unless someone wants
      to revisit the registry-resolution design.

    - **3b (populate `PredictionMarketCrossVenueMapping` + `mapped_sport_event_id`):** COVERED (Kalshi half). The commit
      stamps `canonical_instrument_id` on Kalshi `InstrumentRecord` for every `SPORTS_*` market — the Kalshi-side
      prerequisite. Without this, `_build_mapping()` (UAC@1dddc680) cannot pair Kalshi↔Polymarket instruments because
      the Kalshi side has no fixture ID to match on. `mapped_sport_event_id` (`CanonicalPredictionMarket`) was
      separately investigated and found DEAD/unwired — populating it would not advance the real arb-pairing mechanism;
      the field this pipeline actually reads/writes is `api_football_fixture_id` on `PredictionMarketCrossVenueMapping`,
      which the UAC half of this batch populates. Verdict: commit covers its half of 3b; the full 3b requires both this
      commit AND `unified-api-contracts@1dddc680`.

    - **3c (team-name canonicaliser):** NOT COVERED. The commit uses raw venue-rendered team names via `build_team_id`
      directly — no alias registry, no cross-venue normalization. This was explicitly deferred to batch6's `[DATA] P2`
      "team-name alias tables" todo, which shipped 2026-08-05 (`unified-api-contracts@41c13454`,
      `strategy-service@217e5b0e`). Verdict: correctly excluded — the commit message and diff are honest about this.

    - **League scope:** ALL LEAGUES structurally. The code gates on `underlying_axis.value.startswith("SPORTS_")` and
      calls `parse_kalshi_sports_fixture()` which covers every league `fixture_parsing.py` knows (MLB/NFL/NBA/tennis/
      soccer). Test coverage is MLB-only (one `KXMLBGAME-26JUN261910SEACLE-SEA` case + one season-future honest-absence
      case), but the code path is league-agnostic. Verdict: structurally covers all leagues the commit message claims,
      not MLB-only; test gap is a coverage concern, not a code-gap.

    **Overall:** The commit does what its own message claims — stamps `canonical_instrument_id` for Kalshi sports
    fixtures (3a/3b, Kalshi half), honest-absence for non-fixtures, no team-name canonicalisation (3c excluded). The gap
    between the plan text's 3a spec (external registry) and what was actually built (local fixture ID) is a design
    divergence already accepted by the partial-progress note above, not a defect in this commit specifically. Parent
    checkbox remains unchecked — the fixture-pairing residual is NOT fully closed (the team-name canonicaliser shipped
    separately, and the design divergence on 3a means someone could reasonably reopen it).

### 2026-06-26 (autonomous /autonomous) — Kalshi fallback path fixed; IS enum + Polymarket book backfill VMs launched; stale-image alert shipped

**Shipped this session (continuation of prior context):**

4. ✅ [SCRIPT] P1 — UAC fee lift (shipped prior session): `KALSHI_FEE_COEFF=0.07`, `POLYMARKET_FEE_FRACTION=0.0` in
   UAC@4601e242. Plan checkbox flipped prior context.
5. ✅ [OPS] P1 — `features-service-events` PubSub IAM: tf file for topic + default-compute-SA + t1_batch-SA publisher
   grants — deployment-service@7bb33c1. Plan checkbox flipped prior context.
6. ✅ [UAC] P1 — KXHIGH Kalshi weather prefix → WEATHER_TEMP_DAILY: UAC@1aaa5230. Plan checkbox flipped prior context.
7. ✅ [SCRIPT] P2 — Kalshi IS fallback path removed: the dead `instrument_availability/by_date/day={date}/venue=KALSHI`
   fallback (path never existed; IS writes cqg-first since 2026-06-22) is removed from
   `KalshiAdapter._load_lifecycles_from_gcs`. Now relies solely on `market_lifecycle/by_canonical_group/` primary with
   WARNING log when empty. Tests updated (30 unit tests green). Also fixed pre-existing test isolation bug in
   `test_rebuild_tradfi_manifest.py`. mtds@d6edd704, QG-green 119s.
8. [INFRA] — IS Prediction enumeration VM `instr-backfill-pred-20260621` launched for 2026-06-20..21 (fills gap in
   `market_lifecycle/by_canonical_group/` data that was absent pre-06-22). After VM completes → launch Kalshi
   RECENT-window MTDS backfill for 2026-06-20..22.
9. [INFRA] — Polymarket book_snapshot_5 batch backfill VM `mtds-prediction-polymarket-20260626-154329` launched for
   2026-06-20..22 (the pre-live-VM window). Tarball sha `5e52439d` includes UAC fix `1596d4f9`. Verify once VM exits.
10. ✅ [ALERTING] — `DP-VM-007 DP_CLOUD_RUN_STALE_IMAGE` event type + alerting rule shipped: UAC@c6a2fede + UTL@d9d344a9
    add the stale Cloud Run image alert (WARN/FILE_ISSUE for #data-pipeline-alerts Slack channel). Addresses operator
    request to ensure all deployments are alert-covered when running stale code.
11. ✅ [ALERTING] — DP-VM-007 implementation shipped: `stale_image_watcher.py` (308 lines) extracted from
    `meta_watchers.py` + `cli.py` to comply with 900-line limit. Contains `check_cloud_run_image_freshness`,
    `CloudRunImageCheckResult`, injectable `ImageDigestReader`/`LatestDigestReader`,
    `make_image_digest_reader/ make_latest_digest_reader` factories using Cloud Run API + Artifact Registry. Wired into
    `cli.py --mode meta` sweep. Added `emit_finding()` public wrapper in `meta_watchers.py` to avoid private
    cross-module call. Pre-existing TID251 violation in `vm_zombie_watchdog.py:76` suppressed with `# noqa`. QG-green.
    deployment-service@1f4f899.
12. ✅ [FIX] P0 — DeFi manifest consolidator DuckDB 1.5.3 BinderException fix: `enum-universe-v2-defi.parquet` shard (20
    cols) vs canonical `availability_index.parquet` (41 cols) schema mismatch caused `UNION ALL BY NAME` to create
    `NULL AS timeframe` computed aliases that DuckDB treats as SELECT-clause columns → BinderException in
    `PARTITION BY`. Fix: pre-compute shard schema via `DESCRIBE SELECT * FROM read_parquet(...)`, add explicit
    `NULL AS col` pads for missing columns, use plain `UNION ALL` (both incremental and full-rebuild paths). Tested: ran
    locally to completion (12.8s, past DuckDB step). 31 unit tests green. QG-green 118s.
    unified-trading-library@7df4f16e. Clears `DP_CRON_DID_NOT_FIRE::_index/availability_index.parquet` alert once Tier-C
    drain promotes UTL to staging and Cloud Run image is rebuilt (~15-30 min).

**Open live deployments status (2026-06-26 ~22:50 UTC):**

- `prediction-arb-detector-20260626-201140` — RUNNING (15 ARB_DETECT_TICK ticks; 0 pairs expected until fresh book data
  lands)
- `prediction-live-polymarket-book-snapshot-5-20260626-224659` — RUNNING (relaunched on fixed tarball @3043f2dc,
  ~22:47Z)
- `prediction-live-kalshi-book-snapshot-5-20260626-224718` — RUNNING (relaunched on fixed tarball @3043f2dc, ~22:47Z)
- `prediction-live-polymarket-trades-20260626-201051` — RUNNING (unchanged, on tarball 05e84bc5)
- `prediction-live-kalshi-trades-20260626-201119` — RUNNING (unchanged, on tarball 05e84bc5)

**Next actions (2026-06-26 session):**

- T+10min: verify `data_type=book_snapshot_5/` parquets appear in GCS for day=2026-06-26 (Polymarket + Kalshi)
- Confirm arb detector `ARB_DETECT_TICK` shows non-zero `two_way_on_both` once both venue books are live
- Monitor Slack #paper-trading-alerts for any live arb pages (1h cooldown per pair)
- Fix Polymarket IS bare-path parquets:
  `instrument_availability/by_date/day=2026-06-26/venue=POLYMARKET/instruments.parquet` has empty `clob_token_ids`
  (secondary, non-blocking since CQG-partitioned parquets work)
- Check Slack live trading + deadman alerts; add any missing silent-drop monitors

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - dominated by `[DESIGN]`/`[UAC]`
  cross-venue arb-pairing and politics/geo canonicalization calls the doc says would create FALSE arb pairs if
  blanket-mapped.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- swapped in batch4/batch6 (sole executing owners
  of this doc's extracted cqg/fixture-pairing residuals) + rebuild_prediction_manifest.py (active `--apply` script).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06 (prediction tranche, autonomous)**: 7 real open items (strict top-level grep
  undercounts at 6 — one is a 2-space-indented sub-bullet, the fixture-pairing residual). 5 remain KEEP-NA-valid
  (tarball-race design call, POLYMARKET-lifecycle operator-gated re-walk, 2x NICE-TO-HAVE manifest-polish riding the
  next single-walk, mid-gap historical backfill — all independently confirmed still-open/still-gated, several
  cross-checked against `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s own Deferred section). 1
  (fixture-pairing residual, nested) is KEEP-NA-STALE-DUPLICATE, already correctly cited to batch6's team-name-alias-
  tables todo — no action needed. 1 (per-instrument arb-pairing, line 533) CLOSED as KEEP-NA-STALE — a same-run
  classifier flagged this PLAUSIBLE-not-CONFIRMED; independently verified via direct code read (see checkbox) that the
  shipped UAC `build_cross_venue_mapping` matcher is fully consumed end-to-end by features-service's
  `prediction_cross_venue_dispersion` kernel and strategy-service's `build_arbitrage_price_dispersion` — genuinely
  shipped, not a design call still open. Disagrees with the 2026-07-30/08-02 audits, which kept it NA without checking
  the code; this is a fresh finding, not a re-litigation (no operator ruling/redirect-banner/documented-revert protected
  it). 7 open todos -> 6.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — re-verified live (2 open items, down
  from the 6-9 range prior rounds tracked; most items closed/extracted since). Remaining: the `[OPS] P2`
  tarball-overwrite-race item is a genuine open-ended infra design question (two named options, no directive) matching
  this doc's own long-standing precedent for this exact item; the `[SCRIPT] P1` series-scoped historical Kalshi backfill
  residual (the 2025-10→2026-04 mid-gap) is a substantial but genuinely bounded build (IS series enumerator + e2e
  driver, both prerequisites already shipped) and on its own would be a reasonable RECLASSIFY candidate, but
  `assigned_vm` flips whole-doc and the tarball item is a real judgment call, so the doc stays together. Doc stays
  `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-09 (prediction tranche)**: KEEP-NA, valid — 2 open, re-verified (lines 172/380, matches
  Phase 0). Line 172 (tarball race) is `infra`/`ci` scope. Line 380 (fixture-pairing residual) has an open provenance
  question per today's Finding 5 (does `instruments-service@62a8b1d8` cover 3a/3b, not just 3c). **Doc now 1009L, over
  the 1000L hard cap** (was 999 on 08-08) — SCOPED-mode append only; remediation is batch8's active, not-yet-executed
  todo. Doc stays NA.
- **context-scout 2026-08-15**: re-scouted; doc is now 432L (well under the 1000L hard cap, per batch8's 2026-08-09
  extraction — the line-cap issue this note used to describe is resolved); context_scope re-verified (5 entries),
  unchanged.

- **na-eligibility-audit 2026-08-18** [body-hash:277e25cf50a59509]: KEEP-NA, valid -- 2 open items re-confirmed genuine open-ended design/judgment work: an undecided infra tarball-overwrite-race mitigation (2 named options, no directive) and a fixture-pairing design residual explicitly gated by an in-text "(no false pairs -- operator)" annotation. Doc stays NA.
## Extracted items index (2026-08-09)

> **Mechanical todo-conservation index — not live work.** `check_todo_regression.sh` counts total `- [ ]`/`- [x]` lines
> and fails a staged plan whose total shrinks vs `origin/live-defi-rollout`, with no exemption yet for a Finding-J
> archival extraction (filed:
> `/plans/active/issues/todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md`, same root cause,
> different trigger). The 25 lines below are the already-`[x]`-closed checkbox items this extraction moved verbatim to
> `plans/archive/2026_08/prediction_cross_venue_arb_and_coverage_history_2026_08.md` — kept here as one-line stubs
> purely so the mechanical count is conserved (27 total, matching origin); the full original text lives only in the
> archive, not duplicated here.

- [x] [DESIGN] P0. Live cross-venue arb DETECTOR (paper-mode, GCS-persisted, long-lived) — DELIVERED (2026-06-24) — see
      archive.
- [x] [SCRIPT] P0. Producer trades-fix DIAGNOSED + CORRECTED (2026-06-25) — book is LIVE-ONLY + gate root-caused — see
      archive.
- [x] [DESIGN] P1. Trades/mid-price cross-venue dispersion variant — backtestable NOW — SHIPPED — see archive.
- [x] [SCRIPT] P2. Feature honest-absence bug in prediction_cross_venue_dispersion — fixed — see archive.
- [x] [SCRIPT] P1. Polymarket universe load PATH-INCOMPLETE — surface/feature cqg-partitioned load fix — see archive.
- [x] [SCRIPT] P0. Polymarket IS clob_token_ids bridge null — resolved — see archive.
- [x] [DESIGN] P1. CANONICAL HOME — features-service prediction cross-venue dispersion feature — see archive.
- [x] [DESIGN] P1. CANONICAL HOME — strategy-service Kalshi↔Polymarket arbitrage_price_dispersion engine — see archive.
- [x] [UAC] P2. Classifier gap — Polymarket bitcoin-above-<N> / will-bitcoin-reach-<N> slug routing — see archive.
- [x] [SCRIPT] P0. Populate POLYMARKET instrument lifecycle start/end + bound manifest empty-emission — see archive.
- [x] [UAC] P2. Politics/geo cross-venue canonicalization — unified-api-contracts@6c11d0d5 — see archive.
- [x] [UAC] P1. Cross-venue canonicalization BREADTH audit — non-crypto gaps closed (2026-06-24) — see archive.
- [x] [DESIGN] P2. Per-instrument same-game arb-pairing — CLOSED via na-eligibility-audit 2026-08-06 code read — see
      archive.
- [x] [SCRIPT] P1. Polymarket BATCH book_snapshot_5 backfill — VM COMPLETED exit_code=0 (2026-06-26T15:49Z) — see
      archive.
- [x] [SCRIPT] P2. Kalshi RECENT-window (2026-06-20..22) batch trades 0-capture — IS-enumeration gap fixed — see
      archive.
- [x] [DATA] P2. Residual lowercase venue=kalshi + blank/UNKNOWN venue rows in prediction _index manifest — see archive.
- [x] [DATA] P3. 1,454 prediction _index rows at schema v4 — re-walked to v9 — see archive.
- [x] [SCRIPT] P2. Self-enforced rate-limit caps (token-bucket) on prediction REST adapters — SHIPPED — see archive.
- [x] [SCRIPT] P1. rebuild_prediction_manifest --venue POLYMARKET filter + v4→v9 re-walk DONE — see archive.
- [x] [SCRIPT] P2. instruments-service phantom reconciler prefix_tpls covers batch_kalshi — see archive.
- [x] [SCRIPT] P0. instruments-service cutoff-aware date routing — SHIPPED instruments-service@8b118d9 — see archive.
- [x] [SCRIPT] P0. instruments-service RSA-PSS auth — SHIPPED instruments-service@8b118d9 — see archive.
- [x] [DESIGN] P1. CROSS-VENUE BLOCKER RESOLVED + VERIFIED 2026-06-23 — Kalshi catalogue cqg groups — see archive.
- [x] [SCRIPT] P1. cqg partition-completeness — LIVE relaunch DONE 2026-06-23 — see archive.
- [x] [SCRIPT] P2. cqg partition-completeness — recent-window catalogue re-enumeration VERIFIED COMPLETE — see archive.

## Progress Log (cont'd)

- **na-eligibility-audit 2026-08-17** [body-hash:898c2999fc103f29]: KEEP-NA, valid — 2 open, re-verified
  (tarball-overwrite race at line ~172, infra/ci-scoped 2-option design question with no directive; fixture-pairing
  residual nested todo, an open team-name-canonicalization provenance question this workspace's "no false pairs"
  mandate keeps genuinely gated). Matches the 2026-08-09 marker and the 2026-08-16 plan_reconciler's independent
  2-open-item recount. Doc stays NA.

- **na-eligibility-audit 2026-08-17 (prediction tranche, re-verify)** [body-hash:209354abc81b532f]: KEEP-NA, valid —
  2 open items re-confirmed as genuine open-ended design/judgment calls (an unresolved infra tarball-overwrite-race
  mitigation choice with 2 named options and no directive; a fixture-pairing registry-resolution design divergence
  flagged by an independent 2026-08-10 code-diff verification) — no bounded deterministic path, no active
  planning-doc duplicate found. Doc stays NA.

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- re-verified, unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries).
- **na-eligibility-audit 2026-08-21 (prediction tranche)**: KEEP-NA, valid — 2 open items re-confirmed live
  (`grep -cE '^\s*- \[ \]'` = 2): the tarball-overwrite-race infra/ci mitigation choice (2 named options, no
  directive) and the fixture-pairing team-name-canonicalization design residual (explicitly gated by an in-text "no
  false pairs — operator" annotation). Consistent with 6+ prior audit passes. Doc stays NA.
