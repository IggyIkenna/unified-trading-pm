---
doc_type: issue
title: "Sports honest-coverage gap closure — 2026-08-14"
status: open
priority: P1
assigned_vm: NA
execution_scope: local-only
tags: [sports, data-correctness, cross-cutting]
supersedes: NA
resolved_by:
summary:
  "Continuation of `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (now at its 1000-line hard cap — do not
  add to it, use this doc going forward for this thread). ..."
nature: process
asset_group: sports
stage: [meta]
repos: []
scope: [engineer, admin]
related: [sports_consolidated_closeout_2026_07_19]
parent_epic: sports_master
source: interactive-session
created: 2026-08-14
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

# Sports honest-coverage gap closure — 2026-08-14

Continuation of `sports_all_vendor_honest_coverage_convergence_2026_08_07.md` (now at its 1000-line hard cap — do not
add to it, use this doc going forward for this thread). Operator directive this session: "get to 100% sports IS and MTDS
for the relevant leagues for each data source" — i.e. actually close gaps, not just diagnose them. This doc tracks that
campaign.

## Live infra — check these before assuming anything is done

- **VM `mtds-backfill-odds-smallchunk-20260814`** (`asia-northeast1-c`, e2-highmem-4, SPOT) — launched 2026-08-14
  ~10:12Z to close the odds_api 278-day gap (`sports_odds_api_scattered_multiyear_gaps_2026_07_27.md`). 453 chunks
  total. Known risk: the still-unroot-caused silent-hang bug
  (`mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`) — IAP-SSH access to diagnose it live is fixed
  (see that doc), root cause is not. Check:
  `gcloud compute instances describe mtds-backfill-odds-smallchunk-20260814 --zone=asia-northeast1-c --format='value(status)'`;
  progress via `gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-odds-smallchunk-20260814/run.log`
  (read via UTL `download_from_storage`, never raw gsutil).
- **VM `weather-backfill-20260814-110817`** (e2-standard-8, SPOT) — launched to re-run 2024-01-03→2026-08-02 for the
  15,736 `attempted_failed` weather rows, all of which are leftover from an already-fixed bug
  (`instruments-service@a17e5dd0`, landed 2026-08-07 — the backfill that produced these rows ran BEFORE the fix, at
  12:02 UTC same day, fix landed 15:12 UTC, never re-run until now). **After this VM completes, run
  `bash deployment-service/scripts/vm/launch-sports-manifest-rescan-vm.sh`** — required to materialize empty_confirmed
  rows, per the launcher's own printed instruction.
- Both VMs confirmed alive and doing real work as of launch (not hung) — odds on chunk 1/453 LIGUE_1, weather correctly
  hitting-and-recovering from the (now-fixed) forecast-skip path.

## OpenMeteo API key — was invalid, now rotated (2026-08-14)

**Root cause of the "Previous Runs API failed" pattern in every weather log line**: the configured key (GSM secret
`open-meteo-api-key`, was version 1) was rejected outright by Open-Meteo
(`{"error":true,"reason":"The supplied API key is invalid."}` — confirmed via direct curl, not inferred). This blocked
ALL customer-tier calls (Previous Runs + Customer Archive), meaning **effectively zero rows in the weather dataset have
real T-24h/T-0 pre-match forecast data** — only actual/observed weather (via the free-tier archive fallback, which does
exist for that endpoint). This gap is invisible to capture_status coverage % — a row can be `captured` while its
forecast columns are structurally empty.

- **Fixed**: operator supplied a new key (`muJrislIpPsezh6M`, 5M calls/month). Verified live against both
  `customer-previous-runs-api.open-meteo.com` and `customer-archive-api.open-meteo.com` — both return real 200 data now.
  Rotated into GSM: `open-meteo-api-key` version 2 (now latest). `ApiKeyReloader` hot-reloads every 300s from Secret
  Manager (`unified-trading-library/unified_trading_library/api_key_reloader.py`) — **no service/VM restart needed**,
  including the already-running weather-backfill VM above.
- **Code fix written, NOT yet shipped** (see "in-flight" section below for why): added a free-tier fallback for the
  Previous Runs API call in `open_meteo.py` (mirrors the existing customer-archive→ free-archive fallback pattern
  already in the file). Confirmed live: free tier has real non-null forecast-run data for RECENT dates (tested
  2026-08-10, worked) but all-null for older dates (tested 2024-01-20) — a retention-window limit on the free tier, not
  a format/bug issue. This fallback only helps recent-date resilience against a future key outage; it does not
  retroactively fix historical data (that needed the valid key, which is now fixed separately).

## In-flight, not yet shipped (blocked on a concurrent peer session sharing this checkout)

- [ ] [SCRIPT] P1. **Ship the OpenMeteo Previous-Runs free-tier fallback** —
      `instruments-service/instruments_service/reference_data/adapters/sports/adapters/open_meteo.py`, currently
      uncommitted in slot-3's working tree (not lost — `git status` shows it modified, just not yet QG'd/shipped).
      Blocked because another session (general-purpose agent, working the FIXTURES_OUTCOMES fix below) has 5 files
      mid-edit in the SAME instruments-service checkout, and `quality-gates.sh` evaluates the whole tree — running it
      now would conflate the two changes' results. **Next session/tick: check `git status` in
      `.tabs/3/instruments-service` — once the other 5 files are gone (peer shipped) or confirmed abandoned, run
      `quality-gates.sh --no-fix` and
      `quickmerge.sh --agent --files 'instruments_service/reference_data/adapters/sports/adapters/open_meteo.py'`.**

- [ ] [SCRIPT] P1. **api_football FIXTURES_OUTCOMES/FIXTURES_SCHEDULE missing honest-absence classification** — real bug
      (NOT the SFI/weather league-scope bug class; league universe ~384 and the 2020-06-06 floor are both correctly
      applied). Writer (`sports_fixtures.py`) only writes `FIXTURES_OUTCOMES` when a match actually completed — a
      non-match day gets NOTHING written (no captured, no empty_confirmed). Enumerator's no-fixture calendar gate
      (`enumerate_expected_universe.py`, `_AF_FIXTURES_DATA_TYPE`) is hardcoded to the legacy `FIXTURES` entity name
      only, never fires for the two 2026-07-14 writer-split sibling entities. Net effect: `FIXTURES_OUTCOMES` shows
      94.2% `expected_unattempted` — almost certainly mostly genuine non-match days masquerading as gaps, not real
      failures; true coverage is likely much closer to `FIXTURES_SCHEDULE`'s own 83.3%-resolved once fixed. Also
      explains "I thought we backfilled everything" — `sports_af_full_entity_completion_2026_08_03.md`'s campaign never
      tracked these two split-off data_types at all. **Status as of last check: a general-purpose agent is implementing
      the writer+enumerator fix in this exact instruments-service checkout (files: `sports_fixtures.py`,
      `sports_reference_fixtures.py`, `sports_fixtures_daily_repoll.py`, `enumerate_expected_universe.py`, + a test
      file) — said "quickmerge in progress, couple minutes" but has NOT yet landed on origin as of this checkpoint
      (`git log origin/live-defi-rollout` doesn't show it). DO NOT duplicate this work — check origin log first; if
      genuinely abandoned/stalled, resume from the diagnosis above, don't re-derive it.** After the code fix lands: a
      dry-run reclassification pass for the ~820K-row historical backlog was requested (cross-reference against
      already-captured `FIXTURES_SCHEDULE` data, no live vendor calls needed) — apply is explicitly NOT authorized
      without reviewing the dry-run counts first.

- [ ] [SERVICE] P1. **api_football derived-entity architecture: enumerate-then-classify instead of gate-before-enumerate
      — confirmed real, ~94-97% denominator impact, NOT fixed yet.** Read-only audit completed (live queries against
      15,650,808-row prod manifest + code reads, no edits made). Two findings:

      **(a) Classification is 80-86% genuine, but a real live bug exists in the rest.** FIXTURE_EVENTS/STATS/
          LINEUPS/PLAYER_STATS empty_confirmed is dominated (80-86%) by `EXPECTED_NO_PROVIDER_COVERAGE` (correct —
          spot-checked: those leagues have ZERO captured rows ever, genuine MVP-scoping, ~88-96 leagues not 385).
          But `EXPECTED_NO_FIXTURE` (10-16% of empty_confirmed) contradicts real captured sibling data for the
          SAME (league,date) cell in **12,815 FIXTURE_STATS rows (9.76% of that reason), 6,618 PLAYER_STATS
          (7.47%), 2,971 FIXTURE_LINEUPS (2.37%), 1,234 FIXTURE_EVENTS (1.00%)** — 23,638 rows total, and 10,614 of
          the FIXTURE_STATS ones were freshly (re-)stamped in the last 14 days, i.e. still actively happening, not
          stale history. Example: `SUPERETTAN, 2020-06-27` — FIXTURES/FIXTURES_SCHEDULE/FIXTURES_OUTCOMES/
          FIXTURE_EVENTS/FIXTURE_LINEUPS all show real captured data (5 matches, 60 events, 216 lineup rows) for
          that exact cell, yet FIXTURE_STATS and PLAYER_STATS stamp it `empty_confirmed(EXPECTED_NO_FIXTURE)`.
          Root cause: `instruments_service/engine/orchestrator/sports_reference_core.py:275-317`
          (`_emit_empty_gap_for_league`) unconditionally stamps `EXPECTED_NO_FIXTURE` for any league absent from
          *that run's* `captured_league_ids`, with NO cross-check against sibling entities' captured status — the
          cross-check DOES exist elsewhere in the same file (`_close_stale_enrichment_expected_unattempted_cells`,
          lines 368-518, has 4 safety gates) but that sweep doesn't run in this live emission path.

          **(b) The operator's architectural point is CONFIRMED CORRECT, and broader than stated** — it applies to
          BOTH the day axis (`EXPECTED_NO_FIXTURE`) AND the (larger, 80-86%) league-scope axis
          (`EXPECTED_NO_PROVIDER_COVERAGE`). Confirmed: `enumerate_expected_universe.py:2450-2773`
          (`_enumerate_v2_sports`) iterates every league × every date for every sports data_type — the manifest
          atom itself has no `fixture_id` in its key (`_SPORTS_PRESENT_COLS = ["data_type","league_id","date"]`,
          line 158) for ANY sports entity. The one fixture-existence gate in this file
          (`_AfFixtureCalendar.is_no_fixture_day`, lines 2248-2398) is scoped only to the legacy `FIXTURES` entity
          — never extended to the 4 enrichment entities. **Checked for a legitimate reason this might be
          required** (not just validating the intuition): the only real consumer,
          `unified_api_contracts/canonical/domain/sports/feature_upstream.py:245-303` (`in_coverage()`), is a pure
          static lookup that never reads manifest row-presence at all — **no downstream consumer needs a
          materialized cell for a structurally-inapplicable league/day.** Also checked and REFUTED an assumed
          precedent: the "116-each FIXTURE_STATS/LINEUPS floor" from an earlier session finding is NOT a
          fixture-keyed model — `census_fixture_stats_lineups_widening_volume_2026_07_31.py` still computes needed
          work at (date,league_id) grain. **There is no existing fixture-keyed precedent in this codebase.**

          **Quantified impact of fixing**: restricting enumeration to real applicable (league,day) cells (gate
          BEFORE enumerate, using the already-existing `_AfFixtureCalendar` oracle + `get_entity_league_coverage`
          — no new oracle needs building) would shrink each entity's denominator by roughly **94-97%** — e.g.
          FIXTURE_EVENTS would drop from 877,974 rows to ~48,409 (40,582 captured + 4,996 attempted_failed + 2,831
          genuine expected_unattempted), flipping the headline reading from "94.49% empty" to effectively
          near-100%-resolved for what can actually exist. STANDINGS (46.62% empty_confirmed, 100%
          `EXPECTED_NO_PROVIDER_COVERAGE`) and TEAMS (18.67%, same reason) would shrink similarly if the same
          league-scope gate were applied to them.

          **NOT fixed this session** — this is a genuine design change (move the fixture/league-coverage check
          from post-hoc classification to pre-enumeration gating in both `enumerate_expected_universe.py` and
          `sports_reference_core.py`), bigger in scope than the FIXTURES_OUTCOMES classification-only fix above,
          and touches the same live daily-cron files that fix is already mid-editing — sequence AFTER that fix
          lands, don't run both in parallel on the same files. Needs operator sign-off on scope before starting
          (this changes the historical denominator materially, ~94-97% down, for 6 data_types at once).

- [ ] [SCRIPT] P1. **SFI: retry the 7 dates behind the 112 `attempted_failed` rows** — 2 confirmed-retriable root
      causes, no structural gap: 79 rows (`JSONDecodeError`, 6 dates in 2022-2023, all attempted 2026-08-07) were hit by
      a truncated-JSON bug already fixed same-session by `instruments-service@ecfc2749` (2026-08-10) — genuinely
      retriable now. 33 rows (`TimeoutError`, single date 2026-08-10) are a one-off transient slowness, also retriable.
      Retry mechanism (no new code needed):
      `python -m instruments_service     --operation instruments --mode batch --asset-group sports --sports-provider SOCCER_FOOTBALL_INFO     --sports-entity SFI_PROGRESSIVE_STATS --start-date <date> --end-date <date>`,
      run once per date (7 dates: 2022-01-23, 2022-02-20, 2022-03-02, 2023-03-05, 2023-04-22, 2023-12-03, 2026-08-10) —
      `DEPLOYMENT_ENV=prod` required (a first attempt silently hit the dev bucket without it). **A general-purpose agent
      was mid-test on the smallest date (2023-04-22, 3 leagues) as of this checkpoint — status unknown, not yet
      confirmed complete. Check its result before re-running; if abandoned, the 7-date retry list above is everything
      needed to finish this without re-deriving anything.**

## What NOT to re-derive — already answered this session

- Transfermarkt's `attempted_failed=8` is CORRECTLY classified, not a misclassification — a vendor 502 means "couldn't
  determine if data exists," which is categorically different from `empty_confirmed` ("vendor confirmed no data"). Do
  not convert these to empty_confirmed; the fix here is retrying against the vendor, which is `BLOCKED-UPSTREAM-OUTAGE`
  (external, confirmed via direct probe, not our bug).
- api_football's league scope (~384 leagues) and 2020-06-06 floor are BOTH correctly applied — confirmed live, not the
  SFI/weather bug class. Don't re-suspect denominator scope for `FIXTURES`/`FIXTURES_OUTCOMES`.
- The odds_api gap (278 days) is a genuine, already-diagnosed capture-pipeline gap, not a sentinel-gating or
  fixture-check problem — v2's real per-day fixture catalog is populated for essentially every day in the two largest
  gap windows; the gaps are downstream capture failures (see
  `mtds_odds_backfill_watchdog_kill_after_silent_hang_2026_08_08.md`).

## Session numbers snapshot (fresh pulls, not rollup-cached, ~11:00Z 2026-08-14 — will already be stale by

the time the VMs above finish; re-pull before quoting)

| Source                   |      Honest % | attempted_failed | Note                                                        |
| ------------------------ | ------------: | ---------------: | ----------------------------------------------------------- |
| footystats               |       100.00% |                0 | Genuinely clean                                             |
| understat                |       100.00% |                0 | Genuinely clean                                             |
| transfermarkt            |        99.98% |                8 | Vendor-blocked, correctly classified                        |
| SFI                      |        99.86% |              112 | Fix identified, retry in flight (see above)                 |
| weather                  |        84.68% |           15,736 | Backfill VM running (see above); credential fixed           |
| api_football (aggregate) |        89.50% |           21,833 | `FIXTURES_OUTCOMES` classification bug found, fix in flight |
| odds_api                 | 87.7%d/73.0%s |           32,583 | Backfill VM running; hang bug unroot-caused                 |

## Lessons this session (don't re-learn these)

- `gsutil`/`gcloud storage` CLI object ops are hard-blocked by a local hook — always
  `unified_trading_library.cloud_interface.{download_from_storage,gcs_describe_object,gcs_delete_object}`.
- A squash-merge promotion means `git merge-base --is-ancestor <original-sha> origin/main` gives a FALSE NEGATIVE even
  when the content is already on main — compare file content directly, or trust the promotion workflow's own
  `SKIP ... content-identical` log line over local ancestry checks.
- `rm -f`/`shred` are blocked as wipe-utilities by a local hook; use `unlink <single-file>` for verified single-file
  deletes.
- A live production monitoring/coverage-rollup dashboard endpoint can itself OOM a shared Cloud Run container on a broad
  unscoped query — always scope by source/date before hitting `/api/data-status/drilldown/*` broadly; the isolated-child
  memory guard (another session's fix) turns this into a controlled 503 now instead of a crash, but it's still
  expensive.
- Coverage % (captured+empty_confirmed)/total says nothing about whether the CONTENT of a captured row is complete — the
  OpenMeteo forecast-column gap was 100% invisible to every coverage number checked this session; it only surfaced from
  reading actual log lines.
