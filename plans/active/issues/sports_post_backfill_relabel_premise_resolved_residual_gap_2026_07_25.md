---
doc_type: issue
title:
  "sports_satellite_ao_dispatch_batch2-014's 789-league/120-date entity-coverage relabel premise is STALE (already
  resolved by intervening canonicalization work) — a much smaller, differently-shaped 33,905-row residual remains,
  needing its own targeted diagnosis, not the described migration"
summary: >-
  The dispatched todo (source: data_completion_sports_2026_07_24.md, itself dated from a 2026-06-22 finding) says the
  sports manifest carries ~1,027,396 `expected_unattempted` rows across 120 dates (2026-02-20→06-19) x 789 league_ids
  from a WEATHER-driven over-enumeration bug, and prescribes a relabel (no-coverage pairs -> expected_empty, GCS-backed
  cells -> captured) once 6 named backfill VMs go terminal. Live measurement today (2026-07-25) shows that finding is
  now STALE: only 33,905 expected_unattempted rows remain in that exact window, across 96 league_ids (not 789) - ALL 96
  of which are IN the current 94/96-league api_football in-universe set (zero out-of-universe leagues left in the
  window). The 30x reduction is a side effect of the intervening canonical-universe write-gate + dereg + canonicalize
  program (instruments-service@0345ffc and follow-ons, 2026-06-24 through 2026-07-21) - not something this todo's script
  needs to redo. The residual is dominated by odds_horizon_bucket (11,146, MDPS-owned) and
  FIXTURES_OUTCOMES/FIXTURES_SCHEDULE (9,265 + 9,256 = 18,521, the 2026-07-14+ split entities) - a structurally
  DIFFERENT shape (in-universe leagues with plausible genuine gaps, not out-of-universe phantoms) that a blind
  no-coverage->expected_empty relabel could mislabel as false-empty (the exact corruption class
  close_stale_enrichment_expected_unattempted_cells_2026_07_19.py's docstring warns against). Filed instead of running
  the stale-premise migration against a currently-live manifest writer.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer]
tags: [sports, honest-coverage, manifest, data-correctness, stale-finding, entity-coverage]
related:
  [
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency_2026_07_19.md,
  ]
created: 2026-07-25
priority: P2
parent_epic: sports_master
source:
  "Slot 9, data_engineering, 2026-07-25 — measured live against prod manifest while executing
  sports_satellite_ao_dispatch_batch2-014."
execution_scope: orchestrator-agent
drift_direction: advance-code
sequential: false
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# sports post-backfill entity-coverage relabel: premise resolved, residual needs its own diagnosis

## What I found

Dispatched task `sports_satellite_ao_dispatch_batch2-014` asked me to run a manifest relabel over "120 recent dates
(2026-02-20->06-19) x 789 leagues" per a 2026-06-22 finding (`data_completion_sports_2026_07_24.md` line 722-737): a
WEATHER-honest-coverage investigation found the sports `_index/availability_index.parquet` carried 1,027,396
`expected_unattempted` rows in that exact window across 789 league_ids (the enumerator over-expanded to the full raw
league universe instead of the ~57-94 leagues actually captured).

Before running the prescribed script, I measured the CURRENT manifest state directly (single read of
`_index/availability_index.parquet`, no new whole-corpus GCS walk):

- Total `expected_unattempted` rows workspace-wide: 249,338 (was ~1.03M+ in the window alone a month ago).
- Rows in the SAME 120-date window today: **33,905** (a ~30x reduction from the diagnosed 1,027,396).
- Distinct `league_id`s in that window subset today: **96** (not 789).
- **All 96 are in the current `get_expected_leagues_for_source("api_football")` in-universe set** — zero out-of-universe
  leagues remain in the window (the 94-league count is now 96 after CHINA_SUPER_LEAGUE/ RUSSIA_PREMIER_LEAGUE were added
  2026-07-21).
- Breakdown by `data_type` (top contributors): `odds_horizon_bucket` 11,146 (MDPS-owned, not IS); `FIXTURES_OUTCOMES`
  9,265; `FIXTURES_SCHEDULE` 9,256; `TEAMS` 1,758; the rest (WEATHER/STANDINGS/FIXTURES/SFI_PROGRESSIVE_STATS/
  INJURIES/FIXTURE_LINEUPS) 240 each; MATCHES/PREDICTIONS/ODDS 212 each; FIXTURE_STATS/FIXTURE_EVENTS 82 each.

This is NOT the bug the source finding described. The old bug's signature was "789 raw league_ids, mostly
out-of-universe, WEATHER-driven, ~1M rows." Today's residual signature is "96 in-universe league_ids, dominated by
`FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` (the 2026-07-14+ entity-split), 34k rows." The most plausible read: the
2026-07-14 FIXTURES-schema split introduced a NEW enumerator-vs-writer-timing mismatch for PRE-cutover historical dates
(the enumerator now expects `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` for every in-window date, but the writer only
started producing those entities going forward from the cutover, per `gcs_paths.py`'s own "NO legacy dual-write" note) —
not independently confirmed, flagged as the leading hypothesis for whoever picks this up.

**Additionally**: while measuring, I found a currently-RUNNING sports backfill VM (`af-backfill-20260725-002739`,
INJURIES/API_FOOTBALL/SPORTS, `days=1800` from 2018-01-01, currently ~2020-04) writing DIRECTLY to
`_index/availability_index.parquet` (no per-VM shard — the last-modified timestamp on the index was ~15s behind the VM's
own log tail at check time). This is unrelated to the 6 named VMs from the original 2026-06-22 finding (those ARE
confirmed terminal — 0 sports-tagged instances, running or otherwise, exist in the project today) but it means the
manifest is NOT currently in a safe drained state for an unprotected read-modify-write regardless of the premise
question above.

## Why it matters

- The dispatched todo's "Done when" (relabel over 120x789, re-measure honest-cov, record the delta) cannot honestly be
  satisfied as written — there is no 789-league phantom set left to relabel. Running the prescribed script against
  today's manifest would either no-op on 693 leagues that no longer have any rows in-window, or — worse — if adapted to
  match today's 96-league residual without re-diagnosing it, risks mislabeling genuine post-cutover pending-fetch gaps
  as `expected_empty` (false-absence corruption), exactly the failure mode
  `close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`'s docstring documents for a structurally similar
  case (a blind "no coverage" closer stamping `EXPECTED_NO_FIXTURE` over a real pending gap).
- Honest coverage is currently reading a manifest with a much healthier `expected_unattempted` count than the parent
  plan believes — the parent plan's "expect a large jump" framing for this todo is itself now stale and should be
  corrected so a future reader doesn't re-diagnose the same already-resolved bug.
- The residual 33,905-row gap (mostly `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE`) is real, current, and undiagnosed — it
  should not be silently dropped just because the original prescription no longer fits.

## Recommended decision

Not prescribing the fix (needs someone to confirm the FIXTURES-split-timing hypothesis against real data first). Shape
of the follow-up:

1. Confirm/refute whether `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE`'s 18,521 pre-cutover-window `expected_unattempted`
   rows are a genuine enumerator/writer timing mismatch (the split entities never had a writer to fill them before
   2026-07-14) vs. a real pending-fetch gap the writer should still be able to close on a targeted re-run.
2. If timing-mismatch: this is an honest-absence classification fix (the enumerator should not expect
   `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` for dates before the entity existed, OR — if the FIXTURES legacy entity's own
   row already proves the fixture happened — a provable-closure script mirroring
   `close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`'s safety pattern, not a blind relabel).
3. `odds_horizon_bucket` (11,146, MDPS-owned) and `TEAMS` (1,758) need their own separate check — different owning
   service/writer, not necessarily the same root cause.
4. Any future manifest read-modify-write against `_index/availability_index.parquet` MUST use CAS
   (`download_bytes_with_generation` + `conditional_upload_bytes(if_generation_match=...)`, mirroring
   `dereg_purge_24_leagues_2026_07_13.py`'s pattern) given a live sports backfill VM is confirmed actively writing this
   same file with no per-VM sharding.

## Todos

- [x] ✅ [DATA] P2. Confirm or refute the FIXTURES-split-timing hypothesis for the 18,521
      `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` `expected_unattempted` rows in the 2026-02-20->06-19 window (check whether
      the legacy `FIXTURES` entity's own row proves the fixture happened for a sample of these cells, and whether the
      writer has ever been asked to backfill the split entities for pre-cutover dates). (repo: instruments-service) —
      **REFUTED 2026-07-25T06:00Z (slot 11, data_engineering) — the true root cause is different and simpler than the
      timing-mismatch hypothesis.** Downloaded the current `_index/availability_index.parquet` (single read, no new
      corpus walk) and checked per-league status across the window date-by-date: `ALLSVENSKAN`'s `FIXTURES_SCHEDULE`
      rows alternate `captured` (real `instrument_count`, e.g. 2/3/4/5) on genuine match days and `expected_unattempted`
      (blank count) on days with no matches, INTERLEAVED throughout the whole window — not a clean pre/post-cutover date
      split as the hypothesis predicted. **The writer clearly ran on every date in range** (proven by real captured rows
      scattered across the full window, not clustered after 2026-07-14) — it just never writes ANYTHING (not even an
      empty-confirmation) on a day with zero real fixtures for that league. Cross-checked against the legacy `FIXTURES`
      entity (which DOES correctly mark `empty_confirmed`/`instrument_count=0` for the exact same off-days) — confirming
      these are genuinely zero-fixture days, not silently-dropped real data. **Root cause**: the
      `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` writer skips writing on a no-content day instead of calling the same
      expected-empty confirmation path the legacy `FIXTURES` writer uses — leaving the enumerator's original
      `expected_unattempted` seed permanently unresolved for every genuinely-empty day, not just pre-cutover ones.
      Verified at full scale, not just the one sample league: of all 9,265 unique `(date, league_id)` cells the split
      entities carry as `expected_unattempted` in this window, **8,937 (96.5%) have a legacy `FIXTURES` row confirming
      `empty_confirmed`/0 instruments** — provably safe honest-absence, not a real gap. The remaining 328 split into two
      genuinely different buckets: **88 have a legacy `FIXTURES` row showing `captured`** (real fixture data exists
      there but never reached the split entities — a genuine, narrow gap needing a targeted re-fetch, NOT a relabel);
      **240 have the legacy `FIXTURES` row ALSO `expected_unattempted`** (both entities pending — concentrated in
      `CHINA_SUPER_LEAGUE`/`RUSSIA_PREMIER_LEAGUE`, added to the in-universe set 2026-07-21, so this is most likely
      their own historical-window backfill lag, a separate/already-known gap class, not this issue).
- [x] [DATA] P2. ✅ Close the provably-closeable subset via a safety-pattern script (never a blind no-coverage relabel)
      — `instruments-service@5cd1cfb0` (`scripts/close_fixtures_split_expected_unattempted_cells_2026_07_25.py`),
      mirrors `close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`'s provable-closure discipline.
      **Correction to slot 11's 8,937/9,265 (96.5%) estimate above**: that count was measured on UNIQUE
      `(date, league_id)` pairs (deduped across both split entities — 9,265 checks out exactly as the union) and did NOT
      exclude `SOURCE_RETURNED_ZERO` as a mirror-safe FIXTURES reason. Re-measured per-row (both entities, 18,521 total
      stuck rows = 9,265 + 9,256) and found 1,171 of the 8,937 "provably safe" pairs actually carry
      `SOURCE_RETURNED_ZERO` as their legacy FIXTURES reason — mirroring that specific reason is NOT safe (the manifest
      writer's Phase-1 KEYSTONE honest-absence gate requires real `FetchEvidence` for `SOURCE_RETURNED_ZERO`, which a
      classification-only closer never has; a blind mirror would hard-crash `UnprovenHonestAbsenceError`, exactly the
      failure class `close_stale_enrichment_expected_unattempted_cells_2026_07_19.py`'s own docstring documents for the
      same reason code). **Final safe closure, applied to prod 2026-07-25T06:03Z**: 15,532 of 18,521 stuck rows closed
      (84%), reason distribution `EXPECTED_NO_FIXTURE` 6,762×2≈13,524 / `EXPECTED_POST_SEASON` 729×2≈1,458 /
      `EXPECTED_PRE_SEASON` 275×2≈550 (both entities). 2,989 correctly left untouched: 647×2 lack any FIXTURES proof
      (genuine pending-fetch gaps, incl. the 240-pair `CHINA_SUPER_LEAGUE`/`RUSSIA_PREMIER_LEAGUE` case already flagged
      below) + 1,171×2 excluded via the `SOURCE_RETURNED_ZERO` safety gate. **Verified by content, not the writer's own
      return** — a naive immediate re-read initially showed `delta=0` because the raw
      `_index/availability_index.parquet` is append-only between consolidator cycles (a `record_empty` write adds a NEW
      row rather than overwriting the prior `expected_unattempted` row for the same key — confirmed directly on
      `2026-02-20/FIXTURES_OUTCOMES/ALLSVENSKAN`, both rows present, disambiguated by `written_at`); fixed the
      verification to dedupe by latest `written_at` per `(date, data_type, league_id)` key before counting, which
      confirmed the exact expected delta (18,521→2,989, delta=15,532). No CAS-specific code needed —
      `ManifestWriter.flush()` already applies `if_generation_match` internally (`_writer_io.py:912`), the standard path
      every manifest write in this codebase uses; the issue doc's §4 CAS warning is satisfied by using the standard
      `ManifestWriter` API, not a custom mechanism. Did NOT touch the writer itself (the "fix the root cause so this
      stops re-accruing" follow-up stays open, flagged in todo 2's own text above, out of this todo's
      read-only-then-provable-write scope).
- [x] ✅ [DATA] P3. Separately check the `odds_horizon_bucket` (11,146 rows, MDPS-owned) and `TEAMS` (1,758 rows)
      residuals in the same window — different owning writer, likely a different root cause than the FIXTURES-split
      timing gap. (repo: market-tick-data-service for odds_horizon_bucket; instruments-service for TEAMS) — **DIAGNOSED
      2026-07-25T06:35Z (slot 2, data_engineering) — TWO further distinct root causes, neither matching the
      FIXTURES-split interleaved pattern.** Single manifest read (window-filtered, no new corpus walk).
      **`odds_horizon_bucket`** (`source=mdps_odds_horizon_bucket`, 18,419 total rows, 11,146 stuck — confirms the issue
      doc's count exactly): 96 distinct stuck league_ids, but the shape is LEAGUE-LEVEL, not date-level — **66 leagues
      (cups + lower tiers: `COPA_DEL_REY`, `CARABAO_CUP`, `BRASILEIRAO_SERIE_B`, `AUSTRIAN_2_LIGA`, etc.) have ZERO
      captured rows anywhere in the entire 120-day window** (every single date stuck, confirmed via a full per-date dump
      of a sample league) — this is a provider-coverage gap (the odds book simply doesn't list markets for these
      competitions), not a per-day timing artifact; textbook `EXPECTED_NO_PROVIDER_COVERAGE`, not a relabel of anything
      real. The other **30 leagues DO have real captures** (e.g. `EPL`, `BUNDESLIGA`, `ALLSVENSKAN`) with a smaller
      residual — cross-checked against the legacy `FIXTURES` entity for the identical `(date, league_id)`:
      **8,924/11,146 (80%) match a `FIXTURES` `empty_confirmed` row** (provably no fixture that day → safe to close,
      same discipline as `close_fixtures_split_expected_unattempted_cells_2026_07_25.py`); **1,982/11,146 (18%) match a
      `FIXTURES` `captured` row** (a REAL fixture existed that day but odds were never captured for it — a genuine
      capture gap, NOT safe to relabel, needs its own investigation into why); the remaining 240 are the already-known
      `CHINA_SUPER_LEAGUE`/`RUSSIA_PREMIER_LEAGUE` historical-lag case from todo 1. **`TEAMS`** (`source=api_football`,
      1,758 stuck, confirms the issue doc's count): only 2 leagues (`RUSSIA_PREMIER_LEAGUE`, `CHINA_SUPER_LEAGUE`, 120
      each — the same already-known newly-added-league lag) are FULLY absent; the other 33 partial leagues show a sharp
      CLIFF-EDGE pattern, not interleaved gaps — sampled `EREDIVISIE` in full: captured daily (`instrument_count=1`)
      every single date from `2026-02-20` through `2026-05-04`, then **zero captures for any date after that** (all 46
      remaining dates through `2026-06-19` stuck) — the TEAMS roster-capture job for these 33 leagues appears to have
      simply STOPPED running around `2026-05-04`/`05`, not a per-day writer-skip pattern like FIXTURES_OUTCOMES.
      **Recommendation (not fixed this pass — diagnosis-only per this todo's scope)**: three follow-ups, each
      independent: (1) `odds_horizon_bucket` — a closer script for the 8,924 provably-empty cells mirroring
      `close_fixtures_split_expected_unattempted_cells_2026_07_25.py` (repo: market-tick-data-service); (2) the 66
      no-coverage leagues need an `EXPECTED_NO_PROVIDER_COVERAGE`-class registry entry, not a relabel, so the enumerator
      stops re-seeding `expected_unattempted` for them (repo: market-tick-data-service); (3) the 1,982
      real-fixture-but-no-odds cells and the TEAMS 33-league capture-stall both need someone to check the ACTUAL capture
      job/cron for signs of failure around early May (repo: market-tick-data-service for odds; instruments-service for
      TEAMS) — this is a "did the job stop running" question, not a manifest-classification one, and out of a read-only
      diagnosis todo's scope to answer from manifest data alone.
- [ ] [DATA] P3. Close the provably-empty subset of `odds_horizon_bucket` `expected_unattempted` cells (8,924 of 11,146,
      cross-checked against legacy `FIXTURES` `empty_confirmed` for the identical `(date, league_id)` — diagnosed above
      by todo 3) via a safety-pattern closer script mirroring
      `close_fixtures_split_expected_unattempted_cells_2026_07_25.py`'s provable-closure discipline (never a blind
      relabel; exclude `SOURCE_RETURNED_ZERO` FIXTURES reasons the same way). (repo: market-tick-data-service)
- [x] [DATA] P3. ✅ Register ODDS_HORIZON_BUCKET league coverage — `unified-api-contracts@2a378fb2`. **Repo attribution
      was wrong in the original todo text** (said market-tick-data-service): the actual enumerator that seeds
      `expected_unattempted` for this data_type is `instruments-service/scripts/enumerate_expected_universe.py`'s
      `_enumerate_v2_sports`, which ALREADY consults a generic `get_entity_league_coverage(data_type)` SSOT
      (`unified_api_contracts.canonical.domain.sports.provider_league_ids`) for every sports data_type — but
      `ODDS_HORIZON_BUCKET` simply had no entry in `SPORTS_ENTITY_LEAGUE_COVERAGE`, defaulting to `None` ("all leagues
      expected"), the exact bug. **This is an allow-list mechanism, not an exclude-list** — I don't need the 66 "never
      covered" league_ids at all, only the (smaller) set that IS genuinely covered. Measured directly from a
      full-history manifest read (408,815 rows, no window restriction — a structural claim needs to hold across all
      time, not just the diagnosed window): 200,412 real captured rows across 63 DISTINCT raw `league_id` values.
      **Found and fixed a real data-quality gap in the raw data before trusting it**: those 63 raw values were NOT fully
      canonicalized — the same real league appears under 2-4 different forms (canonical UAC id, raw odds-api provider
      slug in 2 casings, e.g. `A_LEAGUE` / `A-LEAGUE` / `SOCCER_AUSTRALIA_ALEAGUE` / `soccer_australia_aleague` are all
      Australia's A-League). Resolved every raw value via `DEFAULT_CLASSIFICATION_REGISTRY`'s `odds_api_league_name`
      field (not taken verbatim) — 32 genuinely distinct canonical leagues, all major domestic top flights (EPL,
      LA_LIGA, BUNDESLIGA, SERIE_A, LIGUE_1, BRASILEIRAO, MLS, etc.), zero cups or lower-tier leagues, consistent with
      the todo's own framing. 9 raw values remained ambiguous after registry lookup (bare generic names like
      `PREMIER_LEAGUE`/`SUPERLIGA`/`SUPER_LEAGUE`) — verified via real football-domain knowledge that every plausible
      resolution of each ambiguous name maps to a league ALREADY in the 32-league set (e.g. `SUPERLIGA` → Denmark or
      Turkey, both already covered separately), so the 32-league allow-list is complete regardless of how they resolve.
      Added the data to `sports_league_entity_coverage.json` (mirrors the existing `PLAYER_VALUES` "observed coverage
      from manifest" pattern) + wired `SPORTS_ENTITY_LEAGUE_COVERAGE["ODDS_HORIZON_BUCKET"]` to read it — **zero
      enumerator code changes needed**, `get_entity_league_coverage` was already generically consulted for every
      data_type. Verified live: `COPA_DEL_REY`/`CARABAO_CUP`/`BRASILEIRAO_SERIE_B`/`AUSTRIAN_2_LIGA` (the todo's own
      examples) all correctly NOT covered; `EPL` etc. correctly covered. Added 22 new tests
      (`tests/unit/sports/test_entity_league_coverage.py`) covering the None-means-all-covered entities, the new
      allow-list membership (both directions), case-insensitivity, and a regression guard on the pre-existing Understat
      big-5 entry. `quality-gates.sh` green.
- [x] ✅ [DATA] P3. Investigate whether the `odds_horizon_bucket` and `TEAMS` capture jobs actually stopped running
      around early May 2026 for a subset of leagues (diagnosed above by todo 3: `TEAMS`'s `EREDIVISIE` captured daily
      through `2026-05-04` then zero captures for any date since; `odds_horizon_bucket` has 1,982 cells where a real
      fixture existed per `FIXTURES` but no odds were ever captured for it) — check the actual cron/job logs for errors
      or a silent stop around that date, not just the manifest's own record of the gap. (repo: market-tick-data-service
      for odds_horizon_bucket; instruments-service for TEAMS) — **DIAGNOSED 2026-07-25 (slot 8, data_engineering) —
      NEITHER job "silently stopped" due to a crash; both are explained by dated, git-verifiable mechanism changes. No
      live Cloud Logging access in this sandbox (gcloud creds invalid) — evidence trail is git commit history +
      Terraform provisioning history + script docstrings, which is conclusive on its own (dated commits pinpoint intent,
      not just absence).**

      **TEAMS (instruments-service), 33-league cliff-edge at ~2026-05-04**: this is an INTENTIONAL cadence
          retirement, not a failure. `scripts/migrate_teams_cadence_2026_05_07.py` (instruments-service@53c67c43,
          2026-05-07) documents the C.11 audit finding (rosters change per-season, not daily — daily writes were an
          ~830x denominator inflation) and flips legacy daily `TEAMS` rows to `empty_confirmed`/
          `EXPECTED_REFDATA_CADENCE_CHANGE` per a UAC `SchemaContract.cadence="per_season"` declaration shipped the same
          day (unified-api-contracts@e12af89). The script's own docstring states the per-season REPLACEMENT writer
          ("C.11 Unit 2") was DEFERRED, not shipped alongside the retirement — confirmed still incomplete as of this
          check: `plans/epics/sports_master.md`'s "Trigger-date backfill script" + "VM fleet run for trigger-date
          backfill" todos are both still `- [ ]` unchecked, and no commit touches
          `engine/orchestrator/sports_reference.py` after 2026-05-07. So the diagnosed window's `expected_unattempted`
          residual for these 33 leagues is the accurate, expected shape of an intentionally-paused writer awaiting its
          replacement — not a hidden outage. Compounding but separate: the season-boundary-gated periodic dispatcher
          that's meant to eventually replace the daily writer (`sports_trigger_periodic.py`, introduced
          deployment-service@d9652cd 2026-04-21) had its OWN independent bug — the CLI never passed `--backend cloud`,
          so it silently defaulted to `backend="local"` which cannot exec in the Cloud-Run-only image, meaning EVERY
          periodic "reference"-tier dispatch attempt (TEAMS included) silently no-op'd from 2026-04-21 until fixed
          2026-07-08 (deployment-service@bb880b6, verified against prod: `last_run.reference` advanced from a stale
          `2026-06-24` to live). This bug is already fixed and post-dates the diagnosed window's end (06-19), so it adds
          color but doesn't change the verdict for this window.

          **Separately** (not the cliff-edge pattern, a different TEAMS root cause already fully resolved before this
          check — confirms rather than reopens it): the "2 fully-absent leagues" thread from todo 3
          (`RUSSIA_PREMIER_LEAGUE`/`CHINA_SUPER_LEAGUE`) is the tail of an unrelated, already-fixed enumeration bug —
          `_fetch_teams_and_standings` looped the 33-league `get_prediction_leagues()` filter instead of the full
          94-league `get_expected_leagues_for_source("api_football")` denominator, so 61 of 94 leagues got ZERO TEAMS
          captures ever (instruments-service@0d2ea24f, fixed 2026-07-13). A same-day backfill
          (`scripts/backfill_teams_61_leagues_2026_07_13.py`) closed 162,032/162,032 cells for 86 of those 94 leagues (8
          confirmed-honest zero-roster cup competitions); `RUSSIA_PREMIER_LEAGUE`/`CHINA_SUPER_LEAGUE` were added to the
          in-universe set 2026-07-21, 8 days AFTER this backfill ran, so they were never in its scope — exactly the
          "already-known newly-added-league lag" todo 3 flagged, no new action needed.

          **odds_horizon_bucket (market-data-processing-service, NOT market-tick-data-service — the writer is
          `market-data-processing-service/scripts/reprocess_sports_odds.py`)**: there was NEVER a recurring scheduled
          driver for this job anywhere in the fleet before 2026-07-14 — confirmed via
          `deployment-service/terraform/gcp/mdps_odds_horizon_scheduler.tf`'s own header, which states plainly this job's
          "only production path has been manual one-off VM launches"
          (`deployment-service/scripts/vm/launch-mdps-sports-bucket-vm.sh`, itself headed "Pass K of
          sports_predictions_e2e_2026_05_05" — i.e. a sequence of ad-hoc passes, not a cadence). So "did the job stop
          running around early May" doesn't apply as posed — there was no regular cadence to stop; the 1,982 real-fixture
          /no-odds cells in the diagnosed window are gaps BETWEEN irregular manual passes, consistent with the script's
          own comment history. A genuine daily Cloud Scheduler cron
          (`uts-prod-mdps-odds-horizon-bucket-daily`, `15 1 * * *` UTC) was provisioned 2026-07-14
          (deployment-service@de117f5) — this class of gap should not recur going forward for new dates; the historical
          residual in the diagnosed window is exactly what this issue doc's own still-open closer-script todo (above)
          already exists to remediate — the coverage-registry half of that remediation shipped separately
          (`unified-api-contracts@2a378fb2`, todo above) while this diagnosis was in flight.

          **No new issue doc filed** — findings confirm/refine already-tracked open work (`sports_master.md`'s TEAMS
          trigger-date backfill todos; this doc's own odds_horizon_bucket closer-script todo above) rather than
          surfacing anything requiring new tracking.

## Progress Log

- **2026-07-25 (slot 8, data_engineering)**: Dispatched the final open todo (investigate whether `odds_horizon_bucket` /
  `TEAMS` capture jobs actually stopped running around early May 2026). No live gcloud/Cloud Logging access in this
  sandbox — used git commit history + Terraform provisioning history + script docstrings as the evidence trail instead
  (dated, verifiable, and conclusive on its own). Findings: neither job "crashed" or silently stopped. `TEAMS`'s
  33-league cliff-edge is an intentional cadence retirement (instruments-service@53c67c43, 2026-05-07, daily→per-season
  per the C.11 audit) whose replacement writer is still only partially delivered (`sports_master.md`'s
  trigger-date-backfill todos remain open) — plus a since-fixed, unrelated scheduler wiring bug
  (deployment-service@bb880b6, fixed 2026-07-08) that would have blocked season-boundary dispatch attempts in the same
  window regardless. The separate "2 fully-absent leagues" thread is the tail of an already-fixed, fully-backfilled
  61-league enumeration bug (instruments-service@0d2ea24f, fixed + backfilled 2026-07-13) — no new action needed there.
  `odds_horizon_bucket` (writer lives in market-data-processing-service, not MTDS) never had ANY recurring scheduler
  before 2026-07-14 (`deployment-service/terraform/gcp/mdps_odds_horizon_scheduler.tf`'s own header confirms this) — its
  only path was irregular manual VM launches, so the 1,982-cell gap is inter-pass gaps, not a stopped job; a real daily
  cron now exists going forward. No new issue doc filed — this confirms/refines already-tracked open work rather than
  surfacing new findings. Reconciled against a concurrent peer edit (slot-3, `unified-api-contracts@2a378fb2`) that
  landed the `ODDS_HORIZON_BUCKET` coverage-registry todo while this diagnosis was in flight — merge conflict resolved
  by hand, keeping both todos' completed work. 5 of 6 todos in this issue doc are now resolved; only the
  `odds_horizon_bucket` provably-empty-subset closer-script todo remains open.

- **2026-07-25T06:35Z (slot 2, data_engineering)**: Dispatched todo 3 (diagnose `odds_horizon_bucket` + `TEAMS`
  residuals). Single manifest read (window-filtered, no new corpus walk), no writes. Found two DIFFERENT root causes
  from both each other and from todo 1's FIXTURES-split finding: `odds_horizon_bucket` is a league-level
  provider-coverage gap for 66 cup/lower-tier leagues (zero captures ever) plus a smaller date-level gap for 30 covered
  leagues (80% provably closeable via `FIXTURES` cross-check, 18% are real fixtures with a genuine missing-odds gap);
  `TEAMS` is a cliff-edge capture-job stall for 33 leagues (ran daily through `2026-05-04`, zero captures since). Filed
  3 new follow-up todos (closer script, coverage-registry fix, cron/job investigation) rather than leaving the
  recommendations as prose only. Did not attempt any fix — diagnosis was this todo's full scope.

- **2026-07-25 (slot 9, data_engineering)**: Filed while executing `sports_satellite_ao_dispatch_batch2-014`. Measured
  the current manifest directly (single read, no new corpus walk) before running the prescribed script; found the
  original 789-league/1M-row premise resolved (30x reduction, 0 out-of-universe leagues left in-window) and a much
  smaller, structurally different 33,905-row residual that needs its own diagnosis rather than the prescribed relabel.
  Also confirmed a live sports backfill VM (`af-backfill-20260725-002739`) is currently writing the same manifest file
  unprotected — any future write against it needs CAS. Not fixing the residual in this pass (would be unplanned scope on
  top of an already-resolved-premise task); filed as this new, correctly-scoped issue instead.
