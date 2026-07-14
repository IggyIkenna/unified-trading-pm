---
doc_type: issue
title:
  features-service sports travel_calculator silently NaN'd travel/cumulative-travel columns for every tz-aware
  kickoff_utc fixture — fixed, backfill re-run of affected dates still owed
summary: >
  While re-verifying sports_p2_features_history_to_ml_ready-002 (Todo 3, still structurally BLOCKED-PREREQ on Todo 1's
  in-progress 2015→present compute), found `travel_calculator.compute_travel_batch` (features-service) raising
  `ValueError: Cannot pass a datetime or Timestamp with tzinfo with the tz parameter` on
  `pd.Timestamp(fixture["kickoff_utc"], tz="UTC")` whenever `kickoff_utc` arrives already tz-aware. The per-fixture
  shard-level try/except (by design, for genuine failure isolation) caught it and silently defaulted
  `away_cumulative_travel_30d` / `home_cumulative_travel_30d` / `*_travel_per_game_30d` / `travel_fatigue_ratio` to NaN
  — 8,648 occurrences on ONE of the 3 currently-running gap-fill VMs (`features-sports-sports-20260714-085703`) within
  ~3h of live backfill traffic. This is a code-defect NaN, not an honest-absence NaN (the data existed and was
  computable) — it just wasn't typed/counted as a failure anywhere. Fixed in features-service@d878f11a (switched to
  `pd.to_datetime(..., utc=True, errors="coerce")`, matching the tz-naive/tz-aware normalization already used for
  `fixtures_history` two lines above). The 3 VMs currently running the P2c 2015→present backfill are on a pre-fix
  tarball snapshot and will keep producing these silent NaNs on every tz-aware-kickoff fixture until relaunched or until
  a targeted gap-fill re-run picks up the fix.
status: open
nature: notes
asset_group: [sports]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [sports, features, data-correctness, travel-calculator, honest-absence, timezone, silent-failure]
related:
  [
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    plans/active/issues/sports_venue_id_numeric_coercion_data_loss_2026_07_13.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-14
parent_epic: sports_master
priority: P2
source: sports_p2_features_history_to_ml_ready-002 dispatch, slot 12, 2026-07-14 (Todo 3 re-verify, log-tail dive)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-14
locked_by:
resolved_by:
---

# features-service sports travel_calculator silent NaN on tz-aware kickoff_utc

## What I found

`features_service/sports/calculators/travel_calculator.py:258` (pre-fix):

```python
match_date = pd.Timestamp(cast(object, fixture["kickoff_utc"]), tz="UTC")
```

`pd.Timestamp(value, tz="UTC")` raises
`ValueError: Cannot pass a datetime or Timestamp with tzinfo with the tz parameter. Use tz_convert instead.` whenever
`value` already carries tzinfo. `compute_travel_batch`'s per-fixture loop wraps the whole body in
`except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, ArithmeticError, OSError):` (correct
shard-level-isolation design — no `raise` inside a per-fixture loop), which caught this and logged
`"Travel calc failed for fixture %s, defaulting to NaN"` before defaulting the whole row's `TRAVEL_COLUMNS` to NaN.

Confirmed live-scale via the run.log of one of the 3 currently-running P2c backfill VMs
(`features-sports-sports-20260714-085703`, `gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`):
**8,648** "Travel calc failed" warnings between 09:11:47Z and 11:52:57Z (~2h41m) — every one the identical `ValueError`
traceback, i.e. every fixture whose `kickoff_utc` happened to already be tz-aware on read. The other 2 VMs (`-085642`,
`-085726`) were mid different date ranges at inspection time and not directly sampled for this specific warning, but run
the identical code path.

Two of `TRAVEL_COLUMNS`' six fields are gated behind this one `pd.Timestamp` call
(`away_cumulative_travel_30d`/`home_cumulative_travel_30d`/`away_travel_per_game_30d`/`home_travel_per_game_30d`/
`travel_fatigue_ratio` — everything past the point-to-point `*_travel_distance_km`/`*_is_long_travel`/
`travel_distance_diff` fields, which compute fine before this line). So this is a partial-row degradation, not a
whole-row blank — but for every affected fixture the 5 cumulative-travel columns are code-defect NaN, not honest
upstream absence, and nothing distinguishes the two in the written parquet (both are just NaN).

## Why it matters

- Violates the data_engineering craft's north-star #1 (no silent placeholders — a computable value silently degraded to
  NaN by a code bug must not be indistinguishable from a genuine honest-absence NaN).
- At 8,648 occurrences on one VM in <3h, this affected a large fraction of the 2015→present sports backfill
  `sports_p2_features_history_to_ml_ready-002` (Todo 1) is currently running — likely tens of thousands of fixtures
  fleet-wide by the time that backfill completes, unless re-run with the fix.
- Directly relevant to this plan's Todo 2 gate ("every NaN traces to a typed upstream honest-absence") — these NaNs do
  NOT trace to honest absence, they trace to a code defect. Todo 2 already found the Todo-2 gate failing for other
  reasons (compute not yet complete) and is slated for re-run once Todo 1 finishes; that re-run should also sample
  cumulative-travel columns specifically, now that the code-side cause is fixed.

## Recommended decision

Fix now (small, clear, root-caused) — **done**, shipped features-service@d878f11a. Remaining question is operational,
not a design decision: the 3 already-running P2c backfill VMs are on a pre-fix snapshot and won't pick up the fix
without a relaunch or a targeted gap-fill re-run. Given the backfill is >55% through history and healthy (per this
plan's extensive Progress Log), killing and relaunching the live VMs now to force-adopt the fix is a bigger, riskier
action than this finding warrants on its own — recommend letting the current pass finish, then gap-filling the affected
date-ranges (identifiable via `--force` re-run scoped to dates whose parquet cumulative-travel columns are all-NaN, once
the fix is in the deployed tarball) as a normal follow-up backfill pass.

## Todos

- [x] [DATA] P1. **Fix the tz-handling bug** in `travel_calculator.compute_travel_batch` — replace
      `pd.Timestamp(fixture["kickoff_utc"], tz="UTC")` with
      `pd.to_datetime(fixture["kickoff_utc"], utc=True,     errors="coerce")` (matches the fixtures_history
      normalization 2 lines above). (repo: features-service) — features-service@d878f11a, QG green, shipped via
      quickmerge --agent 2026-07-14.
- [ ] [DATA] P2. **After `sports_p2_features_history_to_ml_ready-002` Todo 1 (2015→present compute) reaches
      completion**, identify date-ranges computed BEFORE features-service@d878f11a landed (2026-07-14) whose
      `sports_features/by_date/day=*/feature_group=*` cumulative-travel columns
      (`away_cumulative_travel_30d`/`home_cumulative_travel_30d`/`*_travel_per_game_30d`/`travel_fatigue_ratio`) are
      suspiciously all-NaN for dates with tz-aware `kickoff_utc` fixtures, and gap-fill re-run those with `--force` on
      the fixed code. (repo: features-service)
- [x] ✅ [DATA] P3. **Audit whether other sports calculators share the same
      `pd.Timestamp(value, tz="UTC")`-on-possibly-aware-value pattern** — grepped
      `features_service/sports/calculators/*.py` for `tz="UTC"`/`tz=UTC`, found 7 call sites, checked each: -
      **`european_fatigue_calculator.py:207`** — IDENTICAL bug (`match_date = pd.Timestamp(raw_date, tz="UTC")` on the
      same `kickoff_utc` column), and WORSE than travel_calculator's: `match_date` gates the ENTIRE row (all
      `EUROPEAN_FATIGUE_COLUMNS`), not just a subset. Confirmed live-scale on the 3 running P2c backfill VMs: **33,348**
      occurrences on `-085703`, **261** on `-085642`, 0 on `-085726` (mid a different date range). Fixed —
      features-service@81036512 (same `pd.to_datetime(utc=True, errors="coerce")` swap). - `manager_calculator.py:522`,
      `season_context.py:319` — `tz="UTC"` only reached via the `pd.Timestamp.now(tz="UTC")` fallback branch (always a
      fresh timestamp, never re-parses a possibly-aware value) — NOT vulnerable. - `h2h_calculator.py:283` —
      `pd.Timestamp.now(tz="UTC")`, same as above — NOT vulnerable. - `european_fatigue_calculator.py:157` — string
      literal `f"{season_year}-07-01"`, always naive — NOT vulnerable. - `transfer_window_calculator.py:378` —
      `match_date.isoformat()` where `match_date: date` (not `datetime`) per the function signature, so `.isoformat()`
      is always a bare `YYYY-MM-DD` with no tzinfo — NOT vulnerable. **Gate met**: audited all 7 sites; found + fixed 1
      additional real instance (the other 6 are safe by construction). No further sports-calculator instances of this
      exact pattern remain.
