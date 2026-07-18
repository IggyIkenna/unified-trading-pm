---
doc_type: issue
title:
  features-service sports read_historical_fixtures raises "truth value of a Series is ambiguous" for the most-recent
  ~week, degraded (all-NaN) rows still written despite quality-gate FAILED, and it crashed a gap-fill VM on the final
  date
summary: >
  While monitoring the elo+travel consolidated gap-fill fleet (10 SPOT VMs, full 2017-02-02→2026-07-17 recompute), the
  last VM (features-sports-sports-20260717-135916, range 2025-08-07→2026-07-17) exited non-zero (exit_code=1,
  "Processing failed") on its FINAL date. Root cause: `read_historical_fixtures` raises `ValueError: The truth value of
  a Series is ambiguous` (recovery=fail_fast) on every one of the most-recent ~7 days (2026-07-11 through 2026-07-17
  observed), which empties `Team history`, disabling every history-dependent calculator (league, venue_context
  [travel_distance_km + cumulative_travel!], season_context, halftime, multisource_xg, squad_value, team_derived,
  player_lineup) for those dates. The batch quality gate correctly flags this (`Feature validation FAILED ...
  recovery=skip`), but the pipeline still proceeds to WRITE the degraded (100+ all-NaN-column) `fixture_features` rows
  to GCS afterward on every affected date except the very last one, where a downstream assertion/exit finally aborts the
  whole process with exit_code=1.
status: open
nature: notes
asset_group: [sports]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [sports, features, data-correctness, honest-absence, read_historical_fixtures, quality-gate]
related:
  [
    plans/active/issues/sports_elo_calculator_tz_naive_season_boundary_silent_skip_2026_07_17.md,
    plans/active/issues/sports_travel_calculator_home_venue_coords_never_resolved_2026_07_17.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-18
parent_epic: sports_master
priority: P1
source:
  sports_elo_calculator_tz_naive_season_boundary_silent_skip-004 dispatch, slot 6, 2026-07-18 (monitoring the
  consolidated elo+travel gap-fill fleet's last VM)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
gate_on_depends: false
last_updated: 2026-07-18
locked_by:
resolved_by:
---

# sports read_historical_fixtures Series-ambiguous bug — recent-week degraded writes + a fatal crash

## What I found

VM `features-sports-sports-20260717-135916` (10-VM consolidated elo+travel gap-fill fleet, range 2025-08-07→2026-07-17)
exited with `exit_code=1` ("Processing failed") at 2026-07-18T07:54:34Z, right after processing its FINAL date
(2026-07-17). All other 9 VMs in the fleet, and every prior date within VM10's own range, completed with `exit_code=0`.

Log trace (`gs://deployment-scripts-central-element-323112/vm-logs/features-sports-sports-20260717-135916/run.log`),
first occurrence at date 2026-07-11:

```
ERROR [MEDIUM] validation error in features-service.read_historical_fixtures: The truth value of a Series is
ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all(). (recovery=fail_fast, correlation=4fd0d41b)
WARNING No historical fixtures found — history-dependent calculators will be limited
INFO Team history: 0 rows from completed fixtures before 2026-07-11
WARNING Missing fixture_stats — calculators skipped: ['team_form', 'team_xg', 'team_goals', 'advanced_stats']
WARNING No team history — skipping form/xg/goals/h2h/promoted_team calculators
```

The SAME error recurs identically on 2026-07-12, -13, -14, -15, -16, -17 (every date I checked in the last week of the
corpus). On EVERY occurrence except the last, the pipeline still writes `fixture_features` afterward despite the batch
quality gate flagging the shard:

```
ERROR Feature validation FAILED for 2026-07-12: 112 violations across 8 groups — {'halftime': 25, 'league': 30,
  'multisource_xg': 19, 'player_lineup': 1, 'season_context': 15, 'squad_value': 11, 'team_derived': 2,
  'venue_context': 9}
ERROR [HIGH] data_quality error in features-service.batch_feature_quality_gate: Feature output for 2026-07-12 has
  103 all-NaN columns: [...] (recovery=skip, correlation=572b392d)
INFO Wrote fixture_features league=103 (canonical=ELITESERIEN): 8 rows
```

`venue_context`'s all-NaN columns include `travel_distance_km` / `away_cumulative_travel_km` — i.e. the SAME
travel-calculator columns the sibling issue doc's gap-fill is trying to fix, going NaN again on these specific recent
dates (via a different failure path — this is `read_historical_fixtures` cascading into `venue_context`, not the
tz-naive bug). `league` is NOT in this bug's affected-columns list, and neither is `elo_calculator`'s own output group —
the elo/travel tz-naive fixes themselves are unaffected code paths; this is a separate defect.

On the LAST date (2026-07-17), the identical sequence occurs but this time the process does NOT recover — it writes a
partial `fixture_features` row (`league=253 (canonical=MLS): 3 rows`), then `ManifestWriter` records the per-VM shard
update, then the process exits 1 with no further traceback logged between the quality-gate warning and
`ERROR Processing failed` — the exact trigger for the fatal (vs. recoverable) path on this specific date wasn't captured
in the log and needs a direct repro to pin down.

## Why it matters

1. **A real code bug**: `read_historical_fixtures` hitting a pandas "truth value of a Series is ambiguous" error is
   never intentional — it's a boolean-context bug (likely an `if some_series:` / `and`/`or` on a Series instead of
   `.empty`/`.any()`/`.all()`) that needs a direct fix, not a workaround.
2. **Silent-ish degraded writes**: despite the quality gate correctly detecting 100+ all-NaN columns and logging
   `recovery=skip`, the pipeline still WRITES that degraded row to GCS on every affected date except the last — "skip"
   here means "skip raising/blocking", not "skip writing". A manifest consumer would see these `derived_features` shards
   as `captured` even though most feature groups are all-NaN for that date.
3. **Crashed a fleet VM mid-flight**: this is what caused `features-sports-sports-20260717-135916` (part of the
   authorized `BLK-a3149ab4` elo+travel consolidated gap-fill) to exit non-zero on its final date, after successfully
   completing all 344 prior dates in its range.
4. **CORRECTED 2026-07-18T08:2xZ (slot-4) — NOT confined to the most-recent week.** A full re-scan of all 10 fleet VM
   logs
   (`gs://deployment-scripts-central-element-323112/vm-logs/features-sports-sports-20260717-1356{08,32,53,14,33,55, 20,38,56}/run.log` +
   `-135916`), correlating every `Team history: 0 rows` line against the preceding
   `truth value of a Series is ambiguous` error (excluding one unrelated transient 503 on 2025-12-15), finds the bug
   recurs in **three separate corpus windows, ~521 affected dates total**, not ~7:
   - VM `135653` (range 2018-12-26→2019-12-05): **244** affected dates, scattered/intermittent from 2019-01-20 through
     2019-12-06 (dozens of short runs, not one contiguous block).
   - VM `135714` (range 2019-12-07→2020-11-14): **52** affected dates, scattered from 2019-12-12 through 2020-03-03.
   - VM `135916` (range 2025-08-07→2026-07-17): **225** affected dates, ONE CONTIGUOUS block from 2025-12-04 through
     2026-07-17 (with a single gap at 2025-12-15, caused by an unrelated transient 503 GCS error, not this bug).
   - All other 6 fleet VMs (covering 2017-02-02→2018-12-18 and 2020-11-16→2025-08-04) show **zero** occurrences —
     confirmed via `grep`-equivalent count, not sampling. So the true window is bimodal: an intermittent 2019-01→2020-03
     patch (~1 year) and a solid 2025-12-04→2026-07-17 block (~7.5 months, and still open-ended — every date since
     2025-12-04 up to the corpus's live edge is affected). This is NOT a recency-only issue; whatever triggers it
     recurred once ~6 years ago and again now. Todo 3 below is updated to reflect the real gap-fill scope.
     **Cross-cutting risk**: the elo+travel consolidated gap-fill fleet (this same 10-VM run) was just marked
     complete/verified via "direct parquet content sampling" — if that spot-check didn't happen to sample from inside
     these ~521 dates, its `venue_context`/travel-column verification may not actually cover them (this bug zeroes
     `venue_context` independently of the elo/travel fixes). Flagging for operator awareness, not re-opening that plan
     myself — outside this issue's scope to verify.

## Recommended decision

Fix `read_historical_fixtures`'s Series-ambiguous boolean check (find the `if <Series>:` / bare-Series truthiness site
and replace with an explicit `.empty`/`.any()`/`.all()`), and separately decide whether the
`batch_feature_quality_gate`'s `recovery=skip` for >85%(ish)-NaN shards should actually BLOCK the write (matching the
`FeatureWriteGate REJECTED shard` pattern already used elsewhere in this same pipeline for `fixture_player_stats`)
rather than writing degraded data through. Did not attempt either fix myself — outside this dispatch's scope (elo/travel
tz-naive gap-fill), and the root cause needs a direct repro/read of `read_historical_fixtures`, not something safely
fixed from a log trace alone.

## Todos

- [ ] [DATA] P1. Root-cause + fix the `read_historical_fixtures` "truth value of a Series is ambiguous" error
      (`recovery=fail_fast`, correlation ids `4fd0d41b` and similar) — find the bare-Series boolean-context site and use
      `.empty`/`.any()`/`.all()` explicitly. Add a regression test reproducing the exact failure mode. (repo:
      features-service)
- [ ] [DATA] P2. Decide whether `batch_feature_quality_gate`'s `recovery=skip` path should BLOCK the write (like
      `FeatureWriteGate REJECTED shard` does for `fixture_player_stats`) instead of writing a >85%-all-NaN shard through
      — this is a data-correctness policy decision, not just a bug fix. (repo: features-service)
- [ ] [DATA] P2. Once the above is fixed, gap-fill the CORRECTED affected-date set (~521 dates, not 7): 2019-01-20
      through 2019-12-06 (intermittent, ~244 dates), 2019-12-12 through 2020-03-03 (intermittent, ~52 dates), and
      2025-12-04 through the corpus's live edge (contiguous, 225+ dates and growing daily until the fix ships) — the
      exact per-VM date lists are in "What I found" item 4 above. `--force` on the fixed code, same pattern as the
      sibling elo/travel gap-fill. Re-verify against the live corpus edge at fix time since the 2025-12-04→ window is
      still open. (repo: features-service)

## Progress Log

### 2026-07-18T08:01Z — data_engineering slot-6 (found while monitoring the elo+travel consolidated gap-fill fleet)

Found while watching the last VM (135916) of the authorized `BLK-a3149ab4` 10-VM fleet finish — it exited 1 instead of 0
on its final date. Traced the root cause via direct log read (not guesswork): confirmed via `grep` that the identical
`read_historical_fixtures` error recurs on every date from 2026-07-11 through 2026-07-17 in this VM's log, and that
degraded (all-NaN) `fixture_features` rows were written through on every occurrence except the last. Filing this as its
own issue doc — separate from the elo tz-naive-season-boundary bug and the travel str/int-mismatch bug this dispatch's
actual task is gap-filling (confirmed `venue_context`'s all-NaN columns here come from `read_historical_fixtures`
failing, not from either of those two already-fixed bugs). Not fixing this myself (outside scope). Returning to the
elo/travel gap-fill task to verify its actual completion coverage (3,452/3,453 corpus dates — every VM finished 0-exit
except this one date on this one VM) before flipping its checkboxes.

### 2026-07-18T08:2xZ — data_engineering slot-4 (dispatched to Todo-3 gap-fill; found scope was wrong before starting)

Dispatched `-003` (the gap-fill todo). `-001` (root-cause fix, slot 2) and `-002` (quality-gate policy decision, slot 3)
are still `dispatched`/in-progress — this todo has no formal `prereqs` gate on them (`depends_on: []`,
`gate_on_depends: false` in this doc's frontmatter), so the dispatcher handed it to me anyway even though the gap-fill
genuinely cannot run until the fix lands. Rather than idle-wait doing nothing useful, did the "re-check whether the
window is wider" part of my own todo's brief now (read-only GCS log analysis via the features-service `.venv`'s
`google.cloud.storage` client, no code touched, no collision risk with slots 2/3): downloaded and grepped all 10 fleet
VM run.logs, correlating every `Team history: 0 rows` line against a preceding `truth value of a Series is ambiguous`
error. Result: the affected-date count is **~521, not ~7** — see the corrected "What I found" item 4 and the rewritten
Todo 3 above. This is a big-enough scope change (7.4x, spans 3 non-contiguous corpus windows across 2 different years)
that I'm flagging it rather than silently absorbing it. Filing `/blocked` next to notify main/operator of (a) the
widened scope so `-001`'s regression test and `-002`'s policy decision account for the real window, not just last week,
and (b) the cross-cutting risk that the just-completed elo+travel gap-fill's "verified via parquet sampling" claim may
not have covered these same ~521 dates. Continuing to wait on `-001`/`-002` before I can actually run the gap-fill.
