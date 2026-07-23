---
doc_type: issue
title:
  FIXTURES postponed/cancelled status lifecycle — api_football misflags + reference-source-itself-missing-data +
  new-time fixture identity question
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
author: ikenna
source:
  - instruments-service/instruments_service/engine/orchestrator.py (FIXTURES write path)
  - unified-api-contracts/unified_api_contracts/external/api_football/normalize.py
  - unified-api-contracts/unified_api_contracts/external/api_football/schemas.py:143-159
  - {
      "operator-confirmed empirical observation (Harsh, 2026-05-08)":
        "I have seen in few matches where api football said cancelled and footystats gave me match data and then
        cross-checked it. the match was postponed and not cancelled. api football misflaggeed it as cancelled instead of
        postponed. and sometimes they dont have the data for a match that was played on original time (no cancel or
        postponed) but they failed to capture, and thats the really tricky one. as api-football is the reference, and
        reference is missing data",
    }
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# FIXTURES postponed/cancelled lifecycle — reference-source quality holes

> **Severity**: P1 — affects fixtures truthset accuracy; cascades to FIXTURE_STATS / ODDS / PREDICTIONS coverage %
> calculations and downstream feature compute that filters by `status_long`. **Blast radius**: instruments-service
> (orchestrator) + UAC (api_football normalize + status taxonomy) + features-sports-service consumers + manifest
> expected-universe enumerator. **Suggested owner**: `sports_master_2026_05_07.md` Phase 3 (fixture truthset recovery,
> currently 75% per master plan).

## What I found

Three distinct failure modes in the api_football FIXTURES capture lifecycle, all observed empirically:

### Failure 1 — api_football misflags postponed as cancelled

api_football's `status.long` field can return `"Match Cancelled"` for a fixture that was actually rescheduled
(postponed). Cross-checking against footystats reveals the match WAS played on a later date, with full match data. So:

- api_football `status_long = "Match Cancelled"` → captured FIXTURES row has `home_goals=NULL, away_goals=NULL`, no
  FIXTURE_STATS attempt.
- footystats has the match data → played on a new date, full stats available.
- Reference-source (api_football) is wrong; cross-source (footystats) is right.

If the orchestrator skips FIXTURE_STATS / ODDS for cancelled fixtures (correct behaviour for genuinely-cancelled), and
api_football misflags some postponed → cancelled, we silently lose downstream data for the rescheduled-and-played
fixtures.

### Failure 2 — Reference itself misses data for matches played on original time

api_football's data ingestion can simply fail to capture a fixture's stats / events / lineups / outcome despite the
match being played on its original kickoff time with no cancellation/postponement. The fixture row is captured (kickoff
time, teams, league) but `home_goals=NULL, away_goals=NULL, status_long="Not Started"` (or similar) persists past
`match_end_time`.

This is tricky because **api_football is the reference truthset for the workspace** — if reference is missing, our
coverage % is mathematically capped below 100%, and downstream consumers can't tell whether NULL scores mean "match not
yet played" vs "match played but reference dropped it." The available cross-source signal (footystats has match data,
understat has xG) can bridge the gap, but the orchestrator currently makes no cross-source verification attempt.

### Failure 3 — Postponed fixture identity: same fixture_id with new time, or new fixture_id?

Open question: when api_football reschedules a postponed fixture, does it:

- (a) Reuse the same `fixture_id` and update the `date` / `timestamp` to the new kickoff time?
- (b) Issue a new `fixture_id` for the rescheduled fixture and leave the old `fixture_id` as cancelled/abandoned?
- (c) Some hybrid (e.g. flagged as `status_long="Postponed"` then later updated in place)?

This determines:

- Whether our forward-poll naturally captures the new time (case a — overwrites in place) or needs explicit "new fixture
  for postponed-original" handling (case b).
- Whether the manifest gets one row per `(league, original_kickoff_date)` or two rows for the same fixture across two
  dates (case b).
- Whether downstream consumers see a single `available_at` per fixture or need to track the full lifecycle
  (`status_history`).

This needs empirical investigation against api_football's actual behaviour (replay a known postponed-then-rescheduled
fixture, observe what api_football returns over time).

## Why it matters

- **Coverage % truthfulness**: if 5% of fixtures are reference-missing-data despite being played, our FIXTURE_STATS /
  ODDS / PREDICTIONS coverage % is mathematically capped at 95% even with perfect downstream capture.
- **Feature compute correctness**: features that filter by `status_long="Match Finished"` skip rescheduled-and-played
  fixtures (because api_football still has them as "Match Cancelled"). Training set is biased toward fixtures
  api_football tracked correctly.
- **Manifest expected-universe**: when writegate Phase 3.D.5 Wave 3 ships the v2 expected-universe enumerator (catalog ×
  dates × data_types), the FIXTURES truthset becomes the canonical input — if FIXTURES is wrong about
  cancelled-vs-postponed, the entire downstream universe is wrong.
- **Live trading**: a misflagged-cancelled fixture means a live execution-service position-balance check might let the
  system trade odds on a "cancelled" fixture that's actually being played — significant operational risk.

## Recommended decision

Three workstreams; prioritise (1) before (2)+(3) because (1) is the cheapest cross-source check that catches Failures
1 + 2:

### Workstream 1 — Cross-source FIXTURES verification at orchestrator commit

After api_football captures FIXTURES for a `(league, date)`:

- For each fixture flagged `status_long ∈ {"Cancelled", "Postponed", "Abandoned", "Suspended", "TBD"}`:
  - Cross-check against footystats (and SFI / understat where available).
  - If cross-source has match data with non-null scores at the same `(home_team, away_team, original_kickoff_date)` or a
    nearby date (rescheduled): emit `FIXTURES_STATUS_DISCREPANCY` event with
    `{api_football_status, cross_source_status, cross_source, fixture_id, evidence_url_or_ref}`.
  - Flag the manifest row: `record_failed(reason=REFERENCE_STATUS_DISCREPANCY)` instead of `record_captured` (so
    downstream consumers know not to trust api_football's status here).
- For each fixture flagged `status_long="Match Finished"` but with `home_goals=NULL OR away_goals=NULL`:
  - Cross-check against cross-source.
  - If cross-source has scores: `record_failed(reason=REFERENCE_MISSING_OUTCOME_DATA, cross_source_evidence=...)`.
  - If cross-source also missing: leave as captured but with the NULL outcome columns honest.

This catches Failures 1 + 2 without requiring us to change the FIXTURES schema. Lifts api_football reference quality
from "trust blindly" to "trust + verify via cross-source."

### Workstream 2 — Empirical investigation of postponed-fixture identity

- Pick 3-5 known-postponed fixtures from prior seasons (e.g. EPL Covid-postponed matches Mar-Jun 2020).
- Re-fetch from api_football and observe: does the same `fixture_id` appear at both the original date and the
  rescheduled date? Does `status_long` evolve over time (`"Not Started" → "Postponed" → "Match Finished"`)?
- Document the empirical lifecycle in
  [`unified-trading-pm/codex/02-data/sports-fixtures-lifecycle.md`](/codex/02-data/sports-fixtures-lifecycle.md) (NEW
  codex doc).
- Wire orchestrator to handle the empirical case correctly (case a: re-fetch overwrites in place + clear status_history;
  case b: explicit new-fixture detection + linked manifest rows).

### Workstream 3 — Status taxonomy + downstream filter correctness

- Codify the api_football `status_long` closed-set in UAC `unified_api_contracts.canonical.domain.sports.fixture_status`
  (NEW SSOT). Currently the values are stringly-typed throughout the codebase.
- Map each status to a typed enum:
  `MatchStatus = {SCHEDULED, IN_PROGRESS, FINISHED, POSTPONED, CANCELLED, ABANDONED, SUSPENDED, TBD, REFERENCE_DISCREPANT}`.
- features-sports-service calculators that today filter by `status_long="Match Finished"` migrate to
  `MatchStatus.FINISHED` enum check. Calculators that previously ignored postponed/cancelled now must explicitly handle
  the rescheduled-and-played case (Workstream 1's `REFERENCE_DISCREPANT` flag).

## Acceptance criteria

- [ ] `FIXTURES_STATUS_DISCREPANCY` event type added to UAC + emitted by orchestrator on cross-source mismatch.
- [ ] At least 1 cross-source verifier (footystats) wired into orchestrator FIXTURES commit.
- [ ] `MatchStatus` typed enum SSOT in UAC; all features-sports-service consumers migrated.
- [ ] Empirical postponed-fixture lifecycle documented in codex.
- [ ] Manifest distinguishes `record_failed(reason=REFERENCE_STATUS_DISCREPANCY)` from `record_captured` for
      cross-source-flagged fixtures.
- [ ] Downstream feature compute test: ML training set excludes `MatchStatus.REFERENCE_DISCREPANT` rows OR explicitly
      opts in via cross-source-corrected outcome data.

## Open questions

- Does api_football re-emit corrections to historical fixture status (e.g. weeks later flip cancelled→finished if data
  team finds the match was actually played)? If so, how does our forward-poll detect the change?
- Is footystats authoritative enough to act as cross-source-of-truth, or do we need 2-of-3 quorum (footystats + SFI +
  understat)?
- What's the expected rate of cross-source disagreement? If 0.1%, the cross-source check is effectively a sanity gate;
  if 5%+, we have a fundamental reference quality problem requiring a primary-source change.
