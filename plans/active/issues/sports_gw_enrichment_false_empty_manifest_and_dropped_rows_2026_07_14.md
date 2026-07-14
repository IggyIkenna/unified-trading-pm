---
doc_type: issue
title:
  GW enrichment fleet (2026-07-14) content-verification RED — 3,720 FALSE-EMPTY manifest cells (EXPECTED_NO_FIXTURE
  stamped over cells whose enrichment parquets EXIST) + 225,854 fetched rows dropped ("could not be mapped to a league")
  + INJURIES writer only touches the 33 prediction-tier leagues
summary:
  "Content verification of the 2026-07-14 golden-window api-football enrichment fleet (5 SPOT VMs, all
  DEPLOYMENT_COMPLETED exit_code=0) FAILED. The fleet DID land real data (2,951 new per-league enrichment parquets,
  ~739k rows written) but (1) emit_empty_gaps_for_entity classifies absence from THIS-RUN captured_league_ids only, so
  every league whose enrichment was skip-as-already-present (the P1a-era top/prediction-tier leagues) was stamped
  empty_confirmed/EXPECTED_NO_FIXTURE over cells whose parquet data exists — 943/975/986/816 false-empty cells for
  EVENTS/LINEUPS/STATS/PLAYER_STATS on the 1,848 captured-fixture GW cells; (2) 225,854 fetched rows (~23% of quota
  spent) were DROPPED by the bare-path fallback ('N rows could not be mapped to a league') because
  _build_fixture_league_map_from_gcs covers only ~35% of the day's canonical fixtures; (3) the INJURIES per-date path
  wrote markers for only the 33 prediction-tier leagues (94 expected), leaving 30 A_LEAGUE September EU cells
  blank-reason. Todo-9 GW gate NOT flipped; the 2020+ full-enrichment fleet launch and the GW features recompute are
  HELD (same write path would replicate the damage at ~400k-call scale)."
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, sports, api-football, enrichment, honest-absence, false-empty, golden-window, data-correctness]
related:
  [
    plans/active/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    plans/active/sports_data_sources_canonical_completion_2026_07_13.md,
  ]
created: 2026-07-14
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
source: [gw-verify agent 2026-07-14 (operator-ruled GW verify -> 2020+ launch chain; chain halted at RED verification)]
resolved_by:
  [
    "instruments-service@0d9ffabd (3-leg write-path fix)",
    "instruments-service@86cc71ff (presence guard + factory pool-date + 94-league zero-day markers + regression tests)",
    "instruments-service@0fe2f17b (gw_false_empty_repair one-off; 4170 restamps)",
    "deployment-service@a79fa65 + e2e-testing@b6b04b8 (launcher --skip-lock + features --force chain)",
    "2026-07-14 16:54Z parquet-presence cross GREEN (false-empty 0 / phantom 0 / blank 0; INJURIES EU 0)",
  ]
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# GW enrichment fleet content-verification RED (2026-07-14)

> **NOTIFY-OPERATOR (data-correctness big finding).** The GW fleet completed green at the VM level (all 5
> `DEPLOYMENT_COMPLETED exit_code=0`, self-deleted) and the naive gate query reads "0 pending-fetch / 0 blank-reason / 0
> missing cells" — but ONLY because false `empty_confirmed` rows cover the cells. Parquet-level truth contradicts the
> manifest on 3,720 cells. The operator-authorized follow-on launches (2020+ enrichment fleet, GW features recompute)
> are **HELD** — launching the same write path over 2020→present would burn ~400k API calls while stamping the same
> false honest-absence over the full history.

## Fleet run being verified

`af-backfill-20260714-111307` FIXTURE_EVENTS · `-111346` FIXTURE_LINEUPS · `-111414` FIXTURE_STATS · `-111447`
PLAYER_STATS · `-111518` INJURIES; window 2025-09-01..2025-11-30; launched 11:13-11:15Z per P2a session-20; all five
`DEPLOYMENT_COMPLETED (exit_code=0)` (INJURIES 11:45:39Z, EVENTS 12:15:06Z, LINEUPS 13:37:06Z, STATS 13:37:36Z,
PLAYER_STATS 13:37:31Z); no `PREEMPTED` blobs; per-VM manifest shards consolidated into the canonical index by 13:39:02Z
(verified swept from `_index/per_vm/`).

## Measured verdict (index snapshot 13:39Z, 5,759,709 rows; GCS parquet presence matrix 91 days x 4 entities)

Scope: the 1,848 deduped captured-FIXTURES `(date, league_id)` GW cells (86 leagues, 91 days, 4,787 fixtures — matches
session-20 scoping exactly). Manifest deduped at key grain with precedence captured > empty_confirmed >
attempted_failed > expected_unattempted, `source=api_football`.

| entity          | manifest captured | parquet PRESENT | **FALSE-EMPTY** (parquet exists, manifest `empty_confirmed`) | parquet-absent + empty | attempted_failed | pending-fetch EU |
| --------------- | ----------------: | --------------: | -----------------------------------------------------------: | ---------------------: | ---------------: | ---------------: |
| FIXTURE_EVENTS  |               537 |           1,480 |                                                      **943** |                    365 |                3 |                0 |
| FIXTURE_LINEUPS |               475 |           1,450 |                                                      **975** |                    396 |                2 |                0 |
| FIXTURE_STATS   |               153 |           1,139 |                                                      **986** |                    698 |               11 |                0 |
| PLAYER_STATS    |               269 |           1,085 |                                                      **816** |                    763 |                0 |                0 |
| INJURIES        |               887 |             n/a |                                                          n/a |                    n/a |      0 (deduped) |    **30, blank** |

- **Phantom-captured = 0 everywhere** (no manifest-captured cell lacks its parquet) — the manifest never over-claims
  capture; it over-claims ABSENCE.
- FALSE-EMPTY cells are overwhelmingly the TOP leagues (LA_LIGA 39, BRASILEIRAO 50, SERIE_A 34, BUNDESLIGA 30, MLS 40,
  LIGUE_1 31 ... 15/15 sampled ENF leagues are prediction-tier); the fleet's 45 newly-captured cells are almost all
  NON-prediction-tier leagues (2/15 sampled in tier). Written-at proves authorship: 1,177 of 1,204 EVENTS ENF rows
  written 2026-07-14 (the fleet), vs the 492 pre-existing captured rows written 2026-07-13.
- Cell-level content proof: `(2025-11-08, LA_LIGA, FIXTURE_EVENTS)` — manifest `empty_confirmed/EXPECTED_NO_FIXTURE`
  (written today) while
  `sports_reference/by_date/day=2025-11-08/pipeline_mode=batch_api_football/entity=fixture_events/league=LA_LIGA/fixture_events.parquet`
  holds **65 event rows across 4 fixtures**.
- The fleet also DID land real new data: 2,951 of the 5,160 present enrichment parquets have object mtime 2026-07-14;
  ~739k rows written across the 4 per-fixture VMs.
- **Dropped rows**: run.log sums of the `"N rows could not be mapped to a league. Skipping bare write"` warnings —
  EVENTS **53,805** dropped (vs 56,843 written), LINEUPS **126,016** (vs 381,241), STATS **2,182** (vs 14,324),
  PLAYER_STATS **43,851** (vs 286,351) = **225,854 rows fetched-then-dropped** (quota paid, data discarded). The
  bare-path fallback fired on 91/91 dates (EVENTS, LINEUPS) and 83/91 (STATS, PLAYER_STATS).
- INJURIES: the 30 `expected_unattempted` blank-reason cells are A_LEAGUE 2025-09-01..2025-09-30. The INJURIES VM's
  per-date path logs `"wrote empty_confirmed markers for 33 leagues"` — the prediction-tier list, not the 94-league
  api_football universe, so A_LEAGUE was never attempted or typed.

## Mechanism (three legs, all in instruments-service)

1. **Skip-as-present cells resolve to EMPTY, not captured** —
   `engine/orchestrator/sports_reference_core.py::emit_empty_gaps_for_entity` derives absence from `captured_league_ids`
   = leagues that yielded rows **in this run**. The per-fixture pre-fetch skip
   (`"N (entity, fixture_id) pairs already in existing per-league parquets — skipping api calls"`, e.g. 212/326 fixtures
   on 2025-11-29) means already-complete leagues yield zero new rows -> stamped `EXPECTED_NO_FIXTURE` (league in
   coverage map) or `EXPECTED_NO_PROVIDER_COVERAGE`. The docstring itself says ENF "would falsely imply the gap is
   restorable by a re-fetch" — here it falsely asserts a PERMANENT absence over data that EXISTS.
2. **Fetched-row league-map drop** — `engine/orchestrator/sports_fixtures.py::_build_fixture_league_map_from_gcs` yields
   ~35% of the day's canonical fixtures (115 of 326 on 2025-11-29); unmapped rows are dropped by the bare-path fallback
   in `sports_reference_fixtures.py` (~line 606). Candidate contributors to the short map (needs a repro to apportion):
   (a) the `af_league_id` fallback maps through `get_prediction_leagues()` (33 leagues) instead of
   `get_expected_leagues_for_source("api_football")` (94) — the SAME classification-filter mismatch class fixed for
   TEAMS/STANDINGS on 2026-07-13 (see `_fetch_teams_and_standings` docstring); (b) `_read_per_league_entity_df` defaults
   `max_results=100` per list call — truncation risk on busy dates; (c) fixture-id column-name drift (`af_fixture_id`
   expected by the map vs `fixture_id` carried by enrichment frames).
3. **INJURIES per-date league loop is prediction-tier-only** (33 of 94) — A_LEAGUE (and any other non-tier league with
   an expected INJURIES window) is never attempted; its EU rows stay blank-reason.

## Why the naive gate reads green (and must not be trusted)

Todo-9's gate query on the current index returns: per-fixture entities 0 pending-fetch, 0 blank-reason, 0 missing-cells;
every non-captured cell carries a typed reason. All three zeros are REAL — but the typed reasons are FALSE on 3,720
cells. Honest-absence integrity is the entire point of the manifest
(`codex/02-data/honest-absence-downstream-handling.md`); a green readout built on false `empty_confirmed` is a RED.

## Consequences / holds (operator-ruled chain interrupted)

- **Todo 9 (GW enrichment cleanliness) NOT flipped.**
- **2020+ full-enrichment fleet launch HELD** — same binary would replicate: ~400k calls with ~25-50% row-drop waste +
  false-ENF stamped across 2020->present (much harder to unwind later than to fix first). Live quota at hold time:
  48,729/300,000 used, 251,271 remaining (also note: live `limit_day=300k`; the "450k/day" registry note in P2a is stale
  vs the live read).
- **GW features recompute HELD** — enrichment parquet inputs are still materially incomplete (the 225,854 dropped rows
  span the window); recomputing now means a guaranteed second recompute after the fix + re-fetch.

## Suggested fix order (owner: data_engineering, instruments-service)

1. `emit_empty_gaps_for_entity`/orchestrator: on skip-as-present, `record_captured` from parquet-derived counts (or at
   minimum leave the cell's prior status untouched) so a no-op run cannot demote a present cell to empty. Never stamp
   `EXPECTED_NO_FIXTURE` on a `(date, league)` whose captured-FIXTURES count >= 1.
2. Fix the league map: 94-league mapping (not prediction-tier), lift/paginate the `max_results=100` cap, reconcile the
   fixture-id column name; convert the bare-path "drop" into `record_failed` so dropped rows can never be silent.
3. INJURIES loop -> `get_expected_leagues_for_source("api_football")`; type or attempt the A_LEAGUE September cells.
4. Re-run the SAME GW fleet post-fix (idempotent; presence-skip makes it cheap — only the dropped rows re-fetch), then
   re-run the content verification (parquet-presence cross, not the naive gate), then flip Todo 9 and resume the
   operator chain (2020+ fleet -> features recompute -> ML re-verify).
5. Coordinate manifest-row correction for the 3,720 false-empty cells with
   `sports_data_sources_canonical_completion_2026_07_13.md` (consolidator dedup-key NULL/`""` fix + honest-empty flip
   owner) — the fixed re-run's `record_captured` rows must WIN the dedup against today's false `empty_confirmed` rows,
   which is exactly the dedup-key semantics that plan owns.

## Progress log

- 2026-07-14 ~14:10Z: Filed by the gw-verify agent after the content verification above. No code changed; no manifest
  rows written; launches held; P2a plan updated in the same commit (session-31 entry + banner).
- 2026-07-14 ~16:30Z (fix-now agent, operator-mandated): **fix order items 1-3 fully shipped, item 5 (manifest repair)
  APPLIED.** Code: `instruments-service@0d9ffabd` (session 33, 3 legs) + `instruments-service@86cc71ff` (this agent —
  found two MORE live legs on the re-run fleet's own logs: (4) `reference_data/factory.py` pooled the api_football URDI
  adapter WITHOUT the date in the pool key, so a multi-date `--force` run pinned the FIRST date's fixture universe onto
  every later date — observed 91/91 URDI fetches all `date=2025-09-01` on the 14:46Z INJURIES VM → 90 false zero-fixture
  verdicts → ~2,970 false `EXPECTED_NO_FIXTURE` FIXTURES markers (33-league), masked at read time only by captured>empty
  precedence; (5) `process_zero_records.py::_zero_sports_empty_fixture_markers` was STILL prediction-tier-33 — fixed to
  the 94-league `get_expected_leagues_for_source("api_football")`. Plus an emit-boundary PRESENCE guard:
  `emit_empty_gaps_for_entity` now unions leagues whose per-league parquet EXISTS into the captured set (list-only GCS
  probe `_list_present_parquet_leagues`; fail-safe: probe failure → skip empty emission), closing the
  `redo_all`/zero-fixture-day paths the leg-1 fix could not reach. 7 regression tests incl. the 3 exact legs.
  **Repair**: `scripts/gw_false_empty_repair_2026_07_14.py` (`instruments-service@0fe2f17b`, recency-adjudication
  mechanics; snapshot-first `_index/snapshots/availability_index.20260714-161952/-162xxx…`): scope reproduced session-31
  exactly (1,848 captured-FIXTURES cells / 86 leagues / 91 days); object-probe adjudication over 5,726 empty_confirmed
  scope cells → **restamp-captured 4,170** (EVENTS 974 / LINEUPS 1,205 / STATS 1,082 / PLAYER_STATS 909; count > the
  13:39Z-snapshot 3,720 because the post-fix fleet had landed more parquets whose captured rows had not yet
  consolidated), **adjudicated-empty 1,556** (no attributable parquet — left as-is, listed in
  `gw_false_empty_adjudication.csv`), attempted_failed report-only 13. Per-VM shard
  `_index/per_vm/gw-false-empty-repair-20260714.parquet` written 16:29:06Z (4,170 captured rows, explicit `.write()`);
  consolidator cron-absorbs. Parquet-level `--cross` re-verify runs after the post-fix fleet completes (LINEUPS+STATS
  still RUNNING at 16:35Z) + ≥1 consolidator cycle.
- 2026-07-14 ~17:30Z (fix-now agent): **RESOLVED — verification GREEN, chain resumed.** Fleet completed 5/5
  `exit_code=0` (LINEUPS 16:5xZ, STATS 16:5xZ; 0 bare-path drops vs 225,854); repair shard cron-absorbed by 16:52:55Z;
  `--verify` 4,170/4,170 restamps read captured; `--cross` 16:54Z: false-empty 0 / phantom-captured 0 / untyped-blank 0
  across all 4 per-fixture entities over the 1,848 GW cells; INJURIES window EU 0 (was 30), the 30 A_LEAGUE cells typed
  `EXPECTED_PAUSED_LEAGUE`; independently matched by the peer verify script (`instruments-service@c06fbf1b`, same
  numbers, incl. its second-pass 50-cell residual repair). Todo 9 + the post-fix re-run todo flipped in P2a. Held
  launches RESUMED: GW features recompute relaunched 17:1xZ after fixing a launcher no-op defect (`--force` chain broken
  — `e2e-testing@b6b04b8` + `deployment-service@a79fa65`, see P2c banner); 2020+ enrichment fleet launched 17:24-17:27Z
  (5 SPOT VMs, tarball `@86cc71ff`, NO redo_all via the new `--skip-lock`, quota-budgeted 172,782 with 15% headroom —
  see P2a banner). Residuals routed: pre-2025-09 history false-empty restamp (widened repair window) noted in P2a
  session 36b; INJURIES 91 blank-league legacy failed rows → `sports_data_sources_canonical_completion_2026_07_13.md`.
- 2026-07-14 ~14:20Z (P2a session 32, data_engineering slot-3): independent corroboration of leg 2
  (`_build_fixture_league_map_from_gcs` truncation/mapping-gap). Retried FIXTURE_EVENTS/LINEUPS/STATS for the ~16
  residual `attempted_failed` (`CF11_MATCH_DAY_EMPTY_GUARANTEED_TYPE`) cells via direct narrow-date-range CLI calls
  (single entity, ≤10-day windows, run in-slot, not a VM). Every retry fetched real rows but logged the same
  `"<entity> bare-path fallback triggered ... no fixture-id column or empty af_fid->league map"` warning and skipped the
  manifest write. Confirms the mapping-gap bug reproduces on a narrow single-entity/single-digit-day range, not just the
  full 91-day fleet run — a fast, cheap repro surface for whoever picks up the `[CODE] P0` fix todo (no need to run the
  full fleet to test the fix). Also shipped a narrow, non-overlapping fix (`instruments-service@6a318ff4`) for a
  distinct 166-cell EU residual (genuinely fixture-less days, captured-FIXTURES count 0) — does not touch or mask any of
  the 3,720 false-empty cells this issue tracks. Full writeup:
  `sports_p2_history_apifootball_2015_to_present_2026_06_27.md` session 32.
