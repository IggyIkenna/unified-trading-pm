---
doc_type: issue
title:
  features-service sports travel_calculator's home-side venue-coordinate lookup silently fails almost universally —
  home_travel_distance_km ~100% NaN and cumulative-travel columns hardcoded to 0.0 across the ENTIRE corpus, historical
  AND current-live
summary: >
  While verifying `sports_travel_calculator_tz_aware_kickoff_crash_2026_07_14.md` Todo 2 (identify + gap-fill pre-fix
  all-NaN cumulative-travel date-ranges — now that the parent plan's Todo 1 2015→present compute finished today), found
  the tz-crash-specific all-NaN pattern is NOT present anywhere sampled (0/7,641 rows across 3 independent samples) —
  but discovered a much bigger, separate, still-live defect instead: `home_travel_distance_km` is NaN in ~100% of
  sampled rows, `away_travel_distance_km` is NaN in 86-98.5%, and ALL FIVE cumulative-travel columns
  (`away_cumulative_travel_30d`/`home_cumulative_travel_30d`/`away_travel_per_game_30d`/`home_travel_per_game_30d`/
  `travel_fatigue_ratio`) are **uniformly, exactly 0.0** — never NaN, never nonzero — in every one of 7,641 rows sampled
  across 2017-2026 AND the freshest available day (2026-07-16, current fully-patched code). This means the travel
  feature family is effectively non-functional corpus-wide and still is today, not just in historical backfill data.
status: open
nature: notes
asset_group: [sports]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [sports, features, data-correctness, travel-calculator, venue-coords, silent-failure, honest-absence]
related:
  [
    plans/active/issues/sports_travel_calculator_tz_aware_kickoff_crash_2026_07_14.md,
    plans/active/issues/sports_venue_id_numeric_coercion_data_loss_2026_07_13.md,
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-17
parent_epic: sports_master
priority: P1
source:
  sports_travel_calculator_tz_aware_kickoff_crash-001 dispatch, slot 4, 2026-07-17 (Todo 2 verification — real-data
  content sampling across pre-fix bug-window + broad-history + latest-live dates)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-17
locked_by:
resolved_by:
---

# features-service sports travel_calculator's home venue-coordinate lookup never resolves

## What I found

While doing the real gap-fill-identification work for `sports_travel_calculator_tz_aware_kickoff_crash_2026_07_14.md`
Todo 2 (now unblocked — the parent plan's Todo 1 2015→present compute finished today, 2026-07-17, at 4216/4216 =
100.0%), I read the sports features availability manifest
(`gs://features-sports-prd-central-element-323112/_index/availability_index.parquet`, one file, single-walk) to find
`DERIVED_FEATURES`/`captured` shards written before the tz-crash fix (`features-service@d878f11a`,
2026-07-14T12:20:33Z), then downloaded and content-checked the actual `feature_group=derived_features/features.parquet`
files for the 5 `TRAVEL_COLUMNS` cumulative-travel fields the tz-crash bug was reported to silently NaN.

**Three independent samples, all real GCS data (real content, not manifest metadata):**

1. **Broad stratified sample**: 46 dates spread 2017-2026 (every ~40th of the 1,845 pre-fix candidate dates), 622 shard
   files, 2,021 rows (GCS mtimes confirmed 2026-07-12/13, genuinely pre-fix).
2. **Exact documented bug-window sample**: the 111 unique dates whose manifest `written_at` falls inside
   2026-07-14T08:56–12:20:33Z — the EXACT window the original issue doc's 8,648 "Travel calc failed" log-warning count
   came from (`features-sports-sports-20260714-085703`'s run.log). 1,558 shard files, 5,620 rows. GCS `ls -l` mtimes
   cross-checked directly against a 5-date sub-sample and confirmed to match the manifest exactly (e.g.
   `day=2019-10-06/league=103/…features.parquet` → `2026-07-14T09:08:27Z`), so these are genuinely the shards written
   during the documented crash window, never overwritten since.
3. **Freshest available day**: `day=2026-07-16/league=253` (yesterday, computed with the CURRENT fully-patched code,
   post both `d878f11a` and `81036512`).

**Result across all three (7,641 rows total): the tz-crash's specific "all 5 travel columns NaN via exception" pattern
occurs ZERO times.** `df[TRAVEL_COLUMNS].isna().all(axis=1).sum()` == 0 in every sample, including the exact
crash-window one. So Todo 2's premise (the parent issue doc's own recommended decision: "identifiable via `--force`
re-run scoped to dates whose parquet cumulative-travel columns are all-NaN") does not hold — there is nothing to
gap-fill for THAT specific bug.

**But a different, much bigger pattern was found instead, in the SAME data:**

```
home_travel_distance_km       NaN in ~100.0% of rows  (2,021/2,021 and 5,620/5,620)
away_travel_distance_km       NaN in  86-98.5% of rows
home_cumulative_travel_30d    == 0.0 in 100% of rows (never NaN, never nonzero)
away_cumulative_travel_30d    == 0.0 in 100% of rows (never NaN, never nonzero)
away_travel_per_game_30d      == 0.0 in 100% of rows
home_travel_per_game_30d      == 0.0 in 100% of rows
travel_fatigue_ratio          == 0.0 in 100% of rows
```

This is NOT a code-defect-NaN like the tz-crash — it's a **constant, hardcoded-looking 0.0** for the cumulative fields,
which per `travel_calculator.py`'s own logic (read in full at `features_service/sports/calculators/travel_calculator.py`
current HEAD) only happens when the `except` branch is NOT hit (cumulative fields are explicitly set inside the
`if match_date is not None` success branch, lines 265-288) — meaning the code runs to completion, but
`_compute_cumulative_travel()` (lines 97-144) is returning `(0.0, …)` almost every time via its
`if home_coords is None: return (0.0, len(recent))` branch (or the earlier `(0.0, 0)` no-recent-games branch) — i.e.
`_get_team_home_venue_coords()` (lines 61-94) is failing to resolve a team's home venue coordinates from
`fixtures_history` nearly universally, for BOTH the away-team lookup (used for `away_cumulative_travel_30d` /
`away_travel_distance_km`) and — even more consistently (100% vs 86-98.5%) — the home-team's OWN lookup (used for
`home_travel_distance_km` / `home_cumulative_travel_30d`), which is the more surprising half: a team playing at home
today failing to find ITS OWN historical home fixtures in the same league's `completed` history is the harder case to
explain as "genuinely no data" (the team, by construction, IS a participant in this league).

**Confirmed this is not a stale/historical-only artifact**: the freshest available day (2026-07-16, computed with
current post-both-fixes code) shows the identical pattern — this is a live, ongoing defect, not something resolved by
either the July-14 tz fix or the July-13 venue_id-normalization fix
(`sports_venue_id_numeric_coercion_data_loss_2026_07_13.md`, itself already `status: resolved`; its fix,
`features-service@a9684e27`, landed 2026-07-13T20:31:40Z — BEFORE every shard I sampled — so this is not a regression of
that already-fixed bug, it's a separate, still-open one).

**Not yet root-caused to an exact line** — ran out of budget on this dispatch (Todo 2's actual scope) to trace further,
but the strongest lead: `_get_team_home_venue_coords()` filters
`fixtures_history[fixtures_history["home_team_id"] == team_id]` then joins to `venues` on `venue_id`. `fixtures_history`
here is the `completed` DataFrame built by `_filter_completed_before()`
(`features_service/sports/exporters/derived_features_helpers.py:365`), which is fed in per-`(date, league)` batch by
`_run_phase4_history_calculators` → `compute_travel_batch(target_fixtures, venues, completed)`
(`features_service/sports/exporters/derived_new_calculators.py:129-134`). Worth checking first: (a) whether `completed`
is scoped too narrowly (e.g. missing most of a season's prior home fixtures for the league being processed at export
time — would explain near-100% failure for both home AND away lookups equally, and the small away-lookup success
minority as noise/edge fixtures); (b) whether `venues["venue_id"]` and `fixtures_history["venue_id"]` still mismatch in
dtype/normalization on some SUBTLER axis than the one `a9684e27` already fixed (e.g. whitespace/casing on the canonical
code, or a stale `venues` snapshot missing newer venue codes); (c) instrumenting `_get_team_home_venue_coords` with a
one-off debug script against a single real `(date, league)` batch's actual `fixtures_history`/`venues` inputs (not just
the OUTPUT parquet, which is all I inspected here) would show directly which branch is failing and why.

## Why it matters

- Violates the data_engineering craft's north-star #1 (no silent placeholders) — `_compute_cumulative_travel` returning
  `0.0` for a genuinely-missing-data case is indistinguishable in the output parquet from a team that legitimately had
  zero travel in the last 30 days (e.g. two home games in a row). Every downstream ML consumer of
  `TRAVEL_COLUMNS`/`away_cumulative_travel_30d` etc. is training on a corpus-wide constant-zero feature dressed up as a
  real signal — worse than an honest NaN, since NaN at least signals "missing" to a model/imputer while a constant 0.0
  silently degrades feature usefulness without any visible signal.
- This is corpus-wide (sampled 2017-2026 and the freshest live day) and STILL HAPPENING as of yesterday (2026-07-16) —
  it is not fixed by either of the two related fixes that already landed this week (`d878f11a` tz-crash, `a9684e27`
  venue_id-normalization).
- `sports_p2_features_history_to_ml_ready_2026_06_27.md`'s own ML-readiness gate ("every NaN traces to a typed upstream
  honest-absence") would not even catch this specific defect, since the affected columns are NOT NaN — they're a
  plausible-looking 0.0 — meaning this failure mode can survive an NaN-focused honest-absence audit undetected. Worth
  flagging to that plan's gate design too (does not block THIS issue doc, just a fyi for whoever reads `related`).

## Recommended decision

**NOT fixing inline** — this needs its own root-cause investigation (I traced the mechanism but not the exact broken
line; the fix likely touches `_get_team_home_venue_coords` and/or its caller's `completed`/`venues` scoping, and any fix
must be verified against real `(date, league)` batch inputs, not just output parquets, before being trusted). Filing as
its own issue doc per the findings-triage HARD RULE (big finding: data-correctness, corpus-wide, cross-cutting the ML
feature surface) rather than absorbing into `sports_travel_calculator_tz_aware_kickoff_crash_2026_07_14.md`'s scope
(that issue doc is specifically about the tz-crash, already fixed and verified-absent per this doc's own evidence).

## Todos

- [x] ✅ [DATA] P1. **Root-cause `_get_team_home_venue_coords` / `_compute_cumulative_travel` returning `(0.0, …)`
      almost universally** — instrument a debug run against one real `(date, league)` batch's actual `fixtures_history`
      (`completed`) and `venues` DataFrames (not just the output parquet) to see exactly which branch fails: empty
      `completed`, empty `home_fixtures` after the `home_team_id` filter, or an unsuccessful `venue_id` join against
      `venues`. Check `_filter_completed_before`'s scoping
      (`features_service/sports/exporters/     derived_features_helpers.py:365`) and the caller's `completed`
      construction (`derived_new_calculators.py:80-134`) as the leading candidates. (repo: features-service) — **Found
      the `completed` was empty, not just the home_team_id filter**: `read_historical_fixtures()`
      (`features_service/sports/data/gcs_reader.py:644`) is what supplies the `historical` fixtures that
      `derived_features_exporter.export_derived_features()` combines with today's fixtures to build `fixtures_all` →
      `completed` (`_filter_completed_before`). Its internal `_list_historical_fixture_blob_paths` matched blob paths
      against a literal `"/entity=fixtures/fixtures.parquet"` substring, but every real `FIXTURES` shard uses the
      per-league subpartition layout (`entity=fixtures/league={L}/fixtures.parquet` —
      `unified_api_contracts.canonical.domain.sports.gcs_paths.SportsPathLayout.PER_DAY_PER_LEAGUE`), which that
      substring never matches — **`read_historical_fixtures` always returned 0 rows, for every date, always**. This
      means `completed`/`fixtures_history` was unconditionally empty in production regardless of the
      `home_team_id`/`team_id` dtype question — so slot-8's str/int fix (`features-service@6efefde2`, Todo 2 below),
      while a real and necessary correctness fix, would have been **inert in production** without this one also landing:
      `_get_team_home_venue_coords`'s `if fixtures_history.empty: return None` short-circuits before the `home_team_id`
      comparison ever runs. Confirmed empirically: called
      `read_historical_fixtures('2024-06-01',     lookback_days=400)` directly against real GCS pre-fix → 0 rows; same
      call post-fix → 1,385 real rows with real `kickoff_utc`/`home_team_id`/`venue_id` values. The unscoped
      `list_blobs(bucket, prefix="sports_reference/by_date/     day=")` walk (no year/date bound) also timed out at
      corpus scale on its own (a whole-corpus GCS walk on every call) — fixed both issues together in
      `features-service@9923b0d8` (shipped same dispatch as this investigation): matched the real per-league (and
      bare-legacy) path shape, and rescoped the listing to iterate per spanned calendar year instead of one unbounded
      walk. Verified end-to-end against real GCS post-both-fixes (this fix + slot-8's `6efefde2`, both now on
      `live-defi-rollout`): `away_travel_distance_km` populated ~67% of a 21-fixture sample with real varying km values
      (257-2715km range), `home_travel_distance_km` populated ~81% (mostly legitimate 0.0 for true home fixtures), and
      at least one genuine nonzero `home_cumulative_travel_30d` observed in-sample — the full mechanism now works
      end-to-end, not just in isolated unit tests. (repo: features-service)
- [x] ✅ [DATA] P1. **Fix the root cause** found above, restoring genuine (non-zero, non-hardcoded) travel-distance and
      cumulative-travel computation for fixtures where the data genuinely exists — and make the genuinely-missing case
      (no data available) surface as an honest NaN, not a silent `0.0`, per
      `codex/02-data/honest-absence-downstream-handling.md`. Add/extend a unit test using a real fixture+venue fixture
      pair with actual travel history spanning >0km, asserting a nonzero cumulative-travel result — the existing test
      suite evidently didn't catch this (all current tests must be using either trivial single-fixture cases or
      synthetic data that happens to avoid the broken path). (repo: features-service) — features-service@6efefde2. Root
      cause: `_get_team_home_venue_coords`/`_compute_cumulative_travel` compared `fixtures_history["home_team_id"]`
      (stringified in production via `gcs_normalizers._to_str_id`) against an `int()`-coerced `team_id` in
      `compute_travel_batch` — an int-vs-str dtype mismatch that made the lookup fail almost universally. Fixed by
      comparing as strings (no longer force-casting to `int()`) and by returning honest `NaN` (not `0.0`) from
      `_compute_cumulative_travel` when a resolvable game window exists but the team's home venue can't be found. Added
      a production-shaped regression test (stringified ids, real >0km travel history) asserting a nonzero
      cumulative-travel result, plus a str/int-mismatch regression test on `_get_team_home_venue_coords` directly. Full
      sports unit suite + whole-service `quality-gates.sh` green (17,641 passed, 0 failed; sentinel `d74f96a5`/HEAD
      `6efefde2` match). Todo 1 (root-cause investigation) was dispatched separately to slot 4 — not flipped here; this
      fix subsumes that investigation's findings but the other slot's task record is left for it to close on its own
      thread.
- [ ] [DATA] P2. **After the fix ships**, gap-fill re-run the full 2015→present sports history for `derived_features`
      with `--force` (this is now the REAL gap-fill this corpus needs — much larger in scope than the tz-crash gap-fill
      this doc's sibling issue doc originally anticipated) and re-verify via the same content-sampling method used here
      (sample real parquet rows for nonzero cumulative-travel values, not just NaN-absence) that the fix actually
      produces real, varying travel data before closing this out. (repo: features-service)

## Progress Log

### 2026-07-17T13:5xZ — data_engineering slot-4 (filed this issue doc; found + fixed a SECOND, independent root cause that slot-7/slot-8's team_id fix does not cover; reconciled + shipped alongside their concurrent fix)

Filed this issue doc originally (see `created`/`source` above) while verifying the sibling
`sports_travel_calculator_tz_aware_kickoff_crash_2026_07_14.md`'s Todo 2. Picked up Todo 1 (root-cause) myself on the
very next dispatch of this doc.

**Found a second, independent root cause** that slot-7/slot-8's `home_team_id` str/int fix (`features-service@6efefde2`)
does not touch: `read_historical_fixtures()` (`features_service/sports/data/gcs_reader.py:644`) — the function that
supplies `completed`/`fixtures_history` to `compute_travel_batch` in the real production pipeline
(`derived_features_exporter.export_derived_features()` → `run_new_calculators()` → `_run_phase4_history_calculators()`)
— **always returned 0 rows, for every date**, because its internal `_list_historical_fixture_blob_paths` matched blob
paths against a literal `"/entity=fixtures/fixtures.parquet"` substring that never matches the real
per-league-subpartitioned layout every FIXTURES shard actually uses (`entity=fixtures/league={L}/fixtures.parquet`).
Confirmed directly against real GCS: pre-fix, `read_historical_fixtures` returned 0 rows for a real date with a 400-day
lookback; post-fix, 1,385 real rows. The unscoped `list_blobs(prefix="sports_reference/by_date/day=")` walk (no date
bound at all) also timed out on its own at corpus scale — a genuine whole-corpus GCS walk on every single call.

**This means slot-8's team_id fix alone would have been inert in production**: with `fixtures_history` always empty,
`_get_team_home_venue_coords`'s `if fixtures_history.empty: return None` short-circuits before the `home_team_id`
comparison this fix corrects ever runs. Both fixes are independently necessary and complementary, not redundant — I
confirmed this isn't a hypothetical concern by testing the exact sequence (path bug present + team_id bug present → 0
rows; path bug fixed + team_id bug still present → real rows but still-wrong 0.0 travel distances; both fixed → real
nonzero travel distances end-to-end against live GCS data).

Fixed in `features-service@9923b0d8`: corrected the path-matching (per-league + bare-legacy layout support) and rescoped
the listing to iterate per spanned calendar year instead of one unbounded whole-corpus walk. Full `quality-gates.sh`
green (17,647 passed, sentinel-verified). Hit `BEHIND_DIVERGED_CONFLICT` on first `quickmerge` attempt — slot-8's
`6efefde2` had landed on `travel_calculator.py`/its test file concurrently; reconciled by rebasing and taking slot-8's
version of those two files verbatim (their fix is objectively superior — honest NaN instead of a silent 0.0 for the
genuinely-unresolvable case — so no value in shipping a competing/lesser version), keeping only my non-overlapping
`gcs_reader.py` + new test file changes. Re-ran full QG on the reconciled HEAD (clean), shipped via quickmerge. Verified
end-to-end post-both-fixes against real GCS: `away_travel_distance_km` populated ~67% of a 21-fixture sample with real
varying km values (257–2715km), `home_travel_distance_km` populated ~81% (mostly legitimate 0.0 for true home fixtures),
at least one genuine nonzero `home_cumulative_travel_30d` observed.

Flipped Todo 1 above with this finding. Todo 2 (the team_id fix itself) was already closed by slot-8 — not re-flipping,
already `[x]`. Todo 3 (the actual gap-fill re-run) is genuinely not attempted this dispatch — per slot-8's cost analysis
above (~140+ VM-hours, operator-decision scale), consistent with the sibling elo issue doc's gap-fill precedent.
`/done`.

### 2026-07-17T13:2xZ — data_engineering slot-7 (dispatched Todo 3 gap-fill; found the fix already shipped by a peer)

Dispatched this issue doc's Todo 3 (gap-fill), but its own wording ("after the fix ships") meant Todo 1/Todo 2 were the
real blocking prerequisites, and both were still `- [ ]` at dispatch time. Rather than gap-fill against still-broken
code, root-caused the bug myself first (matching the craft's data-correctness north-star): confirmed via direct repro
that `compute_travel_batch` casts `home_team_id`/`away_team_id` to `int()`, but `fixtures_history`'s
`home_team_id`/`away_team_id` columns are string dtype in production (`gcs_normalizers._stringify_id_columns`/
`_to_str_id`) — `int == str` is always `False` in pandas, so `_get_team_home_venue_coords`'s team-fixture lookup failed
almost universally, and `_compute_cumulative_travel`'s `(0.0, …)` fallback made this look like a plausible constant-zero
feature instead of an honest absence. Verified with a direct repro (`team_id=int(12345)` → `None`,
`team_id=str('12345')` → resolves correctly) and wrote regression tests, 2 of which were confirmed to fail against the
pre-fix source via `git stash` isolation. Committed a fix (`features-service@d57c4165`, local only) and ran it through
full `quality-gates.sh` (17,642 passed, 0 failed) — but on `quickmerge --agent`, hit `BEHIND_DIVERGED_CONFLICT`: slot-8
had independently root-caused and fixed the **exact same bug** in parallel (`features-service@6efefde2`, already
shipped + this doc's Todo 2 already flipped by that slot).

**Compared the two fixes rather than forcing a merge**: slot-8's version is a strict superset of mine — same core
str-normalization + drop-the-`int()`-cast fix, PLUS a correctness improvement I missed: `_compute_cumulative_travel`
returning `(0.0, len(recent))` when games happened but the team's home venue still can't be resolved is ITSELF a silent
non-honest-absence case (a real games-happened-but-unresolvable-venue stretch should read as NaN, not 0.0, per
`codex/02-data/honest-absence-downstream-handling.md` — the same north-star violation this whole issue doc is about).
Discarded my redundant local commit (`git reset --keep origin/live-defi-rollout` — safe, working tree was clean, no
foreign WIP at risk) and adopted slot-8's shipped fix instead of shipping a competing/lesser version. Confirmed
`features-service@6efefde2` passes the full `tests/sports/unit/calculators/test_travel_calculator.py` suite (43 passed)
in my own worktree post-pull.

**Todo 1 left untouched** — slot-8's own Progress Log entry notes it was dispatched separately to slot-4 and left for
that slot's thread to close; not mine to flip.

**Todo 3 (gap-fill) NOT attempted this dispatch.** It's now genuinely unblocked (the fix has shipped), but re-running
the full 2015→present `derived_features` history with `--force` is a significant infra-cost decision — same magnitude as
the sibling elo issue doc's gap-fill, which needed its own audit-then-cost-estimate split (P2b/P2c) rather than a blind
full re-run, per the data-correctness HARD RULE's "surface the cost decision, don't default to a full re-run" guidance.
Recommend the same pattern here: a cheap single-walk audit sampling real `derived_features` parquets post-`6efefde2` for
genuinely-nonzero travel columns (confirming the fix's real-world effect) BEFORE committing to a multi-VM 2015→present
recompute — not attempted this dispatch (out of scope for a single 1h-estimated task). `/skip-current-task` after this —
the assigned Todo 3 checkbox cannot be honestly flipped without doing the actual gap-fill, and Todo 2 (what I actually
worked) was already closed by slot-8 first.

### 2026-07-17T13:4xZ — data_engineering slot-8 (re-dispatched Todo 3; measured real per-date recompute cost; confirmed VM-fleet scale, did not launch)

Re-dispatched this issue doc's Todo 3 after slot-7's skip. Rather than re-derive slot-7's conclusion from scratch,
measured the actual per-date compute cost directly (same methodology the sibling elo issue doc's gap-fill used):

```
GCP_PROJECT_ID=central-element-323112 python3 -m features_service.sports --operation compute --mode batch \
  --asset-group SPORTS --date 2018-03-18 --league COPA_ARGENTINA --force
```

First attempt under a 200s timeout did **not** complete (SIGTERM-killed mid-calculator-stack, hadn't yet reached
`team_derived`/`travel`) — matching the elo gap-fill's own 180s-timeout non-completion on the identical `(date, league)`
pair. Re-ran with a generous 550s timeout to get a real data point: **completed in ~278s** (13:36:32→13:41:10Z) for the
full date (488 fixtures across all leagues that specific date actually had reference data for — note `COPA_ARGENTINA`
itself turned out to have zero fixtures on 2018-03-18 despite being the elo doc's own example pair, so this run wrote
`expected_unattempted` for that specific league filter and produced no sample row to content-check; recompute cost
scales with the DATE's full reference-data read + 400-day historical-fixtures lookback, not the league filter, so the
~278s figure is still the right per-date unit cost).

**Scale conclusion, consistent with the elo sibling issue's finding**: ~278s/date × ~1,844+ distinct affected dates
(this bug's near-universal ~86-100% failure rate makes its affected-date count at least as large as the elo bug's
1,844-date figure, likely larger) ≈ 140+ hours of serial single-worker compute — squarely VM-fleet scale, matching Todo
1's original 4-10 VM `fss-backfill-vm-*` precedent, not something executable from a worker dispatch.

**Consolidation finding worth flagging to the operator decision**: `run_new_calculators` computes ALL Phase-4
calculators (elo, travel, manager, formation, european_fatigue, …) together in one pass per `(date, league)` and writes
one row — so a single full-corpus `--force` re-run now (both this fix, `features-service@6efefde2`, and the sibling elo
fix, `features-service@04274b6a`, have already shipped) would satisfy **both** gap-fills simultaneously. The operator
does not need two separate VM-fleet launches; one full 2015→present recompute against current HEAD covers both. Worth
noting explicitly on whichever `/blocked` decision request the operator ultimately acts on first (elo's or this one) so
the other isn't re-launched redundantly afterward.

**Did not launch a VM fleet autonomously** and did not file a second, duplicate `/blocked` (an equivalent VM-fleet
sign-off request is already open from the elo issue doc's own gap-fill dispatch) — added this cost data + the
consolidation insight to this doc instead, and `/skip-current-task`'d. **Todo 3 checkbox NOT flipped** — the actual
gap-fill has not happened.
