---
doc_type: issue
title: footystats MATCHES 4-league fetch gap + PREDICTIONS cup fixture-calendar gap block sports_p2 item #7 VERIFY gate
summary: |
  Filed 2026-07-08 as follow-up to sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md item #5
  (footystats history → zero-missing) and item #7 (full-history reference cleanliness VERIFY gate, which cannot flip
  until item #5 does). Slot-7's 2026-07-08 20:10 UTC re-verification (see plan Progress Log) ran the existing typing
  pass for genuinely non-covered leagues (432 rows cleared) and confirmed the REMAINING residual is a real CODE gap,
  not closeable by a VM re-run or another typing script: MATCHES pending_fetch=5,641 is 96% concentrated in 4
  nominally-covered leagues (CHILE_PRIMERA=1,459, K_LEAGUE_1=1,451, LIGA_MX=1,291, ARGENTINA_PRIMERA=1,228) — a
  near-total-history gap despite each league having ≥1 captured row (so the coverage-typing mask correctly leaves
  them untyped as real gaps). PREDICTIONS pending_fetch=44,163 is 93% concentrated in continental/cup competitions
  (UECL/UEL/UCL/SWISS_CUP/COPA_ARGENTINA/CHILE_PRIMERA_B/LIGA_EXPANSION_MX/JLEAGUE_CUP/TURKIYE_KUPASI/TACA_DE_PORTUGAL
  +37 more), each missing ~75-85% of its full 2019-2026 date range in a near-uniform pattern (not a recent tail) —
  consistent with a fixture-calendar-awareness gap where the PREDICTIONS orchestrator never resolves a
  no-fixture-that-day cup date to `empty_confirmed(EXPECTED_NO_FIXTURE)`, leaving the enum's blanket eu placeholder
  untouched forever. ODDS pending_fetch=1,264 is not yet root-caused. Recommendation from slot-7: file a dedicated
  follow-up before the next footystats VM launch, else a re-run reproduces the same residual. No such doc existed
  until this filing (checked 2026-07-08 by slot-14).
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [footystats, honest-coverage, fetch-gap, fixture-calendar, sports-p2, deferred]
related:
  [
    sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md,
    sports_reference_backfill_oom_2026_06_22.md,
    ../../codex/02-data/honest-coverage-model.md,
    ../../codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-08
last_updated: 2026-07-08
parent_epic: sports_master
priority: P2
source:
  sports_p2_history_reference_and_odds_2015_to_present-015 (slot-14, re-surfacing slot-7's 2026-07-08 20:10 UTC
  diagnosis)
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 1.0
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
depends_on:
supersedes:
superseded_by:
---

## What I found

`sports_p2_history_reference_and_odds_2015_to_present_2026_06_27.md` item #7 (the P1 VERIFY gate for full-history
reference cleanliness across all 6 sports reference sources) cannot flip until item #5 (footystats history →
zero-missing) reaches `pending_fetch == 0`. Item #5's 2026-07-08 diagnosis (slot-7, re-confirmed unchanged by slot-5 at
20:58 UTC and by this filing) identified two distinct real gaps in
`instruments_service/engine/orchestrator/footystats.py` (971 lines; MATCHES row-emission logic starts ~line 405,
PREDICTIONS/cup handling elsewhere in the same file):

1. **MATCHES 4-league fetch gap** — `pending_fetch=5,641`, 96% concentrated in CHILE_PRIMERA (1,459), K_LEAGUE_1
   (1,451), LIGA_MX (1,291), ARGENTINA_PRIMERA (1,228). These leagues pass the coverage-typing mask (≥1 captured row
   exists per the dynamic "≥1 captured row = covered" logic in
   `type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py`), so this is NOT a config/typing issue — it
   looks like a league-specific fetch failure in the MATCHES orchestrator path (line ~405 onward) that has left
   near-total history unfetched for exactly these 4 leagues while other covered leagues are clean.
2. **PREDICTIONS cup fixture-calendar gap** — `pending_fetch=44,163`, 93% concentrated in continental/cup competitions
   (UECL, UEL, UCL, SWISS_CUP, COPA_ARGENTINA, CHILE_PRIMERA_B, LIGA_EXPANSION_MX, JLEAGUE_CUP, TURKIYE_KUPASI,
   TACA_DE_PORTUGAL, +37 more). Each is missing ~75-85% of its full 2019-2026 date range in a near-uniform pattern (not
   a recent tail), consistent with the PREDICTIONS orchestrator never resolving a no-fixture-that-day cup date to
   `empty_confirmed(EmptyConfirmedReason.EXPECTED_NO_FIXTURE)` (the pattern already used for MATCHES at
   footystats.py:584/598/940) — cup competitions don't play every day, so the blanket eu placeholder from the enum stays
   un-typed forever for those dates.
3. **ODDS gap** — `pending_fetch=1,264`, not yet root-caused (no investigation session has looked at this cluster
   specifically).

## Why it matters

This is the SAME class of silent-placeholder risk the honest-coverage model exists to eliminate: a `pending_fetch` row
that is neither a genuine capture failure nor a documented `empty_confirmed` reason just sits un-terminal indefinitely.
Concretely it blocks:

- `sports_p2_history_reference_and_odds_2015_to_present-0XX` item #5 (its own gate) and therefore item #7 (the
  cross-source VERIFY gate) — both stay `- [ ]` and both keep re-bouncing to data_engineering slots on every dispatch
  cycle (2+ re-verifications already logged with byte-identical findings: 2026-07-08 20:10 UTC slot-7, 20:58 UTC
  slot-5).
- Any future footystats backfill VM re-run reproduces the identical residual (confirmed: `fs-backfill-20260706-161335`
  already ran to completion with `exit_code=0` and did NOT close this gap), so further VM spend on footystats without a
  code fix is wasted compute.

## Recommended decision

File this as its own dedicated fix, decoupled from the sports_p2 VERIFY-gate task (which is diagnosis-only scope, not a
code-fix task). A data_engineering slot with a full session budget should:

1. Root-cause the MATCHES 4-league gap — check whether footystats' upstream API returns 4xx/5xx/empty for these specific
   league IDs across the full date range, or whether a league-ID mapping / season-boundary bug in the MATCHES fetch path
   (footystats.py ~405-625) is silently swallowing them.
2. Add cup/continental-competition fixture-calendar awareness to the PREDICTIONS path — resolve a no-fixture date to
   `empty_confirmed(EXPECTED_NO_FIXTURE)` the same way MATCHES already does (mirror the existing pattern at
   footystats.py:584/598/940), scoped to competitions with irregular (non-daily) schedules.
3. Root-cause the ODDS 1,264-row residual (currently undiagnosed).
4. Re-run the existing typing pass + confirm `pending_fetch == 0` for footystats before re-dispatching a backfill VM (a
   VM re-run without the code fix reproduces the same residual — confirmed by `fs-backfill-20260706-161335`).

## Actionable todos

- [x] ✅ [CODE] P2. **Root-cause + fix footystats MATCHES 4-league fetch gap** (CHILE_PRIMERA, K_LEAGUE_1, LIGA_MX,
      ARGENTINA_PRIMERA — 96% of the 5,641-row residual) — instruments-service@1af6c92 (slot-8 sonnet/high). **Root
      cause**: all 4 leagues carry `data_sources=PRED_NO_FOOTYSTATS` (footystats excluded per subscription limit —
      `unified-api-contracts/.../league_data_prediction.py`), so they are correctly ABSENT from the footystats-scoped
      expected-league set (`_ft_expected`) used by the honest-coverage skip/gap loop in
      `_fetch_footystats_matches`/`_fetch_footystats_predictions`. But the per-league captured-write gate in both
      functions checked only the GENERIC `_is_in_canonical_write_universe` (api_football-scoped, which DOES track these
      leagues) — not the footystats-scoped set. FootyStats' bulk `/todays-matches` endpoint returns incidental rows for
      these leagues regardless of subscription; the mismatched gate let those get written as `captured`, fooling the "≥1
      captured row = covered" dynamic heuristic in
      `type_footystats_matches_predictions_non_covered_leagues_2026_07_06.py` into treating them as footystats-covered
      and seeding a full-history expected-universe denominator the per-league loop (correctly scoped to `_ft_expected`)
      never systematically backfills — a permanent, unclosable `pending_fetch` gap. **Fix**: both write paths now also
      gate on the footystats-subscribed expected-league set, matching the honest-coverage loop's own scoping; future
      incidental rows for out-of-subscription leagues are dropped (no captured/empty manifest row written), consistent
      with how the ~62 other non-covered footystats leagues already behave. Added 2 regression tests in
      `tests/unit/test_orchestrator_sports.py` (`test_out_of_subscription_league_dropped_not_captured` in both
      `TestFetchFootystatsMatches` and `TestFetchFootystatsPredictions`) asserting the drop + no manifest pollution.
      Full `quality-gates.sh` green (ALL QUALITY GATES PASSED), shipped via quickmerge --agent. **Scope note**: this
      closes the WRITE-PATH bug (prevents future recurrence) but does NOT retroactively clean the EXISTING ~5,415
      pending_fetch rows already seeded for these 4 leagues in the live manifest — that data cleanup is todo #4 below's
      scope (re-run the typing pass after this fix lands; the existing few incidental `captured` rows for these leagues
      will still need an explicit re-type pass since the dynamic "≥1 captured row" heuristic reads historical manifest
      state, not just going-forward writes).
- [ ] [CODE] P2. **Add cup/continental-competition fixture-calendar awareness to footystats PREDICTIONS** — mirror the
      existing `EmptyConfirmedReason.EXPECTED_NO_FIXTURE` resolution already used for MATCHES (footystats.py:584/598) so
      no-fixture dates for UECL/UEL/UCL/SWISS_CUP/COPA_ARGENTINA/+37 more resolve to a terminal typed state instead of
      staying un-typed `pending_fetch` forever; add regression test on a cup competition's known off-days (repo:
      instruments-service).
- [ ] [DATA] P3. **Root-cause footystats ODDS 1,264-row residual** — no investigation session has looked at this
      cluster; determine whether it shares the MATCHES or PREDICTIONS root cause or is a distinct third gap (repo:
      instruments-service).
- [ ] [DATA] P2. **Re-verify + re-dispatch footystats backfill VM after the above land** — once the two CODE fixes are
      shipped, re-run the typing pass, confirm `(footystats, MATCHES)` + `(footystats, PREDICTIONS)` +
      `(footystats,     ODDS)` `pending_fetch == 0`, then flip `sports_p2_history_reference_and_odds_2015_to_present`
      item #5 (and contribute to unblocking item #7) (repo: instruments-service).

## Progress Log

- **2026-07-08** — Issue filed by slot-14 (data_engineering), dispatched to
  `sports_p2_history_reference_and_odds_2015_to_present-015` (item #7 VERIFY gate). Re-confirmed
  `tm-backfill-20260708-205809` (item #7's TM sub-gate) still RUNNING and healthy (heartbeats + successful club fetches
  in `run.log` as of 21:03 UTC, started 21:00 UTC — too early to expect completion, not stalled). Since item #7 cannot
  flip regardless of the TM VM's outcome until items #4 (understat) and #5 (footystats) also close, and item #5's own
  diagnosis (slot-7, 2026-07-08 20:10 UTC) explicitly recommended filing a dedicated follow-up before further VM spend —
  checked and no such doc existed — filed this issue with 4 actionable todos so a future data_engineering dispatch with
  full session budget can execute the code fixes instead of re-diagnosing from scratch.
