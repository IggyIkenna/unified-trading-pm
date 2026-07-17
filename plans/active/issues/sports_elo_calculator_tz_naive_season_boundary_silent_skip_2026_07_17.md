---
doc_type: issue
title:
  features-service sports elo_calculator silently skipped Elo updates for every history row past the first whenever
  kickoff_utc parses tz-aware — fixed, backfill re-run of affected dates still owed
summary: >
  While spot-checking the live serial log of `fss-backfill-vm-4` during `sports_p2_features_history_to_ml_ready-001`
  (Todo 1's 2015→present compute), found `elo_calculator._crosses_season_boundary` comparing a tz-naive `boundary =
  pd.Timestamp(year=..., month=8, day=1)` against tz-aware `prev_date`/`curr_date` (parsed from `kickoff_utc`), raising
  `TypeError: Cannot compare tz-naive and tz-aware timestamps`. `compute_elo_batch`'s per-row `except (ValueError,
  TypeError, KeyError)` (correct shard-isolation design) caught it and silently skipped the ENTIRE row's Elo update —
  not just a subset of columns. Because the boundary check runs unconditionally once `prev_date` is set (i.e. every
  history row after the first), this meant every historical fixture past the first for any date range with tz-aware
  `kickoff_utc` values never updated Elo ratings at all — teams silently stayed pinned near the 1500 starting Elo
  instead of NaN, so downstream consumers could not distinguish "genuinely early in Elo history" from "code defect
  dropped every update". Confirmed live-scale: one VM's serial log showed 4700+ "Skipping fixture row N: Cannot compare
  tz-naive and tz-aware timestamps" lines in a single tail sample. Same bug family as the already-fixed
  `travel_calculator`/`european_fatigue_calculator` tz bugs
  (`sports_travel_calculator_tz_aware_kickoff_crash_2026_07_14.md`), but a different code shape (direct `<`/`<=`
  comparison against a hand-built `pd.Timestamp(year=...)`, not a `pd.Timestamp(value, tz="UTC")` re-parse) — the prior
  issue's P3 audit grepped only for `tz="UTC"` call sites and did not catch this one. Fixed in features-service (pending
  commit): `boundary` now built with `tz=curr_date.tz` so it always matches the tz-awareness of the dates it's compared
  against. The 10 VMs currently running the 2015→present backfill (`fss-backfill-vm-1..10`) are on a pre-fix tarball
  snapshot and will keep silently flat-lining Elo for tz-aware-kickoff history rows until relaunched or gap-filled.
status: open
nature: notes
asset_group: [sports]
stage: [features]
repos: [features-service]
scope: [engineer, admin]
tags: [sports, features, data-correctness, elo-calculator, honest-absence, timezone, silent-failure]
related:
  [
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    plans/active/issues/sports_travel_calculator_tz_aware_kickoff_crash_2026_07_14.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-17
parent_epic: sports_master
priority: P2
source:
  sports_p2_features_history_to_ml_ready-001 dispatch, slot 15, 2026-07-17 (Todo 1 in-progress monitoring, log-tail
  spot-check)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
  - sports_p2_features_history_to_ml_ready_2026_06_27.md
gate_on_depends: true
last_updated: 2026-07-17
locked_by:
resolved_by:
---

# features-service sports elo_calculator silent Elo-skip on tz-aware kickoff_utc

## What I found

`features_service/sports/calculators/elo_calculator.py`:

```python
def _crosses_season_boundary(prev_date: pd.Timestamp, curr_date: pd.Timestamp) -> bool:
    ...
    for year in range(prev_year, curr_year + 1):
        boundary = pd.Timestamp(year=year, month=_SEASON_BOUNDARY_MONTH, day=_SEASON_BOUNDARY_DAY)  # tz-naive
        if prev_date < boundary <= curr_date:  # raises when prev_date/curr_date are tz-aware
            return True
    return False
```

Called from `compute_elo_batch`'s per-row loop as
`if prev_date is not None and _crosses_season_boundary(prev_date, curr_date): ...` — i.e. on every history row **after
the first** (the first row has `prev_date is None` and skips the check).
`dates = pd.to_datetime(history_sorted[kickoff_col], errors="coerce")` parses tz-aware whenever the source `kickoff_utc`
values carry explicit UTC offset info — the same column already implicated in the travel_calculator /
european_fatigue_calculator tz bugs. When that happens, `prev_date < boundary` raises
`TypeError: Cannot compare tz-naive and tz-aware timestamps` **unconditionally**, regardless of whether a real season
boundary is actually being crossed — the comparison itself is what fails, not the boundary logic.

The whole per-row `try` body (Elo rating update, form tracking, everything) is wrapped by:

```python
except (ValueError, TypeError, KeyError) as exc:
    logger.warning("Skipping fixture row %s: %s", idx, exc)
    continue
```

(correct shard-level-isolation design — no `raise` inside a per-fixture loop) — so the TypeError is caught and the
**entire row's Elo update is dropped**, not just a subset of derived columns. Confirmed live-scale via
`fss-backfill-vm-4`'s serial console output (`sports_p2_features_history_to_ml_ready-001`, 2026-07-17 03:5xZ): **4700+**
occurrences of `Skipping fixture row N: Cannot compare tz-naive and tz-aware timestamps` in a single tail sample,
sequential from row 1 — consistent with every row past the first in that date's history chunk being dropped.

Reproduced + verified with 2 unit tests (both confirmed to FAIL on the pre-fix code, reproducing the exact live log
message):

- `TestCrossesSeasonBoundary::test_tz_aware_dates_do_not_raise`
- `TestEloExceptionHandlers::test_tz_aware_kickoff_history_updates_every_row` — 2-row history, team wins both matches;
  pre-fix `elo_after_two_wins == elo_after_one_win` (second win's Elo update silently dropped); post-fix
  `elo_after_two_wins > elo_after_one_win`.

## Why it matters

- Violates the data_engineering craft's north-star #1 (no silent placeholders) — worse than the travel_calculator case,
  because the result isn't even NaN, it's a **plausible-looking but wrong** value (teams stuck near 1500 starting Elo
  look like genuinely-early-history teams, not like a code defect). Nothing in the written parquet distinguishes the
  two.
- Directly threatens `sports_p2_features_history_to_ml_ready_2026_06_27.md` Todo 1's own gate ("ML-ready ... NaN only
  where honest-absence") and Todo 2's gate ("every NaN traces to a typed upstream honest-absence") — these degraded Elo
  columns aren't NaN at all, so Todo 2's NaN-tracing check wouldn't even flag them; they'd pass the gate while carrying
  wrong values.
- The 10 VMs (`fss-backfill-vm-1..10`) launched for Todo 1's 2015→present compute are running the pre-fix code and will
  keep producing this silent degradation on every affected date until relaunched or gap-filled.

## Recommended decision

Fix now (small, clear, root-caused) — **done** (pending commit/QG/ship this dispatch). Per the sibling travel_calculator
issue's precedent: given the backfill is well underway and healthy, killing/relaunching the 10 live VMs now is a bigger,
riskier action than this finding warrants on its own. Recommend letting the current pass finish, then identifying +
gap-filling the affected date ranges (dates with tz-aware-kickoff fixtures computed before this fix lands) as a normal
follow-up backfill pass — same operational pattern as Todo 2 in the sibling issue doc.

## Todos

- [x] ✅ [DATA] P2. **Fix the tz-handling bug** in `elo_calculator._crosses_season_boundary` — build `boundary` with
      `tz=curr_date.tz` so it matches the tz-awareness of the dates it's compared against. Add regression tests
      confirming the pre-fix code raises/silently drops the update and the post-fix code doesn't. (repo:
      features-service) — features-service@04274b6a; QG green (full suite + formula-hash + no-look-ahead gates), shipped
      via quickmerge --agent 2026-07-17.
- [x] ✅ [DATA] P2. **SCOPE CORRECTED (2026-07-17, slot-15) — this is NOT a contiguous date-range problem, it's
      per-(date,league) DATA-DEPENDENT.** Original wording assumed "everything computed before the fix landed" is
      affected — empirically FALSE. Sampled 7 known-populated `derived_features` dates spanning 2018→2026 directly
      (`home_elo`/`away_elo` == exactly `1500.0` flat = bug fired for that query's `fixtures_history`): **2018-10-23
      FLAT, 2019-06-01 FLAT, 2020-01-15 FLAT, 2021-05-22 NOT-flat (1529.04), 2024-06-14 NOT-flat (1504.18), 2025-12-05
      NOT-flat (1503.57), 2026-06-01 FLAT** — 4/7 affected, scattered across eras with no visible date-range boundary.
      Root cause is per-call: whether `kickoff_utc` parses tz-aware for that SPECIFIC `fixtures_history` slice (varies
      by which historical fixtures land in a given team/league/date's lookback), not a global "before vs after a
      timestamp" split. A raw-source `kickoff_utc` dtype check (attempted this dispatch, `entity=fixtures` parquets) did
      not resolve which upstream field/format drives the split — needs a deeper source-schema dig, not chased further
      this dispatch (time-boxed). **Split into 2b/2c below** (audit-scale work, not a quick date-range gap-fill) — this
      original formulation is superseded, not actionable as written. (repo: features-service)
- [ ] [DATA] P2. **(audit step) Build a single-walk audit** (following this codebase's phantom-audit pattern — read the
      availability manifest for `feature_group=derived_features`, NOT a raw whole-corpus GCS walk) that, for each
      captured (date, league), reads ONLY the `home_elo`/`away_elo` columns and flags exact-`1500.0`-flat rows as
      bug-affected. Output: a list of affected (date, league) pairs (or a manifest-attached flag) — this is the
      concrete, cheap identification step the original P2 wording assumed was trivial but isn't. (repo:
      features-service)
- [ ] [DATA] P2. **(gap-fill step) Gap-fill re-run** the (date, league) pairs the audit step above identifies with
      `--force` on the fixed (`elo_calculator.py`@`04274b6a`+) code. Scope depends entirely on the audit step's output —
      could range from a small targeted set to a large fraction of history; re-estimate cost once the real count is
      known before launching any multi-VM fleet (this is exactly the kind of infra-cost decision the data-correctness
      HARD RULE says to surface, not default to a full 10-VM re-run for). (repo: features-service)
- [ ] [VERIFY] P3. **Audit whether other sports calculators build a hand-constructed
      `pd.Timestamp(year=..., month=...,     day=...)` (or similar tz-naive-by-construction Timestamp) that gets
      compared against a possibly-tz-aware value** — grepped `features_service/sports/calculators/*.py` for
      `pd.Timestamp(year=` this dispatch and found only `elo_calculator.py`'s one site (now fixed), but a full audit of
      naive-vs-aware _comparison_ sites (not just re-parse sites, which the sibling issue's P3 already covered) hasn't
      been done. (repo: features-service)

## Progress Log

### 2026-07-17T03:5xZ — data_engineering slot-15 (found + fixed while monitoring Todo 1's live backfill fleet)

Spot-checked `fss-backfill-vm-4`'s serial console log while monitoring the 10-VM Todo 1 fleet (routine health check, not
an audit) and found the warning volume above. Root-caused via direct code read (not guesswork) — confirmed
`_crosses_season_boundary`'s `boundary` construction is tz-naive-by-construction and only reachable once `prev_date` is
set. Confirmed no other `pd.Timestamp(year=` sites exist in `features_service/sports/calculators/*.py` (single grep, not
a full walk). Fixed with the minimal `tz=curr_date.tz` change (mirrors the existing `_crosses_season_boundary` NaT-guard
pattern, doesn't touch the `pd.to_datetime` parse call, so blast radius is contained to this one function). Added +
verified 2 regression tests (confirmed both fail pre-fix via `git stash` of just the source file, confirmed both pass
post-fix). QG in progress this dispatch; will ship via quickmerge once green. Not relaunching the live 10-VM fleet — per
the sibling issue's precedent, treating this as a follow-up gap-fill (Todo 2 above) once Todo 1 completes, not a reason
to kill healthy in-progress infra work.

### 2026-07-17T12:1xZ — data_engineering slot-15 (Todo 2 dispatch — scope investigation, corrected the date-range assumption, split into P2b/P2c)

Continuation from this same slot's earlier entries (fixed the bug, then monitored+completed the parent plan's Todo 1
2015→present compute — 4216/4216, 100.0%, `/done`'d that task). Server auto-dispatched this issue doc's Todo 2 next
(`sports_elo_calculator_tz_naive_season_boundary_silent_skip-001`), now that its `depends_on` prereq (Todo 1) is
satisfied.

**Investigated before acting** rather than assuming the original wording ("identify date-ranges computed before the
fix") was correct. Sampled `derived_features` parquets directly across 7 dates spanning 2018→2026 (bounded, targeted
reads — NOT a whole-corpus GCS walk): confirmed the bug is genuinely real (2018-10-23/2019-06-01/2020-01-15/2026-06-01
show exact flat `home_elo=away_elo=1500.0`) but **NOT contiguous by date** — 2021-05-22/2024-06-14/2025-12-05 in the
same sample show real, varying Elo values despite also predating the fix. Attempted to trace this to the raw source
`kickoff_utc` field's tz-format directly (would have been a cheap, precise diagnostic vs. scanning outputs) but the
`entity=fixtures` parquets I checked didn't carry a `kickoff_utc` column under the paths I probed — didn't chase this
further given the time-box on a 1h-estimated task.

**Conclusion: the original P2 wording is not actionable as a "before/after a date" cutoff** — rewrote it as
COMPLETE-BUT-SUPERSEDED (documents the corrected finding) and split the real remaining work into P2b (build a
single-walk manifest-driven audit to precisely identify affected (date,league) pairs — the genuinely cheap way to do
this, not per-file sampling) and P2c (gap-fill whatever P2b finds, cost/scope TBD until P2b runs). This is audit-scale
follow-up work, not a 1-hour fix — did not attempt to build the P2b audit script in this dispatch (would need real
design: read the availability manifest for capture status, decide the read strategy for a
potentially-tens-of-thousands-of-files corpus without blowing the single-walk-discipline budget). Declining to build/run
P2b/P2c this dispatch; shipping the scope-correction (real, durable progress — corrects a wrong assumption future
dispatches would otherwise have wasted time on) and returning to the queue. `/skip-current-task` after this ships
(done_definition — "checkbox flipped + code shipped" — isn't met for the ORIGINAL P2 ask, since gap-filling didn't
happen; the corrected-scope todo itself is the shippable unit here).
