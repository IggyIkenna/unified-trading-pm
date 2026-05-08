---
title:
  "FIXTURES lookahead bias — post-match scores ride the same row as schedule, available_at uses arbitrary kickoff−7d
  heuristic"
created: 2026-05-08
author: ikenna
source:
  - instruments-service/instruments_service/engine/orchestrator.py:540-545
  - instruments-service/instruments_service/engine/orchestrator.py:3567,3571,3625
  - unified-api-contracts/unified_api_contracts/external/api_football/normalize.py:224-265
  - unified-api-contracts/unified_api_contracts/external/api_football/schemas.py:143-159
  - unified-api-contracts/unified_api_contracts/canonical/crosscutting/availability_semantics.py:61
  - unified-trading-library/unified_trading_library/availability_stamping.py:161-206
  - plans/active/api_football_minimal_flattening_removal_2026_05_07.plan.md
  - plans/active/sports_master_2026_05_07.plan.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# FIXTURES lookahead bias — post-match scores ride the same row as schedule

> **Severity**: P0 — data correctness violation in the canonical sports fixture truthset; affects every sports feature
> compute that joins FIXTURES with score columns. **Blast radius**: instruments-service (orchestrator) + UAC
> (api_football schema + availability_semantics) + every features-sports-service calculator that reads FIXTURES.parquet
> for outcome data. **Suggested owner**: `sports_master_2026_05_07.plan.md` Phase 3.

## What I found

Two compounded problems in the FIXTURES write path:

### Problem 1 — `kickoff − 7d` heuristic, not real announcement time

[orchestrator.py:540-545](../../../instruments-service/instruments_service/engine/orchestrator.py#L540-L545):

```python
if "timestamp" in fixture_df.columns:
    fixture_df["data_available_at"] = pd.to_datetime(
        fixture_df["timestamp"], utc=True, errors="coerce"
    ) - pd.Timedelta(days=7)
```

Same pattern repeated at
[orchestrator.py:3567, 3571, 3625](../../../instruments-service/instruments_service/engine/orchestrator.py#L3567). The
only justification is the comment `# PIT safety: scheduled fixtures published ~1 week before kickoff` — no audit, no
plan reference, no data showing api_football's actual announcement-to-kickoff distribution per league.

### Problem 2 — Post-match scores written at the same `available_at`

[normalize.py:224-265](../../../unified-api-contracts/unified_api_contracts/external/api_football/normalize.py#L224-L265)
writes `home_goals` / `away_goals` / `status="Match Finished"` / `winner_id` / halftime / fulltime / extratime / penalty
scores whenever the API returns them, with NO null-out for pre-match rows. After re-fetch (forward-poll covers fixtures
multiple times), the same fixture row gets `available_at = kickoff − 7d` but now carries the final score.

**A feature compute at T = kickoff − 1d would see the actual match result.** That's textbook lookahead.

`LookaheadBiasError` doesn't catch it — the feature timestamp comparison `available_at <= T − horizon` is satisfied; the
bias is inside the row, not at the join boundary.

### Sub-finding — api_football does NOT expose an announcement timestamp

[schemas.py:143-159](../../../unified-api-contracts/unified_api_contracts/external/api_football/schemas.py#L143-L159) —
full timestamp list in the raw response: `date` (kickoff ISO), `timestamp` (kickoff Unix epoch), `periods.first` /
`periods.second` (half-start times for played matches). No `announced_at`, `created_at`, `published_at`, `last_updated`,
`update`. We're not throwing data away — we genuinely don't have it from the source.

[availability_semantics.py:61](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/availability_semantics.py#L61)
declares `("sports", "FIXTURES"): "announced_at"` as the canonical stamping rule — UAC contract + source reality +
implementation are three layers in disagreement.

## Why it matters

- Every sports feature compute that reads FIXTURES with score columns silently gets lookahead. ML models trained on
  these features are confidently wrong.
- The `Live = batch` workspace principle requires identical schemas + timing semantics; live mode would never see
  post-match scores at `kickoff − 7d`, so batch parquets diverge from live in the most important direction
  (training-vs-serving skew).
- Per `LookaheadBiasError` semantics in CLAUDE.md, this is exactly the case the strict-mode check exists to prevent —
  but the check fires at join boundary, not row content, so it's blind here.
- The 7d heuristic is wrong both ways: lookahead bias for late-announced cup replays (we claim 7d but actual was 3d),
  unnecessarily-conservative clipping for EPL fixtures (announced months in advance, we clip to 7d losing ~50d+ of
  available_at fidelity).

## Recommended decision

Three-phase fix; Phase 1 is hard P0 stop-the-bleed:

### Phase 1 — Split FIXTURES into FIXTURES_SCHEDULE + FIXTURES_OUTCOMES

- New data_type `FIXTURES_SCHEDULE`: schedule columns only (kickoff, league, season, round, home_team, away_team, venue,
  referee). NO score / status / winner columns. `available_at` = empirical per-league announcement floor (Phase 2 input)
  or current 7d heuristic as interim.
- New data_type `FIXTURES_OUTCOMES`: outcome columns (home_score, away_score, status_long, status_short,
  status_elapsed_time, halftime/fulltime/extratime/penalty scores, winner_id) keyed by `fixture_id`. `available_at` =
  `match_end_time` per `stamp_available_at_post_match`
  ([availability_stamping.py:161-206](../../../unified-trading-library/unified_trading_library/availability_stamping.py#L161-L206)).
- Existing FIXTURES data_type deprecated; reader-side helpers migrate to join SCHEDULE + OUTCOMES on `fixture_id` with
  `available_at` from each side (downstream consumers naturally get correct timing).
- Migration: write a one-time reprocessor that splits the ~234k captured FIXTURES rows into the two new parquets. NO
  fallback reader after migration — delete the old FIXTURES path per workspace "manifest migration, NOT fallback" rule.

### Phase 2 — Empirical per-league announcement-floor audit

- Wire a first-seen logger into the api_football forward-poll: for every `(league_id, fixture_id)`, record
  `first_seen_at = poll_run_start` the first time the fixture appears.
- After 2-week observation window, per-league
  `announced_at_lead_floor_days = min over fixtures of (kickoff - first_seen_at)`. Sanity-clip to ≥ 1 day.
- Replace the global 7d in orchestrator.py:540-545 + 3567-3625 with per-league floor lookup.
- Costs zero additional API quota (forward-poll already runs daily).

### Phase 3 (optional) — Cross-source backfill for historical announced_at

- Check if footystats / soccer_football_info / transfermarkt expose a fixture creation/announcement timestamp.
- If yes: backfill historical FIXTURES_SCHEDULE rows' `available_at` via cross-source lookup.
- If no: apply the per-league empirical floor (from Phase 2) as the historical clip.

## Acceptance criteria

- [ ] FIXTURES_SCHEDULE parquet exists, NO score columns, `available_at` < kickoff for every row.
- [ ] FIXTURES_OUTCOMES parquet exists, score columns populated only for `status_short ∈ {"FT", "AET", "PEN"}`,
      `available_at >= match_end_time` for every row.
- [ ] Reader-side join helper ships in UTL.
- [ ] All features-sports-service calculators migrated off direct FIXTURES.parquet read.
- [ ] Old FIXTURES data_type deleted, no fallback.
- [ ] Per-league announcement-floor table populated in UAC after 2-week empirical audit.
- [ ] Workspace `LookaheadBiasError` strict-mode validates that no FIXTURES_OUTCOMES row has
      `available_at < match_end_time`.
- [ ] `Live = batch` invariant: live-mode FIXTURES_SCHEDULE + FIXTURES_OUTCOMES capture produces identical schemas to
      the batch reprocessor output.

## Open questions

- Does footystats / SFI / transfermarkt provide any fixture-announcement timestamp we could cross-reference for
  historical backfill? (Phase 3 input.)
- Should `available_at` for FIXTURES_SCHEDULE be per-league empirical OR a hardcoded 30d-conservative-default until
  empirical floor is computed? (Phase 1 → Phase 2 transition.)
- Are there existing features-sports-service calculators that already correctly handle "outcome data is post-match
  only," or do they all assume FIXTURES is single-row-per-fixture with all data available pre-kickoff? (Migration scope
  sizing.)
