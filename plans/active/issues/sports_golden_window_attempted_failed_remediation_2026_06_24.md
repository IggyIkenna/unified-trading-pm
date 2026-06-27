---
title: Sports golden-window attempted_failed remediation — mostly misclassification, not missing data
created: 2026-06-24
parent_epic: sports_master
source:
  - "Coverage audit 2026-06-24: golden window (2025-09-01..2025-11-30) instruments 98.0% / market-data 94.1%; ~5,900
    attempted_failed cells"
locked_by: live-defi-rollout
priority: P2
status: active
---

> **🔱 RE-HOMED to `vm-sports` (2026-06-27).** The open fixes here (#2 understat-404, #5 forward path-shapes, #6
> IS-ODDS-wipe, the `--unphantom` re-run, the odds-api 3-league gaps) are now owned by the golden-window-first vm-sports
> plan set — see `sports_p0_sourcing_and_honest_coverage_correctness_2026_06_27.md` (#2/#5/#6 + unphantom) +
> `sports_p1_golden_window_mtds_odds_2026_06_27.md` (odds-api gaps), under coordinator
> `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md`. This issue doc remains the diagnosis-of-record;
> dispatch now happens via those plans.

## Diagnosis (measured 2026-06-24)

Golden window is effectively at 100% on FIXTURES/MATCHES/TEAMS/VENUES/LEAGUES/ODDS/XG/STANDINGS/PLAYER_STATS. The ~5,900
`attempted_failed` cells are **mostly misclassification, not missing data**:

- **~258 PLAYER_VALUES + FIXTURE_LINEUPS + FIXTURE_STATS** — phantom false-positive: parquet EXISTS on disk; the phantom
  reconciler probed `candidate_parquet_paths` WITHOUT the row's `pipeline_mode=`, so it missed the post-migration
  canonical path. NOT a gap.
- **~165 XG_SHOTS (0% in-window)** — understat over-broad 404: a single per-league 404 flips ALL that-day expected
  leagues to `record_failed(HTTP_NOT_FOUND)` instead of `record_empty`; the genuinely-missing leagues are an honest
  understat coverage gap, not failures.
- **5,265 market-data `trades` (BETFAIR/MATCHBOOK/PINNACLE, source=api_football)** — WRONG SOURCE: the canonical sports
  bookmaker-odds source is **odds-api** (`batch_odds_api`), not api_football. api_football is per-fixture detail only.
  These cells are redundant/wrong-source → wipe (verify odds-api covers them first).
- **~90 INJURIES** — real upstream `ApiFootballResponseError`; retry.

Also surfaced: **no Slack alert fires on `attempted_failed`** — the VM exit-code monitor classifies exit0+some-capture
as CLEAN even with thousands of failed cells, so a partial-failure backfill is invisible (the operator's "why don't
alerts trigger on VM ERRORs" — confirmed gap).

## Fixes

- [x] ✅ #1 [SCRIPT] P1. Phantom reconciler: pass row `pipeline_mode` into `candidate_parquet_paths` so canonical
      post-migration parquets aren't false-flagged. — instruments-service@c01bb1c (QG-green). Cross-asset-group blast
      radius (the reconciler runs for every AG). f|PLACEHOLDER
      `reconcile_phantom_manifest_rows_all.py --asset-group sports --unphantom --apply` re-run flips the ~258 false
      phantoms back to `captured` (consolidator-paused, verify manifest).
- [ ] [CODE] P2. understat per-league 404 scoping (`understat.py`): adapter exposes WHICH leagues errored; orchestrator
      records `record_failed` only for errored leagues, `record_empty(EXPECTED_NO_FIXTURE)` for the rest. Mirrors the
      transfermarkt per-league error-dict pattern. (Same file the off-season-guard agent just shipped — coordinate.)
      BUILT this session (instruments-service working tree, QG-green) — adapter `_failed_league_names: set[str]` +
      `_canonical_league_id(name)` mapping (`La_Liga`→`LA_LIGA` verified) in both the XG (`_xg_fetch_errors>0`) and
      XG_SHOTS branches; per-match `get_match_shots` errors attributed to their league. Pending ship by main agent.
- [ ] [CODE] P3. **3-way understat absence split (EXPECTED_NO_PROVIDER_COVERAGE) — BLOCKED on a coverage source.** The
      canonical 3-way split (provider-not-covering → `EXPECTED_NO_PROVIDER_COVERAGE`; covered+errored → `failed`;
      covered+no-fixture → `EXPECTED_NO_FIXTURE`) cannot use `is_league_entity_covered` for understat: that gate's
      `LEAGUE_ENTITY_COVERAGE` map (UAC `registry/sports_league_entity_coverage`) is keyed ONLY on API-Football
      enrichment entities (`FIXTURE_EVENTS/INJURIES/PLAYER_VALUES/…`) — `XG`/`XG_SHOTS` are absent, so
      `is_league_entity_covered(lid,'XG')` returns `False` for ALL leagues → wiring it would mislabel EVERY understat
      absence (incl. real 404 failures + genuine no-fixture days) as `EXPECTED_NO_PROVIDER_COVERAGE` (the opposite of
      correct). **Today the 3-way is a no-op**: `get_expected_leagues_for_source("understat", ["Prediction"])` already
      returns ONLY understat-native leagues (`{EPL, LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1}`), so the denominator never
      contains a league understat doesn't cover → the 2-way split (#2) is correct for the current expected set. The
      3-way only becomes necessary if the understat expected-denominator broadens to include a league understat lacks;
      then add `XG`/`XG_SHOTS` keys to `LEAGUE_ENTITY_COVERAGE` (built from understat's observed corpus, NOT
      API-Football's), and only then apply the `is_league_entity_covered`-first ordering. Provenance: coordinator
      refinement 2026-06-24 + diagnosis that the gate is API-Football-scoped.
- [x] ✅ #3 [DATA] P1. api*football sports odds wipe DONE (operator: full wipe, odds-api is canonical). Dropped ALL
      1,398,423 source=api_football MTDS-sports rows (trades + odds_horizon_bucket*\* + ARBITRAGE_OPPORTUNITY) + deleted
      231,532 `batch_api_football` GCS objects. `_index` 1,760,262 → 361,839. `trades` now odds_api 211,299 captured /
      **0 failed / 100.0%** (golden-window 5,265 failures gone). Snapshot:
      `_index/snapshots/pre_api_football_wipe_2026_06_24.parquet` (reversible). Consolidator paused→resumed. Script:
      `market-tick-data-service/.../scripts/wipe_api_football_sports_odds_2026_06_24.py` (oneoff; commit pending a clean
      MTDS tree — foreign WIP present; delete after GCS-orphan-sweep).
- [ ] [DATA] P2. odds-api backfill gaps surfaced by the wipe: 3 leagues odds_api doesn't carry
      (`soccer_uefa_champs_league`, `soccer_china_superleague`, `soccer_russia_premier_league`, 2025-H2) + the in-scope
      gap-dates behind the former 112,653 api_football failures — backfill via odds-api (the canonical source), not
      api_football. (UEFA Champions League is the notable one.)
- [x] ✅ #4 [CODE] P2. attempted_failed Slack alert in deployment-service — deployment-service@cb330f7 (QG-green, 8
      tests): per (asset_group, data_type) failure-batch alert so an exit0 backfill that fails thousands of cells is no
      longer invisible. (Gate on real failures, not misclassified honest-absence — fix #1/#2/#3 first so it isn't
      noisy.)
- [ ] [CODE] P2. **candidate_parquet_paths path-shape gap (FORWARD phantom over-flag — DO NOT run forward `--apply` on
      sports until fixed).** UAC `unified_api_contracts/canonical/domain/sports/gcs_paths.py` `candidate_parquet_paths`
      does not emit several real on-disk path shapes, so the reconciler's FORWARD pass false-flags ~144,997 sports
      captured rows as phantom (running forward `--apply` would flip real `captured`→`attempted_failed`). Missing
      shapes: (a) the `fetched_at_hour=` segment (footystats odds), (b) the `transfermarkt_teams.parquet` filename, (c)
      `league=`-without-`season=` (player_values). Add these candidate shapes to `candidate_parquet_paths` (mirror the
      pipeline_mode= candidate addition), then re-verify the forward sports phantom count drops to ~0 before any forward
      `--apply`. **Interim**: the reconciler's NEW `--unphantom-only --apply` mode (instruments-service, this session)
      is the SAFE heal — it runs ONLY the reverse re-validation (phantom→captured), never the forward flip, so the
      ~258/~5,977 genuinely-false phantoms can be healed now without this gap fixed.

## #6 — IS footystats `ODDS` is misplaced (odds = MTDS, not IS) — operator 2026-06-24

**Principle:** odds (any bookmaker odds — footystats OR odds-api) are **market-tick-data (MTDS)**, never
instruments-service. The ONLY footystats odds-like data_type that belongs in IS is **`PREDICTIONS`** (footystats'
_in-house_ prediction model — a derived fixture attribute, not market odds). Measured: IS `ODDS` = 194,789 rows (194,727
footystats + 62 odds_api; 29,701 captured) — **misplaced**; IS `PREDICTIONS` = 195,115 rows (footystats in-house) —
**keep**.

- [ ] [CODE] P2. Drop `"ODDS": "footystats"` from UAC `SPORTS_DATA_TYPE_TO_SOURCE` (league_data.py:152); ODDS is not an
      IS data_type. Remove the footystats ODDS capture path from the IS sports orchestrator (stop fetching odds into
      IS). Keep `"PREDICTIONS": "footystats"`.
- [ ] [DATA] P2. Wipe the existing IS footystats `ODDS` (194,789 manifest rows + the 29,701 captured cells' GCS objects)
      — snapshot-first, consolidator-paused, like the #3 api_football wipe. odds-api in MTDS is the canonical odds
      source (211,299 captured / 0 failed post-#3); IS odds are redundant + wrong-service. Do NOT touch `PREDICTIONS`.
- [ ] [DOCS] P3. Codex: state odds=MTDS-domain (the footystats exception in IS is PREDICTIONS, not ODDS) in
      `tradfi-databento-sourcing-ssot`-style sports SSOT + `instruments-foundation-and-catalogue-completeness.md`
      (sports universe = fixtures + reference + enrichment + footystats PREDICTIONS; NOT odds).
