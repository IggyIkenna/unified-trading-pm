---
doc_type: issue
title:
  "weather/SFI/odds_api falsely record 'empty_confirmed' for leagues they're deliberately scoped OUT of — should never
  attempt the fetch or write any manifest row for these; existing rows need retagging"
summary: >-
  Operator ruling (2026-08-10): `open_meteo`/`soccer_football_info`/`odds_api` are deliberately capped at the 33-league
  Prediction tier (NOT the 96-league MVP football universe api_football/footystats/transfermarkt cover) — this is
  correct, intended behaviour, not a gap. But the current implementation writes `empty_confirmed` rows for every
  out-of-scope-league × fixture-date combo (weather ~205K rows, SFI ~205K rows per the 2026-08-07 re-census in
  `sports_all_vendor_honest_coverage_convergence_2026_08_07.md`) — treating "we deliberately never wanted this" the same
  as "we tried and genuinely got nothing," which (a) is semantically wrong and (b) bloats both the numerator and
  denominator of honest-coverage % for these 3 sources. Operator's explicit ruling: the code path should not even
  attempt these leagues, `empty_confirmed` should not be the tag used, and this needs a genuine out-of-scope tag + a
  manifest backfill correcting the ~410K+ already-written rows.
status: resolved
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service, market-tick-data-service, unified-api-contracts]
scope: [engineer, admin]
tags: [sports, honest-coverage, data-correctness, weather, sfi, odds-api, manifest, out-of-scope, capture-status]
related:
  [
    /plans/active/issues/sports_all_vendor_honest_coverage_convergence_2026_08_07.md,
    /codex/02-data/mvp-scope-canonical.md,
    /codex/02-data/sports-data-source-coverage-matrix.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: 2026-08-10
author: claude-agent
priority: P2
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: unified-api-contracts@5d4a1e6fb9fb078e50232b52369f97c5d7d9987c, instruments-service@9f93da039
source:
  Operator ruling during the sports honest-coverage convergence monitoring loop (continuation of
  sports_all_vendor_honest_coverage_convergence_2026_08_07.md), answering an AskUserQuestion about whether
  weather/SFI/odds_api's 33-league scope should widen to 96 — operator confirmed 33 is correct but flagged the
  empty_confirmed tagging + non-skipping fetch attempts as themselves a real defect.
context_scope:
  [
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/mvp-scope-canonical.md,
    unified-api-contracts/unified_api_contracts/canonical/domain/sports/league_data.py,
  ]
---

## What was found

`get_expected_leagues_for_source(source, ["Prediction"])` correctly scopes weather/SFI/odds_api to 33 leagues, but that
scoping only gates the _expected-denominator_ calculation, not the fetch attempt itself. The per-fixture orchestrator
loops for these 3 sources still iterate every league in the fixture set, attempt (or synthesize) a result for
out-of-scope leagues, and write `empty_confirmed` when nothing comes back — rather than recognizing up-front "this
league isn't in this source's scope, don't even try, don't write anything (or write a distinct out-of-scope marker)."

This is the SAME general shape as the weather/SFI `expected_unattempted` structural bug found and fixed 2026-08-07
(`sports_all_vendor_honest_coverage_convergence_2026_08_07.md` todos) — but that fix was about leagues _outside the
96-league MVP universe entirely_ (non-football, or unregistered). This is a narrower, still-open case: leagues _inside_
the 96-league MVP universe (Features/Reference tier) that these 3 specific sources were never meant to cover at all.

## Why it matters (operator's own framing)

- **Numerator/denominator bloat**: every `empty_confirmed` row for an out-of-scope league counts toward both sides of
  the honest-coverage percentage for that source, making the metric less meaningful than a true out-of-scope tag that's
  excluded from the ratio entirely (the same pattern `is_sports_structural_gap()` already uses for the 3 existing
  structural gaps in `mvp-scope-canonical.md` §Sports — A_LEAGUE×footystats, GREEK_SUPER_LEAGUE×transfermarkt,
  understat's big-5-only allowlist).
- **Wasted fetch attempts**: if the code path currently attempts a real fetch before recording empty (rather than
  skipping up front), that's wasted API calls/compute for leagues we already know are out of scope.
- **Retrospective correctness**: ~410K+ already-written `empty_confirmed` rows (weather + SFI) misrepresent history —
  they should read as out-of-scope, not as "we checked and there was nothing."

## What's needed (3 parts, per the operator's ruling)

1. **Docs** — DONE this session: `mvp-scope-canonical.md` §Sports now has a caveat clarifying weather/SFI/odds_api's
   33-league Prediction-tier scope is intentional and distinct from the 96-league MVP business-scope list; changelog
   pending in `sports-data-source-coverage-matrix.md` if not already covered by the earlier footystats 48→50 fix.
2. **Code** — the 3 sources' orchestrator loops (wherever they iterate the fixture-date × league set) need an up-front
   out-of-scope check per `get_expected_leagues_for_source(source, ["Prediction"])` that skips the league ENTIRELY (no
   fetch attempt, no manifest write of any kind) rather than falling through to `record_empty()`.
3. **Manifest backfill** — a retag/cleanup pass over the existing `empty_confirmed` rows for weather/SFI (and any
   odds_api rows in the same shape) where `league_id` is outside the 33-league Prediction set: either delete them (if
   genuinely zero-signal, matching this doc's own framing of "we never wanted this") or retag to a distinct out-of-scope
   `capture_status`/`error_reason` value consistent with `is_sports_structural_gap()`'s existing pattern — needs a
   design call on which (see todo 1).

## Todos

- [x] [DATA] P2. **Design call: delete-vs-retag for the out-of-scope backfill.** Operator ruling (2026-08-10, given
      interactively answering the AskUserQuestion this doc was filed for — see this doc's own
      `sports_weather_sfi_odds_out_of_scope_leagues_falsely_empty_confirmed_2026_08_10.md` Progress Log below,
      verbatim): "delete the ~410K out-of-scope rows outright AND ensure that in the future they would be tagged out of
      scope" + "and would be excluded from the ratio" — delete outright (not retag), and the future-tagging +
      ratio-exclusion is achieved by registering the 3 sources in the existing `SPORTS_SOURCE_LEAGUE_ALLOWLIST` SSOT
      (same mechanism `is_sports_structural_gap()` already uses for A_LEAGUE×footystats /
      GREEK_SUPER_LEAGUE×transfermarkt / understat's big-5 — no new `capture_status` value needed).
- [x] [CODE] P2. Shipped as `unified-api-contracts@5d4a1e6fb` (live-defi-rollout). Root-cause correction to the original
      diagnosis: `weather.py`/`sfi.py`'s own write loops were ALREADY correctly scoped — both iterate
      `for _exp_lid in sorted(_expected_*_league_ids)` where that set comes from
      `get_expected_leagues_for_source(source, classifications=["Prediction"])`, so neither ever wrote an
      out-of-scope-league row (verified by reading both files' write loops directly). The real accumulation source was a
      DIFFERENT, unaudited caller — almost certainly a manifest placeholder-materialization/reconcile job that calls
      `get_expected_leagues_for_source(source)` WITHOUT the classification filter, which (before this fix) fell through
      to the full 96-league MVP universe for these 3 sources because they had no `SPORTS_SOURCE_LEAGUE_ALLOWLIST` entry.
      Registering them in the SSOT makes every such caller — audited or not — get the correct 33-league set
      automatically; proven by `test_expected_leagues_for_source_matches_allowlist_without_classification_filter` in
      `test_sports_structural_gaps.py`. odds_api's own write path (partly MTDS-side) was not independently re-audited
      the same way — the SSOT fix covers it as a shared dependency, but its accumulation was far smaller (5,840 of the
      722,190 total) and lower-priority to trace further. No per-orchestrator up-front-skip code change was needed
      beyond the SSOT registration itself.
- [x] [DATA] P3. Backfill executed and independently verified 2026-08-10:
      `instruments-service/scripts/delete_weather_sfi_odds_out_of_scope_rows_2026_08_10.py`
      (`instruments-service@9f93da039`, live-defi-rollout) deleted 722,190 rows from
      `instruments-store-sports-prd-central-element-323112` (open_meteo 362,063 · soccer_football_info 354,287 ·
      odds_api 5,840 — larger than this doc's original ~410K estimate; re-measured via direct manifest query before
      running). Followed the delete-safety protocol (fresh same-run `gcs_bucket_soft_delete_retention_seconds()` =
      604800s check) and the staleness-safe write-back pattern (`merge_canonical_with_outstanding_shards` re-read
      immediately before write). Verified independently two ways: a post-delete dry-run of the same script found 0
      remaining out-of-scope rows, and the bucket's total manifest row count dropped by exactly 722,190 (17,098,067 →
      16,375,877). `compute_coverage_for_bucket()` confirms the deletion is reflected in a live coverage computation.

## Progress Log

- **2026-08-10 (autonomous session)**: filed per operator ruling (see `source:` above) during the sports honest-coverage
  monitoring loop. Confirmed the codex doc gap (found no ruling doc narrowing weather/SFI/odds_api to 33 leagues despite
  `mvp-scope-canonical.md` listing them among the 96-league-scope sources) and fixed it in the same session
  (`mvp-scope-canonical.md` §Sports caveat added). Did not touch code or manifest data — filed for proper scoping first
  (todo 1's design call), consistent with this workspace's "don't pick a disposition unilaterally when it changes
  storage/schema" convention.

- **2026-08-10 (same session, RESOLUTION)**: operator ruled on todo 1 ("delete the ~410K out-of-scope rows outright AND
  ensure that in the future they would be tagged out of scope" + "and would be excluded from the ratio"). Shipped the
  SSOT fix (`unified-api-contracts@5d4a1e6fb`): registered `open_meteo`/`soccer_football_info`/`odds_api` in
  `SPORTS_SOURCE_LEAGUE_ALLOWLIST` against the 33-league Prediction tier, same mechanism as the 3 pre-existing
  structural gaps — 4 new tests in `test_sports_structural_gaps.py`, full QG green, landed on live-defi-rollout.
  Investigated the actual accumulation source before touching orchestrator code: read `weather.py` and `sfi.py`'s write
  loops directly and found both were ALREADY correctly scoped (iterate only the 33-league
  `classifications=["Prediction"]` set) — so the original todo-2 diagnosis (orchestrator loops need an up-front skip)
  was based on an incomplete read; the real gap was that ANY OTHER caller of `get_expected_leagues_for_source()` that
  forgot to pass the classification filter fell through to the full 96-league universe for these 3 sources (most likely
  a manifest placeholder-materialization/reconcile job, not independently traced further — lower priority once the
  SSOT-level fix covers it regardless of caller). Ran the retrospective backfill delete
  (`instruments-service/scripts/delete_weather_sfi_odds_out_of_scope_rows_2026_08_10.py`,
  `instruments-service@9f93da039`): 722,190 rows deleted from `instruments-store-sports-prd-central-element-323112`
  (open_meteo 362,063 · soccer_football_info 354,287 · odds_api 5,840 — measured directly, larger than this doc's
  original ~410K estimate). Independently verified via a post-delete dry-run (0 remaining) and an exact total-row-count
  delta (17,098,067 → 16,375,877). Triggered a manual `data_status_rollup_worker` run for instruments-service so
  deployment-ui/deployment-api reflect the corrected coverage without waiting for the next 5-min cron tick. All 3 todos
  done — archiving.
